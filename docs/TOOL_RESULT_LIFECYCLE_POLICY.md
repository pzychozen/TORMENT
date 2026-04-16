# Tool-Result Lifecycle Policy — Audit & Proposal

**Version:** Draft 1.0
**Date:** 2026-04-07
**Phase:** Post v2.4.3 (tool-result memory lane complete)
**Scope:** Memory lifecycle only — no capability boundary changes

**Doctrine constraint:** Tool-result lifecycle policy must remain entirely inside the epistemic memory system. It must not imply freshness refresh, background re-query, scheduled updates, or any autonomous external action.

---

## 1. Audit: Current Lifecycle Behavior for Tool-Result Memories

### 1.1 Half-Life Assignment (fabric.py ingest path)

When a tool-result memory is ingested via `_fast_tool_result_ingest` → `fabric.ingest()`, the kernel processes the text and produces `KernelSignals`:

```
half_life = 20.0 + 80.0 * coherence   # range: [20, 100] days
```

Then the ingest path applies:
```
half_life_days = max(1.0, signals.half_life * decay_scale * hl_mult)
```

Where `hl_mult` comes from survival/tearing modulation (range [0.85, 1.25]).

**Finding:** Tool-result memories get the same half-life as user memories — determined entirely by the kernel's coherence assessment of the text content. A high-coherence API response (structured, clear) will get ~100 day half-life. This is semantically wrong: the *informational value* of most tool outputs (weather, prices, search results) decays far faster than personal experience.

### 1.2 Reinforcement / Dedup (fabric.py lines 2288–2326)

When a new memory is ≥0.92 similar to an existing private memory, instead of creating a new entity, the existing one is reinforced (strength asymptotically approaches 0.98, `reinforcement_count` incremented).

Provenance rule on reinforcement: existing provenance is NEVER overwritten (Rule F: no laundering). New provenance is only backfilled if the existing entity has none AND the new write is `direct_ingest`.

**Finding:** If the same tool is called twice with similar output, the second ingest will reinforce the first. The reinforcement correctly preserves the tool-result provenance. But reinforcement also *extends* the memory's effective lifetime by boosting strength, which means repeated identical tool outputs become progressively harder to compress. This is appropriate for user memories (repeated ideas = important) but questionable for tool results (repeated API calls = staleness indicator, not importance).

### 1.3 Compression Classification (compression.py `classify_retention_tier`)

The classifier assigns memories to tiers:

| Tier | Condition | Compression behavior |
|---|---|---|
| `protected` | canon=true, seed/identity kind, SRG crystal | Never compressed |
| `identity` | half_life ≥ 365 days | Only long-path (deep export) |
| `echo` | collective provenance | +15% compressibility, 0.4x short-path mult |
| `relational` | half_life ≥ 7 days | −15% compressibility, 0.7x short-path mult |
| `situational` | everything else | Default, 0.5x short-path mult |

**Finding:** Tool-result memories land in either `relational` (if coherence > ~0.85 → half_life ≥ 7) or `situational` (if lower coherence). There is no tool-result-specific tier. They are compressed at the same rate as experiential memories of the same half-life. This is the core lifecycle gap.

### 1.4 Compression Routing (compression.py `CompressionRouter.route`)

| Route | When |
|---|---|
| `long_path` (deep export) | identity tier, archive class, echo tier + old enough, high score + old enough |
| `short_path` (strength reduction) | everything else |

**Finding:** Tool results follow the default routing. No provenance-aware routing exists. A high-coherence tool result could sit in core memory for a long time before being compressed.

### 1.5 Short-Path Execution

Tier-specific strength multipliers:
- `relational`: 0.7x (gentle)
- `echo`: 0.4x (aggressive)
- `situational`: 0.5x (default)

**Finding:** If a tool result is classified as `relational`, it gets the gentle 0.7x multiplier — meaning it retains 70% of its strength after compression. This is designed for relational memories (shared social context), not for API responses.

### 1.6 Deep Memory / Spirit Return

Compressed memories exported to deep stores can return via the spirit return mechanism during retrieval. Deep memories carry no provenance-specific behavior.

**Finding:** A tool result exported to deep memory would return via spirit return exactly like a personal memory. No special handling needed here yet — spirit return is already low-weight and gap-filling.

---

## 2. Summary of Lifecycle Gaps

