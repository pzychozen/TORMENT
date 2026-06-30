# TORMENT — Dynamic-Kernel / Chirality Simulation Recovery Inventory v0.1

Status: **docs-only recovery inventory / NON-AUTHORIZING / no code / no tests / no runtime /
no regenerated images.** Codex decision: PASS docs-only recovery inventory first.

Purpose: establish, from repo-backed evidence only, what survives of the prior exploratory
"continuous kernel motion / chirality / identity-field" simulation lane after a PC crash that
lost out-of-repo work. This inventory **recovers no mechanics from screenshots beyond their
visible labels and repo-backed text matches**, and it **authorizes nothing** (no archaeology,
no repair, no re-run, no plot regeneration). It only classifies what exists, what is
screenshot-only, and what is missing — and names the gate any future move would require.

Surfaced trigger: three prior simulation images
(`chirality_flip_hunt.png`, `continuous_kernel_sim.png`, `conversation_shock_sim.png`).

---

## 1. Found artifacts (repo-backed, KNOWN)

### 1.1 The three screenshots — PRESENT in the working tree
- `docs/chirality_flip_hunt.png` (≈654 KB)
- `docs/continuous_kernel_sim.png` (≈748 KB)
- `docs/conversation_shock_sim.png` (≈662 KB)

These are the **plot outputs** of the lost scripts (not the scripts themselves). Their visible
labels (chirality-flip hunting, J_eff sign changes, Z-field + chirality memory, seed orbits,
identity triangle/state, conversation-shock injection, affirm/challenge/identity-probe events)
are **independently corroborated in repo text** by §1.2 below, so they are treated as
repo-backed, not screenshot-only inference.

### 1.2 The two grounding documents — PRESENT
- **`docs/RESEARCH_simulation_findings.md`** — "Simulation Findings: Continuous Kernel Motion —
  Phase A Results" (April 9, 2026; pzychozen + Claude Opus 4.6). This is the **primary recovery
  asset.** It documents all three runs in full: parameters (`MICRO_DT`, `Z_COUPLING`,
  `SEED_DRAG`, initial Omega, `omega_noise_sigma`), result tables (Z / J_eff ranges, flip
  counts, triangle-area growth, seed displacements, identity-state counts, the 4 chirality-flip
  scenarios A–D, the 3-shock schedule and impact table), and emergent principles. **It names the
  scripts and plots explicitly** (see §3).
- **`docs/RESEARCH_continuous_kernel_motion.md`** — "Research Note: Continuous Kernel Motion via
  Z-Field and Chirality Coupling" (April 9, 2026; same authors). The companion design proposal:
  the step-bound-kernel problem, a per-step component table citing `model_core.py` /
  `seed_entities.py` line ranges, the math-paper grounding, and a three-layer continuous-motion
  proposal (background Omega tick / Z-field coupling / seed drift). Marked
  "**research proposal — not for immediate implementation.**"

### 1.3 The engine primitives the sims used — PRESENT (production + siblings)
`RESEARCH_simulation_findings.md` states the sims "used the production `TriOctaPhaseLockModel`
and `SeedWorld` classes directly — no modifications to engine code. Z-force coupling was applied
externally in the simulation loop." Both classes survive:
- **Production:** `torment_service/kernel/model_core.py` (`class TriOctaPhaseLockModel`, with
  `z_mem`, the J_eff/chirality EMA, and `step()`) and `torment_service/kernel/seed_entities.py`
  (`class SeedWorld`).
- **Sibling copies** (differ slightly; line numbers diverge): `epistemic_kernel/kernel/`,
  `v4.0/`, and `Zenodo_research/tri_octagon_Model/17766958/model_core.py`.
- Repo-backed primitive tokens confirmed present in the production kernel: `z_mem`,
  `J_eff`/chirality (signed triad area, EMA chirality memory), `Z_chiral`, seed
  position/velocity dynamics, cycle stage, identity state.

### 1.4 Adjacent exploratory source (related lane, NOT the three sims)
Substantial chirality/kernel exploration survives under `v4.0/` (e.g. `chirality_param_scan.py`,
`side_zchiral_probe.py`, `z_spike_diagnostic.py`, `phase_triad_experiment.py`, `run_sim.py`,
`wide_scan_triocta.py`) and `Zenodo_research/tri_octagon_Model/17766958/` (`run_sim.py`,
`param_scan.py`, `physics_sampler*.py`). These are **related to the lane but are not** the three
named simulation scripts behind the screenshots.

### 1.5 Math grounding — PRESENT
`pdfs/` holds the cited papers, including `chirality_stabilized_geometry.pdf`
("Chirality-Stabilized Geometry"), `Toy_Model_RSB_Patch_3_4_Internal_Memo.pdf`
("Toy Model v3.4"), `TriOcta_v4.0.pdf`, and the broader RSB/SRG/TriOcta corpus.

---

## 2. Screenshot-only (visible labels, NOT repo-source-backed beyond §1)

The rendered plot panels themselves (axes, exact curves, color encodings, per-step trajectory
data) exist **only as pixels** in the three PNGs. The *quantitative* values are recoverable from
`RESEARCH_simulation_findings.md` (§1.2), but the **plotting code, panel layout, and raw
per-step arrays are not present**. No mechanics are inferred here beyond the labels already
corroborated by §1.2.

---

## 3. Source scripts — FOUND or ABSENT

`RESEARCH_simulation_findings.md` line 16 names the scripts and line 17 the plots:

| Screenshot (plot) — PRESENT | Named source script | Script status |
|---|---|---|
| `continuous_kernel_sim.png` | `sim_continuous_kernel.py` | **ABSENT** |
| `chirality_flip_hunt.png` | `sim_chirality_flip.py` | **ABSENT** |
| `conversation_shock_sim.png` | `sim_conversation_shock.py` | **ABSENT** |

**None of the three named simulation scripts exists anywhere in the mounted tree** (verified by
filename search and by string search). The three names appear **only inside
`RESEARCH_simulation_findings.md`** — nowhere in any `.py`. This is consistent with the reported
loss of out-of-repo work in the PC crash: the screenshots and the findings write-up were checked
into `docs/`, but the standalone driver scripts that produced them were not.

What the lost scripts contained (per the findings doc, not reconstructed here): the simulation
loops, the **external Z-force coupling** applied around `TriOctaPhaseLockModel`/`SeedWorld`, the
four chirality scenarios (A–D), the three-shock schedule (affirm +Z / challenge −Z / identity
probe Ω-rotation), and the plotting.

---

## 4. Missing artifacts (LOST)

1. **The three driver scripts** `sim_continuous_kernel.py`, `sim_chirality_flip.py`,
   `sim_conversation_shock.py` (§3).
2. **Raw per-step / trajectory data** behind the plots — no run-output, CSV, or log directory
   for these three sims was found.
3. **The external Z-force-coupling loop and scenario/shock configuration** as code (only their
   prose description in the findings doc survives).

---

## 5. Classification summary

| Item | Repo-backed source/docs | Screenshot-only | Missing |
|---|---|---|---|
| Three plot PNGs | ✅ present in `docs/` | — | — |
| Findings write-up (params + results) | ✅ `RESEARCH_simulation_findings.md` | — | — |
| Design/proposal note | ✅ `RESEARCH_continuous_kernel_motion.md` | — | — |
| Engine classes (`TriOctaPhaseLockModel`, `SeedWorld`) | ✅ production + siblings | — | — |
| Kernel primitives (J_eff, z_mem, chirality, seeds, identity state) | ✅ in production kernel | — | — |
| Math papers | ✅ `pdfs/` | — | — |
| The 3 driver scripts | — | — | ❌ absent |
| Raw per-step data / run outputs | — | — | ❌ absent |
| External Z-coupling loop / scenario+shock config as code | prose only | — | ❌ absent as code |

---

## 6. HOLD preserved (nothing below is opened by this inventory)

This inventory authorizes none of the following; all remain HOLD:
continuous runtime motion; Z-force coupling; spirit-return coupling; conversation-shock runtime;
identity-state runtime behavior; **tests-only archaeology**; **code+tests repair**; new
simulations; regenerated plots; production/runtime integration; memory writes; persistence /
logs / transcripts / generated outputs; endpoint / MCP / API / schema; provider / runtime /
AgentRunner / Terrain B / app / server / character surfaces; database / substrate / private
dream runtime; identity / canon / output-control / finalizer / refusal paths.

This document changed only itself (and, if convention required, a one-line §0 pointer). No
code, tests, runtime behavior, persistence, provider calls, generated outputs, or image
regeneration.

---

## 7. Future gate required before any next move

Before **tests-only archaeology** (characterizing/locking the documented sim behavior against
the surviving primitives) or **code+tests repair** (reconstructing the lost driver scripts), a
separate, explicitly-authorized gate must first decide, on paper:

1. **Reconstruction posture** — standalone research *outside* `torment_service/` (matching the
   original "no production code touched" stance) vs. production-adjacent. The original work was
   explicitly standalone; a repair should default to the same unless re-decided.
2. **Canonical primitive source** — which `TriOctaPhaseLockModel` / `SeedWorld` copy is the
   reference (production `torment_service/kernel/` vs `v4.0/` vs `epistemic_kernel/` vs
   `Zenodo_research/`); they are not byte-identical.
3. **Scope of reconstruction** — re-derive the external Z-coupling loop + scenarios + shock
   schedule from the findings doc's parameters, vs. treat the findings doc as a frozen historical
   record only.
4. **Fences carried forward** — every item in §6 stays HOLD; any reconstruction must not wire
   into runtime, persistence, providers, or identity/output-control surfaces.

Only after such a gate (and Codex/operator authorization) would a tests-only archaeology slice
or a code+tests repair slice be admissible. This recovery inventory opens none of them.

### 7.1 Operator-confirmed sequencing (recorded 2026; non-authorizing)

pzychozen confirmed the preferred order for any future follow-up — **reconstruction must NOT
come first**, because rebuilding the scripts first would risk inventing mechanics from the
screenshots:

1. **This inventory (now)** — docs-only; done.
2. **Tests-only archaeology next (only if grounded artifacts exist)** — before any rebuild,
   establish whether *any* further source shape survives: source fragments, scratch files, docs,
   imports, constants, filenames, or test traces tied to the three sims / the external Z-coupling
   loop. Characterize what the surviving primitives still do; invent nothing from pixels.
3. **Reconstruction (`code+tests`) only afterwards** — admissible only once archaeology has
   proven enough genuine source shape to rebuild against, not against screenshot inference.
4. **Frozen record** — if archaeology finds nothing reliable, treat the findings doc + PNGs as a
   preserved historical record and stop.

Each step is a separate, explicitly-authorized gate. This slice scopes to step 1 only: no
regenerated plots, no new scripts, no tests, no code.
