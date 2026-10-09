"""Produce + score synthesis briefs for a skill version (the v2 hard benchmark).

For each task: feed the FROZEN corpus to a writer harness running the kung-fu-pack method, have
it write out/page.md + pack.json, then score with the full stack (compose.score_all). Results are
archived per run (results_rN/<cell>.json) for the hill-climb curve.

    PYTHONPATH=. python3 drive_synth.py --skill ../skills/kung-fu-pack/SKILL.md \
        --results r0 --writer claude --ids f3-multitool
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import config
from harnesses import llm, manifest as manifest_mod
from scorers import compose

BENCH = Path(__file__).resolve().parent
MAX_CORPUS_CHARS = int(os.environ.get("KFP_MAX_CORPUS", "400000"))

CONTRACT = """
OUTPUT CONTRACT (write files in your current directory, structured per the skill method):
- Write your brief into out/. You may use a single out/page.md, or, if your method calls for it, an
  out/index.md plus linked out/<section>.md sub-pages. Choose the structure the method prescribes.
- EVERY fact line ends with a lead in parentheses (a source id/url/tag from the corpus). NO em or en
  dashes anywhere (use hyphens). End the top page with a Sources section.
- Also write pack.json: {"output_path":"out/page.md or out/index.md","sources_reached":[...ids/urls
  you used...],"claims":[{"claim":"...","lead":"..."}]}.
Synthesize ONLY from the provided corpus. Compress: find the most important and distinct facts, merge
duplicates, and surface cross-source patterns (facts that need combining multiple sources). Do not pad.
Reply with just: BRIEF_DONE.
"""


def _load_corpus(task: dict) -> str:
    base = BENCH / task["corpus_path"]  # an absolute corpus_path overrides BENCH
    if task.get("corpus_dir"):
        parts = [p.read_text(errors="ignore") for p in sorted((base / task["corpus_dir"]).glob("*"))
                 if p.is_file()]
        return "\n\n".join(parts)
    return (base / task.get("corpus_file", "blurbs.txt")).read_text(errors="ignore")


def build_prompt(task: dict, skill_text: str, corpus: str) -> str:
    skill = skill_text.strip()[:40000]
    return (
        "You are executing the kung-fu-pack skill. Follow its method.\n\n===== SKILL METHOD =====\n"
        + skill + "\n===== END METHOD =====\n\n"
        f"TARGET: {task['target']}\nSCOPE: {task['scope']}\n"
        f"AUDIENCE: {task.get('audience','a technical peer')}\n" + CONTRACT
        + "\n\n===== FROZEN CORPUS (synthesize only from this) =====\n" + corpus[:MAX_CORPUS_CHARS]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", default=str(BENCH.parent / "skills/kung-fu-pack/SKILL.md"))
    ap.add_argument("--tasks", default=str(BENCH / "tasks/synth_tasks.jsonl"))
    ap.add_argument("--ids", default="")
    ap.add_argument("--writer", default="claude")
    ap.add_argument("--model", default="opus", help="cell label only; set KFP_CLAUDE_MODEL to change the model")
    ap.add_argument("--results", default="r0")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--produce-only", action="store_true", help="write packs, score later")
    ap.add_argument("--rescore", action="store_true", help="score existing packs, do not regenerate")
    a = ap.parse_args()

    skill_text = Path(a.skill).read_text()
    tasks = [json.loads(l) for l in Path(a.tasks).read_text().splitlines() if l.strip()]
    if a.ids:
        want = set(a.ids.split(","))
        tasks = [t for t in tasks if t["instance_id"] in want]
    results = BENCH / f"results_{a.results}"
    results.mkdir(parents=True, exist_ok=True)
    packs_root = config.WORKSPACE / "packs"

    def run(t: dict) -> None:
        tid = t["instance_id"]
        cell = f"{a.writer}__{a.model}__{tid}"
        pack = packs_root / f"{a.results}__{cell}"
        fx = BENCH / t["corpus_path"]
        t0 = time.time()
        if not a.rescore:
            if pack.exists():
                shutil.rmtree(pack)  # a fresh pack per run; stale sub-pages would leak into scoring
            (pack / "out").mkdir(parents=True)
            prompt = build_prompt(t, skill_text, _load_corpus(t))
            (pack / "agent.log").write_text(llm.call(a.writer, prompt, cwd=str(pack)))
            if not (pack / "pack.json").exists():  # keep the writer's own manifest
                manifest_mod.build(pack)
            if a.produce_only:
                print(f"{a.results} {cell}: produced ({round(time.time() - t0, 1)}s)", flush=True)
                return
        # gold + sources travel with the pack for scoring (refreshed so rescoring uses current gold)
        if (fx / "gold.json").exists():
            shutil.copy(fx / "gold.json", pack / "gold.json")
        if (fx / "sources").is_dir() and not (pack / "sources").exists():
            shutil.copytree(fx / "sources", pack / "sources")
        t_task = dict(t)
        t_task["corpus_path"] = str(fx)
        sc = compose.score_all(t_task, pack, with_models=True)
        rec = {"cell": cell, "instance_id": tid, "version": a.results, "split": t.get("split"),
               "duration_s": round(time.time() - t0, 1), "scores": sc,
               "composite": sc["composite"], "floors_pass": sc["floors_pass"]}
        (results / f"{cell}.json").write_text(json.dumps(rec, indent=2))
        p = sc["parts"]
        print(f"{a.results} {cell}: composite={sc['composite']} floors={sc['floors_pass']} "
              f"integ={p['integration_recall']} vital={p['vital_nugget_recall']} "
              f"cite={p['citation']} ({rec['duration_s']}s)", flush=True)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max(1, a.workers)) as ex:
        list(ex.map(run, tasks))


if __name__ == "__main__":
    main()
