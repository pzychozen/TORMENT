# TORMENT Brainvision Independent Higher-Order Witness Verifier and Freeze Infrastructure Implementation Specification v0.1

## 0. Status / authority

**DOCS-ONLY specification. Non-implementing.** This document governs only the independent verifier, canonical
serialization, certificate/manifest schemas, and family freeze/replay infrastructure for the higher-order
witness family. It authorizes no execution and drafts no generator mathematics.

```text
FORMAL_HOLD = active
Mode_0      = active

documentation_authorization            = True
verifier_implementation_authorization  = False
generator_implementation_authorization = False
witness_generation_authorization       = False
PsiTRS_evaluation_authorization         = False
scientific_inference_authorization      = False
```

Governing accepted document (authoritative for witness-family mathematics; not amended here):

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_DESCRIPTOR_BLIND_HIGHER_ORDER_WITNESS_FAMILY_IMPLEMENTATION_SPECIFICATION_v0.1.md
```

Immutable — never modified or imported for their witness mathematics:

```text
research/brainvision/psi_trs.py
research/brainvision/run_n64_falsifier_v0_1.py
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

## 1. Scope

This specification governs **only**:

```text
independent mathematical verifier
canonical JSON serialization
candidate and certificate schemas
accepted-family manifest schema
family freezer (deterministic descriptor-blind freeze selection)
same-environment deterministic replay
positive and negative regression fixtures
forbidden-import and independence tests
```

Explicitly excluded (not designed, specified, or authorized here):

```text
candidate generation mathematics ; SAT/SMT ; CP-SAT ; custom backtracking ; difference-multiset search ;
algebraic construction ; small-N feasibility pilots ; N=64 witness generation ; PsiTRS evaluation
```

The verifier consumes raw candidate supports supplied through the frozen external **candidate-stream envelope**
(§4, §16). It must not care how those candidates were generated, and it recomputes every certificate itself.

## 2. Proposed modules

```text
research/brainvision/witness_family_verifier_v0_1.py
  responsibility: independent integer-exact recomputation of every witness certificate from raw supports;
                  candidate/pair/family predicate evaluation; failure-code emission.
research/brainvision/witness_canonical_json_v0_1.py
  responsibility: canonical JSON serialization + SHA-256 only. Contains ZERO witness mathematics.
research/brainvision/witness_family_freeze_v0_1.py
  responsibility: consume the frozen candidate-stream envelope of raw records; invoke the verifier per record;
                  perform deterministic descriptor-blind freeze selection; assemble/validate the K=3 family
                  manifest; run same-environment replay; emit manifest or failure record. No generation.

tests/research/test_brainvision_witness_family_verifier_v0_1.py
tests/research/test_brainvision_witness_family_freeze_v0_1.py
```

Allowed dependency direction:

```text
freezer   -> verifier
freezer   -> serializer
verifier  -> serializer   (only because the serializer contains zero witness mathematics)
```

Forbidden dependency direction:

```text
verifier   -> any generator
serializer -> verifier
serializer -> any witness mathematics
verifier   -> psi_trs
verifier   -> N64 evaluator logic
freezer    -> PsiTRS or descriptors
```

## 3. Independent-verifier definition

"Independent" binds to these testable requirements:

```text
separate module from every generator
no generator imports
no shared witness-predicate helpers
no trust in generator summaries or certificates
all certificates recomputed from raw supports
equivalence and canonicalization independently re-derived
no importing mathematical predicates from the immutable N64 lane
N64 or balanced-complement fixture values may be copied BY VALUE only (never imported as logic)
```

Standard-library and serialization utilities may be shared only when they contain no witness mathematics.
Independence is enforced by AST forbidden-import tests plus a transitive import-graph test and a source-path
test (§15).

## 4. Candidate-stream envelope, verification modes, and input validation

### 4.1 Canonical candidate-stream envelope

The verifier/freezer consume **one canonical JSON document**, not a stream of independent records and not
JSONL. There are no implicit record boundaries.

