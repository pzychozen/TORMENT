"""Recoverable P3 source admission before the existing root B3/B4 normalizer.

The root normalizer intentionally starts after B1/B2.  This module supplies
the missing, narrowly bounded source-admission carrier for P3: it captures
only declared source evidence into external snapshots, records the selected
snapshot identities atomically, runs the established B1 and B2 services, and
then constructs an ordinary :class:`RootNormalizationRequest` for the
existing B3/B4 coordinator.

The carrier is evidence, not deployment authority.  Its one record is
deliberately external to ``data_root`` and contains no selector, cutover, or
progress-ledger state.  It retains only the snapshot selection and the B1/B2
identities needed to recover an interrupted P3 without minting new snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from ..canonical_intent import canonical_intent_text
from ..character_seed_witness import (
    CharacterSeedWitnessRefused,
    read_legacy_character_seed_witness_from_frozen_bytes,
)
from ..errors import (
    SubstrateConfigurationError,
    SubstrateEvidenceIntegrityMismatch,
    SubstrateSnapshotManifestError,
)
from ..ids import native_id_from_bytes, native_id_to_bytes
from ..runtime_binding import NativeRepresentationLane
if TYPE_CHECKING:
    from ..corrective_freeze_packet import (
        MetadataLessPerEidEvidence,
        RootSourceScopePlan,
        SourceArtifactPresence,
    )
from .explicit_source_evidence import (
    EvidencePresenceExpectation,
    EvidenceSemanticRole,
    ExplicitSourceEvidence,
    ExplicitSourceEvidenceDrift,
    resolve_explicit_source_evidence_path,
)
from .metadata_less_per_eid_legacy_source import qualify_metadata_less_per_eid_legacy_source
from .admission import NativeLegacyObjectAdmissionService
from .motif_admission import NativeLegacyMotifAdmissionService
from .rehearsal import MigrationRehearsalConfig, NativeLegacyMigrationRehearsal
from .partial_motif_authority import (
    MotifSemanticDisposition,
    NativePartialMotifAuthorityRetentionService,
    PartialMotifAuthorityCertification,
    PartialMotifAuthorityRefused,
    PartialMotifRetentionRequest,
    certify_partial_motif,
    classify_frozen_motifs,
    continuation_summary,
    write_or_reload_continuation,
)
from .root_admission_description import (
    MaterializedScopePosture,
    RootNativeProductionAdmissionDescription,
    RootRepresentationDisposition,
)
from .root_normalization import (
    MetadataLessB3BDispatch,
    RootB2CertifiedRefusalDisposition,
    RootB4CertifiedRefusalDisposition,
    RootNormalizationRequest,
    RootNormalizationScopeInput,
)
from .root_scope import RootScopeKey, RootScopeKind
from .runtime_motif_projection import MigrationRuntimeMotifProjectionRequest
from .runtime_motif_regeometry_projection import MigrationRuntimeMotifRegeometryProjectionRequest
from .runtime_normalization import (
    MigrationRuntimeNormalizationRequest,
    NativeMigrationRuntimeNormalizationService,
)
from .character_seed_normalization import (
    CHARACTER_SEED_NORMALIZATION_OPERATION_KIND,
    CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE,
    MigrationCharacterSeedNormalizationRequest,
    NativeMigrationCharacterSeedNormalizationService,
)
from .root_p3_character_witness_continuation import (
    RootP3CharacterDomainCandidateEvidence,
    RootP3CharacterDomainDerivation,
    RootP3CharacterWitnessContinuationRefused,
    RootP3CharacterWitnessInput,
    RootP3ExternalOwnerObservationAuthority,
    select_or_recover_character_continuation,
    validate_character_witness_inputs,
)
from .runtime_readiness import (
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    LegacyVectorStrategy,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
)
from .runtime_reembedding_bootstrap import MigrationRuntimeReembeddingBootstrapRequest
from .runtime_representation_bootstrap import MigrationRuntimeRepresentationBootstrapRequest
from .runtime_zero_member_motif_projection import MigrationRuntimeZeroMemberMotifProjectionRequest
from .snapshot import (
    complete_snapshot_manifest,
    create_snapshot_manifest,
    load_snapshot_manifest,
    verify_snapshot,
)
from .workspace_runtime_readiness import (
    NativePostWriteQualificationConfiguration,
    WorkspaceNativeEmbedderIdentity,
)


_RECORD_NAME = "p3_source_admission_carrier.json"
_RECORD_SCHEMA = "TORMENT_ROOT_P3_SOURCE_ADMISSION_CARRIER"
_RECORD_VERSION = 1
_REFUSAL_EVIDENCE_NAME = "p3_b2_refused_source_semantic_gap_evidence_set.json"
_REFUSAL_CERTIFICATE_NAME = "p3_b2_refused_source_semantic_gap_certificate.json"
_TERMINAL_EVIDENCE_NAME = "p3_terminal_disposition_evidence_set_e.json"
_REFUSAL_OPERATION_KIND = "P3_B2_REFUSED_SOURCE_SEMANTIC_GAP"
_REFUSAL_CODE = "B2_REFUSED_SOURCE_SEMANTIC_GAP"
_B4_REFUSAL_OPERATION_KIND = "P3_B4_REFUSED_MEMBER_SEMANTIC_GAP"
_B4_REFUSAL_CODE = "B4_REFUSED_MEMBER_SEMANTIC_GAP"
_COMPLETION_ALLOWED_ROLES = frozenset({
    EvidenceSemanticRole.WORKSPACE_META,
    EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
    EvidenceSemanticRole.LEGACY_REPRESENTATION,
})


def _corrective_freeze_types():
    """Load the corrective-freeze-owned runtime classes only after import init."""

    from ..corrective_freeze_packet import (
        MetadataLessPerEidEvidence,
        RootSourceScopePlan,
        SourceArtifactPresence,
    )
    return MetadataLessPerEidEvidence, RootSourceScopePlan, SourceArtifactPresence


class RootP3SourceAdmissionRefused(SubstrateConfigurationError):
    """The P3 source-admission carrier cannot prove an exact input."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class RootP3SourceAdmissionInterruptionPoint(StrEnum):
    """Focused qualification seams; never production semantic inputs."""

    AFTER_SNAPSHOT_SELECTION = "AFTER_SNAPSHOT_SELECTION"
    AFTER_B1 = "AFTER_B1"


class RootP3SourceAdmissionInterrupted(RuntimeError):
    """Test-only interruption after durable carrier evidence."""

    def __init__(self, point: RootP3SourceAdmissionInterruptionPoint) -> None:
        self.point = point
        super().__init__(f"forced root P3 source-admission interruption at {point.value}")


@dataclass(frozen=True)
class RootP3ScopeBinding:
    """One P1-established namespace binding consumed by P3 B1/B2 only."""

    scope_key: RootScopeKey
    scope_plan: MigrationRuntimeScopePlan
    unknown_semantic_scope_id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise ValueError("scope_key must be RootScopeKey")
        if not isinstance(self.scope_plan, MigrationRuntimeScopePlan):
            raise ValueError("scope_plan must be MigrationRuntimeScopePlan")
        if not isinstance(self.unknown_semantic_scope_id, UUID):
            raise ValueError("unknown_semantic_scope_id must be UUID")
        if _scope_key_from_plan(self.scope_plan) != self.scope_key:
            raise ValueError("scope_plan must match scope_key")


@dataclass(frozen=True)
class RootP3CertifiedRefusalSourceMember:
    """One frozen-source identity authorized for terminal B2 refusal.

    This deliberately contains no successor-core object or revision ID.  B1
    replay creates those native identities afresh; the member selects only the
    frozen source row whose current B1 binding must later be recorded.
    """

    scope_key: RootScopeKey
    legacy_source_namespace_id: UUID
    eid: int
    selected_raw_row_sha256: str
    nodes_source_artifact_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope_key, RootScopeKey):
            raise ValueError("refusal source member scope_key must be RootScopeKey")
        if not isinstance(self.legacy_source_namespace_id, UUID):
            raise ValueError("refusal source member namespace must be UUID")
        if not isinstance(self.eid, int) or isinstance(self.eid, bool) or self.eid < 0:
            raise ValueError("refusal source member eid must be non-negative")
        for value, label in (
            (self.selected_raw_row_sha256, "selected_raw_row_sha256"),
            (self.nodes_source_artifact_sha256, "nodes_source_artifact_sha256"),
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"refusal source member {label} must be SHA-256")
            try:
                int(value, 16)
            except ValueError as exc:
                raise ValueError(f"refusal source member {label} must be SHA-256") from exc

    @property
    def identity_payload(self) -> dict[str, object]:
        return {
            "scope_key": self.scope_key.identity_payload(),
            "legacy_source_namespace_id": str(self.legacy_source_namespace_id),
            "eid": self.eid,
            "selected_raw_row_sha256": self.selected_raw_row_sha256,
            "nodes_source_artifact_sha256": self.nodes_source_artifact_sha256,
        }


@dataclass(frozen=True)
class RootP3SourceAdmissionRequest:
    """One external P3A carrier request, bounded to recovered P1/P2 facts."""

    data_root: str | Path
    native_core_database_path: str | Path
    expected_native_core_id: UUID
    description: RootNativeProductionAdmissionDescription
    source_scope_plans: tuple[RootSourceScopePlan, ...]
    scope_bindings: tuple[RootP3ScopeBinding, ...]
    unknown_identity_evidence: tuple[MetadataLessPerEidEvidence, ...]
    carrier_directory: str | Path
    operation_key: str
    qualification_embedder_identity: WorkspaceNativeEmbedderIdentity
    b3b_embedder: object
    post_write_configurations: tuple[NativePostWriteQualificationConfiguration, ...] = ()
    predecessor_carrier_record_path: str | Path | None = None
    character_observation_authority: RootP3ExternalOwnerObservationAuthority | None = None
    character_witness_inputs: tuple[RootP3CharacterWitnessInput, ...] = ()
    character_continuation_carrier_directory: str | Path | None = None
    partial_authority_continuation_directory: str | Path | None = None
    recovered_p2_explicit_source_manifest_digest: str | None = None
    certified_refusal_source_members: tuple[RootP3CertifiedRefusalSourceMember, ...] = ()

    def __post_init__(self) -> None:
        MetadataLessPerEidEvidence, RootSourceScopePlan, _SourceArtifactPresence = _corrective_freeze_types()
        root = _directory(self.data_root, "data_root")
        core = Path(self.native_core_database_path).expanduser().resolve()
        if not core.is_file():
            raise ValueError("native_core_database_path must name an existing database")
        if not isinstance(self.expected_native_core_id, UUID):
            raise ValueError("expected_native_core_id must be UUID")
        if not isinstance(self.description, RootNativeProductionAdmissionDescription):
            raise ValueError("description must be RootNativeProductionAdmissionDescription")
        if self.description.target_representation_lane != self.qualification_embedder_identity_to_lane:
            raise ValueError("qualification embedder identity must match the root target lane")
        if not callable(getattr(self.b3b_embedder, "embed", None)):
            raise ValueError("b3b_embedder must provide embed")
        if not isinstance(self.operation_key, str) or not self.operation_key or len(self.operation_key) > 160:
            raise ValueError("operation_key must be bounded non-empty text")
        if not isinstance(self.source_scope_plans, tuple) or any(
            not isinstance(item, RootSourceScopePlan) for item in self.source_scope_plans
        ):
            raise ValueError("source_scope_plans must be typed")
        if not isinstance(self.scope_bindings, tuple) or any(
            not isinstance(item, RootP3ScopeBinding) for item in self.scope_bindings
        ):
            raise ValueError("scope_bindings must be typed")
        if not isinstance(self.unknown_identity_evidence, tuple) or any(
            not isinstance(item, MetadataLessPerEidEvidence) for item in self.unknown_identity_evidence
        ):
            raise ValueError("unknown_identity_evidence must be typed")
        if not isinstance(self.certified_refusal_source_members, tuple) or any(
            not isinstance(item, RootP3CertifiedRefusalSourceMember)
            for item in self.certified_refusal_source_members
        ):
            raise ValueError("certified_refusal_source_members must be typed")
        if not isinstance(self.post_write_configurations, tuple) or any(
            not isinstance(item, NativePostWriteQualificationConfiguration)
            for item in self.post_write_configurations
        ):
            raise ValueError("post_write_configurations must be typed")
        if not isinstance(self.character_witness_inputs, tuple) or any(
            not isinstance(item, RootP3CharacterWitnessInput) for item in self.character_witness_inputs
        ):
            raise ValueError("character_witness_inputs must be typed")
        if self.character_observation_authority is not None and not isinstance(
            self.character_observation_authority, RootP3ExternalOwnerObservationAuthority,
        ):
            raise ValueError("character_observation_authority must be typed")
        recovered_manifest_digest = self.recovered_p2_explicit_source_manifest_digest
        if recovered_manifest_digest is not None:
            if (
                not isinstance(recovered_manifest_digest, str)
                or len(recovered_manifest_digest) != 64
                or recovered_manifest_digest != self.description.explicit_source_manifest.digest
            ):
                raise ValueError("recovered P2 manifest digest must exactly bind the description manifest")
            try:
                int(recovered_manifest_digest, 16)
            except ValueError as exc:
                raise ValueError("recovered P2 manifest digest must be SHA-256 hex") from exc
        carrier = Path(self.carrier_directory).expanduser().resolve()
        if carrier == root or root in carrier.parents:
            raise ValueError("carrier_directory must resolve outside data_root")
        if not carrier.parent.is_dir():
            raise ValueError("carrier_directory parent must already exist")
        predecessor = self.predecessor_carrier_record_path
        if predecessor is not None:
            if not isinstance(predecessor, (str, Path)) or not str(predecessor).strip():
                raise ValueError("predecessor_carrier_record_path must be an explicit path when supplied")
            predecessor_path = Path(predecessor).expanduser().resolve()
            if not predecessor_path.is_file() or predecessor_path.is_symlink():
                raise ValueError("predecessor_carrier_record_path must name an existing regular record")
            if carrier in predecessor_path.parents:
                raise ValueError("completion carrier must be separate from its predecessor carrier")
        character_carrier = self.character_continuation_carrier_directory
        if character_carrier is not None:
            if not isinstance(character_carrier, (str, Path)) or not str(character_carrier).strip():
                raise ValueError("character_continuation_carrier_directory must be an explicit path")
            character_path = Path(character_carrier).expanduser().resolve()
            if character_path == root or root in character_path.parents or character_path == carrier or (
                character_path in carrier.parents or carrier in character_path.parents
            ):
                raise ValueError("Character continuation carrier must be separate from P3 source evidence")
            if not character_path.parent.is_dir():
                raise ValueError("character_continuation_carrier_directory parent must already exist")
        if self.character_witness_inputs and self.character_continuation_carrier_directory is None:
            raise ValueError("Character witness inputs require a separate continuation carrier")
        if self.character_observation_authority is not None and self.character_continuation_carrier_directory is None:
            raise ValueError("Character authority requires a separate continuation carrier")
        partial_carrier = self.partial_authority_continuation_directory
        if partial_carrier is not None:
            if not isinstance(partial_carrier, (str, Path)) or not str(partial_carrier).strip():
                raise ValueError("partial_authority_continuation_directory must be an explicit path")
            partial_path = Path(partial_carrier).expanduser().resolve()
            if (
                partial_path == root or root in partial_path.parents or partial_path == carrier
                or partial_path in carrier.parents or carrier in partial_path.parents
            ):
                raise ValueError("partial authority continuation must be outside and separate from P3 carrier")
            if not partial_path.parent.is_dir():
                raise ValueError("partial authority continuation parent must already exist")
        source_by_key = {item.scope_key: item for item in self.source_scope_plans}
        bindings_by_key = {item.scope_key: item for item in self.scope_bindings}
        declared = {
            item.scope_key: item
            for workspace in self.description.workspace_plans
            for item in workspace.runtime_scopes
        }
        if (
            len(source_by_key) != len(self.source_scope_plans)
            or len(bindings_by_key) != len(self.scope_bindings)
            or set(source_by_key) != set(declared)
            or set(bindings_by_key) != set(declared)
        ):
            raise ValueError("P3 source plans and bindings must exactly cover declared runtime scopes")
        for key, declared_plan in declared.items():
            source = source_by_key[key]
            binding = bindings_by_key[key]
            if (
                source.materialization_posture != declared_plan.materialization_posture
                or source.representation_disposition != declared_plan.representation_disposition
                or source.target_representation_lane != self.description.target_representation_lane
                or binding.scope_plan.motif_domain_id != source.motif_domain_id
            ):
                raise ValueError("P3 source plan or namespace binding disagrees with root description")
        unknown = {item.scope_key for item in self.unknown_identity_evidence}
        expected_unknown = {
            key for key, item in source_by_key.items()
            if item.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY
        }
        if unknown != expected_unknown:
            raise ValueError("metadata-less evidence must exactly cover UNKNOWN_IDENTITY scopes")
        if len({(item.scope_key, item.eid) for item in self.unknown_identity_evidence}) != len(
            self.unknown_identity_evidence
        ):
            raise ValueError("metadata-less evidence must have unique scope/EID pairs")
        refusal_keys = {
            (item.scope_key, item.legacy_source_namespace_id, item.eid)
            for item in self.certified_refusal_source_members
        }
        if len(refusal_keys) != len(self.certified_refusal_source_members):
            raise ValueError("certified refusal source members must have unique scope/namespace/EID keys")
        for member in self.certified_refusal_source_members:
            binding = bindings_by_key.get(member.scope_key)
            if binding is None or binding.scope_plan.legacy_source_namespace_id != member.legacy_source_namespace_id:
                raise ValueError("certified refusal source member must match its P1 source namespace")
            node_entries = [
                entry for entry in self.description.explicit_source_manifest.entries
                if entry.scope_key == member.scope_key
                and entry.semantic_role is EvidenceSemanticRole.NODES
                and entry.presence_expectation is EvidencePresenceExpectation.EXPECTED_PRESENT
            ]
            if len(node_entries) != 1 or node_entries[0].sha256_hex != member.nodes_source_artifact_sha256:
                raise ValueError("certified refusal source member must bind declared nodes evidence")

    @property
    def root(self) -> Path:
        return Path(self.data_root).expanduser().resolve()

    @property
    def carrier_root(self) -> Path:
        return Path(self.carrier_directory).expanduser().resolve()

    @property
    def record_path(self) -> Path:
        return self.carrier_root / _RECORD_NAME

    @property
    def predecessor_record_path(self) -> Path | None:
        if self.predecessor_carrier_record_path is None:
            return None
        return Path(self.predecessor_carrier_record_path).expanduser().resolve()

    @property
    def character_continuation_carrier_root(self) -> Path | None:
        if self.character_continuation_carrier_directory is None:
            return None
        return Path(self.character_continuation_carrier_directory).expanduser().resolve()

    @property
    def partial_authority_continuation_root(self) -> Path | None:
        if self.partial_authority_continuation_directory is None:
            return None
        return Path(self.partial_authority_continuation_directory).expanduser().resolve()

    @property
    def qualification_embedder_identity_to_lane(self) -> NativeRepresentationLane:
        identity = self.qualification_embedder_identity
        lane = self.description.target_representation_lane
        if (identity.provider, identity.model, identity.dim) != (
            lane.provider, lane.model, lane.dimension,
        ):
            raise ValueError("qualification embedder identity must match the root target lane")
        return lane


@dataclass(frozen=True)
class RootP3SourceAdmissionResult:
    """Exact B1/B2 carrier facts and the newly bound existing B3/B4 request."""

    carrier_record_path: Path
    normalization_request: RootNormalizationRequest
    snapshot_scope_count: int
    b1_memory_count: int
    b2_memory_count: int
    b2_refused_memory_count: int
    child_request_counts: tuple[tuple[str, int], ...]
    b1m_identity_universe_digest: str | None = None
    b1f_total_motif_count: int = 0
    b1f_exact_motif_count: int = 0
    b1f_partial_motif_count: int = 0
    b1f_zero_member_motif_count: int = 0
    partial_authority_continuation_path: Path | None = None
    final_evidence_set_e_digest: str | None = None
    root_disposition_closed: bool = False
    completion_class: str = "BLOCKED"


