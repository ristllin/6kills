---
name: security-audit
description: >-
  Fan-out security audit. Spawns parallel read-only subagents, each analyzing the code through
  one threat lens (injection, authz/authn, secrets & crypto, input/output, business-logic,
  supply-chain/config, plus conditional memory-safety and LLM-app lenses), then triages and
  adversarially re-verifies findings to kill false positives, and reports a concise severity-
  ranked list with root-cause, blast-radius-aware fixes. Use when the user says "security
  audit", "prism audit", "check for vulnerabilities", "is this secure", or wants a security
  review of a diff or a whole codebase. Reports Medium severity and above by default.
---

# Security Audit (fan-out)

One reviewer looking for "security issues" misses things — each threat class needs its own
mindset, and diverse specialists beat homogeneous voters (2 diverse agents ≈ 16 identical ones,
arXiv 2602.03794). This lens **fans out** to specialized read-only subagents, one per threat
lens, collects their findings, then **triages and adversarially re-verifies** before reporting.
False positives are expensive; noise gets filtered hard.

## Step 1 — Set scope

- `pr`/diff mode → audit only changed files/lines (`git diff`) plus their immediate reachable
  callers. `improve`/`audit` on a clean repo → whole codebase (announce, it may take a while).
- `plan`/`new` mode → no code yet: do a **design-level** review (threat-model the approach,
  secure-by-design checklist) instead of scanning files.
- **Read textual context first** — the commit message(s), PR description, and any linked issue.
  Intent context measurably beats extra code context (ContextCRBench, arXiv 2511.07017).
- Large diff (> ~150 changed lines)? Precision collapses on giant diffs (arXiv 2606.15689):
  review chunk-by-logical-change rather than dumping the whole diff into one pass.
- Read `references/threat-lenses.md` for the per-lens checklists before dispatching.

## Step 1.5 — Detect the stack (which lenses to spawn)

Run the **core** lenses always. Add a **conditional** lens only when the stack calls for it —
conditional-by-detection keeps the fan-out orthogonal instead of paying for lenses that can't
fire (`git ls-files` / `Glob` to detect):

- **Memory-unsafe languages present** (`.c`/`.cpp`/`.cc`/`.h`, unsafe Rust, cgo) → spawn a
  **memory-safety** lens. No dedicated agent file — brief a general read-only subagent with
  §6 of `references/threat-lenses.md` (CWE-787/125/416/476/190).
- **The audited app itself integrates LLMs** (calls an LLM API, defines tools/agents, renders
  model output) → tell `prism-sec-inputoutput` to also apply the **LLM-app** brief (§7):
  treat model output as untrusted input (prompt injection, unsanitized model output → sink,
  excessive agent tool permissions — OWASP LLM Top 10).

## Step 2 — Fan out (parallel, read-only)

Spawn these subagents **in parallel** (single message, multiple Task calls). Each is read-only
(no edits), gets the scope + relevant files, and returns findings as structured items. The
plugin ships matching agent definitions (`prism-sec-*`); use them, or brief general subagents
with the same charge if custom agent types aren't available.

| Subagent | Threat lens | When |
|----------|-------------|------|
| `prism-sec-injection` | SQL / NoSQL / command / LDAP / template / XXE injection | core |
| `prism-sec-authz` | AuthN & authZ — IDOR, privilege escalation, broken access control, session/JWT | core |
| `prism-sec-secrets-crypto` | Hardcoded secrets, weak/mis-used crypto, key management, weak randomness | core |
| `prism-sec-inputoutput` | Input validation, XSS, SSRF, path traversal, unsafe deserialization, open redirect (+ LLM-app brief if detected) | core |
| `prism-sec-logic` | Race/TOCTOU, business-logic flaws, insecure design, workflow bypass | core |
| `prism-sec-supplychain-config` | Vulnerable/outdated deps, lockfile/CI-CD integrity, insecure defaults, CORS/headers, IaC/cloud misconfig | core |
| memory-safety (general subagent, §6) | Out-of-bounds R/W, use-after-free, null-deref, integer overflow | if memory-unsafe code present |

