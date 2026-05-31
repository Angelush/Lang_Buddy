#!/usr/bin/env python3
"""Round 2: derive prose pages for index items that have NO page yet.

Round 1 (_prose_prep.py) covered every [[wikilink]] target. This round covers
the rest of the deep layer: items DECLARED in dialogue frontmatter
(vocab_introduced / recycles / patterns / grammar) but never wikilinked, so the
linter never flagged them. Driven by kb/index/*.json `page: false` entries.

Differs from round 1: no gloss hint (item was never in a `## … highlights`
bullet → model writes the gloss), and adds the grammar page schema.

Outputs: _prose/manifest2.json, _prose/batches2.json, _prose/prompts2/<id>.txt
"""
import json
import pathlib
import collections

ROOT = pathlib.Path(__file__).resolve().parent
KB = ROOT / "kb"
IDX = KB / "index"
DIAL = KB / "dialogues"
OUT = ROOT / "_prose"
PROMPTS = OUT / "prompts2"
PROMPTS.mkdir(parents=True, exist_ok=True)

CEFR_RANK = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
LANG_NAME = {"en": "English", "fr": "French"}
BATCH_SIZE = 8
UPDATED = "2026-05-31"

lessons_idx = {x["slug"]: x for x in json.loads((IDX / "lessons.json").read_text(encoding="utf-8"))}


def lesson_lang(s):
    return lessons_idx.get(s, {}).get("target_lang") or ("en" if s.startswith("en-") else "fr")


def lesson_sort_key(s):
    return (CEFR_RANK.get(lessons_idx.get(s, {}).get("cefr"), 9), s)


# ---- 1. collect page==false items from the three indices -------------------
manifest = {}
for kind in ("vocab", "patterns", "grammar"):
    data = json.loads((IDX / f"{kind}.json").read_text(encoding="utf-8"))
    for slug, e in data.items():
        if e.get("page"):
            continue
        less = sorted(e.get("lessons", []), key=lesson_sort_key)
        if not less:
            continue
        first = less[0]
        manifest[f"{kind}/{slug}"] = {
            "kind": kind, "slug": slug,
            "target_lang": lesson_lang(first),
            "cefr": e.get("cefr") or lessons_idx.get(first, {}).get("cefr") or "A1",
            "lessons": less, "first_lesson": first, "frequency": len(less),
        }

