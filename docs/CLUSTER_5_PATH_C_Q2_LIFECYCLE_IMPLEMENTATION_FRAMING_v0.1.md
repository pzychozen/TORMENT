# Cluster 5 §9.3 Path C — Q2 Lifecycle Implementation Framing v0.1

**Status:** Implementation framing draft. **Not doctrine.** Not authorization to patch. Not a code change. Not a schema change.
**Date:** 2026-05-22
**Author:** Claude (drafted for trio: pzychozen + GPT + Claude); ratified by trio on 2026-05-22.
**Mode:** Pre-code implementation frame. No code, no schema, no tests, no migrations, no automation, no remediation, no implementation authorization. Each step ends in a review gate.
**Audit baseline:** `HEAD = 4dd4f6f`
**Parent framing:** `docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`
**Sibling framing:** `docs/CLUSTER_5_PATH_C_Q1_IMPLEMENTATION_FRAMING_v0.1.md` (Q1 / Shape B — substantively complete)
**Anchor docs:** Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 v0.1.

**Predecessors:**

- Cluster 5 §9.3 Path C audit Q2 lock (lifecycle-durability gap)
- Path C framing (`c1cddd1`)
- Q1 implementation framing (`a181cef`)
- Q1 Shape B implementation (`11dd0ba` Slice 0 through `4dd4f6f` H4d — substantively complete)
- Q2 design opening framing — Shape D (hybrid canonical lifecycle envelope) ratified

---

## 1. Purpose

Convert the ratified Shape D lifecycle envelope into a stable design boundary that all future Q2 implementation must obey, mirroring the pattern that produced Q1's eight successful slices (Slice 0 → H4d). This document is the bridge between ratified design and the first reviewable patch.

It does not patch, edit, schema, test, or implement anything. After this artifact is committed, subsequent slices (envelope type, validation helper, wiring) become admissible.

---

## 2. Ratified Q2 invariant

> **A consumer reading a memory row must be able to determine its lifecycle state — including whether the row is authoritative for that state or whether a join to a named side channel is required — without guessing.**

This is the Q2-specific application of the Path C invariant. Three corollaries:

1. **Lifecycle may live on the row or in a side channel — but the row must announce which.**
2. **Multi-source states must collapse to a single canonical value at write time, not recompute live at each read.**
3. **The absence of a lifecycle field is itself a lifecycle state** (`unset`) and must be representable.

---

## 3. Chosen Q2 shape

**Shape D — Hybrid canonical lifecycle envelope.**

The envelope is a self-describing block on every memory row that announces both the canonical current state and whether the row is authoritative for that state. Side channels are honored where they are the genuine source of truth (e.g., `review_queue.jsonl`); the envelope names them explicitly.

The envelope is the structural enforcement of §2's invariant: a consumer reading the row sees the envelope and can determine status without guessing.

---

## 4. Proposed envelope fields (design level)

Working shape — exact field names and structure deferred to the Slice 0 schema commit:

```
"lifecycle_status": {
    "state":                      <state-name string>,
    "is_authoritative_on_row":    <bool>,
    "requires_join":              null | {
        "side_channel":  <named channel>,
        "join_key":      <field name>
    },
    "set_by": {
        "actor":  <"operator" | "system" | "user" | other ratified value>,
        "via":    <"api" | "compression" | "review_ratification" | other>,
        "at":     <unix_ts>
    },
    "history_ref":                null | {
        "ledger":          <path>,
        "last_event_id":   <id>
    }
}
```

**Field rationale:**

- **`state`** — the canonical current lifecycle state from the ratified vocabulary. Single-valued.
- **`is_authoritative_on_row`** — the load-bearing boolean. If `true`, the row alone is the truth. If `false`, the consumer must consult `requires_join` before any authoritative decision.
- **`requires_join`** — null when the row is authoritative; a structured pointer otherwise. The pointer names the side channel and join key so the consumer cannot guess where to look.
- **`set_by`** — write-time provenance. Required for audit, lifecycle-history reconstruction, and (critically) for the `protected` dual-source collapse — `set_by.via` records which derivation source resolved the state to its canonical value.
- **`history_ref`** — optional pointer to an event ledger when history matters (closure-style sequences). Null for states that do not have an event-stream backing.

**What the envelope deliberately is NOT:**

- Not a typed wrapper class at the row layer. (A typed accessor for *consumers* may follow — deferred.)
- Not an immutable record — `state` and `set_by` change over time as transitions occur.
- Not a substitute for governance flags. Lifecycle answers *"what stage is this in?"*; governance answers *"what authority does this carry?"* The two remain separate dicts.

---

## 5. Candidate state vocabulary (provisional)

A working closed set — **not yet ratified.** The final vocabulary is deferred to a separate ratification step (analogous to the Q1 Step C `role` vocabulary ratification).

