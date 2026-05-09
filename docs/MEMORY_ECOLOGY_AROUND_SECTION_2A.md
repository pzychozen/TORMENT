# Memory Ecology Around §2A

**Status:** Historical design record / explanatory doctrine.
**Scope:** Conceptual map only. Names and connects work that already shipped. Does not change any runtime behavior, gate, or threshold.
**Parent docs:**
- [`SECTION_2A_VALIDATION_FRAMING.md`](SECTION_2A_VALIDATION_FRAMING.md) — what §2A tests
- [`SECTION_2A_EVALUATION_SET_v1.md`](SECTION_2A_EVALUATION_SET_v1.md) — the seeded corpus and queries
- [`REINFORCE_CONTRACT_FRAMING_v2.4.x.md`](REINFORCE_CONTRACT_FRAMING_v2.4.x.md) and [`REINFORCE_CONTRACT_IMPLEMENTATION_PLAN_v2.4.x.md`](REINFORCE_CONTRACT_IMPLEMENTATION_PLAN_v2.4.x.md) — per-memory significance
- [`CHARACTER_SYSTEM.md`](CHARACTER_SYSTEM.md) — character tiers, anchors, drift

---

## 1. Purpose

§2A is described in its own framing doc as a "behavioral retrieval-shaping change." That is true at the runtime layer, but it understates what was actually built around it.

Across one work day (2026-04-16) the §2A landing chain produced not a single memory store but a **layered memory ecology** — a controlled environment for testing how TORMENT balances dense private recall, identity stability, background context, deep retrieval, fast non-expansion, and derived-anchor hygiene against advisory lane shaping.

The individual pieces are documented in the framing doc, the eval-set doc, the reinforce-contract docs, and the v2.4.4 release notes. This document exists so a contributor reading the docs cold can see that those pieces form one system, in what order they were added, and why each layer matters.

It does not introduce new policy. It is a **map** over existing **terrain**.

---

## 2. Build-order timeline

All eight commits landed on **2026-04-16** in `torment_fabric`. The tight cluster is intentional: each commit unblocked the next in a single-day validation push that ended with §2A advisory shaping flipped to default-on.

| # | Commit | Time (UTC) | What it added |
|---|--------|------------|---------------|
| 1 | `c3c2252` | 11:51 | Bucket 1 minimum-viable seeded corpus: A-01..A-05 anchors, C-01..C-07 dense core-private cluster, three B1 queries, §9 doctrine. |
| 2 | `cc4c3b1` | 12:14 | C-cluster density 7 → 9 (added C-08, C-09); cooled identity-adjacent phrasing in C-02 / C-03 / C-07; B1-01 / B1-02 materiality corrections; B1-03 control-query revision. |
| 3 | `3331a18` | 12:31 | Identity-adjacent surround §10.4 (P-01..P-04) + environmental / deep-adjacent surround §10.5 (D-01..D-04). Total seeded corpus reaches **22 memories**. |
| 4 | `74ccba1` | 12:52 | D-03 token-sanitization (TORMENT name removed) and D-04 phase-transition reframe — surround hardening after pressure-testing the embedder. |
| 5 | `71368dd` | 15:39 | §10.6 anchor snapshot from a clean `ws_section_2a_v2` instantiation; workspace-id bumped to v2 for reproducibility. Adds `tools/instantiate_section_2a_eval.py`. |
| 6 | `a0fd7b4` | 21:45 | Anchor hygiene: `derived_identity` tier, provenance tagging on emitted anchors, anchor-boost filtering, drift-measurement separation of derived vs core. First runtime change in the chain. |
| 7 | `ea07744` | 22:47 | Controller-surface widening: `RELATIONAL_HINT_WORDS`, `ANALYTICAL_DEPTH_HINT_WORDS`. Unblocks Bucket 2 (0/18 → 18/18 RETRIEVAL) and Bucket 3 (0/16 → 15/16 REFLECTIVE). |
| 8 | `6dbd0e0` | 23:29 | Final §2A eval validation across baseline + two patched states; advisory eligible for default-on. Default flipped in `spine.py` / `app.py`. |

Items 1–5 are doc-only corpus work. Item 6 is the only commit in the chain that changed runtime semantics in service of the eval. Items 7–8 close the validation loop.

---

## 3. The nine ecology layers

The ecology has **nine** named layers. Five describe **kinds of memory** that exist in the seeded corpus or in real workspaces; three describe **doctrinal mechanisms** for keeping those kinds from contaminating each other; one is a **non-expansion guard** that protects the same boundary from the other direction.

