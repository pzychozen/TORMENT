# TORMENT gravity_correction Automatic-Canon Audit-First Reconciliation v0.1

**Status:** Requirement-level **reconciliation / audit-first** memo — docs-only. **Promoted docs-only 2026-06-15.** Closure registered in the Decision Registry **§N14**. A bounded audit-first reconciliation of the single live automatic writer `torment_service/character.py::gravity_correction` — the not-yet-reconciled automatic drift-correction-canon writer — performed *before* any P6 / Stage B / database substrate mechanics. It records doctrine status, tensions, entanglement routing, and later-owner routing only; it selects no mechanics and patches no writer.
**Date:** 2026-06-15.
**Authoritative state at promotion:** HEAD = origin/main = `0d908d8` (*docs(engine): promote matched P2.5/P4 reconciliation*), pre-promotion; working tree clean. Subsequent versions require their own trio/operator ratification.
**Lineage:** matched P2.5/P4 reconciliation closure (registry §N13) + DB/Substrate Doctrine Reconciliation §10/§11/§16 routing → accepted gate-framing plan (`GATE_FRAMING_..._v0.1_PLAN.md`, GPT + Codex scope corrections applied) → promoted-candidate draft → GPT steering review → Codex adversarial leakage review (required-wording correction applied) → operator promotion (docs-only). Working-folder drafts and the framing plan remain non-load-bearing evidence lineage.

**Mandatory wording locks (load-bearing, carried verbatim in intent):**

1. `gravity_correction` is a **not-yet-reconciled automatic drift-correction-canon writer**.
2. This artifact may identify constraints and routing for the `gravity_correction` automatic-canon seam. **It may not patch the writer, decide it is right or wrong, decide its Seed-Governance conformance, or choose, imply, prepare, or privilege any substrate mechanic.**
3. **Pairing, routing, classification, and audit are not conformance.**
4. **Audit observes and classifies the seam; audit does not become authority.**
5. **P4 read-side retrieval / continuity-boost behavior is named as adjacency only.** This artifact does not characterize, evaluate, repair, redesign, or assert conformance/non-conformance of read-side behavior. Later P4 runtime conformance owns that.
6. **Existing labels are seam evidence only**, not future field/carrier/schema endorsements.

**Blade-width lock:** scoped to the single live writer `torment_service/character.py::gravity_correction` only. It does **not** extend to `plant_seed`, `promote_chunk`, collective/quorum canon, `_maybe_emit_identity_anchor`, Seed-Governance mechanics, or automatic canon writers in general. Those appear only as named adjacency, never as scope.

---

## 1. Status and non-authorization boundary

This is a **docs-only, reconciliation-only, audit-first** artifact. It is:

- **not** an implementation plan
- **not** a runtime patch
- **not** a database / substrate design
- **not** P6 carrier mechanics
- **not** Stage B
- **not** migration
- **not** Seed-Governance mechanics or canon-source representation
- **not** P4 runtime conformance
- **not** a registry amendment by itself

It classifies the doctrine status and later-owner routing of one live writer. It opens no gate, selects no mechanic, and amends no contract. Its promotion and closure are registered in the Decision Registry §N14 (see §13).

**Gate status:** This artifact, promoted docs-only, opens no gate. It closes this docs-only reconciliation slice (registered §N14) and opens no later gate. **Active gate after promotion: none. Next gate: unselected.** Promotion does not imply or open Stage B, P6 carrier mechanics, database design, migration, runtime enforcement, Seed-Governance mechanics, or P4 runtime conformance; each remains unopened and requires its own bounded decision.

## 2. Purpose and one-scope question

The pre-substrate stack closed five contracts and the matched P2.5/P4 reconciliation (registry §N13) while Stage B substrate mechanics remained paused behind GitHub Issue #54. The DB/Substrate Doctrine Reconciliation memo §11 seam 8 named the `mood_drift → drift centroid → gravity_correction → canon=True` pathway as a dependency-scoped parked seam, and §16 routed its reconciliation to a dedicated audit-first slice before the trio free-design council and Stage B. This artifact is that slice's content.

**One-scope question:**

> What is the **doctrine status and later-owner routing** of the live `gravity_correction` automatic drift-correction-canon writer, given that it can emit `canon=True`, `tier="core_identity"` drift-correction memories automatically, on ingest, before any P6 / Stage B / database substrate mechanics exist?

It classifies and routes. It resolves nothing about whether the writer should keep, lose, or change its behavior.

