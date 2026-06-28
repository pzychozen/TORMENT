# TORMENT — Memory-to-Prompt-for-Generation Spine / Cognition Pipeline Architecture Evidence Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / source-first architecture-evidence frame / Terrain B HOLD /
AgentRunner live wiring HOLD / no code / no tests / no wiring.** This frame writes **no code and
no tests**, implements **nothing**, wires **nothing**, makes **no endpoint / schema / API /
public-surface change**, revives **no** Terrain B, wires **no** AgentRunner, does **not** modify
`/agent/query` or `/retrieve`, and creates **no** output-control / review / suppression / retry /
ranking / style steering and **no** autonomy/monitoring expansion. It surveys the live Spine /
`cognition.pipeline` source path ON PAPER, classifies existing memory/context seams, identifies
whether any seam is model-visible, and concludes with a verdict. Terrain B and AgentRunner live
wiring remain **HOLD**. Where this frame and any parent contract/guard differ, the contract/guard
wins.

Standing posture carried verbatim:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.

Anchor: `4f3eecc` (docs(project): close Terrain B live trigger decision).

## 2. Parent closure / why this frame exists

`b569708` proved the Terrain B live trigger is HOLD: the live production cognition path is the
Spine / `run_cognition_pipeline`, while the Terrain B path is the `AgentRunner.run_turn` memory
seam, and the two are architecturally disjoint. Therefore the next valid question is **not** "wire
Terrain B" but: **does the live Spine / `cognition.pipeline` path already have a safe, bounded,
guidance-only memory-to-prompt (or context-shaping) seam — and if not, what is required before any
implementation may be proposed?**

## 3. Current-edge source survey (source-grounded at `4f3eecc`)

```text
A. torment_service/app.py
   - /agent/query (query) builds a SpineRequest and calls submit_task(...);
   - /cognition/run (cognition_run) calls run_cognition_pipeline(...);
   - /spine/submit_task (spine_submit_task) calls submit_task(...);
   - /retrieve (retrieve_assembled) is read-only / context-source; no generation.
   => endpoints enter the SPINE / cognition pipeline; none exposes a model-visible prompt or
      invokes AgentRunner.

B. torment_service/spine.py
   - _full_cognition(fabric, ctx, req) [L986]: builds a TaskPacket from SpineRequest
     (user_input from payload), a query_fn that wraps fabric.query(...), a character_fn (drift /
     seed state), a drift_check_fn, and calls run_cognition_pipeline(task, query_fn, character_fn,
     primary_domains, drift_check_fn) [L1051]. INTENTIONALLY READ-ONLY: it passes NO lookup_fn /
     ingest_fn, so archivist writeback is structurally disabled on this path.
   - the Spine does NOT generate itself; it delegates to cognition.pipeline.

C. cognition/pipeline.py + adjacent cognition modules
   - run_cognition_pipeline(task, query_fn, character_fn, drift_check_fn, primary_domains,
     ingest_fn, lookup_fn, lane_provider) [L28]:
       route(task) → build_memory_context(...) → execute deterministic roles
       (ROLE_REGISTRY / ROLE_EXECUTION_ORDER; role.run(task, memory_context, role_outputs)) →
       reintegrate(...) → result dict (final_answer, merged_findings, dissent, memory_effects,
       drift_report, governance_rejections, role_summaries, routing).
   - DECISIVE: a grep across the ENTIRE cognition/ package finds NO llm / llm_client / .complete( /
     model / prompt / provider client / openai / anthropic. **The live cognition pipeline has NO
     model-visible prompt and NO LLM/model generation boundary — it is DETERMINISTIC (role-based).**
   - memory enters as `memory_context` (built from query_fn=fabric.query retrieval + character +
     drift) and is consumed by DETERMINISTIC ROLES + reintegration — it is NOT a model prompt.

D. torment_service/thinking_controller.py / MemoryPlan
   - MemoryPlan (top_k / weight by lane) is ADVISORY retrieval/context shaping; it does not control
     output and is not a model-visible prompt; it writes/persists nothing.

E. torment_service/fabric.py — query/retrieval
   - TormentFabric.query(...) returns rescored core hits ("results"); it performs NO generation and
     supplies retrieval evidence/context only.

F. torment_service/retrieval_assembler.py and /retrieve
   - assemble_context(...) → AssembledContext.assembled_text is the /retrieve assembler. It is
     read-only context-source terrain. **It does NOT feed the live cognition pipeline** — the
     pipeline uses build_memory_context (aperture), a DIFFERENT context builder. assembled_text is
     not model-visible in the live Spine path (there is no model there).

G. torment_service/mcp_server.py
   - references no AgentRunner / run_turn / orchestrator and no generation; it is a memory /
     projection surface (live projection / negative terrain). It neither calls cognition.pipeline
     to generate model-visible prompts nor invokes AgentRunner.

H. Excluded negative terrain
   - agent_loop.py (AgentRunner LLM path), memory_context_orchestrator.py, PrivateGenerationOwner,
     selected-items bridge — all EXCLUDED Terrain B / negative terrain. NOT revived here.
```

