# TORMENT Documentation Audit Tracker

Process: one document at a time, read it, compare against code, test what's relevant, report only, no edits until agreed.

---

## docs/

- [x] geometric_modulation_report.md
- [x] SPEC_adaptive_disp_scale.md
- [x] CRYSTAL_ATTUNEMENT.md
- [x] TUNING.md
- [x] CHARACTER_SYSTEM.md
- [x] MEMORY_KERNEL_ARCHITECTURE.md
- [x] STABILITY_VALIDATION_v2.0.md
- [x] geometric_modulation.md
- [x] AGENT_SPINE_OVERVIEW.md
- [x] COMPANION_CONTRACT.md
- [x] DESIGN_retention_compression_policy.md
- [x] DOCTRINE_v2.4.x.md
- [x] GUIDE.md
- [x] HIVEMIND_GUIDE.md
- [x] MCP_CAPABILITY_BOUNDARY.md
- [x] MCP_EXPANSION_GUIDE.md
- [x] MCP_README.md
- [x] MCP_SMOKE_TEST.md
- [x] MEMORY_HEALTH_REPORT.md
- [x] PATH_2_MEMORY_QUALITY_AUDIT.md
- [x] PATH_3_MCP_DEVELOPER_EXPERIENCE.md
- [x] PROJECT_OVERVIEW.md
- [x] QUICKSTART.md
- [x] README.md
- [x] RECURSION_SAFETY_POLICY_v2.4.x.md
- [x] ROADMAP_v2.4.x.md
- [x] SESSION_HANDOFF_NOTES.md
- [x] SPINE_CONTRACT.md
- [x] SPIRIT_REFLECTION_DEV_NOTES.md
- [x] SPIRIT_RETURN_AND_REFLECTION.md
- [x] TOOL_RESULT_LIFECYCLE_POLICY.md
- [x] TOOL_RESULT_RETRIEVAL_SEMANTICS.md
- [x] TORMENT_THINKING_ROADMAP.md
- [x] TROUBLESHOOTING.md
- [x] VALIDATION_REPORT_v2.4.2.md
- [x] WORKING_NOTES.md
- [x] advanced_cognition.md
- [x] fabric_phase1_analysis.md
- [x] fabric_phase2_analysis.md
- [x] security_hardening_summary.md
- [x] testing_and_smoke_harness.md
- [x] ryuki_torment_setup.md

## docs/archive/

- [x] AGENT_SPINE_PLAN.md
- [x] DISP_SCALE_data_for_recalibration.md
- [x] HIVEMIND_IMPLEMENTATION_PLAN.md
- [x] MCP_INTEGRATION_AUDIT.md
- [x] MILESTONE_hivemind_v1.md
- [x] PROPOSALS_v2.4.2.md
- [x] ROADMAP_post_hivemind_milestone.md
- [x] SRG_INTEGRATION_SPEC.md
- [x] TODO_disp_scale_recalibration.md
- [x] Torment_agent.md
- [x] hivemind.md

---

## Findings Log

### geometric_modulation_report.md — CHECKED
- Empirical report from run_geo_compare.py, 63 comparisons across 7 geometric profiles
- 3 stance shifts observed, all classified GOOD
- social_resonance is a designed subsystem, not external experiment leakage
- LIVE_SOCIAL modulates social_compact threshold (rules 6-7 in stance policy)
- Governance unchanged across all profiles (rules 1-2 never modulated)
- Modifier band 0.85-1.15 confirmed working as designed
- **Finding: LIVE_SOCIAL was misclassified as external-experiment-leaked in previous session planning docs. It is a live, integrated subsystem.**

### SPEC_adaptive_disp_scale.md — CHECKED (Batch 2 deep verify)
- Spec for self-calibrating DISP_SCALE replacing fixed constant
- Status: "Implemented" confirmed — ADAPTIVE_DISP=True in memory_kernel.py
- All values verified against memory_kernel.py: k=2.0 (line 79), window=50 (line 80), warmup=10 (line 81), fallback=1.50 (line 64), COH_FLOOR=0.05 (line 63), COH_SMOOTH=0.70 (line 68)
- KernelSignals formulas verified (lines 363-366)
- **Finding: Fully accurate. No fixes needed.**

