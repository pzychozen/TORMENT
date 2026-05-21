# Cluster 5 §9.3 Path C — Governance Preservation Framing v0.1

**Status:** Ratified framing draft. **Not doctrine.** Not a doctrine promotion.
**Date:** 2026-05-21
**Author:** Claude (drafted for trio: pzychozen + GPT + Claude); ratified by trio on 2026-05-21.
**Mode:** Framing-only design boundary. No code, no schema, no tests, no migrations, no automation, no remediation, no implementation authorization.
**Audit baseline:** `HEAD = 7b9173b`
**Anchor docs:** Track A v0.1 (`docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`), Cluster 2 v0.1 (`docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`), Track B v0.1 (`docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md`), Cluster 5 v0.1 (`docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md`).

**Predecessors:** Cluster 5 §9.3 Path C audit Q1 lock, Q2 lock, Q3 lock, consolidated Path C report, Phase 6 working-tree delta lock.

---

## 1. Purpose of this framing

This document does one thing: it converts the three Path C audit findings into a single stable design boundary that all future remediation, implementation, and storage decisions must obey.

It is not a patch plan. It is not a schema. It is not a doctrine promotion. It is the *rule that future implementation must respect* — written down once, so that later work can be evaluated against it rather than against scattered intuition.

After this framing is reviewed and ratified, subsequent work (lifecycle enum design, affect-provenance schema, deep-store contract, custom-storage question) can begin. Before it is ratified, no remediation should land — including a "small obvious patch" — because every patch implicitly commits to an interpretation of the invariant.

This artifact records the ratified framing for durable reference. It does not promote any doctrine, modify the four ratified spine doctrines, or authorize any implementation.

---

## 2. The through-line invariant

> **TORMENT memory derivatives must never preserve signal while losing the authority/provenance/lifecycle context that tells the system how that signal is allowed to be used.**

This is the core rule. It applies to every derivative layer (compression, deep export, echoes, projections, summaries, future caches), every persistence surface (payload row, side-channel ledger, queue file, event stream), and every consumer (cognition, character continuity, autonomy, sharing, spirit return).

Three corollaries follow from the invariant:

1. **Content alone is not a memory.** A row that carries content but not the context that governs its use is not a complete memory; it is a fragment.
2. **Derivatives inherit accountability, not just data.** A derivative that preserves the signal must either carry the authority context with it or declare itself non-authoritative.
3. **Side channels do not absolve the row.** If lifecycle, authority, or attribution lives in a side file, the row that depends on it must say so explicitly, so consumers cannot accidentally read the row in isolation.

---

## 3. The three audit surfaces

**Q1 — Deep-export boundary.**
Long-path compression to `DeepMemory` preserves content, embedding, affect tags, geometry, and scope while the `DeepMemoryStore.export` allowlist excludes `governance`, `provenance`, `baton_lifecycle`, `canon`, and `srg`. The source row survives, so the derivative is governance-dependent by source-row survival — but that dependency is not explicit or enforced. The audit classified this as a latent governance-preservation gap at the deep-store boundary.

**Q2 — Lifecycle representation.**
Lifecycle behavior exists across the system, but no unified durable lifecycle contract exists on the row. `released` and `scratch` are not modeled at HEAD; `protected` is dual-sourced between an explicit governance flag and a live-derived retention tier; `review-pending` is encoded by membership in `review_queue.jsonl` joined with payload admission markers; closure state is reconstructed from the `closure_ledger` event stream. The audit classified this as a lifecycle-durability gap. Phrase of record: *the system has lifecycle behavior, but not yet a unified lifecycle contract.*

**Q3 — Affect attribution.**
`affect_tag` and `affect_conf` are stored and survive long-path deep export. The shape does not distinguish user-confirmed, user-asserted, agent-inferred, system-measured, migrated/recovered, or ambiguous affect. `user_confirmed` exists as a real concept but is wired to overlay/feedback tuning, not to affect attribution. The audit classified this as an affect-provenance gap. Phrase of record: *the system remembers the emotional tag, but not who had the right to say it was true.*

All three surfaces are the same architectural shape: **signal survives, governing context does not.**

---

## 4. Provisional working rule

Pending final design decisions, the following rule is adopted as the working interpretation of the invariant:

> **Every derived memory layer must be either:**
>
> **(a) *governance-carrying* — the derivative stores its own governance / provenance / lifecycle / consent snapshot at the time of derivation, sufficient for the derivative to be read authoritatively in isolation; or**
>
> **(b) *governance-dependent* — the derivative is explicitly marked non-authoritative and is forced to rehydrate / join back to the source row (or canonical context) before any decision is made on it.**

A derivative that is neither — i.e., one that preserves signal in a shape that *looks* authoritative but quietly depends on context it does not carry and does not require — is the failure mode this framing forbids.

The rule does not yet say which derivatives must be (a) versus (b). That decision belongs to the later design pass, per-surface.

### 4.1 Acceptance test

The working rule reduces to a single consumer-side test, which any future remediation, patch, or schema change must pass:

> **A future memory derivative passes this framing only if a consumer can determine, without guessing, whether the derivative is authoritative by itself or must rehydrate from canonical context before use.**

