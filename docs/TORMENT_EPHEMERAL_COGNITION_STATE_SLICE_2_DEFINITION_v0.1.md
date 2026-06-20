# TORMENT Ephemeral Cognition State — Slice 2 Definition / Authorization v0.1

**Status:** ACTIVE — first rule **IMPLEMENTED** (`06a9536`). The envelope below remains in force for any
*further* shaping rules. **Not doctrine, not a gate or registry artifact.** It fixes the *envelope* of
what Slice 2 numeric retrieval-shaping may touch, so each rule stays tiny, explicit, reversible, and
test-locked.

**Lane:** Ephemeral structured cognition state (pre-database).
**Slice 1:** CLOSED — code `4e164c3`, board `3d461b8`. Behavior-preserving routing scaffold only; no
capability added.
**Provenance:** Claude audit + Codex adversarial review both concluded Slice 2 is premature for direct
implementation and needs this definition first.
**Authority note:** navigation / authorization aid only. The orientation map, Decision Registry, and
promoted contracts remain source of truth.

> One-line gate: a Slice 2 rule may NOT be implemented until §4 (exact numeric rule) and §5 (final
> rollout posture) are filled in and accepted. (Rule 1 is now accepted and landed — see implementation
> status below; this gate still governs any *additional* rule.)

> **Implementation status (2026-06-20):** Rule 1 landed at `06a9536`, default-off behind
> `TORMENT_COGNITION_SHAPING_V2`: when `ambiguity_score >= 0.50` **and** `deep.top_k > 0`, `deep.top_k`
> +1 (cap 4, never reduce). The §2 **deep-disabled guard was ratified** — no `retrieve_deep=False` with
> `deep.top_k=1`. §4/§5 are DECIDED *for Rule 1*; the schema and §11 gate still apply to further rules.
> Validation `126 passed`; working tree clean (`## main...origin/main`).

---

## 1. Target surface — DECIDED

- **In scope:** controller-produced `MemoryPlan` (`ThinkingController.build_memory_plan` /
  `deliberate_only` / `think`) and the `/agent/query` plan export (`top_k_by_lane`, `weight_by_lane`)
  that feeds `fabric.query`.
- **Out of scope:** behavior packs. Active packs replace the controller plan wholesale in
  `AgentRunner.run_turn` (`bundle = replace(bundle, memory_plan=self.pack.aperture_recipe.memory_plan)`),
  so shaping the controller plan has no effect under a pack and must not pretend otherwise.
- **Unpacked `AgentRunner`:** inherits the controller plan, so it is covered transitively — but Slice 2
  adds NO runner-specific logic.

## 2. Eligible fields — DECIDED

- **May change:** `top_k_by_lane`, `weight_by_lane` (bounded; see §3–§4).
- **Frozen in Slice 2:** `safety_constraints` (governance/identity invariants) and `max_token_budget`.
  These are not retrieval *shaping*; leaving them untouched keeps the slice's blast radius to lane
  aperture only.
- Retrieval booleans (`retrieve_*`) are NOT a Slice 2 target — Slice 2 shapes *how much* of an
  already-enabled lane, never *whether* a lane is enabled.

## 3. Eligible lanes — DECIDED

- Source review: `fabric.query` wires lane budgets for **`core`**, **`relational`**, **`deep`** only
  (`_core_k`, `_relational_k`, `_deep_k`). `archive` and `collective` `top_k_by_lane` values are **not
  consumed** in that path.
- **Slice 2 may shape only `core`, `relational`, and/or `deep`.**
- `archive` / `collective` remain **named-only, no live shaping** until their consumer path is proven
  live (separate audit). A Slice 2 that changes archive/collective numbers is a scope breach.

## 4. Scalar drivers — UNRESOLVED (operator/trio decision required before implementation)

- **Candidate drivers** (fields already on `EphemeralCognitionState`): `ambiguity_score`, `urgency`,
  `confidence_need`, `memory_need`, `governance_sensitive`, `identity_sensitive`.
- **No fuzzy policy.** A driver→effect statement like "more ambiguity means more memory" is NOT
  acceptable. Every rule must instantiate this schema exactly:

  ```
  RULE: when <driver> <comparator> <threshold>,
        <lane>.<top_k|weight> changes by <exact bounded delta>,
        clamped to <explicit bound>; otherwise unchanged.
  ```

  Required properties of any proposed rule: (a) exact integer (top_k) or exact float (weight) delta;
  (b) monotonic and bounded — small, named min/max; (c) reversible — flag-gated per §5; (d) expressed as
  exact before→after on a single named eligible lane.
- **Recommended minimal first instance:** exactly **one driver × one eligible lane × one bounded delta**
  (prefer an integer `top_k` nudge on `core` or `deep`). Add further rules only as separate, separately
  tested follow-ups.
