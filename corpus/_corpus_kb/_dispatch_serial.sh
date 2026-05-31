#!/usr/bin/env bash
set -uo pipefail
SKILL=/home/angelus/.claude/skills/multi-model-orchestration
cd "$(dirname "$0")/_authored"
valid() { local f="$1"; [ -f "$f" ] && [ "$(wc -c <"$f")" -ge 1500 ] && head -1 "$f" | grep -q '^---'; }
done=0; skip=0; fail=0
for p in prompts/*.txt; do
  s=$(basename "$p" .txt); out="raw/$s.md"
  if valid "$out"; then skip=$((skip+1)); continue; fi
  bash "$SKILL/scripts/call_gemini.sh" gemini-3-flash-preview executive-prose "$(cat "$p")" > "$out" 2>"raw/$s.err"
  rc=$?; echo "$rc $s" > "raw/$s.code"
  if valid "$out"; then done=$((done+1)); echo "OK $s"; else fail=$((fail+1)); echo "FAIL($rc) $s"; fi
  sleep 5
done
echo "SUMMARY done=$done skip=$skip fail=$fail"
