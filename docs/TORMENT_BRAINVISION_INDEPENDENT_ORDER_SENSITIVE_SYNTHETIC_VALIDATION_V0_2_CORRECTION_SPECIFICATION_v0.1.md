# TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation v0.2 Correction Specification v0.1

## Document status

```text
document_type = docs-only correction specification
specification_version = v0.1 (of the v0.2 correction lane)
specification_status = READY_FOR_ADVERSARIAL_REVIEW
codex_review = ACCEPT_WITH_REQUIRED_CORRECTIONS (this revision resolves all required corrections)
posture = docs-only, non-executing, non-authorizing, version-separated from v0.1
brainvision = offline, quarantined, non-production, non-service, non-kernel, non-memory-integrated
implementation_authorized = False
execution_authorized = False
real_manifest_contact_authorized = False
```

Authoritative repository baseline:

```text
branch = main
working tree = clean
HEAD = origin/main
HEAD = 54d98f3
```

This document specifies a corrected Stage S3B v0.2 synthetic-validation lane. It is a specification only. It creates no code, edits no test, runs nothing, contacts no real manifest, performs no Git operation, and modifies no v0.1 artifact. It confers no implementation authority and no execution authority. Every new v0.2 identity referenced here is explicitly unbound; the exact values are to be calculated and bound later, during a separate implementation review and a separate execution authorization. No existing hash or Git-blob identity is invented, recalculated, normalized, or altered by this document.

This revision incorporates the read-only, source-derived canonical schema enumerated in Section 6, obtained by review of the already-committed frozen fixture generator, verifier, and freeze library. The real frozen Stage S1 manifest was not opened, read, hashed, parsed, or evaluated to produce this document.

Throughout, the following claim classes are kept distinct and are labelled where used:

```text
FACT(v0.1)          = a fact established by the Stage S3B v0.1 execution-failure findings
REQ(v0.2)           = a normative requirement imposed on the future v0.2 lane
FUTURE(unbound)     = an implementation detail not yet fixed or bound
SCI-VOCAB           = scientific-result vocabulary (only valid when the science was genuinely reached)
OPS-VOCAB           = operational / controlled-outcome vocabulary (consumed, non-scientific outcomes)
```

Normative keywords MUST, MUST NOT, SHALL, SHALL NOT, and MAY are used in their ordinary specification sense.

---

## 1. Purpose and status

FACT(v0.1). The single Stage S3B v0.1 one-run authority is permanently consumed. The v0.1 invocation reached real-manifest contact, consumed its authority, and then failed on an operational implementation defect before any descriptor call or scientific gate evaluation. The observed process outcome was:

```text
SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION
exit = 2
manifest contact count = 1
scientific result = unavailable
final publication = absent
empty staging directory = retained permanently
```

Purpose. This specification defines a version-separated v0.2 lane whose sole operational purpose is to correct the confirmed fixed-fixture field-name defect and the surrounding coverage, phase-accounting, evidence-durability, and exit-masking weaknesses, while leaving the preregistered science, the frozen fixture family, and all v0.1 artifacts entirely unchanged.

Status.

```text
SPECIFICATION_STATUS = READY_FOR_ADVERSARIAL_REVIEW
IMPLEMENTATION_AUTHORIZED = False
EXECUTION_AUTHORIZED = False
REAL_MANIFEST_CONTACT_AUTHORIZED = False
```

This document does not itself authorize implementation, execution, or manifest contact. Acceptance of this specification advances only to a separate implementation-authorization stage. The opening status here and the closing verdict (Specification verdict) are identical: `READY_FOR_ADVERSARIAL_REVIEW`.

---

## 2. Historical v0.1 preservation

FACT(v0.1). The confirmed source-level contradiction was a fixed-fixture field-name mismatch:

```text
canonical fixed fixture emits:
binary_H0
binary_H1

v0.1 runner incorrectly expected on the fixed fixture:
binary_A
binary_B
```

Accepted generated fixtures correctly use `binary_A` and `binary_B`. The defect was therefore narrow: the v0.1 fixed-positive path applied the accepted-fixture key names to the fixed fixture, whose canonical keys are `binary_H0` and `binary_H1`. This is confirmed directly by the frozen source schema in Section 6: the verifier's fixed-fixture record uses `_H0`/`_H1` member keys, while accepted fixtures use `_A`/`_B` member keys.

FACT(v0.1). The reconstructed immediate exception is:

```text
KeyError("binary_A")
```

This is the high-confidence source-supported reconstructed immediate cause recorded in the v0.1 execution-failure findings. It MUST NOT be presented as a captured traceback; no traceback or persisted in-process execution-state record was retained.

REQ(v0.2). The v0.2 lane MUST preserve the v0.1 record intact. The following artifacts are frozen consumed-run evidence and SHALL NOT be altered, repaired, reused, cleaned, deleted, renamed, reconstructed, or executed by the v0.2 lane or its tests:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_FAILURE_FINDINGS_v0.1.md
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

REQ(v0.2). The frozen Stage S1 synthetic manifest and the independent Stage S2 descriptor (and its test) SHALL remain unchanged. The v0.2 lane MUST NOT modify, regenerate, normalize, or re-hash them, and MUST NOT rerun the Stage S1 fixture freezer. The v0.1 retained empty staging directory MUST remain exactly as retained; the v0.2 lane MUST NOT inspect it for reuse, promote into it, clean it, or depend on its state in any way.

---

## 3. Exact operational correction

REQ(v0.2). The v0.2 runner MUST read the canonical fixed-fixture member sequences from the frozen manifest fields:

```text
fixed_fixture.binary_H0
fixed_fixture.binary_H1
```

REQ(v0.2). The v0.2 runner MUST read the accepted generated fixtures' member sequences from:

```text
accepted_fixtures[*].binary_A
accepted_fixtures[*].binary_B
```

REQ(v0.2). The correction is limited to the runner-side field-name contract and the surrounding validation, phase-accounting, exit-mapping, and evidence weaknesses identified in the v0.1 findings and the Codex review. The v0.2 lane SHALL NOT rename, rewrite, remap, alias, or normalize any frozen manifest field. The canonical field names are a property of the frozen manifest, not of the runner; the runner MUST conform to the manifest, never the reverse.

REQ(v0.2). No other operational behavior may change under cover of this correction. The correction grants no license to alter descriptor logic, fixture construction, family membership, or the gate.

---

## 4. Scientifically unchanged contract

REQ(v0.2). The preregistered scientific gate is unchanged. The operational v0.1 failure grants no authority to:

```text
tune or relax any threshold
alter fixture membership or count
weaken, sample, or aggregate any control
reinterpret or re-score any result
rescue, strengthen, or revive the strong-order hypothesis
substitute derived output for the frozen descriptor's actual output
```

