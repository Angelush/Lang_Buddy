#!/usr/bin/env python3
"""Parse a dispatched chunk's output JSON and write dialogue files + manifest.

Usage:
  python3 _apply_chunk.py <chunk_id>

Reads _dispatch_outputs/<chunk_id>.out.txt, extracts the JSON block, writes:
- kb/dialogues/<slug>.md per dialogue (overwrites)
- kb/_inflight/<chunk_id>.json with proposals

Skips lessons already on disk if --skip-existing is passed.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"


def robust_loads(js_str: str):
    """Try json.loads; on common defects from LLM output, patch and retry."""
    last_err = None
    for _ in range(500):
        try:
            return json.loads(js_str)
        except json.JSONDecodeError as e:
            last_err = e
            pos = e.pos
            if e.msg.startswith("Expecting"):
                # Likely stray unescaped " inside a string value.
                back = pos - 1
                while back >= 0 and js_str[back] != '"':
                    back -= 1
                if back > 0 and js_str[back - 1] != '\\':
                    js_str = js_str[:back] + '\\"' + js_str[back + 1:]
                    continue
            if "Invalid control character" in e.msg:
                # Replace the raw control char with an escape.
                bad = js_str[pos]
                if bad == '\n':
                    js_str = js_str[:pos] + '\\n' + js_str[pos + 1:]
                elif bad == '\t':
                    js_str = js_str[:pos] + '\\t' + js_str[pos + 1:]
                elif bad == '\r':
                    js_str = js_str[:pos] + '\\r' + js_str[pos + 1:]
                else:
                    js_str = js_str[:pos] + js_str[pos + 1:]
                continue
            if "Unterminated string" in e.msg:
                js_str = js_str[:pos] + '"' + js_str[pos:]
                continue
            if "Invalid \\escape" in e.msg:
                # e.pos points at the char AFTER the backslash. Drop the backslash.
                js_str = js_str[:pos - 1] + js_str[pos:]
                continue
            raise
    if last_err:
        raise last_err
    return json.loads(js_str)


def extract_json(text: str):
    # First try fenced block
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try raw {...} starting at first {
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON found in output")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\" and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise ValueError("unterminated JSON in output")


def fmt_audio(audio_pattern: str, audio_root: str, lesson: int) -> str:
    # audio path is already substituted in the per-dialogue 'audio' field; keep as-is
    return audio_pattern


def yaml_list(items):
    if not items:
        return "[]"
    return "[" + ", ".join(items) + "]"


def render_dialogue(d: dict) -> str:
    fm_lines = [
        "---",
        f"title: {json.dumps(d.get('title', ''), ensure_ascii=False)}",
        "type: dialogue",
        f"slug: {d['slug']}",
        f"source: {d.get('source', d['slug'].rsplit('-l', 1)[0])}",
        f"lesson: {d['lesson']}",
        f"target_lang: {d['target_lang']}",
        f"base_lang: {d['base_lang']}",
        f"audio: {d.get('audio', '')}",
        f"themes: {yaml_list(d.get('themes', []))}",
        f"patterns: {yaml_list(d.get('patterns', []))}",
        f"vocab_introduced: {yaml_list(d.get('vocab_introduced', []))}",
        f"grammar: {yaml_list(d.get('grammar', []))}",
        f"cefr: {d['cefr']}",
        f"updated: {date.today().isoformat()}",
        "---",
        "",
    ]
    return "\n".join(fm_lines) + d.get("body", "").lstrip("\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    chunk_id = sys.argv[1]
    skip_existing = "--skip-existing" in sys.argv

    out_file = BASE / "_dispatch_outputs" / f"{chunk_id}.out.txt"
    if not out_file.exists():
        print(f"missing output: {out_file}", file=sys.stderr)
        sys.exit(2)

    text = out_file.read_text(encoding="utf-8", errors="replace")
    try:
        js_str = extract_json(text)
        data = robust_loads(js_str)
    except Exception as e:
        print(f"JSON parse failed for {chunk_id}: {e}", file=sys.stderr)
        # Save the raw extracted JSON attempt for debugging
        (BASE / "_dispatch_outputs" / f"{chunk_id}.parse-error.txt").write_text(
            str(e), encoding="utf-8"
        )
        sys.exit(3)

    source_slug = data.get("source_slug", "")
    dialogues = data.get("dialogues") or data.get("lessons") or []
    if isinstance(dialogues, dict):
        dialogues = list(dialogues.values())
    if not dialogues:
        # Fallback: collect any dict value at top-level that looks like a dialogue
        # (has slug + lesson + body). Mistral often emits a hybrid map where
        # vocab_proposals etc. sit beside dialogue-shaped entries.
        for v in (data.values() if isinstance(data, dict) else []):
            if isinstance(v, dict) and "slug" in v and "lesson" in v and "body" in v:
                dialogues.append(v)
    # Normalize body: some models emit body as a dict {Original: "...", Translation: "..."}
    # instead of a markdown string. Convert to markdown.
    for d in dialogues:
        if isinstance(d, dict) and isinstance(d.get("body"), dict):
            sections = []
            for sec_name, sec_content in d["body"].items():
                sections.append(f"## {sec_name}\n{sec_content}\n")
            d["body"] = "\n".join(sections)
    # Drop entries with empty body OR with [OCR unreadable] as the Original content.
    def usable(d):
        if not isinstance(d, dict):
            return False
        body = d.get("body", "")
        if not isinstance(body, str) or not body.strip():
            return False
        # Skip dialogues where Original is just [OCR unreadable] (no extracted content)
        m = re.search(r"^## Original\s*\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
        if m and m.group(1).strip().lower() in ("[ocr unreadable]", "", "[unreadable]"):
            return False
        return True
    dialogues = [d for d in dialogues if usable(d)]
    if not source_slug and dialogues:
        # Infer source_slug from first dialogue's slug
        s = dialogues[0].get("slug", "")
        source_slug = s.rsplit("-l", 1)[0] if "-l" in s else ""
    dialogues_dir = KB / "dialogues"
    dialogues_dir.mkdir(parents=True, exist_ok=True)

    written = []
    skipped = []
    for d in dialogues:
        d.setdefault("source", source_slug)
        slug = d.get("slug")
        if not slug:
            continue
        # Coerce chunk-id-prefixed slugs to the canonical source-prefixed form.
        # Pattern: "<chunk_id>-l<NNN>" where chunk_id isn't a real source slug.
        m = re.match(r"^(.+?)-l(\d+)$", slug)
        if m and source_slug and m.group(1) != source_slug:
            slug = f"{source_slug}-l{int(m.group(2)):03d}"
            d["slug"] = slug
            d["source"] = source_slug
        target = dialogues_dir / f"{slug}.md"
        if skip_existing and target.exists():
            skipped.append(slug)
            continue
        target.write_text(render_dialogue(d), encoding="utf-8")
        written.append(slug)

    # Write manifest
    inflight_dir = KB / "_inflight"
    inflight_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "group_id": chunk_id,
        "source_slug": source_slug,
        "lesson_range": data.get("lesson_range"),
        "lessons_written": [d["lesson"] for d in dialogues if d.get("slug") in written],
        "lessons_skipped": [d["lesson"] for d in dialogues if d.get("slug") in skipped],
        "vocab_proposals": data.get("vocab_proposals", []),
        "pattern_proposals": data.get("pattern_proposals", []),
        "grammar_proposals": data.get("grammar_proposals", []),
        "issues": data.get("issues", []),
    }
    (inflight_dir / f"{chunk_id}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"chunk={chunk_id} written={len(written)} skipped={len(skipped)} "
          f"vocab={len(manifest['vocab_proposals'])} "
          f"patterns={len(manifest['pattern_proposals'])} "
          f"grammar={len(manifest['grammar_proposals'])}")


if __name__ == "__main__":
    main()
