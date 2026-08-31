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
from torment_service.kernel.trajectory_v2 import TrajectoryV2Writer

from experiments.memory_substrate_d1_trace_replay_v1.compare import compare_scalar, compare_vector
from experiments.memory_substrate_d1_trace_replay_v1.baseline import LegacyBaselineBuilder, LegacyBaselineSpec
from experiments.memory_substrate_d1_trace_replay_v1.manifest import (
    CORE_CHARACTER_FREE_BASELINE_PROFILE,
    fingerprint_legacy_baseline,
)
from experiments.memory_substrate_d1_trace_replay_v1.side_store_observation import (
    observe_frozen_d1_core_retained_side_stores,
)
from experiments.memory_substrate_d1_trace_replay_v1.fixture_qualification import (
    FixtureKind,
    CharacterSubarmQualification,
    DuplicateDecisionKind,
    FrozenFixtureEvidence,
    FrozenReplayArm,
    FrozenReplayPlan,
    FrozenFixtureSet,
    ReplayEventRole,
    StorageDecisionEvidence,
    WriteGateEvidence,
    load_fixture_recipes,
)
from experiments.memory_substrate_d1_trace_replay_v1.legacy_capture import (
    LegacyCapturedEvent,
    InitialPostWritePlaceholderPosture,
    LegacyObservedOutcome,
    LegacyStorageFacingFacts,
    require_no_forced_reinforcement_target,
)
from experiments.memory_substrate_d1_trace_replay_v1.n0 import (
    N0BaselineRefused,
    materialize_l0_snapshot,
    require_d1_motif_alias_separation,
    validate_n0_readiness,
)
from experiments.memory_substrate_d1_trace_replay_v1.native_replay import NativeCoreStorageSnapshot, NativeReplayHarness
from experiments.memory_substrate_d1_trace_replay_v1.formal import (
    FormalAdministrationAuthorization,
    FormalAdministrationRefused,
    FormalAdministrationRunner,
)
from experiments.memory_substrate_d1_trace_replay_v1.protocol import (
    ComparisonTolerances,
    D1ProtocolError,
    FROZEN_TOLERANCES,
    FrozenAdministrationInputs,
    ReplayOperationKeyRegistry,
    StoreDisposition,
    StoreDispositionRule,
    StoreDispositionManifest,
    StorePresence,
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
        embedder_lane=_lane(), memory_type="episodic", memory_class="core", strength=0.9, confidence=0.8, promotion_score=0.7,
        half_life_days=30.0, logical_step=1, created_ts=10, last_active_ts=10, last_reinforced_ts=10,
        provenance=ProvenanceV1(), governance=MemoryGovernanceFlags(), flexible_payload={},
    )


_POSTURE = InitialPostWritePlaceholderPosture(False, "read_only")


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


def _write_character_free_core_l0_tree(root: Path) -> None:
    base = root / "workspaces" / "d1-core"
    private = base / "agents" / "core-agent" / "private"
    (private / "embeddings").mkdir(parents=True)
    (base / "domains" / "research").mkdir(parents=True)
    (base / "workspace_meta.json").write_text(
        '{"embed_provider":"hash","embed_model":"hash:3:core","embed_dim":3}', encoding="utf-8",
    )
    (base / "agents" / "core-agent" / "identity.json").write_text(
        '{"seed":{"d1_baseline_profile":"core_character_free"}}', encoding="utf-8",
    )
    (private / "nodes.jsonl").write_bytes(b'{"eid":1,"payload":{"summary":"ordinary core"}}\n')
    (private / "embeddings" / "shard_000000.npy").write_bytes(b"exact-embedding-bytes")
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


def test_core_d1_l0_has_no_character_seed_or_planting_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "core-legacy"
    _write_character_free_core_l0_tree(root)
    baseline = fingerprint_legacy_baseline(
        root=root, workspace_id="d1-core", agent_id="core-agent", character_seed_required=False,
    )
    assert baseline.baseline_profile == CORE_CHARACTER_FREE_BASELINE_PROFILE
    assert baseline.character_seed is None and baseline.character_state is None
    snapshot = materialize_l0_snapshot(baseline=baseline, destination=tmp_path / "core-snapshot")
    assert (snapshot / "nodes.jsonl").read_bytes() == b'{"eid":1,"payload":{"summary":"ordinary core"}}\n'
    assert not (snapshot / "workspaces" / "d1-core" / "seeds").exists()
    transport = _RecordingHttp()
    LegacyBaselineBuilder(
        transport, LegacyBaselineSpec(root, "d1-core", "core-agent", None),
    ).create_l0()
    agent_payload = transport.calls[1][2]
    assert agent_payload["seed"] == {"d1_baseline_profile": "core_character_free"}


