# kung-fu-pack benchmark v2: a hard, unsaturated synthesis eval, and one gated hill-climb cycle

The first eval was saturated (a self-reported comprehension quiz ceilinged at 1.0) and could not
drive improvement. This rebuilds the benchmark around published, reimplementable methods so it is
genuinely hard and unsaturated, then runs one full gated hill-climb cycle. All numbers below are real;
nothing is fabricated.

## 1. What the benchmark measures
Three task families, each "many sources -> a tight brief", with frozen post-cutoff corpora so the
answer cannot come from parametric memory:
- **F1 arxiv-landscape:** compress ~220 recent cs.LG abstracts into a landscape (hard compression +
  distinct coverage).
- **F2 release-digest:** digest several vLLM/Transformers versions into a what-changed brief (nesting
  + cross-version integration).
- **F3 distributed-evidence:** a 3-source corpus (design doc, issue tracker, changelog) where key
  facts require combining 2+ sources (Loong-style "no single source has the answer").

Grading stack (`scorers/`), composite with hard floors, built from proven methods:
- **eligibility gate** (FACTS-style): rejects evasive/empty briefs before scoring.
- **nugget recall + integration recall** (AutoNuggetizer AutoAssign, model-judged not heuristic):
  fraction of gold vital nuggets, and of integration-facts that each need 2+ sources, that the brief
  conveys. Integration recall is the hard, unsaturated core.
- **citation** (ALCE-inspired): leads present and resolving to the frozen corpus.
- **anti-redundancy** and **tool-agnostic source-coverage** (anti-overfit routing).
- **nesting-appropriateness:** rewards an index + linked sub-pages when the corpus truly warrants it,
  penalizes a monolith overflow, rewards a tight single page when that fits.
- Floors: eligibility, em-dashes == 0, and a length rule that a nest-expected task passes only by
  actually nesting or staying within budget.

Writer: Claude (opus). Judge: astra (gpt-6, independent of the writer). ML4 was blocked on a stale
Mistral key, so this run is single-judge; cross-judge with opus is the documented next step.

## 2. Unsaturation (the gate the old eval failed)
Baseline v0 composite by task: **F1 0.072, F2 0.143, F3 0.702.** A wide spread with large headroom,
and F1/F2 fail the floors (they overflowed to 3.8 and 3.6 pages). Integration recall at baseline is
**0.0 / 0.167 / 0.8**. This is the opposite of the old 1.0 ceiling: the benchmark discriminates and
leaves plenty to climb.

## 3. Iteration v1 (the two reported skill bugs), measured
Applied as the first iteration: (1) clarifying questions made parameter-shaped (never invent specific
project names); (2) a nesting methodology (index + linked sub-pages on genuine overflow instead of a
monolith). Same scorer for both versions.

| task | v0 | v1 | delta |
|---|---|---|---|
| F1 arxiv-landscape | 0.072 | 0.248 | +0.176 (now nests: index + 7 theme sub-pages; floors pass) |
| F2 release-digest | 0.143 | 0.478 | +0.335 (nests: index + per-project sub-pages) |
| F3 distributed-evidence | 0.702 | 0.706 | +0.004 (correctly stays a single page; no regression) |
| **avg** | **0.306** | **0.477** | **+0.171** |

See `report/figures/v2_v0_v1.svg`. The benchmark detected the real fix: nesting resolved the overflow
on the big-corpus tasks and did not fragment the small one.

**Peer review (astra):** returned **revise**, flagging that a rigid page-count trigger could fragment
readable briefs and duplicate overview prose. Addressed before accepting: nesting is now a complexity
judgment, the index links to sub-pages and does not duplicate them, and a brief that reads well as one
page is never fragmented. Re-ran F2 with the revised wording: still nests, composite 0.478 (held).

**Gatekeeper decision: ACCEPT v1.** Composite up on the overflow tasks, no regression on the flat
task, peer-review concern resolved.

## 4. Honest findings
- **Integration recall barely moved** (F1 still 0.0, F2 0.167). Nesting fixes structure, not the hard
  compression/synthesis core. That core is the real remaining headroom and the next hill-climb target,
  and its persistence is evidence the benchmark is not gameable by formatting alone.
- **A scorer bug was found and fixed mid-cycle:** the deterministic scorer only read `out/page.md`, so
  nested packs looked empty and failed floors. Fixed to read `index.md` + sub-pages. v0 (monoliths)
  was unaffected, so the v0-vs-v1 comparison stays fair.
- **Judge stochasticity:** F3 integration recall varied 0.8 to 1.0 across identical re-runs
  (single-judge). Deltas under ~0.05 are noise; the v1 nesting gains (+0.18, +0.34) are well beyond it.

## 5. Threats to validity
n = 3 dev tasks; single judge (astra), cross-judge pending ML4; gold for F1/F2 proposed by a model
then vetted (integration-facts confirmed to need 2+ sources); F1 writing is slow (8 files) and timed
out once during production (re-scored from the produced pack). Widen tasks, add the opus cross-judge,
and harden the nugget match before strong claims.

## 6. Reproduce
```
cd plugins/kung-fu-pack/bench && export PYTHONPATH=$PWD
# rebuild corpora (post-cutoff): python3 corpora/arxiv.py ... ; python3 corpora/releases.py ...
# baseline and iteration:
python3 drive_synth.py --results v0 --writer claude --ids f1-arxiv-cslg,f2-releases,f3-multitool
python3 drive_synth.py --results v1 --writer claude --ids f1-arxiv-cslg,f2-releases,f3-multitool
# deterministic-only scoring needs no keys: python3 scorers/deterministic.py <pack_dir>
```

## 7. Bottom line
A hard, unsaturated benchmark exists and is verified to discriminate (spread 0.07 to 0.70, integration
recall as low as 0.0). One full gated cycle ran: baseline, a measured fix, independent peer review,
a revision, and an evidence-based accept, with the net skill genuinely improved on structure while the
hard synthesis core remains open as the next lever.
