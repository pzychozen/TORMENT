# TORMENT — Participation Guidance Frame v0.1

**FRAMING ARTIFACT — NO CODE, NO IMPLEMENTATION AUTHORIZED.** Defines the boundary
for moving `stance` from observation-only into **visible advisory participation
guidance**. It authorizes only a later *narrow, default-off implementation
proposal* — not implementation itself.

**Core principle: `participation_guidance` ≠ output control.** `participation_guidance`
is visible advisory guidance the character MAY express; it never suppresses,
blocks, vetoes, finalizes, or empties a response. "Chosen silence" is only the
expressive, character-facing idea (the character choosing restraint or brevity) —
it is **not** a suppression mechanism and is never a blocker. The code-facing name
is `participation_guidance`, deliberately, to avoid reading it as suppression.

**Date:** 2026-06-21. **Lineage:** Claude source-first frame → Codex accept-after-frame → this filing.

---

## 1. Source premise

- `social_resonance` is computed in `geometric_harvester` and carried on `GeometricStanceContext`.
- `stance_policy._social_compactness_modifier()` already consumes `social_resonance` to influence stance thresholds (e.g. the `SILENT_OBSERVE` token threshold; `RESPOND_BRIEFLY` as a fallback stance).
- Current `stance` is **advisory / observable only** — attached to `ThinkingResult.stance` and the reflection trace; it is not consumed by any decision / retrieval / write / output path.
- `/agent/query` consumes only the `MemoryPlan` (lane `top_k` / `weight`); draft / review / stance are discarded (Gate A C2 lock).
- The existing **real suppression path is `agent_loop` review (`review.blocked`)**. This work **must not** touch it.

## 2. Boundary

`participation_guidance` is **visible advisory guidance only**.

- **MAY:** recommend expressive restraint / defer / briefness, surfaced as an advisory value.
- **MUST NOT:** suppress, block, refuse, veto, finalize, or set response text to `None`.
- **MUST NOT** alter `ok`, `allowed`, `path`, `result_code`, `review.blocked`, or any governance / trust-routing outcome.
- **MUST NOT** write memory, persist state, create authority, canonize, promote, or admit memory.

## 3. Allowed first implementation shape

- A **default-off flag**.
- **Character / agent social route only.**
- A single **visible advisory field** (e.g. `participation_guidance`), values:
  - `none`
  - `respond_briefly_candidate`
  - `defer_candidate`
  - `silent_observe_candidate`
- Final response assembly remains **free to ignore, soften, or express** the value.
- **No** hidden refusal category. **No** hidden risk scoring. **No** durable state.

## 4. Exclusions

No database / substrate; no R-field; no Gate B writer-authority; no Document B / dream / private-cognition runtime; no Seed-Governance; **no `agent_loop.review.blocked` changes**; no output veto; no identity / governance / system / operator turns.

## 5. Required tests (for the later code slice)

1. **Flag-off parity** — no field; behavior byte-identical to today.
2. The visible advisory field appears **only** under the flag.
3. **No** change to `ok`, `allowed`, `path`, `result_code`.
4. **No** `review.blocked` set or changed.
5. **No** `response_text = None`.
6. **No** memory writes / persistence.
7. Governance / identity / operator / system turns are **skipped**.
8. The final response path **remains capable of responding** even when `silent_observe_candidate` is present.
9. The advisory audit remains **inspectable**.

## 6. Closing decision

This frame authorizes only a later **narrow, default-off implementation proposal**.
It does **not** authorize implementation by itself. A code slice proceeds only if
Hilmir / GPT explicitly select it after reviewing this frame, with Codex
challenging the boundary-bearing choices at that point.
