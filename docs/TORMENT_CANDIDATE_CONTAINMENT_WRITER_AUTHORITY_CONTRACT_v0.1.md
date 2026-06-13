# TORMENT Document A — Candidate Containment and Writer-Authority Contract v0.1

**Status:** Requirement-level **write-side** design contract — docs-only. Promoted 2026-06-13. States *what must be true of writers and unadmitted reflection artifacts*; selects no mechanics. Authorizes **no implementation, no runtime Authority Gate, no mechanics, no schema, no store, no field names, no serialization, no database, no storage layout, no model API, no trigger schedule, no budget, no migration, no Stage B, no Document B, and no autonomy.** It is the write-side requirement boundary, paired with P4's read-side boundary; runtime conformance and enforcement are later-owned (P2.5 / a separately authorized implementation track). Windows-visible tracked repo state remains authoritative.

**Lineage:** pre-substrate reconstruction packet (Pass-0 … Pass-1D-R2) → Document A grounding report → grounding closure addendum → scratch contract candidate → first Codex adversarial corrections → operator-ratified admission default → second Codex closure corrections → operator-ratified admission ceiling refinement → three final wording micro-corrections → docs-only promotion (this artifact). The scratch working packet (`scratch/pre_substrate_architecture_reconstruction/2026-06-13/`) remains non-load-bearing evidence lineage.

**Tags:** `[OBLIGATION]` requirement clause · `[DEFINITION]` · `[OPERATOR-RATIFIED]` exact operator-ratified block · `[OPERATOR POSTURE]` operator intent · `[CONTRACT CANDIDATE]` proposed, not yet ratified · `[FACT]` traced runtime fact · `[DISTINCTION]` controlled non-collapse · `[LATER OWNER]` · `[NON-AUTHORIZATION]` · `[OPEN]`.

---

## 0. Status and authority boundary

`[FACT]` This is a **write-side, requirement-level contract**. It states *what must be true of writers and unadmitted reflection artifacts*; it selects no mechanics. It is **not** a runtime Authority Gate, **not** a Cluster 2 amendment, **not** an implementation plan, **not** a candidate-store schema, **not** a database design, **not** a private-cognition (Document B) design.

```
Document A  → write-side requirement boundary
P4          → read-side requirement boundary
later P2.5 / separately authorized implementation track → runtime conformance + enforcement mechanics
```

Authorizes no implementation, schema, store, field names, serialization, storage technology, storage layout, model API, trigger schedule, budget, migration, or autonomy. Opens neither Document B nor Stage B.

---

## 1. Purpose

`[OBLIGATION]` Document A defines the **safe outer boundary** within which a future Layer-2 private-cognition / unified-reflection interior (Document B) may be designed. It answers, at requirement level: *how do future private-reflection artifacts remain bounded, inspectable, and non-authoritative until an explicit governed admission crossing?* It also fixes the **writer-authority** requirement: which writers may create which classes of artifact, and which writers may **not** write directly into ordinary cognition-facing memory.

---

## 2. Standing anchors and controlled distinctions

`[FACT]` Standing anchors, carried exactly:

```
Memory may shape context. Memory may not seize authority.
Audit observes authority. Audit does not become authority.
Preserve continuity without preserving compulsion.
Automatic remains allowed only where separately ratified. Autonomous remains unopened.
```

`[DISTINCTION]` Axis separation:

```
identity influence ≠ canonicality ≠ cognition eligibility ≠ prompt visibility
≠ retrieval opportunity ≠ retrieval priority ≠ promotion rights
≠ writer authority ≠ governance authority
```

`[DISTINCTION]` Writer-side and class non-collapses:

```
creation ≠ admission · admission ≠ promotion · inspection ≠ authority · inspection ≠ projection
contest ≠ resolver · recommendation ≠ application · persistence ≠ cognition eligibility
cognition eligibility ≠ projection permission · projection visibility ≠ identity shaping
canon ≠ governance authority · recovery ≠ admission · recovery ≠ promotion · recovery ≠ cognition eligibility
private thread-continuity state ≠ reflection synthesis ≠ unadmitted reflection candidate ≠ admitted released / low-authority memory
```

`[OBLIGATION]` **Containment invariant (load-bearing, verbatim).**

