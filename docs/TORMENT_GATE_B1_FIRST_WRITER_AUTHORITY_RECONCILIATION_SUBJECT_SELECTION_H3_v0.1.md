# TORMENT Gate B1 — First Writer-Authority Reconciliation Subject Selection (H3) v0.1

**DOCS-ONLY NON-IMPLEMENTING SELECTION — NO CODE, NO TESTS, NO WRITER CHANGE, NO PROMOTE REDESIGN,
NO BEHAVIOR CHANGE, NO GOVERNANCE VEHICLE, NO REGISTRY AMENDMENT, NO DATABASE/SUBSTRATE.**

This artifact names **H3 (`POST /promote` force bypass)** as the **first reconciliation subject** for
Gate B1. It is a **non-implementing selection** only: it names a subject for a **future separately
authorized decision** and builds nothing.

**Date:** 2026-06-19. **Baseline HEAD = origin/main = `982c69c`** (latest commit *feat(policy): honor
pack high drift action*). Builds on the Gate B hazard inventory
(`docs/TORMENT_GATE_B_WRITER_AUTHORITY_HAZARD_INVENTORY_v0.1.md`) and the Gate B decision frame
(`docs/TORMENT_GATE_B_WRITER_AUTHORITY_DECISION_FRAME_v0.1.md`).

> Memory may shape context. Memory may not seize authority.

---

## 1. Status and anti-drift banner

Selection only. Naming H3 as the first reconciliation subject neither opens it, changes it, nor blesses
any remedy. No writer is changed, governed, scheduled, or built. H3 remains a **parked
non-conformance**; this artifact moves it from "inventoried hazard" to "named first subject for a
future separately authorized decision," and stops there.

**Gate B remains the authority-boundary frame. Gate B1 is adjacent to Gate B — not an amendment that
begins implementation.** The inventoried hazards H1–H6 retain their Gate B classifications unchanged.
This is a **non-implementing selection**, **selected for tractability, not severity**.

## 2. Scope

In scope: record that, among the canon-asserting authority-bearing hazards named in the Gate B decision
frame (H1 and H3), **H3 is selected as the first reconciliation subject** — **selected for tractability,
not severity** — and record why, what stays parked, and what a future separately authorized decision
could (but does not here) take up.

Out of scope: every remedy and every mechanism. This artifact does not change the `/promote` endpoint,
does not touch the `force` field, selects no governance vehicle, designs no crossing, and authorizes no
code, tests, or behavior change. The full non-authorization list is §8.

## 3. Decision — H3 selected as first Gate B1 reconciliation subject

**Selected first reconciliation subject:** H3 — the `POST /promote` force path that asserts an
authority-bearing claim.

Grounded source facts (carried from the Gate B hazard inventory §3 H3; no new inspection performed):

- Source: `app.py::promote_chunk_endpoint` (`@app.post("/promote")`) → `promotion.py::promote_chunk`.
- `PromoteReq.force` defaults `False`. With `force=True`, the handler passes `is_canon=True` and
  `user_approved=True` into `evaluate_promotion` and additionally proceeds under the
  `if result.promote or req.force:` guard, so promotion proceeds regardless of the evaluator's decision.
- Write: a core memory `mtype="identity"`, `canon=True` (`extra_payload kind="canon_promotion"`).
- Reachability: **endpoint-driven; not ordinary-ingest reachable; not automatic.**

This selection records H3 as a **bounded authority question**: a caller-supplied flag can assert a
canon, identity-class claim while the endpoint's evaluation step is bypassed. Naming it as the first
subject states only that this is the question Gate B1 would examine first — under a **future separately
authorized decision**, not here.

## 4. Why H3 first — boundedness and legibility, not severity

H3 is selected because it is the most **tractable** subject to reason about first. It is a **first
reconciliation subject, not a first writer change**, and the ordering reflects legibility:

- **Bounded.** It is reached only through one endpoint (`POST /promote`); it is not part of the
  ordinary-ingest fan-out.
- **Endpoint-driven and explicit.** It is triggered by an explicit HTTP request, not by an automatic
  internal process.
- **Caller-flag-scoped.** The authority-bearing crossing is gated on one named request field (`force`),
  which makes the crossing legible at a single, well-localized site.
- **Legible.** The source path and the asserted claim (`canon=True`, `mtype="identity"`) trace to a
  small, named set of anchors.

These are **tractability** properties — they make H3 a clean *first* object of study. They are
explicitly **not** a claim that H3 is higher severity, higher priority, more urgent, or in any way
addressed. The ordering here reflects where reasoning is most tractable to begin, not a severity
ranking.

## 5. Why H1 is not selected here — and why that is not a de-risking claim

H1 (`gravity_correction` automatic `canon=True`) is **not** selected as the first subject, and that
non-selection carries **no** claim that H1 is lower-risk, parked-because-safe, or de-risked.

