#!/usr/bin/env python3
"""Split raw batch outputs into individual vocab/pattern pages, validate, write.

Reads _prose/raw/*.md (one file per dispatched batch), splits on the
`===FILE: <kind>/<slug>.md===` delimiters the model was told to emit, cleans
LLM noise, validates schema essentials, and writes valid pages into
kb/vocab/ and kb/patterns/. Cross-checks against _prose/manifest.json so missing
pages are reported.

Usage: _prose_integrate.py [--write]   (omit --write for a dry run)
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
KB = ROOT / "kb"
WRITE = "--write" in sys.argv


def _argval(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


RAW = ROOT / _argval("--raw", "_prose/raw")
MANIFEST = json.loads((ROOT / _argval("--manifest", "_prose/manifest.json")).read_text(encoding="utf-8"))

MARKER = re.compile(r"^===\s*FILE:\s*(vocab|patterns|grammar)/([a-z0-9-]+)\.md.*$", re.M)
REQUIRED = {
    "vocab": ["## Definition", "## Examples"],
    "patterns": ["## Form", "## Function", "## Examples"],
    "grammar": ["## Rule", "## Examples", "## Common errors"],
}


def clean(block: str) -> str:
    # drop anything before the first frontmatter '---'
    m = re.search(r"^---[ \t]*$", block, re.M)
    if not m:
        return ""
    body = block[m.start():].strip()
    body = re.sub(r"^```[a-zA-Z]*\n", "", body)
    body = re.sub(r"\n```\s*$", "", body)
    body = body.strip()
    # drop a trailing standalone '---' file-separator the model emitted between pages
    body = re.sub(r"\n-{3,}\s*$", "", body).strip()
    return body + "\n"


def fm_of(text):
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def validate(kind, slug, text):
    issues = []
    if not text.startswith("---"):
        return ["no frontmatter"]
    fm = fm_of(text)
    if f"slug: {slug}" not in fm:
        issues.append("slug mismatch")
    if f"type: {kind[:-1] if kind=='patterns' else kind}" not in fm:
        issues.append("type mismatch")
    if "cefr:" not in fm:
        issues.append("missing cefr")
    if "<FILL" in text:
        issues.append("unfilled <FILL> token")
    for h in REQUIRED[kind]:
        if h not in text:
            issues.append(f"missing {h}")
    return issues


def main():
    found = {}   # "kind/slug" -> text
    bad = []
    for f in sorted(RAW.glob("*.md")):
        raw = f.read_text(encoding="utf-8", errors="replace")
        marks = list(MARKER.finditer(raw))
        for i, mk in enumerate(marks):
            kind, slug = mk.group(1), mk.group(2)
            end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
            block = clean(raw[mk.end():end])
            key = f"{kind}/{slug}"
            issues = validate(kind, slug, block)
            if issues:
                bad.append((key, f.name, issues))
                continue
            found[key] = (kind, slug, block)

    wrote = 0
    if WRITE:
        for key, (kind, slug, text) in found.items():
            (KB / kind).mkdir(parents=True, exist_ok=True)
            (KB / kind / f"{slug}.md").write_text(text, encoding="utf-8")
            wrote += 1

    expected = set(MANIFEST.keys())
    got = set(found.keys())
    missing = sorted(expected - got)
    extra = sorted(got - expected)

    print(f"{'WROTE' if WRITE else 'DRY-RUN'}  valid={len(found)}  invalid={len(bad)}  "
          f"missing={len(missing)}  extra={len(extra)}  (expected {len(expected)})")
    for key, fn, iss in bad[:40]:
        print(f"  BAD  {key} [{fn}]: {', '.join(iss)}")
    if missing:
        print("  MISSING:", ", ".join(missing[:40]), ("…" if len(missing) > 40 else ""))
    if extra:
        print("  EXTRA:", ", ".join(extra[:20]))


if __name__ == "__main__":
    main()
