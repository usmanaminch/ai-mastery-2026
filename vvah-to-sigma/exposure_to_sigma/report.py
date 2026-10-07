from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .analyze import ORDER, Verdict


def render(verdicts: list[Verdict], meta: dict) -> str:
    prio = [v for v in verdicts if v.verdict]
    skipped = len(verdicts) - len(prio)
    lines = ["# Exposure-to-detection coverage", ""]
    lines += [f"- {k}: {v}" for k, v in meta.items()]
    lines += ["", f"**{len(verdicts)}** CVE exposures in: {sum(v.priority == 'exploited' for v in verdicts)} confirmed "
              f"exploited, {sum(v.priority == 'likely' for v in verdicts)} likely by probability, "
              f"{sum(v.priority == 'low' for v in verdicts)} not known to be exploited. Every exposure gets a verdict; "
              "exploitation sets the order, because what isn't exploited today may be tomorrow."
              + (f" ({skipped} low-priority exposures counted only: --exploited-only.)" if skipped else ""), "",
              "| Verdict | Exposures |", "|---|---|"]
    c = Counter(v.verdict for v in prio)
    lines += [f"| {k} | {c.get(k, 0)} |" for k in ORDER]
    lines += ["", "## Exposures, exploited first", "",
              "| Asset | CVE | Product | Priority | Verdict | Rules |", "|---|---|---|---|---|---|"]
    key = lambda v: (ORDER.index(v.verdict), v.priority != "exploited", -(v.probability or 0))
    for v in sorted(prio, key=key):
        e = v.exposure
        pr = v.priority + (" (ransomware)" if v.ransomware else "")
        if v.probability is not None:
            pr += f", EPSS {v.probability:.2f}"
        prod = f"{e.vendor} {e.product} {e.version}".strip()
        if not e.version_checked:
            prod += " *(version not checked)*"
        rules = "<br>".join(f"{r.ruleset}: `{r.path}`" for r in v.rules[:3]) or "-"
        if len(v.rules) > 3:
            rules += f"<br>+{len(v.rules) - 3} more"
        lines.append(f"| {e.asset} | {e.cve} | {prod} | {pr} | {v.verdict} | {rules} |")
    lines += ["", "## How to read this", "",
              "- **Detected by your rules / Public rule available:** a rule that names this CVE reads a log "
              "source this asset sends. Deploy or confirm it, and retire it once patched.",
              "- **Public rule in another format:** Splunk, Elastic or Google SecOps content names this CVE. "
              "Deploy it if that's your SIEM, or translate it to Sigma (the drafter does this, grounded in the "
              "source rule). Which logs it reads isn't checked.",
              "- **Generic coverage likely:** no rule names the CVE, but a rule for the same weakness class "
              "(from the CWE) reads a log you collect. A heuristic: test it before relying on it.",
              "- **Rule exists, logs not collected:** the detection exists but can never fire here. "
              "The fix is a log pipeline, not a rule.",
              "- **No log signature:** the weakness (typically denial of service) leaves nothing a rule can "
              "match. Patch; a rule would only add noise.",
              "- **Gap:** nothing public or internal names it and no generic rule applies. These are the "
              "candidates for a drafted, scoped rule.",
              "- *(version not checked)*: matched from an inventory by vendor and product name only. "
              "Confirm the version is affected with a scanner before acting.", ""]
    return "\n".join(lines)


def write(verdicts: list[Verdict], meta: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "coverage-exposures.md").write_text(render(verdicts, meta), encoding="utf-8")
    rows = [{"asset": v.exposure.asset, "cve": v.exposure.cve, "vendor": v.exposure.vendor,
             "product": v.exposure.product, "version": v.exposure.version,
             "version_checked": v.exposure.version_checked, "logs": sorted(v.exposure.logs),
             "source": v.exposure.source, "cwes": v.exposure.cwes,
             "notes": [f"{s.feed}: {s.note}" for s in v.signals if s.note],
             "priority": v.priority, "probability": v.probability, "ransomware": v.ransomware,
             "verdict": v.verdict, "rules": [f"{r.ruleset}:{r.path}" for r in v.rules],
             "rule_files": [{"file": r.file, "format": r.fmt, "ruleset": r.ruleset} for r in v.rules]} for v in verdicts]
    (out_dir / "exposures.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    prio = [v for v in verdicts if v.verdict]
    return {"exposures": len(verdicts), "judged": len(prio),
            "verdicts": dict(Counter(v.verdict for v in prio))}
