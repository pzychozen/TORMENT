# Agent Automation — Next Step Audit

**Status:** Ratified historical record. Originally drafted 2026-05-16 in `scratch/`; pressure-tested by GPT and ratified as the audit driving Tier 0 / Tier 1 / Tier 2 long-iteration evidence work.
**Promotion:** Copy-promoted from `scratch/AGENT_AUTOMATION_NEXT_STEP_AUDIT_DRAFT.md` to `docs/` on 2026-05-24 after Tier 1 / Q2-D / Level 3 / Tier 2 evidence closures. Scratch original preserved as working-memory artifact.
**Authority:** This document records the historical audit state at draft time. The body below (sections 1–7 plus GPT handoff summary) is preserved verbatim from the 2026-05-16 draft. New material is appended in the "Closures since draft" and "Current next gate after promotion" sections at the end.
**Date (original):** 2026-05-16
**Author:** Claude (cowork), code-grounded against then-current `main`.
**Question asked:** Is "automation for agents" the right next architectural step for TORMENT, or should something else come first?

---

## Headline finding

**The "should we automate?" framing is partly outdated.** A substantial agent automation layer already exists in the repo at v0.1 proof-slice maturity (tagged `v2.4.6-proof-slice-complete`). The honest question is not whether to automate, but **what comes next in the agent runtime's lifecycle, given that the v0.1 proof slice has landed and the May 9 brainstorm explicitly rate-limits everything else behind "Phase 1 long-iteration test results."**

---

## Recommendation: A (refined) — Continue Phase 1 long-iteration testing of the existing v0.1 agent runtime, with narrow telemetry/diagnostic automation built around it

This is GPT's option A and option B combined into the right shape. The Phase 1 long-iteration testing the brainstorm ratified as the prerequisite for ALL roadmap promotion *is itself* a long-iteration test of the existing v0.1 agent runtime. The narrow safe automation that earns its place now is the telemetry/diagnostic layer that makes those iterations produce usable evidence.

What this is NOT: lifting Cluster 4, building new tool families, expanding external action, starting v0.2 multi-agent, or any work that crosses the capability boundary.

---

## Section 1 — Roadmap inventory

### Brainstorming folder (`brainstorming/memory_roadmap_2026_05_09/`)

12 files. The brainstorm session ratified six clusters as **"stable" design status, deferred implementation**:

| Cluster | Status | Anchor file | Automation relevance |
|---|---|---|---|
| 1 — Truth & Voice (Track A) | stable | `02_track_A_truthfulness_envelope.md` | Envelope governs everything any agent loop emits |
| 2 — Authorship + Authority + Visibility (Track B + N + R) | stable | `03_track_B_agent_authored_memory.md` | Authority gate is the failsafe for any candidate from automation |
| 3 — Significance & Affect (Track C + O) | stable | `04_track_C_significance_and_affect.md` | Less directly automation-related |
| 4 — Offline / Reflective (E + F + G) | stable | `05_cluster_4_offline_reflection.md` | Dream / Continued Thought / Envelope Audit — closest existing track to "agent automation" in the autonomous sense; explicitly deferred |
| 5 — Storage & Survivability (D + GPT thread) | stable | `06_cluster_5_storage_and_survivability.md` | Storage substrate; can run in parallel as engineering |
| 6 — Methodology / Research / Defer | classified | `07_cluster_6_methodology_research_defer.md` | Most parked |

**The session's explicit closing posture** (`99_session_summary.md` line 121, ratified by user 2026-05-09):

> The doctrine is the philosophy. The brainstorm is the architecture. **Phase 1 testing is the evidence. The framing docs come later. Implementation comes after that.** Nothing here is doctrine. Nothing here authorizes change.

**Best first promotion order after Phase 1:** (1) Track A envelope, (2) Cluster 2 authority gate + visibility, (3) Cluster 5 storage in parallel, (4) Cluster 4 reflection later, (5) Track C affect last.

### NLA research note (`brainstorming/2026-05-09_nla_activation_reflection_research_note.md`)

