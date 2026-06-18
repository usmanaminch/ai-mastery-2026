import pytest
from eval.report.models import StructuralResult, BehavioralResult, TestSuiteResult
from eval.report.verdict import compute_combined_verdict

def make_structural(label="strong_match", conf=1.0):
    return StructuralResult(verdict_label=label, confidence=conf, locality={}, minimality={}, overlap={})

def make_behavioral(resolved=True):
    return BehavioralResult(crash_resolved=resolved, detail="", source="")

def make_test_suite(passed=True):
    return TestSuiteResult(passed=passed, total=10, failed=0, warnings=0, detail="", source="")

def test_inconclusive_missing_inputs():
    verdict = compute_combined_verdict(make_structural(), make_behavioral(), make_test_suite(), ["Some error"])
    assert verdict.label == "INCONCLUSIVE"
    assert verdict.confidence <= 0.5

def test_reject_wrong_location():
    s = make_structural("wrong_file")
    verdict = compute_combined_verdict(s, make_behavioral(), make_test_suite(), [])
    assert verdict.label == "REJECT_WRONG_LOCATION"
    assert verdict.confidence <= 0.5

def test_needs_behavioral_verification():
    verdict = compute_combined_verdict(make_structural(), make_behavioral(False), make_test_suite(), [])
    assert verdict.label == "NEEDS_BEHAVIORAL_VERIFICATION"
    assert verdict.confidence <= 0.5

def test_reject_regression():
    verdict = compute_combined_verdict(make_structural(), make_behavioral(), make_test_suite(False), [])
    assert verdict.label == "REJECT_REGRESSION"
    assert verdict.confidence <= 0.5

def test_reject_incomplete():
    s = make_structural("under_broad")
    verdict = compute_combined_verdict(s, make_behavioral(), make_test_suite(), [])
    assert verdict.label == "REJECT_INCOMPLETE"
    assert verdict.confidence <= 0.5

def test_ready_high_confidence():
    verdict = compute_combined_verdict(make_structural("strong_match", 0.99), make_behavioral(), make_test_suite(), [])
    assert verdict.label == "READY_HIGH_CONFIDENCE"
    assert verdict.confidence == 0.99

def test_ready_with_caveats():
    verdict = compute_combined_verdict(make_structural("over_broad", 0.90), make_behavioral(), make_test_suite(), [])
    assert verdict.label == "READY_WITH_CAVEATS"
    assert verdict.confidence == 0.75

def test_blind_spot_closure():
    # This demonstrates how Phase 2B closes Phase 2A's structural blind spot.
    # A patch can be structurally aligned but behaviorally unproven or failed,
    # so it must not be approved.
    s = make_structural("strong_match", 1.0)
    b = make_behavioral(False)
    ts = make_test_suite(True)
    
    verdict = compute_combined_verdict(s, b, ts, [])
    assert verdict.label == "NEEDS_BEHAVIORAL_VERIFICATION"
    assert verdict.confidence <= 0.5
    assert "crash_resolved is False" in verdict.reasons[0]
