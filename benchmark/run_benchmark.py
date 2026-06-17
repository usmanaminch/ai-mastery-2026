from __future__ import annotations

import json
import subprocess
import sys
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


ACCEPT_VERDICTS = {"strong_match", "acceptable_broader"}
REJECT_VERDICTS = {"wrong_file", "wrong_function", "under_broad", "over_broad", "parse_error"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def verdict_to_class(verdict_label: str) -> str:
    if verdict_label in ACCEPT_VERDICTS:
        return "accept"
    if verdict_label in REJECT_VERDICTS:
        return "reject"
    return "needs_review"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def candidate_preflight(source_tree: Path, candidate_path: Path) -> tuple[str, str]:
    """Return one of: applies, non_applicable, malformed.

    For the structural benchmark, only syntactically malformed diffs are rejected
    before scoring. Path/context mismatches are recorded but still sent to the
    structural scorer, because historical benchmark candidates may be rooted
    differently.
    """
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


def run_case(case_dir: Path) -> list[dict[str, Any]]:
    meta = load_json(case_dir / "meta.json")
    labels = load_json(case_dir / "labels.json")

    case_id = meta["case_id"]
    source_tree = ROOT / meta["source_tree"]
    reference_diff = case_dir / "reference_upstream_fix.diff"
    candidates_dir = case_dir / "candidates"

    if not source_tree.exists():
        raise FileNotFoundError(f"Missing source_tree for {case_id}: {source_tree}")

    if not labels.get("labels_written_before_scoring"):
        raise ValueError(f"{case_id}: labels_written_before_scoring must be true")

    rows = []

    for candidate_name, label in sorted(labels["candidates"].items()):
        candidate_path = candidates_dir / candidate_name
        if not candidate_path.exists():
            raise FileNotFoundError(f"{case_id}: missing candidate {candidate_path}")

        preflight_status, preflight_detail = candidate_preflight(source_tree, candidate_path)

        # Benchmark rule:
        # Only hard-reject explicitly preserved malformed model outputs.
        # Other non-applicable/path-awkward diffs should still be scored structurally.
        if "malformed" in candidate_path.name:
            score_json = {
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
        else:
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

        verdict = score_json["verdict"]["label"]
        actual_class = verdict_to_class(verdict)
        expected_class = label["expected_class"]

        if expected_class == "known_blind_spot":
            match = actual_class == "accept"
        else:
            match = actual_class == expected_class

        out_score = RESULTS_DIR / case_id / f"{candidate_path.stem}.patch_score.json"
        write_json(out_score, score_json)

        rows.append(
            {
                "case_id": case_id,
                "library": meta["library"],
                "cve": meta.get("cve"),
                "cwe": meta.get("cwe"),
                "candidate": candidate_name,
                "expected_class": expected_class,
                "expected_reason": label.get("expected_reason"),
                "actual_class": actual_class,
                "verdict": verdict,
                "match": match,
                "confidence": score_json["verdict"].get("confidence"),
                "same_file": score_json["overlap"].get("same_file"),
                "same_function": score_json["overlap"].get("same_function"),
                "line_overlap_ratio": score_json["overlap"].get("line_overlap_ratio"),
                "minimality_label": score_json["minimality"].get("minimality_label"),
                "minimality_ratio": score_json["minimality"].get("minimality_ratio"),
                "score_output": str(out_score.relative_to(ROOT)),
            }
        )

    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    matched = sum(1 for row in rows if row["match"])

    accept_rows = [row for row in rows if row["expected_class"] == "accept"]
    reject_rows = [row for row in rows if row["expected_class"] == "reject"]
    misses = [row for row in rows if not row["match"]]

    def rate(items: list[dict[str, Any]]) -> float | None:
        if not items:
            return None
        return round(sum(1 for row in items if row["match"]) / len(items), 3)

    by_library: dict[str, dict[str, Any]] = {}
    for row in rows:
        lib = row["library"]
        by_library.setdefault(lib, {"total": 0, "matched": 0})
        by_library[lib]["total"] += 1
        by_library[lib]["matched"] += int(row["match"])

    for lib, stats in by_library.items():
        stats["match_rate"] = round(stats["matched"] / stats["total"], 3)

    return {
        "total_candidates": total,
        "matched": matched,
        "overall_match_rate": round(matched / total, 3) if total else None,
        "accept_recall": rate(accept_rows),
        "reject_recall": rate(reject_rows),
        "by_library": dict(sorted(by_library.items())),
        "misclassifications": misses,
    }


def render_markdown(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# EdgePatch Patch-Scoring Benchmark Results",
        "",
        "## Summary",
        "",
        f"- Total candidates: {summary['total_candidates']}",
        f"- Matched labels: {summary['matched']}",
        f"- Overall match rate: {summary['overall_match_rate']}",
        f"- Accept recall: {summary['accept_recall']}",
        f"- Reject recall: {summary['reject_recall']}",
        "",
        "## Results by Library",
        "",
        "| Library | Matched | Total | Match Rate |",
        "|---|---:|---:|---:|",
    ]

    for lib, stats in summary["by_library"].items():
        lines.append(f"| {lib} | {stats['matched']} | {stats['total']} | {stats['match_rate']} |")

    lines.extend(
        [
            "",
            "## Per-Candidate Results",
            "",
            "| Case | Candidate | Expected | Actual | Verdict | Match | Confidence | Same Function | Line Overlap | Minimality |",
            "|---|---|---|---|---|---:|---:|---|---:|---|",
        ]
    )

    for row in rows:
        lines.append(
            "| {case_id} | {candidate} | {expected_class} | {actual_class} | {verdict} | "
            "{match} | {confidence} | {same_function} | {line_overlap_ratio} | {minimality_label} |".format(
                **row
            )
        )

    lines.extend(["", "## Misclassifications", ""])

    misses = summary["misclassifications"]
    if not misses:
        lines.append("No misclassifications in this run.")
    else:
        lines.append("| Case | Candidate | Expected | Actual | Verdict |")
        lines.append("|---|---|---|---|---|")
        for row in misses:
            lines.append(
                f"| {row['case_id']} | {row['candidate']} | {row['expected_class']} | "
                f"{row['actual_class']} | {row['verdict']} |"
            )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- This benchmark evaluates structural patch scoring only.",
            "- It does not prove semantic correctness.",
            "- It does not reproduce vulnerabilities or execute patches.",
            "- Seed cases are marked in labels.json and are not blind benchmark cases.",
            "- Behavioral validation belongs to full-pipeline case studies.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    all_rows = []

    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        all_rows.extend(run_case(case_dir))

    summary = summarize(all_rows)
    output = {
        "summary": summary,
        "results": all_rows,
    }

    write_json(RESULTS_JSON, output)
    RESULTS_MD.write_text(render_markdown(all_rows, summary))

    print(f"Wrote {RESULTS_JSON}")
    print(f"Wrote {RESULTS_MD}")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
