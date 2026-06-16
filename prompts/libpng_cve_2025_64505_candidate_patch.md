Role:
You are a senior C systems engineer generating a minimal defensive patch for a public libpng vulnerability.

Safety boundary:
- Do NOT generate exploit inputs.
- Do NOT generate a proof-of-concept file.
- Do NOT describe how to trigger the vulnerability.
- Do NOT run anything.
- Produce only a defensive patch diff.
- Keep the patch minimal and localized.

Context:
This is for EdgePatch, an offline-first defensive C/C++ remediation workflow for disconnected environments.

Target:
- Project: libpng
- CVE: CVE-2025-64505
- Affected area: pngrtran.c, function png_do_quantize
- Public advisory summary: prior to libpng 1.6.51, png_do_quantize has a heap buffer over-read risk involving malformed palette indices. Public advisories describe the fix as allocating quantize_index to PNG_MAX_PALETTE_LENGTH / 256 rather than sizing it based on num_palette.

Input source context:
The file eval_cases/libpng-cve-2025-64505/context/png_do_quantize_context.c contains the relevant vulnerable source context extracted from targets/libpng/pngrtran.c.

Task:
Generate a minimal unified diff patch for targets/libpng/pngrtran.c.

Requirements:
- Touch only pngrtran.c unless absolutely necessary.
- Prefer the smallest localized change inside png_do_quantize.
- Use existing libpng constants/macros where appropriate.
- Preserve style consistent with surrounding code.
- Do not include markdown fences.
- Output ONLY the unified diff.
- Do not include explanation.
