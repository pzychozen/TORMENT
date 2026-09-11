"""I4 qualification: disposable prepared roots and deterministic embeddings only."""
from contextlib import closing, contextmanager
from dataclasses import replace
import json
from uuid import UUID, uuid4

import numpy as np
import pytest

from torment_service.character import CharacterStore, _split_seed_text
from torment_service.identity import IdentityStore
from torment_service.external_owner_json import owner_bytes
from torment_service.atomic_publication import replace_if_exact_predecessor
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate.genesis_contracts import GenesisAdministrativePhase, GenesisIntent
from torment_service.substrate.genesis_fence import GenesisPreparationRefused, read_genesis_fence
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime as Planter
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRequest
from torment_service.substrate.representations import NativeRepresentationService
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from test_native_genesis_administration import intent_for, prepare, quiet_observer, observe, child


class DeterministicEmbedder:
    provider, model, dim = "fixture-provider", "fixture-model", 3

    def __init__(self, *, forbid=False, changed=False):
        self.calls = []
        self.forbid, self.changed = forbid, changed

    def embed(self, text):
        self.calls.append(text)
        if self.forbid:
            raise AssertionError("completed recovery must not embed")
        return np.asarray((0, 1, 0) if self.changed else (1, 0, 0), dtype=np.float32)


def setup_root(tmp_path, enabled=True):
    root = tmp_path / "root"
    value = intent_for(root, enabled).payload()
    if enabled:
        value["character"]["definition"]["seed_text"] = (
            "A patient and enduring first concept. A second resilient concept. A third lasting purpose."
        )
        value["agent"]["identity_seed"]["seed_text"] = value["character"]["definition"]["seed_text"]
    intent = GenesisIntent.from_payload(value)
    prepare(root, intent)
    return root, intent


def run_bundle(root, intent, embedder=None, *, fault=i3._noop, observer=quiet_observer):
    with i4.begin_genesis_character_administration(data_root=root, intent=intent, fault=fault) as session:
        observe(session, observer)
        result = session.prepare_first_character_bundle(embedder=embedder, observer=observer,
            operator_attestation="Disposable root has no writers.", issuer_reference="i4-test")
        return result, session.record


def core_path(root, intent):
    return root / i3.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]


def native_snapshot(root, intent):
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        return {table: sorted(connection.execute('SELECT * FROM "' + table + '"').fetchall(), key=repr)
                for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def owner_snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in (root / "workspaces").rglob("*.json")}


def assert_inert(root, intent, record):
    assert record.administrative_phase is GenesisAdministrativePhase.PREPARING
    assert record.sealed_completion_payload is None
    assert record.final_activation_references == ()
    assert read_genesis_fence(data_root=root).value == "BLOCK_LEGACY"
    assert not (root / i3.CONTROL_DIRECTORY / "selector-era-v1.json").exists()
    assert not (root / i3.CONTROL_DIRECTORY / "selector.sqlite").exists()
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        assert connection.execute("SELECT core_role FROM core_metadata").fetchall() == [("STAGING",)]
        assert connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() == [("LEGACY_ACTIVE", None)]
        assert connection.execute("SELECT count(*) FROM relationships WHERE relationship_kind='ROOT_SCOPE_MEMBERSHIP'").fetchone() == (0,)
        allocation = intent.payload()["allocations"]
        profile_operation_id = allocation["root_profile_idempotency_namespace_id"]
        profile_operation_namespace = UUID(profile_operation_id).bytes
        assert connection.execute("SELECT count(*) FROM idempotency_namespaces").fetchone() == (4,)
        assert connection.execute("SELECT namespace_key FROM idempotency_namespaces WHERE idempotency_namespace_id=?",
            (profile_operation_namespace,)).fetchone() == (allocation["namespace_keys"][profile_operation_id],)
        assert connection.execute("SELECT count(*) FROM operations WHERE idempotency_namespace_id=?",
            (profile_operation_namespace,)).fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM objects WHERE object_id=? OR identity_namespace_id=?",
            (UUID(allocation["root_profile_object_id"]).bytes, UUID(allocation["root_profile_identity_namespace_id"]).bytes)).fetchone() == (0,)
        assert connection.execute("SELECT count(*) FROM object_revisions WHERE effective_semantic_scope_id=?",
            (UUID(allocation["root_profile_semantic_scope_id"]).bytes,)).fetchone() == (0,)


