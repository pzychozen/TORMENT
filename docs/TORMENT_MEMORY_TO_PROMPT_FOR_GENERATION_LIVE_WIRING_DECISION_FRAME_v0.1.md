# TORMENT — Memory-to-Prompt-for-Generation Live Wiring Decision Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / decision frame only / no live caller selected / HOLD
preserved.** Hilmir authorized **only this decision frame**; Codex PASS. It writes **no code
and no tests**, **wires nothing**, **selects no live caller**, and makes **no endpoint / API /
schema / public-surface change**. Where this frame and any parent contract/guard differ, the
contract/guard wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `f9a97ff` (repo edge). Subordinate to, and may not contradict: the live-caller
eligibility frame (`2cc5210`), the orchestration decision frame (`e037ad1`), the
CALLER-PROPOSAL frame (`4fa96ea`), the implementation-proposal frame (`9eff11c`), the dormant
runner seam (`5d04658`), the dormant memory-context orchestrator (`b3b5647`), and the three
closed evidence harnesses (`75dba41`, `81b625e`, `b61cddb`).

## 2. The exact decision question

> May the project advance to a later, separately authorized LIVE-CALLER-PROPOSAL for
> production memory-to-generation wiring, and if so which terrain may be considered as the
> owner of the same-turn path from governed retrieval/assembly to
> `AgentRunner.run_turn(..., memory_context_text=...)`?

## 3. Evidence now available

```text
- b3b5647  feat(cognition): add dormant memory context orchestrator (code + tests, dormant).
- 75dba41  test(cognition): add fake local operator demo harness.
- 81b625e  test(cognition): add bounded provider/manual harness.
- b61cddb  test(cognition): add bounded real-retrieval manual harness.
- f9a97ff  docs(project): §0 closure for the real-retrieval harness (current edge / anchor).
```

What the evidence establishes:

```text
- AgentRunner has a DORMANT runner-local memory_context_text seam
  (_execute_with_prompt_request → _execute → _build_llm_prompt_request →
  _build_memory_context_message); bounded ≤1200, labelled, read-only, turn-local, non-exposed.
- memory_context_orchestrator owns assembly (calls assemble_context(...)) and invokes
  AgentRunner.run_turn(..., memory_context_text=...); it remains CALLED NOWHERE in production.
- The fake local operator harness proves the memory-before-raw prompt shape (memory block
  labelled and ordered before the raw user input; raw input stays separate/later).
- The provider/manual harness proves the runner-built prompt shape can be sent to a real
  provider ONLY under an explicit manual env gate (default fake; no provider import otherwise).
- The real-retrieval harness proves TormentFabric.query(...) can retrieve real local-workspace
  memory and feed the orchestrator/prompt seam SAFELY under an explicit manual env gate (temp
  snapshot; source not mutated; fake runner fabric + fake LLM).
- Manual Ryuki run: workspace/agent = ryuki / ryuki_nox; ST/BGE embedder; 8 retrieved hits;
  temporary snapshot; source_data_mutated = False.
- /agent/query and /retrieve remain untouched throughout.
```

## 4. What this evidence does NOT prove

```text
- It does NOT authorize live production wiring.
- It does NOT authorize endpoint changes.
- It does NOT prove memory should control output.
- It does NOT add review / suppression / retry / ranking / style steering.
- It does NOT authorize provider runtime.
- It does NOT authorize persistence / write / logging / transcripts.
- It does NOT open U1 / audit-owner / private-owner / selected-items routes.
- It does NOT open Gate D / private cognition / dream / Envelope Audit runtime.
- It does NOT open database / substrate.
```

## 5. Candidate terrains to evaluate — ON PAPER ONLY

```text
A. Existing app.py / /agent/query terrain (as possible orchestration terrain).
   - Considerable ONLY as future terrain, because it is the existing live query entry terrain.
   - This frame must NOT touch it; it stays unmodified.
   - It is NOT selected here.
   - Any later proposal must prove NO public-surface / schema / API drift unless separately
     authorized.

B. A new internal, non-endpoint production orchestration caller.
   - Considerable because the prior candidate-6 shape used an internal orchestrator.
   - Must be SEPARATELY proposed.
   - NOT invented / designed / named here beyond the terrain category.
   - NOT selected here.

C. Existing memory_context_orchestrator.py.
   - It is the dormant callee / assembly owner.
   - It is NOT automatically a live caller.
   - It remains called nowhere in production unless a later proposal selects a caller.

D. TormentFabric.query(...), assemble_context(...), AgentRunner.run_turn(...).
   - Treat as source / generation components.
   - They are NOT themselves enough to be a live caller unless a same-turn owner proves the
     full path (governed retrieval/assembly → memory_context_text → run_turn) in one turn.
```

