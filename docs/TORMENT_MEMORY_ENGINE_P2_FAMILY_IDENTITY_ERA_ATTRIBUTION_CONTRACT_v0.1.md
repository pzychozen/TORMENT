# TORMENT Memory Engine — P2: Family Identity and Era Attribution Contract v0.1

**Status:** RATIFIED P2 CONTRACT — promoted by trio decision 2026-06-07. Design-only: defines vocabulary and obligations, authorizes no implementation, no H-1 patch, no identity-token selection, no fingerprint-algorithm selection, no storage-product selection, no adjacent gate opening.
**Gate:** P2 — Family Identity and Era Attribution Contract (deliberately opened by trio decision, 2026-06-07).
**Posture:** design-only · audit-first · bounded · no implementation · no H-1 patch · no identity-token/fingerprint-algorithm/storage-product selection · no adjacent gate opening.
**Anti-drift reference:** `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md` (as amended 2026-06-07; P2-closure registry amendment is a separate slice).
**Interpretation contract:** `docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md`.
**Evidence base:** P2 opening survey (2026-06-07) + H-1 disposable Windows characterization (operator-run, 2026-06-07, `H1_CONFIRMED`).
**Lineage:** P2 opening survey → P2 contract draft + pushback → Codex adversarial review (*sound with required corrections*) → corrections applied → final wording micro-corrections → Hilmir lost-anchor values-layer ratification → trio promotion.
**Tagging:** [FACT] · [CONTRACT-CANDIDATE] · [POSTURE] · [RISK] · [PARKED] · [NON-DECISION] · [QUESTION] · [RECOMMENDATION]. No silent promotion between tags. (Tags retained from the ratified draft; "[CONTRACT-CANDIDATE]" denotes the now-ratified contract clauses.)

---

## 1. Executive summary

P1 obligated every post-genesis durable object to a valid era-attribution path and forbade laundering unattributable objects into `legacy_precontract`. The H-1 characterization then demonstrated, on a real Windows run of the real loader, allocator, deep store, and beta-filter predicate, that the obvious anchor for honoring that obligation — `eid` — is **a reusable local integer label, not durable identity** [FACT]. The whole revalidation chain was reproduced: clean trailing-row loss → allocator re-derivation → integer reuse by an unrelated memory → stale deep echo (old summary, old `affect_tag`) becoming presence-valid against the new memory.

This contract builds on one corrected axiom (§2), an explicit **three-axis identity model** (§3), and the conflict/failure vocabulary that lets P1's hard rule be enforced for the core family. In one sentence: `eid` is retained as the load-bearing **local graph handle** and is never again allowed to stand alone as evidence of sameness or era membership; **memory-lineage identity** and **record-revision identity** (plus a checkable **revision fingerprint**) are the durable axes that make sameness checkable; and the legacy corpus is bound by a **Genesis Baseline profile of IntegrityManifest** whose membership proof is revision fingerprints, never bare eid ranges. All mechanics — allocators, fingerprint algorithms, manifests-on-disk, echo-side checking, clone reconciliation, projection filtering — remain parked with named owners (§10, §13, §15).

The contract guarantees **checkability and detectable failure**; it does not promise survival. Survival, replication, and durability are P6's.

---

## 2. Axiom

[CONTRACT-CANDIDATE]

> A durable identity-dependent claim must never silently succeed when the evidence required to validate it is missing, truncated, conflicting, or attached to a reused local handle. The claim must either validate from durable evidence or fail detectably into an explicit non-cognition posture.
>
> P2 defines the required evidence and the failure vocabulary. P6 defines survival, replication, and durability mechanics.

Distinction preserved:

- **P2:** checkability · detectable failure · failure vocabulary.
- **P6:** survival · replication · durability mechanics.

[NON-DECISION] Scope guard: this axiom governs **identity-dependent claims** (sameness, era membership, echo→source linkage, cursor→corpus ordinality). It is **not** a mandate to validate every historical read, and it does not authorize re-reading or re-validating the corpus at runtime — instantiation of any check is owned by a later phase.

---

## 3. Identity vocabulary (three-axis model)