class NativeRootP3SourceAdmissionService:
    """Compose existing capture/B1/B2 owners; it grants no P2/P4 authority."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("root P3 source admission requires an open SQLite connection")
        self._connection = connection

    def admit(
        self,
        request: RootP3SourceAdmissionRequest,
        *,
        _test_interrupt_after: RootP3SourceAdmissionInterruptionPoint | None = None,
        _test_lose_response_after_b2: bool = False,
    ) -> RootP3SourceAdmissionResult:
        if not isinstance(request, RootP3SourceAdmissionRequest):
            raise ValueError("request must be RootP3SourceAdmissionRequest")
        if _test_interrupt_after is not None and not isinstance(
            _test_interrupt_after, RootP3SourceAdmissionInterruptionPoint,
        ):
            raise ValueError("_test_interrupt_after must be RootP3SourceAdmissionInterruptionPoint")

        # This recheck is deliberately immediately before any carrier selection
        # or B1 write.  It reads only the P2-bound explicit source proposition.
        _verify_p2_bound_source(request)
        record = _select_or_recover_record(self._connection, request)
        character_bindings = _validated_character_bindings(request, record)
        if _test_interrupt_after is RootP3SourceAdmissionInterruptionPoint.AFTER_SNAPSHOT_SELECTION:
            raise RootP3SourceAdmissionInterrupted(_test_interrupt_after)

        ordered = _ordered_scope_entries(record)
        # B1M is deliberately root-wide and object-only.  Motif files are
        # present in frozen snapshots, but this pass never calls a motif owner.
        for entry in ordered:
            _run_b1m(self._connection, request, entry)
        b1m = _seal_b1m_identity_universe(self._connection, request, record)
        record["b1m"] = b1m
        _write_record(request.record_path, record)
        if _test_interrupt_after is RootP3SourceAdmissionInterruptionPoint.AFTER_B1:
            raise RootP3SourceAdmissionInterrupted(_test_interrupt_after)

        # B1F is only legal after the complete B1M identity universe is
        # sealed.  It yields an exact runtime motif or an external partial
        # authority certificate, never a mixed motif.
        _revalidate_b1m_identity_universe(self._connection, request, record)
        b1f, partial_certifications = _run_b1f(
            self._connection, request, record, b1m["identity_universe_digest"],
        )
        record["b1f"] = b1f
        if b1f["blocking_motif_count"]:
            _write_record(request.record_path, record)
            raise RootP3SourceAdmissionRefused("P3_B1F_BLOCKING_QUARANTINE")
        # Ordinary B1 evidence (representations, identity, and relationships)
        # is resumed only after B1F.  Motif derivation remains excluded: B1F
        # already owns the complete exact/partial terminal disposition.
        refresh_b1_scopes = {
            _scope_key_from_payload(entry.get("scope_key"))
            for entry in ordered
            if _b1_evidence_refresh_required(entry.get("b1"), record)
        }
        for entry in ordered:
            if _scope_key_from_payload(entry.get("scope_key")) in refresh_b1_scopes:
                _run_b1_nonmotif_evidence(self._connection, request, entry)
        for entry in ordered:
            if _scope_key_from_payload(entry.get("scope_key")) not in refresh_b1_scopes:
                continue
            previous_b1 = entry.get("b1")
            memories = _read_b1_memory_evidence(
                self._connection, request, entry, character_bindings,
            )
            completion = record.get("carrier_completion")
            if isinstance(completion, dict) and completion.get("predecessor_b1_revalidation_pending"):
                _revalidate_preexisting_b1_memory(previous_b1, memories)
            scope_dispositions = _scope_b1f_dispositions(entry, b1f)
            entry["b1"] = {
                "memories": memories,
                "motifs": [
                    item["exact_motif"] for item in scope_dispositions
                    if item.get("exact_motif") is not None
                ],
                "motif_dispositions": scope_dispositions,
            }
        completion = record.get("carrier_completion")
        if isinstance(completion, dict) and completion.get("previous_b1_scope_reuse_candidate_count", 0):
            completion["previous_b1_scope_reuse"] = "QUALIFIED"
            completion["predecessor_b1_revalidation_pending"] = False
        _write_record(request.record_path, record)
        _require_refusal_b1_source_set_closure(request, record)

        partial_continuation: Path | None = None
        if partial_certifications:
            if request.partial_authority_continuation_root is None:
                raise RootP3SourceAdmissionRefused("P3_PARTIAL_AUTHORITY_CONTINUATION_REQUIRED")
            predecessor_digest = (
                _file_digest(request.predecessor_record_path)
                if request.predecessor_record_path is not None
                else _digest({"law": "P3_INITIAL_PARTIAL_CONTINUATION_V1", "record": record["root_description_digest"]})
            )
            try:
                partial_continuation = write_or_reload_continuation(
                    directory=request.partial_authority_continuation_root,
                    predecessor_carrier_sha256=predecessor_digest,
                    b1m_identity_universe_digest=b1m["identity_universe_digest"],
                    b1f_disposition_digest=b1f["disposition_digest"],
                    certifications=partial_certifications,
                )
            except PartialMotifAuthorityRefused as exc:
                raise RootP3SourceAdmissionRefused(exc.code) from exc

        if character_bindings:
            for entry in ordered:
                scope = _scope_key_from_payload(entry.get("scope_key"))
                expected_character_eids: set[int] | None = None
                if scope in character_bindings:
                    expected_character_eids = _expected_character_b1_eids(
                        self._connection, request, entry, character_bindings,
                    )
                _validate_character_b1_eid_agreement(
                    entry, character_bindings,
                    expected_character_eids=expected_character_eids,
                )
        try:
            character_witnesses = select_or_recover_character_continuation(
                directory=request.character_continuation_carrier_root,
                predecessor_record_path=request.record_path,
                predecessor_identity_digest=_character_predecessor_identity_digest(record),
                snapshot_scope_count=len(_ordered_scope_entries(record)),
                snapshot_identity_digest=_snapshot_identity_digest(record),
                authority=request.character_observation_authority,
                bindings=character_bindings,
                scope_facts=_character_scope_facts(request),
                domain_derivations={
                    key: binding.domain_derivation
                    for key, binding in character_bindings.items()
                },
            )
        except RootP3CharacterWitnessContinuationRefused as exc:
            raise RootP3SourceAdmissionRefused(exc.code) from exc

        lose_response = _test_lose_response_after_b2
        refusal_certification = _prepare_source_semantic_gap_certification(
            self._connection, request, record,
        )
        if refusal_certification is not None:
            record["b2_refusal_certification"] = {
                key: refusal_certification[key]
                for key in (
                    "evidence_path", "final_evidence_set_e_digest", "certificate_path",
                    "certificate_digest", "exception_set_digest",
                )
            }
            _write_record(request.record_path, record)
        for entry in ordered:
            _revalidate_b1m_identity_universe(self._connection, request, record)
            source = _source_plan_for_key(request, _scope_key_from_payload(entry.get("scope_key")))
            memories, _motifs = _carrier_b1_evidence(entry, source, character_witnesses)
            b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
            b2_by_eid = _carrier_b2_memory_evidence(b2)
            memory_eids = {item["eid"] for item in memories}
            if not set(b2_by_eid).issubset(memory_eids):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_EID_SET_MISMATCH")
            for memory in memories:
                eid = memory["eid"]
                if eid in b2_by_eid:
                    continue
                base = _b2_normalization_request(request, entry, memory)
                if memory["normalization_kind"] == "CHARACTER_SEED":
                    witness = character_witnesses.get(
                        _scope_key_from_payload(entry.get("scope_key")),
                    )
                    if witness is None or eid not in witness.seed_eids:
                        raise RootP3SourceAdmissionRefused("P3_CARRIER_CHARACTER_WITNESS_REQUIRED")
                    result = NativeMigrationCharacterSeedNormalizationService(
                        self._connection
                    ).normalize_character_seed(
                        MigrationCharacterSeedNormalizationRequest(base, witness),
                        _test_lose_response_after_commit=lose_response,
                    )
                elif memory["normalization_kind"] == "ORDINARY":
                    result = NativeMigrationRuntimeNormalizationService(
                        self._connection
                    ).normalize_legacy_core_memory(
                        base, _test_lose_response_after_commit=lose_response,
                    )
                elif memory["normalization_kind"] == _REFUSAL_CODE:
                    if refusal_certification is None:
                        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_CERTIFICATE_REQUIRED")
                    operation_id = _record_source_semantic_gap_refusal(
                        self._connection, request, entry, memory, refusal_certification,
                    )
                    b2.setdefault("memories", []).append({
                        "eid": eid,
                        "disposition": _REFUSAL_CODE,
                        "certificate_digest": refusal_certification["certificate_digest"],
                        "receipt_operation_id": str(operation_id),
                    })
                    b2["memories"] = sorted(b2["memories"], key=lambda item: item["eid"])
                    b2_by_eid = _carrier_b2_memory_evidence(b2)
                    _write_record(request.record_path, record)
                    continue
                else:  # _carrier_b1_memory_evidence has already made this unreachable.
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_KIND_INVALID")
                lose_response = False
                b2.setdefault("memories", []).append({
                    "eid": eid,
                    "disposition": "ADMITTED",
                    "r2_revision_id": str(result.revision_id),
                })
                b2["memories"] = sorted(b2["memories"], key=lambda item: item["eid"])
                b2_by_eid = _carrier_b2_memory_evidence(b2)
                _write_record(request.record_path, record)
            _require_b2_closure(memories, b2_by_eid)

        _revalidate_b1m_identity_universe(self._connection, request, record)
        b4_routes = _prepare_or_revalidate_b4_routes(
            self._connection, request, record, refusal_certification,
        )
        if record.get("b4_routes") != b4_routes:
            record["b4_routes"] = b4_routes
            _write_record(request.record_path, record)
        normalization_request = _build_normalization_request(
            request, record, character_witnesses, partial_continuation,
        )
        actual = p3_child_request_counts(normalization_request.scope_inputs)
        expected = _carrier_evidence_child_request_counts(request, record, character_witnesses)
        if actual != expected:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_CHILD_COUNT_DRIFT")
        terminal_evidence = _prepare_or_revalidate_terminal_disposition_evidence(
            request, record, b1f, actual, refusal_certification,
        )
        if record.get("terminal_disposition_evidence") != terminal_evidence:
            record["terminal_disposition_evidence"] = terminal_evidence
            _write_record(request.record_path, record)
        memory_count = sum(
            len(_require_list(_require_mapping(item.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED").get("memories"), "P3_CARRIER_B1_MEMORY_EVIDENCE_REQUIRED"))
            for item in ordered
        )
        return RootP3SourceAdmissionResult(
            carrier_record_path=request.record_path,
            normalization_request=normalization_request,
            snapshot_scope_count=len(ordered),
            b1_memory_count=memory_count,
            b2_memory_count=sum(
                sum(
                    item["disposition"] == "ADMITTED"
                    for item in _carrier_b2_memory_evidence(
                        _require_mapping(item.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
                    ).values()
                )
                for item in ordered
            ),
            b2_refused_memory_count=sum(
                sum(
                    item["disposition"] == _REFUSAL_CODE
                    for item in _carrier_b2_memory_evidence(
                        _require_mapping(item.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
                    ).values()
                )
                for item in ordered
            ),
            child_request_counts=tuple(sorted(actual.items())),
            b1m_identity_universe_digest=b1m["identity_universe_digest"],
            b1f_total_motif_count=b1f["total_motif_count"],
            b1f_exact_motif_count=b1f["exact_motif_count"],
            b1f_partial_motif_count=b1f["partial_motif_count"],
            b1f_zero_member_motif_count=b1f["zero_member_motif_count"],
            partial_authority_continuation_path=partial_continuation,
            final_evidence_set_e_digest=terminal_evidence["final_evidence_set_e_digest"],
            root_disposition_closed=True,
            completion_class="P3_DISPOSITION_CLOSED_WITH_CERTIFIED_EXCEPTIONS",
        )


def pre_b1_p3_scope_shape_counts(
    source_scope_plans: tuple[RootSourceScopePlan, ...],
    unknown_identity_evidence: tuple[MetadataLessPerEidEvidence, ...],
) -> dict[str, int]:
    """Return pre-B1 structural facts, never executable child-operation counts."""

    MetadataLessPerEidEvidence, RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    if not isinstance(source_scope_plans, tuple) or any(
        not isinstance(item, RootSourceScopePlan) for item in source_scope_plans
    ):
        raise ValueError("source_scope_plans must be typed")
    if not isinstance(unknown_identity_evidence, tuple) or any(
        not isinstance(item, MetadataLessPerEidEvidence) for item in unknown_identity_evidence
    ):
        raise ValueError("unknown_identity_evidence must be typed")
    result = {
        "target_compatible_memory_scope_count": 0,
        "ordinary_reembed_memory_scope_count": 0,
        "unknown_identity_evidence_count": len(unknown_identity_evidence),
        "motif_present_scope_count": 0,
    }
    for plan in source_scope_plans:
        if plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if plan.representation_disposition is RootRepresentationDisposition.TARGET_COMPATIBLE:
                result["target_compatible_memory_scope_count"] += 1
            elif plan.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                continue
            else:
                result["ordinary_reembed_memory_scope_count"] += 1
        if plan.motif_presence is SourceArtifactPresence.PRESENT:
            result["motif_present_scope_count"] += 1
    return result


def p3_child_request_counts(
    scope_inputs: tuple[RootNormalizationScopeInput, ...],
) -> dict[str, int]:
    """Count the exact B3/B4 inputs produced by this carrier."""

    if not isinstance(scope_inputs, tuple) or any(
        not isinstance(item, RootNormalizationScopeInput) for item in scope_inputs
    ):
        raise ValueError("scope_inputs must be typed")
    result = {
        "b3a": 0, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 0, "b4p": 0,
    }
    for item in scope_inputs:
        result["b3a"] += len(item.b3a_requests)
        result["ordinary_b3b"] += len(item.b3b_requests)
        result["metadata_less_b3b"] += len(item.metadata_less_b3b_dispatches)
        result["b4a"] += len(item.b4a_requests)
        result["b4b"] += len(item.b4b_requests)
        result["b4c"] += len(item.b4c_requests)
        result["b4p"] += len(item.b4p_requests)
        refused = len(item.b4_refused_motif_dispositions)
        if refused:
            result["b4_refused_member_semantic_gap"] = (
                result.get("b4_refused_member_semantic_gap", 0) + refused
            )
    result["total_b3b"] = result["ordinary_b3b"] + result["metadata_less_b3b"]
    return result


def request_binding(request: RootP3SourceAdmissionRequest, entry: dict[str, Any]) -> RootP3ScopeBinding:
    key = _scope_key_from_payload(entry.get("scope_key"))
    matches = [item for item in request.scope_bindings if item.scope_key == key]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_BINDING_MISSING")
    return matches[0]


def _verify_p2_bound_source(request: RootP3SourceAdmissionRequest) -> None:
    # A copied P3 recovery can be run after an earlier, separately recorded
    # Envelope-C opening.  Its recovered digest binds exactly the description
    # manifest and deliberately avoids a second contact with the live root;
    # all subsequent source bytes still come from the immutable P3 snapshots.
    if request.recovered_p2_explicit_source_manifest_digest is not None:
        if (
            request.recovered_p2_explicit_source_manifest_digest
            != request.description.explicit_source_manifest.digest
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_RECOVERED_MANIFEST_BINDING_MISMATCH")
        return
    try:
        request.description.explicit_source_manifest.verify(data_root=request.root)
    except (ExplicitSourceEvidenceDrift, OSError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_MANIFEST_DRIFT") from exc


def _select_or_recover_record(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
) -> dict[str, Any]:
    path = request.record_path
    if path.exists():
        record = _load_record(path, request)
        _verify_record_snapshots(connection, record, request)
        return record
    if request.predecessor_record_path is not None:
        return _complete_predecessor_record(connection, request)
    p1_namespace_keys = {
        binding.scope_key: _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        for binding in request.scope_bindings
    }
    carrier = request.carrier_root
    if carrier.exists():
        if not carrier.is_dir() or carrier.is_symlink() or any(carrier.iterdir()):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_DESTINATION_NOT_EMPTY")
    else:
        carrier.mkdir()
    (carrier / "snapshots").mkdir()
    (carrier / "manifests").mkdir()
    scopes: list[dict[str, Any]] = []
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    for index, binding in enumerate(sorted(request.scope_bindings, key=lambda item: item.scope_key.canonical_key)):
        token = f"{index:03d}-{_scope_token(binding.scope_key)}"
        snapshot_root = carrier / "snapshots" / token
        manifest_path = carrier / "manifests" / f"{token}.json"
        _create_scope_snapshot(
            request,
            source_by_key[binding.scope_key],
            binding,
            p1_namespace_keys[binding.scope_key],
            snapshot_root,
            manifest_path,
        )
        manifest = load_snapshot_manifest(manifest_path)
        scopes.append({
            "scope_key": binding.scope_key.identity_payload(),
            "scope_plan": binding.scope_plan.intent(),
            "unknown_semantic_scope_id": str(binding.unknown_semantic_scope_id),
            "legacy_source_namespace_id": str(binding.scope_plan.legacy_source_namespace_id),
            "legacy_source_namespace_key": manifest.legacy_source_namespace_key,
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "manifest_digest": _file_digest(manifest_path),
            "b1": None,
            "b2": {"memories": []},
        })
    record: dict[str, Any] = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
        "scopes": scopes,
    }
    _write_record(path, record)
    return record


def _complete_predecessor_record(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
) -> dict[str, Any]:
    """Create a separate carrier that only completes omitted source evidence.

    The first carrier, its snapshots, manifests, and B1 facts stay immutable.
    A successor carrier can share a snapshot identity only through the strict
    snapshot completion law, which retains every predecessor artifact exactly.
    Scopes without an omission continue to reference their predecessor
    snapshots rather than manufacturing a non-strict "completion" manifest.
    """

    predecessor_path = request.predecessor_record_path
    assert predecessor_path is not None
    predecessor, predecessor_digest = _load_predecessor_record(predecessor_path)
    predecessor_core_id = _verify_predecessor_record(connection, predecessor, request)
    predecessor_core_superseded = predecessor_core_id != request.expected_native_core_id
    carrier = request.carrier_root
    if carrier.exists():
        if not carrier.is_dir() or carrier.is_symlink() or any(carrier.iterdir()):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_DESTINATION_NOT_EMPTY")
    else:
        carrier.mkdir()
    (carrier / "completed_snapshots").mkdir()
    (carrier / "completed_manifests").mkdir()
    predecessor_by_key = {
        _scope_key_from_payload(item.get("scope_key")): item
        for item in _require_list(predecessor.get("scopes"), "P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    }
    p1_namespace_keys = {
        binding.scope_key: _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        for binding in request.scope_bindings
    }
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    scopes: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    inherited: list[dict[str, Any]] = []
    inherited_b1_reuse_candidate_count = 0
    for index, binding in enumerate(sorted(request.scope_bindings, key=lambda item: item.scope_key.canonical_key)):
        predecessor_entry = predecessor_by_key.get(binding.scope_key)
        if predecessor_entry is None:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
        token = f"{index:03d}-{_scope_token(binding.scope_key)}"
        snapshot_root, manifest_path, completion = _complete_scope_snapshot(
            request=request,
            source_plan=source_by_key[binding.scope_key],
            predecessor_entry=predecessor_entry,
            destination=carrier / "completed_snapshots" / token,
            manifest_destination=carrier / "completed_manifests" / f"{token}.json",
        )
        manifest = load_snapshot_manifest(manifest_path)
        scope = {
            "scope_key": binding.scope_key.identity_payload(),
            "scope_plan": binding.scope_plan.intent(),
            "unknown_semantic_scope_id": str(binding.unknown_semantic_scope_id),
            "legacy_source_namespace_id": str(binding.scope_plan.legacy_source_namespace_id),
            "legacy_source_namespace_key": p1_namespace_keys[binding.scope_key],
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "manifest_digest": _file_digest(manifest_path),
            # Preserve the predecessor's B1 evidence only as a candidate for
            # strict B1M revalidation.  The successor never treats the old
            # motif-presence closure as authoritative; B1F replaces it.
            # An old-core B1 carrier is retained source evidence, never an
            # object/revision carrier for a distinct corrected P1 core.  The
            # successor must therefore recapture B1 against its own R1 facts.
            "b1": None if predecessor_core_superseded else predecessor_entry.get("b1"),
            "b2": {"memories": []},
        }
        scopes.append(scope)
        (completed if completion else inherited).append({
            "scope_key": binding.scope_key.identity_payload(),
            "snapshot_root": str(snapshot_root),
            "manifest_path": str(manifest_path),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
        })
        if not completion and not predecessor_core_superseded and predecessor_entry.get("b1") is not None:
            inherited_b1_reuse_candidate_count += 1
    record: dict[str, Any] = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
        "scopes": scopes,
        "carrier_completion": {
            "predecessor_record_path": str(predecessor_path),
            "predecessor_record_digest": predecessor_digest,
            **({
                "predecessor_native_core_id": str(predecessor_core_id),
                "successor_native_core_id": str(request.expected_native_core_id),
                "predecessor_core_disposition": "PRESERVED_SUPERSEDED_PREDECESSOR_EVIDENCE",
            } if predecessor_core_superseded else {}),
            "completed_snapshots": completed,
            "completed_manifests": [item["manifest_path"] for item in completed],
            "inherited_snapshots": inherited,
            "previous_b1_scope_reuse_candidate_count": inherited_b1_reuse_candidate_count,
            "predecessor_b1_revalidation_pending": inherited_b1_reuse_candidate_count > 0,
        },
    }
    _write_record(request.record_path, record)
    return record


def _load_predecessor_record(path: Path) -> tuple[dict[str, Any], str]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_UNREADABLE") from exc
    if not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_SHAPE_INVALID")
    payload = outer.get("payload")
    if (
        outer.get("schema") != _RECORD_SCHEMA
        or outer.get("version") != _RECORD_VERSION
        or not isinstance(payload, dict)
        or outer.get("digest") != _digest(payload)
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_RECORD_INTEGRITY_INVALID")
    return payload, str(outer["digest"])


def _verify_predecessor_record(
    connection: sqlite3.Connection,
    predecessor: dict[str, Any],
    request: RootP3SourceAdmissionRequest,
) -> UUID:
    try:
        predecessor_core_id = UUID(predecessor["expected_native_core_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_CORE_INVALID") from exc
    if predecessor_core_id != request.expected_native_core_id:
        # P1 corrective supersession retains the old carrier and its frozen
        # snapshots as evidence, but the successor's distinct P1 core is the
        # only object/revision authority for resumed B1/B2 work.
        for binding in request.scope_bindings:
            _require_p1_motif_alias_separation(connection, binding.scope_plan)
    scopes = _require_list(predecessor.get("scopes"), "P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    keys = {
        _scope_key_from_payload(item.get("scope_key"))
        for item in scopes
        if isinstance(item, dict)
    }
    if len(keys) != len(scopes) or keys != {item.scope_key for item in request.scope_bindings}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
    for entry in scopes:
        if not isinstance(entry, dict):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SCOPE_SET_INVALID")
        binding = request_binding(request, entry)
        expected_key = _p1_legacy_source_namespace_key(
            connection, binding.scope_plan.legacy_source_namespace_id,
        )
        root = Path(entry.get("snapshot_root", "")).expanduser().resolve()
        manifest_path = Path(entry.get("manifest_path", "")).expanduser().resolve()
        try:
            manifest = load_snapshot_manifest(manifest_path)
            verify_snapshot(snapshot_root=root, manifest=manifest)
        except (SubstrateConfigurationError, OSError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SNAPSHOT_INVALID") from exc
        if (
            manifest.legacy_source_namespace_id != binding.scope_plan.legacy_source_namespace_id
            or manifest.legacy_source_namespace_key != expected_key
            or entry.get("legacy_snapshot_id") != str(manifest.legacy_snapshot_id)
            or entry.get("manifest_digest") != _file_digest(manifest_path)
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_PREDECESSOR_SNAPSHOT_BINDING_MISMATCH")
    return predecessor_core_id


def _complete_scope_snapshot(
    *,
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
    predecessor_entry: dict[str, Any],
    destination: Path,
    manifest_destination: Path,
) -> tuple[Path, Path, bool]:
    predecessor_root = Path(predecessor_entry.get("snapshot_root", "")).expanduser().resolve()
    predecessor_manifest_path = Path(predecessor_entry.get("manifest_path", "")).expanduser().resolve()
    predecessor_manifest = load_snapshot_manifest(predecessor_manifest_path)
    selected = _snapshot_sources_for_scope(request, source_plan)
    predecessor_locators = {item.observed_relative_locator for item in predecessor_manifest.artifacts}
    additions: list[tuple[ExplicitSourceEvidence, Path]] = []
    for evidence, relative in selected:
        if relative.as_posix() in predecessor_locators:
            continue
        if evidence.semantic_role not in _COMPLETION_ALLOWED_ROLES:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_UNAPPROVED_ADDITION")
        additions.append((evidence, relative))
    if not additions:
        return predecessor_root, predecessor_manifest_path, False
    if destination.exists() or manifest_destination.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_DESTINATION_EXISTS")
    temporary = destination.parent / f".{destination.name}.pending"
    if temporary.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_INCOMPLETE_CAPTURE")
    temporary.mkdir()
    try:
        for artifact in predecessor_manifest.artifacts:
            source = predecessor_root / artifact.observed_relative_locator
            _require_regular_source_inside_root(predecessor_root, source)
            target = temporary / artifact.observed_relative_locator
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        for evidence, relative in selected:
            source = resolve_explicit_source_evidence_path(data_root=request.root, evidence=evidence)
            _require_regular_source_inside_root(request.root, source)
            payload = source.read_bytes()
            if len(payload) != evidence.byte_length or hashlib.sha256(payload).hexdigest() != evidence.sha256_hex:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SOURCE_EVIDENCE_DRIFT")
            target = temporary / relative
            if target.exists():
                if target.read_bytes() != payload:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_DRIFT")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        completed = complete_snapshot_manifest(
            predecessor=predecessor_manifest,
            snapshot_root=temporary,
            manifest_path=manifest_destination,
            allowed_additional_locators=tuple(relative.as_posix() for _, relative in additions),
        )
        verify_snapshot(snapshot_root=temporary, manifest=completed)
        os.replace(temporary, destination)
    except Exception:
        raise
    return destination, manifest_destination, True


def _create_scope_snapshot(
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
    binding: RootP3ScopeBinding,
    legacy_source_namespace_key: str,
    destination: Path,
    manifest_path: Path,
) -> None:
    if destination.exists() or manifest_path.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_DESTINATION_EXISTS")
    temporary = destination.parent / f".{destination.name}.pending"
    temporary_manifest = manifest_path.parent / f".{manifest_path.stem}.pending.json"
    if temporary.exists() or temporary_manifest.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_INCOMPLETE_SNAPSHOT_CAPTURE")
    temporary.mkdir()
    try:
        for evidence, relative in _snapshot_sources_for_scope(request, source_plan):
            source = resolve_explicit_source_evidence_path(data_root=request.root, evidence=evidence)
            _require_regular_source_inside_root(request.root, source)
            payload = source.read_bytes()
            if len(payload) != evidence.byte_length or hashlib.sha256(payload).hexdigest() != evidence.sha256_hex:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_DRIFT")
            target = temporary / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        manifest = create_snapshot_manifest(
            snapshot_root=temporary,
            manifest_path=temporary_manifest,
            legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
            legacy_source_namespace_key=legacy_source_namespace_key,
            capture_label=f"root P3 source admission {binding.scope_key.canonical_key}",
        )
        verify_snapshot(snapshot_root=temporary, manifest=manifest)
        os.replace(temporary, destination)
        os.replace(temporary_manifest, manifest_path)
    except Exception:
        # Do not remove incomplete captures: absence of an authoritative record
        # plus residue must fail closed rather than silently choose new IDs.
        raise


def _snapshot_sources_for_scope(
    request: RootP3SourceAdmissionRequest,
    source_plan: RootSourceScopePlan,
) -> tuple[tuple[ExplicitSourceEvidence, Path], ...]:
    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    scope = source_plan.scope_key
    manifest = request.description.explicit_source_manifest
    selected: list[tuple[ExplicitSourceEvidence, Path]] = []
    roles = {
        EvidenceSemanticRole.NODES,
        EvidenceSemanticRole.EDGES,
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
        EvidenceSemanticRole.LEGACY_REPRESENTATION,
        EvidenceSemanticRole.MOTIFS,
        EvidenceSemanticRole.WORKSPACE_META,
    }
    for item in manifest.entries:
        if item.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT:
            continue
        include = item.scope_key == scope
        if (
            item.scope_key is None
            and item.owner_boundary.workspace_id == scope.workspace_id
            and item.semantic_role is EvidenceSemanticRole.WORKSPACE_META
            and (
                source_plan.motif_presence is SourceArtifactPresence.PRESENT
                or (
                    source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH
                    and source_plan.representation_disposition
                    is not RootRepresentationDisposition.UNKNOWN_IDENTITY
                )
            )
        ):
            include = True
        if not include:
            continue
        if item.semantic_role not in roles:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_UNSUPPORTED_DECLARED_SOURCE_ROLE")
        relative = _snapshot_relative_path(item, scope)
        selected.append((item, relative))
    destinations = [relative.as_posix() for _, relative in selected]
    if len(set(destinations)) != len(destinations):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_DESTINATION_AMBIGUOUS")
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH and not any(
        item.semantic_role is EvidenceSemanticRole.NODES for item, _ in selected
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_SOURCE_MISSING")
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT and not any(
        item.semantic_role is EvidenceSemanticRole.MOTIFS for item, _ in selected
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_SOURCE_MISSING")
    return tuple(sorted(selected, key=lambda item: item[1].as_posix()))


def _snapshot_relative_path(evidence: ExplicitSourceEvidence, scope: RootScopeKey) -> Path:
    if evidence.semantic_role in {
        EvidenceSemanticRole.NODES,
        EvidenceSemanticRole.EDGES,
        EvidenceSemanticRole.EMBEDDING_MANIFEST,
        EvidenceSemanticRole.EMBEDDING_SHARD_OR_MAP,
        EvidenceSemanticRole.LEGACY_REPRESENTATION,
    }:
        if evidence.owner_boundary.scope_key != scope:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_SOURCE_BOUNDARY_MISMATCH")
        return Path(*evidence.canonical_locator.split("/"))
    if evidence.semantic_role is EvidenceSemanticRole.MOTIFS:
        domain = evidence.owner_boundary.domain_id
        if domain is None or domain != scope.domain_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_SOURCE_BOUNDARY_MISMATCH")
        return Path("workspaces", scope.workspace_id, "domains", domain, *evidence.canonical_locator.split("/"))
    if evidence.semantic_role is EvidenceSemanticRole.WORKSPACE_META:
        if evidence.owner_boundary.workspace_id != scope.workspace_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_WORKSPACE_SOURCE_BOUNDARY_MISMATCH")
        return Path("workspaces", scope.workspace_id, *evidence.canonical_locator.split("/"))
    raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_ROLE_UNSUPPORTED")


def _run_b1m(connection: sqlite3.Connection, request: RootP3SourceAdmissionRequest, entry: dict[str, Any]) -> None:
    """Run only current-state legacy node admission for one B1M scope."""

    binding = request_binding(request, entry)
    source = _source_plan_for_key(request, binding.scope_key)
    if source.materialization_posture is not MaterializedScopePosture.MEMORY_GRAPH:
        return
    NativeLegacyObjectAdmissionService(connection).admit_nodes_current_state(
        snapshot_root=Path(entry["snapshot_root"]),
        manifest_path=Path(entry["manifest_path"]),
        idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
        object_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
        unknown_semantic_scope_id=binding.unknown_semantic_scope_id,
    )


def _run_b1(connection: sqlite3.Connection, request: RootP3SourceAdmissionRequest, entry: dict[str, Any]) -> None:
    """Compatibility seam for older focused tests; production uses B1M/B1F."""

    binding = request_binding(request, entry)
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=Path(entry["snapshot_root"]),
        manifest_path=Path(entry["manifest_path"]),
        config=MigrationRehearsalConfig(
            native_core_id=request.expected_native_core_id,
            idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
            object_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
            relationship_identity_namespace_id=binding.scope_plan.membership_identity_namespace_id,
            unknown_semantic_scope_id=binding.unknown_semantic_scope_id,
            eligible_member_source_namespace_ids=_eligible_member_source_namespace_ids(request, binding),
        ),
    )


def _run_b1_nonmotif_evidence(
    connection: sqlite3.Connection, request: RootP3SourceAdmissionRequest, entry: dict[str, Any],
) -> None:
    """Resume established non-motif B1 evidence after root B1F."""

    binding = request_binding(request, entry)
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=Path(entry["snapshot_root"]),
        manifest_path=Path(entry["manifest_path"]),
        config=MigrationRehearsalConfig(
            native_core_id=request.expected_native_core_id,
            idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
            object_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
            relationship_identity_namespace_id=binding.scope_plan.membership_identity_namespace_id,
            unknown_semantic_scope_id=binding.unknown_semantic_scope_id,
            eligible_member_source_namespace_ids=None,
            include_motif_derivation=False,
        ),
    )


def _seal_b1m_identity_universe(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
) -> dict[str, Any]:
    rows = _b1m_identity_universe_rows(connection, request, record)
    evidence = {
        "law": "P3_B1M_IDENTITY_UNIVERSE_DIGEST_V1",
        "scope_closure": len(_ordered_scope_entries(record)),
        "legacy_core_node_count": len(rows),
        "eid_alias_count": len(rows),
        "identity_universe_digest": _digest(rows),
    }
    prior = record.get("b1m")
    if prior is not None and prior != evidence:
        raise RootP3SourceAdmissionRefused("P3_B1M_IDENTITY_UNIVERSE_DRIFT")
    return evidence


def _revalidate_b1m_identity_universe(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
) -> None:
    prior = _require_mapping(record.get("b1m"), "P3_B1M_IDENTITY_UNIVERSE_REQUIRED")
    current = _seal_b1m_identity_universe(connection, request, record)
    if current != prior:
        raise RootP3SourceAdmissionRefused("P3_B1M_IDENTITY_UNIVERSE_DRIFT")


def _b1m_identity_universe_rows(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    result: list[dict[str, Any]] = []
    for entry in _ordered_scope_entries(record):
        key = _scope_key_from_payload(entry.get("scope_key"))
        if source_by_key[key].materialization_posture is not MaterializedScopePosture.MEMORY_GRAPH:
            continue
        binding = request_binding(request, entry)
        rows = connection.execute(
            """SELECT a.alias_value,a.object_id,o.object_kind,o.identity_namespace_id
                 FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
                WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
                  AND o.object_kind='LEGACY_CORE_NODE'
                ORDER BY CAST(a.alias_value AS INTEGER),a.alias_value""",
            (native_id_to_bytes(binding.scope_plan.legacy_source_namespace_id),),
        ).fetchall()
        if not rows:
            raise RootP3SourceAdmissionRefused("P3_B1M_MEMORY_ALIAS_CLOSURE_MISMATCH")
        for alias_value, object_id, object_kind, identity_namespace_id in rows:
            try:
                eid = int(alias_value)
            except (TypeError, ValueError) as exc:
                raise RootP3SourceAdmissionRefused("P3_B1M_MEMORY_ALIAS_INVALID") from exc
            if str(eid) != alias_value or eid < 0:
                raise RootP3SourceAdmissionRefused("P3_B1M_MEMORY_ALIAS_INVALID")
            result.append({
                "scope_key": key.identity_payload(),
                "legacy_snapshot_id": entry["legacy_snapshot_id"],
                "legacy_source_namespace_id": str(binding.scope_plan.legacy_source_namespace_id),
                "eid": eid,
                "object_id": str(native_id_from_bytes(object_id)),
                "object_kind": object_kind,
                "identity_namespace_id": str(native_id_from_bytes(identity_namespace_id)),
            })
    result.sort(key=lambda item: (
        canonical_intent_text(item["scope_key"]), item["legacy_source_namespace_id"], item["eid"],
    ))
    if len({(item["legacy_source_namespace_id"], item["eid"]) for item in result}) != len(result):
        raise RootP3SourceAdmissionRefused("P3_B1M_MEMORY_ALIAS_DUPLICATE")
    return result


def _run_b1f(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
    identity_universe_digest: str,
) -> tuple[dict[str, Any], tuple[PartialMotifAuthorityCertification, ...]]:
    """Classify every source motif against the sealed root alias universe."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    per_scope: list[dict[str, Any]] = []
    certifications: list[PartialMotifAuthorityCertification] = []
    counts = {item.value: 0 for item in MotifSemanticDisposition}
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        source_plan = _source_plan_for_key(request, binding.scope_key)
        dispositions: list[dict[str, Any]] = []
        if source_plan.motif_presence is SourceArtifactPresence.PRESENT:
            eligible = _eligible_member_source_namespace_ids(request, binding)
            try:
                classified = classify_frozen_motifs(
                    connection,
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    scope_key=binding.scope_key.identity_payload(),
                    eligible_member_source_namespace_ids=eligible,
                )
            except PartialMotifAuthorityRefused as exc:
                raise RootP3SourceAdmissionRefused(exc.code) from exc
            normal = NativeLegacyMotifAdmissionService(connection).admit_motifs_current_state(
                snapshot_root=Path(entry["snapshot_root"]),
                manifest_path=Path(entry["manifest_path"]),
                idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
                motif_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
                membership_identity_namespace_id=binding.scope_plan.membership_identity_namespace_id,
                unknown_semantic_scope_id=binding.unknown_semantic_scope_id,
                eligible_member_source_namespace_ids=eligible,
            )
            normal_by_id: dict[str, Any] = {}
            for item in normal.results:
                if item.motif_id is not None:
                    if item.motif_id in normal_by_id:
                        raise RootP3SourceAdmissionRefused("P3_B1F_NORMAL_ADMISSION_DUPLICATE")
                    normal_by_id[item.motif_id] = item
            for classified_item in classified:
                if classified_item.source is None:
                    counts[MotifSemanticDisposition.BLOCKING_QUARANTINE.value] += 1
                    dispositions.append({
                        "motif_id": None,
                        "domain_id": None,
                        "disposition": MotifSemanticDisposition.BLOCKING_QUARANTINE.value,
                        "blocking_code": classified_item.blocking_code,
                    })
                    continue
                frozen = classified_item.source
                normal_item = normal_by_id.get(frozen.motif_id)
                if normal_item is None:
                    raise RootP3SourceAdmissionRefused("P3_B1F_NORMAL_ADMISSION_MISSING")
                item: dict[str, Any] = {
                    "motif_id": frozen.motif_id,
                    "domain_id": frozen.domain_id,
                    "disposition": classified_item.disposition.value,
                    "source_motif_payload_digest": frozen.source_motif_payload_digest,
                    "source_member_count": len(frozen.ordered_occurrences),
                }
                counts[classified_item.disposition.value] += 1
                if classified_item.disposition in {
                    MotifSemanticDisposition.EXACT_ADMITTED,
                    MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED,
                }:
                    if normal_item.admission_status != "ADMITTED" or normal_item.motif_object_id is None or normal_item.motif_revision_id is None:
                        raise RootP3SourceAdmissionRefused("P3_B1F_EXACT_ADMISSION_MISMATCH")
                    if len(normal_item.memberships) != len(frozen.ordered_occurrences):
                        raise RootP3SourceAdmissionRefused("P3_B1F_EXACT_MEMBERSHIP_MISMATCH")
                    item["exact_motif"] = {
                        "runtime_motif_id": frozen.motif_id,
                        "source_object_id": str(normal_item.motif_object_id),
                        "r1_revision_id": str(normal_item.motif_revision_id),
                    }
                elif classified_item.disposition is MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED:
                    if normal_item.admission_status == "ADMITTED" or normal_item.motif_object_id is not None or normal_item.memberships:
                        raise RootP3SourceAdmissionRefused("P3_PARTIAL_MIXED_NATIVE_MEMBERSHIP")
                    quarantine = connection.execute(
                        "SELECT quarantine_record_id FROM legacy_quarantine_records WHERE admission_record_id=?",
                        (native_id_to_bytes(normal_item.admission_record_id),),
                    ).fetchone()
                    certificate = certify_partial_motif(
                        classified_item,
                        b1m_identity_universe_digest=identity_universe_digest,
                        normal_admission_record_id=normal_item.admission_record_id,
                        normal_quarantine_record_id=None if quarantine is None else native_id_from_bytes(quarantine[0]),
                    )
                    certifications.append(certificate)
                    item["partial_reason"] = classified_item.partial_reason.value if classified_item.partial_reason else None
                    item["partial_certification_digest"] = certificate.digest
                else:
                    item["blocking_code"] = classified_item.blocking_code
                dispositions.append(item)
        per_scope.append({
            "scope_key": binding.scope_key.identity_payload(),
            "motif_dispositions": sorted(dispositions, key=lambda item: (str(item["motif_id"]), str(item["domain_id"]))),
        })
    ordered_scopes = sorted(per_scope, key=lambda item: canonical_intent_text(item["scope_key"]))
    payload = {
        "law": "P3_B1F_TERMINAL_MOTIF_DISPOSITION_V1",
        "scope_dispositions": ordered_scopes,
        "total_motif_count": sum(counts.values()),
        "exact_motif_count": counts[MotifSemanticDisposition.EXACT_ADMITTED.value],
        "partial_motif_count": counts[MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED.value],
        "zero_member_motif_count": counts[MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value],
        "blocking_motif_count": counts[MotifSemanticDisposition.BLOCKING_QUARANTINE.value],
    }
    payload["disposition_digest"] = _digest(payload)
    return payload, tuple(sorted(certifications, key=lambda item: item.digest))


