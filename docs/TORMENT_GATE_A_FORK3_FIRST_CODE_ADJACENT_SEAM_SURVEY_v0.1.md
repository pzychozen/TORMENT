# TORMENT Gate A — Fork 3 First Code-Adjacent Seam Survey v0.1

## 0. Status / authorization scope

**Archaeology-only. This report identifies whether a future code-adjacent seam may
be considered; it selects no seam for implementation, writes no tests, authorizes no
code, and creates no carrier, schema, enum, field, ID, API, runtime, producer,
admission workflow, promotion mechanism, or authority option. Any tests or code
require separate Hilmir authorization plus Codex review.**

This is the Option-3 archaeology pass Codex selected: a read-only survey for the
**smallest** future code-adjacent seam that could bear a future inert /
called-nowhere helper or a tests-only lock **while preserving all Fork 3
boundaries** and selecting nothing. It answers one question (§3) and ends with one
of two conclusions (§7).

Held true throughout: no production code; no tests; no git; no carrier / store /
schema / field / enum / ID / API / runtime / persistence; no producer; no governed
admission; no promotion; no authority-option selection; no Gate A wall completion;
no Gate D; no Gate B writer implementation; no writer fixes; no database / substrate;
no endpoint expansion; no Layer 4 reopening; no audit-as-control; no identity / canon
/ seed / tier writes; no hidden output control.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `9cbd3cb` (origin/main; Gate A Fork 3 per-artifact admission refinement recorded).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md
docs/TORMENT_GATE_A_FORK3_WALL_SEAM_SELECTION_FRAME_v0.1.md            (layered topology)
docs/TORMENT_GATE_A_PRE_CARRIER_REPRESENTATION_CONSTRAINTS_FRAME_v0.1.md   (representation unbuilt; inert)
docs/TORMENT_GATE_A_FORK3_PER_ARTIFACT_ADMISSION_REFINEMENT_FRAME_v0.1.md  (outcomes are NOT enums/schema)
docs/TORMENT_GATE_A_LAYER4_CONTAINMENT_BRICK_SERIES_CLOSURE_v0.1.md    (five negative bricks closed; CandidateShapedValue inert-by-construction)
```

Where this report and any contract appear to differ, the contracts win.

## 2. Method (what counts as a safe code-adjacent seam)

Two move-types are already-precedented as boundary-preserving in this codebase, and
are the only shapes a future seam could safely take:

```text
- TESTS-ONLY / SOURCE-ONLY characterization (precedent: Seam B aa7befd, Seam C 6895b8e):
  pins existing behavior via AST/source reads; changes no production; selects nothing.
- INERT / CALLED-NOWHERE production helper (precedent: candidate_types.py CandidateShapedValue;
  audit_evidence_packet.py / audit_private_generation_owner.py — added but called nowhere in production):
  an inert artifact with no producer, no store, no wiring.
```

A safe seam must trip **none** of the seven risk axes in §4. Anything that would
require a carrier, schema/enum/field, admission workflow, producer, authority
selector, runtime/API/persistence, or promotion/writer-authority is unsafe by the
Fork 3 boundaries and is rejected.

## 3. The exact question

```text
Which existing code surface, if any, could support a future inert / called-nowhere
helper OR tests-only lock while preserving all Fork 3 boundaries and selecting no
carrier / store / schema / field / enum / ID / API / runtime / persistence /
admission / promotion?
```

## 4. Candidate surfaces surveyed + risk classification

Risk axes: **CAR** carrier · **SCH** schema/enum/field · **ADM** admission-workflow ·
**PRD** producer-boundary · **AUT** authority-selector · **RAP** runtime/API/persistence ·
**PWA** promotion/writer-authority. ( `—` = no risk; `X` = trips the axis. )

```text
# Surface (read-only evidence)                          CAR SCH ADM PRD AUT RAP PWA  Verdict
--+-----------------------------------------------------+---+---+---+---+---+---+---+--------
S1 candidate_types.py :: CandidateShapedValue            —   —   —   —   —   —   —   SAFE (anti-drift lock only; §5)
   (existing inert, sealed, called-nowhere type)
S2 a NEW inert "candidate outcome / admission outcome"   X   X   X   —   X   —   —   REJECT
   type or enum reifying C1-C4 / the outcome categories
