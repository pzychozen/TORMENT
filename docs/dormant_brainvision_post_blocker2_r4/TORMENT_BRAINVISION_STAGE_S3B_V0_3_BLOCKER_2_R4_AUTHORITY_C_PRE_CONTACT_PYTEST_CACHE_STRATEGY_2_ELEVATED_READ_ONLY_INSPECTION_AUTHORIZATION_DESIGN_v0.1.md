# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority C Pre-Contact Pytest Cache Strategy-2 Elevated Read-Only Inspection Authorization Design v0.1

## 1. Purpose

This document defines a future Strategy-2 narrow elevated read-only inspection authorization design for the inaccessible ignored `.pytest_cache` artifact.

It is a design document only. It does not issue the future operator act, perform elevated inspection, dispose of the artifact, remediate the artifact, delete it, quarantine it, modify permissions, rerun pre-contact verification, or begin implementation contact.

The future Strategy-2 act may authorize only read-only inspection through an already authorized elevated Windows operator context whose existence, identity, elevation, integrity, and process provenance are proven before any target-path contact.

## 2. Bound Target

The only target artifact is:

```text
repository-relative path:
scratch/substrate_free_design_council/2026-06-15/.pytest_cache

expected absolute Windows path:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\scratch\substrate_free_design_council\2026-06-15\.pytest_cache
```

The future act must reject any:

```text
path substitution
sibling path
alternate repository checkout
junction redirection
symbolic-link redirection
reparse traversal
case-normalized replacement
short-name alias
environment-variable expansion
wildcard expansion
operator-selected equivalent
```

The target path must match the bound path exactly. The future act must not accept a path merely because it resolves to a similar visual location.

## 3. Governing State

The governing project state remains:

```text
issued bounded implementation operation:
VALID BUT SUSPENDED BEFORE FIRST CONTACT

implementation contact:
NOT STARTED

implementation opportunity:
NOT CONSUMED

source write:
NOT STARTED

test write:
NOT STARTED

Authority C:
INACTIVE

Authority D:
INACTIVE

Authority E:
INACTIVE

canonical-input path:
NOT CONTACTED

governed runner:
NOT EXECUTED

candidate construction:
NOT STARTED

implementation-result document:
ABSENT

FORMAL_HOLD:
ACTIVE

BLOCKER-2:
OPEN

BLOCKER-4:
INACTIVE
```

Brainvision remains quarantined under research governance. No production TORMENT memory-kernel integration is permitted. BLOCKER-4 remains inactive.

## 4. Authority Separation

This design distinguishes:

```text
design authority:
this document specifies a future Strategy-2 inspection act and its constraints

future operator issuance:
a later operator act may issue the Strategy-2 inspection if prerequisites are proven

future elevated inspection execution:
the later act may perform read-only inspection only through an already authorized elevated context

later artifact disposition:
a later separate governance step decides baseline admission, removal, quarantine, or unusability

later pre-contact verification:
a later separate process reruns the full pre-contact gate from the beginning

later implementation opportunity:
implementation remains suspended until all pre-contact gates are satisfied
```

Only the future operator may establish that an elevated context exists and authorize bounded use of that context. This design does not assume an elevated context exists. Normal administrative-group membership is not proof that the current process is elevated.

## 5. Operator-Context Proof Before Target Contact

Before any target-path contact, the future act must require reproducible evidence proving:

```text
the elevated context already exists
the context was authorized independently of this Strategy-2 act
the exact Windows account identity
the exact security principal SID
the elevation state
the integrity level
the process identity used for inspection
the process creation method or already-open context provenance
the operator who invoked the inspection
the repository root used by the process
the working directory
the command interpreter
the Python interpreter, if Python is used
the absence of impersonation or unexplained token substitution
the absence of a newly created privilege-escalation mechanism
```

The future act must fail closed if any identity, token, elevation, provenance, or process fact is absent, ambiguous, inconsistent, or not reproducible.

The act must not authorize creation of a new elevated context. It may authorize use only of an already authorized elevated operator context.

## 6. Mandatory Prohibitions

The future Strategy-2 act must explicitly prohibit:

```text
ACL modification
temporary ACL modification
persistent ACL modification
ownership modification
ownership takeover
inheritance modification
permission inheritance reset
permission repair
permission normalization
permission propagation
privilege enablement beyond the pre-existing elevated context
file creation
script creation
helper-file creation
temporary-file creation
log creation inside the repository
content modification
intentional timestamp modification; unavoidable read-access timestamp effects are governed by Section 15
attribute modification
alternate data stream modification
deletion
movement
rename
replacement
copying into the repository
copying out for disposition
quarantine
archiving
compression
extraction
test execution
pytest execution
repository implementation contact
authorized Python implementation-path contact
canonical-input path contact
governed-runner execution
Authority C activation
Authority D activation
Authority E activation
journal-artifact contact
Git staging
Git commit
Git push
line-ending normalization
repository configuration change
BLOCKER-4 work
```

All ACL change is prohibited, not merely persistent ACL change. Script creation is prohibited explicitly. No implementation source may be opened for writing.

## 7. Journal-Artifact Exclusion

The Strategy-2 act must not inspect, hash, delete, modify, move, quarantine, or otherwise contact:

```text
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json

research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json.tmp
```

Those journal artifacts remain outside this act. They may be considered only by a separate disposition or remediation authority.

## 8. Root Verification Before Traversal

Before recursive enumeration, the future act must perform non-mutating verification of the exact target root.

The evidence must establish:

```text
the target exists
the target is a directory
the target is not a regular file
the target root is not a symbolic link
the target root is not a junction
the target root is not another reparse-point type
the target root is not an alternate data stream
the target resolves beneath the accepted authoritative repository root
the target path matches the bound path exactly
the repository root itself is the accepted checkout
no traversal has occurred before these checks pass
```

Any reparse point, path mismatch, unexpected type, path-resolution ambiguity, or failure to verify must stop the act before traversal.

The repository root proof must bind:

```text
repository root:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric

branch:
main

accepted HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

accepted local origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043

HEAD equals local origin/main:
YES

.git/index.lock:
ABSENT
```

## 9. Read-Only Traversal Authority

After root verification passes, the future act may authorize recursive read-only metadata and file-content reads solely to construct two deterministic manifests.

The traversal must not:

```text
execute discovered content
import Python modules
invoke pytest
evaluate configuration as executable instruction
follow links
open network paths
interpret cache records as commands
write logs or helper files into the repository
reuse cached enumeration or hashes from a prior pass
```

The root reparse rule applies before traversal to the exact target root. The descendant reparse rule applies after traversal begins.

Every discovered reparse point at or below the target root must cause immediate fail-closed termination under:

```text
D. STRATEGY_2_TARGET_REPARSE_OR_PATH_ESCAPE_DETECTED_FAIL_CLOSED
```

Neither root nor descendant reparse points may be followed. Neither root nor descendant reparse points may be tolerated as a successful partial enumeration. A manifest containing or skipping a discovered reparse point cannot terminate as stable identity resolution. File count, directory count, recursive byte count, and manifest identity must never be represented as complete after a reparse encounter.

## 10. Two Independent Manifest Passes

The future act must require two complete read-only passes.

The passes must be independently initiated. Pass 2 must not reuse cached enumeration, cached metadata, cached file sizes, or cached file hashes from Pass 1.

Each pass must produce evidence binding every entry through the single normative manifest-entry schema in Section 12.

Section 12 is the only normative definition of serialized manifest entries. Earlier or later references to manifest entries must be read as references to that ten-key schema, not as alternate schemas.

For any unsupported or unclassified entry type, fail closed.

Per-entry read failure must abort the complete manifest pass. A partially completed manifest must not be accepted.

## 11. Path Canonicalization

The future act must preserve on-disk path observation and canonical identity path construction separately.

Required path rules:

```text
preserve on-disk case verbatim
do not case-fold
represent canonical relative paths with forward slashes
apply Unicode NFC normalization to canonical relative paths
use ordinal sorting
reject absolute paths in manifest entries
reject "." and ".." traversal components
reject empty path components
reject normalized paths escaping the target root
reject duplicate canonical paths
reject Unicode-normalized path collisions
reject comparison-only Unicode casefolded canonical-path collisions
reject ambiguous path decoding
reject unrepresentable path names
```