def _scope_b1f_dispositions(entry: dict[str, Any], b1f: dict[str, Any]) -> list[dict[str, Any]]:
    key = entry.get("scope_key")
    matches = [item for item in _require_list(b1f.get("scope_dispositions"), "P3_B1F_SCOPE_DISPOSITIONS_REQUIRED") if item.get("scope_key") == key]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_B1F_SCOPE_DISPOSITION_MISSING")
    values = _require_list(matches[0].get("motif_dispositions"), "P3_B1F_MOTIF_DISPOSITIONS_REQUIRED")
    return [dict(item) for item in values]


def _revalidate_preexisting_b1_memory(
    previous: object,
    current: list[dict[str, Any]],
) -> None:
    """Reuse old scope evidence only when its memory facts remain exact."""

    if previous is None:
        return
    prior = _require_mapping(previous, "P3_CARRIER_PREVIOUS_B1_EVIDENCE_INVALID")
    prior_memories = list(_carrier_b1_memory_evidence(prior))
    if prior_memories != current:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_PREVIOUS_B1_MEMORY_REVALIDATION_FAILED")


def _b1_evidence_refresh_required(previous: object, record: dict[str, Any]) -> bool:
    """A recovered successor preserves already-written current B1 evidence."""

    completion = record.get("carrier_completion")
    if isinstance(completion, dict) and completion.get("predecessor_b1_revalidation_pending"):
        return True
    return not isinstance(previous, dict) or "motif_dispositions" not in previous


