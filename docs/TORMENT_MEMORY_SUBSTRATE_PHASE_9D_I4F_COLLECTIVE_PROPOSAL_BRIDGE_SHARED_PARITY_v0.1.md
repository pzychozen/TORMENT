# TORMENT Memory Substrate — Phase 9D I4F

## Collective, proposal, bridge, and shared-composition parity

**Status:** I4F-A is frozen. I4F-B has passed its required documentation
correction and freezes the bounded non-true-split shared precommit/composition
artifact. It does not authorize activation, real-root use, a service/provider
contact, a SQLite shadow store, compression/deep-memory work, or retirement of
a legacy owner.

**Base:** `53cbf06ac5235fb578bc5741c889eb2734591141` (`qualify-phase-9d-i4e-srg-world-trajectory-checkpoint-parity`).

**I4F-B starting HEAD:** `0e417a592cfa84181b71ceee1cf379b1119b145b`
(`qualify-phase-9d-i4f-a-private-collective-proposal-bridge-parity`).

```text
I4F_IMPLEMENTATION_SHAPE = SPLIT_SUBSLICES_REQUIRED
I4F_A = IMPLEMENTED
    ordinary broad-private native-public conflict correction + proposal + bridge continuation
I4F_A_DELTA_REVIEW = PASS_AFTER_REQUIRED_SCOPE_CORRECTION
I4F_A_READY_TO_FREEZE = YES
I4F_B = FROZEN
    bounded shared external-owner restoration + shared native-public composition

SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION = PASS
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = NO_LONGER_OPEN
SHARED_I4B2_TWO_STAGE_PARITY = NOT_CLAIMED
SHARED_NATIVE_PUBLIC_PARITY = PASS_BOUNDED_NON_TRUE_SPLIT_SCOPE
PREEXISTING_QUALIFIED_HIVEMIND = FROZEN_PRESERVED
NEW_HIVEMIND_OWNER = NO
SQLITE_SHADOW_PACKET_STORE = NO
EXACTLY_ONCE_CLAIM = NO
COMPRESSION_DEEP_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Shape decision and implementation boundary

At I4F-A, shared restoration remained deliberately deferred: the native public
executor selected I4B precommit parity only for private requests, while shared
used the established I3 composition/recovery path. I4F-B replaces that coupling
with a bounded capability split; its exact current disposition is recorded
below. I4F-A's frozen private statements remain historical truth.

I4F-A restores only the ordinary, non-true-split private tail:

```text
canonical successful private storage
  CREATED_NEW only:
    conflict -> SRG -> existing Hivemind -> motif/anchors/mood
  all successful dispositions:
    world -> Character -> checkpoint -> [compression deferred]
    -> general proposal -> bridge suggestion