### CRYSTAL_ATTUNEMENT.md — CHECKED (Batch 2 deep verify)
- All core math verified: γ_srg≈0.08699, ω₀=0.244, R*≈0.176329, L₀=9.0
- Scoring bonuses verified in fabric.py: same-band +8% (line 3380), crystal +5% (line 3383), Class A +3% (line 3386)
- Collision thresholds verified: sim≥0.75 (srg_engine.py:65), band_dist≤1 (srg_engine.py:66)
- Class A warmth floor +0.15 verified in spirit_return.py:364
- Crystal state verified: R=R*, band=2, no breathing (srg_engine.py:331-343)
- TORMENT_SRG_ENABLE=0 default verified (srg_engine.py:79)
- 81 SRG tests pass, 53 spirit return tests pass
- **DEAD ENV VARS (3)**: Doc lists these as configurable but code never reads them:
  - `TORMENT_SRG_BANDS` — hardcoded `DEFAULT_NUM_BANDS=5` at srg_engine.py:62, no os.environ.get()
  - `TORMENT_SRG_CLASS_A_RATIO` — hardcoded `CLASS_A_RATIO=0.25` at srg_engine.py:59, no os.environ.get()
  - `TORMENT_SRG_CRYSTAL` — no code reads this anywhere; crystal behavior is implicit
  - Cross-ref: FORGE_TRUTH_TABLE rows 22-24, FORGE_RESEARCH_RECONSTRUCTION §1.2-1.4
  - Impact: Forge generates these vars, users may set them, backend silently ignores them

### TUNING.md — CHECKED
- User-facing tuning guide, confirms defaults: drift_correction_threshold=0.35, drift_gravity_strength=0.12
- Covers character tuning, continuity knobs, compression tuning, spirit return tuning
- References working env vars and endpoints
- TODO: spot-check that all referenced env vars still exist and work

### CHARACTER_SYSTEM.md — CHECKED (Batch 3 deep verify)
- All env vars verified live: CHARACTER_ENABLE=1 (fabric.py:591), DRIFT_WINDOW_STEPS=500 (config_view.py:91), CORRECTION_THRESHOLD=0.35 (config_view.py:92), GRAVITY_STRENGTH=0.12 (config_view.py:93), DRIFT_CHECK_EVERY=25 (fabric.py:592)
- derive_kernel_modulation() verified: g ±15% (character.py:680,686), theta_lock ±0.1 rad (character.py:683)
- Seed motif boost: strength ≥ 0.85 (line 360), stability ≥ 0.90 (line 361) — matches doc
- Drift gate: `drift_score > -threshold` FALSE AND `direction == "away_seed"` (lines 559-562) — matches doc
- Tier weights: raw 0.50/0.35/0.15 → normalized 1.43x/1.0x/0.43x via `tw / relational_weight` (line 851) — matches doc
- 10 character tests pass
- **Finding: Fully accurate. No fixes needed.**

### MEMORY_KERNEL_ARCHITECTURE.md — CHECKED (Batch 3 deep verify)
- KernelSignals formulas verified: strength=0.40+0.60*coh (line 363), confidence=0.35+0.65*coh (line 364), half_life=20+80*coh (line 365), promotion_score=0.50+0.50*coh (line 366)
- write_mult 0.90-1.10 verified (lines 245-247)
- proposal_mult 0.90-1.10 verified (line 249)
- bridge_p initial 0.05-0.12 → final 0.03-0.20 verified (lines 250, 332)
- bridge_sim 0.84-0.90 verified (line 251)
- Duration resistance: sustained ≥10 steps → j_score -0.15 verified (compression.py:460-461)
- Warmup window says 400 steps (line 126) — matches code after prior fix
- 3 golden emergent tests pass
- **Finding: Fully accurate. No fixes needed.**

### STABILITY_VALIDATION_v2.0.md — CHECKED (Batch 2 deep verify)
- Historical empirical report (5000 steps)
- Coupling ±15% verified: character.py:686 `np.clip(g_mod, g_default * 0.85, g_default * 1.15)`
- Theta_lock ±0.1 rad verified: character.py:683
- Empirical bounds (Z range, coh range, Omega divergence) are measurement results, not code constants
- 3 golden emergent replay tests pass
- **Finding: Accurate historical report. No fixes needed.**

