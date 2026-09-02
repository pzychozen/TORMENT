"""B5-A4R2 direct native public-ingest recovery envelope evidence."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest

from torment_service.fabric import TormentFabric
from torment_service.ingest_orchestration import (
    deserialize_prepared_fabric_ingest,
    serialize_prepared_fabric_ingest,
)
from torment_service.post_write_runtime import LegacyFabricPostWriteAdapter
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativeSharedTriggerMoodDriftBinding,
)
from torment_service.substrate.native_public_ingest_executor import (
    NativePublicIngestExecutor,
    NativePublicIngestInterruption,
    NativePublicIngestRequest,
)
from torment_service.substrate.native_public_mutation_receipts import (
    NativePublicMutationReceiptStore,
    PublicMutationIdempotencyConflict,
    PublicMutationRecoveryRequired,
    PublicMutationRecoveryState,
)
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.production_native_owner import NativeProductionResourceOwner

# Reuse B5-A3's real active core/admission fixture.  It creates an ACTIVE core
# with the admitted private ``aria`` scope and actual SQLite operation ledger.
from test_b5_a3_production_native_resource_owner import _Embedder, _active_fixture


class _SideStore:
    def __init__(self) -> None:
        self.anchor = {"motifs": {}}
        self.affect = {"last_tag": "", "last_conf": 0.0, "last_step": 0, "drift_hist": []}

    def load_anchor_state(self, **_kwargs):
        return dict(self.anchor)

    def save_anchor_state(self, *, state, **_kwargs):
        self.anchor = dict(state)

    def load_affect_state(self, **_kwargs):
        return dict(self.affect)

    def save_affect_state(self, *, state, **_kwargs):
        self.affect = dict(state)


def _executor(tmp_path: Path):
    root, _core, descriptor, profile, agreement = _active_fixture(tmp_path)
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=root, effective_profile=profile, agreement=agreement,
        admission_descriptor_path=descriptor,
    )
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric"))
    fabric.kernel.embedder = _Embedder()
    workspace = fabric.get_workspace("orchard", domains=["personal", "research", "archive"])
    # This recovery fixture exercises the existing core native post-write
    # profile.  Motif auto-merge is a separately-qualified maintenance
    # mutation, so keep its policy inactive rather than widening this slice.
    workspace.domain_policies["personal"]["auto_merge_motifs"] = False
    identity = fabric.create_agent("orchard", "aria")
    side_store = _SideStore()
    owner_ref = [owner]

    def configuration(prepared):
        runtime = owner_ref[0]._recover_active_runtime()
        private = runtime.lookup_private("aria").fabric_routing_scope
        scope = (
            private if prepared.scope == "private"
            else runtime.lookup_shared(prepared.domain_id).fabric_routing_scope
        )
        runtime_scope = private.runtime_scope
        template = NativeDerivedMemoryRuntimeConfiguration(
            workspace_id="orchard", agent_id="aria", domain_id=prepared.domain_id,
            legacy_source_namespace_id=runtime_scope.legacy_source_namespace_id,
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            memory_identity_namespace_id=runtime_scope.identity_namespace_id,
            semantic_scope_id=runtime_scope.semantic_scope_id,
            idempotency_namespace_id=private.idempotency_namespace_id,
            parent_native_operation_key="b5-a4r2-template",
            expected_dimension=3, embed=fabric.kernel.embedder.embed,
            embedder_provider="b5-a3", embedder_model="deterministic-3",
            side_store=side_store,
        )
        if prepared.scope == "shared":
            return NativePostWriteQualificationConfiguration(
                routing_scope=scope,
                profile=NativePostWriteQualificationProfile.core_staging_with_shared_m1_mood_drift(),
                external=NativePostWriteExternalDependencies(
                    owner=fabric, workspace=workspace, identity=identity,
                    agent_key=fabric._agent_key("orchard", "aria"),
                    detect_canon_conflict=lambda incoming, existing, score: (False, 0.0, ""),
                    proposal_allowed=lambda *_args, **_kwargs: False,
                    hivemind_log=logging.getLogger("b5.a4r2.shared"),
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
        return NativePostWriteQualificationConfiguration(
            routing_scope=scope, profile=NativePostWriteQualificationProfile.core_staging(),
            external=NativePostWriteExternalDependencies(
                owner=fabric, workspace=workspace, identity=identity,
                agent_key=fabric._agent_key("orchard", "aria"),
                detect_canon_conflict=lambda incoming, existing, score: (False, 0.0, ""),
                proposal_allowed=lambda *_args, **_kwargs: False,
                hivemind_log=logging.getLogger("b5.a4r2"),
            ),
            derived_runtime_template=template,
            motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False,
            checkpoint_snapshots_required=False,
            bridge_suggestions_required=False,
            deep_memory_required=False,
        )

    executor = NativePublicIngestExecutor(owner=owner, fabric=fabric, post_write_configuration=configuration)
    # Test-only holder: a recreated executor can use the same external Fabric
    # objects while its configuration resolves against its newly reopened
    # native owner rather than stale process-local capability state.
    executor._test_owner_ref = owner_ref  # type: ignore[attr-defined]
    executor._test_post_write_configuration = configuration  # type: ignore[attr-defined]
    return executor, owner, fabric


def _request(key: str = "r2-retry-key", **overrides) -> NativePublicIngestRequest:
    values = {
        "workspace_id": "orchard", "agent_id": "aria", "text": "native public recovery",
        "public_mutation_key": key, "step": 7,
        "supplied_embedding": [1.0, 0.0, 0.0], "scope": "private",
    }
    values.update(overrides)
    return NativePublicIngestRequest(**values)


def _native_operation_count(owner: NativeProductionResourceOwner, prefix: str) -> int:
    with open_existing_native_core_connection(owner.authority_facts.core_database_path) as opened:
        return int(opened.connection.execute(
            "SELECT count(*) FROM operations WHERE idempotency_key LIKE ?", (f"{prefix}%",),
        ).fetchone()[0])


def _receipt_effect_counts(owner: NativeProductionResourceOwner) -> tuple[int, int, int]:
    """Receipt operations are ledger evidence, never semantic publications."""
    with open_existing_native_core_connection(owner.authority_facts.core_database_path) as opened:
        connection = opened.connection
        return tuple(int(connection.execute(query).fetchone()[0]) for query in (
            "SELECT count(*) FROM operations WHERE idempotency_key LIKE 'NATIVE_PUBLIC_MUTATION_RECEIPT:%'",
            "SELECT count(*) FROM semantic_transitions t JOIN operations o ON o.operation_id=t.operation_id "
            "WHERE o.idempotency_key LIKE 'NATIVE_PUBLIC_MUTATION_RECEIPT:%'",
            "SELECT count(*) FROM operation_outputs out JOIN operations o ON o.operation_id=out.operation_id "
            "WHERE o.idempotency_key LIKE 'NATIVE_PUBLIC_MUTATION_RECEIPT:%'",
        ))


def _native_durable_counts(owner: NativeProductionResourceOwner) -> tuple[int, ...]:
    with open_existing_native_core_connection(owner.authority_facts.core_database_path) as opened:
        connection = opened.connection
        return tuple(int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]) for table in (
            "objects", "object_revisions", "relationships", "relationship_revisions",
            "representations", "representation_payloads", "operations",
        ))


def _reopen_executor(
    executor: NativePublicIngestExecutor,
    owner: NativeProductionResourceOwner,
    fabric: TormentFabric,
) -> tuple[NativePublicIngestExecutor, NativeProductionResourceOwner]:
    """Recreate the owner/process-local native state over the same core."""
    agreement = owner._revalidate_authority()
    reopened = NativeProductionResourceOwner.from_native_agreement(
        data_root=owner.authority_facts.data_root,
        effective_profile=owner._effective_profile,
        agreement=agreement,
        admission_descriptor_path=owner._admission_descriptor_path,
    )
    owner.close()
    owner_ref = executor._test_owner_ref  # type: ignore[attr-defined]
    owner_ref[0] = reopened
    return (
        NativePublicIngestExecutor(
            owner=reopened,
            fabric=fabric,
            post_write_configuration=executor._test_post_write_configuration,  # type: ignore[attr-defined]
        ),
        reopened,
    )


def test_prepared_receipt_round_trips_exact_float32_carrier(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    try:
        with pytest.raises(NativePublicIngestInterruption):
            executor.execute(_request(), _test_interrupt_after="PREPARED")
        # Read the durable state through the receipt API, not through private
        # test-only SQLite row construction.
        store = NativePublicMutationReceiptStore(owner)
        prepared_recovery = store.recover(store.reserve(
            workspace_id="orchard", agent_id="aria", operation="ingest",
            native_operation_key="public-mutation/v1/" + "0" * 64,
            public_request_fingerprint="wrong",
        ))
        assert prepared_recovery.state is PublicMutationRecoveryState.NEW

        prepared = fabric.ingest(
            "orchard", "aria", "round trip", supplied_embedding=[1.0, 0.0, 0.0],
            public_mutation_key="serialization-key", _prepare_only=True,
        )
        payload = serialize_prepared_fabric_ingest(prepared)
        hydrated = deserialize_prepared_fabric_ingest(payload)
        assert np.array_equal(hydrated.embedding, prepared.embedding)
        assert hydrated.embedding.dtype == np.dtype("float32")
        assert hydrated.public_request_fingerprint == prepared.public_request_fingerprint
        assert hydrated.domain_ranked == prepared.domain_ranked
        assert hydrated.signal_half_life_days == prepared.signal_half_life_days
        assert serialize_prepared_fabric_ingest(hydrated) == payload
        payload["embedding"]["sha256"] = "0" * 64
        with pytest.raises(ValueError, match="prepared receipt"):
            deserialize_prepared_fabric_ingest(payload)
    finally:
        fabric.close()
        owner.close()


def test_complete_retry_replays_exact_result_without_cognition_or_legacy_graph(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    graph = fabric.private_graphs[fabric._agent_key("orchard", "aria")]
    process_calls = 0
    original_process = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal process_calls
        process_calls += 1
        return original_process(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    monkeypatch.setattr(graph, "search_by_embedding", lambda *_a, **_k: pytest.fail("legacy graph authority"))
    monkeypatch.setattr(graph, "spawn_memory", lambda *_a, **_k: pytest.fail("legacy graph authority"))
    monkeypatch.setattr(graph, "flush_node", lambda *_a, **_k: pytest.fail("legacy graph authority"))
    try:
        first = executor.execute(_request())
        replay = executor.execute(_request())
        assert replay == first
        assert process_calls == 1
        assert graph.entities == {}
    finally:
        fabric.close()
        owner.close()


def test_changed_request_conflicts_before_cognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        executor.execute(_request())
        with pytest.raises(PublicMutationIdempotencyConflict, match="PUBLIC_IDEMPOTENCY_CONFLICT"):
            executor.execute(_request(text="changed public meaning"))
        assert calls == 1
    finally:
        fabric.close()
        owner.close()


def test_cognition_started_is_a_fail_closed_uncertain_window(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    try:
        with pytest.raises(NativePublicIngestInterruption):
            executor.execute(_request(), _test_interrupt_after="COGNITION_STARTED")
        with pytest.raises(PublicMutationRecoveryRequired, match="COGNITION_OUTCOME_UNCERTAIN"):
            executor.execute(_request())
    finally:
        fabric.close()
        owner.close()


def test_prepared_retry_executes_storage_once_without_reprocessing(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        with pytest.raises(NativePublicIngestInterruption):
            executor.execute(_request(), _test_interrupt_after="PREPARED")
        result = executor.execute(_request())
        assert result["stored"] is True
        assert calls == 1
    finally:
        fabric.close()
        owner.close()


def test_receipt_stages_are_ledger_only_and_bind_one_immutable_result(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    try:
        result = executor.execute(_request("ledger-only"))
        # RESERVED, COGNITION_STARTED, PREPARED, and COMPLETE are the only
        # public recovery receipts.  They cannot publish a native source.
        assert _receipt_effect_counts(owner) == (4, 0, 0)

        store = NativePublicMutationReceiptStore(owner)
        reservation = store.reserve(
            workspace_id="orchard", agent_id="aria", operation="ingest",
            native_operation_key=(
                "public-mutation/v1/"
                "b0f09e52f0e1a1e6aebc1f52df2f2823b2a08ef7cb9759f8609700d2e3e10e65"
            ),
            public_request_fingerprint="different-operation",
        )
        # A fabricated reservation has no PREPARED evidence, proving that the
        # receipt API will not synthesize completion outputs or transitions.
        assert store.recover(reservation).state is PublicMutationRecoveryState.NEW
        assert result["stored"] is True
    finally:
        fabric.close()
        owner.close()


def test_w0_reserved_retry_starts_cognition_once(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        with pytest.raises(NativePublicIngestInterruption, match="RESERVED"):
            executor.execute(_request("w0"), _test_interrupt_after="RESERVED")
        assert executor.execute(_request("w0"))["stored"] is True
        assert calls == 1
    finally:
        fabric.close()
        owner.close()


def test_w2_preparation_failure_is_fail_closed_without_a_second_cognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0

    def interrupted_process(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise NativePublicIngestInterruption("forced during preparation")

    monkeypatch.setattr(fabric.kernel, "process", interrupted_process)
    try:
        with pytest.raises(NativePublicIngestInterruption, match="during preparation"):
            executor.execute(_request("w2"))
        with pytest.raises(PublicMutationRecoveryRequired, match="COGNITION_OUTCOME_UNCERTAIN"):
            executor.execute(_request("w2"))
        assert calls == 1
    finally:
        fabric.close()
        owner.close()


def test_w4_source_commit_recovery_reuses_native_source_without_recognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            executor.execute(_request("w4"), _test_storage_stop_after="source")
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
        recovered = executor.execute(_request("w4"))
        assert recovered["stored"] is True and recovered["reinforced"] is False
        assert calls == 1
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
    finally:
        fabric.close()
        owner.close()


def test_w6_post_write_response_loss_converges_before_completion(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        with pytest.raises(NativePublicIngestInterruption, match="post-write"):
            executor.execute(_request("w6"), _test_interrupt_after="POST_WRITE")
        # The native source was already durable, but public completion was
        # intentionally absent.  Retrying reuses both source and tail keys.
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
        result = executor.execute(_request("w6"))
        assert result["stored"] is True
        assert calls == 1
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
    finally:
        fabric.close()
        owner.close()


def test_restart_w5_partial_post_write_converges_without_duplicate_native_effects(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    original = LegacyFabricPostWriteAdapter._run_world_step

    def interrupt_after_world_step(adapter, context):
        original(adapter, context)
        raise NativePublicIngestInterruption("forced during post-write tail")

    monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_world_step", interrupt_after_world_step)
    reopened = None
    try:
        with pytest.raises(NativePublicIngestInterruption, match="post-write tail"):
            executor.execute(_request("restart-w5"))
        after_partial = _native_durable_counts(owner)
        # Restore the unchanged tail, then recreate its B5-A3 process-local
        # state over the same active core before recovery.
        monkeypatch.setattr(LegacyFabricPostWriteAdapter, "_run_world_step", original)
        restarted, reopened = _reopen_executor(executor, owner, fabric)
        assert restarted.execute(_request("restart-w5"))["stored"] is True
        after_recovery = _native_durable_counts(reopened)
        assert after_recovery[:-1] == after_partial[:-1]
        # The only new durable row is the immutable public COMPLETE receipt.
        assert after_recovery[-1] == after_partial[-1] + 1
        assert _native_operation_count(reopened, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
    finally:
        fabric.close()
        (reopened or owner).close()


def test_no_write_prepared_completion_replays_without_native_source_or_cognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    request = _request("no-write", text="")
    try:
        first = executor.execute(request)
        replay = executor.execute(request)
        assert first == replay
        assert first["stored"] is False and first["reinforced"] is False
        assert calls == 1
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 0
    finally:
        fabric.close()
        owner.close()


def test_soft_write_gate_is_decided_once_across_lost_response_replay(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    identity = fabric.ident_store.load("orchard", "aria")
    identity.overlay["write_threshold"] = 1.0
    identity.overlay["write_band"] = 0.1
    fabric.ident_store.save(identity)
    draws = 0

    def random_chance(_probability):
        nonlocal draws
        draws += 1
        return True

    monkeypatch.setattr("torment_service.fabric.random_chance", random_chance)
    request = _request("soft-gate")
    try:
        with pytest.raises(NativePublicIngestInterruption, match="post-write"):
            executor.execute(request, _test_interrupt_after="POST_WRITE")
        assert executor.execute(request)["stored"] is True
        assert draws == 1
    finally:
        fabric.close()
        owner.close()


@pytest.mark.parametrize(
    "changes",
    (
        {"text": "changed text"},
        {"step": 8},
        {"supplied_embedding": [0.0, 1.0, 0.0]},
        {"scope": "shared", "domain_id": "research"},
    ),
)
def test_changed_public_semantics_conflict_before_cognition(tmp_path: Path, monkeypatch, changes):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    try:
        executor.execute(_request("changed-fields"))
        with pytest.raises(PublicMutationIdempotencyConflict, match="PUBLIC_IDEMPOTENCY_CONFLICT"):
            executor.execute(_request("changed-fields", **changes))
        assert calls == 1
    finally:
        fabric.close()
        owner.close()


def test_new_and_reinforcement_results_replay_without_second_native_source(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    try:
        created = executor.execute(_request("create"))
        reinforced = executor.execute(_request("reinforce"))
        replay = executor.execute(_request("reinforce"))
        assert created["stored"] is True and created["reinforced"] is False
        assert reinforced["stored"] is True and reinforced["reinforced"] is True
        assert replay == reinforced and replay["eid"] == created["eid"]
        assert _native_operation_count(owner, "NATIVE_REINFORCEMENT:SOURCE:") == 1
    finally:
        fabric.close()
        owner.close()


def test_shared_source_replay_does_not_duplicate_its_native_source(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    request = _request(
        "shared-source", scope="shared", domain_id="research", step=200,
        text="I feel very angry and furious",
    )
    try:
        first = executor.execute(request)
        replay = executor.execute(request)
        assert first == replay
        assert first["stored"] is True and first["domain_chosen"] == "research"
        assert _native_operation_count(owner, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
    finally:
        fabric.close()
        owner.close()


def test_caller_structural_payload_shadows_cannot_alter_native_route_facts(tmp_path: Path):
    executor, owner, fabric = _executor(tmp_path)
    request = _request(
        "structural-shadow",
        extra_payload={
            "scope": "shared",
            "provenance": {"source_type": "forged"},
            "governance": {"protected": True},
            "ordinary_note": "retained",
        },
    )
    try:
        result = executor.execute(request)
        assert result["stored"] is True
        assert result["domain_chosen"] == "personal"
    finally:
        fabric.close()
        owner.close()


def test_restart_w3_prepared_receipt_resumes_without_cognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    reopened = None
    try:
        with pytest.raises(NativePublicIngestInterruption, match="PREPARED"):
            executor.execute(_request("restart-w3"), _test_interrupt_after="PREPARED")
        restarted, reopened = _reopen_executor(executor, owner, fabric)
        assert restarted.execute(_request("restart-w3"))["stored"] is True
        assert calls == 1
    finally:
        fabric.close()
        (reopened or owner).close()


def test_restart_w4_source_commit_recovers_with_fresh_native_process_state(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    reopened = None
    try:
        with pytest.raises(RuntimeError, match="committed native new-memory source"):
            executor.execute(_request("restart-w4"), _test_storage_stop_after="source")
        restarted, reopened = _reopen_executor(executor, owner, fabric)
        assert restarted.execute(_request("restart-w4"))["stored"] is True
        assert calls == 1
        assert _native_operation_count(reopened, "NATIVE_FABRIC_NEW_MEMORY:SOURCE:") == 1
    finally:
        fabric.close()
        (reopened or owner).close()


def test_restart_w7_completion_replays_exact_result_without_cognition(tmp_path: Path, monkeypatch):
    executor, owner, fabric = _executor(tmp_path)
    calls = 0
    original = fabric.kernel.process

    def process(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(fabric.kernel, "process", process)
    reopened = None
    try:
        first = executor.execute(_request("restart-w7"))
        restarted, reopened = _reopen_executor(executor, owner, fabric)
        assert restarted.execute(_request("restart-w7")) == first
        assert calls == 1
    finally:
        fabric.close()
        (reopened or owner).close()
