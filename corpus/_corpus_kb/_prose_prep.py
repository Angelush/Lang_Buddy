#!/usr/bin/env python3
"""Prepare the prose-layer derivation batch.

Scans kb/dialogues/ for every [[vocab/<slug>]] and [[patterns/<slug>]] wikilink,
computes the DETERMINISTIC frontmatter for each target page (slug, target_lang,
cefr, lessons, first_lesson, frequency, gloss hint), then groups pages by their
owning dialogue and writes pre-scaffolded batch prompts under _prose/prompts/.

A free model only fills judgment fields (pos, register, glosses, form/function,
stability) and writes the prose body — it cannot corrupt the structural fields
because they are already rendered into the scaffold.

Outputs:
  _prose/manifest.json   full per-page metadata (used by _prose_integrate.py)
  _prose/batches.json    [{batch_id, owner, provider, pages:[slug...]}]
  _prose/prompts/<batch_id>.txt
"""
import json
import pathlib
import re
import collections

ROOT = pathlib.Path(__file__).resolve().parent
KB = ROOT / "kb"
DIAL = KB / "dialogues"
OUT = ROOT / "_prose"
PROMPTS = OUT / "prompts"
PROMPTS.mkdir(parents=True, exist_ok=True)

CEFR_RANK = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
LANG_NAME = {"en": "English", "fr": "French"}
BATCH_SIZE = 8
UPDATED = "2026-05-30"

LINK_RE = re.compile(r"\[\[(vocab|patterns)/([a-z0-9-]+)\]\]")
BULLET_RE = re.compile(r"^\s*-\s*\[\[(vocab|patterns)/([a-z0-9-]+)\]\]\s*[—-]\s*(.+?)\s*$")


def fm_field(fm_text, key):
    m = re.search(rf"^{key}:\s*(.+?)\s*$", fm_text, re.M)
    return m.group(1).strip() if m else ""


# ---- 1. scan dialogues -----------------------------------------------------
dialogues = {}            # slug -> {lang, cefr, body}
refs = collections.defaultdict(lambda: {"lessons": set(), "gloss": {}})  # (kind,slug)->...

for f in sorted(DIAL.glob("*.md")):
    txt = f.read_text(encoding="utf-8")
    parts = txt.split("---", 2)
    fm = parts[1] if len(parts) >= 3 else ""
    slug = fm_field(fm, "slug") or f.stem
    lang = fm_field(fm, "target_lang") or ("en" if f.name.startswith("en-") else "fr")
    cefr = fm_field(fm, "cefr") or "A1"
    dialogues[slug] = {"lang": lang, "cefr": cefr, "body": txt}
    for kind, target in LINK_RE.findall(txt):
        refs[(kind, target)]["lessons"].add(slug)
    for line in txt.splitlines():
        m = BULLET_RE.match(line)
        if m:
            kind, target, gloss = m.groups()
            refs[(kind, target)]["gloss"][slug] = gloss.strip()


def lesson_sort_key(s):
    return (CEFR_RANK.get(dialogues[s]["cefr"], 9), s)


# ---- 2. compute per-page metadata -----------------------------------------
manifest = {}
for (kind, target), data in refs.items():
    if (KB / kind / f"{target}.md").exists():
        continue  # already authored — only build prompts for missing pages
    lessons = sorted(data["lessons"], key=lesson_sort_key)
    first = lessons[0]
    lang = dialogues[first]["lang"]
    cefr = dialogues[first]["cefr"]
    gloss = data["gloss"].get(first) or next(iter(data["gloss"].values()), "")
    manifest[f"{kind}/{target}"] = {
        "kind": kind,
        "slug": target,
        "target_lang": lang,
        "cefr": cefr,
        "lessons": lessons,
        "first_lesson": first,
        "frequency": len(lessons),
        "gloss_hint": gloss,
    }

