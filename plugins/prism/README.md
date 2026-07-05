# prism

A **mode-aware code orchestrator** for Claude Code. Prism refracts your code (or your plan)
through up to four independent lenses and recombines the results into one prioritized report —
but it only runs the lenses that fit the situation it detects.

## The four lenses

| Lens | What it does |
|------|--------------|
| 🔥 **roast-with-docs** | Witty, brutal-but-fair critique — every jab cited to a real doc or linter rule. |
| 🧹 **simplify** | Maintainability pass: guard clauses, low nesting, lower complexity, better names — behavior preserved. |
| 🧑‍⚖️ **peer-review** | Independent second opinion from a *different model family* — discovers whatever headless AI CLI/endpoint is available at runtime, with graceful fallback. |
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

## Peer review — provider-agnostic

`peer-review` routes an adversarial critique to a **different model family** so you get genuine
independence — LLM judges measurably favor their own family, so a different lineage is the
mitigation. It is vendor-neutral: no single product is required. Selection is layered:

1. **Your override wins** — set `PRISM_PEER_REVIEWER` to a command template (e.g.
   `PRISM_PEER_REVIEWER='llm -m gemini-2.5-pro'`) or name a reviewer in CLAUDE.md.
2. **Otherwise it probes** whatever headless AI CLI/endpoint is installed and authenticated —
   `codex exec`, `gemini -p`, `opencode run`, `qwen -p`, `llm -m`, `goose run`, `aider`, or any
   OpenAI-compatible endpoint. The list is examples, not an allow-list; anything that runs a
   one-shot read-only prompt qualifies. A pure completion tool like `llm` is a first-class
   judge (a critique needs reasoning, not agentic tool use).
3. **Fallbacks:** a local `ollama` model (flagged low-tier), then a fresh Claude skeptic
   subagent (flagged same-provider).

If two or more different-family backends are available, it can run an **opt-in jury** (2–3
judges reconciled together — panels beat a single judge on bias and cost), announcing the extra
cost first. It reads the current model from Claude Code's runtime context (models can't
introspect their own id) and always tells you which reviewer actually ran.

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
    ├── prism-sec-logic.md
    ├── prism-sec-supplychain-config.md
    └── prism-sec-triage.md
```
