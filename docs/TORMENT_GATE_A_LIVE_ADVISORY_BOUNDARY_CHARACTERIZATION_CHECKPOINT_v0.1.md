# TORMENT Gate A — Live-Advisory Boundary Characterization Checkpoint v0.1

**CHARACTERIZATION CHECKPOINT ONLY — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION.**

Records the characterized boundary from Claude's read-only trace report + Codex's adversarial
corrections. A **characterization checkpoint, not a proof closure.** It changes no runtime, adds
no tests, and authorizes no locks or fixes.

**Date:** 2026-06-17. **Lineage:** Gate A trace plan → Claude read-only trace report → Codex
adversarial corrections (query-mutation precision) → this checkpoint.

---

## 1. Status and scope

- **Trace baseline: `03cf734`** (Gate A opening commit). **Checkpoint filed at `3316073`.**
- **Gate A is open characterization-only.** This is a checkpoint, **not a proof closure**. No tests,
  no code, no fixes are produced or authorized here.

## 2. Confirmed boundaries

- `ThinkingController`, `MemoryPlan`, stance, draft/review, and geometric harvesting **do not directly
  perform memory admission, canon promotion, private-cognition candidate admission, or Document B
  chamber writes.**
- `ThinkingController` is **not** Document B private cognition (it is deterministic/advisory routing +
  retrieval shaping + response drafting/stance).
- **No Document B chamber, candidate store, or dream runtime exists.**

## 3. Corrected query characterization (Codex precision)

> Advisory surfaces do not directly perform memory admission, canon promotion, private-cognition
> candidate admission, or Document B chamber writes. `MemoryPlan` shapes retrieval budgets/weights.
> `/agent/query` uses only that plan, but `fabric.query` has retrieval-internal state effects, so
> "read-only" here means **no direct advisory authority writer, not no mutation anywhere.**

**`fabric.query` is not fully side-effect-free** — it has retrieval-internal mutation:
- the deep / spirit-return lane can **persist warmup state** through `WarmupTracker.get_or_create()`
  and `_persist()`;
- query scoring can **mutate an entity payload with evolved SRG state**.

These are **not** canon / admission / private-cognition writes, but they refute any broad
"query is side-effect-free" wording. The correct three-way model:

```
1. Direct advisory write           → NOT FOUND
2. Retrieval-internal mutation      → FOUND inside fabric.query (warmup state, evolved SRG state)
3. Advisory-shaped response → memory → FOUND via AgentRunner Phase-7 ordinary ingest
```

## 4. `/agent/query` characterization

- calls `ThinkingController.think()`;
- **discards** draft / review / stance;
- converts **only** `memory_plan` to lane budgets/weights;
- calls `fabric.query`;
- does **not** directly call ingest / promote / gravity;
- **can inherit** `fabric.query` retrieval-internal state effects (warmup persist, evolved SRG state).

## 5. Phase-7 ordinary-ingest characterization

- `AgentRunner.run_turn` builds a compact turn summary (`_build_ingest_summary`) and calls
  `fabric.ingest` (only when the turn was not review-blocked, has response text, and is not a no-op).
- **Advisory-shaped response text can enter ordinary memory through this path.**
- **Ordinary ingest is NOT Document B private-cognition candidate admission.**
- Ordinary ingest can: reinforce existing rows, emit `_maybe_emit_identity_anchor`, emit `mood_drift`,
  measure drift, save character state, and (periodically, via the drift band) invoke gravity correction
  — the ordinary-ingest **fan-out**.
- It **does not** route through `/promote` force.

## 6. Writer hazards remain parked Gate B issues

Kept visible, routed to Gate B / separate reconciliation; **not** characterized as correct, **not**
fixed here:

- `gravity_correction` automatic `canon=True`.
- `_maybe_emit_identity_anchor` automatic derived identity writer.
- `POST /promote` force bypass — **note: not part of the Phase-7 path**, but remains parked.
- `mood_drift → centroid → gravity_correction → canon=True`.
- **`AgentRunner.run_turn` Phase-8 (Stabilize) `gravity_correction` reachability** — a parked Gate B
  residual. `run_turn` reaches gravity correction by **two distinct routes**, not only one: (a) the
  Phase-7 ordinary-ingest fan-out (drift band), and (b) **Phase-8 Stabilize**, which reuses the Phase-5
  drift measurement and can invoke gravity correction directly. Readers must not infer all `run_turn`
  gravity reachability flows only through Phase-7 ordinary ingest.

The Phase-7 ordinary-ingest fan-out (§5) is *one* path by which a turn can *reach* the
mood_drift / drift-band / identity-anchor hazards; **Phase-8 Stabilize is a separate route to
`gravity_correction`** within the same turn; `/promote` force is a separate caller-triggered
surface.

## 7. Spine / audit characterization and residual

- No durable advisory persistence was found in the **traced Spine success path**.
- Alignment is an **in-memory ring buffer**.
- Advisory / alignment outputs are placed into the **returned audit envelope** (observability in the
  response), not a durable store in the traced path.
- **Residual:** external logging / audit durability outside the immediate return path is **not fully
  traced** and remains open (§8).

## 8. Residuals explicitly open

- Exact **durability / classification** of `fabric.query` retrieval-internal mutations (warmup state,
  evolved SRG state) — persistence scope and governance posture not fully pinned.
- **Spine / audit envelope durability** outside the immediate return path.
- **Ordinary-ingest fan-out** reachability to the parked Gate B writer hazards (named, routed to Gate B).
- **`AgentRunner.run_turn` Phase-8 (Stabilize) `gravity_correction` reachability** — a second,
  distinct route to gravity correction within a turn (separate from the Phase-7 fan-out); parked Gate B.
- Full line-by-line confirmation that `fabric.query` performs no admission/authority write (the
  inspected evidence shows none; the retrieval-internal mutations above are the only writes
  identified in the inspected evidence — this is not a full line-by-line proof).

## 9. What this checkpoint does not authorize

No tests-only locks yet; no production fixes; no writer fixes; no P4 mechanics; no Document B runtime;
no dream/incubation; no candidate store; no durable private state; no database/substrate mechanics /
schema / storage / carriers / migration / construction; no `canon_source` selection; no change to
promotion / gravity / identity-anchor behavior; no old-doc mechanism adoption; no registry edit / number.

## 10. Recommended next step

Either a **Codex challenge** of this checkpoint, or — if Codex is already satisfied — a **separate
authorization for tests-only boundary locks after residual review** (§8). **Do not auto-chain:** each
of trace → checkpoint → (challenge) → locks is its own authorized step.

---

## Anti-drift footer

CHARACTERIZATION CHECKPOINT ONLY — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION. Records a
*characterized* (proposed) boundary, not enforcement and not proof closure. "Read-only" for
`fabric.query` means **no direct advisory authority writer, not no mutation anywhere.** Writer hazards
remain parked Gate B issues. Opens no writer fixes, P4 implementation, Document B private cognition,
dream/incubation, candidate store, durable private state, or database/substrate mechanics. No
`canon_source`, no source-sameness mechanics, no monitoring, no durable user-risk scoring, no autonomy.
No registry amendment; no registry number reserved. Old-doc quarantine binding. Guide, not control;
audit observes authority and does not become authority; nothing rewrites identity/canon/seed/soul.
Subsequent steps require their own explicit authorization.
