# Reinforce Contract Implementation Plan (v2.4.x)

**Status:** RATIFIED 2026-04-15 — all seven plan decisions closed. Framing and plan are both complete. Next step: single PR per §9.3. Contract-invariant test in §7 is the landing gate.

**Filed:** 2026-04-15
**Predecessor:** `docs/REINFORCE_CONTRACT_FRAMING_v2.4.x.md` (RATIFIED 2026-04-15, all six decisions closed)
**Companion:** `docs/ISSUE_reinforce_contract_gap.md` (observation record)
**Pattern reference:** Step 6 implementation plan (same draft → ratify → code discipline)

---

## 1. Context and contract recap

The ratified reinforce contract establishes:

- **Mutation semantics (Framing Decision 3).** Earned significance lives with the memory on the memory row. Observed content is immutable after ingest; per-memory reinforcement state may evolve.
- **Envelope wording (Framing Decision 5).** `result_code` is strictly `"reinforced"` (at least one eid moved) or `"no_op"` (admitted, nothing moved). No `mutations` block. No other values.
- **Observability (Framing Decision 6).** `result_code` is authoritative; callers may trust the envelope without reading downstream state. Machine-enforced by a contract-invariant test.
- **Asymmetry (Framing Decision 4).** Reinforce is a per-memory evidence signal distinct from feedback's overlay/outcome signal. Docs must state this explicitly.

This plan translates the contract into a concrete implementation — field shape, mutation rules, retrieval integration, envelope logic, test, and docs. It does not revisit framing decisions. If any proposed implementation choice here conflicts with a framing decision, the framing decision wins and this document is wrong.

**Delivery shape (pre-approved 2026-04-15):** single PR, no A/B split. Reinforce is smaller and tighter than step 6; the contract invariant requires writer, retrieval consumption, envelope update, test, and docs to land together as one coherent close.

**User preference carried into every section:** conservative, bounded retrieval effect from day one. Reinforcement should help earned memories surface more readily; it must not bulldoze semantic relevance over time.

---

## 2. Field shape on the memory row

### 2.1 Position — RATIFIED 2026-04-15 (Plan-D1)

**Rename `last_reinforced` to `reinforcement_count`.** Type: integer, default `0`, monotonic non-decreasing. No structured trace in this pass.

**Why rename:** `last_reinforced` reads as a timestamp. It has already misled downstream observers into thinking it means "last touched" — this is exactly the freshness-bump confusion that §3 of the framing explicitly rejects. Keeping the name locks the misinterpretation into the doctrine.

**Why `reinforcement_count`:** it names what the field *is* (a count of reinforcement events), not what the field is *for* (which is a retrieval-ranking question that lives in §4 of this plan). Narrow, honest, and type-faithful.

**Why integer counter instead of a structured trace:** simpler. A trace (e.g., list of reinforcement timestamps) would add per-memory storage and unlock features that are explicitly out of scope (temporal analysis, decay-of-signal, dashboards). Starting with a counter is the minimum sufficient representation. A trace can be added later as a bounded extension if a concrete need emerges.

**Migration:** existing memory rows with `last_reinforced` (currently stuck at `0` for all memories, per the 2026-04-14 observation) are migrated by renaming the column and preserving the value. Since all existing values are `0`, no data transformation is needed — this is a pure rename.

### 2.2 Rejected alternatives

- **Keep `last_reinforced` name.** Rejected for the freshness-bump reason above.
- **Name `significance_score` or `significance`.** Rejected as too broad — "significance" implies a general concept that reinforcement is only one input to. If a broader significance model is ever built, it should be a separate field that consumes `reinforcement_count` among other inputs.
- **Structured trace (list of event records).** Rejected as out-of-scope speculation. Re-evaluate only if decay-of-signal (§5) is later ratified and requires per-event metadata.

---

## 3. Mutation rules

### 3.1 Which eids move — RATIFIED 2026-04-15 (Plan-D2)

Only eids present in the call's `used_successfully` list move state. Eids present in `memory_ids` but absent from `used_successfully` are considered "retrieved but not specifically reinforced" and do not move. Retrieved is not the same thing as earned reinforcement.

**Reasoning:** this matches the framing §4 reading of reinforce as a per-memory evidence signal. The full `memory_ids` list is what the caller considered; `used_successfully` is what specifically earned reinforcement. Collapsing the two would reinstate the "reinforce = reward everything retrieved" reading the framing already rejected.

