Implement ONLY Phase 2B of EdgePatch: the Verification Reporter.

Context:
EdgePatch is an offline-first defensive C/C++ remediation workflow for disconnected environments. Phase 1 produced a real zlib CVE remediation case. Phase 2A built a deterministic structural patch scorer that compares a candidate patch against a reference patch and reports locality, minimality, overlap, and verdict.

Phase 2B exists because Phase 2A has an intentional limitation:
Structural scoring can tell whether a patch landed in the right file/function/line region, but it cannot prove semantic correctness. A structurally aligned but logically wrong patch can still receive a strong structural score.

Core design principle:
Structural alignment alone must never green-light a patch. Behavioral evidence is required.

Safety boundary:
This package consumes pre-captured artifacts and produces a report.
It does NOT run crashing inputs.
It does NOT reproduce vulnerabilities.
It does NOT execute patches.
It does NOT run the test suite.
It does NOT verify anything itself.
All behavioral results are inputs captured elsewhere.
This code only aggregates, validates, and judges supplied evidence.

Do NOT implement:

* evidence bundle generator
* SBOM generator
* SARIF generator
* cryptographic signing
* benchmark runner
* website updates
* article content
* LinkedIn content

Build clean, generic, well-tested Python under:

eval/report/

Use standard library only, except pytest for tests.

Create these files:

eval/report/**init**.py
eval/report/models.py
eval/report/inputs.py
eval/report/verdict.py
eval/report/render.py
eval/report/reporter.py

Tests:

tests/test_report_inputs.py
tests/test_report_verdict.py
tests/test_report_render.py
tests/test_reporter.py

Synthetic fixtures:

tests/fixtures/report_cases/

Required input files per case:

1. patch_score.json
   Produced by Phase 2A. Must include at least:

* verdict.label
* verdict.confidence
* locality
* minimality
* overlap

2. post_patch_result.json
   Schema:
   {
   "crash_resolved": true,
   "detail": "Targeted post-patch check exited cleanly.",
   "source": "pre-captured docker validation log"
   }

3. test_suite_result.json
   Schema:
   {
   "passed": true,
   "total": 100,
   "failed": 0,
   "warnings": 0,
   "detail": "Standard test suite passed.",
   "source": "pre-captured test-suite output"
   }

4. proof.txt
   Raw proof artifact text captured elsewhere.

Important:
Any missing or unparseable required input must be flagged.
Do not silently default missing evidence to pass or fail.

Data models:

models.py should define dataclasses with type hints:

* BehavioralResult

  * crash_resolved: Optional[bool]
  * detail: str
  * source: str

* TestSuiteResult

  * passed: Optional[bool]
  * total: int
  * failed: int
  * warnings: int
  * detail: str
  * source: str

* StructuralResult

  * verdict_label: str
  * confidence: float
  * locality: dict
  * minimality: dict
  * overlap: dict

* CombinedVerdict

  * label: str
  * confidence: float
  * explanation: str
  * reasons: list[str]
  * required_human_actions: list[str]

* RemediationReport

  * case_id: str
  * combined_verdict: CombinedVerdict
  * structural: StructuralResult
  * behavioral: BehavioralResult
  * test_suite: TestSuiteResult
  * proof_excerpt: str
  * evidence_inputs: dict
  * limitations: list[str]

All JSON output must be deterministic:

* stable key order
* sorted collections
* no raw set ordering

inputs.py:
Load and validate:

* patch_score.json
* post_patch_result.json
* test_suite_result.json
* proof.txt

If any input is missing or malformed:

* return/report an input error
* final combined verdict should be INCONCLUSIVE

verdict.py:
Implement combined_verdict(structural, behavioral, regression, input_errors) using this exact ordered first-match-wins decision tree:

1. Any required input missing or unparseable
   -> INCONCLUSIVE

2. structural verdict in {wrong_file, wrong_function}
   -> REJECT_WRONG_LOCATION

3. crash_resolved is not True
   -> NEEDS_BEHAVIORAL_VERIFICATION

4. regression suite failed
   -> REJECT_REGRESSION

5. structural verdict == under_broad
   -> REJECT_INCOMPLETE

6. crash_resolved is True and regression passed and structural verdict in {strong_match, acceptable_broader}
   -> READY_HIGH_CONFIDENCE

7. crash_resolved is True and regression passed and structural verdict == over_broad
   -> READY_WITH_CAVEATS

8. otherwise
   -> NEEDS_REVIEW

Confidence:
Compute deterministically.
Suggested:

* Start from structural confidence if available.
* If behavioral crash_resolved is True, keep confidence.
* If regression passed, keep confidence.
* If warning/caveat state, cap at 0.75.
* If rejection or inconclusive, cap at 0.5.
  Do not invent subjective confidence.

render.py:
Render both:

1. Markdown report
2. Stable machine-readable JSON

Markdown report must include:

* title with case_id
* summary verdict
* structural assessment
* behavioral evidence assessment
* regression test assessment
* combined recommendation
* evidence consumed section
* limitations section
* human reviewer checklist

The limitations section must explicitly state:

* Structural scoring cannot prove semantic correctness.
* This reporter does not run code, execute tests, reproduce vulnerabilities, or verify behavior itself.
* It only judges pre-captured evidence supplied as input.

Human reviewer checklist should include:

* Review patch diff manually.
* Confirm behavioral validation was produced in a trusted environment.
* Confirm standard test-suite result source.
* Review any warnings or sanitizer notes.
* Confirm rollback or remediation plan before deployment.

reporter.py:
Expose:

generate_report(case_dir: Path) -> RemediationReport

Also write helper functions if useful:

* write_report(case_dir: Path, out_dir: Path) -> tuple[Path, Path]

Tests:
Use pytest with synthetic fixtures only.

Required tests:

1. READY_HIGH_CONFIDENCE branch.
2. READY_WITH_CAVEATS branch.
3. REJECT_WRONG_LOCATION branch.
4. NEEDS_BEHAVIORAL_VERIFICATION branch.
5. REJECT_REGRESSION branch.
6. REJECT_INCOMPLETE branch.
7. INCONCLUSIVE for missing input.
8. INCONCLUSIVE for malformed JSON.
9. Deterministic JSON output.
10. Deterministic markdown output.

Mandatory blind-spot closure test:
Create a case where:

* structural verdict == strong_match
* crash_resolved == false
  Expected:
* combined verdict == NEEDS_BEHAVIORAL_VERIFICATION

Add a test comment explaining:
This demonstrates how Phase 2B closes Phase 2A's structural blind spot. A patch can be structurally aligned but behaviorally unproven or failed, so it must not be approved.

Quality:

* Keep code readable and small.
* Use standard library only except pytest.
* No network calls.
* No shelling out.
* No Docker.
* No source mutation.
* Do not claim the reporter verified behavior. It only consumes evidence generated elsewhere.

After implementation:

* Print files created.
* Show how to run tests:
  python -m pytest -q
* Show one example markdown report.
* Show one example JSON report.
* Stop.
