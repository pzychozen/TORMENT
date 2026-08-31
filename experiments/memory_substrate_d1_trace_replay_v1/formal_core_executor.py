"""CORE_ONLY D1 formal-trace callback glue.

This module deliberately has no command-line entry point and does not create
an authorization, marker, or result root.  A future caller supplies the
already-authorized callback to ``FormalAdministrationRunner``.  The executor
only loads immutable evidence, binds six isolated arm roots, invokes the
provided legacy/native experiment ports once, and returns one result schema.
"""
from __future__ import annotations

import base64
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

import numpy as np

from .compare import (
    ComparisonDifference,
    ComparisonResult,
    compare_exact_fields,
    compare_rankings,
    compare_scalar,
    compare_vector,
    validate_native_no_write_structure,
    validate_native_structure,
)
from .fixture_qualification import D1ReplayProfile, ReplayEventRole
from .formal import FormalResultSchema
from .protocol import D1ProtocolError, FROZEN_TOLERANCES, FrozenAdministrationInputs, sha256_value
from .side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)


CORE_FIXTURE_FILENAME = "concrete_core_legacy_only_fixture_set_20260831.json"
CHARACTER_FIXTURE_FILENAME = "concrete_legacy_only_fixture_set_20260831.json"
CORE_FIXTURE_GENERATION_HEAD = "35b6a3101190b3a75dcd404cbbbcb20881ce2cba"
CORE_PROTOCOL_SHA256 = "4d3e7136735b1fb52b87521b397885d33682402208e4d966bd54ac9f458352b4"
CORE_FIXTURE_SHA256 = "dcd32c4c5ed0778d7972d757310da4d090fae2574f145e9d298a7933bc03a580"
CORE_TOLERANCES_SHA256 = "f98749b86ec4fcc78c97bdcb85167a742558fed66b3d7b1ea690dfccf6950bec"
CHARACTER_SUBARM_STATUS = "DEFERRED_PENDING_PROVENANCE_VOCABULARY"

CORE_ARM_ORDER = (
    "M1_CREATE",
    "M2_REINFORCE",
    "M3_DISTINCT",
    "M4_CONTRADICTION",
    "M5_NO_WRITE",
    "SEQUENTIAL",
)
_ARM_EVENT_ROLES = {
    "M1_CREATE": (ReplayEventRole.CREATE.value,),
    "M2_REINFORCE": (ReplayEventRole.CREATE.value, ReplayEventRole.REINFORCE.value),
    "M3_DISTINCT": (ReplayEventRole.CREATE.value, ReplayEventRole.DISTINCT.value),
    "M4_CONTRADICTION": (ReplayEventRole.CREATE.value, ReplayEventRole.CONTRADICTION.value),
    "M5_NO_WRITE": (ReplayEventRole.NO_WRITE.value,),
    "SEQUENTIAL": (
        ReplayEventRole.CREATE.value,
        ReplayEventRole.REINFORCE.value,
        ReplayEventRole.DISTINCT.value,
        ReplayEventRole.CONTRADICTION.value,
    ),
}
_STORAGE_EXACT_FIELDS = (
    "stored",
    "reinforced",
    "compatible_eid",
    "summary",
    "memory_type",
    "memory_class",
    "lifecycle",
    "governance",
    "provenance",
    "raw_representation_bytes",
    "motif_membership",
    "motif_geometry",
    "conflict",
)
_STORAGE_SCALAR_FIELDS = ("strength", "confidence", "half_life_days", "reinforcement_count")
_POST_WRITE_EXACT_FIELDS = ("qualified_post_write_outputs", "deterministic_runtime_ordering")
_NO_WRITE_STORAGE_FIELDS = (
    "stored", "reinforced", "compatible_eid", "conflict", "created_motif", "motif_membership", "motif_geometry",
)
_NO_WRITE_STORAGE_EXPECTED = {
    "stored": False,
    "reinforced": False,
    "compatible_eid": False,
    "conflict": None,
    "created_motif": None,
    "motif_membership": [],
    "motif_geometry": [],
}
_FORBIDDEN_NATIVE_FIELDS = {
    "eid",
    "legacy_eid",
    "legacy_response",
    "legacy_only_observed_outcome",
    "reinforcement_target_eid",
    "legacy_reinforcement_target_eid",
    "selected_reinforcement_eid",
}


