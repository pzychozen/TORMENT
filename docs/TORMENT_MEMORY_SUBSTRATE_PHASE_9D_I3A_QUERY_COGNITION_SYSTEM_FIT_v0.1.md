# TORMENT Phase 9D-I3A - Query Cognition System-Fit

Status: PROPOSED / NOT FROZEN - offline archaeology, 2026-09-03

## Scope and authority

This record traces MAIN TORMENT COGNITION only. It neither reads nor classifies an unrelated repository-resident cognitive function. Repository co-location is not evidence of a runtime link.

    MAIN_TORMENT_QUERY_COGNITION = IN_SCOPE / ACTIVE TORMENT SEMANTIC OWNER
    SECOND_REPOSITORY_COGNITIVE_FUNCTION = OUT_OF_SCOPE / NOT INSPECTED
    I3A_PRODUCTION_CODE_CHANGES = 0 (historical archaeology boundary)
    I3A_TEST_CODE_CHANGES = 0 (historical archaeology boundary)
    REAL_ROOT_CONTACT = NO
    SERVICE_START = NO
    PROVIDER_CONTACT = NO

The frozen target is one request-cognitive workspace and one active TORMENT query cognition implementation. The representation contract is st / BAAI/bge-small-en-v1.5 / 384 dimensions. Dimension alone is not representation proof.

## 1. One true main query cognition owner

The semantic/query owner is TormentFabric.query, assisted at the HTTP boundary by main ThinkingController when /agent/query advisory thinking is enabled. ThinkingController deterministically derives a MemoryPlan of lane budgets and weights; it does not replace retrieval or ranking. The service route catches a thinking failure and passes no plan, preserving flat retrieval.

Native call chain:

    POST /agent/query
      -> optional ThinkingController.think(...).memory_plan
      -> selected public runtime .query(...)
      -> NativePublicTormentRuntime.query
         -> preflight_spine_operation(query_memory, fast)
         -> _prepare_native_agent(workspace, agent)
         -> _workspace_view(workspace)
         -> NativeProductionResourceOwner.open_query_context(embedder)
         -> TormentFabric.query(
              _native_public=True,
              _qualification_read_model=NativeProductionQueryContext,
              _native_workspace_view=NativePublicWorkspaceView,
              _native_identity=existing AgentIdentity)
         -> result dictionary

/retrieve is a composite consumer, not a second core query algorithm. It calls the same selected public .query, then may add archive/reference material and run the retrieval assembler. Its archive retrieval-count update is independently mutable external/archive behavior, not core query parity.

Legacy reaches the same TormentFabric.query, but gets Workspace and AgentIdentity through get_workspace and create_agent, then creates LegacyQualifiedQueryReadModel. Native public mode supplies all three qualified arguments and query refuses their absence before it can call either legacy materializer.

    MAIN_QUERY_COGNITION_OWNER =
      app optional ThinkingController memory-plan policy + TormentFabric.query

    NATIVE_QUERY_ATTACHMENT_SEAM =
      NativePublicTormentRuntime.query ->
      NativeProductionResourceOwner.open_query_context ->
      QualifiedQueryReadModel supplied to TormentFabric.query

This is the existing storage seam. It is below main query scoring and above native durable/vector readers. It is not a place to create a root query algorithm, a native cognition fork, or a simplified query path.

## 2. Query-stage ownership map

| Stage | Current owner and operation | Classification | Native disposition |
|---|---|---|---|
| Request plan | ThinkingController.build_memory_plan derives deterministic budgets/weights | Semantic policy owner | Existing main owner; pass plan unchanged |
| Root/scope resolution | native facade, production owner recovery, admitted lookup, inert view | Routing / identity adapter | Existing, root-qualified, fail-closed |
| Existing agent identity / kernel context | prepare_native_cognition_agent | External durable owner plus process-local cognition state | Existing identity only; no graph/identity creation |
| Query embedding | kernel.embedder.embed(query_text) | Cognition / mathematical owner | Same configured embedder; dimension checked |
| Domain rank | TormentFabric._rank_domains_from_read_model | Cognition / mathematical owner | Same owner; native geometry adapter |
| Private/shared candidates | QualifiedQueryLane.search | Storage read adapter | Legacy MemoryGraph; native vector runtime |
| Bridge peek | bridge policy and bridge reader | Semantic policy + external durable owner | Read-only external projection |
| Motif geometry/active motifs | query orchestration plus motif read model | Cognition plus storage adapter | Existing geometry/read adapters |
| Conflict state | _build_conflict_map | External durable owner + semantic policy | Read-only retained external logs |
| Per-hit scoring | score_hit, continuity, motif/conflict/SRG/provenance/plan adjustments | Cognition / mathematical owner | Must remain one Fabric implementation |
| Governance exclusion | filter_llm_facing | Semantic policy owner | Same post-rank call |
| Character context | assemble_character_context and CharacterStore reads | External Character owner + semantic adapter | Keep external, not SQLite |
| Role/affect/resonance | role/affect stores and SRG state | Policy/external owner/read-side mutation | Preserve exact behavior and gates |
| Result assembly | TormentFabric.query dictionary; /retrieve assembler | Provenance / presentation | Same query shape; composite separately qualified |

