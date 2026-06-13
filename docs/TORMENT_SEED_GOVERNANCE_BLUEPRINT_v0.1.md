# TORMENT Seed-Governance Blueprint v0.1

**Status:** Requirement-level **seed / identity / canon governance** contract — docs-only. **Promoted 2026-06-13.** States *what must be true before the authored seed, identity-tier, or canon may change*; selects no mechanics. Authorizes **no implementation, no runtime seed writer, no runtime mutation, no canon-editing mechanics, no schema, no store, no field names, no serialization, no migration, no database design, no Stage B, no scheduler / trigger / budget, no private cognition loop, no prompt/retrieval coupling, and no autonomy.** It specializes Document A's write-side wall for seed / identity / canon outcomes; it amends Document A in no way. Windows-visible tracked repo state remains authoritative.

**Lineage:** Seed-Governance opening survey (read-only archaeology, 2026-06-13) → draft rev0 → GPT review (rev0 Q-1…Q-5 + seven steering answers) → rev1 → Codex adversarial review (ACCEPT WITH WORDING CORRECTIONS; five wording corrections) → rev2 → GPT ACCEPT FOR OPERATOR PROMOTION → docs-only promotion (this artifact). The scratch working drafts (`scratch/pre_substrate_architecture_reconstruction/2026-06-13/`) remain non-load-bearing evidence lineage.

**Opening guardrail (load-bearing, verbatim):**

> Seed-Governance is not a seed rewrite mechanism. It is the requirement-level governance contract preventing seed, identity, and canon from being quietly rewritten.

**Architecture relation (carried, exact):**

```
Document A   → write-side containment wall        (the boundary)
Document B   → private-cognition interior         (what must be true inside the wall)
P4           → read-side projection boundary      (the window)
Stage A      → recovery / reconciliation semantics
Cluster 2    → authority / lifecycle / promotion vocabulary
Ledger       → audit observes authority; audit does not become authority
MCP boundary → automatic only where ratified; autonomous unopened
Seed-Gov     → specializes the write-side wall for seed / identity / canon outcomes
later P2.5 / gravity-correction audit-first slice / writer-authority reconciliation → mechanics + enforcement
```

**Standing anchors (carried together):**

```
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit does not become authority.
Preserve continuity without preserving compulsion.
Automatic remains allowed only where separately ratified. Autonomous remains unopened.
Control means absolute / coercive control; guidance is allowed; the soul cannot be quietly rewritten.
```

**Tags:** `[OBLIGATION]` · `[DEFINITION]` · `[OPERATOR-RATIFIED]` · `[OPERATOR POSTURE]` · `[CONTRACT CANDIDATE]` · `[FACT]` traced runtime fact (point-in-time) · `[DISTINCTION]` · `[LATER OWNER]` · `[NON-AUTHORIZATION]` · `[PARKED]` · `[OPEN]`.

---

## 1. Status and non-authorization boundary

`[FACT]` This is a **requirement-level** contract. It states what must be true of seed / identity / canon changes *before* any implementation exists. It is **not** a runtime seed writer, **not** a canon-editing mechanism, **not** a patch to any existing writer, **not** P4 read-side enforcement, **not** the Memory-Engine P1 SRG disposition, **not** an autonomy doctrine.

`[NON-AUTHORIZATION]` Opens no Stage B. Opens no autonomy. Amends no upstream contract (A / B / P4 / Stage A / Cluster 2 / Ledger / MCP boundary). Patches none of the existing automatic writers it names.

## 2. Purpose

`[OBLIGATION]` Seed-Governance defines, at requirement level, the governance any change to the **authored seed, identity-tier material, or canon** must satisfy. It answers: *under what governed conditions may the character's authored center change, and how do we guarantee it can never change quietly, automatically, or irreversibly without an explicit operator-authorized, auditable, contestable crossing?* It also fixes the **specialized writer-authority requirement** for seed / identity / canon-class outcomes — the Document A wall, sharpened for the most sensitive class of write. It does not answer *how* any of it is implemented.

