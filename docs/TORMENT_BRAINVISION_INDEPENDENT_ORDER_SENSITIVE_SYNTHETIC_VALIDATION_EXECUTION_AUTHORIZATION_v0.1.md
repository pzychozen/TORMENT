# TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Execution Authorization v0.1

## Document status

```text
document_type = docs-only one-run execution authorization
authorization_stage = S3B (synthetic-validation execution)
synthetic_validation_execution_authorized_by_committed_document = deferred until commit + operator order
real_frozen_manifest_contact_authorized = deferred until commit + operator order
runner_implementation = frozen at Stage S3A (see Section 2)
```

Authoritative repository baseline (frozen S3A runner-implementation commit):

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch = main
frozen base commit = 9bd02b4793bf683a4ae2e390ae7601b096cc90e8
commit subject = research(brainvision): implement synthetic validation runner
Python required for execution = 3.11.15
```

This document authorizes exactly one future authoritative synthetic-validation runner invocation against the frozen synthetic-fixture family, and only once this document is the committed authorization HEAD and Hilmir gives a separate explicit invocation order. It authorizes nothing else.

No synthetic-validation runner, descriptor function, test, generator, freezer, manifest read, fixture evaluation, publication, or project-module function was executed while preparing this document. No real frozen manifest byte was read. No Git command was run. Exactly one file — this document — was created; no runner, descriptor, test, fixture, manifest, result, kernel, service, or production file was modified.

---

## 0. Decision

```text
A. EXACTLY ONE FUTURE AUTHORITY-CONSUMING INDEPENDENT ORDER-SENSITIVE
   SYNTHETIC-VALIDATION RUN IS AUTHORIZED THROUGH THE SOLE PERMITTED
   INVOCATION SHAPE, AGAINST THE FROZEN SYNTHETIC-FIXTURE FAMILY, AND ONLY
   WHILE THIS DOCUMENT IS THE COMMITTED AUTHORIZATION HEAD AND ONLY AFTER
   HILMIR'S SEPARATE EXPLICIT INVOCATION ORDER.
```

This document authorizes exactly one future authoritative synthetic-validation operation, performed by exactly this invocation:

```text
python research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
```

It authorizes only that exact invocation shape, one authority-consuming deterministic two-pass validation, evaluation of the one fixed positive fixture and the exactly eight frozen first-eight synthetic pairs, publication of the exact three reserved outputs, and post-run read-only inspection and findings preparation. It authorizes nothing else.

This document does not itself instruct Claude, Codex, GPT, or any automated agent to execute the runner. Preparing this draft is not execution authority. The uncommitted working-tree document is not executable authority. Committing this document does not automatically trigger execution. Runner execution becomes authorized only once this document is reviewed, committed as the sole changed file, pushed, is the latest commit affecting its own exact committed path at HEAD (Section 7), and Hilmir has issued a separate explicit final invocation order.

---

## 1. Stage split and why S3B is separate

```text
S3A = synthetic-validation runner and runner-test implementation authorization (complete, committed, accepted, frozen)
S3B = this one-run synthetic-validation execution authorization
```

Stage S3 was split so that the runner implementation exists, is adversarially reviewed, and has committed, frozen identities before any real-manifest scientific exposure is authorized. Stage S3A produced identity-frozen runner code that made no real-manifest contact. This Stage S3B document binds the frozen runner and runner-test identities, binds the frozen synthetic-manifest identity, and authorizes exactly one authoritative synthetic-validation invocation. The split does not weaken, amend, or reinterpret the challenger specification or the frozen synthetic family.

---

## 2. Governing documents and completed prerequisites

Governing documents:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_FINDINGS_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

The Stage S3A runner-implementation authorization remains governing for runner architecture, the import/side-effect boundary, the complete synthetic gate, Method B for the exhaustive nuisance controls, the ordered failure vocabulary, deterministic replay, and the reserved publication paths and write policy. Where any wording here appears looser than the challenger specification or the Stage S3A authorization, those governing documents govern.

Completed prerequisite state:

```text
S0 specification accepted
S1 synthetic fixture family frozen and its findings recorded (family_frozen = true)
S2 descriptor implemented, bounded-tested, adversarially reviewed, committed, and frozen
S3A synthetic-validation runner and runner-test implemented, bounded-tested (non-authoritative), reviewed, committed, accepted, and frozen
CHALLENGER_DESCRIPTOR_IMPLEMENTATION_FROZEN = True
CHALLENGER_SYNTHETIC_VALIDATION_RUNNER_IMPLEMENTATION_FROZEN = True
```

No scientific result or challenger-detection claim follows from the completed implementation or from the bounded non-authoritative tests. The frozen synthetic-fixture family establishes only that a procedure froze the first eight eligible pairs under predetermined descriptor-blind rules; it is not challenger detection, not Brainvision order sensitivity, and not F3 repair.

---

## 3. Reviewed repository baseline and the future execution HEAD

This authorization was reviewed against the frozen Stage S3A runner-implementation checkpoint:

```text
branch = main
frozen base commit = 9bd02b4793bf683a4ae2e390ae7601b096cc90e8
commit subject = research(brainvision): implement synthetic validation runner
Python required for execution = 3.11.15
```

This reviewed baseline commit is the runner-implementation checkpoint. It is not the future execution HEAD.

The future execution HEAD will be the later docs-only commit that adds this authorization document as its sole changed file. That future commit identity must not be guessed, precomputed, or embedded anywhere in this document. It is resolved non-circularly by the runner through read-only Git at execution time (Section 7).

```text
the execution-authorization commit identity must not be guessed or precomputed
the eventual execution HEAD must not be guessed or precomputed
each exact commit identity is recorded only after that commit and push
```

---

## 4. Exact one-file allowlist and docs-only commit boundary

Exactly one file is created by this task, and no other:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
```

