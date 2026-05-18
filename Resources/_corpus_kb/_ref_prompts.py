#!/usr/bin/env python3
"""Build per-reference prompts for Phase C complementary content.

Writes _dispatch_prompts/ref_<name>.prompt.txt files for these references:
- ref_cefr_can_do
- ref_es_pitfalls_en
- ref_es_pitfalls_fr
- ref_freq_anchors
"""
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "_dispatch_prompts"
OUT.mkdir(exist_ok=True)

PROMPTS = {
    "ref_cefr_can_do": """You are compiling a quick-reference table for a language-tutor AI agent.

Produce a markdown document `cefr_can_do.md` covering the six CEFR levels (A1, A2, B1, B2, C1, C2). For each level, list 6-10 "can-do" statements grouped under: SPEAKING, LISTENING, READING, WRITING. Base the content on the official Council of Europe Companion Volume / Common Reference Levels descriptors (which are openly published) — do NOT invent. Keep each statement as a short bullet (under 25 words). Use the present-tense second-person form: "Can introduce yourself..."

Output structure:
```markdown
# CEFR can-do statements (quick reference)

## A1
### Speaking
- ...
### Listening
- ...
### Reading
- ...
### Writing
- ...

## A2
... (same structure) ...

(continue through C2)
```

Output ONLY the markdown. No commentary. Target length 2-4 KB.""",

    "ref_es_pitfalls_en": """You are compiling a Spanish-L1 → English-L2 error-pattern reference for a language-tutor AI agent.

Produce a markdown document `es_speaker_pitfalls_en.md` listing the most common, well-documented mistakes Spanish-speaking learners make in English. Base content on standard applied-linguistics references (Swan's "Learner English", Whitley's "Spanish/English Contrasts", etc.) — established patterns only, do NOT invent.

Sections (use this exact structure):
```markdown
# Spanish speakers learning English — common pitfalls

## Phonology
- (e.g., adding /e/ before initial s+consonant: "espicy" → "spicy"; /b/-/v/ merger; word-final consonant clusters)

## Morphosyntax
- (subject-pronoun drop, missing /-s/ on 3rd-person singular, "I have 25 years" calque, etc.)

## Tense & aspect
- (present perfect vs. preterite confusion, "since" + present misuse, etc.)

## Articles & prepositions
- (definite article overuse, "depend of", "married with", "in the morning vs. at noon", etc.)

## Word choice & false friends
- (assist ≠ asistir, embarrassed ≠ embarazada, success ≠ suceso, etc.)

## Pragmatic / register
- (overformal "would you like to", direct-speech expectations, etc.)
```

Each bullet: 1-2 sentences, include the Spanish source pattern and the English target. Aim for 6-12 bullets per section. Target length 3-5 KB.

Output ONLY the markdown. No commentary.""",

    "ref_es_pitfalls_fr": """You are compiling a Spanish-L1 → French-L2 error-pattern reference for a language-tutor AI agent.

Produce a markdown document `es_speaker_pitfalls_fr.md`. Base on standard contrastive analyses (Spanish-French is a notoriously deceptive proximity pair). Document established patterns only, do NOT invent.

Sections:
```markdown
# Spanish speakers learning French — common pitfalls

## Phonology
- (nasal vowels, /ʁ/ vs. tap /ɾ/, /y/ vs. /u/, schwa elision, h muet vs. aspiré)

## Gender & agreement
- (gender mismatches between cognates: la leche → le lait, la sangre → le sang)

## Tense & mood
- (subjonctif triggers Spanish doesn't share, passé composé selection of être vs. avoir)

## Word order & negation
- (ne... pas placement, object pronoun position, inversion in questions)

## Articles, partitives, prepositions
- (du/de la partitive, en vs. dans, à + city vs. en + country)

## False friends and false cognates
- (constipé ≠ constipado [constipated → enrhumé]; embrasser ≠ abrazar; rester ≠ restar; etc.)

## Pragmatic / register
- (tu/vous selection, formality cues)
```

6-12 bullets per section, 1-2 sentences each. Include Spanish form → French target. Target length 3-5 KB.

Output ONLY the markdown.""",

    "ref_freq_anchors": """You are compiling a frequency-anchored vocabulary reference for a language-tutor AI agent.

Produce a markdown document `freq_anchors.md` listing the top 100 lemmas in English and 100 in French by general spoken-language frequency. Base on widely-cited public-domain frequency lists (OpenSubtitles, SUBTLEX) — established lemma counts only, do NOT fabricate.

Structure:
```markdown
# Frequency-anchored core vocabulary

## English — top 100 lemmas (spoken-language frequency rank)
1. you
2. I
3. the
4. to
5. a
... (continue to 100, one lemma per line, no commentary)

## French — top 100 lemmas
1. de
2. la
3. le
4. et
... (continue to 100)
```

Just the numbered lemma lists. No glosses, no part of speech tags. The tutor will cross-reference these with the corpus vocab to prioritize promotion. Target length 4-6 KB.

Output ONLY the markdown.""",
}


def main():
    for name, prompt in PROMPTS.items():
        path = OUT / f"{name}.prompt.txt"
        path.write_text(prompt, encoding="utf-8")
        print(f"{path} ({len(prompt)} bytes)")


if __name__ == "__main__":
    main()