Discusses Anthropic NLA work as potential telemetry for Continuation mode. Explicitly bounded:
- "NLA output cannot become canon automatically."
- "Not 'continuous thought' yet. Not 'self-knowledge.' Not 'recursive memory autoencoder.'"
- The note self-corrects past framing ("Claude wanting continuous thought") as "interpretive drift the rest of the architecture was designed to prevent."

Relevance: confirms the doctrine's discipline around what counts as "agent automation" vs "telemetry that informs the agent."

### Repo-level roadmap docs

- **`docs/ROADMAP_v2.4.x.md`** (partially superseded but architecturally canonical): three-tier safe-now / gated-next / **blocked-until-provenance** framing. §3 explicitly blocks: archivist writeback, autonomous tool use, self-writing cognition loops.
- **`docs/TORMENT_ROADMAP_NOTES.md`** (current state, April 2026): "TORMENT is now a governed memory-and-identity system for persistent AI characters and agents. **It is not an automation engine or autonomous tool runner.**" Active tracks: security hardening, MCP compatibility (narrowed to Claude Desktop). Next candidates explicitly include "Autonomous tool use, self-writing cognition loops — **still blocked**."

---

## Section 2 — Current architecture inventory (what already exists for agent automation)

This is where the framing flips. The user/GPT prompt asked whether automation is the next step; the code says **a substantial automation layer already shipped at v0.1 proof slice.**

### Agent Doctrine v0.1 (ratified 2026-04-17, `v2.4.5`)

`docs/TORMENT_AGENT_DOCTRINE_v0.1.md` defines the agent loop architecture:
- 8-phase outer loop: `observe → deliberate → policy gate → execute → assimilate → stabilize` (plus framing and stabilization)
- Inner deliberation loop already existed in `thinking_controller.py`
- Doctrine Part 9: nine load-bearing invariants the runtime must preserve

Load-bearing principles, repeated verbatim because they directly answer "should we automate":

> The outer loop may execute internal reflexes, policy gating, assimilation outcomes, and stabilization steps without any LLM call.

> Coherence, drift, and gravity are considered agent-steering signals only if they can alter or veto outward action.

> TORMENT is not "better autonomous agents." It is state-governed cognition where the LLM is only one participant in a larger loop.

### Agent Runtime v0.1 proof slice (complete, tagged `v2.4.6-proof-slice-complete`)

Per `torment_service/agent_loop.py` docstring header, all slice milestones have landed:

- **M1**: Phase 7 assimilation-outcome dispatcher scaffold — landed.
- **M2**: Mode-legality enforcement + fallback chain (`action_policy.py`) — landed.
- **S1**: `AgentRunner.run_turn` orchestrator wiring Phases 1–8 — landed.
- **S2**: Drift-regime veto on Phase 5 — landed.
- **S3**: Tool-policy gate + single-signature narrowing — landed.
- **S4**: Behavior pack (five-object bundle) — landed.
- **S5**: Drift-triggered stabilization reflex via `enter_reflex`, proven with zero LLM calls — landed.

### Direct answers to GPT's seven sub-questions on current capability

| GPT's question | Answer in current code |
|---|---|
| a) Internal deliberation loop | **Yes.** `thinking_controller.think()` (component-level), `agent_loop.AgentRunner.run_turn` (full 8-phase) |
| b) Autonomous action policy | **Yes (narrow).** `action_policy.py` Mode→legal-intents table with Part 2.5 fallback chain; `stance_policy.determine_stance` |
| c) External tool execution | **Yes (one family).** `tool_executors/subprocess_python.py` — bounded subprocess Python for `code_exec` only. Explicit doc: "Not a hostile-code containment boundary" |
| d) Assimilation / writeback gate | **Yes (partially).** Phase 7 dispatcher in `agent_loop` for assimilation outcomes. Archivist writeback still gated at `TORMENT_ARCHIVIST_WRITEBACK=0` per doctrine |
| e) Rollback / audit trail | **Yes.** Incident log (`incident_log.py`), provenance v1, `memory_events.jsonl`. No automated rollback yet — manual via Spine envelope responses |
| f) Scheduler / daemon loop | **No.** No background loop, no scheduler, no daemon. Spirit reflection writer exists but only fires on explicit HTTP trigger (we confirmed yesterday) |
| g) Operator approval boundary | **Yes (multiple).** MCP exposure tiers, trust tiers, Mode→legal-intents fallback to `GOVERNANCE_REVIEW` |

