import argparse
import json
from pathlib import Path

from .adapters import dedupe, load_grype, load_mapped_csv, load_product_csv, load_trivy
from .analyze import analyze
from .feeds import EpssFeed, KevFeed, MappedFeed
from .report import write
from .rulesets import ForeignRuleset, Ruleset


def main() -> None:
    ap = argparse.ArgumentParser(prog="exposure_to_sigma",
                                 description="Which exploited CVEs do you have, and can you detect them?")
    ap.add_argument("--kev", type=Path, required=True, help="CISA KEV JSON (known_exploited_vulnerabilities.json)")
    ap.add_argument("--trivy", type=Path, action="append", default=[], help="Trivy JSON (repeatable)")
    ap.add_argument("--grype", type=Path, action="append", default=[], help="Grype JSON (repeatable)")
    ap.add_argument("--asset", default="app", help="asset name for --trivy/--grype/--mapped-csv inputs")
    ap.add_argument("--logs", default="", help="log sources that asset sends, comma-separated")
    ap.add_argument("--inventory", type=Path, help="product CSV: asset,vendor,product,version,logs")
    ap.add_argument("--mapped-csv", type=Path, nargs=2, metavar=("CSV", "MAPPING"), action="append",
                    default=[], help="any scanner export plus its column mapping")
    ap.add_argument("--epss", type=Path, help="FIRST EPSS CSV (optionally .gz)")
    ap.add_argument("--epss-from-grype", action="store_true", help="use EPSS scores embedded in --grype output")
    ap.add_argument("--feed", type=Path, nargs=2, metavar=("EXPORT", "MAPPING"), action="append", default=[],
                    help="paid threat-intel export plus its field mapping")
    ap.add_argument("--own-rules", type=Path, action="append", default=[], help="your Sigma rules folder")
    ap.add_argument("--public-rules", type=Path, action="append", default=[], help="e.g. a SigmaHQ checkout")
    ap.add_argument("--other-rules", type=Path, action="append", default=[],
                    help="non-Sigma detection repos: Splunk security_content/detections, elastic/detection-rules/rules, "
                         "chronicle/detection-rules (matched by CVE only)")
    ap.add_argument("--likely", type=float, default=0.1, help="EPSS threshold to prioritise unconfirmed CVEs")
    ap.add_argument("--exploited-only", action="store_true",
                    help="judge only exploited or likely CVEs (default: every CVE, ordered by exploitation)")
    ap.add_argument("--out", type=Path, default=Path("out"))
    a = ap.parse_args()

    kev = KevFeed(a.kev)
    feeds = [kev]
    if a.epss:
        feeds.append(EpssFeed.from_first_csv(a.epss))
    if a.epss_from_grype:
        for g in a.grype:
            feeds.append(EpssFeed.from_grype(g))
    feeds += [MappedFeed(p, m) for p, m in a.feed]

    exposures = []
    for p in a.trivy:
        exposures += load_trivy(p, a.asset, a.logs)
    for p in a.grype:
        exposures += load_grype(p, a.asset, a.logs)
    for p, m in a.mapped_csv:
        exposures += load_mapped_csv(p, m, a.logs)
    if a.inventory:
        exposures += load_product_csv(a.inventory, kev.catalog)
    exposures = dedupe(exposures)

    own = [Ruleset(f"yours:{p.name}", p) for p in a.own_rules]
    public = [Ruleset(f"public:{p.name}", p) for p in a.public_rules]
    other = [ForeignRuleset(f"other:{p.name}", p) for p in a.other_rules]
    verdicts = analyze(exposures, feeds, own, public, a.likely, other, a.exploited_only)
    meta = {"CISA KEV catalog": kev.version,
            "Feeds": ", ".join(getattr(f, "source", f.name) for f in feeds),
            "Rulesets": ", ".join(f"{r.name} ({len(r.rules)} rules)" for r in own + public + other) or "none"}
    print(json.dumps(write(verdicts, meta, a.out), indent=2))


if __name__ == "__main__":
    main()
