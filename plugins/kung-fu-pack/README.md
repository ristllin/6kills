# 🥋 kung-fu-pack

**Turn a target into a tight, diagram-rich briefing page, sourced from everything you can reach.**

Point it at a target (a system, a codebase, an account, a set of engagements, a person, a topic) with
a scope and some links. It fans out parallel exploration across every source you have (Notion, Linear,
local code, the web), caches the raw findings in a local workspace, pulls live data and flags
staleness, consolidates into a planned structure, generates real architecture diagrams, and publishes
a styled page to Notion, a self-contained HTML file, local Markdown, or a local preview server.

The craft is three things, and they are where packs usually fail:

- **Reach every source and pull live truth.** The pack is only as good as what you actually reached;
  gaps are disclosed, never faked.
- **Cache the raw findings.** One file per source in a per-target workspace, so every claim is
  auditable and the next refresh is cheap.
- **Compress to high signal with a lead behind every claim.** file:line, a Notion/Linear ID, or a
  URL, so the reader can verify and dig. Corrections to the old mental model are the gold.

It never uses em dashes, and it will not overwrite an existing page or publish to a named destination
without confirming.

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install kung-fu-pack@6kills
```

## Setup (once)

```
/kung-fu-pack-init
```

Detects which sources you can reach (Notion, Linear, Tavily, Beeper) and which render tools you have
(node, Chrome, python3), interviews you for your defaults (default output, Notion destination, enabled
sources, code roots, depth, house rules), then saves `~/kung-fu-pack/config.json` and scaffolds the
workspace. The default output is inferred: Notion if its MCP is connected, otherwise self-contained
HTML. Re-run anytime to change defaults.

## Usage

```
kung-fu-pack                                   # build a pack on the target in context
/kung-fu-pack "Crucible platform - onboarding brief for a new eng manager; include arch + Linear"
/kung-fu-pack "<target>" --output=html --depth=deep
/kung-fu-pack "<target>" --output=notion --dest=https://notion.so/<page-id>
```

Flags override the saved defaults: `--output=<notion|html|md|server>`, `--dest=<notion-url-or-id|draft>`,
`--depth=<standard|deep>`, `--audience=<who>`, `--model=<id>`. With no arguments it uses the target
already in the conversation; with none, it asks and stops.

## The seven steps

| Step | What happens |
|---|---|
| 1. Scope | Fix the target, audience, angle, must-cover points, and output. Ask a focused batch if thin. |
| 2. Capability check | Confirm which enabled sources resolve right now; state the mode; degrade on gaps. |
| 3. Fan out | Parallel exploration agents, one per source/subtopic, each caching findings to `research/`. Pull live data, flag staleness. |
| 4. Consolidate + plan | Reconcile conflicts, surface insights and corrections, write `plan.md`; confirm structure for big pages. |
| 5. Diagrams | Author the 1 to 3 information-carrying diagrams, render to PNG (headless Chrome), eyeball each. |
| 6. Publish | Notion (upload PNGs, draft unless a destination is named), HTML, Markdown, or local server. |
| 7. Verify | Re-open the result, confirm diagrams and structure, grep for dashes (zero), spot-check claims, report with leads. |

## Workspace

Each target gets a cached folder so nothing lives only in chat:

```
~/kung-fu-pack/packs/<slug>/
  research/   one findings file per source (raw + SOURCES)
  assets/     diagram gen.js + .html + rendered .png
  out/        local page.md / page.html when not publishing to Notion
  plan.md     the planned page structure
```

## Requirements

- **Diagrams:** `node` + a Chrome/Chromium binary (for PNG render). Without Chrome, diagrams still
  generate as HTML and inline into the HTML output.
- **Notion output:** the Notion MCP connected. **Live tracker data:** the Linear MCP. **Web research:**
  the Tavily MCP or built-in web search. All optional; the skill degrades to whatever you have.
- **Local preview server:** `python3` (or node).

Nothing secret is stored in the config; MCP auth and API keys stay in the environment / MCP layer.
