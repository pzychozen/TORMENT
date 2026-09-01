# 7G5E4D-B1 native shared post-write bridge capability

## Scope

B1 qualifies one native shared post-write consumer only: the existing
`BridgeRegistry` suggestion workflow.  It does not select a production
backend, wire public `TormentFabric.ingest()` to native storage, add a bridge
table, or open direct shared ingest.

The qualified authority split is:

```text
SQLite current motif revisions -> NativeMotifGeometryAdapter -> BridgeRegistry
                                                  ^                    |
                              explicit B1 profile + random gate         +-- bridges.json
                                                                       +-- bridge_events.jsonl
```

`BridgeRegistry` remains the external owner of suggestion status, persistence,
and endpoint-pair/reverse-pair duplicate suppression.  B1 neither creates a
shadow `MotifRegistry` nor reads `workspace.motif_regs` for the native path.

## Frozen ordinary-ingest contract

The legacy post-write adapter calls the bridge decision after its
created-memory branch and all other ordinary post-write consumers.  It is
therefore considered for every post-write outcome, but performs a suggestion
only when both of these are true:

```text
context.stored
random_chance(probability)
```

The exact current laws are:

```text
tear        = float(tri_mod.get("tearing_risk", 0.0))
probability = clip(float(tri_mod.get("bridge_p", 0.08)) * (1 - 0.40 * tear), 0.02, 0.12)
threshold   = clip(float(tri_mod.get("bridge_sim", 0.86)) + 0.03 * tear, 0.84, 0.92)
max_new     = 5
```

The only influencing context fields are `stored` and the three `tri_mod`
values above.  `BridgeRegistry.suggest()` iterates the injected domain ordering
first, then each domain's current motif ordering, comparing cross-domain pairs
only (`i < j`).  It skips incompatible centroid dimensions and records only
cosines at or above `threshold`.  Existing endpoint pairs are suppressed in
both forward and reverse direction.  The bridge call is intentionally
fail-loud: legacy code does not catch a `BridgeRegistry` exception, and B1
uses that same helper unchanged.

## B1 capability boundary

`NativePostWriteQualificationProfile.core_staging()` remains closed for shared
post-write.  B1 adds the distinct
`core_staging_with_shared_bridge_suggestion()` profile member and requires all
of the following before a shared context can run:

- a claimed `SHARED_DOMAIN` routing scope matching workspace and domain;
- `shared_bridge_suggestions_required=True`;
- `shared_bridge_suggestion=QUALIFIED`;
- no derived-memory runtime binding;
- an injected `NativeMotifGeometryAdapter` covering exactly the admitted
  shared domains, plus an injected `random_chance` callable.

The shared branch invokes only `run_bridge_suggestions()`.  It does not bind
or run conflict, SRG, Hivemind, derived-memory, world, character, proposal,
checkpoint, compression, trajectory, deep-memory, or motif-maintenance
consumers.  A private context presented to this profile, an unqualified
profile, an unadmitted domain, or missing native geometry fails closed.

## Geometry, retirement, and recovery

The B1 caller supplies the existing `NativeMotifGeometryAdapter` with explicit
admitted-domain order.  The adapter reads current motif revisions through the
qualified multi-scope native reader.  Retired M2 motifs are excluded by that
reader; their aliases/history remain durable but cannot become bridge
endpoints.  The adapter refuses domains outside the supplied admitted set.

Each geometry read opens qualified SQLite readers, so B1 works after a cold
recovery without `motifs.json`.  Bridge state is independently reloaded from
the existing external `bridges.json` side store; a post-recovery retry remains
deduplicated by `BridgeRegistry`.

## Non-effects

Bridge suggestion reads geometry and writes only its external workflow files.
It does not mutate native motif revisions, memberships, process-order state,
memory representations, or a `NativeMemoryVectorRuntime`.  In particular,
there is no vector invalidation path in B1.

## Qualification evidence

`tests/test_substrate_native_shared_bridge_post_write.py` covers explicit
shared admission, false/true random gates, all probability and threshold clamp
positions, `max_new=5`, result and duplicate parity against the legacy helper,
M2 retired-endpoint exclusion, unadmitted-domain refusal, fail-loud bridge
errors, cold geometry/bridge recovery, and native no-mutation assertions.

Native-substrate qualification uses conda environment `torment-substrate`
with SQLite 3.53.4.  The ordinary `torment` environment is intentionally not
changed by B1.
