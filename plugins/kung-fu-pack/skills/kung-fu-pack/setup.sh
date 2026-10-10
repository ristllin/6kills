#!/bin/bash
# Kung-Fu Pack - setup / capability checker.
# Verifies the local render toolchain and reports workspace + config state. Safe to re-run.
# It never checks MCP auth (that lives in the Claude Code MCP layer); the init command probes
# Notion/Linear/Tavily/Beeper via ToolSearch instead.
set -uo pipefail

ROOT="${KUNG_FU_PACK_ROOT:-$HOME/kung-fu-pack}"
ok()   { printf "  \033[32mok\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31mx\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "== Kung-Fu Pack setup check =="

# 1. node - diagram generation
echo "[1/4] node (diagram generation)"
if command -v node >/dev/null 2>&1; then ok "node $(node --version)."
else warn "node not found. Install it (macOS: brew install node) to generate diagrams. HTML/MD text still work without it."; fi

# 2. a Chrome/Chromium binary - PNG rendering
echo "[2/4] Chrome/Chromium (PNG render)"
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null)" \
  "$(command -v chromium 2>/dev/null)" \
  "$(command -v chromium-browser 2>/dev/null)"; do
  if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
done
if [ -n "$CHROME" ]; then ok "found: $CHROME"
else warn "No Chrome/Chromium found. Diagrams will generate as HTML but not render to PNG. Install Google Chrome, or use --output=html (diagrams inline) which does not need it."; fi

# 3. python3 - local preview server + HTML inlining helper
echo "[3/4] python3 (preview server / html inlining)"
if command -v python3 >/dev/null 2>&1; then ok "python3 $(python3 --version 2>&1 | awk '{print $2}')."
else warn "python3 not found. Only needed for --output=server and the base64 HTML helper."; fi

# 4. workspace + config
echo "[4/4] workspace + config ($ROOT)"
mkdir -p "$ROOT/packs" 2>/dev/null
if [ -d "$ROOT/packs" ]; then ok "workspace ready at $ROOT/packs."; else bad "could not create $ROOT/packs."; fi
if [ -f "$ROOT/config.json" ]; then ok "config.json present."
else warn "no config.json yet. Run /kung-fu-pack-init to create it (detects your sources + saves defaults)."; fi

echo
echo "Done. Diagrams need node + Chrome; Notion output needs the Notion MCP; everything else degrades."
