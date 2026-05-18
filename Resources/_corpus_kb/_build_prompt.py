#!/usr/bin/env python3
"""Build per-chunk extraction prompts for the Assimil corpus.

Two slicing strategies are supported:
  page    — slice by `## Page NNN` markers using pages_per_lesson ratio (default
            for noisy OCR like the Inglés book where lesson markers are unreliable).
  marker  — search the OCR for lesson markers (Leçon NN, Lesson NN, Lección NN);
            falls back to `page` if no markers found near the requested range.

Usage:
  _build_prompt.py [--strategy page|marker] <chunk_id> <book_md> <source_slug>
                   <target_lang> <base_lang> <audio_root> <audio_pattern>
                   <lesson_start> <lesson_end> <cefr> <total_pages> <total_lessons>

Writes _dispatch_prompts/<chunk_id>.prompt.txt.
"""
import argparse
import re
from pathlib import Path

BASE = Path(__file__).parent

SCHEMA = """
For each lesson in the requested range, emit a JSON object with these keys:
- slug: "<source_slug>-l<NNN>" (NNN zero-padded to 3 digits). CRITICAL: prefix is the SOURCE SLUG, not the chunk_id.
- lesson: integer
- title: lesson title in target language (best effort from OCR; "Leçon NN" / "Lesson NN" if untitled)
- target_lang, base_lang, audio: as passed in
- themes: short list of theme tags (max 4)
- patterns, vocab_introduced, grammar: lists of group-prefixed slugs (prefix = chunk_id)
- cefr: as passed in
- body: a markdown string with these exact `##` sections IN ORDER:
  - `## Original` (target lang, numbered lines, **Prononciation:** sub-block if present)
  - `## Translation` (base lang)
  - `## Modernized` (ONLY if obsolete tech in source; omit section otherwise)
  - `## Lesson notes` (numbered NOTES (1)(2)... VERBATIM, format `- **(N)** <text>`)
  - `## Exercises` (Ejercicio/Exercice + Corrigé verbatim; omit if absent)
  - `## Vocabulary highlights` (bullets `- **lemma** — gloss [[vocab/<group-prefixed-slug>]]`)
  - `## Patterns` (bullets with [[patterns/...]] links)
  - `## Agent cues` (2-4 sentences on Pincer gaps, prosody, register)
  - `## Audio` (audio path)

Top-level alongside `dialogues`:
- vocab_proposals: list of {group_slug, lemma, target_lang, gloss, lessons}
- pattern_proposals: list of {group_slug, form, function, lessons}
- grammar_proposals: list of {group_slug, title, category, lessons}

Output a single JSON object wrapped in ```json fences. Output `dialogues: [...]` as an ARRAY, not a dict. NO commentary outside the JSON.
"""

RULES = """
RULES:
1. `## Original` and `## Translation` MUST be VERBATIM from the OCR — do NOT modernize there. Preserve OCR artifacts.
2. Only add `## Modernized` if the lesson references obsolete tech (cassette/VCR/fax/video-rental/operator-call/answering-machine-tape/phone-book).
3. CEFR is MANDATORY in every dialogue. Use the cefr value passed in.
4. Vocab/pattern/grammar slugs MUST be prefixed with the chunk_id (e.g. "fr2a-bonjour").
5. The DIALOGUE slug uses the SOURCE SLUG prefix (e.g. "el-nuevo-frances-sin-esfuerzo-l029"), NOT the chunk_id.
6. If a lesson is too OCR-noisy, still emit the lesson object but put real content where readable; add it to top-level `issues` array if multiple sections are unreadable.
"""


def slice_by_page(text, lesson_start, lesson_end, total_pages, total_lessons,
                  pad_lessons=1):
    pages_per_lesson = total_pages / total_lessons
    page_start = max(1, int((lesson_start - 1 - pad_lessons) * pages_per_lesson))
    page_end = min(total_pages, int((lesson_end + pad_lessons) * pages_per_lesson) + 1)
    page_marks = [(m.start(), int(m.group(1)))
                  for m in re.finditer(r"^## Page (\d+)", text, re.MULTILINE)]
    page_marks.append((len(text), total_pages + 1))
    start_off, end_off = 0, len(text)
    for off, pg in page_marks:
        if pg <= page_start:
            start_off = off
        if pg > page_end:
            end_off = off
            break
    return start_off, end_off


