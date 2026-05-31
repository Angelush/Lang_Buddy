# Tutor retrieval indices

Built by `_build_index_new.py` from `kb/dialogues/*.md` frontmatter.

- **lessons.json** — dialogue catalog. Filter by `cefr` (learner level or +1 notch) and `theme`; fetch the matching `kb/dialogues/<slug>.md` for full text and `## Agent cues` gap candidates.
- **themes.json** — theme → dialogue slugs.
- **vocab.json / patterns.json / grammar.json** — item slug → {cefr, lessons[], page}. The SRS (`srs.md`) sources candidate items here, level-capped; each points back to the dialogues that teach it. `page: true` means a deep prose page exists under `kb/vocab|patterns|grammar/` (the optional reference layer the tutor can surface).
