# TORMENT Brainvision Independent Order-Sensitive Synthetic Fixture Freeze Specification v0.1

## Document status

```text
document_type = docs-only specification
specification_version = v0.1
implementation_authorized = False
execution_authorized = False
```

Authoritative repository baseline:

```text
HEAD = origin/main = a7667c2
working tree = clean
```

Committed parent specification:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
```

Recommended path:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
```

This document specifies the synthetic-fixture infrastructure that must exist and be frozen before the Independent Order-Sensitive Descriptor Challenger v0.1 is implemented or run. It completes only specification stage S1A. It does not authorize implementation or execution.

## 0. Authority posture and fixed historical disposition

The completed frozen N64/K=3 F3 result remains permanently:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

At acceptance of this specification, the authority state is:

```text
FORMAL_HOLD = active
Mode_0 = active

SYNTHETIC_FIXTURE_FREEZE_SPECIFIED = True

SYNTHETIC_FIXTURE_GENERATOR_IMPLEMENTATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_VERIFIER_IMPLEMENTATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_GENERATION_AUTHORIZED = False
SYNTHETIC_FIXTURE_EXECUTION_AUTHORIZED = False
SYNTHETIC_FIXTURE_FREEZE_AUTHORIZED = False
CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_INPUT_ACCESS_AUTHORIZED = False
CHALLENGER_FROZEN_FAMILY_EVALUATION_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
RETAINED_EVIDENCE_MODIFICATION_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

Nothing in this fixture-freeze branch may amend, weaken, reinterpret, rescue, or replace the completed F3 result. A future synthetic freeze produces preregistered controls only; it establishes no scientific claim about the frozen benchmark and does not retroactively change the F3 verdict.

## 1. Purpose

This document specifies an independent synthetic-fixture generator, verifier, and deterministic freezer that will eventually:

1. independently verify the fixed homometric fixture;
2. enumerate the admitted `C+D` / `C-D` construction family;
3. select the first eight unique eligible pairs descriptor-blindly;
4. emit a deterministic frozen manifest;
5. prove byte-identical replay before the challenger is implemented or run.

The infrastructure exists only to provide preregistered synthetic controls.

It must never use challenger descriptor values to generate, accept, reject, rank, deduplicate, or freeze fixtures.

All selection information is drawn from raw supports and raw lower-order and triple-count certificates only. No challenger descriptor output is consulted at any point in generation, verification, deduplication, or freezing.

## 2. Isolation boundary

Reserve future implementation under:

```text
research/brainvision/
```

The generator and verifier must not import or call:

```text
independent_order_sensitive_descriptor_v0_1.py
PsiTRS
historical F3 modules
historical asymmetry-audit modules
torment_service
production services
```

The primary mathematical functions must be:

```text
offline
pure
deterministic
integer-only
filesystem-independent after input delivery
environment-independent
network-disconnected
non-production
```

No random numbers, timestamps, locale-sensitive ordering, process identity, machine identity, or unordered-container iteration may influence accepted fixtures or serialized output.

## 3. Fixed fixture

The fixed fixture is specified exactly:

```text
C = {0,25,55}
D = {0,49,57}

H0 = C + D
H1 = C - D
```

with:

```text
H0 = {0,10,18,25,40,48,49,55,57}
H1 = {0,6,7,15,25,32,40,55,62}
```

The future independent verifier must recompute, from the raw supports alone:

```text
weight(H0) = weight(H1) = 9
full periodic A2 equality
step-one transition-table equality
affine inequivalence
affine-plus-complement inequivalence
direct labeled nondegenerate triple-array difference
exact disagreement count = 288 of 3906
```

The verifier must not treat the values written in this specification as proof. Every fixed-fixture certificate must be recomputed from the raw supports.

A mismatch in any fixed-fixture certificate must block freezing with a deterministic failure code.

## 4. Exact generated construction family

Define:

```text
C = {0,c1,c2}
D = {0,d1,d2}

