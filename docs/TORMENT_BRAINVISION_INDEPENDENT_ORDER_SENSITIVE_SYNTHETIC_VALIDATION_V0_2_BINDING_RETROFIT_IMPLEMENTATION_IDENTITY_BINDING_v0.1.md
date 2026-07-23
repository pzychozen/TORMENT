# TORMENT Brainvision Independent Order-Sensitive Synthetic Validation v0.2 Binding-Retrofit Implementation Identity-Binding v0.1

## 0. Document class and status

```text
document_class                         = binding-retrofit implementation identity-binding record (docs-only)
lane                                   = Stage S3B v0.2 independent order-sensitive synthetic validation
authority_created                      = none
code_modified                          = none
tests_modified                         = none
schema_contract_modified               = none
prior_docs_modified                    = none
result_paths_created                   = none
git_mutations                          = none
runner_executed                        = false
runner_imported                        = false
real_manifest_contact                  = none
execution_authorization_drafted        = false
later_execution_authorization_identity = UNBOUND
scientific_result_published            = false
record_review_state                    = proposed binding in untracked draft
effective_repository_binding           = false until accepted commit and synchronization
```

This document is docs-only, non-executing, non-authorizing, pre-contact, non-production, and non-kernel. While it remains uncommitted, it is a proposed identity-binding and supersession record for the accepted Stage S3B v0.2 authorization-binding retrofit. It creates no execution authority, authorizes no runner invocation, performs no real-manifest contact, and does not draft the final execution-authorization document.

After acceptance, commit, push, and synchronization as `HEAD == origin/main` with a clean working tree, this record may serve as the repository binding for the revised implementation identities recorded below. It does not calculate or bind `later_execution_authorization_identity`.

All current prohibitions remain active and unchanged:

```text
FORMAL_HOLD                              = active
Mode_0                                   = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
authoritative v0.2 CLI execution         = prohibited
real frozen Stage S1 manifest contact    = prohibited
authority consumption                    = prohibited
scientific publication                   = prohibited
final execution authorization            = absent
explicit Hilmir execution order          = not given
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Purpose and authority boundary

This document records the authoritative post-commit implementation identities for the accepted binding retrofit, supersedes the dormant runner and runner-test identities, preserves the unchanged schema-contract identity, preserves the accepted semantic configuration and manifest identities, and does not authorize execution or manifest contact.

In scope:

```text
- bind the post-commit runner implementation identity
- bind the post-commit runner-test identity
- reconfirm the unchanged schema-contract identity
- explicitly supersede the old dormant runner and runner-test identities
- preserve the accepted v0.2 configuration identity
- preserve the accepted expected manifest identities
- record the current no-execution authority state
```

Out of scope:

```text
- no Stage S3B v0.2 execution
- no real frozen-manifest contact
- no authority consumption
- no scientific evaluation
- no result publication
- no final execution-authorization document
- no calculation of later_execution_authorization_identity
```

## 2. Authoritative implementation commit

Calculated synchronized repository state:

```text
branch                = main
implementation commit = 0b57a262384b5c6e588d69187de0c088654cfcab
commit subject        = research(brainvision): retrofit synthetic validation v0.2 authorization binding
HEAD                  = origin/main
working tree          = clean
```

The identity calculations in this record were performed from the authoritative Windows working tree at the synchronized commit above. No temporary copy, alternate checkout, editor buffer, cloud-staged copy, or container-mounted mirror was used.

## 3. Revised runner identity

```text
path              = research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
Git blob          = c2dcdc25cc3e057bf63a49ccf8f4584e5ca20e5f
raw SHA-256       = 8e2fdbe5a10c0351d485cb4b650143b9aa61fb1a16c28e0de6e7caf1daf893e6
byte length       = 80385
line-ending form  = LF-only
CR count          = 0
LF count          = 1991
terminal LF       = true
```

The revised runner raw SHA-256 matches the pre-commit corroborating review observation for the accepted retrofit bytes.

## 4. Revised runner-test identity

```text
path              = research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
Git blob          = 2f2189560f0c6a481594d1d7fe7fe46d036a0c92
raw SHA-256       = d7d1e82cfa64eededbb3e989e11675f44a0b870756161440291ab4524c9e5462
byte length       = 73530
line-ending form  = LF-only
CR count          = 0
LF count          = 1795
terminal LF       = true
```

The revised runner-test raw SHA-256 matches the pre-commit corroborating review observation for the accepted retrofit bytes.

## 5. Unchanged schema-contract identity

```text
path              = research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
Git blob          = a37b818609ba7be24105776e2d83d82773909727
raw SHA-256       = ce57ae583a631da8255b6d87ddcea64346c378a70c54aeb3d2827247e2584986
byte length       = 27751
line-ending form  = LF-only
CR count          = 0
LF count          = 735
terminal LF       = true
```

The schema-contract identity is unchanged and remains the accepted runner-external schema-contract identity for the v0.2 lane.

## 6. Explicit supersession

The old dormant runner identity is superseded:

```text
old runner Git blob    = c8f8eb525ffea16c2a15ec3a2d1b94af4425824f
old runner raw SHA-256 = 01d289e7ee83488c51f8cbb3472eb778c3ec7703491e08ceaa1ca28d0ee08898
```

The old dormant runner-test identity is superseded:

```text
old runner-test Git blob    = fe20088acff77aa5345c9af7d06abb0783a4ef61
old runner-test raw SHA-256 = 3ef6bd8318b3bea42ccc92889d486903392bb02cd8a802d02aa3d0a371ab2120
```

These old identities describe only the dormant pre-retrofit implementation. They must not appear as the accepted runner or runner-test identities in the future execution authorization.

## 7. Preserved semantic identities

The following accepted semantic identities remain valid and unchanged:

```text
v0_2_configuration_identity =
fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9

