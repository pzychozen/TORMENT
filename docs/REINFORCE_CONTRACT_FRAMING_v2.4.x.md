# Reinforce Contract Framing (v2.4.x)

**Status:** RATIFIED 2026-04-15 — all six decisions closed. Next artifact is a separate implementation plan (`docs/REINFORCE_CONTRACT_IMPLEMENTATION_PLAN_v2.4.x.md`). Do not write code until that plan is ratified.

**Filed:** 2026-04-14
**Companion issue:** `docs/ISSUE_reinforce_contract_gap.md`
**Pattern reference:** `docs/WRITE_MIGRATION_FRAMING_v2.4.x.md` (step 6). This framing follows the same draft → ratify → implementation plan → code discipline.

---

## 1. Context

On 2026-04-14, a live MCP session against `torment_service` (hash embedder, workspace `default`) confirmed that `torment_reinforce` returns a successful governed envelope while producing no observable mutation anywhere. Per-memory `last_reinforced` stays at `0`. Overlay values (`decay_scale`, `motif_sensitivity`, `promotion_bias`, `reinforcement_gain`, `write_threshold`) are unchanged before and after. Identity state and drift overlay are untouched.

The same session confirmed `torment_feedback` does move the overlay — five values shift by `0.002` per call in the reward-seeking direction — but does not move per-memory state either. So the asymmetry is two-sided: reinforce is a no-op everywhere, feedback is a no-op at the per-memory level.

This is not a bug in the usual sense. The Spine envelope is healthy (`ok: true`, `result_code: "reinforced"`, `drift_status: "green"`, full audit block). Everything downstream of the Spine looks like a successful write-path call. The failure mode is not "the code crashed" — it is "the code silently returned success for a write that never happened." That is the class of failure doctrine calls **misleading result wording**, and it is worse than a crash because crashes force investigation.

This framing is therefore a contract pass, not a code pass. The implementation may be correct for one of the candidate contracts and wrong for another. Reading the code first would only reshuffle the ambiguity.

---

## 2. Doctrinal register

Anchor sentence, load-bearing:

> *A reinforced memory is not a weighted duplicate; it is a signal that this memory earned its place in the retrieval surface.*

Unpacked:

- **"Signal that this memory earned its place"** — reinforce is evidence that a specific memory was useful at a specific time. It attaches to the memory as significance, not to the global system as a dial.
- **"Not a weighted duplicate"** — reinforce does not add mass, does not extend life, does not boost the kernel. It changes how the retrieval surface ranks and surfaces a memory that already exists; it does not change what the memory is or how long it lives.
- **"Retrieval surface"** — the effect is scoped to retrieval/ranking, not to decay, not to compression routing, not to promotion thresholds, not to the kernel's band dynamics.

This sentence decides which downstream design choices are load-bearing versus ornamental. Anything that turns reinforce into a freshness bump, a decay slowdown, a promotion shortcut, or a disguised write path is *ornamental at best and doctrine-violating at worst*.

---

## 3. What reinforce is NOT

Explicit out-of-scope list, parallel to step 6's "What step 6 is NOT" section:

1. **Not a write path for new memories.** Reinforce does not ingest. It operates on eids that already exist. `torment_ingest` and `torment_tool_result_ingest` are the canonical write surfaces.
2. **Not a freshness refresh.** Reinforce does not update a "last touched" timestamp that feeds half-life. The whole point of the lifecycle policy is that memories age on their ingest clock, not on their usage clock. Turning reinforce into a freshness bump would silently break retention predictability.
3. **Not a decay-scale override.** Reinforce does not adjust `decay_scale`, `half_life`, or any per-memory aging parameter. Those belong to the lifecycle layer, not the retrieval layer.
4. **Not a kernel boost.** Reinforce does not touch identity state, tangent_align, coh_phase, S_mag, or any kernel band. The kernel is downstream of retrieval, not a reinforce target.
5. **Not a promotion shortcut.** Reinforce does not change `promotion_bias` for the affected memories or move them toward shared/collective scope. Promotion has its own governance path.
6. **Not overlay movement.** Overlay movement belongs to `torment_feedback`. Reinforce and feedback are distinct reward signals at distinct granularities; collapsing them is explicitly rejected (see §4).
7. **Not a way around the archivist writeback gate.** `TORMENT_ARCHIVIST_WRITEBACK=0` stays at 0. Reinforce is not a side channel for writeback.
8. **Not a motif-layer operation.** Reinforce operates on individual eids, not on motifs. Motif-level reinforcement is a separate question that does not block this framing.

