# TORMENT Memory Substrate — 7G5D1 Formal Administration 001 Harness Failure

## Immutable administration record

This document closes, but does not alter, the consumed formal administration
`7g5d1-core-formal-20260831-001`.  The administration is permanently consumed:
it must not be rerun, reused, repaired in place, or reclassified.

| Field | Value |
| --- | --- |
| Repository HEAD | `6e17c50c5affcac90ec98515f4a6f9c8437c2b5d` |
| Administration ID | `7g5d1-core-formal-20260831-001` |
| Marker path | `C:\\TORMENT\\experiments\\7g5d1_core_formal_administration_20260831_001\\.7g5d1-core-formal-20260831-001.administration-started.json` |
| Marker SHA-256 | `796A549C7A962330C9C54A81B5DD02AB45CCA81B22C34C20983728E1EE5D8CC7` |
| Result path | `C:\\TORMENT\\experiments\\7g5d1_core_formal_administration_20260831_001\\result\\result.json` |
| Result SHA-256 | `49F98CBBD6515B1238C11731BCA32C0FC407B815A4259C28A10433E34DF45CAD` |
| Work-root SHA-256 | `414d6b9c7622972b57e2e60c46933861d3947f6c0e3b0cb5f1236c6e09f8f1d5` |
| Legacy contact count | `1` |
| Native formal event count | `1` |

The raw external evidence remains immutable.  This document does not copy,
edit, or reformat its `result.json`.

## Recorded outcome

```text
HARNESS_VALIDITY = EXPERIMENT_HARNESS_FAILURE
SCIENTIFIC_STORAGE_VERDICT = NOT_ESTABLISHED
SCIENTIFIC_POST_WRITE_VERDICT = NOT_ESTABLISHED

M1_RESULT = NOT_EMITTED
M2_RESULT = NOT_REACHED
M3_RESULT = NOT_REACHED
M4_RESULT = NOT_REACHED
M5_RESULT = NOT_REACHED
SEQUENTIAL_RESULT = NOT_REACHED
CHARACTER = NOT_ADMINISTERED

ERROR_TYPE = AttributeError
ERROR = 'types.SimpleNamespace' object has no attribute 'domain_policies'
```

## Root cause and repair boundary

`formal_core_ports.py` reused `real_n0._configuration(plan, lane)` for live
native formal execution.  That configuration was intentionally created for
B5/readiness construction and includes inert external placeholders, including
`owner = SimpleNamespace()`, `workspace = SimpleNamespace()`, and
`identity = SimpleNamespace(seed={})`.

B5 never called the post-write adapter.  It therefore truthfully established
`POST_WRITE_ADAPTER_CONSTRUCTIBLE = YES`; it did not establish
`POST_WRITE_ADAPTER_EXECUTABLE_WITH_FORMAL_EXTERNAL_DEPENDENCIES = YES`.
During M1, `NativeFabricPostWriteAdapter._validate_profile_pre_effect()` read
`ext.workspace.domain_policies`, correctly exposing the missing live external
dependency.

```text
ROOT_CAUSE_CLASSIFICATION = FORMAL_NATIVE_POST_WRITE_EXTERNAL_DEPENDENCY_BINDING_DEFECT
FIX_SCOPE = EXPERIMENT_ONLY
D1_CORE_FORMAL_V1 = INVALID_HARNESS_ADMINISTRATION
D1_CORE_FORMAL_SUCCESSOR = NOT_YET_AUTHORIZED
```

No B1/B2/B3/B4/B5 semantic claim is changed by this closure.  Any future
administration requires separately authorized successor instrumentation, a new
repository HEAD, a new administration ID, and separate work and result roots.
