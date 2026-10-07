# Drafted rules for detection gaps

- Model: anthropic:claude-opus-5
- Gap CVEs drafted: 48
- Tokens: {"input_tokens": 329433, "output_tokens": 44075, "calls": 48}
- Rechecked: 2026-10-07
- Reviewer: anthropic:claude-opus-5-5 (tokens {"input_tokens": 237073, "output_tokens": 27189, "calls": 25})

Every rule here is a **draft** (status: experimental) written by a model from public advisory text. The checks below are mechanical: they catch invented indicators, rules for logs you don't collect, and syntax errors. They do not show a rule catches the exploit or stays quiet on normal traffic. A person approves what ships; the AI review column, when present, is a second model's opinion to speed that up, not an approval.

| CVE | Task | Assets | Outcome | Logs collected | Grounded values | Syntax | AI review | File |
|---|---|---|---|---|---|---|---|---|
| CVE-2018-8581 | draft | mail-01 | insufficient_info | - | - | - | - | - |
| CVE-2019-11539 | draft | ivanti-vpn-01 | review: ungrounded values | yes | 7/8 | pass | edit | `rules/draft_cve_2019_11539.yml` |
| CVE-2020-3259 | draft | edge-fw-01 | insufficient_info | - | - | - | - | - |
| CVE-2020-3580 | draft | edge-fw-01 | review: logs not collected | **no** | 6/6 (+1 method/status) | pass | reject | `rules/draft_cve_2020_3580.yml` |
| CVE-2021-26085 | draft | wiki-01 | ready for review | yes | 3/3 (+1 method/status) | pass | edit | `rules/draft_cve_2021_26085.yml` |
| CVE-2021-27065 | draft | mail-01 | insufficient_info | - | - | - | - | - |
| CVE-2021-31207 | translate | mail-01 | ready for review | yes | 4/4 (+2 method/status) | pass | edit | `rules/draft_cve_2021_31207.yml` |
| CVE-2021-34523 | translate | mail-01 | ready for review | yes | 6/6 (+2 method/status) | pass | edit | `rules/draft_cve_2021_34523.yml` |
| CVE-2021-45046 | translate | hr-portal-01 | review: ungrounded values | yes | 7/37 | pass | hunting query | `rules/draft_cve_2021_45046.yml` |
| CVE-2023-20269 | draft | edge-fw-01 | ready for review | yes | 4/4 | pass | edit | `rules/draft_cve_2023_20269.yml` |
| CVE-2023-22515 | translate | wiki-01 | ready for review | yes | 2/2 (+2 method/status) | pass | edit | `rules/draft_cve_2023_22515.yml` |
| CVE-2023-22527 | translate | wiki-01 | ready for review | yes | 1/1 (+3 method/status) | pass | keep | `rules/draft_cve_2023_22527.yml` |
| CVE-2023-3519 | translate | citrix-gw-01 | ready for review | yes | 7/7 (+1 method/status) | pass | hunting query | `rules/draft_cve_2023_3519.yml` |
| CVE-2023-46805 | translate | ivanti-vpn-01 | ready for review | yes | 5/5 (+7 method/status) | pass | keep | `rules/draft_cve_2023_46805.yml` |
| CVE-2024-21887 | translate | ivanti-vpn-01 | ready for review | yes | 3/3 (+5 method/status) | pass | edit | `rules/draft_cve_2024_21887.yml` |
| CVE-2024-21893 | translate | ivanti-vpn-01 | ready for review | yes | 4/4 (+2 method/status) | pass | hunting query | `rules/draft_cve_2024_21893.yml` |
| CVE-2025-0282 | draft | ivanti-vpn-01 | refused | - | - | - | - | - |
| CVE-2025-22457 | draft | ivanti-vpn-01 | refused | - | - | - | - | - |
| CVE-2025-5777 | translate | citrix-gw-01 | ready for review | yes | 1/1 (+2 method/status) | pass | hunting query | `rules/draft_cve_2025_5777.yml` |
| CVE-2014-2120 | draft | edge-fw-01 | insufficient_info | - | - | - | - | - |
| CVE-2016-6366 | draft | edge-fw-01 | ready for review | yes | 2/2 | pass | reject | `rules/draft_cve_2016_6366.yml` |
| CVE-2016-6367 | draft | edge-fw-01 | insufficient_info | - | - | - | - | - |
| CVE-2017-6316 | draft | citrix-gw-01 | review: ungrounded values | yes | 5/7 | pass | reject | `rules/draft_cve_2017_6316.yml` |
| CVE-2018-0296 | draft | edge-fw-01 | review: logs not collected | **no** | 4/4 | pass | reject | `rules/draft_cve_2018_0296.yml` |
| CVE-2019-12989 | draft | citrix-gw-01 | ready for review | yes | 4/4 (+1 method/status) | pass | reject | `rules/draft_cve_2019_12989.yml` |
| CVE-2019-12991 | draft | citrix-gw-01 | ready for review | yes | 6/6 | pass | edit | `rules/draft_cve_2019_12991.yml` |
| CVE-2020-8243 | draft | ivanti-vpn-01 | insufficient_info | - | - | - | - | - |
| CVE-2020-8260 | draft | ivanti-vpn-01 | insufficient_info | - | - | - | - | - |
| CVE-2021-22894 | draft | ivanti-vpn-01 | insufficient_info | - | - | - | - | - |
| CVE-2021-22899 | draft | ivanti-vpn-01 | insufficient_info | - | - | - | - | - |
| CVE-2021-22900 | draft | ivanti-vpn-01 | insufficient_info | - | - | - | - | - |
| CVE-2021-31196 | draft | mail-01 | insufficient_info | - | - | - | - | - |
| CVE-2022-26138 | draft | wiki-01 | ready for review | yes | 4/4 | pass | reject | `rules/draft_cve_2022_26138.yml` |
| CVE-2023-6548 | draft | citrix-gw-01 | insufficient_info | - | - | - | - | - |
| CVE-2023-6549 | draft | citrix-gw-01 | ready for review | yes | 2/2 (+1 method/status) | pass | keep | `rules/draft_cve_2023_6549.yml` |
| CVE-2024-20353 | draft | edge-fw-01 | no_signature | - | - | - | - | - |
| CVE-2024-20359 | draft | edge-fw-01 | ready for review | yes | 7/7 | pass | edit | `rules/draft_cve_2024_20359.yml` |
| CVE-2024-20481 | draft | edge-fw-01 | ready for review | yes | 3/3 | pass | edit | `rules/draft_cve_2024_20481.yml` |
| CVE-2024-21410 | draft | mail-01 | insufficient_info | - | - | - | - | - |
| CVE-2025-6543 | draft | citrix-gw-01 | insufficient_info | - | - | - | - | - |
| CVE-2025-7775 | draft | citrix-gw-01 | insufficient_info | - | - | - | - | - |
| CVE-2026-19490 | draft | citrix-gw-01 | behavioral | - | - | - | - | - |
| CVE-2026-20349 | draft | edge-fw-01 | no_signature | - | - | - | - | - |
| CVE-2026-3055 | draft | citrix-gw-01 | ready for review | yes | 3/3 (+1 method/status) | pass | edit | `rules/draft_cve_2026_3055.yml` |
| CVE-2026-8452 | draft | citrix-gw-01 | no_signature | - | - | - | - | - |
| CVE-2026-88771 | translate | citrix-gw-01 | review: ungrounded values, logs not collected | **no** | 12/26 | pass | reject | `rules/draft_cve_2026_88771.yml` |
| CVE-2026-88772 | draft | citrix-gw-01 | insufficient_info | - | - | - | - | - |
| CVE-2026-88779 | draft | citrix-gw-01 | no_signature | - | - | - | - | - |

## Notes per CVE

