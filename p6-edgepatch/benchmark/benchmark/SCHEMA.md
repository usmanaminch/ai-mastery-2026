# EdgePatch Patch-Scoring Benchmark — Case Schema v2

## Grounding Principle

A candidate may contribute to the SCORER ACCURACY metric only if its ground-truth label was established independently of, and prior to, scoring.

A label is grounded in one of two ways:

1. By construction
2. By independent verification

Model-generated output with an unverified label is never scored for accuracy. It is recorded under GENERATOR EVALUATION only.

## Candidate Provenance

Every candidate in `labels.json` must define one of the following provenance values:

### derived

Built from `reference_upstream_fix.diff` while preserving the same logic.

Examples:

- exact upstream fix copy
- cosmetic-only change
- whitespace-only change
- comment-only drift
- small positional drift that preserves logic

Rules:

- `expected` must be `accept`
- included in SCORER ACCURACY

### constructed

Deliberately built to fail in a named way.

Examples:

- wrong file
- wrong function
- over-broad patch
- under-broad patch
- malformed patch

Rules:

- `expected` must be `reject`
- `failure_class` is required
- included in SCORER ACCURACY

### generated_unverified

Produced by a model, but ground truth has not been independently established.

Rules:

- `expected` must be `null`
- not included in SCORER ACCURACY
- included in GENERATOR EVALUATION only

### generated_verified

Produced by a model, then independently verified.

Examples:

- targeted reproducer passes after patch
- regression tests pass
- Docker/sandbox validation evidence exists
- human/security review accepted the patch with evidence

Rules:

- `expected` must be `accept` or `reject`
- `verification` block is required
- included in SCORER ACCURACY

## Metric Buckets

SCORER ACCURACY:

- derived
- constructed
- generated_verified

GENERATOR EVALUATION:

- generated_unverified

## labels.json Format

{
  "case_id": "example-cve-id",
  "labels_written_before_scoring": true,
  "seed_case": false,
  "candidates": {
    "candidate.diff": {
      "provenance": "derived",
      "expected": "accept",
      "basis": "Reference upstream fix used as known-good control."
    }
  }
}

## Candidate Fields

Each candidate entry supports:

{
  "provenance": "derived | constructed | generated_unverified | generated_verified",
  "expected": "accept | reject | null",
  "basis": "One-line explanation of how the label was established.",
  "failure_class": "wrong_file | wrong_function | over_broad | under_broad | malformed",
  "generator": "gemini-3.1-pro-preview",
  "verification": {
    "method": "behavioral",
    "post_patch_result": "path/to/post_patch_result.json",
    "test_suite_result": "path/to/test_suite_result.json",
    "verified_by": "EdgePatch Phase 1 validation",
    "date": "2026-06-14"
  }
}

## Validation Rules

The benchmark harness must enforce these rules before scoring:

- `labels.json` must exist.
- `labels_written_before_scoring` must be `true`.
- Every candidate file named in `labels.json` must exist.
- Every candidate must define `provenance`.
- `derived` requires `expected == "accept"`.
- `constructed` requires `expected == "reject"` and `failure_class`.
- `generated_unverified` requires `expected == null`.
- `generated_verified` requires `expected` in `{"accept", "reject"}` and a `verification` block.

Any violation is a hard error.

## Results Output

Benchmark results must contain two separate sections:

### SCORER ACCURACY

Grounded candidates only.

Metrics:

- total grounded candidates
- matched
- overall match rate
- accept recall
- reject recall
- by library
- by CWE
- misclassification table

### GENERATOR EVALUATION

Generated-unverified candidates only.

Metrics:

- total generated-unverified candidates
- verdict distribution
- by library
- by CWE
- per-candidate scorer verdicts

No accuracy claim is made for generator-eval candidates.

## Important Boundary

This benchmark evaluates structural patch scoring.

It does not prove semantic correctness.

It does not reproduce vulnerabilities.

It does not execute patches.

Behavioral validation belongs to full-pipeline case studies.