## 3. Read-model contracts and current native capabilities

TormentFabric.query creates qemb, requires its dimension to equal ws.embed_dim, and ranks at most two shared domains. An explicit domain is prepended and de-duplicated before the two-domain cap. It recalls the private lane, ranked shared lanes, and qualifying bridge-peek lanes. Legacy deep retrieval is a separate gap-fill lane. Native qualification refuses an enabled compression/deep profile rather than mix native core candidates with legacy deep candidates.

Each lane search receives query text, top_k, user_id, min_score, and type_filter. Lane retrieval intentionally embeds the text in its own storage adapter as MemoryGraph.search historically did. qemb is used for domain ranking, motif alignment, and legacy deep retrieval. A future port must preserve this call structure unless a separate parity decision proves it irrelevant.

MemoryGraph.search yields flattened hit dictionaries: eid, decayed score, raw_score, decay_factor, summary, type, strength, confidence, step, ts, and flexible payload fields. Its EID is lane-local. Empty query/no usable vector is a valid empty result; invalid individual vectors are skipped. It normalizes float32 vectors, pads/truncates mismatch, applies half-life decay after candidate cosine selection, then re-sorts by decayed score.

LegacyQualifiedQueryReadModel adds a non-public QualifiedQueryHit. It proves workspace_id, scope, agent_id or domain_id, and eid before the hit enters main cognition while returning an unchanged compatibility dictionary. It projects current motif membership from its registry.

| Query requirement | Native capability now | Disposition |
|---|---|---|
| Private lane | recovered admitted private scope -> native qualified lane | Existing native adapter |
| Shared lane | recovered admitted shared domain -> native qualified lane | Existing native adapter |
| Candidate compatibility fields | NativeMemoryVectorRuntime current projection | Existing native adapter |
| Candidate identity | QualifiedQueryHit identity plus object/revision witness | Direct equivalent, stronger than raw EID |
| Current motif membership | relationship reader by member object identity | Direct equivalent |
| Domain centroid | native motif geometry adapter/reader | Existing native adapter |
| Active motif presentation | native read models -> active summary | Existing native adapter |
| SRG baseline / overlay | effective_srg_state and replace_srg_state | Available, conditional writeback gate |
| Conflict/bridge evidence | retained read-only external projections | External owners remain external |
| Character/role/affect | current external stores | External owners remain external |
| Legacy deep store | no native deep lane | Intentionally unsupported native profile |

The native vector reader requires exact provider, model, and dimension equality with its admitted lane. It snapshots current rows, retains object/revision witness, uses float32 vectors, and returns empty instead of mixing a stale vector snapshot with a new payload.

## 4. Preserved main scoring and semantic contributions

For every merged hit, the single owner computes a lane score already half-life decayed, then score_hit with strength, recency, motif alignment, contradiction risk, and continuity bonus. It then applies reinforcement logarithmic boost, SRG multipliers, collective/tool discounts, and bounded MemoryPlan lane weight.

score_hit owns the current formula:
sim * (1 + .35*strength + .10*recency_bonus + .20*motif_alignment)
- .30*contradiction_risk + type_bonus,
where recency_bonus is 1/(1+max(0, days)).

This formula, continuity formulas, reinforcement, SRG, motif equations, and Character equations are not migration adapters and must not change.

Motif membership is domain-qualified. A hit with no membership may select the best qualified motif centroid at cosine >= .55. This is a query semantic threshold. Active motifs feed response presentation and dominant_thread; centroids also contribute to domain routing and per-hit alignment.

