# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 Identity-Derivation-Cycle Correction Authorization v0.1

## 0. Document Status

Status: authorization assessment.

Scope: docs-only authorization for the narrow BLOCKER-2 identity-derivation-cycle correction discovered while preparing the exact inactive authoritative retained single-run authorization.

This document does not modify implementation or tests, does not authorize an authoritative real run, does not run any wrapper mode, does not create or consume authority, and does not close BLOCKER-2.

```text
defect = "IDENTITY_DERIVATION_CYCLE"
correction_model = "STAGED_NON_CIRCULAR_DERIVATION"
authoritative_run_authorized = false
authoritative_run_executed = false
authority_consumed = false
result_directory_created = false
blocker_2_state = "OPEN"
blocker_4_started = false
```

## 1. Authorization Question

Should the repository authorize a narrow implementation correction that removes the discovered BLOCKER-2 identity-derivation cycle while preserving deterministic result-directory derivation, caller-unselectable result paths, source identity binding, and cross-registry-root replay resistance?

## 2. Baseline

Verified read-only baseline on 2026-07-26:

```text
branch:
main

HEAD:
54762c84214f7a6e8ff18666b6fe2f3050146f57

origin/main:
54762c84214f7a6e8ff18666b6fe2f3050146f57

working tree:
clean before this document was created

.git/index.lock:
absent
```

## 3. Preserved Boundaries

Prepared roots are present and admitted from prior BLOCKER-2 preparation work. No path preparation rerun is authorized by this document.

```text
authority registry root:
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3

fixture root:
C:\TORMENT\brainvision_authoritative_fixture\blocker2_s3b_v0_3

result parent:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3
```

Prior preparation execution authorization identity retained for boundary reference only:

```text
9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92
```

The corresponding inactive artifacts remain absent:

```text
result directory:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92
state: absent

global authority entry:
C:\TORMENT\brainvision_authority\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92.global_authority_entry.canonical.json
state: absent

local gate:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\gate_entry.canonical.json
state: absent

RUN_RESULT:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\run_result.canonical.json
state: absent

RETAINED_COMPLETION:
C:\TORMENT\brainvision_retained_results\blocker2_s3b_v0_3\9888fd0b1ed0f392df98690eaecaa2b593cfe867a58115ea4661a7d6f2a1ea92\retained_completion.canonical.json
state: absent

authority consumed:
false

BLOCKER-2:
OPEN

BLOCKER-4:
not started
```

## 4. Cycle Evidence

The discovered defect is not a test failure and not an operator error. It is a committed identity-derivation cycle:

```text
execution_authorization_identity
-> result_directory path
-> result_directory_identity
-> run_identity
-> execution_authorization declaration
-> execution_authorization_identity
```

Committed wrapper surface:

```text
research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

Evidence:

```text
derived_path_model(execution_authorization_identity) derives:
result_directory = RESULT_PARENT / execution_authorization_identity

_validate_path_model(payload) reads:
retained_authorization.authorization_identity

_validate_path_model(payload) then computes:
expected = derived_path_model(auth_id)
```

Thus the wrapper requires the fixed path model, including result directory and artifact paths, to be derived from the authorization identity.

Committed runtime surface:

```text
research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
```

Evidence:

```text
execution_authorization_identity_declaration(...) includes:
result_directory_identity
run_identity

run_identity_declaration(...) includes:
result_directory_identity

build_execution_authorization_identity_block(...) derives:
authority_registry_root_identity
fixture_root_identity
result_parent_identity
result_directory_identity
derived_run_identity
identity_declaration
derived_authorization_identity

