# TORMENT Brainvision — Stage S3B v0.3 Durable-Evidence Implementation Authorization v0.1

Status: DRAFT authorization for independent (GPT + Codex) review. Docs-only. Delivered outside the repository; not committed by the drafting agent. This document grants a single, bounded, synthetic-only, offline-only implementation authority — and nothing else — effective only upon operator (Hilmir) acceptance and commit. It implements nothing, executes nothing, contacts no manifest, and reconstructs no v0.2 result.

```text
document_class                         = implementation authorization (docs-only, single-purpose)
grants                                 = bounded authority to BUILD and TEST the quarantined Stage S3B v0.3
                                         durable-evidence infrastructure, synthetic-only and offline-only,
                                         conforming EXACTLY to the accepted Implementation Specification v0.1
grant_effective                        = only upon operator acceptance + commit of this document
implementation_authorized_by_this_doc  = yes — bounded (synthetic-only, offline-only, quarantined); no other scope
execution_authorized                   = false (no real/scientific execution of any runner)
manifest_contact                       = prohibited
frozen_manifest_contact                = prohibited
publication_authorized                 = false
publication_recovery_authorized        = false
durability_reconfirmation_authorized   = false
scientific_reconstruction              = prohibited
v0_2_retry / reconstruction / inference = prohibited
psitrs_contact                         = prohibited
production_integration                 = prohibited
kernel_modification                    = prohibited
retained_evidence_modified             = none
git_mutations_by_drafting_agent        = none
saved_into_docs                        = false (delivered outside the repository; operator commits if accepted)
```

Scientific claim boundary (preserved exactly, never crossed):

```text
two complete v0.2 scientific passes occurred
the two canonical v0.2 pass bundles were byte-identical
the unpublished v0.2 result kind is NOT durably available
the v0.2 result must not be reconstructed; this document does not state or imply
  SYNTHETIC_GATE_PASSED or SYNTHETIC_GATE_FAILED for v0.2
```

---

## 1. What this document is, and what it is not

This is the bounded implementation-authorization gate that sits between the accepted v0.3 durable-evidence *architecture and specification* and any *future construction* of that infrastructure. It authorizes a future implementation agent, acting under operator direction, to build and test the synthetic-only, offline-only, quarantined infrastructure that conforms exactly to the accepted Implementation Specification v0.1 (§2). It is narrow, single-purpose, and self-contained.

Binding separations, stated up front and preserved throughout:

```text
architecture/specification acceptance does NOT itself grant implementation authority
this document grants ONLY the bounded implementation authority stated in §6–§7
building this infrastructure does NOT grant scientific-execution authority
building this infrastructure does NOT establish that the named Windows primitives are valid
building this infrastructure does NOT recover the unavailable v0.2 result
building this infrastructure does NOT prove any future security-paper claim
every later execution and publication lane remains SEPARATELY authorized (§8, §9)
```

This document creates no scientific truth, asserts no scientific result, and moves no project boundary. Where the accepted Implementation Specification v0.1 is more precise than this authorization, the specification governs.

---

## 2. Bound baseline and governing documents

Authoritative repository and synchronized baseline (observed read-only; no mutation performed):

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
branch     = main
HEAD       = origin/main = bf465f5
working tree = clean
```

Current lineage at the bound baseline:

```text
bf465f5 docs(research): specify durable evidence implementation v0.3
f1dfa30 docs(research): resolve durable evidence architecture decisions v0.3
72c7edd docs(research): specify durable evidence architecture v0.3
c185e08 docs(research): record synthetic validation v0.2 execution failure findings
890c47a docs(research): bind synthetic validation v0.2 execution authorization
2637fac docs(research): specify synthetic validation v0.2 final execution authorization
```

Accepted governing documents this authorization is bound to and must not weaken, reinterpret, or omit:

```text
Architecture Review v0.1
  path              = docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_REVIEW_v0.1.md
  committed at      = 72c7edd (present at bf465f5)
  git blob          = 8dd09ffc7be8e7a2b44fafaa3acf52ada858053a
  whole-file SHA-256= 18aaa3732c24702df372c41ef747c2d326d949b5317902677cf84bc2fcf23d48
  byte length       = 51551

Architecture Decision Record v0.1 (H1–H5 binding)
  path              = docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_DECISION_RECORD_v0.1.md
  git blob          = fd2f5ade108f196c8caaf8fa4a2d8df50db2190b
  whole-file SHA-256= 2b4e31e590cfb9a2b0228b865ebd43eb7c53a454420d29e21782a388d0900922
  byte length       = 16565

