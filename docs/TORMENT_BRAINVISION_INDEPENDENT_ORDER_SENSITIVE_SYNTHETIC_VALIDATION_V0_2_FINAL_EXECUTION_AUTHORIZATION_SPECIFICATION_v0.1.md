# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Final Execution-Authorization Specification v0.1

## 0. Document class and status

```text
document_class          = final execution-authorization SPECIFICATION (docs-only)
subject                 = the future Stage S3B v0.2 execution-authorization document and its later_execution_authorization_identity
this_document_is        = a specification of the future authorization artifact and its calculation procedure
this_document_is_not    = the final execution-authorization document
authority_created       = none
execution_authorized    = false
manifest_contact        = prohibited
authority_consumption   = prohibited
scientific_evaluation   = prohibited
publication             = prohibited
later_execution_authorization_identity = UNBOUND (deliberately not calculated here)
final_authorization_document           = absent
git_operations          = none
source_modified         = none
tests_modified          = none
schema_contract_modified = none
prior_docs_modified     = none
```

This document is **docs-only, non-executing, non-authorizing, pre-contact, non-production, non-kernel**. It defines the exact construction, calculation procedure, and lifecycle of the *future* Stage S3B v0.2 execution-authorization document. It does not create that document, does not calculate the final authorization identity, and authorizes no runner execution, real-manifest contact, authority consumption, scientific evaluation, or publication.

All current prohibitions remain active and unchanged:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
authoritative v0.2 CLI execution      = prohibited
real frozen Stage S1 manifest contact = prohibited
authority consumption                 = prohibited
scientific publication                = prohibited
explicit Hilmir execution order       = not given
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Governing synchronized state and inputs

Operator-confirmed synchronized state:

```text
repository   = torment_fabric
branch       = main
HEAD         = dec5e15339d92a5b1aa7e7260d7b058796d62ffb
origin/main  = dec5e15339d92a5b1aa7e7260d7b058796d62ffb
working tree = clean
```

Governing documents (read; not modified):

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_ARCHITECTURE_REVIEW_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_BINDING_MECHANISM_RETROFIT_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_BINDING_RETROFIT_IMPLEMENTATION_IDENTITY_BINDING_v0.1.md
```

Reference implementation (read-only; not imported, not executed) — the specification below was verified to match its committed parser and canonical-identity construction:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py   (HEAD blob c2dcdc25cc3e057bf63a49ccf8f4584e5ca20e5f)
```

## 2. Purpose, scope, and non-authorization

In scope:

```text
- fix the future authorization-document path (runner-owned, non-overridable)
- specify the exact single machine-readable binding block and its ordered field contract
- specify the exact 19-field canonical authorization-identity payload, serialization, and hash
- define the dual-independent calculation-and-verification procedure for later_execution_authorization_identity
- define the dedicated-commit and non-circular execution-HEAD rule
- restate the LF-only byte-state requirements and the fail-closed autocrlf fragility
- require a bounded Windows pre-execution diagnostic as a later prerequisite
- declare the current no-execution authority state
```

Out of scope (explicitly not done by this document):

```text
- no creation of the final execution-authorization document
- no calculation or substitution of later_execution_authorization_identity
- no runner execution or import
- no real-manifest contact
- no authority consumption, scientific evaluation, or publication
- no source/test/schema/prior-doc modification
- no Git operation
```

## 3. Fixed future authorization-document path

