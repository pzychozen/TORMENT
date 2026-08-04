# TORMENT A0 Lived-Use Scientific Checkpoint — 2026-08-04

## 1. Purpose

A0 tested whether compact semantic memory improves ordinary, cross-session AI interaction without transcript replay.

The wider scientific question is whether TORMENT makes an AI relationship more continuous, useful, and human without becoming intrusive, rigid, repetitive, or confidently wrong. Eira Voss is the test vehicle, not the objective itself.

## 2. Minimal A0 Configuration

A0 deliberately kept higher systems paused:

- compression off
- archive recall off
- SRG off
- Hive off
- Spirit Return off
- optional shaping systems off

Vision remains paused until ordinary memory use is comfortable, stable, useful, correctable, restrained, and understandable.

## 3. Evidence Corpus

Preserved capture files:

- `20260803T212137Z-1425a4456c.jsonl`
- `20260804T042037Z-82f0573342.jsonl`
- `20260804T054425Z-89c4c6b7dd.jsonl`

Current audit and capture interpretation:

- 80 conversational turns
- 7 newly stored memories
- 73 handled ingest attempts without durable writes
- latest stored memory: `eid 27`, `step 25`

These figures describe the current source-audited interpretation, not the initial live assumption.

## 4. Corrections Already Proven

`PROVIDER_BOUNDARY_SAFETY_PROVEN`: provider responses produced valid visible replies and were not confused with hidden thinking blocks.

`RELATIONAL_GUIDANCE_CORRECTION_PROVEN`: the false "No relational memories yet" recommendation is suppressed when live relational-tier hits exist, while the persisted drift-state `relational_count` remains unchanged.

## 5. Three-Session Chronology

The three captures preserve an ordinary cross-session lived-use attempt. Early turns created a small durable memory set. Later turns continued the local conversation and produced transformer/Spine handled ingest responses, but most did not execute durable memory writes.

The recent-memory index reported `step 25` after restart because `eid 27` was genuinely the newest durable memory. Later local steps represented interaction attempts, not durable memory growth.

## 6. Initial Interpretation

Client-local step advancement and transformer HTTP success were initially treated as evidence of durable memory growth.

That interpretation collapsed separate layers: provider/LLM response, transformer/Spine response, memory outcome, and A0 client-local bookkeeping.

## 7. Source-Audited Correction

The corrected interpretation is that the transformer/Spine can handle an explicit ingest request without a durable memory action. HTTP success at that boundary is not proof from the memory system.

The provider produced valid visible assistant replies. Stored memories persisted. The recent-memory index was correct. Later roleplay or personal-arc retrieval failures are not ranking results because the expected content was not stored.

## 8. Supported Findings

`CROSS_SESSION_MEMORY_PERSISTENCE_PROVEN_FOR_STORED_SET`: stored memories survived across sessions for the stored set.

`CLIENT_HISTORY_INDEPENDENCE_PROVEN_FOR_STORED_SET`: recall of stored material did not depend on replaying the full local transcript.

`SERVICE_RESTART_PERSISTENCE_PROVEN_FOR_STORED_SET`: the stored set remained available after service restart.

## 9. Narrowed Findings

`COMPACT_SEMANTIC_RECALL_MECHANISM_SUPPORTED`: compact semantic recall is supported for the small stored corpus.

This does not establish large-corpus recall quality, roleplay arc continuity at scale, or retrieval behavior for content that was never written.

## 10. Unsupported Findings

`RECALL_AT_SCALE_NOT_TESTED`.

Later roleplay or personal-arc retrieval failures are not ranking results because the content was not stored.

The frozen A0 basin must not be used to claim that 80 memories were stored, that retrieval failed on a large later corpus, or that explicit-write routing is already corrected.

## 11. Frozen-Basin Status

The A0 basin is frozen scientific evidence:

- do not continue chatting in it
- do not delete or mutate it
- do not use it as an A1 control
- do not tune retrieval using it

## 12. Observability Correction

Commit: `9f124648db493b3e43c48a72fd96eaf930fd17c4`.

Effect: the A0 client can now capture transformer path, escalation and result metadata alongside `stored`, `reinforced`, `eid` and `reason` fields.

Non-effect: routing and write behavior were not changed.

## 13. Unresolved Explicit-Write Semantics

Still unresolved:

- whether explicit ingest may escalate
- whether escalation should still permit a write
- whether escalation should visibly refuse
- whether behavior should depend on operation type

No final explicit-write policy is selected by this checkpoint.

## 14. Requirements for A0b

A0b requires:

- live scratch reproduction using the new observability
- explicit-write semantic decision with Hilmir
- bounded behavioral implementation
- focused Windows tests
- new clean basin
- honest classification of every accepted turn
- restart and cross-session persistence verification

## 15. Relation to the Wider Lived-Use Mission

The purpose is not merely to accumulate memory records.

The purpose is to determine whether remembering makes an AI relationship more continuous, useful and human without becoming intrusive, rigid or confidently wrong.
