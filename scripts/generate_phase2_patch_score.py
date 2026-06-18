from pathlib import Path
import os
import re
from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

ROOT = Path(".").resolve()
PROMPT_PATH = ROOT / "prompts" / "phase2_patch_score.md"

ALLOWED_PREFIXES = (
    "eval/patch_score/",
    "tests/",
)

SYSTEM_GUARDRAIL = """
You are generating source files for a defensive offline evaluation module.

Return ONLY files in this exact format:

START_FILE: relative/path.py
<file content>
END_FILE

START_FILE: relative/path
<file content>
END_FILE

Rules:
- Only write files under eval/patch_score/ or tests/.
- Do not modify unrelated files.
- Do not include markdown fences.
- Do not include explanation outside START_FILE/END_FILE blocks.
- Use standard library only except pytest in tests.
- No network calls.
- No cloud calls.
- No shelling out for diff parsing.
- No vulnerability reproduction.
- No crashing inputs.
"""

def extract_files(text: str) -> dict[str, str]:
    pattern = re.compile(
        r"START_FILE:\s*(?P<path>[^\n]+)\n(?P<body>.*?)\nEND_FILE",
        re.DOTALL,
    )
    files = {}
    for match in pattern.finditer(text):
        rel_path = match.group("path").strip()
        body = match.group("body")
        if not rel_path.startswith(ALLOWED_PREFIXES):
            raise ValueError(f"Refusing to write outside allowed paths: {rel_path}")
        if ".." in Path(rel_path).parts:
            raise ValueError(f"Refusing path traversal: {rel_path}")
        files[rel_path] = body.rstrip() + "\n"
    return files

def main() -> None:
    if not PROMPT_PATH.exists():
        raise SystemExit(f"Missing prompt file: {PROMPT_PATH}")

    prompt = PROMPT_PATH.read_text()

    client = genai.Client()
    print(f"Calling Gemini model: {MODEL}")

    response = client.models.generate_content(
        model=MODEL,
        contents=SYSTEM_GUARDRAIL + "\n\n" + prompt,
    )

    raw = response.text or ""
    raw_path = ROOT / "phase2_patch_score_raw_gemini_output.txt"
    raw_path.write_text(raw)

    files = extract_files(raw)
    if not files:
        raise SystemExit(
            "No START_FILE blocks found. Raw output saved to "
            "phase2_patch_score_raw_gemini_output.txt"
        )

    for rel_path, body in sorted(files.items()):
        path = ROOT / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        print(f"Wrote {rel_path}")

    print(f"\nGenerated {len(files)} files using {MODEL}.")
    print("Raw output saved to phase2_patch_score_raw_gemini_output.txt")

if __name__ == "__main__":
    main()
