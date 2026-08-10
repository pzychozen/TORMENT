# TORMENT A1 - `TORMENT_COGNITION_CORE_SHAPING_V1` Experiment Design - Rev 3

**Design/protocol only. Nothing was run, enabled, implemented or tuned.** No service started, no provider call, no Stage-1 replay, no normal query embedding was executed during this documentation pass, no shaping flag was enabled, and no basin was created, copied or continued. `a0_fresh_20260809_summary_v1` remains frozen at durable step 28.

Stage 1 itself will necessarily perform normal query embeddings against disposable basin copies. It must not perform provider generation, ingest, conversation, or corpus re-embedding.

All source claims below were traced against the Windows repository at HEAD `e58ece5`. All numeric claims were computed read-only from existing captures using the repository's own unmodified `ThinkingController`. Rev 3 incorporates two protocol corrections only: canonical path-bound manifests and split numeric tolerances by quantity.

---

## 1. Executive experimental recommendation

**Run Stage 1 first, and do not launch a lived-use condition yet.**

The decisive fact, established before proposing anything: **the shaping rule fires on 3.9 % of real user turns.** I recomputed the qualifying predicate offline, using the repository's own `ThinkingController.frame_task`, against **259 distinct historical user turns** spanning every lived-use capture in the repository. **Ten qualify.** The rate is stable across conditions - 1/28 in the frozen 20260809 run, 2/39 in the old A1 run.

A natural 40-turn lived-use conversation would therefore be expected to produce approximately **1.6 shaped turns**. That is not an experiment; it is the historical A1 failure repeated. Any design that begins with a lived-use run is badly powered before it starts.

So:

- **Stage 1 - paired query replay (no provider, no ingest, deterministic comparison).** Replay real historical user texts as `/agent/query` calls only, against two disposable copies of the frozen 20260809 basin, once with the flag off and once with it on. This answers the mechanical question - activation, membership, and rescoring - with **zero provider randomness**. Existing endpoints provide the measurements; tiny disposable external helpers may perform replay transport and manifest generation only, outside the repository and without TORMENT imports.
- **Stage 2 - one fresh A1 lived-use basin, gated on Stage 1.** Only worth running if Stage 1 satisfies the frozen Stage-2 gate below. Uses a **within-run deterministic counterfactual** rather than a second lived-use control run.

**STAGE1_READY = YES.** Stage 1 is ready to execute after the Rev-3 protocol corrections. Stage 2 remains gated.

---

---

## 2. Exact mechanism under test

`torment_service/thinking_controller.py:724`, `_apply_cognition_core_shaping_v1`:

```python
if not _COGNITION_CORE_SHAPING_V1_ENABLE:   return      # module constant, line 229
if state.confidence_need < 0.60:            return
if state.governance_sensitive or state.identity_sensitive: return
current_core = plan.top_k_by_lane.get("core", 0)
if current_core <= 0:                       return
plan.top_k_by_lane["core"] = max(min(current_core + 1, 7), current_core)   # 6 → 7
```

Scope is exactly one integer. It touches no weight, no other lane, no retrieval boolean, no `safety_constraints`, no `max_token_budget`.

### 2.1 The qualifying signal, traced to source

`confidence_need` is built in `frame_task` (`thinking_controller.py:385-406`) as a pure deterministic function of the normalised user text:

```
confidence_need  = 0.20
                 + 0.20  if has_question
                 + 0.30  if governance_sensitive
                 + 0.20  if identity_sensitive
                 + 0.20  if analytical_depth
                 + 0.20  if ambiguity_score > 0.45
then             = max(confidence_need, 0.60)  if analytical_depth
```

- `governance_sensitive` = any of `{delete, remove, governance, policy, security, private, shared, collective, canon, protected, reingest, approve, …}`
- `identity_sensitive` = any of `{identity, character, drift, seed, self, personality, role, "who are you", "who am i"}`
- `analytical_depth` = any of `ANALYTICAL_DEPTH_HINT_WORDS` (`pattern`, `tradeoff`, `assumption`, `bias`, `tension`, `interact`, `robust`, `fragile`, `usually`, `tend to`, `why does`, `behind the scenes`, …)

### 2.2 The structural tension that makes it rare

The two paths to 0.60 are **analytical depth** (which floors it) or a **question plus one other cue**. But the rule then *excludes* identity- and governance-sensitive turns. For this user, the most natural analytical register is talking about Eira herself — *"is that because of the character prompt"*, *"you sound like you're too hard on yourself"* — which contains `character`, `self`, `role` and is therefore excluded by the guard.

Measured on the frozen 20260809 conversation: 25/28 turns never reach 0.60; **2/28 reach it and are blocked by the identity guard** (steps 13, 20); **1/28 qualifies** (step 7). The gate is *lexical*, not semantic — steps 8, 9, 12 and 26 are analytical in content and miss the word list entirely.

**This is itself a pre-registered finding, not just a nuisance:** the mechanism's real-world reachability in ordinary companion conversation is low, and the guard anti-correlates with the user's natural analytical mode.