def test_d1_core_side_store_observer_binds_complete_zero_and_real_trajectory_eid(tmp_path: Path) -> None:
    root = tmp_path / "core-side-stores"
    _write_character_free_core_l0_tree(root)
    private = root / "workspaces" / "d1-core" / "agents" / "core-agent" / "private"
    (private / "nodes.jsonl").write_text(
        '{"eid":1,"payload":{"scope":"private"}}\n', encoding="utf-8",
    )
    (private / "memory_events.jsonl").write_text(
        '{"type":"MEMORY_CREATE","eid":1,"scope":"private"}\n', encoding="utf-8",
    )
    shared = root / "workspaces" / "d1-core" / "domains" / "research" / "shared" / "trajectories" / "v2"
    shared.mkdir(parents=True)
    (shared / "boundaries.jsonl").write_text(
        '{"type":"EPOCH_START","epoch":1,"previous_epoch":0}\n', encoding="utf-8",
    )
    writer = TrajectoryV2Writer(str(private))
    entity = SimpleNamespace(
        eid=1, pos=np.zeros(3), vel=np.zeros(3), vel0=np.zeros(3),
        born_step=1, channel=0, alive=True, payload={},
    )
    assert writer.write_step([entity], 1).ok
    baseline = fingerprint_legacy_baseline(
        root=root, workspace_id="d1-core", agent_id="core-agent", character_seed_required=False,
    )
    artifact = observe_frozen_d1_core_retained_side_stores(
        root=root, workspace_id="d1-core", agent_id="core-agent", domain_id="research",
        legacy_source_namespace_id=uuid4(), expected_l0_fingerprint_sha256=baseline.digest,
    )
    by_store = {item.side_store: item for item in artifact.observations}
    assert by_store["deep_memory"].state.value == "COMPLETE_ABSENT"
    assert by_store["trajectory_evidence"].state.value == "COMPLETE_PRESENT_WITH_EIDS"
    assert by_store["trajectory_evidence"].references[0].eid == 1
    assert len(artifact.digest) == 64


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
        placeholder_posture=_POSTURE,
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
        placeholder_posture=_POSTURE,
    ).replay(event)
    assert outcome.storage_outcome is PostWriteStorageOutcome.NO_WRITE
    assert outcome.route_attempt is None and outcome.post_write_outcome is not None
    assert router.requests == [] and len(post_write.calls) == 1
    context, witness = post_write.calls[0]
    assert context.storage_outcome is PostWriteStorageOutcome.NO_WRITE
    assert witness.route_result is None and witness.native_operation_key is None


def test_d1_dedicated_no_write_context_never_routes() -> None:
    router, post_write = _FakeRouter(), _FakePostWrite()
    harness = NativeReplayHarness(
        router=router, post_write=post_write,
        native_storage_snapshot=lambda: NativeCoreStorageSnapshot((("objects", 1),)),
        placeholder_posture=_POSTURE,
    )
    context = NativeReplayHarness._context(
        _facts(fixture_id="M5"), outcome=PostWriteStorageOutcome.NO_WRITE, eid=None, motifs=(),
    )
    outcome = harness.replay_no_write_context(context)
    assert outcome.route_attempt is None and outcome.operation_key is None
    assert router.requests == [] and len(post_write.calls) == 1

    invalid = NativeReplayHarness._context(
        _facts(fixture_id="M5"), outcome=PostWriteStorageOutcome.CREATED_NEW, eid=1, motifs=(),
    )
    with pytest.raises(D1ProtocolError, match="dedicated NO_WRITE replay"):
        harness.replay_no_write_context(invalid)