Implementation Specification v0.1  (THE authority this document authorizes building; it governs on any conflict)
  path              = docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_SPECIFICATION_v0.1.md
  committed at      = bf465f5 (origin/main == main == HEAD)
  Codex disposition = A. ACCEPT
  character         = corrected replacement; resolved the two prior Codex blocking defects
                      (a durable publication-recovery evidence representation; the nine-column taxonomy repair)
```

Retained v0.2 forensic evidence remains immutable, read-only, and must never be repaired, renamed, deleted, promoted, terminalized, reused, or recomputed (`current_state.json` 144B `63bd8dbe…`; `current_state.json.tmp` 136B `b0910c0e…`). The v0.2 pass-bundle SHA-256, the scientific result kind, the underlying exception detail, and any terminal evidence JSON were **not** retained and must not be reconstructed.

---

## 3. Binding architecture decisions (H1–H5) — preserved without weakening

```text
H1  publication is a projection, not scientific truth creation
H2  authoritative result = verified immutable scientific bundle + linked valid SCIENTIFIC_COMPLETION record
H3  evidence becomes authoritative only when that pair is durable, byte/hash/identity verified, and linked
H4  publication recovery is separately authorized, publication-only, evidence-only, and non-automatic
H5  contradictory primary/emergency evidence fails closed
```

These decisions are authoritative and may not be reinterpreted, relaxed, or omitted by the implementation. Where they use "observer/evidence boundary," the term is engineering terminology for *when evidence becomes authoritative* (H3); it carries no consciousness, quantum, metaphysical, or physics-derived meaning, and none may be imported as a requirement.

---

## 4. Preserved identity model and evidence-chain separations

Preserve the identity distinction without collapse:

```text
logical_record_sha256  = nonce-free canonical logical identity (chain link; scientific identity)
stored_object_sha256   = nonce-bearing physical storage-instance identity (forensic only)
```

The nonce (`writer_attempt_identity`) never enters any chain link, any scientific identity, or any canonical scientific output. The analogous separation holds for bundles (`bundle_payload_sha256` nonce-free / scientific vs `stored_bundle_object_sha256` nonce-bearing / forensic).

Preserve the three separate evidence chains as structurally distinct, per specification §8, §10–§14, §19:

```text
scientific evidence chain
publication-projection evidence chains   (one per projection authorization)
publication-recovery evidence chains     (one per recovery authorization; Model A)
```

Hard, non-negotiable chain rules the implementation must enforce structurally:

```text
publication must NEVER append to or reopen the scientific chain
recovery must NEVER append to or reopen the original publication-projection chain
each chain's accepted position is DERIVED BY REPLAY of write-once, hash-linked, content-addressed
  immutable objects — there is no mutable authoritative pointer and no os.replace-style transition
same logical hash  = redundant storage instances (flag; accept one; retain all)
different logical hash at one sequence/predecessor = fork; fail closed
```

---

## 5. Permanent project boundaries (active throughout)

```text
FORMAL_HOLD = active
Mode 0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision remains offline and quarantined under `research/brainvision/`. The authorized implementation, its fixtures, and its tests live entirely under `research/brainvision/` and touch nothing else.

The implementation MUST NOT modify, import into, integrate with, or alter — no exception, and no production-kernel exception is permitted:

```text
torment_service/kernel/
production TORMENT memory functionality
live service behavior
prompt or memory writes
live capture
autonomous actions
production visual systems
```

The valid scientific result kinds are exactly `SYNTHETIC_GATE_PASSED` and `SYNTHETIC_GATE_FAILED`. Execution invalidity (`SYNTHETIC_GATE_INVALID`) is controlled invalidity — it is not a third scientific result and produces no bundle and no `SCIENTIFIC_COMPLETION`. This document states or implies nothing about which occurred in v0.2.

---

## 6. Exact authorized objective

Upon operator acceptance and commit, this document authorizes a future implementation agent, acting under operator direction, to **build and test** the:

```text
quarantined Stage S3B v0.3 durable-evidence infrastructure
```

as synthetic-only, offline-only, quarantined infrastructure that conforms **exactly** to the accepted Implementation Specification v0.1 (§2). The authorization is bounded to construction and synthetic testing of that infrastructure. It authorizes no scientific execution, no manifest contact, no publication, no recovery, and no durability reconfirmation. It grants no authority beyond the scope enumerated in §7, and it does not itself implement anything.

