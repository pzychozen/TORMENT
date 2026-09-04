# TORMENT Memory Substrate — Functionality Preservation Matrix

**Version:** 0.1

**Status:** living I3C / bounded I4B-1, I4B-2, I4C, I4D, I4E, and frozen
I4F-A preservation artifact. I4E correction state is **FROZEN** after focused delta review;
I4F-A is D1 scope-corrected and **READY_TO_FREEZE**. Its shared I4F-B
prerequisite is not claimed. It records current offline evidence and
does not authorize a real-root contact, service start, provider contact,
re-embedding, selected-profile activation, or component retirement.

## Preservation law

```text
LEGACY_FUNCTIONALITY = REFERENCE
NATIVE_GAP = ACTIVATION_BLOCKER
NATIVE_GAP != PERMISSION_TO_REMOVE_LEGACY_BEHAVIOR

RETIREMENT_ALLOWED = NO
MATRIX_ROW_ABSENT = RETIREMENT_FORBIDDEN
CAPABILITY_UNMAPPED = ACTIVATION_BLOCKING
```

The last value can change for one row only after all of the following are
named and independently satisfied: parity evidence, qualified composition
behavior, a selected-profile disposition, and the explicit retirement gate.
I3C satisfies none of those retirement conditions for any legacy component.

`PASS` below means only the bounded evidence named in that cell. `OPEN`,
`BLOCKING`, `PARTIAL`, and `NOT YET QUALIFIED` deliberately retain their
ordinary meaning and must not be read as hidden approvals.

