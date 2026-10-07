"""Build the writer prompt: run the kung-fu-pack skill on a task, headless.

The writer gets the current SKILL.md method (so hill-climbing the skill text actually
changes behavior), the task, and an explicit output contract it can satisfy with
built-in web/file tools. It writes the brief + a research note + a manifest into the
pack dir, so scoring never parses chat.
"""
from __future__ import annotations

from pathlib import Path

CONTRACT = """
OUTPUT CONTRACT (write these files in your current directory):
1. out/page.md       the briefing: 1 to 3 A4 pages (about 500 to 1500 words). A short
                     framing line first, then tight sections and tables. EVERY claim
                     carries a lead in parentheses: a URL, a path:line, or an id. NO em
                     dashes or en dashes anywhere (use hyphens). End with a Sources section.
2. research/NOTES.md your raw findings with a SOURCES list (URLs/ids you actually used).
3. pack.json         a JSON object: {"output_path":"out/page.md","output_format":"md",
                     "sources_reached":[... the sources you actually used ...],
                     "claims":[{"claim":"...","lead":"..."} ...]}.
Research the target using your web and file tools before writing. Be concise and high
signal: a reader must understand the target and be able to answer questions from the brief
alone. Do not invent sources. When done, reply with just: BRIEF_DONE.
"""


def build_writer_prompt(task: dict, skill_text: str) -> str:
    skill = skill_text.strip()
    if len(skill) > 9000:
        skill = skill[:9000] + "\n...[truncated]"
    return (
        "You are executing the kung-fu-pack skill. Follow its method exactly.\n\n"
        "===== SKILL METHOD =====\n" + skill + "\n===== END METHOD =====\n\n"
        f"TARGET: {task['target']}\n"
        f"SCOPE: {task['scope']}\n"
        f"AUDIENCE: {task.get('audience','a technical peer new to the topic')}\n"
        f"DEPTH: {task.get('depth','standard')}\n"
        f"SOURCES AVAILABLE: {', '.join(task.get('sources_available', ['web']))}\n"
        + CONTRACT
    )
