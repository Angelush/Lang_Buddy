# KB — AGENTS contract (original CEFR curriculum)

## Purpose

This `kb/` is a Karpathy-style wiki of **original** language-learning content
for an AI oral-practice tutor (English + French, base language Spanish). Every
dialogue, note, and exercise here is **authored from the CEFR objective spine**
(`refs/objectives.md`) — not extracted from any published course.

### Method, not text

The pedagogy is **Assimil-inspired** — short recurring dialogues, vocabulary
spiralled naturally across levels, learning by exposure rather than grammar
drills, paired with the **Pimsleur anticipation** principle (predict/produce the
next utterance) and **graduated interval recall** (a disguised SRS). Those are
uncopyrightable teaching *methods*, and we keep
and improve on them. We do **not** reproduce or paraphrase any course's
copyrighted *expression* (its dialogue text, translations, or footnotes). If you
are generating content and feel tempted to recall a specific published lesson,
stop — invent fresh characters and situations that hit the same CEFR objective.

### Improvements over the classic method
- **CEFR is the primary axis** (mandatory `cefr:` tag), not a book's lesson order.
- **Modern situations** by default (smartphones, streaming, apps, voicemail).
- **Machine-readable spiralling**: the `recycles:` field lists earlier items a
  lesson re-surfaces, so the SRS (`srs.md`) can target them.
- **Audio via host TTS** (phase 1) — no bundled audio files.

## Structure

```
kb/
├── AGENTS.md      # this contract
├── index.md       # learning-path views + cross-reference index (built)
├── log.md         # append-only operations log
├── dialogues/     # one page per original lesson (CEFR+theme keyed)
├── vocab/         # lemma pages (level, examples citing dialogues)
├── patterns/      # recurring constructions ("il y a", "going to V")
├── grammar/       # grammar points (tenses, agreement, etc.)
├── refs/          # objective spine + CEFR can-do + frequency + L1 pitfalls
└── index/         # tutor retrieval JSONs (built by _build_indices.py)
```

## Page format

Every page opens with YAML frontmatter.

### Dialogue page (`dialogues/<lang>-<cefr>-<theme>-<NN>.md`)

Slug example: `en-a1-greetings-01`, `fr-b1-voyage-02`. `<cefr>` lowercase.

```yaml
---
title: <original lesson title in the target language>
type: dialogue
slug: en-a1-greetings-01
target_lang: en | fr
base_lang: es
cefr: A1 | A2 | B1 | B2 | C1 | C2        # mandatory — primary axis
theme: <primary theme slug>
themes: [<theme>, ...]                    # primary + secondary tags
grammar: [<grammar-slug>, ...]            # grammar points exercised
patterns: [<pattern-slug>, ...]
vocab_introduced: [<vocab-slug>, ...]     # new lemmas first taught here
recycles: [<slug>, ...]                   # earlier vocab/patterns spiralled back
register: neutral | familiar | formal
origin: original                          # provenance guard — always "original"
updated: YYYY-MM-DD
---
```

Body sections (use these exact `##` headings, in order):
- **`## Dialogue`** — the original target-language dialogue, numbered lines.
  Short, natural, level-appropriate; recurring vocab; modern situations.
- **`## Pronunciation`** — IPA (or a clear respelling) for tricky lines/words.
  Authored for our lines; pronunciation guidance is the learner aid Assimil
  popularised — we keep the convention, our content.
- **`## Translation`** — a faithful Spanish translation of *our* dialogue.
- **`## Notes`** — the "teacher's voice": 2–6 short footnotes on grammar quirks,
  false friends (ES↔TL), register, culture, phonetics. Original wording.
- **`## Exercises`** — 3–5 original practice prompts + an answer key. Paste-ready
  for anticipation drills.
- **`## Vocabulary highlights`** — bullets, each linked `[[vocab/<slug>]]`.
- **`## Patterns`** — bullets, each linked `[[patterns/<slug>]]`.
- **`## Agent cues`** — meta-notes for the tutor: which lines are good
  **anticipation prompts** (gap candidates), correction strategy, prosody,
  register flags. 2–5 sentences.

### Vocab page (`vocab/<lemma-slug>.md`)

