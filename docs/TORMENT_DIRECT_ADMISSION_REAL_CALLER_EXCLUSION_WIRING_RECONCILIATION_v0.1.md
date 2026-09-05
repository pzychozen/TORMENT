# TORMENT direct admission real-caller exclusion wiring reconciliation

```text
STARTING_HEAD = 9a092dc8131bab23b414e35c446baa314de81961
AUDIT_MODE = STATIC_CALLER_WIRING_RECONCILIATION
REAL_ROOT_CONTACT = NONE
PROCESS_CONTACT = NONE
SQLITE_WRITE = NONE
```

## Recovered failed caller

The retained direct-administration command history is the only available
failed-run caller; no committed runner/helper or repository shell script
constructed that adapter.  Its construction was exactly:

```text
RealRootTypedEvidenceAdapter(
  data_root_identity = TORMENT_REAL_ROOT_DIRECT_ADMISSION_P1_20260905
  operator_identity = OPERATOR_AUTHORIZED_DIRECT_REAL_ADMISSION_P1
  excluded_source_artifacts = ()  # constructor default, not supplied
  excluded_alternate_roots = ()   # constructor default, not supplied
)
```

Therefore the failed direct preparation had not bound any of the already
established qualified-root exclusions.

```text
FAILED_REAL_CALLER_CONFIGURATION_RECOVERED = YES
KNOWN_EXCLUSION_nodes_jsonl_CONFIGURED = NO
KNOWN_EXCLUSION_emb_1_npy_CONFIGURED = NO
KNOWN_EXCLUSION_lived_use_CONFIGURED = NO

DIRECT_REAL_CALLER_EXCLUSION_WIRING = FAIL
ROOT_GRAMMAR_NEW_ARTIFACT_PROVEN = NO
```

The generic refusal at root-child validation cannot distinguish this omitted
configuration from a newly discovered artifact.  This audit makes no claim
that a new production-root artifact exists.

## Bounded repair

`build_real_direct_admission_source_adapter(...)` is now the explicit caller
configuration seam in `torment_service.substrate.real_root_typed_evidence`.
It constructs only these root-specific existing exclusions:

```text
ExcludedSourceArtifactLocator("nodes.jsonl", "TOP_LEVEL_UNSCOPED_NODES")
ExcludedSourceArtifactLocator("emb_1.npy", "TOP_LEVEL_UNSCOPED_EMBEDDINGS")
ExcludedAlternateRootLocator("lived_use")
```

The first two role strings are the existing top-level unscoped-node and
unscoped-embedding roles from the typed-evidence qualification lane.  The
alternate-root locator retains its existing `ALTERNATE_SELECTED_ROOT` type
default.  The generic adapter defaults remain empty, so these names are not a
global source-grammar allowance.

```text
CODE_CHANGE_REQUIRED = YES
DIRECT_SOURCE_TO_ADMISSION_SEAM_CHANGED_SEMANTICALLY = NO
NEW_ROOT_ALLOWLIST_LAW = NO
NEW_HASH_LAW = NO
NEW_BYTE_IDENTICAL_LAW = NO
```

## Synthetic qualification

The added production-shaped fixture uses exactly the three established
top-level names plus `workspaces/`.  It proves:

```text
CONFIGURED_FACTORY_DIRECT_PREPARATION = PASS
nodes.jsonl_OMITTED = REFUSE
emb_1.npy_OMITTED = REFUSE
lived_use_OMITTED = REFUSE
UNEXPECTED_FOURTH_ROOT_ARTIFACT = REFUSE
lived_use_DESCENDANTS_ENUMERATED = NO
lived_use_DESCENDANTS_READ_OR_HASHED = NO
GENERIC_ADAPTER_DEFAULT_EXCLUSIONS = EMPTY
```

Focused tests under command prompt `conda activate torment`:

```text
tests/test_real_root_typed_evidence_adapter.py
  26 passed, 1 skipped

tests/test_root_writer_freeze_evidence.py
tests/test_substrate_root_admission_description.py
tests/test_post_i4_generalized_root_blocker5_binding.py
  36 passed, 1 skipped
```

The normal pytest cache warning on this host was non-functional; the specified
test basetemp directories were used.

## Resulting boundary

```text
P1_STAGING_BOOTSTRAP = NOT_EXECUTED
ROOT_ADMISSION_ENVELOPE = NOT_PERSISTED
SELECTOR_CHANGE = NONE
NORMALIZATION = NOT_EXECUTED
P6 = NOT_EXECUTED
P7 = NOT_EXECUTED

READY_TO_RETRY_DIRECT_REAL_PREPARATION_AND_P1 = YES
```

`YES` authorizes no automatic retry.  It means the identified caller
configuration defect has a synthetically qualified, explicit repair; a new
real preparation still requires its own fresh operator-authorized writer and
source-stability procedure and must stop on any subsequent typed refusal.
