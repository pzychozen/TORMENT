# TORMENT Memory Substrate — P9D-I4C-R1 archaeology closure

## Broad-private conflict read roundtrip — no implementation

**Status:** documentation-only closure, uncommitted and unpushed.

**Archaeology base:** `f2626ba5aa0e7daf4d686ce2a37434830d80ecd8`
(`qualify-phase-9d-i4f-b-shared-precommit-composition-parity`).

## Scope and preserved key law

I4C-R1 was opened after I4F-A corrected the broad-private conflict writer. The
writer remains lawful external evidence; this closure neither weakens it nor
reopens the separately-qualified I4C true-split path.

```text
private = (scope, agent_id, eid)
shared = (scope, domain_id, eid)
origin-less = ignored for qualified lookup
```

The qualified key model, conflict record schema, `_ReadOnlyConflictRegistry`,
`_build_conflict_map`, `_conflict_hit_key`, conflict heuristic, and query/trace
ordering are unchanged.

## Archaeology result

The proposed implementation premise was falsified by source composition:

```text
native workspace conflict bindings = admitted shared domains only
query/trace conflict domains       = ranked shared domains, then existing override
private hits                       = retrieved separately
conflict application               = canonical shared hit only
```

`NativePublicWorkspaceView` constructs read-only conflict registries for its
`domains` collection, which is the admitted shared-domain sequence. The native
query uses the frozen Fabric query surface; its conflict map receives the
ranked shared domains (or the existing override followed by that ranking).
Legacy trace has the same domain selection and map construction.

Although `_build_conflict_map` can represent a private-origin key, query and
trace apply the resulting evidence only when the hit scope is `shared` and the
hit is canonical. Adding an applicable private registry to the map would not
apply a private conflict penalty, evidence, or score effect.

`trace` also remains in the explicit public Fabric fallthrough census. There
is no qualified `NativePublicRuntime.trace` surface. I4C-R1 does not add one.

## Stop condition and decision

Closing the proposed reader/writer roundtrip would require changing the frozen
shared-only conflict-application condition and qualifying a new native public
trace surface. That is not a read-domain-composition repair or migration
parity, and it is not authorized for I4C-R1.

```text
PRIVATE_HIT_CONFLICT_SCORING_CHANGE = NOT_AUTHORIZED
I4C_R1_READER_IMPLEMENTATION = NOT_AUTHORIZED
NATIVE_PUBLIC_TRACE_IMPLEMENTATION_FOR_I4C = NOT_AUTHORIZED

I4C_R1_ARCHAEOLOGY = CLOSED_BY_STOP_CONDITION
I4C_R1_IMPLEMENTATION = NOT_AUTHORIZED
I4C_R1_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = NOT_APPLICABLE_TO_LEGACY_QUERY_TRACE_LAW
I4C_R1_REQUIRED_BEFORE_I4G_FINAL_FREEZE = NO
I4C_R1 = CLOSED_WITHOUT_IMPLEMENTATION

I4C_TRUE_SPLIT_CONFLICT_PARITY = FROZEN_PRESERVED
I4C_BROAD_PRIVATE_CONFLICT_WRITER = PASS_WRITE_SIDE_ONLY
I4C_BROAD_PRIVATE_CONFLICT_EXTERNAL_OWNER = PRESERVED
I4C_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = NOT_PART_OF_LEGACY_QUERY_TRACE_LAW
I4C_BROAD_PRIVATE_CONFLICT_SYSTEM_PARITY = NOT_CLAIMED

I4G_NATIVE_TRACE_QUALIFICATION_QUESTION = OPEN
I4G_READY_TO_OPEN_AFTER_CLOSURE_COMMIT = YES

LEGACY_QUERY_SEMANTICS_CHANGED = NO
CONFLICT_SCORING_FORMULA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

The I4G question is only whether final native public lifecycle/capability
parity requires a qualified native public trace route. A future trace route
must preserve actual legacy trace semantics; lawful broad-private external
conflict evidence does not authorize private-hit conflict scoring.

## Implementation and validation boundary

```text
PRODUCTION_CHANGES = 0
TEST_CHANGES = 0
CONFLICT_SCORING_FORMULA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
```

No runtime suite was required or run: this closure records source archaeology
and an authorization stop condition. I4G was not started.
