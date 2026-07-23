# TORMENT Brainvision — Independent Order-Sensitive Synthetic Validation v0.2 — Execution-Authorization Architecture Review v0.1

## 0. Document class and status

```text
document_class        = execution-authorization ARCHITECTURE REVIEW (docs-only)
this_document_is      = a review + blocker record, NOT an execution authorization
authority_created     = none
execution_authorized  = false
code_modified         = none
docs_modified         = this untracked architecture-review draft may be corrected by the bounded review;
                        a separate untracked retrofit implementation-authorization draft may be created
git_mutations         = none
git_inspection        = read-only only
runner_executed       = false
runner_imported       = false
real_manifest_contact = none
verdict               = BLOCKER_CONFIRMED_RETROFIT_IMPLEMENTATION_AUTHORIZATION_REQUIRED
```

This document is a docs-only architecture review of the final Stage S3B v0.2 execution-authorization phase. It deliberately does **not** draft an execution-authorization specification, because static review found a genuine, concrete binding-mechanism gap in the committed runner. Per the review contract, no convincing-looking authorization draft is produced while the architecture is incomplete.

All permanent prohibitions remain active and unchanged:

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision = offline / quarantined / non-production / non-service / non-kernel / non-memory-integrated
```

This document does not amend, rescue, rerun, weaken, replace, or reinterpret the frozen historical F3 result.

## 1. Governing synchronized state and reviewed sources

```text
repository   = torment_fabric
branch       = main
HEAD         = origin/main
HEAD commit  = 58e8cef
working tree = clean except for this expected untracked architecture-review document
```

Reviewed (read-only, no execution, no import, no manifest contact):

```text
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py            (the v0.2 runner)
research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py             (bounded v0.2 tests)
research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py (static)
docs/…_V0_2_CORRECTION_SPECIFICATION_v0.1.md                    (§17 identity/authorization chain)
docs/…_V0_2_IMPLEMENTATION_AUTHORIZATION_v0.1.md                (§16 identity-binding & review sequence)
docs/…_V0_2_CONFIGURATION_IDENTITY_SPECIFICATION_v0.1.md        (config identity)
docs/…_V0_2_IDENTITY_BINDING_RECORD_v0.1.md                     (file + config identity bindings, dfcb205)
docs/…_V0_2_EXACT_MANIFEST_IDENTITY_BINDING_RECORD_v0.1.md      (manifest identity bindings, 58e8cef)
PRECEDENT docs/…_SYNTHETIC_VALIDATION_EXECUTION_AUTHORIZATION_v0.1.md          (S3B v0.1 — direct predecessor)
PRECEDENT docs/…_SYNTHETIC_FIXTURE_FREEZE_EXECUTION_AUTHORIZATION_v0.1.md      (S1 freeze)
PRECEDENT docs/…_SYNTHETIC_VALIDATION_EXECUTION_FAILURE_FINDINGS_v0.1.md       (v0.1 execution outcome)
PRECEDENT research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_1.py  (binding parser/checks)
PRECEDENT research/brainvision/run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py (binding parser/checks)
PRECEDENT bounded tests for the v0.1 validation and S1 freeze authorization mechanisms
```

## 2. Verdict

```text
BLOCKER_CONFIRMED_RETROFIT_IMPLEMENTATION_AUTHORIZATION_REQUIRED
```

The completed docs-only identity bindings (implementation identities + configuration identity at `dfcb205`; exact-manifest identities at `58e8cef`) are correct and non-circular as records. But the committed v0.2 **runner** has no mechanism to consume those docs-bound identities into its pre-contact gate. Its gate reads a hardcoded `AUTHORITATIVE_IDENTITIES` map whose entries are all `UNBOUND`, `main()` supplies no override, and the runner reads no authorization document, computes no file hashes, and enforces no latest-path-commit execution-HEAD rule. Therefore the runner is currently a dormant gate that cannot pass via the CLI through any committed mechanism, and the only way to satisfy it — editing the runner source — changes the runner's own committed identity and invalidates the `dfcb205` runner binding, with no committed non-circular closure. This is a missing **binding mechanism**, not merely a pending value or a judgment call.

The selected remediation architecture is now fixed by overseer direction:

```text
RETROFIT THE v0.1/FREEZE AUTHORIZATION-DOCUMENT BINDING MECHANISM INTO THE v0.2 RUNNER
```

A launcher/wrapper is not selected, and a bare hardcoded replacement of `UNBOUND` values is rejected.

## 3. The established (correct) lane mechanism — v0.1 and freeze precedent

Both prior one-run lanes resolve the self-reference cycles identically and non-circularly:

```text
1. The bound identities live in a machine-readable BEGIN/END binding block embedded in the
   execution-authorization DOCUMENT (not in runner source).
      v0.1 validation auth §6:  BEGIN-SYNTHETIC-VALIDATION-EXECUTION-AUTHORIZATION-BINDING-v0.1 … END-…
      freeze auth §6:           BEGIN-SYNTHETIC-FIXTURE-FREEZE-AUTHORIZATION-BINDING-v0.1 … END-…
