# TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Findings v0.1

## Document status

```text
document_type = docs-only authoritative findings record
findings_version = v0.1
records = one completed authoritative freeze execution
execution_authorized = False (the single one-run authority is consumed; no rerun is authorized)
implementation_change = none (no source, test, authorization, or evidence file is modified by this record)
```

Authoritative repository baseline:

```text
HEAD = origin/main = 6cd69122e16b9a9ad99c2abc7ddeda8dd6358fbb
working tree = clean
```

This document records the outcome of the single authoritative independent order-sensitive synthetic-fixture freeze operation. It is a findings record only. It authorizes nothing, opens no successor, and produces no new evidence; it restates the already-published canonical evidence and its identities. No scientific result or fixture-discovery claim beyond the frozen construction follows from it.

---

## 0. Disposition

```text
A. THE AUTHORITATIVE INDEPENDENT ORDER-SENSITIVE SYNTHETIC-FIXTURE FREEZE
   OPERATION COMPLETED SUCCESSFULLY. THE CANONICAL FIRST-EIGHT FIXTURE FAMILY
   IS FROZEN. THE ONE-RUN EXECUTION AUTHORITY IS CONSUMED. NO RERUN IS
   PERMITTED.
```

The descriptor-blind canonical selection procedure ran its deterministic two-pass freeze-with-replay, produced `ACCEPTED_EIGHT`, matched on replay, finalized, and promoted its evidence atomically with process exit code 0. The frozen family is a stable independent synthetic fixture family for later, separately-authorized challenger evaluation. It is not a scientific claim about Brainvision, about any challenger, or about order sensitivity.

Permanent posture is preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

---

## 1. Governing documents and authority

This findings record is governed by the independent synthetic-fixture branch documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SELF_BOUNDARY_CORRECTION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md
```

The freeze execution authorization is the operation's authority. The runner-implementation authorization remains governing for architecture, behavior, boundaries, and binding structure; the accepted self-boundary correction supersedes only the two corrected S1B identity pairs and the resulting runner identity. This record adds no authority to any of them.

---

## 2. Authoritative execution identity

The sole authoritative invocation, from the repository root, was:

```cmd
python research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

```text
repository execution HEAD = 6cd69122e16b9a9ad99c2abc7ddeda8dd6358fbb
authorization commit      = 6cd69122e16b9a9ad99c2abc7ddeda8dd6358fbb
Python                    = 3.11.15
process exit code         = 0
```

The immediate process exit code was captured before any other command and was zero. Under the frozen runner exit-code contract, `exit 0` means the atomic staging-to-final promotion succeeded for a complete canonical result. No arguments, options, flags, environment gates, or stdin were supplied; the invocation used exactly the sole permitted shape.

---

## 3. Bound source and configuration identities

The operation ran under the corrected, committed identities. Git-object identity and Windows raw-file SHA-256 identity are separate and both mandatory.

Runner

```text
artifact role = runner
path = research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = fa9d63764b68e92111386fd71f35ee339c787130
Windows raw SHA-256 = 3b62a026d9ca42d3641e02cd2c07890166267ae25a2e9d99a0213e442d549210
```

Five S1B execution identities

```text
verifier
path = research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
Git blob = 74e25002db4e45870ee20397cbc9e5416f108cb0
Windows raw SHA-256 = 15e31e50319daaf8e45704c5e3b339e876a0e2949927365928b32f5c412ba95c

generator
path = research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py
Git blob = 77bc2e319e1283ce5d00b283f99a1d1d56732d83
Windows raw SHA-256 = 001317367d5f8e3c06ae3da177901b88f94560ae555eeca54247464e2cb9ed78

freeze_library
path = research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = 9f69e3610ced5bb8f3e90986e9b12f808a78bed2
Windows raw SHA-256 = 8f934e8615c0f6b599fe00e8f6425c1bf0e13c44aa27853885b4c7546cda2cde

verifier_test
path = research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py
Git blob = 97f2605284c53dedfec43d8e65112d30418877a8
Windows raw SHA-256 = af0a798d5195e78ad2e051cc0ec2846ec82d20c8d796f448e355f77ec4d76032

generator_freeze_test
path = research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = d90a95016dcd20e49b35c6039efd46fbcde1d779
Windows raw SHA-256 = ab669740f6489dc7e726363811360d51797f9e96900cbde43082bed159b881e7
```

Configuration

```text
configuration SHA-256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
```

The published execution envelope records `python_version = 3.11.15` and `authorization_document_path = docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md`.

---

## 4. Canonical outcome