| # | Layer | Kind | One-line role |
|---|-------|------|---------------|
| 1 | Reinforced memory | mechanism | Per-memory significance grows from successful use (`reinforcement_count`, additive log-scaled rank-stage boost). |
| 2 | Identity anchor memory | kind | Seed-canon character anchors (`mtype="seed_canon"`, deep half-life, canon=True) — the deepest basin. |
| 3 | Core private project memory | kind | Dense same-domain project-history cluster (the C-cluster); pressures the `top_k=8 → core lane budget=6` truncation risk. |
| 4 | Cooled phrasing hygiene | mechanism | Project memories deliberately stripped of identity-coloured wording so Bucket 1 recall does not also reinforce Bucket 4 anchors. |
| 5 | Identity-adjacent private surround | kind | Personal habits / preferences (the P-band) — present and retrievable, but explicitly not anchors. |
| 6 | Environmental background memory | kind | Ambient world facts (the D-01 / D-02 environmental sub-band) — climate, neighbourhood, etc. |
| 7 | Deep-adjacent earlier-work memory | kind | Distanced earlier technical history (the D-03 / D-04 sub-band) — useful for deep retrieval but token-sanitised so it does not pull on current-project queries. |
| 8 | Fast operational non-expansion guard | mechanism | Bucket 5 verifies that simple prompts stay FAST and do not unnecessarily open relational / deep / identity lanes. The opposite of layers 3 and 7. |
| 9 | Derived identity memory | mechanism | Auto-emitted identity-like anchors classified into a separate `derived_identity` tier so they cannot equal seed canon. |

Each layer maps to a documented section of the eval set and / or a runtime construct in `torment_service/character.py`.

---

## 4. Corpus composition summary

Seeded corpus on `ws_section_2a_v2` / `ryuki_eval`:

| Band | Section | Items | Count |
|------|---------|-------|-------|
| Identity anchors | §10.2 | A-01, A-02, A-03, A-04, A-05 | 5 |
| Core-private C-cluster | §10.3 | C-01, C-02, C-03, C-04, C-05, C-06, C-07, C-08, C-09 | 9 |
| Identity-adjacent | §10.4 | P-01, P-02, P-03, P-04 | 4 |
| Background / deep-adjacent | §10.5 | D-01, D-02, D-03, D-04 | 4 |
| **Total** | | | **22** |

That is **5 + 9 + 4 + 4 = 22**. The composition is ratified — each band has its own design rationale and guardrails in the eval-set doc. The total is recorded here so it can be cited without re-counting.

---

## 5. The `top_k` / advisory relationship

Bucket 1 was designed around one specific risk: under flat baseline retrieval, `/agent/query` defaults to `top_k=8`. Under advisory, the **core lane budget shrinks to 6** (per [`SECTION_2A_VALIDATION_FRAMING.md`](SECTION_2A_VALIDATION_FRAMING.md) §2.4 and §4.1). If a private-heavy query has more than six genuinely relevant private memories, advisory may silently lose useful recall before ranking even occurs.

The C-cluster therefore had to satisfy two conditions at once:

1. produce **strictly more than six** semantically distinct hits on broad project-history queries (so the `8 → 6` shaping has something to drop, and the loss is observable);
2. give that count **real margin** against embedder-level semantic collapse — i.e. the cluster cannot rely on perfect separation of seven items inside a floor-level cluster.

This is why the cluster grew from seven memories at `c3c2252` to nine at `cc4c3b1`. The §10.3 preamble lists the nine orthogonal angles: kernel (C-01), architectural breakthrough (C-02), discipline (C-03), process framing (C-04), technical debugging (C-05), process validation (C-06), architectural vision (C-07), voice-layer landing (C-08), and seed-to-canon (C-09).

---

## 6. Embedder hardening lesson

Token sanitization in D-03 (commit `74ccba1`) generalises into a doctrine point worth recording on its own:

> Dense embedders may not respect negation or temporal distancing as strongly as literal token overlap. Prose like "before X" or "unrelated to X" can still pull toward queries that mention X, because the literal token presence dominates the prose-level negation signal under BAAI/bge-small-en-v1.5 and similar BGE-class small models.

**Practical rule:** for surround memories whose role is *"nearby but not retrievable for this query family,"* token economy beats prose negation. Remove or avoid the literal target token rather than relying on explanatory negation.

D-03's first revision used GPT's structurally-correct draft ("before any TORMENT work...") and still pulled toward B1 queries during pressure-testing. The token-sanitised variant — *"Years before any agent or memory-system work..."* — drops the literal `TORMENT` token while preserving temporal distance and explicit architectural separation, and that is what was ratified.

