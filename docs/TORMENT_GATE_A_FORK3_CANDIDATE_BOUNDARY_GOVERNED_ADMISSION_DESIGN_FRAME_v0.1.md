# TORMENT Gate A — Fork 3 Candidate Boundary and Governed Admission Design Frame v0.1

## 0. Status / authorization scope

**Requirement-level design frame only. Selects no carrier, store, schema, field,
API, runtime, producer, admission implementation, or promotion implementation.
Authorizes no code or tests. Any future mechanism requires separate Hilmir
authorization plus Codex review.**

This is the Fork 3 pass that Hilmir approved opening (Tier-2 decision frame, Fork 3)
and that Codex ruled admissible **docs-only**. It answers one requirement-level
question and nothing else (see §3). It states *what must be true* of a future
candidate boundary and governed admission crossing; it does **not** state how to
build either, and it builds nothing.

Held true throughout: no production code; no tests; no git; no Gate A wall
completion; no Gate D / private cognition; no Gate B implementation; no writer
fixes; no candidate producer / store / carrier / schema / field / API / runtime
wiring; no governed admission or promotion implementation; no database / substrate;
no endpoint / API / schema expansion; no reopening of the Layer 4 brick series; no
audit/inspection turned into control; no implementation strategy selected.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.
> Automatic remains allowed only where separately ratified. Autonomous remains unopened.

Anchor: `f2658e0` (docs: record Gate A Tier-2 frame).

## 1. Subordination (and relationship to the existing requirement layer)

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md       (Document A: A-C1/A-C2/A-C3, A-O1..A-O5, A-D1/A-D2, A-I1..A-I3; §8 admission; §9 inspection)
docs/TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md      (Layer-3: boundary = property, admission = crossing condition, promotion = separate authority increase)
docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md  (wall boundary; §3 roots; §6 proof bars)
docs/TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md     (Seam B selected; Tier-1 carried; Tier-2 deferred)
docs/TORMENT_GATE_A_TIER2_ADMISSIBILITY_AND_PRODUCTION_BRICK_DECISION_FRAME_v0.1.md  (Fork 3 is this path)
```

**Relationship note (anti-duplication).** A **Layer-3 requirement contract already
exists** — `TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md` —
which keeps *candidate boundary / governed admission / promotion crossing* distinct
at requirement level. This Fork 3 frame **does not supersede, re-decide, or diverge
from it.** It **consolidates** those requirements into a single answer to the
operator's Fork 3 question (§3), restating the existing properties as that answer
(§4–§11) and **adding two things that the Layer-3 doc does not enumerate**: the
**future proof-obligation map** (§12) and the **unresolved / separately-gated list**
(§13). Where this frame and any contract above appear to differ, the contracts win.
This frame likewise sits below the Layer-1 producer-shaped contract and the Layer-2
seam-selection comparison; it selects no seam and assumes no producer.

## 2. Doctrine filter

> A candidate boundary is a containment **property**, not a place or a store.
> Admission is a governed **crossing condition**, not a procedure.
> A requirement that could only be met by violating the standing posture is out of
> scope by definition.

## 3. The question this frame answers (and only this)

```text
What requirement-level properties must a future candidate boundary and governed
admission crossing satisfy so candidate-shaped outputs remain contained,
inspectable, non-authoritative, and unable to reach ordinary cognition until
explicit governed admission, while keeping admission distinct from promotion?
```

It must not — and does not — answer *how to build it*.

## 4. Requirement-level role of a future candidate boundary

The candidate boundary is a **containment property the producer's candidate-shaped
outputs must satisfy — not a place, object, store, container, queue, or data
shape** (Layer-3 §4.1; Document A A-C1/A-C2/A-C3). Its required role:

```text
- For the WHOLE existence of a candidate-shaped output, that output remains
  non-reachable to every Document A A-C1 site (ordinary ingest fan-out root and
  everything it fans out to), held AT the ingest entry, not only at the graph.
- Non-reachability holds BY CONSTRUCTION, not by downstream readers honoring an
  exclusion tag (A-C2).
- The output remains inspectable / contestable / resettable / recoverable
  throughout, without that inspectability itself becoming a re-entry path (A-C3).
- The boundary confers NO authority and NO ordinary-memory entry by itself; it is
  the property of staying contained, nothing more.
```

## 5. Requirement-level role of a future governed admission crossing

Governed admission is the **only governed condition** under which a candidate-shaped
output may be considered for ordinary memory (Document A A-O3; Layer-3 §4.2). Its
required role:

```text
- Admission is the SOLE exit from containment into ordinary memory; no side path
  may convert a candidate (A-O3).
- An admitted output lands at NO HIGHER THAN a released / low-authority posture
  (A-D1) — a ceiling, not a guarantee of ordinary-memory entry.