validate_execution_authorization_identity_block(...) recomputes:
build_execution_authorization_identity_block(...)
```

Because the wrapper derives `result_directory` from `execution_authorization_identity`, and the runtime derives `execution_authorization_identity` from a declaration that includes both `result_directory_identity` and `run_identity`, the current graph requires the authorization identity before the path can be known and requires the path-derived identities before the authorization identity can be known.

## 5. Root Cause

The root cause is that the execution-authorization identity currently mixes upstream authorization facts with downstream execution-path facts.

The authorization identity is used as an input to derive the result directory path. The result directory path is then used to derive `result_directory_identity`. That path identity is used to derive `run_identity`. Both `result_directory_identity` and `run_identity` are then included in the execution-authorization declaration that hashes back into `execution_authorization_identity`.

That makes the authorization identity both a prerequisite and a result of the same derivation graph.

## 6. Required Staged Derivation

The correction must use a staged, non-circular derivation model.

Stage A derives `execution_authorization_identity` from only upstream and independently observable authorization inputs. Stage A must bind the deterministic derivation rule for the future result directory but must not include the future result directory identity or run identity.

Stage B derives the result directory from the Stage A authorization identity:

```text
result_directory = result_parent / execution_authorization_identity
```

Stage B then derives `result_directory_identity` from that deterministic path.

Stage C derives `run_identity` after Stage B. The run identity is downstream of the execution authorization and result directory. It must not feed back into the execution-authorization declaration.

## 7. Execution-Authorization Declaration

The corrected execution-authorization declaration must bind, at minimum:

```text
repository commit
branch
origin/main
all committed source identities
all controlling-document identities
authority-registry-root identity
fixture-root identity
result-parent identity
deterministic result-directory derivation rule
runtime identities
wrapper identities
operator identity
single-process declaration
single-attempt declaration
real-executor selector
case set
case order
A6 false
fault injection disabled
authorization-document identity
```

The corrected declaration must explicitly bind this derivation rule:

```text
result_directory = result_parent / execution_authorization_identity
```

The corrected declaration must not include:

```text
result_directory_identity
run_identity
```

The declaration must remain canonical and transparent. It must not replace the removed downstream fields with an opaque operator-selected authorization identity.

## 8. Result-Directory Derivation

After the corrected execution authorization identity is computed, the result directory must be derived deterministically as:

```text
result_directory = result_parent / execution_authorization_identity
```

The result directory remains caller-unselectable. The caller may not provide a competing result-directory path to satisfy a precomputed identity. Any wrapper input containing an arbitrary or mismatched path model must continue to fail validation.

After the deterministic path is known, `result_directory_identity` must be derived from the absent result directory path and the admitted result parent.

## 9. Run-Identity Declaration

The corrected run identity must be derived only after the result directory and result-directory identity are known.

The corrected run-identity declaration must bind, at minimum:

```text
execution_authorization_identity
authority-registry-root identity
fixture-root identity
result-parent identity
result-directory identity
repository commit
case-set identity
case order
A6 false
operator identity
real-executor selector
single-attempt declaration
```

The run identity may depend on the execution authorization identity. The execution authorization identity must not depend on the run identity.

## 10. Replay-Resistance Preservation

The correction must preserve this invariant:

```text
one execution authorization
-> one exact authority-registry root
-> one exact fixture root
-> one exact result parent
-> one deterministically derived result directory
-> one run identity
```

The corrected model preserves cross-registry-root replay resistance only if the authority-registry-root identity is bound in Stage A before `execution_authorization_identity` is computed. With that binding, the same authorization identity cannot be replayed under a different registry root because the registry root identity contributes to the authorization identity itself.

The correction must fail closed if any of these change:

```text
registry root
fixture root
result parent
derivation rule
repository commit
source identity
case set
case order
operator
executor
A6 state
```

The same authorization must not map to two result directories, and two registry roots must not admit the same execution authorization.

## 11. Authorized File Surface

The authorized future implementation surface is limited to the smallest necessary BLOCKER-2 files:

```text
MODIFIED research/brainvision/blocker2_retained_absolute_path_control_v0_1.py
MODIFIED research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
MODIFIED research/brainvision/test_blocker2_retained_absolute_path_control_v0_1.py
MODIFIED research/brainvision/test_run_blocker2_authoritative_retained_single_run_v0_1.py
```

Integration tests may be modified only if a Windows-specific assertion is genuinely required to prove the correction.

No unrelated files are authorized. Legacy promotion primitives are not authorized for modification by this correction.

## 12. Required Tests

The implementation must retain all existing tests and add focused proof for the staged model:

```text
execution authorization derives without result_directory_identity
execution authorization derives without run_identity
result directory derives deterministically from authorization identity
result-directory identity derives after authorization identity
run identity derives after result-directory identity
no hash cycle exists
changing result parent changes authorization identity
changing registry root changes authorization identity
changing fixture root changes authorization identity
changing result-directory path directly is impossible
changing derived result-directory identity changes run identity
run identity does not change authorization identity
cross-registry replay remains rejected
same authorization cannot map to two result directories
wrapper path-model validation still rejects arbitrary result paths
inactive canonical input can be constructed deterministically
```

No authoritative real run may occur while proving this correction.

## 13. Identity-Versioning Requirements

Old and proposed new identities must be recorded separately after implementation. This document does not compute new implementation identities because no implementation or test files are changed here.

Known current identities from the retained BLOCKER-2 line:

```text
retained schema identity:
a82515184f99862dbf9be23730114ad6df81d6ab2b223df1293c7416f4a5ff66