This test is the practical review check. It does not ask whether governance context is *present* on the derivative — it asks whether the derivative's *authority status is unambiguous to the consumer reading it.* A governance-carrying derivative passes the test by being self-evidently authoritative. A governance-dependent derivative passes the test by being self-evidently non-authoritative. A derivative that requires the consumer to guess — to "know somehow" that it must rejoin, or to infer authority from the surrounding context — fails the test, even if all the right fields happen to be carried.

The test is the operational form of the invariant. The invariant says *what must be preserved.* The acceptance test says *how a consumer must be able to tell.*

---

## 5. What this framing does NOT decide

This framing explicitly defers — and any premature decision on the following items is out of scope:

- **The custom-storage / custom-DB question.** The audit showed the storage layer is downstream of an unresolved modeling question. Storage decisions are deferred until the contract is settled. Building a DB now would fossilize fragmentation.
- **The lifecycle enum shape.** Whether lifecycle becomes a single nested dict (like `baton_lifecycle`), a flat enum, a per-state flag set, or a graph of events — deferred. The framing only commits that *some* unified, row-durable contract must exist; not what its shape is.
- **The affect-provenance schema.** Whether affect provenance becomes a sibling field, an extension of `provenance_v1`, a nested `affect_provenance` dict, or a re-routing of the existing `user_confirmed` wiring — deferred.
- **Remediation strategy per surface.** Patch, schema migration, derivative-shape change, contract enforcement at boundaries, or some combination — deferred.
- **Implementation order.** Which surface to address first, whether in parallel, whether gated on tests — deferred.
- **Working-tree delta status.** Resolved by Phase 6 first pass: the working-tree delta against `HEAD = 7b9173b` is line-ending-only and delta-orthogonal across all Path C surfaces. Line-ending hygiene is parked for the user's Windows / source-of-truth environment, not for this audit.

These deferrals are intentional. The framing is the precondition for those decisions; making any of them inside the framing would compromise the framing.

---

## 6. Phase 6 — Working-tree delta review (completed, first pass)

Phase 6 ran read-only against the working tree relative to `HEAD = 7b9173b`. Result:

- The entire working-tree delta is **line-ending-only** (LF → CRLF). Confirmed by equal-insertion-equal-deletion stat across the modified set, an empty `git diff --ignore-all-space HEAD --stat`, and `file -b` reporting `CRLF line terminators` on working-tree copies while HEAD content is LF.
- **All relevant modified files classify as delta-orthogonal** across Q1, Q2, Q3, and spine doctrine surfaces. Zero delta-improving, zero delta-weakening, zero unclear.
- **No Path C findings change.** The Q1, Q2, Q3 baseline findings and this framing apply byte-equivalently to the working tree.
- **No second pass required.** Line-ending hygiene is a tooling/environment matter, not a Path C governance matter.

Phase 6 is therefore **complete at first pass**, not parked.

---

## 7. Final recommendation

**Review and ratify this framing before any implementation work — including before any "small obvious patch" on Q1, Q2, or Q3.**

Reasoning:

- Every implementation choice — even a one-line allowlist addition in `deep_memory.export` — implicitly answers "what context must travel with the derivative?" The framing must answer that *first* so the choice is evaluable.
- The three surfaces share one architectural shape. Patching one surface in isolation risks producing three locally-correct fixes that fail to compose. The framing is the precondition for compositional remediation.
- TORMENT already contains the vocabulary needed to honor the invariant (`baton_lifecycle` shape, `MemoryGovernanceFlags` shape, `user_confirmed` plumbing). Ratifying the framing allows later passes to *extend existing patterns* rather than invent new ones — which is the cheap path, but only available once the invariant is canonical.
- The current state is consistent at HEAD; nothing is failing. There is no urgency that justifies skipping the framing step. The urgency was finding the pattern. The pattern is found.

After this framing artifact is committed, the recommended sequence is: (1) decide per-surface remediation strategy with §4.1 as the acceptance test, (2) only then approach the storage / custom-DB question. Any later patch, schema, or storage proposal must be evaluated against §2 (invariant) and §4.1 (acceptance test) before review.

---

## 8. Status of related artifacts

- **Q1 baseline finding** — locked (deep-export governance preservation gap).
- **Q2 baseline finding** — locked (lifecycle-durability gap).
- **Q3 baseline finding** — locked (affect-provenance gap).
- **Consolidated Path C report** — locked.
- **Framing draft rev. 1** — ratified and recorded by this document.
- **Acceptance test (§4.1)** — ratified.
- **Phase 6 first pass** — locked (delta-orthogonal; line-ending-only).
- **Spine doctrines (Track A v0.1, Cluster 2 v0.1, Track B v0.1, Cluster 5 v0.1)** — unchanged. This artifact does not modify them.
- **Doctrine status of this framing** — none. This is a ratified design boundary, not a doctrine promotion. A separate doctrine commit, if desired, would be a future controlled step.

---

### Held throughout

No patches. No code edits. No tests. No doctrine promotion. No remediation design. No lifecycle enum. No affect-provenance schema. No custom DB design. No storage rewrite. No spine doctrine modification.

**Spine state:** `HEAD = 7b9173b`. Cluster 5 §9.3 Path C audit + framing + delta-classification layer complete. This artifact records that completion.
