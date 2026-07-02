# TORMENT — Gate B Writer-Authority Readiness Scan v0.1

**Status:** DOCS-ONLY readiness scan. **Non-authorizing.** Records that Gate B writer-authority
characterization is currently **saturated at the safe producer-independent / read-only layer**, and that
the remaining writer-authority hazards are **blocked pending separately-authorized governance decisions**
and later carrier / admission / substrate work. Selects no mechanic, opens no gate, authorizes no code or
test, changes no writer behavior, and names no durable field / schema / carrier. Navigation / decision
aid only.

**Authority note:** the Gate B hazard inventory, decision frame, read-only characterization evidence
frame, the candidate-containment writer-authority contract, the matched P2.5-writer / P4-reader
reconciliation, Document A/B, the Ledger Observational-Boundary, and `PROJECT_ORIENTATION_MAP.md` §0
remain source of truth. This scan reads them; it does not amend or reinterpret them.

**Provenance:** after the P4 source-sameness arc (readiness characterization, O3/O4 guard refresh, policy
frame + Codex correction, `update_payload` canonical-last reader-trace hazard characterization). Gate A
producer-independent wall = HOLD; Dream / Regime-B = HOLD / blocker-dependent. Gate B writer-authority is
the named next distinct blocker.

**Doctrine (carried, exact):**

> Memory may guide context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.

---

## 1. Current §0 interpretation

P4 source-sameness is strongly framed and guarded. Gate A wall work and Dream/Regime-B are HOLD. Gate B
writer-authority is the **write-side complement** to the doctrinal kernel — *memory may guide context;
memory may not seize authority* — governing the integrity of the crossing where an **authority-bearing
write** (a claim of `canon=True`, an identity/seed-class `mtype`, or promotion of content into core
memory) must not be asserted **automatically or unilaterally** without an explicit, separately-authorized
governed crossing. This scan asks whether the next safe motion is a test/helper or a HOLD. It is a HOLD.

*(Bookkeeping: §0's HEAD line names the prior edge; the pushed edge is `bbe90db`. Not corrected here —
this slice edits no §0.)*

## 2. Gate B doctrine inventory (already exists)

- **Hazard inventory** — `TORMENT_GATE_B_WRITER_AUTHORITY_HAZARD_INVENTORY_v0.1.md` (H1–H6, read-only).
- **Decision frame** — `TORMENT_GATE_B_WRITER_AUTHORITY_DECISION_FRAME_v0.1.md` (authority boundary;
  requirement-level definition of "governed writer"; non-binding order-of-consideration; definitional
  only, opens nothing).
- **Read-only characterization evidence frame** — `TORMENT_GATE_B_READ_ONLY_CHARACTERIZATION_EVIDENCE_FRAME_v0.1.md`.
- **Candidate-containment writer-authority contract** — `TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md`.
- **Matched P2.5-writer / P4-reader reconciliation** — `TORMENT_MEMORY_ENGINE_MATCHED_P2_5_WRITER_P4_READER_RECONCILIATION_v0.1.md`.
- **B1 / H3 lane** — `TORMENT_GATE_B1_FIRST_WRITER_AUTHORITY_RECONCILIATION_SUBJECT_SELECTION_H3_v0.1.md`
  (H3 named first subject, *selected for tractability, not severity*), `..._GATE_B1_H3_BOUNDED_WRITER_AUTHORITY_QUESTION_FRAME_v0.1.md`,
  `..._GATE_B1_H3_EVIDENCE_READINESS_NOTE_v0.1.md` (seven evidence categories, satisfied vs not-determined).
- **Checkpoints** — `CHECKPOINT_2026-06_GATE_B1_H3_FORCE_ROUTE_PROVENANCE.md`,
  `CHECKPOINT_2026-06_WRITER_PATH_CHARACTERIZATION_TRIAD.md`.

The doctrine layer is dense and definitional-only; it governs, fixes, and builds nothing.

## 3. Live writer surfaces (today)

- `promotion.promote_chunk` (canon promotion) via `app.py::promote_chunk_endpoint` (`POST /promote`).
- `MemoryGraph.spawn_memory` / `update_payload` / `reinforce` / `flush_node` / `save_node_record`.
- `ReferenceStore.ingest` (`reference_memory.py`).
- `EnvironmentStore.write` (`environment_memory.py`).
- `deep_memory` (deep-store writes).
- fabric auto-writers: gravity / anchors / mood / warmth / role.
- **No `archive_store.py`** — archive is a `memory_class` within the graph, not a separate store.

## 4. Already guarded / characterized surfaces (tests)

Producer-independent writer-authority characterization is broad and green:

- `test_promote_force_bypass_endpoint_wiring.py` — pins H3's `POST /promote` `force=True` shape end to end
  (see §5).
- `test_promote_chunk_authority_guard.py` — rejects a live `NonAuthoritativeDeepHit` before the canon
  write.
- `test_update_governance_authority_guard`, `test_lifecycle_authority_guard`,
  `test_should_emit_packet_authority_guard`, `test_governance_authority_guards`,
  `test_filter_llm_facing_authority_guard` — governance/lifecycle/packet/filter authority guards.
