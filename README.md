# 6kills

A public [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) **plugin marketplace**.

Four plugins:

| Plugin | What it is |
|--------|------------|
| 🔺 [**prism**](plugins/prism) | Mode-aware code orchestrator. Refracts code (or a plan) through five lenses: 🔥 roast-with-docs, 🧹 simplify, 🧑‍⚖️ peer-review, 🛡️ security-audit, 📚 docs-align. Auto-detects whether you're planning, starting fresh, improving an existing project, or preparing a PR, and runs the right lenses for that mode. |
| 🔎 [**deep-research**](plugins/deep-research) | Plans queries, fans out [Tavily](https://tavily.com) searches, extracts sources, and writes a cited report. Exposes `/research`. |
| 🏁 [**relentless**](plugins/relentless) | Operating charter for long, unattended build-and-ship tasks: pins a Definition of Done, works in an isolated git worktree, self-continues across context resets, fans work across parallel agents, guards every surface with a full test pyramid, runs autonomous end-to-end QA, hardens with a review pass, and stops only when the result is shippable. Exposes `/relentless`. |
| 📥 [**linkedin-triage**](plugins/linkedin-triage) | Auto-triage your unread LinkedIn DMs, sandboxed in a throwaway Docker container. Reads DMs through the [Beeper](https://beeper.com) Desktop app, categorizes each one, replies from templates you control, and leaves personal/strategic chats unread. The AI sees only the Beeper tools and your rules file. Exposes `/linkedin-triage`. |

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install prism@6kills
/plugin install deep-research@6kills
/plugin install relentless@6kills
/plugin install linkedin-triage@6kills
```

Or point at a local clone during development:

```
/plugin marketplace add /path/to/6kills
```

## prism: quick start

```
prism            # auto-detects mode: reviews the diff, or offers a whole-codebase pass
prism pr         # review + harden the pending changes only, prep for PR
prism audit      # security audit only (fan-out subagents → triage → severity-ranked report)
prism roast      # a cited, brutal-but-fair roast
prism simplify   # maintainability pass (guard clauses, low nesting, lower complexity)
prism peer       # independent second opinion from a different model family (auto-discovers installed AI CLIs)
prism docs       # align docs with the repo: fix stale claims, strip AI slop, check newcomer readiness
```

Prism is **considerate**: read-only in plan mode, confirms before whole-codebase sweeps and
before any credit-spending cross-provider call, scopes `pr` to the diff, and validates
(tests/build) after every auto-fix. See [plugins/prism](plugins/prism) for the full mode matrix.

## relentless: quick start

Point it at a big, autonomous, ship-it task and let it run:

```
relentless "build X end to end and don't stop until it's shippable"
/relentless                # uses the task already established in the conversation
```

It first pins a **Definition of Done** (acceptance criteria, surfaces in scope, quality bar,
out-of-scope), then works in an isolated git worktree, arms a self-continuing loop so
work resumes across context resets, builds in verified increments up a test pyramid,
guards every surface against regressions, runs autonomous end-to-end QA (real paid
API calls, browser plus screenshots, waiting on async flows, LLM-as-judge for answer
quality), hardens with a review pass (pairs well with prism), and stops when the
Definition of Done is met with evidence. Discipline is built in: no scope creep, no
faked-green tests, confirmation before anything hard to reverse or outward-facing, and it
cleans up its branches, worktrees, and loops when done.

## deep-research: requirements

deep-research uses the **Tavily MCP server** and needs a `TAVILY_API_KEY` in your environment
(the plugin's `.mcp.json` reads `${TAVILY_API_KEY}`). With that set:

```
/research "your topic"  [--breadth N] [--depth N] [--out path]
```

## linkedin-triage: quick start

Runs a sandboxed Docker container that triages your unread LinkedIn DMs via the Beeper Desktop
app. One-time setup (Docker + Beeper + `/mcp` auth + API access) is checked automatically; run
`/linkedin-triage` and it points you at anything missing. Auth works two ways: a direct
`ANTHROPIC_API_KEY`, or a shared Foundry/gateway proxy (`CLAUDE_CODE_USE_FOUNDRY=1` +
`ANTHROPIC_FOUNDRY_BASE_URL`). Customize your reply templates in
`plugins/linkedin-triage/sandbox/memory/linkedin_triage_rules.md` before the first run. Full guide:
[plugins/linkedin-triage/sandbox/SETUP.md](plugins/linkedin-triage/sandbox/SETUP.md).

```
/linkedin-triage
```

## Repo layout

```
6kills/
├── .claude-plugin/marketplace.json   # marketplace manifest (lists all four plugins)
└── plugins/
    ├── prism/                        # orchestrator command + skill, 5 lens skills, 7 sec agents
    ├── deep-research/                # /research command + deep-researcher agent + Tavily MCP
    ├── relentless/                   # /relentless command + relentless charter skill
    └── linkedin-triage/              # /linkedin-triage command + Docker sandbox (Beeper DM triage)
```

## Authoring notes

Each plugin has its own `.claude-plugin/plugin.json`. Skills live under `plugins/<plugin>/skills/
<name>/SKILL.md`; commands under `commands/`; subagents under `agents/`. Skill descriptions are
what Claude matches against to decide when to trigger, so keep them specific and
trigger-phrase-rich.

## License

[MIT](LICENSE)
