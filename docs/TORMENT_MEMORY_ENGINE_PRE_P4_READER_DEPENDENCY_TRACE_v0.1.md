# TORMENT Memory Engine — Pre-P4 Reader-Dependency Trace v0.1

**Status:** TRACKED PRE-P4 EVIDENCE ARTIFACT — bounded read-only reader-dependency trace distillate. Records facts, risks, and later-owner routing only. Authorizes no implementation, opens no gate, selects no mechanics, and does not draft P4.
**Date:** 2026-06-07.
**Anti-drift reference:** `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.
**Lineage:** Claude bounded read-only pre-P4 reader-dependency trace → Codex narrow adversarial verification (surfaced the motif→identity-anchor second path) → GPT steering synthesis → this distillate. Claude independently re-verified the Codex-surfaced path against code before recording it.
**Tags:** [FACT] (file:line) · [RISK] · [ROUTING] · [PARKED] · [NON-DECISION] · [ANTI-DRIFT].

---

## 1. Scope and posture

[NON-DECISION] P0, P1, P2, and P2.5 remain closed. Active gate: none. P4 is next in the dependency graph but **unopened and unselected**. This artifact is the evidence precondition for later P4 framing. No implementation and no executable probe is authorized.

## 2. Corrected headline

[FACT] There are **two** confirmed cognition-affecting reusable-eid dependencies, on different axes:

> DeepMemoryEcho is the sole confirmed **direct echo-to-prompt** H-1 reader.
>
> It is **not** the sole cognition-affecting reusable-eid dependency. Motif membership → identity-anchor emission is a **separate, derived** cognition-affecting reusable-eid path.

[ANTI-DRIFT] Do not collapse the two paths; do not overstate either. The deep path is a *retrieval-time direct read* of a borrowed eid into the prompt. The motif path is an *ingest-time derived emission* that resolves persisted member eids by presence and distills them into a new memory; its cognition reach is real but bounded (§4). An earlier internal framing that called DeepMemoryEcho the "sole confirmed cognition surface" is **superseded by this two-path statement** — it had traced retrieval-time readers and missed the ingest-time derived-emission path.

## 3. DeepMemoryEcho direct cognition path

[FACT]
- `_query_deep_lane` beta validation is **presence-only**: it admits a deep hit iff a live graph entity exists under the borrowed eid (`fabric.py:3702–3710`).
- It does **not** validate source sameness — no lineage/revision/fingerprint check (none exists; P2.5 zero-match).
- Admitted deep echoes flow into ordinary query assembly (`fabric.py:3933, 3943`) and can reach model cognition after rescore.
- **FILTER-A is orthogonal**: `filter_llm_facing` filters governance visibility (`non_shareable`) and fails loud on raw non-authoritative *wrapper* objects, but the echo flows as a plain enriched dict (the `DeepRetrievalHit` wrapper is built only for the marker block, not flowed downstream — `fabric.py:3696–3699`), so the filter never inspects identity sameness (`governance.py:318–389`; `fabric.py:4320`).
- Therefore **FILTER-A does not close H-1**.

[ROUTING] Later owner: **P4** source-sameness requirement for the echo→source join. No runtime fix authorized.
Evidence: `torment_service/fabric.py`, `torment_service/governance.py`, `torment_service/deep_hits.py`, `torment_service/app.py` (`app.py:2328–2335` aperture deep lane), `tests/test_query_deep_lane_beta.py`.

## 4. Motif-derived identity-anchor path

[FACT]
- Motif membership persists local `member` eids; `_maybe_emit_identity_anchor()` resolves them against the **current** private graph by presence: `agent_member_eids = [int(eid) for eid in (m.members or []) if int(eid) in g.entities]` (`fabric.py:1435`) — presence, not sameness (the same weakness as the deep beta filter).
- It reads the currently resolved members' payloads/summaries (`fabric.py:1444, 1482`).
- It distills those summaries into a **new durable `identity_anchor` memory** (`mtype="identity_anchor"`, `fabric.py:1522`), recording `source_member_eids` (`fabric.py:1544`); emitted from the ingest enrichment path (`fabric.py:3271`).
- Derived identity_anchors are retrievable and participate in scoring/assembly (`retrieval_assembler.py:161, 219`; `scoring.py:188`), so reusable-eid membership can contaminate a later derived cognition artifact even though this is **not** a direct echo-to-prompt join.

[FACT] **Bound (do not overstate):** derived (non-canon) identity_anchors are **excluded from the full continuity / identity-block boost** — `fabric.py:4051–4053` skips non-canon identity_anchors in the continuity-boost pass, and `retrieval_assembler.py:159–161` applies the special identity-anchor shortcut only to *canon* identity_anchors; non-canon anchors fall through to ordinary tier classification, which may still place them in an identity block by tier/half-life. So a reused-eid-contaminated derived anchor reaches cognition as an **ordinary tier-classified memory, not as a privileged canon identity anchor / full-continuity-boosted anchor**, unless and until separately promoted to canon.

[ROUTING] Later owner: a **narrow P4 source-membership obligation** for derived identity-anchor emission (presence → membership-sameness); downstream durability mechanics remain **P6**. No motif redesign authorized.
Evidence: `torment_service/motifs.py`, `torment_service/fabric.py` (`:1382, 1435, 1522, 1544, 3271, 4051`), `torment_service/retrieval_assembler.py` (`:161, 219`).

## 5. Stored node-edge result

[FACT] Stored node→node edges are initialized, loaded, and appended (`memory_graph.py:254, 595, 766`); a service-wide search found **no cognition or governance reader** of stored `self.edges`. Bridges operate on domains, not node eids (`fabric.py:3591–3612`). Trace-export edges are rebuilt fresh as string-keyed viz edges (`fabric.py:6773–6806`).

[FACT] Current reassociation risk is **latent only** (no reader to corrupt).

[ROUTING] Exclude stored-edge repair and attribution mechanics from P4; route future repair/durability to **P5a/P6**.
[ANTI-DRIFT] Before any future cognition-facing stored-edge reader lands, edge attribution / source-sameness must land first.

## 6. Durable source-eid trails

[FACT, recorded conservatively]
- Spirit-reflection persists `source_eid` (`spirit_reflection.py:66, 305, 330`); its summary is **derived event prose, not copied source content** (`:299–303, 319`).
- No current live source-content re-resolution into cognition was proven for spirit-reflection.
- A cooldown/dedup collision risk under eid reuse remains a **derived** concern (`spirit_reflection.py:276–278, 344`).
- Collective packets/events also carry source-eid-like trails (`collective_models.py`; `fabric.py:3164–3197`).
- Do **not** describe spirit-reflection as the unique "second trail."

[ROUTING] Later owner: **P4** light read-confirmation where model-facing re-entry is plausible; **P5a/P6** for repair or durability mechanics.

## 7. Diagnostic-intent versus cognition-capability gap

[FACT] The raw deep-memory query endpoint returns raw deep records directly (`app.py:2218–2233`), bypassing beta source-presence filtering, authority-status shaping, FILTER-A, and assembled projection. Its intent is diagnostic/research; its output remains **structurally cognition-reenterable by caller action**.

[ANTI-DRIFT] diagnostic intent ≠ guaranteed non-reentry.
Related caller-visible / diagnostic surfaces (trace inputs): raw deep-memory query · trace/explain (`fabric.py:6639–6660`) · provenance/debug · collective context/status · orphan listing (`fabric.py:3790+`).
[ROUTING] Later owner: a narrow **P4** intent-versus-capability fencing contract. No mechanism designed here.

## 8. Projection and field-surfacing result

[FACT]
- Query hit construction spreads full payload fields (`memory_graph.py:405–417`, `**payload`).
- `/agent/query` (`app.py:907, 966`) and MCP `torment_query_memory` (`mcp_server.py:512–547`) inherit future payload-resident identity fields automatically unless deliberately projected (both apply FILTER-A governance but not field-shaping).
- `/retrieve` uses a narrower shaped projection (`assembled_text`/`blocks` + ten-field `character_context`, `app.py:1465–1484`; raw internal dict explicitly not exposed).
- Trace does **not** arbitrarily spread full payload — it uses an explicit projection set (`fabric.py:6639–6660`) — but still needs a future-field policy, because fields may be deliberately projected or nested within already-projected envelopes.

[RISK] Future identity-resident fields (era_ref, lineage id, revision id, fingerprint) must not silently become prompt-visible merely because they reside in storage (P2 §12 adjacency).

Existing tiers:
```
assembled_text / blocks:        shaped model-visible prompt surface
/retrieve structured projection: selected caller-visible context
/agent/query and MCP query:      FILTER-A-filtered but wider full-payload caller-visible results
trace / raw deep / provenance / debug / collective status: diagnostic or caller-visible surfaces
assembly_audit:                  opt-in observability
```
[ROUTING] Later owner: **P4** field-surfacing contract.

## 9. Probe verdict

[FACT/ROUTING] No executable probe is justified before P4. The factual reader map is sufficiently answered by read-only archaeology. A later disposable probe may become useful only after P4 frames the requirement — to validate threading of source-sameness evidence through deep export and beta filtering (and, by extension, motif member resolution). No probe authorized now.

## 10. Smallest later P4 boundary (ROUTING only)

[ROUTING] P4 should later frame:
```
DeepMemoryEcho source-sameness requirement
motif-member source-membership requirement for derived identity-anchor emission
raw diagnostic endpoint intent-versus-capability fence
field-surfacing tiers across: /retrieve · /agent/query · MCP query · trace · audit · raw deep · provenance/debug · collective status
orphan observability
light spirit-reflection model-facing re-entry confirmation
```
Explicit P4 exclusions:
```
motif redesign · stored-edge repair and attribution mechanics · identity-token selection ·
fingerprint algorithm · canonical serialization · allocator persistence · IntegrityManifest mechanics ·
TORMENT-specific substrate mechanics · migration execution · broad Class-D ledger classification ·
disclosure-channel values-layer default · runtime patching
```

## 11. TORMENT-specific substrate anti-drift guard

[ANTI-DRIFT] Future storage work is **TORMENT-specific governed memory substrate design**, not generic database-product selection. The current JSONL-canonical + SQLite-derived-sidecar substrate is scaffolding for the doctrine, archaeology, and testing stage. SQLite is non-authoritative, optional, deletable, and rebuildable. Generic database products may appear only as derived sidecars, implementation components, or benchmark references. Do not frame the future phase as generic database-product selection. The controlling direction remains: **TORMENT-governed memory first, database second.** This is not new architecture — it is a pointer to the existing roadmap concern and Cluster 5 doctrine. See `docs/TORMENT_ROADMAP_NOTES.md` (future storage concern section) and `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md` §3.1–§3.2.

## 12. Hard non-decisions

[NON-DECISION]
```
no implementation · no patch · no tests · no executable probe · no P4 opening ·
no carrier designed · no identity-token technology selected · no fingerprint algorithm selected ·
no serialization mechanics selected · no allocator mechanics selected · no manifest mechanics selected ·
no TORMENT-specific substrate mechanics selected · no generic database promoted · no migration authorized ·
no edge repair designed · no motif redesign · no diagnostic-fence mechanism designed ·
no disclosure-channel semantics drafted
```

---
*End Pre-P4 Reader-Dependency Trace v0.1. Evidence and routing only; no implementation authority; P4 unopened and unselected.*
