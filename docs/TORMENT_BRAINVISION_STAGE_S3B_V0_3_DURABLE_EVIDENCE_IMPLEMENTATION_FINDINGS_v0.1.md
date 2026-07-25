# TORMENT Brainvision — Stage S3B v0.3 Durable-Evidence Implementation Findings v0.1

## 1. Document Status

```text
document_class                    = implementation findings (docs-only)
authority_created                 = none
implementation_authorized         = false
execution_authorized              = false
manifest_contact_authorized       = false
publication_authorized            = false
publication_recovery_authorized   = false
real_results_tree_contact         = none
scientific_reconstruction         = none
retained_evidence_modified        = false
production_kernel_modified        = false
code_modified_by_this_document    = false
tests_modified_by_this_document   = false
prior_docs_modified               = false
git_mutations_by_this_document    = none
```

The implementation was previously authorised, implemented, independently reviewed,
accepted, committed, and synchronized.

This findings document creates no new authority.

This document is descriptive only. It does not amend or reinterpret the governing
architecture review, architecture decision record, implementation specification,
or implementation authorization.

Bound governing documents:

```text
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_REVIEW_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_ARCHITECTURE_DECISION_RECORD_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_SPECIFICATION_v0.1.md
docs/TORMENT_BRAINVISION_STAGE_S3B_V0_3_DURABLE_EVIDENCE_IMPLEMENTATION_AUTHORIZATION_v0.1.md
```

Authoritative committed implementation source:

```text
IMPLEMENTATION_COMMIT = f2ef7b9fb423da52853a79d96dc0d6212c6f5f26
```

Only synthetic pytest-local execution occurred under the prior implementation
authorization. This document does not say that publication or recovery is
generally authorised.

## 2. Scientific and Cognitive Boundary

```text
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

This implementation:

```text
does not reconstruct the unpublished v0.2 scientific result kind
does not imply SYNTHETIC_GATE_PASSED
does not imply SYNTHETIC_GATE_FAILED
does not reinterpret the historical v0.2 result
does not create scientific truth
does not alter scientific truth
does not select AI beliefs
does not control AI truth selection
does not enter AI cognition
does not enter AI autonomy
does not enter live memory
```

The architecture and implementation are recorded only as security,
provenance, and publication-integrity infrastructure.

## 3. Committed Implementation Surface

Exact committed implementation surface:

### Shared substrate modifications

```text
research/brainvision/durable_evidence_schema_v0_3.py
research/brainvision/durable_evidence_primary_writer_v0_3.py
research/brainvision/durable_evidence_replay_v0_3.py
research/brainvision/durable_evidence_durability_v0_3.py
```

### J1/J2 modules

```text
research/brainvision/durable_evidence_publication_v0_3.py
research/brainvision/durable_evidence_publication_replay_v0_3.py
research/brainvision/durable_evidence_publication_recovery_v0_3.py
research/brainvision/durable_evidence_publication_recovery_replay_v0_3.py
```

### Existing replay test corrected for Windows long paths

```text
research/brainvision/test_durable_evidence_replay_v0_3.py
```

### New focused J1/J2 tests

```text
research/brainvision/test_durable_evidence_publication_v0_3.py
research/brainvision/test_durable_evidence_publication_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_boundary_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_replay_v0_3.py
research/brainvision/test_durable_evidence_publication_recovery_boundary_v0_3.py
```

```text
committed implementation file count = 15
production/kernel files modified     = 0
service/runtime files modified       = 0
files outside docs/ and research/brainvision/ modified = 0
```

No new file identities are calculated or bound by this findings phase.

## 4. Architecture Findings

Preserved architecture decisions:

```text
H1 PUBLICATION_IS_PROJECTION
H2 authoritative durable scientific result =
   verified IMMUTABLE_SCIENTIFIC_BUNDLE
   plus linked valid SCIENTIFIC_COMPLETION
H3 observer/evidence boundary requires the durable verified linked pair
H4 publication recovery is separately authorised, publication-only,
   non-automatic, and scientifically incapable