## 3. Live write-surface evidence map

Grounded by direct read of `torment_service/character.py` at HEAD `0d908d8`. Labels are seam evidence only.

| Element | Location | Observed behavior |
|---|---|---|
| Function | `gravity_correction(...)` `:565` | Keyword-only: `graph`, `motif_registry`, `embedder`, `seed`, `agent_id`, `step`, `drift_info`. |
| Threshold / direction gate | `:587`, `:589` | Returns `{correction_applied: False}` unless `drift_score <= -seed.drift_correction_threshold` **and** `drift_direction == "away_seed"`. Automatic but **conditional**. |
| Additive-only claim | docstring `:575–582` | "purely additive — it never rewrites or deletes existing memories." |
| Memory mint | `graph.spawn_memory(...)` `:600–616` | Emits a new memory with the fields below. |
| `mtype` | `:603` | `mtype="drift_correction"`. |
| `half_life_days` | `:606` | `half_life_days=seed.core_half_life`. |
| `canon` | `:607` | **`canon=True`**. |
| `tier` | `:612` (extra_payload) | **`tier="core_identity"`**. |
| `corrects_drift_score` | `:613` | provenance field carrying the drift score at correction. |
| `corrects_at_step` | `:614` | provenance field carrying the step. |
| Motif attach | `:619–629` | If `seed.seed_motif_id`, `motif_registry.attach_or_create(... attach_threshold=0.50)` binds the new eid to the seed motif. |
| Durable flush | `graph.flush_node(int(eid))` `:631` | Flushes the new node to the durable graph store. |
| Return metadata | `:633–639` | Returns `correction_applied`, `correction_eid`, `correction_strength`, `drift_score_at_correction`, `concept_reinforced`. |

## 4. Ingest / wiring evidence map

Grounded by direct read of `torment_service/fabric.py` at HEAD `0d908d8`.

- `_maybe_emit_mood_drift(...)` runs **earlier** in the ingest band (def `:1575`; call `:3279`).
- `_maybe_emit_mood_drift` is **guidance-only** — docstring: "This is guidance-only … without dominating retrieval or defining persona" (`:1586`).
- it emits `mtype="mood_drift"` (`:1649`).
- it sets **`canon=False`** (`:1654`).
- the character drift check is **periodic and non-blocking** — gated by `self._character_enable and stored and step > 0 and step % self._character_drift_every == 0` (`:3290`).
- `measure_drift(...)` runs (`:3297`).
- `CharacterState` is updated and **saved before** any possible correction — `self.character_store.save_state(...)` (`:3325`), after assigning drift score/direction/basin fields.
- high `away_seed` drift calls `gravity_correction(...)` — gate `:3328–3331` (`drift_score < -threshold` and `drift_direction == "away_seed"`), call `:3333`.
- a drift-reflex callback fires on the below→above transition only (`:3343–3359`) — see §7 (under-claimed).

## 5. Doctrine anchor map