> Unadmitted reflection artifacts must be unable to influence or re-enter any cognition-shaping, retrieval-shaping, prompt-shaping, affect-shaping, identity-shaping, or projection-reentry path until explicit governed admission.

`[OBLIGATION]` **Chamber nuance.** Private thread continuity may shape its own later synthesis inside the bounded private-reflection chamber. It may not leak into ordinary cognition-shaping machinery before governed admission.

`[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]` **Reconciliation of the older Cluster 2 sentence.** The framing sentence *"The agent may have private transient thought. The agent may not have private persistent influence."* is **refined, not discarded**:

```
bounded chamber-internal thread continuity
 ≠ private persistent influence over ordinary cognition machinery
```

The prohibition targets **ungoverned persistent influence over *ordinary* cognition/identity**. Chamber-internal continuity that is bounded, inspectable, contestable, resettable, and structurally walled from ordinary machinery is permitted; it becomes prohibited only if it reaches ordinary machinery without an explicit governed crossing.

---

## 3. Definitions (requirement level only — no field names, enums, stores, schemas, serialization, or APIs)

- `[DEFINITION]` **Private-reflection chamber** — a bounded region in which private cognition may run and hold working state, structurally separated from ordinary cognition-facing memory and from every ordinary cognition / retrieval / prompt / affect / identity / projection path.
- `[DEFINITION]` **Private thread-continuity state** — chamber-internal **bounded soft continuity** that lets a private thread legitimately continue across turns or idle intervals. It is **not** an admission candidate merely by existing. Soft, inspectable at the level of existence/lineage/status, contestable, resettable; never canonical or authority-bearing.
- `[DEFINITION]` **Raw reflection artifact** — **unsummarized** intermediate reasoning content; ephemeral by default; never durable governed memory automatically.
- `[DEFINITION]` **Reflection synthesis** — a compressed product of reflection. It is an inspectable chamber artifact; it **may become a candidate when explicitly staged for possible crossing**, not before.
- `[DEFINITION]` **Unadmitted reflection candidate** — a synthesis or proposed write (or contradiction / risk flag / unresolved question) that has been **explicitly staged for a possible crossing** but has not crossed governed admission. Subject to the full containment invariant.
- `[DEFINITION]` **Admitted released / low-authority memory** — an artifact that has crossed governed admission into ordinary memory at **no higher than** the released / low-authority class: it may be retained and queryable, but with no identity-shaping weight and no unrestricted promotion rights. (Admission is a *ceiling*, not a guarantee of ordinary-memory entry — see §8.)
- `[DEFINITION]` **Governed admission crossing** — an explicit, governed, recorded, contestable crossing that moves an unadmitted candidate to an ordinary-memory outcome of at most released / low-authority. The only legitimate path out of containment into ordinary memory.
- `[DEFINITION]` **Governed promotion crossing** — a *separate* governed, auditable, contestable crossing required for any upgrade beyond released / low-authority (e.g., toward identity-shaping or canon). Distinct from admission.
- `[DEFINITION]` **Writer authority** — the requirement that a writer be authorized for the *class* of write it performs (ordinary / canonical / identity-shaping / projection / cognition-eligibility). The write-side analogue of P4's read-side obligations. `[FACT]` Today largely absent (payload flags trusted).
- `[DEFINITION]` **Promotion rights** — the Cluster 2 sub-dimension naming what process is needed to upgrade a memory's authority class; candidates default to not-self-promotable.
- `[DEFINITION]` **Inspection** — read-only observation of candidates for audit; observes authority, never becomes authority; **not projection** (§9).
- `[DEFINITION]` **Contest** — a recorded objection that **constrains future authority outcomes**; routes toward low-authority / released / refuse per Cluster 2 §12; does not resolve, apply, admit, or promote.
- `[DEFINITION]` **Recommendation** — a staged proposal that an admission/promotion *could* occur; staging only, never application (Stage A O4: staged recommendation ≠ authority).
- `[DEFINITION]` **Retirement** — dropping or expiring an unadmitted candidate; a scratch-bounded lifecycle action with no cognition effect.

---

## 4. Artifact-class taxonomy

`[OBLIGATION]` Distinct classes with default posture (no mechanics):

