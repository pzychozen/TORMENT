# Cluster 5 v0.1 — Storage / Survivability Doctrine
**Status:** RATIFIED ADVISORY DOCTRINE — 2026-05-21
**Authority:** Advisory doctrine only. No implementation authorized by this document.
**Date:** 2026-05-21
**Author:** Claude (drafted for trio: pzychozen + GPT + Claude); ratified by trio on 2026-05-21.
**Mode:** doctrine-only advisory. No code, no tests, no migrations, no schema changes, no automation, no runtime mechanism authorization.
**Anchor docs:** Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`), Cluster 2 v0.1 (`docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`), Track B v0.1 (`docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`), `docs/MEMORY_DIGESTION_DOCTRINE_v0.1.md`.

**Lineage to this ratification:**
1. 2026-05-09 brainstorm Cluster 5 (`scratch/brainstorming/memory_roadmap_2026_05_09/06_cluster_5_storage_and_survivability.md`) — surfaced the anchor sentence and proposed a mechanism list.
2. 2026-05-21 Cluster 5 storage/survivability audit (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_AUDIT_2026_05_21.md`) — read-only audit of substrate code reality.
3. 2026-05-21 Cluster 5 v0.1 scratch framing draft (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1_DRAFT_2026_05_21.md`) — first framing attempt, preserved unchanged for lineage.
4. 2026-05-21 v0.1 vs audit review notes (`scratch/CLUSTER_5_V0.1_VS_AUDIT_REVIEW_NOTES_2026_05_21.md`) — three precision fixes recommended.
5. 2026-05-21 Cluster 5 v0.1.1 scratch polish (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.1_DRAFT_2026_05_21.md`) — three fixes applied, preserved unchanged for lineage.
6. 2026-05-21 promotion to this document — ratified by trio.

**Posture:** Cluster 5 v0.1 is **advisory doctrine** that names what storage must preserve, what storage substrate currently exists in code, and what fragilities are known to live in that substrate today. It is doctrine-only. It does not authorize patches, schema changes, journal mechanisms, checksum systems, or verify CLI implementations. Subsequent versions (Cluster 5 v0.2 or a parallel implementation track) may specialize the runtime mechanisms; v0.1's job is to name the invariants and the seams.

---

## Tone discipline (read this before reading the rest)

This doctrine talks about a real engineering substrate that exists in the repo today, and about engineering mechanisms that have been described in the brainstorm but **have not been built**. The tone discipline for this doctrine is to keep those two categories visibly separated at every step.

