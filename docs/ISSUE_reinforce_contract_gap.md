# `torment_reinforce` contract gap: return envelope claims success, neither per-memory state nor overlay moves

**Status:** CLOSED — implemented in commit 63f9b2d (2026-04-16). Framing ratified (6 decisions), plan ratified (7 decisions), contract-invariant test green.  
**Severity:** Contract/semantics failure, not a crash. Callers relying on `result_code` to mean anything mutated will be silently misled.  
**Filed:** 2026-04-14  
**Discovered via:** Live MCP session against local `torment_service` (hash embedder, workspace `default`). Observations recorded as eids 5 and 6.  
**Related but distinct from:**
- `lookup_fn` / `ingest_fn` writeback divergence (parked behind `TORMENT_ARCHIVIST_WRITEBACK=0`)
- `drift_check_fn` gap (resolved 2026-04-12 in `ISSUE_spine_drift_check_fn_gap.md`)

---

## The observation

Two back-to-back MCP calls during the 2026-04-14 session:

1. `torment_reinforce([1,2,3,4], used_successfully=[2])` — returned a success envelope. Per-memory `last_reinforced` stayed at `0` for every affected eid. Overlay values (`decay_scale`, `motif_sensitivity`, `promotion_bias`, `reinforcement_gain`, `write_threshold`) were unchanged before/after. Identity state and drift overlay untouched.
2. `torment_feedback([2], useful=true, confirmed=true)` — returned a success envelope. All five overlay values moved by 0.002 in the reward-seeking direction. Per-memory `last_reinforced` on eid 2 still stayed at `0`.

**So the asymmetry is real and two-sided:**

- `reinforce` is a no-op everywhere visible (per-memory AND overlay).
- `feedback` mutates overlay but does NOT touch per-memory reinforcement state either.
- Neither path increments `last_reinforced`. The field exists on every stored memory and never moves under any MCP surface tested.

This is not a transient failure. It is reproducible and currently indistinguishable from a correct response on the envelope alone.

---

## What makes this a contract problem, not just a bug

The governed Spine envelope is healthy. `ok: true`, `drift_status: "green"`, `result_code` populated, `task_id` present, `escalation_reasons: []`, `elapsed_ms` small. Audit block is complete. Everything downstream of the Spine looks like a successful write-path call.

So callers — including Claude in this session — trust the envelope and assume state moved. It didn't. The failure mode is:

- An operator runs a reinforcement sweep expecting decay slowdown on frequently-used memories.
- Every call returns success.
- Forgetting proceeds at the default rate anyway because `last_reinforced` never advances and no overlay term shifts in response.
- There is no signal to the operator that anything is wrong until they read the raw DB and find stale counters.

This is the class of failure the doctrine calls **misleading result wording**. It is worse than a crash, because crashes force investigation.

---

## The contract questions that need ratification

Before any code moves, the doctrine needs to answer these four questions explicitly. Each has a defensible answer; what's not defensible is leaving them implicit.

### Q1. Is per-memory reinforcement a concept that exists?

Does `last_reinforced` on the memory record have semantic meaning in the v2.4.x model, or is it a vestigial field from an earlier iteration? If it has meaning, what is it meant to influence — half-life multiplier, retrieval boost, promotion threshold, nothing?

**If vestigial:** remove the field (or mark it explicitly reserved), and stop shipping it in every query response.  
**If meaningful:** specify which path writes it and on what signal.

### Q2. What is `torment_reinforce` supposed to mutate?

Four candidate answers, all internally consistent:

- **(a)** Per-memory state only — `last_reinforced`, possibly `strength`/`half_life`. Overlay untouched. Governance event emitted.
- **(b)** Overlay only — shifts `reinforcement_gain` etc. based on `used_successfully` hit list. Per-memory state untouched.
- **(c)** Both — overlay as a global learning signal + per-memory counter for retrieval weighting.
- **(d)** Neither — `reinforce` is a governance/audit event, deliberately read-only on state, returning `result_code` only to confirm the call was admitted.