```text
raw_candidate_record = {
  "raw_support_A": <ascending unique integer list>,
  "raw_support_B": <ascending unique integer list>,
  "candidate_generation_index": <integer>,
  "generator_diagnostics": <optional, untrusted, canonical finite JSON>
}

candidate_stream_payload = {
  "schema_name": "brainvision_descriptor_blind_candidate_stream",
  "schema_version": "0.1",
  "verification_mode": "REFERENCE_REGRESSION_N12" | "PRIMARY_CANDIDATE_N64",
  "N": 12 | 64,
  "generator_identity_hash": <64 lowercase hex>,
  "generator_configuration_hash": <64 lowercase hex>,
  "budget_identity_hash": <64 lowercase hex>,
  "records": [ raw_candidate_record, ... ],
  "candidate_count": <integer>,
  "terminal_status": "stream_completed" | "budget_exhausted" | "route_incomplete" | "dependency_unavailable"
}

candidate_stream_envelope = {
  "candidate_stream": candidate_stream_payload,
  "candidate_stream_sha256": SHA256(canonical_json_bytes(candidate_stream_payload))
}
```

Requirements:

```text
one canonical JSON document only ; no JSONL ; no alternative framing ; no implicit record boundaries
records array order is the authoritative candidate order
candidate_count == len(records)
generation_index starts at 0 ; monotone and gap-free ; records[i].candidate_generation_index == i
terminal_status is part of the hashed payload
replay operates on the exact bytes of candidate_stream_envelope (§13)
```

Optional `generator_diagnostics` inside a record: included in the canonical candidate-stream bytes and stream
hash; recorded verbatim; untrusted; ignored by every verifier and freeze predicate; must itself satisfy
canonical finite JSON requirements.

### 4.2 Verification modes and supported N

```text
REFERENCE_REGRESSION_N12:
  N must equal 12 ; used only for the frozen N=12 positive/negative regressions ;
  cannot produce or enter a primary family manifest.
PRIMARY_CANDIDATE_N64:
  N must equal 64 ; used for external candidate-stream verification and family freezing.
UNSUPPORTED_N:
  every other N, or any mismatch between mode and N.
```

`CANDIDATE_N_MODE_INVALID` is emitted for `UNSUPPORTED_N` and **precedes all mathematical candidate checks**.

### 4.3 Per-record validation

The verifier rejects (with the corresponding §14 code):

```text
duplicate support indices ; out-of-range indices ; non-integer indices ; non-binary reconstructed sequence ;
empty or malformed members ; A = B ; missing required fields ; unknown schema version ;
noncanonical serialization input where canonical input is required
```

A malformed stream envelope or a broken stream hash is **invalid execution** (`CANDIDATE_STREAM_INVALID` /
`CANDIDATE_STREAM_HASH_MISMATCH`), not a candidate rejection (§14). **Generator certificates or diagnostics
never substitute for verifier computation.**

## 5. Exact verifier algorithms (integer arithmetic only)

```text
binary sequence reconstruction: x[t] = 1 iff t in support; validate support subset of Z_N, no duplicates.
weight:                         w = |support|.
complete periodic autocorrelation (N entries):
                                r(k) = |{ t : t in S and (t+k) mod N in S }|, k in 0..N-1.
directed one-step table:        c_{ab} = |{ t : x[t]=a and x[(t+1) mod N]=b }|.
absolute transition multiset:   counts of |x[(t+1) mod N] - x[t]| over t (values 0,1).
complete labeled triple array (N x N):
                                T(k,l) = |{ t : t, (t+k) mod N, (t+l) mod N all in S }|.
primitive circular period:      primitive iff rotate(x,r) != x for all r in 1..N-1.
affine sequence action:         (u,a) maps support S to { (u*s + a) mod N : s in S }, u in U(N), a in Z_N.
symbol complement:              complement(S) = Z_N \ S.
group enumeration:              every element of C2 x (Z_N semidirect_product U(N)) (see §6).
member_G_equivalence_key:       lexicographically minimal support tuple over the full group orbit of the member.
canonical_pair_key:             ordered pair (min,max) of the two members' member_G_equivalence_keys (§5.3).
```

### 5.1 Lower-order pair equalities (explicit; emitted and checked)

```text
autocorrelation_equal   = member_certificate_A.autocorrelation   == member_certificate_B.autocorrelation
one_step_table_equal    = member_certificate_A.one_step_table     == member_certificate_B.one_step_table
transition_multiset_equal = member_certificate_A.transition_multiset == member_certificate_B.transition_multiset
```

All three must be `True` for `pair_valid`. The latter two are mathematically implied by autocorrelation
equality in the selected circular binary domain, but **they must still be emitted and independently checked.**

