#!/bin/bash
# LinkedIn Triage - isolated runner.
# Runs Claude Code inside a Docker container with ONLY the triage skill + your
# triage rules mounted. The container talks to the Beeper Desktop app running on
# your host machine to read and reply to LinkedIn DMs.
#
# Usage:  ./run.sh
#
# Auth - two supported modes (see SETUP.md → "API access"):
#   Mode A (default): a standard Anthropic API key.
#       ANTHROPIC_API_KEY   (required)
#       ANTHROPIC_BASE_URL  (optional - custom Anthropic-compatible endpoint)
#       TRIAGE_MODEL        (optional - override the model, e.g. claude-sonnet-4-6)
#   Mode B (shared internal proxy): a Foundry / gateway proxy that injects the key
#       server-side. Enabled when CLAUDE_CODE_USE_FOUNDRY=1 OR ANTHROPIC_FOUNDRY_BASE_URL is set.
#       ANTHROPIC_FOUNDRY_BASE_URL    (required in this mode)
#       ANTHROPIC_FOUNDRY_API_KEY     (optional - a placeholder if the proxy injects the real key)
#       ANTHROPIC_DEFAULT_SONNET_MODEL / ANTHROPIC_DEFAULT_HAIKU_MODEL   (optional)
set -euo pipefail

# Resolve this script's directory so the package can live anywhere.
SANDBOX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="linkedin-triage-runner"
BEEPER_URL="http://host.docker.internal:23373/v0/mcp"

# Optional persisted config written by `/linkedin-triage-init` (git-ignored). It may set the
# model (TRIAGE_MODEL or ANTHROPIC_DEFAULT_* for a proxy) and/or auth. The file uses
# `export VAR="${VAR:-value}"` lines, so anything already set in your shell wins over it.
if [ -f "$SANDBOX/config.env" ]; then
  # shellcheck disable=SC1091
  . "$SANDBOX/config.env"
fi

# --- 1. Docker must be installed and running ------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "[linkedin-triage] ERROR: 'docker' not found. Install OrbStack (macOS) or Docker Desktop." >&2
  echo "  macOS:  brew install --cask orbstack   (then: open -a OrbStack)" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "[linkedin-triage] ERROR: Docker daemon not running. Start OrbStack / Docker Desktop and retry." >&2
  echo "  macOS:  open -a OrbStack   (wait ~15s, then re-run)" >&2
  exit 1
fi

# --- 2. Extract the current Beeper MCP token from the host ----------------------
# Claude Code stores the OAuth token it obtained via `/mcp` in the macOS keychain
# ("Claude Code-credentials") or, on Linux, in ~/.claude/.credentials.json.
# The container cannot run OAuth, so we read the live token here and inject it.
# This self-heals: whenever you re-auth on the host, the next run picks up the new token.
read_token_from_json() {
  python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    for k,v in d.get('mcpOAuth',{}).items():
        if k.startswith('beeper|'):
            print(v.get('accessToken') or v.get('access_token') or ''); break
except Exception:
    pass"
}

BEEPER_TOKEN=""
if command -v security >/dev/null 2>&1; then   # macOS keychain
  BEEPER_TOKEN=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | read_token_from_json || true)
fi
if [ -z "$BEEPER_TOKEN" ] && [ -f "$HOME/.claude/.credentials.json" ]; then   # Linux / fallback
  BEEPER_TOKEN=$(read_token_from_json < "$HOME/.claude/.credentials.json" || true)
fi

if [ -z "$BEEPER_TOKEN" ]; then
  echo "[linkedin-triage] ERROR: could not find a Beeper MCP token." >&2
  echo "  In Claude Code run '/mcp', authenticate the 'beeper' server, then retry." >&2
  echo "  (Make sure the Beeper Desktop app is installed, signed in, and running.)" >&2
  exit 1
fi

