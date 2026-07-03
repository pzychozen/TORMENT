# TORMENT — Typed Embodiment Tunnels / Effect-Scope Ladder v0.1

**Status:** DOCS-ONLY doctrine/design artifact. **Decision-framing only — non-authorizing, non-implementing.
Opens no implementation lane.** A design frame for **future external-model-first AI embodiment**: how an
external model, given governed context and possibly sensory input, could one day drive a visible VR/3D/game
body through **sealed, effect-scoped channels** — without any of it becoming generic MCP/tool agency, OS
control, model runtime, durable write, or a self-driving loop. It **touches no database / substrate /
admission** and works like TORMENT's cognition surfaces: typed, bounded, candidate-like, traceable,
non-authorizing, session-local. Subordinate to `docs/TORMENT_LIVE_POWER_DOCTRINE_MODEL_BOUNDARY_CEILING_v0.1.md`
(this elaborates its Surfaces 4/5/5b); `PROJECT_ORIENTATION_MAP.md` §0 remains the active work-order. §0 wins
unless Hilmir explicitly overrides.

**Carry doctrine (exact):**

> **Typed Embodiment Tunnels may be framed as sealed, effect-scoped channels for input, presentation,
> sandbox motor, sandbox action, and operator override — but they authorize no model runtime, no MCP/tool
> action, no OS control, no durable write, and no perception-to-action loop without a separate autonomy
> gate.**
>
> **Input-only is not authority-free cognition, and sandbox input is bounded by injection point, not by key
> name.**

---

## A. Purpose

To fix, at requirement level, the **shape and ceiling** of any future embodiment control before a line of it
is built. The organizing principle is a single safety axis — **how far a message's effect can reach** — the
*Effect-Scope Ladder*. Every channel ("tunnel") is pinned to exactly one rung; the ladder, not the channel
list, is the doctrine. External-model-first is preferred: the external model may form intent; TORMENT is only
the **governed router + typed executors + sealed sandbox**, and holds no more authority than the rung a
message is classed to.

## B. Effect-Scope Ladder

| Rung | Effect scope | Authority class | Meaning |
|---|---|---|---|
| **0** | `input_only` | `input` | Sensory input; reads only, effects nothing |
| **1** | `render_only` | `presentation` / `autonomic_presentation` | Changes only the avatar's own appearance/voice |
| **2** | `self_position_only` | `sandbox_motor` | Moves the avatar's own pose/position in a non-shared sandbox |
| **3** | `sandbox_state_only` | `sandbox_action` | Mutates objects/state **inside the sealed sandbox only** |
| **4** | `external_world` | — | **FORBIDDEN as an embodiment tunnel.** OS/file/app/net/tool = generic MCP/tool action, a separate surface that remains **HOLD** |
| **⊥** | `operator_control` | `operator_control` | Orthogonal; operator-only session control / emergency stop; overrides all rungs |

**No rung authorizes the rung above it.** Rung 4 is never an embodiment tunnel — it is named here only to
be excluded, so nothing in the embodiment vocabulary can reach it.

## C. Tunnel classes

Each tunnel is pinned to exactly one rung. Presentation tunnels carry a **driver** sub-axis: a *procedural /
idle* slice (Autonomic Embodiment, Surface 5b) and a *deliberate / model-driven* slice (Surface 5, and if
model-generated, Surface 2).

| Tunnel | Rung | Autonomic (5b) slice | Separate gate for |
|---|---|---|---|
| Facial expression | 1 `render_only` | idle blink, micro-drift, breathing-linked | selected expressions, emotion tags |
| Gaze / attention | 1 `render_only` | idle gaze drift | look-at-target (perception-modulated / model-driven) |
| Body posture | 1 `render_only` | idle sway, breathing, balance | chosen stance/attitude |
| Gesture | 1 `render_only` | micro-fidget only | semantic gestures (wave, point, nod) |
| Speech / voice / lip-sync | 1 `render_only` | — | always separate (content-bearing; §F.6 / Surface 2) |
| Autonomic body | 1 `render_only` | (this *is* the 5b tunnel) | — |
| Locomotion | 2 `self_position_only` | — (idle wander only if later gated) | all locomotion |
| Object interaction | 3 `sandbox_state_only` | — | all interaction |
| Sandbox Input Emulation | 2–3 (per input) | — | all input (see §E) |
| Sensory input | 0 `input_only` | — | any downstream use (see §G, cognition note) |
| Operator session control | ⊥ `operator_control` | — | operator-only |

**Tunnel doctrine:**

- Each tunnel binds **per-message effect only**.
- Tunnels do **not** authorize continuous control, perception-to-action loops, background watching, idle
  navigation, or any sensorimotor policy. **Tunnel permission is not loop permission** (§F).
- A tunnel's closed vocabulary is a finite enum; anything outside it is rejected.

**Request shape (illustrative, not a schema):** `tunnel_class` · `authority_class` · `effect_scope` ·
`driver: procedural | model_driven` · `loop_binding: single_shot | operator_session_bound` ·
`render_target / sandbox_id` · `duration: instant | timed | until_cancelled` · `executor` ·
`allowed_vocabulary` · reject-list · invariant `operator_revocable: true`.

## D. Executor / sink rules

- **Authority lives at the executor/sink, never at the router.** The router may classify and route but holds
  **no execution capability**.
- Each sink **independently revalidates**: tunnel class, authority class, effect scope, sandbox ID, origin,
  duration, closed vocabulary, and reject-list — and refuses any mismatch (defense in depth; type-at-the-sink).
- **No shared credential, token, capability, dispatcher, or escalation path** across tunnels. A grant on one
  tunnel can never widen into, delegate to, or bootstrap another.
