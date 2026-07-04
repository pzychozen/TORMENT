# TORMENT - Brainvision / Render-Body Non-Coupling Orientation Frame v0.1

**Status:** DOCS-ONLY mutual-orientation frame. **Non-authorizing, non-implementing. Opens no
implementation lane.** This frame exists only to keep two tempting future branches from being bundled before
either is ready to design:

1. **Brainvision** - perception-shaped / visual-scene awareness.
2. **3D render-body movement** - embodiment-shaped / visible avatar presentation.

`PROJECT_ORIENTATION_MAP.md` Section 0 remains the active work-order and wins unless Hilmir explicitly
overrides. Current ceiling remains **memory/context floor + Mode 0**.

## 1. Purpose

Brainvision and render-body movement point at adjacent future desires, but they are different authority
shapes. Brainvision is an input/perception question. Render-body movement is a presentation/effect-sink
question. If they are designed as one system, the danger is not "vision" or "body" by itself; the danger is
an accidental perception-to-action loop.

This frame therefore sets the default posture before either branch is designed: **firewall first, design
later, implement nothing now.**

## 2. Brainvision boundary

Brainvision is a **perception shape**, not a live camera feed, sensor stream, polling loop, scheduler, runtime,
or provider/prompt path. At this phase it means only a possible future way to represent or reason about visual
scene awareness.

Brainvision may not, by implication:

- open camera capture or a sensor stream;
- poll frames, watch a screen, or run in the background;
- trigger generation, action, render-body movement, memory writes, Dream, MCP/tool calls, OS input, or
  scheduler work;
- become prompt/context material, durable memory, identity/canon evidence, or output-control authority.

## 3. Render-body boundary

3D render-body movement is a **render/effect sink**, not MCP action, tool control, OS input, actuation, or
world-authority. It belongs, if ever separately framed, under visible embodiment / Typed Embodiment Tunnels:
render-only presentation or sealed sandbox motor/effect, never generic action.

Render-body movement may not, by implication:

- invoke MCP, tools, files, apps, OS input, browser/desktop control, or external-world actions;
- consume Brainvision output as a control signal;
- write memory, create canon, alter identity/personhood, or finalize/refuse/output-control anything;
- become a scheduler, idle navigation policy, background watcher, or autonomous body loop.

## 4. Firewall rule

Brainvision and render-body movement must be **scene-disjoint and authority-disjoint by default**.

- Brainvision must not name, consume, trigger, steer, score, or control the render body.
- The render body must not name, consume, trigger, steer, score, or control Brainvision.
- Neither branch may share a dispatcher, credential, capability, event bus, loop owner, memory store,
  scheduler, tool surface, MCP action surface, OS-input path, or escalation path.
- No message from either branch may carry, wrap, reference, or encode a payload for the other.
- The render body should not appear inside Brainvision's scene by default. No mirror, self-camera,
  self-observation, avatar-visible HUD, or body-state visual feedback is assumed.

Any later desire for self-perception, mirror behavior, body-aware scene interpretation, or visual feedback from
body state is a separate gate. It must be challenged as a possible perception-to-action loop, not treated as a
natural consequence of having both branches.

## 5. Main hazard: self-perception feedback

The failure mode is a closed loop:

**Brainvision observes scene -> model or router selects movement -> render body changes scene -> Brainvision
observes the changed scene -> further movement follows.**

That is a perception-to-action loop even if each individual message is typed and bounded. Under the
Automatic-First / Autonomy Ceiling Doctrine, tunnel permission is not loop permission. A sensorimotor policy,
idle body navigation, background watcher, or self-perception feedback loop remains an autonomy gate and stays
closed.

## 6. Empirical blocker: visual_bus_v0

`../visual_bus_v0` remains evidence and a blocker, not an implementation seed. Its declared question was
whether fixed, no-learned-encoder frame-derived TORMENT diagnostics could match or beat a frame-difference
baseline for visual event detection or show structural event separation.

The current result does **not** justify Brainvision mechanics:

- `../visual_bus_v0/outputs/results_summary.md` reports **H1(a) NOT SUPPORTED**: best TORMENT F1 was below
  the frame-diff baseline margin.
- The same result reports **H0 not rejected**: fixed-mapping TORMENT did not beat frame-diff and showed no
  structural ordering separation.
- The experiment conclusion says a learned encoder is likely required before TORMENT can touch pixels
  usefully.

Therefore Brainvision is not mechanically ready. Any future Brainvision frame must start from this blocker,
not from an assumption that the visual bus already works.

## 7. Allowed / frameable / HOLD

| Posture | Items |
|---|---|
| **Allowed now** | Nothing new. Memory/context floor + Mode 0 remain the ceiling. |
| **Frameable later (NOT authorized)** | Brainvision as a perception-shaped design question; render-body movement as a scene-disjoint render/effect-sink design question; a later Codex challenge on whether either branch is ready to frame. |
| **Still HOLD** | Camera runtime; sensor stream; polling loop; scheduler; provider wiring; prompt paths; MCP/tool action; OS input; perception-to-action loop; embodiment implementation; 3D control; autonomy; durable memory writes; substrate/admission mechanics; Dream / Document B / Gate D / Envelope-Audit runtime; identity/canon/personhood authority; final-output/finalizer/refusal authority. |

## 8. Verdict

**BRAINVISION / RENDER-BODY NON-COUPLING ORIENTED - PERCEPTION AND RENDER-BODY EFFECTS MUST BE FIREWALLED /
SCENE-DISJOINT BY DEFAULT / SELF-PERCEPTION FEEDBACK IS THE PRIMARY HAZARD / VISUAL_BUS_V0 REMAINS AN
EMPIRICAL BLOCKER / NO IMPLEMENTATION LANE OPENED.**

*End - Brainvision / Render-Body Non-Coupling Orientation Frame v0.1. Docs-only, non-authorizing. Opens no
implementation lane.*
