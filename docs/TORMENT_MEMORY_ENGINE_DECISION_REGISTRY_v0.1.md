# TORMENT Memory Engine — Decision Registry and Vocabulary Discipline v0.1

**Status:** P0 artifact. Anti-drift reference. NOT doctrine, NOT a schema,
NOT implementation authorization. Every later engine phase cites this
document; no later phase silently amends it.
**Date:** 2026-06-06 · amended 2026-06-07 (P1 closure amendment — docs-only Slice B; see §N1) · amended 2026-06-07 (P2 closure amendment — docs-only Slice B; see §N2) · amended 2026-06-07 (P2.5 closure registration — docs-only; see §N3) · amended 2026-06-07 (pre-P4 reader-dependency trace registration — docs-only; see §N4) · amended 2026-06-09 (P4 contract promotion and closure registration — docs-only; see §N5) · amended 2026-06-09 (Stage A recovery/reconciliation semantics contract promotion and closure registration — docs-only; see §N6) · amended 2026-06-09 (thinking-layer archaeology: ratified soft-state continuity postures + parked private-thinking-layer seam — docs-only; see §N7) · amended 2026-06-13 (Document A — Candidate Containment and Writer-Authority Contract promotion and closure registration — docs-only; see §N8)
**Lineage:** Eight-report design-archaeology arc (R1 roadmap recovery; R2
deep pressure; KA kernel anatomy; KP kernel-persistence addendum; SRG-A SRG
runtime/ethics/era audit; C-SRG Codex SRG review; DP-A deep-projection
audit; C-DP Codex deep-projection verification) → work-programme draft →
trio decision to open P0 only → P0 amendment pass → operator promotion.
**Citation keys:** [R1] [R2] [KA] [KP] [SRG-A] [C-SRG] [DP-A] [C-DP],
plus tracked docs by path.

## Quick reference (future-chat orientation)

| | |
|---|---|
| **Active gate** | none — P0, P1, P2, P2.5 closed; P4 contract promoted and closed at `dbdbc30`; Governed-Memory Substrate Programme Stage A Recovery and Reconciliation Semantics Contract promoted and closed at `2bf3b29` |
| **Next gate** | unselected — Stage A is closed; no next gate is auto-opened. Stage B mechanics and database design remain unopened. Selecting any next active slice requires deliberate trio steering and the Issue #54 clean-checkpoint boundary |
| **Registry classes** | FACT · POSTURE · DOCTRINE · OPERATOR INTENT · PARKED QUESTION · RESEARCH HYPOTHESIS |
| **Current graph** | P0 → P1 → P2 → P2.5 → P4 → P3 → P5a → P6 → P7 → P8a → P9 → P10 → P11 |
| **Side lanes** | P5b (after P5a, alongside P6) · P8b (after P8a, non-blocking) · maintenance (separately authorized) |
| **Three hard non-goals** | no implementation · no storage-product selection · no Stage B or database-design auto-open |

---

## A. Purpose and anti-drift rule

This registry exists so the engine programme never re-litigates settled
ground or silently promotes unsettled ground. The anti-drift rule:

>  A claim may be used as load-bearing input to a later phase only in the
>  class recorded here. Promotion or demotion between classes is itself a
>  registry amendment: a small docs slice with trio sign-off.

P0's scope is exactly four things: this decision registry, the controlled
vocabulary (§H), the revised phase dependency graph (§I), and the
maintenance-versus-evidence routing table (§J). Nothing else is P0.

Registry row format (all registries below):
**Item** · CLASS · *Source* · Reason · Negative constraint ·
Authority-to-change · Dependent phase(s) · Revisit trigger.

## B. Decision-class vocabulary

- **VERIFIED FACT** — code- or paper-grounded, line-cited, adversarially
  reviewable. Changes only with new code/paper evidence.
- **PROVISIONAL DESIGN POSTURE** — a working design intent agreed in trio
  discussion; NOT ratified. A posture may guide phase drafting, but may
  not be cited as settled authority until its owning phase ratifies or
  revises it. Changes by trio decision at the owning phase's gate.
- **RATIFIED DOCTRINE** — promoted, tracked `docs/` artifacts. Changes only
  by the audit-first amendment cadence of the doctrine itself.
- **OPERATOR INTENT (PROVIDED)** — Hilmir's values-layer input, recorded in
  tracked docs; not to be reopened as missing. Underlying operator intent
  may be revised only by Hilmir. The trio may design, reject, or revise
  mechanisms intended to satisfy that intent; those mechanisms remain
  postures or doctrine according to their own class. The three layers —
  values-layer input, mechanism choice, ratified doctrine — are distinct
  and must not be conflated.
- **PARKED QUESTION** — genuinely open; owned by a named phase; answering
  it elsewhere is drift.
- **RESEARCH HYPOTHESIS** — admissible to canonical semantics only through
  the P8a/P8b benchmark gate.

No silent promotion of workshop conclusions into doctrine. No silent
demotion of verified facts into open questions.

## C. Verified facts registry

C1. **TriOctaMemoryKernel is live and load-bearing** · FACT · *[KA][KP];
fabric.py:674,695,2839* · grounds the organism claim · do not describe the
kernel as optional · evidence-only · P2,P3,P6 · contradicting code change.

C2. **Kernel shell posture is in-memory during ordinary runtime** · FACT ·
*[KP §A]; fabric.py:784* · shell continuity gap is real · do not assume any
posture survives restart · evidence-only · P3 · restore wiring lands.

C3. **Checkpoint save exists (auto + endpoint); full ModelState/monitor/
runtime-context serialization** · FACT · *[KP]; checkpoint.py:116–216,
fabric.py:3409, app.py:1683* · snapshot format is a real asset · do not
treat checkpoints as a recovery *system* · evidence-only · P3 · —.

C4. **Production restore is not wired into ordinary restart**; restore
functions exist with zero callers · FACT · *[KP]; checkpoint.py:394,435;
repo-wide caller search* · "fresh awakening" is current behavior, not yet a
chosen design · do not claim resume exists · evidence-only · P3 ·
restore-roundtrip characterization (routed §J).

C5. **SRG is default-off at the main gate** (`TORMENT_SRG_ENABLE=0`) ·
FACT · *[SRG-A]; fabric.py:716* · — · do not call SRG "running" in
production narratives · evidence-only · P1 · env default change.

C6. **SRG stamps are canonical, versionless, era-unmarked**; unknown keys
silently filtered on read · FACT · *[SRG-A §G]; srg_engine.py:130–151* ·
proves the era-contract need · no new versionless feature stamps ·
evidence-only · P1 · schema fields added.

