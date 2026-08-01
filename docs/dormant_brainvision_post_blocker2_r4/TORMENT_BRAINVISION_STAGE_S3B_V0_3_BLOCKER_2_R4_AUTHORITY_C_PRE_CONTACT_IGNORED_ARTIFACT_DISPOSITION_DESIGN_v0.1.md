# TORMENT Brainvision Stage S3B v0.3 BLOCKER-2 R4 Authority C Pre-Contact Ignored Artifact Disposition Design v0.1

## 1. Scope

This draft addresses the two ignored repository artifacts discovered during immediate pre-contact verification after issuance of the bounded non-commit implementation-operation authorization.

This draft does not authorize implementation, deletion, quarantine, normalization, Git index modification, Git ignore-rule modification, or contact with the canonical-input path.

The operation state remains:

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

The failed pre-contact verification did not begin implementation contact, did not consume the opportunity, did not activate Authority C/D/E, did not contact the canonical-input path, and did not execute the governed runner. No retry has occurred yet. A later rerun is a continuation of pre-contact verification, not reuse after consumption.

## 2. Read-only Evidence Base

Repository evidence:

```text
repository root:
C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric

branch:
main

HEAD:
1f915e29119cd58ea39e8cf355f7364118c71043

local origin/main:
1f915e29119cd58ea39e8cf355f7364118c71043

.git/index.lock:
ABSENT
```

Tracked and Git-visible status evidence:

```text
staged entries: 0
tracked deletions: 0
unmerged entries: 0
authoritative filtered tracked status: empty
Git-visible untracked inventory: exactly the expected eleven R4 Markdown governance drafts
unexpected Git-visible untracked entries: 0
```

Read-only artifact commands used:

```text
git --no-optional-locks check-ignore -v -- scratch/substrate_free_design_council/2026-06-15/.pytest_cache research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json.tmp
dir /a /t:c scratch\substrate_free_design_council\2026-06-15
dir /a /t:w scratch\substrate_free_design_council\2026-06-15
dir /a /t:c research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal
dir /a /t:w research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal
dir /a /t:c research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal\current_state.json.tmp
dir /a /t:w research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal\current_state.json.tmp
attrib scratch\substrate_free_design_council\2026-06-15\.pytest_cache
icacls scratch\substrate_free_design_council\2026-06-15\.pytest_cache
dir /a /s /b scratch\substrate_free_design_council\2026-06-15\.pytest_cache
python -B -c os=__import__('os');p='scratch/substrate_free_design_council/2026-06-15/.pytest_cache';print('exists',os.path.exists(p));print('isdir',os.path.isdir(p));print('isfile',os.path.isfile(p));print('stat_size',os.stat(p).st_size)
certutil -hashfile research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal\current_state.json.tmp SHA256
git --no-optional-locks grep -n --fixed-strings "independent_order_sensitive_synthetic_validation_v0_2" -- .
git --no-optional-locks grep -n --fixed-strings "current_state.json.tmp" -- .
git --no-optional-locks grep -n --fixed-strings "scratch/substrate_free_design_council" -- .
git --no-optional-locks grep -n --fixed-strings "independent_order_sensitive_synthetic_validation_v0_2" -- research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
git --no-optional-locks grep -n --fixed-strings "current_state.json.tmp" -- research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
git --no-optional-locks grep -n --fixed-strings "scratch/substrate_free_design_council" -- research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py
```

Access-time caveat:

```text
fsutil behavior query disablelastaccess:
DisableLastAccess = 2  (System Managed, Last Access Time Updates ENABLED)
```

Therefore last-access timestamps are not used as binding evidence. Creation and last-write timestamps are used only as low-trust supplemental evidence.

Issued authorization timestamp comparator:

```text
accepted bounded-operation authorization creation time:
07/30/2026 10:07 PM

accepted bounded-operation authorization last-write time:
07/30/2026 10:23 PM

accepted operator-issuance instrument creation time:
07/30/2026 11:20 PM

accepted operator-issuance instrument last-write time:
07/31/2026 12:14 AM
```

## 3. Artifact 1: scratch pytest cache directory

Principal disposition:

```text
E. ARTIFACT_IDENTITY_OR_ORIGIN_NOT_PROVABLE_FAIL_CLOSED
```

Identity:

```text
absolute path:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\scratch\substrate_free_design_council\2026-06-15\.pytest_cache

relative path:
scratch/substrate_free_design_council/2026-06-15/.pytest_cache

artifact type:
directory

ignored-by rule:
.git/info/exclude:7:scratch/

file count:
UNPROVABLE

recursive byte count:
UNPROVABLE

deterministic recursive manifest identity:
UNPROVABLE
```

