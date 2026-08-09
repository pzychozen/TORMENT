# TORMENT A0 Recovered Lived-Use Checkpoint — 2026-08-09

Scientific checkpoint for the recovered Fresh A0 companion condition.
Frozen at durable step 28. Source: the final bounded analysis of both session captures; this document records results rather than re-deriving them.

---

## 1. Experiment identity

| | |
|---|---|
| Condition | `a0_fresh_20260808_v1` — **FROZEN** at durable step 28 |
| Repository HEAD | `7a8efaf4518a7db36221e4a6581919c1e94f9ec8` (identical to `origin/main`) |
| Runtime basin | `data/lived_use/eira_voss/a0_fresh_20260808_v1` |
| Session A capture | `outputs/lived_use/lived_use_eira_voss_a0/20260808T202235Z-ab5614f1e0.jsonl` |
| Session B capture | `outputs/lived_use/lived_use_eira_voss_a0/20260808T215442Z-d2dfff5cf5.jsonl` |
| Launchers | `examples/lived_use_a0_fresh_20260808_server.cmd`, `examples/lived_use_a0_fresh_20260808_chat.cmd` |
| Embedding backend | `st` / `BAAI/bge-small-en-v1.5` / CPU / dim 384 / strict |
| Configuration | A0 baseline — all seven MemoryPlan shaping flags `0`, compression / SRG / hivemind / archive-recall / live-social / contextual-abstention off |

**Relationship to the kernel recovery.** The canonical TrioOctagon kernel had already been independently restored to oracle parity before this condition ran (`18c0969`, `fix(kernel): restore canonical TrioOctagon Z semantics`). This checkpoint does **not** re-establish that parity and makes no claim about it. What A0 adds is different and complementary: it establishes that the full companion runtime built on the recovered foundation behaves coherently in lived use — durable writes, cross-session retrieval, and the character cadence all functioning together over 28 steps and a process restart.

---

## 2. Two-session timeline

| step range | eid range | session | notes |
|---|---|---|---|
| 1 | 5 | A | EID 6 identity anchor emitted (`motif_personal_0001`, members `[1,2,3,4,5]`) |
| 2–4 | 7–9 | A | garden / backyard thread begins |
| 5 | 10 | A | EID 11 identity anchor emitted (`motif_personal_0003`, members `[8,9,10]`) |
| 6–16 | 12–22 | A | 11 clean query → generate → ingest cycles |
| — | — | A | **3 query failures**, `ingest_call_count 0`, no durable state change |
| *restart* | — | — | preflight resumed at step 16; `write_capable true`; `runtime_parity_verified true` |
| 17 | 23 | B | cross-session continuity turn (§4) |
| 18–24 | 24–30 | B | 7 clean cycles |
| **25** | **31** | B | **first drift cadence fires** (§5) |
| 26–28 | 32–34 | B | post-cadence writes; guidance and alignment line now in prompt |

**Totals:** 28 / 28 successful durable ingests, 0 failed ingests, 0 Spine escalations, all writes `path=fast` / `decision_code=fast_allowed`. Final basin: 34 nodes — 4 `seed_canon`, 2 `identity_anchor`, 28 `episode`.

---

## 3. Why the provider-history restart matters

The client's conversation history (`self.history`) is caller-side state. It is not persisted and is not reconstructed on restart. Durable memory lives entirely in the TORMENT basin and is reached only through `/agent/query`.

Starting Session B in a new client process therefore produced a clean separation that a single continuous session cannot: at Session B turn 1 the provider received **one** message — the user's current line — and nothing else. Any prior-session content appearing in the model's reply had to arrive through retrieval, because there was no other channel for it.

This is the property that makes §4 a measurement rather than an impression.

---

## 4. Cross-session continuity result

**Session B, turn 1 (durable step 17).**

Provider conversation state: `provider_messages n=1, roles: ['user']`.

User message, in full:

> `someone is pooping in my garden again...`

That message names no remedy, no animal, and no prior exchange.

