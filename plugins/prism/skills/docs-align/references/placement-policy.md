# Placement policy: where content belongs

Loaded by `docs-align` Steps 5 and 6. The rule behind every row: committed docs describe the
current state of the repo for external readers. Everything else has a different home.

## The placement table

| Content type | Belongs in |
|---|---|
| What the project is, install, usage, license pointer | `README.md` |
| Durable long-form docs (guides, architecture, reference) | `docs/` (lowercase filenames) |
| Agent operating instructions: exact build/test/lint commands with flags, conventions that differ from defaults, "never touch X" boundaries | `AGENTS.md` (or `CLAUDE.md` importing it via `@AGENTS.md`) |
| Architecturally significant decisions (hard to reverse, affect structure or key quality attributes) with rationale and considered alternatives | `docs/decisions/NNNN-title.md` (MADR format) |
| Forward-looking direction, planned work | `ROADMAP.md` or the issue tracker; if a Projects board exists, ROADMAP.md is a short pointer, never a parallel copy |
| Contributor setup and process detail | `CONTRIBUTING.md` |
| Release history | `CHANGELOG.md` or releases, never inline in README |
| Implementation plans, task checklists, progress notes, findings dumps, session transcripts, review summaries | Gitignored location (`plans/`, `.scratch/`, `*.local.md`) or the PR description. Never the committed tree. |
| Personal, machine-specific, or operator-only notes | Gitignored local file (`CLAUDE.local.md`, `*.local.md`) |

## Never in committed docs

- **Session narration**: "in this session", "as discussed", "the user asked", "I have
  implemented", "we just fixed", "per your request", "now the tests pass".
- **Personal information**: individual names and attributions, machine-specific absolute
  paths (`/Users/<name>/`, `C:\Users\`), personal sandbox URLs, contact details.
- **Secrets**: API keys, tokens, database URLs, internal hostnames, in any file including
  AGENTS.md and CLAUDE.md. Infrastructure is described only in general terms.
- **Decision history that guides nobody**: changelog-style narration of how the doc or code
  evolved ("previously we used X, then switched to Y"). Current state belongs in the doc;
  the path there belongs in git history; rationale that still matters belongs in an ADR.
- **Vibe-coding context**: one-off user decisions made mid-session that only make sense with
  the conversation open. If the decision constrains future work, restate it as a rule an
  external contributor can follow (AGENTS.md or ADR); otherwise drop it.

## Agent litter: file patterns to flag

Any committed file matching these names is presumptively litter. Verify its durable
conclusions were promoted (into code, docs, an ADR, or a commit message), then propose
deletion plus a gitignore entry:

```
IMPLEMENTATION_PLAN.md  TEST_RESULTS.md  TEST_REPORT*.md  CODE_REVIEW.md
QA_CHECKLIST.md  SUMMARY.md  WALKTHROUGH.md  NOTES.md  FINDINGS.md
PROGRESS.md  BACKLOG.md  task_plan.md  findings.md  progress.md
research_notes.md  plan-*.md  *.plan.md  PLAN.md
```

Also flag: any new root-level ALL_CAPS `.md` outside the timeless set (README, LICENSE,
CONTRIBUTING, CHANGELOG, SECURITY, CODE_OF_CONDUCT, AGENTS, CLAUDE, ROADMAP, GOVERNANCE,
MAINTAINERS), and a merged PR that leaves its completed plan file in the tree.

Exclusions come first. Never flag `SUMMARY.md` when mdBook is in use (`book.toml` present).
Before flagging any pattern-matched file, search build configs, CI workflows, and other docs
for references to it; any hit disqualifies the file. Deletion plus a gitignore entry for a
pattern-matched file is propose-only and requires user confirmation, even in auto-fix modes.

## Recommended gitignore set for AI-assisted repos

```gitignore
# AI agent artifacts: plans, scratch, session-local state
*.plan.md
plan-*.md
PLAN.md
plans/
.planning/
.scratch/
.claude/plans/
.claude/scratch/
*.local.md
CLAUDE.local.md
.claude/settings.local.json
.aider*
```

Repos that ship subtree content (plugin marketplaces, monorepo packages) should root-anchor
these patterns with a leading `/` so they never mask distributed files.

Commit (never ignore) the shared instruction layer: `AGENTS.md`, `CLAUDE.md`,
`.claude/settings.json`, `.claude/agents/*.md`, `.claude/commands/*.md`. Flag these appearing
in .gitignore, and flag `settings.local.json` or `CLAUDE.local.md` appearing in the tree.

## AGENTS.md content rules

- Written for external readers: any competent contributor or agent, with zero session context.
- Commands are executable with flags (`npm test -- --watch=false`), never tool names alone.
- Boundaries expressed as Always / Ask first / Never lists.
- Keep it under ~150 lines. Every line loads into every agent session, so cut anything an
  agent can derive from the codebase (directory listings, dependency inventories,
  architecture overviews).
- No overlap with README: AGENTS.md holds what would clutter the README for humans; README
  holds what agents do not need repeated.
- If both AGENTS.md and CLAUDE.md exist, CLAUDE.md should import AGENTS.md, and any divergent
  duplicated instructions across the two are a finding.
- Stable rules only. Current-sprint tasks, in-flight migrations, and "TODO this week" go to
  issues or a gitignored plan.

## ADR basics (for the relocation recommendation)

An ADR records: context and problem, considered options, the decision with rationale, and
consequences. A record without considered alternatives loses its value; flag those. Accepted
ADRs are append-only: a changed decision gets a new record marked "supersedes NNNN". Reserve
ADRs for architecturally significant choices; variable naming and one-off fixes do not
qualify.