The commit that carries this execution authority must contain exactly this one changed file and nothing else. It must not create, modify, rename, or delete any source, test, result, evidence, staging, configuration, fixture, manifest, registry, pointer, findings, helper, or other documentation file, including but not limited to:

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
research/brainvision/independent_order_sensitive_descriptor_v0_1.py
research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
the frozen synthetic manifest and its freeze evidence
research/brainvision/results/ result, staging, or retained evidence
historical F3 modules and their retained evidence
PsiTRS modules
torment_service/ and torment_service/kernel/ files
the TORMENT memory system
```

A single-file docs-only commit is required both to keep the change reviewable and to make the non-circular execution-HEAD rule (Section 7) provable: the latest commit affecting the exact authorization path must equal HEAD. This task performed no Git operation; committing is a later, separate operator step.

---

## 5. Frozen runner, runner-test, descriptor, descriptor-test, and configuration identities

The runner and runner test are frozen at their committed Stage S3A identities. Git-object identity and raw-file SHA-256 identity are recorded separately and are both mandatory. A mismatch in either identity blocks execution authorization as a pre-contact refusal.

Runner

```text
artifact role = runner
path = research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
Git blob = e4328235f1135ee22e9e31bab8140a828e4e46fb
raw SHA-256 = 5db33fa3a1eee1e47dce93c98bbe42e8c1dc83ad37b09c85e503f99bb6a0c86e
```

Runner test

```text
artifact role = runner_test
path = research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_1.py
Git blob = 25a4ff122afde6fc005d92246a286aa93b1de872
raw SHA-256 = 421786d8760945557d7b1afa0a11c53af8f247afd45d0db8455d28c1bf3bd466
```

The frozen Stage S2 descriptor and its test are bound by their committed identities and must not be modified. They are outside every allowlist in this document. Their frozen identities, recorded in the governing descriptor-implementation and Stage S3A authorizations, are:

```text
descriptor
path = research/brainvision/independent_order_sensitive_descriptor_v0_1.py
Git blob = f9a369e6c7f09204092155b99638f8cec4e8b1ae
raw SHA-256 = cdd313a0dfc3c71b33c4b9964397a5d0710427d612b4d781a46353a4d2522be9