```yaml
---
title: <lemma in target language>
type: vocab
slug: <lemma-slug>                  # kebab-case lemma, e.g. il-y-a, look-forward-to
lemma: <surface form>
target_lang: fr | en
pos: noun | verb | adj | adv | phrase | idiom
gloss_es: <Spanish gloss>
gloss_en: <gloss if useful>
frequency: <count of dialogues it appears in>
first_lesson: <dialogue-slug>
lessons: [<dialogue-slug>, ...]
register: neutral | familiar | formal | slang | regional
cefr: A1 | A2 | B1 | B2 | C1 | C2    # level at which it becomes productive (mandatory)
stability: evergreen | evolving | volatile
updated: YYYY-MM-DD
---
```
Body: definition, 2–3 example sentences (each citing `[[dialogues/<slug>]]`),
false-friend notes, common ES-L1 learner errors.

### Pattern page (`patterns/<slug>.md`)

```yaml
---
title: <pattern name in target language>
type: pattern
slug: <pattern-slug>
target_lang: fr | en
form: <abstract form, e.g. "going to + V">
function: <semantic role>
lessons: [<dialogue-slug>, ...]
related_grammar: [<grammar-slug>, ...]
cefr: A1 | A2 | B1 | B2 | C1 | C2    # mandatory
stability: evergreen | evolving | volatile
updated: YYYY-MM-DD
---
```
Body: `## Form`, `## Function`, `## Examples` (cite `[[dialogues/...]]`),
`## Contrasts`, `## Anticipation hint`.

### Grammar page (`grammar/<slug>.md`)

```yaml
---
title: <grammar point>
type: grammar
slug: <grammar-slug>
target_lang: fr | en
category: tense | mood | agreement | syntax | phonology | orthography
lessons: [<dialogue-slug>, ...]
related_patterns: [<pattern-slug>, ...]
cefr: A1 | A2 | B1 | B2 | C1 | C2    # level at which it is required (mandatory)
stability: evergreen
updated: YYYY-MM-DD
---
```
Body: `## Rule`, `## Examples`, `## Common errors` (ES-L1 focus),
`## When the agent should correct vs. let it slide`.

## Wikilinks & stability

- Links: `[[dialogues/<slug>]]`, `[[vocab/<slug>]]`, `[[patterns/<slug>]]`,
  `[[grammar/<slug>]]`. Broken wikilinks are intentional TODO markers — the
  linter flags them; do not delete.
- `stability`: **evergreen** (core grammar/phonology/foundational lemmas),
  **evolving** (usage/idioms), **volatile** (situational, may date).

## Provenance guard

- Every dialogue carries `origin: original`.
- No `## Original`/`## Modernized` split exists anymore — content is original and
  modern by construction.
- The quarantined verbatim extraction (copyrighted) lives **outside the repo** in
  the gitignored `_verbatim_private/` and is never an input to generation.

## Workflows

### Author a new lesson
1. Pick a `(lang, level, theme)` from `refs/objectives.md`.
2. Write `dialogues/<lang>-<cefr>-<theme>-<NN>.md` to the dialogue schema above,
   within the level's CEFR band, recycling earlier anchors.
3. Add/update `vocab/`, `patterns/`, `grammar/` pages; cite the new dialogue.
4. Rebuild indices (`_build_indices.py`) and append `log.md`.

### Drive a Pimsleur session
1. Filter `index/lessons.json` by CEFR (learner level or +1 notch) and theme.
2. Use `## Agent cues` gap candidates; surface due `vocab/`/`patterns/` via SRS.

### Lint
```bash
python3 corpus/_corpus_kb/_lint.py   # broken-wikilink check
```

## Log operations
Append-only in `log.md`. Format: `## [YYYY-MM-DD] <op> | <summary>`.
Ops: `author`, `derive`, `index`, `lint`, `review`, `decision`, `migration`.

## When in doubt
- Update an existing page before creating a new one.
- Vocab slugs are the lemma in kebab-case.
- Cite every example sentence with `[[dialogues/<slug>]]`.
- Invent; never reproduce a published course's text.
- CEFR tag is mandatory on every page.
