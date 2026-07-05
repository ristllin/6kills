---
name: simplify
description: >-
  Simplify code for maintainability and prepare it for a PR — flatten nesting with guard
  clauses/early returns, lower cyclomatic complexity, shorten functions, improve names,
  remove duplication and nested ternaries — all while preserving behavior exactly. Use when
  the user says "simplify", "prism simplify", "clean this up", "prep for PR", or wants a
  maintainability refactor of recently changed or existing code. Grounded in canonical code-
  review references (Google eng-practices, Sandi Metz rules, guard-clause refactoring).
---

# Simplify

Make code easier to read, change, and review — **without changing what it does.** This lens
is quality-only: it does not hunt for bugs (that's `security-audit`) and it never alters
observable behavior.

## What "simpler" means here (grounded checklist)

- **Low nesting.** Replace nested conditionals with **guard clauses / early returns**. Aim for
  ≤ 2 levels of indentation in a function.
  (refactoring.guru — Replace Nested Conditional with Guard Clauses)
- **Low complexity.** Target cyclomatic complexity ≤ 10 per function; split or extract when
  above. Each `if`/`for`/`while`/`case`/`&&`/`||` adds a path — count them.
- **Short, single-purpose functions.** A function that does three things becomes three
  well-named functions. (Sandi Metz: small methods, intention-revealing names.)
- **Intention-revealing names.** `prepareFeedForPublishing()`, not `step2()`. No abbreviations
  that need a decoder ring.
- **No duplication.** Extract repeated logic; DRY, but not at the cost of a bad abstraction.
- **No nested ternaries**, no clever one-liners that trade clarity for brevity. Prefer clarity.
- **Remove noise.** Delete obvious/redundant comments, dead code, commented-out blocks.
- **Match the codebase.** Follow existing conventions (module system, error handling, naming,
  formatting) — read neighboring files first. Simpler ≠ *your* style; it means *consistent*.

## Balance (don't over-simplify)

Keep helpful abstractions, meaningful names, and necessary edge-case handling. Fewer lines is
not the goal — **lower cognitive load** is. If a "simplification" makes the code harder to
follow or loses an edge case, don't do it.

## Process

1. **Scope.** `pr` → only changed code (`git diff`). `improve` → whole codebase, file by file.
   `new`/`plan` → offer conventions/guidance rather than edits. Read the commit message / PR
   description first to understand *intent* before touching anything.
2. **Analyze** each target: nesting depth, complexity, function length, naming, duplication.
   Before refactoring a function, pull in its **callers/usages** — the same "precise +
   complete context" rule the security lens uses; a refactor is only safe against the code
   that actually depends on it.
3. **Refactor** one concern at a time, smallest correct change first.
4. **Preserve behavior** — reason through inputs/outputs and edge cases before/after; do not
   change signatures used elsewhere without checking callers.
5. **Validate — externally, never by self-certification.** Run the project's tests / typecheck
   / build after the pass; those are the arbiter of "behavior preserved," not your own
   reasoning. (Models silently endorse ~32% of their own behavior-breaking refactors even when
   they can name the pitfall.) If a change touches a path with thin or no test coverage, **say
   so explicitly** in the report rather than asserting behavior is preserved. If anything
   fails, revert that change and report it.
6. **Prep for PR.** Summarize what changed and why; suggest a Conventional-Commits message
   (e.g. `refactor(auth): flatten token-validation with guard clauses`).

## Output

```
## 🧹 Simplify — <scope>

- `auth/token.ts:20-58` — 4-level nesting → guard clauses; extracted `assertNotExpired()`.
  Complexity 14 → 6. Behavior unchanged. ✓ tests pass
- `utils/parse.js:10` — nested ternary → early returns for readability.

Suggested commit: refactor(auth): flatten token validation, extract expiry guard
```

## References
- Google Engineering Practices — Code Review: google.github.io/eng-practices/review/
- Sandi Metz's rules: thoughtbot.com/blog/sandi-metz-rules-for-developers
- Guard clauses: refactoring.guru/replace-nested-conditional-with-guard-clauses
- Cyclomatic complexity thresholds: blog.codacy.com/cyclomatic-complexity
