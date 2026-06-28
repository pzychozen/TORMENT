# TORMENT — Optional Autonomy Layer Readiness / Boundary Decision Frame v0.1

## 1. Status / non-authorization

**Docs-only / NON-AUTHORIZING / readiness + boundary decision frame / no code / no tests /
no startup wiring / no provider runtime / no live LLM generation / implementation HOLD.**

This frame answers a boundary/readiness question ON PAPER and records a paper-only verdict. It
writes **no code and no tests**, designs **no** supervisor, wires **nothing** into server
startup, makes **no endpoint / MCP / schema / API / public-surface change**, authorizes **no**
provider or model runtime, persists **nothing**, and opens **no** database/substrate work. It
chooses **no** env var name, designs **no** schema/queue/API/storage, and proposes **no**
concrete startup code. It does **not** revive `AgentRunner` as a live runtime or reopen
Terrain B. Where this frame and any parent contract, doctrine, or guard differ, **the
contract/guard wins**.

Standing posture, carried verbatim from the parent arc:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit must not become authority.
> Automatic is allowed. Autonomous is not.

Anchors. Current pushed edge: `7b673ca` (docs(project): close Spine model-boundary architecture
decision). Direct parent decision: `3e4bc2d` (Spine model-boundary architecture decision —
Option D HOLD). Evidence lock the parent rests on: `f480b69` (Spine memory-context
characterization lock, 11 source/AST tests). This frame sits **one level up** from `3e4bc2d`:
that frame asked *whether/where live LLM generation may exist*; this frame asks *whether an
optional layer may ever run unprompted at server start and, if so, what it may do* — which
**presupposes** the still-open model-boundary fork and adds the further question of unprompted
lifecycle and action.

## 2. Decision question (verbatim)

> Should TORMENT ever support an optional, default-off autonomous supervisor layer that may run
> when the server starts; and if so, what may it observe, report, suggest, decide, or write
> without crossing into hidden authority, tool-dispatch autonomy, public-surface drift,
> self-writing feedback, or identity/canon/seed mutation?

This frame does not answer "build it." It answers "is the idea admissible at all, in what
shape, and against what proof obligations" — and leaves every concrete step HOLD.

## 3. The load-bearing distinction: automatic service behavior vs autonomy

The question is easy to mis-read as "is the service allowed to do things on its own." The
existing doctrine already draws the line precisely, and the source already lives on the safe
side of it.

**Automatic** (already present, already allowed): bounded, request-scoped, deterministic
behavior that runs *because a caller asked* and *within one governed operation* — escalation,
governance checks, drift gating, role execution, reintegration. `docs/MCP_CAPABILITY_BOUNDARY.md`
states it directly: *"TORMENT allows: Bounded automatic behavior (e.g. escalation, governance
checks). TORMENT does not allow: Autonomous action, Self-directed tool usage, External
execution. Automatic is allowed. Autonomous is not."*

**Autonomy** (the subject of this frame, not present): a layer that runs **unprompted** —
specifically *at server start*, outside any single caller request — and that may, of its own
motion, observe, decide, act, or write. This is exactly what `AGENT_AUTOMATION_NEXT_STEP_AUDIT.md`
§2 sub-question (f) records as absent: *"Scheduler / daemon loop — No. No background loop, no
scheduler, no daemon."* The whole automation programme is summarized there as *"automation that
watches TORMENT, not automation that acts for TORMENT,"* and in the long-iteration plan as
*"automate observation of the agent loop before expanding the agent loop."*

A supervisor "that may run when the server starts" is therefore, by definition, an **autonomy**
construct, not an extension of existing automatic behavior. The verdict below is built on that
distinction.

## 4. Evidence baseline (source-grounded; referenced, not reopened)

All claims below are grounded in the committed tree at `7b673ca`. Nothing here is reopened or
re-decided; it is the terrain the verdict stands on.