---

## 4. Feedback vs reinforce asymmetry

This section carries the observation the whole framing turns on.

Feedback and reinforce are both reward signals from the MCP surface, but they operate at different granularities and should have different contracts:

**`torment_feedback`** takes boolean flags (`useful`, `confirmed`, `contradicted`) and an optional eid list. It is an **operator signal about a whole retrieval** — "this answer was good/bad." The natural target of that signal is the global overlay, because the operator is telling the system "your retrieval tuning worked/didn't work." Per-memory state is not the right target: the operator is not necessarily endorsing each individual memory that contributed; they are endorsing the outcome.

**`torment_reinforce`** takes an eid list and a `used_successfully` subset. It is a **per-memory retrieval-usage signal** — "these specific memories earned their place at this moment." The natural target of that signal is per-memory significance, because the signal is specifically about individual memories that surfaced and were useful.

So the asymmetry is not a bug; it is a feature the doctrine should make explicit:

- Feedback moves overlay. It does not touch per-memory state. This is correct.
- Reinforce should move per-memory significance. It should not touch overlay.

Under that reading, the current `reinforce` behavior — no overlay movement, no per-memory movement — is half-right and half-wrong. The half that is right (no overlay movement) matches the intended asymmetry. The half that is wrong (no per-memory movement) is the contract gap.

This framing rejects the alternative where reinforce and feedback are "the same thing at different granularities." They are different kinds of evidence, and the system benefits from keeping them separate. Feedback says *the retrieval worked*. Reinforce says *this memory was the reason*.

---

## 5. The bound trio

When this framing is ratified, three concerns must be decided together in a single decision, not sequentially. This is the core lesson of the current gap: decoupling them is what created the trust hazard.

### 5.1 Mutation semantics

What state changes, where, and under what signal? Candidates are narrowed in §6 (Q2) to two positions. The decision names a single position and specifies every field that mutates, every field that does not, and every signal that triggers the mutation.

### 5.2 Envelope wording

What is `result_code` allowed to claim, and what additional fields (if any) must accompany it? The current `"reinforced"` is misleading when nothing moves. The decision names the exact allowed values of `result_code` for the reinforce operation and specifies whether a `mutations` block or equivalent is required.

### 5.3 Observability expectations

**Ratified clause (Decision 6, 2026-04-15):**

> *`result_code` on reinforce is authoritative. A successful envelope with `result_code: "reinforced"` is a contractual guarantee that at least one eid in the call moved per-memory significance state. A successful envelope with `result_code: "no_op"` is a contractual guarantee that no eid moved. Callers may trust the envelope without reading downstream state to verify.*

**Machine-enforced floor:** The implementation plan must ship a contract-invariant test that fails if envelope and per-memory state disagree. Candidate name: `test_reinforce_envelope_reflects_mutation_invariant`. The test must assert both directions — `"reinforced"` implies at least one eid moved, `"no_op"` implies no eid moved. If the test fails, the trio is broken and the failure must be resolved by re-ratifying the trio, not by silencing the test.

**Binding consequence:** Any future change to reinforce mutation semantics (§5.1) or envelope wording (§5.2) requires explicit revisit of the other two legs. The three legs cannot drift apart silently. A PR that changes one leg without the other two is rejected at review.

