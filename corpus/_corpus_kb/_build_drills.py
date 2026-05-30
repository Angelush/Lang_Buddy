#!/usr/bin/env python3
"""Build Pincer drill packs from dialogue markdown.

For each dialogue, emit kb/drills/<lesson_id>.json with the dialogue cleaned to
a conversational form the tutor agent can drive directly — no OCR garbage, no
phonetic-block clutter, no exercise text. Just the lines, paired target↔base,
with gap candidates flagged.

A "gap candidate" is a target-language line that:
- comes after a question or trigger line whose answer is constrained, OR
- contains a vocab_introduced lemma the agent wants to test, OR
- is a repeated/predictable construction (idiom in 2+ adjacent lines)

The agent uses this file at runtime: read it, pick a gap, deliver the prior
line(s) aloud, wait for the learner, validate against expected_answer.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"


LINE_RE = re.compile(r"^\s*(\d+)\s*[\.—\-]?\s*[—\-]?\s*(\S.*?)\s*$", re.MULTILINE)


def parse_section(body: str, name: str) -> str:
    m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def split_dialogue_and_pronunciation(section: str) -> tuple[str, str]:
    """Inside `## Original`, the dialogue numbered lines come first, then a
    `**Prononciation:**` (FR) / `**PRONUNCIATION**` (EN) block with its own
    numbered phonetic lines. Split them so we don't confuse the phonetic guide
    with the target text."""
    m = re.search(r"\*\*(?:Pronon[cç]iation|PRONUNCIATION|Pronunciation)[:\s]*\*\*",
                  section, re.IGNORECASE)
    if m:
        return section[:m.start()].strip(), section[m.end():].strip()
    return section.strip(), ""


def parse_numbered_lines(text: str) -> dict[int, str]:
    """Return {line_num: text} from a section like '## Original'."""
    out = {}
    for line in text.split("\n"):
        m = LINE_RE.match(line)
        if m:
            try:
                n = int(m.group(1))
            except ValueError:
                continue
            out[n] = m.group(2).strip()
    return out


def strip_footnote_marks(s: str) -> str:
    """Remove '(N)' footnote references that pollute target text."""
    return re.sub(r"\s*\(\d+\)\s*", " ", s).strip()


def is_question(line: str) -> bool:
    return "?" in line or line.startswith(("Est-ce", "Qu'", "Où", "Comment", "Pourquoi",
                                            "Quand", "Combien", "Quel", "Qui", "Quoi",
                                            "Do ", "Does ", "Did ", "Is ", "Are ",
                                            "Was ", "Were ", "Will ", "Can ", "Could ",
                                            "Should ", "Would ", "Have ", "Has ", "What",
                                            "Where", "Why", "When", "How", "Who"))


def gap_candidates(target_lines: dict[int, str],
                   vocab_introduced: list[str]) -> list[dict]:
    """Identify which lines are good Pincer gap candidates.

    A line is a candidate if:
    1. It immediately follows a question line (predictable answer pattern)
    2. It contains one of the lesson's vocab_introduced lemmas
    3. It's a short response (≤8 words) following another line
    """
    candidates = []
    sorted_nums = sorted(target_lines)
    vocab_set = {v.replace("_", " ").lower() for v in vocab_introduced if "-" in v}
    # Also handle bare slugs
    vocab_set |= {v.lower() for v in vocab_introduced}
    for i, n in enumerate(sorted_nums):
        line = target_lines[n]
        reasons = []
        if i > 0 and is_question(target_lines[sorted_nums[i - 1]]):
            reasons.append("answer_to_question")
        words = line.split()
        if i > 0 and len(words) <= 8:
            reasons.append("short_response")
        # Vocab match
        line_lower = line.lower()
        for v in vocab_set:
            slug_root = v.split("-")[-1] if "-" in v else v  # last token of slug
            if slug_root in line_lower:
                reasons.append(f"vocab:{slug_root}")
                break
        if reasons:
            candidates.append({
                "line": n,
                "target": line,
                "reasons": reasons,
            })
    return candidates


def build_one(f: Path) -> dict | None:
    text = f.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return None
    fm_raw = fm_match.group(1)
    fm = {}
    for line in fm_raw.split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    body = text[fm_match.end():]

    original_full = parse_section(body, "Original")
    translation = parse_section(body, "Translation")
    if not original_full.strip() or original_full.strip().lower() in ("[ocr unreadable]", ""):
        return None

    original, pronunciation = split_dialogue_and_pronunciation(original_full)
    target_lines = parse_numbered_lines(original)
    base_lines = parse_numbered_lines(translation)
    pron_lines = parse_numbered_lines(pronunciation)

    # Pair up target↔base by line number; surface pronunciation separately.
    pairs = []
    all_nums = sorted(set(target_lines) | set(base_lines))
    for n in all_nums:
        target = strip_footnote_marks(target_lines.get(n, ""))
        base = base_lines.get(n, "")
        if not target and not base:
            continue
        entry = {"line": n, "target": target, "base": base}
        if n in pron_lines:
            entry["pronunciation"] = pron_lines[n]
        pairs.append(entry)

    # Parse vocab_introduced from frontmatter list
    vi_raw = fm.get("vocab_introduced", "[]")
    vi = [x.strip().strip('"').strip("'") for x in vi_raw.strip("[]").split(",") if x.strip()]

    gaps = gap_candidates(target_lines, vi)

    # Audio + meta
    drill = {
        "lesson_id": fm.get("slug", f.stem),
        "source": fm.get("source", ""),
        "lesson": int(fm.get("lesson", "0")) if fm.get("lesson", "0").isdigit() else 0,
        "title": fm.get("title", "").strip('"'),
        "target_lang": fm.get("target_lang", ""),
        "base_lang": fm.get("base_lang", ""),
        "cefr": fm.get("cefr", ""),
        "audio": fm.get("audio", "").strip('"'),
        "themes": [x.strip().strip('"').strip("'") for x in fm.get("themes", "[]").strip("[]").split(",") if x.strip()],
        "lines": pairs,
        "gap_candidates": gaps,
        "vocab_introduced": vi,
    }
    return drill


def main():
    out_dir = KB / "drills"
    out_dir.mkdir(exist_ok=True)
    written = 0
    skipped = 0
    total_gap_candidates = 0
    for f in sorted((KB / "dialogues").glob("*.md")):
        drill = build_one(f)
        if not drill:
            skipped += 1
            continue
        (out_dir / f"{drill['lesson_id']}.json").write_text(
            json.dumps(drill, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        written += 1
        total_gap_candidates += len(drill["gap_candidates"])
    print(f"wrote {written} drill packs, skipped {skipped}")
    print(f"total gap candidates: {total_gap_candidates} "
          f"(avg {total_gap_candidates/max(1,written):.1f} per lesson)")
    # Sum size
    total = sum(p.stat().st_size for p in out_dir.glob("*.json"))
    print(f"total drills dir: {total:,} bytes ({total/1024:.1f} KB)")


if __name__ == "__main__":
    main()
