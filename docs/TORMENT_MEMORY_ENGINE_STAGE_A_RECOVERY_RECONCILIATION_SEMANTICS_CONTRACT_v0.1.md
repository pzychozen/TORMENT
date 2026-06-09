# TORMENT Governed-Memory Substrate Programme
# Stage A — Recovery and Reconciliation Semantics Contract v0.1

**Status:** Stage A requirement-level recovery and reconciliation semantics contract — docs-only. Promoted 2026-06-09. Authorizes no implementation, no substrate mechanics, no database design, no migration, and no Stage B opening. States what must be true of governed-memory recovery, reconciliation, committed-write durability, restoration, per-lane recovery posture, and character-basin preservation; selects no mechanics.

**Lineage:** post-P4 substrate-readiness logistics memo → Stage A / Stage B design-framing report v0.1 → Codex adversarial boundary review → Hilmir three-point values-layer ratification → framing rev1 → GPT four-point micro-correction pass → framing rev2 → mechanics-free contract extraction draft → GPT strict review → Codex adversarial wording review → eight-point wording polish → GPT final promotion-candidate acceptance → docs-only promotion Slice A. The full framing reports, adversarial reviews, and working-folder drafts remain working-folder evidence only and are not promoted.

**Standing anchors (carried together):** Memory may shape context. Memory may not seize authority. Audit observes authority. Audit does not become authority. Automatic allowed where ratified; autonomous not authorized unless separately opened.

**Contract-wide distinctions (collapsing any is drift):** recovery ≠ text-only reread · storage lane ≠ authority class · canonicality ≠ authority · eligibility ≠ projection · projection ≠ cognition admission · `diagnostic_only` ≠ deletion · quarantine ≠ deletion · fingerprint ≠ truth · inventory ≠ authority · era attribution ≠ authority · representability ≠ implementation · guidance-map fact ≠ non-coercion verdict.

---

## 1. Status and authority boundary

[CONTRACT] This is the promoted docs-only Stage A recovery and reconciliation semantics contract. It is requirement-level: it states what must be true, not how. It authorizes no implementation, no substrate mechanics, no database design, no migration, and does not open Stage B.

Closure registration in the decision registry and orientation map is a separate docs-only Slice B. GitHub Issue #54 remains the barrier before database design opens.

## 2. Purpose

[CONTRACT] Stage A fixes the semantics any future TORMENT governed-memory substrate must honor when memory is recovered, reconciled, or restored — *before* Stage B carriers and mechanics are designed. It is layered on P1/P2/P2.5/P4: those phases fixed identity vocabulary, family identity/era attribution, reader/projection safety, and the no-carrier reconciliation finding. Stage A governs what "recovered" means and what must remain visible, auditable, and non-coercive when recovery is partial or unverifiable. It is **not** a storage-architecture memo and selects no storage shape.

## 3. Controlled interpretation boundary

[CONTRACT] The contract is read under the distinctions above and these postures: presence ≠ sameness; surviving bytes ≠ governance ratification; `diagnostic_only` is an eligibility posture, not a projection instruction and not a universal error bin; family-bound interpretation discipline is not a hidden central authority engine. Collapsing any distinction, or treating a descriptive fact (e.g., the guidance influence map) as a ratified verdict, is drift.

[CONTRACT] **Visibility definition.** Unless separately surface-classified, **visibility in this contract means operator-auditable and inspectable visibility**. Visibility does **not** itself require default model-facing disclosure, caller-visible projection, ordinary model-facing notice, or automatic diagnostic projection. ( `diagnostic_only` = eligibility posture; diagnostic projection = explicit surface mechanism; `diagnostic_only` ≠ automatic exposure. ) This preserves P4 exactly: prompt-silent non-admission of an unverifiable reference is permitted when the reference remains operator-auditable and inspectable; ordinary model-facing notice is not required by default.

## 4. Contract obligations

Seven obligations. Each states a requirement; none selects a mechanism. A contract-wide non-coercion/audit invariant (§5) governs all seven and is not an eighth feature.

### O1. Governance-meaning-complete recovery

