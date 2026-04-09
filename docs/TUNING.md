# TORMENT — Tuning Guide

v2.1

TORMENT is meant to be adaptable. Use `TORMENT_PROFILE` for presets, then override individual knobs.

## Presets

- `TORMENT_PROFILE=companion` — strong continuity + emotional guidance + guardrails
- `TORMENT_PROFILE=minimalist` — lighter continuity, fewer identity features
- `TORMENT_PROFILE=assistant` — balanced
- `TORMENT_PROFILE=hive` — multi-agent leaning (still safe by domain)

Inspect with `GET /profiles` and `GET /config`.

## Character tuning (v2.0)

### "Character feels flat / doesn't grow"
Lower the correction threshold to let the character drift more before pulling back:
- `TORMENT_CHARACTER_CORRECTION_THRESHOLD` (default `0.35`, try `0.50`)

### "Character drifts too far from seed"
Strengthen the gravity pull:
- `TORMENT_CHARACTER_GRAVITY_STRENGTH` (increase from `0.12`)
- `TORMENT_CHARACTER_CORRECTION_THRESHOLD` (decrease from `0.35`)

### "Don't want character features at all"
- `TORMENT_CHARACTER_ENABLE=0`

### "Running many bots"
Each bot has independent seed, kernel state, and drift tracking. The only shared resource is the domain motif registry. No extra tuning needed for multi-bot setups.

## Continuity knobs (common)

### "Make it remember *me* more"
Increase:
- `TORMENT_SELF_MEMORY_BONUS`
- `TORMENT_THREAD_WINDOW_STEPS`
- `TORMENT_THREAD_WINDOW_BONUS`

### "Anchors are too frequent / too sticky"
Increase:
- `TORMENT_ID_ANCHOR_MIN_COUNT`
- `TORMENT_ID_ANCHOR_MIN_GAP_STEPS`

Reduce:
- `TORMENT_ANCHOR_BOOST_TOPK`
- `TORMENT_SELF_ANCHOR_BONUS`

### "Don't turn moods into identity"
Keep enabled:
- `TORMENT_MOOD_SPIRAL_ENABLE`
- `TORMENT_ID_ANCHOR_AFFECT_COUNT_MULT`
- `TORMENT_ID_ANCHOR_AFFECT_GAP_MULT`

### "Less emotional guidance"
Reduce or disable:
- `TORMENT_AFFECT_MATCH_BONUS`
- `TORMENT_MOOD_DRIFT_QUERY_BONUS`
- `TORMENT_AFFECT_ENABLE=0`
- `TORMENT_MOOD_DRIFT_ENABLE=0`

## Compression tuning (v2.1)

### "Compression not firing"
Compression requires `TORMENT_COMPRESS_ENABLE=1` and a corridor transition event. If the kernel stays in a stable corridor forever, compression won't trigger.
- `TORMENT_COMPRESS_ENABLE=1` — master switch (default `0`)
- `TORMENT_COMPRESS_MIN_STEP=100` — earliest step for compression (lower for faster start)
- `TORMENT_COMPRESS_MIN_AGE=50` — minimum memory age before eligible (lower for more aggressive compression)

### "Too many memories compressed"
Raise the protection floor:
- `TORMENT_COMPRESS_MIN_AGE` (increase to protect younger memories)
- `TORMENT_COMPRESS_DEEP_THRESHOLD=0.7` — only memories scoring above this go to long-path. Higher means fewer deep exports.

### "Sustained memories getting compressed"
Duration resistance is built-in (memories born in corridors ≥10 steps get j_score -0.15). If this isn't enough, consider raising `TORMENT_COMPRESS_MIN_AGE`.

### "Emergency compression too sensitive"
- `TORMENT_COMPRESS_TEAR_EMERGENCY=0.7` — raise to reduce false emergencies

## Spirit return tuning (v2.1)

Spirit return has no dedicated env vars — it activates automatically when `TORMENT_COMPRESS_ENABLE=1` and deep store has memories. Tuning happens through the warmup constants in `spirit_return.py`:

- **WARMTH_FLOOR** (0.2): starting warmth for first retrieval. Lower = colder initial returns.
- **WARMTH_INCREMENT** (0.15): warmth gained per retrieval within the window. Lower = slower warm-up.
- **WARMTH_WINDOW_STEPS** (400): retrieval must happen within this window to count. Larger = more forgiving.
- **WARMTH_CAP** (1.0): maximum warmth. Could lower if returns feel too strong.
- **SUSTAINED_CORRIDOR_THRESHOLD** (10): corridor duration needed for warmth floor boost. Lower = easier boost.
- **SUSTAINED_WARMTH_FLOOR** (0.3): boosted warmth floor for sustained memories.

### "Spirit return feels too frequent"
This is usually because deep store has many memories and queries are sparse. Increase `top_k` on queries to fill the private hit budget, leaving less room for deep fallback.

### "Spirit return voice feels wrong"
Voice cues are deterministic per return mode. Check which mode is firing by looking at `spirit_return_mode` in query results. Resonance should be rare (requires symbol match + high warmth).

## Debugging what the system is doing

Use `POST /agent/query` with `continuity_debug=true`. If you see an unwanted bonus dominating, tune the corresponding knob down.

## Embeddings (quality vs speed)

- `hash` provider: deterministic, testing, lowest quality
- `st` provider: better semantics (recommended for production)
- `ollama` provider: local endpoint, easy integration with existing stacks

Use `GET /embedder/check` to validate your configuration quickly.

Note: character seeds work best with real embeddings. Hash embeddings produce orthogonal vectors, so seed concepts won't cluster naturally — the system still functions, but semantic relationships between seed concepts won't be captured.
