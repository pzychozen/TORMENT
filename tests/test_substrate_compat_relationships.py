"""Focused Phase 7G3A native compatibility LINK tests on STAGING cores."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
    SubstrateObjectNotFound,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.objects import NativeObjectService, ObjectState
from torment_service.substrate.schema import CORE_ROLE_STAGING, create_schema, open_schema


def _id(): return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat-relationships.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identity, scope_a, scope_b, idem, source_a, source_b = (_id() for _ in range(6))
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(identity), "compat-relationships-identities"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope_a), "compat-relationships-scope-a"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope_b), "compat-relationships-scope-b"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "compat-relationships-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_a), "compat-relationships-source-a"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_b), "compat-relationships-source-b"))
    return qualified, identity, scope_a, scope_b, idem, source_a, source_b


def _memory(facade, identity, scope, idem, source, key, **overrides):
    values = {
        "summary": f"memory {key}", "memory_type": "episodic", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 5.0,
        "user_id": "compat", "logical_step": 12, "extra_payload": {"tag": key},
    }
    values.update(overrides)
    return facade.create_memory_state(
        legacy_source_namespace_id=source, idempotency_namespace_id=idem,
        idempotency_key=f"memory:{key}", identity_namespace_id=identity,
        semantic_scope_id=scope, **values,
    )


def _link(facade, identity, scope, idem, source_a, source_eid, source_b, target_eid, key="link-1", **overrides):
    values = {"relationship_kind": "LINK", "weight": 0.75, "legacy_timestamp": 1234.5, "extra_payload": {"domain": "memory"}}
    values.update(overrides)
    return facade.create_memory_relationship(
        source_legacy_source_namespace_id=source_a, source_eid=source_eid,
        target_legacy_source_namespace_id=source_b, target_eid=target_eid,
        idempotency_namespace_id=idem, idempotency_key=key,
        identity_namespace_id=identity, semantic_scope_id=scope, **values,
    )


def _relationship_counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "relationships", "relationship_revisions", "relationship_revision_endpoints",
        "relationship_revision_effects", "semantic_transitions", "operations",
    ))


def test_native_link_uses_scoped_eids_identity_endpoints_and_no_file_shadow(tmp_path: Path, monkeypatch):
    qualified, identity, scope_a, scope_b, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        assert open_schema(connection).core_role == CORE_ROLE_STAGING
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "source", governance_state="STAGING")
        target = _memory(facade, identity, scope_b, idem, source_b, "target")
        assert source.eid == target.eid == 0 and source.object_id != target.object_id
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("compatibility LINK opened a legacy file")))
        first = _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, governance_state="STAGING")
        assert _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, governance_state="STAGING") == first
        assert connection.execute("SELECT relationship_kind,current_revision_id,current_revision_ordinal FROM relationships WHERE relationship_id=?", (native_id_to_bytes(first.relationship_id),)).fetchone() == ("LINK", native_id_to_bytes(first.revision_id), 1)
        assert connection.execute("SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,governance_state,authority_category,payload_format FROM relationship_revisions WHERE relationship_revision_id=?", (native_id_to_bytes(first.revision_id),)).fetchone() == ("NATIVE_CREATION", None, None, "STAGING", "NOT_APPLICABLE", "JSON")
        assert connection.execute("SELECT endpoint_ordinal,endpoint_role,endpoint_semantic_scope_id,object_id,binding_mode,bound_object_revision_id FROM relationship_revision_endpoints WHERE relationship_revision_id=? ORDER BY endpoint_ordinal", (native_id_to_bytes(first.revision_id),)).fetchall() == [
            (0, "SOURCE", native_id_to_bytes(scope_a), native_id_to_bytes(source.object_id), "IDENTITY", None),
            (1, "TARGET", native_id_to_bytes(scope_b), native_id_to_bytes(target.object_id), "IDENTITY", None),
        ]
        assert connection.execute("SELECT origin_kind,transition_kind FROM semantic_transitions WHERE transition_id=?", (native_id_to_bytes(first.transition_id),)).fetchone() == ("NATIVE", "RELATIONSHIP_REVISION")
        assert connection.execute("SELECT count(*) FROM relationship_revision_effects WHERE transition_id=? AND relationship_id=? AND relationship_revision_id=?", (native_id_to_bytes(first.transition_id), native_id_to_bytes(first.relationship_id), native_id_to_bytes(first.revision_id))).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM operation_outputs WHERE operation_id=? AND output_kind='RELATIONSHIP' AND relationship_id=? AND relationship_revision_id=?", (native_id_to_bytes(first.operation_id), native_id_to_bytes(first.relationship_id), native_id_to_bytes(first.revision_id))).fetchone()[0] == 1
        assert not (tmp_path / "edges.jsonl").exists()
        view = facade.get_memory_relationship(
            relationship_id=first.relationship_id,
            source_legacy_source_namespace_id=source_a,
            target_legacy_source_namespace_id=source_b,
        )
        assert (view.source_eid, view.target_eid, view.weight, view.legacy_timestamp, view.payload["domain"]) == (0, 0, 0.75, 1234.5, "memory")
        with pytest.raises(SubstrateObjectNotFound):
            facade.get_memory_relationship(
                relationship_id=first.relationship_id,
                source_legacy_source_namespace_id=source_b,
                target_legacy_source_namespace_id=source_b,
            )
    finally:
        qualified.close()


def test_link_source_revision_advance_does_not_retarget_identity_binding(tmp_path: Path):
    qualified, identity, scope_a, scope_b, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "source")
        target = _memory(facade, identity, scope_b, idem, source_b, "target")
        link = _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid)
        r2 = facade.patch_memory_state(
            legacy_source_namespace_id=source_a, eid=source.eid, patch={"strength": 0.9},
            idempotency_namespace_id=idem, idempotency_key="source-r2", expected_revision_id=source.revision_id,
        )
        assert r2.revision_id != source.revision_id
        assert connection.execute("SELECT current_revision_id,current_revision_ordinal FROM relationships WHERE relationship_id=?", (native_id_to_bytes(link.relationship_id),)).fetchone() == (native_id_to_bytes(link.revision_id), 1)
        assert connection.execute("SELECT binding_mode,bound_object_revision_id FROM relationship_revision_endpoints WHERE relationship_revision_id=? AND endpoint_ordinal=0", (native_id_to_bytes(link.revision_id),)).fetchone() == ("IDENTITY", None)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE relationship_revision_endpoints SET endpoint_role='OTHER' WHERE relationship_revision_id=?", (native_id_to_bytes(link.revision_id),))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM relationship_revisions WHERE relationship_revision_id=?", (native_id_to_bytes(link.revision_id),))
    finally:
        qualified.close()


def test_link_retry_changed_intent_and_independent_same_endpoint_publications(tmp_path: Path):
    qualified, identity, scope_a, scope_b, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "source")
        target = _memory(facade, identity, scope_b, idem, source_b, "target")
        first = _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key="lost-response")
        assert _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key="lost-response") == first
        with pytest.raises(SubstrateIdempotencyConflict):
            _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key="lost-response", weight=0.1)
        second = _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key="independent", weight=0.1)
        assert second.relationship_id != first.relationship_id
        assert _relationship_counts(connection)[:4] == (2, 2, 4, 2)
    finally:
        qualified.close()


def test_link_refuses_drafts_unknown_or_wrong_carriers_without_source_or_relationship_residue(tmp_path: Path):
    qualified, identity, scope_a, scope_b, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        source = _memory(facade, identity, scope_a, idem, source_a, "source")
        target = _memory(facade, identity, scope_b, idem, source_b, "target")
        source_before = facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=source.eid)
        before = _relationship_counts(connection)
        draft = facade.begin_memory_draft(
            legacy_source_namespace_id=source_a, idempotency_namespace_id=idem, idempotency_key="draft",
            identity_namespace_id=identity, semantic_scope_id=scope_a, summary="not committed",
            memory_type="episodic",
        )
        with pytest.raises(ValueError):
            _link(facade, identity, scope_a, idem, source_a, draft.draft_token, source_b, target.eid, key="draft-endpoint")
        with pytest.raises(SubstrateObjectNotFound):
            _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, 99, key="unknown-endpoint")
        for kind, weight in (("OTHER", 0.2), ("LINK", float("nan")), ("LINK", float("inf"))):
            with pytest.raises(ValueError):
                _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key=f"invalid-{kind}-{weight}", relationship_kind=kind, weight=weight)
        for key in ("relationship_id", "endpoints", "source_eid", "binding_mode", "scope", "lifecycle_state", "authority", "authorization", "operation_id", "weight"):
            with pytest.raises(ValueError):
                _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, target.eid, key=f"shadow-{key}", extra_payload={key: "blocked"})
        wrong = NativeObjectService(connection).create_object(
            idempotency_namespace_id=idem, idempotency_key="wrong-carrier",
            state=ObjectState(identity, scope_b, "LEGACY_MOTIF", "EXISTS", "UNSET", True, "UNKNOWN"),
        )
        connection.execute("INSERT INTO legacy_object_aliases VALUES (?,'EID',?,?)", (native_id_to_bytes(source_b), "77", native_id_to_bytes(wrong.object_id)))
        with pytest.raises(SubstrateInvariantViolation):
            _link(facade, identity, scope_a, idem, source_a, source.eid, source_b, 77, key="wrong-carrier")
        assert _relationship_counts(connection)[:4] == before[:4]
        assert facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=source.eid).revision_id == source_before.revision_id
    finally:
        qualified.close()
