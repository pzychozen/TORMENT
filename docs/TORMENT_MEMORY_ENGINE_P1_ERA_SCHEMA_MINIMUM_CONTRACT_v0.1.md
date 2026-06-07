# TORMENT Memory Engine — P1: Era and Schema Minimum Contract v0.1

**Status:** RATIFIED P1 CONTRACT — promoted by trio decision 2026-06-07; decision-registry amendment completed in docs-only Slice B.
**Gate:** P1 — Era and Schema Minimum Contract. Design-only · audit-first · bounded · no implementation · no automatic widening.
**Date:** 2026-06-07
**Lineage:** P0 decision registry (`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`, closed at `2742949`) → Claude read-only archaeology + minimum-contract draft (2026-06-07) → Codex adversarial review → Windows historical deep-store scan (`metadata.srg` matches: 0) → GPT/Hilmir ratification of contract posture → wording-only closure pass → final steering micro-corrections → trio closure decision and this promotion → decision-registry amendment Slice B.
**Class discipline:** every load-bearing statement below is tagged **[FACT]** (code- or scan-grounded, line-cited), **[CONTRACT]** (ratified P1 clause), **[PARKED]** (later-phase question), **[MAINT]** (maintenance-lane candidate), or **[NON-DECISION]**. No silent promotion between classes.
**Authority note:** this memo defines interpretation vocabulary and reader discipline. It authorizes no code change, no schema edit, no migration, no storage product, and no phase opening. The registry changes only by amendment slice.

---

## 1. Executive summary

P1 asked one question: how does a future Memory Engine reader determine what an old durable object means, which interpretation policy applies, and whether it remains eligible for cognition — without silently reviving disabled feature influence or inventing authority?

The archaeology established that TORMENT already contains the contract's raw material — three generations of envelope versioning culminating in the fail-loud self-versioned `affect_attribution` pattern, plus a complete ratified corpus-migration vocabulary — and exactly one true zero: **era vocabulary does not exist anywhere in the codebase** [FACT]. The ratified contract therefore generalizes existing discipline and adds the missing era layer as a declared, append-only, per-workspace ledger ordered by an assigned ordinal — with era attribution explicitly bounded as *interpretation context, never authority*.

The values-layer decisions are resolved. **SRG disable honesty:** when SRG is disabled, audit, diagnostic, and provenance visibility remain allowed; direct protection, direct influence, and query-time mutation from raw `srg` are disabled; historical `srg.is_crystal` is visible but inert as a direct behavior input [CONTRACT]. **Crystal re-homing:** historical `srg.is_crystal` must not automatically become active lifecycle protection; a future, separately authorized migration may stage an auditable, contestable, reversible protection *recommendation* — never a silent conversion of an old heuristic into lifecycle truth [CONTRACT, Hilmir-ratified].

The Windows scan of the authoritative local corpus found **zero** historical deep-store memories carrying `metadata.srg` [FACT — local corpus evidence only; not proof of global absence]. This removes the only known live path by which historical SRG stamps could reach the spirit-return influence reader on the local corpus, without weakening the contract clauses that would govern such records if they exist elsewhere.

P1's closure test is answerable: era via genesis-or-attribution (never guessed, never self-attested for post-genesis objects); influence via live-gate consultation with disable honesty; history via append-only declaration and never-backfill; authority via family-bound ReaderPolicy outcomes that ratify nothing. Mechanics — rollback execution, recovery, torn-append repair, transactions, identity scope, projection instantiation — are explicitly parked with named owners (§9). P2 does not open by this memo.

---

## 2. Verified current facts

Carried from the 2026-06-07 archaeology (all line-verified; full evidence table in the archaeology report) plus new scan evidence. Facts, not clauses.