2. At execution time the RUNNER READS those expected identities from the authorization document's
   committed bytes and self-verifies:
      v0.1 auth line 205 / freeze auth line 192:
      "the runner reads the runner, runner-test, and configuration expected values from the
       machine-readable binding in Section 6 of this document"
      pre-contact checks include "runner Git and raw identities match", "runner-test … match", etc.
3. NON-CIRCULAR execution-HEAD rule: the runner verifies, by read-only Git, that the latest commit
   affecting the exact authorization-document path equals HEAD:
      git log -1 --format=%H -- docs/…_EXECUTION_AUTHORIZATION_v0.1.md   ==   HEAD
      The document embeds NEITHER its own commit hash NOR its own Git blob (Cycle B / Cycle C closed).
      A single-file docs-only commit makes the rule provable; any later unrelated commit closes authority.
```

The v0.2 Correction Specification §17 and Implementation Authorization §16 explicitly anticipate this same pattern: "new execution-authorization document → latest-commit authorization binding (non-circular execution-HEAD rule)."

## 4. The v0.2 runner as committed — identity-gate mechanics

Facts established by static source review of `run_independent_order_sensitive_synthetic_validation_v0_2.py`:

```text
- AUTHORITATIVE_IDENTITIES (module constant, lines 133-144) hardcodes all 10 gate identities = "UNBOUND".
- perform_precontact_validation(..., identities=AUTHORITATIVE_IDENTITIES) (line 1483 default) checks each
  identity ONLY for presence (== UNBOUND -> refuse). It performs NO file-hash computation or comparison.
- _run_git (line 1451) runs ONLY repository-state commands: rev-parse --show-toplevel, status --short
  --branch, rev-parse HEAD, rev-parse origin/main. There is NO `git log -1 --format=%H -- <path>`.
- The runner reads NO authorization document: its only file reads are the journal/state files and the
  manifest reader (open(manifest_path,"rb")). There is no BEGIN/END binding parser and no .md read.
- construct_authoritative_run_config (line 1561) uses only expected_manifest_external_sha256 and
  expected_manifest_payload_sha256 from `identities` (for POST-contact manifest verification), plus the
  schema constant FROZEN_CONFIGURATION_SHA256. The git-blob/raw/config gate identities are never used
  beyond the presence check.
- main() (line 1609) calls run_authoritative(sys.argv, stdin_bytes) with NO identities argument -> the
  hardcoded all-UNBOUND AUTHORITATIVE_IDENTITIES is used -> pre-contact always refuses
  (FAIL_PRECONTACT_AUTHORIZATION, exit 2).
- The only injection channel for bound identities is the in-process `identities=` parameter used by the
  bounded tests; the runner docstring states these seams "are not exposed through CLI flags or
  environment values", and the runner reads no environment identity/config (Correction Spec §15).
