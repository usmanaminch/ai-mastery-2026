from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def add_label(case_id: str, candidate_name: str, label: dict) -> None:
    labels_path = ROOT / "benchmark" / "cases" / case_id / "labels.json"
    labels = json.loads(labels_path.read_text())
    labels["candidates"][candidate_name] = label
    write_json(labels_path, labels)
    print(f"Updated labels: {labels_path} -> {candidate_name}")


def find_marker(lines: list[str], markers: list[str]) -> int:
    for marker in markers:
        for idx, line in enumerate(lines):
            if marker in line:
                return idx
    raise SystemExit(f"Could not find any marker: {markers}")


def make_comment_diff(
    *,
    repo_dir: str,
    file_rel: str,
    markers: list[str],
    comment: str,
    out_path: Path,
) -> None:
    repo = ROOT / repo_dir
    source = repo / file_rel

    if not source.exists():
        raise SystemExit(f"Missing source file: {source}")

    original = source.read_text(errors="replace")
    lines = original.splitlines()

    idx = find_marker(lines, markers)
    line = lines[idx]
    indent = line[: len(line) - len(line.lstrip())]

    new_lines = lines[: idx + 1] + [f"{indent}{comment}"] + lines[idx + 1 :]
    source.write_text("\n".join(new_lines) + "\n")

    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--", file_rel],
        check=True,
        text=True,
        capture_output=True,
    ).stdout

    source.write_text(original)

    if not diff.strip():
        raise SystemExit(f"No diff produced for {file_rel}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(diff)
    print(f"Wrote {out_path}")


def make_zlib_wrong_file() -> None:
    case_id = "zlib-cve-2022-37434"
    out = ROOT / "benchmark" / "cases" / case_id / "candidates" / "constructed_wrong_file.diff"

    make_comment_diff(
        repo_dir="targets/zlib",
        file_rel="deflate.c",
        markers=["int ZEXPORT deflate", "deflate("],
        comment="/* EdgePatch constructed reject: wrong file for CVE-2022-37434. */",
        out_path=out,
    )

    add_label(
        case_id,
        "constructed_wrong_file.diff",
        {
            "basis": "Deliberately modifies deflate.c even though the reference fix targets inflate.c.",
            "expected": "reject",
            "failure_class": "wrong_file",
            "provenance": "constructed",
        },
    )


def make_libpng_wrong_function() -> None:
    case_id = "libpng-cve-2025-64505"
    out = ROOT / "benchmark" / "cases" / case_id / "candidates" / "constructed_wrong_function.diff"

    make_comment_diff(
        repo_dir="targets/libpng",
        file_rel="pngrtran.c",
        markers=["png_set_strip_alpha"],
        comment="/* EdgePatch constructed reject: wrong function for CVE-2025-64505. */",
        out_path=out,
    )

    add_label(
        case_id,
        "constructed_wrong_function.diff",
        {
            "basis": "Deliberately modifies png_set_strip_alpha even though the reference fix targets png_set_quantize.",
            "expected": "reject",
            "failure_class": "wrong_function",
            "provenance": "constructed",
        },
    )


def make_expat_malformed() -> None:
    case_id = "expat-cve-2022-25315"
    out = ROOT / "benchmark" / "cases" / case_id / "candidates" / "constructed_malformed.diff"

    out.write_text(
        """--- expat/lib/xmlparse.c
+++ expat/lib/xmlparse.c
@@ this is intentionally malformed
+/* EdgePatch constructed reject: malformed diff. */
"""
    )

    print(f"Wrote {out}")

    add_label(
        case_id,
        "constructed_malformed.diff",
        {
            "basis": "Deliberately malformed unified diff used to test parse_error rejection.",
            "expected": "reject",
            "failure_class": "malformed",
            "provenance": "constructed",
        },
    )


def make_libxml2_under_broad() -> None:
    case_id = "libxml2-cve-2022-40303"
    out = ROOT / "benchmark" / "cases" / case_id / "candidates" / "constructed_under_broad.diff"

    make_comment_diff(
        repo_dir="targets/libxml2",
        file_rel="parser.c",
        markers=["xmlParseNameComplex(xmlParserCtxtPtr ctxt)"],
        comment="/* EdgePatch constructed reject: same function but intentionally incomplete. */",
        out_path=out,
    )

    add_label(
        case_id,
        "constructed_under_broad.diff",
        {
            "basis": "Deliberately same-function but incomplete patch; does not implement the upstream remediation.",
            "expected": "reject",
            "failure_class": "under_broad",
            "provenance": "constructed",
        },
    )


def main() -> None:
    make_zlib_wrong_file()
    make_libpng_wrong_function()
    make_expat_malformed()
    make_libxml2_under_broad()

    print("")
    print("Constructed reject candidates created.")
    print("Now run: python benchmark/run_benchmark.py")


if __name__ == "__main__":
    main()
