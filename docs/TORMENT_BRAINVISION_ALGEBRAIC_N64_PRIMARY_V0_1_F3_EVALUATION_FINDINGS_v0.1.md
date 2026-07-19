# TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluation Findings v0.1

## 0. Disposition

```text
A. RECORD VALID AUTHORITATIVE FROZEN-FAMILY F3 NEGATIVE
```

This document records the completed one-run authoritative frozen-family F3 evaluation faithfully and conservatively. It is a findings record only.

This document is:

```text
docs-only
non-executing
offline
quarantined
non-production
```

This document does not authorize any rerun, threshold adjustment, witness replacement, reinterpretation, or scientific inference. The one-run F3 authority is already consumed.

The retained canonical JSON result is the authoritative evaluation evidence. The retained operator summary is a convenience artifact only and is not a substitute for the canonical result. This document transcribes both retained artifacts; it does not replace, regenerate, edit, rename, delete, normalize, or reserialize either one.

---

## 1. Governing authorization

Bound execution authorization:

```text
docs/TORMENT_BRAINVISION_ALGEBRAIC_N64_PRIMARY_V0_1_F3_EVALUATION_EXECUTION_AUTHORIZATION_v0.1.md
```

Authorization commit:

```text
c4f489c439d4190611e8e0c5b3034ead3353c26d
```

Commit subject:

```text
docs(research): authorize frozen N64 F3 evaluation
```

Authority state after the completed run:

```text
F3_EXECUTION_AUTHORIZATION_DOCUMENTED = True
F3_EXECUTION_AUTHORIZED = consumed
F3_EXECUTION_AUTHORIZATION_COUNT = 1
F3_EXECUTED = True
FROZEN_FAMILY_PSITRS_CONTACT = True
F3_RERUN_AUTHORIZED = False
```

The sole frozen-witness evaluation authority has been consumed. One successful frozen-witness evaluation was performed after one earlier proven pre-contact refusal. No further F3 execution is authorized under this authority.

Recorded invocation accounting:

```text
runner command attempts = 2
pre-contact refusals = 1
frozen-witness evaluations = 1
successful authoritative evaluations = 1
```

The pre-contact refusal was not descriptor contact and was not an F3 hypothesis evaluation.

---

## 2. Execution identity

Recorded execution identity:

```text
execution_commit_identity =
c4f489c439d4190611e8e0c5b3034ead3353c26d
```

The committed runner dynamically resolved and recorded this synchronized execution `HEAD` in the canonical result. It equals the authorization commit, as required.

Runner:

```text
research/brainvision/run_algebraic_n64_f3_evaluation_v0_1.py
```

Runner Git blob:

```text
f8103c37569f9b1eb3ca19533d0374bd2b80ada9
```

Runner raw-byte SHA-256:

```text
505316892cf8b02548da2a4dab6796b7bc70e7d55067076712d3ad10279b0a17
```

Recorded execution conditions for the successful invocation:

```text
the gate was initially unset
the final and staging output paths were initially absent
the authoritative Windows working tree was clean
HEAD == origin/main
the runner was invoked once after a prior proven pre-contact refusal
the successful invocation exited 0
the gate was cleared immediately afterward
the working tree remained clean
```

### 2.1 Prior accidental pre-contact refusal

A prior invocation encountered a dirty working tree caused by an accidental untracked file named `main`.

```text
The final output directory remained absent.
The staging directory remained absent.
The runner had not entered production-pass execution.
No frozen-witness PsiTRS contact occurred.
The refusal was classified as pre-contact and the authority remained unconsumed.
```

After the accidental file was deleted, the exact required pre-execution state was restored and the later successful invocation was permitted under the same authorization.

The pre-contact refusal is not counted as an F3 evaluation run. Exactly one authorized frozen-witness evaluation was performed, by the later successful invocation.

---

## 3. Frozen family identity

```text
N = 64
K = 3
accepted candidate order = [478, 479, 480]
six binary circular members
member weight = 12
```

Freeze-result identity:

```text
freeze-result whole-file SHA-256 =
97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5

freeze-result payload SHA-256 =
35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e

family-manifest SHA-256 =
352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151

family-verifier-certificate SHA-256 =
416d32bba578856b5122402186860643071070c946829020799138da13ee764e

candidate-stream payload SHA-256 =
70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5
```

Pair-certificate hashes, in frozen order:

```text
478 =
51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b

479 =
3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408

480 =
d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9
```

