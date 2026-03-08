# TORMENT Fabric — Stability and Attractor Validation

Kernel validation lineage: v1.12.6, preserved in v2.0

---

## 1. Purpose

This document records long-horizon stability testing of the TORMENT memory kernel. The goal was to verify bounded internal dynamics, absence of runaway multipliers, stable attractor behavior, and reproducibility across seeds.

---

## 2. Test Environment

Scripts: `sim/test_metastability_dryrun.py`, `sim/test_corridor_stress.py`

Configuration: affect disabled, private ingest scope, long-horizon runs (5000 steps). Seeds tested: default, 456, 789.

---

## 3. Metrics Monitored

coh, disp, coh_phase, z, tear, surv, align, aema, wm, pm, bp, bs

---

## 4. Periodic Forcing Results

Under periodic text cycling the system forms a **limit-cycle attractor**. Z oscillates between +0.209 and -0.193. Coherence stabilizes near 0.77-0.80. Dispersion remains bounded near 1e-4 to 5e-4.

---

## 5. Random Forcing Results

Randomized text selection removes the strict limit cycle. The system instead occupies a **bounded attractor basin**. Typical Z range: -0.21 to +0.22. Coherence range: 0.75-0.92. No unbounded drift was observed.

---

## 6. Seed Sensitivity

All seeds (default, 456, 789) converged to the same attractor envelope. The system is **seed robust**.

---

## 7. Perturbation Tolerance

Occasional dispersion spikes (disp ~ 1.9e-2) were observed. The system recovered automatically within one cycle. No persistent instability occurred.

---

## 8. Corridor Stress

Corridor tests show tear ~ 0.33-0.37 with no upward drift. Corridor integrity remains intact.

---

## 9. Multiplier Stability

Multipliers remained bounded: wm ~ 1.05-1.10, pm ~ 1.02-1.03, bp ~ 0.11, bs ~ 0.84. No runaway amplification occurred.

---

## 10. Verdict

The kernel demonstrates bounded attractor dynamics, seed robustness, perturbation recovery, multiplier equilibrium, and corridor stability. The system is considered **stable for controlled deployments**.

---

## 11. Character Modulation Stability (v2.0)

The v2.0 character modulation operates within conservative bounds: coupling g is modulated ±15% of the default 0.2 (range 0.17-0.23), and theta_lock is shifted ±0.1 rad from the default 0.244. These bounds were chosen to preserve all stability properties validated above.

Tested configurations: warm character (g=0.215, warmth=0.997) and analytical character (g=0.185, structure=0.981) both produced stable trajectories over 30 steps with identical forcing. Omega divergence of 0.017 confirms the modulation creates meaningfully different dynamics while remaining bounded. Global parameters are restored after every step via try/finally.

---

## 12. Future Validation

Future research directions: noise injection analysis, basin mapping, attractor visualization, multi-agent coupling experiments, character modulation long-horizon stress testing.