```text
STARTUP / LIFECYCLE
- torment_service/app.py:67 constructs `FastAPI(...)` (version 2.4.3). The module declares NO
  startup lifecycle hook of any kind — no `@app.on_event("startup")`, no `lifespan=`, no
  startup callback — and NO background machinery: no BackgroundTask, no asyncio.create_task,
  no threading/Thread, no schedule/Timer, no daemon, no long-lived `while True` loop.
  => There is NO startup lifecycle owner in the live service today. A layer that "runs when
     the server starts" has no existing host; it would have to be newly created. This is a
     fact about the absence of a seam, not a suggestion to add one.

LIVE COGNITION PATH IS DETERMINISTIC (test-locked at f480b69)
- cognition/ and roles/ contain NO LLM / model / prompt boundary. roles/base.py: executors
  "Not make external calls (network, LLM, filesystem)"; roles/interpreter.py: "It does NOT
  call an LLM." cognition/reintegration.py final-answer is deterministic (role-summary join);
  "Future versions may use LLM synthesis" is a docstring note, not a call.
- The only "*Provider" on the live path is `LaneQueryProvider` (cognition/apertures.py) — a
  memory-query object, not a model/provider client.

MCP IS A MEMORY SURFACE, NOT AN ACTION SURFACE
- torment_service/mcp_server.py exposes memory operations only: torment_submit_task,
  torment_ingest, torment_query_memory, torment_query_state, torment_feedback,
  torment_reinforce, torment_tool_result_ingest. Exposure capped by
  `TORMENT_MCP_EXPOSURE_TIER` (open|guarded, default open). No tool dispatch, no exec.
- docs/MCP_CAPABILITY_BOUNDARY.md: "There is no tool dispatch system in the Spine. There is no
  action execution layer. This is intentional." Tier 3 (identity rewrite, seed modification,
  policy changes) is "Never exposed via MCP."

SPINE COGNITION IS STRUCTURALLY READ-ONLY
- torment_service/spine.py (`_full_cognition`, ratified Decision D1 2026-04-17) does NOT pass
  lookup_fn or ingest_fn to run_cognition_pipeline(), so archivist writeback is structurally
  disabled on the Spine path even when TORMENT_ARCHIVIST_WRITEBACK=1. "MCP-surface cognition
  observes but does not self-write." (drift_check_fn IS passed.)

SELF-WRITE IS GATED, DEFAULT-OFF, GUARD-FENCED
- cognition/pipeline.py:122 reads TORMENT_ARCHIVIST_WRITEBACK (default "0"); `_write_back_approved`
  no-ops without an ingest_fn; approved proposals pass a fail-closed recursion guard; writeback
  rows self-declare `source_role="archivist_writeback"`, `write_path="cognition_writeback"`.
- docs/ROADMAP_v2.4.x.md §3 keeps archivist write-back, broad autonomous tool use, and
  self-writing cognition loops "Blocked Until Provenance."

THE AGENTIC RUNTIME EXISTS BUT IS WIRED TO NOTHING LIVE
- torment_service/agent_loop.py (`AgentRunner`) holds the 8-phase outer loop, a single
  model-call boundary (`_build_llm_prompt_request` / `_LLMPromptRequest`), and the
  drift-triggered `enter_reflex` (proven zero-LLM). It is referenced NOWHERE in app.py,
  spine.py, or mcp_server.py — no production endpoint constructs or calls it.
- torment_service/fabric.py:692 declares `self.drift_reflex_callback = None` and invokes it at
  ~3413-3425 only `if ... is not None`. No production code assigns it a non-None value: it is
  a dormant seam.

TOOL CAPABILITY IS A SINGLE BOUNDED FAMILY, NOT A DISPATCHER
- torment_service/tool_registry.py declares ONE family, `code_exec`, as a signature the LLM may
  see (`llm_visible_tool_names`); it is a signature registry, not an action dispatcher.
- torment_service/tool_executors/subprocess_python.py executes `code_exec` as bounded
  subprocess Python and states it is "Not a hostile-code containment boundary." It is reachable
  only through AgentRunner — which is wired to nothing live.

POLICY / PACKS / THINKING (advisory, request-scoped)
- torment_service/action_policy.py: Mode -> legal-intents table with a fallback chain into
  GOVERNANCE_REVIEW. torment_service/behavior_packs.py: five-object behavior bundle.
  torment_service/thinking_controller.py: inner deliberation, advisory
  (TORMENT_THINKING_ADVISORY default-on since 2026-04-16); it ROUTES MemoryPlan emphasis, it
  does not think for the system.

DOCTRINE FENCES (verbatim)
- WORKING_NOTES.md: "No autonomous tool calls. No scheduling. No polling. No automation. No
  chained workflows. No internal role-triggered tool usage."
- TORMENT_ROADMAP_NOTES.md: TORMENT "is not an automation engine or autonomous tool runner";
  any future track requires the full audit -> scratch framing -> review -> revised draft ->
  explicit trio ratification cycle before implementation.
- AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN.md §1.5 wrapper invariants W2/W5/W6/W9 already encode
  the safe-observer shape: no scheduler/daemon/background loop, no mutation outside the
  agent-loop write set, workspace isolation, fail-closed abort.
```