---

## 7. Authorized implementation scope

The implementation agent MAY build and synthetically test exactly the following, and only insofar as each conforms to the accepted specification (cross-references are to Implementation Specification v0.1):

```text
canonical schemas                                                   (spec §8, §9, §16, §17)
canonical serialization                                             (spec §7)
logical-record identity derivation (nonce-free)                     (spec §6, §7, §8)
stored-object identity derivation (nonce-bearing)                   (spec §6, §7, §9)
immutable object writers (write-once; no mutable pointer)           (spec §9, §18)
scientific evidence-chain records                                   (spec §10)
publication-projection chain records                                (spec §11, §12)
publication-recovery chain records                                  (spec §13, Model A)
authority-state machinery (four-state; §10 below)                   (spec §11, §13, §15)
single-use invocation consumption                                   (spec §11, §13, §15)
bundle validation                                                   (spec §16)
SCIENTIFIC_COMPLETION validation                                    (spec §17)
publication artifact validation                                     (spec §24)
publication recovery validation (evidence-only)                     (spec §13, §22, §24)
emergency evidence handling (non-authoritative)                     (spec §20)
fork and contradiction detection                                    (spec §9, §19)
cross-chain and cross-identity rejection                            (spec §19)
deterministic three-chain replay                                    (spec §19)
synthetic fault-injection infrastructure                            (spec §26)
synthetic fixtures                                                   (spec §14, §27)
synthetic-only tests                                                (spec §27)
fail-closed Windows durability adapter stubs                        (spec §21)
fail-closed same-volume no-replace promotion adapter stubs          (spec §12, §21)
```

The implementation must remain quarantined and synthetic-only at every step. No step may contact the real frozen manifest, execute a real descriptor, perform a real publication projection, or assert an authoritative durable result.

---

## 8. Explicit exclusions — authority denied

This document explicitly DENIES authority for, and the implementation must not perform or enable, any of the following:

```text
real scientific execution
v0.2 retry
v0.2 reconstruction
v0.2 result inference
frozen-manifest contact
PsiTRS execution or contact
real descriptor execution
real publication projection
publication recovery execution
durability reconfirmation
evidence repair
scientific reconstruction
production integration
kernel modification
live service integration
memory writes
prompt mutation
tool autonomy
action control
live visual input
authoritative durable-result claims
authoritative scientific-result claims
```

Any future evaluation, execution, publication projection, publication recovery, or durability reconfirmation is a **new lineage** and requires **separate** authorization. Nothing in the accepted architecture, the accepted specification, or this authorization may be read as pre-authorizing any of them.

---

## 9. Platform blockers (preserved unresolved)

The following remain UNRESOLVED, named blockers. This authorization does not close any of them, and building the infrastructure does not close any of them:

```text
BLOCKER-1  a validated Windows directory-entry durability primitive
BLOCKER-2  a validated same-volume no-replace directory-promotion primitive
BLOCKER-3  numeric size-bound confirmation against the real v0.2 pass-bundle size class
BLOCKER-4  separate future docs-only authorizations for:
             - publication projection
             - durability reconfirmation
             - publication recovery
```

Stub rule (BLOCKER-1 / BLOCKER-2): fail-closed adapter interfaces and stubs MAY be implemented and synthetically tested. A stub returns `UNCONFIRMED` / not-implemented and fails closed. No stub may be represented as satisfying the real platform durability or promotion requirement. Until BOTH the durability primitive and the no-replace promotion primitive are validated on the authoritative Windows/NTFS environment, the implementation must not assert durable acceptance, promote a publication, authorize protected manifest contact, perform authoritative execution, or publish an authoritative result.

BLOCKER-3 note (preserved and bounded): the real v0.2 pass-bundle SHA-256 and byte size were **not** retained and must not be reconstructed. This authorization therefore does NOT grant any means to close BLOCKER-3 — in particular, no manifest contact and no v0.2 reconstruction. The 4 MiB stored-bundle bound (spec §7) may be implemented and its enforcement fail-closed-tested synthetically, but confirming the bound against the real v0.2 pass-bundle size class remains a separate future authorization that must establish the size class by legitimate, boundary-preserving means. The blocker stays open.

---

## 10. Required authority semantics (bound to the accepted four-state model)

The implementation must bind every protected authorization (scientific-execution, publication-projection, and publication-recovery) to the accepted authority-state model. It MODELS and ENCODES these states; it does not itself begin any protected invocation (those are separately authorized under BLOCKER-4).