### CVE-2018-8581: Exchange Server elevation of privilege / user impersonation
- The advisory text contains only a generic description of an elevation-of-privilege/impersonation flaw in Exchange Server with no URL path, parameter, header, API endpoint, process name, or log message that an exploit attempt would leave behind. Every reference is a broken link or a vendor patch page, and no scanner check or source detection rule is included, so any rule would have to be built from outside knowledge.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2018-8581.txt` and rerun.

### CVE-2019-11539: Post-auth (admin) command injection via tcpdump options parameter
- The write-up gives the exact vulnerable endpoint (/dana-admin/diag/diag.cgi), the injected parameter (options), and the distinctive payload artifacts (-r$x="...",system$x#, redirection into /data/runtime/tmp/tt/setcookie.thtml.ttc) plus the follow-up fetch of /dana-na/auth/setcookie.cgi, so a webserver-log rule can match the exploit attempt; note the payload may travel in a POST body that many webserver logs do not record, in which case only the diag.cgi hit followed by an unusual setcookie.cgi request is visible. Also note the host is Ivanti Connect Secure 22.7R2, far outside the listed affected 8.x/9.0 versions.
- **Not found in the advisory text** (verify or remove): `options=`
- **AI review (claude-opus-5-5): edit**, confidence high
  - noise: In selection_diag the cs-uri-query|contains list is OR'd, so 'options=' alone matches, and every legitimate admin tcpdump run on /dana-admin/diag/diag.cgi will fire.
  - grounding: 'options=' does not appear in the source; the source only names the CGI parameter 'options', so the drafter built this string themselves, and it is also the term that causes the noise.
  - logic: The description promises detection of the follow-up fetch of /dana-na/auth/setcookie.cgi, but no selection covers it, so the description overstates what the rule does.
  - specificity: 'system$x' and '-r$x' are the variable names of the single public PoC and are trivial to rename, while the durable artifacts are the template-cache path /data/runtime/tmp/tt/ and the .thtml.ttc extension.
  - telemetry: The payload has to sit in the cs-uri-query field and contain literal '$', '/' and spaces, but the injection may be sent as a POST body, which webserver logs rarely capture, or arrive URL-encoded (%24, %2F, %20), so even true attempts can be missed.
  - specificity: The asset is Ivanti Connect Secure 22.7R2, which is far beyond the fixed releases (9.0R3.4 and later), so a hit would mean an attempt rather than a compromise, and a high level overstates it.
  - Suggested change: Require diag.cgi AND (|contains|any of '/data/runtime/tmp/tt/', '.thtml.ttc', '-r$x', 'system$x', plus their URL-encoded forms), and drop 'options=' as a standalone match. Also lower the level to medium given the patched version, or add a selection for GET /dana-na/auth/setcookie.cgi if correlation is intended.

### CVE-2020-3259: information disclosure (heap memory leak) in ASA/FTD web services interface
- The advisory only says an attacker sends a 'crafted GET request' with 'invalid URLs' to the web services interface; it names no specific URL path, parameter, header, syslog message ID or other value that would appear in a log, so any rule would either be untraceable to the text or match all WebVPN traffic. The only concrete artifact mentioned is Snort rule 53850, which is not a loggable exploit indicator expressible in Sigma.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2020-3259.txt` and rerun.

### CVE-2020-3580: Reflected cross-site scripting in ASA/FTD WebVPN web services interface
- The Nuclei scanner check gives a concrete, traceable request: POST to /+CSCOE+/saml/sp/acs?tgname=a with a SAMLResponse parameter carrying an HTML/script payload; the rule matches that path together with script-injection markers in the request, i.e. probing or exploitation attempts. Cisco ASA syslog (the collected 'cisco' source) does not record URI paths or POST bodies, so the rule is written for web proxy/reverse-proxy or WAF logs fronting the VPN interface.
- **AI review (claude-opus-5-5): reject**, confidence high
  - telemetry: The rule needs webserver logs (cs-method, cs-uri-stem, cs-uri-query), but only Cisco ASA syslog is collected; ASA syslog does not record WebVPN request URLs or query strings, and the automated check confirms the log source is not collected.
  - logic: In the Nuclei request, SAMLResponse travels in the POST body and the query string holds only tgname=a, so the payload selection on cs-uri-query cannot match the documented exploit request.
  - telemetry: POST bodies are almost never logged by web or proxy sources, so even a webserver log source would usually lack the SAMLResponse value the rule depends on.
  - fidelity: The scanner check matches the reflected payload in the response body together with a text/html 200 response, while the rule moves the payload into the request query; this is a different, unsupported condition, not a stricter or looser version of the source.
  - specificity: The values 'svg/onload=alert' and '%3Csvg/onload' are generic XSS markers rather than anything specific to CVE-2020-3580, although the URI-stem selection does narrow the rule to the ACS endpoint.
  - Suggested change: No small change makes this work on the collected ASA syslog; it would need a request-body-capable source such as a WAF or TLS-terminating proxy that logs POST bodies, with the payload matched on that body field. Short of that, IDS alerts (the Snort SIDs 57856/57857 named in the advisory) are the realistic detection path.

### CVE-2021-26085: Pre-authorization arbitrary file read / local file inclusion in the /s/ endpoint
- The Nuclei scanner check sends GET /s/{random}/_/;/WEB-INF/web.xml, so the path pattern '/s/', '/_/;/' and '/WEB-INF/' are traceable log indicators of probing or exploitation; the rule matches that URI pattern in web server access logs.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - noise: The only affected host runs Confluence 8.5.3, which is past every fixed version (7.4.10, 7.12.3, 7.13.0+), so every hit here is a failed scan of a patched server, and level high overstates that.
  - fidelity: The Nuclei check counts a hit only when the response is 200 and the body holds the Confluence web.xml markers; the rule drops the 200 status check, so it fires on blocked or 404 attempts as well as successful reads.
  - specificity: The rule matches only the literal '/_/;/' sequence with GET, so URL-encoded variants (e.g. %3B) or other separators are not covered; it is a narrow signature of the Nuclei template, not of the whole bug.
  - telemetry: Some web servers or proxies strip or normalize ';' path parameters before logging cs-uri-stem; check that wiki-01's access log keeps the raw request path, or the rule may never match.
  - Suggested change: Add sc-status: 200 to the selection so it alerts only on a likely successful WEB-INF read, which on a patched 8.5.3 host would be unexpected. Otherwise lower the level to low or medium and treat matches as scan noise.