---

## 6. Q1–Q4 positions

Each question is carried forward from the issue doc with a doctrinal position and a confidence register. Positions are proposed starting points for the ratification walk, not binding conclusions.

### Q1. Is per-memory reinforcement a concept that exists?

**Position — RATIFIED 2026-04-15 (Decision 1):** Per-memory reinforcement state is load-bearing. The v2.4.x model requires reinforce to have a per-memory target; whether that target is the current `last_reinforced` field, a renamed field, a single field, or a small structured trace is an implementation question, not a contract question.

**Reasoning:** The doctrinal register requires that reinforce be a signal attached to the memory. That cannot be implemented without per-memory state of some kind. The anchor sentence already commits reinforce to being attached to a memory, not to the system in general; the feedback/reinforce asymmetry in §4 depends on reinforce being a per-memory evidence signal distinct from feedback's overlay-level outcome signal. Rejecting this position would collapse reinforce into either no-op semantics or feedback-like semantics, both of which the framing already rejects.

**What this forecloses:** The "remove the field entirely, reinforce has no per-memory target" reading is rejected. Future decisions are now constrained to **how** per-memory reinforcement is represented, not **whether** it exists.

### Q2. What is `torment_reinforce` supposed to mutate?

**Narrowing — RATIFIED 2026-04-15 (Decision 2):** The four candidate answers in the issue doc reduce to two under the doctrinal register and the now-ratified Decision 1. The rejected trio first:

- **(b) Overlay only** — rejected. Collapses reinforce into feedback at the overlay level. §4 establishes they are distinct reward signals at distinct granularities. Also incompatible with Decision 1 — reinforce must have a per-memory target, so it cannot be overlay-only.
- **(c) Both overlay and per-memory** — rejected. Redundant with feedback at the overlay level and introduces two signal paths for the same kind of evidence. Re-couples what the framing deliberately decoupled.
- **(d) Neither (governance/audit event only)** — rejected. A signal that is never recorded on the memory is not a per-memory signal. Directly contradicts Decision 1.

The surviving pair:

- **(P1) Per-memory state on the memory record.** Reinforce writes a significance counter or trace to the memory row itself. Retrieval ranking reads it as a ranking input (a boost, a tie-breaker, a surface-more-readily signal — exact shape is an implementation question). Half-life is untouched; decay is untouched; the field is **not** a "last touched" timestamp.
- **(P2) Per-memory state in a parallel reinforcement ledger.** Reinforce writes to a separate ledger keyed by eid. The memory row stays immutable after ingest. Retrieval ranking consults the ledger at ranking time (count, recency-weighted count, whatever shape the decision specifies).

**Position — RATIFIED 2026-04-15 (Decision 3): P1, with explicit observation/significance separation.**

The ratified form of P1 carries a precise doctrinal commitment that addresses the strongest part of the P2 argument without paying its operational cost:

> *Earned significance lives with the memory, not beside it. The memory's observed content remains immutable after ingest, but its per-memory reinforcement state may evolve as part of the retrieval surface contract.*

This means:
- **Observation is fixed.** The memory's observed content (text, embedding, ingest-time provenance, source metadata) remains immutable after ingest. Reinforce does not rewrite observation.
- **Significance is local.** Per-memory reinforcement state lives on the memory row itself as a separate concern from observed content. Retrieval reads it at ranking time from the row it is already loading.
- **Overlay remains separate.** Feedback's overlay path is untouched by this decision.
- **Reinforce is still not a new-memory write path.** P1 does not enable ingest via reinforce. Only pre-existing eids are reinforceable.
- **Retrieval remains single-surface.** No parallel ledger. No second read path. No second audit surface.

**Reasoning for not picking P2:** The provenance-style separation P2 offered is intellectually clean, but it introduces too much operational surface for this stage. It is the kind of design adopted when strict row immutability is already a deeply held system law. TORMENT does not have to pay that price yet, and the observation/significance distinction above captures the load-bearing insight without adopting P2's structure.

