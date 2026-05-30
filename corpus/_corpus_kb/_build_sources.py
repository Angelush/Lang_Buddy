#!/usr/bin/env python3
"""Write kb/sources/<slug>.md for each Assimil book covered by dialogues/."""
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"


def parse_fm(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


META = {
    "el-nuevo-frances-sin-esfuerzo": {
        "title": "Assimil — El Nuevo Francés Sin Esfuerzo",
        "target_lang": "fr", "base_lang": "es",
        "year": 2002, "lesson_count": 99,
        "cefr_range": ["A1", "B2"],
        "audio_root": "Resources/Assimil - El Nuevo Francés sin Esfuerzo/Audio",
    },
    "ingles": {
        "title": "Assimil — Inglés (con desenvoltura)",
        "target_lang": "en", "base_lang": "es",
        "year": 2003, "lesson_count": 140,
        "cefr_range": ["A1", "B2"],
        "audio_root": "Resources/Assimil Inglés/Audio",
    },
    "ingles-perfeccionamiento": {
        "title": "Assimil — Inglés Perfeccionamiento",
        "target_lang": "en", "base_lang": "es",
        "year": 2008, "lesson_count": 70,
        "cefr_range": ["B2", "C1"],
        "audio_root": "Resources/Assimil - Ingles Perfeccionamiento/Audio",
    },
    "french-en-et-y-exos": {
        "title": "Assimil — Exercices en/y (extra)",
        "target_lang": "fr", "base_lang": "fr",
        "year": 2010, "lesson_count": 1,
        "cefr_range": ["A2", "B1"],
        "audio_root": "Resources/Assimil French (extras)",
    },
}


def main():
    dialogues = sorted((KB / "dialogues").glob("*.md"))
    by_src = defaultdict(list)
    for f in dialogues:
        fm = parse_fm(f.read_text(encoding="utf-8"))
        src = fm.get("source", "")
        lesson = int(fm.get("lesson", "0")) if fm.get("lesson", "").isdigit() else 0
        title = fm.get("title", "").strip('"')
        cefr = fm.get("cefr", "?")
        by_src[src].append((lesson, fm.get("slug", f.stem), title, cefr))

    out_dir = KB / "sources"
    out_dir.mkdir(exist_ok=True)
    for src, items in by_src.items():
        meta = META.get(src, {
            "title": src,
            "target_lang": "?", "base_lang": "?",
            "year": "?", "lesson_count": len(items),
            "cefr_range": ["A1", "C1"],
            "audio_root": f"Resources/{src}/Audio",
        })
        items.sort()
        fm = [
            "---",
            f"title: {meta['title']}",
            "type: source",
            f"slug: {src}",
            f"artifact_ref: _md_cache/assimil-{src}.pdf.md",
            "artifact_kind: external",
            f"target_lang: {meta['target_lang']}",
            f"base_lang: {meta['base_lang']}",
            f"year: {meta['year']}",
            "publisher: Assimil",
            f"lesson_count: {meta['lesson_count']}",
            f"cefr_range: [{meta['cefr_range'][0]}, {meta['cefr_range'][1]}]",
            f"audio_root: {meta['audio_root']}",
            f"updated: {date.today().isoformat()}",
            "---",
            "",
            f"## Summary",
            f"Assimil-method language-learning course. {meta['lesson_count']} lessons covering {meta['cefr_range'][0]} to {meta['cefr_range'][1]}.",
            "",
            "## Audio assets",
            f"Native-speaker MP3s under `{meta['audio_root']}/`.",
            "",
            f"## Lessons covered ({len(items)} of {meta['lesson_count']})",
        ]
        for lesson, slug, title, cefr in items:
            fm.append(f"- L{lesson:03d} [{cefr}] [[dialogues/{slug}]] — {title}")
        (out_dir / f"{src}.md").write_text("\n".join(fm) + "\n", encoding="utf-8")

    print(f"wrote {len(by_src)} source pages")


if __name__ == "__main__":
    main()
