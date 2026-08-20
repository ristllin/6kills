#!/bin/bash
# macOS only: install / update a launchd job that runs the triage on a schedule.
# Usage:  ./update-schedule.sh <hour> [minute]
# Example: ./update-schedule.sh 9 0   → runs daily at 9:00 AM
#
# The scheduled run needs the Beeper Desktop app running at that time, and it captures
# whichever auth environment you have set right now (ANTHROPIC_API_KEY, or the Foundry
# proxy vars) from the shell where you run this script.
set -euo pipefail

HOUR=${1:?"Usage: $0 <hour> [minute]"}
MIN=${2:-0}
LABEL="com.$(id -un | tr -cd '[:alnum:]').linkedin-triage"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
RUN_SH="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/run.sh"

# Build the <EnvironmentVariables> block from whatever auth vars are currently set.
# PATH is always included so `docker` resolves under launchd's minimal environment.
emit_env() {
  printf '        <key>PATH</key>\n        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>\n'
  for var in ANTHROPIC_API_KEY ANTHROPIC_BASE_URL TRIAGE_MODEL \
             CLAUDE_CODE_USE_FOUNDRY ANTHROPIC_FOUNDRY_BASE_URL ANTHROPIC_FOUNDRY_API_KEY \
             ANTHROPIC_DEFAULT_SONNET_MODEL ANTHROPIC_DEFAULT_HAIKU_MODEL; do
    val="${!var:-}"
    if [ -n "$val" ]; then
      printf '        <key>%s</key>\n        <string>%s</string>\n' "$var" "$val"
    fi
  done
}

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${RUN_SH}</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
$(emit_env)
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>${MIN}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${HOME}/Library/Logs/linkedin-triage.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/Library/Logs/linkedin-triage.err.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
printf "[linkedin-triage] Scheduled '%s' daily at %d:%02d\n" "$LABEL" "$HOUR" "$MIN"
printf "  Logs: ~/Library/Logs/linkedin-triage.log\n"
printf "  Remove with: launchctl unload %s && rm %s\n" "$PLIST" "$PLIST"
