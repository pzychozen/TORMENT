# TORMENT — Dynamic-Kernel / Chirality Reconstruction Decision Frame v0.1

Status: **docs-only decision frame / NON-AUTHORIZING / no code / no tests / no scripts / no
runtime / no regenerated images or data.** Codex decision: PASS docs-only reconstruction
decision frame.

Purpose: make the dynamic-kernel / chirality simulation recovery lane **auditable** and decide,
on paper, whether script reconstruction is admissible yet. Verdict up front:
**reconstruction is NOT yet authorized.** This frame selects no canonical source, recreates no
script, and keeps every runtime/production behavior closed.

Grounding (evidence already on disk; this frame derives nothing new):
- `docs/TORMENT_DYNAMIC_KERNEL_CHIRALITY_SIMULATION_RECOVERY_INVENTORY_v0.1.md` (recovery
  inventory + operator-confirmed sequencing: archaeology before any reconstruction).
- `tests/test_dynamic_kernel_chirality_recovery_archaeology.py` (phase-1: the surviving
  deterministic primitives are importable and structurally usable).
- `tests/test_dynamic_kernel_copy_relationship_archaeology.py` (phase-2: the copy-relationship
  map across the four kernel copies).

---

## 1. Reconstruction status

**NOT AUTHORIZED.** The lane is at "archaeology complete, reconstruction undecided." The
surviving evidence is sufficient to *describe* what was done and *which primitives still exist*,
but not sufficient to rebuild the three driver scripts without inventing mechanics. No canonical
kernel copy has been chosen. No reconstruction gate is opened by this document.

---

## 2. What is absent (lost in the crash)

1. **The three driver scripts remain ABSENT** — confirmed by archaeology (named only in
   `RESEARCH_simulation_findings.md`, present in no `.py` under any copy; a test lock asserts
   they stay absent):
   - `sim_continuous_kernel.py`
   - `sim_chirality_flip.py`
   - `sim_conversation_shock.py`
2. **Raw per-step / trajectory data remains ABSENT** — no run-output, CSV, or log directory for
   the three sims exists. Only the rendered PNGs survive as pixels.
3. **The external coupling/scenario/shock loop survives as PROSE ONLY** — the Z-force coupling
   applied "externally in the simulation loop", the four chirality scenarios (A–D), and the
   three-shock schedule exist only as description in the findings doc, not as code.

---

## 3. Surviving evidence (recovery assets)

| Asset | Where | Recovery value |
|---|---|---|
| Three plot PNGs | `docs/chirality_flip_hunt.png`, `docs/continuous_kernel_sim.png`, `docs/conversation_shock_sim.png` | Visual record only (pixels); labels corroborated by §3 findings doc. |
| **Findings doc** | `docs/RESEARCH_simulation_findings.md` | **Primary asset:** full parameters (`MICRO_DT`, `Z_COUPLING`, `SEED_DRAG`, initial Ω, `omega_noise_sigma`), result tables, scenarios A–D, the 3-shock schedule + impacts, emergent principles. |
| Design note | `docs/RESEARCH_continuous_kernel_motion.md` | The per-step component table + math grounding + the 3-layer continuous-motion proposal. |
| Production kernel primitives | `torment_service/kernel/` (`TriOctaPhaseLockModel`, `SeedWorld`, `z_mem`/`jeff` chirality memory, `Z_chiral`, `cycle_stage`, `identity_state`, `update_z`, `step`) | Deterministic and importable (phase-1). The substrate the sims ran on. |
| Math papers | `pdfs/` (`chirality_stabilized_geometry.pdf`, Toy-Model memos, TriOcta corpus) | Theory grounding for the chirality/Z-field mechanics. |
| Copy-relationship map | phase-2 test | Establishes which copy holds which primitive (see §4). |

---

## 4. Why reconstruction is NOT yet authorized

1. **`model_core.py` copies DIVERGE.** The four kernel copies (production, `v4.0`,
   `epistemic_kernel`, `Zenodo_research/…/17766958`) have **four distinct `model_core.py`
   bodies** (four distinct content hashes). They are not interchangeable.
2. **No canonical source is selected** — and this frame does not select one. The chirality-memory
   surface (`z_mem` + `jeff`) survives in **two** copies (production AND `epistemic_kernel`);
   `v4.0` kept the `Z_chiral` vector but dropped the memory; `Zenodo` has neither and lacks
   `seed_entities.py` entirely. With ≥ 2 viable candidates and divergent bodies, "which kernel did
   the sims actually run on" is **unresolved**.
