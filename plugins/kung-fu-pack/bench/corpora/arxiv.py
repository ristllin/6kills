"""Freeze a corpus of recent arXiv abstracts (stdlib only, no deps, no key).

Pulls the newest submissions for a category via the arXiv Atom API, keeps only those
submitted on/after a cutoff date (so the content is post-training-cutoff and cannot be
answered from parametric memory), and writes an immutable JSON corpus + a plain-text
blurbs file into a fixture dir. Each entry is one "blurb" (title + abstract + date + id).

    python arxiv.py --category cs.LG --after 2026-09-01 --n 250 --out <fixture_dir>
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
API = "http://export.arxiv.org/api/query"


def _fetch_page(category: str, start: int, page: int) -> list[dict]:
    url = (f"{API}?search_query=cat:{category}&start={start}&max_results={page}"
           f"&sortBy=submittedDate&sortOrder=descending")
    req = urllib.request.Request(url, headers={"User-Agent": "kfp-bench/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        xml = r.read().decode("utf-8", "ignore")
    root = ET.fromstring(xml)
    out = []
    for e in root.findall(f"{ATOM}entry"):
        out.append({
            "id": (e.findtext(f"{ATOM}id") or "").strip(),
            "title": " ".join((e.findtext(f"{ATOM}title") or "").split()),
            "abstract": " ".join((e.findtext(f"{ATOM}summary") or "").split()),
            "published": (e.findtext(f"{ATOM}published") or "").strip(),
            "authors": [a.findtext(f"{ATOM}name") for a in e.findall(f"{ATOM}author")],
        })
    return out


def freeze(category: str, after: str, n: int, out: Path) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    page = 100
    kept: list[dict] = []
    start = 0
    while len(kept) < n and start < n * 4:
        batch = _fetch_page(category, start, page)
        if not batch:
            break
        for e in batch:
            if e["published"][:10] >= after:
                kept.append(e)
        start += page
        time.sleep(3)  # arXiv API etiquette
    kept = kept[:n]
    (out / "corpus.json").write_text(json.dumps(kept, indent=2))
    blurbs = "\n\n".join(
        f"[{i+1}] {e['title']} ({e['published'][:10]})\n{e['id']}\n{e['abstract']}"
        for i, e in enumerate(kept))
    (out / "blurbs.txt").write_text(blurbs)
    meta = {"source": "arxiv", "category": category, "after": after,
            "n": len(kept), "oldest": min((e["published"][:10] for e in kept), default=None),
            "newest": max((e["published"][:10] for e in kept), default=None)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True)
    ap.add_argument("--after", required=True, help="YYYY-MM-DD; keep submissions on/after")
    ap.add_argument("--n", type=int, default=250)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = freeze(a.category, a.after, a.n, Path(a.out))
    print(json.dumps(m, indent=2))
