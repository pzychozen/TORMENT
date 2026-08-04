# TORMENT Pre-Database Layer Status Board v0.1

**Purpose:** A compact, living checklist of where each pre-database layer actually stands — to fix
direction confusion and to be reused in handoffs. **Not a gate, registry, roadmap, or doctrine artifact.**

> Honesty rules for this board: *tests/hardening ≠ capability implemented; framed ≠ implemented;
> promoted contract ≠ runtime; database/substrate stays deferred.*

---

## 1. Baseline

- **HEAD / baseline:** `24bd268` *docs(project): record first model-api audit tests-only characterization*
- **Expected Windows state:** `main...origin/main` (clean)
- **Board status:** living checklist; update the rows + the handoff block each session.

## 2. Status legend

`ACTIVE` working now · `DONE` finished · `HARDENED-FOR-NOW` implemented + tests-locked, paused ·
`PARTIAL` some real, some framed/parked · `FRAMED` requirements/questions/selection exist; no
runtime/mechanics opened · `WAITING` ready, needs operator decision · `PAUSED` deliberately stopped ·
`DEFERRED` intentionally later · `BLOCKED` gated by an external barrier · `NOT STARTED` doctrine may
exist, zero build.

## 3. Current active direction

- **This board is the current administrative bridge.**
- **Ephemeral structured cognition** lane (see §5) — **Slice 1 CLOSED** (`4e164c3`) and **Slice 2
  IMPLEMENTED + CLOSED** (impl `06a9536`, docs `3564b79`); **Slice 3 core-lane shaping ALSO ALREADY
  LANDED** (`TORMENT_COGNITION_CORE_SHAPING_V1` / `_apply_cognition_core_shaping_v1`; plus later
  geometric + relational-prominence shaping); lane **paused / PARTIAL** — **NOT "Slice 3 pending"**;
  any further shaping is **Slice 4+** (see §5).
- **Recently closed since then (record only, no lane reopened):**
  - participation guidance **v1** — advisory-only, implemented + measured, default-off
    `TORMENT_PARTICIPATION_GUIDANCE_V1` (`8e4e27b`, `9e0cbca`; §0 record `d73c148`).
  - **D** motion-keeper — tests-only `query().explain` shape lock vs `trace()` decomposition (`022c86e`).
  - **A0** Gate D readiness review — **DEFER / NO-OPEN** recorded (`d8a65e3`).
  - **A0 lived-use scientific checkpoint** — evidence correction recorded (`9f124648`, checkpoint
    `docs/TORMENT_A0_LIVED_USE_SCIENTIFIC_CHECKPOINT_2026_08_04.md`): provider-visible replies
    were valid; stored-memory persistence is supported for the small stored set; transformer/Spine
    HTTP handling was initially mistaken for durable memory growth; observability corrected only.
  - **SRG R-surface authority-fencing inventory** — docs-only; existing `R` / `R_band` / `is_crystal` /
    `heartbeat_class` fenced as guidance/continuity, not authority; **R-field NOT opened**, tests not
    authorized (`d1b357b`; §0 record `93f6519`).
  - **Model-API truthfulness audit — first tests-only characterization** — CLOSED-FOR-NOW; tests-only
    negative-property characterization (audit-observation non-consumption / payload-absence; `srg.is_crystal`
    anti-pattern by negation); **no** implementation / runtime / model call / schema / output control /
    memory write / database / substrate; test commit `384bf95`, validation `6 passed in 0.56s`;
    closure/status commit pending. (Lane framed across docs-only boundaries; see
    `PROJECT_ORIENTATION_MAP.md` §0.)
- **Current posture: HOLD.** No active implementation lane is open. The next move is an **operator/trio
  fork**, not a board-driven next-row selection — see `PROJECT_ORIENTATION_MAP.md` §0 (the live work
  order and fork list).

---

## 4. Main status table

