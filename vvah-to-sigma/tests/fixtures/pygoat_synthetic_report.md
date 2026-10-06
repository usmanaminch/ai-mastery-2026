# Security Scan Report — pygoat (SYNTHETIC FIXTURE)

This file is a hand-written fixture in VVAH's report format, used only to test
the converter before a real scan exists. Findings mirror the lab categories
PyGoat is known to contain; file paths and lines are illustrative.

## Findings

### 1. [CRITICAL] SQL injection in login lab via string-formatted query
**Class:** CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')
**CWE:** CWE-89: SQL Injection - https://cwe.mitre.org/data/definitions/89.html
**File:** `introduction/views.py:120-138`
**CVSS 3.1:** 9.8 (Critical) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
**Confidence:** 0.92 (3 runs agreed)

#### Description
User-supplied `name` and `pass` parameters are concatenated into a raw SQL query.

### 2. [CRITICAL] OS command injection in DNS lookup lab
**Class:** CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
**CWE:** CWE-78: OS Command Injection - https://cwe.mitre.org/data/definitions/78.html
**File:** `introduction/views.py:410-425`
**CVSS 3.1:** 9.8 (Critical) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
**Confidence:** 0.95 (3 runs agreed)

#### Description
The `domain` parameter is passed to `subprocess.Popen(..., shell=True)`.

### 3. [HIGH] Server-side request forgery in URL fetch lab
**Class:** CWE-918: Server-Side Request Forgery (SSRF)
**CWE:** CWE-918: Server-Side Request Forgery (SSRF) - https://cwe.mitre.org/data/definitions/918.html
**File:** `introduction/views.py:880-901`
**CVSS 3.1:** 8.6 (High) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N`
**Confidence:** 0.88 (3 runs agreed)

#### Description
A user-supplied URL is fetched server-side with no allowlist.

### 4. [HIGH] Path traversal in file read endpoint
**Class:** CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
**CWE:** CWE-22: Path Traversal - https://cwe.mitre.org/data/definitions/22.html
**File:** `introduction/views.py:650-662`
**CVSS 3.1:** 7.5 (High) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**Confidence:** 0.81 (2 runs agreed)

#### Description
A filename parameter is joined to a base directory without normalization.

### 5. [HIGH] Insecure deserialization of cookie with pickle
**Class:** CWE-502: Deserialization of Untrusted Data
**CWE:** CWE-502: Deserialization of Untrusted Data - https://cwe.mitre.org/data/definitions/502.html
**File:** `introduction/views.py:540-552`
**CVSS 3.1:** 9.8 (Critical) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
**Confidence:** 0.90 (3 runs agreed)

#### Description
A base64 cookie value is passed to `pickle.loads`.

### 6. [MEDIUM] Reflected cross-site scripting in search lab
**Class:** CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')
**CWE:** CWE-79: Cross-site Scripting - https://cwe.mitre.org/data/definitions/79.html
**File:** `introduction/templates/Lab/XSS/xss_lab.html:22-24`
**CVSS 3.1:** 6.1 (Medium) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N`
**Confidence:** 0.86 (3 runs agreed)

#### Description
The `q` parameter is rendered with the `safe` filter.

### 7. [HIGH] Hardcoded Django SECRET_KEY
**Class:** CWE-798: Use of Hard-coded Credentials
**CWE:** CWE-798: Use of Hard-coded Credentials - https://cwe.mitre.org/data/definitions/798.html
**File:** `pygoat/settings.py:23-23`
**CVSS 3.1:** 7.5 (High) — `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
**Confidence:** 0.97 (3 runs agreed)

#### Description
`SECRET_KEY` is committed in source.

### 8. [MEDIUM] Weak password hashing with MD5
**Class:** CWE-327: Use of a Broken or Risky Cryptographic Algorithm
**CWE:** CWE-327: Use of a Broken or Risky Cryptographic Algorithm - https://cwe.mitre.org/data/definitions/327.html
**File:** `introduction/views.py:300-305`
**CVSS 3.1:** 5.9 (Medium) — `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N`
**Confidence:** 0.84 (3 runs agreed)

#### Description
Passwords are hashed with unsalted MD5.

### 9. [HIGH] Insecure direct object reference on user profile
**Class:** CWE-639: Authorization Bypass Through User-Controlled Key
**CWE:** CWE-639: Authorization Bypass Through User-Controlled Key - https://cwe.mitre.org/data/definitions/639.html
**File:** `introduction/views.py:720-735`
**CVSS 3.1:** 6.5 (Medium) — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N`
**Confidence:** 0.79 (2 runs agreed)

#### Description
The `id` parameter selects any user's profile without an ownership check.
