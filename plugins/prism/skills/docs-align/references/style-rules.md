# Style rules: slop deny-list and newcomer rubric

Loaded by `docs-align` Step 4 and Step 5. Two parts: patterns to remove (with detection cues
and rewrite rules), then the rubric for judging whether a doc serves someone new to the repo.

Scope note: apply to prose. Skip code spans, fenced blocks, CLI flags (`--flag`), YAML front
matter, and quoted output. Skill and agent instruction files (LLM-executed, like this one)
are exempt from the format rules (e.g. bold-lead-in lists); those target human-facing docs.
Language rules (em dashes, negation patterns) still apply everywhere.

## Part 1: The deny-list

Each entry: the pattern, a detection cue, the rewrite.

1. **Em dash.** Cue: `—`, `&mdash;`, or ` -- ` in prose. Rewrite: remove, always. Pick the
   replacement by context: complete-clause break becomes a period and new sentence; brief
   aside becomes commas; introducing an explanation, list, or consequence becomes a colon;
   true parenthetical detail becomes parentheses. Never keep the em dash.
2. **Negation pattern ("what it's not").** Cue: "it's not just X, it's Y", "this isn't
   about X", "not only X but also Y", "not because X but because Y", "no X, no Y, just Z",
   "X, not Y" used rhetorically. Rewrite: delete the negated clause; state the positive claim
   once with a concrete specific. "Not just a dashboard, a command center" becomes "Shows
   approvals, comments, and status in one place."
3. **Rule-of-three padding.** Cue: triads of near-synonyms ("fast, simple, and powerful");
   staccato triads ("Think bigger. Act bolder. Move faster."). Rewrite: keep the one item
   that carries information, or replace the triad with a single verifiable claim.
4. **Bold-lead-in bullet lists.** Cue: three or more consecutive items shaped
   `- **Term**: description`. Rewrite: plain list if the terms are the content, prose or a
   table if the descriptions matter. Never default every list to this shape.
5. **Hype vocabulary.** Cue: seamless(ly), effortless(ly), robust, powerful, blazing-fast,
   cutting-edge, state-of-the-art, world-class, game-changing, revolutionize, supercharge,
   unleash, "unlock the power", elevate, empower. Rewrite: delete, or replace with a measured
   fact (number, platform list, actual mechanism). Unverifiable praise never survives review.
6. **AI-favored words.** Cue: delve, leverage, utilize, harness, foster, bolster, underscore,
   showcase, boasts, tapestry, testament, landscape, realm, journey, intricate, meticulous,
   pivotal, holistic. Rewrite to the plain word: leverage/utilize/harness become "use", delve
   into becomes "explain", showcase becomes "show", boasts becomes "has".
7. **Generic scene-setting intro.** Cue: opens with "In today's ...", "In the ever-evolving
   world of ...", "With the rise of ...". Rewrite: delete the sentence; open with what the
   thing is or does.
8. **Fluffy conclusion.** Cue: "In conclusion", "To summarize", "Overall", "At the end of
   the day", a "Final Thoughts" heading in a README. Rewrite: delete; docs end after the last
   fact or instruction. A genuine follow-up becomes "Next steps" with links.
9. **Throat-clearing filler.** Cue: "It's important to note that", "Please note that",
   "Without further ado", "Let's face it", repeated sentence-initial
   Additionally/Moreover/Furthermore. Rewrite: delete the filler, keep the bare claim.
10. **Sycophancy and cheerleading.** Cue: "Great question", "Congratulations!", "Happy
    coding", "Let's dive in", "Whether you're a beginner or an expert", exclamation points in
    body prose. Rewrite: delete; use neutral imperatives. "Congratulations! X is configured"
    becomes "X is now configured."
11. **Difficulty-minimizers.** Cue: simply, easily, just, obviously, of course,
    straightforward, attached to an action the reader must perform. Rewrite: delete the word;
    the instruction stands alone. What is easy for the writer may not be easy for the reader.
12. **Emoji clusters.** Cue: decorative emoji strings in headings, bullets, or badges
    (🚀✨🔥✅ pileups). Rewrite: remove decoration. Exception: a repo's established, stable
    iconography (one emoji per named product or lens, used consistently) is identity, and
    stays. Flag additions beyond that.
13. **Inflated structure.** Cue: sections with bodies under two sentences; an
    Overview + Introduction + Key Features + Why X + Conclusion scaffold wrapping under 500
    words; heading levels that skip. Rewrite: collapse thin sections into their parent.