```text
NOT_ATTEMPTED             = a LIVE process state only (before the manually authorized invocation begins)
CONSUMED                  = durably proven (a valid, durable genesis/consumption record exists)
ATTEMPT_FAILED            = durably evidenced consumption attempt that could not become valid+durable
ATTEMPT_STATE_INDETERMINATE = post-event; cannot distinguish never-started from started-then-died
```

Required semantics, enforced structurally and by test:

```text
each protected authorization is CONSUMED for reuse-policy purposes when the manually authorized invocation
  begins — immediately after authorization + anchor validation and immediately BEFORE any protected mutation —
  regardless of whether a durable genesis is created
ambiguous process death fails CLOSED (ATTEMPT_FAILED or ATTEMPT_STATE_INDETERMINATE, never silent success)
missing genesis evidence NEVER permits silent reuse
both non-success states (ATTEMPT_FAILED, ATTEMPT_STATE_INDETERMINATE) prohibit automatic reuse, automatic
  retry, automatic output, and automatic evidence completion, and REQUIRE a new separate authorization
the implementation adds NO automatic retries — nothing in this design auto-retries
scientific execution never resumes once scientific authority is consumed
```

---

## 11. Required evidence semantics

```text
immutable scientific bundle payload + valid linked SCIENTIFIC_COMPLETION = AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
bundle without a valid matching receipt  = ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE (non-authoritative)
receipt without a valid matching bundle  = INVALID_SCIENTIFIC_COMPLETION      (non-authoritative)
```

Required, and enforced structurally and by test:

```text
scientific terminal status is OPTIONAL closing evidence — not required for scientific-result recognition,
  publication eligibility, publication authorization, publication-chain genesis, or publication recovery
publication completion NEVER creates or strengthens scientific truth
recovery completion means ONLY: already-existing final artifacts were verified under a separate recovery authority
recovery completion does NOT imply the original projection invocation completed normally, nor that the
  original publication chain is complete; the strongest resulting publication fact is
  "final artifacts verified under separately authorized recovery evidence"
emergency evidence (EMERGENCY_OBSERVED_UNCOMMITTED) is NON-AUTHORITATIVE and must never become scientific truth,
  authorize publication, or permit execution/result recovery or reconstruction
contradictory primary/emergency evidence = CONTRADICTORY_EVIDENCE → fail closed: no verdict, no publication,
  no auto-reconciliation, no execution recovery, no retry, no repair/deletion; both channels retained
  byte-for-byte; operator forensic review required
no publication-authority, staging, promotion, final-directory, publication-evidence, or recovery failure may
  erase or weaken an already-established authoritative scientific result
```

---

## 12. Required publication-recovery capability boundary (J2 evidence-only)

The implementation must preserve the J2 evidence-only boundary. Structural incapability is REQUIRED over policy-only prohibition wherever feasible (enforced by transitive source-boundary inspection, path-ownership checks, callable-surface inspection, monkeypatch sentinels, isolated-subprocess module-loading tests, and negative import tests — spec §22).

J2 MAY be implemented to:

```text
read original projection evidence
read already-existing final artifacts
validate filenames
validate bytes
validate hashes
validate identities
validate the deterministic publication recipe
write ONLY to a separate publication-recovery evidence chain
```

J2 MUST NOT be capable of:

```text
generating publication artifacts
promoting staging
copying or renaming directories
overwriting evidence
deleting evidence
merging evidence
repairing evidence
appending to the original projection chain
executing descriptors
contacting the manifest
constructing scientific results
```

The publication projector (J1) and the recovery verifier (J2) must both be structurally unable to import the scientific descriptor or manifest reader, load fixtures for recomputation, change scientific configuration, construct a result kind, create a scientific bundle, or create a `SCIENTIFIC_COMPLETION` record. J2 additionally must be structurally unable to import artifact generators, the promotion adapter, or J1, and must write nowhere except its own publication-recovery chain.

---

## 13. Fault-injection obligations

The implementation must provide synthetic fault-injection coverage across the important transition boundaries, including at minimum interruption or failure at each of:

```text
before authority consumption
after authority consumption but before genesis
after genesis but before attempted evidence
during immutable-object writing
after bundle persistence but before SCIENTIFIC_COMPLETION
during publication staging
after final publication promotion but before PUBLICATION_COMPLETED
during publication-recovery verification
during emergency evidence creation
during replay
during contradictory-evidence detection
```