def _validated_character_bindings(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
):
    """Compose only P2-anchored descriptors against frozen private P3 facts."""

    try:
        return validate_character_witness_inputs(
            authority=request.character_observation_authority,
            inputs=request.character_witness_inputs,
            scope_facts=_character_scope_facts(request),
            domain_derivations=_derive_character_domain_derivations(request, record),
        )
    except RootP3CharacterWitnessContinuationRefused as exc:
        raise RootP3SourceAdmissionRefused(exc.code) from exc


def _derive_character_domain_derivations(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
) -> dict[RootScopeKey, RootP3CharacterDomainDerivation]:
    """Derive Character-only motif domains from P2 and already-frozen P3 bytes.

    A private scope's ordinary ``motif_domain_id`` is deliberately not an input
    to this law.  The candidate universe is the intersection of the
    Envelope-C manifest and the selected P3 snapshot carrier, then the
    existing complete Character witness is the sole predicate.
    """

    if not request.character_witness_inputs:
        return {}
    entries = _ordered_scope_entries(record)
    by_scope = {
        _scope_key_from_payload(entry.get("scope_key")): entry
        for entry in entries
    }
    result: dict[RootScopeKey, RootP3CharacterDomainDerivation] = {}
    for item in request.character_witness_inputs:
        if item.scope_key in result:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_WITNESS_SCOPE_DUPLICATE")
        private_entry = by_scope.get(item.scope_key)
        if private_entry is None:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_WITNESS_SCOPE_MISSING")
        private_manifest, private_root = _character_snapshot_manifest(private_entry)
        if private_manifest.legacy_source_namespace_id != item.legacy_source_namespace_id:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_WITNESS_NAMESPACE_MISMATCH")
        private_nodes = _character_snapshot_artifact_bytes(
            manifest=private_manifest,
            snapshot_root=private_root,
            locator="nodes.jsonl",
            code="P3_CHARACTER_WITNESS_PRIVATE_NODES_MISSING",
        )
        candidates = _character_domain_candidates(
            request=request, entries_by_scope=by_scope, workspace_id=item.scope_key.workspace_id,
        )
        successful: list[tuple[RootP3CharacterDomainCandidateEvidence, Any]] = []
        for candidate, motif_bytes in candidates:
            try:
                witness = read_legacy_character_seed_witness_from_frozen_bytes(
                    seed_definition_bytes=item.seed_definition_bytes,
                    private_nodes_bytes=private_nodes,
                    motif_bytes=motif_bytes,
                    workspace_id=item.scope_key.workspace_id,
                    agent_id=item.scope_key.agent_id or "",
                    domain_id=candidate.domain_id,
                    requested_seed_id=_character_seed_id_from_descriptor(item.descriptor_payload),
                )
            except CharacterSeedWitnessRefused:
                # A P2/P3-authorized motif source is only a candidate.  The
                # existing Character witness, rather than motif-id coincidence,
                # decides whether that candidate proves the full relationship.
                continue
            successful.append((candidate, witness))
        if not successful:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_WITNESS_DOMAIN_UNRESOLVED")
        if len(successful) != 1:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_WITNESS_DOMAIN_AMBIGUOUS")
        selected, witness = successful[0]
        candidate_evidence = tuple(item[0] for item in candidates)
        result[item.scope_key] = RootP3CharacterDomainDerivation(
            scope_key=item.scope_key,
            domain_id=selected.domain_id,
            candidate_evidence=candidate_evidence,
            candidate_evidence_digest=_digest({
                "law": "UNIQUE_BOUNDED_CHARACTER_WITNESS_DOMAIN_V1",
                "scope_key": item.scope_key.identity_payload(),
                "candidate_evidence": [candidate.identity_payload() for candidate in candidate_evidence],
            }),
            witness_digest=witness.witness_digest,
            freshly_rederived_witness=witness,
        )
    return result


def _character_domain_candidates(
    *, request: RootP3SourceAdmissionRequest, entries_by_scope: dict[RootScopeKey, dict[str, Any]],
    workspace_id: str,
) -> tuple[tuple[RootP3CharacterDomainCandidateEvidence, bytes], ...]:
    """Return exactly the P2∩P3 frozen motif candidates for one workspace."""

    candidates: list[tuple[RootP3CharacterDomainCandidateEvidence, bytes]] = []
    seen_domains: set[str] = set()
    for evidence in request.description.explicit_source_manifest.entries:
        if (
            evidence.semantic_role is not EvidenceSemanticRole.MOTIFS
            or evidence.presence_expectation is not EvidencePresenceExpectation.EXPECTED_PRESENT
            or evidence.owner_boundary.workspace_id != workspace_id
        ):
            continue
        domain_id = evidence.owner_boundary.domain_id
        expected_scope = (
            RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain_id)
            if domain_id is not None else None
        )
        if (
            domain_id is None
            or evidence.scope_key != expected_scope
            or expected_scope not in entries_by_scope
        ):
            continue
        if domain_id in seen_domains:
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_DOMAIN_CANDIDATE_DUPLICATE")
        snapshot_entry = entries_by_scope[expected_scope]
        manifest, root = _character_snapshot_manifest(snapshot_entry)
        expected_locator = _snapshot_relative_path(evidence, expected_scope).as_posix()
        motif_bytes, artifact = _character_snapshot_artifact_bytes_with_identity(
            manifest=manifest,
            snapshot_root=root,
            locator=expected_locator,
            code="P3_CHARACTER_DOMAIN_CANDIDATE_MOTIF_MISSING",
        )
        if (
            artifact.byte_length != evidence.byte_length
            or artifact.digest_hex != evidence.sha256_hex
        ):
            raise RootP3SourceAdmissionRefused("P3_CHARACTER_DOMAIN_CANDIDATE_EVIDENCE_MISMATCH")
        candidates.append((RootP3CharacterDomainCandidateEvidence(
            domain_id=domain_id,
            p2_manifest_evidence_identity_digest=_digest(evidence.identity_payload()),
            p3_snapshot_id=manifest.legacy_snapshot_id,
            p3_motif_artifact_id=artifact.artifact_id,
            p3_motif_artifact_digest=artifact.digest_hex,
        ), motif_bytes))
        seen_domains.add(domain_id)
    return tuple(sorted(candidates, key=lambda item: item[0].domain_id))


def _character_snapshot_manifest(entry: dict[str, Any]):
    try:
        root = Path(entry.get("snapshot_root", "")).expanduser().resolve()
        manifest = load_snapshot_manifest(Path(entry.get("manifest_path", "")).expanduser().resolve())
        verify_snapshot(snapshot_root=root, manifest=manifest)
    except (
        OSError, SubstrateConfigurationError, SubstrateEvidenceIntegrityMismatch,
        SubstrateSnapshotManifestError, ValueError,
    ) as exc:
        raise RootP3SourceAdmissionRefused("P3_CHARACTER_DOMAIN_SNAPSHOT_INVALID") from exc
    if entry.get("legacy_snapshot_id") != str(manifest.legacy_snapshot_id):
        raise RootP3SourceAdmissionRefused("P3_CHARACTER_DOMAIN_SNAPSHOT_IDENTITY_MISMATCH")
    return manifest, root


def _character_snapshot_artifact_bytes(
    *, manifest, snapshot_root: Path, locator: str, code: str,
) -> bytes:
    value, _artifact = _character_snapshot_artifact_bytes_with_identity(
        manifest=manifest, snapshot_root=snapshot_root, locator=locator, code=code,
    )
    return value


def _character_snapshot_artifact_bytes_with_identity(
    *, manifest, snapshot_root: Path, locator: str, code: str,
):
    matches = [item for item in manifest.artifacts if item.observed_relative_locator == locator]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused(code)
    artifact = matches[0]
    try:
        value = (snapshot_root / artifact.observed_relative_locator).read_bytes()
    except OSError as exc:
        raise RootP3SourceAdmissionRefused(code) from exc
    if len(value) != artifact.byte_length or hashlib.sha256(value).hexdigest() != artifact.digest_hex:
        raise RootP3SourceAdmissionRefused("P3_CHARACTER_DOMAIN_CANDIDATE_EVIDENCE_MISMATCH")
    return value, artifact


def _character_seed_id_from_descriptor(value: Any) -> str:
    if not isinstance(value, dict) and not hasattr(value, "get"):
        raise RootP3SourceAdmissionRefused("P3_CHARACTER_DESCRIPTOR_SEED_ID_INVALID")
    seed_id = value.get("seed_id")
    if not isinstance(seed_id, str) or not seed_id:
        raise RootP3SourceAdmissionRefused("P3_CHARACTER_DESCRIPTOR_SEED_ID_INVALID")
    return seed_id


def _character_scope_facts(
    request: RootP3SourceAdmissionRequest,
) -> dict[RootScopeKey, tuple[UUID, str | None]]:
    """The frozen P3 scope topology is the only source for descriptor context."""

    return {
        binding.scope_key: (
            binding.scope_plan.legacy_source_namespace_id,
            _source_plan_for_key(request, binding.scope_key).motif_domain_id,
        )
        for binding in request.scope_bindings
    }


def _character_predecessor_identity_digest(record: dict[str, Any]) -> str:
    """Stable predecessor identity: snapshots and B1, intentionally never B2."""

    scopes: list[dict[str, Any]] = []
    for entry in _ordered_scope_entries(record):
        scopes.append({
            key: entry.get(key) for key in (
                "scope_key", "scope_plan", "unknown_semantic_scope_id",
                "legacy_source_namespace_id", "legacy_source_namespace_key",
                "snapshot_root", "manifest_path", "legacy_snapshot_id", "manifest_digest", "b1",
            )
        })
    return _digest({
        "root_description_digest": record.get("root_description_digest"),
        "explicit_source_manifest_digest": record.get("explicit_source_manifest_digest"),
        "expected_native_core_id": record.get("expected_native_core_id"),
        "operation_key": record.get("operation_key"),
        "carrier_completion": record.get("carrier_completion"),
        "scopes": scopes,
    })


def _snapshot_identity_digest(record: dict[str, Any]) -> str:
    return _digest([
        {
            "scope_key": entry.get("scope_key"),
            "legacy_source_namespace_id": entry.get("legacy_source_namespace_id"),
            "legacy_snapshot_id": entry.get("legacy_snapshot_id"),
            "manifest_digest": entry.get("manifest_digest"),
        }
        for entry in _ordered_scope_entries(record)
    ])


def _b2_normalization_request(
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any], memory: dict[str, Any],
) -> MigrationRuntimeNormalizationRequest:
    binding = request_binding(request, entry)
    return MigrationRuntimeNormalizationRequest(
        snapshot_root=Path(entry["snapshot_root"]),
        manifest_path=Path(entry["manifest_path"]),
        legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
        legacy_source_namespace_id=UUID(entry["legacy_source_namespace_id"]),
        expected_native_core_id=request.expected_native_core_id,
        eid=memory["eid"],
        expected_revision_id=UUID(memory["r1_revision_id"]),
        scope_plans=(binding.scope_plan,),
        idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
        idempotency_key=_stage_key(request, entry, "B2", str(memory["eid"])),
    )


def _eligible_member_source_namespace_ids(
    request: RootP3SourceAdmissionRequest,
    motif_binding: RootP3ScopeBinding,
) -> tuple[UUID, ...]:
    """Return the P3-declared memory-owner universe for one motif workspace.

    Only the frozen request topology is consulted.  No database alias scan can
    discover another workspace or a non-materialized source namespace.
    """
    source_by_key = {item.scope_key: item for item in request.source_scope_plans}
    eligible = [
        binding.scope_plan.legacy_source_namespace_id
        for binding in request.scope_bindings
        if binding.scope_key.workspace_id == motif_binding.scope_key.workspace_id
        and source_by_key[binding.scope_key].materialization_posture
        is MaterializedScopePosture.MEMORY_GRAPH
    ]
    if not eligible:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_MEMBER_SCOPE_UNIVERSE_EMPTY")
    if len(set(eligible)) != len(eligible):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_MEMBER_SCOPE_UNIVERSE_AMBIGUOUS")
    return tuple(sorted(eligible, key=str))


