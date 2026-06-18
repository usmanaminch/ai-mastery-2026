#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    try:
        from eval.patch_score.scorer import score_patches
    except ImportError:
        print("ERROR: Could not import eval.patch_score.scorer")
        sys.exit(1)

    zlib_target = repo_root / "targets" / "zlib"
    if not zlib_target.exists():
        print(f"SKIP: Target directory not found at {zlib_target}. Real zlib adversarial scoring skipped.")
        sys.exit(0)

    eval_dir = repo_root / "eval_cases" / "zlib-cve-2022-37434"
    adv_dir = eval_dir / "adversarial"
    ref_diff = eval_dir / "reference.diff"

    if not adv_dir.exists():
        print(f"SKIP: Adversarial diffs directory not found at {adv_dir}.")
        sys.exit(0)

    if not ref_diff.exists():
        print(f"SKIP: Reference diff not found at {ref_diff}.")
        sys.exit(0)

    results = {}
    for cand_diff in sorted(adv_dir.glob("*.diff")):
        score = score_patches(cand_diff, ref_diff, zlib_target)
        results[cand_diff.name] = {
            "verdict": score.verdict.label,
            "confidence": score.verdict.confidence,
            "minimality_label": score.minimality.get("minimality_label", "N/A"),
            "same_file": score.overlap.get("same_file", False),
            "same_function": score.overlap.get("same_function", False),
            "failure_taxonomy": score.verdict.failure_taxonomy
        }

    out_file = eval_dir / "adversarial_scorecard.json"
    out_file.write_text(json.dumps(results, indent=2, sort_keys=True))
    
    print("\nAdversarial Cases Verdict Table:")
    print(f"{'Candidate':<40} | {'Verdict':<20} | {'Minimality':<15}")
    print("-" * 80)
    for cand, data in sorted(results.items()):
        print(f"{cand:<40} | {data['verdict']:<20} | {data['minimality_label']:<15}")
    print(f"\nSaved adversarial scorecard to {out_file}")

if __name__ == "__main__":
    main()