```

Per-identity inventory (all 10 gate identities):

```text
identity                              current source repr / value   pre-contact behavior      requires source mod?   mod invalidates?
------------------------------------  ----------------------------  ------------------------  ---------------------  -----------------------------
later_execution_authorization_identity AUTH_IDENTITIES=UNBOUND (l134) refuse if ==UNBOUND (l1493) YES (no external channel) editing runner -> runner blob changes
runner_git_blob                        AUTH_IDENTITIES=UNBOUND (l135) presence-only (l1499-1509)  YES                      YES (self: Cycle A)
runner_raw_sha256                      AUTH_IDENTITIES=UNBOUND (l136) presence-only               YES                      YES (self: Cycle A)
runner_test_git_blob                   AUTH_IDENTITIES=UNBOUND (l137) presence-only               YES                      editing runner -> runner blob changes
runner_test_raw_sha256                 AUTH_IDENTITIES=UNBOUND (l138) presence-only               YES                      editing runner -> runner blob changes
schema_contract_git_blob               AUTH_IDENTITIES=UNBOUND (l139) presence-only               YES                      editing runner -> runner blob changes
schema_contract_raw_sha256             AUTH_IDENTITIES=UNBOUND (l140) presence-only               YES                      editing runner -> runner blob changes
expected_manifest_external_sha256      AUTH_IDENTITIES=UNBOUND (l141) presence pre + compare post  YES                      editing runner -> runner blob changes
expected_manifest_payload_sha256       AUTH_IDENTITIES=UNBOUND (l142) presence pre + compare post  YES                      editing runner -> runner blob changes
v0_2_configuration_identity            AUTH_IDENTITIES=UNBOUND (l143) presence-only (l1505)        YES                      editing runner -> runner blob changes
```

Docs-bound values that the runner cannot currently read: runner `c8f8eb5…`/`01d289e7…`, runner-test `fe20088…`/`3ef6bd83…`, schema-contract `a37b818…`/`ce57ae5…`, config `fff90bf5…` (all `dfcb205`); manifest external `05ce02af…`, payload `56a141bd…` (`58e8cef`). All are bound in DOCS only; the runner has no channel to consume any of them.

Intended final source/input (per lane precedent, ABSENT from the v0.2 runner): each gate identity should be read from the execution-authorization document's machine-readable binding and, for the file identities, matched against the runner's own recomputed file hashes, with the document's authority established by the latest-path-commit execution-HEAD rule.

## 5. Self-reference analysis (Cycles A, B, C)

### Cycle A — runner identity mutation — UNRESOLVED in committed sources

```text
runner file hardcodes UNBOUND gate identities
-> to pass the CLI gate, the identities must become non-UNBOUND
-> the only committed channel is editing the runner source (no doc-reader, no env, no args, no stdin)
-> editing the runner changes runner_git_blob (c8f8eb5…) and runner_raw_sha256 (01d289e7…)
-> the dfcb205 runner identity binding becomes stale
-> embedding the runner's own blob is a fixed point (embedding it changes it); and because the runner
   never self-verifies its blob, an embedded value is an unverified, silently-stale token
```

Which of the task's candidate resolutions the committed design actually provides:

```text
external immutable authorization payload the runner reads      = NO (v0.2 runner reads no such payload)
generated but non-source identity input                        = NO
source-excluded identity projection                            = NO (the gate expects the identities present)
two-stage runner identity                                      = NO
wrapper or launcher                                            = NOT COMMITTED (would be a new, unbound file)
deliberately authorized post-binding source revision           = the ONLY viable path, but it is NOT
                                                                 specified/committed and it invalidates the
                                                                 current runner binding, forcing re-binding
```

Conclusion: Cycle A is open. The v0.2 runner is a regression from the v0.1/freeze design, which closed Cycle A by keeping the runner frozen and putting the binding in the authorization document that the runner reads. The v0.2 runner has neither the doc-reader nor file-hash self-verification, so it has no non-circular way to hold bound identities.

### Cycle B — authorization-document identity — RESOLVABLE at the document level, but moot

```text
The precedent resolves this: the authorization document embeds NEITHER its own commit hash NOR its own
Git blob; its authority is established by the latest-path-commit rule, not by self-hashing. A future v0.2
authorization document could follow this exactly. However, this resolution is moot until the runner can
READ and ENFORCE it — which the committed v0.2 runner cannot.
```

### Cycle C — execution HEAD — RULE well-defined by precedent, but UNENFORCEABLE by the v0.2 runner

```text
The non-circular rule is: git log -1 --format=%H -- <auth-doc-path> == HEAD, with the authorization
committed as the sole changed file so it becomes HEAD, and a later unrelated commit closing authority.
The v0.2 runner does NOT implement this check (no `git log -1 -- <path>`; _run_git only queries repo
state). So the rule exists in precedent but cannot be enforced by the committed v0.2 runner.
```

## 6. The blocker

```text
BLOCKER: The committed Stage S3B v0.2 runner cannot move the docs-bound identities into its pre-contact
gate through any committed, non-circular mechanism.

