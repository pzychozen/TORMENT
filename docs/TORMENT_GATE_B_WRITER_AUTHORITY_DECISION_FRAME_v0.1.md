# TORMENT Gate B — Writer-Authority Decision Frame v0.1

**DECISION FRAME — DEFINITIONAL ONLY. NO CODE, NO TESTS, NO REGISTRY EDIT, NO WRITER FIX,
NO BEHAVIOR CHANGE, NO MECHANISM, NO VEHICLE SELECTED.**

This artifact ratifies only a boundary and a vocabulary. **No writer is governed, fixed, selected, or
built by this artifact.** It builds on the read-only Gate B hazard inventory
(`docs/TORMENT_GATE_B_WRITER_AUTHORITY_HAZARD_INVENTORY_v0.1.md`) and turns its named hazards into a
shared decision frame, while opening nothing.

**Date:** 2026-06-17. **Baseline HEAD = origin/main = `2ec4023`** (latest commit
*docs(engine): point orientation map to Gate B inventory*).

> Memory may guide context. Memory may not seize authority.

---

## 1. Anti-drift banner

Decision frame — definitional only. This document defines the write-side authority boundary, defines
"governed writer" as a **requirement-level characterization**, and records a **non-binding**
order-of-consideration for later reconciliation. It selects no mechanism, no vehicle, no schema, and no
remedy; it changes no behavior; it opens no gate. Naming a hazard or a leading candidate here neither
opens nor blesses it. Gate A closed only as advisory-boundary characterization + tests-only lock and
did not certify runtime safety; the Gate B inventory is read-only and opens no fixes; this frame stays
definitional and continues that posture.

## 2. Scope and posture

In scope: ratify (a) the authority boundary Gate B protects, (b) the requirement-level definition of a
"governed writer," (c) a non-binding order-of-consideration over the inventoried hazards, (d) what
stays characterization-only, (e) what stays postponed, and (f) the explicit non-authorizations.

Out of scope: every remedy and selection. The frame does not fix, govern, select, schedule, or build
any writer; it does not choose a governance vehicle; it does not design or adopt any mechanism. The
inventoried hazards (H1–H6) remain **parked non-conformances** and must not be encoded here as correct
or as baseline authority.

## 3. The authority boundary Gate B protects

For Gate B framing, this authority-bearing write set is provisional and non-exhaustive. A write is treated as authority-bearing when it asserts one or more currently named signals: `canon=True`, an identity/seed-class `mtype`, or promotion of content into core memory. Ordinary additive writes that claim none of those sit on the permitted side for this framing; authority-bearing writes sit on the governed side.

What Gate B protects is the integrity of that crossing: **an authority-bearing claim must not be
asserted automatically or unilaterally without an explicit, separately-authorized governed crossing.**
This is the write-side expression of the doctrinal kernel — *memory may guide context; memory may not
seize authority* — and it is continuous with the existing requirement contracts: Document A is the
admission edge (admission ≠ promotion; unadmitted reflection is barred from authority-bearing fan-out),
and Seed-Governance specializes that wall for seed/identity/canon outcomes. Gate B frames the boundary;
it does not implement, relocate, or amend those contracts.

Stating the boundary is not the same as enforcing it. This frame asserts no gate exists, builds none,
and requires none here; it only names where the line is so that later, separately-authorized work can
reason about crossings without re-litigating the boundary.

## 4. Definition — "governed writer" (requirement-level only)

A **governed writer**, *at this stage*, is a **requirement-level characterization** — a description of
properties a writer of authority-bearing claims would need to satisfy. It is **not** an implemented
gate, **not** an approval workflow, **not** a blocker or finalizer, and **not** a finalized mechanism.
No such writer exists or is built by this artifact; the term names a target shape, not a component.

A writer would be considered *governed* (as a requirement, to be defined and authorized later) when its
authority-bearing output is **visible, provenance-bearing, contestable, and bounded in its authority
posture** rather than self-asserting. Concretely as requirements (not mechanisms):

- **Visibility** — an authority-bearing claim is observable as such, not silent.
- **Provenance** — the claim carries where it came from and how it was produced.
- **Contestability** — the claim must remain contestable in principle and must not be treated as unappealable. This posture does not select or imply any implemented writer contest mechanism, Ledger mechanism, or disagreement workflow.
- **Bounded authority posture** — as posture words only, not a selected implementation status and not P4/source-sameness or `diagnostic_only` cognition mechanics, authority-bearing claims default to non-authoritative or characterization-only until a later governed crossing is explicitly defined and separately authorized.

**Governance means visibility, provenance, contestability, and bounded authority posture — not hidden
control.** Per the operator design value, "control" means absolute or coercive blocking; a governed
writer in this sense imposes no hidden finalizer, output blocker, identity pin, durable user-risk
scoring, invisible refusal/delete rule, monitoring, or autonomy layer. Governance here is about making
authority *answerable*, not about silently suppressing or finalizing anything.

## 5. Order-of-consideration (non-binding)

The following groups *consideration only* for later, separately-authorized reconciliation work. It authorizes nothing, schedules nothing, and selects no first target. The grouping reflects **authority height** — whether the asserted bit is canon — a structural distinction, **not** a severity or priority ranking. **Leading candidate does not mean authorization.**

