# AGENTS.md: working on 6kills

Guidance for any agent (or human) changing this repo. 6kills is a **public** plugin marketplace:
everything committed here is published.

## Repo shape
- `.claude-plugin/marketplace.json` lists every plugin; each plugin lives in `plugins/<name>/` with
  its own `.claude-plugin/plugin.json`, `commands/`, `skills/<name>/SKILL.md`, and a README.
- Portable skills (Agent Skills `SKILL.md`) also install on Mistral Vibe and OpenAI Codex through
  the plugin's `install.sh` (see `plugins/kung-fu-pack/install.sh`).
- `qa/` is the clean-room release QA harness (Docker, three harnesses).

## Branches and PRs
- Never commit to `main`. One feature = one branch = one PR. Do not stack PRs; if work fans out
  into several branches, collapse them into one branch off current `main` before asking for review.
- Agents open PRs; a human merges.

## Release flow (required before any PR to `main`)
Run these in order. Do not open the PR until every step is green or a failure is explicitly
accepted and written in the PR body.

1. **Commit** the candidate on its branch. QA tests the committed ref, not the working tree.
2. **Docker QA on all three harnesses:** `qa/run-qa.sh` (defaults to `claude codex vibe`).
   For each harness, in a fresh container, it:
   - fresh-installs 6kills from the committed ref (Claude Code: marketplace add + plugin install;
     Codex and Vibe: `install.sh`);
   - **scenario A**, a thin request ("build me an onboarding brief"): the skill must ask general,
     parameter-shaped questions and must not invent concrete names (model-graded);
   - **scenario B**, a real-world pack on a public repo (default `fastapi/typer`): the workspace is
     used (research files + plan), output exists, zero em/en dashes, length rule holds (one page
     within ~3 A4 pages, or a short index plus linked sub-pages whose links resolve), at least 60%
     of fact lines carry a lead, and code leads resolve to real files (`qa/check_pack.py`).
   Credentials pass by env var name only. Harness configs (Codex provider, Vibe model) are supplied
   from a directory outside the repo via `KFP_QA_CFG`. Read `$KFP_QA_OUT/summary.md`, and open at
   least one produced pack to judge it by eye; the checks are a floor, not a quality bar.
3. **Prism** on the final diff (`prism pr`), then fix what it finds and re-run any affected QA.
4. **Sanitize** the full diff against `main`, because the repo is public:
   - no secrets, tokens, or keys; no internal hostnames, proxy or tailnet URLs, or local paths;
   - no private names: employers, customers, internal projects or codenames, colleagues;
   - no Notion, Linear, or other workspace IDs; no private emails;
   - no em or en dashes in authored text (third-party data under `bench/tasks/fixtures` is kept
     verbatim and exempt).
   Grep for each category; do not rely on memory.
5. **Docs:** update the top-level `README.md` (plugin count, table row with description, install
   line, quick start, repo layout) and the plugin's own README, plus `marketplace.json` description
   and version.
6. **Open the PR** to `main` with the QA summary table, prism outcome, and any accepted failures.

## House rules
- No em or en dashes anywhere in authored content (code, docs, commit messages, PR text).
- Raw eval artifacts (packs, logs, gold scratch) stay outside the repo; commit only curated results.
- Keep secrets in the environment; never write them to files inside the repo.
