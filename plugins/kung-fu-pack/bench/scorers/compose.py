"""Merge the full scorer stack into one composite with hard floors.

Layers (see each module): eligibility gate + nugget/integration recall (nuggets.py, model-judged),
citation resolvability (citation.py), anti-redundancy (coverage.py), nesting-appropriateness
(nesting.py), and the tool-agnostic source-coverage routing metric (deterministic.py). The
composite weights the HARD, unsaturated core (integration recall) highest. Hard floors gate the
score so nothing wins by being evasive, dash-ridden, or over-length.
"""
from __future__ import annotations

import json
from pathlib import Path

from scorers import deterministic, nuggets, citation, coverage, nesting

WEIGHTS = {
    "integration_recall": 0.35,   # the hard, unsaturated core
    "vital_nugget_recall": 0.25,
    "citation_recall": 0.15,
    "source_coverage_f1": 0.10,
    "nesting": 0.10,
    "non_redundancy": 0.05,
}


def score_all(task: dict, pack_dir: Path, with_models: bool = True) -> dict:
    pack = Path(pack_dir)
    det = deterministic.score(task, pack)
    nug = nuggets.score(task, pack) if with_models else {"ran": False, "reason": "models off"}
    cit = citation.score(task, pack)
    cov = coverage.score(task, pack)
    nst = nesting.score(task, pack)

    eligible = nug.get("eligible", True) and det.get("has_brief", False)
    em_ok = det.get("em_dash_ok", False)
    # length floor: a flat brief must be within budget; a nest-expected task passes only if it
    # actually nested (index + sub-pages) or still fit the budget. A monolith overflow fails.
    if task.get("expect_nested"):
        length_ok = bool(nst.get("nested")) or det.get("length_ok", False)
    else:
        length_ok = det.get("length_ok", False)
    floors_pass = bool(eligible and em_ok and length_ok)

    parts = {
        "integration_recall": nug.get("integration_recall", 0.0),
        "vital_nugget_recall": nug.get("vital_nugget_recall", 0.0),
        "citation_recall": cit.get("recall", 0.0),
        "source_coverage_f1": det.get("source_coverage", {}).get("f1", 0.0),
        "nesting": nst.get("appropriateness", 0.0),
        "non_redundancy": cov.get("non_redundancy", 0.0),
    }
    raw = sum(WEIGHTS[k] * parts[k] for k in WEIGHTS)
    composite = round(raw if floors_pass else raw * 0.3, 4)  # floor breach is heavily penalized
    return {
        "composite": composite,
        "floors_pass": floors_pass,
        "parts": {k: round(v, 3) for k, v in parts.items()},
        "detail": {"deterministic": det, "nuggets": nug, "citation": cit,
                   "coverage": cov, "nesting": nst},
    }


if __name__ == "__main__":
    import sys
    t = {}
    cp = sys.argv[2] if len(sys.argv) > 2 else None
    if cp:
        t["corpus_path"] = cp
    print(json.dumps(score_all(t, Path(sys.argv[1])), indent=2))
