"""Synthetic-only qualification for the 7G5D1H concrete D1 execution ports."""
from __future__ import annotations

import base64
import inspect
import subprocess
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pytest

from experiments.memory_substrate_d1_trace_replay_v1.formal import (
    FormalAdministrationAuthorization,
    FormalAdministrationRunner,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_administer import (
    _parser,
    build_formal_operator_plan,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_executor import (
    CHARACTER_SUBARM_STATUS,
    CORE_ARM_ORDER,
    CORE_FIXTURE_SHA256,
    CORE_PROTOCOL_SHA256,
    CORE_TOLERANCES_SHA256,
    CoreFormalAdministrationExecutor,
    CoreFrozenArm,
    CoreFrozenEvent,
    CoreFrozenFixture,
    CoreReplayEvidence,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_ports import (
    CoreNoWritePostWriteFacts,
    CoreD1SourceLocations,
    CoreFormalPortFailure,
    ConcreteCoreFormalExecutionPorts,
    QualifiedNativeArmSession,
    _facts_from_mapping,
    validate_frozen_core_input_contract,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_legacy_worker import _legacy_evidence
from experiments.memory_substrate_d1_trace_replay_v1.protocol import (
    D1ProtocolError,
    FrozenAdministrationInputs,
    sha256_value,
)
from experiments.memory_substrate_d1_trace_replay_v1.side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)


_ROOT = Path(__file__).resolve().parents[1]


def _request(fixture_id: str, *, text: str, step: int) -> dict[str, Any]:
    vector = np.zeros(384, dtype=np.float32)
    vector[10] = 1.0
    return {
        "text": text,
        "supplied_summary": text,
        "supplied_embedding_base64": base64.b64encode(vector.tobytes()).decode("ascii"),
        "supplied_embedding_encoding": "float32-le-c-384",
        "step": step,
        "scope": "private",
        "domain_id": "research",
    }


def _event(arm: str, ordinal: int, *, no_write: bool = False, reinforced: bool = False) -> CoreFrozenEvent:
    fixture_id = f"{arm}-{ordinal}"
    text = "" if no_write else ("same" if arm in {"M2_REINFORCE", "SEQUENTIAL"} and ordinal < 2 else fixture_id)
    request = _request(fixture_id, text=text, step=ordinal + 1)
    request["_request_sha256"] = sha256_value(request)
    return CoreFrozenEvent(
        fixture_id=fixture_id,
        kind="M5_NO_WRITE" if no_write else arm,
        request=request,
        storage_facts={"fixture_id": fixture_id, "summary": text},
        legacy_expected={"stored": not no_write, "reinforced": reinforced},
        qualification={},
    )


def _fixture() -> CoreFrozenFixture:
    arms = (
        CoreFrozenArm("M1_CREATE", "l1", "n1", (_event("M1_CREATE", 0),)),
        CoreFrozenArm("M2_REINFORCE", "l2", "n2", (_event("M2_REINFORCE", 0), _event("M2_REINFORCE", 1, reinforced=True))),
        CoreFrozenArm("M3_DISTINCT", "l3", "n3", (_event("M3_DISTINCT", 0), _event("M3_DISTINCT", 1))),
        CoreFrozenArm("M4_CONTRADICTION", "l4", "n4", (_event("M4_CONTRADICTION", 0), _event("M4_CONTRADICTION", 1))),
        CoreFrozenArm("M5_NO_WRITE", "l5", "n5", (_event("M5_NO_WRITE", 0, no_write=True),)),
        CoreFrozenArm("SEQUENTIAL", "l6", "n6", (_event("SEQUENTIAL", 0), _event("SEQUENTIAL", 1, reinforced=True), _event("SEQUENTIAL", 2), _event("SEQUENTIAL", 3))),
    )
    return CoreFrozenFixture(
        fixture_generation_head="35b6a3101190b3a75dcd404cbbbcb20881ce2cba",
        inputs=FrozenAdministrationInputs(CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256),
        arms=arms, l0_fingerprint_sha256=CORE_CHARACTER_FREE_L0_FINGERPRINT,
        side_store_observation_digest=CORE_SIDE_STORE_OBSERVATION_DIGEST,
    )


def _storage(request: Mapping[str, Any], *, stored: bool, reinforced: bool) -> dict[str, Any]:
    return {
        "stored": stored, "reinforced": reinforced, "compatible_eid": stored,
        "summary": request.get("summary", request.get("supplied_summary", "")), "memory_type": "episode",
        "memory_class": "core", "lifecycle": None if not stored else {"state": "ACTIVE", "authoritative": False},
        "governance": {"state": "UNKNOWN"}, "provenance": None,
        "raw_representation_bytes": request.get("supplied_embedding_base64", ""),
        "raw_representation_vector": [0.0] * 384, "motif_membership": [], "motif_geometry": [],
        "conflict": None, "strength": 1.0, "confidence": 1.0, "half_life_days": 1.0,
        "reinforcement_count": 1 if reinforced else 0,
    }


def _no_write_storage() -> dict[str, Any]:
    return {
        "stored": False, "reinforced": False, "compatible_eid": False,
        "conflict": None, "created_motif": None, "motif_membership": [], "motif_geometry": [],
    }


def _no_write_witness() -> dict[str, bool]:
    return {
        "router_not_invoked": True, "route_witness_absent": True,
        "durable_storage_unchanged": True, "stored_object_created": False,
    }


def _post_write() -> dict[str, Any]:
    return {
        "qualified_post_write_outputs": {"proposal_id": None},
        "deterministic_runtime_ordering": ["contradiction", "srg", "hivemind", "derived", "world", "proposal"],
    }


class _FakeWorker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.seen: set[str] = set()
        self.closed = False

    def request(self, command: str, **values: Any) -> Mapping[str, Any]:
        self.calls.append((command, values))
        if command == "replay_http":
            request = dict(values["request"])
            summary = str(request["supplied_summary"])
            stored = bool(request["text"])
            reinforced = stored and summary in self.seen
            self.seen.add(summary)
            storage = _no_write_storage() if not stored else _storage(request, stored=stored, reinforced=reinforced)
            return {"storage": storage, "post_write": _post_write(), "optional_feature_divergences": []}
        if command == "capture_durable_state":
            return {"writes": len(self.seen)}
        if command == "search_by_embedding":
            return {"ranking": [["1", 1.0]]}
        return {"ok": True}

    def close(self) -> None:
        self.closed = True


class _FakeNative:
    stores: dict[Path, int] = {}
    vectors: list[np.ndarray] = []
    router_calls = 0
    total_router_calls = 0

    def __init__(self, root: Path) -> None:
        self.root = root
        self.stores.setdefault(root, 0)

    def replay(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        self.router_calls += 1
        type(self).total_router_calls += 1
        summary = str(request["summary"])
        reinforced = summary == "same" and self.stores[self.root] > 0
        self.stores[self.root] += 1
        return CoreReplayEvidence(_storage(request, stored=True, reinforced=reinforced), _post_write(), native_structural_invariants=_structural())

    def replay_no_write(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        return CoreReplayEvidence(_no_write_storage(), _post_write(), native_structural_invariants=_no_write_witness())

    def capture_durable_state(self) -> Mapping[str, Any]:
        return {"writes": self.stores[self.root]}

    def compatibility_embedding_search(self, vector: np.ndarray):
        self.vectors.append(vector.copy())
        return (("1", 1.0),)

    def close(self) -> None:
        return None


def _structural() -> dict[str, bool]:
    return {
        "uuid_uniqueness": True, "correct_parentage": True, "revision_advancement": True,
        "current_revision_ownership": True, "operation_ownership": True, "idempotency": True,
        "retry_stability": True,
    }


def _ports(tmp_path: Path) -> tuple[ConcreteCoreFormalExecutionPorts, list[_FakeWorker]]:
    source_l0, source_n0 = tmp_path / "source-l0", tmp_path / "source-n0"
    source_l0.mkdir(parents=True)
    source_n0.mkdir()
    (source_n0 / "n0_core.db").write_bytes(b"synthetic")
    _FakeNative.stores = {}
    _FakeNative.vectors = []
    _FakeNative.router_calls = 0
    _FakeNative.total_router_calls = 0
    workers: list[_FakeWorker] = []

    def worker(_root: Path, _source: Path) -> _FakeWorker:
        item = _FakeWorker()
        workers.append(item)
        return item

    return ConcreteCoreFormalExecutionPorts(
        administration_work_root=tmp_path / "new-admin-work",
        source_locations=CoreD1SourceLocations(source_l0.resolve(), source_n0.resolve()),
        legacy_worker_factory=worker, native_session_factory=_FakeNative,
        legacy_source_verifier=lambda: {
            "l0_fingerprint_sha256": CORE_CHARACTER_FREE_L0_FINGERPRINT,
            "side_store_observation_digest": CORE_SIDE_STORE_OBSERVATION_DIGEST,
            "character_arm_absent": True,
        }, native_source_verifier=lambda: None,
    ), workers


def test_concrete_ports_advertise_qualified_environments_and_unique_roots(tmp_path: Path) -> None:
    ports, _ = _ports(tmp_path)
    assert (ports.legacy_environment, ports.native_environment) == ("torment", "torment-substrate")
    assert ports.legacy_normal_http_surface is True and ports.native_qualified_staging_only is True
    roots = [ports.allocate_arm_roots(arm) for arm in _fixture().arms]
    values = [value for roots_for_arm in roots for value in (roots_for_arm.legacy_root, roots_for_arm.native_root)]
    assert len(values) == len(set(values)) == 12
    assert all(not value.exists() for value in values)
    assert [item.legacy_root.parent.name for item in roots] == list(CORE_ARM_ORDER)


def test_preexisting_administration_root_and_root_reuse_are_refused(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    with pytest.raises(CoreFormalPortFailure, match="new"):
        ConcreteCoreFormalExecutionPorts(administration_work_root=occupied)
    ports, _ = _ports(tmp_path / "reuse")
    arm = _fixture().arms[0]
    ports.allocate_arm_roots(arm)
    with pytest.raises(CoreFormalPortFailure, match="exactly once"):
        ports.allocate_arm_roots(arm)


def test_synthetic_concrete_process_ports_preserve_http_facts_restarts_and_native_root(tmp_path: Path) -> None:
    ports, workers = _ports(tmp_path)
    arm = _fixture().arms[0]
    roots = ports.allocate_arm_roots(arm)
    legacy = ports.open_legacy(arm, roots.legacy_root)
    native = ports.open_native(arm, roots.native_root)
    request = arm.events[0].legacy_http_request()
    legacy.replay_http(request)
    legacy.restart_cleanly()
    reopened = ports.reopen_native(arm, roots.native_root)
    assert workers[0].calls[0] == ("replay_http", {"request": request})
    assert [name for name, _ in workers[0].calls].count("replay_http") == 1
    assert roots.native_root == reopened.root and (roots.native_root / "n0_core.db").is_file()
    vector = arm.events[0].query_vector()
    legacy.search_by_embedding(vector)
    reopened.compatibility_embedding_search(vector)
    assert np.array_equal(_FakeNative.vectors[-1], vector)
    legacy.close()


def test_native_input_refuses_selected_legacy_eid_and_has_no_memorygraph_fallback() -> None:
    event = CoreFrozenFixture.load().arms[0].events[0]
    facts = _facts_from_mapping(event.native_request())
    assert facts.fixture_id == event.native_request()["native_operation_key"]
    forbidden = dict(event.native_request())
    forbidden["selected_reinforcement_eid"] = 2
    with pytest.raises(CoreFormalPortFailure, match="forbidden legacy selection"):
        _facts_from_mapping(forbidden)
    assert "MemoryGraph" not in inspect.getsource(QualifiedNativeArmSession)
    assert "torment_service.fabric" not in inspect.getsource(__import__(
        "experiments.memory_substrate_d1_trace_replay_v1.formal_core_ports", fromlist=["*"]
    ))


def test_exact_frozen_m5_uses_no_write_contract_and_stored_parser_refuses_it() -> None:
    fixture = CoreFrozenFixture.load()
    m5 = next(event for arm in fixture.arms if arm.arm_id == "M5_NO_WRITE" for event in arm.events)
    facts = CoreNoWritePostWriteFacts.from_mapping(m5.native_request())
    context = facts.to_post_write_context()
    assert facts.evidence_operation_key == m5.native_request()["native_operation_key"]
    assert context.stored is False and context.eid is None
    assert not hasattr(facts, "governance") and not hasattr(facts, "provenance")
    with pytest.raises(CoreFormalPortFailure, match="malformed frozen storage facts"):
        _facts_from_mapping(m5.native_request())


def test_exact_frozen_input_precontact_validation_parses_all_twelve_without_ports(tmp_path: Path) -> None:
    fixture = CoreFrozenFixture.load()
    before = sorted(tmp_path.rglob("*"))
    validate_frozen_core_input_contract(fixture)
    assert len([event for arm in fixture.arms for event in arm.events]) == 12
    assert len([event for arm in fixture.arms if arm.arm_id == "SEQUENTIAL" for event in arm.events]) == 4
    assert sorted(tmp_path.rglob("*")) == before


def test_legacy_no_write_evidence_never_labels_the_supplied_embedding_as_persisted(tmp_path: Path) -> None:
    evidence = _legacy_evidence(
        request={"supplied_embedding_base64": "not-a-persisted-representation"},
        response={"stored": False, "reinforced": False, "eid": None, "motifs": [], "proposal_id": None},
        private_root=tmp_path / "no-access", motif_path=tmp_path / "no-access" / "motifs.json",
    )
    assert evidence["storage"] == _no_write_storage()
    assert "raw_representation_bytes" not in evidence["storage"]
    assert "raw_representation_vector" not in evidence["storage"]


def test_legacy_worker_is_bound_to_the_normal_service_and_arm_data_directory() -> None:
    worker = (_ROOT / "experiments" / "memory_substrate_d1_trace_replay_v1" / "formal_core_legacy_worker.py").read_text(encoding="utf-8")
    capture = (_ROOT / "experiments" / "memory_substrate_d1_trace_replay_v1" / "legacy_fixture_capture.py").read_text(encoding="utf-8")
    assert "_start_service(self._root" in worker and "_stop_service(self._service)" in worker
    assert '[sys.executable, "-m", "torment_service"]' in capture
    assert 'env["TORMENT_DATA_DIR"] = str(data_root)' in capture


def test_synthetic_runner_executor_concrete_ports_m5_uses_no_router_and_no_retry(tmp_path: Path) -> None:
    ports, workers = _ports(tmp_path)
    executor = CoreFormalAdministrationExecutor(fixture=_fixture(), ports=ports)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    runner = FormalAdministrationRunner(repository_root=_ROOT, expected_repository_head=head)
    result_root = tmp_path / "synthetic-result"
    authorization = FormalAdministrationAuthorization(
        "synthetic-ports", head, CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256,
        CORE_TOLERANCES_SHA256, str(result_root), True,
    )
    result = runner.run(
        authorization=authorization, inputs=executor.fixture.inputs,
        protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256,
        verify_baselines_and_fixture=ports.verify_frozen_sources,
        contact_formal_trace=lambda: executor.execute(administration_id=authorization.administration_id),
    )
    assert result.harness_validity == "VALID"
    assert _FakeNative.total_router_calls == 11
    m5_worker = workers[4]
    assert [name for name, _ in m5_worker.calls].count("replay_http") == 1
    assert (result_root.parent / ".synthetic-ports.administration-started.json").is_file()
    assert (result_root / "result.json").is_file()
    assert result.character == {"CHARACTER_ARM_ADMINISTERED": "NO", "CHARACTER_SUBARM_STATUS": CHARACTER_SUBARM_STATUS}


def test_worker_failure_propagates_once_without_automatic_retry(tmp_path: Path) -> None:
    ports, _ = _ports(tmp_path)
    arm = _fixture().arms[0]
    roots = ports.allocate_arm_roots(arm)

    class FailingWorker(_FakeWorker):
        def request(self, command: str, **values: Any) -> Mapping[str, Any]:
            self.calls.append((command, values))
            raise RuntimeError("synthetic worker failure")

    ports._legacy_worker_factory = lambda _root, _source: FailingWorker()  # type: ignore[attr-defined]
    session = ports.open_legacy(arm, roots.legacy_root)
    with pytest.raises(RuntimeError, match="synthetic worker failure"):
        session.replay_http(arm.events[0].legacy_http_request())


def test_native_open_failure_releases_the_already_opened_legacy_service_once(tmp_path: Path) -> None:
    ports, workers = _ports(tmp_path)
    ports._native_session_factory = lambda _root: (_ for _ in ()).throw(RuntimeError("native open failure"))  # type: ignore[attr-defined]
    executor = CoreFormalAdministrationExecutor(fixture=_fixture(), ports=ports)
    with pytest.raises(RuntimeError, match="native open failure"):
        executor.execute(administration_id="synthetic")
    assert len(workers) == 1 and workers[0].closed is True


def test_operator_surface_requires_all_authority_values_and_never_touches_real_result_root(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _parser().parse_args([])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    with pytest.raises(Exception, match="current checkout"):
        build_formal_operator_plan(
            administration_id="synthetic", expected_repository_head="0" * 40,
            protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256,
            tolerances_sha256=CORE_TOLERANCES_SHA256,
            administration_work_root=tmp_path / "wrong-head-work", result_root=tmp_path / "wrong-head-result", repository_root=_ROOT,
        )
    with pytest.raises(Exception, match="hashes"):
        build_formal_operator_plan(
            administration_id="synthetic", expected_repository_head=head,
            protocol_sha256="0" * 64, fixture_sha256="0" * 64, tolerances_sha256="0" * 64,
            administration_work_root=tmp_path / "work", result_root=tmp_path / "result", repository_root=_ROOT,
        )
    work, result = tmp_path / "operator-work", tmp_path / "operator-result"
    plan = build_formal_operator_plan(
        administration_id="synthetic", expected_repository_head=head,
        protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256,
        tolerances_sha256=CORE_TOLERANCES_SHA256,
        administration_work_root=work, result_root=result, repository_root=_ROOT,
    )
    assert plan.authorization.authorized is True
    assert not work.exists() and not result.exists()


def test_operator_precontact_validation_runs_before_any_future_marker_or_port_contact(tmp_path: Path) -> None:
    calls: list[str] = []

    class ReadOnlyPorts:
        legacy_environment = "torment"
        native_environment = "torment-substrate"
        legacy_normal_http_surface = True
        native_qualified_staging_only = True

        def __init__(self, **_values: Any) -> None:
            return None

        def verify_frozen_sources(self) -> None:
            calls.append("read-only-source-verification")

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    work, result = tmp_path / "precontact-work", tmp_path / "precontact-result"
    plan = build_formal_operator_plan(
        administration_id="synthetic-precontact", expected_repository_head=head,
        protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256,
        tolerances_sha256=CORE_TOLERANCES_SHA256, administration_work_root=work,
        result_root=result, repository_root=_ROOT, ports_factory=ReadOnlyPorts,
    )
    plan.verify_baselines_and_fixture()
    assert calls == ["read-only-source-verification"]
    assert not work.exists() and not result.exists()


def test_old_character_fixture_is_not_an_operator_input(tmp_path: Path) -> None:
    with pytest.raises(D1ProtocolError, match="Character-bearing"):
        CoreFrozenFixture.load(
            _ROOT / "experiments" / "memory_substrate_d1_trace_replay_v1" / "fixtures" / "concrete_legacy_only_fixture_set_20260831.json"
        )