D-04 is the tighter phase-transition framing of the same lesson applied to language-history surround.

This rule is recorded in the eval-set doc as §10.7 and lives here as the generalisation.

---

## 7. Derived identity summary

The `a0fd7b4` patch addresses a problem that surfaced during the §10.6 anchor snapshot work: the contaminated v1 workspace auto-emitted an identity anchor from the P-02 / P-03 / P-04 personal-habit motif clustering, because doubled corpus inflated motif membership counts and tripped `_maybe_emit_identity_anchor` spuriously.

The patch separates auto-emitted anchors from seed canon at the tier layer rather than removing the auto-emission path:

**Tier classification** (`torment_service/character.py::classify_tier`):
- `mtype="identity_anchor"` and `canon=False` → tier `derived_identity`
- `mtype="seed_canon"` or canon-true identity_anchor → tier `core_identity` (unchanged)

**Tier weights** (`CharacterSeed` defaults, all absolute):

| Tier | Absolute weight | Relative to relational |
|------|-----------------|------------------------|
| `core_identity` | 0.50 | 1.43× |
| `derived_identity` | 0.42 | **1.20×** |
| `relational` | 0.35 | 1.00× (baseline) |
| `situational` | 0.15 | 0.43× |

The derived tier sits **below seed canon and above relational** — derived anchors are useful and remain in the identity block, but cannot equal canon weight.

**Anchor boost filtering** (`fabric.query` / `fabric.trace`): the full anchor boost is restricted to `seed_canon`, `drift_correction`, and **canon** identity_anchors. Derived (non-canon) identity anchors fall through to tier-based classification only.

**Drift measurement separation** (`character.py::measure_drift`): the function now passes `mtype` and `canon` through to `classify_tier` and returns `derived_count` as a separate counter from `core_count`, so derived anchors do not inflate the core-tier count and trigger spurious "stable" readings.

**Provenance tagging** on emitted anchors (`_maybe_emit_identity_anchor`):
- `anchor_origin` — where the anchor came from
- `seed_aligned` — whether the cluster aligns with the seed motif
- `seed_overlap_count` — overlap measure with seed-canon members
- `anchor_source` — e.g. `motif_cluster`
- `source_member_eids` — the eids that produced the emission

Twelve contract-invariant tests in `tests/test_anchor_tier_hygiene.py` lock the tier semantics. `tests/test_retrieval_assembler.py` was updated for canon-aware classification.

The full design rationale is in `CHARACTER_SYSTEM.md` ("Canon anchors vs derived identity anchors"); this section is the §2A-anchored summary.

---

## 8. Failure modes this ecology prevents

The nine layers map onto a small set of concrete failure modes that each layer was added to prevent.

- **Private recall loss hidden by advisory shaping** — addressed by Bucket 1's `>6 relevant hits` design + nine-angle C-cluster (layers 2, 3, 5).
- **Identity anchors accidentally reinforced by project-memory wording** — addressed by cooled phrasing in C-02 / C-03 / C-07 + identity-adjacent surround guardrails (layers 4, 5).
- **Background memories polluting core recall through token overlap** — addressed by D-03 token sanitization and the surround guardrail set (layers 6, 7).
- **Auto-emitted anchors overpowering seed canon** — addressed by the `derived_identity` tier + boost-filtering + drift-measurement separation (layer 9).
- **Fast prompts unnecessarily opening deep / relational / identity lanes** — addressed by Bucket 5's non-expansion verification (layer 8).
- **Per-memory significance unobservable in retrieval** — addressed by the reinforce-contract additive log-scaled rank-stage boost (layer 1).
- **Semantic eval becoming irreproducible** — addressed by the synthetic-but-canonical `ws_section_2a_v2` workspace-lock policy and the §10.6 pre-run anchor snapshot.

If any of these failure modes recurs in future work, the corresponding layer is the right place to look first.

---

## 9. What this document does not do

- It does not change any runtime behavior, threshold, or default.
- It does not redefine §2A — see [`SECTION_2A_VALIDATION_FRAMING.md`](SECTION_2A_VALIDATION_FRAMING.md).
- It does not duplicate the per-entry corpus content — see [`SECTION_2A_EVALUATION_SET_v1.md`](SECTION_2A_EVALUATION_SET_v1.md).
- It does not authorize any new mechanism. New layers or weight changes still require their own ratification.

It exists so the layered system stays visible after the build day fades from working memory.
