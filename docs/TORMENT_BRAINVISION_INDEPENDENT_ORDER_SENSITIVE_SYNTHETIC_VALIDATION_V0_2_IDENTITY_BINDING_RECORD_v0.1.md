# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Identity-Binding Record v0.1

## 0. Document class and status

```text
document_class                        = identity-binding record (docs-only)
lane                                  = Stage S3B v0.2 independent order-sensitive synthetic validation
authority_created                     = none
code_modified                         = none
tests_modified                        = none
schema_contract_modified              = none
frozen_providers_modified             = none
prior_docs_modified                   = none
result_paths_created                  = none
git_mutations                         = none
runner_executed                       = false
runner_imported                       = false
real_manifest_contact                 = none
exact_manifest_identities_calculated  = none
execution_authorization_drafted       = false
scientific_result_published           = false
record_review_state                   = proposed binding in untracked draft
effective_repository_binding          = false until accepted commit and synchronization
```

This document is **docs-only, non-executing, non-authorizing, pre-contact, non-production, non-kernel**. While it remains untracked, it is a **PROPOSED BINDING IN UNTRACKED DRAFT**: it proposes accepted values for the completed Stage S3B v0.2 implementation-file identities and the independently reproduced v0.2 configuration identity, so that a later, separately reviewed execution-authorization document can reference them after activation. It creates no execution authority, authorizes no runner invocation, and performs no real-manifest contact.

"Bound in this record" is effective only after activation. Activation occurs when the exact accepted document is committed to `main`, pushed, and synchronized as `HEAD == origin/main` with a clean working tree. Before that event, this file is a proposed binding record and fixes no authoritative repository state. The record MUST NOT predict or embed its own future commit hash. After activation, "BOUND IN THIS RECORD" means the activated document fixes the accepted value for use by the later authorization phase; it does **not** mean any runner, schema-contract, or test source constant has been modified. Those constants continue to read `UNBOUND` in the committed sources until a later authorized implementation change, if any.

All current prohibitions remain active and unchanged:

```text
FORMAL_HOLD                             = active
Mode_0                                  = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
authoritative v0.2 CLI execution        = prohibited
real frozen Stage S1 manifest contact   = prohibited
exact-manifest hashing                  = not authorized (see §13)
scientific publication                  = prohibited
execution authorization                 = not present
explicit Hilmir execution order         = not given
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Governing synchronized state

Draft base state and current review state:

```text
repository                                   = torment_fabric
branch                                       = main
draft base HEAD                              = origin/main
draft base commit                            = 1339a512307ee95fb3dfb7f24f42fe2645b0957f
operator-confirmed tree before target draft  = clean
current expected review state                = clean except the one untracked target document
target document                              = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_IDENTITY_BINDING_RECORD_v0.1.md
```

Normative configuration-identity specification and its commit:

```text
specification = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CONFIGURATION_IDENTITY_SPECIFICATION_v0.1.md
commit        = 1339a512307ee95fb3dfb7f24f42fe2645b0957f
subject       = docs(research): specify synthetic validation v0.2 configuration identity
```

## 2. Purpose and scope

### 2.1 In scope

```text
- propose activation-time binding of the six calculated implementation-file identities (schema-contract, runner, runner-test)
- propose activation-time binding of the independently reproduced v0.2 configuration identity
- record the evidence that independent calculations A and B agreed exactly
- preserve the exact-manifest identities as separate and still UNBOUND
- preserve the non-circular identity hierarchy
- prepare the lane for a later, separately reviewed execution-authorization document
```

### 2.2 Out of scope (explicitly not done here)

```text
- no execution authority is created
- no runner invocation or real-manifest contact is authorized or performed
- no exact-manifest external or payload SHA-256 is calculated
- no arming/journal/staging/result/publication path is created
- no runner, schema-contract, or test source constant is modified
- no execution-authorization document is drafted
- no scientific PASS or FAIL is claimed
- no Git mutation is performed
```

## 2.3 Authoritative identity-gate inventory

Static source inventory:

```text
source = research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
AUTHORITATIVE_IDENTITIES keys = lines 133-143
pre-contact checks           = lines 1493-1518
```

Complete authoritative identity keys and lifecycle disposition:

| key | classification | disposition |
|---|---|---|
| `later_execution_authorization_identity` | REMAINS_UNBOUND_FOR_EXECUTION_AUTHORIZATION | must be supplied by a later accepted execution-authorization document; not bound here |
| `runner_git_blob` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `runner_raw_sha256` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `runner_test_git_blob` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `runner_test_raw_sha256` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `schema_contract_git_blob` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `schema_contract_raw_sha256` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §3 |
| `expected_manifest_external_sha256` | REMAINS_UNBOUND_FOR_MANIFEST_PHASE | exact manifest file-byte identity; not calculated or bound here |
| `expected_manifest_payload_sha256` | REMAINS_UNBOUND_FOR_MANIFEST_PHASE | exact canonical manifest-payload identity; not calculated or bound here |
| `v0_2_configuration_identity` | BOUND_BY_THIS_RECORD | proposed activation-time binding in §7 |

Pre-contact gate inventory:

```text
later_execution_authorization_identity == UNBOUND
  -> FAIL_PRECONTACT_AUTHORIZATION