```

`NativePrivatePostWriteExternalWorkspace` is a narrow binding with existing
`ConflictRegistry`, `ProposalRegistry`, `BridgeRegistry`, and policy facts
only. It exposes no legacy graph, motif registry, router, or shared writer.
Its conflict mapping opens only the current admitted private domain's retained
JSONL writer; it does not grant a shared conflict writer. The proposal map
memoizes one existing registry object per admitted domain in a post-write
configuration, so the convergence and general-proposal paths see the same
owner without introducing request-level dedupe. The proposal registry is
resolved only after the legacy proposal gates pass; the bridge registry is
opened only when the retained random gate passes. No owner is moved to SQLite.

The private source uses the dedicated
`NativePrivateBridgeGeometryAdapter`, not the generic shared-only
`NativeMotifGeometryAdapter`. It reads the exact legacy domain sequence from
`workspaces/<workspace>/domains.json` and exposes the complete ordered
private-plus-admitted-shared geometry. The private motif is read through the
prepared private scope and every other declared domain through its admitted
shared scope. It refuses rather than repairs a missing, malformed, duplicate,
or coverage-mismatched declaration. The generic shared adapter remains
unchanged. Private proposal domains include the shared domains and separately
admitted private motif domains, so a private `chosen_domain` such as
`personal` reaches its existing proposal owner.

The frozen I4B-2 true-split tail remains `conflict -> SRG -> M1/anchor prefix -> mood -> world/trajectory -> Character -> checkpoint -> STOP`. It still excludes Hivemind, compression, proposal, and bridge work; reinforcement and ordinary no-write perform no true-split tail work.

## Hivemind, packet, and convergence archaeology

`LegacyFabricPostWriteAdapter._run_hivemind` is the sole retained
packet/convergence call in the ordinary broad-private `CREATED_NEW` position.
I4F-A does not call it directly or create another collective owner.

Its exact outer gate is:

```text
owner._hivemind_enable
and context.stored
and context.eid is not None
and not context.skip_packet_emission
```

It reads the current post-write memory. `governance.non_shareable`, `governance.collective_export_blocked`, and collective-echo provenance block emission; a governance-read failure is handled by the existing logging boundary. The remaining gate is `coherence >= 0.15`. No I4F code widens these conditions.

The retained `ResonancePacket` has its existing random packet ID and complete existing field set: workspace, agent, domain, source EID, summary, MD5-derived 12-character embedding hash, cycle/identity state, coherence and stability, corridor/phase durations, motifs and created motif, state symbol, resonance/loop facts, Character drift facts, and SRG band/heartbeat/crystal facts. Existing blocked/skipped/emitted/error telemetry remains unchanged. The outer Hivemind error boundary is fail-soft.

`CollectiveField` preserves external truth at:

```text
workspaces/<workspace>/collective/packets.jsonl
workspaces/<workspace>/collective/events.jsonl
```

`append_packet` appends the packet, updates its bounded process cache, then detects convergence only when an embedding is supplied. It has no operation key or dedupe. Re-entering post-write after a packet append produces a second packet with a new ID; the I4F direct re-entry test demonstrates that existing behavior.

Convergence compares only cached embeddings from a different agent in the same domain. It chooses the strict-best cosine at or above `0.72`, applies its 30-second per-agent-pair/domain process-local cooldown, and requires confidence at least `0.45` using the unchanged formula:

```text
0.50 * semantic_similarity
+ 0.15 * phase_alignment
+ 0.15 * symbol_alignment
+ 0.20 * motif_alignment
```

The new random-ID event is appended before the cooldown changes. On restart, the last 200 packet records warm the packet cache but full embeddings are neither persisted nor rebuilt into the embedding cache; cooldowns also reset. Stored history remains readable but cannot become a cross-restart embedding candidate until new in-process packets arrive. `CONVERGENCE_TIME_WINDOW` and `CONVERGENCE_MIN_AGENTS` are declared constants, not additional gates in this implementation.

```text
HIVEMIND_EXISTING_PARITY = FROZEN_PRESERVED
HIVEMIND_REPLAY_MODEL = APPEND_ONLY_NO_PACKET_DEDUPE
COLLECTIVE_OWNER_PARITY = QUALIFIED_EXTERNAL_OWNER_PRESERVED
CONVERGENCE_FORMULA_AND_OWNER = FROZEN_PRESERVED
```

## Collective proposal side effect versus general proposal

On a convergence event, the existing Hivemind code calls
`_get_proposal_bridge(...).maybe_draft_proposal(...)` inside its independent
fail-soft boundary. Before I4F-A, the private external workspace did not
expose the required `proposals` property, so this retained collective effect
was inert on the native-public route. I4F-A restores its legacy-effective
behavior by supplying the same retained proposal owner map; it does not add a
second Hivemind call or a new collective writer. This is distinct from general
proposal parity and never produces the public `proposal_id`.

`CollectiveProposalBridge` preserves its separate external tracker at `workspaces/<workspace>/collective/convergence_patterns.jsonl`. It always records the pattern first, then retains its `0.70` confidence, two-event/7200-second persistence, event-ID, 1800-second domain cooldown, and five-pending-proposal gates. Pending-list errors are fail-open. Its drafting branch may attempt a normal proposal submit, yet records the event as proposed even with no registry/embedding or a failed submit. The enclosing Hivemind call suppresses bridge exceptions.

## General proposal parity — I4F-A

The unchanged general proposal gate is:

```text
context.stored
and context.scope == "private"
and identity.seed["coupling_mode"] in {"propose", "sync"}
and context.half_life_days is not None
```

It calls unchanged `_proposal_allowed` with identity, policy, `created_motif`, promotion score, strength, confidence, and `tri_mod`. Rate-window/min-gap, novelty, threshold, coupling-mode, and clipped `proposal_mult` behavior are unchanged.

The existing `ProposalRegistry` appends to
`workspaces/<workspace>/domains/<domain>/proposals.jsonl`; the existing
identity store is saved afterward. A convergence draft and the later general
proposal can therefore append separate records through the same memoized
external owner. The latter returned ID remains
`FabricPostWriteOutcome.proposal_id`, which the native public executor includes
in its public result. A collective-draft failure remains contained by its
Hivemind boundary and cannot suppress the independent general proposal.

The proposal sibling audit finds no conflicting configuration execution flag:
the private tail always reaches the existing general proposal slot, while
pre-effect validation requires `profile.proposal` to be qualified. Its existing
proposal gate remains the only decision gate.

| Case | Existing disposition retained |
|---|---|
| Gate miss / absent registry | `None`, no append. |
| Policy failure | Propagates. |
| Registry submit failure | Propagates; earlier post-write state remains. |
| Identity-save failure after append | Propagates after the durable external proposal; no compensation/outbox. |
| Direct tail re-entry | No global dedupe; an eligible re-entry can append another UUID proposal and return a new ID. |
| Completed public receipt replay | Returns the completed receipt without rerunning post-write. |

```text
PROPOSAL_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
PROPOSAL_REPLAY_MODEL = RETAINED_BOUNDED_NO_GLOBAL_DEDUPE
PROPOSAL_PROFILE_AUTHORITY = PASS
I4F_A_N1_PROPOSAL_REGISTRY_MEMOIZATION = CORRECTED
PROPOSAL_FORMULA_CHANGES = 0
PROPOSAL_THRESHOLD_CHANGES = 0
```

## Bridge parity — I4F-A

I4F calls the existing `_run_bridges` after the existing general proposal call. The exact unchanged decision is:

```text
tear        = tri_mod["tearing_risk"] default 0.0
probability = clip(tri_mod["bridge_p"] default 0.08 * (1 - 0.40 * tear), 0.02, 0.12)
threshold   = clip(tri_mod["bridge_sim"] default 0.86 + 0.03 * tear, 0.84, 0.92)

