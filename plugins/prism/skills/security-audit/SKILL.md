---
name: security-audit
description: >-
  Fan-out security audit. Spawns parallel read-only subagents, each analyzing the code through
  one threat lens (injection, authz/authn, secrets & crypto, input/output, logic & deps), then
  triages and re-verifies findings to kill false positives, and reports a concise severity-
  ranked list with root-cause, blast-radius-aware fixes. Use when the user says "security
  audit", "prism audit", "check for vulnerabilities", "is this secure", or wants a security
  review of a diff or a whole codebase. Reports Medium severity and above by default.
---

# Security Audit (fan-out)

One reviewer looking for "security issues" misses things — each threat class needs its own
mindset. This lens **fans out** to specialized read-only subagents, one per threat lens,
collects their findings, then **triages and re-verifies** before reporting. False positives are
expensive; noise gets filtered hard.

## Step 1 — Set scope

- `pr`/diff mode → audit only changed files/lines (`git diff`) plus their immediate reachable
  callers. `improve`/`audit` on a clean repo → whole codebase (announce, it may take a while).
- `plan`/`new` mode → no code yet: do a **design-level** review (threat-model the approach,
  secure-by-design checklist) instead of scanning files.
- Read `references/threat-lenses.md` for the per-lens checklists before dispatching.

## Step 2 — Fan out (parallel, read-only)

Spawn these subagents **in parallel** (single message, multiple Task calls). Each is read-only
(no edits), gets the scope + relevant files, and returns findings as structured items. The
plugin ships matching agent definitions (`prism-sec-*`); use them, or brief general subagents
with the same charge if custom agent types aren't available.

| Subagent | Threat lens |
|----------|-------------|
| `prism-sec-injection` | SQL / NoSQL / command / LDAP / template / XXE injection |
| `prism-sec-authz` | AuthN & authZ — IDOR, privilege escalation, broken access control, session/JWT |
| `prism-sec-secrets-crypto` | Hardcoded secrets, weak/mis-used crypto, key management, weak randomness |
| `prism-sec-inputoutput` | Input validation, XSS, SSRF, path traversal, unsafe deserialization, open redirect |
| `prism-sec-logic-deps` | Race/TOCTOU, business-logic flaws, vulnerable/outdated deps, insecure config/defaults |

Each subagent returns, per finding: `file:line`, threat class, concrete evidence (the code),
why it's exploitable, a **confidence** (0–100), and a proposed **severity**.

## Step 3 — Triage & validate

Hand all raw findings to the `prism-sec-triage` agent (or do it in the parent):

- **Dedup** overlapping findings across lenses.
- **Drop noise.** Suppress low-value categories the way Anthropic's security-review does:
  generic DoS/rate-limiting, purely theoretical issues, style-only "validation" nits, and
  anything not actually reachable. Keep only real, reachable risks.
- **Re-verify.** For each surviving finding, independently re-read the cited code to confirm it
  is real and exploitable in context. Discard confidence < 80.
- **Rank** by severity (see below).

## Step 4 — Fixes (root-cause, blast-radius-aware)

For each confirmed finding, design a fix that addresses the **root cause**, not the symptom,
and that **won't break callers**: inspect who uses the code, what the fix changes for them, and
prefer the smallest correct change. In fix-enabled modes (`pr`, `improve`) apply it and then
**validate** (tests/build); otherwise present it as a diff for the user to apply.

## Severity & threshold

Map to CVSS-style tiers: **Critical** (RCE, auth bypass, secret exposure) · **High** (injection,
IDOR, SSRF) · **Medium** (weak crypto, missing hardening with real impact) · **Low** (defense-in-
depth). **Report Medium and above by default**; note how many Low items were suppressed.

## Output

```
## 🛡️ Security audit — <scope>  (5 lenses · <N> raw → <M> confirmed)

### Critical
- `app/api.py:88` — `eval(request.args["q"])` → RCE via user input.
  Root cause: untrusted input reaches a code evaluator.
  Fix: replace with an explicit allow-list parser; no eval. Blast radius: only `search()` calls
  this; return type unchanged. ✓ tests pass

### High
- `auth/session.py:40` — IDOR: object id from the request isn't checked against the caller.

### Summary
1 Critical · 1 High · 2 Medium · (3 Low suppressed) · validation: tests pass
```

## References
- OWASP Secure Code Review Cheat Sheet
- anthropics/claude-code-security-review (false-positive filtering)
- See `references/threat-lenses.md` for the full per-lens checklists.