descriptor_test
path = research/brainvision/test_independent_order_sensitive_descriptor_v0_1.py
Git blob = 9054b36aebf32014053d2a877b0cb7eb42dce6fc
raw SHA-256 = 3eed5c7e482bad65ab662941bc3b3bc04477e9669ae6e067d93bea4e524f3a94
```

Configuration identity

The committed runner's inert configuration identity was captured without invoking `main()`, reading the manifest, evaluating fixtures, or publishing results:

```text
CONFIGURATION_SHA-256 = fbea00f09d5843694a8056e533a2fd6c7637a994b162f47786fe53622a04e9aa
```

Capture evidence:

```text
Python = 3.11.15
command exit code = 0
manifest bytes read = 0
fixtures evaluated = 0
runner main invoked = false
publication attempted = false
files modified = none
```

Identity doctrine:

```text
Git-object identity and raw-file SHA-256 identity are separate and mandatory identities.
Neither substitutes for the other.
A mismatch in either identity is a fail-closed pre-contact refusal before any real manifest byte is read.
```

At execution time the runner reads the runner, runner-test, and configuration expected values from the machine-readable binding in Section 6 of this document, and validates the descriptor and descriptor-test identities against the exact constants compiled into the committed runner. The descriptor and descriptor-test identities are not part of the seven-field binding; they remain checked through the committed runner constants. Any change to the runner, the runner test, the frozen descriptor, the frozen descriptor test, or the configuration invalidates this authorization and requires a new review and a refreshed execution-authorization commit at this same frozen document path.

---

## 6. Machine-readable authorization binding

Exactly one copy of the following binding block is embedded in this document. The begin marker, the end marker, the field order, the field spelling, the lowercase hexadecimal values, and the absence of spaces around `=` are exact and must not be altered.

```text
BEGIN-SYNTHETIC-VALIDATION-EXECUTION-AUTHORIZATION-BINDING-v0.1
authorization_schema=torment-brainvision-independent-order-sensitive-synthetic-validation-execution-authorization-v0.1
authorization_version=0.1
runner_git_blob=e4328235f1135ee22e9e31bab8140a828e4e46fb
runner_raw_sha256=5db33fa3a1eee1e47dce93c98bbe42e8c1dc83ad37b09c85e503f99bb6a0c86e
runner_test_git_blob=25a4ff122afde6fc005d92246a286aa93b1de872
runner_test_raw_sha256=421786d8760945557d7b1afa0a11c53af8f247afd45d0db8455d28c1bf3bd466
configuration_sha256=fbea00f09d5843694a8056e533a2fd6c7637a994b162f47786fe53622a04e9aa
END-SYNTHETIC-VALIDATION-EXECUTION-AUTHORIZATION-BINDING-v0.1
```

The binding contains exactly seven fields, once each, in exactly the displayed order: the authorization schema, the authorization version, the runner Git blob, the runner raw SHA-256, the runner-test Git blob, the runner-test raw SHA-256, and the configuration SHA-256. There is exactly one begin marker and exactly one end marker, no duplicate binding field anywhere else in this document, no alternate machine-binding block, no Markdown prefix inside the block, no spaces around `=`, and no trailing machine-readable field. Every other occurrence of these value names elsewhere in this document is deliberately written in spaced, human-readable prose form (for example, "runner Git blob" and "configuration SHA-256") so that no surrounding line can be parsed as an additional binding field.

The binding is the sole source of exactly these five expected values: the runner Git blob, the runner raw SHA-256, the runner-test Git blob, the runner-test raw SHA-256, and the configuration SHA-256. None of these may be supplied through the CLI, environment variables, stdin, external files, or runtime choices.

Two identities are deliberately NOT embedded in the binding: the repository execution HEAD and any authorization-document Git blob. The repository execution HEAD cannot be embedded inside the commit whose tree contains this document without a fixed point; instead, the runner verifies through read-only Git that the latest commit affecting the exact authorization path equals the repository execution HEAD (Section 7). The runner does not resolve, compare, or record an authorization-document Git blob; no such field exists, and none is supplied by or compared against any embedded binding value.

The execution envelope records:

```text
repository_execution_head
s3b_authorization_path
binding_identity_sha256
```

and does not record an authorization-document Git blob.

Parsing is a pure deterministic read over the authorization document's working-tree bytes, performed only after the runner has required a clean working tree and verified that the latest commit affecting the exact authorization path equals HEAD. Those two requirements — the clean-tree requirement and the exact latest-path-commit rule — bind the working-tree document to the committed authorization state; Git does not supply the document bytes. The runner never imports, executes, or evaluates the authorization document.

---

## 7. Non-circular execution-HEAD rule and required pre-contact checks

Before opening the real frozen manifest, and in a fixed fail-closed order, the future authoritative runner must successfully verify all of the following. Failure of any one of these pre-contact checks must refuse before any real manifest byte is read.

```text
Python = 3.11.15
repository root is exact
branch = main
working tree is clean (including ordinary untracked files)
HEAD = origin/main
authorization document exists at its exact committed path
authorization document latest commit = HEAD
runner Git and raw identities match
runner-test Git and raw identities match
descriptor Git and raw identities match
descriptor-test Git and raw identities match
CONFIGURATION_SHA-256 matches
static source boundaries pass
manifest path identity is exact
final result directory is absent
staging directory is absent
argv shape is exact (no arguments, no flags, no configuration path)
stdin is empty
```

The latest-path-commit check uses an exact frozen read-only Git operation equivalent to:

```text
git log -1 --format=%H -- docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md
```

A missing result, a malformed result, or a result unequal to HEAD is a fail-closed pre-contact refusal. The repository execution HEAD is recorded into the execution envelope at execution time, never guessed and never embedded; the runner does not resolve, compare, or record an authorization-document Git blob.

Consequence — a later unrelated commit closes execution authority even if the document bytes are unchanged. Once any commit that does not touch this exact authorization path is added on top, the latest commit affecting the authorization path no longer equals HEAD, so the rule fails closed. Byte-identical document content does not keep authority alive; authority lives only while this document's own commit is the current HEAD.

A pre-contact refusal, and any pre-contact validation failure, does not consume the one-run scientific authority, because no real manifest byte was read. No manifest is opened merely to investigate a pre-contact refusal.

---

## 8. Exact invocation and CLI boundary

The runner is invoked in exactly one shape, from the repository root:

```text
python research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py
```

The command accepts:

```text
no arguments
no flags
no configuration path
no environment-supplied identity
empty stdin
```

Any positional argument, any option, any flag, or any non-empty stdin is a fail-closed pre-contact refusal. No environment variable is read or accepted as an identity or configuration input, and environment values cannot override the frozen identities, configuration, control plan, manifest path, or publication paths; the runner does not inspect or reject arbitrary environment variables merely because they are set. The presence of an execution entry point does not itself authorize invocation. Invocation is authorized only by this committed document (once it is the authorization HEAD) plus a separate explicit final operator instruction from Hilmir. This command must not be executed during this task; committing this document must not automatically trigger execution.

---

## 9. Frozen synthetic manifest identity

The single authoritative run reads exactly, and only, the frozen synthetic manifest bound here. These are provenance/binding constants, validated by the runner against the constants compiled into its committed source; they are not part of the seven-field binding of Section 6.

```text
manifest path = research/brainvision/results/independent_order_sensitive_synthetic_fixture_freeze_v0_1/independent_order_sensitive_synthetic_fixture_freeze_manifest_v0_1.json
external manifest SHA-256 = 05ce02af1c1a4b508e9a6566c9ff638849039df5caa45479858e634e2a117404
manifest payload SHA-256 = 56a141bd13937caa6ac800ab8c9c12229f6bf75ee97ab490a26844664a65b4b9
freeze configuration SHA-256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
K_synthetic = 8
```

During the single authorized run the runner must read only the exact bound manifest path, verify the external file SHA-256 before parsing, parse canonical JSON, reconstruct and verify the manifest payload SHA-256, verify schema and the fixed freeze-configuration identity, require family_frozen = true, require exactly one fixed fixture, require exactly eight accepted fixtures, and preserve the frozen accepted-fixture order. The descriptor function receives only validated raw 64-entry binary vectors; it must never receive manifest metadata, fixture indices, seed tuples, certificates, or pair labels. No fixture may be removed, reordered, replaced, edited, reconstructed from another source, selected by descriptor output, or skipped after failure.

The frozen fixture freezer must never be rerun, retried, resumed, replaced, or regenerated. Its one-run authority was already consumed when the family was frozen; this document does not reopen it.

---

## 10. One-run authority semantics

The one-run scientific authority is consumed at the first real frozen-manifest byte read, not before. This document distinguishes the following states exactly.

Before first real manifest-byte contact:

```text
authority_consumed = false
manifest_contact_count = 0
```

A pre-contact refusal or validation failure does not consume the one-run scientific authority, because no real manifest byte was read. No manifest is opened merely to investigate a pre-contact refusal.

At first real manifest-byte contact:

```text
authority_consumed = true
manifest_contact_count = 1
```

From this point onward, within the same invocation and for any later invocation:

```text
no retry
no rerun
no resume
no replacement invocation
no cleanup for another attempt
```

Second read inside the same invocation. The runner performs its required fresh replay read (pass 2 independently reloads and re-verifies the manifest) inside the same consumed invocation:

```text
authority_consumed = true
manifest_contact_count = 2
```

A third real manifest read is prohibited and rejected. A failure after first contact must retain durable staging or failure evidence; it must not be erased to enable another attempt. After the one-run authority is consumed, no rerun, retry, resume, recovery execution, third pass, replacement scan, or repeated publication is authorized. A new run would require a separately reviewed and explicitly approved future authorization decision. This document provides no such authority.

---

## 11. Complete synthetic scientific gate

The single authorized run must retain the exact frozen gate, with no sampling, subset reduction, random selection, or early-stop shortcut. The gate passes only when all of the following hold:

```text
all malformed and degenerate controls correct
all identity controls correct
all nuisance controls correct
fixed positive fixture distinguished
8 of 8 frozen generated pairs distinguished
two complete pass bundles byte-identical
all input, boundary, serialization, and publication checks valid
```

Deterministic replay. The sole authoritative invocation performs two separate real-manifest reads. Each pass independently validates freshly read manifest bytes and constructs a new parsed manifest and a new scientific pass bundle. Pass 2 does not reuse pass 1's scientific result bundle as its own output. The two complete canonical pass bundles are compared byte-for-byte; any mismatch is a replay failure. The runner may reuse the same frozen immutable control-plan object and deterministic module-level permutation or plan caches across the two passes; this does not substitute pass-1 scientific output for pass-2 evaluation. The exhaustive nuisance controls use the preregistered Method B exactly as frozen by the Stage S3A authorization; the runner-local integer-exact reference recomputation that provides the observed side of each exhaustive comparison must not reuse descriptor implementation helpers.

No weakening is permitted:

```text
7 of 8 = scientific failure
no majority threshold
no tolerance
no aggregate score substitution
no fixture removal
no tuning
no sampling
no floating-point relaxation
```

A failed or invalid gate does not authorize descriptor modification, fixture removal, threshold changes, lag selection, normalization changes, or automatic rerun. A v0.1 failure is a valid negative result. Any future v0.2 must be separately specified and must not overwrite v0.1.

---

## 12. Exact result kinds, semantics, and exit-code mapping

The single authorized run may produce exactly these result kinds:

```text
SYNTHETIC_GATE_PASSED
SYNTHETIC_GATE_FAILED
SYNTHETIC_GATE_INVALID
```

Semantics:

```text
SYNTHETIC_GATE_PASSED =
  the complete exact synthetic gate passed

