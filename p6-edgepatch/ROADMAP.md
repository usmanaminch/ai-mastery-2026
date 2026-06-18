# EdgePatch Roadmap

EdgePatch is an offline-first C/C++ vulnerability remediation evaluation system for disconnected, air-gapped, and high-assurance environments.

Core principle:

> LLM proposes. Deterministic tools inspect. Sandbox validates. Reporter judges evidence. Human approves.

EdgePatch does not blindly trust generated patches. It turns patch proposals into auditable, reproducible, evidence-gated remediation decisions.

---

## V1 Scope

V1 proves the core remediation evaluation loop.

### Included in V1

- Phase 1 zlib CVE-2022-37434 end-to-end remediation case
- Model-generated candidate patch
- Docker-based validation
- Targeted post-patch reproducer evidence
- Regression test evidence
- Deterministic patch scoring engine
- Source-aware function mapping
- Locality, minimality, and overlap scoring
- Verification reporter producing Markdown and JSON evidence reports
- Provenance-gated benchmark harness
- Four real C libraries:
  - zlib
  - libpng
  - expat
  - libxml2
- Grounded accept cases
- Constructed reject cases
- Separate generator-evaluation section for generated-unverified candidates

Current benchmark posture:

- Scorer accuracy uses only grounded labels.
- Generated-unverified candidates are analyzed separately.
- Structural benchmark results do not claim semantic correctness.
- Behavioral validation belongs to full-pipeline case studies.

---

## V1 Non-Goals

The following are intentionally out of scope for V1:

- Fully autonomous remediation
- Blind trust in model-generated patches
- Live CVE ingestion
- Production-grade patch deployment
- Full local model backend
- Signed offline update packs
- Signed official patch library
- C++ benchmark expansion
- Large-scale benchmark dataset
- Feedback/regeneration loop
- IDE integration
- Pull request automation
- C/C++ to Rust rewriting

---

## Post-V1 Roadmap

### 1. Local Model Backend

Add a pluggable patch-generation interface.

Candidate backends:

- Gemini or another cloud model backend
- Local code-specialized model backend
- llama.cpp backend
- Ollama backend
- MLX backend for Apple Silicon

Preferred local model families:

- Qwen Coder
- DeepSeek Coder
- Codestral-class models

Design rule:

- Generator output is never trusted directly.
- Every generated patch still goes through scoring, sandbox validation, reporting, and human approval.

---

### 2. PatchGenerator Interface

Create a stable generator abstraction.

Example:

    PatchGenerator.generate(
        case_context,
        vulnerability_metadata,
        source_snippet,
        constraints
    ) -> CandidatePatch

Every generated candidate should record:

- model name
- model version
- backend
- prompt hash
- temperature
- top_p
- seed, if available
- generation timestamp
- raw model output
- normalized diff
- apply status

Purpose:

- Make model output reproducible and auditable.

---

### 3. Signed Official Patch Library

Add support for curated official fixes.

The patch library should contain vetted upstream or vendor fixes, not cached generated patches.

Each entry should include:

- CVE ID
- library name
- affected version range
- fixed version range
- upstream commit
- official patch diff
- source URL
- CWE
- package ecosystem metadata
- signature
- pack version

Design rule:

- Official or vetted patch first.
- Generator fallback only when no vetted fix applies.
- Both paths go through the same scorer, validation, reporter, and approval gate.

---

### 4. Offline Update Packs

Support disconnected deployments through signed update packs.

Flow:

    connected staging environment
      -> ingest vulnerability intelligence
      -> curate official fixes
      -> normalize metadata
      -> sign update pack
      -> transfer to disconnected site
      -> verify signature
      -> import into EdgePatch

Possible intelligence sources:

- NVD
- OSV
- GitHub Security Advisories
- vendor advisories
- distro advisories
- commercial threat intelligence

Design rule:

- Disconnected environments should not require live internet access.
- Imported content must be signed and verifiable.

---

### 5. Expanded Behavioral Validation

Future validation modes:

- targeted reproducer
- regression test suite
- sanitizer run
- fuzz harness
- compile-only gate
- static-analysis gate
- containerized sandbox
- resource and time limits
- before/after crash comparison

Purpose:

- Move from structural confidence toward behavioral evidence.

---

### 6. Feedback and Regeneration Loop

Add a bounded loop for failed candidates.

Example:

    generate patch
      -> score patch
      -> reject wrong file/function/under-broad/over-broad
      -> feed structured failure reason back to generator
      -> generate revised candidate
      -> re-score
      -> validate
      -> report

Design rule:

- The loop must be bounded.
- Every iteration must preserve evidence.
- Human approval remains required.

---

### 7. CLI Polish

Move from scripts to a cohesive command-line interface.

Potential commands:

    edgepatch case create
    edgepatch candidate generate
    edgepatch candidate score
    edgepatch candidate validate
    edgepatch report build
    edgepatch benchmark run

Desired UX:

- clear pipeline stages
- patch preview
- evidence summary
- accept/reject gate
- branch-per-patch workflow
- reproducible output paths

---

### 8. C++ Support

Expand beyond C after the C benchmark is stable.

Additional needs:

- C++ function parsing
- namespace and class awareness
- template-aware source mapping
- method-level locality
- build system diversity
- CMake, Bazel, and Make support

C++ is a natural extension, but not a V1 requirement.

---

## Explicitly Out of Scope

### C/C++ to Rust Rewriting

EdgePatch is not a C-to-Rust migration tool.

The goal is secure-in-place remediation for legacy C/C++ systems where rewriting is impractical, too risky, or impossible in the near term.

### Blind Generated Patch Cache

EdgePatch should not cache generated model patches and blindly reuse them.

Generated patches are proposals, not truth.

The safe reusable artifact is a signed library of official or vetted fixes.

### Fully Autonomous Production Patching

EdgePatch may assist remediation, but production deployment should remain human-approved.

---

## Project Thesis

Modern models can propose useful patches, but patch proposals are not evidence.

EdgePatch turns patching into an evidence pipeline:

    proposal
      -> structural inspection
      -> behavioral validation
      -> auditable report
      -> human approval

The value is not that an LLM writes code.

The value is that every patch candidate is forced through deterministic, reproducible, and reviewable gates before anyone trusts it.