The current behavior matches (d), but `result_code: "reinforced"` contradicts (d)'s read-only semantics.

### Q3. Why does `feedback` move the overlay but `reinforce` doesn't?

Both are reward signals. `feedback` takes `useful` / `confirmed` / `contradicted` booleans; `reinforce` takes `used_successfully` eids. If they have different effects, the doctrine needs to say why — what does `useful=true` mean that `used_successfully=[eid]` does not?

If they're meant to be equivalent, one of them is implemented incorrectly.  
If they're meant to differ (`feedback` = operator signal, `reinforce` = retrieval-usage signal), the docs need that distinction and the envelope wording needs to reflect it.

### Q4. Should the envelope `result_code` be precise about what moved?

Today `result_code: "reinforced"` is returned even when nothing measurable changed. Options:

- Make `result_code` reflect actual state mutations (`"no_op"`, `"overlay_updated"`, `"per_memory_updated"`, `"both"`).
- Keep `result_code` as an admission signal (call was accepted) and add a separate `mutations` block to the envelope listing what actually moved.
- Document that `result_code` is admission-only and callers must read per-memory state to verify.

Option 3 is cheapest but puts the burden on every caller forever.

---

## What NOT to do first

**Do not audit the implementation until the contract is ratified.** The code may be correct for contract (d) and wrong for contract (c). Fixing without a ratified contract will just reshuffle the same ambiguity.

**Do not generalize from the current motif behavior.** The session ran under `hash:384:torment`. Singleton motifs and missed semantic duplicates (eid 5 vs eid 6) are embedder artifacts, not motif-layer bugs. Any conclusion about the motif pipeline needs to be re-run under sentence-transformers with `BAAI/bge-small-en-v1.5` or equivalent before it counts as evidence.

---

## What to keep as durable record from this session

Three things worth preserving regardless of which contract wins ratification:

1. **`feedback` is measurably alive.** Five overlay values moved by 0.002 per call, in the reward-seeking direction. This is the first live confirmation that the adaptive overlay responds to MCP input.
2. **`submit_task` envelope exposes Spine metadata that direct tools hide.** `path`, `decision_code`, `trust_tier`, `client_id`, `session_id`, `task_id` with `spine_` prefix, full `audit` block. If operators want visibility, they should prefer `submit_task` as the entry point.
3. **Role classifier drifts with session behavior.** Explorer climbed from 0.538 → 0.621 over six exploratory writes. Reflector held ~0.20, planner ~0.03. The classifier is windowed over all `samples` (= `memory_count`), not recency-weighted.

---

## Ratification coupling requirement

When Q1–Q4 are ratified, the three concerns below must be decided **together in
a single decision**, not sequentially:

1. **Mutation semantics** — what state changes, where, and under what signal.
2. **Envelope wording** — what `result_code` is allowed to claim, and what
   additional fields (e.g. a `mutations` block) must accompany it.
3. **Observability expectations** — what callers are contractually allowed to
   infer from a successful envelope without reading downstream state.

The current trust hazard is precisely the gap between (1) and (2): envelope
says "reinforced," nothing observable moved. If ratification fixes mutation
semantics but leaves envelope wording decoupled, the same hazard can re-emerge
the next time either side changes independently. Bind the trio and the class of
failure goes away by construction.

Put another way: the envelope is a public API surface with its own contract,
and a mutation decision that doesn't also bind that surface is only half a
ratification.

---

## Recommendation

**Doctrine decision first, then implementation audit.** Open a framing doc for Q1–Q4 with an options-and-trade-offs block per question, and require that each answer include an envelope-wording / observability clause per the coupling requirement above. Ratify the whole trio together. Only then read `torment_service/api.py` or equivalent to determine which of (a)–(d) the code currently implements and what the gap to ratified contract is.

The embedder limitation means any fix that depends on motif behavior should be deferred until sentence-transformers is bound in the test workspace. The `reinforce` contract itself, though, is testable under hash — the per-memory counter is a local state question.
