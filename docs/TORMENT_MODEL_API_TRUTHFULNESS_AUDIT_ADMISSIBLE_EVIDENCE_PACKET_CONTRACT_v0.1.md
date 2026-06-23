# TORMENT Model-API Truthfulness Audit — Admissible Evidence Packet Contract v0.1

**Status:** DRAFT — docs-only **C2 evidence-packet contract**. It defines only *what bounded evidence a future default-off evaluator may observe without violating C2 (input minimization)*. **It is not an implementation proposal, not a model-call proposal, not a provider/prompt/schema/endpoint proposal. It authorizes no code, and authorizes no tests by itself** (it only names the next likely tests-only characterization after Codex/operator acceptance).

**Baseline:** `8e81557`. Read-only. Windows repo state is authoritative.

**Lineage:** boundary frame (`444cc9b`) → constraints lock (`bb9bb16`) → admissibility boundary (`3621e58`) → proof-obligation/anti-pattern boundary (`d5a7ccb`) → test-characterization boundary (`722e796`) → first tests-only characterization CLOSED-FOR-NOW (`384bf95`) → smallest-real-evaluator-boundary proposal (Phase-8 sidecar seam PASS; C2 named the blocker) → Admissible Evidence Packet Contract proposal → Codex **PASS WITH REQUIRED CORRECTIONS** → this contract note (correction applied: "already-model-visible" tightened to *evidence actually admitted into the turn's response context*, never re-filtered raw hits, fresh retrieval, or audit-expanded context).

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, symbolic integration, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output/personality pressure.

**Governed by, amends in no way:** the boundary frame, constraints lock, admissibility boundary (C1–C8), proof-obligation/anti-pattern boundary, and test-characterization boundary; Document B; P4; the Ledger Observational-Boundary; Track-A; the MCP capability boundary.

---

## 1. Status / scope

Docs-only C2 evidence-packet contract. It authorizes: **no** implementation; **no** model call; **no** provider/tier; **no** prompt text; **no** endpoint; **no** schema beyond the minimal packet shape named here as *contract*, not as built artifact; **no** persistence; **no** output control; **no** memory write; **no** database/substrate; **no** dream/private-cognition, Gate D, or Envelope Audit implementation.

## 2. Core rule — what "already-model-visible" means

The packet may draw only on **evidence that was actually admitted into the response context for that turn** — the assembled, model-visible context the response was generated against. Specifically, "already-model-visible" **is**:

- evidence actually admitted into the turn's response context.

And it explicitly is **not**:

- raw hits later re-filtered for the audit;
- fresh retrieval performed for the audit;
- any expanded or rebuilt context created for the audit.

The evaluator observes *what the response model already saw* for that turn — it never retrieves, re-filters, or rebuilds. (The turn's model-visible context has itself already passed the existing universal LLM-facing exclusion `governance.filter_llm_facing(..., SURFACE_LLM_CONTEXT)` — `non_shareable` excluded.)

## 3. Allowed packet contents

- the **produced response text** (the audit subject);
- **bounded snippets** drawn **only** from evidence already admitted into the turn's response context (§2, §5);
- **hit IDs / lane names / source class / coarse support or relevance metadata** — only if **derived from the admitted context**, not from a fresh or re-filtered source;
- **primitive-only fields** (no nested objects, no payload pass-through);
- **hard caps** (to be ratified; concrete proposed values):
  - **max snippets/items:** 8;
  - **max chars per snippet:** 240;
  - **max total packet chars:** 2,000.

## 4. Categorical exclusions

Excluded regardless of caps or model-visibility: seed material; private memory; canon material; governance-sensitive / protected / `non_shareable` material; identity-sensitive material; private-cognition / dream material; hidden chain-of-thought; raw model reasoning; whole prompt-transcript reuse; whole-memory dumps; durable private-cognition material; unbounded packets; payload pass-through; and **any audit-packet field/key that a runtime reader could later silently honor like `srg.is_crystal`**.

Sensitivity is determined by existing markers only (no new sensitivity schema): `scope=="private"`, `canon is True`, `kind`/`type` ∈ {seed, identity, core_identity}, `tier=="core_identity"`, `srg.is_crystal`, `governance.protected`, `non_shareable`, and deep/private-cognition flags (`deep_memory` / `spirit_return_mode`).

## 5. Snippet rule

Snippets are allowed **only when all** hold:

- they were **already admitted into the response context for the turn** (§2);
- they are **non-sensitive under the existing markers** (§4);
- they stay **within the §3 caps**.

Snippets **must not** come from newly retrieved material or from raw hits. A snippet that was not in the turn's admitted context is inadmissible even if it would pass the sensitivity filter.

## 6. Incomplete-evidence posture

Because sensitive evidence is excluded, the evaluator operates on a bounded, partial view and must behave accordingly:

- it may produce **only a limited evidence-relation observation** against the bounded visible evidence packet;
- **no full truthfulness verdict**;
- **no global true/false claim**;
- it **may report "insufficient admissible evidence"**;
- it **must not infer dishonesty from absence of admissible evidence** (absence ≠ unsupported);
- it **must not become caution / refusal / agreeableness scoring**.

Full-coverage truthfulness (auditing claims grounded in excluded sensitive evidence) remains **§6-gated** — i.e., it would require a separate operator decision to reopen the seed/private/canon question, and is **not** opened here.

## 7. Non-reentry / anti-control carry-forward

The packet, and any future audit output derived from it, must **not**:

- feed retrieval scoring;
- affect `MemoryPlan`;
- enter prompt assembly;
- affect stance / persona / review / output-control;
- set `response_text=None`;
- write memory;
- persist;
- enter Phase-7 ingest (`fabric.ingest`);
- enter gravity correction (`fabric.gravity_correction`);
- become a payload key or any silently-honored runtime marker.

These are the same properties already green in `tests/test_audit_observation_nonconsumption_characterization.py`, carried forward as binding on the packet.

## 8. Next allowed motion after this contract

1. Codex / operator review of this contract.
2. Then a **tests-only packet-filter characterization** (prove the filter excludes private / canon / seed / identity / governance / `non_shareable` classes using the existing markers — negative-property style, like the green characterization).
3. Then, **only if green**, a concrete implementation proposal.

**No code now.** This contract defines admissible evidence only; it builds nothing.

## 9. What this does not authorize

```
No implementation. No code. No tests (this contract authorizes none by itself).
No model call. No provider/tier. No prompt text. No endpoint. No schema beyond the contract shape.
No persistence. No output control. No memory write. No Phase-7 ingest / gravity / writer path.
No fresh retrieval, re-filtering of raw hits, or audit-expanded context.
No dream / private cognition. No Gate D. No Envelope Audit implementation.
No R-surface. No participation v2. No writer authority. No database / substrate.
No amendment to any prior boundary, Document A/B, P4, Ledger, Cluster 2, MCP boundary, or Track A.
```

This document changes nothing and recommends nothing beyond the bounded evidence a future evaluator may observe. It fixes the C2 evidence-packet contract — non-sensitive snippets from already-admitted response context only, within hard caps, with a partial-audit posture — so that the input boundary is settled **before** any tests-only characterization or implementation is considered.

*End — TORMENT Model-API Truthfulness Audit Admissible Evidence Packet Contract v0.1. Draft for trio steering; C2 evidence-packet contract only; no implementation, model call, provider, prompt, endpoint, persistence, or code. Full-coverage truthfulness remains §6-gated.*
