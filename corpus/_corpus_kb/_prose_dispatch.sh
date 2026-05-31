#!/usr/bin/env bash
# Dispatch prose-layer batches to free providers with a concurrency cap.
# Resumable: skips any batch whose raw output already holds >=1 ===FILE: marker.
# Paths are overridable via env (BATCHES / PROMPTS_DIR / RAW_DIR) for round 2.
#
#   _prose_dispatch.sh <gemini|mistral|all> [concurrency]
#   _prose_dispatch.sh __one <batch_id> <model> <gemini|mistral>   (internal)
set -uo pipefail
KB="$(cd "$(dirname "$0")" && pwd)"
SKILL="/home/angelus/.claude/skills/multi-model-orchestration/scripts"
export BATCHES="${BATCHES:-_prose/batches.json}"
export PROMPTS_DIR="${PROMPTS_DIR:-_prose/prompts}"
export RAW_DIR="${RAW_DIR:-_prose/raw}"

if [[ "${1:-}" == "__one" ]]; then
  batch_id="$2"; model="$3"; prov="$4"
  prompt="$(cat "$KB/$PROMPTS_DIR/$batch_id.txt")"
  out="$KB/$RAW_DIR/$batch_id.md"; err="$KB/$RAW_DIR/$batch_id.err"
  if [[ "$prov" == gemini ]]; then
    bash "$SKILL/call_gemini.sh" "$model" extraction "$prompt" > "$out" 2> "$err"
  else
    bash "$SKILL/call_vibe.sh" "$model" extraction "$prompt" > "$out" 2> "$err"
  fi
  n=$(grep -c '^===FILE:' "$out" 2>/dev/null)
  echo "  $batch_id  markers=$n"
  exit 0
fi

FILTER="${1:-all}"
CONC="${2:-3}"
cd "$KB"
mkdir -p "$RAW_DIR"
python3 - "$FILTER" > "$RAW_DIR/_worklist.txt" <<'PY'
import json, os, sys, pathlib
filt = sys.argv[1]
raw_dir = pathlib.Path(os.environ["RAW_DIR"])
for x in json.load(open(os.environ["BATCHES"])):
    prov = 'gemini' if x['provider'].startswith('gemini') else 'mistral'
    if filt != 'all' and prov != filt:
        continue
    raw = raw_dir / (x['batch_id'] + '.md')
    if raw.exists() and raw.read_text(errors='replace').count('===FILE:') >= 1:
        continue
    print(x['batch_id'], x['provider'], prov)
PY
count=$(wc -l < "$RAW_DIR/_worklist.txt")
echo "dispatching $count batches (filter=$FILTER conc=$CONC batches=$BATCHES)"
[[ "$count" -eq 0 ]] && { echo "nothing to do"; exit 0; }
xargs -P "$CONC" -L1 bash "$0" __one < "$RAW_DIR/_worklist.txt"
echo "ALL DONE filter=$FILTER"