The future execution-authorization document is bound to exactly:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_v0.1.md
```

This path is:

```text
runner-owned            (compiled constant AUTHORIZATION_DOCUMENT_PATH in the committed runner)
repository-relative     (forward-slash, no drive letter, no operator root)
non-overridable
not replaceable by CLI, environment, stdin, or any caller input
not replaceable by symlink or alternate path (repository-root containment is enforced with realpath/normcase/commonpath)
```

No parsed field, CLI argument, environment variable, or stdin content may select, redirect, or replace this path.

## 4. Exact future binding block (template — not an authorization)

The future authorization document must contain **exactly one** machine-readable block, byte-exact in marker text, field spelling, field order, lowercase hexadecimal, and the absence of whitespace around `=`. The fixed identity values below are the accepted, docs-bound implementation and semantic identities (identity-binding record at `dec5e15`); the authorization identity is deliberately left as an explicit non-hex placeholder:

```text
BEGIN-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1
authorization_schema=TORMENT_BRAINVISION_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_BINDING
authorization_version=v0.2
later_execution_authorization_identity=<TO-BE-CALCULATED-AFTER-SPECIFICATION-ACCEPTANCE>
runner_git_blob=c2dcdc25cc3e057bf63a49ccf8f4584e5ca20e5f
runner_raw_sha256=8e2fdbe5a10c0351d485cb4b650143b9aa61fb1a16c28e0de6e7caf1daf893e6
runner_test_git_blob=2f2189560f0c6a481594d1d7fe7fe46d036a0c92
runner_test_raw_sha256=d7d1e82cfa64eededbb3e989e11675f44a0b870756161440291ab4524c9e5462
schema_contract_git_blob=a37b818609ba7be24105776e2d83d82773909727
schema_contract_raw_sha256=ce57ae583a631da8255b6d87ddcea64346c378a70c54aeb3d2827247e2584986
v0_2_configuration_identity=fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
expected_manifest_external_sha256=05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
expected_manifest_payload_sha256=56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
END-SYNTHETIC-VALIDATION-V0-2-EXECUTION-AUTHORIZATION-BINDING-v0.1
```

The placeholder `<TO-BE-CALCULATED-AFTER-SPECIFICATION-ACCEPTANCE>` is not valid hexadecimal; the runner's parser requires `later_execution_authorization_identity` to be lowercase 64-hex, so the template above is deliberately non-authoritative and cannot pass validation until the real digest (calculated per §7–§9) replaces the placeholder. This specification does not compute that digest and does not insert a plausible-looking hexadecimal value.

## 5. Exact ordered field contract and rejection conditions

The binding block body must contain exactly these twelve fields, once each, in exactly this order (matching the committed runner's `BINDING_FIELDS`):

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

Field/value typing: `authorization_schema` must equal `TORMENT_BRAINVISION_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_BINDING`; `authorization_version` must equal `v0.2`; `runner_git_blob`, `runner_test_git_blob`, `schema_contract_git_blob` must be lowercase 40-hex; `later_execution_authorization_identity`, `runner_raw_sha256`, `runner_test_raw_sha256`, `schema_contract_raw_sha256`, `v0_2_configuration_identity`, `expected_manifest_external_sha256`, `expected_manifest_payload_sha256` must be lowercase 64-hex.

The future authorization document (and therefore any invocation depending on it) MUST be rejected, fail-closed, for any of:

```text
missing document / not a regular file
non-UTF-8 bytes
any carriage return or CRLF
missing begin marker
missing end marker
duplicate begin marker
duplicate end marker
nested marker / markers out of order
binding-like content outside the single block (any recognized-key or identifier=value line outside)
wrong body field count (not exactly 12)
duplicate key
unknown key
missing key
wrong key order
leading or trailing whitespace on any block line
whitespace around "=" (spaced key/value)
more than one "=" on a block line
empty value
uppercase or mixed-case hexadecimal
wrong hexadecimal length
authorization_schema or authorization_version not equal to the fixed values
runner-owned anchor mismatch (see §7)
authorization-identity mismatch (see §7–§8)
implementation Git-blob or raw SHA-256 mismatch (see §11)
wrong fixed authorization path
latest authorization-path commit != HEAD
HEAD != origin/main, wrong branch, dirty tree, unsupported repository root
CLI override, environment override, stdin override, caller override
```

## 6. Authorization-identity payload — exact 19 fields

`later_execution_authorization_identity` is a SHA-256 commitment over a canonical JSON object with **exactly nineteen** top-level fields, in exactly this insertion order (matching the committed runner's `AUTHORIZATION_IDENTITY_PAYLOAD_FIELDS`):

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

Every top-level field is a JSON string except field 5, which is an ordered JSON array of strings.

Fixed, runner-owned string values (NOT taken from the parsed binding — the runner supplies these; the parsed binding's `authorization_schema`/`authorization_version` are separately checked to equal fields 6/7):

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

Field 5, `field_order_without_later_execution_authorization_identity`, is an ordered array containing **exactly** these eleven strings, in exactly this order (matching the runner's `AUTHORIZATION_IDENTITY_FIELD_ORDER`):

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

This array, and the 19-field payload as a whole, **exclude** `later_execution_authorization_identity` — the identity is never part of its own payload. Fields 9, 10, 12, 13, 15, 16, 17, 18, 19 are taken from the parsed binding; fields 17–19 (`v0_2_configuration_identity`, `expected_manifest_external_sha256`, `expected_manifest_payload_sha256`) are ALSO independently verified against the runner-owned trusted anchors (§7) before the digest is trusted.

## 7. Verification direction and trusted anchors

The runner verifies, before manifest contact and in the non-circular direction "parsed candidate → runner-owned trusted value":

```text
runner-owned anchors (fixed runner constants; the parsed binding's values must equal these):
  v0_2_configuration_identity        == fff90bf53f1c5a45a6c6fe5532208db479e4e153469aed3707accce2a8653be9
  expected_manifest_external_sha256  == 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
  expected_manifest_payload_sha256   == 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9

authorization-identity check:
  parsed later_execution_authorization_identity == SHA-256 of the canonical 19-field payload (§6, §8)

implementation self-verification (§11):
  recomputed runner/runner-test/schema-contract Git blob (HEAD:<path>) and raw SHA-256 (working-tree bytes)
      == the corresponding parsed binding values
```

A verification that compares a parsed value only against another value from the same parsed block (a tautology) is prohibited; the config/manifest anchors are compared against runner-owned constants, and the implementation identities are compared against values independently recomputed from the committed/working-tree bytes.

## 8. Canonical serialization and hash

The canonical bytes are computed exactly as (matching the committed runner and the schema-contract canonical-byte discipline):

```python
json.dumps(
    payload,
    ensure_ascii=True,
    separators=(",", ":"),
    allow_nan=False,
    sort_keys=False,
).encode("utf-8") + b"\n"
```

Required properties:

```text
encoding                = UTF-8
hash algorithm          = SHA-256
digest form             = lowercase 64-hex
terminal newline        = exactly one 0x0A, appended after the JSON text
CRLF                    = forbidden
internal whitespace     = none (compact "," and ":" separators, no spaces)
key sorting             = none (sort_keys=False); dictionary insertion order is significant
array order             = significant
self-identity field     = excluded from the payload
```

The `later_execution_authorization_identity` is the digest of these bytes, and it is compared against the value carried in the binding block. It is explicitly **not**:

```text
the authorization document whole-file SHA-256
the authorization document Git blob
the authorization commit hash
repository HEAD
an arbitrary token
a user-selected value
a runner-owned constant
```

## 9. Calculation and independent dual-verification procedure

The future `later_execution_authorization_identity` must be produced by two independent calculations that agree exactly. No single calculation may be used to create the final authorization.

```text
1.  this specification is reviewed and accepted
2.  this specification is committed and synchronized (HEAD == origin/main, clean tree)
3.  Codex independently constructs the 19-field payload from §6 (runner-owned fixed values + the accepted
    implementation/semantic identities), without importing runner code
4.  Codex emits: the canonical JSON text, canonical byte length, Base64 of the canonical bytes, and the SHA-256 digest
5.  Claude independently reconstructs the payload from §6 (standard-library json + hashlib only; no runner import/execution)
6.  Claude compares, and all must match exactly:
      - field order (19 fields)          - array order (11 strings)
      - canonical JSON text              - canonical byte length
      - terminal LF (exactly one 0x0A)   - Base64 of canonical bytes
      - SHA-256 digest
7.  any discrepancy => rejection; no digest is bound
8.  on exact agreement, the digest becomes later_execution_authorization_identity
9.  only then is the final execution-authorization document drafted, with that digest replacing the §4 placeholder
10. the final authorization document receives independent adversarial review before any commit
```

## 10. Dedicated authorization commit and non-circular execution-HEAD rule

The final execution-authorization document must be committed as a **dedicated docs-only commit** containing that document only:

```text
future execution-authorization commit = the authorization document only (no implementation, test, schema, or other change)
```

At any eventual invocation, the runner enforces the non-circular execution-HEAD rule (matching the committed `_verify_latest_authorization_commit`):

```text
git log -1 --format=%H -- docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_EXECUTION_AUTHORIZATION_v0.1.md
    ==
HEAD
```

Consequences and prohibitions:

```text
the authorization document must be the latest commit affecting its own fixed path AND equal to HEAD
any later unrelated commit automatically closes the authorization (latest-path commit != HEAD => fail-closed)
the authorization document MUST NOT embed its own Git blob, its own commit hash, or repository HEAD
authority is established by the latest-path-commit rule, never by a self-referential document identity
```

## 11. Repository and byte-state requirements

Before final authorization construction, and again before any eventual invocation:

```text
branch = main
HEAD = origin/main
working tree = clean
supported repository root (contains .git; fixed runner/test/schema/authorization paths resolve within root)
```

The bound implementation identities are over literal LF-only working-tree bytes (verified at this HEAD):

```text
runner:          bytes = 80385   CR = 0   LF = 1991   terminal LF = true
runner test:     bytes = 73530   CR = 0   LF = 1795   terminal LF = true
schema contract: bytes = 27751   CR = 0   LF = 735    terminal LF = true
```

The Git blob is taken from `HEAD:<path>` (committed content, stable); the raw SHA-256 is over the working-tree bytes. `core.autocrlf=true` creates operational fragility:

```text
working-tree byte conversion (LF -> CRLF)
    -> raw SHA-256 mismatch against the bound value
    -> fail-closed pre-contact refusal
```

This is fail-closed and is **not** an authorization bypass. The final authorization must bind the same literal byte form that will exist at execution. No `.gitattributes` or Git-configuration change is authorized in this phase.

## 12. Windows subprocess pre-execution diagnostic (later prerequisite)

The known bounded-test diagnostic is recorded:

```text
reproducible Windows access-violation output during pytest/Git subprocess interaction
pytest exit code = 0
functional tests = passing
independent source review found no subprocess-lifecycle defect (subprocess.run with managed pipes; no manual Popen/communicate misuse)
classification = environment/toolchain anomaly
```

Before the eventual one-run invocation, a bounded pre-execution diagnostic is a **prerequisite** of the later execution-authorization review. That diagnostic must:

```text
exercise only repository/pre-contact Git observations
avoid the real manifest
avoid authority consumption
avoid authoritative artifact creation
confirm fail-closed behavior
```

This specification does not define, schedule, or authorize that diagnostic's execution; it only makes it a required prerequisite for later execution-authorization review.

## 13. Permanent scientific and production boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision = offline / quarantined / non-production / non-service / non-kernel / non-memory-integrated
```

The future authorization concerns only **one bounded invocation of the already-frozen experiment**. It must not:

```text
modify the production kernel
integrate Brainvision into live memory
enable live capture
enable service integration
contact PsiTRS
reinterpret the historical frozen F3 result
weaken the scientific gate (fixed-positive + 8/8 exact-signature distinction; 7/8 = FAIL; full controls; byte-identical two-pass)
change fixtures
change the descriptor (descriptor.affine_plus_complement_signature)
introduce tolerance
introduce majority rule
permit scientific rescue
authorize publication automatically
```

## 14. Authority semantics — separate states, none implies the next

```text
specification accepted
authorization identity calculated (dual-independent agreement)
final authorization document committed (dedicated docs-only commit; latest-path == HEAD)
runner technically able to pass pre-contact verification
Hilmir explicit one-run execution order issued
```

None of these implies the next automatically. In particular:

```text
final authorization document committed
    !=
Hilmir explicit execution order
```

A committed authorization document is a necessary but not sufficient condition. No runner invocation may occur until Hilmir separately issues the explicit one-run execution order, after final adversarial review and the §12 diagnostic prerequisite.

## 15. Required current-state declaration

```text
retrofit implemented                   = true
retrofit committed and synchronized    = true
revised identities calculated          = true
revised identities docs-bound          = true

final execution-authorization specification = drafted by this document
later_execution_authorization_identity      = UNBOUND
final execution-authorization document      = absent

authoritative execution authorized     = false
real manifest contact authorized       = false
authority consumption authorized       = false
scientific evaluation authorized       = false
scientific publication authorized      = false
```

## 16. Prohibited content (self-constraint of this document)

This specification does not, and any accepted revision of it must not:

```text
calculate later_execution_authorization_identity
create the final authorization document
insert a valid-looking placeholder digest
claim authorization is active
authorize execution
authorize manifest contact
authorize authority consumption
authorize publication
modify source or tests
modify prior documents
modify the schema contract
create a launcher or wrapper
perform any Git operation
```

The §4 binding block is a specification template only; its `later_execution_authorization_identity` is the non-hex text placeholder `<TO-BE-CALCULATED-AFTER-SPECIFICATION-ACCEPTANCE>`, which cannot pass the runner's parser, and this specification file is not the fixed authorization path the runner reads.

## 17. Self-verification checklist

```text
all known Git blobs lowercase 40-hex           : PASS (c2dcdc25…, 2f218956…, a37b818…)
all known SHA-256 values lowercase 64-hex      : PASS (8e2fdbe5…, d7d1e82c…, ce57ae5…, fff90bf5…, 05ce02af…, 56a141bd…)
all fixed paths repository-relative            : PASS (authorization doc, runner, runner-test, schema-contract)
ordered lists match the runner contract        : PASS (12-field block; 19-field payload; 11-string array)
no field omitted / no field duplicated         : PASS
later_execution_authorization_identity unbound : PASS (explicit non-hex placeholder; not calculated)
no accidental execution grant                  : PASS (no authorization active; Hilmir order still required)
matches committed runner parser/serialization  : PASS (verified read-only against runner HEAD blob c2dcdc25)
```

## 18. Final status

```text
final_execution_authorization_specification = drafted (docs-only)
later_execution_authorization_identity      = UNBOUND (dual-independent calculation pending, §9)
final_execution_authorization_document      = absent
authoritative_execution_authorized          = false
real_manifest_contact_authorized            = false
authority_consumption_authorized            = false
scientific_publication_authorized           = false
next_phase = accept + commit this specification -> dual-independent identity calculation (§9)
             -> draft final authorization document with the calculated digest -> independent review
             -> §12 diagnostic prerequisite -> separate explicit Hilmir one-run order
```

This document authorizes no execution and no real-manifest contact, binds no authorization identity, and does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result. All prohibitions in §0 remain active.
