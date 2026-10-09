"""Thin subprocess callers for the three harnesses (writer + judge roles).

Each returns stdout text and never raises. Keys come from each CLI's own environment; nothing is
logged here. Prompts carry third-party text (abstracts, release notes, model-written briefs), so
calls are least-privilege: a judge call (no cwd) gets no tools; a writer call (cwd = its pack dir)
may only edit files inside that dir, never run shell commands. The Codex profile is configurable (KFP_CODEX_PROFILE) because profile names are local
to each machine.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

WALL = int(os.environ.get("KFP_CALL_WALL_S", "600"))
CODEX_PROFILE = os.environ.get("KFP_CODEX_PROFILE", "")


def _run(cmd: list[str], prompt: str, cwd: str | None = None) -> str:
    # The prompt goes on stdin: a 400k-char corpus as one argv entry hits E2BIG on Linux.
    # A judge call (no cwd) runs in an empty temp dir, so it never picks up the caller's repo
    # (its AGENTS.md, project config, or files) as context.
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = subprocess.run(cmd, input=prompt, cwd=cwd or tmp, capture_output=True, text=True,
                               timeout=WALL)
        return (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.returncode and p.stderr else "")
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:  # noqa: BLE001
        return f"[error] {e}"


def claude(prompt: str, cwd: str | None = None) -> str:
    tools = ["--tools", "Read,Write,Edit", "--permission-mode", "acceptEdits"] if cwd \
        else ["--tools", ""]
    return _run(["claude", "-p", "--model", os.environ.get("KFP_CLAUDE_MODEL", "opus"),
                 *tools, "--output-format", "text"], prompt, cwd=cwd)


def codex(prompt: str, cwd: str | None = None) -> str:
    profile = ["-p", CODEX_PROFILE] if CODEX_PROFILE else []
    sandbox = ["-s", "workspace-write"] if cwd else ["-s", "read-only"]
    return _run(["codex", "exec", *profile, *sandbox, "--skip-git-repo-check", "-"], prompt, cwd=cwd)


def vibe(prompt: str, cwd: str | None = None) -> str:
    if not os.environ.get("MISTRAL_API_KEY"):
        return "[skip] MISTRAL_API_KEY not set"
    mode = ["--agent", "accept-edits", "--trust", "--max-turns", "40"] if cwd \
        else ["--agent", "plan", "--max-turns", "6"]
    return _run(["vibe", "-p", *mode, "--output", "text"], prompt, cwd=cwd)


CALLERS = {"claude": claude, "codex": codex, "vibe": vibe}


def call(name: str, prompt: str, cwd: str | None = None) -> str:
    return CALLERS.get(name, claude)(prompt, cwd=cwd)
