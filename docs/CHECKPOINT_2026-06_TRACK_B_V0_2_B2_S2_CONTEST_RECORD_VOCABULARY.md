# Checkpoint — Track B v0.2 → B2-S2 (ContestRecord vocabulary)

**Type:** Tracked closure checkpoint. Documentation only — records a landed,
isolated Slice-0 vocabulary. No production-code, schema, wiring, or
test-behavior change is authorized by this file, and it does **not** open
another gate.
**Closure recorded:** 2026-06-04.
**Anchors:** `docs/TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md`
(§5 record shape, §12 B2-S2 step), `docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md`,
and the Q2 lifecycle Slice-0 precedent (`torment_service/lifecycle.py`).

---

## 1. Closure identity & purpose

```
Gate:
Track B v0.2 -> B2-S2 (isolated ContestRecord vocabulary)

Closed commit:
f42b6ee feat(track-b): add isolated contest record vocabulary
```

**Track B v0.2 B2-S2 is CLOSED** as a bounded Slice-0 implementation: a
vocabulary, an immutable record, a deterministic fail-closed validator, and
pure serialization exist in code; the runtime does not import, construct,
read, persist, resolve, or apply them.

This mirrors the Q2 lifecycle Slice-0 posture:

```
vocabulary exists
validator exists
serialization exists
tests exist
runtime does not import it
runtime does not know about it
```

`ContestRecord` is a **provisional working name** (framing §13 #1), not a
final public naming decision.

Doctrine anchor (unchanged): a `ContestRecord` is a sidecar memo beside a
memory. It is not a command controlling character voice, response, identity,
or behavior. *Memory may shape context. Memory may not seize authority.*

---

## 2. Landed files

```
torment_service/contest_record.py
tests/test_contest_record.py
tests/test_contest_record_conformance_meta.py
```

No existing file was modified by the slice. No production module imports the
new module.

---

## 3. What landed

```
- Closed str-Enum vocabularies (contest-local; LifecycleState NOT imported):
    ContestScope   {agent, character, workspace}
    ContestActor   {agent, character, operator, user}
    ContestReasonClass {identity_conflict, material_disagreement,
                        scope_creep, audit_concern}
    ContestResult  {low-authority, released, audit-only, refuse}
  (workspace / user accepted as declared vocabulary only; runtime deferred)

- ContestRecordError(ValueError) carrying field + reason (lifecycle pattern).

- @dataclass(frozen=True, kw_only=True) ContestRecord:
    contest_id, contest_scope, contestant_actor, contestant_id,
    reason_class, contest_result, original_memory_preserved,
    contest_provenance (ProvenanceV1), and one-of-required target
    (contested_eid / candidate_handle), plus optional contest_reason.
  created_at_step / session_id intentionally NOT top-level — carried by
  the nested ProvenanceV1.

- Deterministic, side-effect-free validator (validate_contest_record /
  from_dict / __post_init__): UUID-shaped contest_id (never auto-generated),
  exactly-one-of target, UUID-shaped candidate_handle (no binding lookup),
  closed-vocabulary enums, non-empty contestant_id, optional-but-non-empty
  contest_reason, original_memory_preserved literal True (assertion only),
  fail-closed on unknown top-level keys, and the prohibition-only rule
  (non-operator actor may not route to refuse).

- Pure dict / JSON / JSONL-single-record-compatible serialization
  (to_dict / from_dict round-trip). No file writing.

- Mandatory importer-free AST conformance guard + an AST check that
  contest_record.py performs no filesystem/path-construction behavior.
```

**Axis caution preserved (framing §4):** `ContestResult.RELEASED` (the
authority-class value `"released"`) is **NOT** `LifecycleState.RELEASED`.
Distinct axes; the module deliberately does not import `LifecycleState`.

---

## 4. Review chain & corrections

```
GPT synthesis of the B2-S2 boundary
-> Codex adversarial review: ACCEPT WITH NARROW REVISIONS
-> implementation landed
-> Codex patch-level review: ACCEPT WITH NARROW PATCHES
-> blocking correction applied
-> Hilmir authoritative Windows run
```

**Blocking correction (nested-provenance canonicalization).** The first cut
coerced a serialized `contest_provenance` dict via `ProvenanceV1.from_dict()`,
which may synthesize defaults (`schema_version`, `write_path`, auto
`created_at_ts`, ...) and silently drop unknown keys — weakening the
fail-closed posture. The fix tightens **only** the `ContestRecord` boundary:

```
serialized contest_provenance dict
-> reconstruct via ProvenanceV1.from_dict(value)
-> require reconstructed.to_dict() == value exactly
-> else reject (ContestRecordError, reason="non_canonical_provenance")

already-valid ProvenanceV1 object -> accepted unchanged
```

Result: partial, synthesized, drifted, or extra-key nested provenance dicts
fail closed. `ProvenanceV1` itself remains **unchanged**; **no `SOURCE_CONTEST`
added**; nested-provenance behavior is not redesigned globally.

**eid convention grounding.** `contested_eid` is validated as `int` (bool
rejected), `>= 1`, with no existence lookup — grounded in local precedent:
`kernel/seed_entities.py` `_next_id: int = 1` and `memory_graph.py`
(`max_eid = 0` -> `_next_id = max_eid + 1`). Encoded as `MIN_VALID_EID = 1`.

---

## 5. Validation evidence

```
focused B2-S2 suite:
44 passed in 0.57s

full Windows suite (authoritative):
3727 passed, 5 skipped, 22 subtests passed in 89.38s
```

(Local Linux sandbox was unavailable during implementation; both runs above
are authoritative Windows runs performed by the operator.)

---

## 6. Boundary held

```
- no production wiring
- no writer
- no reader
- no persistence
- no resolver / effective-authority computation
- no retrieval influence
- no prompt influence
- no cognition coupling
- no MCP exposure
- no autonomy
- ProvenanceV1 unchanged; no SOURCE_CONTEST added
- no importer of contest_record in production (AST-guarded)
```

The record is a vocabulary + validation artifact only. It records nothing
live, applies nothing, and is not reachable from any runtime path.

---

## 7. Parked / not opened

```
- B2-S3: append-only separate-ledger writer/reader + replay tests
  (isolated; no consumer wiring) -- PARKED, not auto-open
- effective-authority resolver-boundary audit (framing §8.0) -- parked
- all framing §13 open trio decisions (final name, ledger shape,
  handle -> eid binding, operator-refuse provenance carry, complete
  operator authorization rule, first observation surface, derived index
  policy, effective-authority resolution, storage-readiness checkpoint)
- contest_provenance.source_type value (framing §5.2) -- parked
```

Opening B2-S3 requires a separate operator authorization after this
documentation chain is ratified. This checkpoint does not open it.

---

## 8. Provisional-name note

`ContestRecord` (and its enum member names) are provisional working names
adopted because the framing artifact uses them. The final public name remains
an open trio decision (framing §13 #1) and is not settled by this slice.

---

*End of checkpoint. Track B v0.2 B2-S2 closed (Hilmir, 2026-06-04, `f42b6ee`).
Documentation only. Not implementation authorization for any further slice.
B2-S3 requires its own authorization.*
