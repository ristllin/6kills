---
description: "Refract code (or a plan) through prism's four lenses — roast, simplify, peer-review, security — auto-detecting mode from context"
argument-hint: "[pr|audit|review|roast|simplify|peer|new|all]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Task", "WebFetch", "WebSearch"]
---

Run the **prism** skill.

Mode = `$ARGUMENTS` (if empty, auto-detect the mode per the prism skill's Step 1:
plan mode → `plan`; pending git diff → `pr`; clean existing repo → `improve` (confirm first);
empty repo → `new`).

Follow the prism skill's orchestration exactly — including its considerate rules
(read-only in plan mode, confirm before whole-codebase sweeps, announce before any
credit-spending cross-provider peer-review call, scope `pr` to the diff, and validate
after every auto-fix).
