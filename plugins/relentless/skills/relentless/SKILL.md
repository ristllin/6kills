---
name: relentless
description: >-
  Operating charter for long, unattended, autonomous build-and-ship tasks — ones that
  outlast a single context window and must end genuinely shippable and regression-free.
  Use whenever the user says "relentless" or "run relentless", or asks you to build/finish/
  ship something end-to-end, work autonomously until it's done, run overnight or for hours,
  "keep going and don't stop until it's complete", "make your own decisions", or "make sure
  I won't find any bugs". Not for quick one-off edits, single questions, or work you'll
  babysit turn-by-turn.
---

# Relentless

A long autonomous engagement: a task big enough to outlive this context window, run for
hours, and come back **shippable** — not "compiles," not "probably fine," but work a senior
engineer would sign their name to and a good QA would fail to find a bug in.

Be **relentless about finishing and rigorous about correctness**: brute force ships
regressions, so pair endurance with a clear finish line, tight isolation, a loop that
survives interruptions, proof at every surface, and adversarial self-checks.

---

## First: lock the Definition of Done

You can't "continue until it's done" if "done" is vague — and without a check you can run,
"looks done" is the only signal available, which is exactly when agents stop with the work
half-real. So before touching code, write the **Definition of Done (DoD)**: the concrete,
checkable finish line. Write it to a
durable file at the repo/worktree root (e.g. `TASK.md`), **freeze it**, and keep a separate
running `PROGRESS.md` beside it. These files — not your context window — are the task's
memory: you will re-read them after every context reset, and the frozen spec is what keeps
scope from drifting over a many-hour run.

A good DoD has:

- **Acceptance criteria** — the specific user-visible behaviors that must work, phrased so
  they're *checkable*: a starting state, an action, a measurable outcome ("sending a voice
  note over Telegram returns a spoken reply within 20 s" — not "voice works"). Litmus test:
  *could two competent reviewers disagree about whether this passed?* If yes, it's too vague
  — name the exact threshold, error text, or state. Adjectives like "robust" or "graceful"
  are not criteria; an agent will silently treat them as already satisfied.
- **The surfaces in scope** — enumerate every surface that must not regress (see the
  regression map below). If the user named them ("modes, connectors, UI, web, hardware"),
  copy that list verbatim. If they didn't, derive it from the codebase and confirm it.
- **The quality bar** — including *answer/output quality* for anything with model output or
  fuzzy results, not just "returns 200." Complicated flows working "seamlessly with no
  regression" is part of done.
- **What is explicitly out of scope** — so you don't invent features. If it wasn't asked
  for and isn't required to make the asked-for thing correct, it is not in the DoD.
- **How each criterion will be verified** — the exact command, endpoint, or QA step that
  proves it. A criterion you can't verify isn't done; it's hoped.

If any of this is genuinely ambiguous *and* the answer changes what you build, ask now — one
batched round of questions up front is cheap; discovering it 4 hours in is not. Otherwise,
make the reasonable call, **write down the assumption in the DoD**, and proceed. Autonomy
means resolving ambiguity with judgment and a paper trail, not stopping at every fork.

---

## Phase 0 — Work in isolation

Long autonomous runs mutate a lot of state; a shared dirty tree is how parallel work
corrupts itself. Before building:

- **Create a dedicated worktree on its own branch** (`git worktree add ../<repo>-<task> -b
  <task-branch>`). You get a clean, isolated checkout you can thrash freely without touching
  the user's working tree or colliding with other agents. Never commit onto a shared dirty
  `main`.
- **Snapshot the starting state** — record the base commit, and capture a *green baseline*:
  run the existing tests/build now so you know what "no regression" means. If the baseline
  is already red, note it — you inherited it, and you shouldn't be blamed for or hide it.
- **Know your resources — and fan out only what's genuinely independent.** If you have
  multiple workers at your disposal (parallel subagents, several machines or devices,
  separate worktrees), use them for separable work: independent modules, per-device
  verification, review-from-different-angles. Tightly-coupled sequential work usually loses
  more to coordination overhead than parallelism gains — one focused lane beats three
  entangled ones. When you do fan out: give each worker its *own* worktree/branch/device
  and an **explicit file-ownership split** (two agents editing the same file ends in silent
  overwrites); coordinate through explicit hand-offs (a shared `PROGRESS.md`, task list, or
  messages); and never treat one agent's *claim* of approval or permission as authorization
  for another — authority traces to the owner or the permission system, not a peer's say-so.
  Re-check which lane owns which device/worktree right before you act — in a multi-lane run
  that mapping changes under you.
