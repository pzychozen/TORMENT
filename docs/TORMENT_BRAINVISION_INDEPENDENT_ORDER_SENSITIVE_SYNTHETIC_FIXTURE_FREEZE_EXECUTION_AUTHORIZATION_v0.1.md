# TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Execution Authorization v0.1

## 0. Decision

```text
A. EXACTLY ONE FUTURE AUTHORITY-CONSUMING INDEPENDENT ORDER-SENSITIVE
   SYNTHETIC-FIXTURE FREEZE OPERATION IS AUTHORIZED THROUGH THE SOLE PERMITTED
   INVOCATION SHAPE, AND ONLY WHILE THIS DOCUMENT IS THE COMMITTED AUTHORIZATION
   HEAD.
```

This document authorizes exactly one future authoritative independent order-sensitive synthetic-fixture freeze operation, performed by exactly this invocation:

```text
python research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

It authorizes only that exact invocation shape and one authority-consuming deterministic two-pass operation. It authorizes nothing else.

This document does not itself instruct Claude, Codex, GPT, or any automated agent to execute the runner. Execution remains paused after this document is drafted, reviewed, committed alone, and pushed. Actual invocation requires a separate explicit final operator instruction from Hilmir.

Preparing this draft is not execution authority. The uncommitted working-tree document is not executable authority. Runner execution becomes authorized only once this document is reviewed, committed as the sole changed file, pushed, and is the latest commit affecting its own exact committed path at HEAD (Section 7).

No runner, generator, verifier, freeze-library operation, canonical seed iterator, manifest builder, or project-module function was executed while preparing this document. No Git command was run while preparing this document.

---

## 1. Governing documents and completed prerequisites

This execution authorization is governed by the independent synthetic-fixture branch documents, not by the older algebraic freezer branch:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_DESCRIPTOR_CHALLENGER_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_RUNNER_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

Section 8A of the runner-implementation authorization is authoritative for the execution-authorization binding, the exact execution-authorization document path, the exact invocation and CLI boundary, the non-circular execution-HEAD rule, the binding parsing grammar and rejection mapping, and the sole-source identity rule. This document conforms to Section 8A; where any wording here appears looser than Section 8A, Section 8A governs.

Completed prerequisite state:

```text
S1A specifications accepted
S1B verifier / generator / freeze library implemented and accepted
S1B bounded tests implemented and accepted (focused suite green)
S1C runner and runner test implemented and accepted (runner-implementation authorization closed)
```

The accepted synthetic-fixture branch has no retained candidate stream. The authoritative operation scans the canonical seed space directly under the frozen configuration; no retained-stream facts from the earlier algebraic freezer branch are carried into this branch.

---

## 2. Reviewed repository baseline

This authorization was prepared against the completed runner-implementation checkpoint:

```text
branch = main
HEAD = 74a27ad8e0899405c8839081daae9b9143a08860
origin/main = 74a27ad8e0899405c8839081daae9b9143a08860
working tree = clean
commit subject = research(brainvision): implement synthetic fixture freeze runner
Python version required for execution = 3.11.15
```

This reviewed baseline HEAD is the completed runner-implementation checkpoint. It is not the future execution HEAD.

The future execution HEAD will be the docs-only commit that adds this authorization document as its sole changed file. That future commit identity must not be guessed, precomputed, or embedded anywhere in this document. It is resolved non-circularly by the runner through read-only Git at execution time (Section 7).

```text
the execution-authorization commit identity must not be guessed or precomputed
the eventual execution HEAD must not be guessed or precomputed
each exact commit identity is recorded only after that commit and push
```

---

## 3. Frozen runner, runner-test, S1B, and configuration identities

The runner and runner test are frozen at their committed identities. Git-object identity and Windows raw-file SHA-256 identity are recorded separately and are both mandatory.

Runner

```text
artifact role = runner
artifact id = independent-order-sensitive-synthetic-fixture-freeze-runner-v0.1
path = research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = 2af5e43e978fdfb31ecb531bc896b9faca8a0aad
Windows raw SHA-256 = 5b4a146401557cd7037e12ace4a408e8d6c85d72d147daf5e286a34353b57549
```

Runner test

```text
artifact role = runner_test
artifact id = independent-order-sensitive-synthetic-fixture-freeze-runner-test-v0.1
path = research/brainvision/test_brainvision_run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
Git blob = 5184b3cfc4091270951b10de296cbc9db3b15ece
Windows raw SHA-256 = 18f85d446f2af22240a2d8921a5390328774d04fa9b2107b502f2ac68da0be27
```

Configuration

```text
configuration SHA-256 = 5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
```

The five accepted S1B implementation-file identities remain frozen exactly as recorded in Section 3 of the runner-implementation authorization (verifier, generator, freeze library, verifier test, generator/freeze test). That section is their normative authorization source, and the exact values are compiled into the committed runner constants. At execution time, the runner reads the runner, runner-test, and configuration expected identities from the machine-readable binding in Section 6 of this document.

Identity doctrine:

```text
Git blob identity and Windows raw-file SHA-256 identity are separate and mandatory identities.
Neither substitutes for the other.
A mismatch in either identity blocks execution authorization (HASH_IDENTITY_FAILURE / pre_contact).
```

Any change to the runner, the runner test, the frozen S1B sources, or the configuration invalidates this authorization and requires a new review and a new authorization document.

---

## 4. Docs-only authorization-commit boundary

The commit that carries execution authority must add exactly one documentation file and nothing else:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md
```

