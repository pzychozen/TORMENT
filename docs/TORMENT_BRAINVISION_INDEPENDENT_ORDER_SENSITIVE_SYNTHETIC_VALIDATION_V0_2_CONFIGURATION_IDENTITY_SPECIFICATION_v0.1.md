# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Configuration-Identity Specification v0.1

## 0. Document class and status

```text
document_class            = configuration-identity specification (docs-only)
lane                      = Stage S3B v0.2 independent order-sensitive synthetic validation
authority_created         = none
code_modified             = none
tests_modified            = none
frozen_providers_modified = none
prior_docs_modified       = none
result_paths_created      = none
git_mutations             = none
runner_executed           = false
runner_imported           = false
real_manifest_contact     = none
identities_bound          = none
final_configuration_hash_claimed = false
```

This document is **docs-only, non-executing, non-authorizing, pre-contact, non-production, non-kernel**. It defines the exact semantic and byte-level *construction* of the Stage S3B v0.2 configuration identity. It does not calculate, claim, fabricate, predict, or bind the final v0.2 configuration-identity hash value; it does not authorize execution; and it does not contact the real frozen Stage S1 manifest.

All current prohibitions remain active and unchanged:

```text
FORMAL_HOLD                             = active
Mode_0                                  = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
authoritative v0.2 CLI execution        = prohibited
real frozen Stage S1 manifest contact   = prohibited
scientific publication                  = prohibited
identity binding                        = deferred to a later, separately reviewed phase
execution authorization                 = not present
explicit Hilmir execution order         = not given
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Governing source and synchronized state

Reviewed at the operator-supplied synchronized state:

```text
repository     = torment_fabric
branch         = main
HEAD           = origin/main
HEAD commit    = e9faab04ba7f97d724aa4eb5a4eaee1a4aacaa2e
working tree   = clean except this new untracked docs-only specification
```

Governing documents (read-only):

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_CORRECTION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_V0_2_IMPLEMENTATION_FINDINGS_v0.1.md
```

Governing implementation sources (read-only static review; not executed, not imported):

```text
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
```

The three committed implementation-file identities named in the handoff (schema-contract, runner, runner-test Git-blob and raw SHA-256 values) are treated here as **calculated by the separate read-only identity audit but not yet bound**. The Implementation Findings §11 records the binding state as `UNBOUND`. This document deliberately does **not** incorporate any of those file identities into the configuration identity (see §12).

## 2. Purpose and boundary of the configuration identity

### 2.1 Purpose

The Stage S3B v0.2 **configuration identity** (`v0_2_configuration_identity`) is a single lowercase-hex SHA-256 digest that immutably fingerprints the **scientific and execution configuration of the v0.2 synthetic-validation run** — i.e. *what experiment the runner is contracted to perform* — independently of the incidental byte content of the source files that implement it.

The runner already reserves this identity as a required, currently-`UNBOUND` gate:

```text
run_independent_order_sensitive_synthetic_validation_v0_2.py
  AUTHORITATIVE_IDENTITIES["v0_2_configuration_identity"] = "UNBOUND"          (module constant)
  perform_precontact_validation(): refuses FAIL_PRECONTACT_IDENTITY when
      identities["v0_2_configuration_identity"] == UNBOUND                     (pre-contact gate)
```

The bounded test currently satisfies that gate with the placeholder literal `"bound"` (test file, authoritative-identities fixture), which is a stub, not a defined value. The Correction Specification §17, the Implementation Authorization §16, and the Implementation Findings §11 all record `v0.2 configuration identity = UNBOUND (to-be-bound at implementation review)`. No committed material defines its construction. This document supplies that missing construction.

### 2.2 Boundary

The configuration identity is **immutable scientific/execution configuration only**. It is exactly one of three separate identity families that must never be merged:

```text
configuration identity        = immutable scientific/execution configuration  (THIS document)
implementation identities     = per-file Git-blob and raw SHA-256 of the committed sources
execution-authorization identity = the later authority document + its non-circular commit binding
```

The configuration identity MUST NOT include any implementation-file identity, any execution-authorization identity, any mutable journal/publication state, any operator-specific absolute path, or any run-time environment value (§12). This separation exists to avoid self-reference and commit-binding cycles (§13).

## 3. Scientific/execution configuration recovered from committed source