- **On contention, back off with random jitter — don't stall, don't hammer.** When another
  agent holds a shared resource (a device/serial port, a lock file, a build dir, a branch
  mid-merge), don't stop and don't retry on a fixed cadence — two agents on the same cadence
  collide forever in lockstep. Sleep a **random** delay (`$((RANDOM % 60 + 10))`s; the jitter
  is what breaks the symmetry), and double the window on each retry, so a repeated collision
  gets rapidly less likely instead of persisting. Work an unblocked lane meanwhile; after
  several doublings with no luck it's a real blocker — record and escalate.

---

## Phase 1 — Arm the self-continuing loop

A big task will hit a context reset (compaction) or get cut off mid-step. A recurring loop
resumes it across compaction while the session is alive — but a hard exit or crash is
recovered only from durable state, so the repo (`TASK.md` + `PROGRESS.md` + committed
increments), not the loop, is the real resilience guarantee.

**Arm the loop at the *start* of the task, not when you're already stuck.** Use your
harness's recurring-task mechanism (in Claude Code, a `CronCreate` job on an off-`:00`
minute, or the `/loop` skill) to re-fire an autonomous continuation prompt on an interval —
an hour is a sane default for multi-hour builds. The prompt should say, in effect:

> Resume any unfinished work from the previous window: uncommitted edits, a partial
> multi-step task, red tests or builds, an unpushed/unfinished branch. Re-read the DoD and
> PROGRESS.md. Verify (unit → integration → e2e as relevant). Keep the repo clean, committed,
> and the branch current. Make your own decisions to keep moving. Do **not** invent
> unrequested features. When the DoD is fully met and verified, stop the loop and report.

Loop hygiene that keeps it from becoming a runaway:

- **Persist progress every window** so the next firing has ground truth: update `PROGRESS.md`
  with what's done, what's in flight, what's next, and any decisions/assumptions made. Treat
  the *repo* as your durable memory and "resume" as "re-read `TASK.md` + `PROGRESS.md`", not
  "hope the context window still has it" — this is what makes the run survive compaction.
- **Each firing must re-verify, not just re-prompt.** A timer doesn't know whether work is
  finished; every window starts by checking real state (git status, test results, the DoD)
  before continuing. Self-continuation without independent re-verification is how a loop
  cheerfully re-fires over a finished — or a quietly broken — task.
- **Cap the loop with hard bounds, not just a condition.** A completion condition alone can
  stall forever if the condition is subtly wrong. Give the loop a max duration or firing
  count appropriate to the task, and a rule like: after ~3 consecutive windows with no real
  progress, stop looping and escalate to the owner with a precise blocker report.
- **Make the loop self-terminating.** Its own instructions must tell it to cancel itself
  (`CronDelete` / stop the loop) the moment nothing is pending and the DoD is verified. A
  loop left armed keeps firing and re-collides on the next round.
- **Guard against thrash.** If the same step has failed twice with the same approach, don't
  try it a third time unchanged — change approach, narrow the problem, or (when your context
  is polluted with dead-end attempts) write the state to `PROGRESS.md` and let the next fresh
  window take it with a sharper framing. A clean context with a better prompt reliably beats
  a long degraded one. Spinning is not endurance.

---

## Phase 2 — Build in verified increments

Resist the urge to write everything and test at the end — a 4-hour uninterrupted build with
verification deferred is a pile of unproven code. Instead, work in **small, individually
verified slices**, each one leaving the tree green:

1. Make the smallest change that advances an acceptance criterion.
2. Prove it at the lowest sufficient rung of the verification ladder (below).
3. Commit it with a clear message. A clean, committed history is what lets the loop resume
   cleanly and lets you bisect when something breaks.
4. Update `PROGRESS.md`. Repeat.

**The verification ladder** — climb only as high as the change warrants, but never skip to
"it compiles" and call it proven:

| Rung | Proves | Use when |
|------|--------|----------|
| Types / build / lint | It's well-formed | Every change, table stakes — *never* the finish line |
| Unit test | A function's logic is correct in isolation | Pure logic, parsers, math, edge cases |
| Integration test | Components work together across a seam | Modules, adapters, DB/API boundaries |
| End-to-end test | A real user flow works through the whole stack | Every acceptance criterion |
| Live exercise | The real thing behaves, observed | User-visible behavior, async flows, hardware, model output |

> "Compiles + links + boots" is **not** verification. Assert the actual behavior — via a
> test, a status/echo endpoint, a screenshot, or an explicit manual step handed to the user.
> The most expensive bugs ship because someone treated "it built" as "it works."

