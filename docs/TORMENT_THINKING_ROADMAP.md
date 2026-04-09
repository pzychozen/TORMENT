# TORMENT Thinking Layer Roadmap

**Status:** Phase 1 (Cognitive Core) is **implemented** — `thinking_controller.py`, `thinking_models.py`, and `stance_policy.py` are live. Phase 2 (Embodied / Live Agent) remains future work.

## Purpose

Strengthen TORMENT’s internal cognition so it can:

- reason more deliberately
- choose actions more reliably
- use memory more intelligently
- preserve identity and character continuity
- support future live embodiments such as X Spaces, MCP-connected characters, and autonomous tool use

This roadmap assumes TORMENT already has a partial Spine / MCP direction and that Fabric, memory, governance, archive, collective, compression, and character continuity already exist.

The next step is not just “more endpoints,” but a stronger internal thinking and control architecture.

---

## Architectural Position

The clean split should be:

- **Spine** = governed execution gateway
- **Thinking Layer** = cognition / planning / memory gating / self-review
- **Fabric** = state, memory, retrieval, execution substrate

High-level flow:

**Input / event**  
→ Spine request envelope  
→ Thinking Layer  
→ Memory plan  
→ Deliberation  
→ Action recommendation  
→ Spine governance / trust / locking  
→ Fabric execution  
→ Writeback / observability

---

# Phase 1 — Cognitive Core

## Objective

Create a stable internal cognition loop that can:

- interpret inputs
- choose a mode of thought
- retrieve the right memory
- deliberate at the right depth
- decide whether to act, ask, defer, or refuse
- preserve identity while doing so

This phase is about internal intelligence quality, not voice or public embodiment.

---

## Phase 1 System Components

### 1. Input Framing Layer

Transforms raw task/input into a structured internal packet.

#### Responsibilities

- classify task type
- detect urgency
- estimate ambiguity
- infer whether this is:
  - informational
  - relational
  - operational
  - reflective
  - creative
  - risky / needs governance
- detect whether memory retrieval is needed

#### Suggested internal structure

`TaskFrame`

- `workspace_id`
- `agent_id`
- `raw_input`
- `normalized_input`
- `source_type`
- `domain_hints`
- `urgency`
- `ambiguity_score`
- `confidence_need`
- `action_need`
- `memory_need`
- `tool_need`
- `tone_hints`

---

### 2. Cognitive Mode Selector

Chooses how deeply and in what style the system should think.

#### Candidate modes

- `fast`
- `retrieval`
- `reflective`
- `tool`
- `governed`
- `identity_sensitive`
- `live_social`

#### Output

`CognitiveModeDecision`

- `chosen_mode`
- `reason`
- `allowed_depth`
- `requires_self_review`
- `may_escalate`

---

### 3. Memory Gating Layer

Determines what kinds of memory to retrieve and how much weight they should have.

#### Memory lanes

- core / identity
- relational
- situational
- archive
- deep memory
- collective / echo
- checkpoint / long-state context
- character state / drift / seed overlays

#### Responsibilities

- choose memory lanes by task type
- set retrieval budget
- decide whether archive is support-only
- prevent archive from outranking identity
- avoid overloading context with irrelevant memory
- preserve scope boundaries

#### Output

`MemoryPlan`

- `retrieve_core`
- `retrieve_relational`
- `retrieve_archive`
- `retrieve_deep`
- `retrieve_collective`
- `top_k_by_lane`
- `weight_by_lane`
- `max_token_budget`
- `safety_constraints`

---

### 4. Deliberation Engine

The controlled “thinking” layer.

#### Responsibilities

- choose between quick response vs staged reasoning
- break tasks into subgoals
- run internal checks
- branch when uncertainty is high
- merge candidate responses
- avoid runaway loops

#### Recommended structure

Use a bounded staged loop, not open-ended recursion.

Example stages:

1. understand task
2. retrieve memory/tools
3. generate candidate actions or answers
4. critique candidates
5. select best action
6. optionally review for identity/governance alignment

---

### 5. Action Policy Layer

Determines what the system should actually do.

#### Candidate actions

- answer directly
- ask clarification
- defer
- use tool
- write memory
- propose share
- trigger governance path
- create archive note
- do nothing

This is the bridge from “thought” to actual behavior.

---

### 6. Self-Review Layer

A light post-check before output or action.

#### Responsibilities

- check contradiction
- check low-confidence hallucination risk
- check identity drift risk
- check scope / policy mismatch
- check whether the answer is overconfident
- optionally shorten or soften output

#### Output

`ReviewResult`

- `approved`
- `revised`
- `escalate`
- `ask_user`
- `blocked`

---

### 7. State Writeback Layer

Persists what matters after the turn.

#### Responsibilities

- write relevant memory
- update role / affect / continuity state
- track drift
- update live session context
- optionally log decision metadata for observability

This should be selective, not “store everything.”

---

## Phase 1 Dependencies

- existing Fabric retrieval and memory writes
- character store / role store / identity store
- archive memory
- deep memory store
- governance and collective policy
- Spine request / dispatch layer
- observability / incident logging

---

## Phase 1 Risks

- overcomplicating the control loop
- too much latency from “thinking”
- retrieval overload / context bloat
- unstable mode switching
- writing too much memory
- identity drift caused by over-weighting recent or collective context
- building a loop that looks smart but is brittle

---

## Phase 1 MVP Order

### MVP 1 — Task framing + mode selection

Prototype first:

- `TaskFrame`
- `CognitiveModeDecision`
- a simple mode policy

Goal:

TORMENT can decide whether a task is:

- fast
- reflective
- retrieval-heavy
- tool/governance-sensitive

