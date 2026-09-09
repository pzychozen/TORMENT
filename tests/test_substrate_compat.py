"""Focused Phase 7G1 native-only compatibility read tests."""
from __future__ import annotations
from pathlib import Path

import pytest

from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope, idempotency = _id(), _id(), _id()
    connection.execute(
        "INSERT INTO identity_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(identity), "compat-objects"),
    )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(scope), "compat-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(idempotency), "compat-idempotency"),
    )
    return qualified, identity, scope, idempotency


def _source_namespace(connection, key: str):
    source = _id()
    connection.execute(
        "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
        (native_id_to_bytes(source), key),
    )
    return source


def _native_memory(facade, identity, scope, idempotency, source, key: str, *, summary: str = "R1 summary"):
    return facade.create_memory_state(
        legacy_source_namespace_id=source,
        idempotency_namespace_id=idempotency,
        idempotency_key=f"memory:{key}",
        identity_namespace_id=identity,
        semantic_scope_id=scope,
        summary=summary,
        memory_type="episodic",
        memory_class="core",
        strength=0.7,
        confidence=0.8,
        half_life_days=5.0,
        user_id="owner",
        logical_step=5,
        governance_state="STAGING",
    )

def test_namespaced_eid_projection_is_native_structural_and_read_only(tmp_path: Path, monkeypatch):
    qualified, identity, scope, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _source_namespace(connection, "source-a")
        r1 = _native_memory(facade, identity, scope, idempotency, source, "source-a")
        before = (
            connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0],
            connection.execute("SELECT count(*) FROM operations").fetchone()[0],
        )
        view = facade.get_memory_by_eid(legacy_source_namespace_id=source, eid=r1.eid)
        assert facade.resolve_memory_eid(legacy_source_namespace_id=source, eid=r1.eid) == r1.object_id
        assert facade.resolve_native_memory_legacy_eid(
            legacy_source_namespace_id=source, native_object_id=r1.object_id,
        ) == r1.eid
        record = view.to_legacy_dict()
        assert record["summary"] == "R1 summary" and record["strength"] == 0.7 and record["created_at"] == 5
        assert record["representation_refs"] == []
        assert before == (
            connection.execute("SELECT count(*) FROM semantic_transitions").fetchone()[0],
            connection.execute("SELECT count(*) FROM operations").fetchone()[0],
        )
        monkeypatch.setattr(
            Path,
            "open",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("compatibility read opened a legacy file")),
        )
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source, eid=r1.eid).object_id == r1.object_id
    finally:
        qualified.close()


def test_stable_eid_follows_current_native_revision_and_exact_old_revision_remains_readable(tmp_path: Path):
    qualified, identity, scope, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _source_namespace(connection, "source-r1")
        r1 = _native_memory(facade, identity, scope, idempotency, source, "source-r1")
        r2 = facade.patch_memory_state(
            legacy_source_namespace_id=source,
            eid=r1.eid,
            patch={"summary": "R2 summary", "strength": 0.2},
            idempotency_namespace_id=idempotency,
            idempotency_key="compat-r2",
            expected_revision_id=r1.revision_id,
        )
        current = facade.get_memory_by_eid(legacy_source_namespace_id=source, eid=r1.eid)
        old = facade.get_memory_revision(
            legacy_source_namespace_id=source, eid=r1.eid, revision_id=r1.revision_id,
        )
        assert current.revision_id == r2.revision_id and current.summary == "R2 summary"
        assert old.revision_id == r1.revision_id and old.summary == "R1 summary"
        assert facade.resolve_memory_eid(legacy_source_namespace_id=source, eid=r1.eid) == r1.object_id
    finally:
        qualified.close()


def test_same_eid_is_safe_across_namespaces_and_missing_or_wrong_carrier_fails_closed(tmp_path: Path):
    qualified, identity, scope, idempotency = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source_a = _source_namespace(connection, "source-a")
        source_b = _source_namespace(connection, "source-b")
        a = _native_memory(facade, identity, scope, idempotency, source_a, "source-a")
        b = _native_memory(facade, identity, scope, idempotency, source_b, "source-b")
        assert (a.eid, b.eid) == (0, 0)
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=0).object_id == a.object_id
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_b, eid=0).object_id == b.object_id
        assert a.object_id != b.object_id
        count = connection.execute("SELECT count(*) FROM objects").fetchone()[0]
        with pytest.raises(SubstrateObjectNotFound):
            facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=999)
        assert connection.execute("SELECT count(*) FROM objects").fetchone()[0] == count
        nonmemory = NativeObjectService(connection).create_object(
            idempotency_namespace_id=idempotency,
            idempotency_key="identity",
            state=ObjectState(
                identity, scope, "LEGACY_AGENT_IDENTITY", "EXISTS", "UNKNOWN", False,
                "UNKNOWN", "NOT_APPLICABLE", {"x": 1}, "JSON",
            ),
        )
        connection.execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (native_id_to_bytes(source_a), "EID", "8", native_id_to_bytes(nonmemory.object_id)),
        )
        with pytest.raises(SubstrateInvariantViolation):
            facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=8)
    finally:
        qualified.close()

def test_facade_has_no_search_or_write_surface(tmp_path:Path):
    q,obj,scope,idem=_database(tmp_path)
    try:
      f=NativeMemoryCompatibilityFacade(q.connection)
      assert not hasattr(f,'search') and not hasattr(f,'spawn_memory') and not hasattr(f,'update_payload') and not hasattr(f,'flush_node')
    finally: q.close()
