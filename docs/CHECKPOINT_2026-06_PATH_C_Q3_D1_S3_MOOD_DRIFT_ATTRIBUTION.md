# Checkpoint — Cluster 5 §9.3 Path C → Q3-D1-S3 (mood_drift affect attribution)

**Type:** Tracked closure checkpoint. Documentation only — records a landed
producer slice. No production-code, schema, scoring, or test change is authorized
by this file, and it does **not** open D1-S4.
**Closure recorded:** 2026-06-03.
**Anchors:** `docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md`
(ratified contract — §4 producer-default table + §7 mood_drift attribution),
`docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S2_ORDINARY_INGEST_ATTRIBUTION.md`
(prior producer + the T10 boundary this slice consciously inverts),
`docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_H1_CALLER_ENVELOPE_STRIP.md`.

---

## 1. Closure identity

```
Gate:
Cluster 5 Path C -> Q3 affect attribution -> Q3-D1 -> D1-S3

Closed commit:
dcead02 feat(affect-attribution): stamp mood-drift rows as derived
```

**Q3-D1-S3 (mood_drift stamping) is CLOSED.** It is the second affect-attribution
producer, built on the D1-S1 validator/contract and following the D1-S2
ordinary-ingest producer and the H1 caller-envelope hardening. No subsequent
slice is authorized by this checkpoint.

---

## 2. What landed

Production boundary (exactly two files):

```
torment_service/affect_attribution.py
- added the pure, validated constructor
    build_mood_drift_attribution(*, affect_tag)
  returning the ratified mood_drift envelope; self-validates through
  validate_affect_attribution (defense in depth). Always value_state=set.

torment_service/fabric.py
- extended the affect_attribution import to also pull build_mood_drift_attribution.
- added exactly one internally constructed affect_attribution key inside the
  existing extra_payload passed to g.add_memory(...) in the singular mood_drift
  producer _maybe_emit_mood_drift().
```

Tests (exactly one file):

```
tests/test_affect_attribution_ingest.py
- inverted the D1-S2 boundary test (was: mood_drift rows are NOT stamped) into
  TestMoodDriftStampedS3 (mood_drift rows ARE stamped, full-envelope assertions
  + read-shim-returns-persisted + row-lineage/scoring inputs intact).
- added TestMoodDriftConstructorUnit (pure constructor + validation).
- added TestMoodDriftDisabledNoRow / TestMoodDriftFailedNoRow (not-evaluated
  states still emit no mood_drift row, hence no stamp).
```

No other production file or test was modified.

---

## 3. Producer + persistence seam

```
1. Single producer:
   TormentFabric._maybe_emit_mood_drift()  (torment_service/fabric.py)

2. Single internal persistence seam:
   the existing g.add_memory(...) extra_payload in that producer
```

The `extra_payload` is fully internally constructed — there is **no
caller-supplied surface** on this `add_memory` path, so the H1 caller-envelope
strip is not needed here and is untouched (H1 hardens the separate
`TormentFabric.ingest()` caller-merge seam).

---

## 4. Ratified attribution posture

`build_mood_drift_attribution(*, affect_tag)` emits exactly:

```
schema_version="1.0"
value_state="set"
origin_kind="derived"
actor="system"
actor_reference=None
subject="unknown"
confirmation="unconfirmed"
confirmation_actor=None
confirmation_actor_reference=None
via="mood_drift_transition"
```

This is the posture ratified in the contract §4 producer-default table and §7.
`value_state` is **always `set`** because the producer emits no row at all when
affect is absent, neutral, below the confidence threshold, unchanged, or inside
the minimum-gap window — so there is no `unset` or not-evaluated mood_drift row.
`affect_tag` is therefore guaranteed non-None at the seam, and the validator
enforces `value_state=set ⇒ stored affect_tag`.

---

## 5. Semantic distinction (why a dedicated constructor, not reuse)

```
ProvenanceV1       = row lineage          — WHERE the row came from
affect_attribution = affect-value lineage — HOW the affect value was produced
```

A mood_drift row is **not** merely a copied endpoint tag. It is an affect-bearing
**derived** signal:

```
prior affect state + current classifier result + a qualified transition event
```

Although the stored `affect_tag` originates from the same `classify_affect`
call as ordinary ingest, the claim a mood_drift row persists is "a meaningful
mood drift occurred from one state to another." For that claim the ratified
posture `origin_kind=derived / via=mood_drift_transition` is truthful, and is
deliberately distinct from the ordinary-ingest producer
(`inferred / ingest_affect_classifier`).

```
ordinary-ingest classifier output  !=  qualified mood-drift transition signal
```

Reusing `build_ingest_classifier_attribution` was considered and rejected: it
would silently contradict the ratified contract on **two** fields (`origin_kind`
and `via`), not one. (Trio note: this semantic fork was raised, returned to the
ratified contract, and confirmed by second-pass review before implementation.)
Row lineage — the transition itself — stays in `mtype="mood_drift"` /
`mood_from` / `mood_to` / `ProvenanceV1`; this field records affect-value lineage
only.

---

## 6. Conscious scope-boundary flip (T10)

D1-S2 locked mood_drift rows as **unstamped** via `test_T10`
(`docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S2_ORDINARY_INGEST_ATTRIBUTION.md` §8).
D1-S3 is the separately authorized slice that **intentionally inverts** that
boundary: mood_drift rows now carry the derived attribution envelope. The flip
is explicit and reviewed, not a silent regression — the old assertion was
replaced by `TestMoodDriftStampedS3`.

---

## 7. Not-evaluated behavior unchanged

```
disabled or failed classifier
-> no affect_tag
-> _maybe_emit_mood_drift returns before writing
-> no mood_drift row emitted
-> no attribution stamp emitted
```

D1-S3 therefore does **not** re-touch the not-evaluated ambiguity. The parked
fallback-vocabulary mismatch (D1-S2 §7-A / characterization T12b) remains
untouched. Locked by `TestMoodDriftDisabledNoRow` and `TestMoodDriftFailedNoRow`.

---

## 8. Held-closed adjacent lanes

D1-S3 did **not** modify any of:

```
mood_from
mood_to
affect_tag
affect_conf
drift_hist
threshold logic
minimum-gap logic
neutral filtering
scoring
reinforcement
promotion
```

(Scoring continues to apply `mood_drift_bonus` on `type=="mood_drift"` rows; the
stamp only adds a sibling payload key and leaves the row's `type` and affect
fields intact, asserted by `TestMoodDriftStampedS3`.)

---

## 9. Verification evidence (Windows, source of truth)

```
Focused suite:
64 passed in 2.76s

Full Windows suite:
3655 passed, 5 skipped, 22 subtests passed in 89.28s

Commit / push:
1887216..dcead02  main -> main

git status --short --branch:
## main...origin/main
```

(Verification note: per standing project practice, the Windows workspace is the
authoritative verification surface. AI-side mounted filesystem views may contain
EOL noise or stale/truncated file representations and were not used as evidence.)

---

## 10. Still parked (NOT solved here)

```
not-evaluated fallback vocabulary mismatch
D1-S4 deep-rehydrate conformance
D1-S5 cross-surface conformance + generic user_confirmed isolation
direct MemoryGraph producer policy beyond the singular mood_drift seam
affect_state.json authority posture
confirmation writers
ProvenanceV1 changes
scoring
reinforcement
promotion
duplicate handling
archive authority
migration
backfill
```

---

## 11. Ordered continuation

```
D1-S2 ordinary-ingest stamping   -> CLOSED (8b2c1f3)
D1-H1 caller-envelope strip       -> CLOSED (7066b57)
D1-S3 mood_drift stamping         -> CLOSED (dcead02)
D1-S4 deep-rehydrate conformance  -> next candidate gate, AUDIT-FIRST ONLY
D1-S5 cross-surface conformance + generic user_confirmed isolation
```

This checkpoint is documentation only. It records D1-S3 closure. It does **not**
open or authorize D1-S4. D1-S4 opens, if at all, only through the standard
audit → draft → trio review → ratification cycle.

---

*End of Q3-D1-S3 closure checkpoint. Documentation only. D1-S4 remains unopened.*