`[FACT]` Motivating finding (Seed-Governance opening survey, 2026-06-13; point-in-time): the authored seed is not mutated by any current runtime path, but mutation is **not structurally impossible** — `IdentityStore.save` already persists the whole seed dict, so "write-once" is a convention/absent-path, not an invariant. Three runtime writers reach canon/identity-tier (`plant_seed`, `gravity_correction` automatic, `promote_chunk` force), and an automatic compound pathway (`mood_drift → drift centroid → gravity_correction → canon=True`) exists. These are named, not patched, here.

## 3. Scope and upstream dependency map

`[OBLIGATION]` Edges:

- **Specialization edge (toward Document A):** Document A owns the general write-side wall and the governed admission crossing. Seed-Governance **specializes** that wall for seed / identity / canon outcomes; it does not replace, rival, or amend it.
- **Candidate edge (toward Document B):** Document B routed `identity / seed / canon-affecting reflection → stricter than ordinary proposed-write; never auto-admit` to this blueprint (Document B §8 / Q-a). Seed-Governance defines that stricter posture; the staging that produces such candidates stays Document B's.
- **Read-side edge (P4):** any projection/eligibility of seed/identity/canon material is P4-governed; Seed-Governance creates no read-side enforcement.
- **Recovery edge (Stage A):** authored canonical character state must survive verbatim within committed durability (Stage A O6); recovery mechanics route to Stage A / P6.
- **Vocabulary edge (Cluster 2):** authority-class / lifecycle / promotion-rights / scope vocabulary is used as-is; no new fields.

`[FACT]` Dependency map:

| Upstream | Owns | Seed-Gov inherits | Seed-Gov must not |
|---|---|---|---|
| **Document A** | write-side wall; `A-O1` class-bound writer authority; `A-O2` no automatic canon/identity from cognition; governed admission crossing (§8) | the wall; the admission crossing as the single admission edge | amend A; build a rival crossing |
| **Document B** | interior staging; `identity/seed/canon → stricter; never auto-admit` routed here (Q-a) | the candidate class that arrives at the crossing | own interior staging; reopen Document B |
| **P4** | reader/projection safety; `diagnostic_only` default | read-side governance of any surfaced seed/identity material | create read-side enforcement |
| **Stage A** | recovery semantics; O6 verbatim authored-canon survival, no pinning | the recovery/reversibility requirement on revisions | select recovery/durability mechanics |
| **Cluster 2** | authority/lifecycle/promotion vocabulary; `not-self-promotable` | the vocabulary for classifying canon outcomes | add fields; amend Cluster 2 |
| **Ledger** | audit ≠ authority | audit-without-authority on all seed-governance records | let audit become a seed/canon authority path |
| **MCP boundary** | Tier 3: seed modification / identity rewrite never MCP-exposed | the exposure floor (never weaker) | weaken the Tier-3 boundary |

## 4. Definitions (requirement level only — no field names, stores, schemas, serialization, or APIs)

- `[DEFINITION]` **Authored seed** — the operator-supplied identity baseline (`seed_text` + `seed_id`) that establishes the character's deepest basin. Prompt-visible and kernel-modulating soft influence.
- `[DEFINITION]` **Seed revision** — any change to the authored seed's content after creation. Currently has no governed path (and no routine runtime path); this contract defines its governance.
- `[DEFINITION]` **Identity-tier material** — core-identity / decade-half-life memory that shapes the character's behavioral baseline (canon seed memories, drift-correction anchors, promotion-canon, and — at the derived tier — auto-emitted identity anchors). `[DISTINCTION]` Ordinary non-canon derived identity anchors are **identity-relevant seams, not Seed-Governance crossings by default**; they enter this contract's stricter crossing only if promoted, canonized, used as seed-revision evidence, or given durable identity-authority weight (matches §9).
- `[DEFINITION]` **Canon** — a durable authority-relevant class flag whose **governance meaning depends on source class**. `[DISTINCTION]` Canon is currently a single boolean carrying several distinct governance meanings (see §8); this contract treats canon-by-source, not canon-as-boolean, as the governance unit.
- `[DEFINITION]` **Canon-source class** — the governance-meaningful origin of a canon/identity write: *authored-seed-canon*, *drift-correction-canon*, *promotion-canon*, *collective-canon*. Conceptual only; no field is named or added.
- `[DEFINITION]` **Identity / seed / canon-affecting candidate** — a staged candidate (Document B) **seeking an actual seed, identity-tier, canon, promotion, or revision outcome** — *not* every ordinary identity-flavored or identity-relevant reflection. Subject to the stricter crossing (§6).
- `[DEFINITION]` **Governed seed-revision crossing** — a specialized governed seed-state revision boundary; **not** ordinary-memory admission and **not** a path for unadmitted candidates to bypass Document A. It is explicit, operator-authorized, lineage-preserving, auditable, contestable, and reversible (§7).
- `[DEFINITION]` **Stricter-parameterized admission crossing** — Document A's governed admission crossing carrying the additional seed-governance requirements of §6; **not** a separate or rival crossing.
- `[DEFINITION]` **Soft guidance** — mood / drift / warmth / role / symbolic influence: durable-soft, non-canonical, never authority-bearing (Stage A O6 / registry §N7).