expected_manifest_external_sha256 =
05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404

expected_manifest_payload_sha256 =
56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
```

No real manifest byte was contacted, opened, copied, parsed, hashed, or evaluated while preparing this record.

## 8. Review status

```text
bounded modified-suite result             = 116 passed
precedent suites                          = 45 passed
independent adversarial review verdict    = ACCEPT
```

The reproducible Windows pytest/Git subprocess access-violation diagnostic is recorded accurately:

```text
pytest returned exit 0
functional tests passed
no source-level implementation defect was found
classified by independent review as an environment/toolchain anomaly
must be rechecked before the eventual authoritative invocation
does not authorize execution
```

This diagnostic is not omitted and is not interpreted as a scientific failure.

## 9. LF/CRLF operational note

```text
authoritative raw identities bind literal working-tree bytes
current authoritative files were calculated from LF-only bytes
core.autocrlf=true may create future operational byte conversion
any conversion causes fail-closed raw SHA-256 mismatch
```

The final execution authorization must bind the same literal byte form that will exist at execution. This record does not modify `.gitattributes` or Git configuration.

## 10. Current authority state

```text
retrofit implemented                  = true
retrofit committed and synchronized   = true
revised identities calculated         = true
revised identities docs-bound         = pending until this document is committed
final execution authorization         = absent
later_execution_authorization_identity = UNBOUND
authoritative execution authorized    = false
real manifest contact authorized      = false
authority consumption authorized      = false
scientific publication authorized     = false
```

## 11. Next permitted phase

After this identity-binding document is reviewed, committed, pushed, and synchronized, the next permitted work is:

```text
prepare the final Stage S3B v0.2 execution-authorization specification
construct the exact future binding block
calculate later_execution_authorization_identity
independently verify the canonical authorization payload
```

Completion of those steps will not itself constitute Hilmir's explicit one-run execution order. The explicit one-run execution order remains a separate future authority decision.

## 12. Non-authorization closure

This document does not create the final execution-authorization document, does not insert a provisional final authorization binding block, does not calculate `later_execution_authorization_identity`, does not claim execution authority exists, does not authorize real-manifest contact, does not authorize authority consumption, does not authorize publication, does not reinterpret the historical frozen F3 result, does not modify prior documentation, does not modify source or tests, does not modify the schema contract, and does not create a launcher or wrapper.

End of identity-binding and supersession record.
