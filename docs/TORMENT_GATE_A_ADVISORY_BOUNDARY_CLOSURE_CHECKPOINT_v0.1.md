# TORMENT Gate A — Advisory-Boundary Closure Checkpoint v0.1

**DOCS-ONLY CLOSURE CHECKPOINT — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION.**

This checkpoint closes Gate A **only** as an advisory-boundary characterization plus a
tests-only regression lock. It does **not** certify the runtime safe, does **not** fix any
writer hazard, does **not** open Gate B, P4, Seed-Gov, Document B, dream/incubation, or any
database/substrate work, and makes **no** registry amendment.

**Date:** 2026-06-17. **HEAD = origin/main = `9086ae0`.** Working tree clean.

---

## 1. Framing

Gate A asked a bounded question: where does the live advisory/thinking layer sit relative to
memory-authority writers, and what can be locked as *current* behavior without blessing the
parked hazards? The answer was reached by characterization (read-only tracing) followed by a
tests-only lock of the characterized boundary. Gate A closes on that scope and nothing wider.

Closure scope, stated plainly: **advisory-boundary characterization + tests-only lock.** Any
broader reading — that the runtime is proven safe, that mutation is absent, that writer
hazards are resolved — is explicitly out of scope and contradicted by §3 and §5 below.

## 2. Characterization lineage

- `03cf734` — opened Gate A, characterization-only.
- `3316073` — filed the advisory-boundary characterization.
- `c5b522c` — corrected the baseline-wording of the characterization checkpoint.
- `8e88d9c` — filed the tests-only lock proposal (candidates C1–C5; C6 rejected).
- `13d7add` — carried the Codex corrections into the proposal.
- `9086ae0` — committed the tests-only C1–C5 locks.

## 3. Gate A truth (corrected)

- **No direct advisory authority writer was found.** The characterized advisory path does not
  itself call a memory-authority writer directly.
- **This does not mean no mutation anywhere.** Absence of a *direct* advisory writer is a
  narrow finding, not a global no-mutation claim.
- **`fabric.query` has retrieval-internal state effects.** It is treated as opaque and **not**
  mutation-free; Gate A neither proves nor blesses its internals.
- **`/agent/query` consumes only `MemoryPlan` fields for retrieval shaping** — specifically the
  lane top-k and weight maps — and discards the other `ThinkingResult` fields at that seam.
  Gate A does not claim that discarding them is correct or permanent.
- **`AgentRunner.run_turn` Phase-7 can ordinary-ingest advisory-shaped response summaries.**
  A non-blocked, non-no-op, response-present turn routes a compact summary to ordinary
  `fabric.ingest`. This is characterized as *current* routing, not endorsed as correct
  authority behavior.

## 4. Tests locked (C1–C5; C6 rejected)

- **C1 — advisory-module direct-call absence.** AST / resolved-call-name absence of forbidden
  writer calls in the named advisory modules (`thinking_controller.py`,
  `geometric_harvester.py`, `stance_policy.py`). Resolved-name matching, not raw substring; a
  benign `reingest` substring is not flagged as an `ingest` call.
- **C2 — `/agent/query` consumes only `MemoryPlan`.** Handler-shape lock: calls
  `ThinkingController.think()`, reads `memory_plan`, exports only `top_k_by_lane` and
  `weight_by_lane`, and references none of `response_draft` / `review_result` / `stance`.
- **C3 — `/agent/query` no direct ingest/promote/gravity.** Fake/spy-boundary lock: the
  handler calls `fabric.query` and makes no direct call to `ingest`, `promote_chunk`,
  `promote_chunk_endpoint`, or `gravity_correction`; `fabric.query` is handed an opaque,
  pass-through result and is **not** asserted mutation-free.
- **C4 — `MemoryPlan` shape only.** Dataclass shape lock: lane booleans, `top_k_by_lane`,
  `weight_by_lane`, `safety_constraints`. No query-clamp, admission-influence, retrieval-
  mutation, or lane-behavior-inside-query testing.
- **C5 — Phase-7 ordinary-ingest routing characterization only.** Fake-fabric spy: a content
  turn ingests once with text from `_build_ingest_summary`; blocked / no-op / no-response turns
  skip ingest; the path touches no candidate / admission / promotion-force API. The fake models
  no downstream fan-out, so the real `fabric.ingest` fan-out is neither inspected nor blessed.
- **C6 — intentionally rejected / absent.** Testing the absence of Document B / chamber / dream
  / candidate store / durable private state would freeze that absence against future governed
  implementation, so no such test exists.

## 5. Residuals NOT closed by Gate A

Gate A leaves the following explicitly open. None is touched, fixed, normalized, or blessed
here:

- `fabric.query` retrieval-internal mutation classification.
- Ordinary-ingest fan-out.
- `gravity_correction` automatic `canon=True`.
- `_maybe_emit_identity_anchor`.
- `POST /promote` force bypass.
- `mood_drift → centroid → gravity_correction → canon=True`.
- AgentRunner Phase-8 Stabilize gravity route.
- P4 / source-sameness.
- Document B private cognition.
- Seed-Gov.
- Dream / incubation.
- Database / substrate mechanics.

## 6. Evidence

- **Focused Gate A tests:** passed (operator-reported; exact pytest counts/timings not
  captured in this checkpoint — to be appended verbatim if later provided). Command of record:
  `python -m pytest tests\test_gate_a_tests_only_locks_c1_c5.py -v`.
- **Full suite:** passed (operator-reported; exact counts/timings not captured here).
- **`git status --short --branch`:**

  ```text
  ## main...origin/main
  ```

- **`git log --oneline -8`:**

  ```text
  9086ae0 (HEAD -> main, origin/main, origin/HEAD) test(engine): lock Gate A advisory characterization
  13d7add docs(engine): carry Gate A tests-only corrections
  8e88d9c docs(engine): propose Gate A tests-only locks
  c5b522c docs(engine): correct Gate A checkpoint baseline wording
  3316073 docs(engine): characterize Gate A advisory-boundary trace
  03cf734 docs(engine): open Gate A advisory-boundary characterization
  0ff0769 docs(engine): file cognition roadmap sequencing map
  f309b0a docs(engine): authorize L2 Stage-B-to-framing decision
  ```

## 7. Closure posture

- Gate A does **not** certify the whole runtime safe.
- Gate A does **not** fix writer hazards.
- Gate A does **not** open database construction.
- The next likely step is **Gate B — writer-authority hazards**, pending explicit operator
  authorization. The operator may instead choose a separate closure/review step first; Gate A
  closing does not auto-chain into any successor gate.

---

## Anti-drift footer

DOCS-ONLY CLOSURE CHECKPOINT — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION. Closes Gate A
only as advisory-boundary characterization + tests-only lock (C1–C5; C6 rejected). Records
*current* boundary truth — never "safety," never a future-freezing negative, never
normalization of the parked hazards in §5. Opens no Gate B / P4 / Seed-Gov / Document B / dream
/ incubation / candidate store / durable private state / database / substrate work. Makes no
registry amendment and reserves no registry number. Guide, not control; audit observes
authority and does not become authority; memory may guide context, memory may not seize
authority. Tests and any successor gate remain separate authorizations.
