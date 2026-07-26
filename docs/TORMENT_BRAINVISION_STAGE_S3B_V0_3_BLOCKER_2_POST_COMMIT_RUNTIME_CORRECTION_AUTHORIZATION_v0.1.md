# TORMENT Brainvision Stage S3B v0.3
# BLOCKER-2 Post-Commit Runtime Correction Authorization v0.1

## 0. Document Status

This is a post-commit authorization document for a narrow runtime correction only.

It is docs-only. It does not modify implementation code, tests, validation runners, gates, retained artifacts, native rename cases, or production integration. It does not execute an authoritative retained run.

The only authorized follow-on work described here is a later narrow code change that corrects the retained single-run runtime so that an execution authorization can be identity-bound, globally one-shot, locally gated, and truthfully completed after the already committed retained-run preparation work.

## 1. Authorization Question

Should the repository authorize a narrow post-commit runtime correction before any authoritative retained single-run execution is allowed?

Answer: yes.

The retained-run preparation is present, but the committed readiness assessment identifies runtime blockers that prevent execution authorization. This document authorizes only the correction of those blockers. It does not authorize the retained run itself.

## 2. Authoritative Baseline

The baseline for this authorization is:

```text
branch = "main"
head = "0503f1c970cc248b66b02c600d2d8f12aa77feef"
origin_main = "0503f1c970cc248b66b02c600d2d8f12aa77feef"
assessment_commit = "0503f1c970cc248b66b02c600d2d8f12aa77feef"
assessment_subject = "docs(research): assess blocker 2 retained runtime readiness"
```

The controlling runtime-preparation commit is:

```text
retained_preparation_commit = "e144752"
retained_preparation_subject = "research(brainvision): implement blocker 2 retained-run preparation"
```

The controlling earlier authorization commit is:

```text
retained_preparation_authorization_commit = "4a9d58a"
retained_preparation_authorization_subject = "docs(research): authorize blocker 2 retained-run preparation"
```

## 3. Preserved Boundaries

This authorization preserves all committed boundaries:

- BLOCKER-2 remains OPEN.
- BLOCKER-4 remains not started.
- Production integration remains unauthorized.
- No retained authoritative run is authorized by this document.
- No retained authoritative run is executed by this document.
- No gate is created, consumed, repaired, released, replayed, or deleted by this document.
- No native same-volume no-replace case is executed by this document.
- No retained artifact is created by this document.

## 4. Controlling Assessment

The controlling assessment is the committed readiness document at:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_BLOCKER_2_RETAINED_RUNTIME_READINESS_ASSESSMENT_v0.1.md
```

That assessment records the post-preparation state as not executable for authoritative retained use. Its final decision requires a narrow runtime correction before execution authorization.

The relevant assessment findings are:

- Authoritative retained preflight is still structurally rejected.
- Terminal run results hard-code `retained_execution = false`.
- Real native executor observations do not yet satisfy retained policy identity admission.
- Schema, case-set, fixture-profile, and complete source identity bindings are not required as execution-authorization inputs.
- One-shot authority is only local to the selected result directory.
- Cross-location replay is not prevented.
- Fixture root, result parent, host profile, and volume identity are not bound into the authorization.

## 5. Remaining Runtime Gaps

The retained runtime must be corrected before an execution authorization can be issued.

The remaining gaps are:

- The authoritative path must be enabled only through a complete identity-bound authorization object, not through a plain boolean.
- A global one-shot authority registry must exist before the local gate can be consumed.
- The local gate must include and verify the global authority entry hash.
- The native execution result and the retained completion receipt must be separate canonical records.
- The retained completion receipt must be the only record that can set `retained_execution = true`.
- The retained evaluator must accept real native case observations through an explicit retained envelope that binds both the native helper policy identity and the retained absolute-path policy identity.
- The implementation must bind the exact expected schema, case-set, fixture-profile, repository, source, path, host, and volume identities before authoritative mode can become reachable.

## 6. Authorization Decision

This document authorizes:

```text
authorization_verdict = "AUTHORIZE_NARROW_POST_COMMIT_RUNTIME_CORRECTION"
authorized_task = "NARROW_POST_COMMIT_RUNTIME_CORRECTION"
authoritative_retained_run_authorized = false
authoritative_retained_run_executed = false
authoritative_gate_consumed = false
authoritative_artifact_created = false
blocker_2_state = "OPEN"
blocker_4_started = false
production_integration_authorized = false
```

The authorization is for correction work only. It is not an execution authorization.

## 7. Authorized Architecture

The authorized correction architecture is a four-record evidence chain:

```text
GLOBAL_AUTHORITY_ENTRY -> LOCAL_GATE_ENTRY -> RUN_RESULT -> RETAINED_COMPLETION
```

The global authority entry establishes the one-shot right to attempt exactly one retained authoritative run in the bound environment.

The local gate entry binds the selected run directory to that global authority entry.

The run result records the native case observations and remains a run-output record only.

The retained completion receipt records that the retained run completed after the run result was durably written, reread, hash-verified, and linked to the already consumed authority chain.

## 8. Authorized File Surface

The authorized implementation surface is limited to these files:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py
research/brainvision/test_blocker2_retained_absolute_path_control_integration_v0_1.py
```