## 5. Candidate modes evaluated (on paper)

Each mode is assessed for what it is, what the source says about it, its risk surface, and its
paper-only admissibility. No mode is selected for implementation; admissibility means "could be
framed as a future separately-gated design," never "may be built now."

### Mode 0 — HOLD / current automatic-only service
```text
- What: no autonomous layer; the service runs request-scoped automatic behavior only.
- Source: this is the live state (no startup owner, no scheduler — app.py; deterministic Spine
  — f480b69 lock; "Automatic is allowed. Autonomous is not." — MCP boundary).
- Risk: none introduced. Preserves every locked invariant.
- Admissibility: CURRENT / LIVE. This is the baseline the others are measured against.
```

### Mode 1 — default-off observe / report-only supervisor
```text
- What: a default-off layer that, if ever enabled, only reads already-exposed state and emits
  operator-visible reports; no suggestions, no writes, no actions.
- Source: closest to the ratified "watch TORMENT, don't act for it" posture and the W-series
  wrapper-invariant shape (observation isolated from TORMENT's read path). Diagnostic/telemetry
  observation is classified doctrine-safe in AGENT_AUTOMATION_NEXT_STEP_AUDIT.md §4 (category 2).
- Risk: low IF (and only if) it is genuinely read-only, default-off, has a real lifecycle owner,
  fails closed, persists nothing, and never re-enters cognition. The novel risk versus existing
  telemetry is the UNPROMPTED startup lifecycle, which does not exist today (app.py) and would
  be the load-bearing new thing to prove.
- Admissibility: admissible ONLY as a future, separately-gated design, if the §9 proof
  obligations are met. NOT admissible as built or wired by this frame.
```

### Mode 2 — default-off suggestion-only supervisor (operator-visible, no writes/actions)
```text
- What: Mode 1 plus operator-visible suggestions; still no writes, no tool/action dispatch, no
  model-output entering memory.
- Source: suggestion is "guidance," which doctrine permits ONLY where it cannot seize authority
  ("Memory may shape context. Memory may not seize authority."). A suggestion that is surfaced
  to a human and consumed by nothing else stays guidance.
- Risk: medium. The failure mode is a suggestion silently becoming an input to cognition,
  retrieval, ranking, output, or a writer — i.e. guidance crossing into authority, or audit
  crossing into control. If suggestions are ever generated by a model, that crosses the still-
  open `3e4bc2d` model-boundary fork and is out of scope here.
- Admissibility: admissible ONLY as a future, separately-gated design, if §9 is met AND the
  guidance-not-authority / observation-not-control lines are provably preserved. NOT admissible
  as built by this frame.
```

