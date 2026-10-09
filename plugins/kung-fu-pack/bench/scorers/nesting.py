"""Nesting-appropriateness scorer (offline, structural).

The right structure depends on how much the corpus demands:
  - If honest coverage fits in <= max_flat_pages, a single tight page is correct; nesting is
    over-engineering.
  - If it genuinely exceeds that, the brief should NEST: an index/overview page plus linked
    sub-pages, not a monolith that overflows or truncates.

This scorer reads the pack's out/ tree and the task's expected size class and returns a 0..1
appropriateness score plus the detected structure. No model call.
"""
from __future__ import annotations

import re
from pathlib import Path

MAX_FLAT_PAGES = 3
WORDS_PER_PAGE = 500


def _structure(pack: Path):
    out = pack / "out"
    pages = []
    if out.is_dir():
        pages = sorted([p for p in out.rglob("*.md")] + [p for p in out.rglob("*.html")])
    if not pages and (pack / "page.md").exists():
        pages = [pack / "page.md"]
    total_words = 0
    for p in pages:
        total_words += len(re.findall(r"\S+", p.read_text(errors="ignore")))
    index = None
    for p in pages:
        if p.stem.lower() in ("index", "readme", "page") or p.name.lower() == "index.md":
            index = p
            break
    # a nested structure = an index plus >=2 other pages, with the index linking to them
    sub = [p for p in pages if p != index]
    index_links = 0
    if index is not None:
        itext = index.read_text(errors="ignore")
        index_links = len(re.findall(r"\]\(([^)]+\.(?:md|html))\)", itext))
    nested = index is not None and len(sub) >= 2 and index_links >= 2
    return {"n_pages": len(pages), "total_words": total_words, "nested": nested,
            "index": index.name if index else None, "sub_pages": len(sub),
            "index_links": index_links}


def score(task: dict, pack_dir: Path) -> dict:
    pack = Path(pack_dir)
    st = _structure(pack)
    # expected size class: the task may declare it; else infer from corpus size if present
    expected_large = bool(task.get("expect_nested"))
    pages = round(st["total_words"] / WORDS_PER_PAGE, 2)

    if expected_large:
        # should nest; a single overflowing page is wrong
        if st["nested"]:
            appropriateness = 1.0
            note = "nested as required"
        elif pages > MAX_FLAT_PAGES:
            appropriateness = 0.2
            note = "overflowed into a monolith instead of nesting"
        else:
            appropriateness = 0.4
            note = "stayed flat and likely truncated coverage"
    else:
        # should be a tight single page; nesting is over-engineering, overflow is bad
        if not st["nested"] and pages <= MAX_FLAT_PAGES:
            appropriateness = 1.0
            note = "appropriately flat and within budget"
        elif st["nested"]:
            appropriateness = 0.6
            note = "nested when a single page would do"
        else:
            appropriateness = 0.3
            note = "single page but over the length budget"
    return {"appropriateness": appropriateness, "note": note, "pages": pages, **st}


if __name__ == "__main__":
    import json, sys
    print(json.dumps(score({"expect_nested": "--nest" in sys.argv}, Path(sys.argv[1])), indent=2))