(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


# ---- 3. scaffold one page ---------------------------------------------------
def scaffold(meta):
    kind, slug, lang = meta["kind"], meta["slug"], meta["target_lang"]
    lessons_csv = ", ".join(meta["lessons"])
    cite = meta["first_lesson"]
    if kind == "vocab":
        gloss = meta["gloss_hint"] or "<FILL: gloss en español>"
        return f"""===FILE: vocab/{slug}.md===
---
title: <FILL: lemma de superficie en {LANG_NAME[lang]}, con acentos/artículo si es natural>
type: vocab
slug: {slug}
lemma: <FILL: forma de superficie>
target_lang: {lang}
pos: <FILL: noun|verb|adj|adv|phrase|idiom>
gloss_es: {gloss}
gloss_en: <FILL: glosa corta en inglés>
frequency: {meta['frequency']}
first_lesson: {cite}
lessons: [{lessons_csv}]
register: <FILL: neutral|familiar|formal|slang|regional>
cefr: {meta['cefr']}
stability: <FILL: evergreen|evolving|volatile>
updated: {UPDATED}
---

## Definition
<1-2 frases en español, para un hispanohablante que aprende {LANG_NAME[lang]}>

## Examples
- "<frase de ejemplo en {LANG_NAME[lang]} que usa el lema>" — [[dialogues/{cite}]]
- "<segunda frase de ejemplo>" — [[dialogues/{cite}]]

## Notes
<falso amigo ES↔{LANG_NAME[lang]} si lo hay; error típico de hispanohablante; registro. 1-3 viñetas.>
"""
    else:  # pattern
        return f"""===FILE: patterns/{slug}.md===
---
title: <FILL: nombre del patrón en {LANG_NAME[lang]}>
type: pattern
slug: {slug}
target_lang: {lang}
form: <FILL: forma abstracta, p.ej. "going to + V">
function: <FILL: función semántica>
lessons: [{lessons_csv}]
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
- "<ejemplo en {LANG_NAME[lang]}>" — [[dialogues/{cite}]]
- "<segundo ejemplo>" — [[dialogues/{cite}]]

## Contrasts
<contraste con el español o con un patrón cercano>

## Anticipation hint
<qué hueco vaciar para un drill de predecir-la-siguiente-palabra>
"""


PROMPT_HEADER = """Eres un autor de contenido ORIGINAL para una wiki de aprendizaje de idiomas (lengua base: español). Vas a derivar páginas de referencia de VOCABULARIO y PATRONES a partir del diálogo original que se incluye abajo.

REGLAS DURAS:
- 100% ORIGINAL. No reproduzcas, traduzcas ni parafrasees ningún curso publicado (Assimil ni otro). Inventa los ejemplos.
- Idioma meta de estas páginas: {lang_name}. Lengua base de glosas/explicaciones: español.
- Cita SOLO slugs de diálogo reales de la lista `lessons:` de cada página (formato [[dialogues/<slug>]]).
- Rellena ÚNICAMENTE los campos marcados <FILL: ...> y escribe el cuerpo de cada página. NO cambies ningún otro valor del frontmatter (slug, lessons, cefr, frequency, target_lang ya están correctos).
- Respeta EXACTAMENTE el orden de secciones y los encabezados ## del andamiaje.
- Mantén el nivel CEFR indicado: ejemplos y explicaciones acordes a ese nivel.
- Situaciones modernas (smartphone, app, streaming); nunca casetes/fax/VCR.

FORMATO DE SALIDA (crítico):
- Devuelve SOLO los ficheros, cada uno empezando por su línea `===FILE: <ruta>===` tal cual, seguido del contenido completo (--- frontmatter --- y cuerpo).
- NADA de preámbulo, comentarios, ni ```fences```. Empieza directamente con la primera línea `===FILE:`.

DIÁLOGO DE ORIGEN (contexto; extrae de aquí ejemplos y matices):
<<<DIALOGUE
{dialogue}
DIALOGUE

Ahora produce EXACTAMENTE estas {n} páginas, en este orden, rellenando los <FILL: ...> y los cuerpos:

{scaffolds}
"""


# ---- 4. group by owner, split into batches, write prompts ------------------
by_owner = collections.defaultdict(list)
for key, meta in manifest.items():
    by_owner[meta["first_lesson"]].append(meta)

batches = []
bidx = 0
providers = ["gemini-3.1-flash-lite-preview", "gemini-3.1-flash-lite-preview", "mistral-medium-3.5"]
for owner in sorted(by_owner, key=lesson_sort_key):
    pages = sorted(by_owner[owner], key=lambda m: (m["kind"], m["slug"]))
    for i in range(0, len(pages), BATCH_SIZE):
        chunk = pages[i:i + BATCH_SIZE]
        bidx += 1
        batch_id = f"b{bidx:03d}-{owner}"
        provider = providers[(bidx - 1) % len(providers)]
        lang = chunk[0]["target_lang"]
        dialogue_text = dialogues[owner]["body"]
        scaffolds = "\n".join(scaffold(m) for m in chunk)
        prompt = PROMPT_HEADER.format(
            lang_name=LANG_NAME[lang], dialogue=dialogue_text,
            n=len(chunk), scaffolds=scaffolds,
        )
        (PROMPTS / f"{batch_id}.txt").write_text(prompt, encoding="utf-8")
        batches.append({
            "batch_id": batch_id,
            "owner": owner,
            "provider": provider,
            "pages": [f"{m['kind']}/{m['slug']}" for m in chunk],
        })

(OUT / "batches.json").write_text(json.dumps(batches, indent=2, ensure_ascii=False), encoding="utf-8")

# ---- summary ----
ng = sum(1 for b in batches if b["provider"].startswith("gemini"))
nm = len(batches) - ng
print(f"pages: {len(manifest)} ({sum(1 for m in manifest.values() if m['kind']=='vocab')} vocab, "
      f"{sum(1 for m in manifest.values() if m['kind']=='patterns')} patterns)")
print(f"batches: {len(batches)}  (gemini={ng}, mistral={nm})  batch_size={BATCH_SIZE}")
print(f"owners: {len(by_owner)}")
