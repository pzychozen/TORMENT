"""Experiment-local L0 snapshot packaging and N0 B-series orchestration."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import shutil
import sqlite3
from typing import Any
from uuid import UUID

from torment_service.substrate.ids import native_id_from_bytes
from torment_service.substrate.migration import (
    LegacyVectorStrategy,
    MigrationRehearsalConfig,
    MigrationRuntimeMotifProjectionRequest,
    MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeRepresentationBootstrapRequest,
    MigrationRuntimeScopePlan,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeMotifProjectionService,
    NativeMigrationRuntimeNormalizationService,
    NativeMigrationRuntimeReadinessPreflight,
    NativeMigrationRuntimeRepresentationBootstrapService,
    NativeWorkspaceRuntimeReadiness,
    ObjectRuntimeReadiness,
    WorkspaceNativeRuntimeReadinessReport,
    WorkspaceNativeRuntimeReadinessRequest,
    create_snapshot_manifest,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import open_schema

from .manifest import LegacyBaselineFingerprint, verify_legacy_baseline
from .protocol import D1ProtocolError


class N0BaselineRefused(D1ProtocolError):
    """A D1 input requires a migration capability outside the frozen protocol."""


def require_d1_motif_alias_separation(
    plans: tuple[MigrationRuntimeScopePlan, ...],
) -> None:
    """Reject a harness topology that would collapse source and runtime motifs."""
    if any(
        plan.motif_alias_namespace_id == plan.legacy_source_namespace_id
        for plan in plans
    ):
        raise N0BaselineRefused("D1_N0_MOTIF_ALIAS_NAMESPACE_COLLAPSED")


def materialize_l0_snapshot(
    *, baseline: LegacyBaselineFingerprint, destination: str | Path,
) -> Path:
    """Copy the exact L0 evidence shape expected by existing 7F/B readers.

    This is packaging only: no JSON is rewritten, no embedding is recomputed,
    and no source byte is modified.  The destination must be new and is the
    immutable snapshot consumed by the existing migration services.
    """
    verify_legacy_baseline(baseline)
    source = Path(baseline.root).resolve()
    target = Path(destination).resolve()
    if target.exists():
        raise N0BaselineRefused("D1 L0 snapshot destination must not already exist")
    if source == target or source in target.parents:
        raise N0BaselineRefused("D1 snapshot destination must be outside the legacy L0 root")
    workspace = Path("workspaces") / baseline.workspace_id
    private = workspace / "agents" / baseline.agent_id / "private"
    required = [
        private / "nodes.jsonl",
        workspace / "workspace_meta.json",
        workspace / "agents" / baseline.agent_id / "identity.json",
        workspace / "domains" / "research" / "motifs.json",
    ]
    if baseline.character_seed is not None and baseline.character_state is not None:
        required.extend((
            workspace / "agents" / baseline.agent_id / "character_state.json",
            workspace / "seeds" / str(baseline.character_seed.value["seed_id"]) / "seed.json",
        ))
    optional_private_records = (private / "edges.jsonl", private / "memory_events.jsonl")
    try:
        for relative in required:
            source_path = source / relative
            if not source_path.is_file():
                raise N0BaselineRefused(f"required L0 evidence is missing: {relative.as_posix()}")
            destination_path = target / (relative.relative_to(private) if str(relative).startswith(str(private)) else relative)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
        for relative in optional_private_records:
            source_path = source / relative
            if source_path.is_file():
                destination_path = target / relative.relative_to(private)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination_path)
        source_embeddings = source / private / "embeddings"
        if not source_embeddings.is_dir():
            raise N0BaselineRefused("L0 has no private embedding evidence directory")
        shutil.copytree(source_embeddings, target / "embeddings")
    except Exception:
        if target.exists():
            shutil.rmtree(target)
        raise
    return target


@dataclass(frozen=True)
class N0BuildPlan:
    baseline: LegacyBaselineFingerprint
    snapshot_root: str | Path
    manifest_path: str | Path
    legacy_source_namespace_id: UUID
    legacy_source_namespace_key: str
    migration_config: MigrationRehearsalConfig
    scope_plans: tuple[MigrationRuntimeScopePlan, ...]
    target_lane: NativeRepresentationLane
    readiness_request: WorkspaceNativeRuntimeReadinessRequest


@dataclass(frozen=True)
class N0BuildResult:
    legacy_snapshot_id: UUID
    rehearsal: Any
    normalized_eids: tuple[int, ...]
    b3a_eids: tuple[int, ...]
    b4a_motif_ids: tuple[str, ...]
    readiness: WorkspaceNativeRuntimeReadinessReport


class N0BaselineBuilder:
    """Coordinates existing 7F/B services; it owns no admission semantics."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("N0 requires an already-open STAGING SQLite connection")
        self._connection = connection

    def build(self, plan: N0BuildPlan) -> N0BuildResult:
        verify_legacy_baseline(plan.baseline)
        snapshot_root = Path(plan.snapshot_root).resolve()
        manifest_path = Path(plan.manifest_path).resolve()
        if snapshot_root == Path(plan.baseline.root).resolve():
            raise N0BaselineRefused("N0 must consume a separately materialized immutable L0 snapshot")
        metadata = open_schema(self._connection, writable=False)
        core_id = native_id_from_bytes(metadata.core_id)
        if core_id != plan.migration_config.native_core_id:
            raise N0BaselineRefused("N0 migration config does not name the supplied STAGING core")
        if plan.readiness_request.expected_native_core_id != core_id:
            raise N0BaselineRefused("B5 request does not name the supplied STAGING core")
        if plan.readiness_request.target_lane != plan.target_lane or plan.readiness_request.scope_plans != plan.scope_plans:
            raise N0BaselineRefused("B5 request does not match the frozen D1 scope/lane plan")
        require_d1_motif_alias_separation(plan.scope_plans)
        manifest = create_snapshot_manifest(
            snapshot_root=snapshot_root,
            manifest_path=manifest_path,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            legacy_source_namespace_key=plan.legacy_source_namespace_key,
            capture_label="7G5D1 L0 frozen baseline",
        )
        rehearsal = NativeLegacyMigrationRehearsal(self._connection).run(
            snapshot_root=snapshot_root, manifest_path=manifest_path, config=plan.migration_config,
        )
        first = self._readiness(manifest.legacy_snapshot_id, core_id, plan)
        normalized: dict[int, Any] = {}
        for item in first.object_items:
            if item.readiness is ObjectRuntimeReadiness.EVIDENCE_ONLY_NOT_RUNTIME_OBJECT:
                continue
            if item.readiness is not ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED or item.eid is None:
                raise N0BaselineRefused(f"D1 baseline memory is not normalizable as-is: {item.reason_codes}")
            normalized[item.eid] = NativeMigrationRuntimeNormalizationService(self._connection).normalize_legacy_core_memory(
                MigrationRuntimeNormalizationRequest(
                    snapshot_root, manifest_path, manifest.legacy_snapshot_id,
                    plan.legacy_source_namespace_id, core_id, item.eid, item.current_revision_id,
                    plan.scope_plans, plan.migration_config.idempotency_namespace_id,
                    f"D1:N0:B2:{item.eid}",
                )
            )
        after_b2 = self._readiness(manifest.legacy_snapshot_id, core_id, plan)
        b3a_eids: list[int] = []
        for item in after_b2.object_items:
            if item.eid is None or item.eid not in normalized:
                continue
            if item.legacy_vector_strategy is not LegacyVectorStrategy.BYTE_DERIVATION_POSSIBLE:
                raise N0BaselineRefused("D1 baseline requires B3A captured-vector evidence; B3B is not admitted")
            NativeMigrationRuntimeRepresentationBootstrapService(self._connection).bootstrap_from_legacy_capture(
                MigrationRuntimeRepresentationBootstrapRequest(
                    snapshot_root, manifest_path, manifest.legacy_snapshot_id,
                    plan.legacy_source_namespace_id, core_id, item.eid,
                    normalized[item.eid].predecessor_revision_id, normalized[item.eid].revision_id,
                    plan.target_lane, plan.migration_config.idempotency_namespace_id,
                    f"D1:N0:B3A:{item.eid}",
                )
            )
            b3a_eids.append(item.eid)
        after_b3a = self._readiness(manifest.legacy_snapshot_id, core_id, plan)
        b4a_ids: list[str] = []
        projector = NativeMigrationRuntimeMotifProjectionService(self._connection)
        for item in after_b3a.motif_items:
            if item.runtime_motif_id is None:
                raise N0BaselineRefused("D1 baseline has an unresolved legacy runtime motif ID")
            projector.project_lane_preserving_legacy_motif(MigrationRuntimeMotifProjectionRequest(
                snapshot_root, manifest_path, manifest.legacy_snapshot_id,
                plan.legacy_source_namespace_id, core_id, item.runtime_motif_id,
                item.motif_object_id, item.current_revision_id, plan.scope_plans,
                plan.target_lane, plan.migration_config.idempotency_namespace_id,
                f"D1:N0:B4A:{item.runtime_motif_id}",
            ))
            b4a_ids.append(item.runtime_motif_id)
        # The concrete snapshot ID is allocated only when the new immutable
        # manifest is written above.  B5 must observe that same snapshot, never
        # an operator placeholder supplied before capture.
        readiness = NativeWorkspaceRuntimeReadiness(self._connection).run(
            replace(plan.readiness_request, legacy_snapshot_id=manifest.legacy_snapshot_id)
        )
        validate_n0_readiness(readiness)
        return N0BuildResult(
            manifest.legacy_snapshot_id, rehearsal, tuple(sorted(normalized)), tuple(sorted(b3a_eids)),
            tuple(sorted(b4a_ids)), readiness,
        )

    def _readiness(self, snapshot_id: UUID, core_id: UUID, plan: N0BuildPlan) -> Any:
        return NativeMigrationRuntimeReadinessPreflight(self._connection).run(
            MigrationRuntimeReadinessRequest(snapshot_id, core_id, plan.scope_plans, plan.target_lane)
        )


def validate_n0_readiness(readiness: WorkspaceNativeRuntimeReadinessReport) -> None:
    """Reject a baseline that is not B4A-only, fully closed STAGING evidence."""
    if not (readiness.memory_closure_ready and readiness.motif_closure_ready and readiness.member_reference_closure_ready):
        raise N0BaselineRefused("D1 N0 did not establish whole-workspace closure")
    if not (readiness.core_staging_runtime_ready and readiness.controlled_native_staging_experiment_ready):
        raise N0BaselineRefused("D1 N0 did not establish controlled STAGING readiness")
    if readiness.b4a_ready_motif_count < 1:
        raise N0BaselineRefused("D1 requires at least one B4A-projected motif baseline")
    if readiness.b4b_ready_motif_count != 0:
        raise N0BaselineRefused("D1 baseline unexpectedly requires B4B regeometry")