That commit must not create, modify, rename, or delete any source, test, result, evidence, staging, configuration, helper, or other documentation file, including but not limited to:

```text
the committed runner and runner test
the five frozen S1B implementation files
research/brainvision/results/results.csv
research/brainvision/results/results.json
any research/brainvision results, staging, or retained evidence
the challenger descriptor
historical F3 modules and their retained evidence
historical asymmetry-audit modules and their retained evidence
frozen candidates 478, 479, 480
PsiTRS
torment_service/ and production-kernel files
the TORMENT memory system
```

A single-file docs-only commit is required both to keep the change reviewable and to make the non-circular execution-HEAD rule (Section 7) provable: the latest commit affecting the exact authorization path must equal HEAD.

---

## 5. Exact invocation and CLI boundary

The runner is invoked in exactly one shape, from the repository root:

```text
python research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py
```

No arguments, options, flags, configuration path, environment gate, environment-supplied identity, caller-supplied identity, or non-empty stdin is authorized. The runner reads no environment variable as an input to its decisions.

Any positional argument, any option, any flag, any attempt to supply identity or configuration through the environment, a file, or stdin, or any non-empty stdin is a fail-closed pre-contact refusal:

```text
UNAUTHORIZED_EXECUTION / pre_contact
```

The runner may contain the single execution-boundary block `if __name__ == "__main__":`. The presence of that entry point does not itself authorize invocation. Invocation is authorized only by this committed document (once it is the authorization HEAD) plus a separate explicit final operator instruction from Hilmir.

---

## 6. Machine-readable authorization binding

Exactly one copy of the following binding block is embedded in this document. The begin marker, the end marker, the field order, the field spelling, the lowercase hexadecimal values, and the absence of spaces around `=` are exact and must not be altered.

```text
BEGIN-SYNTHETIC-FIXTURE-FREEZE-AUTHORIZATION-BINDING-v0.1
authorization_schema=torment-brainvision-independent-order-sensitive-synthetic-fixture-freeze-authorization-binding-v0.1
authorization_version=0.1
runner_git_blob=2af5e43e978fdfb31ecb531bc896b9faca8a0aad
runner_raw_sha256=5b4a146401557cd7037e12ace4a408e8d6c85d72d147daf5e286a34353b57549
runner_test_git_blob=5184b3cfc4091270951b10de296cbc9db3b15ece
runner_test_raw_sha256=18f85d446f2af22240a2d8921a5390328774d04fa9b2107b502f2ac68da0be27
configuration_sha256=5f3a568bc4286136a93d9b9bac74985af4b68202373a56210eddbcfbf2625263
END-SYNTHETIC-FIXTURE-FREEZE-AUTHORIZATION-BINDING-v0.1
```

The binding contains exactly these seven fields, once each, in exactly this order:

```text
authorization_schema
authorization_version
runner_git_blob
runner_raw_sha256
runner_test_git_blob
runner_test_raw_sha256
configuration_sha256
```

