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
from typing import Any, Protocol
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
from .canonical_intent import canonical_intent_text
from .errors import DeploymentAuthorityError
from .migration.root_admission_description import RootNativeProductionAdmissionDescription
from .migration.root_normalization import RootNormalizationResult
from .migration.root_scope import RootScopeKey, RootScopeKind
from .migration.runtime_readiness import MigrationRuntimeScopePlan
from .root_profile import RootProfileGenerationRef
from .root_scope_membership import RootScopeMembershipRuntime
from .runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from .writer_freeze_evidence import (
    RootWriterFreezeEvidencePayload,
    RootWriterFreezeEvidenceRefused,
    RootWriterFreezeRecheck,
    bind_root_writer_freeze_witness,
    recheck_root_writer_freeze_evidence,
)


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


def root_runtime_scope_plan_digest(
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...],
    target_representation_lane: NativeRepresentationLane,
) -> str:
    """Digest the canonical root-qualified runtime plans without inference."""

    return digest_mapping({
        "runtime_scope_plans": [
            _runtime_scope_plan_payload(plan, target_representation_lane)
            for plan in _ordered_runtime_scope_plans(runtime_scope_plans)
        ],
    })


def root_runtime_scope_plan_payloads(
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...],
    target_representation_lane: NativeRepresentationLane,
) -> tuple[dict[str, object], ...]:
    """Expose the exact recoverable plan tuple used by the root envelope."""

    return tuple(
        _runtime_scope_plan_payload(plan, target_representation_lane)
        for plan in _ordered_runtime_scope_plans(runtime_scope_plans)
    )


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
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    writer_freeze_evidence: RootWriterFreezeEvidencePayload | None = None
    writer_freeze_recheck: RootWriterFreezeRecheck | None = None

    def __post_init__(self) -> None:
        _require_description(self.description)
        if not isinstance(self.writer_freeze, RootWriterFreezeWitness):
            raise RootBlocker5BindingRefused("root envelope requires writer freeze evidence")
        if self.writer_freeze.data_root_identity != self.description.data_root_identity:
            raise RootBlocker5BindingRefused("root writer freeze names another data root")
        if self.writer_freeze_evidence is None:
            if self.writer_freeze_recheck is not None:
                raise RootBlocker5BindingRefused("root writer freeze recheck requires payload evidence")
        else:
            if not isinstance(self.writer_freeze_evidence, RootWriterFreezeEvidencePayload):
                raise RootBlocker5BindingRefused("root envelope writer freeze payload must be typed")
            if not isinstance(self.writer_freeze_recheck, RootWriterFreezeRecheck):
                raise RootBlocker5BindingRefused("root envelope requires a fresh writer freeze recheck")
            try:
                bind_root_writer_freeze_witness(
                    payload=self.writer_freeze_evidence, witness=self.writer_freeze,
                )
            except RootWriterFreezeEvidenceRefused as exc:
                raise RootBlocker5BindingRefused("root writer freeze witness payload mismatch") from exc
            if (
                self.writer_freeze_evidence.external_owner_observation_digest
                != self.description.external_owner_observation_digest
            ):
                raise RootBlocker5BindingRefused("root writer freeze external owner evidence disagrees")
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
        ordered = _ordered_runtime_scope_plans(self.runtime_scope_plans)
        _require_runtime_scope_plan_description_parity(ordered, self.description)
        if (
            self.effective_profile.admitted_scope_plan_digest
            != root_runtime_scope_plan_digest(ordered, self.description.target_representation_lane)
        ):
            raise RootBlocker5BindingRefused("ROOT_QUALIFIED_PROFILE_SCOPE_PLAN_MISMATCH")
        object.__setattr__(self, "runtime_scope_plans", ordered)

    @property
    def digest(self) -> str:
        return digest_mapping(self.payload())

    def payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
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
            "root_runtime_scope_plan_digest": root_runtime_scope_plan_digest(
                self.runtime_scope_plans, self.description.target_representation_lane,
            ),
        }
        if self.writer_freeze_evidence is not None:
            payload.update({
                "writer_freeze_evidence_digest": self.writer_freeze_evidence.digest,
                "frozen_workspaces_tree_digest": self.writer_freeze_evidence.source_tree_snapshot.tree_digest,
            })
        return payload


