"""Produce + score briefs for a skill version. Baseline and each hill-climb iteration
call this with a different --skill and --results, so result dirs archive each version.

    python drive.py --skill skills/kung-fu-pack/SKILL.md --results results_v0 \
        --ids sci-attention,eng-speculative-decoding --writer claude --with-models
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import config
import scorers
from harnesses import run as run_mod, manifest as manifest_mod

BENCH = Path(__file__).resolve().parent


def composite(scores: dict) -> dict:
    d = scores.get("deterministic", {})
    comp = (scores.get("comprehension") or {})
    jud = (scores.get("judge") or {})
    w = config.WEIGHTS
    cov = d.get("source_coverage", {}).get("f1", 0.0)
    comprehension = comp.get("comprehension", 0.0) if comp.get("ran") else 0.0
    efficiency = min(1.0, comp.get("efficiency", 0.0)) if comp.get("ran") else 0.0
    grounding = d.get("lead_coverage", 0.0)
    score = (w["comprehension"] * comprehension + w["efficiency"] * efficiency +
             w["grounding"] * grounding + w["source_coverage"] * cov)
    floors_ok = d.get("floors_pass", False) and cov >= config.FLOORS["source_coverage"]
    return {
        "composite": round(score, 4),
        "comprehension": comprehension, "efficiency": round(efficiency, 3),
        "grounding": grounding, "source_coverage": cov,
        "quality": jud.get("quality", 0.0) if jud.get("ran") else 0.0,
        "floors_ok": bool(floors_ok),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default="skills/kung-fu-pack/SKILL.md")
    ap.add_argument("--tasks", default="bench/tasks/tasks.jsonl")
    ap.add_argument("--ids", default="")
    ap.add_argument("--writer", default="claude")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--results", default="results_v0")
    ap.add_argument("--packs-root", default=str(config.WORKSPACE / "packs"))
    ap.add_argument("--with-models", action="store_true")
    a = ap.parse_args()

    skill_text = (BENCH.parent / a.skill).read_text() if not Path(a.skill).exists() \
        else Path(a.skill).read_text()
    tasks_path = Path(a.tasks) if Path(a.tasks).exists() else BENCH / "tasks/tasks.jsonl"
    tasks = [json.loads(l) for l in tasks_path.read_text().splitlines() if l.strip()]
    if a.ids:
        want = set(a.ids.split(","))
        tasks = [t for t in tasks if t["instance_id"] in want]
    results = (BENCH / a.results) if not Path(a.results).is_absolute() else Path(a.results)
    results.mkdir(parents=True, exist_ok=True)
    packs_root = Path(a.packs_root).expanduser()

    for t in tasks:
        tid = t["instance_id"]
        cell = f"{a.writer}__{a.model}__{tid}"
        pack = packs_root / f"{a.results}__{cell}"
        rec = {"cell": cell, "instance_id": tid, "version": a.results, "t": time.time()}
        agent = run_mod.run_one(t, a.writer, a.model, pack, skill_text)
        rec["agent"] = agent
        manifest_mod.build(pack)
        rec["scores"] = scorers.score(t, pack, with_models=a.with_models)
        rec["composite"] = composite(rec["scores"])
        rec["scored"] = True
        (results / f"{cell}.json").write_text(json.dumps(rec, indent=2))
        c = rec["composite"]
        print(f"{cell}: composite={c['composite']} comp={c['comprehension']} "
              f"ground={c['grounding']} srcF1={c['source_coverage']} "
              f"floors={c['floors_ok']} ({agent['duration_s']}s)", flush=True)


if __name__ == "__main__":
    main()