The binding is the sole source of exactly these five expected values: `runner_git_blob`, `runner_raw_sha256`, `runner_test_git_blob`, `runner_test_raw_sha256`, and `configuration_sha256`. None of these may be supplied through the CLI, environment variables, stdin, external files, or runtime choices. The five S1B source identities continue to come from Section 3 of the runner-implementation authorization.

Two fields are deliberately NOT in the binding:

```text
repository_execution_head
authorization_document_git_blob
```

Neither is embedded, because both are self-referential to the commit whose tree contains this document: the document cannot canonically contain and verify its own containing-commit hash or its own Git blob without a fixed point. Both are therefore resolved non-circularly by the runner through read-only Git at execution time (Section 7) and recorded into the execution envelope. Neither is supplied by, nor compared against, any embedded binding value.

Binding grammar and rejection mapping are frozen by Section 8A.5 of the runner-implementation authorization:

```text
each field line is exactly key=value with no spaces around "="; one field per line; LF endings
exactly one begin marker and exactly one end marker; block content is exactly the enclosed lines
exactly the seven declared keys, each once, in the declared order
authorization_schema = the exact literal above; authorization_version = "0.1"
runner_git_blob, runner_test_git_blob = exactly 40 lowercase hex
runner_raw_sha256, runner_test_raw_sha256, configuration_sha256 = exactly 64 lowercase hex
duplicate / missing / extra field, bad marker, wrong order, bad hex -> UNAUTHORIZED_EXECUTION / pre_contact
well-formed binding whose bound value disagrees with the runner's independently computed value
  -> HASH_IDENTITY_FAILURE / pre_contact
```

Parsing is a pure deterministic read over the committed document bytes obtained through an exact read-only Git operation (not the working-tree copy, so working-tree newline conversion cannot affect it). The runner never imports, executes, or evaluates this document.

---

## 7. Non-circular execution-HEAD rule

Execution is authorized only when all of the following are simultaneously true:

```text
the current branch is main
HEAD equals origin/main
the working tree is clean, including ordinary untracked files
the authorization document exists at its exact committed path
the latest commit affecting that exact path equals HEAD
the authorization document's Git blob is resolved from HEAD
```

The intended authorization commit must contain only:

```text
docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md
```

Before the project-module import and any canonical contact, the runner performs, in this exact order (Section 8A.4 of the runner-implementation authorization):

```text
resolve HEAD
resolve origin/main
require HEAD == origin/main
require the exact execution-authorization path to exist in HEAD
resolve the latest commit affecting that exact path
require that path commit == HEAD
resolve the authorization document Git blob from HEAD
record HEAD as repository_execution_head
record the resolved document blob as authorization_document_git_blob
```

The latest-path-commit check uses an exact frozen read-only Git operation equivalent to:

```text
git log -1 --format=%H -- docs/TORMENT_BRAINVISION_INDEPENDENT_ORDER_SENSITIVE_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md
```

A missing result, a malformed result, or a result unequal to HEAD maps to `UNAUTHORIZED_EXECUTION / pre_contact`. A malformed resolved authorization-document Git blob maps to `HASH_IDENTITY_FAILURE / pre_contact`.

Consequence — a later unrelated commit closes execution authority even if the document bytes are unchanged. Once any commit that does not touch this exact authorization path is added on top, the latest commit affecting the authorization path no longer equals HEAD, so the rule fails closed. Byte-identical document content does not keep authority alive; authority lives only while this document's own commit is the current HEAD. Both `repository_execution_head` and `authorization_document_git_blob` are resolved this way at execution time and recorded into the envelope, never guessed and never embedded.

---

## 8. Exact authorized operation

This document authorizes exactly, and only, the following deterministic operation:

```text
repository-root execution only
main only
HEAD == origin/main
clean working tree (including ordinary untracked files)
Python 3.11.15
exact committed runner identity (Git blob and Windows raw SHA-256)
exact committed runner-test identity (Git blob and Windows raw SHA-256)
exact frozen five-file S1B source identities
exact configuration SHA-256
two fresh independent canonical passes
parallelism = 1
backtracking = false
descriptor-blind selection
fixed-fixture duplicate-key seeding
first-eight-unique-eligible-pairs selection
stop immediately after the eighth acceptance
exact pass-bundle comparison
positive finalization only after exact replay agreement
deterministic evidence publication through exclusive staging and atomic promotion
```