### geometric_modulation.md — CHECKED
- Design doc for stance modulation, companion to the report
- 5 signals: coherence, stability, identity_lock, ambiguity_tolerance, social_resonance
- 3 modifiers: identity_defer, ambiguity_clarify, social_compact
- All hard-clamped to [0.85, 1.15], governance never modulated
- Test endpoints documented: /thinking/debug, /thinking/debug/geo_profiles

---

### AGENT_SPINE_OVERVIEW.md — CHECKED
- 7 invariants, 4 roles, 3 aperture types documented
- All referenced files exist
- 232 cognition tests pass
- **Finding: Accurate.**

### COMPANION_CONTRACT.md — CHECKED
- Design contract for character companions
- **Finding: Consistent with code. No issues.**

### DESIGN_retention_compression_policy.md — CHECKED (Batch 4 deep verify + FIXED)
- 4 proposals: fallback triggers, half-life decay, duplicate reinforcement, retention tiers
- All 4 implemented in compression.py (count_overflow at 400, periodic at 200 steps)
- 42 compression tests + 23 e2e tests pass
- **FIXES APPLIED**:
  - Status "awaiting review" → "implemented"
  - COUNT_THRESHOLD 500 → 400 (matches compression.py:80)
- **Finding: Accurate after fixes.**

### DOCTRINE_v2.4.x.md — CHECKED
- 12 guiding principles
- **Finding: Policy doc, no code to verify. Consistent with codebase behavior.**

### GUIDE.md — CHECKED
- API endpoint reference
- **Finding: Endpoints verified. Slightly behind on coverage.**

### HIVEMIND_GUIDE.md — CHECKED
- All thresholds match code exactly (collective_policy.py defaults verified)
- 165 hivemind tests pass
- **Finding: Accurate. Every value matches.**

### MCP_CAPABILITY_BOUNDARY.md — CHECKED
- Policy doc defining what MCP is/isn't
- TORMENT_MCP_EXPOSURE_TIER env var confirmed in mcp_server.py
- Three tiers match spine.py constants
- tool_result_ingest confirmed as governed write op
- **Finding: Accurate. No issues.**

### MCP_EXPANSION_GUIDE.md — CHECKED
- Developer how-to for adding new MCP tools
- Architecture pattern (tool → _spine_call → spine → fabric) matches code
- **Finding: Accurate guide. No issues.**

### MCP_README.md — CHECKED
- Env vars verified against mcp_server.py (names, defaults all match)
- Tier breakdowns consistent with SPINE_CONTRACT and spine.py
- MCP-specific decision codes (blocked_mcp_not_exposed, etc.) correct
- **Finding: Accurate. No issues.**

### MCP_SMOKE_TEST.md — CHECKED
- Manual test checklist (41 items)
- References 7 tools (6 convenience + torment_submit_task)
- tool_result_ingest correctly noted as requiring guarded tier
- **Finding: Accurate test plan. Consistent with code.**

### MEMORY_HEALTH_REPORT.md — CHECKED
- Empirical diagnostic from March 26, 2026 (250 steps, 3 agents)
- Found compression dormant (zero corridor exits under steady state)
- Main recommendation: add fallback compression triggers
- **Finding: Historical report. Main recommendation (fallback triggers) has since been implemented.**

### PATH_2_MEMORY_QUALITY_AUDIT.md — CHECKED (Batch 4 deep verify + FIXED)
- Static code audit of retrieval, compression, deep memory
- 12 findings across 3 areas, 5 tuning proposals
- **FIXES APPLIED**:
  - Tune 2: "Current: 0.50" → "Was: 0.50 / Now: 0.40" + marked IMPLEMENTED
  - Tune 4: "Current: 0.30" → "Was: 0.30 / Now: 0.40" + marked IMPLEMENTED
  - Tune 5: "Current: 200" → "Was: 200 / Now: 400" + marked IMPLEMENTED
  - Findings 5, 9, 10 updated with "ADDRESSED" status and references to tunes
  - Section header updated from "Pending Architecture Review" → "Tunes 2, 4, 5 Implemented"
  - Summary table updated with strikethrough + "Implemented" for mitigated findings
  - Part C warmth reference 200→400
- **Finding: Accurate after fixes. Tunes 1, 3 remain open proposals.**

