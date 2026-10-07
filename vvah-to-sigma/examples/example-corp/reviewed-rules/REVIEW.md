# Review of drafts5 (Opus, 48 CVEs, 25 rules)

Reviewer verdicts on the 25 drafted rules. The review was done by an AI reviewer (Claude, in a working
session, reading each rule against its source text the way a detection engineer would); the author approved
the verdicts and edits. `python -m exposure_to_sigma.draft ... --review` now runs the same step. "Ready for
review" from the automated checks is not approval.

## Repeat with the package's reviewer

The same 25 original drafts were then reviewed with `--recheck --review --review-model claude-opus-5-5`
(a different model from the drafter). Full output: [`ai-review-package-run.md`](ai-review-package-run.md).

| | Keep | Edit | Hunt | Reject |
|---|---|---|---|---|
| Session review (above) | 8 | 11 | 2 | 4 |
| Package reviewer | 3 | 11 | 4 | 7 |

- Same verdict on 10 of 25. Where they differ, the package reviewer was stricter on 12 and looser on 3.
- It caught all four problems in this file's "Reject or rewrite" and fidelity notes: the failed-VPN-login rule
  (2024-20481), generic Java-spawns-shell (2021-45046), the translation stricter than its Splunk source
  (2021-34523), and web rules on firewall syslog with no URIs (2018-0296, 2020-3580).
- It also flagged things the session review missed: rules for hosts already on a fixed version (a hit means an
  attempt, not a compromise), CVEs matched to the wrong product (SD-WAN CVEs on a NetScaler ADC; inventory
  matching ignores versions and product lines), and a description citing the wrong source rule (2023-22515).
- Of the 19 drafts that passed every automated check, it would ship 3 as written; 10 need edits, 3 are hunting
  queries, 3 should be rejected.
- Two AI reviews disagreeing on 15 of 25 is the case for the next layer: replay the attack and run alert-only on
  normal traffic, so approval rests on evidence rather than opinion.

| Verdict | Count | CVEs |
|---|---|---|
| Keep as is | 8 | 2021-26085, 2021-31207, 2023-20269, 2023-22515, 2023-22527, 2023-46805, 2024-21887, 2026-3055 |
| Keep with edits | 11 | 2016-6366, 2017-6316, 2018-0296, 2019-11539, 2019-12989, 2019-12991, 2021-34523, 2022-26138, 2023-6549, 2024-20359, 2024-21893 |
| Hunting query, not an alert | 2 | 2023-3519, 2025-5777 |
| Reject or rewrite | 4 | 2020-3580, 2021-45046, 2024-20481, 2026-88771 |

## Why

- **Keep as is:** faithful translations of Splunk analytics (ProxyShell, Confluence, Ivanti) or tight, sourced indicators (Cisco tunnel groups, Confluence WEB-INF read, NetScaler wsfed probe).
- **Keep with edits:**
  - 2019-12989: an unused selection with mismatched fields (referer, user agent); delete it. Path is matched on the query field; use the URI stem.
  - 2021-34523: requires a Python user agent AND a chain marker in one selection, stricter than the Splunk source; make the user agent optional.
  - 2019-11539 and 2019-12991: one branch matches normal admin use of the diagnostic or patch page; keep only the payload-marker branches. 2019-11539 also doesn't apply to the host's version (inventory issue).
  - 2018-0296: correct, but ASA syslog doesn't log URIs; deploy on proxy or WAF logs. Drop the redundant entries.
  - 2017-6316, 2022-26138: indicators sit in cookies or POST bodies; they fire only where those are logged.
  - 2024-20359: drop the bare generic file-name prefix (it can match legitimate files); fix the log source.
  - 2016-6366: post-crash indicator only (it tells you a crash happened); fix the log source name.
  - 2023-6549, 2024-21893: field names and false-positive notes need tightening for the target proxy schema.
- **Hunting, not alert:** 2023-3519 and 2025-5777 match normal SAML or login traffic; the Splunk sources are hunting searches.
- **Reject or rewrite:**
  - 2020-3580: the payload rides in a POST body and the asset's logs don't carry URIs.
  - 2021-45046: generic "Java spawns a shell" with the source's network sequence dropped; that's generic coverage, not a CVE rule.
  - 2024-20481: every failed VPN login matches; needs a count-threshold correlation rule.
  - 2026-88771: shell metacharacters plus common process terms is noisy, the field names are Elastic-specific, and the log isn't collected.

## Scorecard (48 exploited CVEs on assets that send logs)

| Outcome | CVEs |
|---|---|
| Detection rule, approved (as is or with edits) | 19 |
| Hunting query | 2 |
| Rejected after review | 4 |
| Correctly classified: no signature (DoS) or behavioral | 5 |
| Needs better source text | 16 |
| Refused by the model | 2 |
