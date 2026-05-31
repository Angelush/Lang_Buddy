#!/usr/bin/env python3
"""Custom KB lint for the language-learning schema.

The bundled `Session_template/scripts/kb_lint.py` only scans concepts/sources/people/orgs.
Our LL schema uses dialogues/vocab/patterns/grammar/sources, so we use this instead.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).parent
KB = BASE / "kb"

WIKILINK_RE = re.compile(r"\[\[([^\]]+?)\]\]")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
CATEGORIES = ["dialogues", "vocab", "patterns", "grammar", "sources", "people", "orgs"]


def main():
    targets = {}
    inbound = defaultdict(int)
    pages = {}
    for cat in CATEGORIES:
        d = KB / cat
        if not d.is_dir():
            continue
        for f in d.glob("*.md"):
            slug = f.stem
            targets[f"{cat}/{slug}"] = f
            targets[slug] = f
            pages[(cat, slug)] = f.read_text(encoding="utf-8")

    # Scan all wikilinks
    broken = []
    for (cat, slug), text in pages.items():
        body = HTML_COMMENT_RE.sub("", text)
        for link in WIKILINK_RE.findall(body):
            base = link.split("|", 1)[0].split("#", 1)[0].strip()
            if base in targets:
                inbound[base] += 1
            else:
                broken.append((f"{cat}/{slug}", base))

    # Root index/log
    for root_name in ("index.md", "log.md"):
        p = KB / root_name
        if p.is_file():
            body = HTML_COMMENT_RE.sub("", p.read_text(encoding="utf-8"))
            for link in WIKILINK_RE.findall(body):
                base = link.split("|", 1)[0].split("#", 1)[0].strip()
                if base in targets:
                    inbound[base] += 1
                else:
                    broken.append((root_name, base))

    # The tutor retrieves via the index catalog (kb/index/*.json), not graph
    # traversal — so a page listed there IS reachable. Treat index presence as a
    # reference; a true orphan is neither wikilinked nor in the catalog.
    import json
    indexed = set()
    for cat in ("vocab", "patterns", "grammar"):
        p = KB / "index" / f"{cat}.json"
        if p.is_file():
            indexed.update(f"{cat}/{k}" for k in json.loads(p.read_text(encoding="utf-8")))

    orphans = []
    for (cat, slug), text in pages.items():
        if cat in ("dialogues",):
            continue  # dialogues are leaf documents
        if inbound[f"{cat}/{slug}"] == 0 and inbound[slug] == 0 and f"{cat}/{slug}" not in indexed:
            orphans.append(f"{cat}/{slug}")

    counts = {cat: sum(1 for (c, _) in pages if c == cat) for cat in CATEGORIES}

    print(f"== KB Lint ({KB}) ==")
    print(f"pages by category: {counts}")
    print(f"total pages: {sum(counts.values())}")
    print(f"broken wikilinks: {len(broken)}")
    print(f"orphans (no inbound link): {len(orphans)}")

    if broken:
        print("\nBroken sample (first 10):")
        for o, t in broken[:10]:
            print(f"  {o} → {t}")

    return 0 if not broken else 1


if __name__ == "__main__":
    sys.exit(main())
