# TORMENT Gate B — Writer-Authority Hazard Inventory v0.1

**DOCS-ONLY READ-ONLY HAZARD INVENTORY — NO TESTS, NO CODE, NO FIXES, NO IMPLEMENTATION.**

This is **Gate B framing only**: a read-only inventory of known writer-authority hazards. It does
**not** authorize writer fixes, behavior changes, tests, registry edits, or any database/substrate
work. It records where the hazards are and how they are reached, and defers every decision and remedy
to a later, separately-authorized Gate B decision artifact.

**Date:** 2026-06-17. **Baseline HEAD = origin/main = `1dc7c6e`** (latest commit
*docs(engine): point orientation map to Gate A closure*). Carries Codex's ACCEPT-WITH-CORRECTIONS on
the inventory.

---

## 1. Anti-drift banner

Inventory only. Naming a hazard here neither opens it nor blesses it. No hazard below is fixed,
normalized, prioritized, or scheduled. Source-level facts are grounded in current code at the baseline
above; reachability is described as *eligibility under existing gates*, not as guaranteed or routine
behavior. Gate A closed only as advisory-boundary characterization + tests-only lock; it did not fix
or bless any write-side hazard. This document extends that characterization to the write side and stops
at characterization.

## 2. Scope

In scope: a read-only map of six known writer-authority hazards (H1–H6) — source site, current trigger
route and gates, what (if anything) is written, how each is reached, and why each is authority-relevant.

Out of scope (see §6 for the full forbidden-openings list): any writer fix, any behavior or canon-
semantics change, any gating logic, any test, any registry edit, and all database/substrate, P4 /
source-sameness, Seed-Gov, Document B, and dream/incubation work.

## 3. Hazard inventory (H1–H6)

### H1 — `gravity_correction` automatic `canon=True`

- **Source.** `character.py::gravity_correction()` (def line 565); invoked from `fabric.py::ingest()`
  at line 3333.
- **Trigger route (grounded).** Reached **through the periodic post-store drift check inside
  `TormentFabric.ingest()`** — *not* on every ingest. The drift check (fabric.py 3289–3341) runs only
  when all of the following current gates hold:
  - character enabled (`_character_enable`),
  - a memory was stored this call (`stored`),
  - positive step (`step > 0`),
  - step divisible by `_character_drift_every` (`step % _character_drift_every == 0`),
  - seed exists (`seed_id` resolvable),
  - seed motif exists (`seed.seed_motif_id`),
  - high-away drift (`drift_score < -drift_correction_threshold` **and** `direction == "away_seed"`).
- **Writes.** Yes — `graph.spawn_memory(mtype="drift_correction", canon=True, …)` (character.py
  600–607), tier `core_identity`, attaches to the seed motif, `flush_node`. Purely additive (it never
  rewrites or deletes existing memories), but it is an automatic **canon-true core-identity write**.
- **Classification.** Automatic; ordinary-ingest reachable **only** when the gates above fire.
- **Authority-relevance.** It creates canon identity-reinforcing memory autonomously from a derived
  drift metric — squarely on the "automatic allowed vs autonomous not authorized" doctrinal edge, and
  on canon (highest-authority) rows.

### H2 — `_maybe_emit_identity_anchor` derived identity-family writer

- **Source.** `fabric.py::_maybe_emit_identity_anchor()` (def line 1382); invoked from `ingest()` at
  line 3271.
- **Framing.** Automatic derived identity-family writer; **`canon=False`**; ordinary-ingest reachable
  **only through gated motif / fan-out conditions**.
- **Trigger route.** Post-store fan-out inside `ingest()`, gated by motif-recurrence heuristics
  (`TORMENT_ID_ANCHOR_MIN_COUNT` / `MIN_GAP_STEPS`, role multipliers, affect-sensitivity tightening):
  emitted when an agent repeatedly contributes to the same motif and the count/gap conditions are met.
- **Writes.** Yes — `g.add_memory(mtype="identity_anchor", canon=False, …)` (1519–1550) with
  provenance `anchor_origin="derived"`, `anchor_source="motif_cluster"`; may retire a prior anchor for
  the same motif via `update_payload` (1558).
- **Authority-relevance.** It writes an identity-typed memory derived from motif statistics with no
  seed-gov or operator input; `identity_anchor` rows receive a dedicated tier (`character.py::classify_tier`
  274–275). It is an identity-family write reached only under its gates.

### H3 — `POST /promote` force bypass

- **Source.** `app.py::promote_chunk_endpoint()` (`@app.post("/promote")`, line 1775) →
  `promotion.py::promote_chunk()` (def line 242).
