"""Narrow frozen-legacy evidence and typed current-node admission boundary.

The package inventories evidence first, then admits only selected ``nodes.jsonl``
current-state candidates through explicit legacy-admission transitions.  It does
not replay legacy history or admit relationships, representations, or aliases
other than namespaced EID aliases for those admitted objects.
"""

from .inventory import InventoryArtifact, InventorySnapshot, get_inventory, inventory_snapshot
from .admission import (
    LegacyNodeAdmissionRun,
    LegacyObjectAdmissionResult,
    NativeLegacyObjectAdmissionService,
)
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
    "LegacyNodeAdmissionRun",
    "LegacyObjectAdmissionResult",
    "LegacyArtifact",
    "LegacySnapshotManifest",
    "NativeLegacyObjectAdmissionService",
    "SnapshotVerification",
    "create_snapshot_manifest",
    "get_inventory",
    "inventory_snapshot",
    "load_snapshot_manifest",
    "verify_snapshot",
]
