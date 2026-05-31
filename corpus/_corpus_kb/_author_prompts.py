#!/usr/bin/env python3
"""Build per-dialogue authoring prompts from the CEFR objective spine + the
same-language gold-standard exemplar. Outputs one prompt file per slug under
_authored/prompts/. A separate bash loop dispatches them to the gemini CLI.

The generator receives ONLY: the schema, the level objective block, and an
exemplar of OUR original content. It never sees any copyrighted source text.
"""
import os
import pathlib

KB = pathlib.Path(__file__).resolve().parent / "kb"
OUT = pathlib.Path(__file__).resolve().parent / "_authored" / "prompts"
OUT.mkdir(parents=True, exist_ok=True)

EXEMPLAR = {
    "en": (KB / "dialogues" / "en-a1-greetings-01.md").read_text(encoding="utf-8"),
    "fr": (KB / "dialogues" / "fr-a1-rencontres-01.md").read_text(encoding="utf-8"),
}

# Compact level specs mirrored from refs/objectives.md (the authoritative spine).
LEVELS = {
    ("en", "A1"): ("6-10", "to be / to have present, articles (a/an/the), plurals, subject pronouns, possessive adjectives, yes/no + wh- questions, isn't/aren't. PRESENT TENSE ONLY; no past or future."),
    ("en", "A2"): ("8-12", "past simple (regular + irregular), 'going to' future, can/can't, comparatives, frequency adverbs, prepositions of place/time, there is/are. No conditionals, no subjunctive, no present perfect."),
    ("en", "B1"): ("10-14", "present perfect vs past simple, 'will' future, first conditional, relative clauses (who/which/that), should/have to, used to. One subordinate clause per sentence is fine."),
    ("en", "B2"): ("12-16", "second & third conditional, passive voice, reported speech, discourse markers (however/although/despite), common phrasal verbs. Complex subordination allowed."),
    ("en", "C1"): ("14-18", "inversion, cleft sentences, nuanced modality, advanced connectors, idiomatic phrasal verbs, hedging & emphasis. Register-aware and idiomatic."),
    ("en", "C2"): ("14-20", "full native range; stylistic devices, irony and figurative language, fine register/tone control, subtle implicature."),
    ("fr", "A1"): ("6-10", "etre / avoir present, articles definis/indefinis, genre & nombre, pronoms sujets, negation ne...pas, questions est-ce que, il y a. PRESENT ONLY."),
    ("fr", "A2"): ("8-12", "passe compose (avoir/etre), futur proche, pouvoir/devoir, comparatif, adverbes de frequence, prepositions de lieu, partitifs (du/de la). Pas de conditionnel ni subjonctif."),
    ("fr", "B1"): ("10-14", "imparfait vs passe compose, futur simple, conditionnel present, pronoms relatifs (qui/que/ou), pronoms en/y, 'il faut que' (intro)."),
    ("fr", "B2"): ("12-16", "subjonctif present, conditionnel passe, voix passive, discours indirect, connecteurs (cependant/bien que/malgre), 'dont'."),
    ("fr", "C1"): ("14-18", "mise en relief (c'est...que), inversion, modalite nuancee, subjonctif passe, connecteurs avances, locutions idiomatiques. Sensible au registre."),
    ("fr", "C2"): ("14-20", "gamme native complete; procedes stylistiques, ironie/figure, controle fin du registre, implicite subtil, concordance des temps."),
}