| Function / behavior | Legacy semantic owner | Durable / external owner | Native replacement or adapter | Parity evidence | Composition gate | Retirement allowed? |
|---|---|---|---|---|---|---|
| Input write gate / provenance | `TormentFabric.ingest` input gate and provenance boundary | Legacy graph, identity, and provenance records | Native public ingest executor only after selected-policy proof | Main ingest census; direct-writer bypasses remain unresolved | I4 must preserve the gate and provenance authority | NO |
| Memory create | `TormentFabric.ingest` / legacy storage adapter | Legacy graph, identity, external admission | `NativePrimaryPrecommitService` through the bounded native route | I4B-1 primary fixtures; private I4B-2/I4C/I4D fixtures; I4E and I4F-A public outcome fixtures | Ordinary broad-private create retains the existing external Hivemind call. I4E extends the tail with SRG, private world/trajectory, and checkpoint; I4F-A corrects the broad-private conflict map and retains proposal then bridge after the deferred compression slot. True split adds none of those tails and shared is not claimed | NO |
| Embed-audit dirty marking | Legacy ingest and derived-memory creation audit invalidation | Existing workspace embed_audit.json when present | Bounded public-ingest observer; external file owner retained | I4B-1 synthetic temp-path observer proves post-spawn/pre-motif ordering and survival after canonical failure | Best-effort dirty state occurs after spawn and before motif/flush; real-root/service activation remains forbidden | NO |
| Reinforcement | Fabric / legacy post-write adapter | Legacy graph payload and JSONL | Native reinforcement/runtime primitive | `test_substrate_memory_reinforcement.py`, I4B-1 formula/backfill fixtures, and I4B1F full native-public reinforcement fixture | I4B-1 preserves formulas and the existing reinforcement source owner; RoleStore/affect preparation runs while CREATE-only motif/symbol effects remain absent; SRG and post-commit consumers remain separately gated | NO |
| Motif attach / create | Legacy motif runtime selected by `TormentFabric.ingest` | Live legacy motif registry | I4B-1 precommit motif mutation plus private I4B-2 two-stage existing-schema split operations | I4B-1 ordinary attach/flush fixtures; private I4B-2 T0/T1/T2, candidate disposition, source/abort recovery and public CREATE fixtures | Private true split is qualified only as attach -> durable parent -> atomic final parent/child topology; no formula/schema/outbox change. Shared I4B-2 topology is not qualified | NO |
| Motif maintenance / split / merge | Legacy motif runtime and merge policy | Live registry, merge suggestions, and policy records | Private I4B-2 bounded true-split `CREATED_NEW` M1/M2 workflow plus existing native motif split/merge owners | Private I4B-2 motif-only tail, null-runtime, independent failure, public-handoff, I4C conflict-before-M1, I4D ordered continuation, I4E true-split order, and motif regression fixtures | Qualified only for the private true-split prefix: I4C conflict, then SRG, entropy/suggestions, policy-authorized auto-merge, frozen anchors, I4D mood, and I4E world/trajectory -> Character -> checkpoint. Shared remains separately dispatched; Hivemind, compression, proposal, and bridge are outside this profile | NO |
| Query embedding | Fabric kernel embedder | Configured provider/model lane | Same Fabric owner and admitted native lane validation | I3A/I3B query parity | Representation identity remains selected-profile gate | NO |
| ThinkingController MemoryPlan policy | `ThinkingController.build_memory_plan` + `TormentFabric.query` | Ephemeral policy state; no native storage owner | Same existing cognition owner | Main query census: lane budgets, weights, bounded allocation, and deep-lane interaction | Native storage must not become the MemoryPlan owner | NO |
| Candidate retrieval | `MemoryGraph.search` | Legacy graph embeddings | `NativeMemoryVectorRuntime` through `NativeQualifiedQueryReadModel` | I3B candidate shape, stale, and I3C malformed-vector tests | Qualified snapshot required | NO |
| Malformed legacy representation | Legacy graph/cache may contain non-finite vectors | Legacy representation payload/cache | Qualified native admission requires finite geometry | I3C NaN fixture | `MALFORMED_VECTOR_DISPOSITION = LAWFUL_FAIL_CLOSED_ASYMMETRY`; normalize, disposition, or exclude before migration | NO |
| Decay | `MemoryGraph.search` half-life law | Memory payload timestamps | Native compatible vector projection | I3B normalization/decay differential | No formula consolidation before I3D | NO |
| Query scoring | `TormentFabric.query` / `score_hit` | None beyond qualified input facts | Same Fabric owner | I3A/I3B explain decomposition | One query owner must remain | NO |
| Continuity | Fabric continuity construction | External role/affect state where applicable | Same Fabric owner | A3 differential coverage plus I4B1E and I4B1F full-public role/affect fixtures | Native public precommit preserves RoleStore and affect-classification behavior for CREATE, REINFORCE, and ordinary NO_WRITE; post-write mood drift remains separately owned | NO |
| Governance / FILTER-A | Existing cognition/governance path, `filter_llm_facing` | Governance flags/audit and hit payload | No native storage replacement | Main query census: `filter_llm_facing`, `excluded`, `filter_excluded`, `_core_hits_in_count` | Active LLM-facing query chokepoint; preserve owner and filtering semantics | NO |
| Ordering / top-k truncation | MemoryGraph and Fabric stable ordering | Persisted EID/order witnesses | Native vector rows plus existing Fabric merge/sort | I3B plus I3C non-contiguous EID fixture; I4B-1 live motif append/recovery fixture | Query ordering is unchanged; I4B-1 qualifies lexical recovery plus appended live motif creation only | NO |
| Domain routing | Fabric `_rank_domains_from_read_model` | Domain declaration order | Native geometry read adapter | I3B tie/override fixture | No independent native router policy | NO |
| Motif geometry | `MotifRegistry` | Persisted motifs / embeddings | Native motif reader/geometry adapter | I3B geometry differential; private I4B-2 two-stage split parent/child topology fixtures | Private I4B-2 preserves the policy-owned parent/child geometry and appends a child only after Stage B; restart order remains lexical | NO |
| Zero-member motifs | Legacy zero-member geometry law | Certified B4C durable lineage | Native zero-member reader/projection | B4C and I3B tests | Certification remains required | NO |
| Active motif context | Motif registry + Fabric presentation | Persisted motif state | Native motif reader plus existing `_active_summary` | I3B active-order parity; I4B-1 orphan member-count/domain-centroid fixture | I4B-1 preserves precommit orphan-motif read effect; post-commit maintenance remains open | NO |
| `dominant_thread` | Fabric `dominant_thread` | Active motif context | Same Fabric function | I3B gravity/raw-strength fixture | No new tie policy | NO |
| Character seed/context | Fabric + `assemble_character_context` | External `CharacterStore` | Retained external owner | A3 and I3C absent/read-failure characterization | Absence of `character_context` is not a health signal: disabled Character, absent seed/state, and `CharacterStore` read failure share the same broad fail-soft boundary; write composition is I4 | NO |
| Character drift | Character runtime | External `CharacterStore` state JSON | Qualified native measurement with retained external state owner | I4D full public create/state/reload and native drift parity suites | Private native-public only: exact measurement/order/formula/cadence/history retained; reinforcement is an effective no-op, no-write is not due, canonical failure stops before post-write | NO |
| Character drift reflex | Fabric rising-edge callback after high-drift measurement | Process-local Fabric high-drift map plus external callback owner | Retained callback composed after qualified native Character/gravity | I4D public high-drift/reflex fixture | Existing rising-edge and callback-failure behavior retained. Restart clears the process-local map, so the first later high measurement may re-fire. No autonomous control authority | NO |
| Character gravity | Character runtime | Native additive correction plus retained external Character state | Existing native gravity runtime | I4D public high-drift fixture and native gravity/recovery suites | Private native-public only: additive qualified child, retained formula, and best-effort motif work; it never calls Fabric ingest or re-enters full post-write | NO |
| Conflict persistence | `LegacyFabricPostWriteAdapter._run_contradiction_surface` and existing conflict heuristic | External `ConflictRegistry` JSONL/evidence | Retained legacy contradiction surface on private native-public `CREATED_NEW`: frozen I4C true-split prefix plus I4F-A's corrected ordinary broad-private private-domain binding | I4C true-split evidence; I4F-A broad-private external-owner/write-side/failure/replay fixtures | True-split private conflict roundtrip remains qualified. I4F-A qualifies the ordinary broad-private external writer only: private/core/EID gates, candidate filtering, conflict mathematics, append owner, and fail-soft disposition are preserved. Owner re-entry after incomplete post-write has no exactly-once claim | NO |
| Conflict query read | Fabric conflict map | Read-only external conflict evidence | `_ReadOnlyConflictRegistry` | I3B/I3B0 present, absent, malformed evidence tests; I4C origin-isolation regression | Frozen reader: qualified origin map, scoring condition, explain shape, and query ordering remain unchanged. It does not currently include the broad-private conflict domain written by I4F-A; broad-private reader roundtrip is I4C-R1, while shared parity remains unclaimed | NO |
| SRG read | Fabric score/explain source | Legacy payload or native qualified source | `effective_srg_state` | I3B source test; I3C modifier/refusal tests | Full valid state required; optional absence remains lawful | NO |
| SRG query mutation / breathing | Fabric historical nested breathing gate | Live legacy payload / native process overlay | Native process-local overlay | I3C lifecycle characterization | Legacy live-payload mutation is lost after restart without same-entity write; unrelated flush does not persist it; later same-entity write serializes it. Native overlay is process-local only. Restart/write successor parity BLOCKED_PENDING_I4 | NO |
| SRG last-ingest-band coupling | Fabric ingest-to-query/trace same-band resonance | Process-local Fabric state keyed by workspace_id and agent_id | No qualified native cross-route owner | Main ingest/query/trace census | Ingest stores R_band; query and trace apply the existing 1.08 multiplier only when the same agent's last band matches; restart clears it | NO |
| SRG relational EMA | Fabric ingest-to-Spine geometric-context coupling | Process-local Fabric EMA keyed by workspace_id and agent_id | No qualified native cross-route owner | Main ingest/Spine census | First ingest seeds L_amplitude; later ingests use 0.8 previous + 0.2 new; restart clears it | NO |
| SRG error-handler failure disposition | Fabric breathing error handler | No separate durable owner | Same handler; I3C defect repair | I3C first-hit evolution-failure characterization | `SRG_ERROR_HANDLER_LATENT_DEFECT_FIXED = YES`; the prior first-hit `UnboundLocalError` / later-hit stale-EID diagnostic behavior is not retained | NO |
| SRG post-write collision / state | Legacy post-write adapter and SRG runtime | Current source payload plus process-local collision overlay | Retained collision writer over `NativeSRGTransientRuntime`; existing typed R2/N02 successors only | I4E same-process/restart-baseline, public outcome, and existing ordered transient/reinforcement suites | Private `CREATED_NEW` collision only; no fake durable write, new successor, formula, or shared claim. Exact successor materialization remains frozen R2/N02 authority | NO |
| World / trajectory | Legacy world and post-write runtime | Process-local world plus external private trajectory artifacts | `NativeWorldRuntime` plus `NativePrivateTrajectoryEvidenceProcessState` and separately bound `NativePrivateTrajectoryEvidenceRuntime` | I4E private replay/failure/V2 sealing and public outcome suites; existing native world/trajectory suites | Private native-public only, all successful post-write outcomes; V2 genesis is created-only, physics remains process-local, evidence stays external and has one writer lifetime per core/private-source process owner. Shared D3 ownership is separate | NO |
| Checkpoint | Checkpoint subsystem | External private checkpoint files | Separately bound private existing `save_checkpoint` writer with qualified native reads | I4E checkpoint content/absence/failure/public-owner suites; existing D4 checkpoint suites | Private native-public only, after Character on legacy cadence and all successful outcomes. Snapshot is non-authoritative; existing private embeddings manifest is read through `build_shard_snapshot`, otherwise snapshot is `None`; shared D4 is separate | NO |
| Bridge peek | Fabric `_query_shared_lane` | Existing bridge registry and domain policies | Same query owner over qualified shared reads | Main query census: `bridge_peek_requires_approval`, approved-or-confidence `>= 0.65`, `via_bridge` marking | Query-side retrieval is distinct from bridge suggestion mutation | NO |
| Bridge suggestions | Bridge policy / post-write behavior | External `BridgeRegistry` JSON/files | I4F-A retained private post-write writer with a private-specific, authoritative-order native geometry | I4F-A public outcome/formula/owner/failure fixtures; existing bridge suites | Ordinary broad-private successful private outcomes only, after general proposal. Geometry preserves the full legacy private-plus-admitted-shared domain set and `domains.json` order; random/geometry/registry failures propagate. I4B-2 true split and shared system parity remain excluded | NO |
| Bridge registry inspection / decision | Existing bridge registry routes | External bridge records | No native public route parity | I2/public-service census | Root-native path remains refused until route parity | NO |
| Hivemind / collective context | Collective presentation owner | External collective field | No native read adapter | I3B0 refusal test | REFUSE_WHEN_APPLICABLE; activation gate OPEN | NO |
| Archive recall | `/retrieve` composite assembler | External archive store | No native composite adapter | I3B0 refusal test | REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY | NO |
| Archive retrieval-count write | Archive promotion/read accounting | External archive counter | No native adapter | Not reached after archive refusal | BLOCKING composite gate | NO |
| Shared ingest | Fabric shared ingest / proposal policy | Shared graph and external policy | Native public ingest route | Storage path exists; shared direct `created_motif` now follows route truth (`ATTACH_EXISTING` -> `None`); system parity NOT YET QUALIFIED | Current native-public shared scope is not claimed. I4B-2 excludes shared requests from the private-qualified I4B precommit route and does not qualify shared true-split topology or post-write. Existing shared post-write claims remain separately qualified; I4 post-write and conflict composition remain open | NO |
| Proposals | General post-write proposal and proposal orchestration | External `ProposalRegistry` records / existing receipts | I4F-A retained private post-write proposal binding with one memoized registry per admissible domain/configuration; native authorized proposal primitives remain separate | I4F-A public proposal-result/replay/failure and collective convergence co-existence fixtures and existing substrate suites | Ordinary broad-private private scope only. Existing gates/formulas/identity-save-after-submit disposition retained; a convergence proposal and general proposal remain independently appendable. Shared system parity remains excluded | NO |
| Role / affect / symbol | RoleStore, affect classifier, and Fabric symbol-state writer | External role file / affect history / symbol state | I4B1E/F source-selected native precommit composition | I3B0 read fencing plus I4B1E storage and I4B1F full public create/reinforce/NO_WRITE/failure/restart fixtures | Role and classifier precommit parity is qualified on each reachable branch; affect history is post-write mood drift; symbol/resonance state is CREATE-only precommit | NO |
| Derived memory | Derived-memory runtime | Native derived children plus retained anchor/affect external state | Native derived runtime primitives | Existing N02 lifecycle tests; I4B-2 anchor prefix; I4D public mood success/miss/failure/replay and derived recovery suites | Identity anchors remain frozen N02. I4D qualifies only private native-public mood after the retained M1/anchor gate; no general SRG successor, shared, or remaining derived composition is claimed | NO |
| Compression / deep-memory export | Legacy compression post-write runtime | Deep-memory files and compressed source metadata | No qualified native post-write path | Main ingest/post-write and public-service census | Deep export/compression control remains pre-activation gated | NO |
| Deep memory / spirit return | Legacy `_query_deep_lane` and spirit-return enrichers | Per-agent deep-memory store | NATIVE SUPPORT = NO | Main query/service census: spirit modes `resonance`, `surfacing`, `recollection`; `_is_deep` classification; Character voice recommendations can consume spirit hits | When `TORMENT_COMPRESS_ENABLE` / deep retrieval applies, activation is refused; `DEEP_RETRIEVAL_PROFILE_GATE = OPEN_PRE_ACTIVATION` | NO |
| Hivemind emission / convergence | Legacy post-write adapter / collective field | External collective packets, events, convergence-pattern records, and retained proposal owner | Retained existing broad-private external call; I4F-A restores its previously inert convergence-proposal side effect through the memoized external proposal owner map | I4E retained-call regression, I4F-A direct re-entry/convergence-proposal/failure-independence evidence, collective suites | Existing broad-private created-only owner remains preserved. Packet re-entry remains append-only; restart loses embedding/cooldown process state. Convergence drafting is fail-soft and distinct from the later general proposal. Query remains refuse-when-applicable; no shared/new-owner parity is claimed | NO |
| Failure dispositions | Each current semantic owner | Owner-specific files/state | Qualified read refusal and existing fail-soft paths | I3B snapshot/conflict; I3C SRG/Character/malformed vector; I4B-1 attach/flush/fallthrough witnesses | Preserve per-surface behavior; no universal normalization | NO |
| Provenance / explain | Fabric result assembly | Candidate payload/external provenance | Same Fabric owner over qualified hits | I3A/I3B explain differential | Query math and provenance owner retained | NO |
| Restart / recovery | Legacy graph reload; native root recovery | Legacy files / qualified root profile | Native recovery and process-local overlays | I1/I1C and I3C SRG restart characterization | SRG query-to-write composition I4; real activation prohibited | NO |
| Reference ordinary query class | Explicit reference surface, not MemoryGraph default query | External reference store | Existing native parity-ready classification | I3AR classification; `_NON_DEFAULT_CLASSES` excludes it | Any materializing public route needs its own classification | NO |
| Environment ordinary query class | Explicit environment surface, not MemoryGraph default query | External environment store | Existing native parity-ready classification | I3AR classification; `_NON_DEFAULT_CLASSES` excludes it | Any materializing public route needs its own classification | NO |
| Baton ordinary query class | Explicit baton surface, not MemoryGraph default query | External baton store | Existing native parity-ready classification | I3AR classification; `_NON_DEFAULT_CLASSES` excludes it | Any materializing public route needs its own classification | NO |
| Closure ordinary query class | Explicit closure surface, not MemoryGraph default query | External closure store | Existing native parity-ready classification | I3AR classification; `_NON_DEFAULT_CLASSES` excludes it | Any materializing public route needs its own classification | NO |
| Public health / profile / config observability | Existing service configuration and deployment resolver | Process configuration / selected deployment agreement | Existing explicit public properties only | I2 explicit property census and public-route census | Observability is not native authority, admission, or activation | NO |
| Embedding audit / repair operations | Legacy workspace repair and embedder health paths | Legacy embedding files and configured provider lane | No complete native maintenance route | I2 public census and service-route census | Root-native operations remain refused until qualified | NO |
| Workspace lifecycle / clone | Legacy workspace constructors and clone runtime | Legacy workspace tree / clone records | Root-qualified workspace view is read-only; no native lifecycle authority | I2 fencing census | External admission/lifecycle authority remains open | NO |
| Workspace maintenance / clone jobs | Legacy maintenance and job registries | Legacy job records and workspace files | No native maintenance replacement | I2 and service-route census | Native route classification and post-write parity required | NO |
| Workspace / domain metadata | Existing workspace metadata and domain listing owners | Legacy workspace metadata | Root-qualified view only where already explicit | I2 public census | No materializing fallback in native mode | NO |
| Agent identity lifecycle | Legacy `create_agent` / identity store | Legacy identity and external admission facts | Native preparation of already-admitted identity only | I2 public fencing | Admission-owner authority remains open | NO |
| Character external-state inspection | Existing Character routes and `CharacterStore` | External Character seed/state | Retained external owner | Public-service census | Read surface does not authorize Character writes | NO |
| Trace / chain / index diagnostics | Fabric trace/lineage/index and service diagnostic routes | Legacy graph, archive, trajectory, and provenance records | No general native fallthrough | I2 plus public-service census | Each materializing or composite route needs its own qualification | NO |
| Archive document lifecycle | Archive document endpoints / `ArchiveStore` | External archive documents | No native document lifecycle adapter | Public-service census | Archive operations remain separately gated | NO |
| Index rebuild | Legacy index rebuild operation | Legacy index files | No native rebuild route | Public-service census | Rebuild is a post-write/maintenance gate | NO |
| Promotion operations | Existing promote routes and promotion policy | External promotion/archive evidence | No qualified native operation | Public-service census | I4/post-write parity required | NO |
| Cognition / Spine orchestration | Existing cognition and Spine controllers | Existing operation/task records | No native substrate ownership replacement | Public-service census | Route classification is independent of storage migration | NO |
| Tool-result ingestion | Existing tool-ingest route and provenance policy | Legacy graph and tool provenance | No qualified native route parity | Public-service census | Input gate/provenance parity required | NO |
| Thinking / debug / metrics observability | Thinking-controller and diagnostics routes | Ephemeral controller/diagnostic state | Same owner; no storage replacement | Public-service census | Observability does not authorize policy replacement | NO |
| Reference lifecycle | `ingest_reference`, `load_reference`, `unload_reference`, active-loads path | External reference store | No qualified native materializing lifecycle route | I2 public census | `Reference ordinary query class` does not qualify lifecycle writes | NO |
| Environment lifecycle | `write_environment`, `consult_environment`, probe path | External environment store | No qualified native materializing lifecycle route | I2 public census | `Environment ordinary query class` does not qualify lifecycle writes | NO |
| Baton lifecycle | Baton list / resolve path | External baton store | No qualified native materializing lifecycle route | I2 public census | `Baton ordinary query class` does not qualify lifecycle writes | NO |
| Closure lifecycle | Closure proposal, ratification, commit, revision, and read paths | External closure records | No qualified native materializing lifecycle route | I2 public census | `Closure ordinary query class` does not qualify lifecycle writes | NO |

