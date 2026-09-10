# TORMENT — Stage 3 native scale and memory growth

2026-09-10 UTC. **POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_3 = PASS.**

Existing qualification corpora of 28, 114 and 505 memories served correct scoped
retrievals. Ordinary lifecycle ingestion grew the selected native corpus from
9 to 12 to 15 memories. Representative existing and new memories remained
available after growth and clean restart, with Character and trajectory
continuity intact. This is bounded characterization; P1–P7 and Stages 1–2 remain closed.

## Git and runtime

Starting HEAD = origin/main = e2d69f0e326c714ef779f7eade2a1a7cdb1d02f3;
tracked worktree clean. This document is the only repository change. The final
evidence-only publication commit has that starting commit as its parent;
the actual final HEAD/origin/main comparison, tracked-clean check and unchanged
preexisting untracked listing are recorded in external publication.json and
the final return.

Both service processes used Windows CMD, conda activate torment, and
python -m torment_service under the established root-v2 seven-fact profile.
HF_HUB_OFFLINE=1, strict st embeddings and diagnostic query timing OFF remained
unchanged. SQLite runtime: 3.53.4. No application code, topology, query semantics,
timeouts, SQLite settings, indexes, cache, model or policy was changed.

Both launches retained selector generation 8 / NATIVE_ACTIVE, core
f21c730f-5222-4aa8-9a5f-1c1188456df3 / ACTIVE_CORE and NATIVE_AGREEMENT.
Health was HTTP 200 / NATIVE / non-degraded BAAI/bge-small-en-v1.5, CPU, 384 dimensions.
The launch profile digest remained
35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a.
No legacy public fallback or unexpected generative provider was observed.

## Workload and correctness

Existing admitted scale workspaces were selected before new data was added.
Population estimates came from scoped EID aliases, confirmed against native
enumeration counts for the three selected corpora. Each used scale-observer,
native_memory_scale_qualification and its admitted private semantic scope.
These read-only qualification scopes had no Character seed.

| Existing workspace | Approximate native memories | Ordinary query seconds |
| --- | ---: | ---: |
| scale-20260826t030102z-ac179d64 | 28 | 27.031–28.453 |
| scale-20260826t031118z-9c9e7541 | 114 | 27.625–28.828 |
| scale-20260826t033652z-a6a9760b | 505 | 27.625–28.484 |

Two existing anchors were queried in each corpus, smallest to largest. The
505-memory lamp query was repeated later in the warm process after growth.
Every selected anchor returned with the expected EID, content fingerprint and
private scope through the ordinary native vector query path. This is a small
representative retrieval sample, not an exhaustive recall measurement.

The write scope was lifecycle-e9f54df99882 / lifecycle-agent-e9f54df99882 /
lifecycle_qualification, private. The first batch added compass, recipe and
bicycle notes; representative reads followed before a second batch added
concert, pottery and orchard notes. No shared lane was populated.

| Private EID | Native object | Final current revision | Reinforcements |
| --- | --- | --- | ---: |
| 10 | e5fd29f4-b8a7-4a0e-9a56-1a2a7a2cfa18 | e3fbca38-0d11-482b-a9d8-cb1a2ab9550b | 1 |
| 11 | c06550e4-23f7-4d38-af0d-d5a144c959a3 | 98120ba1-4735-49e9-801b-e6abb614bb0a | 0 |
| 12 | f730d2e0-08fb-422c-a7d0-77e45df00875 | 502acc89-5eb3-452e-b4de-393117a6daf8 | 0 |
| 13 | c1ebd443-6894-4d99-afc1-8fb90aea14e4 | 3ba3c21e-1cbe-4fea-81e1-4fda22710ac0 | 0 |
| 14 | 9ef92dfc-1b16-4b23-8494-d64c137d405e | 5602441a-ed40-4169-9a20-f1f4166a7850 | 0 |
| 15 | 1d58587c-feb4-4e7c-ad60-7791eefcdcac | 8a9349b1-5d6c-4bd2-b159-0e7a9fb328d5 | 0 |

All six creates returned distinct EIDs and native objects. The nine preexisting
objects retained their current revisions and recorded memory metadata across
the observations. New content fingerprints matched the normal ingest receipts.
After restart, representative compass, orchard and existing lens reads passed.
One normal reminder then reinforced the compass under the same EID with one
new revision and count 1, without creating another memory. The final normal
query and selected metadata agreed on its reinforcement timestamp and state.

Totals: **22 ordinary reads, 7
ordinary writes (6 creates + 1
reinforcement), and 4 health calls**. Health is excluded from
the read count. Every HTTP operation completed successfully and was submitted
once. Mutations used fresh idempotency keys; no supplied summaries, embeddings,
direct SQL writes or standalone trajectory effects were used.

All returned private results matched the requested workspace and agent.
Post-restart control queries in audit_smoke_v0_2 / smoke_runner / personal and
the existing research contrarian scope returned none of the six new private
content fingerprints. This is bounded scope-isolation evidence. Existing P3
refusals were not recertified, and nonempty shared ranking remains
DEFERRED_EXISTING_CORPUS_EMPTY.

## Character, trajectory and restart

