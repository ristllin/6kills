"""Semi-automated gold authoring: a model proposes nuggets + integration-facts from a frozen
corpus; the orchestrator vets the output before it is used. Writes gold.json into the fixture.

    python gold/author.py --corpus tasks/fixtures/f1_arxiv_cslg --kind landscape --judge codex

Map-reduce so the gold covers the WHOLE corpus: each slice is summarized (map), then one call
builds corpus-level nuggets and integration-facts from all slice notes (reduce). An earlier
single-shot version only saw the first slice, so its gold named details from ~20 of 220 papers.

Vetting is a human/gatekeeper step after this runs: check counts, drop duplicates, and confirm
each integration_fact genuinely needs >=2 sources.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harnesses import llm  # noqa: E402

SCHEMA = (
    'Return ONLY JSON: {"task":"...","nuggets":[{"id":"N1","text":"...","vital":true,'
    '"sources":[1,2]}],"integration_facts":[{"id":"I1","text":"...","min_sources":2,'
    '"sources":[1,5]}],"answer_key":[{"q":"...","a":"..."}]}.'
)


def _extract_json(text: str):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


MAP = {
    "landscape": (
        "You are reading ONE slice of a larger corpus of recent arXiv abstracts. List the themes, "
        "methods, problems, and recurring findings in this slice. For each, give the supporting "
        "paper index numbers (the [n] tags) and one concrete, checkable detail. Note any pairs of "
        "papers that converge on, or disagree about, the same question. Be exhaustive and terse.\n"
    ),
    "releases": (
        "You are reading ONE slice of a larger set of software release notes. List the user-facing "
        "changes that matter for an upgrade: features, breaking changes, deprecations, removals, "
        "defaults that changed, and migrations. For each give the release tag and one concrete "
        "detail (PR number if shown). Be exhaustive and terse.\n"
    ),
}

REDUCE = {
    "landscape": (
        "You are building a GOLD answer key to grade 1-3 page landscapes of the WHOLE corpus "
        "summarized below (notes from every slice; paper indices are global). Salience is "
        "corpus-level: prefer themes many papers share and the few findings a landscape reader "
        "must not miss; do not pick single-paper trivia.\n"
        "1) nuggets: 18-24 atomic facts. vital=true for must-have corpus-level points (a recurring "
        "theme, a dominant method, a major result), vital=false for nice-to-have. Each lists its "
        "supporting paper indices.\n"
        "2) integration_facts: 6-8 cross-paper patterns that need >=2 papers, ideally from "
        "different slices (convergence on a technique, a disagreement, a shared bottleneck). Phrase "
        "each so a reader can check it from a good landscape without needing every paper named.\n"
        "3) answer_key: 6 questions with concise answers.\n"
    ),
    "releases": (
        "You are building a GOLD answer key to grade 1-3 page what-changed / migration briefs of "
        "ALL the releases summarized below (notes from every slice). Salience is upgrade impact.\n"
        "1) nuggets: 16-22 atomic facts; vital=true for breaking changes, removals, changed "
        "defaults, and headline features; each lists its supporting release index numbers.\n"
        "2) integration_facts: 6-8 CROSS-VERSION or CROSS-PROJECT patterns needing >=2 releases "
        "(introduced then changed or removed; a deprecation and its later removal; the same "
        "direction in both projects).\n"
        "3) answer_key: 6 questions with concise answers.\n"
    ),
}


def _chunks(text: str, size: int) -> list[str]:
    """Split on entry boundaries ([n] at line start) into slices of about `size` chars."""
    entries = re.split(r"(?m)^(?=\[\d+\] )", text)
    out, cur = [], ""
    for e in entries:
        if cur and len(cur) + len(e) > size:
            out.append(cur)
            cur = ""
        cur += e
    if cur.strip():
        out.append(cur)
    return out


def _vet(data: dict) -> dict:
    """Drop integration facts that do not really cite >=2 distinct sources."""
    kept = [f for f in data.get("integration_facts", []) if len(set(f.get("sources", []))) >= 2]
    data["vetting"] = {"integration_dropped": len(data.get("integration_facts", [])) - len(kept)}
    data["integration_facts"] = kept
    return data


def author(corpus_dir: Path, kind: str, judge: str, chunk_chars: int, workers: int = 6) -> dict:
    from concurrent.futures import ThreadPoolExecutor

    blurbs = (corpus_dir / "blurbs.txt").read_text(errors="ignore")
    slices = _chunks(blurbs, chunk_chars)
    with ThreadPoolExecutor(workers) as ex:
        notes = list(ex.map(lambda c: llm.call(judge, MAP[kind] + "\n=== SLICE ===\n" + c), slices))
    bad = [i for i, n in enumerate(notes) if n.startswith("[timeout]") or n.startswith("[error]")]
    if bad:
        raise SystemExit(f"map step failed on slices {bad}; rerun")
    merged = "\n\n".join(f"=== NOTES FROM SLICE {i + 1}/{len(notes)} ===\n{n}"
                          for i, n in enumerate(notes))
    (corpus_dir / "gold.map.txt").write_text(merged)
    out = llm.call(judge, REDUCE[kind] + SCHEMA + "\n\n" + merged)
    data = _extract_json(out)
    if not data:
        (corpus_dir / "gold.raw.txt").write_text(out)
        raise SystemExit("no JSON from judge; raw saved to gold.raw.txt for manual authoring")
    data = _vet(data)
    data["provenance"] = {"method": "map-reduce over the full corpus", "slices": len(slices),
                          "corpus_chars": len(blurbs), "judge": judge}
    data.setdefault("split", "dev")
    (corpus_dir / "gold.json").write_text(json.dumps(data, indent=2))
    return {"slices": len(slices), "nuggets": len(data.get("nuggets", [])),
            "vital": sum(1 for n in data.get("nuggets", []) if n.get("vital")),
            "integration_facts": len(data.get("integration_facts", [])),
            "answers": len(data.get("answer_key", [])), **data["vetting"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--kind", required=True, choices=list(MAP))
    ap.add_argument("--judge", default="codex")
    ap.add_argument("--chunk-chars", type=int, default=45000)
    a = ap.parse_args()
    print(json.dumps(author(Path(a.corpus), a.kind, a.judge, a.chunk_chars), indent=2))
