# TORMENT Memory Engine — P2.5 Cross-Contract Reconciliation v0.1

**Status:** TRACKED RECONCILIATION ARTIFACT — records inspected conformance findings and later-owner routing only. Authorizes no implementation, selects no mechanics, opens no adjacent gate, closes no gate. Date: 2026-06-07.
**Gate:** P2.5 — P1/P2 Cross-Contract Reconciliation and Write-Site Conformance Review (bounded read-only; opened 2026-06-07, remains open).
**Anti-drift reference:** `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md` (as amended 2026-06-07; N1 P1 closure, N2 P2 closure).
**Contracts reconciled:** P1 (`...P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md`) · P2 (`...P2_FAMILY_IDENTITY_ERA_ATTRIBUTION_CONTRACT_v0.1.md`).
**Evidence base:** the read-only P2.5 writer-first reconciliation report (2026-06-07, post-Codex revision); this artifact is its bounded doctrine-shaped distillate, not the full archaeology transcript.
**Tagging:** [FACT] · [RISK] · [QUESTION] · [PARKED] · [NON-DECISION] · [RECOMMENDATION].

---

## 1. Scope and posture

P2.5 is a **bounded reconciliation gate**. This artifact records inspected conformance findings and later-owner routing only. It authorizes no implementation. It selects no mechanics. It opens no adjacent gate. It does not close P2.5, amend the registry, or modify the orientation map — those, if pursued, are separate slices under their own discipline.

## 2. Corrected headline

[FACT]

> Canonical P1/P2 carrier field vocabulary was absent across the inspected current `torment_service` code surfaces.
>
> Several durable families contain semantic identity analogues.
>
> None of those analogues is automatically proven contract-conformant.
>
> Analogue ≠ canonical carrier.

The inherited "memory-lineage identity has no carrier" gap is confirmed and contextualized: it is one instance within a broader absence of *canonical* carrier vocabulary, alongside families that do carry identity *analogues* of varying scope and stability. (Deliberately not stated as "substrate-wide" or "all carriers absent everywhere" — the claim is bounded to the inspected code surfaces.)

## 3. Canonical vocabulary searched

[FACT] A repo-wide search across the inspected `torment_service/*.py` surfaces for the following canonical carrier tokens returned **zero matches**:

```
era_ref · era_id · lineage_id · revision_id · memory_lineage · record_revision · revision_fingerprint · fingerprint
```

[FACT] No EraEvent ledger, IntegrityManifest, or Genesis Baseline artifact was found in the inspected code surfaces. This is the expected state: P1 and P2 ratified the vocabulary; they did not instantiate it.

## 4. Compact family classification

Families group into six provisional classes. This is a routing classification, not a single conformance matrix; operational/derived/checkpoint families are **not** pulled into the primary carrier table.

- **A. Primary memory families** — MemoryNode; SeedRecord.
- **B. Edge and linkage families** — edges; bridges.
- **C. Source-evidence families** — DeepMemoryEcho; compression/spirit-return derived outputs.
- **D. Operational and audit ledgers** — governance audit log, memory/feedback/motif/baton/conflict/reference/environment/proposal ledgers, incident log.
- **E. Derived substrate and migration artifacts** — SQLite sidecar; embedding manifest/shards/map; compression/trajectory/daily logs; migration cursor + review queue.
- **F. Checkpoint and state artifacts** — checkpoints; identity / character-state / roles / symbol / anchor / workspace-meta point-states.

**Obligation-routing table.** P2-carrier treatment status per class: **required / likely / unclear / not established.** ER=era_ref · ML=lineage identity · RR=revision identity · FP=revision fingerprint · SE=source-evidence.

| Class / family | Carrier treatment | Canonical P1/P2 carriers today | Note |
|---|---|---|---|
| A. MemoryNode | **required** | ER/ML/RR/FP absent | core family; local handle = eid; adjacent content-derived prior art = embedding_checksum (§5; neither identity analogue nor P2 carrier) |
| A. SeedRecord | **likely** | absent; analogue = `seed_id` | import-collision visibility motivates treatment |
| B. Edges | **likely** | absent (endpoint-only linkage) | own-assertion per P2 §8; pending §6 reassociation decision |
| B. Bridges | **unclear** | requires later bounded classification trace | linkage vs operational event not yet distinguished |
| C. DeepMemoryEcho | **required** (source-evidence, P2 §5) | SE absent (source eid only) | presence-only join is the H-1 surface |
| C. Compression / spirit-return outputs | **unclear** | requires later bounded classification trace | durable vs derived-diagnostic not yet split |
| D. Operational/audit ledgers | **not established** | uuid/append-order analogues vary | candidate audit evidence *outside* the carrier table (Q-3); requires later bounded classification trace |
| E. Derived substrate / migration | **not established** | n/a (re-derivable) | re-derive attribution; P6/P9-owned |
| F. Checkpoints / state | **unclear** | absent | P3-adjacent; identity/character-state writers require later bounded classification trace; overlaps parked atomic-save item |

