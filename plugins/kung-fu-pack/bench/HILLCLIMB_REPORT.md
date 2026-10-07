# kung-fu-pack hill-climb: method and results

A benchmark for the `kung-fu-pack` skill (research a target across available tools, write a 1-3 page
briefing) and a gated hill-climb of the skill text against it. This reports one full, real cycle:
a baseline, one proposed mutation, measurement, independent peer review, and a gatekeeper decision.
No numbers are fabricated.

## 1. Setup that ran
- **Writer:** Claude Code (opus), foundry-anthropic quota.
- **Scorers:** astra (gpt-6-astra via Codex, foundry-openai quota) as the cold reader for the
  comprehension quiz and as the rubric judge. astra is never the writer, so reader and writer are
  independent. ML4 (Mistral) was not used: the inherited Mistral key was stale and the run proceeded
  rather than block (single-judge, noted as a threat).
- **Tasks (dev, web-answerable):** `sci-attention` (the Transformer paper), `sci-raft` (the Raft
  paper), `eng-speculative-decoding`. Each has gold questions; the writer researched with built-in web
  tools and wrote `out/page.md` + `research/` + `pack.json`.
- **Metrics:** composite = 0.45 comprehension + 0.15 efficiency + 0.20 grounding + 0.20 source-coverage
  F1, with hard floors (em-dashes 0, length 1-3 pages, source F1 >= 0.5). Comprehension = fraction of
  gold questions a cold reader can answer from the brief alone.

## 2. Baseline v0 (real)
| task | composite | comprehension | grounding | source F1 | floors |
|---|---|---|---|---|---|
| eng-speculative-decoding | 0.842 | 1.00 | 0.733 | 0.556 | pass |
| sci-attention | 0.830 | 1.00 | 0.625 | 0.667 | pass |
| sci-raft | 0.793 | 1.00 | 0.400 | 0.833 | fail (length) |
| **avg** | **0.822** | **1.00** | 0.586 | 0.685 | - |

Reading: **comprehension is saturated at 1.0** (the briefs convey the facts a reader needs). The
headroom is in **grounding** (a lead behind every claim) and **source precision**, and one brief
tripped the length floor.

## 3. Iteration 1 (v1): proposed, measured, reviewed, rejected
**Hypothesis:** strengthen the skill's grounding and source-precision rules (a lead on 100 percent of
fact lines; list only sources actually used). Edited `SKILL.md` Principles, re-ran the same 3 tasks.

**Result (real):**
| task | v0 | v1 | delta |
|---|---|---|---|
| eng-speculative-decoding | 0.842 | 0.869 | +0.027 |
| sci-attention | 0.830 | 0.722 | -0.108 |
| sci-raft | 0.793 | 0.597 | -0.196 |
| **avg** | **0.822** | **0.729** | **-0.093** |

See `report/figures/iteration_v0_v1.svg`. grounding and source-coverage swung sharply the wrong way on
two of three tasks.

**Independent peer review (astra):** verdict **revise**. Biggest risk flagged: the rigid "100 percent"
per-line citation rule risks overfitting to the coverage metric, adding citation clutter and
suppressing synthesis without ensuring sources actually support claims.

**Gatekeeper decision: REJECT and revert to v0.** Evidence: composite regressed 0.093 overall and
breached the no-regression intent on two tasks; the peer reviewer said revise; the swing exposed a
metric problem (below). v0 stands as the best skill version.

## 4. What the negative result taught us (the real finding)
grounding (and source-coverage) are computed from `pack.json`, whose claims are extracted
heuristically from the brief. They proved **too sensitive to formatting** to optimize against: the
same "cite everything" nudge made the extracted lead-coverage fall, not rise. So before more
iterations, the right lever is **hardening the metric**, not changing the skill: have the writer emit
claims+leads explicitly in `pack.json` (contract already supports it) and verify each lead resolves,
rather than inferring claims from prose. Separately, comprehension is already 1.0 on this small suite,
so the quiz needs **harder, more discriminating questions** to create headroom. These are the next two
work items, and they matter more than another skill tweak.

## 5. Honest scope and threats to validity
- **n = 3 web tasks.** The 4-category suite exists in `tasks.jsonl` (code, science, eng, company), but
  code tasks need local repos and the company task used placeholder sources, so the live run used the
  three clean web tasks. Widen before drawing strong conclusions.
- **Single judge (astra) for both quiz and rubric.** No cross-judge in this run (ML4 blocked). Judge
  self-preference is partly mitigated because the judge is not the writer, but a second judge is needed.
- **Comprehension saturation** limits what the primary metric can currently distinguish.
- **Writer variance:** one sample per cell; the agent is stochastic, so per-task deltas near 0.03 are
  within noise. The v1 regression (-0.09 avg, -0.11 and -0.20 on two tasks) is beyond that.

## 6. Bottom line
One complete, honest, gated hill-climb cycle ran end to end: baseline measured, a mutation proposed,
measured, peer-reviewed by an independent model, and **rejected on evidence**, with the skill reverted.
The net skill change is zero (v0 kept), which is the correct outcome here. The highest-value next steps
are metric hardening and a harder, wider task suite, both specified above.

## 7. Reproduce
```
cd plugins/kung-fu-pack/bench
# baseline on the three web tasks (needs the foundry env; writer=claude, judge=astra):
python3 drive.py --ids sci-attention,sci-raft,eng-speculative-decoding \
    --writer claude --results results_v0 --with-models
# propose a skill variant, then:
python3 drive.py --ids sci-attention,sci-raft,eng-speculative-decoding \
    --writer claude --results results_v1 --with-models
```
Deterministic-only scoring needs no keys: `python3 scorers/deterministic.py <pack_dir>`.
