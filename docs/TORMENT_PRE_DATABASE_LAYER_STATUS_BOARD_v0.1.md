# TORMENT Pre-Database Layer Status Board v0.1

**Purpose:** A compact, living checklist of where each pre-database layer actually stands — to fix
direction confusion and to be reused in handoffs. **Not a gate, registry, roadmap, or doctrine artifact.**

> Honesty rules for this board: *tests/hardening ≠ capability implemented; framed ≠ implemented;
> promoted contract ≠ runtime; database/substrate stays deferred.*

---

## 1. Baseline

- **HEAD / baseline:** `6e492a9` *test: clean CodeQL hygiene alerts*
- **Expected Windows state:** `main...origin/main` (clean)
- **Board status:** living checklist; update the rows + the handoff block each session.

## 2. Status legend

`ACTIVE` working now · `DONE` finished · `HARDENED-FOR-NOW` implemented + tests-locked, paused ·
`PARTIAL` some real, some framed/parked · `FRAMED` requirements/questions/selection exist; no
runtime/mechanics opened · `WAITING` ready, needs operator decision · `PAUSED` deliberately stopped ·
`DEFERRED` intentionally later · `BLOCKED` gated by an external barrier · `NOT STARTED` doctrine may
exist, zero build.

## 3. Current active direction

