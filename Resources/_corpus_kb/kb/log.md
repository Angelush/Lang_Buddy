# KB — Log

_Append-only chronological log of KB operations._
_Format: `## [YYYY-MM-DD] <op> | <one-line summary>`. Operations: `ingest`, `lint`, `decision`, `session`, `migration`, `query`._

---

## [2026-05-17] migration | KB scaffolded by corpus-indexer from 5 Assimil archives at Resources/. Schema adapted for oral-practice agent (dialogues/vocab/patterns/grammar/sources).
## [2026-05-17] decision | audio not transcribed — PDF dialogue text is authoritative, MP3 paths are referenced from dialogue pages for runtime playback by the agent.
## [2026-05-17] decision | modernization rule: original/translation sections verbatim, modernized rewrites only in derived sections (see AGENTS.md).
## [2026-05-17] decision | sources skipped from text extraction: "Assimil Le Francais En Pratique" (audio-only, no PDF), "Assimil French" .doc transcripts (no libreoffice available to convert). Both flagged for follow-up.
## [2026-05-17] ingest | canary | added french-en-et-y-exos: 1 source, 1 grammar, 2 patterns
## [2026-05-18] session | PAUSED — Sonnet Pro quota exhausted mid-dispatch (resets 05:20 Europe/Madrid). 1 group complete (fr1, 25 lessons), ~10 partial. See _RESUME_HERE.md.
lun 18 may 2026 09:52:46 CEST
## [2026-05-18] ingest+merge+lint | Extracted 283 dialogues across 4 books via parallel Gemini+Vibe dispatch. 140 vocab, 68 pattern, 46 grammar canonical pages. 8 source pages. Index rebuilt with CEFR groupings. 1684 broken wikilinks are intentional TODO markers per AGENTS.md (vocab mentioned in dialogues but not promoted).

## [2026-05-18] complete | Corpus extraction pipeline run end-to-end. 281 dialogues (FR 99 / EN 182), 140 vocab / 68 pattern / 46 grammar canonical pages, all CEFR-tagged, 11 modernized for obsolete tech. Parallel Gemini-flash + Vibe/Mistral dispatch via free-tier CLI APIs (no Pro Agent fan-out). Coverage gaps: Inglés 109-118+125-140 (~24 lessons), Perfeccionamiento 43-70 region (~25 lessons) — OCR slices too noisy for clean extraction. See `_RESUME_HERE.md`.

## [2026-05-18] phase-a+b+c | Fixed 2 fabrications (l005, l085), 14 slug mismatches, 251 blank cefr fields. Built tutor JSON indices (kb/index/*) and Pincer drill packs (kb/drills/*). Added complementary refs (cefr_can_do, es_pitfalls_en/fr, freq_anchors). Two Sonnet read-only audits, second caught drill-builder bug (pronunciation in target field), fixed. Coverage: 99 FR + 127 EN + 69 EN-Perf = 295 dialogues all CEFR-tagged. Gaps: ingles l109/114-117/125-131; enp-l005; enp-l64-70 missing audio.
