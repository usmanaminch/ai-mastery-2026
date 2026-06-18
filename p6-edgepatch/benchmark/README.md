# EdgePatch Patch-Scoring Benchmark

## Purpose

This benchmark evaluates EdgePatch Phase 2A: the deterministic patch-scoring engine.

The benchmark asks:

> Given a candidate patch, a trusted upstream reference fix, and a source tree, can EdgePatch distinguish structurally good patches from structurally bad patches?

This benchmark is intentionally focused on structural patch quality. It does not attempt to reproduce vulnerabilities, generate crashing inputs, execute patches, or prove semantic correctness.

## Scope

In scope:

- Public C/C++ vulnerability fixes with identifiable upstream commits.
- Candidate-vs-reference structural scoring.
- Known-good and known-bad candidate diffs.
- Deterministic scorer outputs:
  - locality
  - minimality
  - overlap
  - verdict
  - confidence
  - failure taxonomy

Out of scope:

- Vulnerability reproduction.
- Exploit generation.
- Behavioral validation.
- Regression-test execution.
- Runtime proof of semantic correctness.
- LLM-based judging.

Behavioral validation belongs to the deeper full-pipeline case studies, not the core structural benchmark.

## Selection Protocol

To reduce cherry-picking, benchmark cases should be selected using pre-declared inclusion criteria.

Candidate libraries should be well-known C/C++ libraries with public CVE fix history, such as:

- zlib
- libpng
- libjpeg-turbo
- libxml2
- expat
- libtiff

A case is eligible if all of the following are true:

1. The vulnerability has a public CVE or clearly identified security advisory.
2. The upstream fix commit is publicly available.
3. The fix touches C/C++ source code.
4. The patch has a reasonably identifiable affected file/function/region.
5. The reference fix is small enough for structural comparison to be meaningful.
6. The case is not excluded simply because EdgePatch scores it poorly.

Preferred CWE families for v1:

- CWE-120: Buffer Copy without Checking Size of Input
- CWE-121: Stack-based Buffer Overflow
- CWE-122: Heap-based Buffer Overflow
- CWE-787: Out-of-bounds Write
- Related memory-safety issues may be included if the upstream fix is clear.

## Anti-Cherry-Picking Rule

Once a case is added to the benchmark candidate list and meets inclusion criteria, it should remain in the benchmark even if the scorer performs poorly.

Failures are benchmark findings, not cleanup tasks.

## Labeling Protocol

Labels must be written before scoring.

Each candidate patch receives an expected class:

- `accept`
- `reject`

And an expected reason, such as:

- `known_good`
- `known_good_drift`
- `wrong_file`
- `wrong_function`
- `over_broad`
- `under_broad`
- `parse_error`
- `known_semantic_blind_spot`

Labels should be based on construction, not scorer output.

## Candidate Types

Each case should include several candidate diffs when feasible:

1. `good_derived.diff`
   - Derived from the upstream reference fix.
   - Same logic, same function, minor cosmetic differences.
   - Expected label: `accept`.

2. `good_drift.diff`
   - Logic-preserving derivative with more formatting/positional drift.
   - Expected label: `accept`.

3. `bad_wrong_function.diff`
   - Candidate touches the correct file but wrong function/region.
   - Expected label: `reject`.

4. `bad_over_broad.diff`
   - Candidate touches the correct region but makes unnecessarily sprawling changes.
   - Expected label: `reject` or `review`, depending on benchmark label policy.

5. `bad_incomplete.diff`
   - Candidate partially applies the fix or misses a key required change.
   - Expected label: `reject`.

6. `aligned_but_wrong.diff`
   - Candidate lands in the correct file/function/line region but uses wrong logic.
   - Expected label: `known_semantic_blind_spot`.
   - This case documents that structural scoring cannot prove semantic correctness.

## Metrics

The benchmark should report:

- Overall candidate classification rate.
- Accept recall:
  - known-good candidates correctly accepted.
- Reject recall:
  - known-bad candidates correctly rejected.
- Results by library.
- Results by CWE where available.
- Misclassification table.
- Known blind-spot table.

A benchmark result is only credible if it includes failures and limitations.

## Verdict Mapping

Structural scorer verdicts are mapped to benchmark classes as follows:

Accepted:

- `strong_match`
- `acceptable_broader`
- `READY_HIGH_CONFIDENCE` is not used here because this is Phase 2A only.

Rejected:

- `wrong_file`
- `wrong_function`
- `under_broad`
- `over_broad`
- `parse_error`

Special:

- `aligned_but_wrong` style cases may structurally score as accepted.
- These are recorded as known semantic blind spots, not scorer bugs, because structural scoring alone cannot prove semantic correctness.

## Relationship to Full Pipeline

This benchmark evaluates the deterministic structural scorer only.

Full EdgePatch remediation confidence requires additional layers:

1. Diff quality gate.
2. Phase 2A structural scoring.
3. Behavioral validation evidence.
4. Regression-test evidence.
5. Phase 2B verification reporter.
6. Evidence binding/signing.
7. Human approval.

The benchmark is one artifact in that larger pipeline, not a claim of autonomous patch correctness.

## Positioning

EdgePatch is not competing with large multi-agent vulnerability-repair systems on raw patch generation.

EdgePatch focuses on:

- offline operation
- deterministic evaluation
- reproducible scoring
- auditable evidence
- human-reviewable remediation decisions

The benchmark measures whether a small deterministic evaluator can discriminate patch quality in disconnected environments.