runner_git_blob / runner_raw_sha256 /
runner_test_git_blob / runner_test_raw_sha256 /
schema_contract_git_blob / schema_contract_raw_sha256 /
v0_2_configuration_identity == UNBOUND
  -> FAIL_PRECONTACT_IDENTITY

expected_manifest_external_sha256 /
expected_manifest_payload_sha256 == UNBOUND
  -> FAIL_PRECONTACT_MANIFEST_EXPECTATION
```

No authoritative identity key required for this binding phase is omitted. `ALREADY_BOUND_ELSEWHERE` does not apply to any key in the runner's `AUTHORITATIVE_IDENTITIES` map. Frozen descriptor and descriptor-test identities are governed by prior frozen documents but are not entries in this runner pre-contact identity map. Repository state, Python version, CLI/stdin shape, schema key sanity, output-path absence, and retained-v0.1 staging boundary checks are pre-contact gates but are `NOT_AN_IDENTITY_GATE`.

## 3. Implementation identities

The three committed v0.2 implementation files and their identities, proposed for activation-time binding by this record:

```text
schema-contract
  path      = research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
  git_blob  = a37b818609ba7be24105776e2d83d82773909727
  raw_sha256 = ce57ae583a631da8255b6d87ddcea64346c378a70c54aeb3d2827247e2584986

runner
  path      = research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
  git_blob  = c8f8eb525ffea16c2a15ec3a2d1b94af4425824f
  raw_sha256 = 01d289e7ee83488c51f8cbb3472eb778c3ec7703491e08ceaa1ca28d0ee08898

runner-test
  path      = research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
  git_blob  = fe20088acff77aa5345c9af7d06abb0783a4ef61
  raw_sha256 = 3ef6bd8318b3bea42ccc92889d486903392bb02cd8a802d02aa3d0a371ab2120
```

### 3.1 Calculation context (as recorded by the operator)

```text
identities calculated from     = authoritative Windows checkout
HEAD = origin/main             = e9faab04ba7f97d724aa4eb5a4eaee1a4aacaa2e
working tree                   = clean
runner invocation              = none
manifest contact               = none
files unchanged through        = 1339a512307ee95fb3dfb7f24f42fe2645b0957f (config-spec commit added only the docs file)
```

### 3.2 Independent read-only reproduction at 1339a51 (confirmation)

To confirm the files remained unchanged through `1339a51`, the reviewer independently recomputed each file's Git-blob SHA-1 (`sha1("blob "+len+"\0"+bytes)`) and raw SHA-256 from the current committed checkout, using only `hashlib`. No Git command was run; no file was modified.

```text
method               = read-only hashlib recomputation from the synchronized checkout
git commands executed = none
files modified        = none

