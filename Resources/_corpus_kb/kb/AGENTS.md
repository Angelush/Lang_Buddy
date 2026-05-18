# KB — AGENTS contract

## Purpose

This `kb/` is a Karpathy-style wiki of the **Assimil corpus** (English + French language-learning courses), curated as direct input to an AI agent that practices **oral expression** with the user. It was scaffolded by the `corpus-indexer` skill from documents in `Resources/` (markdown cache at `_md_cache/`).

The agent's pedagogy combines:
- **Assimil method** — short recurring dialogues, vocabulary surfaced naturally across lessons.
- **Pincer method** — the agent drives the dialogue and leaves silent gaps for the learner to predict the next utterance.
- **SRS** — vocabulary and patterns resurface right before they would be forgotten, always embedded in live conversation.

Sources here are **books and audio**, not project source files. The schema is therefore adapted: pages describe dialogues, vocabulary lemmas, recurring constructions, and grammar points rather than generic concepts. Maintenance afterwards is handled by the `kb-curator` skill (Session_template plugin) — the frontmatter and wikilink conventions are deliberately compatible.

## Structure

```
kb/
├── AGENTS.md      # this contract
├── index.md       # learning-path views + cross-reference index
├── log.md         # append-only operations log
├── dialogues/     # one page per Assimil lesson (text + audio path)
├── vocab/         # lemma pages (frequency, lessons, example contexts)
├── patterns/      # recurring constructions ("il y a", "going to V")
├── grammar/       # grammar points (verb tenses, agreement, etc.)
├── sources/       # one page per Assimil course / artifact
├── people/        # optional: notable authors cited
└── orgs/          # optional: publisher (Assimil) or related entities
```

## Page format

Every page starts with a YAML frontmatter block. Page types and their bodies:

### Dialogue page (`dialogues/<source-slug>-l<NNN>.md`)

```yaml
---
title: <Lesson title in target language>
type: dialogue
slug: <source-slug>-l<NNN>             # e.g. en-frances-l017
source: <source-slug>                   # which Assimil book
lesson: 17                              # zero-padded
target_lang: fr | en
base_lang: es | fr | en                 # learner's reference language
audio: <relative-path-to-mp3>           # path under Resources/
themes: [travel, food, ...]             # short tags
patterns: [<pattern-slug>, ...]         # patterns covered
vocab_introduced: [<vocab-slug>, ...]   # new lemmas in this lesson
grammar: [<grammar-slug>, ...]
cefr: A1 | A2 | B1 | B2 | C1 | C2       # CEFR level (mandatory — Common European Framework)
updated: YYYY-MM-DD
---
```

