"""Emit pack.json for a kung-fu-pack workspace so scoring is not prose-parsing.

The skill already writes packs/<slug>/{research,plan.md,assets,out}. This post-processor
walks that workspace and writes a machine-readable manifest the scorers consume:
  output_path, output_format, sources_reached, claims[{claim, lead}], research_files,
  diagrams, staleness. It is a best-effort extractor: claims come from bullet/table lines
  in the brief, each paired with the first lead token it carries; sources_reached come
  from the SOURCES sections of research/*. A richer manifest can be emitted by the skill
  itself; this guarantees one exists for the eval.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

LEAD_RE = re.compile(r"(https?://\S+|`[^`]+`|[\w./-]+\.\w+:\d+|[0-9a-f]{8,})")
SRC_RE = re.compile(r"(https?://\S+|[A-Z]+-\d+|`[^`]+`|[\w./-]+#[\w./-]+)")


def _brief(pack: Path) -> tuple[Path | None, str]:
    for rel in ("out/index.md", "out/page.md", "out/page.html", "page.md"):
        p = pack / rel
        if p.exists():
            return p, p.read_text(errors="ignore")
    return None, ""


def build(pack_dir: Path) -> dict:
    pack = Path(pack_dir)
    brief_path, text = _brief(pack)
    claims = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("-", "*", "|")) and len(s) > 8:
            m = LEAD_RE.search(s)
            claims.append({"claim": s[:160], "lead": m.group(0) if m else ""})
    sources = set()
    research = []
    rdir = pack / "research"
    if rdir.is_dir():
        for f in sorted(rdir.glob("**/*")):
            if f.is_file():
                research.append(str(f.relative_to(pack)))
                for m in SRC_RE.findall(f.read_text(errors="ignore")):
                    sources.add(m.strip("`"))
    diagrams = [str(p.relative_to(pack)) for p in (pack / "assets").glob("*.png")] \
        if (pack / "assets").is_dir() else []
    manifest = {
        "output_path": str(brief_path.relative_to(pack)) if brief_path else None,
        "output_format": brief_path.suffix.lstrip(".") if brief_path else None,
        "sources_reached": sorted(sources),
        "claims": claims,
        "research_files": research,
        "diagrams": diagrams,
    }
    (pack / "pack.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    out = build(Path(sys.argv[1]))
    print(f"wrote pack.json: {len(out['claims'])} claims, "
          f"{len(out['sources_reached'])} sources, {len(out['research_files'])} research files")