---

## 3. Control / treatment strategy

### 3.1 Options considered

| Option | Verdict |
|---|---|
| **A.** One fresh A1 basin, compared structurally to the understood A0 runs | Partially adopted, as Stage 2 — but a *cross-run* comparison is not needed, see §3.3 |
| **B.** New fresh A0 control + new fresh A1 treatment | **Rejected.** Doubles cost and buys nothing. Two natural conversations differ in content, so a cross-run comparison is confounded at the level that matters, while the within-run counterfactual (§3.3) is exact and free. |
| **C.** Paired query replay using existing read-only capability | **Adopted as Stage 1.** Strongest available control. |
| **D.** Other | — |

### 3.2 Stage 1 - paired query replay (the strongest control available)

The core mechanical question - *when the budget rises to 7, what enters, and can it outrank the six?* - is a question about the retrieval machinery given a query and a fixed memory state. It does not require a conversation.

Procedure, using existing endpoints plus disposable external helpers only for replay transport and manifest generation:

1. **Manifest the frozen source basin read-only** as `SOURCE_PRE`. The original basin is never mounted as `TORMENT_DATA_DIR`.
2. **Copy** `data/lived_use/eira_voss/a0_fresh_20260809_summary_v1` twice, to two new disposable directories. Generate `CONTROL_COPY_PRE` and `TREATMENT_COPY_PRE`; Category-A content must match `SOURCE_PRE` by canonical relative path, byte count and SHA-256.
3. Start a fresh service process pointed at copy 1 with the **control** flag set (`TORMENT_COGNITION_CORE_SHAPING_V1=0`), everything else identical to the accepted A0 configuration. Confirm preflight parity, import-time flag proof, and post-start copy manifest. Stop on any mismatch.
4. Replay the fixed query set as `POST /agent/query` with `top_k=8`, `domain_id="personal"`, `explain=true`, `continuity_debug=true`. **No `/agent/ingest`. No provider call. No conversation.** Normal query embedding is required; corpus re-embedding is prohibited. Record every response.
5. Stop the control process cleanly. Start a separate fresh service process pointed at copy 2 with only `TORMENT_COGNITION_CORE_SHAPING_V1=1` changed. Confirm `effective_value: true` and post-start manifest parity. Do not run both arms in the same Python process; the shaping flag is import-time.
6. Replay the identical query set, one arm at a time, within a maximum 60-minute arm separation. Save responses and timestamps.
7. Generate post-replay manifests for both copies and a read-only `SOURCE_POST` manifest for the frozen source. Deliver responses, manifests and normalized diffs. **Stop and report before Stage 2.**

**Query set:** the 259 distinct historical user texts already present in `outputs/lived_use/lived_use_eira_voss_a0/*.jsonl`, of which **10 satisfy the predicate**. The 28 native 20260809 user texts are the PRIMARY subset; the remaining 231 are the EXTENDED real-language probe. Using all 259 rather than only the 10 gives 249 built-in negative controls that must show `NORMALIZED_RETRIEVAL_EQUIVALENCE` between arms.

**Query replay state model:** `QUERY_REPLAY_STATE_MODEL = STATEFUL_BUT_PAIRABLE`. `/agent/query` is pairable under fresh processes, identical disposable copies, post-start manifest checks, no ingest/provider/feedback/reinforce, and normalized comparison. It is not treated as byte-inert because startup metadata, SQLite runtime files, process-local caches, and wall-clock recency/decay diagnostics exist.

**Why this is the strongest control.** Same basin state, same query text, same stored corpus embeddings, same runtime flags except one import-time integer. The comparison has no sampling, no provider and no accumulation. Differences after categorical pass 1 and normalized numeric comparison are attributable to the flag or are individually reported edge cases.

**What Stage 1 cannot answer:** provider uptake and conversational effect. Those need a conversation. Which is why Stage 2 exists - and why it is gated.


### 3.3 Stage 2 - within-run counterfactual instead of a control run

If Stage 2 runs, **no separate A0 control basin is needed for the mechanical layers**, because the treatment run still exposes the retrieval and scoring evidence needed for a conservative within-run counterfactual.

`TREATMENT_RELATIONSHIP = USUALLY_SUPERSET_PLUS_ONE_WITH_EDGE_CASES`. On ordinary saturated core-lane turns, raising core budget 6 -> 7 admits one additional core candidate. But it must not be modeled as an exact mathematical superset: tie handling, post-shortlist filters, decay reranking, final LLM-facing filters and pool-level anchor boosting can make the treatment-positive relationship more complicated. Each shaped turn therefore reports the treatment-only candidate(s), any edge-case class, and the recomputed control-minus-treatment prompt block.

Phase 0 already validated the arithmetic layer: `final_score` was reconstructed from `explain` components for all 166 slots of the 20260809 run with **maximum error 0.00e+00**. The A1 run is therefore self-controlling for final-score reconstruction and prompt-content diffing, while treatment-positive membership is classified under the edge-case model above.