`[DISTINCTION]` Carried, exact (the desired posture):

```
recognizing identity continuity ≠ granting identity authority
identity-relevant ≠ identity-authoritative
seed resonance ≠ seed mutation
canon-affecting insight ≠ canon admission
private reflection staging ≠ ordinary memory write
audit concern ≠ authority change
guidance ≠ control
```

## 5. Seed-governance obligations (requirement level)

`[OBLIGATION] SG-O1 — Operator-governed seed revision.` Authored seed revision is **operator-governed, explicit, auditable, contestable, and reversible**. It may never occur silently, automatically, or as a side effect. `[OPERATOR-RATIFIED]` Operator-only is the v0.1 default; the operator (Hilmir) remains final authority over authored seed revision. User-co-sign may be a later **stricter** option but is **not required** in v0.1.

`[OBLIGATION] SG-O2 — Stricter, never-auto-admit candidate class; authorization scoped to actual outcome.` Identity / seed / canon-affecting candidates (per the §4 tightened meaning) are **stricter than ordinary proposed writes and never auto-admit** (consumes Document B §8 / Q-a). `[OPERATOR-RATIFIED]` **Operator authorization is required for authored seed revision and for automatic or candidate-originated seed / identity / canon outcomes unless a separately ratified governance path already owns that canon-source class.** This does **not** amend existing separately ratified collective-canon / quorum / operator materialization paths; Seed-Governance only requires their canon-source class to remain governance-distinguishable. A candidate merely staged as audit-only, refused, retired, or kept below ordinary identity/canon effect requires **no** authorization beyond Document A's ordinary inspection/audit posture.

`[OBLIGATION] SG-O3 — Document A remains the admission edge.` Document A's governed admission crossing remains the single admission edge. Seed-Governance adds **stricter class requirements** to it (§6); it builds no rival crossing and amends A in no way.

`[OBLIGATION] SG-O4 — Canon meaning must be governance-distinguishable.` A single `canon` boolean is **not sufficient governance truth**. Governance must be able to distinguish canon by source class (§8). `[OPERATOR-RATIFIED]` Any future governed crossing must be able to **identify which canon-source class it is acting on**; **v0.1 selects no storage representation, field, or schema** for that identification — the requirement is conceptual.

`[OBLIGATION] SG-O5 — Automatic identity/seed/canon writers require later governed reconciliation.` Existing automatic writers that create or condition identity/seed/canon material may **not** be treated as safely authorized merely because they run today. Each requires later governed reconciliation (§9) before it counts as conformant. `[OPERATOR-RATIFIED]` SG-O5 is a **not-yet-conformant / requires-reconciliation flag**, not a must-patch-now order; this document mandates no immediate change to any named writer.

`[OBLIGATION] SG-O6 — Soft guidance must not silently become seed/canon authority.` Mood, drift, warmth, role, and symbolic influence may guide; they may not silently become seed or canon authority, directly or through an automatic chain (§9). This sharpens, and does not amend, Stage A O6.

`[OBLIGATION] SG-O7 — Recognition is not authority.` Seed resonance and identity-continuity recognition are **not** seed mutation or identity authority. Material being *identity-relevant* does not make it *identity-authoritative*; recognizing alignment with the seed confers no power to change the seed or to self-promote to canon.

`[OBLIGATION] SG-O8 — Recovery preserves authored canon without pinning or locking.` Recovery must preserve authored canonical character state verbatim (Stage A O6) **without** pinning soft guidance into rigid control and **without** blocking future governed revision. Preservation is not a personality lock; reversibility and future governed change remain open.