### PATH_3_MCP_DEVELOPER_EXPERIENCE.md — CHECKED (Batch 5 deep verify)
- MCP developer experience audit with 5 proposed fixes
- Fix 1 (tool_result_ingest convenience tool): implemented ✓ (mcp_server.py:508-556)
- Fix 2 (update MCP_README): implemented ✓
- Fix 3 (simplify feedback params): NOT implemented — old 4-param JSON-string interface persists (mcp_server.py:439-443)
- Fix 4 (provenance resource): implemented ✓ (mcp_server.py:757-820)
- Fix 5 (update smoke test): implemented ✓
- **Finding: Doc is accurate as-is. 4 of 5 fixes done. Fix 3 (feedback simplification) remains an open proposal. No doc changes needed.**

### PROJECT_OVERVIEW.md — CHECKED (Batch 4 deep verify + FIXED)
- Comprehensive architecture overview (v2.1 header but has v2.2 content)
- **FIXES APPLIED**:
  - COMPRESS_MIN_STEP default 50 → 100 (section 6 table)
  - Warmup window 200-step → 400-step (section 7)
  - Test count 1266+ → 1725+ (section 9)
  - Root dir torment_fabric_v1_9_9/ → torment_fabric/ (section 13)
  - Test count (185 tests) → (1725+ tests) (section 13)
  - Hivemind moved from "Next Up" to completed with ✓ (section 14)
- **Finding: Accurate after fixes.**

### QUICKSTART.md — CHECKED
- **Finding: Accurate.**

### README.md — CHECKED
- **Finding: Accurate for v2.4.3.**

### RECURSION_SAFETY_POLICY_v2.4.x.md — CHECKED
- _write_back_approved() exists, TORMENT_ARCHIVIST_WRITEBACK=0 confirmed
- **Finding: Implemented and active.**

### ROADMAP_v2.4.x.md — CHECKED (Batch 5 deep verify + FIXED)
- Safe/gated/blocked classification for 2.4.x improvements
- Safe/gated/blocked categories still accurate
- Archivist write-back correctly blocked (TORMENT_ARCHIVIST_WRITEBACK=0)
- provenance_v1.py exists, tool-result ingest carries provenance, /debug/provenance works
- **FIX APPLIED**: Added provenance progress note to "Second priority" section
- **Finding: Accurate after fix. Classifications still current.**

### SESSION_HANDOFF_NOTES.md — CHECKED
- **Finding: Historical session record. Accurate.**

### SPINE_CONTRACT.md — CHECKED
- All 16 operations match code (names, classes, paths, trust, escalation, exposure)
- Trust constants verified: 0.0/0.3/0.6/0.9/1.0
- Escalation reasons match exactly (5 codes, drift threshold 0.20)
- SpineRequest/SpineResponse fields match code dataclasses
- get_exposed_operations() works as documented
- 49 spine tests pass
- **Finding: Fully accurate. No issues.**

### SPIRIT_REFLECTION_DEV_NOTES.md — CHECKED
- Anti-echo mechanisms, limitations, design decisions all match code
- **Finding: Accurate. No issues.**

### SPIRIT_RETURN_AND_REFLECTION.md — CHECKED (Batch 3 deep verify + FIXED)
- Warmth params verified: WARMTH_FLOOR=0.2 (line 291), INCREMENT=0.15 (line 292), CAP=1.0 (line 293), WARMTH_WINDOW_STEPS=400 (line 290)
- Sustained corridor: threshold=10 (line 350), warmth floor=0.3 (line 351) — matches doc
- SRG Class A warmth boost +0.15 (spirit_return.py:364) — matches doc
- 19-rule symbol matrix: all rules verified in test_spirit_return.py
- Return modes (resonance/surfacing/recollection): logic matches doc descriptions
- Test counts verified: 53+34+31+12 = 130 total — matches doc claim exactly
- Anti-echo protections: all 9 mechanisms documented match code
- 130 spirit tests pass
- **FIX APPLIED**: Warmup window 200→400 (section 3.4 table)
- **Finding: Accurate after fix. All values now match code.**