REQ(v0.2). The complete gate SHALL remain exactly as governed by the challenger specification and bound by the Stage S3A runner-implementation authorization: all malformed and degenerate controls correct; all identity controls correct; all nuisance controls correct (Method B, full enumeration, no sampling); the fixed positive fixture distinguished; 8 of 8 frozen generated pairs distinguished; two complete pass bundles byte-identical; and all input, boundary, serialization, and publication checks valid. `7 of 8` remains a scientific failure. No majority threshold, tolerance, aggregate score, fixture removal, tuning, sampling, or floating-point relaxation is permitted.

Permanent posture is preserved:

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
FORMAL_HOLD = active
Mode_0 = active
```

A future v0.2 PASS would establish only that the corrected challenger distinguishes the frozen synthetic family under the unchanged gate; it would remain a synthetic-fixture result, not a claim about Brainvision, and not a repair of the frozen historical F3 result.

---

## 5. Version-separated v0.2 artifact namespace

REQ(v0.2). The v0.2 lane MUST be fully version-separated from v0.1. No v0.1 artifact is edited, extended, imported for reuse of its defective paths, or continued. The intended new implementation paths are fixed as follows unless a stronger collision-free naming reason is established during implementation review:

```text
runner                 = research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py
runner_test            = research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py
schema_contract_module = research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py
```

REQ(v0.2). Four distinct execution-artifact concepts are defined, and MUST NOT be conflated. Their intended v0.2 paths are:

```text
execution_arming_path =
  research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.arming
  artifact type = temporary directory (OUTSIDE the final execution-journal directory)
  required content = execution_arming_path/current_state.json, durably written, read back, and
  verified BEFORE consumption with the complete intended consumed state
  (phase = CONTACT_ARMED, authority_consumed = true, contact_armed = true,
  manifest_contact_attempt_count = 0, manifest_read_success_count = 0).
  The temporary directory and its current_state.json existing does NOT by itself consume authority.

execution_journal_dir =
  research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal
  established ONLY by one atomic same-filesystem directory rename of execution_arming_path to this
  path (Section 9); it MUST NOT be separately created and MUST NOT exist before the rename.

execution_journal_dir/current_state.json =
  the same current_state.json carried in by the rename; thereafter the atomically-replaceable
  durable snapshot of the latest verified execution state

execution_journal_dir/terminal_evidence.json =
  the file exclusively created once at terminalization and immutable thereafter
```

REQ(v0.2). The scientific-result paths are separate again from all four execution-artifact concepts:

```text
scientific_result_staging_dir =
  research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.staging

final_publication_dir =
  research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_2
```

REQ(v0.2). None of the v0.2 paths above may collide with, inspect for reuse, or operate inside the v0.1 retained staging directory. The `execution_journal_dir` MUST be distinct from `scientific_result_staging_dir`; durable consumed-outcome and operational-failure evidence MUST NOT be written into, or depend on the creation or promotion of, the scientific-result staging directory (Sections 14, 15).

FUTURE(unbound). The exact final scientific file names within `final_publication_dir` are fixed in Section 15; the directory and artifact names above are the intended v0.2 namespace, subject at implementation review only to confirmation of collision-freedom, never to reuse of a v0.1 path.

---

## 6. Canonical fixed-fixture schema

REQ(v0.2). The complete canonical manifest schema is knowable before implementation authorization. It is derived by read-only review of the already-committed frozen sources; the real manifest is not consulted. The authoritative frozen schema-provider sources are:

```text
manifest structure + top-level/accepted/wrapper/source/diagnostics key contracts:
  research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py

fixed-fixture record field contract (the _H0/_H1 member schema):
  research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py

configuration-identity payload contract:
  research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

FUTURE(unbound). The exact Git-blob and raw identities of these three frozen sources are already recorded in the governing Stage S1 documents; this specification does not restate, recompute, or alter those hash values. The v0.2 schema-contract module (Section 5) MUST bind against these frozen sources by identity during implementation review.

REQ(v0.2). The manifest schema-contract identity string (the top-level `schema` value) is:

```text
torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-manifest-v0.1
```

REQ(v0.2). The complete top-level manifest key set, in exact order, is:

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

REQ(v0.2). The canonical fixed-fixture record key set, in exact order, is:

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

REQ(v0.2). Within the fixed-fixture record: `binary_H0` and `binary_H1` are the canonical member sequences (each a raw 64-entry integer binary sequence over {0,1}); `weight_H0`/`weight_H1`, `A2_H0`/`A2_H1`, and `transition_table_H0`/`transition_table_H1` are the lower-order evidence; and `affine_inequivalence_certificate`, `affine_complement_inequivalence_certificate`, `triple_disagreement_count`, and `triple_disagreement_indices` are the certificate fields. Certificate and lower-order fields MUST be validated for presence and required structure post-contact, but MUST NOT be passed into the descriptor.

REQ(v0.2). The two auxiliary top-level contracts required by v0.2 validation are, in exact order:

```text
source_identity keys:
  generator_source_path, generator_git_blob, generator_raw_sha256,
  verifier_source_path, verifier_git_blob, verifier_raw_sha256,
  test_source_identities, repository_commit, python_version

search_diagnostics keys:
  total_seeds_visited, eligibility_rejection_counts, eligible_duplicate_count,
  accepted_seed_order_positions, terminal_seed_tuple, terminal_status

configuration_identity object:
  configuration_payload (the frozen 16-field configuration payload)
  configuration_sha256
```

REQ(v0.2). Because the complete authoritative schema is derivable from the frozen sources above without consulting the real manifest, no blocking schema-discovery prerequisite is required. The v0.2 schema-contract module (Section 5) is a normal v0.2 implementation artifact that re-expresses exactly this enumerated contract, is owned outside the runner, is parity-verified against the frozen provider sources by the bounded tests (Section 16), and is reviewed and identity-bound within the standard authorization chain (Section 17). The v0.2 runner and tests MUST both consume that single schema-contract module and MUST NOT independently invent field names.

---

## 7. Accepted-fixture schema

REQ(v0.2). The frozen manifest's accepted generated fixtures MUST be consumed using the canonical accepted-fixture key set, in exact order, derived from the frozen freeze library:

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

REQ(v0.2). The accepted-fixture member sequences are `binary_A` and `binary_B` (each a raw 64-entry integer binary sequence over {0,1}). There MUST be exactly eight accepted fixtures, in the frozen accepted-family order, with `family_index` gap-free and equal to list position. No accepted fixture may be removed, reordered, replaced, reconstructed from another source, selected by descriptor output, or skipped after failure.

