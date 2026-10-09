---
name: kung-fu-pack
description: >-
  Turn a target into a tight, high-signal briefing page. Given a target (a system, codebase,
  account, set of engagements, person, or topic) plus a scope, audience, and any links, it fans
  out parallel exploration across every source the user can reach (Notion, Linear, local code,
  web, Beeper), caches intermediate findings in a local workspace, pulls live data and flags
  staleness, consolidates into a planned structure, generates real information-carrying diagrams
  (dataviz dark-mode, rendered to PNG via headless Chrome), shows the target in action with a
  carefully chosen example and real screenshots, and publishes a styled page to Notion,
  a self-contained HTML file, local Markdown, or a local preview server. Every claim carries a
  deep-dive lead and it never uses em dashes. Use whenever the user says "kung-fu-pack", or asks
  to build a briefing, onboarding page, dossier, one-pager, or overview of something by pulling
  together Notion, Linear, code, and the web. First run needs /kung-fu-pack-init.
---

# Kung-Fu Pack

A "pack" is a briefing: a dense, scannable page that lets a reader (often a new owner of some area)
understand a target at altitude and then jump straight into the real resources. The craft is not the
writing. It is three things: **reaching every source the user has and pulling live truth from each**,
**caching the raw findings so the page is auditable and re-runs are cheap**, and **compressing it
into high signal with a deep-dive lead behind every claim**. A pretty page built on a stale cache or
an unverified guess is the failure mode.

This skill runs on Claude Code, Mistral Vibe, and OpenAI Codex (they share the Agent Skills
`SKILL.md` format). It expects a saved config of defaults + sources at
`${KUNG_FU_PACK_ROOT:-~/kung-fu-pack}/config.json`. On Claude Code that is created by
`/kung-fu-pack-init`; on any harness, if the config is missing, run the short setup inline on first
use (see "First run" below) and write it, then continue. If a source is unreachable at run time,
degrade gracefully and say so; the discipline never changes, only the mechanics. See "Harness notes"
at the end for the per-harness equivalents of the few tool-specific steps.

---

## Prerequisites (state them, then degrade)

Check at the start and tell the user which mode you are in.

- **Config.** `${KUNG_FU_PACK_ROOT:-~/kung-fu-pack}/config.json`: default output, Notion
  destination, enabled sources, code roots, depth, model, house rules. No config: run the "First
  run" setup inline and write it before continuing.
- **Sources (deduced, not assumed).** Check which MCP servers are connected for `notion`, `linear`,
  `tavily`, `beeper` (Claude Code: `ToolSearch`; Vibe/Codex: your connected MCP server list), and
  probe the configured code roots exist. Each present source is a research lane; each absent one is
  a gap to disclose, not to fake.
- **Render toolchain.** `node` (diagram generation) and a Chrome/Chromium binary (PNG render). No
  Chrome: still write the diagram HTML and either inline it (HTML output) or link it, and say the
  PNG step was skipped. `python3` or `node` only needed for the local preview server output.
- **A reachable user** for one default gate: scope confirmation when the brief is thin, and plan
  confirmation for a large or high-stakes page. Everything else you decide and record.

---

## The workspace (cache everything)

Each target gets its own folder under the workspace root so nothing lives only in chat and re-runs
are cheap:

```
<workspace-root>/packs/<slug>/
  research/     one intermediate file per source or subtopic (raw findings + SOURCES)
  assets/       diagram gen.js, the .html, and rendered .png files
  out/          local output (page.md / page.html, or index.md plus <section>.md when nested)
                (product targets: index.md plus usage.md, and business.md when needed)
  plan.md       the planned page structure, written before publishing
```

`<slug>` is a short kebab-case name for the target. Keep the research files even after publishing;
they are the audit trail behind every claim and the starting point for the next refresh.

---

## The method

### 1. Scope
Read the directive, links, and description. Fix: the **target**, the **audience** (who reads this
and what decision it serves), the **angle/depth**, the **must-cover** points, and the **output**
(default from config, override from `--output`). If any of these is unclear, ask one numbered batch
of clarifying questions and wait. Keep every question general and parameter-shaped: ask about the
KIND of thing (its category, boundary, audience, depth, time window), never a guessed instance. Offer
a proposed default only for genuine parameters (audience, depth, output format); never invent concrete
names (projects, products, teams, people) as a default. If the target or its members are unknown, ask
the user to name them. Do not fan out on guesses. The target must come from the user: never pick
it yourself from a configured code root, the working directory, or the workspace, even when only one
candidate exists. You may list what you found as options, then wait for the answer.

### 2. Capability check
Confirm which enabled sources actually resolve right now and state the mode in one line (for
example: "Notion + Linear + local code reachable; web off; Beeper not connected"). Map each source
to what only it can answer, so the fan-out has no overlap and no gap.

