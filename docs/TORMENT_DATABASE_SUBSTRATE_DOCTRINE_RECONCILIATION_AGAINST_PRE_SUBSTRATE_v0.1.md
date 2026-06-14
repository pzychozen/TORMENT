# TORMENT Database/Substrate Doctrine Reconciliation Against Pre-Substrate Architecture v0.1

**Status:** Requirement-level **reconciliation / compatibility-audit** memo — docs-only.
**Promoted docs-only 2026-06-14.** States *what a future database/substrate
doctrine must already understand about the closed pre-substrate stack before Stage B can ever
be separately opened*; it selects no mechanics. Authorizes **no implementation, no Stage B, no
database design, no schema, no store, no field names, no storage technology, no storage layout,
no carrier, no enum, no serialization, no migration, no runtime mechanics, no enforcement
mechanics, no MCP action surface, and no autonomy.** It is a compatibility audit conducted
*before* mechanics; runtime conformance and any substrate mechanics are later-owned. This memo
makes **no registry amendment.** Windows-visible tracked repo state remains authoritative.

**Review state:** Codex ACCEPT WITH REQUIRED CORRECTIONS (2026-06-14) — four substrate-leakage
wording fixes applied (§10 routing labels; §11 seams 10 and 11; §14 tension 7); no architecture
changed. Codex ACCEPT on re-review. GPT ACCEPT FOR PROMOTION CANDIDATE (2026-06-14). Promoted
docs-only 2026-06-14; closure registered at registry §N12. Subsequent versions require their own
trio ratification.

**Authoritative state at drafting:** HEAD = origin/main = `06eb81c` (top commit:
*docs(engine): promote bounded defensive availability invariant*). Active gate before this:
none. Stage B unopened; database/substrate mechanics unopened; implementation unopened;
schema/store/migration/storage-product selection unselected.

**Mandatory wording lock (load-bearing, verbatim):**

> This reconciliation may identify constraints on any later substrate proposal. It may not
> choose, imply, prepare, or privilege substrate mechanics.

**Mandatory label-evidence clause (load-bearing, verbatim):**

> Existing runtime or doctrine labels may be cited only as evidence of current seams. This
> gate creates no new field names, endorses no existing field as a future representation, and
> treats all such labels as non-design evidence.

**Lineage:** pre-substrate reconstruction packet (Pass-0 … Pass-1D-R2) → the five promoted
pre-substrate contracts (framing, Document A, Document B, Seed-Governance, No-Corner) → the
accepted working-folder planning artifact
(`scratch/pre_substrate_architecture_reconstruction/2026-06-14/DB_SUBSTRATE_DOCTRINE_RECONCILIATION_AGAINST_PRE_SUBSTRATE_v0.1_PLAN.md`,
rev1, Codex ACCEPT WITH CORRECTIONS) → this promoted memo. The planning artifact and
the scratch packet remain **non-load-bearing evidence lineage**; this memo does not promote
them and is not a substitute for the contracts it reconciles.

**Tags:** `[DOCTRINE]` ratified upstream doctrine · `[OPERATOR POSTURE]` operator values-layer
input · `[CONSTRAINT]` later-substrate constraint identified by this reconciliation ·
`[NON-COLLAPSE]` future-representation non-collapse constraint · `[EPHEMERAL]` must-not-persist
requirement · `[INSPECT-BOUNDARY]` provisional inspectable-not-model-visible boundary item ·
`[ROUTING]` not-this-gate routing · `[PARKED]` parked seam / dependency-scoped blocker ·
`[FINDING]` evidence, not authority · `[TENSION]` · `[NON-AUTHORIZATION]` · `[LABEL-EVIDENCE]`
existing label cited as seam evidence only.

---

## 1. Status and non-authorization boundary

This is a **docs-only, reconciliation-only** memo. It is a compatibility audit performed
*before* any mechanics. It is **not** a database design, **not** a Stage B opening, **not** a
schema/store/carrier proposal, **not** an implementation plan, **not** a runtime conformance or
enforcement layer, **not** an MCP action surface, **not** an autonomy doctrine, and **not** a
registry amendment.