H5 primary/emergency contradiction is CONTRADICTORY_EVIDENCE
```

Clarifications:

```text
publication does not create scientific truth
publication failure does not weaken or change scientific truth
recovery does not repair the original publication chain
recovery does not establish normal original publication completion
```

## 5. J1 Publication Findings

Accepted publication transition grammar:

```text
sequence 0 = PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED
sequence 1 = PUBLICATION_ATTEMPTED
sequence 2 = PUBLICATION_COMPLETED
sequence 3 = optional PUBLICATION_TERMINAL_STATUS
```

Publication replay fails closed on:

```text
missing genesis
standalone completion
wrong sequence
wrong predecessor
sequence gap
fork
cross-chain object
cross-identity object
non-durable required record
post-terminal extension
valid-prefix concealment of a contradictory tail
```

Publication operation posture:

```text
durable authority record before artifacts
durable attempted record before artifacts
canonical staging artifacts
staging durability confirmation
same-volume no-replace promotion adapter boundary
final byte and SHA-256 read-back
durable publication completion evidence
```

The shipped Windows promotion blocker is not solved. The default shipped
promotion adapter remains fail closed.

## 6. Publication Artifact Findings

Exactly three publication artifacts are defined:

```text
iososv_v0_3_result.json
iososv_v0_3_execution_envelope.json
iososv_v0_3_summary.txt
```

Artifact findings:

```text
exact inventory
exact filenames
canonical JSON
ASCII-only encoding
no BOM
no CR
one terminal LF
exact key ordering
exact regenerated-byte comparison
per-artifact SHA-256 verification
extra or missing artifact rejection
```

Only pytest-local synthetic positive adapters exercised successful projection.
No real results tree was used. No real artifact was published.

## 7. J2 Recovery Findings

Accepted publication-recovery transition grammar:

```text
sequence 0 = PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED
sequence 1 = PUBLICATION_RECOVERY_ATTEMPTED
sequence 2 = PUBLICATION_RECOVERY_ARTIFACTS_VERIFIED
sequence 3 = PUBLICATION_RECOVERY_EVIDENCE_COMPLETED
sequence 4 = optional PUBLICATION_RECOVERY_TERMINAL_STATUS
```

The term `PUBLICATION_RECOVERY_STARTED` is not part of the source or tests. It
appeared only in an implementation-agent prose report.

Recovery meaning:

```text
final artifacts verified under separate recovery evidence only
artifact source = already-existing final publication directory
```

J2 cannot:

```text
run science
read the manifest
generate publication artifacts
stage publication artifacts
promote artifacts
copy artifacts
rename artifacts
replace artifacts
overwrite artifacts
delete artifacts
repair artifacts
append to the original publication chain
write to the scientific chain
claim the original publication completed normally
```

All J2 evidence writes are confined to the distinct publication-recovery chain.

## 8. Authority and Durability Findings

Authority findings:

```text
same-object authority reuse denied
cross-object authority reuse denied through shared context
reuse after failed invocation denied
no automatic retry
durable chain replay is the post-event source of truth
```

Authoritative replay requires:

```text
VerifiedDurabilityEvidence
```

and rejects:

```text
raw hash sets
plain caller assertions
completion self-declarations
missing per-object durability
foreign physical-object durability
```

Accepted residual note carried forward:

```text
A public frozen ImmutableWriteResult could theoretically be hand-constructed with
DURABLE_ACCEPTED status in a synthetic trust context.
```

```text
J1/J2 did not introduce a weaker trust path
J1/J2 did not amplify the residual into a demonstrated authority-manufacturing exploit
the residual remains carried forward for later trust-surface review
```

## 9. Windows Long-Path Findings

Production correction:

```text
durable_evidence_primary_writer_v0_3.py
durable_evidence_replay_v0_3.py
durable_evidence_durability_v0_3.py
```

now route relevant physical filesystem operations through bounded Windows
extended-length paths.

Helper semantics:

```text
absolute path first
non-Windows path unchanged except absolute normalization
already extended path not double-prefixed
UNC path uses \\?\UNC\
drive path uses \\?\
```

The correction changes:

```text
changes no canonical bytes
changes no logical identity
changes no stored-object identity
changes no filename
changes no predecessor
changes no chain identity
changes no artifact hash
```

Discovered test-harness defect:

```text
failing path length = 271 characters
failing operation   = direct Path.write_bytes()
cause               = old replay test helper bypassed production long-path surfaces
```

Narrow correction:

```text
test_durable_evidence_replay_v0_3.py
test-local _windows_api_path()
same record_storage_filename()
same canonical_json_bytes()
binary write to the same full destination
```

Long-path support does not imply that Windows directory durability or
no-replace directory promotion is solved.

## 10. Review and Correction History

Initial implementation report:

```text
focused J1/J2 suite = 48 passed
existing durable-evidence slice = 124 passed
combined suite = 172 passed
```

First independent adversarial review findings:

```text
recovery vocabulary in source = correct
J1 transition grammar = accepted
J2 transition grammar = accepted
authority boundary = accepted
durability boundary = accepted
J2 structural incapability = accepted
artifact semantics = accepted
recovery semantics = accepted
long-path production patch = necessary and bounded
```

The first review returned `C. REQUIRE CORRECTION` only because the reported
Windows faulthandler access-violation output had not yet been characterised.

Authoritative Windows diagnostic capture:

```text
full suite run 1 = 171 passed, 1 failed
full suite run 2 = 171 passed, 1 failed
boundary run 1   = 17 passed
boundary run 2   = 17 passed
```

The single deterministic failure was:

```text
test_publication_and_recovery_chains_replay_with_distinct_chain_identities
direct Path.write_bytes()
271-character path
FileNotFoundError at traditional Windows MAX_PATH boundary
```

Explicit faulthandler produced first-chance/handled access-violation diagnostics
at unrelated pytest/import/subprocess locations. Those diagnostics:

```text
did not fail either boundary run
were not the deterministic cause of the full-suite exit code
were not attributed to J1 or J2
were not suppressed by a repository change
```

They are classified conservatively as:

```text
Windows environment/toolchain diagnostic evidence
```

No CPython or operating-system bug is claimed as proven.

Narrow correction validation:

```text
focused formerly failing test = 1 passed, twice
complete replay file          = 11 passed
complete suite                = 172 passed, twice
boundary suite                = 17 passed
warnings                      = none reported
skips                         = 0
```

Final independent review:

```text
verdict = A. ACCEPT
blocking defects = none
```

The final reviewer independently confirmed that only the one test file changed
in the correction and all production/J1/J2 files remained byte-identical to the
previously reviewed implementation.

## 11. Committed-State Replay

Post-commit read-only replay was performed from:

```text
repository = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
HEAD       = f2ef7b9fb423da52853a79d96dc0d6212c6f5f26
origin/main = f2ef7b9fb423da52853a79d96dc0d6212c6f5f26
```

Initial temporary-root inspection:

```text
TEMP=C:\Users\Notandi\AppData\Local\Temp
TMP=C:\Users\Notandi\AppData\Local\Temp
PYTEST variable = not defined
ordinary pytest temp root = C:\Users\Notandi\AppData\Local\Temp\pytest-of-Notandi
ordinary pytest temp root accessibility = Access is denied
```

Because the ordinary pytest temp root was inaccessible, shell-local temporary
values outside the repository were selected:

```text
TEMP=C:\Users\Notandi\AppData\Local\Temp\codex-docs-pytest
TMP=C:\Users\Notandi\AppData\Local\Temp\codex-docs-pytest
```

Observed complete suite output summary:

```text
172 passed in 6.04s
exit code = 0
```

Observed boundary suite output summary:

```text
17 passed in 0.98s
exit code = 0
```

Both replay commands emitted non-gating Windows access-violation diagnostic text
at pytest/subprocess/import locations. No pytest warning summary was reported.
The shell-local codex-docs-pytest scratch temporary root was removed after the replay.

## 12. Non-Contact and Non-Execution Findings

```text
real manifest contact                     = 0
descriptor/PsiTRS execution               = 0
scientific execution                      = 0
real publication invocation               = 0
real publication-recovery invocation      = 0
real results-tree writes                  = 0
production kernel modifications           = 0
live memory-system modifications          = 0
production service modifications          = 0
scientific reconstruction                 = 0
retained historical evidence modification = 0
```

Synthetic pytest-local paths and synthetic adapters are not real publication or
recovery.

## 13. Remaining Platform Blockers

All four blockers remain open:

```text
BLOCKER-1 = Windows directory durability is not yet established
BLOCKER-2 = real same-volume no-replace directory promotion is not yet established
BLOCKER-3 = authoritative artifact/result size bounds are not yet established
BLOCKER-4 = separate future real-operation authorizations are not present
```

```text
long-path support does not close BLOCKER-1
fail-closed promotion does not close BLOCKER-2
three fixed artifact names do not close BLOCKER-3
implementation acceptance does not close BLOCKER-4
```

No blocker is solved, partially solved, effectively solved, or operationally
sufficient.

## 14. Next Separately Reviewed Phase

```text
NEXT_PHASE =
SEPARATE_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION
```

The next phase is docs-only architecture analysis.

It will compare BLOCKER-1, BLOCKER-2, and BLOCKER-3, select one bounded blocker
for the next implementation cycle, define its exact proof obligation, and
preserve BLOCKER-4 until all required platform properties are separately
resolved.

No platform implementation is authorised by this findings document.

## 15. Permanent Boundaries

```text
FORMAL_HOLD = active
Mode_0 = active
STRONG_ORDER_HYPOTHESIS_NOT_SUPPORTED_BY_FROZEN_FAMILY
```

Brainvision and the durable-evidence implementation remain:

```text
offline
quarantined
synthetic-only
non-production
non-service
non-kernel
non-memory-integrated
non-cognitive
non-autonomous
```

The durable-evidence architecture remains security and provenance
infrastructure only.

## 16. Required Findings Verdict

```text
IMPLEMENTATION_STATUS = COMPLETE_AND_COMMITTED
IMPLEMENTATION_COMMIT = f2ef7b9fb423da52853a79d96dc0d6212c6f5f26
IMPLEMENTATION_REVIEW = ACCEPTED
FINAL_INDEPENDENT_VERDICT = A_ACCEPT

COMBINED_DURABLE_EVIDENCE_TESTS = 172_PASSED
BOUNDARY_TESTS = 17_PASSED

REAL_PUBLICATION_PERFORMED = False
REAL_RECOVERY_PERFORMED = False
REAL_MANIFEST_CONTACT = False
SCIENTIFIC_EXECUTION_PERFORMED = False

BLOCKER_1_CLOSED = False
BLOCKER_2_CLOSED = False
BLOCKER_3_CLOSED = False
BLOCKER_4_CLOSED = False

NEXT_PHASE =
SEPARATE_PLATFORM_BLOCKER_DECOMPOSITION_AND_FIRST_BOUND_SELECTION
```

*End of implementation findings v0.1. Docs-only. Creates no authority.*
