import json
from eval.report.models import RemediationReport, CombinedVerdict, StructuralResult, BehavioralResult, TestSuiteResult
from eval.report.render import render_json, render_markdown

def get_dummy_report():
    return RemediationReport(
        case_id="case_001",
        combined_verdict=CombinedVerdict(
            label="READY_HIGH_CONFIDENCE",
            confidence=0.95,
            explanation="Test explanation",
            reasons=["Test reason"],
            required_human_actions=["Test action"]
        ),
        structural=StructuralResult("strong_match", 0.95, {}, {}, {}),
        behavioral=BehavioralResult(True, "Detail", "Source"),
        test_suite=TestSuiteResult(True, 10, 0, 0, "Detail", "Source"),
        proof_excerpt="proof text",
        evidence_inputs={"patch_score": {}},
        limitations=["Limitation 1"]
    )

def test_render_json_deterministic():
    report = get_dummy_report()
    json_str = render_json(report)
    data = json.loads(json_str)
    
    assert data["case_id"] == "case_001"
    assert data["combined_verdict"]["label"] == "READY_HIGH_CONFIDENCE"
    assert "patch_score" in data["evidence_inputs"]

def test_render_markdown():
    report = get_dummy_report()
    md = render_markdown(report)
    
    assert "# Remediation Report: case_001" in md
    assert "## Summary Verdict" in md
    assert "**Verdict:** READY_HIGH_CONFIDENCE" in md
    assert "## Structural Assessment" in md
    assert "## Behavioral Evidence Assessment" in md
    assert "## Regression Test Assessment" in md
    assert "## Combined Recommendation" in md
    assert "## Evidence Consumed" in md
    assert "## Limitations" in md
    assert "## Human Reviewer Checklist" in md
    assert "- [ ] Test action" in md
    assert "- Limitation 1" in md
