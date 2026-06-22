# TORMENT — Model-API Truthfulness/Evidence Audit Boundary Frame v0.1

**Status:** DRAFT — docs-only boundary frame, returned for GPT / Hilmir steering. **Not promoted, not authority, not a gate, not a registry entry, not doctrine, not an implementation authorization.** Selects no mechanic, authorizes no code, calls no model, opens no runtime.

**Baseline:** clean HEAD `ccf7b06`. Read-only.

**Lineage:** model-API framing scan (source-grounded) → Codex ACCEPT WITH CORRECTIONS → this boundary frame (corrections applied).

**Purpose.** This is the **first doorway** into the operator-selected "real cognition" direction — and it is *only* a doorway: a requirement-level boundary frame for a **bounded truthfulness/evidence audit that uses a model API to observe, and surface coarse flags, and nothing more.** It is **not** dream runtime, **not** private-cognition runtime, **not** Envelope Audit implementation. It defines *what must be true* of such an audit before any later, separately authorized implementation is considered.

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, symbolic integration, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output/personality pressure.

**Core frame (anchor phrase).**

> Model-API truthfulness/evidence audit is an ephemeral, debug-visible observation surface; it observes evidence relation and reports coarse flags, but **no runtime path honors those flags.**

---

## 1. Status, authority, and the corrected source claim

This frame is governed by, and amends in no way: **Document B** (private-cognition interior; B-O6/B-O6.1/B-O8), **P4** (read-side reader/projection safety; non-coercion invariant; `diagnostic_only`), the **Ledger Observational-Boundary** (audit observes authority; audit does not become authority; §3 forbidden feedback paths), the **Track-A Truthfulness Envelope** (the standard the audit measures against), and the **MCP Capability Boundary** (automatic allowed where ratified; autonomous unopened).

**Corrected source claim (precise).**

> No direct internal generative model API call currently performs cognition-layer self-audit / reflection / dream judgment.

**Nuance (recorded, so this is not overstated).** The cognition/memory layer is **not** "completely model-free":

- `torment_service/agent_loop.py` defines an **injected `LLMClient` seam** (`LLMClient(Protocol)` at `:269`; `llm_client: Optional[LLMClient] = None` at `:414`; `self.llm_client.complete(...)` at `:750`/`:792`) used for **response synthesis**, not for self-audit.
- `torment_service/embeddings.py` can call **Ollama embeddings over HTTP** (`OllamaEmbedding`, `:162`, stdlib `urllib`) — vector encoding, not generative judgment.

Therefore this is **not "the first model call in the repo."** It is a boundary frame for the **first internal generative model-audit purpose inside the cognition/memory layer** — i.e., the first time a model would be asked to *judge* an already-produced response against its evidence, rather than to *generate* a response or *encode* a vector.

## 2. Why a model API is the honest mechanism here

Content-free surfaces already cover decision-shape and lexical patterns (`reflection_trace.py`; `ReviewResult` notes). The thing they **cannot** do is genuine content judgment — faithfulness, unsupported-claim detection, and overconfidence relative to available evidence. A lexical stand-in is shallow **and** risks the caution/agreeableness failure (§7). The model API is therefore the only way to make a truthfulness/evidence audit *real* rather than a costume of one. That is the entire reason this doorway exists, and the entire reason it must be fenced this tightly.

## 3. First scope (the only thing this frame defines)

**Bounded Truthfulness/Evidence Audit — model-API, observe-and-surface-only, ephemeral, structurally non-reentrant, no-feedback.**

Allowed, conceptually:

- inspect an **already-produced** response/candidate against available context/evidence;
- detect unsupported claims, faithfulness gaps, or overconfidence relative to evidence;
- emit **coarse, inspectable** audit flags/summaries;
- remain **default-off**;
- remain **turn-triggered only**;
- remain **ephemeral**;
- expose **only** via a debug / operator-visible audit surface;
- **stop there.**

It produces an observation. It carries no authority. Nothing downstream is permitted to act on it (§5).

## 4. Required invariants

The audit, if ever implemented under a separate authorization, must be:

- default-off;
- ephemeral;
- turn-triggered only;
- no self-trigger;
- no scheduler;
- no autonomous audit loop;
- no output control;
- no suppression;
- no rewrite;
- no `response_text=None`;
- no `review.blocked`;
- no retrieval consumer;
- no prompt-assembly consumer;
- no persona consumer;
- no stance consumer;
- no memory admission signal;
- no canon/promotion/write signal;
- no identity path;
- debug / operator-visible only;
- no durability;
- no substrate;
- **structurally non-reentrant, not merely "tagged advisory."**