The earlier phrase "declared stable record identity" was structurally ambiguous and is withdrawn. Replaced by an explicit, separable model [CONTRACT-CANDIDATE throughout]. Each axis is distinct; merging any two is drift.

**Local graph handle (`eid`).** The per-graph integer used for joins (entities map, deep store keys, embedding maps, sidecar rows, migration cursor ordinals). Retained · load-bearing · reusable · operational join key · **never sufficient evidence of sameness or era membership** post-H-1.

**Memory-lineage identity.** Identity of one evolving memory across its legitimate updates. Stable across legitimate revision (a memory that is reinforced, re-classified, or patched keeps one lineage identity). Binds authored revisions to one evolving memory lineage. Separate from `eid` (a recycled handle does not transfer lineage; a relocated record keeps it).

**Record-revision identity.** Identity of one immutable authored appended revision. Binds exactly one revision. Separate from lineage identity (one lineage has many revision identities over time). Paired with a revision fingerprint or equivalent checkable evidence.

**Revision fingerprint.** Checkable evidence binding the *immutable authored meaning of one revision*. Not evolving-object state · not truth · not authority. (Algorithm, serialization, and field names deliberately unselected — §15.)

**Record vs object distinction (preserved):**

- **Record** = one immutable authored appended revision (one `nodes.jsonl` line, in current substrate terms — but the contract speaks of revisions, not file lines).
- **Object / memory lineage** = the evolving last-wins memory represented by multiple revisions over time.

[NON-DECISION] No field names, UUID/ULID choices, hash functions, serialization algorithms, or storage layouts are selected here. The axes are roles; their realization is P6.

[RISK] Existing conceptual merges P2.5/P4 must inherit explicitly (no code change here): deep store merges identity with join-validity (borrowed eid); archive merges identity with creation time (`doc_{title}_{ts}`); embedding map merges identity with storage position (`{shard,row}`).

---

## 4. Hybrid identity posture

[CONTRACT-CANDIDATE] Post-genesis MemoryNode authored revisions carry, at contract level, requirements for:

- `era_ref` (P1 vocabulary);
- **memory-lineage identity**;
- **record-revision identity**;
- **revision fingerprint** or equivalent checkable revision evidence.

Clarifications:

- `eid` is **retained as the local handle** and is **never sufficient durable historical identity**.
- A **legitimate update** produces a **new record-revision identity** under the **same memory-lineage identity**.
- A **new unrelated memory** receives a **new memory-lineage identity**, even if its local `eid` is recycled — this is precisely the H-1 case, and the lineage axis is what makes the grocery-list memory distinguishable from the dragon memory despite the shared handle.

Ruled out by H-1: `eid` as durable identity (demonstrated, §1). eid-only and eid+durable-allocator-state are insufficient as the P2 answer — the first fails sameness, the second is P6 mechanics and still does not prove revision sameness. The hybrid is the smallest combination satisfying §2.

---

## 5. DeepMemoryEcho source-evidence requirement

[CONTRACT-CANDIDATE] At contract level, a DeepMemoryEcho must preserve enough source evidence for future checking:

- source local handle;
- source family;
- source memory-lineage identity;
- source record-revision identity **or** revision fingerprint;
- source `era_ref`.

This evidence is copied at export under P1's verbatim-or-omit nested-projection rule (§3.4 of P1) and is **not re-synthesized on read**.

[PARKED → P4] P4 owns: echo-side source-sameness validation mechanics · diagnostic fencing · projection filtering · model-facing surfacing. [NON-DECISION] No mechanics designed or implemented here. The H-1 demonstration that presence-only validation is insufficient [FACT] is the requirement's motivation, not a design of the check.

---

## 6. Genesis Baseline profile of IntegrityManifest

[CONTRACT-CANDIDATE] **Noun:** the genesis baseline inventory is the **Genesis Baseline profile of IntegrityManifest** — IntegrityManifest is an already-accepted first-class noun with deliberate headroom (registry §H); this is a profiled use, not a new noun.

**Special interpretation role (stated explicitly):**

- derive `legacy_precontract` membership;
- bind the pre-contract baseline;
- make handle reuse detectable;
- fail visibly when unverifiable.

**Fingerprint contract:**

