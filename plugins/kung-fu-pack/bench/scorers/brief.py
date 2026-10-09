"""One shared reader for a pack's brief, so every scorer grades the same text.

A brief is either a single page (out/page.md) or a nested tree (out/index.md plus linked
sub-pages). For a nested tree the full text is the index followed by every sub-page; grading
only the index would undercount whatever the sub-pages carry.
"""
from __future__ import annotations

from pathlib import Path

TOP_PAGES = ("out/index.md", "out/page.md", "out/page.html", "page.md")


def pages(pack: Path) -> list[Path]:
    """The brief's pages, top page first."""
    pack = Path(pack)
    top = next((pack / rel for rel in TOP_PAGES if (pack / rel).exists()), None)
    outdir = pack / "out"
    rest = sorted(outdir.rglob("*.md")) if outdir.is_dir() else []
    ordered = ([top] if top else []) + [p for p in rest if p != top]
    return ordered


def read(pack: Path) -> str:
    return "\n\n".join(p.read_text(errors="ignore") for p in pages(pack))


def read_top(pack: Path) -> str:
    ps = pages(pack)
    return ps[0].read_text(errors="ignore") if ps else ""