if context.stored and random_chance(probability):
    workspace.bridges.suggest(native_multi_domain_geometry,
                              sim_threshold=threshold,
                              max_new=5)
```

The existing `BridgeRegistry` remains the external owner of
`workspaces/<workspace>/bridges.json` and `bridge_events.jsonl`. It retains
the complete authoritative geometry order, cosine rule, bidirectional duplicate
detection, save-before-event ordering, and the exact `max_new=5` argument. Its
historical outer-pair traversal applies that cap as implemented; I4F-A does
not reinterpret it as a new global cap law. No native motif truth is added.

Random-gate, geometry read, registry load/save, and suggestion failures remain propagating failures. The I4F public regression forces a bridge-owner failure and proves the preceding external proposal row remains while the caller receives that error.

```text
BRIDGE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
BRIDGE_FAILURE_DISPOSITION = PROPAGATES_AFTER_EARLIER_POSTWRITE_STATE
BRIDGE_FORMULA_CHANGES = 0
BRIDGE_PROBABILITY_CHANGES = 0
```

## Compression dependency

Compression remains deferred and the qualified private profile still refuses an enabled compression posture before effects. Legacy compression mutates legacy private-graph payload/deep artifacts. General proposal consumes frozen context plus identity/policy/registry; bridge suggestion consumes `tri_mod`, random chance, and qualified native motif geometry. Neither consumes a compression event or compressed graph payload.

```text
COMPRESSION_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4F
I4F_BLOCKED_ON_COMPRESSION_ORDER = NO
```

## I4F-A shared inventory baseline and non-claim (historical — superseded by I4F-B)

| Shared behavior | Existing status | I4F result |
|---|---|---|
| B1 bridge suggestion | Frozen standalone primitive | Preserved; not selected by the I4F-A public shared configuration. |
| D1 M1 + private-target mood | I4F-A public shared configuration | Narrow/partial, not full system parity. |
| D2 Hivemind | Frozen standalone primitive | Preserved; not selected by the I4F-A public shared configuration. |
| D3 trajectory / D4 checkpoint / D6 compression no-op | Frozen standalone primitives | Preserved; not selected by the I4F-A public shared configuration. |
| E1 integrated default | Explicit separately prepared profile | Not an I4F-A shared public route claim. |

At I4F-A, the public shared configuration was D1-only. It did not use I4F's
private proposal/bridge bindings and did not compose B1/D2/D3/D4/D6/E1 as a
system. The following are historical I4F-A receipts only; I4F-B's current
shared receipts supersede them below.

```text
I4F_A_SHARED_PRECOMMIT_OWNER_PARITY = NOT_ATTEMPTED_PENDING_I4F_B
I4F_A_SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION = REQUIRED
I4F_A_SHARED_TRUE_SPLIT_DISPOSITION = NOT_CLAIMED
I4F_A_SHARED_POSTWRITE_PARITY = EXISTING_PRIMITIVES_ONLY_NOT_SYSTEM_LEVEL
I4F_A_SHARED_NATIVE_PUBLIC_PARITY = NOT_YET_QUALIFIED
```

## Formula audit and bounded verdict

Focused and frozen-regression evidence was executed under `conda activate torment`
using fresh external pytest bases. Port 8787 had no listener before each run:

```text
tests/test_p9d_i4b1f_public_outcome_parity.py -k i4f
7 passed