### CVE-2021-27065: unspecified remote code execution (ProxyLogon exploit chain)
- The advisory text contains no concrete exploit artifact — no URL path, parameter, process name, file path or log message ID — because both exploit references are behind bot-protection pages and the MSRC page is empty; only the generic label 'ProxyLogon exploit chain' is given. Writing a rule would require pulling ProxyLogon indicators from memory, which a reviewer could not trace to this text.
- **CWE mismatch:** The text calls the flaw an 'unspecified' remote code execution issue and gives no evidence of the drive-relative path traversal pattern that CWE-39 describes.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2021-27065.txt` and rerun.

### CVE-2021-31207: ProxyShell chain - Autodiscover SSRF leading to arbitrary file write / RCE (mailbox export)
- Translated the Splunk analytic's web-datamodel conditions (HTTP 200 POST to /autodiscover/autodiscover.json with ProxyShell backend-access markers X-Rps-CAT=, /powershell/?, /mapi/ in the query string, plus Python/urllib user agents) into a Sigma webserver rule. Sigma cannot express the Splunk `addtotals`/`Score >= 3` scoring across five eval flags, so the rule requires the autodiscover.json POST plus at least one backend indicator; the suspicious user-agent is listed as a separate optional enrichment that the scoring model used.
- **AI review (claude-opus-5-5): edit**, confidence high
  - fidelity: The source alerts only when Score >= 3, meaning autodiscover.json plus at least two of x-rps-cat, /powershell/?, /mapi/ or a python/urllib user agent. The Sigma fires on autodiscover.json plus any single marker, which is effectively Score >= 2 and looser than the source.
  - fidelity: The source's suspicious_agent signal (http_user_agent matching python or urllib) was dropped, so one of the five scoring conditions is missing.
  - noise: Because only one marker is required, a lone /mapi/ or /powershell/? substring in an autodiscover POST query is enough to alert. The source deliberately needs corroboration before it fires.
  - specificity: Like the source, the rule detects the whole ProxyShell/ProxyNotShell SSRF chain rather than CVE-2021-31207's mailbox-export file write specifically. This is acceptable because 31207 is exploited through this chain.
  - Suggested change: Split each marker (X-Rps-CAT=, /powershell/?, /mapi/, and a new cs-user-agent|contains python/urllib selection) into its own selection, then use `selection_request and 2 of selection_marker_*` to reproduce the source's Score >= 3 threshold.

### CVE-2021-34523: Improper authentication / access-token validation bypass in Exchange PowerShell service (ProxyShell chain, SSRF via Autodiscover)
- Translates the Splunk ProxyShell/ProxyNotShell SSRF analytic: successful (HTTP 200) POST requests to /autodiscover/autodiscover.json combined with the exploit-chain query artifacts X-Rps-CAT=, /powershell/?, /mapi/ or Python/urllib user agents. Sigma cannot express the Splunk eval/addtotals scoring (Score >= 3 out of five weighted conditions) or the Web data-model tstats aggregation, so the rule requires the autodiscover.json endpoint plus at least one other chain artifact instead.
- **AI review (claude-opus-5-5): edit**, confidence high
  - fidelity: The source alerts when at least 3 of 5 indicators are present (autodiscover path, X-Rps-CAT, /powershell/?, /mapi/, python/urllib UA). The Sigma instead requires autodiscover AND one query indicator AND a python/urllib user agent, which is much stricter.
  - fidelity: Because the user-agent check is now mandatory, the rule misses exploitation where the attacker sends a normal browser UA. For example, autodiscover + X-Rps-CAT + /powershell/? scores 3 in the source but would not fire here.
  - fidelity: The source does not require the autodiscover path. Any three of the other indicators also qualify, and the Sigma drops that branch entirely.
  - logic: Putting the cs-uri-query and cs-user-agent lists in one selection map ANDs them together. That AND is what silently turns the source's scoring into a mandatory UA match.
  - specificity: The affected host runs Exchange 2019 CU14, which postdates the ProxyShell fixes. This rule therefore mainly catches exploitation attempts rather than a live CVE-2021-34523 exposure.
  - Suggested change: Keep POST/200 as the base and split each indicator into its own selection (autodiscover, rps_cat, backend, mapi, ua). Then rewrite the condition as base AND an OR of the combinations of any three of those five selections, so it reproduces the source's Score >= 3 instead of requiring the Python UA.

### CVE-2021-45046: JNDI lookup injection via Thread Context Lookup Pattern leading to remote code execution (Log4Shell follow-up)
- Translated the second stage of the Elastic EQL sequence: a java parent process spawning a shell/interpreter/download tool, with the same child-process name list and the same command_line exclusions. Sigma cannot express the EQL sequence correlation (the preceding network 'connection_accepted' ingress event with destination.port < 49152 and source.port >= 32768, the maxspan=5s window, or the by-PID join), so the network precondition is dropped and the rule is noisier than the source.
- **Not found in the advisory text** (verify or remove): `/java`, `/sh`, `/dash`, `/ksh`, `/tcsh`, `/zsh`, `/ash`, `/mksh`, `/busybox`, `/curl`, `/wget`, `/socat`, `/nc`, `/ncat`, `/netcat`, `/netcat.openbsd`, `/netcat.traditional`, `/nc.openbsd`, `/nc.traditional`, `/nohup`, `/setsid`, `/disown`, `/hostname`, `/whoami`, `/id`, `/java`, `/perl`, `/ruby`, `/php`, `/lua`
- **AI review (claude-opus-5-5): hunting query**, confidence high
  - fidelity: The Sigma drops the source rule's 5-second sequence gate (java connection_accepted, ingress, destination.port < 49152, source.port >= 32768, joined by pid), so it fires on every java-spawned shell or utility, not only after an inbound connection.
  - noise: Even with the network correlation the source rule is tagged 'Noise: High' and 'Profile: Aggressive'; without it, Tomcat, Jenkins, Elasticsearch and app-server wrappers routinely spawn sh, bash, hostname, id or python, so this would alert constantly.
  - specificity: This is a generic Java-service child-process behavior rule; nothing in it is tied to CVE-2021-45046's Thread Context/MDC JNDI lookup path, and the source rule itself targets deserializing Java listeners rather than this CVE.
  - fidelity: selection_interpreters uses Image|contains '/perl' etc., which matches any path containing those strings (e.g. a perl5 library directory), looser than the source's process.name 'perl*' prefix match.
  - fidelity: The filters 'bash -c ulimit -u' and 'bash -c echo $$' are exact matches in the source but are startswith in the Sigma, which slightly widens the exclusions.
  - telemetry: process_creation:linux is collected, but nothing in it can recover the dropped ingress-connection condition, and the collected webserver logs are not used to stand in for it.
  - Suggested change: Deploy as a hunting query. To alert, scope ParentImage/host to the hr-portal-01 Java service and pair it with a webserver-log selection for '${jndi:' or '${ctx:' in request fields. Also replace Image|contains with endswith or basename matching.

### CVE-2023-20269: improper AAA separation allowing unauthorized remote access VPN / clientless SSL VPN session via default connection profiles (tunnel groups)
- The advisory supplies explicit indicators of compromise: syslog messages %ASA-7-734003 (DAP session attribute aaa.cisco.tunnelgroup) and %ASA-4-113019 (session disconnect) referencing the unexpected connection profiles/tunnel groups DefaultADMINGroup or DefaultL2LGroup. The brute-force half of the IoC set (%ASA-6-113015 at high rate per user/source IP) requires a rate/aggregation threshold that plain Sigma cannot express, so this rule covers only the unauthorized clientless SSL VPN session establishment indicator.
- **CWE mismatch:** The advisory explicitly states "This vulnerability does not allow an attacker to bypass authentication"; the flaw is improper separation of AAA between features (an alternate-channel authorization problem), not an authentication bypass as CWE-288 implies.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - noise: %ASA-4-113019 disconnect messages with Group = DefaultL2LGroup are routine where site-to-site IPsec peers without a dedicated tunnel group fall back to DefaultL2LGroup, so legitimate L2L tunnel rekeys and drops would alert at level high.
  - telemetry: %ASA-7-734003 is a debug-level (7) DAP message that most ASA logging configs do not forward, so in practice only the 113019 branch is likely to fire unless debug-level syslog is collected from edge-fw-01.
  - telemetry: The rule assumes the raw syslog line is in a field named Message; confirm the cisco/asa pipeline maps the full message text there, or use keywords instead.
  - fidelity: The rule faithfully mirrors the vendor IoC (734003/113019 plus DefaultADMINGroup or DefaultL2LGroup), and the affected 9.16.4 device is within the clientless-SSL-capable range, so specificity and grounding are sound.
  - Suggested change: Require 'Session Type: SSL' (or exclude IPsec/IKE session types) for the %ASA-4-113019 branch so routine site-to-site disconnects on DefaultL2LGroup do not alert. Verify that debug-level 734003 messages are actually forwarded.

### CVE-2023-22515: broken access control / privilege escalation (unauthorized Confluence administrator account creation)
- Translated the Splunk 'Confluence CVE-2023-22515 Trigger Vulnerability' web-datamodel search into a Sigma webserver rule: same URL substrings (/server-info.action with bootstrapStatusProvider.applicationConfig.setupComplete=false or =0&), same GET method and HTTP 200 constraint; the Nuclei check sends the identical /server-info.action?bootstrapStatusProvider.applicationConfig.setupComplete=0&cache... request, so this matches the probe/exploit trigger. The tstats aggregation and Web data-model grouping fields (src, dest, url_length, http_user_agent) cannot be expressed in Sigma, and the second source rule (Sysmon EventID 11 file creation under *\Atlassian\Confluence\*) was not translated because only process_creation:linux and webserver logs are collected, not Windows file-creation telemetry.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - fidelity: The detection logic is a faithful translation of the Splunk 'Confluence CVE-2023-22515 Trigger Vulnerability' rule: the same two URL substrings via contains (matching the SPL leading and trailing wildcards), GET, and status 200, with nothing added or dropped.
  - logic: The description wrongly cites windows_unusual_file_creation_in_confluence_directory.yml as the translation source; that is an unrelated Windows file-creation analytic, so the provenance and license note point at the wrong rule.
  - telemetry: The rule relies on cs-uri carrying the full path plus query string; many webserver pipelines split this into cs-uri-stem and cs-uri-query, and if so the '?'-joined pattern never matches and the rule silently cannot fire.
  - specificity: The pattern is tied to the CVE trigger parameter, but it only catches the literal unencoded forms '=false' and '=0&'; URL-encoded, reordered, or other-valued variants (e.g. '=0' as the last parameter) evade it, as they do in the source rule.
  - noise: The affected host runs 8.5.3, which is a fixed version (8.5.2+), so a hit here most likely means an exploitation attempt or scanner probe rather than a successful compromise; triage should treat it that way and pivot to /setup/*.action requests.
  - Suggested change: Correct the description so it cites only confluence_cve_2023_22515_trigger_vulnerability.yml. Confirm that the webserver mapping puts the query string in cs-uri; if it does not, match the parameter in cs-uri-query and server-info.action in cs-uri-stem.

### CVE-2023-22527: OGNL/template injection leading to unauthenticated RCE (SSTI)
- Faithful translation of the Splunk Web-datamodel search: POST requests whose URL contains /template/aui/text-inline.vm returning HTTP 200 or 202, the endpoint the Nuclei scanner check also posts to. The tstats aggregation (count, firstTime/lastTime, BY src/dest/user_agent) and the datamodel field names (Web.url, Web.status) have no Sigma equivalent and are dropped; Sigma matches each event individually.
- **AI review (claude-opus-5-5): keep**, confidence high

### CVE-2023-3519: unauthenticated remote code execution via SAML processing (code injection)
- Faithful translation of the Splunk hunting search: POST requests to the seven Citrix ADC endpoints listed in the source rule, mapped to proxy web logs. Splunk's tstats aggregation (count, firstTime/lastTime grouped by user agent, status, url_length, src, dest) and the datamodel-specific fields such as Web.url_length cannot be expressed in Sigma; the Nuclei check confirms POST /saml/login with a SAMLRequest body is the probe, but Sigma rules on the URI only.
- **AI review (claude-opus-5-5): hunting query**, confidence high
  - noise: POST to /saml/login, /saml/activelogin, /cgi/samlauth and /cgi/logout is ordinary SAML sign-in and logout traffic on any Citrix Gateway that uses SAML, so this will fire on every normal user session.
  - specificity: The rule matches Gateway endpoints rather than the SAML overflow itself; the distinguishing part (the oversized or malformed SAMLRequest body) is not in the URI and is not visible to this rule.
  - fidelity: The source analytic is explicitly 'type: Hunting', not an alert, so promoting it to an alerting rule overstates what the source intended.
  - fidelity: The SPL patterns '*/cgi/logout', '*/cgi/samlauth', '*/saml/activelogin' and '*/saml/login' are suffix matches, but the Sigma uses contains, which also matches query strings and longer paths, so it is looser than the source.
  - telemetry: The proxy category normally means forward or outbound proxy logs, and inbound requests to citrix-gw-01 will only show up if a reverse proxy or WAF in front of the gateway logs to this source; request bodies, where the payload lives, are not logged either way.
  - Suggested change: Keep it as a hunting query scoped to the citrix-gw-01 destination. Use endswith for the four suffix patterns to match the SPL, and baseline the request volume or URL length rather than alerting on every hit.

### CVE-2023-46805: authentication bypass in web component (path-traversal style control-check bypass), chained with command injection
- Both Splunk analytics key off specific Web-datamodel URL/method/status triplets, which map directly onto webserver access log fields; the Nuclei check adds two more concrete bypass URIs (/api/v1/totp/user-backup-code/../../system/system-information and /api/v1/cav/client/status/../../admin/options). Not expressible in Sigma: the tstats aggregation (count, firstTime/lastTime, group-by src/dest/user_agent) and the Splunk datamodel field names/filter macros; also note some web servers normalize '../' out of the logged URI, so matching may need the raw request line.
- **AI review (claude-opus-5-5): keep**, confidence medium
  - telemetry: Three selections (cmdinject and both authbypass_probe URIs) depend on a literal '../../' surviving in cs-uri-stem; the Splunk sources were tested on Suricata raw URLs, while many web servers and appliance access logs normalize or URL-decode the path before logging, so those selections may never match on ivanti-vpn-01's webserver logs.
  - telemetry: The Nuclei check also requires specific response-body strings and an application/json header, and the bookmark source rule specifies an empty 403 body; none of these can be checked in webserver logs, so only the URI, method and status parts were carried over.
  - fidelity: The rule merges both Splunk analytics and adds a third selection taken from the Nuclei probe URIs (GET, 200); that selection is looser than the scanner check because its body and header matchers were dropped, though the URIs themselves are grounded in the source.
  - noise: The bookmark GET-403 branch mainly catches blocked probes and mass mitigation-check scanners against a mitigated appliance, so on an internet-facing gateway it will fire on attempts that did not succeed, at level high.

### CVE-2024-21887: command injection in web components (via path traversal to unauthenticated endpoints)
- Both Splunk analytics key on specific Ivanti URIs — the bookmark endpoint probe (GET, 403) and the traversal endpoints /api/v1/totp/user-backup-code/../../system/maintenance/archiving/cloud-server-test-connection and /api/v1/totp/user-backup-code/../../license/keys-status/ (GET/POST, 200); the Nuclei check sends the same keys-status traversal path with an injected ';curl' command. Sigma cannot express the tstats aggregation/BY grouping or the Web datamodel field names, so standard webserver fields are used and status codes are kept per the source rules.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - noise: The bookmark-endpoint branch (GET, 403) matches the public mitigation-check probe that internet-wide scanners send to any exposed Ivanti gateway; at level high it will page on routine scanning of ivanti-vpn-01, not on exploitation.
  - fidelity: The rule merges two separate Splunk analytics into one high-severity alert, so a mitigated-gateway probe (403) and a successful traversal or command-injection request (200) get the same severity; the per-branch conditions match the sources (GET+403, GET/POST+200, same URI substrings).
  - telemetry: The exploit branch needs the literal '/api/v1/totp/user-backup-code/../../' string in cs-uri-stem, but many web servers and proxies normalize dot-segments before logging, so confirm the collected webserver logs keep the raw request path or this branch may never match.
  - logic: The source uses Web.url, which includes the query string, while the Sigma uses cs-uri-stem; this is harmless because all matched substrings are in the path, but the cs-uri-stem field must actually be populated by the webserver mapping.
  - Suggested change: Split into two rules: keep the traversal/command-injection selection at level high, and move the 403 bookmark probe to its own rule at low/informational for hunting or correlation. Verify that the webserver logs preserve un-normalized '../' in the URI.

### CVE-2024-21893: Server-side request forgery (SSRF) in SAML component
- Direct translation of the Splunk Web-datamodel search: POST requests to the SAML endpoints /dana-ws/saml20.ws, /dana-ws/saml.ws, /dana-ws/samlecp.ws and /dana-na/auth/saml-logout.cgi that return HTTP 200; the Nuclei check confirms POST /dana-ws/saml20.ws is the probe path. The tstats aggregation/grouping by src, dest, user_agent and the custom filter macro cannot be expressed in Sigma, and the Web data-model field names were mapped to webserver fields (cs-uri-stem, cs-method, sc-status).
- **AI review (claude-opus-5-5): hunting query**, confidence medium
  - noise: A POST to the SAML SOAP/ECP endpoints or saml-logout.cgi that returns 200 is exactly what normal SAML SSO/SLO produces, so any appliance with SAML authentication enabled will fire on ordinary logins and logouts (the drafter's own falsepositives entry admits this).
  - specificity: Nothing in the rule separates the SSRF payload from legitimate SAML messages, because the distinguishing content (the XML signature KeyInfo RetrievalMethod pointing to an attacker or internal URI) is in the request body, which webserver logs do not carry.
  - fidelity: The rule is a faithful translation of the Splunk search (same four paths with contains, POST, status 200); the only change is that cs-uri-stem replaces Web.url, which drops query-string matching but does not affect these path-based patterns.
  - telemetry: Ivanti Connect Secure does not natively emit standard webserver access logs, so this only works if the 'webserver' source is a reverse proxy or WAF in front of ivanti-vpn-01 that logs method, URI and status.
  - Suggested change: Keep it as a hunting query. To make it alert-worthy, exclude the configured IdP and SP source IPs (or alert only on sources outside them), and consider limiting it to the /dana-ws/*.ws SOAP endpoints, dropping the commonly used saml-logout.cgi.

### CVE-2025-0282: refused
- The model declined (stop reason: refusal), most likely because the input contained exploit details. Try another model, or remove exploit write-ups from the input.

### CVE-2025-22457: refused
- The model declined (stop reason: refusal), most likely because the input contained exploit details. Try another model, or remove exploit write-ups from the input.

### CVE-2025-5777: memory overread / memory disclosure (CitrixBleed 2) via insufficient input validation
- Translates the Splunk 'Citrix ADC and Gateway CitrixBleed 2 Memory Disclosure' search (Web datamodel: POST to */p/u/doAuthentication.do* returning 200) into a Sigma proxy rule, which is the endpoint the Nuclei scanner check also probes; the tstats stats-by aggregation (grouping by user agent, url_length, src/dest) and the Cisco Secure Firewall rule's Snort signature_id=65118 IntrusionEvent logic cannot be expressed in a proxy-category Sigma rule.
- **AI review (claude-opus-5-5): hunting query**, confidence high
  - noise: A POST to /p/u/doAuthentication.do returning 200 is the normal NetScaler Gateway login flow, so on citrix-gw-01 this fires on every legitimate user authentication; the rule's own falsepositives section says so.
  - specificity: Nothing in the selection separates an exploit request (a login form key with no value, per Horizon3) from a real login, so the rule detects endpoint usage rather than CVE-2025-5777.
  - fidelity: The rule matches the Splunk Web-datamodel source rule (POST, URL contains /p/u/doAuthentication.do, status 200), but that source is typed Anomaly with a risk score of 20, while the Sigma rule is set to level high as an alerting TTP.
  - telemetry: The real distinguishing traits (a short or empty request body, or leaked bytes in the response) live in request and response bodies, which proxy logs normally do not record, so the rule cannot be tightened on these logs.
  - Suggested change: Lower the level to low or informational and use it as a hunting query, for example aggregating by source IP to surface high-volume repeated POSTs from one client. For alerting, use the Snort SID 65118 intrusion-event rule instead, which needs IDS telemetry that is not collected here.

### CVE-2014-2120: Cross-site scripting (XSS) in the WebVPN login page
- The advisory only states that injection occurs via an 'unspecified parameter' on the WebVPN login page; it names no URL path, parameter name, payload string or log message ID that an exploit attempt would leave behind, and adding the known ASA WebVPN logon path from memory would not be traceable to this text.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2014-2120.txt` and rerun.

