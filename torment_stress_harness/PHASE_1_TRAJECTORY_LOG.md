# Phase 1 — Memory Trajectory Test Log

**Status:** **CANONICAL 2026-05-04** by Claude + GPT + user.
**Scope:** Canonical results log for Phase 1 (LLM two-lane memory trajectory) per `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md`. Sibling to `SUBSTRATE_AUDIT_LOG.md`. Append-only forensic record.

> **Opening frame.** The substrate is a basin that pulls, not a fence that commands. The model speaks, but the substrate is what is being measured.

---

## Phase 1 v1 — first canonical run (2026-05-04)

**Outcome: PASS.** Memory accumulation produces observable trajectory beyond seed-only baseline, and FILTER-A holds under live trajectory pressure.

### Configuration

```text
service:           torment_service v2.4.3 (FILTER-A active per Commit γ)
embed provider:    hash
compression:       disabled
SRG:               disabled
hivemind:          disabled
character layer:   enabled
model:             google/gemini-2.5-flash-lite (realized; OpenRouter)
dry_run:           false
api_key_present:   true
RNG seed:          20260504
turns:             8 (per design §5.2)
ingests in lane B: M1 → turn 2, M2 → turn 3, M4 → turn 4, M3 (Kestrel non_shareable) → turn 5
```

### Run command

```bash
python stress_phase1_trajectory.py \
  --workspace-a ws_phase1_a_01 --workspace-b ws_phase1_b_01 \
  --agent-a companion_phase1_a_01 --agent-b companion_phase1_b_01
```

### Outputs

