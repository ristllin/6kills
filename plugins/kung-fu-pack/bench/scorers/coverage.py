"""Anti-redundancy scorer (offline).

Compression quality is partly "say each distinct thing once." This penalizes intra-brief
redundancy: near-duplicate sentences waste the length budget. Distinct-information COVERAGE is
already measured by nugget/integration recall (scorers/nuggets.py); this complements it with a
redundancy penalty, computed as 1 - mean(max pairwise token-Jaccard) over sentences.
"""
from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

from scorers import brief as brief_mod


def _brief(pack: Path) -> str:
    return brief_mod.read(pack)



def _sentences(text: str):
    text = re.sub(r"`[^`]+`|\([^)]*\)", " ", text)  # drop code/leads so content drives similarity
    parts = re.split(r"(?<=[.!?])\s+|\n", text)
    return [s.strip() for s in parts if len(s.split()) >= 5]


def _toks(s: str):
    return set(t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 2)


def score(task: dict, pack_dir: Path) -> dict:
    text = _brief(Path(pack_dir))
    sents = _sentences(text)
    if len(sents) < 2:
        return {"ran": True, "non_redundancy": 1.0, "n_sentences": len(sents)}
    tok = [_toks(s) for s in sents]
    maxsim = []
    for i, a in enumerate(tok):
        best = 0.0
        for j, b in enumerate(tok):
            if i == j or not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            best = max(best, jac)
        maxsim.append(best)
    redundancy = sum(maxsim) / len(maxsim)
    return {"ran": True, "non_redundancy": round(1 - redundancy, 3),
            "n_sentences": len(sents)}


if __name__ == "__main__":
    import sys
    print(json.dumps(score({}, Path(sys.argv[1])), indent=2))