- Every tunnel **rejects** foreign payloads: `external_action`, `memory_write`, `tool_call`,
  `provider_prompt`, `scheduler`, `identity_canon`, `finalizer`. No message may carry, wrap, reference, or
  encode a higher-rung or foreign payload.
- **Transport is not authority.** Even if MCP or any protocol later carries tunnel messages, an
  embodiment-classed message may only produce its rung's effect and may never be routed, retyped, or
  escalated as a tool/action call.

## E. Sandbox Input Emulation (keyboard / mouse / controller)

Renamed from "keyboard/mouse/controller" to **Sandbox Input Emulation** (a.k.a. Bound-Process Input Channel)
— because the danger is the **injection point, not the key name**. A keystroke is harmless in a game's own
buffer and catastrophic in the OS input queue.

- **Bound by injection point and target identity**, not by key name. Delivered into **one sandbox process /
  one render-input target** only.
- **Never** OS `SendInput`, global HID, active-window routing, clipboard, shell, browser, desktop,
  Alt-Tab, system shortcuts, global mouse coordinates, or any unbound window.
- **Losing sandbox identity cancels input** — it must never redirect to another target.
- Movement inputs (WASD, sticks, camera) are rung 2 `sandbox_motor`; state-changing inputs (click-to-use,
  action buttons, inventory) are rung 3 `sandbox_action`. **Combos/sequences inherit the highest effect
  rung** of their constituents.
- If a synthetic input can ever reach the OS input layer, it has silently become rung-4 generic computer
  control — the single most severe leak; the executor must be structurally incapable of it.

## F. Sensorimotor-loop warning (the deepest leak)

**Typed tunnels bound the effect of each message; they do not bound the loop.** Even if every message is
perfectly bounded, running sensory → motor/action as a **continuous self-driving loop is autonomy** — the
body initiating work without a per-step operator request (Live-Power Surface 3). Therefore:

- **Tunnel permission is never loop permission.** Granting tunnels authorizes single, operator-session-bound
  messages, not a live perception-to-action policy.
- Any closed perception→action loop, idle navigation, background watcher, or sensorimotor policy is a
  **separate autonomy gate** requiring an explicit Mode change (ceiling remains Mode 0).
- **External-model-first sharpens, not softens, this**: the external model could drive a tight sensorimotor
  loop, so granting it tunnels never grants it a live loop over them. Who closes the loop, and whether it
  runs unprompted, is the autonomy question — separate from this taxonomy.
- Speech is content-bearing and so is also always a separate gate (§C).

## G. Database / substrate non-touch rule

This frame **touches no** database, carrier, substrate, admission, durable write, learning store, body-state
memory, telemetry memory, identity evidence, canon evidence, or prompt/context persistence. Sensory input,
body-state, and embodiment telemetry are **session-local, transient, input/presentation data only**. **Input-only
is not authority-free cognition**: sensory input must **not** become prompt/context material, task detection,
profiling, memory extraction, durable memory, or action selection unless separately gated. Any future
learning from gameplay is a **separate durable-write / admission decision**, not implied here.

**Relation to cognition.** Treat tunnel requests like bounded **candidates/effects, not authority** —
analogous to memory candidates that are contained until governed admission. TORMENT may later inspect, trace,
or request-shape tunnels, but **tunnel traces never become memory or authority by implication**.

## H. Allowed / frameable / HOLD

| Posture | Items |
|---|---|
| **Allowed now** | Nothing new — current ceiling stays memory/context floor + Mode 0; this is framing only |
| **Frameable later (NOT authorized)** | The Effect-Scope Ladder; typed tunnels for input / presentation / sandbox motor / sandbox action / operator control; Sandbox Input Emulation as a bound-process channel; external-model-first embodiment routing under the live-power ceiling |
| **Still HOLD** | Model runtime · provider wiring · prompt paths · generic MCP/tool action · OS-level input control · perception-to-action loops / sensorimotor policy / idle navigation · scheduler/trigger/budget loops · background watchers · durable memory writes · substrate/admission mechanics · Dream runtime · Document B chamber runtime · Gate D / Envelope-Audit runtime · identity/canon/personhood authority · final-output/finalizer/refusal authority |

*"Frameable later" means a future separate gate may frame it; **framing is not authorization**, and each item
still requires an explicit operator decision plus Codex challenge before any mechanics.*

## I. This opens no implementation lane

Decision-framing only. No implementation, code, tests, runtime, provider wiring, prompt path, scheduler /
trigger / budget loop, background watcher, generic MCP action, OS-level input control, durable memory write,
substrate / admission mechanics, Dream continuation, Document B chamber runtime, Gate D / Envelope-Audit
runtime, identity / canon / personhood authority, or final-output / finalizer / refusal authority. Transport
is not authority; no surface authorizes another; embodiment and external-action authorization remain disjoint;
typed tunnels authorize no perception-to-action loop. Every tunnel and rung remains closed until a separate,
explicit operator decision — with Codex challenge — chooses to open it.

**Verdict: TYPED EMBODIMENT TUNNELS FRAMED ON THE EFFECT-SCOPE LADDER — SEALED, PER-MESSAGE, EXECUTOR-ENFORCED,
INJECTION-POINT-BOUND / NO LOOP, NO OS CONTROL, NO MCP ACTION, NO DURABLE WRITE, NO SUBSTRATE / NO LANE OPENED.**

*End — Typed Embodiment Tunnels / Effect-Scope Ladder v0.1. Docs-only, decision-framing, non-authorizing.
Opens no implementation lane.*
