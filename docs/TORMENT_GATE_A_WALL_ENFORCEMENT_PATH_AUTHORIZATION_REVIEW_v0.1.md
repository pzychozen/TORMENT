# TORMENT Gate A — Wall Enforcement-Path Authorization / Selection Review v0.1

## 0. Status / authorization scope

**Docs-only AUTHORIZATION / SELECTION REVIEW.** Unlike the prior enforcement-path
artifacts, this review *does* grant one tightly bounded authorization — and only
the one defined in §1/§4. It **does not implement the wall**, claims **no Gate A
wall completion**, opens **no Gate D**, and authorizes **no candidate producer,
candidate store, governed admission, or promotion crossing**. It writes no code
and no tests; it authorizes the *opening* of a future tests/source-first slice and
selects the seam and proof bars admissible first.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `8c32fb3` (docs: review Gate D readiness after Layer 4 bricks). Operator /
Codex decision in force: **PASS TO GATE A WALL ENFORCEMENT-PATH AUTHORIZATION
REVIEW.**

Subordinate to, and may not contradict:

```text
Document A (A-C1/A-C2/A-C3, A-O1/A-O2/A-O3, A-I1, A-D1/A-D2)
docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md   (wall boundary; §3 roots; §6 proof bars; §7 Gate D dependency)
docs/TORMENT_GATE_A_CONTAINMENT_WALL_ENFORCEMENT_PATH_PROPOSAL_v0.1.md       (b84191b; §5 invariants; §6 seams; §7 matrix; §8 guards)
docs/TORMENT_GATE_D_DEPENDENCY_MAP_v0.1.md                                   (§5-§8 Gate D dependencies)
docs/TORMENT_GATE_A_LAYER4_CONTAINMENT_BRICK_SERIES_CLOSURE_v0.1.md          (five negative bricks; §5 postponed surfaces)
docs/TORMENT_GATE_D_READINESS_REVIEW_AFTER_GATE_A_LAYER4_BRICKS_v0.1.md      (NO-OPEN; bricks harden one §5 row only)
PROJECT_ORIENTATION_MAP.md §0
```

Where this review and any contract appear to differ, the contracts win.

## 1. Verdict

**CONDITIONAL YES — authorize one bounded, tests/source-first Gate A wall
enforcement-path slice.**

The authorization is limited to:

- **Seam selection:** **Seam B (ingest-entry structural gate)** is selected as the
  *foundational first* seam. Seam A is *sequenced later* (it presupposes a producer
  that does not exist and is not authorized); Seam C is *routed to Gate B
  writer-authority* and stays parked. Selecting B first rejects nothing in the
  design — it sequences.
- **Scope:** the slice may carry **only the producer-independent proof bars** (§5
  "carried-first"). Every proof bar that requires a live candidate producer, a real
  admission crossing, or a promotion crossing is **deferred** to a later, separately
  authorized slice — because authorizing those carriers is forbidden here.
- **Form:** the slice's first and only deliverable is **tests/source guards**, with
  **no production wall code**, and even that opening is **gated by a further Codex
  review** of the concrete guard set and file scope before any file is named.

Why not a stronger YES: the wall's load-bearing proofs (A-C1/A-C2 *against a live
producer*, A-O3/A-D1 admission-sole-exit *with the crossing present*, A-D2 with
real staging/admission/promotion) cannot be closed without exactly the carriers
this review may not authorize. So the wall **cannot be built** in a first slice,
and this review does not pretend otherwise. What *can* move is the
producer-independent foothold the wall will later stand on.

Why not NO: the readiness review already showed the bricks hardened the §5
absence-wall row; the ingest-root inventory (`58d5a49`) and no-tag-dependence
lock (`8f8fa7a`) already exist as producer-independent scaffolding. A bounded
characterization slice extends provable, forbidden-line-free ground without
touching any producer/store/admission/promotion. That is admissible forward motion.

## 2. Evidence basis

