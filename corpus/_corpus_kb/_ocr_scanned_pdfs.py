#!/usr/bin/env python3
"""OCR the scanned Assimil PDFs into the _md_cache/ as plain-text markdown.

Uses system tesseract + pdftoppm; reads .traineddata from ~/.local/share/tessdata.
Writes one big .md per PDF with `## Page NNN` separators. Idempotent at the
PDF level (skips a PDF if its .md already has substantial content).

Concurrency: per-page workers per book; books processed sequentially so disk I/O
and tesseract memory stay bounded.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/angelus/MEGA/IA/Language learning/Resources/_corpus_kb")
STAGE = ROOT / "_pdf_staging"
OUT = ROOT / "_md_cache"
TESSDATA = Path.home() / ".local" / "share" / "tessdata"

# (staged_pdf_filename, tesseract_langs, source_slug)
BOOKS = [
    ("assimil-el-nuevo-frances-sin-esfuerzo.pdf", "fra+spa", "el-nuevo-frances-sin-esfuerzo"),
    ("assimil-ingles.pdf",                        "eng+spa", "ingles"),
    ("assimil-ingles-perfeccionamiento.pdf",      "eng+spa", "ingles-perfeccionamiento"),
]

DPI = 300
PSM = "3"      # auto layout without OSD — faster than PSM 1, handles Assimil columns fine
WORKERS = 2    # 2 workers × OMP_NUM_THREADS=2 = 4 cores (matches `nproc` on this host)
THREADS_PER_WORKER = "2"


def ocr_one_page(png: Path, langs: str) -> tuple[int, str]:
    page_num = int(re.search(r"-(\d+)\.png$", png.name).group(1))
    env = os.environ.copy()
    env["TESSDATA_PREFIX"] = str(TESSDATA)
    env["OMP_THREAD_LIMIT"] = THREADS_PER_WORKER
    env["OMP_NUM_THREADS"] = THREADS_PER_WORKER
    try:
        result = subprocess.run(
            ["tesseract", str(png), "-", "-l", langs, "--psm", PSM, "--oem", "1"],
            env=env,
            check=True,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return page_num, result.stdout
    except subprocess.CalledProcessError as e:
        return page_num, f"<OCR_FAIL: {e.stderr.strip()}>"
    except subprocess.TimeoutExpired:
        return page_num, "<OCR_TIMEOUT>"


def process_book(pdf_filename: str, langs: str, source_slug: str) -> None:
    pdf = STAGE / pdf_filename
    out_md = OUT / f"{pdf.stem}.pdf.md"

    if not pdf.exists():
        print(f"[skip] {pdf_filename}: missing", file=sys.stderr)
        return

    # Skip if already OCR'd substantially
    if out_md.exists() and out_md.stat().st_size > 50_000:
        print(f"[skip] {pdf_filename}: {out_md.name} already has content ({out_md.stat().st_size} bytes)")
        return

    print(f"[start] {pdf_filename} (langs={langs})", flush=True)
    with tempfile.TemporaryDirectory(prefix="ocr_") as tmp:
        tmp_p = Path(tmp)
        # Rasterize PDF -> page-001.png, page-002.png, ...
        subprocess.run(
            ["pdftoppm", "-r", str(DPI), "-png", str(pdf), str(tmp_p / "page")],
            check=True,
        )
        pages = sorted(tmp_p.glob("page-*.png"))
        print(f"[rasterized] {pdf_filename}: {len(pages)} pages", flush=True)

        pages_text: dict[int, str] = {}
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futs = {pool.submit(ocr_one_page, p, langs): p for p in pages}
            done = 0
            for fut in as_completed(futs):
                page_num, txt = fut.result()
                pages_text[page_num] = txt
                done += 1
                if done % 20 == 0 or done == len(pages):
                    print(f"  [{pdf_filename}] OCR {done}/{len(pages)}", flush=True)

        # Assemble in page order
        lines: list[str] = []
        for n in sorted(pages_text):
            lines.append(f"\n\n## Page {n:03d}\n\n")
            lines.append(pages_text[n].strip())
        body = "".join(lines).strip() + "\n"

    frontmatter = (
        "---\n"
        f"source_file: {pdf_filename}\n"
        f"source_slug: {source_slug}\n"
        f"converted_at: {datetime.now(timezone.utc).date().isoformat()}\n"
        "converter: tesseract-5.5+pdftoppm\n"
        f"ocr_langs: {langs}\n"
        f"ocr_dpi: {DPI}\n"
        f"ocr_psm: {PSM}\n"
        "---\n\n"
    )
    out_md.write_text(frontmatter + body, encoding="utf-8")
    print(f"[done] {pdf_filename} -> {out_md.name} ({out_md.stat().st_size} bytes)", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not TESSDATA.exists():
        print(f"error: tessdata dir missing: {TESSDATA}", file=sys.stderr)
        return 2
    for fn, langs, slug in BOOKS:
        process_book(fn, langs, slug)
    print("[all done]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
