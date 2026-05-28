# TORMENT — Project Orientation Map

**Purpose:** A short map for any future GPT / Claude / operator session opening
the project, so we stop rediscovering project state by accident.

**Read this first.** This is not doctrine, not a roadmap, and not an audit.
It is the *anti-confusion layer*: where to look, what each layer means, and how
to start a new gate without re-litigating work that already exists.

**Date of last refresh:** 2026-05-27.

---

## 1. Current main project thread

TORMENT is preparing for controlled automation — specifically, **memory-to-prompt
automation** in which retrieved memory may shape the context of a later LLM
call. The constraint that anchors all work in this direction is doctrinal:

> *Memory may shape context. Memory may not seize authority.*

Consistent with the existing MCP capability boundary doctrine
(`docs/MCP_CAPABILITY_BOUNDARY.md`): **Automatic is allowed. Autonomous is not.**

Any future slice that pushes against this boundary needs its own ratification.
Any slice that respects this boundary can proceed under the gate-start survey
rule in §5.

---

## 2. Where main currently stands

As of 2026-05-27, the following arcs are closed on `main`. Each has a formal
checkpoint doc that is the source of truth for what shipped when:

| Arc | Closed | Source of truth |
|---|---|---|
| Phase 1 / Tier 1 runtime envelope (Batch A no-pack, Batch B debugging pack) | 2026-05-17 | `docs/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md` (promoted from scratch 2026-05-28; scratch original preserved as lineage) |
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

Working tree was clean at the close of the 2026-05-27 v0.2.4 session.
Full suite runs cleanly without the historical
`--ignore=tests\test_visualize_attractors.py` flag — the old
convention is retired; current baseline is
**3,570 passed / 5 skipped / 22 subtests passed** under
`python -m pytest tests\ -q`. Live S6-style smoke for v0.2.4 archive
FILTER-A (hash embedder, disposable workspace) closed at **32 GREEN
/ 0 YELLOW / 0 RED**. The next gate is the user's call (see §7).

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

---

## 4. `do_not_touch_torment_test_rig/`

This folder is the source of repeated mid-session confusion through 2026-05-24
and deserves an explicit boundary statement.

**What it is:** a historical / local runtime test harness, living inside the
repo with the warning prefix `do_not_touch_`. It produced the Tier 0, Tier 1,
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

**Candidate next gates** (named, not sequenced; the trio picks when
ready, and may choose something else entirely):

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
- Broader pre-autonomy spine extensions (named in
  `CHECKPOINT_2026-05_MEMORY_TO_PROMPT_OBSERVABILITY_v0.2.md`):
  **Cluster 2 v0.2 runtime Authority Gate**, **Track B v0.2 runtime
  contest ledger**, **Cluster 5 v0.2 storage survivability
  mechanisms**, **v0.2.x ledger persistence** (Option A vs B from
  v0.2 §5).
- Something else entirely — the trio is not locked into this list.

This section is *current candidate list*, not *prescription*. None of
the above is opened by this v0.2.4 closure; the next gate is the
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