schema-contract : bytes=27751  contains_CRLF=false  git_blob=MATCH  raw_sha256=MATCH
runner          : bytes=65836  contains_CRLF=false  git_blob=MATCH  raw_sha256=MATCH
runner-test     : bytes=58040  contains_CRLF=false  git_blob=MATCH  raw_sha256=MATCH
```

All six identities reproduced exactly. These three implementation files carry LF line endings on disk (no CRLF mount artifact), so the raw and LF-normalized digests coincide and no line-ending ambiguity arises. No source mismatch was discovered; the operator-provided values are accepted as the proposed activation-time values without substitution.

Later adversarial review may additionally use read-only Git and filesystem hash commands to verify these same identities. Such verification does not mutate Git state and does not change the recorded identity inputs.

### 3.3 Implementation binding validity boundary

The implementation bindings apply only to the exact three paths and identity pairs recorded here:

```text
schema-contract path + Git blob + raw SHA-256
runner path + Git blob + raw SHA-256
runner-test path + Git blob + raw SHA-256
```

Any later byte change to one of those files invalidates the corresponding binding for future authorization, even if the filename remains unchanged. A later filename-preserving edit therefore requires a new identity calculation, review, and binding phase before it can be referenced by an execution authorization.

## 4. Configuration-identity specification provenance

```text
normative specification = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CONFIGURATION_IDENTITY_SPECIFICATION_v0.1.md
specification commit    = 1339a512307ee95fb3dfb7f24f42fe2645b0957f
commit role             = provenance for the calculation surface only; NOT a field inside the configuration identity
payload                 = the ordered 26-field configuration payload defined in §5 of that specification
serializer              = canonical_json_bytes shape (json.dumps ensure_ascii=True, separators=(",",":"),
                          allow_nan=False, sort_keys=False) + UTF-8 + exactly one trailing LF
```

### 4.1 Source-state nuance (recorded truthfully)

```text
- the configuration specification's §1 historical text records its pre-commit drafting state
  at implementation HEAD e9faab04 ("working tree = clean except this new untracked docs-only specification")