- **Framing.** **Endpoint-driven; not ordinary-ingest reachable; not automatic.**
- **Trigger route.** HTTP request to `/promote`. `PromoteReq.force` defaults `False`. With `force=True`
  the handler **bypasses the endpoint's promotion decision guard**: it passes `is_canon=True` and
  `user_approved=True` into `evaluate_promotion` (app.py 1831/1835) and additionally executes under the
  `if result.promote or req.force:` guard (1840), so promotion proceeds regardless of the evaluator's
  decision.
- **Writes.** Yes — `promote_chunk` writes a core memory `mtype="identity"`, `canon=True`
  (promotion.py 290–295; `extra_payload kind="canon_promotion"`).
- **Authority-relevance.** A request-supplied flag elevates an archive chunk to canon core-identity
  while bypassing the endpoint's promotion decision guard — caller-driven authority creation without the
  evaluation gate.

### H4 — `mood_drift → centroid → gravity_correction` (topology only)

- **Source chain.** `fabric.py::_maybe_emit_mood_drift()` (def line 1575; emits `mtype="mood_drift"`,
  `canon=False`, 1646–1683) → `character.py::measure_drift()` (def line 399) →
  `character.py::gravity_correction()` (H1 writer).
- **Framing (topology/reachability only).** `mood_drift` rows can enter the recent-memory centroid
  considered by `measure_drift` — `measure_drift` excludes only `seed_canon` rows (character.py
  422–423) and applies a recency filter, so an eligible recent `mood_drift` row with an embedding is
  among the rows that contribute to the centroid. **Topology only; no causal or magnitude claim.** No
  assertion that `mood_drift` causes, materially moves, usually triggers, or is decisive for gravity
  correction.
- **Classification.** A reachability/topology relationship, not a separate writer. The `mood_drift`
  seed has its own affect/state/gap emission gates; any later gravity correction remains separately
  gated by H1's periodic drift-check gates.
- **Authority-relevance.** Records that a derived affect-transition row is *eligible to be among* the
  inputs to the drift measurement that gates H1 — an input-reachability fact only.

### H5 — AgentRunner Phase-8 gravity route (`FabricHandle`)

- **Source.** `agent_loop.py::AgentRunner.run_turn()` Phase 8 (lines 587–600):
  `if drift_info is not None and drift_regime.vetoes_outward_action: self.fabric.gravity_correction(...)`
  (593); `drift_info` from the Phase-5 `self.fabric.measure_drift(...)` (492).
- **Framing.** A Phase-8 `FabricHandle` gravity route. **It becomes a second route to the same gravity
  writer only for `FabricHandle` implementations that bind it to `character.gravity_correction`.** The
  live binding from a production `TormentFabric` to `character.gravity_correction` was **not verified**
  here; in the runtime slice the handle is a protocol seam (tests inject fakes; live wiring is parked).
  Phase-8 behavior is kept **parked**, not characterized as a proven live route.
- **Writes.** Conditional on the bound implementation: if bound to `character.gravity_correction`, the
  same `canon=True` write as H1; otherwise whatever the bound handle does. Not asserted here.
- **Authority-relevance.** Names a second potential door to the gravity writer through the agent loop,
  contingent on the `FabricHandle` binding — recorded so it is not forgotten, not asserted as live.

### H6 — ordinary-ingest fan-out reachability (eligibility)

- **Source.** `fabric.py::ingest()` (def line 2440); the post-store fan-out block (3270–3341) is inside
  `ingest()` (the next method, `query`, begins at line 3882).
- **Framing (eligibility/reachability, not guaranteed fan-out).** Advisory-shaped Phase-7 summaries can
  enter ordinary ingest and then become subject to ordinary ingest's existing writer hazards if storage
  and the downstream gates fire. The surfaces are separately gated: H1 by the periodic drift-check
  gates, H2 by motif/anchor gates, and the H4 seed by mood-drift affect/state/gap gates. The fan-out is
  reachable, not automatic on every ingest, and the advisory layer itself is not the writer.
- **Classification.** A reachability envelope linking Gate A's "Phase-7 ordinary-ingest" finding to the
  write-side hazards — eligibility only.
- **Authority-relevance.** Records that content entering via ordinary ingest is *eligible to be subject
  to* the gated writer hazards above; it does not attribute any write to the advisory layer.

## 4. Linkage map

- **Gravity route (H1 / H5).** H1 (ingest-internal drift check, fabric.py 3333) is a grounded route to
  `character.gravity_correction` (canon=True). H5 relates to the gravity route **only with the
  `FabricHandle` caveat**: it is a second route to the same writer *only for handle implementations that
  bind Phase-8 to `character.gravity_correction`* (live binding unverified; parked).
- **H4 — input reachability into `measure_drift`.** Topology-only: `mood_drift` rows are eligible to be
  among the recent-memory centroid inputs that `measure_drift` considers. No causal or magnitude claim,
  and no claim about the gravity outcome.