### Mode 3 — default-off proposal queue requiring explicit human approval before any write
```text
- What: Mode 2 plus a proposal queue; nothing is written or acted on until a human explicitly
  approves each item.
- Source: structurally analogous to the archivist-writeback discipline (default-off env gate,
  recursion guard fail-closed, opt-in-first, instant rollback) in
  ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md, and to the gated-next "explicit permissions,
  auditable calls, easy disable/rollback" posture of ROADMAP_v2.4.x.md §2B.
- Risk: medium-high. Even with human-in-the-loop, the queue itself is new persisted/stateful
  surface (storage, schema), an approval path is new control surface, and an approved write is
  a real cognition->memory or external effect. None of that storage/schema/queue is designed
  here, by rule. The model-boundary fork still gates any model-generated proposal.
- Admissibility: admissible ONLY as a future, separately-gated design, downstream of Modes 1-2,
  if §9 is met and a separate storage/governance gate is opened. NOT admissible as built here.
```

### Mode 4 — bounded self-write or tool/action autonomy
```text
- What: a layer permitted to perform bounded self-writes or tool/action dispatch without
  per-item human approval.
- Source: this is exactly what ROADMAP_v2.4.x.md §3 ("Blocked Until Provenance"),
  TORMENT_ROADMAP_NOTES.md ("not an autonomous tool runner ... still blocked"), and
  WORKING_NOTES.md ("No autonomous tool calls ... ever, in this phase") hold blocked.
- Risk: high. Self-writing feedback and tool-dispatch autonomy are the precise crossings the
  whole pre-autonomy spine (Track A / Cluster 2 / Track B / Cluster 5) was built to prevent.
- Admissibility: PARKED / REJECTED unless separately gated through the full ratification cycle.
  Not admissible by this frame in any form.
```

### Mode 5 — unrestricted autonomous tool dispatch
```text
- What: a layer that dispatches tools/actions freely, no governance, no approval.
- Source: directly contradicts the capability boundary ("There is no action execution layer.
  This is intentional.") and every doctrine fence above.
- Risk: maximal; eliminates the epistemology/capability separation the architecture is built on.
- Admissibility: FORBIDDEN. Not admissible now or under any later gate contemplated here.
```

## 6. Decision criteria

```text
A candidate mode may be called "admissible as a future separately-gated design" only if it can,
in a later proposal, preserve ALL of:
- memory remains guidance, not authority; audit observes authority, does not become authority;
- automatic (request-scoped) vs autonomous (unprompted) stays cleanly separated;
- default-off, with an explicit operator gate; source-proven no-default behavior;
- a real, named startup lifecycle owner (none exists today — app.py);
- a bounded, enumerated observation surface (reads only already-exposed state);
- an exact write/no-write contract (Modes 1-2: no writes; Mode 3: writes only post human
  approval);
- fail-closed behavior on error/uncertainty; workspace isolation; no cross-workspace bleed;
- no hidden scheduler / no hidden tool dispatch / no background chained workflow;
- no public-surface (endpoint/MCP/schema/API) drift;
- no model-output-to-memory feedback; no transcript/log persistence beyond a separately-gated,
  explicit observability decision;
- no identity / canon / seed mutation path, ever;
- it leaves implementation, tests, and live wiring HOLD until a separate gate.
```

## 7. Mode-by-mode readiness verdict (paper-only)

```text
Mode 0  HOLD / automatic-only ............ CURRENT / LIVE. Remains the live state.
Mode 1  observe/report-only .............. ADMISSIBLE ONLY as a future separately-gated design,
                                           if §9 proof obligations are met. Not built/wired here.
Mode 2  suggestion-only .................. ADMISSIBLE ONLY as a future separately-gated design,
                                           downstream of Mode 1, if §9 met and guidance-not-
                                           authority is provable. Not built/wired here.
Mode 3  approval-gated proposal queue ..... ADMISSIBLE ONLY as a future separately-gated design,
                                           downstream of Modes 1-2, if §9 met and a separate
                                           storage/governance gate is opened. Not built/wired here.
Mode 4  bounded self-write / tool autonomy  PARKED / REJECTED unless separately gated through the
                                           full audit->draft->review->ratify cycle.
Mode 5  unrestricted tool dispatch ........ FORBIDDEN.
```

