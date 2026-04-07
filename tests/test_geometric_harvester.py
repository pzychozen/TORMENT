"""Tests for the GeometricStanceContext harvester.

Validates that harvest_geometric_context correctly normalizes raw
kernel/character state into 0.0–1.0 signals, and returns None when
no meaningful state is available.
"""

from torment_service.geometric_harvester import harvest_geometric_context


def test_returns_none_with_no_state():
    """No character_state and no tri_mod → None."""
    assert harvest_geometric_context() is None


def test_returns_none_with_empty_character():
    """character_state without seed_id → None."""
    assert harvest_geometric_context(character_state={}) is None


def test_minimal_character_state():
    """With just a seed_id, we should get a context with defaults + character signals."""
    ctx = harvest_geometric_context(character_state={
        "seed_id": "ryuki",
        "drift_score": 0.0,
        "drift_direction": "stable",
        "seed_basin_phi": 0.0,
        "seed_basin_role": "plateau",
    })
    assert ctx is not None
    # identity_lock: (0.0 + 1.0)/2.0 = 0.5, stable direction → no adjustment
    assert abs(ctx.identity_lock - 0.5) < 0.01
    # ambiguity_tolerance: (0.0 + 1.0)/2.0 = 0.5
    assert abs(ctx.ambiguity_tolerance - 0.5) < 0.01
    # stability: 0.6*tear(default 0.5) + 0.4*plateau(0.5) = 0.5
    assert abs(ctx.stability - 0.5) < 0.01


def test_kernel_state_normalizes_coherence():
    """coh_ema of 0.825 should map to ~0.5 (midpoint of 0.70–0.95 range)."""
    ctx = harvest_geometric_context(tri_mod={
        "coh": 0.825,
        "tearing_risk": 0.35,
        "survival_steps": 1.0,
    })
    assert ctx is not None
    assert abs(ctx.coherence - 0.5) < 0.05


def test_high_coherence_maps_high():
    """coh_ema of 0.95 → coherence = 1.0."""
    ctx = harvest_geometric_context(tri_mod={"coh": 0.95, "tearing_risk": 0.0})
    assert ctx is not None
    assert ctx.coherence >= 0.95


def test_high_tearing_risk_lowers_stability():
    """tearing_risk of 0.70 → tear_component = 0.0."""
    ctx = harvest_geometric_context(tri_mod={"coh": 0.80, "tearing_risk": 0.70})
    assert ctx is not None
    assert ctx.stability < 0.35


def test_drift_toward_seed_boosts_lock():
    """drift_score=0.5 toward_seed should give identity_lock > 0.75 * 1.10."""
    ctx = harvest_geometric_context(character_state={
        "seed_id": "ryuki",
        "drift_score": 0.5,
        "drift_direction": "toward_seed",
        "seed_basin_phi": 0.0,
        "seed_basin_role": "basin",
    })
    assert ctx is not None
    # base: (0.5+1.0)/2.0 = 0.75, * 1.10 = 0.825
    assert ctx.identity_lock > 0.80


def test_drift_away_seed_penalizes_lock():
    """drift_score=0.5 away_seed should give identity_lock = 0.75 * 0.80 = 0.60."""
    ctx = harvest_geometric_context(character_state={
        "seed_id": "ryuki",
        "drift_score": 0.5,
        "drift_direction": "away_seed",
        "seed_basin_phi": 0.0,
        "seed_basin_role": "basin",
    })
    assert ctx is not None
    assert abs(ctx.identity_lock - 0.60) < 0.02


def test_basin_role_boosts_stability():
    """seed_basin_role='basin' gives basin_component=0.9, boosting stability."""
    ctx = harvest_geometric_context(
        character_state={
            "seed_id": "ryuki",
            "drift_score": 0.0,
            "drift_direction": "stable",
            "seed_basin_phi": 0.0,
            "seed_basin_role": "basin",
        },
        tri_mod={"coh": 0.80, "tearing_risk": 0.35},
    )
    assert ctx is not None
    # tear_component = 1.0 - (0.35/0.70) = 0.5
    # stability = 0.6*0.5 + 0.4*0.9 = 0.66
    assert ctx.stability > 0.60


def test_live_social_boosts_resonance():
    """live_social=True should raise social_resonance above 0.5 default."""
    ctx = harvest_geometric_context(
        character_state={"seed_id": "ryuki", "drift_score": 0.0,
                         "drift_direction": "stable", "seed_basin_phi": 0.0,
                         "seed_basin_role": "plateau"},
        live_social=True,
    )
    assert ctx is not None
    assert ctx.social_resonance > 0.5


def test_all_fields_bounded():
    """All fields should be in [0.0, 1.0] regardless of extreme inputs."""
    ctx = harvest_geometric_context(
        character_state={
            "seed_id": "ryuki",
            "drift_score": -1.0,
            "drift_direction": "away_seed",
            "seed_basin_phi": -1.0,
            "seed_basin_role": "ridge",
        },
        tri_mod={"coh": 0.50, "tearing_risk": 0.90, "survival_steps": 5.0},
        live_social=True,
    )
    assert ctx is not None
    for field_name in ("coherence", "stability", "identity_lock",
                       "ambiguity_tolerance", "social_resonance"):
        val = getattr(ctx, field_name)
        assert 0.0 <= val <= 1.0, f"{field_name}={val} out of bounds"