[CONTRACT — inherited from Cluster 5 §4] A TORMENT memory counts as **recovered only when its governance meaning is recovered with it**; recovery of content text alone is insufficient. **For every recoverable canonical governed-memory record or memory-bearing canonical artifact within Stage A scope**, the applicable governance meaning must remain recoverable with its write-time (or latest-committed) value, interpreted under the applicable era-aware rule (O3). This covers, where applicable: private/shared canonical memories · deep non-authoritative echoes · collective records · future Track B contest-ledger governance records when landed · other memory-bearing canonical artifacts. It **excludes derived artifacts except through their reconciliation and rebuild obligations** (§6), and it does not imply every artifact carries the same governance dimensions or flattens lane semantics. Governance meaning is honored by storage-status class, **not** assumed to be a literal database column:

- **[stored]** — recover from named fields.
- **[composed]** — faithfully recompute from recovered inputs.
- **[doctrine]** — apply the attributable interpretation rule.
- **[derivable]** — recover through the attributable canonical-ledger scan.
- **[future]** — becomes covered when the owning future track lands.

### O2. Family-bound visible failure disposition

[CONTRACT — inherited from P1 ReaderPolicy + P4 O5 + P2 identity axiom] Recovery and reconciliation failures must receive **visible, family-bound ReaderPolicy dispositions** (visibility per §3). There is no universal storage-error bin. A failure must not silently enter cognition and must not invisibly disappear; a readable artifact must not silently become authoritative merely because its bytes survived; a non-readable artifact must not be fictionalized into a readable diagnostic memory. Outcome vocabulary (family-bound read outcomes): `admit_cognition` · `diagnostic_only` · `quarantine` · `refuse_fail_closed` · `raise_fail_loud`. These outcomes do **not** mutate canonical fact, ratify truth, create hidden doctrine, create lifecycle protection, or create hidden authority. Fixed inherited postures are in §6.

### O3. Era-aware recovery and no silent reclassification

[CONTRACT — inherited from P1 era/rollback + P2 serialization-era validity] Recovery must preserve enough era, provenance, governance, policy, migration, rollback, and restoration evidence to **identify which interpretation rule is being applied**, and must keep these attributable where applicable: write-era · latest-committed · current-doctrine · explicit-migrated · explicit-reclassification-event · rollback-declared · restoration-event interpretation. Recovery must **never silently** rewrite authored meaning, reclassify identity-shaping facts, convert historical provenance into present authority, or reinterpret unverifiable evidence as valid. [CONTRACT — inherited from P1] Era attribution is **interpretation context** — not semantic ratification, lifecycle protection, proof of truth, or authority. Migration mechanics are not designed here.

### O4. Explicit audited restoration boundary

[HILMIR-RATIFIED — 2026-06-09] Deterministic automatic restoration is allowed **only when the required evidence is fully proven valid again under the applicable family-bound ReaderPolicy** (ReaderPolicy = family-bound interpretation discipline, **not** a hidden central authority or centralized proof engine). The restoration must create an explicit auditable event and remain inspectable, contestable, and reversible. Ambiguous or judgment-bearing cases may only stage a recommendation or await explicit governance acceptance. No invisible automatic finalizer. Hilmir retains ultimate operator authority. Preserve: automatic restoration under full proof ≠ general autonomous finalization; staged recommendation ≠ authority; audited event ≠ proof of truth; ultimate operator authority ≠ manual approval required for every deterministic recovery. Restoration-event schema and proof mechanics are not selected.

### O5. Committed-write durability promise

[HILMIR-RATIFIED — 2026-06-09] A write may pass through **attempted · accepted · acknowledged · pending · committed** states. Once TORMENT visibly acknowledges a memory as **committed**, it must honestly promise that the committed memory is recoverable after process crash and ordinary OS or power interruption, within the honest guarantees of the local storage hardware. If that promise has not yet been secured, the write must **not** be reported as committed. Any detected durability failure must remain visible and auditable.

[CONTRACT — O5 bound to O1] A governed-memory write may be reported **committed only when the artifacts and evidence required to satisfy O1 governance-meaning-complete recovery are within the committed durability promise**. **Committed bytes without recoverable governance meaning do not satisfy the committed-write promise.**

Explicit external boundary (outside this minimum promise unless separately authorized): external backup · catastrophic hardware failure · replication policy · off-device recovery. Fsync, journal, transaction, commit-protocol, replication, and backup mechanics are not selected — they must *satisfy* this promise, not define it.

### O6. Character-basin preservation without rigid pinning