REQ(v0.2). The accepted-fixture field names `binary_A`/`binary_B` are correct and unchanged from v0.1. The defect corrected by v0.2 concerns only the fixed-fixture member field names (`binary_H0`/`binary_H1`); the accepted-fixture contract MUST NOT be altered. The family identity/order fields required by v0.2 are `family_index`, `seed_order_position`, `seed_tuple`, `member_orbit_key_A`/`member_orbit_key_B`, and `pair_duplicate_key`, together with top-level `family_frozen`, `K_synthetic`, and `N`.

---

## 8. Pre-contact preflight contract

REQ(v0.2). Before creating the arming artifact, before contact arming, and before any real-manifest contact, the v0.2 runner MUST validate — fail-closed and in a fixed order — only information genuinely available without reading the real manifest:

```text
repository root
branch
clean working tree
HEAD = origin/main
supported Python version
latest execution-authorization commit identity
runner Git-blob and raw identities
runner-test Git-blob and raw identities
descriptor Git-blob and raw identities
descriptor-test Git-blob and raw identities
schema-contract module Git-blob and raw identities
expected manifest path
expected manifest external identity
expected manifest payload identity
expected freeze-configuration identity
expected manifest schema-contract identity
canonical fixed-fixture field contract (binary_H0 / binary_H1)
canonical accepted-fixture field contract (binary_A / binary_B)
CLI shape
stdin emptiness
absence of the execution_arming_path (temporary directory)
absence of the execution_journal_dir
absence of the scientific_result_staging_dir
absence of the final_publication_dir
production-boundary restrictions
evidence-contact restrictions
```

REQ(v0.2). Pre-contact validation MUST validate only expected contract identities and repository/authorization/boundary state. It MUST NOT open, read, hash, parse, or otherwise inspect the real manifest contents. Pre-contact checks cannot validate unread real-manifest contents; any claim, check, or code path that purports to validate real fixed-fixture or accepted-fixture contents before contact is prohibited.

REQ(v0.2). The `expected manifest external identity`, `expected manifest payload identity`, `expected freeze-configuration identity`, `expected manifest schema-contract identity`, and the `canonical fixed-fixture / accepted-fixture field contract` are compared pre-contact against expected constant identities, the expected path, and the schema-contract module; they are expectations bound into the runner and the schema-contract module, not observations read from the manifest. The corresponding observed identities are computed only post-contact (Section 10).

REQ(v0.2). Any pre-contact failure MUST refuse before arming, before the CONTACT_ARMED promotion, and before any real-manifest byte is read, and MUST leave authority unconsumed. Preflight MUST confirm the absence of all four v0.2 execution and scientific paths and of the arming artifact (Sections 5, 9, 15).

---

## 9. Durable authority-consumption protocol

REQ(v0.2). The v0.2 runner MUST implement the following conservative durable authority-consumption protocol. The intent is that real-manifest contact can never occur before authority consumption has durable, machine-readable evidence, and that no consumed execution journal can exist unless authority was actually consumed.

```text
1. Complete every pre-contact validation (Section 8). Any failure is a pre-contact refusal
   with authority unconsumed; neither the arming directory nor the execution journal is created.

2. Exclusively create the temporary arming DIRECTORY at execution_arming_path (OUTSIDE
   execution_journal_dir) and durably write, read back, and verify
   execution_arming_path/current_state.json containing the complete intended consumed state:
       phase = CONTACT_ARMED
       authority_consumed = true
       contact_armed = true
       manifest_contact_attempt_count = 0
       manifest_read_success_count = 0
   The write MUST be durable (flushed/synced) and MUST be read back and verified. Exclusive
   creation MUST fail closed (EVIDENCE_ARMING_FAILED) if the arming path already exists, or on any
   failure to create, write, flush, read back, or verify the directory or its current_state.json.
   Preparing this directory and file does NOT by itself consume authority: the serialized booleans
   describe the state that becomes authoritative only upon successful promotion (Section 11).

3. Perform exactly one atomic same-filesystem directory rename:
       execution_arming_path  ->  execution_journal_dir
   execution_journal_dir MUST NOT exist before the rename. No separate creation of
   execution_journal_dir, no file-only move into a pre-created journal directory, no
   copy-and-delete promotion, and no merge, overwrite, replacement, or reuse of an existing
   journal directory is permitted. A failure of the rename before durable completion
   (CONTACT_ARM_PROMOTION_FAILED) leaves authority unconsumed.

4. The successful durable completion and verification of that single atomic directory rename is
   the EXACT authority-consumption point. Authority is consumed if and only if the rename durably
   succeeds, at which moment execution_journal_dir/current_state.json (carried in by the rename)
   is the first authoritative journal state (CONTACT_ARMED, authority_consumed = true, both
   counters 0).

5. Before the rename durably succeeds, authority remains unconsumed. After it durably succeeds,
   no cleanup, rollback, retry, restart, reuse, or second v0.2 operation is permitted, even if the
   subsequent manifest open or read fails. The single v0.2 authority is spent. All subsequent
   journal updates operate on execution_journal_dir/current_state.json through the atomic
   file-replacement protocol (Section 14).

6. For each pass n in {1, 2}, immediately before any filesystem open/read of the manifest, the
   runner MUST durably increment and verify manifest_contact_attempt_count and record
   phase = MANIFEST_CONTACT_STARTED_PASS_n. Only after all manifest bytes have been read
   successfully MUST the runner durably increment manifest_read_success_count and record
   phase = MANIFEST_READ_SUCCEEDED_PASS_n.

7. A crash or exception during open/read therefore leaves durable evidence of:
       authority_consumed = true
       manifest_contact_attempt_count >= 1
       manifest_read_success_count possibly 0
```

REQ(v0.2). The two contact counters obey the following invariants, which MUST be preserved by every durable state update:

```text
manifest_contact_attempt_count is incremented and durably verified BEFORE each open/read attempt
manifest_read_success_count is incremented ONLY after all manifest bytes have been read successfully
manifest_read_success_count <= manifest_contact_attempt_count
manifest_contact_attempt_count <= 2
manifest_read_success_count <= 2
```

REQ(v0.2). A third contact attempt or a third successful read is prohibited and MUST be rejected. There is no ambiguous single "contact count"; the split attempt/success counters ensure durable evidence can never undercount manifest contact. Removal of a retained temporary arming directory MUST NOT be performed silently by the runner; it MUST require the separately bounded cleanup procedure that first proves all of: execution_journal_dir absent; no successful atomic promotion; no manifest-contact attempt; and authority unconsumed. The runner itself MUST NOT silently clean and retry.

---

## 10. Post-contact validation contract

REQ(v0.2). For each pass independently, after the authorized real-manifest read for that pass and before any descriptor call or gate evaluation for that pass, the v0.2 runner MUST perform, fail-closed and in order:

```text
durably increment manifest_contact_attempt_count (before the open/read)
open and read fresh manifest bytes
durably increment manifest_read_success_count (after complete successful read)
compute and compare observed external manifest hash against the bound expected identity
parse independently
compute and compare observed payload hash against the bound expected identity
validate the complete top-level manifest key set
validate the complete fixed-fixture key set
validate binary_H0 and binary_H1 presence, structure, and binary domain
validate fixed-fixture lower-order evidence
validate fixed-fixture certificates and required certificate fields
validate the complete accepted-fixture key set
validate binary_A and binary_B presence, structure, and binary domain
validate accepted fixture count = 8
validate accepted-family order and identity constraints
validate family_frozen = true
validate all frozen-family constraints required by the scientific gate
only then enter descriptor / scientific evaluation for that pass
```

REQ(v0.2). Pass 2 MUST NOT reuse pass 1's parsed manifest object, validation result, fixture objects, or descriptor outputs; each pass independently reloads, re-verifies, and re-validates. The maxima are `manifest_contact_attempt_count = 2` and `manifest_read_success_count = 2`. If pass 1 fails before valid scientific evaluation, pass 2 MUST NOT be attempted.

REQ(v0.2). Every schema or identity error detected in this post-contact phase MUST produce a controlled post-contact invalidity outcome (Section 12: `POSTCONTACT_SCHEMA_INVALID` or `POSTCONTACT_IDENTITY_INVALID`), not a generic pre-contact refusal, and not an uncaught exception. In particular, a fixed-fixture field-set or `binary_H0`/`binary_H1` presence/structure failure — the exact class of defect that crashed v0.1 — MUST be detected here and converted into a controlled invalid outcome (Section 3 correction verified against the Section 6 schema). Descriptor calls MUST receive only validated raw 64-entry binary vectors; manifest metadata, certificates, indices, seed tuples, and labels MUST NOT reach the descriptor.

REQ(v0.2). Hash handling is clarified as follows:

```text
prohibited =
  recomputing hashes to revise, replace, normalize, or newly bind historical identities

permitted only after authorized contact =
  computing the OBSERVED external and payload hashes for comparison against the already-bound
  expected identities (never to revise or rebind them)
```

---

## 11. Execution phase machine

REQ(v0.2). The v0.2 runner MUST maintain an explicit, durably-recorded execution phase. Before consumption the runtime distinguishes a physical preparation state from a serialized intended journal state:

```text
physical preparation state =
  the runtime is in PRE_CONTACT during preflight, then the temporary arming directory
  (execution_arming_path) exists and is being prepared

serialized intended journal state (written into execution_arming_path/current_state.json) =
  phase = CONTACT_ARMED
  authority_consumed = true
  contact_armed = true
  manifest_contact_attempt_count = 0
  manifest_read_success_count = 0
```

The serialized booleans describe the state that becomes authoritative only when the temporary arming directory is atomically renamed to execution_journal_dir (Section 9). While that serialized state is still located at execution_arming_path:

```text
authority actually consumed = false
```

and after the successful directory rename:

```text
authority actually consumed = true
```

The serialized state does not itself consume authority while still located at the temporary arming path; there is no distinct pre-consumption `EVIDENCE_ARMING_PRECONSUMPTION` serialized phase.

REQ(v0.2). The consumed execution-journal phases (recorded in execution_journal_dir/current_state.json) begin with CONTACT_ARMED and proceed per pass:

```text
CONTACT_ARMED

MANIFEST_CONTACT_STARTED_PASS_1
MANIFEST_READ_SUCCEEDED_PASS_1
MANIFEST_VALIDATING_PASS_1
MANIFEST_VALIDATED_PASS_1
SCIENTIFIC_EVALUATING_PASS_1

MANIFEST_CONTACT_STARTED_PASS_2
MANIFEST_READ_SUCCEEDED_PASS_2
MANIFEST_VALIDATING_PASS_2
MANIFEST_VALIDATED_PASS_2
SCIENTIFIC_EVALUATING_PASS_2

RESULT_CONSTRUCTING
STAGING_WRITING
STAGING_VERIFYING
PROMOTING
FINAL_VERIFICATION
COMPLETE
```

REQ(v0.2). The first state recorded in the consumed execution journal MUST be exactly:

```text
phase = CONTACT_ARMED
authority_consumed = true
manifest_contact_attempt_count = 0
manifest_read_success_count = 0
```

REQ(v0.2). The transition to `MANIFEST_CONTACT_STARTED_PASS_n` MUST durably increment `manifest_contact_attempt_count` before any filesystem open/read. The transition to `MANIFEST_READ_SUCCEEDED_PASS_n` MUST occur only after the complete byte read succeeds and MUST durably increment `manifest_read_success_count`. `SCIENTIFIC_EVALUATING_PASS_n` and later phases MUST NOT be entered unless that pass's post-contact validation (Section 10) completed successfully.

REQ(v0.2). The runner MUST also define explicit terminal states, and MUST NOT record a phase or terminal state that implies the scientific gate was evaluated when it was not:

```text
REFUSED_PRE_CONTACT
FAILED_EVIDENCE_ARMING
FAILED_CONTACT_ARM_PROMOTION
FAILED_MANIFEST_READ_POST_CONSUMPTION
INVALID_POST_CONTACT
FAILED_POST_CONTACT_IMPLEMENTATION
FAILED_SCIENTIFIC_EVALUATION
FAILED_RESULT_CONSTRUCTION
FAILED_STAGING_WRITE
FAILED_STAGING_VERIFICATION
FAILED_PROMOTION
FAILED_FINAL_VERIFICATION
FAILED_EVIDENCE_UPDATE_AFTER_CONSUMPTION
COMPLETE_PUBLISHED
```

---

## 12. Failure taxonomy and canonical codes

REQ(v0.2). The v0.2 lane MUST separate, at minimum, the following failure situations, each routed to a distinct canonical failure category:

```text
pre-contact refusal
evidence-arming failure
contact-arm promotion failure
manifest open/read failure after consumption
post-contact schema invalidity
post-contact identity invalidity
post-contact implementation exception
scientific evaluation exception
artifact construction failure
staging write failure
staging verification failure
atomic promotion failure
final verification failure
evidence-update failure after consumption
```

REQ(v0.2). The following canonical failure codes are fixed by this specification; their exact string spellings are normative.

Pre-consumption, refusal-class (authority unconsumed, exit 2) — OPS-VOCAB refusal family:

```text
PRECONTACT_REPOSITORY_STATE_REFUSED
PRECONTACT_AUTHORIZATION_REFUSED
PRECONTACT_IDENTITY_REFUSED
PRECONTACT_SCHEMA_CONTRACT_REFUSED
PRECONTACT_MANIFEST_EXPECTATION_REFUSED
PRECONTACT_CLI_REFUSED
PRECONTACT_STDIN_REFUSED
PRECONTACT_OUTPUT_PATH_PRESENT_REFUSED
PRECONTACT_BOUNDARY_REFUSED
EVIDENCE_ARMING_FAILED
CONTACT_ARM_PROMOTION_FAILED
```