C7. **Some canonical-payload SRG readers remain ungated**:
protection-family readers and influence-family readers exist outside the
main SRG enable gate (lifecycle.py:983–985; compression.py:399–400,
482–484; compression.py:626–637). Q2-D admitted crystal as a legacy
protection marker, but **P1 must decide what provenance, if any, allows an
SRG crystal claim to become durable lifecycle / governance protection** ·
FACT · *[SRG-A §C][C-SRG]* · disable does not currently disable; the
protection lineage is admitted-but-unresolved · **do not treat a raw
experimental `srg.is_crystal` claim as legitimate durable protection
without the P1 provenance decision** · evidence-only · P1 · reader-policy
and provenance decision.
**P1 disposition (2026-06-07, amendment):** the verified fact stands —
ungated canonical-payload SRG readers exist. The ratified contract
disposition: raw historical `srg.is_crystal` remains visible for
provenance but inert as a direct behavior input when SRG is disabled;
historical `srg.is_crystal` must not automatically become active
lifecycle protection; a future separately authorized migration may stage
an auditable protection recommendation; recommendation != lifecycle
truth; recommendation != automatic ratification. See
`docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md`
§5–§6. Migration mechanics remain parked.

C8. **The cognition SRG gate defaults ON** (`TORMENT_SRG_COGNITION=1`),
contradicting the main gate · FACT · *[SRG-A]; thinking_controller.py:196,
410* · gate semantics are inconsistent · do not add further SRG gates
pre-P1 · evidence-only · P1; maintenance candidate §J · default change.
**P1 refinement (2026-06-07, amendment):** `TORMENT_SRG_COGNITION`
currently gates `plan.retrieve_srg_state`; repo-wide archaeology found
zero read sites for `retrieve_srg_state`; the contradiction is presently
semantic and drives a dormant flag. Default reconciliation remains a
separately ratifiable maintenance candidate (§J). No patch authorized.

C9. **RSB exists with no ordinary-runtime coupling** (migrated, dormant;
zero imports outside kernel/) · FACT · *[KP §C][KA §F]* · tail engine is
available, unwired · do not describe RSB as live · evidence-only · P8a ·
any runtime import.

C10. **RGD is research lineage only behind a fixed heuristic** (60/40 at
compression.py:640; comments :436,:639; no settling-time code) · FACT ·
*[KP §D]* · the memo must use the conservative wording verbatim · never
write "RGD is implemented" · evidence-only · P7,P8a · RGD code lands.

C11. **Deep export uses one 25-key conditional allowlist** (deep_memory.py
:221–242; single constructor; no post-mutations) · FACT · *[DP-A §B]
[C-DP]* · supersedes the earlier 27 miscount · do not cite 27 · evidence-
only · P4 · allowlist change.

C12. **`srg` is absent from the current 25-key DeepMemoryStore export
allowlist. Therefore the spirit-return SRG reader is unreachable on the
ordinary live projection-mediated deep lane** (spirit_return.py:335–336,
356). **Historical or nonstandard deep records may still require scan
evidence** · FACT · *[DP-A §F]* · narrows C7 to payload-direct readers ·
do not describe spirit-return SRG as an active leak, and do not declare it
historically clean, before the §J scan · evidence-only · P1,P4 ·
historical scan result (§J).
**Scan evidence (2026-06-07, amendment):** Windows historical deep-store
scan: `metadata.srg` matches: 0. Classification: local authoritative
corpus evidence only. Negative constraint: do not claim global absence;
copied workspaces, external archives, and future imports remain
uncharacterized.

C13. **Normal deep retrieval requires source-row presence** (beta filter,
fabric.py:3679–3712) · FACT · *[DP-A §C]* · non-authority is structurally
enforced · do not weaken without P4 · evidence-only · P4 · —.

C14. **Normal deep hits carry a constructed non-authoritative marker**
(authority_status: authoritative=false / requires_rehydration=true /
role=retrieval_echo; fabric.py:3721–3742) · FACT · *[DP-A §E]* · — ·
echoes must never be read as authority · evidence-only · P4 · —.

C15. **Raw diagnostic deep reads are a separate surface**: `recall()`,
`list_orphaned_deep_hits`, and `POST /workspace/{workspace_id}/deep-memory/
query` (app.py:2218; endpoint existence verified in the P0 amendment
pass). These may return raw deep records outside the normal cognition-path
source-row gate and authority-status construction.
**RawDiagnosticRead != cognition-eligible retrieval** · FACT ·
*[DP-A §C][C-DP]; app.py:2218* · the diagnostics/cognition distinction
exists but is not uniformly fenced · keep the surfaces visibly distinct;
P4 owns the fencing contract · evidence-only · P4 · —.

C16. **Source-row loss suppresses deep echoes safely but silently** (filter
`continue`; no counter, no audit event) · FACT · *[DP-A §H]* · safe ≠
observable · do not add ad-hoc signals outside P4/maintenance routing ·
evidence-only · P4; maintenance candidate §J · counter lands.

C17. **affect_attribution crosses the projection as a self-versioned nested
envelope, verbatim, with fail-loud affect_tag pairing; affect_conf is
carried but deliberately unsurfaced** · FACT · *[DP-A §G]; fabric.py:
3744–3764; deep_memory.py:233–241* · the one ratified governance-adjacent
crossing · never re-synthesize on read · evidence-only · P4 · D1-S5 work.

