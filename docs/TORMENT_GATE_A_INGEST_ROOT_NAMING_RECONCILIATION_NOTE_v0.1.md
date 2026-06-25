# TORMENT Gate A — Ingest-Root Naming Reconciliation Note v0.1

## 1. Status / scope

**Docs-only reconciliation note. NON-AUTHORIZING. Selects nothing.** This note
reconciles a naming slip in the Gate A wall artifacts: prior references to
`MemoryFabric.ingest` should be read as shorthand for the live ordinary ingest
fan-out root, which is actually `TormentFabric.ingest`. It changes no contract, no
mechanics, no code, and no tests, and it opens no gate.

It edits no other document. In particular it does **not** edit
`docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`,
`docs/TORMENT_GATE_A_DOCUMENT_A_CONTAINMENT_WALL_ENFORCEMENT_FRAME_v0.1.md`,
`docs/TORMENT_GATE_A_CONTAINMENT_WALL_ENFORCEMENT_PATH_PROPOSAL_v0.1.md`, or
`docs/PROJECT_ORIENTATION_MAP.md`. Those keep their wording; this note records how
to read it.

## 2. The naming fact

- The live ordinary ingest fan-out root is **`TormentFabric.ingest`**
  (`torment_service/fabric.py`).
- **There is no `MemoryFabric` class** in `torment_service/`.
- Earlier Gate A wording — Document A discussion, the wall enforcement frame, and
  the enforcement-path proposal — used `MemoryFabric.ingest`. **Read that as a
  naming slip / shorthand for the ordinary fabric ingest root, i.e.
  `TormentFabric.ingest`.**

This is source-backed by the inventory guard
`tests/test_gate_a_wall_ingest_fanout_root_inventory.py`, which anchors on
`TormentFabric.ingest` as the root and records (in
`test_naming_mapping_no_memoryfabric_class`) that no `MemoryFabric` class exists.

## 3. What this note is NOT

The `MemoryFabric.ingest` → `TormentFabric.ingest` reading is **not**:

- a selected or renamed class;
- a contract amendment (Document A and the Gate A artifacts are unchanged);
- a mechanics choice;
- a carrier / store / schema / field / API decision;
- any wall implementation or wiring.

It is purely a reading convention for already-written prose.

## 4. Preserved contract meaning

This note preserves, and does not alter, the existing Gate A posture:

- The **ordinary ingest fan-out root remains the terrain** the wall concerns
  itself with (the fan-out root into motif / drift / mood / role / deep / SRG /
  reinforcement / retrieval / projection / promotion).
- The **wall remains unbuilt**.
- The **wall enforcement path remains non-authorizing** (proposal only).
- **No live unadmitted-candidate producer exists.**
- **No A-C1 future-candidate proof is claimed** — the existing A-C1 work is
  resting-state inventory/characterization only.

## 5. No-go list (verbatim, in force)

```
No production code.
No wall mechanics.
No Gate D.
No Envelope Audit runtime.
No private-owner live wiring.
No Shape B.
No endpoint/schema/API changes.
No prompt exposure.
No AgentRunner ownership expansion.
No database/substrate.
No carriers/schema/fields.
No writer fixes.
No P4 O1/O2.
No Seed-Gov mechanics.
No retrieval feedback.
No persistence changes.
No autonomy.
No audit-to-control feedback.
No candidate store.
No governed admission implementation.
No promotion-crossing implementation.
```

## 6. Stop condition

After this naming note lands, the Gate A wall vein **pauses** (or hands off to a
phase handoff). This note opens **no new lane** and does **not** open A-C2, A-O2,
A-D1, or A-D2 by implication. Any next Gate A move requires separate Codex/operator
authorization.

---

**Anti-drift footer.** Docs-only reconciliation note. Reading convention only:
`MemoryFabric.ingest` is shorthand for the live `TormentFabric.ingest` ordinary
ingest fan-out root. No class renamed, no contract amended, no mechanics selected,
no gate opened. Guidance not control; audit observes authority and does not become
authority; nothing rewrites identity / canon / seed / soul.
