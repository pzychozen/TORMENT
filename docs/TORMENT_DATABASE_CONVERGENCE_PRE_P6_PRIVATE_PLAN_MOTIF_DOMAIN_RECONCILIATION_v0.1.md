# TORMENT SQLite Database Convergence — Pre-P6 Private-Plan `motif_domain_id` Reconciliation

## Result

The private-plan omission is intentional and lawful. The real P4 root has 76
private plans with `motif_domain_id=None`; P2 deliberately keeps this field
absent because a private memory scope is not itself a motif domain. The post-P7
native reader had incorrectly applied the one-domain shared-lane assumption to
private lanes. The bounded repair is therefore **Model D**: private and shared
lanes use different, already-authorized motif read paths. No private identity
or domain was invented, and no P1–P7 durable contract was changed.

```text
PRIVATE_PLAN_NATIVE_CONTINUATION_RECONCILIATION = PASS
STARTING_HEAD = 3b8f41b9dc2483f7fd436f02d0a670c255567f89
FINAL_HEAD = recorded by the commit which adds this reconciliation record
ORIGIN_MAIN = 3b8f41b9dc2483f7fd436f02d0a670c255567f89 at work start
TRACKED_WORKTREE = clean at start; only the files listed in this record changed; pre-existing untracked files untouched

PRIVATE_PLAN_COUNT = 76
PRIVATE_PLAN_WITH_MOTIF_DOMAIN_ID = 0
PRIVATE_PLAN_WITHOUT_MOTIF_DOMAIN_ID = 76
PRIVATE_PLAN_MOTIF_DOMAIN_ABSENCE_CLASSIFICATION = INTENTIONAL_AND_LAWFUL

FIRST_CONSUMER_REQUIRING_MOTIF_DOMAIN_ID = NativeQualifiedQueryReadModel._private_motif_domains
CONSUMER_ACTUAL_USE = construct private-lane motif memberships and fixed private post-write geometry; it did not route private memory identity
PRIMARY_RECONCILIATION_MODEL = MODEL_D__SPLIT_PRIVATE_AND_SHARED_RUNTIME_PATHS
MOTIF_DOMAIN_AUTHORITY_SOURCE = per-operation admitted shared-domain identity; private scope remains bound by admitted workspace, agent, native namespace, and semantic scope
NEW_SEMANTIC_AUTHORITY_INVENTED = NO

PRIVATE_SCOPE_ISOLATION_PRESERVED = YES
SHARED_SCOPE_ISOLATION_PRESERVED = YES

P1_CONTRACT_CHANGE_REQUIRED = NO
P2_CONTRACT_CHANGE_REQUIRED = NO
P3_CONTRACT_CHANGE_REQUIRED = NO
P4_CONTRACT_CHANGE_REQUIRED = NO
P5_CONTRACT_CHANGE_REQUIRED = NO
P6_CONTRACT_CHANGE_REQUIRED = NO
P7_CONTRACT_CHANGE_REQUIRED = NO
POST_P7_RUNTIME_CHANGE_REQUIRED = YES

DISPOSABLE_PRIVATE_QUERY = PASS
DISPOSABLE_SHARED_QUERY = PASS
DISPOSABLE_PRIVATE_TEXT_SEARCH = PASS
DISPOSABLE_PRIVATE_VECTOR_SEARCH = PASS
DISPOSABLE_PRIVATE_WRITE = PASS
DISPOSABLE_PRIVATE_REINFORCEMENT = PASS
DISPOSABLE_RESTART_RECOVERY = PASS

LEGACY_FALLBACK = NO
DUAL_READ_AUTHORITY = NO
DUAL_WRITE = NO
POST_ACTIVATION_CERTIFIED_REFUSAL_MEMORY_LEAK = NO
POST_ACTIVATION_CERTIFIED_REFUSAL_MOTIF_LEAK = NO

CORRECTED_P0_P8_REHEARSAL = PASS (2 passed in 30.63s)
CLAUDE_ADVERSARIAL_REVIEW = UNAVAILABLE_NO_CLAUDE_OR_ANTHROPIC_CONNECTOR; internal bounded adversarial review completed

REAL_ROOT_WRITE = NONE
REAL_ROOT_UNCHANGED = YES
REAL_P5_EXECUTED = NO
REAL_P6_EXECUTED = NO
REAL_P7_EXECUTED = NO

FOCUSED_TESTS = PASS (11 passed in 9.98s)
BROADER_TESTS = PASS (55 passed in 66.51s)
GIT_DIFF_CHECK = PASS

P5_READINESS = READY
P6_READINESS = READY
P7_CONTINUATION_READINESS = READY
POST_P7_RUNTIME_READINESS = READY
TERMINAL_STATUS = PASS
NEXT_AUTHORIZATION_BOUNDARY = REAL_P5, only if separately authorized
```