# (slug, lang, level, theme_slug, situation hint, register)
JOBS = [
    ("en-a1-cafe-01", "en", "A1", "cafe", "ordering a drink and a snack at a cafe; asking the price; paying", "neutral"),
    ("en-a2-directions-01", "en", "A2", "directions", "a tourist asks a local for directions to a museum; turn left/right, go straight, it's near", "neutral"),
    ("en-b1-travel-01", "en", "B1", "travel", "two friends; one describes a recent trip - what they did, what went wrong, what they'd do again", "familiar"),
    ("en-b1-opinions-film-01", "en", "B1", "opinions", "two friends disagree about a film/series they streamed; giving and justifying opinions", "familiar"),
    ("en-b2-technology-01", "en", "B2", "technology", "weighing pros and cons of constant smartphone use in daily life", "neutral"),
    ("en-b2-workplace-01", "en", "B2", "workplace", "two colleagues politely disagree about a project decision in a meeting", "formal"),
    ("en-c1-debate-citylife-01", "en", "C1", "debate", "a reasoned argument between two people: living in the city vs the countryside", "neutral"),
    ("en-c1-negotiation-01", "en", "C1", "negotiation", "a delicate negotiation over a freelance rate / project scope; hedging and diplomacy", "formal"),
    ("en-c2-irony-01", "en", "C2", "irony", "a witty, ironic exchange between close friends about a minor disaster; humour and understatement", "familiar"),
    ("en-c2-ai-creativity-01", "en", "C2", "debate", "an abstract debate: can artificial intelligence be genuinely creative", "neutral"),
    ("fr-a1-cafe-01", "fr", "A1", "cafe", "commander une boisson et quelque chose a manger au cafe; demander le prix; payer", "neutral"),
    ("fr-a2-routine-01", "fr", "A2", "routine", "decrire sa routine et raconter la veille au passe compose", "familiar"),
    ("fr-a2-directions-01", "fr", "A2", "directions", "un touriste demande son chemin vers un musee; a gauche/droite, tout droit, c'est pres", "neutral"),
    ("fr-b1-voyage-01", "fr", "B1", "voyage", "deux amis; l'un raconte un voyage recent - ce qu'il a fait, un imprevu, ce qu'il referait", "familiar"),
    ("fr-b1-opinions-film-01", "fr", "B1", "opinions", "deux amis ne sont pas d'accord sur un film/serie; donner et justifier son avis", "familiar"),
    ("fr-b2-technologie-01", "fr", "B2", "technologie", "peser le pour et le contre de l'usage constant du smartphone au quotidien", "neutral"),
    ("fr-b2-travail-01", "fr", "B2", "travail", "deux collegues sont poliment en desaccord sur une decision de projet en reunion", "formal"),
    ("fr-c1-debat-ville-campagne-01", "fr", "C1", "debat", "une argumentation raisonnee: vivre en ville ou a la campagne", "neutral"),
    ("fr-c1-negociation-01", "fr", "C1", "negociation", "une negociation delicate sur un tarif freelance / le perimetre d'un projet; diplomatie", "formal"),
    ("fr-c2-ironie-01", "fr", "C2", "ironie", "un echange plein d'ironie entre amis proches a propos d'un petit desastre; humour et litote", "familiar"),
    ("fr-c2-ia-creativite-01", "fr", "C2", "debat", "un debat abstrait: l'intelligence artificielle peut-elle etre vraiment creative", "neutral"),
]

TEMPLATE = """You are authoring ORIGINAL language-learning content for an AI oral-practice tutor. Output EXACTLY ONE dialogue page in Markdown, matching the schema and quality of the example below.

HARD RULES (follow all):
- 100% ORIGINAL. Invent the characters, situation, and every line. Do NOT reproduce, translate, or paraphrase any published course (Assimil or any other). If a known textbook lesson comes to mind, discard it and invent something new.
- Target language: {lang_name}. CEFR level: {level}. Theme: "{theme}". Slug: `{slug}`. base_lang: es (give a faithful Spanish translation of YOUR dialogue).
- Situation to dramatise: {hint}.
- STAY INSIDE THE {level} BAND. Grammar/structures allowed: {grammar}. At most ONE stretch item one notch up, embedded so its meaning is recoverable from context.
- Dialogue length: {lines} numbered lines. Lines must be speakable for TTS; punctuation engineers the pace.
- Modern situations only (smartphone, app, streaming, messaging, voicemail). Never cassettes/fax/VCR/video stores/phone books.
- Output ONLY the Markdown file content (frontmatter + body). No preamble, no commentary, no code fences.

SECTIONS, in this exact order:
1) YAML frontmatter, keys: title, type: dialogue, slug: {slug}, target_lang: {lang}, base_lang: es, cefr: {level}, theme: {theme}, themes (list of kebab-case slugs), grammar (list of kebab-case slugs), patterns (list of kebab-case slugs), vocab_introduced (list of kebab-case lemma slugs), recycles (list of earlier-level lemma/pattern slugs reused, may be empty), register: {register}, origin: original, updated: 2026-05-30
2) ## Dialogue  — numbered lines
3) ## Pronunciation  — IPA for tricky words / liaisons / links
4) ## Translation  — faithful Spanish translation of YOUR dialogue
5) ## Notes  — 2-6 short pedagogical footnotes (grammar quirk, false friend ES<->{lang_name}, register, phonetics)
6) ## Exercises  — 3-5 original prompts, then a line starting "**Answer key:**"
7) ## Vocabulary highlights  — bullets, each `[[vocab/<slug>]]` with a short gloss
8) ## Patterns  — bullets, each `[[patterns/<slug>]]` with a short gloss
9) ## Agent cues  — 2-5 sentences: anticipation prompts (by line number), correction strategy, prosody, register flags, common ES-L1 errors

All frontmatter list values MUST be kebab-case slugs (no spaces, lowercase, hyphens).

GOLD-STANDARD EXAMPLE (same language, level A1 — for FORMAT and QUALITY ONLY; do NOT reuse its content, characters, or situation):
<<<EXEMPLAR
{exemplar}
EXEMPLAR

Now author `{slug}`.
"""

LANG_NAME = {"en": "English", "fr": "French"}

for slug, lang, level, theme, hint, register in JOBS:
    lines, grammar = LEVELS[(lang, level)]
    prompt = TEMPLATE.format(
        lang_name=LANG_NAME[lang], lang=lang, level=level, theme=theme,
        slug=slug, hint=hint, grammar=grammar, lines=lines, register=register,
        exemplar=EXEMPLAR[lang],
    )
    (OUT / f"{slug}.txt").write_text(prompt, encoding="utf-8")

print(f"wrote {len(JOBS)} prompts to {OUT}")
for slug, *_ in JOBS:
    print(" ", slug)
