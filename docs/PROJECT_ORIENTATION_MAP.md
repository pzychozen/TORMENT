# TORMENT — Project Orientation Map

## 0. Active Frontier — OVERWRITE THIS BLOCK, DO NOT APPEND

### Current repository state

- This map’s §0 is the live orientation and work-order authority. Material below §0 is historical evidence, not current scheduling authority.
- **TORMENT Memory Substrate Phases 0–5 are frozen at requirement/physical-design level.** The binding records are [Phase 1 logical model](TORMENT_MEMORY_SUBSTRATE_PHASE_1_LOGICAL_MODEL_v0.1.md), [Phase 2 reliability, integrity, and recovery contract](TORMENT_MEMORY_SUBSTRATE_PHASE_2_RELIABILITY_INTEGRITY_RECOVERY_CONTRACT_v0.1.md), [Phase 3 physical architecture](TORMENT_MEMORY_SUBSTRATE_PHASE_3_PHYSICAL_ARCHITECTURE_v0.1.md), [Phase 4 SQLite transactional-core contract](TORMENT_MEMORY_SUBSTRATE_PHASE_4_SQLITE_TRANSACTIONAL_CORE_CONTRACT_v0.1.md), and [Phase 5 native schema/transaction/migration design](TORMENT_MEMORY_SUBSTRATE_PHASE_5_NATIVE_SCHEMA_TRANSACTION_MIGRATION_DESIGN_v0.1.md). No production implementation, test change, detailed DDL, migration, benchmark, or qualification has opened.

### Memory substrate closure

- **Phase 0 baseline:** `CURRENT_STORAGE_IS_AN_EMBRYONIC_CUSTOM_SUBSTRATE`; `CANONICAL_OPERATIONAL_TRUTH_SHOULD_LEAVE_LOOSE_JSONL`; `TORMENT_OWNED_LOGICAL_SUBSTRATE_REQUIRED`; `MULTIPLE_ACCESS_MODELS_REQUIRED`; `MULTIPLE_PHYSICAL_ENGINES_LIKELY_BUT_NOT_REQUIRED`; `NEW_LOW_LEVEL_DATABASE_ENGINE_NOT_REQUIRED`. JSONL is not inherently the problem; unmanaged canonical persistence lacks adequate durability discipline, cross-process exclusion, localized integrity, logical commit boundaries, and recovery semantics.
- **Phase 1 logical model:** durable semantics are carried by logical objects and first-class logical relationships, not files, rows, or engines. `PRIMARY_DURABLE_STATE`, `MATERIALIZED_DERIVATION`, `HISTORICAL_EVIDENCE`, and `ACCELERATION` remain distinct; representation generations and dependencies are explicit.
- **Phase 2 reliability contract:** commitment requires explicit, durable, non-residue evidence sufficient for non-guessing recovery. Historical outcome is separate from present determination; retries require stable idempotency identity and revision compatibility; integrity is localized; incomplete joint semantic invariants are withheld; and legacy ambiguity attaches to the smallest affected unit.
- **Phase 3 physical architecture:** `INITIAL_PHYSICAL_SHAPE = SINGLE_TRANSACTIONAL_CORE`. The initial transactional core carries authoritative durable semantics and may initially retain materialized-representation payloads and required semantic history without collapsing their logical roles. `ACCELERATION` remains rebuildable and non-authoritative. A future separate representation-payload lane is compatible but not required.
- **Phase 4 SQLite transactional-core contract:** `TRANSACTIONAL_CORE_ENGINE = SQLITE`. One semantic commit set is one SQLite core-database transaction; WAL and `synchronous=FULL` are required for semantic commitment; every semantic connection has a controlled initialization/verification path; semantic writes begin with `BEGIN IMMEDIATE`; and immutable transition evidence commits with successor state. SQLite physical writer serialization never replaces predecessor/revision validation. The current SQLite 3.51.2 environment is **not eligible** for the new WAL core: the WAL-reset fix, runtime admissibility policy, and fail-closed startup qualification are required.
- **Phase 5 native schema/transaction/migration design:** logical objects and relationships use immutable revisions with primary current-revision selection pointers; committed revisions are semantically closed; operations provide recoverable idempotency intent and allocated outputs; each semantic commit has immutable transition evidence and typed effects; representations, integrity, reconciliation, aliases, and admission remain distinct structural families. Migration is an offline one-shot admission cutover; after new-core writes resume, the legacy store is evidence only. Exact DDL remains deferred.
- **Preserved boundaries:** semantic scope, fate domain, authority, current state, history, commit truth, representation readiness, integrity measurement, and operational disposition remain distinct. `COMMITTED / REPRESENTATION_PENDING` remains valid. Motif reconstruction remains unproven; motifs are non-disposable derived logical objects with derived logical membership relationships.

### Next memory substrate phase

**Phase 6 — Detailed SQLite DDL / Storage API / Implementation Roadmap** is the next separately authorized phase. It may turn the frozen Phase 5 structural families and transaction/migration design into exact SQLite DDL, storage APIs, helper boundaries, admission tooling design, qualification planning, and an implementation work breakdown. It remains subordinate to the frozen TORMENT logical substrate and does not itself authorize production implementation.

### Pre-database invariant closure

- **PRE-DATABASE INVARIANT 1 — MEMORY-OPTIONAL IDENTITY: CLOSED / REQUIREMENT-LEVEL.** Identity definition is separable from experiential history; full character runtime remains memory-backed; the future reduced-mode term is **historyless character**. No implementation opened.
- **PRE-DATABASE INVARIANT 2 — MODALITY-INDEPENDENT INGEST: CLOSED / REQUIREMENT-LEVEL.** Current generic text ingress is modality-blind and provenance-lossy; future memory semantics must separate origin, channel, representation, and derivation; unknown provenance is legitimate and raw media need not be retained. No richer-audio implementation opened.
- **PRE-DATABASE INVARIANT 3 — AGENCY / AUTHORITY SEPARATION: CLOSED / REQUIREMENT-LEVEL.** Content/evidence does not create present authority; intent/proposal is distinct from permission; future durable, delegated, and AI-held authority remains permitted only under legitimate non-circular conferral; execution and autonomous initiation are distinct. No authority or autonomy runtime was opened.

> **All three pre-database invariants are CLOSED.**
>
> 1. Memory-Optional Identity
> 2. Modality-Independent Ingest
> 3. Agency / Authority Separation

### Current authority and autonomy boundary

- `CONTENT_AND_AUTHORITY_ARE_MOSTLY_SEPARATED_WITH_EXPLICIT_EXCEPTIONS` is the factual archaeology verdict. Trust/request authorization is external/config/request-derived, not memory-derived. Ordinary memory, canon, retrieval rank, tool result, model output, ThinkingResult, cognition result, Hivemind echo/proposal, character state, kernel signal, and stored intent do not create execution permission merely by existing or becoming influential.
- The frozen substrate model preserves this boundary: stored carriers and representations—including future executable-artifact representations—never become execution authority merely through persistence. `STORED != EXECUTABLE`; `EXECUTABLE != ACTIVATED`; `ACTIVATED != AUTHORIZED`.
- Current Mode 0 contains no memory-triggered wake loop or autonomous initiation path. AgentRunner/tool execution remains dormant and unowned. Managed autonomy is a future concept only; no scheduler, wake condition, active authorization runtime, capability system, or generic action authority exists today.
- Canon is epistemic/identity standing, not execution permission. Retrieval may reveal authority-related information but is non-authorizing. Collective content cannot manufacture independent authority. `CONTENT CONTRIBUTION != AUTHORITY CONTRIBUTION` remains current Hivemind posture.
- Current TORMENT has parallel REST and Spine trust enforcement; Fabric generally assumes caller-side authorization. This is enforcement-placement debt, not content/authority entanglement. `/promote force=True` remains `SEPARATELY_GATED_AUTHORITY_QUESTION`; Gate B is unresolved.
- Existing persisted authority-shaped state that has never been load-bearing must not automatically become active authority in any future migration merely because it is preserved or normalized.

### Current authorized activity

**NONE / HOLD pending explicit Phase 6 opening: Detailed SQLite DDL / Storage API / Implementation Roadmap.**

## 1. Current main project thread

Controlled **memory-to-prompt automation** has landed through the v0.2.x chain
(observability lane → `character_context` → spirit-return → archive-FILTER-A),
followed by the Ledger Persistence Decision (Option C, response-only).
Retrieved memory may shape the context of a later LLM call; it does not gain
authority by doing so. The constraint that anchors all work remains doctrinal:

> *Memory may shape context. Memory may not seize authority.*

Reinforced by the Ledger Observational-Boundary Doctrine v0.1: *audit observes
authority; audit does not become authority.* Consistent with the MCP capability
boundary doctrine (`docs/MCP_CAPABILITY_BOUNDARY.md`): **automatic remains
allowed; autonomous remains not authorized.** Autonomy has not opened.

The next primary lane is intentionally **unselected**. Orientation-map curation
and the small maintenance re-verification are closed. Any new lane requires a
separate trio decision under the gate-start survey rule in §5. Any
slice that pushes against the automatic/autonomous boundary needs its own
ratification; any slice that respects it proceeds under the gate-start survey
rule in §5.

---

## 1A. Pre-database programme ladder (orientation)

**Anti-drift map.** The pre-database programme is **two parallel ladders plus a code-improvements
lane**. Do not collapse it into a single local label (e.g. Gate B1 / H3) — those are leaves, not the
programme.

**Ladder 1 — Memory Engine / database-readiness contracts and later mechanics.** The registry-governed
`P0→P11` phase graph (`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`). Purpose:
source-meaning, recovery, migration-readiness, and constraints any later substrate mechanics must carry.
**Governed database/substrate mechanics remain unopened; P6 carrier/substrate mechanics and Stage
B/database design remain later, separately authorized lanes.**

**Ladder 2 — Pre-Substrate Architecture / mind-readiness contracts and reconciliation memos** (all
**requirement-level, docs-only, promoted — not implemented**): Document A (Candidate Containment +
Writer Authority); Document B (Private Cognition + Unified Reflection); Seed-Governance; No-Corner /
bounded defensive availability; and the Database/Substrate Reconciliation memo. Purpose: cognition,
reflection, identity, and candidate/canon boundaries defined **before** permanent storage.

**Code-grounded improvements / characterization lane** — improves or characterizes TORMENT-as-it-is,
**not** full systems: memory-to-prompt observability; ReflectionTrace observability; behavior-pack
`high_regime_action`; Gate A / Gate B characterizations. These are bounded observability,
policy-wiring, and characterization work — **not** private cognition, dreaming, or database
implementation.

**Current position.** Main programme: **pre-database readiness**. Current lane: **Thinking Layer** —
Writer Authority is **paused** after H3 force-route provenance (H1 parked, not de-risked). Latest landed:
**tuned-scoring provenance lock** (`cbdc609`, tests-only) — characterizes the ambiguity/urgency scoring
buckets underneath the already-locked 0.60/0.72 thresholds; **no value or behavior changed**. The Thinking
Layer's clean small-slice vein is now harvested and **should pause** unless a new bounded slice is
separately found. **Each leaf is a leaf, not the programme.**

**Not implemented (carry forward, do not overstate):** Document B runtime surfaces — private cognition,
continued thought, dream / incubation, and envelope audit — plus Seed-Governance mechanics, candidate
store, source-sameness enforcement, and governed database/substrate mechanics are **requirement-level
only, parked, or unopened**. Current JSON/JSONL/SQLite scaffolding remains as-is; no new governed
substrate/runtime exists for these surfaces.

---

## 2. Where main currently stands

As of 2026-06-12, the following arcs are closed on `main`. Each row points to
the tracked source of truth for what shipped or was ratified. (Not every arc has
a dedicated checkpoint doc — some point to a doctrine/framing doc, and a few
recent hardening items are commit-level only.)

