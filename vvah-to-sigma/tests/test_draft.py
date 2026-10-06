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


def test_reference_ranking_prefers_exploit_writeups():
    nvd = ("NVD: desc\n"
           "Reference: https://vendor.example/psirt [Vendor Advisory]\n"
           "Reference: https://news.example/x [Press/Media Coverage]\n"
           "Reference: https://blog.example/poc [Exploit, Third Party Advisory]\n")
    assert D.reference_urls(nvd) == ["https://blog.example/poc", "https://vendor.example/psirt"]


def test_short_values_never_count_as_grounded():
    g, u = D.grounding({"sel": {"sc-status": 200, "cs-method": "POST", "x|contains": "logon_hash=1"}},
                       "send a POST with logon_hash=1, server returns 200")
    assert g == ["logon_hash=1"] and sorted(u) == ["200", "POST"]


def test_html_is_reduced_to_text():
    t = D._Text()
    t.feed("<html><script>evil()</script><p>GET /remote/x</p><style>p{}</style></html>")
    assert t.parts == ["GET /remote/x"]


def test_logged_gaps_sort_first(tmp_path):
    rows = [{"asset": a, "cve": c, "logs": l, "priority": "exploited", "ransomware": r,
             "verdict": "Gap: x"} for a, c, l, r in
            [("vpn", "CVE-2099-0009", [], True), ("web", "CVE-2099-0008", ["webserver"], False)]]
    p = tmp_path / "e.json"
    p.write_text(json.dumps(rows))
    assert [g.cve for g in D.load_gaps(p)] == ["CVE-2099-0008", "CVE-2099-0009"]


def test_api_errors_are_explained_and_temperature_is_dropped(monkeypatch):
    import io
    import urllib.error
    sent = []

    def fake_urlopen(req, timeout=0):
        body = json.loads(req.data)
        sent.append(body)
        if "temperature" in body:
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                         io.BytesIO(b'{"error":{"message":"temperature is not supported"}}'))
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b'{"ok": 1}'
        return R()

    monkeypatch.setattr(D.urllib.request, "urlopen", fake_urlopen)
    assert D._HTTPClient()._post("https://x", {}, {"model": "m", "temperature": 0}) == {"ok": 1}
    assert "temperature" not in sent[-1]


class SeqClient:
    usage, last_stop = None, "end_turn"

    def __init__(self, replies):
        self.replies = list(replies)

    def complete(self, system, user):
        return self.replies.pop(0)


def test_non_json_reply_is_retried_then_saved(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    ok = json.dumps({"verdict": "insufficient_info", "reason": "r"})
    assert D.draft_one(gap, SeqClient(["Here is my analysis...", ok]), "m", "t", tmp_path / "rules").verdict \
        == "insufficient_info"
    d = D.draft_one(gap, SeqClient(["prose", "more prose"]), "m", "t", tmp_path / "rules")
    assert d.status == "error" and (tmp_path / "raw" / "CVE-2099-0001.txt").read_text() == "more prose"


def test_no_cwe_means_no_mismatch_note(tmp_path):
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    gap.cwes = set()
    reply = json.dumps({"verdict": "behavioral", "cwe_agrees": False, "cwe_note": "No CWE assigned"})
    assert D.draft_one(gap, SeqClient([reply]), "m", "t", tmp_path / "rules").cwe_note == ""


def test_other_format_rules_are_indexed_and_deprecated_skipped():
    from exposure_to_sigma.rulesets import ForeignRuleset
    rs = ForeignRuleset("other", F / "other")
    assert {r.fmt for r in rs.rules} == {"splunk-spl", "elastic"}
    assert rs.specific("CVE-2099-0001")[0].title.startswith("ExampleOS Admin")
    assert not rs.specific("CVE-2099-0003")


def test_other_format_beats_gap_and_drafter_translates(tmp_path):
    from exposure_to_sigma.analyze import OTHER_FORMAT, analyze
    from exposure_to_sigma.feeds import KevFeed
    from exposure_to_sigma.models import Exposure
    from exposure_to_sigma.report import write
    from exposure_to_sigma.rulesets import ForeignRuleset
    kev = tmp_path / "kev.json"
    kev.write_text(json.dumps({"catalogVersion": "t", "vulnerabilities": [
        {"cveID": "CVE-2099-0001", "cwes": [], "knownRansomwareCampaignUse": "Unknown"}]}))
    ex = [Exposure(asset="edge-01", cve="CVE-2099-0001", logs={"webserver"})]
    v = analyze(ex, [KevFeed(kev)], [], [], other=[ForeignRuleset("other", F / "other")])
    assert v[0].verdict == OTHER_FORMAT
    write(v, {}, tmp_path / "out")
    gap = D.load_gaps(tmp_path / "out" / "exposures.json")[0]
    assert gap.mode == "translate"
    adv = D.advisory_for(gap, {}, tmp_path / "adv", fetch=False)
    assert "SOURCE RULE (splunk-spl" in adv and "logon_hash=1" in adv
    assert "translate the SOURCE RULE" in D.build_prompt(gap, adv)


def test_nuclei_and_saved_pages_feed_the_prompt(tmp_path):
    gap = D.Gap("CVE-2099-0004", assets=["a"])
    (tmp_path / "CVE-2099-0004.html").write_text("<p>Vendor IOC: %EX-1-PWN</p><script>x</script>")
    adv = D.advisory_for(gap, {}, tmp_path, False, nuclei=D.nuclei_index(F / "nuclei"))
    assert "/cgi-bin/examplecheck.cgi" in adv and "%EX-1-PWN" in adv and "SAVED BY YOU" in adv


def test_refusal_is_an_outcome_not_an_error(tmp_path):
    class Refuser(SeqClient):
        last_stop = "refusal"
    gap = D.load_gaps(_exposures(tmp_path, ["webserver"]))[0]
    d = D.draft_one(gap, Refuser([""]), "m", "t", tmp_path / "rules")
    assert d.status == "refused"
    md = D.needs_input([d], tmp_path / "adv")
    assert "CVE-2099-0001" in md and "refused" in md
