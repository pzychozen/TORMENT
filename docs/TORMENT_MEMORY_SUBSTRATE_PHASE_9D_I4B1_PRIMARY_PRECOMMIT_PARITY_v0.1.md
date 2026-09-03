# TORMENT Memory Substrate — Phase 9D I4B-1

## Primary outcome and precommit truth parity

**Status:** corrected offline implementation slice; uncommitted freeze candidate
with external-owner and public-outcome precommit composition qualified.

**Scope:** the first native write's primary outcome, create/reinforce branch
truth, durable precommit residue, motif attachment, and process-local live
motif ordering. This is not a production-activation or component-retirement
decision.

```text
FUNCTIONALITY_DENOMINATOR_COUNT = 76
MAPPED_CAPABILITIES = 76
UNMAPPED_CAPABILITIES = 0
ONE_POST_WRITE_SEMANTIC_IMPLEMENTATION_FEASIBLE = YES
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Delivered boundary

`NativePrimaryPrecommitService` provides the smallest native lifecycle that
can honestly distinguish precommit intent from a canonical memory:

```text
reserve
  -> R1 PENDING LEGACY_CORE_NODE with scoped EID alias
  -> best-effort embed-audit observer
  -> persist motif attach/create
  -> canonical R2 EXISTS source commit
  -> publish representation / return route result
```

The pending reservation has no memory-runtime enumeration entry and no
representation. Compatibility, runtime enumeration, and vector candidate
selection accept only a current `EXISTS` source, so a reserved or aborted EID
cannot become a fake canonical memory.

The `EXISTS` successor keeps the established canonical operation identity:
`NATIVE_FABRIC_NEW_MEMORY:SOURCE:<route-key>`.  The I4B-1 reservation, motif,
and abort operations remain additional precommit evidence only; they are not a
second canonical source owner.

If canonical source commit fails after motif persistence, the reservation gets
an `ABORTED` successor. Its scoped EID alias remains allocated; the attached
motif membership remains durable. If attach/create itself fails before it
commits, the reservation is aborted and `NativePrecommitAttachFailure` exposes
the outcome witness; no motif is manufactured.

```text
FAILED_EID_NON_REUSE = RESTART_STABLE
LEGACY_CROSS_RESTART_ABORTED_EID_REUSE = DOCUMENTED_UNSAFE_RECOVERY_DIVERGENCE
NATIVE_MUST_REPRODUCE_REUSE = NO
CROSS_RESTART_EID_DIVERGENCE = DELIBERATELY_ACCEPTED_IDENTITY_SAFETY_REPAIR
```

The native allocator considers the durable aborted alias after core reopen, so
the next lawful native create receives a distinct monotonic EID. This is not
claimed as exact legacy parity: reconstruction from only legacy canonical nodes
can reuse a failed EID after restart. Native non-reuse intentionally preserves
the legacy abort intent's identity-safety invariant: durable failed residue
must never become ambiguous about which attempted memory it describes.

This deliberately uses the existing generic object lifecycle, motif service,
runtime-order primitive, and compatibility readers. It adds no schema table,
generic event framework, query owner, or post-write queue.

## Primary outcome witness

`NativePrimaryOutcomeWitness` records rather than decides storage behavior:

| Fact | Qualified values |
|---|---|
| Scope | `private`, `shared` |
| Attempt origin | `DIRECT_CREATE_PATH`, `INGEST_REINFORCEMENT_ATTEMPT` |
| Reinforcement disposition | `NOT_APPLICABLE`, `REINFORCED`, `SEMANTIC_FALLTHROUGH_TO_CREATE`, `EXCEPTION_FALLTHROUGH_TO_CREATE` |
| Final storage outcome | `CREATED_NEW`, `REINFORCED_EXISTING`, `NO_WRITE`, `REFUSED`; a pre-source refusal is recorded on the route attempt, never fabricated as a memory result |
| Create failure disposition | `NONE`, `PRECOMMIT_MOTIF_ATTACH_FAILURE_RAISED`, `CANONICAL_FLUSH_FAILURE_STRUCTURED` |
| Canonical state | explicit boolean plus EID/object/revision where available |

`qualified_memory_eid` remains for witness compatibility. On a failed CREATE
it means the **reserved / attempted EID**, not proof of canonical memory
existence.

Shared duplicate selection is not attempted, so the witness does not invent a
shared-reinforcement outcome. The explicit `fabric.reinforce(...)/Spine`
route remains its separate existing route; I4B-1 neither forces it through
ingest duplicate selection nor invokes the post-write adapter to make its
result look uniform.

## Commit asymmetry and reinforcement preservation

CREATE's native canonical boundary is the successful
`NATIVE_PRIMARY_CANONICAL_COMMIT` transition from `PENDING` to `EXISTS`, after
the precommit motif operation. It is the native semantic equivalent of the
legacy `flush_node` boundary; representation publication occurs afterwards
and does not make a pending reservation canonical.

REINFORCE remains `NativeMemoryReinforcementService`'s same-entity successor
write. It does not acquire create's pending/abort semantics. Existing
reinforcement math is unchanged: normal memories retain their asymptotic
strength update; tool-result sources increment the count and update refresh
time without the strength boost; timestamps remain owned by the existing
reinforcement patch.

The only structural addition is a narrow provenance rule: if a qualified
current source has no provenance child, the direct-ingest typed provenance
input is inserted with the R2 successor. A source with existing provenance is
preserved, and a missing provenance with no direct-ingest input still refuses
as before. This does not alter a formula or assign provenance ownership to the
witness.

## Precommit residue and motif truth

The public-ingest storage adapter opts into the protocol for the currently
claimed private native-public scope (`precommit_parity_required =
prepared.scope == "private"`) and retains Fabric's existing
`_mark_embed_audit_dirty` call as a best-effort observer after reservation and
before motif persistence. The native route does not replace the audit file's
external durable owner. Synthetic qualification proves the ordering and that
an observer result can survive a later canonical failure; it does not contact
a real workspace root.

A persisted orphan motif remains readable by the existing native motif reader:
its member count participates in the motif read model and its stored
prospective centroid participates in domain-centroid weighting. Its aborted
member has no usable embedding representation, so candidate retrieval and
canonical-memory enumeration remain empty. This is intentionally ugly,
durable precommit truth—not a compensating fake memory or a rollback.

```text
CANONICAL_MEMORY_FILTER_RULE =
    existence_state == EXISTS is required on paths that answer
    "is this a canonical memory?"

    It must not automatically be propagated to paths answering
    "what state does this semantic owner count?"
    unless that owner's existing semantics require canonical-member filtering.
