"""Quality-rubric scorer: coverage, grounding, insight, navigability (1-5 each).

Judged by astra (independent of the Claude writer). Returns a normalized 0..1 mean plus
the per-axis scores. Never raises. For full de-bias a second judge (opus/ml4) can be run
and averaged; this ships the single-judge version and labels it as such.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from harnesses import llm

JUDGE = "astra"
AXES = ["coverage", "grounding", "insight", "navigability"]


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


def score(task: dict, pack_dir: Path, judge: str = JUDGE) -> dict:
    brief = _brief(Path(pack_dir))
    if not brief:
        return {"ran": False, "reason": "no brief"}
    prompt = (
        "Score this briefing on four axes, 1 (poor) to 5 (excellent). Be strict.\n"
        "- coverage: does it cover what the scope asks?\n"
        "- grounding: does every claim carry a resolvable lead (url/path:line/id)?\n"
        "- insight: non-obvious synthesis vs a flat table of contents.\n"
        "- navigability: can a reader deep-dive via its structure and links?\n"
        f"SCOPE: {task.get('scope','')}\n"
        'Return ONLY JSON: {"coverage":n,"grounding":n,"insight":n,"navigability":n}.\n\n'
        f"=== BRIEF ===\n{brief[:12000]}\n"
    )
    out = llm.call(judge, prompt)
    data = _extract_json(out)
    if not data:
        return {"ran": False, "reason": "no json from judge", "raw": out[:300]}
    vals = []
    for a in AXES:
        try:
            vals.append(max(1, min(5, int(round(float(data.get(a, 0)))))))
        except Exception:
            vals.append(0)
    mean5 = sum(vals) / len(vals) if vals else 0.0
    return {
        "ran": True, "judge": judge,
        **{a: v for a, v in zip(AXES, vals)},
        "quality": round(mean5 / 5.0, 3),
    }