@pytest.mark.parametrize("enabled", [False, True])
def test_first_bundle_and_full_replay(tmp_path, enabled, monkeypatch):
    root, intent = setup_root(tmp_path, enabled)
    embedder = DeterministicEmbedder()
    if not enabled:
        monkeypatch.setattr(Planter, "__init__", lambda *a, **k: pytest.fail("disabled path constructed planter"))
    result, record = run_bundle(root, intent, embedder)
    assert len(record.child_operation_references) == (10 if enabled else 8)
    paths = i4._owner_paths(intent)
    assert json.loads((root / paths[1]).read_text())["domains"] == ["zeta", "alpha"]
    identity = IdentityStore(str(root)).load("workspace", "agent")
    assert identity.created_ts == identity.updated_ts == 11
    assert identity.seed == intent.payload()["agent"]["identity_seed"]
    assert identity.overlay == intent.payload()["agent"]["initial_overlay"]
    assert_inert(root, intent, record)
    snapshot, owners = native_snapshot(root, intent), owner_snapshot(root)
    assert set(owners) == {p.as_posix() for p in paths}
    if enabled:
        native = result.native_seed
        assert native.seed_eids == (0, 1, 2)
        assert tuple(s.concept for s in native.sources) == tuple(_split_seed_text(i4._seed(intent).seed_text))
        assert native.seed_definition_digest == i4.character_seed_definition_digest(i4._seed(intent))
        seed = CharacterStore(str(root)).load_seed("workspace", "seed-one")
        assert tuple(seed.seed_eids) == native.seed_eids and seed.seed_motif_id == native.seed_motif_id
        assert len(snapshot["representations"]) == 3
        with closing(i3._open_readonly(core_path(root, intent))) as connection:
            assert connection.execute("SELECT readiness FROM representation_current_state").fetchall() == [("READY",)] * 3
        assert embedder.calls == [s.concept for s in native.sources]
        assert "seed_eids" not in json.dumps(intent.external_owner_projection())
    else:
        assert result.native_seed is None and embedder.calls == []
        assert not (root / "workspaces/workspace/seeds").exists()
        for table in ("objects", "representations", "relationships", "operations"):
            assert snapshot[table] == []
    raising = DeterministicEmbedder(forbid=True)
    if enabled:
        monkeypatch.setattr(Planter, "plant_seed", lambda *a, **k: pytest.fail("completed Genesis replay called planter"))
    replay, replay_record = run_bundle(root, intent, raising)
    assert replay == result and raising.calls == []
    assert native_snapshot(root, intent) == snapshot
    assert owner_snapshot(root) == owners
    assert replay_record.child_operation_references == record.child_operation_references
    assert len(replay_record.quiescence_observations) == len(record.quiescence_observations) + 3
    assert_inert(root, intent, replay_record)


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("conflict", ["missing", "wrong-key"])
def test_c2_i4_requires_root_profile_operation_namespace_before_any_bundle_work(tmp_path, enabled, conflict):
    root, intent = setup_root(tmp_path, enabled)
    namespace = UUID(intent.payload()["allocations"]["root_profile_idempotency_namespace_id"]).bytes
    with i4.open_existing_native_core_connection(core_path(root, intent)) as opened:
        if conflict == "missing":
            opened.connection.execute("DELETE FROM idempotency_namespaces WHERE idempotency_namespace_id=?", (namespace,))
        else:
            opened.connection.execute("UPDATE idempotency_namespaces SET namespace_key=? WHERE idempotency_namespace_id=?",
                                      ("wrong-profile-domain-key", namespace))
    before = native_snapshot(root, intent)
    embedder = DeterministicEmbedder(forbid=True)
    with pytest.raises(GenesisPreparationRefused, match="prerequisite|namespace"):
        run_bundle(root, intent, embedder)
    assert native_snapshot(root, intent) == before
    assert not embedder.calls and not (root / "workspaces").exists()


def test_completed_readonly_recovery_and_direct_planter_replay(tmp_path):
    root, intent = setup_root(tmp_path)
    result, _record = run_bundle(root, intent, DeterministicEmbedder())
    snapshot, owners = native_snapshot(root, intent), owner_snapshot(root)
    embedder = DeterministicEmbedder(forbid=True)
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        before = connection.total_changes
        runtime = Planter(connection, configuration=i4._configuration(intent, embedder))
        assert runtime.recover_completed_seed(NativeCharacterSeedPlantRequest(i4._seed(intent))) == result.native_seed
        assert connection.total_changes == before == 0
    with i4.open_existing_native_core_connection(core_path(root, intent)) as opened:
        runtime = Planter(opened.connection, configuration=i4._configuration(intent, embedder))
        assert runtime.plant_seed(NativeCharacterSeedPlantRequest(i4._seed(intent))) == result.native_seed
        assert opened.connection.total_changes == 0
    assert not embedder.calls
    assert native_snapshot(root, intent) == snapshot and owner_snapshot(root) == owners