### 3. Fan out (the core move)
Create the pack workspace. Fan out exploration, one worker per source or subtopic, each with a tight
remit and instructed to return a findings file saved into `research/` with a `SOURCES` section
(URLs, IDs, file:line). If your harness supports subagents, run them in parallel (Claude Code: the
Agent tool in a single message; Vibe/Codex: their subagent mechanism); otherwise do focused
sequential passes, one source at a time. Typical lanes:
- **Notion**: open the authoritative pages deeply (not just titles); capture IDs and last-edited
  dates; mark authoritative vs stale/draft/stub.
- **Linear / tracker**: pull live initiatives, projects, milestones, key issues; record IDs and
  percentages with the pull date.
- **Local code**: Explore agents over the code roots; read READMEs and entrypoints; verify claims
  with file:line; compare git recency to settle "is X still used / deprecated".
- **Web**: Tavily/WebSearch for external context, with citations.
- **Usage and visuals** (show-it targets: products, platforms, tools, vendors, libraries, codebases): docs quickstarts,
  sample repos, CLI or API references, launch posts and public demos. Collect candidate examples and
  real screenshots or output with their URLs; for a code target you can run, run it and save the
  output (third-party code only in a sandbox or after the user confirms; a container you are already
  in counts, see `references/examples-and-visuals.md`). If you cannot run it, the real view comes from the docs or README images; never skip it. Keep fetched pages small (extract the part you need) so one page cannot flood the context.
Two rules that bite: subagents often cannot write files, so have each **return** its findings and
you persist them; and **pull live data** wherever a tool allows, stamping the age of anything that
is a cache or snapshot. For `--depth=deep`, add a second wave: an adversarial cross-check of the
riskiest claims and a "what is missing" completeness pass.

