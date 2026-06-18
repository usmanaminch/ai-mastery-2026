# EdgePatch CLI Quickstart

EdgePatch v1 includes a narrow reproducibility CLI.

The goal is not to patch arbitrary codebases yet. The goal is to let a reviewer clone the repository and reproduce the bundled benchmark result locally.

## Run the bundled benchmark

Command:

    python -m edgepatch bench

Expected result:

    Grounded scorer accuracy
    Total grounded candidates : 9
    Matched                   : 9
    Overall match rate        : 1.0
    Accept recall             : 1.0
    Reject recall             : 1.0
    Misclassifications        : 0

## Print JSON output

Command:

    python -m edgepatch bench --json

## Read existing results without rerunning

Command:

    python -m edgepatch bench --no-run

## What this CLI does

- Runs the bundled deterministic benchmark.
- Prints grounded scorer accuracy.
- Prints generated-unverified model findings separately.
- Writes benchmark JSON and Markdown artifacts.

## What this CLI does not do in v1

- It does not run Gemini.
- It does not require internet access.
- It does not require Docker.
- It does not patch arbitrary codebases.
- It does not claim semantic proof.
- It does not replace human approval.

EdgePatch v1 proves the remediation verification layer first.
