# TORMENT — post-P7 native production validation, Stage 1R8B

Date: 2026-09-10 UTC.

**Stage 1R8B: PASS. Stage 1: PASS, bounded functional qualification.**
One reinforcement of the existing R8A memory persisted across a clean restart.
The existing Character observation matched before and after restart. A fresh
qualified native runtime reconstructed trajectory authority and emitted one
post-restart frame. No new memory was created.

Nonempty shared ranking remains **DEFERRED_EXISTING_CORPUS_EMPTY / NOT_YET_VALIDATED**.
Full SQLite migration validation remains **NO**. P1–P7, R8 and R8A remain closed.
Stage 2 was not begun.

## Authority and Git state

- Repository: C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric.
- Starting HEAD and origin/main: 9aff16162bc3cac5f64e7de726d1f0c3c40f5d35.
- Tracked worktree was clean at preflight and throughout the runtime exercise.
- Pre-existing untracked listing SHA-256:
  9ba939264bf6c6feb85775c430f010e89a41d417bdd3041dcdeef57c86fda467;
  unchanged after the runtime exercise.
- This result document is the sole intended repository change. No application,
  schema, configuration, policy, model, or validation-frequency change was made.
- The original Stage-1 work order §25 authorizes an evidence-only commit and
  push after git diff --check. The exact publication commit and actual remote
  HEAD are recorded in publication_verification.json and the final return.
  The commit containing this record is the final evidence commit.

Both service runs used Windows CMD, conda activate torment, and
python -m torment_service. Python was
C:/Users/Notandi/miniconda3/envs/torment/python.exe; SQLite was 3.53.4.
Both launchers recovered the same exact seven-field deployment profile from
the immutable selected-core root admission record into SETLOCAL, with no
external descriptor or data-root override:

~~~text
TORMENT_EMBED_PROVIDER=st
TORMENT_EMBED_STRICT=1
TORMENT_DIAGNOSTIC_QUERY_TIMING=1
HF_HUB_OFFLINE=1
~~~

Selector generation 8 remained NATIVE_ACTIVE. Core
f21c730f-5222-4aa8-9a5f-1c1188456df3 remained ACTIVE_CORE, ever_active=true,
with root-v2 completion and NATIVE_AGREEMENT.

~~~text
profile digest:
35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a
root envelope digest:
e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb
~~~

Both health responses were HTTP 200, ok=true, public_memory_mode=NATIVE,
with non-degraded st / BAAI/bge-small-en-v1.5 / dimension 384.
Normal public reads and the reinforcement succeeded without legacy public
fallback or maintenance-only posture.

## Exact existing memory and one reinforcement

The initial read-only EID alias join resolved exactly:

| Binding | Value |
| --- | --- |
| Workspace | lifecycle-e9f54df99882 |
| Agent | lifecycle-agent-e9f54df99882 |
| Operation domain | lifecycle_qualification |
| Scope / EID | private / 6 |
| Source namespace | 311cd3ac-175c-4532-83c7-87fdf84b4e4c |
| Identity namespace | 925405a4-ba68-4fd2-b19e-677a3d1f67f8 |
| Semantic scope | 1736a09d-acd3-494c-a0c4-e10c1ec624e2 |
| Object | 4b22364b-194b-4a9a-92a2-1cd3cb1589c1 |
| R8A current revision, ordinal 2 | 58737d7a-858c-411d-b1ec-17637725d844 |
| R8B current revision, ordinal 3 | 6b328bc2-87fd-4873-8856-343c5f8d381f |
| R8B READY representation | 2ded9ea8-24cb-4454-a609-9c366b087646 |

The starting core and trajectory table snapshots matched R8A's complete final
table snapshots. The current summary hash was
140aab4bcb5e2ef2326aaac66c048dfaf035e8f905e171165b4723e77047437f.

Ordinary reinforcement is implemented by the production ingest duplicate route:
POST /agent/ingest, through the spine, native public executor and
NativeFabricMemoryRouter._select_private_duplicate, then
NativeMemoryReinforcementService. One fresh request used the current stored
summary as text, step 1000202, and the new key below. The original R8A request
body and original idempotency key were not replayed. No summary or embedding
was supplied; normal offline BGE embedding and duplicate selection ran.

~~~text
Idempotency-Key:
R8B-20260910-68a1708b-4fed-41aa-85da-e2ab0736f1a2:reinforce
request SHA-256:
c8cde4cc60112680f613d1a916af99b6041177a24c2e0766a495af650531511f
derived native operation key:
public-mutation/v1/3e4bcc52fb4b7338537773e21ce0802dadbc950aecc60475c0882f773ef8e61a
~~~

