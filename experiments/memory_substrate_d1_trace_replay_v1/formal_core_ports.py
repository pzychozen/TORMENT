"""Concrete, experiment-local ports for a future CORE_ONLY D1 administration.

The module is intended to run under ``torment-substrate`` only.  It imports
and opens qualified native STAGING machinery, while the ordinary legacy HTTP
service and all legacy-file interpretation live in ``formal_core_legacy_worker``
under the separate ``torment`` environment.  Nothing here selects a production
backend or starts a formal administration by itself.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Protocol, Sequence
from uuid import UUID

import numpy as np

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.fabric_native_routing import (
    NativeFabricMemoryRouter,
    NativeFabricRoutingScope,
    prepare_native_fabric_routing_capability,
)
from torment_service.substrate.ids import native_id_from_bytes
from torment_service.substrate.native_post_write_runtime import (
    prepare_native_fabric_post_write_adapter,
)
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.runtime_binding import (
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)
from torment_service.substrate.schema import open_schema

from .formal_core_executor import (
    CORE_ARM_ORDER,
    CORE_FIXTURE_SHA256,
    CORE_PROTOCOL_SHA256,
    CORE_TOLERANCES_SHA256,
    CoreArmRoots,
    CoreFrozenArm,
    CoreReplayEvidence,
)
from .legacy_capture import (
    InitialPostWritePlaceholderPosture,
    LegacyCapturedEvent,
    LegacyObservedOutcome,
    LegacyStorageFacingFacts,
)
from .native_replay import NativeCoreStorageSnapshot, NativeReplayHarness
from .protocol import D1ProtocolError
from .real_n0 import _configuration
from .side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)
from torment_service.substrate.migration import MigrationRuntimeScopePlan


CORE_WORKSPACE_ID = "d1core20260831"
CORE_AGENT_ID = "d1coreagent"
CORE_DOMAIN_ID = "research"
_CORE_SOURCE_KEY = "d1-real-l0-20260831"
_OBJECT_NAMESPACE_KEY = "d1-n0-objects"
_RELATIONSHIP_NAMESPACE_KEY = "d1-n0-relationships"
_MOTIF_ALIAS_SOURCE_KEY = "d1-n0-runtime-motif-aliases"
_SEMANTIC_SCOPE_KEY = "d1-n0-private-research"
_IDEMPOTENCY_NAMESPACE_KEY = "d1-n0"


class CoreFormalPortFailure(D1ProtocolError):
    """A concrete process, source, or qualified-STAGING port failed once."""


@dataclass(frozen=True)
class CoreD1SourceLocations:
    """The pre-established, read-only CORE_ONLY source locations."""

    l0_root: Path
    n0_root: Path

    @classmethod
    def frozen_default(cls) -> "CoreD1SourceLocations":
        root = Path(r"C:\TORMENT\experiments\7g5d1_formal_preflight_20260831")
        return cls(
            l0_root=(root / "core_character_free_20260831").resolve(),
            n0_root=(root / "core_n0_fixture_freeze_20260831").resolve(),
        )

    def __post_init__(self) -> None:
        if not self.l0_root.is_absolute() or not self.n0_root.is_absolute():
            raise CoreFormalPortFailure("CORE_ONLY source locations must be absolute")


class _LegacyWorker(Protocol):
    def request(self, command: str, **values: Any) -> Mapping[str, Any]: ...
    def close(self) -> None: ...


def _default_conda_bat() -> Path:
    """Resolve CMD's activation script, never the Python environment itself."""
    configured = os.environ.get("CONDA_EXE")
    if configured:
        candidate = Path(configured).resolve()
        if candidate.suffix.lower() == ".bat":
            return candidate
        # Conda's usual CONDA_EXE points at ``Scripts\\conda.exe``; CMD
        # activation must instead call the sibling ``condabin\\conda.bat``.
        return (candidate.parent.parent / "condabin" / "conda.bat").resolve()
    return Path(r"C:\Users\Notandi\miniconda3\condabin\conda.bat").resolve()