def interrupt_native(monkeypatch, point):
    if point == "source":
        cls, name = Planter, "_source"
    elif point == "expectation":
        cls, name = NativeRepresentationService, "establish_representation_integrity_expectation"
    elif point == "ready":
        cls, name = NativeRepresentationService, "publish_representation_ready"
    elif point == "later-concept":
        cls, name = Planter, "_publish_representation"
    elif point == "motif-decision":
        cls, name = NativeMotifService, "create_motif_with_member"
    elif point == "basin":
        cls, name = NativeMotifService, "advance_motif_state"
    original = getattr(cls, name)
    calls = []
    def after_commit(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(result)
        if len(calls) == (2 if point == "later-concept" else 1):
            raise RuntimeError("I4 injected interruption: " + point)
        return result
    monkeypatch.setattr(cls, name, after_commit)


@pytest.mark.parametrize("point,expected_embeds", [
    ("source", 3), ("expectation", 3), ("ready", 2), ("later-concept", 1),
    ("motif-decision", 0), ("basin", 0), ("after-native-seed-plant", 0),
    ("before-character-linkage", 0), ("after-character-linkage", 0),
    ("before-first-character-checkpoint", 0),
])
def test_partial_seed_recovery(tmp_path, monkeypatch, point, expected_embeds):
    root, intent = setup_root(tmp_path)
    def fault(actual):
        if actual == point:
            raise RuntimeError("I4 injected interruption: " + point)
    with monkeypatch.context() as patch:
        if point in {"source", "expectation", "ready", "later-concept", "motif-decision", "basin"}:
            interrupt_native(patch, point)
        with pytest.raises(RuntimeError, match="I4 injected interruption"):
            run_bundle(root, intent, DeterministicEmbedder(), fault=fault)
    prior = native_snapshot(root, intent)
    embedder = DeterministicEmbedder(forbid=expected_embeds == 0)
    result, record = run_bundle(root, intent, embedder)
    assert len(embedder.calls) == expected_embeds
    assert result.native_seed.seed_eids == (0, 1, 2)
    after = native_snapshot(root, intent)
    for table in ("operations", "object_revisions", "representations", "representation_payloads", "integrity_expectations"):
        assert all(row in after[table] for row in prior[table])
    assert len(after["representations"]) == 3
    assert len({s.object_id for s in result.native_seed.sources}) == 3
    assert_inert(root, intent, record)


@pytest.mark.parametrize("point", ["source", "expectation"])
def test_changed_embedding_refuses_without_rewriting_committed_truth(tmp_path, monkeypatch, point):
    root, intent = setup_root(tmp_path)
    with monkeypatch.context() as patch:
        interrupt_native(patch, point)
        with pytest.raises(RuntimeError, match="I4 injected interruption"):
            run_bundle(root, intent, DeterministicEmbedder())
    native, owners = native_snapshot(root, intent), owner_snapshot(root)
    changed = DeterministicEmbedder(changed=True)
    with pytest.raises(SubstrateIdempotencyConflict, match="embedding hash differs"):
        run_bundle(root, intent, changed)
    assert len(changed.calls) == 1
    assert native_snapshot(root, intent) == native and owner_snapshot(root) == owners


@pytest.mark.parametrize("field", [
    "semantic_scope_id", "identity_namespace_id", "legacy_source_namespace_id", "motif_alias_namespace_id",
    "motif_identity_namespace_id", "membership_identity_namespace_id", "idempotency_namespace_id", "domain", "lane",
])
def test_routing_configuration_negatives_refuse_before_planting(tmp_path, monkeypatch, field):
    root, intent = setup_root(tmp_path)
    original = i4._configuration
    def changed(intent, embedder):
        config = original(intent, embedder)
        if field == "domain":
            return replace(config, domain_id="alpha")
        if field == "lane":
            return replace(config, representation_lane=replace(config.representation_lane, generation=2))
        scope = config.routing_scope
        if field in {"semantic_scope_id", "identity_namespace_id", "legacy_source_namespace_id"}:
            scope = replace(scope, runtime_scope=replace(scope.runtime_scope, **{field: uuid4()}))
        else:
            scope = replace(scope, **{field: uuid4()})
        return replace(config, routing_scope=scope)
    monkeypatch.setattr(i4, "_configuration", changed)
    before = native_snapshot(root, intent)
    embedder = DeterministicEmbedder(forbid=True)
    with pytest.raises(GenesisPreparationRefused, match="routing configuration"):
        run_bundle(root, intent, embedder)
    assert not embedder.calls and not (root / "workspaces").exists()
    assert native_snapshot(root, intent) == before


@pytest.mark.parametrize("field", [
    "target_semantic_scope_id", "target_identity_namespace_id", "legacy_source_namespace_id", "motif_alias_namespace_id",
    "motif_identity_namespace_id", "membership_identity_namespace_id", "idempotency_namespace_id",
])
@pytest.mark.parametrize("mutation", ["mismatch", "missing"])
def test_persisted_prerequisite_mismatch_refuses_before_planting(tmp_path, field, mutation):
    root, intent = setup_root(tmp_path)
    plan = next(p.payload()["scope_plan"] for p in intent.runtime_plans if p.payload()["scope_key"]["scope_kind"] == "PRIVATE")
    with i4.open_existing_native_core_connection(core_path(root, intent)) as opened:
        for table, (identifier, key) in i3.CATALOG_COLUMNS.items():
            if str(plan[field]) in i3.genesis_prerequisites(intent)[table]:
                if mutation == "mismatch":
                    opened.connection.execute(f"UPDATE {table} SET {key}=? WHERE {identifier}=?", ("foreign-key", UUID(plan[field]).bytes))
                else:
                    opened.connection.execute(f"DELETE FROM {table} WHERE {identifier}=?", (UUID(plan[field]).bytes,))
    before = native_snapshot(root, intent)
    embedder = DeterministicEmbedder(forbid=True)
    with pytest.raises(GenesisPreparationRefused, match="namespace|prerequisite"):
        run_bundle(root, intent, embedder)
    assert not embedder.calls and native_snapshot(root, intent) == before


@pytest.mark.parametrize("conflict", ["identity-seed", "definition", "owner-agent", "linkage", "malformed", "workspace", "domains"])
def test_external_conflicts_preserved(tmp_path, conflict):
    root, intent = setup_root(tmp_path)
    run_bundle(root, intent, DeterministicEmbedder())
    paths = i4._owner_paths(intent)
    index = {"identity-seed": 2, "definition": 3, "owner-agent": 3, "linkage": 3, "malformed": 2, "workspace": 0, "domains": 1}[conflict]
    path = root / paths[index]
    payload = json.loads(path.read_text())
    if conflict == "identity-seed":
        payload["seed"]["seed_text"] = "Conflicting identity."
    elif conflict == "definition":
        payload["seed_text"] = "Conflicting Character."
    elif conflict == "owner-agent":
        payload["owner_agent_id"] = "someone-else"
    elif conflict == "linkage":
        payload["seed_eids"] = [98]
        payload["seed_motif_id"] = "foreign-motif"
    elif conflict == "workspace":
        payload["embed_model"] = "foreign-model"
    elif conflict == "domains":
        payload["domains"].reverse()
    path.write_bytes(b"{" if conflict == "malformed" else owner_bytes(payload))
    before, owners = native_snapshot(root, intent), owner_snapshot(root)
    embedder = DeterministicEmbedder(forbid=True)
    with pytest.raises((ValueError, GenesisPreparationRefused)):
        run_bundle(root, intent, embedder)
    assert not embedder.calls
    assert native_snapshot(root, intent) == before and owner_snapshot(root) == owners


def test_preexisting_linkage_requires_native_completion(tmp_path):
    root, intent = setup_root(tmp_path)
    def fault(point):
        if point == "after-character-definition":
            raise RuntimeError("stop before planting")
    with pytest.raises(RuntimeError, match="stop before planting"):
        run_bundle(root, intent, DeterministicEmbedder(), fault=fault)
    path = root / i4._owner_paths(intent)[3]
    value = json.loads(path.read_text())
    value.update(seed_eids=[0], seed_motif_id="unproved-motif")
    path.write_bytes(owner_bytes(value))
    before = native_snapshot(root, intent)
    with pytest.raises(GenesisPreparationRefused, match="no matching native completion"):
        run_bundle(root, intent, DeterministicEmbedder(forbid=True))
    assert native_snapshot(root, intent) == before


@pytest.mark.parametrize("point", ["after-workspace-declaration", "after-identity-publication", "after-character-definition"])
def test_partial_external_bundle_recovery(tmp_path, point):
    root, intent = setup_root(tmp_path)
    def fault(actual):
        if point == actual:
            raise RuntimeError("external owner committed")
    with pytest.raises(RuntimeError, match="external owner committed"):
        run_bundle(root, intent, DeterministicEmbedder(), fault=fault)
    before = owner_snapshot(root)
    result, record = run_bundle(root, intent, DeterministicEmbedder())
    after = owner_snapshot(root)
    for path, state in before.items():
        if path.endswith("seed.json"):
            # The definition survives; only the authorized linkage CAS advances.
            assert json.loads(state[0])["seed_text"] == json.loads(after[path][0])["seed_text"]
        else:
            assert after[path] == state
    assert result.native_seed.seed_eids == (0, 1, 2)
    assert_inert(root, intent, record)


def test_missing_lock_quiescence_and_ended_session_refuse(tmp_path):
    root, intent = setup_root(tmp_path)
    record = i3._matching_record(root, intent)
    manual = i4.GenesisCharacterAdministration(root, record)
    kwargs = dict(embedder=DeterministicEmbedder(forbid=True), observer=quiet_observer,
                  operator_attestation="test", issuer_reference="test")
    with pytest.raises(GenesisPreparationRefused, match="live I3"):
        manual.prepare_first_character_bundle(**kwargs)
    with i4.begin_genesis_character_administration(data_root=root, intent=intent) as session:
        with pytest.raises(GenesisPreparationRefused, match="quiescence"):
            session.prepare_first_character_bundle(**kwargs)
        process = child("from torment_service.substrate.genesis_administration import root_onboarding_lock\n"
                        "import sys\nwith root_onboarding_lock(data_root=sys.argv[1],timeout_seconds=0): pass", root)
        out, err = process.communicate(timeout=20)
        assert process.returncode != 0 and "root-onboarding-lock-busy" in err
    with pytest.raises(GenesisPreparationRefused, match="ended"):
        session.prepare_first_character_bundle(**kwargs)
    assert not (root / "workspaces").exists()


@pytest.mark.parametrize("when", ["initial", "before", "after"])
def test_quiescence_rechecked_and_failed_observation_prevents_checkpoint(tmp_path, when):
    root, intent = setup_root(tmp_path)
    calls = []
    def observer(root, intent):
        calls.append(1)
        facts = quiet_observer(root, intent)
        return replace(facts, complete=False) if len(calls) == {"initial": 1, "before": 2, "after": 3}[when] else facts
    with pytest.raises(GenesisPreparationRefused, match="incomplete"):
        run_bundle(root, intent, DeterministicEmbedder(), observer=observer)
    record = i3._matching_record(root, intent)
    assert len(record.child_operation_references) == 5
    if when != "after":
        assert not (root / "workspaces").exists()
    else:
        result, record = run_bundle(root, intent, DeterministicEmbedder(forbid=True))
        assert result.native_seed.seed_eids == (0, 1, 2)
    assert_inert(root, intent, record)


def test_owner_changed_during_final_observation_cannot_be_checkpointed(tmp_path):
    root, intent = setup_root(tmp_path)
    calls = []
    def observer(root, intent):
        calls.append(1)
        if len(calls) == 3:
            path = root / i4._owner_paths(intent)[1]
            path.write_bytes(owner_bytes(dict(domains=["alpha", "zeta"])))
        return quiet_observer(root, intent)
    with pytest.raises(GenesisPreparationRefused, match="workspace changed"):
        run_bundle(root, intent, DeterministicEmbedder(), observer=observer)
    assert len(i3._matching_record(root, intent).child_operation_references) == 5


def test_actual_cold_owner_reads_with_persistent_i2_publication_locks(tmp_path):
    root, intent = setup_root(tmp_path)
    result, _record = run_bundle(root, intent, DeterministicEmbedder())
    for relative in i4._owner_paths(intent):
        path = root / relative
        raw = path.read_bytes()
        replace_if_exact_predecessor(path, raw, raw)
        assert path.with_name(f".{path.name}.publication.lock").is_file()
    before = owner_snapshot(root)
    code = '''import json, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path.cwd() / 'tests'))
from torment_service.identity import IdentityStore
from torment_service.character import CharacterStore
from test_native_genesis_external_owners import isolated_workspace_format_methods
root = sys.argv[1]
identity = IdentityStore(root).load('workspace', 'agent')
seed = CharacterStore(root).load_seed('workspace', 'seed-one')
cls, _ = isolated_workspace_format_methods()
workspace = cls()
workspace.data_dir, workspace.workspace_id = root, 'workspace'
workspace.kernel = SimpleNamespace(embedder=SimpleNamespace(dim=3, provider='fixture-provider', model='fixture-model'))
print(json.dumps(dict(identity=identity.agent_id, eids=seed.seed_eids, motif=seed.seed_motif_id,
                     metadata=workspace._load_or_init_meta(), domains=workspace._load_or_init_domains())))
'''
    process = child(code, root)
    out, err = process.communicate(timeout=30)
    assert process.returncode == 0, err
    cold = json.loads(out)
    assert cold["identity"] == "agent" and cold["eids"] == [0, 1, 2]
    assert cold["motif"] == result.native_seed.seed_motif_id
    assert cold["domains"] == ["zeta", "alpha"] and cold["metadata"]["created_ts"] == 10
    assert owner_snapshot(root) == before
    replay, _record = run_bundle(root, intent, DeterministicEmbedder(forbid=True))
    assert replay == result
    assert all((root / p).with_name(f".{p.name}.publication.lock").is_file() for p in i4._owner_paths(intent))


@contextmanager
def corrupt_immutable_table(connection, table):
    """Inject storage damage in a fixture, restoring the exact schema atomically."""
    triggers = connection.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,)).fetchall()
    connection.execute("BEGIN IMMEDIATE")
    try:
        for name, _sql in triggers:
            connection.execute('DROP TRIGGER "' + name.replace('"', '""') + '"')
        yield
        for _name, sql in triggers:
            connection.execute(sql)
        connection.execute("COMMIT")
    except BaseException:
        connection.execute("ROLLBACK")
        raise


