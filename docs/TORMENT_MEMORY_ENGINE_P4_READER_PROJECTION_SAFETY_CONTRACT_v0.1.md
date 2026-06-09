# TORMENT Memory Engine P4 — Reader and Projection Safety Contract v0.1

**Status:** P4 requirement-level design contract — docs-only. Promoted 2026-06-09. Authorizes **no implementation, no substrate mechanics, and no migration**. States *what must be true* of cognition-facing readers, derived cognition writers, projection surfaces, and orphan/mismatch handling; selects no mechanics. Each obligation is satisfiable family-by-family by later phases.
**Lineage:** Pre-P4 reader-dependency trace → P4 framing report v0.1 (Claude local-reality inspection) → Codex adversarial pass → wording corrections (rev1) → contract extraction → Codex four-point wording closure → Hilmir values-layer ratification → GPT final steering clarification. The full framing report remains working-folder evidence only and is not promoted.

---

## 1. Status and authority boundary

This is the **P4 requirement-level design contract**, docs-only. It authorizes:

- no implementation;
- no substrate-mechanics;
- no migration.

Standing anchors, carried together:

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.

This contract states requirements. It does not rule, implement, or select mechanics. Each obligation is satisfiable family-by-family by later phases; this document fixes only *what must be true*, not *how*.

## 2. Purpose

P4 constrains four things before any future carrier or substrate mechanics are designed: **cognition-facing readers**, **derived cognition writers that resolve persisted source references**, **projection surfaces**, and **orphan/mismatch handling**.

P4 is an **enforcement-edge contract layered on P1/P2/P2.5**. P1/P2 fixed the identity vocabulary (a local `eid` is a reusable handle, never sufficient sameness; memory-lineage identity, record-revision identity, revision fingerprint, `era_ref`). P2.5 established that vocabulary is not yet carried in code. P4 governs what a reader or writer must prove before *using* a stored reference, and what must stay visible when it cannot.

P4 is **not** a redo of identity vocabulary, and **not** a storage-design phase.

## 3. Controlled interpretation boundary

The contract is read under these distinctions; collapsing any of them is drift:

- **presence ≠ sameness** — a reference resolving to a live node proves only that *something* occupies the handle, not that it is the same source.
- **caller-visible ≠ automatically prompt-visible** — a field returned to an API/MCP caller is prompt-reenterable only by caller action; the hazard is silent default exposure.
- **diagnostic intent ≠ guaranteed non-reentry** — a debug/research/provenance/trace/telemetry label does not make a surface structurally incapable of re-entering cognition.
- **audit visibility ≠ audit authority** — an observability surface may witness authority; it must not become authority over cognition.
- **family-bound interpretation discipline ≠ one hidden central ReaderPolicy authority engine** — obligations are met per family/surface, not by a single centralized reader.

## 4. Contract obligations

Five normative obligations. Each states the requirement only; none selects an evidence carrier, comparison method, schema, or fence.

### O1. Echo source-sameness

A DeepMemoryEcho may resolve a live source node and contribute to ordinary cognition **only when source-sameness is proven**. Presence of a reusable local `eid` is insufficient.

*(Carrier and comparison mechanism not selected here.)*

### O2. Derived motif-member source-membership sameness

A persisted motif member reference may contribute to derived identity-anchor emission **only when source-membership sameness is proven under the applicable family-bound source-sameness adequacy standard**.

No centralized ReaderPolicy implementation is required; no single identical mechanism across every memory family is required; motifs are not redesigned.

### O3. Intent and re-entry-capability classification

Every cognition-facing, caller-visible, audit-visible, or diagnostic surface must be classified by **both** its *intent* **and** its *re-entry capability*. A surface may **not** rely solely on a debug, research, provenance, trace, audit, or telemetry label as its safety boundary.

MCP query (a Spine-routed tool over the normal query path) stays distinct from MCP resource bypass surfaces.

### O4. Explicit projection gating

Identity and substrate fields may become prompt-visible or caller-visible **only through an explicit, surface-classified projection**. They must never become exposed accidentally merely because a storage payload spreads its fields by default.

Deliberate diagnostic projection is permitted when explicit and surface-classified; such projection does not by itself make the projected data cognition-eligible retrieval.

*(No allowlist, version format, or schema mechanism selected here.)*

