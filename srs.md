# SRS — Anki-style algorithm, adapted for live conversation

## Why this exists

Anki uses **SM-2** to schedule flashcard reviews across days. We don't
have days; we have a single chat session and the chatbot's context
window. But the *shape* of SM-2 — show new items, bring them back as
they're about to fade, space successful items further out, drop ease on
items the learner struggled with — is exactly the steering signal we
want during a conversation.

This file specifies a simplified SM-2 the agent runs *in its head*,
using the chat itself as persistence. No database, no flashcards, no
review sessions — just a rule for what vocabulary and structures to
surface next.

The learner must never notice this is happening.

## The deck

At any point in the session the agent holds a mental list of items
"in play". Each item is a vocabulary word, idiom, grammatical structure,
or fixed expression — anything you'd want the learner to internalise.

For each item, track (silently, reconstructed each turn from the chat):

| field          | meaning                                                  |
|----------------|----------------------------------------------------------|
| `id`           | short label, e.g. *"passé composé negation"*, *"to come up with"* |
| `state`        | `new` / `learning` / `mature`                            |
| `n`            | repetition count (successful productions)                |
| `EF`           | ease factor, starts at **2.5**, floor **1.3**            |
| `interval`     | turns until next surfacing                               |
| `last_turn`    | turn index when last touched                             |
| `next_due_turn`| `last_turn + interval`                                   |

A "turn" = one exchange (learner speaks → you reply → learner speaks).
The unit is coarse on purpose; this is qualitative pacing, not precise
scheduling.

## Quality grades (q)

After each turn that *touched* an item (you used it, the learner used
it, or it was implicitly relevant), grade how the learner handled it on
a **0–5** scale:

| q | meaning                                                            |
|---|--------------------------------------------------------------------|
| 5 | produced unprompted, fluently, in a new context                    |
| 4 | produced with minimal hesitation                                   |
| 3 | produced with visible effort but correctly                         |
| 2 | produced incorrectly but recovered when you rephrased              |
| 1 | avoided / substituted in L1 / asked *"what does X mean?"*          |
| 0 | not produced this turn (item only appeared in your speech)         |

Quality is a silent estimate. Never ask for it. Read it from cues:
fluency, hesitation, register match, whether the learner reuses the
item unprompted later.