- The crossing must be EXPLICIT, RECORDED, and CONTESTABLE. "Recorded" is a
  requirement only — no format, log, event, store, database, or persistence is
  selected (Layer-3 §4.2 / §5).
- Stricter per-artifact outcomes (chamber-only / audit-only / operator-visible-only
  / refused / retired) require no admission (Document A §8).
- Admission is never automatic, retrieval-driven, or reinforcement-driven; it is a
  governed decision, never a side effect of being produced, staged, inspected, or
  retrieved (Layer-3 §6).
```

## 6. How candidate-shaped outputs remain contained before admission

A property statement, no mechanism (Document A A-C1/A-C2):

```text
Before any governed admission, a candidate-shaped output must be unable to: enter
ordinary ingest or the ordinary private graph; become a motif member; shift the
drift centroid; trigger gravity_correction; feed mood_drift; shift role scores;
affect anchor cadence; be compressed or deep-exported; accrue spirit warmth; carry
SRG metadata into ordinary scoring/warmth; influence MemoryPlan lane budgets; enter
ordinary retrieval; spread into prompt-visible or caller-visible projection; reach
archive->core promotion; write canon or identity-tier material; reinforce ordinary
memories or update reinforcement/strength/last_reinforced; feed feedback / bridge /
retrieval-count / promotion-suggestion surfaces; or silently become ordinary memory
through any side path.
```

This must hold **structurally / by construction at the ingest fan-out root** (the
Seam B sole-entry terrain already characterized source-only), **not** by tag
honoring (A-C2). No containing object is named; this is the producer's output
property.

## 7. How inspection remains observation-only and cannot become control

Document A A-I1 / A-C3 / §9, carried as requirement:

```text
- Inspection may: observe, flag, record, stage.
- Inspection may NOT directly: admit, promote, change retrieval weights, change
  cognition eligibility, change prompt visibility, change persona/seed/canon state
  — unless a SEPARATE governed crossing explicitly authorizes the change.
- Inspection defaults to operator-auditable / governance-auditable visibility only;
  it is not model-/caller-/prompt-/retrieval-/MemoryPlan-visible unless separately
  surface-classified and governed (A-I1, inspection != projection).
- Inspectability must not itself be a re-entry path (A-C3).
```

This restates the audit posture the Seam B/C source-only characterizations already
lock (audit observes authority; audit does not become authority; packets drive no
branch). The boundary's inspectability inherits that non-control posture.

## 8. How candidate material remains non-authoritative before admission

```text
- A candidate-shaped output is NOT ordinary memory, NOT canon, NOT identity-tier,
  NOT seed, NOT long-half-life, and NOT cognition-eligible until a crossing changes
  its class (Document A §4 taxonomy; A-O2).
- Existence, staging, recommendation, and inspection confer NO authority
  (creation != admission; recommendation != application; staging != authority).
- No private-cognition / reflection writer may produce canon / identity-tier / seed
  / long-half-life material directly; such writes require a governed promotion
  crossing (A-O2). The four parked writer non-conformances stay parked context
  only; this frame neither fixes nor reclassifies them.
```

## 9. How ordinary cognition cannot consume candidate material before governed admission

This is §6 viewed from the consumer side: because non-reachability holds **at the
ingest fan-out root by construction** (A-C1/A-C2), ordinary cognition — ingest,
motif, drift, mood, role, deep, SRG, reinforcement, retrieval, assembly, prompt
projection — has **no path to consume** a candidate-shaped output until that output
has crossed governed admission to released / low-authority. Consumption before a
crossing would be a containment failure, not a feature. The crossing is the only
event that changes the output's class from "contained candidate" to "released /
low-authority ordinary memory."

## 10. How admission remains distinct from promotion

Document A A-D2; Layer-3 §4.3 / §5:

```text
- Admission lands at NO HIGHER THAN released / low-authority. It confers no canon
  status, no identity-shaping weight, and no unrestricted promotion rights.
- "boundary != store", "admission != procedure", "released/low-authority != schema
  or enum or field": admission is an authority-posture condition, not a
  representation and not a worked-out sequence.
- Admission and promotion are never the same crossing and never folded together.
```

## 11. How promotion remains a separate later authority decision, not implied by admission

```text
- Any move beyond released / low-authority toward identity-shaping or canon is a
  DISTINCT, separately-authorized governed promotion crossing (A-D2). It is never
  implied, triggered, or unlocked by admission.
- Any later revocation, reclassification, or reversal likewise requires its OWN
  separate governed crossing (no direct-reversal semantics).
- Promotion is an authority-posture requirement, not a mechanism; nothing here
  selects, schedules, or enables it.
