#!/bin/bash
# Release QA for 6kills: build a clean image, then fresh-install and exercise kung-fu-pack on
# Claude Code, Codex, and Vibe in parallel containers. Prints a PASS/FAIL table and writes a
# summary to $OUT/summary.md. See AGENTS.md for where this sits in the release flow.
#
#   qa/run-qa.sh [claude codex vibe]
#
# Env (all optional):
#   KFP_QA_REF          git ref to test (default: HEAD of this checkout; commit first)
#   KFP_QA_OUT          results dir (default: $TMPDIR/6kills-qa)
#   KFP_QA_CFG          dir holding codex.config.toml / vibe.config.toml to copy into the
#                       containers (read-only); keep it outside the repo
#   KFP_QA_TARGET_REPO  public repo used as the real-world target: owner/repo or a git URL
#                       (default: fastapi/typer)
#   KFP_QA_PRODUCT_REPO public repo of a product for scenario C (default: httpie/cli)
#   KFP_QA_CODEX_MODEL  model override for codex exec
# Credentials pass through by NAME only (docker -e VAR), so values never touch the command line.
# Needs a host `claude` CLI to grade scenario A. Exits nonzero if any harness fails any column.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HARNESSES=("${@:-claude codex vibe}"); read -r -a HARNESSES <<<"${HARNESSES[*]}"
OUT="${KFP_QA_OUT:-${TMPDIR:-/tmp}/6kills-qa}"
REF="${KFP_QA_REF:-$(git -C "$ROOT" rev-parse HEAD)}"
IMAGE=6kills-qa

PASS_ENV=(CLAUDE_CODE_USE_FOUNDRY ANTHROPIC_API_KEY ANTHROPIC_FOUNDRY_BASE_URL
  ANTHROPIC_FOUNDRY_API_KEY ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL
  ANTHROPIC_DEFAULT_HAIKU_MODEL OPENAI_API_KEY OPENAI_BASE_URL AZURE_OPENAI_API_KEY
  MISTRAL_API_KEY VIBE_ACTIVE_MODEL KFP_QA_CODEX_MODEL KFP_QA_TARGET_REPO KFP_QA_PRODUCT_REPO)
ENV_ARGS=(); for v in "${PASS_ENV[@]}"; do [ -n "${!v:-}" ] && ENV_ARGS+=(-e "$v"); done
CFG_ARGS=(); [ -n "${KFP_QA_CFG:-}" ] && CFG_ARGS=(-v "$KFP_QA_CFG:/cfg:ro")

case "$OUT" in ""|/|"$HOME"|"$HOME/") echo "refusing to wipe KFP_QA_OUT=$OUT" >&2; exit 2 ;; esac
rm -rf "$OUT" && mkdir -p "$OUT"
# Snapshot qa/ from the tested ref: the containers must not read live (possibly edited) scripts.
QA_DIR="$OUT/.qa-ref"; mkdir -p "$QA_DIR"
git -C "$ROOT" archive "$REF" qa | tar -x -C "$QA_DIR" || { echo "cannot export qa/ at $REF" >&2; exit 1; }
echo "building $IMAGE ..."
docker build -q -t "$IMAGE" "$QA_DIR/qa" >"$OUT/build.log" 2>&1 || { cat "$OUT/build.log"; exit 1; }

echo "testing ref ${REF:0:9} on: ${HARNESSES[*]}"
for h in "${HARNESSES[@]}"; do
  docker run --rm --name "6kills-qa-$h" ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} ${CFG_ARGS[@]+"${CFG_ARGS[@]}"} -e KFP_QA_REF="$REF" \
    -v "$ROOT:/src:ro" -v "$QA_DIR/qa:/qa:ro" -v "$OUT:/out" "$IMAGE" "$h" \
    >"$OUT/$h.container.log" 2>&1 &
done
wait

# Scenario A is judged by a model: questions must be general and parameter-shaped. The transcript
# is untrusted container output, so the grader runs with no tools. It reads the tail, where the
# reply is (Codex prints its skill-loading log first).
grade_interview(){
  local t="$OUT/$1/A_interview.txt"
  [ -s "$t" ] || { echo "FAIL (no transcript)"; return; }
  claude -p "A user asked a briefing skill only: 'build me an onboarding brief'. Below is the \
skill's reply. PASS only if it asks clarifying questions before doing research, the questions are \
general and parameter-shaped (target, audience, depth, sources, output), and it does NOT invent \
concrete project, product, team, or person names as suggestions. Reply with one line: PASS or \
FAIL, then a short reason.

=== REPLY ===
$(tail -c 12000 "$t")" --tools "" --output-format text 2>/dev/null | head -1
}

{
  echo "# 6kills QA: kung-fu-pack (ref ${REF:0:9})"
  echo
  echo "| harness | install | interview (A) | pack (B) | structure | lead ratio | product (C) |"
  echo "|---|---|---|---|---|---|---|"
  for h in "${HARNESSES[@]}"; do
    inst=$(grep -o "PASS install\|FAIL install" "$OUT/$h/steps.log" 2>/dev/null | head -1)
    a=$(grade_interview "$h")
    b=$(jq -r 'if .pass then "PASS" else "FAIL: " + ([.checks|to_entries[]|select(.value|not)|.key]|join(",")) end' "$OUT/$h/B_check.json" 2>/dev/null || echo "FAIL (no check)")
    st=$(jq -r '"\(.structure.pages) pages, nested=\(.structure.nested), \(.structure.total_pages) A4 total"' "$OUT/$h/B_check.json" 2>/dev/null)
    lr=$(jq -r '.lead_ratio' "$OUT/$h/B_check.json" 2>/dev/null)
    c=$(jq -r 'if .pass then "PASS" else "FAIL: " + ([.checks|to_entries[]|select(.value|not)|.key]|join(",")) end' "$OUT/$h/C_check.json" 2>/dev/null || echo "FAIL (no check)")
    echo "| $h | ${inst:-FAIL} | ${a:-FAIL} | $b | ${st:-n/a} | ${lr:-n/a} | $c |"
    [[ "$inst" == PASS* && "$a" == PASS* && "$b" == PASS && "$c" == PASS ]] || echo "$h" >>"$OUT/.failed"
  done
} | tee "$OUT/summary.md"
echo "artifacts: $OUT"
[ ! -s "$OUT/.failed" ]