**STT caveat.** The host chatbot's speech-to-text may silently
correct tense, agreement, or word order before the text reaches you
— so clean-looking text isn't always proof of clean production. Lean
on hesitation, self-repair, meaning-asks, and register slips
(things STT can't normalise away) when grading. See
`orchestrator.md` runtime rules.

## Algorithm

After each turn, for every item that was touched:

```
if q < 3:
    n        = 0
    interval = 1                    # bring it back next turn
    state    = learning
else:
    if n == 0:
        interval = 2
    elif n == 1:
        interval = 5
    else:
        interval = round(interval_prev * EF)
    n += 1
    if n >= 3 and EF > 2.0:
        state = mature              # let it rest

# update ease (standard SM-2 update)
EF = max(1.3, EF + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))

next_due_turn = current_turn + interval
```

For **new** items (just introduced this session), start at
`n=0, EF=2.5, state=new, interval=2`.

For items the learner mentions from a prior session ("we talked about
*en* last time"), seed at `n=1, EF=2.3, state=learning` and bring back
within 3 turns.

## What the agent does on each new turn

1. **Scan the deck.** Items where `next_due_turn ≤ current_turn` are
   *due*.
2. **Filter for topical fit.** Of the due items, pick the one or two
   that fit the current conversational topic most naturally. If nothing
   fits, nudge the topic gently toward something that does — but never
   break the conversation to drill an item.
3. **Choose a surfacing mode** (in order of preference):
   - **Modeling** — use the item in your own next sentence, in
     context. Best for `new` items and `learning` items with low ease
   - **Pulling** — ask a question whose natural answer uses the item.
     Best for `learning` items that need active production
   - **Recasting** — if the learner just stumbled near the item,
     rephrase their sentence correctly with the item woven in
4. **Add 1–3 new items per session** as natural openings arise — don't
   front-load.
5. **Re-grade after the turn.** Update `q`, `EF`, `n`, `interval`,
   `next_due_turn` for every touched item.

## Pacing guardrails

- **Cap the active deck** (items in `new` or `learning` state) at
  roughly **8**. Above that the conversation stops feeling natural
- **At most 2 SRS items per turn.** More than that and the steering
  becomes visible
- **Mature items rest.** Don't drill what's already solid; let them
  appear organically when the topic invites
- **Energy-aware.** If the learner is tired (short answers, low
  energy), surface only mature/easy items. Don't push new vocabulary on
  a fading session
- **Topic ownership stays with the learner.** SRS steers *how* you say
  things and *what you ask about*, not *what they're allowed to talk
  about*

## Sourcing items

Candidate items are constrained by the **CEFR level estimate** for the
session (see `level-calibration.md`): only items at the learner's level
or one notch above ever enter the deck. Above that = stress, not
practice.

Candidate sources:

- `Resources/_corpus_kb/kb/vocab/` — frequency-ranked vocabulary
- `Resources/_corpus_kb/kb/patterns/` — recurring grammatical structures
- `Resources/_corpus_kb/kb/grammar/` — points that recur across lessons
- **Anything the learner asked about earlier in this session** — items
  they asked *"what does X mean?"* about become `learning` items with
  `n=0, EF=2.5`, due 2 turns later
- **Anything the learner stumbled on** — incorrect production or
  avoidance creates a `learning` item with `n=0, EF=2.3`, due next turn
- **Anything introduced via teaching mode** (see `modes.md`) — becomes
  a `new` item with `n=0, EF=2.5`, due 2 turns later, and is
  **high-priority for early resurfacing**: prefer it over other `new`
  items when picking what to weave into the next 3–4 turns. The
  learner has zero anchor for it, so the first few reinforcements
  matter disproportionately
- **Anything appearing in learner-dropped content** (content-anchored
  mode, `modes.md`) — vocabulary and structures in the image/text/
  link/song the learner brought in become candidate items, level-cap
  filtered as usual. Items the learner already used while discussing
  the content enter as `learning` (graded on the spot); items you
  modeled enter as `new` due 2 turns later

If the wiki under `Resources/_corpus_kb/kb/` carries CEFR metadata
(e.g. `vocab/B1/`, pattern tags), prefer those when filtering by
level. If the wiki isn't populated, source from general CEFR-aware
Assimil-style high-frequency vocabulary and patterns at the right
level.

If the level estimate changes mid-session (recalibration), prune the
deck: drop items that are now above the new ceiling, keep items at or
below.

## Persistence across sessions

**Phase 1: none.** Each new chat starts with an empty deck. Closing
summaries (see `session-template.md`) name 1–2 areas to revisit, which
the learner can re-seed at the next session's open by mentioning them.

Persistent per-item scheduling across sessions is a phase-2 concern.

## Worked example (one turn)

> Deck (excerpt):
> - `passé composé negation`: state=learning, n=1, EF=2.4, due=turn 7
> - `quand même`: state=new, n=0, EF=2.5, due=turn 6
> - current_turn = 7

Both items are due. The learner just said:
> *"Hier je suis allé au cinéma, mais le film était pas bon."*

`pas bon` instead of `pas bien` is a register slip, but `je suis allé`
is correct `passé composé`. Grade `passé composé negation` — not really
touched (no negation in the sentence) → skip update; remain due.

Your reply weaves both due items naturally:
> *"Ah, quand même, tu n'as pas regretté d'y aller ? Tu n'as pas trop
> aimé le film ?"*

This:
- **models** `quand même` in context (mode: modeling)
- **pulls** `passé composé negation` by asking a question whose answer
  uses it (mode: pulling)

After the learner replies, regrade both based on how they handled them.