The following immutable parameters were recovered by direct static review of the committed v0.2 sources. Each is cited to its committed origin. These are the raw materials of the configuration payload defined in §5.

```text
sequence length N                 = 64            schema_contract: N
accepted-family cardinality K     = 8             schema_contract: K_SYNTHETIC
required generated-pair count     = 8             runner: accepted_fixtures length == K_SYNTHETIC gate
descriptor module import path     = independent_order_sensitive_descriptor_v0_1   runner: exact import token (line 20)
scientific distinction operator   = affine_plus_complement_signature             runner: BoundedRunConfig.descriptor_callable
scientific distinction rule       = exact signature inequality (left != right)   runner: _distinguished_by_signature
fixed-positive pass requirement   = fixed positive must be distinguished          runner: _evaluate_scientific_bundle / findings §6.1
accepted-pair pass requirement    = 8 of 8 distinguished; 7 of 8 = FAIL          findings §6.1
malformed/degenerate control set  = 8 cases, expected input-validation codes      runner: _evaluate_malformed_and_degenerate_controls (lines 604-613)
identity control set              = 7 behaviors                                   runner: _evaluate_identity_controls (lines 657-703)
rotation enumeration count        = 64            runner: required["rotations"] = N
affine enumeration count          = 2048          runner: required["affine_transforms"] = phi(64)*64; schema AFFINE_SEARCH_SPACE_SIZE
affine+complement enum count      = 4096          runner: required["affine_plus_complement_transforms"] = phi(64)*64*2; schema AFFINE_COMPLEMENT_SEARCH_SPACE_SIZE
unit group order phi(64)          = 32            runner: len(_units_mod_n())
sampling used                     = false         runner: sampling_used False; exact counts; no sampled route
pass count                        = 2             runner/schema: two-pass
two-pass independence             = required      findings §6.2
pass-bundle byte identity         = required      findings §6.2
exit-code model                   = 0..5          runner: EXIT_* constants (lines 26-31)
result schema identifier          = torment-brainvision-synthetic-validation-result-v0.2               runner: _result_artifacts
envelope schema identifier        = torment-brainvision-synthetic-validation-execution-envelope-v0.2   runner: _result_artifacts
terminal schema identifier        = torment-brainvision-synthetic-validation-terminal-v0.2             runner: _terminal_payload
configuration schema/version      = v0.2 / 0.2   this specification's validation-configuration domain label
expected manifest path            = research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json   runner: EXPECTED_MANIFEST_PATH
final publication path            = research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_2   runner: FINAL_PUBLICATION_DIR
expected manifest schema          = torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1     schema_contract: MANIFEST_SCHEMA
expected freeze-config sha256     = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263   schema_contract: FROZEN_CONFIGURATION_SHA256
```

## 4. Disposition of the existing 16-field frozen fixture-generation payload

The repository already contains a fully-defined, frozen **fixture-generation (freeze) configuration payload** — the 16-field object built by `frozen_configuration_payload()` in the schema-contract module, with `configuration_schema = "…-fixture-freeze-configuration-v0.1"`, `configuration_version = "0.1"`, and the verified digest `FROZEN_CONFIGURATION_SHA256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263`. Its digest re-derivation is asserted by the committed test `test_provider_parity_for_configuration_payload_contract` (`schema.canonical_configuration_sha256() == FROZEN_CONFIGURATION_SHA256`). This document does not recompute that digest and does not compute the v0.2 configuration digest.

That payload describes **how the frozen Stage S1 family was generated**. The Stage S3B v0.2 configuration identity describes **how the v0.2 run validates that already-frozen family**. They are different scientific objects at different lifecycle stages.

**Decision — choose exactly one of A / B / C / D:**

```text
[ ] A. the complete v0.2 configuration payload
[ ] B. one nested component of a larger v0.2 payload
[X] C. referenced only by its already-frozen configuration hash
[ ] D. outside the v0.2 configuration identity
```

**Selected: C — referenced only by its already-frozen configuration hash.**

Justification, grounded in source:

1. The runner already treats it as an *external, by-hash* expectation, distinct from the v0.2 configuration identity. `BoundedRunConfig.expected_freeze_configuration_sha256` defaults to `schema.FROZEN_CONFIGURATION_SHA256`; the post-contact check compares the manifest's embedded `configuration_identity.configuration_sha256` against that expected hash (`"freeze configuration identity mismatch"`); and the terminal payload records `expected_freeze_configuration_identity = schema.FROZEN_CONFIGURATION_SHA256`. In the same runner, `v0_2_configuration_identity` is a **separate** entry, still `UNBOUND`. The two are never equated in committed code.

