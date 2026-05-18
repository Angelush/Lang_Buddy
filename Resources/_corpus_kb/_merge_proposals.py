#!/usr/bin/env python3
"""Merge group-prefixed vocab/pattern/grammar proposals into canonical KB pages.

Reads all kb/_inflight/*.json, deduplicates by stripping the gX- prefix from slugs,
writes canonical kb/vocab/<slug>.md, kb/patterns/<slug>.md, kb/grammar/<slug>.md,
then rewrites the wikilinks in every dialogue file from [[vocab/gX-foo]] → [[vocab/foo]].
"""
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"


def strip_group_prefix(slug: str) -> str:
    return re.sub(r"^[a-z]+[0-9]+[a-z]?-", "", slug)


def slug_key(s: str) -> str:
    return strip_group_prefix(s).lower()


def yaml_list(items):
    if not items:
        return "[]"
    return "[" + ", ".join(json.dumps(i, ensure_ascii=False) if not isinstance(i, list)
                            else "[" + ", ".join(json.dumps(x, ensure_ascii=False) for x in i) + "]"
                            for i in items) + "]"


def render_vocab(slug, info, lessons_of_dialogues):
    fm = [
        "---",
        f"title: {json.dumps(info['lemma'], ensure_ascii=False)}",
        "type: vocab",
        f"slug: {slug}",
        f"lemma: {json.dumps(info['lemma'], ensure_ascii=False)}",
        f"target_lang: {info.get('target_lang', '')}",
        f"pos: {info.get('pos', 'phrase')}",
        f"gloss_es: {json.dumps(info.get('gloss', ''), ensure_ascii=False)}",
        f"frequency: {info['frequency']}",
        f"first_lesson: {yaml_list(info['first_lesson']) if info.get('first_lesson') else '[]'}",
        f"lessons: {info['lessons_yaml']}",
        f"register: {info.get('register', 'neutral')}",
        f"cefr: {info.get('cefr', 'A2')}",
        "stability: evergreen",
        f"updated: {date.today().isoformat()}",
        "---",
        "",
        f"**{info['lemma']}** — {info.get('gloss', '')}",
        "",
        "## Appears in",
    ]
    for src, lesson in info["lessons_pairs"]:
        d_slug = f"{src}-l{int(lesson):03d}"
        fm.append(f"- [[dialogues/{d_slug}]]")
    return "\n".join(fm) + "\n"


def render_pattern(slug, info):
    fm = [
        "---",
        f"title: {json.dumps(info.get('form') or slug, ensure_ascii=False)}",
        "type: pattern",
        f"slug: {slug}",
        f"target_lang: {info.get('target_lang', '')}",
        f"form: {json.dumps(info.get('form', ''), ensure_ascii=False)}",
        f"function: {json.dumps(info.get('function', ''), ensure_ascii=False)}",
        f"lessons: {info['lessons_yaml']}",
        f"cefr: {info.get('cefr', 'A2')}",
        "stability: evergreen",
        f"updated: {date.today().isoformat()}",
        "---",
        "",
        "## Form",
        info.get("form", ""),
        "",
        "## Function",
        info.get("function", ""),
        "",
        "## Examples",
    ]
    for src, lesson in info["lessons_pairs"]:
        d_slug = f"{src}-l{int(lesson):03d}"
        fm.append(f"- [[dialogues/{d_slug}]]")
    return "\n".join(fm) + "\n"


def render_grammar(slug, info):
    fm = [
        "---",
        f"title: {json.dumps(info.get('title') or slug, ensure_ascii=False)}",
        "type: grammar",
        f"slug: {slug}",
        f"target_lang: {info.get('target_lang', '')}",
        f"category: {info.get('category', 'syntax')}",
        f"lessons: {info['lessons_yaml']}",
        f"cefr: {info.get('cefr', 'B1')}",
        "stability: evergreen",
        f"updated: {date.today().isoformat()}",
        "---",
        "",
        "## Rule",
        info.get("rule", "(See lessons listed below.)"),
        "",
        "## Lessons that cover it",
    ]
    for src, lesson in info["lessons_pairs"]:
        d_slug = f"{src}-l{int(lesson):03d}"
        fm.append(f"- [[dialogues/{d_slug}]]")
    return "\n".join(fm) + "\n"