@dataclass(frozen=True)
class RootAdmissionEnvelopeRecord:
    """Immutable v2 recovery evidence persisted in the existing core stream.

    This is a subordinate copy of the P2-frozen proposition.  Its envelope
    digest remains the sole selector/core/completion identity; the record does
    not mint another deployment or completion authority.
    """

    envelope_digest: str
    envelope_payload: dict[str, object]
    root_description_payload: dict[str, object]
    declared_census_payload: dict[str, object]
    discovered_census_payload: dict[str, object]
    writer_freeze_payload: dict[str, str]
    target_representation_lane: NativeRepresentationLane
    geometry_disposition_entries: tuple[dict[str, str], ...]
    effective_profile_payload: dict[str, object]
    root_profile_payload: dict[str, object]
    root_membership_closure_digest: str
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...]

    CONTRACT = "TORMENT_ROOT_ADMISSION_ENVELOPE_RECORD"
    VERSION = 1

    def __post_init__(self) -> None:
        require_digest(self.envelope_digest, "root admission envelope digest")
        if not isinstance(self.envelope_payload, dict) or not isinstance(self.root_description_payload, dict):
            raise RootBlocker5BindingRefused("root envelope record payloads must be mappings")
        if not isinstance(self.declared_census_payload, dict) or not isinstance(self.discovered_census_payload, dict):
            raise RootBlocker5BindingRefused("root envelope record census payloads must be mappings")
        if not isinstance(self.writer_freeze_payload, dict) or not isinstance(self.effective_profile_payload, dict):
            raise RootBlocker5BindingRefused("root envelope record evidence payloads must be mappings")
        if not isinstance(self.root_profile_payload, dict):
            raise RootBlocker5BindingRefused("root envelope record profile payload must be a mapping")
        if not isinstance(self.target_representation_lane, NativeRepresentationLane):
            raise RootBlocker5BindingRefused("root envelope record lane must be typed")
        if not isinstance(self.geometry_disposition_entries, tuple) or any(
            not isinstance(item, dict) for item in self.geometry_disposition_entries
        ):
            raise RootBlocker5BindingRefused("root envelope record geometry entries must be typed")
        ordered = _ordered_runtime_scope_plans(self.runtime_scope_plans)
        scope_digest = root_runtime_scope_plan_digest(ordered, self.target_representation_lane)
        required_envelope_keys = {
            "data_root_identity", "root_description_digest", "writer_freeze",
            "declared_census_digest", "discovered_census_digest", "manifest_digest",
            "external_owner_observation_digest", "geometry_disposition_table_digest",
            "target_representation_identity", "native_staging_core_id",
            "qualified_deployment_profile_digest", "root_profile",
            "root_membership_closure_digest", "root_runtime_scope_plan_digest",
        }
        freeze_evidence_keys = {
            "writer_freeze_evidence_digest", "frozen_workspaces_tree_digest",
        }
        actual_envelope_keys = set(self.envelope_payload)
        if (
            actual_envelope_keys != required_envelope_keys
            and actual_envelope_keys != required_envelope_keys | freeze_evidence_keys
        ):
            raise RootBlocker5BindingRefused("root envelope record envelope payload is noncanonical")
        if freeze_evidence_keys <= actual_envelope_keys:
            require_digest(self.envelope_payload["writer_freeze_evidence_digest"], "writer freeze evidence digest")
            require_digest(self.envelope_payload["frozen_workspaces_tree_digest"], "frozen workspaces tree digest")
        if self.envelope_digest != digest_mapping(self.envelope_payload):
            raise RootBlocker5BindingRefused("root envelope record digest does not recompute")
        if self.envelope_payload.get("root_description_digest") != hashlib.sha256(
            canonical_intent_text(self.root_description_payload).encode("utf-8")
        ).hexdigest():
            raise RootBlocker5BindingRefused("root envelope record root description disagrees")
        if (
            self.envelope_payload.get("data_root_identity")
            != self.root_description_payload.get("data_root_identity")
            or self.root_description_payload.get("target_representation_lane")
            != _lane_payload(self.target_representation_lane)
            or self.root_description_payload.get("expected_census") != self.declared_census_payload
        ):
            raise RootBlocker5BindingRefused("root envelope record root description facts disagree")
        if self.envelope_payload.get("root_runtime_scope_plan_digest") != scope_digest:
            raise RootBlocker5BindingRefused("root envelope record scope-plan digest disagrees")
        if self.envelope_payload.get("qualified_deployment_profile_digest") != _profile_digest_from_payload(
            self.effective_profile_payload,
        ):
            raise RootBlocker5BindingRefused("root envelope record profile payload disagrees")
        if self.envelope_payload.get("root_membership_closure_digest") != self.root_membership_closure_digest:
            raise RootBlocker5BindingRefused("root envelope record membership payload disagrees")
        root_profile = root_profile_ref_from_record_payload(self.root_profile_payload)
        if self.envelope_payload.get("root_profile") != root_profile.payload():
            raise RootBlocker5BindingRefused("root envelope record root profile disagrees")
        if self.envelope_payload.get("writer_freeze") != self.writer_freeze_payload:
            raise RootBlocker5BindingRefused("root envelope record writer freeze disagrees")
        if self.envelope_payload.get("geometry_disposition_table_digest") != digest_mapping({
            "entries": list(self.geometry_disposition_entries),
        }):
            raise RootBlocker5BindingRefused("root envelope record geometry disposition disagrees")
        if self.envelope_payload.get("declared_census_digest") != hashlib.sha256(
            canonical_json(self.declared_census_payload).encode("utf-8")
        ).hexdigest():
            raise RootBlocker5BindingRefused("root envelope record declared census disagrees")
        if self.envelope_payload.get("discovered_census_digest") != digest_mapping(
            self.discovered_census_payload,
        ):
            raise RootBlocker5BindingRefused("root envelope record discovered census disagrees")
        object.__setattr__(self, "runtime_scope_plans", ordered)

    @classmethod
    def from_envelope(cls, envelope: RootAdmissionEnvelope) -> "RootAdmissionEnvelopeRecord":
        if not isinstance(envelope, RootAdmissionEnvelope):
            raise RootBlocker5BindingRefused("root envelope record requires a typed envelope")
        return cls(
            envelope_digest=envelope.digest,
            envelope_payload=envelope.payload(),
            root_description_payload=envelope.description.canonical_payload,
            declared_census_payload=envelope.description.expected_census.identity_payload(),
            discovered_census_payload=envelope.discovered_census.payload(),
            writer_freeze_payload=envelope.writer_freeze.payload(),
            target_representation_lane=envelope.description.target_representation_lane,
            geometry_disposition_entries=tuple(item.payload() for item in envelope.geometry_disposition_plan.entries),
            effective_profile_payload=_profile_payload(envelope.effective_profile),
            root_profile_payload=_root_profile_record_payload(envelope.root_profile),
            root_membership_closure_digest=envelope.root_membership_closure_digest,
            runtime_scope_plans=envelope.runtime_scope_plans,
        )

    def payload(self) -> dict[str, object]:
        return {
            "contract": self.CONTRACT,
            "version": self.VERSION,
            "root_admission_envelope_digest": self.envelope_digest,
            "root_admission_envelope_payload": self.envelope_payload,
            "root_admission_description_payload": self.root_description_payload,
            "declared_census_payload": self.declared_census_payload,
            "discovered_census_payload": self.discovered_census_payload,
            "writer_freeze_payload": self.writer_freeze_payload,
            "target_representation_lane": _lane_payload(self.target_representation_lane),
            "geometry_disposition_entries": list(self.geometry_disposition_entries),
            "qualified_deployment_profile_payload": self.effective_profile_payload,
            "root_profile_payload": self.root_profile_payload,
            "root_membership_closure_digest": self.root_membership_closure_digest,
            "root_runtime_scope_plan_digest": root_runtime_scope_plan_digest(
                self.runtime_scope_plans, self.target_representation_lane,
            ),
            "runtime_scope_plans": list(root_runtime_scope_plan_payloads(
                self.runtime_scope_plans, self.target_representation_lane,
            )),
        }