wrapper authorization-input schema identity:
5ae200411efaccb9fc847a213566d158740396020007dfb42b595081d369a327

fixed-path profile identity:
c92e5906b98e5e3fa497ac86abaa57660a93c44ae8cc663685ed01bc87a7fbb6

evidence-chain identity:
185e4dea85abf436ac93a01632f0b1ab4895086177e2de073608a0c08b2d174b
```

The execution-authorization declaration currently uses the schema label:

```text
torment.brainvision.blocker2.retained.execution_authorization_identity.v0.1
```

That declaration must be versioned when `result_directory_identity` and `run_identity` are removed and the deterministic derivation rule is added as a Stage A binding.

The run-identity declaration currently uses the schema label:

```text
torment.brainvision.blocker2.retained.run_identity.v0.1
```

That declaration must be versioned if it is changed to bind `execution_authorization_identity`, result-parent identity, case order, operator identity, real-executor selector, or single-attempt declaration.

Identity-versioning assessment:

```text
retained schema identity:
must change if retained canonical payloads, dataclass payloads, or schema declarations change; otherwise may remain unchanged.

execution-authorization declaration identity:
must change because the canonical declaration shape changes.

run-identity declaration identity:
must change if the declaration is extended as required by this staged model.

wrapper authorization-input schema identity:
must change if wrapper canonical input adds staged derivation fields or changes path-model validation expectations.

fixed-path profile identity:
may remain unchanged if the exact roots and derivation rule identity remain unchanged; must change if the profile declaration itself changes.

evidence-chain identity:
may remain unchanged if evidence record and chain semantics do not change; must change if the chain binds new staged identity records.
```

No old schema identity may be silently retained when its canonical declaration changes.

## 14. Claims Supported

This document supports these claims:

```text
The current committed model contains an identity-derivation cycle.
The cycle is rooted in declaration ordering, not in operator usage.
The staged derivation model removes the cycle by excluding downstream path and run identities from Stage A.
The result directory can remain deterministic and caller-unselectable.
Cross-registry-root replay resistance can be preserved by binding authority-registry-root identity in Stage A.
The authorized implementation surface can be narrow.
BLOCKER-2 remains open.
BLOCKER-4 has not started.
```

## 15. Claims Not Supported

This document does not support these claims:

```text
The correction has been implemented.
The correction has been tested.
An authoritative retained run is authorized.
An authoritative retained run has executed.
Authority has been created or consumed.
A result directory has been created.
BLOCKER-2 is closed.
BLOCKER-4 may start.
New implementation identity hashes have been computed.
```

## 16. Prohibited Actions

This authorization does not permit:

```text
modifying source outside the authorized future file surface
modifying tests outside the authorized future file surface
running PREPARE_PATHS
running PREFLIGHT_ONLY
running EXECUTE_EXACT_SINGLE_RUN
invoking native cases
creating a result directory
creating a global authority entry
creating or consuming a local gate
writing RUN_RESULT
writing RETAINED_COMPLETION
consuming authority
closing BLOCKER-2
starting BLOCKER-4
committing
pushing
```

## 17. Authorization Verdict

A. AUTHORIZE_NARROW_IDENTITY_DERIVATION_CYCLE_CORRECTION

## 18. Exact Next Step

Implement only the staged non-circular identity derivation correction on the authorized future file surface, with tests proving that the execution authorization identity is computed before result-directory identity and run identity, while preserving deterministic result-directory derivation and cross-registry-root replay rejection.
