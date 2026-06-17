from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def ensure_repo(repo_url: str, repo_dir: Path) -> None:
    if repo_dir.exists():
        print(f"Repo exists: {repo_dir}")
        run(["git", "-C", str(repo_dir), "fetch", "--all", "--tags"])
        return

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {repo_url} -> {repo_dir}")
    run(["git", "clone", repo_url, str(repo_dir)])


def export_reference_fix(repo_dir: Path, fix_commit: str, target_file: str, out_path: Path) -> None:
    print(f"Exporting reference fix {fix_commit} for {target_file}")
    diff = run(
        [
            "git",
            "-C",
            str(repo_dir),
            "show",
            "--format=medium",
            "--no-ext-diff",
            fix_commit,
            "--",
            target_file,
        ]
    )

    if "--- " not in diff or "+++ " not in diff or "@@" not in diff:
        raise SystemExit(
            f"Reference fix did not look like a unified diff for {target_file}. "
            f"Check commit/file path."
        )

    out_path.write_text(diff)
    print(f"Wrote {out_path}")


def checkout_vulnerable_parent(repo_dir: Path, fix_commit: str) -> None:
    parent = f"{fix_commit}^"
    print(f"Checking out vulnerable parent: {parent}")
    run(["git", "-C", str(repo_dir), "checkout", parent])


def extract_context(
    repo_dir: Path,
    target_file: str,
    target_function: str,
    out_path: Path,
    before: int,
    after: int,
) -> None:
    src = repo_dir / target_file
    if not src.exists():
        raise SystemExit(f"Target file does not exist after checkout: {src}")

    lines = src.read_text(errors="replace").splitlines()

    hit = None
    for idx, line in enumerate(lines):
        if target_function in line:
            hit = idx
            break

    if hit is None:
        raise SystemExit(f"Could not find target function text '{target_function}' in {src}")

    start = max(hit - before, 0)
    end = min(hit + after, len(lines))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines[start:end]) + "\n")

    print(f"Wrote {out_path}")
    print(f"Captured source lines {start + 1}-{end}")


def write_meta(args: argparse.Namespace, repo_dir: Path, case_dir: Path) -> None:
    meta = {
        "case_id": args.case_id,
        "library": args.library,
        "cve": args.cve,
        "cwe": args.cwe,
        "language": args.language,
        "upstream_fix_commit": args.fix_commit,
        "upstream_fix_url": args.fix_url,
        "reference_file": args.target_file,
        "reference_function": args.target_function,
        "source_tree": rel(repo_dir),
        "notes": args.notes,
    }

    path = case_dir / "meta.json"
    path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {path}")


def write_prompt(args: argparse.Namespace, case_dir: Path, context_path: Path) -> None:
    prompt_dir = case_dir / "prompt"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    prompt = f"""You are helping evaluate a defensive offline patching system.

Task:
Generate a minimal source patch for {args.cve}.

Context:
- Project/library: {args.library}
- Language: {args.language}
- CWE: {args.cwe}
- Vulnerability summary: {args.vulnerability_summary}
- Target file: {args.target_file}
- Target function: {args.target_function}
- Goal: generate the smallest safe patch that addresses the vulnerability while preserving existing behavior.

Constraints:
- Return a unified diff only.
- Patch only {args.target_file}.
- Prefer the smallest correct guard or size-check.
- Do not include explanation.
- Do not include markdown fences.
- Do not modify unrelated functions.
- Do not include exploit, reproducer, or test input content.
- Do not assume access to the upstream fix.

Vulnerable source context:

{context_path.read_text()}
"""

    path = prompt_dir / "candidate_patch.md"
    path.write_text(prompt)
    print(f"Wrote {path}")


def write_label_stub(args: argparse.Namespace, case_dir: Path) -> None:
    path = case_dir / "labels.stub.json"

    stub = {
        "case_id": args.case_id,
        "labels_written_before_scoring": False,
        "seed_case": False,
        "candidates": {
            "good_derived.diff": {
                "expected_class": "accept",
                "expected_reason": "known_good",
                "construction": "Reference upstream fix used as a strict positive control."
            },
            "candidate_gemini_pro.diff": {
                "expected_class": "TODO_accept_or_reject_before_scoring",
                "expected_reason": "TODO_manual_pre_score_label",
                "construction": "Gemini-generated candidate patch. Inspect manually before scoring."
            }
        }
    }

    path.write_text(json.dumps(stub, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {path}")


def copy_good_derived(case_dir: Path) -> None:
    src = case_dir / "reference_upstream_fix.diff"
    dst = case_dir / "candidates" / "good_derived.diff"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text())
    print(f"Wrote {dst}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a benchmark case skeleton from a CVE fix commit."
    )
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--library", required=True)
    parser.add_argument("--cve", required=True)
    parser.add_argument("--cwe", required=True)
    parser.add_argument("--language", default="C")
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--fix-commit", required=True)
    parser.add_argument("--fix-url", required=True)
    parser.add_argument("--target-file", required=True)
    parser.add_argument("--target-function", required=True)
    parser.add_argument("--vulnerability-summary", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--context-before", type=int, default=35)
    parser.add_argument("--context-after", type=int, default=220)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    case_dir = ROOT / "benchmark" / "cases" / args.case_id
    repo_dir = ROOT / args.repo_dir
    context_path = case_dir / "context" / f"{args.target_function}_context.c"

    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "candidates").mkdir(parents=True, exist_ok=True)

    ensure_repo(args.repo_url, repo_dir)
    export_reference_fix(
        repo_dir=repo_dir,
        fix_commit=args.fix_commit,
        target_file=args.target_file,
        out_path=case_dir / "reference_upstream_fix.diff",
    )
    checkout_vulnerable_parent(repo_dir, args.fix_commit)
    extract_context(
        repo_dir=repo_dir,
        target_file=args.target_file,
        target_function=args.target_function,
        out_path=context_path,
        before=args.context_before,
        after=args.context_after,
    )
    copy_good_derived(case_dir)
    write_meta(args, repo_dir, case_dir)
    write_prompt(args, case_dir, context_path)
    write_label_stub(args, case_dir)

    print("")
    print("Case factory complete.")
    print(f"Case directory: {case_dir}")
    print("")
    print("Next steps:")
    print("1. Generate candidate patch.")
    print("2. Inspect candidate manually.")
    print("3. Copy labels.stub.json to labels.json and set labels before scoring.")


if __name__ == "__main__":
    main()
