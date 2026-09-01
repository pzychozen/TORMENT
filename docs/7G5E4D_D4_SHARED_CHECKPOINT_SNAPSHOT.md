# 7G5E4D-D4 shared checkpoint snapshot parity

## Scope and authority

D4 begins at `24ac760 Qualify 7G5E4D shared trajectory evidence` and qualifies only creation of the existing external checkpoint JSON for a shared-trigger post-write context. The standalone profile is `core_staging_with_shared_checkpoint_snapshot`.

~~~text
CHECKPOINT_MEMORY_AUTHORITY = NONE
CHECKPOINT_MOTIF_AUTHORITY = NONE
CHECKPOINT_CHARACTER_AUTHORITY = NONE
CHECKPOINT_NATIVE_CORE_RECOVERY_AUTHORITY = NONE
~~~

No checkpoint table, object, revision, relationship, representation, native recovery route, selector, activation, dual write/read, or kernel/world mathematics was added. D4 does not load or restore a checkpoint; native core recovery remains the current SQLite core.

## Frozen legacy law

Legacy post-write reaches checkpoint for every storage outcome, after world and Character slots and before compression. The slot returns unless `owner._checkpoint_enable`, `step > 0`, and `step % owner._checkpoint_interval == 0`. Fabric defaults are enabled, interval `500`, and retain `10` checkpoints.

The triggering workspace and agent own the file even for a shared source:

~~~text
<data_dir>/workspaces/<workspace_id>/agents/<agent_id>/private/checkpoints
~~~

`save_checkpoint` writes version `3` with `checkpoint_<step:06d>.json`. It writes a `.tmp` file, then calls `os.replace`. Matching checkpoint names sort ascending and prune the oldest above `max_checkpoints`; unrelated and stale `.tmp` files are left alone.

| Component | Existing source / serialization |
| --- | --- |
| `model_state` | Live `ModelState` through `serialize_model_state`, including canonical Omega, z, stages, vectors, step, and `_char_mod` |
| `corridor_monitor` | Live runtime-context monitor |
| `kernel_runtime_context` | Monitor, dispersion buffer, effective scale, cognitive state; model data also receives `z_mem` |
| `character_state` | `asdict(CharacterStore.load_state(...))`, or `None` |
| `motif_summary` | Existing `total_count` / strength-ordered `top_motifs` schema |
| `shard_snapshot` | Existing optional schema member |

Preparation order is motif summary, shard snapshot, Character snapshot, runtime-context check, then save. Component failures degrade independently; the outer checkpoint slot is fail-soft.

## Native D4 binding

D4 binds only live process `ModelState` and `KernelRuntimeContext`. It never recomputes kernel state from SQLite. It uses the existing CharacterStore `load_state` interface but does not run Character measurement, gravity, reflex, or persistence.

~~~text
claimed shared context, including NO_WRITE/stored outcomes
  -> current NativeMotifRuntimeReader scoped by native motif alias + semantic scope
  -> existing build_motif_summary over a read-only native projection
  -> existing CharacterStore.load_state for triggering agent
  -> shard_snapshot = None
  -> existing save_checkpoint JSON writer
~~~

The native motif projection contains current runtime motif ID, label, strength, and member count only. It reads neither `motifs.json` nor a legacy `MotifRegistry`. Runtime-ID ordering supplies stable tie order before the existing builder applies descending-strength ordering. No memory EID is exported or cross-scope interpreted.

SQLite has no truthful equivalent of the legacy embedding-shard manifest. D4 intentionally does not call `build_shard_snapshot`:

~~~text
NATIVE_SHARD_SNAPSHOT = NONE
FABRICATED_NATIVE_SHARD_SNAPSHOT = NO
SHARED_CHECKPOINT_SEMANTIC_PARITY = PASS_WITH_NATIVE_SHARD_ABSENCE
KERNEL_CHECKPOINT_SERIALIZATION_PARITY = PASS
MONITOR_SNAPSHOT_PARITY = PASS
CHECKPOINT_MOTIF_SUMMARY_PARITY = PASS
CHARACTERSTORE_REMAINS_AUTHORITY = YES
CHARACTER_MEASUREMENT_IN_D4 = NO
CHARACTER_GRAVITY_IN_D4 = NO
~~~