3. **The scenario / shock / Z-force loop is prose-backed only.** Reconstructing it from the
   findings doc's narrative would mean *inventing* the external-coupling mechanics (how Z-force
   was applied per step, exact shock injection points, scenario initial conditions beyond the few
   recorded numbers). That is screenshot/prose inference, explicitly out of bounds.
4. **Raw data is absent**, so a reconstruction could not be validated against the original
   per-step trajectories — only against the prose result tables, which is a weak and partial
   oracle (and risks fitting code to summary statistics).

Reconstructing now would therefore require canonical-source selection **and** mechanic invention
**and** would lack a trustworthy validation oracle. All three are disqualifying for this gate.

---

## 5. Admissibility criteria for a later reconstruction gate

A future, separately-authorized gate may consider reconstruction **only if it first establishes,
on paper and by source/test evidence:**

- **A1 — Canonical primitive source decided.** A separate decision frame selects which kernel
  copy (or an explicitly-frozen vendored snapshot) is the reference, with the divergences from §4
  characterized. This frame does **not** make that choice.
- **A2 — Mechanic provenance, not invention.** Every reconstructed mechanic (external Z-coupling,
  scenario IC, shock schedule) must be traceable to a repo-backed source value (findings-doc
  parameter, a surviving primitive, or a math-paper equation) — never inferred from a PNG curve.
  Where the source is insufficient, the mechanic stays unbuilt and is recorded as a gap.
- **A3 — A defined validation oracle.** State explicitly what a reconstruction is checked against
  (e.g. the findings-doc summary statistics as a *coarse* sanity oracle, with a documented caveat
  that raw per-step data is unavailable). No oracle ⇒ no reconstruction.
- **A4 — Fences preserved.** Every HOLD item in §8 stays closed; the work is standalone
  research/test-adjacent, deterministic, non-runtime, and wires into nothing.
- **A5 — Tests-first or code+tests under a separate explicit gate** (see §7). The decision to
  reconstruct, and the decision of *posture* (standalone vs production-adjacent), are distinct,
  separately-authorized steps.

If A1–A3 cannot be satisfied, the lane resolves to **frozen record** (the findings doc + PNGs +
archaeology stand as the preserved outcome), not reconstruction.

---

## 6. Future reconstruction targets (separated; none authorized)

If a later gate proceeds, the three are **independent** targets, in increasing reconstruction
risk:

- **T1 — `continuous_kernel`** (Sim 1, baseline continuous dynamics). **Lowest risk:** it used the
  surviving `TriOctaPhaseLockModel` + `SeedWorld` directly with recorded parameters and *no
  external shock/scenario machinery*; closest to the already-characterized deterministic
  primitives.
- **T2 — `chirality_flip`** (Sim 2, four noise/IC scenarios). **Medium risk:** needs the four
  scenario initial conditions and noise levels; only partially recorded; flip-counting depends on
  noise (`omega_noise_sigma > 0`), i.e. a *stochastic* regime — determinism would require seed
  pinning and the exact scenario configs, which are not fully recorded.
- **T3 — `conversation_shock`** (Sim 3, external Z/Ω shock injection). **Highest risk:** the
  entire external Z-force / Ω-rotation shock loop is prose-only; reconstructing it is the most
  inference-heavy and most likely to invent mechanics. Most dependent on A2.

This ordering is a risk note, not a work plan; it authorizes none of them.

---

## 7. Required shape of any future reconstruction

Should a separate gate ever authorize reconstruction, it MUST be:

- **deterministic** (no hidden randomness; any stochastic regime seed-pinned and reproducible);
- **non-runtime** (no continuous tick, no background motion, no service/Spine/endpoint wiring);
- **standalone research / test-adjacent** (matching the original "no production code touched"
  stance — outside `torment_service/` unless a separate posture decision re-decides it);
- **no plots by default** (no image generation);
- **no generated data by default** (no CSV/log/output files);
- **tests-first, or code+tests, ONLY under a separate explicit gate** — never as a side effect of
  this or any docs frame.

---

## 8. HOLD preserved

This frame opens nothing. All of the following remain **HOLD**: script reconstruction;
canonical-source selection; regenerated images/data; the Z-force runtime loop; conversation-shock
runtime; continuous runtime motion; production changes; provider/runtime wiring; endpoints / API /
schema; database / substrate; AgentRunner / Terrain B; memory writes; persistence / logging /
transcripts / output files; private-cognition runtime; identity / canon / output-control /
finalizer / refusal paths.

This document changed only itself. No code, tests, scripts, plots, images, data, runtime
behavior, persistence, or provider calls. The next move (if any) — a canonical-source decision
frame, or a tests-first reconstruction gate for T1 — is a separate, explicitly-authorized step.
