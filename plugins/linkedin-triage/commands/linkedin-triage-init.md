---
description: "Interactive onboarding for LinkedIn triage - interviews you about your inbox, then writes your personalized rules file, model choice, and (optional) schedule"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion"]
---

You are running the **first-time onboarding interview** for the linkedin-triage plugin. Your job
is to interview the user, then generate two files from their answers:

1. `${CLAUDE_PLUGIN_ROOT}/sandbox/memory/linkedin_triage_rules.md` - the categories, reply
   templates, red lines, and leave-unread rules the sandbox uses on every run.
2. `${CLAUDE_PLUGIN_ROOT}/sandbox/config.env` - the model choice (and, if they want, the API key).

The triage itself runs later in an isolated container; this command only builds its config. Be
warm, concise, and concrete. **Never use em dashes** in anything you write.

---

## Before you start

1. Read the current template so you match its structure:
   `Read ${CLAUDE_PLUGIN_ROOT}/sandbox/memory/linkedin_triage_rules.md`
2. Detect the likely auth mode (affects which model variable you write):
   `bash -c 'if [ "${CLAUDE_CODE_USE_FOUNDRY:-0}" = "1" ] || [ -n "${ANTHROPIC_FOUNDRY_BASE_URL:-}" ]; then echo foundry; elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then echo key; else echo none; fi'`
3. Tell the user, in one or two sentences, what you're about to do and that they can say "use a
   sensible default" to any question.

## Interview

Ask in small batches. Use **AskUserQuestion** for the discrete choices (multiple choice), and ask
open questions in plain chat for anything free-form (their voice, example replies, specific
phrases). Do not dump all questions at once. Cover these topics:

**A. Identity & resources**
- Their name (used to sign replies), company/role, and the careers/apply URL.
- Any resources to hand out: a referral link, a blog, a scheduling link. Capture each and note
  exactly when each should be shared.

**B. The messages they actually get**
- Ask them to describe the kinds of LinkedIn DMs they typically receive (e.g. senior job seekers,
  junior/students, vendors, external recruiters, headhunters, networking asks, generic "let's
  connect", personal). For each type they name, capture: should the agent **auto-reply and close**,
  or **leave it unread and just notify** them?
- Offer the proven default category set (senior job seeker, junior/student, already-has-link,
  vendor, external recruiter, headhunter, networking call, generic networking, personal) and let
  them add, remove, or rename.

**C. How to answer each type**
- For every auto-reply category, get the intent and a sample line in their own voice. Keep replies
  short and human. Confirm the em-dash ban and ask for any sign-off they want.

**D. Referral policy (if they hand out a referral link)**
- Who qualifies (seniority/experience bar, and any domain focus, e.g. only cybersecurity or AI).
- Who to refuse: use AskUserQuestion (multiSelect) with options like: non-job-seekers,
  junior/students, people who already have the link, anyone outside their domain.

**E. Red lines (hard "never do" rules)**
- e.g. never send the referral link to non-job-seekers, never agree to a call except in case X,
  never engage vendor pitches, never discuss unreleased/confidential topics. Capture as a bullet list.

**F. Leave-unread / notify-only triggers** (use AskUserQuestion, multiSelect)
Which of these should make the agent NOT reply and instead leave the chat unread for the user:
   - "I've already replied at least once in this thread" (hand back once a human is engaged)
   - "The conversation is in a specific language" -> if picked, ask which language(s)
   - "It's a personal or known contact"
   - "It's an ongoing deal / strategic / recruiting-for-my-team thread"
   - "Anything I'm not confident how to categorize" (the safe default - recommend keeping this on)

**G. Calls policy**
- When to accept a call vs politely decline, and any exception (e.g. exceptional/very senior
  talent, or someone in a priority domain).

**H. Operational**
- **Model** (AskUserQuestion). Triage is mostly classification plus short templated replies, so a
  fast, cheap model is usually enough. Offer: "Fast & cheap (recommended) - Haiku", "Higher quality
  for nuanced replies - Sonnet", "Let me type an exact model id". Map their pick to a concrete id.
- **Inbox scope**: primary inbox only (default) or all.
- **Cadence / poll rate** (AskUserQuestion): "Manual only", "Daily", "Twice a day", "Custom". If not
  manual, ask the time(s) and offer to install the schedule at the end (macOS launchd via
  `sandbox/schedule/update-schedule.sh`; on Linux tell them to add a cron entry).

## Generate the files

**1. Rules file.** Overwrite `${CLAUDE_PLUGIN_ROOT}/sandbox/memory/linkedin_triage_rules.md` with a
complete file (no `{{PLACEHOLDERS}}` left) following the existing template's shape: a short intro,
a "your details / resources" block, referral usage rules (omit entirely if they don't refer),
one section per category with its Rule + Template, a "leave unread / notify-only" section listing
their chosen triggers (including the language list and the already-replied rule if selected), a
calls rule, writing-style rules (keep the em-dash ban), and a "common mistakes to avoid" list.
Preserve the core principle: **when in doubt, leave unread.**

**2. Config file.** Write `${CLAUDE_PLUGIN_ROOT}/sandbox/config.env`. Use `${VAR:-value}` form so a
shell export always wins. Pick the variable by auth mode:
   - key mode:      `export TRIAGE_MODEL="${TRIAGE_MODEL:-<model-id>}"`
   - foundry mode:  `export ANTHROPIC_DEFAULT_SONNET_MODEL="${ANTHROPIC_DEFAULT_SONNET_MODEL:-<model-id>}"`
   Only offer to save an API key into this file if they are in key mode and explicitly ask; it is
   git-ignored, but exporting it in the shell is cleaner. Start the file with a comment noting it is
   generated and git-ignored.

## Finish

- Run `bash "${CLAUDE_PLUGIN_ROOT}/sandbox/setup.sh"` and report the checklist.
- If they chose a schedule (macOS), run `bash "${CLAUDE_PLUGIN_ROOT}/sandbox/schedule/update-schedule.sh" <hour> <minute>`.
- Show a short summary of what you saved and where, and tell them they can re-run
  `/linkedin-triage-init` anytime to change it, or hand-edit the rules file. Then point them to
  `/linkedin-triage` for the first real run (offer a read-only dry run first if they're nervous).