```text
autocorrelation_equal false  -> CANDIDATE_NOT_HOMOMETRIC
one_step_table_equal or transition_multiset_equal false WHILE autocorrelation_equal true
                             -> VERIFIER_INTERNAL_DISAGREEMENT   (not an ordinary candidate rejection)
```

### 5.2 Complement predicates (direct vs affine-plus-complement, separated)

```text
direct_complement_image =
  raw_support_B == complement(raw_support_A)     (exact raw-support complement; no affine)

affine_plus_complement_inequivalent =
  no affine map (u,a) sends A to complement(B)   (broader predicate; retained)
```

`CANDIDATE_COMPLEMENT_IMAGE` means **only** the direct raw-support complement case.
`CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT` covers **every** affine-plus-complement relationship, including
the direct case. Failure ordering:

```text
CANDIDATE_COMPLEMENT_IMAGE  then  CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT
```

When the direct-complement condition holds, both codes may appear in `ordered_failure_codes`, but the direct
code is primary. The certificate carries `direct_complement_image` and `affine_plus_complement_inequivalent`
as two distinctly-named predicates; no single mathematical predicate is disguised as two independent checks.

### 5.3 Triple-array G-nonalignment (single accepted formulation, preserved)

```text
Translation is omitted from triple-array alignment because the complete cyclic triple array is
translation-invariant.

for c in {identity, complement} and u in U(N):
    X = A            if c = identity
    X = complement(A) if c = complement
    compute T_X
    compare T_B(k,l) with T_X( (u^-1 * k) mod N , (u^-1 * l) mod N )  for all (k,l)

Do not additionally transform the sequence by u in the same calculation.
No pair (c,u) may produce complete equality; any complete match => triple-G-alignable.
```

The production predicate uses **exactly one** formulation. The equivalent transform-and-recompute route is
exercised only as a regression cross-check test against the production one; the two are never both applied
inside the production predicate.

### 5.4 Lexicographic ordering (cross-language exact)

For every support tuple and canonical-key comparison:

```text
compare integers left to right ; the first differing integer determines order ;
if all shared positions are equal and one tuple is a strict prefix, the shorter tuple is smaller.
```

Raw supports are ascending unique integer tuples before comparison. This rule governs member
equivalence-key minimization, canonical pair-key member ordering, and raw A/B naming. It does **not** reorder
accepted pairs in the family.

## 6. Orbit handling

```text
The verifier enumerates 2 * N * |U(N)| group elements (N=64 -> 4096 ; N=12 -> 96).
The group-element count is NOT necessarily the de-duplicated orbit size; a member with a nontrivial stabilizer
has a smaller distinct orbit. Equivalence is decided by comparing over the enumerated elements.
Orbit members are STREAMED where practical; full transformed triple arrays must not all be retained
simultaneously (hold one N x N array at a time).
```

Deterministic transform ordering (fixed, total; no set/dict iteration order may define canonical identity):

```text
complement flag order : identity (0) then complement (1)
unit order            : units of Z_N in ascending integer order
translation order     : a in 0,1,...,N-1 ascending
```

## 7. N=12 positive fixture (frozen by value)

```text
N = 12
A = {0,1,3,5,6}
B = {0,1,2,4,7}
```

Expected exact certificates (the verifier must reproduce these from the raw supports):

```text
autocorrelation              = (5,2,2,2,1,2,2,2,1,2,2,2)
one-step table               = c00=4 ; c01=3 ; c10=3 ; c11=2
absolute transition multiset = 0 -> 6 ; 1 -> 6
triple-array disagreement count = 48 of 144
primitive period             = 12 for both members
affine equivalent            = False
affine-plus-complement equivalent = False
direct_complement_image      = False
triple-G-alignable           = False
```

## 8. Negative regression fixtures

Independent rejection fixtures are required for:

```text
non-homometric pair ; identical pair ; translation-equivalent pair ; reflection-equivalent pair ;
unit-affine-equivalent pair ; complement-equivalent pair ; balanced-complement homometric pair ;
non-primitive member ; malformed raw support ; wrong sequence length ; reused family member ;
duplicate autocorrelation class at family level
```

For triple-array alignment, **no** unproven tiny "G-inequivalent-but-triple-alignable" fixture is required.
Instead require two separate test classes:

```text
triple-alignable negative:  may also be sequence-G-equivalent ; proves the detector RETURNS alignment
triple-nonaligned positive: the accepted N=12 witness ; proves the detector RETURNS nonalignment
```

Recorded explicitly: **no claim is made that a tiny G-inequivalent-yet-triple-alignable regression fixture
exists.**

## 9. Candidate and certificate schemas (payload/envelope; nonrecursive hashing)

Every hashed object is split into a `_payload` (all fields except its own hash) and an `_envelope` carrying an
**external** hash of the payload bytes:

```text
<object>_envelope = { "<object>": <object>_payload, "<object>_sha256": SHA256(canonical_json_bytes(<object>_payload)) }
```

No object's hash field is ever computed over itself. A `hashes` map may contain hashes of separately defined
payloads, but must not contain the hash of the outer object that contains the map.

```text
raw_candidate_record        : §4.1 (raw supports + generation index + optional untrusted diagnostics)
member_certificate          : raw_support, weight, autocorrelation[N], one_step_table, transition_multiset,
                              primitive_period, member_G_equivalence_key
pair_verifier_certificate_payload:
                              member_certificate_A, member_certificate_B, canonical_pair_key,
                              autocorrelation_equal, one_step_table_equal, transition_multiset_equal,
                              triple_disagreement_count, affine_inequivalent,
                              affine_plus_complement_inequivalent, direct_complement_image,
                              triple_G_nonaligned, pair_valid, ordered_failure_codes
family_verifier_certificate_payload:
                              pair_certificates[3], mutual_G_inequivalent, members_non_reused,
                              distinct_autocorrelation_classes, family_valid, ordered_failure_codes
accepted_pair_record        : pair_verifier_certificate_envelope, accepted_order_index, raw_AB_naming
family_manifest_payload      : schema, version, N, K, accepted_pair_records[3], autocorrelation_classes[3],
                              verifier_identity, verifier_configuration_envelope, freeze_configuration_envelope,
                              source_identities, generator_reference_hashes
verifier_configuration_payload : module identity, algorithm identities, triple-formulation choice, tool versions
freeze_configuration_payload : K, ordering policy, replay policy, tool versions
replay_record_payload        : §13 decision ledger and byte/hash agreements
failure_record               : failure_code, stage, ordered_failure_codes, partial_diagnostics
```

These preserve **separately** and never conflate: raw evaluation supports ; member G-equivalence keys ;
canonical pair key ; raw autocorrelation vectors ; raw triple disagreement count ; all Boolean predicate
results ; failure codes ; source identities and hashes. Raw supports are **never** replaced by canonical
transformed representatives.

## 10. Canonical serialization

Canonical JSON, identical in discipline to the accepted operational / N64 lineage:

```text
UTF-8 ; ensure_ascii = True ; sort_keys = True ; separators = (",", ":") ; allow_nan = False
trailing newline policy = NO trailing newline (canonical bytes end at the final '}')
integer-only mathematical certificates (no floats in any witness certificate)
```

Representation rules:

```text
tuples / supports : JSON arrays of integers, ascending where the value is a set (support tuples sorted ascending)
maps (one_step_table, transition_multiset): objects with string keys, sort_keys applied
booleans          : JSON true / false
integers          : raw unrounded integer values (no scientific notation, no floats)
```

Canonical witness outputs must **exclude** nondeterministic metadata (see §11/§13): timestamps ; wall-clock
durations ; absolute paths ; temporary paths ; process IDs ; hostnames ; usernames ; machine identifiers ;
unordered environment dumps ; filesystem enumeration order ; memory addresses ; random object
representations. Repository-relative paths may be recorded only as fixed normalized forward-slash strings. Tool
versions may be recorded only as explicitly queried stable strings inside frozen configuration payloads.
Performance diagnostics may be emitted separately as noncanonical human diagnostics and must not affect the
candidate-stream hash, verifier decisions, certificate hashes, family manifest, or replay verdict. The
serializer contains **no** witness mathematics.

## 11. Hashing and identities

All object hashes follow the §9 payload/envelope pattern (hash covers the canonical payload bytes, never its
own field). Coverage rule: every SHA-256 covers the exact canonical bytes as emitted, **without** a trailing
newline (§10).

Source identities are raw-file-byte hashes:

```text
verifier_source_sha256   = SHA256(raw bytes of research/brainvision/witness_family_verifier_v0_1.py)
serializer_source_sha256 = SHA256(raw bytes of research/brainvision/witness_canonical_json_v0_1.py)
freeze_source_sha256     = SHA256(raw bytes of research/brainvision/witness_family_freeze_v0_1.py)
```

```text
raw file bytes exactly as present in the authoritative checkout ; no newline normalization ;
no path bytes included in the source hash ; repository-relative source path recorded separately ;
git commit identity recorded separately.
```

Configuration identities: `SHA256(canonical_json_bytes(configuration_payload))`.

Generator identity/configuration/budget hashes supplied by the external stream are **opaque references**:
exactly 64 lowercase hexadecimal characters; recorded verbatim; **not** independently authenticated by this
verifier/freezer.

`HASH_IDENTITY_FAILURE` may detect: missing hash ; wrong length ; non-lowercase-hex encoding ; mismatch
between a supplied payload and its supplied hash ; mismatch between a locally recomputed source/config payload
and its hash. **Limitation (stated):** it cannot prove the authenticity of an opaque external generator hash
when no corresponding payload is supplied.

## 12. Family-freeze contract

### 12.1 Deterministic descriptor-blind freeze selection (authorized)

The freezer performs deterministic descriptor-blind freeze selection from the frozen ordered candidate stream:

```text
For each raw candidate record in authoritative stream order:
  1. invoke the independent verifier on the raw record;
  2. record the complete verifier decision and ordered failure codes;
  3. reject invalid pair candidates;
  4. for a valid pair, evaluate incremental family predicates against already accepted pairs:
       - no raw member reuse
       - all member G-equivalence keys remain unique
       - autocorrelation class is new
  5. accept the first candidate satisfying all pair and incremental family predicates;
  6. stop accepting after K=3, preserving the remaining input stream identity and terminal status in the
     replay record.
```

The freezer may select **only** by: stream order ; verifier predicates ; incremental family predicates. It
must **never** select by: PsiTRS response ; descriptor behavior ; generation method ; candidate aesthetics ;
manual preference ; post hoc replacement. It must also never: reorder candidates based on response ; replace
failed candidates ; invoke a generator ; inspect PsiTRS ; consult descriptor outputs ; weaken family
requirements.

Authoritative accepted order = the verifier/freezer acceptance order inherited from candidate-stream order. It
is **not** canonical-pair-key sorting order.

For K=3, the freezable family requires: three valid pair certificates ; six unreused members ; all six
mutually G-inequivalent ; primitive period 64 for every member ; three distinct complete-autocorrelation
vectors ; all pair predicates true.

### 12.2 Certificate trust boundary

The freezer consumes the `candidate_stream_envelope` of `raw_candidate_record` objects and **invokes the
verifier itself** for every candidate. A supplied certificate, summary, `pair_valid=true`, or generator
diagnostic is **never trusted** and cannot enter the family manifest without recomputation. The freezer may
cache verifier results produced during the same run, but every accepted pair certificate must be produced by
the frozen verifier identity/configuration recorded in the manifest. If externally supplied verifier
certificates are ever accepted for replay convenience, the freezer must recompute them from raw supports,
compare complete canonical certificate bytes and hashes, and reject any mismatch as
`VERIFIER_INTERNAL_DISAGREEMENT`. The primary interface remains raw records plus internal verifier invocation.

## 13. Replay contract (complete deterministic decision ledger)

Two same-environment runs over the exact same frozen `candidate_stream_envelope` bytes and configuration.
Replay never invokes a generator; both runs consume identical frozen input bytes. Replay equality must
include:

```text
candidate_stream_envelope bytes ; candidate_stream_sha256 ; verification mode ; candidate count ;
terminal stream status ; generator identity/configuration hashes ; budget identity hash ;
verifier source/configuration identities ; serializer source/configuration identities ;
freeze source/configuration identities ; ordered per-candidate decision ledger ;
ordered verifier failure codes for every candidate ; incremental family-predicate decisions ;
accepted candidate indices ; accepted pair certificate bytes ; final family certificate bytes ;
family manifest payload and envelope bytes ; all output hashes ; failure record when no family freezes
```

```text
candidate_decision_ledger = one deterministic entry per input record, in original stream order.
```

A replay mismatch is detectable even when zero candidates are accepted, fewer than three pairs are accepted,
the stream ends by budget exhaustion, or the family is not freezable. Any divergence produces
`REPLAY_MISMATCH`, and **no family may be frozen.**

