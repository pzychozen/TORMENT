# 7G5E4D Proposal Orchestration Qualification

## Boundary

`TormentFabric.process_proposals` and `TormentFabric.decide_proposal` still
construct `LegacyAuthorizedSharedProposalStorage` directly.  Their public
return envelopes and authority paths remain legacy.  The native counterpart
is private (`_process_proposals_with_qualified_native_storage` and
`_decide_proposal_with_qualified_native_storage`) and requires a caller-made
`NativeAuthorizedSharedProposalStorage` containing all of:

- the already-qualified `NativeAuthorizedSharedProposalMaterializer`;
- an explicit `NativeMemoryVectorRuntime` for the claimed shared lane;
- qualified native motif geometry; and
- the M1/M2 `NativeMotifMaintenanceAdapter`.

There is no Fabric-native-core discovery, selector, activation, fallback,
dual-write, dual-read, or kernel change in this phase.

```text
PROCESS_PROPOSALS_PRODUCTION_BACKEND = LEGACY
DECIDE_PROPOSAL_PRODUCTION_BACKEND = LEGACY
NATIVE_ACTIVE = NO
```

The extracted storage port begins only after existing TORMENT authority has
selected the representative.  It exposes pre-conflict vector read,
quorum/operator publication, legacy-only deferred motif attachment, M1
maintenance, and read-only motif geometry.  It does not own proposal events,
conflicts, bridges, or domain suggestions.

## Frozen authority and process order

The shared implementation retains pending enumeration, first-anchor grouping,
used-set behavior, quorum, and representative selection unchanged.  A
`collective_echo` stays in a qualified group's content and
`source_proposal_ids`, but is excluded from support agents and cannot be the
representative.  Manual collective approval still fails before storage;
manual reject still marks rejected without a storage call.

The current `process_proposals` order is:

1. enumerate and group pending proposals;
2. decide genuine authority and representative;
3. read six existing canonical shared candidates;
4. publish the authorized shared memory;
5. record any ConflictRegistry result;
6. make motif truth current (legacy attachment here; native publication already
   owns attach/create/split and is therefore a no-op);
7. run M1 maintenance for a newly-created memory, including M2 when policy
   enables auto-merge;
8. mark every group proposal approved;
9. if a memory was created, refresh bridges at `0.86 / 10`;
10. run domain suggestion over injected neutral geometry; and
11. return the original envelope.

Manual approve is publication, motif-current, proposal mark, bridge refresh at
`0.86 / 5`, domain suggestion, then return.  It intentionally gains no
entropy/auto-merge callback.

`NativeMemoryVectorRuntime.search_by_embedding(..., top_k=6,
canon_only=True)` supplies the native pre-conflict read.  It is the existing
MemoryGraph-shaped qualified vector surface, not a new SQLite cosine query.

## Normal qualification results

Focused native qualification proves all of the following:

```text
LEGACY_PROPOSAL_ORCHESTRATION_REGRESSION = PASS
PROCESS_PROPOSALS_SHARED_WRITE_PARITY_DEFAULT_POLICY = PASS
PROCESS_PROPOSALS_SHARED_WRITE_PARITY_AUTO_MERGE = PASS
DECIDE_PROPOSAL_SHARED_WRITE_PARITY = PASS
QUORUM_AUTHORITY_LOGIC_CHANGED = NO
OPERATOR_AUTHORITY_LOGIC_CHANGED = NO
COLLECTIVE_CONTENT_AUTHORITY_SEPARATION = PRESERVED
PRE_CONFLICT_VECTOR_READ_PARITY = PASS
CONFLICT_BEHAVIOR_PARITY = PASS
MOTIF_MAINTENANCE_PARITY = PASS
MOTIF_AUTO_MERGE_PARITY = PASS
BRIDGE_REFRESH_TIMING_PARITY = PASS
DOMAIN_SUGGESTION_PARITY = PASS
PROCESS_PROPOSALS_SIDE_EFFECT_ORDER_PARITY = PASS
DECIDE_PROPOSAL_SIDE_EFFECT_ORDER_PARITY = PASS
SHADOW_LEGACY_MOTIF_STATE = NONE
```

The default-policy comparison uses two genuine agents plus a collective echo,
compares representative outcome, proposal status, conflict outcome, native and
legacy vector score/order, return shape, and the trace:

```text
AUTHORITY_DECIDED
PRE_CONFLICT_READ
STORAGE_COMMITTED
CONFLICT_SIDE_EFFECT
MOTIF_MAINTENANCE
PROPOSAL_MARK
BRIDGE_SUGGEST
DOMAIN_SUGGEST
RETURN
```

The auto-merge comparison seeds two genuinely native, merge-eligible motifs,
sets `auto_merge_motifs=True`, and exercises an actual M2 mutation.  The
legacy and native paths choose the same merge survivor and finish with matching
current centroid and strength.  Its trace additionally contains
`AUTO_MERGE_IF_ANY` between maintenance and proposal marking.