Exactly one HTTP ingest returned 200 in 118.407 seconds: stored=true,
reinforced=true, eid=6, created_motif=null, proposal_id=null, path=fast,
escalated=false. It created a successor of the same object. Its existing
LEGACY_CORE_NODE compatibility kind does not imply legacy storage authority.

| Persisted reinforcement field | Before | After, including restart |
| --- | --- | --- |
| reinforcement_count | absent, existing semantics default 0 | 1 |
| strength | 0.9636289305094766 | 0.9745 |
| confidence | 0.960598008051933 | 0.960598008051933 |
| last_reinforced | 1000201 | 1000202 |
| last_reinforced_ts | absent | 1789032882 |

Strength matches the frozen non-tool formula:
round(min(0.98, old_strength + (1 - old_strength) * 0.3), 4).
The new 384-dimensional COMPAT_EMBEDDING representation is READY / USABLE,
bound to this object and revision 3. Its integrity measurement is
867934a7-bc33-414c-a27d-b0fa071449ba.

Ordinary POST /agent/query returned EID 6 in the correct private scope both
before and after restart, with reinforcement_count=1 and the same
last_reinforced_ts. Each result was joined read-only to its exact native alias,
current revision and semantic admission witness. The full three-revision
lineage, current payload hash, current revision and reinforcement fields matched
after restart and at final shutdown. The summary was unchanged. Incidental
query scores were not treated as persistence invariants.

## Existing Character continuity and isolation

The separate existing Character scope was
hivemind-natural-n5-v2-n5-20260825T201516Z-19a8097e25 / contrarian / research.
The same ordinary query, “P7 bounded native production smoke memory,” ran once
before restart and once after restart with top_k=8, explain=true and
continuity_debug=true. All ten Character context fields matched:
seed_preamble, seed_id, character_name, tier_breakdown, drift_score,
drift_summary, recommendations, drift_direction, seed_basin_role and
relational_count.

Character context SHA-256 before and after:
5c6fecada71ea04315f4ccb0a099a13362d0dc867e3ab595b418b9a6ddb17970.
This also matches the prior R8A observation. All observed files in that
workspace, including existing Character seed/state and identity files,
remained unchanged. No Character was created in the lifecycle scope.

After restart, bounded target-text queries in the contrarian/research scope
and audit_smoke_v0_2 / smoke_runner / personal returned respectively six and
five private control hits, with zero shared hits. The target marker and native
object were absent from both. Every returned hit passed exact workspace,
agent/domain, source-namespace, semantic-scope, current-lineage and summary
checks. No bridge peek was requested.

| Ordinary query | Client seconds |
| --- | ---: |
| read_after_reinforcement | 28.328 |
| character_pre_restart | 26.922 |
| read_after_restart | 28.188 |
| character_after_restart | 27.438 |
| isolation_other_agent | 28.031 |
| isolation_other_workspace | 28.828 |

These are functional observations only; no latency optimization was performed.

## Shutdown, restart and trajectory reconstruction

Run 1 used server PID 34268. Normal shutdown completed and the process exited
with code 0, leaving no listener on port 8787. Run 2 started normally as
PID 35536 with the identical qualified environment and native health posture.
After its checks, normal shutdown drained the final in-flight isolation query
to HTTP 200, completed application shutdown, and exited 0. No service process
or listener remained.

R8A already satisfied the pre-restart native trajectory-write requirement.
Its generation-4 authority, four settled native initialize/genesis/step/close
intents, and sealed V2 chunk still matched the frozen evidence. Therefore
NATIVE_TRAJECTORY_WRITE=PASS_R8A_RETAINED. No separate pre-restart trajectory
operation was manufactured. The authorized reinforcement naturally emitted
its ordinary world-step tail and sealed it at run-1 shutdown.

The post-restart ordinary reads changed neither core tables, trajectory
tables nor the observed external files. To obtain the one required actual
post-restart trajectory effect without another memory write, the external
helper used the existing
NativeWorldRuntime.advance_for_post_write_with_trajectory_evidence API.
It recovered a fresh NativeProductionResourceOwner from exact
NATIVE_AGREEMENT, opened ordinary admitted-workspace recovery, verified the
private binding, opened an existing qualified core connection, and initialized
the native world from the six current admitted native sources.

