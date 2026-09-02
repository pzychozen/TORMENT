"""B5-A3 active-native resource lifecycle qualification."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import logging
from pathlib import Path
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.connection import open_existing_native_core_connection, open_temporary_test_connection
from torment_service.substrate.deployment_core_maintenance import (
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    staging_legacy_witness,
)
from torment_service.substrate.deployment_selector import (
    activate_selector_native,
    begin_cutover_pending,
    establish_selector_era,
    initialize_selector,
    resolve_deployment_agreement,
)
from torment_service.substrate.deployment_types import (
    AdmissionCompletionWitness,
    DeploymentResolutionMode,
    QualifiedDeploymentProfile,
)
from torment_service.substrate.fabric_native_routing import NativeFabricRouteRequest, NativeFabricRoutingScope
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.migration.existing_workspace_multi_scope_admission import ExistingWorkspaceNativeLanePlan
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativePostWriteRouteWitness,
    NativeSharedTriggerMoodDriftBinding,
)
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwner,
    NativeProductionResourceOwnerError,
)
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


class _Embedder:
    provider = "b5-a3"
    model = "deterministic-3"
    dim = 3

    def embed(self, _text: str) -> np.ndarray:
        return np.asarray((1.0, 0.0, 0.0), dtype=np.float32)


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        "b5-a3", "deterministic-3", 3,
        "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32",
    )


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _profile(scope_digest: str, **overrides: object) -> QualifiedDeploymentProfile:
    values: dict[str, object] = {
        "compression_enabled": False,
        "deep_memory_enabled": False,
        "representation_provider": "b5-a3",
        "representation_model": "deterministic-3",
        "representation_dimension": 3,
        "admitted_scope_plan_digest": scope_digest,
        "external_owner_digest": hashlib.sha256(b"external-owners-remain-external").hexdigest(),
    }
    values.update(overrides)
    return QualifiedDeploymentProfile(**values)  # type: ignore[arg-type]


def _plan(tmp_path: Path, *, kind: str, qualifier: str) -> ExistingWorkspaceNativeLanePlan:
    return ExistingWorkspaceNativeLanePlan(
        workspace_id="orchard",
        scope_kind=kind,
        legacy_graph_source_path=tmp_path / "legacy" / kind / qualifier,
        legacy_source_namespace_id=_id(),
        legacy_source_namespace_key=f"orchard:{kind}:{qualifier}",
        target_identity_namespace_id=_id(),
        target_semantic_scope_id=_id(),
        motif_alias_namespace_id=_id(),
        motif_identity_namespace_id=_id(),
        membership_identity_namespace_id=_id(),
        idempotency_namespace_id=_id(),
        motif_domain_id="personal" if kind == "PRIVATE_AGENT" else qualifier,
        representation_lane=_lane(),
        agent_id=qualifier if kind == "PRIVATE_AGENT" else None,
        domain_id=qualifier if kind == "SHARED_DOMAIN" else None,
    )


def _insert_scope_rows(connection, plan: ExistingWorkspaceNativeLanePlan) -> NativeFabricRoutingScope:
    for identifier, label in (
        (plan.target_identity_namespace_id, "memory"),
        (plan.motif_identity_namespace_id, "motif"),
        (plan.membership_identity_namespace_id, "membership"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(identifier), f"{plan.qualifier}:{label}"),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(plan.target_semantic_scope_id), f"{plan.qualifier}:semantic"),
    )
    for identifier, label in (
        (plan.legacy_source_namespace_id, "memory-source"),
        (plan.motif_alias_namespace_id, "motif-alias"),
    ):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(identifier), f"{plan.qualifier}:{label}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(plan.idempotency_namespace_id), f"{plan.qualifier}:operations"),
    )
    runtime = NativeMemoryRuntimeScope(
        plan.workspace_id,
        plan.scope_kind,
        plan.legacy_source_namespace_id,
        plan.target_identity_namespace_id,
        plan.target_semantic_scope_id,
        plan.agent_id,
        plan.domain_id,
    )
    return NativeFabricRoutingScope(
        runtime,
        plan.motif_alias_namespace_id,
        plan.motif_identity_namespace_id,
        plan.membership_identity_namespace_id,
        plan.idempotency_namespace_id,
    )


def _active_fixture(tmp_path: Path, *, activate: bool = True):
    root = tmp_path / "production-root"
    core_root = root / "substrate" / "cores"
    core_root.mkdir(parents=True)
    core_name = "active.db"
    core_path = core_root / core_name
    plans = (
        _plan(tmp_path, kind="PRIVATE_AGENT", qualifier="aria"),
        _plan(tmp_path, kind="SHARED_DOMAIN", qualifier="archive"),
        _plan(tmp_path, kind="SHARED_DOMAIN", qualifier="research"),
    )
    qualified = open_temporary_test_connection(core_path)
    try:
        metadata = create_schema(qualified.connection)
        for plan in plans:
            _insert_scope_rows(qualified.connection, plan)
        core_id = native_id_from_bytes(metadata.core_id)
    finally:
        qualified.close()

    lane_plans = [plan.payload() for plan in plans]
    descriptor_payload = {
        "descriptor_schema": "TORMENT_EXISTING_WORKSPACE_NATIVE_MULTI_SCOPE_ADMISSION",
        "descriptor_version": 1,
        "profile": "EXISTING_WORKSPACE_MULTI_SCOPE_CORE",
        "admission_state": "ADMISSION_COMPLETE",
        "workspace_id": "orchard",
        "native_core_id": str(core_id),
        "representation_lane": {name: getattr(_lane(), name) for name in _lane().__dataclass_fields__},
        "lane_plan_digest": _digest(lane_plans),
        "declared_lane_count": len(plans),
        "lanes": [{"plan": plan.payload()} for plan in plans],
    }
    descriptor_digest = _digest(descriptor_payload)
    descriptor_path = root / "active-admission.json"
    descriptor_path.write_text(
        _canonical({"descriptor_digest": descriptor_digest, "payload": descriptor_payload}) + "\n",
        encoding="utf-8",
    )
    profile = _profile(descriptor_payload["lane_plan_digest"])
    establish_selector_era(data_root=root)
    initial = initialize_selector(data_root=root, operation_key="initialize")
    selected = begin_cutover_pending(
        data_root=root,
        core_relative_path=core_name,
        descriptor_digest=descriptor_digest,
        profile=profile,
        expected_generation=initial.generation,
        operation_key="select-pending",
    )
    inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=core_name)
    pending = enter_cutover_pending(
        data_root=root,
        core_relative_path=core_name,
        expected_witness=staging_legacy_witness(
            inspection,
            descriptor_digest=selected.descriptor_digest or "",
            profile_digest=selected.profile_digest or "",
        ),
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest or "",
        operation_key="core-pending",
    )
    if not activate:
        agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
        assert agreement.mode is DeploymentResolutionMode.MAINTENANCE_ONLY
        return root, core_path, descriptor_path, profile, agreement
    active = activate_core(
        data_root=root,
        core_relative_path=core_name,
        expected_witness=pending.witness,
        selector_generation=selected.generation,
        selector_witness_digest=selected.core_witness_digest or "",
        operation_key="core-active",
        completion_witness=AdmissionCompletionWitness(
            admission_identity_digest=descriptor_digest,
            completed_descriptor_digest=descriptor_digest,
            completed_progress_digest=_digest("b5-a3-completed-progress"),
            native_core_id=core_id,
            workspace_id="orchard",
            whole_workspace_closure_digest=_digest("b5-a3-whole-workspace-closure"),
            profile_digest=profile.digest,
        ),
    )
    activate_selector_native(
        data_root=root,
        core_relative_path=core_name,
        core_result=active,
        expected_generation=selected.generation,
        operation_key="selector-active",
    )
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    assert agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    return root, core_path, descriptor_path, profile, agreement


def _request(
    key: str,
    *,
    scope: str = "private",
    domain_id: str = "personal",
    vector: tuple[float, float, float] = (1., 0., 0.),
    step: int = 12,
) -> NativeFabricRouteRequest:
    return NativeFabricRouteRequest(
        workspace_id="orchard",
        scope=scope,
        agent_id="aria",
        domain_id=domain_id,
        native_operation_key=key,
        embedder_lane=_lane(),
        summary=f"production native {key}",
        memory_type="reflection",
        memory_class="core",
        strength=.8,
        confidence=.9,
        half_life_days=0,
        logical_step=step,
        created_ts=step,
        last_active_ts=step,
        last_reinforced_ts=step,
        incoming_embedding=np.asarray(vector, dtype=np.float32),
        provenance=ProvenanceV1.for_user_ingest(step=12),
        governance=MemoryGovernanceFlags(),
        flexible_payload={"production_b5_a3": True},
    )


def _owner(tmp_path: Path):
    root, core_path, descriptor_path, profile, agreement = _active_fixture(tmp_path)
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=root,
        effective_profile=profile,
        agreement=agreement,
        admission_descriptor_path=descriptor_path,
    )
    return owner, root, core_path, descriptor_path, profile, agreement


def test_owner_requires_exact_native_agreement_and_refuses_deep_profiles(tmp_path: Path):
    root, _core, descriptor, profile, agreement = _active_fixture(tmp_path)
    legacy_root = tmp_path / "legacy-root"
    legacy_root.mkdir()
    legacy = resolve_deployment_agreement(data_root=legacy_root, effective_profile=profile)
    assert legacy.mode is DeploymentResolutionMode.LEGACY_PUBLIC
    with pytest.raises(NativeProductionResourceOwnerError, match="NATIVE_AGREEMENT"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=legacy_root, effective_profile=profile, agreement=legacy,
            admission_descriptor_path=descriptor,
        )

    pending_root, _pending_core, pending_descriptor, pending_profile, pending = _active_fixture(
        tmp_path / "maintenance", activate=False,
    )
    assert pending.mode is DeploymentResolutionMode.MAINTENANCE_ONLY
    with pytest.raises(NativeProductionResourceOwnerError):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=pending_root, effective_profile=pending_profile, agreement=pending,
            admission_descriptor_path=pending_descriptor,
        )

    with pytest.raises(NativeProductionResourceOwnerError):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root,
            effective_profile=replace(profile, deep_memory_enabled=True),
            agreement=agreement,
            admission_descriptor_path=descriptor,
        )
    refused = resolve_deployment_agreement(
        data_root=root,
        effective_profile=replace(profile, representation_model="drifted-model"),
    )
    assert refused.mode is DeploymentResolutionMode.REFUSED
    with pytest.raises(NativeProductionResourceOwnerError):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root,
            effective_profile=replace(profile, representation_model="drifted-model"),
            agreement=refused,
            admission_descriptor_path=descriptor,
        )


def test_owner_refuses_profile_or_runtime_drift_before_context_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    from torment_service.substrate import production_native_owner as owner_module

    owner, root, _core, descriptor, profile, agreement = _owner(tmp_path)
    try:
        owner._effective_profile = replace(profile, representation_model="drifted-model")
        with pytest.raises(NativeProductionResourceOwnerError):
            owner.open_write_context()
    finally:
        owner.close()

    original_qualify = owner_module.qualify_runtime
    monkeypatch.setattr(
        owner_module,
        "qualify_runtime",
        lambda: replace(original_qualify(), sqlite_runtime_version="3.51.2", runtime_admissible=False),
    )
    with pytest.raises(NativeProductionResourceOwnerError, match="runtime"):
        NativeProductionResourceOwner.from_native_agreement(
            data_root=root,
            effective_profile=profile,
            agreement=agreement,
            admission_descriptor_path=descriptor,
        )


def test_active_owner_request_scopes_write_then_fresh_query_srg_and_restart(tmp_path: Path):
    owner, root, core_path, descriptor, profile, agreement = _owner(tmp_path)
    try:
        assert not any(hasattr(value, "execute") for value in vars(owner).values())
        with owner.open_write_context() as write:
            attempt = write.route(_request("first-private"))
        assert attempt.result is not None and attempt.result.stored is True

        with owner.open_query_context(embedder=_Embedder()) as query:
            hits = query.private_lane("orchard", "aria").search("find", top_k=3)
            assert len(hits) == 1
            hit = hits[0]
            query.replace_srg_state(hit, {"phase": "process-overlay"})
            assert query.effective_srg_state(hit) == {"phase": "process-overlay"}
            lane = query.private_lane("orchard", "aria")
            first_connection = lane._runtime._connection  # request-owned diagnostic only
        with pytest.raises(NativeProductionResourceOwnerError, match="closed"):
            query.domain_ids()

        with owner.open_query_context(embedder=_Embedder()) as next_query:
            fresh_hits = next_query.private_lane("orchard", "aria").search("find", top_k=3)
            assert [item.memory_identity.eid for item in fresh_hits] == [0]
            assert next_query.effective_srg_state(fresh_hits[0]) == {"phase": "process-overlay"}
            second_connection = next_query.private_lane("orchard", "aria")._runtime._connection
            assert second_connection is not first_connection

        with open_existing_native_core_connection(core_path) as opened:
            revision_before_restart = opened.connection.execute(
                "SELECT current_revision_ordinal FROM objects"
            ).fetchall()
        owner.close()
        owner.close()
        with pytest.raises(NativeProductionResourceOwnerError, match="closed"):
            owner.open_query_context(embedder=_Embedder())

        restarted = NativeProductionResourceOwner.from_native_agreement(
            data_root=root, effective_profile=profile,
            agreement=resolve_deployment_agreement(data_root=root, effective_profile=profile),
            admission_descriptor_path=descriptor,
        )
        try:
            with restarted.open_query_context(embedder=_Embedder()) as query:
                hits = query.private_lane("orchard", "aria").search("find")
                assert len(hits) == 1
                assert query.effective_srg_state(hits[0]) != {"phase": "process-overlay"}
            with open_existing_native_core_connection(core_path) as opened:
                assert opened.connection.execute(
                    "SELECT current_revision_ordinal FROM objects"
                ).fetchall() == revision_before_restart
        finally:
            restarted.close()
    finally:
        owner.close()


def test_stale_or_missing_active_authority_refuses_before_next_context(tmp_path: Path):
    owner, _root, core_path, _descriptor, _profile_value, _agreement = _owner(tmp_path)
    try:
        moved = core_path.with_name("removed-active.db")
        core_path.rename(moved)
        with pytest.raises(NativeProductionResourceOwnerError):
            owner.open_query_context(embedder=_Embedder())
    finally:
        owner.close()


def test_context_thread_discipline_and_staging_guard_are_preserved(tmp_path: Path):
    owner, _root, core_path, _descriptor, _profile_value, _agreement = _owner(tmp_path)
    try:
        context = owner.open_query_context(embedder=_Embedder())
        lane = context.private_lane("orchard", "aria")
        assert lane.search("same-thread") == ()
        failures: list[Exception] = []

        def cross_thread() -> None:
            try:
                lane.search("cross-thread")
            except Exception as exc:  # exact owner error matters below
                failures.append(exc)

        worker = threading.Thread(target=cross_thread)
        worker.start(); worker.join()
        assert len(failures) == 1
        assert "thread" in str(failures[0]).lower()
        context.close()

        with open_existing_native_core_connection(core_path) as opened:
            with pytest.raises(Exception, match="only STAGING"):
                prepare_native_memory_runtime_binding(
                    connection=opened.connection,
                    core_database_path=core_path,
                    expected_core_id=owner.authority_facts.core_id,
                    scope_bindings=(),
                    representation_lane=_lane(),
                )
    finally:
        owner.close()


def test_active_post_write_context_reuses_existing_adapter_without_owner_absorption(tmp_path: Path):
    owner, _root, _core, _descriptor, _profile_value, _agreement = _owner(tmp_path)
    try:
        recovered = owner._recover_active_runtime()
        scope = recovered.lookup_private("aria").fabric_routing_scope
        runtime_scope = scope.runtime_scope
        template = NativeDerivedMemoryRuntimeConfiguration(
            workspace_id=runtime_scope.workspace_id,
            agent_id=runtime_scope.agent_id or "",
            domain_id="personal",
            legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            motif_alias_namespace_id=scope.motif_alias_namespace_id,
            memory_identity_namespace_id=runtime_scope.identity_namespace_id,
            semantic_scope_id=runtime_scope.semantic_scope_id,
            idempotency_namespace_id=scope.idempotency_namespace_id,
            parent_native_operation_key="b5-a3-post-write",
            expected_dimension=3,
            embed=lambda _text: np.asarray((1., 0., 0.), dtype=np.float32),
            embedder_provider="b5-a3",
            embedder_model="deterministic-3",
            side_store=SimpleNamespace(),
        )
        external = NativePostWriteExternalDependencies(
            owner=SimpleNamespace(),
            workspace=SimpleNamespace(),
            identity=SimpleNamespace(),
            agent_key="aria",
            detect_canon_conflict=lambda *_args: (False, 0.0, ""),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=logging.getLogger("b5-a3.post-write"),
        )
        configuration = NativePostWriteQualificationConfiguration(
            routing_scope=scope,
            profile=NativePostWriteQualificationProfile.core_staging(),
            external=external,
            derived_runtime_template=template,
            motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False,
            checkpoint_snapshots_required=False,
            bridge_suggestions_required=False,
            deep_memory_required=False,
        )
        with owner.open_post_write_context(configuration=configuration):
            assert external.character_store is None
        assert owner._character_store is None
    finally:
        owner.close()


def test_active_shared_post_write_exposes_private_mood_in_a_fresh_query_context(tmp_path: Path):
    class _SideStore:
        def __init__(self) -> None:
            self.anchor = {"motifs": {}}
            self.affect = {"last_tag": "sad", "last_conf": .7, "last_step": 1, "drift_hist": []}

        def load_anchor_state(self, **_kwargs):
            return dict(self.anchor)

        def save_anchor_state(self, *, state, **_kwargs):
            self.anchor = dict(state)

        def load_affect_state(self, **_kwargs):
            return dict(self.affect)

        def save_affect_state(self, *, state, **_kwargs):
            self.affect = dict(state)

    owner, _root, _core, _descriptor, _profile_value, _agreement = _owner(tmp_path)
    try:
        recovered = owner._recover_active_runtime()
        private = recovered.lookup_private("aria").fabric_routing_scope
        shared = recovered.lookup_shared("research").fabric_routing_scope
        side = _SideStore()
        template = NativeDerivedMemoryRuntimeConfiguration(
            workspace_id="orchard",
            agent_id="aria",
            domain_id="research",
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            memory_identity_namespace_id=private.runtime_scope.identity_namespace_id,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
            idempotency_namespace_id=private.idempotency_namespace_id,
            parent_native_operation_key="b5-a3:shared-mood",
            expected_dimension=3,
            embed=lambda _text: np.asarray((2., .6, 0.), dtype=np.float32),
            embedder_provider="b5-a3",
            embedder_model="deterministic-3",
            side_store=side,
            now_ts=lambda: 777,
        )
        configuration = NativePostWriteQualificationConfiguration(
            routing_scope=shared,
            profile=NativePostWriteQualificationProfile.core_staging_with_shared_m1_mood_drift(),
            external=NativePostWriteExternalDependencies(
                owner=SimpleNamespace(_log=logging.getLogger("b5-a3.shared")),
                workspace=SimpleNamespace(
                    data_dir=str(tmp_path / "workflow"),
                    domain_policies={"research": {
                        "motif_entropy_target_n": 2,
                        "motif_entropy_high": 0.0,
                        "motif_merge_similarity": .93,
                        "motif_merge_max_suggestions": 20,
                        "auto_merge_motifs": False,
                        "auto_merge_entropy_trigger": .8,
                    }},
                ),
                identity=SimpleNamespace(seed={}),
                agent_key="aria",
                detect_canon_conflict=lambda *_args: (False, 0.0, ""),
                proposal_allowed=lambda *_args, **_kwargs: False,
                hivemind_log=logging.getLogger("b5-a3.shared.hivemind"),
            ),
            derived_runtime_template=None,
            motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False,
            checkpoint_snapshots_required=False,
            bridge_suggestions_required=False,
            deep_memory_required=False,
            shared_motif_suggestion_maintenance_required=True,
            shared_mood_drift_binding=NativeSharedTriggerMoodDriftBinding(private, template),
        )
        with owner.open_write_context() as write:
            seed = write.route(_request("shared-seed", scope="shared", domain_id="research", vector=(1., 0., 0.), step=1)).result
            result = write.route(_request("shared-current", scope="shared", domain_id="research", vector=(0., 1., 0.), step=200)).result
        assert seed is not None and result is not None and result.reinforced is False
        post_context = FabricPostWriteContext.make(
            workspace_id="orchard", agent_id="aria", scope="shared", chosen_domain="research",
            step=200, storage_outcome=PostWriteStorageOutcome.CREATED_NEW, stored=True, eid=result.eid,
            created_motif=result.motifs[0], motif_ids=result.motifs, half_life_days=0,
            summary="production native shared-current", embedding=np.asarray((0., 1., 0.), dtype=np.float32),
            memory_class="core", memory_type="reflection", strength=.8, confidence=.9,
            promotion_score=.0, stability_delta=.0, tri_mod={}, debug={}, srg_state=None,
            phase_durations={}, state_symbol=None, affect_tag="angry", affect_conf=.8,
            skip_packet_emission=True,
        )
        with owner.open_post_write_context(configuration=configuration) as post_write:
            assert post_write.run(
                post_context,
                route_witness=NativePostWriteRouteWitness(result, "shared-current"),
            ).proposal_id is None

        with owner.open_query_context(embedder=_Embedder()) as query:
            assert len(query.shared_lane("orchard", "research").search("q", top_k=8)) == 2
            private_hits = query.private_lane("orchard", "aria").search("q", top_k=8)
            assert len(private_hits) == 1
            assert private_hits[0].compatibility_hit["type"] == "mood_drift"
            assert query.shared_lane("orchard", "archive").search("q", top_k=8) == ()
        assert side.affect["drift_hist"] == [{"from": "sad", "to": "angry", "step": 200, "conf": .8}]
    finally:
        owner.close()


def test_public_entrypoints_do_not_construct_the_private_owner():
    repository = Path(__file__).resolve().parents[1]
    for path in (
        repository / "torment_service" / "app.py",
        repository / "torment_service" / "mcp_server.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert "production_native_owner" not in source
        assert "NativeProductionResourceOwner" not in source