def collect():
    manifests = sorted((KB / "_inflight").glob("*.json"))
    vocab = defaultdict(lambda: {
        "lemma": "", "target_lang": "", "gloss": "",
        "frequency": 0, "lessons_pairs": [],
        "first_lesson": None,
    })
    patterns = defaultdict(lambda: {
        "form": "", "function": "", "target_lang": "",
        "lessons_pairs": [],
    })
    grammar = defaultdict(lambda: {
        "title": "", "category": "", "target_lang": "",
        "lessons_pairs": [],
    })

    for mpath in manifests:
        m = json.loads(mpath.read_text(encoding="utf-8"))
        src = m.get("source_slug", "")
        # vocab
        for v in m.get("vocab_proposals", []):
            slug = strip_group_prefix(v.get("group_slug") or v.get("slug", ""))
            if not slug:
                continue
            info = vocab[slug]
            if not info["lemma"]:
                info["lemma"] = v.get("lemma", slug)
                info["target_lang"] = v.get("target_lang", "")
                info["gloss"] = v.get("gloss", v.get("gloss_es", ""))
                info["pos"] = v.get("pos", "phrase")
                info["cefr"] = v.get("cefr", "")
            for lesson in v.get("lessons", []):
                try:
                    info["lessons_pairs"].append((src, int(lesson)))
                except (TypeError, ValueError):
                    # Slug-form lesson reference (e.g. "ingles-l120"); extract the int
                    mm = re.search(r"l(\d+)$", str(lesson))
                    if mm:
                        info["lessons_pairs"].append((src, int(mm.group(1))))
        for p in m.get("pattern_proposals", []):
            slug = strip_group_prefix(p.get("group_slug") or p.get("slug", ""))
            if not slug:
                continue
            info = patterns[slug]
            if not info["form"]:
                info["form"] = p.get("form", slug)
                info["function"] = p.get("function", "")
                info["target_lang"] = p.get("target_lang", "")
                info["cefr"] = p.get("cefr", "")
            for lesson in p.get("lessons", []):
                try:
                    info["lessons_pairs"].append((src, int(lesson)))
                except (TypeError, ValueError):
                    mm = re.search(r"l(\d+)$", str(lesson))
                    if mm:
                        info["lessons_pairs"].append((src, int(mm.group(1))))
        for g in m.get("grammar_proposals", []):
            slug = strip_group_prefix(g.get("group_slug") or g.get("slug", ""))
            if not slug:
                continue
            info = grammar[slug]
            if not info["title"]:
                info["title"] = g.get("title", slug)
                info["category"] = g.get("category", "syntax")
                info["target_lang"] = g.get("target_lang", "")
                info["cefr"] = g.get("cefr", "")
            for lesson in g.get("lessons", []):
                try:
                    info["lessons_pairs"].append((src, int(lesson)))
                except (TypeError, ValueError):
                    mm = re.search(r"l(\d+)$", str(lesson))
                    if mm:
                        info["lessons_pairs"].append((src, int(mm.group(1))))

    def cefr_for(source, lesson):
        if "perfeccionamiento" in source:
            return "B2" if lesson <= 25 else "C1"
        if lesson <= 25: return "A1"
        if lesson <= 50: return "A2"
        if lesson <= 75: return "B1"
        return "B2"

    # Dedup lessons_pairs and finalise
    def finalise(d):
        order = {"A1":1,"A2":2,"B1":3,"B2":4,"C1":5,"C2":6}
        for slug, info in d.items():
            uniq = sorted(set(info["lessons_pairs"]))
            info["lessons_pairs"] = uniq
            info["lessons_yaml"] = "[" + ", ".join(
                f'[{json.dumps(s, ensure_ascii=False)}, {l}]' for s, l in uniq
            ) + "]"
            info["frequency"] = len(uniq)
            info["first_lesson"] = [uniq[0][0], uniq[0][1]] if uniq else None
            # Derive CEFR from earliest lesson if not already set.
            if not info.get("cefr"):
                cefrs = [cefr_for(s, l) for s, l in uniq]
                info["cefr"] = min(cefrs, key=lambda c: order[c]) if cefrs else "A2"

    finalise(vocab)
    finalise(patterns)
    finalise(grammar)
    return vocab, patterns, grammar


def write_pages(vocab, patterns, grammar):
    (KB / "vocab").mkdir(exist_ok=True)
    (KB / "patterns").mkdir(exist_ok=True)
    (KB / "grammar").mkdir(exist_ok=True)
    n = 0
    for slug, info in vocab.items():
        (KB / "vocab" / f"{slug}.md").write_text(render_vocab(slug, info, None), encoding="utf-8")
        n += 1
    for slug, info in patterns.items():
        (KB / "patterns" / f"{slug}.md").write_text(render_pattern(slug, info), encoding="utf-8")
        n += 1
    for slug, info in grammar.items():
        (KB / "grammar" / f"{slug}.md").write_text(render_grammar(slug, info), encoding="utf-8")
        n += 1
    return n, len(vocab), len(patterns), len(grammar)


def rewrite_dialogue_links():
    """Strip gX- prefixes from wikilinks AND from frontmatter list fields in dialogues."""
    # Pattern matches things like fr1-foo, en2a-bar inside [[vocab/...]], [[patterns/...]], [[grammar/...]]
    link_re = re.compile(r"\[\[(vocab|patterns|grammar)/([a-z]+[0-9]+[a-z]?-)([^\]]+)\]\]")
    fm_field_re = re.compile(r"^(patterns|vocab_introduced|grammar): \[(.*?)\]$", re.MULTILINE)
    slug_in_list_re = re.compile(r"\b([a-z]+[0-9]+[a-z]?-)([a-z0-9_-]+)\b")
    count = 0
    for f in (KB / "dialogues").glob("*.md"):
        text = f.read_text(encoding="utf-8")
        new = link_re.sub(lambda m: f"[[{m.group(1)}/{m.group(3)}]]", text)
        # strip prefix in frontmatter lists too
        def strip_list(m):
            field, body = m.group(1), m.group(2)
            cleaned = slug_in_list_re.sub(lambda mm: mm.group(2), body)
            return f"{field}: [{cleaned}]"
        new = fm_field_re.sub(strip_list, new)
        if new != text:
            f.write_text(new, encoding="utf-8")
            count += 1
    return count


def main():
    vocab, patterns, grammar = collect()
    total, nv, np, ng = write_pages(vocab, patterns, grammar)
    rewritten = rewrite_dialogue_links()
    print(f"wrote {total} pages (vocab={nv}, patterns={np}, grammar={ng})")
    print(f"rewrote group prefixes in {rewritten} dialogue files")


if __name__ == "__main__":
    main()
