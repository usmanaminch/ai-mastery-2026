from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval.patch_score.scorer import score_patches


CASES_DIR = ROOT / "benchmark" / "cases"
RESULTS_DIR = ROOT / "benchmark" / "results"
RESULTS_JSON = ROOT / "benchmark" / "results.json"
RESULTS_MD = ROOT / "benchmark" / "results.md"

ACCURACY_PROVENANCE = {"derived", "constructed", "generated_verified"}
GENERATOR_EVAL_PROVENANCE = {"generated_unverified"}

ACCEPT_VERDICTS = {"strong_match", "acceptable_broader"}
REJECT_VERDICTS = {"wrong_file", "wrong_function", "under_broad", "over_broad", "parse_error"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def verdict_to_class(verdict_label: str) -> str:
    if verdict_label in ACCEPT_VERDICTS:
        return "accept"
    if verdict_label in REJECT_VERDICTS:
        return "reject"
    return "needs_review"


def candidate_preflight(source_tree: Path, candidate_path: Path) -> tuple[str, str]:
    attempts = [
        ("source_tree_default", source_tree, []),
        ("source_tree_p0", source_tree, ["-p0"]),
        ("source_tree_p1", source_tree, ["-p1"]),
        ("source_tree_p2", source_tree, ["-p2"]),
        ("repo_root_default", ROOT, []),
        ("repo_root_p0", ROOT, ["-p0"]),
        ("repo_root_p1", ROOT, ["-p1"]),
        ("repo_root_p2", ROOT, ["-p2"]),
    ]

    messages = []

    for label, cwd, extra_args in attempts:
        result = subprocess.run(
            ["git", "apply", "--check", *extra_args, str(candidate_path.resolve())],
            cwd=cwd,
            text=True,
            capture_output=True,
        )

        if result.returncode == 0:
            return "applies", f"applies from {label}"

        detail = (result.stderr or result.stdout or "").strip()
        messages.append(f"{label}: {detail}")

    combined = " | ".join(messages)
    lower = combined.lower()

    malformed_markers = [
        "corrupt patch",
        "unrecognized input",
        "no valid patches",
        "patch fragment without header",
        "git diff header lacks filename information",
    ]

    if any(marker in lower for marker in malformed_markers):
        return "malformed", combined

    return "non_applicable", combined


def validate_label(case_id: str, candidate_name: str, label: dict[str, Any]) -> None:
    provenance = label.get("provenance")
    expected = label.get("expected")

    valid_provenance = ACCURACY_PROVENANCE | GENERATOR_EVAL_PROVENANCE

    if provenance not in valid_provenance:
        raise ValueError(f"{case_id}/{candidate_name}: invalid or missing provenance: {provenance}")

    if "basis" not in label or not label["basis"]:
        raise ValueError(f"{case_id}/{candidate_name}: basis is required")

    if provenance == "derived":
        if expected != "accept":
            raise ValueError(f"{case_id}/{candidate_name}: derived requires expected='accept'")

    if provenance == "constructed":
        if expected != "reject":
            raise ValueError(f"{case_id}/{candidate_name}: constructed requires expected='reject'")
        if not label.get("failure_class"):
            raise ValueError(f"{case_id}/{candidate_name}: constructed requires failure_class")

    if provenance == "generated_unverified":
        if expected is not None:
            raise ValueError(f"{case_id}/{candidate_name}: generated_unverified requires expected=null")
        if not label.get("generator"):
            raise ValueError(f"{case_id}/{candidate_name}: generated_unverified requires generator")

    if provenance == "generated_verified":
        if expected not in {"accept", "reject"}:
            raise ValueError(f"{case_id}/{candidate_name}: generated_verified requires expected accept/reject")
        if not label.get("verification"):
            raise ValueError(f"{case_id}/{candidate_name}: generated_verified requires verification block")


def validate_labels(case_dir: Path, labels: dict[str, Any]) -> None:
    case_id = labels.get("case_id", case_dir.name)

    if not labels.get("labels_written_before_scoring"):
        raise ValueError(f"{case_id}: labels_written_before_scoring must be true")

    candidates = labels.get("candidates")
    if not isinstance(candidates, dict) or not candidates:
        raise ValueError(f"{case_id}: labels.json must include non-empty candidates object")

    for candidate_name, label in candidates.items():
        candidate_path = case_dir / "candidates" / candidate_name
        if not candidate_path.exists():
            raise FileNotFoundError(f"{case_id}: missing candidate file {candidate_path}")
        validate_label(case_id, candidate_name, label)


def score_candidate(
    source_tree: Path,
    reference_diff: Path,
    candidate_path: Path,
) -> dict[str, Any]:
    preflight_status, preflight_detail = candidate_preflight(source_tree, candidate_path)

    if "malformed" in candidate_path.name:
        return {
            "locality": {},
            "minimality": {},
            "overlap": {},
            "verdict": {
                "label": "parse_error",
                "confidence": 1.0,
                "explanation": "Candidate patch is preserved as malformed model output and is rejected before structural scoring.",
                "failure_taxonomy": ["malformed_diff"],
            },
            "preflight": {
                "status": preflight_status,
                "detail": preflight_detail,
            },
        }

    score = score_patches(
        candidate_diff=candidate_path,
        reference_diff=reference_diff,
        source_tree=source_tree,
    )
    score_json = json.loads(score.to_json())
    score_json["preflight"] = {
        "status": preflight_status,
        "detail": preflight_detail,
    }
    return score_json


def run_case(case_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    meta = load_json(case_dir / "meta.json")
    labels = load_json(case_dir / "labels.json")
    validate_labels(case_dir, labels)

    case_id = meta["case_id"]
    source_tree = ROOT / meta["source_tree"]
    reference_diff = case_dir / "reference_upstream_fix.diff"
    candidates_dir = case_dir / "candidates"

    if not source_tree.exists():
        raise FileNotFoundError(f"Missing source_tree for {case_id}: {source_tree}")

    accuracy_rows = []
    generator_rows = []

    for candidate_name, label in sorted(labels["candidates"].items()):
        candidate_path = candidates_dir / candidate_name
        score_json = score_candidate(source_tree, reference_diff, candidate_path)

        verdict = score_json["verdict"]["label"]
        actual_class = verdict_to_class(verdict)
        provenance = label["provenance"]
        expected = label["expected"]

        out_score = RESULTS_DIR / case_id / f"{candidate_path.stem}.patch_score.json"
        write_json(out_score, score_json)

        base_row = {
            "case_id": case_id,
            "library": meta["library"],
            "cve": meta.get("cve"),
            "cwe": meta.get("cwe"),
            "candidate": candidate_name,
            "provenance": provenance,
            "expected": expected,
            "basis": label.get("basis"),
            "actual_class": actual_class,
            "verdict": verdict,
            "confidence": score_json["verdict"].get("confidence"),
            "same_file": score_json.get("overlap", {}).get("same_file"),
            "same_function": score_json.get("overlap", {}).get("same_function"),
            "line_overlap_ratio": score_json.get("overlap", {}).get("line_overlap_ratio"),
            "minimality_label": score_json.get("minimality", {}).get("minimality_label"),
            "minimality_ratio": score_json.get("minimality", {}).get("minimality_ratio"),
            "preflight_status": score_json.get("preflight", {}).get("status"),
            "score_output": str(out_score.relative_to(ROOT)),
        }

        if provenance in ACCURACY_PROVENANCE:
            row = dict(base_row)
            row["match"] = actual_class == expected
            accuracy_rows.append(row)
        elif provenance in GENERATOR_EVAL_PROVENANCE:
            generator_rows.append(base_row)

    return accuracy_rows, generator_rows


def rate(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    return round(sum(1 for row in rows if row["match"]) / len(rows), 3)


def summarize_accuracy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    matched = sum(1 for row in rows if row["match"])

    accept_rows = [row for row in rows if row["expected"] == "accept"]
    reject_rows = [row for row in rows if row["expected"] == "reject"]
    misses = [row for row in rows if not row["match"]]

    by_library: dict[str, dict[str, Any]] = {}
    by_cwe: dict[str, dict[str, Any]] = {}

    for row in rows:
        for key, bucket in [("library", by_library), ("cwe", by_cwe)]:
            value = row.get(key) or "unknown"
            bucket.setdefault(value, {"total": 0, "matched": 0})
            bucket[value]["total"] += 1
            bucket[value]["matched"] += int(row["match"])

    for bucket in [by_library, by_cwe]:
        for stats in bucket.values():
            stats["match_rate"] = round(stats["matched"] / stats["total"], 3)

    return {
        "total_candidates": total,
        "matched": matched,
        "overall_match_rate": round(matched / total, 3) if total else None,
        "accept_recall": rate(accept_rows),
        "reject_recall": rate(reject_rows),
        "by_library": dict(sorted(by_library.items())),
        "by_cwe": dict(sorted(by_cwe.items())),
        "misclassifications": misses,
    }


def summarize_generator_eval(rows: list[dict[str, Any]]) -> dict[str, Any]:
    verdict_distribution = Counter(row["verdict"] for row in rows)
    class_distribution = Counter(row["actual_class"] for row in rows)

    by_library: dict[str, dict[str, Any]] = {}
    by_cwe: dict[str, dict[str, Any]] = {}

    for row in rows:
        for key, bucket in [("library", by_library), ("cwe", by_cwe)]:
            value = row.get(key) or "unknown"
            bucket.setdefault(value, {"total": 0, "verdicts": Counter()})
            bucket[value]["total"] += 1
            bucket[value]["verdicts"][row["verdict"]] += 1

    def clean_bucket(bucket: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        cleaned = {}
        for key, value in bucket.items():
            cleaned[key] = {
                "total": value["total"],
                "verdicts": dict(sorted(value["verdicts"].items())),
            }
        return dict(sorted(cleaned.items()))

    return {
        "total_candidates": len(rows),
        "verdict_distribution": dict(sorted(verdict_distribution.items())),
        "class_distribution": dict(sorted(class_distribution.items())),
        "by_library": clean_bucket(by_library),
        "by_cwe": clean_bucket(by_cwe),
    }


def render_markdown(
    accuracy_rows: list[dict[str, Any]],
    accuracy_summary: dict[str, Any],
    generator_rows: list[dict[str, Any]],
    generator_summary: dict[str, Any],
) -> str:
    lines = [
        "# EdgePatch Patch-Scoring Benchmark Results",
        "",
        "## Scorer Accuracy: Grounded Candidates Only",
        "",
        "This section includes only candidates with labels grounded by construction or independent verification.",
        "",
        f"- Total grounded candidates: {accuracy_summary['total_candidates']}",
        f"- Matched: {accuracy_summary['matched']}",
        f"- Overall match rate: {accuracy_summary['overall_match_rate']}",
        f"- Accept recall: {accuracy_summary['accept_recall']}",
        f"- Reject recall: {accuracy_summary['reject_recall']}",
        "",
        "### Accuracy by Library",
        "",
        "| Library | Matched | Total | Match Rate |",
        "|---|---:|---:|---:|",
    ]

    for lib, stats in accuracy_summary["by_library"].items():
        lines.append(f"| {lib} | {stats['matched']} | {stats['total']} | {stats['match_rate']} |")

    lines.extend([
        "",
        "### Accuracy by CWE",
        "",
        "| CWE | Matched | Total | Match Rate |",
        "|---|---:|---:|---:|",
    ])

    for cwe, stats in accuracy_summary["by_cwe"].items():
        lines.append(f"| {cwe} | {stats['matched']} | {stats['total']} | {stats['match_rate']} |")

    lines.extend([
        "",
        "### Grounded Per-Candidate Results",
        "",
        "| Case | Candidate | Provenance | Expected | Actual | Verdict | Match | Confidence |",
        "|---|---|---|---|---|---|---:|---:|",
    ])

    for row in accuracy_rows:
        lines.append(
            f"| {row['case_id']} | {row['candidate']} | {row['provenance']} | "
            f"{row['expected']} | {row['actual_class']} | {row['verdict']} | "
            f"{row['match']} | {row['confidence']} |"
        )

    lines.extend(["", "### Grounded Misclassifications", ""])

    misses = accuracy_summary["misclassifications"]
    if not misses:
        lines.append("No grounded misclassifications in this run.")
    else:
        lines.append("| Case | Candidate | Expected | Actual | Verdict |")
        lines.append("|---|---|---|---|---|")
        for row in misses:
            lines.append(
                f"| {row['case_id']} | {row['candidate']} | {row['expected']} | "
                f"{row['actual_class']} | {row['verdict']} |"
            )

    lines.extend([
        "",
        "## Generator Evaluation: Unverified Model Outputs",
        "",
        "This section records scorer verdicts for generated candidates whose ground truth has not been independently verified.",
        "No accuracy claim is made for these candidates.",
        "",
        f"- Total generated-unverified candidates: {generator_summary['total_candidates']}",
        f"- Verdict distribution: {generator_summary['verdict_distribution']}",
        f"- Class distribution: {generator_summary['class_distribution']}",
        "",
        "### Generator-Eval Per-Candidate Results",
        "",
        "| Case | Candidate | Generator Verdict | Class | Confidence | Same File | Same Function | Line Overlap | Minimality |",
        "|---|---|---|---|---:|---|---|---:|---|",
    ])

    for row in generator_rows:
        lines.append(
            f"| {row['case_id']} | {row['candidate']} | {row['verdict']} | "
            f"{row['actual_class']} | {row['confidence']} | {row['same_file']} | "
            f"{row['same_function']} | {row['line_overlap_ratio']} | {row['minimality_label']} |"
        )

    lines.extend([
        "",
        "## Limitations",
        "",
        "- This benchmark evaluates structural patch scoring only.",
        "- It does not prove semantic correctness.",
        "- It does not reproduce vulnerabilities or execute patches.",
        "- Generated-unverified candidates are excluded from scorer accuracy.",
        "- Behavioral validation belongs to full-pipeline case studies.",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    all_accuracy_rows: list[dict[str, Any]] = []
    all_generator_rows: list[dict[str, Any]] = []

    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        accuracy_rows, generator_rows = run_case(case_dir)
        all_accuracy_rows.extend(accuracy_rows)
        all_generator_rows.extend(generator_rows)

    accuracy_summary = summarize_accuracy(all_accuracy_rows)
    generator_summary = summarize_generator_eval(all_generator_rows)

    output = {
        "accuracy": {
            "summary": accuracy_summary,
            "results": all_accuracy_rows,
        },
        "generator_eval": {
            "summary": generator_summary,
            "results": all_generator_rows,
        },
    }

    write_json(RESULTS_JSON, output)
    RESULTS_MD.write_text(
        render_markdown(
            all_accuracy_rows,
            accuracy_summary,
            all_generator_rows,
            generator_summary,
        )
    )

    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")
    print("")
    print("Scorer accuracy:")
    print(json.dumps(output["accuracy"]["summary"], indent=2, sort_keys=True))
    print("")
    print("Generator evaluation:")
    print(json.dumps(output["generator_eval"]["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