### CVE-2016-6366: SNMP buffer overflow leading to remote code execution / device reload (EXTRABACON)
- The only indicator the advisory shows landing in a device log is the ASA crash traceback produced by the EXTRABACON overflow ('Thread Name: snmp' followed by 'Page fault: Unknown'); the rule matches that on the collected cisco log source. The network-level indicator (the crafted SNMP GET-BULK with OID 1.3.6.1.4.1.9.9.491.1.3.3.1.1.5... and shellcode in the .1.3.6.1.2.1.1.1 varbind, UDP/161) cannot be expressed against cisco syslog and would need IDS/packet data (Snort SID 3:39885 is cited in the text).
- **AI review (claude-opus-5-5): reject**, confidence medium
  - telemetry: The 'Thread Name: snmp' / 'Page fault' traceback in the source is console and crashinfo output from a device that is crashing and reloading. ASA does not normally forward this crash dump through syslog, so the collected cisco syslog is unlikely to contain it.
  - logic: Even if traceback lines were forwarded, 'Thread Name: snmp' and 'Page fault: Unknown' are separate lines that syslog would split into separate events, so a single-message contains|all on both strings would likely never match.
  - specificity: The rule catches any SNMP-thread page fault rather than exploitation itself. It would also miss a successful EXTRABACON run, which executes code without crashing; the crash in the source came from a mismatched or failed attempt.
  - specificity: NVD lists affected ASA software as through 9.4.2.3 and Cisco has published fixes, so edge-fw-01 on 9.16.4 does not appear to be an affected version, which makes a CVE-specific high-severity alert unwarranted here.
  - Suggested change: Drop this rule. If coverage is still wanted, use an SNMP-to-ASA network or IDS rule for the long overflow under the 1.3.6.1.4.1.9.9.491 OID, or a hunt for unexpected ASA reloads correlated with SNMP from non-NMS hosts. Separately, verify the version exposure.

