"""Deterministic acceptance checks for a kung-fu-pack produced during release QA.

Checks the newest pack under <root>/packs: the workspace was used (research files + plan), the
output exists, zero em/en dashes, the length rule (one page within ~3 A4 pages, or an index within
that budget plus linked sub-pages whose links all resolve), most fact lines carry a lead, and code
leads resolve to real files in the target repo or the pack. Writes a JSON report; exit code 0 only if all pass.

    python3 check_pack.py --root ~/kung-fu-pack --repo ~/work/typer --out report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORDS_PER_PAGE = 500
MAX_PAGES = 3
DASHES = (chr(0x2014), chr(0x2013))
LINK_RE = re.compile(r"\]\(([^)#\s]+\.(?:md|html))\)")
PATH_LEAD_RE = re.compile(r"`?([\w./-]+/[\w.-]+\.\w+)(?::\d+(?:-\d+)?)?`?")
# A lead is a URL, a file:line, a path, or inline code that names something locatable (a path,
# a dotted symbol, a #ref). A bare backticked word is not a lead.
LEAD_RE = re.compile(r"(https?://|`[^`\s]*[./:#][^`]*`|[\w./-]+\.\w+:\d+|[\w-]+/[\w./-]+\.\w+)")


def words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def newest_pack(root: Path) -> Path | None:
    packs = [p for p in (root / "packs").glob("*") if p.is_dir()]
    return max(packs, key=lambda p: p.stat().st_mtime) if packs else None


def check(root: Path, repo: Path) -> dict:
    res: dict = {"checks": {}}
    pack = newest_pack(root)
    if pack is None:
        res["checks"]["pack_exists"] = False
        return res
    res["pack"] = pack.name
    c = res["checks"]
    c["pack_exists"] = True
    c["research_cached"] = any((pack / "research").glob("*"))
    c["plan_written"] = (pack / "plan.md").exists()

    pages = sorted((pack / "out").rglob("*.md")) + sorted((pack / "out").rglob("*.html"))
    c["output_exists"] = bool(pages)
    if not pages:
        return res
    texts = {p: p.read_text(errors="ignore") for p in pages}
    allt = "\n".join(texts.values())
    c["zero_dashes"] = sum(allt.count(d) for d in DASHES) == 0

    index = next((p for p in pages if p.stem.lower() == "index"), None)
    links = LINK_RE.findall(texts[index]) if index else []
    nested = index is not None and len(pages) >= 3 and len(links) >= 2
    res["structure"] = {"pages": len(pages), "nested": nested,
                        "total_pages": round(words(allt) / WORDS_PER_PAGE, 2)}
    if nested:
        c["length_ok"] = words(texts[index]) <= MAX_PAGES * WORDS_PER_PAGE
        c["links_resolve"] = all((index.parent / ln).exists() for ln in links)
    else:
        c["length_ok"] = words(allt) <= MAX_PAGES * WORDS_PER_PAGE

    facts = [ln for ln in allt.splitlines()
             if ln.strip().startswith(("-", "*", "|")) and len(ln.strip()) > 20
             and not re.fullmatch(r"\|[\s:|-]+\|", ln.strip())]
    with_lead = [ln for ln in facts if LEAD_RE.search(ln)]
    res["lead_ratio"] = round(len(with_lead) / len(facts), 3) if facts else 0.0
    c["leads_present"] = res["lead_ratio"] >= 0.6

    # Version strings like 3.10/3.12 are not paths; pack-relative leads (research/, plan.md) are
    # valid and resolve against the pack itself.
    paths = {m.group(1).removeprefix("./") for ln in with_lead
             for m in PATH_LEAD_RE.finditer(re.sub(r"https?://\S+", "", ln))
             if not m.group(1).startswith(("http", "www.")) and not m.group(1)[0].isdigit()}

    def resolves(p: str) -> bool:
        # exact path in the repo or pack, else a repo file whose path ends with the lead
        # (leads are often written relative to a package dir); never a bare basename match
        if (repo / p).exists() or (pack / p).exists() or (pack / "out" / p).exists():
            return True
        return "/" in p and any(str(f).endswith("/" + p) for f in repo.rglob(Path(p).name))
    resolved = [p for p in paths if resolves(p)]
    res["code_leads"] = {"distinct": len(paths), "resolved": len(resolved),
                         "unresolved_sample": sorted(paths - set(resolved))[:10]}
    c["code_leads_resolve"] = not paths or len(resolved) / len(paths) >= 0.8
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = check(Path(a.root).expanduser(), Path(a.repo).expanduser())
    res["pass"] = bool(res["checks"]) and all(res["checks"].values())
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