Operator approve traces:

```text
AUTHORITY_DECIDED
STORAGE_COMMITTED
PROPOSAL_MARK
BRIDGE_SUGGEST
DOMAIN_SUGGEST
RETURN
```

Reject and collective-echo manual approve issue zero storage calls.

## Ownership after extraction

| State | Owner and retry observation |
| --- | --- |
| shared memory, representation, motif attach/create/split | qualified native materializer; stable same-operation replay |
| proposal events | ProposalRegistry; append-only and observable duplicates on some retries |
| conflicts | ConflictRegistry; external and non-idempotent under replay |
| entropy / merge suggestions / merge decision workflow | M1 external workflow store; new suggestions are suppressed, entropy events repeat |
| native motif merge truth | M2 SQLite mutation; bounded idempotency remains intact |
| bridges | BridgeRegistry; repeated calls are observable but existing bridge topology is duplicate-tolerant |
| domain suggestions | Fabric JSON workflow; repeated calls suppress an existing `(domain_id, motif_id)` suggestion |

Native qualification never reads `ws.motif_regs` for motif truth.  The only
legacy/native difference in raw motif event streams is expected storage
ownership: legacy attachment logs its legacy attachment event, while native
attachment is structural native truth.  The subsequent external M1 workflow
events are compared directly.

```text
PROPOSAL_REGISTRY_REMAINS_EXTERNAL = YES
CONFLICT_REGISTRY_REMAINS_EXTERNAL = YES
BRIDGE_REGISTRY_REMAINS_EXTERNAL = YES
MOTIF_WORKFLOW_STORE_REMAINS_EXTERNAL = YES
KERNEL_FILES_CHANGED = 0
PRODUCTION_SELECTOR_ADDED = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```

## Retry characterization — intentionally not repaired

The following are injected *after* the named side effect and then retried by
a normal `process_proposals` call from durable state.  The matrix includes two
pre-existing canon nodes so repeated external conflicts are observable.

| Boundary | Natural retry result | Observable external result |
| --- | --- | --- |
| A. storage commit | group reconstructs; one native proposal memory | conflict, maintenance, and three marks complete once on retry |
| B. conflict | group reconstructs; memory remains one | ConflictRegistry receives the same conflict a second time |
| C. motif maintenance | group reconstructs; memory remains one | conflict duplicates; `MOTIF_ENTROPY` is appended twice while suggestions remain suppressed |
| D. first of group marks | **BLOCKED** | one proposal is approved; genuine-B plus echo remain pending and no longer meet quorum |
| E. all marks | **BLOCKED** | no pending group remains, so bridge and domain callbacks are never resumed |
| F. bridge refresh | **CHARACTERIZED** | bridge callback ran before failure; no pending group remains, so domain callback is never resumed |
| G. domain suggestion | **CHARACTERIZED** | all side effects completed before lost response; retry returns the ordinary no-pending envelope rather than the original created EID |

Same-authorized-group replay of a frozen quorum with the same native operation
key reconstructs the one committed native memory and adds no external effect.
That component result is `PASS`; it must not be confused with natural API
retry, which rereads ProposalRegistry state.

For operator approval, native memory remains one and the returned EID remains
continuous at every injected boundary.  The natural retry outcome is:

| Boundary | Proposal marks | Bridge calls | Domain calls |
| --- | ---: | ---: | ---: |
| storage commit → mark | 1 | 1 | 1 |
| mark → bridge | 2 | 1 | 1 |
| bridge → domain | 2 | 2 | 1 |
| domain → response | 2 | 2 | 2 |

This is current behavior, not a repair recommendation.  In particular,
`decide_proposal` has no existing already-approved fast path, so it appends a
second status event on post-mark retry while native storage reconstructs the
same memory.

### Cold restart result

The partial-mark case was repeated after closing Fabric, closing qualified
native reader/runtime objects, reopening Fabric from JSONL, reopening the
native core, and constructing fresh native readers.  Durable state remained
one approved / two pending.  The natural retry processed the two remaining
proposals, found only one genuine authority contributor, created no second
memory, and left them pending.

```text
PROCESS_PROPOSALS_PARTIAL_MARK_RETRY = BLOCKED
PROPOSAL_ORCHESTRATION_RETRY = BLOCKED
```

No orchestration journal, two-phase commit, event de-duplication rule,
already-approved branch, compensating delete, or bridge/domain repair was
added.  Plausible future repair classes require an explicit architecture
choice: durable group-decision/journal state, an atomic external workflow
protocol, or carefully scoped resumable callbacks.  This qualification stops
before selecting one.

## Verification

The cross-slice preflight run before extraction completed with **141 passed,
12 skipped**.  The post-extraction focused orchestration qualification covers
default and auto-merge parity, manual authority outcomes, side-effect traces,
process A–G, same-operation replay, operator A–D, and cold restart.  No
repository-global suite was attempted for this phase.
