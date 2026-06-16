# Benchmark Case Schema

Each benchmark case uses this structure:

benchmark/cases/<library>-<cve-id>/
  meta.json
  reference_upstream_fix.diff
  candidates/
    good_derived.diff
    good_drift.diff
    bad_wrong_function.diff
    bad_over_broad.diff
    bad_incomplete.diff
    aligned_but_wrong.diff
  labels.json

Not every case must include every candidate type, but every candidate that exists must have a label before scoring.

## meta.json

Required fields:

{
  "case_id": "libpng-cve-2025-64505",
  "library": "libpng",
  "cve": "CVE-2025-64505",
  "cwe": "CWE-122",
  "language": "C",
  "upstream_fix_commit": "6a528eb5fd0dd7f6de1c39d30de0e41473431c37",
  "upstream_fix_url": "https://github.com/pnggroup/libpng/commit/6a528eb5fd0dd7f6de1c39d30de0e41473431c37",
  "reference_file": "pngrtran.c",
  "reference_function": "png_set_quantize",
  "notes": "Short human-readable case summary."
}

## labels.json

Labels must be written before scoring.

Example:

{
  "case_id": "libpng-cve-2025-64505",
  "labels_written_before_scoring": true,
  "candidates": {
    "good_derived.diff": {
      "expected_class": "accept",
      "expected_reason": "known_good",
      "construction": "Cosmetic derivative of upstream fix."
    },
    "good_drift.diff": {
      "expected_class": "accept",
      "expected_reason": "known_good_drift",
      "construction": "Logic-preserving derivative with positional drift."
    },
    "bad_wrong_function.diff": {
      "expected_class": "reject",
      "expected_reason": "wrong_function",
      "construction": "Patch relocated to the wrong function."
    }
  }
}

## Expected classes

Allowed expected_class values:

- accept
- reject
- known_blind_spot

## Expected reasons

Suggested expected_reason values:

- known_good
- known_good_drift
- wrong_file
- wrong_function
- over_broad
- under_broad
- parse_error
- known_semantic_blind_spot

## Scorer output

The benchmark harness writes per-candidate scorer output under:

benchmark/results/<case_id>/<candidate_name>.patch_score.json

Aggregate outputs:

benchmark/results.json
benchmark/results.md

## Required label timing

labels.json must be created before running the benchmark harness.

This prevents label leakage from scorer output into expected labels.