## 14. Failure codes

Two disjoint classes. **A rejected candidate is a valid verifier execution, not an error.**

Valid candidate/family rejection (engineering-valid):

```text
CANDIDATE_SCHEMA_INVALID
CANDIDATE_N_MODE_INVALID
CANDIDATE_SUPPORT_INVALID
CANDIDATE_NOT_HOMOMETRIC
CANDIDATE_MEMBER_NOT_PRIMITIVE
CANDIDATE_AFFINE_EQUIVALENT
CANDIDATE_COMPLEMENT_IMAGE
CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT
CANDIDATE_TRIPLE_G_ALIGNABLE
CANDIDATE_CERTIFICATE_INVALID
FAMILY_MEMBER_REUSED
FAMILY_MEMBER_G_EQUIVALENT
FAMILY_AUTOCORRELATION_CLASS_REUSED
FAMILY_PAIR_COUNT_INVALID
FAMILY_NOT_FREEZABLE
```

Invalid engineering execution:

```text
CANDIDATE_STREAM_INVALID
CANDIDATE_STREAM_HASH_MISMATCH
VERIFIER_REGRESSION_FAILURE
VERIFIER_CONFIGURATION_INVALID
VERIFIER_INTERNAL_DISAGREEMENT
SERIALIZATION_FAILURE
HASH_IDENTITY_FAILURE
REPLAY_MISMATCH
FORBIDDEN_IMPORT_DETECTED
```

Phased evaluation (replaces any "short-circuit while emitting all codes" wording):

```text
execution validation:
  checks run in frozen precedence order; all codes discovered before the first mandatory short-circuit are
  emitted; processing stops when continued computation would be unsafe or undefined.
candidate validation:
  runs only after execution and schema validity pass; all mathematically applicable candidate-rejection codes
  are emitted in frozen precedence order.
family validation:
  runs only for verifier-valid candidate pairs; all applicable incremental or final family-rejection codes are
  emitted in frozen precedence order.
```

Exact triggers:

```text
CANDIDATE_CERTIFICATE_INVALID: an internally assembled certificate is missing a required field, violates its
  own schema, or fails canonical serialization after the mathematical calculations completed successfully.
FAMILY_NOT_FREEZABLE: stream processing terminates without K=3 accepted pairs while no more specific
  invalid-execution code applies.
HASH_IDENTITY_FAILURE: a required hash is missing, malformed, or disagrees with the exact payload/source/config
  bytes it claims to identify.
VERIFIER_INTERNAL_DISAGREEMENT: two required independently derived calculations disagree; equivalent
  production/regression formulations disagree; an implied binary lower-order equality unexpectedly fails; or
  recomputed certificate bytes disagree with supplied replay bytes.
```

`CANDIDATE_SCHEMA_INVALID`, `CANDIDATE_N_MODE_INVALID`, and `CANDIDATE_SUPPORT_INVALID` are valid deterministic
**record** rejections when the stream envelope itself is structurally valid. A malformed stream envelope or a
broken stream hash is invalid **execution** (`CANDIDATE_STREAM_INVALID` / `CANDIDATE_STREAM_HASH_MISMATCH`).

Deterministic precedence (all applicable codes go to `ordered_failure_codes`; the primary `failure_code` is the
first that applies):

```text
1. execution-invalid (checked first, short-circuits when unsafe to continue):
     VERIFIER_CONFIGURATION_INVALID -> FORBIDDEN_IMPORT_DETECTED -> CANDIDATE_STREAM_INVALID ->
     CANDIDATE_STREAM_HASH_MISMATCH -> SERIALIZATION_FAILURE -> HASH_IDENTITY_FAILURE ->
     VERIFIER_INTERNAL_DISAGREEMENT -> VERIFIER_REGRESSION_FAILURE -> REPLAY_MISMATCH
2. candidate rejection, in pipeline order:
     CANDIDATE_SCHEMA_INVALID -> CANDIDATE_N_MODE_INVALID -> CANDIDATE_SUPPORT_INVALID ->
     CANDIDATE_NOT_HOMOMETRIC -> CANDIDATE_MEMBER_NOT_PRIMITIVE -> CANDIDATE_AFFINE_EQUIVALENT ->
     CANDIDATE_COMPLEMENT_IMAGE -> CANDIDATE_AFFINE_PLUS_COMPLEMENT_EQUIVALENT ->
     CANDIDATE_TRIPLE_G_ALIGNABLE -> CANDIDATE_CERTIFICATE_INVALID
3. family rejection, in pipeline order:
     FAMILY_PAIR_COUNT_INVALID -> FAMILY_MEMBER_REUSED -> FAMILY_MEMBER_G_EQUIVALENT ->
     FAMILY_AUTOCORRELATION_CLASS_REUSED -> FAMILY_NOT_FREEZABLE
```

