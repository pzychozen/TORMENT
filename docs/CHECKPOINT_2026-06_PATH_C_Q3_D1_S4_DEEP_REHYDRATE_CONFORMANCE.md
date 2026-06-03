# Checkpoint — Cluster 5 §9.3 Path C → Q3-D1-S4 (deep-rehydrate affect-attribution conformance)

**Type:** Tracked closure checkpoint. Documentation only — records a landed
conformance slice in two authorized halves. No production-code, schema, scoring,
or test change is authorized by this file, and it does **not** open D1-S5.
**Closure recorded:** 2026-06-03.
**Anchors:** `docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md`
(ratified contract — §11 staged plan, §12 falsifier: "Deep echo → Q1 markers;
preserves source attribution snapshot; NOT relabeled recovered; authority use
requires rejoin"), `docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`
(Q1 deep-hit markers), and the prior D1 checkpoints (S2 / H1 / S3).

---

## 1. Closure identity

```
Gate:
Cluster 5 Path C -> Q3 affect attribution -> Q3-D1 -> D1-S4

Closed commit:
b602fc7 feat(affect-attribution): preserve deep-echo source snapshot
```

**Q3-D1-S4 (deep-rehydrate conformance) is CLOSED.** It is the third
affect-attribution producer-conformance slice, after D1-S2 (ordinary ingest),
H1 (caller-envelope hardening), and D1-S3 (mood_drift). No subsequent slice is
authorized by this checkpoint.

---

## 2. Two-layer implementation

D1-S4 landed in two authorized halves. The first was implemented and held
uncommitted as provisional; a second read-only audit established that a runtime
boundary remained, and the second half was separately authorized before
implementation. Both halves shipped together in `b602fc7`.

**D1-S4a — durable deep-record snapshot preservation**

```
DeepMemoryStore.export(...)   (torment_service/deep_memory.py)
- adds "affect_attribution" to the existing metadata whitelist
- copies the source row envelope verbatim into DeepMemory.metadata
- does NOT synthesize, mutate, validate-rewrite, or overwrite the snapshot
- copies only when present; genuinely unstamped legacy rows remain without one
```

**D1-S4b — internal runtime retrieval-echo snapshot surfacing**

```
TormentFabric._query_deep_lane(...)   (torment_service/fabric.py)
- at the lane-assembler layer beside the existing authority_status injection
- surfaces affect_tag
- surfaces the preserved affect_attribution
- copies both only when a preserved snapshot exists in _dm.metadata
- leaves affect_conf UNSURFACED in this slice
```

---

## 3. Semantic distinction (three orthogonal axes)

```
ProvenanceV1       = row lineage          — WHERE the source row came from
affect_attribution = affect-value lineage — HOW the source affect value was produced
authority_status   = echo authority       — WHAT the runtime echo is permitted to do
```

The runtime retrieval echo truthfully carries both the preserved affect-value
lineage:

```
affect_tag
affect_attribution
```

and, separately, its echo authority posture:

```
authority_status = {
    authoritative: false,
    requires_rehydration: true,
    role: "retrieval_echo",
}
```

These coexist without rewriting history. The snapshot describes how the source's
affect value was produced; `authority_status` constrains what the echo may do.

```
preserved lineage != granted authority
deep echo         != recovered
retrieval echo    != original producer
```

---

## 4. Why affect_tag is copied beside the snapshot

The read shim validates a present `set` envelope against the row's stored tag:

```
read_affect_attribution(payload)
-> validates a present set-envelope against payload["affect_tag"]

set envelope + missing affect_tag
-> fail loud
```

A preserved producer envelope has `value_state=set`. Surfacing
`affect_attribution` alone onto the runtime echo would therefore make
`read_affect_attribution` raise. Runtime conformance requires copying:

```
affect_tag + affect_attribution
```

not the envelope alone. `affect_conf` is **not** required for validation or the
snapshot-preservation claim and is deliberately left unsurfaced in this slice.

---

## 5. Scope correction caught during implementation

The audit initially found that the deep-export metadata whitelist dropped
`affect_attribution`. The provisional S4a fix preserved it in the durable
record — but implementing it exposed a second boundary:

```
stored in DeepMemory.metadata
!=
surfaced on the runtime _query_deep_lane() echo
```

A second read-only audit established that the Q1 authority markers and the
preserved source snapshot belong on the **same runtime echo object** (the §12
falsifier binds "preserves source attribution snapshot" to the echo carrying the
Q1 markers). The runtime hit builder (`spirit_return.inject_spirit_return_into_hit`)
emits no affect fields, so the snapshot was not reaching the live echo. D1-S4b
was separately authorized and implemented to close that runtime layer. This is
the difference between "stored somewhere" and "carried by the live echo."

---

## 6. Verification evidence (Windows, source of truth)

```
Focused suite:
96 passed in 2.53s

Full Windows suite:
3670 passed, 5 skipped, 22 subtests passed in 79.81s

Commit / push:
415b8b9..b602fc7  main -> main

git status --short --branch:
## main...origin/main
```

(Verification note: per standing project practice, the Windows workspace is the
authoritative verification surface. AI-side mounted filesystem views may contain
EOL noise or stale/truncated file representations and were not used as evidence.)

---

## 7. Exact landed footprint

Production (two files):

```
torment_service/deep_memory.py   (S4a — metadata whitelist)
torment_service/fabric.py        (S4b — _query_deep_lane surfacing)
```

Tests (one file):

```
tests/test_affect_attribution_deep_rehydrate.py
  - record-level (S4a): export preserves ingest + mood_drift snapshots; JSONL
    recall round-trip; read returns producer not fallback; snapshot/authority
    orthogonality; rehydrate returns source unchanged (+ orphan raises); legacy
    source keeps fallback; scoring-relevant metadata unchanged.
  - live-echo (S4b): _query_deep_lane hit exposes affect_tag + exact snapshot;
    read returns producer envelope without raising; Q1 markers preserved
    orthogonally; affect_conf not surfaced; legacy echo keeps fallback with
    role=retrieval_echo; orphan source still filtered.
```

No other production file or test was modified.

---

## 8. Held-closed boundaries

D1-S4 did **not** edit or open:

```
fallback vocabulary redesign
affect_conf runtime surfacing
external/API cross-surface presentation
spirit_return.py general field expansion
DeepRetrievalHit.to_dict() expansion
deep_hits.py authority semantics
rehydrate() behavior
backfill for pre-existing deep-memory records
generic user_confirmed semantics
confirmation writers
affect_state.json authority posture
ProvenanceV1 redesign
scoring
reinforcement
promotion
duplicate handling
archive authority
migration
autonomy expansion
```

---

## 9. Parked legacy behavior

```
stamped source
-> snapshot preserved durably (S4a) and surfaced internally (S4b)
-> echo read returns original producer lineage (inferred / derived)

genuinely unstamped legacy source
-> no source snapshot exists
-> legacy fallback characterization remains unchanged
-> vocabulary mismatch remains parked
```

The `recovered / migration / legacy_read_fallback` characterization is **not**
redesigned by this checkpoint. It remains the parked deferred-vocabulary
question (D1-S2 §7-A / characterization tests).

---

## 10. Ordered continuation

```
D1-S2 ordinary-ingest stamping          -> CLOSED (8b2c1f3)
D1-H1 caller-envelope strip              -> CLOSED (7066b57)
D1-S3 mood_drift stamping                -> CLOSED (dcead02)
D1-S4 deep-rehydrate conformance         -> CLOSED (b602fc7)
D1-S5 cross-surface conformance
      + generic user_confirmed isolation -> next candidate gate, AUDIT-FIRST ONLY
```

This checkpoint is documentation only. It records D1-S4 closure. It does **not**
open or authorize D1-S5. D1-S5 opens, if at all, only through the standard
audit → draft → trio review → ratification cycle.

---

*End of Q3-D1-S4 closure checkpoint. Documentation only. D1-S5 remains unopened.*