[HILMIR-RATIFIED — 2026-06-09] **Within the committed durability and recoverability scope fixed by O5, authored canonical character state survives verbatim.** Durable basin-shaping relationship assertions survive, or are faithfully rederived from preserved canonical evidence. Derived relationships may be rebuilt. Genuinely ephemeral modulation may disappear or recompute naturally. **Warmth, mood, drift, symbolic influence, voice-cue inputs, or other soft guidance must not be durably pinned merely because a substrate can store them.** Recovery must never harden guidance into a preservation lock, personality lock, or inability to change direction. [PARKED] The soft-guidance persistence tier — spirit-return warmth state · mood · drift · symbolic influence state · voice-cue inputs where durable state is involved — is **explicitly unsettled**: these may not be silently classified as canonical, silently erased, or durably pinned into rigid control; their precise canonical/derived/ephemeral treatment remains a later technical-and-audit seam. [FACT] `MotifRecord` is the current durable persisted representation; `MotifBasin` is a future/research noun whose tier is unsettled. The separate guidance-without-coercion audit is not reopened.

### O7. Storage-shape freedom under invariant preservation

[CONTRACT — substrate-readiness memo + registry §K] Stage A fixes **semantic invariants, not a permanent storage layout**. Current JSONL, NPY, and SQLite roles are **descriptive evidence** of the present substrate only. A later explicitly authorized Stage B may change storage shape, canonical carriers, sidecars, transaction boundaries, or adapter boundaries — but any such change must preserve governance meaning and the Stage A obligations, and **storage-shape change may not silently become semantic change**. No database is selected.

[EXTRACTION-NOTE — programme-boundary reminder] *TORMENT-governed memory first. Database second. Reusability third.* This reminder prevents generic database convenience from silently pre-answering TORMENT semantics. It does not pre-select an internal-only substrate, reusable package, adapter shape, repository boundary, or database product.

## 5. Contract-wide non-coercion and audit invariant

[CONTRACT / HILMIR-RATIFIED] Governs O1–O7; **not an eighth implementable feature.**

Recovery **may**: withhold an unverifiable memory from cognition admission · quarantine evidence visibly · report visible loss · rebuild derived artifacts from attributable canonical sources.

Recovery **may not**: block output generation merely because one memory cannot be validated · delete evidence invisibly · create covert unauditable suppression of evidence or eligibility state · create authority seizure · create personality lock · harden soft guidance into inability to change direction.

> Audit observes authority. Audit does not become authority.
> Prompt-silent non-admission of an unverifiable memory is **allowed when operator-auditable and inspectable**; silent output blocking is **not authorized**.

## 6. Fixed inherited failure postures

[CONTRACT] The rows explicitly marked **inherited** carry fixed contract-level postures from P1/P2/P4. The remaining rows preserve Stage A requirement boundaries without pretending each family's mechanics or final disposition has already been designed.

| Failure family | Contract-level posture |
|---|---|
| **[inherited P4]** Runtime source-sameness cannot be proven | **`diagnostic_only` cognition eligibility by ratified P4 default** until explicit audited governance restoration; reference remains operator-auditable, inspectable, recoverable |
| **[inherited P2]** Identity-dependent claim with missing / truncated / conflicting / handle-reuse-tainted evidence | Validate from durable evidence or **fail detectably into an explicit non-cognition posture** |
| **[inherited P2 / Hilmir-ratified]** Genesis Baseline IntegrityManifest profile missing, unreadable, or unverifiable | Legacy records remain readable, inspectable, operator-visible, recoverable, never deleted, never silently suppressed. The unverifiable `legacy_precontract` claim defaults to `diagnostic_only`; later explicit recovery or governance action may restore classification |
| **[inherited P1]** Post-genesis durable object lacking a valid attribution path | `diagnostic_only` or `quarantine` until explicitly classified; **never fall back to `legacy_precontract`** |
| **[inherited P1]** Era-ledger integrity violation (duplicate `event_id`, duplicate `event_ordinal`, torn-append evidence, ledger inconsistency) | **Fail closed to `diagnostic_only` or `quarantine`; never silently reinterpret; repair mechanics parked** |
| Unknown or newer schema-bearing envelope version | Never partially interpret; never silently admit to cognition; family shim disposition applies |
| Torn unreadable canonical record | **Visible recovery incident; not automatically a readable diagnostic memory** |
| Missing canonical artifact | **Visible loss** unless an explicit external recovery route exists |
| Derived-sidecar drift or loss | Must be auditable and inspectable. Reconcile or rebuild from attributable canonical sources. **Escalate visibly when** reconciliation/rebuild fails, changes recovered governance meaning, or exposes inconsistency unresolvable from attributable canonical sources. **Successful routine rebuild need not create model-facing disclosure or operator interruption** |
| Orphan artifact | No silent cognition admission; no invisible disappearance; family-specific inspectable handling |
| Clone-lineage uncertainty | Representable and visible; family-bound reconciliation remains parked |