- the specification was committed at 1339a51
- the v0.2 configuration identity was calculated from the committed corrected specification at 1339a51
```

This historical wording inside the specification's §1 describes the document's authoring context; it does not claim the current synchronized commit and does not affect the normative 26-field payload. The committed specification is not altered by this record.

## 5. Independent calculation A

```text
performer            = reviewer (this lane's independent calculator A)
inputs               = the committed 26-field specification payload (§5 of the specification)
tooling              = Python standard library only (json, hashlib, base64)
runner executed      = false
runner imported      = false
repository modules imported = none
real manifest contact = none

top-level field count = 26
canonical byte length = 1957
final byte            = 0x0A (exactly one trailing LF; no CRLF)
sort_keys             = false
ensure_ascii          = true
separators            = compact comma/colon (no whitespace)
allow_nan             = false
encoding              = UTF-8

internal cross-check  = two independently written build paths were used:
                        A1 = explicit ordered construction from the normative §5 table
                        A2 = fresh programmatic extraction parsed from the committed specification file
                        A1 and A2 produced identical canonical bytes and digest (distinct payload objects)

digest (candidate)    = fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
```

## 6. Blind independent calculation B

```text
performer            = separate independent calculator B (Codex), performed separately and blindly enough
                       to provide meaningful independence
normative source     = the same committed configuration specification (byte-construction authority)

top-level field count = 26
canonical byte length = 1957
final byte            = 0x0A
sort_keys             = false
ensure_ascii          = true
separators            = compact comma/colon
allow_nan             = false
encoding              = UTF-8
trailing newline      = exactly one LF

digest               = fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
```

## 7. Agreement and accepted identity

Calculations A and B agreed exactly on every compared element:

```text
ordered field names        = identical
field types                = identical
nested-object key ordering = identical (exit_code_model; output_schema_identifiers)
canonical JSON text        = identical
canonical bytes            = identical (1957 bytes, final byte 0x0A)
Base64 representation       = identical
SHA-256 digest             = identical
```

Accepted configuration identity, proposed for activation-time binding by this record:

```text
v0_2_configuration_identity = fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
```

The full canonical Base64 is not reproduced here; per the configuration specification, the committed 26-field payload and its §6 byte-construction rules remain the normative source of the bytes, and the digest, byte length (1957), final-byte rule (single 0x0A), and the A/B exact-agreement statement above are sufficient for this record.

### 7.1 Configuration binding validity boundary

Any change to the normative 26-field configuration specification, its ordered field set, nested-object ordering, canonical serialization rules, canonical payload bytes, or SHA-256 digest invalidates the recorded configuration identity for future authorization. Such a change requires a new independent calculation and binding phase. The value recorded here applies only to the committed 26-field specification at `1339a512307ee95fb3dfb7f24f42fe2645b0957f`.

## 8. Exact-manifest identities remaining unbound

```text
expected_manifest_external_sha256 = UNBOUND
expected_manifest_payload_sha256  = UNBOUND
```

The accepted configuration identity does **not** identify:

```text
- exact frozen manifest bytes
- exact accepted-family payload bytes
- exact external manifest file identity
- exact canonical manifest payload identity
```

It fingerprints the configured v0.2 operation and its route/schema/freeze-configuration expectations only (the freeze-configuration commitment `5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263` is carried by reference, not as manifest-byte identity). The exact-manifest external and payload identities are deliberately left `UNBOUND`; they must be bound separately, under explicitly resolved contact authority, before any real-manifest contact can become authorized. They are **not** calculated in this record.

## 9. Identity hierarchy and non-circularity

The following acyclic dependency structure is preserved. No arrow points backward into the configuration identity.

```text
configuration literals
+ fixed scientific rules
+ route/schema expectations
+ frozen fixture-configuration commitment
    -> v0_2_configuration_identity

committed implementation-file bytes
    -> implementation Git-blob / raw-SHA identities

exact frozen manifest bytes
    -> later exact-manifest external / payload identities

configuration identity
+ implementation identities
+ exact-manifest identities
    -> later execution-authorization document

execution authorization
+ synchronized authorized execution HEAD
+ explicit Hilmir execution order
    -> authoritative runner invocation
```

The configuration identity is a leaf: its inputs are literals, fixed rules, route/schema expectations, and the already-frozen fixture-configuration hash — none of which depends on the implementation-file bytes, the exact-manifest bytes, the execution-authorization document, or any commit. It is computed once and thereafter only referenced by value. Admitting any file blob, manifest-byte identity, authorization identity, or commit into the configuration payload would create a back-edge into the leaf and is therefore forbidden.

## 10. Binding semantics

Distinguished states:

```text
PROPOSED BINDING IN UNTRACKED DRAFT
                   = accepted values are proposed by an untracked document;
                     no authoritative repository state is fixed
EFFECTIVE BINDING AFTER ACCEPTED COMMIT AND SYNCHRONIZATION
                   = the exact accepted record has been committed to main, pushed,
                     and synchronized as HEAD == origin/main with a clean working tree
CALCULATED         = a value has been computed from committed inputs by a read-only procedure
ACCEPTED           = the calculated value has passed independent A/B agreement and review
BOUND IN THIS RECORD = after activation, this document fixes the accepted value for use by the
                       later authorization phase (does NOT modify any runner/schema/test
                       source constant)
UNBOUND            = no accepted value is fixed; the runner pre-contact gate continues to refuse
AUTHORIZED         = a separate execution-authorization document has granted execution (NOT present)
EXECUTED           = the authoritative runner has been invoked (has NOT occurred)
PUBLISHED          = a scientific result bundle has been written (has NOT occurred)
```

Current draft review state, before activation:

```text
record review state                       = PROPOSED BINDING IN UNTRACKED DRAFT / pending review
effective repository binding              = false until accepted commit and synchronization

schema-contract implementation identities = PROPOSED FOR BINDING BY THIS RECORD
runner implementation identities          = PROPOSED FOR BINDING BY THIS RECORD
runner-test implementation identities     = PROPOSED FOR BINDING BY THIS RECORD
v0_2_configuration_identity               = PROPOSED FOR BINDING BY THIS RECORD

expected_manifest_external_sha256          = UNBOUND
expected_manifest_payload_sha256           = UNBOUND
execution-authorization identity           = UNBOUND / ABSENT
authoritative execution                    = NOT AUTHORIZED
runner executed                            = false
real manifest contact                      = none
scientific result published                = false
```

After the activation condition in §0 is satisfied, the four proposed binding lines above become `BOUND IN THIS RECORD`. This activation rule does not authorize execution and does not fill the manifest or execution-authorization identities.

## 11. Authority and contact accounting

```text
execution authority created                = none
runner invocation                          = none
runner import                              = none
real frozen Stage S1 manifest contact       = none
exact-manifest hashing                     = not performed, not authorized
arming path created                        = false
execution-journal path created             = false
staging path created                       = false
result path created                        = false
publication path created                   = false
scientific evaluation                      = none
scientific result published                = false
git operations                             = read-only identity verification permitted; mutations none
```

The only computations performed for this record were read-only `hashlib` recomputations of the three committed implementation files (§3.2) and the standard-library configuration-identity calculation over the committed specification payload (§5). Neither touched the runner, the real manifest, the environment, or any authoritative path.

## 12. Permanent scientific and production boundaries

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

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 13. Required next phase

The next separately reviewed phase is:

```text
1. Attempt NON-CONTACT DISCOVERY of already-recorded exact-manifest identities by searching committed
   docs, frozen findings, prior evidence, and source constants. This operation must not open, hash,
   parse, or inspect the real manifest.
2. If exact-manifest identities are not already authoritatively recorded, obtain a separate explicit
   CONTROLLED CONTACT CALCULATION authorization before reading any real manifest byte.
3. Under that separate authority only, read the real manifest, account for contact, and calculate the
   external and canonical-payload hashes without scientific descriptor evaluation.
4. Bind those manifest identities without scientific evaluation.
5. Prepare a separate docs-only v0.2 execution-authorization document.
6. Bind that authorization to the latest synchronized authorized commit using a non-circular rule.
7. Perform a final adversarial pre-contact review.
8. Obtain a new, explicit Hilmir execution order.
```

Contact-authority caveat (do not skip):

```text
Manifest hashing is NOT already authorized merely because it is not scientific evaluation.
Reading the real frozen Stage S1 manifest bytes — even solely to compute its external or canonical
payload SHA-256 — is real-manifest contact and requires explicitly resolved contact authority.
That contact authority MUST be resolved explicitly (step 2 above) before any real manifest byte is read.
This record neither grants nor assumes that authority.
```

## 14. Final status

```text
RECORD_REVIEW_STATE               = pending review while untracked; accepted draft only after review verdict
EFFECTIVE_REPOSITORY_BINDING      = false until exact accepted record is committed and synchronized
IMPLEMENTATION_IDENTITIES         = PROPOSED FOR BINDING BY THIS RECORD (schema-contract, runner, runner-test)
V0_2_CONFIGURATION_IDENTITY       = PROPOSED FOR BINDING BY THIS RECORD = fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
INDEPENDENT_CALCULATIONS_AGREED   = true (A == B, exact)
EXACT_MANIFEST_IDENTITIES         = UNBOUND (external, payload)
EXECUTION_AUTHORIZATION_PRESENT   = false
AUTHORITATIVE_EXECUTION_AUTHORIZED = false
REAL_MANIFEST_CONTACT_AUTHORIZED  = false
SCIENTIFIC_PUBLICATION_AUTHORIZED = false
RUNNER_EXECUTED                   = false

NEXT_PHASE = EXACT_MANIFEST_IDENTITY_RESOLUTION_AND_SEPARATE_EXECUTION_AUTHORIZATION
```

All prohibitions in §0 remain active and unchanged. While untracked, this record proposes identity bindings only. After activation, it binds identities only; it authorizes no execution and no real-manifest contact, and it does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.
