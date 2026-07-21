# TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Self-Boundary Correction Authorization v0.1

## 0. Decision

```text
A. A TIGHTLY SCOPED IMPLEMENTATION CORRECTION OF THE FREEZE-LIBRARY SELF-BOUNDARY
   FALSE POSITIVE IS AUTHORIZED. RUNNER EXECUTION REMAINS CLOSED. THE CANONICAL
   ITERATOR WAS NEVER CONTACTED AND THE ONE-RUN AUTHORITY WAS NOT CONSUMED.
```

This document authorizes a bounded infrastructure correction to the source-boundary false positive that caused the authoritative invocation to refuse fail-closed at pre-contact. It authorizes nothing else. It does not weaken the source-boundary checker, does not amend the frozen F3 result, does not authorize a retry, and does not consume the canonical iterator.

This is a docs-only authorization. No source or test file was modified while preparing it. No runner, canonical iterator, generator, verifier, freeze operation, manifest builder, or project function was executed. No results, staging, evidence, fixtures, or manifests were created. No Git command was run.

---

## 1. Established finding

The authoritative invocation

```text
python research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

at execution-authorization HEAD

```text
9ad6086d984ac9acaf46944ccc8218987d6e9f19
```

returned silently and created neither of:

```text
research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1
research/brainvision/results/.independent_order_sensitive_synthetic_fixture_freeze_v0_1.staging
```

The repository remained clean and synchronized. The visible pre-contact requirements were all confirmed satisfied:

```text
Python = 3.11.15
branch = main
HEAD = origin/main = 9ad6086d984ac9acaf46944ccc8218987d6e9f19
authorization path latest commit = HEAD
working tree = clean
repository root = authoritative repository root
final output path absent
staging output path absent
```

A silent return with no staging directory, no final directory, and exit-2 semantics is the exact signature of a pre-contact `PreContactRefusal`: the runner refused before requesting the canonical seed iterator. The refusal is therefore a fail-closed pre-contact event, not a post-contact process failure, and it published no evidence.

---

## 2. Exact defect

The committed freeze library

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

has frozen identities

```text
Git blob = a06a80ac1a253a6b85f2c3e6bf4bf712b0d78d8a
Windows raw SHA-256 = ef78cc21a3a6e139a781ce4f8c356c88b9a132ab89771d8250dc57ea375b2fca
```

The library assembles its forbidden-marker vocabulary from fragments so that no full marker appears verbatim in its own source, which is precisely what keeps the boundary checker from flagging its own vocabulary. The generic marker is assembled correctly:

```python
"asymmetry" + "_audit"
```

Its runtime value is `asymmetry_audit`, and it is a member of the generic frozen tokens and therefore of `_FROZEN_PATH_MARKERS`.

One compound marker, however, is assembled with a verbatim second operand:

```python
"algebraic_n64_primary_v0_1_f3_" + "asymmetry_audit"
```

`ast.parse` represents the second operand as the direct string constant

```text
asymmetry_audit
```

`_string_constants` walks the AST and collects every `str` constant, so it collects that literal. `validate_source_boundary` then checks, for every collected literal, whether any `_FROZEN_PATH_MARKERS` value appears within it:

```python
if any(marker in literal for marker in _FROZEN_PATH_MARKERS):
```

Because `_FROZEN_PATH_MARKERS` contains the generic marker `asymmetry_audit`, and the collected literal is exactly `asymmetry_audit`, the substring test matches. The library therefore rejects its own exact source with:

```text
PROHIBITED_FROZEN_FAMILY_CONTACT / source_boundary
```

raised as the single `SyntheticFixtureProcessFailure(selected, "source_boundary", ...)`.

During pre-contact, the runner validates the five frozen S1B source texts through `validate_source_boundary`. The freeze-library source is one of those five. Its self-rejection is converted by the runner into a silent `PreContactRefusal`: the canonical iterator is never requested, no seed is consumed, and no staging or final evidence is created. This is the exact cause of the observed silent, evidence-free return.

The defect is a false positive in the checker's self-scan caused by one verbatim literal fragment. It is not a real frozen-family contact, and it does not indicate any weakness in the boundary policy the checker enforces against genuine sources.

---

## 3. Authorization decision

A tightly scoped implementation correction is authorized, covering only these three files:

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

### 3.1 Exact freeze-library source correction

The freeze-library source correction must be exactly equivalent to replacing:

```python
"algebraic_n64_primary_v0_1_f3_" + "asymmetry_audit"
```

with:

```python
"algebraic_n64_primary_v0_1_f3_" + "asymmetry" + "_audit"
```

This splits the verbatim `asymmetry_audit` operand into two fragments so that `_string_constants` no longer collects the full marker as a single literal, while the assembled runtime marker value `algebraic_n64_primary_v0_1_f3_asymmetry_audit` is preserved byte-for-byte. The marker's meaning, coverage, and membership in `_FROZEN_PATH_MARKERS` are unchanged.

No forbidden-marker semantics may be removed, narrowed, weakened, bypassed, allowlisted, or special-cased. In particular, the correction must not:

```text
delete or shorten any marker
add any self-referential exemption, allowlist entry, or path exception to the checker
skip, disable, or short-circuit the string-literal scan
introduce any escape hatch that suppresses PROHIBITED_FROZEN_FAMILY_CONTACT for real literals
```

The only permitted change to marker construction is fragment-splitting that leaves every assembled runtime value identical.

### 3.2 Required regression coverage

The implementation must add a bounded regression proving that the exact committed freeze-library source passes its own boundary check:

```python
validate_source_boundary(
    freeze_library_path,
    exact_freeze_library_source_text,
    AUTHORIZED_ALLOWLIST,
)
```

The regression must also preserve positive detection of genuine direct literals containing any of:

```text
asymmetry_audit
historical_f3
frozen_family
retained_family
retained_evidence
```

so that a real source carrying one of these complete literals verbatim is still rejected with `PROHIBITED_FROZEN_FAMILY_CONTACT / source_boundary`. The correction must fix the self-scan false positive without lowering true-positive detection.

Positive-regression self-scan safeguard. Because the generator/freeze test source is itself one of the five sources that must pass exact self-validation, the test file must not contain any complete prohibited marker as a direct AST string constant merely to define a positive test case. Positive test inputs must construct the prohibited marker text from fragments in the test implementation, then build a synthetic source string whose parsed AST contains the genuine complete direct literal being tested. The synthetic source passed to `validate_source_boundary` must therefore contain the real complete prohibited literal, while the exact generator/freeze test source must remain self-clean. This applies to each required positive token:

```text
asymmetry_audit
historical_f3
frozen_family
retained_family
retained_evidence
```

This is a test-construction constraint only. It must not weaken, bypass, allowlist, or special-case any production boundary behavior.

### 3.3 Runner change scope

The runner source may change only to refresh the exact frozen S1B identity constants affected by this correction:

```text
freeze library Git blob
freeze library Windows raw SHA-256
generator/freeze test Git blob
generator/freeze test Windows raw SHA-256
```

No other runner change is authorized. Specifically, none of the following may change:

```text
runner behavior
CLI shape
pre-contact sequencing
one-run consumption threshold
two-pass logic
publication behavior
canonical result vocabulary
process-outcome and failure-code mapping
execution-envelope, summary, or exit-code contract
```

The runner test (`test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py`) is not in this correction's scope and is not changed by this authorization.

---

## 4. Required verification

Focused, bounded tests are required, covering at least:

```text
freeze-library source-boundary suite
generator/freeze test suite
runner suite
self-validation of all five exact frozen S1B source texts
false-positive guard for marker construction fragments
positive detection of genuine prohibited complete literals
```

Self-validation must pass `validate_source_boundary` against each of the five exact frozen S1B source texts under `AUTHORIZED_ALLOWLIST` (verifier, generator, freeze library, verifier test, generator/freeze test). The false-positive guard must confirm that fragment-assembled marker construction does not self-trip the checker. The positive-detection tests must confirm that genuine complete literals still reject.

No real canonical iterator may be driven by any test. Tests use only bounded hand-authored inputs, injected sources, and mocked responses; the full canonical seed iterator is never consumed.

---

## 5. Identity consequences

Implementing this correction will change committed bytes and therefore invalidate the current frozen identities and the current execution authorization. Specifically, changing the freeze-library source changes its Git blob and Windows raw SHA-256; adding the regression changes the generator/freeze test's Git blob and Windows raw SHA-256; refreshing the runner's S1B constants changes the runner's own Git blob and Windows raw SHA-256; and because the runner's `runner_git_blob` / `runner_raw_sha256` change, the execution-authorization binding at the frozen path no longer matches and must be revised.

The implementation correction must be prepared and committed through this exact identity sequence, in order:

```text
finalize the exact corrected freeze-library bytes
finalize the exact generator/freeze-test bytes
compute the candidate Git blob and Windows raw SHA-256 identities of those exact bytes
refresh the runner's frozen S1B constants with those exact candidate identities
run the complete bounded verification suite against the final three-file candidate
confirm the candidate freeze-library and generator/freeze-test bytes have not changed since their identities were computed
commit exactly the authorized three implementation files together
verify the committed freeze-library and generator/freeze-test Git blobs and Windows raw SHA-256 values equal the values embedded in the committed runner
resolve and record the committed runner Git blob and Windows raw SHA-256
rerun bounded direct and adversarial review
revise the exact execution-authorization document at its frozen path with the new runner identity values
commit that authorization document alone as a new authorization HEAD
stop again before execution
```

The identity refresh must be commit-consistent:

```text
The runner constants must be correct in the same implementation commit that carries the corrected freeze library and regression test.
No implementation commit containing the corrected freeze library may retain the old freeze-library or generator/freeze-test identity constants in the runner.
If either corrected dependency changes after its candidate identities are computed, recompute both identities and refresh the runner before committing.
```

Only these three implementation files are authorized:

```text
research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

