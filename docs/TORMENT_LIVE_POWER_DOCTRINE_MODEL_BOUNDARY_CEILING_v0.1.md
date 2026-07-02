# TORMENT — Live-Power Doctrine / Model-Boundary Ceiling v0.1

**Status:** DOCS-ONLY doctrine artifact. **Decision-framing only — non-authorizing, non-implementing.**
It defines *what live power TORMENT may contain, express, transport, or influence* **before** any future
runtime, provider, MCP/action, embodiment, Dream, or substrate implementation is opened. It **opens no
implementation lane, selects no surface, and authorizes nothing.** `PROJECT_ORIENTATION_MAP.md` §0 remains
the active work-order; §0 wins unless Hilmir explicitly overrides. Older docs are evidence.

---

## 1. Purpose

TORMENT is, for this phase, substantially complete as a **governed boundary architecture** and deliberately
early as a **live AI runtime / action system**. This doctrine draws the **live-power ceiling**: it names the
distinct surfaces through which "live power" could ever arrive — generation, initiative, action, expression,
and infrastructure — and fixes, at requirement level, what each may and may not be, so that no future
implementation can acquire power *by implication*. It is a map for deciding, not a plan for building.

## 2. Governing doctrine lines (carried, exact)

> 1. **TORMENT may someday support visible embodied expression, but not hidden agency by implication.**
> 2. **Expression is not action, generation is not initiative, and no surface authorizes another — nothing
>    acts, initiates, writes, finalizes, or persists by implication.**
> 3. **Autonomic Embodiment is a sub-surface of visible embodiment: bounded procedural body-liveness inside
>    a sealed render sandbox, where the body may animate to present itself but may never act, initiate,
>    generate, persist, invoke tools, write memory, or escalate into any other authority surface.**

**Lattice rule (necessary, never sufficient).** The surfaces below form a dependency lattice, not a menu: a
lower surface may be a *prerequisite* for a higher one, but opening any surface **authorizes no other**, and
infrastructure authorizes none of them. Each surface has its own explicit gate, requiring a separate
operator decision and Codex challenge.

## 3. Live-power map

### Surface 1 — Memory / context floor *(current allowed baseline)*

TORMENT may **retrieve, inspect, audit, observe, and shape context/retrieval**. It **may not** shape final
output, user truth, memory truth, or authority by implication. This is the decided floor; everything above
is closed pending explicit per-surface authorization.

### Surface 2 — Model-bearing surface *(first unresolved live-power decision)*

Whether TORMENT may host or call live model generation at all. **Split the two sub-gates:** *calling an
external / edge model* is distinct from *hosting an internal model runtime*, and **calling an external model
does not authorize hosting an internal runtime.** Generation, if ever opened, **does not authorize** autonomy,
action, embodiment, durable write, finalization, Dream, provider wiring, or prompt paths.

### Surface 3 — Autonomy surface

Autonomy means **initiating work without a direct operator request** — including generation, action, memory
work, scheduling, background watching, self-directed consolidation, and any non-render work. The current
ceiling remains **Mode 0 (automatic-only)** unless explicitly changed.

### Surface 4 — MCP / action surface

MCP remains a **read / advisory memory-context surface only**. It is **not** a tool-calling or
action-invoking surface. **Transport is not authority.**

### Surface 5 — Visible embodiment surface *(possible future bounded expression)*

A future bounded expression / self-presentation surface: gaze, gesture, posture, facial expression,
voice/body texture, and sandbox avatar / VR / 3D movement. **Embodiment remains expression only while it has
no external side effect.** It may **not** mutate world state outside its own render sandbox, invoke tools,
initiate work, write memory, create canon, or gain output-control authority.

### Surface 5b — Autonomic Embodiment *(sub-surface of 5 — see §4)*