@dataclass(frozen=True)
class CoreFrozenEvent:
    fixture_id: str
    kind: str
    request: Mapping[str, Any]
    storage_facts: Mapping[str, Any]
    legacy_expected: Mapping[str, Any]
    qualification: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (self.fixture_id, self.kind)):
            raise D1ProtocolError("core frozen event requires fixture identity and kind")
        request = dict(self.request)
        request_sha256 = request.pop("_request_sha256", None)
        if not isinstance(request_sha256, str) or sha256_value(request) != request_sha256:
            raise D1ProtocolError("core frozen request bytes are internally inconsistent")
        forbidden = _FORBIDDEN_NATIVE_FIELDS.intersection(self.storage_facts)
        if forbidden:
            raise D1ProtocolError(f"core native input contains legacy selection data: {sorted(forbidden)}")

    @property
    def is_no_write(self) -> bool:
        return self.kind == "M5_NO_WRITE" and self.legacy_expected.get("stored") is False

    def legacy_http_request(self) -> Mapping[str, Any]:
        """The exact frozen request object for the ordinary legacy HTTP surface."""
        request = dict(self.request)
        request.pop("_request_sha256", None)
        return request

    def native_request(self) -> Mapping[str, Any]:
        """Storage-facing facts only; it contains no legacy outcome or selected EID."""
        return dict(self.storage_facts)

    def query_vector(self) -> np.ndarray:
        embedding = self.request.get("supplied_embedding_base64")
        encoding = self.request.get("supplied_embedding_encoding")
        if encoding != "float32-le-c-384" or not isinstance(embedding, str):
            raise D1ProtocolError("core retrieval characterization requires the frozen float32 query vector")
        vector = np.frombuffer(base64.b64decode(embedding), dtype=np.float32).copy()
        if vector.shape != (384,) or not np.isfinite(vector).all():
            raise D1ProtocolError("core retrieval characterization query vector is invalid")
        vector.setflags(write=False)
        return vector


@dataclass(frozen=True)
class CoreFrozenArm:
    arm_id: str
    legacy_clone_id: str
    native_clone_id: str
    events: tuple[CoreFrozenEvent, ...]


