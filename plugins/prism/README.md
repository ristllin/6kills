# prism

A **mode-aware code orchestrator** for Claude Code. Prism refracts your code (or your plan)
through up to four independent lenses and recombines the results into one prioritized report —
but it only runs the lenses that fit the situation it detects.

## The four lenses

| Lens | What it does |
|------|--------------|
| 🔥 **roast-with-docs** | Witty, brutal-but-fair critique — every jab cited to a real doc or linter rule. |
| 🧹 **simplify** | Maintainability pass: guard clauses, low nesting, lower complexity, better names — behavior preserved. |
| 🧑‍⚖️ **peer-review** | Independent second opinion from a *different provider* (via `cursor-agent`), with graceful fallback. |
| 🛡️ **security-audit** | Fan-out subagents (one per threat class) → triage & re-verify → severity-ranked, root-cause fixes. |

Each lens is also usable on its own (`prism roast`, `prism simplify`, `prism peer`, `prism audit`).

## Modes (auto-detected)

Prism picks a mode from context — you rarely need to specify it:

| Mode | When | Lenses | Fixes |
|------|------|--------|-------|
| **plan** | plan mode is active | peer-review · security (design) · roast | read-only advice |
| **new** | empty / fresh repo | security (by-design) · peer-review · simplify (guidance) | guidance only |
| **pr** | pending git diff, or `prism pr` | all four, scoped to the diff | auto-fix → validate |
| **improve** | clean existing repo, bare `prism` | all four, whole codebase (confirms first) | auto-fix → validate |
| **audit** | `prism audit` | security-audit only | propose (apply in pr/improve) |

## Usage

```
prism            # auto-detect: reviews the diff, or offers a whole-codebase pass
prism pr         # review + harden only the pending changes, prep for PR
prism audit      # security audit only
prism roast      # just the roast
prism simplify   # just the maintainability pass
prism peer       # just the cross-provider second opinion
```

Or the slash command: `/prism [pr|audit|review|roast|simplify|peer|new|all]`.

## How it stays considerate

- **Read-only in plan mode** — never edits while you're still planning.
- **Confirms before whole-codebase sweeps** and before any credit-spending cross-provider call.
- **Scopes `pr` to the diff** — no drive-by refactors of untouched code.
- **Root-cause, blast-radius-aware fixes**, and it **validates** (tests/build) after every auto-fix.

## Peer review — cross-provider

`peer-review` routes an adversarial critique to a **different** AI provider so you get genuine
independence:

1. `cursor-agent -p` (GPT/Gemini via your Cursor account) — preferred.
2. `ollama` local model — offline fallback (flagged low-tier).
3. Fresh Claude skeptic subagent — ultimate fallback (flagged same-provider).

It reads the current model from Claude Code's runtime context (models can't introspect their own
id) and always tells you which reviewer actually ran.

## Layout

```
prism/
├── commands/prism.md              # /prism entry point
├── skills/
│   ├── prism/SKILL.md             # orchestrator (mode detection + routing)
│   ├── roast-with-docs/SKILL.md
│   ├── simplify/SKILL.md
│   ├── peer-review/SKILL.md
│   └── security-audit/
│       ├── SKILL.md
│       └── references/threat-lenses.md
└── agents/                        # read-only fan-out workers for security-audit
    ├── prism-sec-injection.md
    ├── prism-sec-authz.md
    ├── prism-sec-secrets-crypto.md
    ├── prism-sec-inputoutput.md
    ├── prism-sec-logic-deps.md
    └── prism-sec-triage.md
```
