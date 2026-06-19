# Checkpoint — Thinking Layer Tuned-Scoring Provenance Lock

**CODE-SLICE CHECKPOINT — docs-only record of a landed tests-only protection slice. No new gate, no
behavior change, no registry amendment.**

**Anchor:** `cbdc609` *test(cognition): lock tuned scoring buckets under ambiguity thresholds*.
**Date:** 2026-06-19.

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

This is a **tests-only provenance / characterization lock** for the scoring functions that sit
underneath the already-locked ambiguity-clarify thresholds. It is **not** a behavior change, **not** a
threshold change, **not** private cognition, **not** dream / incubation, **not** database/substrate, and
**not** Writer Authority. It records current behavior so a future agent cannot silently drift the tuned
scoring buckets. Tuned constants are not cleanup dust.

## 2. What landed (and what did not)

Tests added to `tests/test_thinking_controller.py` that pin the **current** output of
`thinking_controller._estimate_ambiguity` and `_estimate_urgency` through the public `frame_task` seam.

**No scoring value changed. No threshold changed. No shared constant introduced. No behavior changed.
No production code changed.**

- **Source surface (unchanged, only characterized):** `torment_service/thinking_controller.py` —
  `_estimate_ambiguity` and `_estimate_urgency`.
- **Test surface:** `tests/test_thinking_controller.py` — per-signal contribution locks, reachable-bucket
  locks, the `??`-guard distinction, and the urgency-override boundary.

## 3. Protected buckets (current implementation; neither reaches 1.0)

- **Ambiguity:** `{0.0, 0.20, 0.35, 0.40, 0.55, 0.60, 0.75, 0.95}`
  (short-text +0.35; "maybe/sort of/kind of" +0.20; `count("?") > 1` +0.20; "something/stuff/thing"
  +0.20; capped at 1.0).
- **Urgency:** `{0.0, 0.1, 0.2, 0.3, 0.6, 0.7, 0.8, 0.9}`
  ("urgent/asap/immediately" +0.6; "now/quickly" +0.2; "!" +0.1; capped at 1.0).

`1.0` is **not reachable** through current public text signals.

## 4. Validation evidence (Windows-authoritative)

- `tests/test_thinking_controller.py` — **18 passed** (0.11s).
- Adjacent focused set (thinking_controller + fallback_chain + action_policy_legality + drift_veto +
  cognition_pipeline) — **307 passed** (0.42s).
- Full suite — **3975 passed, 5 skipped, 22 subtests passed** (83.41s).

## 5. Why it mattered

The prior `0.60` (fallback) / `0.72` (primary) ambiguity-threshold provenance lock
(`docs/CHECKPOINT_2026-06_THINKING_LAYER_AMBIGUITY_THRESHOLD_PROVENANCE.md`) reasons about *additive
scoring buckets* — e.g., 0.72 sits in the empty gap between the reachable 0.55 and 0.75 buckets, and the
fallback 0.60 corresponds to the three-signal bucket. Those thresholds were locked, but the **scoring
buckets they depend on were under-characterized** (only spot-tested at two combinations). A silent
change to a `+0.20` or `+0.35` contribution could have shifted the buckets and quietly invalidated the
threshold reasoning *without failing the existing tests*. This slice closes that hole: the calibration
basis is now test-characterized and will fail loudly on drift.

## 6. Codex correction recorded

A reachable high-ambiguity bucket is **not** the same as a primary-clarify-triggering case. Buckets that
require `??` (e.g. the 0.95 bucket) can be **above 0.72** yet are still **blocked from primary
clarification** by `choose_action`'s separate `"?" not in lower` guard. The tests assert this distinction
explicitly (a `0.95`-scoring `"??"` input does not produce `ASK_CLARIFICATION` on the primary path),
locking "all reachable buckets" apart from "primary-clarify-triggering behavior."

## 7. Boundaries held

No scoring value change. No threshold change. No shared constant. No behavior change. No production code
change. No private cognition / dream runtime. No database / substrate. No Writer Authority continuation.
No Seed-Governance / P4 / source-sameness / governance vehicle. No hidden chain-of-thought storage or
exposure. No mode-selection or lane-budget change.

## 8. Lane posture

The Thinking Layer's clean, honest small-slice vein (observability parity, dead-field wiring, threshold
provenance, and now scoring provenance) is harvested. **The Thinking Layer should pause after this**
unless a new, genuinely bounded, non-decorative slice is separately found — do **not** force another
protection lock. Database / substrate remains last.

---

*Code-slice checkpoint only. Tests-only protection, not behavior change. No scoring value, threshold, or
shared constant changed; no production code changed. Tuned constants are not cleanup dust. Audit observes
authority and does not become authority. Memory may shape context. Memory may not seize authority.
Database / substrate remains last.*
