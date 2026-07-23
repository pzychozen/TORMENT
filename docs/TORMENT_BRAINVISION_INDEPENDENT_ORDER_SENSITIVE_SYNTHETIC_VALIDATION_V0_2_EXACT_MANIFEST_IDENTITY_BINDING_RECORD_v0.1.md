# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Exact-Manifest Identity-Binding Record v0.1

## 0. Document class and draft status

```text
document_class                        = proposed exact-manifest identity-binding record (docs-only)
lane                                  = Stage S3B v0.2 independent order-sensitive synthetic validation
authority_created                     = none
code_modified                         = none
tests_modified                        = none
frozen_evidence_modified              = none
prior_docs_modified                   = none
result_paths_created                  = none
git_mutations                         = none
runner_executed                       = false
runner_imported                       = false
fixture_freezer_invoked               = false
verifier_or_descriptor_invoked        = false
real_manifest_contact                 = none
hashes_calculated_from_manifest_bytes = false
identities_recovered_from_committed_evidence = true
effective_exact_manifest_binding      = false until accepted commit + push + synchronization
execution_authorization_drafted       = false
scientific_result_published           = false
```

This document is **docs-only, non-executing, non-authorizing, pre-contact, non-production, non-kernel**. While it remains uncommitted, it is a proposed exact-manifest identity-binding record: it records accepted proposed values for the two exact frozen Stage S1 manifest identities required by the Stage S3B v0.2 runner, recovering them from committed authoritative evidence with zero real-manifest contact. It creates no execution authority, authorizes no runner invocation, and leaves the later execution-authorization identity `UNBOUND`.

After activation under §10, "bound by this record" fixes the accepted value for use by the later v0.2 execution-authorization phase. Before activation, the effective binding state is false. Activation does **not** modify the runner's `UNBOUND` source constants.

All current prohibitions remain active and unchanged:

```text
FORMAL_HOLD                             = active
Mode_0                                  = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
authoritative v0.2 CLI execution        = prohibited
real frozen Stage S1 manifest contact   = prohibited
scientific publication                  = prohibited
execution authorization                 = not present
explicit Hilmir execution order         = not given
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Governing synchronized state

Draft base state before this target document was created:

```text
repository     = torment_fabric
branch         = main
HEAD           = origin/main
HEAD commit    = dfcb205f2f644290fcc1271e85f34d516aed6fd1
working tree   = clean
```

Current review state:

```text
branch         = main
HEAD           = origin/main = dfcb205f2f644290fcc1271e85f34d516aed6fd1
working tree   = clean except the one expected untracked target document
untracked      = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXACT_MANIFEST_IDENTITY_BINDING_RECORD_v0.1.md
```

Current binding-record commit (the prior effective bindings this record extends):

```text
commit  = dfcb205f2f644290fcc1271e85f34d516aed6fd1
subject = docs(research): bind synthetic validation v0.2 identities
```

## 2. Purpose and scope

### 2.1 In scope

```text
- record the successful non-contact discovery of the two exact frozen manifest identities
- record accepted proposed values for expected_manifest_external_sha256 (final external file-byte hash)
- record accepted proposed values for expected_manifest_payload_sha256 (final canonical-payload hash)
- define the activation rule under which those values become effective bindings
- establish authoritative provenance and lineage from committed evidence
- distinguish these identities from every other hash in the lane
- preserve zero real-manifest contact
- prepare the lane for a separately reviewed v0.2 execution-authorization document
```

### 2.2 Out of scope (explicitly not done here)

```text
- no execution authority is created
- no runner invocation, fixture-freeze, verifier, evaluator, or descriptor call is performed or authorized
- no real frozen manifest byte is opened, read, hashed, parsed, copied, inspected, or stat-ed
- no arming/journal/staging/result/publication path is created
- no runner identity constant or prior document is modified
- the later_execution_authorization_identity is left UNBOUND
- no execution-authorization document is drafted
- no scientific PASS or FAIL is claimed
- no Git mutation is performed
```

## 3. Non-contact discovery method

The two exact-manifest identities were recovered from committed authoritative evidence, not by contacting the real frozen manifest.

```text
recovery source            = committed freeze-lane evidence (docs findings + v0.1 runner source constants)
real manifest contact during discovery      = false
hashes newly calculated from manifest bytes  = false
identities recovered from committed evidence = true
tooling                    = read-only static review of committed text
git mutations              = none
read-only Git inspection   = permitted for review/provenance; not real-manifest contact
```

The real frozen manifest file (`…/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json`) was not opened, read, hashed, parsed, copied, inspected, or stat-ed for this record. The identities already exist as authoritative retained values in committed evidence; they are transcribed here verbatim, not recomputed.

## 4. Authoritative freeze evidence

Primary authoritative evidence:

```text
document = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_FINDINGS_v0.1.md
authoritative evidence commit = cae2f640896de1a0c06ce4c11cc59014424929ae
```

Confirmed exact lines from the synchronized checkout (§5 "Published artifact set and identities"):

```text
line 166  (results directory) research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/
line 169  independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json   <- external manifest file
line 177  manifest_payload_sha256  = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
line 178  external_manifest_sha256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
line 179  configuration_sha256     = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263   (distinct; see §8)
```

The reviewer confirmed lines 169, 177, and 178 directly from the repository rather than trusting a summary; the discovery-audit references (external identity: findings lines 169 and 178; canonical payload identity: findings line 177) are accurate.

## 5. Exact external-manifest identity

```text
expected_manifest_external_sha256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
```

Semantic meaning:

```text
SHA-256 of the final published frozen manifest's external file bytes
```

Authoritative evidence:

```text
freeze findings line 178  external_manifest_sha256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
freeze findings line 169  names the external manifest file to which this hash applies
corroboration (v0.1 runner) line 60  EXTERNAL_MANIFEST_SHA256 = "05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404"
```

Binding state before activation: **ACCEPTED PROPOSED BINDING VALUE**; effective binding remains false until activation per §10. After activation, this value becomes **BOUND BY THIS RECORD**.

## 6. Exact canonical-payload identity

```text
expected_manifest_payload_sha256 = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
```

Semantic meaning:

```text
SHA-256 of the final published frozen manifest's canonical payload bytes
```

Authoritative evidence:

```text
freeze findings line 177  manifest_payload_sha256 = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
corroboration (v0.1 runner) line 61  MANIFEST_PAYLOAD_SHA256 = "56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9"
```

The canonical payload is the manifest object with only its own `manifest_payload_sha256` field excluded, with original key order preserved. This projection rule is defined by the frozen fixture-freeze lane in `research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py` (`_payload_projection`, lines 202-213), which is serialized by compact fixed-key-order UTF-8 JSON with `ensure_ascii=True`, `separators=(",", ":")`, `allow_nan=False`, and exactly one terminal LF (`_canonical_json_bytes`, lines 193-199). The v0.2 schema contract independently preserves the same projection and serialization rule in `research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py` (lines 266-268 and 297-306). The recorded `56a141bd...` value semantically matches that final published manifest canonical-payload projection as recorded in the freeze findings line 177; it was not recalculated here from manifest bytes.

Binding state before activation: **ACCEPTED PROPOSED BINDING VALUE**; effective binding remains false until activation per §10. After activation, this value becomes **BOUND BY THIS RECORD**.

## 7. Corroborating evidence and lineage

Corroborating committed material (lineage/semantic consistency only; the freeze findings remain the primary authoritative source):

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
  lines 56-59  MANIFEST_PATH = research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/
                               independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
  line 60      EXTERNAL_MANIFEST_SHA256 = "05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404"
  line 61      MANIFEST_PAYLOAD_SHA256  = "56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9"
  lines 63-65  EXPECTED_MANIFEST_SCHEMA = torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1
```

(The v0.1 scientific execution logic was not inspected or reused; only these frozen identity/route constants were read.)

### 7.1 Single-manifest lineage

Both exact-manifest identities refer to the **same** final published manifest:

```text
research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
```

Lineage is established through committed findings (freeze findings §5, which lists exactly one published external manifest file and one authoritative pair of external/payload identities) and the corroborating frozen v0.1 validation constants (which bind the same path and the same two values) — **not** by reopening the real manifest. The external hash (05ce02af…) is the whole-file byte hash of that manifest file; the payload hash (56a141bd…) is the canonical-payload hash of the same manifest's projected content. They are two identities of one artifact.

## 8. Hash-semantic distinctions

All of the following are distinct and non-interchangeable:

```text
expected_manifest_external_sha256
  = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
  = final manifest external file-byte hash

expected_manifest_payload_sha256
  = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
  = final manifest canonical-payload hash

expected_freeze_configuration_sha256
  = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
  = fixture-generation configuration commitment (freeze findings line 179; v0.1 runner line 62)
  = NOT an exact-manifest identity

pass-bundle payload / external SHA-256 (freeze execution evidence)
  = payload  dc43fa2836362d3e73c2121c421be732c944cb94700630bf475240beeb6d9d1e   (freeze findings line 185)
  = external 00ef48224f4effaf0fbdbc7264b0676bd6bfafe168496166e9dcca578ddbd942   (freeze findings line 186)
  = separate freeze-execution evidence identities; different-by-construction (freeze findings line 189)
  = NOT either exact-manifest identity

v0_2_configuration_identity
  = fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
  = configured v0.2 validation-operation identity (bound by the prior record at dfcb205)
  = NOT a manifest hash

Git blob identities (SHA-1 of committed implementation objects)
  = runner c8f8eb525ffea16c2a15ec3a2d1b94af4425824f
  = schema-contract a37b818609ba7be24105776e2d83d82773909727
  = runner-test fe20088acff77aa5345c9af7d06abb0783a4ef61
  = SHA-1 identities of committed implementation objects
  = NOT manifest SHA-256 identities
```

No entry above may be described as interchangeable with any other. In particular, the pass-bundle hashes and the freeze-configuration commitment are not the final exact-manifest identities, and the exact-manifest identities are not Git blob identities.

## 9. Contradiction search

The non-contact discovery checked committed evidence for competing values:

```text
alternate final external-manifest hashes  = none found (only 05ce02af… as the final external identity)
alternate final canonical-payload hashes  = none found (only 56a141bd… as the final payload identity)
stale or superseded values                = none found
test placeholders                         = present only as non-authoritative bounded-test stubs
                                            (the v0.2 test uses obvious filler such as "e"*64 / "f"*64);
                                            these are not authoritative retained values
pass-bundle hashes                        = present and clearly labelled distinct (freeze findings 185-186)
configuration hashes                      = present and clearly labelled distinct (5f3a568b…)
unrelated manifest / source hashes        = the freeze findings "Windows raw SHA-256" values (lines 91-120)
                                            and descriptor identities are source-file identities, not manifest hashes
```

Result:

```text
no contradictory authoritative retained value was found
```

The Stage S3B v0.2 runner's source values `expected_manifest_external_sha256 = UNBOUND` and `expected_manifest_payload_sha256 = UNBOUND` are classified as **lifecycle placeholders**, not contradictory hash values. They mark identities that were intentionally deferred to this binding phase, consistent with the governing documents.

## 10. Binding activation and invalidation

### 10.1 Activation

```text
The exact-manifest identity bindings defined by this record become effective only when the exact accepted
document is committed to main, pushed, and synchronized with HEAD == origin/main and a clean working tree.

Before that event, the document is a proposed binding record and creates no authoritative repository binding.
```

This record does not predict or embed its own future commit hash. Once activated, it binds the two values for use by the later v0.2 execution-authorization phase; it does not modify the runner's `UNBOUND` source constants and does not embed or predict the activation commit hash.

### 10.2 Invalidation

```text
The binding applies only to the exact retained Stage S1 manifest lineage identified by the authoritative
freeze findings and the repository-relative manifest path recorded in §7.

If later authoritative evidence establishes that the retained manifest artifact changed, was replaced, or
belongs to another lineage, these bindings are invalid for future authorization and must be reviewed again.
```

Ordinary, unrelated documentation commits do **not** invalidate these manifest identities; only authoritative evidence that the retained manifest artifact itself changed, was replaced, or belongs to another lineage does.

## 11. Complete runner identity-gate state

The Stage S3B v0.2 runner pre-contact identity-gate inventory:

```text
later_execution_authorization_identity
runner_git_blob
runner_raw_sha256
runner_test_git_blob
runner_test_raw_sha256
schema_contract_git_blob
schema_contract_raw_sha256
expected_manifest_external_sha256
expected_manifest_payload_sha256
v0_2_configuration_identity
```

Required state after this record becomes effective:

```text
runner implementation identities          = BOUND (prior record, dfcb205)
runner-test implementation identities     = BOUND (prior record, dfcb205)
schema-contract implementation identities = BOUND (prior record, dfcb205)
v0_2_configuration_identity               = BOUND (prior record, dfcb205)
expected_manifest_external_sha256          = BOUND IN THIS RECORD
expected_manifest_payload_sha256           = BOUND IN THIS RECORD

later_execution_authorization_identity     = UNBOUND
authoritative execution                    = NOT AUTHORIZED
```

## 12. Non-circular identity hierarchy

The following acyclic dependency structure is preserved:

```text
configuration payload
    -> v0_2_configuration_identity

implementation bytes
    -> implementation identities

committed authoritative freeze evidence
    -> recovery and binding of the already-recorded exact-manifest identities

exact retained manifest bytes
    -> original external/payload identities recorded by the freeze lane

configuration identity
+ implementation identities
+ exact-manifest identities
    -> later execution-authorization document

accepted execution authorization
+ synchronized authorized execution HEAD
+ explicit Hilmir execution order
    -> authoritative invocation
```

This binding record does not contain its own future commit identity as an input to either manifest hash. The two exact-manifest identities were fixed by the freeze lane from the retained manifest bytes; this record only recovers those already-recorded values from committed evidence and, after activation, binds them for the later authorization phase, so no dependency points forward from this record's future commit back into either hash.

## 13. Authority and contact accounting

```text
real frozen manifest contact              = none
controlled-contact authorization          = unnecessary for current identities
runner execution                          = false
fixture-freeze / verifier / descriptor    = not invoked
scientific evaluation                     = none
scientific result published               = false
execution authorization                   = absent
later_execution_authorization_identity    = UNBOUND
explicit Hilmir execution order           = not given
git mutations                             = none
read-only Git inspection                  = permitted for review/provenance; not real-manifest contact
```

Controlled real-manifest contact is **unnecessary for these identities** because authoritative committed values were found in the freeze findings and corroborating v0.1 constants. This is a statement about the current identities only; it does not declare controlled contact universally forbidden forever. Any future need for real-manifest contact remains subject to explicit authorization.

## 14. Permanent boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

Brainvision = offline
Brainvision = quarantined
Brainvision = non-production
Brainvision = non-service
Brainvision = non-kernel
Brainvision = non-memory-integrated
```

This record does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 15. Required next phase

After this document is independently reviewed, accepted, committed, pushed, and synchronized, the next separately reviewed phase is:

```text
1. Prepare the docs-only Stage S3B v0.2 execution-authorization specification.
2. Bind the authorization to the complete accepted identity set.
3. Define the non-circular authorized execution-HEAD rule.
4. Perform a final adversarial pre-contact review.
5. Obtain a new and explicit Hilmir execution order.
6. Only then permit an authoritative runner invocation.
```

That authorization is **not** drafted in this task.

## 16. Final status

```text
record review state                = proposed exact-manifest identity-binding record / pending review until accepted
effective exact-manifest binding    = false until accepted commit, push, and synchronization
expected_manifest_external_sha256  = ACCEPTED PROPOSED BINDING VALUE = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
expected_manifest_payload_sha256   = ACCEPTED PROPOSED BINDING VALUE = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
manifest lineage                   = single final published manifest (research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json)
non-contact discovery              = confirmed (real manifest contact = none)
contradiction search               = no contradictory authoritative retained value found

prior effective bindings           = schema-contract / runner / runner-test implementation identities + v0_2_configuration_identity (dfcb205)
later_execution_authorization_identity = UNBOUND
EXECUTION_AUTHORIZATION_PRESENT    = false
AUTHORITATIVE_EXECUTION_AUTHORIZED = false
REAL_MANIFEST_CONTACT_AUTHORIZED   = false
SCIENTIFIC_PUBLICATION_AUTHORIZED  = false

NEXT_PHASE = SEPARATE_DOCS_ONLY_V0_2_EXECUTION_AUTHORIZATION
```

Activation-result state, only after §10 succeeds:

```text
expected_manifest_external_sha256 = BOUND BY THIS RECORD
expected_manifest_payload_sha256  = BOUND BY THIS RECORD
later_execution_authorization_identity = UNBOUND
execution authorization = absent
authoritative invocation = prohibited
```

All prohibitions in §0 remain active and unchanged. This proposed record defines the two exact-manifest identity bindings and their activation rule only; it authorizes no execution and no real-manifest contact, and it does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.