## 4. Candidate seams — classification

```text
SEAM                                   | CLASSIFICATION
---------------------------------------+------------------------------------------------------------
run_cognition_pipeline inputs          | advisory / context only (query_fn, character_fn,
  (query_fn, character_fn, drift_fn,    |   drift_check_fn, lane_provider) — retrieval/state/drift
   lane_provider)                       |   evidence; non-model-visible.
memory_context (build_memory_context)  | NON-MODEL-VISIBLE advisory context to deterministic roles;
                                       |   same-turn; sourced from retrieval + character + drift.
model-visible prompt                   | ABSENT (no LLM / model boundary in the live cognition path).
response draft / final_answer          | deterministically synthesized by reintegrate(...); no model.
role prompt / aperture context         | roles are deterministic Python classes; "aperture" builds a
                                       |   retrieval/memory recipe, NOT a model prompt.
reintegration                          | deterministic synthesis of role outputs; non-model-visible.
governance / drift gates               | governance_rejections + drift hard-block (Invariant E) are
                                       |   GOVERNANCE/identity gates, not model output-style steering
                                       |   (there is no model output to steer).
MemoryPlan / advisory query paths      | advisory retrieval shaping; non-model-visible; no write.
write / persistence                    | DISABLED on the Spine path (read-only; no ingest_fn);
                                       |   /cognition/run can writeback only under an env gate.
AssembledContext.assembled_text        | /retrieve-only; ABSENT from the live cognition path.
```

## 5. Same-turn data-flow classification

```text
A same-turn memory/context seam EXISTS in the live path:
  source:        fabric.query(...) retrieval (+ character state + drift), via build_memory_context
  same-turn?     YES (built per task inside run_cognition_pipeline)
  model-visible? NO — there is no model/LLM/prompt boundary in the live cognition path
  reaches model-visible generation? NO (none exists)
  bounded?       it is a structured memory_context for roles (aperture-budgeted), not a prompt block
  labelled/read-only/non-authoritative? it is advisory context to deterministic roles
  turn-local?    YES
  non-public?    YES (internal pipeline structure, not a public payload field)
  non-persistent? YES on the Spine path (read-only; no writeback)
  avoids output-control/review/ranking/retry/suppression/style steering? YES (no model output to steer)

=> THERE IS NO MODEL-VISIBLE MEMORY-TO-PROMPT SEAM IN THE LIVE PATH, because the live cognition
   pipeline has NO model-visible prompt / LLM generation boundary at all. The memory_context seam is
   real but NON-MODEL-VISIBLE (advisory context to deterministic role logic).

WHAT IS MISSING for a safe model-visible memory-to-prompt seam in the live path:
  - a model-visible generation boundary (none exists in cognition.pipeline today);
  - a characterization of the deterministic memory_context flow (build_memory_context → roles →
    reintegrate) as the authoritative live evidence;
  - an ARCHITECTURE DECISION about whether a model-visible LLM generation boundary should ever exist
    in the live cognition path, or whether prompt-based memory-to-generation belongs to a separate
    LLM-bearing path (e.g. the AgentRunner runtime used outside torment_service) — a larger,
    separately-gated decision.
```

## 6. Forbidden routes

```text
- code; tests; wiring; endpoint edits; provider runtime;
- AgentRunner live wiring; Terrain B runtime;
- /agent/query retrofit; /retrieve generation; schema/API/public-surface drift;
- persistence/write/logging/transcripts;
- output review/control/suppression/retry/ranking/style steering;
- autonomy/monitoring expansion;
- U1/audit/private-owner/selected-items paths;
- Gate D/dream/Envelope Audit runtime;
- database/substrate work.
```

## 7. Decision options

```text
- Option A: existing Spine/cognition.pipeline already has a safe model-visible memory-to-prompt seam.
- Option B: existing Spine/cognition.pipeline has memory/context shaping, but NOT a safe
            model-visible memory-to-prompt seam; require a characterization/design frame before any
            implementation.
- Option C: no relevant memory/context seam exists in the live Spine/cognition path; require an
            architecture/design frame.
- Option D: HOLD because live-path memory-to-prompt would require forbidden output-control / autonomy
            / public-surface drift.
- Option E: source-gap — more source survey required.
(Select at most one. Do not force selection.)
```

Verdict:

```text
=> SELECT Option B.
   - A is FALSE: there is no model-visible prompt / LLM boundary in the live cognition path, so there
     is no model-visible memory-to-prompt seam to call safe.
   - C is too strong: a same-turn memory/context seam DOES exist (memory_context from retrieval +
     character + drift, feeding deterministic roles).
   - D is not yet the finding: nothing here proves a live-path memory-to-prompt MUST require forbidden
     drift — it would require introducing a model-visible generation boundary, which is an
     architecture decision, not an inherently-forbidden one.
   - E is not needed: the survey is decisive on the key fact (the live cognition pipeline is
     deterministic / non-model-visible).
   The live path HAS memory/context shaping (non-model-visible, advisory to deterministic roles) but
   NO safe model-visible memory-to-prompt seam. A later CHARACTERIZATION/DESIGN frame is required
   before any implementation may be proposed.
```

## 8. Proof obligations before any later implementation (named only)

```text
- characterization tests for the ACTUAL live pipeline flow (route → build_memory_context → roles →
  reintegrate), and for the absence of a model boundary;
- AST/source guards for NO AgentRunner / Terrain B revival;
- guards for /retrieve read-only;
- guards for no endpoint/API/public-surface drift;
- guards for memory bounded / read-only / non-authoritative / turn-local / non-public / non-persistent;
- guards for no output-control / review / suppression / retry / ranking / style steering;
- guards for no write / persistence / logging / transcripts;
- guards for no autonomy / monitoring expansion.
```

## 9. Required no-go list (this step)

```text
No code, tests, wiring, endpoint edits, provider runtime, AgentRunner live wiring, Terrain B runtime,
/agent/query retrofit, /retrieve generation, schema/API/public-surface drift, persistence/write/
logging/transcripts, output review/control/suppression/retry/ranking/style steering, autonomy/
monitoring expansion, U1/audit/private-owner/selected-items paths, Gate D/dream/Envelope Audit
runtime, or database/substrate work.
```

## 10. Must remain HOLD

```text
- Terrain B;
- AgentRunner live wiring;
- implementation;
- the code / tests slice;
- endpoint behavior;
- public surface;
- provider runtime;
- write / persistence paths;
- all audit / private-owner / Gate D / database lanes.
```

## 11. Final verdict

**Option B — the live Spine / `cognition.pipeline` path has same-turn memory/context shaping
(`memory_context` from `fabric.query` retrieval + character + drift, consumed by deterministic
roles + reintegration), but it has NO safe model-visible memory-to-prompt seam, because the live
cognition path has NO model-visible prompt / LLM generation boundary at all (it is deterministic).**
No production code is authorized. No tests are authorized. No wiring is authorized. Terrain B and
AgentRunner live wiring remain HOLD. The recommended next move — **not code** — is a later,
separately-authorized **characterization frame** (characterize the deterministic memory_context
flow and the absence of a model boundary, with source/AST guards) and/or a **design/architecture
frame** (decide whether a model-visible generation boundary should ever exist in the live cognition
path, or whether prompt-based memory-to-generation belongs to a separate LLM-bearing path). If no
safe shape emerges, HOLD.

## 12. Anti-drift footer

TORMENT — MEMORY-TO-PROMPT-FOR-GENERATION SPINE / COGNITION PIPELINE ARCHITECTURE EVIDENCE FRAME /
DOCS-ONLY / NON-AUTHORIZING / SOURCE-FIRST / TERRAIN B HOLD / AGENTRUNNER LIVE WIRING HOLD.
Source-grounded at `4f3eecc`: the live production cognition path is the Spine /
`run_cognition_pipeline` (route → build_memory_context → deterministic roles → reintegrate → result
dict); a grep across the cognition package finds NO LLM / model / prompt boundary, so the live path
is DETERMINISTIC and has NO model-visible prompt. Memory enters as `memory_context` (from
`fabric.query` retrieval + character + drift), consumed by deterministic roles — a real same-turn
context seam that is NON-MODEL-VISIBLE; `AssembledContext.assembled_text` is /retrieve-only and
absent from the live path; MemoryPlan is advisory; the Spine path is read-only (no writeback);
`mcp_server` is a memory surface; AgentRunner / orchestrator / PrivateGenerationOwner / selected-items
bridge stay excluded. **Verdict: Option B — memory/context shaping exists but NO safe model-visible
memory-to-prompt seam; a later characterization/design frame is required before any implementation.**
It authorizes no code, no tests, no wiring, no endpoint/API/schema/public-surface change, no provider
runtime, no AgentRunner live wiring, and no Terrain B runtime; the next move is a characterization or
design frame, not code, under separate Hilmir + Codex authorization. Memory remains guidance, not
authority; audit observes authority and does not become authority; nothing rewrites identity / canon
/ seed / soul.