| Class | Nature | Default posture |
|---|---|---|
| **Raw reflection artifact** | unsummarized intermediate reasoning | **ephemeral**; never auto-durable |
| **Private thread-continuity state** | chamber-internal bounded continuity | **bounded soft state**; inspectable/contestable/resettable; never pinned (Stage A O6); **not a candidate by existing** |
| **Reflection synthesis** | compressed product | chamber artifact; **becomes a candidate only when explicitly staged** |
| **Unadmitted candidate (staged synthesis / proposed write / contradiction / risk flag / question)** | staged for possible crossing | **candidate-class**; isolated until governed admission |

`[DISTINCTION]` None of these is ordinary memory, canon, identity-tier, or governance authority until a crossing changes its class.

---

## 5. Writer-authority decomposition

`[OBLIGATION]` Distinct writer roles (not collapsible into one "writer"), each mapped onto existing Cluster 2 vocabulary (Authority class / Lifecycle / Promotion rights / Scope / Lane), which is **doctrine-only with no runtime gate**:

| Role | May | Maps onto (Cluster 2) |
|---|---|---|
| artifact creation | create chamber working artifacts | interior (Document B) |
| candidate persistence | persist a staged candidate within the **candidate boundary** (requirement-level vocabulary; no store/lane mechanics selected) | requirement-level isolation |
| candidate revision | revise an unadmitted candidate | — |
| candidate retirement | drop/expire a candidate | Lifecycle (scratch-bounded) |
| candidate inspection | read candidates for audit | audit-only visibility; Ledger boundary |
| candidate contest | object to / constrain a candidate's future authority | Cluster 2 §12 disagreement primitive |
| candidate recommendation | stage (not apply) an admission/promotion | Stage A O4 (stage ≠ authority) |
| governed admission | cross a candidate to ≤ released/low-authority | Promotion rights (operator / user-co-sign / governance) |
| ordinary-memory write | write a non-canon ordinary memory | ordinary ingest |
| canonical write | write `canon=True` | Authority class `persist` + Lifecycle `ratified` |
| identity-shaping write | write seed/anchor/identity-tier/long-HL material | Scope = character/agent |
| projection permission | make a field prompt/caller-visible | P4 O4 |
| cognition-eligibility permission | admit to ordinary cognition | P4 O1/O2 (and `diagnostic_only` **only** where the applicable P4 source-sameness / source-membership failure posture, or inherited P1/P2/Stage-A family-bound posture, requires it) |

---

## 6. Write-side authority obligations

`[OBLIGATION] A-O1 — Class-bound writer authority.` A writer may perform a write only if authorized for that **class**. Authorization must not be inferred solely from payload flags (`canon`, `mtype`, half-life, tier) or from source presence. `[FACT]` Today these are trusted without a writer-authority check.

`[OBLIGATION] A-O2 — No silent canon or identity-shaping from cognition.` No private-cognition / reflection writer may produce `canon=True`, identity-tier, seed, or long-half-life identity material directly. Such writes require a governed promotion crossing.

`[OBLIGATION] A-O3 — Admission is the sole containment exit.` An unadmitted candidate may reach ordinary memory only through a governed admission crossing (§8); no side path may convert it.

`[OBLIGATION] A-O4 — Writer-authority pairs with P4.` Document A's write-side obligations are the matched pair of P4's read-side obligations. `[LATER OWNER]` runtime conformance: P2.5 / separately authorized track.

`[OBLIGATION] A-O5 — Existing automatic writers are named unreconciled seams, not exemptions.` Document A **patches none of them.** Future conformance must bring them under A-O1 / A-O2 through separately authorized reconciliation work (§11).

---

## 7. Candidate-containment obligations

`[OBLIGATION] A-C1 — Non-reachability.` An unadmitted reflection candidate must **not** be able to do any of the following (required non-reachability properties, **not** selected mechanisms):

```
enter ordinary ingest
enter the ordinary private graph
become a motif member
shift the drift centroid
trigger gravity_correction
feed mood_drift
shift role scores
affect anchor cadence
be compressed or deep-exported
accrue spirit warmth
carry SRG metadata into ordinary scoring or warmth paths
influence MemoryPlan lane budgets
enter ordinary retrieval
spread into prompt-visible or caller-visible projection
reach archive→core promotion
write canon
write identity-tier material
reinforce existing ordinary memories
update reinforcement_count
update strength
update last_reinforced metadata
feed feedback overlay
feed bridge-confidence learning
feed retrieval-count promotion signals
feed promotion-suggestion surfaces
silently become ordinary memory through any side path
```

