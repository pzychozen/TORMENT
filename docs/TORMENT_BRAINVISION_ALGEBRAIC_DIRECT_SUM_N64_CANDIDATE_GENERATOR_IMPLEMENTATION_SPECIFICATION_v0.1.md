# TORMENT Brainvision Algebraic Direct-Sum N=64 Candidate Generator Implementation Specification v0.1

## 0. Status / authority

**DOCS-ONLY implementation specification. Non-implementing, non-executing.** This note specifies a future
deterministic, descriptor-blind candidate generator. It implements nothing, enumerates no parameter domain,
produces no candidate stream, freezes no family, and runs no ΨTRS or descriptor evaluation.

```text
FORMAL_HOLD_active = True
Mode_0_active      = True

DOCUMENTATION_AUTHORIZED             = True
GENERATOR_IMPLEMENTATION_AUTHORIZED  = False
N64_WITNESS_GENERATION_AUTHORIZED    = False
PsiTRS_EVALUATION_AUTHORIZED          = False
SCIENTIFIC_INFERENCE_AUTHORIZED       = False
```

Prepared after synchronization to `HEAD = 8aefb0a` (branch `main`). The tracked working tree was clean before
drafting. At review time the sole working-tree entry is this untracked specification document.

Brainvision remains offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production,
descriptor-blind, and descriptive-only. No SRG, quantum-clock, triangular-rotor, FPS, kernel-spin, or Z-vector
interpretation may enter generator logic, ordering, ranking, acceptance, rejection, deduplication, or budgeting.

Immutable — never modified or proposed for modification:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

## 1. Scope

Specifies **only** the future candidate generator for the route selected in the route-decision document: its
parameter domain, normalization, deterministic order, candidate construction, exact deduplication,
candidate-stream emission, structural budget, terminal semantics, identity/hashing, replay artifact,
independence tests, failure codes, and required tests.

Out of scope: any witness predicate decision, any family decision, any ΨTRS or descriptor evaluation, any
generator execution, any dependency addition, and any modification to the accepted verifier, freezer,
serializer, or their specifications.

## 2. Governing documents and directly inspected sources

```text
docs/TORMENT_BRAINVISION_N64_CANDIDATE_GENERATOR_ROUTE_DECISION_v0.1.md              (route selection)
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_HIGHER_ORDER_WITNESS_VERIFIER_AND_FREEZE_INFRASTRUCTURE_IMPLEMENTATION_SPECIFICATION_v0.1.md
research/brainvision/witness_canonical_json_v0_1.py
research/brainvision/witness_family_verifier_v0_1.py
research/brainvision/witness_family_freeze_v0_1.py
tests/research/test_brainvision_witness_family_verifier_v0_1.py
tests/research/test_brainvision_witness_family_freeze_v0_1.py
```

Interface facts confirmed by direct inspection and binding here:

```text
STREAM_SCHEMA_NAME    = "brainvision_descriptor_blind_candidate_stream"
STREAM_SCHEMA_VERSION = "0.1"
SUPPORTED_MODES       = ("REFERENCE_REGRESSION_N12", "PRIMARY_CANDIDATE_N64")
MODE_N                = {"REFERENCE_REGRESSION_N12": 12, "PRIMARY_CANDIDATE_N64": 64}
VALID_TERMINAL_STATUS = ("stream_completed","budget_exhausted","route_incomplete","dependency_unavailable")
K_FAMILY              = 3
SERIALIZER_NAME/VERSION = "witness_canonical_json_v0_1" / "0.1"
canonical JSON        = ensure_ascii, sort_keys, (",",":"), allow_nan=False, NO trailing newline
envelope(name,payload) = {name: payload, name+"_sha256": SHA256(canonical_json_bytes(payload))}  (nonrecursive)
source_file_sha256     = SHA256 of raw file bytes (no newline normalization, no path bytes)
is_lower_hex_64        = exactly 64 lowercase hex characters
```

**Exactness asymmetry (must not be confused).** The accepted stream validator requires each record to be a
mapping carrying a strict-int, gap-free `candidate_generation_index` and (for verification) `raw_support_A` /
`raw_support_B`; it does **not** enforce an exact record key set, so an optional `generator_diagnostics` key is
tolerated. The pair **certificate**, by contrast, enforces an exact key set at every level. The generator relies
on the former and never assumes the latter regime applies to stream records.

## 3. Frozen route mathematics

```text
N = 64
|U| = 3
|V| = 4

A = U + V  mod 64
B = U + (-V) mod 64

candidate weight = 12
```

