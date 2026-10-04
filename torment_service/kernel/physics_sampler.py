"""Compatibility re-exports from offline.samplers.

Functions execute in their owner's namespace. Assigning attributes here
does not change the owner's globals; patch the implementation owner when needed.
"""
from .offline.samplers import (
    np,
    compute_jeff_from_omega,
    compute_flavor_probabilities,
    compute_relative_phases,
    compute_cp_like_invariant,
    sample_physics_observables,
    summarize_observables,
    plot_phase_and_cp_distributions,
)
