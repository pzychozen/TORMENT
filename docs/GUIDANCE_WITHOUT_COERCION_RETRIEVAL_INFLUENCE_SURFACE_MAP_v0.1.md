# Guidance Without Coercion — Existing Retrieval Influence Surface Map v0.1

**Status:** Tracked framing artifact. **Descriptive map of existing behavior only.** Not doctrine. Not a standard. Not an audit verdict. Not a remedy. Not a patch proposal. Not an implementation gate. Not a retrieval-stack gate. Not Track B coupling authorization. No fork selected. No probe authorized.
**Date:** 2026-06-05
**Author:** Claude (drafter), for the trio (Hilmir as operator + GPT review + Codex adversarial review).
**Review lineage:** Claude surface-map pass → GPT merge-point trace → Codex adversarial rounds (ACCEPT WITH REQUIRED REVISIONS ×2: precision corrections + terminology corrections) → operator promotion (Hilmir, 2026-06-05).
**Audit baseline:** resting checkpoint `8d948f7`. Read-only.

## Status and non-authorization banner

```
DESCRIPTIVE MAP OF EXISTING BEHAVIOR ONLY.

Not doctrine. Not a standard. Not an audit verdict. Not implementation
authorization. No patch recommended. No removal recommended. No remedy
selected. No new symbolic coupling proposed. No Track B coupling authorized.
No retrieval-stack gate opened. No fork selected. No probe authorized.

Track B remains parked. This artifact records what the live system already
does so that any later "Guidance Without Coercion" evaluation audits reality,
not a sketch. It applies no judgment and proposes no change.
```

## Purpose

To fix, in tracked form, the retrieval-influence surfaces that already exist in the live system — their inputs, what they touch, and where they accumulate — at resting checkpoint `8d948f7`. The map exists so a future evaluation has an accurate ground truth. The perception / exit / revision frame is named here only as the lens a *later* audit would apply; it is deliberately **not** applied as judgment in this document.

## Existing-system posture

The live system already shapes retrieval and assembler/client model-visible context through several deterministic, default-on mechanisms. The most relevant is a **deep-memory echo** lane (spirit return): semantically selected deep-memory candidates are enriched with a symbolic interaction (the memory's *birth symbol* against the kernel's *current symbol*), which is **positive-only** (mismatch yields `confidence_boost = 0.0`, never a penalty; `spirit_return.py:251-256`) and bounded. That enrichment sets a return mode and strength, can classify the echo into the highest-precedence identity block, contributes a warmth-based secondary ordering inside its assigned block bucket, and injects model-visible voice-cue and flavor text. The main private/shared scoring path reads no symbol data. None of this is a finding *against* the system; it is the system as built.

## Corrected influence-surface map

Columns — **Obs**: observational-only · **Elig**: changes candidate eligibility · **Ord**: changes ordering · **Class**: changes block classification · **Txt**: changes model-visible text · **Accum**: accumulates across turns · **Drive**: what makes it move over time · **Insp**: operator-inspectable · **On**: default-on · **Bucket**: I (immediate spirit-return audit) / P (parked retrieval-stack audit).

