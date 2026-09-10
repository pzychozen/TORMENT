# TORMENT — Stage 4 failure/recovery characterization

2026-09-10 UTC. **POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4 = BLOCKED_DISPOSABLE_ROOT_ADMISSION.**

Stage 4 stopped at its disposable-root safety gate, before baseline service
startup or failure injection. A byte-identical copy retains valid native
selector/core evidence, but its trajectory coordinator refuses the relocated
root because the persisted coordinator identity names the production path.
No failure/recovery scenario passed or failed: none was run.

## Starting state and copy

Starting HEAD = origin/main = 4e697ed7d7c787912247713af2a4ff7fca79aae7;
tracked worktree clean. P1–P7 and Stages 1–3 remain closed. This result document
is the only repository change. Its final publication commit, remote comparison,
clean tracked worktree and preserved untracked listing are recorded in external
publication.json and the final return.

All Python administration used Windows CMD with conda activate torment.
The runtime was SQLite 3.53.4. No production or disposable service was launched;
there was no port-8787 listener and no active Python service at preparation.

The established cold-copy approach is documented in
docs/TORMENT_DATABASE_CONVERGENCE_POST_P4_PRE_P6_ACTIVATION_REHEARSAL_REVIEW_v0.1.md,
section 2. That earlier rehearsal copied a P4 root and then crossed P5–P7;
it does not establish portability of the current post-handoff coordinator.
The synthetic disposable-root builder in
tests/test_post_i4_full_root_disposable_rehearsal_r1.py constructs and admits a
new root, rather than relocating this current authority history.

Source: C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/data.
Destination: C:/TORMENT/TORMENT_administration/post-p7-stage-4-20260910/copy/data.
The quiescent full-tree copy used shutil.copytree/copy2, retained existing
SQLite DB/WAL/SHM files and trajectory artifacts, and contained no reparse
points or hard-link substitution. Source and destination were disjoint.
All 2,093 files / 1,163,889,969 bytes matched
by relative path, size and SHA-256 immediately after construction.
No selector, core, metadata, receipt, trajectory path or generation was rewritten.

DISPOSABLE_ROOT_CREATED = YES.
DISPOSABLE_ROOT_SOURCE_STATE = current post-Stage-3 native root, selector
generation 8, lifecycle population 15 inherited from Stage 3, trajectory
generation 10 / HANDOFF_COMPLETE / legacy fence 2.
DISPOSABLE_ROOT_PRODUCTION_FAITHFUL = NO for runnable authority admission;
the physical copy itself was byte-identical.

## Concrete admission refusal

Read-only copied selector/core inspection returned NATIVE_AGREEMENT,
NATIVE_ACTIVE and core f21c730f-5222-4aa8-9a5f-1c1188456df3 / ACTIVE_CORE.
The effective seven-field profile retained digest
35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a;
envelope e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb.

Calling the existing TrajectoryWriterHandoffCoordinator.open_existing on the
disposable root raised:

~~~text
TrajectoryHandoffRefused: trajectory authority database metadata is missing or incompatible
~~~

The copied authority_metadata.data_root still names the production root.
The requested coordinator root is the destination above. The selected copied
lifecycle artifact_root also still names its production location. The
coordinator database bytes stayed unchanged by the admission probe.

The boundary is explicit in torment_service/substrate/trajectory_writer_handoff.py:
_validate_database at line 1052 compares the stored data_root to the resolved
coordinator root; TrajectoryScopeIdentity at line 101 includes the resolved
artifact_root in its payload and exclusivity digest. A simple string rewrite
would therefore change authority identities beyond a filesystem copy.
The inspected coordinator API and repository administration expose no qualified
relocation operation that preserves this current history and its bindings.

Section 5 of the work order says: "If a faithful isolated root cannot be
established safely: STOP." This refusal triggers that gate. No coordinator
metadata edit, coordinator removal/reinitialization, generation reset, migration
rerun, or production-path alias was used to bypass it. It is a copy-admission
limitation, not evidence of a production recovery defect or SQLite corruption.

## Baseline and scenarios

| Observation | Result |
| --- | --- |
| Copied selector/core agreement | PASS, read-only metadata observation |
| Copied SQLite and foreign-key integrity | PASS for core, selector and trajectory authority |
| Baseline service startup / native owner recognition | NOT_RUN_COPY_ADMISSION_BLOCKED |
| Baseline read / write / read-after-write | NOT_RUN_COPY_ADMISSION_BLOCKED |
| A: committed write and abrupt restart | NOT_RUN_COPY_ADMISSION_BLOCKED |
| B: interrupted in-flight write / partial publication / receipt recovery | NOT_RUN_COPY_ADMISSION_BLOCKED |
| C: bounded lock contention | NOT_RUN_COPY_ADMISSION_BLOCKED |
| D: stale writer refusal / current writer acceptance | NOT_RUN_COPY_ADMISSION_BLOCKED |
| E: native authority reconstruction after failure | NOT_RUN_COPY_ADMISSION_BLOCKED |
| Scope / Character observations after failure | NOT_RUN_COPY_ADMISSION_BLOCKED |
| Model D | NOT_OBSERVED |

The existing SQLite integrity helpers from substrate/schema.py checked the
three copied databases once over read-only connections. No structural or
foreign-key error was found. These checks precede failure injection and are
not post-failure recovery evidence. Existing public-ingest interruption hooks
were located, but none was exercised after the earlier admission gate failed.
There were zero ordinary HTTP requests, writes, abrupt terminations, held locks,
or stale-writer attempts. No runtime certified-refusal leak was observed;
runtime leakage and hidden fallback were not tested in this stage.

## Production postcheck and review boundary

The final read-only production observation matched Stage-4 preflight exactly:
all 2,093 files, including DB/WAL/SHM and trajectory evidence,
retained identical size and content hashes. Changed paths: zero.
Tree SHA-256: 345d29441220273acc1371641be08e4e0dfd0fc381018b16a601b16dfb648776.
Selector generation 8 / NATIVE_ACTIVE, NATIVE_AGREEMENT, selected core and
lifecycle trajectory generation 10 with legacy fence 2 remained unchanged.
No production service was started and no failure injection contacted the real root.

External evidence: C:/TORMENT/TORMENT_administration/post-p7-stage-4-20260910.
It includes the preserved disposable copy, construction proof, admission refusal,
copied integrity results, pre/post production inventories and publication record.
Evidence manifest SHA-256: 1f05ac085cf6cde405568cd4e0bffd40a715c8ce15bac7e6394218d7e6fececc.
Only this documentation record is committed; git diff --check validates its
formatting. No application change or test-suite campaign was performed.

~~~text
REAL_ROOT_UNCHANGED_BY_STAGE4_FAILURE_INJECTION = YES
REAL_SELECTOR_CORE_AGREEMENT = PASS
REAL_NATIVE_ACTIVE = YES
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = NONE; no model invoked; offline BGE-only boundary retained
NONEMPTY_SHARED_RANKING = NOT_YET_VALIDATED; DEFERRED_EXISTING_CORPUS_EMPTY
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4 = BLOCKED_DISPOSABLE_ROOT_ADMISSION
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_4_REVIEW
~~~

Review must establish an authorized, qualified method for isolating the current
trajectory authority before these failure scenarios can proceed. No repair or
further validation stage was started.
