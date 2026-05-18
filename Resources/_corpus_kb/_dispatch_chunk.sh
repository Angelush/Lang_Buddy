#!/usr/bin/env bash
# Dispatch one extraction chunk to a free-tier API.
# Usage: _dispatch_chunk.sh <chunk_id> <provider:gemini|vibe>
set -euo pipefail
CHUNK="$1"
PROVIDER="${2:-gemini}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
PROMPT_FILE="$ROOT/_dispatch_prompts/$CHUNK.prompt.txt"
OUT_FILE="$ROOT/_dispatch_outputs/$CHUNK.out.txt"
ERR_FILE="$ROOT/_dispatch_outputs/$CHUNK.err.txt"

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "missing prompt: $PROMPT_FILE" >&2
  exit 2
fi

mkdir -p "$ROOT/_dispatch_outputs"

START=$(date +%s)
echo "[start $(date -u +%Y-%m-%dT%H:%M:%S)] chunk=$CHUNK provider=$PROVIDER" >> "$ROOT/_dispatch.log"

case "$PROVIDER" in
  gemini)
    GMODEL="${GEMINI_MODEL:-gemini-2.5-flash-lite}"
    if gemini -m "$GMODEL" -o text < "$PROMPT_FILE" > "$OUT_FILE" 2> "$ERR_FILE"; then
      STATUS=ok
    else
      STATUS=fail
    fi
    ;;
  vibe|vibe2)
    PROMPT="$(cat "$PROMPT_FILE")"
    if [[ "$PROVIDER" == "vibe2" ]]; then
      MKEY=$(grep -m1 "^Studio second account:" /home/angelus/MEGA/IA/multi-model-orchestration/Mistral.txt | awk -F': *' '{print $2}' | tr -d '[:space:]')
    else
      MKEY=$(grep -m1 "^Studio:" /home/angelus/MEGA/IA/multi-model-orchestration/Mistral.txt | awk -F': *' '{print $2}' | tr -d '[:space:]')
    fi
    if MISTRAL_API_KEY="$MKEY" vibe -p "$PROMPT" --output text --trust --max-price 0.30 > "$OUT_FILE" 2> "$ERR_FILE"; then
      STATUS=ok
    else
      STATUS=fail
    fi
    ;;
  *)
    echo "unknown provider $PROVIDER" >&2
    exit 2
    ;;
esac

END=$(date +%s)
SIZE=$(wc -c < "$OUT_FILE" 2>/dev/null || echo 0)
echo "[end   $(date -u +%Y-%m-%dT%H:%M:%S)] chunk=$CHUNK provider=$PROVIDER status=$STATUS dur=$((END-START))s size=$SIZE" >> "$ROOT/_dispatch.log"

[[ "$STATUS" == "ok" ]] || exit 1
