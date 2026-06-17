# TORMENT Cognition Roadmap Completion and Implementation Sequence v0.1

**READ-ONLY / FRAMING / SEQUENCING ONLY — NO IMPLEMENTATION AUTHORIZED.**

This artifact maps and orders existing commitments. It selects no mechanics, opens no gate,
authorizes no implementation/construction, and names only **candidate gates** (not opened).
"Substrate-independent candidates" may be *considered* before database/substrate work;
"substrate-dependent deferred items" wait for carriers/substrate or separate authorization.
Naming a candidate gate is not permission to build it.

**Date:** 2026-06-17. **Lineage:** Claude read-only roadmap map → Codex adversarial review
(conditional safe-to-file; must-fixes carried) → GPT/Hilmir steering → this filing.

---

## 1. Status and scope

- **HEAD = origin/main = `f309b0a`** ("docs(engine): authorize L2 Stage-B-to-framing decision").
- **L2 Stage-B-to-framing is open only** for this cognition-layer-first framing deliverable:
  dream / cognition / thinking / private-state / seed / guided-memory roadmap completion and
  ratification-to-implementation **sequencing**.
- **No implementation, no mechanics, no construction, no database/schema/storage/carriers/
  migration is authorized by this artifact.** It is read-only framing/sequencing.

## 2. Source map

- **Current authority (ratified requirement contracts):** Document A; Document B; Seed-Governance;
  P4; No-Corner; Stage A; P1/P2/P2.5; Cluster 2 (doctrine-only); Ledger Observational-Boundary;
  MCP Capability Boundary; Track A Truthfulness Envelope; §N7 soft-state postures.
- **Live runtime evidence:** `thinking_controller.py` (ThinkingController→MemoryPlan, deterministic
  routing); TriOcta kernel; current retrieval/drift/promotion paths; stance/role policy; soft-state
  behaviors (ModelState, CorridorMonitor EMA, spirit-return warmth, mood/drift).
- **Historical / scoped / quarantined (non-authoritative unless separately reconciled):** external
  `ROADMAP_13042026.md`; `TORMENT_ROADMAP_NOTES.md` future-storage; `AUDIT_index_and_mcp_resources.md`;
  `docs/archive/SRG_INTEGRATION_SPEC.md`; Block A/B/C designs; Cluster 5 Path C framing;
  Memory-Kernel-Architecture docs.
- **Bridge / substrate-protection:** DB/Substrate Doctrine Reconciliation (N12); council framing/outcome
  (N15/N16); substrate-readiness memo; L2-A closure; Issue #54 checkpoint; L2 decision record.

### Four buckets (kept distinct throughout)
1. **Ratified requirement docs:** Document A, Document B, Seed-Gov, P4, No-Corner, Stage A (+ related current authority).
2. **Live pre-contract runtime:** ThinkingController, stance/role policy, current retrieval/drift/promotion paths, TriOcta / soft-state behavior.
3. **Parked non-conformances:** `gravity_correction` automatic `canon=True`; `_maybe_emit_identity_anchor`; `POST /promote` force bypass; `mood_drift → centroid → gravity_correction → canon=True`.
4. **Not-yet-built conformance:** Document B private cognition; P4 runtime gates; Seed-Gov mechanics; candidate store; durable chamber state; dream/incubation runtime.

## 3. Roadmap completion matrix