`[FACT]` The ordinary-ingest entry is the **fan-out root** into motif / drift / mood / role / deep / SRG / retrieval, so non-reachability must hold at the ingest entry itself, not only at the graph.

`[OBLIGATION] A-C2 — Structural, not tag-honoring.` Non-reachability must hold by construction; it may not depend on every downstream reader/writer remembering to honor an exclusion tag. `[FACT]` The `ws_section_2a_v1` precedent shows that once material enters ordinary fan-out, auto-emitted identity pressure can occur even when the material was not intended as identity-bearing.

`[OBLIGATION] A-C3 — Throughout-containment inspectability.` Every candidate must remain inspectable, contestable, resettable, and recoverable throughout containment (Stage A O-invariants), without that inspectability itself becoming a re-entry path (§9).

`[OBLIGATION] A-L1 — Lineage and audit safeguards (requirement level; no schema/mechanics).`

```
candidate provenance / lineage must be preserved
lineage preservation does not require raw-reflection exposure by default
admission events must be inspectable
contest history must be preserved
no invisible deletion of persisted inspected / contested / referenced candidates
no recommendation auto-application
no candidate self-promotion
no indirect side-channel influence (per A-C1)
recovery retains class (§9)
```

---

## 8. Governed admission crossing

`[OPERATOR-RATIFIED]` Default admission posture (verbatim):

```
An admitted private-reflection candidate defaults to released / low-authority.

It may enter ordinary memory only through an explicit governed admission crossing.

Admission does not confer canon status.
Admission does not confer identity-shaping weight.
Admission does not confer unrestricted promotion rights.

Any later upgrade beyond released / low-authority requires
a separately governed, auditable, contestable crossing.
```

`[OPERATOR-RATIFIED]` Admission **ceiling** refinement (verbatim):

```
Released / low-authority is the maximum default authority posture
available through ordinary governed admission.

It is not a guarantee that every reflection artifact enters
ordinary retrieval or becomes queryable ordinary memory.

Per-artifact outcomes may be stricter:
chamber-only
audit-only
operator-visible-only
refused
retired

Any ordinary-memory admission must still occur through an explicit
governed, auditable, contestable crossing.

Any later revocation, reclassification, or reversal must occur
through another separately governed crossing.

Inspection is operator-auditable or governance-auditable by default.
It is not model-visible, caller-visible, prompt-visible,
retrieval-visible, or MemoryPlan-visible unless separately
surface-classified and governed.
```

`[OBLIGATION] A-D1.` The admission crossing is an **explicit governed crossing** — recorded and contestable. It is the only governed crossing that may move a candidate to an ordinary-memory outcome, and any such outcome must be no higher than released / low-authority unless a later explicitly ratified doctrine narrows or changes that ceiling. Stricter outcomes (chamber-only / audit-only / operator-visible-only / refused / retired) require no admission.

`[OBLIGATION] A-D2 — Admission ≠ promotion; reversal needs its own crossing.` Admission lands at no higher than released / low-authority. Any move toward identity-shaping or canon is a **separate governed promotion crossing**. Any later **revocation, reclassification, or reversal requires another separately governed crossing** (no direct-reversal semantics are selected here).

`[FACT]` / `[CONTRACT CANDIDATE]` Prior-art boundary (collective proposals):

```
single-agent reflection ≠ multi-agent convergence
borrow collective-proposal isolation shape ≠ inherit collective-proposal shared-canon materialization target
```

`[FACT]` Collective-proposal materialization writes `canon=True` on operator-approval or distinct-agent quorum; reflection candidates **must not** inherit that shared-canon target.

---

## 9. Inspection, contest, recommendation, and retirement boundary

`[OBLIGATION]` Carried: *Audit observes authority. Audit does not become authority.*

Candidate inspection, contest, and recommendation **may**:

```
observe · flag · record · stage
```

They **may not** directly:

```
admit · promote · change retrieval weights · change cognition eligibility
change prompt visibility · change persona · change seed state · change canon status
```

