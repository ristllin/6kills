"""Scorer dispatch for the kung-fu-pack eval.

Two tiers:
  - deterministic: fast, no model calls, the hard floors + anti-overfit routing metric.
  - model-based (quiz, judge): the comprehension-transfer primary metric + quality
    rubric; these need API keys and minutes per brief, so they are opt-in.

`score(task, pack_dir, with_models=False)` returns the merged metric block. With
`with_models=True` it also runs the comprehension quiz and the LLM-judge if those
modules and keys are available; it never raises on a model failure (records a reason).
"""
from __future__ import annotations

from pathlib import Path

from . import deterministic


def score(task: dict, pack_dir: Path, with_models: bool = False) -> dict:
    out = {"deterministic": deterministic.score(task, pack_dir)}
    if with_models:
        try:
            from . import quiz
            out["comprehension"] = quiz.score(task, pack_dir)
        except Exception as e:  # noqa: BLE001
            out["comprehension"] = {"ran": False, "reason": str(e)[:200]}
        try:
            from . import judge
            out["judge"] = judge.score(task, pack_dir)
        except Exception as e:  # noqa: BLE001
            out["judge"] = {"ran": False, "reason": str(e)[:200]}
    return out
