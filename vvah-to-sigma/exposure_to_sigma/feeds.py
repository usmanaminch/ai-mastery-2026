"""Exploitation feeds. Each answers: is this CVE being exploited, and how likely?

Shipped: CISA KEV (free), FIRST EPSS (free, from FIRST's daily CSV or from the
scores Grype embeds in its output), and a mapped feed for paid threat intel
exports. A paid API connector would implement the same interface:
    feed.lookup(cve) -> ExploitSignal | None
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import re
from pathlib import Path

import yaml

from .models import ExploitSignal


class KevFeed:
    name = "cisa-kev"

    def __init__(self, path: Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.catalog = data["vulnerabilities"]
        self.version = data.get("catalogVersion", "")
        self._by_cve = {v["cveID"].upper(): v for v in self.catalog}

    def lookup(self, cve: str) -> ExploitSignal | None:
        v = self._by_cve.get(cve.upper())
        if not v:
            return None
        return ExploitSignal(feed=self.name, exploited=True,
                             ransomware=v.get("knownRansomwareCampaignUse", "").lower() == "known",
                             cwes=list(v.get("cwes") or []),
                             note=f"added {v.get('dateAdded', '')}: {v.get('vulnerabilityName', '')}")


class EpssFeed:
    """FIRST EPSS: probability a CVE is exploited in the next 30 days."""
    name = "epss"

    def __init__(self, scores: dict[str, float], source: str):
        self.scores, self.source = scores, source

    @classmethod
    def from_first_csv(cls, path: Path) -> "EpssFeed":
        raw = Path(path).read_bytes()
        text = gzip.decompress(raw).decode() if raw[:2] == b"\x1f\x8b" else raw.decode()
        lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
        scores = {r["cve"].upper(): float(r["epss"]) for r in csv.DictReader(io.StringIO("\n".join(lines)))}
        return cls(scores, f"FIRST EPSS file {Path(path).name}")

    @classmethod
    def from_grype(cls, path: Path) -> "EpssFeed":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        scores = {}
        for m in data.get("matches", []):
            for e in m.get("vulnerability", {}).get("epss") or []:
                scores[e["cve"].upper()] = float(e["epss"])
        return cls(scores, "EPSS scores embedded by Grype")

    def lookup(self, cve: str) -> ExploitSignal | None:
        p = self.scores.get(cve.upper())
        return None if p is None else ExploitSignal(feed=self.name, probability=p)


class MappedFeed:
    """A paid threat-intel export (CSV or JSON list), described by a YAML mapping:

        format: csv                # or json
        source: vendor-intel       # label for the report
        fields:
          cve: "cve_id"            # required
          exploited: "exploited"   # optional; truthy values: true/yes/1/confirmed
          probability: "score"     # optional; 0..1 (or 0..100, auto-scaled)
          note: "summary"          # optional
    """

    def __init__(self, path: Path, mapping_path: Path):
        spec = yaml.safe_load(Path(mapping_path).read_text(encoding="utf-8"))
        self.name, f = spec.get("source", "mapped-feed"), spec["fields"]
        if spec.get("format", "csv") == "json":
            rows = json.loads(Path(path).read_text(encoding="utf-8"))
        else:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                rows = list(csv.DictReader(fh))
        self._by_cve = {}
        for r in rows:
            cve = str(r.get(f["cve"], "")).upper()
            if not re.fullmatch(r"CVE-\d{4}-\d{4,7}", cve):
                continue
            prob = r.get(f.get("probability", ""), None) if f.get("probability") else None
            prob = float(prob) if prob not in (None, "") else None
            if prob is not None and prob > 1:
                prob /= 100
            exploited = str(r.get(f.get("exploited", ""), "")).strip().lower() in ("true", "yes", "1", "confirmed")
            self._by_cve[cve] = ExploitSignal(feed=self.name, exploited=exploited, probability=prob,
                                              note=str(r.get(f.get("note", ""), "")) if f.get("note") else "")

    def lookup(self, cve: str) -> ExploitSignal | None:
        return self._by_cve.get(cve.upper())
