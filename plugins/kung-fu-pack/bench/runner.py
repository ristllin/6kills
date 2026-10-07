"""Resumable scorer runner for kung-fu-pack packs.

Given a tasks file and a directory of produced packs (one per cell), it builds each
pack's manifest, scores it, and writes result.json per cell. Deterministic scoring
runs with no keys; pass --with-models to also run the comprehension quiz + judge
(needs API keys from the ephemeral env store and minutes per brief).

The brief-production step (launching the kung-fu-pack skill on claude/vibe/codex to
WRITE each pack) is driven by orchestrator/lane-launch.sh; this runner scores whatever
packs exist, so producing and scoring are decoupled and independently resumable.

Usage:
    python runner.py --tasks tasks/tasks.jsonl --packs ~/kung-fu-pack-eval/packs \
        --results results_v0 [--with-models]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import scorers
from harnesses import manifest as manifest_mod


def _load_tasks(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def run(tasks_path: Path, packs_root: Path, results: Path, with_models: bool) -> None:
    tasks = _load_tasks(tasks_path)
    results.mkdir(parents=True, exist_ok=True)
    done = 0
    for t in tasks:
        tid = t["instance_id"]
        # a cell is <harness>__<model>__<instance>; score every pack dir we find for it
        for pack in sorted(packs_root.glob(f"*__{tid}")) or [packs_root / tid]:
            if not pack.exists():
                continue
            cell = pack.name
            out_file = results / f"{cell}.json"
            if out_file.exists() and json.loads(out_file.read_text()).get("scored"):
                done += 1
                continue
            try:
                manifest_mod.build(pack)
            except Exception:
                pass
            rec = {
                "cell": cell, "instance_id": tid, "benchmark": t.get("benchmark"),
                "t": time.time(), "scored": False,
            }
            try:
                rec["scores"] = scorers.score(t, pack, with_models=with_models)
                rec["scored"] = True
            except Exception as e:  # noqa: BLE001
                rec["error"] = str(e)[:300]
            out_file.write_text(json.dumps(rec, indent=2))
            done += 1
            d = rec.get("scores", {}).get("deterministic", {})
            print(f"[{done}] {cell} floors_pass={d.get('floors_pass')} "
                  f"em={d.get('em_dashes')} pages={d.get('length_pages')} "
                  f"src_f1={d.get('source_coverage', {}).get('f1')}", flush=True)
    print(f"done. scored {done} packs -> {results}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--packs", required=True)
    ap.add_argument("--results", default="results_v0")
    ap.add_argument("--with-models", action="store_true")
    a = ap.parse_args()
    run(Path(a.tasks), Path(a.packs).expanduser(), Path(a.results), a.with_models)
