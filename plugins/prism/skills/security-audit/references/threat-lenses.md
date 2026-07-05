# Threat lenses — per-subagent checklists

Loaded by `security-audit` before fan-out. Each lens is deliberately narrow so the subagent
thinks like a specialist. All lenses are **read-only**: find and evidence, do not fix.

Every finding needs an **exploit_scenario** — a concrete attacker action and the path it
reaches — and a **taint walk** *where the class is a data-flow bug* (injection, XSS, SSRF,
path traversal, IDOR, unsafe deserialization). For classes that are **not** source-to-sink
flows (weak crypto, a hardcoded secret, a public S3 bucket, an unpinned dependency, an
insecure default), a taint walk doesn't apply — give class-appropriate evidence instead
(the weak primitive and where it's used, the exposed value, the misconfigured resource). Don't
suppress a real non-taint finding just because it has no source→sink chain. Apply a
**generation-time confidence floor**: below ~70, don't report at all.

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
- Field/resolver-level authz: GraphQL resolvers or API fields authorized only at the
  endpoint level, not per-field/per-object (a common blind spot for route-level reviewers).

## 3. Secrets & crypto (`prism-sec-secrets-crypto`)
- Hardcoded secrets/API keys/passwords/private keys in source or config.
- Weak algorithms: MD5/SHA1 for passwords, DES/ECB, custom "encryption".
- Password storage without a slow salted KDF (bcrypt/scrypt/argon2).
- Weak randomness for security (`Math.random`, `random`) instead of a CSPRNG.
- Key management: keys in repo, no rotation, overly broad scope.
- Secrets leaking into logs / error messages / telemetry sinks.

## 4. Input / output handling (`prism-sec-inputoutput`)
- Missing/weak input validation at trust boundaries.
- XSS: unescaped user data into HTML/DOM; `dangerouslySetInnerHTML`, `innerHTML`.
- SSRF: server-side fetch to a user-controlled URL without allow-listing.
- Path traversal: user input into file paths without normalization/containment.
- Unsafe deserialization; open redirects; header/CRLF injection; unsafe file upload handling.
- Mishandling of exceptional conditions: fail-open on error, verbose errors leaking internals
  (OWASP A10 2025).

## 5a. Logic & insecure design (`prism-sec-logic`)
- Race conditions / TOCTOU: check-then-act on shared state, non-atomic money/inventory ops,
  missing locks/transactions where concurrency matters.
- Business-logic flaws: negative quantities, price/qty tampering, workflow step-skipping,
  missing server-side enforcement of client-side rules.
- Insecure design (OWASP A06): architectural assumptions that no implementation check can
  rescue — trust placed in the client, missing threat-model controls for the feature's intent.

## 5b. Supply chain & configuration (`prism-sec-supplychain-config`)
- Vulnerable/outdated dependencies: scan manifests/lockfiles (`package.json`, `requirements`,
  `go.mod`, `Gemfile`, `Cargo.lock`, etc.) for known-risky or unpinned packages; recommend
  advisory checks (`npm audit`, `pip-audit`, `osv`). Don't fabricate CVE numbers — flag for
  verification (OWASP A03).
- Supply-chain integrity: typosquatted/confusable package names, unpinned or unverified
  install/build steps, malicious `postinstall`/lifecycle scripts, unsigned artifacts.
- Insecure defaults & config: debug on in prod, permissive CORS (`*` with credentials),
  verbose errors, missing security headers, world-readable perms (OWASP A02).
- IaC / cloud misconfiguration (when Terraform/K8s/CloudFormation/IAM files present):
  over-broad IAM policies, public buckets/records, disabled encryption, open security groups,
  privileged containers, missing least-privilege.

## 6. Memory safety (conditional — spawn only if C/C++/unsafe-Rust/cgo present)
- Out-of-bounds write (CWE-787) and read (CWE-125): missing bounds checks, off-by-one,
  `memcpy`/`strcpy`/array indexing on attacker-influenced sizes/offsets.
- Use-after-free (CWE-416) and double-free: pointer lifetime errors, freeing then dereferencing.
- NULL pointer dereference (CWE-476): unchecked allocation/lookup results.
- Integer overflow/underflow (CWE-190) feeding allocation sizes or bounds calculations.
- `unsafe` Rust blocks / cgo boundaries that break the safety guarantees of the safe code.

## 7. LLM-app risks (conditional — fold into lens 4 if the app integrates LLMs)
- Prompt injection: untrusted content (user input, retrieved docs, tool output) reaching the
  model's instructions without isolation (OWASP LLM01).
- Improper output handling: unsanitized model output flowing into a shell/SQL/HTML/eval sink
  (OWASP LLM05) — treat model output as untrusted input.
- Excessive agency: agents/tools granted broader permissions than the task needs (LLM06).
- Sensitive information disclosure and system-prompt leakage via the model (LLM02/LLM07).

## Suppress (noise — do NOT report unless clearly impactful)
- DoS / rate-limiting *without a concrete amplification*. Keep it if there's a real multiplier —
  algorithmic-complexity blowup, a zip/decompression bomb, an unbounded upload, queue
  exhaustion, or login brute-force with actual impact.
- Purely theoretical issues with no reachable attacker path.
- Style-only "you should validate this" nits with no security impact.
- Defense-in-depth suggestions on already-safe code.
- Memory-safety findings in memory-safe languages (managed/GC'd, safe Rust).
- **Style-only** findings that live only in docs/markdown. Do **not** blanket-drop docs: a
  hardcoded secret, a `curl | bash` install snippet, an IaC example copied into a deploy, or
  prompt-injection content an LLM app will ingest is real wherever it lives.

## Finding format each lens returns
```
- file: <path:line>
  class: <threat class>
  evidence: <the offending code / config / value>
  taint: <source → propagation → sink → missing sanitizer>   # data-flow classes only; omit if N/A
  exploit_scenario: <concrete attacker action + the path/impact it reaches>
  why: <why exploitable, attacker path>
  confidence: <70-100>   # below ~70, don't report
  severity: <Critical|High|Medium|Low>
```