## I3C query-composition reading

```text
CORE_QUERY_READ_PARITY = QUALIFIED_OFFLINE
SRG_READ_PARITY = PASS
SRG_SAME_PROCESS_MUTATION = PASS_WITHIN_HISTORICAL_NESTED_GATE
SRG_RESTART_WRITE_COMPOSITION = BLOCKED_PENDING_I4
MOTIF_LIVE_INSERTION_ORDER = QUALIFIED_I4B1_PRIMARY_CREATE_PLUS_PRIVATE_I4B2_TRUE_SPLIT_SCOPE
CHARACTER_QUERY_READ = PASS
CHARACTER_WRITE_COMPOSITION = QUALIFIED_I4D_PRIVATE_NATIVE_PUBLIC_SCOPE
DERIVED_MOOD_WRITE_COMPOSITION = QUALIFIED_I4D_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_WORLD_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4D
CHARACTER_WORLD_COMPOSITION = COMPOSED_PRIVATE_I4E
SHARED_I4D_PARITY = NOT_CLAIMED
SRG_POSTWRITE_COLLISION = QUALIFIED_PRIVATE_TRANSIENT_SCOPE
SRG_RESTART_WRITE_COMPOSITION = QUALIFIED_PRIVATE_NATIVE_PUBLIC_BASELINE_ONLY_NO_FAKE_PERSISTENCE
WORLD_TRAJECTORY_WRITE_COMPOSITION = QUALIFIED_PRIVATE_EXTERNAL_OWNER_SCOPE
CHECKPOINT_WRITE_COMPOSITION = QUALIFIED_PRIVATE_EXTERNAL_OWNER_SCOPE
HIVEMIND_BROAD_PRIVATE_EXTERNAL_OWNER = RETAINED
HIVEMIND_NEW_SCOPE = EXCLUDED
SHARED_I4E_PARITY = NOT_CLAIMED
CONFLICT_QUERY_READ = PASS_FROZEN
I4C_TRUE_SPLIT_CONFLICT_ROUNDTRIP = QUALIFIED
I4C_BROAD_PRIVATE_CONFLICT_WRITER = PASS_WRITE_SIDE_ONLY
I4C_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = NOT_YET_QUALIFIED
I4C_BROAD_PRIVATE_CONFLICT_SYSTEM_PARITY = NOT_YET_QUALIFIED
I4C_R1_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = OPEN
I4C_R1_REQUIRED_BEFORE_I4G_FINAL_FREEZE = YES
SHARED_I4C_PARITY = NOT_CLAIMED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
COLLECTIVE = REFUSE_WHEN_APPLICABLE
ARCHIVE = REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
LEGACY_QUERY_READER_RETIREMENT = NOT_AUTHORIZED
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

The matrix distinguishes a query read that retains an external owner from a
future write route that would have to preserve the same owner. Query parity
does not authorize that write route.

## I4B-1C primary/precommit qualification

```text
FAILED_EID_NON_REUSE = RESTART_STABLE
LEGACY_CROSS_RESTART_ABORTED_EID_REUSE = DOCUMENTED_UNSAFE_RECOVERY_DIVERGENCE
CROSS_RESTART_EID_DIVERGENCE = DELIBERATELY_ACCEPTED_IDENTITY_SAFETY_REPAIR

