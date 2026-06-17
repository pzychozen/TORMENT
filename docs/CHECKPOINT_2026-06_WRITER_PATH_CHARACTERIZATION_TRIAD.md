# Checkpoint — Writer-Path / Endpoint-Wiring Characterization Triad (Seams 1–3)

**Type:** Tracked closure checkpoint. Documentation only — records a closed
read-only / test-only characterization chain. No production-code, schema,
scoring, doctrine, or governance change is authorized by this file, and it opens
no design gate.
**Closure recorded:** 2026-06-17.
**Runtime/test-chain baseline:** HEAD = origin/main = `b549a97` (authoritative
pre-doc baseline / closed test-chain HEAD); working tree clean. This checkpoint
doc is added after that baseline and was not present at `b549a97`.
**Anchors (context only, not runtime requirements):**
`docs/TORMENT_GRAVITY_CORRECTION_AUTOMATIC_CANON_AUDIT_FIRST_RECONCILIATION_v0.1.md`
(§N14), `docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`
(Document A §11), `docs/TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md` (§9),
`docs/TORMENT_MEMORY_ENGINE_PRE_P4_READER_DEPENDENCY_TRACE_v0.1.md`.

---

## 1. Scope and posture

This records three small seams that followed the closed Candidate A/B
`gravity_correction` lane. All three are **characterization only**: they pin
current behavior as read-only findings or test-only regression barriers. None is
a fix, none asserts that the characterized behavior is desired runtime doctrine,
and none opens database design, Stage B, Seed-Governance implementation,
Document A runtime gates, `canon_source`, P4 / read-side conformance, or new
doctrine.

The anchors above are cited as the doctrinal context that *named* these seams as
unreconciled; citing them here imports none of their later-owned mechanics and
asserts no runtime requirement.

---

## 2. Seam 1 — `drift_reflex_callback` consumption trace (CLOSED read-only)

Traced the **consumption side only**; the firing-side state machine is already
covered by `tests/test_reflex_auto_fires.py` and was not re-characterized.

Finding: `drift_reflex_callback` is **declared** (`torment_service/fabric.py:691`)
and **dispatch-capable** (fired on a below→above transition,
`fabric.py:3353–3371`), but **unwired** — no path in the repository registers a
consumer, so it defaults to `None` and never fires in shipped paths. The
documented intended sink `enter_reflex` (`torment_service/agent_loop.py`) is not
connected to it. It is a latent extension point, not dead/removable code; removal
is not proposed.

Because no consumer exists, there is no current canon / identity / authority /
storage / cognition / retrieval / model-visible effect through this seam. The
dispatch passes a defensive copy of the drift dict, ignores any return value, and
isolates callback exceptions from ingest.

**Closure:** read-only finding. No test, no patch, no doc-gate added.

---

## 3. Seam 2 — `_maybe_emit_identity_anchor` writer-path characterization (CLOSED test-only)

Closed at commit `cd35aae` with `tests/test_identity_anchor_writer_path_characterization.py`,
which drives the **real** `TormentFabric._maybe_emit_identity_anchor`.

It pins the **current** automatic emission shape: when motif count / gap
thresholds are met by present same-fixture members, the writer emits one derived
`identity_anchor` row with `canon=False`, `anchor_origin="derived"`,
`anchor_source="motif_cluster"`, decade half-life, and `source_member_eids`
reflecting the present members — driven solely by motif count / gap / role /
affect heuristics, **without any authority, seed-governance, or operator input**.

This is characterization of current behavior, not a fix and not a statement of
desired runtime behavior. Read-side tier hygiene
(`tests/test_anchor_tier_hygiene.py`) is not re-tested. No P4 / source-sameness,
presence-vs-sameness, or prior-anchor retirement semantics are opened.

---

## 4. Seam 3 — `POST /promote` force-bypass endpoint-wiring characterization (CLOSED test-only)

Closed at the `b549a97` baseline with
`tests/test_promote_force_bypass_endpoint_wiring.py` (FastAPI `TestClient`,
isolated `TORMENT_DATA_DIR`).

It pins the **current endpoint wiring**: a bland low-signal chunk does not
promote under `force=False`; with `force=True` the handler maps the flag into
both evaluation inputs (`is_canon=True`, `user_approved=True`) and reaches
`promote_chunk`; and the `result.promote or req.force` branch executes even when
evaluation is stubbed to decline. The writer row shape is **not** re-tested — it
is owned by `tests/test_checkpoint_promotion.py`, and `promote_chunk` is
sentinel-replaced so only endpoint reachability is asserted.

This is a current request-surface characterization only. No auth / governance
doctrine is imported, and no claim is made about the presence or absence of any
auth middleware or security control beyond this single call path.

---

## 5. Parked (no work opened)

Any future **fix** or governance change for these seams is explicitly parked, not
authorized here:

```
_maybe_emit_identity_anchor writer authority     → writer-authority reconciliation slice (later owner)
identity-anchor source-membership (presence→same) → P4 O2 (later owner)
promote_chunk / POST /promote force authorization → writer-authority reconciliation slice (later owner)
drift_reflex_callback wiring (if ever)            → separate cognition-affecting slice (later owner)
```

None of the above is opened by this checkpoint.

---

## 6. Gate state

Active gate: none. **Next lane: unselected.** This checkpoint opens nothing; any
next slice requires a separate gate-start survey (orientation map §5) and explicit
operator authorization.