Post-consumption, consumed class (authority consumed) — OPS-VOCAB consumed family:

```text
MANIFEST_READ_FAILED_AFTER_CONSUMPTION
POSTCONTACT_SCHEMA_INVALID
POSTCONTACT_IDENTITY_INVALID
POSTCONTACT_IMPLEMENTATION_EXCEPTION
SCIENTIFIC_EVALUATION_EXCEPTION
RESULT_CONSTRUCTION_FAILED
STAGING_WRITE_FAILED
STAGING_VERIFICATION_FAILED
PROMOTION_FAILED
FINAL_VERIFICATION_FAILED
EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION
```

REQ(v0.2). Refusal vocabulary is reserved for failures occurring strictly before authority consumption (before the CONTACT_ARMED promotion durably succeeds). No post-consumption failure may be printed, logged as a terminal status, or serialized into evidence as:

```text
UNAUTHORIZED_EXECUTION
```

The token `UNAUTHORIZED_EXECUTION` (and any equivalent refusal-class label) SHALL NOT appear as the terminal status of any outcome after CONTACT_ARMED is durably promoted. The v0.1 masking defect — a post-contact implementation exception surfaced through the pre-contact refusal channel — MUST NOT recur.

REQ(v0.2). The runner MUST NOT serialize arbitrary traceback text into scientific or terminal evidence. A bounded implementation diagnostic field MAY carry an exception class name and a bounded, sanitized message for operational triage, but evidence MUST use the canonical phase and failure vocabulary above, never free-form exception text.

REQ(v0.2). `POSTCONTACT_SCHEMA_INVALID` and `POSTCONTACT_IDENTITY_INVALID` are controlled invalidity outcomes (Section 13 exit 3). `EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION`, `MANIFEST_READ_FAILED_AFTER_CONSUMPTION`, `POSTCONTACT_IMPLEMENTATION_EXCEPTION`, and `SCIENTIFIC_EVALUATION_EXCEPTION` are consumed implementation/infrastructure failures (exit 4). `RESULT_CONSTRUCTION_FAILED`, `STAGING_WRITE_FAILED`, `STAGING_VERIFICATION_FAILED`, `PROMOTION_FAILED`, and `FINAL_VERIFICATION_FAILED` are consumed publication/verification failures (exit 5).

---

## 13. Exit-code contract

REQ(v0.2). The v0.2 runner MUST define distinct process exit codes so that a consumed failure can never resemble an unconsumed refusal and a controlled validation invalidity is never a scientific result:

```text
0 = published scientific PASS
    SYNTHETIC_GATE_PASSED; three-file scientific bundle published; authority consumed

1 = published scientific FAIL
    SYNTHETIC_GATE_FAILED (valid scientific miss, including failure to distinguish all 8 pairs);
    three-file scientific bundle published; authority consumed

2 = unconsumed pre-contact refusal
    no manifest contact; no scientific result; no controlled outcome; authority_consumed = false

3 = consumed controlled validation invalidity
    controlled post-contact schema or identity invalidity; authority consumed;
    NOT a scientific result; NO three-file scientific publication; durable controlled terminal evidence retained

4 = consumed implementation / infrastructure failure
    authority consumed; NOT a scientific result and NOT a controlled validation outcome;
    durable operational terminal evidence retained where the evidence medium permits

5 = consumed publication / verification failure
    authority consumed; result construction, staging, promotion, or final verification failed;
    durable operational terminal evidence retained where the evidence medium permits
```

REQ(v0.2). Exit `2` is reserved for pre-consumption refusals only (including `EVIDENCE_ARMING_FAILED` and `CONTACT_ARM_PROMOTION_FAILED`, which occur before durable CONTACT_ARMED promotion). Exit `3` is reserved for controlled post-contact validation invalidity and MUST NOT produce the three-file scientific publication bundle. Exits `4` and `5` are reserved for post-consumption operational failures. Under no circumstances may a post-consumption failure exit `2`; under no circumstances may exit `3`, `4`, or `5` be reported with a SCI-VOCAB gate result kind as its scientific result.

REQ(v0.2). The future operator MUST capture the process exit code immediately after the single invocation, before running any other command, and record it alongside the durable evidence. The exit code and the durably-recorded terminal status MUST be mutually consistent.

---

## 14. Durable consumed-failure evidence

REQ(v0.2). Two durable journal artifacts exist inside `execution_journal_dir`, with distinct and non-contradictory write semantics:

```text
current_state.json =
  the mutable durable snapshot of the latest verified execution state. Its initial contents are
  the verified CONTACT_ARMED state carried into execution_journal_dir by the atomic arming-
  directory rename (Section 9), not a separately created file; thereafter it is updated by atomic
  replacement (write-temp + atomic rename) at each state transition. It is NOT collision-refused
  per update.

terminal_evidence.json =
  the immutable terminal record; it is created exactly once at terminalization by EXCLUSIVE
  creation and is never rewritten, replaced, or appended thereafter.
```

Optional append-only transition records MAY be specified by the implementation, but MUST NOT be required unless a concrete design need is demonstrated at implementation review. No single file is both repeatedly atomically replaced and collision-refused for every update.

REQ(v0.2). Every terminal condition reached at or after CONTACT_ARMED — including a controlled invalid outcome (exit 3) and every operational failure (exit 4, 5) — MUST attempt to write durable terminal evidence into `execution_journal_dir/terminal_evidence.json`, independently of the scientific-result staging directory. The terminal evidence MUST NOT depend on the creation, writing, or promotion of `scientific_result_staging_dir`.

REQ(v0.2). The terminal evidence record MUST use a wrapper that resolves the self-reference paradox by digesting only the payload bytes:

```text
{
  "payload": { ...canonical terminal evidence fields... },
  "payload_sha256": "<SHA-256 of the canonical serialized payload bytes only>"
}
```

The digest excludes the wrapper's own `payload_sha256` field. Writing `terminal_evidence.json` MUST use deterministic canonical serialization of the payload, a durable (flushed/synced) write, read-back verification of the exact bytes, exact payload-digest verification, and exclusive creation of `terminal_evidence.json` (collision refusal if it already exists).

REQ(v0.2). The terminal-evidence payload MUST contain at least:

```text
format identifier
schema version
operation version
authority_consumed
contact_armed
manifest_contact_attempt_count
manifest_read_success_count
execution phase
terminal status
failure category
canonical failure code
failure stage
controlled_outcome_available
controlled_outcome_kind
scientific_result_available
scientific_result_kind
scientific_evaluation_reached
descriptor_evaluation_reached
final_publication_available
repository execution HEAD
branch
Python version
runner path and identities
runner-test path and identities
descriptor path and identities
descriptor-test path and identities
schema-contract module path and identities
expected manifest path
expected external manifest identity
expected payload identity
expected freeze-configuration identity
observed identities when safely available
publication status
staging status
timestamps
```

REQ(v0.2). Controlled invalid outcome semantics. When post-contact schema or identity validation fails, the runner MUST record exactly:

```text
controlled_outcome_available = true
controlled_outcome_kind = SYNTHETIC_GATE_INVALID

scientific_result_available = false
scientific_result_kind = null
scientific_evaluation_reached = false
descriptor_evaluation_reached = false

terminal_status = INVALID_POST_CONTACT
publication_status = NO_SCIENTIFIC_PUBLICATION_OPERATIONAL_EVIDENCE_RETAINED

exit_code = 3
authority_consumed = true
```

`SYNTHETIC_GATE_INVALID` MAY remain the controlled-outcome vocabulary but MUST NOT be called a scientific result and MUST NOT be stored in `scientific_result_kind`. The three SCI-VOCAB gate result kinds `SYNTHETIC_GATE_PASSED`, `SYNTHETIC_GATE_FAILED`, and `SYNTHETIC_GATE_INVALID` MUST NOT be published, implied, or reconstructable as a scientific result unless the corresponding scientific and publication conditions were genuinely reached and satisfied. For any consumed operational failure (exit 4 or 5), `scientific_evaluation_reached`, `descriptor_evaluation_reached`, `scientific_result_available`, and `final_publication_available` MUST be recorded truthfully as false where they were not reached, and `controlled_outcome_available` MUST be false unless a controlled invalid outcome had already genuinely completed.

REQ(v0.2). Evidence-update failure after consumption. A failed evidence medium cannot be required to durably record its own failure. When a journal update fails after consumption (for example, `current_state.json` replacement or `terminal_evidence.json` creation fails), the runner MUST:

```text
treat the failure as EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION
authority_consumed = true
exit_code = 4
scientific_result_available = false unless a scientific result had already genuinely completed
controlled_outcome_available = false unless a controlled invalid outcome had already genuinely completed
```

Define:

```text
last_verified_durable_state =
  the authoritative persisted state (the most recent successfully written and verified
  current_state.json) at the moment a later journal update fails
```

The runner MUST emit a bounded console fallback line containing at least:

```text
EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION
last_verified_phase
authority_consumed = true
manifest_contact_attempt_count
manifest_read_success_count
exit = 4
```

with no arbitrary traceback text. Where `terminal_evidence.json` cannot be written, the `last_verified_durable_state` plus this bounded console line is the complete available evidence; this specification does not claim impossible guaranteed terminal-file creation on a failed evidence medium.

---

## 15. Staging and publication architecture

REQ(v0.2). The v0.2 lane MUST distinguish three separate concerns, using the new v0.2 paths (Section 5):

```text
execution journal / operational + controlled evidence -> execution_journal_dir
scientific-result staging                             -> scientific_result_staging_dir
final scientific publication                          -> final_publication_dir
```

REQ(v0.2). The execution journal (`execution_journal_dir`, its `current_state.json`, and its `terminal_evidence.json`) MUST be usable independently of the scientific-result staging artifact. `execution_journal_dir` is established solely by the single atomic arming-directory rename of Section 9 and is never created by a separate mkdir or by a copy-and-delete promotion. Durable controlled and operational evidence MUST be writable even when `scientific_result_staging_dir` was never created or its promotion failed. A controlled invalid outcome (exit 3) MUST produce durable terminal evidence in `execution_journal_dir` and MUST NOT produce the three-file scientific bundle.

REQ(v0.2). A successfully promoted scientific result (exit 0 or exit 1) MUST publish exactly the three reserved final files into `final_publication_dir`:

```text
independent_order_sensitive_synthetic_validation_v0_2_result.json
independent_order_sensitive_synthetic_validation_v0_2_execution_envelope.json
independent_order_sensitive_synthetic_validation_v0_2_summary.txt
```

REQ(v0.2). Scientific publication MUST follow an exclusive-staging and atomic-promotion sequence: exclusive creation of `scientific_result_staging_dir`; confirm empty; write exactly the three files; close and re-read; verify exact bytes and SHA-256; verify the exact file set; atomically promote staging to `final_publication_dir`; mark published only after promotion. Existing `scientific_result_staging_dir` or existing `final_publication_dir` MUST cause a pre-contact refusal (their absence is a Section 8 pre-contact check). No overwrite, merge, append, or destructive rollback of promoted evidence is permitted; a partial staging set is failure evidence, never a permitted successful file set.

REQ(v0.2). No v0.2 operation may touch, inspect, reuse, promote into, or clean:

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

---

## 16. Schema-faithful bounded-test requirements

REQ(v0.2). The eventual v0.2 tests MUST NOT read, hash, import, parse, or evaluate the real frozen manifest, MUST NOT run the authoritative CLI against the real manifest, MUST NOT create the v0.2 journal/staging/final repository paths (bounded-test output goes to operating-system temporary directories), and MUST NOT contact the v0.1 artifacts or retained staging.

REQ(v0.2). An independent test oracle is required. The tests MUST NOT rely solely on the runner and tests importing one runner-owned contract. Specifically:

```text
tests MUST assert the normative literal fixed-fixture keys:
  binary_H0
  binary_H1

tests MUST assert the normative literal accepted-fixture keys:
  binary_A
  binary_B

tests MUST verify parity between the v0.2 schema-contract module and the authoritative frozen
  fixture-generation/verifier/freeze source (the Section 6 providers)

the runner MUST consume the independently owned schema-contract module (Section 5)

the runner MUST NOT define or override its own competing fixture-key constants

AST or direct-source boundary checks MUST reject runner-owned schema invention or alternate
  field aliases
```

The independent schema oracle (the schema-contract module) MUST be owned outside the runner and MUST be derivable without real-manifest access. The tests remain forbidden from reading, hashing, parsing, or evaluating the real frozen manifest.

REQ(v0.2). The v0.2 tests MUST use schema-faithful injected fixtures and MUST cover at least:

```text
canonical fixed fixture using binary_H0 / binary_H1
accepted fixtures using binary_A / binary_B
missing fixed-fixture field
unexpected fixed-fixture field
field-order violation where order is contractual
malformed fixed binary
non-binary fixed value
wrong fixed binary length
missing accepted-fixture field
unexpected accepted-fixture field
malformed accepted binary
accepted fixture count not equal to 8
pre-contact refusal with zero manifest contact
evidence-arming failure (pre-consumption)
contact-arm promotion failure (pre-consumption)
arming path is a directory
current_state.json is fully verified before promotion
journal directory does not exist before promotion
promotion is one same-filesystem atomic directory rename
no separate journal-directory creation
no file-only move into a pre-created journal directory
rename failure leaves authority unconsumed
rename success makes CONTACT_ARMED the first authoritative journal state
no manifest contact before rename success
no rollback or retry after rename success
contact-attempt counter incremented before open/read
read-success counter incremented only after complete read
manifest-read failure after consumption (attempt >= 1, success possibly 0)
post-contact schema invalidity -> controlled INVALID_POST_CONTACT, exit 3, no scientific publication
post-contact identity invalidity -> controlled invalid, exit 3
post-contact implementation exception routing -> exit 4
scientific evaluation not reached after validation failure
both-pass independent full validation; pass 2 reuses no pass-1 object
maximum two attempts and two successful reads; third prohibited
durable current_state.json atomic replacement
immutable terminal_evidence.json exclusive-once creation and payload-digest verification
evidence-update failure after consumption -> exit 4, last_verified_durable_state + bounded console line
staging write failure
staging verification failure
promotion failure
final verification failure
no generic UNAUTHORIZED_EXECUTION after consumption
no v0.1 path contact
no production-kernel contact
no live service or memory-system contact
```

REQ(v0.2). The v0.2 tests MUST derive all fixture builders from the single schema-contract module — the one source of truth for the canonical fixed-fixture field names (`binary_H0`/`binary_H1`), the accepted-fixture field names (`binary_A`/`binary_B`), and their structure — rather than independently inventing field names, and MUST additionally assert the literal key names above so a corrupted contract cannot silently pass. This closes the v0.1 test-fidelity gap in which `_make_manifest()` mirrored the runner's wrong keys.

---

## 17. Identity and authorization chain

REQ(v0.2). No v0.1 authority, identity binding, or execution permission carries forward. The v0.2 lane requires, in order:

```text
1. accepted correction specification (this document, once accepted)
2. new implementation-authorization document
3. new runner, runner-test, and schema-contract module implementation (exactly the v0.2 allowlist)
4. bounded test execution (non-authoritative; no real-manifest contact)
5. direct source review
6. adversarial implementation review
7. binding of new runner / test / schema-contract / configuration identities
8. new execution-authorization document
9. latest-commit authorization binding (non-circular execution-HEAD rule)
10. final pre-contact review
11. separate explicit Hilmir execution order
```

REQ(v0.2). New v0.2 identities are unbound at the time of this specification:

```text
v0.2 runner Git-blob identity                 = UNBOUND (to-be-bound at implementation review)
v0.2 runner raw SHA-256 identity              = UNBOUND (to-be-bound at implementation review)
v0.2 runner-test Git-blob identity            = UNBOUND (to-be-bound at implementation review)
v0.2 runner-test raw SHA-256 identity         = UNBOUND (to-be-bound at implementation review)
v0.2 schema-contract module Git-blob identity = UNBOUND (to-be-bound at implementation review)
v0.2 schema-contract module raw SHA-256       = UNBOUND (to-be-bound at implementation review)
v0.2 configuration identity                   = UNBOUND (to-be-bound at implementation review)
```

REQ(v0.2). These identities MUST be calculated and bound only during the later implementation review and bound into the later v0.2 execution-authorization document; this specification MUST NOT fabricate them. The v0.2 runner MUST reuse the frozen, unchanged Stage S2 descriptor and its test, and MUST bind the frozen Stage S1 manifest identities and the frozen descriptor/descriptor-test identities exactly as recorded in the governing frozen documents; this document does not restate, recompute, or alter those existing frozen hash values. The frozen schema-provider sources named in Section 6 MUST be identity-bound as the parity target for the schema-contract module during implementation review.

---

## 18. Implementation authorization prerequisites

REQ(v0.2). Implementation of the v0.2 runner, runner-test, and schema-contract module MUST NOT begin until a separate v0.2 implementation-authorization document is drafted, reviewed, and committed. That implementation-authorization document MUST:

```text
bind the exact v0.2 runner, runner-test, and schema-contract module allowlist paths
forbid modification of the frozen descriptor, descriptor-test, manifest, and all v0.1 artifacts
forbid real-manifest contact during implementation and bounded testing
require the canonical schema of Section 6 (top-level, fixed-fixture binary_H0/H1, accepted-fixture binary_A/B)
require the independent schema-contract module and the test oracle of Section 16
require the split attempt/read-success contact counters and per-pass phases of Sections 9, 11
require the atomic arming-directory-rename consumption operation (one same-filesystem rename; journal directory never separately created) of Sections 5, 9
require the exit-code, controlled-invalid, and failure-taxonomy contracts of Sections 12, 13, 14
require the durable current_state.json / terminal_evidence.json evidence architecture of Sections 14, 15
require the evidence-update-failure fallback of Section 14
defer execution and manifest contact to a separate v0.2 execution authorization
```

REQ(v0.2). Because the complete canonical schema is derivable from the frozen sources (Section 6), implementation authorization is NOT blocked on schema discovery. It remains gated only on the normal chain above, including review and identity-binding of the schema-contract module against the frozen providers. Execution and real-manifest contact MUST NOT be authorized by the implementation-authorization document; execution authority requires a separate v0.2 execution-authorization document, its non-circular authorization-HEAD binding, a final pre-contact review, and a separate explicit Hilmir execution order (Section 17). Acceptance of this specification advances none of these.

---

## 19. Explicit prohibitions

REQ(v0.2). The v0.2 lane SHALL NOT, at any stage:

```text
edit, repair, reuse, clean, delete, rename, reconstruct, or execute any v0.1 artifact
touch, inspect, reuse, promote into, or clean the v0.1 retained staging directory
silently clean and retry, or reuse a retained pre-consumption arming artifact
modify, regenerate, normalize, or re-hash the frozen Stage S1 manifest
recompute any hash to revise, replace, normalize, or newly bind a historical identity
rerun the Stage S1 fixture freezer
modify the frozen Stage S2 descriptor or its test
modify the frozen Section 6 schema-provider sources
rename, rewrite, remap, alias, or normalize any frozen manifest field
define runner-owned competing fixture-key constants or field aliases
tune, relax, sample, aggregate, or otherwise weaken the scientific gate
alter fixture membership, order, or the accepted count of 8
reinterpret, rescue, strengthen, or revive the strong-order hypothesis
store SYNTHETIC_GATE_INVALID as a scientific_result_kind or publish it as a scientific result
produce the three-file scientific bundle for a controlled invalid (exit 3) outcome
serialize UNAUTHORIZED_EXECUTION (or any refusal-class label) as a post-consumption terminal status
serialize arbitrary traceback text into evidence
claim guaranteed terminal-evidence-file creation on a failed evidence medium
invent, recalculate, normalize, or alter any existing hash or Git-blob identity
fabricate any v0.2 hash before implementation review
authorize implementation, execution, or manifest contact
```

