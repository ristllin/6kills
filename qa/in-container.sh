#!/bin/bash
# One harness, one clean container: fresh-install 6kills from the committed ref, then run the
# kung-fu-pack scenarios against a real public repo. Writes everything to /out/<harness>/.
#   in-container.sh <claude|codex|vibe>
set -uo pipefail

H="${1:?usage: in-container.sh <claude|codex|vibe>}"
OUT="/out/$H"; mkdir -p "$OUT"
REF="${KFP_QA_REF:-HEAD}"
TARGET_REPO="${KFP_QA_TARGET_REPO:-fastapi/typer}"
[[ "$TARGET_REPO" == *://* ]] || TARGET_REPO="https://github.com/$TARGET_REPO"  # owner/repo or a URL
TARGET_NAME="$(basename "$TARGET_REPO")"
log(){ echo "[$H] $*" | tee -a "$OUT/steps.log"; }

# --- 1. fresh install from the committed ref (not the host's working tree) ---
git config --global --add safe.directory '*'
git clone -q /src "$HOME/6kills" && git -C "$HOME/6kills" checkout -q "$REF" || { log "FAIL clone"; exit 1; }
log "cloned 6kills at $(git -C "$HOME/6kills" rev-parse --short HEAD)"

case "$H" in
  claude)
    claude plugin marketplace add "$HOME/6kills" >>"$OUT/install.log" 2>&1
    claude plugin install kung-fu-pack@6kills >>"$OUT/install.log" 2>&1
    claude plugin list 2>&1 | tee -a "$OUT/install.log" | grep -q "kung-fu-pack" \
      && log "PASS install" || log "FAIL install" ;;
  codex|vibe)
    bash "$HOME/6kills/plugins/kung-fu-pack/install.sh" "$H" >>"$OUT/install.log" 2>&1
    test -f "$HOME/.$H/skills/kung-fu-pack/SKILL.md" && log "PASS install" || log "FAIL install" ;;
esac

# Harness config is supplied read-only by the host (never baked into the image or the repo).
if [ "$H" = codex ] && [ -f /cfg/codex.config.toml ]; then
  mkdir -p "$HOME/.codex" && cp /cfg/codex.config.toml "$HOME/.codex/config.toml"
fi
if [ "$H" = vibe ] && [ -f /cfg/vibe.config.toml ]; then
  mkdir -p "$HOME/.vibe" && cp /cfg/vibe.config.toml "$HOME/.vibe/config.toml"
fi

# --- 2. a real-world target and a seeded config (same schema /kung-fu-pack-init writes) ---
mkdir -p "$HOME/work" && git clone -q --depth 1 "$TARGET_REPO" "$HOME/work/$TARGET_NAME"
mkdir -p "$HOME/kung-fu-pack/packs"
cat > "$HOME/kung-fu-pack/config.json" <<JSON
{"version": 1, "output_default": "md", "notion_destination": "draft",
 "workspace_root": "$HOME/kung-fu-pack", "sources": {"code": true, "web": true, "notion": false,
 "linear": false, "beeper": false}, "code_roots": ["$HOME/work"], "depth": "standard",
 "model": "inherit", "writing_standard": "default",
 "house_rules": {"no_em_dashes": true, "every_claim_has_a_lead": true, "flag_staleness": true,
  "confirm_before_overwrite": true, "default_audience": "", "extra": []}}
JSON

run(){  # prompt -> transcript file
  local prompt="$1" file="$2"
  case "$H" in
    claude) claude -p "$prompt" --permission-mode bypassPermissions --output-format text ;;
    codex)  codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
              ${KFP_QA_CODEX_MODEL:+-m "$KFP_QA_CODEX_MODEL"} "$prompt" ;;
    vibe)   vibe -p "$prompt" --trust --output text --max-turns 150 ;;
  esac >"$file" 2>&1
}

case "$H" in
  claude) INVOKE="/kung-fu-pack" ;;
  codex)  INVOKE="\$kung-fu-pack" ;;
  vibe)   INVOKE="/kung-fu-pack" ;;
esac

# --- 3. scenario A: a thin request must trigger general, parameter-shaped questions ---
log "scenario A (interview)"
run "$INVOKE build me an onboarding brief" "$OUT/A_interview.txt"

# --- 4. scenario B: a full pack on the real repo, local Markdown output ---
log "scenario B (pack on $TARGET_NAME)"
run "$INVOKE the $TARGET_NAME library checked out at $HOME/work/$TARGET_NAME. Scope: onboarding \
brief for a new maintainer covering architecture, key modules, extension points, and the testing \
and release process. Audience: an experienced Python engineer. Output: md. The scope is complete; \
do not ask questions, proceed to publish." "$OUT/B_pack.txt"

python3 /qa/check_pack.py --root "$HOME/kung-fu-pack" --repo "$HOME/work/$TARGET_NAME" \
  --out "$OUT/B_check.json" && log "PASS pack checks" || log "FAIL pack checks"
cp -R "$HOME/kung-fu-pack/packs" "$OUT/packs" 2>/dev/null
log "done"
