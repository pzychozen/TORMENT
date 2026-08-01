# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority C Pre-Contact Pytest Cache Access and Identity Resolution Design v0.1

## 1. Scope

This design specifies a future separately authorized operator act to resolve access and identity for the unreadable ignored artifact:

```text
absolute path:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\scratch\substrate_free_design_council\2026-06-15\.pytest_cache

relative path:
scratch/substrate_free_design_council/2026-06-15/.pytest_cache

ignored by:
.git/info/exclude:7:scratch/

current disposition:
E. ARTIFACT_IDENTITY_OR_ORIGIN_NOT_PROVABLE_FAIL_CLOSED
```

This design does not authorize deletion, movement, quarantine, renaming, content modification, timestamp normalization, cache recreation, pytest execution, Python imports, ownership takeover, persistent ACL change, ignore-rule modification, Git index modification, implementation contact, canonical-input contact, staging, commit, or push.

This design also carries forward the known sibling ignored artifacts in the independent validation journal so later remediation cannot treat the temp file in isolation:

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json
bytes: 144
SHA-256: 63bd8dbe4ee9eab89bb4cb9aea66e39b1cecf43def4f2b19a19a6e0c28edc965
ignored by: research/brainvision/.gitignore:2:results/

research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json.tmp
bytes: 136
SHA-256: b0910c0e5266d23105faae3fc2228396cb5ea54fbc5f33561bd891818c00b11b
ignored by: research/brainvision/.gitignore:2:results/
```

Those journal artifacts are not dispositioned, removed, quarantined, or otherwise altered by this design.

## 2. Issued Operation Relationship

The issued bounded implementation operation remains:

```text
bounded implementation-operation authorization: ISSUED_NON_COMMIT
implementation contact: NOT STARTED
implementation opportunity: NOT CONSUMED
Authority C/D/E: INACTIVE
canonical-input path: NOT CONTACTED
FORMAL_HOLD: ACTIVE
BLOCKER-2: OPEN
BLOCKER-4: INACTIVE
```

Access-resolution work is separate remediation governance. It is not implementation contact and must not consume the implementation opportunity. A future pre-contact rerun remains a continuation of the same pre-contact gate. No retry after consumption occurs because the opportunity has not been consumed.

## 3. Resolution Purpose

The future operator act may have only one permitted purpose: obtain enough read-only access to determine all of the following for the `.pytest_cache` directory:

```text
directory existence
directory type
owner
ACL
inheritance state
reparse-point state
recursive file inventory
recursive directory inventory
recursive byte count
deterministic recursive manifest identity
presence of executable or test-affecting content
whether contents are stable across two read-only passes
```

The future act must stop immediately if the target is not exactly the expected path, if a reparse point redirects inspection outside the expected directory, if a lock or permission state prevents safe proof, or if any command would touch implementation paths, the canonical-input path, the governed runner, ignore rules, Git configuration, or the Git index.

## 4. Access Strategy Analysis

### Strategy 1: Read-only inspection under current identity

```text
required authority:
ordinary read-only verification authority

expected filesystem mutation:
none intended; access-time mutation may occur depending on filesystem policy and must be treated as low-trust metadata noise

whether the mutation is reversible:
not applicable for content; access timestamps are not identity-bearing and are not used in manifest identity

required pre-state evidence:
repository root, branch, HEAD, local origin/main, .git/index.lock absent, target absolute path, visible directory entry, current ignore-rule provenance, no implementation contact

required post-state evidence:
same target visible, no tracked status change, no implementation path change, no result document created, Authority C/D/E inactive, opportunity not consumed

failure mode:
ACCESS_NOT_RESOLVED_FAIL_CLOSED when recursive inventory, ACL, owner, or manifest evidence is denied or incomplete

whether it preserves the issued implementation opportunity:
YES
```

Current evidence already shows this strategy is insufficient: the directory entry is visible, but recursive contents and stable manifest identity are unprovable due access denial.

### Strategy 2: Read-only inspection through an already authorized elevated operator context

```text
required authority:
separate remediation governance authorizing an already available elevated read-only operator context for this one directory

expected filesystem mutation:
none intended; no ACL, owner, contents, ignore rules, Git configuration, or index mutation

whether the mutation is reversible:
not applicable because no permission or content mutation is authorized

required pre-state evidence:
exact operator identity, exact elevated context identity, exact target path, proof the context already exists, proof no permission/ownership modification is needed, .git/index.lock absent, repository identity, target visible, ignore-rule provenance

required post-state evidence:
two identical read-only manifests, target still present, no tracked/index change, no implementation path change, no result document created, no canonical-input contact, Authority C/D/E inactive, opportunity not consumed

failure mode:
ACCESS_NOT_RESOLVED_FAIL_CLOSED if elevated read-only context cannot enumerate owner, ACL, inheritance, reparse state, and descendants; ACCESS_RESOLVED_CONTENTS_UNSTABLE_FAIL_CLOSED if the two passes differ