2. Re-embedding the full 16-field object (option B) would duplicate data already committed by the existing digest `5f3a568b…`. Under the ordinary SHA-256 collision-resistance assumption, that digest is a compact cryptographic commitment to the frozen payload, including the payload's own schema/domain label. The Correction Specification and the task both prohibit silently equating or needlessly duplicating that hash. A single by-hash reference is therefore the narrower stable reference.

3. It is not option A: the v0.2 configuration identity has its own validation-specific parameters (descriptor operator, distinction rule, control batteries, enumeration counts, two-pass/byte-identity requirement, exit-code and publication contract) that are absent from the freeze payload.

4. It is not option D: the freeze family is the **input route under test**. The v0.2 configuration must pin the expected manifest route, manifest schema, and fixture-generation configuration commitment. Those values do **not** by themselves identify the exact accepted-family bytes or exact manifest contents; the separate `expected_manifest_external_sha256` and `expected_manifest_payload_sha256` identities do that later. This payload therefore carries the manifest path/schema and the freeze-configuration hash as route/configuration expectations, not as a substitute for exact manifest identity.

Therefore the freeze-configuration hash appears in the v0.2 configuration payload **only as an opaque, externally-bound reference value** (field 26 in §5), never as a nested payload, never as the v0.2 identity itself, and never as a claim to identify the exact manifest bytes.

## 5. Configuration payload — complete ordered field set

The configuration identity is the digest (per §6) of a single JSON object, the **v0.2 configuration payload**, whose fields appear in **exactly** the order below. No field may be added, removed, reordered, renamed, retyped, or revalued without producing a different identity.

Provenance legend:

```text
L = literal committed source token or constant (value copied verbatim from committed source)
D = derived (computed from committed constants by a fixed rule stated here)
S = spec-introduced label (a stable string this specification defines for a plan that
    exists in code only as procedure; the exact spelling is the ratification surface, §6.5)
X = externally bound by reference (an opaque identity/label owned by another frozen artifact)
```

| # | field name | JSON type | value | provenance |
|---|---|---|---|---|
| 1 | `configuration_schema` | string | `torment-brainvision-independent-order-sensitive-synthetic-validation-configuration-v0.2` | S |
| 2 | `configuration_version` | string | `0.2` | S |
| 3 | `sequence_length_N` | integer | `64` | L |
| 4 | `accepted_family_cardinality_K` | integer | `8` | L |
| 5 | `required_generated_pair_count` | integer | `8` | D (= K) |
| 6 | `descriptor_module_import_path` | string | `independent_order_sensitive_descriptor_v0_1` | L |
| 7 | `scientific_distinction_operator` | string | `affine_plus_complement_signature` | L |
| 8 | `scientific_distinction_rule` | string | `exact-signature-inequality` | S |
| 9 | `fixed_positive_pass_rule` | string | `fixed-positive-distinguished-required` | S |
| 10 | `accepted_pair_pass_rule` | string | `eight-of-eight-distinguished-required` | S |
| 11 | `malformed_degenerate_control_policy` | string | `eight-case-input-validation-battery-v0.2` | S |
| 12 | `identity_control_policy` | string | `seven-behavior-identity-battery-v0.2` | S |
| 13 | `method_b_enumeration_policy` | string | `full-enumeration-no-sampling-v0.2` | S |
| 14 | `rotation_enumeration_count` | integer | `64` | D (= N) |
| 15 | `affine_enumeration_count` | integer | `2048` | D (= phi(64)·64) |
| 16 | `affine_plus_complement_enumeration_count` | integer | `4096` | D (= phi(64)·64·2) |
| 17 | `pass_count` | integer | `2` | D |
| 18 | `two_pass_independence_required` | boolean | `true` | D |
| 19 | `pass_bundle_byte_identity_required` | boolean | `true` | D |
| 20 | `sampling_used` | boolean | `false` | L |
| 21 | `exit_code_model` | object | see §5.1 | L |
| 22 | `output_schema_identifiers` | object | see §5.2 | L |
| 23 | `expected_manifest_path` | string | `research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json` | L |
| 24 | `final_publication_path` | string | `research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_2` | L |
| 25 | `expected_manifest_schema` | string | `torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1` | L |
| 26 | `expected_freeze_configuration_sha256` | string | `5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263` | X |

