"""7G5E4B qualification for the process-local native vector runtime.

The tests intentionally instantiate the runtime directly.  They do not add a
Fabric selector, shared admission, durable cache state, or legacy-file input.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Any

import numpy as np
import pytest

from torment_service import memory_graph as memory_graph_module
from torment_service.memory_graph import MemoryGraph
from torment_service.substrate import native_memory_vector_runtime as vector_runtime_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from torment_service.substrate.motifs import MotifState, NativeMotifService, NativeMotifSplitPlan
from torment_service.substrate.native_memory_vector_runtime import (
    NativeMemoryVectorRuntime,
    NativeMemoryVectorRuntimeConfiguration,
)
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationIntegrityExpectationRequest,
    RepresentationIntegrityVerificationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


class _Embedder:
    provider = "7g5e4b-test"
    model = "frozen-float32"
    dim = 3

    def __init__(self, vector: Any = (1.0, 0.0, 0.0)) -> None:
        self.vector = np.asarray(vector, dtype=np.float32)
        self.calls: list[str] = []

    def embed(self, text: str) -> np.ndarray:
        self.calls.append(text)
        return self.vector.copy()


def _lane() -> NativeRepresentationLane:
    return NativeRepresentationLane(
        provider="7g5e4b-test",
        model="frozen-float32",
        dimension=3,
        representation_class="COMPAT_EMBEDDING",
        generation=1,
        derivation_contract_version="compat-embedding-v1",
        encoding_id="RAW_VECTOR",
        dtype="float32",
    )


def _scope(connection, *, workspace: str, kind: str, qualifier: str) -> NativeMemoryRuntimeScope:
    identity, semantic, source = _id(), _id(), _id()
    for table, identifier, label in (
        ("identity_namespaces", identity, f"7g5e4b:identity:{workspace}:{kind}:{qualifier}"),
        ("semantic_scopes", semantic, f"7g5e4b:semantic:{workspace}:{kind}:{qualifier}"),
        ("legacy_source_namespaces", source, f"7g5e4b:source:{workspace}:{kind}:{qualifier}"),
    ):
        connection.execute(
            f"INSERT INTO {table} VALUES (?,?,0)",
            (native_id_to_bytes(identifier), label),
        )
    return NativeMemoryRuntimeScope(
        workspace_id=workspace,
        scope_kind=kind,
        agent_id=qualifier if kind == "PRIVATE_AGENT" else None,
        domain_id=qualifier if kind == "SHARED_DOMAIN" else None,
        legacy_source_namespace_id=source,
        identity_namespace_id=identity,
        semantic_scope_id=semantic,
    )


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "native-memory-vector-runtime.db")
    metadata = create_schema(qualified.connection)
    connection = qualified.connection
    idempotency = _id()
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), "7g5e4b:idempotency"),
    )
    return qualified, connection, native_id_from_bytes(metadata.core_id), idempotency


def _provenance(connection) -> Any:
    identifier = _id()
    connection.execute(
        "INSERT INTO provenance_records VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            native_id_to_bytes(identifier), "RUNTIME_PROVENANCE_V1", "user_input", "user",
            "direct_ingest", "KNOWN", None, None, None, None,
        ),
    )
    return identifier


def _memory(
    connection,
    scope: NativeMemoryRuntimeScope,
    idempotency,
    key: str,
    *,
    summary: str | None = None,
    memory_type: str = "episodic",
    user_id: str = "aria",
    half_life_days: float = 0.0,
    extra_payload: dict[str, Any] | None = None,
):
    return NativeMemoryCompatibilityFacade(connection).create_memory_state(
        legacy_source_namespace_id=scope.legacy_source_namespace_id,
        idempotency_namespace_id=idempotency,
        idempotency_key=f"memory:{scope.qualifier}:{key}",
        identity_namespace_id=scope.identity_namespace_id,
        semantic_scope_id=scope.semantic_scope_id,
        summary=summary or f"memory {key}",
        memory_type=memory_type,
        memory_class="core",
        strength=.7,
        confidence=.8,
        half_life_days=half_life_days,
        user_id=user_id,
        logical_step=12,
        extra_payload=extra_payload or {"tag": key, "step": 12, "ts": 100},
        governance_state="STAGING",
        provenance_id=_provenance(connection),
    )


def _ready(connection, source, idempotency, key: str, vector: Any):
    payload = np.asarray(vector, dtype=np.float32).reshape(-1).tobytes(order="C")
    service = NativeRepresentationService(connection)
    pending = service.create_representation_pending(
        idempotency_namespace_id=idempotency,
        idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3,
            (), None, len(payload),
        ),
    )
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=idempotency,
        idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(),
            INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return service.publish_representation_ready(
        idempotency_namespace_id=idempotency,
        idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", payload,
        ),
    )


def _configuration(qualified, core_id, scope) -> NativeMemoryVectorRuntimeConfiguration:
    return NativeMemoryVectorRuntimeConfiguration(
        core_database_path=qualified.database_path,
        expected_core_id=core_id,
        scope=scope,
        representation_lane=_lane(),
    )


def _legacy_graph(tmp_path: Path, connection, scope, sources_and_vectors, embedder: _Embedder) -> MemoryGraph:
    graph = MemoryGraph(str(tmp_path / "legacy"), embedder=embedder)
    # Native compatibility EIDs are namespace-local and begin at zero.  The
    # deterministic differential corpus must therefore use that same frozen
    # source EID sequence rather than SeedWorld's normal interactive default.
    graph.world._next_id = 0
    reads = NativeMemoryCompatibilityFacade(connection)
    for source, vector in sources_and_vectors:
        eid = graph.add_memory(
            summary=f"placeholder {source.eid}",
            embedding=np.asarray(vector, dtype=np.float32),
            mtype="episodic",
            strength=.7,
            confidence=.8,
            half_life_days=0.0,
            user_id="aria",
            step=12,
        )
        assert eid == source.eid
        native = reads.get_memory_by_eid(
            legacy_source_namespace_id=scope.legacy_source_namespace_id,
            eid=source.eid,
        )
        graph.entities[eid].payload = dict(native.payload)
        graph._emb_by_eid[eid] = graph._normalize(np.asarray(vector, dtype=np.float32))
    graph._rebuild_matrix()
    return graph


def _runtime(qualified, core_id, scope, *, vector=(1.0, 0.0, 0.0)) -> NativeMemoryVectorRuntime:
    return NativeMemoryVectorRuntime(_configuration(qualified, core_id, scope), embedder=_Embedder(vector))


def test_vector_and_text_search_are_byte_exact_memorygraph_differentials(tmp_path: Path, monkeypatch):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    graph = None
    try:
        scope = _scope(connection, workspace="w", kind="PRIVATE_AGENT", qualifier="aria")
        vectors = (
            (2.0, 0.6, 0.0),
            (1e-12, 3e-13, 0.0),
            (0.6, 0.8, 0.0),
            (-0.4, 0.9, 0.0),
            (1.0, 0.0, 0.0),
        )
        sources = (
            _memory(connection, scope, idempotency, "ordinary", extra_payload={"tag": "ordinary", "step": 12, "ts": 100}),
            _memory(connection, scope, idempotency, "small", user_id="nox", extra_payload={"tag": "small", "step": 12, "ts": 100}),
            _memory(connection, scope, idempotency, "canon", extra_payload={"canon": True, "tag": "canon", "step": 12, "ts": 100}),
            _memory(connection, scope, idempotency, "negative", memory_type="reference", extra_payload={"tag": "negative", "step": 12, "ts": 100}),
            _memory(connection, scope, idempotency, "decayed", half_life_days=1.0, extra_payload={"created_ts": 100, "tag": "decayed", "step": 12, "ts": 100}),
        )
        for index, (source, vector) in enumerate(zip(sources, vectors, strict=True)):
            _ready(connection, source, idempotency, f"vector:{index}", vector)
        legacy_embedder = _Embedder((.7, .4, 0.0))
        graph = _legacy_graph(tmp_path, connection, scope, tuple(zip(sources, vectors, strict=True)), legacy_embedder)
        runtime = _runtime(qualified, core_id, scope, vector=(.7, .4, 0.0))
        monkeypatch.setattr(memory_graph_module, "_now_ts", lambda: 100 + 86400)
        monkeypatch.setattr(vector_runtime_module.time, "time", lambda: float(100 + 86400))

        query = np.asarray((.7, .4, 0.0), dtype=np.float32)
        native_vector = runtime.search_by_embedding(query, top_k=4)
        legacy_vector = graph.search_by_embedding(query, top_k=4)
        assert native_vector == legacy_vector
        assert runtime.snapshot is not None and graph._emb_mat is not None
        assert [row.eid for row in runtime.snapshot.rows] == graph._eid_list
        assert runtime.snapshot.matrix.tobytes() == graph._emb_mat.tobytes()
        normalized_query = graph._normalize(query)
        assert runtime._normalize(query).tobytes() == normalized_query.tobytes()
        assert (
            (runtime.snapshot.matrix @ runtime._normalize(query)).astype(np.float32).tobytes()
            == (graph._emb_mat @ normalized_query).astype(np.float32).tobytes()
        )

        native_filtered = runtime.search_by_embedding(
            query, top_k=3, user_id="aria", type_filter=["episodic"], canon_only=True,
        )
        legacy_filtered = graph.search_by_embedding(
            query, top_k=3, user_id="aria", type_filter=["episodic"], canon_only=True,
        )
        assert native_filtered == legacy_filtered

        native_text = runtime.search("  frozen query  ", top_k=4)
        legacy_text = graph.search("  frozen query  ", top_k=4)
        assert native_text == legacy_text
        assert runtime._embedder.calls == ["frozen query"]
        assert legacy_embedder.calls == ["frozen query"]
    finally:
        if runtime is not None:
            runtime.close()
        if graph is not None:
            graph.close()
        qualified.close()


def test_edge_normalization_argpartition_and_atomic_invalidation_match_memorygraph(tmp_path: Path):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    graph = None
    try:
        scope = _scope(connection, workspace="w", kind="PRIVATE_AGENT", qualifier="aria")
        vectors = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (-1.0, 0.0, 0.0))
        sources = tuple(_memory(connection, scope, idempotency, f"edge:{index}") for index in range(len(vectors)))
        for index, (source, vector) in enumerate(zip(sources, vectors, strict=True)):
            _ready(connection, source, idempotency, f"edge-vector:{index}", vector)
        embedder = _Embedder((1.0, 0.0, 0.0))
        graph = _legacy_graph(tmp_path, connection, scope, tuple(zip(sources, vectors, strict=True)), embedder)
        runtime = _runtime(qualified, core_id, scope)
        for query, top_k in (
            (np.asarray((1.0,), dtype=np.float32), 2),
            (np.asarray((1.0, 0.0, 0.0, 99.0), dtype=np.float32), 2),
            (np.asarray((0.0, 0.0, 0.0), dtype=np.float32), 8),
            (np.asarray((1.0, 0.0, 0.0), dtype=np.float32), 2),
        ):
            assert runtime.search_by_embedding(query, top_k=top_k) == graph.search_by_embedding(query, top_k=top_k)
        assert runtime.search_by_embedding((), top_k=3) == graph.search_by_embedding((), top_k=3) == []
        before = runtime.rebuild_count
        runtime.invalidate("qualified-writer-published")
        assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=2) == graph.search_by_embedding((1.0, 0.0, 0.0), top_k=2)
        assert runtime.rebuild_count == before + 1
        assert runtime.last_invalidation_reason is None
    finally:
        if runtime is not None:
            runtime.close()
        if graph is not None:
            graph.close()
        qualified.close()


def test_current_revision_and_representation_integrity_changes_refuse_stale_rows(tmp_path: Path, monkeypatch):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    try:
        scope = _scope(connection, workspace="w", kind="PRIVATE_AGENT", qualifier="aria")
        r1 = _memory(connection, scope, idempotency, "reinforced")
        e1 = _ready(connection, r1, idempotency, "r1", (1.0, 0.0, 0.0))
        runtime = _runtime(qualified, core_id, scope)
        assert [hit["eid"] for hit in runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=3)] == [r1.eid]
        assert runtime.snapshot is not None and runtime.snapshot.rows[0].representation_id == e1.representation_id

        r2 = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=scope.legacy_source_namespace_id,
            eid=r1.eid,
            patch={"strength": .9},
            idempotency_namespace_id=idempotency,
            idempotency_key="reinforced:r2",
            expected_revision_id=r1.revision_id,
        )
        assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=3) == []
        assert runtime.snapshot is not None and runtime.snapshot.rows == ()

        e2 = _ready(connection, r2, idempotency, "r2", (.0, 1.0, .0))
        assert runtime.search_by_embedding((0.0, 1.0, 0.0), top_k=3)[0]["eid"] == r1.eid
        assert runtime.snapshot is not None and runtime.snapshot.rows[0].representation_id == e2.representation_id

        from torment_service.substrate import representations as representations_module

        original_measure = representations_module._measure_payload
        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        verification = NativeRepresentationService(connection).verify_published_representation_integrity(
            idempotency_namespace_id=idempotency,
            idempotency_key="r2:later-mismatch",
            request=RepresentationIntegrityVerificationRequest(e2.representation_id, "test mismatch"),
        )
        assert verification.result == "MISMATCH"
        assert runtime.search_by_embedding((0.0, 1.0, 0.0), top_k=3) == []
        assert runtime.snapshot is not None and runtime.snapshot.rows == ()
        monkeypatch.setattr(representations_module, "_measure_payload", original_measure)
        r3 = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=scope.legacy_source_namespace_id,
            eid=r1.eid,
            patch={"strength": .95},
            idempotency_namespace_id=idempotency,
            idempotency_key="reinforced:r3",
            expected_revision_id=r2.revision_id,
        )
        e3 = _ready(connection, r3, idempotency, "r3-restored", (0.0, 1.0, 0.0))
        assert runtime.search_by_embedding((0.0, 1.0, 0.0), top_k=3)[0]["eid"] == r1.eid
        assert runtime.snapshot is not None and runtime.snapshot.rows[0].representation_id == e3.representation_id
    finally:
        if runtime is not None:
            runtime.close()
        qualified.close()


def test_invariant_failed_rebuild_refuses_partial_or_stale_snapshot(tmp_path: Path, monkeypatch):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    try:
        scope = _scope(connection, workspace="atomic", kind="PRIVATE_AGENT", qualifier="aria")
        source = _memory(connection, scope, idempotency, "atomic")
        _ready(connection, source, idempotency, "atomic", (1.0, 0.0, 0.0))
        runtime = _runtime(qualified, core_id, scope)
        assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        prior = runtime.snapshot
        assert prior is not None and prior.matrix is not None
        prior_bytes = prior.matrix.tobytes()

        def broken_vectors():
            raise SubstrateInvariantViolation("test candidate invariant failure")

        monkeypatch.setattr(runtime, "_enumerate_qualified_vectors", broken_vectors)
        runtime.invalidate("test invariant failure")
        assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4) == []
        assert runtime.snapshot is None
        assert prior.matrix.tobytes() == prior_bytes

        monkeypatch.setattr(runtime, "_enumerate_qualified_vectors", runtime.__class__._enumerate_qualified_vectors.__get__(runtime))
        assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        assert runtime.snapshot is not None and runtime.snapshot.matrix is not None
        assert runtime.snapshot.matrix.tobytes() == prior_bytes
    finally:
        if runtime is not None:
            runtime.close()
        qualified.close()


@pytest.mark.parametrize("top_k", (1, 8, 32))
def test_warm_selected_results_use_one_batched_read_transaction(tmp_path: Path, monkeypatch, top_k: int):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    try:
        scope = _scope(connection, workspace=f"batch-{top_k}", kind="PRIVATE_AGENT", qualifier="aria")
        vector = _seed_scale_lane(connection, scope, idempotency, 64)
        runtime = _runtime(qualified, core_id, scope, vector=vector)
        assert len(runtime.search_by_embedding(vector, top_k=top_k)) == top_k

        def forbidden_single_row_lookup(*_args, **_kwargs):
            raise AssertionError("warm selected projection must not perform an N+1 lookup")

        monkeypatch.setattr(runtime._compatibility, "get_memory_by_eid", forbidden_single_row_lookup)
        monkeypatch.setattr(runtime._embeddings, "read_current", forbidden_single_row_lookup)
        statements: list[str] = []
        runtime._connection.set_trace_callback(statements.append)
        try:
            hits = runtime.search_by_embedding(vector, top_k=top_k)
        finally:
            runtime._connection.set_trace_callback(None)
        assert len(hits) == top_k
        begin = next(index for index, statement in enumerate(statements) if statement.strip().upper() == "BEGIN")
        commit = next(index for index, statement in enumerate(statements) if statement.strip().upper() == "COMMIT")
        post_selection = statements[begin:commit + 1]
        assert len(post_selection) == 5
        assert post_selection[0].strip().upper() == "BEGIN"
        assert post_selection[-1].strip().upper() == "COMMIT"
        assert sum(statement.lstrip().upper().startswith(("SELECT", "WITH")) for statement in post_selection) == 3
    finally:
        if runtime is not None:
            runtime.close()
        qualified.close()


def test_concurrent_writer_returns_one_read_snapshot_then_next_query_refuses_stale_rows(tmp_path: Path):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    try:
        scope = _scope(connection, workspace="race", kind="PRIVATE_AGENT", qualifier="aria")
        r1 = _memory(connection, scope, idempotency, "r1")
        _ready(connection, r1, idempotency, "r1", (1.0, 0.0, 0.0))
        entered_read_snapshot = threading.Event()
        allow_projection = threading.Event()
        completed = threading.Event()
        observed: dict[str, Any] = {}

        def query_in_reader_thread() -> None:
            runtime = None
            try:
                runtime = _runtime(qualified, core_id, scope)
                assert runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
                original_validate = runtime._embeddings.validate_current_witnesses

                def pause_after_read_snapshot(*args, **kwargs):
                    result = original_validate(*args, **kwargs)
                    entered_read_snapshot.set()
                    if not allow_projection.wait(timeout=5):
                        raise TimeoutError("writer did not complete during the reader snapshot")
                    return result

                runtime._embeddings.validate_current_witnesses = pause_after_read_snapshot
                observed["during"] = runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
                observed["after"] = runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
            except BaseException as exc:  # capture thread failures as test evidence
                observed["error"] = exc
            finally:
                if runtime is not None:
                    runtime.close()
                completed.set()

        reader = threading.Thread(target=query_in_reader_thread, daemon=True)
        reader.start()
        assert entered_read_snapshot.wait(timeout=5)
        r2 = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=scope.legacy_source_namespace_id,
            eid=r1.eid,
            patch={"strength": .9},
            idempotency_namespace_id=idempotency,
            idempotency_key="race:r2",
            expected_revision_id=r1.revision_id,
        )
        assert r2.revision_id != r1.revision_id
        allow_projection.set()
        assert completed.wait(timeout=5)
        reader.join(timeout=1)
        assert "error" not in observed
        assert [item["eid"] for item in observed["during"]] == [r1.eid]
        assert observed["during"][0]["strength"] == .7
        assert observed["after"] == []
    finally:
        qualified.close()


def test_cold_runtime_rebuild_uses_only_core_path_scope_and_lane(tmp_path: Path):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    try:
        scope = _scope(connection, workspace="cold", kind="PRIVATE_AGENT", qualifier="aria")
        source = _memory(connection, scope, idempotency, "cold")
        _ready(connection, source, idempotency, "cold", (.6, .8, .0))
        code = """