CANONICAL_MEMORY_FILTER_RULE =
    existence_state == EXISTS is required where the answer is
    "is this a canonical memory?"
    It is not automatically propagated to a semantic owner's state count.

CANONICAL_READERS_FILTER_ABORTED = YES
MOTIF_MEMBERSHIP_READER_FILTERS_MEMBER_EXISTENCE = NO (DELIBERATE)
MISSING_CURRENT_REVISION = MALFORMED_SUBSTRATE_STATE_SILENTLY_EXCLUDED

TRUE_SPLIT_I4B1_REACHABILITY = YES
TRUE_SPLIT_NATIVE_DISPOSITION = RETIRED_BY_QUALIFIED_PRIVATE_I4B2_TWO_STAGE_PARITY
TRUE_SPLIT_FAILURE_STAGE_COUNT = 5
TRUE_SPLIT_REPLAY = QUALIFIED_BOUNDED_STAGE_A_STAGE_B_WITNESS
TRUE_SPLIT_POSTCOMMIT_TAIL = QUALIFIED_PRIVATE_MOTIF_ONLY_CREATED_NEW_PREFIX
I4B1_ATTACH_FAILURE_STAGE_MODEL = COMPLETE_TWO_STAGE
EMBED_AUDIT_DIRTY_PARITY = PASS_TESTED_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE (SYNTHETIC_EXTERNAL_OBSERVER)

