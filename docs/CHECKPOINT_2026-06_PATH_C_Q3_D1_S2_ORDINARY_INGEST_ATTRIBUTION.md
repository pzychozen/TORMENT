# Checkpoint — Cluster 5 §9.3 Path C → Q3-D1-S2 (ordinary-ingest affect attribution)

**Type:** Tracked closure checkpoint. Documentation only — records a landed slice.
No production-code, schema, scoring, or test change is authorized by this file,
and it does **not** open D1-S3.
**Closure recorded:** 2026-06-02.
**Anchors:** `docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md`
(ratified contract), `scratch/CLUSTER_5_PATH_C_Q3_D1_S2_PREIMPL_AUDIT_2026-06-01.md`
(pre-implementation audit, rev 2).

---

## 1. Closure identity

```
Gate:
Cluster 5 Path C -> Q3 affect attribution -> Q3-D1 -> D1-S2

Closed commit:
8b2c1f3 feat(affect-attribution): stamp ordinary-ingest rows
```

**D1-S2 (ordinary-ingest stamping) is CLOSED.** D1-S1 (validator + read shim +
scoring-invariance baseline) closed earlier at commits
`8505678 feat(affect-attribution): add D1-S1 validator and legacy read shim` and
`6e728e8 test(affect-attribution): harden D1-S1 validation and parity guards`;
D1-S2 builds the first producer on top of it. No subsequent slice is authorized
by this checkpoint.

---

## 2. What landed

Production boundary (exactly two files):

```
torment_service/affect_attribution.py
- added the pure, validated constructor
    build_ingest_classifier_attribution(*, affect_tag)
  returning the canonical ordinary-ingest envelope; self-validates through
  validate_affect_attribution (defense in depth).
- updated the module scope docstring from S1-only to describe the S2 producer
  and the not-evaluated exclusion.

torment_service/fabric.py
- imported the constructor.
- added a local completion guard `affect_classification_completed` (init False).
- set it True ONLY after classifier processing completed without raising (it
  stays False when affect is disabled or when the classifier raises under
  fail-soft).
- conditionally stamped payload `affect_attribution` inside the fresh-spawn
  `_internal_ep` literal, BEFORE the existing internal-wins merge.
```

Tests (exactly three files):

```
tests/test_affect_attribution.py          (added ingest-classifier constructor units)
tests/test_affect_attribution_ingest.py   (new; producer + boundary suite)
tests/test_affect_attribution_parity.py   (added produced-envelope parity beside
                                            the existing injected-envelope S1 parity)
```

No other production file or test was modified.

---

## 3. Binding semantic rule

```
Stamp every fresh TormentFabric.ingest() row
iff affect classification completed successfully.
```

```
unset != not evaluated
```

The four affect-classification states:

```
set       = classifier completed successfully and produced an affect value
unset     = classifier completed successfully and produced no affect value
disabled  = classifier intentionally did not run
failed    = classifier attempted to run but raised
```

Only `set` and `unset` receive the D1-S2 envelope. `disabled` and `failed` are
*not-evaluated* states and are deliberately left unstamped — emitting
`via=ingest_affect_classifier / value_state=unset` for either would be false.
The completion guard (not the enable flag) is what enforces this: because
`classify_affect` is fail-soft, "enabled" does not imply "ran".

---

## 4. Architectural distinction

```
ProvenanceV1       = row lineage          — WHERE the row came from
affect_attribution = affect-value lineage — HOW the affect value was produced
```

These are orthogonal axes that coexist on one row. The D1-S2 seam is
**mechanism-defined, not caller-defined**: it stamps **all fresh rows written
through the `TormentFabric.ingest()` fresh-spawn branch when affect classification
completed successfully**, because each such row's affect was produced by the same
`classify_affect(summary)` mechanism. The stamp asserts nothing about row lineage;
that remains recorded, unchanged, in `ProvenanceV1`.

Named callers are **examples, not an allowlist**:

```
ordinary /agent/ingest
tool-result ingest
collective-echo reingest
cognition writeback
direct agent-loop assimilation
shared-scope ingest
baton-capable direct ingest
```

Caller identity stays irrelevant unless a future producer introduces a *different*
affect mechanism, at which point that producer defines its own attribution posture.

---

## 5. Integrity property (internal-wins) — scoped, not global

The existing merge in `TormentFabric.ingest()`:

```python
_merged_ep = dict(extra_payload or {})
_merged_ep.update(_internal_ep)   # internal wins on collision
```

