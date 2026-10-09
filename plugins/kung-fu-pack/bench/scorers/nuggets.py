"""Core discriminating scorers: eligibility gate + nugget recall + integration recall.

Presence is decided by a JUDGE (a Codex model by default), not heuristic string matching, because
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
import os
import re
from pathlib import Path

from scorers import brief as brief_mod

from harnesses import llm

JUDGE = "codex"
# Cross-judge panel (debias): recall is the mean over judges; agreement is reported.
JUDGES = [j for j in os.environ.get("KFP_JUDGES", "codex,claude").split(",") if j]
MIN_WORDS = 150  # below this a "brief" is evasive/empty
JUDGE_CHARS = 90000  # judge sees the whole brief incl. sub-pages (was 14k, which truncated nests)


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
        f"TASK: {task}\n=== BRIEF (start) ===\n{brief[:8000]}\n=== (end) ==="
    )
    data = _extract_json(llm.call(JUDGE, prompt)) or {}
    if "eligible" in data:
        return {"eligible": bool(data["eligible"]), "reason": data.get("reason", "")}
    return {"eligible": words >= MIN_WORDS, "judge_failed": True,
            "reason": "judge-unavailable; word-count fallback"}


def _assign(brief: str, items: list, kind: str, judge: str = JUDGE) -> set | None:
    """Return the set of item ids the brief supports, or None if the judge gave no usable verdict
    (a failed judge must not be scored under its own name)."""
    listing = "\n".join(f'{it["id"]}: {it["text"]}' for it in items)
    prompt = (
        f"For each {kind} below, decide if the BRIEF clearly states or supports it. Be strict: "
        "mark supported only if the brief actually conveys the fact (not just mentions the topic). "
        'Reply ONLY JSON: {"supported":["id1","id2",...]}.\n'
        f"=== {kind.upper()} ===\n{listing}\n=== BRIEF ===\n{brief[:JUDGE_CHARS]}\n"
    )
    data = _extract_json(llm.call(judge, prompt))
    if isinstance(data, dict) and isinstance(data.get("supported"), list):
        return set(str(x) for x in data["supported"])
    return None


def _keyword_assign(brief: str, items: list) -> set:
    """Last-resort deterministic match, used only when every judge failed (and labelled as such)."""
    return {it["id"] for it in items if _keyword_present(brief, it["text"])}


def score(task: dict, pack_dir: Path) -> dict:
    pack = Path(pack_dir)
    gold_path = pack / "gold.json"
    gold = json.loads(gold_path.read_text()) if gold_path.exists() else task.get("gold", {})
    brief = brief_mod.read(pack)
    task_desc = gold.get("task", task.get("scope", ""))
    if not brief:
        return {"ran": False, "reason": "no brief"}

    elig = eligibility(brief, task_desc)
    nuggets = gold.get("nuggets", [])
    integ = gold.get("integration_facts", [])
    if not elig["eligible"]:
        return {"ran": True, "eligible": False, "reason": elig["reason"],
                "vital_nugget_recall": 0.0, "all_nugget_recall": 0.0, "integration_recall": 0.0}

    vital = [n for n in nuggets if n.get("vital")]
    per_judge, failed = {}, []
    for j in JUDGES:
        sn = _assign(brief, nuggets, "nugget", j) if nuggets else set()
        si = _assign(brief, integ, "integration fact", j) if integ else set()
        if sn is None or si is None:
            failed.append(j)
            continue
        per_judge[j] = {
            "vital_nugget_recall": _frac(vital, sn), "all_nugget_recall": _frac(nuggets, sn),
            "integration_recall": _frac(integ, si),
            "supported_nuggets": sorted(sn), "supported_integration": sorted(si),
        }
    method = "judges"
    if not per_judge:  # every judge failed: score by keyword, never under a judge's name
        method = "keyword-fallback"
        sn, si = _keyword_assign(brief, nuggets), _keyword_assign(brief, integ)
        per_judge["keyword"] = {
            "vital_nugget_recall": _frac(vital, sn), "all_nugget_recall": _frac(nuggets, sn),
            "integration_recall": _frac(integ, si),
            "supported_nuggets": sorted(sn), "supported_integration": sorted(si),
        }
    keys = ("vital_nugget_recall", "all_nugget_recall", "integration_recall")
    mean = {k: round(sum(v[k] for v in per_judge.values()) / len(per_judge), 3) for k in keys}
    return {"ran": True, "eligible": True, **mean,
            "n_vital": len(vital), "n_integration": len(integ),
            "method": method, "failed_judges": failed, "judges": per_judge,
            "agreement": _agreement(per_judge, nuggets + integ)}


def _frac(items: list, supported: set) -> float:
    return round(sum(1 for it in items if it["id"] in supported) / len(items), 3) if items else 0.0


def _agreement(per_judge: dict, items: list) -> dict:
    """Pairwise percent agreement and Cohen's kappa over all gold items (supported or not)."""
    js = list(per_judge)
    if len(js) < 2 or not items:
        return {}
    out = {}
    for a in range(len(js)):
        for b in range(a + 1, len(js)):
            sa = set(per_judge[js[a]]["supported_nuggets"] + per_judge[js[a]]["supported_integration"])
            sb = set(per_judge[js[b]]["supported_nuggets"] + per_judge[js[b]]["supported_integration"])
            xa = [it["id"] in sa for it in items]
            xb = [it["id"] in sb for it in items]
            n = len(items)
            po = sum(1 for x, y in zip(xa, xb) if x == y) / n
            pa, pb = sum(xa) / n, sum(xb) / n
            pe = pa * pb + (1 - pa) * (1 - pb)
            kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
            out[f"{js[a]}~{js[b]}"] = {"agree": round(po, 3), "kappa": round(kappa, 3)}
    return out


if __name__ == "__main__":
    import sys
    print(json.dumps(score({}, Path(sys.argv[1])), indent=2))
