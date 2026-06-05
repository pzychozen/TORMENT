# Checkpoint — Track B v0.2 → B2-S4 (counter-contest event persistence)

**Type:** Tracked closure checkpoint. Documentation only — records a landed,
isolated counter-contest event vocabulary + append-only persistence slice. No
production-code, schema, wiring, or test-behavior change is authorized by this
file, and it does **not** open another gate.
**Closure recorded:** 2026-06-04.
**Anchors:** `docs/TRACK_B_V0_2_B2_S4_COUNTER_CONTEST_EVENT_FRAMING_v0.1.md`
(the ratified B2-S4 framing artifact),
`docs/TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md`
(parent framing §12 B2-S4 step, §8.0 resolver boundary, §13 parked decisions),
`docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S2_CONTEST_RECORD_VOCABULARY.md`,
`docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S3_CONTEST_LEDGER_PERSISTENCE.md`,
`docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md` (audit-visibility / Inv 14).

---

## 1. Closure status

```
Gate:
Track B v0.2 -> B2-S4 (counter-contest event vocabulary
                       + isolated append-only persistence)
-> CLOSED

implementation commit:
1a17d6f feat(track-b): add isolated counter-contest event persistence

framing commit:
36a8a84 docs(track-b): frame B2-S4 counter-contest events
```

**Track B v0.2 B2-S4 is CLOSED** as a bounded, isolated slice: a counter-contest
event vocabulary, one workspace-scoped append-only `contest_events.jsonl`
ledger with literal full-file replay, focused tests, and strict AST importer /
import-purity / no-resolver-surface guards. The runtime does not import or
consume either new module.

This continues the Slice-0 posture established by B2-S2 / B2-S3: the vocabulary
and storage exist in code, are tested, but are **not load-bearing** — no
production caller imports `CounterContestEvent` or `ContestEventLedger`, and the
slice resolves nothing, applies nothing, and touches no memory row or
`ContestRecord`.

Doctrine anchor (unchanged): a counter-contest is immutable observational
history. *Recording disagreement != resolving authority. Literal linked-event
replay != authority resolver. Append order = chronology only; append order !=
precedence. Persistence != consumer wiring. Memo != control.*

---

## 2. Files landed

```
torment_service/counter_contest_event.py
torment_service/contest_event_ledger.py
tests/test_counter_contest_event.py
tests/test_contest_event_ledger.py
tests/test_counter_contest_event_conformance_meta.py
tests/test_contest_event_ledger_conformance_meta.py
tests/test_contest_record_conformance_meta.py   (narrow allowlist adjustment)
```

The two new production modules are the only new runtime files; no other
production file was modified. The single edit to
`test_contest_record_conformance_meta.py` is the importer-allowlist widening
described in §7.

---

## 3. Event vocabulary boundary

`CounterContestEvent` is a frozen, immutable, kw-only dataclass with exactly six
required fields:

```
event_id
target_contest_id
contestant_actor
contestant_id
reason_class
event_provenance
```

Semantics:

```
- event_id            -> UUID-shaped, supplied externally, never auto-generated,
                         never derived from content
- target_contest_id   -> UUID-shaped structural validation only; structurally
                         identifies the ContestRecord the event claims to
                         contest; no existence lookup
- contestant_actor    -> closed vocabulary (reused ContestActor)
- contestant_id       -> non-empty string
- reason_class        -> closed required vocabulary (reused ContestReasonClass)
- event_provenance    -> ProvenanceV1; exact canonical nested serialization
                         required (partial / synthesized / unknown-key forms
                         fail closed), mirroring the B2-S2 boundary
- pure dict / JSON / JSONL-compatible serialization (to_dict / from_dict)
- deterministic fail-closed reconstruction; unknown top-level keys rejected
```

Explicit absences (a counter-contest event records disagreement only; it asserts
no outcome — these are not fields on the record, and passing any of them fails
closed as an unknown top-level key):

```
no contest_result
no status
no effective_status
no active/inactive
no overturned
no superseded
no winner
no precedence
no ranking weight
no confidence
no authority routing
```

There is intentionally **no operator-prohibition rule**: B2-S2 carries one only
because it has a `contest_result=refuse` value to gate; this event has no result
field, so there is no routing to restrict — any actor may *record* disagreement.

---

## 4. Ledger persistence boundary

```
Storage:
<data_dir>/workspaces/<workspace_id>/contest_memory/contest_events.jsonl
  - append-only
  - workspace scoped
  - sibling to the B2-S3 contest_records.jsonl (same contest_memory/ dir)
  - path-safe construction via the existing safe_slug +
    _canonical_storage_root + _child_path + _guard idiom

Surface:
append_event(event) -> None
list_events() -> list[CounterContestEvent]
list_events_for_contest(contest_id) -> list[CounterContestEvent]

append_event
  - validated CounterContestEvent INSTANCE only; raw dict rejected (TypeError)
  - append is the only write; no ID generation, no append-time duplicate scan,
    no target lookup, no row mutation, no governance, no cache, no lock, no fsync

list_events
  - literal unbounded full-file forward walk; append order preserved
  - fail closed: malformed non-empty JSONL line raises (ContestEventLedgerError
    "malformed_line"); invalid event propagates CounterContestEventError;
    duplicate event_id raises (ContestEventLedgerError "duplicate_event_id")
    during the read
  - no silent skip, no silent collapse, no cache, no index

list_events_for_contest
  - validates the contest_id query argument for UUID shape only (a query-shape
    check, NOT a target-existence check)
  - routed through the same fail-closed list_events() read, then filters
    literal matches in append order only
```

