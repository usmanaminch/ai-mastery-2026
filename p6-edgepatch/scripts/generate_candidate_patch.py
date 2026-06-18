from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google import genai


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")


def strip_markdown_fences(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return clean


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an AI candidate patch for a benchmark case."
    )
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-name", default="candidate_gemini_pro.diff")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    case_dir = ROOT / "benchmark" / "cases" / args.case_id
    meta_path = case_dir / "meta.json"
    prompt_path = case_dir / "prompt" / "candidate_patch.md"

    if not meta_path.exists():
        raise SystemExit(f"Missing meta.json: {meta_path}")

    if not prompt_path.exists():
        raise SystemExit(f"Missing prompt: {prompt_path}")

    meta = json.loads(meta_path.read_text())
    prompt = prompt_path.read_text()

    out_path = case_dir / "candidates" / args.output_name
    raw_path = case_dir / "candidates" / f"{Path(args.output_name).stem}.raw.txt"

    guardrail = f"""
Return ONLY a unified diff for {meta['reference_file']}.
Do not include markdown fences.
Do not include prose.
Do not include exploit, reproducer, or test input content.
Do not patch unrelated files.
"""

    client = genai.Client()
    print(f"Calling Gemini model: {args.model}")
    print(f"Case: {args.case_id}")

    response = client.models.generate_content(
        model=args.model,
        contents=guardrail + "\n\n" + prompt,
    )

    raw = response.text or ""
    raw_path.write_text(raw)

    clean = strip_markdown_fences(raw)

    if "--- " not in clean or "+++ " not in clean or "@@" not in clean:
        raise SystemExit(
            f"Generated output does not look like a unified diff. Raw saved to {raw_path}"
        )

    out_path.write_text(clean + "\n")
    print(f"Wrote {out_path}")
    print(f"Raw output saved to {raw_path}")


if __name__ == "__main__":
    main()
