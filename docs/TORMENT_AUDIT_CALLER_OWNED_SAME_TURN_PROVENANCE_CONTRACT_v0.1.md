# TORMENT Audit — Caller-Owned Same-Turn Provenance Contract v0.1

**Status:** DRAFT — docs-only, requirement-level contract. It authorizes **no
code, no tests, no schema, no endpoint, and no wiring**. It defines the contract
under which a future orchestration layer *outside* `AgentRunner` may honestly
supply `audit_admitted_context_items` to the TurnResult audit packet observation
sink — without selecting which owner/path that layer will be.

**Baseline:** read-only; Windows repo state is authoritative.

**Lineage:** admissible evidence packet contract (§2/§5 same-turn rule) →
identity-context exclusion §4A → assembler prompt-context invariant (`a695a85`) →
output-sink co-occurrence gap (`af98662`) → pure composition sidecar (`5f98fb1`)
→ TurnResult staging seam (`dd052a3`) → TurnResult packet observation sink
(`e37da83`) → same-turn provenance caller inventory (`c67b443`, conclusion: no
honest live caller path exists yet) → **this contract (Codex/operator: PASS for
B with conditions)**.

**Governed by, amends in no way:** the Admissible Evidence Packet Contract v0.1
(`docs/TORMENT_MODEL_API_TRUTHFULNESS_AUDIT_ADMISSIBLE_EVIDENCE_PACKET_CONTRACT_v0.1.md`,
esp. §2 same-turn rule, §4 + §4A exclusions, §6 incomplete-evidence posture, §7
non-reentry); the boundary frame (`444cc9b`); Document B; P4; the Ledger
Observational-Boundary; Track-A; the MCP capability boundary.

**Core posture (governing).** TORMENT is an ethical memory system, not a control
system. Memory may guide context, continuity, revision, and history awareness.
Memory must not seize authority, suppress output, or create hidden output/
personality pressure. *Audit observes authority; audit does not become authority.*

---

## 1. Naming and framing

This is the **caller-owned same-turn provenance contract for an orchestration
layer outside `AgentRunner`**. It is deliberately **not** called "external
orchestration": "external" can read as *public API*, and **no public endpoint or
public API contract is created or implied here**.

The "orchestration layer outside `AgentRunner`" is the role that, in some future
ratified slice, would own the same-turn provenance claim and pass already-
selected admitted item dicts into `run_turn`. **This document does not select
that owner.** The future owner may turn out to be an internal orchestrator, a
demo/harness owner, a service wrapper, an endpoint, or something else; this
contract chooses none of them. It defines only the *obligations any such owner
must satisfy* before any wiring is considered.

## 2. What `AgentRunner` does and does not do

`AgentRunner` **composes explicit inputs only**. For the audit packet it uses
exactly two caller-visible inputs: the final reviewed
`execution_outcome.response_text` and the caller-supplied
`audit_admitted_context_items`, via the item-core builder
(`build_audit_evidence_sidecar_from_items`).

`AgentRunner` does **not** retrieve, assemble, verify, certify, persist, or
remember admitted context. It performs no retrieval, calls no assembler, makes
no provenance/verification claim, writes nothing, and keeps no record of the
items beyond returning the resulting observation-only packet on `TurnResult`.

## 3. The caller's provenance obligation

**The caller owns the claim** that `audit_admitted_context_items` were the items
selected/admitted into the **same turn** that produced `response_text`. The
runner does not and cannot establish this; co-location on one `TurnResult` is a
structural convenience, not a proof (see §5).

An honest caller therefore must, within a single call frame it controls, hold
**both halves of the same turn** — the response the model produced and the
admitted context that response was generated against — and pass only the latter's
already-selected admitted item dicts into `run_turn`. The same-turn rule of the
Admissible Evidence Packet Contract (§2/§5) is the caller's obligation here, not
the runner's.

## 4. Candidate item shape

- Candidate items MUST be **pre-extracted admitted item dicts** (the shape the
  existing extractor/packet builder already consume).
- Candidate items MUST NOT be an `AssembledContext` (object or dict). The whole
  `AssembledContext` is never passed into `AgentRunner`; extraction/selection
  happens in the caller's frame, before the call.
- No new field, schema, or marker is introduced by this contract.

## 5. Observation-only semantics

`TurnResult.audit_evidence_packet` is **observation-only**. It is returned on
`TurnResult` and is never routed into prompt assembly, review, output/output-
control, ingest, fabric, writer paths, retrieval, model-visible context,
persistence, or any authority decision.

**Structural co-location on `TurnResult` does not prove provenance.** The packet
appearing beside `response_text` means only that the caller supplied both; it
asserts nothing about whether the items were genuinely the same turn's admitted
context. Provenance is the caller's claim (§3), not an inference from layout.

**Packet-absence semantics.** A missing/`None` packet (no items supplied, empty/
blocked/suppressed response, or fail-soft builder error) MUST NOT be treated as:
dishonesty, unsupportedness, a refusal basis, a suppression basis, a retrieval
signal, an authority signal, or a memory-write signal. Absence of an admissible
packet is not evidence of anything (consistent with packet-contract §6).

## 6. Explicit forbids

The caller (and any future wiring) MUST NOT:

- supply **stale or different-turn** context as if it were this turn's;
- **re-filter raw hits** for the audit;
- perform **fresh retrieval** for the audit;
- pass a whole **`AssembledContext`** into `AgentRunner`;
- use **packet contents** for review, output suppression, retrieval, prompt
  construction, ingest, writer paths, authority decisions, or any model-visible
  context;
- treat **packet absence** as evidence the answer is dishonest or unsupported;
- claim **same-turn provenance from mere structural co-location**.

## 7. What this contract does not create

- **No public endpoint or public API contract.**
- No endpoint change, no `/retrieve` change, no `/agent/query` change.
- No persistence, no memory write, no output control.
- No prompt / model / provider / evaluator change.
- No `same_turn_verified`, `truth`, `authority`, provenance-certification, or
  equivalent flag.
- No selection of the future owner/path.

## 8. Next-step gate

**Wiring remains BLOCKED** until a later Codex/operator review selects a concrete
owner/path under this contract.

- The **first permissible later code slice**, *if* an owner is selected, would be
  a **non-endpoint, tests-backed orchestration adapter or harness** that already
  owns **both halves in one call frame** and passes **only selected admitted item
  dicts** into `run_turn`. It must add **no** public schema, verification flag,
  endpoint behavior, persistence, model/provider/prompt/evaluator behavior,
  output control, or authority.
- If **no such owner exists**, the next step is **another inventory / design
  fork — not wiring**.

Path forward is gated: Hilmir explicit owner/path selection + a Codex challenge
that the selected owner honestly holds both halves in one call frame and adds no
public schema / flag / endpoint / persistence / authority, before any code.

---

*End — TORMENT Audit Caller-Owned Same-Turn Provenance Contract v0.1. Docs-only,
requirement-level; selects no owner, authorizes no wiring; amends no prior
boundary, packet contract, Document B, P4, Ledger, or MCP boundary. Wiring stays
blocked pending explicit owner/path selection + Codex challenge.*
