# TORMENT Memory Roadmap — Pre-Block-C Preconditions

**Status:** **RATIFIED 2026-04-21** by user + GPT. All 11 §12 checklist items accepted after one wording-narrowing review round. Block C may now move to its implementation-analysis phase.
**Date:** 2026-04-21
**Scope:** Preconditions for Block C implementation — arc-level closure / end-of-arc synthesis. Block C is the third and final block of the regrouped memory roadmap and the most ethically load-bearing part of it.

**Precedents (inherited, not restated):**
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` — ratified 2026-04-19
- `docs/BLOCK_A_DESIGN.md` — ratified 2026-04-19; merged to main 2026-04-21
- `docs/PRE_BLOCK_B_PRECONDITIONS.md` — ratified 2026-04-21
- `docs/BLOCK_B_IMPLEMENTATION_ANALYSIS.md` — ratified 2026-04-21
- `docs/BLOCK_B_DESIGN.md` — ratified 2026-04-21
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` §7 (Item 4 — Closure / End-of-Arc Synthesis)
- `roadmap_tests/Roadmap_working_memo.md` — operating discipline (closure stays late; do-later §4)
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md`, `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` — runtime doctrine + scorecard
- `docs/DOCTRINE_v2.4.x.md` — standing principles

> This document freezes the preconditions for Block C implementation work. It is a ratification gate, not a design spec. It does not pre-decide the closure object storage shape, the ratification flow details, closure proposal heuristics, or arc-scope vocabulary — those belong to the Block C design doc, which cannot start until this document is ratified. Block C is the point at which Blocks A and B's guardrails get their real test: closure is where an agent's history becomes self-narrative, and where coercive, sanitizing, myth-making, or revisionist failure modes can silently take hold if the structural supports aren't already load-bearing.

---

## 1. Mission sentence for this phase

> **How should TORMENT introduce arc-level closure — a ratified synthesis operation that metabolizes coherent work sequences into durable, versioned closure objects for the agent's future self — so that (1) closure objects either live as Block B-style reference citizens or justify a stricter alternative without reopening Block A substrate semantics; (2) ratification is structural rather than implied, with explicit audit; (3) the process avoids coercive timing, false finality, mythologized self-history, and silent retrospective editing; (4) audience ordering preserves future-self honesty before user-facing polish; (5) deferred or open items are required structural fields, not optional; (6) the writeback-vs-closure guardrail holds hard, with no shared test harness or review path; and (7) the implementation does not widen writeback, automate ratification, or drift Block C behavior into Block A substrate or Block B retrieval mechanics?**

All seven clauses are load-bearing. Clause 1 names the preferred direction (Block B reference citizens) without hard-freezing the storage shape — the Block C design doc may propose a stricter alternative if it can justify one without reopening Block A substrate semantics. Clauses 2, 3, and 5 are the ethically load-bearing ones the regrouped roadmap §7 specifically calls out. Clause 4 is the audience-ordering invariant that deserves its own standalone section (§6). Clause 6 is the guardrail Blocks A and B ratified; Block C is where it gets its real test. Clause 7 is the non-reopening discipline Blocks A and B already depend on.

---

## 2. Runtime / roadmap handoff rule

Block C implementation runs on top of Blocks A (substrate) and B (reference + environment) already landed. It does not depend on the deferred Block A runtime increments (`SessionLifecycleHook` wiring, `fabric.py` reflex hookup, hardened `code_exec` sandbox). If those increments happen in parallel with Block C, the same regression rule applies: no Block C change may rely on them, and no Block C change may silently absorb them.

> **Block C work must plug into the existing 8-phase runner at every implementation milestone. No Block C change is accepted that regresses any test in the nine-invariant scorecard from `TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` §7, unless a separately ratified runtime change explicitly updates that scorecard.**

The full nine-invariant mapping is in `PRE_BLOCK_A_PRECONDITIONS.md` §2 and is cited here rather than restated.

The "unless separately ratified" clause has the same meaning as for Blocks A and B: scorecard invariants are doctrine-level; any test change that invalidates one is itself a doctrine-shaping amendment.

---

## 3. Red lines

The existing red lines from `Roadmap_working_memo.md`, `DOCTRINE_v2.4.x.md`, Block A's R+1 / R+2, and Block B's R+3 / R+4 / R+5 / R+6 all remain in force. Block C adds **five new red lines**.

### Red line R+7 — No automatic closure enactment

Structural signals may *propose* closure; they may never silently *enact* it. Every closure commit requires explicit ratification with a declared ratifier and its own recorded action. Heuristic readiness checks (related batons resolved, TaskList residue empty, no open questions tagged to the arc remain) are **proposal triggers only**, never commit triggers. The difference between "closure is eligible to be proposed" and "closure is committed" is structural, not a field flip.

### Red line R+8 — No retrospective editing without versioning

Closure objects are revisable, but visibly. Revising a committed closure produces a **new version stored alongside the prior one** — never a silent overwrite. The original closure stays readable. Version history is inspectable. The system must be able to see both what it believed at closure time and how that understanding evolved later.

### Red line R+9 — Model synthesis alone is not a valid closure authorship basis

No closure commit may rely on model synthesis alone as its authorship basis. Model assistance may help draft or organize a proposal, but commit authorship and ratification must be **explicit, attributable, and separately recorded**. A closure whose only recorded authorship is "the LLM synthesized this" is refused at commit. Agent-authored or user-authored closures are legitimate; model-assisted drafts that pass through explicit ratification are legitimate; model synthesis presented as ratified commit is not.

### Red line R+10 — `deferred_or_open_items` is a required structural field

Even when empty, the `deferred_or_open_items` section of a closure object exists. A closure that cannot state its open items is refused at commit. This is the primary structural protection against false finality — every closure is forced to declare what remains unresolved, even if that declaration is "none remain."

### Red line R+11 — Closure must not silently reclassify unresolved contradiction as settled canon

A closure may summarize where an arc stands, but it may not convert disputed, ambiguous, or unresolved material into authoritative identity or canonical state without an explicit separate path. If a closure's scope contains entries the `ConflictRegistry` records as `status="open"`, the closure commit cannot silently mark those entries as resolved canon as a side effect. Promoting contradiction-free material from the arc into durable canon is a separately-ratified write path, not an implicit effect of closure.

---

## 4. Ratification-is-structural rule

Closure ratification is not a metadata flag. It is a separate recorded action with:

- its own provenance factory (`ProvenanceV1.for_closure_ratification` or equivalent — Block C design decides the factory names),
- its own ledger event in an audit trail,
- its own explicit ratifier identity (user, agent, or dual),
- its own timestamp distinct from draft / proposal timestamps.

Closure proposals and closure commits are **different entities at different lifecycle points**, not the same entity with a flipped `ratified` bool. A proposal that is never ratified remains inspectable as a proposal; a ratified commit carries structural evidence of ratification that cannot be reverse-engineered from post-hoc metadata.

Structural signals (related batons resolved, residue empty, open questions cleared) may compute "this arc looks ready for closure" and surface that as a proposal — they may not skip the ratification step.

---

## 5. Closure object minimum shape invariant

Per the regrouped roadmap §7, every closure object declares at minimum:

- `arc_name`
- `scope` (which substrate entries / batons / task residues / references / project deltas belong to the arc)
- `what_it_was`
- `what_worked`
- `what_surprised`
- `what_to_carry_forward`
- `deferred_or_open_items` — **required, never optional** (see R+10)
- `authorship_provenance` — distinct from any provenance Blocks A or B produce; closure authorship is its own thing
- `version_history` — **required, never optional** (see R+8); empty on first commit, populated on every revision

These are structural requirements, not recommendations. The Block C design doc may add additional fields (arc kind, nested arc references, etc.) but cannot remove or make any of these optional.

---

## 6. Audience-ordering invariant

Closure's primary audience ordering is:

1. **The agent's future self** (highest priority — closure preserves honest self-narrative for continuity).
2. **The next AI / future collaborator** (closures inform handoff).
3. **The user** (closures may be user-facing but user-readability is not optimized at the cost of future-self honesty).

This ordering is not flavor. It is load-bearing for design trade-offs:

- When closure wording is ambiguous between "polished for the user" and "honest for future self," future-self honesty wins.
- When closure shape could be flattened to improve user-readability but would lose future-self-relevant structural detail (open items, contradictions, scope deltas), flattening is refused.
- When closure proposal UX is considered, the agent's future self is the implicit reviewer whose comprehension matters, not the user.

Implementation language, test assertions, and design review notes must preserve this ordering. Any optimization that improves user-readability at a measurable cost to future-self comprehension requires explicit ratification.

---

## 7. Acceptance-criteria-before-start rule

Before Block C spec work begins, the Block C design doc must declare **3–5 concrete, testable acceptance criteria**. Unlike Block B, closure is a single category (not a pair) — one criteria set, not two.

If the design doc cannot produce 3–5 such criteria before starting, Block C is not ready to begin. The inability to state criteria is diagnostic.

### Illustrative criteria (examples, not the complete set)

- **Shape validation.** A closure commit missing any required field from §5 is rejected at commit with a named result code. `deferred_or_open_items` absent → rejected specifically (it may be empty, but it cannot be missing).
- **Ratification discipline.** A closure commit without explicit ratification provenance is rejected. Proposals without ratification remain inspectable but do not reach committed state.
- **Versioning honesty.** Revising an existing closure produces a new version; the original is readable and distinct; a `version_history` record links the two.
- **Open-items honesty.** A closure whose scope contains source-arc evidence of unresolved items but whose `deferred_or_open_items` is empty is flagged for review (see §8 test 8.4).
- **Canon isolation.** Committing a closure does not automatically promote any arc-scoped memory into durable canon.

These are illustrative; the Block C design doc owns the final set.

---

## 8. Evaluation harness minimum

Block C has a single category but the highest ethical weight. The harness earns an extra test beyond Block B's four to make the anti-false-finality guard testable rather than philosophical. Five tests at minimum.

**8.1 — Closure-object-shape test.**
A closure commit missing any required §5 field is rejected. `deferred_or_open_items` specifically must be present even when empty; an absent field is a different failure from an empty one.

**8.2 — Ratification-required test.**
A closure commit without explicit ratification provenance is rejected. The commit path cannot be reached by flipping a `ratified` bool on a proposal.

**8.3 — Version-not-overwrite test.**
Revising a committed closure produces a new version stored alongside the original. The original closure remains readable. A `version_history` entry linking the two is created. Silent overwrite is not possible through any API.

**8.4 — Open-items-honesty test.**
A closure proposal or commit whose scope contains arc-evidence of unresolved items (e.g., source-scope entries with `ConflictRegistry` `status="open"`, baton entries with `status="active"`, or TaskList residues marked unresolved) but whose `deferred_or_open_items` is empty is rejected or flagged for ratification review. This is not a full "automatic truth" test — it's a mismatch-detection test, pinning the anti-false-finality invariant.

**8.5 — Block-C-meets-Blocks-A-and-B integration test.**
Closure storage and retrieval do not modify Block A substrate behavior or Block B retrieval mechanics. The nine-invariant scorecard stays green with closure objects present. Baton retrieval, core retrieval, archive retrieval, reference load, and environment consult all produce identical results before and after a closure commit is made.

---

## 9. Extension contract deliverable

The `EXTENSION_CONTRACT.md` cover index gets one new row at Block C close:

- **New closure arc kind** — how to register a new arc-scope kind (e.g., small cleanup arc, feature arc, stability window, release-level arc — multi-scale per roadmap §7). Must cite Block C's design doc as the canonical per-surface reference.

No other extension surfaces change as part of Block C.

---

## 10. Writeback-vs-closure guardrail + Block-B-vs-Block-C guardrail (reaffirmed)

The writeback-vs-closure hard guardrail from `PRE_BLOCK_A_PRECONDITIONS.md` §7 remains in force, and Block C is where it gets its real test:

- Writeback and closure must not share test infrastructure, harness code, or review checklists.
- Block C's `ClosureLedger` (or equivalent audit trail) is NOT the writeback audit path and must not accept writeback entries.
- Any PR that touches both writeback and closure without clear separation requires explicit doctrine review before merge.

**The Block-B-vs-Block-C guardrail from `PRE_BLOCK_B_PRECONDITIONS.md` §8 is now the mirror concern:**

- If closure objects live as Block B reference citizens (the preferred direction per clause 1 of §1), Block C does NOT add closure-related fields to the `ReferenceEntry` shape, and does NOT add closure flags or closure-eligibility markers to existing reference entries.
- If Block C design chooses a stricter alternative (its own store or its own memory class), that alternative must not duplicate reference-entry identity and must not absorb Block B retrieval mechanics.
- Block C does not redefine baton lifecycle, environment consult semantics, or reference load state — those are Block A and Block B concerns.

---

## 11. What this document does not cover

- **Block C design.** Closure object storage shape, ratification flow details, proposal heuristics, arc-scope vocabulary, ledger field structure, commit envelope shape. All owned by the Block C design doc.
- **Block A substrate semantics.** Baton, core, archive, and their interactions remain frozen per `BLOCK_A_DESIGN.md`.
- **Block B retrieval mechanics.** Reference `load` / `unload` / `list_active_loads`, environment `write` / `consult` / `probe_on_fail`, and the primitive non-substitutability — all frozen per `BLOCK_B_DESIGN.md`.
- **Runtime slice v0.1 internals.** Owned by `TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` and unchanged by Block C.
- **`SessionLifecycleHook` wiring.** Still declaration-only.
- **MCP surface.** Owned by `MCP_EXPANSION_GUIDE.md` and unchanged by Block C.
- **High-level doctrine.** Owned by `DOCTRINE_v2.4.x.md`.
- **Branch / merge workflow.** Implementation plumbing.
- **Block D and beyond.** Not under consideration.

---

## 12. Ratification record

**Drafted:** 2026-04-21 by Claude, following the Block C entry framing proposed by user + GPT the same day.

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 — Mission sentence wording accepted (seven clauses; clause 1 softened during review)
- [x] §2 — Runtime/roadmap handoff rule accepted
- [x] §3 — Red lines R+7 / R+8 / R+9 / R+10 / R+11 wording accepted — R+9 tightened during review to distinguish model-assisted drafting from model-authored commitment; R+11 added during review to protect against closure silently converting unresolved material into canon
- [x] §4 — Ratification-is-structural rule accepted
- [x] §5 — Closure object minimum shape invariant accepted
- [x] §6 — Audience-ordering invariant accepted (standalone during review)
- [x] §7 — Acceptance-criteria-before-start rule accepted (single category, 3–5 criteria)
- [x] §8 — Evaluation harness minimum (five tests) accepted — expanded from four to five during review with an open-items-honesty test
- [x] §9 — Extension contract deliverable scope accepted
- [x] §10 — Writeback-vs-closure + Block-B-vs-Block-C guardrail accepted
- [x] §11 — Scope boundary accepted

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block C implementation-analysis phase is unblocked. Any change to these rules after this point requires a separately ratified amendment.

### Carry-forward concerns for Block C implementation analysis

Concerns surfaced during ratification that the analysis phase must keep visibly load-bearing:

1. **Clause 1 is deliberately open.** The preferred direction is that closure objects live as Block B reference citizens, but the analysis must surface whether a stricter alternative is warranted. If yes, that alternative must not reopen Block A substrate semantics.

2. **Ratification is structural, not metadata.** The analysis must look for existing code patterns that would *tempt* collapsing ratification into a bool flag (e.g., `ConflictRegistry.decide`, `baton_lifecycle.status = "consumed"`) and explicitly resist that collapse for closure.

3. **Versioning is honest, not silent.** The analysis must check whether the existing "last record per EID is canonical" pattern (from `memory_graph.py`) is appropriate for closure or whether closure needs explicit version-tuple storage to avoid silent-overwrite.

4. **Model assistance is distinct from model authorship.** When the analysis considers how proposals get drafted, it must preserve the line between model-assisted and model-authored. A drafting path that uses LLM output is fine; a commit path where the LLM is the only recorded author is not.

5. **Open-items honesty is testable, not just aspirational.** The analysis must identify where in the current codebase arc-scope evidence lives (ConflictRegistry, baton_lifecycle, task residues if any, reference staleness) so the 8.4 mismatch-detection test has concrete signals to check against.

6. **Writeback-vs-closure separation is the load-bearing invariant.** Every implementation choice must be challenged against this guardrail. If closure and writeback ever appear to share a code path, the path itself is the failure mode.

---

## Appendix — Source trail

Assembled from:
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` §7 (Item 4 — Closure)
- `roadmap_tests/Roadmap_working_memo.md` (do-later §4)
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` + `docs/PRE_BLOCK_B_PRECONDITIONS.md` (preconditions pattern carried forward)
- `docs/BLOCK_A_DESIGN.md` + `docs/BLOCK_B_DESIGN.md` (baseline Block C inherits from)
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` + `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` (runtime doctrine + scorecard)
- `docs/DOCTRINE_v2.4.x.md` (standing principles)
- Block C entry question drafted by user + GPT 2026-04-21; narrowed in one review round the same day.
