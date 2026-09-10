# TORMENT post-P7 native production validation: Stage 1R6

## Result and boundary

The single identical private query returned **HTTP 200 in 27.672 seconds** with
all eight result-shape checks passing. Its measured server request span was
**27.647768 seconds**, compared with R5's **587.018371 seconds**. SQLite API time
fell from **581.451731 to 25.164343 seconds**.

All **471 profile verifications**, **468 membership recoveries**, and **three
outer whole-root recovery passes** remain. R6 directly measured **1,030 schema
validations** but **94 full integrity-check / foreign-key-check pairs**. The
bounded correction reuses successful physical validation during one unchanged
root membership closure; fresh logical and schema-catalog verification remains.

PER_MEMBERSHIP_FULL_DB_INTEGRITY_CHECK_REQUIRED_BY_FROZEN_SEMANTICS = NO.
POST_P7_NATIVE_VALIDATION_HOT_PATH_AMPLIFICATION = CONFIRMED_AND_CORRECTED.
Stage 1R6 passes its bounded correction and private-query scope. Stage 1 remains
HELD_FOR_REVIEW; the SQLite migration is not fully validated.

## Starting state and frozen authority

~~~text
STARTING_HEAD = f083521da8de2019e6e4eb7bbf49a00c9115e5c7
ORIGIN_MAIN_AT_START = f083521da8de2019e6e4eb7bbf49a00c9115e5c7
HEAD_EQUALS_ORIGIN_MAIN_AT_START = YES
TRACKED_WORKTREE_AT_START = CLEAN
BRANCH = main
PORT_8787_LISTENERS_AT_START = 0
~~~

Existing untracked artifacts were preserved. This record's containing commit is
the implementation revision. Final literal Git IDs, remote verification, tracked
worktree status, and this file's hash are recorded in the external
publication_verification.json and final delivery, avoiding a self-referential
commit hash inside the committed file.

Before launch and after normal shutdown, read-only observations agree on:

- Selector generation **8**, state **NATIVE_ACTIVE**.
- Active core **f21c730f-5222-4aa8-9a5f-1c1188456df3**, role ACTIVE_CORE,
  ever_active=true.
- Profile digest
  **35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a**.
- Immutable root admission digest
  **e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb**.
- Root completion witness v2, NATIVE_AGREEMENT, SQLite runtime **3.53.4**.
- The same exact seven-field deployment profile recovered from the selected
  core's immutable root-v2 admission record.

All project Python ran through Windows CMD with conda activate torment.
The service used python -m torment_service with process-local
TORMENT_DEPLOYMENT_PROFILE_JSON, TORMENT_EMBED_PROVIDER=st,
TORMENT_EMBED_STRICT=1, TORMENT_DIAGNOSTIC_QUERY_TIMING=1, and
HF_HUB_OFFLINE=1 under SETLOCAL. No external descriptor, data-root override,
model override, or generative provider was configured.

Both cache checks matched all **29** R3 cache/lock fingerprints, with no added,
removed, or changed files. Frozen certified refusals (35 memory and 23 motif)
and Character, motif, SRG, kernel, admission, selector, and profile semantics
were unchanged and were not recertified by this slice.

The R5 evidence record remains byte-identical, SHA-256:
**9b9b0013abd804d73b3dbac094809fc24847e0b5a7a83c89e2e2265de9c40bdb**.
Its historical SQLITE_MIGRATION_DIRECTLY_CAUSING_QUERY_TIMEOUT = YES remains
valid for that revision and has not been rewritten.

## Semantic-frequency review, completed before implementation

Direct frozen support comes from:

1. [Phase 4 transactional-core contract, section 19](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/docs/TORMENT_MEMORY_SUBSTRATE_PHASE_4_SQLITE_TRANSACTIONAL_CORE_CONTRACT_v0.1.md:217):
   SQLite structural integrity and TORMENT logical integrity are separate.
   Structural verification applies at migration/restore admission, relevant
   unclean recovery, corruption-error, and reconciliation boundaries. The
   contract explicitly does not require an expensive full scan at every
   ordinary clean startup merely because SQLite was selected.
2. [Phase 5 schema/migration design](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/docs/TORMENT_MEMORY_SUBSTRATE_PHASE_5_NATIVE_SCHEMA_TRANSACTION_MIGRATION_DESIGN_v0.1.md:204):
   current, older supported, and unknown/incompatible schema states have
   distinct write-admission rules. This does not attach a whole-database
   integrity scan to each membership verification.