```

The proof is intentionally split by owner: compatibility lookup, vector
candidate search, and current/post-write enumeration filter `ABORTED`; the
motif membership reader deliberately does **not** filter a member memory by
existence state. This preserves the orphan member-count and centroid effects
without manufacturing a queryable canonical memory.

The reader's canonical-memory joins are inner joins. Therefore an alias with
no current revision is excluded rather than projected with NULL state:

```text
LAWFUL_CANONICAL_MEMORY = UNAFFECTED
MISSING_CURRENT_REVISION = SUBSTRATE_INVARIANT_VIOLATION / MALFORMED_STATE
MALFORMED_STATE_DIAGNOSTIC = SILENT_EXCLUSION (BOUNDED_NON_BLOCKING_DEBT)
```

The remaining ordinary attach/create path has two semantically relevant
durability stages only: before a successful `NativeMotifService` mutation, and
after it but before the canonical source commit. The attach-failure fixture
proves no motif residue in the first stage; canonical-flush failure proves
durable motif residue in the second.

```text
I4B1_ATTACH_FAILURE_STAGE_MODEL = COMPLETE_TWO_STAGE
ADDITIVE_FAILURE_PROVENANCE = QUALIFIED_NATIVE_EVIDENCE
```

The additive abort record differs deliberately from legacy attach failure:
legacy raises and may leave no explicit abort record; native raises and records
an `ABORTED` failed-intent successor. It remains noncanonical and does not
change the caller's failure disposition.

`NativeMotifProcessOrder` is the explicit live-order witness:

```text
process initialization: lexical current runtime motif IDs
locally created later motif: append in creation order
restart: lexical recovery baseline again
```

No runtime-ID sort is performed after live insertion and no new tie rule was
introduced.

## True-split fence, external owners, and exclusions

The precommit route can reach a true-split preview. I4B-1 now refuses it
before EID reservation or motif mutation; the established non-precommit route
continues to use its unchanged atomic split path.

```text
TRUE_SPLIT_I4B1_REACHABILITY = YES
TRUE_SPLIT_NATIVE_DISPOSITION = REFUSED_PENDING_I4B2
TRUE_SPLIT_ACTIVATION_GATE = OPEN
```

This is an I4B-2 topology qualification, not a split redesign.

External ownership has been re-traced and composed without a SQLite migration
or a cross-owner transaction.

| Owner | Trigger and owner | Scope / branch | Failure disposition and residue |
|---|---|---|---|
| Role | After kernel summary and before the write decision, `RoleStore.load → update_from_text → save` | private and shared; CREATE, REINFORCE, and NO_WRITE | failures are debug-log fail-soft; durable `roles.json` remains after later primary failure and reload |
| Affect | `classify_affect(summary)` before the write decision | private and shared; CREATE, REINFORCE, and NO_WRITE | classifier failure is silent fail-soft (`completed=False`); classification is an ephemeral/prepared fact. `affect_state.json` belongs to post-write mood-drift continuity and is not a precommit effect |
| Symbol state | After durable motif attach/create and before flush/primary commit, Fabric's retained symbol-state writer saves `symbol_state.json` | CREATE only; current claimed private native-public precommit scope | writer failure is debug-log fail-soft; successful side state remains after later primary failure and reload |
| Resonance enrichment | Same symbolic projection, returned to the primary payload | CREATE only; current claimed private native-public precommit scope | it becomes durable only with canonical commit; failed primary memory has no canonical resonance payload |

Native preparation now invokes the existing RoleStore owner even when
`_native_public=True`. Affect already followed source behavior in preparation;
this pass records that its external historical state is post-write mood-drift,
not a synthetic precommit write. Native routing calls Fabric's retained symbol
side-state writer only after motif persistence and before canonical commit.
The writer receives native projection facts but neither owns nor changes the
symbol/resonance mathematics.

```text
EXACT_PRECOMMIT_CAUSAL_ORDER =
  role / affect classification
  -> reserve
  -> embed-audit dirty
  -> motif attach/create
  -> symbol side-state + resonance enrichment
  -> canonical commit

