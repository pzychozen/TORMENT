# Checkpoint — Thinking Layer Ambiguity-Threshold Provenance Lock

**CODE-SLICE CHECKPOINT — docs-only record of a landed protection slice. No new gate, no behavior
change, no registry amendment.**

**Anchor:** `d2e26cd` *test(cognition): lock ambiguity-threshold provenance*. **Date:** 2026-06-19.

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

This is a **Thinking Layer threshold-provenance protection** slice. It is **not** a behavior change,
**not** a threshold redesign, **not** private cognition, **not** dream / incubation, **not**
database/substrate, and **not** Writer Authority. It exists to stop a future agent from casually
"unifying" two intentionally distinct tuned thresholds. Tuned constants are not cleanup dust.

## 2. What landed (and what did not)

A comment correction plus tests that lock an intentional distinction. **No threshold value changed; no
shared constant was introduced; no runtime behavior changed.**

- Corrected the misleading comment above `_AMBIGUITY_CLARIFY_THRESHOLD = 0.60` in
  `torment_service/action_policy.py`. The old comment wrongly claimed the 0.60 fallback threshold was
  "tuned to match" the 0.72 primary threshold; the new comment states the two are **intentionally
  different** and must not be unified casually.
- Added tests locking the distinction:
  - primary `choose_action` does **not** ask clarification below its 0.72 bucket boundary;
  - the action-policy fallback **clarifies at 0.60**;
  - the fallback **defers at 0.59**;
  - a drift guard asserting the fallback threshold (0.60) remains **strictly below** the primary (0.72).

## 3. The two thresholds (factual record)

- **Primary** — `thinking_controller.choose_action` uses `ambiguity_score > 0.72`. It is documented and
  test-backed as **bucket-calibrated** against `_estimate_ambiguity`'s additive buckets (see
  `tests/test_thinking_controller.py`): the reachable non-`?` scores straddling it are 0.55 and 0.75, so
  0.72 sits in that gap by design.
- **Fallback** — `action_policy._AMBIGUITY_CLARIFY_THRESHOLD = 0.60`, module-private. It is
  **intentionally lower** than the primary bar (the fallback fires only after an action was already
  ruled illegal for the mode) and belongs to the stance/fallback clarification family (cf.
  `stance_policy` rule 5, `0.60 * geometric_modifier`).

These two values are distinct **by design**. Operator-supplied out-of-project context confirms 0.60 was
deliberately kept as the module-private fallback threshold, separate from the primary 0.72.

## 4. Validation evidence (Windows-authoritative)

- `tests/test_thinking_controller.py` + `tests/test_fallback_chain.py` — **166 passed**.
- `tests/test_action_policy_legality.py` + `tests/test_drift_veto.py` + `tests/test_cognition_pipeline.py`
  — **135 passed**.
- Full suite — **3969 passed, 5 skipped, 22 subtests passed**.

## 5. Files changed in the slice

- `torment_service/action_policy.py` — comment only (value `0.60` unchanged).
- `tests/test_thinking_controller.py` — one primary-side test added (existing 0.75-crosses-0.72 test
  left intact).
- `tests/test_fallback_chain.py` — fallback-side provenance-lock tests added; `_AMBIGUITY_CLARIFY_THRESHOLD`
  imported **only in the test**, not in production.

## 6. What it is NOT (boundaries held)

No threshold value change. No shared constant. No behavior change. No mode-selection or lane-budget
change. No private cognition / dream runtime. No database / substrate. No Writer Authority. No
Seed-Governance / P4 / governance vehicle. No hidden chain-of-thought storage or exposure. No broad
refactor.

## 7. Provenance discipline (carry forward)

Future changes to either threshold — or any tuned constant in this family — require **provenance
archaeology first**: source, tests, docs, commit history, and operator context, *before* any value is
touched. Codex may challenge evidence handling, but is **not** treated as a mathematical authority for
tuned constants; the values were measured and the system was tuned against them. This checkpoint plus the
new tests are the guard that makes accidental unification fail loudly.

## 8. Direction / next step

The intentional 0.60-vs-0.72 distinction is now documented correctly and test-locked. Any further
Thinking Layer work is a separate, explicitly-chosen step. Database / substrate remains last.

---

*Code-slice checkpoint only. Protection, not behavior change. No threshold value changed, no shared
constant, no runtime change. Tuned constants are not cleanup dust. Audit observes authority and does not
become authority. Memory may shape context. Memory may not seize authority. Database / substrate remains
last.*