| # | Surface (file:line) | Input | Obs | Elig | Ord | Class | Txt | Accum | Drive | Insp | On | Bkt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `symbols.py:66-183` watermark projection | coherence geometry at ingest | writes only | N | N | N | N | Y (`last_symbol`/trace persisted `fabric.py:346-371,2902-2966`) | geometry per ingest | Y | Y | I |
| 2 | `resonance.py:49-210` trace analytics | `symbol_trace` | **Y** | N | N | N | N | N (stateless) | — | Y | Y | I (low) |
| 3 | `spirit_return.py:107-256` interaction matrix | birth x current symbol | N | N | indirect | indirect | Y (flavor) | via 4 | current-symbol drift + warmth | partial | Y | I |
| 4 | warmth: `get_or_create` `spirit_return.py:498-529` (called `fabric.py:3712`) + `compute_warmth` `spirit_return.py:296-321` | candidate appearance in enrichment | N | **N** (does not affect semantic selection) | **Y** (via strength + via 10) | Y (via mode) | Y (via mode) | **Y** | **candidate-appearance warmth recursion** (note A) | Y (warmup persisted) | Y | **I** |
| 5 | `spirit_return.py:358-366` SRG metadata consumption | `srg` meta: `is_crystal`, `heartbeat_class` | N | N | Y (via mode/strength) | Y (forced resonance) | Y | N (static flags) | `is_crystal` -> forced resonance; `heartbeat_class==A` -> +0.15 warmth-floor | Y | Y | **I** |
| 6 | `spirit_return.py:392-410` strength mapping | return_mode + warmth | N | N | **Y** (strength = 0.6/0.4/0.1 x warmth) | carries mode | indirect | via 4 | via 4 | Y (hit fields) | Y | I |
| 7 | `fabric.py:3655-3716` `_query_deep_lane` | semantic deep query -> enrichment | N | **N for symbol** (candidates semantically selected first; beta source-row filter is separate) | Y (downstream) | feeds asm | Y downstream | via 4 | via 4 | partial | Y (deep stores present) | I |
| 8 | `fabric.py` query merge / rescore | all lanes + `score_hit` + bonuses | N | top-k per lane | **Y** (deep-echo strength enters `score_hit` alpha*strength) **[INFERENCE]** | N | N | reinforcement / warmth | reinforcement = usage-tuned; warmth = recursion | partial (debug) | Y | **P** (whole stack); deep-strength slice = I |
| 9 | `retrieval_assembler.py:144-185` echo classification | `from_spirit_return` + mode | N | N | **Y downstream** — warmth is a secondary within-bucket sort key after classification (see 10) | **Y** (resonance -> `BLOCK_IDENTITY`, `:166-174`) | inclusion *not guaranteed* (note B) | via 4 | via 4 | Y (block_type) | Y | **I** |
| 10 | `retrieval_assembler.py:438-442` block-bucket secondary sort | each bucket sorted `(b.score, warmth_score)` desc | N | N | **Y** (direct secondary ordering key) | N (consumes classification) | indirect (sort affects which survive block cap) | via 4 | warmth (note A) | Y | Y | **I** |
| 11 | `retrieval_assembler.py:193-285` voice-cue + flavor | mode + flavor | N | N | N | N | **Y** (`[Voice: ...deja vu...]`, `[Flavor:]`) | via 4 | via 4 | Y (visible) | Y | **I** |
| 12 | `retrieval_assembler.py:334-348,421` seed drift injection | `drift_info` (when supplied) | N | N | N (seed first `:53-58`) | in identity block | **Y, conditional** (`[Drift: score=..., direction=...]` only `if drift_info`) | drift evolves | interaction-evolved drift | Y | Y (character on, drift_info present) | **P** (prompt-surface, with P6) |
| 13 | `fabric.py:4198-4205` SRG score multipliers | `srg` meta: `R_band`, `is_crystal`, `heartbeat_class` | N | N | **Y** (x1.08 same-band / x1.05 crystal / x1.03 heartbeat-A) | N | N | N | ingest band match; static flags | Y | Y (`_srg_enable`) | **P** |

**Correction / grounding notes:**

- **Note A (surface 4, 10) — candidate-appearance warmth recursion. [FACT]** `WarmupTracker.get_or_create()` "increments the appearance count and recomputes warmth" on every call (`spirit_return.py:498-529`, increment at `:521-523`), invoked once per deep candidate during enrichment (`fabric.py:3712`) — **before** final rescore, lane filtering, prompt inclusion, model acknowledgment, successful use, or operator confirmation; per-appearance warmth math is in `compute_warmth` (`spirit_return.py:296-321`). Warmth is therefore **retrieval-recursive, not model-output-tuned**, and it does **not** change semantic deep-lane candidate *selection* (selection happens first). Its recursion is **post-selection**: appearing again raises warmth, and warmth raises *post-selection treatment* — strength (surface 6), return-mode classification (surface 9), and the secondary within-bucket sort key (surface 10). (Distinct from `reinforcement_count`, surface 8, which is usage-tuned.)
- **Note B (surface 9) — classification != ordering != inclusion. [FACT]** Classification itself is not ordering: a resonant deep-memory echo with sufficient warmth is *classified* into the highest-precedence `identity_context` bucket (`FILL_ORDER`, `:53-58`). Selected spirit-return blocks then *separately* participate in warmth-based secondary ordering **inside** their assigned block bucket (surface 10). And **prompt inclusion is not guaranteed**: token budget and per-block selection via the per-block token budget computed from `PROFILES` weights (`budget_per_block`, `:104-131,447-449`) still apply. Highest-precedence classification plus a warmth-favoured within-bucket position raises inclusion priority; it does not force inclusion.
- **Note C (surfaces 2-13) — "deep-memory echo," not "archived memory." [FACT]** Spirit-return hits are a distinct **deep lane**; they are not the `BLOCK_ARCHIVE` archive-context bucket. The map uses "deep-memory echo" throughout.
- **Note D (surfaces 5 vs 13) — SRG is split by scope. [FACT]** Surface 5 (immediate) is the spirit-return SRG *metadata consumption* (`is_crystal` -> forced resonance; `heartbeat_class==A` -> +0.15 warmth-floor, `spirit_return.py:358-366`). Surface 13 (parked) is the separate `fabric.py:4198-4205` *score multipliers* (`R_band` x1.08 / `is_crystal` x1.05 / `heartbeat_class==A` x1.03). The immediate spirit-return audit scope does not absorb the broader scoring-stack multipliers.