ZERO_MEMBER != MEANINGLESS. A certified B4C native zero-member baseline retains centroid, strength, stability, label, and runtime ID. It participates in geometry, domain-centroid weighting, active-motif gravity, and fallback alignment without a fabricated member. Radius is 0.0 with no member vector, matching the existing helper. An unproved zero-member native motif is refused.

Conflict keys are scope, qualifier, and eid within the query workspace. Only a shared canonical hit matched to an open conflict gets conflict metadata/penalty. I3A identified a correction requirement: genuine missing files are a lawful empty read, but unreadable or malformed native conflict evidence must be a structured qualified-read refusal rather than silently removing conflict penalties. I3B0 now carries that lower-level refusal through `_build_conflict_map` and translates it only at the native public boundary. Conflict writer/composition parity is not yet qualified and gates future writes.

Character runs after scoring, filtering, and truncation. It reads seed/state, adds tier metadata and character_weighted_score, and returns seed preamble, tier breakdown, and drift recommendations. It does not re-rank or change final_score. Role context is presentation/continuity-debug only and does not directly rank. Native role load uses create_if_missing=False. Affect classification is deterministic and pure; retained affect drift history can influence the mood-spiral continuity penalty.

SRG scoring reads flattened srg first and then nested payload. It can multiply same-band by 1.08, crystal by 1.05, and heartbeat-A by 1.03. Normal lane hits are flattened, but breathing writeback requires nested payload.srg. Thus ordinary current MemoryGraph/native-vector lane hits score SRG but do not activate breathing writeback. A specially shaped nested payload makes legacy mutate only the live graph entity and native set a process-local overlay keyed by core, lane namespace, eid, and current revision. Native query itself writes no SQLite successor. Later same-process query can observe the overlay; durability requires a separately authorized exact-successor materialization. This is a composition gate, not a math change.

## 5. Qualified identity, ordering, and numeric parity

| State/read | Required identity | Evidence |
|---|---|---|
| Fabric agent state, kernel context, deep-store map | workspace_id, agent_id via _agent_key | Existing composite key |
| Candidate / anchor | workspace_id, scope, qualifier, eid | QueryMemoryIdentity fails closed |
| Native candidate | qualified identity + object_id + revision_id | QualifiedQueryHit |
| Motif | workspace_id, domain_id, motif_id; native semantic scope UUID | Query motif identities |
| Conflict | workspace_id, scope, qualifier, eid | workspace filter + qualified map |
| SRG overlay | core_id, lane legacy-source namespace, eid, revision | exact-current process witness |
| Workspace view | admitted workspace_id, revalidated owner | no singleton fallback |

workspace_A/private/agent_7 and workspace_B/private/agent_7, plus shared research in A and B, cannot collide in Fabric state or qualified read identity. Current native owner recovers one admitted workspace runtime at a time: a mismatch is refused, never redirected. Concurrent independently admitted workspaces need an owner/routing map above this seam, not root-global EIDs or new query math.

Ordering must be tested exactly:

- Domains use stable descending score order, preserving explicit admitted domain order on equal scores. No EID fallback.
- Candidates merge private, ranked shared, bridge peeks, then legacy deep. Lane top-k uses float32 plus argpartition/argsort; no declared semantic EID tie-break.
- Final sort is stable descending final_score. Equal scores retain merged-lane/candidate order. Character does not reorder; governance filtering retains survivor order.
- Active motifs sort descending strength plus gravity then last_active_ts. dominant_thread uses strict greater-than and retains first in domain iteration order on ties.
- Bridges sort descending confidence and conflicts descending created time; neither declares a tertiary tie-break.

Native active motif input is runtime-ID ordered whereas legacy registry iteration is map order. Persisted legacy saves often have sorted JSON keys, but that is not semantic proof. Tie/order fixtures are a gate.

Both vector runtimes coerce to float32, pad/truncate to dimension, and normalize with norm + 1e-12. Candidate cosine is normalized float32 dot product. Half-life is 2 ** (-age_days / half_life), floor .03, anchored to last_reinforced_ts then created_ts. Final score arithmetic is mostly Python float. No query-side quantization is selected; native compatibility vectors are qualified raw float32 before the same normalization.

## 6. Formula duplicate map - no I3A consolidation