Provisional initial set:

- `unset` — no lifecycle declared. Default for legacy memories that pre-date Q2 and for newly-spawned memories before lifecycle is assigned. The "absence is also a state" requirement from corollary 3.
- `scratch` — preliminary / draft material. Not yet committed to system use.
- `released` — material formally released for normal operational use.
- `protected` — material immune to automated mutation (collapses the current dual-source `canon / kind / tier / srg.is_crystal` derivation into a single canonical value at write time).
- `review_pending` — material awaiting human ratification. Row-side; `is_authoritative_on_row=false`; `requires_join` points at `review_queue.jsonl`.
- `active` — material in normal operational status (parallels `baton_lifecycle.status == "active"`).
- `consumed` — material terminally used (parallels `baton_lifecycle.status == "consumed"`).
- `archived` — material removed from active surfaces but preserved.

States deferred for possible later inclusion (closure-style):

- `committed`, `ratified`, `revised` — currently derived from `closure_ledger` events. Whether the envelope subsumes these or coexists with the ledger is a downstream design question.

The closed set must be ratified before any code lands. The exact list above is intentionally provisional.

---

## 6. How the envelope handles the four audit markers

**`released`** — row-authoritative.

```
{ "state": "released", "is_authoritative_on_row": true, "requires_join": null,
  "set_by": {"actor": <...>, "via": <...>, "at": <...>}, "history_ref": null }
```

Consumer reads the row and knows the state. No join.

**`scratch`** — row-authoritative.

```
{ "state": "scratch", "is_authoritative_on_row": true, "requires_join": null, ... }
```

Consumer reads the row and knows the state. No join.

**`protected`** — row-authoritative, *with dual-source collapse at write time*.

```
{ "state": "protected", "is_authoritative_on_row": true, "requires_join": null,
  "set_by": {"actor": "system", "via": "canon" | "kind" | "tier" | "srg_crystal" | "governance_flag", ...},
  ... }
```

