# 7G5E4E-A0 query integration preflight

## Scope and frozen production state

This archaeology and characterization record was made against local `main` at `2e7ce1f8a7d35fd0915fb7409a650e6a1ff506e4`. It introduces no production selector, activation path, dual read/write, SQL cosine path, or native query implementation.

```text
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
PRODUCTION_SELECTOR_ADDED = NO
CUTOVER_OPENED = NO
KERNEL_CHANGE_REQUIRED = NO
```

Inspected native qualification components: `NativeMemoryVectorRuntime`, `NativePostWriteMemoryAccess`, `NativeMotifGeometryAdapter`, `NativeMotifRuntimeReader`, the E4C recovered multi-scope runtime, and the B1 external `BridgeRegistry` geometry boundary. Inspected legacy consumers: `TormentFabric.query()`, `/agent/query`, `/retrieve`, `DomainRouter`, `MemoryGraph.search`, `BridgeRegistry`, scoring/continuity, Character, SRG, and governance filtering.

Native qualification remains in `torment-substrate` (SQLite 3.53.4). Ordinary `torment` remains native-ineligible and was not changed.

## Public query and retrieve paths

### `/agent/query`

`QueryReq` accepts workspace, agent, text, `top_k`, optional requested domain, bridge-peek, explain, and continuity-debug flags. With `TORMENT_THINKING_ADVISORY=1` (the default), it first asks `ThinkingController` for a `MemoryPlan`; errors fall back to no plan. It passes only `top_k_by_lane` and `weight_by_lane` to `TormentFabric.query()`. `MemoryPlan.retrieve_*` booleans are not passed to Fabric.

### `/retrieve`

`/retrieve` is distinct assembly, but its core-memory read is `fabric.query(...)` with no plan, bridge peek, or explain. It then optionally retrieves archive chunks, filters archive hits at the LLM-facing governance surface, resolves explicit active references, and calls `assemble_context`. Its hard order is identity, reference, relational, situational, archive. It does not replace Fabric core ranking.

## Exact `TormentFabric.query()` order

```text
query_text
  -> create/get workspace and agent
  -> kernel.embedder.embed(query_text)
  -> workspace dimension check
  -> DomainRouter.rank_domains(query embedding, top_k=2)
  -> requested-domain reordering, if supplied
  -> MemoryPlan lane budgets
  -> private MemoryGraph.search(query_text)
  -> selected shared-domain MemoryGraph.search(query_text), in domain order
  -> optional bridge-peek MemoryGraph.search(query_text), in bridge-domain order
  -> canonical step
  -> optional deep-store query using the first query embedding
  -> concatenate private + shared + deep candidates
  -> hard memory-class exclusion
  -> score/modifier pass
  -> stable descending final-score sort and truncate to top_k
  -> LLM-facing non_shareable filter (no refill after exclusion)
  -> optional continuity debug construction
  -> bridge/role/embed/optional Character/optional collective context
  -> public result dictionary
```

Fabric embeds before individual lanes check candidates. `MemoryGraph.search` trims and returns immediately for blank text, so a blank Fabric query makes the router embedding call but no lane embedding calls. Deep does not embed again.

## Embedder-call law

The current law is repeated embedding, not shared-vector optimization:

```text
one Fabric/kernel embedder call for routing
+ one call in each non-empty-text private MemoryGraph.search invocation
+ one call in each non-empty-text selected shared MemoryGraph.search invocation
+ one call in each non-empty-text bridge-peek MemoryGraph.search invocation
+ zero calls in _query_deep_lane (it receives Fabric's first vector)
```

Ordinary Fabric graphs are constructed with the Fabric kernel embedder, so their provider/model/dimension are the configured lane unless a caller deliberately replaces one. The repeated lane text is stripped; Fabric routing receives original `query_text`. The provider calls are externally observable and must remain so.

`tests/test_7g5e4e_query_integration_preflight.py` locks private + two selected shared + approved bridge peek: one routing call and four lane calls, with the same text. `NativeMemoryVectorRuntime.search` already owns a matching lane embedder call. A native public seam must call `runtime.search(query_text)`, not Fabric-vector `search_by_embedding`.

```text
QUERY_EMBEDDER_CALL_BEHAVIOR_CHANGED = NO
```

