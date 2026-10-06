"""Convert VVAH SARIF findings into Sigma rules plus a coverage report."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import yaml

from .cwe_map import BEHAVIORAL, RULE, UNCOVERABLE, UNMAPPED, Detector, strategy_for
from .routes import build_route_map, input_channels, routes_for

NAMESPACE = uuid.UUID("6f1d3c52-8a0e-4c2b-9f57-2d1b0a9e7c41")
ANGLE = {"webserver": "request payload", "process_creation": "app spawned a shell"}
LEVELS = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low", "INFO": "informational"}


@dataclass
class Finding:
    finding_id: str
    title: str
    cwe_id: str | None
    cwe_name: str | None
    severity: str
    confidence: float | None
    file: str
    line: int
    cvss: str | None


def _cwe_from(result: dict) -> str | None:
    props = result.get("properties", {})
    for candidate in (props.get("cweId"), props.get("cwe")):
        if candidate:
            m = re.search(r"CWE-\d+", str(candidate))
            if m:
                return m.group(0)
    for taxon in result.get("taxa", []):
        m = re.search(r"CWE-\d+", str(taxon.get("id", "")))
        if m:
            return m.group(0)
    return None


def load_findings(sarif_path: Path) -> list[Finding]:
    sarif = json.loads(sarif_path.read_text(encoding="utf-8"))
    findings: list[Finding] = []
    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            props = result.get("properties", {})
            loc = (result.get("locations") or [{}])[0].get("physicalLocation", {})
            file = loc.get("artifactLocation", {}).get("uri", "unknown")
            line = loc.get("region", {}).get("startLine", 0)
            title = re.sub(r"\s+\[CVSS.*\]$", "", result.get("message", {}).get("text", "")).strip()
            fid = (result.get("partialFingerprints", {}).get("vvaFindingId/v1")
                   or hashlib.sha256(f"{file}:{line}:{title}".encode()).hexdigest()[:16])
            conf = props.get("confidence")
            findings.append(Finding(
                finding_id=fid, title=title, cwe_id=_cwe_from(result),
                cwe_name=props.get("cweName"), severity=str(props.get("severity", "MEDIUM")).upper(),
                confidence=float(conf) if conf is not None else None,
                file=file, line=int(line), cvss=props.get("cvssVector"),
            ))
    return findings


def load_routes(path: Path | None) -> dict[str, list[str]]:
    """routes.yaml maps 'file' or 'file:line' to a URL path (or list of paths)."""
    if not path:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(k): ([str(x) for x in v] if isinstance(v, list) else [str(v)]) for k, v in data.items()}


def route_for(f: Finding, manual: dict[str, list[str]], repo: Path | None, route_map) -> tuple[list[str], str]:
    hit = manual.get(f"{f.file}:{f.line}") or manual.get(f.file)
    if hit:
        return hit, "routes file"
    if repo is not None:
        return routes_for(repo, route_map, f.file, f.line)
    return [], "no --repo or routes file given"


def endpoint_selection(routes: list[str]):
    """Exact match for fixed paths (with and without trailing slash); prefix match
    for parameterized paths such as /challenge/<str:name>."""
    exact, prefix = set(), set()
    for r in routes:
        if "<" in r or "(" in r:
            prefix.add(re.split(r"[<(]", r)[0])
        else:
            base = r.rstrip("/") or "/"
            exact.update({base, base + "/"} if base != "/" else {"/"})
    parts = []
    if exact:
        parts.append({"cs-uri-stem": sorted(exact)})
    if prefix:
        parts.append({"cs-uri-stem|startswith": sorted(prefix)})
    return parts[0] if len(parts) == 1 else parts


def build_rule(f: Finding, det: Detector, routes: list[str], author: str) -> dict:
    selection = {f"{det.field}|{det.modifier}": det.values}
    detection: dict = {"selection_payload": selection}
    condition = "selection_payload"
    if det.parent_field:
        detection["selection_parent"] = {f"{det.parent_field}|endswith": det.parent_values}
        condition = "selection_parent and selection_payload"
    if routes and det.route_scoped:
        detection["selection_endpoint"] = endpoint_selection(routes)
        condition = f"selection_endpoint and {condition}"
    detection["condition"] = condition

    scope = f"endpoint(s) {', '.join(routes)}" if (routes and det.route_scoped) else (
        "the application runtime" if not det.route_scoped else "all endpoints (no route mapped)")
    return {
        "title": (f"Exploit attempt ({ANGLE.get(det.logsource.get('category'), 'signal')}): "
                  f"{f.title}")[:140],
        "id": str(uuid.uuid5(NAMESPACE, f"{f.finding_id}:{det.name}")),
        "status": "experimental",
        "description": (
            f"Generated from VVAH finding {f.finding_id} ({f.cwe_id}) at {f.file}:{f.line}. "
            f"Watches {scope} for exploitation of a known, unpatched weakness. "
            f"Retire this rule once the fix is deployed."
        ),
        "references": [f"https://cwe.mitre.org/data/definitions/{f.cwe_id.split('-')[1]}.html"],
        "author": author,
        "date": dt.date.today().strftime("%Y-%m-%d"),
        "tags": det.attack_tags,
        "logsource": det.logsource,
        "detection": detection,
        "falsepositives": det.falsepositives,
        "level": LEVELS.get(f.severity, "medium"),
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def convert(sarif_path: Path, out_dir: Path, routes_path: Path | None = None,
            min_confidence: float = 0.0, author: str = "vvah-to-sigma",
            repo: Path | None = None) -> dict:
    findings = load_findings(sarif_path)
    manual = load_routes(routes_path)
    route_map = build_route_map(repo) if repo else {}
    rules_dir = out_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    rows, written = [], 0
    shared: dict[str, dict] = {}
    for f in findings:
        strat = strategy_for(f.cwe_id)
        skipped_low_conf = f.confidence is not None and f.confidence < min_confidence
        routes, route_how = route_for(f, manual, repo, route_map)
        files: list[str] = []
        channels = input_channels(repo, f.file, f.line) if repo else set()
        body_only = bool(channels) and "query" not in channels
        blind: list[str] = []
        if strat.bucket == RULE and not skipped_low_conf:
            for det in strat.detectors:
                if det.field == "cs-uri-query" and body_only:
                    blind.append(det.name)
                    continue
                if not (routes and det.route_scoped):
                    entry = shared.setdefault(det.name, {"det": det, "findings": []})
                    entry["findings"].append(f)
                    files.append(f"shared_{_slug(det.name)}.yml")
                    continue
                rule = build_rule(f, det, routes, author)
                name = f"{_slug(f.cwe_id or 'unknown')}_{_slug(det.name)}_{f.finding_id[:8]}.yml"
                (rules_dir / name).write_text(yaml.safe_dump(rule, sort_keys=False, allow_unicode=True),
                                              encoding="utf-8")
                files.append(name)
                written += 1
        web_scoped = any(d.route_scoped for d in strat.detectors)
        rows.append({"finding": f, "bucket": strat.bucket, "note": strat.note, "routes": routes,
                     "channels": sorted(channels), "blind": blind,
                     "route_how": route_how,
                     "web_scoped": web_scoped,
                     "rules": files, "skipped_low_conf": skipped_low_conf})

    sev_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    for det_name, entry in shared.items():
        fs = sorted(entry["findings"], key=lambda x: sev_rank.get(x.severity, 5))
        rule = build_rule(fs[0], entry["det"], [], author)
        rule["title"] = (f"Exploit attempt ({ANGLE.get(entry['det'].logsource.get('category'), 'signal')}): "
                         f"{det_name.replace('_', ' ')} ({len(fs)} finding{'s' if len(fs) > 1 else ''})")
        rule["id"] = str(uuid.uuid5(NAMESPACE, f"shared:{det_name}"))
        rule["description"] = (
            "App-wide rule covering these VVAH findings: "
            + "; ".join(f"{x.finding_id} {x.cwe_id} {x.file}:{x.line}" for x in fs)
            + ". Retire when all are fixed.")
        rule["references"] = sorted({f"https://cwe.mitre.org/data/definitions/{x.cwe_id.split('-')[1]}.html"
                                     for x in fs if x.cwe_id})
        (rules_dir / f"shared_{_slug(det_name)}.yml").write_text(
            yaml.safe_dump(rule, sort_keys=False, allow_unicode=True), encoding="utf-8")
        written += 1

    report = render_coverage(rows, sarif_path, min_confidence)
    (out_dir / "coverage.md").write_text(report, encoding="utf-8")
    return {"findings": len(findings), "rules": written,
            "web_rules_skipped_body_only": sum(len(r["blind"]) for r in rows),
            "rule_bucket_with_no_rule": sum(1 for r in rows if r["bucket"] == RULE and not r["rules"]),
            "by_bucket": {b: sum(1 for r in rows if r["bucket"] == b)
                          for b in (RULE, BEHAVIORAL, UNCOVERABLE, UNMAPPED)}}


def render_coverage(rows: list[dict], sarif_path: Path, min_conf: float) -> str:
    total = len(rows)
    covered = [r for r in rows if r["rules"]]
    lines = [
        "# Detection coverage for VVAH findings", "",
        f"Source: `{sarif_path.name}`  ",
        f"Findings: {total} · with at least one rule: {len(covered)} · "
        f"rules written: {sum(len(r['rules']) for r in rows)}", "",
        "Every finding is listed. A finding without a rule is not an oversight; "
        "the reason column says why a log signature cannot cover it.", "",
        "| # | Severity | CWE | Finding | Location | Bucket | Rules | Why |",
        "|---|---|---|---|---|---|---|---|",
    ]
    order = {RULE: 0, BEHAVIORAL: 1, UNCOVERABLE: 2, UNMAPPED: 3}
    sev = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    for i, r in enumerate(sorted(rows, key=lambda r: (order[r["bucket"]], sev.get(r["finding"].severity, 5))), 1):
        f = r["finding"]
        why = r["note"]
        if r["skipped_low_conf"]:
            why = f"Confidence {f.confidence} below threshold {min_conf}. " + why
        if r["blind"]:
            why += (f" Input arrives via {'/'.join(r['channels'])}, not the query string, so access logs "
                    f"cannot see the payload; skipped {len(r['blind'])} query-string rule(s). "
                    "Needs WAF or request-body logging" + (", or rely on the process rule." if r["rules"] else "."))
        if r["rules"] and r["web_scoped"] and not r["blind"]:
            why += (f" Scoped to {', '.join(r['routes'])} ({r['route_how']})." if r["routes"]
                    else f" Unscoped, watches all endpoints ({r['route_how']}).")
        lines.append(f"| {i} | {f.severity} | {f.cwe_id or '-'} | {f.title} | `{f.file}:{f.line}` | "
                     f"{r['bucket']} | {len(r['rules'])} | {why} |")
    lines += ["", "Buckets: **rule** = log signature exists; **behavioral** = needs baselining or "
              "correlation; **uncoverable** = no request-time signal, the fix is the only control; "
              "**unmapped** = no mapping yet, review manually.", ""]
    return "\n".join(lines)
