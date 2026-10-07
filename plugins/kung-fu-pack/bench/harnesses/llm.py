"""Thin subprocess callers for the three harnesses (writer + judge roles).

Each returns stdout text. Keys come from the ambient env (the app already has the
foundry vars; vibe/ML4 needs MISTRAL_API_KEY in env). No secret is logged here.
"""
from __future__ import annotations

import os
import subprocess

WALL = int(os.environ.get("KFP_CALL_WALL_S", "600"))


def _run(cmd: list[str], cwd: str | None = None, stdin: str | None = None) -> str:
    try:
        p = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True,
                           text=True, timeout=WALL)
        return (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.returncode and p.stderr else "")
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:  # noqa: BLE001
        return f"[error] {e}"


def claude(prompt: str, model: str = "opus", cwd: str | None = None) -> str:
    return _run(["claude", "-p", prompt, "--model", model,
                 "--permission-mode", "bypassPermissions", "--output-format", "text"], cwd=cwd)


def astra(prompt: str, cwd: str | None = None) -> str:
    return _run(["codex", "exec", "-p", "astra", "--skip-git-repo-check", prompt], cwd=cwd)


def ml4(prompt: str, cwd: str | None = None) -> str:
    env_ok = bool(os.environ.get("MISTRAL_API_KEY"))
    if not env_ok:
        return "[skip] MISTRAL_API_KEY not set"
    return _run(["vibe", "-p", prompt, "--trust", "--output", "text", "--max-turns", "6"], cwd=cwd)


CALLERS = {"claude": claude, "opus": claude, "astra": astra, "ml4": ml4}


def call(name: str, prompt: str, cwd: str | None = None) -> str:
    fn = CALLERS.get(name, claude)
    return fn(prompt, cwd=cwd)
