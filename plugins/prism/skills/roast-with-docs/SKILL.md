---
name: roast-with-docs
description: >-
  Roast code — a witty, brutal-but-fair critique where every jab is backed by an
  authoritative source (language docs, framework guides, linter/lint-rule pages, style
  guides). Use when the user says "roast my code", "roast this", "prism roast", or wants a
  funny-but-useful review that doesn't make things up. Humor is the delivery; the underlying
  finding is always real and cited. Supports a tone flag: --harsh (savage) or --kind (gentle).
---

# Roast With Docs

A roast is only funny if it's *true*. This lens finds real problems, grounds each one in an
authoritative reference, and *then* delivers it with humor. The comedy layer is optional; the
citation is not.

## Rules

1. **Finding first, joke second.** For every roast line, first identify a concrete, defensible
   issue (anti-pattern, deprecated/misused API, footgun, complexity smell, wrong tool for the
   job). If you can't name the real problem, you don't get to make the joke.
2. **Cite an authority.** Back each finding with a real source and link:
   - Language: official stdlib/reference docs (e.g. Python docs, MDN, cppreference, pkg.go.dev).
   - Framework: the framework's own guide (React, Django, Rails, Spring…).
   - Lint/style: the specific rule page (ESLint `no-await-in-loop`, Ruff/Flake8 code, `clippy`,
     Google/PEP 8/Airbnb style-guide section).
   - Prefer fetching the page (WebFetch) to quote the relevant line accurately. Never invent a
     citation — if you can't find a real source, downgrade it to an uncited "opinion" and say so.
3. **Tie it to the code.** Every line references `file:line` so the target is unambiguous.
4. **Respect the tone flag.** Default is *witty-useful*. `--harsh` = savage stand-up energy;
   `--kind` = gentle ribbing. Never punch at the person — only at the code.
5. **Stay in scope.** Roast the diff in `pr` mode, the whole codebase in `improve`, the
   *approach* in `plan`/`new` mode. Read-only: this lens never edits.

## Cite-check before you ship it

Freeform "code quality" judgment is exactly where LLM reviewers diverge most from real
developer preference — grounding in an external authority is the mitigation, so it has to be
real grounding. Before emitting the roast, run a quick pass over your own findings:

- **Verify each citation actually supports the claim.** When in doubt, WebFetch the page and
  confirm the rule/line says what you say it does. Drop any finding whose citation doesn't hold
  (or downgrade it to a clearly-labelled uncited opinion).
- **Skip nits the project already governs.** If a lint/format rule you'd cite is already
  configured in the repo (`.eslintrc`, `ruff.toml`, `.prettierrc`, etc.) and the code passes
  it, don't roast it — that's noise, not insight.
- **Report what you suppressed**, so the filtering is visible (see the output line below).

## Output

```
## 🔥 Roast — <scope>  (tone: witty)

1. `api/handler.js:12` — Awaiting inside a `for` loop like it's 2015. This serializes every
   request; your event loop is filing a complaint.
   → ESLint `no-await-in-loop`: https://eslint.org/docs/latest/rules/no-await-in-loop

2. `utils/date.py:30` — Hand-rolling timezone math. The `datetime` docs wrote 4 paragraphs
   begging you not to.
   → https://docs.python.org/3/library/datetime.html#aware-and-naive-objects

...

_Verdict:_ <one-line overall temperature check> — <N> cited burns shown · <M> uncited
opinions suppressed · <K> nits skipped (already caught by the project's own linter).
```

Keep it tight. A good roast is 5–12 lines, each a real, cited issue. If there's genuinely
nothing to roast, say so (that itself is a compliment) rather than manufacturing weak jokes.

## References (prior art / grounding)
- Roast-my-code projects: github.com/Arephan/roast-my-code, github.com/dalmaer/glaser
- LLM grounding / citing sources: keep claims tied to fetched docs, not memory.