unless a **separately governed crossing** explicitly authorizes the change.

`[OBLIGATION] A-I1 — Inspection ≠ projection.` Inspection defaults to **operator-auditable or governance-auditable visibility only**. It must **not** create prompt-visible, caller-visible, retrieval-visible, cognition-visible, or MemoryPlan-visible exposure unless separately surface-classified and governed.

`[OBLIGATION] A-I2 — Recovery ≠ admission/promotion/cognition-eligibility.` Recovery restores **at most** the prior candidate / retired / audit posture (recovery retains class). Recovery must **not** admit, promote, project, or make cognition-eligible.

`[OBLIGATION] A-I3 — Contest semantics.` Contest records an objection and **constrains future authority outcomes**; it does not resolve, apply, admit, or promote. The resolver boundary is parked (Track B territory). Retirement is a scratch-bounded lifecycle action with no cognition effect.

---

## 10. Chamber-continuity reconciliation

`[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]` The chamber may **preserve its own bounded thread continuity and shape its own later synthesis**; it may **not** leak into ordinary cognition-shaping machinery before governed admission. Bounded chamber-internal continuity is **not** the "private persistent influence" the older sentence prohibits, because that prohibition targets *ungoverned* persistent influence over *ordinary* cognition. The chamber's continuity is permitted precisely because it is bounded, inspectable, contestable, resettable, and structurally walled (A-C1/A-C2) from the ordinary fan-out. This refines the older sentence; it does not discard it.

---

## 11. Existing writer seams and later-owner routing

`[FACT]` **Current traced authority-relevant write-side map** (point-in-time; from the grounding closure addendum, not a timeless claim):

```
canon=True writers (traced):
  1. plant_seed              (creation; operator seed; out of candidate scope)
  2. gravity_correction      (AUTOMATIC; drift-gated; no authority check)
  3. process_proposals       (crossed; distinct-agent quorum)
  4. decide_proposal         (crossed; explicit operator)
  5. promote_chunk           (caller-triggered POST /promote; force bypass)

automatic canon=False identity-tier writer (traced):
  6. _maybe_emit_identity_anchor  (AUTOMATIC; motif-threshold; role-tuned; no authority check)

ordinary ingest:
  → fail-closed for canon today (_auto_canon hardcoded False)
  → still the fan-out root into motif / drift / mood / role / deep / SRG / retrieval

closed fact (traced):
  → add_memory and spawn_memory default canon=False (memory_graph.py:677, :804)
```

`[FACT]` **Promotion seam (precise).**

```
promote_chunk
  → caller-triggered POST /promote path
  → req.force bypass exists today
  → writes canon=True, tier=core_identity, decade half-life (3650d)
  → identity-shaping
  → no further governance/trust check visible in the handler after force
```

`[FACT]` **Affect correction (precise).**

```
promotion emotional criterion
  → computed (classify_affect on chunk text)
  → W_EMOTIONAL = 0.10
  → cannot alone cross threshold 0.60 today
  → non-decisive alone by current constants
  → NOT structurally inert
```

`[OPEN]` `POST /promote` upstream auth surface is **still untraced** → later conformance owner.

`[NON-AUTHORIZATION]` Document A **patches none of these seams.** Routing (without solving):

```
runtime writer-authority enforcement        → P2.5 / separately authorized implementation track
reader source-sameness and projection gating → P4 implementation owner
gravity_correction automatic canon           → dedicated bounded audit-first reconciliation slice
promote_chunk req.force bypass               → dedicated writer-authority reconciliation slice
POST /promote upstream auth surface          → writer-authority reconciliation (untraced)
seed revision                                → Seed-Governance Blueprint
mood / warmth / roles soft-guidance tier     → Stage A O6 later seam
candidate-store carrier/schema/serialization/durability/storage layout → Stage B / P6-shaped mechanics
private cognition interior / dream / incubation / envelope audit / triggers / budgets → Document B
migration                                    → later separately opened phase
autonomy                                     → unopened
```

---

## 12. Relationship to Cluster 2, P4, Stage A, and Ledger doctrine