`[NON-AUTHORIZATION]` Opens no Stage B. Opens no database/substrate mechanics. Opens no
implementation. Selects no schema, store, field name, storage technology, storage layout,
carrier, enum, serialization, or migration. Amends no upstream contract (Document A / Document B
/ Seed-Governance / No-Corner / P4 / P2.5 / Stage A / Cluster 2 / Ledger / MCP boundary).
Amends the Memory-Engine Decision Registry in no way. Opens no gate beyond this docs-only
reconciliation gate.

`[NON-AUTHORIZATION]` Every classification in this memo — every register row, matrix cell, and
label — is a **working reconciliation label, not a frozen taxonomy** and not a new authority,
storage, or visibility class.

The mandatory wording lock and label-evidence clause above govern the entire memo.

## 2. Purpose: compatibility audit before mechanics

`[FINDING]` The pre-substrate stack closed five contracts (Document A, Document B,
Seed-Governance, No-Corner) under one framing, on top of the previously promoted P4 / P2.5 /
Stage A / Cluster 2 / Ledger / MCP doctrine, while **Stage B substrate mechanics remained
paused** (registry §N6; GitHub Issue #54 checkpoint barrier). The risk this memo addresses: a
later substrate proposal — or a runtime-adjacent slice that precedes it — could silently encode
assumptions the closed stack forbids, because the stack states its requirements in
contract-language scattered across ten artifacts and never in one substrate-facing inventory.

`[CONSTRAINT]` This memo answers one question without acting on it: **what must a future
database/substrate doctrine already understand about the closed pre-substrate stack before
Stage B can ever be separately opened?** It produces (a) the inherited conceptual invariants,
(b) a later-substrate-constraint register, (c) the future-representation non-collapse
constraints, (d) the ephemerality / must-not-persist requirements, (e) the provisional
inspectable-not-model-visible boundary, (f) the not-this-gate routing, (g) the parked seams that
block dependent substrate mechanics, and (h) a working compatibility inventory. It selects no
mechanics for any of them.

## 3. Source stack and inherited role assignments

`[DOCTRINE]` Reconciled artifacts (all under `torment_fabric/docs/` unless noted):

- `TORMENT_PRE_SUBSTRATE_ARCHITECTURE_FRAMING_v0.1.md` — umbrella; family inventory A–N;
  containment checklist; seams and later owners.
- `TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md` — **Document A**.
- `TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md` — **Document B**.
- `TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md` — **Seed-Governance**.
- `TORMENT_BOUNDED_DEFENSIVE_AVAILABILITY_NO_CORNER_INVARIANT_v0.1.md` — **No-Corner**.
- `TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md` — **P4**.
- `TORMENT_MEMORY_ENGINE_P2_5_CROSS_CONTRACT_RECONCILIATION_v0.1.md` — **P2.5**.
- `TORMENT_MEMORY_ENGINE_STAGE_A_RECOVERY_RECONCILIATION_SEMANTICS_CONTRACT_v0.1.md` — **Stage A**.
- `CLUSTER_2_AUTHORITY_GATE_v0.1.md` — **Cluster 2**.
- `LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md` — **Ledger**.
- `MCP_CAPABILITY_BOUNDARY.md` — **MCP boundary**.
- `TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md` — **Registry** (anti-drift reference; §N5–N11
  register P4 / Stage A / Document A / Document B / Seed-Governance / No-Corner).

`[DOCTRINE]` Inherited role assignments (carried exactly; this memo does not redefine them):

```
Document A     → write-side containment wall
P4             → read-side projection / cognition-eligibility window
Document B     → private-cognition interior (inside A, behind P4) — not implementation
Seed-Governance→ seed / identity / canon governance — not a rewrite mechanism
No-Corner      → bounded defensive availability — not autonomy or monitoring
Stage A        → recovery / reconciliation semantics
Cluster 2      → authority / lifecycle / promotion-rights / scope / lane vocabulary
Ledger         → audit observes authority; audit does not become authority
MCP boundary   → automatic only where separately ratified; autonomous remains unopened
```

## 4. Standing anchors (doctrine vs operator posture)

`[DOCTRINE]` Carried doctrinal anchors (each is ratified doctrine with its own amendment cadence):

```
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit does not become authority.
Automatic remains allowed only where separately ratified. Autonomous remains unopened.
```

`[OPERATOR POSTURE]` Carried operator values-layer postures (revisable only by Hilmir; the trio
may design or revise mechanisms intended to satisfy them, per registry §B / E10):

```
Preserve continuity without preserving compulsion.
The agent may not seize authority. The agent also may not be architected as helpless.
Control means absolute / coercive blocking; guidance is allowed; the soul cannot be quietly rewritten.
```

`[FINDING]` These anchors are **compatible with any later substrate as-is**: none selects a
representation, and a substrate that violated any of them would be non-conformant by definition.
The reconciliation work is to ensure a later substrate proposal *carries* them, not to encode
them now.

## 5. Conceptual invariants (no representation selected)

`[CONSTRAINT]` The following are substrate-neutral distinctions that constrain *meaning*, not
storage. A later substrate doctrine inherits them as invariants; **none selects or requires a
representation**, and this memo selects none.

`[NON-COLLAPSE]` Influence-axis separation (framing §4; Document A §2):

```
identity influence ≠ canonicality ≠ cognition eligibility ≠ prompt visibility
≠ retrieval opportunity ≠ retrieval priority ≠ promotion rights
≠ writer authority ≠ governance authority
```

`[NON-COLLAPSE]` Write-side / class non-collapses (Document A §2):

```
creation ≠ admission · admission ≠ promotion · inspection ≠ authority · inspection ≠ projection
contest ≠ resolver · recommendation ≠ application · persistence ≠ cognition eligibility
canon ≠ governance authority · recovery ≠ admission/promotion/cognition-eligibility
private thread-continuity state ≠ reflection synthesis ≠ unadmitted candidate
  ≠ admitted released/low-authority memory
```

`[NON-COLLAPSE]` Seed-Governance desired-posture set (Seed-Governance §4):

```
identity-relevant ≠ identity-authoritative · seed resonance ≠ seed mutation
canon-affecting insight ≠ canon admission · recognition ≠ authority · guidance ≠ control
```

`[CONSTRAINT]` Carried meaning-anchors that a substrate must not contradict: "Not canon does
not mean harmless; not governance authority does not mean behaviorally inert" (framing §4); and
"a TORMENT memory is not recovered unless its governance meaning is recovered" (Cluster 5 / Stage
A anchor; registry E4).

## 6. Later-substrate-constraint register

`[CONSTRAINT]` Requirements that **may constrain any later substrate proposal** — i.e. they may
impose constraints on a later substrate only if and when Stage B is separately opened. Each is
named and routed; **no carrier, representation, or mechanic is selected.**

| # | Constraint (requirement level) | Grounding | Later owner |
|---|---|---|---|
| C-1 | A candidate boundary must be expressible as an inspectable, isolated region | Document A §3; framing fam. J/L | Stage B / P6 |
| C-2 | Candidate and seed-revision lineage / provenance must be preservable | Document A A-L1; Seed-Governance §7 | Stage B / P6; Seed-Gov mechanics later-owner |
| C-3 | Contest history must be preservable | Document A A-L1; Cluster 2 §12 | Stage B / P6; Track B adjacency |
| C-4 | Governed admission-crossing records must be representable as recorded, contestable, reversible | Document A §8 (A-D1/A-D2) | Stage B / P6 |
| C-5 | Canon-source class must remain governance-distinguishable | Seed-Governance SG-O4 / §8 | Stage B / P6 (representation unselected) |
| C-6 | Chamber-continuity status must be representable as resettable + inspectable at existence/lineage/status level | Document B B-O2 / B-O2.1; framing fam. K | Stage B / P6; Stage A O6 seam |
| C-7 | Recovery must be governance-meaning-complete without pinning | Stage A O1/O5/O6; Seed-Governance SG-O8 | P5a / Stage B-P6 |
| C-8 | Era-aware recovery / no silent reclassification must be supportable | Stage A O3; registry EraEvent vocabulary | P5a / P6; P9 migration adjacency |
| C-9 | Durable-soft families (mood/warmth/roles) must be representable as durable yet never pinned, never authority-bearing | framing fam. E–G; Stage A O6; registry §N7 | Stage A O6 seam / P5a |

`[LABEL-EVIDENCE]` Where the grounding cites an existing runtime concept (e.g. `EraEvent`,
canon-source labels), it is cited only as evidence of the current seam; this gate creates no new
field names and endorses no existing field as a future representation.

## 7. Future-representation non-collapse constraints

`[NON-COLLAPSE]` These are the **representation integrity invariants**: pairs a later substrate
proposal must not collapse. A later substrate proposal is checked against this list; **no field
is named, and no representation is selected or implied here.** This is the most load-bearing
section for a future substrate, expressed entirely at requirement level.

A later representation must **not** collapse:

```
identity influence            ↔ canonicality                         (framing §4)
canonicality                  ↔ governance authority                 (Document A §2; Seed-Gov §4)
canon-as-single-flag          ↔ canon-by-source-class                (Seed-Gov SG-O4 / §8)
cognition eligibility         ↔ prompt / caller / retrieval visibility (P4 O3/O4; Document A §8)
inspection                    ↔ projection                           (Document A A-I1; B-O8; P4 O3/O4)
persistence                   ↔ cognition eligibility                (Document A §2; registry E4 anchor)
defensive audit               ↔ user-risk / reputation scoring        (No-Corner NC-O10 / §11)
chamber thread-continuity     ↔ ordinary memory                      (Document A §3/§4; B-O2)
private thread-continuity ↔ synthesis ↔ unadmitted candidate ↔ admitted released/low-authority
                                                                     (Document A §2 four-way split)
seed resonance                ↔ seed mutation                        (Seed-Gov §4)
storage lane                  ↔ authority class                      (Stage A anti-drift; registry §N6)
diagnostic_only (eligibility posture) ↔ projection / deletion / suppression
                                                                     (P4 anti-drift; registry §H, §N5)
automatic                     ↔ autonomous                           (MCP boundary; framing §2)
```

`[NON-AUTHORIZATION]` Naming these non-collapses does not authorize building separation
mechanisms for them. Whether a later substrate enforces a non-collapse by structure, by
governance, or otherwise is **not decided here.**

## 8. Ephemerality / must-not-persist requirements

`[EPHEMERAL]` Requirements that must **not** become durable records by default. The memo
preserves these as non-durable-by-default requirements and must not select how any later
substrate would satisfy them; a later substrate must additionally never persist them as a side
effect, and must never auto-promote them.

- Raw reflection artifacts — "unsummarized intermediate reasoning; ephemeral by default; never
  durable governed memory automatically" (Document A §3; Document B B-O3).
- Inside-turn expression and withdrawal — "ephemeral and need not be logged" (No-Corner NC-O11).
- Provisional non-admission of identity-shaping claims — "creates no candidate record, audit
  write, durable non-admission, basin exclusion, retrieval change, authority change, or
  future-treatment rule" (No-Corner NC-O8 / §8).
- Withheld-synthesis (silence) footprint — permitted, **not mandatory**; "mandatory footprints
  would risk forcing durability/recovery mechanics too early" (Document B B-O10.1).
- Durable defensive classification absent a governed crossing (No-Corner NC-O11 / §12).
- Ephemeral modulation — `tri_mod` multipliers, cycle-stage transients: "never persist as
  durable state; recompute naturally" (registry §N7 soft-state postures).
- Any audit-derived statistic / summary / embedding / hash as a runtime-readable durable input
  (Ledger §3; Document B B-O6 Ledger binding).

`[FINDING]` Whether the defensive-audit footprint persists *at all* is **not yet decided**
(No-Corner §13 routes "defensive-audit persistence representation (if ever) → governed admission
+ Ledger-aligned later work"); a later substrate must not assume it persists.

## 9. Provisional inspectable-not-model-visible boundary

`[INSPECT-BOUNDARY]` A recurring surface across the stack needs operator/governance audit
visibility **without** becoming prompt, retrieval, cognition, or MemoryPlan input. This memo
labels it the **provisional inspectable-not-model-visible boundary**. *This is a provisional
reconciliation label, not a new authority class, storage class, visibility class, or registry
amendment.*

Items that fall in this boundary (working inventory, not a frozen set):

- Candidate lineage / provenance (Document A A-L1; A-C3 "throughout-containment inspectability").
- Candidate contest history (Document A A-L1; Cluster 2 §12).
- Withheld-synthesis footprint (Document B B-O10 / §9 — "never read by the runtime to alter
  subsequent live behavior").
- Chamber-continuity existence / status (Document B B-O2; Document A §3).
- Defensive-audit evidence (No-Corner NC-O10 / §11 — evidence-only).
- Governed crossing records (Document A §8 — "recorded and contestable").

`[NON-COLLAPSE]` Binding constraint on all of the above (Document A A-I1; Document B B-O8; P4
O3/O4; Ledger §5): inspection defaults to **operator-auditable or governance-auditable only**;
it is *not* model-visible, caller-visible, prompt-visible, retrieval-visible, or
MemoryPlan-visible unless separately surface-classified and governed; and inspectability must
not itself become a re-entry path. **No model visibility may be derived from inspectability.**

`[PARKED]` The stack has **no settled noun** for this surface (registry §H controlled vocabulary
contains none). Naming it durably is itself a parked seam (§11); the label here is provisional.

## 10. Not-this-gate routing table

`[ROUTING]` Requirements that belong to later runtime/implementation tracks — **not** this memo,
**not** a substrate design, and **not** this gate. Listed so substrate work does not absorb
runtime enforcement and runtime slices do not smuggle in storage commitments.

```
P4 projection / cognition-eligibility enforcement (O1–O5 + non-coercion invariant)
                                                  → runtime conformance, later-owned (registry §N5)
class-bound writer-authority checks (Document A A-O1/A-O4)
                                                  → P2.5 / separately authorized implementation track
candidate-boundary / chamber-continuity / admission-crossing mechanics
                                                  → Stage B / P6 (Document A §11)
No-Corner runtime availability of the defensive floor (NC-O1/NC-O6)
                                                  → later runtime conformance
gravity_correction automatic-canon reconciliation
                                                  → gravity-correction audit-first slice (framing §9; Document A §11; Seed-Gov §9)
live prompt/retrieval coupling for Regime A continuity (Document B B-O5/B-O5.1)
                                                  → P4 / Cluster 2 / cognition-coupling lane
seed-revision writer / lineage mechanics
                                                  → Seed-Governance later-owner / Stage B-P6
recovery / reconciliation / quarantine mechanics
                                                  → P5a
migration execution
                                                  → P9
```

## 11. Parked seams and dependency-scoped blockers

`[PARKED]` Open questions that **block substrate mechanics that would depend on these seams.**
None blocks further docs-only reconciliation, operator review, or separately bounded
non-mechanical gates. Each is named, not solved; none is a database design task in this memo.

1. What counts as the **candidate boundary** at requirement level without selecting a store?
   (Document A §3; A §11 routes carrier to Stage B/P6.)
2. How is **lineage preserved without raw-reflection exposure** by default? (Document A A-L1;
   Document B B-O8.)
3. How is **canon-source class governance-identifiable** without prematurely choosing a
   representation? (Seed-Governance SG-O4 / §8 — "v0.1 selects no storage representation.")
4. How is **authored seed canon preserved verbatim** (Stage A O6) without a personality lock or
   blocking governed revision? (Seed-Governance SG-O8; No-Corner NC-O9.)
5. How is **chamber continuity resettable + inspectable** without hidden persistent influence?
   (Document B B-O2/B-O2.1 — durable cross-session continuity is "a later governed question.")
6. How is **audit supported without audit becoming authority**, including for absence/silence?
   (Ledger §3; Document B B-O10; Document A A-I1.)
7. How is **defensive availability supported without a durable user-risk score / retrieval
   penalty / reputation memory**? (No-Corner NC-O10 / §11–§12.)
8. The compound hazard `mood_drift → drift centroid → gravity_correction → canon=True` — an
   automatic soft-guidance-to-identity-canon pathway requiring reconciliation before any
   substrate persists its products (Seed-Governance §9; Document A §11).
9. SRG `is_crystal` protection lineage — adjacent, Memory-Engine-P1-owned, **not absorbed**
   (Seed-Governance §12; registry C7) — must not be frozen into first-class substrate
   (registry §N7).
10. Allocator / `eid` reuse + `DeepMemoryEcho` presence-only validation (registry C20; P2.5 §N3)
    — durable-sameness overload must be resolved before any later durable representation of echo
    sameness or candidate-boundary state.
11. The provisional inspectable-not-model-visible boundary (§9) has **no settled noun** —
    before any later proposal represents this boundary, the stack needs either a governed
    vocabulary decision or an explicit decision to keep the label provisional.

`[LABEL-EVIDENCE]` Seams 8–11 cite existing runtime labels (`mood_drift`, `gravity_correction`,
`is_crystal`, `eid`, `DeepMemoryEcho`) only as evidence of current seams; this gate endorses
none as a future representation.

## 12. Compatibility matrix (working inventory only)

`[FINDING]` A working inventory, **not authority and not a frozen taxonomy**. One row per source
artifact; columns are the working reconciliation labels of this memo:
*conceptual only · later-substrate constraint · forbidden shortcut (non-collapse) ·
must-not-persist · inspectable-not-model-visible · later runtime conformance ·
parked-before-dependent-mechanics.*

| Artifact | Primary reconciliation weight (working labels) |
|---|---|
| **Document A** | non-collapse (heavy); must-not-persist (raw reflection); inspectable-not-model-visible (candidate lineage/contest); parked (candidate boundary, §11.1) |
| **Document B** | must-not-persist (raw reflection, silence footprint); inspectable-not-model-visible (chamber status, withheld footprint); parked (durable cross-session continuity, §11.5) |
| **Seed-Governance** | non-collapse (canon-by-source); later-substrate constraint (seed lineage); parked (canon-source representation, compound hazard, §11.3/§11.8) |
| **No-Corner** | must-not-persist (inside-turn moves, provisional non-admission); inspectable-not-model-visible (defensive-audit evidence); non-collapse (no durable user-risk score) |
| **P4** | later runtime conformance (dominant); non-collapse (inspection≠projection; `diagnostic_only` posture) |
| **P2.5** | later runtime conformance (writer-site stamping); parked (analogue ≠ canonical carrier; §11.10) |
| **Stage A** | later-substrate constraint (governance-meaning-complete recovery); non-collapse (storage-lane ≠ authority-class); parked (recovery mechanics → P5a/P6) |
| **Cluster 2** | conceptual only (vocabulary); later-substrate constraint (promotion-rights, §12) |
| **Ledger** | non-collapse (audit ≠ authority); must-not-persist (audit-as-runtime-input) |
| **MCP boundary** | conceptual only; non-collapse (automatic ≠ autonomous); hard red line (no action surface; Tier-3 seed/identity never exposed) |

## 13. Findings (evidence, not authority)

`[FINDING]` These findings are **evidence for a later trio decision, not authority over it.**

- **Compatible as-is.** The standing anchors (§4), the conceptual invariants (§5), the
  automatic≠autonomous boundary, and the Ledger observational invariant carry forward unchanged.
  No conflict between the closed stack and a *future* substrate doctrine is detected at the
  conceptual layer.
- **Requires wording clarification before mechanics (see §14).** The chamber-continuity vs
  "private persistent influence" refinement; canon-as-single-flag vs canon-by-source; the
  durable-soft vs must-not-pin pairing; the unnamed inspectable-not-model-visible boundary.
- **Requires later reconciliation (runtime / slice owners).** Every §10 routing item; the
  gravity_correction compound hazard; the `eid` / echo sameness overload.
- **Blocks substrate mechanics that would depend on these seams.** The §11 parked seams gate any
  dependent substrate mechanics; they do not block further docs-only reconciliation, operator
  review, or separately bounded non-mechanical gates. None is a substrate design task in this
  memo; each is a requirement a later substrate proposal must be able to *state it will honor*
  before mechanics open.

## 14. Tensions / stale assumptions

`[TENSION]` Identified for adversarial review; each is a wording or assumption risk a later
substrate proposal could trip over.

1. **Chamber continuity vs "private persistent influence."** Document A §10 and Document B
   *refine* (not discard) the older Cluster-2 sentence "private transient thought yes, private
   persistent influence no." A later substrate must inherit the refined reading or it will
   mis-encode the chamber as either ordinary memory or as forbidden. **Collision risk: high if
   read literally.**
2. **Canon single-flag.** Seed-Governance SG-O4 declares one `canon` flag insufficient
   governance truth, while the *current* runtime (Seed-Governance §2 finding; Document A §11
   trace) carries one flag across four source classes. A later substrate that carries the single
   flag forward as-is would silently violate SG-O4. `[LABEL-EVIDENCE]` Stated as seam evidence;
   no field or representation is proposed here. **Stale assumption to flag.**
3. **Durable-soft families.** framing fam. E–G mark mood/warmth/roles durable yet ungoverned;
   Stage A O6 and registry §N7 require durable-soft to never pin. A later substrate must hold
   "durable" and "never authority / never pinned" simultaneously — a representation tension, not
   resolved here.
4. **The inspectable-not-model-visible boundary has no settled noun.** Document A A-I1, Document B
   B-O8, P4 O3/O4, and Ledger §5 describe one surface without a shared name; registry §H has no
   first-class noun for it. The label used here is provisional. **Naming gap → drift risk.**
5. **`diagnostic_only` overload.** Used by P4 (sameness failure), registry §H (lost-anchor), and
   Stage A — an *eligibility posture*, never projection/deletion/suppression. Easy to collapse
   into a single status value by a later substrate. **Anti-drift wording must travel with it.**
6. **Defensive-audit persistence ambiguity.** No-Corner §13 leaves it undecided whether
   defensive audit persists at all; a later substrate must not assume it does.
7. **Automatic carve-outs vs autonomous.** The MCP boundary permits "bounded automatic behavior
   (escalation, governance checks)" while the framing keeps autonomous unopened. Any later
   proposal that accounts for automatic-writer outputs must not let "automatic" drift toward
   "autonomous." Keep separated.

## 15. Non-authorizations and red lines

`[NON-AUTHORIZATION]` This memo authorizes none of the following, and must not be read as
implying, preparing, or privileging any of them:

```
No Stage B.
No database design.
No schema, storage layout, field, enum, carrier, migration, or store selection.
No storage technology selection.
No implementation, enforcement, runtime conformance, or patch.
No model visibility derived from inspectability.
No audit-derived authority (Ledger §3 carried).
No No-Corner monitoring, notification, MCP action, autonomy, or user-risk memory.
No Seed-Governance rewrite mechanism, personality lock, or veto over governed operator revision.
No chamber continuity as ordinary memory or hidden persistent influence.
No automatic-to-autonomous drift.
No registry amendment.
No gate opened by this memo beyond this docs-only reconciliation gate.
```

`[NON-AUTHORIZATION]` All classifications in this memo are **working reconciliation labels, not
frozen taxonomy.** Reaffirmed boundaries: keep automatic vs autonomous separated; keep audit
observing authority and never becoming it; keep "control = absolute/coercive blocking" while
guidance stays allowed; keep the seven distinct concepts (identity influence, canonicality,
cognition eligibility, prompt visibility, retrieval priority, writer authority, governance
authority) uncollapsed.

The mandatory wording lock governs: *This reconciliation may identify constraints on any later
substrate proposal. It may not choose, imply, prepare, or privilege substrate mechanics.*

## 16. Sequencing recommendation (advisory only)

`[ROUTING]` Per framing §10–11 and registry §N6 (no auto-open; each step requires its own bounded
decision):

```
this reconciliation memo (docs-only; promoted)
→ matched P2.5 writer / P4 reader reconciliation
→ gravity_correction audit-first reconciliation slice
→ trio free-design council review
→ Stage B / database mechanics ONLY after the above + Issue #54 clean-checkpoint
```

This sequencing recommendation is **advisory.** It opens no next gate and does not make this
memo an authority over gate selection.

## 17. Evidence lineage

`[FINDING]` Distilled from: the five promoted pre-substrate contracts (framing, Document A,
Document B, Seed-Governance, No-Corner); the Memory-Engine Decision Registry v0.1 in full
(incl. §N5–N11); the Ledger Observational-Boundary Doctrine v0.1; the MCP Capability Boundary;
and the P4 / P2.5 / Stage A / Cluster 2 content (read directly and cross-read via registry
§N3/N5/N6 and the dependency tables inside Documents A/B/Seed-Governance/No-Corner). The
accepted working-folder planning artifact (rev1, Codex ACCEPT WITH CORRECTIONS) is the drafting
scaffold and remains **non-load-bearing evidence**. This memo authorizes nothing and amends
nothing; runtime conformance and any substrate mechanics are later-owned.

---

*End TORMENT Database/Substrate Doctrine Reconciliation Against Pre-Substrate Architecture v0.1
(promoted docs-only). docs-only · reconciliation-only · compatibility-audit-before-mechanics.
No Stage B, no database design, no schema/store/carrier/migration, no implementation, no MCP
action surface, no autonomy, no registry amendment. All classifications are working reconciliation
labels, not frozen taxonomy. Promotion is a separate trio decision; subsequent versions require
their own trio ratification.*