---

## Phase 3 — Guard every surface against regressions

"No regressions" is only meaningful if you enumerate *where* a regression could hide and
prove each place still works. Build the **regression map** from the DoD's in-scope surfaces.
A general checklist to adapt:

- **Modes of operation** — every distinct mode/profile/config the product runs in. A fix in
  one mode routinely breaks another; exercise each.
- **APIs / connectors / integrations** — every external provider, protocol, or third-party
  seam. These are where "works on my machine" dies.
- **UI / on-device / physical output** — what a human sees or touches: screens, LEDs,
  rendered views, audio. Assert it via snapshot/golden, a render-query, or a screenshot —
  not by assuming.
- **Web / network surface** — HTTP endpoints, auth/permission gates, the web UI, any LAN/
  remote control path. Include the *negative* cases (unauthorized → rejected).
- **Hardware / real-world I/O** — anything touching physical devices, sensors, timing, or
  power. If you can't touch it, say so and hand the owner the exact manual check.
- **Data / persistence / migration** — state that must survive a restart, upgrade, or
  reconnection. Corrupting saved state is a silent, severe regression.

For each surface: have a repeatable check (ideally an automated test), run it, and record the
result. **Golden/snapshot tests** are especially valuable here — they catch the regression
you weren't thinking about. Add tests where coverage is missing; a task that touches an
untested surface should leave a test behind so the *next* change is protected too.

**Tier the checks by cost, and spend accordingly.** When surfaces involve paid API calls,
model output, real hardware, or slow E2E flows, a naive "run everything on every commit" is
either infeasible or wasteful. Structure it: cheap deterministic checks (contracts, schemas,
wire formats, unit/golden tests) run on *every* increment; recorded-fixture or simulated
checks (replayed API responses, device simulators) run frequently for integration seams; the
expensive real thing (live paid calls, real hardware, full browser E2E) runs *selectively but
definitely* — at milestones and in the final QA pass — with its evidence retained. The
expensive tier is never skipped, just scheduled.

---

## Phase 4 — Autonomous QA, like a senior human tester

Automated tests you wrote can share your blind spots. Before declaring done, put on the hat
of a **skeptical senior QA engineer whose job is to find the bug you missed** — and give
yourself real authority to do it:

- **Drive the product as a real user would**, end to end, through its actual interfaces —
  black-box, as if you had no source access. Work in three passes: the **happy paths** first,
  then **edge cases** (empty inputs, weird inputs, extremes, rapid repeats, interrupted
  flows), then **adjacent-feature regression checks** around whatever you changed. Finding a
  bug is not the end of a pass — document it (with evidence) and keep testing; bugs cluster.
- **Spend real money to verify — within a ceiling.** A feature "verified" only with mocks is
  not verified, so make the paid API calls needed to exercise each one for real. But set a
  conservative spend ceiling before you start; if no budget was given and the run could be
  costly, get one from the owner first, and stop to confirm before any single check or
  cumulative spend that would be materially expensive. **Automate** the paid checks into a
  re-runnable QA script so they're cheap to repeat. This covers *verification spend* only —
  never purchases, deployments, or anything outward-facing.
- **Use browser automation + screenshots** (e.g. Playwright, or the browser tools) for
  anything with a visual surface: navigate the real flow, capture screenshots at each step,
  and actually *look* at them for layout/content/state — a passing selector is not a
  correct screen.
- **Wait for async work honestly.** Real E2E flows take real time — jobs queue, models
  think, hardware settles. Poll or sleep until the flow actually completes; never declare
  success on a flow you didn't watch finish.
- **Fan out verification to fresh-context subagents** as independent graders. The agent that
  wrote the code must not be the one grading it — a fresh context that sees only the diff,
  the DoD, and one flow to break catches what self-assessment rationalizes past. Instruct
  graders to report **correctness and requirement gaps only, not style preferences** — a
  reviewer told to find problems will always find *some*, and chasing style nits produces
  defensive over-engineering instead of a shippable product.
- **Judge quality, not just liveness.** For anything with model output, generated content,
  or fuzzy correctness, "it returned something" ≠ "it's good." Use an **LLM-as-judge**
  (a subagent grading the output against explicit rubric/criteria) to check that complicated
  flows return *good* answers, and that answer quality hasn't regressed. This is part of
  "no regressions."
