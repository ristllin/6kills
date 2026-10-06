#!/bin/bash
# kung-fu-pack cross-harness installer.
# Materializes the portable skill into Mistral Vibe or OpenAI Codex (which both read the same
# Agent Skills SKILL.md format). For Claude Code, use the plugin marketplace instead (prints how).
#
# Usage:
#   bash install.sh vibe            # install into ${VIBE_HOME:-~/.vibe}/skills/kung-fu-pack
#   bash install.sh codex           # install into ${CODEX_HOME:-~/.codex}/skills/kung-fu-pack
#   bash install.sh claude          # print Claude Code (plugin marketplace) instructions
#   bash install.sh all             # install into every harness detected on this machine
#   bash install.sh vibe --link     # symlink instead of copy (updates track this repo)
#   bash install.sh vibe --uninstall
# With no target, it detects ~/.vibe and ~/.codex and asks nothing: it reports what it found.
set -uo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SRC/skills/kung-fu-pack"      # the portable skill (SKILL.md + references + setup.sh)
ok(){ printf "  \033[32mok\033[0m %s\n" "$1"; }
bad(){ printf "  \033[31mx\033[0m %s\n" "$1"; }
info(){ printf "  %s\n" "$1"; }

LINK=0; UNINSTALL=0; TARGET=""
for a in "$@"; do
  case "$a" in
    --link) LINK=1 ;;
    --uninstall) UNINSTALL=1 ;;
    vibe|codex|claude|all) TARGET="$a" ;;
    *) bad "unknown arg: $a"; exit 2 ;;
  esac
done

claude_help(){
  echo "Claude Code uses the plugin marketplace, not this script:"
  echo "    /plugin marketplace add ristllin/6kills"
  echo "    /plugin install kung-fu-pack@6kills"
  echo "  (or, for a local checkout: /plugin marketplace add <path-to-6kills>)"
}

# install the skill dir into a harness skills root; adds Codex/Vibe specific bits.
install_into(){
  local harness="$1" dest_root
  case "$harness" in
    vibe)  dest_root="${VIBE_HOME:-$HOME/.vibe}/skills" ;;
    codex) dest_root="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  esac
  local dest="$dest_root/kung-fu-pack"

  if [ "$UNINSTALL" = "1" ]; then
    rm -rf "$dest" && ok "removed $dest" || bad "could not remove $dest"
    return
  fi

  mkdir -p "$dest_root"
  rm -rf "$dest"
  if [ "$LINK" = "1" ]; then
    ln -s "$SKILL_SRC" "$dest" && ok "linked $harness: $dest -> $SKILL_SRC"
  else
    cp -R "$SKILL_SRC" "$dest" && ok "installed $harness: $dest"
  fi

  # Vibe: make sure the skill is user-invocable as /kung-fu-pack.
  if [ "$harness" = "vibe" ] && [ "$LINK" = "0" ]; then
    python3 - "$dest/SKILL.md" <<'PY' 2>/dev/null && ok "ensured user-invocable: true (vibe)"
import sys,re
p=sys.argv[1]; s=open(p).read()
m=re.match(r'^(---\n)(.*?)(\n---\n)(.*)$', s, re.S)
if m and 'user-invocable:' not in m.group(2):
    open(p,'w').write(m.group(1)+m.group(2)+'\nuser-invocable: true'+m.group(3)+m.group(4))
PY
  fi

  # Codex: drop the openai.yaml adapter so Codex auto-discovers it and knows its MCP deps.
  if [ "$harness" = "codex" ] && [ "$LINK" = "0" ]; then
    mkdir -p "$dest/agents"
    cp "$SRC/install/codex-openai.yaml" "$dest/agents/openai.yaml" && ok "wrote Codex agents/openai.yaml"
  fi
  info "invoke it on $harness as: /kung-fu-pack (or by name). First run writes ~/kung-fu-pack/config.json."
}

detect(){
  echo "Detected harness homes:"
  [ -d "${VIBE_HOME:-$HOME/.vibe}" ]  && ok "Vibe  (${VIBE_HOME:-$HOME/.vibe})"  || info "Vibe not found"
  [ -d "${CODEX_HOME:-$HOME/.codex}" ] && ok "Codex (${CODEX_HOME:-$HOME/.codex})" || info "Codex not found"
  echo
  echo "Run:  bash install.sh <vibe|codex|claude|all> [--link] [--uninstall]"
}

echo "== kung-fu-pack installer =="
case "$TARGET" in
  claude) claude_help ;;
  vibe)   install_into vibe ;;
  codex)  install_into codex ;;
  all)
    [ -d "${VIBE_HOME:-$HOME/.vibe}" ]   && install_into vibe  || info "skip vibe (no ${VIBE_HOME:-$HOME/.vibe})"
    [ -d "${CODEX_HOME:-$HOME/.codex}" ] && install_into codex || info "skip codex (no ${CODEX_HOME:-$HOME/.codex})"
    echo; claude_help ;;
  "") detect ;;
esac
