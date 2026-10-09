"""Shared paths for the kung-fu-pack benchmark.

Raw, bulky run artifacts (packs, agent logs) live OUTSIDE the repo in the workspace; only curated
result JSON and the report are written back under bench/.
"""
from __future__ import annotations

import os
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("KFP_EVAL_WORKSPACE", Path.home() / "kung-fu-pack-eval"))