## 1. Contract trace and classification

The durable path is:

```text
legacy source scope
  -> P1 source identity / root scope key
  -> P2 RootSourceScopePlan
  -> P3 Character-only witness continuation where applicable
  -> P4 materialized runtime scope plan and completion evidence
  -> P5 CUTOVER_PENDING posture
  -> P6 native-core activation
  -> P7 selector activation
  -> NativeProductionResourceOwner root-v2 recovery
  -> NativeQualifiedQueryReadModel / NativePublicTormentRuntime
```

At P2, `root_p2_source_plan_recovery.py` explicitly says private scopes retain
`motif_domain_id=None`; Character witness-domain derivation is a separate P3
concern and is not folded into the generic source-plan projection. The
`RootSourceScopePlan` validation requires motif-domain facts only for the
shared postures. P3 did not alter the private `runtime_scope_plans`, and its
Character continuation is not a general private motif-domain authority.

The real P4 census corroborates this law rather than contradicting it:
`76 / 76` private runtime plans have `None`, including source-bearing
`ryuki/ryuki_nox` and `orchard/aria`. By contrast, shared plans legitimately
have an explicit domain because their scope identity is that domain.

Legacy private operations were also not bound to a static private domain:
they used the admitted shared domain selected for that operation. For example,
`ryuki` has `personal`, while `orchard` has multiple shared domains. A
private namespace can therefore hold motifs associated with multiple admitted
shared domains. The root P2 field cannot truthfully be backfilled from a
workspace name, agent, namespace, scope UUID, or a P3 Character witness.

The first fail-closed mismatch occurred in
`NativeQualifiedQueryReadModel._private_motif_domains`, which required a
nonempty string for every private plan. The value was then used to enumerate
and decorate motif memberships; `NativePublicTormentRuntime` reused the same
assumption for private ingest and private bridge geometry. It was not needed
to identify the private memory lane: that already has exact workspace, agent,
legacy-source namespace, semantic-scope, and identity bindings.

## 2. Repair boundary

The repair preserves two explicit modes:

- An older explicitly-bound private descriptor keeps its one fixed
  motif-domain behavior unchanged.
- A root P2 private descriptor with `None` keeps its qualified private scope
  and reads only motifs tagged with each admitted shared domain. Private
  public ingest either validates a supplied admitted shared domain or ranks
  the existing admitted shared geometry for that operation. The selected
  operation domain is then the private post-write motif/conflict domain.

`NativeMotifRuntimeReader.list_runtime_motifs` remains strict. It still
refuses a mixed-domain shared namespace. The new
`list_runtime_motifs_for_domain` is not a broad read: it verifies the exact
private alias namespace and semantic scope, then filters to the already
admitted shared domain. `NativePrivateBridgeGeometryAdapter` applies the
same distinction to centroids and post-write geometry. The runtime never
creates, persists, or derives a private `motif_domain_id`.

This is bounded to post-P7 runtime consumption. It leaves P1 source identity,
P2 propositions, P3 witnesses, P4 receipts, P5 posture, the P6 point of no
return, P7 selector ordering, and certified-refusal semantics unchanged.

