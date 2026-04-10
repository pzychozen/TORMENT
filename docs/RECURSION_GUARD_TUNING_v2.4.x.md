# Recursion Guard — Tuning Parameters (v2.4.x)

**Owner:** TORMENT storage/recursion-safety surface
**Status:** Active (step 5 of the tactical provenance pass)
**Companion docs:**
- `docs/RECURSION_SAFETY_POLICY_v2.4.x.md` — the policy itself (Rules A–F)
- `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md` — the source-type + write-path registry
- `cognition/recursion_guard.py` — the implementation

---

## Purpose

Several parameters in the archivist writeback recursion guard are **bounded
on purpose**. This document exists so that any future attempt to loosen,
widen, or remove those bounds has a clearly written discipline to follow
before it can be merged.

The guiding stance is the corridor-tearing framing from doctrine rule #5:
*"Provenance is a hard boundary."* If the corridor cannot be shown clean
inside the bounded enforcement window, the safe answer is to reject, not to
keep walking. Every parameter here should be read as a conservative default,
not as a target to maximize.

**Tuning discipline.** Any change to a parameter in this document requires
all three of the following before it lands:

1. **Corpus analysis.** Measure the distribution of the quantity the
   parameter governs (e.g., ancestor-chain depth) on a real production
   corpus. A proposed change must be justified by what the corpus actually
   looks like, not by what the rewrite happens to make convenient.
2. **Rejection-rate diagnosis.** Look at how often the current value is
   causing rejections in the live writeback path. If the current value has
   never fired a rejection, there is no operational pressure to change it
   and the request is premature.
3. **Explicit doctrine review.** The rule numbers in
   `RECURSION_SAFETY_POLICY_v2.4.x.md` are the policy, and this guard is
   their enforcement. Any parameter change must be checked against those
   rules — in particular whether the change preserves the "fail-closed on
   unknown ancestry" posture.

A parameter change that cannot clear all three of these gates is a
parameter change that has not been analysed, has not been diagnosed, and
should not land.

---

## Parameters

### 1. `_RECURSION_GUARD_DEPTH_CAP = 3`

**Location:** `cognition/recursion_guard.py`
**What it does:** Maximum ancestor depth the DFS walk will resolve before
giving up and rejecting the writeback candidate. Depth 1 = immediate parent
of the proposal; depth 3 is the furthest ancestor that can be inspected
inside the window.

**Why 3, not 4 or more:**
- The guard is enforcing a guarded memory corridor, not reconstructing full
  genealogies. A short bounded horizon matches the current conservative
  doctrine posture.
- The concrete laundering cases the policy cares about (collective echo,
  archivist re-chaining, deferred `derived` vocabulary) are all detectable
  within a 3-hop window given the current producer set.
- Every additional hop linearly increases the per-writeback lookup cost
  and the blast radius of a bad normalization rule. The cost is not free.
- Going deeper before we have evidence it is needed would add structural
  complexity ahead of operational pressure, which is exactly the kind of
  drift this document is meant to prevent.

**Failure mode on cap exceeded:** Reject, not warn-and-accept. This is
deliberate. The guard's contract is "the corridor is provably clean inside
the window"; a cap-exceeded chain violates the contract, and the
doctrine-correct answer is to tear the corridor rather than continue
optimistically. See `REASON_DEPTH_EXCEEDED` in the guard module.

**May be tuned later, but only after:**
- Corpus analysis that produces an ancestor-chain-length histogram for a
  meaningful sample of production memories. Needs to show (a) whether
  real chains routinely exceed 3 hops, (b) what the tail looks like, and
  (c) whether the tail contains any value we are currently excluding.
- Diagnosis of whether `REASON_DEPTH_EXCEEDED` has fired in the live
  writeback path at all. If it has fired, how often, and for what chain
  shapes. If it has not fired, there is no operational pressure.
- Doctrine review that confirms the wider window does not weaken the
  archivist-chain or collective-echo exclusions, and does not change the
  admissibility of `derived` or any future reserved source_type.

**Do not change this value** as part of a refactor, a convenience fix, or
to make a specific test pass. The value is a policy choice, not a
performance knob.

---

### 2. `_SAFE_SOURCE_TYPES_IN_WALK`

