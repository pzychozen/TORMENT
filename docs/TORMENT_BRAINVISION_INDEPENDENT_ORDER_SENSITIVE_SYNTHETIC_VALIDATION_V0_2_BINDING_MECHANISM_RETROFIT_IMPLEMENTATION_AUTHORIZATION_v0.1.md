# TORMENT Brainvision - Independent Order-Sensitive Synthetic Validation v0.2 - Binding-Mechanism Retrofit Implementation Authorization v0.1

## 0. Document class and status

```text
document_class        = bounded implementation authorization (docs-only)
subject               = Stage S3B v0.2 execution-authorization binding-mechanism retrofit
authorization_active  = false while this document is untracked
implementation_scope  = bounded runner/test retrofit only
execution_authorized  = false
manifest_contact      = prohibited
authority_created     = none
authority_consumed    = false
scientific_result     = none
publication           = prohibited
```

This document authorizes no Stage S3B execution. It authorizes only a later bounded implementation of the
selected binding-mechanism retrofit, and only after this exact accepted document is committed to `main`,
pushed, and synchronized with `HEAD == origin/main` and a clean working tree. This document does not embed
or predict its own future commit hash.

## 1. Governing synchronized state

```text
repository        = torment_fabric
branch            = main
required_HEAD     = origin/main = 58e8cef7a3fb868415df3ffb3e0ae0d8abd8b069
required_tree     = clean except accepted untracked review/authorization drafts during review
Git permissions   = read-only inspection until a later explicit implementation task
```

The current architecture blocker review is:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_ARCHITECTURE_REVIEW_v0.1.md
```

## 2. Confirmed blocker

The committed Stage S3B v0.2 runner contains an unreachable execution-authorization gate:

```text
AUTHORITATIVE_IDENTITIES = all values UNBOUND
main()                   = supplies no authoritative identity override
authorization document   = not read
binding block parser     = absent
file identity checks     = absent
latest-path-commit rule  = absent
```

The in-process `identities=` parameter is a bounded-test seam only. It is not an authoritative CLI,
environment, stdin, or document channel.

An execution-authorization document drafted now would therefore be inert with respect to the current
runner. A bare source edit replacing `UNBOUND` values is not authorized because it changes the runner's
own identity and does not create a self-verifying, non-circular binding mechanism.

## 3. Selected remediation architecture

The selected architecture is:

```text
RETROFIT THE v0.1/FREEZE AUTHORIZATION-DOCUMENT BINDING MECHANISM INTO THE v0.2 RUNNER
```

The revised runner must, before any manifest contact:

```text
1. Read one fixed repository-relative execution-authorization document path.
2. Parse exactly one machine-readable BEGIN/END binding block from that document.
3. Verify repository root, branch, clean tree, HEAD == origin/main, and latest authorization-path commit == HEAD.
4. Recompute and compare runner, runner-test, and schema-contract Git blob and raw SHA-256 identities.
5. Compare the v0.2 configuration identity and exact-manifest identities.
6. Recompute and compare the non-circular later_execution_authorization_identity.
7. Fail closed before authority consumption on any absence, malformed input, mismatch, stale HEAD, dirty tree,
   unsupported route, or attempted CLI/environment override.
```

No launcher/wrapper is authorized. No final execution-authorization document is authorized by this
implementation-authorization document.

## 4. Authorized files and exact change-set boundary

Authorized implementation files for the later bounded retrofit:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
```

Default prohibitions:

```text
schema-contract modification = prohibited unless a later implementation review proves it technically required
new executable file          = prohibited
launcher/wrapper             = prohibited
production/kernel files      = prohibited
prior committed docs         = prohibited
```

If the schema-contract file appears necessary to modify, the implementation must stop and require a
separate explicit authorization. This document does not authorize that expansion.

## 5. Authorization-document path and binding format

