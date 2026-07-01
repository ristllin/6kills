---
name: peer-review
description: >-
  Get an independent, critical second opinion from a DIFFERENT AI provider. Use when the user
  says "peer review", "prism peer", "get a second opinion", "have another model check this",
  or wants an adversarial review of a plan, a diff, or completed work. Detects the current
  agent/model, routes the critique to a comparable model from another provider via a
  cross-provider CLI (codex / cursor-agent), and gracefully falls back (local ollama, then a
  fresh Claude skeptic) when none is available. Announces before spending credits.
---

# Peer Review (cross-provider)

The value of a peer review is *independence* — a model from a different lineage catches what
the author's own family of models is blind to. This lens routes the work to a **different
provider** for an adversarial critique, then reconciles that critique with our own view.

## Step 1 — Identify the current agent

You are running as Claude inside Claude Code. Read the current model from your runtime context
(the session's model id, e.g. `claude-opus-4-8`). You **cannot** introspect it via an API —
there is no "what model am I" call — so use what the harness already tells you. Record the
provider (Anthropic) and rough tier (frontier / mid / small) so you can pick a comparable
competitor.

## Step 2 — Pick a different-provider reviewer (best available)

Probe, in order, and use the first that works (`command -v <cli>`). **Announce before calling** —
external calls may spend the user's credits. Prefer a frontier competitor comparable to the
current Claude tier.

1. **`codex` — OpenAI Codex CLI (preferred cross-provider).** OpenAI's own frontier (GPT-5-codex),
   a genuinely different lineage. Run headless and read-only so it can't touch files:
   ```bash
   codex exec --sandbox read-only "<critique prompt>"
   # add -m <model> to pick a tier; --json for structured output
   ```
   Auth is via the user's ChatGPT login or `OPENAI_API_KEY`. If not installed, it can be added
   with `npm i -g @openai/codex` (or `brew install codex`) — mention this if the user wants it.
2. **`cursor-agent` — Cursor CLI (cross-provider).** Routes to GPT / Gemini via the user's Cursor
   account. Non-interactive:
   ```bash
   cursor-agent -p --output-format json "<critique prompt>"
   ```
   Pick a frontier competitor model when the CLI allows model selection.
3. **`ollama` (offline fallback).** If no cloud cross-provider CLI is available/authenticated:
   ```bash
   ollama list          # see what's local
   ollama run <model> "<critique prompt>"
   ```
   Use the strongest local non-Anthropic model (e.g. `mistral:7b`). **Flag it as low-tier** —
   a 7B local model is not a peer of a frontier model; treat its critique as a sanity check.
4. **Fresh Claude skeptic (ultimate fallback).** If no external provider is reachable, spawn a
   fresh Claude subagent (Task tool) with an adversarial, skeptical persona and, if possible, a
   different model tier. **Flag clearly that this is same-provider** and therefore a weaker form
   of independence.

Other cross-provider CLIs (e.g. `gemini`, `llm`, `aider`) are fine substitutes at tier 1/2 if
present — the rule is simply: a different provider, run headless and read-only, frontier if possible.

Always state which reviewer was actually used and why (so the user can weigh the independence).

## Step 3 — Brief the reviewer

Give the reviewer everything it needs to be genuinely critical, self-contained:

- **The original ask** — what the user actually requested (the real goal).
- **The artifact** — the plan (in `plan` mode), the diff (`pr` mode), or the completed work.
- **Context** — key constraints, the relevant files/snippets, and any assumptions made.
- **The charge**: *"Critically review this. Find flaws, risks, missed requirements, incorrect
  assumptions, edge cases, and simpler/safer alternatives. Be specific and adversarial. Do not
  be agreeable. Rank issues by severity."*

Keep the prompt focused; paste only the relevant code/plan, not the whole repo.

## Step 4 — Reconcile

Don't just relay the critique — **evaluate it.** For each point the reviewer raised, state
whether prism agrees, and why. Distinguish real catches from noise or misunderstanding.

## Output

```
## 🧑‍⚖️ Peer review
Current agent: claude-opus-4-8 (Anthropic, frontier)
Reviewer: cursor-agent → gpt-5 (OpenAI, frontier)   [or: ollama mistral:7b (local, low-tier)]

Reviewer's critique:
- [High] <point> ...
- [Med]  <point> ...

Prism's reconciliation:
- Agree with #1 — <reason>; will address in <lens/fix>.
- Disagree with #2 — <reason it's a false alarm>.

Net: <what actually needs to change>.
```

## References
- Cross-provider LLM-as-judge (use a different family to reduce bias): comet.com/site/blog/llm-as-a-judge
- Cursor CLI (`cursor-agent`) non-interactive `-p --output-format json`.
