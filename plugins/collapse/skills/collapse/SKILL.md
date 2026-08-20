---
name: collapse
description: >-
  Closing bracket to a fan-out of autonomous work: converge many parallel lanes into one
  clean main, review the combined diff, and ship it. Use whenever the user says "collapse"
  or "run collapse", or asks you to consolidate/merge parallel worktrees and branches into
  main, wait out other agents/sessions and then merge, "collapse everything into main and
  deploy", cut a clean-slate release, or gather several in-flight streams of work into one
  reviewed, deployed, QA'd whole. Starts as a relentless run on your own lane, then adds a
  convergence + release + live-QA layer. Not for a single quick merge or a one-branch PR you
  will babysit.
---

# Collapse

Relentless builds one lane to shippable. **Collapse is the closing bracket.** It takes a
fan-out of parallel autonomous work (several worktrees, branches, sessions, or devices, each
mid-build) and converges it into a **single clean main**, reviews the *combined* change,
ships it as one clean-slate release, and QAs the live deployment before reporting.

The hard parts are not the merge. They are three. **Knowing when a sibling lane is actually
done** (versus still moving, versus stalled), so you never collapse a moving target or silently
drop a finished one. **Reviewing the union** of all lanes, where the integration bugs that no
single lane saw are hiding. And **shipping a structural change to production safely**, staged
and reversible, without bricking a single point of failure. Be relentless about converging and
rigorous about not shipping the seam between two lanes' work.

This skill assumes the **relentless** skill and the **prism** skill are available and uses them
by name; a companion **e2e-qa-loop** (or similar autonomous-QA) skill, if present, is the
harness for Phase 6. If they are not installed, apply their principles inline: a Definition of
Done, worktree isolation, a self-continuing loop, verified increments, an adversarial review
pass, autonomous end-to-end QA.

---

## Phase 0: Be relentless first

Collapse **is a relentless run**, then more. Everything the relentless charter says applies in
full: lock a checkable Definition of Done, work in an isolated worktree, arm a self-continuing
loop, build in verified increments, map every regression surface, run autonomous end-to-end QA,
harden with a review pass, and leave the tree clean. Collapse only adds a convergence, release,
and live-QA layer on top.

The order matters. **You cannot collapse half-built work.** Get your own lane genuinely done and
green first. A collapse that merges an unfinished lane just spreads the unfinished-ness into
main. If you were invoked to collapse a fleet you did not build, your own lane may be empty and
you go straight to Phase 1; but if you are also building, finish and prove your lane before you
converge anyone's.

Set up two pieces of durable state now, because a collapse outlives context windows and often
runs unattended:

- **`COLLAPSE.md`** at the primary worktree root is the run's memory: the fleet inventory
  (Phase 1), the frozen included set and per-lane merge progress (Phase 3), and the running
  HEAD. Re-read it every window; a resumed loop reconstructs exactly where the collapse stands
  from this file, not from a context window that may be gone.
- **The absent-owner channel.** Collapse's core scenario is a long unattended run, so "stop and
  ask the owner" is a no-op at 3 a.m. unless you make it real. Whenever you hold for a decision
  (the default deploy fork, a contention blocker, a control weaker than planned, an owner-only
  conflict), write it to a durable `DECISION.md` / `BLOCKERS.md` at the worktree root, **fire an
  out-of-band notification** if the harness has one (in Claude Code, `PushNotification`), and
  then act on a stated safe default so no unblocked lane idles against a question no one will
  read.

Read the flags now (full list at the end), because two of them change what Phases 2 and 5 do:
whether stalled sibling lanes are waited on or excluded, and whether the run deploys or stops
with a report.

---

## Phase 1: Map the fleet

Before you merge anything, enumerate **every lane that still has a claim on main**, meaning
every place a change could still arrive that this collapse must either include or knowingly
leave out. Do not merge against a picture you did not take.

- **Worktrees:** `git worktree list`. Each is a lane with its own branch and possibly
  uncommitted state.
- **Branches:** `git branch -a --no-merged main` and `git for-each-ref --sort=-committerdate
  refs/heads`. Every unmerged branch, with how far ahead/behind main it is.
