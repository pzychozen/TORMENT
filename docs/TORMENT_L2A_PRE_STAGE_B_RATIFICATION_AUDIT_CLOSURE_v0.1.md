# TORMENT L2-A — Pre-Stage-B Roadmap / Ratification Audit Closure v0.1

**Status:** Promoted docs-only closure memo. Synthesis of a read-only archaeology
pass (Claude) and an adversarial challenge pass (Codex). Records findings and
carry-forward warnings only. **NOT a Stage B opening. NOT the L2 Stage B Opening
Decision. NOT database/substrate design. NOT a registry amendment.**
**Date:** 2026-06-17.
**Runtime/test-chain baseline at audit time:** HEAD = origin/main = `01ec838`;
working tree clean. This memo is added after that baseline and was not present at
`01ec838`.

---

## 1. Status and scope

L2-A is the pre-Stage-B ratification audit: before deciding whether the L2 Stage B
Opening Decision can be prepared, verify that the cognition-, thinking-, dream-,
private-state-, guided-memory-, and roadmap-layer commitments are each (1) ratified
and correctly represented, (2) implemented where they are supposed to be, (3)
explicitly parked, or (4) marked as needing a reconciliation memo before any
database/substrate work. This memo is **read-only synthesis**; it selects no
mechanics, edits no prior design docs, and opens no gate.

## 2. Sources considered

Orientation map; Issue #54 clean-checkpoint record (and its `01ec838`
re-verification); Memory-Engine Decision Registry (§N5–N16); P4, P2.5, P1/P2,
Stage A; Document A, Document B, Seed-Governance, No-Corner; Ledger
Observational-Boundary; MCP capability boundary; thinking-layer archaeology
soft-state postures (§N7); DB/Substrate Doctrine Reconciliation (N12);
matched P2.5/P4 (N13); gravity_correction reconciliation (N14); council framing
(N15) and outcome (N16); substrate-readiness memo. Historical/scoped material was
read **as context only**: external `ROADMAP_13042026.md`, `TORMENT_ROADMAP_NOTES.md`
future-storage section, `docs/archive/SRG_INTEGRATION_SPEC.md`, Block A/B/C design
docs, Cluster 5 framing, memory-kernel architecture docs.

## 3. Ratified requirement stack

All promoted docs-only, closed, **requirement-level**: P4 (reader/projection
safety), Document A (write-side containment / writer-authority), Document B
(private-cognition / unified-reflection interior, incl. Dream/Incubation Regime B),
Seed-Governance (seed/identity/canon), No-Corner (bounded defensive availability),
Stage A (recovery/reconciliation semantics), P1/P2/P2.5 (era/identity/cross-contract
reconciliation), Cluster 2 (authority/lifecycle vocabulary), Ledger, MCP boundary,
and the §N7 soft-state continuity postures. The bridge/closure layer (N12–N16) is
likewise closed. The stack is internally consistent and substrate-neutral; none of
it selects a representation.

## 4. Runtime-conformance gap posture

The pre-substrate stack is **ratified at requirement level and deliberately not
implemented**. Each contract states "runtime conformance is later-owned (P2.5 / a
separately authorized implementation track)." The gap between requirement and
runtime is therefore the **designed, documented posture — not drift.** Live runtime
carries the pre-contract behaviors (TriOcta kernel, measure_drift, gravity_correction,
_maybe_emit_identity_anchor, promote_chunk/force, mood_drift, spirit-return,
character_context, deterministic ThinkingController→MemoryPlan routing). Dream /
private deliberative cognition is **roadmap-only / parked**, not implemented.

## 5. Claude findings accepted

1. The ratified requirement stack is internally consistent and substrate-neutral.
2. No tracked database/substrate-design document selects schema, carriers, storage
   product, source-sameness, or migration mechanics.
3. The automatic canon/identity writers (gravity_correction, _maybe_emit_identity_anchor,
   promote_chunk/force) are **characterized but not yet conformant** with Document A
   A-O1 / Seed-Gov SG-O4/SG-O5 — **documented and parked** (DB/Substrate memo §11
   seam 8; routed to writer-authority + gravity audit-first reconciliation), not silent
   drift.
