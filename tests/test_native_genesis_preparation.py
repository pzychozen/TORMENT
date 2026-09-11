"""I3 inert SQLite prerequisites and crash recovery in disposable roots."""

from __future__ import annotations

from contextlib import closing
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from torment_service.substrate import genesis_administration as a
from torment_service.substrate import genesis_contracts as g
from torment_service.substrate import genesis_fence as f
from torment_service.substrate.connection import open_existing_native_core_connection, open_new_native_core_connection
from torment_service.substrate.schema import create_schema, require_current_schema, SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR
from test_native_genesis_administration import child, files, intent_for, observe, prepare


def core_path(root, intent):
    return root / a.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]


def native_snapshot(path):
    with closing(a._open_readonly(path)) as connection:
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {table: connection.execute(f'SELECT * FROM "{table}"').fetchall() for table in tables}


def assert_inert(root, intent, record):
    path = core_path(root, intent)
    with closing(a._open_readonly(path)) as connection:
        metadata = require_current_schema(connection)
        assert metadata.core_id == UUID(intent.payload()["allocations"]["core_id"]).bytes
        assert metadata.core_role == "STAGING"
        assert (metadata.schema_id, metadata.schema_major, metadata.schema_minor) == (SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR)
        expected = a.genesis_prerequisites(intent)
        assert a._verify_native(connection, intent, expected, complete=True) == expected
        assert connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() == [("LEGACY_ACTIVE", None)]
    snapshot = native_snapshot(path)
    assert len(snapshot["core_metadata"]) == len(snapshot["deployment_metadata"]) == 1
    assert {t: len(snapshot[t]) for t in a.CATALOG_COLUMNS} == {
        "identity_namespaces": 10, "semantic_scopes": 4,
        "legacy_source_namespaces": 6, "idempotency_namespaces": 3,
    }
    # All remaining schema tables are exactly devoid of rows, including objects,
    # relationships/memberships, revisions/profiles, representations, transitions,
    # operations, provenance, source admissions, maintenance, and migration ledger.
    assert not any(rows for table, rows in snapshot.items()
                   if table not in {*a.CATALOG_COLUMNS, "core_metadata", "deployment_metadata"})
    all_paths = {p.relative_to(root).as_posix() for p in root.rglob("*")}
    for name in ("workspace_meta.json", "domains.json", "identity.json", "seed.json", "character_state.json",
                 "selector-era-v1.json", "selector.sqlite"):
        assert not any(Path(p).name == name for p in all_paths)
    assert [p for p in all_paths if p.endswith(".db")] == [path.relative_to(root).as_posix()]
    assert record.administrative_phase is g.GenesisAdministrativePhase.PREPARING
    assert record.sealed_completion_payload is None
    assert not record.final_activation_references
    assert len(record.child_operation_references) == 5
    assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.BLOCK_LEGACY
    return snapshot


@pytest.mark.parametrize("enabled", [False, True])
def test_exact_inert_core_prerequisites_and_replay_without_external_or_semantic_owners(tmp_path, enabled):
    root = tmp_path / "root"
    intent = intent_for(root, enabled)
    record = prepare(root, intent)
    snapshot = assert_inert(root, intent, record)
    path = core_path(root, intent)
    core_bytes = path.read_bytes()
    core_inode = path.stat().st_ino
    replay = prepare(root, intent)
    assert replay.child_operation_references == record.child_operation_references
    assert len(replay.quiescence_observations) == 2  # current observation every session
    assert assert_inert(root, intent, replay) == snapshot
    assert path.stat().st_ino == core_inode
    assert path.read_bytes() == core_bytes


CRASH_POINTS = [
    "after-record-publication", "after-private-open", "after-private-preparation",
    "after-core-publication", "before-checkpoint:native-core-preparation",
    "during-catalog:identity_namespaces", "after-native-commit:identity_namespaces",
    "before-checkpoint:native-catalog:identity_namespaces",
    "during-catalog:semantic_scopes", "after-native-commit:semantic_scopes",
    "during-catalog:legacy_source_namespaces", "after-native-commit:legacy_source_namespaces",
    "during-catalog:idempotency_namespaces", "after-native-commit:idempotency_namespaces",
]