REQ(v0.2). Permanent production boundary. The v0.2 lane SHALL NOT modify, integrate with, or contact:

```text
torment_service/kernel/
production memory behavior
live service / runtime behavior
prompt surfaces
action surfaces
autonomy surfaces
live ingestion
historical F3
PsiTRS
prerecorded challenger bridges
```

Everything in the v0.2 lane remains quarantined under:

```text
research/brainvision/
docs/
```

Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated, and MUST NOT be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route. The v0.2 lane does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

---

## 20. Acceptance checklist

REQ(v0.2). This specification is acceptable only if all of the following hold:

```text
[ ] docs-only, non-executing, non-authorizing, version-separated from v0.1
[ ] opening status and closing verdict both READY_FOR_ADVERSARIAL_REVIEW
[ ] v0.1 runner, test, S3B execution authorization, failure findings, and retained staging preserved unaltered
[ ] frozen Stage S1 manifest, Stage S2 descriptor, and Section 6 schema-provider sources preserved unaltered; freezer not rerun
[ ] exact operational correction limited to fixed-fixture binary_H0 / binary_H1 consumption
[ ] accepted-fixture binary_A / binary_B contract unchanged; no frozen manifest field renamed or aliased
[ ] scientific gate unchanged; 8-of-8 required; 7-of-8 is a scientific failure; no weakening
[ ] STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY, FORMAL_HOLD, Mode_0 preserved
[ ] contact accounting split into manifest_contact_attempt_count and manifest_read_success_count
[ ] attempt incremented before each open/read; success only after complete read; both <= 2; success <= attempt
[ ] per-pass phases MANIFEST_CONTACT_STARTED / READ_SUCCEEDED / VALIDATING / VALIDATED / SCIENTIFIC_EVALUATING for pass 1 and pass 2
[ ] execution_arming_path is a complete temporary directory, distinct from and outside execution_journal_dir
[ ] verified CONTACT_ARMED current_state.json exists inside the arming directory before promotion
[ ] one same-filesystem atomic directory rename creates execution_journal_dir
[ ] successful rename is the exact authority-consumption point; no rollback/retry/reuse after
[ ] no multi-operation journal creation/promotion sequence is permitted (no mkdir, file-move, or copy-and-delete)
[ ] EVIDENCE_ARMING_FAILED and CONTACT_ARM_PROMOTION_FAILED both exit 2, authority unconsumed
[ ] SYNTHETIC_GATE_INVALID is a controlled outcome (exit 3), never a scientific result, never a three-file publication
[ ] controlled-invalid fields: controlled_outcome_available=true, scientific_result_available=false, scientific_result_kind=null, terminal_status=INVALID_POST_CONTACT
[ ] four artifact concepts: arming_path, journal_dir, current_state.json (atomic replace), terminal_evidence.json (exclusive-once, immutable)
[ ] no file both atomically replaced and collision-refused for every update
[ ] terminal_evidence.json uses {payload, payload_sha256} with digest over payload bytes only
[ ] EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION defined (exit 4) with last_verified_durable_state + bounded console fallback; no impossible-guarantee claim
[ ] distinct exit codes 0/1/2/3/4/5 as specified; consumed failure never resembles unconsumed refusal
[ ] complete canonical schema enumerated and authoritative frozen source paths named (Section 6)
[ ] independent schema-contract module owned outside runner; tests assert literal keys and verify parity; AST boundary rejects runner-owned schema
[ ] both passes fully validate independently; pass 2 reuses no pass-1 object; pass 2 not attempted if pass 1 fails pre-evaluation
[ ] re-hash prohibition clarified (revise/rebind forbidden; observed-vs-expected comparison permitted only after authorized contact)
[ ] identity/authority chain requires new implementation authorization and new execution authorization; no v0.1 authority carries forward
[ ] all new v0.2 identities labelled UNBOUND / to-be-bound; no fabricated hashes
[ ] permanent production/kernel/service/memory/F3/PsiTRS/prerecorded/live-ingestion boundary preserved
[ ] closing verdict withholds implementation, execution, and manifest-contact authority
```

---

## Specification verdict

```text
SPECIFICATION_STATUS = READY_FOR_ADVERSARIAL_REVIEW
IMPLEMENTATION_AUTHORIZED = False
EXECUTION_AUTHORIZED = False
REAL_MANIFEST_CONTACT_AUTHORIZED = False
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation v0.2 Correction Specification v0.1 (revised to resolve the Codex ACCEPT_WITH_REQUIRED_CORRECTIONS verdict). Docs-only, non-executing, non-authorizing, version-separated from v0.1, offline, quarantined, non-production, non-service, non-kernel. Splits manifest contact accounting into manifest_contact_attempt_count (incremented before each open/read) and manifest_read_success_count (incremented only after a complete read), with per-pass phases and the invariants success <= attempt <= 2. Separates the pre-consumption temporary arming directory (holding a verified CONTACT_ARMED current_state.json) from the consumed execution-journal directory, which is established by one atomic same-filesystem directory rename of the arming directory — the exact authority-consumption point; adds EVIDENCE_ARMING_FAILED and CONTACT_ARM_PROMOTION_FAILED (exit 2, unconsumed). Makes SYNTHETIC_GATE_INVALID a controlled post-contact outcome (exit 3, durable terminal evidence, no three-file scientific publication), never a scientific result. Defines four distinct artifacts — arming_path, journal_dir, atomically-replaced current_state.json, and exclusively-created immutable terminal_evidence.json with a {payload, payload_sha256} digest over payload bytes only — and adds EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION (exit 4) with a last_verified_durable_state and a bounded console fallback, without claiming impossible guaranteed terminal-file creation. Enumerates the complete canonical manifest schema from the frozen freeze library, verifier, and freeze-runner configuration (named as the authoritative sources; identities bound at implementation review) and requires an independent, runner-external schema-contract module with literal-key test assertions, parity verification, and AST boundary enforcement. Requires full independent post-contact validation for both passes with pass 2 reusing no pass-1 object. The preregistered scientific gate is unchanged and no threshold, membership, or hypothesis is weakened. All v0.1 artifacts, the retained empty v0.1 staging directory, the frozen Stage S1 manifest, the frozen Stage S2 descriptor, and the Section 6 schema-provider sources remain unaltered; the freezer is not rerun. No hash is invented, recalculated, or altered, and every new v0.2 identity is explicitly unbound pending a separate implementation review and a separate execution authorization. This document performs no Git operation, implements no file, contacts no real manifest, and confers no implementation, execution, or manifest-contact authority. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted; Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated.*
