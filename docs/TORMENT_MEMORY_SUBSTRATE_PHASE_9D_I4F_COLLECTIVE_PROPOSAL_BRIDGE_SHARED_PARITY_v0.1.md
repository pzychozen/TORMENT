# TORMENT Memory Substrate — Phase 9D I4F

## Collective, proposal, bridge, and shared-composition parity

**Status:** D1 scope-corrected I4F-A artifact, **READY_TO_FREEZE**. It does not
authorize activation, real-root use, a service/provider contact, a
SQLite shadow store, compression/deep-memory work, or retirement of a legacy
owner.

**Base:** `53cbf06ac5235fb578bc5741c889eb2734591141` (`qualify-phase-9d-i4e-srg-world-trajectory-checkpoint-parity`).

```text
I4F_IMPLEMENTATION_SHAPE = SPLIT_SUBSLICES_REQUIRED
I4F_A = IMPLEMENTED
    ordinary broad-private native-public conflict correction + proposal + bridge continuation
I4F_A_DELTA_REVIEW = PASS_AFTER_REQUIRED_SCOPE_CORRECTION
I4F_A_READY_TO_FREEZE = YES
I4F_B = NOT_IMPLEMENTED
    shared external-owner restoration + shared native-public composition

SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
SHARED_I4B2_TWO_STAGE_PARITY = NOT_CLAIMED
SHARED_NATIVE_PUBLIC_PARITY = NOT_YET_QUALIFIED
PREEXISTING_QUALIFIED_HIVEMIND = FROZEN_PRESERVED
NEW_HIVEMIND_OWNER = NO
SQLITE_SHADOW_PACKET_STORE = NO
EXACTLY_ONCE_CLAIM = NO
COMPRESSION_DEEP_MIGRATED = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Shape decision and implementation boundary

Shared restoration is materially larger than I4F-A. The native public executor deliberately sets `precommit_parity_required=True` only for private requests. Shared stays on the established I3 composition/recovery path. The request may carry the retained embed-audit spawn observer and symbol-state callback, but that does not prove the private I4B-1 owner ordering, recovery facts, or I4B-2 true-split topology for shared. Enabling the private parity flag for shared would re-admit an unproven private-qualified precommit route.

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

## Shared inventory and non-claim

| Shared behavior | Existing status | I4F result |
|---|---|---|
| B1 bridge suggestion | Frozen standalone primitive | Preserved; not selected by current public shared configuration. |
| D1 M1 + private-target mood | Existing public shared configuration | Narrow/partial, not full system parity. |
| D2 Hivemind | Frozen standalone primitive | Preserved; not selected by current public shared configuration. |
| D3 trajectory / D4 checkpoint / D6 compression no-op | Frozen standalone primitives | Preserved; not selected by current public shared configuration. |
| E1 integrated default | Explicit separately prepared profile | Not a current shared public route claim. |

The public shared configuration remains D1-only. It does not use I4F's private proposal/bridge bindings and does not compose B1/D2/D3/D4/D6/E1 as a system.

```text
SHARED_PRECOMMIT_OWNER_PARITY = NOT_ATTEMPTED_PENDING_I4F_B
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION = REQUIRED
SHARED_TRUE_SPLIT_DISPOSITION = NOT_CLAIMED
SHARED_POSTWRITE_PARITY = EXISTING_PRIMITIVES_ONLY_NOT_SYSTEM_LEVEL
SHARED_NATIVE_PUBLIC_PARITY = NOT_YET_QUALIFIED
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
I4F_B = NOT_STARTED
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
