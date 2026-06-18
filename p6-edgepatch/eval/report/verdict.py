from typing import List, Optional
from .models import StructuralResult, BehavioralResult, TestSuiteResult, CombinedVerdict

def compute_combined_verdict(
    structural: Optional[StructuralResult],
    behavioral: Optional[BehavioralResult],
    regression: Optional[TestSuiteResult],
    input_errors: List[str]
) -> CombinedVerdict:
    
    reasons = []

    if input_errors or not structural or not behavioral or not regression:
        label = "INCONCLUSIVE"
        explanation = "Missing or unparseable required input evidence."
        reasons.extend(input_errors)
        if not structural and "Missing file: patch_score.json" not in input_errors:
            reasons.append("Structural results could not be loaded.")
    elif structural.verdict_label in ("wrong_file", "wrong_function"):
        label = "REJECT_WRONG_LOCATION"
        explanation = "The patch modified an incorrect structural location."
        reasons.append(f"Structural verdict is {structural.verdict_label}.")
    elif behavioral.crash_resolved is not True:
        label = "NEEDS_BEHAVIORAL_VERIFICATION"
        explanation = "Behavioral evidence does not confirm the crash is resolved."
        reasons.append("crash_resolved is False or missing.")
    elif regression.passed is not True:
        label = "REJECT_REGRESSION"
        explanation = "The patch caused a regression in the standard test suite."
        reasons.append("Test suite failed.")
    elif structural.verdict_label == "under_broad":
        label = "REJECT_INCOMPLETE"
        explanation = "The patch is structurally incomplete."
        reasons.append("Structural verdict is under_broad.")
    elif behavioral.crash_resolved is True and regression.passed is True and structural.verdict_label in ("strong_match", "acceptable_broader"):
        label = "READY_HIGH_CONFIDENCE"
        explanation = "Structural and behavioral evidence strongly support the patch."
        reasons.append("Crash resolved, regression passed, strong structural match.")
    elif behavioral.crash_resolved is True and regression.passed is True and structural.verdict_label == "over_broad":
        label = "READY_WITH_CAVEATS"
        explanation = "Behavioral evidence passes, but patch is structurally over-broad."
        reasons.append("Patch includes extra structural changes (over_broad).")
    else:
        label = "NEEDS_REVIEW"
        explanation = "Evidence is mixed or inconclusive."
        reasons.append("Did not meet high confidence or automatic rejection criteria.")

    base_conf = structural.confidence if structural else 0.0

    if label in ("READY_HIGH_CONFIDENCE",):
        conf = base_conf
    elif label in ("READY_WITH_CAVEATS", "NEEDS_REVIEW"):
        conf = min(base_conf, 0.75)
    else:
        conf = min(base_conf, 0.5)

    actions = [
        "Review patch diff manually.",
        "Confirm behavioral validation was produced in a trusted environment.",
        "Confirm standard test-suite result source.",
        "Review any warnings or sanitizer notes.",
        "Confirm rollback or remediation plan before deployment."
    ]

    return CombinedVerdict(
        label=label,
        confidence=conf,
        explanation=explanation,
        reasons=reasons,
        required_human_actions=actions
    )