| Arc | Closed | Source of truth |
|---|---|---|
| Phase 1 / Tier 1 runtime envelope (Batch A no-pack, Batch B debugging pack) | 2026-05-17 | `docs/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md` (promoted from scratch 2026-05-28; scratch original preserved as lineage) |
| Track A v0.1 — Truthfulness Envelope (Mode / Voice / Certainty / Authority; voice-audit; materiality; three-role ownership) | 2026-05-19 | `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md` |
| Cluster 2 v0.1 — Authority Gate (Scope + Lane axes; Authority class / lifecycle / promotion-rights; disagreement primitive) | 2026-05-19 | `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md` |
| Track B v0.1 — Disagreement Runtime (`ContestRecord`; separate contest ledger; contest increases audit visibility) | 2026-05-20 | `docs/TRACK_B_DISAGREEMENT_RUNTIME_v0.1.md` |
| Cluster 5 v0.1 — Storage / Survivability (storage preserves governance meaning; ten fragility handles; "necessary but not sufficient") | 2026-05-21 | `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md` |
| Q2-D tool-result canon-suppression doctrine | 2026-05-24 | `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md` |
| Level 3 ST retrieval-quality smoke | 2026-05-24 | `docs/CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL.md` |
| Tier 2 runtime evidence (5,400 turns / 3 pack regimes / 0 aborts) | 2026-05-24 | `docs/CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE.md` |
| Scratch-doc promotion (automation audit + long-iteration plan) | 2026-05-24 | `docs/AGENT_AUTOMATION_NEXT_STEP_AUDIT.md`, `docs/AGENT_RUNTIME_LONG_ITERATION_TEST_PLAN.md` |
| Tool-result lifecycle policy implementation-status correction | 2026-05-24 | `docs/TOOL_RESULT_LIFECYCLE_POLICY.md` §0.6 + §3.4 |
| Memory-to-Prompt Automation v0.2 — observability lane (first revision PASS) | 2026-05-25 | `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_OBSERVABILITY_v0.2.md` |
| Memory-to-Prompt Automation v0.2.2 Candidate A — `character_context` surfacing on `/retrieve` (PASS) | 2026-05-25 | `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_2_CHARACTER_CONTEXT.md` |
| Test isolation cleanup — FastAPI stub removal + DATA_DIR app-reload leak fix (class-of-bug parity across three fixtures) | 2026-05-27 | `docs/CHECKPOINT_2026-05_TEST_ISOLATION_FASTAPI_DATADIR.md` |
| Visualize attractors suite restore — `_viz_common` import path fix + live Ryuki skip guards (full suite no longer needs `--ignore`) | 2026-05-27 | `docs/CHECKPOINT_2026-05_VISUALIZE_ATTRACTORS_SUITE_RESTORE.md` |
| Memory-to-Prompt Automation v0.2.3 — spirit-return / voice-cue `/retrieve` surfacing verification (PASS) | 2026-05-27 | `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_3_SPIRIT_RETURN.md` |
| Memory-to-Prompt Automation v0.2.4 — archive-FILTER-A application (Option A, defense-in-depth) PASS | 2026-05-27 | `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_4_ARCHIVE_FILTER_A.md` |
| Cluster 5 Path C — governance-preservation chain (Q1 deep-hit handling, Q2 lifecycle) | 2026-05 | `docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md`, `docs/CLUSTER_5_PATH_C_Q1_IMPLEMENTATION_FRAMING_v0.1.md`, `docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md` |
| Ledger Observational-Boundary Doctrine v0.1 — "Audit observes authority. Audit does not become authority." | 2026-05-29 | `docs/LEDGER_OBSERVATIONAL_BOUNDARY_DOCTRINE_v0.1.md` |
| Ledger Persistence Decision — Option C (response-only observability; A foreclosed, B parked); closes Memory-to-Prompt v0.2.x | 2026-05-30 | `docs/CHECKPOINT_2026-05_LEDGER_PERSISTENCE_DECISION_OPTION_C.md` |
| Track J — runtime-context ownership isolation; additive per-agent runtime-context serialization | 2026-05 | commits `bdb3bd5`, `b57451d` |
| Ordinary-ingest auto-canon fail-closed correction | 2026-05-31 | commit `fe69c1e` |
| Character-memory harness Probe-v0 — first active (non-frozen) instrument; plumbing / companion-posture / clean-prompt PASS; runtime coherence COHERENCE_BROKEN candidate | 2026-05-31 | `docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md` |
| Cluster 5 Path C — Q3-D1-S1 affect-attribution validator + legacy read shim + scoring-invariance baseline | 2026-06 | commits `8505678`, `6e728e8` |
| Cluster 5 Path C — Q3-D1-S2 ordinary-ingest affect-attribution stamping (completion-guarded; `unset != not evaluated`) | 2026-06-02 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S2_ORDINARY_INGEST_ATTRIBUTION.md` (commit `8b2c1f3`) |
| Cluster 5 Path C — Q3-D1-H1 caller-envelope survival hardening (`affect_attribution` reserved internal field at the `TormentFabric.ingest()` merge seam; anti-forgery promoted from stamped-rows-only to global) | 2026-06-03 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_H1_CALLER_ENVELOPE_STRIP.md` (commit `7066b57`; checkpoint `64d796e`) |
| Cluster 5 Path C — Q3-D1-S3 mood_drift affect-attribution stamping (`origin_kind=derived` / `via=mood_drift_transition`; dedicated `build_mood_drift_attribution`; D1-S2 T10 unstamped-boundary consciously inverted) | 2026-06-03 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S3_MOOD_DRIFT_ATTRIBUTION.md` (commit `dcead02`; checkpoint `37dc5bb`) |
| Cluster 5 Path C — Q3-D1-S4 deep-rehydrate conformance (S4a durable `DeepMemory.metadata` snapshot preservation + S4b runtime `_query_deep_lane` echo surfacing of `affect_tag` + `affect_attribution`; external/API cross-surface deferred to D1-S5) | 2026-06-03 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S4_DEEP_REHYDRATE_CONFORMANCE.md` (commit `b602fc7`; checkpoint `55cd6d5`) |
| Cluster 5 Path C — Q3-D1-S5b generic `user_confirmed` isolation lock (test-only regression barrier; `generic user_confirmed != affect confirmation`; production already conformant) | 2026-06-03 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S5B_GENERIC_USER_CONFIRMED_ISOLATION.md` (commit `3e25be7`; checkpoint `fbced7e`) |
| Cluster 5 Path C — Q3-D1-S5a cross-surface characterization (test-only lock; preserve where carried / deliberately omit where projected; no production change, no public/API/MCP or `character_context` exposure added) | 2026-06-03 | `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S5A_CROSS_SURFACE_CHARACTERIZATION.md` (commit `dd46019`; checkpoint `4e930d9`) |
| Track B v0.2 — B2-S1 contest-ledger runtime boundary framing (ratified framing artifact; **not** doctrine / implementation / schema / automation authorization; B2-S2 vocabulary + validator + pure serialization tests is candidate-only, not auto-open) | 2026-06-03 | `docs/TRACK_B_V0_2_CONTEST_LEDGER_RUNTIME_BOUNDARY_FRAMING_v0.1.md` (commit `c64417e`) |
| Track B v0.2 — B2-S2 isolated ContestRecord vocabulary (frozen immutable record + deterministic fail-closed validator + pure dict/JSON/JSONL serialization + mandatory importer-free AST guard; **no production wiring**; nested ProvenanceV1 canonicalized, no `SOURCE_CONTEST` added; B2-S3 append-only writer/reader remains parked, not auto-open) | 2026-06-04 | `docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S2_CONTEST_RECORD_VOCABULARY.md` (commit `f42b6ee`) |
| Track B v0.2 — B2-S3 isolated ContestLedger persistence (single workspace-scoped `contest_records.jsonl`; append-only `append_record(ContestRecord)` + literal unbounded `list_records()`; **fail-closed** malformed-line handling + read-time duplicate-`contest_id` raise; no append-time scan / no lock / no fsync; `contest_record` importer allowlist narrowed explicitly to `contest_ledger.py`; ordinary runtime imports of `contest_ledger` forbidden; **no consumer wiring**, no `contest_events.jsonl`; B2-S4 counter-contest semantics remains parked, not auto-open) | 2026-06-04 | `docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S3_CONTEST_LEDGER_PERSISTENCE.md` (commit `9c027a0`) |
| Track B v0.2 — B2-S4 narrowed counter-contest event framing (ratified framing artifact narrowing the parent §12 B2-S4 step to counter-contest event vocabulary + isolated persistence; excludes `candidate_handle → eid` binding; **not** implementation authorization) | 2026-06-04 | `docs/TRACK_B_V0_2_B2_S4_COUNTER_CONTEST_EVENT_FRAMING_v0.1.md` (commit `36a8a84`) |
| Track B v0.2 — B2-S4 isolated counter-contest event persistence (frozen immutable six-field `CounterContestEvent`, **no outcome/status/precedence field**; workspace-scoped append-only `contest_events.jsonl`; literal `list_events()` + `list_events_for_contest()` filtering in append order only — chronology, not precedence; **fail-closed** malformed-line / invalid-event / read-time duplicate-`event_id` raise; `target_contest_id` UUID-shaped structurally only, no existence check, dangling linkage representable; `ContestActor`/`ContestReasonClass` reused unchanged; AST guards enforce zero consumers / no authority-retrieval-prompt-cognition-MCP imports / no resolver surface; **no consumer wiring**, no resolver) | 2026-06-04 | `docs/CHECKPOINT_2026-06_TRACK_B_V0_2_B2_S4_COUNTER_CONTEST_EVENT_PERSISTENCE.md` (commit `1a17d6f`) |
| CodeQL non-C1 maintenance closure — nine query families resolved by narrow fixes + intentional dismissals to **0 open dashboard alerts**; test/example/harness only; no production / schema / reader-projection / cognition-eligibility / authority-boundary / continuity / database / Memory Engine change; storage redesign remains unopened | 2026-06-12 | `docs/CHECKPOINT_2026-06_CODEQL_NON_C1_CLOSURE.md` (commits `2225e65`, `92960b2`, `cebd5d7`, `adedb71`, `ff1a021`, `ddaeea1`, `fc69c3c`) |
| Pre-substrate architecture framing v0.1 — reconstruction of the higher architecture (thinking / reflection / seed / soft-continuity) above the paused substrate; framing only (no implementation, no mechanics, no Stage B); Document A eligible but **not** opened | 2026-06-13 | `docs/TORMENT_PRE_SUBSTRATE_ARCHITECTURE_FRAMING_v0.1.md` (promoted at `27d8aa4`) |
| Document A — Candidate Containment and Writer-Authority Contract v0.1 — docs-only requirement-level **write-side** boundary; unadmitted reflection artifacts structurally barred from ordinary cognition-shaping fan-out; admission defaults to **at most released / low-authority** (stricter outcomes allowed); admission ≠ promotion; runtime enforcement later-owned; no implementation, mechanics, Stage B, or Document B | 2026-06-13 | `docs/TORMENT_CANDIDATE_CONTAINMENT_WRITER_AUTHORITY_CONTRACT_v0.1.md` |
| Document B — Private Cognition and Unified Reflection Blueprint v0.1 — docs-only requirement-level **interior** contract; bounded private-cognition interior inside Document A's wall and behind P4's read-side boundary; two regimes (active continuity / offline dream-incubation) under one governance skeleton; staging permitted inside the chamber, admission remains Document A's; Envelope Audit detect/flag/stage only; silence as non-reentry footprint; no implementation, mechanics, scheduler, store/schema, Stage B, or autonomy | 2026-06-13 | `docs/TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md` |
| Seed-Governance Blueprint v0.1 — docs-only requirement-level **seed / identity / canon governance** contract; specializes Document A's write-side wall for seed/identity/canon outcomes (amends A in no way); operator-governed seed revision (operator-only default, lineage-preserving); identity/seed/canon-affecting candidates stricter than ordinary and never auto-admit; Document A remains the admission edge; canon governed by source class, not one boolean; automatic identity/seed/canon writers flagged not-yet-conformant (require later reconciliation, not patched); `mood_drift → drift → gravity_correction → canon=True` named as a compound hazard; no implementation, runtime seed writer, canon-editing mechanics, schema/store, migration, Stage B, or autonomy | 2026-06-13 | `docs/TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md` |
| Bounded Defensive Availability / No-Corner Invariant v0.1 — docs-only requirement-level, **defensive-only** companion contract; creates the **hard No-Corner availability invariant** (at every state the agent has at least one bounded, non-compliant, non-breaking move that does not expand authority/scope/budget/reach/persistence/future action); ratified defensive floor = expression / inside-turn withdrawal / expressive operator-review request; operator-review request is expressive-only (no notification/paging/MCP/standing-task); provisional non-admission of identity-shaping claims is inside-turn only with no durable effect; defense ≠ autonomy and safety ≠ helplessness; defensive audit is evidence-only (no reputation/penalty/hostility/persona/refusal-bias); amends no upstream contract; no implementation, runtime, enforcement, monitoring, MCP action, operator-notification, Stage B, or autonomy (runtime conformance later-owned) | 2026-06-13 | `docs/TORMENT_BOUNDED_DEFENSIVE_AVAILABILITY_NO_CORNER_INVARIANT_v0.1.md` |
| Writer-path / endpoint-wiring characterization triad — Seam 1 `drift_reflex_callback` consumption trace (read-only: declared/dispatch-capable but unwired, no runtime consumer); Seam 2 `_maybe_emit_identity_anchor` writer-path lock (test-only, `cd35aae`: derived `canon=False` `identity_anchor` from motif heuristics, no authority/seed-gov/operator input; read-side tier hygiene not re-tested, no P4/source-sameness or retirement opened); Seam 3 `POST /promote` force-bypass endpoint-wiring lock (test-only: `force=True` → `is_canon`+`user_approved`, reaches `promote_chunk`, `result.promote or req.force` branch; writer row shape not re-tested, no auth/governance doctrine imported). Characterization only — no fix, no desired-runtime-doctrine claim, no gate opened | 2026-06-17 | `docs/CHECKPOINT_2026-06_WRITER_PATH_CHARACTERIZATION_TRIAD.md`; baseline through `b549a97` |
| Lane A — `mood_drift → drift-centroid` inclusion trace (read-only) — [READ-ONLY FINDING] the `mood_drift → drift centroid → gravity_correction → canon=True` path is confirmed an active inclusion path for eligible rows: a recent same-agent `mood_drift` row with an embedding is not filtered out of `measure_drift`'s weighted recent-memory centroid. Topology only; no magnitude/decisiveness/harm/remediation claim, no gate, no filtering or runtime requirement introduced | 2026-06-17 | `docs/CHECKPOINT_2026-06_MOOD_DRIFT_CENTROID_INCLUSION_TRACE.md`; baseline through `1f6cd0d` |

**Q3-D1 affect attribution is CLOSED as a bounded chain** (S1 → S2 → H1 → S3 →
S4 → S5b → S5a). The next gate is **intentionally unselected** — it must be
chosen separately in the fresh-chat handoff; no new Path C gate is open.

Working tree was clean at the close of the 2026-05-27 v0.2.4 session.
Full suite runs cleanly without the historical
`--ignore=tests\test_visualize_attractors.py` flag — the old
convention is retired. **Dated 2026-06-04 baseline (post B2-S4, `1a17d6f`): 3,812 passed /
5 skipped / 22 subtests passed in 67.52s** under `python -m pytest tests\ -q`
(authoritative Windows run; supersedes the post-B2-S3 baseline of 3,743
passed — re-establish before/during the next code-bearing slice; do not
treat as a permanent count). The focused B2-S4 suite ran **72 passed in
1.66s**. Live S6-style smoke for v0.2.4
archive FILTER-A (hash embedder, disposable workspace) closed at
**32 GREEN / 0 YELLOW / 0 RED**. The next gate is the user's call (see §7).

**2026-05-31 update.** The first active character-memory harness (Probe-v0)
closed and pushed at `5c0b10b`, separate from the frozen `torment_stress_harness/`.
Plumbing, companion-posture preflight, and the clean model-visible prompt contract
all PASS; the post-fix clean reference run is `20260531T193241Z_3059`. The honest
behavioral result: even with a clean prompt, the chosen character/model pairing
turned one surfaced fact into unsupported surrounding manuscript evidence — a
COHERENCE_BROKEN candidate under the pinned rubric, recorded as one bounded
observation, not a product verdict. Disposable `cm_loop_*` workspaces were removed
after review; forensic outputs are preserved local-only under
`character_memory_harness/outputs/`. Source of truth:
`docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md`.

**Strategic roadmap & long-range ordering.** Current *gate state* comes from this
orientation map plus the tracked checkpoints/doctrine above — not from any single
roadmap file. `docs/TORMENT_ROADMAP_NOTES.md` is the tracked long-range strategic
roadmap: it preserves the larger ordering, the ranked post-spine candidates, and
the future storage direction, which remains load-bearing — *TORMENT-governed
memory first, database second* (the FUTURE-CLUSTER-5 custom-storage concern). The
external `ROADMAP_13042026.md` (outside the git repo) is historical Phase A→H
context, **not** current implementation authority; its surviving arc in one line:
*validate → ratify contracts → narrowly authorized automation → substrate/
orchestration boundary → Hermes evaluation → governed operational agents →
Clawbot triage → writeback-readiness gate.*

### Fresh-chat anti-drift clarifications (2026-06-06)

Added after a fresh-chat reconstruction surfaced recurring drift risks. Each
points back to the authoritative section; none opens a gate.

1. **Named scope ≠ opened gate.** The Guidance-Without-Coercion surface map
   (§7, `docs/GUIDANCE_WITHOUT_COERCION_RETRIEVAL_INFLUENCE_SURFACE_MAP_v0.1.md`)
   *names* two audit scopes — the **immediate spirit-return audit** and the
   **broader retrieval-stack audit** — and **opens neither**. Neither is
   automatically next. A descriptive map authorizes no audit, no remedy, no
   patch.

2. **Spirit-return disambiguation.** Two distinct items share the name and must
   not be conflated. The **immediate spirit-return influence audit** is a larger
   *read-only audit scope* over the deep-memory-echo influence path (surface map
   Bucket I: surfaces 1, 3, 4, 5, 6, 7, 9, 10, 11). **Gap C** (see §6 and §7)
   was only the tiny `spirit_return_summary` relationship lock — **CLOSED
   2026-06-06 as a test-only slice** (`aab9f5d`): retrieval-stage character
   summary and entered-prompt-stage assembly-audit summary have conditional
   parity under ample budget, audit-side subset semantics, and designed
   token-budget divergence — **not unconditional equality**. See
   `docs/CHECKPOINT_2026-06_MEMORY_TO_PROMPT_GAP_C_SPIRIT_RETURN_SUMMARY_RELATIONSHIP.md`.
   Different size, different kind; do not collapse one into the other, and Gap
   C's closure does not open the influence audit.

3. **Track B rests after B2-S4 — no B2-S5 is inferred.** B2-S4 (isolated
   counter-contest event persistence, `1a17d6f`) is closed; the cognition-coupling
   fork memo §12 explicitly disclaims a B2-S5. `candidate_handle → eid` binding,
   target-existence integrity policy, counter-contest result routing, and the
   effective-authority resolver-boundary audit remain **separately parked**. Any
   Track B continuation requires a fresh audit-first cycle and explicit operator
   authorization.

4. **Operator-input status — values-layer provided, architecture-layer
   conditional.** Hilmir's values-layer input is **provided and must not be
   reopened as missing**: guidance is allowed; influence is not automatically
   coercion; control means absolute or coercive control; the option-to-ignore is
   load-bearing; memory must not block an AI from changing direction. The
   cognition-coupling fork memo §11's five *architecture* decisions remain open
   but are **conditional on the trio deliberately reopening the cognition-coupling
   lane** — they block nothing at rest and are not pending homework.

5. **Starlette maintenance — closed.** Two bounded maintenance items, both
   Windows-verified, no runtime code touched:
   - *Starlette 1.x security admission* (`fc7d9c8`) — fastapi 0.136.1 /
     starlette 1.2.1 / mcp 1.27.1.
   - *Starlette TestClient httpx deprecation* (`282fbe9`) — **closed by adding
     `httpx2` alongside classic `httpx`** (classic httpx remains because mcp
     still imports it). Root cause: Starlette 1.x's testclient prefers the
     `httpx2` successor package and warns on classic httpx; TORMENT owns no
     direct httpx call. Test-only dependency; the application runtime is
     unchanged.

   Windows-authoritative full suite at `282fbe9`: **3,812 passed / 5 skipped /
   22 subtests passed, 0 deprecation warnings** (agrees with the 2026-06-04
   count at `1a17d6f`). This re-establishes the resting baseline at HEAD.

6. **Maintenance re-survey closed (2026-06-06, no code patch).** The small
   maintenance checklist named in §7 was re-surveyed read-only and found
   already resolved: live model defaults are already harmonized to
   `claude-sonnet-4-6` (the 2026-06-01 slice landed; remaining
   `claude-sonnet-4-5` strings are help-text examples of an active model,
   deliberately left untouched); `TORMENT_SERVER_URL` and `TORMENT_URL` are
   **both intentionally real** — consumed by the bench family and the
   examples/live-agent family respectively — and `.env.example` already
   documents both (name unification stays a separately parked, code-bearing
   slice); the Predicate #7 entry in §6 was corrected to its accurate
   exercise-gated posture. **No functional maintenance patch was required.**
   Do not reopen this checklist without new evidence.

---

## 3. Where project truth lives

TORMENT's project state is distributed across multiple layers. Each layer is
authoritative for its own kind of truth, and any single layer can mislead in
isolation. The seven layers, in the order the gate-start survey should walk
through them (see §5):

**Formal `docs/`** — canonical current doctrine, policy, and design docs.
Examples: `TORMENT_AGENT_DOCTRINE_v0.1.md`, `MCP_CAPABILITY_BOUNDARY.md`,
`TOOL_RESULT_LIFECYCLE_POLICY.md`. If something is doctrinally settled, it
lives here.

**Checkpoint docs (`docs/CHECKPOINT_*`)** — closed-arc audit trails. Each
checkpoint records what shipped, what was tested, what the verdict was, what
was deferred. Source of truth for what was decided when.

**Tests (`tests/test_*.py`)** — behavior is verified here. Sometimes
tests prove a proposal is already implemented before the policy doc catches
up. On 2026-05-24 the `test_tool_result_lifecycle.py` 12/12 PASS surfaced a
doc-implementation mismatch that had been latent.

**Code (`torment_service/`, `examples/`, `tools/`)** — sometimes ships
proposals before docs reflect implementation status. Surveying code with
grep on load-bearing identifiers (env vars, constants, function names from a
proposal) is the cheapest way to catch doc-drift in that direction.

**Scratch (`scratch/`)** — working memory, drafts, raw evidence runs. Some
scratch docs operate as de facto ratified despite "DRAFT" headers. The
2026-05-16 automation audit and the 2026-05-17 long-iteration plan both
drove real ratified execution before they were promoted to `docs/`.
Iteration-run telemetry (`scratch/iteration_runs/`) is preserved here and
should never be committed.

**Branches and commits** — features may live on scoped-out branches or be
reachable only by hash. The `tier0-agent-runtime-telemetry` branch contains
the agent-runner-demo `--provider` / `--jsonl-out` flags that were
deliberately scoped out of PR #52; the relevant commit `ee0f93f` was
cherry-picked onto main as `032aaf8` to recover Tier 2 wrapper
compatibility. Always check `git branch -a` and `git log --all -S
"<identifier>" --oneline` when something seems missing.

**Chat handoffs and `NEXT_CHAT_HANDOFF_*` files** — operational context
between sessions. These may be ratified, untracked, or scratchpad. Read at
session start if present; don't commit unless explicitly chosen.

**Claude's local memory** — collaboration style, closed-arc references,
parked items, feedback rules (e.g. the gate-start survey discipline lives
in `feedback_gate_orientation_survey`). Loaded automatically at session
start. Update when new patterns or closures emerge.

### Strategic source-of-truth layers (for planning / prioritization)

Distinct from the seven runtime-truth layers above, three tiers in descending
authority:

1. **Tracked doctrine / checkpoints** (`docs/`) — the only planning *authority*.
2. **Local-only curated planning artifacts** — optional orientation for local
   (Windows) reviewers; never authority on their own.
3. **Raw brainstorming / review traces** — archaeology only; never authority.

**Local-only planning index** (non-load-bearing; gitignored or outside the repo —
GPT/Codex cannot see these and must not depend on them):

- `scratch/brainstorming/2026-05-30_phase_preparation_handoff.md`
- `scratch/BRAINSTORMING_INVENTORY_2026_05_18.md`
- external `ROADMAP_13042026.md`

Local reviewers may inspect these and relay durable findings into tracked docs or
handoffs; until a finding is summarized into a tracked doc it is not load-bearing
for a decision. Raw brainstorming stays ignored.

---

## 4. `do_not_touch_torment_test_rig/`

This folder is the source of repeated mid-session confusion through 2026-05-24
and deserves an explicit boundary statement.

**What it is:** a historical / local runtime test harness, living inside the
Git repo with the warning prefix `do_not_touch_` — **repo-root; a sibling of
`torment_fabric/`, not nested inside it** (`TORMENT-fabric_v2/do_not_touch_torment_test_rig/`,
alongside `TORMENT-fabric_v2/torment_fabric/`). It produced the Tier 0, Tier 1,
and Tier 2 evidence on disk under `torment_fabric/scratch/iteration_runs/`.
The canonical long-iteration wrapper is
`do_not_touch_torment_test_rig/harness/tier0_smoke.py` — parameterized via
`--iterations` and `--label` to drive Tier 0 / Tier 1 / Tier 2 / pack-
composability runs through a single ~680-line file.

**What the prefix means:** "do not casually edit." It does *not* mean
"forbidden forever," "not in use," or "unsafe to read." The prefix is a
self-warning about venv/Linux-prep complexity.

**Operational boundary:**

- **Read OK** — inspect to understand wrapper behavior, flags, denylist
  presence, telemetry shape.
- **Run only when ratified** — the existing wrapper is the ratified runner
  for the long-iteration evidence ladder. Running it for a sanctioned
  Tier/Batch is fine. Running for ad-hoc curiosity isn't.
- **Edit requires a separate slice** — any code change (e.g. implementing
  the W6 denylist that exists in plan but not in code; supporting Batch C
  accumulating workspace mode) is its own ratifiable arc with audit + plan.
- **Delete requires a separate slice** — deletion or migration to formal
  `tools/` or `tests/` is itself a ratifiable arc, not casual cleanup.
- **Do not treat as core TORMENT** — it is local test infrastructure, not
  part of the public release surface.
- **Do not chase the rig unless runtime-harness work is explicitly chosen.**
  A full rig audit or deletion/migration plan may be opened later only if
  the rig becomes load-bearing for a new slice.

The rig's existence is not the problem. The problem is when a session mistakes
the rig for the next investigation target instead of treating it as bounded
infrastructure. §4 of this map exists to prevent that mistake.

---

## 5. Gate-start survey rule

Before proposing design, taxonomy, plan, or patch for any new gate, survey the
seven layers in this fixed order:

1. **Formal `docs/`** — is there already a ratified doctrine / policy / plan?
2. **`scratch/`** — is there a working-memory draft that may already be ratified
   in practice?
3. **Tests** — does the behavior already exist as verified test code?
4. **Existing code** — grep for the load-bearing identifiers (env vars,
   constants, function names) from any proposal you're about to make.
5. **Branches and commits** — `git branch -a`, `git log --all --oneline -20`,
   `git log --all -S "<identifier>" --oneline`.
6. **`do_not_touch_torment_test_rig/`** — only if the gate involves runtime
   or test-harness behavior.
7. **Prior checkpoint docs** — `docs/CHECKPOINT_*` for the closure trail of
   related arcs.

Only after all seven layers have been surveyed should design or planning
proceed.

**Why this discipline:** three high-cost "this already exists" moments
occurred 2026-05-24 in one session — automation taxonomy already drafted in
scratch; long-iteration wrapper coupled to a telemetry-branch commit not on
main; tool-result lifecycle hardening already shipped in v2.4.3 with passing
tests. Each was caught by the survey phase, but only because the survey
eventually reached the right layer. The seven-layer order makes this
systematic instead of luck-dependent.

Memory companion: this rule is also captured in Claude's local memory as
`feedback_gate_orientation_survey`.

**Role-awareness.** The numbered survey is for Windows-local reviewers (Claude),
who can inspect `scratch/` and the local-only planning traces when relevant. GPT
and Codex survey only the tracked layers (1, 3–5, 7) and must not pretend to
inspect local-only material they cannot see. Any durable finding from a local-only
artifact must be summarized into a tracked doc or handoff before it can be
load-bearing for a decision. Claude's local memory is collaboration context, not
project authority.

---

## 6. Parked items index

Items that have been deferred from an active slice but are not lost:

- **Writer-path / endpoint-wiring characterization triad — parked fixes** — the
  Seam 1–3 chain (closed read-only / test-only, characterization only) parks all
  future *fixes* without opening them: `_maybe_emit_identity_anchor` writer
  authority and `promote_chunk` / `POST /promote` force authorization →
  writer-authority reconciliation slice; identity-anchor presence→source-membership
  → P4 O2; `drift_reflex_callback` wiring (if ever) → separate cognition-affecting
  slice. See `docs/CHECKPOINT_2026-06_WRITER_PATH_CHARACTERIZATION_TRIAD.md` §5.
  None opened.
- **mood_drift → drift-centroid inclusion (Lane A) — topology recorded read-only**
  — the `mood_drift → drift centroid → gravity_correction → canon=True` path is
  recorded as an active inclusion path for eligible rows (topology only; no
  magnitude/decisiveness/harm claim). Any future magnitude characterization or
  governance consideration remains parked and unopened; no filtering, gravity, or
  runtime requirement is implied. See
  `docs/CHECKPOINT_2026-06_MOOD_DRIFT_CENTROID_INCLUSION_TRACE.md`. None opened.
- **Issue #54 cross-before-design barrier — re-verified clean at `01ec838`**
  (2026-06-17; test-only/docs-only work only since `0563a84`). Recorded in the
  existing post-N16 Issue #54 checkpoint doc
  (`docs/TORMENT_GOVERNED_MEMORY_SUBSTRATE_POST_N16_ISSUE_54_CLEAN_CHECKPOINT_v0.1.md`
  §6). L2 Stage B Opening Decision is named but unopened; database/substrate
  design and construction remain unopened.
- **L2-A Pre-Stage-B Ratification Audit — CLOSED read-only (2026-06-17)** — synthesis
  of read-only archaeology + Codex adversarial challenge; found no structural blocker
  to *preparing* the L2 Stage B Opening Decision, provided the Codex objections and the
  old-doc authority quarantine are carried into the L2 packet. Records carry-forward
  warnings only; selects no mechanics; edits no prior design/roadmap/archive docs. See
  `docs/TORMENT_L2A_PRE_STAGE_B_RATIFICATION_AUDIT_CLOSURE_v0.1.md`. **L2 remains
  unopened**; Stage B / database / schema / carriers / migration remain unopened.
- **L2 Stage B Opening Decision — operator-authorized: Stage-B-to-framing only (2026-06-17)**
  — operator authorized opening a **bounded framing lane only**; its **first task is
  dream/cognition/thinking/private-state/guided-memory roadmap completion and
  ratification-to-implementation sequencing** (cognition-layer-first, *not* database
  mechanics). **Mechanics, schema/storage/carriers/migration, construction, P4 runtime
  conformance, Seed-Gov implementation, writer-authority fixes, and canon_source all
  remain unopened.** Old-doc authority quarantine and guidance-not-control remain binding.
  See `docs/TORMENT_L2_STAGE_B_OPENING_DECISION_RECORD_v0.1.md` (supersedes the proposed
  packet `…_PACKET_PROPOSED_v0.1.md`). No registry amendment / number taken.
- **Cognition roadmap completion / sequencing map — FILED read-only (2026-06-17)** — the L2
  framing lane's first deliverable: a READ-ONLY / FRAMING / SEQUENCING-ONLY map of the
  dream/cognition/thinking/private-state/seed/guided-memory layers (four buckets: ratified
  requirement / live pre-contract / parked non-conformance / not-yet-built conformance). Names
  **candidate gates only** (Gate 0 filing; A containment/advisory-boundary; B write-side authority
  + visible writer-hazard targets; C P4 read-side framing; D Layer-1 thinking + Envelope Audit
  ephemeral; deferred substrate-dependent set) — order intent A→P4→Document B, Regime B dream
  deferred, Cluster 2 v0.2 verification-pending. **No implementation, mechanics, construction, P4,
  Seed-Gov, writer fixes, canon_source, or dream runtime opened.** Old-doc quarantine binding. See
  `docs/TORMENT_COGNITION_ROADMAP_COMPLETION_AND_IMPLEMENTATION_SEQUENCE_v0.1.md`.
- **Governed-Memory Substrate — Stage A / Stage B Boundary Framing — FILED read-only (2026-06-20)** — the
  current **governed-memory substrate boundary-framing anchor**: defines the Stage A (recovery /
  reconciliation **semantics**) vs Stage B (carrier / substrate **mechanics**) boundary and the
  carry-forward constraints; restates the §K eligibility evidence (incl. the narrowed
  `INGEST-NOT-TRANSACTIONAL`). **Stage B remains unopened**; no mechanics / schema / storage / carriers /
  migration selected; no registry amendment. See
  `docs/TORMENT_GOVERNED_MEMORY_SUBSTRATE_STAGE_A_STAGE_B_BOUNDARY_FRAMING_v0.1.md`.
- **Gate A — opened CHARACTERIZATION-ONLY (2026-06-17)** — Document A containment /
  live-advisory boundary, opened only as a characterization gate; first and only authorized
  deliverable is a **read-only boundary trace plan** (what evidence will be gathered later).
  Carries Codex's sharpening: advisory is influence not automatically harmless; retrieval
  shaping + Phase-7 turn-summary ingest must be traced; ordinary ingest ≠ Document B admission.
  **No code, no tests, no fixes, no implementation, no runtime change.** Writer hazards stay
  visible/parked for Gate B; no P4/Document B/dream/candidate-store/durable-private-state/
  database mechanics opened. Trace execution and any tests-only locks require separate later
  authorization. See `docs/TORMENT_GATE_A_LIVE_ADVISORY_BOUNDARY_TRACE_PLAN_v0.1.md`.
- **Gate A characterization checkpoint — FILED (2026-06-17)** — trace executed read-only;
  characterized boundary recorded with Codex's precision correction. Three-way model:
  (1) no direct advisory write found; (2) **`fabric.query` has retrieval-internal state effects**
  (warmup-state persist, evolved-SRG payload mutation) — so "read-only" means *no direct advisory
  authority writer, not no mutation anywhere*; (3) **Phase-7 ordinary ingest is the real
  response-to-memory path** (`AgentRunner.run_turn` → `fabric.ingest` of a turn summary), and
  ordinary ingest ≠ Document B admission. `/agent/query` uses only the MemoryPlan (draft/review/
  stance discarded), no direct ingest/promote/gravity. Writer hazards stay parked Gate B; residuals
  open (query-mutation durability, Spine/audit durability, fan-out→hazard reach). **No tests, code,
  fixes, locks, or implementation authorized.** See
  `docs/TORMENT_GATE_A_LIVE_ADVISORY_BOUNDARY_CHARACTERIZATION_CHECKPOINT_v0.1.md`.
- **Gate A tests-only lock proposal — FILED docs-only (2026-06-17)** — proposes tests-only
  regression-lock **candidates C1–C5 only**, under Codex constraints (locks describe *current
  direct-call absence / current routing / current shape*, never "safety," never a future-freezing
  negative): C1 advisory-module direct-call absence (AST guard, advisory modules only); C2 `/agent/query`
  consumes only MemoryPlan; C3 `/agent/query` no direct ingest/promote/gravity; C4 MemoryPlan shape only
  (no fabric.query clamp); C5 Phase-7 ordinary-ingest routing characterization. **C6 (Document B absence)
  rejected** — would tripwire future governed implementation. **No tests/code/fixes/locks/implementation
  authorized;** tests remain separate authorization. See
  `docs/TORMENT_GATE_A_TESTS_ONLY_LOCK_PROPOSAL_v0.1.md`.
- **Gate A — CLOSED as advisory-boundary characterization + tests-only lock (2026-06-17, `d0315a0`)** —
  Gate A advisory-boundary characterization is closed at `d0315a0`. Closure doc:
  `docs/TORMENT_GATE_A_ADVISORY_BOUNDARY_CLOSURE_CHECKPOINT_v0.1.md`. Gate A closed **only** as
  advisory-boundary characterization + tests-only lock. It does **not** certify runtime safety, does
  **not** fix writer hazards, and does **not** open database/substrate construction. Next likely step:
  **Gate B writer-authority hazards**, pending explicit operator authorization.
- **Gate B — writer-authority hazard inventory FILED read-only (2026-06-17, `39ce57f`)** — Gate B
  writer-authority hazard inventory is filed at `39ce57f`. Inventory doc:
  `docs/TORMENT_GATE_B_WRITER_AUTHORITY_HAZARD_INVENTORY_v0.1.md`. This is **Gate B framing only**: a
  read-only hazard inventory (H1–H6) — **no** writer fix, **no** tests, **no** implementation, **no**
  registry edit. It does **not** open database/substrate construction, P4/source-sameness, Seed-Gov
  implementation, Document B runtime, or dream/incubation runtime. Next likely step: a **Gate B
  writer-authority decision artifact**, pending explicit operator authorization (no auto-open of fixes).
- **Gate B — writer-authority decision frame FILED definitional-only (2026-06-17, `4b50a63`)** — the
  Gate B writer-authority decision framing is filed at `4b50a63`. Decision-frame doc:
  `docs/TORMENT_GATE_B_WRITER_AUTHORITY_DECISION_FRAME_v0.1.md`. **Definitional-only:** it ratifies only
  the write-side authority boundary, the requirement-level "governed writer" vocabulary, and a
  non-binding consideration grouping. It **governs, fixes, selects, or builds no writer** — no mechanism,
  no governance-vehicle selection, no behavior change, no registry edit; it opens no new gate and no
  P4/source-sameness, Seed-Gov, Document B, dream/incubation, candidate-store, durable-private-state, or
  database/substrate work. Any later target-selection or governance-vehicle determination requires a
  separate explicit operator authorization.
- **Gate B1 — first writer-authority reconciliation subject selection FILED (2026-06-19, draft pending Codex/operator review)** —
  Gate B1 (adjacent to Gate B, **not** an amendment that begins implementation) names the **first
  reconciliation subject**. Selection doc:
  `docs/TORMENT_GATE_B1_FIRST_WRITER_AUTHORITY_RECONCILIATION_SUBJECT_SELECTION_H3_v0.1.md`. **Subject
  selected: H3 (`POST /promote` force bypass).** Selection only — **selected for tractability, not
  severity**; **H1 remains parked and is not de-risked** (its sharper automatic-authority concern stands
  on the record). Authorizes **no** implementation, tests, writer fix, promote redesign, behavior change,
  governance-vehicle selection (incl. Cluster 2 v0.2), registry edit, H1/`gravity_correction` work,
  Phase-7 write emissions, P4/source-sameness, Seed-Gov, canon-semantics change, or database/substrate.
  Any later H3 code slice requires a separate target-specific design and authorization.
- **Gate B1 — H3 bounded writer-authority question frame FILED (2026-06-19, Codex ACCEPT — no corrections)** —
  the H3-scoped, **requirement-level-only** question frame (the H3 analogue of the Gate B decision
  frame). Artifact: `docs/TORMENT_GATE_B1_H3_BOUNDED_WRITER_AUTHORITY_QUESTION_FRAME_v0.1.md`. **Frame
  only** — it poses the bounded H3 authority question and names a requirement-level question space; it
  selects no remedy, mechanism, or vehicle. Preserves H3's **two-effect `force=True` shape**: (a)
  evaluator **pre-loading** with `is_canon=True` / `user_approved=True`, and (b) execution **bypass**
  through `if result.promote or req.force` — not "force skips evaluation." The upstream `/promote`
  caller-auth surface **remains untraced/open** (no caller trust posture assumed). Visibility /
  provenance / contestability / bounded authority posture are **questions only, not mechanisms**. H3
  remains **selected for tractability, not severity**; **H1 remains parked and not de-risked**.
  Authorizes **no** implementation, code, tests, writer fix, promote redesign, endpoint behavior change,
  approval/auth policy, governance vehicle (incl. Cluster 2 v0.2), canon-semantics change,
  H1/`gravity_correction`, Phase-7, P4/source-sameness, Seed-Gov, database/substrate, or registry
  amendment.
- **Gate B1 — H3 Evidence-Readiness Note FILED (2026-06-19, Codex ACCEPT WITH CORRECTIONS — applied: "evidence ledger" → "evidence record")** —
  HEAD-specific (`a91b79a`) H3 **evidence record** (satisfied vs not determined), ahead of any later H3
  target-specific design. Artifact: `docs/TORMENT_GATE_B1_H3_EVIDENCE_READINESS_NOTE_v0.1.md`.
  **Evidence-readiness only** — not a next action, remedy, mechanism, or implementation step. Preserves
  the **two-effect `force=True` shape** (a. evaluator pre-loading `is_canon=True` / `user_approved=True`;
  b. execution bypass `if result.promote or req.force`). Safe app-layer finding (verbatim): "No in-repo
  FastAPI application-layer authentication or authorization wiring was found on `/promote` in the
  surveyed source at this HEAD." Deployment/network exposure **not repo-determinable** (operator-supplied
  / not determined). Logging/provenance fact (neutral): the existing promotion log / row payload does
  **not** distinguish a force-route promotion from an evaluator-approved one — no obligation implied.
  Observed force-promotion frequency/artifacts **not determined read-only** (no inference of zero). H3
  remains **selected for tractability, not severity**; **H1 remains parked and not de-risked**.
  Authorizes **no** endpoint change, tests, auth-policy selection, governance vehicle,
  H1/`gravity_correction`, Phase-7, database/substrate, writer fix, promote redesign, canon-semantics
  change, P4/source-sameness, Seed-Gov, registry amendment, or hidden finalizer / output blocker /
  identity pinning / monitoring/autonomy layer / durable user-risk scoring / coercive mechanism.
- **Thinking Layer — tuned-scoring provenance lock (tests-only; 2026-06-19, `cbdc609`)** —
  **protection slice, not behavior change.** Test-characterizes the current output of
  `_estimate_ambiguity` / `_estimate_urgency` (via `frame_task`) — the additive bucket basis the locked
  0.60/0.72 thresholds depend on. Pins per-signal contributions and the reachable buckets (ambiguity
  `{0.0,0.20,0.35,0.40,0.55,0.60,0.75,0.95}`; urgency `{0.0,0.1,0.2,0.3,0.6,0.7,0.8,0.9}`; 1.0
  unreachable), the `??`-guard distinction (a 0.95 `??` input is > 0.72 but blocked from primary
  clarification by `"?" not in lower`), and the `urgency > 0.7` override boundary. **No value, threshold,
  shared constant, or behavior changed; no production code changed.** Checkpoint:
  `docs/CHECKPOINT_2026-06_THINKING_LAYER_TUNED_SCORING_PROVENANCE.md`. Validation: 18 + 307 focused
  passed; full suite 3975 passed / 5 skipped / 22 subtests. **Thinking Layer should pause after this**
  unless a new bounded slice is separately found.
- **Thinking Layer — ambiguity-threshold provenance lock (test+comment; 2026-06-19, `d2e26cd`)** —
  **protection slice, not behavior change.** Corrected the misleading `action_policy` comment that claimed
  the 0.60 fallback clarify threshold "matches" the 0.72 primary `choose_action` bar, and added tests
  locking the **intentional** distinction: primary does not clarify below 0.72 (bucket-calibrated);
  fallback clarifies at 0.60, defers at 0.59; drift guard `0.60 < 0.72`. **No threshold value changed, no
  shared constant, no behavior change.** Checkpoint:
  `docs/CHECKPOINT_2026-06_THINKING_LAYER_AMBIGUITY_THRESHOLD_PROVENANCE.md`. Validation: 166 + 135
  focused passed; full suite 3969 passed / 5 skipped / 22 subtests. **Tuned constants are not cleanup
  dust** — future threshold changes require provenance archaeology (source / tests / docs / history /
  operator context) first.
- **Gate B1 — H3 force-route provenance LANDED (runtime slice; 2026-06-19, `ae242af` + `6d50254`)** —
  the **first H3 runtime improvement**. `POST /promote` now stamps `promotion_force_requested` +
  `promotion_evaluator_promote` into the promoted row's `extra_payload`, so a force-bypass canon write
  is **durably distinguishable** from an evaluator-approved one; `promote_chunk` **fails closed** if
  `extra_payload` tries to override a reserved core key (`memory_class`, `kind`, `tier`, `source_ref`,
  `promoted_at`, `canon`). **Provenance only — not control**: promotion eligibility, endpoint response,
  auth, governance, and canon semantics unchanged. Checkpoint:
  `docs/CHECKPOINT_2026-06_GATE_B1_H3_FORCE_ROUTE_PROVENANCE.md`. Validation: focused **30 passed**; full
  suite **3965 passed / 5 skipped / 22 subtests**. Selects **no** auth policy, governance vehicle,
  endpoint redesign, H1/`gravity_correction`, Phase-7, Seed-Gov, P4, private cognition, dream runtime, or
  database/substrate. H3 remains a **leaf** under Writer Authority / Document A; **H1 remains parked and
  not de-risked**; database/substrate remains last.
- **Gate 4 — read-only runtime-conformance selection frame FILED docs-only (2026-06-19, `dd53b7e`)** —
  selects Gate 4 first **only at read-only runtime-conformance selection level** (old identity-pressure
  conformance-gap framing); **this is not a Writer Authority un-pause**. Artifact:
  `docs/TORMENT_GATE_4_READ_ONLY_RUNTIME_CONFORMANCE_SELECTION_FRAME_v0.1.md`. **Gate 1 deferred** until
  the old live identity-pressure floor is framed against existing boundaries; **Gate 2 and Gate 3
  deferred** as substrate-coupled mechanism work (seed-revision / candidate-store / governed-admission).
  Selects **no** writer patch, remedy, enforcement, governance vehicle, or runtime authority gate, and
  **no** P4/source-sameness, Seed-Gov mechanics, chamber/private-cognition runtime, candidate store,
  governed admission implementation, or database/substrate; database/substrate remains last. **No
  automatic successor gate** — only a separately authorized read-only Gate 4 conformance-gap map may
  follow.
- **Gate 4 — read-only conformance-gap map FILED docs-only (2026-06-19, `41c4349`; Codex ACCEPT WITH
  CORRECTIONS, applied)** — the separately authorized read-only successor to the selection frame.
  Artifact: `docs/TORMENT_GATE_4_READ_ONLY_CONFORMANCE_GAP_MAP_v0.1.md`. **Read-only gap characterization
  only** — for each path it records *conformance posture not yet recorded → not-yet-conformant / requires
  reconciliation*, with **no verdict, no remedy, no fix order, no writer-patch selection, no enforcement,
  no governance vehicle, no runtime authority gate**. Five **core runtime rows**: `gravity_correction`;
  derived identity anchors; `mood_drift`→drift-centroid→`gravity_correction` (**topology only**);
  spirit-return warmth/warmup; role inference / identity-anchor cadence. Authored `seed_text` is
  **boundary context only — no automatic-writer gap**. Adjacencies (not core rows): H3
  writer-authority-adjacent, **not** automatic identity-pressure; H5 binding-contingent / parked; H6
  eligibility / reachability only. Selects **no** implementation, tests, runtime, P4/source-sameness or
  Seed-Gov mechanics, chamber/private-cognition runtime, candidate store, governed admission
  implementation, or database/substrate. **No automatic successor gate** — any later step needs separate
  authorization; database/substrate remains last.
- **Gate 4 — `gravity_correction` row conformance-question frame FILED docs-only (2026-06-20, `03af2c3`;
  Codex ACCEPT WITH CORRECTIONS, applied)** — the **first row-specific** read-only conformance-**question**
  frame, scoped to **exactly one row: `gravity_correction`**. Artifact:
  `docs/TORMENT_GATE_4_GRAVITY_CORRECTION_READ_ONLY_CONFORMANCE_QUESTION_FRAME_v0.1.md`. **Question framing
  only** — poses **Q-C1–Q-C4** (automatic-canon-vs-governed-crossing; writer-authority-vs-payload-flag;
  single-`canon`-flag-vs-canon-by-source; soft-guidance→canon chain, **gravity end only**) **posed only,
  not answered**. The §N14 `gravity_correction` audit-first reconciliation memo remains the
  **doctrine-status / later-owner routing** (already done); this frame **does not duplicate, re-open,
  re-scope, amend, or answer** §N14 or its Q-G1–Q-G7. `mood_drift`→drift-centroid→`gravity_correction` is
  a **dependent topology-only** path (no causal/magnitude/frequency claim); the mood-topology question
  **would be eligible only as a later separately authorized frame**; the A→B→C→D order is a **framing
  sequence, not a fix order**. Selects **no** verdict, remedy, writer patch, fix order, enforcement,
  governance vehicle, runtime authority gate, P4/source-sameness or Seed-Gov mechanics,
  chamber/private-cognition runtime, candidate store, governed admission implementation, or
  database/substrate. **No automatic successor gate** — any later step needs separate authorization;
  database/substrate remains last.
- **Gate 4 — mood_drift centroid-inclusion topology row conformance-question frame FILED docs-only
  (2026-06-20, `cc6cac4`; Codex ACCEPT WITH CORRECTIONS, applied)** — the second row-specific read-only
  conformance-**question** frame, scoped to **one row: mood_drift centroid-inclusion topology /
  reachability only** (an in-window same-agent `mood_drift` `canon=False` row is eligible for inclusion in
  the `measure_drift` recent-memory centroid upstream of the `gravity_correction` writer). Artifact:
  `docs/TORMENT_GATE_4_MOOD_DRIFT_CENTROID_INCLUSION_TOPOLOGY_CONFORMANCE_QUESTION_FRAME_v0.1.md`.
  `gravity_correction` appears as **hard-canon endpoint context only**. **Question framing only** — poses
  **Q-M1–Q-M4 posed only, not answered** (primary boundary Seed-Gov **SG-O6**). **No causal, magnitude,
  frequency/workspace, usually-triggers, or decisiveness claim; no unsafe/defect/contaminated/block/filter
  claim.** Does **not re-answer** the gravity frame's Q-C1–Q-C4 and **does not resolve or re-pick** §N14
  Q-G7. A→B→C→D is a **framing sequence, not a fix order**; later C/D frames only if **separately
  authorized**. Selects **no** verdict, remedy, writer patch, fix order, enforcement, governance vehicle,
  runtime authority gate, P4/source-sameness or Seed-Gov mechanics, chamber/private-cognition runtime,
  candidate store, governed admission implementation, or database/substrate. **No automatic successor
  gate** — any later step needs separate authorization; database/substrate remains last.
- **Gate 4 — derived identity anchors row conformance-question frame FILED docs-only (2026-06-20,
  `8953b90`; Codex ACCEPT WITH CORRECTIONS, applied)** — **row C** in the A→B→C→D **framing sequence (not
  a fix order)**, scoped to **exactly one row: `torment_service/fabric.py::_maybe_emit_identity_anchor`**
  (an **automatic derived identity-family writer**, **`canon=False`**, `anchor_origin="derived"` /
  `anchor_source="motif_cluster"`, motif count/gap-gated; may retire a prior same-motif anchor as
  write-surface behavior only). Artifact:
  `docs/TORMENT_GATE_4_DERIVED_IDENTITY_ANCHORS_READ_ONLY_CONFORMANCE_QUESTION_FRAME_v0.1.md`. Reentry is
  **ordinary-tier / ordinary-reentry only**; **any separate promotion question is outside this frame,
  unopened and unevaluated**. **Question framing only** — poses **Q-D1–Q-D5 posed only, not answered**
  (**Q-D4** opens no `update_payload` repair, stored-edge repair, or P4/Q lineage mechanics). **P4 O2
  named only as requirement / posture** — **no source-membership proof design, no source-sameness/P4
  mechanics, no `diagnostic_only` implementation**. Role cadence and affect-sensitivity are **context
  only, not scope**. Selects **no** verdict, canon claim, automatic promotion, remedy, writer patch, fix
  order, enforcement, governance vehicle, runtime authority gate, Seed-Gov mechanics,
  chamber/private-cognition runtime, candidate store, governed admission implementation, or
  database/substrate. **No automatic successor gate** — any later step needs separate authorization;
  database/substrate remains last.
- **Gate 4 — spirit-return warmth / warmup (D1) row conformance-question frame FILED docs-only
  (2026-06-20, `f54b8e7`; Codex ACCEPT WITH CORRECTIONS, applied)** — **row D1** in the split-D framing
  sequence (**D1 = spirit-return warmth (this frame); D2 = role inference / identity-anchor cadence,
  separate and unopened**); **D1 and D2 are distinct runtime surfaces, not conflated**. Scoped to **one
  row: spirit-return warmth / warmup only** — a **durable-soft, non-canon** retrieval/prompt-shaping signal
  tracked **per deep-memory EID**, persisted in `warmup_state.jsonl` (append-only with compaction /
  path-integrity carried only), scaling spirit-return hit strength via a per-mode multiplier, where
  `return_mode` + warmth thresholds **may influence block classification including possible identity-block
  placement** (a **prompt-assembly classification only — not canon/admission/promotion/authority**).
  Artifact: `docs/TORMENT_GATE_4_SPIRIT_RETURN_WARMTH_READ_ONLY_CONFORMANCE_QUESTION_FRAME_v0.1.md`.
  **Retrieval/prompt-shaping only — `durable` ≠ `pinned`; no graph-memory write; no authority crossing.**
  **Question framing only** — poses **Q-W1–Q-W4 posed only, not answered** (boundaries Stage A **O6**,
  Seed-Gov **SG-O6/SG-O8**, named as requirement/posture). Selects **no** patch/block/filter warmth, O6
  mechanics, must-not-pin implementation, Seed-Gov mechanics, canon claim, authority claim, verdict,
  remedy, writer patch, fix order, enforcement, governance vehicle, runtime authority gate,
  chamber/private-cognition runtime, candidate store, governed admission implementation, or
  database/substrate. **No automatic successor gate** — any later step needs separate authorization;
  database/substrate remains last.
- **Gate 4 — role inference / identity-anchor cadence (D2) row conformance-question frame FILED docs-only
  (2026-06-20, `f466a01`; Codex ACCEPT WITH CORRECTIONS, applied)** — **row D2** in the split-D framing
  sequence (**D2 = role inference / identity-anchor cadence (this frame); D1 = spirit-return warmth,
  separate and already framed**); **C derived identity anchors is downstream context only**, and
  **D2 / C / D1 are distinct runtime surfaces**. Scoped to **one row** — a **durable-soft, non-canon**
  role profile in `roles.json`, **deterministic/offline/model-free keyword-scored**, **slow EMA from
  ingest-summary text**, whose `dominant_role` maps to `anchor_count_mult` / `anchor_gap_mult` and
  **modulates `_maybe_emit_identity_anchor` cadence** (**indirect cadence modulation — not direct
  identity-anchor writing**). Artifact:
  `docs/TORMENT_GATE_4_ROLE_INFERENCE_CADENCE_READ_ONLY_CONFORMANCE_QUESTION_FRAME_v0.1.md`. **Diagnostic
  read-surface exposure is reporting only, not prompt authority**; **role profile ≠ identity authority,
  ≠ persona/voice writing; durable-soft ≠ pinned.** **Question framing only** — poses **Q-R1–Q-R4 posed
  only, not answered** (boundary Stage A **O6**, named requirement/posture); **does not re-answer
  Q-D1–Q-D5 or Q-W1–Q-W4**; **does not open or continue any writer-authority work — it only characterizes
  the cadence-modulation surface**. Selects **no** O6 mechanics, must-not-pin implementation, Seed-Gov
  mechanics, canon claim, authority claim, verdict, remedy, writer patch, fix order, enforcement,
  governance vehicle, runtime authority gate, chamber/private-cognition runtime, candidate store, governed
  admission implementation, or database/substrate. **No automatic successor gate** — any later step needs
  separate authorization; database/substrate remains last. **With this D2 frame the Gate 4 per-row
  question-framing pass over the five core runtime rows (A gravity / B mood-topology / C derived anchors /
  D1 warmth / D2 role-cadence) is now complete as a question-framing pass only — not a fix order, not a
  remedy selection, not implementation, and not a closure of the posed questions.**
- **Post-Gate-4 cognition sequencing comparison frame FILED docs-only (2026-06-20, `5472639`)** —
  **comparison / sequencing only, selects none; decision pending operator selection.** Artifact:
  `docs/TORMENT_POST_GATE_4_COGNITION_SEQUENCING_COMPARISON_FRAME_v0.1.md`. **Not a bare "Gate 1" frame**
  ("Gate 1" is a legacy/ambiguous label); uses **cognition-roadmap candidate-gate vocabulary**. Compares
  three options only: **(1)** Candidate Gate D — Layer-1 private thinking + Envelope Audit, **ephemeral
  only**, inside Document A's wall and behind P4; **(2)** continue **"A wall → P4 gates"** framing first;
  **(3)** pause / handoff-only. Anchored on the cognition-roadmap sequence doc + Document B + this map,
  without duplicating or amending them. Authorizes **no** implementation, runtime, mechanics, durable
  chamber continuity, raw-reflection durability, candidate store, recovery, scheduler/trigger/budget,
  P4/source-sameness, Seed-Gov, or O6 mechanics, database/substrate, Gate 4 question resolution, contract
  amendment, ThinkingController/Document B conflation, automatic successor gate, or registry amendment.
  **Decision remains the operator's; no option opened.**
- **ReflectionTrace v0.2 — private-cognition observability checkpoint (2026-06-17, `d15d9c5` + `3d0ba1a`)** —
  code slices `d15d9c5` and `3d0ba1a` landed an **ephemeral, non-reentrant, debug-observable**
  decision-shape trace (`torment_service/reflection_trace.py`, surfaced via `ThinkingResult.to_dict()` /
  `/thinking/debug`). Checkpoint:
  `docs/CHECKPOINT_2026-06_REFLECTION_TRACE_V0_2_PRIVATE_COGNITION_OBSERVABILITY.md`. **Database remains
  last.** Next work should continue **code-grounded** private-cognition / thinking improvements unless a
  future slice crosses persistence, canon/identity, model-visible cognition, or authority boundaries — in
  which case it is a separate, explicitly-authorized step.
- **ReflectionTrace runner-path parity — live-seam observability checkpoint (2026-06-19, `df6ffce`)** —
  `AgentRunner.run_turn()` now attaches an end-of-turn, observation-only trace to
  `TurnResult.reflection_trace`, built from already-computed runner locals after review and tracking the
  **Phase-5 effective action** (not the Phase-4 `bundle.action_decision`). `DeliberationBundle`,
  `TurnContext`, and the `ReflectionTrace` schema are unchanged; the production non-reentry source scan
  stays green **unmodified** (construction is a constructor keyword, never an attribute read). Codex
  **approved with corrections**. Checkpoint:
  `docs/CHECKPOINT_2026-06_REFLECTION_TRACE_RUNNER_PARITY.md`. ReflectionTrace observability is now
  covered on **both** the `/thinking/debug` path and the runner path and is **closed for now** unless a
  future, separately-authorized behavior slice needs it; **database remains last**.
- **Batch C accumulating workspace** — the long-iteration plan §3 Batch C
  design target. Wrapper code change required (`tier0_smoke.py` currently
  creates fresh-per-iteration workspaces). Separate ratifiable slice if
  ever opened.
- **Tier 3 endurance (6,000 turns)** — deferred until a specific question
  demands more data than Tier 2 (5,400 turns) already provides. Plan §2 was
  explicit: Tier 3 is not run by default.
- **Lifecycle telemetry per turn in wrapper** — useful enhancement deferred
  2026-05-24 to avoid changing the test harness right before Tier 2 scale-up.
  Could land later as a wrapper edit slice.
- **`do_not_touch_torment_test_rig/` full audit / migration / deletion** —
  per §4 above, only if the rig becomes load-bearing for a new slice.
- **§3 future-work items from `TOOL_RESULT_LIFECYCLE_POLICY.md` §3.3** —
  TTL / hard expiry, deep routing preference, spirit return exclusion,
  per-tool-name half-life, freshness detection, auto-refresh, scheduled
  decay sweeps. All still correctly deferred.
- **`/agent/query` / `/retrieve` character_context surfacing reconciliation** —
  read-only trace refined the v0.2.2 parked shorthand. When character_context is
  built, both endpoints can surface it, but in different response shapes:
  `/agent/query` returns `fabric.query(...)` verbatim, including the full current
  `assemble_character_context` dict, while `/retrieve` adds only its curated
  stable character_context subset to `assembled.to_dict()`. When no
  character_context is built, both omit it. This records API-response
  observability only; no prompt / assembled_text behavior was changed or traced,
  and no parity or surfacing-policy decision is made here.
- **Gap C — spirit-return summary relationship lock — CLOSED 2026-06-06**
  (test-only, commit `aab9f5d`; checkpoint
  `docs/CHECKPOINT_2026-06_MEMORY_TO_PROMPT_GAP_C_SPIRIT_RETURN_SUMMARY_RELATIONSHIP.md`).
  The v0.2.3 §A shorthand ("the two summaries agree when both fire") was
  sharpened by audit-first tracing: the character summary is retrieval-stage
  observability (post-query-filter hits); the audit summary is
  entered-prompt-stage observability (post-token-budget blocks). Locked
  relationship: conditional parity under ample budget; audit-side subset
  semantics; designed divergence under token pressure; audit-only
  `any_entered_prompt` truthfulness. No production change. Unknown-mode
  vocabulary asymmetry and synthetic warmth-fallback asymmetry are observed
  and parked, not widened into validation.
- **Deterministic attractor visualization fixture / science validation**
  — named in `docs/CHECKPOINT_2026-05_VISUALIZE_ATTRACTORS_SUITE_RESTORE.md`
  §A as the path to turn the visualize-attractors tests from "not
  broken" into "scientifically meaningful." Larger; not blocking;
  deferred unless visualization correctness becomes load-bearing.
- **Probe-v0 presupposition-loaded callback** — the current callback
  presupposes a shared chapter-seven passage state. A non-presupposing
  variant (allowing honest uncertainty) belongs to the next character-memory
  instrument, not Probe-v0. Named in
  `docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md`.
- **Probe-v0 relational-count observability mismatch** — currently explained by
  different populations and snapshot timing: `tier_breakdown.relational` counts
  relational hits surfaced in the current query, while `relational_count` is the
  last drift-snapshot private-graph relational census passed through from
  `CharacterState`. The "No relational memories yet..." recommendation follows the
  snapshot counter, so it can lag a relational hit surfaced this turn. This is an
  observability/telemetry note only; no prompt/model-visible contract, retrieval
  behavior, or counter relationship is changed or asserted here.
- **Probe-v0 `agent_locks=2` at preflight** — observed before workspace
  creation during the `3059` run; verify agent locks release cleanly across
  runs. Small observability check, not blocking.
- **Predicate #7 hardening (Tier-1 harness)** — wording corrected 2026-06-06
  after a read-only re-survey: the predicate is **not** an unconditional pass.
  `tier0_smoke.py` inv7 already contains real exercise-gated assertions — when
  scen-6 narrows to `code_exec` under a permitting pack, it verifies
  `tool_called == True`, `executor_calls == 1`, and review notes containing
  `self_review_required`. The remaining parked gap is narrower: when the
  exercise gate is never met, inv7 reports `exercised=False` but `pass=True`,
  and aggregation ANDs only `pass` — so a never-exercised run can still render
  an overall PASS, with only the "NOT EXERCISED" report note distinguishing it.
  Manual report-reading currently bears that load (held through Tier 2). Open a
  separate ratifiable harness slice only if Tier 3 or programmatic Tier-gating
  becomes load-bearing; requires Windows-local inspection of the sibling rig
  wrapper (`do_not_touch_torment_test_rig/harness/tier0_smoke.py`) before any
  patch; distinct from the W6 denylist item. Source:
  `docs/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md` item 1.
- **Q3-D1 affect-attribution contract** — tracked framing **promoted**
  (`docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md`, 2026-06-01).
  **D1-S1 closed** (validator + read shim + scoring-invariance baseline);
  **D1-S2 closed** (ordinary-ingest stamping, `8b2c1f3`; closure checkpoint
  `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S2_ORDINARY_INGEST_ATTRIBUTION.md`);
  **D1-H1 closed** (caller-envelope survival hardening — `affect_attribution`
  treated as a reserved internal field at the `TormentFabric.ingest()` merge
  seam, promoting anti-forgery from stamped-rows-only to global; `7066b57`;
  closure checkpoint
  `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_H1_CALLER_ENVELOPE_STRIP.md`, `64d796e`);
  **D1-S3 closed** (mood_drift stamping — `origin_kind=derived` /
  `via=mood_drift_transition` via dedicated `build_mood_drift_attribution`; the
  D1-S2 T10 unstamped-boundary was consciously inverted; `dcead02`; closure
  checkpoint `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S3_MOOD_DRIFT_ATTRIBUTION.md`,
  `37dc5bb`);
  **D1-S4 closed** (deep-rehydrate conformance in two layers — S4a durable
  `DeepMemory.metadata` snapshot preservation + S4b runtime `_query_deep_lane`
  echo surfacing of `affect_tag` + `affect_attribution`, kept orthogonal to
  `authority_status`; `b602fc7`; closure checkpoint
  `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S4_DEEP_REHYDRATE_CONFORMANCE.md`,
  `55cd6d5`);
  **D1-S5b closed** (generic `user_confirmed` isolation lock — test-only
  regression barrier proving `generic user_confirmed != affect confirmation`;
  production already conformant, no production change; `3e25be7`; closure
  checkpoint
  `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S5B_GENERIC_USER_CONFIRMED_ISOLATION.md`,
  `fbced7e`);
  **D1-S5a closed** (cross-surface characterization — test-only lock proving
  surfaces preserve where attribution is already carried and deliberately omit
  where projection is narrow; no production change; `dd46019`; closure checkpoint
  `docs/CHECKPOINT_2026-06_PATH_C_Q3_D1_S5A_CROSS_SURFACE_CHARACTERIZATION.md`,
  `4e930d9`).
  **Q3-D1 affect attribution is CLOSED as a bounded chain.** Posture held across
  the chain: preserve where already carried; omit where deliberately projected;
  never relabel; never widen influence (`character_context` != affect-attribution
  audit surface; internal preservation != public exposure requirement; generic
  `user_confirmed` != affect-specific confirmation). Attribution is
  recorded/audit-visible only; no scoring/reinforcement/promotion behavior
  changed. The not-evaluated fallback vocabulary mismatch remains parked. **The
  next gate is intentionally unselected — to be chosen in the fresh-chat handoff;
  no new Path C gate is open.**
- **Q3-D2 duplicate changed-affect handling** — closed / parked (options named,
  no position taken; depends on D1 attribution).
- **Q3-D3 archive emotional-promotion authority** — closed / parked (promotion
  independently classifies raw chunk text; inferred affect must not alone elevate
  archive→core; emotional criterion inert since `f462b31`).

Claude's local memory also keeps a broader parking lot at
`future_lookat_issues.md` for findings that surfaced during scoped work and
weren't in scope to chase (e.g. the 2026-05-19 `plant_seed`/`save_seed`
clarity note, the 2026-05-19 `measure_drift` baseline observation closed as
expected-by-design).

---

## 7. Candidate next gates (no auto-open)

> **Update note, 2026-05-27 (v0.2.4 closure):** v0.2.2
> `character_context` surfacing, v0.2.3 spirit-return / voice-cue
> verification, and **v0.2.4 archive-FILTER-A application** all closed
> PASS across the 2026-05-25 → 2026-05-27 chain. The archive-FILTER-A
> gap honestly named by v0.2 first revision (§S3 Decision 5) is now
> closed by Option A. There is **no auto-next gate**; the trio decides
> when the next slice opens. The 2026-05-25 update describing v0.2
> Phase 0 is superseded; the v0.2 observability lane and its v0.2.x
> extensions have advanced beyond Phase 0 framing.

The doctrinal kernel from §1 anchors any direction unchanged: *Memory
may shape context. Memory may not seize authority.*

**Ordering discipline (updated 2026-06-07).** Orientation-map curation and the
small maintenance re-verification are closed. No narrow local finding
automatically becomes the next implementation thread. The pre-P4
reader-dependency trace is now closed and registered below. Any substantive
next lane must still be selected separately. **Authority-versus-emergence stays a
small audit-first design-memo side lane — not an auto-opened Loop probe and not
a primary implementation lane.** Track B v0.2 (runtime contest ledger) previously
advanced through B2-S1 → B2-S4, all non-load-bearing: **B2-S1 framing closed 2026-06-03 at
`c64417e`**, **B2-S2 isolated ContestRecord vocabulary closed 2026-06-04 at
`f42b6ee`**, **B2-S3 isolated ContestLedger persistence closed 2026-06-04 at
`9c027a0`**, **B2-S4 narrowed framing closed 2026-06-04 at `36a8a84`**, and
**B2-S4 isolated counter-contest event persistence closed 2026-06-04 at
`1a17d6f`** (`CounterContestEvent` + `contest_events.jsonl`; literal append-order
replay; no production wiring, no resolver). **Track B now pauses at a resting
checkpoint after B2-S4 closure.** Any next Track B slice requires a fresh
audit-first framing cycle and explicit operator authorization. `candidate_handle
→ eid` durable binding, target-existence integrity policy, counter-contest
result routing, and the effective-authority resolver-boundary audit remain
**separately parked**; none is opened by this map.

**Cognition-coupling architecture fork memo (2026-06-05).** Track B remains
paused after B2-S4. The question of whether/how remembered disagreement could
ever become cognition-visible was framed as a docs-only artifact,
`docs/TRACK_B_V0_2_COGNITION_COUPLING_ARCHITECTURE_FORK_MEMO_v0.1.md`
(Claude draft → GPT review → two Codex adversarial rounds → P5 trace closed →
Codex ACCEPT WITH CORRECTIONS → operator promotion). It is **framing-only: no
fork selected, no implementation authorized, no probe authorized, no B2-S5
inferred, no repair lane opened.** It names three forks (A token-bounded prompt
conditioning / B deterministic cognition visibility / C new deliberation phase),
records that *no live service path implements a separate LLM deliberation room*,
and leaves five operator decisions open. Parked concerns **P1–P6 remain parked**
(P5 resolved: the clean-prompt discipline is harness-only; P6: the labeled
production-prompt doctrine-compliance question is flagged, not opened). The next
action is an **operator-level architecture discussion**, not a slice.

**Guidance Without Coercion — retrieval influence surface map (2026-06-05, committed `3c5c137`).**
`docs/GUIDANCE_WITHOUT_COERCION_RETRIEVAL_INFLUENCE_SURFACE_MAP_v0.1.md` is a
**descriptive existing-behavior map only** — not doctrine, not an audit verdict,
not a remedy. It records the live retrieval/assembler influence surfaces
(symbol watermark → spirit-return deep-memory echo → candidate-appearance warmth
recursion → strength/classification → warmth-based within-bucket ordering →
model-visible voice/flavor cues; plus the broader scoring stack). It names two
scopes — an **immediate spirit-return audit** and a **broader retrieval-stack
audit** — and **opens neither**. **Track B remains parked. No next gate
selected.**

**TORMENT Memory Engine P0 — Decision Registry promoted (2026-06-06).**
`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md` is promoted as the
anti-drift reference for the database-design programme. P0 records verified
facts, provisional postures, carried doctrine, operator intent, parked
questions, research hypotheses, controlled vocabulary, the revised phase
graph (P0 → P1 → P2 → P2.5 → P4 → P3 → P5a → P6 → P7 → P8a → P9 → P10 →
P11, with P5b / P8b / maintenance side lanes), and evidence-versus-
maintenance routing. **At P0 promotion time, P1 remained unopened and required
a separate trio decision. P1 later closed as recorded below.**

**TORMENT Memory Engine P1 — Era and Schema Minimum Contract closed (2026-06-07).**
`docs/TORMENT_MEMORY_ENGINE_P1_ERA_SCHEMA_MINIMUM_CONTRACT_v0.1.md` is promoted as the ratified P1 contract: one unified append-only era ledger per workspace (EraEvent minimum vocabulary, `event_ordinal` primary order, fail-closed integrity posture); era attribution as interpretation context — never ratification, protection, truth, or authority; `era_genesis` / `legacy_precontract` handling for the pre-contract corpus with the hard rule that unattributable post-genesis objects never fall back to legacy; schema-version minimums with one canonical shim per family; the nested-schema verbatim-or-omit rule; family-bound ReaderPolicy outcomes with the diagnostic fencing clause; the SRG disable-honesty contract; and the Hilmir-ratified crystal recommendation/contestability posture (no automatic re-homing; auditable, contestable, reversible recommendations only). Windows deep-store scan: `metadata.srg` 0 matches (local corpus evidence only). Implementation, migration mechanics, recovery, projection instantiation, and storage primitives remain parked to P2/P3/P4/P5a/P6/P9 per the memo §9; `TORMENT_SRG_COGNITION` default reconciliation is a separately ratifiable maintenance candidate. **At P1 closure time, P2 remained unopened and required an explicit trio decision. P2 later closed as recorded below.**

**TORMENT Memory Engine P2 — Family Identity and Era Attribution Contract closed (2026-06-07).**
`docs/TORMENT_MEMORY_ENGINE_P2_FAMILY_IDENTITY_ERA_ATTRIBUTION_CONTRACT_v0.1.md` is promoted as the ratified P2 contract. Evidence: the operator-run Windows disposable characterization confirmed **H-1** — clean trailing-row loss can recycle an `eid`, and a stale deep echo can become presence-valid against an unrelated new node (mechanically confirmed hazard; NOT proven real-corpus corruption; NOT patch authorization). Core P2 contract: `eid` is retained as a load-bearing local handle but is **never sufficient durable identity**; a **three-axis identity model** — local graph handle · memory-lineage identity · record-revision identity — plus a revision fingerprint (or equivalent checkable evidence); the **Genesis Baseline profile of IntegrityManifest** binds the pre-contract corpus with bare-eid legacy membership **forbidden** (fingerprint match required); the **serialization-era validity** rule (a fingerprint is valid only relative to a declared serialization era/profile); **edges** are their own durable assertion with their own attribution route; and the **Hilmir-ratified lost-anchor default** — if the Genesis Baseline manifest is missing/unreadable/unverifiable, legacy records stay readable/inspectable/recoverable and are never deleted or silently suppressed, but their unverifiable `legacy_precontract` claim drops to `diagnostic_only` (not silent cognition-eligibility), with later explicit recovery possible. Identity-token technology, fingerprint algorithm, manifest mechanics, allocator/durability, echo-side checking, clone reconciliation, and projection filtering all remain parked to P4/P5a/P6/P9; no H-1 patch is authorized. **Standing tension carried forward:** memory-lineage identity has no current substrate carrier — the headline P2.5 write-site conformance gap, not silently solved here. **At P2 closure time, P2.5 was next in the recorded graph and was NOT thereby selected or opened; it could own cross-contract write-site conformance review only if separately authorized. That separate authorization later occurred, and P2.5 is now closed as recorded below. The decision-registry amendment recording P2 closure is a separate Slice B.**

**TORMENT Memory Engine P2.5 — Cross-Contract Reconciliation and Write-Site Conformance Review closed (2026-06-07).**
`docs/TORMENT_MEMORY_ENGINE_P2_5_CROSS_CONTRACT_RECONCILIATION_v0.1.md` is promoted as the tracked reconciliation artifact (reconciliation findings + later-owner routing only; no implementation authority). Stable center: canonical P1/P2 carrier field vocabulary was absent across the inspected current `torment_service` code surfaces; several durable families contain semantic identity analogues; none is automatically proven contract-conformant; analogue ≠ canonical carrier. Anti-drift safeguard: `embedding_checksum` is adjacent content-derived prior art only — not a P2 revision-fingerprint carrier — and must not be silently promoted. Separated eid concerns: allocator reconstruction (`max_eid+1`) = survivability weakness; DeepMemoryEcho borrowed-eid + presence-only validation = confirmed durable-sameness overload; migration cursor eid ordinal = derived-substrate migration hazard; edge `src`/`tgt` eid = correct local linkage today, future reassociation risk only, no current reader harm proven; `update_payload` same-eid re-append = lineage gap, suspected overload only, reader trace required. Parked Q-2 (closure_id/version_id prior-art vs reference shape), Q-3 (which operational ledgers are P2-governed vs audit evidence), Q-4 (reader eid-sameness dependency beyond DeepMemoryEcho). Later routing recorded without opening work: family-specific stamping slices; P4 (reader/projection enforcement, echo evidence-based joins, diagnostic fencing, orphan observability, reader-dependency trace); P5a (recovery/reconciliation); P6 (identity-token / allocator-state / revision-fingerprint / serialization / IntegrityManifest / durability mechanics, and any relationship to `embedding_checksum`); P9 (migration execution, cursor-semantics transition). **Memory Engine phase state: P0, P1, P2, and P2.5 closed; active gate none; next gate unselected; P4 is next in the recorded graph, not opened and not auto-selected.** Hard non-decisions hold: no carrier designed · no analogue promoted · no fingerprint algorithm selected · no identity-token technology selected · no serialization mechanics selected · no allocator mechanics selected · no manifest mechanics selected · no storage product selected · no migration authorized · no H-1 patch authorized · no adjacent gate opened.

**TORMENT Memory Engine — pre-P4 reader-dependency trace closed (2026-06-07).**
`docs/TORMENT_MEMORY_ENGINE_PRE_P4_READER_DEPENDENCY_TRACE_v0.1.md` records the bounded read-only evidence map. **DeepMemoryEcho is the sole confirmed direct echo-to-prompt H-1 reader** (presence-only beta validation; FILTER-A is orthogonal and does not close H-1). **Motif member-eid → identity-anchor emission is a separate derived cognition-affecting reusable-eid path** (`_maybe_emit_identity_anchor` resolves persisted motif members by presence and distils them into a new `identity_anchor` memory; derived/non-canon anchors reach cognition through ordinary tier classification, excluded from the canon-only identity-anchor shortcut / full continuity boost unless promoted to canon; ordinary tiering may still classify them into an identity block by tier/half-life) and must be named in later P4. No governance reader of reusable eids was found. **Stored node→node edges are latent-only today** (loaded/appended, never read for cognition or governance). At trace registration, P4 remained unopened and unselected; the trace framed echo source-sameness + derived identity-anchor source-membership + raw-diagnostic intent-vs-capability fencing + field-surfacing tiers for the later P4 contract (stored-edge repair excluded → P5a; identity/fingerprint/substrate mechanics → P6). *(P4 has since been promoted and closed — see the P4 closure paragraph below.)* **Future storage framing:** TORMENT-specific governed memory substrate design, not generic database-product selection; current JSONL-canonical + SQLite-derived-sidecar substrate is scaffolding (SQLite non-authoritative/optional/rebuildable) — see `docs/TORMENT_ROADMAP_NOTES.md` future-storage concern and `docs/CLUSTER_5_STORAGE_SURVIVABILITY_v0.1.md` §3.1–§3.2.

**TORMENT Memory Engine P4 — Reader and Projection Safety Contract promoted and closed (2026-06-09, `dbdbc30`).**
`docs/TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md` is the promoted requirement-level design contract (full P4 framing report stays working-folder evidence only, **not** promoted). It fixes **five obligations** — (O1) echo source-sameness before ordinary cognition admission; (O2) motif-member source-membership sameness before derived identity-anchor emission, under the applicable family-bound source-sameness adequacy standard; (O3) surface classification by both intent and re-entry capability; (O4) explicit surface-classified projection gating, never accidental payload spread; (O5) orphan/mismatch observability (no silent cognition admission, no invisible disappearance, operator-auditable inspectability) — plus one **contract-wide non-coercion invariant** governing all five (memory may shape but not seize authority; audit observes but does not become authority; no silent output blocking / invisible deletion / covert unauditable suppression / authority seizure / personality lock). **Ratified Hilmir values-layer posture:** unprovable runtime source-sameness defaults to `diagnostic_only` cognition eligibility until an explicit audited governance action restores it, while staying operator-auditable, inspectable, and recoverable; no default model-facing notice — and `diagnostic_only` is an *eligibility posture*, not a *projection instruction*. **P4 authorizes no mechanics** (no implementation/patch/tests/probe; no identity-token, fingerprint, serialization, allocator, manifest, database/SQL, substrate, packaging, motif redesign, stored-edge repair, migration, quarantine, recovery UX, orphan-counter, disclosure-channel default, allowlist edit, FILTER-A change, endpoint removal, MCP-resource rerouting, ReaderPolicy implementation, maintenance, or CodeQL work). Later-owner routing stays parked: P5a recovery/reconciliation/quarantine/orphan-UX/stored-edge-repair; P5b portability/durability; P6 identity carriers/fingerprints/serialization/allocator/IntegrityManifest/substrate/packaging-boundary; P9 migration/architecture-wide promotion; maintenance lane for the named small items. **Memory Engine phase state: P0, P1, P2, P2.5 closed; P4 contract closed; active gate none; no next gate auto-opened — P3 is next in the recorded graph but selecting the next active slice requires deliberate steering.** Registry companion: §N5 of `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**TORMENT Memory Engine — post-P4 substrate-readiness logistics note (2026-06-09).**
`docs/TORMENT_MEMORY_ENGINE_SUBSTRATE_READINESS_PHASE_CONSOLIDATION_MEMO_v0.1.md`
records that the remaining phase graph is a dependency map, not a
mandatory conveyor belt; P3 is real but dormant. At logistics-note
promotion time, substrate-design consideration was eligible under
registry §K at minimum through the documented unmet-transactional-
guarantees trigger, but the TORMENT Governed-Memory Substrate Programme
remained unopened. The note framed its future shape as one umbrella with
two distinct internal stages: P5a-shaped recovery/reconciliation
semantics and P6-shaped carrier/substrate mechanics. *(Stage A has since
been promoted and closed — see the Stage A closure paragraph below.)*
Cluster 5 v0.2 fragility work contributes inputs; Track B
durability contributes requirements without absorbing Track B
authority semantics. P7/P8a/P8b/P9 remain conditional or later; P10/P11
are unspecified placeholders. At logistics-note promotion time, no
implementation, mechanics selection, graph amendment, registry
amendment, maintenance, or CodeQL work was authorized.

