# I11: a fresh root requires explicit Native Genesis

Accepted starting commit: `25bc037173099e7d25e8f9e438805e0a60aadd70`.
The I10C real-service fresh-install qualification remains accepted. I11 does
not repeat its BGE qualification or change any Genesis contract.

## Decision

Absence of a selector is not evidence of an existing legacy installation.
When both selector artifacts are absent, the deployment resolver first retains
the existing Genesis fence and controlled-core checks, then reads installation
presence. A fresh root is refused with `fresh-root-requires-native-genesis`.
An existing legacy witness retains `LEGACY_PUBLIC`, now with reason
`pre-selector-existing-legacy`. Unknown or invalid evidence is refused with
`pre-selector-root-ambiguous-or-invalid`. Reasons contain no private paths.

The new helper is filesystem inspection only. It never opens SQLite, constructs
Fabric, Workspace, MemoryGraph or an embedder, invokes migration, repairs data,
or creates Genesis. Explicit `LEGACY_ACTIVE` selector authority bypasses this
presence helper. Historical v1, root-v2 and active Genesis agreement logic,
including profile verification, is unchanged.

## Historical evidence and qualified presence grammar

Presence is satisfied by at least one of the following witnesses beneath the
normal `workspaces/<workspace>` hierarchy. These are existing formats, not a new
legacy manifest. Additional historical side files remain allowed. This proves
installation presence; it is not a whole-root integrity audit or admission.

1. **Workspace ownership.** A regular `workspace_meta.json` JSON object whose
   `workspace_id` exactly matches the containing directory. If `domains.json`
   exists, it must be an object containing a list of nonempty domain strings;
   an empty list is lawful. Neither optional representation metadata nor exact
   Genesis-era key closure is required. The historical identity-only payload
   is explicitly exercised by `tests/test_identity_collision_f7.py` and accepted
   by `fabric.py::_verify_workspace_identity_before_initialization`. The
   permissive load/init methods preserve missing domains and optional metadata.
   Later five-field workspace metadata plus domains covers declared but empty
   shared scopes as well as populated installations.
2. **Metadata-less per-EID graph.** In
   `agents/<agent>/private` or `domains/<domain>/shared`, a nonblank `nodes.jsonl`
   object with a nonnegative integer EID (including zero), and a dictionary
   payload when present, paired with its regular `emb_<eid>.npy`. The NPY must
   be a one-dimensional, positive-length, non-object float array with a valid
   v1/v2/v3 header and matching total file length. No vector is loaded or
   embedded. `tests/test_substrate_metadata_less_per_eid_legacy_source.py`
   contains the concrete metadata-less private source witness. MemoryGraph's
   `_load` and `_emb_path` establish the runtime format; Workspace constructs
   the same MemoryGraph storage beneath the shared-domain hierarchy.
3. **Materialized shard storage, including empty scopes.** In either canonical
   scope hierarchy above, regular `embeddings/manifest.json` with the existing
   v1 integer fields (`version`, `embedding_dim`, `rows_per_shard`,
   `active_shard`, `next_row`, `total_rows`), dtype `float32`, positive dimensions,
   nonnegative shard/counters, `0 <= next_row <= rows_per_shard`, and
   `total_rows = active_shard * rows_per_shard + next_row`; plus the named active
   `shard_<six-digit-minimum-index>.npy` with matching two-dimensional shape,
   float32 element width and file length. These are the storage owner and array
   written by `embedding_store.py::EmbeddingShardWriter`. Empty storage does
   not require a node log or map file: they are created on the first write.

Bounded archaeology also inspected the frozen D1 legacy-only fixture inventory
(`concrete_core_legacy_only_fixture_set_20260831.json`), which records workspace
owners, populated private shards and an empty shared shard without a map file.
The real-root typed evidence fixtures separately distinguish empty private,
declared shared, populated scopes and metadata-less import sources. Their
synthetic `workspace` alias is migration fixture vocabulary, not the current
runtime's `workspace_id` identity owner; it is not adopted as startup authority.
Migration qualifiers were inspected as evidence sources and are never called
by this helper or newly introduced into normal startup.

The helper rejects duplicate JSON keys, malformed witness types and redirected
evidence (including Windows reparse points). Traversal is limited to the fixed
workspace/scope depths, with a 32,768-entry inspection budget. JSON reads are
capped at 1 MiB and per-EID discovery at 128 node lines; NPY headers are capped
at 64 KiB. Failure to establish a witness within these bounds is ambiguous and
refused, not silently accepted. Arrays are header/length inspected, not scanned
for semantic validity. Ordinary runtime owners retain responsibility for data
integrity when loading a selected legacy installation.