whether it preserves the issued implementation opportunity:
YES, provided no implementation contact occurs
```

This is the recommended least-authority future strategy if an already authorized elevated read-only context exists.

### Strategy 3: Temporary access grant with exact pre-state capture and exact restoration

```text
required authority:
separate remediation authorization naming exactly the target directory and allowing only a temporary non-recursive read/list permission grant if Strategy 2 is unavailable

expected filesystem mutation:
temporary ACL mutation on the one target directory only

whether the mutation is reversible:
reversible only if exact machine-readable pre-state ACL, owner, inheritance, and reparse-point state are captured first and exact restoration is proven afterward

required pre-state evidence:
exact current owner identity, exact ACL in machine-readable form, exact inheritance state, exact reparse-point state, exact operator identity, exact target path, exact command plan, proof no recursion is used unless independently required and justified

required post-state evidence:
exact ACL/owner/inheritance/reparse equality proof against pre-state, two identical manifests, target still present, no tracked/index change, no implementation path change, no result document created, no canonical-input contact, Authority C/D/E inactive, opportunity not consumed

failure mode:
STOP if pre-state cannot be captured; STOP if restoration cannot be proven; ACCESS_NOT_RESOLVED_FAIL_CLOSED if read access remains insufficient; ACCESS_RESOLVED_CONTENTS_UNSTABLE_FAIL_CLOSED if manifests differ

whether it preserves the issued implementation opportunity:
YES, if classified and executed as separate remediation contact and if implementation contact remains not started
```

This strategy is not authorized by this design. It is a fallback design option requiring a later explicit authorization.

### Strategy 4: Ownership or ACL modification only if no lesser strategy can work

```text
required authority:
separate elevated remediation authorization with explicit justification that Strategies 1, 2, and 3 cannot work

expected filesystem mutation:
ownership and/or ACL mutation on the one target directory

whether the mutation is reversible:
only conditionally reversible; failure to prove exact restoration fails closed

required pre-state evidence:
exact owner identity, exact ACL in machine-readable form, exact inheritance state, exact reparse-point state, exact operator identity, exact command list, exact scope limited to one directory, explicit non-recursive default

required post-state evidence:
machine-readable equality proof for owner, ACL, inheritance, and reparse-point state, plus two identical manifests and no repo/governance state drift

failure mode:
STOP if exact pre-state cannot be captured; STOP if restoration cannot be proven; classify as D. ACCESS_NOT_RESOLVED_FAIL_CLOSED or require separate remediation disposition

whether it preserves the issued implementation opportunity:
YES only if it remains separate remediation contact and no implementation contact occurs
```

This strategy must not be chosen casually. It is not authorized by this design.

### Strategy 5: Governed removal or quarantine without enumeration

```text
required authority:
separate remediation authorization declaring identity resolution impossible and naming exact removal or quarantine scope

expected filesystem mutation:
deletion, movement, or quarantine of the one target directory

whether the mutation is reversible:
deletion is not safely reversible; quarantine may be reversible only if the exact move and restoration path are preauthorized and verified

required pre-state evidence:
proof access resolution failed under lesser strategies, exact target path, visible directory entry, ignore-rule provenance, repository identity, no implementation contact

required post-state evidence:
target absence or exact quarantine location, parent-directory residue check, no tracked/index change, no implementation path change, no result document created, no ignore-rule change, Authority C/D/E inactive, opportunity not consumed

failure mode:
new residue, incomplete removal/quarantine, path ambiguity, or unexpected discovered artifacts fail closed

whether it preserves the issued implementation opportunity:
YES only if governed as separate remediation and followed by full pre-contact rerun
```

This strategy must not be used merely because the path looks disposable. It is not authorized by this design.

## 5. Recommended Least-Authority Strategy

The recommended future path is:

```text
1. Attempt Strategy 2 if an already authorized elevated read-only operator context exists.
2. If no such context exists, request separate authorization for Strategy 3 with exact pre-state capture and exact restoration.
3. Use Strategy 4 only after written proof that Strategies 1, 2, and 3 cannot provide the required evidence.
4. Use Strategy 5 only after identity resolution is declared impossible by separate governance.
```

ACL or ownership change is not currently required as a conclusion of this design. It is only a future fallback if lesser authority cannot work and a separate authorization explicitly permits it.

## 6. ACL and Ownership Prerequisites

Any future temporary permission or ownership alteration must require:

```text
exact current owner identity
exact current ACL in machine-readable form
exact inheritance state
exact reparse-point state
exact operator identity
exact commands
exact scope limited to the one directory
no recursion unless independently required and justified
exact restoration commands
post-restoration equality proof
STOP if restoration cannot be proven
```

The permission or ownership change must be classified as separate remediation contact, not implementation contact. It must not consume the implementation opportunity.

## 7. Manifest Schema

If read access becomes available, the operator must perform two read-only passes and compute a deterministic recursive manifest for the `.pytest_cache` directory. The manifest must include every descendant and the root directory marker.

Each entry must contain:

```text
relative_path
entry_type
file_byte_count
file_sha256
directory_marker
reparse_point_state
```

Entry rules:

```text
relative_path:
path relative to scratch/substrate_free_design_council/2026-06-15/.pytest_cache, normalized to forward slashes; root is "."