- It has no authorization-document reader (cannot consume a v0.1/freeze-style binding block).
- It has no file-hash self-verification (its gate is presence-only, weaker than v0.1's hash-match).
- It has no latest-path-commit execution-HEAD rule (_run_git never runs `git log -1 -- <path>`).
- Its only identity channel is an in-process test seam that main() does not use and that is deliberately
  not exposed to the CLI/env.

Therefore an execution-authorization document written in the established (correct) style — a machine-
readable binding block the runner reads and enforces — would be inert: the v0.2 runner cannot read it,
cannot self-verify against it, and cannot apply the execution-HEAD rule. Drafting such a document now
would be a convincing-looking authorization that the runner cannot honor.
```

## 7. Consequence for the current bindings

```text
- The dfcb205 implementation-identity bindings and 58e8cef manifest-identity bindings are correct AS
  RECORDS, but they are inert with respect to execution: the runner cannot consume them.
- Any bounded revision that gives the runner the ability to consume these identities will change the
  runner's committed bytes, superseding the dfcb205 runner Git-blob/raw binding (c8f8eb5…/01d289e7…).
  The runner identity must therefore be RE-CALCULATED and RE-BOUND after that revision, before an
  execution-authorization document can bind a stable, self-verifiable runner identity.
- The schema-contract and runner-test identities need re-binding only if those files are also revised.
```

## 8. Required remediation sequence (the missing binding mechanism)

The lane cannot proceed to a valid execution authorization until the runner gains the established
identity-consumption mechanism. The minimal, precedent-aligned path is:

```text
1. SELECTED REMEDIATION (overseer direction): retrofit the v0.1/freeze mechanism into the v0.2 runner:
   read a fixed-path execution-authorization document's BEGIN/END binding block before manifest contact;
   strictly parse exact ordered fields; recompute and MATCH runner / runner-test / schema-contract
   Git-blob + raw SHA-256 identities; compare configuration and exact-manifest identities; enforce the
   latest-path-commit execution-HEAD rule; and populate later_execution_authorization_identity from the
   committed authorization binding mechanism rather than a hardcoded runner constant.
2. Prepare a separate docs-only IMPLEMENTATION-AUTHORIZATION amendment for that bounded runner revision
   (single, reviewable change set; no manifest contact; no execution).
3. Implement + bounded-test (non-authoritative) the runner revision.
4. Direct source review + Codex adversarial review.
5. RE-CALCULATE and RE-BIND the revised runner (and any revised file) identities, superseding dfcb205
   for those files; re-confirm configuration and manifest identities are unaffected.
6. Only THEN draft the docs-only v0.2 EXECUTION-AUTHORIZATION SPECIFICATION with a machine-readable
   binding block, the non-circular execution-HEAD rule, one-run authority semantics, and exit/failure
   semantics — modeled on the v0.1 validation authorization.
7. Final adversarial pre-contact review.
8. Separate explicit Hilmir execution order.
9. Only then, one authoritative invocation.
```

No step may rely on a future value not yet calculably fixed: in particular, the revised runner's Git blob is calculable only after step 3, and it must be bound (step 5) before any execution-authorization document references it.

The selected retrofit should adapt the exact reusable precedent elements: fixed repository-relative
authorization-document path, strict machine-readable binding block, read-only Git verification,
`HEAD == origin/main`, clean-tree check, latest authorization-path commit equal to `HEAD`, file-identity
recalculation, pre-contact fail-closed behavior, and zero manifest contact on refusal. The v0.2-specific
adaptations are the schema-contract identity pair, the v0.2 configuration identity, the exact-manifest
external and payload SHA-256 values, and the non-circular construction of
`later_execution_authorization_identity` from the authorization binding payload.

## 9. Answers to the 15 review questions

```text
1. later_execution_authorization_identity semantic meaning defined?  PARTIAL — precedent defines it (a
   doc-bound authority token verified via the execution-HEAD rule); the v0.2 runner only presence-checks a
   hardcoded UNBOUND constant and cannot derive it from a document.
2. Exact authorization payload defined?                              NO for v0.2 (precedent has a 7-field
   binding block; v0.2 has none and the runner cannot read one).
3. Ordered fields/types?                                             NO (no v0.2 binding block exists).
4. Canonical serialization / hash construction of the authorization? Precedent uses a plaintext binding
   block + latest-path-commit rule (no self-hash); v0.2 defines none.
5. Spec vs record relationship?                                     Precedent: spec-style authorization
   doc IS the record carrying the binding; v0.2 undefined.
6. Authorized execution-HEAD rule?                                   Defined by precedent (latest-path-
   commit == HEAD) but NOT implemented in the v0.2 runner.
7. Binds a pre-existing or later commit?                             Precedent: the authorization's OWN
   single-file commit becomes HEAD; execution HEAD resolved at runtime, never embedded.
8. Must implementation source replace UNBOUND constants?             YES — the runner must be revised to
   consume the identities (read doc / self-verify), OR a launcher added; a bare constant edit is the
   weak, non-recommended path.
9. How without invalidating the bound runner identity?               It CANNOT be done without a one-time
   runner revision + re-binding; afterwards the frozen runner reads the binding from the doc so future
   authorizations never touch the runner (the v0.1/freeze invariant the v0.2 runner currently lacks).
10. How does the runner verify its own bound identities non-circularly? Only by reading the expected
    values from a SEPARATE document and recomputing its own file bytes to compare — the mechanism the
    committed v0.2 runner does not have.
11. How does one-run authority become effective/consumed?           Precedent: consumed at first real
    manifest byte; pre-contact refusal consumes nothing; two reads per invocation, third prohibited. The
    v0.2 runner's arming/journal/exit model supports this; only the identity gate is unreachable.
12. Role of the explicit Hilmir order?                              Separate and mandatory after a
    committed authorization HEAD; the authorization document is necessary but not sufficient.
13. Authorization scope?                                            One authoritative invocation / one
    authority-consumption event (precedent).
14. Pre-contact refusal behavior?                                   Exit 2, authority unconsumed, no
    scientific result (runner already implements this).
15. Post-consumption failure behavior?                              Consumed exit 3/4/5 with retained
    durable evidence, no rerun (runner already implements this).
```

Items 11, 14, 15 are already satisfied by the committed runner's arming/journal/exit machinery; items 1–10 are blocked by the missing identity-consumption mechanism.

## 10. What requires Hilmir/Codex judgment

```text
- The remediation mechanism choice is CLOSED: retrofit the v0.1/freeze authorization-document binding
  mechanism into the v0.2 runner.
- Acceptance that the dfcb205 runner identity binding will be superseded by a post-revision re-binding.
- Acceptance that the final execution authorization remains prohibited until the revised runner/test
  identities are committed, reviewed, recalculated, and re-bound.
```

## 11. Final status

```text
architecture_complete            = false
binding_mechanism_present        = false (runner cannot consume docs-bound identities)
selected_remediation             = retrofit v0.1/freeze authorization-document binding mechanism
retrofit_technically_coherent    = true
cycle_A_runner_identity_mutation = UNRESOLVED in committed sources
cycle_B_auth_document_identity   = resolvable at document level (precedent), moot until runner can read it
cycle_C_execution_HEAD_rule      = defined by precedent, NOT enforceable by the committed v0.2 runner
execution_authorization_drafted  = false (deliberately not drafted; architecture incomplete)
implementation_authorization_drafted = separate docs-only draft may authorize bounded retrofit implementation
later_execution_authorization_identity = UNBOUND (and unreachable without a runner revision)

RECOMMENDATION = PREPARE_BOUND_RETROFIT_IMPLEMENTATION_AUTHORIZATION_FOR_OVERSEER_REVIEW
```

This review authorizes no execution, grants no authority, and claims no Hilmir order. It records a docs-only architecture finding and a required remediation sequence, and preserves all permanent boundaries.