Families with identity analogues include collision-resistant UUID-shaped ids in collective packets, closures, and several ledgers; operator-scoped seed ids; and time-embedded archive doc/chunk ids.

These are recorded as analogue-present, conformance-not-proven. None is promoted here.

## 5. embedding_checksum anti-drift safeguard

[FACT] [RECOMMENDATION — resolves Q-1]

> `embedding_checksum` is adjacent content-derived prior art only.
>
> It is **not** a P2 revision-fingerprint carrier.
>
> It must **not** be silently promoted into that role.

Reasons preserved:

- **Mis-scoped:** binds `summary` + embedder identity only (`embedding_checksum(summary, provider, model)`, sha256), not the immutable authored meaning of the revision (type, governance flags, affect, provenance, …).
- **Mutable:** re-stamped in place on staleness (object-level refresh).
- **Therefore:** not an immutable authored-revision binding, which is what a P2 revision fingerprint must be (P2 §6).

[PARKED → P6] P6 owns the future relationship, if any, between `embedding_checksum` and revision-fingerprint mechanics. No replacement is implied or authorized here. Its existence is recorded as feasibility evidence (content-derived in-payload checkable artifacts are practical in this substrate) and as a cautionary object-vs-record example.

## 6. eid concern classification

Distinct concerns, separately named [FACT except where marked]:

- **Allocator reconstruction from `max_eid + 1`** — allocator-state survivability weakness; *enables* handle reuse after trailing-row loss; **not itself a durable-sameness overload**. (Registry C20; P6/durability-adjacent.)
- **DeepMemoryEcho borrowed eid + presence-only validation** — **confirmed durable-sameness overload**; the H-1 revival surface.
- **Migration cursor eid ordinal** — derived-substrate migration hazard; monotonic only absent tail-loss. (P9-input.)
- **Edge `src`/`tgt` eid** — correct local linkage today; future reassociation risk after reuse; **no current reader harm proven** (no trace).
- **`update_payload` same-eid re-append** — lineage gap; **suspected overload only**; a reader trace is required before any stronger claim. [RISK]

## 7. Later-owner routing

Only already-supported routing is recorded; no new owner is invented, and no gate is opened.

- **Later family-specific slices** — write-site stamping, *after* carrier design. Each separately ratified.
- **P4** — reader and projection enforcement; echo evidence-based joins; diagnostic fencing; orphan observability; the reader-dependency trace (Q-4).
- **P5a** — recovery and reconciliation; clone reconciliation; quarantine; edge repair.
- **P6** — identity-token mechanics; allocator-state persistence; revision-fingerprint mechanics; canonical serialization; IntegrityManifest mechanics; durability mechanics; the relationship, if any, to `embedding_checksum`. P6 ownership is not broadened over every diagnostic or derived log. Those remain provisionally classified unless a later bounded trace establishes a specific obligation.
- **P9** — migration execution; cursor-semantics transition (eid-ordinal → revision identity).

## 8. Questions

**Parked** (answering outside the owning step is drift):

- **Q-2** [PARKED] — Are closures' `closure_id` / `version_id` semantics merely prior art, or a later reference shape for lineage/revision vocabulary?
- **Q-3** [PARKED] — Which operational ledgers (class D) are directly P2-governed records, and which are audit evidence outside the primary carrier table?
- **Q-4** [PARKED → P4] — Does any reader beyond DeepMemoryEcho rely on eid sameness across reload for cognition or governance behavior?

**Resolved as anti-drift posture:**

- **Q-1** [RECOMMENDATION — resolved] — `embedding_checksum` must explicitly be recorded as **do-not-promote-to-P2-revision-fingerprint** (§5).

## 9. Hard non-decisions

[NON-DECISION]

```
no carrier designed
no analogue promoted
no fingerprint algorithm selected
no identity-token technology selected
no serialization mechanics selected
no allocator mechanics selected
no manifest mechanics selected
no storage product selected
no migration authorized
no H-1 patch authorized
no adjacent gate opened
```

This artifact records; it does not rule. P2.5 remains open for reconciliation only; any registry amendment or orientation-map update recording this artifact is a separate, separately-authorized docs slice.

---
*End P2.5 Cross-Contract Reconciliation v0.1. Tracked reconciliation artifact; reconciliation findings and routing only; no implementation authority.*
