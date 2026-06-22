# TORMENT — SRG R-Surface Authority-Fencing Inventory v0.1

**Status:** DRAFT — docs-only boundary inventory, returned for GPT / Hilmir steering. **Not promoted, not committed as authority, not a gate, not a registry entry, not doctrine.** Selects no mechanic, authorizes no code, proposes no remedy, opens no audit scope.

**Baseline:** clean HEAD `d8a65e3`. Read-only.

**Lineage:** R-field fork proposal (source-grounded) → Codex ACCEPT WITH CORRECTIONS → this inventory (Codex corrections applied, see §1).

**Purpose.** This is **not "opening R-field."** It is a source-grounded inventory of the SRG **R-surface** signals that *already* influence the live system, so those existing surfaces remain **ethical memory guidance, not control**. It records what exists and draws the fence; it changes nothing.

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output / personality pressure.

---

## 1. Codex corrections applied (verbatim discipline)

This inventory is written under the following corrections; each is load-bearing wording, not paraphrasable:

1. **Gating is not a single env flag.** New SRG payload production and retrieval scoring are gated by `fabric._srg_enable`, but downstream readers can honor existing `payload["srg"]` metadata if present. **Compression, lifecycle/protected derivation, and spirit-return read the payload, not the environment flag directly.**
2. **Raw-`R` consumer, qualified.** Compression is the **only direct runtime scoring/retention consumer of raw `R`**; `R` is also **mutated by SRG breathing/collision helpers**.
3. **Confirmed split (held).** Raw `R` has **no retrieval-scoring consumer at this HEAD**. Retrieval scoring uses `R_band`, `is_crystal`, and `heartbeat_class`, **not raw `R`**.
4. **`is_crystal` is broader than retrieval/spirit-return.** It also participates in protected / lifecycle / compression surfaces: **`srg.is_crystal` can make a row protected / never compressed.**
5. **Boundary-bearing.** `is_crystal → resonance → BLOCK_IDENTITY` is a **prompt-placement and continuity-force** inventory item, not harmless exploration.
6. **Compression resistance is fenced.** Resistance must **not** be described as permanence, canon, identity truth, unrevisability, or entitlement to future retrieval.

---

## 2. What an "R-surface" signal is

SRG (`torment_service/srg_engine.py`) gives each memory a per-memory dual-field state (`SRGMemoryState`): a resonance field **R** ("what the memory is") and a compression field **L** ("who the memory is to"). This inventory fences the **R-surface family** the trio named:

- **`R`** — raw resonance scalar. Seeded `R = float(strength)` at ingest (`build_memory_srg`, `srg_engine.py:446`); crystal state pins `R = R_STAR ≈ 0.176` (`create_crystal_state`, `srg_engine.py:343`).
- **`R_band`** — golden-tower band index (`assign_band`); crystal → band 2.
- **`is_crystal`** — center-crystal (seed/identity) flag.
- **`heartbeat_class`** — `"A"` (slow/deep) / `"B"` (fast/active) / `"crystal"`.

`L` / `L_amplitude` are **out of scope** here (the relational `L_amplitude → social_resonance` advisory chain is separate and already live); this document fences only the R-surface.

---

## 3. Existing consumers (source-grounded inventory)

The table records **current** behavior at HEAD `d8a65e3`. No consumer is added, removed, or re-weighted by this document.

| Consumer surface | Reads | File / function | Gating | Effect (descriptive) |
|---|---|---|---|---|
| **Ingest payload construction** | builds `R, R_band, is_crystal, heartbeat_class` | `fabric.py` ingest → `srg_engine.build_memory_srg`; stored as `payload["srg"]` | `fabric._srg_enable` (production) | Writes the SRG payload; sets per-agent `_srg_last_ingest_band_by_agent[(ws, agent)]` |
| **Retrieval multipliers** | `R_band`, `is_crystal`, `heartbeat_class` | `fabric.py` query rescore (SRG multipliers) | `fabric._srg_enable` | Same-band ×1.08 / crystal ×1.05 / heartbeat-A ×1.03 on `final` |
| **Trace parity** | `R_band`, `is_crystal`, `heartbeat_class` | `fabric.py` `trace()` `explain_for_hit`; `test_trace_srg_parity.py` | `fabric._srg_enable` | Mirrors retrieval multipliers read-only; surfaces `srg_*` fields in `explain` |
| **Breathing / collision writeback** | mutates `R` (and `L`) | `srg_engine.evolve_breathing` (`R → R_STAR`), `srg_engine.collision` (`equilibrium_shift` on `R`); evolved state written back to payload at retrieval | `fabric._srg_enable` | Converges `R` toward the fixed point; collision nudges `R` |
| **Compression scoring / protection** | `is_crystal`, `heartbeat_class`, raw `R` | `compression.py:625-637` (`payload.get("srg")`) | **reads payload, not env flag** | `is_crystal` → `return None` (never compressed); heartbeat-A → ×0.85; `R > 0.15` → ×(1 − 0.1·min(1, R/0.176)) resist |
| **Lifecycle / protected derivation** | `is_crystal` | `lifecycle.py` `derive_protected_lifecycle_from_legacy_markers` (`:982-986`), precedence `canon > kind > tier > srg.is_crystal > governance.protected` | **reads payload, not env flag** | `srg.is_crystal` truthy → `SRG_CRYSTAL` via → PROTECTED lifecycle envelope (one of five legacy protected markers) |
| **Spirit-return mode / warmth** | `is_crystal`, `heartbeat_class` | `spirit_return.py:358-366` | reads payload | `is_crystal` → forced resonance; `heartbeat_class == "A"` → +0.15 warmth floor |
| **Identity-block classification** | resonance mode (from `is_crystal`) | `retrieval_assembler.py` echo classification (`BLOCK_IDENTITY`) | reads upstream mode | forced resonance → highest-precedence identity-context block at assembly |

