# kung-fu-pack synthesis benchmark: design, a corrected baseline, and what it says next

The first eval was saturated (a self-reported comprehension quiz ceilinged at 1.0). This benchmark
replaces it with published, reimplementable methods so it can drive improvement. All numbers below
are real. An earlier version of this report claimed a large v0 to v1 gain; an audit showed that claim
came from scorer and gold bugs, so it is retracted here and the comparison is re-run (section 3).

## 1. Tasks
"Many sources into a tight brief", with frozen post-training-cutoff corpora so answers cannot come
from parametric memory. Three dev tasks and two held-out tasks (held-out guards against overfitting
the skill text to the dev set):

| id | family | corpus | split |
|---|---|---|---|
| f1-arxiv-cslg | landscape | 220 cs.LG abstracts (336k chars) | dev |
| f2-releases | what-changed digest | 6 vLLM + Transformers releases (193k chars) | dev |
| f3-multitool | distributed evidence | design doc + issue tracker + changelog; key facts need 2+ sources | dev |
| h1-arxiv-cscr | landscape | 200 cs.CR abstracts | held-out |
| h2-releases | what-changed digest | 41 PyTorch + LangChain releases | held-out |

Task scopes describe only the goal. They do not say whether to nest; deciding structure is the
skill's job.

## 2. Grading stack (`scorers/`)
- **Gold** (`gold/author.py`): map-reduce over the whole corpus. A model summarizes each ~45k-char
  slice, then builds corpus-level nuggets (vital/okay) and 6 to 8 integration facts that each need
  2+ sources. Integration facts citing fewer than 2 distinct sources are dropped automatically.
- **Eligibility gate** (FACTS-style): evasive or empty briefs score zero.
- **Nugget and integration recall** (AutoNuggetizer-style, model-judged): judged by a two-model
  panel (Codex and Claude); recall is the panel mean and inter-judge agreement (Cohen's kappa) is
  recorded per brief.
- **Citation** (ALCE-inspired, deterministic): share of fact lines with a lead x share of leads that
  resolve to the frozen corpus.
- **Anti-redundancy** and **nesting appropriateness** (structural).
- **Composite** = 0.40 integration + 0.30 vital nuggets + 0.10 all nuggets + 0.10 citation + 0.05
  nesting + 0.05 non-redundancy. **Floors:** eligible, zero em/en dashes, and length (a large task
  passes only by nesting into an index plus sub-pages or by staying within 3 pages). A floor breach
  multiplies the composite by 0.3.

## 3. Audit and correction
Before a second iteration, the benchmark itself was audited. Four defects were found and fixed:
1. **Gold covered a slice, not the corpus.** F1 gold came from the first ~20 of 220 abstracts, F2
   gold from 2 of 6 releases. Now map-reduce over everything (F1 gold cites 121 distinct papers).
2. **The writer saw half the corpus.** A 160k-char cap cut F1 in half. Now the whole corpus is sent.
3. **Scorers disagreed on what the brief is.** The nugget judge read only `index.md` of a nested
   pack, and the v0 run was scored before a reader fix while v1 was scored after it. One shared
   reader (`scorers/brief.py`) now feeds every scorer.
4. **Citation leads were not recognized.** `arXiv:2610.10381`, `#53183`, and `(C1, C3)` styles all
   scored as uncited. The lead pattern and the resolver now handle them.

The task scopes also told the writer to nest, which made nesting a property of the prompt, not of
the skill. That hint is removed. The retracted headline (v0 0.306 to v1 0.477) is superseded by:

## 4. Corrected baseline: v0 vs v1 (same scorer, same gold, fresh packs)
Writer: Claude. Judges: Codex + Claude. "raw" is the composite before the floor multiplier.

| task | v0 | v1 | v0 raw | v1 raw | pages v0 / v1 | kappa range |
|---|---|---|---|---|---|---|
| f1-arxiv-cslg | 0.177 | 0.195 | 0.59 | 0.65 | 6.6 / 4.6 (flat) | 0.72 to 0.86 |
| f2-releases | 0.176 | 0.204 | 0.59 | 0.68 | 4.6 / 5.1 (flat) | 0.38 to 0.66 |
| f3-multitool | 0.962 | 0.964 | 0.96 | 0.96 | 1 page, correct | n/a |
| h1-arxiv-cscr | 0.166 | 0.156 | 0.55 | 0.52 | 5.8 / 5.8 (flat) | 0.50 to 0.69 |
| h2-releases | 0.157 | 0.203 | 0.52 | 0.68 | 4.5 / 5.5 (flat) | 0.44 to 0.82 |

Integration recall ranges 0.25 to 0.56 on the four large tasks; vital-nugget recall 0.68 to 0.86.

## 5. Findings
- **The length problem is not solved.** With no nesting hint in the prompt, neither v0 nor v1 nests;
  every large task becomes a 4.5 to 6.6 page monolith and fails the length floor. The v1 nesting
  rule, softened into "a judgment call" after peer review, is too permissive to change behavior.
  This is the first target of the next iteration: a concrete trigger (draft over ~3 pages means nest)
  while keeping the "do not fragment a brief that fits" guard.
- **v1 content is modestly better** on 3 of 4 large tasks (raw +0.06 to +0.16) and slightly worse on
  h1 (-0.03), at n=1 per cell. Treat as suggestive, not significant.
- **The benchmark is unsaturated where it matters.** Integration recall tops out at 0.56, and the
  floors still bite. **F3 is saturated** (0.96 for both versions) and needs a harder variant.
- **Judges mostly agree** (kappa 0.38 to 0.86, mostly substantial), so a two-judge mean is a reasonable
  signal; single-run variance is still the main threat.
- The v1 interview fix (parameter-shaped questions, no invented names) is not exercised by these
  frozen-corpus tasks; it is checked in the harness QA run instead (see the repo AGENTS.md).

## 6. Threats to validity
n=1 run per cell; gold is model-authored then auto-vetted (spot-checked by hand, not fully
human-verified); F3 is synthetic and saturated; the writer is a single model family.

## 7. Reproduce
```
cd plugins/kung-fu-pack/bench && export PYTHONPATH=$PWD
python3 gold/author.py --corpus tasks/fixtures/f1_arxiv_cslg --kind landscape   # rebuild gold
python3 drive_synth.py --results r2 --workers 5     # produce + score all tasks with the current skill (new run id;
                                                     # r0/r1 are the curated runs, do not overwrite)
python3 drive_synth.py --results r1 --rescore       # rescore existing packs (e.g. after a scorer change)
```
Set `KFP_CODEX_PROFILE` if your Codex judge needs a named profile. Raw packs and logs go to
`~/kung-fu-pack-eval` (outside the repo); curated results land in `results_r0/` and `results_r1/`.