## 3. Disposable P5–P7 behavior and test matrix

`test_post_i4_root_v2_production_recovery.py` creates a disposable root-v2
fixture with the real P2 shape: one private plan whose `motif_domain_id` is
`None` and one lawful shared plan. The fixture passes through P5
`CUTOVER_PENDING`, P6 core activation/disposition, and selector-last P7
activation before any native public operation. It then verifies private native
create, reinforcement, text/vector-backed query, shared write/query,
restart/recovery, and unchanged legacy private-node bytes. Every legacy
`MemoryGraph` reader/writer that would provide an authority fallback is
monkeypatched to fail, and no call occurs.

`test_7g5e4e_native_query_read_model.py` adds a mixed private namespace with
motifs for `research` and `engineering`. With a root-style `None`
descriptor, the private query sees exactly those admitted-domain memberships.
It refuses a cross-workspace lookup; a malformed private descriptor with no
`agent_id` refuses; and the original strict reader refuses the same mixed
namespace when asked to pretend it is a one-domain lane. A shared-lane query
continues to succeed with the strict reader.

The corrected full P0–P8 rehearsal remains an independent disposable
selector/transport proof. It reaches P7/P8, exercises REST, Spine, MCP,
native public ingest and restart/retry, forbids legacy `MemoryGraph` calls,
and retains the certified-refusal negative assertions. The earlier
real-P4-derived activated copy independently retained all 35 B2 historical
refusals and passed its 23 B4 target-alias/runtime-reader absence proof.
Thus the reconciliation did not weaken certified-refusal exclusion.

A direct owner-query probe against that large activated copy was intentionally
bounded and cancelled before it completed its full 76-scope recovery scan. It
is not counted as passing evidence. The passing root-v2 P5–P7 fixture is the
deterministic execution proof of the exact producer shape; the prior copy
remains supporting lifecycle and certified-refusal evidence only.

Character continuity is not applicable to the minimal root-v2 fixture because
it has no Character witness/seed. The repair does not consume or reinterpret
P3 Character authority, and existing Character continuations remain outside
this generic private-motif routing rule.

## 4. Adversarial review

Claude was explicitly requested, but this workspace has no Claude/Anthropic
connector or callable tool; the available-tool inventory was checked before
implementation. The substitute review was deliberately bounded and relied on
executable negative cases rather than claiming a Claude verdict:

- `None` is retained in the recovered descriptor and never replaced by a
  generated value.
- Missing private routing identity (`agent_id`) still refuses.
- Shared strict-domain validation still refuses a mixed-domain namespace.
- Cross-workspace private lookup refuses; shared lookup remains qualified.
- Native public create/reinforcement/query/restart execute while every legacy
  `MemoryGraph` search/write method is forbidden.
- The P0–P8 rehearsal and activated-copy B2/B4 proofs retain their
  certified-refusal non-leak guarantees.

The review found no reason to reopen P1–P4. The previous contradiction was
solely a post-P7 consumer overgeneralization expressed through the required
Model D split, not new predecessor semantic authority.

## 5. Validation commands

All Python and pytest commands ran through `conda activate torment`, with
bytecode disabled, the cache provider disabled, and disposable external pytest
bases:

```text
tests/test_7g5e4e_native_query_read_model.py
tests/test_post_i4_root_v2_production_recovery.py
11 passed in 9.98s

tests/test_b5_a3_production_native_resource_owner.py
tests/test_b5_a4r2_native_public_ingest_recovery.py
tests/test_b5_a4r3_public_backend_selection.py
tests/test_p9d_i4b1f_public_outcome_parity.py
55 passed in 66.51s

tests/test_b5_a5_offline_cutover_rehearsal.py
2 passed in 30.63s

git diff --check
PASS
```

No lifecycle call, plan mutation, selector mutation, core activation, or write
was applied to the real P4 root.