def _read_b1_memory_evidence(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    character_bindings: dict[RootScopeKey, Any],
) -> list[dict[str, Any]]:
    """Read B1 memory evidence only; motif disposition belongs to B1F."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    binding = request_binding(request, entry)
    source_plan = _source_plan_for_key(request, binding.scope_key)
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(
            legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
            expected_native_core_id=request.expected_native_core_id,
            scope_plans=(binding.scope_plan,),
            target_lane=request.description.target_representation_lane,
        )
    )
    memories: list[dict[str, Any]] = []
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
        allowed = {
            ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED,
            ObjectRuntimeReadiness.UNKNOWN_ORIGINAL_PROVENANCE_NORMALIZATION_REQUIRED,
            ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED,
        }
        seen_eids: set[int] = set()
        for item in report.object_items:
            if item.eid is None:
                # Motifs are independently represented in the same frozen
                # snapshot but are not logical memories.  They are explicitly
                # marked evidence-only by the existing readiness owner and
                # are closed below through ``report.motif_items``.
                if (
                    item.readiness is ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT
                    and "OBJECT_KIND_NOT_CORE_RUNTIME_PROFILE" in item.reason_codes
                ):
                    continue
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_EID_INVALID")
            eid = _require_nonnegative_int(item.eid, "P3_CARRIER_MEMORY_B1_EID_INVALID")
            if eid in seen_eids:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_EID_DUPLICATE")
            if not isinstance(item.current_revision_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_REVISION_INVALID")
            character_required = "CHARACTER_NORMALIZATION_WITNESS_REQUIRED" in item.reason_codes
            character_witness = character_bindings.get(binding.scope_key)
            if character_required:
                # Character precedence is deliberate: a seed-shaped row with
                # absent legacy provenance cannot enter the ordinary structural
                # unknown lane, even if some later readiness owner adds it.
                if character_witness is None or eid not in character_witness.witness.seed_eids:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_NOT_NORMALIZABLE")
                normalization_kind = "CHARACTER_SEED"
            elif item.readiness in allowed:
                normalization_kind = "ORDINARY"
            elif (
                item.readiness is ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED
                and item.governance.value == "MISSING_GOVERNANCE"
                and item.lifecycle.value == "UNKNOWN_LIFECYCLE"
            ):
                normalization_kind = _REFUSAL_CODE
            else:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_NOT_NORMALIZABLE")
            seen_eids.add(eid)
            if not isinstance(item.legacy_vector_strategy, LegacyVectorStrategy):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_STRATEGY_INVALID")
            memory = {
                "eid": eid,
                "r1_revision_id": str(item.current_revision_id),
                "legacy_vector_strategy": item.legacy_vector_strategy.value,
                "normalization_kind": normalization_kind,
            }
            if normalization_kind == _REFUSAL_CODE:
                raw = connection.execute(
                    """SELECT payload_text FROM object_revisions
                         WHERE object_id=? AND object_revision_id=? AND revision_ordinal=?""",
                    (native_id_to_bytes(item.object_id), native_id_to_bytes(item.current_revision_id),
                     item.current_revision_ordinal),
                ).fetchone()
                if raw is None or not isinstance(raw[0], str):
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_RAW_ROW_MISSING")
                raw_row_digest = hashlib.sha256(raw[0].encode("utf-8")).hexdigest()
                source_member = _certified_refusal_source_member(
                    request, binding.scope_key, binding.scope_plan.legacy_source_namespace_id, eid,
                )
                if source_member is None:
                    # The readiness predicate is an audit assertion, never a
                    # grant of terminal disposition for a newly appearing row.
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_UNENUMERATED_SOURCE_MEMBER")
                if source_member.selected_raw_row_sha256 != raw_row_digest:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_RAW_ROW_DRIFT")
                memory.update({
                    "object_id": str(item.object_id),
                    "raw_row_digest": raw_row_digest,
                    "source_identity": source_member.identity_payload,
                    "governance_readiness": "NO_EXACT_GOVERNANCE_FACT_FOUND_IN_E",
                    "lifecycle_readiness": "NO_AUTHORITATIVE_LIFECYCLE_FACT_FOUND_IN_E",
                    "provenance_evidence_state": item.provenance.value,
                })
            memories.append(memory)
        memories.sort(key=lambda item: item["eid"])
        if not memories:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_CLOSURE_MISMATCH")
    elif any(item.eid is not None for item in report.object_items):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_EMPTY_SCOPE_CREATED_MEMORY")
    return memories


def _certified_refusal_source_member(
    request: RootP3SourceAdmissionRequest,
    scope_key: RootScopeKey,
    legacy_source_namespace_id: UUID,
    eid: int,
) -> RootP3CertifiedRefusalSourceMember | None:
    matches = [
        item for item in request.certified_refusal_source_members
        if item.scope_key == scope_key
        and item.legacy_source_namespace_id == legacy_source_namespace_id
        and item.eid == eid
    ]
    if len(matches) > 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_ENUMERATION_DUPLICATE")
    return matches[0] if matches else None


def _require_refusal_b1_source_set_closure(
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
) -> None:
    """Prove readiness selected exactly, and only, the frozen refusal census."""

    expected = {
        canonical_intent_text(item.identity_payload)
        for item in request.certified_refusal_source_members
    }
    actual: set[str] = set()
    for entry in _ordered_scope_entries(record):
        scope = _scope_key_from_payload(entry.get("scope_key"))
        namespace_id = _require_uuid(
            entry.get("legacy_source_namespace_id"), "P3_CARRIER_REFUSAL_NAMESPACE_INVALID",
        )
        b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
        for memory in _carrier_b1_memory_evidence(b1):
            if memory["normalization_kind"] != _REFUSAL_CODE:
                continue
            source_identity = _require_mapping(
                memory.get("source_identity"), "P3_CARRIER_REFUSAL_SOURCE_IDENTITY_INVALID",
            )
            member = _certified_refusal_source_member(request, scope, namespace_id, memory["eid"])
            if member is None or source_identity != member.identity_payload:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_SOURCE_IDENTITY_MISMATCH")
            actual.add(canonical_intent_text(source_identity))
    if actual != expected:
        # A listed member whose fresh B1 readiness changed is a contradiction,
        # not an invitation to manufacture a receipt from the old census.
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_B1_READINESS_DRIFT")


def _expected_character_b1_eids(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    character_bindings: dict[RootScopeKey, Any],
) -> set[int]:
    """Read the stable Character B1 expectation for one bound scope.

    Before B2, frozen readiness is the owner of the required Character subset.
    After a resumable B2 plant, that readiness rightly changes; the exact
    persisted ``CHARACTER_SEED_PLANT`` provenance becomes the stable owner of
    the subset instead.  This never promotes a merely authorized seed EID.
    """

    binding = request_binding(request, entry)
    rows = connection.execute(
        """SELECT a.alias_value,op.idempotency_key
             FROM legacy_object_aliases a
             JOIN objects o ON o.object_id=a.object_id
             JOIN object_revisions r
               ON r.object_id=o.object_id AND r.object_revision_id=o.current_revision_id
             JOIN provenance_records p ON p.provenance_id=r.provenance_id
             JOIN operation_outputs out
               ON out.object_id=o.object_id
              AND out.object_revision_id=r.object_revision_id
              AND out.object_revision_ordinal=r.revision_ordinal
             JOIN operations op ON op.operation_id=out.operation_id
            WHERE a.legacy_source_namespace_id=?
              AND a.alias_kind='EID'
              AND p.origin_kind='CHARACTER_SEED_PLANT'
              AND op.operation_kind=?
              AND out.output_role=?
              AND out.output_kind='OBJECT'
            ORDER BY a.alias_value""",
        (
            native_id_to_bytes(binding.scope_plan.legacy_source_namespace_id),
            CHARACTER_SEED_NORMALIZATION_OPERATION_KIND,
            CHARACTER_SEED_NORMALIZATION_OUTPUT_ROLE,
        ),
    ).fetchall()
    persisted: set[int] = set()
    for row in rows:
        if (
            len(row) != 2
            or not isinstance(row[0], str)
            or not row[0].isdigit()
            or not isinstance(row[1], str)
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_CHARACTER_B1_EID_MISMATCH")
        eid = _require_nonnegative_int(int(row[0]), "P3_CARRIER_CHARACTER_B1_EID_MISMATCH")
        if row[1] == _stage_key(request, entry, "B2", str(eid)):
            persisted.add(eid)
    if persisted:
        return persisted
    return {
        item["eid"]
        for item in _read_b1_memory_evidence(connection, request, entry, character_bindings)
        if item["normalization_kind"] == "CHARACTER_SEED"
    }


def _read_b1_evidence(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    character_bindings: dict[RootScopeKey, Any],
) -> dict[str, Any]:
    """Legacy compatibility reader; new production closure uses B1F records."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    binding = request_binding(request, entry)
    source_plan = _source_plan_for_key(request, binding.scope_key)
    memories = _read_b1_memory_evidence(connection, request, entry, character_bindings)
    report = NativeMigrationRuntimeReadinessPreflight(connection).run(
        MigrationRuntimeReadinessRequest(
            legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
            expected_native_core_id=request.expected_native_core_id,
            scope_plans=(binding.scope_plan,),
            target_lane=request.description.target_representation_lane,
        )
    )
    motifs: list[dict[str, Any]] = []
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT:
        if not report.motif_items:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
        seen_runtime_motif_ids: set[str] = set()
        for item in report.motif_items:
            runtime_motif_id = item.runtime_motif_id
            if not isinstance(runtime_motif_id, str) or not runtime_motif_id:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_RUNTIME_ID_INVALID")
            if runtime_motif_id in seen_runtime_motif_ids:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_RUNTIME_ID_DUPLICATE")
            if not isinstance(item.motif_object_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_SOURCE_OBJECT_INVALID")
            if not isinstance(item.current_revision_id, UUID):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_REVISION_INVALID")
            seen_runtime_motif_ids.add(runtime_motif_id)
            motifs.append({
                "runtime_motif_id": runtime_motif_id,
                "source_object_id": str(item.motif_object_id),
                "r1_revision_id": str(item.current_revision_id),
            })
        motifs.sort(key=lambda item: item["runtime_motif_id"])
        if len(motifs) != len(report.motif_items):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
    elif report.motif_items:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNDECLARED_MOTIF_ADMITTED")
    return {"memories": memories, "motifs": motifs}


def _carrier_b1_evidence(
    entry: dict[str, Any], source_plan: RootSourceScopePlan,
    character_witnesses: dict[RootScopeKey, Any],
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    """Validate recovered B1 evidence before it can drive B2/B3/B4 work."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
    memories = _carrier_b1_memory_evidence(b1)
    motifs = _carrier_b1_motif_evidence(b1)
    if source_plan.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
        if not memories:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MEMORY_B1_CLOSURE_MISMATCH")
    elif memories:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_EMPTY_SCOPE_CREATED_MEMORY")
    _validate_character_b1_eid_agreement(entry, character_witnesses)
    if source_plan.motif_presence is SourceArtifactPresence.PRESENT:
        dispositions = _carrier_b1_motif_dispositions(b1)
        if not dispositions:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_CLOSURE_MISMATCH")
        if any(item["disposition"] == MotifSemanticDisposition.BLOCKING_QUARANTINE.value for item in dispositions):
            raise RootP3SourceAdmissionRefused("P3_B1F_BLOCKING_QUARANTINE")
        exact_ids = {
            item["motif_id"] for item in dispositions
            if item["disposition"] in {
                MotifSemanticDisposition.EXACT_ADMITTED.value,
                MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value,
            }
        }
        if exact_ids != {item["runtime_motif_id"] for item in motifs}:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_DISPOSITION_MISMATCH")
    elif motifs or _carrier_b1_motif_dispositions(b1):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNDECLARED_MOTIF_ADMITTED")
    return memories, motifs


def _validate_character_b1_eid_agreement(
    entry: dict[str, Any], character_witnesses: dict[RootScopeKey, Any], *,
    expected_character_eids: set[int] | None = None,
) -> None:
    """Close Character-normalized B1 EIDs against their witness and readiness."""

    b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
    memories = _carrier_b1_memory_evidence(b1)
    scope = _scope_key_from_payload(entry.get("scope_key"))
    candidate = character_witnesses.get(scope)
    witness = candidate.witness if candidate is not None and hasattr(candidate, "witness") else candidate
    character_eids = {item["eid"] for item in memories if item["normalization_kind"] == "CHARACTER_SEED"}
    if witness is None:
        if character_eids:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_CHARACTER_WITNESS_REQUIRED")
    elif not character_eids.issubset(set(witness.seed_eids)):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_CHARACTER_B1_EID_MISMATCH")
    elif expected_character_eids is not None and character_eids != expected_character_eids:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_CHARACTER_B1_EID_MISMATCH")


def _carrier_b1_memory_evidence(b1: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    memories = _require_list(b1.get("memories"), "P3_CARRIER_B1_MEMORY_EVIDENCE_REQUIRED")
    result: list[dict[str, Any]] = []
    seen_eids: set[int] = set()
    for memory in memories:
        eid = _require_nonnegative_int(memory.get("eid"), "P3_CARRIER_B1_MEMORY_EID_INVALID")
        if eid in seen_eids:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_EID_DUPLICATE")
        revision = _require_uuid(memory.get("r1_revision_id"), "P3_CARRIER_B1_MEMORY_REVISION_INVALID")
        try:
            strategy = LegacyVectorStrategy(memory.get("legacy_vector_strategy"))
        except (TypeError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_STRATEGY_INVALID") from exc
        normalization_kind = memory.get("normalization_kind", "ORDINARY")
        if normalization_kind not in {"ORDINARY", "CHARACTER_SEED", _REFUSAL_CODE}:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MEMORY_KIND_INVALID")
        seen_eids.add(eid)
        normalized = {
            "eid": eid,
            "r1_revision_id": str(revision),
            "legacy_vector_strategy": strategy.value,
            "normalization_kind": normalization_kind,
        }
        if normalization_kind == _REFUSAL_CODE:
            object_id = _require_uuid(memory.get("object_id"), "P3_CARRIER_REFUSAL_OBJECT_INVALID")
            raw_row_digest = memory.get("raw_row_digest")
            source_identity = _require_mapping(
                memory.get("source_identity"), "P3_CARRIER_REFUSAL_SOURCE_IDENTITY_INVALID",
            )
            if (
                not isinstance(raw_row_digest, str)
                or len(raw_row_digest) != 64
                or memory.get("governance_readiness") != "NO_EXACT_GOVERNANCE_FACT_FOUND_IN_E"
                or memory.get("lifecycle_readiness") != "NO_AUTHORITATIVE_LIFECYCLE_FACT_FOUND_IN_E"
                or not isinstance(memory.get("provenance_evidence_state"), str)
            ):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_EVIDENCE_INVALID")
            normalized.update({
                "object_id": str(object_id),
                "raw_row_digest": raw_row_digest,
                "source_identity": source_identity,
                "governance_readiness": memory["governance_readiness"],
                "lifecycle_readiness": memory["lifecycle_readiness"],
                "provenance_evidence_state": memory["provenance_evidence_state"],
            })
        result.append(normalized)
    return tuple(sorted(result, key=lambda item: item["eid"]))


def _carrier_b1_motif_evidence(b1: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    motifs = _require_list(b1.get("motifs"), "P3_CARRIER_B1_MOTIF_EVIDENCE_REQUIRED")
    result: list[dict[str, Any]] = []
    seen_runtime_motif_ids: set[str] = set()
    for motif in motifs:
        runtime_motif_id = motif.get("runtime_motif_id")
        if not isinstance(runtime_motif_id, str) or not runtime_motif_id:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MOTIF_RUNTIME_ID_INVALID")
        if runtime_motif_id in seen_runtime_motif_ids:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MOTIF_RUNTIME_ID_DUPLICATE")
        source_object_id = _require_uuid(
            motif.get("source_object_id"), "P3_CARRIER_B1_MOTIF_SOURCE_OBJECT_INVALID",
        )
        revision = _require_uuid(
            motif.get("r1_revision_id"), "P3_CARRIER_B1_MOTIF_REVISION_INVALID",
        )
        seen_runtime_motif_ids.add(runtime_motif_id)
        result.append({
            "runtime_motif_id": runtime_motif_id,
            "source_object_id": str(source_object_id),
            "r1_revision_id": str(revision),
        })
    return tuple(sorted(result, key=lambda item: item["runtime_motif_id"]))


def _carrier_b1_motif_dispositions(b1: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    values = _require_list(b1.get("motif_dispositions"), "P3_CARRIER_B1_MOTIF_DISPOSITIONS_REQUIRED")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    allowed = {item.value for item in MotifSemanticDisposition}
    for value in values:
        motif_id = value.get("motif_id")
        disposition = value.get("disposition")
        if not isinstance(motif_id, str) or not motif_id or disposition not in allowed or motif_id in seen:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_MOTIF_DISPOSITION_INVALID")
        if disposition == MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED.value:
            if (
                value.get("partial_reason") not in {"IDENTITY_AMBIGUOUS", "MULTIPLICITY_INCOMPATIBLE", "BOTH"}
                or not isinstance(value.get("partial_certification_digest"), str)
                or value.get("exact_motif") is not None
            ):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_PARTIAL_DISPOSITION_INVALID")
        elif disposition in {
            MotifSemanticDisposition.EXACT_ADMITTED.value,
            MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value,
        }:
            member_count = value.get("source_member_count")
            if (
                not isinstance(value.get("exact_motif"), dict)
                or not isinstance(member_count, int)
                or isinstance(member_count, bool)
                or member_count < 0
                or (
                    disposition == MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value
                    and member_count != 0
                )
                or (
                    disposition == MotifSemanticDisposition.EXACT_ADMITTED.value
                    and member_count == 0
                )
            ):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_EXACT_DISPOSITION_INVALID")
        elif not isinstance(value.get("blocking_code"), str):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B1_BLOCKING_DISPOSITION_INVALID")
        seen.add(motif_id)
        result.append(dict(value))
    return tuple(sorted(result, key=lambda item: item["motif_id"]))


def _carrier_b2_memory_evidence(b2: dict[str, Any]) -> dict[int, dict[str, Any]]:
    memories = _require_list(b2.get("memories"), "P3_CARRIER_B2_MEMORY_EVIDENCE_REQUIRED")
    result: dict[int, dict[str, Any]] = {}
    for memory in memories:
        eid = _require_nonnegative_int(memory.get("eid"), "P3_CARRIER_B2_MEMORY_EID_INVALID")
        if eid in result:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_MEMORY_EID_DUPLICATE")
        disposition = memory.get("disposition", "ADMITTED")
        if disposition == "ADMITTED":
            revision = _require_uuid(memory.get("r2_revision_id"), "P3_CARRIER_B2_MEMORY_REVISION_INVALID")
            result[eid] = {"eid": eid, "disposition": disposition, "r2_revision_id": str(revision)}
        elif disposition == _REFUSAL_CODE:
            digest = memory.get("certificate_digest")
            operation_id = _require_uuid(
                memory.get("receipt_operation_id"), "P3_CARRIER_B2_REFUSAL_RECEIPT_INVALID",
            )
            if not isinstance(digest, str) or len(digest) != 64:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_REFUSAL_CERTIFICATE_INVALID")
            result[eid] = {
                "eid": eid,
                "disposition": disposition,
                "certificate_digest": digest,
                "receipt_operation_id": str(operation_id),
            }
        else:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_MEMORY_DISPOSITION_INVALID")
    return result


def _require_b2_closure(
    memories: tuple[dict[str, Any], ...], b2_by_eid: dict[int, dict[str, Any]],
) -> None:
    if {item["eid"] for item in memories} != set(b2_by_eid):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_EID_SET_MISMATCH")


def _prepare_source_semantic_gap_certification(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
) -> dict[str, Any] | None:
    """Write the immutable external E/certificate pair for terminal B2 refusals.

    The certificate is deliberately constructed before its database receipts:
    E binds frozen source and B1 identity facts, while receipts bind E's
    resulting certificate digest.  Neither artifact invents semantic values.
    """

    members: list[dict[str, Any]] = []
    source_identity_members: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    for entry in _ordered_scope_entries(record):
        scope = _scope_key_from_payload(entry.get("scope_key"))
        namespace_id = _require_uuid(
            entry.get("legacy_source_namespace_id"), "P3_CARRIER_REFUSAL_NAMESPACE_INVALID",
        )
        namespace_key = entry.get("legacy_source_namespace_key")
        if not isinstance(namespace_key, str) or not namespace_key:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_NAMESPACE_INVALID")
        manifest, _root = _character_snapshot_manifest(entry)
        source_artifacts.append({
            "scope_key": scope.identity_payload(),
            "legacy_snapshot_id": str(manifest.legacy_snapshot_id),
            "manifest_digest": entry.get("manifest_digest"),
            "artifacts": [
                {
                    "artifact_id": str(artifact.artifact_id),
                    "artifact_class": artifact.artifact_class,
                    "observed_relative_locator": artifact.observed_relative_locator,
                    "byte_length": artifact.byte_length,
                    "digest": artifact.digest_hex,
                }
                for artifact in manifest.artifacts
            ],
        })
        b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
        for memory in _carrier_b1_memory_evidence(b1):
            if memory["normalization_kind"] != _REFUSAL_CODE:
                continue
            source_identity = _require_mapping(
                memory.get("source_identity"), "P3_CARRIER_REFUSAL_SOURCE_IDENTITY_INVALID",
            )
            expected = _certified_refusal_source_member(
                request, scope, namespace_id, memory["eid"],
            )
            if expected is None or source_identity != expected.identity_payload:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_SOURCE_IDENTITY_MISMATCH")
            source_identity_members.append(source_identity)
            members.append({
                "source_identity": source_identity,
                "legacy_source_namespace_key": namespace_key,
                "fresh_b1_native_binding": {
                    "object_id": memory["object_id"],
                    "r1_revision_id": memory["r1_revision_id"],
                    "raw_row_digest": memory["raw_row_digest"],
                    "governance_readiness": "NO_EXACT_GOVERNANCE_FACT_FOUND_IN_E",
                    "lifecycle_readiness": "NO_AUTHORITATIVE_LIFECYCLE_FACT_FOUND_IN_E",
                    "provenance_evidence_state": memory["provenance_evidence_state"],
                },
            })
    if not members:
        return None
    members.sort(key=lambda item: (
        canonical_intent_text(item["source_identity"]["scope_key"]),
        item["source_identity"]["legacy_source_namespace_id"], item["source_identity"]["eid"],
    ))
    source_identity_members.sort(key=canonical_intent_text)
    if len({canonical_intent_text(item) for item in source_identity_members}) != len(source_identity_members):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_MEMBER_DUPLICATE")
    if source_identity_members != sorted(
        (item.identity_payload for item in request.certified_refusal_source_members),
        key=canonical_intent_text,
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_ENUMERATED_SET_MISMATCH")
    b1m = _require_mapping(record.get("b1m"), "P3_B1M_IDENTITY_UNIVERSE_REQUIRED")
    exception_digest = _digest(source_identity_members)
    source_artifacts.sort(key=lambda item: canonical_intent_text(item["scope_key"]))
    predecessor = request.predecessor_record_path
    predecessor_digest = _file_digest(predecessor) if predecessor is not None else None
    evidence_payload = {
        "law": "TORMENT_P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_EVIDENCE_SET_V1",
        "native_core_id": str(request.expected_native_core_id),
        "root_p2_binding": {
            "root_description_digest": request.description.identity_digest,
            "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        },
        "p3_predecessor_carrier": None if predecessor is None else {
            "path": str(predecessor), "digest": predecessor_digest,
        },
        "p3_successor_carrier_path": str(request.record_path),
        "b1m_identity_universe_digest": b1m["identity_universe_digest"],
        "exception_set_digest": exception_digest,
        "exception_count": len(members),
        "enumerated_frozen_source_identities": source_identity_members,
        "selected_raw_rows": members,
        "frozen_snapshot_artifacts": source_artifacts,
        "forensic_census_digest": _digest({
            "law": "P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_FORENSIC_CENSUS_V1",
            "count": len(members),
            "members": members,
            "character_external_owner_applicability": "NONE",
        }),
        "provisional_evidence_digest": "d44f3d095f477eb48138fb28c4538a83bd77e04042dfd6c1910ea0145955bb45",
        "provisional_evidence_status": "SUPERSEDED",
    }
    evidence_digest = _write_or_load_external_immutable(
        request.carrier_root / _REFUSAL_EVIDENCE_NAME,
        "TORMENT_P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_EVIDENCE_SET",
        evidence_payload,
    )
    certificate_payload = {
        "law": "TORMENT_P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_CERTIFICATE_V1",
        "native_core_id": str(request.expected_native_core_id),
        "root_p2_binding": evidence_payload["root_p2_binding"],
        "b1m_identity_universe_digest": b1m["identity_universe_digest"],
        "exception_set_digest": exception_digest,
        "final_evidence_set_e_digest": evidence_digest,
        "members": members,
    }
    certificate_digest = _write_or_load_external_immutable(
        request.carrier_root / _REFUSAL_CERTIFICATE_NAME,
        "TORMENT_P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_CERTIFICATE",
        certificate_payload,
    )
    return {
        "evidence_path": str(request.carrier_root / _REFUSAL_EVIDENCE_NAME),
        "final_evidence_set_e_digest": evidence_digest,
        "certificate_path": str(request.carrier_root / _REFUSAL_CERTIFICATE_NAME),
        "certificate_digest": certificate_digest,
        "exception_set_digest": exception_digest,
        "members": members,
    }


def _prepare_or_revalidate_terminal_disposition_evidence(
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
    b1f: dict[str, Any],
    child_counts: dict[str, int],
    refusal_certification: dict[str, Any] | None,
) -> dict[str, str]:
    """Bind the complete B1/B2/B4 terminal partition only after assembly.

    B2 refusal certificates necessarily predate their own rejection receipts.
    They are therefore evidence for the frozen memory exception set, not the
    final root E.  This immutable document is written only once the carrier
    has sealed every B4 route and independently recomputed its child counts.
    """

    b4_counts = {
        name: child_counts.get(name, 0)
        for name in ("b4a", "b4b", "b4c", "b4p", "b4_refused_member_semantic_gap")
    }
    nonempty_exact_terminal_count = sum(
        b4_counts[name]
        for name in ("b4a", "b4b", "b4_refused_member_semantic_gap")
    )
    total_terminal_count = (
        nonempty_exact_terminal_count + b4_counts["b4c"] + b4_counts["b4p"]
    )
    if (
        nonempty_exact_terminal_count != b1f["exact_motif_count"]
        or b4_counts["b4c"] != b1f["zero_member_motif_count"]
        or b4_counts["b4p"] != b1f["partial_motif_count"]
        or total_terminal_count != b1f["total_motif_count"]
        or b1f["blocking_motif_count"] != 0
    ):
        raise RootP3SourceAdmissionRefused("P3_TERMINAL_MOTIF_DISPOSITION_CLOSURE_MISMATCH")
    b4_routes = _require_mapping(record.get("b4_routes"), "P3_B4_ROUTE_CARRIER_REQUIRED")
    b1m = _require_mapping(record.get("b1m"), "P3_B1M_IDENTITY_UNIVERSE_REQUIRED")
    b2_admitted_count = 0
    b2_refused_count = 0
    for entry in _ordered_scope_entries(record):
        b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
        memories = _carrier_b1_memory_evidence(b1)
        b2 = _carrier_b2_memory_evidence(
            _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
        )
        _require_b2_closure(memories, b2)
        b2_admitted_count += sum(item["disposition"] == "ADMITTED" for item in b2.values())
        b2_refused_count += sum(item["disposition"] == _REFUSAL_CODE for item in b2.values())
    if b2_refused_count and refusal_certification is None:
        raise RootP3SourceAdmissionRefused("P3_TERMINAL_REFUSAL_CERTIFICATE_REQUIRED")
    if refusal_certification is not None:
        if b2_refused_count != len(refusal_certification["members"]):
            raise RootP3SourceAdmissionRefused("P3_TERMINAL_REFUSAL_MEMORY_CLOSURE_MISMATCH")
        certificate_digest: str | None = refusal_certification["certificate_digest"]
        b2_evidence_digest: str | None = refusal_certification["final_evidence_set_e_digest"]
    else:
        certificate_digest = None
        b2_evidence_digest = None
    payload = {
        "law": "TORMENT_P3_TERMINAL_DISPOSITION_EVIDENCE_SET_E_V1",
        "native_core_id": str(request.expected_native_core_id),
        "root_p2_binding": {
            "root_description_digest": request.description.identity_digest,
            "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        },
        "b1m_identity_universe_digest": b1m["identity_universe_digest"],
        "b1f_disposition_digest": b1f["disposition_digest"],
        "b2_partition": {
            "admitted_count": b2_admitted_count,
            "refused_source_semantic_gap_count": b2_refused_count,
            "refusal_certificate_digest": certificate_digest,
            "b2_refusal_evidence_set_digest": b2_evidence_digest,
        },
        "b4_partition": {
            "b4a": b4_counts["b4a"],
            "b4b": b4_counts["b4b"],
            "b4c": b4_counts["b4c"],
            "b4p": b4_counts["b4p"],
            "b4_refused_member_semantic_gap": b4_counts["b4_refused_member_semantic_gap"],
            "total": total_terminal_count,
            "unaccounted": 0,
            "overlap": 0,
        },
        "b4_route_carrier_digest": _digest(b4_routes),
        "source_carrier_path": str(request.record_path),
    }
    digest = _write_or_load_external_immutable(
        request.carrier_root / _TERMINAL_EVIDENCE_NAME,
        "TORMENT_P3_TERMINAL_DISPOSITION_EVIDENCE_SET_E",
        payload,
    )
    summary = {
        "path": str(request.carrier_root / _TERMINAL_EVIDENCE_NAME),
        "final_evidence_set_e_digest": digest,
    }
    previous = record.get("terminal_disposition_evidence")
    if previous is not None and previous != summary:
        raise RootP3SourceAdmissionRefused("P3_TERMINAL_EVIDENCE_CARRIER_DRIFT")
    return summary


def _write_or_load_external_immutable(path: Path, schema: str, payload: dict[str, Any]) -> str:
    """Create one external immutable document, or prove exact retry identity."""

    outer = {"schema": schema, "version": 1, "payload": payload, "digest": _digest(payload)}
    encoded = canonical_intent_text(outer) + "\n"
    if path.exists():
        try:
            observed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_EXTERNAL_RECORD_INVALID") from exc
        if observed != outer:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_EXTERNAL_RECORD_DRIFT")
        return outer["digest"]
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_EXTERNAL_TEMPORARY_EXISTS")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_EXTERNAL_RECORD_WRITE_FAILED") from exc
    return outer["digest"]


def _record_source_semantic_gap_refusal(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    memory: dict[str, Any],
    certification: dict[str, Any],
) -> UUID:
    """Persist one idempotent refusal receipt with no semantic publication."""

    binding = request_binding(request, entry)
    member_matches = [
        item for item in certification["members"]
        if item["source_identity"]["legacy_source_namespace_id"] == entry["legacy_source_namespace_id"]
        and item["source_identity"]["eid"] == memory["eid"]
    ]
    if len(member_matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_CERTIFICATE_MEMBER_MISSING")
    member = member_matches[0]
    source_identity = _require_mapping(
        memory.get("source_identity"), "P3_CARRIER_REFUSAL_SOURCE_IDENTITY_INVALID",
    )
    native_binding = _require_mapping(
        member.get("fresh_b1_native_binding"), "P3_CARRIER_REFUSAL_CERTIFICATE_MEMBER_INVALID",
    )
    if member.get("source_identity") != source_identity or any(native_binding[key] != memory[key] for key in (
        "object_id", "r1_revision_id", "raw_row_digest", "governance_readiness",
        "lifecycle_readiness", "provenance_evidence_state",
    )):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_CERTIFICATE_MEMBER_DRIFT")
    object_id = _require_uuid(memory["object_id"], "P3_CARRIER_REFUSAL_OBJECT_INVALID")
    revision_id = _require_uuid(memory["r1_revision_id"], "P3_CARRIER_REFUSAL_REVISION_INVALID")
    intent = canonical_intent_text({
        "law": "TORMENT_P3_B2_REFUSED_SOURCE_SEMANTIC_GAP_RECEIPT_V1",
        "native_core_id": str(request.expected_native_core_id),
        "certificate_digest": certification["certificate_digest"],
        "source_identity": source_identity,
        "object_id": str(object_id),
        "r1_revision_id": str(revision_id),
        "raw_row_digest": memory["raw_row_digest"],
    })
    key = _stage_key(request, entry, "B2_REFUSED_SOURCE_SEMANTIC_GAP", str(memory["eid"]))
    try:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            """SELECT operation_id,canonical_intent_json FROM operations
                 WHERE idempotency_namespace_id=? AND idempotency_key=?""",
            (native_id_to_bytes(binding.scope_plan.idempotency_namespace_id), key),
        ).fetchone()
        if existing is not None:
            operation_id, existing_intent = existing
            if existing_intent != intent:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_IDEMPOTENCY_CONFLICT")
            rejection = connection.execute(
                "SELECT rejection_code,rejection_detail FROM operation_rejections WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
            transitions = connection.execute(
                "SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (operation_id,),
            ).fetchone()[0]
            outputs = connection.execute(
                "SELECT count(*) FROM operation_outputs WHERE operation_id=?", (operation_id,),
            ).fetchone()[0]
            if rejection != (_REFUSAL_CODE, certification["certificate_digest"]) or transitions or outputs:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_RECEIPT_DRIFT")
            connection.execute("COMMIT")
            return native_id_from_bytes(operation_id)

        current = connection.execute(
            """SELECT r.lineage_kind,o.current_revision_id,o.current_revision_ordinal
                 FROM objects o JOIN object_revisions r ON r.object_id=o.object_id
                   AND r.object_revision_id=? AND r.revision_ordinal=1
                 JOIN legacy_object_aliases a ON a.object_id=o.object_id
                WHERE o.object_id=? AND a.legacy_source_namespace_id=?
                  AND a.alias_kind='EID' AND a.alias_value=?""",
            (native_id_to_bytes(revision_id), native_id_to_bytes(object_id),
             native_id_to_bytes(UUID(entry["legacy_source_namespace_id"])), str(memory["eid"])),
        ).fetchone()
        if current != ("LEGACY_PREDECESSOR_UNKNOWN", native_id_to_bytes(revision_id), 1):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_REFUSAL_R1_NOT_CURRENT_EVIDENCE")
        operation_id = uuid4().bytes
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
            (operation_id, native_id_to_bytes(binding.scope_plan.idempotency_namespace_id), key,
             _REFUSAL_OPERATION_KIND, "TMS-INTENT-1", intent),
        )
        connection.execute(
            """INSERT INTO operation_targets(
                   operation_id,target_ordinal,target_role,target_kind,object_id,
                   object_revision_id,object_revision_ordinal
               ) VALUES (?,?,?,?,?,?,?)""",
            (operation_id, 0, "REFUSED_SOURCE_MEMORY", "OBJECT", native_id_to_bytes(object_id),
             native_id_to_bytes(revision_id), 1),
        )
        connection.execute(
            "INSERT INTO operation_rejections VALUES (?,?,?,0)",
            (operation_id, _REFUSAL_CODE, certification["certificate_digest"]),
        )
        connection.execute("COMMIT")
        return native_id_from_bytes(operation_id)
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def _prepare_or_revalidate_b4_routes(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    record: dict[str, Any],
    refusal_certification: dict[str, Any] | None,
) -> dict[str, Any]:
    """Seal P3 B4 routing from frozen lanes plus already-terminal B2 facts.

    B1F remains source authority: an exact source motif is still exact even
    when a member was truthfully refused B2 semantic admission.  This later
    P3 seam chooses only the terminal *runtime* disposition and records a
    no-output B4 receipt where full runtime membership is unavailable.
    """

    routes_by_scope: list[dict[str, Any]] = []
    entries_by_namespace = {
        str(entry["legacy_source_namespace_id"]): entry
        for entry in _ordered_scope_entries(record)
    }
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        source = _source_plan_for_key(request, binding.scope_key)
        b1 = _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
        motifs = _require_list(b1.get("motifs"), "P3_CARRIER_B1_MOTIF_EVIDENCE_REQUIRED")
        dispositions = {
            item["motif_id"]: item
            for item in _carrier_b1_motif_dispositions(b1)
        }
        workspace_plans = tuple(sorted(
            (
                candidate.scope_plan
                for candidate in request.scope_bindings
                if candidate.scope_key.workspace_id == binding.scope_key.workspace_id
            ),
            key=lambda item: (item.workspace_id, item.scope_kind, item.qualifier),
        ))
        b2_by_namespace = {
            str(plan.legacy_source_namespace_id): _carrier_b2_memory_evidence(
                _require_mapping(
                    entries_by_namespace[str(plan.legacy_source_namespace_id)].get("b2"),
                    "P3_CARRIER_B2_EVIDENCE_REQUIRED",
                )
            )
            for plan in workspace_plans
        }
        scope_routes: list[dict[str, Any]] = []
        for motif in sorted(motifs, key=lambda item: item["runtime_motif_id"]):
            if not isinstance(motif, dict):
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_EVIDENCE_INVALID")
            motif_id = motif.get("runtime_motif_id")
            disposition = dispositions.get(motif_id)
            if not isinstance(motif_id, str) or disposition is None:
                raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_DISPOSITION_MISMATCH")
            route = _derive_b4_route(
                connection, request, entry, binding, source, motif, disposition,
                workspace_plans, b2_by_namespace, refusal_certification,
            )
            if route["runtime_motif_id"] != motif_id:
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_MOTIF_ID_DRIFT")
            scope_routes.append(route)
        # B1F partials do not have a native source motif object.  They remain
        # B4P source-only retention and are intentionally not in this route set.
        if source.motif_presence.value == "PRESENT" and len(scope_routes) != len(motifs):
            raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_EXACT_CLOSURE_MISMATCH")
        routes_by_scope.append({
            "scope_key": binding.scope_key.identity_payload(),
            "routes": scope_routes,
        })
    payload = {
        "law": "TORMENT_P3_B4_ROOT_BOUND_RUNTIME_ROUTE_V1",
        "scope_routes": sorted(routes_by_scope, key=lambda item: canonical_intent_text(item["scope_key"])),
    }
    previous = record.get("b4_routes")
    if previous is not None and previous != payload:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_DRIFT")
    return payload


def _derive_b4_route(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    binding: RootP3ScopeBinding,
    source: Any,
    motif: dict[str, Any],
    disposition: dict[str, Any],
    workspace_plans: tuple[MigrationRuntimeScopePlan, ...],
    b2_by_namespace: dict[str, dict[int, dict[str, Any]]],
    refusal_certification: dict[str, Any] | None,
) -> dict[str, Any]:
    """Derive one exact B4 route without consulting source-scope posture."""

    if disposition["disposition"] not in {
        MotifSemanticDisposition.EXACT_ADMITTED.value,
        MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value,
    }:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_NONEXACT_SOURCE")
    plan = binding.scope_plan
    root = Path(entry["snapshot_root"])
    meta_path = root / "workspaces" / plan.workspace_id / "workspace_meta.json"
    motif_path = root / "workspaces" / plan.workspace_id / "domains" / str(plan.motif_domain_id) / "motifs.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        registry = json.loads(motif_path.read_text(encoding="utf-8"))
        raw = registry["motifs"][motif["runtime_motif_id"]]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_EVIDENCE_UNREADABLE") from exc
    lane = (meta.get("embed_provider"), meta.get("embed_model"), meta.get("embed_dim"))
    centroid = raw.get("centroid") if isinstance(raw, dict) else None
    members = raw.get("members") if isinstance(raw, dict) else None
    if (
        not isinstance(lane[0], str) or not lane[0]
        or not isinstance(lane[1], str) or not lane[1]
        or not isinstance(lane[2], int) or isinstance(lane[2], bool) or lane[2] < 1
        or not isinstance(centroid, list) or len(centroid) != lane[2]
        or not isinstance(members, list)
        or any(not isinstance(eid, int) or isinstance(eid, bool) or eid < 0 for eid in members)
    ):
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_GEOMETRY_UNQUALIFIED")
    if raw.get("motif_id") != motif["runtime_motif_id"] or raw.get("domain_id") != plan.motif_domain_id:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_MOTIF_DRIFT")
    source_object_id = _require_uuid(motif.get("source_object_id"), "P3_B4_ROUTE_SOURCE_OBJECT_INVALID")
    source_revision_id = _require_uuid(motif.get("r1_revision_id"), "P3_B4_ROUTE_SOURCE_REVISION_INVALID")
    source_row = connection.execute(
        """SELECT t.transition_id,t.operation_id
             FROM objects o
             JOIN object_revisions r ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id AND r.revision_ordinal=o.current_revision_ordinal
             JOIN semantic_transitions t ON t.transition_id=o.creating_transition_id
             JOIN legacy_object_aliases a ON a.object_id=o.object_id
            WHERE o.object_id=? AND o.current_revision_id=? AND o.current_revision_ordinal=1
              AND r.lineage_kind='LEGACY_PREDECESSOR_UNKNOWN'
              AND a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID' AND a.alias_value=?""",
        (
            native_id_to_bytes(source_object_id), native_id_to_bytes(source_revision_id),
            native_id_to_bytes(plan.legacy_source_namespace_id), motif["runtime_motif_id"],
        ),
    ).fetchone()
    if source_row is None:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_MOTIF_TOPOLOGY_DRIFT")
    transition_id, operation_id = source_row
    rows = connection.execute(
        """SELECT out.output_ordinal,member.object_id
             FROM operation_outputs out JOIN relationship_revision_effects effect
               ON effect.transition_id=? AND effect.relationship_id=out.relationship_id
              AND effect.relationship_revision_id=out.relationship_revision_id AND effect.relationship_revision_ordinal=out.relationship_revision_ordinal
             JOIN relationship_revisions rr ON rr.relationship_id=out.relationship_id AND rr.relationship_revision_id=out.relationship_revision_id
             JOIN relationship_revision_endpoints motif_endpoint ON motif_endpoint.relationship_revision_id=rr.relationship_revision_id AND motif_endpoint.endpoint_ordinal=0 AND motif_endpoint.endpoint_role='MOTIF' AND motif_endpoint.binding_mode='IDENTITY'
             JOIN relationship_revision_endpoints member ON member.relationship_revision_id=rr.relationship_revision_id AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER' AND member.binding_mode='IDENTITY'
            WHERE out.operation_id=? AND out.output_role='LEGACY_MOTIF_MEMBERSHIP_ADMISSION'
              AND out.output_kind='RELATIONSHIP' AND motif_endpoint.object_id=?
            ORDER BY out.output_ordinal""",
        (transition_id, operation_id, native_id_to_bytes(source_object_id)),
    ).fetchall()
    if [row[0] for row in rows] != list(range(1, len(members) + 1)):
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_MEMBERSHIP_DRIFT")
    if len(members) != disposition["source_member_count"]:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_SOURCE_MEMBER_COUNT_DRIFT")
    if not members:
        if disposition["disposition"] != MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value:
            raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_ZERO_MEMBER_DISPOSITION_DRIFT")
        route_name = "B4C"
        refused_members: list[dict[str, Any]] = []
    else:
        if disposition["disposition"] != MotifSemanticDisposition.EXACT_ADMITTED.value:
            raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_NONEMPTY_DISPOSITION_DRIFT")
        refused_members = []
        for eid, (_ordinal, object_id) in zip(members, rows, strict=True):
            aliases: list[tuple[bytes, bytes]] = []
            for member_plan in workspace_plans:
                aliases.extend(connection.execute(
                    """SELECT a.object_id,a.legacy_source_namespace_id
                         FROM legacy_object_aliases a JOIN objects o ON o.object_id=a.object_id
                        WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
                          AND a.alias_value=? AND o.object_kind='LEGACY_CORE_NODE'""",
                    (native_id_to_bytes(member_plan.legacy_source_namespace_id), str(eid)),
                ).fetchall())
            resolved = [row for row in aliases if row[0] == object_id]
            if len(resolved) != 1:
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_MEMBER_SCOPE_UNRESOLVED")
            namespace = str(native_id_from_bytes(resolved[0][1]))
            b2 = b2_by_namespace.get(namespace, {}).get(eid)
            if b2 is None:
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_MEMBER_B2_MISSING")
            if b2["disposition"] not in {_REFUSAL_CODE, "ADMITTED"}:
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_MEMBER_B2_DISPOSITION_INVALID")
        # The loop above deliberately verifies every member's B2 terminal
        # status.  The scoped refusal details are recovered below from the
        # carrier's namespace map, avoiding any motif-scope substitution.
        for eid, (_ordinal, object_id) in zip(members, rows, strict=True):
            aliases = []
            for member_plan in workspace_plans:
                aliases.extend(connection.execute(
                    "SELECT object_id,legacy_source_namespace_id FROM legacy_object_aliases WHERE legacy_source_namespace_id=? AND alias_kind='EID' AND alias_value=?",
                    (native_id_to_bytes(member_plan.legacy_source_namespace_id), str(eid)),
                ).fetchall())
            resolved = [row for row in aliases if row[0] == object_id]
            namespace = str(native_id_from_bytes(resolved[0][1]))
            b2 = b2_by_namespace[namespace][eid]
            if b2["disposition"] != _REFUSAL_CODE:
                continue
            refused_members.append({
                "legacy_source_namespace_id": namespace,
                "eid": eid,
                "object_id": str(native_id_from_bytes(object_id)),
                "r1_revision_id": _member_r1_revision_id(connection, object_id, namespace, eid),
                "b2_receipt_operation_id": b2["receipt_operation_id"],
                "b2_certificate_digest": b2["certificate_digest"],
            })
        if refused_members:
            route_name = _B4_REFUSAL_CODE
        elif lane == (
            request.description.target_representation_lane.provider,
            request.description.target_representation_lane.model,
            request.description.target_representation_lane.dimension,
        ):
            route_name = "B4A"
        else:
            route_name = "B4B"
    route: dict[str, Any] = {
        "runtime_motif_id": motif["runtime_motif_id"],
        "source_motif_object_id": str(source_object_id),
        "source_motif_r1_revision_id": str(source_revision_id),
        "source_lane": {"provider": lane[0], "model": lane[1], "dimension": lane[2], "centroid_dimension": len(centroid)},
        "route": route_name,
    }
    if route_name == _B4_REFUSAL_CODE:
        if refusal_certification is None:
            raise RootP3SourceAdmissionRefused("P3_B4_REFUSAL_CERTIFICATE_REQUIRED")
        refused_members.sort(key=lambda item: (item["legacy_source_namespace_id"], item["eid"]))
        certificate_payload = {
            "law": "TORMENT_P3_B4_REFUSED_MEMBER_SEMANTIC_GAP_CERTIFICATE_V1",
            "native_core_id": str(request.expected_native_core_id),
            "b2_root_exception_certificate_digest": refusal_certification["certificate_digest"],
            "source_motif": {
                "legacy_source_namespace_id": str(plan.legacy_source_namespace_id),
                "runtime_motif_id": motif["runtime_motif_id"],
                "object_id": str(source_object_id), "r1_revision_id": str(source_revision_id),
            },
            "members": refused_members,
        }
        certificate_digest = _digest(certificate_payload)
        receipt_operation_id = _record_b4_member_semantic_gap_refusal(
            connection, request, entry, source_object_id, source_revision_id,
            motif["runtime_motif_id"], certificate_digest, refused_members,
        )
        route["refused_members"] = refused_members
        route["certificate_digest"] = certificate_digest
        route["receipt_operation_id"] = str(receipt_operation_id)
    return route


def _member_r1_revision_id(
    connection: sqlite3.Connection, object_id: bytes, namespace: str, eid: int,
) -> str:
    row = connection.execute(
        """SELECT o.current_revision_id FROM objects o JOIN legacy_object_aliases a ON a.object_id=o.object_id
            WHERE o.object_id=? AND a.legacy_source_namespace_id=? AND a.alias_kind='EID' AND a.alias_value=?""",
        (object_id, native_id_to_bytes(UUID(namespace)), str(eid)),
    ).fetchone()
    if row is None:
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_MEMBER_R1_DRIFT")
    return str(native_id_from_bytes(row[0]))


def _record_b4_member_semantic_gap_refusal(
    connection: sqlite3.Connection,
    request: RootP3SourceAdmissionRequest,
    entry: dict[str, Any],
    source_object_id: UUID,
    source_revision_id: UUID,
    motif_id: str,
    certificate_digest: str,
    refused_members: list[dict[str, Any]],
) -> UUID:
    """Persist one idempotent rejected B4 operation, never a motif transition."""

    binding = request_binding(request, entry)
    intent = canonical_intent_text({
        "law": "TORMENT_P3_B4_REFUSED_MEMBER_SEMANTIC_GAP_RECEIPT_V1",
        "native_core_id": str(request.expected_native_core_id),
        "certificate_digest": certificate_digest,
        "source_motif": {
            "legacy_source_namespace_id": entry["legacy_source_namespace_id"],
            "runtime_motif_id": motif_id, "object_id": str(source_object_id),
            "r1_revision_id": str(source_revision_id),
        },
        "refused_members": refused_members,
    })
    key = _stage_key(request, entry, _B4_REFUSAL_CODE, motif_id)
    try:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT operation_id,canonical_intent_json FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
            (native_id_to_bytes(binding.scope_plan.idempotency_namespace_id), key),
        ).fetchone()
        if existing is not None:
            operation_id, existing_intent = existing
            if existing_intent != intent:
                raise RootP3SourceAdmissionRefused("P3_B4_REFUSAL_IDEMPOTENCY_CONFLICT")
            rejection = connection.execute(
                "SELECT rejection_code,rejection_detail FROM operation_rejections WHERE operation_id=?", (operation_id,),
            ).fetchone()
            transitions = connection.execute("SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (operation_id,)).fetchone()[0]
            outputs = connection.execute("SELECT count(*) FROM operation_outputs WHERE operation_id=?", (operation_id,)).fetchone()[0]
            if rejection != (_B4_REFUSAL_CODE, certificate_digest) or transitions or outputs:
                raise RootP3SourceAdmissionRefused("P3_B4_REFUSAL_RECEIPT_DRIFT")
            connection.execute("COMMIT")
            return native_id_from_bytes(operation_id)
        current = connection.execute(
            """SELECT r.lineage_kind,o.current_revision_id,o.current_revision_ordinal
                 FROM objects o JOIN object_revisions r ON r.object_id=o.object_id AND r.object_revision_id=? AND r.revision_ordinal=1
                 JOIN legacy_object_aliases a ON a.object_id=o.object_id
                WHERE o.object_id=? AND a.legacy_source_namespace_id=? AND a.alias_kind='MOTIF_ID' AND a.alias_value=?""",
            (native_id_to_bytes(source_revision_id), native_id_to_bytes(source_object_id),
             native_id_to_bytes(binding.scope_plan.legacy_source_namespace_id), motif_id),
        ).fetchone()
        if current != ("LEGACY_PREDECESSOR_UNKNOWN", native_id_to_bytes(source_revision_id), 1):
            raise RootP3SourceAdmissionRefused("P3_B4_REFUSAL_SOURCE_MOTIF_NOT_CURRENT")
        operation_id = uuid4().bytes
        connection.execute(
            "INSERT INTO operations VALUES (?,?,?,?,?,?,0)",
            (operation_id, native_id_to_bytes(binding.scope_plan.idempotency_namespace_id), key,
             _B4_REFUSAL_OPERATION_KIND, "TMS-INTENT-1", intent),
        )
        connection.execute(
            """INSERT INTO operation_targets(
                   operation_id,target_ordinal,target_role,target_kind,object_id,
                   object_revision_id,object_revision_ordinal
               ) VALUES (?,?,?,?,?,?,?)""",
            (operation_id, 0, "REFUSED_SOURCE_MOTIF", "OBJECT", native_id_to_bytes(source_object_id),
             native_id_to_bytes(source_revision_id), 1),
        )
        connection.execute(
            "INSERT INTO operation_rejections VALUES (?,?,?,0)",
            (operation_id, _B4_REFUSAL_CODE, certificate_digest),
        )
        connection.execute("COMMIT")
        return native_id_from_bytes(operation_id)
    except Exception:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise


def _carrier_b4_route_map(
    record: dict[str, Any],
) -> dict[tuple[RootScopeKey, str], dict[str, Any]]:
    routes = _require_mapping(record.get("b4_routes"), "P3_B4_ROUTE_CARRIER_REQUIRED")
    if routes.get("law") != "TORMENT_P3_B4_ROOT_BOUND_RUNTIME_ROUTE_V1":
        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
    scope_routes = _require_list(routes.get("scope_routes"), "P3_B4_ROUTE_CARRIER_INVALID")
    result: dict[tuple[RootScopeKey, str], dict[str, Any]] = {}
    for item in scope_routes:
        scope_key = _scope_key_from_payload(_require_mapping(item.get("scope_key"), "P3_B4_ROUTE_CARRIER_INVALID"))
        values = _require_list(item.get("routes"), "P3_B4_ROUTE_CARRIER_INVALID")
        for value in values:
            route = _require_mapping(value, "P3_B4_ROUTE_CARRIER_INVALID")
            motif_id = route.get("runtime_motif_id")
            name = route.get("route")
            source_lane = _require_mapping(route.get("source_lane"), "P3_B4_ROUTE_CARRIER_INVALID")
            if (
                not isinstance(motif_id, str) or not motif_id
                or name not in {"B4A", "B4B", "B4C", _B4_REFUSAL_CODE}
                or not isinstance(source_lane.get("provider"), str)
                or not isinstance(source_lane.get("model"), str)
                or not isinstance(source_lane.get("dimension"), int)
                or not isinstance(source_lane.get("centroid_dimension"), int)
            ):
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
            _require_uuid(route.get("source_motif_object_id"), "P3_B4_ROUTE_CARRIER_INVALID")
            _require_uuid(route.get("source_motif_r1_revision_id"), "P3_B4_ROUTE_CARRIER_INVALID")
            if name == _B4_REFUSAL_CODE:
                _require_uuid(route.get("receipt_operation_id"), "P3_B4_ROUTE_CARRIER_INVALID")
                digest = route.get("certificate_digest")
                if not isinstance(digest, str) or len(digest) != 64:
                    raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
                members = _require_list(route.get("refused_members"), "P3_B4_ROUTE_CARRIER_INVALID")
                if not members:
                    raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
            elif any(key in route for key in ("receipt_operation_id", "certificate_digest", "refused_members")):
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
            key = (scope_key, motif_id)
            if key in result:
                raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_DUPLICATE")
            result[key] = dict(route)
    return result


def _build_normalization_request(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
    character_witnesses: dict[RootScopeKey, Any],
    partial_continuation: Path | None,
) -> RootNormalizationRequest:
    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    inputs: list[RootNormalizationScopeInput] = []
    unknown_by_scope_eid = _unknown_evidence_by_scope_eid(request)
    b4_routes = _carrier_b4_route_map(record)
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        source = _source_plan_for_key(request, binding.scope_key)
        memories, motifs = _carrier_b1_evidence(entry, source, character_witnesses)
        motif_dispositions = _carrier_b1_motif_dispositions(
            _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
        )
        b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
        b2_by_eid = _carrier_b2_memory_evidence(b2)
        _require_b2_closure(memories, b2_by_eid)
        motif_disposition_by_id = {item["motif_id"]: item for item in motif_dispositions}
        b3a: list[MigrationRuntimeRepresentationBootstrapRequest] = []
        b3b: list[MigrationRuntimeReembeddingBootstrapRequest] = []
        metadata_dispatches: list[MetadataLessB3BDispatch] = []
        b2_refused: list[RootB2CertifiedRefusalDisposition] = []
        if source.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                _require_unknown_eid_closure(binding.scope_key, memories, unknown_by_scope_eid)
            for memory in memories:
                eid = memory["eid"]
                b2_memory = b2_by_eid.get(eid)
                if b2_memory is None:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_B3_REQUIRES_B2_FACT")
                if b2_memory["disposition"] == _REFUSAL_CODE:
                    # Certified refusal is terminal P3 disposition, never a
                    # substitute for an R2 runtime semantic successor.
                    b2_refused.append(RootB2CertifiedRefusalDisposition(
                        legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                        eid=eid,
                        object_id=UUID(memory["object_id"]),
                        r1_revision_id=UUID(memory["r1_revision_id"]),
                        receipt_operation_id=UUID(b2_memory["receipt_operation_id"]),
                        certificate_digest=b2_memory["certificate_digest"],
                    ))
                    continue
                if b2_memory["disposition"] != "ADMITTED":
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_B2_MEMORY_DISPOSITION_INVALID")
                common = dict(
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
                    legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                    expected_native_core_id=request.expected_native_core_id,
                    eid=eid,
                    expected_r1_revision_id=UUID(memory["r1_revision_id"]),
                    expected_r2_revision_id=UUID(b2_memory["r2_revision_id"]),
                    target_lane=request.description.target_representation_lane,
                    idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
                )
                strategy = LegacyVectorStrategy(memory["legacy_vector_strategy"])
                if strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
                    b3a.append(MigrationRuntimeRepresentationBootstrapRequest(
                        **common,
                        idempotency_key=_stage_key(request, entry, "B3A", str(eid)),
                    ))
                elif source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                    evidence = unknown_by_scope_eid[(binding.scope_key, eid)]
                    try:
                        qualified = qualify_metadata_less_per_eid_legacy_source(
                            data_root=request.root,
                            scope_key=binding.scope_key,
                            legacy_eid=eid,
                            legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                            target_identity_namespace_id=binding.scope_plan.target_identity_namespace_id,
                            nodes_source=evidence.canonical_text_evidence,
                            optional_edges_source=_optional_edges_source(request, binding.scope_key),
                            legacy_representation_source=evidence.vector_evidence,
                        )
                    except (SubstrateConfigurationError, OSError, ValueError) as exc:
                        raise RootP3SourceAdmissionRefused("P3_CARRIER_METADATA_LESS_SOURCE_REFUSED") from exc
                    b3b_request = MigrationRuntimeReembeddingBootstrapRequest(
                        **common,
                        scope_plans=(binding.scope_plan,),
                        idempotency_key=_stage_key(request, entry, "B3B_METADATA_LESS", str(eid)),
                    )
                    metadata_dispatches.append(MetadataLessB3BDispatch(qualified, b3b_request))
                else:
                    b3b.append(MigrationRuntimeReembeddingBootstrapRequest(
                        **common,
                        scope_plans=(binding.scope_plan,),
                        idempotency_key=_stage_key(request, entry, "B3B", str(eid)),
                    ))

        b4a: list[MigrationRuntimeMotifProjectionRequest] = []
        b4b: list[MigrationRuntimeMotifRegeometryProjectionRequest] = []
        b4c: list[MigrationRuntimeZeroMemberMotifProjectionRequest] = []
        b4p: list[PartialMotifRetentionRequest] = []
        b4_refused: list[RootB4CertifiedRefusalDisposition] = []
        if source.motif_presence is SourceArtifactPresence.PRESENT:
            motif_scope_plans = tuple(sorted(
                (
                    candidate.scope_plan
                    for candidate in request.scope_bindings
                    if candidate.scope_key.workspace_id == binding.scope_key.workspace_id
                ),
                key=lambda item: (item.workspace_id, item.scope_kind, item.qualifier),
            ))
            for motif in motifs:
                disposition = motif_disposition_by_id.get(motif["runtime_motif_id"])
                if disposition is None:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_DISPOSITION_MISMATCH")
                route = b4_routes.get((binding.scope_key, motif["runtime_motif_id"]))
                if route is None:
                    raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_MISSING")
                common_motif = dict(
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
                    legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                    expected_native_core_id=request.expected_native_core_id,
                    runtime_motif_id=motif["runtime_motif_id"],
                    expected_source_motif_object_id=UUID(motif["source_object_id"]),
                    expected_source_motif_revision_id=UUID(motif["r1_revision_id"]),
                    scope_plans=motif_scope_plans,
                    target_lane=request.description.target_representation_lane,
                    idempotency_namespace_id=binding.scope_plan.idempotency_namespace_id,
                )
                if route["route"] == "B4C":
                    if disposition["disposition"] != MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value:
                        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_DISPOSITION_DRIFT")
                    b4c.append(MigrationRuntimeZeroMemberMotifProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4C", str(motif["runtime_motif_id"])),
                    ))
                elif disposition["disposition"] != MotifSemanticDisposition.EXACT_ADMITTED.value:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_EXACT_DISPOSITION_REQUIRED")
                elif route["route"] == "B4A":
                    b4a.append(MigrationRuntimeMotifProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4A", str(motif["runtime_motif_id"])),
                    ))
                elif route["route"] == "B4B":
                    b4b.append(MigrationRuntimeMotifRegeometryProjectionRequest(
                        **common_motif,
                        idempotency_key=_stage_key(request, entry, "B4B", str(motif["runtime_motif_id"])),
                    ))
                elif route["route"] == _B4_REFUSAL_CODE:
                    b4_refused.append(RootB4CertifiedRefusalDisposition(
                        legacy_source_namespace_id=binding.scope_plan.legacy_source_namespace_id,
                        runtime_motif_id=motif["runtime_motif_id"],
                        source_motif_object_id=UUID(route["source_motif_object_id"]),
                        source_motif_r1_revision_id=UUID(route["source_motif_r1_revision_id"]),
                        receipt_operation_id=UUID(route["receipt_operation_id"]),
                        certificate_digest=route["certificate_digest"],
                    ))
                else:
                    raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
            for motif in motif_dispositions:
                if motif["disposition"] != MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED.value:
                    continue
                if partial_continuation is None:
                    raise RootP3SourceAdmissionRefused("P3_PARTIAL_AUTHORITY_CONTINUATION_REQUIRED")
                digest = motif.get("partial_certification_digest")
                if not isinstance(digest, str) or len(digest) != 64:
                    raise RootP3SourceAdmissionRefused("P3_PARTIAL_CERTIFICATION_DIGEST_INVALID")
                b4p.append(PartialMotifRetentionRequest(
                    continuation_record_path=partial_continuation,
                    certification_digest=digest,
                    snapshot_root=Path(entry["snapshot_root"]),
                    manifest_path=Path(entry["manifest_path"]),
                    expected_native_core_id=request.expected_native_core_id,
                    eligible_member_source_namespace_ids=_eligible_member_source_namespace_ids(request, binding),
                    b1m_identity_universe_digest=_require_mapping(
                        record.get("b1m"), "P3_B1M_IDENTITY_UNIVERSE_REQUIRED",
                    )["identity_universe_digest"],
                ))
        inputs.append(RootNormalizationScopeInput(
            scope_key=binding.scope_key,
            scope_plan=binding.scope_plan,
            legacy_snapshot_id=UUID(entry["legacy_snapshot_id"]),
            b3a_requests=tuple(b3a),
            b3b_requests=tuple(b3b),
            metadata_less_b3b_dispatches=tuple(metadata_dispatches),
            b2_refused_memory_dispositions=tuple(b2_refused),
            motif_source_admitted=(
                source.motif_presence is SourceArtifactPresence.PRESENT
            ),
            b4a_requests=tuple(b4a),
            b4b_requests=tuple(b4b),
            b4c_requests=tuple(b4c),
            b4p_requests=tuple(b4p),
            b4_refused_motif_dispositions=tuple(b4_refused),
        ))
    return RootNormalizationRequest(
        description=request.description,
        data_root=request.root,
        native_core_database_path=request.native_core_database_path,
        expected_native_core_id=request.expected_native_core_id,
        scope_inputs=tuple(sorted(inputs, key=lambda item: item.scope_key.canonical_key)),
        qualification_embedder_identity=request.qualification_embedder_identity,
        b3b_embedder=request.b3b_embedder,
        post_write_configurations=request.post_write_configurations,
        b1m_identity_universe_digest=_require_mapping(
            record.get("b1m"), "P3_B1M_IDENTITY_UNIVERSE_REQUIRED",
        )["identity_universe_digest"],
        recovered_p2_explicit_source_manifest_digest=(
            request.recovered_p2_explicit_source_manifest_digest
        ),
    )