def root_admission_envelope_record_from_payload(value: object) -> RootAdmissionEnvelopeRecord:
    """Decode one explicit versioned record; unknown shapes never downgrade."""

    if not isinstance(value, dict) or value.get("contract") != RootAdmissionEnvelopeRecord.CONTRACT:
        raise RootBlocker5BindingRefused("root envelope record contract is unsupported")
    if value.get("version") != RootAdmissionEnvelopeRecord.VERSION:
        raise RootBlocker5BindingRefused("root envelope record version is unsupported")
    required = {
        "contract", "version", "root_admission_envelope_digest", "root_admission_envelope_payload",
        "root_admission_description_payload", "declared_census_payload", "discovered_census_payload",
        "writer_freeze_payload", "target_representation_lane", "geometry_disposition_entries",
        "qualified_deployment_profile_payload", "root_profile_payload", "root_membership_closure_digest",
        "root_runtime_scope_plan_digest", "runtime_scope_plans",
    }
    if set(value) != required or not isinstance(value["runtime_scope_plans"], list):
        raise RootBlocker5BindingRefused("root envelope record shape is invalid")
    lane = _lane_from_payload(value["target_representation_lane"])
    plans = tuple(_runtime_scope_plan_from_payload(item, lane) for item in value["runtime_scope_plans"])
    record = RootAdmissionEnvelopeRecord(
        envelope_digest=value["root_admission_envelope_digest"],
        envelope_payload=value["root_admission_envelope_payload"],
        root_description_payload=value["root_admission_description_payload"],
        declared_census_payload=value["declared_census_payload"],
        discovered_census_payload=value["discovered_census_payload"],
        writer_freeze_payload=value["writer_freeze_payload"],
        target_representation_lane=lane,
        geometry_disposition_entries=tuple(value["geometry_disposition_entries"]),
        effective_profile_payload=value["qualified_deployment_profile_payload"],
        root_profile_payload=value["root_profile_payload"],
        root_membership_closure_digest=value["root_membership_closure_digest"],
        runtime_scope_plans=plans,
    )
    if value["root_runtime_scope_plan_digest"] != root_runtime_scope_plan_digest(plans, lane):
        raise RootBlocker5BindingRefused("root envelope record serialized scope-plan digest disagrees")
    if canonical_json(record.payload()) != canonical_json(value):
        raise RootBlocker5BindingRefused("root envelope record is not canonical")
    return record


