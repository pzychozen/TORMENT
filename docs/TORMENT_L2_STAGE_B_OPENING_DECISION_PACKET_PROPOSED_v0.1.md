# TORMENT Governed-Memory Substrate Programme — L2 Stage B Opening Decision Packet [PROPOSED]

**PROPOSED / NON-AUTHORIZING / OPENS NOTHING.**

**Status:** Proposed decision packet (Claude-side draft input). Not promoted as a decision. Selects no mechanics. Opens no gate. Authorizes nothing.
**Date:** 2026-06-17.
**Current synchronized baseline for this packet:** `fd25ab4`. Issue #54 was re-verified at `01ec838` and L2-A subsequently closed at `fd25ab4`; both are part of the chain, but `fd25ab4` is the current HEAD.

**Terminology (load-bearing):** "Stage B" (Issue #54 / council sense) = the database/substrate design gate. Opening it would start the Governed-Memory Substrate Programme, whose first task is a bounded design-framing pass defining the programme's internal Stage A (recovery/reconciliation semantics, P5a-shaped) / internal Stage B (carrier/substrate mechanics, P6-shaped) boundary.

---

## 0. Nature of this packet

A proposed bounded gate for the trio + Hilmir. It proposes **whether to authorize Stage-B-to-framing** — nothing more. It is the Claude-side draft input; the GPT steering pass, the Codex adversarial challenge (§5), and operator authorization are **not yet done**, so the packet is incomplete until they are. **This opening decision excludes mechanics; any later Stage B mechanics/design/construction work requires separately bounded authorization.**

## 1. Scope of what this decision proposes

- The **L2 decision packet proposes whether to authorize Stage-B-to-framing.**
- **If authorized later, Stage B opening authorizes bounded design framing only.**
- The **initial design-framing pass may inventory requirements, constraints, proof bars, and topic headings, but selects no mechanics.**
- **Later mechanics selection requires separate bounded authorization.**
- **Construction requires a separate construction-entry packet with evidence, clean state, and Hilmir hand-back.**

**Topic headings** the framing pass may inventory (council outcome §5 — headings only, no answers, no mechanics): meaning-preserving recovery; identity/sameness; canon-by-source distinguishability; write-side authority; durability/crash-safety; migration approach from JSON/JSONL; read-side conformance *scheduling* (P4 runtime conformance stays a separate, later-authorized track). Adopted work-ordering rule (council §4): `requirements → carrier proposal → family write-site work`, reader/projection runtime conformance separate.

## 2. Old-doc authority quarantine (carried)

> No current Stage-B opening authority has selected schema, carriers, storage products, or migration mechanics. Older tracked audits, roadmap notes, archive specs, Block designs, Cluster 5 framing, and memory-kernel architecture docs may contain concrete mechanism language, but they remain historical/scoped/non-authoritative for Stage B unless separately reconciled.

### 2.1 Explicit non-authority warnings

- `AUDIT_index_and_mcp_resources.md` SQLite/`core_nodes` **schema and migration fix-direction language** (e.g. "add `provenance_type` column", "migration: rebuild index") is **non-authoritative** for Stage B.
- `TORMENT_ROADMAP_NOTES.md` **future-storage section is idea-map only** ("none authorized today; TORMENT-governed memory first, database second").
- **SRG archive, Block A/B/C, Cluster 5 Path C, and Memory Kernel docs are historical/scoped unless separately reconciled.**
- **Older concrete implementation docs cannot become Stage B mechanism authority by implication.**

## 3. Unresolved constraints carried (NOT solved design)

These are requirements a later design must honor; none is solved or represented here.

- **Document A writer-authority:** payload flags (`canon`/`mtype`/`tier`/half-life) and source presence are **not authorization**.
- **Document B private cognition / dream / thinking layers are requirement-level only:** no runtime loop, scheduler, store, or reentry.
- **Seed-Gov canon-by-source distinguishability required;** no `canon_source` field/enum/schema selected.
- **P4 source-sameness not assumed from presence-only joins.**
- **P2.5 memory-lineage carrier absent;** analogues are not carriers.
- **Cluster 5 storage fragility handles** (`JSONL-NO-FSYNC`, `IDENTITY-NON-ATOMIC-SAVE`, `INGEST-NOT-TRANSACTIONAL`, `JSONL-LOADER-NOT-FAIL-TOLERANT`) **are design inputs, not fix authorization.**
- **No-Corner:** guidance not control; audit does not become authority.
- **Stage A recovery preserves governance meaning without pinning identity/canon/seed/soul** (and without invisible finalizer, output blocking, or hidden deletion/refusal).

## 4. Runtime hazards — parked non-conformances (NOT baseline behavior)

Carried as parked non-conformances; a later design must not encode them as correct:

- `gravity_correction` automatic `canon=True`.
- `_maybe_emit_identity_anchor` automatic derived identity writer.
- `POST /promote` force bypass.
- `mood_drift → centroid → gravity_correction → canon=True` inclusion path.

## 5. Proof bar (framing → mechanics → construction)

- **Registry §K trigger evidence before framing → construction** — at least one of: measured volume/load-time limits; transactional guarantees unmet by subordinate primitives; benchmarked geometric-locality advantage (G7); portability/auditability/recovery blockers; a TORMENT-native mechanism requiring deeper coupling (owning P6 eval / P8b evidence; trio authority).
- **Requirement-to-carrier traceability before carrier proposals become load-bearing** (each §3 requirement has an explicit "the design will honor this" statement first).
- **Fresh clean checkpoint before construction-entry** (Issue #54-style state re-verified at the construction-entry HEAD).
- **Hilmir hand-back before any identity/canon/seed/soul meaning change.**
- **No irreversible migration behavior without separate authorization.**
- **No construction-entry from L2** — construction requires its own separate construction-entry packet.

## 6. What Codex must challenge before authorization

Hidden database auto-opening; premature substrate assumptions (any implied carrier/schema/source-sameness); old-doc authority leakage (quarantine completeness); guidance→control wording (pinning / invisible finalizer / output blocker / hidden deletion-refusal); scope creep into parked tracks (P4 runtime conformance, writer-authority fixes, Seed-Gov implementation, canon_source representation); category-vs-mechanic boundary (headings only); two-stage integrity (semantics not skippable or pre-answered by mechanics).

## 7. Explicit non-authorizations

This packet opens **none** of: L2, Stage B, database/schema/storage/carriers/migration design, product/mechanic selection, implementation, construction, writer-authority fixes, P4 mechanics, Seed-Gov mechanics, `canon_source`, mood_drift filtering, promote authorization redesign, autonomy, or old-doc mechanism adoption. **No registry amendment; no registry number reserved.** No prior doc edited.

---

## Anti-drift footer

PROPOSED / NON-AUTHORIZING / OPENS NOTHING. This packet records a proposed gate and carry-forward constraints only. **This opening decision excludes mechanics; any later Stage B mechanics/design/construction work requires separately bounded authorization.** Active gate: none. Next gate: unselected — L2 Stage B Opening Decision remains named but unopened. Guide, not control; audit observes authority and does not become authority; nothing rewrites identity/canon/seed/soul. Subsequent versions require their own trio/operator ratification.
