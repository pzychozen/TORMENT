# TORMENT Envelope Audit — Observability Shell Definition / Authorization v0.1

**Status:** DRAFT DEFINITION — docs-only scoping. **Not an implementation, not a patch, not a gate, not a
registry entry, not doctrine.** It decides whether a *safe, content-free, ephemeral* Envelope-Audit
observability shell exists pre-substrate, and bounds what it may / may not do **before** any
implementation is considered.

**Lane:** Candidate Gate D / Layer-1 private thinking (pre-database). **Gate D remains pending operator
selection and is NOT opened by this artifact.**
**Provenance:** next-row audit (this session) → Envelope-Audit-first scoping → this filing.
**Authority note:** navigation / authorization aid only. Document A, Document B, P4, the Ledger
Observational-Boundary, the orientation map, and the Decision Registry remain source of truth.

> **One-line conclusion:** No safe *and worthwhile* Envelope-Audit implementation slice is available
> pre-substrate. A narrow content-free shell is technically expressible in the ReflectionTrace boundary
> class, but it either duplicates existing observability or needs a model API (deferred). **Recommended:
> DEFER.** The one open call is left to operator + Codex (§7).

---

## 1. Status / authority

- Docs-only definition artifact. Selects no mechanic, opens no gate, authorizes no code, names no
  durable field or schema.
- **Document B §7 (Envelope Audit boundary)** governs: Envelope Audit **may** observe / summarize / flag
  / record / stage; it **may not** admit, promote, change retrieval/scoring weights, change cognition
  eligibility, change prompt visibility, change persona/voice, change seed, or change canon/promotion
  rights unless a *separately governed* boundary authorizes that specific change (Document A admission;
  P4 projection; Seed-Gov for identity/seed/canon).
- **B-O6** — "detect / summarize / flag / stage only; never alter authority, weights, eligibility,
  persona, seed, canon, or promotion." **B-O6.1** — ordinary risk flags default to operator-visible-only
  staged candidates; immediate high-stakes safety surfacing is allowed but is **not** admission, memory,
  authority, or cognition-eligibility. **Anti-agreeableness guard (§7):** Envelope Audit measures against
  the Track-A truthfulness envelope, **never** toward an agreeableness / caution gradient.
- **B-O8** — inspectability without authority; lineage preserved without raw-reflection exposure;
  inspectability must not itself become a re-entry path. **B-O10 / §9** — silence/footprints are
  non-reentry only.
- **Ledger §3 binding:** no audit-derived statistic, summary, embedding, or hash may feed retrieval,
  routing, persona, prompt-assembly, governance gating, contestability resolution, or intent. *Surfacing
  ≠ acting.*
- **Boundary-class precedent — ReflectionTrace:** the existing ephemeral, content-free, non-reentrant,
  debug-observable decision-shape surface is the template for "observe without acting." Any shell, if
  ever built, must sit in exactly that class.

## 2. What Layer-1-only allows pre-substrate

Per the cognition sequencing comparison frame, **"Layer-1-only = ephemeral only."** Allowed: ephemeral,
per-turn, content-free observation/framing. **Not allowed pre-substrate / without separate
authorization:** durable chamber continuity · raw-reflection durability · candidate store · recovery
mechanics · Regime-B / dream · **model API** · schema / serialization / durable store · runtime private
cognition loop · scheduler / trigger / budget / autonomy. Document B §10 authorizes **no** implementation,
field names, or serialization; this artifact does not change that.

## 3. Existing-surface inventory / do-not-duplicate

Already landed and occupying the content-free observability niche:

- **ReflectionTrace v0.1 → v0.2** (`d15d9c5`, `3d0ba1a`) — ephemeral, per-turn, in-memory, **debug-only**
  (surfaced via `ThinkingResult.to_dict()` / `/thinking/debug`), coarse decision-shape labels / flags /
  counts / scores only; **no** raw reasoning / input / prompt / memory / seed / kernel values;
  **non-reentrant by construction** (test-proven, production non-reentry source scan).
- **Runner-path parity** (`df6ffce`, 2026-06-19) — end-of-turn observation-only trace on
  `AgentRunner.run_turn`, reflecting the Phase-5 effective action; schema unchanged.
- **`ReviewResult`** — already carries some response-content review output (e.g. softened-overconfidence
  / trimmed-for-live-social notes), surfaced in the result/debug shape.

**Implication:** decision-shape (mode / action / stance / review flags / top_k / frame scalars) and basic
response-review notes are **already covered**. A shell that re-emits those adds nothing. The only *new*
territory Envelope Audit would occupy is **evaluation of the response/candidate against the Track-A
truthfulness envelope** — which is precisely the part that needs content judgment (§4 deferred bucket).

## 4. Candidate observable set

**(All field names below are ILLUSTRATIVE EXAMPLES — NOT authorized implementation or schema.)**

