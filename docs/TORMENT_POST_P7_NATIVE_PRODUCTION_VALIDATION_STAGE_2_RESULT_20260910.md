# TORMENT — Stage 2 native production operation

2026-09-10 UTC. **POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_2 = PASS.**

Normal native service operation accepted small memory growth, continued serving
scoped retrievals in a warm process, retained Character state, and resumed
correctly after a clean restart. This is a bounded behavioral sample, not a
scale or endurance certification. P1–P7 and Stage 1 remain closed.

## Run and workload

Starting HEAD = origin/main =
9e330067f03044f29892d85dc6bc1a522f1d73ff; tracked worktree clean.
The existing untracked artifacts were preserved. This document is the only
repository change; its evidence-only publication commit and actual remote
HEAD are recorded in the final return and external publication.json.

Both runs used Windows CMD, conda activate torment, python -m torment_service,
the existing root-v2 seven-field deployment profile, and HF_HUB_OFFLINE=1.
Diagnostic query timing was disabled throughout. No profiling package was
installed, and no application, SQLite, model, policy or resource setting was
tuned. SQLite runtime was 3.53.4.

Health remained HTTP 200 / NATIVE / non-degraded local st embedding.
Selector 8 / NATIVE_ACTIVE and core
f21c730f-5222-4aa8-9a5f-1c1188456df3 retained NATIVE_AGREEMENT.
No legacy public fallback or maintenance-only posture was observed.

The mutation scope was the existing safe
lifecycle-e9f54df99882 / lifecycle-agent-e9f54df99882 /
lifecycle_qualification private corpus. The existing Character-bearing
hivemind-natural-n5-v2-n5-20260825T201516Z-19a8097e25 / contrarian / research
scope was read only.

- First process, PID 44724: existing-memory and Character reads; two
  distinct notes about a stored lens and a reading-group arrangement; later
  paraphrased retrievals; one ordinary reinforcement of the lens note; another
  Character observation and retrieval. Three bounded health checks.
- After normal shutdown, PID 13736: normal startup and health; retrieval
  of both first-run notes and the reinforced state; Character observation;
  one further ordinary note about a plant-watering routine, its retrieval,
  and a control-workspace isolation query; normal shutdown.
- Totals: **12 ordinary reads, 3
  new private memories, 1 reinforcement**.
  Health calls are excluded from the read count.
- Five-second process counters cover approximately 10.5
  minutes in run 1 and 5.3 minutes in run 2. Useful completed
  operations, rather than idle duration, define this sample.

All requests used the normal REST service. No supplied embeddings, synthetic
trajectory entities, standalone trajectory helper, populated shared test lane,
or generative provider was used. Each mutation had a fresh idempotency key and
was submitted once.

## Observed behavior

The selected corpus grew from 6 to 8 memories in the first process and to 9
during normal continuation after restart. The new objects are distinct:

| Private EID | Native object | Final current revision | Reinforcement count |
| --- | --- | --- | ---: |
| 7 | 1c2b1c9c-3d78-474d-a056-721a43fed402 | c67b09f7-86f0-47fe-9c9f-9d93977a3b47 | 1 |
| 8 | 0b904e00-cda1-48be-aebe-087abd3ef16a | e2899c43-6367-47e4-89fb-c623d26f577c | 0 |
| 9 | fd4e6530-6a33-4638-a68f-e75dae9cd440 | 17e1c42c-9e29-4d9d-989a-ff17255f6e26 | 0 |

The first-run notes retained the same native objects, current revisions and
reinforcement metadata after restart. The lens query exposed count 1 and the
same reinforcement timestamp before and after restart. Reinforcement returned
the existing EID and did not create a duplicate. Paraphrased vector queries
retrieved the intended notes in the correct private scope.

Three separated ordinary reads returned the same existing Character continuity
state. Its context SHA-256 was
5c6fecada71ea04315f4ccb0a099a13362d0dc867e3ab595b418b9a6ddb17970.
Existing Character identity/seed/state file fingerprints also stayed unchanged.
Query ranking and floating scores were allowed to vary.

