---
description: "One-time onboarding for kung-fu-pack: detects which sources you can reach (Notion, Linear, web, code), interviews you about defaults, then saves your config and builds the local workspace"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion", "ToolSearch"]
---

You are running the **first-time onboarding** for the kung-fu-pack plugin. Your job is to detect
what the user can reach, interview them for their defaults, then write their config and scaffold
the local workspace. The briefing runs later via `/kung-fu-pack`; this command only sets things up.

Be warm, concise, concrete. The user can say "use a sensible default" to anything. **Never use em
dashes** in anything you write (chat, config, files). Use hyphens or rephrase.

---

## 1. Detect capabilities (do this before asking)

Deduce what the user has access to, so the defaults are inferred, not guessed:

- **MCP sources.** Run `ToolSearch` for each of: `notion`, `linear`, `tavily`, `beeper`. A match
  means that source is probably connected. Note which resolved. (Notion present -> Notion is the
  natural default output; Tavily present -> web research is available; Linear present -> live
  project/issue data; Beeper present -> message history.)
- **Render toolchain.** Run `bash "${CLAUDE_PLUGIN_ROOT}/skills/kung-fu-pack/setup.sh"` and read its
  checklist (node for diagrams, a Chrome/Chromium binary for PNG rendering, python3 for the local
  preview server). Relay anything missing with its one-line install hint; diagrams and the HTML/MD
  outputs still work without every piece, so degrade gracefully.

Tell the user, in two or three sentences, what you detected and that you will now ask a few setup
questions.

## 2. Interview (small batches, use AskUserQuestion for the discrete choices)

**A. Default output destination.** Pre-select based on detection: if Notion MCP resolved, recommend
**Notion page**; otherwise recommend **self-contained HTML**. Offer all four and record the pick:
  - Notion page (uploads PNG diagrams, styled page) - needs Notion MCP.
  - Self-contained HTML (one portable file, diagrams inlined) - no MCP needed.
  - Local Markdown (.md + assets/ folder) - zero dependencies.
  - Local preview server (renders the pack and serves it at localhost) - needs python3 or node.
  Note that `/kung-fu-pack` can still override per run with `--output=`.

**B. Notion destination (only if Notion is the default or an option).** Where should pages land:
  a named parent page/database (ask them to paste a Notion URL or ID), or **draft** (private
  workspace-level, movable later). Default to draft if they are unsure.

**C. Sources to enable by default** (AskUserQuestion, multiSelect). Pre-check the ones that
  resolved in step 1: Notion, Linear, local code repositories, web search (Tavily/WebSearch),
  Beeper messages. For "local code repositories", ask for one or more root paths to search by
  default (e.g. `~/projects`), or leave blank to decide per run.

**D. Workspace root.** Where the cached per-target workspaces live. Default `~/kung-fu-pack`
  (each target gets `packs/<slug>/` with `research/`, `assets/`, `out/`, `plan.md`). Accept an
  override.

**E. Depth + model.** Default depth "standard" (a handful of parallel explorers); offer "deep"
  (larger fan-out, adversarial cross-check) for audits. Model: default to inheriting the session
  model; let them pin one if they want.

**F. House rules.** Confirm the defaults: no em dashes anywhere; every claim carries a lead
  (file:line, Notion/Linear ID, URL); flag staleness of any cached or snapshot data; confirm
  before overwriting an existing page. These are on by default; let them add their own (tone,
  banned words, a signature, a default audience like "new engineering manager").

## 3. Write the config and scaffold the workspace

Expand `~` to `$HOME`. Create the workspace root and its `packs/` dir. Write
`<workspace-root>/config.json` (pretty-printed JSON), for example:

```json
{
  "version": 1,
  "output_default": "notion",
  "notion_destination": "draft",
  "workspace_root": "~/kung-fu-pack",
  "sources": { "notion": true, "linear": true, "code": true, "web": false, "beeper": false },
  "code_roots": ["~/projects"],
  "depth": "standard",
  "model": "inherit",
  "house_rules": {
    "no_em_dashes": true,
    "every_claim_has_a_lead": true,
    "flag_staleness": true,
    "confirm_before_overwrite": true,
    "default_audience": "",
    "extra": []
  }
}
```

Only include keys for sources that exist; set unreachable ones to `false` with a short note. Do not
store any secret in this file (MCP auth and API keys live in the environment / MCP layer, never here).

## 4. Finish

- Re-run `bash "${CLAUDE_PLUGIN_ROOT}/skills/kung-fu-pack/setup.sh"` and show the final checklist.
- Print a short summary: detected sources, chosen default output, workspace path, config path.
- Tell them they can re-run `/kung-fu-pack-init` anytime to change defaults, or hand-edit
  `config.json`. Then point them at `/kung-fu-pack "<target> <scope/links>"` for the first real run.