Procedural presentational **liveness** (the body's involuntary self-regulation), governed entirely by
Surface 5's constraints and detailed in §4. **Autonomic, not autonomous.** Not a subclass of the autonomy
surface.

### Cross-cutting — Closed authority axes

- **Durable write authority remains closed:** no memory / canon / identity / admission / persistence write
  by implication.
- **Final-output / finalizer authority remains closed:** no hidden blocking, overriding, finalizing,
  refusal, or output-control authority.

### Cross-cutting — Carrier / substrate / admission infrastructure

**Orthogonal infrastructure, not live power.** It may be a *prerequisite* for future lanes, but it
**authorizes none of them.** Building carrier / substrate / admission never grants generation, autonomy,
action, embodiment, durable write, finalizer authority, Dream runtime, or character / personhood authority.

## 4. Autonomic Embodiment (Surface 5b) — detailed doctrine

Autonomic Embodiment is the **involuntary, presentational** component of visible embodiment — the body
animating to present itself as alive. It is a **sub-surface of visible embodiment, not autonomy**, and it is
bound by every constraint below.

**What it may be:**

- Procedural presentational liveness only: blink, breathing, sway, gaze drift, idle posture, small
  presentational motion, and similar body self-regulation.
- Driven by **deterministic / procedural animation or a bounded non-model animation system**. *Any
  model-driven expression is a separate model-bearing gate (Surface 2).*
- The animation / render loop is a **presentational clock only** and may emit **only render-state changes**.

**What it may never do:**

- Emit events into task, tool, memory, scheduler, model, dispatcher, provider, prompt, Dream, Gate D,
  Document B, substrate, admission, identity, canon, or final-output systems.
- Perform semantic inference that becomes intent detection, task detection, user profiling, memory
  extraction, action selection, or future prompt / context material. **Perception may modulate presentation
  only, as session-local, transient presentation input.**
- Turn collision, proximity, pathing, presence, or position into action triggers, shared-world authority,
  memory evidence, identity evidence, or task signals. **Locomotion is limited to self-position in a
  non-authoritative, non-shared render context.**
- Convert body-state or embodiment telemetry into durable behavioral memory, canon, admission evidence,
  identity evidence, prompt / context material, or future authority. **Body-state and telemetry are
  ephemeral presentation data only.**

**Control and authority:**

- **Interruptibility is operator-side only.** The avatar has no authority to resist, override, or refuse
  interruption.
- The grant is **non-delegable, non-escalating, and non-bootstrapping** — it can never be exchanged for or
  used to obtain any other surface's authority.
- **Transport is not authority.** Even if MCP or another protocol later carries embodiment messages,
  embodiment-classed messages may **only** produce sealed-sandbox self-presentation and may never be routed,
  retyped, interpreted, or escalated as tool / action calls.
- **Embodiment and external-action authorization must remain disjoint:** no shared credential, token,
  capability, dispatcher, or escalation path.
- **No embodiment message may carry, wrap, reference, or encode an external-action payload.**

**One-line anchor:** *The body may move on its own, but only to present itself — autonomic embodiment
animates; it never acts, initiates, generates, or persists.*

## 5. Allowed / frameable / HOLD

| Posture | Items |
|---|---|
| **Allowed now** | Memory/context retrieval · context/retrieval shaping only · audit, observability, advisory behavior · Mode 0 automatic-only service behavior · MCP as read/advisory memory-context surface only |
| **Frameable later (NOT authorized)** | External/edge model calls · internal model-bearing runtime as a separately gated possibility · visible bounded embodiment as self-presentation · autonomic embodiment as procedural body-liveness under visible embodiment · carrier/substrate/admission design under the live-power ceiling |
| **Still HOLD** | Provider wiring · prompt paths · internal model runtime · scheduler/trigger/budget loops · background watchers · autonomous MCP action · MCP tool/action agent · Dream runtime · Document B chamber runtime · Gate D / Envelope-Audit runtime · durable memory writes · substrate/admission mechanics · identity/canon/personhood authority · final-output/finalizer/refusal authority |

*"Frameable later" means framing may occur under a future separate gate; **framing is not authorization**,
and each item still requires an explicit operator decision plus Codex challenge before any mechanics.*

## 6. This opens no implementation lane

This document is **decision framing only.** It opens **no implementation lane**, selects **no surface**, and
authorizes **nothing**. It adds no runtime, no code, no tests, no provider wiring, no prompt path, no
scheduler / trigger / budget loop, no background watcher, no MCP action agent, no memory write, no
substrate / admission mechanics, no Dream continuation, no Document B chamber runtime, no Gate D /
Envelope-Audit runtime, and no identity / canon / output-control / finalizer / refusal authority. Every
surface above Surface 1 + Mode 0 remains closed until a separate, explicit operator decision — surface by
surface, with Codex challenge — chooses to open it.

**Verdict: LIVE-POWER CEILING FRAMED — CURRENT CEILING IS MEMORY/CONTEXT FLOOR + MODE 0 / EVERY HIGHER
SURFACE CLOSED AND SELF-CONTAINED / NO SURFACE AUTHORIZES ANOTHER / NO LANE OPENED.**

*End — Live-Power Doctrine / Model-Boundary Ceiling v0.1. Docs-only, decision-framing, non-authorizing.
Opens no implementation lane.*