All listed file, envelope, payload, manifest, and certificate identities were validated before descriptor contact against the frozen evidence contract. The three pair certificates and the family certificate were additionally recomputed and independently verified through the integer-exact witness verifier. Every recorded identity remained unchanged from the frozen evidence.

---

## 4. Execution and replay result

```text
descriptor calls completed per pass = 768
complete passes = 2
total completed descriptor calls = 1536

run1 SHA-256 =
f215fa2ec81f39426a57c65f58730d00ae721b03169d90cdaf0a6359f9c04391

run2 SHA-256 =
f215fa2ec81f39426a57c65f58730d00ae721b03169d90cdaf0a6359f9c04391

replay_byte_identical = True
valid_run = True
failure_code = absent
exit_code = 0
```

Exact response counts per completed pass:

```text
cross responses = 384
identity controls = 768
nonidentity self-shift responses = 48,384
```

Both complete passes were performed within the single runner invocation. The two canonical pass payloads are byte-identical, so the evaluation qualifies for an authoritative verdict under the frozen two-pass replay contract.

---

## 5. Pair results

Exact result for candidate 478:

```text
primary_pass = False
pair_verdict_flags =
PAIR_FULL_NOT_DUAL_ORBIT_EXTREME

full_dual_orbit_extreme = False
k0_not_extreme = True
recursive_positive = True

full_margin_vs_A =
-0.010524856493317032

full_margin_vs_B =
0.00039953581814153316

k0_margin_vs_A =
-0.0006952292788747448

k0_margin_vs_B =
-0.0007070252508075494

minimum_recursive_difference =
0.0017002566738559522
```

Exact result for candidate 479:

```text
primary_pass = False
pair_verdict_flags =
PAIR_FULL_NOT_DUAL_ORBIT_EXTREME

full_dual_orbit_extreme = False
k0_not_extreme = True
recursive_positive = True

full_margin_vs_A =
-0.009054767777711928

full_margin_vs_B =
0.001506286472729712

k0_margin_vs_A =
-0.0006430114859614479

k0_margin_vs_B =
-0.0006420622902593058

minimum_recursive_difference =
0.0023403454873519147
```

Exact result for candidate 480:

```text
primary_pass = False
pair_verdict_flags =
PAIR_FULL_NOT_DUAL_ORBIT_EXTREME

full_dual_orbit_extreme = False
k0_not_extreme = True
recursive_positive = True

full_margin_vs_A =
-0.008250487647955468

full_margin_vs_B =
0.004602732586142265

k0_margin_vs_A =
-0.0007804290219665155

k0_margin_vs_B =
-0.0007675552898132868

minimum_recursive_difference =
0.0012022793897058803
```

---

## 6. Family verdict

```text
strong_pass_count = 0

family_verdict =
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Classification of this result:

```text
VALID AUTHORITATIVE FROZEN-FAMILY NEGATIVE
```

This result is not:

```text
execution failure
invalid evaluation
null result
PsiTRS total failure
proof that recursion contributes nothing
proof that all higher-order order sensitivity is absent
```

The run completed validly, replayed byte-identically, and produced a well-formed frozen-family verdict. The negative is a genuine, valid outcome of the exact preregistered contract, not a defect of the evaluation.

---

## 7. Required interpretation

Strongest supported reading:

```text
All three frozen pairs independently produced the same preregistered gate pattern:

full dual-orbit extreme = False
k0 not extreme = True
recursive positive at every matched start = True
```

Recorded structure of that pattern:

```text
For every pair, the full PsiTRS cross mean exceeded member B's complete nonidentity self-orbit maximum but did not exceed member A's complete nonidentity self-orbit maximum.

Member A was therefore the blocking self-orbit reference for all three frozen pairs.

The k0 cross response remained non-extreme against both members for all three pairs.

The recursive full-minus-k0 contribution was strictly positive at every one of the 64 matched starts for all three pairs.

Nevertheless, the exact preregistered strong F3 pair criterion required the full response to exceed both members' complete self-orbit maxima.

Because that dual-orbit requirement failed for all three pairs, strong_pass_count was zero and the exact frozen-family strong-order hypothesis was not supported.
```

The margins in §5 make the pattern explicit: for every pair `full_margin_vs_B > 0` while `full_margin_vs_A < 0`, so the full cross mean cleared member B but not member A, and the conjunctive dual-orbit gate failed. Every `minimum_recursive_difference` is strictly positive, confirming the recursive-positive condition held at all matched starts.

Explicit distinction:

```text
The result does not mean that PsiTRS produced no structured effect.