## 6. Identity / seed / canon-affecting candidate crossing

`[OBLIGATION]` This crossing applies to candidates **seeking an actual seed, identity-tier, canon, promotion, or revision outcome** — not to every ordinary identity-flavored or identity-relevant reflection. `[DISTINCTION]` *identity-relevant ≠ identity-authoritative*: a reflection that merely concerns or aligns with identity is governed as an ordinary candidate unless it seeks one of the actual outcomes above.

`[OPERATOR-RATIFIED]` Where it applies, this crossing is a **stricter parameterization of Document A's governed admission crossing — not a rival crossing.** Admission still belongs to Document A. The seed-governance additions:

```
never auto-admit (no automatic path may admit this class)
operator authorization required for authored seed revision and for automatic or
  candidate-originated seed / identity / canon outcomes, UNLESS a separately ratified
  governance path already owns that canon-source class (e.g., collective-canon /
  quorum / operator materialization — not amended here)
  (audit-only / refused / retired / below-ordinary-identity-effect outcomes need no extra
   authorization beyond Document A's ordinary inspection/audit posture)
recorded, auditable, contestable, reversible
canon-source class must be governance-identifiable at the crossing (§8; no storage repr selected)
default outcome ceiling still bounded by Document A (≤ released/low-authority unless a
  governed promotion crossing applies); seed/identity/canon promotion is never automatic
```

`[DISTINCTION]` Extra requirements ride on top of A's crossing; they do not bypass or duplicate it. A staged candidate that cannot meet these requirements does **not** cross — it stays staged, audit-only, refused, or retired per Document A.

## 7. Governed seed-revision crossing

`[OPERATOR-RATIFIED]` The authored seed may change **only** through a governed seed-revision crossing — a specialized seed-state revision boundary, **not** ordinary-memory admission and **not** a bypass of Document A — that is:

```
operator-authorized (operator-only default; user-co-sign a later stricter option, not required v0.1)
explicit (never a side effect of ingest, reflection, drift, or automatic correction)
lineage-preserving (a seed revision must preserve prior authored seed lineage as governance truth)
auditable (the revision event is inspectable)
contestable (a revision may be objected to per Cluster 2 §12 / Track B vocabulary)
reversible (any later revocation/reversal is itself another governed crossing)
verbatim-recoverable (authored canonical state survives per Stage A O6)
```

`[OBLIGATION]` **Prior authored seed lineage must be retained as governance truth** — a revision may not erase or overwrite the prior authored seed as the record of what the center was. `[NON-AUTHORIZATION]` This selects **no versioning mechanics, schema, store, or serialization**; it fixes only the requirement that prior seed lineage survives.

`[FACT]` The durable substrate already *can* persist a changed seed (`IdentityStore.save`); what is absent is this governance. Seed-Governance fixes the requirement; the writer/lineage **mechanics** route to a later separately authorized track.

## 8. Canon-source taxonomy