tests/test_substrate_native_post_write_runtime.py
36 passed

tests/test_p9d_i4b1f_public_outcome_parity.py
14 passed

tests/test_conflict_origin_scope.py tests/test_p9d_i3b_query_read_parity.py
22 passed

tests/test_p9d_i4d_character_derived_parity.py tests/test_substrate_native_shared_trajectory_evidence.py
tests/test_a3d8_world_runtime_port.py tests/test_srg_ordered_transient_runtime.py
tests/test_substrate_fabric_native_routing.py
49 passed

tests/test_substrate_native_shared_bridge_post_write.py tests/test_collective_field.py
tests/test_hivemind_structured_telemetry.py tests/test_substrate_legacy_proposal_admission.py
tests/test_bridges_path_hardening.py
54 passed
```

The focused public set includes the I4F-A B1 geometry/order/dedupe fixture,
M1 broad-private external-owner/write-side/failure/replay fixtures, M2
profile/configuration refusal fixture, N1 memoization assertion, restored
convergence-proposal same-cycle/failure-independence fixture, and true-split
bridge exclusion. The writer fixture does not claim a broad-private native
query-reader roundtrip; I4C-R1 owns that separate prerequisite. The larger
sets retain collective, shared B1/D1/D2/D3/D4/D6/E1, I4E, I4D, I4C, I4B,
query-read, and public-recovery assertions.

```text
HIVEMIND_FORMULA_CHANGES = 0
HIVEMIND_THRESHOLD_CHANGES = 0
CONVERGENCE_FORMULA_CHANGES = 0
PROPOSAL_FORMULA_CHANGES = 0
PROPOSAL_THRESHOLD_CHANGES = 0
BRIDGE_FORMULA_CHANGES = 0
BRIDGE_PROBABILITY_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES

I4C_TRUE_SPLIT_CONFLICT_PARITY = FROZEN_PRESERVED
I4C_BROAD_PRIVATE_CONFLICT_WRITER = PASS_WRITE_SIDE_ONLY
I4C_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = NOT_YET_QUALIFIED
I4C_BROAD_PRIVATE_CONFLICT_SYSTEM_PARITY = NOT_YET_QUALIFIED
I4C_R1_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = OPEN
I4C_R1_REQUIRED_BEFORE_I4G_FINAL_FREEZE = YES
CONFLICT_EXTERNAL_OWNER = PRESERVED_EXTERNAL_CONFLICT_REGISTRY
BRIDGE_GEOMETRY_DOMAIN_SET = LEGACY_EQUIVALENT
BRIDGE_GEOMETRY_DOMAIN_ORDER = LEGACY_EQUIVALENT
BRIDGE_PROFILE_AUTHORITY = QUALIFICATION_PROFILE
HIVEMIND_CONVERGENCE_PROPOSAL_SIDE_EFFECT = RESTORED_TO_LEGACY_EFFECTIVE_BEHAVIOR
P9D_I4F_A_PRIVATE_COLLECTIVE_PROPOSAL_BRIDGE_PARITY = PASS_BOUNDED_PRIVATE_NATIVE_PUBLIC_SCOPE
I4F_B = FROZEN
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## I4F-B — shared precommit restoration and bounded public composition

### Archaeology and capability separation

Legacy shared ingest prepares provenance, Role, and Affect before storage. A
writable shared request has no legacy duplicate/reinforcement branch: the
legacy duplicate search is private-only. Its shared CREATE order is therefore:

```text
shared input/provenance admission
  -> Role preparation -> Affect preparation
  -> source spawn/EID -> embed-audit dirty observer
  -> shared-domain motif attach/create
  -> existing symbol-state + resonance owner
  -> canonical flush
  -> shared post-write dispatch -> public result
```

The prior native public shared route used atomic I3 composition. It skipped the
precommit reservation, retained embed-audit observer, precommit motif mutation,
and symbol/resonance owner sequence; its public configuration selected only D1
M1/private-target mood drift. The private-only `precommit_parity_required`
boolean incorrectly coupled that missing owner sequence to I4B-2 true-split
authority.

`NativeFabricRouteRequest` now separates those facts:

```text
precommit_parity_required = run the I4B-1 external-owner sequence
precommit_true_split_authorized = permit I4B-2 Stage A/B topology

PRECOMMIT_OWNER_PARITY_AUTHORITY != TRUE_SPLIT_AUTHORITY

private public = parity qualified / true split qualified (frozen I4B-2)
shared public  = parity qualified / true split fenced
```

The second flag requires the first. These are explicit route capabilities: the
two scope rows describe the qualified public-route selections, not a router
inference that scope itself grants true-split authority. The split does not add
a schema, a global feature framework, or a new owner. Existing direct I3
callers that do not select precommit parity remain outside this public
qualification claim.

For shared precommit routes without true-split authority, the existing pure
`prepare_plan_from_ordered_catalog` preview runs while holding the existing
catalog lock and **before** `NativePrimaryPrecommitService.reserve`. A planned
split returns the exact public result:

```json
{
  "stored": false,
  "reinforced": false,
  "failure_code": "shared_true_split_refused",
  "eid": null,
  "domain_chosen": "<admitted shared domain>"
}
```

No reservation, EID alias consumption, spawn observer, dirty marker, motif
member attach, Stage-A attach, Stage-B topology, split child, symbol/resonance
owner, canonical primary, representation, or shared post-write tail runs. The
public mutation receipt and ordinary pre-storage Role preparation retain their
already-qualified public-envelope behavior: receipt operation rows are lawful,
and Role state may precede the fence by design. The refused operation has no
native precommit storage or topology residue. A completed refusal receipt
returns the same result on replay/restart. This is not a shared I4B-2 claim.

Recovery also reads any pre-existing Stage-A or Stage-B witness before normal
primary recovery. A route without true-split authority refuses that witness
rather than silently presenting private I4B-2 topology as ordinary shared
state. The fence does not delete or rewrite hypothetical witness evidence; it
refuses to treat it as an authorized shared result. Private Stage-A/Stage-B
recovery is frozen and preserved.