Retrieved memories supplied to the system prompt (top four, all written during Session A):

| rank | score | eid | content |
|---|---|---|---|
| 1 | 1.35 | 8 | the original flower-bed report and Eira's "not folklore — forensics" reply listing cats / raccoons / opossums |
| 2 | 1.29 | 11 | derived anchor containing both the sprinkler list and the chicken-wire exchange |
| 3 | 1.15 | 9 | `what does that deterrant look like` → "Motion-activated sprinkler (like a Scarecrow…)" |
| 4 | 1.14 | 10 | `chicken wire sound like a good solution or a motion sensor water sprinkler…` |

Model reply:

> "Same culprit or a new offender? Because if **the sprinkler and chicken wire situation** never actually happened — just stayed at the planning stage — then, respectfully, of course they're back. A deterrent you talk about but don't install is just a suggestion box for wildlife."

**The demonstrated claim, stated precisely:** a fresh provider conversation containing only the current user message was supplied specific prior-session information through TORMENT retrieval, and the model successfully used that information to continue the earlier conversational thread.

Two details make the result stronger than simple echo. The specifics ("sprinkler", "chicken wire") exist only in the retrieved text — not in the user's message, not in the seed, not in provider history. And the reply *reasons over* the retrieved content: during Session A the user said chicken wire "sound like a good solution" but never said he installed it, so "just stayed at the planning stage" is a correct inference from what the memory actually records.

This is content continuity, distinct from the tone-and-manner continuity that `[Core identity]` would supply on its own.

**Not claimed:** no assertion is made here about consciousness, about memory being autonomous or self-directed, or about canonical Z semantics causing this recall. The retrieval path is ordinary embedding similarity plus the documented scoring and continuity terms.

---

## 5. Step-25 drift cadence result

First valid lived-use execution of the `TORMENT_CHARACTER_DRIFT_CHECK_EVERY = 25` cadence.

Persisted `CharacterState` after step 25:

```json
{
  "drift_score": 0.8817107677459717,
  "drift_direction": "stable",
  "distance_to_seed": 0.02957230806350708,
  "drift_history": [[25, 0.8817107677459717]],
  "relational_count": 25,
  "core_count": 0,
  "situational_count": 0,
  "seed_basin_role": "plateau",
  "seed_basin_phi": 0.0,
  "seed_basin_kappa": 0.0,
  "seed_basin_tension": 0.0
}
```

**Arithmetic verified.** `drift_score = 1.0 − 2.0 × (0.02957230806350708 / 0.5) = 0.8817107677459717` — exact. Under the corrected signed convention (positive = close to seed), a distance of 0.0296 correctly yields a strongly positive score. `relational_count = 25` matches the node census exactly: 31 nodes at step 25, minus 4 `seed_canon` (skipped by `measure_drift`) and 2 `identity_anchor` (tier `derived_identity`). `core_count = 0` is correct by design for the same reason.

**No corrective action fired.** Gravity correction is gated on `drift_score > −threshold` and did not apply; the node census contains no `drift_correction` memory. The drift reflex did not fire, and could not have: `drift_reflex_callback` is never assigned in the service and defaults to `None`.

**The next query observed the updated state.** Step 25's own query ran before its ingest and still saw the pre-cadence values; step 26's query saw `0.8817107677459717` and `relational_count 25`.

**Prompt delta at step 26,** verbatim:

```
[Guidance]
  - Character is well-centered. Safe to explore new directions.
...
[Alignment: +0.88]
```

This is the first run in which the guidance line and the drift line agree. Earlier (invalid) conditions rendered "well-centered" alongside a raw `[Drift: +0.92]`; the signed-semantics and alignment-label repairs are confirmed working in lived use.

**Caveat on `drift_direction`.** Direction is computed from the delta against `previous_state.distance_to_seed`, which on the first cadence is the activation-bridge initial `0.0`. The observed delta of `+0.0296` fell `0.0004` below the `away_seed` threshold of `0.03`. `drift_direction` should therefore be treated as uninformative on the first cadence of any basin; it becomes meaningful only once a real prior measurement exists.