- **F-1.** No era vocabulary exists in `torment_service/` (grep `feature_era` / `"era"` / `era_`: zero matches). [FACT]
- **F-2.** Three generations of envelope versioning coexist: `srg` versionless with silent unknown-key filtering (`srg_engine.py:130–151`); `ProvenanceV1` write-side versioned `"1.0"` with **no read-side version check** and silent default synthesis (`provenance_v1.py:140,157,326–333`); `affect_attribution` fail-loud exact-match self-versioned with reserved values and a never-backfilled legacy read fallback (`affect_attribution.py:30,35–39,82–95,121–125,152–159,289–301`). [FACT]
- **F-3.** A complete ratified migration vocabulary exists: gate-1 outcomes SKIP/RECOVER/FAIL, seven row classes, admission reasons, monotonic-in-tightness re-run decisions, versioned admission policy with ordering rule, crash-safe append-only cursor + review queue, in-schema quarantine sentinel `SOURCE_GATE1_UNRECOVERABLE`, and a row-atomic rewrite invariant (`migration/constants.py:60–175`; `migration/apply.py:375–379,542–544`; `provenance_v1.py:67–76,275–278`). [FACT]
- **F-4.** SRG gates: main gate `TORMENT_SRG_ENABLE` default 0 (`fabric.py:716`); crystal sub-gate default 1-when-on (`srg_engine.py:84–92`); cognition gate `TORMENT_SRG_COGNITION` default 1 (`thinking_controller.py:196,410`). The cognition gate currently controls only `plan.retrieve_srg_state`, which has **zero read sites** repo-wide — a semantic contradiction presently driving a dormant flag (`thinking_models.py:123`; `behavior_packs.py:195,313`). [FACT]
- **F-5.** Ungated SRG readers exist in the protection family (`compression.py:399–401,625–637`; `lifecycle.py:983–986`) and one influence-family reader exists ungated but unreachable on the live projection-mediated deep lane because `srg` is absent from the 25-key deep-export allowlist (`spirit_return.py:355–366`; `deep_memory.py:221–242`; registry C7/C12). All current `payload["srg"]` writers are gated (`fabric.py:2556–2571,2847–2848,3042–3089,4193–4228`). [FACT]
- **F-6.** **Windows historical deep-store scan (operator-run, 2026-06-07): `metadata.srg` matches: 0.** The authoritative local data corpus contains no observed historical deep-store memories with `metadata.srg`. This is local corpus evidence only; it does not prove such records could never exist elsewhere (copied workspaces, external archives, future imports). [FACT — bounded]
- **F-7.** Reader-policy precedents exist and are the patterns this contract generalizes: explicit-wins/legacy-fallback/decline-on-disagreement (lifecycle soft migration, `lifecycle.py:564–686`); fail-loud envelope + synthetic legacy read (affect); fail-closed normalization (`provenance_v1.py:672–721`); structural non-authority on the deep lane (beta filter + `authority_status`, `fabric.py:3702–3743`); sentinel rejection at any depth; silent-tolerance loaders (deep/archive) and a fail-silent deep-lane exception wrapper (`fabric.py:3768–3769`). [FACT]
- **F-8.** Checkpoint snapshots stamp `"version": 2` that no reader checks (restore key-sniffs structure) (`checkpoint.py:334,425–432,449–459`); the SQLite sidecar performs a try/except ALTER upgrade and stamps `schema_version 4.1` without read-side enforcement (`sqlite_index.py:153–175`). [FACT — routed to P3 / P4-adjacent instantiation, §9]
- **F-9.** Two undeclared de-facto era boundaries already exist in the corpus: the dual embedding formats (legacy per-EID vs shard) and governance-less legacy archive chunks (`archive_memory.py:219–233`; Cluster 5 §5.9). They are handled today by reader-side sniffing — the situation the era ledger exists to end. [FACT]

---

## 3. Ratified P1 contract

All clauses in this section are **[CONTRACT]** — ratified P1 contract posture, design-level. Instantiation in any family's code is owned by later phases/slices.

### 3.1 Era ledger

1. **One unified append-only era ledger per workspace.** Eras are cross-family by nature (a gate flip changes interpretation of nodes, echoes, and packets at once); per-family journals remain a P6 question and are not foreclosed.
2. **EraEvent minimum and optional fields** — see §8 for the field table and kind vocabulary.
3. **Ordering:**
   - `event_ordinal` is the primary ledger order.
   - `at_ts` is observational only; `at_ts` cannot resolve ordering conflicts by itself.
   - Exactly one ordinal-assignment authority exists per workspace ledger.
