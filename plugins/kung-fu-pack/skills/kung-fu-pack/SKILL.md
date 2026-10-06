---
name: kung-fu-pack
description: >-
  Turn a target into a tight, high-signal briefing page. Given a target (a system, codebase,
  account, set of engagements, person, or topic) plus a scope, audience, and any links, it fans
  out parallel exploration across every source the user can reach (Notion, Linear, local code,
  web, Beeper), caches intermediate findings in a local workspace, pulls live data and flags
  staleness, consolidates into a planned structure, generates real information-carrying diagrams
  (dataviz dark-mode, rendered to PNG via headless Chrome), and publishes a styled page to Notion,
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

This skill expects the `/kung-fu-pack-init` config to exist (saved defaults + detected sources). If
it is missing, stop and point the user there. If a referenced source is unreachable at run time,
degrade gracefully and say so; the discipline never changes, only the mechanics.

---

## Prerequisites (state them, then degrade)

Check at the start and tell the user which mode you are in.

- **Config.** `${KUNG_FU_PACK_ROOT:-~/kung-fu-pack}/config.json` from `/kung-fu-pack-init`: default
  output, Notion destination, enabled sources, code roots, depth, model, house rules. No config:
  stop and run init.
- **Sources (deduced, not assumed).** `ToolSearch` for `notion`, `linear`, `tavily`, `beeper`;
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
  out/          local output (page.md / page.html) when not publishing to Notion
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
of clarifying questions, each with a proposed default, and wait. Do not fan out on guesses.

### 2. Capability check
Confirm which enabled sources actually resolve right now and state the mode in one line (for
example: "Notion + Linear + local code reachable; web off; Beeper not connected"). Map each source
to what only it can answer, so the fan-out has no overlap and no gap.

### 3. Fan out (the core move)
Create the pack workspace. Launch **parallel exploration agents in a single message**, one per
source or subtopic, each with a tight remit and instructed to write a findings file into
`research/` with a `SOURCES` section (URLs, IDs, file:line). Typical lanes:
- **Notion**: open the authoritative pages deeply (not just titles); capture IDs and last-edited
  dates; mark authoritative vs stale/draft/stub.
- **Linear / tracker**: pull live initiatives, projects, milestones, key issues; record IDs and
  percentages with the pull date.
- **Local code**: Explore agents over the code roots; read READMEs and entrypoints; verify claims
  with file:line; compare git recency to settle "is X still used / deprecated".
- **Web**: Tavily/WebSearch for external context, with citations.
Two rules that bite: subagents often cannot write files, so have each **return** its findings and
you persist them; and **pull live data** wherever a tool allows, stamping the age of anything that
is a cache or snapshot. For `--depth=deep`, add a second wave: an adversarial cross-check of the
riskiest claims and a "what is missing" completeness pass.

### 4. Consolidate and plan
Read every `research/` file. Reconcile conflicts (prefer live over cached, newest over oldest, code
over doc for "what exists"). Pull out the **non-obvious insights and corrections**, not just a
summary. Write `plan.md`: the section order, which claims need a lead, and which 1 to 3 diagrams
carry real information. For a large or high-stakes page, show the user the structure before
publishing (this is the natural place to use plan mode if available).

### 5. Diagrams (only where they carry information)
A diagram earns its place by making a structure clearer than prose can: a layered stack, a runtime
flow, a pipeline, a mapping. Generate from the dataviz template
(`references/diagram-gen.template.js`): copy it into `assets/gen.js`, author your diagrams in the
dark-mode palette, `node gen.js`, then render each to PNG with headless Chrome (see
`references/render-and-publish.md`) and **Read the PNG to eyeball it** before using it. No em dashes
in diagram text either.

### 6. Publish
Follow the house page style in `references/page-style.md` (framing callout, tight sections, tables,
every claim with a lead, a sources/leads section at the end). Then emit to the chosen output:
- **Notion**: upload each PNG via `notion-create-file-upload` + a multipart POST, embed by the
  returned `markdown_source`, then create or update the page. Default to a **draft** unless a
  destination is named; **confirm before overwriting** an existing page.
- **Self-contained HTML**: one file in `out/` with diagrams inlined as base64 so it is portable.
- **Local Markdown**: `out/page.md` plus the `assets/` PNGs referenced relatively.
- **Local preview server**: render the HTML pack and serve `out/` at localhost for live viewing.

### 7. Verify
Re-open or fetch the result: diagrams render, sections hold, tables intact. **Grep the final text
for em and en dashes (U+2014, U+2013); must be zero** (titles included, a common miss). Spot-check a
few claims against their leads. Report the output location, the headline insights, anything you
could not access, and the deep-dive leads.

---

## Principles
- **Deduce access, never assume it.** The pack is only as good as the sources you actually reached;
  name the gaps.
- **Live over cached.** Pull current data; stamp and flag the age of anything that is a snapshot.
- **A lead behind every claim.** file:line, Notion/Linear ID, or URL, so the reader can verify.
- **Cache the raw findings.** The workspace is the audit trail and the cheap path to the next refresh.
- **Diagrams must inform.** No decorative boxes; each diagram replaces a paragraph.
- **Max signal.** Concise but technical; corrections and insights, not a table of contents.
- **No em dashes anywhere.** Hyphens or rephrase, in chat, files, diagrams, and the published page.

## Guardrails
- Do not publish to a named external destination, or overwrite an existing page, without
  confirmation. Notion with no destination goes to a private draft.
- Do not fabricate a source you could not reach or a claim without a lead; disclose the gap instead.
- Do not let a stale cache masquerade as live; if you could not refresh it, label it.
- Do not ship a diagram you have not visually checked.