### O5. Orphan and mismatch observability

An unresolved, mismatched, or sameness-unprovable reference must:

- not silently enter cognition;
- not invisibly disappear;
- remain operator-auditable and inspectable.

P4 does **not** select a shaped model-facing notice, disclosure channel, ledger format, event schema, counter, quarantine record, or recovery UX.

## 5. Contract-wide non-coercion invariant

The following invariant **governs O1–O5 and is not a sixth implementable feature**:

- Withholding an unverified memory from context admission **is allowed**.
- Blocking output generation **is not authorized**.
- Deleting evidence invisibly **is not authorized**.
- An audit or observability surface may observe authority but may **not** become authority over cognition.

> Memory may shape context. Memory may not seize authority.
> Audit observes authority. Audit does not become authority.
> None of O1–O5 may be satisfied through silent output blocking, invisible deletion of evidence, covert unauditable suppression of evidence or eligibility state, authority seizure, or personality lock. Prompt-silent non-admission of an unverifiable memory is permitted when the reference remains operator-auditable and inspectable.

## 6. Current proven instances and watch-items

**Proven instances** (the concrete seams O1–O5 must cover):

- DeepMemoryEcho presence-only source resolution;
- motif-member presence-only resolution before derived identity-anchor emission;
- caller-visible payload spread on `/agent/query` and MCP query;
- raw diagnostic and provenance surfaces with caller-reentry capability;
- safe-but-silent orphan suppression.

**Watch-items only** (no obligation, no repair authorized in P4):

- spirit-reflection cooldown-key collision under `eid` reuse;
- collective source trails;
- stored node-to-node edges with no current cognition/governance reader.

Watch-items do not authorize repair work inside P4. They stand as anti-drift guards: before any future cognition-facing reader of these surfaces lands, the relevant sameness/attribution obligation must land first.

## 7. ReaderPolicy relationship

P4 obligations are **surface-local and join-local**. They constrain any future family-bound ReaderPolicy implementation, but they do **not** instantiate a centralized reader engine. ReaderPolicy remains a contract noun, not a runtime authority introduced by P4.

## 8. Later-owner routing

- **P5a:** recovery, reconciliation, quarantine semantics, orphan recovery UX, stored-edge repair adjacency.
- **P5b:** portability and durability mechanics.
- **P6:** identity carrier mechanics, fingerprints, serialization, allocator durability, IntegrityManifest mechanics, TORMENT-specific governed-memory substrate mechanics, packaging-boundary evaluation.
- **P9:** migration execution and architecture-wide promotion.
- **Maintenance lane:** CodeQL complaints; orphan-observability counter implementation; allowlist regression lock; identity/character-state atomic-save fix.

## 9. Values-layer posture

**Ratified values-layer posture (Hilmir, 2026-06-09).** When runtime source-sameness cannot be proven, the reference defaults to **`diagnostic_only` cognition eligibility** until an explicit audited governance action restores eligibility, while remaining **operator-auditable, inspectable, and recoverable**. Ordinary model-facing notice is not required by default. This does not authorize output blocking, invisible evidence deletion, permanent eligibility lock, or invisible finalization.

`diagnostic_only` is an eligibility posture, not a projection instruction. It does not itself require diagnostic exposure; any diagnostic projection remains governed by O3 and O4 and does not by itself confer cognition eligibility.

This posture is the values-layer answer that O5 and the §5 invariant are read against; it closes the one operator decision required before P4 wording closure.

**Still parked (mechanics, not values):**

- the exact disclosure-channel mechanics;
- whether any reflective or diagnostic context receives a shaped notice;
- the restoration-event schema and governance mechanics.

P4 selects no implementation mechanism for any of these.

## 10. Non-decisions preserved

```
no implementation            no runtime patch             no tests
no executable probe          no identity-token choice     no UUID or ULID choice
no fingerprint algorithm     no canonical serialization   no allocator mechanics
no manifest mechanics        no database or SQL selection no substrate mechanics
no packaging decision        no motif redesign            no stored-edge repair
no migration execution       no quarantine design         no recovery UX
no orphan-counter impl       no disclosure-channel default no allowlist edit
no FILTER-A change           no endpoint removal          no MCP-resource rerouting
no ReaderPolicy implementation  no maintenance work       no CodeQL work
```

