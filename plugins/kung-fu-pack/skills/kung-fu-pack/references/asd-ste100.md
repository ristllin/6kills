# Writing standard: ASD-STE100 (Simplified Technical English)

Apply this when the config `writing_standard` is `asd-ste100` or the run uses `--style=asd-ste100`.
ASD-STE100 is a controlled language for technical documentation (originally aerospace/defense):
restricted grammar plus an approved-word dictionary, so a global, non-native audience reads it the
same way every time.

**Honest limit.** Full certified compliance needs the licensed ASD-STE100 dictionary of approved
words and a checker (for example HyperSTE or Congree). This skill does not ship the dictionary, so it
applies the **writing rules** (below) and a **lint** as a strong approximation. Say so in the page
footer when this mode is on: "Written to ASD-STE100 writing rules (approximated; not dictionary-certified)."
For a deliverable that must be certified, run the output through a licensed STE checker.

## The writing rules to apply

Words and terms
- One word, one meaning. Use a word in only one part of speech and one approved sense across the page.
- One term per concept. Pick a single name for each thing and reuse it exactly; no synonyms, no
  elegant variation. Build a short term list for the target and keep to it.
- Prefer short, common, concrete words over long or rare ones. No slang, idiom, or jargon unless it
  is the target's own defined term (then define it once).
- Noun clusters: at most 3 words in a row. Break up longer strings with prepositions or a rewrite
  (for example "runtime sandbox key isolation" -> "isolation of the key in the runtime sandbox").

Verbs and voice
- Use the active voice. Name who does what.
- Use the imperative for instructions ("Set X.", "Do not remove Y.").
- Use simple tenses (simple present, simple past, simple future) and the past participle only as an
  adjective. Avoid the "-ing" form (present participle / gerund), except in an established technical
  name.

Sentences
- Keep instruction (procedural) sentences to 20 words or fewer.
- Keep descriptive sentences to 25 words or fewer.
- One idea per sentence. For a procedure, one instruction per sentence.
- Use articles (a, an, the) where they help clarity. Do not drop connecting words to save length.

Structure
- Start a paragraph with its topic sentence; keep paragraphs short and single-topic.
- Use a vertical list for anything with more than two linked items, conditions, or steps.
- Use tables for parameter / status / mapping data.
- Write a safety or must-not item as a direct command, condition after the command
  ("Do not deploy to prod. Prod is a disabled skeleton.").
- Put steps in the order of performance.

House rules still apply on top of this: no em or en dashes anywhere; a lead behind every claim;
flag staleness. STE favors the hyphen and the full stop, so these fit naturally.

## Lint (run in the verify step when this mode is on)

Flag and fix before publishing:
- Any sentence over its limit: `grep -nE '[^.!?]{130,}[.!?]'` as a rough long-sentence finder, then
  count words on flagged lines (procedural > 20, descriptive > 25).
- The "-ing" form: `grep -nEi '[a-z]{3,}ing\b'` and rewrite each hit that is a verb (keep approved
  technical names).
- Passive voice markers: `grep -nEi '\b(is|are|was|were|be|been|being)\b +[a-z]+ed\b'` and rewrite
  to active where it is genuinely passive.
- Noun clusters of 4+ words: scan headings and dense noun strings; rewrite with prepositions.
- Consistency: list the key terms and confirm each concept uses one name throughout (no synonyms).
- Dashes: scan for em dash (U+2014) and en dash (U+2013); `grep -nP '\x{2014}|\x{2013}'` (or a
  Python scan for those codepoints) must be empty.

Note in the report that STE mode was applied and that strict certification needs a licensed checker.