def _unknown_evidence_by_scope_eid(
    request: RootP3SourceAdmissionRequest,
) -> dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence]:
    result: dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence] = {}
    for evidence in request.unknown_identity_evidence:
        key = (evidence.scope_key, evidence.eid)
        if key in result:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_UNKNOWN_IDENTITY_EID_DUPLICATE")
        result[key] = evidence
    return result


def _require_unknown_eid_closure(
    scope_key: RootScopeKey,
    memories: tuple[dict[str, Any], ...],
    unknown_by_scope_eid: dict[tuple[RootScopeKey, int], MetadataLessPerEidEvidence],
) -> None:
    memory_eids = {item["eid"] for item in memories}
    evidence_eids = {
        eid for candidate_scope, eid in unknown_by_scope_eid
        if candidate_scope == scope_key
    }
    if memory_eids != evidence_eids:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_UNKNOWN_IDENTITY_EID_SET_MISMATCH")


def _carrier_evidence_child_request_counts(
    request: RootP3SourceAdmissionRequest, record: dict[str, Any],
    character_witnesses: dict[RootScopeKey, Any],
) -> dict[str, int]:
    """Derive executable B3/B4 counts only from completed carrier evidence."""

    _MetadataLessPerEidEvidence, _RootSourceScopePlan, SourceArtifactPresence = _corrective_freeze_types()
    unknown_by_scope_eid = _unknown_evidence_by_scope_eid(request)
    result = {
        "b3a": 0, "ordinary_b3b": 0, "metadata_less_b3b": 0,
        "total_b3b": 0, "b4a": 0, "b4b": 0, "b4c": 0, "b4p": 0,
    }
    b4_routes = _carrier_b4_route_map(record)
    for entry in _ordered_scope_entries(record):
        scope_key = _scope_key_from_payload(entry.get("scope_key"))
        source = _source_plan_for_key(request, scope_key)
        memories, motifs = _carrier_b1_evidence(entry, source, character_witnesses)
        b2 = _require_mapping(entry.get("b2"), "P3_CARRIER_B2_EVIDENCE_REQUIRED")
        b2_by_eid = _carrier_b2_memory_evidence(b2)
        _require_b2_closure(memories, b2_by_eid)
        if source.materialization_posture is MaterializedScopePosture.MEMORY_GRAPH:
            if source.representation_disposition is RootRepresentationDisposition.UNKNOWN_IDENTITY:
                _require_unknown_eid_closure(scope_key, memories, unknown_by_scope_eid)
                result["metadata_less_b3b"] += sum(
                    b2_by_eid[memory["eid"]]["disposition"] == "ADMITTED"
                    for memory in memories
                )
            else:
                for memory in memories:
                    if b2_by_eid[memory["eid"]]["disposition"] == _REFUSAL_CODE:
                        continue
                    strategy = LegacyVectorStrategy(memory["legacy_vector_strategy"])
                    if strategy is LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
                        result["b3a"] += 1
                    else:
                        result["ordinary_b3b"] += 1
        if source.motif_presence is SourceArtifactPresence.PRESENT:
            dispositions = {
                item["motif_id"]: item
                for item in _carrier_b1_motif_dispositions(
                    _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
                )
            }
            for motif in motifs:
                disposition = dispositions.get(motif["runtime_motif_id"])
                route = b4_routes.get((scope_key, motif["runtime_motif_id"]))
                if disposition is None or route is None:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_B1_DISPOSITION_MISMATCH")
                if route["route"] == "B4C":
                    if disposition["disposition"] != MotifSemanticDisposition.ZERO_MEMBER_CERTIFIED.value:
                        raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_DISPOSITION_DRIFT")
                    result["b4c"] += 1
                elif disposition["disposition"] != MotifSemanticDisposition.EXACT_ADMITTED.value:
                    raise RootP3SourceAdmissionRefused("P3_CARRIER_MOTIF_EXACT_DISPOSITION_REQUIRED")
                elif route["route"] == "B4A":
                    result["b4a"] += 1
                elif route["route"] == "B4B":
                    result["b4b"] += 1
                elif route["route"] == _B4_REFUSAL_CODE:
                    result["b4_refused_member_semantic_gap"] = (
                        result.get("b4_refused_member_semantic_gap", 0) + 1
                    )
                else:
                    raise RootP3SourceAdmissionRefused("P3_B4_ROUTE_CARRIER_INVALID")
            result["b4p"] += sum(
                item["disposition"] == MotifSemanticDisposition.PARTIAL_AUTHORITY_CERTIFIED.value
                for item in _carrier_b1_motif_dispositions(
                    _require_mapping(entry.get("b1"), "P3_CARRIER_B1_EVIDENCE_REQUIRED")
                )
            )
    result["total_b3b"] = result["ordinary_b3b"] + result["metadata_less_b3b"]
    return result


