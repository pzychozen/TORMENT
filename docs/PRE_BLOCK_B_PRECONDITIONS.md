# TORMENT Memory Roadmap — Pre-Block-B Preconditions

**Status:** **RATIFIED 2026-04-21** by user + GPT. All nine §10 checklist items accepted after two wording narrowings during review (§2 parallel framing; §6.1 + §6.3 error-mechanism neutrality). Block B may now move to its implementation-analysis phase, using this document as the frame.
**Date:** 2026-04-21
**Scope:** Preconditions for Block B implementation — two stored-but-not-foregrounded memory classes (full-reference memory and environment memory) attached to the substrate core that Block A established.

**Precedents (inherited, not restated):**
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` — ratified 2026-04-19
- `docs/BLOCK_A_IMPLEMENTATION_ANALYSIS.md` — ratified 2026-04-19
- `docs/BLOCK_A_DESIGN.md` — ratified 2026-04-19; merged to main 2026-04-21 (PR #47 + PR #49)
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` — architecture freeze
- `roadmap_tests/Roadmap_working_memo.md` — operating discipline
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` + `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` — runtime doctrine and scorecard
- `docs/DOCTRINE_v2.4.x.md` — standing principles

> This document freezes the preconditions for Block B implementation work. It is a ratification gate, not a design spec. It does not pre-decide the class shapes, retrieval method signatures, scope-tag vocabulary, or lifecycle mechanics — those belong to the Block B design doc(s), which cannot start until this document is ratified. Block B is **not** a "second substrate layer." Block A owns the substrate core. Block B is two memory classes that attach to that substrate core, each with its own retrieval primitive.

---

## 1. Mission sentence for this phase

> **How should TORMENT add stored-but-not-foregrounded memory classes — specifically full-reference memory and environment memory — so that reference objects are pull-for-thinking, environment facts are consult-at-action-site, both remain distinct from Block A core/baton memory, neither breaks lane compatibility or widens writeback/automation authority, and both guide the agent without turning memory into a rigid cage?**

All seven clauses are load-bearing. The two memory classes share an architectural family (stored-but-not-foregrounded) but have **structurally different retrieval mechanics** — formalized in §4 and protected by the red lines in §3.

---

## 2. Runtime / roadmap handoff rule

Block B does not depend on the deferred Block A runtime increments (`SessionLifecycleHook` wiring, `fabric.py` reflex hookup, hardened `code_exec` sandbox). If those increments happen in parallel with Block B, the same regression rule applies: no Block B change may rely on them, and no Block B change may silently absorb them. "Parallel" is permissible only under the regression rule below.

> **Block B work must plug into the existing 8-phase runner at every implementation milestone. No Block B change is accepted that regresses any test in the nine-invariant scorecard from `TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` §7, unless a separately ratified runtime change explicitly updates that scorecard.**

The full nine-invariant mapping is in `PRE_BLOCK_A_PRECONDITIONS.md` §2 and is cited here rather than restated.

The "unless separately ratified" clause has the same meaning here as it did for Block A: no temporary regression waivers, no `@pytest.mark.xfail`, no "we'll fix it next week." Scorecard invariants are doctrine-level; any test change that invalidates one is itself a doctrine-shaping amendment.

---

## 3. Red lines

The existing red lines from `Roadmap_working_memo.md` ("DO NOT DO YET" §1–7), the standing principles from `DOCTRINE_v2.4.x.md`, and the Block A additions R+1 (no LLM-driven semantic compaction of durable memory) and R+2 (no automatic contradiction resolution in durable memory) all remain in force for Block B.

This section adds **four Block-B-specific red lines**.

### Red line R+3 — Reference load must not silently become durable memory

Loading a reference object temporarily elevates it into reasoning context. Loading is not ingestion. A loaded reference object must not silently become a `core` or `baton` substrate entry. Converting reference content into durable substrate memory requires an explicit separate ingest with its own provenance and `parent_eids` linkage to the source reference.

### Red line R+4 — Environment memory must not auto-inject into LLM context

Environment memory is **always consultable**, not **always loaded**. The failure mode this prevents is environment detail continuously injected into LLM prompt context regardless of relevance to the current operation. The correct model is: environment memory is consulted at action sites with relevance filtering; irrelevant environment facts never reach the model.

"Always consultable" ≠ "always loaded." The distinction is load-bearing.

### Red line R+5 — Environment memory creation requires real evidence

Environment memory must never be created from model guesswork alone. A new environment memory entry requires one of:

- **user assertion** — the user explicitly told the system this operational fact;
- **observable system/runtime evidence** — the system directly probed the environment and got a concrete observation;
- **an explicitly ratified inference path** — provenance must mark the entry as inferred rather than observed, and the inference rule itself must be in-doctrine.

"The LLM guessed" is not a valid provenance source for environment memory. Inferred entries must declare themselves as inferred so later code can treat them differently from observed entries.

### Red line R+6 — Reference memory operations are read-only on their source

Reference memory operations are read / attach / load operations, not source-mutation operations. Any operation that writes back to the underlying source (repo file, URL, internal document, generated artifact, stable snapshot) is **out of Block B scope** and requires a separately ratified path.

Loading a reference reads. Loading does not modify. Search, list, load, unload, attach-metadata all read-side only; write-back to source is its own doctrine question.

---

## 4. Formalized retrieval primitive distinction

Block B introduces two categories with **structurally different retrieval mechanics**. The distinction must be preserved visibly in code, not only in prose. This section commits to the *naming* and *non-substitutability* of the two primitives; final method signatures belong to design.

**`load` — reference memory, pull-for-thinking.**
The agent (or runner, acting on pack-declared intent) explicitly elevates a reference object into active reasoning context. Load is intentional, sustained, and reasoning-oriented. The loaded object remains available until explicitly unloaded or until its scope concludes. Staleness is checked on load.

**`consult` — environment memory, consult-at-action-site.**
The agent (or runner) asks whether any environment memory is relevant to a specific operation in a specific scope. Consultation is action-scoped, narrow, and returns only facts relevant to the operation being attempted. The consulted fact never "stays loaded" — it participates in the decision at the action site and then leaves context. Consultation is cheap and invoked at action sites; it is not a default read.

**The two primitives must not collapse.** A future design temptation will be to unify `load` and `consult` behind a generic "get memory" interface. That unification is out of scope for Block B and must not be adopted without a separately ratified amendment to this section. The two primitives have different failure modes — reference is at risk of load-and-never-unload and reference-drift-from-source; environment is at risk of always-injected-clutter, silent-staleness, and scope-failure — and the category discipline depends on the primitives being structurally distinct in the test suite, not just the docstring.

Final method signatures (arguments, return shape, error envelope) are design work. This preconditions doc commits only to the two names and to non-substitutability.

---

## 5. Acceptance-criteria-before-start rule

Before Block B spec work begins, the Block B design doc(s) must declare **3–5 concrete, testable acceptance criteria per category**. Reference memory and environment memory each get their own criteria set; the sets are not merged.

If either category cannot produce 3–5 such criteria before design starts, that category is not ready to begin — and that is diagnostic, not an obstacle to work around.

### Illustrative criteria (examples, not complete sets)

These examples show the level of concreteness expected. The Block B design may adopt, modify, or replace them.

**Reference memory:**
- A loaded reference object is retrievable via the `load` path; it does not appear in Block A default `MemoryPlan` lanes.
- Staleness is checked on load, not on write or at arbitrary intervals.
- Unloading a scoped load is deterministic; no leaked active references remain after the scope concludes.

**Environment memory:**
- `consult(operation, scope)` returns only relevance-filtered facts; unrelated environment entries never appear in the response.
- An environment write that does not declare one of R+5's three evidence classes is rejected at the write call, with no entry created.
- A probe-on-fail path produces an environment entry whose provenance explicitly marks the source as inferred when the observation was indirect.

These are illustrative; the Block B design owns the final set.

---

## 6. Evaluation harness minimum

Block B has two genuinely different categories, so the harness earns extra explicitness over Block A's. Each category proves itself independently; a retrieval-primitive distinctness test and a Block-B-meets-Block-A integration test anchor the cross-category claims.

**6.1 — Reference-memory boundary test.**
Proves reference operations are category-coherent: `load` / `unload` succeed on reference entries; attempting `load` on a non-reference entry returns a specific mismatch result that names the primitive/category error; loaded objects are retrievable via the `load` path but not via Block A default lanes; reference content never silently becomes core/baton on a subsequent write.

**6.2 — Environment-memory boundary test.**
Proves environment operations are category-coherent: `consult` returns only relevance-filtered facts; an environment write without one of R+5's three evidence classes is rejected; environment entries never appear in Block A default lanes; environment facts never auto-inject into LLM context regardless of session state.

**6.3 — Retrieval-primitive distinctness test.**
Proves `load` and `consult` are not substitutable: calling `load` on environment memory or `consult` on reference memory must return a specific mismatch result that names the primitive/category error. The mechanism is open — raised exception, envelope with `ok=False`, or a named result code are all acceptable at design time — but the behavior must not be silent empty, implicit coercion, or convergent success. The two primitives are structurally distinct from the test suite's perspective, not just from the docstring's.

**6.4 — Block-B-meets-Block-A integration test.**
Proves Block B plugs into the substrate without regression: Block A core / baton retrieval is unaffected by Block B entries being present; Block B `load` / `consult` paths do not leak into Block A lanes; all nine scorecard invariant tests remain green when Block B is exercised.

---

## 7. Extension contract deliverable

The `EXTENSION_CONTRACT.md` cover index (drafted during Block A close) requires two new rows at Block B close:

- **New reference memory source kind** — how to register a new reference-source class (repo-file, URL, internal-doc, generated-artifact). Must cite Block B's reference design doc as the canonical per-surface reference.
- **New environment scope tag** — how to register a new `scope_tag` value for environment memory, with the constraint that scope is load-bearing for relevance filtering.

No other extension surfaces change as part of Block B. MCP tools, packs, tool families, executors, policy rules, and Block A substrate classes are all unchanged by Block B.

---

## 8. Writeback-vs-closure guardrail + Block-B-vs-Block-C guardrail

The writeback-vs-closure hard guardrail from `PRE_BLOCK_A_PRECONDITIONS.md` §7 remains in force: writeback and closure must not share test infrastructure, harness code, or review checklists. Block B is not writeback and not closure; this guardrail protects future work from confusing Block B's write paths with either.

**New for Block B: the Block-B-vs-Block-C guardrail.**

Reference objects that later become the subject of closure (arc-synthesis retrospective objects) are still **Block B citizens at the point of storage**. Block B's design must not pre-decide how closure consumes, promotes, or references them — that belongs to Block C.

Specifically:

- Block B does not define closure-related fields on reference entries.
- Block B does not define "this reference is closure-eligible" flags.
- Block B does not add closure-specific provenance factories or write paths.
- Block C, when it lands, inherits Block B's reference entries as-they-are and decides closure semantics then.

If Block B design finds itself needing to decide a closure question to proceed, **surface the contradiction before proceeding** — do not silently widen scope.

---

## 9. What this document does not cover

- **Block B design.** Class shapes, retrieval method signatures, lifecycle transitions, load/unload semantics beyond primitive naming, environment scope-tag vocabulary, probe-on-fail implementation, ownership-class semantics. All owned by the Block B design doc(s).
- **Block A substrate semantics.** Baton, core, archive, and their interactions remain frozen per `BLOCK_A_DESIGN.md`.
- **Block C closure.** Owned by a future Block C design chain, not here.
- **Runtime slice v0.1 internals.** Owned by `TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` and unchanged by Block B.
- **`SessionLifecycleHook` wiring.** Block A declared the Protocol; Block B does not wire it.
- **MCP surface.** Owned by `MCP_EXPANSION_GUIDE.md` and unchanged by Block B.
- **High-level doctrine.** Owned by `DOCTRINE_v2.4.x.md`.
- **Branch / merge workflow.** Implementation plumbing, not a doctrinal precondition.
- **Block D and beyond.** Not under consideration.

---

## 10. Ratification record

**Drafted:** 2026-04-21 by Claude, following the Block B entry framing proposed by user + GPT the same day.

**Ratification pass (2026-04-21, user + GPT):**

- [x] §1 — Mission sentence wording accepted
- [x] §2 — Runtime/roadmap handoff rule accepted — framing narrowed during review from "may run in parallel" (permissive) to "does not depend on" (boundary); same regression rule reaffirmed.
- [x] §3 — Red lines R+3, R+4, R+5, R+6 wording accepted
- [x] §4 — Formalized `load` / `consult` distinction (naming + non-substitutability) accepted
- [x] §5 — Acceptance-criteria-before-start rule accepted (3–5 per category, not merged)
- [x] §6 — Evaluation harness minimum (four tests) accepted — §6.1 and §6.3 wording narrowed during review from "fails with a specific error" (prescriptive) to "must return a specific mismatch result" (mechanism-neutral: raised exception / `ok=False` envelope / named result code all acceptable, as long as behavior is not silent empty, implicit coercion, or convergent success).
- [x] §7 — Extension contract deliverable scope accepted
- [x] §8 — Writeback-vs-closure + Block-B-vs-Block-C guardrail accepted
- [x] §9 — Scope boundary (what this doc does not cover) accepted

**Status:** **RATIFIED 2026-04-21 by user + GPT.** Block B implementation-analysis phase is unblocked. Any change to these rules after this point requires a separately ratified amendment.

### Carry-forward concerns for Block B implementation analysis

Two concerns surfaced during ratification that the analysis phase must keep visibly load-bearing:

1. **`load` and `consult` must stay visibly distinct in code.** Not just different names — different call sites, different expectations, different failure modes. The implementation analysis should actively search the current codebase for *temptation points* where the two primitives might collapse into a generic "get memory" path, and flag them before design starts.

2. **Environment memory is the higher-risk category.** Reference memory's main risks (source drift, load-and-never-unload, overloading) are bounded. Environment memory's risks are systemic: prompt clutter, false certainty from guessed facts, accidental authority widening, silent staleness leading to confident misapplication. The analysis must be especially rigorous on environment-memory evidence paths — R+5's three-evidence-class rule is the load-bearing constraint here.

### Handoff notes for the Block B design doc(s)

Carried forward from the ratification discussion so the design phase inherits them as first-class concerns rather than conversation residue:

1. **Block B is not "a second substrate layer."** Block A owns the substrate core. Block B is two memory classes attached to that core, each with its own retrieval primitive.
2. **`load` and `consult` must remain visibly distinct in code.** Method signatures are design; non-substitutability is a precondition.
3. **Each category produces its own 3–5 acceptance criteria.** Reference and environment do not merge.
4. **Reference operations are read-only on their sources.** Any source mutation is out of Block B scope.
5. **Environment memory creation requires real evidence.** Model guesswork alone is not a valid evidence class; inferred entries must declare themselves as inferred.
6. **Block-B-vs-Block-C boundary is hard.** Block B defines reference and environment storage + retrieval; closure-related semantics belong to Block C when it lands.
7. **Lane compatibility preserved.** Block A's `MemoryPlan` lane interface must continue to work; Block B adds paths, not lane replacements. `RESEARCH_ASSISTANT_PACK`'s `EMPTY_CONTRACT → swap-one-field` promise still holds.

---

## Appendix — Source trail

Assembled from:
- `roadmap_tests/TORMENT_Memory_Roadmap_Regrouped.md` (Items 3 and 5 in the regrouped architecture)
- `roadmap_tests/Roadmap_working_memo.md` (operating discipline)
- `docs/PRE_BLOCK_A_PRECONDITIONS.md` (preconditions pattern carried forward)
- `docs/BLOCK_A_IMPLEMENTATION_ANALYSIS.md` + `docs/BLOCK_A_DESIGN.md` (Block A baseline Block B attaches to)
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` + `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` (runtime doctrine + scorecard)
- `docs/DOCTRINE_v2.4.x.md` (standing principles)
- Block B entry question drafted by user + GPT 2026-04-21; refined and narrowed in the same session
