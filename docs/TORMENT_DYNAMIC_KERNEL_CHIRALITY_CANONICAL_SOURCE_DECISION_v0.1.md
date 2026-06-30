# TORMENT — Dynamic-Kernel / Chirality Canonical-Source Decision v0.1

Status: **docs-only decision note / NON-AUTHORIZING / no code / no tests / no scripts / no
runtime / no regenerated plots or data.** Codex decision: PASS docs-only canonical-source
decision frame.

**Decision:** for any future, separately-gated standalone reconstruction of the recovered
dynamic-kernel / chirality simulation lane, the **canonical REFERENCE source is
`torment_service/kernel/`.**

Grounding (evidence already on disk; this note derives nothing new):
- `docs/TORMENT_DYNAMIC_KERNEL_CHIRALITY_SIMULATION_RECOVERY_INVENTORY_v0.1.md`
- `docs/TORMENT_DYNAMIC_KERNEL_CHIRALITY_RECONSTRUCTION_DECISION_FRAME_v0.1.md`
- `tests/test_dynamic_kernel_chirality_recovery_archaeology.py` (phase-1 primitive characterization)
- `tests/test_dynamic_kernel_copy_relationship_archaeology.py` (phase-2 copy-relationship map)

---

## 1. Scope of this decision (what it is, and is NOT)

This is a **reference-source decision ONLY.** It records which existing copy a *future*
reconstruction should be read/compared against. It is explicitly:

- **NOT production integration** — nothing is wired into the live service / Spine / endpoints.
- **NOT authorization to edit `torment_service/kernel/`** — the canonical copy is touched in no
  way by this lane; "canonical reference" means "read-only point of comparison".
- **NOT runtime behavior** — no continuous tick, no Z-force loop, no shock loop, no motion.
- **NOT script reconstruction** — the three lost driver scripts are not recreated (see §6).
- **NOT plot/data generation** — none.

It selects a reference; it opens no implementation.

---

## 2. Canonical: `torment_service/kernel/`

Chosen as the canonical reference for these repo-backed reasons:

- **Active repo source.** It is the live, in-tree kernel package — the same code the findings doc
  states the original sims "used … directly". It is the natural reference for a standalone
  reconstruction that wants to read the *current* primitive shapes.
- **Protected by current tests and recent archaeology.** It is the copy exercised by the phase-1
  archaeology (importable, deterministic, structurally usable) and by the broader kernel-isolation
  suites; regressions in it are caught. The sibling copies are not under test.
- **Preserves the chirality-memory surface.** Its `model_core.py` carries the full
  `z_mem` + `jeff` (J_eff) chirality-memory EMA, `Z_chiral`, `cycle_stage`, `identity_state`,
  `update_z`, `step`, plus `seed_entities.py` (`SeedWorld` / `SeedEntity`) — i.e. the complete
  primitive surface the recovered lane depends on.
- **Aligns with current repo behavior.** Reading the reconstruction against the active source
  keeps any future archaeology consistent with how the kernel behaves in the repo today, rather
  than against a drifted historical snapshot.

Note: "canonical" here is a *reference* status, not a correctness ranking of the divergent bodies.
The four `model_core.py` copies still differ; this decision picks the one to read against, it does
not declare the others wrong.

---

## 3. Secondary corroboration (NOT canonical): `epistemic_kernel/kernel/`

- **Also preserves the chirality-memory surface** (`z_mem` + `jeff` present), so it is a genuine
  second witness to the primitives the sims used.
- **Useful as a comparison / corroboration source** — divergences between it and the canonical
  copy can be inspected to bound which mechanic details are stable vs copy-specific.
- **Not canonical** because it is **not the active, tested, in-service kernel** — it is a parallel
  snapshot outside `torment_service/`, not under the repo's test protection.

Status: secondary corroboration source; consult, do not treat as the reference of record.

---

## 4. Non-canonical for this lane: `v4.0/`

- **Related kernel lineage** (shares the `TriOctaPhaseLockModel` / `SeedWorld` family and the
  `Z_chiral` vector + `cycle_stage` / `identity_state` / `update_z` / `step` surface).
