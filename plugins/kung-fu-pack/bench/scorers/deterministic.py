"""Deterministic scorers for a kung-fu-pack brief + its workspace.

These need NO model calls, so they are fast, cheap, and reproducible. They form the
guardrail metrics and the hard floors:
  - em_dashes:        count of em/en dashes in the brief (hard floor: must be 0)
  - length_pages:     estimated A4 pages (hard floor: within [1, 3])
  - lead_coverage:    fraction of claims that carry a resolvable lead
  - source_coverage:  precision/recall/F1 of sources reached vs the task gold set
                      (the anti-overfit routing metric: did it use the right sources,
                      regardless of which concrete tool/provider supplied them)

A "pack" is the kung-fu-pack workspace dir: out/page.md (the brief), research/*
(audit trail), and pack.json (machine-readable manifest; see harnesses/manifest.py).
Scorers degrade gracefully: a missing manifest falls back to parsing the brief.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from scorers import brief as brief_mod

WORDS_PER_PAGE = 500  # ~1 dense A4 page of briefing prose
EM_EN = (chr(0x2014), chr(0x2013))  # em dash, en dash; from ordinals so this file is dash-free


def _read_brief(pack: Path) -> str:
    return brief_mod.read(pack)



def _load_manifest(pack: Path) -> dict:
    p = pack / "pack.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def count_em_dashes(text: str) -> int:
    return sum(text.count(c) for c in EM_EN)


def estimate_pages(text: str) -> float:
    words = len(re.findall(r"\S+", text))
    return round(words / WORDS_PER_PAGE, 2)


def lead_coverage(manifest: dict, text: str) -> float:
    """Fraction of claims that carry a lead.

    Prefer the manifest's claims[{claim, lead}]; else heuristically treat bullet
    and table lines as claims and check each for a lead token (path:line, URL, or a
    backticked id).
    """
    claims = manifest.get("claims")
    if isinstance(claims, list) and claims:
        with_lead = sum(1 for c in claims if str(c.get("lead", "")).strip())
        return round(with_lead / len(claims), 3)
    lead_re = re.compile(r"(https?://|`[^`]+`|[\w./-]+\.\w+:\d+|[0-9a-f]{8,})")
    lines = [l.strip() for l in text.splitlines()
             if l.strip().startswith(("-", "*", "|")) and len(l.strip()) > 8]
    if not lines:
        return 0.0
    with_lead = sum(1 for l in lines if lead_re.search(l))
    return round(with_lead / len(lines), 3)


def source_coverage(manifest: dict, gold_sources: list[str]) -> dict:
    """Precision/recall/F1 of sources reached vs the gold set.

    Matching is capability/identity based and tool-agnostic: a gold source is
    "covered" if any reached source shares its normalized identity token, so a brief
    that pulled the right fact from Jira instead of Linear still scores. This is the
    anti-overfit routing signal.
    """
    reached = manifest.get("sources_reached") or []
    gold = gold_sources or []
    if not gold:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "n_gold": 0, "n_reached": len(reached)}

    def norm(s: str) -> str:
        s = str(s).lower()
        s = re.sub(r"^[a-z]+://", "", s)        # drop scheme/provider prefix
        s = re.sub(r"[^a-z0-9]+", " ", s).strip()
        return s

    gold_n = [norm(g) for g in gold]
    reached_n = [norm(r) for r in reached]

    def covered(g: str) -> bool:
        toks = [t for t in g.split() if len(t) > 3]
        return any(any(t in r for t in toks) for r in reached_n) if toks else False

    hit = sum(1 for g in gold_n if covered(g))
    prec_hit = 0
    for r in reached_n:
        rtoks = [t for t in r.split() if len(t) > 3]
        if any(any(t in g for t in rtoks) for g in gold_n):
            prec_hit += 1
    recall = hit / len(gold_n) if gold_n else 0.0
    precision = prec_hit / len(reached_n) if reached_n else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "n_gold": len(gold_n),
        "n_reached": len(reached_n),
    }


def score(task: dict, pack_dir: Path) -> dict:
    """Return the deterministic metric block for one brief."""
    pack = Path(pack_dir)
    text = _read_brief(pack)
    manifest = _load_manifest(pack)
    em = count_em_dashes(text)
    pages = estimate_pages(text)
    leads = lead_coverage(manifest, text)
    cov = source_coverage(manifest, task.get("gold_sources", []))

    lo, hi = 1, 3
    length_ok = lo <= pages <= hi
    out = {
        "em_dashes": em,
        "em_dash_ok": em == 0,
        "length_pages": pages,
        "length_ok": length_ok,
        "lead_coverage": leads,
        "source_coverage": cov,
        "has_brief": bool(text),
        "has_manifest": bool(manifest),
        # hard floors folded into one gate for convenience
        "floors_pass": bool(text) and em == 0 and length_ok,
    }
    return out


if __name__ == "__main__":
    import sys
    t = {"gold_sources": ["repo:acme/auth#README", "url:https://example.com/docs"]}
    print(json.dumps(score(t, Path(sys.argv[1] if len(sys.argv) > 1 else ".")), indent=2))
