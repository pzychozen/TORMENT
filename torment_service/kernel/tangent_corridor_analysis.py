"""Compatibility re-exports from offline.corridors.

Functions execute in their owner's namespace. Assigning attributes here
does not change the owner's globals; patch the implementation owner when needed.
"""
from .offline.corridors import (
    np,
    cp_mask_from_phi_indices,
    default_cp_config,
    detect_tangent_corridors,
    cluster_delta_kz,
    cp_split_big_delta_events,
)