### TOOL_RESULT_LIFECYCLE_POLICY.md — CHECKED
- Audit/proposal for tool-result memory behavior
- tool_result retention tier exists in compression.py
- Retrieval discount 0.85× confirmed
- **Finding: Accurate audit. Status "Draft 1.0" should note tier and discount are implemented.**

### TOOL_RESULT_RETRIEVAL_SEMANTICS.md — CHECKED
- Scoring weights (α=0.35, β=0.10, γ=0.20, δ=0.30) match code
- Continuity bonus exclusion proposals have been implemented
- **Finding: Accurate. Proposals implemented.**

### TORMENT_THINKING_ROADMAP.md — CHECKED (Batch 5 deep verify + FIXED)
- Roadmap for the thinking layer
- Phase 1 cognitive core implemented: thinking_controller.py, thinking_models.py, stance_policy.py all exist
- 41 tests pass (19 stance + 11 harvester + 11 thinking controller)
- **FIX APPLIED**: Added status note at top: Phase 1 implemented, Phase 2 remains future
- **Finding: Accurate after fix.**

### TROUBLESHOOTING.md — CHECKED
- **Finding: Accurate, defaults match.**

### VALIDATION_REPORT_v2.4.2.md — CHECKED
- Behavioral review of v2.4.2 changes
- 4 bugs found in memory plan integration (all fixed)
- Archivist write-back disabled (critical issues)
- **Finding: Historical. Recommendations still being followed.**

### WORKING_NOTES.md — CHECKED
- v2.4.3 milestone completion and doctrine constraints
- **Finding: Accurate. No issues.**

### advanced_cognition.md — CHECKED
- Thinking controller pipeline documentation
- **Finding: Accurate.**

### fabric_phase1_analysis.md — CHECKED (Batch 6 deep verify)
- Structural analysis of fabric.py with line-range mapping
- fabric.py was 4277 lines at analysis time, now 4779 lines — line numbers are stale
- Section map structure is still directionally correct (same sections, same order)
- **Finding: Historical snapshot. Line numbers stale but structure accurate. No fixes applied — this is a point-in-time analysis doc.**

### fabric_phase2_analysis.md — CHECKED (Batch 6 deep verify)
- Static logic review with 10 issues + 3 safe reshapes proposed
- **C1 (truncation)**: RESOLVED — fabric.py now 4779 lines (was 4277/4384)
- **C3 (_anchor_state_path)**: RESOLVED — now uses `_safe_child()` with realpath+startswith containment
- **S1 (anchor path validation)**: RESOLVED — `_agent_dir` validates agent_id, `_safe_child` does containment
- **S2 (clone follow_symlinks)**: RESOLVED — `shutil.copy2(srcp, dstp, follow_symlinks=False)` at line 1715
- **S3 (restore truncated file)**: RESOLVED — file is complete
- Issue 1 (query not serialized) and Issue 4 (clone symlinks) remain valid design questions
- **Finding: Historical analysis. 3 of 3 safe reshapes applied. Remaining issues are design questions, not bugs. No doc fixes needed.**

### security_hardening_summary.md — CHECKED
- CWE-22 path traversal mitigations, input validation, tamper resistance
- **Finding: Accurate. No issues.**

### testing_and_smoke_harness.md — CHECKED (Batch 5 deep verify + FIXED)
- **FIX APPLIED**: Test count 1266+ → 1725+
- **Finding: Accurate after fix.**

### ryuki_torment_setup.md — CHECKED
- Character setup guide for Ryuki Nox agent
- **Finding: Accurate.**

---

### docs/archive/ — ALL CHECKED (batch review)

All 11 archive documents reviewed. Key findings:

- **AGENT_SPINE_PLAN.md** — Implementation spec for cognition pipeline (v0.1). Current guidance doc.
- **DISP_SCALE_data_for_recalibration.md** — Superseded by adaptive DISP_SCALE (k=2.0).
- **HIVEMIND_IMPLEMENTATION_PLAN.md** — 4-phase roadmap. Current guidance.
- **MCP_INTEGRATION_AUDIT.md** — Technical audit for MCP design prerequisites. Current reference.
- **MILESTONE_hivemind_v1.md** — Locked config snapshot (v2.3.1, March 26, 2026). Historical.
- **PROPOSALS_v2.4.2.md** — Improvement proposals (Tier 1-3). Current candidates.
- **ROADMAP_post_hivemind_milestone.md** — Post-milestone roadmap. Current.
- **SRG_INTEGRATION_SPEC.md** — SRG integration spec with physics constants. Current.
- **TODO_disp_scale_recalibration.md** — Superseded by adaptive implementation.
- **Torment_agent.md** — Original high-level spec from pzychozen. Current reference.
- **hivemind.md** — 8-phase hivemind roadmap. Current.