- **ILLUSTRATIVE ONLY — NOT ADOPTED** (shows the schema, decides nothing):
  `when ambiguity_score >= 0.50, deep.top_k += 1, clamped to <= 4; otherwise unchanged.`
  The actual driver, threshold, lane, delta, and bound are operator/trio choices, not made here.

## 5. Default-off / rollout posture — DECIDED (default) / UNRESOLVED (final pick)

- **DECIDED default:** Slice 2 ships **default-off behind an env flag** (proposed name
  `TORMENT_COGNITION_SHAPING_V2`, default off), OR **characterization-first** (rule computed and tested
  but not wired into the live plan) if any doubt.
- **UNRESOLVED:** default-on is permitted **only** if the adopted delta is extremely small AND flag-off
  parity tests prove byte-identical `MemoryPlan` to today. That call is deferred to authorization time,
  after §4 is fixed.

## 6. Pack interaction — DECIDED

- Active behavior packs replace the controller `MemoryPlan` wholesale (§1). Slice 2 must **not** alter
  pack behavior in its first implementation; a pack-active turn must produce the **same** plan as today.
- Pack/controller **merge rules** (letting shaping survive into pack turns) are a **separate, later
  slice**, not authorized here.

## 7. Clamp / retrieval effect — DECIDED

- Downstream, `fabric.query` clamps each lane to `[0, top_k*2]` and further bounds `deep` by remaining
  headroom (`min(_deep_k, _remaining)`). A numeric nudge can therefore be **absorbed** and produce no
  retrieval-result change.
- Consequence: **Slice 2 correctness is asserted at the `MemoryPlan` boundary**, not at retrieval
  results. Any retrieval-result test must be narrow, controlled, and treated as secondary evidence only.

## 8. Trace parity — DECIDED

- `tests/test_trace_lane_weight_parity.py` locks agreement between query and trace lane weights. Any
  Slice 2 change to `weight_by_lane` must **preserve that parity or deliberately update the test in the
  same commit** with a recorded rationale. A `top_k`-only first rule sidesteps this and is preferred for
  the minimal instance.

## 9. Hard exclusions — DECIDED (carried from the lane contract)

No serialization · no `ThinkingResult` exposure · no `/thinking/debug` exposure · no `/agent/query`
output-shape change · no durable state · no database/substrate · no output blocker/finalizer · no
identity pinning · no monitoring/autonomy/self-trigger · no Gate 4 writer remedies · no P4 mechanics ·
no Seed-Gov/O6 mechanics · no candidate store/governed admission · no dream/incubation runtime. Hitting
any of these is a stop condition.

## 10. Required tests before any implementation commit — DECIDED

1. **Flag-off parity** (if a flag is used): `MemoryPlan` byte-identical to pre-Slice-2 across the
   existing representative matrix.
2. **Exact `MemoryPlan` before/after** at the plan boundary for the adopted rule (the only place the
   change is asserted to take effect).
3. **Lane eligibility:** `archive` / `collective` `top_k_by_lane` unchanged vs today.
4. **Pack non-effect:** a pack-active turn yields the same plan as today (shaping is overridden).
5. **Trace lane-weight parity:** preserved, or updated-with-rationale, only if weights change.
6. **Existing anchor validation** (must stay green):
   ```
   python -m pytest tests\test_ephemeral_cognition_state.py tests\test_thinking_controller.py tests\test_gate_a_tests_only_locks_c1_c5.py tests\test_trace_lane_weight_parity.py -v
   ```

---

## 11. Authorization gate (what must be true to start Slice 2 implementation)

- [ ] §4 rule(s) filled in to schema, with exact deltas and bounds.
- [ ] §5 posture finalized (default-off / characterization-first / small-delta default-on).
- [ ] Operator approval recorded; Codex adversarial pass on the chosen rule.
- [ ] Touch-list confirmed: `thinking_controller.py` (+ `thinking_models.py` only if a flag/field is
      needed) and tests only. No `app.py` / `agent_loop.py` / `fabric.py` / `behavior_packs.py` edits.

## 12. Unresolved questions (must be answered before implementation)

1. **Exact rule(s)** — driver, comparator, threshold, lane, field, delta, bound (§4).
2. **Final rollout posture** — flag-gated vs characterization-first vs small-delta default-on (§5).
3. **`top_k` vs `weight`** for the first rule — `top_k`-only avoids the trace-parity obligation and is
   recommended for the minimal instance, but not mandated.

## 13. What this artifact does NOT do

It does not implement, authorize, or schedule Slice 2; does not change code, tests, packs, or any
endpoint; does not modify the orientation map, Decision Registry, or any gate; and does not pick the
numeric policy. It only bounds the design space.

*End — Slice 2 Definition / Authorization v0.1. Definition artifact; not doctrine, gate, or registry.*
