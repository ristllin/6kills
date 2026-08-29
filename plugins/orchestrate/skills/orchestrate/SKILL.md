---
name: orchestrate
description: >-
  Opening bracket to a fleet of autonomous work: turn a raw requirements list into a running
  multi-lane program. Interrogates the owner on every ambiguity first, writes a PRD, converts
  it into a dependency-ordered tracker split into waves of non-conflicting parallel lanes,
  sets up and launches each lane as a detached headless worker running relentless to a frozen
  Definition of Done, supervises on a recurring loop with evidence-based lane state, merges
  finished lanes within one window, gates each wave with review and personal visual QA, and
  ships pre-authorized releases between waves. Use whenever the user says "orchestrate" or
  "run orchestrate", or asks you to plan and launch a big program from scratch, split a
  backlog or spec into parallel agents/lanes, or take a requirements dump to a shipped
  release with minimal human gates. Not for one task (use relentless) and not for converging
  an already-running fleet (use collapse).
---

# Orchestrate

Relentless runs one lane to shippable. Collapse is the closing bracket that converges a
fan-out. **Orchestrate is the opening bracket**: it takes a raw requirements list and turns
it into a running program - clarified requirements, a PRD, a dependency-ordered tracker
split into waves, isolated lanes launched as detached headless workers, a supervision loop
that merges finished work within the window, validation gates, and releases between waves.

The hard parts are not the launch. They are three. **Resolving ambiguity before the fleet
exists**, because twelve autonomous lanes amplify one wrong guess twelve-fold and a frozen
DoD built on a guess ships the wrong program very efficiently. **Truthful supervision**:
knowing each lane's real state from evidence in its logs and progress files, never from
process tables, wishful memory, or a fabricated cause. And **merge cadence**: a finished
lane merged within one supervision window, because completed work sitting unmerged for
hours rots against a moving base and is an orchestrator failure, not a lane failure.