SYNTHETIC_GATE_FAILED =
  a valid scientific miss, including failure to distinguish all 8 generated pairs

SYNTHETIC_GATE_INVALID =
  an integrity, identity, boundary, execution, serialization, replay, or
  publication-invalid outcome
```

A valid scientific miss must never be rewritten as an integrity failure. A SYNTHETIC_GATE_INVALID outcome must never be relabelled as a scientific miss. A pre-contact refusal — a fail-closed identity or boundary refusal, or an unresolved pre-contact exception, occurring before any real manifest byte is read — publishes no scientific result kind and does not consume the one-run authority; it exits 2 and is distinct from a post-contact SYNTHETIC_GATE_INVALID outcome, which exits 3 with the authority consumed.

Expected runner exit-code mapping:

```text
0 = SYNTHETIC_GATE_PASSED
1 = SYNTHETIC_GATE_FAILED
2 = SYNTHETIC_VALIDATION_REFUSED before authority consumption;
    no scientific result kind is published;
    authority_consumed remains false;
    manifest_contact_count remains 0
3 = SYNTHETIC_GATE_INVALID
```

Exit 2 and exit 3 are distinct:

```text
exit 2 =
pre-contact refusal or unresolved pre-contact exception;
no real manifest contact;
authority unconsumed

exit 3 =
post-contact SYNTHETIC_GATE_INVALID outcome;
authority consumed
```

The authority-consuming result exits are 0, 1, and 3. A pre-contact refusal exits with 2 and produces no scientific result kind. The future operator must capture `%ERRORLEVEL%` immediately after the single invocation, before running any other command, and record it in the execution receipt.

---

## 13. Publication paths and write policy

Publication paths are frozen exactly:

```text
final directory = research/brainvision/results/independent_order_sensitive_synthetic_validation_v0_1
staging directory = research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_1.staging
```

Exact output files:

```text
independent_order_sensitive_synthetic_validation_result_v0_1.json
independent_order_sensitive_synthetic_validation_execution_envelope_v0_1.json
independent_order_sensitive_synthetic_validation_summary_v0_1.txt
```

Required publication sequence:

```text
exclusive staging creation
staging confirmed empty
write exactly three files
close and reread
verify exact bytes and SHA-256
verify exact file set
atomic staging-to-final promotion
mark published only after promotion
```

An existing staging directory or an existing final directory must cause a pre-contact refusal before any real manifest byte is read. A publication failure after first manifest contact must leave the staging or failure state retained; it must not be erased and must not enable another run. No overwrite, merge, append, or destructive rollback of promoted evidence is permitted. A partial staging set is failure evidence, never a permitted successful file set.

---

## 14. Cost and execution posture

Recorded execution posture:

```text
classification = HIGH_BUT_EXECUTABLE
admitted base sequences = 18
transformations per base = 6209
two-pass materialized checks = 223524
complete vectors computed = up to 147492
complete-vector comparisons = 596844
base canonicalizations = 36
dense 64x3906 loops = 0
```

The future execution receipt must record wall-clock duration. This document does not authorize reduced coverage, parallel substitution, sampling, floating-point substitution, reuse of descriptor helpers for the independent reference side, or any alteration of the preregistered Method B. Full enumeration, integer-exact mathematics, single-process and single-threaded execution, and exact equality remain mandatory.

---

## 15. Authorization limits

This document authorizes only:

```text
one future authoritative synthetic-validation runner invocation
two manifest reads within that single invocation
evaluation of the fixed positive fixture
evaluation of exactly the frozen first-eight synthetic fixture pairs
publication of the exact three reserved outputs
post-run read-only inspection and findings preparation
```

It does not authorize:

```text
execution during document drafting
execution immediately upon commit
source changes
runner changes
test changes
descriptor changes
fixture changes
manifest changes
freezer rerun
additional attempts
F3 contact
PsiTRS contact
prerecorded evaluation
production integration
TORMENT memory integration
kernel modification
service/runtime contact
live visual ingestion
```

---

## 16. Permanent Brainvision and TORMENT boundary

Project posture is preserved exactly:

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

There is no contact with or modification of the production kernel (`torment_service/kernel/`), production TORMENT memory, live memory functionality, service or runtime surfaces, prompt or action systems, autonomy systems, the historical frozen F3, PsiTRS, or prerecorded-video evaluation. This authorization does not authorize production integration, live capture, gameplay integration, caching architecture, or TORMENT memory integration. This descriptor-blind synthetic-validation operation does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen F3 result. Brainvision must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route.

---

## 17. Required authority-state declarations

Before this document is committed — its present drafted, uncommitted state:

```text
CHALLENGER_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZED = False
CHALLENGER_REAL_SYNTHETIC_MANIFEST_CONTACT_AUTHORIZED = False
CHALLENGER_FIXED_POSITIVE_FIXTURE_EVALUATION_AUTHORIZED = False
CHALLENGER_FROZEN_SYNTHETIC_FAMILY_EVALUATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_RESULT_PUBLICATION_AUTHORIZED = False
```

After the exact document is reviewed, accepted, committed, and synchronized — but before Hilmir issues the separate invocation order — the document may establish:

```text
CHALLENGER_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZED = True
CHALLENGER_REAL_SYNTHETIC_MANIFEST_CONTACT_AUTHORIZED = True
CHALLENGER_FIXED_POSITIVE_FIXTURE_EVALUATION_AUTHORIZED = True
CHALLENGER_FROZEN_SYNTHETIC_FAMILY_EVALUATION_AUTHORIZED = True
CHALLENGER_SYNTHETIC_RESULT_PUBLICATION_AUTHORIZED = True
```

However, even in that committed-and-synchronized state:

```text
execution ordered = false
authority consumed = false
manifest contact count = 0
```

The committed authorization grants bounded capability but is not itself the operator's invocation order. A committed authorization HEAD is a necessary but not sufficient condition for execution; the sufficient additional condition is a separate explicit final invocation instruction from Hilmir.

Permanent posture is preserved: FORMAL_HOLD is active, Mode_0 is active, and the strong order hypothesis remains not supported by the frozen family.

---

## 18. Required closing instruction

```text
Do not execute the authoritative runner automatically after this document is committed.

