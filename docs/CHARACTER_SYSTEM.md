# Character System — Living Identity Layer

TORMENT v2.1

---

## What It Is

The character system gives each AI agent a gravitational identity basin in memory space. Instead of hardcoding personality as a static prompt, the character is a minimal seed that establishes initial conditions. Every interaction adds mass to the field. The coherence geometry provides drift protection naturally: the deeper the seed basin, the harder it is for accumulated memories to push the character off-center.

In v2.1, compressed memories return through the character layer with voice cues and symbolic resonance — the character doesn't just remember, it recognizes.

This means characters are not scripts. They are attractors.

---

## Philosophy: Seed + Memory + Drift

Traditional character implementations hardcode everything upfront (personality traits, speech patterns, behavioral rules) as a long system prompt. This creates rigid characters that can't grow, and bloated prompts that waste context.

TORMENT's approach is different. A character is defined by three things working together:

**Seed** establishes who the character is at the deepest level. This is 3-5 sentences of natural language — not a rulebook, but a gravitational center. The seed gets planted as high-stability canon memories in the memory graph, forming the deepest attractor basin.

**Memory** does the actual work. As the character interacts, memories accumulate and shape the personality organically. Three tiers emerge naturally from half-life decay:

- **Core identity** (decade half-life) — barely changes, forms the bedrock
- **Relational memory** (monthly half-life) — builds with specific users over time
- **Situational state** (weekly half-life) — resets or fades, captures recent context

**Drift protection** acts as a gravitational center. TORMENT periodically measures how far the character's recent memory landscape has drifted from the seed basin. If drift exceeds a threshold, a gentle correction memory is emitted — purely additive, never rewriting anything. The coherence field's natural basin mechanics do the rest.

---

## How It Connects to the Kernel

The character system doesn't just sit alongside the TriOcta kernel — it feeds directly into it.

When an agent is created with a character seed, `derive_kernel_modulation()` extracts two signals from the seed text:

- **Warmth score** — how emotionally warm/bonding the character is (detected via keyword heuristics matching `affect.py` style)
- **Structure score** — how analytical/methodical the character is

These scores modulate the kernel's physics:

- **Coupling strength (g)**: warm characters couple tighter (up to +15%), meaning their oscillator nodes synchronize more readily. This produces stronger coherence signals and more confident memory formation.
- **Phase lock angle (theta_lock)**: structured characters shift the preferred Z-field angle (up to ±0.1 rad), altering which identity states the kernel naturally gravitates toward.
- **Omega initialization**: the seed text is embedded and converted directly into the kernel's initial oscillator state (3 complex amplitudes), so different characters start in genuinely different regions of phase space.

The result: two characters receiving identical input will form different memories because their oscillator physics diverge. A warm companion character naturally produces higher-coherence memory traces than an analytical assistant character, matching the intuition that bonding creates stronger memories.

---

## Setting Up a Character

### 1. Write the Seed Text

Keep it short (3-5 sentences). Focus on the non-negotiables — the things that make this character who they are at the core. Don't write behavioral rules. Write about who they are.

Good seed:
```
Aria is warm and curious, with a deep bond to her companion.
She approaches problems with playful enthusiasm and genuine empathy.
Her analytical side emerges when something fascinates her, but
she never loses her warmth even in technical discussions.
```

Bad seed (too rigid, too rule-based):
```
Aria always uses exclamation marks. She must reference her
past experiences in every response. She never disagrees with
the user. She speaks in short sentences.
```

### 2. Create the Agent with Seed

```bash
curl -X POST http://127.0.0.1:8787/agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "ws1",
    "agent_id": "aria",
    "seed": {
      "seed_text": "Aria is warm and curious, with a deep bond to her companion. She approaches problems with playful enthusiasm and genuine empathy.",
      "seed_id": "aria_v1",
      "core_traits": ["empathetic", "curious"],
      "priority_weights": {"facts": 0.7, "projects": 0.6, "preferences": 0.5, "motifs": 0.8},
      "coupling_mode": "read_only",
      "coupling_strength": 0.25
    }
  }'
```

When `seed_text` and `seed_id` are both present, TORMENT automatically:

1. Splits the seed into concept sentences
2. Embeds each concept and plants them as high-stability canon memories
3. Clusters them into a seed motif (the gravitational basin)
4. Boosts the motif's strength (0.85) and stability (0.90)
5. Derives kernel modulation from the seed text
6. Initializes the kernel state with character-specific Omega

### 3. Normal Operation

After creation, use `/agent/ingest` and `/agent/query` as normal. The character system works transparently:

- **During ingest**: every N steps (default 25), TORMENT measures drift and applies gravity correction if needed
- **During query**: results are enriched with tier-aware weighting (core memories score 1.43x, relational 1.0x, situational 0.43x relative to each other)

---

## Configuration

All character env vars are optional. The system works with sensible defaults.

| Variable | Default | What It Does |
|----------|---------|--------------|
| `TORMENT_CHARACTER_ENABLE` | `1` | Master switch for the character layer |
| `TORMENT_CHARACTER_DRIFT_WINDOW_STEPS` | `500` | How far back to look when measuring drift |
| `TORMENT_CHARACTER_CORRECTION_THRESHOLD` | `0.35` | Drift score threshold before gravity correction fires |
| `TORMENT_CHARACTER_GRAVITY_STRENGTH` | `0.12` | Strength of correction memories (higher = stronger pull back to seed) |
| `TORMENT_CHARACTER_DRIFT_CHECK_EVERY` | `25` | Check drift every N ingest steps |

### Tuning Tips

