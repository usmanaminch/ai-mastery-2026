from pathlib import Path
from .models import RemediationReport
from .inputs import load_case_inputs
from .verdict import compute_combined_verdict
from .render import render_markdown, render_json

def generate_report(case_dir: Path) -> RemediationReport:
    struct_res, behav_res, ts_res, proof_txt, raw_inputs, errors = load_case_inputs(case_dir)
    verdict = compute_combined_verdict(struct_res, behav_res, ts_res, errors)

    limitations = [
        "Structural scoring cannot prove semantic correctness.",
        "This reporter does not run code, execute tests, reproduce vulnerabilities, or verify behavior itself.",
        "It only judges pre-captured evidence supplied as input."
    ]

    proof_excerpt = ""
    if proof_txt:
        proof_excerpt = proof_txt[:1000]

    return RemediationReport(
        case_id=case_dir.name,
        combined_verdict=verdict,
        structural=struct_res,
        behavioral=behav_res,
        test_suite=ts_res,
        proof_excerpt=proof_excerpt,
        evidence_inputs=raw_inputs,
        limitations=limitations
    )

def write_report(case_dir: Path, out_dir: Path) -> tuple[Path, Path]:
    report = generate_report(case_dir)
    md_content = render_markdown(report)
    json_content = render_json(report)

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{report.case_id}_report.md"
    json_path = out_dir / f"{report.case_id}_report.json"

    md_path.write_text(md_content, encoding="utf-8")
    json_path.write_text(json_content, encoding="utf-8")

    return md_path, json_path
