# 🎼 orchestrate

**Relentless runs one lane. Collapse closes a fan-out. Orchestrate is the opening bracket.**

It takes a raw requirements list and turns it into a running program: clarified requirements,
a PRD, a dependency-ordered tracker split into waves of parallel non-conflicting lanes,
detached headless workers each running relentless to a frozen Definition of Done, a
supervision loop that merges finished work within the window, validation gates, and releases
between waves.

The launch is the easy part. The hard parts are three:

- **Resolving ambiguity before the fleet exists.** Twelve autonomous lanes amplify one wrong
  guess twelve-fold; a frozen DoD built on a guess ships the wrong program very efficiently.
- **Truthful supervision.** Lane state comes from logs and progress files, never from process
  tables or memory. Finished, blocked, and errored all look identical from `ps`.
- **Merge cadence.** A finished lane merged within one supervision window; completed work
  sitting unmerged rots against a moving base, and that is an orchestrator failure.

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install orchestrate@6kills
```

## Usage

```
orchestrate                                  # plan and launch the program in context
/orchestrate "path/to/requirements.md"
/orchestrate --tracker=markdown --cadence=30m --max-lanes=8
```

Called with no arguments, it uses the requirements already established in the conversation.
If there are none, it asks the owner for the raw requirements list, then stops.

## The eight phases

| Phase | What happens |
|---|---|
| **1. Interrogate** | Read the whole requirements list, then ask the owner **one numbered list of clarifying questions covering every ambiguous step**, each with a proposed default. Wait for the answers. The one place orchestrate genuinely stops. |
| **2. PRD** | Write it slowly and completely from the answers: checkable acceptance criteria, regression surfaces, non-goals, quality bars, contracts, budgets. Every lane's TASK.md is cut from this. |
| **3. Tracker** | Derive the dependency graph, split into waves of parallel non-conflicting lanes, create projects + issues with **frozen DoDs and evidence requirements**. Human gates default 0-1: plan approval only, plus gates at genuinely irreversible or outward-facing steps. |
| **4. Setup** | Per lane: worktree + branch off the frozen base (env files copied in - worktrees do not inherit gitignored files), TASK.md (frozen DoD, file-ownership contract, prod-care rules, battery definition, evidence discipline), one shared lane charter skill, resource locks if hardware is involved. |
| **5. Launch** | Detached headless `claude -p` processes: nohup, model pinned, `--dangerously-skip-permissions`, preset session ids recorded with pid files in a fleet dir. Each lane runs relentless to its DoD and must message the orchestrator on completion or blockers. Resume kills with `claude -p --resume <session-id>`. |
| **6. Supervise** | A ~30 min loop: lane state from `lane.log` tail + `PROGRESS.md` + `PR_BODY.md` presence ONLY; rule on DECISION comments instead of waiting; launch more lanes as capacity frees; **merge completed lanes within one window** (rebase, full battery, honest conflict resolution). |
| **7. Validate** | Each lane runs prism on its own scope before handback; the orchestrator **looks at UI screenshots itself** before any visual merge; a program-level prism gate runs over the merged wave diff before any release. |
| **8. Release** | Between waves, ship pre-authorized staged releases with post-deploy content QA by fresh-context graders. At program end: the issue-to-evidence report, then flush everything. |

## Lane state is evidence, not liveness

The discipline this skill exists to encode:

- A headless process exits when its turn ends - finished, blocked, and errored are
  indistinguishable from the process table. **Never conclude a lane's state from
  pid-liveness alone.** Read the log tail, the PROGRESS.md head, and check for PR_BODY.md.
- **Never attribute an exit to a cause without log evidence.** "Unknown - reading the log
  now" is a correct status; a fabricated cause is worse than no answer.
- DONE detection: grep the first 10 lines of PROGRESS.md case-insensitively for
  DONE/COMPLETE and check PR_BODY.md exists - formats vary between lanes.
- Lanes are **required** to message the orchestrator on completion and blockers; exiting
  with no marker and no message is a failed handback.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--tracker=<linear\|markdown>` | linear, else markdown | Where the program record lives. No Linear MCP: same fields and discipline in markdown tracker files. |
| `--max-lanes=<n>` | judged per wave | Parallel lane ceiling; the loop re-checks capacity every window. |
| `--cadence=<dur>` | 30m | Supervision loop interval. |
| `--model=<id>` | ask at the plan gate | The pinned lane model. Never launch unpinned. |
| `--gates=<n>` | 0 | Extra human gates beyond plan approval; each must sit on an irreversible or outward-facing step. |

## Requirements

A tracker (Linear via MCP, degrading to markdown tracker files), the `claude` CLI on PATH
with headless `-p`, `--session-id`, and `--resume`, git with worktree support, owner
tolerance for bypass-permissions lanes (bounded by lane charters and the merge gate - lanes
never push, deploy, or touch prod), and an owner reachable async for the single
plan-approval gate. Uses the **relentless** and **prism** skills by name and pairs with
**collapse** (the closing bracket); missing skills degrade to their principles applied
inline.

## Layout

```
plugins/orchestrate/
├── .claude-plugin/plugin.json
├── commands/orchestrate.md          # /orchestrate
└── skills/orchestrate/SKILL.md      # the charter: 8 phases, flags, failure modes to refuse
```