**Exact guarantee (stamped rows only):** When affect classification completes
successfully, `_internal_ep` contains the internally generated
`affect_attribution` envelope. The existing internal-wins merge overwrites any
caller-supplied `extra_payload["affect_attribution"]`, so a caller cannot smuggle
a forged asserted or confirmed envelope into those stamped fresh rows. Locked by
test T7.

**Uncovered boundary (unstamped rows):** When classification is disabled or
raises, D1-S2 deliberately emits no internal `affect_attribution` stamp. In that
unstamped case, the current merge does not overwrite a caller-supplied
`extra_payload["affect_attribution"]` — it can survive. This is a named deferred
hardening boundary (see §7-B). It is **not** solved or authorized by the D1-S2
checkpoint; do not implement hardening here.

---

## 6. Verification evidence (Windows, source of truth)

```
Focused suite:
51 passed in 3.18s

Full Windows suite:
3646 passed, 5 skipped, 22 subtests passed in 94.55s

Staged whitespace check:
git diff --cached --check -> clean (before commit)
```

(Sandbox note: the isolated Linux sandbox could not run the `TormentFabric`-backed
suites — `fabric.py` imports `fastapi`, not installable there — and its `git diff`
renders CRLF on every line; per standing practice Windows is the authoritative
verification surface. The numbers above are the Windows results.)

---

## 7. Parked named limitations (NOT solved here)

Two distinct limitations are parked. Neither is solved or authorized by this
documentation slice.

**A. Not-evaluated fallback mismatch.** Disabled (`TORMENT_AFFECT_ENABLE=0`) or
classifier-exception fresh rows remain unstamped. For those rows the current read
shim synthesizes:

```
origin_kind = recovered
actor       = migration
via         = legacy_read_fallback
```

This is **known inaccurate deferred behavior, not endorsed semantics** — a freshly
created modern row is not legacy/migration-recovered, and the vocabulary has no
"not evaluated" posture yet. Captured as characterization test T12b. Parked for a
separately reviewed vocabulary micro-slice.

**B. Unstamped-row caller-envelope survival.** When no internal stamp is emitted
(the disabled / failed cases above), a caller-supplied
`extra_payload["affect_attribution"]` may survive the `_merged_ep` merge, because
internal-wins only overwrites when an internal stamp exists (see §5). The
anti-forgery guarantee therefore holds for *stamped* rows only, not globally.
This is a **named deferred hardening boundary**, adjacent to D1-S2 but **not part
of the already-landed patch**. It deserves its own separately reviewed hardening
micro-slice. Parked; not solved here.

---

## 8. Held-closed adjacent lanes

D1-S2 did **not** modify any of:

```
duplicate reinforcement
mood_drift stamping
scoring
fallback vocabulary
migration
backfill
deep export / deep rehydrate
promotion
confirmation writers
generic user_confirmed semantics
affect_state.json authority posture
```

(The mood_drift writer stores via a separate `add_memory(...)` path, not the
`_internal_ep` fresh-spawn seam, so it is structurally unstamped; T10 asserts this
boundary holds.)

---

## 9. Ordered continuation

```
D1-S2 ordinary-ingest stamping -> CLOSED (8b2c1f3)
D1-S3 mood_drift stamping      -> next candidate gate, AUDIT-FIRST ONLY
D1-S4 deep-rehydrate conformance
D1-S5 cross-surface conformance + generic user_confirmed isolation
```

D1-S3 is **not** authorized by this checkpoint. It opens, if at all, only through
the standard audit → draft → trio review → ratification cycle.

---

## 10. Orientation-map corrections made alongside this checkpoint

Minimal stale-wording updates only (status lines, not framing):

```
docs/PROJECT_ORIENTATION_MAP.md   — refresh date 2026-05-31 -> 2026-06-02;
                                    §2 snapshot intro date advanced; two D1
                                    closure rows added (D1-S1 commits 8505678 /
                                    6e728e8; D1-S2 commit 8b2c1f3 + this
                                    checkpoint); Q3-D1 parked-items entry:
                                    "implementation not yet opened" -> D1-S1 +
                                    D1-S2 closed, D1-S3 next candidate
                                    (audit-first).
docs/TORMENT_ROADMAP_NOTES.md      — Path C state date 2026-06-01 -> 2026-06-02;
                                    "Q3-D1 implementation still closed" -> D1-S1 +
                                    D1-S2 closed, D1-S3 next candidate
                                    (audit-first).
```

No unrelated orientation or roadmap framing was rewritten.

---

*End of D1-S2 closure checkpoint. Documentation only. D1-S3 remains unopened.*
