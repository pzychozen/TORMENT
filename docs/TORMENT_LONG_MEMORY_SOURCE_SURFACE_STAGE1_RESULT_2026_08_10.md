# TORMENT Long-Memory Source Surface Stage-1 Result

Date: 2026-08-10

Experiment: `long_memory_source_surface_characterization_v1`

This note preserves the completed Stage-1 long-memory source/surface result and the bounded restart-hydration causal repair. It is a scientific record, not a new authorization to tune retrieval, provider behavior, compression, Spirit Return, warmth, or correction semantics.

## 1. Original Stage-1 Negative

Baseline commit: `dd06aea93ea89dbefe8e8aeab032a45bc6ed293e`

Evidence: `outputs/lived_use/lmsc_v1/20260810T210520Z/stage1_result.json`

Verdict: `STAGE_1_COMPLETED_NEGATIVE_SURFACE`

Mechanically demonstrated:

- ordinary private episodic memory -> unchanged production-threshold compression;
- long-path deep export;
- source row retained with compression/lifecycle mutation;
- traceable lossy Deep Memory echo;
- persisted deep object survived restart.

After fresh-process restart, `/retrieve` surfaced the ordinary source row, but the deep lane did not reach `DeepMemoryStore.query`; there was no Spirit Return, no `[Returning Memory]`, and no warmth mutation.

Frozen original outcomes:

- `S0_NO_RETURNING_MEMORY_SURFACE`
- `W0_NO_WARMTH_MUTATION`

This historical negative must remain preserved and not be rewritten by the later fix.

## 2. Causal Investigation

Provider-free no-restart/restart A/B established:

- ARM NR: deep export -> no restart -> `[Returning Memory]` surfaced -> warmth created.
- ARM R: same deep export -> fresh process -> persisted deep object remained valid on disk -> no runtime deep-store attachment -> no `[Returning Memory]`.

Classification:

- `G1_DEEP_SURFACES_WITHOUT_RESTART_AND_FAILS_AFTER_RESTART`
- `G6_DEEP_STORE_NOT_AVAILABLE_TO_RUNTIME`

Root cause: `fabric._deep_stores` was process-local and populated only as a side effect of compression in the current process. A fresh `TormentFabric` initialized `_deep_stores = {}` and did not reconstruct persisted `DeepMemoryStore` state. Independent construction of `DeepMemoryStore` over the persisted directory succeeded, proving persistence itself was intact.

## 3. Bounded Correctness Repair

Fix commit: `c4ad46aecdda1529b2d6510ebbc289e6e248a793`

Commit message: `fix(memory): rehydrate persisted deep stores after restart`

Repair semantics:

- lazy retrieval-time attachment;
- only when compression is enabled;
- cache-first;
- exact workspace/agent scope;
- reuse existing `safe_slug` / realpath / containment hardening;
- persisted `deep_memory/memories.jsonl` must already exist;
- no `DeepMemoryStore` construction when absent;
- no read-path creation of empty deep-memory directories;
- existing agent lock serializes first hydration;
- existing compression/export create behavior unchanged.

No change was made to compression thresholds, deep retrieval budgets, Spirit Return modes/scoring, warmth behavior, provider rendering, randomness, correction/supersession, or status/diagnostic hydration.

## 4. Executable Proof

Pre-patch load-bearing regression: fresh `TormentFabric` over valid persisted deep memory, with no manual `_deep_stores` injection, produced no deep hit. The regression failed as expected on the baseline.

Post-patch focused result:

- `tests/test_deep_memory_restart_hydration.py`: 5 passed.

Additional focused validation:

- compression path hardening: 20 passed;
- query deep lane: 6 passed;
- compression/scorer: 66 passed;
- workspace isolation: 11 passed;
- selected Spirit Return suite: 101 passed, 1 skipped;
- selected retrieval/query suite: 54 passed;
- deep-memory path hardening: 14 passed with the Windows symlink privilege test deselected.

The deselected symlink case was an environment privilege limitation and is not evidence for or against the hydration fix.

## 5. Post-Fix Causal A/B

Evidence: `outputs/lived_use/lmsc_fix_ab_v1/20260810T230433Z/ab_result.json`

- ARM NR: no restart -> `[Returning Memory]` surfaced -> warmth created.
- ARM R: fresh process -> persisted deep store lazily attached -> `[Returning Memory]` surfaced -> warmth created.

Conclusion: `G1` / `G6` are closed for controlled production-threshold retrieval reachability.

## 6. Post-Fix Original Stage-1 Rerun

Evidence: `outputs/lived_use/lmsc_v1/20260810T230500Z/stage1_result.json`

Verdict: `STAGE_1_COMPLETED`

Outcome:

- `S1_RETURNING_MEMORY_SURFACED`
- `S2_NORMAL_AND_DEEP_DUPLICATE_SURFACE`
- `W1`
- `SURFACE_EVIDENCE_ONLY`

Fresh-process `[Returning Memory]` is now demonstrated. First retrieval warmth was `appearance_count=1`, `current_warmth=0.2`. A later restart/retrieve observed `appearance_count=2`, `current_warmth=0.35`. This mechanically establishes warmth mutation/persistence, not warmth usefulness.

## 7. Source / Deep Evidence Finding

The original source remained semantically unchanged but was weakened/marked by compression. The Deep Memory echo was traceable but lossy. Controlled source details lost after raw 200-character truncation included:

- second drawer;
- old wooden desk;
- reason to stay dry.

The deep summary ended mid-sentence.

Park without fixing:

- `DEEP_ECHO_MID_SENTENCE_TRUNCATION`
- status: `EVIDENCE_INTEGRITY_INVESTIGATION_CANDIDATE`

## 8. Other Parked Findings

Preserve without resolving:

- `SPIRIT_RETURN_RANDOMNESS_NOT_PRESENT_CURRENT_HEAD`
  - classification: `HISTORICAL_INTENT_OR_DESIGN_DIVERGENCE_CANDIDATE`
- `S2_NORMAL_AND_DEEP_DUPLICATE_SURFACE`
  - status: `INVESTIGATION_CANDIDATE`
- `SPIRIT_RETURN_SURFACE_RELEVANCE_CUE`
  - status: `INVESTIGATION_CANDIDATE`
- `COMPRESSED_STEP_TIME_DOMAIN_MISMATCH`
  - status: `INVESTIGATION_CANDIDATE`
- `WARMTH_ON_APPEARANCE`
  - status: `READY_FOR_SEPARATE_CHARACTERIZATION`

The restart-hydration fix made some of these behaviors observable after restart. It did not create, validate, or resolve them.

## 9. Scientific Boundary

Mechanically demonstrated:

- production-threshold compression/export;
- durable Deep Memory persistence;
- restart rehydration after fix;
- Spirit Return provider surface;
- first-retrieval warmth mutation;
- warmth persistence across restart.

Not demonstrated:

- ordinary natural-lived-use long-memory reachability;
- random spontaneous flashbacks;
- provider interpretation quality;
- usefulness of warmth;
- adequacy of lossy compression;
- desirability of normal+deep duplicate surfacing.

TORMENT remains an evidence/context system, not a mechanism deciding what the provider must believe.

## 10. Next Scientific Target

Recommended next target: `WARMTH_FEEDBACK_CHARACTERIZATION`.

Do not launch it from this preservation note.

## Files

Keep the existing experiment harness:

- `scripts/long_memory_source_surface_characterization_v1.py`

Do not modify it for this preservation task.
