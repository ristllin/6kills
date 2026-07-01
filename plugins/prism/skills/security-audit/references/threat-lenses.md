# Threat lenses — per-subagent checklists

Loaded by `security-audit` before fan-out. Each lens is deliberately narrow so the subagent
thinks like a specialist. All lenses are **read-only**: find and evidence, do not fix.

## 1. Injection (`prism-sec-injection`)
- SQL / NoSQL: string-built queries, missing parameterization, ORM `.raw()` with interpolation.
- OS command: `exec`/`system`/`subprocess`/backticks with user input; shell=True.
- Template injection (SSTI): user input into Jinja/ERB/Handlebars templates.
- LDAP / XPath / NoSQL operator injection; XML external entities (XXE) in parsers.
- Eval-family: `eval`, `exec`, `Function()`, `pickle.loads`, deserializing untrusted data.
- Evidence: trace untrusted source → sink. Confirm the input is attacker-controlled.

## 2. AuthN / AuthZ (`prism-sec-authz`)
- Missing authorization checks on state-changing or data-returning endpoints.
- IDOR: object identifiers taken from the request without ownership/tenant checks.
- Privilege escalation: role/permission derived from client-controlled data.
- Broken authentication: weak password handling, missing rate limit on login *with* real
  impact, session fixation, predictable tokens.
- JWT: `alg:none`, unverified signature, secret confusion, missing expiry/audience checks.
- Session: insecure cookie flags (missing `HttpOnly`/`Secure`/`SameSite`) where it matters.

## 3. Secrets & crypto (`prism-sec-secrets-crypto`)
- Hardcoded secrets/API keys/passwords/private keys in source or config.
- Weak algorithms: MD5/SHA1 for passwords, DES/ECB, custom "encryption".
- Password storage without a slow salted KDF (bcrypt/scrypt/argon2).
- Weak randomness for security (`Math.random`, `random`) instead of a CSPRNG.
- Key management: keys in repo, no rotation, overly broad scope.

## 4. Input / output handling (`prism-sec-inputoutput`)
- Missing/weak input validation at trust boundaries.
- XSS: unescaped user data into HTML/DOM; `dangerouslySetInnerHTML`, `innerHTML`.
- SSRF: server-side fetch to a user-controlled URL without allow-listing.
- Path traversal: user input into file paths without normalization/containment.
- Unsafe deserialization; open redirects; header/CRLF injection; unsafe file upload handling.

## 5. Logic & dependencies (`prism-sec-logic-deps`)
- Race conditions / TOCTOU: check-then-act on shared state, non-atomic money/inventory ops.
- Business-logic flaws: negative quantities, price/qty tampering, workflow step-skipping.
- Vulnerable/outdated dependencies (flag known-risky packages/pins; suggest checking advisories).
- Insecure defaults & config: debug on in prod, permissive CORS (`*` with credentials), verbose
  errors leaking internals, missing security headers, world-readable perms.

## Suppress (noise — do NOT report unless clearly impactful)
- Generic DoS / "add rate limiting" without a concrete amplification.
- Purely theoretical issues with no reachable attacker path.
- Style-only "you should validate this" nits with no security impact.
- Defense-in-depth suggestions on already-safe code.

## Finding format each lens returns
```
- file: <path:line>
  class: <threat class>
  evidence: <the offending code / data flow>
  why: <why exploitable, attacker path>
  confidence: <0-100>
  severity: <Critical|High|Medium|Low>
```