ROLE_PRECOMMIT_PARITY = PASS
AFFECT_PRECOMMIT_PARITY = PASS
SYMBOL_STATE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
RESONANCE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
PRECOMMIT_EXTERNAL_OWNER_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
EXTERNAL_OWNER_MIGRATION_TO_SQLITE = NO
EXTERNAL_OWNER_FAILURE_DISPOSITION_PARITY = PASS
EXTERNAL_OWNER_RESIDUE_AFTER_PRIMARY_FAILURE = PASS
EXTERNAL_OWNER_NO_WRITE_PARITY = PASS
EXTERNAL_OWNER_REINFORCEMENT_PARITY = PASS
```

Legacy replay is not normalized: ordinary role preparation can reapply its EMA
on a retry; affect classification can rerun; symbol-state write occurs only on
the spawned CREATE branch. Native public receipts retain their existing
recovery fence and do not add an outbox or exactly-once promise.

## Native-public outcome boundary

The public adapter derives post-write eligibility from the source branch, not
from the generic `stored` boolean or its response disposition.

| Source branch | Primary truth / public boundary | External precommit state | Post-write disposition |
|---|---|---|---|
| Ordinary write-gate `NO_WRITE` | truthful non-stored result, no native source operation | Role and affect classification have already run; symbol/resonance have not | reaches the existing qualified post-write boundary with no fabricated route witness |
| Precommit motif attach failure | `NativePrecommitAttachFailure` is raised; reservation becomes `ABORTED` | Role and affect classification may already have run; no symbol owner call because motif did not persist | short-circuit; no adapter/tail |
| Canonical CREATE commit failure | `{stored: false, reinforced: false, failure_code: canonical_commit_failed, eid: null}`; reservation becomes `ABORTED` | Role and affect classification, embed audit, motif state, and successful symbol state may remain | short-circuit before the storage/post-write adapter; no route witness |
| Route/public refusal | an explicit refusal/error before a qualifying stored route result | only effects reached before the refusal are retained; no canonical source is invented | no post-write adapter/tail |

Successful REINFORCE retains RoleStore and affect-classification preparation but
does not invoke CREATE-only motif, symbol, or resonance ownership. Semantic and
uncommitted-exception duplicate fallthroughs remain CREATE branches and do
invoke those CREATE-only effects.

The public storage adapter's ordinary `allow_write=False` branch returns the
truthful `NO_WRITE` disposition instead of surfacing it as `CREATED_NEW`:

```text
PUBLIC_NATIVE_NO_WRITE_REPORTING_DEFECT_FIXED = YES
LEGACY/NATIVE_PUBLIC_OBSERVABLE_BEHAVIOR_CHANGED = YES
```

This is a deliberate observable defect repair, not a query or reinforcement
formula change.

No implementation or formula change was made for conflict, Character drift /
gravity / reflex, SRG collision or coverage expansion, world, checkpoint,
compression/deep, proposals, bridges, Hivemind/collective, archive, shared
proposal processing, or any post-commit cognitive tail.

```text
CHARACTER_GRAVITY_NESTED_WRITE_RECURSION = LEGACY_INVARIANT_MAPPED
GRAVITY_ORPHAN_POLICY_PARITY = NOT_YET_QUALIFIED_I4D
OWNER = I4D
```

I4B-1 did not exercise gravity nested-write parity. The mapped legacy
invariant is that gravity's nested write does not call `Fabric.ingest` and does
not re-enter the full post-write adapter.

## Offline qualification

All tests used temporary native SQLite cores, a synthetic lane, a writable
pytest base outside the repository, and the `torment` Conda environment.

| Evidence | Result |
|---|---|
| `tests/test_p9d_i4b1_primary_precommit_parity.py` | 10 passed (I4B1E focused) |
| `tests/test_p9d_i4b1_external_precommit_owner_parity.py` | 3 passed |
| `tests/test_p9d_i4b1f_public_outcome_parity.py` | 5 passed: full executor CREATE/REINFORCE/NO_WRITE/failure, source-owner, fallthrough, and restart fixtures |
| I4B-1/I4B1C/I4B1E/I4B1F + native-public/recovery/post-write routing + native reinforcement + I3C/I3B/I3B0/I2 + motif composition + role/affect regressions | 336 passed |

The I4B-1 cases cover private/shared create witnesses, successful duplicate
reinforcement, deliberate semantic and exception fallthrough to CREATE,
tool-result formula preservation, direct-ingest provenance backfill, attach
failure before motif persistence, canonical failure after motif persistence,
non-queryable aborted memory, deterministic abort recovery, orphan motif
member/centroid effect, in-process and restart-stable EID non-reuse,
restart-time canonical isolation, a durable synthetic embed-audit residue,
true-split refusal before a source mutation, and live motif insertion/restart
order. I4B1E adds native-public preparation/storage fixtures for role create,
reinforcement, canonical-failure residue, affect classifier failure, NO_WRITE,
and symbol owner failure. They use a temporary synthetic root only; they do
not authorize a real root or post-write-tail migration. I4B1F additionally
crosses the existing native-public executor and post-write boundary only to
prove that the repaired operation witness is internally coherent; it adds no
post-write consumer, formula, or policy.

`netstat` found no listener on port 8787 before tests. No real root, service,
or provider was contacted or started.

## Verdicts and continuing gates

```text
P9D_I4B1_PRIMARY_PRECOMMIT_PARITY = PASS (bounded offline precommit scope)
PRIMARY_OUTCOME_WITNESS = PASSIVE
CANONICAL_OPERATION_OWNER = EXISTING_NATIVE_FABRIC_NEW_MEMORY_SOURCE_OPERATION
I4B1_CANONICAL_OPERATION_OWNERSHIP = NO
CANONICAL_OPERATION_OWNERSHIP = PRESERVED
PUBLIC_INGEST_OPERATION_KEY_MISMATCH = FIXED
PUBLIC_INGEST_REGRESSION_FROM_I4B1E = CLOSED
PRIVATE_CREATE_OUTCOME = PASS
SHARED_CREATE_OUTCOME = PASS
INGEST_REINFORCEMENT_OUTCOME = PASS
REINFORCEMENT_SEMANTIC_FALLTHROUGH = PASS
REINFORCEMENT_EXCEPTION_FALLTHROUGH = PASS
CREATE_COMMIT_BOUNDARY = PASS
REINFORCE_COMMIT_BOUNDARY = PASS
EMBED_AUDIT_DIRTY_PARITY = PASS_TESTED_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE (synthetic external observer residue)
MOTIF_ATTACH_CREATE_PARITY = PASS
MOTIF_LIVE_ORDER_WITNESS = QUALIFIED
ORPHAN_MOTIF_POLICY = QUALIFIED
ORPHAN_MOTIF_COGNITIVE_EFFECT = PASS
FAILED_EID_NON_REUSE_IN_PROCESS = PASS
FAILED_EID_NON_REUSE_AFTER_RESTART = PASS
FAILED_MEMORY_RESTART_CANONICAL_ISOLATION = PASS
CANONICAL_MEMORY_FILTER_RULE = FROZEN
TRUE_SPLIT_I4B1_REACHABILITY = YES
TRUE_SPLIT_NATIVE_DISPOSITION = REFUSED_PENDING_I4B2
I4B1_ATTACH_FAILURE_STAGE_MODEL = COMPLETE_TWO_STAGE
ROLE_PRECOMMIT_PARITY = PASS
AFFECT_PRECOMMIT_PARITY = PASS
SYMBOL_STATE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
RESONANCE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
PRECOMMIT_EXTERNAL_OWNER_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
I4B1_PRECOMMIT_EXTERNAL_OWNER_SCOPE = PRIVATE_QUALIFIED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
I4C_SHARED_SCOPE_PREREQUISITE = DO_NOT_INFER_SHARED_PRECOMMIT_PARITY_FROM_PRIVATE_I4B1_RECEIPTS
PUBLIC_NATIVE_NO_WRITE_REPORTING_DEFECT_FIXED = YES
CANONICAL_FAILURE_POSTWRITE_DISPOSITION = SHORT_CIRCUIT
ORDINARY_NO_WRITE_DISPOSITION = QUALIFIED_BOUNDED
EXTERNAL_OWNER_NO_WRITE_PARITY = PASS
EXTERNAL_OWNER_REINFORCEMENT_PARITY = PASS
EXTERNAL_OWNER_RESTART_PARITY = PASS (RoleStore/symbol-state residue; affect state has no precommit durable mutation)
FAKE_CANONICAL_FAILED_MEMORY = NO
CHARACTER_GRAVITY_NESTED_WRITE_RECURSION = LEGACY_INVARIANT_MAPPED
GRAVITY_ORPHAN_POLICY_PARITY = NOT_YET_QUALIFIED_I4D
POST_WRITE_TAIL_MIGRATED = NO
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
I4B1_READY_TO_FREEZE = YES (bounded artifact; final narrow review still required)
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

I4B-2 must qualify the refused true-split topology and later motif maintenance;
it does not own the now-qualified ordinary precommit external owners. I4C
remains the system/activation programme:
selected-profile and real-root authorization, service-route composition,
owner-specific recovery, and retirement gates are still open.