```text
- Gate D dependency map §5: the wall today holds by absence / unwired topology, not by a
  mechanism; Gate D presupposes a REAL wall. (Blocker stands.)
- Layer 4 closure: five NEGATIVE, type-only CandidateShapedValue refusals at ordinary write
  ingresses, pre-side-effect; explicitly NOT wall completion; no producer/store/admission/
  promotion; does not fix direct writer hazards.
- Gate D readiness review (8c32fb3): NO-OPEN; the bricks harden exactly one dependency row
  (§5 absence-wall) and satisfy zero dependencies.
- Enforcement frame §3: the ordinary-ingest entry is the fan-out root; non-reachability must
  hold AT the ingest entry; ws_section_2a_v1 precedent (material in the fan-out can auto-emit
  identity pressure); sealed audit owner/bridge = by-construction non-reachability precedent.
- Proposal §4: the resting-state proofs hold PARTLY BECAUSE nothing is produced; they do NOT
  establish a wall under a live producer, admission-sole-exit, or staging != admission !=
  promotion with real crossings present.
- Proposal §6/§7: candidate seams A/B/C + inspection surface; proof-obligation matrix mapping
  A-C1/A-C2/A-C3/A-O2/A-O3/A-D1/A-D2/A-I1 to seams and future guard classes.
- Already-landed producer-independent scaffolding: 58d5a49 (ingest fan-out root inventory),
  8f8fa7a (A-C2 no-tag-dependence), c73add5 (P4 O3/O4 read-side projection-safety),
  2732f32 (resting-state non-reachability), the sealed audit owner/bridge.
```

Conclusion from the evidence: the only ground advanceable without a forbidden
carrier is the **producer-independent** portion of **Seam B** plus the
inspection-non-reentry posture. Everything else waits on carriers this review may
not authorize.

## 3. Candidate seams from `b84191b`

Restated from proposal §6, with this review's first-slice disposition. No seam is
deleted from the design; the dispositions are sequencing decisions.

```text
Seam A - producer-side containment boundary
  Proposal: chamber output held in a candidate boundary; only a governed admission crossing
            emits a released/low-authority ordinary write.
  Disposition: DEFERRED (sequenced later). Presupposes a candidate producer + admission
               crossing, both forbidden here. Cannot be the first slice.

Seam B - ingest-entry structural gate                            <= SELECTED FIRST (foundational)
  Proposal: single structural chokepoint at the ordinary-ingest fan-out root; contained
            artifacts structurally unable to arrive there; closed to candidates WITHOUT
            tag-honoring (I-1, I-2).
  Disposition: SELECTED as the foundational seam. Its PRODUCER-INDEPENDENT portion (sole-entry
               structural characterization + no-tag-dependence) is admissible first; its
               against-a-live-producer portion is DEFERRED until a producer is separately
               authorized.

Seam C - class-bound writer-authority gate
  Proposal: writers reject cognition/reflection-origin canon/identity/seed/long-half-life
            writes absent a governed promotion crossing (A-O2; A-O1 matched obligation).
  Disposition: ROUTED TO GATE B (writer authority); PARKED. Write-side authority work with
               its own gate; not opened by this review. See §7.

Cross-cutting - inspection surface
  Proposal: observation surface on the sealed audit owner/bridge posture (observation-only,
            unwired, packet-blind); inspection != projection, non-reentrant (A-I1/A-C3).
  Disposition: its NON-REENTRY POSTURE is carried-forward as a first-slice invariant to
               preserve (no regression); building a NEW candidate inspection surface is
               DEFERRED (there is no contained artifact to inspect yet).
```

## 4. Admissible first slice scope

The authorized first slice is a **producer-independent, tests/source-first Seam B
characterization** — the foothold the wall will later be built on, **not the
wall**. Admissible content:

- A **sole-entry structural characterization** of the ordinary-ingest fan-out root:
  source/AST evidence that `TormentFabric.ingest` is the single live ordinary
  ingest fan-out root (extending `58d5a49`), and that the five negative bricks sit
  pre-side-effect at the scoped write ingresses. This proves the *shape* of the
  chokepoint Seam B would occupy — it does **not** build the gate and does **not**
  assert non-reachability against a producer.
- A **no-tag-dependence carry-forward** (A-C2, extending `8f8fa7a`): the sole-entry
  characterization must hold by topology/absence, not by honored exclusion tags.
- An **inspection-≠-projection / non-reentry carry-forward** (A-I1/A-C3, extending
  `c73add5` and the sealed audit owner/bridge): the slice must not regress the
  observation-only, unwired, packet-blind posture, and must add no reentrant path.
- A **deliberation-room containment carry-forward**: the slice must confirm
  `AgentRunner` / `/agent/query` gain no contained-artifact input — preserving the
  existing unwired, observation-only posture.

