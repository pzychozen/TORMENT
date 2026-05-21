# Cluster 5 §9.3 Path C — Q1 Implementation Framing v0.1

**Status:** Ratified implementation-facing frame. **Not doctrine.** Not authorization to patch. Not a code change. Not a schema change.
**Date:** 2026-05-21
**Author:** Claude (drafted for trio: pzychozen + GPT + Claude); ratified by trio on 2026-05-21.
**Mode:** Pre-code implementation frame. No code, no schema, no tests, no migrations, no automation, no remediation, no implementation authorization. Each step ends in a review gate.
**Audit baseline:** `HEAD = c1cddd1`
**Parent framing:** `docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`
**Anchor docs:** Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`), Cluster 2 v0.1 (`docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`), Track B v0.1 (`docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`), Cluster 5 v0.1 (`docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md`).

**Predecessors:**
- Cluster 5 §9.3 Path C audit Q1 lock (deep-export governance preservation gap)
- Q2 lock (lifecycle-durability gap)
- Q3 lock (affect-provenance gap)
- Consolidated Path C report
- Path C framing (`c1cddd1`)
- Phase 7 / Step 1 — DeepMemory authority-shape comparison (Shape A / B / C)
- Phase 7 / Step 2 — source-row survival audit (Shape B viability verdict: viable, survival currently implicit)
- Phase 7 / Step 3 — orphan behavior ratification (hybrid β/α/γ)
- Phase 7 / Step 4 — enforcement ratification (hybrid API boundary / wrapper / marker)
- Phase 7 / Step 5 — this implementation frame

---

## 1. Purpose of this frame

This document records the ratified Q1 implementation plan **before any code is written**. It is the bridge between ratified design and the first reviewable patch. After this artifact is committed, Step A (consumer API boundary identification, read-only) becomes admissible.

This frame does not patch, edit, schema, test, or implement anything. It produces an implementation-facing plan.

---

## 2. Chosen Q1 contract

**Shape B — `DeepMemory` is non-authoritative.** It is a derivative retrieval object / echo. It must rehydrate from the source row before any authority, admissibility, autonomy, sharing, identity, lifecycle, affect-attribution, or governance decision.

The contract is the Q1-specific application of the Path C invariant. `DeepMemory` carries signal; it does not carry authority.

---

## 3. Ratified orphan behavior

A `DeepMemory` is orphaned when its source row cannot be rehydrated.

- **β at runtime** — orphans are filtered out of normal consumer query results.
- **α restricted to operator diagnostics** — orphans surface only on a dedicated, explicitly-named diagnostic/admin surface.
- **γ for maintenance** — controlled maintenance sweeps remove orphans physically from the deep store with an audit trail.

**Hard boundary:** orphaned `DeepMemory` must never enter cognition, autonomy, sharing, identity, lifecycle, affect-attribution, or governance decision paths.

---

## 4. Ratified enforcement

Three layers at three abstraction levels, each catching a different failure mode:

- **API boundary — primary defense.** Consumer-facing APIs return rehydrated source rows only. Raw `DeepMemory` is unreachable from cognition / autonomy / character / sharing / lifecycle / affect-attribution / governance code paths. β filtering is implemented at this boundary.
- **Wrapper/type — structural reinforcement.** Code that legitimately holds a deep record (admin, diagnostic, telemetry, maintenance) holds it as a non-authoritative typed object. The type itself prevents misuse at the language level.
- **Field marker — diagnostic transparency.** Serialized deep records preserve the non-authoritative status after Python type information is erased — for logs, telemetry, audit dumps, and the γ sweep's audit trail.

**The API boundary does the real safety work. The wrapper/type and the marker reinforce it.**

| Layer | Failure mode it catches |
|---|---|
| API boundary | Consumer attempts to read raw `DeepMemory` from a cognition/autonomy path |
| Wrapper type | Consumer has a deep record in hand and tries to pass it where memory is required |
| Field marker | Deep record has been serialized to JSON/log/telemetry; reader needs to know status without language-level types |

---

## 5. Implementation sequence (no code yet)

Each step is read-only or framing-only. Each step ends in a review gate. **No step authorizes the next.**

**Step A — Identify the consumer API boundary.** Read-only audit pass that lists every entry point in `fabric.py` / `spine.py` / `mcp_server.py` / `app.py` through which a deep record could currently reach a cognition or autonomy code path. Output: a candidate boundary map. No code.

**Step B — Define the wrapper/type contract.** Decide names (e.g. `DeepMemoryHit`, `OrphanedDeepMemoryHit`, or alternatives) and the minimum API for the wrapper (what it carries, what it deliberately does not carry, what `unwrap()` / `rehydrate()` operation produces an authoritative result). Decide whether this is a dataclass, a frozen class, a `typing.NewType`, or a runtime-checked wrapper. Output: a wrapper-type contract note. No code.

**Step C — Define the marker contract.** Decide field name and serialization shape (e.g. `authoritative: false`, `requires_rehydration: true`, or a structured `derivative_role: "retrieval_echo"`). Decide where the marker appears (only when serialized? on the wrapper object directly? both?). Output: a marker-shape note. No code.

**Step D — Define the orphan-filtering point.** Decide the single chokepoint in the read path where β filtering runs. Candidates include `DeepMemoryStore.query`, a layer immediately above it in `fabric`, or the spine fast-path. Pick the location that makes orphan-filtering structurally hard to bypass. Output: a chokepoint-location decision. No code.

**Step E — Define the diagnostic orphan surface.** Decide where α lives — likely a separate `mcp_server` admin endpoint or a `fabric` diagnostic method. The surface is explicitly named for orphans; the name is the disclaimer. Output: a diagnostic-surface contract. No code.

**Step F — Define the maintenance/sweep posture.** Decide γ's trigger (manual operator invocation? scheduled? threshold-based?), its audit-trail shape (where the sweep log lives), and its idempotency rules. Output: a sweep-posture decision. No code.

**Step G — Identify tests that would be needed later.** Catalog the test categories required to ratify the implementation: orphan-filter test, wrapper-type rejection test at authority APIs, rehydration-required test, marker-survives-serialization test, sweep-idempotency test, audit-trail completeness test. Output: a test-category list. No tests.

**Step H — Implementation slice 0.** Only after Steps A–G are reviewed: the smallest possible code change that produces a reviewable patch under all ratified contracts. Likely candidate: introduce the wrapper type *without* yet routing anything through it, so the surface area can be inspected before it is load-bearing.

---

## 6. Acceptance gate for every step

Every output of Steps A–H must pass the Path C §4.1 acceptance test before review:

> A future memory derivative passes this framing only if a consumer can determine, without guessing, whether the derivative is authoritative by itself or must rehydrate from canonical context before use.

Any step output that requires the reviewer to "know somehow" what is authoritative fails the gate, regardless of correctness on other axes.

---

## 7. Known compliance debt

**`fabric.repair_embeddings(max_nodes=N)`** (`fabric.py:1140–1230`) can rewrite `nodes.jsonl` non-preservingly when the `max_nodes` parameter is set and `modified=True`. This is the only currently-identified path that can create orphans against the Shape B contract.

**Posture under this frame:** the compliance issue is **named, not remediated.** Two admissible resolutions, deferred:

- Bring `repair_embeddings` into compliance — stream unprocessed rows through the rewrite so no row is ever dropped.
- Accept `repair_embeddings` as an explicit maintenance boundary — pair it with the γ sweep so any orphans it creates are caught by the contract's existing handling.

The choice is deferred to a separate decision step (likely between Step F and Step H, since γ's posture interacts with it). No code change is authorized here.

---

## 8. Explicit non-decisions

This implementation frame deliberately does not decide:

- **Q2 lifecycle contract** — `released` / `scratch` / `protected` / `review-pending` shape, dual-source `protected`, review-queue join. Path C framing requires this be addressed; the order is deferred.
- **Q3 affect-provenance** — user-confirmed vs system-inferred attribution; whether to extend `provenance_v1` or wire `user_confirmed` into affect.
- **Custom DB question** — still parked. Will not be opened until the contract layer is settled.
- **Storage rewrite** — out of scope at this layer entirely.
- **Doctrine promotion** of any Step-A-through-G output. Each is a framing artifact until a separate doctrine commit step is opened.
- **Schema files** (`schemas/provenance.py`, `schemas/memory_proposal.py`) — no field added, removed, renamed, or typed by this frame.
- **Working-tree CRLF state** — still parked.

---

## 9. Status of related artifacts

- **Q1 baseline finding** — locked (deep-export governance preservation gap).
- **Q2 baseline finding** — locked (lifecycle-durability gap).
- **Q3 baseline finding** — locked (affect-provenance gap).
- **Consolidated Path C report** — locked.
- **Path C framing** — committed at `c1cddd1`.
- **Acceptance test (§4.1)** — ratified.
- **Phase 6 working-tree delta lock** — first pass complete (line-ending-only).
- **Phase 7 Steps 1–4** — ratified inline.
- **Q1 implementation framing** — recorded by this artifact.
- **Spine doctrines (Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 v0.1)** — unchanged.
- **Doctrine status of this framing** — none. This is a ratified implementation-facing plan, not a doctrine promotion. A separate doctrine commit, if desired, would be a future controlled step.

---

## 10. Recommended next move after this commit

**Open Step A — Identify the consumer API boundary.** Read-only audit pass producing a candidate boundary map of every entry point in `fabric.py` / `spine.py` / `mcp_server.py` / `app.py` through which a raw `DeepMemory` record could currently reach a cognition or autonomy code path. Output: a candidate boundary map for review.

Step A is read-only. Step A is framing/audit-only. Step A does not authorize Step B.

---

### Held throughout

No patches. No code edits. No schema edits. No tests. No type definitions. No API design. No doctrine promotion. No `repair_embeddings` modification. No custom DB design. No storage rewrite. No Q2 or Q3 work. No spine doctrine modification.

**Spine state:** `HEAD = c1cddd1`. Cluster 5 §9.3 Path C Q1 implementation frame ready for commit. Step A unlocks after this artifact is committed and reviewed.