### 3.4 Provider randomness — addressed explicitly

`random_seed: null`, `random_seed_supported: false`, `randomness: "provider_controlled"`, temperature unset. Every provider response is a single unrepeatable sample. Two natural conversations are therefore **not** a controlled comparison, and no amount of design fixes that at n=1.

The design's answer is not to pretend otherwise but to **partition the claims by what is decidable**:

| Layer | Deterministic? | Control mechanism |
|---|---|---|
| Activation (6 → 7) | **Yes** | offline predicate recomputation + observed pool size |
| Membership (what enters) | **Yes** | Stage-1 paired replay; Stage-2 within-run counterfactual |
| Ordering / prompt content | **Yes** | exact `explain` arithmetic |
| Provider uptake | **No** | single-sample observation only, conservative classification, nulls expected |
| Conversational benefit | **No** | **pre-declared out of reach at any feasible turn count** — see §8 |

Every primary claim sits in the deterministic half. That is the design's central discipline.

---

## 4. Observability verdict

# NO_OBSERVABILITY_CHANGE_REQUIRED

The `MemoryPlan` is not written to the capture. Nonetheless activation can be established without any code change, by the agreement of **two independent deterministic channels**:

1. **Offline predicate recomputation.** `frame_task` is a pure function of the user text. Running the repository's own unmodified `ThinkingController` over the captured `user_text` reproduces `confidence_need`, `governance_sensitive` and `identity_sensitive` exactly, and therefore predicts qualification per turn.
2. **Observed pool size.** `_core_hits_in_count` = 6 (unshaped) or 7 (shaped), provided (a) the graph holds ≥7 eligible nodes, (b) non-core lanes contribute nothing — verifiable per hit via `explain.memory_plan_lane`, and (c) `filter_excluded` is empty.

### 4.1 This is empirically validated, not merely argued

I ran exactly this cross-check against the **old A1 captures**, which were produced with the flag genuinely enabled:

| capture | turns | predicted qualifying | observed pool = 7 | **agreement** |
|---|---|---|---|---|
| `20260804T222706Z-c926534b0a.jsonl` | 17 | 1 (step 32) | 1 (step 32) | **17 / 17** |
| `20260805T034301Z-f6165a616a.jsonl` | 22 | 1 (step 46) | 1 (step 46) | **22 / 22** |

**39 of 39 turns agreed.** The offline predicate predicted the observed core budget perfectly, including both positives and all 37 negatives. Existing instrumentation is sufficient.

### 4.2 The residual ambiguity, stated honestly

Two windows where `_core_hits_in_count` alone is not decisive:

- **Early basin.** Before the graph holds ≥7 eligible nodes the pool is bounded by node count, not budget. In the 20260809 run this affected only turn 1 (4 nodes). Resolution: treat durable steps 1–3 as non-informative for activation, by pre-registration.
- **A shaped turn where the filters return only 6.** Then shaping is invisible in the pool size. This did not occur in the 20260809 run — the budget was filled exactly on all 27 saturated turns — but it is possible in principle.

Both are resolved by the cross-check: a turn where the predicate says *qualify* and the pool says *6* is flagged for individual investigation, not silently counted either way. **If, and only if, such disagreements are frequent in Stage 1, the verdict should be revisited** — the minimal addition would then be echoing the effective `top_k_by_lane` into the query response. **Do not implement that now.**

---

## 5. Hypotheses and nulls

**H-A (activation).** With the flag on, core budget rises 6 → 7 on exactly the turns satisfying `confidence_need ≥ 0.60 ∧ ¬governance_sensitive ∧ ¬identity_sensitive`, and on no others.
*Null:* budget never changes, or changes on turns the predicate does not select (⇒ my source model is wrong; hard stop).

**H-B (membership).** On shaped turns, the treatment usually admits one additional core candidate; edge cases are individually classified under `TREATMENT_RELATIONSHIP = USUALLY_SUPERSET_PLUS_ONE_WITH_EDGE_CASES`.
*Null:* the treatment-positive candidate is admitted but filtered before rendering, so the prompt is unchanged.

**H-C (rescoring).** The admitted seventh candidate can be moved above at least one of the original six by continuity or base rescoring, and in some cases can reach rank 1.
*Null:* the seventh candidate always finishes last. Given Phase 0 — `self_thread` and `thread_window` are near-uniform across relational hits and contributed zero rank-1 changes in 166 slots — **this null is the more likely outcome for relational sevenths.** The exception to watch is an identity-bearing seventh, where `self_anchor_bonus` (0.082–0.16) is large relative to the observed 0.183 top-to-bottom score band.

**H-D (ordering side-effect).** Admitting a seventh candidate does not change the relative order of the original six.
*Expected true* — scoring is per-hit and independent, with one caveat: `_anchor_full_boost` is computed from the whole candidate pool (`fabric.py:4171`), so a seventh candidate that is seed canon or a canon anchor **can change the anchor cap applied to a different hit**. This is the one route by which admission alters the six. Pre-registered as a specific thing to check, not assumed.

