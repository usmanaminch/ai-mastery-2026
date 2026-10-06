"""CWE -> runtime detection strategy.

Every CWE falls into one of three buckets:

  RULE         The exploit leaves a signature in logs we commonly collect
               (web access logs, process creation). We emit Sigma rules.
  BEHAVIORAL   Exploitation looks like normal traffic from the wrong person
               (IDOR, missing authz, brute force). Needs baselining or
               correlation, not a payload signature. We emit no rule and say so.
  UNCOVERABLE  The weakness is not exercised by a request we can see
               (hardcoded secrets, weak crypto, cleartext storage). The fix is
               the only control. We emit no rule and say so.

Anything not listed here is UNMAPPED and is reported for manual review.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RULE, BEHAVIORAL, UNCOVERABLE, UNMAPPED = "rule", "behavioral", "uncoverable", "unmapped"

WEB = {"category": "webserver"}
PROC_LINUX = {"category": "process_creation", "product": "linux"}

APP_RUNTIMES = ["/python", "/python3", "/gunicorn", "/uwsgi", "/node", "/java", "/php-fpm", "/php"]
SHELLS_AND_TOOLS = ["/sh", "/bash", "/dash", "/zsh", "/curl", "/wget", "/nc", "/ncat", "/socat", "/perl"]


@dataclass(frozen=True)
class Detector:
    """One Sigma rule template."""
    name: str
    logsource: dict
    field: str
    modifier: str
    values: list[str]
    attack_tags: list[str]
    falsepositives: list[str]
    route_scoped: bool = True
    parent_field: str | None = None
    parent_values: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Strategy:
    bucket: str
    note: str
    detectors: tuple[Detector, ...] = ()


def _web(name, values, tags, fps):
    return Detector(name=name, logsource=WEB, field="cs-uri-query", modifier="contains",
                    values=values, attack_tags=tags, falsepositives=fps)


def _child_process(name, tags, fps):
    # Every CWE whose exploitation ends in code execution shares one runtime signal, so they share
    # one detector name and the converter emits a single rule listing all of them.
    return Detector(name="app_runtime_child_shell", logsource=PROC_LINUX, field="Image", modifier="endswith",
                    values=SHELLS_AND_TOOLS, attack_tags=tags, falsepositives=fps,
                    route_scoped=False, parent_field="ParentImage", parent_values=APP_RUNTIMES)


T1190 = ["attack.initial_access", "attack.t1190"]
T1059 = ["attack.execution", "attack.t1059"]

STRATEGIES: dict[str, Strategy] = {
    "CWE-89": Strategy(RULE, "SQL injection payloads appear in the query string.", (
        _web("sqli_payload", ["' or ", "'or'", "union select", "union%20select", "%27%20or%20",
                              "' --", "%27--", "sleep(", "benchmark(", "pg_sleep(", "waitfor delay",
                              "information_schema"],
             T1190, ["Search fields that legitimately accept SQL-like text"]),
    )),
    "CWE-78": Strategy(RULE, "Shell metacharacters in the request, and the app runtime spawning a shell.", (
        _web("cmdi_payload", [";id", "%3Bid", "|id", "%7Cid", "$(", "%24%28", "`", "%60",
                              ";cat ", "%3Bcat", "&&", "%26%26", "/etc/passwd", "; whoami", "%3Bwhoami"],
             T1190 + T1059, ["Parameters that legitimately carry shell-like characters"]),
        _child_process("cmdi_child_shell", T1059,
                       ["Applications that legitimately shell out; baseline expected children first"]),
    )),
    "CWE-77": Strategy(RULE, "Command injection variant; same signals as CWE-78.", (
        _child_process("cmdi_child_shell", T1059,
                       ["Applications that legitimately shell out; baseline expected children first"]),
    )),
    "CWE-22": Strategy(RULE, "Traversal sequences appear in the query string.", (
        _web("path_traversal_payload", ["../", "..%2f", "..%2F", "%2e%2e%2f", "%2E%2E%2F", "%252e%252e",
                                        "..\\", "..%5c", "/etc/passwd", "/etc/shadow", "win.ini",
                                        "/proc/self/environ"],
             T1190, ["Clients requesting relative paths legitimately"]),
    )),
    "CWE-918": Strategy(RULE, "Internal or metadata destinations appear in a URL parameter.", (
        _web("ssrf_internal_target", ["169.254.169.254", "metadata.google.internal", "localhost",
                                      "127.0.0.1", "0.0.0.0", "[::1]", "file://", "file%3A%2F%2F",
                                      "gopher://", "gopher%3A%2F%2F", "dict://"],
             T1190, ["Health checks or admin tools that reference internal hosts"]),
    )),
    "CWE-79": Strategy(RULE, "Script payloads appear in the query string (reflected XSS only).", (
        _web("xss_payload", ["<script", "%3cscript", "%3Cscript", "javascript:", "onerror=", "onload=",
                             "%3Cimg", "%3Csvg", "alert(", "document.cookie"],
             T1190, ["Security scanners", "Content fields that accept HTML"]),
    )),
    "CWE-1336": Strategy(RULE, "Template expressions appear in the query string.", (
        _web("ssti_payload", ["{{", "%7B%7B", "{%", "%7B%25", "${", "%24%7B", "__class__", "__globals__"],
             T1190, ["Fields that accept template-like text"]),
        _child_process("ssti_child_shell", T1059, ["Applications that legitimately shell out"]),
    )),
    "CWE-94": Strategy(RULE, "Code injection: the strongest signal is the runtime spawning a shell.", (
        _web("code_injection_payload", ["__import__", "eval(", "exec(", "os.system", "subprocess",
                                        "%5F%5Fimport%5F%5F"],
             T1190 + T1059, ["Developer tooling endpoints"]),
        _child_process("code_injection_child_shell", T1059, ["Applications that legitimately shell out"]),
    )),
    "CWE-502": Strategy(RULE, "The payload rides in a cookie or body that web logs rarely record, "
                              "so the reliable signal is what the gadget does: spawn a process.", (
        _child_process("deserialization_child_shell", T1059,
                       ["Applications that legitimately shell out; baseline expected children first"]),
    )),
    "CWE-601": Strategy(RULE, "Off-site URLs appear in redirect parameters.", (
        _web("open_redirect_param", ["next=http", "next=%2F%2F", "url=http", "url=%2F%2F",
                                     "redirect=http", "redirect=%2F%2F", "return=http", "returnTo=http"],
             T1190, ["Legitimate cross-domain SSO flows"]),
    )),
    "CWE-95": Strategy(RULE, "Eval injection: code fragments in the request, and the runtime spawning a shell.", (
        _web("eval_injection_payload", ["__import__", "eval(", "exec(", "os.system", "os.popen", "subprocess",
                                        "%5F%5Fimport%5F%5F", "compile("],
             T1190 + T1059, ["Developer tooling endpoints"]),
        _child_process("eval_injection_child_shell", T1059, ["Applications that legitimately shell out"]),
    )),
    "CWE-117": Strategy(RULE, "Log injection: encoded line breaks in the request forge new log lines.", (
        _web("log_injection_crlf", ["%0d", "%0D", "%0a", "%0A", "\\r\\n", "%E5%98%8A", "%E5%98%8D"],
             ["attack.defense_evasion", "attack.t1070"], ["Multi-line form fields submitted via GET"]),
    )),
    "CWE-93": Strategy(RULE, "CRLF injection: encoded line breaks in the request.", (
        _web("crlf_injection", ["%0d%0a", "%0D%0A", "%0a", "%0A"], T1190, ["Multi-line form fields"]),
    )),
    "CWE-113": Strategy(RULE, "HTTP response splitting: encoded line breaks in header-bound parameters.", (
        _web("response_splitting", ["%0d%0a", "%0D%0A", "%0aSet-Cookie", "%0ALocation"], T1190,
             ["Multi-line form fields"]),
    )),
    "CWE-90": Strategy(RULE, "LDAP injection metacharacters in the query string.", (
        _web("ldap_injection", ["*)(", "%2A%29%28", ")(|", "%29%28%7C", "(|(", "%28%7C%28", "*)(uid=*"],
             T1190, ["Search fields accepting wildcard syntax"]),
    )),
    "CWE-643": Strategy(RULE, "XPath injection fragments in the query string.", (
        _web("xpath_injection", ["' or '1'='1", "%27%20or%20%271%27%3D%271", "or 1=1", "count(/", "name(/"],
             T1190, ["Search fields accepting query syntax"]),
    )),
    "CWE-1321": Strategy(RULE, "Prototype pollution keys in the query string.", (
        _web("prototype_pollution", ["__proto__", "constructor[prototype]", "constructor%5Bprototype%5D",
                                     "__proto__%5B"], T1190, ["Rare in legitimate traffic"]),
    )),
    "CWE-400": Strategy(BEHAVIORAL, "Resource exhaustion is a volume or latency pattern over time, not a "
                                    "single request. Needs rate baselines per endpoint."),
    "CWE-770": Strategy(BEHAVIORAL, "Missing rate limits show up as request volume, not a payload."),
    "CWE-1333": Strategy(BEHAVIORAL, "ReDoS shows up as request latency spikes; needs response-time baselines."),
    "CWE-367": Strategy(BEHAVIORAL, "Race conditions are exploited with bursts of concurrent requests; "
                                    "detect as near-simultaneous duplicates per session."),
    "CWE-340": Strategy(BEHAVIORAL, "Predictable identifiers are exploited by enumeration: one client "
                                    "walking sequential IDs. Needs per-client counting."),
    "CWE-359": Strategy(BEHAVIORAL, "Private data exposure looks like normal reads; detect by volume of "
                                    "records returned per user."),
    "CWE-200": Strategy(BEHAVIORAL, "Information exposure looks like normal reads; detect by access volume."),
    "CWE-290": Strategy(BEHAVIORAL, "Spoofed identity (e.g. trusted headers) needs the header logged and an "
                                    "identity-aware baseline; standard web logs omit most headers."),
    "CWE-807": Strategy(BEHAVIORAL, "Security decisions on client-controlled input (cookies, headers, hidden "
                                    "fields) need those values logged plus identity correlation."),
    "CWE-565": Strategy(BEHAVIORAL, "Cookie-based trust is exploited by editing cookies, which standard web "
                                    "logs do not record. Needs application-level logging of the decision."),
    "CWE-384": Strategy(BEHAVIORAL, "Session fixation needs session-ID lifecycle correlation."),
    "CWE-613": Strategy(BEHAVIORAL, "Long-lived sessions need session-age monitoring."),
    "CWE-640": Strategy(BEHAVIORAL, "Weak password recovery is exploited by many reset attempts; needs counting."),
    "CWE-434": Strategy(BEHAVIORAL, "Malicious upload rides in the request body; watch for the uploaded file "
                                    "later being requested or executed."),
    "CWE-922": Strategy(UNCOVERABLE, "Insecure storage is exploited after a separate compromise."),
    "CWE-732": Strategy(UNCOVERABLE, "Incorrect file permissions: configuration fix."),
    "CWE-615": Strategy(UNCOVERABLE, "Sensitive information in source comments: remove it from source and history."),
    "CWE-521": Strategy(UNCOVERABLE, "Weak password policy: policy fix; monitor credential attacks separately."),
    "CWE-250": Strategy(UNCOVERABLE, "Running with unnecessary privilege (e.g. root in a container): "
                                     "configuration fix that shrinks blast radius."),
    "CWE-1104": Strategy(UNCOVERABLE, "Unmaintained third-party component: upgrade or replace."),
    "CWE-1395": Strategy(UNCOVERABLE, "Vulnerable third-party dependency: upgrade."),
    "CWE-209": Strategy(UNCOVERABLE, "Verbose error messages: configuration fix."),
    "CWE-215": Strategy(UNCOVERABLE, "Debug information exposed: configuration fix."),
    "CWE-295": Strategy(UNCOVERABLE, "Improper certificate validation is exploited on the network path."),
    "CWE-326": Strategy(UNCOVERABLE, "Weak key strength is exploited offline."),
    "CWE-338": Strategy(UNCOVERABLE, "Weak PRNG is exploited by prediction, not a payload."),
    "CWE-942": Strategy(UNCOVERABLE, "Permissive CORS: configuration fix."),
    "CWE-1021": Strategy(UNCOVERABLE, "Clickjacking: add frame-ancestors / X-Frame-Options."),
    "CWE-693": Strategy(UNCOVERABLE, "Missing protection mechanism: configuration fix."),
    "CWE-611": Strategy(BEHAVIORAL, "XXE payloads travel in the request body, which standard web logs do "
                                    "not record. Needs WAF or application-level body logging, or egress "
                                    "monitoring for the parser fetching external entities."),
    "CWE-639": Strategy(BEHAVIORAL, "IDOR looks like a valid request for someone else's object. Detect by "
                                    "baselining per-user object access (one session touching many IDs)."),
    "CWE-284": Strategy(BEHAVIORAL, "Access-control failures look like normal requests from the wrong user. "
                                    "Needs identity-aware baselining."),
    "CWE-285": Strategy(BEHAVIORAL, "Authorization failures need identity-aware baselining."),
    "CWE-862": Strategy(BEHAVIORAL, "Missing authorization needs identity-aware baselining."),
    "CWE-863": Strategy(BEHAVIORAL, "Incorrect authorization needs identity-aware baselining."),
    "CWE-287": Strategy(BEHAVIORAL, "Authentication bypass needs session/identity correlation."),
    "CWE-306": Strategy(BEHAVIORAL, "Missing authentication: watch for unauthenticated hits on the "
                                    "endpoint, which requires knowing it should be authenticated."),
    "CWE-307": Strategy(BEHAVIORAL, "Brute force is a count over time (a correlation rule), not a "
                                    "single-event signature."),
    "CWE-352": Strategy(BEHAVIORAL, "CSRF requests are indistinguishable from legitimate ones in logs "
                                    "without Origin/Referer logging."),
    "CWE-798": Strategy(UNCOVERABLE, "A hardcoded secret is exploited wherever the secret is used, not "
                                     "through this app's requests. Rotate the secret; monitor its use at "
                                     "the system it unlocks."),
    "CWE-259": Strategy(UNCOVERABLE, "Hardcoded password: rotate it; monitor its use where it authenticates."),
    "CWE-321": Strategy(UNCOVERABLE, "Hardcoded cryptographic key: rotate it."),
    "CWE-327": Strategy(UNCOVERABLE, "Weak cryptography is exploited offline against stolen data; "
                                     "nothing to see at request time."),
    "CWE-328": Strategy(UNCOVERABLE, "Weak hashing is exploited offline."),
    "CWE-916": Strategy(UNCOVERABLE, "Weak password hashing is exploited offline."),
    "CWE-330": Strategy(UNCOVERABLE, "Predictable randomness is exploited by prediction, not a payload."),
    "CWE-312": Strategy(UNCOVERABLE, "Cleartext storage is exploited after a separate compromise."),
    "CWE-319": Strategy(UNCOVERABLE, "Cleartext transmission is exploited on the network path."),
    "CWE-532": Strategy(UNCOVERABLE, "Secrets in logs: fix the logging and scrub existing logs."),
    "CWE-614": Strategy(UNCOVERABLE, "Missing Secure cookie flag: configuration fix."),
    "CWE-1004": Strategy(UNCOVERABLE, "Missing HttpOnly flag: configuration fix."),
    "CWE-16": Strategy(UNCOVERABLE, "Configuration weakness: configuration fix."),
    "CWE-489": Strategy(RULE, "Debug mode is a configuration fix, but an exposed Werkzeug debugger has a "
                              "distinctive exploitation signature: requests to /console or carrying "
                              "__debugger__=yes&cmd=. Django's DEBUG=True has no equivalent.", (
        _web("werkzeug_debugger_console", ["__debugger__=yes", "__debugger__%3Dyes"], T1190 + T1059,
             ["Developers using the debugger in a non-production environment"]),
        Detector(name="werkzeug_console_path", logsource=WEB, field="cs-uri-stem", modifier="endswith",
                 values=["/console"], attack_tags=T1190, route_scoped=False,
                 falsepositives=["Applications with a legitimate /console route"]),
    )),
}


def strategy_for(cwe_id: str | None) -> Strategy:
    if not cwe_id:
        return Strategy(UNMAPPED, "No CWE resolved for this finding; review manually.")
    return STRATEGIES.get(cwe_id, Strategy(UNMAPPED, f"{cwe_id} has no mapping yet; review manually."))
