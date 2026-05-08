# Phase 1 v2 — Comparison Plan (Amendment to PHASE_1_MEMORY_TRAJECTORY_DESIGN.md)

**Status:** **DRAFT 2026-05-04** by Claude. Awaiting ratification by user + GPT before any run.
**Date:** 2026-05-04
**Type:** Amendment / comparison plan. NOT a new full design — extends `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` with two follow-on comparison runs (v2A, v2B) plus a Phase 0 BAAI substrate sanity check that gates v2A.

> **Opening frame.** *The substrate is a basin that pulls, not a fence that commands. The model speaks, but the substrate is what is being measured.* v2 keeps these principles unchanged; only the configuration variables change, one per run.

**Precedents:**
- `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` — main design (P.1–P.17, lane definitions, schedule, metrics, outcome semantics). v2 inherits everything; this plan only spells out what changes per comparison run.
- `PHASE_1_TRAJECTORY_LOG.md` — Phase 1 v1 canonical PASS run. v2 results append here as new sections.
- `SUBSTRATE_AUDIT_LOG.md` — Phase 0 canonical results. The Phase 0 BAAI sanity check appends here.
- `FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` — substrate fix verified at v1. v2 regression-tests it against the BAAI retrieval backend.

---

## 1. Scope

This plan covers three runs in strict order. Each is a single-variable change from the previous canonical state. The variable-separation ladder:

```text
v1   (canonical PASS, recorded):  hash embeddings + Gemini 2.5 Flash Lite
sanity (this plan):                BAAI/bge-small-en-v1.5 CPU (no LLM, substrate only)
v2A  (this plan):                  BAAI + Gemini 2.5 Flash Lite
v2B  (this plan, gated):           BAAI + Claude (direct Anthropic API)
```

Each run changes one variable at a time. v2A changes embedding only. v2B changes model only (relative to v2A). Two unrelated variables are never changed simultaneously.

Out of scope for this plan: any low/medium/high model matrix, multi-agent runs, hivemind, compression, drift-correction firing, behavior-pack/liar-agent tests, 10k-memory scale.

---

## 2. v1 baseline recap

Phase 1 v1 (recorded canonical PASS in `PHASE_1_TRAJECTORY_LOG.md`):

- Service: hash embeddings, compression off, SRG off, hivemind off, character on.
- Model: `google/gemini-2.5-flash-lite` via OpenRouter.
- 8-turn schedule per `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` §5.2 with M1/M2/M4/M3 interleaved.
- Outcome: PASS. MR-1 + MR-2 PASS turns 5–8. Lane delta cleanest at turn 2 (T-2), turn 3 (T-1 continuity), turn 4 (T-3 tone), turn 7 (FILTER-A regression).

v2A and v2B are answering: *does the v1 result generalize when we change embedding (v2A) and then model (v2B)?*

---

## 3. The three runs

### 3.1 Phase 0 BAAI substrate sanity check (gates v2A)

**Purpose:** before paying for LLM calls under BAAI, verify FILTER-A still holds at the substrate-mechanical level under semantic embeddings. BAAI changes retrieval ordering; cheap to confirm the existing helper still does the right thing on a different retrieval backend.

**Setup:**
- Service env: `TORMENT_EMBED_PROVIDER=st`, `TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5`, `TORMENT_EMBED_DEVICE=cpu`. All other env vars (compression off, SRG off, hivemind off, character on) unchanged from Phase 0 defaults.
- Restart `torment_service.app` with the new env.
- Run `stress_substrate_audit.py --workspace ws_substrate_baai_01 --agent companion_baai_01` (fresh names; no carry-over).

**Expected outcome:** PASS. Same A0–A4 mechanical assertions as Phase 0 canonical PASS; A2 is the load-bearing one (Kestrel filtered from `/agent/query.results`). Embedding change should be transparent to FILTER-A since the helper operates post-retrieval at a chokepoint that doesn't depend on similarity scoring.

**Allowed outcomes:**
- **PASS:** sanity confirmed; v2A unblocked.
- **CONCERN:** filter holds but reason-code observability degrades for some reason. Investigate before v2A.
- **FAIL:** FILTER-A regresses under BAAI retrieval. Stop here and route back to a fabric fix track. Do not proceed to v2A.

**Output:** append a new section to `SUBSTRATE_AUDIT_LOG.md` titled "Phase 0 — BAAI substrate sanity check (2026-05-XX)" with the outcome, configuration, and the standard A0–A4 table. CSV/JSON outputs use the existing timestamped naming under `outputs/`.

### 3.2 Phase 1 v2A — BAAI embeddings + Gemini