@dataclass(frozen=True)
class CoreFrozenFixture:
    fixture_generation_head: str
    inputs: FrozenAdministrationInputs
    arms: tuple[CoreFrozenArm, ...]
    l0_fingerprint_sha256: str
    side_store_observation_digest: str

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CoreFrozenFixture":
        source = Path(path) if path is not None else Path(__file__).with_name("fixtures") / CORE_FIXTURE_FILENAME
        if source.name == CHARACTER_FIXTURE_FILENAME:
            raise D1ProtocolError("the Character-bearing concrete fixture is not valid for CORE_ONLY administration")
        if source.name != CORE_FIXTURE_FILENAME or not source.is_file():
            raise D1ProtocolError("CORE_ONLY administration requires only the named core concrete fixture")
        try:
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise D1ProtocolError("core concrete fixture is unreadable") from exc
        if not isinstance(document, dict) or not isinstance(document.get("binding"), dict):
            raise D1ProtocolError("core concrete fixture has no binding object")
        binding = document["binding"]
        inputs_source = document.get("administration_inputs")
        if not isinstance(inputs_source, dict):
            raise D1ProtocolError("core concrete fixture has no frozen administration inputs")
        inputs = FrozenAdministrationInputs(**inputs_source)
        require_core_formal_inputs(inputs)
        if sha256_value(binding) != inputs.fixture_sha256:
            raise D1ProtocolError("core concrete fixture binding bytes do not match its frozen hash")
        inputs.verify(protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256)
        if (
            binding.get("profile") != D1ReplayProfile.CORE_ONLY.value
            or binding.get("character_arm_administered") is not False
            or binding.get("character_subarm_status") != CHARACTER_SUBARM_STATUS
            or binding.get("l0_fingerprint_sha256") != CORE_CHARACTER_FREE_L0_FINGERPRINT
            or binding.get("side_store_observation_digest") != CORE_SIDE_STORE_OBSERVATION_DIGEST
            or binding.get("native_formal_event_count") != 0
        ):
            raise D1ProtocolError("core concrete fixture violates the fixed CORE_ONLY administration boundary")
        generation_head = binding.get("expected_repository_head")
        if generation_head != CORE_FIXTURE_GENERATION_HEAD:
            raise D1ProtocolError("core fixture generation witness changed")
        fixture_set = binding.get("fixture_set")
        replay_plan = binding.get("replay_plan")
        requests = binding.get("requests")
        if not isinstance(fixture_set, dict) or not isinstance(replay_plan, dict) or not isinstance(requests, list):
            raise D1ProtocolError("core concrete fixture replay material is malformed")
        if fixture_set.get("profile") != D1ReplayProfile.CORE_ONLY.value or replay_plan.get("profile") != D1ReplayProfile.CORE_ONLY.value:
            raise D1ProtocolError("core concrete fixture does not explicitly select CORE_ONLY")
        if replay_plan.get("character_arm") is not None:
            raise D1ProtocolError("CORE_ONLY administration forbids a Character replay arm")
        request_by_id: dict[str, Mapping[str, Any]] = {}
        for item in requests:
            if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str) or not isinstance(item[1], dict):
                raise D1ProtocolError("core concrete fixture request material is malformed")
            if item[0] in request_by_id:
                raise D1ProtocolError("core concrete fixture repeats a request fixture ID")
            request_by_id[item[0]] = item[1]
        event_by_id: dict[str, Mapping[str, Any]] = {}
        for event in fixture_set.get("fixtures", []):
            if not isinstance(event, dict) or not isinstance(event.get("fixture_id"), str):
                raise D1ProtocolError("core concrete fixture event inventory is malformed")
            event_by_id[event["fixture_id"]] = event
        if set(event_by_id) != set(request_by_id) or any(event.get("kind") == "CHARACTER_SUBARM" for event in event_by_id.values()):
            raise D1ProtocolError("CORE_ONLY fixture inventory may not omit, duplicate, or include Character events")
        plan_by_id: dict[str, Mapping[str, Any]] = {}
        arms_source = [*replay_plan.get("micro_arms", ()), replay_plan.get("sequential_arm")]
        if len(arms_source) != len(CORE_ARM_ORDER) or any(not isinstance(item, dict) for item in arms_source):
            raise D1ProtocolError("CORE_ONLY replay plan must contain exactly six arms")
        for arm in arms_source:
            arm_id = arm.get("arm_id")
            if not isinstance(arm_id, str) or arm_id in plan_by_id:
                raise D1ProtocolError("CORE_ONLY replay plan has an invalid arm inventory")
            plan_by_id[arm_id] = arm
        if tuple(plan_by_id) != CORE_ARM_ORDER:
            raise D1ProtocolError("CORE_ONLY replay plan order or inventory changed")
        assigned_ids = [fixture_id for arm_id in CORE_ARM_ORDER for fixture_id in plan_by_id[arm_id].get("fixture_ids", ())]
        if Counter(assigned_ids) != Counter(request_by_id.keys()):
            raise D1ProtocolError("CORE_ONLY replay plan must assign every fixture exactly once")
        arms: list[CoreFrozenArm] = []
        for arm_id in CORE_ARM_ORDER:
            arm = plan_by_id[arm_id]
            fixture_ids = tuple(arm.get("fixture_ids", ()))
            roles = tuple(arm.get("event_roles", ()))
            if roles != _ARM_EVENT_ROLES[arm_id] or not all(isinstance(item, str) for item in fixture_ids):
                raise D1ProtocolError(f"CORE_ONLY {arm_id} event ordering is not frozen")
            events: list[CoreFrozenEvent] = []
            for fixture_id in fixture_ids:
                event = event_by_id[fixture_id]
                material = request_by_id[fixture_id]
                request = material.get("request")
                storage_facts = material.get("storage_facts")
                legacy_expected = material.get("legacy_only_observed_outcome")
                qualification = material.get("qualification")
                if not all(isinstance(value, dict) for value in (request, storage_facts, legacy_expected, qualification)):
                    raise D1ProtocolError("core frozen event lacks exact request or storage-facing facts")
                frozen_request = dict(request)
                request_sha256 = event.get("request_sha256")
                if not isinstance(request_sha256, str) or sha256_value(frozen_request) != request_sha256:
                    raise D1ProtocolError("core frozen request SHA256 differs from the sealed fixture")
                frozen_request["_request_sha256"] = request_sha256
                events.append(CoreFrozenEvent(
                    fixture_id=fixture_id,
                    kind=str(event.get("kind", "")),
                    request=frozen_request,
                    storage_facts=dict(storage_facts),
                    legacy_expected=dict(legacy_expected),
                    qualification=dict(qualification),
                ))
            arms.append(CoreFrozenArm(
                arm_id=arm_id,
                legacy_clone_id=str(arm.get("legacy_clone_id", "")),
                native_clone_id=str(arm.get("native_clone_id", "")),
                events=tuple(events),
            ))
        clone_ids = [value for arm in arms for value in (arm.legacy_clone_id, arm.native_clone_id)]
        if any(not value for value in clone_ids) or len(clone_ids) != len(set(clone_ids)):
            raise D1ProtocolError("CORE_ONLY replay requires unique legacy and native clone identities")
        return cls(generation_head, inputs, tuple(arms), CORE_CHARACTER_FREE_L0_FINGERPRINT, CORE_SIDE_STORE_OBSERVATION_DIGEST)