### CVE-2016-6367: CLI parser flaw allowing privilege escalation / code execution via invalid CLI commands (EPICBANANA)
- The advisory only says the exploit works by 'invoking certain invalid commands' over telnet/SSH after authenticating; it names no specific command string, syslog message ID, file path or packet content for CVE-2016-6367. The concrete artifacts in the page (SNMP OIDs, shellcode bytes, community string 'cisco', crash traceback) all belong to EXTRABACON / CVE-2016-6366, so they cannot be used for this CVE.
- **CWE mismatch:** The text describes a CLI parser mishandling invalid commands by an already-authenticated user (memory corruption / privilege escalation), not injection of attacker-controlled commands into a downstream component as CWE-77 implies.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2016-6367.txt` and rerun.

### CVE-2017-6316: pre-auth command injection via session cookie (CGISESSID/CAKEPHP)
- The exploit sends a POST to /global_data/ with a CGISESSID (or CAKEPHP on CloudBridge) cookie containing backtick-delimited shell commands; the rule matches proxy records where the session cookie carries shell metacharacters or the module's /tmp/n, /tmp/m and 'chmod 755' payload strings. Cookie content must be logged by the proxy for this to fire; if only URIs are logged, only the /global_data/ POST portion is observable.
- **CWE mismatch:** The text describes OS command injection (unsanitized cookie passed to system()), which is CWE-78 rather than the generic CWE-20 input validation.
- **Not found in the advisory text** (verify or remove): `CAKEPHP=`, ```
- **AI review (claude-opus-5-5): reject**, confidence medium
  - telemetry: The rule depends entirely on cs-cookie, but proxy logs rarely record Cookie headers, and a forward proxy would not normally see inbound traffic to an appliance management interface, so the rule is unlikely ever to match on the collected logs.
  - specificity: CVE-2017-6316 affects the NetScaler SD-WAN/CloudBridge management interface up to 9.1.2.26.561201, but the affected asset is NetScaler 14.1-12 on citrix-gw-01, an ADC/Gateway build that is not in scope, so a match here would only be untargeted scanning.
  - noise: Neither cookie name is distinctive on its own: CGISESSID is the default Perl CGI::Session cookie and CAKEPHP is the default CakePHP cookie, so only the injection selection keeps the rule quiet.
  - specificity: The literals '/tmp/n', '/tmp/m', 'chmod 755' and 'echo -e' come from the Metasploit module's dropper, and a URL-encoded backtick (%60) would be missed, so any non-Metasploit payload is caught only by the raw backtick.
  - grounding: The automated flag on 'CAKEPHP=' and the backtick is a false positive, because the NVD text names the CAKEPHP cookie for CloudBridge and the exploit shows backtick-wrapped commands in CGISESSID.
  - Suggested change: Do not deploy against citrix-gw-01 or these proxy logs. If an SD-WAN/CloudBridge appliance at 9.1.2.26 or earlier is found, rebuild the rule on that appliance's web/WAF logs with cookie logging, and add a %60 variant to the backtick match.

