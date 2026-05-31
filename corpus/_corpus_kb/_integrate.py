#!/usr/bin/env python3
"""Normalize raw authored dialogues and integrate valid ones into kb/dialogues/.

Cleans common LLM-output noise (CLI retry notices, ```fences, thinking
preambles) by dropping everything before the first YAML '---' line, then
validates schema essentials before copying into the tracked KB.

Usage: _integrate.py [--write]   (omit --write for a dry run)
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / (sys.argv[sys.argv.index("--raw") + 1] if "--raw" in sys.argv else "_authored/raw")
DST = ROOT / "kb" / "dialogues"
WRITE = "--write" in sys.argv

REQUIRED_HEADINGS = ["## Dialogue", "## Translation", "## Notes",
                     "## Vocabulary highlights", "## Patterns", "## Agent cues"]


def clean(text: str) -> str:
    # Locate the YAML frontmatter start, tolerating leading noise that may be
    # glued onto the opening '---' line (CLI retry notices / thinking preambles).
    m = re.search(r"-{3}[ \t]*\n(?=title:|type:|slug:)", text)
    if m:
        body = text[m.start():]
    else:
        lines = text.splitlines()
        start = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
        if start is None:
            return ""
        body = "\n".join(lines[start:])
    body = body.strip()
    # Strip a wrapping ```markdown ... ``` fence if present.
    body = re.sub(r"^```[a-zA-Z]*\n", "", body)
    body = re.sub(r"\n```$", "", body)
    return body.strip() + "\n"


def validate(slug: str, text: str):
    issues = []
    if not text.startswith("---\n"):
        issues.append("no frontmatter")
        return issues
    fm = text.split("---", 2)[1]
    if f"slug: {slug}" not in fm:
        issues.append(f"slug mismatch (expected {slug})")
    if "origin: original" not in fm:
        issues.append("missing origin: original")
    if "cefr:" not in fm:
        issues.append("missing cefr")
    for h in REQUIRED_HEADINGS:
        if h not in text:
            issues.append(f"missing {h}")
    return issues


def main():
    DST.mkdir(parents=True, exist_ok=True)
    ok, bad = [], []
    for f in sorted(RAW.glob("*.md")):
        slug = f.stem
        if slug in ("dbg", "dbg2", "probe"):
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        if len(raw) < 800:
            bad.append((slug, ["empty/too short"]))
            continue
        text = clean(raw)
        issues = validate(slug, text)
        if issues:
            bad.append((slug, issues))
            continue
        ok.append(slug)
        if WRITE:
            (DST / f"{slug}.md").write_text(text, encoding="utf-8")
    print(f"{'WROTE' if WRITE else 'DRY-RUN'}  valid={len(ok)}  invalid={len(bad)}")
    for s in ok:
        print(f"  OK   {s}")
    for s, iss in bad:
        print(f"  BAD  {s}: {', '.join(iss)}")


if __name__ == "__main__":
    main()