For every parameter tuple the generator computes **both** directness predicates:

```text
all 12 values  u + v  are distinct mod 64
all 12 values  u - v  are distinct mod 64
```

These are mathematically equivalent (a collision `u1+v1 = u2+v2` rearranges to `u1-v2 = u2-v1`, and conversely).
Both are nevertheless computed and compared as a **deterministic internal consistency guard**; disagreement is an
execution failure (§15), never an ordinary rejection. Only collision-free tuples may emit a candidate record.

The generator relies on the direct-sum theorem for exactly one property — equal complete periodic autocorrelation
of `A` and `B` — and claims nothing else. It must **not** claim or decide:

```text
primitive period 64 ; affine inequivalence ; affine-plus-complement inequivalence ;
direct-complement status ; triple-array G-nonalignment ; family member uniqueness ;
mutual G-inequivalence ; distinct autocorrelation classes ; pair validity ; family validity
```

All of those remain exclusively and independently recomputed by the accepted verifier and freezer from raw
supports.

## 4. Module, test, and identity naming

```text
generator module   : research/brainvision/algebraic_direct_sum_n64_candidate_generator_v0_1.py
generator tests    : tests/research/test_brainvision_algebraic_direct_sum_n64_candidate_generator_v0_1.py
generator identity : brainvision-algebraic-direct-sum-z64-candidate-generator-v0.1
```

Direct inspection found no contradiction requiring a different layout. v0.1 adds **no** CLI runner, **no**
fixture module, **no** dependency file, and **no** second implementation module. The generator is a single
module exposing library operations; stream emission is a return value, not a process-level side effect.

## 5. Parameter normalization and deterministic order

**Canonical translation representative.** For a nonempty support tuple `S`:

```text
translation_normal_form(S) =
  lexicographically smallest ascending tuple among
  { sorted((s-a) mod 64 for s in S) : a in S }
```

Only tuples equal to their own translation normal form are enumerated. Consequently `0` belongs to every
enumerated `U` and every enumerated `V`, and translation duplicates are removed structurally.

**V-sign normalization.**

```text
V_negated_normal_form = translation_normal_form({ (-v) mod 64 : v in V })
retain only V <=lex V_negated_normal_form
```

This removes the duplicate parameterization that merely exchanges `U+V` and `U-V`.

**U/V role separation.** Swapping `U` and `V` is **not** treated as a symmetry; `|U| = 3` and `|V| = 4` are
frozen and their roles are distinct.

**Unit-affine handling (v0.1).**

```text
no unit-affine parameter normalization
no generator-side G-orbit suppression
no complement-based suppression
```

This deliberately avoids duplicating or partially importing the verifier's authoritative G-equivalence
mathematics.

**Total parameter order (frozen).**

```text
1. enumerate canonical sign-normalized V tuples in ascending lexicographic order
2. for each V, enumerate canonical U tuples in ascending lexicographic order
3. the exact parameter-tuple order is lexicographic on (V,U)

parameter_order_identity =
  V_LEXICOGRAPHIC_OUTER_U_LEXICOGRAPHIC_INNER

worker_count       = 1
randomness_enabled = False
random_seed        = 0        (identity sentinel only; never consulted)
```

This is a deterministic breadth policy only. It makes no claim that variation in either `U` or `V` is
scientifically preferable. No set order, dictionary order, filesystem order, worker scheduling, or concurrency
may affect identity.

## 6. Parameter-domain cardinality derivation

These counts are **derived**, not asserted.

```text
canonical translation-normalized |U|=3 tuples                 = 651
canonical translation-normalized |V|=4 tuples (pre sign-red.) = 9936
canonical V tuples fixed by negation                          = 496
canonical V tuples after V-sign reduction                     = 5216
ordered normalized (V,U) domain                               = 3,395,616
```

**|U| = 3.** Z_64 has no element of order 3, so every translation stabilizer is trivial and every orbit has
size 64:

```text
orbits = C(64,3) / 64 = 41664 / 64 = 651
```

**|V| = 4 (Burnside over translations).** A subset fixed by a translation of order `d` is a union of cosets of
that subgroup, requiring `d | 4`, so `d in {1,2,4}`:

```text
d=1 (t=0)          : C(64,4) = 635376        (1 element)
d=2 (t=32)         : C(32,2) = 496           (1 element)
d=4 (t in {16,48}) : C(16,1) = 16 each       (2 elements)
orbits = (635376 + 496 + 32) / 64 = 9936
```

**Orbits fixed by negation (dihedral derivation).** There are 64 reflections acting on `Z_64`:

```text
32 vertex-axis reflections:
  2 fixed points and 31 transposed pairs
  fixed weight-4 subsets =
      C(31,2)          [choose two transposed pairs]
    + C(31,1)          [choose both fixed points and one pair]
    = 465 + 31
    = 496

32 edge-axis reflections:
  0 fixed points and 32 transposed pairs
  fixed weight-4 subsets =
      C(32,2)
    = 496
```

Therefore:

```text
sum of reflection-fixed weight-4 subsets = 64 * 496
translation orbits fixed by negation     = (64 * 496) / 64 = 496
sign-reduced translation orbits          = (9936 + 496) / 2 = 5216
```

**Domain.** `5216 * 651 = 3,395,616` ordered normalized `(V,U)` tuples.

**Count-regression requirement.** The implementation must include deterministic tests asserting all five
numbers, computed from the frozen normalization rules, as an independent computational cross-check of the
derivations above — not hard-coded as unexplained constants.

## 7. Candidate construction, orientation, and exact deduplication

```text
raw_A = sorted unique values of (u + v) mod 64
raw_B = sorted unique values of (u - v) mod 64
```

Validation before emission:

```text
len(raw_A) == 12 and len(raw_B) == 12
every value is a strict integer (bool is NOT an integer)
every value lies in 0..63
each support is strictly ascending and unique
```

**Orientation** follows the governing raw-support naming rule: the lexicographically smaller raw support is
emitted as `raw_support_A`, the other as `raw_support_B`. No transform (affine, complement, reflection,
translation, canonical representative) is applied to either support.

**Exact deduplication only.**

```text
exact_raw_pair_key = (raw_support_A, raw_support_B)     # oriented, post-naming
```

A record is skipped only when this oriented raw pair has already been emitted in this run. The generator must
**not** use the verifier's complement-inclusive `member_G_equivalence_key` or `canonical_pair_key` for
suppression.

**No other suppression exists.** Every direct, exact-nonduplicate candidate encountered in frozen parameter
order is emitted until a global termination condition occurs (§9). No eligible candidate may be silently
suppressed.

Trust boundary:

```text
generator exact deduplication : removes byte-identical oriented raw pairs only
verifier / freezer            : independently recompute canonical G-equivalence keys,
                                every pair predicate, and every family predicate
```

No generator diagnostic, counter, or key is authoritative for any predicate.

## 8. Candidate-stream contract

The generator emits exactly the already-accepted canonical envelope, **unchanged**:

```text
candidate_stream_payload = {
  "schema_name": "brainvision_descriptor_blind_candidate_stream",
  "schema_version": "0.1",
  "verification_mode": "PRIMARY_CANDIDATE_N64",
  "N": 64,
  "generator_identity_hash": <64 lowercase hex>,
  "generator_configuration_hash": <64 lowercase hex>,
  "budget_identity_hash": <64 lowercase hex>,
  "records": [...],
  "candidate_count": <strict int>,
  "terminal_status": <one of the four accepted statuses>
}

candidate_stream_envelope = {
  "candidate_stream": candidate_stream_payload,
  "candidate_stream_sha256": SHA256(canonical_json_bytes(candidate_stream_payload))
}
```

Each record:

```text
raw_support_A ; raw_support_B ; candidate_generation_index ; generator_diagnostics (optional)
```

Rules:

```text
candidate_generation_index numbers EMITTED records only
indices begin at zero, are monotone and gap-free
candidate_count == len(records)
records array order is authoritative
one canonical JSON document only ; no JSONL ; no implicit framing
canonical JSON and SHA-256 discipline exactly matches witness_canonical_json_v0_1.py
```

Permitted structural diagnostics (hashed, untrusted, predicate-inert):

```text
parameter_tuple_index ; U ; V ; sum_directness_count ; difference_directness_count ;
exact_duplicate_count_before_emission
```

Canonical output must contain **no** timestamps, wall-clock durations, absolute or temporary paths, process IDs,
usernames, hostnames, memory addresses, or unordered environment data.

## 9. Structural budget

Budgets use deterministic counters only. Wall-clock time and memory are noncanonical diagnostics and can never
terminate enumeration.

**Primary profile (frozen):**

```text
profile_name                     = PRIMARY_V0_1
normalized_parameter_domain_size = 3,395,616
max_parameter_tuples_examined    = 3,395,616
max_candidate_records_emitted    = 20,000
```

**Test profile (frozen):**

```text
profile_name                     = TEST_TINY_V0_1
normalized_parameter_domain_size = 3,395,616
max_parameter_tuples_examined    = 64
max_candidate_records_emitted    = 4
```