The mechanism for Modes 1-3 is, in places, **more ready than the decision is settled** — the
agentic runtime, the dormant reflex seam, the advisory/observer patterns, and the
default-off/fail-closed/rollback disciplines all already exist and are unusually well fenced.
That readiness is by design and is **not** a reason to proceed. Whether an unprompted layer
*should* exist at all — and whether it may ever generate, decide, or act — is a values/product
fork that belongs to the operator and is not derivable from source.

## 8. Not authorized by this frame

```text
This frame authorizes NONE of the following. It records boundaries and a paper verdict only:
- no autonomous supervisor layer of any mode;
- no startup / lifecycle wiring; no daemon, scheduler, poller, watcher, or background loop;
- no env var, flag, config key (no name is chosen);
- no schema, queue, store, table, API, or endpoint;
- no MCP surface change or exposure-tier change;
- no provider/model runtime; no live LLM generation; no model boundary;
- no AgentRunner live wiring; no Terrain B revival; no use of the dormant drift_reflex_callback;
- no tool/action dispatch (no second tool family; no code_exec exposure);
- no memory write, archivist-writeback flip, or self-writing feedback;
- no transcript/log persistence;
- no identity / canon / seed / soul mutation;
- no database / substrate work; no dream / Gate D / private-cognition runtime;
- no output-control / review / suppression / retry / ranking / style steering.
```

## 9. Future proof obligations (before any later implementation of Modes 1-3)

```text
A later, separately-authorized proposal for any admissible mode would have to specify and prove,
with tests and AST/source guards, ALL of:
- an explicit env/config gate, default-off, with source-proven no-default behavior;
- a named startup lifecycle owner (the seam that does not exist today), and proof it does
  nothing unless the gate is on;
- a bounded, enumerated observation surface (reads only already-exposed state);
- an exact write/no-write contract per mode (no writes for 1-2; post-approval-only for 3);
- audited fail-closed behavior on error, uncertainty, or partial state;
- workspace isolation with a cross-workspace no-bleed proof;
- no hidden scheduler and no hidden tool dispatch (static guards);
- no public-surface drift (endpoint/MCP/schema/API guards);
- no model-output-to-memory feedback (and, if any generation is involved, prior resolution of
  the `3e4bc2d` model-boundary fork);
- a transcript/logging prohibition OR a separate, explicit, gated observability decision;
- AST/source guards for every forbidden crossing above, including AgentRunner/Terrain B
  exclusion and identity/canon/seed immutability;
- the full audit -> scratch framing -> review -> revised draft -> explicit trio ratification
  cycle (TORMENT_ROADMAP_NOTES.md) before any implementation planning.
```

## 10. Must remain HOLD

```text
- implementation; tests; server startup wiring; provider/model runtime;
- autonomous tool dispatch; MCP expansion; memory writes;
- persistence / logging / transcripts; AgentRunner / Terrain B;
- database / substrate; dream / private cognition / Gate D;
- all identity / canon / seed mutation paths.
```

## 11. Forbidden routes (this step)

```text
- code; tests; startup wiring; provider runtime; live LLM generation;
- MCP / API / schema / public-surface drift; unrestricted tool dispatch;
- hidden writes; transcript / log persistence; model-output-to-memory feedback;
- identity / canon / seed rewrite; AgentRunner / Terrain B revival;
- database / substrate work; dream / Gate D / private-cognition runtime;
- output-control / review / suppression / retry / ranking / style steering.
```

