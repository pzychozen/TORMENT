# TORMENT Memory Substrate — Functionality Preservation Matrix

**Version:** 0.1

**Status:** living I3C preservation artifact. It records current offline
evidence and does not authorize a real-root contact, service start, provider
contact, re-embedding, selected-profile activation, or component retirement.

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
| Memory create | `TormentFabric.ingest` / legacy storage adapter | Legacy graph, identity, external admission | Native public ingest executor | Native public route exists; full behavioral parity not yet qualified | I4 post-write composition | NO |
| Embed-audit dirty marking | Legacy ingest and derived-memory creation audit invalidation | Existing workspace embed_audit.json when present | No qualified native writer | Main ingest/post-write census | Best-effort dirty state occurs after spawn and before motif/flush; it can remain after failed canonical commit | NO |
| Reinforcement | Fabric / legacy post-write adapter | Legacy graph payload and JSONL | Native reinforcement/runtime primitive | `test_substrate_memory_reinforcement.py` | SRG successor and external consumers require I4 | NO |
| Motif attach / create | Legacy motif runtime selected by `TormentFabric.ingest` | Live legacy motif registry | No qualified native post-write successor | Main ingest census | I4 must preserve attachment, creation, and live order | NO |
| Motif maintenance / split / merge | Legacy motif runtime and merge policy | Live registry, merge suggestions, and policy records | No complete native post-write replacement | Main ingest/post-write census | I4 must preserve maintenance and explicit live-order witness | NO |
| Query embedding | Fabric kernel embedder | Configured provider/model lane | Same Fabric owner and admitted native lane validation | I3A/I3B query parity | Representation identity remains selected-profile gate | NO |
| ThinkingController MemoryPlan policy | `ThinkingController.build_memory_plan` + `TormentFabric.query` | Ephemeral policy state; no native storage owner | Same existing cognition owner | Main query census: lane budgets, weights, bounded allocation, and deep-lane interaction | Native storage must not become the MemoryPlan owner | NO |
| Candidate retrieval | `MemoryGraph.search` | Legacy graph embeddings | `NativeMemoryVectorRuntime` through `NativeQualifiedQueryReadModel` | I3B candidate shape, stale, and I3C malformed-vector tests | Qualified snapshot required | NO |
| Malformed legacy representation | Legacy graph/cache may contain non-finite vectors | Legacy representation payload/cache | Qualified native admission requires finite geometry | I3C NaN fixture | `MALFORMED_VECTOR_DISPOSITION = LAWFUL_FAIL_CLOSED_ASYMMETRY`; normalize, disposition, or exclude before migration | NO |
| Decay | `MemoryGraph.search` half-life law | Memory payload timestamps | Native compatible vector projection | I3B normalization/decay differential | No formula consolidation before I3D | NO |
| Query scoring | `TormentFabric.query` / `score_hit` | None beyond qualified input facts | Same Fabric owner | I3A/I3B explain decomposition | One query owner must remain | NO |
| Continuity | Fabric continuity construction | External role/affect state where applicable | Same Fabric owner | A3 differential coverage | Role/affect read dispositions remain external | NO |
| Governance / FILTER-A | Existing cognition/governance path, `filter_llm_facing` | Governance flags/audit and hit payload | No native storage replacement | Main query census: `filter_llm_facing`, `excluded`, `filter_excluded`, `_core_hits_in_count` | Active LLM-facing query chokepoint; preserve owner and filtering semantics | NO |
| Ordering / top-k truncation | MemoryGraph and Fabric stable ordering | Persisted EID/order witnesses | Native vector rows plus existing Fabric merge/sort | I3B plus I3C non-contiguous EID fixture | Live post-write motif order remains I4 | NO |
| Domain routing | Fabric `_rank_domains_from_read_model` | Domain declaration order | Native geometry read adapter | I3B tie/override fixture | No independent native router policy | NO |
| Motif geometry | `MotifRegistry` | Persisted motifs / embeddings | Native motif reader/geometry adapter | I3B geometry differential | Live native insertion order is not yet witnessed | NO |
| Zero-member motifs | Legacy zero-member geometry law | Certified B4C durable lineage | Native zero-member reader/projection | B4C and I3B tests | Certification remains required | NO |
| Active motif context | Motif registry + Fabric presentation | Persisted motif state | Native motif reader plus existing `_active_summary` | I3B active-order parity | Live insertion order is I4-blocking | NO |
| `dominant_thread` | Fabric `dominant_thread` | Active motif context | Same Fabric function | I3B gravity/raw-strength fixture | No new tie policy | NO |
| Character seed/context | Fabric + `assemble_character_context` | External `CharacterStore` | Retained external owner | A3 and I3C absent/read-failure characterization | Absence of `character_context` is not a health signal: disabled Character, absent seed/state, and `CharacterStore` read failure share the same broad fail-soft boundary; write composition is I4 | NO |
| Character drift | Character runtime | External Character state | Retained external owner | Existing native drift/runtime tests; not query-write qualified | I4 | NO |
| Character drift reflex | Fabric rising-edge callback after high-drift measurement | Process-local Fabric high-drift map plus external callback owner | No qualified native callback composition | Main ingest/post-write census | Restart clears the process-local edge map; the first later high-drift measurement may re-fire the callback | NO |
| Character gravity | Character runtime | External Character state | Retained external owner | Existing native gravity/runtime tests; not query-write qualified | I4 | NO |
| Conflict persistence | Conflict writer/policy | External conflict JSONL/evidence | No native writer parity | NOT YET QUALIFIED | BLOCKED_PENDING_I4 | NO |
| Conflict query read | Fabric conflict map | Read-only external conflict evidence | `_ReadOnlyConflictRegistry` | I3B/I3B0 present, absent, malformed evidence tests | Writer/system parity still I4 | NO |
| SRG read | Fabric score/explain source | Legacy payload or native qualified source | `effective_srg_state` | I3B source test; I3C modifier/refusal tests | Full valid state required; optional absence remains lawful | NO |
| SRG query mutation / breathing | Fabric historical nested breathing gate | Live legacy payload / native process overlay | Native process-local overlay | I3C lifecycle characterization | Legacy live-payload mutation is lost after restart without same-entity write; unrelated flush does not persist it; later same-entity write serializes it. Native overlay is process-local only. Restart/write successor parity BLOCKED_PENDING_I4 | NO |
| SRG last-ingest-band coupling | Fabric ingest-to-query/trace same-band resonance | Process-local Fabric state keyed by workspace_id and agent_id | No qualified native cross-route owner | Main ingest/query/trace census | Ingest stores R_band; query and trace apply the existing 1.08 multiplier only when the same agent's last band matches; restart clears it | NO |
| SRG relational EMA | Fabric ingest-to-Spine geometric-context coupling | Process-local Fabric EMA keyed by workspace_id and agent_id | No qualified native cross-route owner | Main ingest/Spine census | First ingest seeds L_amplitude; later ingests use 0.8 previous + 0.2 new; restart clears it | NO |
| SRG error-handler failure disposition | Fabric breathing error handler | No separate durable owner | Same handler; I3C defect repair | I3C first-hit evolution-failure characterization | `SRG_ERROR_HANDLER_LATENT_DEFECT_FIXED = YES`; the prior first-hit `UnboundLocalError` / later-hit stale-EID diagnostic behavior is not retained | NO |
| SRG post-write collision / state | Legacy post-write adapter and SRG runtime | Legacy payload / collision effects | No qualified native write successor | Main ingest/post-write census | I4 must disposition overlay-write refusal and durable successor composition | NO |
| World / trajectory | Legacy world and post-write runtime | Legacy trajectory evidence | Native world/post-write primitives | Partial unit evidence only | I4 general post-write | NO |
| Checkpoint | Checkpoint subsystem | External checkpoint files | No query-side native replacement | NOT YET QUALIFIED | I4 / separate route classification | NO |
| Bridge peek | Fabric `_query_shared_lane` | Existing bridge registry and domain policies | Same query owner over qualified shared reads | Main query census: `bridge_peek_requires_approval`, approved-or-confidence `>= 0.65`, `via_bridge` marking | Query-side retrieval is distinct from bridge suggestion mutation | NO |
| Bridge suggestions | Bridge policy / post-write behavior | External bridge registry | Existing read-only bridge path | Query bridge read retained by I3B | Suggestion mutation is I4 | NO |
| Bridge registry inspection / decision | Existing bridge registry routes | External bridge records | No native public route parity | I2/public-service census | Root-native path remains refused until route parity | NO |
| Hivemind / collective context | Collective presentation owner | External collective field | No native read adapter | I3B0 refusal test | REFUSE_WHEN_APPLICABLE; activation gate OPEN | NO |
| Archive recall | `/retrieve` composite assembler | External archive store | No native composite adapter | I3B0 refusal test | REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY | NO |
| Archive retrieval-count write | Archive promotion/read accounting | External archive counter | No native adapter | Not reached after archive refusal | BLOCKING composite gate | NO |
| Shared ingest | Fabric shared ingest / proposal policy | Shared graph and external policy | Native public ingest route | Storage path exists; system parity NOT YET QUALIFIED | I4 post-write and conflict composition | NO |
| Proposals | Proposal orchestration | External proposal records / receipts | Native authorized proposal primitives | Existing substrate tests; no full query/system parity | I4 route composition | NO |
| Role / affect | RoleStore and affect helpers | External role file / affect history | Native read-only/non-materializing disposition | I3B0 no-materialization tests | External write behavior remains I4 | NO |
| Derived memory | Derived-memory runtime | Derived/external state | Native derived runtime primitives | Partial substrate evidence | I4 post-write composition | NO |
| Compression / deep-memory export | Legacy compression post-write runtime | Deep-memory files and compressed source metadata | No qualified native post-write path | Main ingest/post-write and public-service census | Deep export/compression control remains pre-activation gated | NO |
| Deep memory / spirit return | Legacy `_query_deep_lane` and spirit-return enrichers | Per-agent deep-memory store | NATIVE SUPPORT = NO | Main query/service census: spirit modes `resonance`, `surfacing`, `recollection`; `_is_deep` classification; Character voice recommendations can consume spirit hits | When `TORMENT_COMPRESS_ENABLE` / deep retrieval applies, activation is refused; `DEEP_RETRIEVAL_PROFILE_GATE = OPEN_PRE_ACTIVATION` | NO |
| Hivemind emission / convergence | Legacy post-write adapter / collective field | External collective packets, events, and proposals | No qualified native write adapter | Main ingest/post-write census | I4 collective emission/convergence parity; query remains refuse-when-applicable | NO |
| Failure dispositions | Each current semantic owner | Owner-specific files/state | Qualified read refusal and existing fail-soft paths | I3B snapshot/conflict; I3C SRG/Character/malformed vector | Preserve per-surface behavior; no universal normalization | NO |
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
MOTIF_LIVE_INSERTION_ORDER = BLOCKED_PENDING_I4_ORDER_WITNESS
CHARACTER_QUERY_READ = PASS
CHARACTER_WRITE_COMPOSITION = BLOCKED_PENDING_I4
CONFLICT_QUERY_READ = PASS
CONFLICT_SYSTEM = BLOCKED_PENDING_I4
COLLECTIVE = REFUSE_WHEN_APPLICABLE
ARCHIVE = REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
LEGACY_QUERY_READER_RETIREMENT = NOT_AUTHORIZED
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

The matrix distinguishes a query read that retains an external owner from a
future write route that would have to preserve the same owner. Query parity
does not authorize that write route.

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
SRG_RESTART_PARITY = BLOCKED_PENDING_I4
SRG_QUERY_WRITE_COMPOSITION_PARITY = BLOCKED_PENDING_I4
MOTIF_LIVE_INSERTION_ORDER_PARITY = BLOCKED_PENDING_I4_ORDER_WITNESS
CONFLICT_SYSTEM_PARITY = BLOCKED_PENDING_I4
CHARACTER_WRITE_COMPOSITION = BLOCKED_PENDING_I4
```
