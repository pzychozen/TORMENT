# Checkpoint — mood_drift → drift-centroid inclusion trace (Lane A, read-only)

**Type:** Tracked closure checkpoint. Documentation only — records a read-only
evidence trace. No production-code, test, schema, scoring, doctrine, or
governance change is authorized by this file, and it opens no design gate.
**Closure recorded:** 2026-06-17.
**Runtime/test-chain baseline:** HEAD = origin/main = `1f6cd0d` (authoritative
pre-doc baseline; working tree clean). This checkpoint doc is added after that
baseline and was not present at `1f6cd0d`.
**Anchor (context only, not a runtime requirement):**
`docs/TORMENT_GRAVITY_CORRECTION_AUTOMATIC_CANON_AUDIT_FIRST_RECONCILIATION_v0.1.md`
§6–§7 (cited as context; no mechanics imported here).

---

## 1. Finding

[READ-ONLY FINDING] The `mood_drift -> drift centroid -> gravity_correction -> canon=True` path is confirmed as an active inclusion path for eligible rows: a recent same-agent `mood_drift` row with an embedding is not filtered out of `measure_drift`'s weighted recent-memory centroid. This records topology only. It does not characterize magnitude, single-row decisiveness, harmfulness, or required remediation; `mood_drift` remains a guidance/affect-continuity signal, and no runtime gate or filtering requirement is introduced here.

---

## 2. Evidence (topology only)

- `_maybe_emit_mood_drift` emits a `canon=False` `mood_drift` row into the
  agent's private graph (`torment_service/fabric.py:1575+`; `add_memory` at
  `:1646`), carrying an embedding.
- `measure_drift` reads that same private graph (called at `fabric.py:3297`;
  centroid loop at `torment_service/character.py:419–454`). Its only centroid
  exclusions are seed_canon rows, other-agent rows, rows outside the recency
  window, and rows lacking an embedding — there is no `mood_drift`, canon, tier,
  or source exclusion, so an eligible `mood_drift` row is included in the
  weighted recent-memory centroid.
- `gravity_correction` is the downstream automatic writer reached on threshold
  `away_seed` drift; it is named here only as the path endpoint and is not
  re-characterized.

---

## 3. Explicit non-claims

- Does not characterize magnitude, and does not assert that a single row can
  cause drift correction.
- Does not say `mood_drift` is bad, contaminated, or should be blocked.
- Does not say `mood_drift` carries or should carry canon authority.
- Imports no Seed-Governance, Document A, writer-authority, or canon-source
  mechanics as runtime requirements.
- Proposes no filtering, no `gravity_correction` change, and no
  schema/storage/test/production work.

---

## 4. Gate state

Active gate: none. **Next lane: unselected.** This checkpoint opens nothing; any
next slice requires a separate gate-start survey (orientation map §5) and
explicit operator authorization. No registry amendment is made by this file.
