"""Compatibility re-exports from offline.experiments.

Functions execute in their owner's namespace. Assigning attributes here
does not change the owner's globals; patch the implementation owner when needed.
"""
from .offline.experiments import (
    np,
    estimate_chirality_timescale,
    ModelParams,
    ModelState,
    TriOctaPhaseLockModel,
    sample_physics_observables,
    summarize_cp_conditioned_observables,
    plot_flavor_time_series,
    plot_Jeff_vs_time,
    detect_chirality_selection_window,
    cp_mask_from_phi_indices,
    default_cp_config,
    detect_tangent_corridors,
    cluster_delta_kz,
    run_once,
    run_ic_scan,
    strong_delta_sector_histogram,
    analyze_Jeff_coupling,
    run_corridor_spectroscopy_scan,
    run_long_time_stability_test,
    run_noise_robustness_test,
)
