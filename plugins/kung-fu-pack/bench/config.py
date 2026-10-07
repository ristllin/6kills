"""Central config for the kung-fu-pack hill-climb eval.

One place for the three harnesses, their models/providers (three independent quota
pools, so parallel runs do not throttle a single quota), the run budget, and the
judge/quiz settings. Values are env-overridable so operating points can be swept
without editing code. No secret values live here: keys come from the ephemeral
env store sourced before any run (see orchestrator/).
"""
from __future__ import annotations

import os
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
# Raw, bulky, possibly-sensitive run artifacts live OUTSIDE the repo.
WORKSPACE = Path(os.environ.get("KFP_EVAL_WORKSPACE", Path.home() / "kung-fu-pack-eval"))
# Only curated results/metrics are written back under the repo for commit.
RESULTS_DIR = Path(os.environ.get("KFP_RESULTS_DIR", BENCH_DIR / "results"))

# --- harnesses: each on its own provider quota (anti-throttle) ---------------
# "launch" is a template; harnesses/run.py fills {prompt}/{workdir}/{model}.
HARNESSES: dict[str, dict] = {
    "claudecode": {
        "provider": "foundry-anthropic",
        "writer": True,   # can author/propose+run skill variants
        "judge": True,
    },
    "vibe": {
        "provider": "mistral-direct",
        "writer": True,
        "judge": True,
    },
    "codex": {
        "provider": "foundry-openai",
        "writer": False,  # reserved as peer reviewer + cross-judge
        "judge": True,
    },
}

# --- models per harness (pin exact ids; never float on an alias) -------------
MODELS: dict[str, dict] = {
    "opus": {"harness": "claudecode", "id": os.environ.get("KFP_OPUS_ID", "opus")},
    "ml4": {"harness": "vibe", "id": "ml4"},
    "astra": {"harness": "codex", "id": "gpt-6-astra"},
}

# --- run budget (env-overridable for operating-point sweeps) -----------------
BUDGET = {
    "max_turns": int(os.environ.get("KFP_MAX_TURNS", "40")),
    "max_price_usd": float(os.environ.get("KFP_MAX_PRICE", "2.0")),
    "wall_s": int(os.environ.get("KFP_WALL_S", "900")),
    "workers": int(os.environ.get("KFP_WORKERS", "3")),  # bounded; scale watching 429s
}

# --- judge / comprehension-quiz settings -------------------------------------
# Primary metric is comprehension transfer: a COLD reader model (never the writer)
# answers gold questions from the brief only. Cross-judged for de-bias.
JUDGE = {
    # reader/judge must differ from the brief's writer harness; picked per-cell.
    "readers": os.environ.get("KFP_READERS", "astra,ml4,opus").split(","),
    "quiz_pass": float(os.environ.get("KFP_QUIZ_PASS", "0.7")),   # fraction correct = pass
    "rubric_axes": ["coverage", "grounding", "insight", "navigability"],
}

# --- composite score weights + per-metric floors (nothing wins by wrecking) --
WEIGHTS = {
    "comprehension": 0.45,   # primary
    "efficiency": 0.15,      # comprehension per 1000 words
    "grounding": 0.20,       # claims trace to a resolvable lead
    "source_coverage": 0.20,  # routing F1 vs gold_sources (anti-overfit)
}
FLOORS = {
    "em_dash": 0,            # hard: must be exactly 0
    "length_pages": (1, 3),  # hard: brief within 1-3 A4 pages
    "source_coverage": float(os.environ.get("KFP_FLOOR_SRC_COV", "0.5")),
    "comprehension": float(os.environ.get("KFP_FLOOR_COMP", "0.0")),  # no regression vs base
}
