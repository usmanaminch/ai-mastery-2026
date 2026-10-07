"""Join exposures x exploitation feeds x rulesets x collected logs into one verdict per exposure."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Exposure, ExploitSignal, RuleRef
from .rulesets import NO_SIGNATURE as NO_SIG_CWES, Ruleset, collected

# Verdicts, best first.
DETECTED = "Detected by your rules"
DEPLOY_PUBLIC = "Public rule available: deploy it"
OTHER_FORMAT = "Public rule in another format (SPL, KQL, YARA-L): translate it"
GENERIC = "Generic coverage likely (heuristic)"
YOURS_NO_LOGS = "Your rule exists, but its logs are not collected"
PUBLIC_NO_LOGS = "Public rule exists, but its logs are not collected"
NO_SIGNATURE = "No log signature for this weakness (e.g. denial of service): patch"
GAP = "Gap: no rule names it; draft a scoped rule"
ORDER = [DETECTED, DEPLOY_PUBLIC, OTHER_FORMAT, GENERIC, YOURS_NO_LOGS, PUBLIC_NO_LOGS, NO_SIGNATURE, GAP]


@dataclass
class Verdict:
    exposure: Exposure
    signals: list[ExploitSignal]
    priority: str                         # exploited | likely | low
    verdict: str = ""
    rules: list[RuleRef] = field(default_factory=list)

    @property
    def probability(self) -> float | None:
        ps = [s.probability for s in self.signals if s.probability is not None]
        return max(ps) if ps else None

    @property
    def ransomware(self) -> bool:
        return any(s.ransomware for s in self.signals)


def analyze(exposures: list[Exposure], feeds: list, own: list[Ruleset], public: list[Ruleset],
            likely_threshold: float = 0.1, other: list | None = None,
            exploited_only: bool = False) -> list[Verdict]:
    """Give every exposure a coverage verdict. Exploitation data (KEV, EPSS) sets the priority, which
    orders the work; it doesn't decide what gets a verdict, because what isn't exploited today may be
    tomorrow. exploited_only=True restores the old behaviour: low-priority exposures are only counted."""
    out = []
    for e in exposures:
        signals = [s for s in (f.lookup(e.cve) for f in feeds) if s]
        for s in signals:
            e.cwes = sorted(set(e.cwes) | set(s.cwes))
        if any(s.exploited for s in signals):
            prio = "exploited"
        elif any((s.probability or 0) >= likely_threshold for s in signals):
            prio = "likely"
        else:
            prio = "low"
        v = Verdict(e, signals, prio)
        if prio != "low" or not exploited_only:
            _judge(v, own, public, other or [])
        out.append(v)
    return out


def _judge(v: Verdict, own: list[Ruleset], public: list[Ruleset], other: list) -> None:
    e = v.exposure
    candidates: list[tuple[str, RuleRef]] = []
    for rs in own:
        for r in rs.specific(e.cve):
            candidates.append((DETECTED if collected(r, e.logs) else YOURS_NO_LOGS, r))
    for rs in public:
        for r in rs.specific(e.cve):
            candidates.append((DEPLOY_PUBLIC if collected(r, e.logs) else PUBLIC_NO_LOGS, r))
    if not candidates:
        # Only when no Sigma rule names the CVE: a "logs not collected" verdict is the more useful
        # finding, and an SPL or KQL rule for it would need the same logs.
        for rs in other:
            for r in rs.specific(e.cve):
                candidates.append((OTHER_FORMAT, r))
    if not any(c[0] in (DETECTED, DEPLOY_PUBLIC, OTHER_FORMAT) for c in candidates):
        for rs in own + public:
            for r in rs.generic(e.cwes, exploited=v.priority == "exploited"):
                if collected(r, e.logs):
                    candidates.append((GENERIC, r))
    if not candidates:
        v.verdict = NO_SIGNATURE if e.cwes and set(e.cwes) <= NO_SIG_CWES else GAP
        return
    best = min(ORDER.index(c[0]) for c in candidates)
    v.verdict = ORDER[best]
    v.rules = [r for verdict, r in candidates if ORDER.index(verdict) == best]
