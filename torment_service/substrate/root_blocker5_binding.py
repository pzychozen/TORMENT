"""Synthetic/offline evidence bridge for generalized root Blocker-5 admission.

The types here bind the already-existing root description, normalizer and
durable membership evidence into the existing selector/core lifecycle.  They
do not discover arbitrary files, start a service, contact a representation
provider, or create another deployment authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import sqlite3
from typing import Protocol
from uuid import UUID

from .deployment_types import (
    FROZEN_ROOT_GEOMETRY_DISPOSITIONS,
    QualifiedDeploymentProfile,
    RootAdmissionCompletionWitness,
    RootDispositionExecutionReceipt,
    RootDispositionOwnerResult,
    canonical_json,
    digest_mapping,
    require_digest,
)
from .errors import DeploymentAuthorityError
from .migration.root_admission_description import RootNativeProductionAdmissionDescription
from .migration.root_normalization import RootNormalizationResult
from .migration.root_scope import RootScopeKey, RootScopeKind
from .root_profile import RootProfileGenerationRef
from .root_scope_membership import RootScopeMembershipRuntime
from .runtime_binding import NativeMemoryRuntimeScope


class RootBlocker5BindingRefused(DeploymentAuthorityError):
    """The synthetic root bridge lacks exact pre-P6 evidence."""


@dataclass(frozen=True)
class RootWriterFreezeWitness:
    """Root-scoped writer-drain evidence; it owns no global transaction."""

    data_root_identity: str
    writer_freeze_operation_identity: str
    writer_evidence_digest: str

    def __post_init__(self) -> None:
        for name in ("data_root_identity", "writer_freeze_operation_identity"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise RootBlocker5BindingRefused(f"root writer freeze {name} must be non-empty text")
        require_digest(self.writer_evidence_digest, "writer_evidence_digest")

    @property
    def digest(self) -> str:
        return digest_mapping(self.payload())

    def payload(self) -> dict[str, str]:
        return {
            "data_root_identity": self.data_root_identity,
            "writer_freeze_operation_identity": self.writer_freeze_operation_identity,
            "writer_evidence_digest": self.writer_evidence_digest,
        }


@dataclass(frozen=True)
class RootDiscoveredCensus:
    """Deterministic canonical-layout discovery, never an arbitrary tree scan."""

    workspace_ids: tuple[str, ...]
    materialized_scope_keys: tuple[RootScopeKey, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_ids, tuple) or any(
            not isinstance(item, str) or not item for item in self.workspace_ids
        ):
            raise RootBlocker5BindingRefused("discovered workspace identities must be typed")
        if not isinstance(self.materialized_scope_keys, tuple) or any(
            not isinstance(item, RootScopeKey) for item in self.materialized_scope_keys
        ):
            raise RootBlocker5BindingRefused("discovered root scope keys must be typed")
        workspaces = tuple(sorted(self.workspace_ids))
        keys = tuple(sorted(self.materialized_scope_keys, key=lambda item: item.canonical_key))
        if len(set(workspaces)) != len(workspaces) or len(set(keys)) != len(keys):
            raise RootBlocker5BindingRefused("discovered root layout contains duplicate identities")
        if {item.workspace_id for item in keys} - set(workspaces):
            raise RootBlocker5BindingRefused("discovered scope has no discovered workspace")
        object.__setattr__(self, "workspace_ids", workspaces)
        object.__setattr__(self, "materialized_scope_keys", keys)

    @property
    def digest(self) -> str:
        return digest_mapping(self.payload())

    def payload(self) -> dict[str, object]:
        return {
            "workspace_ids": list(self.workspace_ids),
            "materialized_scope_keys": [item.identity_payload() for item in self.materialized_scope_keys],
        }


def discover_canonical_root_layout(*, data_root: str | Path) -> RootDiscoveredCensus:
    """Discover only ``workspaces/*/(agents|domains)/*/(private|shared)``.

    The function reads directory identities at fixed TORMENT layout boundaries.
    It neither walks a scope's contents nor fingerprints co-located files.
    """

    root = _existing_root(data_root)
    workspaces_root = root / "workspaces"
    if not workspaces_root.exists():
        return RootDiscoveredCensus((), ())
    _require_real_directory(workspaces_root, "workspaces root")
    workspace_ids: list[str] = []
    scope_keys: list[RootScopeKey] = []
    for workspace in sorted(workspaces_root.iterdir(), key=lambda item: item.name):
        if workspace.is_symlink():
            raise RootBlocker5BindingRefused("canonical workspace path must not be a symlink")
        if not workspace.is_dir():
            continue
        workspace_id = workspace.name
        workspace_ids.append(workspace_id)
        _discover_private_scope_keys(workspace, workspace_id, scope_keys)
        _discover_shared_scope_keys(workspace, workspace_id, scope_keys)
    return RootDiscoveredCensus(tuple(workspace_ids), tuple(scope_keys))


def declared_census_digest(description: RootNativeProductionAdmissionDescription) -> str:
    """Digest exactly the declared root workspace/scope census."""

    _require_description(description)
    return hashlib.sha256(
        canonical_json(description.expected_census.identity_payload()).encode("utf-8")
    ).hexdigest()


def require_discovered_declared_census_parity(
    *,
    description: RootNativeProductionAdmissionDescription,
    discovered: RootDiscoveredCensus,
) -> None:
    """Refuse both undeclared materialization and unaccounted declarations."""

    _require_description(description)
    if not isinstance(discovered, RootDiscoveredCensus):
        raise RootBlocker5BindingRefused("root completion requires a typed discovered census")
    declared_workspaces = tuple(item.workspace_id for item in description.workspace_plans)
    declared_scopes = tuple(
        scope.scope_key
        for workspace in description.workspace_plans
        for scope in workspace.materialized_scopes
    )
    if discovered.workspace_ids != declared_workspaces:
        raise RootBlocker5BindingRefused("ROOT_DISCOVERED_DECLARED_WORKSPACE_CENSUS_MISMATCH")
    if discovered.materialized_scope_keys != tuple(
        sorted(declared_scopes, key=lambda item: item.canonical_key)
    ):
        raise RootBlocker5BindingRefused("ROOT_DISCOVERED_DECLARED_SCOPE_CENSUS_MISMATCH")


@dataclass(frozen=True)
class RootGeometryDispositionPlanEntry:
    owner_identity: str
    disposition: str
    source_observation_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.owner_identity, str) or not self.owner_identity:
            raise RootBlocker5BindingRefused("geometry disposition owner identity must be non-empty text")
        if not isinstance(self.disposition, str) or not self.disposition or "UNRESOLVED" in self.disposition:
            raise RootBlocker5BindingRefused("geometry disposition must be resolved")
        require_digest(self.source_observation_digest, "geometry disposition source_observation_digest")

    def payload(self) -> dict[str, str]:
        return {
            "owner_identity": self.owner_identity,
            "disposition": self.disposition,
            "source_observation_digest": self.source_observation_digest,
        }


@dataclass(frozen=True)
class RootGeometryDispositionPlan:
    """The frozen owner-specific plan that must be fully resolved before P6."""

    entries: tuple[RootGeometryDispositionPlanEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not self.entries:
            raise RootBlocker5BindingRefused("geometry disposition plan requires entries")
        if any(not isinstance(item, RootGeometryDispositionPlanEntry) for item in self.entries):
            raise RootBlocker5BindingRefused("geometry disposition plan entries must be typed")
        ordered = tuple(sorted(self.entries, key=lambda item: item.owner_identity))
        if len({item.owner_identity for item in ordered}) != len(ordered):
            raise RootBlocker5BindingRefused("geometry disposition owners must be unique")
        required = {item[0] for item in FROZEN_ROOT_GEOMETRY_DISPOSITIONS}
        if {item.owner_identity for item in ordered} != required:
            raise RootBlocker5BindingRefused("geometry disposition plan does not cover the frozen owner table")
        object.__setattr__(self, "entries", ordered)

    @property
    def digest(self) -> str:
        return digest_mapping({"entries": [item.payload() for item in self.entries]})


def frozen_root_geometry_disposition_plan(
    *, external_owner_observation_digest: str,
) -> RootGeometryDispositionPlan:
    """Return the one ratified owner-specific plan with derived source proof."""

    require_digest(external_owner_observation_digest, "external_owner_observation_digest")
    return RootGeometryDispositionPlan(tuple(
        RootGeometryDispositionPlanEntry(
            owner_identity=owner,
            disposition=disposition,
            source_observation_digest=digest_mapping({
                "external_owner_observation_digest": external_owner_observation_digest,
                "owner_identity": owner,
            }),
        )
        for owner, disposition in FROZEN_ROOT_GEOMETRY_DISPOSITIONS
    ))


@dataclass(frozen=True)
class RootAdmissionEnvelope:
    """P2-frozen root identity used as the existing selector descriptor digest."""

    description: RootNativeProductionAdmissionDescription
    writer_freeze: RootWriterFreezeWitness
    discovered_census: RootDiscoveredCensus
    geometry_disposition_plan: RootGeometryDispositionPlan
    effective_profile: QualifiedDeploymentProfile
    native_staging_core_id: UUID
    root_profile: RootProfileGenerationRef
    root_membership_closure_digest: str

    def __post_init__(self) -> None:
        _require_description(self.description)
        if not isinstance(self.writer_freeze, RootWriterFreezeWitness):
            raise RootBlocker5BindingRefused("root envelope requires writer freeze evidence")
        if self.writer_freeze.data_root_identity != self.description.data_root_identity:
            raise RootBlocker5BindingRefused("root writer freeze names another data root")
        if not isinstance(self.discovered_census, RootDiscoveredCensus):
            raise RootBlocker5BindingRefused("root envelope requires discovered census evidence")
        require_discovered_declared_census_parity(
            description=self.description, discovered=self.discovered_census,
        )
        if not isinstance(self.geometry_disposition_plan, RootGeometryDispositionPlan):
            raise RootBlocker5BindingRefused("root envelope requires geometry disposition plan")
        if not isinstance(self.effective_profile, QualifiedDeploymentProfile) or not self.effective_profile.is_qualified:
            raise RootBlocker5BindingRefused("root envelope requires a qualified deployment profile")
        if self.native_staging_core_id != self.root_profile.core_id:
            raise RootBlocker5BindingRefused("root profile belongs to another staging core")
        require_digest(self.root_membership_closure_digest, "root_membership_closure_digest")
        _require_profile_matches_description(self.effective_profile, self.description)

    @property
    def digest(self) -> str:
        return digest_mapping(self.payload())

    def payload(self) -> dict[str, object]:
        return {
            "data_root_identity": self.description.data_root_identity,
            "root_description_digest": self.description.identity_digest,
            "writer_freeze": self.writer_freeze.payload(),
            "declared_census_digest": declared_census_digest(self.description),
            "discovered_census_digest": self.discovered_census.digest,
            "manifest_digest": self.description.explicit_source_manifest.digest,
            "external_owner_observation_digest": self.description.external_owner_observation_digest,
            "geometry_disposition_table_digest": self.geometry_disposition_plan.digest,
            "target_representation_identity": _target_representation_identity(self.description),
            "native_staging_core_id": str(self.native_staging_core_id),
            "qualified_deployment_profile_digest": self.effective_profile.digest,
            "root_profile": self.root_profile.payload(),
            "root_membership_closure_digest": self.root_membership_closure_digest,
        }


def build_root_admission_envelope(
    *,
    data_root: str | Path,
    description: RootNativeProductionAdmissionDescription,
    writer_freeze: RootWriterFreezeWitness,
    geometry_disposition_plan: RootGeometryDispositionPlan,
    effective_profile: QualifiedDeploymentProfile,
    native_staging_core_id: UUID,
    root_profile: RootProfileGenerationRef,
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
    connection: sqlite3.Connection,
) -> RootAdmissionEnvelope:
    """Build P2 identity only after manifest, census and membership agreement."""

    _verify_manifest(data_root=data_root, description=description)
    discovered = discover_canonical_root_layout(data_root=data_root)
    require_discovered_declared_census_parity(description=description, discovered=discovered)
    closure = root_membership_closure_digest(
        connection=connection,
        profile=root_profile,
        runtime_scopes=runtime_scopes,
        declared_scope_keys=_declared_scope_keys(description),
    )
    return RootAdmissionEnvelope(
        description=description,
        writer_freeze=writer_freeze,
        discovered_census=discovered,
        geometry_disposition_plan=geometry_disposition_plan,
        effective_profile=effective_profile,
        native_staging_core_id=native_staging_core_id,
        root_profile=root_profile,
        root_membership_closure_digest=closure,
    )


@dataclass(frozen=True)
class RootCompletionVerification:
    envelope: RootAdmissionEnvelope
    normalization_closure_digest: str
    completion_witness: RootAdmissionCompletionWitness


def verify_root_completion(
    *,
    data_root: str | Path,
    envelope: RootAdmissionEnvelope,
    normalization: RootNormalizationResult,
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
    connection: sqlite3.Connection,
) -> RootCompletionVerification:
    """Perform the P4/pre-P6 root agreement checks without mutation."""

    if not isinstance(normalization, RootNormalizationResult):
        raise RootBlocker5BindingRefused("root completion requires a normalization result")
    _verify_manifest(data_root=data_root, description=envelope.description)
    current_discovered = discover_canonical_root_layout(data_root=data_root)
    require_discovered_declared_census_parity(
        description=envelope.description, discovered=current_discovered,
    )
    if current_discovered.digest != envelope.discovered_census.digest:
        raise RootBlocker5BindingRefused("ROOT_DISCOVERED_CENSUS_DRIFT")
    current_membership = root_membership_closure_digest(
        connection=connection,
        profile=envelope.root_profile,
        runtime_scopes=runtime_scopes,
        declared_scope_keys=_declared_scope_keys(envelope.description),
    )
    if current_membership != envelope.root_membership_closure_digest:
        raise RootBlocker5BindingRefused("ROOT_MEMBERSHIP_CLOSURE_DRIFT")
    _require_normalization_complete(normalization, envelope.description)
    closure = normalization_closure_digest(normalization)
    completion = RootAdmissionCompletionWitness(
        data_root_identity=envelope.description.data_root_identity,
        root_admission_envelope_digest=envelope.digest,
        declared_census_digest=declared_census_digest(envelope.description),
        discovered_census_digest=current_discovered.digest,
        manifest_digest=envelope.description.explicit_source_manifest.digest,
        external_owner_observation_digest=envelope.description.external_owner_observation_digest,
        geometry_disposition_table_digest=envelope.geometry_disposition_plan.digest,
        target_representation_identity=_target_representation_identity(envelope.description),
        root_writer_freeze_witness_digest=envelope.writer_freeze.digest,
        native_staging_core_id=envelope.native_staging_core_id,
        qualified_deployment_profile_digest=envelope.effective_profile.digest,
        root_profile_object_id=envelope.root_profile.profile_object_id,
        root_profile_revision_id=envelope.root_profile.profile_revision_id,
        root_profile_ordinal=envelope.root_profile.profile_revision_ordinal,
        root_membership_closure_digest=current_membership,
        normalization_closure_digest=closure,
    )
    return RootCompletionVerification(envelope, closure, completion)


class SyntheticRootDispositionAdapter(Protocol):
    """Narrow synthetic owner seam; real external owners are intentionally absent."""

    def execute(
        self,
        *,
        entry: RootGeometryDispositionPlanEntry,
        root_admission_envelope_digest: str,
        geometry_transition_identity: str,
    ) -> str: ...


def execute_synthetic_root_disposition_plan(
    *,
    envelope: RootAdmissionEnvelope,
    adapter: SyntheticRootDispositionAdapter,
) -> RootDispositionExecutionReceipt:
    """Build deterministic, idempotency-addressable post-P6 receipt evidence."""

    # Protocol runtime checks cannot validate method shape; keep a narrow
    # structural check and never inspect real owner modules.
    if not callable(getattr(adapter, "execute", None)):
        raise RootBlocker5BindingRefused("synthetic disposition adapter must expose execute")
    transition = f"ROOT_GEOMETRY_EPOCH:{envelope.digest}"
    results = tuple(
        RootDispositionOwnerResult(
            owner_identity=entry.owner_identity,
            source_observation_digest=entry.source_observation_digest,
            disposition=entry.disposition,
            outcome=_synthetic_outcome(
                adapter=adapter,
                entry=entry,
                root_admission_envelope_digest=envelope.digest,
                geometry_transition_identity=transition,
            ),
            geometry_transition_identity=transition,
        )
        for entry in envelope.geometry_disposition_plan.entries
    )
    return RootDispositionExecutionReceipt(
        root_admission_envelope_digest=envelope.digest,
        native_staging_core_id=envelope.native_staging_core_id,
        geometry_disposition_table_digest=envelope.geometry_disposition_plan.digest,
        geometry_transition_identity=transition,
        owner_results=results,
    )


def root_membership_closure_digest(
    *,
    connection: sqlite3.Connection,
    profile: RootProfileGenerationRef,
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
    declared_scope_keys: tuple[RootScopeKey, ...],
) -> str:
    """Bind durable memberships to supplied namespace/runtime bundles exactly."""

    runtime = RootScopeMembershipRuntime(
        connection=connection, profile=profile, runtime_scopes=runtime_scopes,
    )
    members = tuple(runtime.resolve(key.scope_key) for key in runtime.cache_keys)
    actual = tuple(member.runtime_key.scope_key for member in members)
    expected = tuple(sorted(declared_scope_keys, key=lambda item: item.canonical_key))
    if actual != expected:
        raise RootBlocker5BindingRefused("ROOT_MEMBERSHIP_CLOSURE_MISMATCH")
    return digest_mapping({
        "profile": profile.payload(),
        "members": [
            {
                "scope_key": member.runtime_key.scope_key.identity_payload(),
                "semantic_scope_id": str(member.runtime_scope.semantic_scope_id),
                "identity_namespace_id": str(member.runtime_scope.identity_namespace_id),
                "legacy_source_namespace_id": str(member.runtime_scope.legacy_source_namespace_id),
                "membership_revision_id": str(member.record.relationship_revision_id),
                "membership_revision_ordinal": member.record.relationship_revision_ordinal,
                "membership_witness": member.record.witness.payload(),
            }
            for member in members
        ],
    })


def normalization_closure_digest(result: RootNormalizationResult) -> str:
    """Digest the normalized root closure without making it activation authority."""

    if not isinstance(result, RootNormalizationResult):
        raise RootBlocker5BindingRefused("normalization closure requires a typed result")
    return digest_mapping({
        "recovery_witness": {
            "root_description_digest": result.recovery_witness.root_description_digest,
            "expected_census_digest": result.recovery_witness.expected_census_digest,
            "source_manifest_digest": result.recovery_witness.source_manifest_digest,
            "native_staging_core_id": str(result.recovery_witness.native_staging_core_id),
        },
        "expected_workspace_count": result.expected_workspace_count,
        "observed_workspace_closure": result.observed_workspace_closure,
        "expected_materialized_scope_count": result.expected_materialized_scope_count,
        "observed_materialized_scope_closure": result.observed_materialized_scope_closure,
        "workspace_results": [
            {
                "workspace_id": item.workspace_id,
                "declared_materialized_scope_count": item.declared_materialized_scope_count,
                "observed_materialized_scope_count": item.observed_materialized_scope_count,
                "completed": item.completed,
            }
            for item in result.workspace_results
        ],
        "scope_results": [
            {
                "scope_key": item.scope_key.identity_payload(),
                "representation_disposition": item.representation_disposition.value,
                "completed": item.completed,
                "representation_results": [
                    {
                        "kind": receipt.kind.value,
                        "eid": receipt.eid,
                        "representation_id": (
                            None if receipt.representation_id is None else str(receipt.representation_id)
                        ),
                        "state": receipt.state.value,
                        "reason_code": receipt.reason_code,
                        "metadata_less_source_evidence_identity": receipt.metadata_less_source_evidence_identity,
                    }
                    for receipt in item.representation_results
                ],
                "motif_results": [
                    {
                        "lineage": receipt.lineage.value,
                        "runtime_motif_id": receipt.runtime_motif_id,
                        "motif_object_id": None if receipt.motif_object_id is None else str(receipt.motif_object_id),
                        "state": receipt.state.value,
                        "reason_code": receipt.reason_code,
                    }
                    for receipt in item.motif_results
                ],
            }
            for item in result.scope_results
        ],
        "source_manifest_recheck_passed": result.source_manifest_recheck_passed,
        "root_normalization_complete": result.root_normalization_complete,
        "root_normalization_ready": result.root_normalization_ready,
        "partial_activation": result.partial_activation,
        "reason_codes": list(result.reason_codes),
    })


def _discover_private_scope_keys(
    workspace: Path, workspace_id: str, result: list[RootScopeKey]) -> None:
    agents = workspace / "agents"
    if not agents.exists():
        return
    _require_real_directory(agents, "workspace agents directory")
    for agent in sorted(agents.iterdir(), key=lambda item: item.name):
        if agent.is_symlink():
            raise RootBlocker5BindingRefused("canonical agent path must not be a symlink")
        if not agent.is_dir():
            continue
        private = agent / "private"
        if private.exists():
            _require_real_directory(private, "canonical private scope")
            result.append(RootScopeKey(workspace_id, RootScopeKind.PRIVATE, agent_id=agent.name))


def _discover_shared_scope_keys(workspace: Path, workspace_id: str, result: list[RootScopeKey]) -> None:
    domains = workspace / "domains"
    if not domains.exists():
        return
    _require_real_directory(domains, "workspace domains directory")
    for domain in sorted(domains.iterdir(), key=lambda item: item.name):
        if domain.is_symlink():
            raise RootBlocker5BindingRefused("canonical domain path must not be a symlink")
        if not domain.is_dir():
            continue
        shared = domain / "shared"
        if shared.exists():
            _require_real_directory(shared, "canonical shared scope")
            result.append(RootScopeKey(workspace_id, RootScopeKind.SHARED, domain_id=domain.name))


def _verify_manifest(*, data_root: str | Path, description: RootNativeProductionAdmissionDescription) -> None:
    try:
        description.explicit_source_manifest.verify(data_root=data_root)
    except Exception as exc:
        raise RootBlocker5BindingRefused("ROOT_SOURCE_MANIFEST_DRIFT") from exc


def _require_normalization_complete(
    result: RootNormalizationResult,
    description: RootNativeProductionAdmissionDescription,
) -> None:
    expected = description.expected_census
    if (
        not result.source_manifest_recheck_passed
        or not result.root_normalization_complete
        or not result.root_normalization_ready
        or result.partial_activation
        or result.reason_codes
        or result.expected_workspace_count != expected.workspace_count
        or result.observed_workspace_closure != expected.workspace_count
        or result.expected_materialized_scope_count != expected.total_materialized_scope_count
        or result.observed_materialized_scope_closure != expected.total_materialized_scope_count
    ):
        raise RootBlocker5BindingRefused("ROOT_NORMALIZATION_CLOSURE_INCOMPLETE")


def _require_profile_matches_description(
    profile: QualifiedDeploymentProfile,
    description: RootNativeProductionAdmissionDescription,
) -> None:
    lane = description.target_representation_lane
    if (
        profile.compression_enabled
        or profile.deep_memory_enabled
        or profile.representation_provider != lane.provider
        or profile.representation_model != lane.model
        or profile.representation_dimension != lane.dimension
    ):
        raise RootBlocker5BindingRefused("ROOT_QUALIFIED_PROFILE_TARGET_LANE_MISMATCH")


def _target_representation_identity(description: RootNativeProductionAdmissionDescription) -> str:
    lane = description.target_representation_lane
    return f"{lane.provider}:{lane.model}:{lane.dimension}:{lane.representation_class}"


def _declared_scope_keys(description: RootNativeProductionAdmissionDescription) -> tuple[RootScopeKey, ...]:
    return tuple(sorted(
        (
            scope.scope_key
            for workspace in description.workspace_plans
            for scope in workspace.materialized_scopes
        ),
        key=lambda item: item.canonical_key,
    ))


def _synthetic_outcome(
    *,
    adapter: SyntheticRootDispositionAdapter,
    entry: RootGeometryDispositionPlanEntry,
    root_admission_envelope_digest: str,
    geometry_transition_identity: str,
) -> str:
    outcome = adapter.execute(
        entry=entry,
        root_admission_envelope_digest=root_admission_envelope_digest,
        geometry_transition_identity=geometry_transition_identity,
    )
    if not isinstance(outcome, str) or not outcome:
        raise RootBlocker5BindingRefused("synthetic disposition adapter returned an invalid outcome")
    return outcome


def _existing_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise RootBlocker5BindingRefused("root layout discovery requires a data root")
    root = Path(value).expanduser().resolve()
    _require_real_directory(root, "data root")
    return root


def _require_real_directory(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_dir():
        raise RootBlocker5BindingRefused(f"{label} must be a non-symlink directory")


def _require_description(value: object) -> RootNativeProductionAdmissionDescription:
    if not isinstance(value, RootNativeProductionAdmissionDescription):
        raise RootBlocker5BindingRefused("root bridge requires RootNativeProductionAdmissionDescription")
    return value


__all__ = [
    "RootAdmissionEnvelope",
    "RootBlocker5BindingRefused",
    "RootCompletionVerification",
    "RootDiscoveredCensus",
    "RootGeometryDispositionPlan",
    "RootGeometryDispositionPlanEntry",
    "RootWriterFreezeWitness",
    "SyntheticRootDispositionAdapter",
    "build_root_admission_envelope",
    "declared_census_digest",
    "discover_canonical_root_layout",
    "execute_synthetic_root_disposition_plan",
    "frozen_root_geometry_disposition_plan",
    "normalization_closure_digest",
    "require_discovered_declared_census_parity",
    "root_membership_closure_digest",
    "verify_root_completion",
]
