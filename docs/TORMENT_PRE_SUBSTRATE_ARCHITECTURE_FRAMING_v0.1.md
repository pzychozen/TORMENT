# TORMENT Pre-Substrate Architecture Framing v0.1 (DRAFT)

> **Draft status.** This is a **scratch draft** of an intended tracked artifact
> (`docs/TORMENT_PRE_SUBSTRATE_ARCHITECTURE_FRAMING_v0.1.md`). It has **not** been
> promoted into `docs/`. It awaits GPT / Hilmir wording review. Until promoted it is
> non-load-bearing local evidence. Windows-visible tracked repo state remains authoritative.

**Tags used throughout:** `[FACT]` · `[OPERATOR POSTURE]` · `[CONTRACT CANDIDATE]` · `[PARKED]` · `[NON-AUTHORIZATION]` · `[LATER OWNER]`.

This artifact is a **framing artifact only**. It preserves a factual reconstruction, the operator values-layer postures, and the containment invariant; it names the next design documents and routes reconciliation seams to later owners. **It selects no mechanics, schemas, storage technology, storage layout, model APIs, trigger schedules, budgets, or prompt formats; it patches no runtime behavior; it amends no Stage A mechanics; it opens no Stage B; it authorizes no migration or implementation.**

---

## 1. Purpose and scope