`normalized_parameter_domain_size` describes the underlying frozen primary domain and therefore remains
`3,395,616` for both profiles. The tiny profile limits traversal; it does **not** define a different
mathematical domain.

**Diagnostics only — never termination caps:**

```text
direct_tuples_found
exact_duplicate_candidates_skipped
colliding_parameter_tuples_rejected
```

`max_direct_tuples_found` and `max_exact_duplicate_skips` are deliberately **not** retained: they do not
independently control artifact size or domain traversal and would introduce unnecessary termination paths.

**Terminal logic (frozen).** After fully processing the current parameter tuple:

```text
1. if no unexamined parameter tuple remains in the normalized domain:
     terminal_status = stream_completed
     termination_reason = DOMAIN_EXHAUSTED

2. else if candidate_records_emitted == max_candidate_records_emitted:
     terminal_status = budget_exhausted
     termination_reason = MAX_CANDIDATE_RECORDS_EMITTED

3. else if parameter_tuples_examined == max_parameter_tuples_examined:
     terminal_status = budget_exhausted
     termination_reason = MAX_PARAMETER_TUPLES_EXAMINED

4. otherwise:
     continue
```

Because the primary profile sets `max_parameter_tuples_examined` equal to the complete domain size, step 3 is
unreachable under `PRIMARY_V0_1`: reaching that value coincides with domain exhaustion and yields
`stream_completed`. If the twenty-thousandth record is emitted on the final tuple, `stream_completed` wins
because no unexamined tuple remains. Under `TEST_TINY_V0_1`, after 64 tuples have been processed while the full
primary domain remains unexamined, `terminal_status = budget_exhausted` with
`termination_reason = MAX_PARAMETER_TUPLES_EXAMINED`.

```text
a completed stream contains every direct, exact-nonduplicate candidate in the frozen domain
a budget-exhausted stream contains the exact deterministic prefix encountered before the ceiling
```

**Rationale.** A record serializes to roughly 320–360 canonical bytes with diagnostics, so a 20,000-record
ceiling bounds the artifact near ~7 MB — a serious first bounded attempt without an unmanageable canonical JSON.
No feasibility claim is made.

The budget identity hashes a complete canonical payload containing every value above and the termination
precedence list.

## 10. Terminal and partial-stream semantics

```text
stream_completed:
  the complete frozen normalized parameter domain was enumerated

budget_exhausted:
  a frozen structural termination condition was reached before full-domain completion

route_incomplete:
  configuration, source identity, internal consistency, or route precondition failure
  prevented valid completion

dependency_unavailable:
  retained for schema compatibility but unreachable in the stdlib-only route
```

Partial-stream rules:

```text
budget_exhausted:
  preserve all deterministically emitted records
  the partial stream remains valid input to the verifier/freezer
  it may freeze a K=3 family if the independent freezer accepts one

route_incomplete:
  records = [] ; candidate_count = 0

dependency_unavailable:
  records = [] ; candidate_count = 0
```

The zero-record rule prevents an internally failed generator run from supplying a freezeable partial family.

A fully completed stream that yields fewer than three freezer-accepted pairs means only `FAMILY_NOT_FREEZABLE`
within the selected direct-sum domain. It never establishes nonexistence of valid N=64 witness families outside
that domain.

## 11. Exact payload schemas

All payloads use the accepted nonrecursive payload/envelope pattern. Hash coverage is always
`SHA256(canonical_json_bytes(payload))` over canonical bytes **without** a trailing newline. Unknown-key policy
for every payload below: **unknown keys are rejected**; there are no optional keys unless stated.

**generator_identity_payload / envelope**

```text
schema_name    = "brainvision_generator_identity"   (str)
schema_version = "0.1"                              (str)
generator_name           (str)
generator_version        (str)
route_identity           (str)   = "ALGEBRAIC_DIRECT_SUM_Z64"
generator_source_path    (str)   repository-relative, forward-slash
generator_source_sha256  (str)   64 lowercase hex, raw file bytes
serializer_source_path   (str)   repository-relative, forward-slash
serializer_source_sha256 (str)   64 lowercase hex, raw file bytes
envelope name = "generator_identity"
```

The candidate stream's `generator_identity_hash` is exactly this payload's hash, so source identity is bound
into generator identity rather than carried as disconnected metadata.

**generator_configuration_payload / envelope**

