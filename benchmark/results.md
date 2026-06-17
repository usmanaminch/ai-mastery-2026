# EdgePatch Patch-Scoring Benchmark Results

## Scorer Accuracy: Grounded Candidates Only

This section includes only candidates with labels grounded by construction or independent verification.

- Total grounded candidates: 5
- Matched: 5
- Overall match rate: 1.0
- Accept recall: 1.0
- Reject recall: None

### Accuracy by Library

| Library | Matched | Total | Match Rate |
|---|---:|---:|---:|
| expat | 1 | 1 | 1.0 |
| libpng | 2 | 2 | 1.0 |
| libxml2 | 1 | 1 | 1.0 |
| zlib | 1 | 1 | 1.0 |

### Accuracy by CWE

| CWE | Matched | Total | Match Rate |
|---|---:|---:|---:|
| CWE-122 | 2 | 2 | 1.0 |
| CWE-190 | 2 | 2 | 1.0 |
| CWE-787 | 1 | 1 | 1.0 |

### Grounded Per-Candidate Results

| Case | Candidate | Provenance | Expected | Actual | Verdict | Match | Confidence |
|---|---|---|---|---|---|---:|---:|
| expat-cve-2022-25315 | good_derived.diff | derived | accept | accept | strong_match | True | 1.0 |
| libpng-cve-2025-64505 | good_derived.diff | derived | accept | accept | strong_match | True | 0.95 |
| libpng-cve-2025-64505 | good_drift.diff | derived | accept | accept | strong_match | True | 0.9 |
| libxml2-cve-2022-40303 | good_derived.diff | derived | accept | accept | strong_match | True | 1.0 |
| zlib-cve-2022-37434 | good_validated_ai.diff | generated_verified | accept | accept | strong_match | True | 1.0 |

### Grounded Misclassifications

No grounded misclassifications in this run.

## Generator Evaluation: Unverified Model Outputs

This section records scorer verdicts for generated candidates whose ground truth has not been independently verified.
No accuracy claim is made for these candidates.

- Total generated-unverified candidates: 3
- Verdict distribution: {'parse_error': 1, 'under_broad': 1, 'wrong_function': 1}
- Class distribution: {'reject': 3}

### Generator-Eval Per-Candidate Results

| Case | Candidate | Generator Verdict | Class | Confidence | Same File | Same Function | Line Overlap | Minimality |
|---|---|---|---|---:|---|---|---:|---|
| expat-cve-2022-25315 | candidate_gemini_pro_malformed.diff | parse_error | reject | 1.0 | None | None | None | None |
| libpng-cve-2025-64505 | bad_wrong_function.diff | wrong_function | reject | 0.3 | True | False | 0.0 | tight |
| libxml2-cve-2022-40303 | candidate_gemini_pro.diff | under_broad | reject | 0.616 | True | True | 0.022 | tight |

## Limitations

- This benchmark evaluates structural patch scoring only.
- It does not prove semantic correctness.
- It does not reproduce vulnerabilities or execute patches.
- Generated-unverified candidates are excluded from scorer accuracy.
- Behavioral validation belongs to full-pipeline case studies.
