# vvah-to-sigma

Two tools for the same gap: the time between "we know we're vulnerable" and "the fix is deployed."

| Your code | Vendor code |
|---|---|
| `vvah_to_sigma`: findings from Visa's VVAH scanner become scoped Sigma rules | `exposure_to_sigma`: exploited CVEs in what you run, checked against your rules and public rules |


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

## Which model runs the scan

The converter uses no LLM. The scan does, and you choose which: see
[`model-profiles/`](model-profiles/README.md) for Anthropic default, an Anthropic budget profile, and any
OpenAI-compatible endpoint (Gemini, local Ollama or vLLM).

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


---

# exposure_to_sigma: vendor and dependency CVEs

Answers, for every CVE in what you run: **is it being exploited, and can you detect it today?**

```
 Trivy / Grype JSON ─┐
 Inventory CSV ──────┼──► exposures ──► exploitation feeds ──► rulesets ──► logs you collect ──► verdict
 Any scanner CSV ────┘                 (CISA KEV, EPSS,       (yours, SigmaHQ,
                                        paid intel)            vendor packs)
```

## Verdicts

| Verdict | Meaning | What to do |
|---|---|---|
| Detected by your rules | Your rule names the CVE and reads a log this asset sends | Confirm it's deployed |
| Public rule available: deploy it | A public rule names it and reads a log you collect | Deploy; retire after patching |
| Generic coverage likely (heuristic) | No rule names it, but a rule for the same weakness class reads a log you collect | Test before relying on it |
| Rule exists, logs not collected | The rule can never fire here | Fix the log pipeline, not the rule |
| No log signature (e.g. denial of service) | Nothing a rule could match | Patch |
| Gap | Nothing names it, nothing generic applies | Draft a scoped rule |

## Inputs

| Input | Flag | Notes |
|---|---|---|
| Trivy JSON | `--trivy` | `trivy fs --scanners vuln --format json` |
| Grype JSON | `--grype` | `grype dir:. -o json`; `--epss-from-grype` reuses the EPSS scores it embeds |
| Inventory CSV | `--inventory` | `asset,vendor,product,version,logs`; matched by product name, **version not checked** |
| Any scanner's CSV export | `--mapped-csv CSV MAPPING` | Tenable, Qualys, Wiz, Rapid7...: a YAML file names the columns |
| CISA KEV | `--kev` | `known_exploited_vulnerabilities.json` from cisagov/kev-data |
| FIRST EPSS | `--epss` | Daily CSV from first.org; CVEs above `--likely` (default 0.1) are prioritised |
| Paid threat intel | `--feed EXPORT MAPPING` | CSV or JSON export plus a field mapping |
| Rulesets | `--own-rules`, `--public-rules` | Any Sigma folders; repeatable |

`logs` (in the inventory, or `--logs` for scanner inputs) lists the log sources that asset sends to your SIEM,
using Sigma's names: `webserver`, `proxy`, `process_creation:linux`, `process_creation:windows`, `fortios`,
`paloalto`, `cisco`. No inventory tool exports this today, so it is the one column you maintain by hand.

API connectors for scanners and intel platforms would implement the same interfaces as the file adapters
(`load_x(...) -> list[Exposure]`, `feed.lookup(cve) -> ExploitSignal`). Example mappings in
`examples/example-corp/` use illustrative column names: set them to your export's real headers.

## Run the examples

```bash
git clone --depth 1 https://github.com/cisagov/kev-data /tmp/kev-data
git clone --depth 1 https://github.com/SigmaHQ/sigma /tmp/sigma

python -m exposure_to_sigma --kev /tmp/kev-data/known_exploited_vulnerabilities.json \
  --inventory examples/example-corp/inventory.csv \
  --mapped-csv examples/example-corp/scanner-export.csv examples/example-corp/scanner-mapping.yaml \
  --asset hr-portal-01 --logs "webserver;process_creation:linux" \
  --own-rules examples/example-corp/rules \
  --public-rules /tmp/sigma/rules --public-rules /tmp/sigma/rules-emerging-threats \
  --out out/example-corp
```

Example Corp is fictional. Its inventory, rules and exports exist only to exercise every verdict.

## Limits

- **Inventory matches ignore versions.** CISA's catalog lists products, not affected versions, so a product
  CSV over-reports. Feed it scanner output for version-accurate results.
- **"Generic coverage likely" is a heuristic** from CWE tags and rule titles. CWE tags can mislead: NVD tags
  some Django denial-of-service bugs as buffer overflows. Treat it as a lead, not a guarantee.
- **Native SIEM rules (SPL, YARA-L, KQL) are not analysed.** Only Sigma folders. Reading what an untagged
  native query detects is a separate problem.
- Test fixtures include rules copied from SigmaHQ under the Detection Rule License 1.1 (see the NOTICE there).
