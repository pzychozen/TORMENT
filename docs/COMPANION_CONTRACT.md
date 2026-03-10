# Companion Contract — What TORMENT Does and Does Not Do

TORMENT v2.0

---

TORMENT is a **memory substrate**. It makes your companion feel continuous without rewriting the character. The v2.0 character layer lets identity emerge from memory rather than being hardcoded — but it still follows the same contract.

## TORMENT SHOULD store

- **User context**: preferences, routines, stable dislikes/likes (when repeated)
- **Relationship context**: boundaries, shared goals, ongoing projects
- **Project context**: task state, decisions, TODOs, constraints
- **Emotional continuity**: light tags (calm/stressed/etc.) and mood drift events as guidance
- **Character seed**: the minimal identity definition (3-5 sentences) that forms the gravitational center

## TORMENT SHOULD NOT

- Decide your companion's personality, tone, morals, or roleplay rules — the seed provides gravity, not rules
- "Diagnose" mental health
- Turn temporary moods into permanent identity
- Override the model's outputs — TORMENT provides context, the model decides what to say
- Rewrite existing memories — gravity correction is always additive

## Character seeds (v2.0)

A seed is not a rulebook the model performs. It is the deepest attractor in the epistemic landscape. Everything else orbits.

Write seeds as natural descriptions of who the character is, not instructions for how the model should behave. The character system will plant these as the deepest memories and let personality grow organically from interactions.

## Summary style (recommended)

When ingesting, send a short stable summary (2-6 lines) covering what happened, what was decided, any stable preference learned (only if repeated), and any ongoing task state. Avoid long raw chat logs.

## Optional features

Continuity features (anchors, affect tags, mood drift, roles, character drift protection) are all **small scoring nudges**. Disable any of them if you want a pure memory store. Set `TORMENT_CHARACTER_ENABLE=0` to disable the character layer entirely.