```text
schema_name    = "brainvision_generator_configuration" ; schema_version = "0.1"
N (int 64) ; u_size (int 3) ; v_size (int 4) ; candidate_weight (int 12)
verification_mode (str "PRIMARY_CANDIDATE_N64")
parameter_order_identity (str "V_LEXICOGRAPHIC_OUTER_U_LEXICOGRAPHIC_INNER")
translation_normalization (str "TRANSLATION_NORMAL_FORM")
v_sign_normalization (str "V_LEQ_LEX_TNF_NEG_V")
u_v_role_separation (bool True)
unit_affine_normalization (bool False)
generator_side_g_orbit_suppression (bool False)
complement_suppression (bool False)
deduplication_policy (str "EXACT_ORIENTED_RAW_PAIR_ONLY")
orientation_rule (str "LEXICOGRAPHICALLY_SMALLER_RAW_SUPPORT_IS_A")
diagnostics_policy (str "HASHED_UNTRUSTED_PREDICATE_INERT")
worker_count (int 1) ; randomness_enabled (bool False) ; random_seed (int 0)
serializer_name (str) ; serializer_version (str)
envelope name = "generator_configuration"
```

**structural_budget_payload / envelope**

```text
schema_name    = "brainvision_generator_structural_budget" ; schema_version = "0.1"
profile_name (str, one of "PRIMARY_V0_1" | "TEST_TINY_V0_1")
normalized_parameter_domain_size (int)
max_parameter_tuples_examined (int)
max_candidate_records_emitted (int)
termination_precedence (list[str]) =
  ["DOMAIN_EXHAUSTED","MAX_CANDIDATE_RECORDS_EMITTED","MAX_PARAMETER_TUPLES_EXAMINED"]
envelope name = "structural_budget"
```

**source_identity_payload / envelope**

```text
schema_name    = "brainvision_generator_source_identity" ; schema_version = "0.1"
generator_source_path (str) ; generator_source_sha256 (str, 64 lowercase hex)
serializer_source_path (str) ; serializer_source_sha256 (str, 64 lowercase hex)
envelope name = "source_identity"
```

**generator_run_result_payload / envelope**

```text
schema_name    = "brainvision_generator_run_result" ; schema_version = "0.1"
provisional (bool, always True)
candidate_stream_envelope (object | null)
terminal_status (str) ; termination_reason (str)
structural_counters (object) with exact keys:
    parameter_tuples_examined ; colliding_parameter_tuples_rejected ;
    direct_tuples_found ; exact_duplicate_candidates_skipped ; candidate_records_emitted
    (all strict int)
failure_record (object | null)
envelope name = "generator_run_result"
```

### 11.1 Failed provisional-run artifact behaviour (frozen)

**Hash satisfiability precondition (frozen).** An accepted-schema candidate stream requires three valid
64-lowercase-hex identity fields, so a stream may not be emitted at all when the failure is precisely what
prevents one of those hashes from existing:

```text
A zero-record accepted-schema candidate_stream_envelope may be emitted for
route_incomplete or dependency_unavailable only after all three stream-required
hashes have been honestly established:

  generator_identity_hash
  generator_configuration_hash
  budget_identity_hash

If the failure occurs before any one of those hashes exists as the SHA-256 of
its valid canonical payload, the generator_run_result_payload MUST use:

  candidate_stream_envelope = null
  terminal_status = route_incomplete
  termination_reason = failure_record.failure_code
  failure_record = populated

This applies, at minimum, to HASH_IDENTITY_FAILURE and to
GENERATOR_CONFIGURATION_INVALID cases that prevent generator identity,
generator configuration, or structural budget payload construction.

No sentinel hash, all-zero hash, hash of an invalid payload, placeholder
envelope, or fabricated identity/configuration/budget hash is permitted.

If all three hashes are available and the candidate-stream payload itself can
be canonically serialized, then a serializable invalid execution may emit the
valid zero-record accepted-schema stream described below.
```

When that precondition holds, for an invalid execution that can still be canonically serialized,
`generate_candidate_stream()` returns a **valid accepted-schema zero-record stream**, not a null stream:

```text
candidate_stream_envelope =
  valid accepted-schema candidate-stream envelope with:
    records = []
    candidate_count = 0
    terminal_status = route_incomplete

generator_run_result_payload:
  provisional      = True
  terminal_status  = route_incomplete
  failure_record   = populated
```

For `dependency_unavailable`, use the same zero-record candidate-stream form with:

```text
terminal_status = dependency_unavailable
```

For `dependency_unavailable`, a zero-record accepted-schema stream is permitted only when all three mandatory
hashes already exist honestly; otherwise the null-stream rule above applies.

Although that path is required for schema compatibility, reaching it under the stdlib-only route also records:

```text
GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE
```

Only when candidate-stream serialization itself cannot be completed may:

```text
candidate_stream_envelope       = null
failure_record.failure_code     = SERIALIZATION_FAILURE
```

Summary of the three frozen provisional-run outcomes:

```text
identity/configuration/budget hashes available + serializable route failure:
  valid accepted-schema zero-record candidate_stream_envelope

required hash unavailable:
  candidate_stream_envelope = null

candidate-stream serialization failure:
  candidate_stream_envelope = null
  failure_record.failure_code = SERIALIZATION_FAILURE
```

The outer minimal failure result must still be serialized when possible.

**generator_replay_result_payload / envelope** — see §13.

The candidate-stream schema itself remains completely unchanged.

## 12. Public module API

```text
generator_identity_payload(generator_source_path, serializer_source_path) -> dict

  Validates both paths and computes both raw-source SHA-256 identities.

  On success:
    returns the exact generator_identity_payload.

  On failure:
    raises a narrowly scoped internal GeneratorIdentityError carrying
    HASH_IDENTITY_FAILURE or GENERATOR_CONFIGURATION_INVALID.

  This exception is never allowed to escape generate_candidate_stream() or
  generate_candidate_stream_with_replay(); those public run operations catch it
  and convert it into the frozen failure-record and route_incomplete semantics.

generator_configuration_payload() -> dict
    returns the frozen §11 configuration payload; takes no arguments

structural_budget_payload(profile_name) -> dict
    profile_name in {"PRIMARY_V0_1","TEST_TINY_V0_1"}; an unknown name raises a narrowly scoped
    internal error carrying GENERATOR_CONFIGURATION_INVALID

generate_candidate_stream(profile_name, generator_source_path=None, serializer_source_path=None)
    -> generator_run_result_envelope
    PROVISIONAL ONLY. Never authoritative. Emits a canonical failure result per §11.1 and leaks no
    uncaught internal error.

generate_candidate_stream_with_replay(profile_name, generator_source_path=None,
                                      serializer_source_path=None)
    -> generator_replay_result_envelope
    The ONLY operation that may mark generator output authoritative for downstream freezing.
    Emits a canonical failure result per §13 and leaks no uncaught internal error.
```

General helper rule:

```text
low-level deterministic helpers may raise only narrowly scoped internal errors
public run and replay operations emit canonical failure results and leak no uncaught internal error
```

These internal error classes are implementation detail only. They are **not** added to the candidate-stream
schema, to any canonical payload schema, or to any emitted canonical field. No CLI is added. Source paths
default to the module's own resolved locations.

## 13. Replay artifact (stream unchanged)

The accepted freezer consumes the existing `candidate_stream_envelope`, so **no replay field is added to the
stream**. Replay evidence lives in a separate artifact:

```text
generator_replay_result_payload = {
  schema_name,                      = "brainvision_generator_replay_result"
  schema_version,                   = "0.1"
  authoritative_operation,          (bool)
  downstream_freeze_eligible,       (bool)
  byte_identical,                   (bool)
  run1_candidate_stream_sha256,     (str | null)
  run2_candidate_stream_sha256,     (str | null)
  generator_identity_envelope,      (object | null)
  generator_configuration_envelope, (object | null)
  structural_budget_envelope,       (object | null)
  source_identity_envelope,         (object | null)
  run1_structural_counters,
  run2_structural_counters,
  candidate_stream_envelope,        (object | null)
  failure_record                    (object | null)
}
envelope name = "generator_replay_result"
```

```text
An identity/configuration/budget/source envelope is null only when the
corresponding valid payload could not be honestly constructed.

No placeholder payload, fabricated hash, sentinel hash, or structurally invalid
envelope may be inserted to avoid nullability.
```

Frozen outcome rules:

```text
successful identical replay of stream_completed or budget_exhausted:
  authoritative_operation    = True
  downstream_freeze_eligible = True
  candidate_stream_envelope  = exact unchanged accepted stream envelope

identical replay of a valid zero-record route_incomplete or
dependency_unavailable stream:
  authoritative_operation    = True
  downstream_freeze_eligible = False
  candidate_stream_envelope  = exact identical zero-record stream
  failure_record             = retained

pre-hash identity/configuration/budget failure:
  authoritative_operation    = False
  downstream_freeze_eligible = False
  candidate_stream_envelope  = null
  unavailable identity/configuration/budget/source envelopes = null
  failure_record             = retained

replay mismatch:
  authoritative_operation    = False
  downstream_freeze_eligible = False
  candidate_stream_envelope  = null
  failure_record.failure_code = REPLAY_MISMATCH

invalid replay execution or replay-result serialization failure:
  authoritative_operation    = False
  downstream_freeze_eligible = False
  candidate_stream_envelope  = null
  failure_record             = populated
```

