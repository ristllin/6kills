"""Core discriminating scorers: eligibility gate + nugget recall + integration recall.

Presence is decided by a JUDGE (astra by default), not heuristic string matching, because
the earlier eval showed heuristic extraction is too formatting-sensitive to optimize against.
The judge reads the brief and the gold list and returns which items are supported (the
AutoNuggetizer AutoAssign step). A deterministic keyword fallback is used only if the judge
call fails, so scoring never raises.

Metrics per task:
  - eligible: the brief is substantive and on-task (FACTS-style gate); if false, recalls are 0.
  - vital_nugget_recall, all_nugget_recall: fraction of gold nuggets supported.
  - integration_recall: fraction of integration-facts (each needs >=2 sources) supported. This
    is the hard, unsaturated core.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from harnesses import llm

JUDGE = "astra"
MIN_WORDS = 150  # below this a "brief" is evasive/empty


def _brief(pack: Path) -> str:
    for rel in ("out/page.md", "out/index.md", "out/page.html", "page.md"):
        p = pack / rel
        if p.exists():
            return p.read_text(errors="ignore")
    # nested output: concatenate all markdown under out/
    outdir = pack / "out"
    if outdir.is_dir():
        md = sorted(outdir.rglob("*.md"))
        if md:
            return "\n\n".join(p.read_text(errors="ignore") for p in md)
    return ""


def _extract_json(text: str):
    m = re.search(r"[\[{].*[\]}]", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _keyword_present(text: str, item_text: str) -> bool:
    toks = [t for t in re.findall(r"[a-zA-Z0-9]+", item_text.lower()) if len(t) > 3]
    if not toks:
        return False
    low = text.lower()
    hit = sum(1 for t in set(toks) if t in low)
    return hit / len(set(toks)) >= 0.55  # most key terms appear


def eligibility(brief: str, task: str) -> dict:
    words = len(re.findall(r"\S+", brief))
    if words < MIN_WORDS:
        return {"eligible": False, "reason": f"too short ({words} words)"}
    prompt = (
        "Is the following a substantive briefing that genuinely attempts the task, or is it "
        "evasive/empty/off-topic? Reply ONLY JSON {\"eligible\":true|false,\"reason\":\"...\"}.\n"
        f"TASK: {task}\n=== BRIEF (start) ===\n{brief[:4000]}\n=== (end) ==="
    )
    data = _extract_json(llm.call(JUDGE, prompt)) or {}
    if "eligible" in data:
        return {"eligible": bool(data["eligible"]), "reason": data.get("reason", "")}
    return {"eligible": words >= MIN_WORDS, "reason": "judge-unavailable; word-count fallback"}


def _assign(brief: str, items: list, kind: str) -> set:
    """Return the set of item ids the brief supports, judged by the model."""
    listing = "\n".join(f'{it["id"]}: {it["text"]}' for it in items)
    prompt = (
        f"For each {kind} below, decide if the BRIEF clearly states or supports it. Be strict: "
        "mark supported only if the brief actually conveys the fact (not just mentions the topic). "
        'Reply ONLY JSON: {"supported":["id1","id2",...]}.\n'
        f"=== {kind.upper()} ===\n{listing}\n=== BRIEF ===\n{brief[:14000]}\n"
    )
    data = _extract_json(llm.call(JUDGE, prompt))
    if isinstance(data, dict) and isinstance(data.get("supported"), list):
        return set(str(x) for x in data["supported"])
    # fallback: deterministic keyword presence
    return {it["id"] for it in items if _keyword_present(brief, it["text"])}


def score(task: dict, pack_dir: Path) -> dict:
    pack = Path(pack_dir)
    gold_path = pack / "gold.json"
    gold = json.loads(gold_path.read_text()) if gold_path.exists() else task.get("gold", {})
    brief = _brief(pack)
    task_desc = gold.get("task", task.get("scope", ""))
    if not brief:
        return {"ran": False, "reason": "no brief"}

    elig = eligibility(brief, task_desc)
    nuggets = gold.get("nuggets", [])
    integ = gold.get("integration_facts", [])
    if not elig["eligible"]:
        return {"ran": True, "eligible": False, "reason": elig["reason"],
                "vital_nugget_recall": 0.0, "all_nugget_recall": 0.0, "integration_recall": 0.0}

    supported_n = _assign(brief, nuggets, "nugget") if nuggets else set()
    supported_i = _assign(brief, integ, "integration fact") if integ else set()
    vital = [n for n in nuggets if n.get("vital")]
    vital_hit = sum(1 for n in vital if n["id"] in supported_n)
    all_hit = sum(1 for n in nuggets if n["id"] in supported_n)
    int_hit = sum(1 for f in integ if f["id"] in supported_i)
    return {
        "ran": True, "eligible": True,
        "vital_nugget_recall": round(vital_hit / len(vital), 3) if vital else 0.0,
        "all_nugget_recall": round(all_hit / len(nuggets), 3) if nuggets else 0.0,
        "integration_recall": round(int_hit / len(integ), 3) if integ else 0.0,
        "n_vital": len(vital), "n_integration": len(integ),
        "supported_nuggets": sorted(supported_n), "supported_integration": sorted(supported_i),
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(score({}, Path(sys.argv[1])), indent=2))