4. **Integrity posture:** duplicate `event_id`, duplicate `event_ordinal`, torn-append evidence, or ledger inconsistency → **fail closed to diagnostic or quarantine posture**. Repair and recovery mechanics are parked for P5a / P6.
5. **Rollback posture:** `rollback_declared` is a new forward event. Rollback changes interpretation state. Rollback is not deletion, not history rewrite, not time travel. Execution mechanics → P5a.

### 3.2 Era attribution

**Semantic boundary (exact):**

> Era attribution is interpretation context.
>
> Era attribution is not: semantic ratification · lifecycle protection · proof of truth · authority.

**Existing corpus:**

- `era_genesis` names the demonstrably pre-contract past (exactly one genesis declaration per workspace ledger).
- `legacy_precontract` membership must be **derived**, from at least one of: a genesis baseline inventory; a deterministic family range; or another non-self-attested, auditable pre-contract anchor.
- Object-local timestamps alone are insufficient to establish `legacy_precontract` membership.

**Future durable objects:**

- Every post-genesis durable object must be attributable to an active era through at least one family-defined method: explicit `era_ref`; deterministic join key; or a durable, non-self-attested, family-specific ordering anchor.

**Hard rule:**

> A post-genesis durable object lacking a valid attribution path must never fall back to `legacy_precontract`. It becomes `diagnostic_only` or `quarantine` until explicitly classified.