| Source | Constraint contributed (none authorizes mechanics) |
|---|---|
| **DB/Substrate Doctrine Reconciliation §10** | Routes "gravity_correction automatic-canon reconciliation → gravity-correction audit-first slice (framing §9; Document A §11; Seed-Gov §9)." This artifact is that destination. |
| **§11 seam 8** | Names `mood_drift → drift centroid → gravity_correction → canon=True` as a dependency-scoped parked seam: reconcile *before any substrate persists its products*. |
| **§13** | Seam blocks dependent substrate mechanics but does **not** block docs-only reconciliation; each is "a requirement a later substrate proposal must be able to state it will honor before mechanics open." |
| **§16** | Sequencing: matched P2.5/P4 → **this slice** → trio free-design council → Stage B/database only after + Issue #54 clean-checkpoint. Advisory; opens nothing. |
| **Decision Registry §N13** | Active gate none; next unselected; "the gravity_correction audit-first slice … remains unopened/unselected; … requires its own bounded decision." |
| **Seed-Governance SG-O4 `:105` / §8 `:162` / §9 `:170`,`:188`** (direct-read) | SG-O4: "A single `canon` boolean is **not sufficient governance truth** … Governance must be able to distinguish canon by source class … v0.1 selects no storage representation, field, or schema." §8 taxonomy classes **drift-correction-canon** = `gravity_correction` (`mtype=drift_correction`), **automatic**, "automatic identity reinforcement; requires §9 reconciliation." §9 seam register: "Named, not patched … SG-O5 is a requires-reconciliation flag, not a must-patch-now order"; compound hazard `mood_drift → drift centroid → gravity_correction → canon=True` "not wrong by inspection; not patched here." (SG-O6 `:109`: soft guidance may not silently become canon authority, including through an automatic chain.) |
| **Document A — Writer-Authority A-O1 `:135` / A-O5 `:143` / §3 trace `:302` / §11 routing `:347`** (direct-read) | A-O1: a writer may write only if authorized for that **class**; "Authorization must not be inferred solely from payload flags (`canon`, `mtype`, half-life, tier) or from source presence … Today these are trusted without a writer-authority check." A-O5: "Existing automatic writers are named unreconciled seams, **not exemptions** … Document A patches none of them." §3 traces `gravity_correction` as "(AUTOMATIC; drift-gated; no authority check)." §11 routes "gravity_correction automatic canon → dedicated bounded audit-first reconciliation slice." Routing, not authorization. |
| **P4 — Reader/Projection Safety (§N5)** | Adjacency only: the **P4 read-side retrieval / continuity-boost adjacency** for `drift_correction` rows is P4's read-side window. **Named here only; not characterized, evaluated, repaired, or asserted conformant/non-conformant — later P4 runtime conformance owns that.** |
| **Stage A — Recovery/Reconciliation Semantics (§N6) / P5a** | Adjacency only: "a memory is not recovered unless its governance meaning is recovered"; storage-lane ≠ authority-class; CharacterState/checkpoint recovery is Stage A / P5a-owned. |
| **Ledger Observational-Boundary Doctrine** (direct-read `:21`, ratified `:156`) | Verbatim: "*Audit observes authority. Audit does not become authority.*" Governs this artifact's own posture. |

## 6. Tension map

Stated for review; classified and routed, resolved none.

1. **Automatic soft-guidance-to-identity-canon pathway.** A threshold-gated automatic process mints `canon=True`, `tier="core_identity"` memories (`character.py:600–616`) without a governed admission crossing. Tension: automatic ≠ governed-admitted (Document A admission edge; Seed-Gov §9 compound hazard).
2. **canon single-flag vs canon-by-source.** The writer sets one `canon=True` boolean (`:607`); Seed-Gov SG-O4 holds one flag insufficient governance truth. Tension: the source-class of this canon is not separately distinguishable today.
3. **Writer authority vs payload flag / source presence.** The write's authority rests on the call site + payload flag, not a class-bound writer-authority check (Document A A-O1/A-O4). Tension: payload flag ≠ writer authority.
4. **mood_drift contribution to the drift centroid.** `_maybe_emit_mood_drift` is guidance-only, `mtype="mood_drift"`, `canon=False` (`fabric.py:1586`/`:1649`/`:1654`), runs earlier in the band (`:3279`), and can contribute non-canon memories to recent-memory state that `measure_drift` reads; high drift then triggers the separate canon mint. Tension: a soft, non-canon signal can be upstream of a hard canon emission. Name only.
5. **CharacterState save / checkpoint adjacency.** `CharacterState` is saved (`:3325`) *before* the possible correction; it is also checkpoint-serialized (registry C3) and is the `IDENTITY-NON-ATOMIC-SAVE` maintenance candidate. Tension: write-ordering + non-atomic-save adjacency. Route, do not repair.
6. **Motif attach + flush_node persistence adjacency.** `attach_or_create` (`character.py:619`) and `flush_node` (`:631`) make the canon product durable and motif-bound. Tension: persistence of an unreconciled automatic-canon product before substrate semantics exist (seam 8 "before any substrate persists its products").
7. **P4 read-side retrieval / continuity-boost adjacency, named only.** `drift_correction` is treated alongside `seed_canon` in two read/retrieve-boost branches (`fabric.py:4064`, `:6705`). **This artifact names the read-side adjacency only. It does not characterize, evaluate, repair, or redesign read-side retrieval/projection behavior; later P4 runtime conformance owns that.** No conformance/non-conformance asserted, no fix proposed.
8. **Audit visibility vs authority.** Classifying this seam must not become control over the writer (Ledger `:21`). Tension held by posture: audit observes, does not become, authority.

## 7. Entanglement map (named and routed, not solved)