Each pass begins from fresh, independent state. Pass 2 must not reuse any pass-1 object:

```text
seed iterator
supports
binary arrays
certificates
triple evidence
member keys
pair keys
seen-key state
accepted records
search diagnostics
manifest objects
serialized bytes
hash values
```

No third pass, retry, resume, parallel search, backtracking, alternative selector, fixture replacement, or challenger-informed selection is authorized. Selection is descriptor-blind: the challenger descriptor is never constructed, imported, executed, or consulted during selection.

The configuration is fully frozen; no configuration value is left to runtime choice. The runner constructs the exact canonical configuration object and requires its `configuration_sha256` to equal the bound value in Section 6 before any canonical contact.

---

## 9. One-run consumption semantics

The one-run consumption threshold is defined exactly as the first real canonical-iterator contact in authoritative pass 1.

Before that threshold:

```text
a pre-contact refusal does not consume the one-run authority
no canonical seed is consumed
no staging or final evidence is created
```

A pre-contact refusal does not authorize an automatic retry. Any later invocation still requires an explicit Hilmir operator instruction and must satisfy the same unchanged authorization-HEAD conditions of Section 7. A pre-contact refusal creates no staging directory and no output files (exit 2).

At and after the first canonical-iterator contact:

```text
the single execution authority is consumed
```

It remains consumed regardless of whether the operation later produces:

```text
ACCEPTED_EIGHT
FIXED_FIXTURE_FAILURE
SEED_SPACE_EXHAUSTED
pass-1 failure
pass-2 failure
replay mismatch
comparison failure
finalization failure
publication failure
```

After consumption, no rerun, retry, resume, recovery execution, third pass, replacement scan, or repeated publication is authorized. A new run would require a separately reviewed and explicitly approved future authorization decision. This document provides no such authority.

---

## 10. Canonical outcomes and process failures

The authorized operation may produce exactly these canonical result kinds:

```text
ACCEPTED_EIGHT
FIXED_FIXTURE_FAILURE
SEED_SPACE_EXHAUSTED
```

Exact two-pass replay agreement is required for all three result kinds. Both passes must produce complete candidate bundles and the runner must compare them; publication requires exact replay success across all six compared fields (canonical payload bytes, `manifest_payload_sha256`, canonical manifest bytes, external manifest SHA-256, accepted-fixture order, and search diagnostics).

For `ACCEPTED_EIGHT`, `family_frozen=true` is permitted only after exact replay comparison success and successful authoritative finalization.

For `FIXED_FIXTURE_FAILURE` or `SEED_SPACE_EXHAUSTED`, publication is a truthful replay-matched canonical negative result with `family_frozen=false`. A canonical negative result must not be treated as permission to weaken, alter, replace, or rerun the construction policy.

Beyond the canonical result kinds, the runner already freezes these exact deterministic process-outcome classes:

```text
pre-contact refusal
pass-1 failure
pass-2 failure
replay mismatch
comparison-process failure
finalization failure
publication failure
```

No new result kind and no new failure vocabulary is introduced by this document; the canonical result kinds, process-outcome classes, failure codes, and failure stages remain exactly those frozen by the runner-implementation authorization.

---

## 11. Publication and exit behavior

A successfully promoted canonical result publishes exactly:

```text
manifest
execution envelope
summary
```

A successfully promoted deterministic post-contact process failure for which the frozen runner contract permits process-failure evidence publication publishes exactly:

```text
execution envelope
summary
```

A pre-contact refusal publishes no evidence: no staging directory, no final directory, no files. Static source-boundary rejection is a pre-contact refusal, not a post-contact process failure, and therefore publishes no evidence. A publication failure itself is not a successfully promoted evidence outcome.

Publication proceeds only through the frozen exclusive-staging and atomic-promotion write order: create the staging directory exclusively, write the outcome-specific files, close them, re-read them, verify exact bytes and SHA-256 identities, confirm the exact outcome-specific file set, then atomically rename staging to final. No overwrite, merge, append, reuse, or destructive rollback of promoted evidence is permitted.

Exit codes are exactly:

```text
exit 0 = atomic promotion succeeded for a complete canonical result
exit 1 = post-contact mathematical, replay, finalization, or process failure whose deterministic
         failure evidence was successfully promoted
exit 2 = pre-contact refusal; no staging or final evidence created
exit 3 = publication operation failed or atomic rename failed
```

A publication failure follows the runner's exact stderr and exit-code protocol (`exit 3`, empty stdout, exactly one frozen ASCII stderr line, staging retained unchanged) and must not fabricate successful evidence. A partial staging set is failure evidence, never a permitted successful file set; it is never promoted and never repaired.

---

## 12. Explicitly withheld authority

The following remain unauthorized. This document opens none of them:

```text
challenger implementation
challenger synthetic validation
challenger contact during selection
frozen F3 contact
historical retained-evidence contact
PsiTRS contact
live capture
production services
service integration
TORMENT memory-system integration
production-kernel integration
kernel modification
rerun authority
third-pass authority
alternative fixture policy
fixture replacement
scientific reinterpretation of the frozen F3 result
```

Do not touch:

```text
research/brainvision/results/results.csv
research/brainvision/results/results.json
torment_service/kernel/
```

---

## 13. Permanent Brainvision and TORMENT boundary

Project posture is preserved exactly:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

This synthetic-fixture operation is independent descriptor-blind research infrastructure. It does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen F3 result.

Brainvision remains:

```text
offline
quarantined
descriptor-blind at this stage
non-production
non-service
non-kernel
non-memory-integrated
```

Brainvision must not be integrated into the production TORMENT memory system or kernel without a later explicit architectural discussion with Hilmir and his approval of the integration route.

---

## 14. Post-commit stop condition

After this document is drafted, reviewed, committed alone, and pushed, execution remains paused.

```text
the runner is not executed by this document
no automated agent (Claude, Codex, GPT, or any other) is instructed by this document to execute the runner
a committed authorization HEAD is a necessary but not sufficient condition for execution
the sufficient additional condition is a separate explicit final invocation instruction from Hilmir
```

Even when Section 7's authorization-HEAD conditions are all satisfied, no invocation occurs until Hilmir gives that separate explicit final operator instruction. The single execution authority, once consumed at first canonical-iterator contact, is not renewed by this document.

---

## 15. Final authorization state

```text
EXECUTION_AUTHORIZATION_DOCUMENT_DRAFTED = True
COMMITTED_AUTHORIZATION_HEAD_ESTABLISHED = False
RUNNER_EXECUTION_AUTHORIZED_BY_COMMITTED_DOCUMENT = False
FINAL_OPERATOR_INVOCATION_ORDER_GIVEN = False
CANONICAL_SEED_SCAN_COMPLETED = False
ACTUAL_FIRST_EIGHT_DISCOVERED = False
FAMILY_FROZEN = False
RERUN_AUTHORIZED = False
CHALLENGER_IMPLEMENTATION_AUTHORIZED = False
CHALLENGER_SYNTHETIC_VALIDATION_AUTHORIZED = False
FROZEN_F3_CONTACT_AUTHORIZED = False
PSITRS_CONTACT_AUTHORIZED = False
PRODUCTION_INTEGRATION_AUTHORIZED = False
TORMENT_MEMORY_INTEGRATION_AUTHORIZED = False
KERNEL_MODIFICATION_AUTHORIZED = False
```

This document may authorize the future one-run operation once it becomes the committed authorization HEAD (Section 7) and Hilmir gives the separate explicit final invocation instruction. Preparation of the draft does not itself make the uncommitted working-tree document executable authority.

*End — TORMENT Brainvision Independent Order-Sensitive Synthetic-Fixture Freeze Execution Authorization v0.1. Docs-only. Authorizes exactly one future authoritative two-pass freeze operation through the sole frozen invocation shape, and only once this document is the committed authorization HEAD and Hilmir gives a separate explicit final instruction. No runner, generator, verifier, freeze library, canonical seed iterator, manifest builder, or project-module function was executed while preparing this document. No canonical seed was requested. No fixture was discovered. No output or staging evidence was created. No Git command was run. No challenger, PsiTRS, retained-F3, frozen-F3, production-service, TORMENT-memory-system, or production-kernel contact occurred. FORMAL_HOLD and Mode_0 remain active; the frozen F3 result is neither amended nor reinterpreted.*