| Layer | Status | Plain meaning | Evidence anchor | Next action |
|---|---|---|---|---|
| Thinking layer (selected surfaces) | HARDENED-FOR-NOW | Selected live thinking surfaces: deterministic routing + retrieval shaping (not deliberation); live path consumes only `MemoryPlan` | `thinking_controller.py`; Gate A C1–C5 (`test_gate_a_tests_only_locks_c1_c5.py`); tuned-scoring/ambiguity provenance checkpoints | none; pause |
| ReflectionTrace / observability floor | HARDENED-FOR-NOW | Ephemeral, content-free decision-shape observation; non-reentrant; stdlib-only | `reflection_trace.py`; `test_reflection_trace.py` + runner-parity; `48ae289` | none; reuse as scaffold |
| /thinking/debug read-only surface | HARDENED-FOR-NOW | Debug endpoint returns full chain (intentional, ephemeral, non-persisted); handler read-only-locked | `app.py:2667`; `TestDebugEndpointReadOnlyCompanion`; `e9212a7` | none |
| Spine thinking-alignment buffer | HARDENED-FOR-NOW | Bounded (200), in-memory, content-free advisory buffer + read endpoint. **Live population now wired (`679b403`):** the advisory live seam in `submit_task()` records the existing content-free `alignment` dict only into the same max-200 in-memory ring; `/spine/alignment` can now return non-empty `records` via the existing field (read surface/schema unchanged). No raw input/prompt/response/memory/seed/hidden CoT; no retrieval/prompt/persona/weight/identity/output-control effects; `app.py` docstring corrected in the same commit | `spine.py`; `test_spine_thinking_alignment_buffer.py`; `805a0ba`, `679b403` | none |
| Ephemeral structured cognition state | PARTIAL | **Slice 1 CLOSED (`4e164c3`)** routing scaffold; **Slice 2 IMPLEMENTED (`06a9536`)** deep-lane shaping (`TORMENT_COGNITION_SHAPING_V2`; `deep.top_k` +1 cap 4 iff `ambiguity_score >= 0.50` & deep enabled); **Slice 3 ALSO LANDED** core-lane shaping (`TORMENT_COGNITION_CORE_SHAPING_V1` / `_apply_cognition_core_shaping_v1`; `core.top_k` +1 cap 7 iff `confidence_need >= 0.60` & not governance/identity & core enabled); **geometric + relational-prominence shaping also live** — all default-off, plan-boundary, `top_k`/weight only. Tests-locked | `thinking_controller.py` (`_apply_cognition_shaping_v2`, `_apply_cognition_core_shaping_v1`); `test_ephemeral_cognition_state.py` (Slice 2 + Slice 3 sections); `4e164c3`, `06a9536` | lane paused; **NOT "Slice 3 pending" — Slice 3 landed**; further = **Slice 4+**, must be justified as real cognition capability (§5) |
| Candidate Gate D / Layer-1 private thinking | FRAMED | Eligible substrate-independent interior slice; **framed only**, pending operator selection | cognition roadmap §9; comparison frame `5472639`; pointer `3659089` | A0 readiness review (`d8a65e3`) concluded **DEFER / NO-OPEN** — valuable Layer-1 / Envelope-Audit version needs model-API/substrate authorization; full Gate D remains unopened |
| Envelope Audit | FRAMED | Requirement only (Document B §7); no module; only a coarse `requires_self_review` flag exists | Document B §7; `..._ENVELOPE_AUDIT_OBSERVABILITY_SHELL_DEFINITION_v0.1.md` | scoped as observability shell → **DEFER** (duplicates ReflectionTrace or needs a model-API track); Gate D unopened, operator/Codex-gated; A0 (`d8a65e3`) reaffirmed **DEFER** |
| Dream / incubation / Regime-B | DEFERRED | Offline reflection; no runtime exists; explicitly deferred + substrate-coupled | Document B §5; pre-substrate §3 | none; last |
| Private cognition / Document B chamber interior | FRAMED | Requirement doctrine **complete (promoted 2026-06-13)**; **zero runtime** | `TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md` | tied to Gate D decision |
| Guided memory layer | PARTIAL | Live retrieval/prompt-shaping + observability hardened; conformance of its automatic inputs only framed (Gate 4) | memory-to-prompt v0.2.x; `character_context`; guidance-without-coercion map | none clean (its open Q = Gate 4) |
| A0 explicit ingest nullification / outcome-observability finding | OPEN | A0 did not show normal memory storage defective; stored-memory restart persistence is supported for the stored set; recent-memory index was correct; later large-corpus retrieval was not tested because the expected corpus was not written. Transformer/Spine outcome observability is corrected in `9f124648`; explicit-write semantics remain unresolved; behavioral routing correction not yet authorized | `docs/TORMENT_A0_LIVED_USE_SCIENTIFIC_CHECKPOINT_2026_08_04.md`; A0 capture audit; observability commit `9f124648` | Block retrieval-quality tuning from the frozen basin, large-corpus recall claims, A1 subsystem activation, and vision integration until explicit-write semantics are resolved and A0 is re-established |
| Reader / projection safety (P4) | FRAMED | P4 contract framed + matched P2.5/P4 reconciliation closed; **runtime gates not built** | P4 contract; matched P2.5/P4 (§N13) | framing largely done; mechanics deferred |
| P4 / source-sameness / diagnostic-only | DEFERRED | Requirement-level posture only; mechanics substrate-coupled | matched P2.5/P4 §5.2; Gate 4 derived-anchors frame (Q-D2) | none now |
| Candidate store / governed admission | DEFERRED | Admission edge framed (Document A §8); carrier = Stage B/P6 | Document A §8/§11; reconciliation frame §8 | substrate-last |
| Seed-Gov / O6 / must-not-pin | PARTIAL | Doctrine framed + authored-seed write-once **test-locked**; revision/O6 mechanics deferred | Seed-Gov Blueprint §7; seed stability lock `4742b87`; gravity §N14 | mechanics deferred |
| Gate 4 old automatic writer paths | PARTIAL | Writers (gravity auto-canon, anchors, mood, warmth, role) **LIVE & UNRECONCILED**; conformance **questions framed, not answered** | 5 Gate 4 question frames; gap map; §N14 gravity memo; Gate B hazard inventory | answers paused/deferred (operator-gated) |
| Operator audit / contestability / revocability | PARTIAL | Provenance + audit endpoints live; candidate contestability/revocability framed; Track B parked (no resolver) | Ledger Observational-Boundary; ProvenanceV1; `/debug/provenance`; Track B (parked) | resolver = parked heavy lane |
| Database / substrate readiness | DEFERRED | Deliberately last; gated by Issue #54; still JSON/JSONL/SQLite scaffolding. **Stage A/Stage B boundary-framing checkpoint FILED read-only** — boundary + carry-forward constraints defined; **Stage B mechanics remain unopened** (no schema/storage/carriers/migration) | pre-substrate §1; DB/Substrate Doctrine Reconciliation; registry P0–P11; `..._STAGE_A_STAGE_B_BOUNDARY_FRAMING_v0.1.md` | framing satisfied → substrate-readiness **parks**; any Stage A/Stage B opening is a separate trio/operator authorization |
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
### Slice 2 — IMPLEMENTED (`06a9536`)