- When this doctrine names a property of current TORMENT storage, that property is verified against code reality in the 2026-05-21 audit (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_AUDIT_2026_05_21.md`). The audit is the source.
- When this doctrine names a *required guarantee*, that guarantee is doctrinal — it says what storage MUST preserve to honor Track A / Cluster 2 / Track B governance, not what storage HAS already implemented to preserve it.
- When this doctrine refers to brainstorm mechanism proposals (memory manifest layer, BLAKE3 checksums, `torment memory verify` CLI, WRITE_START / WRITE_DONE journal, DuckDB sidecar, etc.), the doctrine treats them as **not built** and as **out of scope for v0.1**. Naming a mechanism in §6 below does not authorize building it.
- The doctrine does NOT use the phrase "manifest layer exists" or "verify CLI is part of TORMENT" or anything similar. The doctrine uses "the brainstorm proposed an X; X is not built; X is deferred."
- The doctrine does NOT auto-promote audit-level findings to mandates. Fragilities named in §5 are *known substrate risks*, not v0.1 mandate-to-fix items. Some may become v0.2 implementation-track items; that is a future trio decision, not a v0.1 doctrine commitment.

This is the same discipline Cluster 2 v0.1 used to keep its doctrine-only posture honest about the runtime gate it deferred.

---

## §0 — TL;DR

Cluster 5 v0.1 names a single load-bearing anchor — *a TORMENT memory is not recovered unless its governance meaning is recovered* — and then specifies six things around it:

1. The vocabulary of storage tiers (canonical / derived / ephemeral / sub-types).
2. The code reality those tiers describe today (JSONL canonical, SQLite sidecar non-authoritative + rebuildable, embedding shards with manifest, mixed atomic-write discipline on point-state files).
3. The storage-governance invariant: governance meaning is part of what "memory" means, and storage doesn't get credit for preserving a memory unless it preserves the governance meaning attached to it.
4. The known substrate fragilities (named operationally, not as v0.1 mandates).
5. The honest line between brainstorm doctrine anchor (accepted) and brainstorm mechanism list (not built; deferred).
6. The storage guarantees that must exist before downstream goals — automation, offline reflection, runtime contest ledger, runtime Authority Gate — can be safely authorized.

Cluster 5 v0.1 is doctrine-only with a named implementation seam, mirroring Cluster 2 v0.1 → Cluster 2 v0.2 and Track B v0.1 → Track B v0.2.

---

## §1 — Center question

How does TORMENT preserve memory meaning, authority, provenance, and governance — across restart, crash, rebuild, sidecar drift, and migration — so that what comes back from disk is the same thing that was assigned by the governance layers above?

This question is downstream of three already-ratified doctrines:

- **Track A v0.1** says a TORMENT agent does not merely say true things — it says *what kind of truth they are, how sure it is, and how much authority that memory should have now*. Storage must carry Mode / Voice / Certainty / Authority across restart.
- **Cluster 2 v0.1** decomposes Authority into Authority class / Lifecycle / Promotion rights and adds two top-level axes Scope and Lane. Storage must carry those across restart.
- **Track B v0.1** specifies the disagreement runtime doctrine: ContestRecord, contest ledger (Option C), audit-visibility invariant (Invariant 14), self-issued contests cannot route to refuse (Invariant 16). Storage must, when the contest ledger is implemented, carry contest records *durably enough that contest cannot become a hiding mechanism*.

Cluster 5's job is to name the substrate constraints those three doctrines place on storage, so that future implementation tracks (Cluster 2 v0.2, Track B v0.2, Cluster 4, autonomous tool use) inherit a consistent storage contract.

---

## §2 — Canonical / derived / ephemeral vocabulary

Cluster 5 v0.1 ratifies the following vocabulary for storage tiers. This is the language subsequent doctrine and audit work should use. The definitions are operational — they describe how recovery works, not how trust is assigned.

### §2.1 Canonical (source of truth)

A **canonical artifact** is one for which there is no other authoritative copy in the system. If a canonical artifact is lost, the information it carried is irrecoverable (modulo backups outside TORMENT itself). Examples by sub-type:

- **Canonical append-ledger** — append-only JSONL file where the last record per key is canonical (e.g., per-agent `nodes.jsonl` where each line carries an `eid` and last-record-wins reconstructs the memory graph; `closures.jsonl` where each line is a ClosureEntry version; `closure_events.jsonl` where each line is a lifecycle event and current state is derived by latest-event-kind).
- **Canonical event ledger** — append-only JSONL file where every line is a distinct event and order matters (e.g., `memory_events.jsonl`, `governance/audit.jsonl`, `feedback_events.jsonl`, `baton_events.jsonl`, `reference_load_events.jsonl`, `conflict_events.jsonl`, `motif_events.jsonl`, `bridge_events.jsonl`, collective `packets.jsonl` and `events.jsonl`).
- **Canonical point-state** — a single JSON file whose current contents are the latest state (e.g., `identity.json`, `character_seed_*.json`, `character_state.json`, `roles.json`, `symbol_state.json`, `anchor_state.json`, `workspace_meta.json`, `domains.json`, `domain_policies.json`, embedding `manifest.json`, motifs `motifs.json`).
- **Canonical snapshot** — a single JSON file that captures the state of multiple in-memory objects at a step (e.g., per-agent `checkpoints/<step>.json` carrying model_state + corridor_monitor + character_state + motif_summary + shard_snapshot).
- **Canonical binary** — a single binary file that holds float vectors directly (e.g., embedding `shard_*.npy`).
- **Canonical row-map** — a JSONL file that records what each row of a binary shard means (e.g., `shard_*.map.jsonl`). The shard binary plus its map JSONL together form one canonical artifact.

The defining property of canonical: deletion is loss.

### §2.2 Derived (rebuildable sidecar)

A **derived artifact** is one whose contents can be reconstructed from canonical sources without information loss. If a derived artifact is deleted, the system continues to operate and can rebuild on demand.

Examples by sub-type:

- **Derived index** — `memory_index.sqlite` (header docstring: "*A mirror of canonical JSONL/NPY data (never authoritative). Deletable and rebuildable at any time. Optional — the engine runs fine without it.*"). `rebuild_from_jsonl` exists.
- **Derived column** — within a derived index, a column whose value is computed from canonical fields (e.g., `core_nodes.provenance_type` is derived from raw ProvenanceV1 via `derive_provenance_type`).
- **Derived in-memory state** — runtime objects rebuilt from canonical on load (`MemoryGraph.entities`, `MemoryGraph._emb_by_eid`, `MemoryGraph._emb_mat`, `world.entities`).
- **Derived diagnostic log** — append-only files that record derived computations and are deletable without governance loss (`compression_log.jsonl`, dated logs under `logs/<category>/daily/`).

The defining property of derived: deletion is recoverable.

### §2.3 Ephemeral (runtime-only, lost on restart by design)

An **ephemeral artifact** is one that intentionally does not persist across restart. Loss is expected on every restart and is not a fault condition.

Examples:

- **Bounded ring buffer** — `IncidentLog` (default 500 entries; optional opt-in `spine_incidents.jsonl` append mode).
- **Per-step computation** — half-life "current effective strength" is recomputed at retrieval from `created_ts` + `half_life` + optional `last_reinforced_ts`; the *policy* persists in payload, the *current value* does not.
- **Session state** — recursion-guard state, tri-modulation per-step state, cognition `ReintegrationResult.dissent` (per Track A §9.6 and Track B v0.1 Invariant 15: cognition dissent does not auto-trigger contest and is not persisted as a memory).

The defining property of ephemeral: persistence is not part of the contract.

### §2.4 Cross-tier sub-vocabulary

Two additional terms are useful when discussing canonical artifacts:

- **Atomic-saved** — a canonical artifact whose entire-file rewrite uses tmp + `os.replace` so it is never observed half-written.
- **Append-discipline** — a canonical append-ledger whose writers append complete records (full JSON line + trailing newline) without modifying earlier records.

Cluster 5 v0.1 does not require either atomic-save or append-discipline at the doctrine level for v0.1 (see §5 known fragilities — those discipline gaps exist today). The vocabulary exists so future doctrine and audit work can talk about them precisely.

---

## §3 — Current code reality (descriptive, not aspirational)

The following describes TORMENT storage **as it actually exists in code at 2026-05-21**, per the audit. This section is descriptive. It is not an implementation mandate and it is not a sales pitch — it is a snapshot.

### §3.1 JSONL is canonical at every memory-bearing layer

The per-agent memory graph (`nodes.jsonl`), the event ledgers (`memory_events.jsonl`, `governance/audit.jsonl`, `closure_events.jsonl`, `feedback_events.jsonl`, etc.), the closure store (`closures.jsonl`), the environment memory (`environment.jsonl`), the reference memory (`references.jsonl`), the conflict registry (`conflicts.jsonl`), and the embedding row-maps (`shard_*.map.jsonl`) are all JSONL. The `MemoryGraph._load` method reads `nodes.jsonl` at startup and reconstructs entities via last-record-per-eid semantics.

The JSONL file header comment at `memory_graph.py:387` and `:639` makes the canonicality explicit: "*Canonical write (JSONL first — always)*."

### §3.2 SQLite is sidecar, explicitly non-authoritative, rebuildable

The `memory_index.sqlite` file (with WAL + synchronous=NORMAL) is a fast-metadata-lookup mirror of the canonical JSONL/NPY data. The module header at `sqlite_index.py:5-16` states the design rule literally: "*SQLite should help the system, not define it. ... A mirror of canonical JSONL/NPY data (never authoritative). Deletable and rebuildable at any time. Optional — the engine runs fine without it.*" The `rebuild_from_jsonl` method (`sqlite_index.py:496-626`) is robust to corrupt input lines (try/except per line) and uses `INSERT OR REPLACE` so re-indexing is idempotent. An HTTP rebuild endpoint exists at `app.py:1477-1500`.

### §3.3 Embedding shards have their own manifest, atomic save

The embedding shard storage layer (`embedding_store.py`) uses a separate `manifest.json` per shard directory that is atomically saved (tmp + `os.replace`). Shards are `.npy` files; rows are written via `np.memmap(mode="r+")`. Row-level metadata lives in companion `shard_*.map.jsonl` files. A legacy per-EID `emb_<eid>.npy` format is still supported via fallback.

### §3.4 Some point-state files are atomic-saved, some are not

The atomic-save pattern (tmp + `os.replace`) is used in:
- `_save_symbol_state` (`fabric.py:317-326`)
- `_save_anchor_state` (`fabric.py:281-290`)
- `save_checkpoint` (`checkpoint.py:323-328`)
- `EmbeddingShardWriter._write_json` (`embedding_store.py:154-161`)
- Promotion writes (`promotion.py:102`)
- Nodes.jsonl compaction during repair/clone (`fabric.py:1226-1230`, `:1903-1908`)

The non-atomic raw `open("w") + json.dump` pattern is used in:
- `IdentityStore.save` (`identity.py:77-82`)
- `CharacterStore.save_seed` (`character.py:218-222`)
- `CharacterStore.save_state` (`character.py:239-244`)
- `RoleStore.save` (`roles.py:99-104`)

Cluster 5 v0.1 records this asymmetry without authorizing a fix. The asymmetry is doctrinally relevant because it touches identity / character storage — the artifacts whose loss most directly damages an agent.

### §3.5 Governance meaning is stored *inside payloads*, not as separate columns

Governance flags (canon, canon_locked, protected, scratch, released, review-pending), provenance (`source_type`, `write_path`, `character_*`, `source_role`, `tool_name`, etc.), and authority composition (Cluster 2 v0.1 sub-dimensions: authority class, lifecycle, promotion rights) are all stored as fields inside each node's payload dict in `nodes.jsonl`. They survive restart because the payload survives restart. They do not have a separate "governance file" sibling.

This is the substrate fact that the brainstorm's anchor sentence — *a TORMENT memory is not recovered unless its governance meaning is recovered* — is making operational. Governance meaning is part of the node, not a separate file that could be lost independently.

(For storage-status precision on which authority sub-dimensions are literal payload fields vs composed-from-fields vs doctrine classifications, see §4.2 below.)

### §3.6 What is NOT in the current storage substrate

Doctrine-relevant absences (each was a brainstorm proposal):

- No memory-level manifest file (manifest exists only at embedding-shard level).
- No BLAKE3 / Merkle / checksum integrity system.
- No `torment memory verify` CLI.
- No WRITE_START / WRITE_DONE two-phase journal.
- No DuckDB analysis sidecar.
- No tiered hot / warm / cold / archive storage system (the `memory_class="core"` vs `"archive"` distinction exists and `deep_memory.py` writes compressed `memories.jsonl`, but this is not the full tier system the brainstorm sketched).
- No "user has seen this" visibility tracking field.
- No visibility-tier (immediate / batched / ephemeral) flag.
- No multi-process write coordination on shared collective state.

Cluster 5 v0.1 acknowledges these absences honestly. It does NOT propose to build any of them in v0.1.

---

## §4 — The storage-governance invariant

### §4.1 The anchor sentence

> *A TORMENT memory is not recovered unless its governance meaning is recovered.*

This sentence was surfaced as a load-bearing principle by the 2026-05-09 brainstorm (see brainstorm `99_session_summary.md` framing-doc-grade sentence #8). Cluster 5 v0.1 ratifies it as doctrine.

### §4.2 What "governance meaning" includes

For the purpose of this doctrine, **governance meaning** is the set of fields that must be preserved on a memory for that memory to count as "recovered" rather than "merely re-read." A memory recovered from disk without its governance meaning is a memory that has been *demoted* by recovery — even if the summary text is identical.

**Storage-status legend.** Each item below is tagged with how it lives in storage today, so the doctrine does not accidentally imply every governance dimension is a literal stored field. The tags are:

- **[stored]** — a literal payload or provenance field with a known name (e.g., `payload["provenance"]["source_type"]`).
- **[composed]** — a value derived from multiple stored fields, file location, or payload context. Not a single stored field.
- **[doctrine]** — a classification fixed by an upstream doctrine (Track A / Cluster 2 / Track B), not a field on the row.
- **[future]** — will become stored when a future track lands; not stored today.
- **[derivable]** — recoverable by scanning canonical ledgers; no direct back-link field on the node row.

Governance meaning currently includes (the list is open — Cluster 3 / Cluster 4 will extend it):

- **ProvenanceV1** **[stored]** (Track A v0.1 §3): `source_type`, `write_path`, `source_role`, `tool_name`, `session_id`, `created_at_step`, `parent_eids`, character context fields (`character_id`, `character_name`, `character_scope`), admission outcome (`admission_refused`, `reason`, `policy_version`). All are literal fields in the payload's `provenance` dict.
- **Authority class** **[doctrine + composed]** (Cluster 2 v0.1 §7): the four-value labeling (`persist` / `low-authority` / `released` / `refuse / no-persist`) is a **doctrine classification**. It is **composed** from multiple stored fields — canon, canon_locked, protected, scratch, released, write_path, half_life value — not a single `authority_class` column. There is no row in storage whose value literally says "authority_class = low-authority"; rather, the combination of underlying stored fields is interpreted as one of the four values per Cluster 2 v0.1's vocabulary.
- **Lifecycle** **[mixed: stored + doctrine]** (Cluster 2 v0.1 §7): some sub-states are **[stored]** (`scratch` flag, `protected` flag, `released` flag, `half_life` value, defaults for `tool_result` per Cluster 2 v0.1 §11.3). The composite five-value lifecycle label (`decay-bounded` / `scratch-bounded` / `protected` / `terminal` / `ratified`) is a **doctrine classification** per Cluster 2 v0.1 §7, derived from those stored sub-states and from contextual rules.
- **Promotion rights** **[doctrine]** (Cluster 2 v0.1 §7): not a stored field. Describes who is *allowed* to promote a memory (to canon, to ratified, etc.) and under what conditions. Lives entirely as a doctrine classification — no row in storage carries a `promotion_rights` value.
- **Lane** **[stored]** (Cluster 2 v0.1 axis B): which write path created the memory. Stored as `write_path` in ProvenanceV1.
- **Scope** **[composed]** (Cluster 2 v0.1 axis A): private / collective / character-basin. Expressed via *where* the node lives (per-agent `private/` directory vs collective field membership vs character basin attachment) plus payload context. Not a single stored `scope` field.
- **Voice provenance** **[stored + doctrine]** (Track A v0.1 §3.2 / Track B v0.1 §2.6): `character_id`, `character_name`, `character_scope` are **[stored]** fields in ProvenanceV1 — they record which character voice was active at write time. Whether the memory entered the character basin as canon/continuity/identity weight is **[doctrine]** per Track B v0.1 §2.6 character refusal: a memory may exist in the agent's memory graph but doctrine-classify as not having entered the basin.
- **Governance flags** **[stored]** (existing payload fields): `canon`, `canon_locked`, `protected`, `scratch`, `released`, `review-pending`. Each is a literal payload field. Semantics fixed by the existing codebase and by the audits.
- **Contest links** **[future]** (when Track B v0.2 implements the contest ledger): the link from a node to ContestRecord(s) referencing it, and the reverse link from a ContestRecord to its target node. Not stored today. Per Track B v0.1 Invariant 14, when implemented, contest records must be at least as durable as the memories they contest — recovery that drops contest is recovery that has lost governance meaning.
- **Audit-trail link** **[derivable]** (when relevant): the row(s) in `governance/audit.jsonl` that name this eid as a subject of governance changes. No back-link field on the node row; recoverable by scanning the audit ledger for the eid.

**Why this matters.** The list above is the criterion future implementation tracks must satisfy. The legend prevents the doctrine from accidentally implying that authority class, lifecycle, scope, promotion rights, or basin-entry status are single stored columns. They are not. They are governance meanings that LIVE in stored fields, composed values, file location, and doctrine classifications — together. Storage must preserve all of those layers, not just the payload fields.

### §4.3 The invariant, stated formally

For every canonical memory `m` and every governance field `g ∈ governance_meaning(m)`:

> If `m` is recoverable from canonical storage, then `g(m)` is recoverable from canonical storage with the same value it had at write time (or with the most recent value it had at a subsequent committed write).

Or, contrapositively: if a governance field cannot be recovered, the memory is not recovered — even if its content text is.

This applies to every entry in §4.2 — `[stored]` items must recover from their named payload field; `[composed]` items must recover with the same composition rule applied to the same recovered inputs; `[doctrine]` items must recover with the same classification rule applied; `[future]` items become covered when the relevant future track lands; `[derivable]` items must be discoverable by the same scan over the same recovered canonical ledger.

### §4.4 What the invariant implies about substrate

The invariant is doctrine-only. It does NOT immediately mandate:

- A specific atomic-write discipline.
- A specific journal format.
- A specific checksum algorithm.
- A specific verification mechanism.

It DOES name the criterion future implementation choices must satisfy. If a future change makes some governance field non-recoverable in some crash scenario, that change has violated Cluster 5 v0.1 — regardless of how performant or otherwise-correct it is.

### §4.5 What the invariant does NOT authorize

The invariant authorizes nothing. It is a criterion, not a command. It does not authorize:

- Schema changes to existing canonical files.
- Migration of existing data.
- A new persistent storage format.
- A new sidecar.
- A new verification daemon.
- Any modification to Track A v0.1, Cluster 2 v0.1, or Track B v0.1.

---

## §5 — Known fragilities

This section names substrate risks that exist in the current code as of 2026-05-21. They are documented here so future doctrine and audit work can reference them by name. They are NOT v0.1 mandate-to-fix items. The trio will decide which become Cluster 5 v0.2 / implementation-track items in a future ratification.

Each fragility carries an operational label (used as a stable name for future cross-reference) and a short statement.

### §5.1 `JSONL-NO-FSYNC`

(Write-side fragility.) Every JSONL append in the codebase follows the same pattern:

```python
with open(safe, "a", encoding="utf-8") as f:
    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
```

Examples: `memory_graph.py:145-148`, `governance.py:380-381`, `closure_ledger.py:135-136`. No `f.flush()`, no `os.fsync(f.fileno())`, no atomic rename, no journal entry. On process crash or OS crash between the Python-level write and the kernel page-cache flush, the trailing N records may be lost; if the crash interrupts the byte sequence mid-line (between writing the JSON payload and the trailing `\n`), the file ends with a partial JSON line on disk.

The fix-target for this fragility lives in `_append_jsonl` and similar producer paths. (The read-side consequence of this fragility — what the loader does with a torn line it encounters — is named separately as `JSONL-LOADER-NOT-FAIL-TOLERANT` in §5.10. The two are causally linked but independently fixable.)

### §5.2 `IDENTITY-NON-ATOMIC-SAVE`

`IdentityStore.save`, `CharacterStore.save_seed`, `CharacterStore.save_state`, and `RoleStore.save` use raw `open("w") + json.dump`. `open(p, "w")` truncates to 0 bytes at open time; a crash between truncate and successful close leaves the file zero-byte or partially written.

The asymmetry with the atomic-save pattern used in sibling code paths (§3.4) makes this a substrate inconsistency, not an architectural decision.

### §5.3 `INGEST-NOT-TRANSACTIONAL`

A single `fabric.ingest()` call writes across multiple files: `nodes.jsonl`, `edges.jsonl`, `memory_events.jsonl`, embedding shard `.npy` + `.map.jsonl`, and SQLite index entries. There is no enclosing journal or transactional wrapper.

The code itself documents this hazard at `fabric.py:2509-2514`: "*failing later at `ws.motif_regs[chosen_domain]` leaves orphan state — a MEMORY_CREATE event in memory_events.jsonl and an embedding shard row — without a matching nodes.jsonl row*." The preflight at `:2515` mitigates the specific unknown-domain case but leaves the structural window for other exceptions in the motif/symbol/resonance enrichment band.

### §5.4 `EMBEDDING-SHARD-MEMMAP-NON-TRANSACTIONAL`

`np.memmap(..., mode="r+")` writes embedding vectors via OS page cache. A crash mid-write can leave a shard with the embedding vector partially flushed while the companion `.map.jsonl` already records a row entry pointing at the half-written vector. On reload, the row's data may be garbage but the loader treats the entry as valid.

### §5.5 `SQLITE-SIDECAR-SILENT-DRIFT`

Mirror-write failures from `_safe_execute` are logged at warning level but do not propagate. Callers swallow the result. Repeated mirror failures cause silent divergence; only an operator-triggered `/index/rebuild` corrects it. No periodic drift-check exists.

This is a low-severity fragility (the sidecar is non-authoritative by design) but it can mislead operators who rely on the sidecar for fast lookups and assume it reflects canonical state.

### §5.6 `EMBEDDING-MANIFEST-SINGLE-COPY`

`embeddings/manifest.json` is atomically saved but exists in exactly one copy. If it is lost outside of normal operation, the shard structure (active_shard, next_row, total_rows, dim) must be reconstructed by scanning every `shard_*.map.jsonl`. A reconstruction function does not currently exist.

### §5.7 `DERIVED-COLUMN-DRIFT`

The `core_nodes.provenance_type` column in the SQLite sidecar is the output of `derive_provenance_type(payload.get("provenance"))` at index time. If the derivation function evolves, old rows carry stale derived values until a rebuild. A `schema_version` marker exists (`sqlite_index.py:170`, currently `4.1`) but no auto-rebuild trigger is wired to bumps.

### §5.8 `NO-MULTI-PROCESS-WRITE-COORDINATION`

JSONL appends rely on OS-level atomic-append semantics for a single short write to a single open file descriptor on POSIX. SQLite has its own WAL+timeout coordination. There is no application-level lock file or coordination protocol if two TORMENT processes simultaneously open the same agent directory.

### §5.9 `TWO-EMBEDDING-FORMATS-COEXIST`

Legacy per-EID `emb_<eid>.npy` files and the modern shard format both exist. Two read paths (shard reader + universal loader) both supported in code. Some agents may straddle both formats. Substrate-level inconsistency, low-severity.

### §5.10 `JSONL-LOADER-NOT-FAIL-TOLERANT`

(Read-side fragility.) The main loader at `memory_graph.py:412-418` does NOT catch `json.JSONDecodeError`:

```python
for line in f:
    if not line.strip():
        continue
    obj = json.loads(line)   # raises on torn line → aborts whole load
```

A single corrupt or torn last line aborts the entire load. The robust try/except-per-line pattern exists in the codebase at `rebuild_from_jsonl` (`sqlite_index.py:530-540`) — it just isn't used in the primary loader.

The fix-target for this fragility lives in `MemoryGraph._load` and similar consumer paths. It is causally linked to `JSONL-NO-FSYNC` in §5.1 (the write-side fragility is what produces the torn lines that the loader can't tolerate), but the two are independently fixable: `_load` can be hardened without changing the writers (skip-and-warn on JSONDecodeError, matching `rebuild_from_jsonl`), and the writers can `fsync` without changing the loader. Separate handles let future trio discussions reference each precisely.

---

### §5 framing note

Naming a fragility in this section is **not** authorization to fix it. Some of these will become v0.2 items, some will become "intentional substrate constraint, do not change" items, and some will become "to be addressed by a separate audit or implementation track." The doctrine names them so they have stable cross-reference handles (`JSONL-NO-FSYNC`, `JSONL-LOADER-NOT-FAIL-TOLERANT`, `IDENTITY-NON-ATOMIC-SAVE`, etc.) for future trio discussions.

---

## §6 — Brainstorm mismatch (accepted anchor vs unimplemented mechanism list)

This section preserves an honest line between what Cluster 5 v0.1 inherits from the brainstorm (as doctrine) and what it does NOT inherit (because the mechanism does not exist in code).

### §6.1 Accepted brainstorm doctrine anchor

> A TORMENT memory is not recovered unless its governance meaning is recovered.

This sentence (brainstorm `99_session_summary.md` framing-doc-grade sentence #8) is ratified by Cluster 5 v0.1 as the doctrine center (see §4.1). The two reframes that surround it in the brainstorm (`06_cluster_5_storage_and_survivability.md` §"Cluster 5's distinctive shape" and §"The reframe") are also accepted as doctrine substrate:

- *"Storage's job is to not lose what governance assigns."*
- *"Memory-alignment is not just JSON ↔ .npy ↔ SQLite agreement — it's that the restored memory carries the same authority, mode, certainty, subject, visibility, decay state, provenance, and governance meaning it had before crash/compression/restart."*

These reframes are absorbed into §4 of this doctrine (the storage-governance invariant).

### §6.2 Unimplemented brainstorm mechanism list (DEFERRED — out of scope for v0.1)

The brainstorm proposed a list of engineering mechanisms. As of code reality 2026-05-21, these are **not built**. Cluster 5 v0.1 does NOT authorize building any of them. Cluster 5 v0.1 does NOT recommend the order or priority in which they should be built. That belongs to a future implementation track if and when the trio chooses to open one.

The list, named here for stable cross-reference (so future doctrine can say "the BRAINSTORM-MANIFEST-LAYER item from Cluster 5 v0.1 §6.2 is being specified by Cluster 5 v0.2" or similar):

- **BRAINSTORM-MANIFEST-LAYER** — a memory-level manifest proving alignment between eid, payload JSON, embedding vector, motif membership, provenance, tier/canon flags, checksums.
- **BRAINSTORM-VERIFY-CLI** — `torment memory verify`: integrity scanner that checks physical AND governance alignment.
- **BRAINSTORM-REPAIR-CLI** — `torment memory repair --dry-run`: distinguishing physical-recoverable corruption from governance corruption (governance corruption surfaces to operator, never auto-mutates, per Memory Digestion Doctrine v0.1 advisory-only rule).
- **BRAINSTORM-APPEND-JOURNAL** — append-only journal recording WRITE_START → ... → WRITE_DONE pipeline state, allowing crash replay or quarantine.
- **BRAINSTORM-GEOMETRY-COMPRESSION** — geometry-aware compression with motif centroid + compressed residual. (Note: `compression.py` exists in the repo and writes `compression_log.jsonl`. Whether it preserves governance fields uncompressed is **unverified** by the 2026-05-21 audit; that verification is a candidate for the audit's §8.4 deeper-audit option but is not a v0.1 deliverable.)
- **BRAINSTORM-STORAGE-TIERS** — hot / warm / cold / archive tiers fitting half-life/tier logic. (Note: `memory_class="core"` vs `"archive"` and `deep_memory.py` exist but do not constitute a full tier system in the brainstorm's sense.)
- **BRAINSTORM-MOTIF-LOCAL-CACHE** — RAM cache organized by motif cluster rather than LRU.
- **BRAINSTORM-CHECKSUMS** — BLAKE3 + Merkle-style digests for integrity.
- **BRAINSTORM-DUCKDB-SIDECAR** — DuckDB analysis sidecar for audits.
- **BRAINSTORM-STORAGE-BACKEND-EXPERIMENTS** — backend comparison experiments.
- **BRAINSTORM-VISIBILITY-TIER** — per-row visibility flag (immediate / batched / ephemeral).
- **BRAINSTORM-USER-HAS-SEEN** — per-audit-visible-item user-has-seen tracking.
- **BRAINSTORM-15-VERIFY-INVARIANTS** — the specific 15-invariant verify checklist the brainstorm sketched.
- **BRAINSTORM-3-TIER-COLUMNIZATION** — three-tier columnization in storage layer.

### §6.3 Correction of a brainstorm assumption

The brainstorm `06` doc and GPT's storage thread assumed a layout where SQLite was the control plane and JSONL + .npy were the data plane. This is **not** the layout TORMENT has. The session-closure paragraph in `99_session_summary.md` already named this: "*current TORMENT has JSONL canonical with SQLite as non-canonical sidecar, not the SQLite-as-control-plane the 2026-05-09 brainstorm assumed*." Cluster 5 v0.1 ratifies that correction. The mechanism list in §6.2 is named without endorsing the assumption that SQLite should become the control plane.

### §6.4 Tone discipline restated for this section

When future trio work, audit notes, or implementation-track plans reference Cluster 5 v0.1, they should treat §6.1 as inherited doctrine and §6.2 as labeled-deferrals — neither rejected nor authorized. Anyone reading this doctrine to plan implementation MUST consult the 2026-05-21 audit for code reality, not §6.2's labels.

---

## §7 — Pre-automation storage guarantees

### §7.0 Framing — necessary but not sufficient

Each guarantee in §7.1 – §7.6 below is a **necessary precondition** for safely authorizing the downstream goal it names. Meeting these preconditions does **not** itself authorize that goal. Every downstream goal still requires its own doctrine ratification, its own review process, its own implementation plan, and its own explicit trio decision. Storage readiness is a necessary but not sufficient gate. §7.2 makes this explicit for autonomous tool use (which is also blocked per `ROADMAP_v2.4.x.md §3` regardless of storage readiness); the same posture applies to every other goal in this section. Naming a precondition here does not constitute a roadmap commitment, an automation green-light, or a release of any other doctrine's gate.

### §7.1 Before offline reflection (Cluster 4) can be authorized

- **Canonical-append durability for reflection candidates.** Reflection generates candidate records (NOT canon — per the Memory Digestion Doctrine v0.1 advisory rule and the brainstorm Cluster 4 settlement). If those candidates are lost in a `JSONL-NO-FSYNC` window, the reflection cycle produced output that didn't persist. This is a soft fragility (candidates are not canon) but at high reflection rates it becomes load-bearing.
- **Visible separation of reflection-derived from agent-authored.** Reflection outputs must carry provenance distinguishing them from agent-authored memories. Currently the `source_type` taxonomy supports this; the doctrinal commitment is to keep that separation across restart.

### §7.2 Before autonomous tool use can be authorized

- **Write-rate-tolerant durability.** Autonomous tool use multiplies write rate. The current `JSONL-NO-FSYNC` window is acceptable at human conversation rates; it is not acceptable at autonomous-tool-loop rates without either fsync, batch-journal, or rate limiting.
- **`tool_result` lane integrity** (per Cluster 2 v0.1 §11.3): half-life cap (7d), authority class `low-authority`, lifecycle `decay-bounded`, no promotion. These properties must hold across restart for every `tool_result` ingest. They are currently encoded in payload fields and survive via `nodes.jsonl`, but the lane-integrity invariant becomes Cluster-5-shaped if autonomy ever bypasses the existing `tool_result_ingest` path.
- This goal is explicitly blocked per `ROADMAP_v2.4.x.md §3` regardless of storage readiness; storage readiness is a necessary but not sufficient gate.

### §7.3 Before runtime contest ledger (Track B v0.2) can be authorized

- **Atomic-append discipline on the contest ledger.** Per Track B v0.1 Invariant 14, contest INCREASES audit visibility — contests must not be lost in crash windows. The contest ledger (Option C, per Track B v0.1 §5) will be a new append-only JSONL. Inheriting today's `JSONL-NO-FSYNC` fragility for that ledger is a Track B v0.1 invariant violation in waiting.
- **Durable target-link integrity** between ContestRecord and the node it targets. The contest must remain attached to the right eid across restart, rebuild, and rebuild_from_jsonl runs. The link can live in either direction (ContestRecord → eid via `target_eid` field, or eid → ContestRecord via reverse index in SQLite sidecar). The doctrinal requirement is that recovery preserve at least one direction. Per Track B v0.1 §3.2 immutability, the target field itself never changes after write.
- **`refuse / no-persist` audit visibility under operator-scope.** Per Track B v0.1 §7 routing table, operator-scope contests can route to `refuse / no-persist`. The audit-visibility invariant (Invariant 14) requires that the *refusal* be visible in the contest ledger even though the memory itself is not in `nodes.jsonl`. Storage must support a refusal record that points at a never-existed eid (or at a candidate-id distinct from eid).

### §7.4 Before runtime Authority Gate (Cluster 2 v0.2) can be authorized

- **Per-ingest authority-decision durability.** A runtime Authority Gate writes decisions per ingest. Per the storage-governance invariant, those decisions must be either fully durable or absent — half-decisions break audit. Today's `INGEST-NOT-TRANSACTIONAL` fragility creates a window where the decision could be logged without the node being durable.
- **Lane-attribution durability.** Cluster 2 v0.1 axis B (Lane) attributes each memory to a write path. Cluster 2 v0.2 may make Lane a first-class field. Whatever shape Lane takes, it must survive restart.

### §7.5 Before cross-agent hivemind expansion can be authorized

- **Multi-process write coordination** on shared collective state (currently absent — `NO-MULTI-PROCESS-WRITE-COORDINATION`). The collective field code uses single-process assumptions today.
- **Packet-ledger durability** for `packets.jsonl`; collective state is derived from packets.

### §7.6 Before any future Cluster 5 doctrine extension

- **A working understanding of what `compression.py` preserves** (currently unverified — open question from §6.2 BRAINSTORM-GEOMETRY-COMPRESSION).
- **A working understanding of whether released / scratch / protected / review-pending lifecycle markers are durably distinct in payloads** (currently unverified — open question from the audit §8.4 Option C).
- **A working understanding of affect markers' user-confirmation provenance** (currently unverified).

These three are candidates for a "deeper governance-preservation audit" that could precede a Cluster 5 v0.2 framing.

---

## §8 — Non-goals (what Cluster 5 v0.1 does NOT do)

For unambiguity, here is what this doctrine explicitly does not include or authorize:

- **No code changes.** Not in v0.1, not implicit, not by inference.
- **No tests.** Not in v0.1.
- **No storage migrations.** Existing data on disk is untouched.
- **No schema changes.** SQLite schema, JSONL formats, payload schemas — all untouched.
- **No verify CLI implementation.** `BRAINSTORM-VERIFY-CLI` is named-and-deferred only.
- **No journal mechanism implementation.** `BRAINSTORM-APPEND-JOURNAL` is named-and-deferred only.
- **No checksum system.** `BRAINSTORM-CHECKSUMS` is named-and-deferred only.
- **No backend rewrite.** TORMENT continues to use the JSONL-canonical + SQLite-sidecar + .npy-shard layout it uses today.
- **No new sidecar.** No DuckDB, no new index, no new ledger format.
- **No Track A / Cluster 2 / Track B edits.** Those doctrines are unchanged. Their cross-references are inherited, not amended.
- **No Memory Digestion Doctrine edits.** That doctrine remains the philosophical anchor; Cluster 5 v0.1 sits adjacent to it.
- **No automation.** Cluster 5 v0.1 is a precondition for automation discussions, not an automation step.
- **No real LLM/API calls.** This doctrine touches storage substrate, not cognition.
- **No further promotion authorized by this doctrine.** Promoting Cluster 5 v0.1 ratifies the doctrine itself; it does not authorize any downstream mechanism, schema, CLI, or implementation track. Cluster 5 v0.2 (or any sibling implementation track) requires its own separate trio ratification.
- **No fragility-to-mandate auto-promotion.** Naming a fragility in §5 is not authorizing a fix; that requires separate trio decision.
- **No mechanism-from-§6.2 implementation.** Naming a brainstorm mechanism with a stable label is not endorsing or scheduling its implementation.

---

## §9 — Recommendation (and seam for future versions)

### §9.1 Posture of Cluster 5 v0.1

Cluster 5 v0.1 is ratified as **advisory doctrine**, mirroring Track A v0.1 / Cluster 2 v0.1 / Track B v0.1. It names invariants, vocabulary, code reality, fragilities, and seams. It does not change runtime behavior.

### §9.2 Named implementation seam — Cluster 5 v0.2

If and when the trio chooses to open an implementation track, the seam is "Cluster 5 v0.2 — Storage Survivability Mechanisms." Likely scope (this is the seam description, not authorization):

- Decide which §5 fragilities become fix-targets (`JSONL-NO-FSYNC`, `JSONL-LOADER-NOT-FAIL-TOLERANT`, `IDENTITY-NON-ATOMIC-SAVE`, `INGEST-NOT-TRANSACTIONAL` are the most load-bearing per the audit).
- Decide whether to introduce a journal mechanism, an atomic-write helper applied uniformly, or both.
- Decide the shape of governance-preservation verification (CLI? periodic check? on-restart sanity?).
- Coordinate with Track B v0.2 on contest-ledger durability — these are sibling implementation tracks.

### §9.3 Alternative future paths (named, not chosen)

For trio decision in a future session:

- **Path A — Cluster 5 v0.2 directly.** Open the implementation track.
- **Path B — Track B v0.2 first.** Let Track B v0.2 specify the contest-ledger storage shape (atomic-append, rebuild-from-canonical, etc.); use those concrete choices as templates for Cluster 5 v0.2.
- **Path C — Deeper governance-preservation audit first** (per §7.6). Resolve open questions on compression governance-field preservation, lifecycle-marker distinctness, and affect-marker user-confirmation provenance before specifying Cluster 5 v0.2.

Cluster 5 v0.1 itself does not recommend among A / B / C. The audit (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_AUDIT_2026_05_21.md` §8.2) leans slightly toward Path B (defer until Track B v0.2 substrate planning); §8.4 of the audit names Path C as a smaller follow-up. v0.1 names the seam; v0.2 (whichever shape) names the mechanism.

