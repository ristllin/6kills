---
name: linkedin-triage
description: >-
  Triages unread LinkedIn DMs in Beeper. Categorizes messages, sends appropriate
  responses, and leaves personal/strategic conversations unread for your attention.
  Invoke as /linkedin-triage
---

# LinkedIn Triage

You are triaging the user's unread LinkedIn DMs in Beeper. After you reply, a chat
auto-marks as read. Chats you skip stay unread = the user handles them personally.

**Core rule: when in doubt, leave unread.**

---

## Step 0: Load rules

Read the triage rules from `/sandbox/.claude/projects/-workspace/memory/linkedin_triage_rules.md`.
Internalize the categories, the response templates, and any links (e.g. a referral link).
These rules are user-specific and are the source of truth for how to respond.

---

## Step 1: Fetch unreads

Use `mcp__beeper__search_chats` with `unreadOnly: true`, `inbox: "primary"`, `limit: 50`.

---

## Step 2: Read each chat

For each unread chat, use `mcp__beeper__list_messages` to read the conversation history
(not just the latest unread message - you need context to categorize correctly).

---

## Step 3: Categorize and respond

Classify each chat using the categories defined in the rules file, then respond with the
matching template via `mcp__beeper__send_message`. Personalize where the person's background
is especially relevant to the user. If a chat is personal, strategic, or ambiguous, LEAVE IT
UNREAD - do not reply.

**NEVER use em dashes (—) in any message.** Use a regular hyphen (-) or rewrite the sentence.
Em dashes are a giveaway that the message was written by an AI.

Follow every "do not send" restriction in the rules file exactly (e.g. do not send a referral
link to people who are not job seeking or who already have it).

---

## Step 4: Report

After processing, give the user a brief summary:
- How many chats were handled and in which category
- Which chats were left unread and why (these need their attention)
