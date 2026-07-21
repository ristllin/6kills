---
name: prism
description: >-
  Mode-aware code orchestrator that refracts code through five lenses: roast-with-docs,
  simplify, peer-review, a fan-out security-audit, and docs-align. Use this whenever the user
  says "prism", "prism this", "prism pr", "prism review", "prism audit", "prism roast",
  "prism simplify", "prism peer", "prism docs", or "prism new", OR asks to
  review/improve/harden code, prepare a change for a PR, get a second opinion on a plan or
  diff, or bring documentation in line with the code. Prism AUTO-DETECTS its mode from
  context (plan mode active, empty/new repo, clean existing repo, or a pending diff) and runs
  the right lenses for that mode. It is considerate: read-only in plan mode, confirms before
  large sweeps or credit-spending cross-provider calls, and validates after every auto-fix.
---

# Prism

Prism refracts a body of code (or a plan) through up to five independent **lenses**, then
recombines their findings into one prioritized report. The core job: **run the right lenses,
at the right scope, with the right fix-behavior, for the situation it detects.**

The five lenses are separate skills you invoke as sub-steps:

| Lens | Skill | What it does |
|------|-------|--------------|
| 🔥 Roast | `roast-with-docs` | Witty but technically defensible critique, every jab cited to an authoritative doc or linter rule. |
| 🧹 Simplify | `simplify` | Maintainability pass (low nesting, guard clauses, lower complexity, better names) with behavior preserved. |
| 🧑‍⚖️ Peer review | `peer-review` | Independent second opinion from a different model family. Discovers whatever AI CLI/endpoint is available at runtime, with graceful fallback. |
| 🛡️ Security | `security-audit` | Fan-out subagents, one per threat lens; triage and validate; severity-ranked, root-cause fixes. |
| 📚 Docs align | `docs-align` | Aligns docs with the actual repo state: fixes or deletes stale claims, strips AI-slop style, checks newcomer readiness, relocates misplaced content. |

## Step 1: Detect the mode (in this order)

Do not ask the user which mode to use unless detection is genuinely ambiguous. Detect it.

1. **Plan mode active?** If the harness is in plan mode (you can only take read-only actions
   and edit the plan file), you are in **`plan`** mode. This overrides everything below.
2. **Explicit argument?** If the user wrote `prism <word>`, honor it:
   `pr`, `improve`, `audit`, `review` (alias of `pr`), `roast`, `simplify`, `peer`, `docs`,
   `new`, `all`.
3. **Otherwise infer from git state.** Run:
   ```bash
   git rev-parse --is-inside-work-tree 2>/dev/null
   git status --porcelain
   git diff --stat; git diff --staged --stat
   git log --oneline -1 2>/dev/null
   ```
   Also read the **textual context** before running any lens: the commit message(s), PR
   description, and any linked issue. Intent context measurably beats extra code context; it
   is the cheapest precision win available (ContextCRBench). On a large diff (over ~150
   changed lines) precision collapses if you review it all at once; review
   chunk-by-logical-change instead.

   - **Pending changes** (working tree, staged, or unpushed commits vs the base branch) → **`pr`** mode, scoped to the diff.
   - **Clean tree in a non-empty existing codebase** → **`improve`** mode (whole codebase). Confirm intent first.
   - **Empty / near-empty repo** (no source files, or only scaffolding) → **`new`** mode.
   - **Not a git repo / no code in context** → ask what to point prism at.

## Step 2: Run the lenses for that mode

| Mode | Scope | Lenses (in order) | Fix behavior |
|------|-------|-------------------|--------------|
| **plan** | the proposed plan / approach in context | `peer-review` → `security-audit` (design-level, advisory) → `roast-with-docs` (of the approach) → `docs-align` (advisory: which docs the plan will touch or invalidate) | **Read-only.** No `simplify` (nothing built yet). Never edit files. |
| **new** | intended architecture & approach | `security-audit` (secure-by-design checklist) → `peer-review` (of the approach) → `simplify` (as forward guidance/conventions) → `docs-align` (set up README, AGENTS.md, and gitignore conventions from day one) | Guidance + scaffolding only; minimal edits, ask before writing. |
| **pr** | `git diff` only (working + staged + commits vs base) | `simplify` → `security-audit` → `roast-with-docs` → `peer-review` → `docs-align` **last** | Auto-fix, **then validate** (run tests/build). |
| **improve** | whole codebase | `security-audit` → `simplify` → `roast-with-docs` → `peer-review` → `docs-align` **last** | Confirm intent → auto-fix → validate. |
| **audit** | diff or whole (by context) | `security-audit` only | Propose fixes; apply + validate only if already in pr/improve. |
| **single** (`roast`/`simplify`/`peer`/`docs`) | current context | just that one lens | Per that lens's own default. |

