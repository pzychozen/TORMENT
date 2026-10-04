"""Compatibility imports for deterministic saved-history observables.

Implementations live in observables (triad/history metrics) and offline (RSB
analysis). Re-exports are the actual owner functions; existing callers may
continue importing them here. NumPy's ``np`` name and EPS remain available,
including through wildcard imports. No explicit __all__ restricts that surface.

Cubic-J KEEP_SEPARATE: this J helper accepts reshapeable three-element input;
the cognitive path has a different strict-unpack contract. They intentionally
remain separate, with no shared replacement or cognitive_core change.
"""
import numpy as np

from .observables.chirality import (
    EPS,
    compute_jeff_from_omega,
    compute_jeff_series,
    chirality_sign,
    count_sign_flips,
    estimate_chirality_commit_time,
    jeff_radius_stats,
)
from .observables.recursive_velocity import (
    vrec_entropy,
    vrec_geom_direction,
)
from .observables.chirality import estimate_chirality_timescale
from .observables.z_geometry import estimate_z_stabilization_time
from .offline.rsb_observables import compute_spectral_energy_series
from .observables.recursive_velocity import (
    _wrap_angle_pi,
    compute_recursive_velocity_geom,
    compute_recursive_velocity,
)
from .offline.rsb_classification import classify_run
from .offline.rsb_observables import (
    compute_dominant_band_series,
    compute_spectral_entropy_series,
    compute_rsb_observables,
)
from .offline.rsb_analysis import (
    analyze_rsb_history,
    summarize_rsb_seed,
    format_rsb_seed_summary,
)
