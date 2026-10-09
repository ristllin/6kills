"""Deterministic acceptance checks for a kung-fu-pack produced during release QA.

Checks the newest pack under <root>/packs: the workspace was used (research files + plan), the
output exists, zero em/en dashes, the length rule (one page within ~3 A4 pages, or an index within
that budget plus linked sub-pages whose links all resolve), most fact lines carry a lead, and code
leads resolve to real files in the target repo or the pack. With --show it also checks the "show
it" contract for a tool or codebase target: plan.md records an example choice, the page has a "See
it in action" section with an example within the size limit, and at least one real visual (a
non-diagram image or captured output). --product adds a linked usage sub-page, the default nesting
for a product or vendor target. Writes a JSON report; exit code 0 only if all pass.

    python3 check_pack.py --root ~/kung-fu-pack --repo ~/work/typer --out report.json [--show|--product]
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
LINK_RE = re.compile(r"\]\((?![a-z][\w+.-]*:)([^)#\s]+\.(?:md|html))\)")  # local pages only
PATH_LEAD_RE = re.compile(r"`?([\w./-]+/[\w.-]+\.\w+)(?::\d+(?:-\d+)?)?`?")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
EXAMPLE_MAX_LINES = 25  # about 15 lines is the target; this is the hard ceiling
# A lead is a URL, a file:line, a path, inline code that names something locatable (a path, a
# dotted symbol, a #ref), or a source key like [S12] resolved in a sources table. A bare backticked
# word is not a lead.
LEAD_RE = re.compile(r"(https?://|\[S\d+\]|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}/[^\s)|]+|`[^`\s]*[./:#][^`]*`|[\w./-]+\.\w+:\d+|[\w-]+/[\w./-]+\.\w+)")


def words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def newest_pack(root: Path) -> Path | None:
    packs = [p for p in (root / "packs").glob("*") if p.is_dir()]
    return max(packs, key=lambda p: p.stat().st_mtime) if packs else None


def show_checks(pack: Path, texts: dict, index: Path | None, links: list,
                product: bool) -> tuple[dict, dict]:
    """The "show it" contract: a chosen example and a real visual; products add a usage sub-page."""
    plan = (pack / "plan.md").read_text(errors="ignore") if (pack / "plan.md").exists() else ""
    main = index or next(iter(texts))
    mtext = texts[main]
    sect = re.search(r"^#+\s*(?:\d+[.)]\s*)?see it in action.*?(?=^#{1,2}\s|\Z)", mtext, re.I | re.M | re.S)
    blocks = CODE_RE.findall(sect.group(0)) if sect else []
    # A diagram is a PNG generated from an .html of the same stem in assets/; anything else embedded
    # (a screenshot, a saved vendor image) or a code block of captured output is a real visual.
    diagrams = {h.stem.removesuffix(".min") for h in (pack / "assets").glob("*.html")}
    imgs = [m for t in texts.values() for m in IMG_RE.findall(t)]
    # Notion upload refs (file-upload://) carry no name, so they cannot be told apart; skip them.
    real_imgs = [i for i in imgs if Path(i).stem not in diagrams and not i.startswith("file-upload:")]
    output = [b for t in texts.values() for b in re.findall(r"```(?!mermaid)[^\n]*\n(.*?)```", t, re.S)]
    checks = {
        "example_choice_planned": bool(re.search(r"example choice", plan, re.I)),
        "see_it_in_action": sect is not None and (bool(blocks) or bool(IMG_RE.search(sect.group(0)))),
        "example_size_ok": all(len(b.strip().splitlines()) <= EXAMPLE_MAX_LINES for b in blocks),
        "real_visual": bool(real_imgs) or bool(output),
    }
    if product:
        checks["usage_subpage"] = any("usage" in ln.lower() and (main.parent / ln).exists()
                                      for ln in links)
    return checks, {"real_images": real_imgs[:10], "example_blocks": len(blocks)}


def check(root: Path, repo: Path, show: bool = False, product: bool = False) -> dict:
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

    # The .md and .html outputs are the same page in two formats; count one of them.
    pages = sorted((pack / "out").rglob("*.md")) or sorted((pack / "out").rglob("*.html"))
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
    if show or product:
        sc, res["show"] = show_checks(pack, texts, index, links or LINK_RE.findall(texts[pages[0]]),
                                      product)
        c.update(sc)

    sep = re.compile(r"\|[\s:|-]+\|")
    lines = allt.splitlines()
    # a table header is the row right above its |---| separator; it names columns, not facts
    facts = [ln for i, ln in enumerate(lines)
             if ln.strip().startswith(("-", "*", "|")) and len(ln.strip()) > 20
             and not sep.fullmatch(ln.strip())
             and not (i + 1 < len(lines) and sep.fullmatch(lines[i + 1].strip()))]
    with_lead = [ln for ln in facts if LEAD_RE.search(ln)]
    res["lead_ratio"] = round(len(with_lead) / len(facts), 3) if facts else 0.0
    c["leads_present"] = res["lead_ratio"] >= 0.6

    # Version strings like 3.10/3.12 are not paths; pack-relative leads (research/, plan.md) are
    # valid and resolve against the pack itself.
    paths = {m.group(1).removeprefix("./") for ln in with_lead
             for m in PATH_LEAD_RE.finditer(re.sub(r"(https?://|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}/)\S+", "", ln))
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
    ap.add_argument("--show", action="store_true", help="also check the show-it contract")
    ap.add_argument("--product", action="store_true", help="--show plus a linked usage sub-page")
    a = ap.parse_args()
    res = check(Path(a.root).expanduser(), Path(a.repo).expanduser(), a.show, a.product)
    res["pass"] = bool(res["checks"]) and all(res["checks"].values())
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