- **Cluster 2 v0.1** `[DOC]` — supplies the Authority-class / Lifecycle / Promotion-rights / Scope / Lane vocabulary; doctrine-only with a named runtime seam (its v0.2). Document A is **not** a Cluster 2 amendment; it is the write-side requirement boundary a later runtime gate must satisfy.
- **P4** `[DOC]` — the read-side requirement boundary; `diagnostic_only` applies **only** where its source-sameness/source-membership failure posture (or inherited P1/P2/Stage-A family-bound posture) requires it — not as a universal fallback. Document A is its matched write-side pair (A-O4).
- **Stage A** `[DOC]` — O4 (staged recommendation ≠ authority) and O6 (soft-guidance must not be pinned) govern §9 and the soft-state seams.
- **Ledger Observational Boundary** `[DOC]` — *audit observes authority; audit does not become authority* governs §9.
- **MCP capability boundary** `[DOC]` — *automatic allowed where ratified; autonomous unopened* — Document A introduces no autonomy.

---

## 13. Explicit non-authorizations

`[NON-AUTHORIZATION]`

```
No runtime patch. No runtime Authority Gate. No Cluster 2 amendment.
No candidate-store implemented. No schema / field names / enums / serialization selected.
No storage technology / storage layout / database design selected.
No model API / trigger schedule / budget selected.
No private-cognition (Document B) interior designed.
No gravity_correction behavior changed. No promote_chunk behavior changed.
No seed revision implemented. No migration authorized.
No Stage B opened. No autonomy opened. No Document B gate auto-opened.
```

---

## 14. Honest open questions

- `[OPEN]` Does the admission default need per-artifact-class refinement (e.g., contradictions/risk-flags vs. proposed writes), given the now-ratified stricter-than-released outcomes (chamber-only / audit-only / operator-visible-only / refused / retired)?
- `[OPEN]` What authority does the **governed admission crossing** itself require (operator / user-co-sign / governance-required)? Cluster 2 promotion-rights vocabulary applies; the specific requirement is unselected here.
- `[OPEN]` May chamber **inspection** ever be surface-classified to a non-operator audience, or operator/governance-auditable only? (A-I1 default is the latter.)
- `[OPEN]` How are the existing automatic writers constrained **before** their reconciliation slices land — by requirement immediately (A-O5) with runtime timing as later-owner?
- `[OPEN]` `POST /promote` upstream auth surface (untraced) — later conformance owner.
- `[OPEN]` Where exactly is the **Document A ↔ Document B** boundary for thread-continuity state that is both chamber-internal and bounded soft state? Coupled-blueprint seam.

---

## 15. Evidence lineage

`[FACT]` Distilled from the read-only reconstruction packet (non-load-bearing lineage): `DOCUMENT_A_GROUNDING_REPORT.md`, `DOCUMENT_A_GROUNDING_CLOSURE_ADDENDUM.md`, `CODEX_DOCUMENT_A_ADVERSARIAL_REVIEW.md`, `CODEX_DOCUMENT_A_SECOND_PASS_CLOSURE_REVIEW.md`, `PASS_0 … PASS_1D_R2`, `CODEX_CHALLENGE_BRIEF.md` (all in `scratch/pre_substrate_architecture_reconstruction/2026-06-13/`). Durable authority layer (tracked docs): `TORMENT_PRE_SUBSTRATE_ARCHITECTURE_FRAMING_v0.1`, `CLUSTER_2_AUTHORITY_GATE_v0.1`, `..._P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1`, `..._STAGE_A_RECOVERY_RECONCILIATION_SEMANTICS_CONTRACT_v0.1`, `LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1`, `MCP_CAPABILITY_BOUNDARY`, `..._DECISION_REGISTRY_v0.1`. Runtime facts in §11 were personally traced (`character.py`, `fabric.py`, `promotion.py`, `app.py`, `memory_graph.py`, `spirit_return.py`, `roles.py`, `collective_proposals.py`, `scoring.py`, `compression.py`). This contract is promoted docs-only as a requirement-level write-side boundary; it authorizes no implementation, and its runtime conformance is later-owned. The scratch working packet remains non-load-bearing evidence lineage.

---

*End TORMENT Document A — Candidate Containment and Writer-Authority Contract v0.1. Promoted docs-only requirement-level write-side contract candidate. No mechanics, no implementation, no runtime Authority Gate, no Stage B, no Document B, no autonomy. Subsequent versions require their own trio ratification.*
