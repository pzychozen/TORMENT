# TORMENT — Project Orientation Map

**Purpose:** A short map for any future GPT / Claude / operator session opening
the project, so we stop rediscovering project state by accident.

**Read this first.** This is not doctrine, not a roadmap, and not an audit.
It is the *anti-confusion layer*: where to look, what each layer means, and how
to start a new gate without re-litigating work that already exists.

**Date of last refresh:** 2026-06-03.

---

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

The next primary lane is intentionally **unselected** — pending this
orientation-map curation and a small maintenance re-verification (see §7). Any
slice that pushes against the automatic/autonomous boundary needs its own
ratification; any slice that respects it proceeds under the gate-start survey
rule in §5.

---

## 2. Where main currently stands

As of 2026-06-03, the following arcs are closed on `main`. Each row points to
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

**Q3-D1 affect attribution is CLOSED as a bounded chain** (S1 → S2 → H1 → S3 →
S4 → S5b → S5a). The next gate is **intentionally unselected** — it must be
chosen separately in the fresh-chat handoff; no new Path C gate is open.

Working tree was clean at the close of the 2026-05-27 v0.2.4 session.
Full suite runs cleanly without the historical
`--ignore=tests\test_visualize_attractors.py` flag — the old
convention is retired. **Dated 2026-06-04 baseline (post B2-S2, `f42b6ee`): 3,727 passed /
5 skipped / 22 subtests passed in 89.38s** under `python -m pytest tests\ -q`
(authoritative Windows run; supersedes the 2026-05-27 baseline of 3,570
passed — re-establish before/during the next code-bearing slice; do not
treat as a permanent count). The focused B2-S2 suite ran **44 passed in
0.57s**. Live S6-style smoke for v0.2.4
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
- **`/agent/query` doctrine-vs-reality correction** — parked from v0.2.2
  closure. The v0.2.2 surfacing (Option A) wired only `/retrieve`;
  doctrine names both `/retrieve` and `/agent/query`. Small docs-vs-code
  reconciliation slice.
- **Gap C — `spirit_return_summary` consistency check** — named in
  `docs/CHECKPOINT_2026-05_MEMORY_TO_PROMPT_v0_2_3_SPIRIT_RETURN.md`
  §A as the smallest possible follow-up to v0.2.3. Asserts that
  `character_context.spirit_return_summary` and
  `assembly_audit.spirit_return_summary` agree when both fire.
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
- **Probe-v0 relational-count observability mismatch** —
  `character_context.tier_breakdown.relational=1` while `relational_count=0`
  / "no relational memories yet" when the relational hit is surfaced.
  Forensic-only; does not touch the model-visible prompt contract.
- **Probe-v0 `agent_locks=2` at preflight** — observed before workspace
  creation during the `3059` run; verify agent locks release cleanly across
  runs. Small observability check, not blocking.
- **Predicate #7 logic upgrade (Tier-1 harness)** — the Tier-1 predicate is
  `pass: True` unconditional; manual verification has borne the load through
  Tier 2 (shipped 2026-05-24). Open only if Tier 3 or programmatic Tier-gating
  is opened; requires Windows-local inspection of the sibling rig wrapper
  (`do_not_touch_torment_test_rig/harness/tier0_smoke.py`) before any patch;
  distinct from the W6 denylist item; explicitly NOT closed by the 2026-06-01
  maintenance slice. Source: `docs/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md` item 1.
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

**Ordering discipline (2026-05-31).** No narrow local finding automatically
becomes the next implementation thread. Sequence: (1) this orientation-map
curation, then pause; (2) small maintenance re-verification — re-survey before
acting (do not assume the old checklist is still current): remaining model
defaults in bench tools, the `.env.example` URL naming inconsistency
(`TORMENT_SERVER_URL` vs `TORMENT_URL`), and the Predicate #7 hardening item;
(3) re-rank substantive work afterward. **Authority-versus-emergence stays a
small audit-first design-memo side lane — not an auto-opened Loop probe and not
a primary implementation lane.** If maintenance closes cleanly and the trio wants
an implementation lane, Track B v0.2 (runtime contest ledger) is a strong existing
candidate — its **B2-S1 framing closed 2026-06-03 at `c64417e`** and its **B2-S2
isolated ContestRecord vocabulary closed 2026-06-04 at `f42b6ee`** (non-load-bearing;
no production wiring), so the candidate next slice is **B2-S3 (append-only
separate-ledger writer/reader + replay tests)** — but B2-S3 is candidate-only,
parked, and is not opened by this map.

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
- **Gap C — `spirit_return_summary` consistency check** (per §6 and
  the v0.2.3 checkpoint). Smallest possible v0.2.x follow-up.
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
  closed 2026-06-03 `c64417e`; B2-S2 isolated ContestRecord vocabulary closed
  2026-06-04 `f42b6ee`, no production wiring; next slice B2-S3 — append-only
  writer/reader + replay tests — is candidate-only, parked, not auto-open),
  **Cluster 5 v0.2 storage survivability mechanisms** (see `docs/TORMENT_ROADMAP_NOTES.md`
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
