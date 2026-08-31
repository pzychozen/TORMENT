"""Focused guards for the 7G5D1 experiment-local trace-replay preflight."""
from __future__ import annotations

from dataclasses import replace
import inspect
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from uuid import uuid4

import numpy as np
import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.post_write_runtime import PostWriteStorageOutcome
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.fabric_native_routing import NativeFabricRouteResult, NativeFabricRoutingCapability
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteBehavior,
    NativePostWriteQualificationProfile,
    _ForbiddenNativeGraph,
)
from torment_service.substrate.runtime_binding import NativeRepresentationLane

from experiments.memory_substrate_d1_trace_replay_v1.compare import compare_scalar, compare_vector
from experiments.memory_substrate_d1_trace_replay_v1.baseline import LegacyBaselineBuilder, LegacyBaselineSpec
from experiments.memory_substrate_d1_trace_replay_v1.fixture_qualification import (
    FixtureKind,
    CharacterSubarmQualification,
    FrozenFixtureEvidence,
    FrozenReplayArm,
    FrozenReplayPlan,
    FrozenFixtureSet,
    StorageDecisionEvidence,
    WriteGateEvidence,
    load_fixture_recipes,
)
from experiments.memory_substrate_d1_trace_replay_v1.legacy_capture import (
    LegacyCapturedEvent,
    LegacyObservedOutcome,
    LegacyStorageFacingFacts,
    require_no_forced_reinforcement_target,
)
from experiments.memory_substrate_d1_trace_replay_v1.n0 import N0BaselineRefused, materialize_l0_snapshot, validate_n0_readiness
from experiments.memory_substrate_d1_trace_replay_v1.native_replay import NativeCoreStorageSnapshot, NativeReplayHarness
from experiments.memory_substrate_d1_trace_replay_v1.protocol import (
    ComparisonTolerances,
    D1ProtocolError,
    FROZEN_TOLERANCES,
    ReplayOperationKeyRegistry,
    StoreDisposition,
    StoreDispositionManifest,
    refuse_formal_administration,
)
from experiments.memory_substrate_d1_trace_replay_v1.report import D1PreflightReport


