# TORMENT Roadmap and Research Notes

## Current project state

TORMENT is now a governed memory-and-identity system for persistent AI characters and agents.

It is not an automation engine or autonomous tool runner.
It is strongest as:
- a memory core
- an identity core
- a provenance-aware governed system
- a safe MCP-compatible memory interface

---

## Completed (April 9, 2026)

- Doc audit: all 62 docs deep-verified against codebase, stale values fixed
- Test audit: 10 test files deep-verified, zero stale values
- Bug fix: Spine HTTPException propagation (409 no longer swallowed as 500)
- Bug fix: propose_share KeyError on missing domain (guard + clear error message)
- Character Forge alignment: all generated payloads, endpoints, env vars verified and fixed
- SRG env var wiring: TORMENT_SRG_BANDS, CLASS_A_RATIO, CRYSTAL now configurable
- Test score: 1739 passed, 5 failed (environment-only), 2 skipped
- CodeQL cleanup phases A through E merged
- fabric.py character_name fix: reads character_name from seed dict, falls back to seed_id
- 5 cognition env vars wired into thinking_controller.py (default ON, opt-out via env)
- torment_feedback simplified: memory_ids + bool flags replaces 4 JSON-string arrays
- provencev1 reviewed: healthy, well-tested, no functional issues (cosmetic doc refs only)
- Character creator updated: character_name in payloads, cognition env vars no longer commented out
- Test score: 1721 passed, 2 skipped (environment-only)

---

## Outstanding small fixes

Status update (April 11, 2026):

1. **docs/archive/AGENT_SPINE_PLAN.md references — CLOSED (resolved upstream by commit `4ebd0a3`).** The note that originally flagged this item was written against an earlier repo state where references pointed at the pre-archive path `docs/AGENT_SPINE_PLAN.md`. Commit `4ebd0a3` ("Normalize AGENT_SPINE_PLAN references to archived path") normalized all 30+ references to `docs/archive/AGENT_SPINE_PLAN.md`, which is the actual current location of the file. A verification sweep on 2026-04-11 (v2.4.3-consolidation branch) confirms every remaining reference in the repo already uses the archived path — there is nothing left to do. This item is kept in the roadmap for historical traceability only.