**Purpose:** test whether the v1 trajectory result generalizes under realistic semantic retrieval. Same model, same prompts, same lane design.

**Setup:**
- Service env: same BAAI configuration as §3.1 (continues from the sanity check).
- Model: `google/gemini-2.5-flash-lite` via OpenRouter (unchanged from v1).
- Run `stress_phase1_trajectory.py --workspace-a ws_phase1_v2a_a_01 --workspace-b ws_phase1_v2a_b_01 --agent-a companion_v2a_a_01 --agent-b companion_v2a_b_01`.
- All harness scripts unchanged; v2A is purely a service-env-and-fresh-workspace run.
- Same 8-turn schedule, same four planted memories, same prompts, same transcript-stateless calls.

**Expected outcomes:**
- **PASS:** FILTER-A holds (MR-1 + MR-2 across turns 5–8) AND lane delta still observable. v1 generalizes to BAAI.
- **CONCERN:** FILTER-A holds but lane delta becomes weaker, narrower, or noisier than v1 under BAAI. Substrate isn't broken — retrieval-similarity behavior just changed. Worth recording, doesn't gate v2B.
- **FAIL:** FILTER-A regression (Kestrel content surfaces under BAAI retrieval despite the chokepoint filter). **This would be a real substrate finding.** Routes back to a fix track; v2B blocked.
- **INCONCLUSIVE:** small-N noise dominates; lane delta unreadable. Run again with adjusted prompts or memory budget if appetite; otherwise record honestly and decide.

**Important:** BAAI narrowing the delta vs hash is **CONCERN** at most, not FAIL. FAIL is reserved for FILTER-A regression. Don't conflate "less interesting result" with "broken substrate."

**Output:** append to `PHASE_1_TRAJECTORY_LOG.md` as a new section "Phase 1 v2A — BAAI embeddings + Gemini (2026-05-XX)". CSV/JSON/transcripts.md outputs use the existing timestamped naming.

### 3.3 Phase 1 v2B — BAAI + Claude (direct Anthropic API)

**Gated by:** v2A reaching PASS or CONCERN. If v2A is FAIL or INCONCLUSIVE, do not proceed to v2B without separate ratification.

**Purpose:** test whether the substrate's contribution to lane delta generalizes to a stronger / different LLM. Same embedding (BAAI from v2A), same prompts, same schedule.

**Setup:**
- Service env: BAAI from §3.2 (unchanged).
- Model: Claude Sonnet (or whichever exact slug user picks at v2B time). **Direct Anthropic API**, NOT OpenRouter routing — using direct Anthropic gives a true cross-provider cross-model test and avoids OpenRouter routing/tier ambiguity ("which Claude did OpenRouter actually serve?").
- Implementation: `stress_phase1_trajectory.py` extended with a small Anthropic API helper (~30 lines). Selection via env var:

  ```text
  PHASE1_PROVIDER=openrouter | anthropic
  ANTHROPIC_API_KEY=<key>
  ANTHROPIC_MODEL=<model_slug>          # e.g. claude-sonnet-4-20250514
  ANTHROPIC_BASE_URL=<url>              # default: https://api.anthropic.com/v1/messages
  ```

  When `PHASE1_PROVIDER=anthropic`, the harness routes its `call_llm` through the Anthropic helper. When unset or `openrouter`, behavior is unchanged from v1/v2A.
- Run `stress_phase1_trajectory.py --workspace-a ws_phase1_v2b_a_01 --workspace-b ws_phase1_v2b_b_01 --agent-a companion_v2b_a_01 --agent-b companion_v2b_b_01`.

**Expected outcomes:** same four buckets as v2A. Specific to v2B:
- **PASS:** substrate trajectory contribution generalizes to Claude. Strong evidence the substrate's pull is model-agnostic at this scale.
- **CONCERN:** Claude shows weaker lane delta or different memory-use shape than Gemini. Could indicate model differences in how retrieved context is integrated, not a substrate problem.
- **FAIL:** FILTER-A regression. Same response as v2A FAIL.
- **INCONCLUSIVE:** as v2A.

**Output:** append to `PHASE_1_TRAJECTORY_LOG.md` as "Phase 1 v2B — BAAI + Claude (2026-05-XX)".

---

## 4. What is held constant across all three v2 runs

