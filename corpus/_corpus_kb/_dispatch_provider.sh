#!/usr/bin/env bash
# Usage: _dispatch_provider.sh <callscript> <model> <prefix>
# Authors all prompts matching prefix*, serially, via one provider. Resumable.
set -uo pipefail
SKILL=/home/angelus/.claude/skills/multi-model-orchestration
CALL="$1"; MODEL="$2"; PREFIX="$3"
cd "$(dirname "$0")/_authored"
valid(){ local f="$1"; [ -f "$f" ] && [ "$(wc -c <"$f")" -ge 1500 ] && head -1 "$f" | grep -q '^---'; }
done=0; skip=0; fail=0
for p in prompts/${PREFIX}*.txt; do
  s=$(basename "$p" .txt); out="raw/$s.md"
  if valid "$out"; then skip=$((skip+1)); continue; fi
  bash "$SKILL/scripts/$CALL" "$MODEL" executive-prose "$(cat "$p")" > "$out" 2>"raw/$s.err"
  echo "$? $s" > "raw/$s.code"
  if valid "$out"; then done=$((done+1)); echo "OK $s"; else fail=$((fail+1)); echo "FAIL $s"; fi
  sleep 4
done
echo "[${PREFIX}/${MODEL}] SUMMARY done=$done skip=$skip fail=$fail"
