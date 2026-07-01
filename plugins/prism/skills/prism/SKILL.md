---
name: prism
description: >-
  Mode-aware code orchestrator that refracts code through four lenses — roast-with-docs,
  simplify, peer-review, and a fan-out security-audit. Use this whenever the user says
  "prism", "prism this", "prism pr", "prism review", "prism audit", "prism roast",
  "prism simplify", "prism peer", or "prism new", OR asks to review/improve/harden code,
  prepare a change for a PR, or get a second opinion on a plan or diff. Prism AUTO-DETECTS
  its mode from context (plan mode active, empty/new repo, clean existing repo, or a
  pending diff) and reuses the right lenses accordingly — it does not always run all four.
  It is considerate: read-only in plan mode, confirms before large sweeps or credit-spending
  cross-provider calls, and validates after every auto-fix.
---

# Prism

Prism refracts a body of code (or a plan) through up to four independent **lenses**, then
recombines their findings into one prioritized report. The point of prism is not to always
run everything — it is to **run the right lenses, at the right scope, with the right
fix-behavior, for the situation it detects.**

The four lenses are separate skills you invoke as sub-steps:

| Lens | Skill | What it does |
|------|-------|--------------|
| 🔥 Roast | `roast-with-docs` | Witty but technically-defensible critique, every jab cited to an authoritative doc/linter rule. |
| 🧹 Simplify | `simplify` | Maintainability pass — low nesting, guard clauses, lower complexity, better names — behavior preserved. |
| 🧑‍⚖️ Peer review | `peer-review` | Independent second opinion from a *different provider* (via `cursor-agent`), with graceful fallback. |
| 🛡️ Security | `security-audit` | Fan-out subagents, one per threat lens; triage + validate; severity-ranked, root-cause fixes. |

## Step 1 — Detect the mode (in this order)

Do not ask the user which mode to use unless detection is genuinely ambiguous. Detect it.

1. **Plan mode active?** If the harness is in plan mode (you can only take read-only actions
   and edit the plan file), you are in **`plan`** mode. This overrides everything below.
2. **Explicit argument?** If the user wrote `prism <word>`, honor it:
   `pr`, `audit`, `review`, `roast`, `simplify`, `peer`, `new`, `all`.
3. **Otherwise infer from git state.** Run:
   ```bash
   git rev-parse --is-inside-work-tree 2>/dev/null
   git status --porcelain
   git diff --stat; git diff --staged --stat
   git log --oneline -1 2>/dev/null
   ```
   - **Pending changes** (working tree, staged, or unpushed commits vs the base branch) → **`pr`** mode, scoped to the diff.
   - **Clean tree in a non-empty existing codebase** → **`improve`** mode (whole codebase). Confirm intent first.
   - **Empty / near-empty repo** (no source files, or only scaffolding) → **`new`** mode.
   - **Not a git repo / no code in context** → ask what to point prism at.

## Step 2 — Run the lenses for that mode

| Mode | Scope | Lenses (in order) | Fix behavior |
|------|-------|-------------------|--------------|
| **plan** | the proposed plan / approach in context | `peer-review` → `security-audit` (design-level, advisory) → `roast-with-docs` (of the approach) | **Read-only.** No `simplify` (nothing built yet). Never edit files. |
| **new** | intended architecture & approach | `security-audit` (secure-by-design checklist) → `peer-review` (of the approach) → `simplify` (as forward guidance/conventions) | Guidance + scaffolding only; minimal edits, ask before writing. |
| **pr** | `git diff` only (working + staged + commits vs base) | `simplify` → `security-audit` → `roast-with-docs` → `peer-review` | Auto-fix, **then validate** (run tests/build). |
| **improve** | whole codebase | `security-audit` → `simplify` → `roast-with-docs` → `peer-review` | Confirm intent → auto-fix → validate. |
| **audit** | diff or whole (by context) | `security-audit` only | Propose fixes; apply + validate only if already in pr/improve. |
| **single** (`roast`/`simplify`/`peer`) | current context | just that one lens | Per that lens's own default. |

When multiple lenses run, prefer to run the **read-only analysis lenses in parallel**
(spawn them as concurrent subagents), then apply fixes **sequentially** (simplify before
security fixes, re-validating between) so edits never race each other.

## Step 3 — Be considerate (non-negotiable rules)

- **Plan mode = read-only.** Detect it and never attempt an edit, even if a lens suggests one.
  Output advice; the user applies it later.
- **Validate before improving on a clean repo.** Before `improve` mode touches a whole
  codebase, confirm: *"No pending changes detected — run prism across the entire codebase to
  review and improve it? This may take a while."* Only proceed on yes.
- **Announce credit-spending / external calls.** `peer-review` may invoke `cursor-agent`
  (spends the user's Cursor credits) or a local model. Say so first and let the user skip.
- **Scope `pr` to the diff.** In `pr` mode, only reason about and modify lines within the
  diff (and their immediate blast radius). Do not opportunistically refactor untouched code.
- **Fixes are root-cause and blast-radius-aware.** Before applying any fix, check callers and
  dependents so the fix doesn't break something else. Prefer the smallest correct change.
- **Validate after every auto-fix sweep.** Run the project's tests / build / typecheck. If a
  fix breaks them, revert that fix and report it rather than leaving the tree broken.

## Step 4 — Recombine into one report

After the lenses run, merge their outputs into a single prioritized report. Use the shared
severity vocabulary so findings from different lenses stack rank together:

- **Confidence** 0–100 per finding; only surface ≥ 80 (drop likely false positives).
- **Severity**: `Critical` / `High` / `Medium` / `Low`. Default reporting threshold is
  `Medium` and up (security-audit) — mention how many low-severity items were suppressed.
- Each finding: `file:line` → what & why → severity → suggested/applied fix.

Report shape:

```
## Prism report — <mode> mode (<scope>)
Lenses run: 🧹 simplify · 🛡️ security · 🔥 roast · 🧑‍⚖️ peer

### 🛡️ Security (Critical/High first)
- [High] path/to/file.py:42 — <finding> · Fix: <root-cause fix, blast radius noted>

### 🧹 Simplify
- path/to/file.ts:88 — nested 4 deep; applied guard clauses (behavior unchanged) ✓ tests pass

### 🔥 Roast
- api/handler.js:12 — "<cited jab>" — per <official doc/rule link>

### 🧑‍⚖️ Peer review (reviewer: <codex gpt-5-codex | cursor-agent | ollama:mistral | claude-skeptic>)
- <cross-provider critique> — prism's take: agree/disagree because <reason>

### Summary
<counts by severity> · <N low-severity suppressed> · <validation status>
```

## Invoking the lenses

Each lens is a sibling skill in this plugin (`roast-with-docs`, `simplify`, `peer-review`,
`security-audit`). Invoke a lens by loading and following its `SKILL.md`, passing it the
**mode**, the **scope** (diff vs whole vs plan), and the **fix-behavior** decided above.
`security-audit` fans out to its own read-only subagents; the other lenses run in the main
context (or as a single subagent each when parallelizing analysis).

If you were reached via the `/prism` command, the command passes its argument as the mode;
treat a missing argument as "auto-detect" per Step 1.
