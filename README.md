# 6kills

A public [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) **plugin marketplace**.

Two plugins:

| Plugin | What it is |
|--------|------------|
| 🔺 [**prism**](plugins/prism) | Mode-aware code orchestrator. Refracts code (or a plan) through four lenses — 🔥 roast-with-docs, 🧹 simplify, 🧑‍⚖️ peer-review, 🛡️ security-audit — auto-detecting whether you're planning, starting fresh, improving an existing project, or preparing a PR, and reusing the right lenses accordingly. |
| 🔎 [**deep-research**](plugins/deep-research) | Plans queries, fans out [Tavily](https://tavily.com) searches, extracts sources, and writes a cited report. Exposes `/research`. |

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install prism@6kills
/plugin install deep-research@6kills
```

Or point at a local clone during development:

```
/plugin marketplace add /path/to/6kills
```

## prism — quick start

```
prism            # auto-detects mode: reviews the diff, or offers a whole-codebase pass
prism pr         # review + harden the pending changes only, prep for PR
prism audit      # security audit only (fan-out subagents → triage → severity-ranked report)
prism roast      # a cited, brutal-but-fair roast
prism simplify   # maintainability pass (guard clauses, low nesting, lower complexity)
prism peer       # independent second opinion from a different provider (codex/cursor-agent/...)
```

Prism is **considerate**: read-only in plan mode, confirms before whole-codebase sweeps and
before any credit-spending cross-provider call, scopes `pr` to the diff, and validates
(tests/build) after every auto-fix. See [plugins/prism](plugins/prism) for the full mode matrix.

## deep-research — requirements

deep-research uses the **Tavily MCP server** and needs a `TAVILY_API_KEY` in your environment
(the plugin's `.mcp.json` reads `${TAVILY_API_KEY}`). With that set:

```
/research "your topic"  [--breadth N] [--depth N] [--out path]
```

## Repo layout

```
6kills/
├── .claude-plugin/marketplace.json   # marketplace manifest (lists both plugins)
└── plugins/
    ├── prism/                        # orchestrator command + skill, 4 lens skills, 6 sec agents
    └── deep-research/                # /research command + deep-researcher agent + Tavily MCP
```

## Authoring notes

Each plugin has its own `.claude-plugin/plugin.json`. Skills live under `plugins/<plugin>/skills/
<name>/SKILL.md`; commands under `commands/`; subagents under `agents/`. Skill descriptions are
what Claude matches against to decide when to trigger — keep them specific and trigger-phrase-rich.

## License

[MIT](LICENSE)