3. [Phase 6 engineering blueprint, section 6](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/docs/TORMENT_MEMORY_SUBSTRATE_PHASE_6_DETAILED_SQLITE_ENGINEERING_BLUEPRINT_v0.1.md:772):
   qualification is a controlled connection/operation path with runtime,
   FK-enabled, WAL, schema, authority, and applicable structural-health gates.
4. [Phase 9D I1, section 3](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/docs/TORMENT_MEMORY_SUBSTRATE_PHASE_9D_I1_ROOT_SCOPE_MEMBERSHIP_RUNTIME_IDENTITY_v0.1.md:97):
   each resolution reconstructs committed membership state; a retirement
   must be observed before a later resolution returns the old active member.
5. [Phase 9D I1C, sections 1-3](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/docs/TORMENT_MEMORY_SUBSTRATE_PHASE_9D_I1C_ROOT_PROFILE_MEMBERSHIP_CORRECTIONS_v0.1.md:9):
   the supplied profile is a claim checked against current core metadata and
   current admissible object/revision facts. Membership pins the exact profile
   revision. No retained hot-path membership cache is qualified.

Inspection followed root_membership_closure_digest, _recover_memberships,
verify_root_profile_generation, current_root_profile_generation, open_schema,
_validate_schema, _recover_root_v2_workspace_runtime, and _recover_active_runtime,
plus their focused tests. Before R6, each successful profile verification
opened schema twice, and each schema open independently ran both full scans.
The logical profile and relationship SQL itself was already fresh.

| Question | Required validation and mechanism |
| --- | --- |
| A. Every membership | Fresh current profile claim, committed relationship revision/lifecycle, exact root/scope/namespace binding, and admissibility. Every existing recovery and resolve remains. |
| B. Every whole-root recovery | Fresh selector/core/profile agreement, admission/completion/disposition evidence, topology and namespace routing, complete membership closure, and structural-health gate. All three outer recoveries remain. |
| C. Every database connection | Existing qualified connection path and runtime, FK-enabled, WAL, schema/version, and applicable structural-health gates. Connection factories and their qualification are unchanged. |
| D. Admission/recovery/error boundaries | Full structural validation at required admission, restore, recovery, and error boundaries. R6 retains the stronger existing checks at all unscoped schema opens and at every new root closure; it does not move checking exclusively to startup. |
| E. Retirement freshness | Current relationship state is reread on every resolve, including inside one context. A committed retirement causes the next resolution to refuse the old active member. |
| F. Profile-generation changes | Every profile verification still reads current core metadata and current admissible profile object/revision. A successor generation invalidates the old claim and its pinned memberships. |
| G. Actual corruption | The unchanged real foreign_key_check and integrity_check run at fresh qualification/recovery boundaries and after a context observes data/schema/local-write change. Errors propagate and cannot publish reusable success. |

| Invariant | Current mechanism retained | Required frequency | Expensive whole-DB check inherently required? |
| --- | --- | --- | --- |
| Active core identity | Selector/core witnesses and current core metadata | REQUIRED at each existing owner recovery and current profile check | NOT_REQUIRED for the logical identity comparison |
| Selector generation | Exact deployment agreement | REQUIRED at each of the three owner recoveries | NOT_REQUIRED for the generation comparison |
| Deployment/root profile generation | Deployment digest and current profile object/revision | REQUIRED at every existing logical verification | NOT_REQUIRED for the profile comparison |
| Root membership visibility | Committed relationship recovery and exact binding | REQUIRED on every resolve | NOT_REQUIRED for the logical membership check |
| Retired membership freshness | Current committed lifecycle reread | REQUIRED on every later resolve, including inside a closure | NOT_REQUIRED for the lifecycle check |
| Schema compatibility | Existing metadata/catalog/table/index/trigger/strictness/governance/runtime-order/ledger validation | REQUIRED at every existing schema open | NOT_REQUIRED for the expensive full data scan; all catalog checks remain |
| Foreign-key integrity | PRAGMA foreign_key_check | REQUIRED at fresh recovery/qualification and invalidation boundaries | REQUIRED there; NOT_REQUIRED repeatedly for unchanged data inside the same closure |
| SQLite integrity | PRAGMA integrity_check | REQUIRED at fresh recovery/qualification and invalidation boundaries | REQUIRED there; NOT_REQUIRED repeatedly for unchanged data inside the same closure |