PUBLIC_NATIVE_NO_WRITE_REPORTING_DEFECT_FIXED = YES
LEGACY/NATIVE_PUBLIC_OBSERVABLE_BEHAVIOR_CHANGED = YES

CANONICAL_OPERATION_OWNER = EXISTING_NATIVE_FABRIC_NEW_MEMORY_SOURCE_OPERATION
I4B1_CANONICAL_OPERATION_OWNERSHIP = NO
CANONICAL_OPERATION_OWNERSHIP = PRESERVED
PUBLIC_INGEST_OPERATION_KEY_MISMATCH = FIXED
PUBLIC_INGEST_REGRESSION_FROM_I4B1E = CLOSED
CANONICAL_FAILURE_POSTWRITE_DISPOSITION = SHORT_CIRCUIT
ORDINARY_NO_WRITE_DISPOSITION = QUALIFIED_BOUNDED
EXTERNAL_OWNER_NO_WRITE_PARITY = PASS
EXTERNAL_OWNER_REINFORCEMENT_PARITY = PASS
EXTERNAL_OWNER_RESTART_PARITY = PASS (RoleStore/symbol-state residue; affect has no precommit durable mutation)
I4B1_READY_TO_FREEZE = YES (bounded artifact; final narrow review still required)

CHARACTER_GRAVITY_NESTED_WRITE_RECURSION = QUALIFIED_I4D_NO_FABRIC_REENTRY
GRAVITY_ORPHAN_POLICY_PARITY = QUALIFIED_BOUNDED_PRIVATE_NATIVE_PUBLIC_SCOPE

