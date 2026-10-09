"""Produce + score synthesis briefs for a skill version (the v2 hard benchmark).

For each task: feed the FROZEN corpus to a writer harness running the kung-fu-pack method, have
it write out/page.md + pack.json, then score with the full stack (compose.score_all). Results are
archived per version (results_vN/<cell>.json) for the hill-climb curve.

    PYTHONPATH=. python3 drive_synth.py --skill ../skills/kung-fu-pack/SKILL.md \
        --results v0 --writer claude --ids f3-multitool
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import config
from harnesses import llm, manifest as manifest_mod
from scorers import compose

BENCH = Path(__file__).resolve().parent
MAX_CORPUS_CHARS = int(__import__("os").environ.get("KFP_MAX_CORPUS", "160000"))

CONTRACT = """
OUTPUT CONTRACT (write files in your current directory):
1. out/page.md  the brief: 1 to 3 A4 pages. Framing line first, then tight sections and tables.
   EVERY fact line ends with a lead in parentheses (a source id/url/tag from the corpus). NO em or
   en dashes anywhere (use hyphens). End with a Sources section.
2. pack.json  {"output_path":"out/page.md","sources_reached":[...ids/urls you used...],
   "claims":[{"claim":"...","lead":"..."}]}.
Synthesize ONLY from the provided corpus. Compress: find the most important and distinct facts, merge
duplicates, and surface cross-source patterns (facts that need combining multiple sources). Do not pad.
Reply with just: BRIEF_DONE.
"""


def _load_corpus(task: dict) -> str:
    base = BENCH / task["corpus_path"] if not Path(task["corpus_path"]).is_absolute() \
        else Path(task["corpus_path"])
    if task.get("corpus_dir"):
        parts = [p.read_text(errors="ignore") for p in sorted((base / task["corpus_dir"]).glob("*"))
                 if p.is_file()]
        return "\n\n".join(parts)
    return (base / task.get("corpus_file", "blurbs.txt")).read_text(errors="ignore")


def build_prompt(task: dict, skill_text: str, corpus: str) -> str:
    skill = skill_text.strip()[:9000]
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
    ap.add_argument("--model", default="opus")
    ap.add_argument("--results", default="v0")
    a = ap.parse_args()

    skill_text = Path(a.skill).read_text()
    tasks = [json.loads(l) for l in Path(a.tasks).read_text().splitlines() if l.strip()]
    if a.ids:
        want = set(a.ids.split(","))
        tasks = [t for t in tasks if t["instance_id"] in want]
    results = BENCH / f"results_{a.results}"
    results.mkdir(parents=True, exist_ok=True)
    packs_root = config.WORKSPACE / "packs"

    for t in tasks:
        tid = t["instance_id"]
        cell = f"{a.writer}__{a.model}__{tid}"
        pack = packs_root / f"{a.results}__{cell}"
        (pack / "out").mkdir(parents=True, exist_ok=True)
        # make gold + sources available inside the pack for scoring
        fx = BENCH / t["corpus_path"]
        if (fx / "gold.json").exists():
            shutil.copy(fx / "gold.json", pack / "gold.json")
        if (fx / "sources").is_dir() and not (pack / "sources").exists():
            shutil.copytree(fx / "sources", pack / "sources")
        corpus = _load_corpus(t)
        prompt = build_prompt(t, skill_text, corpus)
        t0 = time.time()
        log = llm.call(a.writer, prompt, cwd=str(pack))
        (pack / "agent.log").write_text(log)
        manifest_mod.build(pack)
        t_task = dict(t)
        t_task["corpus_path"] = str(fx)
        sc = compose.score_all(t_task, pack, with_models=True)
        rec = {"cell": cell, "instance_id": tid, "version": a.results,
               "duration_s": round(time.time() - t0, 1), "scores": sc,
               "composite": sc["composite"], "floors_pass": sc["floors_pass"]}
        (results / f"{cell}.json").write_text(json.dumps(rec, indent=2))
        p = sc["parts"]
        print(f"{cell}: composite={sc['composite']} floors={sc['floors_pass']} "
              f"integ={p['integration_recall']} vital={p['vital_nugget_recall']} "
              f"cite={p['citation_recall']} ({rec['duration_s']}s)", flush=True)


if __name__ == "__main__":
    main()