### 4. Consolidate and plan
Read every `research/` file. Reconcile conflicts (prefer live over cached, newest over oldest, code
over doc for "what exists"). Pull out the **non-obvious insights and corrections**, not just a
summary. Always write `plan.md` in the pack folder (it records the structure decision): the section order, which claims need a lead, and which 1 to 3 diagrams
carry real information. For a show-it target (`references/examples-and-visuals.md` defines the two target kinds), also record
the **load-bearing mechanism** in one sentence and an `## Example choice` section (2 or 3 candidates,
scored, the winner and why) per `references/examples-and-visuals.md`. **Decide structure by complexity, not a hard page count.** Keep a single tight
page when the material reads well as one 1 to 3 page brief; that is the default and the goal (product targets excepted, below). Nest only
when genuine breadth would otherwise force a cramped monolith or lose navigability: then write a short
index/overview (framing, the mental model, and a linked map of the sub-pages, each with a one-line
summary and a lead) plus one sub-page per major section. The index summarizes and links; it must not
repeat the sub-pages. A product target (product, platform, tool, or vendor) nests by default: the main page stays
technical and links a usage sub-page (walkthrough, screenshots, more examples) and, if business
context would crowd it, a business sub-page. Prefer the lightest structure that stays readable, never fragment a brief that
works as one page (except a product target's usage sub-page; "one-pager" bounds the main page and does not drop it), and honor an explicit "no sub-pages" request. For a large or high-stakes page, show
the user the structure before publishing (the natural place to use plan mode if available).

### 5. Diagrams and screenshots (only where they carry information)
A diagram earns its place by making a structure clearer than prose can: a layered stack, a runtime
flow, a pipeline, a mapping. Generate from the dataviz template
(`references/diagram-gen.template.js`): copy it into `assets/gen.js`, author your diagrams in the
dark-mode palette, `node gen.js`, then render each to PNG with headless Chrome (see
`references/render-and-publish.md`) and **Read the PNG to eyeball it** before using it. No em dashes
in diagram text either. Diagrams explain; screenshots prove. A show-it target also gets at
least one real view of the thing (UI screenshot, results view, captured output), saved in `assets/`
with its source URL as the lead and read back before use. Never draw a fake UI. Choose and place the
example and visuals per `references/examples-and-visuals.md`.

### 6. Publish
Follow the house page style in `references/page-style.md` (framing callout, tight sections, tables,
a "See it in action" example for show-it targets, every claim with a lead, a sources/leads section at
the end). Apply the configured
`writing_standard`: `default` (dense peer-level prose) or `asd-ste100` (Simplified Technical English
per `references/asd-ste100.md`; short single-idea sentences, active voice, one term per concept, no
"-ing" verbs, vertical lists). The page structure is the same either way; only the prose changes.
Then emit to the chosen output:
- **Notion**: upload each PNG via `notion-create-file-upload` + a multipart POST, embed by the
  returned `markdown_source`, then create or update the page. Default to a **draft** unless a
  destination is named; **confirm before overwriting** an existing page.
- **Self-contained HTML**: one file in `out/` with diagrams inlined as base64 so it is portable.
- **Local Markdown**: `out/page.md` plus the `assets/` PNGs referenced relatively.
- **Local preview server**: render the HTML pack and serve `out/` at localhost for live viewing.

If `plan.md` chose a nested structure, publish a tree, not one page: **Notion** = an overview page
with one child sub-page per section, each linked from the overview; **HTML** = `index.html` plus one
linked section page each (wiki-like); **Markdown** = `out/index.md` plus `out/<section>.md`, linked
with relative links; **preview server** = serve the directory so the index and sub-pages are browsable.
Verify every inter-page link resolves.

### 7. Verify
Re-open or fetch the result: diagrams render, sections hold, tables intact. Confirm `plan.md` exists. **Count
the words of every page: a single page over ~1500 words (3 A4 pages) is out of bounds**; cut it, or
nest it if the material is genuinely broad. For a nested pack, the index stays within that budget.
For a show-it target, confirm the example passes its own tests (shows the mechanism, about 15 lines
or one screen, lead or `Illustrative` label) and at least one real visual is embedded. A missing
real visual is a gap to close, not to report: go back, fetch a docs or README image (or run the code
if you are already in a container or sandbox), then publish; for a product
target, also that the usage sub-page exists and is linked. **Grep the final text
for em and en dashes (U+2014, U+2013); must be zero** (titles included, a common miss). If
`writing_standard` is `asd-ste100`, run the lint in `references/asd-ste100.md` (sentence length, the
"-ing" form, passive voice, 4+ word noun clusters, one-term-per-concept) and fix the hits, and add
the "approximated, not dictionary-certified" footer note. Spot-check a few claims against their
leads. Report the output location, the headline insights, anything you could not access, and the
deep-dive leads.

---

## Principles
- **Deduce access, never assume it.** The pack is only as good as the sources you actually reached;
  name the gaps.
- **Live over cached.** Pull current data; stamp and flag the age of anything that is a snapshot.
- **A lead behind every claim.** file:line, Notion/Linear ID, or URL, so the reader can verify.
- **Cache the raw findings.** The workspace is the audit trail and the cheap path to the next refresh.
- **Diagrams must inform.** No decorative boxes; each diagram replaces a paragraph.
- **Show, then explain.** One well-chosen example of the load-bearing mechanism and one real view of
  the thing beat a page of description.
- **Max signal.** Concise but technical; corrections and insights, not a table of contents.
- **No em dashes anywhere.** Hyphens or rephrase, in chat, files, diagrams, and the published page.

## Guardrails
- Do not publish to a named external destination, or overwrite an existing page, without
  confirmation. Notion with no destination goes to a private draft.
- Do not fabricate a source you could not reach or a claim without a lead; disclose the gap instead.
- Do not let a stale cache masquerade as live; if you could not refresh it, label it.
- Do not ship a diagram you have not visually checked.

---

## First run (any harness, when no config exists)

If `${KUNG_FU_PACK_ROOT:-~/kung-fu-pack}/config.json` is missing, do a short setup before the first
pack (on Claude Code this is the `/kung-fu-pack-init` command; on Vibe/Codex, do it inline):
1. Detect reachable sources (the connected MCP servers for notion/linear/tavily/beeper) and the
   render toolchain (`bash skills/kung-fu-pack/setup.sh`, or `setup.sh` from the installed skill dir).
2. Ask the user: default output (recommend Notion if its MCP is connected, else self-contained
   HTML), Notion destination (a page/DB URL or draft), which sources to enable, code roots, depth,
   and any house rules (the no-em-dashes and lead-behind-every-claim defaults stay on).
3. Write `config.json` (see the schema in the init command) and scaffold `packs/` under the
   workspace root. Never store secrets there.

## Harness notes

The method is identical everywhere; only these mechanics differ:

| Step | Claude Code | Mistral Vibe | OpenAI Codex |
|---|---|---|---|
| Invoke | `/kung-fu-pack`, `/kung-fu-pack-init` | `/kung-fu-pack` (user-invocable skill) | by name, or `$kung-fu-pack` |
| Skill location | plugin (installed via marketplace) | `~/.vibe/skills/kung-fu-pack/` | `~/.codex/skills/kung-fu-pack/` |
| Detect MCPs | `ToolSearch` | connected MCP servers | connected MCP servers (declare in `agents/openai.yaml`) |
| Fan out | Agent tool, parallel | subagents if available, else sequential | subagents if available, else sequential |
| Ask the user | `AskUserQuestion` | ask in chat | ask in chat |
| Clarify + plan | plan mode optional | inline | inline |

Install on Vibe or Codex with `bash plugins/kung-fu-pack/install.sh <vibe|codex>` (see the plugin
README). The MCP tool names (for example Notion `notion-create-file-upload`) are the same across
harnesses whenever the same MCP server is connected, so publishing is portable.
