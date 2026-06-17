# TORMENT Gate A — Live-Advisory Boundary Trace Plan v0.1

**CHARACTERIZATION-ONLY. NO CODE. NO TESTS. NO FIXES. NO IMPLEMENTATION. NO RUNTIME CHANGE.**

Gate A is opened **only as a characterization gate.** "Boundary lock" here means a
*proposed/characterized* boundary first — **not enforcement.** This artifact is a **trace
plan** (what evidence will be gathered later), not the trace itself and not proof. Any
later tests-only regression locks require **separate explicit authorization after this
plan is reviewed.** Production fixes are forbidden.

**Date:** 2026-06-17. **Lineage:** cognition roadmap sequencing map → Gate A opening proposal
→ Codex sharpened scope → operator authorization (characterization-only) → this trace plan.

---

## 1. Status and scope

- **HEAD = origin/main = `0ff0769`** ("docs(engine): file cognition roadmap sequencing map").
- **Gate A opened as characterization-only.** No code, no tests, no fixes, no implementation,
  no runtime behavior change is authorized by this artifact.
- Purpose: define the **plan** to trace and characterize the live advisory/thinking boundary
  against Document A — to be executed read-only in a later step, then reviewed before any
  tests or locks.

## 2. Codex corrections carried

- **Advisory is influence, not automatically harmless.** Retrieval shaping and response
  assimilation can still influence what later becomes memory.
- **Retrieval shaping can affect visibility/context** (what is surfaced into a turn), even
  without writing.
- **Ordinary Phase-7 turn-summary ingest must be traced** — it is a real write path.
- **Ordinary ingest is NOT Document B private-cognition admission** — the two must be kept
  distinct; tracing one must not relabel it as the other.
- **Writer hazards remain visible and parked** (§7), not absorbed into Gate A.

## 3. Live advisory dataflow — trace surface (targets)

Intended surfaces to map (read-only, later):

```
ThinkingController  →  MemoryPlan  →  retrieval shaping (fabric.query lane budgets/weights)
   →  draft / review / stance surfaces  →  geometric context / geometric harvesting
   →  /agent/query  (single-shot)  AND  AgentRunner.run_turn  (outer loop)
   →  Phase 7 ordinary ingest (turn assimilation)
   →  Spine advisory / alignment / audit surfaces
   →  any write path reachable from advisory-shaped outputs
```

Concrete code targets: `thinking_controller.py` (`think`, `deliberate_only`, MemoryPlan
builder, `determine_stance`, `_draft_response`, `review`); `geometric_harvester.py`;
`action_policy.py` / stance policy; `app.py` `/agent/query`; `agent_loop.py`
`AgentRunner.run_turn` and the Phase-7 assimilation step; `fabric.query` (MemoryPlan
consumption); `spine.py` advisory/alignment/audit surfaces; and the write entrypoints
(`fabric.ingest`, `spawn_memory`) **only** to confirm reachability/non-reachability — not to
modify them.

## 4. Questions the trace must answer

1. Does any advisory output **write directly**?
2. Does any advisory output **persist indirectly** (via assimilation, audit, logs, or state)?
3. Does **MemoryPlan only shape retrieval**, or does it influence **admission/authority**?
4. Does **response assimilation ingest advisory-shaped output as ordinary memory** — and if so,
   is it characterized as ordinary ingest (not private-cognition admission)?
5. Does any advisory artifact **reenter future cognition as private state**?
6. Does any advisory output **bypass writer authority**?
7. Are **Spine / audit surfaces logged, persisted, returned, or reused** — and with what posture?

## 5. Document A boundary claims to characterize

- **Containment / non-reachability** (A-C1/A-C2): which forbidden reachabilities are structurally
  prevented vs tag-dependent.
- **Staging vs admission** (A-D1/A-D2): whether anything crosses into ordinary memory, and via what.
- **Inspection vs projection** (A-I1): whether any advisory/audit surface is operator-auditable
  only vs model/caller/retrieval-visible.
- **Advisory vs authority**: whether advisory output ever gains authority.
- **Ordinary ingest vs private-cognition candidate admission**: the two must stay distinct;
  ordinary turn-summary ingest is not a Document B admission crossing.

## 6. Explicit out-of-scope items

Production fixes; writer-hazard reconciliation; P4 mechanics; Document B private cognition;
dream/incubation; candidate store; durable private state; database/substrate mechanics;
schema/storage/carriers/migration/construction; `canon_source` selection; source-sameness
mechanics; Seed-Gov implementation; monitoring; durable user-risk scoring; autonomy; registry
edits.

## 7. Writer hazards remain parked (kept visible)

Routed to Gate B / separate reconciliation — **not** characterized or fixed here, **not** absorbed
into Gate A:

- `gravity_correction` automatic `canon=True`.
- `_maybe_emit_identity_anchor` automatic derived identity writer.
- `POST /promote` force bypass.
- `mood_drift → centroid → gravity_correction → canon=True`.

## 8. Proof plan (plan, not proof yet)

Evidence to be gathered in the later read-only trace step (each requires this plan to be
reviewed first; tests/locks require separate authorization):

- **Call-graph / dataflow characterization** of the §3 surfaces, answering the §4 questions.
- **Docs characterization checkpoint** recording the §5 boundary claims as characterized
  (proposed boundary), with any exception named and bounded.
- **Possible later tests-only regression locks** — *only if separately authorized after the
  trace*, mirroring the existing characterization-lock pattern; never a production fix.
- **Clear separation** of Gate A (advisory boundary characterization) from Gate B (write-side
  authority + writer hazards), Gate C (P4 read-side), Gate D (Layer-1 thinking + Envelope Audit),
  and the deferred substrate-dependent set.

## 9. Sequence note

This artifact is the **first and only** Gate A deliverable authorized so far. After it is
reviewed, a separate decision authorizes the read-only trace execution; the trace is then
reviewed before any tests-only locks. No step is auto-chained.

---

## Anti-drift footer

CHARACTERIZATION-ONLY trace **plan**. No code, no tests, no fixes, no implementation, no runtime
change. Opens no writer fixes, no P4 implementation, no Document B private cognition, no
dream/incubation, no candidate store, no durable private state, and no database/substrate
mechanics/schema/storage/carriers/migration/construction. Selects no `canon_source` and no
source-sameness mechanics. No monitoring, durable user-risk scoring, or autonomy. No registry
amendment; no registry number reserved. Old-doc quarantine remains binding. Guide, not control;
audit observes authority and does not become authority; nothing rewrites identity/canon/seed/soul.
Subsequent steps (trace execution; any tests/locks) require their own explicit authorization.
