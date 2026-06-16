import json
from dataclasses import asdict
from .models import RemediationReport

def render_json(report: RemediationReport) -> str:
    data = asdict(report)
    return json.dumps(data, sort_keys=True, indent=2)

def render_markdown(report: RemediationReport) -> str:
    md = []
    
    md.append(f"# Remediation Report: {report.case_id}")
    md.append("")
    
    md.append("## Summary Verdict")
    md.append(f"**Verdict:** {report.combined_verdict.label}")
    md.append(f"**Confidence:** {report.combined_verdict.confidence:.2f}")
    md.append(f"**Explanation:** {report.combined_verdict.explanation}")
    md.append("")
    
    md.append("## Combined Recommendation")
    md.append("Reasons:")
    for reason in report.combined_verdict.reasons:
        md.append(f"- {reason}")
    md.append("")
    
    md.append("## Structural Assessment")
    if report.structural:
        md.append(f"**Verdict Label:** {report.structural.verdict_label}")
        md.append(f"**Confidence:** {report.structural.confidence:.2f}")
    else:
        md.append("No structural assessment available.")
    md.append("")
    
    md.append("## Behavioral Evidence Assessment")
    if report.behavioral:
        md.append(f"**Crash Resolved:** {report.behavioral.crash_resolved}")
        md.append(f"**Detail:** {report.behavioral.detail}")
        md.append(f"**Source:** {report.behavioral.source}")
    else:
        md.append("No behavioral evidence available.")
    md.append("")
    
    md.append("## Regression Test Assessment")
    if report.test_suite:
        md.append(f"**Passed:** {report.test_suite.passed}")
        md.append(f"**Total / Failed / Warnings:** {report.test_suite.total} / {report.test_suite.failed} / {report.test_suite.warnings}")
        md.append(f"**Detail:** {report.test_suite.detail}")
        md.append(f"**Source:** {report.test_suite.source}")
    else:
        md.append("No regression test evidence available.")
    md.append("")
    
    md.append("## Evidence Consumed")
    md.append("Inputs loaded successfully:")
    for key in report.evidence_inputs.keys():
        md.append(f"- {key}")
    md.append("")
    
    md.append("## Limitations")
    for lim in report.limitations:
        md.append(f"- {lim}")
    md.append("")
    
    md.append("## Human Reviewer Checklist")
    for act in report.combined_verdict.required_human_actions:
        md.append(f"- [ ] {act}")
        
    return "\n".join(md)