## Domain routing and requested-domain law

`DomainRouter.rank_domains` iterates its insertion-ordered domain-to-`MotifRegistry` map. Each domain gets its strength-and-gravity-weighted centroid; a zero centroid scores `0.0`, otherwise it scores cosine with the Fabric query vector. It stable-sorts descending, takes two, and has no threshold. Equal scores retain workspace domain insertion order. Native routing must use explicit admitted-domain order, never SQLite row order.

If `domain_id` is supplied, Fabric makes it first, retains router order for a different routed domain, then truncates to two:

```text
[requested_domain] + [router_domain for router_domain in ranked if different]
```

The caller therefore gets requested-domain-first then router order, not caller-list, lexical, or score order alone. An unknown requested domain is not prevalidated and fails when the graph or motif registry is addressed.

```text
DOMAIN_ROUTING_MATH_CHANGED = NO
```

## MemoryPlan and budgets

Without a plan, Fabric uses `top_k` for private core and for **each** selected shared domain. With a plan, `core`, `relational`, and `deep` are integer-clamped to `[0, 2 * top_k]`. Core caps private, relational caps each primary shared domain, and bridge peek uses `max(2, top_k // 2)` per peek domain independently.

```text
remaining   = max(0, top_k - len(private_hits) - len(shared_hits))
deep_budget = min(plan.deep, remaining) if "deep" is present else remaining
```

Thus deep is a global gap filler. Explicit `deep: 0` declines it; absent deep preserves baseline gap fill. `archive` and `collective` plan budgets have no Fabric query lane; archive is separate `/retrieve`. When a weight map is present, lane weights apply after scoring: core/private, relational/shared, deep/spirit return. Collective provenance has its own discount. Weight clamps to `[0.1, 2.0]`.

The advisory controller normally builds core 6; relational 4 only when memory/social context asks; deep 3 only in reflective or identity-sensitive mode; archive 4 only behind its separate flag; collective 2 only for qualified contextual intent. Default-off shaping can alter already-enabled budgets/weights before Fabric receives the maps.

## Legacy private and shared retrieval laws

### Private `MemoryGraph.search`

Private search calls `private_graph.search(query_text, top_k, user_id=agent_id)`. It trims and embeds inside `MemoryGraph.search`; cached mode rebuilds a float32 row-normalized matrix ordered by ascending EID, calculates `matrix @ normalized_query`, selects raw-score top-k with `np.argsort` or `np.argpartition` then `np.argsort`, applies user/type/min-score filters, applies half-life decay, then stable-sorts effective score descending. The NumPy candidate behavior is the tie law; no independent secondary tie-break is promised.

Decay uses `last_reinforced_ts`, otherwise `created_ts`, with floor `0.03`. Hits begin with EID, effective/raw score, decay factor, summary/type/strength/confidence/step/ts and then flatten flexible payload.

### Shared primary domains

Fabric searches every selected shared graph in selected-domain order with `user_id=None` and the relational cap. There is no additional agent filter. Correct shared payloads carry flattened `workspace_id`, `scope="shared"`, and source `domain_id`; later conflict, SRG, and result consumers rely on them. EIDs remain graph-local.

### Bridge peek

When requested, `BridgeRegistry.relevant_to_domains(primary_domains, top_k=12)` returns confidence-descending bridges with stable external-file ties. Rejected bridges are skipped. If any primary domain requires approval, only approved bridges pass; otherwise unapproved needs confidence at least `0.65`. Fabric takes the opposite endpoint domain, avoids primary/already-selected peek domains, stops at two, searches each existing peek graph in that order, sets `via_bridge=True` and `bridge_domain=<domain>`, and appends those hits after primary shared hits.

Query-time bridge routing reads endpoints, status, and confidence; it does not resolve motifs. `BridgeRegistry` remains external owner of endpoint/reverse-endpoint duplicate suppression and workflow files. B1's `NativeMotifGeometryAdapter` uses admitted domains plus explicit motif alias namespace and semantic scope; a native query adapter must retain that alias-safe boundary.

### Deep memory

`_query_deep_lane` runs only if `_compress_enable` is true and the calculated budget is positive. It obtains an external persisted deep store, queries it with Fabric's first embedding, requires the source EID to still be present in private `MemoryGraph.entities`, enriches spirit-return data, and marks hits `scope="deep"`. Any error is swallowed and returns no deep hit. This is not a native SQLite query path.