14. **"Serves as" dodge.** Cue: serves as, stands as, functions as, acts as, represents,
    where "is" works; "boasts"/"features" as verbs for possession. Rewrite: "is", "has", or
    the concrete verb ("serves as a wrapper around" becomes "wraps").
15. **Puffery.** Cue: "a testament to", "plays a pivotal role", "underscores its importance",
    "vibrant ecosystem". Rewrite: delete, or replace with the checkable fact behind it.
16. **Trailing "-ing" pseudo-analysis.** Cue: sentence-final participial clause
    (", ensuring reliability.", ", highlighting the importance of ..."). Rewrite: delete the
    clause; if the claim matters, promote it to its own sentence with evidence.
17. **False-drama fragment.** Cue: "The result? Devastating." question-fragment plus short
    answer in expository prose. Rewrite: one declarative sentence.
18. **Vague authority.** Cue: "Experts agree", "Studies show", "It is widely considered",
    with no named source. Rewrite: name and link the source, or delete the sentence.
19. **Hidden verbs.** Cue: "perform an installation of", "conduct an analysis of", "in order
    to", "prior to". Rewrite: uncover the verb: install, analyze, to, before.
20. **Passive procedures.** Cue: "The file should be saved", sentence-initial "There are",
    dense passive voice in step lists. Rewrite: imperative with a real actor ("Save the
    file"); recast "There are three options" as "X has three options".
21. **"Please" and "Let's" in instructions.** Cue: please in procedure text; sentence-initial
    "Let's". Rewrite: delete please; "Let's configure the server" becomes "Configure the
    server".
22. **Emphasis scatter.** Cue: three or more bold spans in one paragraph; the same term
    bolded at every occurrence. Rewrite: at most one emphasized element per paragraph.
23. **Invented round statistics.** Cue: "10x", "99.9%", "24/7", "1000+" with no source or
    measurement stated. Rewrite: keep a number only if measured, and say where it came from.
    One invented figure poisons every true one beside it.
24. **Elegant variation.** Cue: one referent renamed across nearby sentences ("the tool ...
    the platform ... the solution"). Rewrite: pick one term and repeat it. Docs value
    consistent terminology over variety.
25. **Chatbot residue.** Cue: "as of my last training update", "I hope this helps", "let me
    know if", citation artifacts (oaicite, contentReference, utm_source=chatgpt), curly
    quotes near code. Rewrite: delete on sight, then audit the whole document: residue means
    unverified claims and possibly fabricated links nearby.
26. **Marketing register.** Cue: "Say goodbye to X", "Gone are the days", "Look no further",
    "the ultimate guide", "take it to the next level". Rewrite: the concrete capability.
    "Say goodbye to manual deploys" becomes "Deploys run automatically on merge."

## Part 2: Newcomer rubric

Binary checks. A doc facing people new to the repo passes all of them.

1. **Purpose in the first screen.** Within the first two paragraphs: what it does and who it
   is for, before any install or usage content.
2. **Prerequisites before first use.** Every tool, version, account, credential, and env var
   is declared before the first instruction that needs it. A prerequisite that first appears
   mid-procedure is a finding.
3. **First-run integrity.** The first command sequence runs as-is from a fresh clone on a
   stated platform. No unresolved placeholders without instructions for obtaining real
   values, no dependence on state not created earlier in the doc.
4. **No term before definition.** Every project-specific term, acronym, or codename is
   defined or linked at first occurrence.
5. **Expected result per step.** Each step states what success looks like (output, UI state,
   or a verification command).
6. **One mode per section.** A quickstart does not detour into reference dumps or
   multi-paragraph theory. One sentence of "why" plus a link is the ceiling (Diátaxis).
7. **Numbered procedures, one action per step, condition first.** "If you use staging, skip
   this step" comes before the step, never after.
8. **No dangling references.** Every path, script, command, config key, and link resolves at
   the current commit and is reachable by an external reader (no internal dashboards or team
   shorthand).
9. **Doc-code synchrony.** Commands, flags, defaults, ports, and versions in the doc match
   the code right now.
10. **Skimmable.** Headings describe their content (never "Miscellaneous"), link text names
    its destination (never "click here"), paragraphs open with the key point.
11. **Minimal and alive.** No future-feature promises, no implementation history, no second
    copy of content maintained elsewhere (link to the canonical source).
12. **Current-state only.** The doc describes the repo as it is. How it got that way lives in
    git history and ADRs.