The future execution-authorization document path to be consumed by the revised runner is fixed as:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_v0.1.md
```

The future execution-authorization document must contain exactly one binding block:

```text
BEGIN-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1
authorization_schema=TORMENT_BRAINVISION_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_BINDING
authorization_version=v0.2
later_execution_authorization_identity=<lowercase 64-hex>
runner_git_blob=<lowercase 40-hex>
runner_raw_sha256=<lowercase 64-hex>
runner_test_git_blob=<lowercase 40-hex>
runner_test_raw_sha256=<lowercase 64-hex>
schema_contract_git_blob=<lowercase 40-hex>
schema_contract_raw_sha256=<lowercase 64-hex>
v0_2_configuration_identity=<lowercase 64-hex>
expected_manifest_external_sha256=<lowercase 64-hex>
expected_manifest_payload_sha256=<lowercase 64-hex>
END-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1
```

The parser must reject duplicate markers, missing markers, nested markers, binding-like content outside
the single block, duplicate keys, unknown keys, missing keys, wrong ordering, empty values, non-string
values, malformed lines, uppercase hex, and values of the wrong length.

## 6. Binding parser and validation requirements

The parser must be deterministic over document bytes and must not import, execute, evaluate, or contact
any real fixture or manifest. It must not accept values from command-line flags, environment variables,
stdin, generated temporary files, or in-memory caller injection in the authoritative CLI path.

The exact ordered field set is:

```text
authorization_schema
authorization_version
later_execution_authorization_identity
runner_git_blob
runner_raw_sha256
runner_test_git_blob
runner_test_raw_sha256
schema_contract_git_blob
schema_contract_raw_sha256
v0_2_configuration_identity
expected_manifest_external_sha256
expected_manifest_payload_sha256
```

The parser may expose bounded-test seams, but the authoritative route from `main()` must obtain these
values only from the committed authorization-document binding after repository-state checks establish the
allowed path.

## 7. Implementation identity self-verification

The revised runner must recompute and compare all implementation identities before manifest contact:

```text
runner_git_blob              = git rev-parse HEAD:research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
runner_raw_sha256            = SHA-256 of the Windows working-tree bytes of the runner file after clean-tree verification
runner_test_git_blob         = git rev-parse HEAD:research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
runner_test_raw_sha256       = SHA-256 of the Windows working-tree bytes of the runner-test file after clean-tree verification
schema_contract_git_blob     = git rev-parse HEAD:research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
schema_contract_raw_sha256   = SHA-256 of the Windows working-tree bytes of the schema-contract file after clean-tree verification
```

Every recomputed value must match the corresponding value in the future execution-authorization binding.
Presence-only checks are insufficient.

## 8. Configuration and manifest identity verification

The revised runner is authorized to contain fixed expected constants, or semantically equivalent immutable
runner-owned values, for exactly these three non-self semantic identities:

```text
EXPECTED_V0_2_CONFIGURATION_IDENTITY =
fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9

EXPECTED_MANIFEST_EXTERNAL_SHA256 =
05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404

EXPECTED_MANIFEST_PAYLOAD_SHA256 =
56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
```

The required verification direction is:

```text
authorization-binding candidate
    -> compare against fixed runner-owned accepted value
```

The prohibited tautology is:

```text
authorization-binding value
    -> compare only against the same parsed authorization-binding value
```

Embedding these three non-self identities does not create Cycle A. The revised runner's bytes will be
calculated and rebound after implementation, while these three accepted semantic identities remain
unchanged unless the normative v0.2 configuration or retained Stage S1 lineage is separately found to
contradict them.

Runner, runner-test, and schema-contract Git/raw identities must continue to come from the authorization
binding and be compared against identities recomputed from current committed bytes. The
`later_execution_authorization_identity` must continue to come from the authorization binding and be
compared against the independently recomputed canonical authorization-payload digest.

The exact-manifest values must not be recomputed during pre-contact validation, because contacting,
reading, hashing, parsing, copying, or inspecting the real frozen manifest remains prohibited until a
later valid one-run execution order reaches the manifest-contact point.

## 9. Non-circular authorization identity construction

`later_execution_authorization_identity` must be a commitment derived from the authorization binding
payload excluding its own identity field. It must not be an arbitrary literal token, a hardcoded runner
constant, a document self-hash, a Git commit hash, or the authorization document's Git blob.

The authorization-identity payload must be a JSON object with exactly 19 top-level fields in exactly this
insertion order:

```text
1.  domain_label
2.  authorization_document_path
3.  begin_marker
4.  end_marker
5.  field_order_without_later_execution_authorization_identity
6.  authorization_schema
7.  authorization_version
8.  runner_path
9.  runner_git_blob
10. runner_raw_sha256
11. runner_test_path
12. runner_test_git_blob
13. runner_test_raw_sha256
14. schema_contract_path
15. schema_contract_git_blob
16. schema_contract_raw_sha256
17. v0_2_configuration_identity
18. expected_manifest_external_sha256
19. expected_manifest_payload_sha256
```

Every top-level field is a JSON string except `field_order_without_later_execution_authorization_identity`,
which is an ordered JSON array of strings. That array must contain exactly these strings in exactly this
order:

```text
authorization_schema
authorization_version
runner_git_blob
runner_raw_sha256
runner_test_git_blob
runner_test_raw_sha256
schema_contract_git_blob
schema_contract_raw_sha256
v0_2_configuration_identity
expected_manifest_external_sha256
expected_manifest_payload_sha256
```

The fixed string values are:

```text
domain_label =
TORMENT_BRAINVISION_S3B_V0_2_EXECUTION_AUTHORIZATION_BINDING_IDENTITY_v0.1