---

## Appendix A. Extraction ledger

How the five clauses and the invariant were distilled from the corrected framing report (v0.1-rev1). No new archaeology was opened; every clause traces to an existing grounded section.

- **O1 ← framing §3** (DeepMemoryEcho presence-only beta filter `fabric.py:3708–3710`; FILTER-A orthogonal; H-1 reuse). Distilled to the bare requirement; dropped all file:line and mechanism discussion.
- **O2 ← framing §4** (`_maybe_emit_identity_anchor` resolves member eids by presence `fabric.py:1435`, distills into durable `identity_anchor`). Distilled to the requirement; carried the corrected "family-bound adequacy standard, no central mechanism" wording from rev1.
- **O3 ← framing §5** (raw deep endpoint `app.py:2218–2233` diagnostic-but-reenterable; MCP resources bypass Spine). Distilled to the intent+capability rule; carried the rev1 MCP-query-vs-resources distinction.
- **O4 ← framing §6** (`**payload` spread on `/agent/query` + MCP query `memory_graph.py:416`; explicit-allowlist counter-pattern). Distilled to the projection-gating rule; dropped the allowlist evidence.
- **O5 ← framing §7** (safe-but-silent orphan suppression; bare `continue`). Distilled to the three observability requirements; carried the rev1 "no shaped-notice / no disclosure-channel decision here" guard.
- **Invariant ← framing §10 + §13 invariant** (shape-not-seize E9, audit-observes E5, non-coercion E10). Carried verbatim as the contract-wide governor; explicitly *not* a sixth obligation.
- **§3 distinctions ← framing §2 definitions + §9 ReaderPolicy relationship.**
- **§6 proven instances / watch-items ← framing §2 table, §8 light pass, §2 [GENERALIZATION].**
- **§8 routing ← framing §11; §9 values ← framing §12; §10 exclusions ← framing §14** (including rev1 additions: SQL, substrate, packaging, quarantine, recovery UX, orphan-counter, endpoint-removal, maintenance, CodeQL).

All sentences grounded; no clause required reopening code archaeology.

---

## Appendix B. Wording-closure ledger (extraction draft → promoted)

**Codex four-point wording corrections applied:**

1. **§5 invariant** — replaced ambiguous "silent blocking, deletion, invisible suppression" with "silent output blocking, invisible deletion of evidence, covert unauditable suppression of evidence or eligibility state, authority seizure, or personality lock," and added the explicit permission: prompt-silent non-admission is allowed when the reference stays operator-auditable and inspectable.
2. **O4** — added: deliberate diagnostic projection is permitted when explicit and surface-classified, and does not by itself make the projected data cognition-eligible retrieval.
3. **O2** — first sentence now reads "…proven under the applicable family-bound source-sameness adequacy standard."
4. **O5** — parked-mechanics line now reads "P4 does not select a shaped model-facing notice, disclosure channel, ledger format, event schema, counter, quarantine record, or recovery UX."

**Hilmir values-layer confirmation carried:** §9 converted from "flagged but not decided" to a ratified posture — unprovable runtime source-sameness defaults to `diagnostic_only` eligibility until an explicit audited governance action restores it, while remaining operator-auditable, inspectable, and recoverable; no default model-facing notice; no output blocking, invisible deletion, permanent lock, or invisible finalization.

**GPT final steering clarification carried (§9):**

```
diagnostic_only eligibility posture
!=
diagnostic projection instruction
```

`diagnostic_only` is an eligibility posture, not a projection instruction; any diagnostic projection remains governed by O3 and O4 and does not by itself confer cognition eligibility.

**Parked mechanics preserved:** disclosure-channel mechanics; whether reflective/diagnostic context receives a shaped notice; restoration-event schema and governance mechanics. §10 exclusions unchanged.

**No architecture change:** five obligations + one invariant, section structure, routing, and exclusions are identical to the extraction draft. Changes from candidate → promoted are wording, the §9 values-layer ratification, the §9 eligibility-vs-projection clarification, and the promoted header/status.

---

*End P4 Reader and Projection Safety Contract v0.1. Requirement-level design contract, docs-only. No implementation, substrate mechanics, or migration authorized. Amendments are small docs slices with trio sign-off.*
