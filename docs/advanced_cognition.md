# Advanced Cognition — Thinking, Stance, and Optionality

TORMENT v2.2

---

## What This Is

Advanced cognition is an optional layer that sits between raw input and response generation. It gives characters the ability to *think before acting* — framing tasks, planning memory retrieval, choosing actions, reviewing responses, and deciding whether to respond at all.

This is NOT the Agent Spine (which is the governed execution gateway). It is NOT the Fabric (which is the memory substrate). It is a lightweight cognitive loop that advises but never overrides.

---

## The Three Layers

```
Input / Event
    |
    v
Spine              — governed execution gateway, trust enforcement, write authority
    |
    v
Thinking Layer     — advisory cognition (framing, planning, action, review)
    |
    v
Fabric             — memory, retrieval, state, persistence
```

The thinking layer is a **sidecar** to Spine. It observes, frames, and advises — but Spine makes the authoritative decisions about what gets executed and what gets written.

---

## Thinking Controller (`thinking_controller.py`)

The thinking controller runs a single-pass pipeline on every input:

**1. Frame** (`frame_task`) — Classifies the input into a structured TaskFrame: what kind of task is this? How urgent? How ambiguous? Is it identity-sensitive? Does it need governance?

**2. Choose Mode** (`choose_mode`) — Selects a cognitive mode based on the frame:

| Mode | When | Character |
|------|------|-----------|
| engineering | operational/tool tasks | focused, precise |
| strategic | planning/analysis | broad, deliberate |
| identity | identity-adjacent input | protective, careful |
| live_social | social/conversational | fast, compact |
| auto | ambiguous input | adapts to context |

**3. Build Memory Plan** (`build_memory_plan`) — Decides what memory to retrieve and how to weight it. High-urgency tasks skip heavy retrieval; identity-sensitive tasks prioritize seed memories.

**4. Choose Action** (`choose_action`) — Selects an action type:

| Action | Meaning |
|--------|---------|
| respond | generate a response |
| ask_clarification | input is too ambiguous |
| use_tool | needs to inspect state or retrieve context first |
| governance_review | touches governed/sensitive operations |
| propose_share | memory sharing proposal |
| create_archive_note | archive-oriented operation |
| no_op | nothing to do |

**5. Draft Response** (`_draft_response`) — Generates a response draft based on mode and action.

**6. Review** (`review`) — Self-review pass. Softens identity overconfidence ("I am definitely" becomes "I may be"). Trims live-social responses that are too long.

**7. Stance** (`determine_stance`) — Optional stance layer (see below).

The controller outputs a `ThinkingResult` containing the full chain: frame, mode, plan, action, review, stance, and debug metadata.

---

## Stance Layer (`stance_policy.py`)

The stance layer decides *whether and how* a character participates. It sits at the end of the thinking pipeline and produces one of these stances:

| Stance | Meaning |
|--------|---------|
| respond_now | normal response |
| respond_briefly | keep it short (live-social context) |
| ask_clarification | input is too ambiguous to act on |
| defer_to_identity | identity-sensitive, needs governed review |
| silent_observe | stay silent, observe only |

**How it works:** the stance policy evaluates a series of rules in priority order. Each rule checks conditions from the TaskFrame, CognitiveModeDecision, MemoryPlan, ActionDecision, and ReviewResult. The first rule that fires determines the stance.

**Key rules include:** governance-sensitive input forces defer, identity-sensitive blocked input forces defer, high ambiguity forces clarification, ultra-short live-social turns force silence, low-urgency live-social forces brevity.

---

## Three Operating Levels

This is one of the most important ideas in the system. Characters can operate at three levels, and **stepping up is always optional**:

### Level 1 — No Stance (default)

`TORMENT_CONTEXTUAL_ABSTENTION=0` (or unset)

The character always responds. The thinking controller runs but the stance layer is bypassed. This is standard operation — every character starts here.

### Level 2 — Stance Without Geometry

`TORMENT_CONTEXTUAL_ABSTENTION=1`

The stance layer is active. The character can now defer, stay silent, ask for clarification, or choose brevity based on deterministic rules derived from the thinking controller's frame and mode decisions. Behavior is fully rule-based and predictable.

### Level 3 — Stance With Geometry

`TORMENT_CONTEXTUAL_ABSTENTION=1` + geometric context provided

The stance layer is active AND the kernel's geometric state nudges decision thresholds. Five signals from the kernel (coherence, stability, identity lock, ambiguity tolerance, social resonance) produce bounded modifiers that scale thresholds by at most +/- 15%. This means a character with low coherence is more cautious about ambiguous input, and a character with high social resonance is more willing to stay silent in live contexts.

The modifiers never override decisions — they shift thresholds within a narrow band. If geometry is not provided, all modifiers default to 1.0 and Level 2 behavior applies.

---

## Advisory vs Authoritative

This distinction matters:

| Component | Role | Can it write memory? | Can it block execution? |
|-----------|------|---------------------|------------------------|
| Spine | Authoritative | Yes (only write path) | Yes |
| Thinking Layer | Advisory | No | No |
| Stance Policy | Advisory | No | No (recommends, doesn't enforce) |
| Fabric | Substrate | Yes (via Spine) | No |

The thinking layer and stance policy are advisory. They produce recommendations — `ThinkingResult` and stance decisions — that the calling system can inspect, log, or act on. They do not directly write memory, block execution, or modify state.

Spine is the only authoritative write path. If the thinking layer recommends an action, Spine still decides whether to execute it based on trust, governance, and drift status.

---

## How to Enable

In the character creator, toggle:

| Toggle | What it enables |
|--------|----------------|
| Thinking-Layer Assist | `TORMENT_THINKING_ADVISORY=1` — advisory cognitive loop |
| Contextual Abstention | `TORMENT_CONTEXTUAL_ABSTENTION=1` — stance layer active |
| Spine-Governed Execution | `TORMENT_SPINE_ENABLE=1` — governed write path |
| Identity-Sensitive Cognition | `TORMENT_IDENTITY_COGNITION=1` — drift-sensitive escalation |

Geometric modulation requires no special toggle — it activates automatically when `GeometricStanceContext` is provided to the thinking controller. If the kernel provides geometric state, the stance layer uses it. If not, it doesn't.

---

## How to Inspect

**Thinking debug endpoint:** `POST /thinking/debug` — run the thinking pipeline on arbitrary input with optional geometric profiles. Returns the full ThinkingResult.

**Geometric profiles:** `GET /thinking/debug/geo_profiles` — list named profiles for testing (neutral, stable_locked, drifting_fragile, socially_open, ambiguity_tolerant).

**Stance in ThinkingResult:** every ThinkingResult includes a `stance` field showing the stance decision, reason, and any geometric modifiers that were active.

---

## Files

```
torment_service/
    thinking_controller.py   # Cognitive loop: frame → mode → plan → action → review → stance
    thinking_models.py       # Data models: TaskFrame, GeometricStanceContext, ThinkingResult
    stance_policy.py         # Stance rules + geometric modulation
```