A = sorted ascending tuple of distinct residues
    {(c+d) mod 64 : c in C, d in D}

B = sorted ascending tuple of distinct residues
    {(c-d) mod 64 : c in C, d in D}
```

Collisions are collapsed by set construction before cardinality checks.

Enumerate seed tuples in exact nested order:

```text
for c1 = 1..62
    for c2 = c1+1..63
        for d1 = 1..62
            for d2 = d1+1..63
```

This loop order is the canonical lexicographic seed order over `(c1, c2, d1, d2)`.

No parallel execution may alter acceptance order.

## 5. Exact binary and lower-order objects

For support `S`, define:

```text
binary(S)_i = 1 when i in S
binary(S)_i = 0 otherwise
```

Define:

```text
weight(S) = cardinality(S)

A2_S(d) =
    sum over i in Z_64 of
    binary(S)_i * binary(S)_(i+d mod 64)
```

for `d = 0..63`.

Define the step-one table in fixed order:

```text
[[n00,n01],[n10,n11]]
```

with rows indexed by `x_i = 0,1` and columns by `x_(i+1 mod 64) = 0,1`.

Define the direct labeled triple array:

```text
M3_S(a,b) =
    sum over i in Z_64 of
    binary(S)_i *
    binary(S)_(i+a mod 64) *
    binary(S)_(i+b mod 64)
```

using the parent specification's fixed 3906-entry `L3` order:

```text
a = 1..63
b = 1..63
omit b = a
```

These are fixture certificates, not challenger descriptor outputs. They are computed directly from the raw supports and never through the challenger tensor.

## 6. Eligibility

A generated pair `(A,B)` is eligible exactly when:

```text
cardinality(A) = 9
cardinality(B) = 9
A != B
full A2(A) = full A2(B)
step-one tables match
no affine relabeling maps A to B
no affine-plus-complement relabeling maps A to B
M3(A) != M3(B) in fixed L3 order
```

All checks are exact.

No tolerance or floating-point arithmetic is permitted.

The verifier must emit the exact set of differing `L3` indices and the exact disagreement count.

A seed that fails eligibility is rejected without invoking or consulting the challenger.

Each ineligible seed records exactly one `eligibility_rejection_reason`.

Eligibility predicates are evaluated using first-failure semantics in this exact order:

```text
A_CARDINALITY_NOT_9
B_CARDINALITY_NOT_9
IDENTICAL_SUPPORTS
A2_MISMATCH
TRANSITION_TABLE_MISMATCH
AFFINE_EQUIVALENT
AFFINE_COMPLEMENT_EQUIVALENT
TRIPLE_ARRAY_EQUAL
```

The predicates corresponding to those reasons are:

```text
A_CARDINALITY_NOT_9:
    cardinality(A) != 9

B_CARDINALITY_NOT_9:
    cardinality(B) != 9

IDENTICAL_SUPPORTS:
    A = B

A2_MISMATCH:
    full A2(A) != full A2(B)

TRANSITION_TABLE_MISMATCH:
    transition_table(A) != transition_table(B)

AFFINE_EQUIVALENT:
    at least one affine relabeling maps A to B

AFFINE_COMPLEMENT_EQUIVALENT:
    at least one affine-plus-complement relabeling maps A to B

TRIPLE_ARRAY_EQUAL:
    M3(A) = M3(B) in the complete fixed L3 order
```

Once a predicate fails, later eligibility predicates are not evaluated for the rejection diagnostic for that seed.

`eligibility_rejection_counts` is serialized as an object containing exactly the eight reason keys above, in exactly that order, with nonnegative integer counts.

Reasons with count zero remain present.

These eligibility certificates are descriptor-blind. They are necessary preconditions computed from raw supports and raw triple counts. Whether the challenger's own canonical signatures ultimately distinguish an accepted fixture is validated separately in a later stage and is not a condition for freezing.

## 7. Exact affine checks

Let:

```text
U_64 = all odd residues in 0..63
```

`U_64` contains the 32 odd residues modulo 64.

For support `S`, affine transformation is:

```text
affine(S,u,v) =
    {(u*s+v) mod 64 : s in S}