The helper acquired the owner's normal private trajectory runtime, advanced
the existing world once at step 1000203, and closed the owner to seal the tail.
It submitted no memory route, synthesized no entity or genesis, and made no
direct SQL update, handoff override or fencing change. Restart-rehydrated
birth/channel facts remained the existing runtime's unknown values.
This trajectory evidence belongs to the separate native helper PID 13456;
the restarted HTTP service handled the persistence and Character reads.
No public trajectory-write endpoint was added.

| Trajectory observation | R8A retained | R8B reinforcement | Post-restart step |
| --- | --- | --- | --- |
| Native authority generation | 4 | 5 | 6 |
| Writer PID | 12876 | 34268 | 13456 |
| Epoch / chunk sequence | 1 / 1 | 2 / 2 | 3 / 3 |
| Frame sequence in epoch | 1 | 1 | 1 |
| Logical step | 1000201 | 1000202 | 1000203 |
| Frames / records | 1 / 6 | 1 / 6 | 1 / 6 |

All three sealed chunk hashes and decoded frames were verified. Each frame
contains exactly EIDs 1–6 and expected population 6. The hash chain is:

~~~text
epoch 1: 1e49e767e53c6b9062e51c38f9aa0c2bdaac64d3163ab23e2dd77e38c64facad
epoch 2: 2e62cd7385bf68b221284d9a4facb5e57b381bbcb8dcb73831d510a80c38e314
epoch 3: e9005a93cbae9875f20376ee367c68d16f2398ee1720683b7f1f6979885ba9c9
~~~

Scope authority key:
b0f5ad876858c381a82a9c3e9f082d63abe884babaa09cbb07e8beabf4ead738.
HANDOFF_COMPLETE remained in force; legacy_fence_generation stayed 2 and
legacy_session_identity stayed null. The two new handoff events are
NATIVE_SESSION_FENCED_REPLACEMENT. The native writer identities were:

~~~text
run 1: pid:34268:99a09a7b-eefe-4886-851c-832bfc397f88
post-restart helper: pid:13456:970c70fe-a5dd-4ec7-b9bc-ef630295af2e
~~~

Each new session has exactly three SETTLED native intents: initialize, V2 step,
and V2 close. Their exact intent IDs are retained in account_after_shutdown.json.
The native memory core was byte-identical before and after the post-restart
trajectory operation.

An external-helper precheck initially accessed motif_domain_id on
NativeFabricRoutingScope, which has no such field. This AttributeError occurred
before trajectory acquisition, intent creation or world-step invocation.
Complete core tables, trajectory tables, external-file fingerprints and selector
were unchanged. The failed helper, result and logs are preserved. The corrected
precheck reads that fact from the immutable root scope plan. The one actual
trajectory invocation then passed. This was an evidence-helper correction;
no service code was repaired and no trajectory operation was replayed.
An earlier read-only lineage formatter also required a missing-summary-safe
projection for the existing R1 precommit payload; no request was replayed.

## Durable mutation accounting

NEW_MEMORY_COUNT_R8B=0. The only existing core row changed was the target
object's current-revision pointer. Its original revisions remain unchanged.
One NATIVE_ORDINARY revision and one READY representation were appended.
No new memory object, motif object, alias, membership relationship or
enumeration entry was created.

| Core table with a delta | Added | Changed | Removed |
| --- | ---: | ---: | ---: |
| integrity_expectations | 1 | 0 | 0 |
| integrity_measurement_effects | 1 | 0 | 0 |
| integrity_measurements | 1 | 0 | 0 |
| object_revision_effects | 1 | 0 | 0 |
| object_revision_governance | 1 | 0 | 0 |
| object_revisions | 1 | 0 | 0 |
| objects | 0 | 1 | 0 |
| operation_outputs | 3 | 0 | 0 |
| operations | 8 | 0 | 0 |
| representation_current_state | 1 | 0 | 0 |
| representation_payloads | 1 | 0 | 0 |
| representation_state_effects | 2 | 0 | 0 |
| representations | 1 | 0 | 0 |
| semantic_transitions | 3 | 0 | 0 |

All eight operations belong to the one fresh request in private idempotency
namespace df94c51a-3b6d-466e-a7bb-a2cbb2eefb37: four public receipt stages,
one NATIVE_MEMORY_REINFORCEMENT_SOURCE, and three representation stages.
All three semantic transitions are owned by those operations.

Only the selected trajectory authority row changed in the sidecar, with two
new native session-replacement events and six settled write intents. External
effects are the selected agent's ordinary roles.json update, trajectory
boundaries and manifest updates, and the two new sealed chunks. No genesis
file changed. All 51 prior policy observations and both control-workspace file
sets remained unchanged. The recent data-file inventory contained only these
effects and normal SQLite access/sidecar files.