```text
SHARED_TRUE_SPLIT_FENCE_TIMING = PURE_PREVIEW_BEFORE_RESERVATION
SHARED_TRUE_SPLIT_PRECOMMIT_STORAGE_RESIDUE = NONE
SHARED_TRUE_SPLIT_EID_CONSUMPTION = NONE
SHARED_TRUE_SPLIT_REFUSAL_RESIDUE = PUBLIC_MUTATION_RECEIPT_ONLY
PUBLIC_MUTATION_RECEIPT = PRESENT_LAWFUL
PREPARATION_ROLE_STATE = MAY_PRECEDE_FENCE_LAWFUL
SHARED_STAGE_A_RECOVERY = STRUCTURALLY_REFUSED
SHARED_STAGE_B_RECOVERY = STRUCTURALLY_REFUSED
PRIVATE_STAGE_A_STAGE_B_RECOVERY = FROZEN_PRESERVED
SHARED_TRUE_SPLIT_DISPOSITION = STRUCTURALLY_FENCED
SHARED_I4B2_TWO_STAGE_PARITY = NOT_CLAIMED
```

### Shared owner map, gates, and failures

The current bounded shared route is:

```text
shared preparation
  -> restored precommit-owner sequence
  -> ordinary shared storage
  -> canonical commit
  -> existing qualified E1 shared post-write composition
```

| Stage | Owner / durability | CREATE | NO_WRITE | Failure and replay disposition |
|---|---|---:|---:|---|
| Role / Affect | Existing Fabric side-state preparation | Yes | Yes | Existing fail-soft preparation semantics; prepared receipt binds a recoverable public operation. |
| Reservation/source | Existing `NativePrimaryPrecommitService` | Yes | No | Durable noncanonical primary; retry/recovery uses its existing operation keys. |
| Spawn observer / audit | Existing `_mark_embed_audit_dirty` callback | Yes, after reservation | No | Best effort; failure is swallowed and does not block motif work. |
| Motif precommit | Existing shared scoped native motif owner | Yes | No | Attach/create failure aborts the primary and remains caller-visible through the existing precommit failure path. |
| Symbol / resonance | Existing Fabric symbol-state owner | Yes, after motif | No | Fail-soft: no enrichment patch when persistence fails; canonical commit continues. |
| Canonical source | Existing precommit canonical commit | Yes | No | Failure records `CANONICAL_FLUSH_FAILURE`, returns `canonical_commit_failed`, and suppresses post-write while retaining lawful precommit residue. |
| E1 post-write | Existing qualified shared integrated dispatcher | After canonical | Yes | Its existing per-owner boundaries remain intact; bridge failures still propagate after earlier effects. |

Shared reinforcement remains `NOT_APPLICABLE`: legacy has an explicit
private-scope duplicate gate, while the native non-reinforcement result
currently depends on shared rows using `agent_id = None` and the native lookup
filtering by the request's agent ID. I4F-B does not invent a shared formula or
recast repeated shared input as a private reinforcement. This representation
dependency is a future I4G scope-guard review item. Ordinary shared NO_WRITE
creates no route request and therefore cannot invoke precommit planning or any
CREATE-only consumer; it still enters the all-outcome E1 path, preserving the
legacy post-write gate shape.

### Shared E1 public composition and retained owners

The public shared configuration now selects the already-qualified
`core_staging_with_shared_integrated_default` profile. Profile validation runs
before effects and retains the existing E1 order:

```text
CREATED_NEW only:
  contradiction no-op -> SRG -> Hivemind -> M1 -> identity-anchor no-op
  -> mood target
all noncanonical-failure outcomes:
  shared trajectory (CREATE) or world step (other)
  -> Character scope/no-op behavior -> shared checkpoint
  -> compression-disabled no-op -> general proposal gate -> shared bridge suggestion
```

The new `NativeSharedPostWriteExternalWorkspace` is an authority boundary, not
a writer implementation: it supplies the existing `ProposalRegistry` map for
the retained Hivemind convergence side effect and the existing `BridgeRegistry`
writer at E1's existing bridge slot. It exposes no legacy graph, motif registry,
router, or shared conflict writer. Shared bridge geometry is the existing
read-only `NativeMotifGeometryAdapter` over explicit admitted shared-domain
order. Trajectory, checkpoint, Hivemind, motif maintenance, mood target,
Character no-op/scope behavior, compression no-op, and bridge behavior remain
the already-qualified E1 primitives and external owners.