No new runtime module is authorized by this document.

No durable-evidence module is authorized for modification by this document.

No production integration file is authorized for modification by this document.

If the later implementer discovers that the correction cannot be completed within this file surface, the correct outcome is to stop and request a new authorization rather than broadening the implementation.

## 9. Identity-Bound Authoritative Enablement

The correction must replace plain authoritative enablement with an identity-bound authorization object.

The authorization object must be canonical and must bind at least:

- Retained mode.
- Requested authoritative state.
- Execution authorization identity.
- Runtime correction authorization identity.
- Readiness assessment identity.
- Repository branch, HEAD, and origin/main.
- Expected retained absolute-path policy identity.
- Expected native helper policy identity.
- Expected retained schema identity.
- Expected retained case-set identity.
- Expected fixture-profile identity.
- Complete retained source identity set.
- Fixture root.
- Result parent.
- Result directory identity.
- Global authority registry root identity.
- Local gate path identity.
- Run result path identity.
- Retained completion path identity.
- Host identity.
- Volume identity.
- Attempt identity.

Authoritative runtime execution must remain unreachable unless all required identities match before any local gate is consumed.

## 10. Global One-Shot Authority Registry

The correction must add a global one-shot authority registry inside the retained runtime module.

The registry root must be explicit, canonical, local, non-reparse, and outside the repository working tree.

The registry entry path must be derived from the canonical execution authorization identity. It must not be caller-selectable.

The registry entry must be written with exclusive-create semantics, flushed, parent-directory synced through the existing BLOCKER-1 durability adapter, reread, and hash-verified before the local gate is created or consumed.

The registry entry must bind:

- Execution authorization identity.
- Fixture root.
- Result parent.
- Result directory identity.
- Host identity.
- Volume identity.
- Retained mode.
- Retained source identity set.
- Expected policy, schema, case-set, and fixture-profile identities.

After a registry entry exists, the same execution authorization must not be usable for any second authoritative attempt in the same authority domain, including an attempt from a different fixture root or result parent.

No release, force, retry, repair, resume, or manual-consume path is authorized.

## 11. Local Gate Entry

The existing local gate concept remains authorized only as a downstream control.

The local gate entry must include:

- Global authority entry path.
- Global authority entry hash.
- Execution authorization identity.
- Fixture root.
- Result parent.
- Result directory identity.
- Attempt identity.
- Retained mode.
- Expected identity values from the authorization object.

The local gate cannot create authority by itself. It can only bind the local run directory to an already established global authority entry.

## 12. Native Policy and Retained Policy Binding

The authorized correction is the retained-envelope approach.

The existing native helper policy identity remains a native observation identity. It must not be relabeled as the retained absolute-path policy identity.

The retained evaluator must require both:

```text
native_helper_policy_identity = "e1094b40c5f312e32c48e6ac125c2e961996f52656b951646cecbf7432419928"
retained_absolute_path_policy_identity = "3d9b66a180fabf00c8bb6695c74fc9d69d21cd3ac9335cc5d2dc3a1169417531"
```

Each real native case observation must be wrapped in a retained case envelope that records the native helper identity, the retained policy identity, the retained schema identity, the case-set identity, and the fixture-profile identity.

Legacy non-retained modes must remain semantically unchanged.

## 13. Run-Result Contract

The run-result artifact must be canonical JSON.

The run result must contain native case observations, retained envelopes, execution status, and hashes required for retained evaluation.

The run result must continue to report no retained completion. It must not be the source of a final retained-execution claim.

The run result must be written with the existing durable write path, parent-directory sync, reread, and hash verification.

## 14. Retained-Completion Contract

The retained-completion artifact must be a separate canonical JSON receipt.

The completion receipt may set `retained_execution = true` only after:

- The global authority entry has been durably established and verified.
- The local gate has been durably established and verified.
- The native case run has completed.
- The run result has been durably written, reread, and hash-verified.
- The retained evaluator has accepted every required case outcome and every required identity binding.

The completion receipt must reference:

- Global authority entry hash.
- Local gate entry hash.
- Run result hash.
- Execution authorization identity.
- Retained mode.
- Repository identity.
- Source identity set.
- Policy, schema, case-set, and fixture-profile identities.
- Fixture root, result parent, host, volume, and attempt identity.

The completion receipt must not include its own digest as a field inside the canonical object. Its digest may be reported only by the caller after reread verification.

## 15. Evidence-Chain Linkage

The later implementation report must make the evidence chain explicit:

```text
global_authority_hash
local_gate_hash
run_result_hash
retained_completion_hash
```

Every downstream record must include the hash of the upstream record it depends on.

Any missing link is a failed authoritative correction.

## 16. Failure and Interruption Semantics

Failure semantics must be conservative.

If the global authority entry is created and any later step fails, the execution authorization is spent.

If the local gate is created and any later step fails, the execution authorization is spent.

If native execution fails after authority is consumed, the execution authorization is spent.

If durable write, directory sync, reread, or hash verification fails for any authoritative record, the execution authorization is spent.

No automatic retry, resume, cleanup, authority release, or second attempt is authorized.

Non-authoritative synthetic tests may use isolated temporary roots, but they must not exercise or weaken the authoritative authority-spend semantics.

## 17. BLOCKER-1 Durability Use

The correction must continue using the existing BLOCKER-1 directory durability adapter for authoritative records.

Authoritative record creation must require:

- File content flush.
- Parent-directory durability attempt.
- A `DIRECTORY_DURABILITY_CONFIRMED` result.
- Reread verification.
- Byte-level digest verification of the reread content.

Any downgrade, bypass, mock result, or best-effort directory durability state is invalid for authoritative correction.

## 18. Test and Fault-Injection Requirements

The later implementation must add or update tests that prove:

- Plain boolean authoritative enablement is rejected.
- A complete identity-bound authorization object is required.
- Missing or mismatched repository identity is rejected.
- Missing or mismatched source identity is rejected.
- Missing or mismatched policy, schema, case-set, or fixture-profile identity is rejected.
- Missing or mismatched fixture root, result parent, host, or volume identity is rejected.
- Global one-shot authority is consumed before local gate entry.
- A second attempt with the same execution authorization is rejected.
- Cross-location replay with the same execution authorization is rejected.
- Local gate entry binds the global authority entry hash.
- Run-result and retained-completion records are separate.
- Run-result cannot assert retained completion.
- Retained-completion cannot exist without a verified run-result hash.
- Faults after global authority creation spend the authorization.
- Faults after local gate creation spend the authorization.
- Faults after native execution spend the authorization.
- Faults during completion write or verification spend the authorization.
- Retained envelopes bind both native and retained policy identities.
- Legacy non-retained modes remain unchanged.
- Integration coverage remains non-authoritative unless a later execution authorization explicitly permits an authoritative run.

The correction implementation must not run native retained authoritative cases as part of this authorization.

## 19. Claims Supported

After successful completion of the later correction and its tests, the repository may claim:

- A narrow runtime correction has been implemented for identity-bound retained execution authorization.
- Authoritative retained execution remains unavailable without a complete authorization object.
- A global one-shot authority registry exists for the retained authoritative path.
- The retained runtime separates native run results from retained completion receipts.
- The retained evaluator binds both the native helper policy identity and the retained absolute-path policy identity.
- BLOCKER-2 remains open pending an explicitly authorized retained run and evidence review.

## 20. Claims Not Supported

This document does not support any claim that:

- BLOCKER-2 is complete.
- Authoritative retained execution has occurred.
- Native rename behavior has been finally established for BLOCKER-2 closure.
- Directory-entry durability for the retained rename cases has been finally established for BLOCKER-2 closure.
- Power-loss persistence has been finally established for BLOCKER-2 closure.
- Production integration may begin.
- BLOCKER-4 may begin.

## 21. Prohibited Actions

This document prohibits:

- Running an authoritative retained single-run case set.
- Creating an authoritative gate.
- Consuming an authoritative gate.
- Creating authoritative retained artifacts.
- Running native retained rename cases.
- Starting BLOCKER-4.
- Modifying production integration.
- Modifying durable-evidence shared modules.
- Broadening the file surface beyond the authorized files.
- Adding retry, release, resume, repair, or force paths for authoritative execution authority.

## 22. Required Implementation Report

The later implementation report must include:

- Changed file list.
- Exact tests run.
- Test outcomes.
- Confirmation that no authoritative retained run was executed.
- Confirmation that no authoritative gate was created or consumed.
- Confirmation that no authoritative artifact was created.
- Confirmation that BLOCKER-2 remains open.
- Confirmation that BLOCKER-4 was not started.
- Confirmation that production integration remains unauthorized.
- Evidence that the four-record chain is implemented.
- Evidence that retained completion is separate from run result.
- Evidence that the global one-shot registry blocks same-authorization replay.
- Evidence that cross-location replay is rejected.
- Evidence that retained and native policy identities are both bound.

## 23. Authorization Verdict

The verdict is to authorize the narrow post-commit runtime correction only.

No execution authorization is granted.

## 24. Exact Next Step

Implement the narrow post-commit runtime correction within the authorized file surface, then report the implementation and tests without executing an authoritative retained run.

A. AUTHORIZE_NARROW_POST_COMMIT_RUNTIME_CORRECTION