**Provenance notes.** `L` means the value is copied from a committed source token or literal constant, not inferred from prose. `D` means the value is derived from committed constants or committed control flow by the fixed rule shown here. `S` means this document introduces the exact ratified spelling for a stable semantic policy that the committed implementation performs procedurally. `X` means an opaque, already-governed external identity is referenced by value. No prose-derived policy, normalized spelling, or reviewer-created label is tagged as `L`.

### 5.1 `exit_code_model` (field 21) — nested object, fixed key order

```json
{"published_pass":0,"published_fail":1,"precontact_refusal":2,"controlled_invalid":3,"consumed_infrastructure_failure":4,"consumed_publication_failure":5}
```

Each value is `L` (runner `EXIT_*` constants, lines 26–31). Keys appear in ascending exit-code order as shown; this order is part of the identity.

### 5.2 `output_schema_identifiers` (field 22) — nested object, fixed key order

```json
{"result":"torment-brainvision-synthetic-validation-result-v0.2","execution_envelope":"torment-brainvision-synthetic-validation-execution-envelope-v0.2","terminal":"torment-brainvision-synthetic-validation-terminal-v0.2"}
```

Each value is `L` (runner `_result_artifacts` / `_terminal_payload`). The key order `result`, `execution_envelope`, `terminal` is part of the identity.

### 5.3 Deliberate exclusions from the payload (see §12 for the full boundary)

The payload intentionally omits, among others: all per-file Git-blob and raw SHA-256 identities; the later execution-authorization identity and its commit; the expected manifest external/payload SHA-256 (these are separate *manifest-expectation* identities, bound elsewhere and still `UNBOUND`); the 16-field freeze payload body (referenced only by hash, §4); the freeze-configuration schema label as a separate field (the field-26 hash already commits to a payload containing that label); the arming/journal/staging directory route names (mutable operational scaffolding rather than scientific configuration — the *input* manifest path and the *output* publication path are retained as the two route choices that pin what is read and where results land).

### 5.4 Minimality disposition

Retained fields classify as follows:

```text
SCIENTIFIC_CONFIGURATION:
  1-20, 25, 26

EXECUTION_ROUTE_CONFIGURATION:
  23

EVIDENCE_OR_PUBLICATION_CONTRACT:
  21, 22, 24
```

Removed or deliberately excluded candidates classify as follows:

```text
IMPLEMENTATION_DETAIL:
  parallelism

BOUNDARY_POSTURE:
  challenger_contact
  frozen_F3_contact
  production_kernel_contact

REDUNDANT_WITH_SEPARATE_IDENTITY:
  implementation-file Git blobs and raw SHA-256 values
  descriptor / descriptor-test file identities
  later execution-authorization identity and authorization commit
  expected manifest external SHA-256
  expected manifest payload SHA-256

REDUNDANT_WITH_RETAINED_SEMANTIC_FIELDS:
  tolerance
  probabilistic_route
  majority_shortcut
  expected_freeze_configuration_schema

UNSUPPORTED_OR_INFERRED:
  any normalized descriptor label other than the exact import path
```

Rationale: `tolerance=false`, `probabilistic_route=false`, and `majority_shortcut=false` are already implied by the retained exact-signature rule, eight-of-eight pass rule, and `full-enumeration-no-sampling-v0.2` policy. Boundary-posture prohibitions remain governing requirements, but they are not part of the stable semantic payload because they are enforced by the implementation/authorization boundary rather than independently defining the configured experiment. Exact manifest external and payload hashes remain separate manifest-expectation identities; they must not be silently folded into this payload.

## 6. Canonical serialization, ordering, encoding, and hash

The serialization is defined to be **byte-identical** to the committed helper `canonical_json_bytes` in the schema-contract module, so that the same standard-library routine already trusted by the freeze lane produces the configuration bytes. The frozen digest reference in §6.6 is evidence about the serializer and referenced freeze configuration; this document does not recompute it.

### 6.1 Canonical ordering

Object member order is **the explicit order of the §5 table** (and §5.1/§5.2 for nested objects). An implementation may use insertion-ordered objects to realize that order, but the Markdown table and nested-object literals are the authority. Keys are **NOT** sorted. Serialization MUST use `sort_keys=False`. The field order in §5 is normative.

