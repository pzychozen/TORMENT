# TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Execution Failure Findings v0.1

## Document status

```text
document_type = docs-only findings record
findings_version = v0.1
records = one consumed, non-scientific Stage S3B v0.1 execution failure
execution_authorized = False (the single one-run authority is consumed; no rerun is authorized)
implementation_change = none (no source, test, manifest, result, staging, or authorization file is modified by this record)
```

Authoritative repository baseline:

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch = main
execution HEAD = fab3fdc892eff1fc2ee7b1fbf3113df4bd922d0a
execution HEAD subject = docs(research): authorize synthetic validation execution
Python = 3.11.15
working tree = clean
HEAD = origin/main
```

This document records the outcome of the single authorized Stage S3B v0.1 synthetic-validation invocation. That invocation consumed the one-run authority at the frozen consumption threshold and then failed on an implementation defect before any scientific evaluation occurred. This is a findings record only. It authorizes nothing, opens no successor, implements no change, and produces no new evidence beyond this record. Throughout, directly observed evidence, source-proven control-flow facts, and high-confidence forensic reconstruction are labelled distinctly (Section 4). No scientific result, descriptor conclusion, or order-sensitivity claim follows from it.

---

## 0. Disposition

```text
A. THE STAGE S3B v0.1 SYNTHETIC-VALIDATION INVOCATION WAS ATTEMPTED, CONSUMED THE
   ONE-RUN AUTHORITY AT THE FROZEN CONSUMPTION THRESHOLD, AND THEN FAILED
   POST-CONTACT ON A FIXED-FIXTURE KEY MISMATCH BEFORE ANY DESCRIPTOR CALL. NO
   SCIENTIFIC RESULT WAS PRODUCED. NO FINAL EVIDENCE WAS PUBLISHED. AN EMPTY
   STAGING DIRECTORY IS RETAINED. THE ONE-RUN AUTHORITY IS PERMANENTLY CONSUMED.
   NO RERUN IS PERMITTED.
```

The retained staging directory proves that the pre-contact phase completed far enough for exclusive staging creation. The frozen control flow then crosses the authority-consumption threshold before opening the real manifest: `mark_manifest_read()` sets `authority_consumed = true` and `manifest_contact_count = 1`. Source review reconstructs with high confidence that the manifest read and validation completed and that the invocation then failed on the first fixed-fixture access, `fixed_fixture["binary_A"]`, before any descriptor call. No traceback was retained; this is the strongest source-supported reconstruction and no better alternative was found.

The observed exit code `2` is recorded truthfully and is not rewritten. The actual execution phase was post-contact and the actual authority state is classified as consumed; the exit-code appearance is a masking defect, documented in Section 9.

Permanent posture is preserved:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

---

## 1. Governing documents and authority

This findings record is governed by the independent order-sensitive challenger-branch documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
```

The Stage S3B execution authorization was the operation's authority. Its single one-run capability is now consumed. This record adds no authority to any governing document, does not amend the S3B execution authorization, and does not modify the frozen runner, tests, descriptor, manifest, or retained staging evidence.

---

## 2. Authoritative execution identity

The sole authorized invocation, from the repository root, was:

```cmd
python research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
```

Invocation timing:

```text
RUN_START_DATE = Wed 07/22/2026
RUN_START_TIME = 11:57:23.24
RUN_END_DATE = Wed 07/22/2026
RUN_END_TIME = 11:57:23.77
```

Observed console outcome:

```text
SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION
```

Captured process exit:

```text
RUN_EXIT = 2
```

The process exit code was captured immediately after the single invocation, before any other command. No CLI arguments, options, flags, configuration paths, identity overrides, or non-empty stdin were supplied. The runner accepts no environment variable as an identity or configuration override. The elapsed wall-clock time was approximately 0.53 seconds — a short execution shape consistent with a failure at the fixed-fixture boundary and before any descriptor computation, not with a completed gate.

---

## 3. Retained filesystem evidence

The post-invocation filesystem state was directly observed as:

```text
final publication path = absent
staging path = present
staging file count = 0
staging byte count = 0
working tree = clean
HEAD = origin/main
```

Retained staging path:

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

The runner created its exclusive staging directory during the run but never wrote, closed, verified, or promoted any output file, because the failure occurred before the gate produced any publishable bundle. The final publication directory was therefore never created. The empty staging directory is the durable filesystem trace that a consuming invocation occurred.

The retained staging directory must not be deleted, renamed, populated, cleaned, or reused. It is preserved intact as consumed-run evidence. It must not be repurposed as staging for any future run.

---

## 4. Evidence classes and epistemic status

This record separates three classes of evidence and labels every downstream claim accordingly.

Directly observed during and after the single invocation:

```text
the command was invoked once
start and end timestamps were captured
stderr was:
SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION
process exit was 2
final publication path was absent
staging path was present
staging contained 0 files and 0 bytes
the repository remained clean
```

Proven directly by review of the frozen committed source set:

```text
staging creation occurs only after pre-contact checks return no failures
staging is created before authoritative_manifest_read()
authoritative_manifest_read() calls mark_manifest_read() before opening the manifest
mark_manifest_read() sets authority_consumed = true and increments manifest_contact_count
manifest validation occurs after the manifest read
_run_single_pass() follows successful manifest validation
the canonical fixed fixture uses binary_H0 and binary_H1
run_fixed_positive() first attempts fixed_fixture["binary_A"]
main() catches uncaught Exception and returns exit 2 with refusal-style stderr
```

High-confidence forensic reconstruction. The detailed live failure chain — that the run actually crossed the consumption threshold, read and validated the manifest, entered `_run_single_pass()`, and raised `KeyError("binary_A")` at the first fixed-fixture access before any descriptor call — is a high-confidence forensic reconstruction supported by the frozen source, the retained empty staging directory, the short elapsed execution shape, the confirmed schema contradiction, and the absence of a better source-supported alternative. No traceback or persisted in-process execution-state record was retained.

---

## 5. High-confidence source-supported reconstruction of the consuming path

The consuming path is reconstructed as:

```text
pre-contact checks pass
exclusive empty staging directory is created
authoritative_manifest_read() is entered
ExecutionState.mark_manifest_read() sets:
    manifest_contact_count = 1
    authority_consumed = true
the real manifest bytes are read
manifest validation completes
_run_single_pass() begins
fixed_fixture["binary_A"] raises KeyError
```

The staging creation and the source ordering are proven directly from the frozen runner. The post-staging live steps are reconstructed from that frozen ordering, the observed empty staging state, the confirmed schema mismatch, and the masked exit shape. No traceback or persisted in-process state was available.

By the frozen ordering, the one-run consumption threshold — `mark_manifest_read()`, called at the entry of `authoritative_manifest_read()` before the manifest file is opened — is crossed as soon as the consuming path is entered, setting `manifest_contact_count = 1` and `authority_consumed = true`. The reconstruction places the `KeyError` strictly after that threshold, during `_run_single_pass()`. The authority classification is therefore:

```text
authority_consumed = true
manifest_contact_count = 1
```

Because the retained staging and the frozen ordering place the failure at or beyond the consumption threshold, the single scientific authority is classified as consumed. The Stage S3B v0.1 invocation may never be retried, rerun, resumed, replaced, or continued. Manifest contact is classified as reaching count 1 and stopping there; the reconstructed failure falls within the first pass, so the second (pass-2) manifest read never occurred.

---

## 6. Root-cause forensic finding — fixed-fixture key mismatch

The confirmed source-level cause is a fixed-fixture field-name mismatch between the frozen fixture infrastructure and the v0.1 validation runner.

Canonical fixed-fixture fields emitted by the frozen fixture infrastructure:

```text
binary_H0
binary_H1
```

Fields incorrectly expected by the v0.1 validation runner:

```text
binary_A
binary_B
```

Affected runner paths:

```text
run_fixed_positive()
_run_single_pass()
```

The runner attempts its first fixed-fixture access before making any descriptor call. The high-confidence reconstructed uncaught exception is:

```text
KeyError("binary_A")
```

The frozen manifest's fixed fixture stores its two member sequences under the canonical keys `binary_H0` and `binary_H1`. The v0.1 runner's fixed-positive path indexes the fixed fixture with `binary_A` and `binary_B`, which are the accepted-fixture key names, not the fixed-fixture key names. The first such access, `fixed_fixture["binary_A"]`, is the reconstructed immediate cause: it raises `KeyError("binary_A")` before the descriptor is ever invoked on the fixed fixture. The defect is a naming/contract error in the runner, not a fixture, manifest, descriptor, or scientific defect.

The fixed-fixture schema contradiction itself is directly confirmed from the frozen source. The occurrence of that exact exception in the live process is a forensic reconstruction rather than a retained traceback fact.

---

## 7. Manifest-validation coverage gap

Under the frozen v0.1 control flow, `validate_manifest_bytes()`:

```text
verifies only that fixed_fixture is a dictionary
does not validate the canonical fixed-fixture key set
does not verify binary_H0 or binary_H1
validates binary_A and binary_B only for accepted_fixtures
```

The relevant phases are distinct:

```text
pre-contact =
repository, authorization, source identity, path, CLI, stdin, and publication-path checks

post-contact validation =
real manifest hashing, parsing, identity validation, family checks,
and fixed-fixture / accepted-fixture schema validation
```