| Item | Source | Bucket | Implementation | Authority posture | Next action |
|---|---|---|---|---|---|
| Document A containment / writer-authority | Document A | Ratified requirement | Not built | Current authority | Candidate gate (A/B) |
| Document B private-cognition interior | Document B | Ratified requirement | Not built | Current authority | Defer / candidate gate D (Layer-1 only) |
| Seed-Governance | Seed-Gov | Ratified requirement | Not built | Current authority | Defer (substrate-dependent) |
| No-Corner / guidance-not-control | No-Corner | Ratified requirement | Not an enforcement module | Current authority | No action (honor as invariant) |
| P4 reader/projection safety | P4 | Ratified requirement | Not built (live joins presence-only) | Current authority | Candidate gate C |
| P2.5 memory-lineage carrier | P2.5 | Ratified requirement | Carrier absent | Current authority | Defer (substrate-dependent) |
| P1/P2 era / family identity | P1/P2 | Ratified requirement | Not built as carriers | Current authority | Defer (substrate-dependent) |
| Stage A recovery/reconciliation | Stage A | Ratified requirement | Not built | Current authority | Defer (substrate-dependent) |
| Cluster 2 Authority Gate | Cluster 2 | Ratified requirement (doctrine-only) | Runtime seam (v0.2) unopened | Current authority | Verify as write-side vehicle |
| Ledger Observational-Boundary | Ledger | Ratified requirement | N/A (constraint) | Current authority | Honor |
| Track A Truthfulness Envelope | Track A | Ratified requirement | Partial (voice-audit); Envelope Audit not built | Current authority | Candidate gate D |
| §N7 soft-state postures | §N7 | Ratified requirement (posture) | Live pre-contract behaviors exist | Current authority | Reconcile to posture (candidate) |
| ThinkingController → MemoryPlan | `thinking_controller.py` | Live pre-contract | Built (deterministic routing) | Scoped evidence | Verify; not Document B |
| TriOcta kernel | `memory_kernel.py`/`fabric.py` | Live pre-contract | Built, load-bearing | Scoped evidence | No action |
| `gravity_correction` canon=True | char.py / N14 | Parked non-conformance | Live | Parked | Reconcile (visible target, Gate B) |
| `_maybe_emit_identity_anchor` | fabric.py | Parked non-conformance | Live | Parked | Reconcile (visible target, Gate B) |
| `POST /promote` force bypass | app.py | Parked non-conformance | Live | Parked | Reconcile (visible target, Gate B) |
| mood_drift → centroid → gravity → canon | Lane A / N14 | Parked non-conformance | Live inclusion path | Parked | Reconcile (visible target, Gate B) |
| P3 shell continuity | substrate-readiness §6 | Ratified requirement | Defined, dormant/unwired | Current authority | Park |
| Cluster 5 storage fragilities | Cluster 5 v0.1 / §K | Not-yet-built conformance (inputs) | Not fixed | Current authority (as inputs) | Defer (substrate-dependent) |
| Track B contest ledger | Track B v0.2 | Not-yet-built conformance | Isolated persistence built, no wiring | Current authority | Park (own cycle) |
| Database/substrate mechanics | DB recon / council | Not-yet-built conformance | Not built | Current authority (framing) | Defer (substrate-dependent) |

## 4. Dream / incubation layer
- Document B Regime B (Dream/Incubation) is **requirement-level only**; **no runtime exists** (no dream/incubation modules).
- **Regime B is deferred.** If ever authorized later, the cautious on-ramp is Layer-1 private thinking + Envelope Audit (§5), not dream.
- **Forbidden openings (now):** dream scheduler, offline loop, durable private state, self-trigger, self-budget, reentry into ordinary cognition, autonomy.

## 5. Private cognition / thinking / continued thought layer
- Document B interior (private thinking, continued thought, envelope audit, chamber continuity) is **not implemented**.
- `ThinkingController` is **deterministic / advisory routing and retrieval shaping only** (produces a MemoryPlan). It is **not** a private-cognition chamber, **not** dream/incubation, **not** a candidate store, and must not be conflated with Document B.
- Substrate-independent candidate: ephemeral Layer-1 private thinking + observational Envelope Audit (candidate gate D), only if/when separately authorized, only inside a real Document A wall.

## 6. Private-state / soft-state / mood / drift / spirit-return layer
- **Live pre-contract behavior** (ModelState, CorridorMonitor EMA, spirit-return warmth, mood/drift) exists; the **ratified governance posture** (§N7: durable-soft, resettable, inspectable, never canon/authority) is requirement-level and not yet enforced.
- Soft guidance is **never canon/authority**; recognition ≠ authority.
- The `mood_drift → centroid → gravity_correction → canon=True` path remains a **parked non-conformance** (topology recorded, not endorsed, not filtered).