**Confirmed split (Codex #3):** none of the **retrieval-scoring** rows read raw `R`; they read `R_band` / `is_crystal` / `heartbeat_class`. Raw `R`'s only **direct runtime scoring/retention** consumer is compression (Codex #2), and `R` is additionally **mutated** by the breathing/collision helpers.

**Gating note (Codex #1):** SRG *production* and *retrieval scoring* are gated by `fabric._srg_enable`. But **compression, lifecycle/protected derivation, and spirit-return read `payload["srg"]` if present** — so a row that already carries SRG metadata can be honored by those readers independent of the environment flag's current value.

---

## 4. Boundary-bearing item: `is_crystal → resonance → BLOCK_IDENTITY`

This chain is recorded as **boundary-bearing** (Codex #5), not as harmless metadata:

- `is_crystal` (set on seed/identity memories) forces **resonance** return mode in spirit-return (`spirit_return.py:358-366`), which classifies the echo into the **highest-precedence identity-context block** at assembly (`retrieval_assembler.py`).
- This is a **prompt-placement** effect (which block a memory lands in, and thus its inclusion priority under token budget) and a **continuity-force** on placement (the crystal flag persists, so the same memory keeps being placed there).

**Fence (descriptive, not a remedy):** highest-precedence block classification raises *placement priority*; it is **not** identity authority, **not** canon, **not** a guarantee of inclusion (token budget and per-block caps still apply), and **not** an unrevisable status. Placement is guidance. It must never be read as the memory holding authority over identity, nor as a lock that prevents the agent from revising or moving away from that memory.

---

## 5. Compression-resistance fence

`is_crystal` (never compressed), heartbeat-A (×0.85), and raw `R > 0.15` (graded resistance) reduce a memory's eligibility for compression (`compression.py:625-637`). Per Codex #6, this resistance is fenced explicitly:

Compression resistance means **only** that a row is less eligible to be compressed at this step. It does **not** mean, and must not be described or used as: permanence, canon status, identity truth, unrevisability, or any entitlement to future retrieval, placement, or authority. A resistant memory remains revisable, contestable, and subject to ordinary governance; resistance is a retention-eligibility weight, nothing more. Continuity is preserved; compulsion is not.

---

## 6. What this inventory holds (the fence, restated)

- **No new consumption.** No surface reads any R-surface signal that it does not already read at HEAD `d8a65e3`.
- **No implementation. No tests. No behavior change. No authority change. No database/substrate.**
- **No audit scope opened.** Surfaces here overlap the *named-but-unopened* spirit-return / retrieval-stack audit scopes (Guidance-Without-Coercion surface map #5 / #13); this inventory **does not open** either.
- **This is fencing current surfaces, not opening R-field.** The R-surface signals are recorded as **existing memory guidance** to be kept guidance — not promoted toward control, identity authority, output shaping, or stance.

---

## 7. What this does NOT authorize

```
No opening, activating, or expanding R or any R-surface signal.
No new consumer of R / R_band / is_crystal / heartbeat_class (retrieval, stance,
  personality, output, or private cognition).
No change to retrieval multipliers, compression scoring/protection, lifecycle
  protected derivation, spirit-return mode/warmth, or identity-block placement.
No reading of raw R into retrieval scoring.
No treatment of is_crystal as canon, identity authority, or unrevisable status.
No treatment of compression resistance as permanence or entitlement.
No tests, no probe, no remedy, no patch, no implementation.
No database / substrate / migration.
No edit to PROJECT_ORIENTATION_MAP.md or any registry (pending separate review).
```

This document changes nothing and recommends nothing. It fences existing SRG R-surfaces so a later evaluation, if ever separately ratified, audits reality and keeps memory in the role of guidance rather than control.

*End — TORMENT SRG R-Surface Authority-Fencing Inventory v0.1. Draft for trio steering; not promoted, not authority, no gate, no fork opened.*