def require_persisted_root_admission_envelope(
    *, envelope: RootAdmissionEnvelope, record: RootAdmissionEnvelopeRecord | None,
) -> RootAdmissionEnvelopeRecord:
    """Require a durable record equal to the already-frozen in-memory envelope."""

    if not isinstance(envelope, RootAdmissionEnvelope) or record is None:
        raise RootBlocker5BindingRefused("ROOT_ADMISSION_ENVELOPE_RECORD_REQUIRED")
    expected = RootAdmissionEnvelopeRecord.from_envelope(envelope)
    if record != expected:
        raise RootBlocker5BindingRefused("ROOT_ADMISSION_ENVELOPE_RECORD_MISMATCH")
    return record


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
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...],
    connection: sqlite3.Connection,
    writer_freeze_evidence: RootWriterFreezeEvidencePayload | None = None,
    writer_freeze_recheck: RootWriterFreezeRecheck | None = None,
    require_writer_freeze_evidence_payload: bool = False,
) -> RootAdmissionEnvelope:
    """Build P2 identity only after manifest, census and membership agreement."""

    _verify_root_writer_freeze_evidence(
        data_root=data_root,
        description=description,
        writer_freeze=writer_freeze,
        payload=writer_freeze_evidence,
        recheck=writer_freeze_recheck,
        require_payload=require_writer_freeze_evidence_payload,
    )
    _verify_manifest(data_root=data_root, description=description)
    discovered = discover_canonical_root_layout(data_root=data_root)
    require_discovered_declared_census_parity(description=description, discovered=discovered)
    _require_runtime_scope_plan_description_parity(runtime_scope_plans, description)
    closure = root_membership_closure_digest(
        connection=connection,
        profile=root_profile,
        runtime_scopes=runtime_scopes,
        declared_scope_keys=_declared_scope_keys(description),
    )
    _require_runtime_scope_plan_bindings(runtime_scope_plans, runtime_scopes)
    return RootAdmissionEnvelope(
        description=description,
        writer_freeze=writer_freeze,
        discovered_census=discovered,
        geometry_disposition_plan=geometry_disposition_plan,
        effective_profile=effective_profile,
        native_staging_core_id=native_staging_core_id,
        root_profile=root_profile,
        root_membership_closure_digest=closure,
        runtime_scope_plans=runtime_scope_plans,
        writer_freeze_evidence=writer_freeze_evidence,
        writer_freeze_recheck=writer_freeze_recheck,
    )