`[FACT]` This artifact exists because **Stage B substrate mechanics remain paused** (GitHub Issue #54 barrier) while the higher architecture above the substrate — cognition, reflection, identity, and soft continuity — is reconstructed. The pause is over-determined: it was already the repo's posture, and the reconstruction adds the architectural reasons for keeping it.

`[OPERATOR POSTURE]` The governing intent of the pause:

> Do not build a permanent governed-memory substrate around an incomplete model of cognition, reflection, identity, and soft continuity.

`[FACT]` Scope of this artifact: it records *what exists*, *what does not exist*, *which cognition-shaping surfaces must be contained*, *which doctrine tensions must be reconciled*, *which design documents come next*, and *what stays deliberately unopened*. It does not attempt to solve the system.

---

## 2. Standing doctrine anchors

`[FACT]` Carried from promoted doctrine:

```
Memory may shape context. Memory may not seize authority.

Audit observes authority. Audit does not become authority.
```

`[OPERATOR POSTURE]` Carried values-layer anchor:

```
Preserve continuity without preserving compulsion.
```

`[FACT]` Carried capability-boundary posture:

```
Automatic remains allowed only where separately ratified.
Autonomous remains unopened.
```

---

## 3. Factual runtime reconstruction

### Thinking `[FACT]`

- The current live thinking layer is **deterministic routing and retrieval shaping**, not deliberation.
- In the traced live `/agent/query` path, its direct behavior-bearing output is **MemoryPlan lane budget / weight control**; `top_k` may **starve a lane**.
- `mode` / `action` / `draft` / `review` / `stance` / `geometry` are **largely discarded** in the live `/agent/query` path.
- **No meaningful private model-deliberation room exists today.**
- `AgentRunner` (the 8-phase outer loop) is **test/demo-only**, not wired into the live server.

### Reflection `[FACT]`

- **No dream runtime exists.** No offline reflection scheduler exists.
- Cluster-4 is **brainstorm-stable, not promoted**.
- The unified reflection family already prefigured three modes: **Continued Thought**, **Dream / Incubation**, **Envelope Audit**.
- **Spirit reflection** is reactive post-response tracing (external-trigger-only; zero reflection events found in the surveyed workspace), **not dreaming**.

### Seed `[FACT]`

- The authored `seed_text` is **write-once today because no revision writer exists** (not because a lock forbids it).
- It is **prompt-visible and kernel-visible soft influence** (preamble + ±15% kernel modulation).
- `gravity_correction` **auto-writes `canon=True` reinforcement memories today** (drift-gated, randomized seed concept).
- **Derived identity anchors are auto-emitted and cognition-reenterable today.**
- The prior `ws_section_2a_v1` failure (auto-emitted material silently shifting a character's centre of gravity) proves **silent identity-pressure drift is not theoretical**.

---

## 4. Influence-axis separation

`[CONTRACT CANDIDATE]` Grounded in the factual reconstruction:

```
identity influence
≠ canonicality
≠ cognition eligibility
≠ prompt visibility
≠ retrieval opportunity
≠ retrieval priority
≠ promotion rights
≠ writer authority
≠ governance authority
```

```
Not canon does not mean harmless.
Not governance authority does not mean behaviorally inert.
```

---

## 5. Working cognition-shaping family inventory

`[FACT]` / `[CONTRACT CANDIDATE]` This framing records the current working family inventory needed to preserve the reconstruction. The split is deliberately finer than the earlier soft-state bucket, but it is not a frozen schema, storage taxonomy, or mechanics selection. Later design work may refine family boundaries explicitly.

Columns: current status · influence surface · canonical? · durable/ephemeral/parked · current↔future tension · later owner. **No mechanics selected.**

| Family | Current status | Influence surface | Canonical? | Durable/Ephemeral/Parked | Current ↔ future tension | Later owner |
|---|---|---|---|---|---|---|
| **A. Authored identity declaration** (`seed_text`) | implemented (write-once) | prompt-visible + kernel-visible soft influence | classification **OPEN** (own family, not "just canon") | durable | write-once → governed voluntary revision | Seed-Governance Blueprint |
| **B. Canonical seed memories** (`seed_canon`) | implemented (planted at creation) | core-tier prompt + retrieval | canonical | durable | canonicality ≠ authority (class open) | Seed-Governance / Cluster 2 §10 |
| **C. Gravity-correction canon memories** | implemented, **automatic** (drift-gated) | core-tier prompt + retrieval | canonical **today (contested)** | durable; **not safely rebuildable** (randomized) | automatic-canon vs "canon never automatic" | Gravity-correction audit-first slice |
| **D. Derived identity anchors** | implemented, **automatic** (motif) | derived-tier prompt + retrieval; **cognition-reenterable today** | non-canonical | durable | reenterable-today → P4 proof-or-`diagnostic_only` | P4 reader-side + P2.5 writer |
| **E. Mood / affect continuity** (`mood_drift`) | implemented, **default-on** automatic writer | retrieval scoring bonus; feeds drift centroid | non-canonical | durable | behavior-bearing but ungoverned writer | P2.5 writer + Stage A O6 soft tier |
| **F. Durable spirit-return warmth** | implemented (`warmup_state.jsonl`) | warmth → hit strength → ranking; return-mode → prompt block placement | non-canonical | **durable-soft (O6 PARKED)** | durable-soft must-not-pin | Stage A O6 soft-guidance seam |
| **G. Durable role inference** | implemented (`roles.json`, updated from ingest text) | modulates identity-anchor cadence (count/gap) → indirectly retrieval/prompt | non-canonical | durable-soft | ungoverned soft writer modulating identity cadence | Stage A O6 soft tier + P2.5 writer |
| **H. Optional SRG resonance** | implemented, **default-off** | default-off symbolic / retrieval-shaping influence; SRG metadata may amplify spirit-return resonance / warmth; query-time mutation persistence scope remains a later implementation-level trace item | non-canonical | persistence scope TBD (watch item) | watch-item amplification | Document A containment + O6 |
| **I. Compression / deep-export projections** | implemented, **default-off** | deep-export projection with possible deep-lane reentry; exact reentry filtering remains a later implementation-level trace item | non-canonical (**protects** canon/seed/anchor; not a canon writer) | derived / rebuildable | deep-reentry watch item | Stage A §6 rebuild + Document A |
| **J. Collective proposal candidates** | implemented | **none pre-materialization** (isolated store); shared canon only after an authorized crossing (operator-approval or distinct-agent quorum route) | non-canonical until materialized | durable (pending store) | isolation prior art; analogy-break (materializes shared canon) | Document A (prior art) + Cluster 2 gate |
| **K. Future private-thread continuity** (Layer-2 active) | **absent** | may shape **its own** later synthesis inside the chamber; barred from ordinary machinery | non-canonical | bounded-soft (resettable; must not pin) | may shape later expression yet remain non-authority (B1) | Document A boundary + Document B |
| **L. Future reflection artifacts** (synthesis / candidates) | **absent** | none until admitted | non-canonical until admitted | candidate-class (durable-inspectable, separate) | explicit governed admission required | Document A + Document B |
| **M. Governed admitted memory** | implemented (ordinary graph) | full cognition / prompt / retrieval | per Cluster 2 class | durable | writer-authority enforcement (who may admit) | P2.5 + Cluster 2 |
| **N. Diagnostic-only eligibility posture** | P4-ratified posture (mechanics parked) | none (not cognition-eligible) until audited restoration | non-canonical | per recovery posture | restoration mechanics | P5a + P4 |

---

## 6. Locked operator postures

### Private cognition horizon `[OPERATOR POSTURE]`

```
Layer 0 — deterministic routing and retrieval shaping
Layer 1 — private per-turn deliberation
Layer 2 — temporally extended reflection across turns or idle intervals
```

**Layer 2 is the intended long-term horizon.**

### Silence `[OPERATOR POSTURE]`

```
Silence may be a cognitive action.
```

A later separately opened design may allow TORMENT to continue thinking, resume a thread, compress accumulated reflection, surface a later synthesis, or remain silent.

### Unified reflection family `[OPERATOR POSTURE]`

```
Continued Thought
Dream / Incubation
Envelope Audit
```

**Dreaming is one mode of the broader Layer-2 reflection surface, not a separate subsystem.**

### Two regimes `[OPERATOR POSTURE]`

```
Regime A — active continuity
Regime B — offline reflection
```

One governance skeleton; different budgets / triggers / interruption rules to be designed later.

### Persistent private continuity `[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]`

```
The agent may preserve bounded private thread continuity.
That continuity may influence later cognition and expression.
It may not quietly become hidden authority, hidden canon, irreversible identity pressure, or an uninspectable second memory system.
```

### Thread-continuity nuance `[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]`

```
Private thread continuity may shape its own later synthesis inside the bounded private-reflection chamber.
It may not leak into ordinary cognition-shaping machinery before governed admission.
```

### Candidate containment `[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]`

```
Unadmitted reflection artifacts must be unable to influence or re-enter any cognition-shaping, retrieval-shaping, prompt-shaping, affect-shaping, identity-shaping, or projection-reentry path until explicit governed admission.
```

---

## 7. Explicit containment checklist

`[FACT]` / `[CONTRACT CANDIDATE]` The reconstruction confirmed or conservatively retained the following surfaces as explicit containment watch items. Document A must close non-reachability against each relevant surface before reflection mechanics are authorized:

```
mood_drift
spirit warmth / warmup
deep export
compression
SRG resonance
SRG crystal / heartbeat metadata amplification
collective echo
motif clustering
identity-anchor emission
role-score shift → anchor cadence
drift centroid
retrieval-opportunity weights
```

`[PARKED]` Whether containment is enforced by structural separation, capability gating, or another mechanism is **not decided here** — it is Document A's work.

---

## 8. Existing candidate prior art

`[FACT]` Collective proposals provide one existing isolation precedent:

```
collective proposals
→ separate pending store
→ no ordinary cognition / retrieval integration identified before materialization
→ explicit operator-approval route
→ separate distinct-agent quorum route exists
→ shared canon materialization only after an authorized crossing
```

`[FACT]` The analogy break (do not over-borrow):

```
Reflection candidates may borrow the isolation shape.
They must not inherit shared-canon materialization as their default admission target.
Single-agent reflection is not multi-agent convergence.
```

---

## 9. Reconciliation seams and later owners

Named, not solved.

- **Automatic-canon seam.** `[FACT]` Current `gravity_correction` automatic `canon=True`. `[LATER OWNER]` Later bounded **audit-first reconciliation slice**.
- **Writer-authority seam.** `[FACT]` Payload flags and identity weights are trusted without a writer-authority check. `[LATER OWNER]` **Document A + P2.5** writer-side reconciliation.
- **Reader-side seam.** `[FACT]` Derived anchors are currently cognition-reenterable. `[LATER OWNER]` / `[CONTRACT CANDIDATE]` **P4** ratified requirement requires source-membership proof or `diagnostic_only`; runtime enforcement remains future / later-owner work.
- **Authored-seed seam.** `[FACT]` Write-once today. `[LATER OWNER]` Future governed versioned voluntary revision — **Seed-Governance Blueprint**.
- **Soft-state recovery seam.** `[FACT]` Mood, warmth, roles, future Layer-2 thread continuity. `[LATER OWNER]` **Stage A O6 PARKED tier** — soft guidance must not be durably pinned into rigid control.
- **Reflection-candidate seam.** `[OPERATOR POSTURE]` / `[CONTRACT CANDIDATE]` Unadmitted reflection artifacts require a separate inspectable candidate boundary before ordinary cognition influence. `[LATER OWNER]` **Document A**.

---

## 10. Next design documents

`[LATER OWNER]`

```
Document A — Candidate Containment and Writer-Authority Contract
Document B — Private Cognition and Unified Reflection Blueprint
Seed-Governance Blueprint
Matched P2.5 writer / P4 reader reconciliation blueprint
Gravity-correction audit-first reconciliation slice
```

```
If separately opened, Document A defines the safe boundary.
If separately opened, Document B defines the mind inside it.
```

---

## 11. Programme order

`[LATER OWNER]` Recommended dependency order (not an implementation schedule):

```
tracked framing artifact
→ Document A
→ Document B
→ Seed-Governance Blueprint
→ matched writer / reader reconciliation blueprint
→ gravity-correction audit-first reconciliation slice
→ trio free-design council
→ start/examples overhaul
→ Stage B substrate mechanics
```

---

## 12. Explicit non-authorizations

`[NON-AUTHORIZATION]`

```
No runtime patch authorized.
No database mechanics authorized.
No storage technology selected.
No schema selected.
No migration authorized.
No candidate store implemented.
No private cognition implemented.
No dream scheduler implemented.
No seed revision implemented.
No gravity-correction behavior changed.
No Stage B opened.
No autonomy opened.
No Document A gate auto-opened.
No Document B gate auto-opened.
No seed-governance gate auto-opened.
```

---

## 13. Evidence lineage

`[FACT]` This framing is distilled from the read-only reconstruction packet:

```
scratch\pre_substrate_architecture_reconstruction\2026-06-13\
PASS_0_COVERAGE_MAP.md
PASS_1A_THINKING_LAYER_REALITY_MAP.md
PASS_1B_DREAM_OFFLINE_REFLECTION_REALITY_MAP.md
PASS_1C_IDENTITY_SEED_CHARACTER_BASIN_REALITY_MAP.md
PASS_1D_CROSS_SYSTEM_DOCTRINE_INTERACTION_MAP.md
PASS_1D_R1_RECONCILED_MAP.md
PASS_1D_R2_PERSONAL_CONFIRMATION.md
codex\CODEX_CHALLENGE_BRIEF.md
```

`[FACT]` These scratch artifacts remain **non-load-bearing evidence lineage**. They are preserved for audit history; they are not promoted doctrine and do not authorize implementation. Only this framing artifact, once promoted by explicit trio decision, becomes tracked. Even then it authorizes no implementation and auto-opens no subsequent design gate. Sections 10–11 record the eligible next design sequence; each later document still requires a separate bounded opening decision.

---

*End DRAFT TORMENT Pre-Substrate Architecture Framing v0.1. Scratch draft, awaiting GPT / Hilmir wording review. No tracked promotion, no mechanics, no Stage B.*
