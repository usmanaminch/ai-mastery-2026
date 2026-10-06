import json
from pathlib import Path

import yaml

from exposure_to_sigma import draft as D

F = Path(__file__).parent / "fixtures" / "exposure"


class FakeClient:
    usage = None

    def __init__(self, reply):
        self.reply, self.prompts = reply, []

    def complete(self, system, user):
        self.prompts.append(user)
        return "```json\n" + json.dumps(self.reply) + "\n```"


def _exposures(tmp_path, logs):
    rows = [
        {"asset": "edge-01", "cve": "CVE-2099-0001", "vendor": "Example", "product": "ExampleOS",
         "version": "", "logs": logs, "cwes": ["CWE-420"], "notes": [], "priority": "exploited",
         "probability": None, "ransomware": False, "verdict": "Gap: no rule names it; draft a scoped rule"},
        {"asset": "edge-02", "cve": "CVE-2099-0001", "vendor": "Example", "product": "ExampleOS",
         "version": "", "logs": [], "cwes": [], "notes": [], "priority": "exploited",
         "probability": None, "ransomware": True, "verdict": "Gap: no rule names it; draft a scoped rule"},
        {"asset": "app", "cve": "CVE-2099-0002", "priority": "exploited", "logs": [],
         "verdict": "Public rule available: deploy it"},
        {"asset": "app", "cve": "CVE-2099-0003", "priority": "low", "logs": [], "verdict": ""},
    ]
    p = tmp_path / "exposures.json"
    p.write_text(json.dumps(rows))
    return p


RULE_REPLY = {
    "verdict": "rule", "vuln_class": "auth bypass creating admin account", "cwe_agrees": True,
    "reason": "Advisory names the endpoint and parameter.",
    "rule": {"title": "ExampleOS Web UI admin creation", "description": "Exploit request.",
             "logsource": {"category": "webserver"},
             "detection": {"selection": {"cs-uri-stem|endswith": "/webui/logoutconfirm.html",
                                         "cs-uri-query|contains": ["logon_hash=1", "evil_param"]},
                           "condition": "selection"},
             "falsepositives": ["Unlikely"], "level": "critical", "tags": ["attack.initial_access", "bad tag"]},
}


def test_only_prioritised_gaps_are_drafted_and_grouped_by_cve(tmp_path):
    gaps = D.load_gaps(_exposures(tmp_path, ["webserver"]))
    assert [g.cve for g in gaps] == ["CVE-2099-0001"]
    assert sorted(gaps[0].assets) == ["edge-01", "edge-02"] and gaps[0].ransomware


def test_draft_is_checked_not_trusted(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    adv = D.advisory_for(gap, {}, F / "advisories", fetch=False)
    d = D.draft_one(gap, FakeClient(RULE_REPLY), "fake-model", adv, tmp_path / "rules")
    assert d.verdict == "rule" and d.logs_ok
    assert d.ungrounded == ["evil_param"]
    assert d.status.startswith("review:") and "ungrounded" in d.status
    rule = yaml.safe_load((tmp_path / d.file).read_text())
    assert rule["status"] == "experimental" and "cve.2099-0001" in rule["tags"]
    assert "bad tag" not in rule["tags"] and "DRAFT" in rule["description"]
    assert rule["id"] == D.finalize(RULE_REPLY["rule"], gap, "x")["id"]


def test_rule_for_uncollected_logs_is_flagged(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["process_creation:linux"]))[0]
    adv = D.advisory_for(gap, {}, F / "advisories", fetch=False)
    d = D.draft_one(gap, FakeClient(RULE_REPLY), "fake-model", adv, tmp_path / "rules")
    assert d.logs_ok is False and "logs not collected" in d.status


def test_honest_refusals_and_cwe_mismatch_pass_through(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    reply = {"verdict": "no_signature", "vuln_class": "denial of service", "cwe_agrees": False,
             "cwe_note": "Tagged as buffer overflow; text describes resource exhaustion.", "reason": "DoS only."}
    d = D.draft_one(gap, FakeClient(reply), "m", "text", tmp_path / "rules")
    assert d.status == "no_signature" and "resource exhaustion" in d.cwe_note and not d.file
    md = D.render([d], {"Model": "m"})
    assert "CWE mismatch" in md


def test_prompt_carries_logs_and_advisory(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    prompt = D.build_prompt(gap, D.advisory_for(gap, {"CVE-2099-0001": "CISA KEV: x"}, F / "advisories", False))
    assert "COLLECTED LOGS (Sigma names): webserver" in prompt
    assert "CISA KEV: x" in prompt and "logon_hash=1" in prompt