- CharacterState save (`fabric.py:3325`) → Stage A / P5a.
- Checkpoint semantics (registry C3) → Stage A / P5a.
- Identity non-atomic save / plain-JSON state save (`IDENTITY-NON-ATOMIC-SAVE`) → maintenance lane.
- `mood_drift` — guidance-only, `mtype="mood_drift"`, `canon=False` (`fabric.py:1575`/`:1586`/`:1649`/`:1654`; call `:3279`) → named adjacency; see §8 Q.
- Drift centroid / `measure_drift` (`fabric.py:3297`) → named adjacency.
- Motif attach (`character.py:619`) → Stage B / P6 persistence-mechanics adjacency.
- `flush_node` durability (`character.py:631`) → Stage B / P6 durability adjacency.
- P4 read-side retrieval / continuity-boost adjacency for `drift_correction` rows (`fabric.py:4064`, `:6705`) → **named only**, routed to later P4 runtime conformance.
- Seed-Governance canon-source doctrine (SG-O4) → Seed-Governance later-owner.
- Document A class-bound writer authority (A-O1/A-O4) → Document A writer-authority / P2.5 implementation track.
- **Possible `agent_loop` / drift-reflex callback adjacency (`fabric.py:3343–3359`) — under-claimed only.** The callback hook is visible; whether/how a live `TormentFabric` agent loop consumes it is **not traced this pass** and not claimed.

## 8. Parked questions (routed, not answered)

- **Q-G1.** Which later owner decides whether / how this writer can become **conformant**? (Document A writer-authority track / P2.5 implementation track / Seed-Governance later-owner — routed, not picked.)
- **Q-G2.** Which later owner decides **canon-source representation** so SG-O4 can be honored? (Seed-Governance later-owner / Stage B-P6 representation — unselected.)
- **Q-G3.** Which later owner decides whether `canon=True` from *this path* may **persist into substrate form**, and under what governance? (Stage B / P6 + seam 8.)
- **Q-G4.** Which later owner handles the **CharacterState / checkpoint / atomicity** adjacency? (Stage A / P5a + maintenance lane.)
- **Q-G5.** Which later owner handles **P4 read-side retrieval / continuity-boost conformance** for `drift_correction` rows? (later P4 runtime conformance — separately authorized; named-only here.)
- **Q-G6.** Which later owner handles an **actual runtime patch**, if ever authorized? (separately authorized implementation track; not this slice, not Stage B.)
- **Q-G7.** Whether `mood_drift → centroid → gravity_correction` remains **named-only** or becomes future reconciliation scope. (Route to council; do not pre-decide.)

## 9. Findings

Stated as evidence for a later trio decision, not authority over it. Careful language per the wording locks.

- The `gravity_correction` writer is **live** (wired into the fabric ingest band; `fabric.py:33`, `:3333`).
- Its behavior is **automatic and conditional** — it fires only on `away_seed` drift past `seed.drift_correction_threshold` (`character.py:587`/`:589`; `fabric.py:3328–3331`).
- It **mints `canon=True` `drift_correction` rows** with `tier="core_identity"` (`character.py:603`/`:607`/`:612`), additively (never rewrites/deletes; docstring `:575–582`).
- Doctrine **already names this as a parked dependency-scoped seam** (DB/Substrate memo §11 seam 8; Document A §11; Seed-Gov §9).
- **Reconciliation is required before dependent substrate mechanics persist its products** (DB/Substrate memo §11/§13; seam 8 "before any substrate persists its products").
- The **correct next work is classification / routing, not patching** (§16 sequencing; Seed-Gov "requires-reconciliation flag, not a must-patch-now order").

*(This section deliberately avoids: wrong · right · compliant · non-compliant · should patch · must disable · must keep · Seed-Governance-compliant · Seed-Governance violation.)*

## 10. Non-authorizations / red lines

```
No code patch.
No tests as a gate deliverable.
No runtime enforcement.
No Authority Gate wiring.
No writer-authority implementation.
No schema / store / field / carrier / fingerprint / allocator / serialization design.
No migration.
No Stage B.
No P6 carrier mechanics.
No Seed-Governance mechanics, canon-source representation, or seed-rewrite mechanics.
No characterization, evaluation, repair, redesign, or conformance assertion of P4
  read-side retrieval / continuity-boost behavior.
No MCP action surface, automation, autonomy, monitoring, notification, or scheduler.
No broadening to other automatic canon writers
  (plant_seed / promote_chunk / collective canon / identity_anchor).
Existing labels (drift_correction, canon, core_identity, mood_drift, eid, motif)
  are seam evidence only — not future field / carrier / schema endorsements.
Audit observes and classifies the seam; audit does not become authority.
No registry amendment beyond the §N14 closure registration this artifact's promotion carries.
```