## 7. Seed / identity / canon layer
- Seed-Governance is a **ratified requirement, not implemented** (no runtime seed writer / governed crossing).
- **Canon-by-source distinguishability is required** (SG-O4); **no `canon_source` field/enum/schema is selected** (deliberately) — a substrate-dependent design obligation.
- Automatic writer hazards (gravity_correction / identity_anchor / promote-force) are **parked**, not encoded as correct.

## 8. Guided-memory / non-control layer
- No-Corner (bounded defensive availability) and the Ledger Observational-Boundary hold: **guidance not control; audit observes authority, does not become authority.**
- Confirmed absent and not introduced: identity pinning, invisible finalizer, output blocker, hidden deletion/refusal rule, durable user-risk scoring, monitoring, notification surface, reputation/penalty ledger.

## 9. Sequencing proposal — NON-AUTHORIZING (candidate gates only, none opened)

These are **candidate gates only, not opened.** Each would require its own separate authorization.

- **Candidate Gate 0 — roadmap filing / ordering only** (this artifact).
- **Candidate Gate A — Document A containment / live-advisory boundary lock** (containment / non-reachability / staging-vs-admission; lock the live-advisory boundary, e.g. ThinkingController, as non-authoritative). *Substrate-independent.*
- **Candidate Gate B — write-side authority framing + visible writer-hazard reconciliation targets** (the gravity_correction / identity_anchor / promote-force / mood→gravity hazards named as explicit, visible first reconciliation targets — never buried). *Substrate-independent. Adjacent to, not merged into, the authority framing.*
- **Candidate Gate C — P4 read-side gate framing** (a separate guardrail before private-cognition output could touch retrieval/projection). *Substrate-independent framing.*
- **Candidate Gate D — Layer-1 private thinking + Envelope Audit, ephemeral only** (no durable state). *Substrate-independent.*
- **Deferred substrate-dependent set:** durable chamber continuity; candidate-store carrier; lineage/revision carriers; source-sameness; canon-source representation; recovery of private state; migration; durable dream/incubation (Regime B). *Wait for carriers/substrate or separate authorization.*

Order intent (sequencing, not permission): **A wall → P4 gates → Document B interior**, with write-side authority + visible writer-hazard reconciliation (Gate B) adjacent to the wall, and Regime B dream deferred.

## 10. Database/substrate protection notes
- This artifact selects **no carrier / schema / source-sameness / `canon_source` / migration mechanics**.
- The **old-doc authority quarantine remains binding**: historical/scoped/archive/Block/Cluster/memory-kernel docs are non-authoritative for Stage B unless separately reconciled.
- The substrate-protection docs (N12 reconciliation register, council framing/outcome, substrate-readiness memo, Stage A semantics, P2.5/P4 carrier requirements, registry §K) **must not be contradicted**; carrier needs are stated as requirements a later Stage B defines, never as selected mechanics.

## 11. Open questions (ordering / authorization only)
1. Does Hilmir want **Candidate Gate A** next?
2. Should writer hazards sit in **Gate B**, or a separate **Gate B1** (still visible, still adjacent)?
3. Does **Cluster 2 v0.2** actually fit as the write-side authority vehicle? (Verification pending — not locked.)
4. How much **P4 framing** is needed before Layer-1 thinking (Gate D)?
5. When, if ever, does **Regime B dream/incubation** become eligible for a future gate?

---

## Anti-drift footer

READ-ONLY / FRAMING / SEQUENCING ONLY — NO IMPLEMENTATION AUTHORIZED. Names candidate gates only;
opens none. No implementation, mechanics, construction, database/schema/storage/carriers/migration,
P4 implementation, Seed-Gov implementation, writer fixes, `canon_source`, or dream runtime is opened.
Old-doc quarantine binding; substrate docs not contradicted. No registry amendment; no registry number
reserved. Guide, not control; audit observes authority and does not become authority; nothing rewrites
identity/canon/seed/soul. Subsequent gates require their own trio/operator ratification.