@dataclass(frozen=True)
class CoreArmRoots:
    legacy_root: Path
    native_root: Path

    def __post_init__(self) -> None:
        if self.legacy_root == self.native_root or not self.legacy_root.is_absolute() or not self.native_root.is_absolute():
            raise D1ProtocolError("each CORE_ONLY arm requires separate absolute legacy and native roots")


@dataclass(frozen=True)
class CoreReplayEvidence:
    storage: Mapping[str, Any]
    post_write: Mapping[str, Any]
    optional_feature_divergences: tuple[Mapping[str, Any], ...] = ()
    native_structural_invariants: Mapping[str, bool] | None = None


class LegacyArmSession(Protocol):
    def replay_http(self, request: Mapping[str, Any]) -> CoreReplayEvidence: ...
    def capture_durable_state(self) -> Mapping[str, Any]: ...
    def restart_cleanly(self) -> None: ...
    def search_by_embedding(self, vector: np.ndarray) -> Sequence[tuple[str, float]]: ...
    def close(self) -> None: ...


class NativeArmSession(Protocol):
    def replay(self, request: Mapping[str, Any]) -> CoreReplayEvidence: ...
    def replay_no_write(self, request: Mapping[str, Any]) -> CoreReplayEvidence: ...
    def capture_durable_state(self) -> Mapping[str, Any]: ...
    def compatibility_embedding_search(self, vector: np.ndarray) -> Sequence[tuple[str, float]]: ...
    def close(self) -> None: ...


class CoreFormalExecutionPorts(Protocol):
    """Injected experiment ports; production code imports none of these helpers."""

    legacy_environment: str
    native_environment: str
    legacy_normal_http_surface: bool
    native_qualified_staging_only: bool

    def allocate_arm_roots(self, arm: CoreFrozenArm) -> CoreArmRoots: ...
    def open_legacy(self, arm: CoreFrozenArm, root: Path) -> LegacyArmSession: ...
    def open_native(self, arm: CoreFrozenArm, root: Path) -> NativeArmSession: ...
    def reopen_native(self, arm: CoreFrozenArm, root: Path) -> NativeArmSession: ...


def require_core_formal_inputs(inputs: FrozenAdministrationInputs) -> None:
    """Accept only the selected core lock; the older Character lock is invalid here."""
    expected = FrozenAdministrationInputs(CORE_PROTOCOL_SHA256, CORE_FIXTURE_SHA256, CORE_TOLERANCES_SHA256)
    if inputs != expected:
        raise D1ProtocolError("core formal executor refuses a non-core or Character-bearing frozen input lock")
    inputs.verify(protocol_sha256=CORE_PROTOCOL_SHA256, fixture_sha256=CORE_FIXTURE_SHA256)


