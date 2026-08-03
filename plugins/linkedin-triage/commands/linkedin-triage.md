---
description: "Triage your unread LinkedIn DMs in Beeper - runs an isolated Docker sandbox that categorizes each chat, replies from your templates, and leaves personal/strategic ones unread"
allowed-tools: ["Bash"]
---

Run the isolated LinkedIn triage sandbox and report its result to the user.

The triage does **not** run in this session. It runs Claude inside a locked-down Docker
container (only the Beeper tools + the user's rules file are visible; Bash, writes, and web
access are denied). Your job here is only to launch it and relay the outcome.

**First, check whether onboarding has been done.** If the rules file still contains template
placeholders, the user has not personalized it yet - triaging now would send generic replies.
Run:

```bash
grep -q "{{" "${CLAUDE_PLUGIN_ROOT}/sandbox/memory/linkedin_triage_rules.md" && echo NEEDS_INIT || echo READY
```

If it prints `NEEDS_INIT`, do **not** run the triage. Tell the user their rules aren't set up yet
and to run `/linkedin-triage-init` (the interactive onboarding), then stop. Otherwise continue.

Execute:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/sandbox/run.sh"
```

Then:

- **On success**, wait for it to finish and summarize for the user: how many chats were
  handled and in which category, and which chats were left unread (those need their attention).
- **If it exits with a prerequisite error** (Docker not running, no Beeper MCP token, or no
  API auth configured), this is almost always a **fresh / not-yet-set-up machine**. Do not try
  to work around the sandbox. Relay the exact guidance the script printed, and point the user at
  the one-time setup:
    - Run the checker: `bash "${CLAUDE_PLUGIN_ROOT}/sandbox/setup.sh"` - it verifies every
      prerequisite (Docker, Beeper Desktop + local API, Beeper `/mcp` auth, API key) and builds
      the image.
    - Full walkthrough from a clean machine: `${CLAUDE_PLUGIN_ROOT}/sandbox/SETUP.md`.
    - Before the first real run, the user must customize their reply templates in
      `${CLAUDE_PLUGIN_ROOT}/sandbox/memory/linkedin_triage_rules.md` (replace every
      `{{PLACEHOLDER}}`).

Never invent or send replies yourself from this session - you have no Beeper access here. All
messaging happens inside the sandbox.