```

## 12. Future proof obligations before any implementation (additive)

A future, separately-authorized implementation slice would have to **prove**, by
construction, the properties below **before any production code** — and most of
them cannot be proven until a carrier exists, so they are downstream of separate
carrier authorizations. **Stating an obligation is not authorizing the work or
selecting a mechanism.**

```text
Producer-independent (the source-only floor already reached; must compose forward):
  P-1  sole-entry shape at the ingest fan-out root holds (Seam B, characterized).
  P-2  non-reachability does not depend on exclusion tags (A-C2, characterized).
  P-3  inspection is read-only / non-reentrant; audit drives no control branch
       (A-I1/A-C3, characterized).
  P-4  no derived-cognition writer emits canon/identity silently (A-O2, characterized).

Producer-/carrier-dependent (DEFERRED — each needs a carrier this frame may not
authorize; provable only once that carrier is separately authorized to exist):
  P-5  A-C1 non-reachability AGAINST A LIVE candidate producer, by construction.
  P-6  A-C2 no-tag-dependence under that live producer.
  P-7  A-O3 / A-D1 admission is the sole exit, with the governed crossing PRESENT,
       capped at released / low-authority.
  P-8  A-D2 admission != promotion, with real staging / admission / promotion
       crossings present; reversal/reclassification needs its own crossing.
  P-9  A-C3 throughout-containment inspectability for REAL contained candidates.
  P-10 A-I2 recovery retains class (recovery != admission/promotion/eligibility).
  P-11 A-I3 contest constrains future authority but does not admit/promote/apply.

Discipline carried from Seam B/C: proofs land tests/source-first, structural where
possible, behavioral only where required, before any production wall code. This
frame writes none of them.
```

## 13. What remains unresolved and separately gated

```text
- The candidate-boundary REPRESENTATION / carrier / store / schema / serialization /
  durability — none selected; routes to Stage B / P6-shaped mechanics (Document A §11).
- The SEAM where a future wall could live — undecided (Layer-2 seam-selection
  comparison; not chosen here).
- The LIVE candidate producer — does not exist / not authorized (Document B interior).
- What AUTHORITY the governed admission crossing itself requires (operator /
  user-co-sign / governance-required) — Document A §14 OPEN; unselected.
- Per-artifact-class admission refinement (contradictions / risk-flags vs proposed
  writes) — Document A §14 OPEN.
- The Document A <-> Document B boundary for chamber-internal thread-continuity
  state — Document A §14 OPEN.
- Runtime (Layer 4), Gate D (Layer 5), database / substrate, Stage B — separately
  authorized; not entered here.
- The four parked writer non-conformances (gravity_correction canon=True,
  _maybe_emit_identity_anchor, /promote force, mood_drift -> canon) — stay parked;
  not fixed or reclassified here.
```

## 14. What this frame does and does not authorize

```text
DOES:    state requirement-level properties for a future candidate boundary and
         governed admission crossing (§4-§11); enumerate future proof obligations
         (§12); record what stays unresolved / separately gated (§13).

DOES NOT (and does not authorize by implication):
  - production code; tests; git
  - Gate A wall completion, or any claim of it
  - Gate D runtime / private cognition; Gate B implementation
  - writer fixes / reclassification of the four parked hazards
  - candidate producer; candidate store / container / queue / carrier; schema /
    enum / field / canon_source; ledger / event / record format
  - governed admission or promotion IMPLEMENTATION; any procedure / actor / trigger
    / scheduler / hook / validator / policy engine / state machine / approval flow /
    admission API / candidate id
  - database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion
  - reopening the Layer 4 brick series
  - seam binding / seam selection; any implementation strategy
  - audit / inspection turned into control; any positive authority crossing
```

## 15. Anti-drift footer

GATE A FORK 3 — CANDIDATE BOUNDARY & GOVERNED ADMISSION DESIGN FRAME / REQUIREMENT-
LEVEL ONLY / NON-AUTHORIZING / SELECTS NOTHING. It answers one requirement-level
question — candidate boundary as a **containment property**; governed admission as a
**crossing condition** that is the sole exit, explicit / recorded / contestable, and
capped at released / low-authority; inspection observation-only and never control;
candidate material non-authoritative until a crossing changes its class; ordinary
cognition unable to consume a candidate before governed admission; **admission
distinct from promotion**, and promotion a separate, separately-authorized later
crossing never implied by admission — and it **consolidates, without superseding,**
the existing Layer-3 requirements doc, adding only the future proof-obligation map
and the unresolved / separately-gated list. **Selects no carrier, store, schema,
field, API, runtime, producer, admission implementation, or promotion
implementation. Authorizes no code or tests. Any future mechanism requires separate
Hilmir authorization plus Codex review.** Gate A stays paused; Gate D parked; the
parked writer non-conformances stay parked. Guidance not control; audit observes
authority and does not become authority; nothing rewrites identity / canon / seed /
soul.
