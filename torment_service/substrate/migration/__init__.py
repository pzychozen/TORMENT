"""Inert legacy snapshot evidence inventory boundary.

This package records frozen legacy bytes as evidence only.  It neither resolves
legacy identifiers nor admits any legacy material as native semantic truth.
"""

from .inventory import InventoryArtifact, InventorySnapshot, get_inventory, inventory_snapshot
from .snapshot import (
    LegacyArtifact,
    LegacySnapshotManifest,
    SnapshotVerification,
    create_snapshot_manifest,
    load_snapshot_manifest,
    verify_snapshot,
)

__all__ = [
    "InventoryArtifact",
    "InventorySnapshot",
    "LegacyArtifact",
    "LegacySnapshotManifest",
    "SnapshotVerification",
    "create_snapshot_manifest",
    "get_inventory",
    "inventory_snapshot",
    "load_snapshot_manifest",
    "verify_snapshot",
]
