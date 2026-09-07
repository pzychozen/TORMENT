# TORMENT Database Convergence

## P3 Motif-Member Namespace Reconciliation Qualification v0.1

Starting head: `07d4fab58c2d58bb80ac50d54d5ad2cdef4c2acf`

This is a disposable qualification only. It does not contact the real root,
resume real P3, or authorize P4--P7.

## Archaeology and previous failure

`motifs.json` is the current-state source owned by one workspace/domain motif
registry. Its `members` field is an integer EID list; it does not persist a
member scope. `motif_events.jsonl` is deliberately excluded from semantic
admission, and `contributing_agents` remains aggregate motif state rather than
a per-member ownership map.

The previous P3 B1 implementation applied the incorrect law:

```text
motif source namespace + numeric EID = member object
```

That law reproduced `P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH` on the shared
`audit_smoke_v0_2 / personal` registry: each of its EIDs 1--4 belonged to the
paired private `smoke_runner` source namespace. Numeric EID equality across
isolated scopes is not identity.

## Qualified binding law

For each individual motif member EID, the P3 topology coordinator supplies a
finite, same-workspace set of eligible materialized memory source namespaces.
Admission queries aliases only inside that supplied set:

```text
one valid LEGACY_CORE_NODE alias -> admit that exact object
zero aliases                    -> UNRESOLVED / quarantine
multiple aliases                -> AMBIGUOUS / quarantine
```

There is no global EID lookup, first-match lookup, private/shared preference,
event replay, or contributing-agent tie-break. The membership `MEMBER`
endpoint preserves the resolved object's current semantic scope; the motif ID
alias itself remains bound to its registry namespace.

P3 derives its eligible set solely from the frozen request's materialized
private/shared scope bindings for the same workspace. Empty, declared-empty,
and other-workspace scopes cannot become candidates. The service does not
discover scope namespaces from SQLite.

An existing local-only `QUARANTINED` admission is immutable. If the explicit
bounded P3 set is broader, the repair records a separate reconciliation batch
and artifact-record identity. A prior successful admission remains the single
durable motif result and is not duplicated.

## Qualification matrix

`tests/test_substrate_legacy_motif_admission.py` contains production-shaped
fixtures Q1--Q10:

- Q1 preserves local single-namespace admission.
- Q2 admits the shared-registry/private-owner shape with four exact private
  endpoints and no duplicate source objects or EID aliases.
- Q3 proves a single motif resolves members independently across private A,
  shared, and private B scopes.
- Q4 and Q5 prove private/shared and two-private numeric collisions quarantine
  with `AMBIGUOUS_LEGACY_MOTIF_MEMBER_ALIAS` and no partial motif publication.
- Q6 proves zero candidates quarantine with
  `UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS` and no placeholder.
- Q7 proves an imported but non-eligible other-workspace alias is not found.
- Q8 and Q9 prove diagnostic event and contributing-agent temptations cannot
  resolve ambiguity.
- Q10 proves a successful unique cross-scope retry reuses its one motif and
  membership set.
- A separate recovery fixture proves a local-only quarantine is retained while
  the broader explicit candidate bound records one idempotent reconciliation
  admission.

`tests/test_substrate_root_p3_source_admission.py` additionally proves P3 B1
passes the coordinator-owned workspace candidate set into the carrier path and
preserves cross-scope member endpoints. No B2/B3/B4 behavior was redesigned.

## Copied real-carrier reproduction

The preserved predecessor and completion carriers were copied, never changed,
to:

```text
C:\TORMENT\TORMENT_administration\p3-motif-member-namespace-qualification-07d4fab-20260907
```

The disposable runner first applied the old singleton shared namespace law to
the copied `audit_smoke_v0_2` snapshots. It reproduced four quarantines with
`UNRESOLVED_LEGACY_MOTIF_MEMBER_ALIAS`. It then used only the copied private
`smoke_runner` and shared `personal` source namespaces. Every recovered member
had candidate count one:

| Motif | EID | Canonical private object |
| --- | ---: | --- |
| `motif_personal_0001` | 1 | `83aaf861-a098-40bd-b4a2-e1e1f2609714` |
| `motif_personal_0002` | 2 | `147305a6-8dff-46e7-bee5-47055a1b59f2` |
| `motif_personal_0003` | 3 | `ec81a2d1-7ba3-4cb1-86d3-6a258c8d520b` |
| `motif_personal_0004` | 4 | `453a8b88-2965-439c-a68b-bc0b28e3` |

The copied completion carrier identity is
`3777e8fc585504b652b10bcbf8e9eb217323c25d9b937092049b97e7666a1989`.
The copied shared snapshot is `0c460a51-66b4-4538-8cc4-e91123ac0553`; the
paired private snapshot is `db0de0eb-c7f6-4159-b703-074caf66329f`. The
successful repaired retry was idempotent and added no second motif or
membership relationships.

## Regression evidence

- `tests/test_substrate_legacy_motif_admission.py`: 20 passed.
- `tests/test_substrate_root_p3_source_admission.py`: 13 passed.
- `tests/test_substrate_existing_workspace_multi_scope_admission.py`,
  `tests/test_substrate_generalized_runtime_readiness.py`, and
  `tests/test_substrate_integrated_migration_rehearsal.py`: 11 passed.
- `tests/test_substrate_migration_runtime_readiness.py`,
  `tests/test_substrate_migration_runtime_motif_projection.py`,
  `tests/test_substrate_migration_runtime_motif_regeometry_projection.py`,
  `tests/test_substrate_migration_runtime_zero_member_motif_projection.py`,
  and `tests/test_substrate_root_normalization.py`: 49 passed.

The complete targeted run of those ten modules passed 93 tests.

No BGE model was loaded. The copied carrier fixture used no B2/B3/B4 execution
beyond the existing P3 carrier test's established B1/B2 coverage.

## Files changed

```text
torment_service/substrate/migration/motif_admission.py
torment_service/substrate/migration/rehearsal.py
torment_service/substrate/migration/root_p3_source_admission.py
torment_service/substrate/migration/existing_workspace_admission.py
torment_service/substrate/migration/existing_workspace_multi_scope_admission.py
torment_service/substrate/objects.py
tests/test_substrate_legacy_motif_admission.py
tests/test_substrate_root_p3_source_admission.py
docs/PROJECT_ORIENTATION_MAP.md
docs/TORMENT_DATABASE_CONVERGENCE_P3_MOTIF_MEMBER_NAMESPACE_RECONCILIATION_QUALIFICATION_v0.1.md
```

## Required invariants

```text
MOTIF_REGISTRY_IS_WORKSPACE_DOMAIN_SCOPED = YES
MOTIF_MEMBER_SCOPE_IS_PERSISTED_EXPLICITLY = NO
MOTIF_MEMBER_BINDING_IS_PER_MEMBER = YES
CROSS_SCOPE_MOTIF_MEMBERSHIP_REQUIRED_BY_LEGACY_SHAPE = YES
NUMERIC_EID_EQUALITY_ACROSS_SCOPES_IS_MEMBER_IDENTITY = NO
GLOBAL_EID_LOOKUP_ALLOWED = NO
HEURISTIC_TIE_BREAKING_ALLOWED = NO
MOTIF_EVENTS_SEMANTIC_AUTHORITY = NO
CONTRIBUTING_AGENTS_PER_MEMBER_AUTHORITY = NO
UNIQUE_BOUNDED_CANDIDATE_ADMISSION = QUALIFIED
ZERO_CANDIDATE_QUARANTINE = QUALIFIED
MULTI_CANDIDATE_QUARANTINE = QUALIFIED
MIXED_SCOPE_SINGLE_MOTIF = QUALIFIED
UNRELATED_WORKSPACE_BINDING = REFUSED
REAL_FAILURE_SHAPE_REPRODUCED_FROM_CARRIER_COPY = YES
REAL_FAILURE_SHAPE_RECOVERABLE_WITHOUT_HEURISTIC = YES

REAL_ROOT_CONTACT = NONE
REAL_ROOT_WRITE = NONE
REAL_P3_RESUME = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
```

The separately authorized next operation, if any, is real preserved-carrier
P3 recovery. This qualification grants no such authority.
