#!/bin/bash
# LinkedIn Triage - one-shot setup checker.
# Verifies prerequisites, builds the container image, and confirms Beeper is reachable.
# Safe to run repeatedly.
set -uo pipefail

SANDBOX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="linkedin-triage-runner"
ok()   { printf "  \033[32m✔\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31mx\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
FAIL=0

echo "== LinkedIn Triage setup check =="

# 1. Docker
echo "[1/5] Container runtime"
if ! command -v docker >/dev/null 2>&1; then
  bad "docker not found. Install OrbStack (macOS: brew install --cask orbstack) or Docker Desktop."; FAIL=1
elif ! docker info >/dev/null 2>&1; then
  bad "Docker installed but daemon not running. Start OrbStack / Docker Desktop (macOS: open -a OrbStack) and re-run."; FAIL=1
else
  ok "Docker is running."
fi

# 2. Anthropic API auth - either a direct key OR a Foundry/proxy setup
echo "[2/5] Anthropic API auth"
if [ "${CLAUDE_CODE_USE_FOUNDRY:-0}" = "1" ] || [ -n "${ANTHROPIC_FOUNDRY_BASE_URL:-}" ]; then
  if [ -n "${ANTHROPIC_FOUNDRY_BASE_URL:-}" ]; then
    ok "Foundry proxy mode (ANTHROPIC_FOUNDRY_BASE_URL set)."
  else
    bad "Foundry mode requested (CLAUDE_CODE_USE_FOUNDRY=1) but ANTHROPIC_FOUNDRY_BASE_URL is not set."; FAIL=1
  fi
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  ok "ANTHROPIC_API_KEY is set."
else
  warn "No auth set. Either: export ANTHROPIC_API_KEY=sk-ant-...  (https://console.anthropic.com)"
  warn "         or the shared proxy: export CLAUDE_CODE_USE_FOUNDRY=1 ANTHROPIC_FOUNDRY_BASE_URL=https://<proxy>/anthropic"
fi

# 3. Beeper Desktop running + local API up
echo "[3/5] Beeper Desktop local API (localhost:23373)"
CODE=$(curl -s -o /dev/null -m5 -w "%{http_code}" http://localhost:23373/v0/mcp 2>/dev/null || echo "000")
if [ "$CODE" = "000" ]; then
  bad "Beeper local API not reachable. Install/open Beeper Desktop, sign in, and enable its Desktop API (Settings)."; FAIL=1
elif [ "$CODE" = "401" ] || [ "$CODE" = "200" ]; then
  ok "Beeper local API is up (HTTP $CODE)."
else
  warn "Beeper endpoint returned HTTP $CODE (expected 200/401). Check Beeper's Desktop API setting."
fi

# 4. Beeper MCP token available on host
echo "[4/5] Beeper MCP token (from Claude Code /mcp auth)"
TOK=""
if command -v security >/dev/null 2>&1; then
  TOK=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | python3 -c "import json,sys
try:
  d=json.load(sys.stdin)
  print(next((v.get('accessToken') or v.get('access_token') for k,v in d.get('mcpOAuth',{}).items() if k.startswith('beeper|')),''))
except Exception: pass" 2>/dev/null)
fi
if [ -z "$TOK" ] && [ -f "$HOME/.claude/.credentials.json" ]; then
  TOK=$(python3 -c "import json;d=json.load(open('$HOME/.claude/.credentials.json'));print(next((v.get('accessToken') or v.get('access_token') for k,v in d.get('mcpOAuth',{}).items() if k.startswith('beeper|')),''))" 2>/dev/null)
fi
if [ -z "$TOK" ]; then
  bad "No Beeper token found. In Claude Code: add the server then run '/mcp' → beeper → Authenticate."
  echo "      claude mcp add --transport http beeper http://localhost:23373/v0/mcp -s user"; FAIL=1
else
  ok "Beeper token found (self-heals on future re-auth)."
fi

# 5. Build image
echo "[5/5] Container image"
if docker info >/dev/null 2>&1; then
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    ok "Image '$IMAGE' already built."
  else
    echo "  Building '$IMAGE' ..."
    if docker build -t "$IMAGE" "$SANDBOX" >/dev/null 2>&1; then ok "Image built."; else bad "Image build failed - run 'docker build -t $IMAGE $SANDBOX' to see the error."; FAIL=1; fi
  fi
else
  warn "Skipped image build (Docker not running)."
fi

echo
if [ "$FAIL" = "0" ]; then
  echo "All set. Customize memory/linkedin_triage_rules.md, then run:  ./run.sh"
else
  echo "Some checks failed above. Fix them, then re-run ./setup.sh"
  exit 1
fi
