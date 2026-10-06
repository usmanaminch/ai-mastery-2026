"""Input adapters. Each turns a tool's output into a list of Exposure records.

Shipped: Trivy JSON, Grype JSON, a plain product CSV, and a mapped CSV for any
other scanner's export (Tenable, Qualys, Wiz, Rapid7...). API connectors for
those products would implement the same function signature:
    def load_x(...) -> list[Exposure]
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import yaml

from .models import Exposure

CVE_RX = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)


def _logs(value) -> set[str]:
    if not value:
        return set()
    if isinstance(value, (list, set, tuple)):
        return {str(v).strip().lower() for v in value if str(v).strip()}
    return {v.strip().lower() for v in re.split(r"[;,|]", str(value)) if v.strip()}


def _cwe_list(raw) -> list[str]:
    out = []
    for c in raw or []:
        val = c.get("cwe") or c.get("id") or "" if isinstance(c, dict) else str(c)
        m = re.search(r"CWE-\d+", str(val), re.I)
        if m:
            out.append(m.group(0).upper())
    return sorted(set(out))


def load_trivy(path: Path, asset: str, logs=None) -> list[Exposure]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for result in data.get("Results") or []:
        for v in result.get("Vulnerabilities") or []:
            vid = v.get("VulnerabilityID", "")
            if not CVE_RX.fullmatch(vid):
                continue
            out.append(Exposure(
                asset=asset, cve=vid.upper(), product=v.get("PkgName", ""),
                version=v.get("InstalledVersion", ""), fixed_version=v.get("FixedVersion", ""),
                source=f"trivy:{result.get('Target', '')}", cwes=_cwe_list(v.get("CweIDs")),
                logs=_logs(logs)))
    return out


def load_grype(path: Path, asset: str, logs=None) -> list[Exposure]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for m in data.get("matches", []):
        vuln, art = m.get("vulnerability", {}), m.get("artifact", {})
        ids = {vuln.get("id", "")} | {r.get("id", "") for r in m.get("relatedVulnerabilities", [])}
        fixes = (vuln.get("fix") or {}).get("versions") or []
        for cve in sorted(i.upper() for i in ids if CVE_RX.fullmatch(i or "")):
            out.append(Exposure(
                asset=asset, cve=cve, product=art.get("name", ""), version=art.get("version", ""),
                fixed_version=", ".join(fixes), source="grype", cwes=_cwe_list(vuln.get("cwes")),
                logs=_logs(logs)))
    return out


def load_product_csv(path: Path, catalog: list[dict]) -> list[Exposure]:
    """CSV columns: asset, vendor, product, version, logs.

    Matches each row to exploited-vulnerability catalog entries by vendor and product
    name. Versions are NOT checked (the catalog carries none), so every match is marked
    version_checked=False and the report says to confirm with a scanner.
    """
    out = []
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            vendor, product = norm(row.get("vendor")), norm(row.get("product"))
            for entry in catalog:
                if norm(entry.get("vendorProject")) != vendor:
                    continue
                if product and product not in norm(entry.get("product")):
                    continue
                out.append(Exposure(
                    asset=row.get("asset", ""), cve=entry["cveID"].upper(), vendor=row.get("vendor", ""),
                    product=row.get("product", ""), version=row.get("version", ""),
                    source="product-csv", cwes=_cwe_list(entry.get("cwes")),
                    logs=_logs(row.get("logs")), version_checked=False))
    return out


def load_mapped_csv(path: Path, mapping_path: Path, logs=None) -> list[Exposure]:
    """Any scanner's CSV export, given a YAML mapping of its column names:

        columns:
          asset: "Host"            # required
          cve: "CVE"               # required; may hold several CVEs separated by , or ;
          product: "Plugin Name"   # optional
          version: "Version"       # optional
          fixed_version: "Solution"  # optional
        source: tenable            # label for the report
    """
    spec = yaml.safe_load(Path(mapping_path).read_text(encoding="utf-8"))
    cols, label = spec["columns"], spec.get("source", "mapped-csv")
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            for cve in CVE_RX.findall(row.get(cols["cve"], "") or ""):
                out.append(Exposure(
                    asset=row.get(cols["asset"], ""), cve=cve.upper(),
                    product=row.get(cols.get("product", ""), "") if cols.get("product") else "",
                    version=row.get(cols.get("version", ""), "") if cols.get("version") else "",
                    fixed_version=row.get(cols.get("fixed_version", ""), "") if cols.get("fixed_version") else "",
                    source=label, logs=_logs(logs)))
    return out


def dedupe(exposures: list[Exposure]) -> list[Exposure]:
    """Two scanners often report the same CVE on the same asset. Keep one, merge sources."""
    seen: dict[tuple[str, str, str], Exposure] = {}
    for e in exposures:
        key = (e.asset, e.cve, e.product.lower())
        if key in seen:
            prev = seen[key]
            if e.source not in prev.source.split("+"):
                prev.source += "+" + e.source
            prev.cwes = sorted(set(prev.cwes) | set(e.cwes))
            prev.logs |= e.logs
        else:
            seen[key] = e
    return list(seen.values())