- bind **immutable authored record revisions**;
- do **not** bind evolving MemoryNode objects (last-wins mutation rots object-level fingerprints) [RISK];
- expressed in **canonical-serialization** language at the contract level, **not** "bytes-as-written" (bytes are a substrate concern; the contract names the property, P6 names the serialization).

**Serialization-era validity clause** [CONTRACT-CANDIDATE]:

> A revision fingerprint is valid only relative to a declared serialization era or serialization profile. Unknown, mismatched, or unverifiable serialization context must never silently validate an identity-dependent claim.
>
> P2 fixes the obligation. P6 owns serialization mechanics and algorithm selection. P2.5 checks cross-contract conformance.

[NON-DECISION] Boundary preserved: no hash algorithm selected · no serialization format selected · no runtime check designed · no manifest mechanics opened. The clause exists because serialization has already drifted historically (dual embedding formats; governance-less legacy chunks) — a fingerprint whose serialization context is unknown is unverifiable evidence, and §2 forbids unverifiable evidence from silently succeeding.

**Honest bounds (stated clearly):**

- "last record per eid at genesis" is a **baseline snapshot of then-current authoritative revisions only** — **not** proof that no pre-genesis eid reuse ever occurred before the snapshot;
- **bare eid match is never sufficient membership proof**;
- **eid match without revision-fingerprint match is handle-reuse evidence**, routing to the §7 posture.

**Membership rule** [CONTRACT-CANDIDATE]: a revision is `legacy_precontract` iff its revision fingerprint matches a Genesis Baseline entry. Object-level reading: an object whose latest revision is post-genesis is interpreted under that revision's era; its genesis-matched earlier revisions remain legacy history — mixed-era lineages are **representable and auditable**, not forbidden.

**H-1 safety check:** the demonstrated attack (post-genesis grocery-list revision wearing recycled eid 3) fails membership — no fingerprint match — and must then carry its own valid attribution or fall to the §7 posture. Bare-eid laundering is closed at the vocabulary level [FACT-grounded design claim].

[PARKED → P6] Manifest construction tooling, storage, replication, and verification CLI (Cluster 5 §6.2 BRAINSTORM-MANIFEST-LAYER / VERIFY-CLI adjacency — named, not opened). P2 requires only that the profile be **fail-loud verifiable**; it must not become a new silent single point of failure (manifest-single-copy fragility, Cluster 5 §5.6) [RISK].

---

## 7. Conflict and failure posture

[CONTRACT-CANDIDATE] All outcomes use P1's ReaderPolicy vocabulary; none mutates canonical fact, ratifies truth, or creates protection/authority.

