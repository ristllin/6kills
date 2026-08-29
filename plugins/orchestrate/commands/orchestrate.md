---
description: "Orchestrate a program from scratch: interrogate the requirements, write the PRD, split it into waves of non-conflicting lanes on a tracker, launch detached headless lanes running relentless, supervise on a loop with evidence-based state, merge within the window, gate and release between waves"
argument-hint: "[requirements / path to a requirements list + flags: --tracker=<linear|markdown>, --max-lanes=<n>, --cadence=<dur>, --model=<id>, --gates=<n>; empty uses the requirements in context]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Task", "WebFetch", "WebSearch"]
---

Run the **orchestrate** skill on the program.

Requirements + flags = `$ARGUMENTS` (if empty, use the requirements already established in
the conversation context; if none exist, ask the owner for the raw requirements list, then
stop).

Follow the orchestrate skill exactly. First interrogate: read the whole requirements list,
ask the owner one numbered list of clarifying questions covering EVERY ambiguous step, each
with a proposed default, and wait for the answers - do not plan on guesses. Then write the
PRD slowly and completely, convert it into a dependency-ordered tracker split into waves of
parallel non-conflicting lanes with frozen Definitions of Done and evidence requirements
(plan approval is the only default human gate; add more only at genuinely irreversible or
outward-facing steps). Set up each lane (worktree + branch off the frozen base with env
files copied in, TASK.md with the frozen DoD, file-ownership contract, prod-care rules,
battery definition and evidence discipline, a shared lane charter skill, resource locks if
hardware is involved), then launch lanes as detached headless `claude -p` processes with
the model pinned and session ids recorded, each running relentless to its DoD and required
to message the orchestrator on completion or blockers. Supervise on the recurring loop:
lane state from lane.log + PROGRESS.md + PR_BODY presence only, never pid-liveness and
never a cause without log evidence; rule on DECISION comments instead of waiting; launch
more lanes as capacity frees; merge every completed lane within one window with a rebase, a
full green battery, and honest conflict resolution. Validate with per-lane prism before
handback and your own eyes on UI screenshots before any visual merge, run the program-level
prism gate over the merged wave diff before releasing, ship pre-authorized releases between
waves with fresh-context post-deploy content QA, and at program end deliver the
issue-to-evidence report and flush everything. Respect the guardrails: no fabricated lane
state, no unmerged finished work, no overlapping lanes, no blind conflict unions, no red
battery merges, no HITL creep, and never idle against a question no one will read.
