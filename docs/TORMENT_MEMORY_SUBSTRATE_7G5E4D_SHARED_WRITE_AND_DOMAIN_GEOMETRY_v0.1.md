# TORMENT Memory Substrate 7G5E4D

## Frozen shared-writer archaeology

The reachable legacy shared writers are deliberately not treated as one
interchangeable operation.

| Path | Authority before storage | Prepared storage facts | Motif / post-write timing |
| --- | --- | --- | --- |
| `TormentFabric.ingest(scope="shared")` | Ordinary kernel write gate; no canon authority | Kernel/supplied embedding once, summary, signal type/strength/confidence/half-life, caller payload plus Fabric's protected payload envelope and user provenance | `attach_or_create` before the one legacy node flush; then existing post-write adapter runs. Private-only reinforcement remains excluded. |
| `process_proposals` | Quorum of non-collective contributors; strongest authority-contributing proposal supplies content | Proposal embedding, collective actor, canon payload, slow 30-day decay, support agents and proposal IDs | Conflict scan precedes storage; motif attach and entropy update follow it; bridge suggestion occurs once after any created shared nodes. |
| `decide_proposal(..., "approve")` | Explicit operator decision; collective-echo proposals are refused | Proposal embedding, collective actor, canon payload, slow 30-day decay and support-agent evidence | Motif attach follows storage; proposal status, bridge suggestion, then domain suggestion follow. |

`NativeFabricRouteRequest` represents these already-decided storage facts:
the actor, exact lane, payload, representation bytes, provenance, governance,
lifecycle, and flexible evidence are all explicit. It does not decide quorum,
operator approval, kernel policy, Character policy, or Hivemind authority.
The router's duplicate/reinforcement pre-scan is intentionally private-only;
shared routes always take the new-memory composition path.

External retained actions remain external: BridgeRegistry persistence/events,
conflicts, proposal registries, checkpoints, trajectories, and CharacterStore.
No production selector, dual read/write, or query routing is introduced.

## Backend-neutral geometry

`motif_geometry_port` provides a read-only `MotifGeometryPort` with immutable
`RuntimeMotifGeometry` values. `LegacyMotifGeometryAdapter` delegates the
existing registry and centroid law unchanged. `NativeMotifGeometryAdapter`
opens only explicit E4C recovered shared readers and supplies the exact motif
alias namespace, semantic scope, domain, and qualified dimension. It refuses
unadmitted domains rather than guessing aliases.

Bridge suggestion now traverses that port. Legacy `Dict[str, MotifRegistry]`
callers are adapted at the boundary, retaining their established comparison
order, cosine threshold, duplicate suppression, persistence, and event law.
Bridge records themselves remain external JSON evidence.

## Boundary declaration

```text
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
FABRIC_QUERY_NATIVE_WIRED = NO
PRODUCTION_SELECTOR_ADDED = NO
KERNEL_FILES_CHANGED = 0
CHARACTERSTORE_REMAINS_EXTERNAL = YES
BRIDGES_REMAIN_EXTERNAL = YES
```
