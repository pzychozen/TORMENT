"""Geometric State Harvester — reads existing TORMENT kernel/agent state
and normalizes it into a GeometricStanceContext for stance modulation.

This module is a *read-only bridge*.  It does not modify kernel, character,
or SRG state.  It harvests already-computed values and maps them into the
0.0–1.0 normalized signals that the stance policy understands.

When called without state (e.g. at startup or for agents with no kernel
history), it returns ``None`` — the stance policy then behaves as pure
deterministic scaffold.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .thinking_models import GeometricStanceContext


def harvest_geometric_context(
    *,
    character_state: Optional[Dict[str, Any]] = None,
    tri_mod: Optional[Dict[str, Any]] = None,
    coherence_summary: Optional[Dict[str, Any]] = None,
    live_social: bool = False,
    srg_relational: Optional[float] = None,
) -> Optional[GeometricStanceContext]:
    """Build a GeometricStanceContext from available runtime state.

    Parameters
    ----------
    character_state
        Output of ``build_self_state()`` — contains drift_score,
        drift_direction, seed_basin_phi/kappa/tension/role,
        phase_duration_steps, corridor_duration_steps, etc.
    tri_mod
        The kernel's ``tri_mod`` diagnostic dict from the most recent
        ``TriOctaMemoryKernel.process()`` call — contains coh_ema,
        tearing_risk, in_corridor, survival_steps, etc.
    coherence_summary
        Output of ``CoherenceField.summary()`` — contains phi_mean,
        tension_mean, kappa_mean, basin/ridge/plateau counts.
    live_social
        Whether this interaction is in a live-social context.

    Returns
    -------
    GeometricStanceContext or None
        ``None`` if no meaningful geometric state is available (no
        character state AND no kernel state).  The stance policy
        treats ``None`` as "use pure deterministic scaffold."
    """
    has_char = character_state is not None and character_state.get("seed_id")
    has_kernel = tri_mod is not None and "coh" in tri_mod or (
        tri_mod is not None and "coh_phase" in tri_mod
    )

    if not has_char and not has_kernel:
        return None

    # ── Coherence (from kernel coh_ema, or fallback to 0.5) ──────────

    coherence = 0.5
    if tri_mod:
        # coh_ema is the smoothed coherence, typically 0.75–0.92
        raw_coh = tri_mod.get("coh", tri_mod.get("coh_phase", 0.0))
        # Normalize: map 0.70–0.95 range to 0.0–1.0
        coherence = _clamp((raw_coh - 0.70) / 0.25)

    # ── Stability (from tearing_risk inverted + basin role) ──────────

    stability = 0.5
    tear_component = 0.5
    basin_component = 0.5

    if tri_mod:
        # tearing_risk typically 0.33–0.37 stable, up to 0.7+ stressed
        tear = tri_mod.get("tearing_risk", 0.35)
        # Invert and normalize: 0.0 tear → 1.0 stability, 0.7 tear → 0.0
        tear_component = _clamp(1.0 - (tear / 0.70))

    if character_state:
        role = character_state.get("seed_basin_role", "plateau")
        basin_component = {"basin": 0.9, "plateau": 0.5, "ridge": 0.15}.get(role, 0.5)

    stability = 0.6 * tear_component + 0.4 * basin_component

    # ── Identity lock (from drift_score + drift_direction) ───────────

    identity_lock = 0.5
    if character_state:
        # drift_score: -1.0 (far from seed) to +1.0 (on seed)
        drift = character_state.get("drift_score", 0.0)
        direction = character_state.get("drift_direction", "stable")

        # Map -1..+1 to 0..1
        base_lock = _clamp((drift + 1.0) / 2.0)

        # Penalize "away_seed" direction, boost "toward_seed"
        if direction == "away_seed":
            base_lock *= 0.80
        elif direction == "toward_seed":
            base_lock = min(1.0, base_lock * 1.10)

        identity_lock = base_lock

    # ── Ambiguity tolerance (from seed_basin_phi) ────────────────────

    ambiguity_tolerance = 0.5
    if character_state:
        # seed_basin_phi: reinforcement - tension, range roughly -1..+1
        phi = character_state.get("seed_basin_phi", 0.0)
        # Map -1..+1 to 0..1: positive phi = healthy basin = more tolerance
        ambiguity_tolerance = _clamp((phi + 1.0) / 2.0)

    # Coherence also feeds ambiguity tolerance (healthy kernel = more tolerant)
    if tri_mod:
        ambiguity_tolerance = 0.7 * ambiguity_tolerance + 0.3 * coherence

    # ── Social resonance (provisional composite) ─────────────────────

    social_resonance = 0.5
    if live_social:
        social_resonance = 0.6  # Base boost for being in social context

    if tri_mod:
        # Corridor survival = sustained processing = more engaged
        surv = tri_mod.get("survival_steps", 0.0)
        surv_norm = _clamp(surv / 2.0)  # surv_ema range 0–3, normalize to 0–1
        social_resonance = 0.5 * social_resonance + 0.3 * coherence + 0.2 * surv_norm

    # ── SRG relational blend (Slice B, advisory) ─────────────────────
    # When the agent-level SRG relational signal is available, let it lightly
    # inform social_resonance — it informs, never dominates. ``None`` (SRG off,
    # or no ingest yet) reproduces the exact prior behavior. The input is
    # clamped so the blended output stays bounded 0.0–1.0.
    if srg_relational is not None:
        _srg = _clamp(float(srg_relational))
        social_resonance = _clamp(0.85 * social_resonance + 0.15 * _srg)

    return GeometricStanceContext(
        coherence=round(coherence, 4),
        stability=round(stability, 4),
        identity_lock=round(identity_lock, 4),
        ambiguity_tolerance=round(ambiguity_tolerance, 4),
        social_resonance=round(social_resonance, 4),
    )


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))