### The test rig (separate Phase 1 substrate)

`torment_test_rig/` (sibling to `torment_fabric/`, local-only, never pushed). Status: "Phase 1 — mock context + prompt builder + expanded transcript + telemetry + smoke tests." Phase 0 (OpenRouter wire test) closed. Latest phase1 outputs dated **2026-05-04** (probe_26, probe_27).

This is the actual substrate for the brainstorm's "Phase 1 long-iteration testing." It is wired but the latest runs are nearly two weeks old — and the brainstorm's explicit requirement was "at least 100 / 300 / possibly 1000 iterations." Unclear whether those counts have been reached. **Worth confirming with the user.**

---

## Section 3 — Define "automation" (7 categories)

| # | Category | What it means concretely for TORMENT |
|---|---|---|
| 1 | Test / probe automation | Automated runs of the test rig + agent_runner_demo at scale, capturing telemetry |
| 2 | Diagnostic / monitoring automation | Periodic health reports, drift trajectories, memory-volume tracking, provenance leak detection |
| 3 | Internal agent-loop automation | The outer-loop runner already executes phases 1–8 without per-step human approval *within a turn* |
| 4 | Memory-maintenance automation | Compression cycles, anchor formation, lifecycle decay — already exist in the kernel |
| 5 | Offline reflection / Dream automation | Cluster-4 unified surface; doesn't exist yet; explicitly deferred |
| 6 | External tool / action automation | `code_exec` exists narrowly; new tool families would each need their own narrowing pass |
| 7 | Multi-agent coordination automation | ResonancePackets + 7-gate reingest exist (hivemind); full N-agent runtime is v0.2 territory |

---

## Section 4 — Safety/order analysis per category

| # | Category | Doctrine allows? | Blocking prereqs | Failure mode | Evidence needed to proceed | Memory mutation? | Crosses MCP boundary? |
|---|---|---|---|---|---|---|---|
| 1 | Test / probe auto | **Yes** | None | Fake-load coverage | Already happening at small scale; just needs scale-up | No (transcripts only) | No |
| 2 | Diagnostic auto | **Yes** | None | Producing reports no one reads (consumption-surface failure) | None — pure observability | No | No |
| 3 | Internal loop auto | **Yes** (already built) | n/a (shipped) | Drift-veto fails under iteration → unchecked LLM action | Phase 1 long-iteration data | Yes (via assimilation, but gated) | No |
| 4 | Memory-maintenance auto | **Yes** (already built) | n/a (shipped) | Compression eats canon | Existing tests cover this | Yes (decay, compression) | No |
| 5 | Offline / Dream auto | Conditionally yes per Cluster 4 | Cluster 4 implementation; trigger scheduler; cluster-4 hard rule "may not canonize itself" | Self-reinforcing loops, canon laundering | Cluster 4 framing doc promoted post-Phase-1 | Candidates only, gated through authority | No (internal) |
| 6 | External tool / action auto | **Blocked beyond `code_exec`** per `ROADMAP_v2.4.x.md` §3 | Provenance maturity, action-policy per family, hostile-code containment for risky families | Capability layer outpaces governance | Per-family narrowing pass + audit + rollback | No (returns are tool_result via tool_result_ingest if persisted) | At boundary if a future MCP tool dispatches |
| 7 | Multi-agent coordination | Two-agent ready per R1, N-agent is v0.2 | v0.2 runtime design (does not exist) | Cross-agent recursion, parallel-branch hallucination | Multi-agent framing doc + test rig coverage | Yes (cross-graph) | No |

---

## Section 5 — Compare candidates A–H

