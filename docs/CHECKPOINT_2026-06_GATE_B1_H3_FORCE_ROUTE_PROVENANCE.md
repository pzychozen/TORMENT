# Checkpoint — Gate B1 / H3 Force-Route Provenance (landed runtime slice)

**CODE-SLICE CHECKPOINT — docs-only record of a landed code slice. No new gate, no authority doctrine,
no registry amendment.**

**Anchors:** `ae242af` *feat(promotion): record /promote force-route provenance on canon writes* ·
`6d50254` *chore(promotion): normalize app.py line endings after H3 provenance*. **Date:** 2026-06-19.

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

Closure of a landed code slice. This records what shipped for the first H3 runtime improvement and stops
there. It opens no gate, selects no mechanism, amends no registry, and changes no authority. H3 remains a
**leaf under Writer Authority / Document A**; **H1 remains parked and is not de-risked**;
**database/substrate remains last**.

## 2. What landed — the first H3 runtime improvement (provenance, not control)

The first H3 runtime slice landed: `POST /promote` force-route promotions now carry **durable
provenance**, making a force-bypass canon write **distinguishable** from an evaluator-approved one. It
implements **provenance only — not control**: nothing is blocked, gated, refused, or finalized.

- `app.py::promote_chunk_endpoint` now passes `extra_payload={"promotion_force_requested":
  bool(req.force), "promotion_evaluator_promote": bool(result.promote)}` into the existing
  `promote_chunk(...)` call. A true force-bypass is therefore identifiable as
  `promotion_force_requested == True and promotion_evaluator_promote == False`.
- `promotion.py::promote_chunk` now **fails closed** if `extra_payload` attempts to override a reserved
  core promotion payload key — `memory_class`, `kind`, `tier`, `source_ref`, `promoted_at`, `canon` —
  returning `None` with no `spawn_memory` and no `flush_node`.
- The provenance is written into the promoted row's existing payload block (audit-metadata, alongside
  `kind` / `source_ref` / `promoted_at`); it is not surfaced into any model-visible projection.

**Unchanged:** promotion eligibility, the `/promote` endpoint response shape, the
`if result.promote or req.force` execution branch, auth, governance, and canon semantics.

## 3. Validation evidence (Windows-authoritative)

- Focused: `tests/test_promote_force_bypass_endpoint_wiring.py` + `tests/test_checkpoint_promotion.py`
  — **30 passed**.
- Full suite — **3965 passed, 5 skipped, 22 subtests passed**.
- `6d50254` normalized `app.py` line endings so the slice's diff is confined to the intended change.

## 4. Files changed across the slice

- `torment_service/app.py` — force-route provenance passed at the `promote_chunk(...)` call site
  (plus the `6d50254` EOL normalization).
- `torment_service/promotion.py` — reserved-key fail-closed guard before the payload merge.
- `tests/test_promote_force_bypass_endpoint_wiring.py` — force-route provenance assertions +
  evaluator-approved non-force test.
- `tests/test_checkpoint_promotion.py` — direct `promote_chunk` provenance / reserved-key /
  summary-not-polluted tests.

## 5. What it is NOT (boundaries held)

- **Not** control — no blocking, gating, refusal, finalizer, or output suppression.
- **No** auth-policy selection; the upstream `/promote` caller-auth surface remains untraced/open.
- **No** governance-vehicle selection (incl. Cluster 2 v0.2).
- **No** endpoint redesign and **no** endpoint response change.
- **No** canon-semantics change.
- **No** H1 / `gravity_correction` work; **no** Phase-7; **no** Seed-Governance mechanics; **no** P4 /
  source-sameness mechanics; **no** private-cognition / dream runtime; **no** database / substrate.

## 6. Where it sits

H3 is one **leaf** of the Writer-Authority strand of **Document A** (Candidate Containment + Writer
Authority) — not the programme. This slice delivers the **provenance** requirement-property of a
"governed writer" (visible / provenance-bearing / contestable / bounded posture) for the H3 force route
only. The other inventoried hazards (H1, H2, H4–H6) are untouched; **H1 remains parked and is not
de-risked**, its sharper automatic-authority concern standing on the record.

## 7. Direction / next step

The H3 force-route provenance question is now answered in runtime by an additive, audit-visible
provenance stamp. Any further H3 work (or any other writer-authority subject) is a separate, later,
explicitly-authorized step. Database / substrate remains last.

---

*Code-slice checkpoint only. Opens no gate, selects no mechanic, amends no registry, and changes no
authority. Provenance, not control. Audit observes authority and does not become authority. Memory may
shape context. Memory may not seize authority. Database / substrate remains last.*
