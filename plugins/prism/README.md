# prism

A **mode-aware code orchestrator** for Claude Code. Prism refracts your code (or your plan)
through up to five independent lenses and recombines the results into one prioritized report.
It runs the lenses that fit the situation it detects.

## The five lenses

| Lens | What it does |
|------|--------------|
| 🔥 **roast-with-docs** | Witty, brutal-but-fair critique. Every jab cited to a real doc or linter rule. |
| 🧹 **simplify** | Maintainability pass: guard clauses, low nesting, lower complexity, better names. Behavior preserved. |
| 🧑‍⚖️ **peer-review** | Independent second opinion from a different model family. Discovers whatever headless AI CLI/endpoint is available at runtime, with graceful fallback. |
| 🛡️ **security-audit** | Fan-out subagents (one per threat class), then triage and re-verify, then severity-ranked, root-cause fixes. Conditional memory-safety and LLM-app lenses join when the stack calls for them. |
| 📚 **docs-align** | Brings documentation in line with the actual repo state: fixes or deletes stale claims, strips AI-slop style, checks docs work for newcomers, relocates misplaced content. |

Each lens is also usable on its own (`prism roast`, `prism simplify`, `prism peer`,
`prism audit`, `prism docs`).

## Modes (auto-detected)

Prism picks a mode from context; you rarely need to specify it:

| Mode | When | Lenses | Fixes |
|------|------|--------|-------|
| **plan** | plan mode is active | peer-review · security (design) · roast · docs (advisory) | read-only advice |
| **new** | empty / fresh repo | security (by-design) · peer-review · simplify (guidance) · docs (conventions) | guidance only |
| **pr** | pending git diff, or `prism pr` | all five, scoped to the diff, docs last | auto-fix → validate |
| **improve** | clean existing repo, bare `prism` | all five, whole codebase (confirms first), docs last | auto-fix → validate |
| **audit** | `prism audit` | security-audit only | propose (apply in pr/improve) |

`docs-align` always runs last in fix modes, so docs describe the final state of the code
after every other fix has landed.

## Usage

```
prism            # auto-detect: reviews the diff, or offers a whole-codebase pass
prism pr         # review + harden only the pending changes, prep for PR
prism audit      # security audit only
prism roast      # just the roast
prism simplify   # just the maintainability pass
prism peer       # just the cross-provider second opinion
prism docs       # just the docs alignment pass
```

Or the slash command: `/prism [pr|improve|audit|review|roast|simplify|peer|docs|new|all]`
(`review` is an alias of `pr`; `all` runs every lens at the detected scope with that mode's
gates).

## How it stays considerate

- Read-only in plan mode. It never edits while you're still planning.
- Confirms before whole-codebase sweeps and before any credit-spending cross-provider call.
- Scopes `pr` to the diff. No drive-by refactors of untouched code. Docs whose specific claims
  the diff invalidates count as blast radius; a repo-wide docs sweep needs explicit opt-in.
- Root-cause, blast-radius-aware fixes, validated (tests/build) after every auto-fix.

## Peer review: provider-agnostic

`peer-review` routes an adversarial critique to a **different model family** for genuine
independence. LLM judges measurably favor their own family, so a different lineage is the
mitigation. It is vendor-neutral: no single product is required. Selection is layered:

1. **Your override wins.** Set `PRISM_PEER_REVIEWER` to a command template (for example
   `PRISM_PEER_REVIEWER='llm -m gemini-2.5-pro'`) or name a reviewer in CLAUDE.md.
2. **Otherwise it probes** whatever headless AI CLI/endpoint is installed and authenticated:
   `codex exec`, `gemini -p`, `opencode run`, `qwen -p`, `llm -m`, `goose run`, `aider`, or
   any OpenAI-compatible endpoint. The list is examples; anything that runs a one-shot,
   read-only prompt qualifies. A pure completion tool like `llm` is a first-class judge (a
   critique needs reasoning, and agentic tool use adds nothing to it).
3. **Fallbacks:** a local `ollama` model (flagged low-tier), then a fresh Claude skeptic
   subagent (flagged same-provider).

If two or more different-family backends are available, it can run an **opt-in jury** (2-3
judges reconciled together; panels beat a single judge on bias and cost), announcing the
extra cost first. It reads the current model from Claude Code's runtime context (models can't
introspect their own id) and always tells you which reviewer actually ran.

## Docs align: what it enforces

- Accuracy first. Every documented command, flag, path, default, count, and version is
  verified against the repo. Stale claims get fixed or deleted. Wrong docs are worse than
  missing docs.
- No AI slop. No em dashes, no "it's not just X, it's Y" framing, no hype vocabulary, no
  filler intros or conclusions. The full deny-list lives in
  `skills/docs-align/references/style-rules.md`.
- Newcomer-ready. Purpose in the first screen, prerequisites before first use, first
  command runs from a fresh clone, no term used before it's defined.
- Right content, right place. Session narration, personal info, and decision history stay
  out of committed docs. Agent instructions go to AGENTS.md, decisions to ADRs (architecture
  decision records), plans to gitignored files or the roadmap. Committed agent plan files get
  flagged for removal.

## Layout

```
prism/
├── commands/prism.md              # /prism entry point
├── skills/
│   ├── prism/SKILL.md             # orchestrator (mode detection + routing)
│   ├── roast-with-docs/SKILL.md
│   ├── simplify/SKILL.md
│   ├── peer-review/SKILL.md
│   ├── docs-align/
│   │   ├── SKILL.md
│   │   └── references/            # style deny-list + placement policy
│   └── security-audit/
│       ├── SKILL.md
│       └── references/threat-lenses.md
└── agents/                        # read-only subagents for security-audit (6 lens workers + triage)
    ├── prism-sec-injection.md
    ├── prism-sec-authz.md
    ├── prism-sec-secrets-crypto.md
    ├── prism-sec-inputoutput.md
    ├── prism-sec-logic.md
    ├── prism-sec-supplychain-config.md
    └── prism-sec-triage.md
```
