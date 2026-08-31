"""Synthetic-only qualification for the 7G5D1G CORE_ONLY executor glue."""
from __future__ import annotations

import base64
import inspect
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

import numpy as np
import pytest

from experiments.memory_substrate_d1_trace_replay_v1.compare import compare_scalar
from experiments.memory_substrate_d1_trace_replay_v1.formal import (
    FormalAdministrationAuthorization,
    FormalAdministrationRefused,
    FormalAdministrationRunner,
    FormalResultSchema,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_executor import (
    CHARACTER_SUBARM_STATUS,
    CORE_ARM_ORDER,
    CORE_FIXTURE_SHA256,
    CORE_PROTOCOL_SHA256,
    CORE_TOLERANCES_SHA256,
    CoreArmRoots,
    CoreFormalAdministrationExecutor,
    CoreFrozenArm,
    CoreFrozenEvent,
    CoreFrozenFixture,
    CoreReplayEvidence,
    require_core_formal_inputs,
)
from experiments.memory_substrate_d1_trace_replay_v1.protocol import (
    ComparisonTolerances,
    D1ProtocolError,
    FROZEN_TOLERANCES,
    FrozenAdministrationInputs,
    sha256_value,
)
from experiments.memory_substrate_d1_trace_replay_v1.side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)


_ROOT = Path(__file__).resolve().parents[1]
_STRUCTURAL = {
    "uuid_uniqueness": True,
    "correct_parentage": True,
    "revision_advancement": True,
    "current_revision_ownership": True,
    "operation_ownership": True,
    "idempotency": True,
    "retry_stability": True,
}


def _request(fixture_id: str) -> dict[str, Any]:
    vector = np.zeros(384, dtype=np.float32)
    vector[10] = 1.0
    return {
        "text": f"synthetic {fixture_id}",
        "supplied_summary": f"synthetic {fixture_id}",
        "supplied_embedding_base64": base64.b64encode(vector.tobytes()).decode("ascii"),
        "supplied_embedding_encoding": "float32-le-c-384",
    }


def _event(arm_id: str, ordinal: int, *, no_write: bool = False, reinforced: bool = False) -> CoreFrozenEvent:
    fixture_id = f"{arm_id}-{ordinal}"
    request = _request(fixture_id)
    request["_request_sha256"] = sha256_value(request)
    return CoreFrozenEvent(
        fixture_id=fixture_id,
        kind="M5_NO_WRITE" if no_write else arm_id,
        request=request,
        storage_facts={
            "fixture_id": fixture_id,
            "native_operation_key": f"D1:TEST:{fixture_id}",
            "summary": request["supplied_summary"],
        },
        legacy_expected={"stored": not no_write, "reinforced": reinforced},
        qualification={},
    )


def _fixture(*, include_character: bool = False) -> CoreFrozenFixture:
    arms = (
        CoreFrozenArm("M1_CREATE", "legacy-m1", "native-m1", (_event("M1_CREATE", 0),)),
        CoreFrozenArm("M2_REINFORCE", "legacy-m2", "native-m2", (_event("M2_REINFORCE", 0), _event("M2_REINFORCE", 1, reinforced=True))),
        CoreFrozenArm("M3_DISTINCT", "legacy-m3", "native-m3", (_event("M3_DISTINCT", 0), _event("M3_DISTINCT", 1))),
        CoreFrozenArm("M4_CONTRADICTION", "legacy-m4", "native-m4", (_event("M4_CONTRADICTION", 0), _event("M4_CONTRADICTION", 1))),
        CoreFrozenArm("M5_NO_WRITE", "legacy-m5", "native-m5", (_event("M5_NO_WRITE", 0, no_write=True),)),
        CoreFrozenArm("SEQUENTIAL", "legacy-seq", "native-seq", (_event("SEQUENTIAL", 0), _event("SEQUENTIAL", 1, reinforced=True), _event("SEQUENTIAL", 2), _event("SEQUENTIAL", 3))),
    )
    if include_character:
        arms = (*arms, CoreFrozenArm("CHARACTER_SUBARM", "legacy-character", "native-character", (_event("CHARACTER_SUBARM", 0),)))
    return CoreFrozenFixture(
        fixture_generation_head="35b6a3101190b3a75dcd404cbbbcb20881ce2cba",
        inputs=FrozenAdministrationInputs(CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256),
        arms=arms,
        l0_fingerprint_sha256=CORE_CHARACTER_FREE_L0_FINGERPRINT,
        side_store_observation_digest=CORE_SIDE_STORE_OBSERVATION_DIGEST,
    )