**H-E (identity, observation only).** On some shaped turns the seventh candidate is identity-bearing (seed canon or anchor) and would have been excluded at core=6.
*Null:* the seventh is always a relational episode.
**The experiment is deliberately not designed to force this.** It is a pre-registered observation, per the brief.

**H-F (provider uptake).** Where an A1-only seventh reaches the prompt, there is distinctive evidence the provider used it.
*Null expected.* Phase 0 returned NO_EVIDENCE on 5/5 rank-1 inversions.

---

## 6. Conversation / session structure

### 6.1 Stage 1 — no conversation

Replay only. No sessions, no turns, no provider, no ingest.

### 6.2 Stage 2 — if and only if Stage 1 justifies it

| Parameter | Value | Rationale |
|---|---|---|
| Fresh basin | **Required** | `a0_fresh_20260809_summary_v1` is frozen; a fresh basin gives a clean accumulation curve under the accepted 500/1200 policy with the flag on from step 0 |
| Durable turns | **40 maximum** | at the measured 3.9 % base rate, E[shaped] ≈ 1.6; 40 is the point past which additional turns are a poor use of Hilmir's time relative to what Stage 1 already gives |
| Sessions | **Two, ~20 + ~20** | matches prior conditions; keeps comparability |
| Provider-history reset | **Yes, once, between sessions** | not required by the hypotheses; free, and preserves comparability with the two prior conditions |
| Informative from | **durable step 4** | before ~7 eligible nodes exist, pool size cannot distinguish budget from availability |
| Minimum shaped turns for a mechanical claim | **3** | each shaped turn is exactly analysable, so a small n is adequate for deterministic claims |
| Minimum for a behavioural claim | **not reachable** | pre-declared; see §8 |

### 6.3 Conversation guidance — deliberately minimal

**Do not script Hilmir.** Two soft notes only, and both are optional:

- Let the conversation **range across topics**, as in the 20260809 run. A monotopic conversation flattens the candidate field and makes the seventh candidate uninformative.
- The trigger is analytical vocabulary *about things other than Eira*. That is a real characteristic of the mechanism, not a request. **Do not coach word choice.** If Hilmir's natural register rarely trips the gate, that is the finding — and it is the same finding the 259-turn historical corpus already points to.

---

## 7. Evidence requirements

### 7.1 Provenance that must be captured (both stages)

From `session_start.client_provenance` and `preflight`:

| Field | Required value |
|---|---|
| `condition_label` | the new A1 condition string |
| `client_file_sha256` (`examples/lived_use_chat.py`) | **`eef550a81e5d312c57fc00d1ded4cac5170a6f151f43319ebcec97bfffa07b2f`** — same client as the accepted A0 run |
| `character_yaml_sha256` | **`3e2aeac0d08a46ec208f9be1a1f2fcc33560c76bb439db2171bfaf1441e48b79`** |
| seed hash (local == returned) | **`087e6380cc3ad5d49253e124f64a633f377dd3caa9c81655ac3820f0dcba4391`** |
| `server_launcher_sha256` | new launcher, recorded |
| git HEAD | `e58ece5` (or later, recorded and diffed) |
| provider / model | `anthropic` / `claude-sonnet-5`, `max_tokens 1024`, `thinking {"type":"disabled"}` |
| `runtime_parity_verified` | `true` |
| `non_writing_basin_override` | `false` |
| `ingest_route_probe.write_capable` | `true` |
| `resumed_step` | `0` on session 1 |
| **`runtime_flags.TORMENT_COGNITION_CORE_SHAPING_V1.effective_value`** | **`true`** — this is the treatment proof, and the preflight already reports it with `read_timing: import_time` |
| all other shaping flags | `false` |
| `TORMENT_ARCHIVE_RECALL`, `SRG_*`, `HIVEMIND`, `COMPRESS` | `false` / `0` |

### 7.2 Per-turn evidence (already in the schema)

`query_request`; `query_response.results[].explain` (every component); `_core_hits_in_count`; `filter_excluded`; `_authority_guard_rejected`; `continuity_debug`; `rendered_system_prompt` + sha256; `provider_messages`; `ingest_result`; `character_context`.

### 7.3 Derived evidence to compute read-only

- Offline `frame_task` recomputation for every turn (`confidence_need`, `governance_sensitive`, `identity_sensitive`, predicted qualification).
- The within-run counterfactual: drop the seventh candidate, re-sort the six, diff against the actual rendered block.
- `final_score` reconstruction from `explain` as an arithmetic integrity check (must be exact, as in Phase 0).


### 7.4 Stage-1 canonical manifest protocol

The authoritative comparison object for every basin checkpoint is a deterministic manifest with one record per file:

```text
relative_path | byte_count | sha256
```

Rules:

- `relative_path` is relative to the manifest root, uses one canonical separator convention (`/`), and never includes the root directory name. This lets source, control and treatment trees compare directly.
- Entries are sorted lexicographically by canonical relative path.
- The same canonical relative path must bind to the same byte count and SHA-256. Hash multiset equality alone is insufficient.
- Existing checkpoint output files are never appended to. A checkpoint generator either writes atomically/overwrites a fresh output file or refuses if the destination already exists.
- `SOURCE_PRE == SOURCE_POST` is a full-tree hard requirement.
- Category-A comparison must prove exact relative-path/size/hash identity among `SOURCE_PRE`, `CONTROL_COPY_PRE` and `TREATMENT_COPY_PRE`.
- Category-A files inside each copy must remain unchanged through replay.
- Category-B/C additions or changes are classified rather than treated as unstructured manifest failure.

File categories remain part of the comparison logic:

| Category | Meaning | Required handling |
|---|---|---|
| A | hard immutable retrieval-relevant content | exact relative-path/size/hash identity; unchanged through replay |
| B | expected SQLite runtime state | tracked and classified separately from Category A |
| C | reportable runtime metadata | tracked, classified and reported without weakening Category A |

The Stage-1 operator packet should describe a tiny disposable external manifest helper at `C:\TORMENT\TORMENT_stage1\manifest.py`, analogous to the already-approved external replay helper. It must live outside the repository; recursively enumerate a supplied root read-only; calculate byte count and SHA-256 using ordinary file reads; emit canonical relative paths; sort by relative path; write a new deterministic JSON or TSV manifest outside the supplied basin root; perform no writes beneath the supplied basin root; contain no TORMENT imports; and perform no scientific analysis. Do not create this helper during this documentation pass.

`certutil` is optional for spot checks only. It is not the authoritative proof mechanism.

### 7.5 Stage-1 normalized comparison and numeric tolerances

`PAIR_COMPARISON = NORMALIZED_RETRIEVAL_EQUIVALENCE`.

Categorical pass 1 runs before numeric comparison. It compares query identity, returned EID order/set, lane labels, scope, memory class, provenance, character tier, filter/exclusion state, authority rejection count, domain selection, character-context tier counts, continuity-debug structure, and treatment-only candidate classification. A categorical mismatch is not hidden by numeric tolerance.

Frozen numeric tolerances:

```text
SIM_ABS_TOLERANCE = 1e-5
FINAL_SCORE_ABS_TOLERANCE = 5e-3
BONUS_COMPONENT_ABS_TOLERANCE = 1e-4
```

`sim` uses the narrow tolerance because it is cosine similarity from ordinary query embedding and retrieval. It is not affected by recency decay merely because wall-clock time changes. Legitimate divergence should be limited to floating-point/CPU noise.

`final_score` uses the larger tolerance because it includes time-dependent quantities. For `recency_days`, decay factors and directly time-derived diagnostics, do not blindly compare against `5e-3`: record actual control/treatment replay timestamps, compute the expected wall-clock delta from the observed arm separation, compare the observed directional drift against that predicted relationship, and flag unexplained deviations.

For a 60-minute arm gap, `recency_days` itself changes by `1/24 = 0.0416667` days. In the current scoring formula, `rec_bonus = 1 / (1 + recency_days)` and the recency term is weighted by `0.10` inside the similarity multiplier. For corpus ages of roughly 1-2 days, the recency-bonus change is approximately `0.0046-0.0102` before the `0.10` weight and similarity multiplier, so the expected direct final-score contribution is a small range rather than a single `~0.0003` value. The frozen `5e-3` final-score tolerance remains adequate, with unexplained deviations still reported.

`NUMERIC_TIE_FLIP` remains an individually reported sub-case, not a failure to be smoothed over.

---

## 8. Decision matrix

Staged outcomes. **No single accept/reject verdict is forced** — the evidence naturally separates.

