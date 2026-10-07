"""Comprehension-transfer scorer (primary metric).

A cold reader model (astra by default, never the writer) is given ONLY the brief and the
task's gold_questions, answers them, and self-reports whether the brief actually supported
each answer. Score = fraction supported-and-answered. Efficiency = score per 1000 words.
Never raises: a model/parse failure returns ran=False with a reason.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from harnesses import llm

READER = "astra"


def _brief(pack: Path) -> str:
    for rel in ("out/page.md", "out/page.html", "page.md"):
        p = pack / rel
        if p.exists():
            return p.read_text(errors="ignore")
    return ""


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def score(task: dict, pack_dir: Path, reader: str = READER) -> dict:
    brief = _brief(Path(pack_dir))
    qs = task.get("gold_questions", [])
    if not brief or not qs:
        return {"ran": False, "reason": "no brief or no gold_questions"}
    words = len(re.findall(r"\S+", brief))
    q_block = "\n".join(f"{i+1}. {q}" for i, q in enumerate(qs))
    prompt = (
        "You are a cold reader. Use ONLY the briefing below. Do not use outside knowledge.\n"
        "For each question, answer from the brief, then mark supported=true only if the brief "
        "actually contained the information. Return ONLY JSON: "
        '{"answers":[{"n":1,"supported":true}...],"supported_count":N}.\n\n'
        f"=== BRIEF ===\n{brief[:12000]}\n=== QUESTIONS ===\n{q_block}\n"
    )
    out = llm.call(reader, prompt)
    data = _extract_json(out)
    if not data:
        return {"ran": False, "reason": "no json from reader", "raw": out[:300]}
    supported = int(data.get("supported_count") or
                    sum(1 for a in data.get("answers", []) if a.get("supported")))
    comp = round(supported / len(qs), 3)
    return {
        "ran": True, "reader": reader, "n_questions": len(qs),
        "supported": supported, "comprehension": comp,
        "words": words,
        "efficiency": round(comp / (words / 1000.0), 3) if words else 0.0,
    }


if __name__ == "__main__":
    import sys
    t = {"gold_questions": ["What is it?", "How does it work?"]}
    print(json.dumps(score(t, Path(sys.argv[1])), indent=2))