- **Does NOT preserve the full chirality-memory surface the recovered lane needs:** its
  `model_core.py` has `Z_chiral` geometry but **lacks `z_mem` and `jeff`** — the chirality-MEMORY
  EMA that the findings doc's results (chirality memory as resistance, accumulated bias) depend on.

Status: lineage-adjacent but missing the lane's defining primitive; non-canonical here.

---

## 5. Non-canonical: `Zenodo_research/tri_octagon_Model/17766958/`

- **Reduced `model_core.py`** — lacks the diagnostic helpers (`_unit` / `_mirror_z` /
  `_make_history_meta`) and, critically, carries **no chirality machinery at all** (no `z_mem`, no
  `jeff`, no `Z_chiral`).
- **No `seed_entities.py`** — `SeedWorld` / `SeedEntity` (the seed position/velocity / seed-orbit
  state) are absent entirely.
- Therefore it **lacks the recovered lane's full chirality + seed surface.**

Status: earliest/leanest snapshot; non-canonical for this lane.

### Copy-vs-primitive summary (from phase-2 archaeology)

| Primitive surface | `torment_service/kernel` (canonical) | `epistemic_kernel` (secondary) | `v4.0` | `Zenodo …/17766958` |
|---|---|---|---|---|
| `z_mem` + `jeff` chirality memory | ✅ | ✅ | ❌ | ❌ |
| `Z_chiral` vector | ✅ | ✅ | ✅ | ❌ |
| `SeedWorld` / `SeedEntity` | ✅ | ✅ | ✅ | ❌ (no file) |
| `cycle_stage` / `identity_state` / `update_z` / `step` | ✅ | ✅ | ✅ | ✅ |
| Under active repo tests | ✅ | ❌ | ❌ | ❌ |

(`identity_rules.py` is byte-identical across all four; `seed_entities.py` is byte-identical across
the three that have it; the four `model_core.py` bodies all diverge.)

---

## 6. Lost driver scripts remain absent and unreconstructed

This decision recreates nothing. The three driver scripts remain **ABSENT** (named only in
`RESEARCH_simulation_findings.md`, present in no `.py`), and a test lock continues to assert their
absence:
- `sim_continuous_kernel.py`
- `sim_chirality_flip.py`
- `sim_conversation_shock.py`

Raw per-step data and the external Z-force / scenario / shock loop likewise remain absent (the
loop survives as prose only). Selecting a canonical reference does **not** change this.

---

## 7. Required shape of any future reconstruction (still separately gated)

Should a later, explicitly-authorized gate proceed, the reconstruction MUST be:

- **standalone** (research / test-adjacent, outside `torment_service/`; the canonical copy is read
  as reference, not modified);
- **deterministic** (no hidden randomness; any stochastic regime seed-pinned and reproducible);
- **non-runtime** (no continuous tick, no background motion, no service/Spine/endpoint wiring);
- **no plots / no generated data by default** (no images, CSV, logs, or output files);
- **separately gated** (the decision to reconstruct, and whether tests-first or code+tests, are
  distinct authorized steps — never a side effect of a docs frame);
- **sourced against `torment_service/kernel/` as the reference of record**, with
  `epistemic_kernel/` available as corroboration and any mechanic provenance traced to repo-backed
  sources (findings-doc parameters, surviving primitives, math papers) — never inferred from a PNG
  curve.

---

## 8. HOLD preserved

This note opens nothing. All of the following remain **HOLD**: script reconstruction; production
changes; regenerated plots / data / images; runtime behavior; the Z-force loop; the
conversation-shock loop; continuous-motion integration; provider wiring; endpoints / API / schema;
database / substrate; AgentRunner / Terrain B; memory writes; persistence / logging / transcripts /
output files; private-cognition runtime; identity / canon / output-control / finalizer / refusal
paths.

This document changed only itself. No code, tests, scripts, plots, images, data, runtime behavior,
persistence, or provider calls. The next move (if any) — a separately-authorized tests-first
reconstruction gate for the lowest-risk target (`continuous_kernel`), sourced against the canonical
`torment_service/kernel/` — is a distinct, explicit step, not opened here.