- **Other live sessions / agents:** if your harness can list them (other local sessions, cloud
  runs, teammates' agents), do. Otherwise infer state from the repo: commits, an advancing
  `PROGRESS.md`, and a completion marker if one exists.
- **The base:** record the commit main sits at now, and separately the commit currently
  **deployed to production** (they can differ). The combined diff you review in Phase 4 is
  measured from the base; the incoming-changes the owner cares about (Phases 5 and 7) are
  measured from the deployed commit.

For each lane, write into `COLLAPSE.md`: its branch, its worktree (if any), its ahead/behind
counts, the timestamp and message of its last commit, whether it carries a completion marker
(see Phase 2), and a first read of its state. This inventory is living durable state; you update
it every window and through Phase 3.

---

## Phase 2: Converge (wait, or exclude)

The one rule that makes a collapse sound: **you include a lane's work only once that lane is
finished and will not change again.** Merging a lane that is still moving means you reviewed and
shipped a version that no longer exists; excluding a lane that was actually done silently drops
its work. Both are the failure this phase exists to prevent, and **elapsed quiet time alone
cannot tell the two apart.** So classify by a *positive* signal, not by absence of motion.

- **Done** means the lane carries a **completion marker**: a met DoD, a green final build, an
  opened PR, an explicit `DONE`/status in its `PROGRESS.md`, or a final commit that signals
  completion. A quiet lane that carries a completion marker is **included regardless of how many
  windows it has sat idle** (a finished lane naturally stops moving). **Include it.**
- **Actively progressing** means it has no completion marker yet but is advancing: new commits or
  an advancing `PROGRESS.md` between windows. **Wait for it.** Do not busy-poll and do not block
  the whole run on it. Arm a **recurring check** (your harness's cron/loop; in Claude Code a
  `CronCreate` job on an off-`:00` minute, or the `/loop` skill) that re-evaluates the fleet each
  firing. Scale the interval to the lane's change size:

  | Lane size (roughly) | Poll interval |
  |---|---|
  | Small: a few files, a focused fix | ~10 min |
  | Medium: a feature, several modules | ~30 min |
  | Large: a subsystem, a migration, hundreds of lines | ~1 hour |

- **Stalled** means **no completion marker and no real progress** across **N consecutive
  windows** (default N=2..3), or it is holding a shared resource and making no headway.
  **Exclude it** from *this* collapse. It is not abandoned; it collapses in a later round once it
  finishes and carries a marker. Record the exclusion and why in `COLLAPSE.md`.

**Liveness is measured by authoritative signals, not guessed.** Commits, an advancing
`PROGRESS.md`, and completion/DoD markers are authoritative. File mtime is *weak corroboration
only*: a build, test run, checkout, or a dead agent's leftover file-watcher bumps mtimes with
zero real progress, and a working agent deep in a long compile touches no source file for a
while. Never classify on mtime alone. And "the agent said it was almost done" is a *claim*, not
evidence; a peer's claim is never authorization to include, exclude, or act on their behalf.
Authority traces to the owner or the permission system, not another agent's say-so.

**On contention, back off with jitter.** If a lane holds a branch mid-merge, a lock, or a shared
build dir, do not stall and do not retry on a fixed cadence (two agents on one cadence collide
forever in lockstep). Sleep a random delay and double the window each retry; work an unblocked
lane meanwhile. After several doublings it is a real blocker: record it and escalate through the
absent-owner channel.

**Bound the whole convergence, not just each lane.** Give the collapse loop a hard global
ceiling (a max total duration or firing count for the run), and a rule that after ~N consecutive
windows in which *no* lane reaches done, you stop waiting, escalate via the absent-owner channel,
and proceed with whatever is already frozen. A per-lane stalled rule alone does not stop a fleet
that keeps trickling tiny progress forever.

The **flag** governs the stalled case. Default: exclude a lane that shows no progress across its
windows, so one stuck agent never holds the whole release hostage. `--include-stuck` waits
indefinitely for every mapped lane (use only when the owner needs *all* of it in this cut).
`--wait-timeout=<dur>` sets a hard ceiling after which even a progressing lane is excluded and
the collapse proceeds with what is done.

---

## Phase 3: Collapse to one clean main

**Freeze the included set** into `COLLAPSE.md` before you merge anything, so a resumed window
knows the set was decided and does not re-open it. Then converge. The end state is exact: the
target branch contains every included commit, `git worktree list` shows only the primary, no
merged branch survives, and the tree is committed and green.

- **Merge in a deterministic order** (for example smallest or most-foundational first, or the
  order the lanes were based), one lane at a time.
- **After every single merge, re-verify green:** build, lint, the test pyramid to the rung the
  merged change warrants. Not once at the end. If merge #4 breaks the build you want to know it
  was #4, not bisect a pile. A red step stops the collapse until it is fixed honestly.
- **Record each merge in `COLLAPSE.md`** as you go: which lane merged, its green-verification
  result, and the running HEAD. A context reset after merging 3 of 6 lanes must resume knowing
  the set is frozen and exactly which lanes already landed.
- **Resolve conflicts by understanding, never by reflex.** A blind `-X theirs` / `-X ours` or an
  "accept all incoming" silently drops one lane's work, the exact failure this skill exists to
  prevent. Read both sides, keep the union of intent, and if two lanes genuinely contradict, that
  is an owner decision (escalate through the absent-owner channel), not a coin flip.
- **Then flush the fleet:** remove each merged worktree (`git worktree remove`), delete each
  merged branch, and confirm `git worktree list` and the branch list show only what should
  remain. A collapse that leaves orphan worktrees or a red main has not collapsed anything; it
  just re-collides next round.

**If the owner's workflow uses PRs** rather than direct merges: converge the included lanes onto
one collapsed branch and open a single PR against the target. Then the whole tail changes shape.
The Phase 4 review gate runs on the PR branch; **merging the PR is an owner action** (or an
explicitly authorized class under `--auto-deploy`); and the Phase 5 deploy and Phase 7 report
anchor to the **PR-merge commit**, not a preexisting target-branch tag. Do not cut a release off
the target branch until the PR has landed, or you would deploy stale code without the collapsed
work.

---

## Phase 4: Refract the combined diff through prism

The target now holds the **union** of every included lane. Review *that*, `origin/main..HEAD` (or
the Phase-1 base..HEAD, or the PR diff), because the cross-lane interactions are precisely what
no single lane's own review ever saw: two features touching the same gate, a shared helper
changed two ways, a migration from one lane and code from another that assume different schemas.

Run **prism** in PR mode over the full combined diff, security and correctness weighted.
Adversarially verify each finding (confirmed / plausible / refuted), **fix every confirmed one**,
and re-verify after each fix. A review whose findings you do not act on was theater. The combined
diff is where the integration bugs live; give it the hard look.

---

## Phase 5: Ship it, or hold with a report

This is the fork the owner controls with the deploy flag.

**Default (`--auto-deploy` off): stop and hand the owner a decision.** Do not deploy. Produce a
decision report (reuse the incoming-changes-summary and prism-criticals sections from Phase 7,
plus the deploy plan and any owner-input gates), and wait for an explicit go. Make it a
*decision*: the options, your recommendation, and what you will do by default. Deliver it through
the absent-owner channel (durable file + out-of-band notification), because in an unattended run
no one is watching the terminal. **An explicit owner go authorizes running the same staged "ship
it safely" sequence below, then Phase 6 live QA, then the Phase 7 final report** (the go resumes
the run into deploy, it does not end it). This is the honest posture for anything production and
irreversible.