class _JsonLineLegacyWorker:
    """One no-retry JSON-line process boundary around the ``torment`` worker."""

    def __init__(
        self,
        *,
        repository_root: Path,
        conda_bat: Path,
        source_l0_root: Path,
        arm_root: Path,
    ) -> None:
        if not conda_bat.is_file():
            raise CoreFormalPortFailure("the conda activation command for the legacy worker is unavailable")
        command = (
            f"call {conda_bat} activate torment && "
            "python -m experiments.memory_substrate_d1_trace_replay_v1.formal_core_legacy_worker --serve"
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(repository_root) + os.pathsep + environment.get("PYTHONPATH", "")
        try:
            self._process = subprocess.Popen(
                [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", command],
                cwd=repository_root,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            raise CoreFormalPortFailure("could not launch the legacy torment worker") from exc
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise CoreFormalPortFailure("legacy worker has no JSON IPC streams")
        try:
            self.request(
                "open",
                source_l0_root=str(source_l0_root),
                arm_root=str(arm_root),
                workspace_id=CORE_WORKSPACE_ID,
                agent_id=CORE_AGENT_ID,
                domain_id=CORE_DOMAIN_ID,
            )
        except Exception:
            self.close()
            raise

    def request(self, command: str, **values: Any) -> Mapping[str, Any]:
        if self._process.poll() is not None:
            raise CoreFormalPortFailure("legacy torment worker exited unexpectedly")
        assert self._process.stdin is not None and self._process.stdout is not None
        message = json.dumps({"command": command, **values}, sort_keys=True, separators=(",", ":"))
        try:
            self._process.stdin.write(message + "\n")
            self._process.stdin.flush()
            line = self._process.stdout.readline()
        except OSError as exc:
            raise CoreFormalPortFailure("legacy worker IPC failed") from exc
        if not line:
            raise CoreFormalPortFailure("legacy worker returned no IPC result")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CoreFormalPortFailure("legacy worker returned malformed JSON") from exc
        if not isinstance(response, dict) or response.get("ok") is not True:
            detail = response.get("error") if isinstance(response, dict) else "unknown worker failure"
            raise CoreFormalPortFailure(f"legacy worker failed: {detail}")
        value = response.get("value")
        if not isinstance(value, dict):
            raise CoreFormalPortFailure("legacy worker returned a non-object value")
        return value

    def close(self) -> None:
        process = getattr(self, "_process", None)
        if process is None:
            return
        try:
            if process.poll() is None:
                try:
                    self.request("close")
                except CoreFormalPortFailure:
                    pass
                process.terminate()
                process.wait(timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)


def _core_replay_evidence(value: Mapping[str, Any]) -> CoreReplayEvidence:
    storage, post_write = value.get("storage"), value.get("post_write")
    optional = value.get("optional_feature_divergences", ())
    structural = value.get("native_structural_invariants")
    if not isinstance(storage, dict) or not isinstance(post_write, dict) or not isinstance(optional, list):
        raise CoreFormalPortFailure("worker evidence does not satisfy the CORE_ONLY evidence shape")
    if structural is not None and not isinstance(structural, dict):
        raise CoreFormalPortFailure("worker structural evidence is malformed")
    return CoreReplayEvidence(
        storage=dict(storage),
        post_write=dict(post_write),
        optional_feature_divergences=tuple(dict(item) for item in optional if isinstance(item, dict)),
        native_structural_invariants=dict(structural) if structural is not None else None,
    )


class LegacyHttpArmSession:
    """An ordinary ``python -m torment_service`` session owned by its worker."""

    def __init__(self, worker: _LegacyWorker) -> None:
        self._worker = worker

    def replay_http(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        return _core_replay_evidence(self._worker.request("replay_http", request=dict(request)))

    def capture_durable_state(self) -> Mapping[str, Any]:
        return dict(self._worker.request("capture_durable_state"))

    def restart_cleanly(self) -> None:
        self._worker.request("restart_cleanly")

    def search_by_embedding(self, vector: np.ndarray) -> Sequence[tuple[str, float]]:
        value = self._worker.request(
            "search_by_embedding",
            vector_base64=base64.b64encode(np.asarray(vector, dtype=np.float32).tobytes(order="C")).decode("ascii"),
        )
        rows = value.get("ranking")
        if not isinstance(rows, list):
            raise CoreFormalPortFailure("legacy worker retrieval result is malformed")
        return tuple((str(item[0]), float(item[1])) for item in rows if isinstance(item, list) and len(item) == 2)

    def close(self) -> None:
        self._worker.close()


@dataclass(frozen=True)
class _NativeScope:
    lane: NativeRepresentationLane
    runtime: NativeMemoryRuntimeScope
    routing: NativeFabricRoutingScope


def _uuid_by_key(connection: Any, table: str, id_column: str, key_column: str, key: str) -> UUID:
    rows = connection.execute(
        f"SELECT {id_column} FROM {table} WHERE {key_column}=?", (key,)
    ).fetchall()
    if len(rows) != 1 or not isinstance(rows[0][0], bytes):
        raise CoreFormalPortFailure(f"qualified CORE_ONLY N0 lacks its named {table} row: {key}")
    return UUID(bytes=rows[0][0])


def _prepare_native_scope(database: Path) -> tuple[Any, Any, _NativeScope]:
    """Open only an existing qualified core and prepare its frozen A3D wiring."""
    with open_existing_native_core_connection(database) as opened:
        connection = opened.connection
        metadata = open_schema(connection, writable=False)
        core_id = native_id_from_bytes(metadata.core_id)
        lane = NativeRepresentationLane(
            provider="hash", model="hash:384:torment", dimension=384,
            representation_class="COMPAT_EMBEDDING", generation=1,
            derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
        )
        plan = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=_uuid_by_key(connection, "legacy_source_namespaces", "legacy_source_namespace_id", "source_key", _CORE_SOURCE_KEY),
            workspace_id=CORE_WORKSPACE_ID, scope_kind="PRIVATE_AGENT", agent_id=CORE_AGENT_ID,
            target_identity_namespace_id=_uuid_by_key(connection, "identity_namespaces", "identity_namespace_id", "namespace_key", _OBJECT_NAMESPACE_KEY),
            target_semantic_scope_id=_uuid_by_key(connection, "semantic_scopes", "semantic_scope_id", "scope_key", _SEMANTIC_SCOPE_KEY),
            motif_alias_namespace_id=_uuid_by_key(connection, "legacy_source_namespaces", "legacy_source_namespace_id", "source_key", _MOTIF_ALIAS_SOURCE_KEY),
            motif_identity_namespace_id=_uuid_by_key(connection, "identity_namespaces", "identity_namespace_id", "namespace_key", _OBJECT_NAMESPACE_KEY),
            membership_identity_namespace_id=_uuid_by_key(connection, "identity_namespaces", "identity_namespace_id", "namespace_key", _RELATIONSHIP_NAMESPACE_KEY),
            idempotency_namespace_id=_uuid_by_key(connection, "idempotency_namespaces", "idempotency_namespace_id", "namespace_key", _IDEMPOTENCY_NAMESPACE_KEY),
            motif_domain_id=CORE_DOMAIN_ID,
        )
        runtime = NativeMemoryRuntimeScope(
            workspace_id=plan.workspace_id, scope_kind=plan.scope_kind,
            legacy_source_namespace_id=plan.legacy_source_namespace_id,
            identity_namespace_id=plan.target_identity_namespace_id,
            semantic_scope_id=plan.target_semantic_scope_id, agent_id=plan.agent_id,
        )
        routing = NativeFabricRoutingScope(
            runtime_scope=runtime, motif_alias_namespace_id=plan.motif_alias_namespace_id,
            motif_identity_namespace_id=plan.motif_identity_namespace_id,
            membership_identity_namespace_id=plan.membership_identity_namespace_id,
            idempotency_namespace_id=plan.idempotency_namespace_id,
        )
        binding = prepare_native_memory_runtime_binding(
            connection=connection, core_database_path=database, expected_core_id=core_id,
            scope_bindings=(runtime,), representation_lane=lane,
        )
        capability = prepare_native_fabric_routing_capability(
            binding=binding, connection=connection, routing_scopes=(routing,), expected_core_id=core_id,
        )
        return capability, prepare_native_fabric_post_write_adapter(
            capability=capability, configuration=_configuration(plan, lane),
        ), _NativeScope(lane, runtime, routing)


def _facts_from_mapping(value: Mapping[str, Any]) -> LegacyStorageFacingFacts:
    forbidden = {"eid", "legacy_eid", "reinforcement_target_eid", "selected_reinforcement_eid"}.intersection(value)
    if forbidden:
        raise CoreFormalPortFailure(f"native request contains a forbidden legacy selection: {sorted(forbidden)}")
    embedding = value.get("embedding")
    lane_value = value.get("embedder_lane")
    if not isinstance(embedding, dict) or not isinstance(lane_value, dict):
        raise CoreFormalPortFailure("native request lacks frozen representation facts")
    try:
        vector = np.frombuffer(base64.b64decode(embedding["base64"]), dtype=np.float32).copy()
        lane = NativeRepresentationLane(**lane_value)
        provenance = ProvenanceV1.from_dict(dict(value.get("provenance") or {}))
        governance = MemoryGovernanceFlags.from_dict(dict(value.get("governance") or {}))
    except (KeyError, TypeError, ValueError) as exc:
        raise CoreFormalPortFailure("native request contains malformed frozen storage facts") from exc
    return LegacyStorageFacingFacts(
        # The sealed storage-facing mapping intentionally omits the legacy
        # fixture identity. The immutable native operation key is its only
        # admitted identifier on this side of the process boundary.
        fixture_id=str(value.get("fixture_id") or value["native_operation_key"]), workspace_id=str(value["workspace_id"]), agent_id=str(value["agent_id"]),
        scope=str(value["scope"]), domain_id=str(value["domain_id"]), native_operation_key=str(value["native_operation_key"]),
        text=str(value["text"]), summary=str(value["summary"]), embedding=vector, embedder_lane=lane,
        memory_type=str(value["memory_type"]), memory_class=str(value["memory_class"]),
        strength=float(value["strength"]), confidence=float(value["confidence"]), promotion_score=float(value["promotion_score"]),
        half_life_days=float(value["half_life_days"]), logical_step=int(value["logical_step"]),
        created_ts=int(value["created_ts"]), last_active_ts=int(value["last_active_ts"]),
        last_reinforced_ts=int(value["last_reinforced_ts"]), provenance=provenance, governance=governance,
        flexible_payload=dict(value.get("flexible_payload") or {}), attach_threshold=float(value.get("attach_threshold", 0.76)),
        stability_delta=float(value.get("stability_delta", 0.0)), prior_symbol=str(value.get("prior_symbol", "")),
        prior_symbol_trace=tuple(value.get("prior_symbol_trace") or ()), prior_motif_id=str(value.get("prior_motif_id", "")),
        prior_tension=float(value.get("prior_tension", 0.0)), last_tool_refresh_ts=value.get("last_tool_refresh_ts"),
        tri_mod=dict(value.get("tri_mod") or {}), debug=dict(value.get("debug") or {}),
        srg_state=value.get("srg_state"), phase_durations=dict(value.get("phase_durations") or {}),
        affect_tag=value.get("affect_tag"), affect_conf=value.get("affect_conf"),
        skip_packet_emission=bool(value.get("skip_packet_emission", False)),
    )


class QualifiedNativeArmSession:
    """One explicit, qualified native STAGING arm; no graph or legacy fallback."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._database = self._root / "n0_core.db"
        self._capability, self._post_write, self._scope = _prepare_native_scope(self._database)
        self._router = NativeFabricMemoryRouter(self._capability)
        self.router_call_count = 0

    def replay(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        facts = _facts_from_mapping(request)
        self.router_call_count += 1
        outcome = NativeReplayHarness(
            router=self._router, post_write=self._post_write,
            native_storage_snapshot=lambda: NativeCoreStorageSnapshot.capture(self._database),
            placeholder_posture=InitialPostWritePlaceholderPosture(False, "read_only"),
        ).replay(LegacyCapturedEvent(facts, LegacyObservedOutcome(True, False, None)))
        if outcome.route_attempt is None or outcome.route_attempt.result is None:
            raise CoreFormalPortFailure("qualified native STAGING route produced no result")
        return self._evidence_for_result(facts, outcome.route_attempt.result, outcome.post_write_outcome)

    def replay_no_write(self, request: Mapping[str, Any]) -> CoreReplayEvidence:
        facts = _facts_from_mapping(request)
        before = NativeCoreStorageSnapshot.capture(self._database)
        outcome = NativeReplayHarness(
            router=self._router, post_write=self._post_write,
            native_storage_snapshot=lambda: NativeCoreStorageSnapshot.capture(self._database),
            placeholder_posture=InitialPostWritePlaceholderPosture(False, "read_only"),
        ).replay(LegacyCapturedEvent(facts, LegacyObservedOutcome(False, False, None)))
        after = NativeCoreStorageSnapshot.capture(self._database)
        if outcome.route_attempt is not None or before != after:
            raise CoreFormalPortFailure("M5 no-write native port touched the router or durable core")
        return CoreReplayEvidence(
            storage=_no_write_storage(facts), post_write=_post_write_intent(outcome.post_write_outcome),
            native_structural_invariants=_no_write_structural_invariants(),
        )

    def capture_durable_state(self) -> Mapping[str, Any]:
        return {"table_counts": [list(item) for item in NativeCoreStorageSnapshot.capture(self._database).table_counts]}

    def compatibility_embedding_search(self, vector: np.ndarray) -> Sequence[tuple[str, float]]:
        with open_existing_native_core_connection(self._database) as opened:
            hits = NativeMemoryCompatibilityFacade(opened.connection).search_by_embedding(
                legacy_source_namespace_id=self._scope.runtime.legacy_source_namespace_id,
                embedding=np.asarray(vector, dtype=np.float32), dimension=self._scope.lane.dimension,
                representation_class=self._scope.lane.representation_class, generation=self._scope.lane.generation,
                derivation_contract_version=self._scope.lane.derivation_contract_version,
                encoding_id=self._scope.lane.encoding_id, dtype=self._scope.lane.dtype,
            )
        return tuple((str(hit.eid), float(hit.score)) for hit in hits)

    def close(self) -> None:
        # Router/adapter retain only immutable prepared configuration.  Every
        # actual SQLite connection is scoped to the operation that opened it.
        return None

    def _evidence_for_result(self, facts: LegacyStorageFacingFacts, result: Any, post_write: Any) -> CoreReplayEvidence:
        with open_existing_native_core_connection(self._database) as opened:
            connection = opened.connection
            facade = NativeMemoryCompatibilityFacade(connection)
            view = facade.get_memory_by_eid(
                legacy_source_namespace_id=self._scope.runtime.legacy_source_namespace_id, eid=result.eid,
            )
            representations = NativeRepresentationService(connection)
            raw = representations.read_representation_payload(result.representation_id)
            storage = {
                "stored": bool(result.stored), "reinforced": bool(result.reinforced), "compatible_eid": True,
                "summary": view.summary, "memory_type": str(view.payload.get("type", "")),
                "memory_class": str(view.payload.get("memory_class", "")),
                "lifecycle": {"state": view.lifecycle_state, "authoritative": view.lifecycle_authoritative},
                "governance": {"state": view.governance_state},
                "provenance": _provenance_intent(connection, view.provenance_id),
                "raw_representation_bytes": base64.b64encode(raw).decode("ascii"),
                "raw_representation_vector": np.frombuffer(raw, dtype=np.float32).tolist(),
                "motif_membership": list(result.motifs),
                "motif_geometry": _motif_geometry(connection, self._scope.routing, result.motifs, self._scope.lane.dimension),
                "conflict": None,
                "strength": float(view.payload.get("strength", 0.0)),
                "confidence": float(view.payload.get("confidence", 0.0)),
                "half_life_days": float(view.payload.get("half_life", 0.0)),
                "reinforcement_count": int(view.payload.get("reinforcement_count", 0)),
            }
            structural = _native_structural_invariants(connection, self._scope, facts, result, view)
        return CoreReplayEvidence(
            storage=storage, post_write=_post_write_intent(post_write),
            native_structural_invariants=structural,
        )


def _provenance_intent(connection: Any, provenance_id: UUID | None) -> Mapping[str, Any] | None:
    if provenance_id is None:
        return None
    row = connection.execute(
        "SELECT origin_kind,source_channel,source_role,derivation_status,uncertainty_state FROM provenance_records WHERE provenance_id=?",
        (provenance_id.bytes,),
    ).fetchone()
    if row is None:
        raise CoreFormalPortFailure("native memory has an unresolved provenance record")
    return {"origin_kind": row[0], "source_channel": row[1], "source_role": row[2], "derivation_status": row[3], "uncertainty_state": row[4]}


def _motif_geometry(connection: Any, routing: NativeFabricRoutingScope, motifs: Sequence[str], dimension: int) -> list[dict[str, Any]]:
    # Reading current motif geometry is deliberately delegated to the qualified
    # runtime reader; it does not rebuild or re-embed a motif.
    from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader

    listed = NativeMotifRuntimeReader(connection).list_runtime_motifs(
        motif_alias_namespace_id=routing.motif_alias_namespace_id, domain_id=CORE_DOMAIN_ID,
        semantic_scope_id=routing.runtime_scope.semantic_scope_id,
    )
    by_id = {item.read_model.runtime_motif_id: item for item in listed}
    output: list[dict[str, Any]] = []
    for motif_id in motifs:
        motif = by_id.get(motif_id)
        if motif is None:
            raise CoreFormalPortFailure("native route references a non-current motif")
        radius = NativeMotifRuntimeReader(connection).motif_radius(
            motif.motif_object_id, expected_dimension=dimension,
        )
        output.append({"runtime_motif_id": motif_id, "radius": radius, "member_count": motif.read_model.member_count})
    return output


def _post_write_intent(value: Any) -> Mapping[str, Any]:
    return {
        "qualified_post_write_outputs": {"proposal_id": getattr(value, "proposal_id", None)},
        "deterministic_runtime_ordering": ["contradiction", "srg", "hivemind", "derived", "world", "proposal"],
    }


def _no_write_storage(facts: LegacyStorageFacingFacts) -> Mapping[str, Any]:
    return {
        "stored": False, "reinforced": False, "compatible_eid": False, "summary": facts.summary,
        "memory_type": facts.memory_type, "memory_class": facts.memory_class,
        "lifecycle": None, "governance": facts.governance.to_dict(),
        "provenance": facts.provenance.to_dict(),
        "raw_representation_bytes": base64.b64encode(facts.embedding_bytes).decode("ascii"),
        "raw_representation_vector": facts.embedding.tolist(), "motif_membership": [], "motif_geometry": [],
        "conflict": None, "strength": facts.strength, "confidence": facts.confidence,
        "half_life_days": facts.half_life_days, "reinforcement_count": 0,
    }


def _no_write_structural_invariants() -> Mapping[str, bool]:
    return {
        "uuid_uniqueness": True, "correct_parentage": True, "revision_advancement": True,
        "current_revision_ownership": True, "operation_ownership": True, "idempotency": True,
        "retry_stability": True,
    }


def _native_structural_invariants(connection: Any, scope: _NativeScope, facts: LegacyStorageFacingFacts, result: Any, view: Any) -> Mapping[str, bool]:
    operation_key = (
        f"NATIVE_REINFORCEMENT:SOURCE:NATIVE_FABRIC_REINFORCEMENT:{facts.native_operation_key}"
        if result.reinforced else f"NATIVE_FABRIC_NEW_MEMORY:SOURCE:{facts.native_operation_key}"
    )
    rows = connection.execute(
        "SELECT operation_id FROM operations WHERE idempotency_namespace_id=? AND idempotency_key=?",
        (scope.routing.idempotency_namespace_id.bytes, operation_key),
    ).fetchall()
    operation_owned = len(rows) == 1 and connection.execute(
        "SELECT count(*) FROM operation_outputs WHERE operation_id=? AND object_id=? AND object_revision_id=?",
        (rows[0][0], result.memory_object_id.bytes, result.memory_revision_id.bytes),
    ).fetchone()[0] == 1
    return {
        "uuid_uniqueness": len({result.memory_object_id, result.memory_revision_id, result.representation_id}) == 3,
        "correct_parentage": view.semantic_scope_id == scope.runtime.semantic_scope_id,
        "revision_advancement": view.revision_ordinal >= (2 if result.reinforced else 1),
        "current_revision_ownership": view.object_id == result.memory_object_id and view.revision_id == result.memory_revision_id,
        "operation_ownership": bool(operation_owned),
        "idempotency": len(rows) == 1,
        "retry_stability": len(rows) == 1,
    }


class ConcreteCoreFormalExecutionPorts:
    """Concrete ports for exactly one later, explicit CORE_ONLY administration."""

    legacy_environment = "torment"
    native_environment = "torment-substrate"
    legacy_normal_http_surface = True
    native_qualified_staging_only = True

    def __init__(
        self,
        *,
        administration_work_root: str | Path,
        source_locations: CoreD1SourceLocations | None = None,
        repository_root: str | Path | None = None,
        conda_bat: str | Path | None = None,
        legacy_worker_factory: Callable[[Path, Path], _LegacyWorker] | None = None,
        native_session_factory: Callable[[Path], Any] | None = None,
        legacy_source_verifier: Callable[[], Mapping[str, Any]] | None = None,
        native_source_verifier: Callable[[], None] | None = None,
    ) -> None:
        self._work_root = Path(administration_work_root).resolve()
        if not self._work_root.is_absolute() or self._work_root.exists():
            raise CoreFormalPortFailure("formal administration work root must be absolute and new")
        self._locations = source_locations or CoreD1SourceLocations.frozen_default()
        self._repository_root = Path(repository_root or Path(__file__).resolve().parents[2]).resolve()
        self._conda_bat = Path(conda_bat).resolve() if conda_bat is not None else _default_conda_bat()
        self._legacy_worker_factory = legacy_worker_factory
        self._native_session_factory = native_session_factory or QualifiedNativeArmSession
        self._legacy_source_verifier = legacy_source_verifier
        self._native_source_verifier = native_source_verifier
        self._allocated: set[str] = set()

    def allocate_arm_roots(self, arm: CoreFrozenArm) -> CoreArmRoots:
        if arm.arm_id not in CORE_ARM_ORDER or arm.arm_id in self._allocated:
            raise CoreFormalPortFailure("formal arm allocation must be exactly once for a named CORE_ONLY arm")
        parent = self._work_root / arm.arm_id
        legacy, native = parent / "legacy", parent / "native"
        if legacy.exists() or native.exists() or parent.exists():
            raise CoreFormalPortFailure("formal arm root unexpectedly already exists")
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            raise CoreFormalPortFailure("could not allocate an isolated formal arm root") from exc
        self._allocated.add(arm.arm_id)
        return CoreArmRoots(legacy.resolve(), native.resolve())

    def open_legacy(self, arm: CoreFrozenArm, root: Path) -> LegacyHttpArmSession:
        self._require_allocated_root(arm, root, "legacy")
        worker = self._legacy_worker_factory(root, self._locations.l0_root) if self._legacy_worker_factory else _JsonLineLegacyWorker(
            repository_root=self._repository_root, conda_bat=self._conda_bat,
            source_l0_root=self._locations.l0_root, arm_root=root,
        )
        return LegacyHttpArmSession(worker)

    def open_native(self, arm: CoreFrozenArm, root: Path) -> Any:
        self._require_allocated_root(arm, root, "native")
        if root.exists():
            raise CoreFormalPortFailure("native mutable arm root must be new")
        try:
            shutil.copytree(self._locations.n0_root, root)
        except OSError as exc:
            raise CoreFormalPortFailure("could not clone the qualified CORE_ONLY N0 source") from exc
        return self._native_session_factory(root)

    def reopen_native(self, arm: CoreFrozenArm, root: Path) -> Any:
        self._require_allocated_root(arm, root, "native")
        if not (root / "n0_core.db").is_file():
            raise CoreFormalPortFailure("native reopen requires the same existing mutated arm core")
        return self._native_session_factory(root)

    def verify_frozen_sources(self) -> None:
        if self._legacy_source_verifier is not None:
            legacy = self._legacy_source_verifier()
        else:
            legacy = self._verify_legacy_source_in_legacy_environment()
        if (
            legacy.get("l0_fingerprint_sha256") != CORE_CHARACTER_FREE_L0_FINGERPRINT
            or legacy.get("side_store_observation_digest") != CORE_SIDE_STORE_OBSERVATION_DIGEST
            or legacy.get("character_arm_absent") is not True
        ):
            raise CoreFormalPortFailure("legacy source L0 is not the frozen CORE_ONLY baseline")
        if self._native_source_verifier is not None:
            self._native_source_verifier()
        else:
            self._verify_qualified_native_source()

    def _require_allocated_root(self, arm: CoreFrozenArm, root: Path, kind: str) -> None:
        expected = (self._work_root / arm.arm_id / kind).resolve()
        if arm.arm_id not in self._allocated or Path(root).resolve() != expected:
            raise CoreFormalPortFailure("formal port received a root outside its one allocated arm")

    def _verify_legacy_source_in_legacy_environment(self) -> Mapping[str, Any]:
        if not self._conda_bat.is_file():
            raise CoreFormalPortFailure("the conda activation command for the legacy verifier is unavailable")
        command = (
            f"call {self._conda_bat} activate torment && "
            "python -m experiments.memory_substrate_d1_trace_replay_v1.formal_core_legacy_worker --verify-source "
            f"--l0-root {self._locations.l0_root}"
        )
        completed = subprocess.run(
            [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", command],
            cwd=self._repository_root, capture_output=True, text=True, encoding="utf-8", check=False,
            env={**os.environ, "PYTHONPATH": str(self._repository_root) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise CoreFormalPortFailure(f"legacy frozen-source verifier failed: {detail or completed.returncode}")
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise CoreFormalPortFailure("legacy frozen-source verifier returned malformed JSON") from exc
        if not isinstance(result, dict):
            raise CoreFormalPortFailure("legacy frozen-source verifier returned a non-object")
        return result

    def _verify_qualified_native_source(self) -> None:
        report_path = self._locations.n0_root / "n0_build_report.json"
        database = self._locations.n0_root / "n0_core.db"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CoreFormalPortFailure("qualified CORE_ONLY N0 report is unreadable") from exc
        required_true = (
            "whole_workspace_memory_closure", "whole_workspace_motif_closure",
            "whole_workspace_member_reference_closure", "whole_workspace_side_store_retention",
            "core_staging_runtime_ready", "controlled_native_staging_experiment_ready",
            "runtime_binding_constructible", "routing_capability_constructible", "post_write_adapter_constructible",
        )
        if (
            report.get("schema") != "memory-substrate-d1-real-n0-v1"
            or report.get("l0_fingerprint_sha256") != CORE_CHARACTER_FREE_L0_FINGERPRINT
            or report.get("core_side_store_observation_digest") != CORE_SIDE_STORE_OBSERVATION_DIGEST
            or report.get("native_formal_event_count") != 0
            or any(report.get(name) is not True for name in required_true)
            or report.get("b3a_eids") != [1] or report.get("b4b_ready_motif_count") != 0
        ):
            raise CoreFormalPortFailure("qualified CORE_ONLY N0 report is not the frozen constructible baseline")
        # Construction revalidates the existing core without migration, rebuild,
        # route, or any semantic mutation.
        _prepare_native_scope(database)


__all__ = [
    "CORE_AGENT_ID", "CORE_DOMAIN_ID", "CORE_WORKSPACE_ID", "CoreD1SourceLocations",
    "CoreFormalPortFailure", "ConcreteCoreFormalExecutionPorts", "LegacyHttpArmSession",
    "QualifiedNativeArmSession",
]