| Class | Owner / active calls | Duplicate or parallel implementation | Required test | Retirement gate |
|---|---|---|---|---|
| Domain cosine and stable order | TormentFabric._rank_domains_from_read_model, active legacy/native | historical DomainRouter; NativeDomainRouter constructed but not called by this query path | test_p9d_i3_domain_rank_order_parity: ties, zero centroid, explicit override | Keep one Fabric rank call; census then delegate/retire dormant copies |
| Vector normalization + half-life | MemoryGraph.search and NativeMemoryVectorRuntime._search_vector | parallel normalize and half-life helpers | test_p9d_i3_vector_normalization_and_decay_parity: empty/short/long, zero norm, timestamps/floor/ties | Share helper only after byte-level numeric and representation witness proof |
| Motif gravity/density, active order, centroid weighting gates | MotifRegistry.active/domain_centroid; native active summary and motif reader centroid | legacy policy wrapper vs CURRENT_MOTIF_DECISION_POLICY and repeated weighted-centroid loop | test_p9d_i3_motif_geometry_active_order_parity: B4C zero member, equal gravity/timestamp, dimension skips | Consolidate only after legacy/native geometry and order proof |

No duplicate authorizes numerical drift. Consolidation is downstream of native read parity.

## 7. Read-side mutation and failure disposition

| Condition | Current behavior | Native requirement |
|---|---|---|
| Legacy entry | may create workspace/agent/graph | forbidden; I2 arguments prevent it |
| Native agent preparation | process-local kernel state/context; Character modulation may embed existing seed on first prepare | only existing identity, no durable memory creation |
| Vector/index cache | legacy RAM matrix or native request snapshot/cache | process-local only |
| SRG breathing | normal flattened hit inactive; special nested hit mutates graph or overlay | preserve gate; successor persistence is post-write work |
| Affect drift read | helper historically creates agent directory before reading | I3B0 native read passes a non-materializing path disposition |
| Role read | legacy may create default | I3B0 native read-only load; missing role is an in-memory default only |
| Collective result context | optional field constructor creates legacy collective directory before reading | I3B0 refuses native query while collective is applicable; read-only adapter remains a gate |
| /retrieve archive promotion | optional archive read then durable retrieval count | I3B0 refuses native retrieval while archive recall is applicable; non-archive profile remains available |
| Root/profile/scope/identity stale | public owner refuses before read | fail closed, no fallback |
| Embedding/geometry dimension mismatch | explicit refusal | preserve exact refusal |
| Missing lane/vector/empty candidates | valid empty result | preserve |
| Character/affect/SRG per-hit errors | local fail-soft degradation | preserve |
| Conflict unreadable/malformed | historical fail-soft missing contribution | I3B0 structured qualified-read refusal; genuine absence remains empty |
| Governance non-authoritative deep wrapper | LLM filter fails loud | never return wrapper |

random_chance exists in Fabric but has no call from the traced query path. ThinkingController, affect, ranking, and native/legacy read adapters have no query RNG call.

    QUERY_COGNITION_STOCHASTIC_PATHS = NONE_FOUND

## 8. One-cognition plan, retirement, and slices

The smallest correct shape already exists:

    MAIN TORMENT cognition (ThinkingController policy + TormentFabric.query)
        -> QualifiedQueryReadModel port
           -> LegacyQualifiedQueryReadModel / MemoryGraph
           -> NativeProductionQueryContext / NativeQualifiedQueryReadModel
              -> qualified native vector, motif, and SRG adapters

The port must return compatibility fields while carrying non-public qualified identity, membership, and current revision witnesses. Routing belongs in native facade/production owner; storage in the read model. No adapter may reimplement score_hit, continuity, motif alignment, conflict policy, Character, SRG, or final ordering.

| Legacy component | Native replacement | Parity/retirement gate | Eventual survivor |
|---|---|---|---|
| LegacyQualifiedQueryReadModel | NativeProductionQueryContext / NativeQualifiedQueryReadModel | lane, identity, vector, motif, order, failure tests | selected adapter behind read-model port |
| MemoryGraph.search lane | NativeMemoryVectorRuntime | normalization/decay, shape, tie/empty/stale tests | native vector runtime under selected root |
| MotifRegistry geometry/active reader | native motif geometry/runtime reader | zero member, gravity, centroid, active order | native motif reader |
| Public legacy delegation | explicit NativePublicTormentRuntime.query | I2 no fallthrough/materialization test | explicit public route |
| conflict/bridge/Character/role/affect stores | retained external owners | truthful source + read/write composition qualification | external owners, not SQLite core |