entry_type:
one of file, directory, reparse_point, other

file_byte_count:
decimal byte count for files; null for non-files

file_sha256:
lowercase hex SHA-256 for files; null for non-files

directory_marker:
true for directories, false otherwise

reparse_point_state:
object recording whether the entry is a reparse point and, if available read-only, the reparse tag; must not follow a reparse point outside the target tree
```

Canonical manifest identity preimage:

```text
UTF-8
LF-only
paths normalized to forward slashes
ordinal sort by relative_path, then entry_type
no timestamps
compact canonical JSON
object keys sorted lexicographically
SHA-256 computed externally
```

The manifest must not be written into the repository as a standalone file. It may be computed in memory and recorded in a later governance result document.

## 8. Two-Pass Stability Rule

The future operator must run two read-only passes using the same exact scope and canonicalization rules.

The two passes must independently produce identical:

```text
owner
ACL
inheritance state
root reparse-point state
recursive file count
recursive directory count
recursive byte count
canonical manifest SHA-256
presence/absence of executable or test-affecting content
```

If any pass fails, times out, is permission-blocked, encounters a reparse-point ambiguity, or produces a different manifest identity, the result must fail closed.

## 9. Executable and Test-Affecting Content Rule

The manifest analysis must separately flag whether the directory contains entries matching executable or test-affecting categories, including at minimum:

```text
*.py
*.pyc
*.pyo
*.pyd
*.dll
*.exe
*.bat
*.cmd
*.ps1
conftest.py
pytest.ini
pyproject.toml
setup.cfg
tox.ini
```

Presence of such content does not automatically authorize removal or quarantine, but it prevents admissibility until a separate disposition determines the operational effect.

## 10. Complete Ignored-Artifact Enumeration Rule

The future pre-contact rerun must carry forward independent-review finding F-31. It must perform complete enumeration of concerned ignored-artifact classes, not merely the two originally discovered paths.

The enumeration must cover at minimum:

```text
*.tmp
.pytest_cache
__pycache__
*.pyc
*.pyo
.pytest_cache directories
coverage files and directories
editor backup and swap files
*.bak
*~
*.swp
*.orig
*.rej
implementation sidecars
```

The rerun must classify enumeration as exactly one of:

```text
repository-complete enumeration proven
enumeration incomplete or timed out
enumeration blocked by permissions
```

Any incomplete, timed-out, or permission-blocked enumeration must fail closed. Newly discovered artifacts must not be removed automatically; they require separate disposition or remediation authority.

## 11. Terminal Classifications for Future Access Act

The future access act must conclude with exactly one terminal classification:

```text
A. ACCESS_RESOLVED_ARTIFACT_IDENTITY_BOUND
B. ACCESS_RESOLVED_CONTENTS_UNSTABLE_FAIL_CLOSED
C. ACCESS_RESOLVED_REPARSE_OR_UNEXPECTED_TYPE_FAIL_CLOSED
D. ACCESS_NOT_RESOLVED_FAIL_CLOSED
E. ACCESS_RESOLVED_BUT_REMOVAL_OR_QUARANTINE_STILL_REQUIRED
```

Successful identity resolution must not itself make the artifact admissible. After identity resolution, a separate disposition must decide among:

```text
baseline admission
exact removal
exact quarantine
current opportunity unusable
```

## 12. Rerun Requirements

After the future access act, pre-contact verification must be rerun from the beginning. The rerun must include:

```text
repository identity
.git/index.lock absence
staged state
tracked deletions
unmerged entries
authoritative filtered tracked status
complete Git-visible untracked inventory
complete concerned ignored-artifact enumeration
whole-repository raw-byte proof
303-file CRLF presentation-only proof
governance identities
opportunity-key reconstruction
runner identity
retained-control identity
candidate path absence
candidate-test path absence
implementation-result document absence
Authority C/D/E inactivity
canonical-input non-contact
governed-runner non-execution
implementation contact NOT STARTED
implementation opportunity NOT CONSUMED
```

The future rerun must distinguish:

```text
repository-complete enumeration proven
enumeration incomplete or timed out
enumeration blocked by permissions
```

## 13. Principal Classification

```text
B. PYTEST_CACHE_ACCESS_AND_IDENTITY_RESOLUTION_DESIGN_COMPLETE_WITH_OPERATOR_PREREQUISITES
```

Rationale:

```text
The access and identity resolution design is complete, but execution requires a future separately authorized operator act. Current evidence is insufficient to bind recursive contents or stable identity for the unreadable .pytest_cache directory. Identity resolution alone cannot admit the artifact; it can only enable a later disposition decision.
```