### 6.2 Canonical byte serialization, encoding, whitespace, trailing newline

```text
serializer   = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
encoding     = UTF-8            (bytes = text.encode("utf-8"))
separators   = item separator "," and key/value separator ":" with NO whitespace
whitespace   = none anywhere (no spaces, no indentation, no newlines inside the JSON text)
non-ASCII    = escaped (ensure_ascii=True); all payload strings here are already pure ASCII
NaN/Infinity = forbidden (allow_nan=False)
trailing newline = PRESENT — exactly one 0x0A byte is appended AFTER the JSON text
canonical bytes  = text.encode("utf-8") + b"\n"
```

### 6.3 Boolean, integer, list, and object representation

```text
boolean  = JSON true / false (lowercase); Python bool, never 0/1 integers
integer  = bare JSON integer, no quotes, no decimal point, no exponent; strict int (never bool)
string   = double-quoted JSON string, ASCII
object   = JSON object with the fixed key order of §6.1; nested objects follow the same rules
list     = (none required at top level in this payload; if a future ratified field is a list, its
            element order is significant and part of the identity)
```

Note on `strict int, not bool`: the schema-contract module distinguishes `bool` from `int` (`is_strict_int`). Integer fields (3, 4, 5, 14, 15, 16, 17, and the values in §5.1) MUST serialize as integers; boolean fields (18, 19, 20) MUST serialize as `true`/`false`.

### 6.4 Hash algorithm and hex case

```text
algorithm = SHA-256 over the canonical bytes of §6.2
digest    = hashlib.sha256(canonical_bytes).hexdigest()
case      = lowercase hexadecimal, 64 characters, matching is_lower_hex(value, 64)
```

The resulting 64-character lowercase-hex string is the value that later binds `v0_2_configuration_identity`.

### 6.5 Version / domain-separation label

Domain separation is carried by field 1 `configuration_schema = "…-synthetic-validation-configuration-v0.2"` together with field 2 `configuration_version = "0.2"`. This is deliberately distinct from the freeze lane's `"…-fixture-freeze-configuration-v0.1"` / `"0.1"`, so a freeze-configuration payload and a validation-configuration payload can never collide even if their other fields coincided. Fields 1, 2, and the `S`-tagged labels (fields 8–13) are the **ratification surface**: their exact spellings are proposed by this document and must be confirmed by Codex/operator before any hash is computed (§0, §14).

### 6.6 Frozen digest reference — evidence only

The schema-contract module defines the same serializer shape used here (`json.dumps(..., ensure_ascii=True, separators=(",", ":"), allow_nan=False)` plus UTF-8 encoding and one trailing newline) and records the frozen fixture-configuration digest as:

```text
FROZEN_CONFIGURATION_SHA256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
```

That already-governed value is evidence about the serializer and the referenced freeze configuration. This document does not recompute it, does not compute the v0.2 configuration identity, and does not claim any v0.2 digest value.

## 7. Treatment of repository-relative paths

Every path appearing in the payload (fields 23, 24) is, and MUST be:

```text
repository-relative        (rooted at the repository top, e.g. research/brainvision/…)
forward-slash normalized   (POSIX "/" only, even though the operator runs Windows)
case-sensitive as written  (byte-exact casing)
free of drive letters      (no C:\ or similar)
free of operator-specific repository roots  (no C:\TORMENT\… absolute prefix)
free of temporary directories, home directories, or mount points
```

The values in fields 23 and 24 are copied from the runner's `EXPECTED_MANIFEST_PATH` and `FINAL_PUBLICATION_DIR`, which are repository-relative, forward-slash, drive-letter-free source literals. Paths are included **only** as immutable route choices — the manifest route that is read (23) and the output location that is written (24). The mutable operational scaffolding paths (arming/journal/staging) are excluded (§5.3, §12) because they are transient execution mechanics, not scientific route choices, and are in any case bound by the runner file identity.

## 8. Treatment of frozen-provider and manifest identities