```text
pre_contact_status        = PASSED
canonical_contact_status  = PASS_2_COMPLETE
pass_1_status             = COMPLETE
pass_2_status             = COMPLETE
canonical_result_kind     = ACCEPTED_EIGHT
comparison_status         = MATCH
finalization_status       = COMPLETE
family_frozen             = true
failure_code              = null
failure_stage             = null
publication_status        = VERIFIED_FOR_PROMOTION
```

Explicit state:

```text
AUTHORITATIVE_CANONICAL_ITERATOR_CONTACTED = True
ONE_RUN_AUTHORITY_CONSUMED = True
CANONICAL_SEED_SCAN_COMPLETED = True
ACTUAL_FIRST_EIGHT_DISCOVERED = True
FAMILY_FROZEN = True
RERUN_AUTHORIZED = False
```

The promoted canonical envelope records `publication_status = VERIFIED_FOR_PROMOTION` (the frozen staged-and-promoted value; `PROMOTED` is a runtime/operator adjudication state only). Process exit code 0 independently confirms the atomic promotion succeeded. No retry, rerun, resume, or replacement execution is permitted.

---

## 5. Published artifact set and identities

A successfully promoted canonical result published exactly three files under the quarantined results directory `research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/`:

```text
independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_fixture_freeze_summary_v0_1.txt
```

Final published-manifest identities:

```text
manifest_payload_sha256 = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
external_manifest_sha256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
configuration_sha256     = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
```

Identical inner pass-bundle identities (pass 1 and pass 2 agreed exactly):

```text
pass manifest_payload_sha256  = dc43fa2836362d3e73c2121c421be732c944cb94700630bf475240beeb6d9d1e
pass external_manifest_sha256 = 00ef48224f4effaf0fbdbc7264b0676bd6bfafe168496166e9dcca578ddbd942
```

The pass-bundle hashes and the final published-manifest hashes differ legitimately. Each pass bundle is the candidate family and its search diagnostics as constructed within that pass. The final published manifest additionally binds the authoritative source identities, the configuration identity, the validation record, and the publication identity fields, so it is a strict superset of the pass-bundle content and therefore hashes differently. The difference is by construction, not a discrepancy: both passes produced the same pass-bundle bytes, and the single final manifest wraps that agreed content with authoritative provenance.

---

## 6. Search accounting

```text
total_seeds_visited      = 2148
accepted count           = 8
rejected count           = 2140
eligible_duplicate_count = 0

accepted_seed_order_positions = 2140, 2141, 2142, 2143, 2144, 2145, 2146, 2147
terminal_seed_tuple           = [1,3,4,16]
terminal_status               = ACCEPTED_EIGHT
```

Rejection counts (canonical order):

```text
A_CARDINALITY_NOT_9          = 543
B_CARDINALITY_NOT_9          = 0
IDENTICAL_SUPPORTS           = 28
A2_MISMATCH                  = 0
TRANSITION_TABLE_MISMATCH    = 0
AFFINE_EQUIVALENT            = 1569
AFFINE_COMPLEMENT_EQUIVALENT = 0
TRIPLE_ARRAY_EQUAL           = 0
```

Accounting closes exactly:

```text
543 + 28 + 1569 = 2140 rejected
2140 rejected + 8 accepted = 2148 visited
```

The scan is descriptor-blind and stopped immediately after the eighth acceptance at seed position 2147; the terminal seed tuple `[1,3,4,16]` is the eighth accepted seed.

---

## 7. Frozen family

The eight accepted members in canonical (acceptance) order:

```text
family_index 0: seed_order_position = 2140  seed_tuple = [1,3,4,9]
family_index 1: seed_order_position = 2141  seed_tuple = [1,3,4,10]
family_index 2: seed_order_position = 2142  seed_tuple = [1,3,4,11]
family_index 3: seed_order_position = 2143  seed_tuple = [1,3,4,12]
family_index 4: seed_order_position = 2144  seed_tuple = [1,3,4,13]
family_index 5: seed_order_position = 2145  seed_tuple = [1,3,4,14]
family_index 6: seed_order_position = 2146  seed_tuple = [1,3,4,15]
family_index 7: seed_order_position = 2147  seed_tuple = [1,3,4,16]
```

All eight share the same construction shape:

```text
C = [0,1,3]
D = [0,4,d2]     with d2 = 9 through 16
weight_A = weight_B = 9
transition_table_A = transition_table_B = [[50,5],[5,4]]
affine equivalent = false
affine-complement equivalent = false
triple disagreement count > 0
```

Triple-disagreement counts in family order:

```text
168, 180, 192, 264, 276, 288, 300, 300
```

Each accepted pair has matching second-order autocorrelation and matching transition-table information but differs at third order (nonzero triple disagreement), while remaining outside the tested affine and affine-complement equivalence classes. That is: the two members of each pair are second-order-indistinguishable under the tested statistics yet third-order-distinct, which is exactly the order-sensitive property the construction is designed to witness — as a fixed construction, not as a claim about any external system.

