"""Taste scorer for product packs: does the pack SHOW the thing, not just describe it?

Deterministic checks (qa/check_pack.py --product) are a floor: a writer can add a hello-world and a
screenshot and pass them. This scorer asks a judge panel the questions that matter:
  - mechanism:  does the chosen example exercise the load-bearing mechanism of the target?
  - readable:   can a peer read the example in under a minute?
  - real_view:  does the reader see what the product looks like or how it is actually used?
  - technical:  is the main page technical (how it works, how it is used) rather than business-led?
  - honest:     are crafted examples labelled, and does the page avoid inventing behavior?
Each is scored 1 to 5 per pack (absolute), and packs are compared pairwise in both orders (to cancel
position bias); a pairwise win counts only when a judge picks the same pack in both orders.

Judges get text only. Images appear as their alt text and file name, tagged diagram or visual, so
the panel judges placement and captioning, not pixels; eyeball the PNGs yourself.

    python3 -m scorers.taste PACK_DIR [PACK_DIR ...] [--judges claude,codex] [--out taste.json]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import sys
from pathlib import Path

from harnesses import llm

CRITERIA = ("mechanism", "readable", "real_view", "technical", "honest")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
MAX_CHARS = 24000
PAGE_CHARS = 12000  # per page, so one long sub-page cannot crowd the others out of the budget


def _order(p: Path) -> tuple[int, str]:
    # what a reader opens first: the index, then usage, then the rest, business last
    rank = {"index": 0, "page": 0, "usage": 1, "business": 3}.get(p.stem.lower(), 2)
    return rank, str(p)


def render(pack: Path) -> str:
    """The pack as a judge sees it: every out/ page (Markdown preferred), images as tags."""
    out = pack / "out"
    pages = sorted(list(out.rglob("*.md")) or list(out.rglob("*.html")), key=_order)
    diagrams = {h.stem.removesuffix(".min") for h in (pack / "assets").glob("*.html")}

    def tag(m: re.Match) -> str:
        kind = "diagram" if Path(m.group(2)).stem in diagrams else "visual"
        return f"[{kind} image: {m.group(1)} ({Path(m.group(2)).name})]"
    parts = [f"=== {p.relative_to(out)} ===\n"
             + IMG_RE.sub(tag, p.read_text(errors="ignore"))[:PAGE_CHARS] for p in pages]
    return "\n\n".join(parts)[:MAX_CHARS]


def _json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None


ABS = """You are grading a technical briefing pack about a product, written for a cyber/engineering
peer audience. Score each criterion 1 (absent or poor) to 5 (excellent):
- mechanism: the main example exercises the load-bearing mechanism (what makes this product work or
  differ), not setup or category noise.
- readable: the example is small and clear enough to read in under a minute.
- real_view: the reader sees what the product looks like or how it is actually used (real
  screenshots, real output, a usage walkthrough); diagrams alone score at most 2.
- technical: the main page is led by how it works and how it is used, not business context.
- honest: crafted examples are labelled illustrative; nothing presents invented behavior as fact.
Reply with JSON only: {"mechanism":n,"readable":n,"real_view":n,"technical":n,"honest":n,"why":"one line"}

=== PACK ===
"""

PAIR = """Two briefing packs cover the same product for a cyber/engineering peer audience. For each
criterion, say which pack is better: "A", "B", or "tie".
- mechanism: the example exercises the load-bearing mechanism, not setup or category noise.
- readable: the example is readable in under a minute.
- real_view: the reader sees what the product looks like or how it is used (screenshots, output,
  walkthrough); diagrams alone do not count.
- technical: led by how it works and how it is used, not business context.
- honest: crafted examples labelled; no invented behavior.
- overall: which pack better teaches a peer what the product is, does, and looks like in use.
Reply with JSON only: {"mechanism":"A|B|tie",...,"overall":"A|B|tie","why":"one line"}

=== PACK A ===
{a}

=== PACK B ===
{b}
"""


def _pair(a: str, b: str) -> str:
    # one pass, so a "{b}" inside pack A's text is never substituted
    return re.sub(r"\{([ab])\}", lambda m: a if m.group(1) == "a" else b, PAIR)


def absolute(pack: Path, judges: list[str]) -> dict:
    res = {}
    for j in judges:
        r = _json(llm.call(j, ABS + render(pack)))
        res[j] = r if r and all(isinstance(r.get(c), (int, float)) for c in CRITERIA) else None
    ok = [r for r in res.values() if r]
    mean = {c: round(sum(r[c] for r in ok) / len(ok), 2) for c in CRITERIA} if ok else None
    return {"judges": res, "mean": mean,
            "failed_judges": [j for j, r in res.items() if r is None]}


def pairwise(a: Path, b: Path, judges: list[str]) -> dict:
    ta, tb = render(a), render(b)
    keys = (*CRITERIA, "overall")
    res = {}
    for j in judges:
        fwd = _json(llm.call(j, _pair(ta, tb)))
        rev = _json(llm.call(j, _pair(tb, ta)))
        if not fwd or not rev:
            res[j] = None
            continue
        # a criterion is won only when the judge picks the same pack in both orders
        # (reversed, pack A is shown as "B")
        winner = {("A", "B"): str(a), ("B", "A"): str(b)}
        res[j] = {k: winner.get((fwd.get(k), rev.get(k)), "tie/inconsistent") for k in keys}
        res[j]["why"] = fwd.get("why", "")
    return {"a": str(a), "b": str(b), "judges": res,
            "failed_judges": [j for j, r in res.items() if r is None]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("packs", nargs="+")
    ap.add_argument("--judges", default=os.environ.get("KFP_JUDGES", "claude,codex"))
    ap.add_argument("--out")
    a = ap.parse_args()
    judges = a.judges.split(",")
    packs = [Path(p).expanduser().resolve() for p in a.packs]
    report = {"absolute": {str(p): absolute(p, judges) for p in packs},
              "pairwise": [pairwise(x, y, judges) for x, y in itertools.combinations(packs, 2)]}
    text = json.dumps(report, indent=2)
    if a.out:
        Path(a.out).write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
