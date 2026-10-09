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

**Claude Code** (plugin marketplace):

```
/plugin marketplace add ristllin/6kills
/plugin install kung-fu-pack@6kills
```

**Mistral Vibe / OpenAI Codex.** They do not use the Claude plugin marketplace, but they read the
same Agent Skills `SKILL.md` format, so the portable skill installs with one script:

```
bash plugins/kung-fu-pack/install.sh vibe     # -> ~/.vibe/skills/kung-fu-pack
bash plugins/kung-fu-pack/install.sh codex    # -> ~/.codex/skills/kung-fu-pack  (+ agents/openai.yaml)
bash plugins/kung-fu-pack/install.sh all      # every harness detected on this machine
bash plugins/kung-fu-pack/install.sh vibe --link      # symlink so it tracks this checkout
bash plugins/kung-fu-pack/install.sh codex --uninstall
```

Then invoke it as `/kung-fu-pack` (Vibe) or by name / `$kung-fu-pack` (Codex). The first run writes
`~/kung-fu-pack/config.json` after a short setup interview (there is no `-init` command outside
Claude Code; the skill self-initializes). The method is identical on all three; only a few mechanics
differ (how MCP servers are detected, how it fans out, how it asks you) and the skill's "Harness
notes" section maps them. Notion/Linear/web all work on any harness that has the matching MCP server
connected.

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
/kung-fu-pack "our payments platform - onboarding brief for a new eng manager; include arch + tracker"
/kung-fu-pack "<target>" --output=html --depth=deep
/kung-fu-pack "<target>" --output=notion --dest=https://notion.so/<page-id>
```

Flags override the saved defaults: `--output=<notion|html|md|server>`, `--dest=<notion-url-or-id|draft>`,
`--depth=<standard|deep>`, `--audience=<who>`, `--style=<default|asd-ste100>`, `--model=<id>`. With no
arguments it uses the target already in the conversation; with none, it asks and stops.

### Writing standard

`--style` (or `writing_standard` in config) picks the prose rules: `default` (dense, technical,
peer-level) or **`asd-ste100`** (ASD-STE100 Simplified Technical English: short single-idea sentences,
active voice, one term per concept, no "-ing" verbs, vertical lists; good for global/non-native readers
or procedural docs). See `skills/kung-fu-pack/references/asd-ste100.md`. The page structure is the same
either way; only the sentence-level prose changes. STE mode approximates the writing rules and lints
them; strict certification needs a licensed STE checker.

## The seven steps

| Step | What happens |
|---|---|
| 1. Scope | Fix the target, audience, angle, must-cover points, and output. If thin, ask one batch of general, parameter-shaped questions (never guessed names). |
| 2. Capability check | Confirm which enabled sources resolve right now; state the mode; degrade on gaps. |
| 3. Fan out | Parallel exploration agents, one per source/subtopic, each caching findings to `research/`. Pull live data, flag staleness. |
| 4. Consolidate + plan | Reconcile conflicts, surface insights and corrections, write `plan.md`. Keep one tight 1 to 3 page brief when it fits; nest into an index plus linked sub-pages when breadth would force a monolith. |
| 5. Diagrams | Author the 1 to 3 information-carrying diagrams, render to PNG (headless Chrome), eyeball each. |
| 6. Publish | Notion (upload PNGs, draft unless a destination is named), HTML, Markdown, or local server. Nested packs publish as a tree: Notion sub-pages, a wiki-like HTML set, or linked Markdown files. |
| 7. Verify | Re-open the result, confirm diagrams and structure, grep for dashes (zero), spot-check claims, report with leads. |

## Workspace

Each target gets a cached folder so nothing lives only in chat:

```
~/kung-fu-pack/packs/<slug>/
  research/   one findings file per source (raw + SOURCES)
  assets/     diagram gen.js + .html + rendered .png
  out/        local page.md / page.html, or index.md + <section>.md when nested
  plan.md     the planned page structure
```

## Requirements

- **Diagrams:** `node` + a Chrome/Chromium binary (for PNG render). Without Chrome, diagrams still
  generate as HTML and inline into the HTML output.
- **Notion output:** the Notion MCP connected. **Live tracker data:** the Linear MCP. **Web research:**
  the Tavily MCP or built-in web search. All optional; the skill degrades to whatever you have.
- **Local preview server:** `python3` (or node).

Nothing secret is stored in the config; MCP auth and API keys stay in the environment / MCP layer.

## Benchmark

`bench/` holds a synthesis benchmark for hill-climbing the skill text: frozen post-cutoff corpora
(hundreds of arXiv abstracts, dozens of release notes, a distributed-evidence set), full-corpus gold
nuggets and integration facts, a two-model judge panel, and floors for length, dashes, and evasion.
See [`bench/README.md`](bench/README.md) and the results in
[`bench/HILLCLIMB_REPORT.md`](bench/HILLCLIMB_REPORT.md).