## Immediate spirit-return audit scope (named, not opened)

The surfaces that together constitute the deep-memory-echo influence path: **1, 3, 4, 5, 6, 7, 9, 10, 11** (watermark origin -> symbol interaction -> warmth -> SRG-metadata mode forcing -> strength -> deep lane -> classification -> warmth-based secondary ordering -> voice cue).

- **FACT:** the path is live, default-on, positive-only, bounded, reads birth-symbol against the kernel's current symbol, and includes a confirmed direct warmth-based secondary within-bucket ordering key at assembly (surface 10, `retrieval_assembler.py:438-442`).
- **IMMEDIATE CONCERN (descriptive):** the **candidate-appearance warmth recursion** (surface 4) is self-referential in the *post-selection* sense — appearing again as a semantically selected candidate raises warmth; warmth raises strength, return-mode/identity classification, and within-bucket sort position; which **raises future post-selection prominence when the memory appears again** — and it accumulates without model use or operator confirmation in the loop. It does **not** change semantic candidate selection. A later audit would examine this property under the perception/exit/revision lens; this document only records that the property exists.
- **IMMEDIATE CONCERN (descriptive):** symbolic state can change *block classification* into the highest-precedence bucket (surface 9) and then warmth orders within it (surface 10), and the deep-echo voice-cue/flavor text is prescriptive posture language reaching the assembler/client model-visible context (surface 11). Recorded as facts about reach; no judgment applied here.
- **INFERENCE:** that deep-echo strength reorders the *final merged* result via the unified rescore (surface 6->8) is reasoned and externally confirmed but not personally traced to the sort. (Note: the assembler within-bucket warmth ordering at surface 10 is **FACT**, not inference; the inference concerns only the cross-lane rescore.) The warmth threshold gating `resonance` mode lives in `select_return_mode` (`spirit_return.py:259+`), not fully read.

## Parked broader retrieval-stack audit scope (named, not opened)

- **PARKED CONCERN (descriptive):** the general scoring stack — surface 8 unified rescore, the **surface 13** SRG band/crystal/heartbeat *score multipliers* (`fabric.py:4198-4205`), reinforcement boost (`fabric.py:4185-4191`), collective discount (`scoring.py:328-350`), and the `mood_spiral_penalty` congruence *penalty* (`scoring.py:238-251`).
- **PARKED CONCERN (descriptive):** model-visible numeric injections — `[Drift:]` (surface 12) and the score/tier/provenance tags already documented as P6 — as an assembler/client model-visible-context sub-scope.

These are recorded for completeness and explicitly left closed.

## Open questions (unanswered, descriptive)

```
- Under what frame should candidate-appearance warmth recursion (post-selection)
  be evaluated?
- Should symbolic state be able to change block classification and within-bucket
  ordering, or neither? (question, not a proposal)
- How should prescriptive deep-echo cue language be characterized under a later
  standard?
- Do operator-layer numeric values (drift score, hit score, tier, provenance)
  belong in assembler/client model-visible context? (ties to P6)
- Does deep-echo strength's participation in the unified rescore (INFERENCE)
  need a dedicated read-only trace to confirm the cross-lane ordering effect?
```

## Explicit non-goals

```
No patch. No removal. No scoring change. No classification change. No
within-bucket-sort change. No cue rewording. No warmth-recursion change. No
doctrine verdict. No new symbolic coupling. No Track B coupling. No
retrieval-stack gate. No fork. No probe. No remedy of any kind. This artifact
changes nothing and recommends nothing.
```

## Stop condition

```
The map is complete for this draft scope after the listed live surfaces are
named.

Two audit scopes are named; neither is opened.
Track B remains parked.
No remedy is selected.
The next step, if any, is a separate ratified decision to OPEN one named
audit scope — not taken here.
```

---

*End of Guidance Without Coercion — Existing Retrieval Influence Surface Map v0.1. Tracked framing artifact (operator promotion, Hilmir, 2026-06-05). Descriptive map of existing behavior; not doctrine, not authorization, no remedy, no gate, no fork, no Track B coupling. Subsequent versions require their own ratification before they supersede this one.*
