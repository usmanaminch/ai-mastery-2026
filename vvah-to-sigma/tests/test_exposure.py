from pathlib import Path

from exposure_to_sigma.adapters import dedupe, load_grype, load_product_csv, load_trivy
from exposure_to_sigma.analyze import (DEPLOY_PUBLIC, DETECTED, GAP, GENERIC, NO_SIGNATURE,
                                       PUBLIC_NO_LOGS, YOURS_NO_LOGS, analyze)
from exposure_to_sigma.feeds import EpssFeed, KevFeed
from exposure_to_sigma.rulesets import Ruleset

F = Path(__file__).parent / "fixtures" / "exposure"
EXCO = Path(__file__).parent.parent / "examples" / "example-corp"


def _feeds():
    return [KevFeed(F / "kev-small.json"), EpssFeed.from_grype(F / "grype-small.json")]


def test_trivy_and_grype_agree_and_dedupe():
    t = load_trivy(F / "trivy-small.json", "app", "webserver")
    g = load_grype(F / "grype-small.json", "app", "webserver")
    assert {e.cve for e in t} == {e.cve for e in g} == {"CVE-2023-4863", "CVE-2023-46695", "CVE-2025-64459"}
    merged = dedupe(t + g)
    assert len({(e.asset, e.cve) for e in merged}) == 3
    assert any("trivy" in e.source and "grype" in e.source for e in merged)


def test_exploited_library_cve_gets_post_exploitation_coverage_only_when_confirmed():
    ex = dedupe(load_grype(F / "grype-small.json", "app", "webserver,process_creation:linux"))
    v = {x.exposure.cve: x for x in analyze(ex, _feeds(), [], [Ruleset("public", F / "sigma")])}
    assert v["CVE-2023-4863"].priority == "exploited" and v["CVE-2023-4863"].verdict == GENERIC
    assert v["CVE-2023-46695"].verdict == NO_SIGNATURE          # CWE-770, denial of service
    assert v["CVE-2025-64459"].verdict == GENERIC               # CWE-89 -> SQL injection rule


def test_no_logs_means_no_generic_coverage():
    ex = dedupe(load_grype(F / "grype-small.json", "app", ""))
    v = {x.exposure.cve: x for x in analyze(ex, _feeds(), [], [Ruleset("public", F / "sigma")])}
    assert v["CVE-2023-4863"].verdict == GAP


def test_inventory_verdicts_cover_yours_public_and_missing_logs():
    kev = KevFeed(F / "kev-small.json")
    ex = load_product_csv(F / "inventory.csv", kev.catalog)
    assert all(not e.version_checked for e in ex)
    v = {(x.exposure.asset, x.exposure.cve): x.verdict for x in
         analyze(ex, [kev], [Ruleset("yours", EXCO / "rules")], [Ruleset("public", F / "sigma")])}
    assert v[("wiki-01", "CVE-2022-26134")] == DETECTED
    assert v[("wiki-01", "CVE-2023-22518")] == DEPLOY_PUBLIC
    assert v[("vpn-gw-01", "CVE-2022-42475")] == YOURS_NO_LOGS


def test_public_rule_without_logs_is_flagged_not_counted():
    kev = KevFeed(F / "kev-small.json")
    ex = load_product_csv(F / "inventory.csv", kev.catalog)
    v = {(x.exposure.asset, x.exposure.cve): x.verdict for x in
         analyze(ex, [kev], [], [Ruleset("public", F / "sigma")])}
    assert v[("vpn-gw-01", "CVE-2022-42475")] == PUBLIC_NO_LOGS
