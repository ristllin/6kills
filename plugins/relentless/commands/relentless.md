---
description: "Go relentless — run a long autonomous build to a genuinely shippable, regression-free finish (worktree, self-continuing loop, full test pyramid, autonomous E2E QA, hardening review)"
argument-hint: "[task description or leave empty to use the current task in context]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Task", "WebFetch", "WebSearch"]
---

Run the **relentless** skill on the task.

Task = `$ARGUMENTS` (if empty, use the task already established in the conversation
context; if none exists, ask the user for the goal and its acceptance criteria, then stop).

Follow the relentless skill exactly — establish the Definition of Done first, work in an
isolated worktree, arm the self-continuing loop, cover every surface against regressions,
run autonomous end-to-end QA, harden with a review pass, and only stop when the Definition
of Done is fully met (or you hit a genuine blocker that needs the owner). Respect its
guardrails: no scope creep, no faked-green tests, confirm before anything hard to reverse
or outward-facing, and leave the tree clean.
