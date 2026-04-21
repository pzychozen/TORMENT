# TORMENT Memory Roadmap — Pre-Block-A Preconditions

**Status:** **RATIFIED 2026-04-19** by user + GPT. All eight §9 checklist items accepted with no narrowing. Block A may now move to its design-doc phase, subject to the rules frozen here.
**Date:** 2026-04-19
**Scope:** Preconditions that must be in place before Block A implementation begins on the regrouped memory roadmap.

**Precedents (inherited, not restated):**
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` — architecture freeze (2026-04-19)
- `roadmap_tests/Roadmap_working_memo.md` — do-now / do-next / do-later / do-not-do-yet discipline
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` — runtime doctrine, ratified 2026-04-17
- `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` — runtime slice plan, ratified 2026-04-17
- `docs/DOCTRINE_v2.4.x.md` — 12 standing principles
- `docs/MCP_EXPANSION_GUIDE.md`, `docs/PATH_3_MCP_DEVELOPER_EXPERIENCE.md` — MCP extension + boundary language

> This document freezes the **preconditions** for Block A implementation work on the regrouped memory roadmap. It is a ratification gate, not a design spec. It does not pre-decide Block A's substrate shape, baton structure, or lifecycle mechanics — those belong to the Block A design doc, which cannot start until this document is ratified.

---

## 1. Mission sentence for this phase

> **TORMENT is proving a memory-first, state-governed runtime where policy, drift, and bounded reflex can shape behavior without collapsing into generic agent-tool scaffolding.**

All four clauses are load-bearing. "Memory-first" names the center of gravity. "State-governed" names the gate stack (policy, drift, mode-legality). "Policy, drift, and bounded reflex shape behavior" is the testable claim that math steers behavior. "Without collapsing into generic agent-tool scaffolding" is the explicit negation of the failure mode.

"Bounded reflex" is internally meaningful but jargon-heavy for external audiences. Translate when the sentence needs to leave the doctrine room.

---

## 2. Runtime / roadmap handoff rule

Block A implementation may run in parallel with the ratified runtime slice (`docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md`). "Parallel" is permissible **only** under the regression rule below.

> **Block A work must plug into the existing 8-phase runner at every implementation milestone. No Block A change is accepted that regresses any test in the nine-invariant scorecard from the runtime slice plan §7, unless a separately ratified runtime change explicitly updates that scorecard.**

### Nine-invariant scorecard (tests already exist in `tests/`)

| # | Invariant | Test |
|---|-----------|------|
| 1 | Memory is never exposed as open-ended search to the LLM | `test_tool_surface_whitelist.py` |
| 2 | The model never receives an open tool-choice menu | `test_tool_narrowing.py` |
| 3 | Drift in the high regime can veto outward action | `test_drift_veto.py` |
| 4 | Assimilation outcomes are not model-chosen intents | `test_assimilation_outcomes_not_deliberative.py` |
| 5 | Internal reflexes may run without an LLM call | `test_reflex_no_llm.py` |
| 6 | Governance can narrow legality but never widen it | `test_governance_narrowing.py` |
| 7 | TOOL mode legality differs pre- and post-execution by declared rule | `test_action_policy_legality.py` |
| 8 | Review may veto or revise on declared grounds but may not re-enter earlier phases | `test_review_no_loopback.py` |
| 9 | Fallback chain runs closed, not open | `test_fallback_chain.py` |

Plus the end-to-end smoke: `test_agent_loop_smoke.py`.

The "unless separately ratified" clause exists to prevent temporary regression waivers. Any Block A change that needs to invalidate a scorecard test requires its own doctrine-shaping ratification — not a skip, not a `@pytest.mark.xfail`, not a "we'll fix it next week."

---

## 3. Red lines

The existing red lines from `Roadmap_working_memo.md` ("DO NOT DO YET" §1–7) remain in force, inheriting from `DOCTRINE_v2.4.x.md` principles 5 (provenance as hard boundary), 6 (automatic before autonomous), 7 (MCP governed), and 9 (safe defaults, risky features gated). MCP-specific "what not to build" rules remain owned by `docs/PATH_3_MCP_DEVELOPER_EXPERIENCE.md` §5 and `docs/MCP_EXPANSION_GUIDE.md`. Both are referenced, not duplicated here.

This section **adds two red lines** that were latent in the working memo but not made explicit.

### Red line R+1 — No LLM-driven semantic compaction of durable memory

Mechanical compaction is permitted: drop oldest low-priority entries, remove revised-out items, cap per-section counts. These are structure-preserving operations.