@pytest.mark.parametrize("point", CRASH_POINTS)
def test_response_loss_and_partial_preparation_reuse_exact_intent(tmp_path, point):
    root = tmp_path / "root"
    intent = intent_for(root)

    class LostResponse(RuntimeError): pass

    def fail(at):
        if at == point: raise LostResponse(at)

    with pytest.raises(LostResponse, match=point):
        prepare(root, intent, fault=fail)
    record = f.read_genesis_operation_record(data_root=root)
    assert record.expanded_intent == intent
    assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.BLOCK_LEGACY
    replay = prepare(root, intent)
    assert replay.expanded_intent == record.expanded_intent
    assert replay.accepted_start_observation == record.accepted_start_observation
    assert_inert(root, intent, replay)


@pytest.mark.parametrize("point", ["after-private-open", "after-private-preparation", "after-core-publication", "during-catalog:identity_namespaces", "after-native-commit:semantic_scopes"])
def test_hard_process_death_wal_recovery_and_root_lock_release(tmp_path, point):
    root = tmp_path / "root"
    intent = intent_for(root)
    input_path = tmp_path / "intent.json"
    input_path.write_text(json.dumps(intent.payload()), encoding="utf8")
    code = """import sys,os,json
sys.path.insert(0,os.path.abspath('tests'))
from test_native_genesis_administration import prepare
from torment_service.substrate.genesis_contracts import GenesisIntent
intent=GenesisIntent.from_payload(json.load(open(sys.argv[2],encoding='utf8')))
def fail(point):
 if point==sys.argv[3]: os._exit(19)
prepare(sys.argv[1],intent,fault=fail)
"""
    process = child(code, root, input_path, point)
    stdout, stderr = process.communicate(timeout=30)
    assert process.returncode == 19, (stdout, stderr)
    with a.root_onboarding_lock(data_root=root, timeout_seconds=0):
        pass
    assert_inert(root, intent, prepare(root, intent))


@pytest.mark.parametrize("conflict", ["key", "uuid", "extra-identity", "extra-scope", "extra-alias", "extra-idempotency", "creation-time", "semantic-content", "missing-checkpointed"])
def test_conflicting_native_catalog_or_semantic_content_is_not_adopted(tmp_path, conflict):
    root = tmp_path / "root"
    intent = intent_for(root)
    prepare(root, intent)
    path = core_path(root, intent)
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        identifier = UUID(intent.payload()["allocations"]["root_profile_identity_namespace_id"]).bytes
        if conflict == "key": connection.execute("UPDATE identity_namespaces SET namespace_key='foreign' WHERE identity_namespace_id=?", (identifier,))
        elif conflict == "uuid": connection.execute("UPDATE identity_namespaces SET identity_namespace_id=? WHERE identity_namespace_id=?", (uuid4().bytes, identifier))
        elif conflict == "creation-time": connection.execute("UPDATE identity_namespaces SET created_at_ns=1 WHERE identity_namespace_id=?", (identifier,))
        elif conflict == "semantic-content":
            connection.execute("INSERT INTO objects(object_id,identity_namespace_id,object_kind,created_at_ns) VALUES (?,?,?,0)", (uuid4().bytes, identifier, "FOREIGN"))
        elif conflict == "missing-checkpointed": connection.execute("DELETE FROM identity_namespaces WHERE identity_namespace_id=?", (identifier,))
        else:
            table = {"extra-identity": "identity_namespaces", "extra-scope": "semantic_scopes", "extra-alias": "legacy_source_namespaces", "extra-idempotency": "idempotency_namespaces"}[conflict]
            suffix = "" if table == "idempotency_namespaces" else ",0"
            connection.execute(f"INSERT INTO {table} VALUES (?,?{suffix})", (uuid4().bytes, "foreign"))
    before = native_snapshot(path)
    with pytest.raises(a.GenesisPreparationRefused):
        prepare(root, intent)
    assert native_snapshot(path) == before


def test_partial_catalog_effect_without_checkpoint_is_verified_and_repaired(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)

    def fail(point):
        if point == "before-checkpoint:native-core-preparation": raise RuntimeError("stop")

    with pytest.raises(RuntimeError): prepare(root, intent, fault=fail)
    path = core_path(root, intent)
    identifier, key = next(iter(a.genesis_prerequisites(intent)["identity_namespaces"].items()))
    with open_existing_native_core_connection(path) as opened:
        opened.connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (UUID(identifier).bytes, key))
    assert_inert(root, intent, prepare(root, intent))


