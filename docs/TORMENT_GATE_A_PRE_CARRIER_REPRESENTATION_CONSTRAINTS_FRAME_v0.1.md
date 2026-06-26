# TORMENT Gate A — Pre-Carrier Representation Constraints Frame v0.1

## 0. Status / authorization scope

**Requirement-level pre-carrier constraints only. This document may define
properties any future representation must preserve, and anti-properties it must
avoid, but selects no carrier, store, schema, field, enum, ID, API, persistence
format, runtime path, producer, admission workflow, or promotion mechanism.
Representation remains unbuilt. Any concrete carrier or test/code work requires
separate Hilmir authorization plus Codex review.**

The seam-topology frame sequenced carrier/representation *before* producer /
admission / per-artifact refinement. Codex ruled that a *concrete* carrier document
would be too implementation-adjacent, so the safe question here is **not** "what
carrier do we use?" but **"what must any future carrier be forbidden from
becoming?"** This frame answers that question (§3) and nothing else: it is a
constraints envelope, not a carrier design.

Held true throughout: no production code; no tests; no git; no Gate A wall
completion; no Gate D / private cognition; no Gate B implementation; no writer
fixes; no candidate producer / store / carrier / schema / field / API / runtime
wiring; no governed admission or promotion implementation; no authority-option
selection; no database / substrate; no endpoint / API / schema expansion; no
reopening of the Layer 4 brick series; no audit/inspection turned into control; no
store / schema / field-name / API / runtime / persistence / ID / status-enum /
lifecycle-implementation choice.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `7ea1b6c` (docs: record Gate A wall seam selection).

## 1. Subordination

Subordinate to, and may not contradict:

```text
docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md   (Document A: A-C1/A-C2/A-C3, A-O1/A-O2/A-O3, A-I1/A-I2/A-I3, A-D1/A-D2, A-L1)
docs/TORMENT_GATE_A_CANDIDATE_BOUNDARY_ADMISSION_REQUIREMENTS_v0.1.md  (Layer-3: boundary = property; "recorded" != store selected; nothing automatic)
docs/TORMENT_GATE_A_FORK3_CANDIDATE_BOUNDARY_GOVERNED_ADMISSION_DESIGN_FRAME_v0.1.md   (boundary = containment property, not a place/store)
docs/TORMENT_GATE_A_GOVERNED_ADMISSION_AUTHORITY_MODEL_FRAME_v0.1.md   (admission authority = options only, unselected)
docs/TORMENT_GATE_A_FORK3_WALL_SEAM_SELECTION_FRAME_v0.1.md            (layered topology; the five distinct roles; carrier sequenced before producer/admission)
docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md   (wall boundary; §3 roots; §6 proof bars)
docs/TORMENT_GATE_A_LAYER4_CONTAINMENT_BRICK_SERIES_CLOSURE_v0.1.md    (five negative bricks closed; CandidateShapedValue inert-by-construction)
```

Where this frame and any contract appear to differ, the contracts win.

## 2. Doctrine filter

> A representation is whatever a future authorized carrier turns out to be. This
> frame fences that future thing: it must **serve** the candidate-boundary
> containment property without **becoming** a store, schema, or authority-bearing
> object. Constraining what a representation must never become is not designing one.

## 3. The question this frame answers (and only this)

```text
What requirement-level constraints must any future candidate-boundary
representation satisfy so it preserves containment, inspectability, contestability,
recovery, and governed-admission separation without becoming a store / schema / API
/ runtime or positive authority?
```

## 4. This is a pre-carrier constraints frame, not carrier design

```text
- It defines a CONSTRAINTS ENVELOPE: required preserved properties (§5) + forbidden
  anti-properties (§6). It picks nothing inside that envelope.
- It does NOT answer "what carrier do we use?" — it answers "what must any future
  carrier be forbidden from becoming?"
- The candidate boundary stays a CONTAINMENT PROPERTY (Fork 3 design frame), not a
  store. A future representation is the thing-that-bears-the-property; these
  constraints keep it from drifting into an object that seizes authority.
- Evidence (NOT a target): the Layer 4 `CandidateShapedValue` is the existing
  inert-by-construction precedent — sealed, opaque, no producer, no store, no
  governed admission, no promotion, no serialization, no persistence. This frame
  cites it to ILLUSTRATE the inertness a future representation must preserve; it
  does NOT extend it, build a producer for it, or reopen the Layer 4 series.
```