LLM-style semantic compaction of durable memory is **forbidden** until the open governance question from `TORMENT_Memory_Roadmap_Regrouped.md` §10 (compaction-vs-ratification) is resolved by explicit ratification. Forbidden forms include but are not limited to: summarization of multiple entries into one; "essence-preserving" rewrites; reinterpretation-style compression; any automated pass that changes the meaning of a durable entry rather than structurally removing it.

This red line closes an unflagged drift path where durable memory could be silently reshaped under the name of cleanup.

### Red line R+2 — No automatic contradiction resolution in durable memory

Contradiction **surfacing** is in-doctrine and remains permitted. Contradiction **resolution** is persistence-shaping and requires explicit ratification per case.

No Block A or runtime change may auto-resolve a contradiction in durable memory — no overwrite, no merge, no prefer-newer, no prefer-confirmed — without surfacing it for ratification first. Revision history must remain a first-class artifact.

Both red lines are load-bearing for Block A specifically, because the substrate is the first place these failure modes become expressible in code.

---

## 4. Acceptance-criteria-before-start rule

Before Block A spec work begins, the Block A design doc must declare **3–5 concrete, testable acceptance criteria**. Each criterion must name the test or code-review step that will verify it.

If the design doc cannot produce 3–5 such criteria before starting, Block A is not ready to begin. The inability to state criteria is diagnostic, not an obstacle to work around.

### Illustrative criteria (examples, not the complete set)

These examples are drawn from the regrouped roadmap analysis and are intended to show the level of concreteness expected. The Block A design doc may adopt, modify, or replace them.

- **Substrate behaviors.** Agent can create, revise, search, and soft-delete entries. Provenance preserved on every write. Contradiction surfaced on write against an existing entry.
- **Baton structure.** Five-field minimum (`content`, `why_still_live`, `owner`, `expires_or_resolves_when`, `status`). `owner` and `expires_or_resolves_when` are required. Soft-consume on resolution rather than silent delete. Aging signal at session start.

The rule is about the discipline of writing testable criteria before implementation, not about locking these particular examples.

---

## 5. Evaluation harness minimum

Block A's evaluation harness, proven by Block A's closing milestone, must include at minimum the following three tests. Each lives in the section that owns it; none of them duplicates the runtime scorecard from §2.

### 5.1 — Negative persistence test

Proves the **absence** of the "temporary silently becomes durable" failure mode. Concrete form: after a baton is resolved via its declared resolution path, baton content is not retrievable via the durable-memory retrieval primitive, regardless of content similarity or recency.

This is the failure-mode-prevention test. It exists because the roadmap's ethics frame (§7.6 of the regrouped roadmap) is built around preventing specific failure modes, not just proving success cases.

### 5.2 — Category-boundary test

Proves substrate, baton, reference, environment, and closure categories do not blur. Concrete form: a write attempt with baton-shaped intent but no `owner` or `expires_or_resolves_when` is rejected, not silently promoted to ordinary semantic memory. Equivalent rejection tests for each adjacent category pairing.

### 5.3 — Block-A-meets-runtime integration test

Proves Block A's substrate hooks into the 8-phase runner without regressing the scorecard. Concrete form: a full turn through `agent_loop.run_turn` executes successfully with Block A substrate in play, and at least one scorecard invariant test continues to pass while substrate-backed memory is exercised.

This is the seam test. It owns the "Block A meets runtime" concern so that §2's scorecard owns only the runtime concern. Runtime-policy correctness beyond this seam remains owned by the existing scorecard.

---

## 6. Extension contract as downstream deliverable

Block A must ship with `EXTENSION_CONTRACT.md` at close. That document is a **cover index**, not a restatement of per-surface guides. Its job is to let a modder and the design team see, on one page, what extension surfaces exist and which doc covers each.

### Required rows (minimum — Block A may add more)

- **New persona / behavior pack** → write a pack. Reference implementations: `behavior_packs/debugging_session.py`, `behavior_packs/research_assistant.py`.
- **New tool family** → add to `tool_registry`. Reference implementation: `code_exec`.
- **New executor** → implement the `ToolExecutor` Protocol. Reference implementation: `SubprocessPythonExecutor`.
- **New policy rules** → add to `action_policy`. Requires ratification — touches doctrine.
- **New MCP tool** → reference `docs/MCP_EXPANSION_GUIDE.md`. That guide remains the canonical per-surface doc; the contract cites it rather than restating.
- **New memory category or lifecycle class** → specified by the relevant design doc; Block A owns the initial substrate / baton form.

