from pathlib import Path
import os
from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview")

prompt_path = Path("prompts/libpng_cve_2025_64505_candidate_patch.md")
context_path = Path("eval_cases/libpng-cve-2025-64505/context/png_do_quantize_context.c")
out_path = Path("eval_cases/libpng-cve-2025-64505/candidate_gemini_pro_patch.diff")
raw_path = Path("eval_cases/libpng-cve-2025-64505/candidate_gemini_pro_patch.raw.txt")

prompt = prompt_path.read_text()
context = context_path.read_text()

guardrail = """
Return ONLY a unified diff for targets/libpng/pngrtran.c.
Do not include markdown fences.
Do not include prose.
Do not include exploit, reproducer, or test input content.
"""

client = genai.Client()
print(f"Calling Gemini model: {MODEL}")

response = client.models.generate_content(
    model=MODEL,
    contents=guardrail + "\n\n" + prompt + "\n\nSOURCE CONTEXT:\n" + context,
)

raw = response.text or ""
raw_path.write_text(raw)

# Strip accidental markdown fences if present.
clean = raw.strip()
if clean.startswith("```"):
    lines = clean.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    clean = "\n".join(lines).strip()

if "--- " not in clean or "+++ " not in clean or "@@" not in clean:
    raise SystemExit(f"Generated output does not look like a unified diff. Raw saved to {raw_path}")

out_path.write_text(clean + "\n")
print(f"Wrote {out_path}")
print(f"Raw output saved to {raw_path}")
