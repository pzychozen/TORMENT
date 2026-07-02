# TORMENT Memory Engine P4 — Source-Sameness Policy Frame v0.1

**Status:** DOCS-ONLY policy frame. **Non-authorizing.** Defines what *source-sameness* and
*source-membership sameness* must **mean** for P4 **before** any `ReaderPolicy`, helper, comparison
mechanism, carrier, or runtime gate is implemented. Selects no mechanic, opens no gate, authorizes no
code, names no durable field / schema / carrier, and changes no eligibility or projection behavior.
Navigation / meaning aid only.

**Authority note:** the ratified P4 Reader/Projection-Safety Contract
(`docs/TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md`), the matched P2.5-writer /
P4-reader reconciliation, the Ledger Observational-Boundary, Document A/B, and `PROJECT_ORIENTATION_MAP.md`
§0 remain source of truth. This frame refines the *meaning layer only* of P4 O1/O2/O5; it does not amend,
weaken, or reinterpret the contract's obligations or its non-coercion invariant.

**Provenance:** after `tests/test_p4_source_sameness_readiness_characterization.py` characterized the
current O1/O2/O5 readiness terrain (commit `adbdbf0`) and the O3/O4 projection/noncoercion guard was
refreshed green (`3f4545b` / §0 closure `2b6931d`). No P4 mechanics are authorized.

**Doctrine (carried, exact):**

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> Presence of a reusable local `eid` is insufficient.

---

## 1. Current state

- **P4 O1/O2/O5 source-sameness readiness is characterized (tests-only).**
  `tests/test_p4_source_sameness_readiness_characterization.py` pins the current seams as
  **presence/existence based, not source-sameness conformance**, and asserts **no** runtime
  `ReaderPolicy` / `source_sameness` / `source_membership` / `diagnostic_only` gate / source
  fingerprint-token / projection-eligibility mechanism exists in production.
- **P4 O3/O4 projection/non-coercion is green again** after the SRG-multiplier guard refresh.
- **Gate A producer-independent wall work is HOLD**; **Dream / Regime-B is HOLD and blocker-dependent.**
- **No P4 mechanics are authorized.** The P4 contract already ratifies the meaning of O1–O5, the
  contract-wide **non-coercion invariant**, and the values-layer **`diagnostic_only` eligibility posture**
  for unprovable runtime source-sameness (§9 of the contract). This frame adds only the *definition +
  evidence model* layer the contract left as a "family-bound adequacy standard."
- *(Bookkeeping: §0's HEAD line names `3f4545b` while the pushed edge is `2b6931d`; not corrected here —
  this slice edits no §0.)*

## 2. Why source-sameness is needed (the exact problem)

A reusable local `eid` is not a stable identity of a *source*. Three characterized seams show the gap:

- **`_query_deep_lane`** (`fabric.py`) resolves a DeepMemoryEcho and admits it when its **source row is
  present** in the private graph (orphan filtering against `entities`). Presence of a row at an `eid`
  does not prove the deep hit and the live row describe the **same source**.
- **`_maybe_emit_identity_anchor`** (`fabric.py`) derives a durable `identity_anchor` when enough
  **motif member eids are present** in the agent graph. Membership-by-presence does not prove the members
  are the **same sources** the motif originally bound.
- **`MemoryGraph.update_payload`** (`memory_graph.py`) mutates the payload behind an **existing eid** and
  **reappends** a `nodes.jsonl` record; the loader treats the **last record as canonical**. So the content
  behind an `eid` is a *moving target*: a reference captured earlier may now resolve to a different
  canonical payload.

The problem P4 source-sameness solves: **prevent a reference from contributing to ordinary cognition (or
to a derived identity anchor) on the strength of `eid` presence alone, when the thing now behind that
`eid` may not be the same source that was referenced.** This is the concrete failure the contract's O1/O2
name and that `ws_section_2a_v1` proved by counterexample (material that entered fan-out produced
identity pressure it was never meant to carry).

## 3. Definitions (meaning only — no field names, carriers, or comparison mechanism)

- **Source** — the originating memory a reference *claims* to be about, independent of the local `eid`
  slot it currently occupies.
- **Source-sameness (O1, single-source echo)** — the property that a DeepMemoryEcho's referenced source
  and the live node it resolves to are **provably the same source**, not merely the same `eid`. Meaning
  requirement only; the comparison mechanism (token / fingerprint / lineage) is **not selected here**.
- **Source-membership sameness (O2, motif/member-derived)** — the property that a motif member reference
  contributing to a derived identity anchor is **provably the same source** the motif bound, judged under
  the **family-bound source-sameness adequacy standard** the contract names — i.e. adequacy may differ per
  memory family; **no single centralized mechanism and no motif redesign is required or implied**.
- **Canonical-last reappend** — the `update_payload` behavior where the newest appended record for an
  `eid` is authoritative; the reader-trace consequence (below) is why sameness cannot bind to `eid` alone.
- **Adequacy standard** — the *bar of evidence* a given family must meet to call a reference "same
  source." Defined per family, later; this frame states the shape of adequacy, not its threshold.

Carried distinctions (exact): `eid presence ≠ source-sameness` · `member presence ≠ source-membership
sameness` · `current canonical payload ≠ the payload a prior reference captured` · `inspection ≠
projection` · `diagnostic ≠ cognition-eligible`.

## 4. Evidence model (what counts / what is insufficient)

