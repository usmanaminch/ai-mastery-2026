import json
from pathlib import Path
from eval.report.inputs import load_case_inputs

def test_load_valid_case_inputs(tmp_path):
    case_dir = tmp_path / "valid_case"
    case_dir.mkdir()
    
    (case_dir / "patch_score.json").write_text(json.dumps({
        "verdict": {"label": "strong_match", "confidence": 0.95},
        "locality": {}, "minimality": {}, "overlap": {}
    }))
    
    (case_dir / "post_patch_result.json").write_text(json.dumps({
        "crash_resolved": True,
        "detail": "ok",
        "source": "log"
    }))
    
    (case_dir / "test_suite_result.json").write_text(json.dumps({
        "passed": True,
        "total": 100,
        "failed": 0,
        "warnings": 0,
        "detail": "ok",
        "source": "ci"
    }))
    
    (case_dir / "proof.txt").write_text("proof content")
    
    struct_res, behav_res, ts_res, proof_txt, raw, errors = load_case_inputs(case_dir)
    
    assert len(errors) == 0
    assert struct_res.verdict_label == "strong_match"
    assert behav_res.crash_resolved is True
    assert ts_res.passed is True
    assert proof_txt == "proof content"
    assert "patch_score" in raw

def test_missing_files(tmp_path):
    case_dir = tmp_path / "empty_case"
    case_dir.mkdir()
    
    struct_res, behav_res, ts_res, proof_txt, raw, errors = load_case_inputs(case_dir)
    assert len(errors) == 4
    assert struct_res is None

def test_malformed_json(tmp_path):
    case_dir = tmp_path / "malformed_case"
    case_dir.mkdir()
    
    (case_dir / "patch_score.json").write_text("{bad json")
    (case_dir / "post_patch_result.json").write_text("{}")
    (case_dir / "test_suite_result.json").write_text("{}")
    (case_dir / "proof.txt").write_text("proof content")
    
    struct_res, behav_res, ts_res, proof_txt, raw, errors = load_case_inputs(case_dir)
    assert any("Malformed JSON" in err for err in errors)
    assert struct_res is None
