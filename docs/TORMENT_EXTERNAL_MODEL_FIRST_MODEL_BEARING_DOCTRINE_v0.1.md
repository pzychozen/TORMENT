# TORMENT — External-Model-First / Model-Bearing Doctrine v0.1

**Status:** DOCS-ONLY doctrine / operator decision record. **Non-authorizing, non-implementing. Opens no
implementation lane.** Records the operator decision that TORMENT remains **external-model-first for now**
and hosts **no internal model runtime**. External / edge model calls may be *framed* later under separate
gates; this doc authorizes no implementation. It resolves the *direction* of the Live-Power Doctrine's
**Surface 2 (model-bearing)** first sub-question — external-call vs internal-host — without opening the gate.
`PROJECT_ORIENTATION_MAP.md` §0 remains the active work-order; §0 wins unless Hilmir explicitly overrides.

**Decision (carried, exact):**

> **TORMENT remains external-model-first for now. It does not host an internal model runtime. Calling an
> external / edge model may be framed later under a separate gate, and never authorizes hosting an internal
> runtime. This decision opens no implementation lane.**

---

## 1. Purpose

To fix, at requirement level, *where model generation may ever live* relative to TORMENT — outside it (an
external / edge model that TORMENT may one day call) versus inside it (a hosted internal runtime) — and to
record that, for this phase, the direction is **external-first** and internal hosting stays closed. This is
a direction decision, not a build decision.

## 2. Decision

**TORMENT remains external-model-first for now.** Any live generation, if ever wired, comes from an
**external / edge model** that TORMENT calls under a future separate gate. TORMENT **does not host an
internal model runtime** in this phase. The current ceiling is unchanged: **memory/context floor + Mode 0**.

## 3. The split — external/edge interaction vs internal hosted runtime

- **External / edge model interaction** *(direction chosen; still gated, not opened):* TORMENT may, under a
  future separately-authorized gate, send governed context (and possibly, under further separate gates,
  bounded sensory input) to an external model and receive output. This remains **framing-only** here — no
  provider, endpoint, prompt path, or call is built.
- **Internal hosted model runtime** *(HOLD):* TORMENT hosting/embedding a model that generates inside the
  system. **Not chosen, not opened.** Calling an external model **never** authorizes hosting an internal
  runtime — these are distinct gates, and the external choice does not bootstrap the internal one.

## 4. What remains allowed now

Nothing new is opened. The standing allowances hold: memory/context **retrieval**; **context/retrieval
shaping only** (never final output or truth); **audit, observability, advisory** behavior; **Mode 0**
automatic-only service behavior; **MCP as a read/advisory memory-context surface only**.

## 5. What may be framed later (NOT authorized)

Under future, separate gates — each requiring an explicit operator decision plus Codex challenge, and none
authorized here: **external / edge model calls**; a governed **context-to-external-model** hand-off shape;
bounded sensory input to an external model (subordinate to the Typed Embodiment Tunnels' input rung and its
own gate). **Framing is not authorization.**

## 6. What remains HOLD

Internal model runtime / hosting; provider wiring; prompt paths; scheduler / trigger / budget loops;
background watchers; generic MCP / tool action; OS-level input; perception-to-action loops; durable memory
writes; substrate / admission mechanics; Dream runtime; Document B chamber runtime; Gate D / Envelope-Audit
runtime; embodiment implementation; identity / canon / personhood authority; final-output / finalizer /
refusal authority.

## 7. No implementation lane opened

This document is decision framing only. It opens **no implementation lane**, wires **no provider**, builds
**no prompt path**, and authorizes **no** runtime, model call, model host, tool action, OS input, loop,
memory write, substrate/admission mechanic, or any runtime surface. Every model-bearing move remains closed
until a separate, explicit operator decision — with Codex challenge — chooses to open it.

## 8. Relation to the Live-Power Doctrine / Model-Boundary Ceiling

This is the **first partial resolution of Surface 2 (model-bearing)** in
`docs/TORMENT_LIVE_POWER_DOCTRINE_MODEL_BOUNDARY_CEILING_v0.1.md`: it chooses the **external-first
direction** and keeps internal hosting closed, while preserving the lattice rule — **no surface authorizes
another; generation authorizes no autonomy, action, embodiment, durable write, or finalization.** It changes
no other surface and does not lift the ceiling.

## 9. Relation to Typed Embodiment Tunnels

Per `docs/TORMENT_TYPED_EMBODIMENT_TUNNELS_EFFECT_SCOPE_LADDER_v0.1.md`: **embodiment tunnels do not
authorize model hosting.** A future external model driving a body would call TORMENT's typed tunnels; the
tunnels remain sealed, effect-scoped, executor-enforced channels regardless of where the model lives.
**Future vision / body / game control is separate sensorimotor-loop / autonomy work** — bounded by the
tunnel rungs, and **tunnel permission is never loop permission**: any perception-to-action loop is a
separate autonomy gate (ceiling stays Mode 0). This doc grants none of it.

## 10. Relation to carrier / substrate / admission

Infrastructure remains **orthogonal and non-authorizing.** Nothing here opens or requires carrier,
substrate, database, schema, or admission mechanics, and building any of them would **never** grant
external-model calls, internal hosting, or any model-bearing capability. Eligibility is not authorization.

## 11. Relation to Dream / Document B / Gate D / Envelope Audit

All remain **HOLD as live runtime surfaces.** External-model-first authorizes **no** Dream runtime, Document
B chamber runtime, Gate D runtime, or Envelope-Audit runtime, and implies no self-trigger, scheduler,
budget, or background loop. Any offline reflection ("dreaming") remains, if ever opened, **externally
triggered and inert-candidate-producing only** — a separate gate, not implied here.

## 12. Relation to identity / personhood / final output

This doc grants **no identity / canon / personhood authority** and **no finalizer / refusal / output
authority.** An external model producing text or expression does not thereby gain authority over user truth,
memory truth, canon, or final output; those axes remain closed (Live-Power Doctrine, closed authority axes).
Character presence, if ever expressed, stays **non-authoritative texture**, never canon.

## Verdict

**EXTERNAL-MODEL-FIRST RECORDED — NO INTERNAL MODEL RUNTIME / EXTERNAL CALLS FRAMEABLE-LATER UNDER SEPARATE
GATE / NO IMPLEMENTATION LANE OPENED / CEILING STAYS MEMORY/CONTEXT FLOOR + MODE 0 / FORMAL HOLD PRESERVED.**

## Semantic summary

TORMENT's direction for the model-bearing surface is now recorded as **external-model-first**: live
generation, if ever wired, comes from an **external/edge model TORMENT calls** under a future separate gate,
and **internal model-runtime hosting stays HOLD** — with the external choice explicitly *not* bootstrapping
the internal one. Nothing is built: no provider, prompt path, call, runtime, loop, memory write, substrate,
or embodiment. It resolves only the **direction** of Live-Power Surface 2, preserves the lattice rule (no
surface authorizes another), keeps embodiment tunnels / vision / body-control as separate
sensorimotor-loop/autonomy gates, keeps carrier/substrate non-authorizing, keeps Dream / Document B / Gate D
/ Envelope-Audit HOLD, and grants no identity/canon/personhood or final-output authority. Ceiling unchanged:
memory/context floor + Mode 0. **Decision framing only — opens no implementation lane.**

*End — External-Model-First / Model-Bearing Doctrine v0.1. Docs-only, decision framing, non-authorizing.
Opens no implementation lane.*