## Fresh and empty legacy roots

Absent roots, empty directories, Genesis's allowed `README.md` / `.gitkeep`
files, and its fixed pre-intent control directories / root-onboarding lock are
fresh. Combinations of harmless files and those controls also remain fresh.
Genesis preparation records retain their earlier, higher-priority refusal.

An old default Fabric with no durable workspace or memory state cannot be
distinguished from a brand-new empty directory by its claimed history. It now
requires Native Genesis. Bare `workspaces/`, bare private/shared directories,
unrelated files, and inert native staging cores alone do not prove legacy
presence. Unrecognized nonempty residue is ambiguous and refused. No residue
is deleted or adopted. A genuinely materialized empty legacy scope has its
durable storage owner, and remains supported by the grammar above.

## Runtime and model boundary

`fabric.py`, `embeddings.py`, selector transition APIs, core maintenance, native
memory, Genesis I1-I9, root profile/membership, Character, Forge, Brainvision
and Hivemind implementation are unchanged.

The original I11-U stop was accepted as correct. The reviewed resume authorizes
the production `HashEmbedding` constructor for legacy compatibility. It remains
normal production code: no fake embedder is injected into the real constructor,
and no real embedding or conversational model is authorized. Resolver-only
qualification constructs no embedder. The successful legacy regression uses
the original metadata-less fixture shape, calls actual `create_public_runtime`
and actual `TormentFabric`, and records hash construction and embedding calls.
It does not request a semantic query or load a workspace to modernize metadata.
Normal legacy constructor effects are observed separately from the strictly
read-only presence check.

Normal `python -m torment_service` continues to call the existing startup-owned
runtime factory. A fresh-root refusal propagates through application startup
before Fabric, workspace metadata, graphs, embed locks or native authority can
be created. No service or Forge code change is required for this behavior.

## Downstream installation contract

```text
new installation
-> Character Creator declaration
-> Native Genesis local operator utility
-> qualified profile
-> normal service startup

FRESH_ROOT_REQUIRES_NATIVE_GENESIS = YES
EXISTING_LEGACY_PRESELECTOR_ROOT_SUPPORTED = YES
DURABLE_LEGACY_SELECTOR_SUPPORTED = YES
AUTOMATIC_FRESH_LEGACY_MATERIALIZATION = NO
AUTOMATIC_GENESIS_ON_SERVICE_START = NO
MIGRATION_SOURCE_QUALIFIER_CALLED_BY_NORMAL_STARTUP = NO
```

Character Creator must not rely on starting normal TORMENT on an empty root.
Forge implementation remains behind the next GPT review boundary.

## Qualification

Focused and bounded regression evidence is recorded in the I11 execution report.
Tests that expected absent/empty or source-free inert roots to be legacy-public
now assert refusal; their Genesis fence and core maintenance behavior is not
changed. Existing native fixtures retain their authority expectations. I9
regressions are selected to avoid deterministic test-embedder construction,
while preserving actual CLI creation/status and read-only/operator-file checks.

Older public-fencing and service/migration fixtures that bootstrapped fresh
legacy roots now supply explicit existing workspace owners before starting the
service. The service fixture prepares the existing production owner format only
on an absent/empty disposable root; it refuses to modernize metadata-less
historical state. These changes are test setup, not new production onboarding.
The old tests' subsequent scope creation, ingestion and admission assertions
are unchanged. I11 qualifies these fixture owners without running their broader
semantic-query or service/migration rehearsals, which are outside its model and
regression scope.

### Execution result — 2026-09-11

438 distinct checks passed, with zero failures, errors or skips:

- 40 classifier/public-runtime checks, including both actual fresh-root
  `python -m torment_service` refusals and actual historical legacy construction.
- 395 deployment, Genesis contracts/administration/recovery/activation,
  historical v1, root-v2, staging-bootstrap, public-factory and selected I9
  operator-utility regressions.
- 3 additional checks for the updated legacy fixture owners and the prohibition
  on modernizing an existing metadata-less fixture.