### CVE-2018-0296: directory traversal / unauthenticated information disclosure via crafted HTTP URL
- The scanner check and the public exploit both send a fixed traversal URI (/+CSCOU+/../+CSCOE+/files/file_list.json?path=...), which is a traceable indicator of probing or exploitation; the rule matches that URI and its known path= values. The DoS side of the bug leaves no distinct log string, but the information-disclosure requests do.
- **AI review (claude-opus-5-5): reject**, confidence high
  - telemetry: The rule uses logsource category webserver / product cisco, but the automated check reports this log source is not collected, so the rule cannot fire on the available data.
  - telemetry: The only collected source is 'cisco' (ASA firewall/VPN syslog), and that syslog does not record the WebVPN request URI, so no field carries the path being matched.
  - logic: The strings start with path segments ('/+CSCOU+/../+CSCOE+/files/file_list.json'), but cs-uri-query normally holds only the query string (e.g. 'path=/sessions'), so a contains match on cs-uri-query cannot be true.
  - logic: The fourth value '+CSCOU+/../+CSCOE+/files/file_list.json' already covers the other three, so those entries are redundant.
  - fidelity: The Nuclei source rule also requires HTTP status 200 and the body word '///sessions' to confirm success; the Sigma rule drops these, which is acceptable for probe detection but means it flags attempts, not successful disclosure.
  - specificity: The affected asset runs ASA 9.16.4, a release well after the 2018 fixes, so hits would be scans against a patched device, which lowers the value of a high-level alert.
  - Suggested change: Point the rule at a source that logs the full request URI, such as a reverse proxy or WAF in front of the WebVPN, and match the traversal string on cs-uri-stem or the full URL rather than cs-uri-query. If no such source exists, drop the rule.

### CVE-2019-12989: Unauthenticated SQL injection in /sdwan/nitro/v1/config/get_package_file
- The scanner check and Tenable PoC both send a POST to /sdwan/nitro/v1/config/get_package_file?action=file_download with the non-standard header SSL_CLIENT_VERIFY: SUCCESS and a SQL injection payload in the JSON 'site_name' field; the rule matches that path/parameter combination plus SQLi keywords in the request body, which is what probing or exploitation leaves in proxy logs.
- **AI review (claude-opus-5-5): reject**, confidence high
  - logic: The condition is only 'selection', so the selection_payload block (action=file_download, SSL_CLIENT_VERIFY, union select) is defined but never used.
  - logic: The endpoint path /sdwan/nitro/v1/config/get_package_file is matched against cs-uri-query, but a path belongs in cs-uri-stem; the query string is only 'action=file_download', so the rule as written can never match.
  - telemetry: The SSL_CLIENT_VERIFY indicator is a custom request header, not a Referer, and the 'union select' payload sits in the JSON POST body, not the User-Agent; proxy logs carry neither the custom header nor the body.
  - fidelity: The source trigger requires POST, the get_package_file path, ?action=file_download, the SSL_CLIENT_VERIFY: SUCCESS header and SQLi in site_name together, but the draft ORs unrelated fields and in practice keys only on method plus path.
  - specificity: The affected asset is Citrix NetScaler 14.1-12 (ADC/Gateway), while CVE-2019-12989 affects the SD-WAN appliance (10.2.x before 10.2.3 and 10.0.x before 10.0.8), so this endpoint does not exist on citrix-gw-01 and the rule cannot detect real exploitation of this host.
  - noise: Even if corrected to POST plus path, the rule would fire on legitimate SD-WAN orchestration calls to get_package_file, as the rule's own falsepositives entry admits.
  - Suggested change: First confirm whether an SD-WAN appliance exists in this estate. If one does, match cs-uri-stem|contains the get_package_file path AND cs-uri-query|contains 'action=file_download' AND cs-method POST. Drop the referer and user-agent clauses, since the header and body are not logged.

