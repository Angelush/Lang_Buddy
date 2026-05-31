#!/usr/bin/env python3
"""Author the REMAINING theme inventory (objectives.md) as new dialogues.

The thin slice built 2 themes per (lang, level). This fills the rest of each
level's theme list from refs/objectives.md — 19 EN + 19 FR = 38 new dialogues.

Reuses the slice's tuned TEMPLATE / LEVELS / EXEMPLAR from _author_prompts.py
(import side effect: re-writes the slice prompts under _authored/prompts/, which
are throwaway). Writes the new prompts to _authored/prompts2/.
"""
import importlib.util
import pathlib

P = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("author_prompts", P / "_author_prompts.py")
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)  # noqa: side effect writes slice prompts (throwaway)

LEVELS, TEMPLATE, LANG_NAME, EXEMPLAR = ap.LEVELS, ap.TEMPLATE, ap.LANG_NAME, ap.EXEMPLAR

OUT = P / "_authored" / "prompts2"
OUT.mkdir(parents=True, exist_ok=True)

# (slug, lang, level, theme_slug, situation hint, register)
JOBS = [
    # ---- English ----
    ("en-a1-family-01", "en", "A1", "family", "introducing your family in a photo — who they are, their names, what they do", "neutral"),
    ("en-a1-numbers-time-01", "en", "A1", "numbers", "asking and giving the time and a phone number; small numbers", "neutral"),
    ("en-a1-classroom-01", "en", "A1", "classroom", "first day in a language class: teacher's name, where to sit, which page, asking to repeat", "neutral"),
    ("en-a1-shopping-01", "en", "A1", "shopping", "buying a couple of basics in a small shop — a size, a colour, how much, paying by phone", "neutral"),
    ("en-a2-weekend-01", "en", "A2", "weekend", "telling a friend what you did last weekend — past simple, what went well", "familiar"),
    ("en-a2-plans-01", "en", "A2", "plans", "two friends making plans for Saturday — going to, can/can't, suggesting a time", "familiar"),
    ("en-a2-doctor-01", "en", "A2", "health", "describing symptoms to a doctor and getting simple advice", "neutral"),
    ("en-a2-describing-people-01", "en", "A2", "describing", "describing a mutual friend's appearance and personality to someone who hasn't met them", "familiar"),
    ("en-b1-hotel-01", "en", "B1", "problems", "sorting out a problem with a hotel room at reception — present perfect, polite complaint", "neutral"),
    ("en-b1-future-plans-01", "en", "B1", "plans", "talking about ambitions for the next year — will, first conditional, hopes", "familiar"),
    ("en-b1-hometown-01", "en", "B1", "hometown", "describing your hometown and how it has changed — used to, relative clauses", "familiar"),
    ("en-b2-news-01", "en", "B2", "media", "discussing a piece of news one of them read — reported speech, discourse markers", "neutral"),
    ("en-b2-environment-01", "en", "B2", "environment", "debating an everyday environmental choice (car vs transit, fast fashion) — conditionals, passive", "neutral"),
    ("en-b2-career-01", "en", "B2", "careers", "weighing a career decision with a friend — modals, second conditional, pros/cons", "familiar"),
    ("en-c1-cultural-difference-01", "en", "C1", "culture", "comparing a cultural difference each noticed living abroad — idiom, hedging, nuance", "neutral"),
    ("en-c1-work-ethics-01", "en", "C1", "ethics", "a reasoned, slightly tense disagreement over a workplace ethics dilemma", "formal"),
    ("en-c1-complaint-01", "en", "C1", "complaints", "making a delicate, diplomatic complaint about poor service — cleft sentences, modality", "formal"),
    ("en-c2-literature-01", "en", "C2", "culture", "an erudite, playful discussion of a novel — figurative language, implicature, allusion", "neutral"),
    ("en-c2-ambiguity-01", "en", "C2", "irony", "a witty exchange that turns on a double meaning / deliberate ambiguity", "familiar"),
    # ---- French ----
    ("fr-a1-famille-01", "fr", "A1", "famille", "présenter sa famille sur une photo — qui ils sont, leurs prénoms, ce qu'ils font", "neutral"),
    ("fr-a1-nombres-heure-01", "fr", "A1", "nombres", "demander et donner l'heure et un numéro de téléphone; petits nombres", "neutral"),
    ("fr-a1-classe-01", "fr", "A1", "classe", "premier jour en cours de langue: le nom du prof, où s'asseoir, quelle page, demander de répéter", "neutral"),
    ("fr-a1-achats-01", "fr", "A1", "achats", "acheter deux ou trois articles de base dans une petite boutique — taille, couleur, combien, payer par téléphone", "neutral"),
    ("fr-a2-weekend-01", "fr", "A2", "weekend", "raconter à un ami son week-end dernier — passé composé, ce qui s'est bien passé", "familiar"),
    ("fr-a2-projets-01", "fr", "A2", "projets", "deux amis font des projets pour samedi — futur proche, pouvoir, proposer une heure", "familiar"),
    ("fr-a2-medecin-01", "fr", "A2", "sante", "décrire ses symptômes au médecin et recevoir un conseil simple", "neutral"),
    ("fr-a2-decrire-personne-01", "fr", "A2", "decrire", "décrire l'apparence et le caractère d'un ami commun à quelqu'un qui ne l'a pas rencontré", "familiar"),
    ("fr-b1-hotel-01", "fr", "B1", "problemes", "régler un souci avec une chambre d'hôtel à la réception — passé composé, plainte polie", "neutral"),
    ("fr-b1-projets-avenir-01", "fr", "B1", "projets", "parler de ses ambitions pour l'année à venir — futur simple, conditionnel, espoirs", "familiar"),
    ("fr-b1-ma-ville-01", "fr", "B1", "ville", "décrire sa ville et comment elle a changé — imparfait, propositions relatives", "familiar"),
    ("fr-b2-actualite-01", "fr", "B2", "medias", "discuter d'une actualité que l'un a lue — discours indirect, connecteurs", "neutral"),
    ("fr-b2-environnement-01", "fr", "B2", "environnement", "débattre d'un choix écologique du quotidien (voiture vs transports, fast fashion) — conditionnel, voix passive", "neutral"),
    ("fr-b2-carriere-01", "fr", "B2", "carriere", "peser un choix de carrière avec un ami — modalité, conditionnel, pour/contre", "familiar"),
    ("fr-c1-difference-culturelle-01", "fr", "C1", "culture", "comparer une différence culturelle remarquée en vivant à l'étranger — idiome, nuance, atténuation", "neutral"),
    ("fr-c1-ethique-travail-01", "fr", "C1", "ethique", "un désaccord raisonné et un peu tendu sur un dilemme d'éthique au travail", "formal"),
    ("fr-c1-plainte-01", "fr", "C1", "plaintes", "formuler une plainte délicate et diplomate sur un mauvais service — mise en relief, modalité", "formal"),
    ("fr-c2-litterature-01", "fr", "C2", "culture", "une discussion érudite et enjouée sur un roman — langage figuré, implicite, allusion", "neutral"),
    ("fr-c2-ambiguite-01", "fr", "C2", "ironie", "un échange plein d'esprit qui joue sur un double sens / une ambiguïté volontaire", "familiar"),
]

for slug, lang, level, theme, hint, register in JOBS:
    lines, grammar = LEVELS[(lang, level)]
    prompt = TEMPLATE.format(
        lang_name=LANG_NAME[lang], lang=lang, level=level, theme=theme,
        slug=slug, hint=hint, grammar=grammar, lines=lines, register=register,
        exemplar=EXEMPLAR[lang],
    )
    (OUT / f"{slug}.txt").write_text(prompt, encoding="utf-8")

print(f"wrote {len(JOBS)} prompts to {OUT}")
print(f"  EN={sum(1 for j in JOBS if j[1]=='en')}  FR={sum(1 for j in JOBS if j[1]=='fr')}")
