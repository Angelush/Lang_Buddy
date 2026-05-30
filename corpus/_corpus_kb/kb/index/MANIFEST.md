# Tutor retrieval manifest

This directory + `../drills/` + `../refs/` is the runtime input for the
oral-practice tutor agent (Phase 1: generic chatbot like Claude.ai with TTS).
Markdown dialogue files in `../dialogues/` remain the source of record.

## Files

| File | Rows | Size | Purpose |
|---|---|---|---|
| `lessons.json` | 267 | 256 KB | Lesson catalog: cefr, themes, audio_path, audio_exists, gap_count, line_count |
| `vocab.json` | 169 | 49 KB | All canonical lemmas; `core: true` if frequency ≥ 2 |
| `patterns.json` | 81 | 18 KB | Recurring constructions |
| `grammar.json` | 49 | 14 KB | Grammar points with rule + common_errors + correct_policy |
| `themes.json` | 428 | 37 KB | theme → [lesson_ids] |
| `../drills/<id>.json` | 264 | ~1.7 MB total | Pincer drill packs (one per lesson) |
| `../refs/cefr_can_do.md` | — | 5 KB | CEFR can-do statements per level |
| `../refs/es_pitfalls_en.md` | — | 6 KB | Spanish-L1 → English-L2 error patterns |
| `../refs/es_pitfalls_fr.md` | — | 6 KB | Spanish-L1 → French-L2 error patterns |
| `../refs/freq_anchors.md` | — | 4 KB | Top 200 lemmas EN + FR (frequency anchors) |

## Loading recipe

**Claude.ai (200K context)** — load at session start:
- `lessons.json` (~65 K tokens)
- `themes.json` (~10 K tokens)
- `grammar.json` (~4 K tokens)
- `patterns.json` (~5 K tokens)
- `refs/*.md` (~5 K tokens)
- Total system context: ~90 K tokens. Fits comfortably.

**ChatGPT Plus (32K context)** — load only `lessons.json` summary fields (id, cefr, themes, audio_exists) ~30 KB, then fetch the drill on demand.

## Live-lesson flow

1. Agent loads indices + user profile (level, recent gaps, SRS state).
2. Agent picks a `lesson_id` matching CEFR window, novel theme, due vocab.
3. Agent fetches `../drills/<lesson_id>.json`. Each line has:
   - `target` — the actual dialogue line in the target language
   - `base` — the translation
   - `pronunciation` — Assimil phonetic guide (when present)
4. Agent reads `target` aloud, leaves `gap_candidates[k]` silent.
5. Learner produces the answer; agent validates against `lines[gap.line].target`.
6. After the dialogue, agent surfaces due vocab (`vocab.json` filtered by user theme + SRS state).
7. On error, agent consults `grammar.json[<slug>].common_errors` + `refs/es_pitfalls_*.md` for contrastive context.

## SRS attachment

`vocab.json` is keyed by stable lemma slug. SRS state should live in a separate
`srs_state.json` keyed by the same slugs:
```json
{ "chapeau": { "last_seen": "2026-05-18", "interval_days": 4, "ease": 2.5 } }
```

## Coverage gaps (acknowledged)

- Inglés lessons 109, 114–117, 125–131 missing (OCR too noisy)
- Ingles-perfeccionamiento lesson 5 missing
- Lessons 64–70 of perfeccionamiento have no audio file (book audio incomplete)
- 28 `[OCR unreadable]` placeholder dialogues removed in cleanup; their lesson_ids are de-listed from all indices
- 3 revision/grammar-only dialogues have no drill pack (`ingles-l021`, `ingles-l028`, `ingles-l035`)
