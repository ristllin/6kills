# kung-fu-pack synthesis benchmark

Measures how well the `kung-fu-pack` skill compresses many sources into a tight, navigable brief,
so the skill text can be hill-climbed against evidence. Results and the audit trail are in
[`HILLCLIMB_REPORT.md`](HILLCLIMB_REPORT.md).

## What it measures
- **Integration recall** (the hard core): facts that only exist by combining 2+ sources.
- **Vital and all-nugget recall:** corpus-level points a good brief must carry.
- **Citation:** fact lines with a lead, and leads that resolve to the frozen corpus.
- **Structure:** nesting appropriateness and anti-redundancy.
- **Floors:** eligibility, zero em/en dashes, and a length rule (nest or stay within 3 pages).

Recall is judged by a two-model panel (Codex + Claude by default, `KFP_JUDGES`), with Cohen's kappa
recorded per brief.

## Layout
```
bench/
  drive_synth.py       produce a brief per task with a writer harness, then score it
  config.py            workspace path (raw packs live outside the repo)
  harnesses/llm.py     subprocess callers for claude / codex / vibe
  harnesses/manifest.py  emit pack.json from a pack workspace
  corpora/             freezers: arXiv abstracts, GitHub release notes
  gold/author.py       map-reduce gold authoring over the whole corpus
  scorers/             brief reader, nuggets (+ eligibility), citation, coverage, nesting,
                       deterministic floors, compose (composite + floors), taste (product packs:
                       does the pack show the thing; absolute and order-swapped pairwise)
  tasks/synth_tasks.jsonl            3 dev + 2 held-out tasks
  tasks/fixtures/<task>/             frozen corpus + gold.json
  results_r0/ results_r1/            curated scores for skill v0 and v1
```

## Run
```
cd plugins/kung-fu-pack/bench && export PYTHONPATH=$PWD
python3 drive_synth.py --results r2 --workers 5                       # current SKILL.md, new run id
python3 drive_synth.py --skill path/to/SKILL.md --results r3 --ids f1-arxiv-cslg
python3 drive_synth.py --results r1 --rescore                         # rescore existing packs only
python3 scorers/deterministic.py <pack_dir>                           # floors, no keys
```
Needs the `claude` and `codex` CLIs authenticated. Set `KFP_CODEX_PROFILE` for a named Codex
profile. Rebuild a corpus with `corpora/arxiv.py` or `corpora/releases.py`, then its gold with
`gold/author.py`.
