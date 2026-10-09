# Kung-Fu Pack: examples and visuals

A reader trusts a pack when they can see the thing work. Prose and diagrams explain; an example and a
real screenshot prove. This file is how to choose them. Choosing the example is the hard part: it must
show the depth and the load-bearing part of the target, and stay simple enough to read in a minute.

## When this applies (two target kinds, used everywhere in the skill)
- **Product target:** a product, platform, tool, or vendor; something a reader would adopt, buy,
  integrate, or compete with. It gets the example and a real view, and nests a usage sub-page by
  default.
- **Show-it target:** any product target, plus a library or a codebase. It gets the example and a
  real view, but stays a single page when the material fits one.
For a person, an account, or a set of engagements, use this only when a concrete artifact (a
deliverable, a run, a report) makes the point better than prose.

## 1. Name the load-bearing mechanism first
Before you pick anything, write one sentence in `plan.md`: what makes this thing work, or what makes
it different from the obvious alternative. Examples of the shape:
- "Rules and an LLM detector run in parallel; a reconciler keeps only validated findings."
- "Commands are plain functions; type hints become the CLI parser."
If you cannot write this sentence, the research is not done; go back to the sources.

## 2. Shortlist, then choose (record it in plan.md)
List 2 or 3 candidate examples under `## Example choice` in `plan.md` and score each:
- **Load-bearing:** remove the mechanism and the example's outcome changes. If it would look the
  same on a competitor or a toy, reject it.
- **Readable:** a peer gets it in under a minute: about 15 lines of code or output, or one screen.
- **Honest:** real (from docs, a public repo, a demo, captured output) with a lead, or crafted from
  documented behavior and labelled as such.
- **Not category noise:** no setup, install, login, or hello-world that every tool in the category shares.
Write one line on why the winner beat the others.

## 3. Prefer a contrast shape
The cheapest way to make depth visible is a before/after or without/with pair: the same input
through the naive path and through the mechanism, with the difference called out in one line. A
contrast shows what the mechanism buys, which a single happy-path run does not.

## 4. Real first, crafted when real is too noisy
- Prefer a real artifact: a docs sample, a public repo file, captured CLI or API output, a published
  case or demo. Trim it to the load-bearing lines and say "trimmed".
- If no real artifact is small and clear enough, craft a minimal one from documented behavior. Label
  it `Illustrative, based on <lead>` directly above or below it. Never present a crafted example as
  captured output, and never invent behavior the sources do not support.
- For a code target you can run, run it and paste the real output rather than describing it. Run
  third-party code only in a sandbox or container, or after the user confirms; never install its
  dependencies or run its scripts on the host unprompted. If you are already inside an isolated,
  disposable environment (a container or CI sandbox, for example `/.dockerenv` exists), that is a
  sandbox: run it there.

## 5. Visuals: diagrams explain, screenshots prove
- A show-it target gets at least one real view of the thing itself when one exists: a UI
  screenshot, a results view, a terminal session, a rendered report. A diagram does not count. Not
  being able to run the tool is no reason to skip it: the docs and README images below are the
  first source anyway.
- A real view shows the product doing its job: a finding with its data flow, a results list, a fix
  diff, a dashboard with data, a CLI run and its output. A screenshot of a repo landing page, a
  marketing page, a blog post, or an advisory is not a view of the product; do not use one as the
  visual.
- Sources, in order: the images embedded in official docs and user guides (docs pages usually carry
  real UI screenshots: open the page, find the `<img>` that shows the feature, and save that image),
  launch posts and release notes with product images, public demo videos (a frame), the README's
  own screenshots or GIFs. Save the image with its page URL as the lead, or capture it with headless
  Chrome (see `render-and-publish.md`). Fetch only public `https://` URLs: never `file://`,
  localhost, or private addresses. If you can run the tool (with the same care as above), real
  terminal output is a real view.
- Embed it, do not point at it: copy the image into `assets/` and embed it, or paste the captured
  output as a block. Prose that describes the output, or a path to a screenshot the reader cannot
  see, is not a real view.
- Read every captured PNG before using it. Crop to the part that matters; illegible is worse than none.
- **Shrink before you look.** Never Read a GIF, a video, or a large image directly: one multi-MB
  file can fill the context and kill the run. Extract one frame to PNG, downscale to at most 1600 px
  wide and about 500 KB (`sips -Z 1600` on macOS, ImageMagick `convert -resize 1600x`, or Pillow;
  or open it in headless Chrome at a fixed window size and screenshot that), Read only the small
  PNG, and delete the raw download. Large images also bloat the self-contained HTML.
- **Pick a settled frame, not the first one.** A demo GIF or video spends many frames in motion: a
  loading spinner, a panel sliding in, a zoom or magnifier overlay, a cursor mid-click, an empty
  pane before the results arrive. Sample about six frames (evenly spaced, the last one included)
  into one small contact sheet, look at the sheet, and keep the frame that shows the result itself:
  findings listed, the detail pane filled, the fix diff visible. Reject any frame with a spinner,
  a "loading" or empty state, a transition, or an overlay covering the content. Recipe:
  `render-and-publish.md`.
- **The visual matches the page.** Prefer the frame or image that shows the same kind of result as
  the chosen example (a taint-flow example wants a finding with its data flow, not a settings
  screen). The lead is the exact image or page URL it came from, not the repo or the docs home.
- If the product UI is gated and no public image exists, say so in one line and use real output or a
  clearly labelled illustrative example instead. Never draw a fake UI.

## 6. Placement
- **Main page:** a short "See it in action" section after "How it works": the one chosen example
  (inline, within the size limit) and one real visual, each with a lead.
- **Usage sub-page** (`usage.md` / a child page): the full walkthrough (how a user actually runs it,
  the output they get, what they do next), more screenshots, and the runner-up examples. Link it from
  the main page. For a product target this sub-page is the default even when the main page would fit
  on its own; a show-it target that is not a product adds it only when the walkthrough is too big.