The existing live-recompute in `compression.derive_retention_tier` (and `is_compression_protected`'s dual surface) is replaced by a write-time decision: whichever derivation source originally resolved the state writes the envelope with `set_by.via` recording the source. Future reads consult the envelope only. The dual-source disagreement risk identified in the audit disappears by construction.

**`review_pending`** — row-side announcement, side-channel-authoritative.

```
{ "state": "review_pending", "is_authoritative_on_row": false,
  "requires_join": {"side_channel": "review_queue.jsonl", "join_key": "eid"},
  "set_by": {...}, "history_ref": null }
```

Consumer reads the row and *immediately knows* a join is required. The review queue file remains the authoritative system of record for resolution status; the envelope's job is to make the join requirement structurally explicit instead of implicit.

---

## 7. Implementation sequence (proposal — no code)

Each step ends in a review gate. **No step authorizes the next.** The shape mirrors Q1's eight-step sequence.

**Step Q2-A — Lifecycle write-surface audit (read-only).**
Identify every place in `torment_service/` that currently writes lifecycle-bearing state: `compression.py`'s `derive_retention_tier`, `is_compression_protected` callers, `migration/review_queue.py` write sites, `baton_lifecycle` assignment in `fabric.py`, `closure_ledger` event emissions, any other surfaces. Output: a candidate boundary map analogous to Q1's Step A. No code.

**Step Q2-B — Envelope-type / schema contract.**
Decide the exact field names, the closed state vocabulary, and the validation rules. Output: a schema contract note. No code.

**Step Q2-C — Authoritative-on-row decision table.**
For each state in the ratified vocabulary, decide `is_authoritative_on_row` defaults and the canonical `requires_join` target. Lock the table. Output: a decision-table note. No code.

**Step Q2-D — Protected dual-source collapse plan.**
Decide how the existing `canon / kind / tier / srg.is_crystal` derivation is normalized into `state="protected"` at write time. Identify the migration path for existing memories that carry the four contributing fields but no envelope. Output: a collapse plan. No code.

**Step Q2-E — Review-queue join formalization.**
Decide the named side-channel format and how `lifecycle_status.requires_join.side_channel = "review_queue.jsonl"` is resolved by consumers. Decide whether existing consumers (admission-policy code paths) need to be refactored to consult the envelope first, then the queue. Output: a join-resolution contract. No code.

**Step Q2-F — Validation / enforcement primitive.**
Decide whether to introduce a parallel to `assert_authoritative_memory(value)` for lifecycle — e.g., `assert_lifecycle_row_authoritative(envelope)` that raises when a consumer tries to make a decision on a `requires_join != null` envelope without performing the join. This is the Q2 analog of the H3 authority guard. Output: an enforcement-primitive contract. No code.

**Step Q2-G — Test category framing.**
Catalog the test categories required, mirroring Q1's Step G. Categories include: envelope shape tests, vocabulary closed-set tests, authoritative-vs-join distinguishability, protected-collapse-at-write tests, review-queue-join tests, migration/back-fill, absence-is-a-state (`unset`), and a Path C §4.1 conformance meta-test. Output: a test-category list. No tests.

**Step Q2-H0 — Slice 0 plan.**
The smallest possible reviewable code slice. Likely shape:

- New file `torment_service/lifecycle.py` (or extension of an existing module) — defines the envelope dataclass / TypedDict / pydantic model, the closed-set state enum, validation helpers, and the enforcement primitive.
- New test file `tests/test_lifecycle_envelope.py` — exercises the schema, validation, and enforcement primitive in isolation.
- **No production wiring.** No existing code modified. The envelope vocabulary exists in code but is not yet load-bearing — exactly the Q1 Slice 0 pattern.

**Step Q2-H1 onward — Wiring slices.**
Each subsequent slice wires the envelope into one surface at a time: write at compression / admission paths, read at consumer paths, protected-collapse refactor, review-queue join formalization, migration of existing memories. Each slice ≤ ~200 lines of diff with parallel tests, following the Q1 H1 → H4d pattern.

The sequencing is intentional: **vocabulary first, wiring later.** Production behavior changes only at H1+, not at H0.

---

## 8. Acceptance tests / test categories

Each P0 test category from Q1 has a Q2 analog. Priority tiers (P0 safety-bearing, P1 contract-completion, P2 hygiene) follow Q1's Step G template.

**P0 (safety-bearing):**

1. **Envelope-shape contract** — every envelope serialization carries `state`, `is_authoritative_on_row`, `requires_join`, `set_by` with the correct types.
2. **State vocabulary closed set** — only ratified state values are accepted; unknown states are rejected at write time.
3. **Authoritative-vs-join distinguishability** — a consumer can determine `is_authoritative_on_row` from the envelope alone, without external knowledge.
4. **`requires_join` consistency** — when `is_authoritative_on_row=false`, `requires_join` must be a populated dict naming a known side channel; conversely, when `true`, `requires_join` must be null.
5. **Protected collapse at write** — the dual-source `canon / kind / tier / srg.is_crystal` inputs are resolved to one canonical `state="protected"` at write time; live recomputation is rejected.
6. **Review-queue join authority** — a consumer that ignores `requires_join` on a `review_pending` envelope must be detectable (likely via the Step Q2-F enforcement primitive).
7. **Path C §4.1 conformance meta-test** — for every lifecycle-bearing row in the test corpus, the lifecycle status is recoverable from the row alone (including the "needs join" instruction). No guessing required.

**P1 (contract-completion):**

8. **`unset` representability** — memories without an explicit lifecycle still produce a meaningful envelope (default `state="unset"`) rather than raising or returning null.
9. **`set_by` provenance round-trip** — actor / via / at survive serialization and re-load intact.
10. **History-ref optionality** — envelopes without history work normally; envelopes with history correctly reference an existing ledger entry.

**P2 (hygiene):**

11. **Legacy-marker compatibility** — during transition, the envelope must not contradict any persistent legacy lifecycle hints (e.g., `payload["compressed"]`, `baton_lifecycle.status`). Either deprecate the legacy markers or assert consistency.
12. **Migration / backfill correctness** — when an existing memory without an envelope is read, the lazy-derive path produces a sensible default envelope.

---

## 9. Known risks and compliance debt

**R1 — Protected dual-source collapse is invasive.**
`derive_retention_tier` in `compression.py` and `is_compression_protected` in `governance.py` both recompute protected status live. Replacing live recompute with envelope reads requires careful migration so that existing memories without an envelope still classify correctly during transition. Likely needs a lazy-derive shim in the read path.

**R2 — Closure ledger overlap.**
`closure_ledger` currently provides closure-state via event-kind sequence (`committed`, `ratified`, `revised`). Whether the envelope subsumes these states or coexists with the ledger as a side channel (with `history_ref` pointing at the ledger) is a meaningful design question that Q2-B / Q2-C must answer.

**R3 — Baton lifecycle overlap.**
`baton_lifecycle` is the existing gold-standard nested lifecycle dict. The envelope's structure should likely supersede `baton_lifecycle`, or at least co-exist while announcing one as authoritative. Migration story needed.

**R4 — Migration of existing memories.**
No memory in the system currently carries a lifecycle envelope. The Slice 0 envelope type can ship without wiring (matching Q1), but the first wiring slice must handle "legacy memories without an envelope" gracefully.

**R5 — Consumer discipline for `requires_join`.**
The envelope announces a join is needed; it does not enforce that the join happens. Step Q2-F's enforcement primitive (an `assert_lifecycle_row_authoritative` analog) is the structural protection.

**R6 — Two systems of record for `review_pending`.**
The envelope on the row says "needs join", and the review queue file holds the resolution state. Drift between the two (row marks `review_pending` but the queue has already resolved, or vice versa) is a real failure mode that needs a defined reconciliation rule.

**R7 — Inline import / module-level import question.**
Same question that arose in Q1. Whether `lifecycle.py` imports go inline at first wiring (matching Q1's H4 precedent) or at module level is a deferred preference.

---

## 10. Explicit non-decisions

This framing deliberately does not decide:

- **The closed state vocabulary.** The provisional set in §5 is a *starting point*, not a commitment.
- **The exact schema field name** (`lifecycle_status` is working; alternatives admissible).
- **The migration strategy** — lazy-on-read vs eager-backfill — deferred.
- **The typed accessor / wrapper-type question** — whether a `LifecycleEnvelope` Python type wraps the dict (parallel to `NonAuthoritativeDeepHit` for Q1) — deferred to Step Q2-F.
- **The closure-ledger / baton-lifecycle overlap resolution** — see R2, R3.
- **The protected dual-source collapse migration shim** — see R1.
- **Whether `review_queue.jsonl` is the canonical side-channel name** or whether a new "side channel registry" namespace is needed.
- **Schema files** (`schemas/provenance.py`, `schemas/memory_proposal.py`) — no field added, renamed, or typed by this frame.
- **Custom DB question** — still parked, out of scope.
- **Q3 affect-provenance design** — opens after Q2 framing is committed.
- **Q1 optional items** (H2a / `repair_embeddings` / γ / inline-import cleanup / non-governance survey) — independent.
- **Working-tree CRLF state** — still parked.

---

## 11. Acceptance gate for every step

Every output of Steps Q2-A through Q2-H must pass the ratified Q2 invariant:

> A consumer reading a memory row must be able to determine its lifecycle state — including whether the row is authoritative for that state or whether a join to a named side channel is required — without guessing.

Any step output that requires the reviewer to "know somehow" the lifecycle status fails the gate, regardless of correctness on other axes.

---

## 12. Position relative to Q1

Q1 Shape B and Q2 Shape D share a structural pattern: **the row announces its own truth shape.**

| Surface | Q1 (deep hits) | Q2 (lifecycle) |
|---|---|---|
| Carrier | `DeepRetrievalHit` / `OrphanedDeepHit` | `lifecycle_status` envelope |
| Truth-shape announcement | `authority_status.authoritative` + `requires_rehydration` + `role` | `is_authoritative_on_row` + `requires_join` + `state` |
| Join target when not authoritative | source row in `MemoryGraph.entities` | named side channel (e.g., `review_queue.jsonl`) |
| Rejection primitive at consumer boundary | `assert_authoritative_memory(value)` | `assert_lifecycle_row_authoritative(envelope)` (proposed) |

The architectural parallel is intentional. Once Q3 (affect-provenance) follows the same pattern, TORMENT will have a uniform "derivative or row announces its own authority shape" idiom across all three Path C audit findings.

---

## 13. Status of related artifacts

- **Q1 baseline finding** — locked.
- **Q2 baseline finding** — locked.
- **Q3 baseline finding** — locked.
- **Consolidated Path C report** — locked.
- **Path C framing** — committed at `c1cddd1`.
- **Q1 implementation framing** — committed at `a181cef`.
- **Q1 Shape B implementation** — substantively complete (`11dd0ba` Slice 0 → `4dd4f6f` H4d). 8 commits, 69 tests passing.
- **Q2 design opening framing** — ratified inline.
- **Q2 implementation framing** — recorded by this artifact.
- **Spine doctrines (Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 v0.1)** — unchanged.
- **Doctrine status of this framing** — none. This is a ratified implementation-facing plan, not a doctrine promotion.

---

## 14. Recommended next move after this commit

**Open Step Q2-A — Lifecycle write-surface audit.** Read-only audit pass producing a candidate boundary map of every code path that currently writes lifecycle-bearing state in `torment_service/`. Mirrors Q1's Step A.

Step Q2-A is read-only. Step Q2-A is framing/audit-only. Step Q2-A does not authorize Step Q2-B.

---

### Held throughout

No patches. No code edits. No schema edits. No tests. No type definitions. No API design. No doctrine promotion. No `repair_embeddings` modification. No custom DB design. No storage rewrite. No Q3 work. No spine doctrine modification. No Q1 optional items touched.

**Spine state:** `HEAD = 4dd4f6f`. Cluster 5 §9.3 Path C Q2 implementation frame ready for commit. Step Q2-A unlocks after this artifact is committed and reviewed.
