---
description: "Refract code (or a plan) through prism's five lenses: roast-with-docs, simplify, peer-review, security-audit, docs-align. Auto-detects mode from context"
argument-hint: "[pr|improve|audit|review|roast|simplify|peer|docs|new|all]"
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Edit", "Write", "Task", "WebFetch", "WebSearch"]
---

Run the **prism** skill.

Mode = `$ARGUMENTS` (if empty, auto-detect the mode per the prism skill's Step 1:
plan mode → `plan`; pending git diff → `pr`; clean existing repo → `improve` (confirm first);
empty repo → `new`).

Follow the prism skill's orchestration exactly, including its considerate rules
(read-only in plan mode, confirm before whole-codebase sweeps, announce before any
credit-spending cross-provider peer-review call, scope `pr` to the diff, run `docs-align`
last so docs match the final state, and validate after every auto-fix).