It means that the observed recursive-positive cross-pair effect was insufficient to clear the stricter dual-member complete self-orbit extremeness gate.
```

---

## 8. Limits and non-claims

This findings record must not claim:

```text
true vision
perception
temporal-order perception
recursive-time mechanism proof
higher-order consciousness
scientific significance
physics emergence
general PsiTRS failure
general impossibility of order sensitivity
failure for witness families not frozen here
failure under other valid preregistered contracts
production readiness
```

The result must not be weakened by inventing a new post hoc success criterion.

This document does not authorize:

```text
threshold adjustment
median substitution
member-A exclusion
one-sided self-orbit comparison
witness replacement
family replacement
new starts
alternate rotation
alternate controls
new ranking
third pass
rerun
```

Any future hypothesis must be a genuinely new preregistered study. It must not be a reinterpretation or rescue of this run. The recorded margins may inform the design of a separate preregistered study, but they may not be converted into a passing criterion for this frozen family.

---

## 9. Retained canonical artifacts

Exact result directory:

```text
research/brainvision/results/algebraic_n64_primary_v0_1_f3_evaluation_v0_1/
```

Exact canonical result:

```text
algebraic_n64_primary_v0_1_f3_evaluation_result.json
```

```text
size = 10,784,993 bytes

whole-file SHA-256 =
51e7cd8087050428c2559262764044624fcb84e19576b5f682bae3ca5b59fd7b
```

Exact operator summary:

```text
algebraic_n64_primary_v0_1_f3_evaluation_summary.txt
```

```text
size = 2,430 bytes

whole-file SHA-256 =
43a19f5ca7d1e22491bfae209603b4f595b17c886a9d4320346ef2aa4a129daf
```

Recorded artifact state:

```text
the final directory exists
the exact two authorized files exist
the staging directory is absent
publication completed by staging-to-final atomic rename
the canonical JSON is authoritative
the summary is operator convenience only
```

These files are immutable retained evidence. This document does not regenerate, edit, rename, replace, delete, normalize, or reserialize either artifact.

Committing the result files is not authorized. It may occur only under a later docs-only evidence-publication decision that explicitly permits it.

---

## 10. Project boundaries

Preserve:

```text
offline
quarantined
non-runtime
non-production
non-live
non-scientific-claim lane
FORMAL_HOLD active
Mode_0 active
```

The production kernel remains immutable:

```text
torment_service/kernel/
torment_service/memory_kernel.py
torment_service/fabric.py
```

Recorded operational boundary of the run:

```text
freezer invoked = False
generator invoked = False
old N64 evaluation invoked = False
scientific interpretation performed by runner = False
production integration performed = False
```

The authorized operation was a self-contained offline PsiTRS descriptor evaluation of a family that was selected and frozen descriptor-blindly. It contacted none of the prohibited production or live surfaces.

---

## 11. Disposition and next state

```text
A. RECORD VALID AUTHORITATIVE FROZEN-FAMILY F3 NEGATIVE
```

Next-state summary:

```text
AUTHORITATIVE_F3_EVALUATION_COMPLETE = True
AUTHORITATIVE_F3_EVALUATION_VALID = True
AUTHORITATIVE_F3_REPLAY_BYTE_IDENTICAL = True
AUTHORITATIVE_F3_STRONG_PASS_COUNT = 0
AUTHORITATIVE_F3_FAMILY_VERDICT =
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY

F3_EXECUTION_AUTHORIZED = consumed
F3_RERUN_AUTHORIZED = False
FROZEN_FAMILY_PSITRS_CONTACT = True
SCIENTIFIC_INFERENCE_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

Recommended commit subject after review:

```text
docs(research): record frozen N64 F3 evaluation findings
```

`FORMAL_HOLD` and `Mode_0` remain active.

No evaluator rerun occurred while preparing these findings. No frozen witness contacted PsiTRS while preparing these findings. The environment gate remained unset. Neither retained F3 artifact was modified. The production TORMENT kernel remained untouched.

*End — TORMENT Brainvision Algebraic N=64 PRIMARY_V0_1 Frozen-Family F3 Evaluation Findings v0.1. Docs-only. Records one completed authoritative valid frozen-family negative under the exact preregistered F3 contract. The one-run authority is consumed; no rerun, rescue criterion, scientific inference, production integration, or kernel modification is authorized.*
