# Checkpoint — Cluster 5 §9.3 Path C → Q3-D1-H1 (caller-envelope survival hardening)

**Type:** Tracked closure checkpoint. Documentation only — records a landed
hardening micro-slice. No production-code, schema, scoring, or test change is
authorized by this file, and it does **not** open D1-S3.
**Closure recorded:** 2026-06-03.
**Anchors:** `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S2_ORDINARY_INGEST_ATTRIBUTION.md`
(§5 scoped guarantee + §7-B named the boundary this slice closes),
`docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md` (ratified contract).

---

## 1. Closure identity

```
Gate:
Cluster 5 Path C -> Q3 affect attribution -> Q3-D1 -> D1-H1

Closed commit:
7066b57 fix(affect-attribution): strip forged caller envelope before ingest merge
```

**Q3-D1-H1 is CLOSED.** It hardens the seam landed by D1-S2
(`8b2c1f3`) without opening any new producer slice. No subsequent slice is
authorized by this checkpoint.

---

## 2. Reason

Caller-supplied `extra_payload["affect_attribution"]` could survive
`TormentFabric.ingest()` when affect classification was **disabled** or
**failed**. In those not-evaluated states the internal writer emits no stamp, so
`_internal_ep` carried no `affect_attribution` key and the prior internal-wins
merge had nothing to overwrite. The anti-forgery guarantee therefore held for
*stamped* rows only, not globally — this is exactly the boundary named in the
D1-S2 checkpoint §7-B (Parked-B).

A surviving forged envelope would read back through `read_affect_attribution`
as authoritative affect-value lineage (e.g. `actor=user / origin_kind=asserted /
confirmation=confirmed`), which `affect_attribution` is not permitted to source
from an ordinary caller.

Scope note: no production or HTTP caller currently sets this field
(`extra_payload` is not plumbed through the Spine `_fast_ingest` / tool-result
forwarders, and no in-process caller passes it), so this closed a **latent**
vector, not an active one. That does not lower its correctness value; it means
the change carried minimal expected compatibility risk.

---

## 3. Resolution

`affect_attribution` is now treated as a **reserved internal field** at the
`TormentFabric.ingest()` caller-payload merge seam. The caller payload is copied,
the reserved key is stripped from the copy, then the internal-wins merge runs:

```python
_caller_ep = dict(extra_payload or {})
_caller_ep.pop("affect_attribution", None)   # reserved internal field
_merged_ep = _caller_ep
_merged_ep.update(_internal_ep)              # internal wins on collision
```

The internal writer adds a truthful envelope back above iff classification
completed successfully. The caller's original dict is never mutated. Posture A
of the authorized H1 framing.

Production boundary (one file): `torment_service/fabric.py` — the merge seam only.
Tests (one file): `tests/test_affect_attribution_ingest.py` — added
`TestH1DisabledCallerEnvelopeStrip` (H1a–H1e) and `TestH1FailedCallerEnvelopeStrip`
(H1f). No other production file or test was modified.

---

## 4. Guarantee

```
Global anti-forgery across TormentFabric.ingest() fresh-spawn rows.
```

A caller can no longer place an `affect_attribution` envelope on any fresh
`TormentFabric.ingest()` row through the generic `extra_payload` carrier —
regardless of whether classification completed, was disabled, or raised. The
field is now writable only by the internal classifier producer. This promotes the
D1-S2 §5 guarantee from *stamped-rows-only* to *global*.

Malformed-envelope corollary: a present-but-malformed caller envelope is also
stripped, so it can never be persisted and then fail loud on later read. Fail-loud
validation continues to apply where it belongs — a malformed envelope that is
genuinely *persisted* still fails loud at validation time.

---

## 5. Verification evidence (Windows, source of truth)

```
Focused suite:
57 passed

Full Windows suite:
3652 passed, 5 skipped, 22 subtests passed

Commit / push:
e1eb45e..7066b57  main -> main
git status --short --branch -> ## main...origin/main
```

(Verification note: per standing project practice, the Windows workspace is the
authoritative verification surface. AI-side mounted filesystem views may contain
EOL noise or stale/truncated file representations and were not used as evidence.)

---

## 6. Still parked (NOT solved here)

```
not-evaluated fallback vocabulary mismatch   (D1-S2 §7-A / characterization T12b)
D1-S3 mood_drift stamping
direct MemoryGraph producer policy
all broader authority and promotion seams
```

H1 stripped forged caller envelopes; it did **not** resolve the not-evaluated
fallback vocabulary. An unstamped fresh row still reads back through the legacy
fallback as `recovered / migration / legacy_read_fallback` — known inaccurate
deferred behavior, locked as characterization (H1b's read assertion and the
existing T12b). That vocabulary decision remains a separate, separately reviewed
micro-slice.

---

## 7. Ordered continuation

```
D1-S2 ordinary-ingest stamping  -> CLOSED (8b2c1f3)
D1-H1 caller-envelope strip      -> CLOSED (7066b57)
D1-S3 mood_drift stamping        -> next candidate gate, AUDIT-FIRST ONLY
D1-S4 deep-rehydrate conformance
D1-S5 cross-surface conformance + generic user_confirmed isolation
```

D1-S3 is **not** authorized by this checkpoint. It opens, if at all, only through
the standard audit → draft → trio review → ratification cycle.

---

*End of Q3-D1-H1 closure checkpoint. Documentation only. D1-S3 remains unopened.*