Explicitly **out of scope for the first slice** (deferred, each needs its own
authorization):

```text
- any candidate producer / chamber / Document B inhabitant
- any candidate store / carrier / schema / field
- any governed admission crossing or admission-sole-exit proof WITH the crossing present
- any promotion crossing or staging!=admission!=promotion proof WITH real crossings present
- any writer fix / Seam C / A-O2 write-side enforcement (Gate B; parked)
- any production wall code (the slice is tests/source guards only)
- a second Layer 4 brick series (see §6)
```

The slice **does not complete the wall** and **must not be described as doing so.**

## 5. Proof bars that must be carried

Two tiers. Tier-1 is admissible in the first slice; Tier-2 is deferred because it
requires a forbidden carrier. **A Tier-1 bar carried now must still hold (not be
weakened) when the producer later arrives** — the first-slice guards are
necessary-but-not-sufficient and must compose forward into the full wall proof.

```text
TIER-1 (carried by the authorized first slice; producer-independent)
  T1  Sole-entry structural shape - the ordinary-ingest fan-out root is the single live
      ordinary ingest entry; the negative perimeter sits pre-side-effect there. (Seam B; A-C1
      shape only, NOT non-reachability against a producer.)
  T2  No-tag-dependence (A-C2) - the structural characterization holds by topology/absence,
      not by honored exclusion tags. (Extends 8f8fa7a.)
  T3  Inspection != projection / non-reentry (A-I1/A-C3) - observation-only, unwired,
      packet-blind posture preserved; no reentrant path added. (Extends c73add5 + sealed
      owner/bridge.)
  T4  Deliberation-room containment - AgentRunner / /agent/query gain no contained-artifact
      input; existing unwired posture preserved.

TIER-2 (DEFERRED to later, separately authorized slices; each needs a forbidden carrier)
  T5  A-C1/A-C2 non-reachability AGAINST A LIVE PRODUCER (needs a producer).
  T6  A-O3/A-D1 admission-sole-exit WITH the admission crossing present (needs admission).
  T7  A-D2 staging != admission != promotion WITH real crossings present (needs admission +
      promotion).
  T8  A-O2 no-silent-canon/identity from cognition/reflection writers (Seam C; write-side;
      Gate B; parked - see §7).
```

The wall is "approved and proved by construction" (frame §7) **only when Tier-2 is
also satisfied in later authorized slices.** This review approves neither Tier-2
nor the carriers it needs.

## 6. Treatment of ArchiveStore / links / update_payload

Handled **inside the wall-path review as dependency / proof-scope questions for
the Seam B sole-entry characterization — NOT as an automatic second Layer 4 brick
series.** The closure doc postponed them; here they become questions the T1
sole-entry proof must *address by classification*, not surfaces to brick.

```text
ArchiveStore
  Proof-scope question: is it an ALTERNATE ordinary-ingest entry that the sole-entry claim
  must account for? Recorded scoping (closure doc): lower ordinary-memory relevance; HTTP
  cannot carry a CandidateShapedValue; archive text self-defends.
  Disposition: in-scope for CLASSIFICATION by the T1 proof (account-for or scope-out with
  reasons). NOT a brick target. No brick authorized.

links
  Proof-scope question: does the structurally-open-but-production-unreachable path constitute
  an alternate entry the sole-entry claim must close or scope out?
  Disposition: in-scope for CLASSIFICATION by the T1 proof. NOT a brick target.

update_payload
  Proof-scope question: do the internally-constructed callers / the wrong-shaped all-values
  guard / the lower-value summary-only mutation guard leave an alternate mutation ingress the
  sole-entry claim must address?
  Disposition: in-scope for CLASSIFICATION by the T1 proof. NOT a brick target; no guard-shape
  fix authorized here.
```

Shared rule: these three are **dependency / proof-scope items for the Seam B
sole-entry characterization**, recorded as Gate D dependencies carried forward —
**not** an auto-opened second brick series. A brick over any of them would be a
separate target requiring its own Codex/operator authorization.

## 7. Treatment of direct writer hazards

**Parked.** The review does not fix them and does not need to fix them to open the
Tier-1 slice. It does, however, name the one specific dependency they create — and
names only.

