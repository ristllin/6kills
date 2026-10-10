# Kung-Fu Pack: house page style

The look and feel every pack follows. The goal: a reader scans it in two minutes and knows where to
dig. Dense, technical, lead-backed, and free of filler.

## Shape
1. **Framing callout (first block).** One quote/callout that says what the target *is* in one or two
   sentences, the one reframing the reader most needs (for example "X is a vertical on Y, not a
   standalone thing"), and where the working notes live. This is the single most important block.
2. **The mental model.** The structure of the thing: a layered stack, the main components, or the
   lifecycle. Put the primary diagram here. Keep the prose to what the diagram does not already say.
3. **How it works / runs.** The runtime or process flow, with the second diagram if it earns one.
   Call out the one or two design decisions that actually matter.
3b. **See it in action.** For a show-it target (see `references/examples-and-visuals.md`): one example
   chosen to show the load-bearing mechanism (often a before/after), readable in under a minute, plus
   one real visual of the thing itself (screenshot or captured output). Each with a lead; label
   crafted examples as illustrative. The full walkthrough goes on a linked usage sub-page. How to
   choose: `references/examples-and-visuals.md`.
4. **Where it fits / what is deployed.** Concrete: environments, what is live vs scaffolding, hosts,
   cloud, chart paths. A deploy diagram often fits here.
5. **Tables over prose for inventories.** Repos, components, workstreams, engagements, primitives:
   a table with a Status column and a lead column beats paragraphs.
6. **Direction / status.** If there is a tracker, a live table (leads, milestone percentages, pull
   date) plus 3 to 5 strategic insights a newcomer must know. Flag what changed vs older notes.
7. **Deep-dive leads and sources (last block).** The explicit jump-off list: key READMEs with paths,
   authoritative doc IDs/URLs, tracker IDs, the workspace path. This is what makes it "onboarding"
   rather than a summary.

## Rules
- **Every claim carries a lead:** `path/file.py:120`, a Notion page ID, a Linear issue ID, or a URL.
  Write URLs in full (`https://...`, or a Markdown link) so they are clickable; a bare domain path is not.
  The rule holds on every sub-page too: "press releases", "platform page", or "see research" is not a
  lead; name the exact URL, or mark the row as a gap. Every table row is a claim: give the table
  a lead column (a file, a URL, or the capture each row came from); one link in the sentence above
  the table does not cover its rows.
  If you cannot back it, soften it or drop it.
- **Corrections are gold.** When the research overturns a prior belief (deprecated, renamed, moved,
  blocker cleared), say so explicitly; that is the highest-value content for a new owner.
- **Flag staleness.** Any snapshot or cache gets its age and a "verify live" note.
- **Status vocabulary, used consistently:** LIVE, in-flight, deprecated, scaffolding, backlog.
- **Length matches the ask, and overflow nests.** A one-pager stays one page; a "be thorough" brief
  can run two or three. If the honest coverage genuinely exceeds about three pages, do NOT cram or
  pile it into one monolith: nest. Write a 1 to 3 page index/overview (framing, mental model, and a
  map of the sub-pages with a one-line summary and a lead each) plus one linked sub-page per section,
  the way a wiki or a Notion space is organized. Nesting is a judgment call on genuine complexity, not
  a hard page-count trigger: the index links to the sub-pages and does not duplicate them, and you
  never fragment a brief that reads well as one page (product targets are the exception: they
  always link a usage sub-page). "One-pager" bounds the main page, not the tree: a product
  one-pager still links its usage sub-page. Only an explicit "single page, no sub-pages" request
  drops it. Prefer
  the lightest structure that stays readable, and prefer tight at every level.
- **Technical first; nest by content, not only by length.** The main page spends its words on what
  the thing is, how it works, and how it is used. For a product target, nest by
  default: a usage sub-page (walkthrough, screenshots, more examples) and, when it would crowd the
  technical content, a business sub-page (funding, market, pricing, deals). Keep a one-line summary
  and a link for each on the main page.
- **No em dashes or en dashes.** Anywhere. Use hyphens, commas, colons, parentheses, or rephrase.
  This includes the page title (a frequent miss) and all diagram text.
- **Accents are fine** (names like Rémi, Théo). Arrows (->), middots, and set symbols are fine.

## Tone
Brief a sharp peer who is new to this area, not a layperson. Assume technical fluency; spend words on
what is non-obvious, what is wrong in the old mental model, and where to look next.

## Writing standard (configurable)
`config.writing_standard` (or `--style`) selects the prose rules:
- `default` (the tone above): dense, technical, peer-level.
- `asd-ste100`: ASD-STE100 Simplified Technical English. Follow `references/asd-ste100.md` (short
  single-idea sentences, active voice and imperatives, one term per concept, no "-ing" verbs, vertical
  lists) and run its lint in the verify step. Use this for a global or non-native audience, for
  maintenance/procedural content, or when the user asks for plain controlled English. The structure
  (framing, mental model, tables, leads) is unchanged; only the sentence-level prose changes.