`authoritative_operation = True` means only that the two-pass replay operation completed deterministically. It
does **not** mean the resulting stream is eligible for freezing; that is represented exclusively by
`downstream_freeze_eligible`. A pre-hash failure cannot qualify as a successfully completed authoritative
replay because the frozen replay identities could not be established.

The replay operation runs the generator twice in the same environment with identical configuration and budget
payload bytes, requires byte-identical candidate-stream envelope output, compares all hashes and structural
counters, and **never** invokes the verifier, freezer, ΨTRS, descriptors, or the N64 evaluator. The freezer
remains unchanged and consumes only the extracted exact `candidate_stream_envelope`; the replay artifact is
operator/audit evidence establishing which stream is authorized for downstream freezing.

## 14. Forbidden dependencies and independence

The generator is standard-library-only, apart from importing the zero-witness-mathematics canonical JSON
utility. Direct inspection confirms `witness_canonical_json_v0_1.py` imports only `hashlib`, `json`, `typing`,
`__future__` and contains no witness mathematics, so this single import is consistent with the accepted
dependency boundary.

Forbidden imports or dynamic loading:

```text
psi_trs ; psi_trs_k0 ; run_n64_falsifier_v0_1 ;
witness_family_verifier_v0_1 ; witness_family_freeze_v0_1 ;
operational harness modules ; paired prerecorded analysis ; descriptor modules ; SAG logic ;
torment_service ; production kernel modules ; SRG or quantum-project code ;
third-party SAT/SMT or numerical libraries
```

Required checks:

```text
AST forbidden-import tests
transitive project-local import-graph checks
source-path ownership checks (resolved path inside the repository and research/brainvision,
  equal to its expected module path; symlink and traversal escapes rejected)
no production-kernel path access
no environment authorization gate that silently changes mathematics
no network access
no subprocess solver invocation
```

## 15. Failure codes

Aligned with accepted infrastructure where semantics truly match:

```text
GENERATOR_CONFIGURATION_INVALID
HASH_IDENTITY_FAILURE
SERIALIZATION_FAILURE
FORBIDDEN_IMPORT_DETECTED
REPLAY_MISMATCH
```

Route-specific codes:

```text
GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT   sum-form and difference-form directness disagree
GENERATOR_SUPPORT_NORMALIZATION_FAILURE          constructed support fails weight/range/ascending/strict-int
GENERATOR_INDEX_ORDER_FAILURE                    indices not zero-based/monotone/gap-free, or
                                                 candidate_count != len(records)
GENERATOR_COUNTER_INCONSISTENCY                  structural counters disagree with emitted records
GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE      dependency_unavailable reached in a stdlib-only route
```

Category separation (frozen):

```text
invalid execution            : the codes above (stream is not authoritative)
ordinary parameter rejection : a non-direct (colliding) tuple  -> normal enumeration outcome
exact duplicate skip         : oriented raw pair already emitted -> normal enumeration outcome
budget termination           : a frozen structural condition reached -> budget_exhausted, records retained
successful completion        : full domain enumerated -> stream_completed
```

A non-direct tuple and an exact duplicate are **never** execution failures.

## 16. Required tests and fixtures

