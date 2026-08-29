"""Narrow frozen-legacy evidence and typed node/relationship admission boundary.

The package inventories evidence first, then admits only selected ``nodes.jsonl``
current-state candidates through explicit legacy-admission transitions.  It does
not replay legacy history.  Relationship admission is limited to conservative,
stable-ID ``edges.jsonl`` candidates with namespaced endpoint aliases.  Legacy
embedding admission is separately conservative: it preserves only complete
object-revision-linked evidence chains as UNKNOWN, non-usable representations.
It does not admit motifs.
"""

from .inventory import InventoryArtifact, InventorySnapshot, get_inventory, inventory_snapshot
from .admission import (
    LegacyEdgeAdmissionRun,
    LegacyNodeAdmissionRun,
    LegacyObjectAdmissionResult,
    LegacyRelationshipAdmissionResult,
    NativeLegacyObjectAdmissionService,
    NativeLegacyRelationshipAdmissionService,
)
from .representation_admission import (
    LegacyEmbeddingAdmissionRun,
    LegacyRepresentationAdmissionResult,
    NativeLegacyRepresentationAdmissionService,
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
    "LegacyEdgeAdmissionRun",
    "LegacyEmbeddingAdmissionRun",
    "LegacyNodeAdmissionRun",
    "LegacyObjectAdmissionResult",
    "LegacyRelationshipAdmissionResult",
    "LegacyRepresentationAdmissionResult",
    "LegacyArtifact",
    "LegacySnapshotManifest",
    "NativeLegacyObjectAdmissionService",
    "NativeLegacyRelationshipAdmissionService",
    "NativeLegacyRepresentationAdmissionService",
    "SnapshotVerification",
    "create_snapshot_manifest",
    "get_inventory",
    "inventory_snapshot",
    "load_snapshot_manifest",
    "verify_snapshot",
]