- `test_reinforce_contract_invariant` — reinforce contract invariant.
- `test_writeback_recursion_guard` — writeback recursion guard.
- `test_identity_anchor_writer_path_characterization` — identity-anchor writer path.
- `test_srg_query_breathing_writeback_characterization` — SRG query-breathing writeback.
- Gate A candidate-refusal tests (`test_gate_a_*_candidate_refusal.py`) + the `CandidateShapedValue`
  inertness lock — refuse candidate-shaped values at the write **entry**.

## 5. Evidence-only and parked non-conformances

**Evidence-only / not enforced:** `test_gate_a_seam_c_writer_authority_ao2_characterization.py` (Seam C /
A-O2 writer-authority **evidence only** — routes fixes to Gate B, applies none); the Gate B **H1–H6
inventory** (read-only); the **H3 seven-category evidence-readiness note** (read-only record).

**H3 (`POST /promote` `force=True`) is already characterized end to end** by
`test_promote_force_bypass_endpoint_wiring.py`, which pins:

- the **two-effect force shape** — the handler passes `is_canon=True` **and** `user_approved=True` into
  `evaluate_promotion`;
- the **execution bypass** — the `if result.promote or req.force:` branch proceeds even when the
  evaluator declines (`promote=False`);
- the **`promotion_force_requested` provenance marker** written into the row's `extra_payload`;
- explicitly framed as **characterization of the current path — a parked non-conformance / evidence, NOT
  an endorsed baseline** ("if a later separately-authorized slice adds a governed crossing, these
  assertions are expected to change deliberately — that is the signal, not a surprise").

**H1, H2, H4–H6 remain parked non-conformances.** Their next move is a *separately-authorized governance
decision*, not a test or helper by default. H1 (the other canon-asserting hazard) stays parked and is
**not** de-risked by H3's selection.

## 6. Why no new safe test / helper is selected

- A **new H3 test (option B)** would **duplicate** the existing end-to-end force-bypass characterization
  and, worse, risk **baselining a parked non-conformance** (encoding force-bypass as "correct"), which
  the Gate B decision frame explicitly forbids.
- A **new characterization of H1/H2/H4–H6** would open a *new* hazard lane, not the smallest next slice,
  and carries the same baselining risk.
- An **inert helper / type (option C)** is neither authorized nor necessary: "governed writer" is a
  **requirement-level characterization only**; building any helper would imply writer mechanics and
  pre-empt a governance decision that is explicitly deferred.

The genuinely-next motion is a **governance decision** about a selected hazard's crossing — above the bar
of an autonomous test/helper slice, and requiring explicit operator/trio authorization.

## 7. Blocked-until table

| Item | Blocked until |
|---|---|
| A governed-writer **mechanism / crossing** for any hazard | separately-authorized **governance decision** (vehicle + policy) |
| H3 remedy (governing the `force=True` path) | governance decision for H3 (selected first subject, not opened) |
| H1 and other canon-asserting hazards | governance decision; **H1 stays parked** |
| Durable writer-authority resolution (persisted governed outcome) | **carrier / schema / substrate** (P6) + **Document A admission** crossing |
| Seam C / A-O2 writer fixes | Gate B governance decision (Gate A only inventoried them) |

## 8. Gate B vs adjacent gates (distinctness)

- **Gate A** — candidate **containment at write entry** (refuse a `CandidateShapedValue`); Gate B governs
  *authority-bearing* writes that are otherwise well-formed.
- **P4** — **read / projection / source-sameness** (reader side); Gate B is the **writer** side.
- **Substrate / admission** — **carrier mechanics + Document A governed crossing**; Gate B frames the
  boundary but implements no crossing and selects no carrier.

## 9. Ranked next slices (none opened here)

1. **HOLD** — writer-authority characterization terrain is saturated for now.
2. **Separately-authorized Gate B governance-decision frame** for **one** selected hazard (operator/trio
   authorization required; not a default test/helper).
3. **Codex adversarial review** of this readiness scan if any wording feels too soft.
4. **Later carrier / admission / substrate work** — only when explicitly selected.

## 10. Explicit non-authorizations

No writer-authority policy implementation. No change to ingest / promotion / archive / graph / update /
canon / identity / reinforcement behavior. No tests. No helper / type / mechanism. No candidate admission.
No candidate store / carrier / schema / substrate. No P4 mechanics. No Dream / Regime-B runtime. No Gate D
runtime. No Document B chamber runtime. No Envelope-Audit runtime. No AgentRunner / app / spine / MCP
wiring. No model / provider / API / prompt path. No memory writes / persistence / logging / transcripts.
No output-control / finalizer / refusal / identity / canon behavior. No dynamic-kernel /
`conversation_shock`. Amends no Gate B / Document A / P4 / Ledger / Cluster 2 contract.

## 11. Verdict — NO-OPEN / HOLD

**NO-OPEN.** Gate B writer-authority micro-work is **HOLD**. The producer-independent / read-only
writer-authority characterization terrain is **saturated** — H3 is fully characterized (incl. provenance)
and the broad authority-guard suite is green; every remaining hazard is a parked non-conformance blocked
behind a **separately-authorized governance decision** and, for durable resolution, later
carrier / admission / substrate work. The next motion requires **explicit governance-decision
authorization**, not an automatic test or helper implementation.

*End — Gate B Writer-Authority Readiness Scan v0.1. Docs-only, non-authorizing. Verdict: NO-OPEN. Gate B
writer-authority micro-work HOLD; next motion requires explicit governance-decision authorization.*
