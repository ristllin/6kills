"""Thin subprocess callers for the three harnesses (writer + judge roles).

Each returns stdout text and never raises. Keys come from each CLI's own environment; nothing is
logged here. The Codex profile is configurable (KFP_CODEX_PROFILE) because profile names are local
to each machine.
"""
from __future__ import annotations

import os
import subprocess

WALL = int(os.environ.get("KFP_CALL_WALL_S", "600"))
CODEX_PROFILE = os.environ.get("KFP_CODEX_PROFILE", "")


def _run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=WALL)
        return (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.returncode and p.stderr else "")
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:  # noqa: BLE001
        return f"[error] {e}"


def claude(prompt: str, cwd: str | None = None) -> str:
    return _run(["claude", "-p", prompt, "--model", os.environ.get("KFP_CLAUDE_MODEL", "opus"),
                 "--permission-mode", "bypassPermissions", "--output-format", "text"], cwd=cwd)


def codex(prompt: str, cwd: str | None = None) -> str:
    profile = ["-p", CODEX_PROFILE] if CODEX_PROFILE else []
    return _run(["codex", "exec", *profile, "--skip-git-repo-check", prompt], cwd=cwd)


def vibe(prompt: str, cwd: str | None = None) -> str:
    if not os.environ.get("MISTRAL_API_KEY"):
        return "[skip] MISTRAL_API_KEY not set"
    return _run(["vibe", "-p", prompt, "--trust", "--output", "text", "--max-turns", "6"], cwd=cwd)


CALLERS = {"claude": claude, "codex": codex, "vibe": vibe}


def call(name: str, prompt: str, cwd: str | None = None) -> str:
    return CALLERS.get(name, claude)(prompt, cwd=cwd)
