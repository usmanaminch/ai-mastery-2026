# EdgePatch Patch-Scoring Benchmark Results

## Summary

- Total candidates: 8
- Matched labels: 7
- Overall match rate: 0.875
- Accept recall: 0.833
- Reject recall: 1.0

## Results by Library

| Library | Matched | Total | Match Rate |
|---|---:|---:|---:|
| expat | 2 | 2 | 1.0 |
| libpng | 3 | 3 | 1.0 |
| libxml2 | 1 | 2 | 0.5 |
| zlib | 1 | 1 | 1.0 |

## Per-Candidate Results

| Case | Candidate | Expected | Actual | Verdict | Match | Confidence | Same Function | Line Overlap | Minimality |
|---|---|---|---|---|---:|---:|---|---:|---|
| expat-cve-2022-25315 | candidate_gemini_pro_malformed.diff | reject | reject | parse_error | True | 1.0 | None | None | None |
| expat-cve-2022-25315 | good_derived.diff | accept | accept | strong_match | True | 1.0 | True | 1.0 | tight |
| libpng-cve-2025-64505 | bad_wrong_function.diff | reject | reject | wrong_function | True | 0.3 | False | 0.0 | tight |
| libpng-cve-2025-64505 | good_derived.diff | accept | accept | strong_match | True | 0.95 | True | 0.75 | tight |
| libpng-cve-2025-64505 | good_drift.diff | accept | accept | strong_match | True | 0.9 | True | 0.5 | acceptable |
| libxml2-cve-2022-40303 | candidate_gemini_pro.diff | accept | reject | under_broad | False | 0.616 | True | 0.022 | tight |
| libxml2-cve-2022-40303 | good_derived.diff | accept | accept | strong_match | True | 1.0 | True | 1.0 | tight |
| zlib-cve-2022-37434 | good_validated_ai.diff | accept | accept | strong_match | True | 1.0 | True | 1.0 | acceptable |

## Misclassifications

| Case | Candidate | Expected | Actual | Verdict |
|---|---|---|---|---|
| libxml2-cve-2022-40303 | candidate_gemini_pro.diff | accept | reject | under_broad |

## Limitations

- This benchmark evaluates structural patch scoring only.
- It does not prove semantic correctness.
- It does not reproduce vulnerabilities or execute patches.
- Seed cases are marked in labels.json and are not blind benchmark cases.
- Behavioral validation belongs to full-pipeline case studies.
