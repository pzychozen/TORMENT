# TORMENT DeepMemory Patch B Characterization Closure

**Date:** 2026-08-12  
**Status:** CLOSED — no production change  
**Patch A reference:** `0810f3fdda94f87b542f038e08224a8b4c716fc8`

## Final characterization

`MemoryGraph` holds the authoritative source summary. `DeepMemory.summary` is
a non-authoritative, bounded lossy retrieval echo.

The first Deep text truncation is in `CompressionScorer.score`:

```python
summary[:200]
```

Normal Deep cognition checks that the source EID is present, but surfaces
`dm.summary`; it does not fetch and rejoin source-row text. Although
`DeepRetrievalHit.rehydrate()` exists, it is deliberately non-load-bearing and
does not itself authorize runtime wiring.

Therefore:

> DeepMemory persists a bounded lossy echo while MemoryGraph retains the source summary. Normal Deep resurfacing verifies source-EID presence but does not rejoin source text. No evidence currently establishes that this behavior is incorrect.

## Disposition

- Patch B is closed without production code or test changes.
- B-1 (`summary_truncated` / `source_summary_chars`) is rejected: it is
  instrumentation and schema/API growth, not a correctness repair.
- Removing or increasing the 200-character bound is rejected because it would
  change prompt-visible and token-budget behavior.
- Duplicating a full `source_summary` in `DeepMemory` is rejected because
  DeepMemory is explicitly source-dependent and non-authoritative.
- Runtime source-text rehydration remains unapproved: the current canonical
  source state may differ from the state associated with an earlier Deep
  export, requiring separate source-sameness/revision evidence.

## Compaction correction

`compact_core_memory` must not be fixed independently.

| Condition | Current result |
| --- | --- |
| Current | Expiry is inert because `half_life_days` is absent. |
| Only half-life key corrected | Dangerous: step-valued `created_at` appears ancient. |
| Only `created_at` semantics corrected | Still inert because `half_life_days` is absent. |
| Both corrected | Expiry operates on genuine age. |