| Letter | Candidate | Verdict |
|---|---|---|
| **A** | Continue Phase 1 long-iteration tests first | **STRONG MATCH.** This is the rate-limiter the brainstorm ratified. Latest test rig outputs are May 4 — work has slowed. Resuming + scaling is the highest-leverage move. |
| **B** | Build narrow test/diagnostic automation | **STRONG MATCH.** Complementary to A. Telemetry around the iteration runs is what makes the evidence useful. |
| **C** | Build internal agent runtime skeleton | **ALREADY DONE.** v0.1 proof slice complete. Going further (v0.2 multi-agent, more tool families) is premature without iteration data. |
| **D** | Lift Cluster 4 offline reflection | **NO.** Explicitly deferred per brainstorm. Glyph reservoir audit already established this dependency yesterday. Lifting it now overrides the original ordering with no new evidence. |
| **E** | Add external tool/action automation | **NO.** Doctrinally blocked per `ROADMAP_v2.4.x.md` §3. New tool families would each need their own narrowing pass; no proven need for more than `code_exec` yet. |
| **F** | Improve docs/onboarding/demo surface | **MEDIUM.** Valuable in parallel; won't move the architecture forward but lowers friction for outside testers. Could include cleanup of the v2.4.4/v2.4.5/v2.4.6 release-note state. |
| **G** | Stabilize memory ontology / manifests / governance columns | **MEDIUM-HIGH.** Cluster 5 storage work; brainstorm flagged it as "first engineering sketch candidate post-tests, in parallel." Not blocked, but should wait until current Phase B (atomicity) fix is committed cleanly. |
| **H** | Build agent box / Linux runtime environment | **NO (not yet).** Subprocess executor is Windows-first by design; Linux hardening is "out of scope for v0.1.0b" per `tool_executors/subprocess_python.py`. Premature without iteration data validating the v0.1 slice. |

---

## Section 6 — Recommendation

**A (refined): Continue Phase 1 long-iteration testing of the existing v0.1 agent runtime, with narrow telemetry/diagnostic automation built around it.**

This is GPT's instinct ("automation that watches TORMENT, not automation that acts for TORMENT") combined with the brainstorm's stated rate limiter. It maps cleanly to:

1. **Resume test-rig iteration work.** Latest phase1 outputs are 2026-05-04. Brainstorm requirement was "at least 100 / 300 / possibly 1000 iterations." Whether those counts have been reached is the load-bearing first question to answer.

2. **Run agent_runner_demo scenarios at scale.** The demo file lists six scenarios covering ANSWER, GOVERNANCE_REVIEW, drift veto + zero-LLM reflex, retrieval probe, analytical probe, execution probe. Running these in batch with telemetry capture gives empirical data on whether the nine doctrine invariants hold under iteration.

3. **Build narrow telemetry automation.** A reporting layer that aggregates: decision-code distribution, drift-veto fire counts, reflex-fire counts, tool-narrowing outcomes, mode-fallback rates, governance-review trigger frequency. This is GPT's "agent watcher, not agent actor" framing — pure observability.

4. **NOT new architecture.** No Cluster 4 lift, no new tool families, no multi-agent runtime, no scheduler/daemon, no external action expansion.

If Phase 1 iteration data has already been captured at the brainstorm's required volume, the recommendation shifts to **G** (Cluster 5 storage sketch, the brainstorm's stated first engineering candidate). But that needs the volume question answered first.

---

## Section 7 — Exit conditions

If the recommendation is followed:

**Scope (what's in):**
- Test-rig iteration runs at 100/300/1000 scales against the v0.1 agent runtime.
- Agent_runner_demo batch runs with telemetry capture per scenario.
- A small reporting/aggregation script (could live in `tools/` or `torment_test_rig/`).
- Pure-read MCP admin resource for "spine_status_summary" if useful.

**Forbidden scope (what's out):**
- Any new tool family.
- Any change to `agent_loop.py`, `action_policy.py`, `thinking_controller.py`, `tool_executors/` beyond test-driven minor fixes.
- Any lift of Cluster 4 / Dream mode / continuous thought.
- Any multi-agent runtime work.
- Any flipping of `TORMENT_ARCHIVIST_WRITEBACK`.
- Any background scheduler / daemon process.

**First small implementation target:**
- A telemetry-collection wrapper around `agent_runner_demo.py` that captures `ThinkingResult.debug` + `ActionPolicyDecision` + `TurnResult` across N iterations into JSONL, plus a small summary report. Maybe 100–200 lines.

**Tests required before merge:**
- The wrapper script must not alter agent behavior (telemetry-only).
- Existing test suite (1998 tests) must remain green.
- A new test verifying telemetry capture doesn't mutate any TORMENT state.

**Rollback plan:**
- Pure additive — telemetry script lives in `tools/` or `torment_test_rig/`, no changes to core. Rollback is `rm`.

**What must remain operator-approved:**
- Decision to scale iteration counts beyond what existing test rig handles.
- Decision to extend telemetry to any state-mutating endpoint.
- Decision (later) to promote a framing doc based on iteration findings.

---

## GPT handoff summary

**Top finding:** The "should we automate?" framing is partly outdated. Substantial agent automation (8-phase outer loop, Mode→legal-intents action policy, drift-veto, tool narrowing, behavior packs, zero-LLM reflex) shipped as the v0.1 proof slice (`v2.4.6-proof-slice-complete`). The doctrine (`TORMENT_AGENT_DOCTRINE_v0.1.md` ratified 2026-04-17) explicitly defines what counts as agent automation in TORMENT terms and what is forbidden. The next architectural step is gated by the same prerequisite the 2026-05-09 brainstorm ratified: Phase 1 long-iteration testing.

**Recommended next step:** Option A refined — resume Phase 1 long-iteration testing of the v0.1 agent runtime, with narrow telemetry/diagnostic automation built around it. Matches GPT's stated instinct ("watch TORMENT, don't act for it").

**Blocked / deferred items (all confirmed against doctrine):**
- Cluster 4 offline reflection — deferred per brainstorm; lifting it would override the original ordering with no new evidence.
- Glyph reservoir — parked behind Cluster 4 (audit closed yesterday).
- New external tool families beyond `code_exec` — each needs its own narrowing pass; no proven need yet.
- Multi-agent / v0.2 runtime — premature without iteration data.
- Archivist writeback (`TORMENT_ARCHIVIST_WRITEBACK=1`) — separate future gate, not bundled with any current work.
- Background scheduler / daemon — not built; would conflict with the brainstorm's external-bound rule for any offline work.

**Files inspected:**
- `brainstorming/memory_roadmap_2026_05_09/` (all 9 cluster/index/summary files; full grep over folder)
- `brainstorming/full_brainstorm_chat.md.txt` (1962 lines; grep-targeted reads on automation language)
- `brainstorming/2026-05-09_nla_activation_reflection_research_note.md`
- `docs/TORMENT_AGENT_DOCTRINE_v0.1.md` (Parts 1, 2 capability audit + ratifications)
- `docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md` (objective, invariants, M1/M2 migration tasks)
- `docs/ROADMAP_v2.4.x.md` (safe-now / gated-next / blocked-until-provenance)
- `docs/TORMENT_ROADMAP_NOTES.md` (active tracks, recent closures, next candidates)
- `docs/RELEASE_NOTES_v2.4.4.md` (most recent landed work)
- `torment_service/agent_loop.py` (header + M1-S5 status)
- `torment_service/action_policy.py` (header + scope)
- `torment_service/tool_executors/subprocess_python.py` (scope + containment caveat)
- `torment_service/thinking_controller.py` (existing inner deliberation)
- `examples/agent_runner_demo.py` (scenarios + DEBUGGING_SESSION_PACK)
- `torment_test_rig/README.md` and `outputs/` (Phase 1 substrate; latest run 2026-05-04)
- `start/BASIC_HIVE_AGENT_SPEC.md`, `PER_AGENT_MODE_SPEC.md`, `SOLO_ALIGNMENT_SPEC.md` (file presence only; not deeply read — flag if you want detailed coverage)

**Open questions for GPT to pressure-test:**

1. **Has the brainstorm's "100/300/possibly 1000 iterations" requirement been met?** Latest test rig output dated 2026-05-04 (probe_26 / probe_27). If iteration counts are already at target, recommendation shifts to candidate G (Cluster 5 storage sketch as first engineering candidate post-tests, per brainstorm itself).

2. **Should the recommendation distinguish "test-rig phase 1" (currently active, OpenRouter wire + transcripts) from "brainstorm phase 1" (100/300/1000 iteration evidence pass)?** These may be the same thing or different things. The test rig docs use "Phase 1" for its own internal milestone; the brainstorm uses "Phase 1" for the evidence-gathering pass before architecture promotion. The audit assumed they overlap but did not prove it.

3. **Is the v0.1 proof slice's S1-S5 actually being exercised by the test rig?** The agent_runner_demo exists and lists scenarios; whether the test rig calls it in iteration is the empirical link between "we have a runtime" and "we have evidence the runtime works under load."

4. **Does the user/GPT consider the May 15-16 MCP probe + atomicity-bug work part of "Phase 1 testing" or a separate ad-hoc track?** It produced real evidence (the fabric.ingest atomicity bug) but was driven by glyph-reservoir-adjacent curiosity, not by the brainstorm's evidence-first plan.

5. **Is "agent automation" being discussed because there's a felt gap, or because it's the next intuitive question on a roadmap that's already running?** If there's a specific failure mode or felt limitation driving the curiosity, name it — that would refine the recommendation significantly.

— end of original draft —

---

## Closures since draft

This audit was originally drafted 2026-05-16. Since then, the following evidence closures have landed on `main`:

- **Tier 1 runtime evidence — closed PASS 2026-05-17.** Tier 1A (Batch A, no pack, 100 iter × 6 = 600 turns) and Tier 1B (Batch B, debugging pack, 100 iter × 6 = 600 turns) both PASS with all nine doctrine invariants verified. Drift veto 100/100 in scenario 3 across both batches; reflex without LLM 100/100; invariant #7 (TOOL pre/post) exercised on 100/100 code_exec narrowed rows under the debugging pack; zero environment aborts. Pillar-by-pillar findings recorded in `scratch/AGENT_RUNTIME_PHASE1_TIER1_FINDINGS.md` (separate docs-promotion candidate).
- **Q2-D tool-result lifecycle doctrine — closed PASS 2026-05-24.** Audit trail at `docs/CHECKPOINT_2026-05_Q2D_TOOL_RESULT_DOCTRINE.md`. Tool-result rows do not auto-canonize regardless of `promotion_score`; enforced via `suppress_canon=True` flag passed by `_fast_tool_result_ingest` to `fabric.ingest`. Live evidence: promotion scores 0.86–0.88 land `UNSET / SYSTEM / INGEST_UNMARKED` instead of `PROTECTED / CANON_SET`.
- **Level 3 ST retrieval-quality smoke — closed PASS 2026-05-24.** Audit trail at `docs/CHECKPOINT_2026-05_LEVEL_3_ST_RETRIEVAL.md`. External tool-result rows written through `/tool/ingest` are semantically retrievable under SentenceTransformers embeddings (`BAAI/bge-small-en-v1.5`, dim=384, cpu) when the service runs in a fresh ST workspace (`default_st / external_inference_smoke_st`). The 3×3 cosine retrieval matrix is diagonal-dominant; provenance preserved through query response. Bonus finding: Q2-D suppression doctrine is embedder-agnostic (high-promotion ST tool-result rows still land `UNSET / INGEST_UNMARKED`).
- **Tier 2 runtime evidence — closed PASS 2026-05-24.** Audit trail at `docs/CHECKPOINT_2026-05_TIER_2_RUNTIME_EVIDENCE.md`. 5,400 turns across three pack regimes (no-pack, debugging-pack, research-pack EMPTY_CONTRACT), zero environment aborts, all measured invariants linearly stable at 3× iteration scale. Telemetry recovery: the `examples/agent_runner_demo.py` `--provider` and `--jsonl-out` flags were cherry-picked from branch `tier0-agent-runtime-telemetry` commit `ee0f93f` onto main as `032aaf8` so Tier 2 ran against current main rather than the stale branch state.

**The "Phase 1 evidence" status this audit and the long-iteration plan asked for is satisfied.** The next gate moves beyond Phase 1 long-iteration testing into pre-automation hardening.

**Resolution of the draft's five open questions:**

1. **"Has the brainstorm's 100/300/possibly 1000 iterations requirement been met?"** — Yes for 100 (Tier 1A + Tier 1B = 1,200 turns, 2026-05-17) and yes for 300 (Tier 2a + Tier 2b + pack-compose research = 5,400 turns, 2026-05-24). 1000 (Tier 3, 6,000 turns) remains deferred — the long-iteration plan §2 was explicit that Tier 3 runs only on a specific question Tier 2 cannot answer, and Tier 2 surfaced no such question.
2. **"Test-rig phase 1 vs brainstorm phase 1 reconciliation"** — resolved as the same thing per the joint formula in the long-iteration plan §6a (Tier 1+ counts AND pillar-structured report = Phase 1 evidence). Tier 1 + Tier 2 reports both satisfy this.
3. **"Is the v0.1 proof slice's S1-S5 actually being exercised by the test rig?"** — Yes. The parameterized wrapper at `do_not_touch_torment_test_rig/harness/tier0_smoke.py` subprocess-drives `examples/agent_runner_demo.py` through all six scenarios per iteration, exercising S1 (Phase orchestration), S2 (drift veto), S3 (tool narrowing), S4 (behavior packs), S5 (reflex) under iteration. Tier 1 + Tier 2 evidence confirms.
4. **"May 15-16 MCP probe + atomicity-bug work — part of Phase 1 or separate?"** — recorded in memory as `project_fabric_ingest_atomicity_bug` (2026-05-15 finding, fixed in fabric.py preflight Phase B 2026-05-15). Treated as a separate ad-hoc track that produced a real fix; not part of the Phase 1 evidence ladder. The Phase 1 evidence ladder is now closed by Tier 1 + Tier 2.
5. **"Felt gap vs next intuitive question?"** — explicitly named 2026-05-24 as no felt gap heard. The next gate (C, tool-result lifecycle §3 hardening) is doctrinal preparation for automation rather than response to a specific failure mode. The audit's caution about "do not build upward because we are excited" remains the operative discipline.

## Current next gate after promotion

Per GPT + pzychozen ratification 2026-05-24:

**Next technical gate is C — `docs/TOOL_RESULT_LIFECYCLE_POLICY.md` §3 hardening.**

Begin with **§3.2 Change A only: tool-result half-life cap.** Approximate scope: ~10 lines in `fabric.py` ingest path adding an env-overridable clamp (`TORMENT_TOOL_RESULT_MAX_HALF_LIFE_DAYS`, default 7), plus the `TestToolResultHalfLifeCap` test class from §4 Patch 4.

**Compression tier (§3.2 Change B) and reinforcement guard (§3.2 Change C) are deferred as separate sub-slices after C1 lands.** Each becomes its own ratifiable arc.

**Subsequent gates, in order:**
- B: Batch C accumulating workspace evidence — the wrapper currently creates fresh-per-iteration workspaces; supporting accumulation is a separate ratifiable wrapper-code slice. The plan §3 Batch C placement remains valid as the design target for that slice.
- D: Memory-to-prompt automation Phase 0 — design-only boundary doc covering what may automation observe, propose, never mutate, what requires explicit user approval, what must be logged, what must be reversible, what is forbidden. Starts after C and B settle the foundation.

**Tier 3 endurance (1000 iter × 6 = 6000 turns) remains deferred** unless a specific question demands more data than Tier 2 (5,400 turns) already provides.

**The doctrinal kernel anchoring all future automation work** (ratified 2026-05-24): *"Memory may shape context. Memory may not seize authority."* — consistent with the existing MCP capability boundary doctrine ("Automatic is allowed. Autonomous is not.").

---

## Promotion notes

- The audit's original "test rig" references (Section 2 "The test rig") describe a `torment_test_rig/` sibling directory. The actual location in the workspace, confirmed during the 2026-05-24 readiness check, is `do_not_touch_torment_test_rig/`. The "do not touch" prefix is a self-warning about venv/Linux-prep complexity, not a hard ban — read and run of the existing ratified wrapper are doctrinally fine; editing or committing the rig requires a separate slice.
- The audit's body has been preserved verbatim from the 2026-05-16 draft. Only the top status header and the closure sections at the end are new in this promoted version.