def build_real_root_v2_admission_envelope(
    *,
    data_root: str | Path,
    description: RootNativeProductionAdmissionDescription,
    writer_freeze: RootWriterFreezeWitness,
    geometry_disposition_plan: RootGeometryDispositionPlan,
    effective_profile: QualifiedDeploymentProfile,
    native_staging_core_id: UUID,
    root_profile: RootProfileGenerationRef,
    runtime_scopes: tuple[NativeMemoryRuntimeScope, ...],
    runtime_scope_plans: tuple[MigrationRuntimeScopePlan, ...],
    connection: sqlite3.Connection,
    writer_freeze_evidence: RootWriterFreezeEvidencePayload | None,
    writer_freeze_recheck: RootWriterFreezeRecheck | None,
) -> RootAdmissionEnvelope:
    """Build a real root-v2 envelope only from payload-bound freeze evidence.

    The historical generic builder remains available for explicitly synthetic
    and v1 compatibility rehearsals.  A future real P2 caller must enter
    through this narrow entry point, which refuses witness-only evidence
    before it reads the source root.
    """

    return build_root_admission_envelope(
        data_root=data_root,
        description=description,
        writer_freeze=writer_freeze,
        geometry_disposition_plan=geometry_disposition_plan,
        effective_profile=effective_profile,
        native_staging_core_id=native_staging_core_id,
        root_profile=root_profile,
        runtime_scopes=runtime_scopes,
        runtime_scope_plans=runtime_scope_plans,
        connection=connection,
        writer_freeze_evidence=writer_freeze_evidence,
        writer_freeze_recheck=writer_freeze_recheck,
        require_writer_freeze_evidence_payload=True,
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
    _verify_root_writer_freeze_evidence(
        data_root=data_root,
        description=envelope.description,
        writer_freeze=envelope.writer_freeze,
        payload=envelope.writer_freeze_evidence,
        recheck=envelope.writer_freeze_recheck,
    )
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


def _verify_root_writer_freeze_evidence(
    *,
    data_root: str | Path,
    description: RootNativeProductionAdmissionDescription,
    writer_freeze: RootWriterFreezeWitness,
    payload: RootWriterFreezeEvidencePayload | None,
    recheck: RootWriterFreezeRecheck | None,
    require_payload: bool = False,
) -> None:
    """Recheck an opted-in Class-B epoch; legacy witness-only callers remain valid.

    This is deliberately a verifier, not a refresh or a process controller.  A
    request that elects the new payload must supply a fresh injected recheck at
    every P2/P4/pre-P6 envelope construction.
    """

    if not isinstance(require_payload, bool):
        raise RootBlocker5BindingRefused("root writer freeze payload requirement must be boolean")
    if payload is None:
        if require_payload:
            raise RootBlocker5BindingRefused("ROOT_V2_WRITER_FREEZE_PAYLOAD_REQUIRED")
        if recheck is not None:
            raise RootBlocker5BindingRefused("root writer freeze recheck has no payload")
        return
    if not isinstance(recheck, RootWriterFreezeRecheck):
        raise RootBlocker5BindingRefused("root writer freeze fresh recheck is required")
    try:
        recheck_root_writer_freeze_evidence(
            data_root=data_root,
            payload=payload,
            witness=writer_freeze,
            recheck=recheck,
            expected_external_owner_observation_digest=description.external_owner_observation_digest,
        )
    except RootWriterFreezeEvidenceRefused as exc:
        raise RootBlocker5BindingRefused("ROOT_WRITER_FREEZE_EVIDENCE_STALE_OR_INVALID") from exc


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
        or result.expected_materialized_scope_count != expected.total_runtime_scope_count
        or result.observed_materialized_scope_closure != expected.total_runtime_scope_count
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


def _ordered_runtime_scope_plans(
    value: tuple[MigrationRuntimeScopePlan, ...],
) -> tuple[MigrationRuntimeScopePlan, ...]:
    if not isinstance(value, tuple) or any(not isinstance(item, MigrationRuntimeScopePlan) for item in value):
        raise RootBlocker5BindingRefused("root runtime scope plans must be typed")
    ordered = tuple(sorted(value, key=lambda item: _root_scope_key_from_plan(item).canonical_key))
    keys = tuple(_root_scope_key_from_plan(item) for item in ordered)
    if len(set(keys)) != len(keys):
        raise RootBlocker5BindingRefused("root runtime scope plans contain duplicate RootScopeKeys")
    return ordered


def _runtime_scope_plan_payload(
    plan: MigrationRuntimeScopePlan,
    lane: NativeRepresentationLane,
) -> dict[str, object]:
    if not isinstance(plan, MigrationRuntimeScopePlan) or not isinstance(lane, NativeRepresentationLane):
        raise RootBlocker5BindingRefused("root runtime scope plan payload requires typed facts")
    return {
        "scope_key": _root_scope_key_from_plan(plan).identity_payload(),
        "scope_plan": plan.intent(),
        "representation_lane": _lane_payload(lane),
    }


def _runtime_scope_plan_from_payload(
    value: object,
    lane: NativeRepresentationLane,
) -> MigrationRuntimeScopePlan:
    if not isinstance(value, dict) or set(value) != {"scope_key", "scope_plan", "representation_lane"}:
        raise RootBlocker5BindingRefused("root runtime scope plan record is malformed")
    if value["representation_lane"] != _lane_payload(lane):
        raise RootBlocker5BindingRefused("root runtime scope plan lane disagrees")
    scope_key = _root_scope_key_from_payload(value["scope_key"])
    plan_payload = value["scope_plan"]
    if not isinstance(plan_payload, dict) or set(plan_payload) != {
        "legacy_source_namespace_id", "workspace_id", "scope_kind", "qualifier",
        "target_identity_namespace_id", "target_semantic_scope_id", "motif_alias_namespace_id",
        "motif_identity_namespace_id", "membership_identity_namespace_id", "idempotency_namespace_id",
        "motif_domain_id",
    }:
        raise RootBlocker5BindingRefused("root runtime scope plan facts are malformed")
    try:
        plan = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=UUID(plan_payload["legacy_source_namespace_id"]),
            workspace_id=plan_payload["workspace_id"],
            scope_kind=plan_payload["scope_kind"],
            target_identity_namespace_id=UUID(plan_payload["target_identity_namespace_id"]),
            target_semantic_scope_id=UUID(plan_payload["target_semantic_scope_id"]),
            motif_alias_namespace_id=UUID(plan_payload["motif_alias_namespace_id"]),
            motif_identity_namespace_id=UUID(plan_payload["motif_identity_namespace_id"]),
            membership_identity_namespace_id=UUID(plan_payload["membership_identity_namespace_id"]),
            idempotency_namespace_id=UUID(plan_payload["idempotency_namespace_id"]),
            agent_id=scope_key.agent_id,
            domain_id=scope_key.domain_id,
            motif_domain_id=plan_payload["motif_domain_id"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RootBlocker5BindingRefused("root runtime scope plan facts are invalid") from exc
    if plan.intent() != plan_payload or _root_scope_key_from_plan(plan) != scope_key:
        raise RootBlocker5BindingRefused("root runtime scope plan facts are noncanonical")
    return plan


def _root_scope_key_from_plan(plan: MigrationRuntimeScopePlan) -> RootScopeKey:
    if plan.scope_kind == "PRIVATE_AGENT":
        return RootScopeKey(plan.workspace_id, RootScopeKind.PRIVATE, agent_id=plan.agent_id)
    if plan.scope_kind == "SHARED_DOMAIN":
        return RootScopeKey(plan.workspace_id, RootScopeKind.SHARED, domain_id=plan.domain_id)
    raise RootBlocker5BindingRefused("root runtime scope plan kind is unsupported")


def _root_scope_key_from_payload(value: object) -> RootScopeKey:
    if not isinstance(value, dict) or set(value) != {"workspace_id", "scope_kind", "agent_id", "domain_id"}:
        raise RootBlocker5BindingRefused("root runtime scope key is malformed")
    try:
        return RootScopeKey(
            value["workspace_id"], RootScopeKind(value["scope_kind"]),
            agent_id=value["agent_id"], domain_id=value["domain_id"],
        )
    except (TypeError, ValueError) as exc:
        raise RootBlocker5BindingRefused("root runtime scope key is invalid") from exc


def _lane_payload(lane: NativeRepresentationLane) -> dict[str, object]:
    return {name: getattr(lane, name) for name in lane.__dataclass_fields__}


def _lane_from_payload(value: object) -> NativeRepresentationLane:
    if not isinstance(value, dict):
        raise RootBlocker5BindingRefused("root envelope record representation lane is malformed")
    try:
        return NativeRepresentationLane(**value)
    except (TypeError, ValueError) as exc:
        raise RootBlocker5BindingRefused("root envelope record representation lane is invalid") from exc


def _profile_payload(profile: QualifiedDeploymentProfile) -> dict[str, object]:
    return {name: getattr(profile, name) for name in profile.__dataclass_fields__}


def _profile_digest_from_payload(value: object) -> str:
    if not isinstance(value, dict):
        raise RootBlocker5BindingRefused("root envelope record profile is malformed")
    try:
        return QualifiedDeploymentProfile(**value).digest
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise RootBlocker5BindingRefused("root envelope record profile is invalid") from exc


def _root_profile_record_payload(profile: RootProfileGenerationRef) -> dict[str, object]:
    if not isinstance(profile, RootProfileGenerationRef):
        raise RootBlocker5BindingRefused("root envelope record root profile is invalid")
    return {
        "core_id": str(profile.core_id),
        "profile_generation": profile.profile_generation,
        "profile_object_id": str(profile.profile_object_id),
        "profile_revision_id": str(profile.profile_revision_id),
        "profile_revision_ordinal": profile.profile_revision_ordinal,
        "profile_semantic_scope_id": str(profile.profile_semantic_scope_id),
    }


def root_profile_ref_from_record_payload(value: object) -> RootProfileGenerationRef:
    """Decode the full root-profile identity retained by immutable evidence."""

    required = {
        "core_id", "profile_generation", "profile_object_id", "profile_revision_id",
        "profile_revision_ordinal", "profile_semantic_scope_id",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise RootBlocker5BindingRefused("root envelope record root profile is malformed")
    try:
        return RootProfileGenerationRef(
            core_id=UUID(value["core_id"]),
            profile_generation=value["profile_generation"],
            profile_object_id=UUID(value["profile_object_id"]),
            profile_revision_id=UUID(value["profile_revision_id"]),
            profile_revision_ordinal=value["profile_revision_ordinal"],
            profile_semantic_scope_id=UUID(value["profile_semantic_scope_id"]),
        )
    except (TypeError, ValueError) as exc:
        raise RootBlocker5BindingRefused("root envelope record root profile is invalid") from exc


def _require_runtime_scope_plan_bindings(
    plans: tuple[MigrationRuntimeScopePlan, ...],
    scopes: tuple[NativeMemoryRuntimeScope, ...],
) -> None:
    ordered_plans = _ordered_runtime_scope_plans(plans)
    if not isinstance(scopes, tuple) or any(not isinstance(item, NativeMemoryRuntimeScope) for item in scopes):
        raise RootBlocker5BindingRefused("root runtime scopes must be typed")
    bindings = {
        _root_scope_key_from_plan(plan): (
            plan.legacy_source_namespace_id,
            plan.target_identity_namespace_id,
            plan.target_semantic_scope_id,
        )
        for plan in ordered_plans
    }
    observed: dict[RootScopeKey, tuple[UUID, UUID, UUID]] = {}
    for scope in scopes:
        try:
            key = (
                RootScopeKey(scope.workspace_id, RootScopeKind.PRIVATE, agent_id=scope.agent_id)
                if scope.scope_kind == "PRIVATE_AGENT"
                else RootScopeKey(scope.workspace_id, RootScopeKind.SHARED, domain_id=scope.domain_id)
            )
        except (TypeError, ValueError) as exc:
            raise RootBlocker5BindingRefused("root runtime scope does not map to a RootScopeKey") from exc
        if key in observed:
            raise RootBlocker5BindingRefused("root runtime scopes contain duplicate RootScopeKeys")
        observed[key] = (
            scope.legacy_source_namespace_id,
            scope.identity_namespace_id,
            scope.semantic_scope_id,
        )
    if bindings != observed:
        raise RootBlocker5BindingRefused("root runtime scope plans disagree with membership bindings")


def _require_runtime_scope_plan_description_parity(
    plans: tuple[MigrationRuntimeScopePlan, ...],
    description: RootNativeProductionAdmissionDescription,
) -> None:
    """Root membership may name exactly, and only, explicit runtime scopes."""

    _require_description(description)
    supplied = {_root_scope_key_from_plan(plan) for plan in _ordered_runtime_scope_plans(plans)}
    declared = set(_declared_scope_keys(description))
    if supplied != declared:
        raise RootBlocker5BindingRefused("ROOT_RUNTIME_SCOPE_PLAN_DECLARATION_MISMATCH")


def _declared_scope_keys(description: RootNativeProductionAdmissionDescription) -> tuple[RootScopeKey, ...]:
    return tuple(sorted(
        (
            scope.scope_key
            for workspace in description.workspace_plans
            for scope in workspace.runtime_scopes
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
    "RootAdmissionEnvelopeRecord",
    "RootBlocker5BindingRefused",
    "RootCompletionVerification",
    "RootDiscoveredCensus",
    "RootGeometryDispositionPlan",
    "RootGeometryDispositionPlanEntry",
    "RootWriterFreezeWitness",
    "SyntheticRootDispositionAdapter",
    "build_root_admission_envelope",
    "build_real_root_v2_admission_envelope",
    "declared_census_digest",
    "discover_canonical_root_layout",
    "execute_synthetic_root_disposition_plan",
    "frozen_root_geometry_disposition_plan",
    "normalization_closure_digest",
    "require_persisted_root_admission_envelope",
    "require_discovered_declared_census_parity",
    "root_membership_closure_digest",
    "root_admission_envelope_record_from_payload",
    "root_profile_ref_from_record_payload",
    "root_runtime_scope_plan_digest",
    "root_runtime_scope_plan_payloads",
    "verify_root_completion",
]