```text
frozen freeze-configuration payload  -> referenced ONLY by hash (field 26); never re-embedded (§4, decision C)
frozen Stage S1 manifest route       -> referenced ONLY by repository-relative path (field 23) + manifest schema label (field 25)
frozen manifest external SHA-256     -> NOT in the configuration identity; it is a separate manifest-expectation identity (runner: expected_manifest_external_sha256), still UNBOUND, bound later
frozen manifest payload SHA-256      -> NOT in the configuration identity; separate manifest-expectation identity (runner: expected_manifest_payload_sha256), still UNBOUND, bound later
frozen accepted-family contents       -> NOT identified by the configuration identity; exact contents are bound later through the manifest external/payload SHA-256 identities
frozen descriptor / descriptor-test  -> NOT in the configuration identity; the descriptor route is named by exact import path and operator (fields 6, 7); its file identities are separate frozen implementation identities bound per the governing frozen documents
```

No manifest bytes are read to build the configuration identity; only the frozen configuration *hash* (already committed as `FROZEN_CONFIGURATION_SHA256`) and immutable *labels/paths* are carried. This keeps the configuration identity pre-contact (§9). The exact frozen manifest byte identities are still required later and are not replaced by this payload.

## 9. Calculation boundary

The configuration identity is calculable by a **read-only, standard-library-only** procedure that:

```text
does NOT execute the v0.2 runner
does NOT import the v0.2 runner
does NOT import any repository module
does NOT read the real frozen Stage S1 manifest bytes
does NOT create any authoritative path
does NOT consume execution authority
does NOT publish scientific evidence
does NOT read any environment variable as identity or configuration input
uses ONLY: json + hashlib from the Python standard library, plus the literal payload of §5
```

```text
without manifest-byte contact   = YES. The payload references the freeze configuration by hash
                                  (field 26) and the manifest route by path (field 23) and schema
                                  label (field 25). No manifest byte is opened, read, hashed, or parsed.
without importing/executing runner = YES. Every payload value is a documented literal or a stated
                                  derivation; the digest needs only json + hashlib over §5.
```

Two admissible static calculation/review surfaces, which MUST agree before any later binding:

```text
surface 1 (preferred, self-contained): construct the §5 payload object literally from THIS document
    and apply §6. No repository import at all.
surface 2 (optional static cross-check): read the committed source text directly, without importing
    any module, and verify that the literals/derivations cited in §5 still match the synchronized
    commit before applying §6 to the literal payload.
```

Surface 2 is a review check, not an import authority. It MUST NOT import the runner, schema-contract module, tests, descriptor, provider, or any other repository module. If surface 2 is used, it MUST reproduce surface 1 byte-for-byte; any divergence is a calculation failure (§11).

## 10. Comparison of two independent calculations

Two independent parties (e.g. Claude and Codex, per the verify-each-other protocol) each compute the identity and compare, in this order:

```text
1. canonical bytes equality  — the two canonical byte strings of §6.2 MUST be identical
                               (byte-for-byte, including the single trailing 0x0A).
2. digest equality           — the two 64-character lowercase-hex SHA-256 digests MUST be equal.
3. field-set equality        — the ordered (key, type, value) tuples of the §5 payload MUST match,
                               including nested §5.1/§5.2 key order.
```

Agreement requires all three. Comparison is on the canonical bytes and the digest, never on a re-formatted or pretty-printed rendering. Because the payload is pure ASCII with no floats and a fixed key order, a correct implementation is deterministic across platforms (no locale, CRLF, or float-formatting sensitivity).

## 11. Configuration-identity calculation failure

A calculation is a **failure** — and MUST fail closed, yielding no bound identity — if any of the following holds:

```text
- the field set, names, order, types, or values differ from §5 / §5.1 / §5.2
- key sorting was applied (sort_keys=True) or any whitespace was emitted
- ensure_ascii or allow_nan settings differ from §6.2
- the trailing newline is absent, duplicated, or is CRLF instead of a single 0x0A
- the digest is not lowercase 64-hex, or a non-SHA-256 algorithm was used
- surface 1 and surface 2 (§9) disagree
- the two independent parties' canonical bytes or digests disagree (§10)
- any prohibited input was touched (runner import/execution, repository module import,
  manifest bytes, environment,
  authoritative-path creation) — such a calculation is void regardless of the digest it produced
- an S-tagged label (§6.5) was altered from the ratified spelling, or an X-tagged reference value
  (field 26) does not match the governing frozen constants, or field 25 does not match the
  committed manifest schema literal
```

