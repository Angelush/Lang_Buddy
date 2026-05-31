# KB index — original CEFR curriculum

Original, CEFR-graded language-learning content for the oral-practice tutor.
Authored from `refs/objectives.md` (Assimil-inspired method, original text). See
`AGENTS.md` for the schema and the provenance guard.

## How the tutor uses this

1. Read `refs/objectives.md` (what each level teaches) and `refs/cefr_can_do.md`.
2. Filter `index/lessons.json` by `cefr` (learner level or +1 notch) and `theme`.
3. Open the chosen `dialogues/<slug>.md` — use `## Dialogue` + `## Agent cues`
   (anticipation prompts), `## Notes` for "why" questions, `## Exercises` for drills.
4. Source SRS items from `index/{vocab,patterns,grammar}.json` (level-capped); each
   slug links back to the dialogues that teach it.

## Coverage (full theme inventory from `objectives.md`)

Dialogues per level (EN / FR mirror each other):

| level | A1 | A2 | B1 | B2 | C1 | C2 |
|-------|----|----|----|----|----|----|
| EN | 6 | 6 | 5 | 5 | 5 | 4 |
| FR | 6 | 6 | 5 | 5 | 5 | 4 |

**62 dialogues** (31 EN / 31 FR), all `origin: original`, all CEFR-tagged.
Deep layer: **517 vocab / 215 patterns / 128 grammar** pages — every index item
resolves to a page; 0 broken wikilinks.

## Layout

- `dialogues/` — the lessons (CEFR+theme keyed).
- `index/` — retrieval JSONs (`lessons`, `themes`, `vocab`, `patterns`, `grammar`) + `MANIFEST.md`.
- `refs/` — `objectives.md` (spine), `cefr_can_do.md`, `freq_anchors.md`, `es_pitfalls_{en,fr}.md`.
- `vocab/` `patterns/` `grammar/` — deep prose pages (populated; every index
  item resolves to a page).

## Next passes

- Generate anticipation `drills/` packs from the `## Agent cues` of each dialogue.
- Add a 2nd lesson per theme (`-02`) where a level needs more practice volume.