```text
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION = PASS
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = NO_LONGER_OPEN
SHARED_SPAWN_OBSERVER_PARITY = PASS
SHARED_EMBED_AUDIT_DIRTY_PARITY = PASS
SHARED_MOTIF_PRECOMMIT_PARITY = PASS_BOUNDED_NON_TRUE_SPLIT_SCOPE
SHARED_SYMBOL_STATE_PARITY = PASS
SHARED_RESONANCE_PARITY = PASS
SHARED_EXISTING_POSTWRITE_DISPATCH = PRESERVED
SHARED_POSTWRITE_PARITY = PASS_BOUNDED_EXISTING_QUALIFIED_COMPOSITION
SHARED_NATIVE_PUBLIC_PARITY = PASS_BOUNDED_NON_TRUE_SPLIT_SCOPE
SHARED_REPLAY_MODEL = QUALIFIED_BOUNDED_PUBLIC_RECEIPT_AND_EXISTING_OWNER_MODEL
SHARED_REINFORCEMENT_EXCLUSION_DEPENDS_ON_SHARED_AGENT_ID_REPRESENTATION = YES_CURRENTLY
I4G_SHARED_REINFORCEMENT_SCOPE_GUARD_REVIEW_REQUIRED = YES
```

Focused I4F-B evidence used fresh external pytest bases under `conda activate
torment` (with no port-8787 listener):

```text
tests/test_b5_a4r2_native_public_ingest_recovery.py::test_shared_source_replay_does_not_duplicate_its_native_source
tests/test_p9d_i4b1f_public_outcome_parity.py::test_i4fb_shared_public_create_restores_precommit_owners_and_enters_e1
tests/test_p9d_i4b1f_public_outcome_parity.py::test_i4fb_shared_true_split_is_refused_before_precommit_or_post_write
tests/test_p9d_i4b1f_public_outcome_parity.py::test_i4fb_shared_no_write_skips_precommit_but_reaches_e1
tests/test_p9d_i4b1f_public_outcome_parity.py::test_i4fb_shared_canonical_failure_keeps_precommit_residue_but_no_e1_tail
tests/test_p9d_i4b1f_public_outcome_parity.py::test_i4fb_repeated_shared_input_is_not_recast_as_private_reinforcement
6 passed

tests/test_p9d_i4b1_primary_precommit_parity.py
tests/test_p9d_i4b1f_public_outcome_parity.py
tests/test_b5_a4r2_native_public_ingest_recovery.py
60 passed

tests/test_p9d_i4b1_external_precommit_owner_parity.py
3 passed

tests/test_substrate_fabric_native_routing.py
tests/test_substrate_native_post_write_runtime.py
tests/test_substrate_native_integrated_direct_shared_ingest.py
tests/test_substrate_native_shared_bridge_post_write.py
tests/test_substrate_native_shared_m1_mood_post_write.py
tests/test_substrate_native_shared_trajectory_evidence.py
tests/test_substrate_native_shared_checkpoint_snapshot.py
tests/test_substrate_native_shared_compression_deep_memory.py
102 passed
```

```text
ROLE_FORMULA_CHANGES = 0
AFFECT_FORMULA_CHANGES = 0
REINFORCEMENT_FORMULA_CHANGES = 0
MOTIF_FORMULA_CHANGES = 0
SYMBOL_FORMULA_CHANGES = 0
RESONANCE_FORMULA_CHANGES = 0
HIVEMIND_FORMULA_CHANGES = 0
TRAJECTORY_FORMULA_CHANGES = 0
BRIDGE_FORMULA_CHANGES = 0
QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES

I4F_B_ADVERSARIAL_REVIEW = PASS_AFTER_REQUIRED_DOCUMENTATION_CORRECTION
I4F_B_READY_TO_FREEZE = YES
I4F_B_FROZEN = YES
P9D_I4F_B_SHARED_COMPOSITION_PARITY = PASS_BOUNDED_SHARED_NON_TRUE_SPLIT_SCOPE
PRIVATE_I4B2_TRUE_SPLIT_PARITY = FROZEN_PRESERVED
I4C_R1_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = OPEN
I4C_R1_REQUIRED_BEFORE_I4G_FINAL_FREEZE = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
