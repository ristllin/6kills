---
description: "Collapse a fan-out of parallel work into one clean main: wait out or exclude sibling agents, merge every finished lane, refract the combined diff through prism, then hold with a report or ship a clean-slate release and QA it live"
argument-hint: "[task/scope + flags: --auto-deploy, --include-stuck, --wait-timeout=<dur>, --qa-spend=<amount>, --target=<branch>; empty uses the current task in context]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Task", "WebFetch", "WebSearch"]
---

Run the **collapse** skill on the task.

Task + flags = `$ARGUMENTS` (if empty, use the task already established in the conversation
context; if none exists, ask the user for the goal, the lanes to converge, and the deploy
policy, then stop).

Follow the collapse skill exactly. Be relentless on your own lane first (Definition of Done,
isolated worktree, self-continuing loop, verified increments, regression map, autonomous QA,
hardening), because you cannot collapse half-built work. Then map the fleet, converge (wait for
progressing lanes on a size-scaled recurring check, exclude stalled ones unless
`--include-stuck`), including a lane only when it carries a completion marker (never dropping a
finished-but-quiet lane on elapsed time alone), collapse every included lane into one clean main
with green verification after each merge and honest conflict resolution, refract the combined
diff through prism and fix every confirmed finding. Then, by default, stop with a decision report
delivered through a durable file plus an out-of-band notification and wait for a go; the go
resumes the same run into deploy. With `--auto-deploy` (or on that go), ship a staged clean-slate
release in dependency order (expand migrations before the app and destructive ones after, bricking
fail-closed parts deferred to a verified follow-up, a defined halt-and-escalate on any mid-stage
failure), QA the live deployment as the orchestrator with fresh-context grader subagents
(checking content, not just status codes), and send the final report. Respect the guardrails:
confirm before dangerous/irreversible substeps even under auto-deploy, never collapse a moving
lane, never resolve conflicts blindly, never declare done from a green pipeline without prod QA,
report any control that is weaker than intended, escalate holds through the absent-owner channel
rather than idling, and flush the fleet (cron/loop, worktrees, branches) so main is the clean
slate the owner asked for.