**With `--auto-deploy`: ship, but auto-deploy authorizes the routine release, not every risky
substep.** A genuinely dangerous or irreversible step still gets confirmed first (through the
absent-owner channel) unless the owner pre-authorized *that class* of action: a schema migration
on a prod database, turning on a user-facing gate, a broad IAM grant, the first-ever run of an
unproven pipeline, anything that spends or is outward-facing.

However you ship, ship it **safely**. The principles are stack-agnostic; the examples are just
examples.

- **Clean-slate release.** The target branch is the single source of truth, and one release
  point drives the deploy (whatever your target ships: container images, packages, serverless
  functions, a static bundle, plus any infrastructure), so the deployed state traces to exactly
  one commit. This is the clean slate a collapse is for.
- **Dependency order.** Deploy what later steps need first: the data layer, and any outbound or
  network dependency a service will call, before the service that calls it.
- **Staged, with verification at each step.** Never a big-bang apply of everything at once. Roll
  one component, prove it healthy, then the next. Reconcile what "deploy" actually changes: if
  production is many commits behind, a deploy may be a *structural* change (new infra, a schema
  migration, a user-facing gate going live), not a version bump. Treat it as such and tell the
  owner so.
- **Sequence migrations by direction (expand/contract).** Snapshot or back up before any schema
  step. An **additive/expand** migration (new table, new nullable column) runs as a separate
  verified job *before* the new app rolls, so a migration failure never takes the app down with
  it. A **destructive/contracting** migration (drop, rename, narrow, tighten to NOT NULL) is the
  opposite: running it while the old app is still serving breaks the live app the instant it
  *succeeds*, a self-inflicted outage. Run destructive steps only *after* the new app is fully
  rolled and no live instance still references the old schema, and defer the drop behind its own
  verified follow-up (the standard expand-then-contract, parallel-change pattern). Keep a
  rollback path (previous artifact, restore point) and then earn never needing it by verifying
  forward.