def _require_fields(value: Mapping[str, Any], fields: Sequence[str], *, boundary: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise D1ProtocolError(f"{boundary} lacks required comparison fields: {missing}")


def _difference_intents(result: ComparisonResult) -> list[dict[str, Any]]:
    return [asdict(item) for item in result.differences]


def _compare_replay(legacy: CoreReplayEvidence, native: CoreReplayEvidence) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _require_fields(legacy.storage, _STORAGE_EXACT_FIELDS, boundary="legacy storage evidence")
    _require_fields(native.storage, _STORAGE_EXACT_FIELDS, boundary="native storage evidence")
    _require_fields(legacy.storage, _STORAGE_SCALAR_FIELDS, boundary="legacy scalar evidence")
    _require_fields(native.storage, _STORAGE_SCALAR_FIELDS, boundary="native scalar evidence")
    _require_fields(legacy.post_write, _POST_WRITE_EXACT_FIELDS, boundary="legacy post-write evidence")
    _require_fields(native.post_write, _POST_WRITE_EXACT_FIELDS, boundary="native post-write evidence")
    storage = _difference_intents(compare_exact_fields(legacy.storage, native.storage, _STORAGE_EXACT_FIELDS))
    for field in _STORAGE_SCALAR_FIELDS:
        storage.extend(_difference_intents(compare_scalar(legacy.storage[field], native.storage[field], field=field)))
    if "raw_representation_vector" in legacy.storage or "raw_representation_vector" in native.storage:
        if "raw_representation_vector" not in legacy.storage or "raw_representation_vector" not in native.storage:
            storage.append(asdict(ComparisonDifference("raw_representation_vector", legacy.storage.get("raw_representation_vector"), native.storage.get("raw_representation_vector"), "both-or-neither")))
        else:
            storage.extend(_difference_intents(compare_vector(legacy.storage["raw_representation_vector"], native.storage["raw_representation_vector"])))
    post_write = _difference_intents(compare_exact_fields(legacy.post_write, native.post_write, _POST_WRITE_EXACT_FIELDS))
    return storage, post_write


def _compare_no_write_replay(legacy: CoreReplayEvidence, native: CoreReplayEvidence) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare the semantic absence of M5 storage, not fictional objects."""
    for boundary, evidence in (("legacy", legacy), ("native", native)):
        _require_fields(evidence.storage, _NO_WRITE_STORAGE_FIELDS, boundary=f"{boundary} NO_WRITE evidence")
        _require_fields(evidence.post_write, _POST_WRITE_EXACT_FIELDS, boundary=f"{boundary} NO_WRITE post-write evidence")
        for field, expected in _NO_WRITE_STORAGE_EXPECTED.items():
            if evidence.storage[field] != expected:
                raise D1ProtocolError(f"{boundary} NO_WRITE evidence makes a non-no-write storage claim: {field}")
    storage = _difference_intents(compare_exact_fields(legacy.storage, native.storage, _NO_WRITE_STORAGE_FIELDS))
    post_write = _difference_intents(compare_exact_fields(legacy.post_write, native.post_write, _POST_WRITE_EXACT_FIELDS))
    return storage, post_write


class CoreFormalAdministrationExecutor:
    """One non-retrying CORE_ONLY callback for a future formal runner call."""

    def __init__(self, *, fixture: CoreFrozenFixture, ports: CoreFormalExecutionPorts) -> None:
        self._fixture = fixture
        self._ports = ports
        require_core_formal_inputs(fixture.inputs)
        if (
            fixture.l0_fingerprint_sha256 != CORE_CHARACTER_FREE_L0_FINGERPRINT
            or fixture.side_store_observation_digest != CORE_SIDE_STORE_OBSERVATION_DIGEST
            or tuple(arm.arm_id for arm in fixture.arms) != CORE_ARM_ORDER
        ):
            raise D1ProtocolError("core formal executor fixture does not match the selected CORE_ONLY boundary")
        if (
            ports.legacy_environment != "torment"
            or not ports.legacy_normal_http_surface
            or ports.native_environment != "torment-substrate"
            or not ports.native_qualified_staging_only
        ):
            raise D1ProtocolError("CORE_ONLY executor requires normal legacy HTTP and qualified native STAGING ports")

    @property
    def fixture(self) -> CoreFrozenFixture:
        return self._fixture

    def execute(self, *, administration_id: str) -> FormalResultSchema:
        if not isinstance(administration_id, str) or not administration_id:
            raise D1ProtocolError("core formal executor requires the runner-provided administration ID")
        roots_by_arm: dict[str, CoreArmRoots] = {}
        root_values: list[Path] = []
        for arm in self._fixture.arms:
            roots = self._ports.allocate_arm_roots(arm)
            if not isinstance(roots, CoreArmRoots):
                raise D1ProtocolError("core formal executor requires typed arm clone roots")
            roots_by_arm[arm.arm_id] = roots
            root_values.extend((roots.legacy_root.resolve(), roots.native_root.resolve()))
        if len(root_values) != len(set(root_values)):
            raise D1ProtocolError("CORE_ONLY arms may not share mutable legacy or native roots")

        arm_results: dict[str, dict[str, Any]] = {}
        restart_evidence: list[dict[str, Any]] = []
        retrieval: list[dict[str, Any]] = []
        structural: list[dict[str, Any]] = []
        optional: list[dict[str, Any]] = []
        all_storage_equivalent = True
        all_post_write_equivalent = True
        for arm in self._fixture.arms:
            result, arm_restart, arm_retrieval, arm_structural, arm_optional = self._execute_arm(arm, roots_by_arm[arm.arm_id])
            arm_results[arm.arm_id] = result
            restart_evidence.append(arm_restart)
            retrieval.append(arm_retrieval)
            structural.extend(arm_structural)
            optional.extend(arm_optional)
            all_storage_equivalent = all_storage_equivalent and not result["storage_differences"]
            all_post_write_equivalent = all_post_write_equivalent and not result["post_write_differences"]
        return FormalResultSchema(
            administration_id=administration_id,
            harness_validity="VALID",
            storage_substrate_verdict=(
                "STORAGE_SUBSTRATE_EQUIVALENT_IN_ADMINISTERED_PROFILE"
                if all_storage_equivalent else "STORAGE_SUBSTRATE_DEFECT"
            ),
            qualified_post_write_verdict=(
                "QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE"
                if all_post_write_equivalent else "QUALIFIED_POST_WRITE_DEFECT"
            ),
            optional_feature_divergences=tuple(optional),
            known_unsupported_edges=("D1_CLOSED_LOOP_QUERY_PARITY_TESTED=NO",),
            m1=arm_results["M1_CREATE"],
            m2=arm_results["M2_REINFORCE"],
            m3=arm_results["M3_DISTINCT"],
            m4=arm_results["M4_CONTRADICTION"],
            m5=arm_results["M5_NO_WRITE"],
            sequential=arm_results["SEQUENTIAL"],
            character={
                "CHARACTER_ARM_ADMINISTERED": "NO",
                "CHARACTER_SUBARM_STATUS": CHARACTER_SUBARM_STATUS,
            },
            restart_evidence=tuple(restart_evidence),
            retrieval_characterization=tuple(retrieval),
            native_structural_invariants=tuple(structural),
        )

    def _execute_arm(
        self, arm: CoreFrozenArm, roots: CoreArmRoots,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
        legacy = self._ports.open_legacy(arm, roots.legacy_root)
        try:
            native = self._ports.open_native(arm, roots.native_root)
        except Exception:
            # Opening the concrete legacy port starts an ordinary child
            # service. If the paired native core cannot open, cleanly release
            # that service before propagating the one original port failure.
            # This is cleanup only: there is no fallback, replay, or retry.
            try:
                legacy.close()
            except Exception:
                pass
            raise
        storage_differences: list[dict[str, Any]] = []
        post_write_differences: list[dict[str, Any]] = []
        structural: list[dict[str, Any]] = []
        optional: list[dict[str, Any]] = []
        try:
            for event in arm.events:
                legacy_evidence = legacy.replay_http(event.legacy_http_request())
                self._verify_legacy_expected(event, legacy_evidence)
                if event.is_no_write:
                    before = native.capture_durable_state()
                    native_evidence = native.replay_no_write(event.native_request())
                    after = native.capture_durable_state()
                    if after != before:
                        raise D1ProtocolError("M5 NO_WRITE changed durable native storage")
                else:
                    native_evidence = native.replay(event.native_request())
                event_storage, event_post = (
                    _compare_no_write_replay(legacy_evidence, native_evidence)
                    if event.is_no_write else _compare_replay(legacy_evidence, native_evidence)
                )
                storage_differences.extend({"fixture_id": event.fixture_id, **item} for item in event_storage)
                post_write_differences.extend({"fixture_id": event.fixture_id, **item} for item in event_post)
                optional.extend(
                    {"arm_id": arm.arm_id, "fixture_id": event.fixture_id, **dict(item)}
                    for item in (*legacy_evidence.optional_feature_divergences, *native_evidence.optional_feature_divergences)
                )
                if native_evidence.native_structural_invariants is None:
                    raise D1ProtocolError("native formal evidence lacks structural invariants")
                if event.is_no_write:
                    validate_native_no_write_structure(native_evidence.native_structural_invariants)
                else:
                    validate_native_structure(native_evidence.native_structural_invariants)
                structural.append({"arm_id": arm.arm_id, "fixture_id": event.fixture_id, **dict(native_evidence.native_structural_invariants)})
            legacy_pre_restart = dict(legacy.capture_durable_state())
            legacy.restart_cleanly()
            legacy_post_restart = dict(legacy.capture_durable_state())
            native.close()
            native = self._ports.reopen_native(arm, roots.native_root)
            native_post_restart = dict(native.capture_durable_state())
            query = arm.events[0].query_vector()
            legacy_ranking = tuple(legacy.search_by_embedding(query))
            native_ranking = tuple(native.compatibility_embedding_search(query))
            ranking = _difference_intents(compare_rankings(legacy_ranking, native_ranking))
            return (
                {
                    "arm_id": arm.arm_id,
                    "event_order": [event.fixture_id for event in arm.events],
                    "storage_differences": storage_differences,
                    "post_write_differences": post_write_differences,
                    "legacy_clone_id": arm.legacy_clone_id,
                    "native_clone_id": arm.native_clone_id,
                },
                {
                    "arm_id": arm.arm_id,
                    "LEGACY_PRE_RESTART": legacy_pre_restart,
                    "LEGACY_POST_RESTART": legacy_post_restart,
                    "NATIVE_POST_RESTART": native_post_restart,
                },
                {
                    "arm_id": arm.arm_id,
                    "query_vector_sha256": sha256_value(query.tolist()),
                    "ranking_differences": ranking,
                    "D1_CLOSED_LOOP_QUERY_PARITY_TESTED": "NO",
                },
                structural,
                optional,
            )
        finally:
            try:
                native.close()
            finally:
                legacy.close()

    @staticmethod
    def _verify_legacy_expected(event: CoreFrozenEvent, evidence: CoreReplayEvidence) -> None:
        _require_fields(evidence.storage, ("stored", "reinforced"), boundary="legacy frozen-outcome evidence")
        if (
            evidence.storage["stored"] != event.legacy_expected.get("stored")
            or evidence.storage["reinforced"] != event.legacy_expected.get("reinforced")
        ):
            raise D1ProtocolError("legacy execution diverged from the frozen CORE_ONLY observed outcome")


__all__ = [
    "CHARACTER_FIXTURE_FILENAME",
    "CHARACTER_SUBARM_STATUS",
    "CORE_ARM_ORDER",
    "CORE_FIXTURE_FILENAME",
    "CORE_FIXTURE_GENERATION_HEAD",
    "CORE_FIXTURE_SHA256",
    "CORE_PROTOCOL_SHA256",
    "CORE_TOLERANCES_SHA256",
    "CoreArmRoots",
    "CoreFormalAdministrationExecutor",
    "CoreFormalExecutionPorts",
    "CoreFrozenArm",
    "CoreFrozenEvent",
    "CoreFrozenFixture",
    "CoreReplayEvidence",
    "require_core_formal_inputs",
]