# --- 3. API auth: choose a mode -------------------------------------------------
# Build the list of -e flags passed to `docker run`, plus any extra /etc/hosts entries.
AUTH_ARGS=()
EXTRA_HOSTS=()
if [ "${CLAUDE_CODE_USE_FOUNDRY:-0}" = "1" ] || [ -n "${ANTHROPIC_FOUNDRY_BASE_URL:-}" ]; then
  # --- Mode B: Foundry / shared proxy ---
  if [ -z "${ANTHROPIC_FOUNDRY_BASE_URL:-}" ]; then
    echo "[linkedin-triage] ERROR: Foundry mode requested but ANTHROPIC_FOUNDRY_BASE_URL is not set." >&2
    echo "  export ANTHROPIC_FOUNDRY_BASE_URL=https://<your-proxy>/anthropic   (and CLAUDE_CODE_USE_FOUNDRY=1)" >&2
    exit 1
  fi
  AUTH_ARGS+=(-e "CLAUDE_CODE_USE_FOUNDRY=1")
  AUTH_ARGS+=(-e "ANTHROPIC_FOUNDRY_BASE_URL=${ANTHROPIC_FOUNDRY_BASE_URL}")
  AUTH_ARGS+=(-e "ANTHROPIC_FOUNDRY_API_KEY=${ANTHROPIC_FOUNDRY_API_KEY:-injected-by-proxy}")
  [ -n "${ANTHROPIC_DEFAULT_SONNET_MODEL:-}" ] && AUTH_ARGS+=(-e "ANTHROPIC_DEFAULT_SONNET_MODEL=${ANTHROPIC_DEFAULT_SONNET_MODEL}")
  [ -n "${ANTHROPIC_DEFAULT_HAIKU_MODEL:-}" ]  && AUTH_ARGS+=(-e "ANTHROPIC_DEFAULT_HAIKU_MODEL=${ANTHROPIC_DEFAULT_HAIKU_MODEL}")
  # Docker Desktop on macOS doesn't route private DNS (e.g. Tailscale MagicDNS). Resolve the
  # proxy host on the host machine and pin it into the container's /etc/hosts so it's reachable.
  PROXY_HOST=$(printf '%s' "$ANTHROPIC_FOUNDRY_BASE_URL" | sed -E 's#^[a-zA-Z]+://##; s#[:/].*$##')
  if [ -n "$PROXY_HOST" ] && command -v dig >/dev/null 2>&1; then
    PROXY_IP=$(dig +short "$PROXY_HOST" 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1 || true)
    if [ -n "$PROXY_IP" ]; then
      EXTRA_HOSTS+=(--add-host="${PROXY_HOST}:${PROXY_IP}")
    else
      echo "[linkedin-triage] WARNING: could not resolve $PROXY_HOST - proxy calls may fail from the container." >&2
    fi
  fi
  echo "[linkedin-triage] Auth mode: Foundry proxy (${PROXY_HOST:-unknown})."
else
  # --- Mode A: standard Anthropic API key ---
  if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "[linkedin-triage] ERROR: no API auth configured." >&2
    echo "  Either set a key:      export ANTHROPIC_API_KEY=sk-ant-...   (https://console.anthropic.com)" >&2
    echo "  Or use a proxy:        export CLAUDE_CODE_USE_FOUNDRY=1 ANTHROPIC_FOUNDRY_BASE_URL=https://<proxy>/anthropic" >&2
    exit 1
  fi
  AUTH_ARGS+=(-e "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
  [ -n "${ANTHROPIC_BASE_URL:-}" ] && AUTH_ARGS+=(-e "ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}")
  [ -n "${TRIAGE_MODEL:-}" ]       && AUTH_ARGS+=(-e "ANTHROPIC_MODEL=${TRIAGE_MODEL}")
  echo "[linkedin-triage] Auth mode: ANTHROPIC_API_KEY."
fi

# --- 4. Build the container image on first run ---------------------------------
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[linkedin-triage] Building container image (first run)..."
  docker build -t "$IMAGE" "$SANDBOX"
fi

# --- 5. Generate the runtime configs (never committed; contain the token) -------
# Claude Code reads MCP servers from ~/.claude.json (NOT from settings.json).
RUNTIME_MCP="$SANDBOX/.claude.runtime.json"
cat > "$RUNTIME_MCP" <<JSON
{"mcpServers":{"beeper":{"type":"http","url":"${BEEPER_URL}","headers":{"Authorization":"Bearer ${BEEPER_TOKEN}"}}}}
JSON
chmod 600 "$RUNTIME_MCP"

# Mounts: container HOME is /sandbox, CWD is /workspace.
# Claude resolves skill memory at $HOME/.claude/projects/<encoded-cwd>/memory/ ; encoded /workspace = -workspace
MEMORY_MOUNT="$SANDBOX/memory:/sandbox/.claude/projects/-workspace/memory:ro"
SETTINGS_MOUNT="$SANDBOX/settings.json:/sandbox/.claude/settings.json:ro"
MCP_MOUNT="$RUNTIME_MCP:/sandbox/.claude.json:ro"
SKILL_MOUNT="$SANDBOX/SKILL.md:/sandbox/.claude/skills/linkedin-triage/SKILL.md:ro"

# --- 6. Run --------------------------------------------------------------------
exec docker run --rm \
  -e HOME=/sandbox \
  "${AUTH_ARGS[@]}" \
  -v "$MEMORY_MOUNT" \
  -v "$SETTINGS_MOUNT" \
  -v "$MCP_MOUNT" \
  -v "$SKILL_MOUNT" \
  --add-host=host.docker.internal:host-gateway \
  ${EXTRA_HOSTS[@]+"${EXTRA_HOSTS[@]}"} \
  "$IMAGE" \
  -p /linkedin-triage