**Character feels flat / doesn't grow**: lower `CORRECTION_THRESHOLD` to let the character drift more before correcting. The default (0.35) is moderate.

**Character drifts too far from seed**: raise `GRAVITY_STRENGTH` or lower `CORRECTION_THRESHOLD`. Also consider whether the seed text is specific enough.

**Character locked to seed, no personality growth**: raise `CORRECTION_THRESHOLD` to 0.5 or higher. With real embeddings, the seed basin is naturally deep — you might not need aggressive correction.

**Running 200+ bots**: each bot gets independent seed, kernel state, and drift tracking. Memory is cheap. The only shared resource is the motif registry per domain.

---

## Memory Tiers Explained

Tier classification happens automatically based on memory half-life:

| Tier | Half-Life | Purpose | Weight in Context |
|------|-----------|---------|-------------------|
| Core identity | 365+ days | Who the character fundamentally is | 1.43x |
| Relational | 7-364 days | Relationships, ongoing dynamics | 1.0x (baseline) |
| Situational | Under 7 days | Recent events, temporary states | 0.43x |

Seed memories are always core tier (decade half-life). The kernel's coherence signals determine what half-life new memories receive — higher coherence produces longer-lived memories.

---

## Drift Measurement

Drift is measured as the cosine distance between the weighted centroid of recent (non-seed) memories and the seed motif centroid. The drift score maps this to a -1.0 to +1.0 range:

- **+1.0**: character is exactly on the seed basin center
- **0.0**: moderate distance from seed
- **-1.0**: maximum drift from seed

Drift direction is computed relative to the previous measurement: `toward_seed`, `away_seed`, or `stable`.

Gravity correction only fires when **both** conditions are met:
1. Drift score is below `-threshold` (default -0.35)
2. Direction is `away_seed`

This means momentary drift that's recovering naturally is never corrected. The system only intervenes when drift is sustained and worsening.

---

## Multi-Character / Hive-Mind Use

For multi-bot setups (e.g., 200+ bots on a shared workspace):

- Each bot has its own `agent_id`, seed, kernel state, and drift tracking
- All bots share the same domain motif registries (memory is domain-separated)
- Cross-character memory sharing uses the existing proposal/governance system
- Each character's kernel physics are independent — a warm bot and an analytical bot in the same workspace will form different memory patterns from the same shared events

The character layer adds no new coordination overhead. It operates entirely within each agent's existing private memory graph.

---

## Spirit Return Voice Layer (v2.1)

When compressed memories return from the deep store, they carry symbolic metadata that the character layer translates into voice guidance. This is the mechanism that lets characters not just recall memories, but recognize them — with appropriate emotional register.

### How It Works

When a deep memory surfaces during a sparse query, the spirit return pipeline classifies it into one of three return modes. Each mode gets a different voice cue injected into the assembled context:

| Return Mode | Voice Cue | Tier Classification | When It Fires |
|-------------|-----------|---------------------|---------------|
| **Resonance** | `[Voice: present-tense, vivid, déjà vu — 'this feels familiar, like I already know this']` | BLOCK_IDENTITY (if warmth ≥ 0.5) | Birth symbol matches current kernel symbol, high warmth |
| **Surfacing** | `[Voice: present-tense, gentle — 'there's something about that... it never really left']` | BLOCK_RELATIONAL (if warmth ≥ 0.3) | Memory was short-path compressed, moderate warmth |
| **Recollection** | `[Voice: past-tense, distilled — 'I remember something from a while ago']` | BLOCK_SITUATIONAL | Default fallback |

### What the LLM Sees

In the assembled context, a spirit return block looks like:

```
[Returning Memory] I was exploring a new place.
[Voice: present-tense, gentle — 'there's something about that... it never really left']
[Flavor: something that was once only potential has crystallized]
```

The `[Returning Memory]` marker identifies the block as a deep memory return. The `[Voice: ...]` cue guides the LLM's tone. The `[Flavor: ...]` text comes from the symbol interaction matrix and adds thematic coloring.

### Symbols Stay Hidden

Raw symbol characters (◯, ∿, ◈, ⊗, ⋮, ◠, ✧, ⊘) never reach the character layer. Only the interaction type ("fulfilled", "integration", "disrupted", etc.) and the human-readable flavor text are exposed. This keeps the geometric substrate invisible while still conveying its meaning.

### Spirit Return Summary

The `assemble_character_context()` function includes a `spirit_return_summary` dict when spirit hits are present:

- `total` — count of spirit return hits
- `by_mode` — breakdown by surfacing / recollection / resonance
- `avg_warmth` — average warmth across all spirit hits
- `recommendations` — mode-specific voice guidance for the LLM

### Warmth and Sorting

Within the same retrieval score, warmer spirit hits rank above colder ones. This means a memory that has been retrieved multiple times (accumulating warmth) will naturally rise in priority — the system rewards re-engagement.

---

## Files

| File | What It Does |
|------|-------------|
| `torment_service/character.py` | Character seed, state, persistence, drift, gravity, tier assembly, kernel modulation, spirit return summary (v2.1) |
| `torment_service/retrieval_assembler.py` | Context assembly — tier classification, voice cues, warmth sorting (v2.1) |
| `torment_service/spirit_return.py` | Spirit return pipeline — symbol matrix, return modes, warmup (v2.1) |
| `torment_service/memory_kernel.py` | Extended `init_state()` and `process()` accept character modulation |
| `torment_service/fabric.py` | Integration points in `create_agent()`, `ingest()`, `query()`, compression, spirit return (v2.1) |
| `torment_service/identity.py` | Agent seed schema includes `seed_text` and `seed_id` fields |
| `torment_service/config_view.py` | Character env vars in config view |