- **Hold back the parts that can brick a single point of failure.** Any change that **fails
  closed** can take the whole service down if one value is wrong: a default-deny firewall or
  network rule, an auth or admission gate that rejects by default, a required migration the app
  cannot boot without. The risk is worst on a single instance or node. Deploy the safe majority
  now and stage the fail-closed parts behind their own verified follow-up (fill the real values,
  apply, functional-test, keep an instant rollback). Deferring the bricking parts to a verified
  pass is correct sequencing, not corner-cutting. Say clearly which parts you deferred and why.
- **Define what happens when a stage fails mid-deploy.** This is the most dangerous moment and
  needs a rule, not improvisation. On a failed stage: stop advancing, and never fold the failure
  into a green claim. If the failed step is reversible, roll that component back and re-verify. If
  an already-applied irreversible step (an expand migration, a data write) blocks a clean
  rollback, halt in a known-safe partial state and escalate through the absent-owner channel with
  the *exact* residual state (what is live, what is not, what is half-applied). Leaving production
  in an unreported half-deployed state is itself a failure.
- **Report honestly when a control is weaker than intended.** If a gate you planned (a required
  reviewer, an approval) is not actually available (a plan limit, a missing permission), do not
  pretend it exists. Say so, install the strongest control that *does* work, and record the gap.
  What you found contradicting how it was described is exactly what the owner needs to hear.

---

## Phase 6: QA the live deployment