| Gap | Impact | Severity |
|---|---|---|
| **Half-life too long** | Tool results get 20–100 day half-life based on text coherence. Structured API output = high coherence = long half-life. Most tool outputs are informational, not autobiographical. | **High** — tool results persist as long as personal memories |
| **No compression tier** | Tool results land in `relational` or `situational` tiers. No tool-result-specific compressibility. | **Medium** — wrong decay rate, wrong short-path multiplier |
| **Reinforcement amplifies staleness** | Repeated identical tool outputs boost strength. Staleness is treated as importance. | **Low** — requires repeated ingests of same output to matter |
| **No deep routing preference** | Tool results follow default routing. No opinion on when they should exit core. | **Low** — default routing is adequate for now |

---

## 3. Policy Proposal

### 3.1 Principle

Tool-result memories have a fundamentally different epistemic character than experiential memories. A weather report, a search result, or an API response is *informational* — its value peaks at ingest and decays monotonically. Personal experience, conversation, and identity memories are *constitutive* — their value depends on resonance, reinforcement, and narrative coherence.

The lifecycle system should reflect this distinction without adding complexity.

### 3.2 Proposed Changes (Minimal, Phase-Appropriate)

#### Change A: Tool-Result Half-Life Cap

Cap the half-life for tool-result memories at ingest time. The kernel can still compute its coherence-based half-life, but for tool-result provenance, the result is clamped to a configurable maximum.

- **Location:** `fabric.py` ingest path, after `half_life_days` computation (~line 2286)
- **Default cap:** 7 days
- **Env override:** `TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS`
- **Rationale:** Most tool outputs are informational. A 7-day cap means they stay accessible for about a week, then start decaying naturally. This is generous — weather and prices are stale in hours, but search results and documentation excerpts remain useful for days. The cap can be raised per-deployment.

#### Change B: Tool-Result Compression Tier

Add a `"tool_result"` tier in the compression classifier, slotted between `echo` and `relational`.