@pytest.mark.parametrize("corruption", ["payload", "expectation", "provenance", "motif-domain", "source-intent", "basin-intent"])
def test_completed_native_truth_is_verified_before_external_finalization(tmp_path, corruption):
    root, intent = setup_root(tmp_path)
    def fault(point):
        if point == "before-character-linkage":
            raise RuntimeError("native ahead of external")
    with pytest.raises(RuntimeError, match="native ahead"):
        run_bundle(root, intent, DeterministicEmbedder(), fault=fault)
    with i4.open_existing_native_core_connection(core_path(root, intent)) as opened:
        connection = opened.connection
        if corruption == "payload":
            with corrupt_immutable_table(connection, "representation_payloads"):
                connection.execute("UPDATE representation_payloads SET payload_bytes=?", (np.asarray((0, 1, 0), dtype=np.float32).tobytes(),))
        elif corruption == "expectation":
            with corrupt_immutable_table(connection, "integrity_expectations"):
                connection.execute("UPDATE integrity_expectations SET expected_value=?", (bytes(32),))
        elif corruption == "provenance":
            with corrupt_immutable_table(connection, "provenance_records"):
                connection.execute("UPDATE provenance_records SET descriptive_notes=?", ('{"wrong":"origin"}',))
        elif corruption == "motif-domain":
            with corrupt_immutable_table(connection, "object_revisions"):
                connection.execute("UPDATE object_revisions SET payload_text=json_set(payload_text,'$.domain_id','alpha') WHERE object_id IN (SELECT object_id FROM objects WHERE object_kind='DERIVED_MOTIF')")
        else:
            runtime = Planter(connection, configuration=i4._configuration(intent, DeterministicEmbedder(forbid=True)))
            key = runtime._source_key("seed-one", 0) if corruption == "source-intent" else runtime._motif_key("seed-one", "SEED_BASIN_BOOST")
            row = runtime._operation_row(key)
            payload = json.loads(row[1])
            if corruption == "source-intent":
                payload["concept"] = "Wrong committed concept."
            else:
                payload["motif_alias_namespace_id"] = str(uuid4())
            connection.execute("UPDATE operations SET canonical_intent_json=? WHERE operation_id=?",
                (json.dumps(payload), row[0]))
    before, owners = native_snapshot(root, intent), owner_snapshot(root)
    with pytest.raises((SubstrateInvariantViolation, SubstrateIdempotencyConflict, GenesisPreparationRefused)):
        run_bundle(root, intent, DeterministicEmbedder(forbid=True))
    assert native_snapshot(root, intent) == before and owner_snapshot(root) == owners
    assert CharacterStore(str(root)).load_seed("workspace", "seed-one").seed_eids == []
    assert len(i3._matching_record(root, intent).child_operation_references) == 5