The strongest H1-first argument stands on the record and is acknowledged here without minimization:
**H1 is the sharper automatic-authority hazard** — `gravity_correction` is **automatic**,
**drift-gated**, **ordinary-ingest reachable under its gates**, and writes **`canon=True`** into
core-identity memory with no writer-authority check. On the automatic-versus-autonomous doctrinal edge,
an automatic canon-asserting writer is the more pointed authority concern.

H1 is not selected first **only because it is more entangled** — it sits within the drift / centroid /
`mood_drift` topology, while the H5 Phase-8 relationship remains separately parked/unverified, and H1 is
routed in Document A §11 to a dedicated
audit-first reconciliation slice. Choosing H3 first is a choice about **tractability of where to begin**,
**not** a comparative safety judgment and **not** a statement that H3 matters more. H1 remains a parked
non-conformance and a standing future reconciliation subject; nothing here lowers its standing or
implies it is handled.

## 6. H2 / H4 / H5 / H6 boundaries

- **H2** (`_maybe_emit_identity_anchor`) remains **outside the canon-asserting group**: it is a
  `canon=False`, derived, identity-family writer — an **identity-family conformance question**, not a
  canon crossing. It is neither selected nor grouped with H1/H3 here.
- **H4** (`mood_drift → centroid` input-reachability into `measure_drift`) remains
  **characterization/parked** — topology only, no causal or magnitude claim.
- **H5** (Phase-8 `FabricHandle` gravity route) remains **parked behind its unverified binding**. The
  Gate B evidence pass found no production `torment_service` binding (`AgentRunner` is constructed only
  in `tests/` and `examples/`); no live route is asserted.
- **H6** (ordinary-ingest fan-out eligibility envelope) remains **characterization/parked** —
  eligibility under existing gates, not guaranteed fan-out.

None of H2/H4/H5/H6 is selected, opened, or reclassified by this artifact.

## 7. What this selection may unblock later — only by separate authorization

This selection, on its own, unblocks nothing executable. It names the subject a **future separately
authorized decision** could take up first. Should such authorization be granted later, the eligible next
step would be a **separate, target-specific design** for H3 — and only then, under its own
authorization, any bounded work. The shape of any such later work (for example, whether an H3
authority-bearing claim should be made visible, provenance-bearing, and contestable in the
requirement sense defined by the Gate B decision frame) is **not designed, selected, or implied here**.

Governance-vehicle selection — **including whether Cluster 2 v0.2 (Authority Gate) is the write-side
vehicle** — remains **deferred**. No vehicle is named for H3 or for any subject. **Any later H3 code
slice would require a separate target-specific design and a separate authorization**; this artifact
grants neither.

## 8. Explicit non-authorizations

This artifact does **not** authorize, and does not perform, any of:

- No implementation. No code. No tests.
- No writer change. No `/promote` endpoint behavior change. **No disabling or changing the `force`
  field.** No promote-path redesign.
- No authorization-policy change. No canon-semantics change.
- No governance-vehicle selection (including Cluster 2 v0.2). No registry amendment unless separately
  authorized.
- No H1 / `gravity_correction` work. No Phase-7 write emissions.
- No database / substrate. No schema / storage / carriers / migration. No `canon_source` /
  source-sameness mechanics. No P4 implementation.
- No Seed-Governance mechanics. No Document B runtime. No dream / incubation runtime. No candidate
  store. No durable private state.
- No hidden finalizer, output blocker, identity pinning, monitoring or autonomy layer, or durable
  user-risk scoring.

Guidance, not coercion: this artifact introduces no coercive or hidden mechanism. It makes a subject
**answerable** for a later governed decision and nothing more.

## 9. Codex / operator review note

This is a **draft** selection artifact. It is routed to **Codex challenge and operator review** before
it is treated as ratified, and before any subsequent H3-specific design or authorization is drafted.
Selection at this layer is authority-relevant — it names the first subject for a real canon/identity
writer question — so it follows the established Gate B practice of an independent adversarial pass plus
operator ratification before promotion. Do not auto-open any H3 design. A first H3 design, a
governance-vehicle determination, or any mechanism is a separate, later, explicitly authorized step.

---

## Anti-drift footer

NON-IMPLEMENTING SELECTION — no code, no tests, no writer change, no promote redesign, no behavior
change, no endpoint change, no disabling or changing of `force`, no authorization-policy change, no
canon-semantics change, no governance vehicle, no registry amendment, no H1 / `gravity_correction` work,
no Phase-7 write emissions, no database / substrate, no schema / storage / carriers / migration, no
`canon_source` / source-sameness, no P4 mechanics, no Seed-Gov mechanics, no Document B runtime, no
dream / incubation runtime, no candidate store, no durable private state. H3 is the **first
reconciliation subject**, **selected for tractability, not severity**; non-selection of H1 is **not** a
de-risking claim, and H1's sharper automatic-authority concern stands on the record. H2 remains a
`canon=False` identity-family conformance question, outside the canon-asserting group; H4/H5/H6 remain
characterization/parked. Naming a subject opens nothing. Audit observes authority and does not become
authority. Memory may shape context. Memory may not seize authority. Any subsequent Gate B / Gate B1
decision remains a separate authorization.