`review` is an alias of `pr`. `all` runs every lens (docs-align still last) at the
auto-detected scope with that mode's fix behavior and confirmation gates; on a clean repo
that means `improve`, including its confirmation.

`docs-align` runs **last** in fix modes on purpose: it aligns documentation to the final
state of the code, after every other lens's fixes have landed. Running it earlier documents
a state that the later fixes then invalidate. For the same reason it is excluded from the
parallel analysis fan-out: in fix modes its entire pass, analysis included, runs only after
the other lenses' fixes are applied and validated.

When multiple lenses run, prefer to run the **read-only analysis lenses in parallel**
(spawn them as concurrent subagents, docs-align excepted per the rule above), then apply
fixes sequentially (simplify before security fixes, re-validating between) so edits never
race each other. The agent that wrote a
fix never signs off on it: validation is the project's tests/build, or a different lens/agent
(models silently endorse their own behavior-breaking changes; use an external check).

## Step 3: Be considerate (non-negotiable rules)

- **Plan mode = read-only.** Detect it and never attempt an edit, even if a lens suggests one.
  Output advice; the user applies it later.
- **Validate before improving on a clean repo.** Before `improve` mode touches a whole
  codebase, confirm: *"No pending changes detected. Run prism across the entire codebase to
  review and improve it? This may take a while."* Only proceed on yes.
- **Announce credit-spending / external calls.** `peer-review` may invoke an external AI CLI
  or API (spends the user's credits) or a local model. Say so first, name the extra cost for
  jury mode, and let the user skip.
- **Scope `pr` to the diff.** In `pr` mode, only reason about and modify lines within the
  diff (and their immediate blast radius). Do not opportunistically refactor untouched code.
  Exception: `docs-align` may fix docs whose specific claims the diff invalidates, found by
  searching the docs for mentions of the changed behavior; a repo-wide docs sweep in `pr`
  mode requires explicit user opt-in.
- **Fixes are root-cause and blast-radius-aware.** Before applying any fix, check callers and
  dependents so the fix doesn't break something else. Prefer the smallest correct change.
- **Validate after every auto-fix sweep.** Run the project's tests / build / typecheck. If a
  fix breaks them, revert that fix and report it rather than leaving the tree broken.

## Step 4: Recombine into one report

After the lenses run, merge their outputs into a single prioritized report. Use the shared
severity vocabulary so findings from different lenses stack rank together:

- **Confidence** 0-100 on security-audit findings; only surface >= 80 (drop likely false
  positives). Roast, simplify, and docs-align findings are gated by their own lens rules:
  citation verified, behavior preserved, claim re-verified against the tree.
- **Severity**: `Critical` / `High` / `Medium` / `Low`. Default reporting threshold is
  `Medium` and up (security-audit); mention how many low-severity items were suppressed.
- Each finding: `file:line`, what and why, severity, suggested or applied fix.

Report shape:

```
## Prism report: <mode> mode (<scope>)
Lenses run: 🧹 simplify · 🛡️ security · 🔥 roast · 🧑‍⚖️ peer · 📚 docs

### 🛡️ Security (Critical/High first)
- [High] path/to/file.py:42: <finding> · Fix: <root-cause fix, blast radius noted>

### 🧹 Simplify
- path/to/file.ts:88: nested 4 deep; applied guard clauses (behavior unchanged) ✓ tests pass

### 🔥 Roast
- api/handler.js:12: "<cited jab>" per <official doc/rule link>

### 🧑‍⚖️ Peer review (reviewer: <CLI/endpoint → model, detected at runtime>)
- <cross-family critique> · prism's take: agree/disagree because <reason>

### 📚 Docs align
- README.md:34: documented flag renamed in this diff; fixed and re-verified · 6 slop edits

### Summary
<counts by severity> · <N low-severity suppressed> · <validation status>
```

## Invoking the lenses

Each lens is a sibling skill in this plugin (`roast-with-docs`, `simplify`, `peer-review`,
`security-audit`, `docs-align`). Invoke a lens by loading and following its `SKILL.md`,
passing it the **mode**, the **scope** (diff vs whole vs plan), and the **fix-behavior**
decided above. `security-audit` fans out to its own read-only subagents; the other lenses run
in the main context (or as a single subagent each when parallelizing analysis).

If you were reached via the `/prism` command, the command passes its argument as the mode;
treat a missing argument as "auto-detect" per Step 1.
