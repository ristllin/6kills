"""Produce one brief: run the kung-fu-pack skill on a task in an isolated pack dir."""
from __future__ import annotations

import time
from pathlib import Path

from harnesses import llm
from harnesses.prompt import build_writer_prompt


def run_one(task: dict, writer: str, model: str, pack_dir: Path, skill_text: str) -> dict:
    pack_dir = Path(pack_dir)
    (pack_dir / "out").mkdir(parents=True, exist_ok=True)
    (pack_dir / "research").mkdir(parents=True, exist_ok=True)
    prompt = build_writer_prompt(task, skill_text)
    t0 = time.time()
    log = llm.call(writer if writer in llm.CALLERS else "claude", prompt, cwd=str(pack_dir))
    (pack_dir / "agent.log").write_text(log)
    brief = pack_dir / "out" / "page.md"
    return {
        "writer": writer, "model": model,
        "ok": brief.exists() and brief.stat().st_size > 50,
        "duration_s": round(time.time() - t0, 1),
        "brief_bytes": brief.stat().st_size if brief.exists() else 0,
    }