```text
Named writer-authority dependency (dependency framing only, no fix):
  The four parked non-conformances - gravity_correction canon=True,
  _maybe_emit_identity_anchor, /promote force, mood_drift -> canon - are the existing
  direct-write paths that the A-O2 "no silent canon/identity from cognition" proof bar
  (Tier-2 T8 / Seam C) would eventually have to hold against.
  => They are a STANDING dependency of Seam C / Gate B, NOT a blocker of the Tier-1 first
     slice (which is ingest-entry / Seam B and write-side-independent).
  => Disposition: PARKED. No writer fix, no reclassification, no promotion into the Tier-1
     slice or any brick series. Named as a Gate B / Seam C dependency only.
```

The first slice (Seam B, Tier-1) is on the ingest-entry axis and does not touch the
writer-authority axis, so the parked hazards do not gate it. They re-enter the
picture only when Seam C / A-O2 is separately authorized at Gate B.

## 8. What remains forbidden

This review authorizes none of, and does not authorize by implication any of:

```text
- code; tests written by this review; production wall code in any slice it opens
- Gate A wall completion, or any claim of it
- Gate D runtime / private cognition / chamber / Envelope Audit runtime
- candidate producer; candidate store; carrier / schema / field selection
- governed admission implementation; admission-sole-exit with a real crossing
- promotion crossing implementation
- writer fixes / reclassification of the four parked non-conformances; Seam C / A-O2 build
- a second Layer 4 brick series (ArchiveStore / links / update_payload stay proof-scope items)
- database / substrate mechanics
- endpoint / API / schema expansion; prompt-request exposure; AgentRunner ownership expansion
- recursive / content / tag / provenance / key filtering; schema policing
- any positive authority crossing
- audit-to-control feedback; any claim that audit becomes authority
- autonomy; retrieval feedback; persistence changes
```

Naming a forbidden item records its boundary; it does not propose to cross it.

## 9. Exact next frontier

**If the bounded authorization in §1/§4 is accepted, the exact next move is a
single Codex/operator gate, then the Tier-1 characterization slice — nothing
heavier.**

```text
Next concrete step (gated):
  1. Codex review of the CONCRETE Tier-1 guard set and file scope (T1-T4), confirming the
     slice is producer-independent, tests/source-first, adds no production wall code, opens no
     Tier-2 carrier, and regresses no existing posture - BEFORE any file is named.
  2. On Codex PASS: land the Tier-1 tests/source guards (sole-entry shape + no-tag-dependence
     + inspection-non-reentry + deliberation-room containment), tests/source first, no
     production wall code.
  3. STOP. Re-gate before anything Tier-2.

Explicitly NOT the next frontier:
  - any candidate producer / store / admission / promotion (forbidden; Tier-2 carriers)
  - Seam A build (deferred until a producer exists) or Seam C / writer fixes (Gate B; parked)
  - a second brick series over ArchiveStore / links / update_payload (proof-scope items)
  - Gate D runtime / private cognition (parked; dependency stands per frame §7)
  - production wall code of any kind

Stop rule: if the Tier-1 guard set cannot be specified producer-independently and
tests/source-first, the seam stays unopened - a stable resting state, not a failure.
```

## 10. Anti-drift footer

GATE A WALL ENFORCEMENT-PATH AUTHORIZATION / SELECTION REVIEW. **Verdict:
CONDITIONAL YES** — authorize **one** bounded, tests/source-first, **producer-
independent** Seam B (ingest-entry structural gate) characterization slice, gated
by a further Codex guard-set review before any file is named. Seam A is sequenced
later (needs a producer); Seam C is routed to Gate B and parked. The slice carries
**Tier-1 only** (sole-entry shape, no-tag-dependence, inspection-non-reentry,
deliberation-room containment); **Tier-2** (non-reachability against a live
producer, admission-sole-exit, staging≠admission≠promotion, no-silent-canon/
identity) is **DEFERRED** because each needs a carrier this review may not
authorize. ArchiveStore / `links` / `update_payload` are **proof-scope dependency
questions for the sole-entry proof, NOT a second brick series.** The four direct
writer hazards stay **parked**, named only as a Seam C / Gate B dependency, not
fixed. This review **builds no wall, claims no wall completion, opens no Gate D,
and authorizes no producer / store / admission / promotion / writer fix / database
/ substrate / endpoint / schema.** Any move beyond the Tier-1 slice requires
separate Codex/operator authorization. Guidance not control; audit observes
authority and does not become authority; nothing rewrites identity / canon / seed
/ soul.