Coarse, content-free, non-reentrant flags expressible **without** a model API and **without** raw
chain-of-thought — but note each is either already-covered or a shallow lexical heuristic:

- whether the existing review step fired a note (already in `ReviewResult.notes` — **covered**);
- count of review notes — coarse int (**near-covered**);
- presence of explicit-certainty lexical markers in the draft (e.g. "definitely/always/never") as a bool
  — *shallow heuristic; adjacency risk to the B-O6.1 anti-agreeableness guard*;
- coarse hedge-marker count / response length bucket — *shallow heuristic*.

**Deferred bucket — requires model API / genuine content judgment (NOT pre-substrate):**

- actual Track-A truthfulness assessment (faithfulness, unsupported-claim detection, overconfidence
  relative to available evidence);
- any semantic comparison of claim vs evidence or context;
- anything judging *meaning* rather than a surface lexical pattern.

**Reading:** the genuinely valuable Envelope Audit lives entirely in the deferred bucket. The
pre-substrate-expressible set is shallow and mostly redundant with ReflectionTrace / `ReviewResult`.

## 5. Non-reentry obligations (binding on any future shell)

If a shell is ever built, it must — by construction, not tag-honoring:

- **never** feed retrieval, prompt assembly, persona/voice, weights, eligibility, identity/seed/canon,
  intent formation, output control, contestability resolution, or any future routing (Ledger §3 / B-O6 /
  B-O8);
- be **debug-observable only** (the ReflectionTrace surface class); never model-visible, never
  caller-visible beyond debug;
- store **no** hidden chain-of-thought and expose **no** raw reasoning — coarse labels / flags / counts
  only;
- leave any silence/withheld footprint as **non-reentry** only (B-O10 / §9), and only if it needs no
  durability.

## 6. Hard exclusions

model API (unless separately authorized) · durable state · schema / serialization · output
blocker/finalizer · candidate store / governed admission · identity pinning · monitoring / autonomy /
self-trigger · Gate 4 writer remedies · P4 / source-sameness mechanics · Seed-Gov / O6 mechanics ·
dream / incubation runtime · database / substrate. Hitting any of these is a stop condition.

## 7. Decision

**Recommendation: DEFER.** Do not build an Envelope-Audit shell now. Rationale (source-grounded):

1. Document B §10 authorizes no implementation / field names / serialization — a shell needs separate
   authorization regardless.
2. The content-free, pre-substrate-expressible observables are shallow and **largely duplicate**
   ReflectionTrace / `ReviewResult` (§3, §4).
3. The genuinely valuable Track-A truthfulness audit requires a **model API** (forbidden here) and a
   separately-authorized track; a heuristic stand-in risks the **B-O6.1 anti-agreeableness** failure
   mode — worse than nothing.

**Unresolved question (operator + Codex own this):** is a *narrow, non-model-API, debug-only* Envelope-
Audit observation worth a slice as a stopgap, despite redundancy and shallowness? This artifact
recommends **no** (defer to an authorized model-API audit track), but does not unilaterally close the
option. If the answer is "wait," the next concrete step is **no artifact and no code** in this lane until
a model-API audit track is separately authorized.

## 8. Required tests if later implemented

Should the operator/Codex later authorize even a narrow shell, the implementation commit must prove:

- **content-free shape** — coarse labels / flags / counts / scores only; no raw text / reasoning /
  memory / seed;
- **non-reentry** — not consumed by any retrieval / prompt / persona / weight / identity / routing /
  output path (by-construction source scan, like ReflectionTrace);
- **debug-only exposure** — no `ThinkingResult` / `/agent/query` / output shape change unless explicitly
  authorized;
- **parity** — existing ReflectionTrace behavior and the anchor suites stay green;
- **no retrieval / prompt / persona / weight / identity effects** (behavioral parity, flag-off if gated).

## 9. Authorization gate (what must be true before any implementation patch)

- [ ] Operator selects Gate D / this shell explicitly (Gate D is currently **pending operator
      selection**; this artifact does not open it).
- [ ] The §7 unresolved question is answered.
- [ ] If the answer involves any Track-A content judgment, a **model-API audit track** is *separately*
      authorized (out of scope here).
- [ ] **Codex adversarial review** of the chosen shell precedes any code.
- [ ] Touch-list confirmed: observability files only (e.g. `reflection_trace.py` / its test), no writer,
      no endpoint shape, no durable surface.

## 10. What this artifact does NOT do

No code. No runtime. No private-cognition chamber. No Gate D opening. No field / schema / serialization
authorization (the §4 names are illustrative only). No model-API authorization. No change to Document A /
B / P4 / Ledger / Seed-Gov / Cluster 2. It only decides that the safe shell is **not worth building now**
and bounds the space for if/when the question is reopened.

*End — Envelope Audit Observability Shell Definition / Authorization v0.1. Definition artifact; not
doctrine, gate, or registry. Gate D remains unopened.*