Normal creates exercised native motif creation and ordinary queries exercised
motif summaries. Normal ingestion and reinforcement produced all trajectory
activity. The first warm session retained writer generation 7 across its three
mutations; the post-restart ordinary create acquired generation 8. The legacy
fence remained generation 2 with no legacy session, under HANDOFF_COMPLETE.
Two newly sealed chunks contain the four normal frames at steps 1000301–1000304,
with populations 7, 8, 8 and 9. Their hashes, decoded populations and settled
native intents were observed once at closure. No extra trajectory write was
manufactured.

The post-restart audit_smoke_v0_2 / smoke_runner / personal query did not return
any of the three new private notes. Returned results stayed in their requested
scopes. No abnormal result suggested certified-refused authority; no P3
recensus was performed. Shared memory was not populated:
NONEMPTY_SHARED_RANKING = NOT_YET_VALIDATED.

## Latency, resources and SQLite

These are Stage-2 normal-service samples with diagnostic timing off.
Stage-1 diagnostic times were not used as a performance baseline.

| Request class | Minimum seconds | Maximum seconds | Median seconds |
| --- | ---: | ---: | ---: |
| Ordinary reads | 26.375 | 27.734 | 26.609 |
| Creates / reinforcement | 117.390 | 118.578 | 118.141 |
| Health | 0.015 | 0.047 | 0.023 |

Latency classification: **stable within this bounded workload**. Later requests
remained correct and responsive, without recurring timeout or accumulating
errors. No performance target was imposed.

| Process sample | Run 1 | Run 2 |
| --- | ---: | ---: |
| Resident RAM range, MiB | 552.3–575.3 | 102.2–574.5 |
| Resident RAM first → last, MiB | 552.3 → 575.2 | 102.2 → 574.4 |
| Peak private committed memory, MiB | 2124.9 | 2123.7 |
| CPU seconds during observed window | 625.1 | 327.5 |
| Peak sampled process CPU, one-core basis | 205.3% | 203.4% |
| Peak sampled core WAL, bytes | 399672 | 0 |

The host has 32 logical CPUs; 100% in the process CPU
row means one core, not the whole host. Run 2 sampling began during startup,
so its low initial resident value precedes normal model loading; warm resident
memory settled near 574–575 MiB in both runs. Resource behavior was sane for this
sample: bounded memory use, CPU activity during work, and no observed runaway.
Counters use built-in Windows APIs. An unavailable optional psutil import in
the external observer was replaced before sampling; no dependency was installed.

Core size was 82,825,216 bytes initially, 82,960,384
after run 1, and 83,005,440 finally: growth 180,224
bytes. Final core WAL was zero length. Five-second sampling can miss brief WAL
peaks; zero sampled/final size is not a claim that WAL was never used.
No BUSY/LOCKED failure, SQLite integrity error, or authority recovery problem
appeared in ordinary results or service logs.

Both shutdowns completed and exited 0 with no surviving service process or
listener on port 8787. Restart used the same qualified environment, and normal
query behavior resumed. No service anomaly required expansion to stop or a
code repair.

## Evidence and review boundary

External evidence:
C:/TORMENT/TORMENT_administration/post-p7-stage-2-20260910.
It contains compact redacted request receipts, the three selected-scope
metadata observations, ordinary service logs, host counters, shutdown records,
and summary.json. No full private memory content is dumped in this record.
There was no whole-root recensus, continuous table hashing, or P-phase validator
campaign.

Evidence manifest SHA-256:
18a4b75f1c4dab4d85fa847adb74b01aada94ac3a37d819f7a6b9c9d72d40f2c.
The repository change is documentation only, checked with git diff --check;
the live ordinary workload is the behavioral validation.

~~~text
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = NONE; local offline BAAI/bge-small-en-v1.5 embeddings only
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_2 = PASS
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_2_REVIEW
~~~

This sample does not establish large-population scale, long-duration resource
stability, failure-injection recovery, or nonempty shared ranking. Return for
review before any further validation stage.