Body sections (use these exact `##` headings in this order):
- **`## Original`** — the dialogue verbatim in the target language. Preserve faithfully. Include the Assimil **Prononciation** lines as a `**Prononciation:**` sub-block. This is the **fidelity reference** — never modernize here.
- **`## Translation`** — the dialogue in the learner's base language. Preserve faithfully.
- **`## Modernized`** — *only* when the original references obsolete tech/culture (cassette player, fax, VCR, video rental store, operator-assisted call, etc.). A modernized rewrite that preserves the linguistic pedagogy but updates the situation. Include a one-line `Modernization note:` explaining the substitution. If the lesson is timeless, omit this section.
- **`## Lesson notes`** — the Assimil **NOTES (1) (2) (3)...** footnotes verbatim. These are the canonical pedagogical "why" content for the lesson (grammar quirks, false friends, register, cultural context, phonetic rules). Preserve numbering and base-language wording. This is the *teacher's voice* of the lesson and is what the agent draws on when the learner asks "why is it like that?". OMIT this section only if the lesson has no notes block in the source. Do NOT paraphrase — copy faithfully. If a footnote is too OCR-noisy to recover, leave a placeholder like `- (note N) [OCR unreadable]` and add an issue to the manifest.
- **`## Exercises`** — the lesson's **Ejercicio / Exercice / Exercise** prompts verbatim, followed by the **Corrigé / Corregido / Answer** if present. Numbered as in the source. These are paste-ready material for the agent's Pincer drills. Omit the section if the lesson has no exercises.
- **`## Vocabulary highlights`** — bullet list of lemmas introduced or reinforced, each linked `[[vocab/<slug>]]`.
- **`## Patterns`** — bullet list of recurring constructions used, each linked `[[patterns/<slug>]]`.
- **`## Agent cues`** — *meta*-notes for the practice agent (distinct from the Assimil ## Lesson notes above): which lines are good Pincer **gap candidates** (predictable from context), suggested correction strategy, prosody hints, register flags. 2-5 sentences.
- **`## Audio`** — explicit relative path to the native-speaker MP3.

### Vocab page (`vocab/<lemma>.md`)

```yaml
---
title: <lemma in target language>
type: vocab
slug: <lemma-slug>                       # e.g. il-y-a, savoir-faire, look-forward-to
lemma: <surface form>
target_lang: fr | en
pos: noun | verb | adj | adv | phrase | idiom
gloss_es: <Spanish gloss>
gloss_en: <English gloss>                # if applicable
gloss_fr: <French gloss>                 # if applicable
frequency: <count of lessons it appears in>
first_lesson: [<source-slug>, <NNN>]
lessons: [[<source-slug>, <NNN>], ...]   # every lesson where it appears
collocations: [<collocation-slug>, ...]  # frequent multi-word patterns
register: neutral | familiar | formal | slang | regional
cefr: A1 | A2 | B1 | B2 | C1 | C2       # CEFR level at which this becomes productive
stability: evergreen | evolving | volatile
updated: YYYY-MM-DD
---
```

Body: definition, 2-3 example sentences (each citing a `[[dialogues/<slug>]]`), false-friend notes, common learner errors.

### Pattern page (`patterns/<slug>.md`)

```yaml
---
title: <Pattern name in target language>
type: pattern
slug: <pattern-slug>                     # e.g. il-y-a, going-to-future
target_lang: fr | en
form: <abstract form, e.g. "il y a + N">
function: <semantic role, e.g. "existential / locative">
lessons: [[<source-slug>, <NNN>], ...]
related_grammar: [<grammar-slug>, ...]
cefr: A1 | A2 | B1 | B2 | C1 | C2       # CEFR level at which this becomes productive
stability: evergreen | evolving | volatile
updated: YYYY-MM-DD
---
```

Body: `## Form`, `## Function`, `## Examples` (with `[[dialogues/...]]` cites), `## Contrasts` (vs. similar constructions), `## Pincer hint` (when to leave this as a gap).

### Grammar page (`grammar/<slug>.md`)

```yaml
---
title: <Grammar point in English or target language>
type: grammar
slug: <grammar-slug>                     # e.g. passe-compose, present-perfect
target_lang: fr | en
category: tense | mood | agreement | syntax | phonology | orthography
lessons: [[<source-slug>, <NNN>], ...]
related_patterns: [<pattern-slug>, ...]
cefr: A1 | A2 | B1 | B2 | C1 | C2       # CEFR level at which this grammar point is required
stability: evergreen
updated: YYYY-MM-DD
---
```

Body: `## Rule` (short summary, evergreen — copy formulations exactly when given), `## Examples`, `## Common errors`, `## When the agent should correct vs. let it slide`.

### Source page (`sources/<slug>.md`)

```yaml
---
title: <Full course title>
type: source
slug: <source-slug>                      # e.g. el-nuevo-frances-sin-esfuerzo
artifact_ref: _md_cache/<filename>.md
artifact_kind: external
target_lang: fr | en
base_lang: es | en
year: <pub year>
publisher: Assimil
lesson_count: <int>
cefr_range: [<min-level>, <max-level>]   # e.g. [A1, B2] for "Sin Esfuerzo" / "With Ease"
audio_root: <relative path to MP3 folder>
concepts: []                             # filled by ingest sub-agents
updated: YYYY-MM-DD
---
```

Body: `## Summary`, `## Pedagogical arc` (what the book teaches and in what order), `## Audio assets` (path to MP3 folder + count), `## Lessons covered` (with `[[dialogues/...]]` links), `## Notable peculiarities` (e.g. outdated references, regional usage).

### Person / org page

Short bio + `## Where they appear` listing the `[[dialogues|sources/...]]` they touch.

## Wikilinks

`[[dialogues/<slug>]]`, `[[vocab/<slug>]]`, `[[patterns/<slug>]]`, `[[grammar/<slug>]]`, `[[sources/<slug>]]`. Broken wikilinks are intentional TODO markers — the linter flags them; do not delete.

## Stability

- **evergreen** — core grammar, phonology, foundational lemmas
- **evolving** — usage notes, idioms (some shift over decades)
- **volatile** — situational vocabulary tied to outdated tech/culture (the source material is 2001–2011 era; some content needs ongoing modernization)

## Modernization rule

The Assimil corpus dates from 2001–2011 and routinely mentions obsolete tech (cassette players, VCRs, fax, video rental stores, operator-assisted calls). When deriving content for the agent:

- **`## Original` and `## Translation`** in dialogue pages preserve the source verbatim — never modernize.
- **`## Modernized`**, vocab example sentences, pattern examples, and agent-facing prompt content all use modern equivalents (audio file/podcast, streaming, messaging, search engine, app, voicemail).
- Cap modernization at the situational vocabulary level. Grammar and core lexicon are timeless.

## Categories

`index.md` groups dialogues, vocab, and patterns under categories that fit oral practice:
- by **language** (English / French)
- by **CEFR level** (A1 / A2 / B1 / B2 / C1 / C2) — primary categorisation, mandatory
- by **theme** (greetings, travel, food, work, etc.) — secondary
- by **pattern family** (existentials, tense families, idiom families)

**CEFR assignment heuristic** for Assimil sources:
- "Sin Esfuerzo" / "With Ease" / "Yourself" series — A1 (lessons 1–25), A2 (26–50), B1 (51–75), B2 (76–end). `cefr_range: [A1, B2]`.
- "Perfeccionamiento" / "Using" / "Practising" series — B2 (lessons 1–25), C1 (26–end). `cefr_range: [B2, C1]`.
- Override these defaults when specific content clearly demands a different level (e.g. an unusually idiomatic A1 lesson may actually be A2).
- When unsure, lean conservative (assign the higher level) so learners aren't shown content above their stated level.

## Workflows

### Ingest a new artifact
1. Convert the artifact via `simplify_format` into `_md_cache/`.
2. Create `sources/<slug>.md`.
3. For each lesson in the artifact, create `dialogues/<source-slug>-l<NNN>.md`.
4. Add/update `vocab/`, `patterns/`, `grammar/` pages; cite the new dialogues.
5. Append `log.md`: `## [YYYY-MM-DD] ingest | <summary>`.

### Drive a Pincer practice session
1. Pick a target lesson from `dialogues/`.
2. Look at `## Notes for the agent` for gap candidates.
3. Surface `vocab/` lemmas with `frequency > 3` that the learner hasn't seen in N days (SRS).
4. Use `## Modernized` if present and the learner is in a contemporary scenario; otherwise `## Original`.

### Lint
```bash
python3 ~/MEGA/IA/Skills/Session_template/scripts/kb_lint.py --kb <kb-path> --append-log
```

## Log operations

`ingest`, `lint`, `decision`, `session`, `migration`, `query`. Append-only. Format: `## [YYYY-MM-DD] <op> | <summary>`.

## When in doubt

- Update an existing page before creating a new one.
- Vocab slugs are the lemma in kebab-case (`il-y-a`, `look-forward-to`).
- Cite every example sentence with `[[dialogues/<slug>]]`.
- Preserve the original lesson text verbatim; modernize only in derived sections.
- Broken wikilinks are intentional TODO markers.
- Any structural change is reflected in `log.md`.
