# 🌀 collapse

**Relentless builds one lane to shippable. Collapse is the closing bracket.**

It takes a fan-out of parallel autonomous work (several worktrees, branches, sessions, or
devices, each mid-build), converges it into a **single clean `main`**, reviews the *combined*
change, ships it as one clean-slate release, and QAs the live deployment before reporting.

The merge is the easy part. The hard parts are three:

- **Knowing when a sibling lane is actually done**, versus still moving, versus stalled, so you
  never collapse a moving target and never silently drop a finished one.
- **Reviewing the union** of every lane, where the integration bugs that no single lane's own
  review ever saw are hiding.
- **Shipping a structural change to production safely**, staged and reversible, without bricking
  a single point of failure.

## Install

```
/plugin marketplace add ristllin/6kills
/plugin install collapse@6kills
```

## Usage

```
collapse                                    # converge the task in play, review, hold for a go
/collapse "converge the auth work into main"
/collapse --auto-deploy                     # ...and ship a staged release, then QA production
```

Called with no arguments, it uses the task already established in the conversation. If there is
none, it asks for the goal, the lanes to converge, and the deploy policy, then stops.

## The seven phases

| Phase | What happens |
|---|---|
| **0. Be relentless first** | Collapse *is* a relentless run, then more. Definition of Done, isolated worktree, self-continuing loop, verified increments, autonomous QA. Half-built work cannot be collapsed. Sets up `COLLAPSE.md` (durable run memory) and the absent-owner channel. |
| **1. Map the fleet** | Enumerate every lane that still has a claim on `main`: worktrees, unmerged branches, other live sessions. Record the base commit **and** the commit actually deployed to production, which are often different. |
| **2. Converge** | Include a lane only once it is finished and will not change again. Wait out lanes that are still advancing; exclude ones that are stalled. |
| **3. Collapse to one clean main** | Freeze the included set, merge one lane at a time in a deterministic order, re-verify green after **every** merge, then flush the worktrees and branches. |
| **4. Refract through prism** | Run prism in PR mode over the full combined diff, adversarially verify each finding, and fix every confirmed one. |
| **5. Ship it, or hold** | Default: stop and hand the owner a decision report. With `--auto-deploy`: a staged clean-slate release. |
| **6. QA the live deployment** | A green pipeline is not a working product. Exercise production black-box with fresh-context grader subagents. |
| **7. Final report** | What shipped with evidence, incoming-changes summary, prism criticals, what was excluded or deferred, owner-only follow-ups. Then cancel the loop and leave the tree clean. |

## Done is a positive signal, not the absence of motion

This is the rule that makes a collapse sound. Elapsed quiet time cannot tell a finished lane from
a dead one, so classification never rests on it:

- **Done**: the lane carries a **completion marker** (a met DoD, a green final build, an opened
  PR, an explicit `DONE` in its `PROGRESS.md`, a final commit that signals completion). A quiet
  lane with a marker is included **regardless of how long it has sat idle**, because a finished
  lane naturally stops moving.
- **Actively progressing**: no marker yet, but new commits or an advancing `PROGRESS.md` between
  windows. Waited on via a recurring check scaled to the lane's size (roughly 10 minutes for a
  focused fix, 30 for a feature, an hour for a subsystem), never a busy-poll.
- **Stalled**: no marker and no real progress across N consecutive windows. Excluded from *this*
  round and recorded with a reason, so one stuck agent cannot hold the release hostage. It
  collapses in a later round once it finishes.

Commits, an advancing `PROGRESS.md`, and completion markers are authoritative. File mtime is weak
corroboration only, since a build or a dead agent's file-watcher bumps mtimes with zero progress.
A peer agent's claim that it is "almost done" is a claim, not evidence, and never authorization to
act on its behalf.

## Shipping safely

Under `--auto-deploy`, the release is staged rather than big-bang, and auto-deploy authorizes the
routine release, not every risky substep. A prod schema migration, a user-facing gate going live,
a broad IAM grant, or the first run of an unproven pipeline still gets confirmed unless that class
was pre-authorized.

- **Dependency order.** Deploy what later steps need first.
- **Expand before, contract after.** Additive migrations run as a verified job *before* the new
  app rolls. Destructive ones (drop, rename, tighten to `NOT NULL`) run only *after* the new app
  is fully rolled, deferred behind their own verified follow-up. Running a destructive migration
  while the old app still serves is a self-inflicted outage the instant it succeeds.
- **Hold back what fails closed.** A default-deny rule, an admission gate, a migration the app
  cannot boot without: any of these can take the whole service down if one value is wrong. Ship
  the safe majority, stage the bricking parts behind a verified pass, and say which were deferred.
- **Define the mid-deploy failure rule.** Stop advancing, roll back what is reversible, and if an
  applied irreversible step blocks a clean rollback, halt in a known-safe state and escalate the
  *exact* residual. Leaving production half-deployed and unreported is itself a failure.

## The absent-owner channel

Collapse's core scenario is a long unattended run, so "stop and ask the owner" is a no-op at
3 a.m. unless it is made real. Every hold (the default deploy fork, a contention blocker, a
control weaker than planned, a conflict only the owner can settle) is written to a durable
`DECISION.md` / `BLOCKERS.md`, fired as an out-of-band notification if the harness has one, and
then acted on via a stated safe default, so no unblocked lane idles against a question nobody is
reading.

## Flags

| Flag | Default | Effect |
|---|---|---|
| `--auto-deploy` | off | Ship after the review gate. Off means stop at Phase 4 with a decision report; an explicit go resumes the same run into staged deploy, live QA, and the final report. |
| `--include-stuck` | off | Wait indefinitely for every mapped lane, stalled ones included. Use only when the owner needs *all* of it in this cut. |
| `--wait-timeout=<dur>` | none | Hard ceiling on the convergence wait. After it, proceed with whatever is done. |
| `--qa-spend=<amount>` | conservative | Ceiling for paid QA calls against prod. Verification spend only, never purchases or deploys. |
| `--target=<branch>` | `main` | The branch everything collapses into. |

## Requirements

Collapse uses the **relentless** and **prism** skills by name, and a companion **e2e-qa-loop**
(or similar autonomous-QA skill) as the Phase 6 harness. If any are missing, it applies their
principles inline: a Definition of Done, worktree isolation, a self-continuing loop, verified
increments, an adversarial review pass, autonomous end-to-end QA.

## Layout

```
plugins/collapse/
├── .claude-plugin/plugin.json
├── commands/collapse.md          # /collapse
└── skills/collapse/SKILL.md      # the charter: 7 phases, flags, failure modes to refuse
```