- **Rule:** default-off behind `TORMENT_COGNITION_SHAPING_V2`. When enabled: if
  `EphemeralCognitionState.ambiguity_score >= 0.50` **and** `deep.top_k > 0`, then `deep.top_k` nudges
  **+1**, capped at **<= 4**, **never reducing** an existing value.
- **Deep-disabled guard (ratified):** Slice 2 does **not** enable a disabled deep lane — never produces
  `retrieve_deep=False` paired with `deep.top_k=1`.
- **Scope preserved:** controller-produced `MemoryPlan` only · plan-boundary shaping only · only
  `top_k_by_lane["deep"]` · no weights · no core/relational/archive/collective · no retrieval booleans ·
  no `safety_constraints` · no `max_token_budget` · no packs · no `app.py` / `agent_loop.py` /
  `fabric.py` / `behavior_packs.py`.
- **Status meaning:** the lane moves from behavior-preserving *scaffold* (Slice 1) to a first **gated,
  reversible** retrieval-shaping improvement. Default-off, so default runtime behavior is unchanged. This
  does **not** newly complete the thinking layer — the selected thinking surfaces were already
  HARDENED-FOR-NOW before this lane (see §4 row 1).
- **Validation:** `126 passed in 1.46s`. Working tree after push clean (`## main...origin/main`).
- **Next:** lane paused. Further shaping rules, live archive/collective shaping, and any default-on
  decision remain deferred — see `docs/TORMENT_EPHEMERAL_COGNITION_STATE_SLICE_2_DEFINITION_v0.1.md`.

### Slice 3 — ALREADY LANDED (core-lane numeric shaping; board correction 2026-06-27)

**Board-staleness correction (docs-only; no code/test/behavior change).** The Slice 2 *Next* line
above is **superseded**: a Slice 3 core-lane shaping rule in fact landed, is wired into
`build_memory_plan`, and is tested. **The lane must no longer be treated as "Slice 3 pending."**

- **Rule:** default-off behind its own flag `TORMENT_COGNITION_CORE_SHAPING_V1` (separate from
  Slice 2). When enabled: if `EphemeralCognitionState.confidence_need >= 0.60` **and** the turn is
  neither governance- nor identity-sensitive **and** the core lane is already enabled
  (`core.top_k > 0`), then `core.top_k -> min(current + 1, 7)`, **never reducing**.
- **Scope:** controller-produced `MemoryPlan` only · plan-boundary only · `top_k_by_lane["core"]`
  only · no weights · no other lanes · no retrieval booleans · no `safety_constraints` /
  `max_token_budget` · no `app.py` / `agent_loop.py` / `fabric.py`. Independent of Slice 2.
- **Anchors:** `thinking_controller.py` — `_apply_cognition_core_shaping_v1` + its call in
  `build_memory_plan`; flag `_COGNITION_CORE_SHAPING_V1_ENABLE`. Tests:
  `test_ephemeral_cognition_state.py` §"Slice 3" (core flag off/on, below-threshold, governance- and
  identity-sensitive guards, cap / never-reduce). Non-control lock:
  `test_audit_memoryplan_shaping_noncontrol_characterization.py` references
  `_apply_cognition_core_shaping_v1`.

**Also already landed** (record only) as later default-off `MemoryPlan` shaping rules in
`build_memory_plan`: **geometric memory shaping v1** (`TORMENT_GEOMETRIC_MEMORY_SHAPING_V1`; lane
*weights* from coherence/stability) and **relational-prominence shaping v1** (relational lane weight
from `ambiguity_tolerance`, ceiling ≤ 0.99).

- **Lane status:** PARTIAL / paused — **not "Slice 3 pending."** Any further shaping is **Slice 4+**
  and must be explicitly justified as **real cognition capability, not another marginal retrieval
  nudge**; default-off / reversible / plan-boundary / content-free remain mandatory. This correction
  changes **no code, no tests, no behavior, no flags**, and opens **no new lane**.

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