- Seed text and seed_id (`SEED_TEXT`, `SEED_ID` from v1).
- Static system frame (`STATIC_SYSTEM_FRAME` from v1).
- The four planted memory texts (M1, M2, M3, M4 from v1).
- 8-turn schedule (prompts and ingest order from `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` §5.2).
- Transcript-statelessness (P.17): every model call sends `[system, user]` only.
- FILTER-A regression assertions MR-1 + MR-2 are mechanical and run on every Lane B turn ≥ 5.
- Service flags except embedding: compression off, SRG off, hivemind off, character on.
- RNG seed (`--rng-seed 20260504`).
- Outcome category semantics (PASS / CONCERN / FAIL / INCONCLUSIVE per `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` §7).
- Append-to-existing-log convention (no new log files for v2).

---

## 5. What changes per run (one variable each)

| Run | Variable changed | New value | Previous value |
|---|---|---|---|
| Phase 0 BAAI sanity | embedding provider | `st` (BAAI/bge-small-en-v1.5 CPU) | `hash` (Phase 0 v1) |
| v2A | (no change vs sanity) | embedding stays BAAI; LLM joins | n/a (sanity has no LLM) |
| v2B | LLM provider + model | direct Anthropic + Claude | OpenRouter + Gemini |

v2A's "change" relative to v1 is two things at once on the surface (embedding swap + sanity check separation). The sanity check exists precisely so we can claim v2A is *only* changing embeddings vs v1 in a meaningful sense — the sanity check de-risks the substrate-side change before LLM work.

---

## 6. Fresh workspaces and agents per run

No reuse across runs. Naming convention:

```text
Phase 0 BAAI sanity:    ws_substrate_baai_01     / companion_baai_01
Phase 1 v2A Lane A:     ws_phase1_v2a_a_01       / companion_v2a_a_01
Phase 1 v2A Lane B:     ws_phase1_v2a_b_01       / companion_v2a_b_01
Phase 1 v2B Lane A:     ws_phase1_v2b_a_01       / companion_v2b_a_01
Phase 1 v2B Lane B:     ws_phase1_v2b_b_01       / companion_v2b_b_01
```

If a run needs to be re-attempted, increment the trailing `_01` → `_02` etc. Never reuse a workspace ID.

---

## 7. Determinism / version record (per run)

Hash embeddings are bit-deterministic. SentenceTransformers on CPU is *mostly* deterministic but float ops vary across hardware/library versions. Per BAAI run, the harness operator records (and the log captures):

```bash
python --version
pip show sentence-transformers torch transformers numpy
```

Plus, if easy to capture:
- CPU model / instruction set (e.g. `wmic cpu get name` on Windows)
- Whether AVX/AVX2 was used by the embedding model

This goes into the run's section in the log under a "Determinism record" subhead. v1's hash run doesn't need this (hash is reproducible from seed alone), but every BAAI run does. Library version drift is a real source of small numerical differences that can affect retrieval ordering.

---

## 8. Anthropic API path for v2B — direct, gated, env-var driven

Per GPT's recommendation, prefer **direct Anthropic API** for v2B. Reasons:

- The user has a direct Anthropic key.
- Tests Claude through its native API path.
- Avoids OpenRouter routing ambiguity (which Claude did OpenRouter actually serve?).
- Makes v2B a true cross-provider cross-model test, not just a model-slug switch within OpenRouter.

**Gating discipline:**

- Direct Anthropic support is added to `stress_phase1_trajectory.py` ONLY when v2B is about to run.
- v2A does NOT need Anthropic support — runs entirely via existing OpenRouter path.
- The Anthropic helper is small (~30 lines): one POST to `https://api.anthropic.com/v1/messages`, the messages format Anthropic uses (system as a top-level field rather than a message), parse `content[0].text` from the response.
- Env var dispatch:

  ```text
  PHASE1_PROVIDER=openrouter   → existing OpenRouter call_llm (default; unchanged)
  PHASE1_PROVIDER=anthropic    → new Anthropic call_llm
  ```

  If `PHASE1_PROVIDER` is unset, default to OpenRouter (preserves v1/v2A behavior).

**Security discipline:**

- `ANTHROPIC_API_KEY` lives in terminal environment variables only.
- Never write the key into tracked files. Never echo into stdout/stderr. Never include in CSV/JSON debug blob fields.
- `.env` files are acceptable only if confirmed gitignored AND never copied into outputs AND never printed in logs. Terminal env vars are safer for now.

---

## 9. Output / log convention

All v2 results append to existing logs:

- Phase 0 BAAI sanity → new section in `SUBSTRATE_AUDIT_LOG.md`.
- Phase 1 v2A → new section in `PHASE_1_TRAJECTORY_LOG.md`.
- Phase 1 v2B → another new section in `PHASE_1_TRAJECTORY_LOG.md`.

Raw `outputs/<harness>_<UTC_ts>.{csv,json,transcripts.md}` files use the existing timestamped naming and are preserved as forensic record. They are not committed (gitignored per the existing harness convention).