- **Canon-asserting authority-bearing hazards for later consideration:** H1
  (`gravity_correction` automatic `canon=True`) and H3 (`POST /promote` force path asserting
  `canon=True` while bypassing the endpoint's promotion decision guard). They are grouped here because
  they assert canon — the highest-authority bit — without a governed crossing.
- **Identity-family conformance question:** H2 (`_maybe_emit_identity_anchor`, `canon=False`,
  derived) — identity-family but not canon-asserting; a conformance question, not a canon-authority
  crossing.
- **Characterization/parked, not for governance consideration at this stage:** H4 (`mood_drift →
  centroid` input-reachability into `measure_drift`, topology only), H5 (Phase-8 `FabricHandle` gravity
  route, parked behind its unverified binding), and H6 (ordinary-ingest eligibility envelope).

No item above is opened, selected, or fixed. Selection of any first reconciliation target is a separate,
later, explicitly-authorized decision.

## 6. Characterization-only at this stage

These remain descriptive and are not governance subjects in this frame:

- H4 — `mood_drift` rows are *eligible to be among* the recent-memory centroid inputs to
  `measure_drift`; topology only, no causal or magnitude claim, no filtering implied.
- H5 — the Phase-8 gravity route is a `FabricHandle` seam; it is a second route to the gravity writer
  **only** for implementations that bind it to `character.gravity_correction`. That live binding is
  unverified and stays parked; no live route is asserted.
- H6 — ordinary-ingest fan-out is an eligibility/reachability envelope, not guaranteed fan-out; the
  advisory layer is not the writer.
- The composition of `measure_drift` inputs is left uncharacterized for magnitude.

## 7. Postponed (later, separately-authorized work)

Carried forward as postponed; this frame opens none of them:

- P4 implementation / read-side projection gates; source-sameness mechanics.
- Seed-Governance mechanics / implementation; `canon_source` field/enum/representation.
- Document B runtime; dream/incubation runtime; candidate store; durable private state; durable chamber
  continuity.
- Database / substrate; schema / storage / carriers / migration.
- `mood_drift` filtering; promote-authorization redesign; any actual writer fix.
- Mechanism design and **governance-vehicle selection** — including whether Cluster 2 v0.2 (Authority
  Gate) is the write-side vehicle, which remains an open, verification-pending question.
- Verification of the H5 live `FabricHandle → character.gravity_correction` binding.

The construction-entry proof bar remains later and unchanged: any future transition from framing toward
mechanics or construction requires applicable Registry §K evidence, requirement-to-carrier
traceability, a fresh clean checkpoint, and operator hand-back. No construction-entry follows from this
frame.

## 8. Open questions (deferred — ordering/authorization only)

Recorded, not answered here:

1. Should writer-hazard reconciliation sit inside Gate B, or in a separate-but-adjacent Gate B1
   (still visible, still adjacent to the authority framing)?
2. Is Cluster 2 v0.2 (Authority Gate) the write-side authority vehicle? (Verification pending; not
   locked.)
3. What verification settles the H5 `FabricHandle` binding before it could leave characterization?
4. How much P4 read-side framing should precede any defined write-side crossing?

## 9. Explicit non-authorizations

This artifact does **not** authorize: any writer fix; any behavior or canon-semantics change; any
gating, blocking, finalizing, or approval-workflow logic; any test; any code; any schema; any registry
edit; any `measure_drift` / `mood_drift` filtering; any promote-authorization redesign; any P4,
Seed-Gov, Document B, dream/incubation, candidate-store, or durable-private-state work; any
database/substrate or schema/storage/carriers/migration work; any `canon_source` / source-sameness
mechanics; and any mechanism or governance-vehicle selection. It reserves no registry number and makes
no registry amendment.

Guidance-not-control remains binding: no identity pinning, invisible finalizer, output blocker, hidden
deletion/refusal rule, durable user-risk scoring, monitoring, notification surface, reputation/penalty
ledger, or autonomy is introduced or implied.

## 10. Recommended next step

Route this decision frame to **Codex challenge and/or operator review** before any target-selection or
mechanism artifact is drafted. Do not auto-open writer reconciliation. A first-target selection, a
governance-vehicle determination, or any mechanism is a separate, later, explicitly-authorized step.

---

## Anti-drift footer

DECISION FRAME — DEFINITIONAL ONLY. No code, no tests, no registry edit, no writer fix, no behavior
change, no mechanism, no vehicle, no schema, no runtime change. **No writer is governed, fixed,
selected, or built by this artifact.** "Governed writer" is a requirement-level characterization, not an
implemented gate, approval workflow, blocker, or finalized mechanism. Leading candidate does not mean
authorization. Governance means visibility, provenance, contestability, and bounded authority posture —
not hidden control. The inventoried hazards remain parked non-conformances; old-doc authority
quarantine and the construction-entry proof bar remain binding. Guide, not control; audit observes
authority and does not become authority. Memory may guide context. Memory may not seize authority.
Any subsequent Gate B decision remains a separate authorization.