A proposed new extension surface that does not fit any row of the contract is an architecture-expansion request and must be challenged, not silently accepted.

This document **requires** `EXTENSION_CONTRACT.md` to exist at Block A close; it does not pre-decide the contract's final wording. The contract's content is Block A's responsibility.

---

## 7. Writeback-vs-closure hard guardrail

Writeback and closure look similar from a distance — both compress, both convert in-flight material to durable form, both involve ratification — but they are different risk classes:

- **Writeback risks** are finer-grained: correctness of specific findings (did we promote the right item?). Per-item gate.
- **Closure risks** are arc-level: narrative honesty (is this retrospective true to what actually happened?). Compresses meaning; carries ethical weight that writeback does not.

If the two converge mechanically, each loses its distinguishing rigor. Closure becomes "just ratify and commit" and sheds its ethical layer. Writeback becomes "just synthesize" and sheds its per-item gate rigor.

### Hard guardrail

Writeback and closure **must not share** test infrastructure, harness code, or review checklists. Any PR that touches both without clearly separating the paths requires explicit doctrine review before merge. Separate paths, separate tests, separate reviews.

This rule applies at the Block A / Block C boundary and at any future point where writeback and closure touch the same runtime surface. It is a hard guardrail, not a mental note.

---

## 8. What this document does not cover

- **Block A design.** Substrate shape, baton fields beyond the minimum, lifecycle transitions, retrieval primitives, protected-vs-free classes, deletion semantics. All Block A design is owned by the Block A design doc.
- **Runtime slice implementation.** Owned by `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md`.
- **MCP extension and boundary material.** Owned by `docs/MCP_EXPANSION_GUIDE.md`, `docs/PATH_3_MCP_DEVELOPER_EXPERIENCE.md`, `docs/MCP_CAPABILITY_BOUNDARY.md`.
- **High-level doctrine.** Owned by `docs/DOCTRINE_v2.4.x.md`.
- **Branch / merge workflow.** Implementation plumbing, not a doctrinal precondition. The regression rule in §2 is the only doctrinal constraint this document places on parallel work.
- **Block B or Block C preconditions.** To be drafted in their own precondition docs when Block A is closing.

---

## 9. Ratification record

**Drafted:** 2026-04-19 by Claude, following ratified direction from user + GPT conversation the same day.

**Ratification pass (2026-04-19):**

- [x] §1 — Mission sentence wording accepted
- [x] §2 — Runtime/roadmap handoff rule + nine-invariant scorecard + "unless separately ratified" clause accepted
- [x] §3 — Red lines R+1 (no LLM semantic compaction of durable memory) and R+2 (no automatic contradiction resolution) wording accepted
- [x] §4 — Acceptance-criteria-before-start rule (3–5 testable criteria threshold) accepted
- [x] §5 — Evaluation harness minimum (negative persistence, category boundary, runtime integration) accepted
- [x] §6 — `EXTENSION_CONTRACT.md` as downstream deliverable accepted (§6 extension-row language reworded to "New memory category or lifecycle class" during draft review)
- [x] §7 — Writeback-vs-closure hard guardrail accepted (scope extended to include shared review checklists during draft review)
- [x] §8 — Scope boundary (what this doc does not cover) accepted

**Status:** **RATIFIED 2026-04-19 by user + GPT.** Block A may now move to its design-doc phase. Block A spec work is bound by the rules frozen in this document. Any change to these rules requires a separately ratified amendment.

**Handoff notes for the Block A design doc (carried forward from ratification discussion):**

- Keep Block A's ownership tight — initial substrate form, initial baton form, and the lifecycle/retrieval semantics Block A actually owns. Do not absorb Block B (reference, environment), Block C (closure), or the full `EXTENSION_CONTRACT.md` body into the Block A design doc just because those topics are architecturally adjacent.
- The first thing the Block A design doc must do is satisfy §4 of this document: declare 3–5 concrete, testable acceptance criteria up front, then design against them — not the other way around.

---

## Appendix — Source trail

Assembled from:
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` (architecture freeze)
- `roadmap_tests/Roadmap_working_memo.md` (operating discipline)
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` + `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` (runtime doctrine + scorecard)
- `docs/DOCTRINE_v2.4.x.md` (standing principles)
- `docs/MCP_EXPANSION_GUIDE.md`, `docs/PATH_3_MCP_DEVELOPER_EXPERIENCE.md` (MCP extension/boundary language referenced but not restated)