---

## 8. Replay and publication

Two fully fresh authoritative passes independently visited the same 2148 seeds, accepted the same eight fixtures in the same order, produced identical pass bundles, and ended at the same terminal seed. The exact comparison reported:

```text
matches = true
mismatch_reasons = []
```

Publication completed through the frozen exclusive-staging and atomic-promotion path: the staging directory was created exclusively, the outcome-specific files were written, closed, re-read, and byte/SHA-256 verified, the exact file set was confirmed, and the staging directory was atomically renamed to the final directory. The staging directory is absent (promoted); the three canonical files are present.

---

## 9. Scientific interpretation

Restrained interpretation. What this establishes:

```text
The descriptor-blind canonical selection procedure successfully produced
and froze the first eight unique eligible N=64 synthetic order-sensitive
pairs under the predetermined construction, eligibility, duplicate, and
replay rules.
```

This establishes a stable independent synthetic fixture family suitable for later challenger evaluation.

It does not establish:

```text
that any challenger detects the family
that Brainvision possesses strong order sensitivity
that the family is representative of all eligible constructions
that the family is diversity-optimized
that the frozen historical F3 claim is repaired
that the strong order hypothesis is supported
```

Structural observation. The first eight eligible pairs form a narrow consecutive construction sequence: C remains [0,1,3], while the final D coordinate advances from 9 through 16. This is an honest consequence of the frozen canonical first-eight selection rule (lexicographic seed enumeration with stop-after-eighth), not a defect and not a post-selection choice. The rule takes the first eight eligible pairs in canonical order; those happen to be consecutive, and the record states that plainly rather than reframing it.

This family is described as the:

```text
canonical first-eight fixture family
```

It is not described as representative, diverse, optimized, challenger-balanced, or best-performing. No such property was measured, selected for, or claimed.

---

## 10. Authority state after execution

```text
AUTHORITATIVE_CANONICAL_ITERATOR_CONTACTED = True
ONE_RUN_AUTHORITY_CONSUMED = True
CANONICAL_SEED_SCAN_COMPLETED = True
ACTUAL_FIRST_EIGHT_DISCOVERED = True
FAMILY_FROZEN = True
RERUN_AUTHORIZED = False

CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_EVALUATION_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

The one-run authority was consumed at the first real canonical-iterator contact in authoritative pass 1 and remains consumed. No rerun, retry, resume, recovery execution, third pass, replacement scan, or repeated publication is authorized. A new run would require a separately reviewed and explicitly approved future decision, which this record does not provide.

---

## 11. Permanent Brainvision and TORMENT boundary

Preserved permanently:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains:

```text
offline
quarantined
non-production
non-service
non-kernel
non-memory-integrated
```

This synthetic-fixture operation is independent descriptor-blind research infrastructure. It does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result. Brainvision must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route. No contact occurred with `torment_service/kernel/`, `research/brainvision/results/results.csv`, `research/brainvision/results/results.json`, PsiTRS, historical retained F3 evidence, future challenger implementations, or production memory-system functionality, and none is authorized here.

---

## 12. Next-state recommendation

The freezer execution phase is closed. The one-run authority is permanently consumed; the freezer is not to be rerun.

The recommended next step is a separate docs-first decision about the exact challenger-evaluation contract against the frozen family. That later decision must preserve:

```text
no fixture replacement
no family reselection
no challenger-informed selection
no rerun of the freezer
no historical retained F3 contact unless separately authorized
no production-kernel or memory-system contact
```

This findings document does not authorize or implement challenger execution. It records completion only.

---

## 13. Final disposition

```text
A. THE AUTHORITATIVE FREEZE IS COMPLETE AND SUCCESSFUL. THE CANONICAL FIRST-EIGHT
   FIXTURE FAMILY IS FROZEN AND ITS EVIDENCE IS PROMOTED AND BYTE-STABLE.
   THE ONE-RUN AUTHORITY IS CONSUMED. RERUN, CHALLENGER EXECUTION, F3 CONTACT,
   PSITRS CONTACT, AND PRODUCTION/MEMORY/KERNEL INTEGRATION REMAIN CLOSED.
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Findings v0.1. Docs-only findings record. Restates already-published canonical evidence for one completed authoritative freeze (exit 0, ACCEPTED_EIGHT, replay MATCH, family_frozen=true, publication VERIFIED_FOR_PROMOTION). Establishes only that the descriptor-blind canonical procedure froze the first eight eligible pairs under predetermined rules; it establishes no challenger detection, no order-sensitivity claim about Brainvision, and no repair of the frozen F3 result. The freezer is not rerun, no source/test/authorization/evidence file is modified, and no Git operation is performed. FORMAL_HOLD and Mode_0 remain active.*