| State | Posture |
|---|---|
| Dangling `era_ref` (names no ledger event) | `diagnostic_only` or `quarantine`; never silent admission; never legacy fallback |
| `era_ref` vs ledger-evidence conflict | fail closed to `quarantine`; **no silent resolution in either direction**; resolution is an explicit later governance event [PARKED → P5a] |
| Reused local handle detected (fingerprint mismatch vs inventory or vs echo's source copy) | record stays readable; the *join* is flagged: joined artifacts (echo, edge) drop to `diagnostic_only` pending explicit classification |
| Unattributable post-genesis revision | P1 hard rule verbatim: `diagnostic_only`/`quarantine`; **never** `legacy_precontract` |
| Genesis Baseline manifest unavailable/unverifiable | **lost-anchor posture — Hilmir-ratified (§11)**: legacy records stay readable/inspectable/recoverable; unverifiable `legacy_precontract` claim → `diagnostic_only`, never silent suppression or deletion |
| Mixed-era lineage (legacy revisions + post-genesis updates) | representable; interpreted under latest revision's era; history auditable (§6) |

No hidden authority: none of these may be implemented as silent output suppression; surfacing/observability shape is P4's [PARKED].

---

## 8. Edge attribution

[CONTRACT-CANDIDATE] An **edge record is its own durable assertion**, not a shadow of its endpoints.

- A **post-genesis edge requires its own family attribution route** (`era_ref` + the applicable identity/fingerprint evidence for an edge record).
- **Endpoint identity / revision evidence validates linkage only** — it confirms the edge points at the intended revisions.
- **Endpoint eras do not silently determine edge era.** An edge asserted in a later era between two legacy-era endpoints is a later-era assertion about historical material, and must be attributable as such.

[PARKED] Edge-repair and dangling-linkage mechanics (detection via endpoint fingerprint mismatch is *possible* at vocabulary level; instantiation later).

---

## 9. Migration-cursor classification

[FACT/RISK] The migration cursor is **eid-keyed and sorted-eid/ordinal-shaped** (`migration/cursor.py:40–54`), and is therefore an **identity-contract hazard under handle reuse**: its "highest terminal ordinal" resume assumption is monotonic only absent tail-loss, which H-1 violates.

Routing: migration **execution** → **P9**; recovery adjacency → **P5a**. [NON-DECISION] No repair designed here. Post-P2 cursor semantics *may* reference record-revision identity instead of bare ordinal; that is a P9 design input, not a P2 decision.

---

## 10. Clone representability boundary

[CONTRACT-CANDIDATE] Identity travels with revisions (lineage identity, revision identity, fingerprints are revision-resident), so a cloned workspace contains revisions with **identical identity and provenance but different workspace membership** — the honest description, not a defect. P2 requires only **representability**: the vocabulary can state "workspace W₂'s revisions share lineage with W₁ as of declaration D."

[CONTRACT-CANDIDATE] `era_note` **remains interpretation-neutral** and must **not** be silently reused as the semantic lineage carrier. A dedicated semantic lineage event kind **may later be proposed through registry-amendment discipline**; **no new event kind is adopted by this contract** [QUESTION Q3].

[PARKED → P5a] Inherit-vs-redeclare semantics · workspace-incarnation mechanics · ledger-copying rules · reconciliation.

## 11. Lost genesis-anchor posture (Hilmir-ratified)

[CONTRACT-CANDIDATE] [HILMIR VALUES-LAYER — RATIFIED 2026-06-07]

> If the Genesis Baseline IntegrityManifest profile is missing, unreadable, or unverifiable: legacy records remain readable, inspectable, operator-visible, and recoverable; they are not deleted and not silently suppressed. But their unverifiable `legacy_precontract` claim does not silently remain cognition-eligible — default `diagnostic_only`. A later explicit recovery or governance action may restore classification.

Standing distinctions [CONTRACT-CANDIDATE]: `diagnostic_only` ≠ deletion · `diagnostic_only` ≠ invisible suppression · readability remains · inspectability remains · operator visibility remains · later explicit recovery remains possible.

This is the values-layer answer to "how hard does the past fail when its anchor is lost": it honors both "do not silently discard meaningful history" and "do not silently grant authority an artifact never earned." Ratified by Hilmir; the drafters do not revise it.

## 12. Model-facing influence boundary

[FACT] Any revision-resident field — lineage identity, revision identity, fingerprint, `era_ref` — automatically surfaces in retrieval hits (`**payload`, `memory_graph.py:405–417`) and trace hits (`fabric.py:6639–6660`). [CONTRACT-CANDIDATE] P2 records the adjacency and the rule *that a deliberate decision must be made*; the decision — what is model-visible, audit-only, or filtered at which surface — is **owned by P4**. Revision-residence is **not** implicit permission for model visibility [RISK if ignored].

## 13. Write-site conformance ownership

[CONTRACT-CANDIDATE] Responsibility is named so the contract cannot be ratified and then never written-to:

- **P2:** states the **abstract write-side obligations** (which authored revisions must carry which evidence).
- **P2.5:** owns **cross-contract write-site conformance review** — inventory writers, confirm required fields, identify gaps, assign implementation owners.
- **Later per-family slices:** implement stamping.
- **P4:** reader and projection enforcement.
- **P6:** substrate mechanics.

[NON-DECISION] Naming this responsibility does **not** open P2.5.

## 14. Family attribution matrix

**Class C — eid-keyed core (deep treatment):**

| Family | Identity posture | Era attribution | Notes |
|---|---|---|---|
| MemoryNode revisions | hybrid (§4): handle + lineage identity + revision identity + fingerprint | explicit `era_ref` per post-genesis revision; Genesis Baseline membership for legacy | record/object distinction (§3); `**payload` surfacing → P4 (§12) |
| Edges | edge record is its own assertion (§8) | own family route; endpoints validate linkage only | dangling-after-reuse detectable; repair parked |
| DeepMemoryEcho | borrowed handle + source-evidence copy (§5) | source `era_ref` copied at export | presence-only insufficient [FACT]; sameness checking → P4 |
| Embedding map rows | positional refs remain derived data; identity-carrying is a P6 question [Q5] | derived; re-derivable | never an identity root |
| Migration cursor | §9 | `migration_run` EraEvents (P1 §8) | hazard recorded; execution P9 |

**Class A — uuid + append-order ledgers (cheap tabular ratification)** [CONTRACT-CANDIDATE]: collective packets/events, closures (+ events), environment, references, conflicts, batons, proposals, contest ledgers. Identity: existing uuid-grade ids ratified as canonical lineage identity (collision-safe, copy-stable). **Many Class A append-only families have effectively one authored revision per identity, so lineage and revision identity may coincide. Explicitly versioned families such as closures (which mint separate `closure_` and `version_` ids, `closure_memory.py:270,274`) must preserve separate lineage and revision axes where their existing vocabulary requires it.** The family table records the distinction; P2 does not flatten it for convenience, and does not widen into closure redesign. Era: explicit `era_ref` on new entries **or** deterministic ledger join where append order is the family's own anchor — per-family choice deferred to each family's first post-P2 write-site slice, default explicit `era_ref` [POSTURE]. Genesis: id enumeration in the manifest.

**Class B — single-writer stores (cheap tabular ratification)** [CONTRACT-CANDIDATE]: SeedRecord (`seed_id` + fingerprint; import collisions become visible), archive docs/chunks (existing ids ratified **with** the recorded caveat that embedded timestamps are bookkeeping, never attribution anchors [FACT/H-7]), motifs (ids ratified; 4-path layout probe recorded as a genesis observation).

**Explicit exclusions:** checkpoints (P3 instantiates identity/era under P1+P2 vocabulary); SQLite sidecar + derived diagnostics (re-derivable; no identity root); embedding substrate internals (P6); IntegrityManifest *mechanics* (P6).

## 15. Parked downstream mechanics table

| Mechanic | Owner |
|---|---|
| Identity-token technology (UUID/ULID/other), allocator design + state persistence | P6 (P2 vocabulary as constraint) |
| Fingerprint algorithm, canonical serialization, computation code | P6 (algorithm) / P2.5 (consistency check vs P1+P2 vocabulary) |
| Genesis Baseline manifest construction, storage, replication, verification CLI | P6 |
| Echo-side source-sameness checking; orphan observability; projection filtering; diagnostic fencing; model-facing surfacing | P4 |
| Clone reconciliation, quarantine procedure, recovery, conflict-resolution governance events, torn-append/duplicate repair | P5a |
| fsync, atomic append, transactions, durable append guarantees | P6 |
| Migration execution against new vocabulary; rollback execution | P9 / P5a |
| Edge-repair / dangling-linkage mechanics | P5a |
| H-1 runtime hardening of any kind | **not authorized by P2**; future separately ratified work informed by this contract |

## 16. Resolved steering questions and standing record

- **Q1 — Axiom acceptance.** Ratified (§2): checkability + detectable failure, scoped to identity-dependent claims, not all reads.
- **Q2 — Noun economy.** Ratified: Genesis Baseline profile of IntegrityManifest (no new noun) + three-axis identity as field-level vocabulary.
- **Q3 — Lineage event kind.** Deferred to registry amendment; this contract adopts none.
- **Q4 — Lost-anchor posture (§11).** Hilmir-ratified 2026-06-07.
- **Q5 — Scope trim.** Embedding-map row identity left out of P2 (noted for P6).
- **Q6 — Record/object semantics.** Ratified as vocabulary; P2.5 must reconcile it against P1's "durable object" phrasing.

## 17. Standing tension carried into P2.5

[QUESTION — open by design] **Memory-lineage identity has no current substrate carrier.** `update_payload` re-appends a full payload with no lineage field (`memory_graph.py:607–653`); today "same memory across updates" is carried *only* by the reused eid — the handle P2 demotes. The contract therefore names an axis (memory-lineage identity) that has **no current carrier**. Correct as design (P2 is vocabulary; per-family slices instantiate), but the lineage axis is **entirely aspirational** until a writer stamps it — heavier than the revision axis, which has fingerprint-able content today. This is the **headline gap** for P2.5's write-site conformance review (§13): "no lineage carrier exists yet" is a structural gap, not a footnote. Recorded here so it stays visible and is not silently solved.

---

## Appendix A — Correction ledger (Codex required correction → revised section)

| # | Codex required correction | Revised section |
|---|---|---|
| 1 | Replace split-axiom wording with the "never silently succeed / fail detectably" formulation, scoped to identity-dependent claims; preserve P2-checkability vs P6-survival; do not broaden to all reads | §2; §1 closing line |
| 2 | Replace ambiguous "declared stable record identity" with explicit three-axis model (handle / memory-lineage identity / record-revision identity / revision fingerprint); preserve record-vs-object | §3; propagated to §4–§6, §14 |
| 3 | Hybrid posture must require era_ref + lineage identity + revision identity + fingerprint; clarify legitimate-update vs new-unrelated-memory under recycled eid | §4 |
| 4 | Echo must preserve source handle/family/lineage/revision-or-fingerprint/era_ref; P4 owns mechanics | §5 |
| 5 | "Genesis Baseline profile of IntegrityManifest"; explicit interpretation role; fingerprint binds revisions not objects; canonical-serialization language not bytes-as-written; bare-eid-match never sufficient; snapshot ≠ proof of no prior reuse | §6 |
| 6 | Edge record is its own assertion; post-genesis edge needs own attribution route; endpoint eras don't silently determine edge era | §8 |
| 7 | Migration cursor: eid-keyed, ordinal-shaped, identity-contract hazard under reuse; execution→P9, recovery→P5a | §9 |
| 8 | Clone: representable now; era_note stays interpretation-neutral; semantic lineage kind only via registry amendment; no kind adopted | §10 |
| 9 | Write-site conformance: P2 abstract obligations, P2.5 conformance review, per-family slices implement, P4 readers, P6 substrate; naming ≠ opening P2.5 | §13 |
| 10 | Lost-anchor posture carried as pending until Hilmir decides; recommended default diagnostic_only, not suppression/deletion | §11; §7 row |
| 11 | Classification discipline; no silent promotion (handle→identity, lineage→revision, fingerprint→truth, inventory→authority, era→protection, diagnostic_only→deletion, representability→implementation, named P2.5 responsibility→opened gate) | applied throughout |

**Final wording micro-corrections (post-Hilmir ratification):**

| # | Final correction | Revised section |
|---|---|---|
| F1 | Serialization-era validity clause — a revision fingerprint is valid only relative to a declared serialization era/profile; unknown/mismatched/unverifiable context must never silently validate; P2 fixes obligation, P6 owns mechanics, P2.5 checks conformance | §6 |
| F2 | Class A closures exception — "lineage and revision *may* coincide" for single-revision families; explicitly versioned families (closures) preserve both axes; table records distinction, no closure redesign | §14 |
| F3 | Hilmir lost-anchor ratification — §11 pending → ratified contract wording; diagnostic_only ≠ deletion/suppression; readability/inspectability/recoverability preserved | §11, §7, §16-Q4 |

## Appendix B — Hilmir-ratification record

> **[RATIFIED — HILMIR VALUES-LAYER, 2026-06-07] Lost genesis-anchor posture (§11).** The lost-anchor default — legacy records remain readable/inspectable/operator-visible/recoverable, never deleted, never silently suppressed; their unverifiable `legacy_precontract` claim drops to `diagnostic_only` rather than staying silently cognition-eligible; later explicit recovery or governance action may restore classification — is ratified contract wording (§11), not a recommendation.

---

**Promotion note.** Promoted docs-only (Slice A, 2026-06-07): this contract + a one-block orientation-map pointer. The decision-registry amendment recording P2 closure and the classification changes is a **separate** Slice B, preserving the registry's amendment discipline. This contract authorizes no runtime code, schema instantiation, migration, storage product, H-1 patch, or adjacent-gate opening. **P2.5 is next in the recorded graph and is not thereby selected or opened.**
