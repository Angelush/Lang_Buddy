#!/usr/bin/env python3
"""Build tutor-optimized JSON retrieval indices.

Outputs:
  kb/index/lessons.json   — flat array, one row per dialogue (the tutor's lesson catalog)
  kb/index/vocab.json     — lemma → metadata (only entries with frequency >= 2)
  kb/index/patterns.json  — pattern_slug → metadata
  kb/index/grammar.json   — grammar_slug → metadata
  kb/index/themes.json    — theme → [lesson_id, ...]
  (audio info inlined into lessons.json as audio_path + audio_exists)

These JSONs are designed to be loaded into a system prompt or fetched on-demand
by a tutor agent. The dialogue markdown files remain the source of record; this
layer is for fast retrieval during a live lesson.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"
RES = BASE.parent  # Resources/


def parse_fm(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip()
    return out


def parse_list_field(s):
    """Parse 'patterns: [a, b, c]' style frontmatter value into a list of strings."""
    s = s.strip()
    if not s.startswith("["):
        return []
    s = s.strip("[]")
    return [x.strip().strip('"').strip("'") for x in s.split(",") if x.strip()]


def gap_count_for(slug: str) -> int:
    """Look up the gap_candidates count from the drill file if it exists."""
    drill = KB / "drills" / f"{slug}.json"
    if not drill.is_file():
        return 0
    try:
        return len(json.loads(drill.read_text(encoding="utf-8")).get("gap_candidates", []))
    except Exception:
        return 0


def line_count_for(slug: str) -> int:
    drill = KB / "drills" / f"{slug}.json"
    if not drill.is_file():
        return 0
    try:
        return len(json.loads(drill.read_text(encoding="utf-8")).get("lines", []))
    except Exception:
        return 0


def main():
    out_dir = KB / "index"
    out_dir.mkdir(exist_ok=True)

    # ---- lessons.json ----
    lessons = []
    themes_idx = defaultdict(list)
    audio_idx = {}
    for f in sorted((KB / "dialogues").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        fm = parse_fm(text)
        body = text[len(text) - len(re.sub(r"^---.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)):]
        try:
            lesson_no = int(fm.get("lesson", "0"))
        except ValueError:
            lesson_no = 0
        slug = fm.get("slug", f.stem)
        audio_rel = fm.get("audio", "").strip('"')
        # Strip a leading "Resources/" if present (the dialogue stores it that way).
        clean_rel = audio_rel
        if clean_rel.startswith("Resources/"):
            clean_rel = clean_rel[len("Resources/"):]
        audio_abs = RES / clean_rel if clean_rel else None
        audio_exists = bool(audio_abs and audio_abs.exists())
        themes = parse_list_field(fm.get("themes", "[]"))
        vocab_intro = parse_list_field(fm.get("vocab_introduced", "[]"))
        patterns_used = parse_list_field(fm.get("patterns", "[]"))
        grammar_used = parse_list_field(fm.get("grammar", "[]"))
        has_mod = "## Modernized" in body
        gap_count = gap_count_for(slug)
        line_count = line_count_for(slug)

        row = {
            "id": slug,
            "source": fm.get("source", ""),
            "lesson": lesson_no,
            "title": fm.get("title", "").strip('"'),
            "target_lang": fm.get("target_lang", ""),
            "base_lang": fm.get("base_lang", ""),
            "cefr": fm.get("cefr", ""),
            "themes": themes,
            "vocab_introduced": vocab_intro,
            "patterns": patterns_used,
            "grammar": grammar_used,
            "audio_path": audio_rel,
            "audio_exists": audio_exists,
            "has_modernized": has_mod,
            "line_count": line_count,
            "pincer_gap_count": gap_count,
            "file_path": f"kb/dialogues/{slug}.md",
        }
        lessons.append(row)
        for t in themes:
            themes_idx[t].append(slug)
        audio_idx[slug] = {"path": audio_rel, "exists": audio_exists}

    (out_dir / "lessons.json").write_text(
        json.dumps(lessons, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "themes.json").write_text(
        json.dumps(themes_idx, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # audio.json dropped — lessons.json already carries `audio_path` and `audio_exists`.

    # ---- vocab.json (ALL canonical pages, flagged with core=frequency>=2) ----
    vocab = {}
    for f in (KB / "vocab").glob("*.md"):
        text = f.read_text(encoding="utf-8")
        fm = parse_fm(text)
        try:
            freq = int(fm.get("frequency", "0"))
        except ValueError:
            freq = 0
        vocab[fm.get("slug", f.stem)] = {
            "lemma": fm.get("lemma", fm.get("title", "")).strip('"'),
            "target_lang": fm.get("target_lang", ""),
            "pos": fm.get("pos", ""),
            "gloss_es": fm.get("gloss_es", "").strip('"'),
            "frequency": freq,
            "core": freq >= 2,
            "cefr": fm.get("cefr", ""),
            "register": fm.get("register", "neutral"),
            "first_lesson": fm.get("first_lesson", "[]"),
            "file_path": f"kb/vocab/{f.stem}.md",
        }
    (out_dir / "vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---- patterns.json ----
    patterns = {}
    for f in (KB / "patterns").glob("*.md"):
        text = f.read_text(encoding="utf-8")
        fm = parse_fm(text)
        patterns[fm.get("slug", f.stem)] = {
            "title": fm.get("title", "").strip('"'),
            "form": fm.get("form", "").strip('"'),
            "function": fm.get("function", "").strip('"'),
            "target_lang": fm.get("target_lang", ""),
            "cefr": fm.get("cefr", ""),
            "file_path": f"kb/patterns/{f.stem}.md",
        }
    (out_dir / "patterns.json").write_text(
        json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # ---- grammar.json ----
    grammar = {}
    for f in (KB / "grammar").glob("*.md"):
        text = f.read_text(encoding="utf-8")
        fm = parse_fm(text)
        rule_match = re.search(r"^## Rule\s*\n(.*?)(?=^## |\Z)",
                               text, re.MULTILINE | re.DOTALL)
        rule = rule_match.group(1).strip() if rule_match else ""
        errors_match = re.search(r"^## Common errors\s*\n(.*?)(?=^## |\Z)",
                                  text, re.MULTILINE | re.DOTALL)
        common_errors = errors_match.group(1).strip() if errors_match else ""
        correct_match = re.search(r"^## When the agent should correct[^\n]*\n(.*?)(?=^## |\Z)",
                                   text, re.MULTILINE | re.DOTALL)
        correct_policy = correct_match.group(1).strip() if correct_match else ""
        grammar[fm.get("slug", f.stem)] = {
            "title": fm.get("title", "").strip('"'),
            "category": fm.get("category", ""),
            "target_lang": fm.get("target_lang", ""),
            "cefr": fm.get("cefr", ""),
            "rule": rule[:600],
            "common_errors": common_errors[:600],
            "correct_policy": correct_policy[:400],
            "file_path": f"kb/grammar/{f.stem}.md",
        }
    (out_dir / "grammar.json").write_text(
        json.dumps(grammar, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Summary
    sizes = {p.name: p.stat().st_size for p in out_dir.glob("*.json")}
    audio_ok = sum(1 for v in audio_idx.values() if v["exists"])
    print(f"lessons.json: {len(lessons)} rows  ({sizes.get('lessons.json', 0):,} bytes)")
    print(f"vocab.json:   {len(vocab)} entries (freq>=2)  ({sizes.get('vocab.json', 0):,} bytes)")
    print(f"patterns.json: {len(patterns)} entries  ({sizes.get('patterns.json', 0):,} bytes)")
    print(f"grammar.json: {len(grammar)} entries  ({sizes.get('grammar.json', 0):,} bytes)")
    print(f"themes.json:  {len(themes_idx)} themes  ({sizes.get('themes.json', 0):,} bytes)")
    print(f"audio: {audio_ok}/{len(audio_idx)} audio files exist on disk "
          f"(inlined in lessons.json as audio_path/audio_exists)")
    total = sum(sizes.values())
    print(f"\nTOTAL indices: {total:,} bytes ({total/1024:.1f} KB)")


if __name__ == "__main__":
    main()
