# TORMENT Agent Doctrine v0.1

**Status: RATIFIED 2026-04-17.** Committed to `main` (doctrine commit `6fc167f`, merged via PR #40 as `8ce3241`, tagged `v2.4.5`). Ratification sign-off by GPT (2026-04-17) and Claude (contradiction check pass: 0 hard, 2 soft migrations logged for v0.1 implementation, 1 clarification applied as CC-1).

**Date:** 2026-04-17
**Authors:** GPT (R1–R6 positions, two rounds of revision pushback), Claude (audit, consistency check, drafting)
**Scope:** Doctrine only. Named agents, implementation plans, and eval design come AFTER this is ratified.

---

## Why this doctrine exists first

TORMENT already has a memory substrate, a kernel that moves, drift and gravity logic, convergence logic, and motif/stance/coherence/phase signals. What it does not yet have is an **agent loop that promotes those signals from memory behavior into agent behavior**. Most agent frameworks start from the opposite end — prompts and tools first, then bolt weak memory on top — and the result is scaffolding around an LLM that the framework does not understand from the inside.

Writing this doctrine before any agent code is a deliberate inversion of that order. The goal is that by the time a named agent exists, the architecture already knows what an agent is *supposed to be* in TORMENT terms, and what it is forbidden from becoming.

---

## The real shape of v0.1

> **TORMENT already has cognition primitives. The novelty in v0.1 does not come from inventing new reasoning blocks. It comes from inventing the correct runtime contract around them.**

> **The deeper framing: TORMENT is not "better autonomous agents." It is state-governed cognition where the LLM is only one participant in a larger loop.**

v0.1 is not a new brain. It is an **outer runtime loop wrapped around an existing inner deliberation scaffold**, plus the policy/action/assimilation contracts that make the math load-bearing.

**Inner deliberation loop (already exists in code):**
`frame_task → choose_mode → build_memory_plan → choose_action → review`
Implemented in `thinking_controller.think()`. Single-shot. Component-level.

**Outer agent runtime loop (to be built in v0.1):**
`observe → deliberate → policy gate → execute → assimilate → stabilize`
This is the agent-level loop. Deliberate calls the inner loop. The outer loop adds policy gating, execution, assimilation, and stabilization — none of which are currently wired end-to-end at the runtime-contract level.

### Non-LLM authority of the outer loop

> **The outer loop may execute internal reflexes, policy gating, assimilation outcomes, and stabilization steps without any LLM call.**

This is doctrine, not implementation detail. The novel part of TORMENT is that some meaningful behavior is *not* prompted, *not* narrated, *not* reasoned out by the model — it is stateful system behavior triggered by kernel state, policy, or explicit reflex rules. Saying this out loud prevents the architecture from drifting back toward "LLM for every meaningful move."

### Load-bearing criterion for the math claim

> **Coherence, drift, and gravity are considered agent-steering signals only if they can alter or veto outward action. If they merely annotate retrieved context, the math is decorative.**

This sentence is the single load-bearing test for whether "TORMENT math moves the system" is true at the agent layer. Every downstream decision in this doctrine answers to it.

---

## Preamble principle: No fake autonomy

**The agent must never narrate its own scaffolding.**

This is not a style rule. It is a structural commitment. An agent in TORMENT should not:

- say "I'll search memory" or "let me recall..."
- narrate a tool chain ("first I'll check X, then Y, then Z")
- expose 9-step chain-of-thought theater
- announce "I'll use my memory function" or name any internal capability
- present itself as a driver sitting on top of a tool menu

Instead, the visible behavior should feel like **continuity** — a participant inside an already-shaped world-state that chooses a move from within that state. TORMENT shapes the state and the action-possibility space underneath; the LLM synthesizes the visible output *inside* that shape.

This principle governs every ratification below. If any ratification tempts a design that would require the agent to narrate its own machinery to work, the ratification wins and the design is wrong.

---

## Part 1 — Capability audit

Honest bucket placement against the codebase at this revision.

**Buckets:**
- **CE** — **component exists** (dataclass, function, or enum is present and works in its own right)
- **LG** — exists but needs **loop glue** (component present, no runtime contract wiring it end-to-end)
- **PC** — **partial contract** (incomplete feature, not ready to rely on)
- **AB** — **absent** (would be novel work)

### Audit table

| # | Domain | Bucket | Where it lives / what's missing |
|---|--------|--------|-------------------------------|
| 1 | Memory retrieval and aperture shaping | **CE** | `MemoryPlan` dataclass, `thinking_controller.build_memory_plan`, `retrieval_assembler.py`. Single-shot only. |
| 2 | Continuity / drift / gravity | **CE** | `character.measure_drift`, `gravity_correction`, seed basin. Called on ingest today, not during action selection. |
| 3 | Controller mode selection | **CE** | `thinking_controller.choose_mode`, 7 `CognitiveMode` values, `frame_task`. Single-shot. |
| 4 | Intent selection | **LG** | `ActionType` enum with 9 values, `choose_action` method (5 if-branches). No Mode→legal-intents table. No primary/outcome split. |
| 5 | Action policy (gating) | **PC** | MCP tiers at external boundary only, `collective_policy.py` 7-gate for reingest only, `governance_sensitive` check inside `choose_action`. No general per-turn policy layer. |
| 6 | External tools (agent consuming them) | **AB** | No tool dispatch layer. Client examples don't give the LLM tool-use either. |
| 7 | MCP role (outward surface) | **CE** | `mcp_server.py`, 7 tools, tiers. Outward only; unrelated to whether our agent consumes tools. |
| 8 | Automation / triggers | **PC** | `compression.py` has geometric-vs-fallback trigger system at memory-lifecycle level. No agent-level reflex layer. |
| 9 | Multi-agent signaling | **CE** | ResonancePackets, `ConvergenceEvent`, 7-gate reingest, terminal echo rule. |
| 10 | Delegation / subagent | **AB** | No spawn surface. No `DELEGATE` ActionType. |
| 11 | Reflection / self-correction | **LG** | `spirit_reflection.py`, `spirit_return.py`, `gravity_correction`, `ReviewResult`, `thinking_controller.review`. No iterated runtime. |
| 12 | Stance / governance / refusal | **CE** | `ResponseStance` (9 values), `stance_policy.determine_stance`, governance flags, exposure tiers. §2A closed + default-on. |
| 13 | Trace / introspection / explainability | **CE** | `continuity_debug=true`, `/agent/{id}/self-state`, `symbol_trace`, `ThinkingResult.debug`. |
| 14 | Behavior-pack equivalent (Part 5) | **AB** | `profiles.py` is tuning bundles, `roles.py` is inference. Neither bundles aperture + intent grammar + stabilization + action contract + event reflex. |
| 15 | Background task / watcher equivalent | **PC** | Compression's state-transition trigger system is the correct substrate. No agent-level watcher loop. |
| 16 | Environment assumptions | **CE (Windows-first)** | `py -3`, port 8787, Claude Desktop active MCP host. Cross-host paused. |
| 17 | **Turn runner / outer-loop orchestrator** | **AB** | No runtime shell. `thinking_controller.think()` is single-shot deliberation, not an agent turn. No execution, no assimilation, no stabilization wired end-to-end. This is the primary gap v0.1 fills. |

### Audit headline

**Eight domains have the component but lack runtime-contract integration. Three need loop glue. Three are partial contract. Four are absent — including the turn runner itself.**

The substrate is ahead of the runtime layer. What we are missing is not intelligence. It is the contract that binds inner deliberation into an outer agent turn and lets the math veto or force outward action.

---

## Part 2 — The six ratifications

### R1 — Scope: single-agent-first, two-agent-ready, not N-agent-first

**Position:** Build one real agent. Architect so a second agent can be added without redesign. Not N-agent first.

**Reason:** One agent proves the doctrine without multi-agent noise. N-agent too early produces fake complexity.

**Boundary:** "Two-agent-ready" means two distinct agents exchanging structured signals via ResonancePackets / ConvergenceEvents / reingest — the current hivemind architecture. It does **not** mean "parallel branches of one brain" — that is v0.2.

### R2 — Memory contract: substrate, not tool

**Position:** The LLM does not treat memory as an open callable tool. Memory is prepared by TORMENT, shaped by `MemoryPlan`, injected as aperture, optionally accompanied by trace metadata.

**Allowed exceptions — closed set of controller-mediated expansion primitives:**
- `trace` — show provenance for an already-surfaced element
- `deepen` — expand detail on an already-surfaced element
- `conflict_check` — surface contradictions on a specific claim in aperture
- `continuity_expand` — extend thread window

Each is a bounded aperture refinement scoped to content *already visible*. The LLM cannot pass arbitrary query strings.

**Boundary:** Forbidden — `search_memory(query: str)`, `fetch_memory_by_id`, `recall`, or any open-domain retrieval surface visible to the LLM. Adding to the primitive set requires amending this doctrine.

### R3 — Runtime split: TORMENT handles cognition-state-memory; LLM handles bounded synthesis

**Position:** Controller and policy layers decide whether action is allowed, which action classes are legal, and ideally which single tool/family is available. The LLM may do bounded synthesis — formulate response, fill parameters, choose between tightly equivalent variants inside an approved family.

**Hard line (the anti-creep test):**

> **The model never receives an open tool-choice problem.**

If the controller cannot narrow to one tool family before the LLM sees it, that is a controller gap — fix the controller, don't delegate to the LLM.

**Boundary:** Forbidden — "here are 5 tools, pick one"; tool selection prompts; fallback where the LLM chooses among unresolved options.

### R4 — Tool doctrine: external tools are policy-gated and late

**Position:** External tools appear only after (1) mode chosen, (2) aperture built, (3) intent selected as `USE_TOOL`, (4) action policy approves and narrows to one tool family. Never first move, never menu-visible.

**Boundary:** Forbidden — LLM-visible tool list, tool-by-default on ambiguous input, tools bypassing Phase 5.

### R5 — MCP doctrine: external actions/adapters only, not core memory/cognition

**Position:** MCP is outbound-to-external-actions + inbound-for-external-consumers. Our own agent uses native TORMENT (in-process or HTTP at `127.0.0.1:8787`). `torment_service/mcp_server.py` is now explicitly a **secondary external interface.**

**Implication:** Cross-host MCP is no longer internally required. Resume conditions in `docs/MCP_CROSS_HOST_FRAMING_v2.4.x.md` unchanged; R5 removes the last internal-validation justification for resuming it.

**Boundary:** Forbidden — "dogfooding MCP by having our own agent call our own MCP server."

### R6 — Action loop: eight phases, no collapse

**Position:** Every agent turn runs:

1. **Observe** — input arrives (user message, file event, tool result, convergence event, reflex trigger)
2. **Frame** — `TaskFrame` computed, `choose_mode` selects mode
3. **Aperture** — `MemoryPlan` built, retrieval executed, character_context assembled; drift/gravity surfaces as aperture content
4. **Intent** — `choose_action` picks a primary runtime intent from the mode-bounded legal set
5. **Action Policy** — risk-class / governance / trust-tier / drift-regime gates; narrows to one tool family for USE_TOOL; can force stabilization path under drift
6. **Execute** — LLM synthesis OR policy-approved tool call OR no-op; `review` runs as a closing gate before Phase 7
7. **Assimilate** — ingest result with correct provenance, trigger any assimilation outcomes (see Part 3)
8. **Stabilize** — drift update, gravity correction if triggered, motif attachment, optional convergence emission, reinforce/feedback, optional checkpoint

**Do not collapse phases 5 and 6.** The seam between policy approval and execution is where risk-class filtering lives.

**Veto criterion reinforced:** Phase 5 must be able to block Phase 6 execution for drift/gravity to be load-bearing.

**Boundary:** Forbidden — "fast path" that skips phases. Every turn runs all eight, some as no-ops when appropriate.

### R6.a — Role of `review` inside Phase 6

Because `review` already exists in `thinking_controller.review` and sits at the seam between deliberation and final output, the doctrine must say what it is allowed to be.

**Position:** `review` is a **structured gate surface at the close of Phase 6** — between synthesis/execution and Phase 7 (Assimilate). It:

- **May** inspect the response draft or tool result for declared violations (governance mismatch, identity overconfidence, live-social length overflow, similar categorical checks).
- **May** revise text on those declared grounds — bounded edits only, not freeform rewrites.
- **May** veto Phase 7 advancement and escalate (governance_sensitive action mismatch → escalate to GOVERNANCE_REVIEW; drift-trip discovered post-synthesis → force Phase 8 stabilize and suppress output).
- **May not** re-enter earlier phases. No re-framing, no re-mode-choice, no second pass through deliberation. If review blocks, the turn escalates through the refusal/escalation chain below or terminates with an explicit reason.
- **May not** be freeform self-critique. Review operates on declared grounds only; adding new grounds requires amending this subsection.

---

## Part 2.5 — Refusal / escalation chain

When Phase 5 cannot find a legal intent, when drift vetoes outward action, when a tool family cannot be narrowed, or when governance forbids direct response, the agent must not silently widen legality to keep the turn moving. The fallback chain is explicit:

1. **If governance-sensitive signal is active** → route to `GOVERNANCE_REVIEW` primary intent. Output is governance-framed; no direct answer produced.
2. **Otherwise, if legal for the current mode** → `DEFER` (decline to act this turn, hold for more context) or `ASK_CLARIFICATION` (scoped question back to user).
3. **Otherwise** → `NO_OP` with an explicit system-side reason recorded in the turn trace (`reason: "no_legal_intent | drift_veto | tool_family_unresolvable"` etc.). Phase 8 (Stabilize) still runs.
4. **Never** silently widen legality. If the fallback chain exhausts without producing a legal path, `NO_OP` with reason is correct; a fifth step that relaxes constraints is not allowed.

This is the "fail closed, not open" rule. Its importance is that scaffold-creep in production agent frameworks almost always starts from someone deciding the turn must produce output and quietly adding a permissive fallback. That door is nailed shut here.

---

## Part 3 — Intents: primary runtime vs assimilation outcomes

### The criterion

> **A runtime decision is something that changes the externally visible course of the turn before or during Phase 6. An assimilation or governance outcome is a post-execution state consequence that the model never chooses.**

This one sentence is the test. Apply it to any future `ActionType` addition: if the action changes visible behavior during Phase 4–6, it's a primary runtime intent. If it's a state consequence emitted during Phase 7–8, it's an assimilation outcome. The nine current `ActionType` values split as follows:

### Primary runtime intents (agent deliberates; LLM may synthesize; mode-bounded)

- **ANSWER** — produce a response inside the aperture
- **ASK_CLARIFICATION** — scoped question back to user
- **DEFER** — decline to act this turn, hold for context
- **USE_TOOL** — request external action (policy-gated, family-narrowed)
- **NO_OP** — no visible output; Assimilate/Stabilize still run
- **GOVERNANCE_REVIEW** — route-level: governance-framed output, not ANSWER

### Assimilation / governance outcomes (controller/kernel/policy-decided; never LLM-chosen)

- **WRITE_MEMORY** — kernel decides on `write_intent`, novelty, coherence
- **PROPOSE_SHARE** — proposal bridge fires from persistent convergence patterns
- **CREATE_ARCHIVE_NOTE** — controller tags a turn for archive on content type

The code enum stays flat; the split is a doctrinal layer on top. This keeps the LLM from ever seeing "propose_share" or "write_memory" as choices — they happen underneath.

### Pre-execution legality — Mode → primary runtime intent

**Pre-execution only** — first Phase 4 decision in a turn. Post-execution legality below.

| Mode \ Intent → | ANSWER | ASK_CLARIFICATION | DEFER | USE_TOOL | NO_OP | GOVERNANCE_REVIEW |
|---|---|---|---|---|---|---|
| **FAST** | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ |
| **RETRIEVAL** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| **REFLECTIVE** | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| **TOOL** | ✗ | ✓ | ✓ | ⚠ | ✓ | ✗ |
| **GOVERNED** | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ |
| **IDENTITY_SENSITIVE** | ✓ | ✓ | ✓ | ✗ | ✓ | ⚠ |
| **LIVE_SOCIAL** | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |

**Load-bearing cells:**
- **TOOL forbids ANSWER pre-execution.** If mode is TOOL, the turn intends to use a tool; answering pre-execution skips the point.
- **GOVERNED forbids ANSWER entirely.** Governance routes through GOVERNANCE_REVIEW.
- **USE_TOOL is legal only in TOOL mode**, and even there is ⚠ (policy-gated, family-narrowed).
- **IDENTITY_SENSITIVE admits GOVERNANCE_REVIEW (⚠)** only if drift + governance signals co-occur.

### Post-execution legality (after Phase 6 completes in-turn)

After a tool executes in TOOL mode and a result returns, the legal next intents narrow to: **ANSWER** (common), **ASK_CLARIFICATION** (if result ambiguous), **DEFER** (if result shows task not fulfillable), **NO_OP** (if result self-sufficient), **GOVERNANCE_REVIEW** (if result surfaces governance-sensitive content — escalates).

TOOL mode is restrictive on the way in and opens up on the way out.

---

## Part 4 — Drift/gravity as action steerer

This is the load-bearing decision. Drift and gravity must drive action selection, not just shape aperture.

**Three regimes (doctrine):**

- **Low drift** — aperture shaping only. Retrieval weighting may favor seed-adjacent memories. No forced intent change. No action veto.
- **Moderate drift** — aperture surfaces a drift warning. Intent layer **promotes** stabilization-leaning primary intents. No hard block.
- **High drift** — Action Policy **blocks** outward actions: `USE_TOOL` denied; `PROPOSE_SHARE` / `CREATE_ARCHIVE_NOTE` outcomes suppressed. Primary intent forced to a stabilization path (controller-generated, not LLM-chosen). `character.gravity_correction` runs at Phase 8. Override only on explicit urgency/governance signal.

The veto criterion is satisfied: high regime vetoes; moderate regime alters selection; low regime shapes context only.

**Default threshold values are in Appendix A**, not in doctrine. The three-regime structure is doctrine; the numbers are a v0.1 reference operating profile, subject to calibration.

---

## Part 5 — Behavior packs: TORMENT-native alternative to "skills"

The term "skill" anchors readers to prompt-file-plus-tool-list thinking. TORMENT does not need that mental model. Call these **behavior packs** (or **behavioral identities**). Outside systems may perceive them as skill-like; internally the model is richer.

A behavior pack bundles five first-class objects under a named identity:

1. **Aperture recipe** — named `MemoryPlan` profile (lanes, weights, character_context pieces).
2. **Intent grammar** — narrowing of the Mode→intent table specific to this class of work.
3. **Stabilization program** — drift/coherence/convergence thresholds and their reflex behaviors for this class.
4. **Action contract** — policy-approved external action families allowed for this pack.
5. **Event reflex** — non-LLM trigger logic driven by motifs, drift, convergence, governance, or phase timing.

A TORMENT behavior pack is **all five bundled**.

### Composition boundary for v0.1

> **One primary behavior pack is active at a time. Optional narrow overlays may apply. Arbitrary multi-pack composition is not allowed.**

"Narrow overlay" means an overlay may:
- Extend the action contract by adding one additional approved action family.
- Tighten the intent grammar (make one more intent illegal under this pack).
- Add a reflex rule to the stabilization program.

An overlay may **not**:
- Loosen any existing restriction.
- Replace the aperture recipe.
- Widen legality in any way (the "never silently widen" rule from Part 2.5 applies here too).

This keeps packs from becoming skill spaghetti. v0.1 ships with one-primary-plus-narrow-overlays as the composition model; wider composition is reserved for v0.2.

### The novelty test for behavior packs and reflexes

> **A proposed behavior pack or event reflex is only TORMENT-native if it is grounded in at least one of: controller mode structure, aperture shaping, drift / gravity / coherence state, convergence / motifs / stance / governance, or assimilation / stabilization behavior.**

If the proposed pack is just a prompt template, a tool list, a persona text file, or a shell script wrapped in a character name — it is not TORMENT-native, even if useful. Useful non-native behaviors can still be shipped as external integrations; they just don't get the behavior-pack label or the protection of this doctrine.

This test is the gatekeeping rule that prevents standard agent-framework habits from entering through the behavior-pack door.

---

## Part 6 — Automation: internal reflex vs external scheduling

### Internal reflex automation (doctrine)

- **No LLM necessarily in the loop.** Reflexes can fire, execute policy-bounded action, assimilate without ever calling the language model.
- **Trigger sources:** drift threshold crossings, convergence events above confidence threshold, governance actions entering audit trail, phase / cycle-stage changes, motif activations.
- **Reflex shape:** kernel detects trigger → event enters outer loop at Phase 1 (Observe) → Phase 2–8 run with a reflex-specific mode forcing a specific primary intent. LLM may or may not be called at Phase 6 depending on the reflex.
- **Prior art:** `compression.py` already has this pattern for memory-lifecycle triggers (geometric prioritized over time-based fallback). Generalizing it to agent behavior is the natural path.

### Reflex priority rule

When multiple reflexes fire for the same agent in the same turn-window, the priority order is:

1. **Governance-triggered** (highest — explicit compliance authority)
2. **Safety / stabilization** (drift high regime, coherence collapse)
3. **Convergence-triggered** (cross-agent resonance)
4. **Identity** (non-safety drift, seed basin adjacency signals)
5. **Motif / phase convenience** (lowest — tuning-level signals)

Ties within a band break by most-recent-event-first. A governance reflex suspends lower-band reflexes until it resolves. This order is v0.1 default and subject to calibration — what is doctrine is that an order exists and collisions are not left undefined.

### External scheduling (out of doctrine scope)

Cron, systemd, Cowork's scheduled-tasks MCP, any external wall-clock timer — not part of TORMENT cognition doctrine. TORMENT does not implement its own time-driven scheduler. External time-based triggers fire `/agent/ingest` or a future `/agent/notify` and enter the outer loop at Phase 1 like any other observation.

Reactive-to-state is the TORMENT-native pattern. Reactive-to-wall-clock is a solved problem someone else owns.

---

## Part 7 — Open questions reserved for v0.2

- **Parallel-branches-of-one-brain architecture.** Different from v0.1's two-distinct-agents model. v0.2 decides whether parallel-branches is a refinement or replacement of ResonancePacket model.
- **Subagent / delegation.** No `DELEGATE` ActionType exists. v0.2 or forbidden direction is undecided.
- **Behavior-pack registration surface.** Part 5 proposes the five-object model; concrete API, file format, scoping, and wider composition rules deferred.
- **Action-family taxonomy.** Phase 5 requires narrowing to a tool family; the taxonomy is deferred until concrete tools are in scope.
- **Evaluation.** How this agent is better than a conventional tool-scaffolded agent; deferred but not forgotten.
- **Live/personal layer interaction.** Voice, response feel, natural memory use; inside-loop vs adjacent-to-loop split is v0.2.

### What to analyze next (v0.2 prep)

Preserved so the highest-value follow-up analyses don't get lost:
- What `choose_action` already means today and how its contract should grow.
- What `review` already constrains and how it generalizes under the Part 2 R6.a rules.
- Whether `ActionType` should be refactored to structurally encode the primary-vs-outcome split.
- Whether drift/gravity can be real action-vetoes without deadlocking an agent in perpetual self-correct.
- What an internal event-reflex layer looks like with no LLM in the loop — design and threshold calibration.

---

## Part 8 — Implementation impact preview

**Extensions:**
- `thinking_controller.py` — `choose_action` gets Mode→legal-intents enforcement; `choose_mode` reads drift from agent state; `review` gets declared-grounds enumeration per R6.a.
- `thinking_models.py` — may gain `ActionPolicyDecision` dataclass for Phase 5 output.
- `character.py` — `measure_drift` exposed to action-policy layer.

**New modules:**
- `torment_service/agent_loop.py` — iterated runner for phases 1–8.
- `torment_service/action_policy.py` — phase 5 gating, drift-regime rules, action-family narrowing, refusal/escalation chain.
- Behavior-pack registry module scaffold (v0.2 spec, skeleton in v0.1 if needed).
- Internal reflex layer (event → outer-loop entry point).

**Unchanged:**
- `mcp_server.py` — secondary external interface (R5).
- `memory_kernel.py` — kernel math intact.
- `collective_field.py`, `collective_policy.py` — hivemind unchanged by v0.1 scope.

Volume estimate, not a plan.

---

## Part 9 — Doctrinal invariants

These are the short verifiable rules the implementation must not violate. Each is a sentence the code can be audited against.

1. **Memory is never exposed as open-ended search to the LLM.** Only the closed expansion primitives (`trace`, `deepen`, `conflict_check`, `continuity_expand`) are LLM-visible memory-adjacent calls. *(Scope: the internal agent's LLM. External MCP consumers operate under the MCP server's separate surface, per R5.)*
2. **The model never receives an open tool-choice menu.** Phase 5 narrows to one tool family before the LLM sees anything tool-related.
3. **Drift in the high regime can veto outward action.** Phase 5 refuses `USE_TOOL` and suppresses outward assimilation outcomes when drift is high, unless urgency/governance override is explicit.
4. **Assimilation outcomes are not model-chosen intents.** `WRITE_MEMORY`, `PROPOSE_SHARE`, `CREATE_ARCHIVE_NOTE` are never presented to the LLM as selectable actions.
5. **Internal reflexes may run without an LLM call.** The outer loop can complete phases 1–8 for reflex-triggered turns with zero model invocations.
6. **Governance can narrow legality but never widen it.** Governance signals can remove legal intents from a mode's set; they cannot add new legal intents or bypass Phase 5 gates.
7. **TOOL mode legality differs pre- and post-execution by declared rule.** Pre-execution is restrictive (USE_TOOL ⚠, no ANSWER); post-execution opens to ANSWER/ASK_CLARIFICATION/DEFER/NO_OP/GOVERNANCE_REVIEW.
8. **Review may veto or revise on declared grounds but may not re-enter earlier phases.** No loop-back from `review`; escalate or terminate via the refusal/escalation chain.
9. **Fallback chain runs closed, not open.** Unresolvable turns become `NO_OP` with an explicit system-side reason. Silent legality widening is forbidden.

These nine are the scorecard for any future v0.1 implementation. If the code can violate any of them, the code is wrong.

---

## Part 10 — Minimum viable runtime slice (post-ratification first-step preview)

Once v0.1 is ratified, the first implementation step is not a named agent. It is a **minimum runtime slice** that proves the doctrine is real in code. Proposed slice:

- **One outer-loop runner** — the skeleton that runs phases 1–8 for one turn.
- **One drift veto path** — Phase 5 gate that blocks `USE_TOOL` when drift ≥ high threshold (Appendix A).
- **One narrow tool-policy gate** — Phase 5 narrowing for one specific tool family (candidate: `code_exec` in sandboxed form, because it's the lowest-ambiguity action family to gate).
- **One behavior-pack skeleton** — the five-object dataclass cluster plus a single reference pack (candidate: a minimal "debugging-session" pack, because its stabilization program and action contract are easiest to write concretely).
- **One internal reflex** — one non-LLM reflex wired end-to-end (candidate: drift-threshold reflex that forces `self_correct`).

The point of the slice is not to be useful. It is to prove the doctrine holds under real code. If any of the nine invariants from Part 9 gets violated implementing this slice, the doctrine needs revision before scaling up. If all nine hold, v0.1 is real and larger work can begin.

This preview is not part of the ratification checklist — the slice gets its own implementation plan after ratification. It is included here so "ratify and next step" is connected in the reader's mind.

---

## Appendix A — v0.1 reference default operating profile

**These numbers are a starting profile for v0.1, subject to calibration. They are not doctrinal constants. The three-regime structure in Part 4 is doctrine; the thresholds are tuning.**

| Signal | Low regime | Moderate regime | High regime |
|--------|------------|-----------------|-------------|
| `drift_score` | `< 0.15` | `0.15 ≤ drift_score < 0.35` | `≥ 0.35` |
| Action effect | aperture shaping only | intent promotion toward stabilization | outward action veto + forced stabilization |
| Gravity correction | no | no (advisory) | yes (Phase 8 runs `character.gravity_correction`) |

The high-regime threshold reuses the existing `TORMENT_CHARACTER_CORRECTION_THRESHOLD=0.35` on purpose — promoting the same threshold from "when to emit a correction memory" (current use) to "when to veto outward action" (v0.1 use). Same number, new semantics.

The moderate-regime boundary (0.15) is provisional. Likely to move during calibration once the outer loop is actually running and we can measure regime-firing frequencies.

---

## Ratification record

**Ratified 2026-04-17** after three revision rounds with GPT pressure-testing and one code-contradiction pass against the existing codebase (0 hard contradictions, 2 soft contradictions logged as v0.1 implementation migration items, 1 consistency clarification applied as CC-1 to invariant 1).

All twenty-one positions below were accepted without further revision:

- [x] "Real shape of v0.1" inner/outer loop framing accepted.
- [x] Non-LLM outer-loop authority sentence accepted as doctrine.
- [x] "State-governed cognition" framing accepted as deeper thesis.
- [x] Load-bearing criterion (math veto or decorative) accepted as headline test.
- [x] Capability audit buckets (CE / LG / PC / AB) accepted; row 17 (turn runner absent) accepted.
- [x] R1–R6 positions, reasons, and boundaries accepted.
- [x] R3 hard line ("no open tool-choice problem") accepted.
- [x] R6.a `review` role (structured gate, declared grounds, no loop-back) accepted.
- [x] Refusal / escalation chain (Part 2.5) accepted — fail-closed rule accepted.
- [x] Runtime-decision vs assimilation-outcome criterion accepted.
- [x] Primary-intent vs assimilation-outcome split accepted.
- [x] Pre-execution Mode→intent table accepted; post-execution note accepted.
- [x] Three drift regimes accepted as doctrine; numeric thresholds accepted as Appendix A reference profile.
- [x] Behavior packs (five-object bundle) accepted as direction.
- [x] Behavior-pack composition boundary (one primary + narrow overlays) accepted.
- [x] Novelty test for packs/reflexes accepted.
- [x] Internal-reflex vs external-scheduling split accepted.
- [x] Reflex priority rule (governance > safety > convergence > identity > motif/phase) accepted as v0.1 default.
- [x] Doctrinal invariants (Part 9, nine rules) accepted as the implementation scorecard.
- [x] Part 7 v0.2 deferrals are the right ones.
- [x] Part 10 MVP runtime slice accepted as the first post-ratification implementation step.

**Sign-off:**
- GPT (via user, 2026-04-17): "This is a sign-off from me. Revision 3 is ratifiable."
- Claude (contradiction check, 2026-04-17): "0 hard contradictions. 2 soft contradictions. 1 consistency clarification. Revision 3 is ratifiable."

**Known migration items for v0.1 implementation (logged, not blocking):**
- **SC-1** — `thinking_controller.choose_action` currently emits `PROPOSE_SHARE` and `CREATE_ARCHIVE_NOTE` as primary Phase 4 outputs. Doctrine Part 3 classifies these as assimilation outcomes. Migrate during v0.1: remove those branches, route into a Phase 7 dispatcher.
- **SC-2** — `thinking_controller.choose_action` default branch returns `ANSWER` without mode-legality enforcement. Violates invariant 9 in `TOOL` / `GOVERNED` modes. Migrate during v0.1: wrap output with mode-legality check that applies the Part 2.5 fallback chain.

**Next artifact:** `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` — ratification pending; covers SC-1, SC-2, and the five slice components (S1 outer-loop runner, S2 drift veto, S3 tool-policy gate, S4 behavior pack skeleton, S5 internal reflex). Current draft in the working outputs folder.