## 12. Final verdict

**TORMENT may, in principle, support an optional, default-off autonomy layer ONLY at the
readiness/boundary level recorded here — and nothing in this frame builds, wires, or authorizes
one.** Concretely:

- **Mode 0 (automatic-only) remains current and live.** It is the architecturally honest
  baseline: no startup owner, no scheduler, deterministic Spine, "Automatic is allowed.
  Autonomous is not."
- **Modes 1, 2, and 3 are admissible only as future, separately-gated designs**, in that order
  of increasing burden, each contingent on meeting the §9 proof obligations and preserving the
  guidance-not-authority and observation-not-control lines. None is selected, designed, or
  wired here.
- **Mode 4 (bounded self-write / tool autonomy) is parked/rejected** unless separately gated
  through the full ratification cycle.
- **Mode 5 (unrestricted tool dispatch) is forbidden.**

The deciding consideration is not a capability gap. The mechanism for Modes 1-3 is largely
already built and well fenced; what is unsettled is the **values/product question** of whether
an unprompted layer should exist at all, and — if it ever generates or acts — the still-open
`3e4bc2d` model-boundary fork beneath it. Those are the operator's forks. This frame's role is
to keep the fences visible and to mark exactly where any concrete step would cross the
guidance-not-authority / observation-not-control / no-identity-mutation lines.

**Implementation is NOT authorized. Tests are NOT authorized. Startup wiring is NOT authorized.
A separate Codex/operator gate — and the full ratification cycle — is required before any next
step. Current source remains unchanged.**

## 13. Recommended next

```text
Per the verdict: the next move is an OPERATOR/PRODUCT decision (does TORMENT want any unprompted
layer at all, and at which mode ceiling — observe-only, suggest, or approval-gated), made
jointly with the still-open 3e4bc2d model-boundary fork it presupposes — OR continued HOLD at
Mode 0. NOT code. Mode 0 stays live; the agentic runtime and reflex seam stay dormant and
unwired; the Spine stays deterministic and test-locked.
```

## 14. Anti-drift footer

TORMENT — OPTIONAL AUTONOMY LAYER READINESS / BOUNDARY DECISION FRAME / DOCS-ONLY /
NON-AUTHORIZING / READINESS + BOUNDARY DECISION / IMPLEMENTATION HOLD. Sits one level up from
the `3e4bc2d` model-boundary HOLD (evidence-locked at `f480b69`) on current edge `7b673ca`. It
grounds, in committed source, that the live service has NO startup lifecycle owner and NO
scheduler/daemon (app.py), that the live Spine/cognition path is deterministic with no LLM/model
boundary (cognition/, roles/), that MCP is a memory surface with no action/tool dispatch
(mcp_server.py, MCP_CAPABILITY_BOUNDARY.md), that Spine cognition is structurally read-only
(spine.py D1) and self-write is default-off + guard-fenced (cognition/pipeline.py,
TORMENT_ARCHIVIST_WRITEBACK=0), and that the agentic `AgentRunner` + `enter_reflex` +
dormant `drift_reflex_callback` exist but are wired to no production endpoint. It evaluates Modes
0-5 and records: **Mode 0 current/live; Modes 1-3 admissible only as future separately-gated
designs if the proof obligations are met; Mode 4 parked/rejected unless separately gated; Mode 5
forbidden.** It authorizes no code, no tests, no startup wiring, no provider/model runtime, no
live LLM generation, no MCP/API/schema/public-surface change, no tool dispatch, no hidden
writes, no persistence/transcripts, no model-output-to-memory feedback, no AgentRunner/Terrain B
revival, no database/substrate work, and no identity/canon/seed mutation; the next move is an
operator/product decision under separate Hilmir + Codex authorization, not code. Memory remains
guidance, not authority; audit observes authority and does not become authority; automatic is
allowed, autonomous is not; nothing rewrites identity / canon / seed / soul.