No security-critical frequency is UNESTABLISHED for this bounded correction.
The decision NO concerns repeated physical scans per membership, and does not
permit skipping any logical verification or required structural-health boundary.
The pre-implementation semantic_frequency_review.md is retained externally.

## Correction architecture and files

RootRecoveryIntegrityContext is created only around membership runtime
construction and member resolution inside root_membership_closure_digest.
It is one-use, bound to the exact connection, and expires before the closure
returns. Wrong-connection, not-entered, expired, and reentered use refuses.

Every nested schema open retains connection qualification and all existing
schema/catalog checks. Every profile and membership read retains its SQL and
validation order. Only a previously successful full FK/integrity pair may be
reused while the connection's main.data_version, main.schema_version, and
total_changes match. Before/after tokens bracket new full checks; a commit
during checking prevents publishing reusable evidence, and the next gate
repeats the pair. Failed checks clear reusable evidence and propagate.

The tokens observe external commits, schema changes, and local row changes:
[SQLite data_version documentation](https://www.sqlite.org/pragma.html#pragma_data_version),
[schema_version documentation](https://www.sqlite.org/pragma.html#pragma_schema_version),
and [total_changes documentation](https://www.sqlite.org/c3ref/total_changes.html).
These are read-only observations, not PRAGMA tuning. Comparison is only within
the same live connection.

This is not a membership snapshot or retained authority cache. No transaction,
connection pooling, process-global state, or cross-closure evidence reuse was
added. Fresh committed logical visibility remains the original behavior.
Out-of-band physical file damage without a SQL change is detected at the next
required fresh integrity boundary; the context is not an instantaneous
corruption monitor. R6 does not introduce or claim new snapshot semantics.

| Changed file | Bounded purpose |
| --- | --- |
| torment_service/substrate/schema.py | One-use context; unchanged physical checks extracted into helpers; three diagnostic stage counters |
| torment_service/substrate/root_profile.py | Thread the explicit private context through both existing schema opens |
| torment_service/substrate/root_scope_membership.py | Thread it through the reader/runtime and every fresh membership recovery |
| torment_service/substrate/root_blocker5_binding.py | Establish and expire the context inside one membership closure |
| tests/test_root_recovery_integrity_context.py | Structural-count regression, logical parity, lifetime, freshness, and disposable corruption tests |
| This evidence record | Semantic decision, qualification, production measurement, and review boundary |

The R5 instrumentation gate remains default OFF. Only schema.validation,
schema.foreign_key_check, and schema.integrity_check were added to measure the
specific correction. No search SQL, ranking, owner-recovery count, schema DDL,
index, WAL/cache/synchronous setting, timeout, model, or persistence format changed.

## Test-first and adversarial qualification

Before implementation, the count regression observed **7** full pairs for one
scope and **11** for three scopes. The corrected baseline run had **2 expected
amplification failures and 9 passing refusal cases**. The first authoring run
also used an overly narrow exception base in six refusal assertions; those
tests were corrected to the existing SubstrateError hierarchy before the
baseline was rerun. Both original logs are retained.

After correction:

| Validation | Result |
| --- | --- |
| Initial regression/refusal selection | 11 passed |
| Expanded R6 adversarial tests | 24 passed in 2.11 s |
| Focused owner, root-v2, membership/profile, qualified query, schema/governance, diagnostics, and R6 tests | **97 passed in 16.79 s**, exit 0 |
| Final R6 and diagnostic selection after adding direct diagnostic-count assertions | **30 passed in 4.39 s** |
| git diff --check | PASS |

The 30-case final selection is a rerun subset, not 30 additional distinct tests.
All tests used disposable databases and a new external pytest --basetemp with
-p no:cacheprovider. run_focused_tests.cmd records the reproducible 97-case
selection. Its files are test_root_recovery_integrity_context.py,
test_b5_a3_production_native_resource_owner.py,
test_post_i4_root_v2_production_recovery.py,
test_substrate_root_scope_membership.py, test_7g5e4e_native_query_read_model.py,
test_substrate_schema.py, test_substrate_schema_evolution_governance.py, and
test_diagnostic_query_timing.py.

| Required property | Practical evidence |
| --- | --- |
| No per-membership full scan | One- and three-scope closures each execute exactly one real FK/integrity pair; the next closure executes a fresh pair. Profile count is N+2 and schema-validation count is 2(N+2)+1. |
| Membership/profile result parity | Scoped and ordinary runtime results are equal across two workspaces. Full logical/catalog SQL trace and ordering are identical after excluding only physical checks and the new version probes. Four fresh profile claim reads remain in the two-scope case; full pairs fall from 9 to 1. |
| Wrong core/profile/membership | Wrong core, wrong generation, absent or retired membership, invalid semantic binding, and cross-workspace closure misuse refuse. |
| Authority, selector, and fallback | Existing owner/root-v2 tests retain deployment mismatch, core/completion disagreement, stale or missing authority, invalid profile, namespace/closure mismatch, and no-legacy-fallback refusal. |
| Retirement visibility | For both the same connection and a second connection: resolve active member, commit retirement, then resolve again inside the live context. The old active member refuses; the next closure also refuses. |
| Profile/core change visibility | The same sequence with committed successor profile or core metadata change refuses on the next resolution and next closure, for both writer locations. |
| FK failure detection | A disposable orphan row created with FK enforcement temporarily off is first confirmed by the real foreign_key_check. New closure and post-change context validation refuse; retry cannot reuse earlier success. |
| SQLite integrity failure detection | A disposable malformed identifier row inserted with CHECK enforcement temporarily off is confirmed by the real integrity_check. New closure and post-change validation refuse. This is actual CHECK-constraint corruption, not simulated random page damage. |
| Schema and connection guards | Unsupported schema version and FK-disabled connection refuse even with a previously successful context; wrong connection and expired/reentered context refuse. |
| Commit during validation | A second connection commits between real validation steps. The next gate reruns full checking instead of reusing evidence spanning that commit; a later unchanged gate may reuse success. |
| Qualified private/shared behavior | Existing disposable query-model tests preserve legacy-shaped results, exact lane qualification, workspace/namespace isolation, and admitted shared-domain reads for a private plan without a motif domain. |
| Diagnostic parity | Existing default-off, enabled, exception, SQL-trace, response, and timing tests pass; the new tests assert exact schema/full-scan counts. |

All seven preproduction semantic/refusal gates were recorded PASS in
preproduction_gates.json before the service launched. No production corruption,
retirement, profile transition, write, or repair was performed for these tests.

## One identical production request

Service PID **56652** started normally. Health returned HTTP 200 in 0.032 s,
NATIVE mode, strict ST provider, BAAI/bge-small-en-v1.5, dimension 384,
embedder_degraded=false. The canonical model remained local on CPU.

Exactly one POST /agent/query was sent at
**2026-09-10T08:01:27.374830+00:00**, with:

~~~text
workspace_id = audit_smoke_v0_2
agent_id = smoke_runner
domain_id = personal
top_k = 8
explain = true
continuity_debug = true
client_timeout = 240 seconds
query SHA-256 = 87c006c9b6f3609934e2cb92228df31747d4b1539c200dc3507949005e11ae8c
request-body SHA-256 = fd649d7ab10d0fc0b760b19ed68cb9dad91d366783116ca020dd0d8c6c293fb2
supplied vector = NONE
~~~

The payload and request/transport logic match R5. The helper additionally checks
the returned shape after receiving the response; the entire helper file is not
claimed byte-identical to R5.

The client received HTTP 200, **17,113 bytes**, in **27.672 s**.
Response SHA-256:
**3ede83b3a2c37a809e9b3286cd9afa4e2f149891d1ecaf62ba416b4f3b70e6ca**.
There were **five private hits**, domain_used=[personal], and zero authority
guard rejections. Raw returned memory text was not retained in the evidence.

Required keys, list shape, top_k bound, qualified hit shape, finite scores,
zero authority-guard rejection, excluded/filter_excluded alias parity, and
empty bridge-peek domains all passed. This verifies the actual production
response shape. Exact R5 response-body equality cannot be established because
that client timed out without receiving a body; logical/result parity is
established by the disposable tests and unchanged search logic.

One diagnostic request ID,
**7f96beff5a5546b4b9b28b5b8b947f64**, has request-start, endpoint-complete,
and ASGI-complete events. The endpoint returned normally, the ASGI status was
200, and final-body send returned. Delivery is independently confirmed by the
client receipt.

## R5 to R6 amplification and timing

Counts below are directly instrumented unless explicitly labeled otherwise.
Durations are inclusive and overlap their parent stages; do not add them.

| Operation | R5 calls | R6 calls | R5 seconds | R6 seconds |
| --- | ---: | ---: | ---: | ---: |
| Server request span | 1 | 1 | 587.018371 | 27.647768 |
| SQLite API leaf total | | | 581.451731 | 25.164343 |
| Native owner recovery | 3 | 3 | 551.033825 | 9.090723 |
| Whole-root recovery/verification | 3 | 3 | 548.062745 | 7.611819 |
| Root membership closure | 3 | 3 | 539.921854 | 3.592593 |
| Membership recovery | 468 | 468 | 537.858095 | 2.471900 |
| Root-profile verification | 471 | 471 | 537.195110 | 2.516387 |
| Schema validation | At least 942, code-derived lower bound | 1,030 | Not separately measured | 25.117923 |
| Full integrity_check | At least 942, code-derived lower bound | 94 | Not separately measured | 17.878632 |
| Full foreign_key_check | At least 942, code-derived lower bound | 94 | Not separately measured | 6.457423 |
| Actual local BGE encode | 3 | 3 | 0.058113 | 0.041211 |

R5's 942 is a lower bound from 471 successful profile verifications and two
schema opens per verification, not a directly instrumented total. R6 has
1,030 schema validations and 94 physical check pairs, a directly measured
difference of **936 reused pairs**.

The count is consistent with the bounded architecture: each 154-scope closure
performs 156 fresh membership/profile recoveries and 313 schema validations,
but one full pair. Across three closures this avoids 3 x 312 = 936 repeated
pairs. All other existing unscoped validations still run full checks. Thus the
94 total includes the three closure pairs and 91 outside them; R6 does not
claim only three full scans across the entire request.

The three whole-root passes still cover **154 scopes across 51 workspaces**
(76 private-agent and 78 shared-domain scopes) from the unchanged immutable
admission record. The count comes from existing evidence, not a new census.

Measured server duration is about **21.23 times shorter (95.29% lower)**.
This is a single R5/R6 observation with diagnostics enabled, not a repeated
benchmark or a controlled comparison with the former backend. The structural
call-count tests establish removal of the amplification independently of timing.
No target duration beyond avoiding the unchanged 240-second timeout was used
as a correctness substitute.

SQLite accounts for **91.017629%** of R6's request span. Leaf measurements are:
34 connects / 0.004901 s, 26,155 executes / 24.634775 s,
244,435 fetch boundaries / 0.512449 s, and 31 closes / 0.012218 s.
SQL execution counts need not fall: inexpensive version probes replace
expensive scans. Connect, execute, and close exception exits and BUSY/LOCKED
codes are zero. The 11,334 fetch exception exits include normal StopIteration,
as in R5, and are not a SQLite failure count.

The existing nonoverlapping exclusive span accounting sums to the
27.647767800022848 s request span. Named stages cover **99.986809%**.
SQLite API timings include row stepping, materialization, and waits inside
those calls; they are not isolated SQLite VM CPU measurements.

Remaining measured work includes motif geometry (2 calls, 11.504451 s),
active motif enrichment (1, 2.930857 s), and private search (1, 4.076681 s).
These overlap their SQLite children. Further optimization is outside R6.

## Model, search exposure, and continuation

All three BGE encodes total **0.041211 s**: existing agent-seed initialization
0.014770 s, Fabric query encoding 0.012962 s, and private vector-lane query
encoding 0.013479 s. Model loading and the startup dimension probe precede
query timing. No conversational/local generative model or external AI API was
configured or observed. The existing thinking advisory is local deterministic
draft/rule logic, not a generative provider.

The private request exercised one text-to-vector entry, one qualified vector
search, and one vector snapshot. The shared callback returned early, with no
qualified shared vector search or shared snapshot. No lexical/full-text search
was invoked. Model D's private motif-domain None and admitted shared-domain
qualification remain unchanged.

No optional separate shared query or production isolation campaign was run.
Disposable tests qualify private/shared isolation and shared lanes; they do
not substitute for the remaining production slice. No production writes,
reinforcement, Character, trajectory, or restart-persistence validation
followed the private query.

## Shutdown and evidence

One Ctrl+C initiated normal Uvicorn shutdown. The log records application
shutdown complete and finished PID 56652. Answering N to CMD's terminate-batch
prompt allowed the launcher to record Python exit code **0**. The process and
port-8787 listener were absent afterward. Read-only authority and cache checks
then passed.

External evidence directory:
C:\TORMENT\TORMENT_administration\post-p7-stage-1r6-20260910

It contains preflight and semantic review, test-first and passing logs,
preproduction gates, the process-local launcher and profile helper,
health/client receipts, raw timing aggregates and extracted summary, shutdown
receipt, post-shutdown authority/scale, and cache comparisons.
evidence_manifest.json hashes the top-level evidence and helpers, excluding
itself, the later publication receipt, and disposable fixture directories.
publication_verification.json binds final Git IDs, record hash, evidence
manifest hash, explicit commit scope, and tracked-worktree verification.

## Required return

Final literal FINAL_HEAD and ORIGIN_MAIN are supplied by publication
verification and the final response.

~~~text
STARTING_HEAD = f083521da8de2019e6e4eb7bbf49a00c9115e5c7
PER_MEMBERSHIP_FULL_DB_INTEGRITY_CHECK_REQUIRED_BY_FROZEN_SEMANTICS = NO
CORRECTION_IMPLEMENTED = YES
CORRECTION_SCOPE = ONE_USE_ROOT_MEMBERSHIP_CLOSURE_INTEGRITY_CONTEXT
AUTHORITY_DECISION_PARITY = PASS
MEMBERSHIP_RESULT_PARITY = PASS
PROFILE_VERIFICATION_PARITY = PASS
REFUSAL_PARITY = PASS
STALE_MEMBERSHIP_VISIBILITY_SEMANTICS_PRESERVED = YES
PROFILE_GENERATION_CHANGE_DETECTION_PRESERVED = YES
SQLITE_INTEGRITY_FAILURE_DETECTION_PRESERVED = YES
FOREIGN_KEY_FAILURE_DETECTION_PRESERVED = YES
FOCUSED_TESTS = PASS (97 selected cases; final subset rerun 30 passed)
ONE_ROOT_RECOVERY_DOES_NOT_PERFORM_PER_MEMBERSHIP_WHOLE_DB_INTEGRITY_SCAN = PASS
R5_ROOT_PROFILE_VERIFICATIONS = 471
R6_ROOT_PROFILE_VERIFICATIONS = 471
R5_WHOLE_ROOT_VALIDATION_CALL_COUNT = 3
R6_WHOLE_ROOT_VALIDATION_CALL_COUNT = 3
R6_SCHEMA_VALIDATION_COUNT = 1030
R6_INTEGRITY_CHECK_COUNT = 94
R6_FOREIGN_KEY_CHECK_COUNT = 94
R5_SQLITE_TIME = 581.451731 s
R6_SQLITE_TIME = 25.164343 s
R5_SERVER_QUERY_TIME = 587.018371 s
R6_SERVER_QUERY_TIME = 27.647768 s
R6_CLIENT_RESULT = RESPONSE (HTTP 200; shape PASS)
R6_CLIENT_ELAPSED = 27.672 s
PRIVATE_NATIVE_QUERY = PASS
SHARED_NATIVE_QUERY = NOT_RUN
PRIVATE_SHARED_SCOPE_ISOLATION = PASS_DISPOSABLE_TESTS; SEPARATE_PRODUCTION_CHECK_NOT_RUN
TEXT_SEARCH = PASS_TEXT_TO_VECTOR; LEXICAL_SEARCH_NOT_EXERCISED
VECTOR_SEARCH = PASS_PRIVATE; SHARED_NOT_EXERCISED
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = LOCAL_BGE_EMBEDDING_ONLY; 3_ENCODES; NO_GENERATIVE_PROVIDER
NORMAL_SHUTDOWN = PASS
SQLITE_ENGINE_DEFECT = NO_EVIDENCE
POST_P7_NATIVE_VALIDATION_HOT_PATH_AMPLIFICATION = CONFIRMED_AND_CORRECTED
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R6 = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R6_REVIEW
~~~

STOP at POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R6_REVIEW.
