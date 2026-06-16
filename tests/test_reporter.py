import json
from eval.report.reporter import generate_report, write_report

def setup_valid_fixture(case_dir):
    case_dir.mkdir(parents=True, exist_ok=True)
    
    (case_dir / "patch_score.json").write_text(json.dumps({
        "verdict": {"label": "strong_match", "confidence": 0.88},
        "locality": {}, "minimality": {}, "overlap": {}
    }))
    
    (case_dir / "post_patch_result.json").write_text(json.dumps({
        "crash_resolved": True,
        "detail": "Targeted post-patch check exited cleanly.",
        "source": "pre-captured docker validation log"
    }))
    
    (case_dir / "test_suite_result.json").write_text(json.dumps({
        "passed": True,
        "total": 100,
        "failed": 0,
        "warnings": 0,
        "detail": "Standard test suite passed.",
        "source": "pre-captured test-suite output"
    }))
    
    (case_dir / "proof.txt").write_text("Crash is fixed!")

def test_generate_report(tmp_path):
    case_dir = tmp_path / "test_case_1"
    setup_valid_fixture(case_dir)
    
    report = generate_report(case_dir)
    assert report.case_id == "test_case_1"
    assert report.combined_verdict.label == "READY_HIGH_CONFIDENCE"
    assert report.combined_verdict.confidence == 0.88
    assert "Structural scoring cannot prove semantic correctness." in report.limitations

def test_write_report(tmp_path):
    case_dir = tmp_path / "test_case_2"
    out_dir = tmp_path / "out_dir"
    setup_valid_fixture(case_dir)
    
    md_path, json_path = write_report(case_dir, out_dir)
    
    assert md_path.exists()
    assert json_path.exists()
    assert md_path.name == "test_case_2_report.md"
    assert json_path.name == "test_case_2_report.json"
    
    md_content = md_path.read_text()
    assert "READY_HIGH_CONFIDENCE" in md_content
