We tested Phase 2A patch scoring against the real zlib CVE-2022-37434 artifacts.

Observed real-case output:
- files_touched_by_candidate: ["inflate.c"]
- files_touched_by_reference: ["inflate.c"]
- line_overlap_ratio: 1.0
- minimality_ratio: 2.0
- minimality_label: "acceptable"
- functions_touched_by_candidate: []
- functions_touched_by_reference: []
- current verdict: "wrong_function"

This is a false negative.

Reason:
Real zlib source may use C declaration styles or macro-heavy signatures that the first simple source_map.py cannot map. When both candidate and reference function lists are empty, function mapping is unavailable, not proof of wrong function.

Task:
Harden Phase 2A for real-world C code.

Allowed changes:
- eval/patch_score/source_map.py
- eval/patch_score/scorer.py
- eval/patch_score/models.py only if needed
- tests/test_source_map.py
- tests/test_patch_scorer.py
- tests/fixtures/source_tree/sample.c only if needed
- tests/fixtures/diffs/*.diff only if needed

Requirements:

1. Do not weaken wrong_function generally.
If both candidate and reference function sets are non-empty and have no overlap, wrong_function should still be returned.

2. Add fallback behavior:
If both candidate and reference function sets are empty, and same_file is true, use line overlap as the locality signal.
- If line_overlap_ratio >= 0.3 and minimality_label is tight or acceptable, verdict should be strong_match.
- If line_overlap_ratio >= 0.3 and minimality_label is broad, verdict should be acceptable_broader.
- If line_overlap_ratio >= 0.3 and minimality_label is sprawling, verdict should be over_broad.
- If line_overlap_ratio < 0.3 and minimality_ratio < 0.5, verdict should be under_broad.

3. Add function-mapping status to locality output:
- function_mapping_status should be one of:
  - "mapped"
  - "unmapped_candidate"
  - "unmapped_reference"
  - "unmapped_both"
- For the zlib-like fallback case, status should be "unmapped_both".

4. Improve source_map.py if reasonable:
Support simple older C/K&R-style function definitions where the function name appears before a parameter declaration block and the opening brace appears later, for example:
int ZEXPORT inflate(strm, flush)
z_streamp strm;
int flush;
{
    ...
}

Use brace-depth to determine span after the opening brace is found.
Document limitations clearly.

5. Add deterministic tests:
- A test where both function sets are empty but same file and line overlap is strong should NOT return wrong_function.
- A test where both function sets are non-empty but do not overlap should still return wrong_function.
- Existing tests must continue to pass.

6. Safety:
- No vulnerability reproduction.
- No crashing inputs.
- No network calls.
- No shelling out for diff parsing.
- Standard library only except pytest.

After changes, all tests must pass with:
python -m pytest -q