(Family-specific identity and attribution mechanisms are P2's; this contract fixes the obligation and the failure posture, not the mechanism.)

### 3.3 Schema minimums

- New durable schema-bearing envelopes **must carry** `schema_version`.
- Known supported version → validate through **one canonical family shim**.
- Unknown or newer version → **never partially interpret; never silently admit to cognition**.
- Missing schema metadata on declared legacy data → a compatibility fallback may be used; the fallback must remain **visible**, must not be silently rewritten, and must not be backfilled merely to clean history.
- **EraEvent itself uses `event_schema_version`** — the ambiguous bare `schema_version` is not used for both the EraEvent envelope and a subject schema-activation event. (A `schema_activated` event describes its subject via `subject` + `from_value`/`to_value`; the envelope's own version is always `event_schema_version`.)

### 3.4 Nested schema rule

> A nested self-versioned envelope owns its own version boundary.
>
> Outer projection: copies the validated nested envelope verbatim, or omits it whole.
>
> Outer projection must not: partially reinterpret it · silently synthesize a new authored form · rewrite its version.

(Existing conforming instance [FACT]: `affect_attribution` across the deep projection, `deep_memory.py:232–241`, `fabric.py:3745–3764`.)

### 3.5 ReaderPolicy

ReaderPolicy is **family-bound interpretation discipline** — one canonical read shim per envelope family, with policy changes owned by the phase that owns the family. It is not a hidden central authority engine.

Outcome vocabulary (closed; may include recognized-but-inactive members under the reserved-values discipline):

`admit_cognition` · `diagnostic_only` · `quarantine` · `refuse_fail_closed` · `raise_fail_loud`

**Bounding clause (exact):**

> ReaderPolicy outcomes are family-bound read outcomes.
>
> They do not: mutate canonical fact · ratify truth · create hidden doctrine · create lifecycle protection · create hidden authority.

**Standing distinctions:**

- `diagnostic_only` ≠ cognition eligibility
- `quarantine` ≠ deletion
- storage survival ≠ semantic ratification
- historical provenance ≠ active influence permission

**Diagnostic fencing clause (exact):**

> `diagnostic_only` must not become an alternate cognition path through downstream tools, surfaces, or consumers.

(Fencing instantiation for the deep/diagnostic surfaces is P4's, per registry C15/D17.)

---

## 4. Reader behavior table

Ratified read-time behavior per state [CONTRACT]. "Family shim" = the one canonical reader per envelope family (§3.5).

| State encountered | Ratified behavior |
|---|---|
| Pre-genesis object with valid derived `legacy_precontract` membership (§3.2) | interpret under `legacy_precontract`; cognition-eligible under current rules; attribution marked derived, never authored |
| Post-genesis object with valid attribution path | interpret under its attributed era |
| **Post-genesis object lacking a valid attribution path** | `diagnostic_only` or `quarantine` until explicitly classified; **never** `legacy_precontract` |
| Unknown or newer `schema_version` on an envelope | envelope: `raise_fail_loud` at the family shim; object: never partially interpreted, never silently admitted to cognition; diagnostic readability per family policy |
| Missing schema metadata on declared legacy data | visible compatibility fallback (synthetic, marked, e.g. `legacy_read_fallback` vocabulary); never rewritten, never backfilled to clean history |
| Nested self-versioned envelope | nested envelope wins for itself; outer copies verbatim or omits whole (§3.4) |
| Historically influenced record, feature disabled now | provenance and stamps remain visible; influence lanes consult the live gate at read time; protection from raw historical stamps: inert (§5, §6) |
| Partially migrated object | must not exist at row level — the row-atomic migration invariant (`apply.py:375–379`) is adopted as a contract clause; corpus-level partiality is cursor state, queryable |
| Quarantined object | readable as diagnostics, never cognition-eligible, never silently dropped; in-schema sentinel precedent; recovery/procedure mechanics → P5a |
| Era-ledger integrity violation (duplicate id/ordinal, torn append, inconsistency) | fail closed to diagnostic or quarantine posture; repair mechanics → P5a / P6 |
| `rollback_declared` encountered | subsequent interpretation under the declared posture; prior-era objects keep their attribution; no deletion, no rewrite, no silent re-enable of disabled influence, no retro-promotion |

---

## 5. SRG disable-honesty contract

Ratified posture [CONTRACT] — resolves registry posture D8 at the contract level:

| Lane | When SRG is disabled |
|---|---|
| Audit visibility | **allowed** |
| Diagnostic visibility | **allowed** |
| Historical provenance | **allowed** |
| Direct protection from raw `srg` | **disabled** |
| Direct influence from raw `srg` | **disabled** |
| Query-time mutation from raw `srg` | **disabled** |
| Raw historical `srg.is_crystal` | **visible but inert as a direct behavior input** |

[NON-DECISION] When SRG is enabled, whether evolution becomes derived non-authoritative state or explicit locked event-sourced evolution remains the enabled-state D12 / P5a question. This memo does not resolve it.

Evidence recorded beside the contract [FACT — bounded]: the Windows corpus scan returned `metadata.srg` matches: 0. This is **local corpus evidence only**; global absence is not claimed. The ungated reader inventory (F-5) names the code paths this contract governs; **no SRG code is patched by P1** — reader-gating work becomes eligible as the already-named §J maintenance candidate ("interim SRG reader gating only after P1 reader policy"), now unblocked at the policy level, each slice separately ratified.

---

## 6. SRG crystal recommendation and contestability contract

Hilmir-ratified values-layer posture [CONTRACT] — resolves registry C7's owed provenance decision and posture D10:

> Historical `srg.is_crystal` must not automatically become active lifecycle protection.
>
> A future, separately authorized migration may stage an **auditable protection recommendation**. It may not silently convert an old heuristic into lifecycle truth.

**Required provenance on any staged recommendation** (preserved sufficiently to remain auditable): original object identity · raw `srg` payload · existing lifecycle status · existing `set_by` · source family · workspace · observed ordering or timestamp · migration event id · rule applied · before state · after proposed state · rollback reference · contest reference.

**Duplicate-source rule:** if an object is already protected through another route — preserve both provenance claims; do not double-count protection strength; do not silently overwrite the existing route.

**Ratified guidance boundary** (E10 mechanism boundary): transparent, contestable retention or compression guidance — **allowed**. Absolute preservation lock — **not allowed**. Output blocking — **not allowed**. Constraint preventing the AI from changing direction — **not allowed**.

**Ratified contestability posture:** Hilmir holds ultimate operator authority; operator tooling may inspect, contest, accept, or revoke recommendations visibly; later doctrine-defined governance events may record contests, acceptance, revision, or revocation; **no invisible automatic finalizer**.

**Key distinction (exact):**

> A re-homed protection record is an auditable governance claim. It is not proof that the historical SRG mark was correct. It must remain contestable and reversible through later explicit events.

---

## 7. Legacy corpus handling

- The entire pre-contract past is honestly named, not reconstructed: one `era_genesis` event declares the `legacy_precontract` era [CONTRACT].
- `legacy_precontract` membership is derived per §3.2 (genesis baseline inventory / deterministic family range / non-self-attested auditable anchor); object-local timestamps alone are insufficient [CONTRACT].
- Legacy envelopes keep their existing declared-legacy reads: synthetic fallbacks remain visible and unmistakable for authored data (`legacy_read_fallback`, `unset_default` vocabularies, F-7), are never rewritten in place, and are never backfilled merely to clean history [CONTRACT].
- The de-facto undeclared boundaries already in the corpus (F-9) are `legacy_precontract` interior detail; the contract's obligation is that the **next** such boundary be declared as an EraEvent rather than discovered by archaeology [CONTRACT].
- Local scan evidence (F-6) is recorded as `legacy_precontract` corpus characterization: no observed deep-store `metadata.srg`. Copied or external workspaces are not characterized by it; copied-workspace reconciliation is parked (§9) [FACT + PARKED].

---

## 8. EraEvent minimum vocabulary

[CONTRACT] EraEvent envelope:

| Field | Class |
|---|---|
| `event_schema_version` | required |
| `event_id` | required |
| `event_ordinal` | required (primary order; one assignment authority per workspace ledger) |
| `kind` | required (closed vocabulary below) |
| `subject` | required (controlled token naming what changed) |
| `at_ts` | required (observational only; never resolves ordering by itself) |
| `declared_by` | required (actor class; reuses existing actor vocabulary — no new actor set) |
| `writer_version` | required |
| `at_step` | optional |
| `from_value` / `to_value` | optional |
| `policy_ref` | optional |
| `notes` | optional |
| `era_id` | optional (readability token; era identity is derivable from the ordinal-ordered boundary events) |
| `precontract_anchor_ref` | optional at envelope level; conditionally required for `era_genesis` |
| `run_ref` | optional at envelope level; conditionally required for `migration_run` |

`precontract_anchor_ref` references the genesis baseline inventory, deterministic family range, or another auditable non-self-attested pre-contract anchor used to derive `legacy_precontract` membership (§3.2).

`run_ref` links a declared migration run to its auditable run identity. Migration execution and storage mechanics remain parked (§9).

Candidate `kind` vocabulary (closed set; extensions enter only by registry amendment; reserved-values discipline applies):

`era_genesis` · `feature_gate_changed` · `schema_activated` · `policy_changed` · `migration_run` · `rollback_declared` · `era_note`

Kind-specific minimums:

- `era_genesis` → requires `precontract_anchor_ref`
- `feature_gate_changed` → requires `from_value` and `to_value`
- `schema_activated` → requires `to_value`; `from_value` is optional only when no prior declared schema exists
- `policy_changed` → requires `policy_ref`; `from_value` / `to_value` are required where they name the policy transition
- `migration_run` → requires `policy_ref` and `run_ref`
- `rollback_declared` → requires `to_value` as the declared rollback target
- `era_note` → interpretation-neutral; must not change active interpretation state

The EraEvent ledger **is** the feature-era audit history: gate-default changes, schema activations, policy bumps, and migration runs become first-class declared events. Minimum audit guarantee: for any durable object and any consulting reader, it is answerable from tracked data which era the object belongs to (attribution per §3.2) and which policy interpreted it (family shim + `policy_ref`).

---

## 9. Explicit parked items and routing

All **[PARKED]** — answering any of these inside P1 would be drift:

| Parked item | Owner |
|---|---|
| Family-specific canonical identity and attribution mechanisms (incl. era_ref/join-key/anchor instantiation) | **P2** |
| MemoryNode hot-path `era_id` requirement | **P2** (with the above) |
| Shell continuity and checkpoint contract (incl. checkpoint `version` enforcement, F-8) | **P3** |
| Deep-projection contract instantiation and diagnostic fencing | **P4** |
| Rollback execution mechanics · recovery semantics · quarantine procedure · torn-append handling · duplicate repair · partial-restore repair · copied-workspace reconciliation | **P5a** |
| Durable append guarantees · checksums · transaction model · storage primitives | **P6** |
| Full migration strategy · architecture-wide promotion | **P9** |
| ProvenanceV1 read-side enforcement tightening (load-bearing silent synthesis; corpus-behavior change) | parked; separate slice with its own evidence |
| SRG runtime patching of any reader/writer | parked; §J maintenance candidates, each separately ratified, now policy-unblocked by §5 |
| `TORMENT_SRG_COGNITION` default flip or removal | **[MAINT]** — see below |
| Storage product selection · custom low-level storage internals | foreclosed for P1; registry §K trigger discipline unchanged |

**Maintenance lane candidate [MAINT]:** `TORMENT_SRG_COGNITION` default reconciliation. Reason: currently a semantic contradiction with the main gate; presently drives only the dormant `retrieve_srg_state` flag (F-4); no P1 patch authorized; separately ratifiable §J slice.

**[NON-DECISION]** — additionally not decided by this memo: era-ledger file format/layout beyond vocabulary (any `era_events.jsonl` shape mentioned in lineage documents is illustration, not format selection); per-workspace vs global record identity (F4 → P2/P5a); journal-vs-per-family ledgers generally (F9 → P6); registry posture D11 (forced resonance as bounded bias) — an enabled-state mechanism question untouched here; the enabled-state half of D12 (locked event-sourced evolution vs derived state) — P5a integrity semantics; orphan-visibility mechanism (F11 → P4); benchmark questions (P8a/P8b); any noun promotion beyond what the registry amendment records.

---

## 10. P1 closure checklist

P1 closes when all of the following hold:

1. ☑ Read-only archaeology complete with line-cited evidence (2026-06-07 report).
2. ☑ Codex adversarial review complete (hidden authority, migration traps, feature-disable honesty); corrections incorporated into the ratified posture.
3. ☑ Operator evidence: Windows historical deep-store scan complete (`metadata.srg`: 0, recorded as local-corpus-only evidence).
4. ☑ Values-layer decisions resolved by Hilmir: SRG disable honesty (§5); crystal recommendation + contestability (§6).
5. ☑ GPT final wording review complete.
6. ☑ Trio closure decision complete: closure test answered; no P2/P4/P5a/P6 question silently resolved.
7. ☑ Hilmir promoted the P1 contract and orientation-map pointer in docs-only Slice A (`88174fc`).
8. ☑ Small registry amendment Slice B completed: P1 closure and listed classification changes recorded explicitly.
9. ☑ Next gate remains unselected: P2 opens only by explicit trio decision. Not implied, not auto-opened.

---

## 11. Proposed promoted-doc filename

```
docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md
```

(Sibling naming to the P0 registry; the archaeology report may be preserved as lineage either in `scratch/` or as a docs appendix — operator's choice at promotion time; this memo is self-sufficient without it.)

## 12. Orientation-map update wording

Proposed one-block insertion for `docs/PROJECT_ORIENTATION_MAP.md` §7 (to be committed by Hilmir with the promotion; not applied by this memo):

> **TORMENT Memory Engine P1 — Era and Schema Minimum Contract closed (2026-06-07).**
> `docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md` is promoted as the ratified P1 contract: one unified append-only era ledger per workspace (EraEvent minimum vocabulary, `event_ordinal` primary order, fail-closed integrity posture); era attribution as interpretation context — never ratification, protection, truth, or authority; `era_genesis` / `legacy_precontract` handling for the pre-contract corpus with the hard rule that unattributable post-genesis objects never fall back to legacy; schema-version minimums with one canonical shim per family; the nested-schema verbatim-or-omit rule; family-bound ReaderPolicy outcomes with the diagnostic fencing clause; the SRG disable-honesty contract; and the Hilmir-ratified crystal recommendation/contestability posture (no automatic re-homing; auditable, contestable, reversible recommendations only). Windows deep-store scan: `metadata.srg` 0 matches (local corpus evidence only). Implementation, migration mechanics, recovery, projection instantiation, and storage primitives remain parked to P2/P3/P4/P5a/P6/P9 per the memo §9; `TORMENT_SRG_COGNITION` default reconciliation is a separately ratifiable maintenance candidate. **The next gate is unselected; P2 opens only by explicit trio decision.**

---

**P1 closure finalized.** This contract and its registry amendment are docs-only. No runtime code, schema implementation, migration, storage product, or subsequent phase is authorized. P2 remains closed and unselected.