The fail-closed read posture deliberately departs from the permissive
skip-silent behavior of `closure_ledger.py` / `baton_ledger.py`: a silently
skipped counter-contest event would hide a contest, contradicting Inv 14. This
matches the governance choice already made in B2-S3.

---

## 5. Observational boundary

```
append order = chronology only
append order != precedence

list_events_for_contest() = literal linked history only
not resolver output

counter-contest persistence != authority application
```

The reader exposes literal linked events and nothing more — no derived state,
no effective view, no latest-wins rule, no count-as-signal interpretation, no
winner, no precedence, no ranking weight. The effective-authority resolver
remains entirely outside this slice (parent framing §8.0 / §13 #8). An
AST guard (`test_contest_event_ledger_defines_no_resolver_surface`) locks the
ledger against growing a resolver-/status-/ranking-shaped def surface.

---

## 6. Integrity boundary

```
target_contest_id is structurally UUID-shaped only

target existence is not checked

dangling-linkage policy remains parked

the slice records a claimed linkage
not a proven linkage
```

A structurally valid `target_contest_id` that matches no `ContestRecord` is
stored and read back literally — dangling linkage remains representable, never
resolved and never an error. Whether dangling linkage should one day fail on
append, fail on replay, surface in an audit report, or stand as a historical
anomaly is a separate later integrity gate (B2-S4 framing §9).

---

## 7. Vocabulary reuse boundary

```
ContestActor
ContestReasonClass
-> reused unchanged from torment_service/contest_record.py
   (single source of truth; no duplicated vocabulary layer)

tests/test_contest_record_conformance_meta.py
-> exact importer allowlist widened narrowly:
   counter_contest_event.py is now permitted to import contest_record
   (alongside contest_ledger.py); still an exact-path set, NO contest_* /
   *_event prefix exemption
```

No generic vocabulary framework was introduced. `ContestRecord` was not
refactored. `ProvenanceV1` is unchanged; no `SOURCE_CONTEST` added. The only
cross-module imports from `counter_contest_event.py` are the two reused
vocabulary enums plus `ProvenanceV1`.

---

## 8. Isolation guards

AST conformance tests preserve, structurally:

```
- exact importer allowlists
  (counter_contest_event importable only by contest_event_ledger;
   contest_event_ledger importable by no ordinary runtime consumer)
- zero ordinary runtime consumers of either new module
- no authority-path imports (memory_graph / fabric / spine / governance)
- no retrieval imports
- no prompt imports
- no cognition imports
- no MCP imports
- no app imports
- no resolver-like helper surface in the event ledger
- counter_contest_event performs no filesystem behavior
```

---

## 9. Validation evidence

```
focused B2-S4 suite:
72 passed in 1.66s

full suite:
3812 passed, 5 skipped, 22 subtests passed in 67.52s

Codex adversarial implementation review:
ACCEPT
no blocking findings
no corrections required
```

Codex non-blocking watch-items (recorded, not acted on during this docs
closure): append order is chronology only (not precedence);
`list_events_for_contest()` is literal linkage only (not status derivation); and
a harmless unused `Enum` import in `counter_contest_event.py` — not a boundary
issue, deliberately not reopened for a code edit during closure.

(Local Linux sandbox was unavailable during implementation; both suite runs
above are authoritative Windows runs performed by the operator.)

---

## 10. Parked / not opened

```
- target-existence integrity policy
- dangling-linkage policy
- candidate_handle -> eid durable binding
- counter-contest result routing
- operator authorization completion
- effective-authority resolver-boundary audit (framing §8.0)
- first observation surface
- runtime consumer wiring
- retrieval surfacing
- prompt surfacing
- cognition coupling
- MCP exposure
- automatic firing
- autonomy
- fsync / locking / multi-process coordination -> Cluster 5
- generic storage redesign
- dependency-maintenance work
```

Opening any of these requires its own audit-first framing cycle and a separate
operator authorization. This checkpoint opens none of them.

---

## 11. Stop condition

```
B2-S4 is closed.

No production consumer wiring exists.
No resolver exists.
No retrieval influence exists.
No prompt influence exists.
No cognition coupling exists.
No MCP exposure exists.
No automatic firing exists.
No autonomy expansion exists.

The repo returns to a resting checkpoint.
The next slice is not auto-opened.
```

---

*End of checkpoint. Track B v0.2 B2-S4 closed (Hilmir, 2026-06-04, `1a17d6f`).
Documentation only. Not implementation authorization for any further slice. Any
next Track B slice requires a fresh audit-first framing cycle and explicit
operator authorization.*