### §9.4 What ratification of Cluster 5 v0.1 means

Ratifying Cluster 5 v0.1 means the trio has accepted:

- The storage-governance invariant (§4).
- The canonical / derived / ephemeral vocabulary (§2).
- The list of named fragilities as stable cross-reference handles (§5) — without authorizing fixes.
- The list of named brainstorm mechanisms as stable cross-reference handles (§6.2) — without authorizing implementation.
- The pre-automation guarantee list (§7) with its "necessary but not sufficient" framing — as criteria future automation must meet, not as authorization.
- The seam to Cluster 5 v0.2 (§9.2).

Nothing more. Ratification is doctrine acceptance, not implementation authorization.

---

## §10 — Cross-references

- **Track A v0.1** — `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md` (commit `4f6cffb`). Provides Mode / Voice / Certainty / Authority. Cluster 5 v0.1 §4.2 cites Track A §3 (provenance fields), §3.2 (voice axis fields), §9.3 (source_type stability under voice), §9.6 (cross-session disagreement record).
- **Cluster 2 v0.1** — `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md` (commit `e527562`). Provides Scope / Lane / Authority class / Lifecycle / Promotion rights. Cluster 5 v0.1 §4.2 cites Cluster 2 §7 (sub-dimensions), §11.3 (tool_result lane defaults), §12 (disagreement primitive — the seam Track B v0.1 specialized).
- **Track B v0.1** — `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md` (commit `bdbd1e0`). Provides ContestRecord / contest ledger / true-but-not-mine / character refusal. Cluster 5 v0.1 §4.2 cites Track B §2.5 (true but not mine), §2.6 (character refusal), §3.2 (immutability + counter-contest reversal), §5 (Option C separate ledger), §7 (routing table), §8 Invariant 14 (contest increases audit visibility), Invariant 16 (self-issued contests cannot route to refuse).
- **Memory Digestion Doctrine v0.1** — `docs/MEMORY_DIGESTION_DOCTRINE_v0.1.md`. Provides released-memory primitive (release ≠ delete: keep content/provenance, lose identity-shaping weight). Cluster 5 §4.2 implicitly inherits via the governance-meaning enumeration.
- **Cluster 5 audit (2026-05-21)** — `scratch/CLUSTER_5_STORAGE_SURVIVABILITY_AUDIT_2026_05_21.md`. The substrate source for everything in §3 and §5 above.
- **Cluster 5 v0.1 vs audit review notes (2026-05-21)** — `scratch/CLUSTER_5_V0.1_VS_AUDIT_REVIEW_NOTES_2026_05_21.md`. Source for the three precision fixes applied in v0.1.1 before promotion.
- **Cluster 5 v0.1 scratch draft (preserved)** — `scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1_DRAFT_2026_05_21.md`. Original framing draft; preserved unchanged for lineage.
- **Cluster 5 v0.1.1 scratch polish (preserved)** — `scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.1_DRAFT_2026_05_21.md`. Polish with the three precision fixes; preserved unchanged for lineage.
- **Brainstorm Cluster 5** — `scratch/brainstorming/memory_roadmap_2026_05_09/06_cluster_5_storage_and_survivability.md`. Source of the anchor sentence and the mechanism list.
- **Brainstorm session summary** — `scratch/brainstorming/memory_roadmap_2026_05_09/99_session_summary.md`. Framing-doc-grade sentence #8 (anchor sentence). 2026-05-20 update names Cluster 5 audit as recommended next audit.
- **May 19 checkpoint** — `scratch/CHECKPOINT_2026_05_19_TRACK_A_CLUSTER_2.md`. Doctrine chain summary.
- **Roadmap notes** — `docs/TORMENT_ROADMAP_NOTES.md`. Records Cluster 5 framing audit as the recommended next audit task and includes the SQLite-as-control-plane correction.

