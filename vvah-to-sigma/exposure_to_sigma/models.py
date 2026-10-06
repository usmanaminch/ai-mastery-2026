"""Common records every adapter, feed and ruleset produces, so the analysis never
cares where the data came from."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Exposure:
    """One CVE on one asset."""
    asset: str
    cve: str
    vendor: str = ""
    product: str = ""
    version: str = ""
    fixed_version: str = ""
    source: str = ""                      # which adapter produced it
    cwes: list[str] = field(default_factory=list)
    logs: set[str] = field(default_factory=set)   # log sources this asset sends to the SIEM
    version_checked: bool = True          # False when matched by product name only


@dataclass
class ExploitSignal:
    """What a feed says about a CVE."""
    feed: str
    exploited: bool = False               # confirmed exploitation in the wild
    probability: float | None = None      # e.g. EPSS, 0..1
    ransomware: bool = False
    cwes: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class RuleRef:
    ruleset: str
    path: str
    title: str
    logsource: dict
    match: str                            # "specific" or "generic"