Supplemental timestamp evidence:

```text
parent directory creation listing shows .pytest_cache:
06/18/2026 06:18 PM <DIR> .pytest_cache

parent directory last-write listing shows .pytest_cache:
06/18/2026 06:18 PM <DIR> .pytest_cache

authorization/instrument creation-write window:
07/30/2026 10:07 PM through 07/31/2026 12:14 AM
```

Predating determination:

```text
whether it predates this bounded operation:
LOW-TRUST TIMESTAMP EVIDENCE INDICATES YES

whether it was created by this verification:
NO, based on command history and the older creation/write timestamp evidence
```

Recursive-manifest determination:

```text
whether a recursive deterministic manifest can safely bind current contents:
NO

reason:
icacls returned "Access is denied"; git ignored-status inspection warned "could not open directory ... Permission denied"; dir /a /s /b returned "File Not Found"; Python stat could prove only existence, directory type, and stat_size 0. These facts do not establish a reliable recursive manifest, file count, recursive byte count, or content identity.
```

Surface relationship:

```text
belongs to authorized three-file implementation surface:
NO

belongs to separately authorized result-document path:
NO

excluded from authorized write surface:
YES
```

Impact analysis:

```text
can affect implementation behavior:
UNPROVABLE, because contents and permissions cannot be bound read-only

can affect test discovery or execution:
UNPROVABLE, because a pytest-cache directory exists and cannot be recursively inspected

can affect import resolution:
UNPROVABLE, because recursive contents cannot be bound

can affect repository identity proofs:
YES for ignored-artifact and baseline proofs; NO for tracked-content identity proofs already shown clean

can affect canonical-input path non-contact:
NO DIRECT MECHANISM OBSERVED; it is not the canonical-input path and was not used to establish contact

can create ambiguity in post-operation unexpected-files evidence:
YES, because it is ignored and cannot currently be manifest-bound
```

Authorization analysis:

```text
mere presence violates the issued authorization:
It violates the explicit pre-contact artifact-absence prerequisite, but it is not proven to be an implementation-created unauthorized artifact.

removal would require separate write/removal authorization:
YES

quarantine would require separate write/move authorization:
YES
```

No deletion or quarantine is authorized by this draft.

## 4. Artifact 2: independent validation current_state temp file

Principal disposition:

```text
B. PRE_EXISTING_IGNORED_ARTIFACT_REQUIRES_SEPARATE_REMOVAL_AUTHORIZATION
```

Identity:

```text
absolute path:
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\research\brainvision\results\.independent_order_sensitive_synthetic_validation_v0_2.execution_journal\current_state.json.tmp

relative path:
research/brainvision/results/.independent_order_sensitive_synthetic_validation_v0_2.execution_journal/current_state.json.tmp

artifact type:
file

ignored-by rule:
research/brainvision/.gitignore:2:results/

byte count:
136

SHA-256:
b0910c0e5266d23105faae3fc2228396cb5ea54fbc5f33561bd891818c00b11b
```

Supplemental timestamp evidence:

```text
file creation time:
07/23/2026 10:22 PM

file last-write time:
07/23/2026 10:22 PM

authorization/instrument creation-write window:
07/30/2026 10:07 PM through 07/31/2026 12:14 AM
```

Predating determination:

```text
whether it predates this bounded operation:
YES, by low-trust timestamp evidence and by its existence before the current disposition drafting operation

whether it was created by this verification:
NO, based on command history and the older creation/write timestamp evidence
```

Tracked-code relationship:

```text
git grep for current_state.json.tmp:
no tracked references

git grep for independent_order_sensitive_synthetic_validation_v0_2:
research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py defines the execution journal path

tracked context:
_current_state_path(journal_or_arming_dir) returns current_state.json
_write_current_state_atomic sets temp_path = target + ".tmp"
```

Authorized BLOCKER-2 runner relationship:

```text
git grep in research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py for independent_order_sensitive_synthetic_validation_v0_2:
no matches

git grep in research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py for current_state.json.tmp:
no matches

git grep in research/brainvision/run_blocker2_authoritative_retained_single_run_v0_1.py for scratch/substrate_free_design_council:
no matches
```

Surface relationship:

```text
belongs to authorized three-file implementation surface:
NO

belongs to separately authorized result-document path:
NO

excluded from authorized write surface:
YES
```

Impact analysis:

```text
can affect implementation behavior:
NO direct effect on the authorized BLOCKER-2 runner was found by tracked-only exact-string search; however, it can affect the separate independent-order-sensitive validation runner if that runner attempts an exclusive atomic write to current_state.json.tmp.

can affect test discovery or execution:
POSSIBLY, if tests or operators exercise the independent-order-sensitive validation runner against the existing local results path; it is not a pytest discovery file by type or location.

can affect import resolution:
NO, it is a JSON temp file under ignored results, not a Python module/package path.

can affect repository identity proofs:
YES for explicit ignored-artifact absence and post-operation unexpected-files evidence; NO for tracked-content identity proofs.

can affect canonical-input path non-contact:
NO DIRECT MECHANISM OBSERVED; it is not the canonical-input path and was not used to establish contact.

can create ambiguity in post-operation unexpected-files evidence:
YES, unless removed under separate authority or explicitly frozen by a separate accepted baseline rule.
```

Removal disposition:

```text
why presence is inadmissible:
The pre-contact verification explicitly required absence of *.tmp artifacts. This file is also an exclusive-write temp residue for a tracked runner family, so its presence is operationally meaningful rather than merely cosmetic.

why action cannot occur under the issued three-file operation:
Removal would alter an ignored path outside the authorized three-file implementation surface and outside the separately authorized result-document path.

exact separate operator authorization required:
A non-commit ignored-artifact removal authorization naming exactly this absolute path and relative path, forbidding any other deletion, movement, ignore-rule edit, Git index operation, implementation contact, canonical-input contact, governed-runner execution, staging, commit, or push.

whether opportunity remains NOT CONSUMED:
YES

whether the issued bounded operation remains valid but suspended:
YES, it remains ISSUED_NON_COMMIT but cannot cross first contact.

whether pre-contact verification must be rerun from the beginning afterward:
YES

whether the 303-file CRLF proof must be rerun afterward:
YES

whether deletion or movement may create parent-directory residue:
YES; parent-directory state must be checked, and parent removal is not authorized unless separately named.

whether Git ignore rules may be changed:
NO
```

No deletion or quarantine is authorized by this draft.

## 5. Required Distinctions

Pre-existing ignored residue:

```text
An ignored file or directory already present before bounded implementation contact. It may still block pre-contact verification if absence was required or if identity cannot be bound.
```

Implementation-created unauthorized artifact:

```text
A file or directory created after implementation contact outside the authorized write surface. No such artifact is proven here because implementation contact has not started.
```

Verification-created artifact:

```text
A file or directory created by read-only verification itself. No such artifact is proven here; the verification commands did not write repository files.
```

Post-contact unexpected artifact:

```text
An untracked, ignored, or otherwise unexpected file appearing after first implementation contact. Because contact has not started, neither discovered artifact is classified as post-contact.
```

## 6. Rerun Conditions

Pre-contact verification may be rerun only after one of these governance paths is explicitly resolved:

```text
1. Separate removal authorization removes the current_state.json.tmp file and verifies parent-directory residue without changing ignore rules.
2. Separate elevated inspection/remediation authorization resolves the unreadable .pytest_cache directory and either binds a deterministic manifest or authorizes exact removal/quarantine.
3. Any accepted baseline-binding path must require absolute path, relative path, artifact type, byte count or recursive byte count, file count for directories, SHA-256 for files, deterministic recursive manifest identity for directories, ignore-rule provenance, proof it predates bounded implementation contact, proof it remains unchanged during implementation, exclusion from the authorized write surface, and re-verification at result capture.
```

The rerun must start from the beginning of pre-contact verification, including repository identity, index/tracked state, complete untracked inventory, ignored-artifact absence or accepted baseline binding, whole-repository raw-byte proof, the 303-file CRLF presentation-only proof, governance identities, opportunity-key reconstruction, runner identity, retained-control identity, candidate path absence, implementation-result absence, authority inactivity, governed-runner non-execution, canonical-input non-contact, and implementation-opportunity non-consumption.

## 7. Overall Classification

```text
E. PRE_CONTACT_IGNORED_ARTIFACT_DISPOSITION_NOT_PROVABLE_FAIL_CLOSED
```

Rationale:

```text
The .pytest_cache directory cannot be recursively identity-bound read-only because access/manifest proof failed. The current_state.json.tmp file has a bindable identity but requires separate removal authorization because it violates the explicit *.tmp absence condition and can affect a tracked runner family's exclusive atomic-write behavior. Therefore the current implementation opportunity remains not consumed, but the issued operation cannot cross first contact until separate governance resolves these ignored artifacts and pre-contact verification is rerun from the beginning.
```