import json
from uuid import UUID
from torment_service.substrate.native_memory_vector_runtime import NativeMemoryVectorRuntime, NativeMemoryVectorRuntimeConfiguration
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
import numpy as np
class Embedder:
    provider = '7g5e4b-test'
    model = 'frozen-float32'
    dim = 3
    def embed(self, text): return np.asarray((.6,.8,0), dtype=np.float32)
scope = NativeMemoryRuntimeScope(workspace_id={workspace!r}, scope_kind='PRIVATE_AGENT', agent_id={agent!r}, legacy_source_namespace_id=UUID({source!r}), identity_namespace_id=UUID({identity!r}), semantic_scope_id=UUID({semantic!r}))
lane = NativeRepresentationLane(provider='7g5e4b-test', model='frozen-float32', dimension=3, representation_class='COMPAT_EMBEDDING', generation=1, derivation_contract_version='compat-embedding-v1', encoding_id='RAW_VECTOR', dtype='float32')
runtime = NativeMemoryVectorRuntime(NativeMemoryVectorRuntimeConfiguration({path!r}, UUID({core!r}), scope, lane), embedder=Embedder())
try:
    hits = runtime.search('cold', top_k=4)
    snapshot = runtime.snapshot
    print(json.dumps({{'eids': [hit['eid'] for hit in hits], 'matrix': snapshot.matrix.tolist(), 'rows': [row.eid for row in snapshot.rows]}}))
