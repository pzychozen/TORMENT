# TORMENT Memory Engine —
# Substrate Readiness and Phase Consolidation Memo v0.1

**Status:** Tracked logistics and programme-boundary memo. Promoted docs-only. Not doctrine. Not a graph amendment. Opens no gate. Authorizes no implementation and selects no mechanics.
**Date:** 2026-06-09. **Lineage:** Remaining-Phase Necessity Audit → Codex adversarial review → working-folder memo → two wording-only corrections → docs-only promotion. The decision registry already holds the authoritative graph and §K trigger; this memo clarifies how to interpret the remaining territory, it does not alter registry classes or rewrite the dependency graph.

## 1. Status

Read-only programme-boundary memo, now tracked. No gate opened. No implementation authorized. No mechanics selected. No graph amendment. No registry amendment.

Standing anchors, carried together:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.

## 2. Executive verdict

The post-P4 roadmap is **not a mandatory gate conveyor belt** — its phases are a dependency-ordered map, not a queue that must be drained in sequence. **P3 is real but dormant** (a genuine shell-continuity seam with no live dependency today). Substrate-design consideration is **eligible under registry §K because tracked evidence already establishes, at minimum, the unmet-transactional-guarantees trigger; related recovery and auditability blockers are also documented (§3 below).**

**Eligibility ≠ authorization.** No substrate programme is opened by this memo. Eligibility means the trio *may* deliberately choose to open a design-framing pass; it does not start one, and it selects no mechanics.

## 3. Existing §K eligibility evidence

Assembled from already-tracked facts only (no new gathering):

- **`JSONL-NO-FSYNC`** — canonical appends carry no flush/fsync/journal; trailing or torn records can be lost on crash (Cluster 5 v0.1 §5.1).
- **`IDENTITY-NON-ATOMIC-SAVE`** — identity/character/role saves use raw truncate-and-write; a crash can leave zero-byte or partial files (Cluster 5 v0.1 §5.2).
- **`INGEST-NOT-TRANSACTIONAL`** — one `fabric.ingest()` writes across `nodes.jsonl`, `edges.jsonl`, `memory_events.jsonl`, embedding shard + map, and SQLite with no enclosing transaction; documented orphan-state window (Cluster 5 v0.1 §5.3).
- **`JSONL-LOADER-NOT-FAIL-TOLERANT`** — the primary loader does not catch `JSONDecodeError`; one torn line aborts the whole load (Cluster 5 v0.1 §5.10).
- **P2.5** — memory-lineage identity has **no current substrate carrier**; canonical P1/P2 carrier-field vocabulary is absent across `torment_service` (registry §J P2.5; P2 closure standing tension).
- **P4** — O1/O2 source-sameness obligations have **no selected carrier or comparison mechanism**; the live joins are presence-only (P4 contract O1/O2).

Together these establish, at minimum, the **unmet-transactional-guarantees** trigger, with related **recovery and auditability blockers** also documented — which is what makes substrate-design consideration eligible under registry §K.

These facts make substrate-design consideration **eligible**. They do **not** authorize: implementation · database selection · SQL selection · identity-token selection · fingerprint algorithm · serialization · allocator · manifest · packaging · migration.

## 4. One umbrella programme, two internal stages

Future umbrella name (recorded, not opened): **TORMENT Governed-Memory Substrate Programme.**

**Internal Stage A — recovery and reconciliation semantics (P5a-shaped):** what must remain recoverable; what remains inspectable; the `diagnostic_only` posture; orphan and mismatch treatment; quarantine semantics; the non-coercive recovery boundary.

**Internal Stage B — carrier and substrate mechanics (P6-shaped):** identity carriers; revision fingerprints; serialization; allocator durability; IntegrityManifest mechanics; substrate architecture; packaging-boundary evaluation.

The two stages are **mutually constraining and should be framed under one umbrella. Stage A may define semantics without selecting Stage B mechanics; Stage B must later satisfy those semantics and may surface bounded questions that require an explicit Stage A amendment.** They remain **distinct deliverables**: semantics must not smuggle mechanics, and mechanics must not silently pre-answer semantics.

## 5. Cluster 5 and Track B relationship

**Cluster 5 v0.2** fragility work (the §5 handles, §9.2 seam) is an **input** to the governed-memory substrate programme — not a separate competing track.

**Track B durability and survivability requirements contribute inputs** where contest-ledger records must remain recoverable *with their governance meaning* (Track B v0.1 Invariant 14; Cluster 5 v0.1 §7.3). **Track B v0.2 is not absorbed** by this programme.

Kept separately parked (Track B's own future audit-first cycles): disagreement semantics · resolver-authority boundary · `candidate_handle → eid` binding · target-existence policy · counter-contest result routing · cognition-coupling decisions.

## 6. P3 relationship

P3 is a **real shell-continuity seam but not the next task** (verified: `restore_from_checkpoint` has zero runtime callers — defined, test-covered, unwired). P3 becomes load-bearing **before any non-test, non-debug runtime path restores checkpoint or shell state in a way that affects** cognition, identity, agency, continuity claims, operator expectations, or output behavior. Until then, **fresh awakening remains current behavior and P3 stays dormant.**

## 7. Later-lane classification

- **P7** — conditional compression lane.
- **P8a** — optional benchmark gate for research-derived hypotheses.
- **P8b** — optional experimental geometry lane; explicitly non-blocking.
- **P9** — real later migration dependency; only after a target substrate exists.
- **P10** — unspecified later-stage placeholder.
- **P11** — unspecified later-stage placeholder.

None is an immediate prerequisite.

## 8. Orientation-map clutter for later curation only

Several old candidate lanes remain useful historical or parked references but should **not** be mentally mixed with the Memory Engine substrate programme.

Retain as potentially live: the substrate-readiness / Cluster 5 family; the authority-versus-emergence small audit-first memo side lane.

Mark as later-curation candidates only: old v0.2.4 archive sub-gates; Gap C (already closed); Tier 3 endurance; deterministic visualization fixture; Ryuki live check; `do_not_touch_` rig audit; paused MCP cross-host work.

(No orientation-map curation of the candidate list is made in this slice.)

## 9. Smallest future decision point

The next deliberate trio decision, **when Hilmir chooses to continue**, is whether to open the **TORMENT Governed-Memory Substrate Programme**. The first programme task would be a **design-framing pass defining its internal Stage A / Stage B boundary**. It is **not opened now.**

## 10. Non-decisions preserved

```
no phase opened          no implementation        no runtime patch
no tests                 no executable probe      no mechanics
no database or SQL selection                      no identity-token selection
no fingerprint algorithm no serialization         no allocator mechanics
no manifest mechanics    no packaging decision    no migration
no motif redesign        no stored-edge repair    no quarantine mechanics
no recovery UX           no Track B authority decision
no P3 doctrine           no maintenance           no CodeQL work
no docs edit beyond this promotion                no graph rewrite
no registry amendment
```

---

*End Substrate Readiness and Phase Consolidation Memo v0.1. Tracked logistics artifact; assembles existing evidence only; opens nothing.*