The qualified native shared profile freezes compression/deep disabled, and ordinary Fabric defaults `TORMENT_COMPRESS_ENABLE=0`. Legacy Fabric can enable deep independently through that environment gate, but this profile is unqualified for native shared operation and must be refused before native query work tries to use it.

```text
DEFAULT_QUERY_DEEP_PROFILE = disabled
```

## Motif contribution and identity finding

The router uses domain geometry. After retrieval Fabric gets `active(top_k=6)` from each primary `MotifRegistry`; active order is descending `(strength + gravity_bonus, last_active_ts)`. Returned active summaries contain label, strength, stability, density, gravity, radius, and member count.

For scoring, Fabric builds centroids from all primary registries. Stored hit `motifs` are used; a hit without motifs receives the best query-centroid ID at similarity at least `0.55`. `motif_alignment` is maximum query/centroid cosine and enters `score_hit`.

There is a local identity contradiction: the centroid map is `Dict[str, ndarray]` keyed only by `motif_id`, not domain plus motif identity. A same-string ID in two selected domains overwrites the earlier centroid. Bridge-peek domains are absent from this map. The A0 characterization test records the overwrite. This does not authorize making bridge aliases globally unique; the corrected reference must use qualified motif identity.

## Conflict, continuity, reinforcement, SRG, provenance, and governance

### Conflicts

Fabric reads each selected primary domain's external `ConflictRegistry` for up to 500 open rows. Its key is already qualified: `(origin_scope, private agent_id or shared domain_id, eid)`. Conflicts do not exclude candidates. A matching canonical shared hit gets status, IDs, and penalty; unless the query asks for contested material, contradiction risk becomes at least half the maximum conflict score. Bridge-peek domains are not read into the map unless primary.

### Continuity

One `ContinuityContext` contains the querying agent, canonical kernel step (with private-graph fallback), affect signals, private affect-state spiral count, and anchor top-k set. Per hit it adds self-thread, identity-anchor, recent private-thread, affect-match, mood-drift, and possible mood-spiral adjustments before reinforcement/SRG/discounts/weights.

`_resolve_srg_writeback_target` correctly validates workspace, scope, private agent or shared domain, graph, entity, and entity payload before resolving an SRG target. It is not a bare-EID graph probe.

However, `anchor_full_boost_eids` is `set[int]`. A private qualifying anchor and shared identity anchor with equal graph-local EID collide, granting the shared hit the private hit's full-anchor treatment. The characterization test demonstrates it. This is score-modifier leakage, not final-result collapse.

### Reinforcement

Search already includes decay from the current effective payload. Query then adds `TORMENT_REINFORCE_BOOST * ln(1 + reinforcement_count)` (default `0.04`) when count is positive. Shared source writes never reinforce under the frozen shared-write contract, but query does not separately exclude a shared hit that happens to carry a count.

### SRG

When `_srg_enable` is true, scoring reads flattened `hit["srg"]`, falling back to nested payload, then multiplies final score by `1.08` for this agent's last-ingest band, `1.05` for crystal, and `1.03` for heartbeat class A. It attempts breathing evolution only from nested `payload["srg"]`; on a qualified legacy graph target it replaces the in-process entity payload. Errors are fail-soft. This is process-local behavior, not generic SQLite ranking.

Native already has `NativeSRGTransientRuntime`, keyed by full `(core_id, source_namespace, eid, revision)` witnesses for process-local overlays. It is not yet a Fabric query breathing adapter. A native seam must bind a matching scoped transient owner, not drop SRG evolution or write an unqualified SQLite update.

### Provenance and governance

Before scoring, Fabric hard-excludes memory classes `baton`, `reference`, `environment`, and `closure`. It derives valid `provenance_type`, discounts collective provenance by default `0.50`, and tool results by default `0.85`. It does not otherwise query-filter canon, protected, lifecycle, retirement, or supersession markers; native reads must project only current qualified rows, not history.

After global top-k, `filter_llm_facing(..., surface="llm_context")` excludes `governance.non_shareable`. It reports `{eid, excluded_reason}` and does not refill results. Its public exclusion diagnostic is scope-ambiguous for equal private/shared EIDs, although returned hits retain scope fields.