The execution-authorization document path is unchanged; only its bound identity values (and the resulting authorization HEAD) are revised. Execution remains paused after the revised authorization is committed and pushed, and still requires a separate explicit final operator instruction from Hilmir.

The configuration SHA-256 is unchanged unless implementation review discovers a real contradiction. No configuration change is authorized by this correction. If review does surface a genuine configuration contradiction, that is a separate finding requiring its own review and authorization; it is not opened here.

---

## 6. Authority state

```text
PRE_CONTACT_REFUSAL_CONFIRMED = True
CANONICAL_ITERATOR_CONTACTED = False
ONE_RUN_AUTHORITY_CONSUMED = False
FAMILY_FROZEN = False
RERUN_AUTHORIZED = False

SELF_BOUNDARY_CORRECTION_IMPLEMENTATION_AUTHORIZED = True
RUNNER_EXECUTION_AUTHORIZED_AFTER_SOURCE_CHANGE = False
CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

Because the pre-contact refusal occurred before the first real canonical-iterator contact, the one-run execution authority was never consumed. A corrected, re-reviewed, and re-committed execution authorization would still spend exactly one future authority-consuming run, and only under a separate explicit Hilmir instruction.

---

## 7. Permanent Brainvision and TORMENT posture

Preserved permanently:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

This correction is infrastructure-only. It does not weaken the source-boundary checker, amend the frozen F3 result, authorize a retry, or consume the canonical iterator. Brainvision remains offline, quarantined, descriptor-blind at this stage, non-production, non-service, non-kernel, and non-memory-integrated. Integration into the production TORMENT memory system or kernel remains prohibited without a later explicit architectural discussion with Hilmir and his approval of the integration route.

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Self-Boundary Correction Authorization v0.1. Docs-only. Authorizes a bounded three-file correction of a freeze-library self-scan false positive (one verbatim `asymmetry_audit` literal fragment) plus its regression coverage and the consequent S1B/runner identity refresh and execution-authorization revision. No forbidden-marker semantics are weakened. The pre-contact refusal is confirmed; the canonical iterator was never contacted; the one-run authority was not consumed. No source, test, runner, result, staging, evidence, fixture, manifest, or kernel file was changed while preparing this document, and no Git command was run. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted.*