This skill assumes the **relentless** skill (each lane's operating charter) and the
**prism** skill (the review gates) are available and uses them by name; **collapse** is the
sibling that converges a fleet you did not launch. If any are missing, apply their
principles inline: a frozen Definition of Done per lane, worktree isolation, self-continuing
work, adversarial review, evidence over claims.

---

## Prerequisites (state them, then degrade gracefully)

Check these at the start and tell the owner which mode you are in. Missing pieces change
the mechanics, never the discipline.

- **A tracker.** Linear via MCP (or an equivalent issue tracker) for projects, issues,
  frozen DoDs, evidence comments, and DECISION threads. **No tracker: degrade to markdown**
  - a `program/TRACKER.md` board plus one `lanes/<id>/ISSUES.md` per lane, same fields,
  same evidence discipline. The tracker is the program's shared memory; the tool is
  negotiable, the record is not.
- **The `claude` CLI on PATH**, able to run headless (`claude -p`) with `--session-id` and
  `--resume`. No headless CLI: lanes run as subagents or interactive sessions the owner
  starts by hand from prompts you write; supervision stays identical.
- **git** with worktree support, one repo (or several) the lanes will share via worktrees.
- **Owner tolerance for bypass-permissions lanes.** Headless lanes stall forever on
  permission prompts, so the launch uses `--dangerously-skip-permissions`, bounded by the
  lane charter's hard limits and the merge gate (lanes never push, deploy, or touch prod).
  If the owner does not accept that, run lanes interactive or with allowlists and accept
  the throughput cost - say so up front.
- **An owner reachable async** for exactly one default gate: plan approval. Everything else
  runs on rulings you make and record.
- **Nice to have:** cross-session messaging (SendMessage) for lane report-ins, a cron or
  scheduled-task mechanism for the supervision loop (else `/loop` or a manual cadence), a
  push-notification channel for the absent owner, and a lock directory if hardware or any
  other exclusive resource is involved.

---

## Phase 1: Interrogate the requirements

Start from the raw requirements list, however messy. Before any planning, PRD writing, or
tracker creation, **ask the owner clarifying questions on every ambiguous step**. Not the
relentless posture of "one batched round then decide alone" - that is correct for one lane,
and wrong here, because every unresolved ambiguity gets frozen into N lanes' DoDs and
multiplied.

- Read the whole list first. For each item, ask: could two competent builders ship
  different things from this line? If yes, it is ambiguous. Scope boundaries, priority
  conflicts, irreversible or outward-facing steps, hardware and account dependencies,
  budget ceilings, and "obvious" defaults the owner may not share are all ambiguous until
  answered.
- Put the questions in **one numbered list**, grouped by requirement, each with your
  proposed default so the owner can answer "yes to all defaults except 4 and 9" in one
  message. Include the questions whose answers change the wave structure (what depends on
  what, what must not run in parallel, what the owner insists on seeing before it ships).
- **Wait for the answers.** This is the one place orchestrate genuinely stops. Do not
  begin Phase 2 on guesses; a program plan built on unanswered questions is the expensive
  version of not asking.
- Record every answer verbatim in a durable `program/DECISIONS.md`. These are load-bearing
  rulings the whole program will cite.

---

## Phase 2: Write the PRD

From the requirements plus the answers, write the PRD - **slowly and completely**. This
document is what every lane's TASK.md is cut from, so thin PRD sections become thin DoDs
become lanes that stop at "looks done".

The PRD covers, per feature area: the user-visible behavior with checkable acceptance
criteria (a starting state, an action, a measurable outcome - adjectives are not
criteria), the surfaces in scope and the surfaces that must not regress, explicit
non-goals, quality bars including output quality for anything model-generated, error and
edge behavior, and how each criterion will be verified (the exact command, endpoint, or
QA step). Program-wide: the architecture seams, the contracts between areas (endpoint
schemas, formats, naming), budgets (API spend, time), release policy, and the owner's
answers folded in with their DECISIONS.md references.

Write it to `program/PRD.md`. It changes only by an owner ruling recorded in
DECISIONS.md, never silently.

---

## Phase 3: Convert to the tracker (waves, lanes, frozen DoDs)

Turn the PRD into a dependency-ordered program:

- **Derive the dependency graph** between work items: who produces a contract, who
  consumes it, what shares files, what needs hardware, what must land before a release.
- **Split into waves of parallel, non-conflicting lanes.** A lane is a coherent scope one
  autonomous worker can own end to end. Two lanes in the same wave must not write the same
  files - shared-file work goes in the same lane, in a later wave, or behind an explicit
  contract where one lane owns the file and the other requests changes. Sequencing by
  genuine file overlap is deliberate design, not lost parallelism.
- **Create the tracker structure**: one project per lane, issues per acceptance criterion
  cluster, each issue carrying a **frozen Definition of Done and its evidence
  requirement** (test names and output markers, screenshot paths, the command a reviewer
  can run). No evidence, no Done - freeze that rule into every issue.
- **Contracts get issues of their own**: the producing lane posts the contract on the
  named issue within its first working day and keeps it stable; consumers build against a
  stub until it lands.
- **Human gates: default 0 to 1.** Plan approval - the owner reads the PRD plus the
  wave/lane plan and says go - is the only default gate. Add another gate ONLY where a
  step is irreversible or outward-facing and a human check is genuinely mandatory (a live
  payment, a public launch, a destructive migration). Every additional gate is a place the
  program idles against an absent owner; HITL creep is a failure mode, not diligence.
  Everything else runs on recorded rulings.

Present the plan (PRD summary, waves, lanes, gates, budgets) to the owner. **This is the
plan-approval gate.** On go, freeze it.

---

## Phase 4: Set up each lane

Per lane, before launch:

- **A git worktree on its own branch**: `git worktree add lanes/<id>/<repo> -b lane/<ID>`
  off the frozen wave base. Record the base commit. **Copy untracked environment files in**
  (`.env` and friends) - worktrees do not inherit gitignored files, and a lane discovering
  missing keys mid-run wastes a window on a stale negative.
- **`lanes/<id>/TASK.md`**, the lane's frozen charter: the DoD copied from the tracker
  (never paraphrased), the **file-ownership contract** naming what this lane owns and what
  concurrent lanes own (needing a change in another lane's files is a contract request,
  not an edit), **prod-care rules** (never push, tag, deploy, publish, or touch live
  services or paid production accounts; test keys only; secrets masked in all output),
  the **battery definition** (the exact build, lint, and test commands with the expected
  green markers the lane must paste as evidence), the **evidence discipline** (every
  issue closes with evidence; DONE goes atop `PROGRESS.md`; a `PR_BODY.md` is written at
  completion for the merge commit), spend budget, and the orchestrator session's name.
- **A lane charter skill** (the fleet-lane pattern): one program-specific skill every lane
  invokes at start, holding the rules shared by all lanes - tracker conventions, contract
  protocol, coordination channels, deletion discipline (`rm -rf` inside a project tree
  trips a hard guardrail that fails headlessly - worktrees via `git worktree remove`, else
  mv-out-then-delete), report-in duties, and hard boundaries. One skill, not N copies in N
  TASK.md files, so a rule fix lands everywhere at once.
- **A device/resource lock protocol if hardware (or any exclusive resource) is involved**:
  a shared map file naming ports/resources, atomic lock files with owner and timestamp
  JSON, random-jitter backoff on contention with doubling windows, a max hold, and a stale
  reclaim age. Any flash/restore/erase of a physical device runs as a detached standalone
  script that completes or fails atomically on its own, so a lane death can never
  interrupt a write mid-flash.
- **Pre-land shared scaffolding on the base before launch** - test tiers, e2e harnesses,
  shared fixtures. Scaffolding that arrives after launch forces every lane to cherry-pick
  it mid-run. And capture the baseline: run the battery on the base now; pre-existing reds
  are inherited, not lane regressions - judge lanes on their own files.

---

## Phase 5: Launch the fleet

Lanes are **detached headless OS processes**, launched by the orchestrator, not by the
owner:

```sh
FLEET=/tmp/<program>-fleet && mkdir -p "$FLEET"
SID=$(uuidgen | tr 'A-Z' 'a-z') && echo "$SID" > "$FLEET/<id>.session"
nohup claude -p "You are lane <id> of program <name>. Invoke the <lane-charter> skill, \
read lanes/<id>/TASK.md, and run relentless to its frozen DoD. Report completion and \
blockers to the orchestrator session by SendMessage." \
  --model <pinned-model-id> \
  --session-id "$SID" \
  --dangerously-skip-permissions \
  >> lanes/<id>/lane.log 2>&1 &
echo $! > "$FLEET/<id>.pid"
```

- **Pin the model explicitly** on every launch - never let a lane float on an alias that
  resolves differently tomorrow.
- **Preset the session id and record it** with the pid in the fleet dir. The session id is
  the resume handle: a dead or cap-killed lane comes back with
  `claude -p --resume "$(cat $FLEET/<id>.session)" "Resume your lane: re-read TASK.md and
  PROGRESS.md, verify real state, continue."` plus the same model and permission flags.
  Cap kills and crashes are survivable precisely because state lives in the repo and the
  tracker, not in the process.
- Each lane **runs relentless** inside its worktree to its frozen DoD, and is **required
  to SendMessage the orchestrator** on completion, on any blocker needing a ruling, and
  when another lane needs a contract from it. The orchestrator does not watch stdout;
  a lane that exits with no marker and no message is a failed handback, and the charter
  skill says so.
- After each launch, **verify exactly one process per lane** and a first log line in
  `lane.log`. A launcher pointed at an unknown lane name with a leftover worktree can
  spawn a defective duplicate; catch it now, kill the impostor, keep the one with the
  correct TASK.md.
- Headless lanes do not arm their own crons; **the supervision loop is their continuation
  guarantee**. Keep the machine awake for the duration (`caffeinate -dims &` with its pid
  recorded for the flush list).

---

## Phase 6: Supervise on a loop

Arm a recurring orchestrator loop (cron or scheduled task, roughly every 30 minutes,
off-`:00`) whose prompt re-reads the program state fresh each firing. Each window:

- **Determine lane state from evidence ONLY**: the tail of `lanes/<id>/lane.log`, the head
  of `PROGRESS.md`, and the presence of `PR_BODY.md`. **NEVER from pid-liveness alone.** A
  headless process exits when its turn ends - finished, blocked, and errored all look
  identical from `ps`. DONE detection: grep the first 10 lines of PROGRESS.md
  case-insensitively for DONE or COMPLETE, and check PR_BODY.md exists - formats vary
  between lanes.
- **Never claim a cause without log evidence.** "Unknown - reading the log now" is a
  correct status; a fabricated cause ("probably the usage cap") is worse than no answer
  and is the exact failure this discipline exists to prevent. If the owner asks how the
  fleet is doing, the answer comes from the logs you just read, not from the last picture
  you remember.
- **Answer DECISION comments with rulings.** Decide, record "DECISION:" with your default
  and reasoning on the issue, and keep the lane moving. The owner overrides
  asynchronously; a lane idling against a question is a supervision failure.
- **Launch more lanes when capacity frees.** The launch-more check lives inside the loop
  prompt itself, so parallelism is re-examined every window, not only when you remember.
  Respect the wave plan's file-overlap sequencing when picking what launches next.
- **Merge completed lanes within ONE window.** Spot-check the evidence against the DoD
  (claims are not evidence - re-run a check if it smells stale), rebase onto the wave
  base, run the full battery with pasted markers, resolve conflicts by understanding both
  sides - never a blind `-X ours`/`-X theirs`, and never a mechanical union of
  non-list hunks; batteries catch some blind-union breakage, but understanding prevents
  it - then merge with `PR_BODY.md` as the commit body, close the tracker project, remove
  the worktree. A red battery stops the merge until fixed honestly.
- Resume dead lanes via their session ids; give a silent-but-live lane a nudge message;
  after three windows with no real progress and no marker, treat it as stalled - message
  it, and if it stays stalled, take the work over in its worktree or re-lane it. Reclaim
  resource locks older than the stale age. Resumed sessions get new peer names -
  re-list agents before messaging.
- Persist everything to a running `program/RUN.md` (window log, merge log, rulings), the
  program's durable memory across your own context resets.

---

## Phase 7: Validate

Two layers, neither optional:

- **Each lane runs prism on its own scope before handback** - the four-lens self-review is
  part of the lane's DoD, and findings get fixed, not filed.
- **The orchestrator personally validates UI work.** For any change with a visual surface,
  drive it in a browser or take the lane's Playwright screenshots and **look at the images
  yourself** (open them with the Read tool) before merging. A passing selector is not a
  correct screen, and a lane grading its own screenshots is the fox auditing the henhouse.
- **Optional program-level prism gate between waves**: before any prod or dev release, run
  prism over the merged wave diff - yours, not a rerun of the lanes' self-reviews, because
  cross-lane integration bugs live in the union no single lane ever saw. Adversarially
  verify each finding, fix the confirmed ones, re-run the battery.

---

## Phase 8: Release between waves

If the owner pre-authorized releases at the plan gate, ship between waves rather than
hoarding everything for the end - real users on wave N find what wave N+1 should fix.

- Tag and deploy through the project's own release mechanism, staged and reversible, with
  the rollback path named before you roll. Anything the plan marked as a mandatory human
  gate (a live payment, a public announcement, a destructive migration) still waits for
  its gate.
- **Post-deploy content QA by fresh-context graders**: fan out subagents that saw none of
  the build to exercise the live deployment black-box, checking content, not status codes
  - a catch-all can serve 200 with the wrong page. Every issue found is fixed and
  re-verified or explicitly logged for the next wave.
- Then the next wave launches on the new base, and the loop continues until the program's
  DoD is met. At program end: final report mapping every issue to its evidence, then flush
  - loops cancelled, worktrees removed, locks and fleet dirs cleared, caffeinate killed,
  any program credentials rotated per the plan.

---

## Flags

Read these from the invocation or the owner's stated intent; default safe and say which
you assumed.

- **`--tracker=<linear|markdown>`**: where the program record lives. **Default: linear**
  if the MCP is reachable, else markdown (announce the fallback).
- **`--max-lanes=<n>`**: parallel lane ceiling per wave. **Default: judge from the
  machine and the wave plan**; the loop re-checks capacity every window.
- **`--cadence=<dur>`**: supervision loop interval. **Default: 30m.**
- **`--model=<id>`**: the pinned lane model. **Default: ask at the plan gate**; never
  launch unpinned.
- **`--gates=<n>`**: additional human gates beyond plan approval. **Default: 0**; each
  one must be tied to an irreversible or outward-facing step, or it is HITL creep.

---

## Failure modes to refuse

- **Planning on guesses.** Skipping the Phase 1 interrogation, or asking and not waiting,
  freezes your assumptions into N lanes' DoDs. The fleet will build the wrong thing with
  total conviction.
- **Fabricating lane state.** Reporting a lane as running, cap-killed, or blocked from
  pid-liveness or memory instead of reading its log and PROGRESS.md. Finished, blocked,
  and errored are indistinguishable from `ps`; only the evidence files can tell you, and
  inventing a cause is worse than "unknown - reading the log now".
- **Sitting on finished work.** A completed lane unmerged past one supervision window rots
  against a moving base and stalls its dependents. Merge cadence is an orchestrator duty.
- **Overlapping lanes.** Two same-wave lanes writing the same files ends in silent
  overwrites or coin-flip conflict resolution. File overlap is resolved in the plan, by
  sequencing or contracts, never at merge time.
- **Blind conflict resolution.** `-X ours`, `-X theirs`, accept-all-incoming, or a
  mechanical union of non-list hunks silently drops or breaks a lane's work. Read both
  sides; keep the union of intent; a genuine contradiction is an owner-recorded ruling.
- **Trusting claims over evidence.** A lane's "done" without the evidence its DoD names,
  a peer's "almost finished", a stale negative ("the file does not exist") never
  re-checked. Spot-check before every merge; re-run checks that matter.
- **Merging on a red battery.** A red battery stops the merge, full stop. Weakening a
  check to get to green is faking green, and every relentless failure mode applies to the
  orchestrator too.
- **Skipping your own eyes on UI.** Merging visual work on a green selector without
  looking at the screenshots yourself.
- **HITL creep - or gate deletion.** Adding approval gates to routine steps parks the
  program against an absent owner; removing the plan-approval gate launches a fleet on an
  unratified plan. Zero to one gates, at the irreversible edges only.
- **Idling against a question.** Every hold gets a durable file, an out-of-band
  notification if available, a recorded default, and continued progress on everything
  unblocked. Never let a fleet sleep on a question no one will read.
- **Leaving the fleet armed.** Loops firing after the program ends, orphan worktrees,
  stale locks, an awake machine no one needs. The flush list is part of done.