def _optional_edges_source(
    request: RootP3SourceAdmissionRequest, scope: RootScopeKey,
) -> ExplicitSourceEvidence:
    matches = [
        item for item in request.description.explicit_source_manifest.entries
        if item.scope_key == scope and item.semantic_role is EvidenceSemanticRole.EDGES
    ]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_OPTIONAL_EDGE_EVIDENCE_MISSING")
    return matches[0]


def _load_record(path: Path, request: RootP3SourceAdmissionRequest) -> dict[str, Any]:
    try:
        outer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_UNREADABLE") from exc
    if not isinstance(outer, dict) or set(outer) != {"schema", "version", "payload", "digest"}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SHAPE_INVALID")
    payload = outer.get("payload")
    if (
        outer.get("schema") != _RECORD_SCHEMA
        or outer.get("version") != _RECORD_VERSION
        or not isinstance(payload, dict)
        or outer.get("digest") != _digest(payload)
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_INTEGRITY_INVALID")
    expected = {
        "root_description_digest": request.description.identity_digest,
        "explicit_source_manifest_digest": request.description.explicit_source_manifest.digest,
        "expected_native_core_id": str(request.expected_native_core_id),
        "operation_key": request.operation_key,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_BINDING_MISMATCH")
    scopes = payload.get("scopes")
    if not isinstance(scopes, list) or len(scopes) != len(request.scope_bindings):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    keys = {_scope_key_from_payload(item.get("scope_key")) for item in scopes if isinstance(item, dict)}
    if keys != {item.scope_key for item in request.scope_bindings}:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    completion = payload.get("carrier_completion")
    if completion is not None:
        _completion_snapshot_pairs(completion, request)
    return payload


def _verify_record_snapshots(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    request: RootP3SourceAdmissionRequest,
) -> None:
    carrier = request.carrier_root
    completion = record.get("carrier_completion")
    inherited_pairs = (
        _completion_snapshot_pairs(completion, request)
        if completion is not None else set()
    )
    for entry in _ordered_scope_entries(record):
        binding = request_binding(request, entry)
        expected_namespace_id = binding.scope_plan.legacy_source_namespace_id
        expected_namespace_key = _p1_legacy_source_namespace_key(connection, expected_namespace_id)
        _require_p1_motif_alias_separation(connection, binding.scope_plan)
        if (
            entry.get("legacy_source_namespace_id") != str(expected_namespace_id)
            or entry.get("legacy_source_namespace_key") != expected_namespace_key
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
        root = Path(entry.get("snapshot_root", "")).expanduser().resolve()
        manifest_path = Path(entry.get("manifest_path", "")).expanduser().resolve()
        pair = (str(root), str(manifest_path))
        if (
            (carrier not in root.parents or carrier not in manifest_path.parents)
            and pair not in inherited_pairs
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_PATH_ESCAPES_RECORD")
        try:
            manifest = load_snapshot_manifest(manifest_path)
            verify_snapshot(snapshot_root=root, manifest=manifest)
        except (
            SubstrateConfigurationError, SubstrateEvidenceIntegrityMismatch,
            SubstrateSnapshotManifestError, OSError, ValueError,
        ) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_RECOVERY_REFUSED") from exc
        if (
            manifest.legacy_source_namespace_id != expected_namespace_id
            or manifest.legacy_source_namespace_key != expected_namespace_key
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
        if (
            str(manifest.legacy_snapshot_id) != entry.get("legacy_snapshot_id")
            or _file_digest(manifest_path) != entry.get("manifest_digest")
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SNAPSHOT_IDENTITY_MISMATCH")


def _completion_snapshot_pairs(
    completion: object,
    request: RootP3SourceAdmissionRequest,
) -> set[tuple[str, str]]:
    """Validate the immutable predecessor cross-binding for a completion carrier."""

    data = _require_mapping(completion, "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    base_keys = {
        "predecessor_record_path",
        "predecessor_record_digest",
        "completed_snapshots",
        "completed_manifests",
        "inherited_snapshots",
    }
    supersession_keys = {
        "predecessor_native_core_id",
        "successor_native_core_id",
        "predecessor_core_disposition",
    }
    has_supersession = bool(set(data) & supersession_keys)
    if has_supersession:
        if not supersession_keys <= set(data):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        base_keys |= supersession_keys
    pending_keys = base_keys | {
        "previous_b1_scope_reuse_candidate_count",
        "predecessor_b1_revalidation_pending",
    }
    qualified_keys = pending_keys | {"previous_b1_scope_reuse"}
    if set(data) not in (base_keys, pending_keys, qualified_keys):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    predecessor_path_raw = data.get("predecessor_record_path")
    predecessor_digest = data.get("predecessor_record_digest")
    if not isinstance(predecessor_path_raw, str) or not isinstance(predecessor_digest, str):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    predecessor_path = Path(predecessor_path_raw).expanduser().resolve()
    requested_predecessor = request.predecessor_record_path
    if requested_predecessor is not None and predecessor_path != requested_predecessor:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_MISMATCH")
    predecessor, observed_digest = _load_predecessor_record(predecessor_path)
    if observed_digest != predecessor_digest:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_DRIFT")
    if has_supersession:
        try:
            predecessor_core_id = UUID(data["predecessor_native_core_id"])
            successor_core_id = UUID(data["successor_native_core_id"])
        except (TypeError, ValueError) as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID") from exc
        if (
            predecessor.get("expected_native_core_id") != str(predecessor_core_id)
            or successor_core_id != request.expected_native_core_id
        ):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_MISMATCH")
        expected_disposition = (
            "SAME_CORE_CONTINUATION"
            if predecessor_core_id == successor_core_id
            else "PRESERVED_SUPERSEDED_PREDECESSOR_EVIDENCE"
        )
        if data.get("predecessor_core_disposition") != expected_disposition:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    predecessor_pairs = {
        (
            str(Path(item.get("snapshot_root", "")).expanduser().resolve()),
            str(Path(item.get("manifest_path", "")).expanduser().resolve()),
        )
        for item in _require_list(
            predecessor.get("scopes"),
            "P3_CARRIER_COMPLETION_PREDECESSOR_SCOPE_SET_INVALID",
        )
        if isinstance(item, dict)
    }
    completed = _require_list(data.get("completed_snapshots"), "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    if any(not isinstance(item, dict) for item in completed):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    manifests = data.get("completed_manifests")
    if not isinstance(manifests, list) or any(not isinstance(item, str) for item in manifests):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    if sorted(manifests) != sorted(
        item.get("manifest_path") for item in completed
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
    inherited = _require_list(data.get("inherited_snapshots"), "P3_CARRIER_COMPLETION_SHAPE_INVALID")
    pairs: set[tuple[str, str]] = set()
    for item in inherited:
        if not isinstance(item, dict):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        root = item.get("snapshot_root")
        manifest = item.get("manifest_path")
        if not isinstance(root, str) or not isinstance(manifest, str):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        pair = (str(Path(root).expanduser().resolve()), str(Path(manifest).expanduser().resolve()))
        if pair in pairs or pair not in predecessor_pairs:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        pairs.add(pair)
    _validate_completion_reuse_metadata(
        completion=data,
        predecessor=predecessor,
        inherited_snapshot_pairs=pairs,
        base_keys=base_keys,
        pending_keys=pending_keys,
        qualified_keys=qualified_keys,
        predecessor_core_superseded=(
            has_supersession and data["predecessor_core_disposition"]
            == "PRESERVED_SUPERSEDED_PREDECESSOR_EVIDENCE"
        ),
    )
    return pairs


def _validate_completion_reuse_metadata(
    *,
    completion: dict[str, Any],
    predecessor: dict[str, Any],
    inherited_snapshot_pairs: set[tuple[str, str]],
    base_keys: set[str],
    pending_keys: set[str],
    qualified_keys: set[str],
    predecessor_core_superseded: bool,
) -> None:
    """Accept only the legacy, pending, or qualified B1-reuse completion state."""

    predecessor_scopes = _require_list(
        predecessor.get("scopes"),
        "P3_CARRIER_COMPLETION_PREDECESSOR_SCOPE_SET_INVALID",
    )
    derived_candidate_count = 0
    for entry in predecessor_scopes:
        if not isinstance(entry, dict):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_PREDECESSOR_SCOPE_SET_INVALID")
        pair = (
            str(Path(entry.get("snapshot_root", "")).expanduser().resolve()),
            str(Path(entry.get("manifest_path", "")).expanduser().resolve()),
        )
        if pair in inherited_snapshot_pairs and entry.get("b1") is not None:
            derived_candidate_count += 1
    if predecessor_core_superseded:
        # A predecessor B1 record names revisions in its retained old core;
        # none may be revalidated or reused in the successor core.
        derived_candidate_count = 0

    keys = set(completion)
    if keys == base_keys:
        # Historical completions had no explicit reuse state.  Derive the
        # pending in-memory state so their inherited B1 evidence is never
        # silently reused; a subsequent normal carrier write upgrades it.
        completion["previous_b1_scope_reuse_candidate_count"] = derived_candidate_count
        completion["predecessor_b1_revalidation_pending"] = derived_candidate_count > 0
        return

    candidate_count = completion.get("previous_b1_scope_reuse_candidate_count")
    pending = completion.get("predecessor_b1_revalidation_pending")
    if (
        type(candidate_count) is not int
        or candidate_count < 0
        or not isinstance(pending, bool)
        or candidate_count != derived_candidate_count
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")

    if keys == pending_keys:
        if pending is not (candidate_count > 0):
            raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")
        return

    if keys != qualified_keys or (
        candidate_count <= 0
        or pending
        or completion.get("previous_b1_scope_reuse") != "QUALIFIED"
    ):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_COMPLETION_SHAPE_INVALID")


def _write_record(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    outer = {
        "schema": _RECORD_SCHEMA,
        "version": _RECORD_VERSION,
        "payload": payload,
        "digest": _digest(payload),
    }
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_TEMPORARY_EXISTS")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_intent_text(outer) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_WRITE_FAILED") from exc


def _ordered_scope_entries(record: dict[str, Any]) -> list[dict[str, Any]]:
    scopes = record.get("scopes")
    if not isinstance(scopes, list) or any(not isinstance(item, dict) for item in scopes):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_RECORD_SCOPE_SET_INVALID")
    return sorted(scopes, key=lambda item: _scope_key_from_payload(item.get("scope_key")).canonical_key)


def _source_plan_for_key(request: RootP3SourceAdmissionRequest, key: RootScopeKey) -> RootSourceScopePlan:
    matches = [item for item in request.source_scope_plans if item.scope_key == key]
    if len(matches) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_PLAN_MISSING")
    return matches[0]


def _scope_key_from_plan(plan: MigrationRuntimeScopePlan) -> RootScopeKey:
    if plan.scope_kind == "PRIVATE_AGENT":
        return RootScopeKey(plan.workspace_id, RootScopeKind.PRIVATE, agent_id=plan.agent_id)
    if plan.scope_kind == "SHARED_DOMAIN":
        return RootScopeKey(plan.workspace_id, RootScopeKind.SHARED, domain_id=plan.domain_id)
    raise ValueError("scope plan kind is unsupported")


def _scope_key_from_payload(value: object) -> RootScopeKey:
    if not isinstance(value, dict):
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_KEY_INVALID")
    try:
        return RootScopeKey(
            value["workspace_id"], RootScopeKind(value["scope_kind"]),
            agent_id=value.get("agent_id"), domain_id=value.get("domain_id"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SCOPE_KEY_INVALID") from exc


def _scope_token(scope: RootScopeKey) -> str:
    value = "-".join(scope.canonical_key)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _p1_legacy_source_namespace_key(
    connection: sqlite3.Connection,
    namespace_id: UUID,
) -> str:
    """Recover the exact P1 namespace pair without creating or repairing it."""

    rows = connection.execute(
        "SELECT source_key FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?",
        (namespace_id.bytes,),
    ).fetchall()
    if len(rows) != 1:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_MISSING")
    source_key = rows[0][0]
    if not isinstance(source_key, str) or not source_key.strip():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_KEY_INVALID")
    reverse_rows = connection.execute(
        "SELECT legacy_source_namespace_id FROM legacy_source_namespaces WHERE source_key=?",
        (source_key,),
    ).fetchall()
    if len(reverse_rows) != 1 or reverse_rows[0][0] != namespace_id.bytes:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_SOURCE_NAMESPACE_BINDING_MISMATCH")
    return source_key


def _require_p1_motif_alias_separation(
    connection: sqlite3.Connection,
    scope_plan: MigrationRuntimeScopePlan,
) -> None:
    """Prove B4's shared routing alias exists as a P1 prerequisite fact."""

    if scope_plan.motif_alias_namespace_id == scope_plan.legacy_source_namespace_id:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_MOTIF_ALIAS_COLLAPSED")
    rows = connection.execute(
        "SELECT source_key FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?",
        (native_id_to_bytes(scope_plan.motif_alias_namespace_id),),
    ).fetchall()
    if len(rows) != 1 or not isinstance(rows[0][0], str) or not rows[0][0].strip():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_P1_MOTIF_ALIAS_MISSING")


def _stage_key(request: RootP3SourceAdmissionRequest, entry: dict[str, Any], stage: str, suffix: str) -> str:
    scope = _scope_key_from_payload(entry.get("scope_key"))
    return f"{request.operation_key}:{stage}:{'|'.join(scope.canonical_key)}:{suffix}"


def _directory(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir() or path.is_symlink():
        raise ValueError(f"{label} must be an existing non-symlink directory")
    return path


def _require_regular_source_inside_root(root: Path, source: Path) -> None:
    """Reject link/reparse traversal before copying declared source evidence."""

    try:
        relative = source.relative_to(root)
    except ValueError as exc:
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_PATH_ESCAPES_ROOT") from exc
    candidate = root
    for part in relative.parts:
        candidate /= part
        try:
            information = candidate.lstat()
        except OSError as exc:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_NOT_REGULAR") from exc
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        attributes = getattr(information, "st_file_attributes", 0)
        if stat.S_ISLNK(information.st_mode) or attributes & reparse_flag:
            raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_LINK_OR_REPARSE_REFUSED")
    if not source.is_file():
        raise RootP3SourceAdmissionRefused("P3_CARRIER_SOURCE_EVIDENCE_NOT_REGULAR")


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_intent_text(value).encode("utf-8")).hexdigest()


def _require_mapping(value: object, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_list(value: object, code: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_nonnegative_int(value: object, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RootP3SourceAdmissionRefused(code)
    return value


def _require_uuid(value: object, code: str) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str) or not value:
        raise RootP3SourceAdmissionRefused(code)
    try:
        return UUID(value)
    except (TypeError, ValueError) as exc:
        raise RootP3SourceAdmissionRefused(code) from exc


__all__ = [
    "NativeRootP3SourceAdmissionService",
    "RootP3CertifiedRefusalSourceMember",
    "RootP3ScopeBinding",
    "RootP3SourceAdmissionInterrupted",
    "RootP3SourceAdmissionInterruptionPoint",
    "RootP3SourceAdmissionRefused",
    "RootP3SourceAdmissionRequest",
    "RootP3SourceAdmissionResult",
    "p3_child_request_counts",
    "pre_b1_p3_scope_shape_counts",
]