(OUT / "manifest2.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


# ---- 2. scaffolds ----------------------------------------------------------
def scaffold(meta):
    kind, slug, lang = meta["kind"], meta["slug"], meta["target_lang"]
    ln = LANG_NAME[lang]
    csv = ", ".join(meta["lessons"])
    cite = meta["first_lesson"]
    if kind == "vocab":
        return f"""===FILE: vocab/{slug}.md===
---
title: <FILL: lemma de superficie en {ln}, con acentos/artículo si es natural>
type: vocab
slug: {slug}
lemma: <FILL: forma de superficie>
target_lang: {lang}
pos: <FILL: noun|verb|adj|adv|phrase|idiom>
gloss_es: <FILL: glosa en español>
gloss_en: <FILL: glosa corta en inglés>
frequency: {meta['frequency']}
first_lesson: {cite}
lessons: [{csv}]
register: <FILL: neutral|familiar|formal|slang|regional>
cefr: {meta['cefr']}
stability: <FILL: evergreen|evolving|volatile>
updated: {UPDATED}
---

## Definition
<1-2 frases en español, para un hispanohablante que aprende {ln}>

## Examples
- "<frase de ejemplo en {ln} que usa el lema>" — [[dialogues/{cite}]]
- "<segunda frase de ejemplo>" — [[dialogues/{cite}]]

## Notes
<falso amigo ES↔{ln} si lo hay; error típico de hispanohablante; registro. 1-3 viñetas.>
"""
    if kind == "patterns":
        return f"""===FILE: patterns/{slug}.md===
---
title: <FILL: nombre del patrón en {ln}>
type: pattern
slug: {slug}
target_lang: {lang}
form: <FILL: forma abstracta, p.ej. "going to + V">
function: <FILL: función semántica>
lessons: [{csv}]
related_grammar: [<FILL: slugs kebab de gramática, puede ir vacío>]
cefr: {meta['cefr']}
stability: <FILL: evergreen|evolving|volatile>
updated: {UPDATED}
---

## Form
<la construcción, esquemáticamente>

## Function
<cuándo/por qué se usa, en español>

## Examples
- "<ejemplo en {ln}>" — [[dialogues/{cite}]]
- "<segundo ejemplo>" — [[dialogues/{cite}]]

## Contrasts
<contraste con el español o con un patrón cercano>

## Anticipation hint
<qué hueco vaciar para un drill de predecir-la-siguiente-palabra>
"""
    # grammar
    return f"""===FILE: grammar/{slug}.md===
---
title: <FILL: nombre del punto gramatical en {ln}>
type: grammar
slug: {slug}
target_lang: {lang}
category: <FILL: tense|mood|agreement|syntax|phonology|orthography>
lessons: [{csv}]
related_patterns: [<FILL: slugs kebab de patrones, puede ir vacío>]
cefr: {meta['cefr']}
stability: evergreen
updated: {UPDATED}
---

## Rule
<la regla, explicada en español para un hispanohablante; concisa y clara>

## Examples
- "<ejemplo en {ln}>" — [[dialogues/{cite}]]
- "<segundo ejemplo>" — [[dialogues/{cite}]]

## Common errors
<errores típicos de hispanohablantes (interferencia del español) con este punto>

## When the agent should correct vs. let it slide
<guía para el tutor: cuándo corregir este punto y cuándo dejarlo pasar según el nivel>
"""


PROMPT_HEADER = """Eres un autor de contenido ORIGINAL para una wiki de aprendizaje de idiomas (lengua base: español). Vas a redactar páginas de referencia ({kinds}) que faltan, a partir del diálogo original incluido abajo.

REGLAS DURAS:
- 100% ORIGINAL. No reproduzcas, traduzcas ni parafrasees ningún curso publicado. Inventa los ejemplos.
- Idioma meta: {lang_name}. Explicaciones y glosas en español.
- Cita SOLO slugs de diálogo reales de la lista `lessons:` de cada página (formato [[dialogues/<slug>]]). NO crees otros wikilinks ([[vocab/...]], [[patterns/...]], [[grammar/...]]) en el cuerpo.
- Rellena ÚNICAMENTE los campos <FILL: ...> y escribe el cuerpo. NO cambies slug, lessons, cefr, frequency ni target_lang (ya están correctos).
- Respeta EXACTAMENTE el orden y los encabezados ## del andamiaje.
- Nivel CEFR indicado: ejemplos y explicaciones acordes a ese nivel. Situaciones modernas; nunca casetes/fax/VCR.

FORMATO DE SALIDA (crítico):
- Devuelve SOLO los ficheros, cada uno empezando por su línea `===FILE: <ruta>===` tal cual, seguido del contenido completo.
- NADA de preámbulo, comentarios ni ```fences```. Empieza directamente con la primera línea `===FILE:`.

DIÁLOGO DE ORIGEN (contexto; de aquí salen ejemplos y matices):
<<<DIALOGUE
{dialogue}
DIALOGUE

Ahora produce EXACTAMENTE estas {n} páginas, en este orden, rellenando los <FILL: ...> y los cuerpos:

{scaffolds}
"""


# ---- 3. batch by owner -----------------------------------------------------
by_owner = collections.defaultdict(list)
for key, meta in manifest.items():
    by_owner[meta["first_lesson"]].append(meta)

providers = ["gemini-3.1-flash-lite-preview", "gemini-3.1-flash-lite-preview", "mistral-medium-3.5"]
batches = []
bidx = 0
for owner in sorted(by_owner, key=lesson_sort_key):
    pages = sorted(by_owner[owner], key=lambda m: (m["kind"], m["slug"]))
    dialogue_text = (DIAL / f"{owner}.md").read_text(encoding="utf-8")
    for i in range(0, len(pages), BATCH_SIZE):
        chunk = pages[i:i + BATCH_SIZE]
        bidx += 1
        batch_id = f"r2-{bidx:03d}-{owner}"
        provider = providers[(bidx - 1) % len(providers)]
        lang = chunk[0]["target_lang"]
        kinds = ", ".join(sorted({m["kind"] for m in chunk}))
        prompt = PROMPT_HEADER.format(
            kinds=kinds, lang_name=LANG_NAME[lang], dialogue=dialogue_text,
            n=len(chunk), scaffolds="\n".join(scaffold(m) for m in chunk),
        )
        (PROMPTS / f"{batch_id}.txt").write_text(prompt, encoding="utf-8")
        batches.append({"batch_id": batch_id, "owner": owner, "provider": provider,
                        "pages": [f"{m['kind']}/{m['slug']}" for m in chunk]})

(OUT / "batches2.json").write_text(json.dumps(batches, indent=2, ensure_ascii=False), encoding="utf-8")

byk = collections.Counter(m["kind"] for m in manifest.values())
ng = sum(1 for b in batches if b["provider"].startswith("gemini"))
print(f"round-2 pages: {len(manifest)}  (vocab={byk['vocab']}, patterns={byk['patterns']}, grammar={byk['grammar']})")
print(f"batches: {len(batches)}  (gemini={ng}, mistral={len(batches)-ng})  owners={len(by_owner)}")