## 5. Required properties any future representation MUST PRESERVE

```text
P-1  containment — a candidate-shaped output remains non-reachable to every Document A
     A-C1 site for its whole existence; the representation never provides a reach path
     (A-C1; containment invariant §2).
P-2  inspectability — remains observable read-only for audit throughout containment,
     without the inspection itself being a re-entry path (A-C3).
P-3  contestability — can be contested/objected-to such that future authority is
     constrained, with no erasure of provenance and no raising of authority (A-C3 / A-L1;
     contest routes down only).
P-4  recovery — can be recovered at no higher than its prior contained / retired / audit
     posture (recovery retains class); recovery never admits, promotes, projects, or makes
     cognition-eligible (A-I2); no invisible deletion of inspected/contested items (A-L1).
P-5  governed-admission separation — the ONLY exit into ordinary memory is a governed
     admission crossing; the representation provides no side path out (A-O3).
P-6  admission distinct from promotion — admission lands at <= released/low-authority and
     never implies promotion; any higher posture is a separate governed crossing (A-D1/A-D2).
P-7  non-reachability before admission — before a crossing, the output cannot enter ingest /
     motif / drift / mood / role / deep / SRG / reinforcement / retrieval / prompt projection /
     promotion / canon / identity writes (A-C1), held structurally (A-C2).
P-8  inspection observation-only — observation never becomes control; audit observes
     authority and does not become it (A-I1; Ledger doctrine).
P-9  no authority from mere existence/staging/inspection — existence, staging, recommendation,
     and inspection confer NO admission, promotion, or authority (creation != admission;
     staging != authority; inspection != authority; not-self-promotable).
```

## 6. Anti-properties any future representation MUST AVOID

```text
A-1  must not become ordinary memory — no side path converts a contained output into
     ordinary memory absent a governed admission crossing (A-O3).
A-2  must not become canon / identity-tier / seed / long-half-life — never directly, and
     never as a side effect of being represented (A-O2).
A-3  must not become retrieval-visible / prompt-visible / MemoryPlan-visible — caller- or
     audit-visibility is not prompt visibility; the representation grants no projection
     (A-C1 / A-I1).
A-4  must not become a store / schema / API / runtime path by implication — "recorded" is a
     requirement only; no log / event / store / database / endpoint / persistence is implied
     or selected (Layer-3 §5; Document A §11 routes carriers to Stage B/P6).
A-5  must not rely on exclusion tags — containment holds by construction, never by downstream
     readers honoring a reflection-exclusion tag (A-C2).
A-6  must not grant admission, promotion, refusal, or authority by being present — presence
     is inert; only a governed crossing with the required authority admits/promotes, and
     refusal authority is itself governed/asymmetric (Document A §2/§9; authority model frame).
A-7  must not make audit / inspection into control — no "represented / inspected / audited ->
     auto-admit / auto-route" path; audit feeds no live decision (Ledger §3 directionality).
A-8  must not silently route to writer surfaces — the representation never reaches
     spawn_memory / add_memory / promote_chunk / reinforce / environment / reference writers,
     or the parked direct-writer hazards, by any implicit path (A-C1 fan-out list).
```

## 7. Tie to the layered seam topology

```text
- A future representation must SERVE the layered topology (seam-selection frame), not
  collapse it. It is borne within containment; it does not merge the roles.
- The five requirement-level roles stay DISTINCT, and the representation must not let any
  bleed into another:
    producer-side containment   (A-C1/A-C2 at origin)        — representation stays inert here.
    ingest-entry structural gate (A-C1/A-C2 at the fan-out root) — representation never arrives here unadmitted.
    writer-authority gate        (A-O1/A-O2, Gate B)          — representation never becomes a write.
    inspection surface           (A-I1/A-C3, observation-only) — representation is inspected, not controlled.
    governed admission crossing  (A-O3/A-D1/A-D2, separate)   — the only exit; representation provides no side path.
- In particular: the representation must not let "recorded" (a requirement) become the
  store; must not let inspection become control; must not let containment become a writer
  surface; must not let presence become admission. Each is the topology's anti-collapse line.
```