## 6. Forbidden terrains

```text
- /retrieve as generation terrain (it stays read-only / context-source only).
- AgentRunner owning retrieval / assembly.
- PrivateGenerationOwner.
- the selected-items audit bridge / U1 / audit-owner routes.
- the harnesses as production callers.
- the provider / manual paths as production runtime.
- any endpoint / API / schema / public-surface change.
```

## 7. Decision options

```text
- Option A: HOLD forever — no LIVE-CALLER-PROPOSAL ever admissible.
- Option B: a later LIVE-CALLER-PROPOSAL is admissible, but ONLY separately authorized and
            source-grounded.
- Option C: live wiring implementation now.
```

Verdict:

```text
- REJECT Option A — too strong: the closed evidence arc is enough to ask a later
  caller-proposal question; foreclosing it has no source basis.
- SELECT Option B — only.
- REJECT Option C — absolutely: no live wiring, no implementation now.
NET ANSWER: a later LIVE-CALLER-PROPOSAL is admissible; live wiring remains HOLD now.
```

## 8. Proof obligations before any later code/test wiring

Any later, separately authorized LIVE-CALLER-PROPOSAL (and the code+tests slice after it) must
prove ALL of:

```text
- a SOURCE-FIRST caller survey at the then-current edge;
- an EXACT same-turn ownership proof (one owner holds governed assembled context AND the
  authoritative run_turn invocation in the same turn);
- the governed memory text source is ONLY AssembledContext.assembled_text or a bounded
  derivative of it;
- the runner stays CONSUMER-ONLY: AgentRunner imports/owns no assembler / retrieval;
- /retrieve stays read-only / context-source;
- the memory stays bounded, labelled, read-only, non-authoritative, turn-local, non-public,
  non-persistent;
- tests / AST guards for the SANCTIONED caller only;
- guards for NO forbidden imports / routes;
- guards for NO public exposure;
- guards for NO control / write feedback;
- an explicit NO-PROVIDER-RUNTIME guard.
```

## 9. Must remain HOLD

```text
- live production wiring;
- /agent/query (unmodified);
- /retrieve (unmodified);
- schema / API / public surface;
- provider runtime;
- audit-owner / U1 / private-owner;
- persistence / write / logging / transcripts;
- any implementation.
```

## 10. Required no-go list (this step)

```text
No code, tests, wiring, live caller selection, endpoint behavior change, persistence / write /
logging / transcripts, provider calls, output control, review / suppression / retry / ranking /
style steering, hidden finalizer / refusal / identity rewrite, hidden chain-of-thought storage /
exposure, Gate D / private cognition / dream / Envelope Audit runtime, database / substrate /
carrier / schema / storage / migration, Gate B / R-field / Probe-v1 / shaping.
```

## 11. Final verdict

**A later, separately authorized LIVE-CALLER-PROPOSAL is admissible.** No live caller is
selected now. No production wiring is authorized now. The lane remains **HOLD** until
Hilmir + Codex authorize the next proposal. The recommended next move is a **source-first
live-caller proposal review**, not code.

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION LIVE WIRING DECISION FRAME / DOCS-ONLY /
NON-AUTHORIZING / NO LIVE CALLER SELECTED / HOLD PRESERVED. It records the closed evidence arc
(dormant orchestrator `b3b5647`; fake operator harness `75dba41`; bounded provider/manual
harness `81b625e`; bounded real-retrieval harness `b61cddb`; closure `f9a97ff`), states what
that evidence does and does NOT prove, evaluates candidate terrains A–D and the forbidden
terrains ON PAPER ONLY, and selects **Option B only**: a later LIVE-CALLER-PROPOSAL is
admissible, but only separately authorized and source-grounded; HOLD-forever (A) is rejected as
too strong and live wiring now (C) is rejected absolutely. It lists the proof obligations any
later wiring must satisfy and the items that must remain HOLD. **It selects no caller, wires
nothing, writes no code/tests, changes no endpoint/API/schema/public surface, authorizes no
provider runtime, opens no lane, and lifts no fence; implementation is not authorized, and any
live wiring requires separate Codex/operator authorization.** Memory remains guidance, not
authority; audit observes authority and does not become authority; nothing rewrites identity /
canon / seed / soul.
