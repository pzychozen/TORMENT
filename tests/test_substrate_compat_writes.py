"""Focused Phase 7G2A compatibility create/patch tests on STAGING cores."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from torment_service.candidate_types import CandidateShapedValue
from torment_service.substrate import compat as compat_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateRevisionConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import create_snapshot_manifest
from torment_service.substrate.migration.admission import NativeLegacyObjectAdmissionService
from torment_service.substrate.schema import CORE_ROLE_STAGING, create_schema, open_schema


def _id(): return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "compat-writes.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    identities, scope, idem, source_a, source_b = _id(), _id(), _id(), _id(), _id()
    connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(identities), "compat-writes-identities"))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(scope), "compat-writes-scope"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idem), "compat-writes-idempotency"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_a), "compat-writes-source-a"))
    connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(source_b), "compat-writes-source-b"))
    return qualified, identities, scope, idem, source_a, source_b


def _create(facade, identities, scope, idem, source, key="create-1", **kwargs):
    values = {
        "summary": "ordinary memory", "memory_type": "episodic", "memory_class": "core",
        "strength": 0.7, "confidence": 0.8, "half_life_days": 5.0,
        "user_id": "user-a", "logical_step": 12, "extra_payload": {"tag": "kept"},
    }
    values.update(kwargs)
    return facade.create_memory_state(
        legacy_source_namespace_id=source,
        idempotency_namespace_id=idem,
        idempotency_key=key,
        identity_namespace_id=identities,
        semantic_scope_id=scope,
        **values,
    )


def _counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "object_revisions", "legacy_object_aliases", "semantic_transitions", "representations"))


def test_native_create_allocates_atomic_scoped_alias_and_uses_native_publication(tmp_path: Path, monkeypatch):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        assert open_schema(connection).core_role == CORE_ROLE_STAGING
        facade = NativeMemoryCompatibilityFacade(connection)
        monkeypatch.setattr(Path, "open", lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("compatibility write opened a legacy file")))
        result = _create(
            facade, identities, scope, idem, source_a,
            extra_payload={"tag": "kept", "authority": "approved", "permission": "allow", "pos": [1, 2, 3]},
            lifecycle_status={"state": "protected", "is_authoritative_on_row": True, "requires_join": None, "set_by": {"actor": "system", "via": "ingest", "at": 1}, "history_ref": None},
        )
        assert result.eid == 0 and result.object_id.version == 4
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,lifecycle_state,lifecycle_authoritative,authority_category FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(result.revision_id),)).fetchone() == ("NATIVE_CREATION", None, None, "PROTECTED", 1, "NOT_APPLICABLE")
        assert connection.execute("SELECT origin_kind,transition_kind FROM semantic_transitions WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone() == ("NATIVE", "OBJECT_REVISION")
        assert connection.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM operation_outputs WHERE operation_id=? AND object_id=? AND object_revision_id=?", (native_id_to_bytes(result.operation_id), native_id_to_bytes(result.object_id), native_id_to_bytes(result.revision_id))).fetchone()[0] == 1
        view = facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=result.eid)
        assert view.object_id == result.object_id and view.lifecycle_state == "PROTECTED" and view.authority_category == "NOT_APPLICABLE"
        assert view.payload["authority"] == "approved" and view.payload["pos"] == [1, 2, 3]
    finally:
        qualified.close()


def test_allocation_continues_after_migrated_high_eid_and_isolated_by_namespace(tmp_path: Path):
    qualified, identities, scope, idem, source_a, source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        for source, name in ((source_a, "source-a"), (source_b, "source-b")):
            capsule = tmp_path / name
            root = capsule / "snapshot"
            root.mkdir(parents=True)
            (root / "nodes.jsonl").write_text(
                "".join(json.dumps({"eid": eid, "summary": f"legacy {eid}"}) + "\n" for eid in (1, 2, 8)),
                encoding="utf-8",
            )
            manifest = create_snapshot_manifest(snapshot_root=root, manifest_path=capsule / "manifest.json", legacy_source_namespace_id=source, legacy_source_namespace_key=f"compat-writes-{name}")
            NativeLegacyObjectAdmissionService(connection).admit_nodes_current_state(snapshot_root=root, manifest_path=capsule / "manifest.json", idempotency_namespace_id=idem, object_identity_namespace_id=identities, unknown_semantic_scope_id=scope)
            assert manifest.legacy_source_namespace_id == source
        a = _create(facade, identities, scope, idem, source_a, key="create-after-a")
        b = _create(facade, identities, scope, idem, source_b, key="create-after-b")
        assert (a.eid, b.eid) == (9, 9)
        assert a.object_id != b.object_id
        assert facade.resolve_memory_eid(legacy_source_namespace_id=source_a, eid=9) == a.object_id
        assert facade.resolve_memory_eid(legacy_source_namespace_id=source_b, eid=9) == b.object_id
    finally:
        qualified.close()


def test_create_is_idempotent_lost_response_safe_and_refuses_before_residue(tmp_path: Path, monkeypatch):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        first = _create(facade, identities, scope, idem, source_a, key="lost-response")
        retry = _create(facade, identities, scope, idem, source_a, key="lost-response")
        assert retry == first
        assert _counts(connection) == (1, 1, 1, 1, 0)
        with pytest.raises(SubstrateIdempotencyConflict):
            _create(facade, identities, scope, idem, source_a, key="lost-response", summary="changed")
        before = _counts(connection)
        with pytest.raises(TypeError):
            _create(facade, identities, scope, idem, source_a, key="candidate-summary", summary=CandidateShapedValue("sealed"))
        with pytest.raises(TypeError):
            _create(facade, identities, scope, idem, source_a, key="candidate-payload-object", extra_payload=CandidateShapedValue("sealed"))
        with pytest.raises(TypeError):
            _create(facade, identities, scope, idem, source_a, key="candidate-payload", extra_payload={"ordinary": CandidateShapedValue("sealed")})
        with pytest.raises(ValueError):
            _create(facade, identities, scope, idem, source_a, key="shadow-scope", extra_payload={"scope": "wrong"})
        assert _counts(connection) == before
        before_atomic_failure = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "legacy_object_aliases", "operations"))
        monkeypatch.setattr(compat_module, "_assert_exact_alias", lambda *_args: (_ for _ in ()).throw(RuntimeError("forced post-alias failure")))
        with pytest.raises(RuntimeError, match="forced post-alias failure"):
            _create(facade, identities, scope, idem, source_a, key="forced-rollback")
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("objects", "legacy_object_aliases", "operations")) == before_atomic_failure
    finally:
        qualified.close()


def test_patch_is_one_immutable_successor_with_stale_and_structural_refusal(tmp_path: Path):
    qualified, identities, scope, idem, source_a, _source_b = _database(tmp_path)
    try:
        connection = qualified.connection
        facade = NativeMemoryCompatibilityFacade(connection)
        r1 = _create(facade, identities, scope, idem, source_a, extra_payload={"pos": [0, 0, 0], "vel": [1, 0, 0], "vel0": [1, 0, 0]})
        r2 = facade.patch_memory_state(
            legacy_source_namespace_id=source_a, eid=r1.eid,
            patch={"strength": 0.9, "exported_deep": True, "exported_step": 24, "compression_route": "long", "compression_score": 0.77, "pos": [2, 3, 4], "vel": [0, 1, 0], "vel0": [1, 1, 0]},
            idempotency_namespace_id=idem, idempotency_key="patch-r2", expected_revision_id=r1.revision_id,
        )
        assert r2.eid == r1.eid and r2.object_id == r1.object_id and r2.revision_id != r1.revision_id
        assert connection.execute("SELECT lineage_kind,predecessor_revision_id,revision_ordinal FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(r2.revision_id),)).fetchone() == ("NATIVE_ORDINARY", native_id_to_bytes(r1.revision_id), 2)
        current = facade.get_memory_by_eid(legacy_source_namespace_id=source_a, eid=r1.eid)
        old = facade.get_memory_revision(legacy_source_namespace_id=source_a, eid=r1.eid, revision_id=r1.revision_id)
        assert current.revision_id == r2.revision_id and current.payload["compression_score"] == 0.77 and current.payload["pos"] == [2, 3, 4]
        assert old.revision_id == r1.revision_id and old.payload["strength"] == 0.7 and old.payload["pos"] == [0, 0, 0]
        assert facade.patch_memory_state(legacy_source_namespace_id=source_a, eid=r1.eid, patch={"strength": 0.9, "exported_deep": True, "exported_step": 24, "compression_route": "long", "compression_score": 0.77, "pos": [2, 3, 4], "vel": [0, 1, 0], "vel0": [1, 1, 0]}, idempotency_namespace_id=idem, idempotency_key="patch-r2", expected_revision_id=r1.revision_id) == r2
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(r1.object_id),)).fetchone()[0] == 2
        with pytest.raises(SubstrateIdempotencyConflict):
            facade.patch_memory_state(legacy_source_namespace_id=source_a, eid=r1.eid, patch={"strength": 0.1}, idempotency_namespace_id=idem, idempotency_key="patch-r2", expected_revision_id=r1.revision_id)
        with pytest.raises(SubstrateRevisionConflict):
            facade.patch_memory_state(legacy_source_namespace_id=source_a, eid=r1.eid, patch={"tag": "new"}, idempotency_namespace_id=idem, idempotency_key="stale", expected_revision_id=r1.revision_id)
        before = _counts(connection)
        for structural_key in ("scope", "lifecycle_state", "authority_category", "authorization", "provenance_id", "representation_readiness", "integrity", "reconciliation", "transition_id"):
            with pytest.raises(ValueError):
                facade.patch_memory_state(legacy_source_namespace_id=source_a, eid=r1.eid, patch={structural_key: "blocked"}, idempotency_namespace_id=idem, idempotency_key=f"blocked-{structural_key}")
        assert _counts(connection) == before
    finally:
        qualified.close()