Final core: 82,825,216 bytes; SHA-256
86b53a0566ddcfe6ff5138ad510f7af2f336ccd54776515d97898cb82a596430.
Final trajectory authority database: 827,392 bytes; SHA-256
2afd3902e1089a2361309bdc8c7257b82c3d69c8b657f8dfb9f0a2a31dba0e1d.
Both WAL files were zero length at final capture. Empty WAL/SHM lifecycle from
ordinary SQLite access is not a semantic mutation.

Model D is preserved: private motif_domain_id=None, admitted
lifecycle_qualification operation routing, and strict shared-domain readers.
The fixed prior 35 refused memory and 23 refused motif identities were checked
against actual returned hits and the bounded native delta. No refused object
received a successor or READY promotion; no refusal leaked into returned
results. P3 was not recensused.

No generative conversational model or external AI API was involved. Normal
embedding used only local offline BAAI/bge-small-en-v1.5 on CPU.
All 29 BGE cache/lock file fingerprints matched the prior frozen cache proof.
The native trajectory helper required no embedding model. No model, policy,
compression or performance configuration was changed.

## Evidence and closure

External evidence directory:
C:/TORMENT/TORMENT_administration/post-p7-stage-1r8b-20260910.

The manifest freezes 92 evidence files and 20
prior-stage/work-order references. It includes request intents and receipts,
all six redacted query observations, exact target lineage observations, both
launch environments and service logs, shutdown proofs, full table row
fingerprints, the retained R8A trajectory proof, both helper precheck records,
the actual post-restart trajectory result, durable accounting, cache
verification, and the result verifier.

~~~text
evidence_manifest.json SHA-256:
9d90833ef6f1cbff55da0401beb3dc703178420ae6ac11c7fa26ccfc091ee4d9
result_verification.json SHA-256:
d621ad8315c77d4f5fcfa422f20bfb307a2aa14e88f8f088b1c864fdde372ca3
result verification: 44/44 checks PASS
~~~

The repository check is git diff --check, followed by exact-path staging and
the evidence-only commit/push under the original Stage-1 Git policy. No test
suite was rerun for a documentation-only repository change; the live lifecycle
and retained evidence checks above are the validation.

R6's corrected private read PASS, R7's bounded read parity PASS, R8A's native
write/read/isolation PASS, and R8B's reinforcement/Character/restart/trajectory
PASS together qualify Stage 1 as PASS. R8's earlier policy refusal remains
frozen and is not reclassified as a successful write. Nonempty shared ranking
remains unvalidated because the existing shared corpus is empty.

The work order §25 identifies Stage 2 as the future direction, while its
explicit §26 required return ends at R8B_REVIEW. This record uses the explicit
required-return boundary. Stage 2 needs the next review/authorization and has
not begun.

~~~text
R8A_MEMORY_PRESENT_AT_R8B_START = YES
R8B_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
MAINTENANCE_ONLY_POSTURE = NO
NATIVE_REINFORCEMENT = PASS
REINFORCEMENT_VISIBLE_PRE_RESTART = PASS
CHARACTER_TEST_SCOPE = hivemind-natural-n5-v2-n5-20260825T201516Z-19a8097e25 / contrarian / research
CHARACTER_CONTINUITY_PRE_RESTART = PASS
R8A_NATURAL_INGEST_TRAJECTORY_SATISFIES_STAGE1_PRE_RESTART_WRITE = YES
NATIVE_TRAJECTORY_WRITE = PASS_R8A_RETAINED
NORMAL_SHUTDOWN = PASS
RESTART_STARTUP = PASS
LEGACY_PUBLIC_FALLBACK_AFTER_RESTART = NO
MAINTENANCE_ONLY_AFTER_RESTART = NO
MEMORY_PERSISTENCE_AFTER_RESTART = PASS
REINFORCEMENT_PERSISTENCE_AFTER_RESTART = PASS
CHARACTER_CONTINUITY_AFTER_RESTART = PASS
TRAJECTORY_AUTHORITY_RECONSTRUCTION = PASS
POST_RESTART_NATIVE_TRAJECTORY_WRITE = PASS
NEW_MEMORY_SCOPE_ISOLATION_AFTER_RESTART = PASS
NEW_MEMORY_COUNT_R8B = 0
AUTHORIZED_DURABLE_MUTATION_ONLY = PASS
MODEL_D_PRESERVED = YES
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = NONE; local offline BGE embeddings only
NONEMPTY_SHARED_RANKING = DEFERRED_EXISTING_CORPUS_EMPTY
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8B = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = PASS
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R8B_REVIEW
~~~
