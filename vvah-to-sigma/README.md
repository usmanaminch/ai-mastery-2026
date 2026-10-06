# vvah-to-sigma

Turn findings from Visa's open-source [Vulnerability Agentic Harness (VVAH)](https://github.com/visa/visa-vulnerability-agentic-harness)
into [Sigma](https://sigmahq.io) detection rules, so a SOC can watch for exploitation of a known
vulnerability during the window between "found" and "fix deployed."

## Why

A scanner tells you the code is vulnerable. A patch fixes it, eventually. In between, the
vulnerability is known to you and exploitable by anyone who finds it. Detection rules scoped to the
exact weakness, and ideally the exact endpoint, cover that window, then get retired when the fix ships.

## What it does

For each finding in a VVAH SARIF report it decides, by CWE, which of four buckets applies:

| Bucket | Meaning | Output |
|---|---|---|
| **rule** | Exploitation leaves a signature in logs most teams collect (web access logs, process creation) | One or more Sigma rules |
| **behavioral** | Exploitation looks like a normal request from the wrong person (IDOR, missing authz) | No rule; explains what baselining is needed |
| **uncoverable** | No request-time signal (hardcoded secrets, weak crypto) | No rule; the fix is the only control |
| **unmapped** | No mapping yet | Flagged for manual review |

Every finding appears in `coverage.md`, including the ones it can't write rules for, and says why.
A tool that silently drops findings it can't handle gives false comfort.

Some findings get more than one rule. Command injection gets a web-payload rule (the attack arriving)
and a process rule (the app runtime spawning a shell, i.e. the attack succeeding). Deserialization gets
only the process rule, because its payload rides in cookies or bodies that web logs rarely record.

## Usage

```bash
pip install -r requirements.txt
python -m vvah_to_sigma path/to/<module>_<ts>_report.sarif --out out --repo path/to/scanned/app
```

`--repo` points at the source tree VVAH scanned. The tool reads it to scope each web rule to the
endpoint that reaches the vulnerable line, instead of watching the whole app:

- **Django:** follows `ROOT_URLCONF` through every `include()`, including `from .views import *` and
  class-based views (`.as_view()`). Parameterized paths like `item/<int:pk>` become prefix matches.
- **Flask:** reads `@app.route` / `@bp.route` decorators.
- **Templates:** a finding in an HTML template is mapped to the view(s) that render it.

It never guesses. A finding it can't resolve (settings files, Dockerfiles, unrouted helpers) gets an
unscoped rule, and `coverage.md` says why.

To override or add routes by hand, `--routes routes.yaml` maps a location to one or more URLs. Manual
entries win over derived ones:

```yaml
"introduction/views.py:120": /sql_lab
"introduction/views.py": /labs
```

`--min-confidence 0.8` skips rule generation for low-confidence findings (they still appear in the report).

## Validate and compile

```bash
sigma check -x attacktag -x d3_fendtag out/rules
sigma convert -t splunk --without-pipeline out/rules
sigma convert -t lucene --without-pipeline out/rules
sigma convert -t secops -p pipelines/secops_webserver.yml -p secops_udm out/rules
```

The `attacktag` check is excluded only where it can't download MITRE ATT&CK data; run it when online.

`pipelines/secops_webserver.yml` exists because the Google SecOps Sigma pipeline has no mapping for the
standard web-log fields (`cs-uri-query`, `cs-uri-stem`). It maps them to UDM `target.url`. Check how your
parser populates `target.url` (path only, or full URL with host): the endpoint-scoped rules assume a path.

## Limits

- Signature rules catch common payloads, not every encoding. They are a bridge until the fix ships, not
  a substitute for it.
- Process rules flag the app runtime spawning a shell. Baseline the children your app legitimately spawns
  before enabling them.
- Rule IDs are deterministic per finding, so re-running produces the same IDs and a SIEM can update rules
  in place rather than duplicating them.

## Tests

```bash
python -m pytest -q
```

The test fixture is a hand-written report in VVAH's Markdown format, converted to SARIF by VVAH's own
`md_to_sarif`, so the input matches what a real scan emits.
