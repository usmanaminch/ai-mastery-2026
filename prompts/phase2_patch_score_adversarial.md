Extend the EdgePatch Phase 2A patch-scoring validation with an adversarial discrimination set.

Context:
EdgePatch is an offline-first defensive C/C++ remediation workflow. Phase 2A built eval/patch_score, a deterministic structural patch-quality scorer. It compares candidate patch diffs against reference patch diffs and reports locality, minimality, overlap, and verdict.

Goal:
Prove the scorer has discrimination power, not just that it can recognize one good patch.

Important safety boundary:
This task only constructs static patch-diff fixtures and pytest assertions.
It does NOT run patched code.
It does NOT execute any crashing input.
It does NOT reproduce vulnerabilities.
It does NOT analyze how any vulnerability triggers.
It does NOT call network/cloud APIs.
It does NOT require Docker.

Design requirement:
Keep normal pytest tests portable. Do not make pytest depend on targets/zlib or any ignored local checkout.

Implement two layers:

Layer 1: Portable synthetic adversarial pytest suite
Create static synthetic fixtures under:

tests/fixtures/adversarial/

Create pytest cases under:

tests/test_patch_scorer_adversarial.py

The synthetic source tree should be committed under tests/fixtures/adversarial/source_tree/ if needed.

Create candidate/reference diffs that exercise six adversarial cases:

1. wrong_file.diff
- candidate edits a different file than the reference
- expected verdict: wrong_file
- assert same_file is false
- assert failure_taxonomy contains wrong_file

2. wrong_function.diff
- candidate edits the same file but a different mapped function than the reference
- expected verdict: wrong_function
- assert same_file is true
- assert same_function is false
- assert failure_taxonomy contains wrong_function

3. over_broad.diff
- candidate edits the right function and overlaps the reference region
- candidate changes enough lines so minimality_ratio > 4.0
- expected verdict: over_broad
- assert minimality_label is sprawling
- assert failure_taxonomy contains over_broad

4. under_broad.diff
- candidate is structurally too small and has low line overlap
- expected verdict: under_broad
- assert minimality_ratio < 0.5
- assert line_overlap_ratio < 0.3
- assert failure_taxonomy contains under_broad

5. aligned_but_wrong.diff
- candidate edits the same file, same function, and same line region as the reference
- candidate has similar size and high overlap
- patch body intentionally differs in logic
- expected verdict: strong_match
- add a test comment documenting this as a KNOWN LIMITATION:
  structural scoring cannot detect semantic incorrectness when a wrong patch lands in the same file/function/line region
- assert same_file is true
- assert same_function is true
- assert line_overlap_ratio >= 0.3
- assert verdict is strong_match

6. fallback_low_overlap_unmapped.diff
- create a synthetic source/diff setup where function mapping is unavailable for both candidate and reference
- candidate and reference are in the same file but line overlap is low
- expected: must NOT return strong_match
- assert function_mapping_status is unmapped_both
- assert verdict.label != strong_match
- this validates that the line-overlap fallback does not rubber-stamp unmapped patches

Layer 2: Optional real zlib adversarial scorer script
Create a helper script:

scripts/score_zlib_adversarial_cases.py

The script should:
- check whether targets/zlib exists
- if targets/zlib does not exist, print a clear skip message and exit 0
- if it exists, score any diffs under eval_cases/zlib-cve-2022-37434/adversarial/
- write a verdict table JSON to:
  eval_cases/zlib-cve-2022-37434/adversarial_scorecard.json

Do not add real zlib adversarial pytest tests that require targets/zlib.

Requirements:
- Deterministic, standard library only except pytest.
- No source mutation.
- No network calls.
- No shelling out for diff parsing.
- Existing tests must keep passing.
- New tests should be explicit and readable.
- Sort all verdict table output deterministically.

After implementation:
- Print files created.
- Show how to run:
  python -m pytest -q
  python scripts/score_zlib_adversarial_cases.py
- Show a small verdict table across the six synthetic adversarial cases.
- Stop.