```text
translation-normal-form correctness
V-sign normalization correctness
U/V role separation (no U<->V symmetry)
V-major lexicographic parameter order (parameter_order_identity honoured)
parameter-domain count regressions (651 / 9936 / 496 / 5216 / 3,395,616)
strict int-not-bool validation
sum/difference directness equivalence, and the consistency-guard failure path
positive and colliding parameter fixtures (below)
weight-12 output construction
raw A/B lexicographic orientation
exact raw-pair deduplication (and that nothing else is suppressed)
candidate-generation indices (zero-based, monotone, gap-free)
candidate-count consistency
canonical stream hash ; identity hash ; configuration hash ; budget hash ; source hash
both budget profiles carry normalized_parameter_domain_size = 3,395,616
stream_completed ; budget_exhausted via MAX_CANDIDATE_RECORDS_EMITTED ;
  budget_exhausted via MAX_PARAMETER_TUPLES_EXAMINED (test profile) ;
  zero-record route_incomplete ; zero-record dependency_unavailable path
terminal precedence (final-tuple emission yields stream_completed, not budget_exhausted)
identity/configuration/budget-available route_incomplete returns a valid
  zero-record accepted-schema candidate_stream_envelope
identity/configuration/budget-available dependency_unavailable returns a valid
  zero-record accepted-schema candidate_stream_envelope and records
  GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE
HASH_IDENTITY_FAILURE returns candidate_stream_envelope = null when a mandatory
  stream identity hash cannot be honestly established
pre-hash GENERATOR_CONFIGURATION_INVALID returns
  candidate_stream_envelope = null
candidate-stream serialization failure returns
  candidate_stream_envelope = null
no sentinel, all-zero, placeholder, fabricated, or invalid-payload hash may
  populate a required candidate-stream identity field
replay artifact identity/configuration/budget/source envelope nullability
  matches actual payload availability
pre-hash replay failure is not authoritative and is not downstream-freeze
  eligible
internal helper errors never escape the public run and replay operations
replay case 1 : identical replay of stream_completed/budget_exhausted -> authoritative, freeze-eligible
replay case 2 : identical replay of route_incomplete/dependency_unavailable ->
                authoritative, NOT freeze-eligible, zero-record stream retained, failure_record retained
replay case 3 : replay mismatch -> not authoritative, not eligible, null stream, REPLAY_MISMATCH
replay case 4 : invalid replay execution or replay-result serialization failure ->
                not authoritative, not eligible, null stream, populated failure_record
forbidden imports ; transitive independence ;
  absence of verifier/freezer/PsiTRS/kernel imports
diagnostics hashed but predicate-inert
small-budget deterministic prefix stability
```

**Frozen positive construction fixture (hand-checkable):**

```text
U = (0,1,2)
V = (0,3,6,9)

translation_normal_form(U)  = U
translation_normal_form(V)  = V
translation_normal_form(-V) = V        (V is sign-normalized)

U+V = (0,1,2,3,4,5,6,7,8,9,10,11)
U-V = (0,1,2,55,56,57,58,59,60,61,62,63)

both contain exactly 12 distinct residues

raw_support_A = (0,1,2,3,4,5,6,7,8,9,10,11)
raw_support_B = (0,1,2,55,56,57,58,59,60,61,62,63)
```

This fixture is structurally separated from the previous weight-9 evidence solely by its frozen weight-12
construction. The old fixture must not be imported, inspected, compared against, or encoded.

**Frozen colliding fixture (hand-checkable):**

```text
U = (0,1,2)
V = (0,1,3,5)

sum collision        : 0+1 = 1+0 = 1
difference collision : 0-0 = 1-1 = 0
```

This is an ordinary rejected parameter tuple, not an execution failure.

## 17. Performance diagnostics

Optional, noncanonical, human-facing only:

```text
parameter tuples examined ; direct tuples found ; records emitted ; exact duplicates skipped ;
rejection counts by structural reason ; peak record count ; wall-clock duration
```

They must never influence candidate ordering, budget decisions, canonical bytes, hashes, terminal status,
verifier decisions, freezer decisions, or scientific interpretation, and must never enter canonical output.

## 18. Known limitations and deferred items

```text
Coverage: a budget_exhausted run contains the exact deterministic prefix of the frozen order.
  A negative outcome is bounded by that prefix, the weight policy, and the frozen budget.
Class diversity: three distinct autocorrelation classes are not guaranteed by the construction and are
  decided only by the independent freezer. This specification makes no feasibility claim.
Deferred to a later specification (not decided here): any unit-affine or G-orbit generator-side
  normalization; any stride or stratified emission policy; any raised budget profile; any second
  parameter shape beyond |U|=3, |V|=4.
```

## 19. Authorization conclusion

```text
DOCUMENTATION_AUTHORIZED = True
GENERATOR_ROUTE_SELECTED = ALGEBRAIC_DIRECT_SUM_Z64
GENERATOR_IMPLEMENTATION_AUTHORIZED = False
N64_WITNESS_GENERATION_AUTHORIZED = False
PsiTRS_EVALUATION_AUTHORIZED = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False
```

```text
no generator was implemented
no parameter enumeration was run
no candidate stream was produced
no witness family was frozen
no PsiTRS evaluation was performed
no production-kernel file was modified
```

*End — TORMENT Brainvision Algebraic Direct-Sum N=64 Candidate Generator Implementation Specification v0.1.
Docs-only, non-authorizing, non-implementing. The accepted witness-family, verifier/freeze, and route-decision
documents are unamended and remain authoritative; `psi_trs.py`, `run_n64_falsifier_v0_1.py`, and the production
TORMENT memory kernel are immutable. No `§0` pointer; no registry or orientation update; no tags.*