Any normalized-path collision must fail closed.

For each `canonical_relative_path`, compute a comparison-only Unicode casefolded form after NFC normalization. If Python terminology is used, the comparison-only form must use Unicode `str.casefold()` semantics, not platform-dependent locale-sensitive lowercasing.

If two distinct observed entries have different `verbatim_relative_path` values but equal comparison-only casefolded canonical forms, the pass must fail closed under:

```text
H. STRATEGY_2_PATH_CANONICALIZATION_OR_COLLISION_FAILED_CLOSED
```

The comparison-only casefolded form is not serialized as `canonical_relative_path`. The comparison-only form is not substituted for the on-disk path. It is used only for collision detection. On-disk case remains preserved verbatim. `canonical_relative_path` remains NFC-normalized without case folding. Ordinary duplicate `canonical_relative_path` values also fail closed. Unicode-normalized collisions also fail closed.

The evidence must preserve both:

```text
verbatim_relative_path
canonical_relative_path
```

The act must not silently rewrite the observed path.

## 12. Canonical Manifest Representation

The deterministic canonical manifest representation must use:

```text
UTF-8
no BOM
LF-only
compact JSON
lexicographically sorted object keys
ordinally sorted entries
forward-slash canonical relative paths
no timestamps in the identity preimage
no machine-local absolute path in the manifest identity preimage
no operator name in the manifest identity preimage
no non-deterministic field
external SHA-256 over the completed canonical bytes
```

The result evidence may separately bind operator, process, repository, and absolute-path facts outside the manifest identity preimage.

The canonical manifest top-level object must contain:

```text
schema
target_relative_path
path_normalization
entry_count
file_count
directory_count
recursive_byte_count
entries
```

Each manifest entry must contain only deterministic identity fields:

```text
verbatim_relative_path
canonical_relative_path
entry_type
file_byte_count
file_sha256
directory_marker
reparse_point_state
executable_content
potentially_test_affecting
unknown_content
```

These ten keys are the complete serialized manifest-entry schema. All ten keys must be present on every entry. No key may be omitted. Object-key names are part of the canonical JSON identity preimage and are therefore normative.

For a regular file:

```text
file_byte_count:
non-negative JSON integer

file_sha256:
64-character lowercase hexadecimal SHA-256 string

directory_marker:
false
```

For a directory:

```text
file_byte_count:
JSON null

file_sha256:
JSON null

directory_marker:
true
```

JSON `null` is part of the canonical identity preimage for directory entries. The serialized string `"not applicable"` must not be used. The null-versus-omission decision is closed: directory entries use JSON null for `file_byte_count` and `file_sha256`, and all ten keys remain present. For any unsupported entry type, the pass must fail closed before acceptance.

## 13. Pytest-Cache Content Classification

The future act must classify whether discovered content is potentially executable or potentially test-affecting.

The test-affecting rules must explicitly recognize at minimum:

```text
CACHEDIR.TAG
README.md
.gitignore
v/cache/lastfailed
v/cache/nodeids
v/cache/stepwise
```

The design must not infer harmlessness solely from filename extensions.

Unknown, unsupported, malformed, or unclassified entries must default to:

```text
potentially_test_affecting:
true
```

Python source, bytecode, executable files, scripts, command files, dynamic libraries, links, configuration files, plugins, startup hooks, or content capable of influencing test selection or execution must be classified conservatively.

The act performs classification only. It must not execute, import, or validate discovered content through pytest.

## 14. Required Pass Agreement

The two passes must agree exactly on:

```text
target root identity
owner
ACL
inheritance state
root reparse-point state
entry set
verbatim relative paths
canonical relative paths
entry types
file byte counts
file SHA-256 values
file count
directory count
recursive byte count
manifest canonical byte count
manifest SHA-256
executable-content flag
test-affecting-content flag
unknown-content flag
read-failure count
collision state
```

Any difference must fail closed. The design must not reinterpret a difference as ordinary cache churn.

## 15. Stability and Non-Mutation Evidence

The future result evidence must demonstrate that the inspection act did not intentionally modify:

```text
owner
ACL
inheritance
root type
reparse state
directory contents
file contents
repository tracked state
repository ignored state
Git index
Git configuration
authorized implementation paths
canonical-input paths
journal artifacts
```

The design does not claim that ordinary read access can universally preserve every filesystem access timestamp.

The future act must:

```text
identify which timestamps may be read or observed
avoid timestamp mutation where the platform permits
not use timestamp equality as the sole non-mutation proof
record any observed timestamp change
fail closed if a content, size, path, permission, ownership, or structural mutation is detected
```

Timestamp equality must be supplemental only. Content identity, path identity, structural identity, owner, ACL, inheritance, reparse state, Git state, and prohibited-contact evidence are the governing non-mutation proofs.

## 16. Repository-Complete Ignored-Artifact Enumeration Boundary

This Strategy-2 act resolves only the inaccessible `.pytest_cache` artifact at the bound target path.

It must not claim that repository-complete ignored-artifact enumeration has been proven.

A later separate process must still cover at minimum:

```text
*.tmp
.pytest_cache
__pycache__
*.pyc
*.pyo
coverage files and directories
editor backup files
swap files
*.bak
*~
*.swp
*.orig
*.rej
implementation sidecars
```

The Strategy-2 result is only one input to that later repository-complete enumeration and disposition process.

## 17. Required Future Result Evidence

The future Strategy-2 result record must contain at minimum:

```text
result schema identifier
strategy_rung_used
strategy_2_design_identity
authorization identity
operator-issuance identity
accepted repository HEAD
accepted origin/main
repository root
target repository-relative path
target absolute path
Windows account name
Windows account SID
elevation state
integrity level
inspection process identity
process provenance
command interpreter identity
Python interpreter identity if applicable
start-state Git evidence
end-state Git evidence
root existence result
root entry type
root reparse-point result
root containment result
pass-1 file count
pass-1 directory count
pass-1 recursive byte count
pass-1 manifest byte count
pass-1 manifest SHA-256
pass-2 file count
pass-2 directory count
pass-2 recursive byte count
pass-2 manifest byte count
pass-2 manifest SHA-256
pass-agreement result
owner observation
ACL observation
inheritance observation
executable-content flag
potentially-test-affecting-content flag
unknown-content flag
descendant_reparse_encountered
normalized-path-collision result
per-entry-read-failure result
mutation-detected result
prohibited-contact result
terminal classification
operator attestation
external whole-result SHA-256 after bytes are frozen
```

The whole-result SHA-256 must not be placed inside its own identity preimage. The whole-result identity must be computed externally after the result bytes are finalized.

Required normative values:

```text
strategy_rung_used:
2

strategy_2_design_identity:
the externally verified identity of this accepted design document

descendant_reparse_encountered:
boolean
```

For any successful stable-identity-resolution terminal state:

```text
descendant_reparse_encountered:
false
```

If a descendant reparse is encountered:

```text
descendant_reparse_encountered:
true
```

and the only permissible terminal route is:

```text
D. STRATEGY_2_TARGET_REPARSE_OR_PATH_ESCAPE_DETECTED_FAIL_CLOSED
```

The result must not claim complete file count, directory count, recursive byte count, or manifest identity after such termination.

## 18. Required Terminal Classifications

The future Strategy-2 result must end with exactly one terminal classification from this set or a stricter added fail-closed refinement:

```text
A. STRATEGY_2_ELEVATED_READ_ONLY_INSPECTION_COMPLETE_STABLE_IDENTITY_RESOLVED
B. STRATEGY_2_ELEVATED_CONTEXT_NOT_PROVEN_FAIL_CLOSED
C. STRATEGY_2_TARGET_ROOT_VERIFICATION_FAILED_CLOSED
D. STRATEGY_2_TARGET_REPARSE_OR_PATH_ESCAPE_DETECTED_FAIL_CLOSED
E. STRATEGY_2_MANIFEST_PASS_1_FAILED_CLOSED
F. STRATEGY_2_MANIFEST_PASS_2_FAILED_CLOSED
G. STRATEGY_2_MANIFEST_PASSES_DIFFER_FAIL_CLOSED
H. STRATEGY_2_PATH_CANONICALIZATION_OR_COLLISION_FAILED_CLOSED
I. STRATEGY_2_UNSUPPORTED_ENTRY_TYPE_FAILED_CLOSED
J. STRATEGY_2_PROHIBITED_MUTATION_DETECTED_FAIL_CLOSED
K. STRATEGY_2_PROHIBITED_CONTACT_DETECTED_FAIL_CLOSED
L. STRATEGY_2_INSPECTION_COMPLETE_IDENTITY_RESOLVED_POTENTIALLY_TEST_AFFECTING
M. STRATEGY_2_INSPECTION_COMPLETE_IDENTITY_RESOLVED_EXECUTABLE_OR_ACTIVE_CONTENT_PRESENT
N. STRATEGY_2_RESULT_IDENTITY_NOT_PROVABLE_FAIL_CLOSED
O. STRATEGY_2_OPERATOR_ABORTED_BEFORE_TRAVERSAL
P. STRATEGY_2_OPERATOR_ABORTED_DURING_READ_ONLY_INSPECTION_FAIL_CLOSED
```

A successful identity resolution must not itself admit, delete, quarantine, or approve the artifact.

Potentially test-affecting or executable content may still yield a complete identity-resolution result, but the result must route to later disposition without admitting the artifact.

Terminal classification `D. STRATEGY_2_TARGET_REPARSE_OR_PATH_ESCAPE_DETECTED_FAIL_CLOSED` covers both target-root reparse detection before traversal and descendant reparse detection after traversal begins.

## 19. State Transitions

This design-stage transition is:

```text
PRE_DESIGN_ONLY
    ->
DESIGN_COMPLETE_WITH_OPERATOR_PREREQUISITES
```

The future Strategy-2 act may transition only as follows:

```text
NOT_ISSUED
    ->
OPERATOR_ISSUED_NOT_STARTED
    ->
ELEVATED_CONTEXT_PROVEN
    ->
TARGET_ROOT_VERIFIED
    ->
MANIFEST_PASS_1_COMPLETE
    ->
MANIFEST_PASS_2_COMPLETE
    ->
PASS_AGREEMENT_PROVEN
    ->
RESULT_BYTES_FROZEN
    ->
RESULT_IDENTITY_COMPUTED_EXTERNALLY
    ->
STRATEGY_2_COMPLETE_STOP_BEFORE_DISPOSITION
```

Every failure state must stop further activity.

No failure state may transition automatically to Strategy 3. Strategy 3 may be considered only through a later separately authorized design after Strategy 2 is proven unavailable or unusable.

## 20. Explicit Non-Effects

Completion of Strategy 2 does not:

```text
admit the .pytest_cache
remove the .pytest_cache
quarantine the .pytest_cache
prove its origin
prove it harmless
prove repository-complete ignored-artifact enumeration
rerun or satisfy pre-contact verification
consume the implementation opportunity
begin implementation contact
activate Authority C
activate Authority D
activate Authority E
contact the canonical-input path
close BLOCKER-2
open BLOCKER-4
change FORMAL_HOLD
```

Origin determination is deliberately deferred to later disposition.

## 21. Design Preconditions For Future Issuance

The future operator issuance must prove:

```text
this design document identity is accepted
the earlier access-resolution design identity is accepted
the ignored-artifact disposition design identity is accepted
the issued bounded implementation operation remains VALID BUT SUSPENDED BEFORE FIRST CONTACT
implementation contact remains NOT STARTED
implementation opportunity remains NOT CONSUMED
Authority C/D/E remain INACTIVE
canonical-input path remains NOT CONTACTED
governed runner remains NOT EXECUTED
implementation-result document remains ABSENT
.git/index.lock is ABSENT
the repository root is the accepted checkout
the future elevated context already exists and was independently authorized
```

If any prerequisite is absent, stale, ambiguous, inconsistent, or not reproducible, the future operator issuance must fail closed.

## 22. Principal Design Classification

```text
B. PYTEST_CACHE_STRATEGY_2_ELEVATED_READ_ONLY_INSPECTION_AUTHORIZATION_DESIGN_COMPLETE_WITH_OPERATOR_PREREQUISITES
```
