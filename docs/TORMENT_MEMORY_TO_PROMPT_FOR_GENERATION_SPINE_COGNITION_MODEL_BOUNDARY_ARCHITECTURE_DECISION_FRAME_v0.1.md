# TORMENT — Memory-to-Prompt-for-Generation Spine Cognition Model-Boundary Architecture Decision Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / architecture decision frame / no code / no tests / no wiring /
implementation HOLD.** This frame evaluates architecture options ON PAPER and records a
direction (or HOLD). It writes **no code and no tests**, implements/designs **no** concrete
model-boundary code, wires **nothing**, makes **no endpoint / schema / API / public-surface
change**, authorizes **no provider runtime**, and opens **no** database/substrate work.
AgentRunner live wiring, Terrain B runtime, and database/substrate all remain **HOLD**. Where
this frame and any parent contract/guard differ, the contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `ada3a64` (docs(project): close Spine memory context lock). Substantive evidence:
`f480b69` (test(cognition): lock Spine memory context characterization).

## 2. Evidence baseline (test-locked at `f480b69`)

```text
- live Spine/cognition path is DETERMINISTIC:
  route → build_memory_context → role.run(memory_context) → reintegrate(memory_context) → result dict;
- memory_context is same-turn / advisory / internal / NON-MODEL-VISIBLE;
- cognition/ and roles/ contain NO LLM/model/prompt boundary;
- final_answer is DETERMINISTIC (a " | ".join of role summaries; LLM synthesis is a FUTURE
  docstring note in _build_final_answer, not a call);
- /retrieve and AssembledContext.assembled_text are NOT the live Spine path;
- AgentRunner and Terrain B are EXCLUDED from the live Spine path;
- no output-control / review / suppression / retry / ranking / style steering;
- no Spine-path writeback / transcript;
- validation: 11 source/AST tests OK.
```

## 3. Required source anchors (referenced, preserved — not reopened)

```text
- tests/test_spine_cognition_memory_context_characterization_lock.py  (the lock)
- cognition/pipeline.py · cognition/reintegration.py · cognition/apertures.py · roles/
- torment_service/spine.py · torment_service/app.py · torment_service/retrieval_assembler.py
- torment_service/agent_loop.py · torment_service/memory_context_orchestrator.py
```

Terrain B is NOT reopened as live terrain; `/retrieve` is NOT treated as generation terrain.

## 4. Candidate architecture options (evaluated ON PAPER)

### Option A — Keep Spine deterministic
```text
- live Spine/cognition remains deterministic; memory stays same-turn advisory memory_context;
  no model-visible prompt enters live Spine; prompt-based memory-to-generation stays outside
  this path for now.
- Safety: maximal — no model output authority on the governed/identity path; no endpoint drift;
  preserves all locked invariants.
- Remains possible: deterministic cognition, governance, drift gates, role synthesis.
- Remains impossible: live natural-language LLM generation through the Spine.
- Impact on the memory-to-prompt lane: the lane has no live home on the Spine; it stays in the
  separate AgentRunner runtime (HOLD).
- This is effectively the CURRENT state; as a verdict it would read as "HOLD-for-now" rather
  than a durable rejection.
```

### Option B — A bounded internal model-visible synthesis stage inside cognition/reintegration (later, separately gated)
```text
- candidate seam: the FUTURE "_build_final_answer LLM-synthesis" point hinted in its docstring;
  memory_context could become source material for a bounded model-visible synthesis request.
- Plausible because the seam is already named and reintegrate already owns final_answer.
- RISKS: it places a model boundary on the deterministic GOVERNANCE/identity path; it couples
  the endpoint response to LLM output (response/schema/public-surface drift); it risks model
  output gaining authority over the governed result; it would require heavy guards (bounds,
  labels, read-only, no writeback, no output-control, same-turn provenance, endpoint-surface
  preservation). No code is authorized now; this would need a SEPARATE implementation proposal
  + tests. Memory must remain guidance, not authority.
- It muddies the clean deterministic/LLM separation the lock just established.
```

### Option C — Keep Spine deterministic; route prompt-based memory-to-generation to a separate non-Spine LLM-bearing runtime (separately gated)
```text
- live Spine stays deterministic; prompt-based memory-to-generation belongs to a SEPARATE
  LLM-bearing runtime; AgentRunner / Terrain B remain HOLD unless separately reopened.
- Benefits: preserves clean separation of concerns (Spine = deterministic cognition/governance;
  a separate runtime = LLM generation); aligns with where AgentRunner already sits; keeps the
  governed path free of model-output authority.
- Risks: a separate LLM runtime could become a hidden parallel product surface if not governed;
  requires a separate architecture/proposal gate and explicit ownership/observability rules.
- Relation to the prior arc: this is essentially the AgentRunner direction, kept disjoint and
  gated rather than retrofitted onto the live Spine.
```

### Option D — HOLD until a broader runtime/product decision exists
```text
- no direction chosen; model-boundary design deferred; both a live-Spine model boundary and a
  separate LLM-bearing runtime remain HOLD.
- A broader runtime/product decision is necessary because the choice among A/B/C/E depends on
  whether and where TORMENT wants live LLM generation — a PRODUCT/RUNTIME question that source
  evidence alone cannot resolve (the lock proves the current shape, not the desired one).
- Missing evidence: an operator/product statement of intent about live LLM generation and its
  home; that is the operator's fork, not a source-derivable fact.
```