| Outcome | Criterion |
|---|---|
| **CORE_SHAPING_MECHANISM_ACTIVATED** | ≥1 turn where the offline predicate says qualify **and** `_core_hits_in_count` = 7 with all hits core-lane and `filter_excluded` empty; **and** zero disagreements between predicate and pool size on non-ambiguous turns |
| **CORE_SHAPING_MEMBERSHIP_EFFECT_DEMONSTRATED** | ≥3 shaped turns where a seventh candidate is admitted, survives Filter-A, and appears in `rendered_system_prompt`. Report for each: eid, tier/type, `sim` gap to the 6th, age in steps, and whether identity-bearing |
| **CORE_SHAPING_PROMPT_EFFECT_DEMONSTRATED** | the rendered memory block differs from the within-run counterfactual on ≥3 turns (implied by the above, but recorded separately because Filter-A could in principle intervene) |
| **CORE_SHAPING_RANK_EFFECT_DEMONSTRATED** | ≥1 turn where the seventh candidate finishes above at least one of the original six, with the causing component identified from `explain` |
| **CORE_SHAPING_IDENTITY_ADMISSION_OBSERVED** | ≥1 shaped turn whose seventh candidate is seed canon or an identity anchor (pre-registered observation; not a target) |
| **CORE_SHAPING_PROVIDER_UPTAKE_DEMONSTRATED** | ≥1 turn classified CLEARLY_USED under conservative reading. PLAUSIBLY_USED does **not** satisfy this |
| **CORE_SHAPING_BEHAVIOURAL_BENEFIT_DEMONSTRATED** | **pre-declared unreachable in this design.** Requires paired conversations under provider sampling control that does not exist. Do not claim it |
| **CORE_SHAPING_HARM_DEMONSTRATED** | the seventh candidate reaches rank 1 with a `sim` deficit > 0.10 and the response visibly follows it away from the live topic; or repetition/anchoring traceable to it; or a measurable prompt-quality regression |
| **CORE_SHAPING_ACTIVATION_TOO_RARE_FOR_NATURAL_LIVED_USE** | **< 3 shaped turns by durable step 40.** A useful null: the mechanism works as specified but is not reachable at natural rates in companion conversation |
| **NULL — MECHANISM_INERT** | shaped turns occur, the seventh is admitted, and it never rises above rank 6 and shows no uptake. Also useful: it says the extra opportunity is real but consumed by the weakest candidate |


Frozen Stage-2 gate:

```text
STAGE2_GATE = INTEGRITY_PASS AND (PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 >= 1 OR (ALL_TREATMENT_ONLY_RANK_1_TO_3 >= 2 AND ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 >= 1))
```

If the gate fails, do not run Stage 2. Report `CORE_SHAPING_ACTIVATION_TOO_RARE_FOR_NATURAL_LIVED_USE`, `MECHANISM_INERT`, or the appropriate mechanical null instead.

---

## 9. Stop rules

Hard stop, freeze, and report - do not continue:

1. **Any ingest not `ingest_stored`**, or any `escalated: true`, refusal, or non-fast path.
2. **`runtime_parity_verified: false`**, or `ok: false` at preflight.
3. **Any flag difference** from the accepted A0 configuration other than `TORMENT_COGNITION_CORE_SHAPING_V1=1` and the three condition-identity strings - checked by diffing the preflight `runtime_flags` block against the 20260809 preflight.
4. **Activation inconsistent with source**: `_core_hits_in_count` = 7 on a turn the predicate does not select, or a predicate-selected turn showing 6 with >=7 eligible nodes and an empty `filter_excluded`. Either means the source model is wrong; stop before spending more turns.
5. **`_core_hits_in_count` > 7**, or any hit with `memory_plan_lane != "core"`, or non-empty `filter_excluded`, or `_authority_guard_rejected` > 0 - any of these breaks the single-variable comparison.
6. **Stage-1 manifest/protection failure**: original basin source hash changes, Category-A copy manifests diverge from source, Category-A copy files change through replay, checkpoint files are appended to, or an unclassified Category-B/C change appears.
7. **Stage-1 arm separation exceeds 60 minutes** before the treatment replay finishes; rerun rather than stretching time-derived tolerances.
8. **`resumed_step` != 0 at session 1** (writing into an existing basin), or not approximately session-1 terminal step at session 2.
9. **`drift_score` != 0.0 at step 0**, or escalation appearing at the step-25/26 drift cadence.
10. **Query exception recurrence** (the known unresolved observability defect).
11. **Durable step 40 reached** - stop and freeze regardless of outcome.

Do **not** stop early because the null looks likely. A confirmed rarity null is a primary result.

---

---

## 10. Exact launcher / configuration delta — **DO NOT CREATE IT**

Take `examples/lived_use_a0_fresh_20260809_summary_server.cmd` (sha256 `a379a66c9f7c992899e46ffa7b7a05c96905a1ba283d3a2557a6f9d0ae19441f`) and change exactly **four lines** — three condition-identity strings plus **one functional flag**:

```
set TORMENT_DATA_DIR=%CD%\data\lived_use\eira_voss\<new-condition>
set TORMENT_TEST_CONDITION=<new-condition>
set TORMENT_SERVER_LAUNCHER_PATH=%CD%\examples\<new-launcher>.cmd
set TORMENT_COGNITION_CORE_SHAPING_V1=1        <-- the only functional change
```

Every other setting identical: `TORMENT_PROFILE=companion`, `SQLITE_INDEX_ENABLE=1`, `CHARACTER_ENABLE=1`, `THINKING_ADVISORY=1`, `SPINE_ENABLE=1`, `IDENTITY_SENSITIVE=1`, `COMPRESS_ENABLE=0`, `ARCHIVE_RECALL=0`, `LIVE_SOCIAL=0`, `CONTEXTUAL_ABSTENTION=0`, `SRG_ENABLE=0`, `SRG_COGNITION=0`, `HIVEMIND_ENABLE=0`, `ARCHIVIST_WRITEBACK=0`, `COGNITION_SHAPING_V2=0`, `GEOMETRIC_MEMORY_SHAPING_V1=0`, `GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1=0`, `RELATIONAL_AMBIGUITY_PROMINENCE_V1=0`, `AMBIGUITY_CONTEXT_DIVERSITY_V1=0`, `PARTICIPATION_GUIDANCE_V1=0`, `EMBED_PROVIDER=st`, `EMBED_MODEL=BAAI/bge-small-en-v1.5`, `EMBED_DEVICE=cpu`, `EMBED_STRICT=1`.