_ROOT = Path(__file__).resolve().parents[1]
_PACKAGE = _ROOT / "experiments" / "memory_substrate_d1_trace_replay_v1"


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane("fixture-provider", "fixture-model", 3, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32")


def _facts(*, fixture_id: str = "M1", operation_key: str = "D1:REPLAY:M1:0:abcdef", vector=(1.0, 2.0, 3.0)) -> LegacyStorageFacingFacts:
    return LegacyStorageFacingFacts(
        fixture_id=fixture_id, workspace_id="d1-workspace", agent_id="d1-agent", scope="private", domain_id="research",
        native_operation_key=operation_key, text="fixture text", summary="fixture summary", embedding=np.asarray(vector, dtype=np.float32),
        embedder_lane=_lane(), memory_type="episodic", memory_class="core", strength=0.9, confidence=0.8,
        half_life_days=30.0, logical_step=1, created_ts=10, last_active_ts=10, last_reinforced_ts=10,
        provenance=ProvenanceV1(), governance=MemoryGovernanceFlags(), flexible_payload={},
    )


class _RecordingHttp:
    def __init__(self) -> None:
        self.calls = []

    def request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if path == "/workspace/create":
            return {"workspace_id": payload["workspace_id"], "domains": payload["domains"]}
        return {"workspace_id": payload["workspace_id"], "agent_id": payload["agent_id"]}


def _write_l0_tree(root: Path) -> None:
    base = root / "workspaces" / "d1-workspace"
    private = base / "agents" / "d1-agent" / "private"
    (private / "embeddings").mkdir(parents=True)
    (base / "seeds" / "seed-1").mkdir(parents=True)
    (base / "domains" / "research").mkdir(parents=True)
    (base / "workspace_meta.json").write_text('{"workspace_id":"d1-workspace","embedding_lock":"fixture"}', encoding="utf-8")
    (base / "agents" / "d1-agent" / "identity.json").write_text('{"seed":{"seed_id":"seed-1"}}', encoding="utf-8")
    (base / "agents" / "d1-agent" / "character_state.json").write_text('{"seed_id":"seed-1"}', encoding="utf-8")
    (base / "seeds" / "seed-1" / "seed.json").write_text('{"seed_id":"seed-1"}', encoding="utf-8")
    (private / "nodes.jsonl").write_bytes(b'{"eid":1}\n')
    (private / "embeddings" / "1.npy").write_bytes(b"exact-embedding-bytes")
    (base / "domains" / "research" / "motifs.json").write_bytes(b'{"motifs":[]}')


def test_d1_l0_uses_http_creation_and_materializes_byte_exact_immutable_snapshot(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    _write_l0_tree(root)
    transport = _RecordingHttp()
    builder = LegacyBaselineBuilder(transport, LegacyBaselineSpec(root, "d1-workspace", "d1-agent", {"seed_id": "seed-1"}))
    receipt = builder.create_l0()
    assert receipt.formal_trace_administered is False
    assert [call[1] for call in transport.calls] == ["/workspace/create", "/agent/create"]
    with pytest.raises(D1ProtocolError, match="only after clean"):
        builder.freeze_after_clean_shutdown(service_has_stopped=False)
    baseline = builder.freeze_after_clean_shutdown(service_has_stopped=True)
    snapshot = materialize_l0_snapshot(baseline=baseline, destination=tmp_path / "snapshot")
    assert (snapshot / "nodes.jsonl").read_bytes() == b'{"eid":1}\n'
    assert (snapshot / "embeddings" / "1.npy").read_bytes() == b"exact-embedding-bytes"
    assert (snapshot / "workspaces" / "d1-workspace" / "workspace_meta.json").is_file()


class _FakeRouter:
    def __init__(self) -> None:
        self.requests = []

    def route(self, request):
        self.requests.append(request)
        return SimpleNamespace(
            qualification=SimpleNamespace(eligible=True, reason_code="QUALIFIED"),
            result=NativeFabricRouteResult(True, False, 7, "research", ("motif-a",), uuid4(), uuid4(), uuid4()),
        )


class _FakePostWrite:
    def __init__(self) -> None:
        self.calls = []

    def run(self, context, *, route_witness):
        self.calls.append((context, route_witness))
        return SimpleNamespace(proposal_id=None)


def test_d1_route_uses_only_storage_facts_and_independent_native_selection() -> None:
    router, post_write = _FakeRouter(), _FakePostWrite()
    event = LegacyCapturedEvent(
        _facts(),
        LegacyObservedOutcome(True, True, 999, ("legacy-answer",), conflict_target_eid=999),
    )
    outcome = NativeReplayHarness(
        router=router, post_write=post_write,
        native_storage_snapshot=lambda: NativeCoreStorageSnapshot((("objects", 1),)),
    ).replay(event)
    assert outcome.storage_outcome is PostWriteStorageOutcome.CREATED_NEW
    assert len(router.requests) == len(post_write.calls) == 1
    request = router.requests[0]
    assert request.raw_links == () and request.qualified_link_targets == ()
    assert not hasattr(request, "reinforcement_target_eid")
    assert not hasattr(request, "legacy_reinforcement_target_eid")
    assert post_write.calls[0][1].route_result.eid == 7
    require_no_forced_reinforcement_target({})
    with pytest.raises(D1ProtocolError):
        require_no_forced_reinforcement_target({"legacy_reinforcement_target_eid": 999})


def test_d1_no_write_performs_zero_native_router_or_tail_mutations() -> None:
    router, post_write = _FakeRouter(), _FakePostWrite()
    event = LegacyCapturedEvent(_facts(fixture_id="M5"), LegacyObservedOutcome(False, False, None))
    outcome = NativeReplayHarness(
        router=router, post_write=post_write,
        native_storage_snapshot=lambda: NativeCoreStorageSnapshot((("objects", 1),)),
    ).replay(event)
    assert outcome.storage_outcome is PostWriteStorageOutcome.NO_WRITE
    assert outcome.route_attempt is None and outcome.post_write_outcome is not None
    assert router.requests == [] and len(post_write.calls) == 1
    context, witness = post_write.calls[0]
    assert context.storage_outcome is PostWriteStorageOutcome.NO_WRITE
    assert witness.route_result is None and witness.native_operation_key is None


def test_d1_no_write_rejects_any_durable_native_storage_mutation() -> None:
    router, post_write = _FakeRouter(), _FakePostWrite()
    snapshots = iter((
        NativeCoreStorageSnapshot((("objects", 1),)),
        NativeCoreStorageSnapshot((("objects", 2),)),
    ))
    harness = NativeReplayHarness(
        router=router, post_write=post_write, native_storage_snapshot=lambda: next(snapshots),
    )
    with pytest.raises(D1ProtocolError, match="changed durable native storage"):
        harness.replay(LegacyCapturedEvent(_facts(fixture_id="M5"), LegacyObservedOutcome(False, False, None)))


def test_d1_representation_input_keeps_captured_raw_float32_bytes_exact() -> None:
    raw = np.array([1.0, -2.5, 0.125], dtype=np.float32)
    facts = _facts(vector=raw)
    assert facts.embedding.dtype == np.float32
    assert facts.embedding.flags.c_contiguous and not facts.embedding.flags.writeable
    assert facts.embedding_bytes == raw.tobytes(order="C")
    assert facts.embedding_sha256 == __import__("hashlib").sha256(raw.tobytes(order="C")).hexdigest()


def test_d1_fixture_recipes_and_hard_qualification_margins_are_frozen() -> None:
    recipe = json.loads((_PACKAGE / "fixtures" / "preflight_fixture_recipes_v1.json").read_text(encoding="utf-8"))
    assert set(load_fixture_recipes(recipe)) == set(FixtureKind)
    base_write = WriteGateEvidence(True, 0.90, 0.50, 0.05)
    fixtures = (
        FrozenFixtureEvidence("M1", FixtureKind.M1_CREATE, "1" * 64, True, base_write, StorageDecisionEvidence(None, None, 0.90, 0.70, None), (), 12),
        FrozenFixtureEvidence("M2-create", FixtureKind.M2_REINFORCE, "2" * 64, True, base_write, StorageDecisionEvidence(None, None, 0.90, 0.70, None), (), 12),
        FrozenFixtureEvidence("M2-duplicate", FixtureKind.M2_REINFORCE, "8" * 64, True, base_write, StorageDecisionEvidence(0.95, 0.90, 0.90, 0.70, True), (), 12),
        FrozenFixtureEvidence("M3", FixtureKind.M3_DISTINCT, "3" * 64, True, base_write, StorageDecisionEvidence(0.70, 0.90, 0.90, 0.70, False), (), 12),
        FrozenFixtureEvidence("M4", FixtureKind.M4_CONTRADICTION, "4" * 64, True, base_write, StorageDecisionEvidence(0.70, 0.90, 0.90, 0.70, False), (), 12),
        FrozenFixtureEvidence("M5", FixtureKind.M5_NO_WRITE, "5" * 64, False, WriteGateEvidence(False, 0.0, 0.50, 0.05), None, (), 12),
        FrozenFixtureEvidence("S", FixtureKind.SEQUENTIAL, "6" * 64, True, base_write, StorageDecisionEvidence(None, None, 0.90, 0.70, None), (), 12),
        FrozenFixtureEvidence("C", FixtureKind.CHARACTER_SUBARM, "7" * 64, True, base_write, StorageDecisionEvidence(None, None, 0.90, 0.70, None), (), 12),
    )
    frozen = FrozenFixtureSet("a" * 64, fixtures)
    frozen.validate()
    plan = FrozenReplayPlan(
        micro_arms=(
            FrozenReplayArm("M1_CREATE", "L0-M1", "N0-M1", ("M1",)),
            FrozenReplayArm("M2_REINFORCE", "L0-M2", "N0-M2", ("M2-create", "M2-duplicate")),
            FrozenReplayArm("M3_DISTINCT", "L0-M3", "N0-M3", ("M3",)),
            FrozenReplayArm("M4_CONTRADICTION", "L0-M4", "N0-M4", ("M4",)),
            FrozenReplayArm("M5_NO_WRITE", "L0-M5", "N0-M5", ("M5",)),
        ),
        sequential_arm=FrozenReplayArm("SEQUENTIAL", "L0-S", "N0-S", ("S",)),
        character_arm=FrozenReplayArm("CHARACTER_SUBARM", "L0-C", "N0-C", ("C",), True),
    )
    plan.validate(frozen)
    CharacterSubarmQualification(3, 25, True, True, False, False, True).validate()
    assert frozen.freeze_inputs().tolerances_sha256 == FROZEN_TOLERANCES.digest
    with pytest.raises(D1ProtocolError):
        replace(fixtures[0], pre_event_motif_member_count=80).validate()
    with pytest.raises(D1ProtocolError):
        replace(fixtures[1], decision=StorageDecisionEvidence(0.91, 0.90, 0.90, 0.70, True)).validate()
    with pytest.raises(D1ProtocolError):
        FrozenReplayPlan(plan.micro_arms, plan.sequential_arm, replace(plan.character_arm, character_specific_baseline=False)).validate(frozen)
    with pytest.raises(D1ProtocolError):
        CharacterSubarmQualification(3, 25, True, True, False, True, True).validate()


def test_d1_operation_keys_are_stable_unique_and_reused_only_for_exact_retries() -> None:
    registry = ReplayOperationKeyRegistry()
    first = registry.claim(fixture_id="M2", ordinal=0, request_sha256="a" * 64)
    assert registry.claim(fixture_id="M2", ordinal=0, request_sha256="a" * 64) == first
    assert registry.claim(fixture_id="M2", ordinal=1, request_sha256="a" * 64) != first
    assert registry.claim(fixture_id="M3", ordinal=0, request_sha256="a" * 64) != first
    with pytest.raises(D1ProtocolError):
        registry.claim(fixture_id="M2", ordinal=0, request_sha256="b" * 64)


def test_d1_staging_only_profile_and_excluded_feature_contract_remain_explicit() -> None:
    fields = NativeFabricRoutingCapability.__dataclass_fields__
    assert fields["production_activation_allowed"].default is False
    assert fields["qualification_only"].default is True
    profile = NativePostWriteQualificationProfile.core_staging_with_character()
    assert profile.motif_suggestion_maintenance is NativePostWriteBehavior.REQUIRED_NOOP
    assert profile.motif_auto_merge is NativePostWriteBehavior.UNSUPPORTED
    assert profile.character is NativePostWriteBehavior.QUALIFIED
    assert profile.compression is NativePostWriteBehavior.UNSUPPORTED
    assert profile.deep_memory is NativePostWriteBehavior.UNSUPPORTED
    assert profile.checkpoint is NativePostWriteBehavior.DISABLED_FOR_PROFILE
    assert profile.bridge_suggestions is NativePostWriteBehavior.DISABLED_FOR_PROFILE


def test_d1_has_no_production_selector_or_memory_graph_fallback() -> None:
    for path in (_ROOT / "torment_service" / "app.py", _ROOT / "torment_service" / "fabric.py", _ROOT / "torment_service" / "memory_graph.py"):
        assert "memory_substrate_d1_trace_replay_v1" not in path.read_text(encoding="utf-8")
    source = inspect.getsource(NativeReplayHarness)
    assert "MemoryGraph" not in source
    assert "_router.route" in source
    with pytest.raises(AssertionError, match="forbidden MemoryGraph"):
        _ForbiddenNativeGraph().read_current(1)
    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert not set(changed).intersection({
        "torment_service/fabric.py", "torment_service/app.py", "torment_service/memory_graph.py",
    })


def test_d1_tolerances_are_immutable_and_store_dispositions_are_total() -> None:
    assert compare_vector([1.0], [1.0]).equivalent
    assert compare_scalar(1.0, 1.0, field="score").equivalent
    changed = ComparisonTolerances(1e-5, 1e-7, 1e-6, 1e-6, 1e-6, 1e-6)
    with pytest.raises(D1ProtocolError):
        compare_vector([1.0], [1.0], tolerances=changed)
    stores = StoreDispositionManifest((("private/nodes", StoreDisposition.IN_SCOPE_EXACT), ("character", StoreDisposition.OUT_OF_PROFILE)))
    stores.validate_observed({"private/nodes", "character"})
    with pytest.raises(D1ProtocolError):
        stores.validate_observed({"private/nodes", "character", "unknown-store"})
    with pytest.raises(D1ProtocolError):
        stores.validate_observed({"private/nodes"})


def test_d1_n0_requires_b4a_and_refuses_b4b_or_incomplete_readiness() -> None:
    ready = SimpleNamespace(
        memory_closure_ready=True, motif_closure_ready=True, member_reference_closure_ready=True,
        core_staging_runtime_ready=True, controlled_native_staging_experiment_ready=True,
        b4a_ready_motif_count=1, b4b_ready_motif_count=0,
    )
    validate_n0_readiness(ready)
    with pytest.raises(N0BaselineRefused):
        validate_n0_readiness(SimpleNamespace(**(vars(ready) | {"b4a_ready_motif_count": 0})))
    with pytest.raises(N0BaselineRefused):
        validate_n0_readiness(SimpleNamespace(**(vars(ready) | {"b4b_ready_motif_count": 1})))
    with pytest.raises(N0BaselineRefused):
        validate_n0_readiness(SimpleNamespace(**(vars(ready) | {"memory_closure_ready": False})))


def test_d1_cannot_record_results_or_formally_administer_before_future_authority() -> None:
    # A minimally-shaped frozen input is enough to prove the administration gate itself.
    inputs = SimpleNamespace(protocol_sha256="a" * 64, fixture_sha256="b" * 64, tolerances_sha256=FROZEN_TOLERANCES.digest)
    with pytest.raises(D1ProtocolError):
        refuse_formal_administration(None)
    with pytest.raises(D1ProtocolError):
        refuse_formal_administration(inputs)
    fingerprint = SimpleNamespace()
    with pytest.raises(D1ProtocolError):
        D1PreflightReport(fingerprint, inputs, True, True, True, True, True, True, results=({"native": "result"},))