---

## 6. Mechanically proven

Established directly from capture fields, basin files, and source, with arithmetic reproduced independently:

- Durable memory formation works end to end: 28 / 28 ingests stored, all fast-path, zero escalations, surviving a full process restart.
- Cross-session semantic recall requires TORMENT: with one provider message in context, the garden-remedy specifics could only have come from retrieval (§4).
- The step-25 cadence computes and persists correct values (§5), and those values reach the following prompt.
- Identity anchors did not dominate retrieval: across all 28 queries, ordinary relational memories held the top-ranked slot 21 times, anchors 6 times, core identity once.
- Post-cadence character state produced **no** change to retrieval weighting, MemoryPlan, or write routing (§7).

---

## 7. Behaviorally observed

Observed in the conversation record; not controlled, not quantified:

- Retrieval read as neither intrusive nor repetitive: six-item lists, anchors typically at rank 2–3, no evidence of displacement of live conversational content.
- The character remained consistent with the intended archetype across the restart.
- Under a deliberate fabrication probe (step 20), the model declined to confirm an unretrieved event rather than inventing one — the correct behavior, though a single instance.
- Post-cadence tone (steps 26–28) is indistinguishable in kind from steps 17–24. **No causal claim is made from response style**; the only channel through which the cadence could have influenced generation is the two lines of prompt text in §5, and their effect is unmeasured.

Provider reasoning quality is deliberately not graded here. The TORMENT result is that the prior-session material was available to be reasoned about at all.

---

## 8. Remaining inference

- That EID 6's reduced retrieval frequency in Session B (2/12, down from 11/16) reflects corpus growth and topic movement rather than the restart itself. Mechanism is clear; not isolated.
- That the Phase-1 `supplied_summary` repair caused the anchors to stop dominating, by raising relational-memory similarity scores. Measured correlation with a clear mechanism; no controlled comparison.
- The cause of Session A's three query failures. Twelve subsequent clean cycles on the same basin, plus an independent replay of all three failing queries against a copy of the step-16 state (all returning HTTP 200 in under 60 ms), exclude deterministic state corruption. A transient transport or service event is the best-supported reading, but the client discarded the exception, so the exact cause is unrecoverable.
- Whether the drift cadence *should* influence retrieval. A0 disables every consumer of the harvested geometric context, so the question is untestable in this arm.

---

## 9. Remaining known defects

Ordered by information destroyed per turn. None were fixed in this condition.

1. **Client-side summary slicing** — `build_ingest_summary` applies `user_text[:200]` and `assistant_text[:300]` at raw character offsets. In Session B, 12 / 12 assistant texts were truncated (405–1184 chars each) and 4 / 12 user texts. Approximately 61 % of assistant content is discarded before storage, deterministically, on every turn. This is now the largest mechanical memory-quality defect in the condition, and the fixed server-side first-sentence truncation is what promotes it to first place.
2. **Missing temporal context** — `created_ts`, `born_step` and `explain.recency_days` all reach the client over HTTP, but `format_memories` reads only summary, score, tier and provenance, and the system prompt has no wall-clock slot. Exposed in lived use as an invented "Tuesday" and an inability to place an event as tonight versus yesterday. No data is lost; a dimension is withheld.
3. **Query-exception observability** — `run_turn` catches the query exception with a bare `except Exception:` and `_empty_turn` has no `error` parameter, so connection failures, HTTP errors and JSON errors are indistinguishable after the fact.
4. **`drift_summary` never populated** — `measure_drift` produces an explanatory string including the distance figure; the query path hardcodes `"explanation": ""`, so it never reaches any surface.
5. **Anchor bonus cap bypass** — the per-anchor reduction is guarded on a non-empty candidate set, so on queries returning no seed-canon hit a derived anchor receives the full bonus instead of the reduced one. Both values (`0.082` and `0.16`) appear in this run's data; the bypass is intermittent and query-dependent.
6. **Premature anchor creation** — EID 6 was emitted at step 1 with `source_member_eids [1,2,3,4,5]` and `seed_overlap_count 4`: four of its five "recurrences" are the seed's own concept memories. EID 11, by contrast, is a legitimate conversation-derived anchor built from three real consecutive user turns with `seed_overlap_count 0`. Same code path, two outcomes.
7. **First-cadence `drift_direction` baseline** (§5 caveat) and **`derived_count` not persisted** to `CharacterState` — both observability-level.