def slice_by_marker(text, lesson_start, lesson_end, total_pages, total_lessons):
    WORDS_TO_NUM = {
        "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciséis": 16, "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
        "veinte": 20, "treinta": 30, "cuarenta": 40,
        "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
        "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18, "nineteenth": 19,
        "twentieth": 20, "thirtieth": 30, "fortieth": 40
    }

    patterns = [
        (r"^Le[çc]on\s+0*(\d+)", 1), (r"^LE[ÇC]ON\s+0*(\d+)", 1),
        (r"^Lesson\s+0*(\d+)", 1), (r"^LESSON\s+0*(\d+)", 1),
        (r"^Lecci[oó]n\s+0*(\d+)", 1), (r"^LECCI[OÓ]N\s+0*(\d+)", 1),
        (r"^(?:Lesson|FESSON|HESSON|ESSON|LESSDN)\s+0*(\d+)", 1),
        (r"^0*(\d+)(?:st|nd|rd|th)?\s+(?:Lesson|FESSON|HESSON|ESSON|LESSDN)", 1),
        (r"^\(0*(\d+)(?:st|nd|rd|th)?\)\s+(?:Lesson|FESSON|HESSON|ESSON|LESSDN)", 1),
        (r"^(?:Hundred|One\s+hundred)\s+and\s+(\w+)\s+.*?\s*0*(\d+)", 2),
        (r"^(?:Hundred|One\s+hundred)\s+and\s+(\w+)", 1),
        (r"^Lecci[oó]n\s+ciento\s+(\w+)", 1),
    ]
    occurrences = {}
    for pat, group_idx in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
            val = m.group(group_idx)
            try:
                if val.isdigit():
                    n = int(val)
                    if "hundred" in m.group(0).lower() or "ciento" in m.group(0).lower():
                        if n < 100: n += 100
                else:
                    n = WORDS_TO_NUM.get(val.lower())
                    if n is not None:
                        if "hundred" in m.group(0).lower() or "ciento" in m.group(0).lower():
                            n += 100
                    else:
                        continue
                
                if n > total_lessons + 10:
                    continue
            except (ValueError, IndexError):
                continue
            occurrences.setdefault(n, []).append(m.start())

    print(f"DEBUG: found markers for lessons: {sorted(occurrences.keys())}")
    for n in range(lesson_start, lesson_end + 3):
        if n in occurrences:
            print(f"DEBUG: Lesson {n} found at: {occurrences[n]}")

    has_start = (lesson_start in occurrences or
                 any(k for k in occurrences if lesson_start - 3 <= k <= lesson_start))
    has_end = (lesson_end in occurrences or
               any(k for k in occurrences if lesson_end <= k <= lesson_end + 3))
    if not (has_start and has_end):
        return slice_by_page(text, lesson_start, lesson_end, total_pages, total_lessons)

    start_off = 0
    if lesson_start in occurrences:
        # Use the first occurrence of the start lesson
        start_off = min(occurrences[lesson_start])
    else:
        cands = sorted(k for k in occurrences if k <= lesson_start)
        if cands:
            start_off = max(occurrences[cands[-1]])
    
    # Try to find an occurrence of lesson_start that is later if the first one is too early?
    # Actually, for Assimil, the English text is usually BEFORE the Spanish notes.
    # If there are multiple occurrences, we probably want the one that is part of the sequence.

    end_off = len(text)
    # Sort occurrences by position to find the one after start_off
    all_marks = []
    for n, offs in occurrences.items():
        for off in offs:
            all_marks.append((off, n))
    all_marks.sort()

    for off, n in all_marks:
        if off > start_off and (n == lesson_end + 1 or n == lesson_end + 2):
            print(f"DEBUG: Found end_off candidate: Lesson {n} at {off}")
            end_off = off
            break
    
    start_off = max(0, start_off - 3000)
    end_off = min(len(text), end_off + 3000)
    return start_off, end_off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", choices=["page", "marker"], default="page",
                    help="Slicing strategy. page=robust default. marker=use lesson markers (falls back to page).")
    ap.add_argument("chunk_id")
    ap.add_argument("book_md_path")
    ap.add_argument("source_slug")
    ap.add_argument("target_lang")
    ap.add_argument("base_lang")
    ap.add_argument("audio_root")
    ap.add_argument("audio_pattern")
    ap.add_argument("lesson_start", type=int)
    ap.add_argument("lesson_end", type=int)
    ap.add_argument("cefr")
    ap.add_argument("total_pages", type=int)
    ap.add_argument("total_lessons", type=int)
    args = ap.parse_args()

    text = Path(args.book_md_path).read_text(encoding="utf-8", errors="replace")

    if args.strategy == "marker":
        start_off, end_off = slice_by_marker(text, args.lesson_start, args.lesson_end,
                                              args.total_pages, args.total_lessons)
    else:
        start_off, end_off = slice_by_page(text, args.lesson_start, args.lesson_end,
                                            args.total_pages, args.total_lessons)

    slice_text = text[start_off:end_off]
    MAX_PROMPT_BYTES = 95_000
    if len(slice_text) > MAX_PROMPT_BYTES:
        slice_text = slice_text[:MAX_PROMPT_BYTES] + "\n\n[TRUNCATED]\n"

    prompt = f"""You are an expert language-learning corpus extractor for the Assimil method.

TASK: From the OCR'd source markdown below, extract structured dialogue pages for lessons {args.lesson_start} through {args.lesson_end} of "{args.source_slug}".

CONTEXT:
- Source book: {args.source_slug}
- Target language: {args.target_lang}
- Base language: {args.base_lang}
- Audio file pattern: "{args.audio_root}/{args.audio_pattern}" — substitute {{NN}} or {{NNN}} for the zero-padded lesson number
- CEFR level for this chunk: {args.cefr}
- Group id (prefix for vocab/pattern/grammar slugs): {args.chunk_id}

{SCHEMA}

{RULES}

=== OCR SOURCE SLICE (offsets {start_off}-{end_off}) ===
{slice_text}
=== END OCR SLICE ===

Emit ONLY the JSON block now.
"""

    out_dir = BASE / "_dispatch_prompts"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{args.chunk_id}.prompt.txt"
    out_path.write_text(prompt, encoding="utf-8")
    print(str(out_path), f"size={len(prompt)}")


if __name__ == "__main__":
    main()