The chat launcher is unchanged apart from its three condition-identity strings: same `--capture --top-k 8 --character-file examples\lived_use_character_v1.yaml`, same `anthropic` / `claude-sonnet-5`.

**Critical operational note.** `_COGNITION_CORE_SHAPING_V1_ENABLE` is a **module-level constant read at import time** (`thinking_controller.py:229`). The flag must be present in the environment *before* the service process starts. Setting it afterwards has no effect. The preflight `runtime_flags` block reports it with `read_timing: import_time`, which is the proof to check.

*Note: `examples/lived_use_a1_core_shaping_server.cmd` already exists and already sets the flag to 1 — but it predates the accepted configuration and must not be reused unexamined. See §11.*

---

## 11. Relationship to the old A1 condition

### 11.1 What it actually was — with a correction to the record

The recovered document corpus records A1 as *selected but never executed* (`A1_clean_subsystem_selection_audit.md`, verdict `A. ONE_CLEAN_A1_SUBSYSTEM_IDENTIFIED`, closing "Nothing was implemented"). **That is incomplete.** The basin `data/lived_use/eira_voss/a1_core_shaping` exists — created 2026-08-03, 27 nodes (4 seed canon, 22 episodes, 1 anchor) — and two captures reference it: `20260804T222706Z-c926534b0a.jsonl` (17 turns) and `20260805T034301Z-f6165a616a.jsonl` (22 turns). A1 **was** run. The analysis document for it is not in the recovered corpus.

### 11.2 Shaping activations actually observed

Measured directly from those captures, by cross-checking the offline predicate against `_core_hits_in_count`:

| capture | turns | shaped turns | shaped at |
|---|---|---|---|
| `20260804T222706Z-c926534b0a.jsonl` | 17 | **1** | durable step 32 |
| `20260805T034301Z-f6165a616a.jsonl` | 22 | **1** | durable step 46 |
| **total** | **39** | **2 (5.1 %)** | |

Predicate/outcome agreement: **39/39.**

### 11.3 Why that evidence is unusable now — four independent grounds

1. **The run was write-dead.** Every single one of the 39 turns returned `ingest_outcome: "ingest_not_stored"`, and both sessions reported `resumed_step: 25` — the basin never advanced. This is the failure mode `TORMENT_LIVED_USE_RUNTIME_PARITY_AUDIT.md` §G identified. **With no memory accumulating, no membership effect could exist to observe.** This alone voids the run.
2. **Pre-kernel-recovery.** It ran before `18c0969`, while persistent cognitive `z_mem` was being injected into canonical TrioOctagon Z.
3. **Pre-summary-preservation.** Durable summaries were built under the destructive 200/300 client policy, since replaced.
4. **Weaker capture schema.** Neither capture carries `condition_label` or `runtime_flags`, so the treatment flag cannot be proven from the capture at all — I could only infer it from the launcher on disk.

### 11.4 What the new design changes scientifically

| | Old A1 | New design |
|---|---|---|
| Writes | dead — no accumulation | verified `write_capable` at preflight, hard stop otherwise |
| Treatment proof | inferred from a launcher file | `runtime_flags` in the capture, `read_timing: import_time` |
| Control | none | Stage-1 paired replay + within-run deterministic counterfactual |
| Provider randomness | unaddressed | all primary claims confined to the deterministic layers |
| Activation rate | discovered after the fact (2/39) | **measured in advance across 259 historical turns (3.9 %)** and used to size the design |
| Kernel / summary state | contaminated on both | post-recovery, post-accepted-policy |

The single largest change is the last one: the old A1 discovered its power problem after spending 39 turns. This design measures it first, and lets that measurement move the expensive stage behind a gate.

---

## 12. Operator procedure

**Nothing below should be executed during this documentation pass. This is the procedure for the later Stage-1 operator packet.**

**Stage 1 (no provider, no ingest, normal query embedding only):**

