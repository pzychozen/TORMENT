# Spirit Reflection — Developer Notes (v1)

> For the full design document covering both spirit return and reflection, see **[SPIRIT_RETURN_AND_REFLECTION.md](SPIRIT_RETURN_AND_REFLECTION.md)**. This file focuses on practical limitations and developer guidance for working with the reflection pipeline.

## What This Is

Spirit reflection is a **post-response write-back loop** for TORMENT Phase 7. When a spirit return memory materially influences a generated response, the reflection pipeline creates a **derived record of the event** — not a copy of the original memory.

This records temporal continuity: "a memory came back and mattered." It does NOT resurrect, duplicate, or mutate any existing memory.

## What This Is NOT

- **Not identity mutation.** Reflections do not alter character seeds, drift vectors, or identity context precedence.
- **Not deep memory rewrite.** Original deep memories are never touched. The reflection is a separate artifact in separate storage.
- **Not resurrected originals.** The reflection summary describes the *event of return*, not the content of the original memory.
- **Not a recursive feedback loop.** Reflections have `eligible_for_spirit_return = False` and `generation_depth = 1`. They cannot feed back into spirit return or spawn further reflections. This is enforced at deserialization (from_dict forces False regardless of what's on disk).
- **Not automatic.** The caller must explicitly invoke the `/spirit-reflections/process` endpoint after generating a response. If they don't call it, nothing happens.

## Current Limitations

### Heuristic Influence Scoring Is Approximate

The influence scorer uses a weighted combination of:

- Lexical overlap (40%) — Jaccard-ish recall of candidate summary tokens in response text
- Concept alignment (30%) — flavor words and mode-related language detection
- Warmth bonus (15%) — warmer memories get a boost
- Resonance mode bonus (15%) — resonance returns get +0.15

This is intentionally simple and conservative for v1. Known weaknesses:

- **Short responses** may have high incidental overlap with any summary
- **Generic emotional vocabulary** ("remember", "familiar") may trigger false positives
- **Paraphrased influence** where the response uses different words for the same concept will be missed
- **Structural influence** where a spirit return shapes the *structure* of a response rather than its vocabulary is invisible to this scorer

The threshold (0.30) is tuned to prefer false negatives over false positives.

### Reflections Cannot Currently Influence Anything

v1 reflections are pure observability artifacts. They are stored, they can be queried, but nothing reads them for decision-making. This is intentional — the system needs to prove it can *record* accurately before it should be allowed to *act* on reflections.

### No Embedding for Reflections

Reflection events are stored as structured JSONL, not embedded. They cannot be retrieved via vector similarity. This is correct for v1 — reflections are not query targets.

### Cooldown Is Step-Based, Not Time-Based

The cooldown window (50 steps) counts agent interaction steps, not wall-clock time. In low-activity agents, a 50-step cooldown could span days. In high-activity agents, it could be minutes. This is acceptable for v1 but may need attention in production.

## Architecture Decisions

### Separate Storage

Reflections live in `data/agents/{agent_id}/spirit_reflections/reflections.jsonl`, completely separate from `deep_memory/`. This prevents any accidental contamination of the original memory store.

### Post-Response Endpoint (Not Inline Hook)

The reflection pipeline is a separate endpoint (`POST /spirit-reflections/process`) rather than being wired inline into `/retrieve` or `query()`. Reasons:

1. The pipeline needs the **response text**, which doesn't exist until after the LLM generates it
2. Fail-soft by design — if the endpoint breaks, the caller's response flow is unaffected
3. The caller controls when/whether to invoke it
4. No modification to any existing retrieval or assembly path

### Conservative Anti-Echo

The anti-echo system is deliberately strict:

- `eligible_for_spirit_return = False` — hardcoded, tamper-resistant
- `generation_depth` capped at 1 — no meta-reflections
- Cooldown by `source_eid:mode:interaction` composite key — prevents the same return event from reflecting repeatedly even if it stays in assembled context across turns
- Influence threshold — weak influence doesn't get recorded
- Duplicate suppression — same source + same step blocked

A healthy v1 should **reject most candidates**. If acceptance rates are above 30%, the threshold is too loose.

## Diagnostics

- `GET /workspace/{workspace_id}/spirit-reflections/status?agent_id=X` — returns total count, mode distribution, average influence, and last 10 reflections
- `POST /workspace/{workspace_id}/spirit-reflections/process` — returns stored reflections + store stats per call
- The store's `stats()` method gives: total_reflections, unique_sources, avg_influence, mode_counts

## Test Coverage

- 31 unit tests (`test_spirit_reflection.py`) covering all 4 stages + storage + end-to-end
- 12 integration tests (`test_spirit_reflection_integration.py`) covering fail-soft, persistence, precedence, and tamper resistance
- All tests pass with no dependency on live data or FastAPI

## What Comes Next (NOT Yet)

These are future possibilities, explicitly **not implemented** in v1:

- Influence scoring with semantic embeddings (requires embedding infra)
- Reflection-aware context assembly (reflections influencing retrieval weights)
- Multi-step warmth tracking for reflections (warmth of the reflection itself)
- Reflection-to-reflection chains (generation_depth > 1)
- Identity-level reflections (character seed evolution based on reflection patterns)

None of these should be built until v1 has been observed in real usage and rejection/acceptance rates are understood.