## 11. Advisory sequencing (carried; opens nothing)

```
N13 matched P2.5/P4 closure                                              [CLOSED 0d908d8]
→ gravity_correction automatic-canon audit-first reconciliation          [THIS ARTIFACT — closed §N14]
→ trio free-design council
→ Stage B / database mechanics — ONLY after the above + Issue #54 clean-checkpoint
```

This artifact opens nothing by itself.

## 12. Evidence lineage

**Code read directly (HEAD `0d908d8`):**
- `torment_service/character.py` — `gravity_correction` `:565–639` (gate `:587`/`:589`; docstring `:575–582`; `spawn_memory` mint `:600–616` incl. `mtype` `:603`, `half_life_days` `:606`, `canon=True` `:607`, `tier` `:612`, `corrects_drift_score` `:613`, `corrects_at_step` `:614`; motif attach `:619–629`; `flush_node` `:631`; return `:633–639`).
- `torment_service/fabric.py` — import `:33`; `_maybe_emit_mood_drift` def `:1575`, docstring "guidance-only" `:1586`, emit `mtype="mood_drift"` `:1649` / `canon=False` `:1654`, call `:3279`; character drift band `:3290–3341` (`measure_drift` `:3297`; `save_state` `:3325`; high-drift gate `:3328–3331`; `gravity_correction` call `:3333`); drift-reflex callback `:3343–3359`; `drift_correction` read/retrieve-boost branches alongside `seed_canon` `:4064`, `:6705` (named only, not characterized).

**Doctrine read / cross-read:**
- `docs/TORMENT_DATABASE_SUBSTRATE_DOCTRINE_RECONCILIATION_AGAINST_PRE_SUBSTRATE_v0.1.md` §10, §11 (seam 8), §13, §16.
- `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md` §N8, §N10, §N12, §N13 (context §C3, §C20).
- `docs/TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md` — **direct-read this pass**: SG-O4 `:105` (canon-by-source; no storage repr selected); SG-O6 `:109` (soft guidance must not silently become seed/canon authority, including through an automatic chain); §8 canon-source taxonomy `:155–166` (drift-correction-canon = `gravity_correction`, automatic, requires §9); §9 automatic-writer seam register `:168–190` (named-not-patched; SG-O5 requires-reconciliation flag; compound hazard `:188`).
- `docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md` — **direct-read this pass**: A-O1 `:135` (class-bound writer authority; payload flags / source presence not sufficient); A-O5 `:143` (existing automatic writers are named unreconciled seams, patched by none); §3 canon=True writer trace `:302` (gravity_correction AUTOMATIC; drift-gated; no authority check); §11 routing `:347` (gravity_correction automatic canon → dedicated bounded audit-first reconciliation slice).
- `docs/TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md` (read-side adjacency only).
- `docs/TORMENT_MEMORY_ENGINE_STAGE_A_RECOVERY_RECONCILIATION_SEMANTICS_CONTRACT_v0.1.md` (recovery/checkpoint adjacency only).
- `docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md` — direct-read `:21` (audit-observes anchor), ratified `:156`.
- `docs/TORMENT_MEMORY_ENGINE_SUBSTRATE_READINESS_PHASE_CONSOLIDATION_MEMO_v0.1.md` §3 (`IDENTITY-NON-ATOMIC-SAVE`).

**Non-load-bearing:** the framing plan; prior scratch packets.

## 13. Promoted-artifact footer

This artifact is **promoted docs-only** as a requirement-level reconciliation / audit-first memo; its closure is registered in the Decision Registry **§N14** (2026-06-15). It confers:

- **no code authority** (no code patch, no runtime enforcement, no Authority Gate wiring, no writer-authority implementation)
- **no Stage B**
- **no P6 carrier mechanics**
- **no database design**
- **no schema / store / carrier / migration** (nor field / fingerprint / allocator / serialization / enum selection)
- **no Seed-Governance mechanics, canon-source representation, or seed-rewrite mechanics**
- **no P4 runtime conformance** (read-side retrieval / continuity-boost named as adjacency only)
- **no MCP action surface, autonomy, automation, monitoring, notification, or scheduler**

It amends no upstream contract and does not amend the recorded dependency graph. Subsequent versions require their own trio/operator ratification.
