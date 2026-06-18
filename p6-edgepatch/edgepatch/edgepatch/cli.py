from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = ROOT / "benchmark" / "run_benchmark.py"
RESULTS_JSON = ROOT / "benchmark" / "results.json"
RESULTS_MD = ROOT / "benchmark" / "results.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def run_benchmark() -> None:
    result = subprocess.run(
        [sys.executable, str(BENCHMARK_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print("EdgePatch benchmark failed.\n", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)


def fmt_rate(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)


def print_accuracy_summary(data: dict[str, Any]) -> None:
    summary = data["accuracy"]["summary"]
    rows = data["accuracy"]["results"]

    print("")
    print("EdgePatch Benchmark")
    print("===================")
    print("")
    print("Grounded scorer accuracy")
    print("------------------------")
    print(f"Total grounded candidates : {summary['total_candidates']}")
    print(f"Matched                   : {summary['matched']}")
    print(f"Overall match rate        : {fmt_rate(summary['overall_match_rate'])}")
    print(f"Accept recall             : {fmt_rate(summary['accept_recall'])}")
    print(f"Reject recall             : {fmt_rate(summary['reject_recall'])}")
    print(f"Misclassifications        : {len(summary['misclassifications'])}")
    print("")

    print("By library")
    print("----------")
    for library, stats in summary["by_library"].items():
        print(
            f"{library:<10} {stats['matched']:>2}/{stats['total']:<2} "
            f"match_rate={stats['match_rate']}"
        )
    print("")

    print("Grounded candidate verdicts")
    print("---------------------------")
    for row in rows:
        status = "PASS" if row["match"] else "MISS"
        print(
            f"{status:<5} "
            f"{row['case_id']:<28} "
            f"{row['candidate']:<38} "
            f"expected={row['expected']:<6} "
            f"actual={row['actual_class']:<6} "
            f"verdict={row['verdict']}"
        )


def print_generator_summary(data: dict[str, Any]) -> None:
    summary = data["generator_eval"]["summary"]
    rows = data["generator_eval"]["results"]

    print("")
    print("Generator evaluation")
    print("--------------------")
    print("Generated-unverified candidates are excluded from scorer accuracy.")
    print(f"Total generated-unverified candidates: {summary['total_candidates']}")
    print("")

    print("Verdict distribution")
    print("--------------------")
    for verdict, count in summary["verdict_distribution"].items():
        print(f"{verdict:<18} {count}")
    print("")

    print("Generated-unverified findings")
    print("-----------------------------")
    for row in rows:
        print(
            f"{row['case_id']:<28} "
            f"{row['candidate']:<38} "
            f"verdict={row['verdict']:<15} "
            f"class={row['actual_class']}"
        )


def cmd_bench(args: argparse.Namespace) -> None:
    if not BENCHMARK_SCRIPT.exists():
        raise SystemExit(f"Missing benchmark script: {BENCHMARK_SCRIPT}")

    if not args.no_run:
        run_benchmark()

    if not RESULTS_JSON.exists():
        raise SystemExit(f"Missing benchmark results: {RESULTS_JSON}")

    data = load_json(RESULTS_JSON)

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return

    print_accuracy_summary(data)
    print_generator_summary(data)

    print("")
    print("Artifacts")
    print("---------")
    print(f"JSON report     : {RESULTS_JSON.relative_to(ROOT)}")
    print(f"Markdown report : {RESULTS_MD.relative_to(ROOT)}")
    print("")
    print("Boundary")
    print("--------")
    print("This benchmark evaluates structural patch scoring only.")
    print("Behavioral validation belongs to full-pipeline case studies.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edgepatch",
        description="EdgePatch offline-first remediation evidence CLI",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    bench = subparsers.add_parser(
        "bench",
        help="Run the bundled deterministic benchmark and print results.",
    )
    bench.add_argument(
        "--json",
        action="store_true",
        help="Print full benchmark results JSON after running.",
    )
    bench.add_argument(
        "--no-run",
        action="store_true",
        help="Do not rerun benchmark; read existing benchmark/results.json.",
    )
    bench.set_defaults(func=cmd_bench)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
