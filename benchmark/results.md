# EdgePatch Patch-Scoring Benchmark Results

## Summary

- Total candidates: 4
- Matched labels: 4
- Overall match rate: 1.0
- Accept recall: 1.0
- Reject recall: 1.0

## Results by Library

| Library | Matched | Total | Match Rate |
|---|---:|---:|---:|
| libpng | 3 | 3 | 1.0 |
| zlib | 1 | 1 | 1.0 |

## Per-Candidate Results

| Case | Candidate | Expected | Actual | Verdict | Match | Confidence | Same Function | Line Overlap | Minimality |
|---|---|---|---|---|---:|---:|---|---:|---|
| libpng-cve-2025-64505 | bad_wrong_function.diff | reject | reject | wrong_function | True | 0.3 | False | 0.0 | tight |
| libpng-cve-2025-64505 | good_derived.diff | accept | accept | strong_match | True | 0.95 | True | 0.75 | tight |
| libpng-cve-2025-64505 | good_drift.diff | accept | accept | strong_match | True | 0.9 | True | 0.5 | acceptable |
| zlib-cve-2022-37434 | good_validated_ai.diff | accept | accept | strong_match | True | 1.0 | True | 1.0 | acceptable |

## Misclassifications

No misclassifications in this run.

## Limitations

- This benchmark evaluates structural patch scoring only.
- It does not prove semantic correctness.
- It does not reproduce vulnerabilities or execute patches.
- Seed cases are marked in labels.json and are not blind benchmark cases.
- Behavioral validation belongs to full-pipeline case studies.