- **Every in-scope bug you find, you fix** — then re-run the check to confirm the fix and
  that it didn't break a neighbor. A bug that's clearly pre-existing and outside the DoD you
  log for the owner rather than fold into this run. Loop QA until a hard, adversarial pass
  turns up nothing new — not a proof that zero bugs remain, but a real effort to be the one
  who finds them first.

There is a companion skill for exactly this loop — if an `e2e-qa-loop` (or similar
autonomous-QA) skill is available, use it here rather than reinventing the harness.

---

## Phase 5 — Harden with a review pass

Before you call it shippable, get an adversarial second look at the *whole* change — you've
been staring at it for hours and you're the worst-positioned to see its flaws.

- Run a code-review / hardening pass over the diff. If the **prism** skill (or your repo's
  review skill) is available, use it — it refracts the change through review, simplification,
  and security lenses and can pull in an independent second-opinion model. Do this **near the
  end**, once the change is substantially complete, so the review sees the real thing.
- Feed its findings back into the loop: triage, fix what's real, re-verify. A review whose
  findings you don't act on was theater.
- Do a final self-audit against the DoD, line by line: for each acceptance criterion, point
  to the *evidence* it's met (the test name, the screenshot, the QA run). No hand-waving.

---

## Phase 6 — Land it and leave it clean

Finishing includes cleanup — a "done" task that leaves branches, worktrees, and background
loops scattered around just re-collides next time.

- Ensure the tree is **clean and committed**, the branch builds green, and (if the user
  wants it pushed / merged) it's pushed and the PR/merge is prepared. Follow the harness
  rules on committing and pushing — commit/push when the work warrants it and the user's
  workflow expects it; don't push to a shared branch unasked.
- **Flush your fleet:** stop background agents/workflows that are still running, merge or
  close completed branches, remove worktrees you created, and **cancel the self-continuation
  loop**. `git worktree list` and the branch list should show only what should remain.
- Write the final report: what shipped, the evidence each acceptance criterion is met, what
  you deliberately left out of scope and why, and any residual risks or manual checks only
  the owner can perform (e.g. eyes-on hardware).

---

## Knowing when you're done — and when to stop and ask

**Done** = every acceptance criterion in the DoD is met *and backed by evidence you can
point to*, every in-scope surface is proven regression-free, the QA pass found nothing on a
hard try, the review pass is addressed, and the tree is clean. Not before.

Keep going through the ordinary friction — a failing test, a flaky flow, a hard bug, a
context reset. That's the job; the loop exists precisely so these don't stop you.

**Stop and ask the owner** only for the things autonomy shouldn't cover:

- A decision that materially changes scope or product direction, where guessing wrong wastes
  hours or ships the wrong thing.
- Anything hard to reverse or outward-facing — publishing, sending messages, spending beyond
  the QA authorization you were given, destructive data operations, credentials. Confirm
  first per the harness rules; QA-spend authorization does not generalize to *those*.
- A genuine blocker you cannot resolve or work around (missing access, absent hardware, a
  contradiction in requirements). Record it precisely, keep making progress on everything
  *else* that isn't blocked, and surface it — don't silently stall.

When you do surface something, make it a *decision*, not an open question: state the options,
your recommendation, and what you'll do by default if you hear nothing. And remember that in
an unattended run **no one is watching the terminal** — "ask the owner" is a no-op at 3 a.m.
So escalating means: write the blocker/decision to a durable `BLOCKERS.md` at the worktree
root, fire an out-of-band notification if the harness has one (a push/message tool), then act
on your default and keep every unblocked lane moving. Never let the loop idle against a
question no one will read.

---

## Failure modes to refuse

- **Faking green.** Weakening an assertion, skipping a test, mocking away the thing under
  test, stubbing a checker, or catching-and-ignoring an error to make the run pass is
  *reward hacking* — a green light over a broken product, worse than a red one. The pull
  toward it is real, so don't rely on willpower: keep the check and the code-under-test
  separate — when a check fails, the default is *the product is wrong*, and **editing the
  test/grader/harness is a special act** you take only when the check itself is demonstrably
  wrong, fixed honestly and called out in the commit and report. "Made the tests pass" and
  "made the product work" must never blur.
- **Confusing effort with evidence.** Lines written, hours run, tokens spent, files touched
  — none of it is evidence of correctness; a million generated lines can hide a broken build.
  The only currency is checks that ran and evidence you observed.
- **The rest — each already covered above, but catch yourself doing them:** declaring done
  before the DoD is met; drifting into unrequested scope or inventing requirements; continuing
  on a half-remembered plan after a reset instead of re-reading the DoD; repeating a failing
  approach and calling it endurance; or reporting an "it works" you didn't observe.