ROLE_PRECOMMIT_PARITY = PASS
AFFECT_PRECOMMIT_PARITY = PASS
SYMBOL_STATE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
RESONANCE_PRECOMMIT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
PRECOMMIT_EXTERNAL_OWNER_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_PRECOMMIT_SCOPE
I4B1_PRECOMMIT_EXTERNAL_OWNER_SCOPE = PRIVATE_QUALIFIED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
I4C_SHARED_SCOPE_PREREQUISITE = DO_NOT_INFER_SHARED_PRECOMMIT_PARITY_FROM_PRIVATE_I4B1_RECEIPTS
EXTERNAL_OWNER_MIGRATION_TO_SQLITE = NO
```

I4B1E preserves the external owners without creating a generalized side-effect
framework: RoleStore updates before the write decision on every ingest branch;
affect classification remains pre-decision while affect-state/mood-drift stays
post-write; and Fabric's symbol-state writer runs after motif persistence but
before canonical commit on CREATE only. Symbol state may survive a failed
primary memory; resonance enrichment may not become canonical without it.

## Functionality-preservation denominator

This is the bounded denominator for pre-I4 planning. It is a source-live
capability census, not a claim about a real production profile. Its three
inputs are: (1) the public/service operation surface, starting with the I2
public fallthrough census and current `app.py` routes; (2) the main
`ThinkingController` / `TormentFabric.query` call graph; and (3) the main
`TormentFabric.ingest` / `LegacyFabricPostWriteAdapter` call graph.

Brainvision, the unrelated cognitive function, historical experiments, and
test-only helpers are excluded. I2's legacy-only public operations are still
included: native refusal is a disposition, not evidence that the live legacy
capability can be omitted.

Every identifier below names a capability rather than an implementation
helper. `MAPPED_MATRIX_ROW` names the row that owns its preservation and
activation disposition. There are no `UNMAPPED` entries.

~~~text
CROSS_ROUTE_PROCESS_STATE_RULE =

Any process-local Fabric state whose write site is on one live route and whose
read site is on another live route, where the value changes observable or
cognitive behavior, is a FUNCTIONAL CAPABILITY and must have its own matrix
disposition. It is not merely a cache.
~~~

### Public / service operation capabilities

| ID | Capability / routed operation family | MAPPED_MATRIX_ROW |
|---|---|---|
| C01 | Service health, profile, and configuration observability | Public health / profile / config observability |
| C02 | Embedder check and embedding audit | Embedding audit / repair operations |
| C03 | Workspace creation and cloning | Workspace lifecycle / clone |
| C04 | Workspace maintenance, embedding repair, and clone/repair jobs | Workspace maintenance / clone jobs; Embedding audit / repair operations |
| C05 | Workspace metadata and domain discovery | Workspace / domain metadata |
| C06 | Agent creation, identity lookup, and admitted-identity preparation | Agent identity lifecycle |
| C07 | Character seed/state inspection | Character external-state inspection |
| C08 | Role profile inspection | Role / affect |
| C09 | Governance flag configuration and audit | Governance / FILTER-A |
| C10 | Collective status, packet, event, and proposal-status observation | Hivemind / collective context |
| C11 | Collective reingest | Shared ingest; Hivemind emission / convergence |
| C12 | Public query invocation and result delivery | Query scoring; Provenance / explain |
| C13 | Trace, chain, full-graph, bundle, and view operations | Trace / chain / index diagnostics |
| C14 | Feedback and explicit named-EID reinforcement through Fabric.reinforce / Spine reinforce | Reinforcement |
| C15 | Active motif inspection, entropy, and merge decision | Motif maintenance / split / merge |
| C16 | Bridge listing, queue inspection, and decision | Bridge registry inspection / decision |
| C17 | Proposal processing, domain suggestions, and proposal decision | Proposals |
| C18 | Conflict listing and decision | Conflict persistence; Conflict query read |
| C19 | Archive document ingest, list, read, and deletion | Archive document lifecycle |
| C20 | Archive query and index/archive inspection | Archive recall; Trace / chain / index diagnostics |
| C21 | Index rebuild | Index rebuild |
| C22 | Checkpoint save, latest, and list/recovery management | Checkpoint |
| C23 | Promotion and promotion-suggestion operations | Promotion operations |
| C24 | Compression and spirit-return control/status operations | Compression / deep-memory export; Deep memory / spirit return |
| C25 | Explicit deep-memory query | Deep memory / spirit return |
| C26 | Cognition run and Spine task/operation/status orchestration | Cognition / Spine orchestration |
| C27 | Tool-result ingestion | Tool-result ingestion |
| C28 | Thinking, alignment, metrics, and provenance diagnostics | Thinking / debug / metrics observability |
| C29 | Reference ingestion/load/unload lifecycle | Reference lifecycle |
| C30 | Environment write/consult/probe lifecycle | Environment lifecycle |
| C31 | Baton list/resolve lifecycle | Baton lifecycle |
| C32 | Closure proposal/ratify/commit/revise/read lifecycle | Closure lifecycle |

### Main query capabilities

| ID | Capability | MAPPED_MATRIX_ROW |
|---|---|---|
| C33 | ThinkingController MemoryPlan policy: lane budgets, weights, bounded allocation, and deep-lane interaction | ThinkingController MemoryPlan policy |
| C34 | Query embedding and dimension validation | Query embedding |
| C35 | Private/core candidate retrieval | Candidate retrieval |
| C36 | Shared/relational candidate retrieval | Candidate retrieval |
| C37 | Domain ranking and override routing | Domain routing |
| C38 | Query-side bridge peek, approval/confidence gate, and `via_bridge` marking | Bridge peek |
| C39 | Deep-memory / spirit-return retrieval and `_is_deep` classification | Deep memory / spirit return |
| C40 | Qualified vector admission and decay geometry | Candidate retrieval; Malformed legacy representation; Decay |
| C41 | Query scoring, including retained SRG multipliers | Query scoring; SRG read |
| C42 | Continuity construction | Continuity |
| C43 | Motif geometry reads | Motif geometry |
| C44 | Zero-member motif handling | Zero-member motifs |
| C45 | Active motif context and `dominant_thread` | Active motif context; `dominant_thread` |
| C46 | Optional Character context assembly | Character seed/context |
| C47 | Role and affect read contribution to query continuity | Role / affect; Continuity |
| C48 | Read-only conflict composition | Conflict query read |
| C49 | Effective SRG read and qualified currentness refusal | SRG read |
| C50 | SRG breathing mutation during query | SRG query mutation / breathing; SRG error-handler failure disposition |
| C51 | Governance FILTER-A LLM-facing exclusion/audit | Governance / FILTER-A |
| C52 | Stable ordering and top-k truncation | Ordering / top-k truncation |
| C53 | Explain, provenance, and result observability assembly | Provenance / explain |
| C54 | Collective query context | Hivemind / collective context |
| C55 | Archive/retrieve composition and archive retrieval-count effect | Archive recall; Archive retrieval-count write |
| C56 | Ordinary reference, environment, baton, and closure query classification | Reference ordinary query class; Environment ordinary query class; Baton ordinary query class; Closure ordinary query class |

### Main ingest / post-write capabilities

| ID | Capability | MAPPED_MATRIX_ROW |
|---|---|---|
| C57 | Ordinary write gate and input provenance validation | Input write gate / provenance |
| C58 | Memory creation / durable legacy storage | Memory create |
| C59 | Motif attachment and creation | Motif attach / create |
| C60 | Motif maintenance, split/merge, and live insertion order | Motif maintenance / split / merge |
| C61 | Conflict detection and persistence | Conflict persistence |
| C62 | SRG collision and post-write state handling | SRG post-write collision / state |
| C63 | Character seed association/provenance on ingest | Character seed/context |
| C64 | Character drift and reflex measurement | Character drift |
| C65 | Character gravity correction | Character gravity |
| C66 | Role update and affect classification/attribution | Role / affect |
| C67 | Derived-memory identity-anchor and mood-drift emission | Derived memory |
| C68 | World step and trajectory advancement | World / trajectory |
| C69 | Hivemind packet emission and convergence | Hivemind emission / convergence |
| C70 | Shared ingest | Shared ingest |
| C71 | Bridge suggestion mutation | Bridge suggestions |
| C72 | Post-write proposal creation | Proposals |
| C73 | Embed-audit dirty marking after ordinary or derived memory spawn | Embed-audit dirty marking |
| C74 | High-drift rising-edge reflex state and optional callback dispatch | Character drift reflex |
| C75 | Ingest-to-query/trace SRG last-ingest-band coupling | SRG last-ingest-band coupling |
| C76 | Ingest-to-Spine geometric-context SRG relational EMA | SRG relational EMA |

The remaining main post-write calls are mapped to their corresponding live
capability above rather than counted twice: reinforcement is C14; checkpoint
creation is C22; compression/deep export is C24; and promotion is C23.

```text
FUNCTIONALITY_MATRIX_DENOMINATOR = FROZEN_I4AFF
TOTAL_ENUMERATED_LIVE_CAPABILITIES = 76
MAPPED_CAPABILITIES = 76
UNMAPPED_LIVE_CAPABILITIES = 0
MATRIX_COMPLETENESS = QUALIFIED_BASELINE_FROZEN_I4AFF
UNMAPPED_LIVE_CAPABILITY = ACTIVATION_BLOCKING
MATRIX_ROW_ABSENT = RETIREMENT_FORBIDDEN
```

### I4 planning denominator

The complete denominator yields these required parity rows before any
post-write native activation. A row can be removed only through a named
selected-profile inapplicability or qualified composition evidence; it cannot
disappear through absence from a later slice.

```text
I4_REQUIRED_PARITY_ROWS =
    Input write gate / provenance
    Memory create
    Embed-audit dirty marking
    Reinforcement
    Motif attach / create
    Motif maintenance / split / merge / live insertion order
    Conflict persistence
    SRG post-write collision / state and overlay-write refusal disposition
    SRG last-ingest-band coupling
    SRG relational EMA
    Character seed/context write composition
    Character drift
    Character drift reflex
    Character gravity
    Role / affect write behavior
    Derived memory
    World / trajectory
    Checkpoint
    Compression / deep-memory export
    Hivemind emission / convergence
    Shared ingest
    Proposals / post-write proposal creation
    Bridge suggestions
    Archive retrieval-count write
    Archive document lifecycle
    Index rebuild
    Promotion operations
    Reference lifecycle
    Environment lifecycle
    Baton lifecycle
    Closure lifecycle