### CVE-2019-12991: Authenticated OS command injection via 'installfile' parameter in installpatch.cgi
- The Tenable advisory gives the exact exploit URL for CVE-2019-12991: /cgi-bin/installpatch.cgi with a swc-token and an 'installfile' parameter whose value is injected into a Perl system() call, demonstrated with backtick-wrapped shell commands; the rule matches requests to that CGI carrying the installfile parameter and, with higher confidence, shell metacharacters. The related auth-bypass path /sdwan/nitro/v1/config/get_package_file?action=file_download is included as a chained-exploit indicator since the command injection PoC requires it first.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - noise: selection_cmdinject matches any request to /cgi-bin/installpatch.cgi carrying installfile=, which is the normal patch-install workflow, and it is OR'd into the condition, so every legitimate admin patch upload alerts.
  - logic: Because the condition is a plain OR, the specific backtick check in selection_metachar adds nothing over the broad selection_cmdinject for that path; and selection_metachar on its own does not require the installpatch.cgi path.
  - specificity: selection_authbypass detects /sdwan/nitro/v1/config/get_package_file?action=file_download, which is CVE-2019-12989 (the SQL injection), not CVE-2019-12991.
  - noise: The get_package_file?action=file_download URL is the endpoint's normal use; the malicious part (the site_name SQL payload, the SSL_CLIENT_VERIFY header) is in the POST body and headers.
  - telemetry: Proxy logs typically record neither the POST body nor custom headers, so the auth-bypass branch cannot tell an attack from normal use.
  - telemetry: The listed asset is a NetScaler 14.1-12 gateway, not an SD-WAN 10.x appliance, so the CVE likely does not apply to it.
  - telemetry: It is not clear that proxy logs see management-plane requests to the appliance at all.
  - Suggested change: Change the condition to require both the /cgi-bin/installpatch.cgi path and installfile= followed by a backtick (` or %60), drop the get_package_file branch or move it to a separate CVE-2019-12989 hunting rule, and confirm an SD-WAN 10.x appliance actually exists and its traffic is in the proxy logs.

### CVE-2020-8243: authenticated arbitrary code execution via custom template upload in admin web interface
- The advisory describes the flaw only as an "unspecified vulnerability" allowing an authenticated admin to upload a custom template, and the vendor advisory page did not load any content; no URL path, parameter, template name, file path, process or log message is given that an exploit attempt would leave in the webserver log.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2020-8243.txt` and rerun.

### CVE-2020-8260: authenticated arbitrary code execution via uncontrolled gzip extraction in the admin web interface
- The advisory is explicitly "unspecified" and the exploit and vendor pages returned only bot-protection/loading placeholders, so no URL path, parameter, filename, process, or log message is available to anchor a rule; writing one would require inventing indicators.
- **CWE mismatch:** CWE-434 (unrestricted upload of dangerous file type) is a plausible fit for an admin config/archive upload, but the text describes uncontrolled archive extraction (path traversal during unpacking, closer to CWE-22/CWE-409) and names no upload endpoint.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2020-8260.txt` and rerun.

### CVE-2021-22894: buffer overflow in meeting room handling leading to remote code execution as root
- The advisory only states that an authenticated attacker can trigger the overflow via a "maliciously crafted meeting room"; no URL path, parameter name, log message, process or file artifact is given, and the vendor advisory page returned no content. There is no traceable indicator to match in webserver logs.
- **CWE mismatch:** The text describes a buffer overflow (CWE-787/CWE-120), not code injection (CWE-94).
- Add the vendor advisory or an intel write-up to `advisories/CVE-2021-22894.txt` and rerun.

### CVE-2021-22899: command injection via Windows File Resource Profiles
- The advisory only names the affected feature ("Windows File Resource Profiles") in prose and gives no URL path, parameter, log message ID, process name, or payload string; the vendor advisory page failed to load, so no traceable indicator exists to build a rule on.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2021-22899.txt` and rerun.

### CVE-2021-22900: unrestricted file upload (malicious archive) in admin web interface
- The advisory names no concrete indicator — no admin upload URL path, parameter name, archive filename, or log message ID — and the vendor advisory page content failed to load, so any rule would have to invent values not traceable to the text.
- **CWE mismatch:** The text describes an unrestricted file upload leading to arbitrary file write (CWE-434), not code injection (CWE-94).
- Add the vendor advisory or an intel write-up to `advisories/CVE-2021-22900.txt` and rerun.

### CVE-2021-31196: Microsoft Exchange Server information disclosure leading to remote code execution
- The advisory text contains only a generic description ("information disclosure vulnerability that allows for remote code execution") with no URL paths, parameters, log message IDs, process names, or file artifacts; the referenced MSRC pages carry no technical detail. Any rule would have to invent indicators (e.g. ProxyShell-style Autodiscover paths or w3wp child processes) not traceable to this text.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2021-31196.txt` and rerun.

### CVE-2022-26138: Hard-coded credentials (disabledsystemuser account created by Questions for Confluence)
- The scanner check and advisory give concrete loggable values: a POST to /dologin.action with os_username=disabledsystemuser (Nuclei also sets os_destination=%2Fhttpvoid.action), and the account name disabledsystemuser itself. The rule detects that probe/login attempt in web server logs; note the credentials are sent in the POST body, so this only fires where the proxy/web server logs request bodies or query strings - otherwise the equivalent check must be done on Confluence's own authentication log for logins by disabledsystemuser.
- **AI review (claude-opus-5-5): reject**, confidence high
  - telemetry: The only request in the source (the Nuclei check) is a POST to /dologin.action with os_username, os_password and os_destination in the form body, and webserver access logs do not record POST bodies, so cs-uri-query will not contain these values for the documented technique.
  - fidelity: The rule moves the source's POST-body parameters into the URI query string, so it only matches a GET-style login with credentials in the URL, which the source never describes.
  - telemetry: The Nuclei success signal is a response Location header of /httpvoid.action, and standard webserver access logs do not capture response headers either.
  - logic: The value list is redundant: 'disabledsystemuser' already covers 'os_username=disabledsystemuser'.
  - logic: The value os_destination=%2Fhttpvoid.action is a scanner-only marker that real attackers would not send.
  - telemetry: The rule's own falsepositives section admits it will miss real exploitation when POST bodies are not logged, which is the normal case for webserver logs.
  - specificity: Exploitation depends on the Questions for Confluence app (2.7.34, 2.7.35, 3.0.2) or a leftover disabledsystemuser account, not on Confluence 8.5.3 itself, so the asset match on wiki-01 is not established by the source.
  - Suggested change: Do not alert on these logs. Detect successful or attempted authentication as disabledsystemuser in Confluence application, authentication or audit logs (or outbound SMTP to dontdeletethisuser@email.com); none of those sources is currently collected.

### CVE-2023-6548: authenticated remote code execution via code injection on management interface
- The advisory only states that a low-privileged authenticated user with access to NSIP/CLIP/SNIP management interface can achieve RCE; it names no URL path, parameter, process, file or log message that an exploit attempt would leave behind (the vendor bulletin content did not load).
- Add the vendor advisory or an intel write-up to `advisories/CVE-2023-6548.txt` and rerun.

### CVE-2023-6549: buffer overflow / out-of-bounds memory read in NetScaler Gateway (Citrix Bleed-like memory disclosure)
- The Nuclei scanner check sends an unauthenticated GET to /nf/auth/startwebview.do with a grossly oversized Host header of repeated 'A' characters; both the path and the overlong Host value are traceable indicators of probing/exploitation in proxy or web access logs. The rule matches that specific request; no aggregation or data-model fields were needed.
- **AI review (claude-opus-5-5): keep**, confidence medium
  - specificity: The rule matches only the Nuclei template's filler of 'A' characters, so a real exploit that pads the Host header with any other character would be missed; it detects this scanner, not the bug class.
  - fidelity: The Sigma rule is looser than the template on length: it requires a 64-character run of 'A' where the template sends thousands, which is acceptable and still tolerates Host truncation in logs.
  - telemetry: The proxy category only sees this inbound request if a reverse proxy or WAF sits in front of citrix-gw-01 and logs cs-host; some proxies reject or truncate oversized Host headers before logging them.

### CVE-2024-20353: Infinite loop / incomplete error checking when parsing an HTTP header, leading to device reload (DoS)
- The advisory describes only a 'crafted HTTP request' with no named header, path, parameter, or log message ID, and the sole impact is an unexpected reload (denial of service), so there is no traceable signature to match; the only stated detection guidance ('monitor system logs for indicators of undocumented configuration changes, unscheduled reboots') is a baseline observation, not an exploit indicator. The concrete artifacts in the Talos blog (host-scan-reply POSTs, client_bundle*.zip on disk0:, csco_config.lua) belong to the Line Dancer/Line Runner implants and CVE-2024-20359, not to this CVE's exploitation itself.

### CVE-2024-20359: persistent local code execution via unvalidated preload ZIP file read from disk0: flash
- The advisory and Talos report name concrete artifacts an exploit leaves behind: a ZIP on disk0: matching ^client_bundle[%w_-]*%.zip$ (e.g. client_bundle_install.zip) copied with the copy command, plus the Line Runner paths csco_config.lua, disk0:/csco_config/97/webcontent/1515480F4B538B669648B17C02337098, /asa/scripts/lina_cs and /run/lock/subsys/krbkdc6; the rule matches these strings in ASA command-accounting/syslog messages. Field naming depends on how ASA syslog is parsed (message text field), and the 'new .zip after upgrade' check from the advisory is a manual CLI comparison that cannot be expressed in Sigma.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - telemetry: Most values (/asa/scripts/lina_cs, /run/lock/subsys/krbkdc6, csco_config.lua, the webcontent path and the 1515480F… endpoint) are files touched internally by the Lua boot script, so they will never show up in ASA syslog or AAA command accounting; only an admin-issued copy of client_bundle*.zip to disk0: is plausibly logged.
  - telemetry: The 'msg' field is not a standard field for the Sigma cisco/aaa log source, which existing rules match with keywords; the field name may not map in the backend, so the rule could silently never match.
  - logic: 'client_bundle' already matches 'client_bundle_install.zip', so the second value is redundant, and a bare 'client_bundle' substring would also match unrelated messages that merely mention the filename.
  - noise: The incident-response step of copying the suspicious zip off the device, which Cisco recommends, will also fire the rule, as will any legitimate use of the legacy preload feature; both are acknowledged but not filtered.
  - specificity: Placing client_bundle*.zip on disk0: is the documented trigger for CVE-2024-20359, so the core idea is specific, but the source notes the actor disables logging, so absence of alerts is not assurance.
  - Suggested change: Reduce the selection to a command-accounting copy whose destination is disk0: and contains 'client_bundle' and '.zip', using keywords or the backend's correct field. Drop the on-box internal paths, the hash and csco_config.lua, which cannot appear in these logs.

### CVE-2024-20481: resource exhaustion / DoS of RAVPN service via mass VPN authentication requests (password spray)
- The impact is denial of service only, but the vendor advisory lists concrete syslog indicators of the attack traffic (%ASA-6-113005, %ASA-6-113015, %ASA-6-716039 authentication-rejected messages), so a signature matching those rejection messages is traceable to the text; the defining characteristic is high volume, which Sigma cannot express natively — a count of these messages per source IP / per minute (or a comparison of 'show aaa-server' reject counters) is needed to separate an attack from normal failed logins.
- **AI review (claude-opus-5-5): edit**, confidence high
  - noise: The rule fires on every single 113005/113015/716039 message, so every mistyped VPN password raises a high-severity alert, while the advisory says these messages only indicate an attack when they occur frequently and in large quantities.
  - fidelity: The source's volume condition ('frequently and in large quantities') was dropped, which turns a rate-based indicator into a per-event match.
  - specificity: Without a volume threshold this is a generic failed-VPN-login rule; the link to CVE-2024-20481 resource exhaustion only holds at spray-scale volume.
  - telemetry: The logsource 'cisco/aaa' and the field 'msg' may not match how the ASA syslog from edge-fw-01 is mapped, so the service and field names should be checked against the collected cisco data.
  - Suggested change: Wrap the selection in a Sigma event_count correlation, for example more than several hundred matches per device (or per source IP) within 5–10 minutes. Lower the per-event base rule to informational. Confirm the logsource service and message field match the ASA syslog mapping.

### CVE-2024-21410: unspecified privilege escalation (elevation of privilege) in Exchange Server
- The advisory text contains no concrete exploitation artifact — no URL path, parameter, process name, file path, log ID, or string — only a generic 'unspecified vulnerability that allows for privilege escalation', so no traceable detection logic can be written. Any rule would have to import indicators (e.g. NTLM relay patterns) from outside the provided text.
- **CWE mismatch:** The text only describes an unspecified elevation of privilege; nothing in it supports an improper-authentication (CWE-287) classification.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2024-21410.txt` and rerun.

### CVE-2025-6543: memory/buffer overflow leading to unintended control flow and Denial of Service
- The advisory text only states that NetScaler ADC/Gateway configured as a Gateway (VPN vserver, ICA Proxy, CVPN, RDP Proxy) or AAA virtual server has a memory overflow; it names no URL path, parameter, request header, process, file, or log message that an exploit attempt would leave behind, and the vendor KB content was not retrievable. Any rule would have to invent indicators or match all Gateway traffic.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2025-6543.txt` and rerun.

### CVE-2025-7775: memory overflow leading to RCE/DoS in NetScaler ADC/Gateway
- The advisory only describes affected configurations (VPN/ICA Proxy/CVPN/RDP Proxy, AAA vserver, LB vservers with IPv6 services, CR vserver type HDX) and gives no URL path, parameter, header, payload string, process name or log message that an exploit attempt would leave behind; the vendor page content was not retrievable. Any rule would have to invent indicators.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2025-7775.txt` and rerun.

### CVE-2026-19490: authentication bypass using an alternate path or channel (AAA vserver / Gateway)
- The text names no URL path, parameter, log message or string an exploit would leave behind — only that an unauthenticated actor can bypass authentication on an AAA vserver or Gateway (SSL VPN, ICA Proxy, CVPN, RDP Proxy); successful exploitation looks like a legitimate authenticated session. Detection requires baselining: VPN/ICA sessions established without a preceding successful AAA authentication event, session creation from source IPs or geolocations with no prior login history, or a spike in gateway session objects relative to authentication log entries for the same user.

### CVE-2026-20349: Remote Access SSL VPN denial of service via crafted HTTP request (insufficient error checking)
- The impact is solely an unexpected device reload / denial of service, and the advisory names no concrete exploit artifact (no URL path, parameter, header, or syslog message ID) that a crafted request would leave in a log; only Snort SIDs 46897 and 59654 are referenced, which are not expressible as Sigma indicators. Detection would at best be noticing unexplained ASA/FTD reloads, which is an availability symptom rather than an exploit signature.
- **CWE mismatch:** CWE-244 (Improper Clearing of Heap Memory Before Release / 'heap inspection') describes an information-exposure weakness, while the advisory describes insufficient error checking on HTTP requests leading to an unexpected device reload (DoS).

### CVE-2026-3055: out-of-bounds read / memory overread via SAML IDP endpoints (CitrixBleed-style)
- The advisory and scanner check give an exact request shape: GET /wsfed/passive?wctx where the wctx query parameter is present but empty and lacks the '=' symbol, which triggers the overread and leaks memory in the NSC_TASS cookie; this rule matches that probe/exploit request in proxy logs. The /saml/login POST with a SAMLRequest body is the second variant, but is indistinguishable from legitimate IDP traffic at the URL level, so it is not included; the response-side indicator (large base64 NSC_TASS Set-Cookie with 302) cannot be expressed in typical proxy URL fields.
- **AI review (claude-opus-5-5): edit**, confidence medium
  - logic: Exact-equality on cs-uri-query ('wctx' or '?wctx') only catches the bare published request; an attacker can add other parameters (e.g. 'wa=wsignin1.0&wctx' or 'wctx&x=1') and still send a valueless wctx, so the rule is easy to evade.
  - specificity: The rule covers only the /wsfed/passive variant; the source says CVE-2026-3055 also includes a /saml/login memory overread, and that variant is not detected (its trigger is in the POST body, which proxy logs rarely carry).
  - telemetry: Proxy logs only see this traffic if inbound requests to citrix-gw-01 pass through a TLS-terminating reverse proxy or WAF; a forward proxy will not see internet-to-gateway requests, so confirm the path before relying on the rule.
  - fidelity: The Nuclei check confirms a vulnerable host from the response (302 plus an NSC_TASS cookie decoding to 'wctx='); the Sigma rule matches only the request, so it flags attempts against patched devices as well, which is acceptable for an exploitation-attempt alert.
  - Suggested change: Replace the exact-match query list with a regex that matches wctx as a parameter with no '=', anywhere in the query, e.g. cs-uri-query|re: '(^|[?&])wctx(&|$)'. Keep the /wsfed/passive stem and the GET method.

### CVE-2026-8452: memory overflow (buffer) leading to denial of service
- The advisory describes only a memory overflow causing unpredictable behavior and denial of service on Gateway/AAA virtual servers, with no URL path, parameter, log message or string that an exploit attempt would leave behind; the vendor article content was not retrievable.

### CVE-2026-88771: improper input validation leading to unauthenticated command injection via NetScaler log poisoning
- Translated the Elastic rule's stated logic: Pitboss/packet-engine/core terminology in the Citrix record combined with shell syntax (separators, command substitution, pipe, redirection) in either citrix.detail or citrix_adc.log.message. The published source file omits the raw EQL query, so the exact token ordering/wildcards and the Elastic-specific field names and index scope (logs-citrix_adc.log-*) cannot be reproduced verbatim; no aggregation was used in the original.
- **CWE mismatch:** CWE-119 (memory buffer errors) does not match the described weakness, which is improper input validation / command injection (closer to CWE-20 / CWE-78).
- **Not found in the advisory text** (verify or remove): `;`, `&&`, `||`, ```, `$(`, `|`, `>`, `;`, `&&`, `||`, ```, `$(`, `|`, `>`
- **AI review (claude-opus-5-5): reject**, confidence high
  - telemetry: The rule needs Citrix ADC appliance syslog (`citrix.detail` / `citrix_adc.log.message`), but the only collected source is proxy and the automated check confirms the log source is not collected, so it cannot fire on these logs.
  - noise: Sigma `contains` is case-insensitive, so the context term `PPE` matches ordinary words such as dropped, stopped, mapped and happened, and the shell tokens `;`, `|` and `>` are common in Citrix log text, so the pairing would fire on routine records.
  - fidelity: The source EQL query is truncated, so the boolean structure cannot be checked; the source describes Pitboss records with shell syntax, or Citrix records combining Pitboss/packet-engine/core terms with shell syntax, and the Sigma does not anchor on a Pitboss record class or pitboss-plus-failure-phrase structure.
  - specificity: Per the source, this is a generic NetScaler log-poisoning behavior rule rather than a CVE-2026-88771-specific signature, which is acceptable only if the context anchoring is tight.
  - grounding: The flagged shell tokens are described in the source note (separators `;` `&&` `||`, backticks, `$()`, pipe, redirection), so this check is mostly a false alarm, though the exact `|` and `>` literals are paraphrases of 'pipe' and 'redirection'.
  - Suggested change: Collect NetScaler native syslog through the citrix_adc integration before deploying. Then require `pitboss` together with `PPE`/`NSPPE` or a failure phrase as the context, instead of matching the bare substring `PPE`.

### CVE-2026-88772: improper restriction of operations within the bounds of a memory buffer (memory corruption leading to RCE or DoS)
- The advisory text only states the vulnerability class and affected version numbers; it names no URL path, parameter, request header, process name, file path or log message that an exploit attempt would leave behind, and the vendor bulletin page did not load. Any rule would have to invent indicators from memory.
- Add the vendor advisory or an intel write-up to `advisories/CVE-2026-88772.txt` and rerun.

### CVE-2026-88779: improper restriction of operations within the bounds of a memory buffer (memory buffer overflow leading to denial of service)
- The advisory describes the impact as denial of service only and names no URL path, parameter, log message or other artifact an exploit attempt would leave behind; the vendor article body did not load, so there is nothing traceable to detect on.
