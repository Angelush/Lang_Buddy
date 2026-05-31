#!/usr/bin/env bash
set -uo pipefail
SKILL=/home/angelus/.claude/skills/multi-model-orchestration
RAW=_authored/raw
MAXJOBS=3
one() {
  local slug="$1"
  bash "$SKILL/scripts/call_gemini.sh" gemini-3-flash-preview executive-prose \
    "$(cat _authored/prompts/$slug.txt)" > "$RAW/$slug.md" 2>"$RAW/$slug.err"
  echo "$? $slug" > "$RAW/$slug.code"
}
for f in _authored/prompts/*.txt; do
  slug=$(basename "$f" .txt)
  one "$slug" &
  while [ "$(jobs -r | wc -l)" -ge "$MAXJOBS" ]; do wait -n; done
done
wait
echo "ALL DONE"