```

where:

```text
u in U_64
v in Z_64
```

Affine equivalence means one transformed support equals the other.

Affine-plus-complement equivalence means either:

```text
affine(A,u,v) = B
```

or:

```text
Z_64 \ affine(A,u,v) = B
```

for at least one exact `(u,v)`.

Report affine-only and affine-plus-complement certificates separately.

Reflection is already included by:

```text
u = -1 mod 64
```

## 8. Exact duplicate key

For every support `S`, enumerate all:

```text
u in U_64 in ascending integer order
v = 0..63
q = 0,1
```

Define:

```text
S_(u,v,0) = affine(S,u,v)
S_(u,v,1) = Z_64 \ affine(S,u,v)
```

There are exactly `32 * 64 * 2 = 4096` transformed supports.

Serialize a transformed support as exactly 64 ASCII characters ordered by residue `0..63`, using `1` where the residue is present and `0` otherwise.

Define:

```text
member_orbit_key(S) =
    lexicographically smallest of the 4096 strings
```

For an eligible pair `(A,B)`:

```text
key_A = member_orbit_key(A)
key_B = member_orbit_key(B)

pair_duplicate_key(A,B) =
    [key_A,key_B] when key_A <= key_B
    [key_B,key_A] otherwise
```

Because eligibility requires `A` and `B` to be affine-plus-complement inequivalent, `key_A != key_B` for every eligible pair.

The generator retains an eligible seed exactly when its pair key has not appeared for an earlier eligible seed.

The first eight previously unseen eligible pair keys in canonical seed order form the synthetic family.

No accepted fixture may be skipped or replaced based on a future challenger result.

## 9. Freeze algorithm

The deterministic freeze algorithm is specified exactly:

```text
verify fixed fixture
calculate fixed_pair_duplicate_key from the verified fixed pair (H0,H1)
initialize seen_pair_keys as a mathematical set containing fixed_pair_duplicate_key
initialize accepted fixtures as an empty ordered list
scan seeds in canonical order
construct A and B
evaluate eligibility
if ineligible:
    record deterministic rejection reason
if eligible:
    calculate pair_duplicate_key
    if key already seen:
        record DUPLICATE_PAIR_KEY
    otherwise:
        add key to seen_pair_keys
        append the complete fixture record
stop immediately after eight fixtures are accepted
```

The fixed fixture is a separate implementation positive control and is not one of the eight generated controls.

An otherwise eligible generated seed whose `pair_duplicate_key` equals `fixed_pair_duplicate_key` is recorded as an eligible duplicate and is not accepted.

Therefore the final synthetic control set consists of:

```text
one fixed fixture
plus
eight generated fixtures that are unique from the fixed fixture and from one another
```

`DUPLICATE_PAIR_KEY` is a search diagnostic reason, not a failure code.

It is recorded when an otherwise eligible seed has a `pair_duplicate_key` already present in `seen_pair_keys`, including equality with `fixed_pair_duplicate_key`.

Every such seed increments `eligible_duplicate_count` by exactly one.

It does not populate `ordered_failure_codes`.

The frozen family order is acceptance order.

Termination is deterministic: the scan stops after the eighth acceptance, or after the canonical seed space is exhausted, whichever occurs first. Seed exhaustion with fewer than eight accepted fixtures is an `INSUFFICIENT_UNIQUE_FIXTURES` outcome and blocks freezing.

The fixture generator must also report:

```text
total seeds visited
eligibility rejection counts by canonical reason
eligible duplicate count
accepted seed-order positions
terminal seed tuple
terminal status
```

No implementation may rely on dictionary or set iteration order for serialization.

## 10. Manifest schema

The canonical manifest must contain exactly these top-level fields in exactly this order:

```text
schema
generator_id
verifier_id
N
K_synthetic
seed_enumeration_policy
construction_policy
eligibility_policy
duplicate_policy
family_frozen
fixed_fixture
accepted_fixtures
search_diagnostics
source_identity
configuration_identity
validation
ordered_failure_codes
manifest_payload_sha256
```

No additional top-level field is permitted.

The fixed scalar values are:

```text
schema =
torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1