**Location:** `cognition/recursion_guard.py`
**Current value:** `{user_input, tool_result, memory, role_output}`
**What it does:** Source types that are admissible at any depth inside the
walked window. Anything outside this set is either explicitly rejected
(`collective_echo`, `derived`) or caught by the "undeclared vocabulary"
fallback.

**Why `role_output` is in the set (and `collective_echo` / `derived` are
not):** See the "Collective Echo Exclusion" subsection in
`RECURSION_SAFETY_POLICY_v2.4.x.md` and the SOURCE_COLLECTIVE_ECHO /
SOURCE_DERIVED rows in `PROVENANCE_STATUS_REGISTRY_v2.4.x.md §4`.

**Important asymmetry between the walk and the producer rules.**
Admitting `role_output` at any depth in the walk does **not** mean the
`_SAFE_SOURCE_TYPES_IN_WALK` set can be copied directly to anything
else. In particular:
- The archivist-role check in the guard is independent of this set and
  still rejects any `source_role` containing `"archivist"` regardless of
  `source_type`.
- Producer vocabularies (what a factory may emit) are governed by
  `VALID_SOURCE_TYPES` in `provenance_v1.py`, not by this set.
- The step-4 `_SAFE_PARENT_SOURCE_TYPES = {user_input, tool_result, memory}`
  exclusion for `collective_echo` as a direct parent remains the
  policy-level stance; the walk enforces it symmetrically by rejecting
  `collective_echo` at every depth.

**May be widened later, but only after:**
- A concrete producer of the proposed new source_type exists and has
  landed in the registry as an Active row.
- Corpus analysis showing the producer does not create chains that
  launder previously excluded ancestors (especially archivist or
  collective).
- Doctrine review of whether admitting the new type in the walk implicitly
  admits it as a safe writeback parent, and whether that is desired.

**May NOT be narrowed without:**
- Checking whether the narrowing would cause the writeback lane to
  collapse on a real corpus (this is the concern that kept `role_output`
  in the set in step 5; narrowing it back out must explicitly re-answer
  that question).

---

### 3. `_REJECTED_SOURCE_TYPES_IN_WALK`

**Location:** `cognition/recursion_guard.py`
**Current value:** `{collective_echo, derived}`
**What it does:** Explicit denylist for clarity — these source types are
rejected at any depth with a stable, test-visible reason string
(`REASON_COLLECTIVE_ECHO`, `REASON_DERIVED`). The general fallback would
already catch them, but the explicit denylist makes the policy visible in
the code and gives downstream logging/metrics a specific handle.

**How to add to this set:**
- A new source type is reserved or deferred in
  `PROVENANCE_STATUS_REGISTRY_v2.4.x.md §4`.
- A matching `REASON_*` constant is added to the guard module with a
  stable name.
- Tests assert the rejection at each relevant depth.

**How to remove from this set:**
- The source type must first graduate to Active status in the registry
  with a real producer.
- The corpus must be analysed for any chains that would retroactively
  become admissible.
- Doctrine review — the same discipline as §1.

---

### 4. `_WRITEBACK_MAX_PER_RUN = 5`

**Location:** `cognition/pipeline.py`
**What it does:** Hard cap on the number of writeback proposals ingested
per cognition pipeline run. Not part of the guard itself, but lives
adjacent to it and shares the "bounded on purpose" stance. Documented here
so it is not forgotten.

**May be tuned later, but only after:**
- Diagnosis of whether any pipeline run has actually hit this cap.
- Corpus analysis of writeback rate per run.
- Doctrine review of whether a higher rate would stress any of the other
  bounded parameters (e.g., more writebacks → deeper chains on average
  → more depth-cap rejections).

---

## Appendix — discipline for future parameters

When a new bounded parameter is introduced in the recursion-safety surface
(or any guard with a similar posture), add a section to this document at
the time of introduction. Each section should contain:

1. **Location** — file and constant name.
2. **What it does** — operationally, in one short paragraph.
3. **Why the current value** — the reasoning, not just the number.
4. **Failure mode** — what the guard does when the parameter is exceeded
   or violated.
5. **May be tuned later, but only after** — the three-gate discipline:
   corpus analysis, rejection-rate diagnosis, doctrine review.
6. **Do-not-touch conditions** — if any.

A parameter that is introduced without a corresponding entry in this
document is a parameter that has not been thought about as a policy
choice, and should be treated as provisional until the entry is written.