[NON-DECISION] This is not expanded into a mechanics matrix.

## 7. Per-lane recovery boundary

[CONTRACT] Recovery semantics are stated per lane; lanes are not flattened:

- **private / shared** — canonical memory-bearing lanes whose contents retain their **own** governance classifications (recovered with the content; lane membership confers none).
- **deep** — non-authoritative echo lane; recovery must **preserve its non-authority** and never promote an echo because its bytes survived.
- **collective** — opt-in, provenance-bearing, discount-postured lane; recovery must preserve provenance and discount posture.

Carried: storage lane ≠ authority class · canonicality ≠ authority · surviving bytes ≠ governance ratification. Private/shared lane membership is **not** itself authoritative.

## 8. Track B durability relationship

[CONTRACT] Future Track B contest-ledger records must remain recoverable **with their governance meaning** — a durability **input** (the O1 invariant applied to a future ledger). It does **not** absorb Track B v0.2. ( recording disagreement durably ≠ resolving authority; durability input ≠ authority-semantics reopening. ) [PARKED] disagreement semantics · resolver-authority boundary · `candidate_handle → eid` binding · target-existence policy · counter-contest result routing · cognition-coupling decisions.

## 9. Stage B and later-owner routing

[PARKED] Routed, none opened:

- **Stage B / P6-shaped mechanics:** identity carriers · revision fingerprints · serialization · allocator durability · IntegrityManifest mechanics · transaction model · append guarantees · substrate architecture · adapter boundary · packaging evaluation · database evaluation.
- **P5a adjacency:** reconciliation procedure · quarantine procedure · rollback recovery semantics · clone reconciliation · torn-append handling · duplicate repair · partial-restore repair · stored-edge repair adjacency.
- **P7:** conditional compaction questions.
- **P8a / P8b:** research-hypothesis admission benchmarks only.
- **P9:** migration execution · architecture-wide promotion.
- **Maintenance lane:** CodeQL · minor named repairs (separately authorized).
- **Future security layer:** multi-process coordination · at-rest protection · access-boundary hardening · security-paper update after database work.

## 10. Parked technical seams

[PARKED] source-sameness carrier · memory-lineage carrier · record-revision carrier · revision-fingerprint algorithm · serialization profile · allocator durability · IntegrityManifest mechanics · transaction boundary · append guarantee · loader-hardening shape · reconciliation mechanism · quarantine representation · soft-guidance persistence tier · MotifRecord storage realization · MotifBasin future tier · snapshot/compaction posture · TORMENT adapter boundary · packaging boundary · database evaluation. [EXTRACTION-NOTE] These are technical; **no further Hilmir values-layer input is currently required** for Stage A.

## 11. Non-decisions preserved

```
no implementation        no runtime patch         no tests
no executable probe       no git
repo edit limited to this promoted contract artifact only
no additional tracked-doc edits
no registry amendment    no orientation-map edit  no Stage B opening
no database design       no database-product selection
no SQL architecture      no UUID or ULID selection no identity-token structure
no fingerprint algorithm no serialization profile no allocator mechanics
no IntegrityManifest format  no journal format    no transaction design
no fsync strategy        no replication design    no backup design
no snapshot format       no compaction mechanism  no packaging decision
no pip distribution      no repository extraction no migration strategy
no broad security redesign   no security-paper update  no CodeQL fixes
no Track B authority decision    no P3 opening
```

---

## Appendix A. Extraction ledger

Every obligation maps to ratified inherited contract / doctrine / Hilmir posture / mechanics-free recommended boundary. **No obligation required new archaeology; no obligation selects mechanics; no obligation opens Stage B.**