---

### MVP 2 — Memory gating

Prototype:

- lane-selection policy for:
  - identity
  - relational
  - archive
  - deep
- weighting rules

Goal:

TORMENT retrieves better rather than just more.

---

### MVP 3 — bounded deliberation loop

Prototype:

1. frame
2. retrieve
3. answer + review

Goal:

Prove that structured thinking improves quality without hurting stability.

---

### MVP 4 — self-review

Prototype:

- contradiction / confidence / drift check
- low-cost post-check before action

Goal:

Reduce obvious bad decisions.

---

## What to Prototype First in Phase 1

### `thinking_controller.py`

Minimal version:

- input: `workspace_id`, `agent_id`, raw task/input
- output:
  - chosen mode
  - memory plan
  - action decision
  - final response draft

Back it with:

- simple heuristics first
- then improve with model-assisted routing later

Why first:

- touches the whole future architecture
- can plug into Spine
- gives immediate observability
- low blast radius

---

# Phase 2 — Embodied / Live Agent Layer

## Objective

Once the cognitive core is stable, connect it to live environments such as:

- X Spaces
- live audio sessions
- MCP-connected interactive characters
- autonomous event participation

This phase is about presence, not just internal reasoning.

---

## Phase 2 System Components

### 1. Session Orchestrator

Maintains live-session state.

#### Responsibilities

- participant tracking
- turn history
- topic stack
- response cooldown
- whether the character is currently listening, thinking, or speaking
- local working memory for the session

#### Output

`LiveSessionState`

- `session_id`
- `current_topic`
- `participants`
- `pending_turns`
- `recent_speaker`
- `agent_response_state`
- `working_memory`

---

### 2. Audio / Transcript Ingress

Turns live session data into usable text events.

#### Inputs

- transcript stream
- or captured live audio

#### Responsibilities

- VAD / segmentation
- STT
- speaker turn detection
- optional diarization
- confidence and timestamps

#### Output

`SessionTurn`

- `speaker_id`
- `text`
- `ts_start`
- `ts_end`
- `directed_to_agent`
- `confidence`
- `tone_hints`

---

### 3. Live Response Decision Layer

Decides whether the character should speak.

#### Responsibilities

- determine if the turn is directed at the character
- decide wait vs answer
- choose response length
- avoid interrupting humans constantly
- respect cooldowns

---

### 4. Voice Synthesis Layer

Converts response text into speech.

#### Responsibilities

- TTS
- pacing
- optional style / emotion shaping
- stream or chunked output

---

### 5. Audio Routing Layer

Routes synthesized audio into the live environment.

#### For X-style integration

- virtual microphone
- device routing
- output buffering
- latency management

---

### 6. Session Memory Bridge

Writes meaningful session outcomes back into TORMENT.

#### Responsibilities

- store long-term useful moments
- archive long transcripts if needed
- preserve social memory
- update warmup / identity continuity / relationship traces

---

## Phase 2 Dependencies

- stable Phase 1 thinking controller
- transcript ingestion
- TTS system
- audio routing / virtual mic
- session state storage
- live moderation / response policy
- optional X integration layer

---

## Phase 2 Risks

- latency too high for conversation
- character talks too often or too little
- voice feels detached from cognition
- transcript errors poison reasoning
- social awkwardness from poor turn-taking
- memory pollution from raw live chatter
- platform integration fragility

---

## Phase 2 MVP Order

### MVP 1 — transcript-only simulation

Prototype:

- feed transcript turns into the thinking controller
- output text responses only

Goal:

Validate social decision logic without audio complexity.

---

### MVP 2 — local voice embodiment

Prototype:

- transcript in
- TTS out
- local loopback room / virtual mic

Goal:

Prove the character can exist in a live conversational loop.

---

### MVP 3 — session memory writeback

Prototype:

- persist meaningful session events
- track who was talked to, topic arcs, and follow-up relevance

Goal:

Make the character feel continuous across sessions.

---

### MVP 4 — X Space integration

Prototype:

- stream transcript/audio from X
- route character voice back into the Space
- test basic moderation and timing

Goal:

Public embodiment of TORMENT cognition.

---

## What to Prototype First in Phase 2

### `live_session_simulator.py`

A local loop that:

- accepts transcript turns
- runs them through the Phase 1 thinking controller
- decides if/when the character should answer
- outputs text first, then optional TTS

Why first:

- much faster iteration
- easier debugging
- better than going directly into live X complexity

---

# Suggested Initial File Layout

## Phase 1

- `torment_service/thinking_models.py`
- `torment_service/thinking_controller.py`
- `torment_service/memory_gating.py`
- `torment_service/review_policy.py`

## Phase 2

- `torment_service/live_session_models.py`
- `torment_service/live_session_simulator.py`
- `torment_service/live_response_policy.py`
- `torment_service/audio_bridge.py`

---

# Immediate Next Step

Build **Phase 1 MVP 1** first:

- define `TaskFrame`
- define `CognitiveModeDecision`
- implement a simple routing policy
- run it on:
  - ingest-like tasks
  - query-like tasks
  - governance-sensitive tasks
  - archive/retrieval tasks

This will tell us quickly whether the thinking layer has the right skeleton.

---

# Open Design Questions

These should be answered before deeper implementation:

1. Which modes matter most?
2. When should TORMENT choose slow thought?
3. What must remain protected from autonomy?
4. What counts as a good independent action?
5. Should the thinking layer be more:
   - geometric / state-machine flavored
   - modern agent-policy flavored
   - or explicitly hybrid?

Current recommendation: **hybrid**
- geometric/state logic for internal continuity
- practical policy logic for tool use and action control