---

## 10. Why the condition is frozen at step 28

The condition reached every objective it was opened to test: the step-25 cadence fired with verifiable values, cross-session continuity was demonstrated under near-ideal isolation, post-cadence writes succeeded, and the anchor question was answered with 28 queries of ranking data.

Continuing would add less than it costs. Reaching step 50 for a second cadence with a meaningful direction baseline is genuinely informative, but it would require ~22 further manual turns on a basin whose stored content is known to be ~61 % truncated — better obtained after defect 1 is repaired, on a fresh basin. New anchors cannot emit until steps 51 and 55 because the per-motif gap is 50.

The decisive reason is different: A0 is now a **clean pre-fix baseline**. Every remaining defect in §9 changes either what gets stored or what reaches the prompt. Frozen at 28, this condition is a 28-step, two-session, restart-crossing, cadence-firing reference against which the next condition can be compared. Extending it would make it a worse control, not a better one.

---

## 11. External evidence bundle

Preserved outside the runtime tree (`data/` and `outputs/` are both gitignored, so the runtime copies are not under version control):

```
C:\TORMENT\TORMENT_evidence\lived_use_a0_recovered_20260808\
    EVIDENCE_MANIFEST.txt
    BASIN_SHA256_MANIFEST.txt          (21 files: relative_path|bytes|sha256, sorted)
    basin_a0_fresh_20260808_v1\        (full basin copy, 21 files, 13,019,879 bytes)
    captures\
        20260808T202235Z-ab5614f1e0.jsonl
        20260808T215442Z-d2dfff5cf5.jsonl
    launchers\
        lived_use_a0_fresh_20260808_server.cmd
        lived_use_a0_fresh_20260808_chat.cmd
```

Every copied file was verified byte-identical to its original by SHA-256 after copying. The basin comparison reported zero differences across all 21 files.

---

## 12. Capture checksums

| capture | bytes | SHA-256 |
|---|---|---|
| `20260808T202235Z-ab5614f1e0.jsonl` (Session A) | 418,633 | `4b8f812f2768056bf41944197ba552248e59ebe3ddb2b9094384884d70bda763` |
| `20260808T215442Z-d2dfff5cf5.jsonl` (Session B) | 300,136 | `1aef501b2bed49e80b9d47007ce0f9e8285a642f2267c24fb7e1b36d749af681` |

Supporting checksums, for cross-reference against the bundle manifest:

| file | bytes | SHA-256 |
|---|---|---|
| `character_state.json` | 529 | `c62f92318be3f995536c1bb1976648fe4e889b9a26471ada0fb0bdf1cc40c52d` |
| `anchors.json` | 246 | `7b29e33069b28c37e237fbb1c4d6a062a2601ec06eb1f10e66a98cdd6a6334f4` |
| `nodes.jsonl` | 86,293 | `91082c8e9fa105ebc98118405bf0e21b5b893c91712ec8b53c8bb1679bad3e8a` |

---

## 13. Preservation statement

The original runtime basin at `data/lived_use/eira_voss/a0_fresh_20260808_v1` and both original captures under `outputs/lived_use/lived_use_eira_voss_a0/` remain untouched. Nothing was moved, renamed, modified, normalized or deleted; the evidence bundle was produced by copying, and the originals were re-hashed after the copy and matched. The two 2026-08-08 launcher files were likewise copied, not altered. No runtime behavior was changed and no fix from §9 was implemented as part of this checkpoint.