**What this forecloses:** P2 is closed. The per-memory reinforcement state is on the memory row. Future decisions (Decision 5 on envelope wording, and the implementation plan) now build on this surface.

### Q3. Why does `feedback` move the overlay but `reinforce` doesn't?

**Position — RATIFIED 2026-04-15 (Decision 4):** Because they are distinct reward signals at distinct granularities. Feedback is an operator/outcome signal about a whole retrieval — "the retrieval worked/didn't work" — and its natural target is the global overlay. Reinforce is a per-memory/evidence signal about specific memories — "this specific memory earned its place" — and its natural target is per-memory significance (on the memory row, per Decision 3). The asymmetry is intentional doctrine, not an implementation accident.

**Docs requirement — BINDING:** The implementation plan must ship with updated documentation that states this distinction explicitly. Candidate targets: `docs/MCP_CAPABILITY_BOUNDARY.md`, `docs/SPINE_CONTRACT.md`, and/or a dedicated reinforce/feedback contract note. Docs silence on this distinction is not acceptable — it would reproduce the current trust hazard at the documentation layer. This is a required deliverable of the implementation plan, not optional polish.

**What this forecloses:** The "reinforce and feedback are the same thing at different granularities" reading is closed. The "reinforce is a looser form of feedback" reading is closed. The docs-silence option is closed.

**Intended practical effect:** After this ratification, nobody should be able to honestly say "I thought reinforce was just another flavor of feedback" or "I thought both could move the same knobs."

### Q4. Should the envelope `result_code` be precise about what moved?

**Position — RATIFIED 2026-04-15 (Decision 5):** `result_code` on reinforce must reflect actual per-memory state mutation. The reinforce contract admits exactly two values:

- `"reinforced"` — at least one eid in the call moved per-memory significance state.
- `"no_op"` — the call was admitted (governance passed) but no eid moved. Triggers include (non-exhaustive, implementation plan will enumerate): empty `used_successfully` list, all eids missing from the workspace, or eids found but reinforcement skipped for a policy reason.

A `mutations` block in the envelope is **not required**. The enumerated `result_code` plus the caller's knowledge of which eids they sent is sufficient to distinguish real state movement from no-op.