A failed calculation does not bind `v0_2_configuration_identity`; the runner's pre-contact gate then continues to refuse (`FAIL_PRECONTACT_IDENTITY`) exactly as it does today.

## 12. What remains deliberately outside the configuration identity

```text
runner Git blob / runner raw SHA-256                 -> implementation identity (separate)
runner-test Git blob / runner-test raw SHA-256       -> implementation identity (separate)
schema-contract Git blob / schema-contract raw SHA-256 -> implementation identity (separate)
descriptor / descriptor-test file identities         -> frozen implementation identities (separate)
later execution-authorization identity               -> execution-authorization identity (separate, §13)
execution-authorization document commit              -> bound later under the non-circular HEAD rule (§13)
expected manifest external / payload SHA-256         -> manifest-expectation identities (separate, UNBOUND)
16-field freeze payload body                         -> referenced by hash only (§4, decision C)
mutable journal state (current_state.json, terminal_evidence.json, attempt/read counts, phases)
mutable publication state (staging/journal/final directory existence, publication_status)
operator-specific absolute repository root (e.g. C:\TORMENT\...)
temporary directory paths (arming/staging scaffolding), pytest basetemp
timestamps (terminalized_at, clock output)
hostnames, process identifiers, usernames
environment variables of any kind
repository HEAD / origin-main commit, branch name, Python-runtime version string
```

Rationale: everything above is either (a) an identity of a *different* family that must stay separable to prevent binding cycles (§13), or (b) mutable/run-specific state that would make the configuration identity non-deterministic and therefore useless as a stable fingerprint. The configuration identity answers only "*what experiment is configured*," never "*which exact bytes/commit/run instantiated it*."

## 13. Non-circular binding by the later execution authorization

The configuration identity is a **leaf**: its inputs (§5) are literals, derivations, and already-frozen external references, none of which depends on the runner file bytes, the test file bytes, the schema-contract file bytes, the execution-authorization document, or any commit hash. Therefore it can be computed **before** any of those are bound, with no forward reference.

Binding then proceeds strictly downstream of the leaf, following Correction Specification §17's ordered chain:

```text
step 7  bind implementation identities  : compute runner / runner-test / schema-contract
                                          Git-blob + raw SHA-256 from the committed file bytes,
                                          and compute v0_2_configuration_identity by §6 (the leaf).
                                          The leaf does not read any of the file blobs -> no cycle.
step 8  execution-authorization document : a NEW docs-only authority that RECORDS, by value, the
                                          leaf digest and the file identities from step 7, plus the
                                          manifest-expectation identities. It is referenced BY them,
                                          never the reverse -> the leaf never mentions the authority.
step 9  latest-commit authorization binding (non-circular execution-HEAD rule): the authorization is
                                          bound to the latest synchronized implementation commit
                                          WITHOUT requiring the authorization commit to embed its own
                                          hash. The execution HEAD is validated at run time by the
                                          runner's repository-state check (HEAD == origin/main, clean,
                                          supported Python), not by self-embedding -> no self-reference.
```

Acyclicity, stated as a dependency direction:

```text
literals / derivations / frozen-external-refs  ->  v0_2_configuration_identity (leaf)
committed file bytes                            ->  file implementation identities
{ leaf, file identities, manifest-expectation identities }  ->  execution-authorization document
execution-authorization document + synchronized commit      ->  runtime authorization
```

No arrow returns to the leaf. The configuration identity is computed once, from immutable material, and is thereafter only *referenced by value* by higher layers. This is exactly why fields listed in §12 (file blobs, the authorization identity/commit, mutable state) are excluded: admitting any of them would create a back-edge into the leaf and reintroduce the self-reference / commit-binding cycle this architecture forbids.

## 14. Draft status and standing prohibitions

```text
document remains  = docs-only, non-executing, non-authorizing, pre-contact, non-production, non-kernel
this document      = defines construction only; binds nothing; computes no v0.2 hash
ratification surface = fields 1-2 configuration schema/version labels + the S-tagged labels
                       (fields 8-13), plus the exact ordered 26-field include/exclude decision in §5.
next step          = Codex review of this construction; on acceptance and label ratification, the leaf
                     digest is computed by §6 during the later implementation-review identity-binding
                     step and recorded into the separate v0.2 execution-authorization document.
all prohibitions in §0 remain active and unchanged.
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result, and it authorizes no execution and no real-manifest contact.
