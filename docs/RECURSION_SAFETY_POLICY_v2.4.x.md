# TORMENT 2.4.x — Recursion-Safety Policy for Archivist-Origin Memories

## Why this exists

The recursion guard is not a speculative safeguard. Without it,
`_write_back_approved` had two real weaknesses:

- **Crash path on legacy provenance.** A parent memory could still carry
  bare-string legacy provenance (e.g. `"collective"`). The old write-back
  path called `parent_prov.get("source_role")` directly, which raises
  `AttributeError` on `str`. Any archivist write-back that touched a
  legacy-provenance parent would crash the pipeline rather than reject
  cleanly.
- **One-hop laundering gap.** The old logic only inspected direct
  parents. Excluded ancestry (archivist / collective_echo / derived)
  could hide two-plus hops back behind an immediate parent that looked
  admissible. Cognition-tainted or collective-tainted material could flow
  back into memory under a clean-looking wrapper, violating Rule F ("no
  laundering") even when the one-hop check passed.

Both risks stay latent while `TORMENT_ARCHIVIST_WRITEBACK=0`, because the
write-back path is the only caller that walks parent provenance in that
context. They become real the moment the gate is lifted against an older
or production-scale corpus — legacy bare-string records exist in the
population being scanned, and multi-hop ancestry chains are no longer
rare. Under a small or fresh corpus with the gate off, both hazards
sleep; under a real corpus with the gate on, they surface as incidents.

The guard exists so write-back either rejects safely or admits only
ancestry that remains inside the governed provenance corridor. It
normalizes parent provenance before reasoning, walks ancestors in a
bounded fail-closed way, rejects archivist / collective_echo / derived
anywhere in the checked window, and fails closed on malformed, unknown,
or over-deep ancestry. This is why the guard had to land before any
future change that flips the gate — "fix before flipping," not "fix
after incident."

## Purpose

Prevent Archivist write-back from creating self-reinforcing cognition loops
while still allowing bounded, provenance-aware memory formation in the future.

## Core Rule

A memory created by Archivist write-back must not be used as direct source
material for another Archivist write-back in 2.4.x.

## Policy Rules

### Rule A — Direct Recursion Block
If any `parent_eids` reference a memory whose provenance has
`source_role == "archivist_writeback"`, reject the write-back.

### Rule B — Multi-Parent Strict
If a proposal is derived from multiple parents and ANY parent is
Archivist-origin, the proposal is not eligible. Not majority-based — any
single archivist parent blocks.

### Rule C — Missing Provenance
If any parent memory lacks readable provenance, treat as unknown.
Unknown provenance = not safe for Archivist write-back.

### Rule D — Retrieval Visibility
Archivist-origin memories may appear in retrieval. They must be marked
so the write-back stage can refuse them as parents. Retrieval is allowed;
write-back eligibility is restricted.

### Rule E — Generation Depth
If a memory has `source_role == "archivist_writeback"`, its effective
Archivist depth is 1. No memory with depth >= 1 may be used as parent
for another write-back.

### Rule F — No Laundering
Archivist-origin memories do not become eligible again through
reinforcement, resurfacing, re-retrieval, summarization, or movement
through other subsystems. Provenance describes origin, not latest actor.

## Safe Parent Classes

**Direct parent (depth 1) — policy stance:**
Allowed: `user_input`, `tool_result`, `memory` (migrated/imported)
Not allowed: `role_output` with archivist source, `derived` (deferred vocabulary), `spirit_reflection` (deferred), `collective_echo` (see §Collective Echo Exclusion)

**Inside the bounded ancestry window (depth 1–3) — guard stance:**
As of step 5, the enforcement point is no longer a one-hop check. The
bounded-DFS guard in `cognition/recursion_guard.py` walks up to
`_RECURSION_GUARD_DEPTH_CAP = 3` hops and applies the rules at every node.
The walk's admissible source_types are:

`user_input`, `tool_result`, `memory`, `role_output` (non-archivist only)

`role_output` is admitted inside the walk — but not as a direct parent in
the one-hop policy stance above — because under the current producer set
every in-corpus `role_output` memory is archivist-written, and the
archivist role check already rejects those. Rejecting `role_output`
everywhere in the walk would pre-emptively collapse the writeback lane
against non-archivist roles that may produce memories in a future model,
without adding any real safety (the archivist check is already the real
blocker). See `docs/RECURSION_GUARD_TUNING_v2.4.x.md §2` for the
tuning-discipline entry that pins this choice.

`collective_echo` and `derived` are rejected at every depth.
`collective_echo` because of the exclusion below; `derived` because
`SOURCE_DERIVED` is deferred vocabulary and must not be pre-authorized as
ancestor through a chain admission.

### Collective Echo Exclusion

`SOURCE_COLLECTIVE_ECHO` is active on the **write** side: hivemind echoes are
ingested into individual agents via `ProvenanceV1.for_collective_echo()` paired
with `WRITE_COLLECTIVE_REINGEST`. However, collective echoes are **not**
admissible as ancestors for Archivist write-back, and are deliberately
rejected at every depth of the bounded-DFS walk in
`cognition/recursion_guard.py` (`REASON_COLLECTIVE_ECHO`).

Reason: allowing echoes to serve as write-back parents would let material that
originated in another agent's cognition launder into the current agent's
self-write ancestry. That violates Rule F ("no laundering") in spirit even
when the single-hop check passes, because the collective origin is upstream
of the echo itself. Echoes are influences, not autobiography — a design
stance also reflected in the retrieval discount applied at
`fabric.py:3425-3433` (`TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT`, default 0.50).

This exclusion is a conservative default. Revising it would require an
explicit architectural decision that either (a) admits echoes to the safe
parent set with a new Rule G bounding how many collective generations can
participate, or (b) introduces a separate write-back channel for
collective-informed proposals that is governed differently from agent-local
write-back. Neither is in scope for v2.4.x.

## Rejection Reasons

As of step 5, the stable reason vocabulary is exported by
`cognition/recursion_guard.py` as `REASON_*` module constants. Tests,
logs, and metrics should reference the constants rather than duplicate
the strings.

- `archivist_parent_blocked` — any ancestor in the window has an
  archivist `source_role`
- `unknown_parent_provenance` — any ancestor cannot be retrieved, has
  malformed/missing provenance, or was unnormalizable via
  `ProvenanceV1.normalize_parent`
- `unsafe_parent_source_type` — any ancestor's `source_type` is not in
  the walk's admissible set
- `collective_echo_in_ancestry` — any ancestor has
  `source_type == "collective_echo"` (see §Collective Echo Exclusion)
- `derived_in_ancestry` — any ancestor has `source_type == "derived"`
  (deferred vocabulary, see §Safe Parent Classes)
- `ancestry_depth_exceeded` — a node at the depth cap still has
  unresolved parents; fail-closed per the corridor-tearing stance
- `role_output_missing_source_role` — a `role_output` ancestor has no
  `source_role` set (malformed shape; ProvenanceV1 normally rejects this
  at construction, but an old corpus entry could still reach the guard)

## Enforcement Point

At write-back eligibility check time (pipeline step 4b), not at proposal
creation time. Order: retrieve → propose → inspect ancestors (bounded
DFS) → decide → ingest.

## Implementation Status

- Rules A–F: enforced by the bounded-DFS guard in
  `cognition/recursion_guard.py::recursion_guard_check()`.
- `cognition/pipeline.py::_write_back_approved()` orchestrates proposal
  selection and calls the guard with the extracted parent EIDs. It no
  longer contains an inline one-hop check.
- Parent-shape normalization: `ProvenanceV1.normalize_parent()` is the
  single source of truth for turning a raw stored provenance value into a
  canonical dict. All four shapes (None, legacy bare string, dict,
  `ProvenanceV1` instance) reduce to a canonical dict-or-None. Fail-closed
  on anything else.
- Tuning parameters (depth cap, admissible source_type set, per-run
  writeback cap) are documented in
  `docs/RECURSION_GUARD_TUNING_v2.4.x.md` with an explicit three-gate
  discipline for any future change.
- Tests: `tests/test_writeback_recursion_guard.py` exercises the guard
  and the normalization helper in isolation (26 cases covering
  normalization contract, clean chains, rejections, cycles, and
  depth-cap boundary conditions).
- Archivist write-back: remains gated behind
  `TORMENT_ARCHIVIST_WRITEBACK=0`.
- Provenance schema: `torment_service/provenance_v1.py::ProvenanceV1`.
- Debug surface: `GET /debug/provenance` endpoint.
- Dead-code cleanup (step 5 commit B): `ProvenanceV1.check_recursion_safe()`
  and `ProvenanceV1.is_archivist_writeback()` have been removed. They
  described a one-hop check that was neither the live enforcement shape
  nor the policy shape after step 5 commit A, and leaving them in place
  would have been actively misleading. The safety asymmetry note is
  preserved for historical context in
  `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md §7.3`.