Wait for Hilmir's separate explicit invocation order.

Until that order is issued:

authority_consumed = false
manifest_contact_count = 0
```

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Validation Execution Authorization v0.1. Docs-only, Stage S3B. Authorizes exactly one future authoritative synthetic-validation run through the sole frozen invocation shape `python research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py`, against the frozen synthetic-fixture family, and only once this document is the committed authorization HEAD and Hilmir gives a separate explicit final invocation instruction. The one-run scientific authority is consumed only at the first real frozen-manifest byte read; a pre-contact refusal consumes nothing. Exactly two manifest reads are permitted within the single invocation; a third is prohibited. The complete synthetic gate may not be weakened (7 of 8 is a scientific failure; no majority, tolerance, aggregate score, fixture removal, tuning, sampling, or floating-point relaxation). Result kinds are exactly SYNTHETIC_GATE_PASSED, SYNTHETIC_GATE_FAILED, and SYNTHETIC_GATE_INVALID; the authority-consuming result exits are 0 (PASSED), 1 (FAILED), and 3 (INVALID), while a pre-contact refusal instead exits 2, produces no scientific result kind, and leaves the one-run authority unconsumed. A valid scientific miss is never rewritten as an integrity failure. No synthetic-validation runner, descriptor, test, generator, freezer, manifest read, fixture evaluation, publication, or project-module function was executed while preparing this document, and no Git command was run. Exactly one file was created and no runner, descriptor, test, fixture, manifest, result, kernel, service, or production file was modified. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted; Brainvision remains offline, quarantined, non-production, non-service, non-kernel, and non-memory-integrated.*
