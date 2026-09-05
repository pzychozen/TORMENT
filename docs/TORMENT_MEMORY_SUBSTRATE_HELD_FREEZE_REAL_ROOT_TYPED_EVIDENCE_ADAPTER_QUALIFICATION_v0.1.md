# TORMENT Memory Substrate — Held-Freeze Real-Root Typed-Evidence Adapter Qualification v0.1

## Status

`SYNTHETIC_QUALIFICATION_COMPLETE`

This phase qualifies a production-shaped, strictly read-only source adapter
against disposable fixture trees only. It does not authorize a real-root read,
capture, admission, migration, writer interaction, process/listener inspection,
service startup, runtime construction, or external-owner execution.

The earlier stopped real corrective capture remains recorded in
`TORMENT_MEMORY_SUBSTRATE_HELD_FREEZE_CORRECTIVE_REAL_EVIDENCE_CAPTURE_RESULT_v0.1.md`.
It stopped before capture because no concrete typed source-evidence adapter
existed. This record supplies the missing adapter contract without revisiting
the real root or overwriting that result.

## Adapter boundary

`torment_service.substrate.real_root_typed_evidence.RealRootTypedEvidenceAdapter`
implements the existing `CorrectiveSourceEvidenceAdapter` protocol. It reads
only the fixed source grammar:

- `workspaces/<workspace>/workspace_meta.json` and `domains.json`
- `workspaces/<workspace>/agents/<agent>/identity.json` and optional `private`
- `workspaces/<workspace>/domains/<domain>/shared`
- optional workspace-local `external_owner_observations.json`
- explicit configured top-level excluded artifacts

There is no arbitrary tree walk. Direct child enumeration is limited to the
workspace, agent, domain, and scope boundaries. Symlinks, unknown durable
artifacts, undeclared materialized domains, noncanonical scope shapes, and
unclassified external-owner records refuse collection.

The adapter does not instantiate `TormentFabric`, a workspace, memory graph,
runtime, REST/MCP surface, provider, model, SQLite connection, or cache. It
does not allocate UUIDs and never writes below the source root. Hashing streams
file content; metadata-less vectors are inspected only through their `.npy`
header to retain dtype and shape, without materializing vector values.

## Persisted evidence mapping

| Persisted source fact | Output | Refusal boundary |
| --- | --- | --- |
| exact target provider/model/dimension | `TARGET_COMPATIBLE` | dimension alone never qualifies |
| `REEMBED_REQUIRED` plus legacy hash | `REEMBED_REQUIRED` | mismatch is not silently reclassified |
| `UNKNOWN_IDENTITY` plus per-EID source list | `UNKNOWN_IDENTITY` | each EID needs exact vector/text paths |
| absent private nodes, zero rows/next row, empty events | `EMPTY_PRIVATE` / `NO_VECTOR` | nonzero state refuses |
| declared shared domain physically absent | `DECLARED_EMPTY_SHARED` / `NO_VECTOR` | declaration is retained |
| shared scope with motifs but no nodes | `EMPTY_SHARED_WITH_MOTIF` / `NO_VECTOR` | motif presence is explicit |

Metadata-less evidence requires `emb_<eid>.npy` and
`canonical_text_<eid>.json`, retains their SHA-256 facts in the existing
manifest, and preserves EID, dtype, shape, and source-evidence identity. It
never infers a provider or loads a vector array.

External owner records use only the frozen `ExternalOwnerObservationKind`
taxonomy. Their file digest becomes the observation digest used by the existing
frozen geometry-disposition plan. An unclassified durable owner is a refusal.

## Packet integration

The adapter produces the existing root description, explicit source manifest,
source scope plans, unknown-identity evidence, empty-private evidence,
declared-empty evidence, external-owner observations, geometry inputs, and
typed excluded-artifact expectations/observations. It adds no evidence model.
`CorrectiveFreezeTypedEvidence` validates all coverage against canonical fixed
layout discovery. Packet serialization stays outside the source root, and the
packet reloads after the source has been removed.

Packet manifest version `2` adds `motif_presence` to source-scope-plan
serialization. This is a deliberate strict contract change; it does not
downgrade or silently decode the prior shape.

## Synthetic qualification fixture

`tests/test_real_root_typed_evidence_adapter.py` creates only a disposable
production-shaped source. It covers multiple workspaces (including zero
private scopes), multiple private/shared scopes, declared shared absences,
empty private and empty shared-with-motif postures, target metadata, legacy
hash metadata, metadata-less per-EID header evidence, external-owner state,
and top-level unscoped exclusions.

The suite verifies discovery/declarations, every persisted classification,
dimension-only refusal, manifest/owner/geometry binding, motif posture,
excluded-artifact typing, unclassified-owner refusal, and exact source-tree
nonmutation. The integration test invokes the actual adapter through
`capture_corrective_freeze_packet`, removes the disposable source, and reloads
the complete packet offline. Its writer/listener/job values are injected
synthetic observations; no process or service is contacted.

The readonly guard compares all fixture file hashes before and after adapter
collection and verifies no SQLite, WAL, or database file appears.

## Qualification command

```cmd
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
python -m pytest tests\test_real_root_typed_evidence_adapter.py tests\test_held_freeze_corrective_evidence_capture.py -q --basetemp _pytest_tmp_held_freeze_typed_adapter -p no:cacheprovider
```

Result: `28 passed`.

## Explicit non-results

- No real-root read occurred for this phase.
- No production writer was started, stopped, or queried.
- No real t0/t1/t2 capture occurred.
- No admission, migration, normalization, activation, geometry execution,
  SQLite write, or provider/model call occurred.
- A future real capture remains separately gated by authorization and concrete
  writer-freeze evidence.