C18. **SRG / TGMO / RPCO / REFU lineage is real. ω₀ = 0.244 numerically
corresponds to theta_lock = 0.244.** This row records three strands
separately: (i) paper-grounded lineage (SRG built from the three operators;
Zenodo 18285147/17253999); (ii) live-code fingerprints (REFU as the named
reinforcement stage, rsb_model.py:33,302,337; RPCO as the L₀=9 bound,
srg_engine.py:52; TGMO not migrated); (iii) interpretive connection (the
integration spec's reading of the shared constant). **It does not make
research constants canonical storage facts or TORMENT-calibrated
parameters** · FACT (strands i–ii) + recorded interpretation (strand iii) ·
*[KA §C–D]; docs/archive/SRG_INTEGRATION_SPEC.md* · anatomy grounding ·
do not present research constants as TORMENT-calibrated · evidence-only ·
P8a,P9 · —.

C19. **Compression preserves the canonical row** (short path = additive
patch; long path = thin projection + row retained; protected classes never
weakened) and **reclaims no storage in the live path** · FACT · *[R2 §A
Findings 2–3]; compression.py:795–862* · baseline for P7 · do not describe
current compression as volume relief · evidence-only · P7 · executor change.

C20. **H-1: MemoryNode `eid` is a reusable local handle, not durable
identity — mechanically confirmed** by operator-run Windows disposable
characterization (2026-06-07, verdict `H1_CONFIRMED`). Clean *complete*
trailing-row loss from `nodes.jsonl` can reduce surviving `max_eid`;
`MemoryGraph` reload derives `world._next_id = max surviving eid + 1`
(memory_graph.py:535,553,599), so a new unrelated memory can receive a
previously used local `eid`. `DeepMemoryEcho` borrows the integer `eid`
without source-sameness evidence, and the presence-only deep beta filter
(fabric.py:3708–3710) can re-admit the stale echo once an unrelated new
node reuses that `eid` · FACT (bounded) · *P2 opening survey 2026-06-07;
H-1 characterization 2026-06-07; memory_graph.py:535,553,599;
fabric.py:3708–3710; migration/cursor.py:40–54* · grounds the P2 identity
contract · **does not prove historical corruption in the real corpus; does
not authorize an H-1 runtime patch; does not select UUIDs/ULIDs/allocators/
fingerprint algorithms/manifests-on-disk/fsync/transactions/storage
product** · evidence-only · P2 (closed at contract level), P4 (echo
source-sameness, diagnostic fencing, projection filtering), P5a (recovery
adjacency), P6 (durability mechanics), P9 (migration execution adjacency) ·
contradicting code change.

## D. Provisional design postures registry

(All rows: CLASS = POSTURE · *Source: trio workshop conclusions recorded in
the work-programme draft + report recommendations* · Authority-to-change =
trio at owning phase gate. Per §B: postures guide drafting; they are not
settled authority until their owning phase ratifies or revises them.)

**Shell continuity** (owning phase P3; revisit trigger: P3 ratification)
D1. Default layered continuity. D2. Stable identity durable. D3. Meaningful
shell transitions eligible for durable records. D4. Transient shell posture
ephemeral by default. D5. Full checkpoint resume explicit and operator-
visible. D6. Safety fallback: fresh awakening. · Negative constraint
(shared): no durable shell record may become an invisible influence
surface; P3 must address the Bucket-I adjacency explicitly.

**SRG** (owning phase P1 — gate ratified 2026-06-07; dispositions per the
P1 contract `docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md`)
D7. SRG remains a valid optional guidance layer — carried forward.
D8. **Resolved at contract level by P1.** When SRG is disabled: audit
visibility allowed; diagnostic visibility allowed; historical provenance
allowed; direct raw-SRG protection disabled; direct raw-SRG influence
disabled; query-time mutation from raw SRG disabled.
D9. Historical stamps remain auditable — carried forward and satisfied by
the P1 contract.
D10. **Resolved at contract level by P1.** Raw historical
`srg.is_crystal` does not automatically become active lifecycle
protection; a future separately authorized migration may stage an
auditable recommendation only; recommendations remain inspectable,
contestable, acceptable, revisable, and revocable; no invisible automatic
finalizer.
D11. **Non-decision** — the enabled-state forced-resonance mechanism
remains unresolved (mechanism-shaping satisfaction of operator intent
E10, not doctrine).
D12. **Split explicitly.** Disabled-state raw-SRG mutation is resolved:
disabled. The enabled-state question remains unresolved — derived
non-authoritative evolution versus explicit locked event-sourced
evolution; P5a owns recovery / integrity semantics.
D13. **Satisfied at contract level by P1.** One unified append-only era
ledger per workspace; EraEvent vocabulary ratified; implementation
remains parked.
· Negative constraint (shared): **No SRG runtime edit is authorized by
this registry amendment.**

**Deep projection** (owning phase P4; trigger: P4 gate)
D14. DeepMemoryEcho is persistent but non-authoritative. D15. Source
MemoryNode presence required for cognition entry. D16. The 25-key allowlist
is the v1 baseline instance of a future versioned DeepProjectionContract.
D17. Raw diagnostics remain visibly distinct from cognition-eligible
retrieval. D18. Orphaned echoes remain blocked but become visibly reported.
D19. Nested schema-bearing projections preserve their own validated
versions. · Negative constraint: the live allowlist is not edited pre-P4.

**Cross-cutting**
D20. **Audit-projection rule** — "every meaningful automated transformation
must produce a truthful human-auditable projection" · POSTURE · *Source:
R2 §E/§I; trio discussion* · staged routing: **P5a defines the integrity
and recovery implications; P9 evaluates full architecture-wide promotion** ·
trigger: P5a gate (implications), P9 gate (promotion).
D21. **Customization principle** — capability does not imply universal
activation · POSTURE (preserved future framing) · *Source:
scratch 2026-05-30 phase-prep handoff §3 (local-only); echoed in tracked
orientation map lineage* · trigger: any persona/capability layer phase.

## E. Existing ratified doctrine carried forward

(CLASS = DOCTRINE except E10; authority-to-change = each doctrine's own
amendment cadence; these are inputs to every phase.)

E1. Track A v0.1 — Truthfulness Envelope (`docs/TRACK_A_TRUTHFULNESS_
ENVELOPE_v0.1.md`). E2. Cluster 2 v0.1 — Authority Gate. E3. Track B v0.1 —
Disagreement Runtime. E4. Cluster 5 v0.1 — Storage/Survivability, including
the §5 fragility handles, §6.2 deferred mechanism list, §7 pre-automation
guarantees, and the anchor: *a TORMENT memory is not recovered unless its
governance meaning is recovered.* E5. Ledger Observational-Boundary
Doctrine v0.1 — *audit observes authority; audit does not become
authority* — applied per [R2]/[KA] to storage tooling (verify, quarantine,
ledgers, recovery console). E6. Q2-D tool-result canon-suppression +
lifecycle protection chain (crystal admitted as a legacy protection
marker; provenance resolution owed to P1 per C7). E7. MCP capability
boundary (memory surface, not autonomous agent). E8. Ledger Persistence
Decision Option C (response-only observability). E9. Doctrinal kernels:
*memory may shape context, may not seize authority* (+ 2026-05-28
sharpening). E10. **Operator intent (provided)** · OPERATOR INTENT class ·
guidance allowed; influence ≠ coercion; control = absolute/coercive
blocking; option-to-ignore load-bearing; no silent output blocking,
authority seizure, or invisible personality lock · *Source: orientation map
anti-drift §2 point 4; SRG-A commission* · underlying intent revisable only
by Hilmir; mechanisms satisfying it (e.g., D8, D10, D11) remain postures or
doctrine per their own class.

## F. Parked questions registry

(CLASS = PARKED; answering outside the owning phase is drift.)

F1. Durability bar (operator intent) → P5a. F2. Inspectability permanence →
P5a/P9. F3. Retention policy for superseded versions → P2. **P2 disposition
(2026-06-07): the record-vs-object distinction is ratified — `record` = one
immutable authored appended revision; `object`/memory lineage = the evolving
memory represented by multiple revisions. Retention mechanics for superseded
revisions remain parked.** F4. Record-
identity scope (per-agent vs global) → P2/P5a. **P2 partial resolution
(2026-06-07, vocabulary layer): `eid` retained as load-bearing local graph
handle, never sufficient durable identity; memory-lineage identity stable
across legitimate updates; record-revision identity binds one immutable
authored revision; revision fingerprint = checkable revision evidence (not
truth, not authority); workspace membership distinct from identity; clone
lineage must be representable. Mechanics remain parked to P2.5 / P5a / P6 /
P9 as routed.** F5. Read-discipline
unification + quarantine shape → P5a. F6. **Contract-level decision resolved by P1 (2026-06-07):** raw
historical crystal stamps do not auto-promote into lifecycle protection;
recommendation vocabulary ratified. Migration, acceptance, rollback, and
recovery mechanics remain parked to P5a / P9. F7. Shell transition-event vocabulary + resume UX → P3. F8.
Engine boundary depth + custom-substrate trigger evaluation → P6 (see §K).
F9. Journal vs per-family ledgers → P6. F10. Snapshot/compaction format →
P6/P7. F11. Orphan-visibility mechanism → P4. F12. Benchmark suite
definition → P8a. F13. **Migration and rollback — staged**: era/migration
vocabulary portion **completed by P1 (2026-06-07)**; rollback and
recovery semantics remain P5a; complete architecture-level migration
strategy remains P9. F14. Noun-cut final
ratification → P2/P9. **P2 outcome (2026-06-07): no new first-class noun
added; IntegrityManifest's first profiled use is ratified as the Genesis
Baseline profile of IntegrityManifest; the three-axis identity vocabulary
is ratified as contract vocabulary. Remaining noun-cut work belongs to
later phases only where justified by ambiguity or invalid-state
prevention.** F15. Maintenance-lane cadence (concurrent vs serial)
→ trio, any time. F16. **Answered for the authoritative local corpus (2026-06-07):**
`metadata.srg` matches: 0. Copied / external / imported workspace
characterization remains open where relevant.

## G. Research hypotheses registry

(CLASS = HYPOTHESIS; admission only via P8a gate → P8b evidence; all carry
the shared negative constraint: no canonical semantics without a pre-
registered benchmark win over a simplicity control.)

G1. Corridor-gated basin folding preserves retrieval + identity. G2.
Stability-priced retention beats recency+strength. G3. Identity-effect
restoration is measurable with existing drift/basin instruments. G4. SRG
resistance classes improve retention quality (constants currently paper-
derived, not TORMENT-calibrated). G5. RSB regime classes gate memory-
formation quality. G6. Recursive-temporality ordering as compaction
invariant. G7. Geometric/basin-clustered storage locality improves
retrieval. G8. Golden-tower constants carry operational (not just
interpretive) value. · Sources: [KA §K–L][R2 §C–D]; Zenodo records as
cited there. Revisit triggers: respective P8b verdicts.

## H. Controlled engine vocabulary

**First-class canonical nouns (working cap: 8):** MemoryNode ·
GovernanceEnvelope · MemoryEvent · SeedRecord · Snapshot ·
IntegrityManifest — accepted (6/8 used; headroom deliberate). The cap is a
discipline tool, not doctrine-grade numerology: a later phase may justify
an additional noun if it prevents ambiguity or invalid states.

**Ratified P1 contract nouns (2026-06-07 amendment):**
EraEvent — one unified append-only per-workspace era-ledger event
vocabulary, including `event_schema_version`, `event_id`,
`event_ordinal`, `kind`, `subject`, `at_ts`, `declared_by`,
`writer_version`, conditional `precontract_anchor_ref`, conditional
`run_ref` (renamed from FeatureEraEvent in P0; ledger-unification and
event-kind decisions made by P1) · ReaderPolicy — family-bound
interpretation discipline, not a hidden central authority engine.
Both are contract-level nouns only: distinct from the first-class
canonical storage nouns above, and NOT promoted into runtime
implementation by this amendment.

**Ratified P2 contract vocabulary (2026-06-07 amendment):**
Contract-level vocabulary only; NOT promoted into runtime implementation by
this amendment. No new first-class noun is added.

- **local graph handle (`eid`)** — retained · load-bearing · reusable ·
  operational join key · never sufficient sameness or era-membership
  evidence.
- **memory-lineage identity** — stable across legitimate updates to one
  evolving memory lineage.
- **record-revision identity** — binds one immutable authored appended
  revision.
- **revision fingerprint** — checkable evidence binding authored revision
  meaning; not evolving-object state · not truth · not authority.
- **record vs object distinction** — `record` = immutable authored
  revision; `object`/lineage = evolving memory represented by revisions.
- **Genesis Baseline profile of IntegrityManifest** — a *profiled use* of
  the existing first-class noun IntegrityManifest, NOT a new noun. Special
  interpretation role: derive `legacy_precontract` membership · bind the
  pre-contract baseline · make handle reuse detectable · fail visibly when
  unverifiable.
- **serialization-era validity** — a revision fingerprint is valid only
  relative to a declared serialization era/profile; unknown, mismatched, or
  unverifiable context must never silently validate an identity-dependent
  claim.
- **DeepMemoryEcho source-evidence requirement** — an echo must preserve:
  source local handle · source family · source memory-lineage identity ·
  source record-revision identity or revision fingerprint · source
  `era_ref`.
- **edges** — own durable assertion · own attribution route · endpoint
  evidence validates linkage only · endpoint eras do not silently determine
  edge era.

**Hilmir-ratified lost-anchor posture (2026-06-07, values-layer):** if the
Genesis Baseline IntegrityManifest profile is missing, unreadable, or
unverifiable — legacy records remain readable, inspectable, operator-visible,
and recoverable; they are not deleted and not silently suppressed; but their
unverifiable `legacy_precontract` claim does not silently remain
cognition-eligible (default `diagnostic_only`); a later explicit recovery or
governance action may restore classification. Standing distinctions:
`diagnostic_only` ≠ deletion · `diagnostic_only` ≠ invisible suppression ·
fingerprint ≠ truth · inventory ≠ authority · era attribution ≠ lifecycle
protection. Source: `docs/TORMENT_MEMORY_ENGINE_P2_FAMILY_IDENTITY_ERA_
ATTRIBUTION_CONTRACT_v0.1.md` §11.

**Provisional contract nouns:** DeepProjectionContract ·
ShellContinuityContract · QuarantineRecord · **ShellState** ·
**CorridorTransition** (the latter two added in P0: P3's postures D2–D5
presuppose them; both remain provisional contract/event nouns only — NOT
promoted into canonical stores in P0).

**Derived / diagnostic nouns:** DeepMemoryEcho (current derived/diagnostic
noun) · **MotifRecord** (current durable persisted motif representation —
the thing motifs.json stores today) · CompressionProjection ·
RawDiagnosticRead · OrphanedDeepEcho.

**Research-only / future nouns:** **MotifBasin** (research/future noun
whose canonical-versus-derived tier remains unsettled; future basin
semantics are not pre-decided here) · **DeepFold** (research-only/future —
not current runtime semantics; DeepMemoryEcho names what exists today) ·
ReturnPath (future; evidence: return events are durably unlogged [KP §E]) ·
RSB-regime object · dynamic RGD state · geometric page layout.

Rule: new nouns enter only by registry amendment.

## I. Revised dependency graph (recorded)

P0 → P1 → P2 → **P2.5 (P1/P2 reconciliation check)** → P4 → P3 → P5a →
P6 → P7 → P8a → P9 → P10 → P11.
Side lanes: **P5b** Portability & Durability Mechanics (after P5a, matures
alongside P6) · **P8b** Experimental Geometry Runs (after P8a; does not
block P9; feeds annexes/amendments only) · **Maintenance lane** (separately
authorized; never silently opens an architecture phase).

## J. Maintenance-versus-evidence routing table

**Evidence for P1 — COMPLETE (2026-06-07 amendment):** historical
workspace scan for `metadata.srg` in deep stores: complete — 0 local
matches (local corpus evidence only); SRG reader-policy inventory:
complete; main-gate vs cognition-gate reconciliation evidence: complete
(dormant `retrieve_srg_state` flag finding, C8 refinement);
era/migration vocabulary inputs: complete (per staged F13, P1 portion
closed).
**Evidence for P2 — COMPLETE (2026-06-07 amendment):** read-only
durable-family identity survey: complete; Codex adversarial H-1 static
review: complete; operator-run Windows disposable H-1 characterization:
complete (verdict `H1_CONFIRMED`); P2 contract promotion: complete at
`950c5a9`.
**P2.5 — P1/P2 reconciliation check: COMPLETE and CLOSED (2026-06-07
closure registration).** Cross-contract write-site conformance review
completed and was distilled into `docs/TORMENT_MEMORY_ENGINE_P2_5_CROSS_
CONTRACT_RECONCILIATION_v0.1.md` (promoted at `093f73a`).
Recorded findings: canonical P1/P2 carrier field vocabulary was absent
across the inspected current `torment_service` code surfaces; several
durable families contain semantic identity analogues; none is automatically
proven contract-conformant; `embedding_checksum` is adjacent content-derived
prior art only and must not be silently promoted into the P2
revision-fingerprint role.
Later routing remains parked: family-specific slices implement only after
carrier design; P4 owns reader/projection enforcement and the
reader-dependency trace; P5a owns recovery/reconciliation; P6 owns substrate
mechanics; P9 owns migration execution. Active gate: none. Next gate:
unselected. P4 is next in the recorded graph, not opened and not
auto-selected.
**Evidence for P3:** checkpoint restore round-trip characterization
(operator-run; verification evidence only, no production wiring).
**Evidence for P4:** literal 25-key allowlist characterization ([DP-A §B]);
raw diagnostic endpoint classification (incl. app.py:2218); orphan-
suppression observability characterization.
**Evidence for P5a:** loader failure-mode inventory ([R1 §F] base);
artifact-class crash-window matrix (on paper); quarantine semantics
options; rollback and recovery semantics inputs (per staged F13).
**Independent maintenance candidates (separately ratifiable, never silently
opening a phase):** identity/character-state atomic-save fix; literal
25-key regression-lock test; orphan observability counter;
`TORMENT_SRG_COGNITION` default reconciliation (remains separately
ratifiable; no patch authorized by the P1 amendment); interim SRG reader
gating **only after** P1 reader policy — P1 reader policy is now ratified,
so this candidate is policy-unblocked; each slice remains separately
authorized.

## K. Custom low-level substrate trigger

NEGATIVE CONSTRAINT (registered): custom low-level storage internals are
not opened merely because a geometric engine is desirable. Eligibility
requires evidence of at least one of: measured volume/load-time limits;
transactional guarantees unmet by subordinate primitives; benchmarked
geometric-locality advantage (G7); portability/auditability/recovery
blockers; a TORMENT-native mechanism requiring deeper coupling. Owning
phase: P6 (evaluation), P8b (evidence). Authority: trio.

## L. Explicit non-goals of P0

No schemas. No formats. No SRG changes. No shell wiring. No allowlist
edits. No storage products. No architecture memo. No implementation. No
doctrine amendment. No benchmark runs. No new nouns beyond §H. No P1
auto-open. This registry confers no authority on itself: it records, it
does not rule.

## M. Recommended stop condition

P0 closes when: this document is reviewed by GPT, attacked by Codex,
amended as needed, committed by Hilmir as
`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`, and the orientation
map gains a one-line pointer to it. The next gate (P1) is then a separate
trio decision — not implied, not auto-opened.

## N. Amendment record

**N1. P1 closure amendment (2026-06-07, docs-only Slice B).**

P1 — Era and Schema Minimum Contract: closed by promoted contract
`docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md`.
Closure date: 2026-06-07. P2: not opened. Next gate: unselected.

This amendment changes registry classification **only** where listed:
quick-reference gate state (§ quick reference); C7 / C8 / C12 disposition
and evidence additions (§C); D7–D13 SRG posture dispositions (§D); F6 /
F13 / F16 parked-question updates (§F); EraEvent / ReaderPolicy promotion
to ratified P1 contract nouns (§H); P1 evidence-set completion and
maintenance-candidate status (§J); and this record (§N). It confers **no
implementation authority**: no runtime code, schema implementation,
migration, storage product, SRG edit, or subsequent phase is authorized.

**N2. P2 closure amendment (2026-06-07, docs-only Slice B).**

P2 — Family Identity and Era Attribution Contract: closed by promoted
contract `docs/TORMENT_MEMORY_ENGINE_P2_FAMILY_IDENTITY_ERA_ATTRIBUTION_
CONTRACT_v0.1.md` (promotion commit `950c5a9`). P2.5: not opened. Next
gate: unselected.

This amendment changes registry classification **only** where listed:
quick-reference gate state (§ quick reference); H-1 verified FACT row C20
(§C); F3 / F4 / F14 dispositions (§F); ratified P2 contract vocabulary,
IntegrityManifest Genesis Baseline profiled-use note, serialization-era
validity clause, and Hilmir-ratified lost-anchor posture (§H); P2
evidence-set completion and P2.5 write-site-conformance responsibility
(§J); and this record (§N). It confers **no implementation authority**: no
runtime code, no schema instantiation, no H-1 patch, no identity-token
selection, no fingerprint-algorithm selection, no manifest mechanics, no
migration, no storage-product selection, no P2.5 opening, no adjacent phase
opening.

**N3. P2.5 closure registration (2026-06-07, docs-only).**

P2.5 — P1/P2 Cross-Contract Reconciliation and Write-Site Conformance
Review: **CLOSED**. Closure artifact: `docs/TORMENT_MEMORY_ENGINE_P2_5_
CROSS_CONTRACT_RECONCILIATION_v0.1.md` (promoted at `093f73a`). Active
gate: none. Next gate: unselected — P4 is next in the recorded graph, not
opened and not auto-selected.

**Stable center.** Canonical P1/P2 carrier field vocabulary was absent
across the inspected current `torment_service` code surfaces; several
durable families contain semantic identity analogues; none of those
analogues is automatically proven contract-conformant; analogue ≠ canonical
carrier.

**Anti-drift safeguard.** `embedding_checksum` is adjacent content-derived
prior art only — not a P2 revision-fingerprint carrier — and must not be
silently promoted into that role.

**Separated eid concerns.** Allocator reconstruction (`max_eid + 1`) =
allocator-state survivability weakness; DeepMemoryEcho borrowed eid +
presence-only validation = confirmed durable-sameness overload; migration
cursor eid ordinal = derived-substrate migration hazard; edge `src`/`tgt`
eid = correct local linkage today, future reassociation risk only, no
current reader harm proven; `update_payload` same-eid re-append = lineage
gap, suspected overload only, reader trace required before a stronger claim.

**Parked questions.** Q-2: are `closure_id` / `version_id` merely prior
art, or a later reference shape? Q-3: which operational ledgers are
P2-governed records, and which are audit evidence? Q-4: does any reader
beyond DeepMemoryEcho rely on eid sameness across reload for cognition or
governance behavior?

**Later routing (no work opened).** Family-specific slices: write-site
stamping after carrier design. P4: reader and projection enforcement; echo
evidence-based joins; diagnostic fencing; orphan observability;
reader-dependency trace. P5a: recovery and reconciliation. P6:
identity-token mechanics; allocator-state persistence; revision-fingerprint
mechanics; canonical serialization; IntegrityManifest mechanics; durability
mechanics; relationship, if any, to `embedding_checksum`. P9: migration
execution; cursor-semantics transition.

This registration changes registry classification **only** where listed:
quick-reference gate state (§ quick reference) and this record (§N). It
confers **no implementation authority**: no carrier designed, no analogue
promoted, no fingerprint-algorithm / identity-token / serialization /
allocator / manifest selection, no storage product, no migration, no H-1
patch, no adjacent gate opened.

**N4. Pre-P4 reader-dependency trace registration (2026-06-07, docs-only).**

Registers the bounded read-only pre-P4 reader-dependency trace as
`docs/TORMENT_MEMORY_ENGINE_PRE_P4_READER_DEPENDENCY_TRACE_v0.1.md`. Active
gate: none. Next gate: unselected. P4 **not opened**.

**Corrected Q-4 disposition** (supersedes the earlier "sole confirmed
cognition surface" framing): there are **two** confirmed cognition-affecting
reusable-eid dependencies, on different axes — (i) **DeepMemoryEcho** is the
sole confirmed *direct echo-to-prompt* H-1 reader (presence-only beta
validation; FILTER-A is orthogonal and does not close H-1); (ii)
**motif membership → identity-anchor emission** is a *separate, derived*
cognition-affecting reusable-eid path (`_maybe_emit_identity_anchor` resolves
persisted motif member eids by presence and distils their summaries into a
new `identity_anchor` memory; derived/non-canon anchors reach cognition
through ordinary tier classification, **excluded** from the canon-only
identity-anchor shortcut / full continuity boost unless promoted to canon;
ordinary tiering may still classify them into an identity block by
tier/half-life). **No governance
reader** of reusable eids was found. **Stored node→node edges are
latent-only** (loaded/appended, never read for cognition or governance).

**Routing:** direct and derived reader/projection safety → **P4** (echo
source-sameness; derived identity-anchor source-membership; raw-diagnostic
intent-vs-capability fence; field-surfacing tiers; orphan observability;
light spirit-reflection re-entry confirmation); recovery / stored-edge repair
→ **P5a**; durability / identity-token / fingerprint / substrate mechanics →
**P6**; migration execution → **P9**. No executable probe authorized.

This amendment changes registry classification **only** where listed:
quick-reference is unchanged (gate state already records P0–P2.5 closed, P4
unselected); this record (§N) registers the trace artifact and the corrected
Q-4 disposition. It does **not** amend P1 or P2 doctrine, does **not** open
P4, and confers **no implementation authority**: no carrier, no identity-token
/ fingerprint / serialization / allocator / manifest / substrate mechanics, no
generic database promoted, no migration, no edge or motif redesign, no
diagnostic-fence or disclosure-channel mechanics.

**N5. P4 contract promotion and closure registration (2026-06-09, docs-only).**

P4 — Reader and Projection Safety Contract: **promoted and closed** at commit
`dbdbc30`. Promoted artifact:
`docs/TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md`
(requirement-level design contract; full P4 framing report remains
working-folder evidence only and is **not** promoted). Active gate: none. Next
gate: unselected — P3 is next in the recorded graph, not opened and not
auto-selected.

**Contract shape (do not reproduce full text here; cite the artifact).** Five
requirement-level obligations: (O1) echo source-sameness before ordinary
cognition admission; (O2) motif-member source-membership sameness before derived
identity-anchor emission, under the applicable family-bound source-sameness
adequacy standard; (O3) surface classification by both intent and re-entry
capability; (O4) explicit surface-classified projection gating, never accidental
payload spread; (O5) orphan/mismatch observability — no silent cognition
admission, no invisible disappearance, operator-auditable inspectability. Plus
one **contract-wide non-coercion invariant** governing O1–O5 (not a sixth
feature): memory may shape context but may not seize authority; audit observes
authority but does not become authority; no silent output blocking, no invisible
deletion, no covert unauditable suppression of evidence or eligibility state, no
authority seizure, no personality lock.

**Ratified Hilmir values-layer posture (records E10-class operator intent).**
When runtime source-sameness cannot be proven, the reference defaults to
`diagnostic_only` cognition eligibility until an explicit audited governance
action restores eligibility; it remains operator-auditable, inspectable, and
recoverable; ordinary model-facing notice is not required by default.
**Anti-drift:** `diagnostic_only` is an *eligibility posture*, not a *projection
instruction* — diagnostic projection stays governed by O3/O4 and does not by
itself confer cognition eligibility. This extends the P2 lost-anchor posture (§H)
to the runtime sameness-failure case.

**No mechanics authorized by P4.** no implementation · no runtime patch · no
tests · no executable probe · no identity-token / UUID / ULID selection · no
fingerprint algorithm · no serialization · no allocator mechanics · no manifest
mechanics · no database/SQL selection · no substrate mechanics · no packaging
decision · no motif redesign · no stored-edge repair · no migration · no
quarantine design · no recovery UX · no orphan-counter implementation · no
disclosure-channel default · no allowlist edit · no FILTER-A change · no endpoint
removal · no MCP-resource rerouting · no ReaderPolicy implementation · no
maintenance · no CodeQL work.

**Later-owner routing stays parked (unchanged from §J / the contract):** P5a
recovery/reconciliation/quarantine-semantics/orphan-recovery-UX/stored-edge-repair
adjacency; P5b portability and durability mechanics; P6 identity carriers /
fingerprints / serialization / allocator durability / IntegrityManifest mechanics
/ TORMENT-specific governed-memory substrate mechanics / packaging-boundary
evaluation; P9 migration execution and architecture-wide promotion; maintenance
lane CodeQL complaints / orphan-observability counter / allowlist regression lock
/ identity-character-state atomic-save fix.

**Next-gate posture.** P4 is closed; **no next gate is auto-opened.** The
dependency graph still places P3 after P4, but selecting the next active slice
requires deliberate steering review (gate-start survey rule).

This amendment changes registry classification **only** where listed:
quick-reference gate state (§ quick reference) and this record (§N). It confers
**no implementation authority** and opens no adjacent gate.

**N6. Governed-Memory Substrate Programme Stage A contract promotion and closure
registration (2026-06-09, docs-only).**

Governed-Memory Substrate Programme Stage A — Recovery and Reconciliation
Semantics Contract: **promoted and closed** at commit `2bf3b29`. Promoted
artifact:
`docs/TORMENT_MEMORY_ENGINE_STAGE_A_RECOVERY_RECONCILIATION_SEMANTICS_CONTRACT_v0.1.md`.
The full Stage A/B framing reports, Codex adversarial reviews, and working-folder
drafts remain working-folder evidence only and are **not** promoted. Active gate:
none. Next gate: unselected — Stage B mechanics and database design remain
unopened and are not auto-selected. GitHub Issue #54 remains the checkpoint
barrier before database design may be considered.

**Contract shape (do not reproduce full text here; cite the artifact).** Seven
requirement-level obligations: (O1) governance-meaning-complete recovery; (O2)
visible family-bound ReaderPolicy dispositions, with no universal storage-error
bin; (O3) era-aware recovery and no silent reclassification; (O4) explicit
audited restoration boundary; (O5) committed-write durability promise bound to
O1 governance-meaning-complete recovery; (O6) character-basin preservation
without rigid pinning; (O7) storage-shape freedom under semantic-invariant
preservation. Plus one **contract-wide non-coercion and audit invariant**
governing O1–O7, not an eighth implementable feature.

**Ratified Hilmir values-layer postures.** (1) A write reported committed
promises recoverability after process crash and ordinary OS or power
interruption within honest local-hardware guarantees; committed durability
includes the artifacts and evidence required for governance-meaning-complete
recovery. (2) Within that durability scope, authored canonical character state
survives verbatim; durable basin-shaping assertions survive or are faithfully
rederived; derived state may rebuild; genuinely ephemeral modulation may
recompute; soft guidance may not be silently pinned into rigid substrate
control. (3) Deterministic automatic restoration is permitted only when required
evidence is fully proven valid again under the applicable family-bound
ReaderPolicy, with an explicit auditable event, inspectability, contestability,
and reversibility; ambiguous cases stage recommendations or await explicit
governance acceptance; no invisible automatic finalizer; Hilmir retains ultimate
operator authority.

**Anti-drift.** recovery != text-only reread · storage lane != authority class ·
canonicality != authority · eligibility != projection · diagnostic_only !=
automatic exposure · diagnostic_only != deletion · quarantine != deletion ·
fingerprint != truth · inventory != authority · era attribution != authority ·
storage-shape change != semantic change.

**No mechanics authorized by Stage A.** no implementation · no runtime patch · no
tests · no executable probe · no database-product or SQL selection · no
identity-token / UUID / ULID selection · no fingerprint algorithm · no
serialization profile · no allocator mechanics · no IntegrityManifest mechanics ·
no journal format · no transaction design · no fsync strategy · no replication or
backup design · no snapshot or compaction format · no packaging decision · no pip
distribution · no repository extraction · no migration · no Track B authority
reopening · no CodeQL work · no security redesign · no security-paper update.

**Later-owner routing stays parked.** Stage B / P6-shaped mechanics: identity
carriers · revision fingerprints · serialization · allocator durability ·
IntegrityManifest mechanics · transaction model · append guarantees · substrate
architecture · adapter boundary · packaging evaluation · database evaluation.
P5a adjacency: reconciliation procedure · quarantine procedure · rollback
recovery semantics · clone reconciliation · torn-append handling · duplicate
repair · partial-restore repair · stored-edge repair adjacency. P7: conditional
compaction questions. P8a/P8b: research-hypothesis admission benchmarks only.
P9: migration execution · architecture-wide promotion. Maintenance lane: CodeQL
and minor named repairs, separately authorized. Future security layer:
multi-process coordination · at-rest protection · access-boundary hardening ·
GitHub security-paper update after database work.

**Next-gate posture.** Stage A is closed. No next gate is auto-opened. Stage B
mechanics and database design remain unopened. Before database design is
considered, Issue #54 requires a synchronized Windows-authoritative clean
checkpoint and a fresh-chat handoff.

This amendment changes registry classification **only** where listed: the
amendment-date line, quick-reference gate state, three-hard-non-goals wording,
and this §N6 record. It confers **no implementation authority**, selects no
mechanics, opens no adjacent gate, and does not amend the recorded dependency
graph.

**N7. Thinking-layer archaeology: ratified soft-state continuity postures and
parked private-thinking-layer seam (2026-06-09, docs-only).**

Source: read-only thinking/cognition runtime archaeology survey + closure
reconciliation (working-folder evidence; survey conclusions confirmed standing at
`076f4c2`, the intervening commit being docs-only). The survey established, as
VERIFIED FACT: (i) the named "thinking/cognition" layer is **deterministic
heuristic routing and retrieval shaping, not a separate private model-deliberation
room** (`thinking_controller.py:398–455`; cognition roles have no model calls and
are off the default `/agent/query` path); (ii) the **TriOcta memory kernel is live
on every ingest and load-bearing** — geometric state gates writes and sets
strength/confidence/half-life/promotion signals (`fabric.py:2535,2654`;
`memory_kernel.py:392–395`); (iii) the **character basin is real and
preservation-relevant**; (iv) **private deliberative cognition is not yet
meaningfully implemented** (roadmap-only). No reader-safety, projection-safety,
path-integrity, or storage-correctness flaw surfaced; RSB is dead code, RGD is a
fixed composite with no dynamics.

**Operator-ratified soft-state continuity postures (Hilmir, 2026-06-09).** These
record OPERATOR INTENT for how future substrate work must treat cognition-adjacent
continuity state; they select no carrier, schema, serialization, or mechanic, and
they refine — they do not amend — the Stage A O6 soft-guidance boundary.

- **TriOcta ModelState** — durable non-canonical continuity state; recoverable
  after ordinary crash when valid evidence exists; not authored canon; not
  immutable; not authority-bearing; not a personality lock; not an absolute
  preservation lock; resettable through an explicit auditable operator-visible
  path.
- **CorridorMonitor EMA** — durable non-canonical continuity state where needed
  for faithful continuation; not authored canon; not rigidly pinned; resettable
  and rebuildable where technically valid.
- **tri_mod multipliers** — ephemeral per-step modulation; never persist as
  durable state; recompute naturally.
- **cycle-stage transients** — ephemeral; do not persist.
- **spirit-return warmth** — durable soft guidance; bounded; inspectable;
  contestable; resettable; decay-capable; never canonical; never authority-bearing;
  never an absolute preservation lock.
- **mood / drift history** — durable soft guidance; preserve enough continuity to
  avoid arbitrary flattening; never silently promote into canon; remain resettable
  and contestable.
- **symbol trace** — rebuildable from attributable durable history where possible;
  do not freeze it into a rigid first-class carrier unless later evidence shows
  faithful reconstruction is insufficient.
- **SRG** — remain default-off; remain benchmark-gated; do not freeze into
  first-class substrate requirements yet.

**Governing principle:** *preserve continuity without preserving compulsion.*

**Parked roadmap seam — future private-thinking-layer gate (parked, not opened,
not designed).** Purpose: make internal cognition meaningfully real while allowing
private deliberation to remain hidden from ordinary output. Standing guards: raw
inner deliberation does not automatically become durable memory; hidden cognition
does not become hidden authority; governed-memory crossing paths remain explicit
and bounded; architecture remains inspectable. This records, honestly, that
TORMENT has a real memory organism but does not yet have the private cognitive
interior it may eventually want; opening the seam requires its own audit-first
trio decision.

This amendment changes registry classification **only** where listed: the
amendment-date line and this §N7 record. It registers OPERATOR INTENT and a PARKED
QUESTION; it confers **no implementation authority**, selects no mechanics, opens
no adjacent gate, does not amend the Stage A contract, and does not amend the
recorded dependency graph.

---

**N8. Document A — Candidate Containment and Writer-Authority Contract promotion and closure registration (2026-06-13, docs-only).**

`docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md` is promoted as a **requirement-level write-side design contract** and **closed** as docs-only. Document A is the write-side requirement boundary that pairs with P4's read-side boundary; runtime conformance and enforcement remain later-owned (P2.5 / a separately authorized implementation track). It belongs to the pre-substrate architecture reconstruction programme (the higher architecture above the paused substrate), distinct from the Memory Engine phase graph, and is registered here because it interacts with Cluster 2 / P4 / Stage A / Ledger doctrine.

**Programme state after N8:** active gate **none**; next gate **unselected**; **Document B eligible but not opened**; Stage B remains **closed**; runtime implementation remains **later-owned**. No Memory Engine phase was opened or selected by this registration.

**Contract shape (summary; full text not reproduced):** class-bound writer-authority requirement (a writer must be authorized for the class of write; payload flags / source presence are not sufficient); the load-bearing containment invariant (unadmitted reflection artifacts unable to influence or re-enter any cognition / retrieval / prompt / affect / identity / projection-reentry path until governed admission); private thread-continuity separation (thread-continuity ≠ synthesis ≠ unadmitted candidate ≠ admitted memory); admission ceiling; admission ≠ promotion; inspection ≠ projection; recovery retains class; lineage preservation without raw-reflection exposure by default; side-channel non-reachability (reinforcement / strength / feedback-overlay / bridge-confidence / retrieval-count / promotion-suggestion paths barred); existing automatic writer seams named and later-routed (`gravity_correction`, `_maybe_emit_identity_anchor`, `mood_drift`, `promote_chunk` force-bypass, soft-state O6 tier) — **patched by none of this contract**.

**Registered values-layer input (operator-ratified, verbatim).** Admission default:

> An admitted private-reflection candidate defaults to released / low-authority. It may enter ordinary memory only through an explicit governed admission crossing. Admission does not confer canon status. Admission does not confer identity-shaping weight. Admission does not confer unrestricted promotion rights. Any later upgrade beyond released / low-authority requires a separately governed, auditable, contestable crossing.

Admission ceiling refinement:

> Released / low-authority is the maximum default authority posture available through ordinary governed admission. It is not a guarantee that every reflection artifact enters ordinary retrieval or becomes queryable ordinary memory. Per-artifact outcomes may be stricter: chamber-only, audit-only, operator-visible-only, refused, retired. Any ordinary-memory admission must still occur through an explicit governed, auditable, contestable crossing. Any later revocation, reclassification, or reversal must occur through another separately governed crossing. Inspection is operator-auditable or governance-auditable by default; it is not model-visible, caller-visible, prompt-visible, retrieval-visible, or MemoryPlan-visible unless separately surface-classified and governed.

This amendment changes registry classification **only** where listed: the amendment-date line, the footer, and this §N8 record. It confers **no implementation authority, no runtime Authority Gate, no runtime patch, no schema, no storage selection, no database design, no migration, no Document B opening, no Stage B opening, and no autonomy opening.** It does not amend the recorded dependency graph or any prior contract text.

---
*End v0.1 as amended 2026-06-07 (N1 P1 closure; N2 P2 closure; N3 P2.5
closure registration; N4 pre-P4 reader-dependency trace registration) and
2026-06-09 (N5 P4 contract promotion and closure registration; N6 Stage A
recovery/reconciliation semantics contract promotion and closure registration;
N7 thinking-layer ratified soft-state postures and parked private-thinking-layer
seam) and 2026-06-13 (N8 Document A candidate-containment and writer-authority
contract promotion and closure registration). Amendments are small docs slices
with trio sign-off.*