Two diagnostic reruns of the original 40 checks also passed: 518 passing test
executions in total, counting repeats. Production hash construction occurred
once per legacy-constructor test, with zero `embed()` calls each time. The
profile/trace audit runs independently observed the production constructors;
20 completed-process audit reports recorded no boundary violations or loaded
real-model modules. Fault-injection children that deliberately use `os._exit`
do not produce normal atexit reports. Native recovery fixtures use previously
committed literal vector data, not test embedder calls.

Fresh service processes exited through application startup refusal without
materializing their roots. The historical metadata-less constructor fixture
remained byte/file/mtime identical, with no workspace metadata added. Port 8787
was absent after verification. No production data root was contacted.

**Diagnostic caveat:** Windows printed `Windows fatal exception: access
violation` diagnostics while the audited processes continued and exited zero.
The same symptom was reproduced by an external standard-library-only file-read
test with no TORMENT imports; that control also passed. A control without the
external audit ran without the diagnostic, while both profiling and alternate
instrumentation runs could emit it. The exact host/audit cause remains
unresolved. Logs were retained; no runtime, embedding, or interpreter behavior
was patched or disabled to suppress them. The passing assertions and XML
results are reported separately from this diagnostic caveat.

External evidence directory:
`C:\Users\Notandi\AppData\Local\Temp\torment-native-genesis-i11-r4emiv_a\resume`.
It contains `verification.json`, exact test commands, pytest logs, JUnit XML,
audit reports and the standalone diagnostic controls. The original preflight
blocker record is retained in its parent directory. Git checks verified the
accepted baseline against live `origin/main`, all 210 unrelated untracked
entries, and unchanged protected production sources. Commands used Windows
CMD with `conda activate torment`.

```text
TORMENT_I11_LEGACY_FRESH_INSTALL_RETIREMENT = COMPLETE
I11_ORIGINAL_STOP = CORRECT
I11_EMBEDDER_BOUNDARY = CORRECTED
I10C_ACCEPTED_BASELINE = YES
SERVICE_LEVEL_FRESH_INSTALL_QUALIFIED = YES
PRESELECTOR_ROOT_CLASSIFIER = PASS
ABSENT_ROOT_CLASSIFICATION = FRESH_UNINITIALIZED
EMPTY_ROOT_CLASSIFICATION = FRESH_UNINITIALIZED
AMBIGUOUS_ROOT_CLASSIFICATION = REFUSED
EXISTING_LEGACY_POSITIVE_EVIDENCE = Matching workspace_id owner with valid domains when present; OR canonical node/per-EID float-NPY pair; OR v1 manifest/matching float32 active shard; exact grammar and bounds above
EXISTING_LEGACY_PRESELECTOR_ROOT = LEGACY_PUBLIC
PRESELECTOR_CLASSIFIER_WRITES = 0
PRODUCTION_HASH_EMBEDDER_CONSTRUCTED_FOR_LEGACY_REGRESSION = YES
PRODUCTION_HASH_EMBED_CALLS_FOR_CONSTRUCTION = 0
REAL_EMBEDDING_MODEL_INVOKED = NO
BGE_MODEL_INVOKED = NO
OLLAMA_EMBEDDING_INVOKED = NO
DETERMINISTIC_TEST_EMBEDDER_INVOKED = NO
CONVERSATIONAL_MODEL_INVOKED = NO
ABSENT_ROOT_LEGACY_PUBLIC = NO
EMPTY_ROOT_LEGACY_PUBLIC = NO
ABSENT_ROOT_MATERIALIZED = NO
EMPTY_ROOT_MATERIALIZED = NO
NORMAL_SERVICE_FRESH_ROOT_REQUIRES_GENESIS = YES
AUTOMATIC_GENESIS_ON_SERVICE_START = NO
DURABLE_LEGACY_SELECTOR_CHANGED = NO
HISTORICAL_V1_CHANGED = NO
ROOT_V2_CHANGED = NO
ACTIVE_GENESIS_CHANGED = NO
EXISTING_LEGACY_AUTO_MIGRATED = NO
MIGRATION_SOURCE_QUALIFIER_CALLED_BY_NORMAL_STARTUP = NO
PRODUCTION_ROOT_CONTACT = NO
PRODUCTION_RUNTIME_STARTED = NO
FORGE_CHANGED = NO
BRAINVISION_ACCESSED = NO
HIVEMIND_TOUCHED = NO
LEGACY_FRESH_INSTALL_COMPATIBILITY_REMOVED = YES
NEXT_AUTHORIZATION_BOUNDARY = GPT_REVIEW_OF_I11_THEN_RETURN_TO_CHARACTER_CREATOR
```
