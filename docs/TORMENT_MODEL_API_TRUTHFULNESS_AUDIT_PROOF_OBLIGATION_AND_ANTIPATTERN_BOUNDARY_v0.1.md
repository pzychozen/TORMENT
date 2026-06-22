# TORMENT Model-API Truthfulness Audit — Proof-Obligation and Anti-Pattern Boundary v0.1

**Status:** DRAFT — docs-only **proof-obligation / anti-pattern boundary**. **NOT a proof plan, NOT an implementation plan, NOT a test plan, NOT a mechanism selection.** It records *what property a future non-reentry proof would have to establish*, and *what anti-pattern it would have to avoid* — at the property level only. It selects no mechanism, surface, field, test, or design.

**Baseline:** `004bc4a`. Read-only. Windows repo state is authoritative.

**Lineage:** boundary frame (`444cc9b`) → §9 operator confirmation → non-reentry constraints lock (`bb9bb16`) → first-slice admissibility boundary (`3621e58`) → read-only non-reentry archaeology packet (Codex Option C **PASS**, chat-only) → Codex **PASS WITH REQUIRED CORRECTIONS** → this proof-obligation/anti-pattern boundary (corrections applied: property-level only; precedents cited as evidence, never as a selected mechanism/test; the two citation guards stated near the top).

**Core posture (governing).** TORMENT is an ethical memory system, not a control system. Memory may guide context, continuity, revision, symbolic integration, and history awareness. Memory must not seize authority, suppress output, trap an agent in prior state, make identity unrevisable, or create hidden output/personality pressure.

**Governed by, amends in no way:** the boundary frame `444cc9b`; the constraints lock `bb9bb16`; the admissibility boundary `3621e58`; Document B (B-O4/B-O6/B-O6.1/B-O8); P4 (non-coercion invariant; `diagnostic_only`); the Ledger Observational-Boundary (§3); the Track-A Truthfulness Envelope; the MCP Capability Boundary.

---

> ## Core forbidden line
>
> **No audit artifact, value, flag, summary, score, prompt, model output, trace, or derived signal may be read by, passed into, stored for, or honored by any runtime path outside the debug/operator observation boundary.**

---

## Citation guards (read before the rest)

> **`ReflectionTrace` is cited only as evidence that TORMENT already knows how to prove non-reentry at the property level; it is not selected as the audit mechanism, storage class, API shape, field location, or test strategy.**

```
`srg.is_crystal` is cited only as an anti-pattern for silent diagnostic-to-runtime honoring; this does not reopen SRG/R-field work.
```

---

## 1. The proof obligation is property-level only

This record states a **proof obligation as a property**, not a plan to discharge it. It says *what would have to be true* of a future non-reentry proof — never *how* such a proof would be constructed, where, in what form, or with which tests. No proof is planned, scoped, or begun here.

## 2. Structural non-reentry by absence of consumer — not by labeling

A future audit slice would have to prove **structural non-reentry by absence of consumer** — i.e., that no runtime path reads, passes, stores, or honors the audit observation — and may **not** rest on an `advisory`, `diagnostic`, `debug`, or `telemetry` label as its safety boundary. A label confers no exception (P4 O3; constraints lock §6). The proof obligation is the *absence of a consumer*, established structurally.

## 3. The accepted property precedent (properties, not a mechanism)

TORMENT already demonstrates, in existing code, that non-reentry is provable at the **property** level. The properties that count as such a demonstration — to be read as *properties a future proof would establish*, **not** as a mechanism to copy — are:

- **frozen / inert object behavior** where applicable (the observed thing cannot be mutated or accumulate authority);
- **shape-only / coarse-only visibility** where applicable (no raw content carried);
- **no consumer outside the debug/operator observation boundary**;
- **no durable accumulator** (ephemeral; nothing grows across turns);
- **absence-of-consumer proof** (the non-reentry is demonstrable in the wiring, not asserted by tag).

That these properties are *already provable in-repo* is the entire weight of the precedent. The precedent proves the obligation is **discharge-able in principle**; it prescribes nothing about how a future slice would discharge it.

## 4. This is not a command to reuse ReflectionTrace

Naming `ReflectionTrace` does **not** mean: implement the audit as `ReflectionTrace`; reuse `ReflectionTrace`; add a trace field; place the audit on the same surface; or use the same tests. None of those is selected, recommended, or implied. The precedent is evidence about *provability of a property*, nothing more (see the citation guard above).

