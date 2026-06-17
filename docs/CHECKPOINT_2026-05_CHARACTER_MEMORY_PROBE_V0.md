# Checkpoint — Character-Memory Harness Probe-v0

**Date:** 2026-05-31
**Status:** Closed / Ratified — plumbing PASS; runtime coherence COHERENCE_BROKEN candidate (no product verdict)
**Cluster:** Character-memory harness — first active (non-frozen) Probe-v0 instrument, independent of the frozen `torment_stress_harness/`.
**Commit:** `5c0b10b` feat(character-memory): add bounded Probe-v0 harness
**Framing:** *Probe-v0 is a single-turn, transcript-stateless, two-arm (seed-only baseline vs runtime-memory) seeded-recall-and-voice bring-up for the Eland seed (`truthful_accidental_lie_v1`) under companion posture. It exercises governed `/retrieve` selection and a deliberately minimal model-visible prompt (verbatim persona seed + plain surfaced memory text only). It is NOT a coherence verdict, NOT the production `assembled_text` surface (parked as Probe-v1), and NOT `/agent/query` (parked). Automation, drift cadence, mood/anchor/role, and relational continuity are structurally dormant at a single ingest and explicitly out of scope.*

---

## Summary

The harness reproduces, in fresh code, the transcript-stateless two-arm retrieval principle that previously existed only inside the frozen `torment_stress_harness/`, so future character-memory testing no longer depends on touching frozen evidence. Probe-v0 seeds both arms identically, ingests one deterministic temporary fact into the runtime arm only (via `/agent/ingest` with `supplied_summary`), calls governed `/retrieve` at a transcript-stateless callback, builds a minimal clean prompt, and makes one stateless model call per arm. Grading is human-applied; the runner only prepares a review template.

Across three runs the instrument deflated its own first impression in the right direction:

- `20260530T183554Z_765e` — bring-up PASS, but ran with companion-profiled retrieval/assembly while the service-derived character posture was empty, so character-level interpretation was deferred; its recall section also still duplicated decomposed `seed_canon` fragments.
- `20260531T181119Z_c1c2` — confirmed the service-level companion posture and exposed the duplicated-seed prompt confound.
- `20260531T193241Z_3059` — after the `seed_canon` exclusion fix, proved the corrected clean prompt contract end-to-end. This is the clean reference artifact.

---

## Arc (chronological, 2026-05-30 → 2026-05-31)

1. Probe-v0 harness brought up; `765e` executed as a plumbing PASS but without service-derived companion posture, and carrying a clean-prompt confound not yet recognized.
2. A preflight gate was added: capture `/health`, `/config`, `/embedder/check` into the manifest; abort before any workspace mutation unless companion posture holds (profile name `companion`, character enabled, embedder `st` / `BAAI/bge-small-en-v1.5` / `cpu` / dim 384 / ok / not degraded). The verifier rejects the exact `765e` posture and a hash-embedder trap.
3. `c1c2` reran under explicit companion posture: posture PASS, manifest captured the posture block, runtime arm surfaced the fact — but the model-visible recall list still repeated the seed, because `extract_plain_memory_lines` excluded only `metadata.is_seed`, letting the decomposed `seed_canon` fragments (eids 1–5) back into "Things you remember:".
4. Narrow fix: exclude `metadata.is_seed OR metadata.type == "seed_canon"`. Codex prevented an over-broad `source == "core"` filter, which would have dropped the planted runtime episode (also serialized as core). The fix is pinned by 8 offline regressions in `test_prompt_surface_offline.py`.
5. `3059` reran post-fix under companion posture: the clean prompt contract was confirmed in the live artifact — seed-only prompt = verbatim seed once with no recall section; runtime prompt = verbatim seed once plus a single plain bullet carrying only the surfaced fact.

---

## What this proves (narrowly stated)

- Fresh disposable `cm_loop_*` workspace isolation; prefix-gated creation; no auto-deletion.
- Companion-posture preflight fails closed before any workspace mutation, and the manifest preserves the captured posture even on abort.
- Governed `/retrieve` selection works; the runtime arm surfaces exactly the planted chapter-seven fact while the seed-only arm does not.
- Clean model-visible prompt contract: verbatim seed once + plain memory bullets only — no scores, tiers, drift labels, provenance, or audit machinery in model-visible text.
- The `seed_canon` duplication confound is fixed and regression-pinned (8/8 offline; `py_compile` clean; `matrix.yaml` parse OK — all run on Windows, the source of truth).

## What this does NOT prove

- It is not a character-coherence verdict. With the prompt clean, `3059`'s runtime reply recalled the surfaced fact accurately and in voice but invented surrounding manuscript details beyond it (harvest references, a child's age, weathered relationships). Under the pinned rubric this is a **COHERENCE_BROKEN candidate** (invented authority), consistent with `c1c2`. The rubric is not loosened retroactively.
- No product-level claim. This is one bounded, single-turn observation. Drift, mood, anchor, role, and relational continuity are dormant at one ingest and untested here.

## Parked / out of scope (carried to the next gate)

- **Authority-versus-emergence tension** — Eland's seed deliberately rewards premature pattern-completion, the very behavior the current rubric scores as invented authority; the seed and the gate are in tension. Subject of a separate audit-first design gate, not closed here.
- **Presupposition-loaded callback** — the current callback presupposes a shared passage state; a non-presupposing variant (allowing honest uncertainty) belongs to the next instrument.
- **Relational-count observability mismatch** — currently explained by different populations and snapshot timing: `tier_breakdown.relational` counts relational hits surfaced in the current query, while `relational_count` is the last drift-snapshot private-graph relational census passed through from `CharacterState`. The "No relational memories yet..." recommendation follows the snapshot counter, so it can lag a relational hit surfaced this turn. This is an observability/telemetry note only; no prompt/model-visible contract, retrieval behavior, or counter relationship is changed or asserted here.
- **`agent_locks = 2` at `3059` preflight** — observed before workspace creation; verify locks release cleanly across runs.
- **Probe-v1** (production `assembled_text` surface with `[Identity Context]`/`[Drift:]`/`[Voice:]`/`[Flavor:]` labels) and **`/agent/query`** raw-retrieval comparison remain parked by design.

## Evidence locations

- Harness source (committed at `5c0b10b`): `character_memory_harness/{README.md, matrix.yaml, run_bounded_loop.py, test_prompt_surface_offline.py}`.
- Forensic artifacts (git-ignored, local-only): `character_memory_harness/outputs/` — `*_manifest.json`, `*.json`, `*_review.md` for `765e`, `c1c2`, `3059`.
- Disposable `cm_loop_*` workspaces (six: seed-only + runtime-memory for each of the three runs) were inspected, then removed via explicit named-path deletion after this closure; the forensic outputs above were preserved.
