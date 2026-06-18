Role:
You are a senior Python systems engineer building the deterministic evaluation layer for EdgePatch, an offline-first defensive C/C++ vulnerability remediation tool.

Product context:
EdgePatch is designed for disconnected and air-gapped environments such as industrial systems, ICS/SCADA, critical infrastructure, regulated finance, regulated healthcare, aviation software environments, and other networks where source code and vulnerability remediation workflows cannot depend on online LLM calls.

EdgePatch must operate locally/offline, consume trusted vulnerability intelligence and local artifacts, generate or evaluate patches, and produce evidence suitable for human review.

Phase 1 already produced a golden remediation case:

* zlib CVE-2022-37434 on zlib v1.2.11
* proof artifact
* candidate patch
* optimized patch
* Dockerized validation
* targeted post-patch reproducer clean
* standard zlib tests passed functionally with an unrelated upstream sanitizer warning tracked separately

Phase 2 builds the evaluation and reporting side of EdgePatch.

Important safety boundary:
This package does NOT reproduce vulnerabilities.
It does NOT run crashing inputs.
It does NOT generate exploit payloads.
It does NOT analyze how any vulnerability triggers.
It operates only on artifacts provided as inputs:

* patch diffs
* source trees
* proof text already captured elsewhere
* test results already captured elsewhere

Current task:
Implement ONLY Phase 2A: the patch-scoring engine.

Do NOT implement:

* verification reporter
* evidence bundle generator
* SBOM generator
* SARIF generator
* cryptographic signing
* benchmark runner
* website updates
* article content
* LinkedIn content

Build clean, generic, well-tested Python modules under:

eval/patch_score/

Create these files:

eval/patch_score/models.py
eval/patch_score/diff_parser.py
eval/patch_score/source_map.py
eval/patch_score/scorer.py

tests/test_diff_parser.py
tests/test_source_map.py
tests/test_patch_scorer.py

tests/fixtures/source_tree/sample.c
tests/fixtures/diffs/reference_same_function.diff
tests/fixtures/diffs/candidate_same_function.diff
tests/fixtures/diffs/candidate_wrong_file.diff
tests/fixtures/diffs/candidate_overbroad.diff
tests/fixtures/diffs/candidate_underbroad.diff
tests/fixtures/diffs/candidate_multifile.diff
tests/fixtures/diffs/candidate_deleted_file.diff

Module purpose:
Given:

* candidate unified diff
* reference unified diff
* source tree

Output:
A deterministic structured JSON comparison explaining how closely the candidate patch matches the reference patch.

The output must include:

1. Locality

* files touched by candidate
* files touched by reference
* functions touched by candidate
* functions touched by reference
* line ranges touched by candidate
* line ranges touched by reference
* whether candidate stayed in the same file/function/region as reference

2. Minimality

* candidate lines added
* candidate lines removed
* candidate total changed lines
* reference lines added
* reference lines removed
* reference total changed lines
* minimality_ratio = candidate_changed_lines / max(reference_changed_lines, 1)
* minimality_label:

  * tight if <= 1.25
  * acceptable if <= 2.0
  * broad if <= 4.0
  * sprawling if > 4.0

3. Overlap

* same_file boolean
* same_function boolean
* line_overlap_ratio
* function_overlap_ratio
* overlap_score

4. Verdict
   Return a single verdict object with:

* label
* confidence
* explanation
* failure_taxonomy list

Supported verdict labels:

* strong_match
* acceptable_broader
* wrong_function
* wrong_file
* under_broad
* over_broad
* parse_error

Failure taxonomy values:

* wrong_file
* wrong_function
* over_broad
* under_broad
* low_line_overlap
* parse_error

Scoring rules:

locality_score:

* 1.0 same file, same function, overlapping lines
* 0.8 same file, same function, no line overlap
* 0.5 same file, different function
* 0.0 different file

minimality_ratio:
candidate_changed_lines / max(reference_changed_lines, 1)

minimality_label:

* tight if <= 1.25
* acceptable if <= 2.0
* broad if <= 4.0
* sprawling if > 4.0

under_broad:

* candidate is under_broad if minimality_ratio < 0.5 AND line_overlap_ratio < 0.3

over_broad:

