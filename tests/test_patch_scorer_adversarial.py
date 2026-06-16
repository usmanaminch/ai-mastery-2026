import pytest
from pathlib import Path
from eval.patch_score.scorer import score_patches

@pytest.fixture
def adv_fixtures():
    base = Path(__file__).parent / "fixtures" / "adversarial"
    return {
        "source_tree": base / "source_tree",
        "diffs": base / "diffs"
    }

def test_wrong_file(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference.diff"
    cand = adv_fixtures["diffs"] / "wrong_file.diff"
    score = score_patches(cand, ref, st)
    
    assert score.verdict.label == "wrong_file"
    assert score.overlap["same_file"] is False
    assert "wrong_file" in score.verdict.failure_taxonomy

def test_wrong_function(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference.diff"
    cand = adv_fixtures["diffs"] / "wrong_function.diff"
    score = score_patches(cand, ref, st)
    
    assert score.verdict.label == "wrong_function"
    assert score.overlap["same_file"] is True
    assert score.overlap["same_function"] is False
    assert "wrong_function" in score.verdict.failure_taxonomy

def test_over_broad(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference.diff"
    cand = adv_fixtures["diffs"] / "over_broad.diff"
    score = score_patches(cand, ref, st)
    
    assert score.verdict.label == "over_broad"
    assert score.minimality["minimality_ratio"] > 4.0
    assert score.minimality["minimality_label"] == "sprawling"
    assert "over_broad" in score.verdict.failure_taxonomy

def test_under_broad(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference.diff"
    cand = adv_fixtures["diffs"] / "under_broad.diff"
    score = score_patches(cand, ref, st)
    
    assert score.verdict.label == "under_broad"
    assert score.minimality["minimality_ratio"] < 0.5
    assert score.overlap["line_overlap_ratio"] < 0.3
    assert "under_broad" in score.verdict.failure_taxonomy

def test_aligned_but_wrong(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference.diff"
    cand = adv_fixtures["diffs"] / "aligned_but_wrong.diff"
    score = score_patches(cand, ref, st)
    
    # KNOWN LIMITATION: structural scoring cannot detect semantic incorrectness 
    # when a wrong patch lands in the same file/function/line region
    assert score.verdict.label == "strong_match"
    assert score.overlap["same_file"] is True
    assert score.overlap["same_function"] is True
    assert score.overlap["line_overlap_ratio"] >= 0.3

def test_fallback_low_overlap_unmapped(adv_fixtures):
    st = adv_fixtures["source_tree"]
    ref = adv_fixtures["diffs"] / "reference_unmapped.diff"
    cand = adv_fixtures["diffs"] / "fallback_low_overlap_unmapped.diff"
    score = score_patches(cand, ref, st)
    
    assert score.locality["function_mapping_status"] == "unmapped_both"
    assert score.verdict.label != "strong_match"