@pytest.mark.parametrize("location", ["private", "published"])
def test_foreign_staging_identity_refused_even_with_matching_operation_record(tmp_path, location):
    root = tmp_path / "root"
    intent = intent_for(root)
    with a.begin_genesis_administration(data_root=root, intent=intent):
        pass
    path = root / a.PRIVATE_CORE if location == "private" else core_path(root, intent)
    path.parent.mkdir(parents=True)
    if location == "private":
        (root / a.PRIVATE_MANIFEST).write_text(json.dumps(a._bootstrap_manifest(intent)), encoding="utf8")
    with open_new_native_core_connection(path) as opened:
        create_schema(opened.connection, core_id=uuid4())
    before = native_snapshot(path)
    with pytest.raises(a.GenesisPreparationRefused, match="foreign"):
        prepare(root, intent)
    assert native_snapshot(path) == before


@pytest.mark.parametrize("conflict", ["no-manifest", "foreign-manifest", "unknown-temp", "orphan-wal"])
def test_unexplained_private_bootstrap_or_temp_refused(tmp_path, conflict):
    root = tmp_path / "root"
    intent = intent_for(root)
    with a.begin_genesis_administration(data_root=root, intent=intent): pass
    private_dir = root / a.PRIVATE_DIRECTORY
    private_dir.mkdir()
    if conflict in ("no-manifest", "foreign-manifest"):
        (root / a.PRIVATE_CORE).touch()
    if conflict == "foreign-manifest": (root / a.PRIVATE_MANIFEST).write_text("{}")
    if conflict == "unknown-temp": (private_dir / "other.tmp").touch()
    if conflict == "orphan-wal": (private_dir / "core.db-wal").touch()
    before = files(root)
    with pytest.raises(a.GenesisPreparationRefused): prepare(root, intent)
    after = files(root)
    # A successful current quiescence observation may append administrative
    # evidence; none of the unexplained native files is changed or removed.
    record_name = (a.CONTROL_DIRECTORY / a.RECORD_NAME).as_posix()
    assert {k: v for k, v in after.items() if k != record_name} == {k: v for k, v in before.items() if k != record_name}


def test_checkpoint_update_response_lost_after_native_commit(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    calls = 0

    def fail(point):
        nonlocal calls
        if point == "after-checkpoint":
            calls += 1
            if calls == 3: raise RuntimeError("checkpoint response lost")

    with pytest.raises(RuntimeError, match="response lost"): prepare(root, intent, fault=fail)
    before = f.read_genesis_operation_record(data_root=root)
    assert len(before.child_operation_references) == 2
    after = prepare(root, intent)
    assert after.child_operation_references[:2] == before.child_operation_references
    assert_inert(root, intent, after)


def test_published_core_does_not_hide_foreign_private_manifest(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    prepare(root, intent)
    path = core_path(root, intent)
    before = native_snapshot(path)
    (root / a.PRIVATE_MANIFEST).write_text("{}", encoding="utf8")
    with pytest.raises(a.GenesisPreparationRefused, match="bootstrap intent conflicts"):
        prepare(root, intent)
    assert native_snapshot(path) == before


def test_extra_schema_view_is_not_an_inert_prerequisite(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    prepare(root, intent)
    path = core_path(root, intent)
    with open_existing_native_core_connection(path) as opened:
        opened.connection.execute("CREATE VIEW foreign_view AS SELECT 1")
    with pytest.raises(a.GenesisPreparationRefused, match="schema view"):
        prepare(root, intent)


def test_missing_checkpointed_core_is_not_recreated(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    prepare(root, intent)
    path = core_path(root, intent)
    retained = tmp_path / "retained-core.db"
    path.rename(retained)
    with pytest.raises(a.GenesisPreparationRefused, match="checkpointed core is missing"):
        prepare(root, intent)
    assert not path.exists()
    assert retained.exists()


def test_genesis_sequence_contains_no_forbidden_orchestration_calls():
    import ast
    source = Path(a.__file__).read_text(encoding="utf8")
    forbidden = {"establish_selector_era", "initialize_selector", "begin_cutover_pending", "activate_selector_native",
                 "activate_core", "enter_cutover_pending", "bootstrap_real_root_staging", "RealRootStagingBootstrap",
                 "create_or_verify_workspace_declaration", "create_or_verify_for_onboarding", "create_or_verify_seed_definition",
                 "finalize_or_verify_seed_linkage", "build_embedder_from_env", "HashEmbedding", "TormentFabric"}
    calls = [node.func for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)]
    assert not {getattr(node, "id", getattr(node, "attr", "")) for node in calls} & forbidden