### Option E — REJECT live-Spine model-visible generation permanently
```text
- live Spine must never host model-visible generation; prompt-based memory-to-generation must
  remain separate forever or be abandoned.
- Evidence does NOT support a PERMANENT rejection: nothing in source proves a model boundary is
  inherently unsafe — only that it does not exist today and would be risky on the governance
  path. Permanent rejection over-constrains future architecture; it is TOO STRONG.
```

## 5. Decision criteria

```text
- preserves memory as guidance, not authority;
- avoids hidden output-control / review / suppression / retry / ranking / style steering;
- avoids endpoint / schema / API / public-surface drift unless separately authorized;
- avoids persistence / write / logging / transcripts;
- preserves non-public / non-persistent memory behavior;
- preserves same-turn provenance;
- keeps AgentRunner / Terrain B excluded unless separately reopened;
- avoids database / substrate creep;
- leaves implementation / tests / live wiring HOLD.
```

## 6. Required proof obligations before any future implementation

```text
A later implementation proposal (for B or C) would need to specify:
- the precise model-boundary owner;
- the exact model-visible input shape;
- the memory-source contract (governed memory only);
- the prompt/request capture rule;
- same-turn provenance;
- bounds / labels / read-only guarantees;
- non-public / non-persistent guarantees;
- no writeback;
- no output-control path;
- endpoint-surface preservation;
- AST/source guards preserving AgentRunner / Terrain B exclusion unless a separate gate
  explicitly reopens them;
- a provider-runtime gate;
- a transcript/logging prohibition OR an explicit, separately-gated observability decision;
- tests for no /retrieve generation;
- tests for no public exposure of memory_context;
- tests for no model-output-to-memory feedback.
```

## 7. Forbidden routes (this step)

```text
- code; tests; implementation; wiring; endpoint edits; provider runtime;
- model-boundary implementation;
- AgentRunner live wiring; Terrain B runtime;
- /agent/query retrofit; /retrieve generation; schema/API/public-surface drift;
- database/substrate work; persistence/write/logging/transcripts;
- output-control/review/suppression/retry/ranking/style steering.
```

## 8. Must remain HOLD

```text
- implementation; tests; live wiring; provider runtime; model-boundary code;
- AgentRunner / Terrain B; /agent/query; /retrieve; public surface; database/substrate;
- output-control paths; persistence paths.
```

## 9. Final verdict

**Option D — HOLD until a broader runtime/product decision exists.** The lock (`f480b69`)
establishes WHAT the live path is (deterministic; no model boundary), not what it SHOULD become.
The choice among keeping the Spine deterministic (A), adding a model boundary inside the
deterministic governance path (B), routing generation to a separate LLM-bearing runtime (C), or
permanently rejecting live-Spine generation (E) turns on whether and where TORMENT wants live
LLM generation — a **product/runtime decision that is the operator's fork**, not a
source-derivable fact. Therefore no direction is forced here.

**Reasoned architectural note (not a selection):** if a model-bearing generation path is ever
wanted, the evidence favours **C over B** — keeping the deterministic Spine/governance path
intact and housing prompt-based memory-to-generation in a SEPARATE, separately-gated
LLM-bearing runtime (where AgentRunner already sits, HOLD) — rather than placing a model
boundary inside `cognition/reintegration` (B), which would couple the governed/identity path to
model-output authority and risk endpoint drift. **E (permanent rejection) is too strong** (it
over-constrains future architecture). **A** (keep Spine deterministic for now) is the current
state and is preserved under this HOLD.

**Implementation is NOT authorized. Tests are NOT authorized. Live wiring is NOT authorized. A
separate Codex/operator gate is required before any next step. Current source remains
unchanged.**

## 10. Recommended next

```text
Per Option D: the next move is a BROADER RUNTIME/PRODUCT DECISION frame (does TORMENT want live
LLM generation, and where should it live — separate runtime vs in-path) OR HOLD. NOT code.
AgentRunner live wiring and Terrain B remain HOLD; the Spine facts remain test-locked.
```

## 11. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SPINE COGNITION MODEL-BOUNDARY ARCHITECTURE DECISION
FRAME / DOCS-ONLY / NON-AUTHORIZING / ARCHITECTURE DECISION / IMPLEMENTATION HOLD. Evidence
baseline test-locked at `f480b69`: the live Spine/cognition path is deterministic
(route → build_memory_context → roles → reintegrate), memory_context is same-turn/advisory/
internal/non-model-visible, no LLM/model/prompt boundary exists in cognition/ or roles/,
final_answer is deterministic, `/retrieve`/`AssembledContext.assembled_text` are excluded, and
AgentRunner/Terrain B are excluded. It evaluates options A–E and selects **Option D — HOLD until
a broader runtime/product decision exists**, with a reasoned (non-selecting) lean that, if live
generation is ever wanted, C (separate non-Spine LLM-bearing runtime) is cleaner than B (model
boundary inside deterministic reintegration), and E (permanent rejection) is too strong; A is
the current state preserved under HOLD. **It authorizes no code, no tests, no implementation, no
wiring, no endpoint/API/schema/public-surface change, no provider runtime, no model-boundary
code, no AgentRunner live wiring, no Terrain B runtime, and no database/substrate work; the next
move is a broader runtime/product decision frame, not code, under separate Hilmir + Codex
authorization.** Memory remains guidance, not authority; audit observes authority and does not
become authority; nothing rewrites identity / canon / seed / soul.
