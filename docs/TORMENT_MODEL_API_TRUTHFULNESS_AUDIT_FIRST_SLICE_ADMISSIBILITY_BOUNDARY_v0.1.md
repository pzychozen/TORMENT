# TORMENT Model-API Truthfulness Audit — First-Slice Admissibility Boundary v0.1

**Status:** DRAFT — docs-only **admissibility / feasibility boundary**. **NOT an implementation plan, NOT a slice design, NOT an implementation proposal, NOT a test plan, NOT a runtime design, NOT a model-API design.** It answers exactly one question — *"What would have to be true for a future first implementation slice to be admissible?"* — and refuses the question *"How should the slice be implemented?"*

**Baseline:** `6239b72`. Read-only. Windows repo state is authoritative.

**Lineage:** boundary frame (`444cc9b`) → §9 operator confirmation (Hilmir) → pre-implementation non-reentry constraints lock (`bb9bb16`) → Codex option-set result (B: docs-only admissibility artifact = **PASS WITH REQUIRED CORRECTIONS**; A and C = FAIL; D = later, after B + a further challenge) → this admissibility boundary (corrections applied: admissibility-conditions-only; no "how"; no design/test/runtime/provider/endpoint/schema/prompt content; the core non-reentry line stated prominently).

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, symbolic integration, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output/personality pressure.

**This artifact is governed by, and amends in no way:** the boundary frame `444cc9b`; the non-reentry constraints lock `bb9bb16`; Document B (B-O4/B-O6/B-O6.1/B-O8); P4 (non-coercion invariant; `diagnostic_only`); the Ledger Observational-Boundary (§3); the Track-A Truthfulness Envelope; the MCP Capability Boundary.

---

> ## Core forbidden line
>
> **No audit artifact, value, flag, summary, score, prompt, model output, trace, or derived signal may be read by, passed into, stored for, or honored by any runtime path outside the debug/operator observation boundary.**
>
> Every admissibility condition below exists to make this line true by construction. A future slice that cannot satisfy this line is inadmissible, regardless of any other merit.

---

## 1. What this artifact is, and is not

- It defines **admissibility conditions only** — the necessary conditions a future first slice would have to satisfy *before it could even be considered.* Failing any one renders a future slice inadmissible.
- It **does not** describe, select, or move closer to any mechanism, design, or "how." It names no code, tests, schema, field names, endpoint, file list, provider/tier, prompt text, API-call shape, runtime wiring, integration, persistence, debug-surface selection, or test-surface selection.
- It opens nothing. It is a gate's *criteria*, not the gate's opening.

## 2. Admissibility conditions

A future first implementation slice in this track is **admissible only if all of the following hold.** These are stated as conditions on admissibility, not as instructions for construction.

### C1 — Non-reentry proof requirement
A future slice is **not admissible unless it can demonstrate, by construction, that audit output has no consumer outside the debug/operator observation boundary** — i.e., that the core forbidden line above holds structurally (in the manner `reflection_trace.py` demonstrates its own non-reentry), not because any reader is trusted to honor a label. Absence of any consumer must be a demonstrable property of the wiring.

### C2 — Input minimization requirement
A future slice is **not admissible unless its inputs exclude**: seed/private/canon material; hidden chain-of-thought; raw model reasoning; whole-memory dumps; prompt-transcript reuse; durable private-cognition material; and any unbounded memory packet. Admissibility requires bounded, minimized inputs; anything beyond that is inadmissible.

### C3 — Evidence-relation-only requirement
A future slice is **not admissible unless truthfulness remains evidence relation only** — faithfulness / unsupported-claim / overconfidence relative to *available* evidence, measured against the Track-A envelope — and **never** caution, agreeableness, refusal shaping, risk scoring, voice flattening, self-silencing, or personality correction. A slice that could become a caution/agreeableness gradient is inadmissible.

### C4 — No-control requirement
A future slice is **not admissible if it can** block, rewrite, suppress, review-block, set `response_text=None`, gate a response, update a response, or guide stance / persona / output. The audit relates to an *already-produced* response and may change nothing about it.

### C5 — No-durability / no-write requirement
A future slice is **not admissible if it** writes memory, stores audit traces, creates durable raw reasoning, or opens canon / admission / promotion, an identity path, a database, a substrate, or any persistence. Admissibility requires ephemerality and zero writes.

### C6 — No provider/runtime selection (kept undecided here)
This artifact **selects none of**: provider/tier; model-call shape; endpoint; schema; prompt shape; runtime wiring; integration. Admissibility neither depends on nor pre-decides any of these — they remain **undecided**, to be neither chosen nor implied by this boundary. (A future slice that smuggles such a selection into this stage is, by that fact, inadmissible at this stage.)

### C7 — Dream / autonomy separation requirement
A future slice is **not admissible if it opens** dream / symbolic / private-cognition runtime, scheduler behavior, self-triggering, autonomy, Gate D implementation, or Envelope Audit implementation. These remain downstream-only and separately gated; an admissible first slice touches none of them.

### C8 — Required future gate
A future slice does **not become eligible to be drafted** (as tests, code, design, or mechanism) **unless**: Hilmir **explicitly selects the next step**, and Codex **adversarially challenges whether that next step preserves first-slice admissibility (C1–C7) and structural non-reentry.** Absent both, nothing advances; this artifact does not itself satisfy this gate.

## 3. How to read these conditions

These are **filters, not a roadmap.** Satisfying all of C1–C8 would make a future first slice *admissible to consider* — it would not make it designed, planned, authorized, or built. Inadmissibility under any one condition is sufficient to stop a future slice; admissibility under all of them authorizes nothing by itself.

## 4. Non-goals / still not authorized

```
No implementation.            No tests.                  No schema.
No endpoint.                  No provider selection.     No model prompt.
No API call.                  No runtime wiring.         No debug surface selection.
No persistence.               No output control.         No memory writes.
No database / substrate.      No dream / private cognition.
No participation guidance v2. No R-surface tests.
No Gate D / Envelope Audit implementation.
No model-call shape, no integration, no design of any kind.
No amendment to the boundary frame, constraints lock, Document A/B, P4, Ledger, Cluster 2, MCP boundary, or Track A.
No edit to PROJECT_ORIENTATION_MAP.md §0 until separately reviewed.
```

This document changes nothing and recommends nothing. It states the conditions under which a future first slice *could* be considered admissible — so that structural non-reentry, input minimization, evidence-relation-only truthfulness, no-control, and no-durability are settled as admissibility gates **before** any design question is ever asked, and so that provider/runtime/endpoint/schema choices remain undecided.

*End — TORMENT Model-API Truthfulness Audit First-Slice Admissibility Boundary v0.1. Draft for trio steering; admissibility conditions only; no implementation, design, mechanism, schema, runtime, model call, provider, or endpoint. Dream downstream only; seed/private/canon parked; the §C8 future gate (Hilmir select + Codex challenge) is the sole path onward.*