**Insufficient evidence (must NOT, by itself, admit to cognition or emit a derived anchor):**

- presence of a reusable local `eid`;
- presence of a source row in `entities` (orphan-absent ≠ same-source-present);
- motif-member presence / member-count threshold alone;
- the *current* canonical payload matching, when it may have been reappended after the reference was taken;
- any debug / trace / provenance / audit / telemetry **label** used as the safety boundary (O3).

**Acceptable evidence (shape only — mechanism deferred):** a family-appropriate demonstration that the
referenced source and the resolved node are the **same source** — e.g. a stable source token / lineage /
fingerprint that survives `update_payload` reappend and `eid` reuse. The *form* is a family-bound
adequacy proof; the *carrier and comparison* are **not selected here**.

**Unprovable case (already ratified by the contract, restated, not changed):** when runtime source-sameness
**cannot be proven**, the reference defaults to **`diagnostic_only` cognition eligibility** — operator-
auditable, inspectable, recoverable, no default model-facing notice — until an explicit audited governance
action restores eligibility. `diagnostic_only` is an **eligibility posture, not a projection instruction**.

## 5. Surface classification (diagnostic/read-only vs prompt-visible/projection-eligible)

Grounded in P4 O3/O4 and the already-green O3/O4 characterization:

- **Must remain diagnostic / read-only:** orphan/mismatch observability (O5); raw deep-memory and
  provenance surfaces; any sameness-unprovable reference (rides at `diagnostic_only`). Diagnostic exposure,
  even when deliberate and surface-classified, **does not by itself confer cognition eligibility**.
- **Prompt-visible / projection-eligible only through explicit, surface-classified projection (O4):**
  identity/substrate fields must never become prompt- or caller-visible merely because a payload spreads
  its fields by default (the `**payload` spread counter-pattern on `/agent/query` and MCP query).
- **Classified by intent + re-entry capability, not by label (O3):** MCP query (Spine-routed) stays
  distinct from MCP resource-bypass surfaces; a "debug"/"trace" name is not a safety boundary.
- **Non-coercion invariant governs all of the above (not a sixth feature):** withholding an unverified
  memory from admission is allowed; **blocking output, invisibly deleting evidence, covert suppression,
  authority seizure, and personality lock are not authorized.** Prompt-silent non-admission is permitted
  only while the reference stays operator-auditable and inspectable.

## 6. Blockers (what is blocked until carrier / schema / substrate / admission exists)

- **The comparison mechanism itself** (source token / fingerprint / lineage) — needs a **carrier /
  schema** → P6.
- **Any runtime `ReaderPolicy` / source-sameness gate** — the contract keeps ReaderPolicy a **noun, not a
  runtime authority**; obligations are surface-local / join-local, not a centralized reader engine.
- **Reader-trace across `update_payload` reappend** — needs durable source lineage that survives
  canonical-last mutation → P5b/P6.
- **Orphan/mismatch recovery UX, quarantine, ledger/event schema, counters** — P5a / maintenance lane;
  explicitly **not selected** by P4.
- **Anchor/canon-affecting outcomes** — remain behind Document A admission and Seed-Governance; **no
  admission / promotion crossing** is opened here.
- **Motif-member-derived identity anchors becoming authority** — blocked until O2 adequacy + admission.

## 7. Safe next slices (ranked; none opened here)

1. **Nothing beyond this frame (HOLD)** — the meaning layer is now stated; mechanics stay blocker-gated.
2. **Tests-only characterization deepening** — e.g. characterize the `update_payload` canonical-last
   reappend reader-trace hazard as an explicit source/AST watch-item (mirrors the existing readiness test;
   no mechanics). Smallest safe motion if any is wanted.
3. **Reviewer pass** — Codex/GPT adversarial review of this frame's definitions + evidence model before
   any future mechanic is proposed.
4. **(Blocker-gated, NOT now)** family-bound adequacy-standard selection → requires carrier/schema
   authorization (P6) and is out of scope until then.

## 8. Explicit non-authorizations

No `ReaderPolicy` implementation. No source-sameness runtime gate. No `diagnostic_only` behavior change
(the posture is restated, not implemented). No projection-eligibility change. No source token / fingerprint
/ lineage / carrier / comparison mechanism. No candidate store / carrier / schema / substrate / admission /
promotion. No Dream / Regime-B runtime. No Gate D runtime. No Document B chamber runtime. No Envelope-Audit
runtime. No AgentRunner / app / spine / MCP wiring. No model / provider / API / prompt path. No memory
writes / persistence / logging / transcripts. No output-control / finalizer / refusal / identity / canon
behavior. No dynamic-kernel / `conversation_shock`. No amendment to the P4 contract, Document A/B, P2.5/P4
reconciliation, Ledger, or Cluster 2.

## 9. Verdict

**NO-OPEN.** P4 source-sameness is defined here as **policy / meaning only** — the definitions, evidence
model, and surface classification that a later family-bound adequacy standard and any future
`ReaderPolicy` must satisfy. **No mechanic, gate, carrier, or eligibility/projection behavior is opened.**
The next safe motion is **tests-only characterization or a reviewer pass, not mechanics**; the mechanism
itself stays blocked until carrier / schema / substrate / admission is separately authorized.

*End — P4 Source-Sameness Policy Frame v0.1. Docs-only, non-authorizing. Verdict: NO-OPEN. Meaning layer
only; P4 mechanics remain unopened and blocker-gated.*
