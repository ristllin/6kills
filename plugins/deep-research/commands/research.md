---
description: Deep research — plans queries, fans out Tavily searches, writes a cited report
argument-hint: <topic> [--breadth N] [--depth N] [--out path]
allowed-tools: Task, Read, Bash(ls:*)
---

Dispatch the `deep-researcher` subagent to run deep research on the user's topic.

**User arguments:** `$ARGUMENTS`

Steps:

1. Parse `$ARGUMENTS` into:
   - `topic` — everything that isn't a flag
   - `--breadth N` → breadth (default 5)
   - `--depth N` → depth (default 2)
   - `--out <path>` → output path (default `./research/<slug>.md` where `<slug>` is the kebab-cased first ~6 words of the topic)

   If `$ARGUMENTS` is empty, ask the user for a topic and stop.

2. Invoke the `deep-researcher` subagent via the Task tool. Pass it a self-contained brief:

   ```
   Topic: <topic>
   Breadth: <N>
   Depth: <N>
   Output path: <path>
   Audience: the user (Roy) — technical, concise. Prefer primary sources.
   ```

3. When the subagent returns, relay its summary to the user and show the output path as a clickable markdown link.

Do not do the research yourself — delegate it. Your job is to dispatch, not to search.