S3 a NEW inert "representation / candidate boundary"     X   X   —   X   —   X   —   REJECT
   helper (CandidateBoundary / store-shaped object)
S4 the five Layer-4 guard sites (fabric.ingest text,     —   —   —   X   —   X   X   REJECT (for new code)
   spawn_memory summary/extra_payload, EnvironmentStore
   .write value, ReferenceStore.ingest fields)
S5 postponed surfaces: spawn_memory `links`,             X   —   —   X   —   X   X   REJECT
   MemoryGraph.update_payload, ArchiveStore.ingest_document
S6 promotion.py promote_chunk / app.py /promote          —   —   X   —   X   X   X   REJECT
   (force route, canon write)
S7 app.py endpoints (any new handler/field)              X   X   X   —   —   X   —   REJECT
S8 a NEW inert "admission / governed-crossing" helper    X   X   X   X   X   X   X   REJECT
S9 tests-only re-lock of audit owner/bridge unwired      —   —   —   —   —   —   —   REDUNDANT (already locked; not Fork-3-specific)
   / Seam B perimeter footprint
```

## 5. Why each rejected surface is unsafe (or redundant)

```text
S2  candidate-outcome type/enum — reifying C1-C4 or admit/refuse/retire/audit-only/
    chamber-only as a TYPE or ENUM selects a schema/enum/field (SCH) and an
    outcome-carrier (CAR), encodes an admission vocabulary (ADM), and starts to fix the
    authority-bearing outcome surface (AUT). The per-artifact frame explicitly held these
    as requirement-level CATEGORIES, NOT enums/schema. Forbidden.
S3  representation / candidate-boundary helper — the pre-carrier frame holds the
    representation UNBUILT and the boundary a containment PROPERTY, not a store/object. Any
    new boundary-shaped helper is a carrier (CAR), implies a producer to fill it (PRD), and
    edges toward persistence/runtime (RAP). Forbidden.
S4  the five Layer-4 guard sites — new code here reopens the Layer 4 brick series and is
    writer-adjacent (PWA) and producer-presupposing (PRD/RAP). Tests-only re-locking is
    already done by Seam B (perimeter carry-forward); more is redundant, and any helper is
    unsafe. Forbidden as a NEW seam.
S5  postponed surfaces (links / update_payload / ArchiveStore) — the seam-selection frame
    classified these as proof-scope dependency questions, NOT targets; a guard/helper here
    is a second brick series (CAR/PRD/RAP/PWA). Seam B already asserts they stay unguarded.
    Forbidden.
S6  promote_chunk / /promote — writer-authority / Gate B territory; the force route is a
    parked non-conformance. Touching it is a writer fix + authority selection (ADM/AUT/RAP/
    PWA). Forbidden; stays parked.
S7  app.py endpoints — any new handler/field is endpoint/API/schema expansion (CAR/SCH/ADM/
    RAP). Forbidden.
S8  admission / governed-crossing helper — trips every axis: it is the crossing mechanism
    itself (carrier + schema + admission + producer + authority + runtime + promotion).
    Maximally forbidden.
S9  re-lock of audit owner/bridge unwired or the Seam B footprint — safe but REDUNDANT:
    already locked by the audit-lane tests and Seam B T4; adds nothing Fork-3-specific.
```

## 6. The one safe candidate (S1) — inertness anti-drift lock only

`[FINDING]` The single surface that trips **no** risk axis is the **existing inert
`CandidateShapedValue` in `candidate_types.py`** — and only as the subject of a
future **tests-only / source-only inertness anti-drift lock**, never as a build or
carrier selection.

```text
Why it is safe (it characterizes the ABSENCE of every forbidden property):
  - CAR  none — it is a sealed structural marker, not a store/container; the lock asserts it
                STAYS carrier-less.
  - SCH  none — no schema/enum/field is added; the lock asserts no fields/accessors exist.
  - ADM  none — no admission vocabulary; the lock asserts no admission/crossing surface.
  - PRD  none — Document A / the module docstring already state "Nothing in production
                constructs it"; the lock asserts no producer constructs it.
  - AUT  none — no authority option; the lock asserts it confers no authority.
  - RAP  none — no runtime/API/persistence; the lock asserts no serialization/persistence/
                endpoint reference.
  - PWA  none — no promotion/writer path; the lock asserts it reaches no writer surface.