## Scoring, merge, and public result contract

For each candidate:

```text
base = sim * (1 + .35*strength + .10*recency + .20*motif_alignment)
       - .30*contradiction_risk
final = base + continuity bonuses
final += reinforcement boost
final *= SRG multipliers
final *= collective and tool-result discounts where applicable
final *= MemoryPlan lane weight where applicable
```

Fabric copies the hit, writes `motifs`, `motif_alignment`, `final_score`, `provenance_type`, conflict data, and optional explain data. It stable-sorts final score descending and truncates to `top_k`; there is **no final dedupe**. Equal scores retain candidate concatenation order: private, primary shared by domain, bridge peek by destination, deep.

Hits retain flattened legacy fields/payload extensions: at least EID, summary, type, strength, confidence, score/raw score/decay factor, step/ts, scope, workspace/domain/agent where stored, motifs, final score, and provenance metadata. Explain/continuity are opt-in. Character runs after filtering/ranking and adds `character_tier`, `character_tier_weight`, and `character_weighted_score`; it does not alter `final_score` or re-rank.

The enclosing result returns router `domains`, `domain_used`, `bridge_peek_domains`, filtered `results`, exclusion/filter diagnostics, active motifs/dominant thread, bridges, role/embed context, and optional continuity-debug, Character, and collective context. The A0 test locks that equal private/shared EIDs remain separate result rows.

## Character query disposition

With Character enabled and a seed, Fabric loads external seed by workspace/seed ID and state by workspace/agent, then calls `assemble_character_context` after filtering/ranking. The current assembler classifies supplied hits by type/canon/half-life and adds tier fields. Its `graph` argument is not read by its current implementation. It uses no private seed EID, shared EID, or motif-ID lookup. D5A's shared post-write no-op does not disable this query context.

```text
CHARACTER_QUERY_SCOPE_AMBIGUITY = NO
```

## Native read foundations and proposed seam

`NativeMemoryVectorRuntime` is the correct native vector primitive. For one explicit `NativeMemoryRuntimeScope` and representation lane it rebuilds an immutable float32 matrix from current READY/USABLE/MATCH witnesses, copies legacy normalization and NumPy top-k selection, projects selected rows through `NativeMemoryCompatibilityFacade` in one read transaction, and rejects raced/stale selections whole. It is not an SQL cosine replacement. Existing native tests establish parity with `MemoryGraph.search` and `search_by_embedding`, including text embed behavior, normalization, argpartition selection, decay, filters, and currentness.

E4C recovery supplies explicit private/shared scopes and a fresh vector runtime per admitted lane. `NativeMotifGeometryAdapter` reads only explicit admitted shared domains through `NativeMotifRuntimeReader`, using the proper motif alias namespace and semantic scope. It provides domain centroids and runtime motifs, but does not itself expose the legacy-specific `MotifRegistry.active()` summary surface.

The future seam must be an injected qualification-only `QualifiedQueryReadModel` used at `_query_private_lane` and `_query_shared_lane`, with Fabric orchestration/scoring remaining outside it:

```text
QualifiedQueryReadModel
  private_lane(workspace_id, agent_id) -> QualifiedQueryLane
  shared_lane(workspace_id, domain_id) -> QualifiedQueryLane
  domain_geometry(domain_id) -> native geometry snapshot
  active_motifs(domain_id) -> legacy-compatible summary projection
  resolve_srg_transient_target(qualified memory identity) -> process-local port

QualifiedQueryLane.search(query_text, top_k, user_id, min_score, type_filter)
  -> MemoryGraph.search-shaped flattened hits with verified workspace/scope/
     agent-or-domain qualifier and native structural identity retained internally
```

The native lane must call `NativeMemoryVectorRuntime.search(query_text, ...)`, then validate rather than invent scope metadata. Memory motif memberships and geometry must be keyed internally by `(domain_id, runtime_motif_id)`. Public fields remain compatible, but anchors, exclusions, conflicts, SRG targeting, motif alignment, and all grouping must retain complete scope identity.

`MemoryGraph` dependencies requiring a seam are:

- public `search` shape and lane-owned embedding call;
- graph-local EID/payload origin fields;
- private `.entities` source presence for external deep retrieval;
- private/shared `.entities` payload access for legacy SRG breathing writeback; and
- the Character graph argument (currently unused).

Fabric does not inspect a `MemoryGraph` candidate matrix, vector cache, or embeddings during normal private/shared scoring. Matrix behavior can remain inside `NativeMemoryVectorRuntime`.

## Qualification fixtures for the later seam (not administered in A0)

| Fixture | Required comparison |
| --- | --- |
| Private-only hit | Legacy versus one private native lane; shape and score parity. |
| Single shared domain | Explicit shared scope metadata, current projection, score parity. |
| Multiple shared domains | Router order, per-domain relational cap, merge order. |
| Overlapping EIDs | No collapse and no cross-scope modifier leakage. |
| Requested domain | Requested-first/router-fallback and invalid-domain failure parity. |
| Automatic selection | Weighted/zero centroids, equal-score order, no threshold. |
| Bridge peek | External status/confidence law, two-domain cap, append order, cold recovery. |
| Motif alignment | Qualified `(domain, motif)` membership/centroid handling, duplicate aliases. |
| Conflict/governance | Qualified conflict key, post-top-k non_shareable exclusion, no refill. |
| Private reinforcement | Current half-life/reinforcement fields and boost. |
| Character | External seed/state, tier annotations, no re-rank. |
| SRG | Same-band/crystal/heartbeat modifiers and transient overlay. |
| Empty lane/tie | Embedder-call law, NumPy tie behavior, stable merge order. |
| Cold native recovery | Recreated vector/geometry readers from SQLite only; no legacy shadow registry. |

Deep is omitted because it is not in the qualified default native profile.

## Blockers and verdict

1. **Bare-EID continuity identity:** `anchor_full_boost_eids` is a bare integer set and crosses private/shared scope on an ordinary collision.
2. **Bare motif-ID geometry identity:** selected-domain centroids are flattened by motif ID and cross domain scope; bridge-peek geometry is unavailable to that map.
3. **SRG adaptation required:** legacy query has process-local breathing side effect; read-only native vector retrieval needs a qualified transient overlay adapter for SRG-enabled parity.
4. **Public exclusion diagnostics:** filtering reports only bare EID. This does not collapse hits, but is ambiguous when reporting cross-scope exclusions.

The first two contradict E4E's required query identity law. Reproducing them natively violates namespace isolation; correcting them only natively diverges from the current legacy reference. Resolve them in a separately authorized legacy query identity repair before native query materialization.

```text
E4E_QUERY_PREFLIGHT = BLOCKED

NATIVE_QUERY_SEAM =
  QualifiedQueryReadModel at Fabric private/shared lane helpers, backed by one
  NativeMemoryVectorRuntime per fully qualified lane, native geometry/active
  projection, and a qualified process-local SRG overlay adapter; blocked until
  legacy query uses composite memory and motif identities.

QUERY_MEMORYGRAPH_INTERNAL_DEPENDENCIES =
  search shape + lane embed call; graph-local EID/payload origin; deep source
  presence; legacy SRG entity/payload writeback; Character graph argument.

QUERY_EMBEDDER_CALL_BEHAVIOR =
  one Fabric routing embed, then one same-text embed per non-empty-text
  private/shared/bridge MemoryGraph search; deep reuses Fabric's vector.

DEFAULT_QUERY_DEEP_PROFILE = disabled
CHARACTER_QUERY_SCOPE_AMBIGUITY = NO
BARE_EID_QUERY_DEDUP_RISK = YES
KERNEL_CHANGE_REQUIRED = NO
```

## A1 supersession status

The A0 observations above are retained as the historical baseline. A1 repairs
the two identified legacy query identity leaks prospectively: continuity
anchor comparison now uses qualified memory identities and motif geometry now
uses qualified domain/motif identities. See
`docs/7G5E4E_A1_QUERY_COMPOSITE_IDENTITY_REPAIR.md` for the repair evidence
and reassessment.

```text
BARE_EID_QUERY_IDENTITY_LEAK = CLOSED
BARE_MOTIF_ID_QUERY_IDENTITY_LEAK = CLOSED
E4E_QUERY_PREFLIGHT = READY
```