- CodeQL hygiene slice **closed** (`6e492a9`; 4 alerts fixed, #996 intentionally left).
- **This board is the current administrative bridge.**
- **Active lane:** the **ephemeral structured cognition** lane (see §5 Active Lane Contract) — **Slice 1
  CLOSED** (`4e164c3`); Slice 2 (numeric retrieval shaping) deferred / not yet authorized.

---

## 4. Main status table

| Layer | Status | Plain meaning | Evidence anchor | Next action |
|---|---|---|---|---|
| Thinking layer (selected surfaces) | HARDENED-FOR-NOW | Selected live thinking surfaces: deterministic routing + retrieval shaping (not deliberation); live path consumes only `MemoryPlan` | `thinking_controller.py`; Gate A C1–C5 (`test_gate_a_tests_only_locks_c1_c5.py`); tuned-scoring/ambiguity provenance checkpoints | none; pause |
| ReflectionTrace / observability floor | HARDENED-FOR-NOW | Ephemeral, content-free decision-shape observation; non-reentrant; stdlib-only | `reflection_trace.py`; `test_reflection_trace.py` + runner-parity; `48ae289` | none; reuse as scaffold |
| /thinking/debug read-only surface | HARDENED-FOR-NOW | Debug endpoint returns full chain (intentional, ephemeral, non-persisted); handler read-only-locked | `app.py:2667`; `TestDebugEndpointReadOnlyCompanion`; `e9212a7` | none |
| Spine thinking-alignment buffer | HARDENED-FOR-NOW | Bounded (200), in-memory, content-free advisory buffer + read endpoint; live population not proven | `spine.py`; `test_spine_thinking_alignment_buffer.py`; `805a0ba` | none |
| Ephemeral structured cognition state | PARTIAL | **Slice 1 CLOSED (`4e164c3`):** behavior-preserving routing scaffold — frozen primitive-only `EphemeralCognitionState`; `build_memory_plan()` routes through it with `MemoryPlan` parity (no production behavior change). Tests-locked; no new capability yet | `thinking_models.py` (`EphemeralCognitionState`); `_build_ephemeral_cognition_state`; `test_ephemeral_cognition_state.py`; `4e164c3` | Slice 2 (numeric retrieval shaping) definition drafted, pending authorization (`..._SLICE_2_DEFINITION_v0.1.md`); see §5 |
| Candidate Gate D / Layer-1 private thinking | FRAMED | Eligible substrate-independent interior slice; **framed only**, pending operator selection | cognition roadmap §9; comparison frame `5472639`; pointer `3659089` | full Gate D remains unopened; proceed only via separately bounded slices |
| Envelope Audit | FRAMED | Requirement only (Document B §7); no module; only a coarse `requires_self_review` flag exists | Document B §7 | none until Gate D opens |
| Dream / incubation / Regime-B | DEFERRED | Offline reflection; no runtime exists; explicitly deferred + substrate-coupled | Document B §5; pre-substrate §3 | none; last |
| Private cognition / Document B chamber interior | FRAMED | Requirement doctrine **complete (promoted 2026-06-13)**; **zero runtime** | `TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md` | tied to Gate D decision |
| Guided memory layer | PARTIAL | Live retrieval/prompt-shaping + observability hardened; conformance of its automatic inputs only framed (Gate 4) | memory-to-prompt v0.2.x; `character_context`; guidance-without-coercion map | none clean (its open Q = Gate 4) |
| Reader / projection safety (P4) | FRAMED | P4 contract framed + matched P2.5/P4 reconciliation closed; **runtime gates not built** | P4 contract; matched P2.5/P4 (§N13) | framing largely done; mechanics deferred |
| P4 / source-sameness / diagnostic-only | DEFERRED | Requirement-level posture only; mechanics substrate-coupled | matched P2.5/P4 §5.2; Gate 4 derived-anchors frame (Q-D2) | none now |
| Candidate store / governed admission | DEFERRED | Admission edge framed (Document A §8); carrier = Stage B/P6 | Document A §8/§11; reconciliation frame §8 | substrate-last |
| Seed-Gov / O6 / must-not-pin | PARTIAL | Doctrine framed + authored-seed write-once **test-locked**; revision/O6 mechanics deferred | Seed-Gov Blueprint §7; seed stability lock `4742b87`; gravity §N14 | mechanics deferred |
| Gate 4 old automatic writer paths | PARTIAL | Writers (gravity auto-canon, anchors, mood, warmth, role) **LIVE & UNRECONCILED**; conformance **questions framed, not answered** | 5 Gate 4 question frames; gap map; §N14 gravity memo; Gate B hazard inventory | answers paused/deferred (operator-gated) |
| Operator audit / contestability / revocability | PARTIAL | Provenance + audit endpoints live; candidate contestability/revocability framed; Track B parked (no resolver) | Ledger Observational-Boundary; ProvenanceV1; `/debug/provenance`; Track B (parked) | resolver = parked heavy lane |
| Database / substrate readiness | DEFERRED | Deliberately last; gated by Issue #54; still JSON/JSONL/SQLite scaffolding | pre-substrate §1; DB/Substrate Doctrine Reconciliation; registry P0–P11 | only after mind-readiness + trio council + clean checkpoint |
| Start/examples/onboarding cleanup | PARTIAL | One factual fix landed (TROUBLESHOOTING §16); more candidates (stale counts, version stamps) named | `194677f`; start/examples scoping survey | optional small doc fixes; version label is operator's call |
| CodeQL hygiene | DONE | 4 tests-only alerts cleaned; #996 intentionally left (module-object introspection) | `6e492a9`; `test_promote_force_bypass_endpoint_wiring.py`, `test_gate_a_*` | none |

**What must NOT be opened yet (deferred/blocked):** Dream/Regime-B, Document B chamber runtime, Envelope
Audit runtime, P4/source-sameness mechanics, candidate store/governed admission, Seed-Gov/O6 mechanics,
Gate 4 writer remedies, and database/substrate/Stage B. See §5.

---

## 5. Active Lane Contract — ephemeral structured cognition state

- **Next lane:** ephemeral structured cognition state.
- **Allowed direction:** **content-free, deterministic, per-turn, advisory** state used by
  `ThinkingController` / `MemoryPlan` shaping. Observation/shape only, ephemeral, non-reentrant — in the
  same boundary class as `ReflectionTrace`.
- **Forbidden (hard lines):** hidden chain-of-thought storage or exposure · durable private state ·
  output blocker/finalizer · identity pinning · monitoring/autonomy/self-trigger · database/substrate ·
  Gate 4 writer remedies · P4/source-sameness mechanics · Seed-Gov/O6 mechanics · candidate store/governed
  admission · dream/incubation runtime.
- **Discipline:** audit-first; characterization and tests travel with any behavior change; Codex challenge before any patch;
  stop if a slice needs any forbidden item.

### Slice 1 — CLOSED (`4e164c3`)

- **Implementation:** frozen, primitive-only `EphemeralCognitionState` (content-free scalar fields only).
- **Builder:** private `ThinkingController._build_ephemeral_cognition_state(frame, mode)` (pure function of frame + mode).
- **Routing:** `build_memory_plan()` now routes through the ephemeral state.
- **Behavior:** `MemoryPlan` parity preserved — **no production behavior change intended.**
- **Validation:** `104 passed in 1.06s`.
- **Boundaries preserved:** no serialization · no `ThinkingResult` exposure · no `/thinking/debug` exposure ·
  no `/agent/query` output-shape change · no durable state · no database/substrate.
- **Next possible slice:** Slice 2 (numeric retrieval shaping) — **definition drafted, pending authorization.**
  Envelope fixed in `docs/TORMENT_EPHEMERAL_COGNITION_STATE_SLICE_2_DEFINITION_v0.1.md`; not implementable
  until that artifact's §4 (exact numeric rule) and §5 (rollout posture) are decided.

---

## 6. Handoff rule

Every future handoff on this programme must include:

- latest **HEAD** + working-tree status (`main...origin/main`?)
- **active lane**
- **current row** on this board
- **last closed slice** (commit)
- **next slice**
- **paused/deferred lanes** in play
- **link/path to this board:** `docs/TORMENT_PRE_DATABASE_LAYER_STATUS_BOARD_v0.1.md`

---

## 7. Maintenance note

- This board is **not** authority; the orientation map, Decision Registry, and promoted contracts remain
  source of truth. This is a navigation aid.
- Update the changed rows + the §6 handoff block per session; do **not** grow it into a roadmap or a
  doctrine restatement.
- Orientation-map / registry pointers to this board are a **separate, later** step (not done in this
  patch).

*End — TORMENT Pre-Database Layer Status Board v0.1. Living checklist; not a gate, registry, or roadmap.*