### 3.2 Per-eid mutation

For each eid in `used_successfully`:

- If the eid exists in the caller's workspace, is a private-scope memory, and is writable under current governance: `reinforcement_count += 1`. One increment per call, regardless of how many times the eid appears in `used_successfully` (duplicates in the request are deduplicated first).
- If the eid does not exist, is outside the caller's workspace, is a shared/collective-scope memory (out of scope per Plan-D7), or is blocked by governance: no movement; eid is recorded in the governance log with a specific reason code ("reinforcement-skipped: not-found", "scope-not-supported", "governance-blocked", etc.) and is operator-visible through existing diagnostic surfaces and normal log inspection. The envelope does not expose this per-eid.

### 3.3 Condition for `result_code: "reinforced"` — RATIFIED 2026-04-15 (Plan-D5)

If **at least one eid** in `used_successfully` was successfully reinforced (existed in the caller's workspace, passed governance, counter incremented), `result_code` is `"reinforced"`. Otherwise `"no_op"`. No hidden all-or-nothing interpretation; the envelope says whether some real reinforcement happened, not whether the request was perfect.

**Reasoning:** the strictest possible no-op guard. A call that moved anything moved something, and the envelope should reflect that. Raising the bar to "all eids moved" would create a class of call that looks more successful than it is (mixed success returning `"no_op"` when some state did move), which is the same trust hazard the framing closed on the other side.

### 3.4 Governance event emission

Every reinforce call — including `"no_op"` outcomes — emits a governance event with the call's eids, the subset that moved, and the reason codes for any that didn't. This is independent of the envelope contract; it is the audit trail. Operators who want per-eid detail read the governance log, not the envelope.

---

## 4. Retrieval ranking integration

### 4.1 Position — RATIFIED 2026-04-15 (Plan-D3), with coefficient amendment

**Ratified stance:**

> *`reinforcement_count` influences ranking through a conservative, additive, log-scaled boost applied at rank stage only. The coefficient is env-configurable via `TORMENT_REINFORCE_BOOST` and must be selected by sanity-check against the observed semantic-score distribution so that early reinforcement helps ordering without overwhelming semantic relevance.*

Formula shape:

```
final_score = semantic_score + (TORMENT_REINFORCE_BOOST * ln(1 + reinforcement_count))
```

**Coefficient policy:**

- Env-configurable via `TORMENT_REINFORCE_BOOST`.
- Default must be selected at implementation time via sanity-check against the observed semantic-score distribution in a representative test workspace.
- Target effect: a single reinforcement should add roughly **3–5% of a typical semantic score**. This is the ratified tuning band.
- Reinforcement must never bulldoze semantic relevance, now or under accumulation.

**Not ratified:** any specific numerical default. The plan does not pin `0.05` or any other value as doctrine. A working reference point during implementation may be ~0.05 if it matches the 3–5% target band for the observed score distribution, but the final number is selected by sanity-check at commit time. Locking a specific number in this doctrine would harden a tuning guess into contract; the amendment above prevents that.

### 4.2 Why log scaling

- **Bounded dominance by construction.** At any coefficient within the target band, going from 0 → 1 reinforcements contributes a meaningful step; going from 100 → 101 contributes a small fraction of that step. A memory that was useful once earns most of its boost immediately; further reinforcement has diminishing returns. This naturally prevents ancient heavily-reinforced memories from dominating semantic score.
- **No magic hard cap.** A linear formula with a cap would require picking the cap number, which is exactly the kind of implicit tuning the framing cautions against. Log scaling lets the coefficient alone govern the effect.
- **Matches the anchor sentence.** "Earned its place" is a qualitative signal, not a linearly accumulating one. The fiftieth reinforcement should mean qualitatively the same thing as the first — "this memory keeps being useful" — not fifty times as much.

### 4.3 Integration point

The boost is applied at the final ranking stage in the retrieval path, **after** the lane-separated recall (the 2026-04-12 lane foundation) has returned candidates with semantic scores. Reinforcement does not influence which candidates enter the ranking pool; it only influences how they are ordered within the pool.

**Why not earlier:** pulling reinforcement into the recall stage (e.g., biasing candidate selection) would widen the reinforcement effect beyond ranking and risk pushing unrelated but heavily-reinforced memories into results they should not reach. Keeping it at the ranking stage enforces the framing's "retrieval surface / significance contract" scope.

### 4.4 Kernel, decay, and overlay all untouched

- Kernel bands, tangent_align, coh_phase, S_mag, id_label, in_corridor: **untouched.**
- Memory half-life, decay_scale, compression routing: **untouched.**
- Overlay values (`decay_scale`, `motif_sensitivity`, `promotion_bias`, `reinforcement_gain`, `write_threshold`): **untouched.**

Reinforcement affects retrieval ranking only. Confirmed against framing §3 (What reinforce is NOT).

### 4.5 Rejected alternatives

- **Tie-breaker only.** Rejected as too weak. If two memories score within rounding distance, the reinforcement one wins — but the signal contributes nothing in normal ranking. This fails the anchor sentence's "earned its place" register.
- **Multiplicative boost.** Rejected as too strong. `final_score = semantic_score * (1 + k * count)` compounds with semantic score, which means high-relevance reinforced memories get amplified beyond what their semantic relevance justifies. Violates the "not a weighted duplicate" clause.
- **Linear additive without log.** Rejected because unbounded linear growth means a memory reinforced 1000 times will dominate all semantic ranking. A hard cap could fix this but introduces magic numbers. Log scaling is the natural fix.

---

## 5. Decay of the signal

### 5.1 Position — RATIFIED 2026-04-15 (Plan-D4)

**Monotonic for this pass.** `reinforcement_count` only increases. No time-based decay of accumulated reinforcement, no EMA, no windowing. Revisit only if live evidence shows reinforced memories drifting into unhealthy long-term ranking dominance.

**Doctrinal register:** this is an explicit commitment to *"significance, once earned, is kept"* — a real doctrinal stance for this pass, not an absence of decision. The alternative register ("significance must be continually re-earned") is a defensible future direction but is not what this plan picks.

### 5.2 Reasoning

- **Simpler.** No new time-based machinery. No extra parameter. No background process touching memory rows.
- **Log scaling already dampens dominance.** §4.2 shows later reinforcements contribute a fraction of earlier ones. Ancient reinforced memories do not run away linearly.
- **Decay adds its own failure modes.** If reinforcement decays, then "earned its place" becomes a past-tense statement with an expiration date, which changes the doctrinal register in ways this plan should not pre-commit to. The framing did not make this decision; smuggling it into implementation would reintroduce the exact drift Decision 6 was designed to prevent.
- **Future decision is cheap.** Monotonic-now does not foreclose decay-later. If evidence emerges, a future decision can add time-weighting or windowing as an explicit contract revisit.

### 5.3 What "revisit deliberately" means

This is listed as a concrete ratification target (Plan-D4 below), not an implementation default. The plan is explicit that monotonic-now is a chosen stance, not an absence of decision.

### 5.4 Out of scope

- Periodic decay sweeps.
- Time-weighted counters (e.g., EMA of reinforcement events).
- Windowed counts (e.g., "reinforcement in last N days").

All three are legitimate future directions but are not part of this implementation pass.

---

## 6. Envelope surface

### 6.1 `result_code` computation

```
if any eid in used_successfully was successfully reinforced:
    result_code = "reinforced"
else:
    result_code = "no_op"
```

No other values. No reserved slots. Exactly as ratified in Framing Decision 5.

### 6.2 No `mutations` block

The envelope does not include a per-eid `mutations` block. Callers who need per-eid detail consult the governance log (§3.4). The envelope remains the minimum sufficient surface to close the contract.

### 6.3 Audit block unchanged

All existing audit fields (`task_id` with `spine_` prefix, `decision_code`, `drift_status`, `elapsed_ms`, `escalation_reasons`, etc.) remain as they are today. Reinforce does not introduce new envelope fields.

### 6.4 Envelope wording check

Across all reinforce call sites, `result_code` returns one of exactly `{"reinforced", "no_op"}`. This is pinned by the contract-invariant test in §7.

---

## 7. Contract-invariant test

### 7.1 Test location and name

- File: `tests/test_reinforce_contract_invariant.py` (new file)
- Canonical test: `test_reinforce_envelope_reflects_mutation_invariant`

### 7.2 Assertion shape — both directions

The test runs each case end-to-end against a fresh test workspace with known seeded memories, then asserts the bidirectional invariant:

**Forward direction:** if the envelope returns `result_code: "reinforced"`, read each eid in the request's `used_successfully` list and assert that at least one has `reinforcement_count` strictly greater than its pre-call value.

**Reverse direction:** if the envelope returns `result_code: "no_op"`, read each eid in the request's `used_successfully` list and assert that none have a `reinforcement_count` strictly greater than its pre-call value.

Both assertions must hold on every test case. Failure of either is a contract break.

### 7.3 Required test cases

At minimum:

1. Single eid, exists in workspace, in `used_successfully` → expect `"reinforced"`, counter +1.
2. Single eid, missing from workspace, in `used_successfully` → expect `"no_op"`, no counter moves.
3. Multiple eids, all in `used_successfully`, all exist → expect `"reinforced"`, all counters +1.
4. Multiple eids, mixed (some exist, some missing), all in `used_successfully` → expect `"reinforced"` (at least one moved), verify only existing eids incremented.
5. Eids in `memory_ids` but not in `used_successfully` → expect `"no_op"` on those eids (counter unchanged), regardless of `result_code`.
6. Empty `used_successfully` list → expect `"no_op"`.
7. Duplicate eids in `used_successfully` → expect single increment per eid (deduplication).
8. Workspace-scoped: eid in a different workspace from caller → expect `"no_op"` for that eid.

### 7.4 Invariant enforcement

If this test fails, the contract trio is broken. The failure must be resolved by re-ratifying the trio (mutation semantics + envelope wording + observability), not by silencing the test or loosening its assertions. This is the machine-enforced floor from Framing Decision 6.

### 7.5 Overlay non-movement check

Separate from the contract invariant, one additional test should confirm reinforce does not move overlay values. Proposed name: `test_reinforce_does_not_move_overlay`. This pins the asymmetry from Decision 4 at the test layer.

---

## 8. Docs deliverables (binding, per Framing Decision 4)

### 8.1 Required updates

- **`docs/MCP_CAPABILITY_BOUNDARY.md`** — expand reinforce and feedback rows to explicitly state the asymmetry: feedback = operator/outcome signal targeting the global overlay; reinforce = per-memory evidence signal targeting per-memory reinforcement state. Include the anchor sentence from the framing.
- **`docs/SPINE_CONTRACT.md`** — update the result-code table for reinforce to show exactly the two values `"reinforced"` and `"no_op"` with their mutation guarantees. Remove any wording that implies reinforce is admission-only.
- **`README.md`** — "What's new" entry for the release that ships this. Short, factual: reinforce now mutates per-memory state and the envelope reflects that truthfully.

### 8.2 Optional but recommended

- A dedicated short doc, `docs/REINFORCE_AND_FEEDBACK_CONTRACT.md`, that carries the asymmetry explanation in one place for future readers. Not strictly required by Framing Decision 4 (it allows the distinction to live across multiple docs), but strongly preferred for preventing re-drift.

### 8.3 Diagrams

An asymmetry table in MCP_CAPABILITY_BOUNDARY or the dedicated doc, showing rows `signal type`, `target`, `what the envelope guarantees`, `what it does not touch`, for feedback and reinforce side by side.

### 8.4 Release note

The release containing this implementation must name the contract close in the changelog, not just list the field rename. Example: *"reinforce: per-memory state now mutates on successful reinforcement; envelope result_code is authoritative (2026-04-15 contract ratification)."*

---

## 9. A/B split decision

### 9.1 Position — ratified 2026-04-15

**Single PR, no A/B split.**

### 9.2 Reasoning

- Contract invariant (§7) requires writer + retrieval consumption + envelope + test + docs together. Splitting breaks the invariant's testability.
- Scope is smaller than step 5 / step 6. No migration classifier, no governance gate flip, no multi-table writer.
- Risk of re-introducing drift during an A/B seam (between "writer landed, retrieval not yet consuming" or "envelope updated, state not yet moving") is the exact class of hazard the framing closed.
- Net change is additive: a new field on the memory row, a new term in ranking, a new result_code value, an invariant test, and doc updates. Each is small; together they are still small.

### 9.3 PR discipline

Single PR must include:

1. Column rename and field addition.
2. Writer logic with governance event.
3. Retrieval ranking integration.
4. Envelope `result_code` computation.
5. `tests/test_reinforce_contract_invariant.py` with all §7.3 cases.
6. `test_reinforce_does_not_move_overlay`.
7. All §8.1 required doc updates.
8. README "What's new" entry.

---

## 10. Out of scope for this plan

Explicit, parallel to framing §3 and §8:

1. Motif-level reinforcement. Remains a future question.
2. Decay of the signal itself (periodic, time-weighted, windowed). If Plan-D4 closes as "monotonic for now," this is future work.
3. Structured reinforcement trace (per-event records). Future work only if decay requires per-event metadata.
4. Dashboards or telemetry surfacing reinforcement counts. Future work.
5. Reinforcement for shared or collective memories. Private scope only for this pass. See Plan-D7.
6. Partial `result_code` values. Closed by Framing Decision 5.
7. Per-eid envelope granularity (`mutations` block or equivalent). Closed by Framing Decision 5.
8. Reinforcement during cognition pipeline (Interpreter/Skeptic/Archivist). Reinforce is an MCP-surface operation; internal role outputs do not self-reinforce.
9. Kernel or identity-state coupling. Closed by Framing §3.
10. Any change to `torment_feedback` behavior. Decision 4 requires docs alignment only, not code changes on feedback.

---

## 11. Ratification walk

Ratify these in order. Do not skip ahead. Do not collapse decisions. Do not write code until Plan-D7 closes.

**Plan-D1 — Field name and type. RATIFIED 2026-04-15.** Rename `last_reinforced` → `reinforcement_count`, integer, default 0, monotonic non-decreasing. Keeping `last_reinforced` and structured trace both closed for this pass.

**Plan-D2 — Which eids mutate. RATIFIED 2026-04-15.** Only eids in `used_successfully` move state; eids in `memory_ids` outside `used_successfully` are not reinforced. Deduplicate within the call; one increment per eid per call; missing/out-of-scope eids do not move state.

**Plan-D3 — Retrieval integration shape and magnitude. RATIFIED 2026-04-15 (coefficient amended).** Additive bounded boost via `semantic_score + TORMENT_REINFORCE_BOOST * ln(1 + reinforcement_count)`, env-configurable. Applied at final ranking stage, after lane-separated recall. Coefficient selected at implementation time via sanity-check against the observed semantic-score distribution; target band: a single reinforcement adds roughly 3–5% of a typical semantic score. No specific numerical default pinned in doctrine — the plan ratifies the process and target band, not the number. Tie-breaker-only, multiplicative, and unbounded linear all closed.

**Plan-D4 — Decay of the signal. RATIFIED 2026-04-15.** Monotonic counter for this pass. No time-based decay, no EMA, no windowing. Explicit doctrinal stance: *"significance, once earned, is kept."* Revisit only on observed long-term ranking-dominance drift.

**Plan-D5 — `"reinforced"` threshold. RATIFIED 2026-04-15.** At least one eid in `used_successfully` successfully reinforced → `"reinforced"`. Otherwise `"no_op"`. No implicit partial or all-or-nothing third state. Per-eid detail lives in the governance log, not the envelope.

**Plan-D6 — A/B split vs single PR. PRE-APPROVED 2026-04-15.** Single PR. No split. PR must contain all items in §9.3.

**Plan-D7 — Scope of reinforce for shared/collective memories. RATIFIED 2026-04-15 (with operator-visibility amendment).** Private-scope memories only for this implementation pass. Shared/collective eids are governed skips, not errors. Skipped eids do not contribute to `result_code`; if all candidate eids are out of scope, the envelope returns `"no_op"`. **Scope-skip reasons must be recorded in the governance log with a specific reason code and must be operator-visible through existing diagnostic surfaces or normal log inspection**, even though they are not surfaced per-eid in the reinforce envelope. The envelope stays clean; the reason stays discoverable in a standard debugging path. Shared/collective reinforcement as a first-class feature is future work with its own framing pass.

---

## Plan ratification complete

All seven plan decisions closed as of 2026-04-15. The reinforce contract implementation is now fully specified: framing ratified 2026-04-15, plan ratified 2026-04-15. Next step is the single PR described in §9.3. The contract-invariant test in §7 is the landing gate — if it passes, the trio is holding.

---

## 12. Re-entry reference

If this plan is paused or picked up later, the load-bearing pieces to re-read in order:

1. Framing doc §2 anchor sentence.
2. This plan's §1 contract recap.
3. This plan's §4 retrieval integration (the most tuning-sensitive section).
4. This plan's §11 ratification walk.

Do not restart the planning discussion. Do not write code before Plan-D7 closes.