The deterministic legacy witness has a legacy shard metadata payload and matches every native semantic component. The only intentional difference is non-null legacy shard metadata versus native `null`.

## Failure, path, and load posture

| Condition | Existing/D4 behavior |
| --- | --- |
| Native motif summary read fails | Debug log; checkpoint saves with `motif_summary: null`. |
| Character unavailable/load failure | Existing `null` behavior; no Character work occurs. |
| Model serialization or ordinary filesystem failure | Existing writer logs/returns `None`; D4 stays fail-soft. |
| Root identity/containment failure | `save_checkpoint` raises `CheckpointContainmentError`; D4’s legacy-shaped outer boundary logs it and continues. Direct checkpoint callers retain the distinct error. |
| Missing checkpoint | `load_latest_checkpoint` returns `None`. |
| Latest matching JSON corrupt | Loader returns `None`, without older-file fallback. |

The checkpoint module retains component validation, canonical containment, a bounded directory-identity guard, and revalidation before write/prune. Prune reconstructs validated child names, refuses links/reparse points, and leaves unrelated files alone.

The D4 retention witness writes steps 5, 10, 15, and due `NO_WRITE` step 20 with retention two. Only checkpoints 15 and 20 remain. Corrupt and missing loads leave native semantic table counts unchanged.

~~~text
CHECKPOINT_FAILURE_TOPOLOGY_PARITY = PASS
CHECKPOINT_ATOMIC_SAVE_REGRESSION = PASS
CHECKPOINT_PATH_HARDENING_REGRESSION = PASS
CHECKPOINT_RETENTION_PARITY = PASS
CORRUPT_CHECKPOINT_MEMORY_MUTATION = NONE
MISSING_CHECKPOINT_MEMORY_MUTATION = NONE
CHECKPOINT_NATIVE_MEMORY_MUTATION = NONE
CHECKPOINT_ONLY_VECTOR_INVALIDATION = NO
~~~

Checkpoint-only execution creates no native representation and mutates no native semantic row. Its model, monitor, Character, and motif reads are snapshots; the live process objects remain unchanged.

## Remaining blockers

| Area | D4 disposition | Future owner/boundary |
| --- | --- | --- |
| Character measurement | Blocked; D4 copies existing CharacterState only. | Existing CharacterStore and mixed shared-source/private-agent measurement. |
| Character gravity/reflex | Blocked; D4 calls neither. | Future explicit mixed topology and any shared correction source. |
| Compression candidate reads/count | Blocked. | Triggering agent private graph and compression policy. |
| Short successor, deep export, hard-cap | Blocked. | Private writes and external deep store; no shared-EID inference. |

D1 M1/D0/mood, D2 Hivemind, D3 trajectory evidence, and B1 remain standalone. D4 refuses their composition; full direct-shared-ingest composition is later.

## Verification

`tests/test_substrate_native_shared_checkpoint_snapshot.py` covers native motif-only summary, version-3 model/monitor/runtime serialization, CharacterState present/absent behavior, native shard absence, triggering-agent path, all-outcome gating, retention, corrupt/missing non-authority, and component/writer/containment failures.

The bounded regression set passed 123 tests under `torment-substrate`, SQLite 3.53.4, including checkpoint compatibility/path hardening plus D3, D2, D1/D0, B1, and process-world coverage.

~~~text
SHARED_CHECKPOINT_SNAPSHOT = QUALIFIED
D3_TRAJECTORY_REGRESSION = PASS
D2_HIVEMIND_REGRESSION = PASS
D1_REGRESSION = PASS
D0_REGRESSION = PASS
B1_REGRESSION = PASS
KERNEL_FILES_CHANGED = 0
PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
~~~
