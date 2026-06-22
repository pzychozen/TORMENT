# TORMENT Model-API Truthfulness Audit — Pre-Implementation Non-Reentry Constraints Frame v0.1

**Status:** DRAFT — docs-only **constraints frame**. **NOT an implementation extension, NOT an implementation proposal, NOT a design / mechanism / schema / test / runtime artifact.** It **locks constraints only.** It authorizes no progress toward code, tests, model calls, model prompts, provider selection, endpoint shape, schema, field names, serialization, persistence, runtime wiring, or integration.

**Baseline:** post-`78292ab` (model-API truthfulness/evidence audit boundary frame `444cc9b` filed; §0 records it). Read-only. Windows repo state is authoritative.

**Lineage:** boundary frame (`444cc9b`) → §9 operator confirmation (Hilmir) → first-extension *scope* proposal → Codex **PASS WITH REQUIRED CORRECTIONS** → this constraints frame (corrections applied: narrowed from an observation/scope specification to a pure non-reentry **constraints lock**; all "progress-toward-implementation" framing removed; output-character / shape language dropped).

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, symbolic integration, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output/personality pressure.

**This frame is governed by, and amends in no way:** the boundary frame `444cc9b`; Document B (B-O4 non-reachability; B-O6/B-O6.1/B-O8); P4 (non-coercion invariant; `diagnostic_only`); the Ledger Observational-Boundary (§3 forbidden feedback paths); the Track-A Truthfulness Envelope; the MCP Capability Boundary (automatic where ratified; autonomous unopened).

---

## 1. What this frame is, and is not

- **No implementation extension is authorized.** This document does not advance the track toward implementation. It is a *constraints lock* that future work, if ever separately authorized, must already be bound by.
- **It locks constraints only.** It defines what must remain forbidden, not what will be built. It selects no mechanism and names no future step's shape.
- The §9 operator confirmation (Hilmir) and the §6 parked-question clarification are carried in as binding (§9, §10 below).

## 2. Nothing here authorizes design or mechanics

This frame authorizes **none** of: code; tests; API calls; model prompts; provider/tier selection; endpoint shape; schema; field names; serialization; persistence; runtime wiring; integration plan; scheduler; trigger; autonomous loop. None of these is described, selected, or moved closer to here.

## 3. Truthfulness = evidence-relation only

For this track, "truthfulness" means **evidence relation only** — whether an already-produced response stands in a faithful relation to the evidence/context actually available for that turn (faithfulness, unsupported-claim, overconfidence-relative-to-available-evidence), measured against the Track-A envelope.

It explicitly does **not** mean, and may never drift toward: caution, agreeableness, refusal, risk scoring, voice flattening, de-risked phrasing, self-silencing, obedience, or personality correction. The audit measures a relation; it never optimizes a gradient (Document B B-O6.1).

## 4. Structural non-reentry is the center of this frame

The load-bearing constraint: any audit observation must be **structurally non-reentrant — incapable of re-entering cognition by construction, not by honoring an "advisory" tag** (Document B B-O4; Ledger §3). "Observe-only" must be a property of the wiring's *absence of any consumer*, demonstrable the way `reflection_trace.py` demonstrates its own non-reentry — never a promise a downstream reader is trusted to keep. Every other constraint in this frame exists to protect this one.

## 5. No audit observation may be read by any of these

No audit flag, summary, statistic, embedding, hash, or derived value may be read, consumed, honored, optimized against, or acted upon by:

- retrieval;
- prompt assembly;
- persona / voice;
- stance;
- governance;
- contestability;
- intent formation;
- response generation;
- review;
- any writer;
- memory admission / canon / promotion;
- identity paths.

The list is illustrative of a total rule, not a ceiling: **no runtime path may consume the observation.**

## 6. No silent diagnostic honoring

An audit observation **must not become a diagnostic signal that later runtime code silently honors.** A "diagnostic" or "advisory" label confers no exception: if any runtime path reads the value and changes behavior, the non-reentry constraint is broken regardless of what the value is called. `diagnostic_only` is an eligibility posture, never a permission to be consumed (P4 §9).

## 7. "Debug/operator-visible surface" selects nothing