Recommended implementation slices:

1. I3B - native query read-port hardening and fixtures. Keep TormentFabric.query owner and add no math. Prove compatibility hit shape, qualified identity, order, zero-member motifs, float32 normalization/decay, empty/refusal, and no materialization. Decide/contain collective before enabling native query.
2. I3C - root-qualified multi-workspace and external composition parity. Use two synthetic qualified roots/workspaces for A/B isolation, conflicts, Character/role/affect, SRG overlay lifecycle, and external failure behavior. Archive/reference composite surfaces need their own classification.
3. I3D - formula duplicate consolidation and retirement decision after I3B/C. Census call sites, then delegate/retain copies with fixtures. Do not delete only because a core test passes.

    QUERY_COGNITION_FORMULA_CHANGES_REQUIRED = NO
    ONE_COGNITION_IMPLEMENTATION_FEASIBLE = YES
    I3_IMPLEMENTATION_READY = YES, SUBJECT TO EXPLICIT GATES

## 9. Required parity gates

- Candidate shape, identity failure, vector precision, decay, order/tie, zero/empty, and stale-currentness parity.
- Domain, motif gravity/centroid, active motif, fallback alignment, bridge, conflict, final score, governance filter, and provenance parity.
- Workspace-A/B duplicate agent/domain fixtures proving qualified keys and refusal, never accidental selection.
- Character seed/state, role no-materialization, affect drift, and external failure tests.
- SRG score/explain parity plus a declared special-shape breathing, overlay survival/restart, and successor-materialization decision.
- Collective must be disabled/refused or supplied by a read-only external adapter. /retrieve archive/reference and archive-promotion mutation need separate native classification.
- Legacy query reader retirement only after all relevant gates pass; fallback fence, query mathematics, and external owners remain.

## 10. Accepted adversarial-review corrections and I3B0 disposition

The adversarial review confirmed the main query owner and one-cognition target,
but corrected the I3A implementation order.  I3B0 must fence downstream
materializers before I3B can qualify ordering or candidate parity.

```
MAIN_QUERY_COGNITION_OWNER = CONFIRMED
ONE_COGNITION_IMPLEMENTATION_FEASIBLE = YES

READ_MODEL_ORDERING_CONTRACT =
    MUST_PRESERVE_EXISTING_OBSERVABLE_ORDER
NEW_TIE_BREAK_POLICY = NO
FLOAT_REDUCTION_ORDER = PARITY_LOAD_BEARING

COLLECTIVE_QUERY_GATE = OPEN
ARCHIVE_RECALL_GATE = OPEN
CONFLICT_FAILURE_DISPOSITION = PASS_AFTER_I3B0_CORRECTION

SRG_MUTATION = COMPOSITION_GATE
B3A_B3B_NEW_I3_DEPENDENCY = NO

NATIVE_QUERY_QUALIFICATION_DISPOSITION =
    SAME_AS_NATIVE_PUBLIC_READ_DISPOSITION
```

I3B0 does not alter query score, continuity, motif, Character, SRG,
reinforcement, or ordering mathematics.  It freezes the existing observable
ordering witnesses: legacy lane row order, declared/insertion domain order,
legacy motif-registry iteration order, and stable merge order.  It does not
introduce EID, motif-ID, or runtime-ID tie policies.  Native motif centroid
float-reduction order is semantic evidence for I3B; if the native substrate
cannot preserve the legacy semantic iteration order, query parity is blocked.

The native vector stale-snapshot `[]` ambiguity remains a named blocking I3B
item.  I3B must make stale currentness distinguishable from a valid empty lane
without adding a retry policy or changing cognition.

P9D-I3B0 also supersedes the former absolute Brainvision-read token for this
uncommitted record.  A documented search-snippet-only exposure occurred; no
code, source, cognition, or finding was used.

```
BRAINVISION_FILES_READ = NOT_CERTIFIABLE_AS_ZERO
BRAINVISION_SEARCH_SNIPPETS_EXPOSED = YES
BRAINVISION_DOCUMENTATION_MENTION_OPENED = YES
BRAINVISION_CODE_OPENED = NO
BRAINVISION_CODE_INSPECTED = NO
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_INFORMATION_USED_FOR_I3A_I3B0 = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
```