Expected behavior at every injected boundary is **fail closed**: the authoritative scientific result is unchanged; no chain is illegitimately appended to or reopened; consumed authorization is not reused; no automatic retry; no artifact generation, promotion, overwrite, or repair by recovery; no cross-chain output collision; forensic material retained; deterministic fail-closed classification. Coverage must span the scientific, publication-projection, and publication-recovery families (spec §26).

---

## 14. Testing obligations

Focused, synthetic, offline tests are required for at least:

```text
canonical serialization stability
terminal-byte rules
logical hash determinism
physical hash nonce separation
redundant physical-instance acceptance
logical fork rejection
predecessor mismatch rejection
cross-chain rejection
cross-identity rejection
bundle/completion linkage
missing completion rejection
authority-state transitions
ambiguous death handling
single-use consumption
missing genesis handling
no automatic retry
emergency evidence non-authority
contradictory evidence closure
publication/scientific separation
recovery/original-projection separation
J2 capability restrictions
deterministic replay
platform-stub fail-closed behavior
fault-injection outcomes
```

The implementation must additionally unit-test the exact recomputable identity values fixed in the specification (spec §7: the scientific logical record, stored-object, `publication_chain_identity` examples A/B, and both `publication_recovery_chain_identity` examples). All tests must remain synthetic and offline; no test contacts the real frozen manifest, and no recovery test generates artifacts.

---

## 15. Implementation-agent discipline

The future implementation agent must:

```text
use Command Prompt
run: conda activate torment
change to the authoritative repository (C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric)
use python (not py)
use ^ for multiline Command Prompt commands
inspect the exact files before changing anything
run focused tests first
run the relevant broader quarantined Brainvision test set afterward
report the exact file inventory
report exact test counts
report blockers and deviations
perform NO commit or push unless separately instructed by Hilmir
```

Do NOT routinely run `python --version` or `where python`; use them only if interpreter ambiguity or an execution failure creates a specific need.

---

## 16. Required document posture and binding statements

This authorization is, and must remain:

```text
narrow ; single-purpose ; docs-only ; implementation-specific ; synthetic-only ; offline-only ;
fail-closed ; identity-bound ; explicitly non-scientific ; explicitly non-production
```

It states clearly, and binds:

```text
architecture acceptance does not itself grant implementation authority
this document grants only the bounded implementation authority stated here (§6–§7)
implementation completion will not grant scientific-execution authority
implementation completion will not establish that the named Windows primitives are valid
implementation completion will not recover the unavailable v0.2 result
implementation completion will not prove the future security-paper claims
all later execution and publication lanes remain separately authorized
```

Where the accepted Implementation Specification v0.1 is more precise than this authorization, the specification governs. This authorization does not silently resolve any ambiguity by inventing new architecture; any named ambiguity is recorded for the operator and the review trio (see the accompanying self-review), not resolved by construction.

---

## 17. Non-authorizations and preserved boundaries (final)

Beyond the bounded implementation authority of §6–§7, this document creates no authority and changes nothing. It does not authorize or recommend enacting:

```text
v0.3 or any runner execution ; manifest contact ; scientific reconstruction/recomputation ;
publication of any result ; publication recovery ; durability reconfirmation ;
evidence repair/rename/deletion/promotion/terminalization ;
reconstruction of the v0.2 scientific verdict ; a v0.2 retry ; PsiTRS contact ;
historical F3 reinterpretation ; production-kernel modification ; live Brainvision integration ;
memory-system integration ; live capture/ingestion ; service/runtime integration ;
threshold/tolerance tuning ; scientific rescue ; production claims ;
a scientific-execution authorization ; a publication-projection authorization ;
a durability-reconfirmation authorization ; a publication-recovery authorization
```

Preserved:

```text
docs-only; delivered outside the repository; not saved into docs/ by the drafting agent
FORMAL_HOLD = active ; Mode 0 = active ; STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
Brainvision remains offline and quarantined under research/brainvision/
v0.2 is consumed, terminal, and immutable; any future evaluation is a NEW lineage — never a retry
valid scientific result kinds are exactly SYNTHETIC_GATE_PASSED and SYNTHETIC_GATE_FAILED;
  SYNTHETIC_GATE_INVALID is controlled invalidity, not a third result; this document does not state
  or imply which occurred in v0.2, which is not durably available and must not be reconstructed
```

*End of implementation authorization v0.1. Docs-only, delivered outside the repository. No repository change, execution, import, manifest access, publication, publication recovery, durability reconfirmation, scientific reconstruction, or Git operation was performed in producing it.*