## 5. The cautionary anti-pattern: `srg.is_crystal`

`srg.is_crystal` is the in-repo **anti-pattern**: descriptive-looking metadata that runtime readers **silently honor**. It rides on a memory's payload and is read directly — not behind the SRG enable flag — by compression (a row carrying it is never compressed) and by lifecycle protected-derivation (it is one of the legacy protected markers). It is the concrete shape of the failure the core forbidden line forbids: a value that *looks* diagnostic but is *consumed* by runtime behavior. (Per the citation guard, this names an anti-pattern only and reopens no SRG/R-field work.)

## 6. What a future audit artifact must never become

A future audit artifact must **never** become a payload field, diagnostic field, advisory field, debug field, score, trace, summary, or derived value **that runtime readers consume.** Whatever its later form, if any runtime path reads it and changes behavior, the obligation is failed — regardless of what the value is named.

## 7. Forbidden consumer surfaces (evidence, not design targets)

The following are named as **evidence** of where consumption must be absent — **not** as places to build, wire, or target. A future audit artifact must be a non-reader to all of them:

- retrieval scoring / `fabric.query()`;
- the `MemoryPlan` (`top_k_by_lane` / `weight_by_lane`);
- prompt assembly / `retrieval_assembler.py`;
- persona / voice paths;
- stance policy (`stance_policy.py`);
- governance / admission / canon / promotion;
- writers / ingest / gravity correction / identity anchor / mood drift;
- review / output control / response generation / `LLMClient.complete`.

## 8. Dangerous seams (evidence)

Named as **evidence** of accidental re-entry routes to guard against — not as design surfaces:

- `ThinkingResult.to_dict()` — caller-visible re-entry risk (caller-visible ≠ prompt-visible, but caller-reenterable; P4 O3);
- `memory_graph.py` `**payload` spread — default field spread leakage (P4 O4);
- Phase-7 turn-summary ingest into `fabric.ingest` — the response-to-memory path; an audit value here would become durable memory;
- Spine `audit["advisory_thinking"]` proximity — a value placed near consumed-looking fields;
- `srg.is_crystal` silent honoring — the §5 anti-pattern, made concrete;
- debug data computed near live scoring — proximity hazard (e.g., values computed inside the query scoring loop).

## 9. Exact line not to cross

**Do not convert the proof pattern into a mechanism, test plan, schema, field, endpoint, runtime wiring, or implementation recommendation.** The property precedent (§3) and the anti-pattern (§5) are descriptions of *what would have to be true / avoided*, never instructions for *how to build*. If any later reading turns §3 into "build it like this," it has crossed this line.

## 10. Non-goals / still not authorized

```
No implementation. No proof plan. No test plan. No tests. No schema. No field.
No endpoint. No provider/tier choice. No prompt text. No API-call shape.
No runtime wiring. No model integration. No persistence. No debug/test surface selection.
No recommendation of where to build the audit. No mechanism selection of any kind.
No model-API implementation. No dream / private cognition. No Gate D. No Envelope Audit.
No participation guidance v2. No R-surface tests (and no SRG/R-field reopening).
No writer authority / Gate B. No database / substrate. No output control. No memory writes.
No amendment to the boundary frame, constraints lock, admissibility boundary, Document A/B, P4, Ledger, Cluster 2, MCP boundary, or Track A.
No edit to PROJECT_ORIENTATION_MAP.md §0 until separately reviewed.
```

This document changes nothing and recommends nothing. It records a property-level proof obligation and a cautionary anti-pattern, with existing precedents and forbidden surfaces named **as evidence only** — so that "structural non-reentry by absence of consumer" and "never a silently-honored value" are settled as properties **before** any design question is ever raised. The §C8 admissibility gate (Hilmir explicit next-step selection + Codex challenge preserving first-slice admissibility and structural non-reentry) remains the sole path onward.

*End — TORMENT Model-API Truthfulness Audit Proof-Obligation and Anti-Pattern Boundary v0.1. Draft for trio steering; property-level proof obligation + anti-pattern only; precedents cited as evidence, never selected; no mechanism, test, schema, surface, or implementation. Dream downstream; seed/private/canon parked; SRG/R-field not reopened.*
