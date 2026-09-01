# 7G5E4D-M1 native motif-maintenance qualification

## Boundary

M1 qualifies suggestion-only motif maintenance and domain-suggestion geometry
as TORMENT workflow operations over either legacy motif truth or explicitly
recovered native motif truth. It does not select native storage in production,
resume proposal orchestration, dual read/write, move workflow JSON into SQLite,
or implement motif merge mutation.

Native current motif truth remains SQLite-owned: current motif revisions,
memberships, membership retirement, and geometry are read through the existing
native motif reader/geometry adapters. The retained TORMENT workflow files
remain their established owners:

```text
motif_events.jsonl       E/F diagnostic event history
motif_merges.json        D merge-suggestion workflow state
domain_suggestions.json  automatic domain-suggestion workflow state
```

Actual motif merge remains B-class durable motif truth and is deliberately
outside M1 (`7G5E4D-M2`).

## Frozen legacy maintenance law

`MotifRegistry.entropy_report(target_n)` has these exact semantics:

1. Zero or one motif returns zero for `shannon`, `fragmentation`, and
   `entropy_score`.
2. Otherwise it iterates the current motif order, floors each strength at
   `1e-6`, normalizes by `sum + 1e-12`, and computes normalized Shannon entropy
   with `log(n) + 1e-12`.
3. Fragmentation is `min(1, n / max(1, target_n))`.
4. The score is `min(1, .55 * shannon + .45 * fragmentation)`.

Every invocation first appends one `MOTIF_ENTROPY` JSONL record with the four
report fields, then adds default `ts`, `workspace_id`, and `domain_id` fields.
If `entropy_score >= entropy_high`, candidate generation visits pairs in the
provided current-geometry order, skips empty/mismatched centroids, computes the
existing epsilon cosine, retains `sim >= sim_threshold`, then stable-sorts only
by descending similarity. The stable sort retains the original pair traversal
order for equal values.

Each selected candidate up to `max_suggestions` uses ID
`merge_{a}__{b}` and record fields:

```json
{
  "suggestion_id": "merge_<a>__<b>",
  "a": "<a>", "b": "<b>", "sim": 0.0,
  "status": "suggested", "created_ts": 0, "updated_ts": 0
}
```

New records append `MOTIF_MERGE_SUGGESTED` before one sorted, indented
`{"suggestions": ...}` write to `motif_merges.json`. Existing IDs update only
their in-process `sim`; exactly as legacy does, a call producing no new record
does not rewrite that JSON. Thus unchanged repeated maintenance appends another
entropy event, suppresses duplicate outstanding suggestion events, and normally
leaves merge JSON bytes unchanged. Malformed merge JSON loads as an empty
in-process suggestion map; events/merge writes otherwise fail at their normal
file operation and the direct maintenance call propagates the error. The legacy
post-write caller retains its existing best-effort exception boundary.

`auto_merge=True` is not routed through this suggestion-only law on native.
`NativeMotifAutoMergeRefused` occurs before an entropy event, suggestion write,
or native motif mutation.

## Ports and no-shadow rule

`MotifMaintenancePort` defines only `update_entropy_and_suggest`. The legacy
adapter delegates to the existing `MotifRegistry`, preserving its authority and
actual auto-merge behavior. `NativeMotifMaintenanceAdapter` consumes a
`MotifGeometryPort` and a `MotifSuggestionWorkflowStore`; it has no registry,
motif persistence API, or SQLite writer.

The native adapters use the qualified `NativeMotifRuntimeReader` through either
the recovered multi-scope `NativeMotifGeometryAdapter` (shared-domain workflows)
or the explicit connection-scoped `NativeScopedMotifGeometryAdapter` (the
staging post-write tail). Both expose runtime ID, label, centroid, strength,
stability, membership count, and clocks. No native maintenance path reads or
writes `motifs.json`, membership files, or a copied `MotifRegistry`.

The native reader's deterministic runtime-ID order is the qualified current
geometry order. Existing workspace fixtures reload legacy `motifs.json` through
its sorted persistence format, giving the same order for current qualified
states; equal-similarity ordering is tested against that order.

## Domain-suggestion geometry law

`TormentFabric._maybe_suggest_domain` now accepts an optional read-only
`MotifGeometryPort`; the default still adapts `ws.motif_regs` for legacy calls.
The method intentionally does **not** use the port's weighted
`domain_centroid` helper. Its preserved rule is the raw `np.mean` of all
non-empty motif centroids in each domain, without strength or membership
weighting.

For the requested domain, every motif with strength at least `.75` is compared
to that raw centroid by epsilon cosine. A score below `.35` derives
`suggested_<slug(label)>` (truncated to 32 characters) and appends the existing
external record shape. Duplicate suppression is exactly `(domain_id, motif_id)`
against the existing JSON list, then the list is truncated to its newest 500
records. There is no separate current-domain-membership refusal in the existing
heuristic: if a different motif derives an already-approved candidate name, the
legacy law still relies solely on the pair key. Domain creation remains only
`approve_domain_suggestion()` operator authority.

## Native post-write posture

`NativePostWriteQualificationProfile.core_staging()` remains frozen with motif
suggestion maintenance as `REQUIRED_NOOP`. M1 adds the explicit opt-in
`core_staging_with_motif_suggestion_maintenance()` profile, where suggestion
maintenance is `QUALIFIED` and `motif_auto_merge` remains `UNSUPPORTED`.
Required maintenance also requires caller-owned `workspace.data_dir`; it writes
only the existing external workflow files. No profile grants activation or
changes the production default.

## Qualification evidence

Focused tests cover empty/one/multiple/uneven entropy fixtures, below/exact/above
threshold decisions, stable merge ordering, maximum suggestions, event and JSON
byte parity, retry/reload behavior, native auto-merge refusal, native post-write
execution, raw domain-centroid calculation, duplicate domain suggestions, and
no-shadow assertions. The E4C admitted workspace test additionally reads
creative/engineering/research geometry from reopened SQLite, runs native
maintenance, reopens the recovery object, and proves retained `motifs.json`
bytes are unchanged.

```text
MOTIF_MAINTENANCE_PORT = QUALIFIED
MOTIF_ENTROPY_NUMERICAL_PARITY = PASS
MOTIF_ENTROPY_EVENT_PARITY = PASS
MOTIF_MERGE_SUGGESTION_PARITY = PASS
MOTIF_MERGE_SIDE_STORE_PARITY = PASS
MOTIF_MERGE_EVENT_PARITY = PASS
MOTIF_MAINTENANCE_RETRY_SEMANTICS = CHARACTERIZED
DOMAIN_SUGGESTION_GEOMETRY_PORT = QUALIFIED
DOMAIN_APPROVAL_AUTHORITY_CHANGED = NO
SHADOW_LEGACY_MOTIF_STATE = NONE
NATIVE_MOTIF_AUTO_MERGE = REFUSED
AUTO_MERGE_MOTIF_TRUTH_CHANGED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
PRODUCTION_SELECTOR_ADDED = NO
KERNEL_FILES_CHANGED = 0
```
