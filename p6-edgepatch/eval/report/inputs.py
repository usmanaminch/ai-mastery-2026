import json
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
from .models import StructuralResult, BehavioralResult, TestSuiteResult

def load_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, f"Missing file: {path.name}"
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except json.JSONDecodeError as e:
        return None, f"Malformed JSON in {path.name}: {e}"

def load_case_inputs(case_dir: Path) -> Tuple[
    Optional[StructuralResult],
    Optional[BehavioralResult],
    Optional[TestSuiteResult],
    Optional[str],
    Dict[str, Any],
    List[str]
]:
    errors = []
    raw_inputs = {}

    ps_json, err = load_json(case_dir / "patch_score.json")
    if err:
        errors.append(err)
    else:
        raw_inputs["patch_score"] = ps_json

    pp_json, err = load_json(case_dir / "post_patch_result.json")
    if err:
        errors.append(err)
    else:
        raw_inputs["post_patch_result"] = pp_json

    ts_json, err = load_json(case_dir / "test_suite_result.json")
    if err:
        errors.append(err)
    else:
        raw_inputs["test_suite_result"] = ts_json

    proof_path = case_dir / "proof.txt"
    proof_txt = None
    if not proof_path.exists():
        errors.append("Missing file: proof.txt")
    else:
        proof_txt = proof_path.read_text(encoding="utf-8")
        raw_inputs["proof"] = proof_txt

    struct_res = None
    if ps_json:
        try:
            struct_res = StructuralResult(
                verdict_label=ps_json["verdict"]["label"],
                confidence=float(ps_json["verdict"]["confidence"]),
                locality=ps_json.get("locality", {}),
                minimality=ps_json.get("minimality", {}),
                overlap=ps_json.get("overlap", {})
            )
        except (KeyError, TypeError) as e:
            errors.append(f"Missing or invalid required key in patch_score.json: {e}")

    behav_res = None
    if pp_json:
        behav_res = BehavioralResult(
            crash_resolved=pp_json.get("crash_resolved"),
            detail=pp_json.get("detail", ""),
            source=pp_json.get("source", "")
        )

    ts_res = None
    if ts_json:
        ts_res = TestSuiteResult(
            passed=ts_json.get("passed"),
            total=ts_json.get("total", 0),
            failed=ts_json.get("failed", 0),
            warnings=ts_json.get("warnings", 0),
            detail=ts_json.get("detail", ""),
            source=ts_json.get("source", "")
        )

    return struct_res, behav_res, ts_res, proof_txt, raw_inputs, errors
