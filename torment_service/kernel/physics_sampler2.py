"""Compatibility re-exports from offline.cp_analysis.

Functions execute in their owner's namespace. Assigning attributes here
does not change the owner's globals; patch the implementation owner when needed.
"""
from .offline.cp_analysis import (
    np,
    estimate_chirality_commit_time,
    cp_mask_from_phi_indices,
    default_cp_config,
    cp_conditioned_masks,
    summarize_cp_conditioned_observables,
    detect_chirality_selection_window,
    plot_flavor_time_series,
    plot_Jeff_vs_time,
)