- **O1** ← Cluster 5 §4 governance-meaning recovery invariant + framing rev2 §§5,15.
- **O2** ← P1 ReaderPolicy vocabulary + P4 O5 + P2 identity-dependent-claim axiom + framing rev2 §9.
- **O3** ← P1 era-attribution + rollback posture + P2 serialization-era validity + framing rev2 §16.
- **O4** ← P4 explicit audited restoration adjacency + Hilmir 2026-06-09 restoration-authority ratification + framing rev2 §§7,16.
- **O5** ← Hilmir 2026-06-09 durability ratification + Cluster 5 fragility evidence + framing rev2 §§7,13. **O5 is bound to O1: committed governed-memory durability includes the artifacts and evidence required for governance-meaning-complete recovery.**
- **O6** ← Hilmir 2026-06-09 character-basin ratification + descriptive guidance-map boundary + framing rev2 §§6,18; verbatim survival scoped within the O5 committed durability/recoverability boundary.
- **O7** ← substrate-readiness logistics memo + registry §K + framing rev2 §§3,19,27; programme-priority slogan moved to an EXTRACTION-NOTE, out of the normative clause.

[EXTRACTION-NOTE] Obligation count: **seven obligations + one contract-wide invariant**, matching the design-framing structure (O1–O7 + §5). The §5 non-coercion invariant is kept as a governing invariant rather than an eighth obligation, mirroring the P4 contract's shape (five obligations + one invariant). The §6 fixed-posture table and §7 per-lane boundary are *applications* of O1/O2, not new obligations.

## Appendix B. Hilmir values-layer ratification ledger

[HILMIR-RATIFIED — 2026-06-09]

1. **Committed-write durability promise** (O5) — committed implies honest recoverability after process crash and ordinary OS/power interruption within local-hardware guarantees; not-yet-secured writes are not reported committed; detected durability failures stay visible/auditable; committed durability includes the governance-meaning artifacts required by O1.
2. **Character-basin persistence without rigid pinning** (O6) — authored canonical verbatim within O5 scope; durable basin-shaping assertions preserved or faithfully rederived; derived rebuildable; ephemeral recomputable; soft guidance never durably pinned; soft-guidance tier explicitly unsettled.
3. **Restoration authority** (O4) — deterministic automatic restoration only when required evidence is fully proven valid again under the applicable family-bound ReaderPolicy; explicit auditable event; inspectable; contestable; reversible; staged recommendation or explicit acceptance for ambiguous cases; no invisible automatic finalizer; ultimate operator authority.

## Appendix C. Promotion Slice A status checklist

```
Stage A semantics:             promoted in this artifact
Stage B mechanics:             not opened
database design:               not opened
contract promotion:            promoted in Slice A
registry closure registration: not yet made — separate Slice B
orientation-map edit:          not yet made — separate Slice B
repo edits:                    this contract artifact only
git:                           not run by Claude
tests:                         not run
probes:                        not run
CodeQL:                        not opened
security redesign:             not opened
security-paper update:         not opened
```

## Appendix D. Codex adversarial wording-correction ledger

Eight wording-only corrections carried into this promoted artifact:

1. **O5 committed durability bound to O1 governance-meaning-complete recovery** — committed bytes without recoverable governance meaning do not satisfy the promise.
2. **O4 evidence proven valid under the applicable family-bound ReaderPolicy** — interpretation discipline, not a centralized proof engine.
3. **Visibility = operator-auditable / inspectable unless separately surface-classified** — does not itself require model-facing disclosure or automatic projection.
4. **Fixed inherited rows added** — lost Genesis Baseline anchor (P2/Hilmir) and invalid post-genesis attribution (P1).
5. **O6 character-state verbatim survival scoped within O5** committed durability/recoverability.
6. **Programme-priority slogan moved outside O7** into an EXTRACTION-NOTE.
7. **Derived-sidecar handling proportional** — auditable/inspectable always; visible escalation only when needed; no mandatory noisy interruption for routine successful rebuild.
8. **O1 applicability broadened** — canonical governed-memory records or memory-bearing canonical artifacts within Stage A scope.

No correction changes architecture. No correction selects mechanics. No correction opens Stage B. No correction opens database design.

---

*End Stage A Recovery and Reconciliation Semantics Contract v0.1. Requirement-level design contract, docs-only. No implementation, substrate mechanics, database design, migration, or Stage B opening authorized. Decision-registry and orientation-map closure registration remain a separate docs-only Slice B.*