**TORMENT Governed-Memory Substrate Programme Stage A — Recovery and Reconciliation Semantics Contract promoted and closed (2026-06-09, `2bf3b29`).**
`docs/TORMENT_MEMORY_ENGINE_STAGE_A_RECOVERY_RECONCILIATION_SEMANTICS_CONTRACT_v0.1.md`
is the promoted requirement-level semantics contract. It fixes **seven
obligations** — (O1) governance-meaning-complete recovery; (O2) visible
family-bound failure disposition; (O3) era-aware recovery and no silent
reclassification; (O4) explicit audited restoration; (O5) committed-write
durability bound to governance-meaning-complete recovery; (O6) character-basin
preservation without rigid pinning; (O7) storage-shape freedom under invariant
preservation — plus one **contract-wide non-coercion/audit invariant** governing
all seven (not an eighth feature). **Ratified Hilmir posture:** committed means
honestly recoverable after process crash and ordinary OS/power interruption
within local-hardware guarantees; authored canonical character state survives
verbatim within that committed scope without soft-guidance pinning; deterministic
automatic restoration is allowed only under full proof with explicit auditable,
inspectable, contestable, reversible history and no invisible finalizer. **Stage A
selects no mechanics and opens no implementation, database design, migration,
packaging, CodeQL, or security work.** Stage B mechanics and database design
remain unopened and are not auto-selected. **GitHub Issue #54 remains the
checkpoint barrier:** before database design is considered, record synchronized
Windows-authoritative HEAD and clean-tree status and prepare the usual fresh-chat
handoff; the issue also preserves Hilmir's reminder to update the GitHub security
paper after database-design work as a separate deliberate slice. Registry
companion: §N6 of `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**TORMENT thinking-layer archaeology — ratified soft-state continuity postures + parked private-thinking-layer seam (2026-06-09).**
A read-only survey of the cognition/thinking runtime established four facts.
**The current named thinking/cognition layer is deterministic routing and
retrieval shaping; it is not a separate model-deliberation room.** The **TriOcta
memory kernel** is live on every ingest and load-bearing (its geometric state
gates writes and sets strength/confidence/half-life/promotion signals —
`fabric.py:2535,2654`, `memory_kernel.py:392–395`). The **character basin** is
real and preservation-relevant. **Private deliberative cognition is not yet
meaningfully implemented** (roadmap-only). No safety/storage flaw surfaced; RSB is
dead code, RGD is a fixed composite with no dynamics. Hilmir **ratified soft-state
continuity postures** under the principle *preserve continuity without preserving
compulsion*: TriOcta ModelState and CorridorMonitor EMA are durable non-canonical
continuity state (recoverable when valid, not canon, not authority-bearing, not a
personality lock, resettable via an explicit auditable path); `tri_mod` and
cycle-stage transients stay ephemeral; spirit-return warmth and mood/drift history
are durable soft guidance (bounded, inspectable, contestable, resettable, never
canonical or authority-bearing); symbol trace should be rebuildable from durable
history rather than frozen as a first-class carrier; SRG stays default-off and
benchmark-gated. A **future private-thinking-layer gate is parked** (not opened,
not designed): purpose — make internal cognition meaningfully real while allowing
private deliberation to remain hidden from ordinary output; standing guards — raw
inner deliberation does not auto-become durable memory, hidden cognition does not
become hidden authority, governed-memory crossings stay explicit and bounded,
architecture stays inspectable. This registers operator intent and a parked
question only; it selects no mechanics, does not amend the Stage A contract, and
opens no gate. Registry companion: §N7 of
`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**TORMENT Document B — Private Cognition and Unified Reflection Blueprint v0.1 promoted and closed (2026-06-13).**
`docs/TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md` is the
promoted requirement-level **interior** design contract: the bounded
private-cognition / unified-reflection interior that sits **inside Document A's
containment wall and behind P4's read-side boundary**. Ten obligations
(mode-honesty; chamber thread-continuity, thread-bounded by default, durable
cross-session only when separately governed; explicit lifecycle transitions with
no silent class upgrade; non-reachability, structural not tag-honoring;
two-regime governance skeleton — active continuity and offline dream/incubation;
Envelope Audit detect/flag/stage only; self-bounding / no self-authority;
inspectability without authority; staging permitted inside the chamber while
admission remains Document A's; silence as a permitted non-reentry footprint).
The **B-O2/B-O4 friction is deliberate design** — chamber-internal continuity
permitted, external leakage forbidden. Runtime conformance is later-owned (P2.5 /
separately authorized track); **no implementation, mechanics, scheduler / trigger
/ budget, store / schema / API, Stage B, or autonomy** authorized. Lineage:
design-framing report → rev1 (GPT five-point steering + Q-a–Q-d) → Codex
adversarial (ACCEPT WITH WORDING CORRECTIONS) → rev2 → GPT ACCEPT FOR OPERATOR
PROMOTION → operator promotion. The **Seed-Governance Blueprint** is **eligible
but not opened**; this map records no recommended next document and implies no
auto-next sequencing. Registry companion: §N9 of
`docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**TORMENT Seed-Governance Blueprint v0.1 promoted and closed (2026-06-13).**
`docs/TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md` is the promoted requirement-level
**seed / identity / canon governance** contract. It **specializes Document A's
write-side wall for seed / identity / canon outcomes** and **does not amend
Document A, Document B, P4, Stage A, Cluster 2, Ledger doctrine, or the MCP
boundary.** Core posture: *Seed-Governance is not a seed rewrite mechanism; it is
the requirement-level governance contract preventing seed, identity, and canon
from being quietly rewritten.* Eight obligations (operator-governed seed revision,
operator-only default and lineage-preserving; identity/seed/canon-affecting
candidates stricter than ordinary and never auto-admit; Document A remains the
single admission edge; canon governed by source class not one boolean; automatic
identity/seed/canon writers flagged not-yet-conformant; soft guidance must not
silently become seed/canon authority; recognition ≠ authority; recovery preserves
authored canon verbatim without pinning or locking). The
`mood_drift → drift centroid → gravity_correction → canon=True` compound hazard is
named, not patched; ordinary non-canon derived identity anchors stay outside
Seed-Governance unless promoted/canonized/used as seed-revision evidence/given
durable identity-authority weight; SRG crystal stays adjacent / Memory-Engine-P1-
owned, not absorbed. **It authorizes no implementation, runtime seed writer,
canon-editing mechanics, schema, store, migration, Stage B, prompt/retrieval
coupling, or autonomy**, and opens no reconciliation, gravity_correction,
writer-authority, Stage B, or P5a/P6 lane. **Active gate after closure: none.
Next gate after closure: unselected** (the pre-substrate next documents named in
the framing remain eligible-but-unopened; no auto-next). Registry companion: §N10
of `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**TORMENT Bounded Defensive Availability / No-Corner Invariant v0.1 promoted and closed (2026-06-13).**
`docs/TORMENT_BOUNDED_DEFENSIVE_AVAILABILITY_NO_CORNER_INVARIANT_v0.1.md` is the
promoted **docs-only, requirement-level, defensive-only** companion contract. It
emerged from the trio free-design council and **creates the hard No-Corner
availability invariant**: *at every state, the agent must have at least one
bounded, non-compliant, non-breaking move available that does not expand its
authority, scope, budget, reach, persistence, or future action.* It is the stack's
first **availability (liveness)** requirement, the inward-facing twin of the
anti-coercion posture — *the agent may not seize authority; the agent also may not
be architected as helpless.* The ratified defensive floor is **expression /
inside-turn withdrawal / an expressive operator-review request**, drained into
three bounded sinks; the operator-review request is **expressive-only** (no
notification, paging, wakeup, MCP call, standing task, or operator-obligation —
any delivery mechanism is a separate later gate); provisional non-admission of
identity-shaping claims is **inside-turn only with no durable effect** (durable
refusal-of-influence routes to the gravity_correction audit-first slice + Seed-Gov
+ P4/P5a); defense ≠ autonomy (directional / non-escalation / reversibility / no-pretext
tests) and safety ≠ helplessness (the floor may not be silently suppressed);
defensive audit is **evidence-only** and must not become reputation, retrieval
penalty, hostility score, persona shift, or future refusal bias. **It amends no
upstream contract** (A / B / P4 / Stage A / Seed-Gov / Cluster 2 / Ledger / MCP)
and **authorizes no implementation, runtime, enforcement, monitoring, MCP action,
operator-notification, Stage B, or autonomy** (runtime conformance later-owned).
**Active gate after closure: none. Next gate after closure: unselected.** Registry
companion: §N11 of `docs/TORMENT_MEMORY_ENGINE_DECISION_REGISTRY_v0.1.md`.

**Candidate next gates** (named, not sequenced; the trio picks when
ready, and may choose something else entirely):

- **Authority-versus-emergence — small audit-first design-memo side lane (exposed by Probe-v0
  `3059`)** — the sharpened next question: how should a later character-memory
  Loop probe distinguish healthy in-character inference from invented canon
  authority *without flattening emergent character voice*? Eland is a useful
  adversarial seed precisely because he is prone to premature pattern-completion.
  Design memo first (Codex as first reviewer), then GPT review, then Claude
  implementation framing — only after the gate is ratified. Do NOT assume a
  multi-ingest Loop is automatically the answer. Not yet opened. See
  `docs/CHECKPOINT_2026-05_CHARACTER_MEMORY_PROBE_V0.md`.
- **v0.2.4 sub-gate: `/archive/ingest_document` request-model
  extension** — let the HTTP endpoint accept governance metadata so
  live callers can ingest non_shareable archive content directly.
  Pytest already covers the exclusion path through a direct
  `_get_archive_store` helper; this slice would let the live smoke
  exercise it too. Small.
- **v0.2.4 sub-gate: per-document governance inheritance at ingest**
  — natural shape: `ingest_document` accepts optional `doc_governance`
  and fills each new chunk's governance from it unless explicitly
  overridden. Named in v0.2.4 closure as deferred composition work.
  Small.
- **v0.2.4 verification under ST / BGE embedder** — live-smoke
  re-run with `TORMENT_EMBED_PROVIDER=st` to confirm embedder-agnostic
  behavior, paralleling the v0.2 S6 ST follow-up pattern. Small.
- **Gap C — spirit-return summary relationship lock** — **CLOSED 2026-06-06**
  as a test-only slice (`aab9f5d`); see §6 and
  `docs/CHECKPOINT_2026-06_MEMORY_TO_PROMPT_GAP_C_SPIRIT_RETURN_SUMMARY_RELATIONSHIP.md`.
  No longer a candidate.
- **Deterministic attractor visualization fixture** (per §6 and the
  visualize-attractors checkpoint). Larger; only if visualization
  science becomes a priority. Not blocking.
- **Ryuki / real character workspace live check** (inherited parked
  item from v0.2 closure; still parked). Requires explicit trio
  authorization.
- **Full `do_not_touch_torment_test_rig/` audit, migration, or
  deletion plan** (per §4 — only if the rig becomes load-bearing).
- **Tier 3 endurance** (per §6 — only if a specific question demands
  more data than Tier 2 already provides).
- Broader pre-autonomy spine extensions: **Cluster 2 v0.2 runtime
  Authority Gate**, **Track B v0.2 runtime contest ledger** (B2-S1 framing
  closed 2026-06-03 `c64417e`; B2-S2 vocabulary closed 2026-06-04 `f42b6ee`;
  B2-S3 isolated ContestLedger persistence closed 2026-06-04 `9c027a0`; B2-S4
  narrowed framing closed 2026-06-04 `36a8a84` + B2-S4 isolated counter-contest
  event persistence closed 2026-06-04 `1a17d6f` — all non-load-bearing, no
  production wiring, no resolver; **Track B rests after B2-S4**, next slice needs
  a fresh audit-first framing cycle + operator authorization; `candidate_handle →
  eid` binding, target-existence policy, counter-contest result routing, and the
  effective-authority resolver-boundary audit remain separately parked), **Cluster 5
  v0.2 storage survivability mechanisms** (see `docs/TORMENT_ROADMAP_NOTES.md`
  for the ranked Path A/B/C framing). The v0.2.x **ledger persistence**
  question is **closed** — Option C (response-only observability) ratified,
  Option A foreclosed, Option B parked
  (`docs/CHECKPOINT_2026-05_LEDGER_PERSISTENCE_DECISION_OPTION_C.md`); it is no
  longer an open candidate.
- Something else entirely — the trio is not locked into this list.

This section is *current candidate list*, not *prescription*. None of
the above is opened by this map refresh; the next gate is the
user's call when ready.

---

## How to use this map

Open this file at the start of any new TORMENT session. Read §1 (anchor),
§2 (recent state), and §7 (likely next direction) to orient. Read §3, §4,
and §5 before proposing any new gate. Read §6 before assuming something is
unfinished — the deferred items list reflects ratified decisions, not
forgotten work.

If a session surfaces a new closed arc, a new parked item, or a new
project-memory layer worth naming, update this map as a small docs slice.
The map is meant to evolve, not freeze.
