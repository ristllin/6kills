# kung-fu-pack hill-climb: method and run report

Status: **honest partial.** This documents the eval method and framework, the real preflight and
deterministic-scorer results, and states plainly what did and did not run in the time window. No
hill-climb iteration numbers are fabricated.

## 1. Objective
Objectively improve the `kung-fu-pack` skill (research a target across available tools, write a 1-3
page briefing) by hill-climbing its method text against a benchmark, using three harnesses on three
independent quota pools (Claude via foundry-anthropic, Codex/astra via foundry-openai, Vibe/ML4
direct to Mistral), with a single orchestrator as gatekeeper.

## 2. Method (as designed and built)
- **Artifact optimized:** `skills/kung-fu-pack/SKILL.md` + references (prompt engineering), not new code.
- **Primary metric, comprehension transfer:** a cold reader model that did not write the brief answers
  the task's `gold_questions` from the brief only; score = fraction correct; efficiency = score per
  1000 words (punishes padding).
- **Quality rubric:** coverage, grounding, insight, navigability; cross-judged across astra + ML4 +
  opus to de-bias (judge never equals writer).
- **Deterministic guardrails + hard floors:** em-dashes == 0, length in [1,3] pages, lead-coverage,
  and **source-coverage precision/recall/F1** vs each task's `gold_sources`. The source-coverage
  metric is tool-agnostic (matches on source identity, not the connector that supplied it), so it is
  the anti-overfit routing signal: a brief that got the right fact from Jira instead of Linear still
  scores. Composite uses per-metric floors so nothing wins by wrecking another axis (`config.py`).
- **Anti-overfit design:** dev vs holdout split on the task suite (`tasks.jsonl`), plus the
  source-coverage metric; the intent is to iterate on dev and confirm no holdout regression.

## 3. What ran (real)
### Preflight (3-harness, one per provider, anti-throttle)
| Harness | Model | Provider pool | Probe |
|---|---|---|---|
| Claude Code | opus | foundry-anthropic | PASS (returned the probe token) |
| Codex | gpt-6-astra | foundry-openai | PASS (returned the probe token) |
| Vibe | ml4 | mistral (direct) | FAIL: Mistral rejected the inherited `MISTRAL_API_KEY` |

Astra (the peer-reviewer gate) and Claude are up. The three sit on three separate quotas, which was
the anti-throttle plan.

### Deterministic scorers (real, no model calls)
Run on two synthetic sample packs (`tasks/fixtures/sample_packs/{good,bad}`):

| metric | good pack | bad pack |
|---|---|---|
| em_dash_ok | true (0 dashes) | false (2 dashes caught) |
| length_ok [1,3 pp] | false (0.1 pp, sample too short) | false (7.2 pp, too long caught) |
| lead_coverage | 1.0 | 0.0 |
| source_coverage F1 | 1.0 | 0.667 |

See `report/figures/deterministic_demo.svg`. The scorers behave correctly: they catch dashes,
over/under-length, missing leads, and partial source coverage. Two honest caveats: (a) the "good"
sample is deliberately tiny so it fails the length floor; that is the floor working, not a bug; (b) the
source matcher can over-credit a common token (for example "example"), so real gold sources should use
distinctive identifiers. Both are noted for the next iteration.

## 4. What did NOT run, and why
**The model-driven hill-climb loop did not run.** Root cause: the run idled waiting on a one-time
Mistral-key fix (the inherited `MISTRAL_API_KEY` was stale; vibe reads it straight from env) and the
optimization window (roughly six hours) elapsed before that was resolved, leaving about 30 minutes
before the 16:00 deadline. That is an orchestration failure on my part: the key-independent harness
should have been built during the wait instead of idling. In the final window I prioritized shipping a
correct, honest, runnable slice over rushed or fabricated results.

Not run: producing briefs by launching the skill on each harness; the comprehension quiz and the
LLM-judge; any accepted/rejected variant iterations; a baseline-to-final curve.

## 5. What is complete vs remaining
Complete and runnable now: `config.py`, `scorers/deterministic.py`, `scorers/__init__.py` dispatch,
`harnesses/manifest.py`, `runner.py` (deterministic scoring over packs), the 6-task 4-category
`tasks.jsonl`, the sample-pack self-test, this report, and the figure.

Remaining to run the full loop: `harnesses/run.py` + `prompt.py` (launch the skill on claude/vibe/codex
to WRITE each pack), `scorers/quiz.py` + `judge.py` (comprehension + rubric, dual-protocol, never-raise,
self-test), `metrics.py` + `report/generate.py` (aggregate and diff archived result dirs into an
iteration story), and `orchestrator/lane-launch.sh` (the detached
`claude -p --session-id --permission-mode bypassPermissions` lanes + the 10-minute and hourly
supervision crons).

## 6. How to run it (exact)
```
# 1. unblock ML4 once (in a terminal where vibe works):
printf 'MISTRAL_API_KEY=%s\n' "$MISTRAL_API_KEY" >> "$TMPDIR/kfp-run/secrets.env"
# 2. deterministic baseline (no keys):
python3 runner.py --tasks tasks/tasks.jsonl --packs ~/kung-fu-pack-eval/packs --results results_v0
# 3. full scoring (after sourcing the key store), once pack production + quiz/judge land:
set -a; . "$TMPDIR/kfp-run/secrets.env"; set +a
python3 runner.py --tasks tasks/tasks.jsonl --packs ~/kung-fu-pack-eval/packs --results results_v0 --with-models
```

## 7. Threats to validity (for when the loop runs)
- Judge self-preference: mitigated by cross-judging across three model families and by keeping the
  writer out of the judge set.
- Data contamination: public targets may be answerable from parametric memory; mitigate with
  recency/holdout and by requiring claims to trace to reached sources (grounding + source-coverage).
- Judge or length gaming: the efficiency ratio and an adversarial unsupported-claim pass counter it.
- Small n: 6 tasks is a dev-scale suite; widen before drawing strong conclusions.

## 8. Honest bottom line
A correct, documented, runnable eval scaffold with a working deterministic tier and a real task suite
is delivered. The model-driven hill-climb was not executed in the window. No results are invented. The
next session can run the loop directly with the commands above.
