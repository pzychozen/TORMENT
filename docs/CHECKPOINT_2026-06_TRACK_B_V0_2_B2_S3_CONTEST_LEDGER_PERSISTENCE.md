# Checkpoint — Track B v0.2 → B2-S3 (ContestLedger persistence)

**Type:** Tracked closure checkpoint. Documentation only — records a landed,
isolated append-only persistence slice. No production-code, schema, wiring, or
test-behavior change is authorized by this file, and it does **not** open
another gate.
**Closure recorded:** 2026-06-04.
**Anchors:** `docs/TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md`
(§3.3 sibling ledger family, §6 separate-ledger boundary, §12 B2-S3 step),
`docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S2_CONTEST_RECORD_VOCABULARY.md`,
`docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md` (Inv 14 / audit-visibility),
and the `closure_ledger.py` / `baton_ledger.py` single-file JSONL precedents.

---

## 1. Closure identity & purpose

```
Gate:
Track B v0.2 -> B2-S3 (isolated ContestLedger persistence)

Closed commit:
9c027a0 feat(track-b): add isolated contest ledger persistence
```

**Track B v0.2 B2-S3 is CLOSED** as a bounded, isolated persistence slice:
**Option A only** — one workspace-scoped append-only `contest_records.jsonl`
with a literal full-file reader, plus replay tests and strict importer guards.
The runtime does not import or consume the ledger.

This continues the Slice-0 posture established by B2-S2: the storage layer
exists in code, is tested, but is **not load-bearing** — no production caller
imports `ContestLedger`, and it resolves nothing, applies nothing, and touches
no memory row.

Doctrine anchor (unchanged): a `ContestRecord` is a sidecar memo beside a
memory. *Memory may shape context. Memory may not seize authority. Literal
ledger read != authority resolver. A persistence slice != consumer wiring.*

---

## 2. Landed files

```
torment_service/contest_ledger.py
tests/test_contest_ledger.py
tests/test_contest_ledger_conformance_meta.py
tests/test_contest_record_conformance_meta.py   (narrow allowlist adjustment)
```

`contest_ledger.py` is the only new production module; no other production
file was modified. The single edit to `test_contest_record_conformance_meta.py`
is the importer-allowlist narrowing described in §3.

---

## 3. What landed

```
- Storage: one workspace-scoped append-only JSONL at
    <data_dir>/workspaces/<workspace_id>/contest_memory/contest_records.jsonl
  Option A ONLY. No contest_events.jsonl. Path-safe construction via the
  existing safe_slug + _canonical_storage_root + _child_path + _guard idiom
  (identical to closure_ledger.py / baton_ledger.py).

- Writer: ContestLedger.append_record(record: ContestRecord) -> None, the
  only write. Accepts an already-validated ContestRecord INSTANCE only; a raw
  dict is rejected (TypeError) -- the writer is not a validation bypass. No ID
  generation, no append-time duplicate scan, no target lookup, no row
  mutation, no governance, no cache, no lock, no fsync.

- Reader: ContestLedger.list_records() -> list[ContestRecord], literal,
  UNBOUNDED, full-file forward walk; append order preserved; each non-empty
  line rebuilt through ContestRecord.from_dict. No cache, no index, no
  per-eid/status/aggregation helper.

- Fail-closed read posture (governance, not convenience): a malformed
  non-empty JSON line raises ContestLedgerError("malformed_line"); an invalid
  record propagates ContestRecordError; a duplicate contest_id raises
  ContestLedgerError("duplicate_contest_id") during the read. Empty lines are
  skipped.

- Guards:
  * tests/test_contest_record_conformance_meta.py narrowed: an EXACT-path
    allowlist now permits torment_service/contest_ledger.py (and only it) to
    import contest_record; every other production module remains forbidden
    (no contest_* prefix exemption -- a future importer needs an explicit
    guard edit + a new gate).
  * tests/test_contest_ledger_conformance_meta.py (new): AST guard that no
    ordinary production module imports contest_ledger, plus an import-purity
    guard that contest_ledger.py imports none of memory_graph / fabric /
    spine / governance / retrieval / cognition / mcp_server / app -- the
    structural enforcement of "no row mutation / no target lookup / no
    resolver / no consumer wiring".
```

---

## 4. Governance-driven departures from the event-ledger precedent

```
closure_ledger.py / baton_ledger.py:
  malformed JSONL line -> skip silently (forgiving audit trail; payload wins)

contest ledger (B2-S3):
  malformed non-empty line  -> raise (fail closed)
  invalid ContestRecord     -> raise (fail closed)
  duplicate contest_id      -> raise during read
```

Rationale: the contest ledger is itself the durable authority-action record.
Silently skipping a malformed contest line would *hide a contest*, directly
contradicting Inv 14 ("contest increases audit visibility; never a hiding
mechanism"). So B2-S3 deliberately does not inherit the permissive
skip-silent behavior; `conflicts.py` (fail-loud parse) is the closer
governance match. Duplicate detection is performed at **read** (a full walk
already happens there), not at append, because an append-time scan without
locking is non-atomic and would give false assurance (TOCTOU).

No fsync and no lock — matching every JSONL ledger in the repo. Storage
hardening (`JSONL-NO-FSYNC`, `NO-MULTI-PROCESS-WRITE-COORDINATION`) remains a
named, deferred Cluster 5 concern; B2-S3 does not open it.

---

## 5. Validation evidence

```
focused B2-S3 suite:
19 passed in 1.14s

full Windows suite (authoritative):
3743 passed, 5 skipped, 22 subtests passed in 82.03s
```

(Local Linux sandbox was unavailable during implementation; both runs above
are authoritative Windows runs performed by the operator.)

---

## 6. Boundary held

```
- Option A only; no contest_events.jsonl
- no consumer wiring; no production importer of contest_ledger (AST-guarded)
- no original-row mutation; no target existence lookup; no candidate_handle -> eid binding
- no resolver / effective-authority computation; no authority overlay
- no retrieval influence; no prompt influence; no character_context exposure
- no cognition coupling; no MCP exposure; no automatic firing; no autonomy
- ProvenanceV1 unchanged; no SOURCE_CONTEST added
- import-purity guard forbids authority/consumer-surface imports in contest_ledger.py
```

---

## 7. Parked / not opened

```
- B2-S4: counter-contest linkage + event semantics (contest_events.jsonl,
  reader-derived counter_contests) -- PARKED, not auto-open
- effective-authority resolver-boundary audit (framing §8.0) -- parked
- all framing §13 open trio decisions (final name, ledger shape for
  counter-contests, handle -> eid binding, operator-refuse provenance carry,
  operator authorization rule, first observation surface, derived index
  policy, effective-authority resolution, storage-readiness checkpoint)
- fsync / locking / multi-process coordination -> Cluster 5
```

Opening B2-S4 requires a separate operator authorization after this
documentation chain is ratified. This checkpoint does not open it.

---

## 8. Provisional-name note

`ContestRecord` and `ContestLedger` (and their member/method names) are
provisional working names adopted because the framing artifact uses them. The
final public names remain an open trio decision (framing §13 #1) and are not
settled by this slice.

---

*End of checkpoint. Track B v0.2 B2-S3 closed (Hilmir, 2026-06-04, `9c027a0`).
Documentation only. Not implementation authorization for any further slice.
B2-S4 requires its own authorization.*