def test_d1_no_write_rejects_any_durable_native_storage_mutation() -> None:
    router, post_write = _FakeRouter(), _FakePostWrite()
    snapshots = iter((
        NativeCoreStorageSnapshot((("objects", 1),)),
        NativeCoreStorageSnapshot((("objects", 2),)),
    ))
    harness = NativeReplayHarness(
        router=router, post_write=post_write, native_storage_snapshot=lambda: next(snapshots),
        placeholder_posture=_POSTURE,
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
    assert facts.promotion_score == 0.7


def test_d1_fixture_recipes_and_hard_qualification_margins_are_frozen() -> None:
    recipe = json.loads((_PACKAGE / "fixtures" / "preflight_fixture_recipes_v1.json").read_text(encoding="utf-8"))
    assert set(load_fixture_recipes(recipe)) == set(FixtureKind)
    base_write = WriteGateEvidence(True, 0.90, 0.50, 0.05)
    no_candidate = StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False)
    reinforce = StorageDecisionEvidence(DuplicateDecisionKind.REINFORCE_MATCH, 0.95, 0.90, 0.90, 0.70, True, False)
    distinct = StorageDecisionEvidence(DuplicateDecisionKind.CREATE_DISTINCT_BELOW_THRESHOLD, 0.70, 0.90, 0.90, 0.70, False, False)
    contradiction = StorageDecisionEvidence(DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.95, 0.90, 0.90, 0.70, False, True)
    fixtures = (
        FrozenFixtureEvidence("M1", FixtureKind.M1_CREATE, "1" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("M2-create", FixtureKind.M2_REINFORCE, "2" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("M2-duplicate", FixtureKind.M2_REINFORCE, "3" * 64, True, base_write, reinforce, (), 12),
        FrozenFixtureEvidence("M3-create", FixtureKind.M3_DISTINCT, "4" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("M3-distinct", FixtureKind.M3_DISTINCT, "5" * 64, True, base_write, distinct, (), 12),
        FrozenFixtureEvidence("M4-create", FixtureKind.M4_CONTRADICTION, "6" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("M4-contradiction", FixtureKind.M4_CONTRADICTION, "7" * 64, True, base_write, contradiction, (), 12),
        FrozenFixtureEvidence("M5", FixtureKind.M5_NO_WRITE, "8" * 64, False, WriteGateEvidence(False, 0.0, 0.50, 0.05), None, (), 12),
        FrozenFixtureEvidence("S-create", FixtureKind.SEQUENTIAL, "9" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("S-reinforce", FixtureKind.SEQUENTIAL, "a" * 64, True, base_write, reinforce, (), 12),
        FrozenFixtureEvidence("S-distinct", FixtureKind.SEQUENTIAL, "b" * 64, True, base_write, distinct, (), 12),
        FrozenFixtureEvidence("S-contradiction", FixtureKind.SEQUENTIAL, "c" * 64, True, base_write, contradiction, (), 12),
        FrozenFixtureEvidence("C-prep", FixtureKind.CHARACTER_SUBARM, "d" * 64, True, base_write, no_candidate, (), 12),
        FrozenFixtureEvidence("C-step25", FixtureKind.CHARACTER_SUBARM, "e" * 64, True, base_write, no_candidate, (), 12),
    )
    frozen = FrozenFixtureSet("a" * 64, fixtures)
    frozen.validate()
    plan = FrozenReplayPlan(
        micro_arms=(
            FrozenReplayArm("M1_CREATE", "L0-M1", "N0-M1", ("M1",), (ReplayEventRole.CREATE,)),
            FrozenReplayArm("M2_REINFORCE", "L0-M2", "N0-M2", ("M2-create", "M2-duplicate"), (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE)),
            FrozenReplayArm("M3_DISTINCT", "L0-M3", "N0-M3", ("M3-create", "M3-distinct"), (ReplayEventRole.CREATE, ReplayEventRole.DISTINCT)),
            FrozenReplayArm("M4_CONTRADICTION", "L0-M4", "N0-M4", ("M4-create", "M4-contradiction"), (ReplayEventRole.CREATE, ReplayEventRole.CONTRADICTION)),
            FrozenReplayArm("M5_NO_WRITE", "L0-M5", "N0-M5", ("M5",), (ReplayEventRole.NO_WRITE,)),
        ),
        sequential_arm=FrozenReplayArm("SEQUENTIAL", "L0-S", "N0-S", ("S-create", "S-reinforce", "S-distinct", "S-contradiction"), (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE, ReplayEventRole.DISTINCT, ReplayEventRole.CONTRADICTION)),
        character_arm=FrozenReplayArm("CHARACTER_SUBARM", "L0-C", "N0-C", ("C-prep", "C-step25"), (ReplayEventRole.CHARACTER_PREPARATION, ReplayEventRole.CHARACTER_ADMINISTRATION), True),
    )
    plan.validate(frozen)
    CharacterSubarmQualification(0, 25, True, True, False, False, True).validate()
    assert frozen.freeze_inputs().tolerances_sha256 == FROZEN_TOLERANCES.digest
    with pytest.raises(D1ProtocolError):
        replace(fixtures[0], pre_event_motif_member_count=80).validate()
    with pytest.raises(D1ProtocolError):
        replace(fixtures[2], decision=StorageDecisionEvidence(DuplicateDecisionKind.REINFORCE_MATCH, 0.91, 0.90, 0.90, 0.70, True, False)).validate()
    with pytest.raises(D1ProtocolError):
        FrozenReplayPlan(plan.micro_arms, plan.sequential_arm, replace(plan.character_arm, character_specific_baseline=False)).validate(frozen)
    with pytest.raises(D1ProtocolError):
        CharacterSubarmQualification(0, 25, True, True, False, True, True).validate()


def test_d1_replay_plan_rejects_reused_fixtures_clones_and_bad_role_shapes() -> None:
    write = WriteGateEvidence(True, 0.90, 0.50, 0.05)
    fixtures = (
        FrozenFixtureEvidence("M1", FixtureKind.M1_CREATE, "1" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("M2a", FixtureKind.M2_REINFORCE, "2" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("M2b", FixtureKind.M2_REINFORCE, "3" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.REINFORCE_MATCH, 0.95, 0.90, 0.90, 0.70, True, False), (), 0),
        FrozenFixtureEvidence("M3a", FixtureKind.M3_DISTINCT, "4" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("M3b", FixtureKind.M3_DISTINCT, "5" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_DISTINCT_BELOW_THRESHOLD, 0.70, 0.90, 0.90, 0.70, False, False), (), 0),
        FrozenFixtureEvidence("M4a", FixtureKind.M4_CONTRADICTION, "6" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("M4b", FixtureKind.M4_CONTRADICTION, "7" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.95, 0.90, 0.90, 0.70, False, True), (), 0),
        FrozenFixtureEvidence("M5", FixtureKind.M5_NO_WRITE, "8" * 64, False, WriteGateEvidence(False, 0.0, 0.50, 0.05), None, (), 0),
        FrozenFixtureEvidence("Sa", FixtureKind.SEQUENTIAL, "9" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("Sb", FixtureKind.SEQUENTIAL, "a" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.REINFORCE_MATCH, 0.95, 0.90, 0.90, 0.70, True, False), (), 0),
        FrozenFixtureEvidence("Sc", FixtureKind.SEQUENTIAL, "b" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_DISTINCT_BELOW_THRESHOLD, 0.70, 0.90, 0.90, 0.70, False, False), (), 0),
        FrozenFixtureEvidence("Sd", FixtureKind.SEQUENTIAL, "c" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.95, 0.90, 0.90, 0.70, False, True), (), 0),
        FrozenFixtureEvidence("Ca", FixtureKind.CHARACTER_SUBARM, "d" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
        FrozenFixtureEvidence("Cb", FixtureKind.CHARACTER_SUBARM, "e" * 64, True, write, StorageDecisionEvidence(DuplicateDecisionKind.CREATE_NO_CANDIDATE, None, None, 0.90, 0.70, False), (), 0),
    )
    frozen = FrozenFixtureSet("a" * 64, fixtures)
    micro = (
        FrozenReplayArm("M1_CREATE", "L1", "N1", ("M1",), (ReplayEventRole.CREATE,)),
        FrozenReplayArm("M2_REINFORCE", "L2", "N2", ("M2a", "M2b"), (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE)),
        FrozenReplayArm("M3_DISTINCT", "L3", "N3", ("M3a", "M3b"), (ReplayEventRole.CREATE, ReplayEventRole.DISTINCT)),
        FrozenReplayArm("M4_CONTRADICTION", "L4", "N4", ("M4a", "M4b"), (ReplayEventRole.CREATE, ReplayEventRole.CONTRADICTION)),
        FrozenReplayArm("M5_NO_WRITE", "L5", "N5", ("M5",), (ReplayEventRole.NO_WRITE,)),
    )
    sequential = FrozenReplayArm("SEQUENTIAL", "LS", "NS", ("Sa", "Sb", "Sc", "Sd"), (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE, ReplayEventRole.DISTINCT, ReplayEventRole.CONTRADICTION))
    character = FrozenReplayArm("CHARACTER_SUBARM", "LC", "NC", ("Ca", "Cb"), (ReplayEventRole.CHARACTER_PREPARATION, ReplayEventRole.CHARACTER_ADMINISTRATION), True)
    plan = FrozenReplayPlan(micro, sequential, character)
    plan.validate(frozen)
    with pytest.raises(D1ProtocolError, match="exactly once"):
        FrozenReplayPlan(micro, sequential, replace(character, fixture_ids=("M1", "Cb"))).validate(frozen)
    with pytest.raises(D1ProtocolError, match="legacy clone"):
        FrozenReplayPlan((replace(micro[0], legacy_clone_id="L2"), *micro[1:]), sequential, character).validate(frozen)
    with pytest.raises(D1ProtocolError, match="native clone"):
        FrozenReplayPlan((replace(micro[0], native_clone_id="N2"), *micro[1:]), sequential, character).validate(frozen)
    with pytest.raises(D1ProtocolError, match="sequential arm"):
        FrozenReplayPlan(micro, replace(sequential, event_roles=(ReplayEventRole.CREATE, ReplayEventRole.DISTINCT, ReplayEventRole.REINFORCE, ReplayEventRole.CONTRADICTION)), character).validate(frozen)
    with pytest.raises(D1ProtocolError, match="Character arm"):
        FrozenReplayPlan(micro, sequential, replace(character, event_roles=(ReplayEventRole.CREATE, ReplayEventRole.CHARACTER_ADMINISTRATION))).validate(frozen)


def test_d1_operation_keys_are_stable_unique_and_reused_only_for_exact_retries() -> None:
    registry = ReplayOperationKeyRegistry()
    first = registry.claim(fixture_id="M2", ordinal=0, request_sha256="a" * 64)
    assert registry.claim(fixture_id="M2", ordinal=0, request_sha256="a" * 64) == first
    assert registry.claim(fixture_id="M2", ordinal=1, request_sha256="a" * 64) != first
    assert registry.claim(fixture_id="M3", ordinal=0, request_sha256="a" * 64) != first
    with pytest.raises(D1ProtocolError):
        registry.claim(fixture_id="M2", ordinal=0, request_sha256="b" * 64)


def test_d1_m4_high_similarity_contradiction_is_distinct_from_m3() -> None:
    accepted = StorageDecisionEvidence(
        DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.95, 0.90, 0.90, 0.70, False, True,
    )
    accepted.validate()
    with pytest.raises(D1ProtocolError):
        StorageDecisionEvidence(
            DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.70, 0.90, 0.90, 0.70, False, True,
        ).validate()
    with pytest.raises(D1ProtocolError):
        StorageDecisionEvidence(
            DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD, 0.95, 0.90, 0.90, 0.70, False, False,
        ).validate()
    StorageDecisionEvidence(
        DuplicateDecisionKind.REINFORCE_MATCH, 0.95, 0.90, 0.90, 0.70, True, False,
    ).validate()
    StorageDecisionEvidence(
        DuplicateDecisionKind.CREATE_DISTINCT_BELOW_THRESHOLD, 0.70, 0.90, 0.90, 0.70, False, False,
    ).validate()


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


def test_d1_post_write_placeholder_posture_closes_every_material_consumer_gate() -> None:
    _POSTURE.validate()
    for posture in (
        InitialPostWritePlaceholderPosture(True, "read_only"),
        InitialPostWritePlaceholderPosture(False, "propose"),
        InitialPostWritePlaceholderPosture(False, "read_only", hivemind_packet_parity_tested=True),
        InitialPostWritePlaceholderPosture(False, "read_only", proposal_parity_tested=True),
    ):
        with pytest.raises(D1ProtocolError):
            posture.validate()
    context = NativeReplayHarness._context(_facts(), outcome=PostWriteStorageOutcome.CREATED_NEW, eid=1, motifs=("native-owned",))
    assert context.promotion_score == _facts().promotion_score
    assert context.created_motif is None and context.state_symbol is None


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
    stores = StoreDispositionManifest((
        StoreDispositionRule("private/nodes", StoreDisposition.IN_SCOPE_EXACT),
        StoreDispositionRule("character", StoreDisposition.OUT_OF_PROFILE),
        StoreDispositionRule("motif-merge-suggestions", StoreDisposition.OUT_OF_PROFILE, StorePresence.OPTIONAL_PRESENT),
    ))
    stores.validate_observed({"private/nodes", "character"})
    stores.validate_observed({"private/nodes", "character", "motif-merge-suggestions"})
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


def test_d1_n0_motif_alias_topology_keeps_source_and_runtime_identities_separate(tmp_path: Path) -> None:
    from test_substrate_migration_runtime_motif_projection import _context
    from torment_service.substrate.migration import NativeMigrationRuntimeMotifProjectionService
    from torment_service.substrate.ids import native_id_to_bytes

    qualified, facts = _context(tmp_path)
    try:
        connection, plan, request = facts["connection"], facts["plan"], facts["request"]
        source_alias = connection.execute(
            """SELECT legacy_source_namespace_id,object_id FROM legacy_object_aliases
                 WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?""",
            (native_id_to_bytes(request.legacy_source_namespace_id), request.runtime_motif_id),
        ).fetchone()
        assert source_alias == (native_id_to_bytes(request.legacy_source_namespace_id), native_id_to_bytes(facts["source"]))
        source_revision = connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(facts["source"]),),
        ).fetchone()
        assert plan.motif_alias_namespace_id != plan.legacy_source_namespace_id
        assert connection.execute(
            "SELECT source_key FROM legacy_source_namespaces WHERE legacy_source_namespace_id=?",
            (native_id_to_bytes(plan.motif_alias_namespace_id),),
        ).fetchone() == ("b4a-runtime-aliases",)
        require_d1_motif_alias_separation((plan,))
        result = NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(request)
        assert NativeMigrationRuntimeMotifProjectionService(connection).project_lane_preserving_legacy_motif(request) == result
        target_alias = connection.execute(
            """SELECT legacy_source_namespace_id,object_id FROM legacy_object_aliases
                 WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?""",
            (native_id_to_bytes(plan.motif_alias_namespace_id), request.runtime_motif_id),
        ).fetchone()
        assert target_alias == (native_id_to_bytes(plan.motif_alias_namespace_id), native_id_to_bytes(result.motif_object_id))
        assert target_alias[1] != source_alias[1]
        assert connection.execute(
            "SELECT current_revision_id,current_revision_ordinal FROM objects WHERE object_id=?",
            (native_id_to_bytes(facts["source"]),),
        ).fetchone() == source_revision
        assert connection.execute(
            """SELECT legacy_source_namespace_id,object_id FROM legacy_object_aliases
                 WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value=?""",
            (native_id_to_bytes(request.legacy_source_namespace_id), request.runtime_motif_id),
        ).fetchone() == source_alias
        assert connection.execute(
            "SELECT count(*) FROM legacy_object_aliases WHERE alias_kind='MOTIF_ID' AND alias_value=?",
            (request.runtime_motif_id,),
        ).fetchone()[0] == 2
        with pytest.raises(N0BaselineRefused, match="D1_N0_MOTIF_ALIAS_NAMESPACE_COLLAPSED"):
            require_d1_motif_alias_separation((replace(plan, motif_alias_namespace_id=plan.legacy_source_namespace_id),))
    finally:
        qualified.close()


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


def test_d1_formal_runner_refuses_before_marker_or_trace_contact_without_authority(tmp_path: Path) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    runner = FormalAdministrationRunner(repository_root=_ROOT, expected_repository_head=head)
    inputs = FrozenAdministrationInputs("a" * 64, "b" * 64, FROZEN_TOLERANCES.digest)
    calls: list[str] = []
    result_root = tmp_path / "formal-result"
    with pytest.raises(FormalAdministrationRefused, match="absent"):
        runner.run(authorization=None, inputs=inputs, protocol_sha256="a" * 64, fixture_sha256="b" * 64, verify_baselines_and_fixture=lambda: calls.append("verify"), contact_formal_trace=lambda: calls.append("contact"))
    assert calls == []
    authorization = FormalAdministrationAuthorization(
        "still-held", head, "a" * 64, "b" * 64, FROZEN_TOLERANCES.digest, str(result_root), False,
    )
    with pytest.raises(FormalAdministrationRefused, match="no explicit"):
        runner.run(authorization=authorization, inputs=inputs, protocol_sha256="a" * 64, fixture_sha256="b" * 64, verify_baselines_and_fixture=lambda: calls.append("verify"), contact_formal_trace=lambda: calls.append("contact"))
    assert calls == []
    assert not result_root.exists()
    assert not (tmp_path / ".still-held.administration-started.json").exists()
    runner.verify_frozen_inputs(inputs=inputs, protocol_sha256="a" * 64, fixture_sha256="b" * 64)
