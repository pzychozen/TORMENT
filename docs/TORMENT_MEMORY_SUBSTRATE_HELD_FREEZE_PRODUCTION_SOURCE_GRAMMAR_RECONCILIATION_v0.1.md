# Held-freeze production source-grammar reconciliation

## Final bounded static result

```text
STARTING_HEAD = 12eb9de6fbd410237d60b9799de1dc535c527f61
REPRESENTATION_IDENTITY_RULE = QUALIFIED
REPRESENTATION_IDENTITY_AUTHORITY = workspace_meta.json
STORAGE_MANIFEST_IDENTITY_AUTHORITY = NO
PRODUCTION_GRAMMAR_RECONCILIATION = PASS
PACKET_VERSION_BEFORE = 3
PACKET_VERSION_AFTER = 3
PACKET_SCHEMA_CHANGED = NO
NEW_HASH_LAW = NO
NEW_BYTE_IDENTICAL_LAW = NO
NEW_CANONICALIZATION_LAW = NO
```

The adapter reads `embed_provider`, `embed_model`, and `embed_dim` directly
from `workspaces/<workspace>/workspace_meta.json`. It recognizes only the
frozen target lock (`st`, `BAAI/bge-small-en-v1.5`, `384`) and the frozen hash
lock (`hash`, `hash:384:torment`, `384`). Any partial, empty, malformed, or
other explicit lock refuses. A missing lock is admitted only for the qualified
Phase-9B scopes `ws3|PRIVATE|a1`, `ws4|PRIVATE|a1`, and
`ws5|PRIVATE|a1`, each with current per-EID evidence.

`embeddings/manifest.json` is now read only as the production seven-key storage
manifest. Its dimension can contradict a workspace lock and therefore refuse;
it cannot establish provider or model identity. Persisted node representation
stamps are likewise equality-only contradiction checks.

## Reconciled production ownership

```text
KNOWN_AGENT_GRAMMAR_RECONCILED = YES
KNOWN_WORKSPACE_GRAMMAR_RECONCILED = YES
KNOWN_PRIVATE_GRAMMAR_RECONCILED = YES
KNOWN_SHARED_GRAMMAR_RECONCILED = YES
EXTERNAL_OWNER_GRAMMAR_RECONCILED = YES
UNCLASSIFIED_KNOWN_PRODUCTION_PATH_CLASS = NONE
```

The adapter derives typed owner observations from production paths, not from
the former synthetic `external_owner_observations.json` registry:

- `agents/<agent>/identity.json`, `roles.json`, and `character_state.json`
- `seeds/<seed>/seed.json`
- workspace `bridges.json`
- domain `proposals.jsonl` and `conflicts.jsonl`

Roles and Character state remain external-owner state; seed definitions remain
Character-owned. They do not become core memory sources. The recognized
retained/evidence paths include affect, anchors, symbols, feedback audit,
derived indexes, archive, warmup, checkpoint, trajectories, bridge events,
motif events/merges, proposal/conflict events, and the named collective,
reference, environment, closure, contest, and governance directories. They
remain owner-bounded retained or audit state rather than a new core source or
a recursive evidence framework. Domain motifs are read from their production
location, `domains/<domain>/motifs.json`.

Unknown durable direct root, workspace, agent, private, shared, storage, and
synthetic owner-registry artifacts continue to refuse. `lived_use` remains
presence-only and its descendants are not read or hashed.

```text
CHARACTER_SEMANTICS_CHANGED = NO
ROLESTORE_SEMANTICS_CHANGED = NO
CORE_MEMORY_SEMANTICS_CHANGED = NO
```

## Synthetic qualification

The disposable production-shaped fixture covers target, hash, and all three
qualified metadata-less locks; real storage manifests; empty private and
shared postures; roles, Character state, seed, motifs, workflow ledgers, and
retained side stores. It additionally proves refusal for missing ordinary
locks, partial/empty locks, other explicit identities, storage dimension
conflict, node-stamp conflict, a synthetic owner registry, and an unexpected
durable workspace artifact.

```text
TESTS_RUN =
  tests/test_real_root_typed_evidence_adapter.py
  tests/test_held_freeze_corrective_evidence_capture.py
  tests/test_root_writer_freeze_evidence.py
  tests/test_substrate_character_seed_continuity.py
  tests/test_substrate_legacy_identity_admission.py
  tests/test_substrate_root_admission_description.py
  tests/test_p9d_i4b1_external_precommit_owner_parity.py
  tests/test_substrate_migration_runtime_readiness.py
  tests/test_substrate_generalized_runtime_readiness.py
  tests/test_substrate_workspace_runtime_readiness.py
  tests/test_substrate_representations.py
  tests/test_substrate_legacy_representation_admission.py
  tests/test_substrate_migration_runtime_representation_bootstrap.py

TEST_RESULT = 167 passed, 2 skipped
```

The two skipped tests are platform-dependent symlink cases. All exercised
source trees were disposable pytest fixtures.

```text
REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
READY_FOR_FINAL_PRACTICAL_REAL_CAPTURE = YES
```