## 15. Tests

Fast tests (ordinary unit; N=12 and tiny N):

```text
N=12 positive certificates ; every negative fixture ; verification modes and N/mode validation ;
candidate-stream envelope + stream hash ; lower-order equality fields ; direct-vs-affine-complement separation ;
autocorrelation ; one-step table ; transition multiset ; triple array ; primitive period ; group enumeration ;
group action ; canonical member key ; canonical pair key ; lexicographic ordering ; complement handling ;
triple-array alignment and nonalignment (two-class, §8) ; family mutual inequivalence ;
distinct autocorrelation classes ; deterministic freeze selection ; schema/stream rejection ;
failure-code precedence ; payload/envelope nonrecursive hashing ; hash coverage ; canonical JSON ;
nondeterministic-metadata exclusion ; decision-ledger byte replay ; forbidden imports ; verifier independence
```

Independence testing (required, deterministic; must not import generator code to inspect it):

```text
AST import test         : verifier imports exclude every generator module, psi_trs, run_n64_falsifier_v0_1,
                          and any shared predicate helper; serializer imports no witness-mathematics module.
transitive import-graph : inspect the verifier's complete project-local import closure and reject any path
                          reaching generator modules, immutable N64 evaluator mathematics, psi_trs, or shared
                          witness-predicate helpers.
source-path test        : confirm the verifier's witness mathematics originates only from the verifier module
                          and permitted standard-library / zero-math serializer dependencies.
```

Slow tests permitted only for:

```text
synthetic N=64 rejection fixtures ; balanced-complement N=64 controls copied by value ;
non-primitive N=64 fixtures ; affine/complement-equivalent N=64 fixtures ;
future frozen primary N=64 witnesses, only after separately authorized.
```

```text
full primary-family N=64 slow tests are deferred and skipped until an authorized frozen family fixture exists.
```

**No test may search for or generate an N=64 witness.** Slow tests are marked and separable from the ordinary
unit run.

## 16. Generator interface boundary

Only the **external interface** expected from a future generator is defined here (no algorithm). The future
generator must provide the frozen `candidate_stream_envelope` (§4.1), i.e.:

```text
candidate_stream schema name/version ; verification mode ; N ; ordered raw records ; candidate count ;
gap-free generation indices ; generator identity hash ; generator configuration hash ; budget identity hash ;
terminal status ; candidate_stream_sha256
```

The terminal status is stored inside the hashed stream payload. The verifier/freezer are agnostic to the
generation algorithm.

```text
The later planning review held generator routing unresolved.

Current candidates remain:
  previously specified SAT/SMT-style route
  custom deterministic backtracking candidate route
  deterministic algebraic fallback

No route is accepted or authorized by this verifier/freezer document.
```

This document defines no generator mathematics.

## 17. Required conclusion

```text
VERIFIER_FREEZE_SPECIFICATION_STATUS = READY_FOR_ADVERSARIAL_DOCUMENT_REVIEW
VERIFIER_IMPLEMENTATION_AUTHORIZED    = False
GENERATOR_ROUTE_STATUS                = UNRESOLVED
GENERATOR_IMPLEMENTATION_AUTHORIZED   = False
N64_WITNESS_GENERATION_AUTHORIZED     = False
```

*End — TORMENT Brainvision Independent Higher-Order Witness Verifier and Freeze Infrastructure Implementation
Specification v0.1. Docs-only, non-authorizing, non-implementing. Governs only the verifier, serializer,
schemas, and freeze/replay infrastructure; specifies no generator mathematics and no ΨTRS evaluation. Does not
amend the accepted witness-family specification. `psi_trs.py`, `run_n64_falsifier_v0_1.py`, and the production
TORMENT memory kernel are immutable. No `§0` pointer; no registry or orientation update; no tags.*