def _storage(event: CoreFrozenEvent, *, mismatch: bool = False) -> dict[str, Any]:
    value = {
        "stored": event.legacy_expected["stored"],
        "reinforced": event.legacy_expected["reinforced"],
        "compatible_eid": True,
        "summary": event.request["supplied_summary"],
        "memory_type": "episode",
        "memory_class": "core",
        "lifecycle": {"status": "ACTIVE"},
        "governance": {"protected": False},
        "provenance": {"schema_version": "1.0"},
        "raw_representation_bytes": event.request["supplied_embedding_base64"],
        "raw_representation_vector": [0.0] * 384,
        "motif_membership": ["synthetic-motif"],
        "motif_geometry": {"radius": 0.0},
        "conflict": None,
        "strength": 0.9,
        "confidence": 0.8,
        "half_life_days": 12.0,
        "reinforcement_count": 1 if event.legacy_expected["reinforced"] else 0,
    }
    if mismatch:
        value["strength"] = 0.7
    return value


class _LegacySession:
    def __init__(self, ports: "_Ports", arm: CoreFrozenArm) -> None:
        self._ports, self._arm, self._cursor = ports, arm, 0

    def replay_http(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        event = self._arm.events[self._cursor]
        self._cursor += 1
        self._ports.legacy_requests.append(dict(request))
        return CoreReplayEvidence(_storage(event), _post_write())

    def capture_durable_state(self) -> Mapping[str, Any]:
        return {"legacy": self._cursor}

    def restart_cleanly(self) -> None:
        self._ports.legacy_restarts += 1

    def search_by_embedding(self, vector: np.ndarray):
        self._ports.legacy_queries.append(vector)
        return (("synthetic", 1.0),)

    def close(self) -> None:
        self._ports.legacy_closes += 1


class _NativeSession:
    def __init__(self, ports: "_Ports", arm: CoreFrozenArm) -> None:
        self._ports, self._arm, self._cursor, self._durable = ports, arm, 0, 0

    def replay(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        event = self._arm.events[self._cursor]
        self._cursor += 1
        self._durable += 1
        self._ports.router_calls += 1
        self._ports.native_requests.append(dict(request))
        if self._ports.raise_native:
            raise RuntimeError("synthetic native refusal")
        return CoreReplayEvidence(_storage(event, mismatch=self._ports.mismatch), _post_write(), ({"kind": "bridge-observation"},), _STRUCTURAL)

    def replay_no_write(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        event = self._arm.events[self._cursor]
        self._cursor += 1
        self._ports.no_write_calls += 1
        self._ports.native_requests.append(dict(request))
        if self._ports.mutate_m5:
            self._durable += 1
        return CoreReplayEvidence(_storage(event, mismatch=self._ports.mismatch), _post_write(), (), _STRUCTURAL)

    def capture_durable_state(self) -> Mapping[str, Any]:
        return {"native": self._durable}

    def compatibility_embedding_search(self, vector: np.ndarray):
        self._ports.native_queries.append(vector)
        return (("synthetic", 1.0),)

    def close(self) -> None:
        self._ports.native_closes += 1


def _post_write() -> dict[str, Any]:
    return {"qualified_post_write_outputs": {"derived": "inert"}, "deterministic_runtime_ordering": ["one"]}


class _Ports:
    legacy_environment = "torment"
    native_environment = "torment-substrate"
    legacy_normal_http_surface = True
    native_qualified_staging_only = True

    def __init__(self, tmp_path: Path, *, same_roots: bool = False, mutate_m5: bool = False, mismatch: bool = False, raise_native: bool = False) -> None:
        self._tmp_path, self._same_roots = tmp_path, same_roots
        self.mutate_m5, self.mismatch, self.raise_native = mutate_m5, mismatch, raise_native
        self.legacy_requests: list[dict[str, Any]] = []
        self.native_requests: list[dict[str, Any]] = []
        self.legacy_queries: list[np.ndarray] = []
        self.native_queries: list[np.ndarray] = []
        self.legacy_restarts = self.no_write_calls = self.router_calls = self.legacy_closes = self.native_closes = 0
        self.reopened = 0

    def allocate_arm_roots(self, arm: CoreFrozenArm) -> CoreArmRoots:
        legacy = self._tmp_path / "legacy" / arm.arm_id
        native = legacy if self._same_roots else self._tmp_path / "native" / arm.arm_id
        return CoreArmRoots(legacy.resolve(), native.resolve())

    def open_legacy(self, arm: CoreFrozenArm, root: Path) -> _LegacySession:
        return _LegacySession(self, arm)

    def open_native(self, arm: CoreFrozenArm, root: Path) -> _NativeSession:
        return _NativeSession(self, arm)

    def reopen_native(self, arm: CoreFrozenArm, root: Path) -> _NativeSession:
        self.reopened += 1
        return _NativeSession(self, arm)


def _executor(tmp_path: Path, **kwargs: Any) -> tuple[CoreFormalAdministrationExecutor, _Ports]:
    ports = _Ports(tmp_path, **kwargs)
    return CoreFormalAdministrationExecutor(fixture=_fixture(), ports=ports), ports


def test_core_only_inventory_hashes_and_character_boundary_are_exact(tmp_path: Path) -> None:
    require_core_formal_inputs(FrozenAdministrationInputs(CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256))
    with pytest.raises(D1ProtocolError, match="non-core or Character"):
        require_core_formal_inputs(FrozenAdministrationInputs("55b715663e2ebadedfbd7579f52ce68e9a90815573c947a71760a8e41f096a1e", "b12704f2158d9667c3bd26a0cc30e41ab7ae686213115588f40727034cdcc26d", CORE_TOLERANCES_SHA256))
    with pytest.raises(D1ProtocolError, match="selected CORE_ONLY"):
        CoreFormalAdministrationExecutor(fixture=_fixture(include_character=True), ports=_Ports(tmp_path))
    executor, _ = _executor(tmp_path)
    assert tuple(arm.arm_id for arm in executor.fixture.arms) == CORE_ARM_ORDER
    assert len(executor.fixture.arms) == 6


def test_executor_forwards_exact_ordered_requests_without_native_legacy_target(tmp_path: Path) -> None:
    executor, ports = _executor(tmp_path)
    result = executor.execute(administration_id="synthetic")
    expected = [event.legacy_http_request() for arm in executor.fixture.arms for event in arm.events]
    assert ports.legacy_requests == expected
    assert [item["fixture_id"] for item in ports.native_requests] == [event.fixture_id for arm in executor.fixture.arms for event in arm.events]
    assert not any({"eid", "reinforcement_target_eid", "legacy_response"}.intersection(item) for item in ports.native_requests)
    assert result.m5["event_order"] == ["M5_NO_WRITE-0"]


def test_m5_does_not_route_and_refuses_durable_mutation(tmp_path: Path) -> None:
    executor, ports = _executor(tmp_path)
    executor.execute(administration_id="synthetic")
    assert ports.no_write_calls == 1
    assert ports.router_calls == 11
    with pytest.raises(D1ProtocolError, match="NO_WRITE changed"):
        _executor(tmp_path / "mutation", mutate_m5=True)[0].execute(administration_id="synthetic")


def test_executor_keeps_mismatch_and_optional_divergence_separate(tmp_path: Path) -> None:
    result = _executor(tmp_path, mismatch=True)[0].execute(administration_id="synthetic")
    assert result.harness_validity == "VALID"
    assert result.storage_substrate_verdict == "STORAGE_SUBSTRATE_DEFECT"
    assert result.qualified_post_write_verdict == "QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE"
    assert result.m1["storage_differences"]
    assert result.optional_feature_divergences and result.optional_feature_divergences[0]["kind"] == "bridge-observation"


def test_roots_restart_retrieval_and_character_disposition_are_bound(tmp_path: Path) -> None:
    executor, ports = _executor(tmp_path)
    result = executor.execute(administration_id="synthetic")
    assert ports.legacy_restarts == 6 and ports.reopened == 6
    assert all(np.array_equal(left, right) for left, right in zip(ports.legacy_queries, ports.native_queries, strict=True))
    assert result.character == {
        "CHARACTER_ARM_ADMINISTERED": "NO",
        "CHARACTER_SUBARM_STATUS": CHARACTER_SUBARM_STATUS,
    }
    with pytest.raises(D1ProtocolError, match="separate absolute"):
        _executor(tmp_path / "same", same_roots=True)[0].execute(administration_id="synthetic")


def test_executor_propagates_without_retry_and_has_no_graph_fallback(tmp_path: Path) -> None:
    executor, ports = _executor(tmp_path, raise_native=True)
    with pytest.raises(RuntimeError, match="native refusal"):
        executor.execute(administration_id="synthetic")
    assert len(ports.native_requests) == 1
    assert "MemoryGraph" not in inspect.getsource(CoreFormalAdministrationExecutor)
    with pytest.raises(D1ProtocolError, match="immutable"):
        compare_scalar(1.0, 1.0, field="strength", tolerances=ComparisonTolerances(1e-5, 1e-7, 1e-6, 1e-6, 1e-6, 1e-6))


def test_loader_refuses_a_temp_character_fixture_name(tmp_path: Path) -> None:
    old = tmp_path / "concrete_legacy_only_fixture_set_20260831.json"
    old.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(D1ProtocolError, match="Character-bearing"):
        CoreFrozenFixture.load(old)


def test_formal_runner_calls_mock_executor_once_after_marker_and_seals_failures(tmp_path: Path) -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=_ROOT, check=True, capture_output=True, text=True).stdout.strip()
    inputs = FrozenAdministrationInputs(CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256)
    runner = FormalAdministrationRunner(repository_root=_ROOT, expected_repository_head=head)
    result_root = tmp_path / "synthetic-result"
    authorization = FormalAdministrationAuthorization("synthetic", head, CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256, str(result_root), True)
    calls: list[str] = []

    class MockExecutor:
        def execute(self, *, administration_id: str) -> FormalResultSchema:
            assert (tmp_path / ".synthetic.administration-started.json").is_file()
            calls.append(administration_id)
            return FormalResultSchema(administration_id, harness_validity="VALID")

    result = runner.run(authorization=authorization, inputs=inputs, protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256, verify_baselines_and_fixture=lambda: None, contact_formal_trace=lambda: MockExecutor().execute(administration_id=authorization.administration_id))
    assert result.harness_validity == "VALID" and calls == ["synthetic"]
    assert (result_root / "result.json").is_file()

    failure_root = tmp_path / "synthetic-failure"
    failure = FormalAdministrationAuthorization("failure", head, CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256, str(failure_root), True)
    failure_calls = 0

    def fail_once() -> FormalResultSchema:
        nonlocal failure_calls
        failure_calls += 1
        raise RuntimeError("synthetic executor failure")

    with pytest.raises(RuntimeError, match="synthetic executor failure"):
        runner.run(authorization=failure, inputs=inputs, protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256, verify_baselines_and_fixture=lambda: None, contact_formal_trace=fail_once)
    assert json.loads((failure_root / "result.json").read_text(encoding="utf-8"))["harness_validity"] == "EXPERIMENT_HARNESS_FAILURE"
    with pytest.raises(FormalAdministrationRefused, match="already used"):
        runner.run(authorization=failure, inputs=inputs, protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256, verify_baselines_and_fixture=lambda: None, contact_formal_trace=fail_once)
    assert failure_calls == 1
