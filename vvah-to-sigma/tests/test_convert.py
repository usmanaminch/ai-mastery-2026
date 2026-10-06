from pathlib import Path

import yaml

from vvah_to_sigma.convert import convert, load_findings
from vvah_to_sigma.cwe_map import BEHAVIORAL, RULE, UNCOVERABLE, UNMAPPED, strategy_for

FIX = Path(__file__).parent / "fixtures"
SARIF = FIX / "pygoat_synthetic.sarif"


def test_loads_every_finding_with_cwe_and_location():
    findings = load_findings(SARIF)
    assert len(findings) == 9
    assert all(f.cwe_id and f.cwe_id.startswith("CWE-") for f in findings)
    sqli = next(f for f in findings if f.cwe_id == "CWE-89")
    assert sqli.file == "introduction/views.py" and sqli.line == 120


def test_buckets_are_honest():
    assert strategy_for("CWE-89").bucket == RULE
    assert strategy_for("CWE-639").bucket == BEHAVIORAL
    assert strategy_for("CWE-798").bucket == UNCOVERABLE
    assert strategy_for("CWE-99999").bucket == UNMAPPED
    assert strategy_for(None).bucket == UNMAPPED


def test_every_finding_appears_in_coverage_report(tmp_path):
    summary = convert(SARIF, tmp_path, FIX / "routes.example.yaml")
    report = (tmp_path / "coverage.md").read_text()
    for f in load_findings(SARIF):
        assert f"{f.file}:{f.line}" in report
    assert summary["findings"] == 9
    assert summary["by_bucket"][UNCOVERABLE] == 2


def test_route_scopes_web_rules_but_not_process_rules(tmp_path):
    convert(SARIF, tmp_path, FIX / "routes.example.yaml")
    rules = {p.name: yaml.safe_load(p.read_text()) for p in (tmp_path / "rules").glob("*.yml")}
    web = next(r for n, r in rules.items() if n.startswith("cwe_78_cmdi_payload"))
    proc = rules["shared_app_runtime_child_shell.yml"]
    assert web["detection"]["selection_endpoint"] == {"cs-uri-stem": ["/cmd_lab", "/cmd_lab/"]}
    assert "selection_endpoint" not in proc["detection"]
    assert proc["logsource"]["category"] == "process_creation"


def test_rule_ids_are_stable_across_runs(tmp_path):
    convert(SARIF, tmp_path / "a")
    convert(SARIF, tmp_path / "b")
    ids = lambda d: sorted(yaml.safe_load(p.read_text())["id"] for p in (d / "rules").glob("*.yml"))
    assert ids(tmp_path / "a") == ids(tmp_path / "b")


def test_min_confidence_suppresses_rules_but_keeps_finding_in_report(tmp_path):
    summary = convert(SARIF, tmp_path, min_confidence=0.99)
    assert summary["rules"] == 0
    assert "below threshold" in (tmp_path / "coverage.md").read_text()


def test_django_route_derivation():
    from vvah_to_sigma.routes import build_route_map, routes_for
    repo = FIX / "minidjango"
    m = build_route_map(repo)
    assert routes_for(repo, m, "app/views.py", 11)[0] == ["/sql_lab"]
    assert routes_for(repo, m, "app/views.py", 9)[0] == ["/sql_lab"]
    assert routes_for(repo, m, "app/views.py", 5)[0] == ["/register"]
    assert routes_for(repo, m, "app/views.py", 15)[0] == ["/shop/cart"]
    assert routes_for(repo, m, "app/views.py", 20)[0] == ["/item/<int:pk>"]
    assert routes_for(repo, m, "Dockerfile", 1)[0] == []


def test_parameterized_route_becomes_prefix_match():
    from vvah_to_sigma.convert import endpoint_selection
    assert endpoint_selection(["/item/<int:pk>"]) == {"cs-uri-stem|startswith": ["/item/"]}
    both = endpoint_selection(["/a", "/item/<int:pk>"])
    assert {"cs-uri-stem": ["/a", "/a/"]} in both and {"cs-uri-stem|startswith": ["/item/"]} in both


def test_input_channel_detection():
    from vvah_to_sigma.routes import input_channels
    repo = FIX / "minidjango"
    assert input_channels(repo, "app/views.py", 11) == {"query"}
    assert input_channels(repo, "app/views.py", 25) == {"body"}
    assert input_channels(repo, "Dockerfile", 1) == set()


def test_app_wide_rules_are_merged_not_duplicated(tmp_path):
    convert(SARIF, tmp_path, FIX / "routes.example.yaml")
    names = [p.name for p in (tmp_path / "rules").glob("*.yml")]
    assert sum(n.startswith("shared_") for n in names) == len({n for n in names if n.startswith("shared_")})
    shared = yaml.safe_load((tmp_path / "rules" / "shared_app_runtime_child_shell.yml").read_text())
    assert "CWE-502" in shared["description"] and "CWE-78" in shared["description"]