A green pipeline is not a working product. After deploying, **you, the orchestrator, run QA
against production**, the real thing, not the test suite that already passed. If an
**e2e-qa-loop** (or relentless's autonomous E2E QA) skill is available, use it as the harness
rather than reinventing one. For each acceptance criterion, verify it landed on prod with
evidence (each item below applies only where your product has that surface):

- **Versions rolled.** The deployed artifacts are the collapsed commit, healthy, no restart
  loops or crash cycles, a clean startup log.
- **Data and schema** (if stateful). Migrations applied and the new objects actually exist (query
  the live store; do not infer from "migrate said ok").
- **Every public surface green.** Each endpoint, page, and control a user touches, including the
  newly shipped ones. Verify *content*, not just a 200: a status code is not proof the right
  thing is served (a catch-all fallback can return 200 with the wrong page).
- **Security boundaries hold.** Auth and permission gates reject the negative case; secrets/keys
  are where they should be and nowhere they should not; the boundary on any new service returns
  the rejection you expect without credentials.
- **New user-facing behavior is live**, and **anything shipped-off is actually off** (a
  feature-flagged-off subsystem creates no state and makes no calls).

Drive it black-box, as a real user would. **Fan out fresh-context subagents as independent
graders**, each on a different surface, because the agent that shipped it is the worst-positioned
to see what it broke, and an independent grader catches the "200 means it works" that
self-assessment rationalizes past. For anything with model output or fuzzy correctness, judge
*quality*, not just liveness. Wait for async flows honestly; never call a flow you did not watch
finish. And **distinguish what is verifiable now from what is gated on an owner action** (a
dormant feature awaiting keys, a flow needing a real account, a surface on a pipeline you cannot
credential) and say which is which, rather than claiming a green you could not observe.

Every issue you find, fix and re-verify (and confirm the fix did not break a neighbor).
Pre-existing issues outside this collapse's scope you log for the owner; you do not fold them in.

---

## Phase 7: Final report, then leave it clean

Send the owner the report the whole run was building toward, through the absent-owner channel so
it lands whether or not anyone is watching:

- **What shipped** to production, with the **evidence** each acceptance criterion is met (the QA
  result, the query output, the screenshot), not "it works" but the proof. (In a hold-only run
  that never deployed, this section is the deploy plan awaiting a go, not a shipped list.)
- **Incoming-changes summary:** the features, fixes, and architecture changes now live, measured
  from the **commit that was deployed to production** (not the internal collapse base), because
  "incoming" means new relative to what users had. If prod was many commits behind, say so.
- **Prism criticals:** the confirmed findings and how each was resolved.
- **Deliberately excluded or deferred:** which sibling lanes were left out (stalled) and which
  hardening or steps were staged for a follow-up, each with its reason.
- **Residual owner-only items:** the follow-ups only the owner can do (place keys, enable a
  dormant feature, upgrade a plan to get a gate, deploy a surface on a pipeline you lack
  credentials for, eyes-on a physical device).

Then **flush everything.** Cancel the recurring collapse loop/cron the moment nothing is pending
(a loop left armed re-fires and re-collides), remove any worktrees you created, and confirm the
target is the branch of record and it is green. The clean slate the owner asked for is part of
"done," not an afterthought.

---

## Flags

Collapse reads these from the invocation (or the owner's stated intent). Default to the safe
choice when unspecified and state which you assumed.

- **`--auto-deploy`**: ship after the review gate. **Default: off** (stop after Phase 4 and hand
  the owner a decision report; an explicit go then resumes into staged deploy + live QA + final
  report). Even on, dangerous or irreversible substeps still confirm first unless that class was
  pre-authorized.
- **`--include-stuck`**: wait indefinitely for every mapped lane, including stalled ones.
  **Default: off** (a lane with no progress and no completion marker across its windows is
  excluded from this round so one stuck agent cannot hold the release hostage).
- **`--wait-timeout=<dur>`**: a hard ceiling on the convergence wait; after it, proceed with
  whatever is done, excluding the rest. **Default: none** (bounded instead by the stalled-lane
  rule and the global loop ceiling).
- **`--qa-spend=<amount>`**: the ceiling for paid QA calls against prod. **Default:
  conservative**; stop and ask before any single or cumulative spend that would be materially
  expensive. Verification spend only, never purchases or deploys.
- **`--target=<branch>`**: the branch everything collapses into. **Default: `main`.**

---

## Failure modes to refuse

- **Collapsing a moving target.** Merging a lane that is still committing means you reviewed and
  shipped a version that no longer exists. Include only lanes that carry a completion marker.
- **Silently dropping a finished lane.** Classifying a done-but-quiet lane as "stalled" on
  elapsed time alone excludes real work. Done is a positive signal, not the absence of motion.
- **Blind conflict resolution.** `-X theirs` / `-X ours` / "accept all incoming" to make a merge
  go through silently drops a lane's work, the precise thing this skill prevents.
- **Big-bang production deploy.** Applying every change and migration at once, including the
  fail-closed parts that brick a single point of failure, because it was "all one release." Stage
  it; defer the bricking parts to a verified pass.
- **A destructive migration while the old app serves.** Running a drop/rename/tighten before the
  new app rolls is a self-inflicted outage, not just a failure risk. Expand before, contract
  after.
- **Leaving prod half-deployed and unreported.** A stage failed, an irreversible step already
  applied, and the run walked away without halting in a known state and escalating the exact
  residual.
- **Declaring done from a green pipeline.** A successful deploy job is not a QA'd product, and a
  200 is not proof the right content is served. If you did not exercise it on prod, you did not
  verify it.
- **Pretending a control exists.** Claiming a gate, approval, or boundary that the plan or
  permissions do not actually provide. Report the gap and install the strongest real control.
- **Idling against a question no one will read.** In an unattended run, "wait for the owner"
  without a durable file and an out-of-band notification is a silent stall. Escalate for real,
  then act on the safe default.
- **Leaving the fleet armed.** A live collapse loop or scattered worktrees re-collide on the next
  round. Flush them, or you have not finished.
- **Every relentless failure mode still applies:** faking green, confusing effort with evidence,
  declaring done before the DoD is met, drifting into unrequested scope. Collapse does not relax
  any of them; it adds more surface to get them wrong on.