4. The `mood_drift → drift centroid → gravity_correction → canon=True` inclusion path
   is recorded as topology only (Lane A), parked.
5. SG-O4 canon-source representation and P2.5 memory-lineage identity carriers are
   **absent by design** — a hard dependency a later Stage B would have to define, not
   a defect.
6. Minor docs-reconciliation candidates exist (SRG archive spec conditional status if
   SRG enters Stage B scope; a pointer tying roadmap-notes future-storage to N12;
   confirming the external roadmap stays non-authoritative) — flagged, not edited here.

## 6. Codex objections accepted

1. **Old-doc mechanism language must be quarantined.** Several historical/scoped docs
   contain concrete mechanism language (fields, constants, SQLite shapes, storage
   candidates) that must not be read as Stage B authority (see §7).
2. **No hidden database auto-opening** — verified; but the L2 packet must restate that
   inventory/candidate language in any doc authorizes nothing, so a later reader cannot
   infer authorization from it.
3. **No premature substrate assumptions.** Absent carriers (SG-O4, P2.5) and presence-only
   P4 joins must be carried as *requirements the design defines*, never assumed solved;
   the design must not encode current automatic-writer behavior as correct.
4. **Guidance must not become control.** Any later recovery/restoration design must
   preserve Stage A O6 / Seed-Gov SG-O8 / No-Corner / Ledger — no pinning of soft
   guidance, no invisible finalizer, no silent authority.
5. **No unratified cognition-layer claims.** The dream / private-thinking layer is
   roadmap-only/parked; Stage B must not assume it exists or build on it.

## 7. Old-doc authority quarantine

> No current Stage-B opening authority has selected schema, carriers, storage products,
> or migration mechanics. Older tracked audits, roadmap notes, archive specs, Block
> designs, Cluster 5 framing, and memory-kernel architecture docs may contain concrete
> mechanism language, but they remain historical/scoped/non-authoritative for Stage B
> unless separately reconciled.

These docs are **preserved intact**; this memo edits none of them. Their mechanism
language is prior art / historical scope only and carries no Stage B authority.

## 8. Mandatory L2 carry-forward warnings

Carry into the L2 Stage B Opening Decision packet:

1. The DB/Substrate Doctrine Reconciliation (N12) register as the "requirements a later
   substrate must honor" — including the influence-axis and write-side non-collapses.
2. The automatic-writer non-conformance (§5.3): do **not** encode current behavior as
   correct; it is a parked reconciliation, not a baseline.
3. The absent SG-O4 canon-source and P2.5 lineage carriers as design obligations, not
   assumptions.
4. The guidance-not-control guards (Stage A O6, SG-O8, No-Corner, Ledger) as binding on
   any recovery/restoration wording.
5. The old-doc authority quarantine (§7).
6. The parked seams: writer-authority reconciliation, P4 runtime conformance, Cluster 5
   v0.2 storage fragilities, Track B v0.2, dream/private-thinking layer — none opened by
   this audit.

## 9. Explicit forbidden openings

This closure opens **none** of: L2, Stage B, database design, schema, storage, carriers,
migration, P4/read-side conformance, Seed-Governance implementation, writer-authority
fixes, `canon_source`, mood_drift filtering, promote authorization redesign, or any
migration plan. It selects no mechanics and amends no contract or registry entry.

## 10. Closure verdict

> L2-A found no structural blocker to preparing the L2 Stage B Opening Decision,
> provided the Codex objections and old-doc authority quarantine are carried into the L2
> packet. This closure does not open L2, Stage B, database design, schema, storage,
> carriers, migration, P4 conformance, Seed-Gov implementation, writer-authority fixes,
> canon_source, mood_drift filtering, promote authorization redesign, or any migration
> plan.

---

## Anti-drift footer

This memo records audit synthesis and carry-forward warnings only. It opens no gate,
selects no mechanics, edits no prior design/roadmap/archive/Block/Cluster/memory-kernel
doc, and makes no registry amendment (and reserves no registry-amendment number). Active
gate: none. Next gate: unselected — **L2 Stage B Opening Decision remains named but
unopened.** Guide, not control; audit observes authority and does not become authority;
nothing rewrites identity/canon/seed/soul. Subsequent versions require their own
trio/operator ratification.