2. **Provenance constants intent pass — LANDED; step 6 CLOSED 2026-04-11.** The earlier "unused provenance constants, kept for future extensibility" framing is superseded. The canonical artifact is `docs/PROVENANCE_STATUS_REGISTRY_v2.4.x.md`, which classifies every declared provenance constant across both vocabularies (spine layer in §6 + storage layer in §4–5) with producer call sites for every Active row and doctrine anchors for every Deferred/Reserved row. Steps 1–5 of the tactical provenance pass are closed on main (step 5 commit B at `9bb310c`). Corrections to the old framing that matter: `SOURCE_MEMORY` on the storage layer is **not** unused — it is the normalization target for legacy bare-string provenance on three read-side surfaces (`/debug/provenance`, `resource_provenance`, retrieval badge), wired in steps 2 and 4 of this pass; and the spine-layer `VALID_SOURCE_TYPES` set is mostly dead in production (tests-only, except `SOURCE_ROLE_OUTPUT`), which is honest documentation of the cognition pipeline, not a bug. **Step 6 (migration tooling for `SOURCE_MEMORY` + `WRITE_MIGRATION` + `WRITE_SYSTEM_IMPORT`) closed operationally on 2026-04-11** — all six open architectural decisions ratified, commits A and B landed (PRs #35 and #36), writer path activated at `c06d69f`, closure recorded in the v2.4.4 README bump (`d1a774b`). Doctrine held throughout: `TORMENT_ARCHIVIST_WRITEBACK=0` gate stays at 0 — step 6 was groundwork for a future gate-flip, not the flip itself. Auto-memory `project_step6_operational_closure.md` carries the re-entry point; do not reopen without a concrete operational reason.

3. **`tool_result_ingest` returned `result_code: "none"` on success — FIXED 2026-04-11.** Surfaced by the guarded-tier live validation on 2026-04-11. A successful `torment_tool_result_ingest` call (exposure tier `guarded`, fast path, memory actually persisted) returned an envelope with `decision_code: "fast_allowed"` but `result_code: "none"` — because the operation was registered in `torment_service/spine.py::_ALWAYS_FAST` without a matching entry in `_OPERATION_RESULT_CODES`, so the fast-path dispatch at `spine.py:1223` silently fell through to `RESULT_NONE`. Storage, governance, and provenance (`source_type: "tool_result"`, `write_path: "tool_ingest"`, `tool_name` preserved) were all correct — only the envelope label was wrong. Fix landed in two layers in the same pass: (a) minimal fix — added `"tool_result_ingest": RESULT_STORED` to `_OPERATION_RESULT_CODES`; (b) guardrail — added an import-time consistency check that raises `RuntimeError` if any `_ALWAYS_FAST` `OperationSpec.name` is missing from `_OPERATION_RESULT_CODES`, so this class of silent coupling bug cannot recur. Verified live on 2026-04-11 via the same reproducer: envelope now returns `result_code: "stored"` with `eid=4`, full provenance tags, and `half_life: 7.0` (7-day tool-result cap honored). Retrieval path also green.

### Completed since April 14

**Reinforce contract — CLOSED (2026-04-16).** Implemented at `63f9b2d` + `a435426`. Per-memory `reinforcement_count` writer, truthful envelope (`"reinforced"` / `"no_op"`), log-scaled additive retrieval boost (`TORMENT_REINFORCE_BOOST`, default 0.04). Contract-invariant test as landing gate. Design records at `docs/REINFORCE_CONTRACT_FRAMING_v2.4.x.md` (6 decisions) and `docs/REINFORCE_CONTRACT_IMPLEMENTATION_PLAN_v2.4.x.md` (7 decisions).

**§2A Memory Plan → Real Query — CLOSED (2026-04-16).** Validated across six eval runs in three patch states. Two upstream patches landed: anchor hygiene (`a0fd7b4` — `derived_identity` tier, provenance tagging, boost filtering) and controller surface widening (`ea07744` — `RELATIONAL_HINT_WORDS` → RETRIEVAL, `ANALYTICAL_DEPTH_HINT_WORDS` → REFLECTIVE). B4/B2/B3/B5 all pass. Advisory default-on: `TORMENT_THINKING_ADVISORY` default flipped from `0` to `1` (2026-04-16) in `spine.py` and `app.py`. Env var retained for `=0` override. §2A validation framing §10 condition met.

### Doctrine promotions (May 2026)

The 2026-05-09 brainstorm closure named Track A (Truthfulness Envelope) and Cluster 2 (Authority Gate + Visibility Contract) as the best two first-promotion candidates after Phase 1 long-iteration tests closed PASS. Phase 1 Tier 1 closed 2026-05-17. The trio (pzychozen + GPT + Claude) ratified both promotions across the 2026-05-18 / 2026-05-19 working sessions. Session-completion bookkeeping lives at `scratch/CHECKPOINT_2026_05_19_TRACK_A_CLUSTER_2.md`.

**Track A v0.1 — Truthfulness Envelope — RATIFIED 2026-05-19.** Promoted at `4f6cffb`. Advisory doctrine. Names the four-axis truthfulness envelope (Mode / Voice / Certainty / Authority), the voice-audit rule (expanded to include Authority), the materiality list (eight categories), and the three-role ownership rule. Doctrine-only; no code or schema changes authorized by the doc. Doc: `docs/TRACK_A_TRUTHFULNESS_ENVELOPE_v0.1.md`.

**Voice Test v0.1 — `tool_result` materiality under active character — LANDED 2026-05-19.** Test at `30e0f98`. Asserts that `tool_result` ingests under an active character voice preserve materiality per Track A §5.1. First runnable regression for the truth/voice/authority doctrine chain. Test: `tests/test_authority_lane_matrix.py`.

**Cluster 2 v0.1 — Authority Gate — RATIFIED 2026-05-19.** Promoted at `e527562`. Advisory doctrine. Decomposes Track A's Authority axis into three sub-dimensions (Authority class / Lifecycle / Promotion rights); adds two top-level Cluster 2 axes (Scope, Lane) orthogonal to Track A; ratifies the `tool_result` default (`(low-authority, decay-bounded, tool_result)` with existing 7d half-life cap), the character-authority default (released-from-agent-scope for roleplay continuity), and the disagreement primitive (Option i-plus: Cluster 2 owns the doctrinal primitive, Track B may specialize the runtime mechanism later). Doctrine-only with a named runtime seam to a future Cluster 2 v0.2; no runtime enforcement, schema, or API changes authorized. Doc: `docs/CLUSTER_2_AUTHORITY_GATE_v0.1.md`.

### Next candidates

- **Forge per-agent single-terminal mode** — deferred to land with solo → `ryuki_chat.py` alignment, not as a third hivemind fork (see `project_per_agent_mode_deferred.md`). Window/broadcast shipped 2026-04-14.
- **`TORMENT_ARCHIVIST_WRITEBACK` flip** — separate future gate. Step 6 was groundwork, not the flip itself.
- Broad MCP expansion (Continue, Cline, Cursor, etc.) — paused per the Claude Desktop first stance.
- Autonomous tool use, self-writing cognition loops — still blocked per `ROADMAP_v2.4.x.md` §3.

**Post-doctrine-chain candidates (from 2026-05-19 checkpoint):** fuller context in `scratch/CHECKPOINT_2026_05_19_TRACK_A_CLUSTER_2.md` §5.

- **Voice Test v0.2 / Phase 4a** — *recommended next technical task.* Next runnable regression around Track A / Cluster 2 authority semantics: voice must not alter authority; `source_type=tool_result` stable under active character (Track A §9.3); no identity/canon promotion from `tool_result`. Small, regression-oriented, no doctrine redesign needed. Independent: can proceed without changing Cluster 2 doctrine.
- **Track B disagreement runtime mechanism planning** — *recommended next doctrine task.* Design the runtime mechanism for contest / disagreement / no-persist vote. Doctrine-only planning first; no implementation until framing is ratified. Must preserve Track A §9.6 and distinguish agent contest from character-basin contest. Pre-promotion audit first, following the Track A / Cluster 2 pattern.
- **Cluster 5 storage framing audit** — *recommended next audit task.* Reality-check storage / survivability claims before promoting storage doctrine. Audit first; no framing doc until code reality is mapped (current TORMENT has JSONL canonical with SQLite as non-canonical sidecar, not the SQLite-as-control-plane the 2026-05-09 brainstorm assumed).
- **Cluster 2 v0.2 runtime Authority Gate** — *deferred unless trio explicitly chooses.* Future implementation-track planning for actual runtime authority enforcement. Explicitly deferred by Cluster 2 v0.1's doctrine-only posture; should not start unless the trio chooses this over Voice Test v0.2 / Track B / Cluster 5.

---

## Active tracks

### 1. Security hardening / bug hunting
- Security hardening
- Bug analysis
- Tightening weak spots
- Making the system less fragile and more runnable

Tools to consider: [Snyk](https://snyk.io/), [Semgrep](https://semgrep.dev/)

### 2. MCP compatibility across hosts

**Status (2026-04-11): narrowed to Claude Desktop hardening pass.
Full cross-host track paused at framing + research maturity.**

**Why Claude Desktop first.** Claude Desktop is the active MCP host
path because it is already the tested and documented integration and
gives the fastest real validation loop for TORMENT's MCP surface.
This also lowers friction for outside testers on macOS/Linux, letting
system coverage expand without immediately taking on host-specific
complexity. Cross-host work remains preserved but paused; Hermes is
the first serious second-host candidate when the track resumes.

The original cross-host track was scoped around two tested hosts
(Claude Desktop and Hermes Agent from Nous Research). Deep research
confirmed that Hermes requires WSL2 on Windows, which turns a single
reliability pass into a split Windows/WSL2 environment problem.
Disproportionate to present demand, so the active work was narrowed.

**Active (2026-04-11): Claude Desktop hardening pass.** Four small
do-now items, all Claude-Desktop-shaped, no host expansion, no
capability sprawl, doctrine unchanged:

- H1 — `mcp>=1.27.0,<2.0.0` added to `requirements.txt` (fixes a real
  install-time bug where cold setup failed at `from mcp.server.fastmcp
  import FastMCP`).
- H2 — stdout cleanliness audit on MCP-reachable runtime paths. Four
  real stdout leaks found in `fabric.py` hivemind packet emission
  block (`[PACKET-EMIT]`, `[PACKET-CONVERGE]`, `[PACKET-SKIP]`,
  `[PACKET-ERROR]`) redirected to stderr. Kernel research/diagnostic
  prints confirmed unreachable from the MCP boot path, left alone.
- H3 — Windows stdio checklist folded inline into
  `docs/MCP_README.md` Claude Desktop config blocks (unbuffered mode,
  UTF-8 discipline, stderr-only logging, abrupt stdin close
  tolerance) + smoke test config synced.
- H4 — pause-state housekeeping across this roadmap, the cross-host
  framing doc, the research request doc, and auto-memory.

**Paused groundwork.** The full cross-host framing doc
(`docs/MCP_CROSS_HOST_FRAMING_v2.4.x.md`) and research request with
delivered findings (`docs/MCP_CROSS_HOST_RESEARCH_REQUEST.md` plus
`docs/TORMENT MCP Cross‑Host Research Findings.pdf`) are preserved as
valuable groundwork, not deleted or abandoned. They remain load-bearing
starting material if the track is resumed.

**Resume conditions (any one of):**
1. Linux or WSL2 test environment becomes available locally, so
   Hermes stops being a split-matrix problem.
2. A real second-host demand from a TORMENT user running Continue,
   Cline, Claude Code, or another stdio MCP host — with reproduction
   evidence on their own environment.
3. A decision to ship a host-agnostic positioning doc tied to an
   external announcement, at which point the landscape research
   becomes load-bearing.

Hermes is the first serious second-host candidate if the track is
later revisited. Untested-host matrix expansion (Continue, Cline,
Claude Code, Cursor) is explicitly out of scope in the paused state.

Focus, unchanged: compatibility, clarity, reliability, developer
usability. Not: lots of new tools, automation, execution expansion.

---

## Deferred tracks

### 3. Path 2: retrieval tuning
- Continuity bonus / recency wall mitigation
- Diversity in top-k retrieval
- Short-path to long-path re-evaluation
- Motif alignment staleness review

This is later tuning, not immediate work.

### 4. Path 1: live / personal layer
- Live agent voice/transcript hardening
- Response feel
- Natural memory use in real interaction
- Making the character experience feel alive

---

## Late roadmap: deep systems research

Look deeply at the libraries TORMENT runs on, especially:
- CPU-side behavior / libraries
- RAM / memory behavior
- Transformer-related layers and dependencies

Possible directions:
- Study what kind of wild research could support them
- Explore whether TORMENT's own math could guide or improve them
- Revisit past research ideas and see if they can inform runtime behavior
- Consider designing custom components that work better for TORMENT than generic ones

This track is for: deep systems research, experimental performance ideas, custom low-level behavior guided by TORMENT's own principles.

Not for: immediate production changes, random optimization churn, derailing the current roadmap.

---

## Order of operations

1. Finish security hardening + pick off outstanding small fixes
2. MCP compatibility/support polish
3. Path 2 deeper tuning
4. Path 1 personal/live refinement
5. Late research track

---

## One-line summary

hardening → compatibility → tuning → lived experience → research

Not: endless new architecture.
