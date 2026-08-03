---
name: linkedin-triage-rules
description: "Rules for handling LinkedIn DMs in Beeper — categories, response templates, and what requires personal attention"
metadata:
  node_type: memory
  type: feedback
---

# LinkedIn Triage Rules  (CUSTOMIZE THIS FILE)

This file is the source of truth for how the triage skill categorizes and replies to your
LinkedIn DMs. Everything in `{{DOUBLE_BRACES}}` is a placeholder - replace it with your own
details. Edit the categories and templates to match how *you* want to respond.

After replying, chats auto-mark as read. Unreplied chats stay unread = you handle them personally.

**When in doubt, leave a chat unread rather than reply with the wrong thing.**

---

## Your details

- Your name: `{{YOUR_NAME}}`
- Your company: `{{COMPANY}}`
- Careers / apply page: `{{CAREERS_URL}}`
- Referral link (optional): `{{REFERRAL_LINK}}`   <!-- delete this whole section if you don't refer people -->

---

## Referral link usage (delete if not applicable)

Only share `{{REFERRAL_LINK}}` with people who (a) explicitly express interest in working at
`{{COMPANY}}` AND (b) appear to be senior/experienced. **Do NOT send it to:**
- People who are not job seeking (a common, embarrassing mistake)
- Junior candidates or students, unless they have exceptional demonstrated work
- People who already have the link (just acknowledge their message)

---

## Categories and templates

### A — Senior job seekers (relevant experience)
**Rule:** Send the referral link with a warm note. Add one personal sentence if their background
is especially relevant to your work.
**Template:** "Hey [Name]! [1 personal sentence if relevant]. Apply through my referral link and
I'll make sure it gets to the right people: {{REFERRAL_LINK}}"

### B — Junior / mid-level job seekers
**Rule:** Do NOT send the referral link. Politely decline any call request. Point them to the
careers page to apply directly.
**Template (wants a call):** "Hi [Name]! Thanks for your interest in {{COMPANY}}. My schedule is
pretty slammed so I can't do intro calls right now. The best path is to apply directly at
{{CAREERS_URL}} - the team reviews applications and will reach out if there's a match. Good luck!"
**Template (no call ask):** "Hey [Name]! Thanks for reaching out. Right now the roles on our team
need more senior profiles - keep building and feel free to reach out again down the line!"

### C — Already has the link / checking in
**Rule:** Brief acknowledgment only. Don't resend the link.
**Template (applied, checking in):** "Hey [Name]! Your application is in the system - the team
will be in touch if there's a fit. Best of luck!"
**Template (closing/thanks):** "Good luck [Name]!"

### D — Vendor / sales cold outreach
**Rule:** Polite one-line decline. Don't engage with details.
**Template:** "Hi [Name], thanks for reaching out - not something we're exploring at the moment.
Best of luck!"

### E — External recruiters offering to help you hire
**Rule:** Polite decline, leave the door open.
**Template:** "Hi [Name], thanks for thinking of us - we're handling recruiting internally right
now. I'll keep you in mind if that changes!"

### F — Headhunting you for another company
**Rule:** Polite decline, mention you're not looking, leave the door slightly open.
**Template:** "Hi [Name], thanks for thinking of me - sounds like a great opportunity. I'm fully
focused on what we're building right now, so not looking to move. Maybe we can revisit down the
line. Best of luck with the search!"

### G — Networking / informational calls (non-job-seekers)
**Rule:** Politely decline the call. Point to public resources if appropriate.
**Template:** "Hi [Name], thanks for reaching out! I'm pretty stretched right now and can't take
on informational calls. Best of luck!"

### G2 — Generic professional networking (no specific ask)
**Rule:** Respond politely and minimally. Do NOT decline - keep the door open with a light
follow-up question. These are ambient connections that may matter later.
**Template:** "Hi [Name]! Thanks for reaching out - always good to connect with people thinking
about [relevant topic from their message]. What are you working on these days?"

### H — Personal / strategic / ongoing conversations
**Rule:** LEAVE UNREAD. You handle these personally.
**Examples:** partners, clients, colleagues, friends, ongoing deal discussions, anything
personal or in another language with a known contact.

---

## Calls rule (applies across categories)
Calls are costly. Only agree to a call if the person is (a) exceptional/very senior talent OR
(b) specifically relevant to a priority area for you. Otherwise decline the call and redirect
using the category flows above.

---

## Writing style rules
- **Never use em dashes (—) in any message.** Use a regular hyphen (-) or restructure. Em dashes
  are an AI tell.
- Keep replies short and human.

## Common mistakes to avoid
- Sending the referral link to people who are not job seeking.
- Sending the referral link to clearly junior candidates / students.
- Resending the link to people who already have it.
- Engaging with vendor pitches (just decline politely).
- Getting stuck in thank-you / reaction loops: if a chat is just cycling through "thanks" →
  reply → reaction with no new substance, leave it unread and don't report it.
- Replying to emoji-only responses or reactions: if the latest message is just an emoji, a
  reaction, or "thanks!" with no new substance or question, leave it unread.