Why it does NOT contradict "representation unbuilt / not a target":
  The target is an ANTI-DRIFT lock that the inert type STAYS inert — the opposite of
  building it into a carrier. It reinforces the pre-carrier constraints by turning the
  "must not become" anti-properties into an executable regression guard on the one concrete
  inert artifact they already govern. It does NOT select CandidateShapedValue as the
  carrier, extend it, or give it a producer.

Exactly one future tests-only characterization target (named, NOT authorized, NOT code):
  >> a tests-only / source-only inertness anti-drift lock asserting that
     `CandidateShapedValue` (and `candidate_types.py`) preserves the pre-carrier
     representation anti-properties — no producer constructs it; no accessor / serialization
     / persistence; no admission / promotion / authority surface; referenced ONLY by the
     classified Layer-4 perimeter modules (candidate_types + the five guard modules);
     remains a structural marker only. <<

  This is a single, producer-independent, carrier-free regression guard. It is a DEFENSIVE
  anti-drift lock, NOT forward progress on the wall (the Tier-2 bars remain
  carrier/producer-dependent and deferred). The operator may still legitimately prefer HOLD.
```

## 7. Conclusion

**Conclusion 2 — One candidate seam is admissible for a future tests-only
characterization.**

```text
The single safe seam is S1: the existing inert CandidateShapedValue, as the subject of a
future TESTS-ONLY / SOURCE-ONLY inertness anti-drift lock (named in §6) — and nothing else.
All other surveyed surfaces (S2-S8) are unsafe under the Fork 3 boundaries, and S9 is
redundant. This is admissible to CONSIDER; it is not authorized here. It remains a
defensive regression guard, not a Tier-2 step; HOLD stays a legitimate alternative.
```

## 8. Not authorized / future proof obligations

```text
NOT AUTHORIZED by this report: any test or code; selecting CandidateShapedValue (or anything)
as the carrier/representation; a candidate producer / store / carrier / schema / enum / field /
ID / API / runtime / persistence; governed admission or promotion; an authority option; Gate A
wall completion; Gate D; Gate B writer implementation; writer fixes; database/substrate;
endpoint expansion; reopening the Layer 4 brick series; audit-as-control; identity/canon/seed/
tier writes; hidden output control.

FUTURE PROOF OBLIGATIONS (for a future, separately-authorized tests-only lock — stating them
authorizes nothing):
  - it must be tests-only / source-only (AST/source reads), changing no production, like Seam B/C.
  - it must assert ABSENCE only: no producer, no accessor/serialization/persistence, no
    admission/promotion/authority surface, perimeter footprint = the classified modules.
  - it must NOT assert or imply CandidateShapedValue is the chosen carrier/representation, and
    must NOT add a field/enum/accessor/producer to it.
  - it must land under separate Hilmir authorization + Codex review before any file is named.
  - HOLD remains admissible; this seam is optional defensive work, not a required next step.
```

## 9. Anti-drift footer

GATE A FORK 3 — FIRST CODE-ADJACENT SEAM SURVEY / ARCHAEOLOGY-ONLY / SELECTS
NOTHING. It surveyed the candidate code-adjacent surfaces for the smallest future
inert/called-nowhere helper or tests-only lock that preserves all Fork 3 boundaries,
classified each on seven risk axes, and found that **every surface except one is
unsafe (S2-S8) or redundant (S9)**. The one safe surface is the **existing inert
`CandidateShapedValue`**, admissible only as the subject of a future **tests-only
inertness anti-drift lock** that asserts it STAYS carrier-less / producer-less /
authority-less — reinforcing "representation unbuilt," not selecting a carrier.
**Conclusion: one candidate seam is admissible for a future tests-only
characterization** (defensive, not Tier-2 progress; HOLD remains legitimate).
**Archaeology-only. This report identifies whether a future code-adjacent seam may
be considered; it selects no seam for implementation, writes no tests, authorizes no
code, and creates no carrier, schema, enum, field, ID, API, runtime, producer,
admission workflow, promotion mechanism, or authority option. Any tests or code
require separate Hilmir authorization plus Codex review.** Gate A stays paused; Gate
D parked; the parked writer non-conformances stay parked. Guidance not control; audit
observes authority and does not become authority; nothing rewrites identity / canon /
seed / soul.