- **H6 — ordinary-ingest eligibility.** Reachability/eligibility, not guaranteed fan-out: Phase-7
  summaries entering ordinary ingest become *subject to* the gated writer hazards if storage and
  downstream gates fire.
- **H2 vs H3 — identity-family but distinct.** Both touch identity-family memory, by different doors and
  different canon values: H2 is a derived, automatic, `canon=False` identity-anchor writer reached only
  under motif/fan-out gates; H3 is an endpoint-forced `canon=True` identity promotion that bypasses the
  endpoint's promotion decision guard. They are not the same writer and must not be conflated.

## 5. Future Gate B decision targets

The following are named as **future Gate B decision targets** / writer-authority decision subjects —
non-authorizing, no remedy implied, no ordering implied:

- H1 — automatic `canon=True` gravity write: a writer-authority decision subject.
- H2 — derived `canon=False` identity-family writer: a governance-conformance question.
- H3 — `/promote` force path bypassing the endpoint's promotion decision guard: a writer-authority
  decision subject.
- H5 — Phase-8 `FabricHandle` gravity route (binding-contingent; parked): a future decision target,
  pending verification of the live binding.
- H4, H6 — topology/eligibility relationships: future decision targets only insofar as a later artifact
  chooses to characterize magnitude or governance; nothing is decided here.

No target above is opened, ranked, or scheduled. Any decision among them is a separate, later,
explicitly-authorized Gate B decision artifact. The Seed-Gov posture stands: automatic identity / seed /
canon writers are flagged not-yet-conformant and are subjects for later reconciliation, **not** patched
here.

## 6. Out of scope (forbidden openings)

- No database mechanics.
- No schema / storage / carriers / migration.
- No `canon_source`.
- No source-sameness mechanics.
- No P4 implementation.
- No Seed-Gov implementation.
- No Document B runtime.
- No dream/incubation runtime.
- No writer fixes.
- No registry edits.

## 7. Recommended next step

Submit this written checkpoint for **Codex challenge**, and/or **operator review**, before any Gate B
decision artifact is drafted. **Do not auto-open fixes.** A decision artifact (e.g. "which writer to
govern first" or a writer-authority conformance contract) is a separate, later, explicitly-authorized
step — it must not be bundled into this inventory.

---

## Anti-drift footer

INVENTORY ONLY — no implementation, no fixes, no behavior change, no tests, no registry amendment, no
database / schema / storage / carriers / migration, no `canon_source` / source-sameness, no P4, no
Seed-Gov implementation, no Document B runtime, no dream/incubation runtime. Reachability is described
as eligibility under existing gates, never as guaranteed fan-out; topology relationships carry no causal
or magnitude claim; the Phase-8 route is parked behind its `FabricHandle` binding caveat. Naming a
hazard opens nothing. Guide, not control; audit observes authority and does not become authority; memory
may guide context, memory may not seize authority. Any Gate B decision remains a separate authorization.

---

## Appendix A — Read-only evidence pass (2026-06-17, `a72d0ba`)

Read-only characterization evidence under the committed evidence frame
(`docs/TORMENT_GATE_B_READ_ONLY_CHARACTERIZATION_EVIDENCE_FRAME_v0.1.md`). Source/docs inspection only;
no execution. Findings are evidence for later decision-making only — not correctness, incorrectness,
priority, target selection, or authorization to fix.

- **Scope inspected:** current source and these Gate B docs only; **no** operator-identified
  workspaces/artifacts were inspected (none were named).
- **H1 — reachable in current source.** `character.gravity_correction` writes `mtype="drift_correction"`
  with `canon=True` and is called from the `TormentFabric.ingest()` periodic post-store drift check.
- **H1 prior observation / content / frequency:** **not determinable read-only — deferred** (requires
  operator-identified pre-existing artifacts/workspaces).
- **H5 — no production service binding found.** `fabric.py` defines no `gravity_correction` method;
  `AgentRunner` is constructed only in `examples/` and `tests/`, not in `torment_service/`. The
  `FabricHandle → character.gravity_correction` Phase-8 route appears demo/test-injected only, not wired
  through the `torment_service` runtime. (De-risks H5; still not a proven live route.)
- **Anchors:** checked anchors fresh for H1 (`character.py` 565/603/607; `fabric.py` ingest drift block
  ~3289–3341, call ~3333) and H3 (`app.py` 1775/1831/1840; `promotion.py` 242/~295). Unchecked anchors
  were not re-verified in this pass.
- **No** execution, tests, service start, loop, endpoint, ingest, writer path, instrumentation, scenario
  forcing, target selection, or fix recommendation was used or made.
