# TORMENT Memory Engine — Decision Registry and Vocabulary Discipline v0.1

**Status:** P0 artifact. Anti-drift reference. NOT doctrine, NOT a schema,
NOT implementation authorization. Every later engine phase cites this
document; no later phase silently amends it.
**Date:** 2026-06-06
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
| **Active gate** | P0 only |
| **Next gate** | P1 — only after separate trio authorization |
| **Registry classes** | FACT · POSTURE · DOCTRINE · OPERATOR INTENT · PARKED QUESTION · RESEARCH HYPOTHESIS |
| **Current graph** | P0 → P1 → P2 → P2.5 → P4 → P3 → P5a → P6 → P7 → P8a → P9 → P10 → P11 |
| **Side lanes** | P5b (after P5a, alongside P6) · P8b (after P8a, non-blocking) · maintenance (separately authorized) |
| **Three hard non-goals** | no schema design · no implementation · no P1 auto-open |

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

C8. **The cognition SRG gate defaults ON** (`TORMENT_SRG_COGNITION=1`),
contradicting the main gate · FACT · *[SRG-A]; thinking_controller.py:196,
410* · gate semantics are inconsistent · do not add further SRG gates
pre-P1 · evidence-only · P1; maintenance candidate §J · default change.

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

**SRG** (owning phase P1, ethics decisions with Hilmir; trigger: P1 gate)
D7. SRG remains a valid optional guidance layer. D8. Disable must
truthfully disable influence lanes. D9. Historical stamps remain auditable.
D10. **Crystal protection may survive only through explicit lifecycle /
governance provenance, pending the P1 decision on valid provenance and
re-homing mechanics.** D11. Forced resonance becomes a bounded bias —
recorded as a **mechanism-shaping satisfaction of operator intent (E10),
not doctrine**. D12. **Query-time mutation must become either derived
non-authoritative state or explicit locked event-sourced evolution; P1
owns reader policy; P5a owns recovery / integrity semantics.** D13.
Feature-era bookkeeping is required. · Negative constraint (shared): none
of D7–D13 authorizes touching SRG code before its owning phase ratifies
reader policy.

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
P5a/P9. F3. Retention policy for superseded versions → P2. F4. Record-
identity scope (per-agent vs global) → P2/P5a. F5. Read-discipline
unification + quarantine shape → P5a. F6. SRG disable option (C vs
D-with-re-homing) + crystal provenance and re-homing mechanics → P1
(+Hilmir). F7. Shell transition-event vocabulary + resume UX → P3. F8.
Engine boundary depth + custom-substrate trigger evaluation → P6 (see §K).
F9. Journal vs per-family ledgers → P6. F10. Snapshot/compaction format →
P6/P7. F11. Orphan-visibility mechanism → P4. F12. Benchmark suite
definition → P8a. F13. **Migration and rollback — staged**: era/migration
vocabulary → P1; rollback and recovery semantics → P5a; complete
architecture-level migration strategy → P9. F14. Noun-cut final
ratification → P2/P9. F15. Maintenance-lane cadence (concurrent vs serial)
→ trio, any time. F16. Whether historical srg-bearing deep records exist in
real workspaces → operator scan, routed §J, feeds P1/P4.

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

**Provisional contract nouns:** EraEvent (renamed from FeatureEraEvent —
P1 decides whether one unified era ledger exists and which event kinds it
contains) · ReaderPolicy · DeepProjectionContract ·
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

**Evidence for P1:** historical workspace scan for `metadata.srg` in deep
stores (operator-run, Windows); SRG reader-policy inventory ([SRG-A §C] as
base); main-gate vs cognition-gate reconciliation evidence; era/migration
vocabulary inputs (per staged F13).
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
25-key regression-lock test; orphan observability counter; SRG cognition
default reconciliation; interim SRG reader gating **only after** P1 reader
policy is chosen.

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

---
*End v0.1. Amendments are small docs slices with trio sign-off.*