```

Open pre-activation gates remain explicit:

```text
DEEP_RETRIEVAL_PROFILE_GATE = OPEN_PRE_ACTIVATION
MALFORMED_LEGACY_REPRESENTATION_GATE = PRE_ACTIVATION
COLLECTIVE_QUERY_ACTIVATION_GATE = OPEN
ARCHIVE_RECALL_NATIVE_DISPOSITION = REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
SRG_RESTART_PARITY = QUALIFIED_PRIVATE_NATIVE_PUBLIC_DURABLE_BASELINE_ONLY
SRG_QUERY_WRITE_COMPOSITION_PARITY = BLOCKED_PENDING_I4
MOTIF_LIVE_INSERTION_ORDER_PARITY = QUALIFIED_I4B1_PRIMARY_CREATE_PLUS_PRIVATE_I4B2_TRUE_SPLIT_SCOPE
CONFLICT_SYSTEM_PARITY = TRUE_SPLIT_QUALIFIED_BROAD_PRIVATE_READ_ROUNDTRIP_OPEN_I4C_R1
DERIVED_MOOD_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_DRIFT_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_GRAVITY_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_REFLEX_EDGE_PARITY = PASS_PRIVATE_NATIVE_PUBLIC_SCOPE
CHARACTER_WORLD_ORDER_DEPENDENCY = INDEPENDENT_FOR_I4D
CHARACTER_WORLD_COMPOSITION = COMPOSED_PRIVATE_I4E
SHARED_I4D_PARITY = NOT_CLAIMED
SRG_POSTWRITE_COLLISION_PARITY = PASS_PRIVATE_TRANSIENT_SCOPE
WORLD_TRAJECTORY_PARITY = PASS_PRIVATE_EXTERNAL_OWNER_SCOPE
CHECKPOINT_PARITY = PASS_PRIVATE_EXTERNAL_OWNER_SCOPE
HIVEMIND_BROAD_PRIVATE_EXTERNAL_OWNER = RETAINED
HIVEMIND_NEW_SCOPE = EXCLUDED
SHARED_I4E_PARITY = NOT_CLAIMED
I4E_SYSTEMS_MIGRATED = BOUNDED_PRIVATE_ONLY
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