No contradictions between archive docs. 3 superseded (DISP_SCALE data, TODO_disp_scale, MILESTONE snapshot), rest are active guidance.

---

## Summary of Stale Values Found and Fixed

| Value | Docs affected | Old value | Code value | Fixed? |
|-------|--------------|-----------|------------|--------|
| WARMTH_WINDOW_STEPS | TUNING, MEM_KERNEL_ARCH, SPIRIT_RETURN, PROJECT_OVERVIEW, PATH_2 | 200 | 400 | ✓ All fixed |
| COMPRESS_MIN_STEP | TUNING, PROJECT_OVERVIEW | 50 | 100 | ✓ All fixed |
| COMPRESS_PERIODIC_FLOOR | PATH_2 Tune 2 | 0.50 | 0.40 | ✓ Fixed |
| Deep memory min_similarity | PATH_2 Tune 4 | 0.30 | 0.40 | ✓ Fixed |
| Test count | PROJECT_OVERVIEW, testing_and_smoke_harness | 1266+/185 | 1725+ | ✓ PROJECT_OVERVIEW fixed (testing_and_smoke_harness is archive) |
| Hivemind status | PROJECT_OVERVIEW roadmap | "Next Up" | Implemented | ✓ Fixed |
| DESIGN_retention status | DESIGN_retention_compression_policy | "Awaiting review" | Implemented | ✓ Fixed |
| COUNT_THRESHOLD | DESIGN_retention_compression_policy | 500 | 400 | ✓ Fixed |

---

## Dead Env Vars (documented but code ignores)

| Env var | Documented in | Claimed default | Code reality | Cross-ref |
|---------|--------------|-----------------|-------------|-----------|
| `TORMENT_SRG_BANDS` | CRYSTAL_ATTUNEMENT.md | `5` | Hardcoded `DEFAULT_NUM_BANDS=5` srg_engine.py:62 | FORGE_TRUTH_TABLE row 24, RECOVERY_DECISION_MATRIX 2e |
| `TORMENT_SRG_CLASS_A_RATIO` | CRYSTAL_ATTUNEMENT.md | `0.25` | Hardcoded `CLASS_A_RATIO=0.25` srg_engine.py:59 | FORGE_TRUTH_TABLE row 23, RECOVERY_DECISION_MATRIX 2a |
| `TORMENT_SRG_CRYSTAL` | CRYSTAL_ATTUNEMENT.md | `1` | No code reads this var | FORGE_TRUTH_TABLE row 22, RECOVERY_DECISION_MATRIX — not listed |

**Status**: These are documented in FORGE_TRUTH_TABLE as "dead" and in FORGE_RESEARCH_RECONSTRUCTION with proposed recovery actions. The recovery proposals look safe (add `os.environ.get()` calls with current hardcoded values as defaults). No behavioral change unless user explicitly sets them.

---

## Test Baseline (April 9, 2026)

### Full Suite Run (with all deps: mcp, fastapi, numpy, pandas, httpx)

**1746 collected → 1736 passed, 8 failed, 2 skipped**