finally:
    runtime.close()
""".format(
            workspace=scope.workspace_id,
            agent=scope.agent_id,
            source=str(scope.legacy_source_namespace_id),
            identity=str(scope.identity_namespace_id),
            semantic=str(scope.semantic_scope_id),
            path=str(qualified.database_path),
            core=str(core_id),
        )
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(Path.cwd()) + os.pathsep + environment.get("PYTHONPATH", "")
        completed = subprocess.run(
            [sys.executable, "-c", code], cwd=Path.cwd(), env=environment,
            check=True, capture_output=True, text=True,
        )
        observed = json.loads(completed.stdout)
        assert observed["eids"] == [source.eid]
        assert observed["rows"] == [source.eid]
        assert np.array_equal(np.asarray(observed["matrix"], dtype=np.float32), np.asarray(((.6, .8, .0),), dtype=np.float32))
    finally:
        qualified.close()


def test_private_and_synthetic_shared_lanes_isolate_overlapping_eids_and_motif_changes(tmp_path: Path):
    qualified, connection, core_id, idempotency = _database(tmp_path)
    private_runtime = shared_runtime = None
    try:
        private = _scope(connection, workspace="multi", kind="PRIVATE_AGENT", qualifier="aria")
        shared = _scope(connection, workspace="multi", kind="SHARED_DOMAIN", qualifier="reflection")
        private_source = _memory(connection, private, idempotency, "private")
        private_split_candidate = _memory(connection, private, idempotency, "private-split-candidate")
        shared_source = _memory(connection, shared, idempotency, "shared")
        _ready(connection, private_source, idempotency, "private", (1.0, 0.0, 0.0))
        _ready(connection, shared_source, idempotency, "shared", (0.0, 1.0, 0.0))
        assert (private_source.eid, shared_source.eid) == (0, 0)
        private_runtime = _runtime(qualified, core_id, private)
        shared_runtime = _runtime(qualified, core_id, shared)
        private_hits = private_runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        shared_hits = shared_runtime.search_by_embedding((0.0, 1.0, 0.0), top_k=4)
        assert [hit["summary"] for hit in private_hits] == ["memory private"]
        assert [hit["summary"] for hit in shared_hits] == ["memory shared"]
        shared_rebuilds = shared_runtime.rebuild_count
        private_rebuilds_before_invalidation = private_runtime.rebuild_count
        private_runtime.invalidate("private-writer")
        assert private_runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        assert private_runtime.rebuild_count == private_rebuilds_before_invalidation + 1
        assert shared_runtime.search_by_embedding((0.0, 1.0, 0.0), top_k=4)
        assert shared_runtime.rebuild_count == shared_rebuilds

        motif_identity, membership_identity, motif_alias = _id(), _id(), _id()
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(motif_identity), "7g5e4b:motif-identity"))
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(membership_identity), "7g5e4b:membership-identity"))
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(motif_alias), "7g5e4b:motif-alias"))
        motifs = NativeMotifService(connection)
        created = motifs.create_motif_with_member(
            idempotency_namespace_id=idempotency,
            idempotency_key="motif-only-create",
            motif_identity_namespace_id=motif_identity,
            membership_identity_namespace_id=membership_identity,
            motif_alias_namespace_id=motif_alias,
            state=MotifState(
                private.semantic_scope_id, "motif_0001", "reflection", "test motif",
                (1.0, 0.0, 0.0), .7, .8, ("aria",), 1, 2,
            ),
            member_object_id=private_source.object_id,
        )
        assert created.motif_object_id
        private_rebuilds = private_runtime.rebuild_count
        assert private_runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        assert private_runtime.rebuild_count == private_rebuilds
        advanced = motifs.advance_motif_state(
            idempotency_namespace_id=idempotency,
            idempotency_key="motif-only-advance",
            motif_alias_namespace_id=motif_alias,
            motif_object_id=created.motif_object_id,
            expected_motif_revision_id=created.motif_revision_id,
            state=MotifState(
                private.semantic_scope_id, "motif_0001", "reflection", "test motif",
                (1.0, 0.0, 0.0), .75, .8, ("aria",), 1, 3,
            ),
        )
        assert advanced.motif_revision_ordinal == 2
        assert private_runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        assert private_runtime.rebuild_count == private_rebuilds
        current = motifs.get_current_motif(created.motif_object_id)
        child = MotifState(
            private.semantic_scope_id, "motif_0002", "reflection", "split child",
            (1.0, 0.0, 0.0), .75, .8, ("aria",), 4, 4,
        )
        split = motifs.split_motif_with_member(
            idempotency_namespace_id=idempotency,
            idempotency_key="motif-only-split",
            motif_identity_namespace_id=motif_identity,
            membership_identity_namespace_id=membership_identity,
            motif_alias_namespace_id=motif_alias,
            plan=NativeMotifSplitPlan(
                created.motif_object_id,
                current.motif_revision_id,
                MotifState(
                    private.semantic_scope_id, "motif_0001", "reflection", "test motif",
                    (1.0, 0.0, 0.0), .75, .8, ("aria",), 1, 4,
                ),
                child,
                (private_source.object_id,),
                private_split_candidate.object_id,
                True,
            ),
        )
        assert split.retired_membership_relationship_ids
        assert private_runtime.search_by_embedding((1.0, 0.0, 0.0), top_k=4)
        assert private_runtime.rebuild_count == private_rebuilds
    finally:
        if private_runtime is not None:
            private_runtime.close()
        if shared_runtime is not None:
            shared_runtime.close()
        qualified.close()


def _seed_scale_lane(connection, scope, idempotency, count: int) -> np.ndarray:
    """Build a transient, structurally qualified corpus without writer timing.

    This is a scale-only fixture, not a semantic-write benchmark: the normal
    compatibility write/READY path establishes the first row, then bulk rows
    reproduce that qualified durable shape inside transactions.  The runtime
    still exercises its real SQLite enumeration, qualified representation
    reads, witness validation, matrix construction, and warm search path.
    """
    if count < 1:
        raise ValueError("scale count must be positive")
    base = _memory(connection, scope, idempotency, "scale-base")
    vector = np.asarray((.6, .8, .0), dtype=np.float32)
    _ready(connection, base, idempotency, "scale-base", vector)
    payload_text = connection.execute(
        "SELECT payload_text FROM object_revisions WHERE object_revision_id=?",
        (native_id_to_bytes(base.revision_id),),
    ).fetchone()[0]
    provenance_id = connection.execute(
        "SELECT provenance_id FROM object_revisions WHERE object_revision_id=?",
        (native_id_to_bytes(base.revision_id),),
    ).fetchone()[0]
    vector_bytes = vector.tobytes(order="C")
    digest = sha256(vector_bytes).digest()
    namespace = native_id_to_bytes(scope.legacy_source_namespace_id)
    identity = native_id_to_bytes(scope.identity_namespace_id)
    semantic = native_id_to_bytes(scope.semantic_scope_id)

    # This test characterizes reader scale, not the cost of 50k semantic
    # admissions.  The rows below are structurally identical qualified rows;
    # avoid paying SQLite's per-insert foreign-key lookup for the artificial
    # bulk fixture, then restore enforcement and validate the completed graph
    # before the runtime gets its independent reader connection.
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    connection.execute("PRAGMA foreign_keys=OFF")
    for first in range(1, count, 1_000):
        last = min(count, first + 1_000)
        objects = []
        revisions = []
        aliases = []
        orders = []
        representations = []
        payloads = []
        expectations = []
        measurements = []
        states = []
        for eid in range(first, last):
            object_id, revision_id, representation_id, expectation_id, measurement_id = (
                native_id_to_bytes(_id()) for _ in range(5)
            )
            objects.append((object_id, identity, "LEGACY_CORE_NODE", None, revision_id, 1, 0))
            revisions.append((
                revision_id, object_id, 1, "NATIVE_CREATION", None, None, semantic,
                "EXISTS", "UNSET", 0, None, None, None, "STAGING", "NOT_APPLICABLE",
                provenance_id, "JSON", payload_text, None, 0,
            ))
            aliases.append((namespace, "EID", str(eid), object_id))
            orders.append((namespace, object_id, eid))
            representations.append((
                representation_id, "OBJECT_REVISION", object_id, revision_id, 1,
                None, None, None, "COMPAT_EMBEDDING", 1, "compat-embedding-v1",
                "RAW_VECTOR", "float32", 3, len(vector_bytes), 0,
            ))
            payloads.append((representation_id, vector_bytes, len(vector_bytes), 0))
            expectations.append((
                expectation_id, "REPRESENTATION", None, None, None, None, None, None,
                representation_id, INTEGRITY_ALGORITHM_SHA256, digest, INTEGRITY_VALUE_ENCODING_RAW, 0,
            ))
            measurements.append((measurement_id, expectation_id, "MATCH", digest, None, 0))
            states.append((representation_id, "READY", "USABLE", measurement_id))
        connection.execute("BEGIN")
        try:
            connection.executemany(
                """INSERT INTO objects(
                    object_id,identity_namespace_id,object_kind,creating_transition_id,current_revision_id,
                    current_revision_ordinal,created_at_ns
                ) VALUES (?,?,?,?,?,?,?)""",
                objects,
            )
            connection.executemany(
                """INSERT INTO object_revisions(
                    object_revision_id,object_id,revision_ordinal,lineage_kind,predecessor_revision_id,
                    predecessor_revision_ordinal,effective_semantic_scope_id,existence_state,lifecycle_state,
                    lifecycle_authoritative,lifecycle_actor,lifecycle_via,lifecycle_set_at_ns,governance_state,
                    authority_category,provenance_id,payload_format,payload_text,payload_blob,created_at_ns
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                revisions,
            )
            connection.executemany("INSERT INTO legacy_object_aliases VALUES (?,?,?,?)", aliases)
            connection.executemany("INSERT INTO memory_runtime_enumeration_orders VALUES (?,?,?)", orders)
            connection.executemany(
                """INSERT INTO representations(
                    representation_id,source_kind,source_object_id,source_object_revision_id,
                    source_object_revision_ordinal,source_relationship_id,source_relationship_revision_id,
                    source_relationship_revision_ordinal,representation_class,generation,
                    derivation_contract_version,encoding_id,dtype,dimension,
                    expected_payload_byte_length,created_at_ns
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                representations,
            )
            connection.executemany("INSERT INTO representation_payloads VALUES (?,?,?,?)", payloads)
            connection.executemany(
                """INSERT INTO integrity_expectations(
                    expectation_id,subject_kind,object_id,object_revision_id,object_revision_ordinal,
                    relationship_id,relationship_revision_id,relationship_revision_ordinal,representation_id,
                    algorithm_id,expected_value,value_encoding,established_at_ns
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                expectations,
            )
            connection.executemany("INSERT INTO integrity_measurements VALUES (?,?,?,?,?,?)", measurements)
            connection.executemany("INSERT INTO representation_current_state VALUES (?,?,?,?)", states)
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            connection.execute("PRAGMA foreign_keys=ON")
            raise
    connection.execute("PRAGMA foreign_keys=ON")
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    return vector


@pytest.mark.skipif(
    os.environ.get("TORMENT_7G5E4B_RUN_SCALE") != "1",
    reason="set TORMENT_7G5E4B_RUN_SCALE=1 for the bounded 1k/10k/50k characterization",
)
@pytest.mark.parametrize("count", (1_000, 10_000, 50_000))
def test_scale_characterization_native_matrix_and_warm_search(tmp_path: Path, count: int):
    """Emit bounded timing evidence; this is characterization, not an SLA."""
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    graph = None
    try:
        scope = _scope(connection, workspace=f"scale-{count}", kind="PRIVATE_AGENT", qualifier="aria")
        vector = _seed_scale_lane(connection, scope, idempotency, count)
        runtime = _runtime(qualified, core_id, scope, vector=vector)
        cold_started = time.perf_counter()
        assert runtime.search_by_embedding(vector, top_k=8)
        native_cold_seconds = time.perf_counter() - cold_started
        assert runtime.snapshot is not None and runtime.snapshot.matrix is not None
        assert runtime.snapshot.matrix.shape == (count, 3)
        assert runtime.snapshot.matrix.dtype == np.float32
        matrix_bytes = runtime.snapshot.matrix.nbytes

        graph = MemoryGraph(str(tmp_path / "legacy-scale"), embedder=_Embedder(vector))
        graph._emb_by_eid = {eid: graph._normalize(vector) for eid in range(count)}
        legacy_rebuild_started = time.perf_counter()
        graph._rebuild_matrix()
        legacy_rebuild_seconds = time.perf_counter() - legacy_rebuild_started
        assert graph._emb_mat is not None and graph._emb_mat.nbytes == matrix_bytes

        repeats = 25
        legacy_started = time.perf_counter()
        for _ in range(repeats):
            graph.search_by_embedding(vector, top_k=8)
        legacy_warm_ms = (time.perf_counter() - legacy_started) * 1_000 / repeats
        native_started = time.perf_counter()
        for _ in range(repeats):
            runtime.search_by_embedding(vector, top_k=8)
        native_warm_ms = (time.perf_counter() - native_started) * 1_000 / repeats
        print(json.dumps({
            "count": count,
            "dimension": 3,
            "native_cold_rebuild_s": round(native_cold_seconds, 6),
            "legacy_matrix_rebuild_s": round(legacy_rebuild_seconds, 6),
            "legacy_warm_search_ms": round(legacy_warm_ms, 6),
            "native_warm_search_ms": round(native_warm_ms, 6),
            "matrix_resident_bytes": matrix_bytes,
        }, sort_keys=True))
    finally:
        if runtime is not None:
            runtime.close()
        if graph is not None:
            graph.close()
        qualified.close()


@pytest.mark.skipif(
    os.environ.get("TORMENT_7G5E4B_RUN_HOT_PATH") != "1",
    reason="set TORMENT_7G5E4B_RUN_HOT_PATH=1 for hot-path component characterization",
)
@pytest.mark.parametrize("count", (1_000, 10_000, 50_000))
@pytest.mark.parametrize("top_k", (1, 8, 32))
def test_hot_path_component_characterization(tmp_path: Path, monkeypatch, count: int, top_k: int):
    """Emit per-phase warm-query timing without changing runtime behavior."""
    qualified, connection, core_id, idempotency = _database(tmp_path)
    runtime = None
    try:
        scope = _scope(connection, workspace=f"hot-path-{count}-{top_k}", kind="PRIVATE_AGENT", qualifier="aria")
        vector = _seed_scale_lane(connection, scope, idempotency, count)
        runtime = _runtime(qualified, core_id, scope, vector=vector)
        assert runtime.search_by_embedding(vector, top_k=top_k)
        assert runtime.snapshot is not None and runtime.snapshot.matrix is not None
        elapsed = {"batch": 0.0, "compatibility": 0.0, "embedding": 0.0}

        original_batch = runtime._batch_project_current_rows
        original_compatibility = runtime._compatibility.get_memories_by_eids
        original_embedding = runtime._embeddings.validate_current_witnesses

        def timed_batch(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original_batch(*args, **kwargs)
            finally:
                elapsed["batch"] += time.perf_counter() - started

        def timed_compatibility(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original_compatibility(*args, **kwargs)
            finally:
                elapsed["compatibility"] += time.perf_counter() - started

        def timed_embedding(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original_embedding(*args, **kwargs)
            finally:
                elapsed["embedding"] += time.perf_counter() - started

        monkeypatch.setattr(runtime, "_batch_project_current_rows", timed_batch)
        monkeypatch.setattr(runtime._compatibility, "get_memories_by_eids", timed_compatibility)
        monkeypatch.setattr(runtime._embeddings, "validate_current_witnesses", timed_embedding)

        repeats = 10
        matrix_started = time.perf_counter()
        for _ in range(repeats):
            query = runtime._normalize(vector)
            scores = (runtime.snapshot.matrix @ query).astype(np.float32)
            if int(scores.shape[0]) <= top_k:
                np.argsort(-scores)
            else:
                candidates = np.argpartition(-scores, top_k - 1)[:top_k]
                candidates[np.argsort(-scores[candidates])]
        matrix_top_k_ms = (time.perf_counter() - matrix_started) * 1_000 / repeats

        total_started = time.perf_counter()
        for _ in range(repeats):
            assert runtime.search_by_embedding(vector, top_k=top_k)
        total_warm_ms = (time.perf_counter() - total_started) * 1_000 / repeats
        print(json.dumps({
            "phase": os.environ.get("TORMENT_7G5E4B_HOT_PATH_PHASE", "unspecified"),
            "count": count,
            "top_k": top_k,
            "matrix_top_k_ms": round(matrix_top_k_ms, 6),
            "batch_transaction_total_ms": round(elapsed["batch"] * 1_000 / repeats, 6),
            "compatibility_projection_ms": round(elapsed["compatibility"] * 1_000 / repeats, 6),
            "batch_currentness_ms": round(elapsed["embedding"] * 1_000 / repeats, 6),
            "native_total_warm_ms": round(total_warm_ms, 6),
        }, sort_keys=True))
    finally:
        if runtime is not None:
            runtime.close()
        qualified.close()
