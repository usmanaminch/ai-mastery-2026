"""Ruleset coverage analysis.

Point it at any number of Sigma rule folders: SigmaHQ, your own detections-as-code,
a vendor content pack. For each CVE it reports, per folder:

  specific  a rule names the CVE (in tags like cve.2023-1234, title, or references)
  generic   no rule names it, but a rule targets the same weakness class (by CWE) on the
            same kind of log; a heuristic, labelled as such
  none      neither

Native SIEM rule formats (Splunk SPL, YARA-L, KQL) are out of scope: reading what an
untagged native query detects is a separate problem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import RuleRef

CVE_ANY = re.compile(r"CVE[-.](\d{4})[-.](\d{4,7})", re.I)

# Weakness class -> how to recognise a generic rule for it: (allowed log categories, title regex).
# None for categories means any log source.
GENERIC: dict[str, tuple[set[str] | None, str]] = {
    "path_traversal": ({"webserver", "proxy"}, r"traversal"),
    "sql_injection": ({"webserver", "proxy", "database"}, r"sql.?injection"),
    "xss": ({"webserver", "proxy"}, r"\bxss\b|cross.?site"),
    "template_injection": ({"webserver", "proxy"}, r"\bssti\b|template"),
    "deserialization": (None, r"deserializ|java payload|ognl|jndi"),
    # Post-exploitation on the host: a web/app server spawning a shell. Deliberately excludes
    # rules that merely mention a web server (e.g. "Python WebServer Execution").
    "code_execution": ({"process_creation"}, r"web ?shell|by web ?server process|spawned from (a )?web|web rce"),
    "ssrf": ({"webserver", "proxy"}, r"\bssrf\b|server.?side request"),
}

# Memory-corruption CWEs. Many are denial-of-service only (and NVD tags some memory-safe
# Python bugs this way), so they count as code execution only when exploitation is confirmed.
MEMORY_CORRUPTION = {"CWE-787", "CWE-119", "CWE-120", "CWE-122", "CWE-416", "CWE-190", "CWE-125"}

# Weaknesses with no request-time log signature: denial of service and resource exhaustion.
NO_SIGNATURE = {"CWE-400", "CWE-770", "CWE-130", "CWE-1333", "CWE-674", "CWE-834", "CWE-407",
                "CWE-1050", "CWE-405", "CWE-409", "CWE-776"}

CWE_CLASS = {
    "CWE-22": "path_traversal", "CWE-23": "path_traversal", "CWE-35": "path_traversal",
    "CWE-89": "sql_injection", "CWE-79": "xss", "CWE-1336": "template_injection",
    "CWE-502": "deserialization", "CWE-917": "deserialization",
    "CWE-77": "code_execution", "CWE-78": "code_execution", "CWE-94": "code_execution",
    "CWE-95": "code_execution", "CWE-434": "code_execution",
    "CWE-918": "ssrf",
}


@dataclass
class _Rule:
    path: str
    title: str
    logsource: dict
    cves: set[str]
    text_lower: str


class Ruleset:
    def __init__(self, name: str, folder: Path):
        self.name, self.folder = name, Path(folder)
        self.rules: list[_Rule] = []
        self.by_cve: dict[str, list[_Rule]] = {}
        for f in sorted(self.folder.rglob("*.yml")) + sorted(self.folder.rglob("*.yaml")):
            text = f.read_text(encoding="utf-8", errors="replace")
            try:
                docs = [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]
            except yaml.YAMLError:
                continue
            if not docs or "detection" not in docs[0] and "title" not in docs[0]:
                continue
            d = docs[0]
            cves = {f"CVE-{a}-{b}" for a, b in CVE_ANY.findall(text)}
            rule = _Rule(path=str(f.relative_to(self.folder)), title=str(d.get("title", "")),
                         logsource=d.get("logsource") or {}, cves=cves, text_lower=str(d.get("title", "")).lower())
            self.rules.append(rule)
            for c in cves:
                self.by_cve.setdefault(c, []).append(rule)

    def specific(self, cve: str) -> list[RuleRef]:
        return [RuleRef(self.name, r.path, r.title, r.logsource, "specific")
                for r in self.by_cve.get(cve.upper(), [])]

    def generic(self, cwes: list[str], exploited: bool = False) -> list[RuleRef]:
        classes = {CWE_CLASS[c] for c in cwes if c in CWE_CLASS}
        if exploited and MEMORY_CORRUPTION & set(cwes):
            classes.add("code_execution")
        hits = []
        for cls in sorted(classes):
            cats, rx = GENERIC[cls]
            for r in self.rules:
                cat = (r.logsource.get("category") or "").lower()
                if cats is not None and cat not in cats:
                    continue
                if re.search(rx, r.text_lower):
                    hits.append(RuleRef(self.name, r.path, r.title, r.logsource, "generic"))
        return hits


def log_tokens(logsource: dict) -> set[str]:
    """The tokens an asset's `logs` list can use to say 'we collect this'.
    Examples: webserver, process_creation:linux, process_creation:windows, fortios, cisco:asa."""
    cat = (logsource.get("category") or "").lower()
    prod = (logsource.get("product") or "").lower()
    svc = (logsource.get("service") or "").lower()
    toks = set()
    if cat and prod:
        toks.add(f"{cat}:{prod}")
    elif cat:
        toks.add(cat)
    if prod and svc:
        toks.add(f"{prod}:{svc}")
    elif prod and not cat:
        toks.add(prod)
    if svc and not prod:
        toks.add(svc)
    return toks


def collected(rule: RuleRef, asset_logs: set[str]) -> bool:
    """True if the asset sends the log source this rule reads. An asset entry without an
    OS qualifier ("process_creation") covers any OS; with one, it must match."""
    need = log_tokens(rule.logsource)
    return bool(need & asset_logs) or bool({t.split(":")[0] for t in need} & asset_logs)
