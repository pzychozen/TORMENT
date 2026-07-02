# TORMENT — Gate A Containment-Wall Enforcement Readiness Scan v0.1

**Status:** DOCS-ONLY readiness scan. **Non-authorizing.** Selects no mechanic, opens no gate,
authorizes no code or test, names no durable field/schema/carrier. Navigation / decision aid only.
Document A, Document B, P4, the Ledger Observational-Boundary, the Decision Registry, and
`PROJECT_ORIENTATION_MAP.md` §0 remain source of truth.

**Provenance:** filed after the Dream / Regime-B proof-obligation map closure
(`docs/TORMENT_DREAM_REGIME_B_PROOF_OBLIGATION_MAP_v0.1.md`, commit `f7cdd24`), whose §0 closure was
`be70b32`. This scan answers the question that map raised: *the next substantive motion is separately
authorized blocker work — is Gate A containment-wall enforcement an open, unguarded lane, or is it
already substantially worked and now blocked?*

> **One-line conclusion:** Gate A wall enforcement is **not empty**. The producer-independent
> tests/source characterization is **substantially worked**; the remaining gaps are **blocked** by
> unauthorized producer / carrier / admission / Gate B / P4 work, **not merely unguarded**. **Verdict:
> NO-OPEN.** Do not open another Gate A wall enforcement micro-test by default. **Recommended: HOLD.**

---

## 1. Current §0 interpretation

- **Dream / Regime-B is closed-for-now / NO-OPEN.** The absence guard (`c095de3`) and the proof-obligation
  map (`f7cdd24`) both pin absence and explicitly open no runtime and no lane.
- **The next substantive motion is blocker work**, not more Dream runtime-adjacent work — per the
  proof-map's own recommendation (Gate A containment-wall enforcement or P4 projection / source-sameness).
- **Minor bookkeeping note:** the §0 HEAD line currently still names `f7cdd24`, while actual git HEAD /
  the operator edge is **`be70b32`**. This scan does not fix that (no §0 update in this slice); it is
  recorded here only so the skew is not mistaken for a substantive divergence.

## 2. Current closed Gate A work (producer-independent — already landed)

Gate A containment-wall enforcement already carries a substantial, deliberately producer-independent body
of work:

- **Document A wall frame + path proposal exist** — `TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md`
  and `TORMENT_GATE_A_CONTAINMENT_WALL_ENFORCEMENT_PATH_PROPOSAL_v0.1.md`.
- **Authorization review selected Seam B first** — `TORMENT_GATE_A_WALL_ENFORCEMENT_PATH_AUTHORIZATION_REVIEW_v0.1.md`
  — but only **producer-independent tests/source characterization**, not a live producer.
- **Layered seam topology exists** (Seam A producer entry / Seam B ingest entry / Seam C writer authority),
  with per-seam scoping frames.
- **Candidate-representation principle + pre-carrier constraints exist** —
  `TORMENT_GATE_A_PRE_CARRIER_REPRESENTATION_CONSTRAINTS_FRAME_v0.1.md` and the representation
  decision/selection frames — carrier stays unselected.
- **Inert `CandidateShapedValue` exists** — a representation-only, side-effect-free value with a limited
  footprint; guarded by an inertness anti-drift lock (`tests/test_gate_a_candidate_shaped_value_inertness_lock.py`).
- **Five negative Layer-4 bricks exist** — five production refusal sites that reject an inert
  `CandidateShapedValue` **before** any mutation / fan-out / persistence side effect
  (`TORMENT_GATE_A_LAYER4_CONTAINMENT_BRICK_SERIES_CLOSURE_v0.1.md`): `TormentFabric.ingest` (text),
  `MemoryGraph.spawn_memory` (summary), `MemoryGraph.spawn_memory` (extra_payload object / immediate
  value), `EnvironmentStore.write` (value), and `ReferenceStore.ingest`
  (title/body/source_link/source_kind/metadata). Covered by the refusal tests
  (`tests/test_gate_a_{ordinary_ingest,spawn_memory,environment_value,reference}_candidate_refusal.py`).
- **Seam B Tier-1 characterization exists** — `tests/test_gate_a_seam_b_ingest_entry_characterization.py`
  (ingest-entry characterization).
- **Seam C / A-O2 writer-authority evidence exists** —
  `tests/test_gate_a_seam_c_writer_authority_ao2_characterization.py` — hazard inventory / evidence only,
  no writer fix.
- **Candidate inertness anti-drift lock exists** — locks `CandidateShapedValue` as representation-only.
- **Memory-to-prompt candidate proof-contract tests exist** —
  `tests/test_memory_to_prompt_candidate_proof_contract.py`.

## 3. Already guarded surfaces (do NOT re-guard)

The following are structurally locked today; another test here would duplicate an existing lock:

