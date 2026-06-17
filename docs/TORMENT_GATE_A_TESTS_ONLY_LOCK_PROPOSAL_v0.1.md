# TORMENT Gate A — Tests-Only Lock Proposal v0.1

**DOCS-ONLY TESTS-LOCK PROPOSAL — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION.**

This proposal identifies tests-only regression-lock **candidates**. It does **not** authorize tests,
does **not** authorize behavior change, does **not** close Gate A, and does **not** open Gate B, P4,
Document B, dream/incubation, substrate, or implementation.

**Date:** 2026-06-17. **Lineage:** Gate A trace plan → characterization checkpoint (corrected) →
tests-only lock proposal (Claude) → Codex corrections carried → this filing.

---

## 1. Status and scope
- HEAD = origin/main = `c5b522c`. **Proposal only.** No tests, code, fixes, or locks authorized.

## 2. Codex corrections carried
- Use **"current direct-call absence"** and **"current routing characterization"** — never "safety."
- **C5 must not** assert a broad "not candidate admission" as a runtime negative over all future paths.
- **C5 may only** say the *current* Phase-7 route calls ordinary `fabric.ingest` with a compact summary
  and does **not** call any known Document-B / candidate / promotion-force API **in that path**.
- **C4 must exclude** `fabric.query` clamp behavior.
- **C1 must stay limited to advisory modules only.**

## 3. Candidate lock C1 — advisory-module direct-call absence
**Safe only as an AST/source guard.** Scope files: `thinking_controller.py`; `geometric_harvester.py`;
and the stance module (where `determine_stance` lives) **only if** stance is named in the final locked
claim. **Do not include** `app.py`, `agent_loop.py`, `fabric.py`, `spine.py`.

Forbidden direct-call names to assert absent (within the scoped advisory modules only): `ingest`,
`spawn_memory`, `add_memory`, `update_payload`, `flush_node`, `save_state`, `append_record`,
`reinforce`, `promote_chunk`, `promote_chunk_endpoint`, `gravity_correction`,
`_maybe_emit_identity_anchor`, `_maybe_emit_mood_drift`, `process_proposals`, `collective_reingest`.
Also treat raw `open(..., "w"/"a")` and `.write()` as forbidden **only in the advisory modules**.

- *Must assert:* the scoped advisory modules contain no calls to the names above.
- *Must NOT claim:* any downstream safety; that the advisory layer is "safe"; anything about
  `fabric.query` / ingest internals.

## 4. Candidate lock C2 — `/agent/query` consumes only MemoryPlan from the ThinkingController result
**Safe as a current handler-shape lock.**
- *Assert:* `/agent/query` calls `ThinkingController.think()`; reads `_result.memory_plan`; exports only
  `top_k_by_lane` and `weight_by_lane`; does **not** consume `response_draft`, `review_result`, or `stance`.
- *Must NOT claim:* that discarding those fields is correct or harmless.

## 5. Candidate lock C3 — `/agent/query` no direct ingest/promote/gravity
**Safe as a direct-call absence lock.**
- *Assert:* `/agent/query` makes no direct calls to `ingest`, `promote_chunk`, `promote_chunk_endpoint`,
  or `gravity_correction`; `/agent/query` calls `fabric.query`.
- *Must explicitly say:* this does **not** assert `fabric.query` is mutation-free.

## 6. Candidate lock C4 — MemoryPlan shape only
**Safe only as a shape/construction lock.**
- *Assert:* the lane booleans; `top_k_by_lane`; `weight_by_lane`; `safety_constraints`.
- *Do NOT test:* `fabric.query` clamp behavior; authority/admission influence; query mutation behavior.

## 7. Candidate lock C5 — Phase-7 ordinary-ingest routing characterization
**Safe only as a routing characterization with a fake-fabric spy.** Assert *current* behavior:
- under current gates, a non-blocked / non-no-op / response-present turn calls `fabric.ingest` once;
- the text comes from `_build_ingest_summary`;
- blocked / no-op / no-response skips ingest (if that is current behavior);
- the path does **not** call any known candidate / admission / promotion-force API.
- *Must NOT assert:* a broad "not candidate admission" as a future-freezing runtime negative; that the
  ordinary-ingest fan-out is correct authority behavior; that gravity / identity-anchor / mood /
  reinforcement hazards are acceptable; that future governed Document B admission must remain absent.

## 8. Rejected lock C6 — absence of Document B chamber / candidate store / dream runtime
**Do not test this absence.** It remains docs-only characterization, because a regression test on its
absence would create a tripwire against future governed implementation.

## 9. Residuals kept out of tests
- `fabric.query` retrieval-internal mutation durability / classification (warmup state, evolved SRG state).
- Spine / audit envelope durability outside the immediate return path.
- Full proof that `fabric.query` has no admission/authority writer.
- Ordinary-ingest fan-out reachability to the parked Gate B hazards.
- Phase-8 Stabilize `gravity_correction` route.

## 10. Forbidden tests
- Tests that bless `fabric.query` as mutation-free.
- Tests that endorse the ordinary-ingest fan-out as correct authority behavior.
- Tests that normalize the gravity / identity-anchor / promote hazards.
- Tests that implement or require P4 / Document B / Seed-Gov / database mechanics.
- Tests that lock private-cognition absence in a way that blocks future governed implementation.

## 11. Proposed order
docs-only proposal filed → Codex challenge if needed → operator authorization → **then** a tests-only
patch for **C1–C5 only** if approved. No auto-chain.

## 12. Exact forbidden openings
No production fixes, writer fixes, P4 implementation, Document B runtime, dream/incubation, candidate
store, durable private state, database / schema / storage / carrier / migration work, `canon_source`,
source-sameness mechanics, registry edits, old-doc mechanism adoption, monitoring, durable user-risk
scoring, autonomy, or behavior changes to promotion / gravity / identity-anchor behavior.

---

## Anti-drift footer

DOCS-ONLY TESTS-LOCK PROPOSAL — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION. Identifies candidates
(C1–C5) only; C6 rejected. Locks describe **current direct-call absence / current routing /
current shape** — never "safety," never a future-freezing negative, never normalization of the parked
hazards. Opens no Gate B / P4 / Document B / dream / candidate store / durable private state / database
/ substrate work; selects no `canon_source` / source-sameness; makes no registry amendment and reserves
no registry number. Old-doc quarantine binding. Guide, not control; audit observes authority and does
not become authority; nothing rewrites identity/canon/seed/soul. Tests remain a separate authorization.