Each subagent returns, per finding: `file:line`, threat class, concrete evidence, a concrete
**`exploit_scenario`** (an attacker action and the path/impact it reaches), a **confidence**
(0–100), and a proposed **severity**. For **data-flow classes** (injection, XSS, SSRF, path
traversal, IDOR, unsafe deser) it also returns a **taint walk** (source → propagation → sink →
missing sanitizer) — forcing that walk is a strong precision lever for those classes. For
non-flow classes (weak crypto, hardcoded secret, misconfig, vulnerable dep) a taint walk
doesn't apply; class-appropriate evidence stands on its own. Lenses apply a **generation-time
floor**: below ~70 confidence, don't report at all.

## Step 3 — Triage & adversarially verify

First a **deterministic pre-filter** (no model call — cheap and consistent): drop
**style-only** findings that live only in docs/markdown (but keep secrets, install commands,
IaC, and LLM-ingested content wherever they appear), DoS / rate-limiting findings that cite
**no concrete amplification** (keep zip bombs, algorithmic-complexity blowups, unbounded
uploads, brute-force with impact), and memory-safety findings in memory-safe languages. Then
hand the survivors to `prism-sec-triage` (or do it in the parent):

- **Dedup** overlapping findings across lenses (including several lenses converging on one
  root flaw).
- **Refute, don't just re-read.** For each finding, *actively try to disprove it* — hunt for
  the sanitizer, the auth check, or the caller that never passes attacker-controlled input.
  The triage agent has license to Read/Grep **beyond** the finding's context (callers,
  validators, config); context breadth is the measured lever (Team Atlanta: 25%→90%). State
  what you checked and ruled out, not just a verdict.
- **Reject hand-wavy findings.** If the `exploit_scenario` is generic ("could be exploited if
  input is untrusted") rather than a concrete input + reachable path, drop it.
- **Discard confidence < 80.** The number is the weaker signal; the refutation above is what
  matters. Keep only what survives a genuine attempt to disprove it.
- **Rank** by severity (see below).

## Step 4 — Fixes (root-cause, blast-radius-aware)

For each confirmed finding, design a fix that addresses the **root cause**, not the symptom,
and that **won't break callers**: inspect who uses the code, what the fix changes for them, and
prefer the smallest correct change. In fix-enabled modes (`pr`, `improve`) apply it and then
**validate** (tests/build); otherwise present it as a diff for the user to apply. The agent
that wrote a fix does not sign off on it — validation is tests/build, or a different agent.

## Severity & threshold

Map to CVSS-style tiers: **Critical** (RCE, auth bypass, secret exposure) · **High** (injection,
IDOR, SSRF) · **Medium** (weak crypto, missing hardening with real impact) · **Low** (defense-in-
depth). **Report Medium and above by default**; note how many Low items were suppressed.

Report findings as **high-confidence leads for human review, not proven exploits** — even
dedicated red-team agents resolve only ~13% of real CVEs end-to-end (CVE-Bench). Confidence is
"a careful reviewer would flag this," not "this is weaponized."

## Output

```
## 🛡️ Security audit — <scope>  (<L> lenses · <N> raw → <P> pre-filtered → <M> confirmed)

### Critical
- `app/api.py:88` — `eval(request.args["q"])` → RCE via user input.
  Taint: request.args["q"] → search() → eval(), no sanitizer.
  Exploit: `?q=__import__('os').system('id')` reaches eval() directly.
  Root cause: untrusted input reaches a code evaluator.
  Fix: replace with an explicit allow-list parser; no eval. Blast radius: only `search()` calls
  this; return type unchanged. ✓ tests pass

### High
- `auth/session.py:40` — IDOR: object id from the request isn't checked against the caller.
  Triage ruled out: no ownership check exists on any caller path.

### Summary
1 Critical · 1 High · 2 Medium · (3 Low suppressed) · validation: tests pass
Leads for human review — not confirmed exploits.
```

## References
- OWASP Top 10 (2025) & OWASP Top 10 for LLM Applications; CWE Top 25.
- anthropics/claude-code-security-review (two-stage filter, generation-time confidence floor, exploit_scenario field).
- Taint-style prompting as the top precision lever; context breadth over prompt cleverness (Team Atlanta, AIxCC).
- See `references/threat-lenses.md` for the full per-lens checklists.
