#!/usr/bin/env bash
# Dispatch dialogue-authoring prompts (_authored/prompts2/*.txt) to free
# providers: EN -> gemini-3-flash-preview, FR -> mistral-medium-3.5.
# Resumable: skips a slug whose raw output already contains a '---' frontmatter.
#
#   _author_dispatch.sh <en|fr|all> [concurrency]
#   _author_dispatch.sh __one <slug> <provider>   (internal)
set -uo pipefail
KB="$(cd "$(dirname "$0")" && pwd)"
SKILL="/home/angelus/.claude/skills/multi-model-orchestration/scripts"
PROMPTS="$KB/_authored/prompts2"
RAW="$KB/_authored/raw2"
mkdir -p "$RAW"

if [[ "${1:-}" == "__one" ]]; then
  slug="$2"; provider="$3"
  prompt="$(cat "$PROMPTS/$slug.txt")"
  out="$RAW/$slug.md"; err="$RAW/$slug.err"
  if [[ "$provider" == gemini* ]]; then
    bash "$SKILL/call_gemini.sh" "$provider" reasoning "$prompt" > "$out" 2> "$err"
  else
    bash "$SKILL/call_vibe.sh" "$provider" reasoning "$prompt" > "$out" 2> "$err"
  fi
  echo "  $slug  bytes=$(wc -c < "$out")"
  exit 0
fi

FILTER="${1:-all}"
CONC="${2:-2}"
> "$RAW/_worklist.txt"
for f in "$PROMPTS"/*.txt; do
  slug="$(basename "$f" .txt)"
  lang="${slug%%-*}"
  [[ "$FILTER" != all && "$lang" != "$FILTER" ]] && continue
  raw="$RAW/$slug.md"
  if [[ -f "$raw" ]] && grep -q '^---' "$raw"; then continue; fi
  if [[ "$lang" == en ]]; then prov="gemini-3-flash-preview"; else prov="mistral-medium-3.5"; fi
  echo "$slug $prov" >> "$RAW/_worklist.txt"
done
count=$(wc -l < "$RAW/_worklist.txt")
echo "authoring $count dialogues (filter=$FILTER conc=$CONC)"
[[ "$count" -eq 0 ]] && { echo "nothing to do"; exit 0; }
xargs -P "$CONC" -L1 bash "$0" __one < "$RAW/_worklist.txt"
echo "ALL DONE filter=$FILTER"