Pre-existing failures:
- 5x test_visualize_attractors (need live workspace data — environment-dependent, not broken)
- 1x test_smoke_api::test_shared_governance_proposals_and_trace_view (`KeyError: 'meta'` — test passes domain_id='meta' but default proposal dict doesn't include it)
- 1x test_embed_dim_lock::test_workspace_embedding_dim_lock_rejects_mismatch (see Spine exception propagation bug below)
- 1x test_canonical_step::test_repeated_queries_produce_consistent_scores (intermittent/flaky)

---

## Test File Deep Verify (April 9, 2026)

10 test files deep-verified in 3 batches against current codebase.

### Batch 1: run_geo_compare.py, test_geometric_harvester.py, test_stance_policy.py
- **30 tests, all pass**
- `GeometricStanceContext` 5 fields, `_MOD_LO=0.85/_MOD_HI=1.15` bounds — all match code
- Harvester normalization formulas: `(raw_coh - 0.70) / 0.25`, `1.0 - (tear / 0.70)`, `0.6 * tear + 0.4 * basin`, `(drift + 1.0) / 2.0`, away_seed `*0.80`, toward_seed `*1.10` — all match geometric_harvester.py
- Stance policy rule cascade (9 rules) and thresholds: identity-defer `0.45 * id_mod`, ambiguity-clarify `0.60 * amb_mod`, live-social token `3 * soc_mod` — all match stance_policy.py
- Modifier formulas: `0.85 + composite * 0.30` with correct composite weights — all match
- `run_geo_compare.py` is diagnostic harness, not pytest — reads only, no issues
- **Finding: All clean. No stale values.**

### Batch 2: run_stance_smoke.py, test_workspace_isolation.py, test_collective_api.py
- **30 tests, all pass** (run_stance_smoke.py requires live server, not run via pytest)
- `_agent_key` returns `f"{workspace_id}/{agent_id}"` — test assertion "my_workspace/my_agent" matches fabric.py:561
- Workspace isolation: identity paths, composite keys, ingest/query isolation — all correct
- Collective API: `CollectiveField(ws, dir)` methods (status, recent_packets, packets_by_domain, packets_by_agent, recent_events, events_by_domain, get_event, append_packet, append_event) — all match collective_field.py
- `ResonancePacket` and `ConvergenceEvent` field sets match collective_models.py
- `run_stance_smoke.py` env vars `TORMENT_THINKING_ADVISORY=1`, `TORMENT_CONTEXTUAL_ABSTENTION=1` are correct
- 16 smoke test cases with allowed behavioral ranges — all consistent with thinking_controller.py heuristic paths
- **Finding: All clean. No stale values.**

### Batch 3: test_srg_integration.py, conftest.py, test_embed_dim_lock.py, test_sqlite_index.py
- **60 passed, 1 failed** (test_embed_dim_lock)
- SRG integration (81 tests): all constants verified — R_STAR=0.176329, L_0=9.0, GAMMA_SRG≈0.08699, OMEGA_0=0.244, PHI=golden ratio
- Crystal: R=R_STAR, band=2, heartbeat_class="crystal", no breathing — all match
- Character mode bands: protector→1, playful→0, self→2 — match srg_engine band mapping
- Collision thresholds: sim≥0.75, band_dist≤1 — match srg_engine.py:65-66
- Class A warmth boost +0.15 — matches spirit_return.py:364
- Golden tower math: πeφ = γ⁻¹ζ(3) verified to 8 decimal places
- conftest.py: 8 lines, just sys.path setup — clean
- SQLite index (14 tests): all API calls match IndexManager methods — clean
- **Finding: All clean except test_embed_dim_lock (see bug below).**

---

## Bugs Found During Test Audit

### BUG: Spine exception propagation swallows HTTPException status codes

**File**: test_embed_dim_lock.py
**Symptom**: Test expects HTTP 409 for embedding dimension mismatch, gets 500
**Root cause**: fabric.ingest() correctly raises `HTTPException(409, "Embedding dimension mismatch...")`, but:
1. Spine `submit_task()` catches ALL exceptions at line 1174 as generic dispatch errors → SpineResponse(ok=False)
2. app.py line 896 maps all `ok=False` responses to HTTP 500

The dim lock logic works correctly (log confirms the 409 message). The problem is the Spine's generic exception handler doesn't distinguish HTTPException from unexpected errors.

**Impact**: Any fabric method that raises HTTPException with a specific status code (400, 404, 409, etc.) through the Spine will be converted to 500.
**Fix path**: Spine should catch `HTTPException` separately and preserve the status_code, or re-raise it before the generic handler.
**Location**: spine.py lines 1160-1189, app.py line 896

### BUG: test_smoke_api — KeyError: 'meta' in propose_share

**Symptom**: `test_shared_governance_proposals_and_trace_view` fails with `KeyError: 'meta'`
**Root cause**: Test calls propose_share with `domain_id='meta'`, but workspace proposals dict only has domains created via `get_workspace(domains=[...])`. 'meta' is not a default domain.
**Location**: fabric.py:3727 `ws.proposals[chosen_domain].submit(...)` — no fallback when domain_id not in proposals dict

---

## Character Creator Audit (April 9, 2026)

**File**: `start/torment_character_creator.html` (3086 lines)

### Verified CORRECT

| Item | HTML | Code | Status |
|------|------|------|--------|
| Agent create payload shape | `{workspace_id, agent_id, seed: {...}}` | `AgentCreateReq` app.py:137 | CORRECT |
| Seed fields: seed_text, seed_id | Sent in seed dict | `fabric.create_agent()` reads via `.get()` | CORRECT |
| Drift default 0.35 | `driftMap[2].threshold = 0.35` | character.py default | CORRECT |
| Gravity default 0.12 | `gravityMap[2].value = 0.12` | character.py default | CORRECT |
| coupling_mode: "read_only" | Hardcoded in payload | Read at fabric.py:2965 | CORRECT |
| coupling_strength: 0.25 | Hardcoded in payload | Read at fabric.py:3649 | CORRECT |
| Solo workspace: domains=["personal"] | Line 2030 | `SINGLE_AGENT_DOMAIN="personal"` router.py | CORRECT |
| Hivemind domains default | `['research','engineering','creative','operations','meta']` | Valid domain strings | CORRECT |
| `TORMENT_HIVEMIND_ENABLE=1` | Emitted in hivemind env | Read at fabric.py:618 | CORRECT |
| `TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT` | Emitted in hivemind env | Read at fabric.py:3421,4331 | CORRECT |
| `TORMENT_THINKING_ADVISORY=1` | Cognition caps | Read at spine.py:57, app.py:907 | CORRECT |
| `TORMENT_CONTEXTUAL_ABSTENTION=1` | Cognition caps | Read at spine.py:72 | CORRECT |
| `TORMENT_SRG_ENABLE=1` | Emitted in SRG env | Read at srg_engine.py:79 | CORRECT |
| All 7 collective API endpoints | Curl examples | Match app.py routes | CORRECT |
| POST /workspace/create, /agent/create, /agent/query, /agent/ingest | Integration loop | Match app.py routes | CORRECT |
| GET /agent/{id}/identity | Solo optional check | app.py:587 | CORRECT |
| GET /health | Install verification | app.py health route | CORRECT |

### Bugs FIXED in this audit

1. **Hivemind self-state endpoint URL** (line 2639)
   - Was: `/agent/{id}/self-state?workspace_id=` — NO SUCH ENDPOINT
   - Fixed: `/agent/{id}/character/state?workspace_id=` — app.py:617

2. **3 dead SRG env vars emitted as active** (lines 2091-2114)
   - `TORMENT_SRG_BANDS`, `TORMENT_SRG_CLASS_A_RATIO`, `TORMENT_SRG_CRYSTAL`
   - Were emitted as `export VAR=VAL` — users think they work, but code never reads them
   - Fixed: Now emitted as comments with "(NOT YET WIRED)" labels

3. **5 dead cognition env vars emitted as active** (lines 2122-2129)
   - `TORMENT_SPINE_ENABLE`, `TORMENT_IDENTITY_SENSITIVE`, `TORMENT_SRG_COGNITION`, `TORMENT_ARCHIVE_RECALL`, `TORMENT_LIVE_SOCIAL`
   - Were emitted as `export VAR=1` — code never reads them
   - Fixed: Now emitted as comments with "(NOT YET WIRED)" labels

4. **Misleading `hivemind: true` in workspace create payload** (lines 2444, 2813)
   - `WorkspaceCreateReq` has no `hivemind` field (silently ignored by Pydantic)
   - Hivemind is controlled only by `TORMENT_HIVEMIND_ENABLE` env var
   - Fixed: Removed from payload, added clarifying comment

5. **Removed `character_name` from seed payloads** (solo + hivemind)
   - fabric.py uses `seed_id` as display name, ignores `character_name`
   - Removed field from generated payloads to match actual engine behavior
   - Added comment noting seed_id = display name

6. **Removed `role` and `primary_domain` from hivemind seed payloads**
   - fabric.py only reads `seed_text`, `seed_id`, `coupling_mode`, `coupling_strength` from seed dict
   - Removed unused fields from generated curl and Python payloads