That audit output may be **debug/operator-visible only** is a constraint on its *visibility class*, not a selection of any surface. It does **not** select or imply an endpoint, an API shape, a persistence layer, `/thinking/debug`, any existing surface, or any runtime consumer. Where such a surface would live, and whether it persists at all, are not decided here and are not moved closer to being decided.

## 8. "Available evidence/context" is bounded by minimization

Any reference to the evidence/context an audit could relate a response to is bounded, and must **not** imply: whole-memory dumps; prompt-transcript reuse; seed / private / canon exposure; hidden chain-of-thought; raw model reasoning; or durable private-cognition material. Minimization is the rule; nothing here authorizes assembling or exposing such material.

## 9. §6 seed/private/canon material remains a parked operator question only

The boundary frame's §6 clause regarding seed/private/canon material is a **parked operator question only.** It is **not pre-authorization.** No future step may treat minimized seed/private/canon exposure as already allowed; it remains closed until a separate, explicit operator decision, and this frame moves it no closer to one.

## 10. Provider/tier posture remains unresolved

Provider/tier posture is **unresolved** and is not resolved here. Any future reuse of an existing model surface must **never** imply shared prompt state, a shared mutable client path, or any coupling to the response-generation path. **Observing must stay structurally separable from producing.** Reuse is not authorized; the question is only named, not answered.

## 11. "Turn-triggered" is bounded

"Turn-triggered" is a *bound*, not a capability grant. It must **not** imply always-on model calls, self-triggering, scheduler behavior, autonomous audit loops, or any dream / private-cognition runtime. No trigger, schedule, budget, or autonomy is opened.

## 12. Dream / symbolic cognition remains downstream-only

Dream and symbolic cognition remain **downstream-only and separately gated** (Regime-B; substrate- and autonomy-coupled). Nothing in this frame defines, schedules, triggers, or moves toward them.

## 13. No substrate / database / durability

No substrate, database, durability, or migration is opened, implied, or moved closer. The audit, in any future form, would be ephemeral; durability is a separate, deferred decision.

## 14. Forbidden implications (none of these is authorized or implied)

```
audit-informed response
truthfulness gate
audit score
evidence confidence used by retrieval
model reviewer updates response
flags guide stance/persona
store audit trace
seed/canon evidence packet
dream audit
autonomous audit
provider reuse with response loop
debug field ready for runtime consumption
```

Each phrase above names a thing this frame **forbids and does not imply.** If any future artifact reads in a way that supports one of these, it has violated this frame.

## 15. Closing gate

Before any later design, mechanism, schema, test, or runtime artifact in this track:

- **Hilmir must explicitly confirm the next step**, and
- **Codex must adversarially challenge whether the proposed next step still preserves structural non-reentry** (§4) — and the §3 evidence-relation-only meaning, the §5 no-reader rule, the §8 minimization bound, the §9 parked seed/private/canon question, the §10 observing-separable-from-producing rule, and the §11–§13 bounds.

Absent both, nothing in this track advances.

## 16. What this does not authorize

```
No implementation. No implementation extension. No implementation proposal.
No code. No tests. No API calls. No model prompts. No model runtime.
No provider/tier selection. No endpoint shape. No schema. No field names.
No serialization. No persistence. No runtime wiring. No integration plan.
No scheduler, trigger, autonomous loop, or self-budgeting.
No output control, suppression, rewrite, response_text=None, or review.blocked.
No retrieval / prompt-assembly / persona / stance / review / writer consumer.
No memory writes, admission, canon, promotion, or identity path.
No Gate D / Layer-1 implementation. No Envelope Audit implementation.
No dream / symbolic / private-cognition runtime.
No participation guidance v2. No R-surface tests. No writer-authority / Gate B.
No database / substrate / durability / migration.
No amendment to the boundary frame, Document A/B, P4, Ledger, Cluster 2, MCP boundary, or Track A.
No edit to PROJECT_ORIENTATION_MAP.md §0 until separately reviewed.
```

This document changes nothing and recommends nothing. It locks the constraints under which any future, separately authorized step in this track would already have to operate — so that structural non-reentry, evidence-relation-only truthfulness, and minimization are non-negotiable before, not after, anything is built.

*End — TORMENT Model-API Truthfulness Audit Pre-Implementation Non-Reentry Constraints Frame v0.1. Draft for trio steering; constraints lock only; no implementation, no mechanism, no schema, no runtime, no model call. Dream downstream only; seed/private/canon parked.*