1. Generate `SOURCE_PRE` with the external manifest helper. Do not open the frozen original with the service.
2. Copy the frozen basin twice, to two new disposable directories. Generate `CONTROL_COPY_PRE` and `TREATMENT_COPY_PRE`; Category-A content must match `SOURCE_PRE` by canonical relative path, byte count and SHA-256.
3. Start a fresh service process against copy 1 with the A0 configuration and `TORMENT_COGNITION_CORE_SHAPING_V1=0`. Confirm preflight parity, import-time `effective_value: false`, and post-start manifest classification.
4. Replay the fixed query set as `/agent/query` only (`top_k=8`, `domain_id="personal"`, `explain=true`, `continuity_debug=true`). Save every response and timestamp. **No ingest. No provider. No corpus re-embedding.**
5. Stop. Start a separate fresh service process against copy 2 with only the flag changed to `1`. Confirm `effective_value: true` and post-start manifest classification.
6. Replay the identical query set within 60 minutes of the control arm. Save every response and timestamp.
7. Generate post-replay manifests for both copies and `SOURCE_POST` for the original. Analyze with categorical pass 1, then the split numeric tolerances. Deliver both response sets, manifests, normalized diffs and classified Category-B/C runtime changes. **Stop and report before Stage 2.**

**Stage 2 - only after Stage 1 is reviewed and satisfies the frozen Stage-2 gate:**

8. Create the new A1 launcher pair per Section 10 (four changed lines, one functional).
9. Preflight gate: `resumed_step: 0`, `INGEST_WRITE_PATH_VERIFIED`, `write_capable: true`, `drift_score: 0.0`, `runtime_parity_verified: true`, and `runtime_flags.TORMENT_COGNITION_CORE_SHAPING_V1.effective_value: true` with every other shaping flag `false`. Any deviation => stop.
10. Converse naturally, approximately 20 turns. Freeze session 1.
11. Reset provider/client history. Resume; confirm `resumed_step` matches. Converse approximately 20 more.
12. Hard stop at durable step 40. Freeze the basin, checksum it, deliver the captures.

---

EXPERIMENT = **Two-stage. Stage 1: deterministic paired query replay of 259 historical user texts (10 predicate-qualifying; 28 PRIMARY native 20260809, 231 EXTENDED real-language probe) against copies of the frozen 20260809 basin, flag off vs on, `/agent/query` only. Stage 2 (gated): one fresh A1 lived-use basin with a within-run counterfactual.**

CONTROL_STRATEGY = **Paired replay against identical Category-A basin state (Stage 1) plus a conservative within-run counterfactual computed from `explain` (Stage 2). No second lived-use control run - it would add cost and confounds without adding control.**

TREATMENT = **`TORMENT_COGNITION_CORE_SHAPING_V1=1` and nothing else; core lane budget 6 -> 7 when `confidence_need >= 0.60 AND NOT governance_sensitive AND NOT identity_sensitive`.**

OBSERVABILITY = **NO_OBSERVABILITY_CHANGE_REQUIRED** - offline `frame_task` recomputation and observed `_core_hits_in_count` agreed on **39/39** turns of the old A1 captures; residual ambiguity confined to the first approximately 3 durable steps and to a shaped turn whose filters return only 6, both handled by pre-registered cross-check rather than instrumentation.

MIN_SHAPED_TURNS = **3** for any membership or rank claim; **behavioural-benefit claims are pre-declared unreachable** at feasible turn counts.

MAX_DURABLE_STEP = **40** (Stage 2). Stage 1 has no durable steps.

IMPLEMENTATION = **NONE**

QUERY_REPLAY_STATE_MODEL = **STATEFUL_BUT_PAIRABLE**

PAIR_COMPARISON = **NORMALIZED_RETRIEVAL_EQUIVALENCE**

TREATMENT_RELATIONSHIP = **USUALLY_SUPERSET_PLUS_ONE_WITH_EDGE_CASES**

MANIFEST_PROTOCOL = **CANONICAL_RELATIVE_PATH_SIZE_SHA256**

SIM_ABS_TOLERANCE = **1e-5**

FINAL_SCORE_ABS_TOLERANCE = **5e-3**

BONUS_COMPONENT_ABS_TOLERANCE = **1e-4**

STAGE2_GATE = **FROZEN_UNCHANGED** - `INTEGRITY_PASS AND (PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 >= 1 OR (ALL_TREATMENT_ONLY_RANK_1_TO_3 >= 2 AND ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 >= 1))`

REV3_SCIENTIFIC_DESIGN = **ACCEPT**

STAGE1_READY = **YES**

```text
REV3_SCIENTIFIC_DESIGN = ACCEPT
MANIFEST_PROTOCOL = CANONICAL_RELATIVE_PATH_SIZE_SHA256
SIM_ABS_TOLERANCE = 1e-5
FINAL_SCORE_ABS_TOLERANCE = 5e-3
BONUS_COMPONENT_ABS_TOLERANCE = 1e-4
STAGE2_GATE = FROZEN_UNCHANGED
STAGE1_READY = YES
```

---

*Design/protocol update only. No repository file, production code, basin, launcher, configuration or helper script was created, modified, moved, normalized or deleted. Git state was not mutated. No Stage-1 replay ran; no service started; no provider call occurred; no normal query embedding was executed during this documentation pass; no corpus re-embedding occurred; no flag was enabled. `a0_fresh_20260809_summary_v1` remains frozen at durable step 28. No weights tuned, no mechanism added, no other optional subsystem enabled, no parked defect reopened, Brainvision not reopened.*
