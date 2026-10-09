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
# pack pages only: relative, no scheme (an absolute path is a lead into the target repo); an
# #anchor or a "title" after the target is allowed
LINK_RE = re.compile(r"\]\((?![A-Za-z][\w+.-]*:|/)([^)#\s]+\.(?:md|html))(?:#[^)\s]*)?(?:\s+\"[^\"]*\")?\)")
# the extension starts with a letter, so versions (HTTP/1.1, v2/3.12) are not paths
PATH_LEAD_RE = re.compile(r"`?([\w./-]+/[\w.-]+\.[A-Za-z]\w*)(?::\d+(?:-\d+)?)?`?")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
# Captured output: an untagged or text/console/shell-style fence, or any fence whose body starts
# with a shell prompt (a python or mermaid block is not output).
OUTPUT_LANGS = {"", "text", "txt", "console", "shell", "shell-session", "output", "terminal", "http"}
EXAMPLE_MAX_LINES = 25  # about 15 lines is the target; this is the hard ceiling
# A lead is a URL, a file:line, a path, inline code that names something locatable (a path, a
# dotted symbol, a #ref), a source key like [S12] resolved in a sources table, or a Markdown link
# (inline to a relative file, or reference-style [text][ref]). A bare backticked word or a bare
# domain path (the style requires full https:// URLs) is not a lead.
LEAD_RE = re.compile(r"(https?://|\[S\d+\]|\]\[[^\]\s][^\]]*\]|\]\((?:\.\.?/)?[\w-][^)\s]*\)|`[^`\s]*[./:#][^`]*`|[\w./-]+\.\w+:\d+|[\w-]+/[\w./-]+\.\w+)")


def words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def main_page(pages: list) -> Path:
    """index, else page, else the largest page that is not a usage or business sub-page."""
    for stem in ("index", "page"):  # the shallowest one, if a sub-folder has its own index
        hits = [p for p in pages if p.stem.lower() == stem]
        if hits:
            return min(hits, key=lambda p: (len(p.parts), str(p)))
    rest = [p for p in pages if p.stem.lower() not in ("usage", "business")] or pages
    return max(rest, key=lambda p: p.stat().st_size)


def newest_pack(root: Path) -> Path | None:
    packs = [p for p in (root / "packs").glob("*") if p.is_dir()]
    return max(packs, key=lambda p: p.stat().st_mtime) if packs else None


def section(text: str, title: str) -> str | None:
    """The body of the first heading named `title` (optionally numbered), up to the next heading
    of the same or a higher level."""
    m = re.search(rf"^(#+)\s*(?:\d+[.)]\s*)?{title}.*$", text, re.I | re.M)
    if not m:
        return None
    end = re.compile(rf"^#{{1,{len(m.group(1))}}}\s", re.M).search(text, m.end())
    return text[m.start():end.start() if end else len(text)]


def show_checks(pack: Path, texts: dict, main: Path, links: list,
                product: bool) -> tuple[dict, dict]:
    """The "show it" contract: a chosen example and a real visual; products add a usage sub-page."""
    plan = (pack / "plan.md").read_text(errors="ignore") if (pack / "plan.md").exists() else ""
    sect = section(texts[main], "see it in action")
    blocks = [m.group(2) for m in FENCE_RE.finditer(sect)] if sect else []
    # A diagram is a PNG generated from an .html of the same stem in assets/; anything else embedded
    # (a screenshot, a saved vendor image) or a block of captured output is a real visual. Whether a
    # screenshot shows the product (not a blog or repo page) is judged by eye and by bench taste.py.
    diagrams = {h.stem.removesuffix(".min") for h in (pack / "assets").glob("*.html")}
    imgs = [m for t in texts.values() for m in IMG_RE.findall(t)]
    # Notion upload refs (file-upload://) carry no name, so they cannot be told apart; skip them.
    # A screenshot is raster; an SVG is a drawn diagram even without an .html source.
    real_imgs = [i for i in imgs if Path(i).stem not in diagrams and not i.startswith("file-upload:")
                 and Path(i).suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp")]
    # a block labelled "Illustrative" just above or below it is crafted, not captured. The window
    # stops at the neighbouring fences, but a label over a code block also covers the output
    # block right after it ("Illustrative example and output"), unless it calls that output real
    # or captured.
    def labelled(t: str, fences: list, i: int) -> bool:
        m = fences[i]
        lo = max(m.start() - 300, fences[i - 1].end() if i else 0)
        hi = min(m.end() + 200, fences[i + 1].start() if i + 1 < len(fences) else len(t))
        if "illustrative" in (t[lo:m.start()] + t[m.end():hi]).lower():
            return True
        if not i or t[fences[i - 1].end():m.start()].strip():
            return False
        prev = fences[i - 1]
        label = t[max(prev.start() - 300, fences[i - 2].end() if i > 1 else 0):prev.start()].lower()
        return "illustrative" in label and not re.search(r"\b(real|captured)\b", label)
    output = []
    for t in texts.values():
        fences = list(FENCE_RE.finditer(t))
        output += [m for i, m in enumerate(fences)
                   if (m.group(1).strip().lower() in OUTPUT_LANGS or m.group(2).startswith("$ "))
                   and not labelled(t, fences, i)]
    checks = {
        "example_choice_planned": bool(re.search(r"example choice", plan, re.I)),
        "see_it_in_action": sect is not None and (bool(blocks) or bool(IMG_RE.search(sect))),
        "example_size_ok": all(len(b.strip().splitlines()) <= EXAMPLE_MAX_LINES for b in blocks),
        "real_visual": bool(real_imgs) or bool(output),
    }
    if product:
        checks["usage_subpage"] = any("usage" in ln.lower() and (main.parent / ln).exists()
                                      for ln in links)
    return checks, {"real_images": real_imgs[:10], "example_blocks": len(blocks)}


def check(root: Path, repo: Path, show: bool = False, product: bool = False,
          slug: str | None = None) -> dict:
    res: dict = {"checks": {}}
    pack = (root / "packs" / slug) if slug else newest_pack(root)
    if pack is None or not pack.is_dir():
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

    main = main_page(pages)
    index = main if main.stem.lower() == "index" else None
    links = LINK_RE.findall(texts[main])
    # nested = an index linking at least one other page (a product's index + usage is the smallest tree)
    subpages = {(main.parent / ln).resolve() for ln in links} - {main.resolve()}
    nested = index is not None and any(p.resolve() in subpages for p in pages)
    res["structure"] = {"pages": len(pages), "nested": nested,
                        "total_pages": round(words(allt) / WORDS_PER_PAGE, 2)}
    if nested:
        c["length_ok"] = words(texts[index]) <= MAX_PAGES * WORDS_PER_PAGE
        c["links_resolve"] = all((index.parent / ln).exists() for ln in links)
    else:
        c["length_ok"] = words(allt) <= MAX_PAGES * WORDS_PER_PAGE
    if show or product:
        sc, res["show"] = show_checks(pack, texts, main, links, product)
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
             for m in PATH_LEAD_RE.finditer(re.sub(r"(https?://|(?<![\w/.])[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}/)\S+", "", ln))
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
    ap.add_argument("--pack", help="pack slug under <root>/packs (default: the newest pack)")
    a = ap.parse_args()
    res = check(Path(a.root).expanduser(), Path(a.repo).expanduser(), a.show, a.product, a.pack)
    res["pass"] = bool(res["checks"]) and all(res["checks"].values())
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