Three ordinary Character-bearing queries, early, after growth and after restart,
returned the same context fingerprint:
5c6fecada71ea04315f4ccb0a099a13362d0dc867e3ab595b418b9a6ddb17970.
The scope was hivemind-natural-n5-v2-n5-20260825T201516Z-19a8097e25 /
contrarian / research. Existing Character identity, seed and state file
fingerprints stayed unchanged; no Character mutation was performed.

Native trajectory authority progressed from generation 8 to 9 in PID 24056
and remained in that same session throughout both growth batches. The normal
post-restart reinforcement in PID 66272 acquired generation 10. Legacy
fence generation 2 remained intact, with no legacy session, under HANDOFF_COMPLETE.
All new native write intents settled. The two newly sealed chunks contain seven
ordinary frames at steps 1000401–1000407, with populations 10, 11, 12, 13, 14,
15 and 15. Chunk hashes, preceding-hash continuity and decoded record populations
were checked once at closure; the previous manifest entries remained intact.

Both normal shutdowns exited 0, completed application shutdown, and left no
service process or port-8787 listener. Restart used the same qualified
environment and retained the 15-memory corpus and native authority.

## Latency and resource observations

Five-second Windows process/host counters covered 20.9
minutes in the first warm process and 5.8 minutes
after restart. Useful ordinary operations defined the duration. Counters used
built-in Windows APIs, with no application profiling or diagnostic timing.

| Request class | Minimum seconds | Maximum seconds | Median seconds |
| --- | ---: | ---: | ---: |
| Ordinary reads | 26.922 | 29.047 | 27.625 |
| Creates / reinforcement | 119.391 | 124.657 | 122.360 |
| Health | 0.000 | 0.031 | 0.024 |

The 0.000-second health observation is below the recorded timer resolution;
it does not mean a request took literally zero time.

LATENCY_BEHAVIOR = **STABLE**. The 28-, 114- and 505-memory read ranges overlap. The same 505-memory lamp query took 27.625 seconds initially and 27.640 seconds after growth in the warm process. Creates took 122.062-124.657 seconds and the post-restart reinforcement took 119.391 seconds. No timeout or progressive latency explosion appeared; no performance threshold was imposed.

| Process resource sample | Run 1 | Run 2 |
| --- | ---: | ---: |
| Resident RAM first → last, MiB | 85.8 → 577.7 | 102.0 → 572.9 |
| Highest observed resident RAM, MiB | 578.0 | 572.9 |
| Peak private committed memory, MiB | 2126.9 | 2122.9 |
| Observed CPU seconds | 1361.5 | 398.2 |
| Peak sampled CPU, one-core basis | 290.9% | 205.0% |
| Peak sampled core WAL, bytes | 86552 | 0 |

RAM_BEHAVIOR = **STABLE**. The first samples (85.8 and 102.0 MiB) precede model loading; the first health points were about 555.2 and 552.8 MiB. After the initial scale reads, run 1 stayed near 574-578 MiB through both growth batches and later reads, finishing at 577.7 MiB. Run 2 finished at 572.9 MiB. Run 1's final minute spanned only 577.6-578.0 MiB. These small warm-workload changes support stability within the sample, without claiming long-duration leak freedom.

CPU was active during requests and returned to 0% in sampled gaps in both processes. Samples outside request windows had medians of 0% and about 0.16% respectively; those windows also include startup and are not a dedicated idle benchmark. The host has 32 logical CPUs;
100% in the process CPU figures means one core, not the entire host.

Core database size: 83,005,440 bytes before, 83,181,568
after the first batch, 83,333,120 after both batches and
shutdown, and 83,357,696 finally. Total growth: 352,256
bytes. The observed core WAL peak was 86,552 bytes during run 1. Core and authority WAL files were zero length at the bounded metadata checkpoints and after both shutdowns. No persistent WAL accumulation or lock failure was observed. Five-second sampling can miss brief WAL peaks.
No BUSY/LOCKED failure, SQLite integrity error, accumulating service exception,
authority failure or stop-condition anomaly was observed. No continuous
integrity scans, core hashing or full-root recensus was performed.

## Evidence and review boundary

External evidence: C:/TORMENT/TORMENT_administration/post-p7-stage-3-20260910.
Compact receipts, selected-scope metadata, service logs, process counters,
shutdown records and summary.json support this record. Evidence manifest SHA-256:
bd5e4126ec5bb3a690afeb9e71540116394b7f9a5ed384c5fa932deb09742dfb.
Only this document changed in the repository; git diff --check was the
documentation check, and the live ordinary workload supplied behavioral validation.

~~~text
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = NONE; local offline BAAI/bge-small-en-v1.5 embeddings only
CHARACTER_CONTINUITY_DURING_SCALE = PASS
TRAJECTORY_AUTHORITY_DURING_SCALE = PASS
SCOPE_ISOLATION = PASS
SCALE_RESTART = PASS
MEMORY_GROWTH_PERSISTENCE = PASS
SQLITE_BUSY_OR_LOCK_FAILURE = NO
SQLITE_INTEGRITY_ERROR = NO
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_3 = PASS
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_3_REVIEW
~~~

This sample does not establish unbounded scale, long-duration leak freedom,
failure-injection recovery or nonempty shared ranking. No optimization or
failure/recovery stage was started. Stop here for review.
