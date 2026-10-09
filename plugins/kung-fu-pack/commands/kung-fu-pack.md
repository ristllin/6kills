---
description: "Build a styled briefing page on a target: scope it, fan out research across every source you can reach into a cached workspace, consolidate and plan, generate diagrams, then publish to Notion, HTML, Markdown, or a local server"
argument-hint: "[<target> + scope/directive/links/description, and flags: --output=<notion|html|md|server>, --dest=<notion-url-or-id|draft>, --depth=<standard|deep>, --audience=<who>, --style=<default|asd-ste100>, --model=<id>; empty uses the target in context]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Agent", "AskUserQuestion", "ToolSearch", "WebFetch", "WebSearch"]
---

Run the **kung-fu-pack** skill on the target.

Target + scope + flags = `$ARGUMENTS` (if empty, use the target already established in the
conversation; if none exists, ask the user for the target and scope, then stop).

**First, load config.** Resolve the workspace root (default `~/kung-fu-pack`) and read its
`config.json`:

```bash
ROOT="${KUNG_FU_PACK_ROOT:-$HOME/kung-fu-pack}"; test -f "$ROOT/config.json" && echo READY || echo NEEDS_INIT
```

If it prints `NEEDS_INIT`, the user has not onboarded. Tell them to run `/kung-fu-pack-init` once
(it detects their Notion/Linear/web access and saves defaults), then stop. Do not guess a config.

Otherwise follow the kung-fu-pack skill exactly, honoring the saved defaults and any flags that
override them (`--output`, `--dest`, `--depth`, `--audience`, `--style`, `--model`). `--style`
selects the writing standard: `default` (dense peer-level prose) or `asd-ste100` (Simplified
Technical English per `references/asd-ste100.md`). In short:

1. **Scope.** Parse the directive, links, and description. If the scope, audience, or must-cover
   points are thin, ask one focused batch of clarifying questions, then wait. Keep questions general
   and parameter-shaped (the KIND of thing, its audience, depth, time window); offer a default only
   for genuine parameters and never invent concrete names (projects, products, teams, people).
   Never choose the target yourself from a code root or the working directory; ask, then wait.
2. **Capability check.** Confirm which enabled sources are actually reachable right now
   (ToolSearch for notion/linear/tavily/beeper; probe the code roots). State the mode and degrade
   gracefully on anything missing.
3. **Fan out.** Create the pack workspace (`packs/<slug>/{research,assets,out}`) and launch parallel
   exploration agents, one per source or subtopic, each saving an intermediate file to `research/`.
   Pull live data where possible and flag the age of any cache or snapshot.
4. **Consolidate and plan.** Read every intermediate file, reconcile conflicts, surface the
   non-obvious insights and corrections, and write `plan.md` with the page structure. For a large
   or high-stakes page, confirm the structure with the user before publishing.
5. **Diagrams.** Identify the 1 to 3 diagrams that carry real information, generate them from the
   dataviz template, render to PNG with headless Chrome, and eyeball each before using it.
6. **Publish** to the chosen output: Notion (upload PNGs, create or update the page; draft unless a
   destination is named; confirm before overwriting), self-contained HTML, local Markdown, or the
   local preview server.
7. **Verify.** Re-open or fetch the result, confirm diagrams render and structure holds, grep for
   em and en dashes (must be zero), and spot-check claims against their leads. Report with the
   output location and the deep-dive leads.

Respect the house rules from config: no em dashes anywhere, every claim carries a lead, staleness is
flagged, and you confirm before overwriting an existing page or publishing to any named external
destination.