---

## §11 — What does NOT happen because Cluster 5 v0.1 exists

Even with Cluster 5 v0.1 ratified and promoted:

- No file on disk changes shape.
- No load path changes behavior.
- No write path changes behavior.
- No CLI is added.
- No daemon is started.
- No `fsync` is added anywhere.
- No `IdentityStore.save` is patched to be atomic.
- No journal is introduced.
- No checksum is computed.
- No verify CLI runs.
- No automation is unblocked.
- Track A v0.1, Cluster 2 v0.1, Track B v0.1, and the Memory Digestion Doctrine v0.1 remain bit-for-bit unchanged.

Cluster 5 v0.1 is doctrine. Its effect is on subsequent trio decisions, audit work, and implementation tracks — not on the bytes currently on disk.

---

## §12 — Status

**Status:** RATIFIED ADVISORY DOCTRINE — 2026-05-21. Promoted from scratch v0.1.1 by trio decision.

**Revision history:**
- v0.1 — 2026-05-21 — initial scratch framing draft (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1_DRAFT_2026_05_21.md`).
- v0.1 vs audit review notes — 2026-05-21 — three precision fixes recommended (`scratch/CLUSTER_5_V0.1_VS_AUDIT_REVIEW_NOTES_2026_05_21.md`).
- v0.1.1 — 2026-05-21 — three precision fixes applied (`scratch/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.1_DRAFT_2026_05_21.md`): §4.2 storage-status legend with five tags; §5 fragility handle split into `JSONL-NO-FSYNC` (write-side) and `JSONL-LOADER-NOT-FAIL-TOLERANT` (read-side); §7.0 "necessary but not sufficient" framing line.
- **Promoted — 2026-05-21 — this document.** Ratified by trio (pzychozen + GPT + Claude). Doctrine-only advisory. No implementation authorized.

**Next gate:** trio decision among the three named paths in §9.3 (Cluster 5 v0.2 directly / Track B v0.2 first / deeper governance-preservation audit first) when a future session opens the implementation track.

**End of Cluster 5 v0.1 doctrine.**
