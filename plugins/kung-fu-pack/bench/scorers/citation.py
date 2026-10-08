"""Citation scorer (ALCE-inspired, deterministic resolvability approximation).

Full ALCE uses NLI entailment of each statement from its cited passage. To stay offline and
avoid the formatting noise seen earlier, this computes a cheaper, honest proxy:
  - recall:  fraction of fact lines (bullets/table rows) that carry a lead at all.
  - resolvable_precision: fraction of DISTINCT cited leads that resolve to a real id/url/path
    present in the task's frozen corpus/sources (padding or invented citations do not resolve).
A model-based ALCE/NLI upgrade can replace this later; it is labelled as an approximation.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LEAD_RE = re.compile(r"(https?://\S+|`[^`]+`|[\w./-]+\.\w+:\d+|[A-Z]{2,}-\d+|\b[0-9a-f]{8,}\b)")
FACT_LINE = re.compile(r"^\s*([-*]|\|)")


def _brief(pack: Path) -> str:
    for rel in ("out/page.md", "out/index.md", "page.md"):
        p = pack / rel
        if p.exists():
            return p.read_text(errors="ignore")
    outdir = pack / "out"
    if outdir.is_dir():
        md = sorted(outdir.rglob("*.md"))
        if md:
            return "\n\n".join(p.read_text(errors="ignore") for p in md)
    return ""


def _corpus_tokens(pack: Path, task: dict) -> str:
    """Concatenate the frozen source text so we can check a lead resolves."""
    parts = []
    for sub in ("sources", "."):
        d = pack / sub if sub != "." else pack
        for name in ("blurbs.txt", "corpus.json"):
            f = d / name
            if f.exists():
                parts.append(f.read_text(errors="ignore"))
    srcdir = pack / "sources"
    if srcdir.is_dir():
        for f in srcdir.glob("*"):
            if f.is_file():
                parts.append(f.read_text(errors="ignore"))
    # also look at the task fixture corpus if given
    cp = task.get("corpus_path")
    if cp and Path(cp).exists():
        for f in Path(cp).rglob("*"):
            if f.is_file() and f.suffix in (".txt", ".json", ".md"):
                parts.append(f.read_text(errors="ignore"))
    return "\n".join(parts)


def score(task: dict, pack_dir: Path) -> dict:
    pack = Path(pack_dir)
    text = _brief(pack)
    if not text:
        return {"ran": False, "reason": "no brief"}
    fact_lines = [l for l in text.splitlines() if FACT_LINE.match(l) and len(l.strip()) > 8]
    if not fact_lines:
        return {"ran": True, "recall": 0.0, "resolvable_precision": 0.0, "n_fact_lines": 0}
    with_lead = [l for l in fact_lines if LEAD_RE.search(l)]
    recall = round(len(with_lead) / len(fact_lines), 3)

    leads = set()
    for l in with_lead:
        for m in LEAD_RE.findall(l):
            leads.add(m.strip("`"))
    corpus = _corpus_tokens(pack, task).lower()
    if leads and corpus:
        resolvable = sum(1 for ld in leads
                         if ld.lower() in corpus or ld.lower().split("/")[-1] in corpus)
        precision = round(resolvable / len(leads), 3)
    else:
        precision = 0.0 if leads else 1.0
    return {"ran": True, "recall": recall, "resolvable_precision": precision,
            "n_fact_lines": len(fact_lines), "n_leads": len(leads),
            "note": "deterministic resolvability approximation of ALCE"}


if __name__ == "__main__":
    import sys
    print(json.dumps(score({}, Path(sys.argv[1])), indent=2))
