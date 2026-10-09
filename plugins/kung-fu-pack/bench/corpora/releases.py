"""Freeze a corpus of GitHub release notes across versions (via `gh api`, authed).

Pulls releases for one or more repos, keeps those published on/after a cutoff date
(post-training-cutoff), and writes an immutable JSON corpus + a blurbs file. Each release
body is a naturally nested changelog (sections -> bullets -> PR links), so this corpus
exercises nesting-aware compression and cross-version integration (breaking changes).

    python releases.py --repos vllm-project/vllm --after 2026-09-01 --out <fixture_dir>
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _gh_releases(repo: str) -> list[dict]:
    # --jq '.[]' emits one release object per line (NDJSON), so pagination across
    # array pages concatenates cleanly without array-boundary parsing.
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/releases?per_page=100", "--paginate", "--jq", ".[]"],
            capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            return []
        rels = []
        for line in out.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rels.append(json.loads(line))
            except Exception:
                pass
        return rels
    except Exception:
        return []


def freeze(repos: list, after: str, out: Path) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    kept = []
    for repo in repos:
        for r in _gh_releases(repo):
            pub = (r.get("published_at") or "")[:10]
            if pub and pub >= after and r.get("body"):
                kept.append({
                    "repo": repo, "tag": r.get("tag_name"), "name": r.get("name"),
                    "published": pub, "url": r.get("html_url"),
                    "body": r.get("body", ""),
                })
    kept.sort(key=lambda x: x["published"])
    (out / "corpus.json").write_text(json.dumps(kept, indent=2))
    blurbs = "\n\n".join(
        f"[{i+1}] {e['repo']} {e['tag']} ({e['published']})\n{e['url']}\n{e['body']}"
        for i, e in enumerate(kept))
    (out / "blurbs.txt").write_text(blurbs)
    meta = {"source": "github-releases", "repos": repos, "after": after, "n": len(kept),
            "oldest": min((e["published"] for e in kept), default=None),
            "newest": max((e["published"] for e in kept), default=None)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", required=True, help="comma-separated owner/repo")
    ap.add_argument("--after", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = freeze([r for r in a.repos.split(",") if r], a.after, Path(a.out))
    print(json.dumps(m, indent=2))