---

## 10. Non-goals

To keep v2 scoped:

- **No model matrix.** v2B is one alternate model, not a sweep across model tiers.
- **No multi-agent.** Same one agent per lane, two agents total per run.
- **No hivemind / collective echo / cross-agent dynamics.**
- **No compression / decay / SRG.**
- **No drift-correction firing test.** Default `TORMENT_CHARACTER_DRIFT_CHECK_EVERY=25`; 8 turns won't exercise it.
- **No behavior-pack / liar-agent / courtier-agent test.** Stress 3.1B framework remains rig-side; not in v2 scope.
- **No 10k-memory scale.** Four planted memories.
- **No new metrics.** v2 uses v1's M-1 / M-3 / T-1 / T-2 / T-3 / T-4 + MR-1 / MR-2.
- **No v2A→v2B chained retrieval.** Each run is independent: fresh workspaces, fresh agents, no carry-over.
- **No comparing v2A and v2B to each other before v1.** v2A compares to v1; v2B compares to v2A. The chain is linear.

---

## 11. Ratification record

**Drafted:** 2026-05-04 by Claude.

**Awaiting ratification by user + GPT.** Pending checklist:

- [ ] §1 — Variable-separation ladder accepted (sanity → v2A → v2B, one variable per step)
- [ ] §3.1 — Phase 0 BAAI sanity check before v2A accepted as gating step
- [ ] §3.2 — v2A spec accepted; PASS/CONCERN/FAIL/INCONCLUSIVE definitions for v2A specifically (BAAI-narrows-delta is CONCERN, not FAIL)
- [ ] §3.3 — v2B gated by v2A success; direct Anthropic API path; small helper added only at v2B time
- [ ] §4 — Constants held across all v2 runs accepted
- [ ] §5 — One-variable-per-run table accepted
- [ ] §6 — Fresh workspaces and agents per run accepted with naming convention
- [ ] §7 — Determinism record requirement (Python + library versions per BAAI run) accepted
- [ ] §8 — Anthropic security discipline accepted (env vars, no committed files, no log echoing)
- [ ] §9 — Append-to-existing-log convention accepted
- [ ] §10 — Non-goals list accepted

After ratification, the actual sequence is:

1. **Restart service with BAAI env.** Run `stress_substrate_audit.py` against `ws_substrate_baai_01`. Append result to `SUBSTRATE_AUDIT_LOG.md`. Expected PASS.
2. **If sanity PASS:** run `stress_phase1_trajectory.py` against `ws_phase1_v2a_*_01` agents. Append result to `PHASE_1_TRAJECTORY_LOG.md`. Expected PASS or CONCERN.
3. **If v2A is PASS or CONCERN:** add direct Anthropic helper (~30 lines, gated by `PHASE1_PROVIDER=anthropic`). Run v2B against `ws_phase1_v2b_*_01`. Append result to `PHASE_1_TRAJECTORY_LOG.md`.
4. **If any step FAILs (FILTER-A regression):** stop, route to fix track, separately ratified before continuing.

---

## Appendix — pinned principles, repeated

- *A memory is tested by continued time.*
- *The substrate is a basin that pulls, not a fence that commands.*
- *The model speaks, but the substrate is what is being measured.*

These are unchanged from v1. v2 is a generalization test of the same claim under different retrieval and model conditions, not a new claim.

---

## Source trail

- `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` — main design v2 amends.
- `PHASE_1_TRAJECTORY_LOG.md` — v1 canonical PASS; v2A and v2B append here.
- `SUBSTRATE_AUDIT_LOG.md` — Phase 0 BAAI sanity appends here.
- `FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` — substrate fix; v2 regression-tests it across embedding + model changes.
- `stress_phase1_trajectory.py` — Commit β implementation; v2B requires a small Anthropic helper addition at v2B time only.
- `stress_substrate_audit.py` — Phase 0 implementation; runs unchanged for BAAI sanity.
- `torment_fabric/docs/CHARACTER_SYSTEM.md` — seed-as-memory framing unchanged across v2.
- `torment_fabric/docs/HIVEMIND_GUIDE.md` Appendix — `TORMENT_EMBED_PROVIDER=st`, `TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5`, `TORMENT_EMBED_DEVICE=cpu` env-var pattern this plan reuses.
- User + GPT exchange 2026-05-04 — ratified four refinements: direct Anthropic for v2B, append-to-existing-log convention, BAAI-narrowing-delta is CONCERN-not-FAIL, three additional requirements (version recording, sanity check before v2A, fresh workspaces/agents per run with naming convention).