* candidate is over_broad if same_file is true, same_function is true, and minimality_label is sprawling

acceptable_broader:

* candidate is acceptable_broader if same_file is true, same_function is true, minimality_label is broad, and line_overlap_ratio >= 0.3

strong_match:

* candidate is strong_match if same_file is true, same_function is true, line_overlap_ratio >= 0.3, and minimality_label is tight or acceptable

Verdict precedence:
Use strict first-match-wins ordering:

1. parse_error
2. wrong_file
3. wrong_function
4. over_broad
5. under_broad
6. acceptable_broader
7. strong_match
8. otherwise use under_broad if candidate_changed_lines < reference_changed_lines, else acceptable_broader

confidence:
Do not invent confidence subjectively.
Compute confidence deterministically as:

confidence = round((0.6 * locality_score) + (0.4 * overlap_score), 3)

Implementation requirements:

1. models.py
   Use dataclasses and type hints for:

* DiffLine
* DiffHunk
* FileDiff
* FunctionRange
* PatchFootprint
* PatchScore
* Verdict

Each top-level result should support deterministic JSON output with stable key ordering.

Every collection in JSON must be sorted before serialization:

* files
* functions
* line ranges
* failure taxonomy values
* any derived sets

Do not rely on raw set ordering.

2. diff_parser.py
   Parse unified diff text without shelling out.

Support common diff headers:

* diff --git a/file b/file
* --- a/file
* +++ b/file
* @@ -old_start,old_count +new_start,new_count @@ optional context

Return structured objects containing:

* old file path
* new file path
* hunks
* old start / old count
* new start / new count
* added lines
* removed lines
* context lines
* changed old line numbers
* changed new line numbers

Multi-file diffs:

* Support multi-file diffs by returning one FileDiff per file.
* Score candidate/reference patches across all files touched.

New/deleted files:

* If a diff uses /dev/null, parse it cleanly.
* Mark created or deleted files explicitly on FileDiff.
* If source mapping cannot map a deleted or created file to functions, do not crash.
* Include the file in the footprint and return an empty function list for that file.

Parse errors:

* Invalid or unsupported diff formats should not crash the program.
* Return a PatchScore with verdict label parse_error and failure_taxonomy containing parse_error.

3. source_map.py
   Given a source tree and a file path, map changed line numbers to enclosing C-like functions.

Use a deterministic regex-plus-brace-depth approach.

Function mapping requirements:

* Identify simple C-like function signatures.
* Once a signature and opening brace are found, count brace depth from the opening { until the matching }.
* The function span is from the signature start line to the matching closing brace line.
* Map changed line numbers to any function span containing those lines.
* Support single-line and multi-line signatures in fixtures.

Known limitations must be documented in a module docstring:

* simple, well-formed C-like functions only
* no K&R style support
* no macro-generated function bodies
* no full C preprocessor expansion
* no Tree-sitter in this first version

Do not mutate the source tree.

4. scorer.py
   Expose a function:

score_patches(
candidate_diff: Path,
reference_diff: Path,
source_tree: Path,
) -> PatchScore

PatchScore.to_json() should return stable, pretty JSON.

5. Tests
   Use pytest.
   Tests must be deterministic.
   Use only synthetic fixtures.
   Do not call network APIs.
   Do not call cloud APIs.
   Do not run crashing inputs.
   Do not require Docker.
   Do not require real CVE artifacts.

Tests should cover:

* parsing a unified diff
* extracting added/removed/context lines
* parsing multi-file diffs
* parsing /dev/null deleted-file diffs
* mapping changed lines to functions
* mapping changed lines to a multi-line C function signature
* candidate same function as reference
* candidate wrong file
* candidate wrong function
* candidate over-broad
* candidate under-broad using numeric threshold
* verdict precedence
* deterministic JSON output with sorted collections

6. Quality

* Keep code readable and small.
* Use standard library only unless pytest for tests.
* No network calls.
* No shelling out for parsing.
* No source mutation.
* Include concise module docstrings explaining:

  * how structural diff comparison works
  * why locality and minimality are useful proxy signals for patch quality
  * why this is safe for offline evaluation

After implementation:

* Print files created
* Show how to run tests
* Show one example JSON output
* Stop