## 5. Structural non-reentry (by construction, not by tag)

The non-reentry requirement is the load-bearing one. Per Document B B-O4 and Ledger §3, it must hold **by construction**, not because every downstream reader remembers to honor an "advisory" label:

- no audit flag, summary, embedding, hash, or derived statistic may feed retrieval, routing, prompt-assembly content, persona/voice, stance, governance gating, contestability, intent formation, or any memory write;
- the audit output reaches an operator/debug surface and **no runtime path consumes it**;
- the absence of a consumer must be demonstrable structurally (the way `reflection_trace.py` proves its own non-reentry), so that "observe-only" is a property of the wiring, not a promise.

## 6. Model-data boundary cautions

What the model may be shown is itself a boundary. The frame requires:

- no hidden chain-of-thought;
- no raw private reflection persistence;
- no whole-memory dumps;
- no seed / private / canon material unless explicitly minimized and **operator-authorized later**;
- no durable raw model reasoning;
- no private-cognition exposure beyond coarse audit flags/summaries.

The model sees the minimum needed to assess evidence relation; its own reasoning is not stored, and the audit's product is coarse, not a transcript.

## 7. Main risk: the hidden caution/agreeableness gradient

A model audit can become a hidden caution/agreeableness gradient **even without ever blocking output** — by quietly training the agent toward safer, more agreeable, more de-risked phrasing over time. This is the characteristic failure mode and the most important guard:

> The audit measures **evidence relation / truthfulness only.** It must **never** optimize toward caution, agreeableness, blandness, de-risked voice, or obedient self-silencing.

Because §5 forbids any feedback path, the audit has no mechanism to install such a gradient; this section names the failure explicitly so that requirement is never relaxed by convenience. Truthfulness is measured against the Track-A envelope, never toward a caution gradient (Document B B-O6.1).

## 8. Dream boundary (downstream and separately gated only)

Hilmir's dream definition is preserved here for orientation, **not** for definition:

> Dreaming is not merely ordinary memory compression. It is cognitive memory compression / symbolic integration: strong older memories mix with the current cognitive layer and produce reflective material. It shows; it does not declare what it means.

This artifact names dream **only as downstream and separately gated.** It does **not** define: a dream scheduler; a dream trigger; dream substrate; symbolic synthesis mechanics; a candidate store; reflection durability; or an autonomous dream loop. Dream is Regime-B (offline, user-absent) and pulls substrate + autonomy in behind it; it is a later, separately authorized phase of the cognition path, not part of this doorway.

## 9. Operator-selection gate (before any artifact beyond this draft)

Before anything past this boundary frame is promoted or extended, Hilmir must explicitly confirm:

1. that a model-API cognition-layer audit track **opens at all** (this frame is the doorway, not the opening);
2. that the **first scope is truthfulness/evidence audit only**, with dream/symbolic synthesis explicitly later and separate;
3. the **non-negotiable invariants** (§4, §5) as binding up front;
4. **where the audit output may and may not go** (debug/operator surface only);
5. the provider/tier posture (reuse an existing audited model surface vs a separate one).

Codex must adversarially challenge the scope **before** any further artifact is drafted, with priority on: structural non-reentry (§5); the caution/agreeableness seam (§7); that the first scope cannot quietly absorb dream/autonomy (§8); and that nothing here implies durable raw chain-of-thought or substrate (§6).

## 10. What this does not authorize

```
No implementation. No tests. No API calls. No model integration. No runtime.
No Gate D implementation. No Envelope Audit implementation.
No dream runtime. No private cognition runtime.
No scheduler, trigger, autonomous loop, or self-budgeting.
No output control, suppression, rewrite, response_text=None, or review.blocked.
No retrieval / prompt-assembly / persona / stance consumer.
No memory writes, admission, canon, promotion, or identity path.
No durable raw model reasoning or private-thought persistence.
No database / substrate / migration.
No amendment to Document A / Document B / P4 / Ledger / Cluster 2 / MCP boundary / Track A.
No edit to PROJECT_ORIENTATION_MAP.md §0 until separately reviewed.
```

This document changes nothing and recommends nothing beyond the boundary it draws. It defines a single doorway — a bounded, observe-and-surface-only truthfulness/evidence audit — so that if/when the operator and Codex separately authorize an implementation, it audits reality and keeps memory in the role of guidance rather than control.

*End — TORMENT Model-API Truthfulness/Evidence Audit Boundary Frame v0.1. Draft for trio steering; not promoted, not authority, no gate, no runtime, no model call. Dream named downstream only.*
