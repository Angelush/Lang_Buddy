#!/usr/bin/env python3
"""Build tutor retrieval indices from the original dialogue frontmatter.

Outputs to kb/index/:
  lessons.json   — per-dialogue catalog (filter by cefr / theme / lang)
  themes.json    — theme -> [dialogue slugs]
  vocab.json     — vocab slug -> {cefr, lessons[]}  (introduced/recycled)
  patterns.json  — pattern slug -> {cefr, lessons[]}
  grammar.json   — grammar slug -> {cefr, lessons[]}
  MANIFEST.md    — how the tutor uses these

Deterministic; safe to re-run. Frontmatter uses inline [a, b] lists.
"""
import json
import re
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent
DLG = ROOT / "kb" / "dialogues"
IDX = ROOT / "kb" / "index"
IDX.mkdir(parents=True, exist_ok=True)

SCALAR = ["title", "slug", "target_lang", "base_lang", "cefr", "theme", "register", "origin"]
LISTS = ["themes", "grammar", "patterns", "vocab_introduced", "recycles"]


def parse_fm(text):
    fm = text.split("---", 2)[1]
    d = {}
    for k in SCALAR:
        m = re.search(rf"(?m)^{k}:\s*(.+?)\s*$", fm)
        if m:
            d[k] = m.group(1).strip().strip('"')
    for k in LISTS:
        m = re.search(rf"(?m)^{k}:\s*\[(.*?)\]\s*$", fm)
        d[k] = [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []
    return d


lessons = []
themes = defaultdict(list)
vocab = defaultdict(lambda: {"cefr": None, "lessons": []})
patterns = defaultdict(lambda: {"cefr": None, "lessons": []})
grammar = defaultdict(lambda: {"cefr": None, "lessons": []})
CEFR_ORDER = {c: i for i, c in enumerate(["A1", "A2", "B1", "B2", "C1", "C2"])}


def note(bucket, slug, lesson_slug, cefr):
    e = bucket[slug]
    if lesson_slug not in e["lessons"]:
        e["lessons"].append(lesson_slug)
    if e["cefr"] is None or CEFR_ORDER.get(cefr, 9) < CEFR_ORDER.get(e["cefr"], 9):
        e["cefr"] = cefr  # earliest (lowest) level it appears


WIKILINK = re.compile(r"\[\[(vocab|patterns|grammar)/([a-z0-9-]+)\]\]")

for f in sorted(DLG.glob("*.md")):
    raw = f.read_text(encoding="utf-8")
    d = parse_fm(raw)
    slug, cefr = d.get("slug", f.stem), d.get("cefr")
    lessons.append({
        "slug": slug, "title": d.get("title"), "cefr": cefr,
        "target_lang": d.get("target_lang"), "theme": d.get("theme"),
        "themes": d["themes"], "grammar": d["grammar"], "patterns": d["patterns"],
        "vocab_introduced": d["vocab_introduced"], "register": d.get("register"),
    })
    for t in set(d["themes"] + ([d["theme"]] if d.get("theme") else [])):
        if slug not in themes[t]:
            themes[t].append(slug)
    for v in d["vocab_introduced"] + d["recycles"]:
        note(vocab, v, slug, cefr)
    for p in d["patterns"]:
        note(patterns, p, slug, cefr)
    for g in d["grammar"]:
        note(grammar, g, slug, cefr)
    # also index items referenced as body wikilinks (keeps index ⊇ prose pages)
    for kind, tgt in WIKILINK.findall(raw):
        note({"vocab": vocab, "patterns": patterns, "grammar": grammar}[kind], tgt, slug, cefr)

# Flag whether a deep prose page exists for each item (drives the optional layer).
for bucket, kind in ((vocab, "vocab"), (patterns, "patterns"), (grammar, "grammar")):
    for slug, e in bucket.items():
        e["page"] = (ROOT / "kb" / kind / f"{slug}.md").exists()

lessons.sort(key=lambda x: (x["target_lang"] or "", CEFR_ORDER.get(x["cefr"], 9), x["slug"]))
(IDX / "lessons.json").write_text(json.dumps(lessons, ensure_ascii=False, indent=1), encoding="utf-8")
(IDX / "themes.json").write_text(json.dumps(dict(sorted(themes.items())), ensure_ascii=False, indent=1), encoding="utf-8")
(IDX / "vocab.json").write_text(json.dumps(dict(sorted(vocab.items())), ensure_ascii=False, indent=1), encoding="utf-8")
(IDX / "patterns.json").write_text(json.dumps(dict(sorted(patterns.items())), ensure_ascii=False, indent=1), encoding="utf-8")
(IDX / "grammar.json").write_text(json.dumps(dict(sorted(grammar.items())), ensure_ascii=False, indent=1), encoding="utf-8")

(IDX / "MANIFEST.md").write_text(
    "# Tutor retrieval indices\n\n"
    "Built by `_build_index_new.py` from `kb/dialogues/*.md` frontmatter.\n\n"
    "- **lessons.json** — dialogue catalog. Filter by `cefr` (learner level or +1 "
    "notch) and `theme`; fetch the matching `kb/dialogues/<slug>.md` for full text "
    "and `## Agent cues` gap candidates.\n"
    "- **themes.json** — theme → dialogue slugs.\n"
    "- **vocab.json / patterns.json / grammar.json** — item slug → {cefr, lessons[], page}. "
    "The SRS (`srs.md`) sources candidate items here, level-capped; each points back "
    "to the dialogues that teach it. `page: true` means a deep prose page exists under "
    "`kb/vocab|patterns|grammar/` (the optional reference layer the tutor can surface).\n",
    encoding="utf-8")

print(f"lessons={len(lessons)} themes={len(themes)} vocab={len(vocab)} patterns={len(patterns)} grammar={len(grammar)}")