- **Resting-state wall nonreachability** — `tests/test_gate_a_containment_wall_nonreachability_characterization.py`.
- **No-tag-dependence** (structural, not tag-honoring) — `tests/test_gate_a_containment_wall_no_tag_dependence_characterization.py`.
- **Ingest fan-out root inventory** — `tests/test_gate_a_wall_ingest_fanout_root_inventory.py`.
- **Inspection non-reentry inventory** — `tests/test_gate_a_wall_inspection_nonreentry_inventory.py`.
- **Dream / Regime-B absence** — `tests/test_regime_b_dream_absence_characterization.py`.
- **`CandidateShapedValue` inertness + limited footprint** — inertness anti-drift lock.
- **Five negative refusal bricks** — the Layer-4 series (see §2).
- **Seam B T1–T4** — ingest-entry characterization.
- **Seam C** — hazard inventory / evidence only (no writer change).

## 4. Remaining gaps — BLOCKED, not merely unguarded

Each remaining gap is gated by a surface that is itself unopened/unauthorized; none is a free "just add a
test" move:

| Gap | Blocked by |
|---|---|
| **Seam A** enforcement | needs a **live producer** (none exists / unauthorized) |
| Full **A-C1 / A-C2** proof *against a producer* | needs **producer + carrier** |
| **A-O3 / A-D1** admission-sole-exit | needs **admission mechanics** (unopened) |
| **A-D2** (class movement) | needs **admission + promotion crossings** (unopened) |
| **Candidate inspection** surface | needs an **actual candidate surface** (carrier-dependent) |
| **Seam C** writer fixes | belong to **Gate B** (writer authority), not Gate A wall |
| `ArchiveStore` / links / `update_payload` | **proof-scope** items, **not brick targets** |

### Dependency table

| Dependency | Status | Enables |
|---|---|---|
| Absence guard (Regime-B) | DONE (`c095de3`) | resting-state safety only |
| Gate A wall characterization | SUBSTANTIALLY DONE (§2/§3) | resting-state + inert-candidate refusal |
| Producer / carrier | UNOPENED / unauthorized | Seam A, full A-C1/A-C2, candidate inspection |
| Admission / promotion crossing | UNOPENED (Document A §8) | A-O3 / A-D1 / A-D2 |
| Gate B writer authority | UNOPENED | Seam C writer fixes |
| P4 projection / source-sameness | FRAMED, mechanics deferred | read-side projection safety |
| Substrate / carrier / schema | DEFERRED (Issue #54) | any durable candidate surface |
| Envelope Audit | DEFER (shell doc) | observation-only, model-API-gated |
| Writer / identity / canon boundaries | LIVE + fenced (Gate 4 open Qs) | out of Gate A wall scope |

## 5. Ranked safe next slices (none opened here)

For reference only — **this doc authorizes none of them.** Each requires separate operator + Codex
authorization of its blocker:

1. **Nothing (HOLD).** The producer-independent wall work is saturated; forcing another micro-test risks
   duplicating existing Seam B / inertness / nonreachability / refusal locks.
2. **Blocker authorization: Gate A containment-wall producer/carrier** — would unblock Seam A and the full
   A-C1/A-C2 producer proofs. Heavy; carrier-coupled.
3. **Blocker authorization: P4 projection / source-sameness mechanics** — read-side; orthogonal to the
   write-side wall; the proof-map's co-equal candidate.
4. **Blocker authorization: Gate B writer authority** — would own Seam C writer fixes.
5. **Admission mechanics (Document A §8)** — substrate-last; unblocks A-O3/A-D1/A-D2.

## 6. Verdict — NO-OPEN

**No more Gate A wall enforcement code or tests should be opened by implication.** The remaining gaps are
blocked, not unguarded; adding another producer-independent micro-test would duplicate an existing lock and
create false motion. Any further Gate A wall brick, seam, or proof requires **separate authorization of its
blocker** — producer / carrier / admission / Gate B writer authority / P4 projection-source-sameness.

## 7. Recommended next state

- **Gate A containment-wall readiness scan: CLOSED** (this doc).
- **Gate A wall enforcement micro-work: HOLD.**
- **Next real lane requires explicit blocker authorization:** producer / carrier / admission, Gate B writer
  authority, or P4 projection / source-sameness — chosen by the operator, not by default motion.

## 8. What this artifact does NOT do

No production code. No tests. No §0 update (this slice). No dream runtime. No Gate D runtime. No Document B
chamber runtime. No P4 mechanics. No database / substrate. No candidate store. No admission / promotion
crossing. No scheduler / background loop. No AgentRunner / app / spine / MCP wiring. No model / provider /
API / prompt path. No memory writes / persistence / logging / transcripts. No output-control / finalizer /
refusal / identity / canon behavior. No dynamic-kernel / `conversation_shock`. It only records readiness and
bounds the space until a blocker is separately authorized.

*End — Gate A Containment-Wall Enforcement Readiness Scan v0.1. Docs-only, non-authorizing. Verdict:
NO-OPEN. Gate A wall enforcement micro-work HOLD; next real motion requires explicit blocker authorization.*