## 8. Preserved framings

```text
- The governed-admission AUTHORITY MODEL stays requirement-level only: the authority-class
  option (operator-only / user-co-sign / governance-required / future policy) remains
  UNSELECTED; admission remains UNBUILT. These constraints presuppose neither.
- The candidate BOUNDARY stays a containment PROPERTY, not a store/object; this frame
  constrains a future representation to remain inert w.r.t. authority, consistent with that.
- The LAYER 4 brick series stays CLOSED: this frame does not reopen Layer 4 and does not
  create another brick series. Pre-carrier constraints are property constraints, not bricks,
  not a producer, not a store. The five landed negative bricks stay as-is; the postponed
  surfaces (ArchiveStore / links / update_payload) stay proof-scope items, not targets.
```

## 9. What remains deferred

```text
- the concrete CARRIER / representation itself.
- store / schema / fields / enums / IDs.
- persistence format.
- API / runtime path.
- the live candidate PRODUCER (Document B interior).
- the admission WORKFLOW / crossing mechanics (Layer 4).
- the promotion MECHANISM.
- tests / code.
- database / substrate; Stage B.
- which authority-class option admission requires (Document A §14 OPEN); per-artifact
  admission refinement.
- the four parked writer non-conformances (incl. /promote force) — stay parked, not fixed.
```

## 10. What the pre-carrier constraints do and do not authorize

```text
DOES:    define the constraints envelope any future candidate-boundary representation
         must satisfy — required preserved properties (§5), forbidden anti-properties
         (§6) — and bind it to the layered seam topology (§7), the unselected authority
         model (§8), and the closed Layer 4 series (§8).

DOES NOT (and does not authorize by implication):
  - select / design a carrier, store, schema, field, enum, ID, API, persistence format,
    runtime path, producer, admission workflow, or promotion mechanism
  - select an authority-class option
  - production code; tests; git
  - Gate A wall completion; Gate D; Gate B implementation; writer fixes (incl. /promote force)
  - candidate producer / store; database / substrate; Stage B; Document B interior
  - endpoint / API / schema expansion; reopening the Layer 4 brick series; another brick series
  - audit / inspection turned into control; any positive authority crossing
```

## 11. Anti-drift footer

GATE A PRE-CARRIER REPRESENTATION CONSTRAINTS FRAME / REQUIREMENT-LEVEL ONLY /
SELECTS NO CARRIER. It answers one question — what any future candidate-boundary
representation must be forbidden from becoming, and what it must preserve. **Required
to preserve:** containment, inspectability, contestability, recovery,
governed-admission separation, admission-distinct-from-promotion, non-reachability
before admission, inspection observation-only, and no-authority-from-existence/
staging/inspection. **Forbidden from becoming:** ordinary memory; canon / identity /
seed / long-half-life; retrieval / prompt / MemoryPlan-visible; a store / schema /
API / runtime by implication; tag-dependent; an admit / promote / refuse / authority
grantor by mere presence; audit-as-control; a silent route to writer surfaces. It
binds the representation to the **layered seam topology** (the five roles stay
distinct), preserves the **unselected authority model** and the **closed Layer 4
series**, and defers the concrete carrier and all mechanics. The Layer 4
`CandidateShapedValue` is cited as inertness evidence, **not** a target. **This
document may define properties any future representation must preserve, and
anti-properties it must avoid, but selects no carrier, store, schema, field, enum,
ID, API, persistence format, runtime path, producer, admission workflow, or
promotion mechanism. Representation remains unbuilt. Any concrete carrier or
test/code work requires separate Hilmir authorization plus Codex review.** Gate A
stays paused; Gate D parked; the parked writer non-conformances stay parked.
Guidance not control; audit observes authority and does not become authority;
nothing rewrites identity / canon / seed / soul.