- **Location:** `compression.py` `classify_retention_tier()`, after the echo check (~line 295)
- **Behavior:**
  - Compressibility: +10% (slightly more compressible than default, less than echo's +15%)
  - Short-path multiplier: 0.45x (between echo's 0.4x and situational's 0.5x)
- **Detection:** Check `provenance.source_type == "tool_result"` in the payload
- **Rationale:** Tool results should compress slightly faster than experiential memories but not as aggressively as collective echoes. They are the agent's own observations (not cross-agent influences), so they deserve more resistance than echoes.

#### Change C: Reinforcement Guard for Tool Results

When a tool-result memory is reinforced by a near-duplicate ingest, increment `reinforcement_count` but do NOT boost strength. Instead, update a `last_tool_refresh_ts` timestamp.

- **Location:** `fabric.py` reinforcement block (~line 2304)
- **Condition:** Only when the *existing* entity has `provenance.source_type == "tool_result"`
- **Behavior:** Update `reinforcement_count` and `last_tool_refresh_ts`, but set `_new_str = _old_str` (no strength boost)
- **Rationale:** Repeated tool output is a staleness signal, not an importance signal. The `reinforcement_count` and timestamp are preserved for debugging and future policy decisions, but the memory doesn't become harder to compress.

### 3.3 What NOT to Change

| Item | Reason to defer |
|---|---|
| **TTL / hard expiry** | TORMENT uses half-life decay, not hard deletion. Adding TTL is a new concept. Defer until there's a clear need. |
| **Deep routing preference** | Tool results can follow default routing for now. Adding a "tool results go deep after N steps" rule is premature. |
| **Spirit return exclusion** | Tool results should be returnable from deep memory. They might be useful long-term (e.g., a historical API response). |
| **Per-tool-name half-life** | Tempting (weather=1h, docs=30d) but requires a tool-name classification system that doesn't exist. Defer. |
| **Freshness detection** | "Is this tool result still fresh?" implies external checking. Hard boundary violation. |
| **Auto-refresh / re-query** | Capability boundary violation. Never. |
| **Scheduled decay sweeps** | TORMENT decays on access (retrieval scoring) and compression events. Adding scheduled sweeps is a new execution pattern. Defer. |

---

## 4. Patch Plan

### Patch 1: Tool-result half-life cap

**File:** `torment_service/fabric.py`
**Location:** After `half_life_days` computation (~line 2286), before reinforcement check

```python
# Tool-result lifecycle: cap half-life for informational memories.
# Tool outputs are observations, not experiences — their value decays faster.
if (_prov.source_type == "tool_result"
        if hasattr(_prov, "source_type") else
        (isinstance(_prov_dict, dict) and _prov_dict.get("source_type") == "tool_result")):
    try:
        _tool_hl_cap = float(os.getenv("TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS", "7"))
    except Exception:
        _tool_hl_cap = 7.0
    half_life_days = min(half_life_days, _tool_hl_cap)
```

### Patch 2: Tool-result compression tier

**File:** `torment_service/compression.py`

**2a — New constants (~top of file):**

```python
COMPRESS_TOOL_RESULT_MULT = 0.45       # short-path strength multiplier for tool results
COMPRESS_TOOL_RESULT_SCORE_MULT = 1.10  # +10% compressibility
```

**2b — Classifier (`classify_retention_tier`), after the echo check (~line 295):**

```python
# Tool result: external observation, decays faster than experiential memory
if isinstance(_prov, dict) and _prov.get("source_type") == "tool_result":
    return "tool_result"
```

**2c — Scorer (`CompressionScorer.score`), tier adjustment block (~line 483):**

```python
elif retention_tier == "tool_result":
    composite = min(1.0, composite * COMPRESS_TOOL_RESULT_SCORE_MULT)  # +10% compressibility
```

**2d — Short-path executor (`_execute_short_path`), multiplier selection (~line 646):**

```python
elif candidate.tier == "tool_result":
    mult = COMPRESS_TOOL_RESULT_MULT
```

### Patch 3: Reinforcement guard for tool results

**File:** `torment_service/fabric.py`
**Location:** Reinforcement block, after similarity check (~line 2304)

```python
# Reinforcement strength logic:
# Tool-result provenance → do NOT boost strength (staleness ≠ importance)
_existing_prov_dict = (_existing_ent.payload or {}).get("provenance")
_existing_is_tool_result = (
    isinstance(_existing_prov_dict, dict)
    and _existing_prov_dict.get("source_type") == "tool_result"
)
if _existing_is_tool_result:
    _new_str = _old_str  # no strength boost
else:
    _new_str = min(0.98, _old_str + (1.0 - _old_str) * 0.3)
```

Also add `last_tool_refresh_ts` to the reinforce updates when tool-result:

```python
if _existing_is_tool_result:
    _reinforce_updates["last_tool_refresh_ts"] = _now_ts()
```

### Patch 4: Tests

**File:** `tests/test_tool_result_lifecycle.py` (new)

- `TestToolResultHalfLifeCap` — verify tool-result memory gets half_life ≤ 7 days, verify env override
- `TestToolResultCompressionTier` — verify `classify_retention_tier` returns `"tool_result"` for tool-result provenance
- `TestToolResultCompressionScoring` — verify +10% compressibility adjustment
- `TestToolResultShortPathMultiplier` — verify 0.45x multiplier on short-path compression
- `TestToolResultReinforcementGuard` — verify reinforcement does not boost strength for tool-result memories, verify `last_tool_refresh_ts` is set

---

## 5. Deferred Items

| Item | Why deferred | When to revisit |
|---|---|---|
| TTL / hard expiry | New lifecycle concept, TORMENT uses decay | If half-life cap proves insufficient |
| Per-tool-name half-life | Needs tool classification system | When tool-name taxonomy exists |
| Deep routing preference | Default routing adequate | During deep memory routing audit |
| Spirit return exclusion | Tool results may be useful long-term | During spirit return policy review |
| Freshness detection | Implies external checking (capability violation) | Never in current doctrine |
| Auto-refresh | Capability boundary violation | Never |
| Scheduled decay sweeps | New execution pattern | If event-gated compression proves too infrequent |
| Compression tier for `tool_metadata` | Could route "ephemeral" tool results even faster | When tool_metadata schema stabilizes |

---

## 6. Doctrine Compliance

All proposed changes respect:

- **No capability boundary crossing:** Half-life cap, compression tier, and reinforcement guard are all internal memory mechanics. No external actions, no tool execution, no polling.
- **No freshness semantics:** The system does not know or care whether a tool result is "still fresh." It applies a shorter half-life because tool outputs are informational, not because they might be outdated. The distinction matters.
- **No autonomous behavior:** Compression is event-gated (triggered by kernel dynamics), not scheduled. The half-life cap applies at ingest time, not via background sweeps.
- **Provenance as read-only signal:** The lifecycle changes read provenance to make routing/decay decisions. They do not modify or generate provenance.
- **Backward compatible:** Existing tool-result memories (from v2.4.3) that were ingested without the half-life cap will naturally decay at their original rate. The compression tier will pick them up on the next compression event.

---

## Summary

Three narrow changes across two files. A half-life cap at ingest (7 days default), a dedicated compression tier (`tool_result`, slotted between `echo` and `relational`), and a reinforcement guard that prevents repeated tool output from inflating memory strength. No new dependencies, no new endpoints, no capability expansion. The lifecycle system gains provenance awareness for tool-result memories through the same patterns already established for collective echoes and identity memories.