authorization_document_path =
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_v0.1.md

begin_marker =
BEGIN-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1

end_marker =
END-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1

authorization_schema =
TORMENT_BRAINVISION_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_BINDING

authorization_version =
v0.2

runner_path =
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py

runner_test_path =
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py

schema_contract_path =
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
```

The remaining identity values come from the parsed future authorization binding:

```text
runner_git_blob
runner_raw_sha256
runner_test_git_blob
runner_test_raw_sha256
schema_contract_git_blob
schema_contract_raw_sha256
v0_2_configuration_identity
expected_manifest_external_sha256
expected_manifest_payload_sha256
```

The canonical serialization is normative and exact:

```python
json.dumps(
    payload,
    ensure_ascii=True,
    separators=(",", ":"),
    allow_nan=False,
    sort_keys=False,
).encode("utf-8") + b"\n"
```

The hash algorithm is SHA-256, and the resulting digest must be lowercase 64-hex. The serialized payload
must contain exactly one terminal LF, no CRLF, no internal whitespace, no key sorting, and significant
array order. The `later_execution_authorization_identity` field remains excluded from this payload and is
compared against the resulting digest.

This is non-circular because the identity field is excluded from its own payload, and the authorization
document does not embed its own commit or blob identity. This adapts the established v0.1/freeze binding
document mechanism and the existing schema-contract canonical byte/hash discipline.

## 10. Latest-path-commit execution-HEAD rule

The revised runner must enforce the non-circular execution-HEAD rule before manifest contact:

```text
branch == main
HEAD == origin/main
working tree == clean
git log -1 --format=%H -- docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_v0.1.md == HEAD
```

The future execution-authorization document must not embed its own commit hash or Git blob. Authority is
established by the latest-path-commit rule, not by a self-referential document identity.

## 11. Pre-contact failure semantics

Any authorization-document absence, parse failure, identity mismatch, unsupported repository state,
stale authorization-path commit, dirty tree, `HEAD != origin/main`, attempted CLI/environment override,
wrong path, or malformed authority identity must fail closed before authority consumption.

Required pre-contact refusal accounting:

```text
exit code                 = 2
manifest contact          = 0
manifest bytes read       = 0
authority consumed        = false
arming/journal created    = false
scientific evaluation     = false
artifact publication      = false
```

## 12. Preservation of authority consumption and evidence

The retrofit must preserve the current v0.2 authority-consumption and evidence model:

```text
manifest-contact accounting       = preserved
two-pass validation protocol      = preserved
current_state/terminal_evidence   = preserved
scientific gate                   = preserved
publication semantics             = preserved
exit-2 pre-contact model          = preserved
exit-3 controlled-invalid model   = preserved
exit-4/5 post-consumption failure = preserved
one-run/retry prohibition         = preserved
```

The retrofit may only make the pre-contact identity gate reachable through the committed
authorization-document binding mechanism. It must not change the scientific fixture evaluation,
descriptor semantics, controlled-invalid model, staging/journal behavior, terminal evidence separation,
or retained boundaries.

## 13. Required bounded tests

The later implementation must add or update bounded, non-authoritative tests covering at least:

```text
valid authorization binding accepted pre-contact
missing authorization document
malformed BEGIN/END markers
duplicate key
unknown key
missing key
wrong ordering
invalid hex
wrong runner Git blob
wrong runner raw SHA-256
wrong runner-test Git blob
wrong runner-test raw SHA-256
wrong schema-contract Git blob
wrong schema-contract raw SHA-256
wrong configuration identity
wrong external manifest identity
wrong manifest-payload identity
wrong later execution-authorization identity
authorization document latest commit != HEAD
HEAD != origin/main
dirty working tree
authorization path mismatch
CLI/environment override rejection
zero manifest contact on every refusal
zero authority consumption on every refusal
current bounded non-authoritative test seams remain usable
existing authority-consumption and exit-model tests remain passing
```

Tests must not contact the real manifest, execute the authoritative runner path, create actual
authoritative arming/journal/staging/result/publication paths, or evaluate real fixtures.

## 14. Identity supersession and re-binding

The existing runner identity binding at `dfcb205` is valid for the old dormant runner only. The bounded
retrofit intentionally supersedes that runner binding.

Required supersession rules:

```text
old runner binding                = superseded if the runner is revised
old runner-test binding           = superseded if the runner-test file is revised
schema-contract binding           = remains valid if the schema-contract file is unchanged
v0.2 configuration identity        = remains valid if the normative 26-field configuration is unchanged
exact-manifest identities          = remain valid if the retained Stage S1 lineage is unchanged
revised implementation identities = must be calculated after implementation review and commit
execution authorization            = prohibited until revised identities are committed and bound
```

No final execution-authorization document may be drafted until the revised implementation identities are
committed, reviewed, recalculated, and docs-bound.

## 15. Review and commit sequence

Required later sequence:

```text
1. Commit this implementation-authorization document to main as an accepted docs-only authorization.
2. Confirm HEAD == origin/main and clean tree.
3. Perform the bounded runner/test retrofit only within the authorized files.
4. Run only bounded non-authoritative tests approved for the implementation task.
5. Review the revised source and tests.
6. Commit the accepted implementation.
7. Recalculate runner/test/schema identities from the committed implementation state.
8. Bind revised identities in a separate docs-only identity-binding record.
9. Only after that, consider a future final execution-authorization specification.
```

Future execution-authorization commit discipline:

```text
future execution-authorization commit = authorization document only
implementation changes in that commit = prohibited
```

The final execution-authorization specification and adversarial review must verify that the future
execution-authorization document is committed as a dedicated docs-only authorization commit with no
implementation changes in that commit. This lifecycle requirement does not add any unreviewed runner Git
command for changed-path enumeration.

This document does not authorize skipping any review, identity-binding, or final authority step.

## 16. Explicit non-authorizations

This document does not authorize:

```text
Brainvision runner execution
runner import for authoritative evaluation
fixture freezer invocation
verifier/evaluator/descriptor invocation
real frozen manifest contact, read, hash, parse, copy, or inspection
arming/journal/staging/result/publication path creation
source/test modification in this review task
schema-contract modification without separate authorization
launcher/wrapper creation
final execution-authorization drafting
scientific result calculation
authority consumption
publication
Git mutation during this review task
```

## 17. Permanent boundaries

Permanent boundaries remain active:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision = offline / quarantined / non-production / non-service / non-kernel / non-memory-integrated
production-kernel and live-system boundary = unchanged
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3
result.

## 18. Final status

```text
blocker_confirmed                       = true
retrofit_technically_coherent           = true
selected_mechanism                      = v0.1/freeze authorization-document binding retrofit
authorization_identity_payload_schema   = deterministic 19-field canonical JSON object, self-identity excluded
trusted_expected_anchors_required       = configuration + external-manifest + manifest-payload runner-owned constants
authorized_later_change_set             = runner + runner-test only
schema_contract_modification_authorized = false
new_executable_file_authorized          = false
execution_authorized                    = false
manifest_contact_authorized             = false
final_execution_authorization_drafted   = false
future_execution_authorization_commit   = authorization document only
activation_state                        = inactive while untracked
```

Final recommendation:

```text
ACCEPT_V0_2_BINDING_MECHANISM_RETROFIT_AUTHORIZATION_FOR_OVERSEER_REVIEW
```