`[OBLIGATION]` Canon must be governed by **source meaning**, not by one boolean. The governance-distinct sources (conceptual; from the survey's point-in-time trace):

| Canon source class | Origin (point-in-time) | Governance meaning |
|---|---|---|
| **authored-seed-canon** | `plant_seed` (`mtype=seed_canon`), operator seed at creation | the authored center; revision is §7-governed |
| **drift-correction-canon** | `gravity_correction` (`mtype=drift_correction`), **automatic** | automatic identity reinforcement; requires §9 reconciliation |
| **promotion-canon** | `promote_chunk` (`mtype=identity`/`canon_promotion`), caller-triggered (`force` bypass) | caller-elevated identity-tier; requires §9 reconciliation |
| **collective-canon** | quorum/operator materialization | crossed via distinct-agent quorum or operator; **separately ratified path, not amended here** |

`[OBLIGATION]` Governance must be able to tell these apart when deciding authority, revision, and reconciliation posture, and any future governed crossing must be able to **name which source class it is acting on** (SG-O4). `[NON-AUTHORIZATION]` No new field, enum, schema, or storage representation is named, added, or selected; existing source/type concepts are referenced at requirement level only.

## 9. Automatic writer seam register and later-owner routing

`[FACT]` / `[LATER OWNER]` Named, not patched. Each requires the SG-O5 governed posture before it is treated as conformant; the patch/enforcement belongs to the routed owner. SG-O5 is a not-yet-conformant flag, not a must-patch-now order.

```
gravity_correction            automatic canon=True identity reinforcement (random concept, not rederivable)
                              → requirement: SG-O5 / SG-O6 governed posture
                              → later owner: gravity-correction audit-first reconciliation slice (Document A §11)

_maybe_emit_identity_anchor   automatic derived (canon=False) identity-tier anchor; cognition-reenterable today
                              → ordinary non-canon derived anchors are NOT automatically Seed-Governance crossings
                              → Seed-Governance applies ONLY if such an anchor is later promoted, canonized,
                                used as seed-revision evidence, or given durable identity-authority weight
                              → later owner: P4 O2 reader-side + writer-authority reconciliation

promote_chunk / /promote force  force=True skips evaluation → canon core_identity; upstream auth untraced
                              → `req.force` is a current runtime bypass signal, not Seed-Governance authorization
                              → requirement: SG-O3 stricter crossing applies to identity/canon promotion outcomes
                              → later owner: writer-authority reconciliation slice (patch / enforcement trace)

mood_drift → drift centroid → gravity_correction → canon=True   [COMPOUND HAZARD — named explicitly]
                              automatic soft-guidance-to-identity-canon pathway
                              → not wrong by inspection; not patched here
                              → requirement: SG-O6 (soft guidance must not silently become canon authority)
                              → later owner: gravity-correction audit-first slice + soft-state O6 seam

soft-state O6 tier (mood/warmth/roles/symbol)   durable-soft, non-canon, must-not-pin
                              → requirement: SG-O6 / SG-O8
                              → later owner: Stage A O6 (parked) / P5a
```

`[DISTINCTION]` The compound hazard `mood_drift → drift centroid → gravity_correction → canon=True` is classified as an **automatic soft-guidance-to-identity-canon pathway requiring Seed-Governance requirements plus later audit-first reconciliation** — not condemned as wrong, not patched here.

`[DISTINCTION]` Ordinary non-canon derived identity anchors are **identity-relevant, not identity-authoritative**; they remain primarily a P4 O2 + writer-authority concern and enter Seed-Governance's stricter crossing only on promotion, canonization, use as seed-revision evidence, or grant of durable identity-authority weight.

## 10. Recovery / reversibility / contestability requirements

`[OBLIGATION]` Authored canonical character state survives recovery **verbatim** within committed durability (inherits Stage A O6); soft guidance is not pinned; recovery never blocks a future governed seed revision. A seed revision and its reversal are each their own governed crossing (§7), and prior authored seed lineage is retained as governance truth. Contest of a seed/identity/canon outcome is recorded and constrains future authority outcomes (Cluster 2 §12 / Track B vocabulary); it does not itself rewrite the seed. `[NON-AUTHORIZATION]` Recovery, lineage, and reversal **mechanics** route to Stage A / P5a / P6.

## 11. Explicit non-authorizations

`[NON-AUTHORIZATION]`

```
No implementation. No runtime mutation. No runtime seed writer. No canon-editing mechanics.
No schema. No store. No field names. No serialization. No migration. No database design.
No Stage B. No private cognition loop. No scheduler / trigger / budget. No prompt/retrieval coupling.
No autonomy.
No patch to gravity_correction. No patch to promote_chunk. No patch to _maybe_emit_identity_anchor or mood_drift.
Nothing in this document forces immediate runtime modification of gravity_correction, promote_chunk,
  mood_drift, or derived identity anchors; SG-O5 flags non-conformance, it does not order a patch.
No P4 read-side enforcement. No absorption of the Memory-Engine P1 SRG crystal disposition.
No amendment to Document A / Document B / P4 / Stage A / Cluster 2 / Ledger / MCP boundary.
No amendment to existing separately ratified collective-canon / quorum / operator materialization paths.
No weakening of the MCP Tier-3 seed/identity-rewrite exposure boundary.
```

## 12. Parked seams and later-owner routing

`[LATER OWNER]` / `[PARKED]`

```
seed-revision writer / lineage store / serialization           → separately authorized implementation track
gravity_correction automatic-canon reclassification (patch)     → gravity-correction audit-first slice (Document A §11)
promote_chunk force bypass + upstream auth trace                → writer-authority reconciliation slice
derived identity-anchor source-membership enforcement           → P4 O2 + writer-authority reconciliation
mood_drift → drift → gravity compound chain (patch)             → gravity-correction audit-first slice + Stage A O6 seam
authored-canon verbatim recovery / reversal mechanics           → Stage A O6 (parked) / P5a / P6
SRG is_crystal seed-marker / protection lineage                 → Memory-Engine P1 SRG disposition lane (adjacent; not absorbed)
user-co-sign stricter seed-revision option                      → later stricter revision of this blueprint
```

`[FACT]` **SRG crystal (adjacent / inherited hazard only).** `srg.is_crystal` marks center-crystal (seed) memory and has ungated protection-family readers (registry C7); SRG is default-off and its raw-crystal disposition is owned by the Memory-Engine P1 lane. Seed-Governance names it as an adjacent inherited hazard and does **not** absorb that lane.

## 13. Operator ratification ledger

`[OPERATOR-RATIFIED]` Steering folded into rev0 (2026-06-13, GPT/Hilmir posture):

1. Seed-revision authority — operator-only default; user-co-sign later/optional; operator final authority. → SG-O1 / §7.
2. gravity_correction — Seed-Gov owns the *requirement*; the patch stays the routed audit-first slice. → SG-O5 / §9.
3. Scope vs Document A — specialize the wall for seed/identity/canon; do not amend A. → SG-O3 / §3.
4. Document B Q-a crossing — stricter *parameterization* of A's crossing, not a rival. → §6.
5. Canon taxonomy — govern by source meaning; one boolean insufficient; no new fields. → SG-O4 / §8.
6. SRG crystal — adjacent/inherited hazard only; P1 lane not absorbed. → §12.
7. /promote force — Seed-Gov owns the requirement; writer-authority reconciliation owns the patch. → §9.

`[OPERATOR-RATIFIED]` Draft-review resolutions (2026-06-13, GPT review round — rev0 Q-1…Q-5):

8. **Q-1** — conceptual canon-source taxonomy sufficient for v0.1; any future governed crossing can name its canon-source class; no storage representation selected. → SG-O4 / §8.
9. **Q-2** — operator authorization scoped to actual seed/identity-tier/canon *outcome*, not mere staged observation/refusal/retirement/audit-only retention. → SG-O2 / §6.
10. **Q-3** — prior authored seed retained as durable governed **lineage** (stronger requirement kept). → SG-O1 / §7 / §10.
11. **Q-4** — ordinary non-canon derived anchors not automatically in the stricter crossing; enter only on promotion/canonization/seed-revision-evidence/durable-identity-authority weight. → §4 / §6 / §9.
12. **Q-5** — SG-O5 is a not-yet-conformant flag, not a must-patch-now order. → SG-O5 / §9 / §11.

`[FACT]` **rev2 (2026-06-13, Codex adversarial round):** Codex verdict ACCEPT WITH WORDING CORRECTIONS; no architecture blocker. Five wording-only corrections applied — (1) Canon definition no longer collapses canon==authority (§4); (2) governed seed-revision crossing defined as a specialized seed-state revision boundary, not a Document A bypass, and "versioned" softened to lineage-preserving (§4 / §7); (3) operator-authorization rule corrected to exempt separately ratified canon-source paths, with explicit collective-canon non-amendment (SG-O2 / §6 / §8 / §11); (4) identity-tier-material definition tightened so ordinary non-canon derived anchors are not over-captured (§4, matching §9); (5) `req.force` named as a runtime bypass signal, not Seed-Governance authorization (§9). No architecture changed. GPT verdict on rev2: ACCEPT FOR OPERATOR PROMOTION.

`[OPEN]` No unresolved operator decision blocks this contract; parked later-owner seams remain in §12. Promoted docs-only 2026-06-13; active gate none; next gate unselected.

---

*End TORMENT Seed-Governance Blueprint v0.1. Promoted docs-only requirement-level seed/identity/canon governance contract. No implementation, mechanics, runtime seed writer, schema, store, migration, Stage B, or autonomy authorized. Specializes Document A's wall; amends nothing. Subsequent versions require their own trio ratification.*
