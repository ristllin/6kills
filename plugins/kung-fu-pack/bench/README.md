# kung-fu-pack eval and hill-climb harness

A benchmark for the `kung-fu-pack` skill (research a target across available tools, write a
1-3 page briefing) and a loop to hill-climb the skill text against it. Built on a standard
cross-product eval pattern (resumable runner, dual-tier scoring, metrics, report), specialized
for briefing quality.

## What it measures
- **Comprehension transfer (primary, model-based):** a cold reader model that did NOT write the
  brief answers the task's `gold_questions` from the brief only; score is fraction correct, plus
  efficiency = score per 1000 words. See `scorers/quiz.py`.
- **Quality rubric (model-based):** coverage, grounding, insight, navigability; cross-judged across
  astra, ML4, and opus to de-bias. See `scorers/judge.py`.
- **Guardrails (deterministic, no keys):** em-dash count (hard floor 0), length in [1,3] pages,
  lead-coverage, and **source-coverage precision/recall/F1** vs the task `gold_sources` (the
  anti-overfit routing metric: did it reach the right sources regardless of which tool supplied
  them). See `scorers/deterministic.py`.

Composite + per-metric floors live in `config.py` so nothing improves by wrecking another axis.

## Layout
```
bench/
  config.py            harnesses (3 provider pools), budget, judge, weights, floors
  runner.py            resumable scorer over produced packs -> results/<cell>.json
  harnesses/
    manifest.py        emit pack.json from a kung-fu-pack workspace (so scoring is not prose-parsing)
    run.py             (model layer) launch the skill on a harness to WRITE a pack  [see Status]
    prompt.py          build the research brief per task                            [see Status]
  scorers/
    deterministic.py   guardrails + routing metric (runnable now, no keys)
    quiz.py judge.py   comprehension quiz + rubric (need keys + minutes/brief)      [see Status]
  tasks/
    tasks.jsonl        6 tasks across the 4 categories (code, science, eng, company)
    fixtures/sample_packs/{good,bad}/  synthetic packs for scorer self-test
  metrics.py report/   aggregation + report generator + figures/
  orchestrator/        lane launch + supervision scripts for the hill-climb         [see Status]
```

## Run
Deterministic scoring works now with no keys:
```
python3 scorers/deterministic.py tasks/fixtures/sample_packs/good
python3 runner.py --tasks tasks/tasks.jsonl --packs ~/kung-fu-pack-eval/packs --results results_v0
```
Full (model-based) scoring, after sourcing the ephemeral key store:
```
set -a; . "$TMPDIR/kfp-run/secrets.env"; set +a
python3 runner.py --tasks tasks/tasks.jsonl --packs ~/kung-fu-pack-eval/packs \
    --results results_v0 --with-models
```
Producing packs (the skill WRITING each brief on each harness) is driven by
`orchestrator/lane-launch.sh`; producing and scoring are decoupled so each is resumable.

## Status
The full pipeline ran end to end for real: `drive.py` produces a brief with a writer harness (Claude),
then scores it with the deterministic tier + the astra comprehension quiz + the astra rubric, computes
the composite, and archives `results_vN/`. One complete gated hill-climb cycle executed (baseline v0,
a proposed v1, astra peer review, gatekeeper reject + revert). See `HILLCLIMB_REPORT.md` for the real
numbers, the decision log, and the next levers (metric hardening + a harder/wider task suite). ML4 was
not used (stale Mistral key), so this run was single-judge; cross-judge is the documented next step.