No other `result_code` values are reserved. A `"partial"` value (some eids moved, some didn't) was considered and deliberately **not** reserved — reserving it now would add conceptual surface without current need. If partial semantics become relevant later, it returns as an explicit future decision with a concrete caller need.

**Reasoning:**
- `"reinforced"` returning when nothing moved is the current trust hazard. An enumerated, truthful `result_code` is the minimal fix.
- A strict two-value close is the narrowest possible envelope contract that closes the gap. Narrower is safer.
- Per-eid granularity in the envelope is deferred as speculative surface until a concrete monitoring or diagnostic need demands it.

**What this forecloses:** Admission-only `result_code` (closed). "Always return reinforced regardless of state" (closed). Mandatory `mutations` block (closed for this contract; may return with evidence). Reserved `"partial"` state (closed; re-opens only on concrete need).

---

## 7. Open decisions for ratification

Ratify these in order. Do not skip ahead. Do not collapse decisions. Do not start an implementation plan until all are ratified.

**Decision 1 — Q1 close. RATIFIED 2026-04-15.** Per-memory reinforcement state is load-bearing. The contract commits reinforce to having a per-memory target; the representation (current field name, rename, one field vs small structured trace) is left to the implementation plan. Forecloses the "no per-memory target" reading.

**Decision 2 — Q2 narrowing close. RATIFIED 2026-04-15.** The four candidate mutation targets narrow to P1 (per-memory state on the memory row) and P2 (per-memory state in a parallel ledger). (b) overlay-only, (c) both, and (d) read-only governance event are all rejected. The live doctrine fork is now exactly: *should earned significance live with the memory itself, or beside it?*

**Decision 3 — Q2 position close. RATIFIED 2026-04-15.** P1 with explicit observation/significance separation: *earned significance lives with the memory, not beside it; the memory's observed content remains immutable after ingest, but its per-memory reinforcement state may evolve as part of the retrieval surface contract.* P2 (parallel ledger) closed. Retrieval remains single-surface.

**Decision 4 — Q3 close. RATIFIED 2026-04-15.** Feedback/reinforce asymmetry is intentional doctrine: feedback = operator/outcome signal → overlay; reinforce = per-memory/evidence signal → per-memory significance. Docs update is a required deliverable of the implementation plan, not optional polish.

**Decision 5 — Q4 close. RATIFIED 2026-04-15.** `result_code` on reinforce must reflect actual per-memory state mutation. Strict two-value vocabulary: `"reinforced"` (at least one eid moved) and `"no_op"` (admitted, nothing moved). No `mutations` block required. No `"partial"` reserved. Narrower is safer.

**Decision 6 — Bound trio close. RATIFIED 2026-04-15.** Decisions 3 and 5 are formally bound together with the observability clause in §5.3 — `result_code` is authoritative, `"reinforced"` guarantees per-memory state moved, `"no_op"` guarantees it did not, callers may trust the envelope without reading downstream state. The implementation plan must ship a contract-invariant test (`test_reinforce_envelope_reflects_mutation_invariant` or equivalent) as the machine-enforced floor. Any future change to any leg of the trio requires explicit revisit of the other two.

**Framing complete.** Next artifact: `docs/REINFORCE_CONTRACT_IMPLEMENTATION_PLAN_v2.4.x.md`, produced under the same discipline as step 6's implementation plan. After that plan is ratified, and only then, code is written under an A/B split if appropriate.

---

## 8. What a reinforce contract close is NOT

Guardrails for the ratification walk and the implementation plan that follows:

1. Not an MCP surface change. Reinforce stays a single governed operation. No new tool. No split into sub-operations. The contract fix is inside the existing envelope.
2. Not a coupling to the archivist writeback gate. Reinforce does not ingest, so `TORMENT_ARCHIVIST_WRITEBACK` remains orthogonal and stays at 0.
3. Not a lifecycle-policy change. Decay, half-life, compression routing, and promotion thresholds are not in scope. Reinforce touches retrieval-surface significance only.
4. Not a motif-layer change. Motif-level reinforcement remains a separate future question. It does not block this contract close.
5. Not a kernel change. No band, no phase, no alignment metric, no stance overlay is touched by reinforce.
6. Not a test-matrix expansion beyond what the contract itself requires. The contract needs coverage for: envelope `result_code` reflects mutation truthfully, per-memory state moves under `used_successfully`, per-memory state does not move for eids outside the hit list, no overlay drift under reinforce, repeated reinforce on the same eid composes sensibly (exact semantics per Decision 3).
7. Not a hash-embedder-dependent outcome. The contract is testable under `hash:384:torment` because the per-memory counter is a local state question. Motif-adjacent observations from the 2026-04-14 session remain parked until `BAAI/bge-small-en-v1.5` (or equivalent) is bound in the test workspace.

---

## 9. Re-entry reference

If this framing is paused or picked up later, the load-bearing pieces to re-read in order are:

1. The anchor sentence in §2.
2. The feedback/reinforce asymmetry framing in §4.
3. The bound trio in §5.
4. The Q2 narrowing in §6 (P1 vs P2 is the contested choice; the rest are well-anchored).
5. The six decisions in §7.

Do not restart the framing discussion. Do not audit code before decisions are ratified. Do not start an implementation plan before Decision 6 closes.

Auto-memory entry (to be written alongside the first ratified decision): `project_reinforce_contract_framing_stance.md` — baton pass note mirroring `project_step6_framing_stance.md`.