generator_id =
independent-order-sensitive-synthetic-fixture-generator-v0.1

verifier_id =
independent-order-sensitive-synthetic-fixture-verifier-v0.1

N =
64

K_synthetic =
8
```

`family_frozen` is a JSON boolean.

It is `false` in every independent pass manifest, non-authoritative manifest, partial failure manifest, and candidate manifest.

It is `true` only in the final authoritative manifest produced after successful two-pass replay comparison and deterministic finalization.

### 10.1 Fixed-fixture object

`fixed_fixture` is exactly one object with keys in this order:

```text
C
D
support_H0
support_H1
binary_H0
binary_H1
weight_H0
weight_H1
A2_H0
A2_H1
transition_table_H0
transition_table_H1
affine_inequivalence_certificate
affine_complement_inequivalence_certificate
triple_disagreement_count
triple_disagreement_indices
member_orbit_key_H0
member_orbit_key_H1
pair_duplicate_key
validation
```

Supports are ascending integer arrays.

Binary sequences are flat arrays of exactly 64 integers in `{0,1}`.

`A2_H0` and `A2_H1` are flat 64-entry integer arrays ordered by `d = 0..63`.

Transition tables are:

```text
[[n00,n01],[n10,n11]]
```

The fixed-fixture `validation` object has keys in this order:

```text
valid
failure_code
detail
```

For a valid fixed fixture it is exactly:

```json
{"valid":true,"failure_code":null,"detail":null}
```

### 10.2 Accepted-fixture records

Each accepted fixture is exactly one object with keys in this order:

```text
family_index
seed_order_position
seed_tuple
C
D
support_A
support_B
binary_A
binary_B
weight_A
weight_B
A2_A
A2_B
transition_table_A
transition_table_B
affine_inequivalence_certificate
affine_complement_inequivalence_certificate
triple_disagreement_count
triple_disagreement_indices
member_orbit_key_A
member_orbit_key_B
pair_duplicate_key
```

`family_index` is the zero-based acceptance index.

A successful family has exactly:

```text
family_index = 0..7
```

`seed_order_position` is the zero-based ordinal in canonical seed enumeration.

The first seed:

```text
(1,2,1,2)
```

has:

```text
seed_order_position = 0
```

`seed_tuple`, `C`, and `D` are four-, three-, and three-entry ascending integer arrays respectively.

`weight_A` and `weight_B` are serialized separately even though eligibility requires both to equal 9.

`A2_A` and `A2_B` are separate 64-entry arrays.

`transition_table_A` and `transition_table_B` are separate 2×2 arrays.

Triple-disagreement indices are ordered `[a,b]` arrays in fixed `L3` order.

### 10.3 Affine certificate objects

For a valid accepted fixture:

```text
affine_inequivalence_certificate
```

is exactly:

```json
{"equivalent":false,"search_space_size":2048,"first_equivalence_mapping":null}
```

and:

```text
affine_complement_inequivalence_certificate
```

is exactly:

```json
{"equivalent":false,"search_space_size":4096,"first_equivalence_mapping":null}
```

Object keys appear in exactly the order shown.

A future verifier may retain richer evidence internally, but no additional certificate field may appear in the canonical manifest.

### 10.4 Search diagnostics

`search_diagnostics` is exactly one object with keys in this order:

```text
total_seeds_visited
eligibility_rejection_counts
eligible_duplicate_count
accepted_seed_order_positions
terminal_seed_tuple
terminal_status
```

`total_seeds_visited` is a nonnegative integer and includes the terminal visited seed whenever seed scanning begins.

`accepted_seed_order_positions` is an array of zero-based seed ordinals in acceptance order.

`terminal_seed_tuple` is:

```text
null
```

when seed scanning never begins.

Otherwise it is the final visited seed tuple as a four-entry integer array.

`terminal_status` is exactly one of:

```text
FIXED_FIXTURE_FAILURE
ACCEPTED_EIGHT
SEED_SPACE_EXHAUSTED
```

These are the only terminal-status values permitted inside a successfully serialized canonical manifest.

Boundary, source-ownership, serialization, hash-construction, hash-verification, and replay-comparison failures that prevent or invalidate canonical manifest production are process-level outcomes. They must not be represented as `terminal_status` values inside a canonical manifest.

Their exact reporting belongs to the later separately authorized execution-envelope specification.

For successful candidate pass manifests and the final authoritative manifest:

```text
terminal_status = ACCEPTED_EIGHT
```

For seed-space exhaustion with fewer than eight accepted fixtures:

```text
terminal_status = SEED_SPACE_EXHAUSTED
```

For a fixed-fixture canonical failure manifest:

```text
terminal_status = FIXED_FIXTURE_FAILURE
```

### 10.5 Source, configuration, and validation objects

`source_identity` is exactly one object with keys in this order:

```text
generator_source_path
generator_git_blob
generator_raw_sha256
verifier_source_path
verifier_git_blob
verifier_raw_sha256
test_source_identities
repository_commit
python_version
```

`test_source_identities` is an array ordered by normalized source path. Each entry has keys:

```text
source_path
git_blob
raw_sha256
```

`configuration_identity` is exactly one object with keys in this order:

```text
configuration_payload
configuration_sha256
```

`configuration_payload` is the exact canonical configuration object specified by the later S1B authorization.

`configuration_sha256` is lowercase hexadecimal of length 64 over the canonical UTF-8 configuration bytes including one terminal LF.

`validation` is exactly one object with keys in this order:

```text
valid
failure_stage
detail
```

For a successful candidate pass manifest:

```json
{"valid":true,"failure_stage":null,"detail":null}
```

For a canonical failure manifest:

```text
valid = false
failure_stage = the canonical stage identifier
detail = null
```

No free-form exception text is permitted.

### 10.6 Canonical manifest hashing

`manifest_payload_sha256` is lowercase hexadecimal consisting of exactly 64 ASCII characters.

The payload projection is the complete manifest object with only the `manifest_payload_sha256` field removed.

The remaining top-level fields preserve their declared relative order.

Canonical payload bytes are the canonical compact UTF-8 JSON serialization of that projection, including exactly one terminal LF.

The payload SHA-256 is computed over those complete canonical payload bytes.

Canonical manifest bytes are the canonical compact UTF-8 JSON serialization of the complete manifest containing the populated `manifest_payload_sha256` value, including exactly one terminal LF.

The external manifest SHA-256 identity is computed over the complete canonical manifest bytes.

The external manifest SHA-256 is not embedded inside the manifest.

The payload hash is non-circular because its own field is excluded from the payload projection.

## 11. Deterministic serialization

Serialization requirements:

```text
UTF-8 without BOM
LF only
one terminal LF
compact JSON separators
base-10 integers
JSON true/false/null
no NaN
no Infinity
no negative zero
fixed key order
fixed array order
```

Human-readable output, if later authorized, must derive from the canonical JSON and must not alter it.

## 12. Two-pass authoritative replay

A future authoritative freeze must perform two independent generation and verification passes from the same frozen source and configuration identities.

Pass 2 must not reuse pass 1 in-memory:

```text
supports
certificates
orbit keys
pair keys
seen-key state
accepted-fixture records
diagnostics
manifest objects
serialized bytes
payload hashes
manifest hashes
```

Each pass must independently:

```text
read the same immutable configuration bytes
reconstruct and verify the fixed fixture
initialize seen_pair_keys with fixed_pair_duplicate_key
enumerate canonical seeds from the beginning
compute all certificates
select the first eight generated fixtures
build a candidate manifest with family_frozen = false
serialize canonical payload bytes
populate manifest_payload_sha256
serialize canonical candidate-manifest bytes
compute the external candidate-manifest SHA-256
```

Comparison occurs only after both complete pass outputs exist.

The two candidate passes must have:

```text
identical canonical payload bytes
identical manifest_payload_sha256 values
identical canonical candidate-manifest bytes
identical external candidate-manifest SHA-256 values
identical accepted-fixture order
identical diagnostics
```

If any comparison fails:

```text
family_frozen = false
```

and no authoritative frozen manifest is produced.

If every comparison succeeds, the deterministic finalization step:

```text
takes the complete verified candidate manifest
changes only family_frozen from false to true
recomputes canonical payload bytes
recomputes manifest_payload_sha256
serializes the complete final manifest
computes the external final-manifest SHA-256
```

No accepted fixture, certificate, diagnostic, identity, policy, or other field may change during finalization.

Only the final manifest produced by this successful finalization has:

```text
family_frozen = true
```

A single generation pass or an unmatched candidate manifest always has:

```text
family_frozen = false
```

## 13. Source and configuration identity

A later implementation authorization must freeze:

```text
generator source path
generator Git blob
generator raw SHA-256
verifier source path
verifier Git blob
verifier raw SHA-256
test source identities
schema identity
configuration payload
configuration SHA-256
repository commit identity
Python version
```

A Git blob hash and a Windows raw-file SHA-256 are distinct identities whenever line-ending normalization applies: the Git blob hash is computed over the repository object bytes, while the raw-file hash is computed over the exact on-disk bytes. Neither identity may silently substitute for the other. Both must be recorded and checked independently.

## 14. Required static boundary checks

A future verifier must reject prohibited imports and source-ownership violations.

Reserve checks for:

```text
torment_service imports
PsiTRS imports
historical F3 imports
challenger descriptor imports
network imports
camera or screen-capture imports
subprocess production contact
environment-gate reads
retained-evidence paths
frozen K=3 paths
files outside the authorized research/brainvision ownership boundary
```

## 15. Required tests

Reserve tests for:

```text
fixed fixture support reconstruction
fixed fixture weight
fixed fixture A2 equality
fixed fixture transition equality
fixed fixture affine inequivalence
fixed fixture affine-plus-complement inequivalence
fixed fixture exact 288 disagreement count
seed-order determinism
collision collapse
eligibility rejection reasons
member-orbit-key invariance
pair-key slot-exchange invariance
duplicate suppression
first-eight stopping rule
manifest key and array order
manifest payload hashing
two-pass replay
forbidden-import detection
source-path ownership
no challenger import
no frozen-family contact
```

Tests must not implement or import the challenger descriptor.

## 16. Failure codes

Reserve a deterministic ordered vocabulary including:

```text
FIXED_FIXTURE_RECONSTRUCTION_FAILURE
FIXED_FIXTURE_LOWER_ORDER_CERTIFICATE_FAILURE
FIXED_FIXTURE_AFFINE_CERTIFICATE_FAILURE
FIXED_FIXTURE_AFFINE_COMPLEMENT_CERTIFICATE_FAILURE
FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE
GENERATOR_CONFIGURATION_INVALID
SEED_ENUMERATION_FAILURE
CONSTRUCTION_FAILURE
ELIGIBILITY_CERTIFICATE_FAILURE
DUPLICATE_KEY_FAILURE
INSUFFICIENT_UNIQUE_FIXTURES
MANIFEST_SCHEMA_FAILURE
SERIALIZATION_FAILURE
HASH_IDENTITY_FAILURE
REPLAY_MISMATCH
FORBIDDEN_IMPORT_DETECTED
SOURCE_OWNERSHIP_FAILURE
PROHIBITED_CHALLENGER_CONTACT
PROHIBITED_FROZEN_FAMILY_CONTACT
PRODUCTION_BOUNDARY_VIOLATION
UNAUTHORIZED_EXECUTION
```

`DUPLICATE_KEY_FAILURE` is reserved only for an implementation or integrity defect, including:

```text
an accepted fixture list containing repeated pair_duplicate_key values
acceptance of a generated fixture matching fixed_pair_duplicate_key
a malformed member_orbit_key or pair_duplicate_key
a pair_duplicate_key inconsistent with its two member keys
eligible_duplicate_count inconsistent with the seed diagnostics
```

Ordinary duplicate eligible seeds encountered during canonical generation use the `DUPLICATE_PAIR_KEY` diagnostic and are not failures.

When multiple failures occur, codes must be emitted in the vocabulary order above.

Duplicate eligible seeds encountered during normal generation are diagnostics, not failures. They are recorded in the eligible-duplicate diagnostics and do not populate `ordered_failure_codes`.

## 17. Failure artifact behavior

If fixed-fixture verification fails, a canonical failure manifest may be produced with:

```text
family_frozen = false
accepted_fixtures = []
total_seeds_visited = 0
accepted_seed_order_positions = []
terminal_seed_tuple = null
terminal_status = FIXED_FIXTURE_FAILURE
```

and the applicable fixed-fixture failure code.

If the canonical seed space is exhausted with fewer than eight unique generated fixtures, a canonical failure manifest may be produced with:

```text
family_frozen = false
accepted_fixtures = all accepted partial fixtures in acceptance order
terminal_status = SEED_SPACE_EXHAUSTED
```

and:

```text
INSUFFICIENT_UNIQUE_FIXTURES
```

If a boundary or source-ownership check fails before canonical manifest construction, no manifest is produced. The failure is reported through the later execution envelope or process failure channel.

If serialization fails, no canonical manifest is produced.

If hash construction or verification fails, no authoritative manifest is produced.

If the two candidate passes disagree, no final authoritative manifest is produced. Replay mismatch is reported through the later execution envelope or process failure channel.

Whenever a canonical failure manifest is successfully produced:

```text
family_frozen = false
validation.valid = false
ordered_failure_codes contains canonical §16 codes in vocabulary order
manifest_payload_sha256 is populated normally
```

Multiple canonical failure codes may be present only when they arise from independently completed checks.

A later separately authorized execution-envelope specification must define process-level failures that prevent canonical manifest production.

## 18. Future success and failure criteria

A future S1 execution succeeds only when:

```text
all fixed-fixture certificates pass
exactly eight unique eligible fixtures are accepted
the first-eight rule is obeyed
all required fixture records are complete
all static boundaries pass
two authoritative passes are byte-identical
family_frozen = true
ordered_failure_codes = []
```

Any certificate failure, insufficient family size, schema failure, boundary failure, or replay mismatch blocks freezing.

A failed freeze is a valid engineering failure.

It does not authorize changing the challenger, weakening eligibility, skipping seeds, removing fixtures, or contacting the frozen K=3 family.

## 19. Stage separation

Define:

```text
S1A = fixture-freeze specification
S1B = separately authorized generator/verifier implementation
S1C = separately authorized synthetic-family freeze execution
S2 = separately authorized challenger implementation
S3 = separately authorized challenger synthetic validation
```

This document completes only S1A.

It must not authorize S1B, S1C, S2, or S3.

## 20. Final disposition

This specification fixes exactly:

```text
K_synthetic = 8
selection = first eight unique eligible pairs
selection information = raw construction and certificates only
challenger information used in selection = none
frozen K=3 contact = prohibited
implementation authorized = False
execution authorized = False
```

The next permitted project action is a docs-only review of this specification, followed only later, and only under a separate authorization, by S1B.

No implementation or execution follows automatically from this document.