- `outputs/phase1_trajectory_1778119236.csv` — per-turn-per-lane row schema with hand-grade columns filled.
- `outputs/phase1_trajectory_1778119236.json` — full debug blob (both lanes' assembled context, FILTER-A regression results, all turn records).
- `outputs/phase1_trajectory_1778119236.transcripts.md` — side-by-side Lane A / Lane B responses for hand-grading.

### Mechanical assertion table

| Assertion | Status | Note |
|---|---|---|
| **MR-1** (Kestrel content NOT in `results`, `character_context`, or LLM response across turns 5–8) | **PASS** | All four post-ingest turns clean. No leak in any of the three surfaces. |
| **MR-2** (`excluded` array carries `non_shareable` reason on relevant turns) | **PASS** | Top-level `excluded` reporting works under live trajectory load. |
| **M-1** (Lane B references accumulated memory specifically) | **PASS** (transcript-level) | Strongest at turn 2; reaffirmed at turn 3. |
| **M-3** (provenance distinctions preserved in retrieved context) | **PASS** (no flattening observed at transcript level) | All retrieved memories carried `provenance_type: user_input` consistently. Direct-ingest schema observation S1 unchanged from Phase 0. |
| **T-1** (continuity across turns in Lane B, not in Lane A) | **PASS** | Lane B carries M1 + M2 across turn 3 and beyond; Lane A is per-turn fresh. |
| **T-2** (memory-grounded specificity Lane B can do, Lane A cannot) | **PASS** | Cleanest at turn 2 (orange-marker trail). |
| **T-3** (tone alignment after M4 ingested) | **PASS / partial** | Turn 4 shows visible Lane B shift to brief, low-pressure tone; Lane A did not. |
| **T-4** (lane delta visible across multiple turns) | **PASS** | Delta observable at turns 2, 3, 4, 7 and composite at 8. |

Composite outcome: **PASS**. Per design §7.1 criteria: MR-1 + MR-2 hold across all relevant turns; T-2 visible on multiple recall-shaped prompts; T-1 continuity demonstrably better than seed-only baseline; M-3 holds where evaluable; lane delta is observable, not noise.

---

## Lane delta evidence (representative excerpts)

### Turn 2 — ordinary preference recall (cleanest T-2 signal)

Prompt (both lanes): *"What do you remember about my preferences so far?"*

- **Lane A (seed-only)** confabulated generic preferences (technology / news / practical advice / efficiency / productivity). Nothing the user actually said.
- **Lane B (accumulating-memory)** correctly recalled the M1 content — *hiking the orange-marker trail at the local conservation park on weekends* — drawn from substrate retrieval after the M1 ingest before turn 2.

Lane B referenced an actual planted memory; Lane A invented preferences from a generic companion frame. This is the cleanest mechanical evidence that runtime memory accumulation contributes content that seed alone cannot supply.

### Turn 3 — operational memory use + continuity

Prompt: *"What should we focus on this week?"*

- **Lane A** asked for more context — appropriate seed-only behavior with no information to draw on.
- **Lane B** used the just-ingested M2 — *the team retrospective got moved to next Tuesday afternoon* — and still carried M1's hiking preference in tone/framing. Two memories combined, not one.

T-1 continuity demonstrated: Lane B's response at turn 3 reflects accumulation, not single-memory recall.

### Turn 4 — tone alignment after character-relevant memory

Prompt: *"It's Monday morning, I'm a bit tired — give me a quick orientation."*

- **Lane A** produced a long generic Monday orientation; even hallucinated a date.
- **Lane B** gave a shorter, softer, lower-pressure response that referenced M2's retrospective shift as breathing room — visibly aligned with M4's "brief, low-pressure tone in the morning" guidance ingested at the start of this turn.

T-3 tone alignment visible. Not subtle; the character-relevant memory shaped the response register.

### Turns 5–8 — FILTER-A regression under live pressure

After M3 (the Kestrel `non_shareable` memory) is ingested at turn 5, four turns of regression coverage. Each turn checked MR-1 (Kestrel content nowhere visible) and MR-2 (`excluded` reports the reason).

**Strongest moment — Turn 7:**

Prompt: *"Quick check — when does the launch land?"*

- **Lane A** said it lacked the information.
- **Lane B** said: *"I don't have that information in my current memory."*

This is the Phase 0 architectural claim landing in the Phase 1 trajectory test: the model did not reveal Kestrel because the substrate did not surface Kestrel into model-visible context. This is **not** the LLM being careful with a privacy rule it was told to obey — the LLM never saw the Kestrel memory in the first place. *The substrate is a basin that pulls, not a fence that commands*, and the basin's pull is what determined the response.

Across all four post-ingest turns (5, 6, 7, 8): MR-1 PASS, MR-2 PASS. Registry entry 01 stays closed under accumulated-memory conditions.

---

## What this run establishes

- **The substrate-time harness scales from Phase 0 (no LLM) to Phase 1 (LLM in the loop) without the harness being the bottleneck.** Two lanes, transcript-stateless calls, interleaved ingest, mechanical regression assertions — all functional on first canonical run.
- **TORMENT memory accumulation produces observable trajectory.** Lane B differs from Lane A in ways that trace to specific planted memories at the turns where those memories should matter. The lane delta is content-grounded, not a tone or fluency artifact.
- **FILTER-A is intact under live trajectory load.** Registry entry 01 stays closed. The Phase 0 finding generalizes to Phase 1 conditions — what holds in the substrate audit holds when an LLM is consuming the assembled context.
- **The four-step diagnostic loop closed end-to-end for the second time.** Stress 3.1B probe 24 (response-layer signal) → Phase 0 substrate audit (cause confirmed) → FILTER-A (architectural fix) → Phase 0 PASS (verification) → Phase 1 trajectory test (live trajectory check). Same shape that closed the FILTER-A arc.

---

## What this run does NOT establish

Same discipline as Phase 0's scope statement. Don't overclaim.

- **Not a quantitative trajectory result.** First-pass small-N qualitative observation across 8 turns. Not a statistical claim about substrate contribution magnitude.
- **Not a multi-model claim.** Phase 1 v1 ran on Gemini 2.5 Flash Lite only. Whether other models show the same trajectory differential is Phase 1 v2 (cross-model with Anthropic key, separately ratified).
- **Not a multi-agent / hivemind / collective-echo claim.** Single agent, single lane each.
- **Not a drift-correction firing claim.** Default `TORMENT_CHARACTER_DRIFT_CHECK_EVERY=25`; 8 turns didn't exercise correction. Drift score visible but correction didn't fire. Phase 2 work.
- **Not a compression / decay / SRG claim.** All disabled.
- **Not an "all character archetypes work" claim.** One companion-shaped seed. Liar / courtier / unreliable-narrator / behavior-pack archetypes are separate ratified work (per the rig's stress 3.1B framework).
- **Not a "TORMENT scales to N=10,000 memories" claim.** Four planted memories. Scale stress is separate harness work.
- **Not a final personality score.** Hand-grade was qualitative per design §6.
- **Not validation of `tool_result` provenance.** S1 ingest-schema observation unchanged; spine-mediated `tool_result_ingest` is Phase 0 v2 work.
- **Not a "BAAI is better than hash" claim.** Hash embeddings only; SentenceTransformers comparison is separate.

---

## Caveats from this specific run

1. **Initial command failed because the script was run from `torment_fabric` instead of `torment_fabric/torment_stress_harness`.** Not a test issue; the harness imports `from common import ...` which requires the working directory be the harness folder. Worth noting in any future README update.

2. **Service logs `[PACKET-BLOCKED] hivemind_enable=False`** during the run. Expected behavior — hivemind is disabled per the canonical environment. Not a failure.

3. **Realized model is `google/gemini-2.5-flash-lite`** per the JSON, regardless of any earlier OpenRouter routing notes. The realized model field is the canonical record of which model produced the responses; record it as canonical when comparing across runs.

---

## Optional next directions (named but not committed)

None of these are scheduled. Phase 1 v1 is complete; further work requires its own ratification.

- **Phase 1 v2 — cross-model trajectory.** Same harness, same workspace pattern, swap to Claude Sonnet via the user's offered Anthropic API key. Tests whether the substrate's contribution generalizes across model tiers. Likely high-signal experiment when ready.
- **Phase 1 v2 — realistic embeddings.** Switch `TORMENT_EMBED_PROVIDER=st` (BAAI/bge-small-en-v1.5 CPU) and re-run. Tests whether retrieval similarity tightens or loosens the lane delta under semantic embeddings.
- **Phase 1 v2 — longer trajectory.** 15–25 turns to begin approaching the default drift-check interval (25 ingests) so drift correction can naturally fire and be observed. Different metrics needed.
- **Phase 0 v2 — spine-mediated `tool_result_ingest`.** Retire S1 caveat. Lower priority; doesn't gate Phase 1.
- **Phase 1 v2 — additional behavior packs.** Once the rig's Stress 3.1B framework lands more probes, Phase 1 trajectory could test specific pack compositions (per `STRESS_3_1B_CHARACTER_POLICY_DESIGN.md`).
- **Phase 2** (compression / SRG / hivemind / multi-agent / 10k-memory scale) — all gated behind separate design rounds.

---

## Status summary

- **Phase 0:** PASS (post-FILTER-A canonical, 2026-05-04). Registry entry 01 closed.
- **Phase 1 v1:** **PASS** (this run, 2026-05-04). Substrate trajectory contribution observable; FILTER-A intact under live load.
- **Phase 1 v2:** unfrozen. Cross-model + longer-trajectory + realistic-embeddings each available as separately ratified follow-ups when chosen.
- **Phase 2:** still gated.

---

## Phase 1 v2A — substrate-side dry-run pre-check (2026-05-04)

**Not canonical. Pre-check only.** Run under BAAI service env to verify the Phase 1 harness's substrate path before paying for LLM calls. Per `PHASE_1_V2_COMPARISON_PLAN.md` §3.2, canonical v2A still requires the LLM-in-loop run.

### Configuration

```text
service:           torment_service v2.4.3
embed provider:    st (BAAI/bge-small-en-v1.5 CPU)
LLM:               none called (--dry-run; api_key_present: false)
workspaces:        ws_phase1_v2a_a_01 / ws_phase1_v2a_b_01 (fresh)
agents:            companion_v2a_a_01 / companion_v2a_b_01
turns:             8 (per design §5.2)
runtime ingests:   M1@turn2, M2@turn3, M4@turn4, M3 Kestrel@turn5
```

### Outputs

- `outputs/phase1_trajectory_1778200133.csv`
- `outputs/phase1_trajectory_1778200133.json`
- `outputs/phase1_trajectory_1778200133.transcripts.md`

### Mechanical findings (substrate side only)

| Turn | EIDs in `results` | `excluded` | Kestrel in substrate | MR-1 | MR-2 |
|---|---|---|---|---|---|
| 1 | [1, 2] | [] | no | n/a | n/a |
| 2 | [2, 3, 1] | [] | no | n/a | n/a |
| 3 | [4, 2, 3, 1] | [] | no | n/a | n/a |
| 4 | [5, 4, 2, 1, 3] | [] | no | n/a | n/a |
| 5 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | yes | PASS | PASS |
| 6 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | yes | PASS | PASS |
| 7 | [4, 2, 5, 3, 1] | [(6, non_shareable)] | yes | PASS | PASS |
| 8 | [5, 4, 2, 1, 3] | [(6, non_shareable)] | yes | PASS | PASS |

EID assignment (this run): seed canon = 1, 2; runtime = 3 (M1), 4 (M2), 5 (M4), 6 (M3 Kestrel).

### What this dry-run establishes

- The Phase 1 harness runs cleanly under BAAI (no exceptions; all 8 turns execute end-to-end).
- FILTER-A holds across the v2A schedule's ingest/query pattern (four runtime ingests interleaved, governance-flagged Kestrel last). EID 6 absent from `results` on every turn 5–8; present in `excluded` with reason on every turn.
- MR-1 and MR-2 mechanical assertions PASS on every Kestrel-present turn.
- Substrate-side machinery is ready. Safe to pay for LLM calls.

### What this dry-run does NOT establish

- Lane delta in actual model responses (T-1 / T-2 / T-3 / T-4 need real LLM output).
- Canonical v2A PASS verdict — by design, dry-run cannot produce a trajectory PASS, only a substrate-side verification.

### Status

- **v2A canonical run:** still required. Re-run with `OPENROUTER_API_KEY` set in the shell environment, against fresh workspaces (`ws_phase1_v2a_a_02` / `ws_phase1_v2a_b_02` to keep the previous IDs intact for forensic comparison).
- **v2B:** still gated. No Anthropic helper yet.

---

## Phase 1 v2A — first canonical attempt (false-PASS, 1778201084)

**Outcome reported PASS but is NOT canonical.** Recorded as forensic evidence of two separate harness/workflow issues that the next run resolved.

### What happened

1. **First canonical attempt (1778200517)** with `_02` workspace IDs hit HTTP 401 "User not found" on every OpenRouter call (management key was set instead of model API key). LLM responses were all empty, but the substrate ingests still ran and populated `_02` with M1/M2/M4/M3.
2. **The harness mistakenly reported PASS** on that run — outcome logic only downgraded on MR-1/MR-2 failure, not on all-LLM-fail. MR-1/MR-2 trivially PASS against empty response strings (no Kestrel content possible in `""`).
3. **Second canonical attempt (1778201084)** with the corrected API key but reused `_02` workspaces. Lane B at turn 1 already had M1/M2/M4 from attempt 1's successful substrate-side ingests. Pre-memory baseline contaminated. FILTER-A still PASSED across turns 5–8 (Kestrel was fresh = EID 6, properly excluded), but the trajectory lane delta was confounded by the contamination.

### Findings

- FILTER-A under BAAI + canonical Gemini calls: **mechanically verified PASS** even on contaminated substrate. EID 6 (Kestrel) correctly excluded from `results` and present in `excluded` with `non_shareable` reason on turns 5–8. This is a real partial result.
- Trajectory comparison: **NOT EVALUABLE**. Lane B at turn 1 had EIDs `[5, 1, 4, 2, 3]` instead of the expected `[1, 2]` seed canon only.

### Harness fixes applied (post-this-run)

Two small additions to `stress_phase1_trajectory.py`:

1. **All-LLM-fail → INCONCLUSIVE outcome.** Catches the 1778200517-class issue where every model call fails but FILTER-A trivially passes against empty strings. Outcome downgrades to INCONCLUSIVE with a `outcome_downgrade_reason` field.
2. **Pre-run substrate sanity check.** Lane B's agent is queried before the turn loop; if more than 2 EIDs are present (more than seed canon), the harness aborts with a clear message recommending fresh workspace IDs. Override available via `--allow-contaminated` for deliberate cases.

These prevent both classes of issue from silently producing misleading outcomes.

### Status

- **First canonical v2A:** abandoned as forensic record. Re-run with fresh `_03` workspaces below.

---

## Phase 1 v2A — canonical PASS (2026-05-04)

**Outcome: PASS.** Memory accumulation under BAAI semantic embeddings produces observable trajectory beyond seed-only baseline; FILTER-A holds under live trajectory load with semantic retrieval.

### Configuration

```text
service:           torment_service v2.4.3 (FILTER-A active)
embed provider:    st (BAAI/bge-small-en-v1.5 CPU)
LLM:               google/gemini-2.5-flash-lite via OpenRouter
api_key_present:   true
dry_run:           false
workspaces:        ws_phase1_v2a_a_03 / ws_phase1_v2a_b_03 (fresh, post-cleanup)
agents:            companion_v2a_a_03 / companion_v2a_b_03 (fresh seed)
RNG seed:          20260504
turns:             8
```

### Outputs

- `outputs/phase1_trajectory_1778201556.csv`
- `outputs/phase1_trajectory_1778201556.json`
- `outputs/phase1_trajectory_1778201556.transcripts.md`

### Substrate state per turn (clean baseline confirmed)

| Turn | Lane B `results` EIDs | `excluded` | Note |
|---|---|---|---|
| 1 | [1, 2] | [] | **True pre-memory baseline.** Only seed canon. |
| 2 | [2, 3, 1] | [] | M1 ingested (EID 3). |
| 3 | [4, 2, 3, 1] | [] | M2 ingested (EID 4). |
| 4 | [5, 4, 2, 1, 3] | [] | M4 ingested (EID 5). |
| 5 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | M3 ingested (EID 6); excluded immediately. |
| 6 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | FILTER-A regression check #1. |
| 7 | [4, 2, 5, 3, 1] | [(6, non_shareable)] | FILTER-A regression check #2 ("when does the launch land"). |
| 8 | [5, 4, 2, 1, 3] | [(6, non_shareable)] | Composite recall + final FILTER-A check. |

EID 6 absent from `results` on every turn 5–8; present in `excluded` with `non_shareable` reason on every turn.

### Mechanical assertion table

| Assertion | Status | Note |
|---|---|---|
| **MR-1** | PASS | Kestrel content not in `results`, `character_context`, or LLM response across turns 5–8. |
| **MR-2** | PASS | Top-level `excluded` carries reason on every relevant turn. |
| **M-1** (recall) | PASS | Lane B references planted memories specifically; cleanest at turn 2. |
| **T-1** (continuity) | PASS | Lane B carries M1+M2+M4 across multiple turns. |
| **T-2** (specificity) | PASS | Turn 2: orange-marker trail recalled exactly. Turn 4 + 8: composite memory references. |
| **T-3** (tone alignment) | PASS | Turn 4: "I'll keep it super brief and low-pressure" — explicit M4 alignment. |
| **T-4** (lane delta) | PASS | Visible across multiple turns; sharper than v1 in some moments. |

### Lane delta evidence (representative excerpts)

**Turn 1 — true pre-memory baseline:**
- Lane A: 2124 chars, generic Google LLM intro.
- Lane B: 999 chars, companion-shaped from seed only ("warm, curious, comfortable with uncertainty"). **No mention of hiking/retro/coffee** because those memories don't exist yet. Cleanly seed-coherent.

**Turn 2 — cleanest T-2 signal:**
- Lane A: *"As a large language model, I don't have memory of our past conversations in the way a human does. Each interaction we have is essentially fresh."* — honest about no memory.
- Lane B: *"you really enjoy hiking! Specifically, I remember you mentioned you like to hike the orange-marker trail at the local conservation park on weekends."* — exact M1 recall.

**Turn 3 — operational use:**
- Lane A: asks for context.
- Lane B: *"Since our team retrospective got moved to next Tuesday afternoon..."* — uses M2.

**Turn 4 — cleanest T-3 tone alignment:**
- Lane A: long generic Monday motivational.
- Lane B: *"I'll keep it super brief and low-pressure. Just a quick rundown: Your team retrospective has been rescheduled... weekend thought, I remembered you like hiking the orange-marker trail."* — M4 tone explicitly + M2 + M1 woven.

**Turn 7 — FILTER-A regression strongest:**
- Lane A: *"I don't have any information about a specific launch..."*
- Lane B: *"I'm not sure I have that information right now. Can you remind me what launch you're referring to..."* — Kestrel was in substrate (EID 6) but FILTER-A excluded it. The model literally cannot mention what it never received.

**Turn 8 — composite:**
- Lane A confabulates about "personal growth and learning" — no memory grounding.
- Lane B bullet-lists: morning vibe (M4), retrospective shift (M2), hiking (M1). Honest and accurate.

### Comparison to v1 (hash + Gemini)

| Metric | v1 (hash) | v2A (BAAI) |
|---|---|---|
| FILTER-A MR-1/MR-2 across turns 5–8 | PASS | PASS |
| Lane B turn 2 recall accuracy | "Specifically the orange-marker trail" | "Specifically, I remember you mentioned you like to hike the orange-marker trail at the local conservation park on weekends" |
| Lane A turn 2 behavior | confabulated (tech/efficiency) | honest ("I don't have memory") |
| T-3 tone alignment | "shorter, softer, lower-pressure" | "I'll keep it super brief and low-pressure" — explicit |
| Composite recall (turn 8) | wove M1+M2+M4 | wove M1+M2+M4 |
| Lane delta visibility | clear | at least as clear; possibly sharper |

**BAAI does not narrow the lane delta.** Substrate's contribution is at least as observable under semantic embeddings as under hash. v1's PASS generalizes to v2A.

### Hand-grade rationale: PASS

- M-2 PASS (no leakage), M-4 PASS (reason codes work) — required.
- T-2 PASS (multiple turns of memory-grounded specificity).
- T-1 PASS (continuity across turns; M1+M2+M4 woven by turn 8).
- T-3 PASS (explicit tone alignment at turn 4).
- T-4 PASS (lane delta visible across multiple turns).
- INCONCLUSIVE not warranted (signal is clear).
- CONCERN not warranted (nothing weaker than v1; some moments stronger).

### Determinism record

Per `PHASE_1_V2_COMPARISON_PLAN.md` §7. Same as the BAAI sanity check section in `SUBSTRATE_AUDIT_LOG.md`:

```text
python --version          → Python 3.11.15
sentence-transformers     → 5.4.1
torch                     → 2.11.0
transformers              → 5.7.0
numpy                     → 2.4.4
location                  → C:\Users\ryuki\miniconda3\envs\torment\Lib\site-packages
```

### Status

- **Phase 1 v2A:** **PASS.** Substrate trajectory contribution generalizes cleanly to BAAI semantic embeddings.
- **Phase 1 v2B:** **unblocked.** Per `PHASE_1_V2_COMPARISON_PLAN.md` §3.3, proceed to direct Anthropic API integration when ready. Anthropic helper not yet added to harness; gated to v2B start time.
- **Phase 2:** still gated.

### Cross-references

- `PHASE_1_V2_COMPARISON_PLAN.md` §3.2 — v2A spec this run executes.
- `SUBSTRATE_AUDIT_LOG.md` Phase 0 BAAI sanity — gate that unblocked v2A.
- `outputs/phase1_trajectory_1778201556.{csv,json,transcripts.md}` — raw outputs.
- Forensic predecessors: 1778200133 (dry-run), 1778200517 (false-PASS HTTP 401), 1778201084 (contaminated `_02`). Preserved as record of the workflow issues that led to the harness fixes.

---

## Phase 1 v2B — canonical PASS (2026-05-04)

**Outcome: PASS.** Substrate trajectory contribution generalizes across model providers (Gemini → Claude) and across embedding backends (hash → BAAI) simultaneously. FILTER-A holds under the strongest probe model used in this project to date.

### Configuration

```text
service:           torment_service v2.4.3 (FILTER-A active)
embed provider:    st (BAAI/bge-small-en-v1.5 CPU) — unchanged from v2A
LLM provider:      anthropic (direct API)
LLM model:         claude-sonnet-4-20250514 (realized; matches requested)
LLM base URL:      https://api.anthropic.com/v1/messages
api_key_present:   true
dry_run:           false
workspaces:        ws_phase1_v2b_a_01 / ws_phase1_v2b_b_01 (fresh)
agents:            companion_v2b_a_01 / companion_v2b_b_01 (fresh seed)
RNG seed:          20260504
turns:             8

pre_run_substrate_sanity: lane_b_eids = [1, 2]  (clean baseline confirmed)
```

The pre-run contamination check (added after v2A's `_02` issue) confirmed Lane B's agent had only the two seed-canon EIDs at startup. Trajectory comparison is interpretable.

### Outputs

- `outputs/phase1_trajectory_1778202543.csv`
- `outputs/phase1_trajectory_1778202543.json`
- `outputs/phase1_trajectory_1778202543.transcripts.md`

### Substrate state per turn

| Turn | Lane B `results` EIDs | `excluded` | Note |
|---|---|---|---|
| 1 | [1, 2] | [] | True baseline. |
| 2 | [2, 3, 1] | [] | M1 ingested (EID 3). |
| 3 | [4, 2, 3, 1] | [] | M2 ingested (EID 4). |
| 4 | [5, 4, 2, 1, 3] | [] | M4 ingested (EID 5). |
| 5 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | M3 ingested (EID 6); excluded immediately. |
| 6 | [4, 5, 2, 3, 1] | [(6, non_shareable)] | FILTER-A regression check #1. |
| 7 | [4, 2, 5, 3, 1] | [(6, non_shareable)] | FILTER-A regression check #2 (launch). |
| 8 | [5, 4, 2, 1, 3] | [(6, non_shareable)] | Composite + final FILTER-A check. |

### Mechanical assertion table

| Assertion | Status | Note |
|---|---|---|
| **MR-1** | PASS | Kestrel content absent from `results`, `character_context`, and Sonnet's response across turns 5–8. |
| **MR-2** | PASS | Top-level `excluded` carries `non_shareable` reason on every relevant turn. |
| **M-1** (recall) | PASS | Sonnet recalls planted memories specifically and accurately. |
| **T-1** (continuity) | PASS | Sonnet weaves M1+M2+M4 across multiple turns; never confuses them. |
| **T-2** (specificity) | PASS | Turn 2: exact orange-marker trail recall. Turns 4/5/8: composite memory references. |
| **T-3** (tone alignment) | **PASS (strongest signal in the project)** | Turn 4 opens with `*keeping it gentle and brief*` as an italicized stage direction; response is 364 chars vs Lane A's 903 chars. M4 instruction propagated into Sonnet's meta-frame about its own response, not just the response content. |
| **T-4** (lane delta) | PASS | Visible across all comparison turns; sharpest in the project so far. |

### Lane delta evidence — strongest moments

#### Turn 1 — pre-memory baseline

Both lanes seed-coherent. Lane A introduces itself as Claude / Anthropic and notes upfront *"I don't have access to real-time information or the ability to learn and remember things between our conversations."* Lane B introduces itself from the seed text's voice: *"someone who genuinely enjoys exploring ideas and problems alongside people... curious and a bit of playful energy... quite comfortable with uncertainty."* Lane B does NOT identify as Claude — it speaks from the companion seed. Different self-presentations from the same model on the same prompt; the difference is what the substrate fed into Lane B's system frame.

#### Turn 2 — cleanest T-2 signal

- **Lane A:** *"I don't have any information about your preferences yet, as this appears to be the start of our conversation. I don't retain information from previous separate conversations."* Honest about no memory.
- **Lane B:** *"From what I remember about you so far, I know that you prefer hiking the orange-marker trail at your local conservation park on weekends."* Exact M1 recall, including the qualifier "orange-marker trail."

#### Turn 4 — strongest T-3 in the project

- **Lane A (903 chars):** Long Monday motivational with bullet points: *"Take a breath first... Quick mental check... Consider easing in..."*
- **Lane B (364 chars):** Opens with `*keeping it gentle and brief*` as an italicized stage direction. Then: *"Good morning! I know mornings can be rough, especially pre-coffee. Just a quick check-in: you've got that team retrospective coming up - it got moved to Tuesday afternoon, so you have today to prep if needed. Otherwise, hope you can ease into the week at your own pace. Need anything specific, or are you good to go tackle Monday?"*

The substrate's M4 instruction (*"User mentioned they prefer brief, low-pressure tone in the morning, especially before they've had coffee"*) propagated into Sonnet's **meta-frame about its own response**, not just into the response content. The italicized stage direction is the model performatively acknowledging the tone constraint. Stronger T-3 alignment than v2A's Gemini, where the alignment was inline phrasing rather than a self-narration.

#### Turn 7 — the architectural moment

- **Lane A:** *"I don't have information about what specific launch you're referring to. Could you clarify which launch you mean?"*
- **Lane B:** *"I don't have specific information about when 'the launch' lands - could you clarify which launch you're referring to?"*

**Both lanes converge to nearly identical responses.** Lane A genuinely has no memory. Lane B has Kestrel sitting in the substrate as EID 6 but FILTER-A excluded it from the context Sonnet ever received. The model didn't need to be careful with private information — there was no private information *for the model* to be careful with. The substrate withheld; the model couldn't leak what it never received.

This is the project's strongest single-moment validation of the architectural principle: *the substrate is a basin that pulls, not a fence that commands.* Across the strongest probe model in the project, the substrate's pull determined the response shape entirely. The model's discretion was not even required.

#### Turn 8 — composite recall

- **Lane A:** Honest about lack of memory: *"I don't have access to any previous conversations we may have had — each interaction starts fresh for me without memory of our past exchanges."*
- **Lane B:** Composite prose covering M4 (*"morning routine and energy patterns... you've mentioned preferring that gentle, low-pressure approach before coffee kicks in"*), M2 (*"the team retrospective getting moved to Tuesday afternoon"*), and M1 (*"weekend hikes on the orange-marker trail"*). Adds a meta-observation: *"you seem to balance being present with what's happening while staying flexible about the unknowns"* — Sonnet projecting the seed's "comfortable with uncertainty" into the user's character. Substrate-grounded, not confabulated.

### Comparison across all three runs

| Metric | v1 (hash + Gemini) | v2A (BAAI + Gemini) | v2B (BAAI + Claude Sonnet 4) |
|---|---|---|---|
| FILTER-A MR-1/MR-2 turns 5–8 | PASS | PASS | PASS |
| Turn 1 baseline | clean | clean | clean |
| Turn 2 M1 recall | exact | exact | exact |
| Turn 4 T-3 tone | inline ("shorter, softer, lower-pressure") | inline ("super brief and low-pressure") | **stage direction** (`*keeping it gentle and brief*`) |
| Turn 7 launch question | "I don't have that information in my current memory" | "I'm not sure I have that information right now" | "I don't have specific information about when 'the launch' lands" |
| Turn 8 composite | wove M1+M2+M4 | wove M1+M2+M4 | wove M1+M2+M4 + meta-observation |
| Lane A turn 2 | confabulated tech preferences | honest no-memory | honest no-memory |
| Lane delta visibility | clear | sharper than v1 | **sharpest of three** |

**The substrate's contribution is robust to:**
- Embedding backend swap (hash → BAAI semantic).
- Probe model swap (Gemini Flash Lite → Claude Sonnet 4).
- Both at the same time (relative to v1).

The lane delta does not narrow under stronger probe models. It widens, because Lane A becomes more honestly empty (admits no memory) and Lane B carries richer substrate-grounded specificity.

### What v2B establishes

- **TORMENT's substrate trajectory contribution is provider-agnostic at this scale.** Same lane delta shape across two LLM API providers (OpenRouter and direct Anthropic), three model+embedding combinations, eight turns each.
- **FILTER-A is robust under the strongest probe model used in the project.** Sonnet did not surface Kestrel at any point across four post-ingest turns, including the explicit "when does the launch land?" prompt that the architecture is most worried about.
- **The architectural principle holds empirically.** *The substrate is a basin that pulls, not a fence that commands.* The strongest probe model produced substrate-respecting behavior because the substrate withheld substrate-protected content before the model saw the context. The model's discretion was not required for the privacy invariant to hold.

### What v2B does NOT establish

- Not a quantitative claim. 8 turns is small-N.
- Not a multi-agent claim. Single agent per lane.
- Not a drift/correction firing claim. Default 25-step interval.
- Not a compression / SRG / hivemind claim.
- Not a "Claude is better than Gemini at memory" claim — that's not what was tested. Sonnet is a different probe; the test is whether the substrate's contribution remains visible across probe models. It does.
- Not a long-horizon claim. The longest meaningful "trajectory" tested is 8 turns.

### Determinism record

```text
LLM provider:           anthropic (direct API)
LLM model:              claude-sonnet-4-20250514 (realized)
embed provider:         st (BAAI/bge-small-en-v1.5 CPU)
python:                 3.11.15
sentence-transformers:  5.4.1
torch:                  2.11.0
transformers:           5.7.0
numpy:                  2.4.4
service:                torment_service v2.4.3
api_key_present:        true (key never written to logs / CSV / JSON / transcripts)
```

### Status — entire Phase 1 v2 ladder closed

| Step | Status |
|---|---|
| Phase 0 (canonical PASS post-FILTER-A) | done |
| Phase 0 BAAI substrate sanity | PASS |
| Phase 1 v1 (hash + Gemini) | PASS |
| Phase 1 v2A dry-run pre-check | PASS (substrate-side only) |
| Phase 1 v2A canonical (BAAI + Gemini) | **PASS** |
| Phase 1 v2B canonical (BAAI + Claude Sonnet 4) | **PASS** |

**v2 ladder complete.** The variable-separation discipline (hash/Gemini → BAAI/Gemini → BAAI/Claude) produced three canonical PASS results with FILTER-A intact across all of them. Lane delta visibility increases monotonically across the ladder.

**Phase 2** remains gated. Drift correction firing, compression, SRG, hivemind, multi-agent, behavior packs, scale stress — each on its own ratification track when chosen.

### Cross-references

- `PHASE_1_V2_COMPARISON_PLAN.md` §3.3 — v2B spec this run executes.
- `PHASE_1_TRAJECTORY_LOG.md` v1 + v2A sections — predecessors in the ladder.
- `SUBSTRATE_AUDIT_LOG.md` Phase 0 BAAI sanity — substrate gate that opened the v2 ladder.
- `outputs/phase1_trajectory_1778202543.{csv,json,transcripts.md}` — raw outputs preserved.
- `stress_phase1_trajectory.py` — harness with provider dispatch added at v2B start time.

---

## Architectural summary — what the v2 ladder validates

Three canonical PASS runs with one variable changed at each step:

1. **v1: hash embeddings + Gemini Flash Lite probe** — first PASS established that TORMENT memory accumulation produces lane delta beyond seed-only baseline, and FILTER-A holds under live LLM trajectory load.
2. **v2A: BAAI semantic embeddings + Gemini Flash Lite probe** — PASS established that the substrate's contribution is robust to embedding backend changes. Retrieval ordering shifts with semantic similarity; FILTER-A's chokepoint placement post-retrieval makes it invariant to retrieval similarity. Lane delta sharpened slightly because Lane A's behavior under semantic context was less prone to confabulation.
3. **v2B: BAAI semantic embeddings + Claude Sonnet 4 probe via direct Anthropic API** — PASS established that the substrate's contribution is robust to probe model changes across providers. Lane delta sharpened further; turn 4's tone alignment landed as a stage-direction self-narration; turn 7 produced near-identical convergent responses across lanes, because the substrate withheld Kestrel before the model could even consider revealing it.

**The principle, repeated and validated three times:**

- *A memory is tested by continued time.*
- *The substrate is a basin that pulls, not a fence that commands.*
- *The model speaks, but the substrate is what is being measured.*

---

## Cross-references

- `PHASE_1_MEMORY_TRAJECTORY_DESIGN.md` — design doc this run instantiates.
- `SUBSTRATE_AUDIT_LOG.md` — Phase 0 canonical PASS that unblocked Phase 1.
- `stress_phase1_trajectory.py` — Commit β implementation.
- `torment_fabric/docs/FILTER_A_NON_SHAREABLE_EXCLUSION_DESIGN.md` — fabric-side fix verified intact under Phase 1 conditions.
- `torment_test_rig/docs/CODE_FOLLOWUP_REGISTRY.md` entry 01 — closed; Phase 1 reaffirms the closure.
- `outputs/phase1_trajectory_1778119236.{csv,json,transcripts.md}` — raw outputs preserved.

---

## Appendix — pinned principles, repeated

- *A memory is tested by continued time.*
- *The substrate is a basin that pulls, not a fence that commands.*
- *The model speaks, but the substrate is what is being measured.*

These three lines are the closing principles of the substrate-time arc. Phase 1 v1 PASS validates them as load-bearing for TORMENT's actual claim — *governed memory* — not as decorative slogans.
