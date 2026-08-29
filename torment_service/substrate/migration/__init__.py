"""Narrow frozen-legacy evidence and typed migration admission boundary.

The package inventories evidence first, then admits only selected ``nodes.jsonl``
current-state candidates through explicit legacy-admission transitions.  It does
not replay legacy history.  Relationship admission is limited to conservative,
stable-ID ``edges.jsonl`` candidates with namespaced endpoint aliases.  Legacy
embedding admission is separately conservative: it preserves only complete
object-revision-linked evidence chains as UNKNOWN, non-usable representations.
Identity admission recognizes only the current durable workspace-agent
``identity.json`` and workspace ``seed.json`` definition shapes, with no
memory dependency; derived ``character_state.json`` remains evidence.  It does
Motif admission recognizes only the current workspace/domain ``motifs.json``
registry and atomically admits its resolved EID memberships; motif events
remain evidence only.
Deep-memory admission recognizes only selected workspace-agent
``deep_memory/memories.jsonl`` records corroborated by imported source export
markers; it preserves those captures as non-READY representations.
Proposal admission recognizes only frozen ``proposals.jsonl`` submissions and
uses paired proposal-event evidence solely to capture their effective status.
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
from .identity_admission import (
    LegacyIdentityAdmissionResult,
    LegacyIdentityAdmissionRun,
    NativeLegacyIdentityAdmissionService,
)
from .motif_admission import (
    LegacyMotifAdmissionResult,
    LegacyMotifAdmissionRun,
    LegacyMotifMembershipResult,
    NativeLegacyMotifAdmissionService,
)
from .deep_memory_admission import (
    LegacyDeepMemoryAdmissionResult,
    LegacyDeepMemoryAdmissionRun,
    NativeLegacyDeepMemoryAdmissionService,
)
from .proposal_admission import (
    LegacyProposalAdmissionResult,
    LegacyProposalAdmissionRun,
    NativeLegacyProposalAdmissionService,
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
    "LegacyDeepMemoryAdmissionResult",
    "LegacyDeepMemoryAdmissionRun",
    "LegacyIdentityAdmissionResult",
    "LegacyIdentityAdmissionRun",
    "LegacyMotifAdmissionResult",
    "LegacyMotifAdmissionRun",
    "LegacyMotifMembershipResult",
    "LegacyProposalAdmissionResult",
    "LegacyProposalAdmissionRun",
    "LegacyNodeAdmissionRun",
    "LegacyObjectAdmissionResult",
    "LegacyRelationshipAdmissionResult",
    "LegacyRepresentationAdmissionResult",
    "LegacyArtifact",
    "LegacySnapshotManifest",
    "NativeLegacyObjectAdmissionService",
    "NativeLegacyIdentityAdmissionService",
    "NativeLegacyMotifAdmissionService",
    "NativeLegacyRelationshipAdmissionService",
    "NativeLegacyRepresentationAdmissionService",
    "NativeLegacyDeepMemoryAdmissionService",
    "NativeLegacyProposalAdmissionService",
    "SnapshotVerification",
    "create_snapshot_manifest",
    "get_inventory",
    "inventory_snapshot",
    "load_snapshot_manifest",
    "verify_snapshot",
]