Manifest validation runs after authority consumption and after the manifest read; it is a post-contact step, not a pre-contact check. Because that post-contact validation checked only that the fixed fixture was a dictionary and validated the `binary_A` / `binary_B` shape solely for the accepted fixtures, the fixed-fixture mismatch was not caught during post-contact manifest validation before the scientific pass began, and it surfaced instead as an uncaught runtime exception once `_run_single_pass()` indexed the fixed fixture.

Complete fixed-fixture validation would have converted the schema mismatch into a controlled post-contact `SYNTHETIC_GATE_INVALID` outcome with process exit `3`, rather than an uncaught exception. Under the frozen v0.1 control flow, that early invalid outcome still would not have produced canonical three-file publication, because it returns before artifact construction and publication; the staging directory would remain retained.

---

## 8. Bounded-test coverage gap

The bounded test helper `_make_manifest()` constructed its synthetic fixed fixture using:

```text
binary_A
binary_B
```

It therefore mirrored the runner's incorrect expectation instead of the canonical frozen fixed-fixture contract. The bounded tests contained no fixed-fixture coverage using:

```text
binary_H0
binary_H1
```

The bounded tests successfully proved their injected contract, but the injected contract was not schema-faithful to the frozen authoritative manifest. Because the injected fixed fixture and the runner shared the same wrong key names, the tests were mutually consistent and passed, while masking the divergence from the real fixture infrastructure. The tests validated the runner against itself rather than against the canonical fixed-fixture schema. This is a test-fidelity gap, not evidence that the runner logic downstream of the fixed-fixture access is correct or incorrect.

---

## 9. Exit-code masking defect

The runner's `main()` catches a broad `Exception` and emits:

```text
SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION
```

with process exit `2`.

Under the S3B authorization's intended exit-code contract, exit `2` denotes a pre-contact refusal with the authority unconsumed. In this invocation, the same exit `2` and the same refusal-style message were emitted for a failure that the reconstruction places after the consumption threshold. The output therefore falsely resembles a pre-contact refusal even though the reconstructed failure was post-contact.

The findings record distinguishes these truthfully:

```text
observed process exit = 2
reconstructed execution phase = post-contact
classified authority state = consumed
```

The observed exit code is not rewritten. It is recorded exactly as `2`, and the discrepancy between the observed exit code and the reconstructed post-contact, authority-consumed state is recorded as a masking defect: the broad `Exception` handler in `main()` collapses a post-contact implementation failure into the pre-contact refusal channel, suppressing the distinct post-contact failure signal and the durable post-contact failure evidence that the contract expects. A future corrected runner must not route post-contact exceptions through the pre-contact refusal exit path.

---

## 10. Scientific interpretation

Recorded exactly:

```text
SYNTHETIC_GATE_PASSED = not established
SYNTHETIC_GATE_FAILED = not established
SYNTHETIC_GATE_INVALID = not canonically published
scientific gate evaluation = not reached
descriptor evaluation = not reached
descriptor conclusion = prohibited
strong order hypothesis status = unchanged
```

The failure occurred before any descriptor call and before any gate evaluation. No malformed/degenerate control, identity control, nuisance control, fixed-positive comparison, or eight-pair comparison was evaluated. No descriptor output was produced or read.

This is not:

```text
a descriptor failure
a synthetic scientific miss
evidence against order sensitivity
evidence for order sensitivity
a valid gate result
```

The event carries no scientific content whatsoever. It is an implementation-defect failure that consumed the one-run authority without reaching the science. Nothing about the challenger descriptor, the frozen family, or Brainvision order sensitivity is established, weakened, or supported by it.

---

## 11. Findings-document classifications

```text
recorded_outcome = CONSUMED_POST_CONTACT_IMPLEMENTATION_FAILURE
scientific_result_status = NO_SCIENTIFIC_RESULT
authority_status = PERMANENTLY_CONSUMED
publication_status = NO_FINAL_PUBLICATION_EMPTY_STAGING_RETAINED
```

These are findings-document classifications, not runner-published v0.1 result kinds. The runner did not canonically publish `SYNTHETIC_GATE_PASSED`, `SYNTHETIC_GATE_FAILED`, or `SYNTHETIC_GATE_INVALID`; no final result, execution envelope, or summary was promoted. The labels above are this record's characterization of the consumed, non-scientific outcome, and they must not be read as, or reconstructed into, a canonical runner result kind.

---

## 12. Permanent Brainvision and TORMENT boundary

Preserved:

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

No production kernel, service, memory, F3, PsiTRS, prerecorded, prompt, action, autonomy, or live-ingestion contact occurred during the invocation or during preparation of this record, and none is authorized here. The event does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result. Brainvision must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route.

---

## 13. Future-work boundary

This record may recommend a separately specified v0.2 correction lane, but it does not authorize implementation or execution of any such lane, and it does not claim that a future corrected scientific run is already authorized.

Any future v0.2 must:

```text
preserve the v0.1 runner, tests, authorization, and retained staging evidence
use a new versioned runner and test path
consume the canonical fixed-fixture binary_H0/binary_H1 schema
add schema-faithful tests derived from the canonical fixture contract
distinguish pre-contact exceptions from post-contact exceptions
produce durable post-contact failure evidence
require a completely new specification and explicit execution authority
```

The fixed-fixture schema must be validated in the correct phase. Pre-contact checks cannot validate unread real-manifest contents.

Pre-contact v0.2 checks must validate:

```text
repository and branch state
authorization state
source and test identities
expected manifest-schema contract identity
expected canonical fixed-fixture field contract
CLI and stdin boundaries
publication-path absence
```

After the real manifest read, but before entering any scientific evaluation, v0.2 must validate:

```text
the complete real-manifest top-level schema
the complete canonical fixed-fixture field set
binary_H0 and binary_H1 structure and domain
all fixed-fixture certificate fields
the complete accepted-fixture field set
all accepted binary_A and binary_B structures
all frozen family and identity constraints
```

The v0.1 runner, its tests, the S3B execution authorization, and the retained empty staging directory are frozen as consumed-run evidence and must not be edited or reused to enable another attempt. A corrected effort is a new versioned artifact under new specification and new execution authority, not a continuation of v0.1. Nothing in this record grants that specification or that authority.

---

## 14. Closing state

```text
STAGE_S3B_V0_1_EXECUTION_ATTEMPTED = True
STAGE_S3B_V0_1_AUTHORITY_CONSUMED = True
STAGE_S3B_V0_1_MANIFEST_CONTACT_COUNT = 1
STAGE_S3B_V0_1_SCIENTIFIC_RESULT_AVAILABLE = False
STAGE_S3B_V0_1_FINAL_PUBLICATION_AVAILABLE = False
STAGE_S3B_V0_1_EMPTY_STAGING_RETAINED = True
STAGE_S3B_V0_1_RERUN_AUTHORIZED = False
STAGE_S3B_V0_2_SPECIFIED = False
STAGE_S3B_V0_2_IMPLEMENTATION_AUTHORIZED = False
STAGE_S3B_V0_2_EXECUTION_AUTHORIZED = False
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Execution Failure Findings v0.1. Docs-only findings record for one consumed, non-scientific Stage S3B v0.1 execution failure. Directly observed: the command was invoked once; start/end timestamps were captured; stderr was `SYNTHETIC_VALIDATION_REFUSED UNAUTHORIZED_EXECUTION`; process exit was 2; the final publication path was absent; the staging path was present with 0 files and 0 bytes; the repository remained clean. Source-proven: staging is created only after pre-contact checks pass and before `authoritative_manifest_read()`, which calls `mark_manifest_read()` — setting `authority_consumed = true` and incrementing `manifest_contact_count` — before opening the manifest; manifest validation is a post-contact step; the canonical fixed fixture uses `binary_H0`/`binary_H1` while `run_fixed_positive()` first indexes `fixed_fixture["binary_A"]`; and `main()` catches uncaught `Exception` and returns exit 2 with refusal-style stderr. High-confidence reconstruction: the retained empty staging directory directly proves the invocation passed the pre-contact phase far enough to create exclusive staging; the frozen source proves the next consuming path marks authority consumed before opening the real manifest; the confirmed `binary_H0`/`binary_H1` versus `binary_A`/`binary_B` contradiction, combined with the masked exit-2 handler and the absence of any better source-supported alternative, supports the high-confidence reconstruction that the invocation failed at `fixed_fixture["binary_A"]` before any descriptor call. No traceback was retained, so the exact `KeyError("binary_A")` is recorded as the source-supported reconstructed cause, not as directly captured process output. Manifest validation is post-contact; a detected fixed-fixture mismatch would have yielded a controlled `SYNTHETIC_GATE_INVALID` outcome with exit 3, which under the frozen v0.1 control flow still would not have produced canonical three-file publication. The one-run authority is classified as permanently consumed (`manifest_contact_count = 1`); no rerun, retry, resume, replacement, or continuation is authorized. No scientific gate or descriptor evaluation was reached and no descriptor conclusion is permitted; the strong order hypothesis status is unchanged. Recorded outcome CONSUMED_POST_CONTACT_IMPLEMENTATION_FAILURE, NO_SCIENTIFIC_RESULT, PERMANENTLY_CONSUMED, NO_FINAL_PUBLICATION_EMPTY_STAGING_RETAINED — findings-document classifications, not runner-published result kinds. The retained empty staging directory must not be deleted, renamed, populated, cleaned, or reused. A future v0.2 correction lane is neither specified, implemented, nor authorized here. No source, test, manifest, result, staging, or authorization file was modified, and no Git operation was performed. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted; Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated.*
