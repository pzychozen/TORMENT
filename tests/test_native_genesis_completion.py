"""I6 sealing qualification: disposable I1-I5 fixtures, read-only native recovery."""
from contextlib import closing, contextmanager
from dataclasses import replace
import json
import sqlite3
from uuid import UUID

import pytest

from torment_service.external_owner_json import owner_bytes
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_membership_administration as i5
from torment_service.substrate import genesis_completion_administration as i6
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.deployment_core_maintenance import inspect_contained_core_deployment
from torment_service.substrate.deployment_types import NativeGenesisCompletionWitness, completion_witness_from_payload
from torment_service.substrate.errors import SubstrateError
from torment_service.substrate.genesis_contracts import GenesisIntent, GenesisOperationRecord, payload_digest
from torment_service.substrate.genesis_fence import GenesisPreparationRefused, read_genesis_operation_record, read_genesis_fence
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime as Planter
from test_native_genesis_administration import quiet_observer, child
from test_native_genesis_character import core_path, native_snapshot, owner_snapshot, corrupt_immutable_table
from test_native_genesis_membership import prepared_bundle, run_memberships, corrupt_authority


@pytest.fixture(autouse=True)
def forbid_planting_and_embedding(monkeypatch):
    def refuse(*_args, **_kwargs):
        pytest.fail("I6 and its fixture setup must not plant or embed")
    monkeypatch.setattr(Planter, "plant_seed", refuse)
    monkeypatch.setattr(Planter, "_embed", refuse)


def prepared_root(tmp_path, enabled=True):
    root, intent, bundle = prepared_bundle(tmp_path, enabled)
    membership, record = run_memberships(root, intent)
    return root, intent, bundle, membership, record


def run_seal(root, intent, *, observer=quiet_observer, fault=i3._noop):
    with i6.begin_genesis_completion_administration(data_root=root, intent=intent, fault=fault) as session:
        return session.seal_preparation(observer=observer,
            operator_attestation="Disposable completed root has no writers.", issuer_reference="i6-final-operator")


def file_snapshot(root):
    # Preserve main DB and nonempty WAL bytes. Shared-memory/empty-WAL files
    # are read coordination, not durable Genesis authority or completion.
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and not p.name.endswith((".lock", "-shm"))
            and not (p.name.endswith("-wal") and p.stat().st_size == 0)}


@contextmanager
def read_only_native_guard(monkeypatch):
    original = i3._open_readonly
    calls, forbidden = [], []
    writes = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
        sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_CREATE_INDEX,
        sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_DROP_TRIGGER,
        sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    def authorizer(action, arg1, arg2, database, trigger):
        if action in writes:
            forbidden.append((action, arg1))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    def read(path):
        connection = original(path)
        assert connection.execute("PRAGMA query_only").fetchone() == (1,)
        calls.append(str(path))
        connection.set_authorizer(authorizer)
        return connection
    with monkeypatch.context() as patch:
        patch.setattr(i3, "_open_readonly", read)
        yield calls
    assert calls and not forbidden


def assert_switched_off(root, intent, record):
    assert record.administrative_phase.value == "PREPARATION_SEALED"
    assert record.sealed_completion_payload is not None and record.final_activation_references == ()
    assert read_genesis_fence(data_root=root).value == "BLOCK_LEGACY"
    assert not (root / i3.CONTROL_DIRECTORY / "selector-era-v1.json").exists()
    assert not (root / i3.CONTROL_DIRECTORY / "selector.sqlite").exists()
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        assert connection.execute("SELECT core_role FROM core_metadata").fetchall() == [("STAGING",)]
        assert connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() == [("LEGACY_ACTIVE", None)]
        assert connection.execute("SELECT * FROM maintenance_events").fetchall() == []
    inspection = inspect_contained_core_deployment(data_root=root,
        core_relative_path=intent.payload()["allocations"]["core_relative_path"])
    assert inspection.activation_completion_witness is None


@pytest.mark.parametrize("enabled", [False, True])
def test_exact_seal_round_trip_export_and_only_one_administrative_write(tmp_path, enabled, monkeypatch):
    root, intent, bundle, membership, before_record = prepared_root(tmp_path, enabled)
    before, files, owners = native_snapshot(root, intent), file_snapshot(root), owner_snapshot(root)
    with read_only_native_guard(monkeypatch):
        result = run_seal(root, intent)
    completion, record = result.completion, result.operation_record
    assert NativeGenesisCompletionWitness.from_payload(completion.payload()) == completion
    assert completion_witness_from_payload(completion.payload()) == completion
    assert result.qualified_profile_payload == completion.qualified_profile_payload()
    assert result.qualified_profile_payload == {**intent.payload()["profile_choice"],
        "admitted_scope_plan_digest": membership.qualified_deployment_profile.admitted_scope_plan_digest,
        "external_owner_digest": membership.qualified_deployment_profile.external_owner_digest}
    exported = result.qualified_profile_payload
    exported["representation_model"] = "changed local copy"
    assert result.qualified_profile_payload != exported
    assert completion.admission_identity_digest == intent.digest
    assert completion.native_core_id == UUID(intent.payload()["allocations"]["core_id"])
    assert completion.profile_digest == membership.qualified_deployment_profile.digest
    assert completion.accepted_start_observation == before_record.accepted_start_observation
    assert completion.expanded_intent == intent
    assert completion.root_profile == membership.root_profile
    assert completion.external_owner_projection.payload() == intent.external_owner_projection()
    assert completion.external_owner_closure_digest == membership.qualified_deployment_profile.external_owner_digest
    assert [m.payload()["scope_key"]["scope_kind"] for m in membership.initial_memberships] == ["SHARED", "SHARED", "PRIVATE"]
    assert [m.payload()["scope_key"]["domain_id"] for m in membership.initial_memberships[:2]] == ["zeta", "alpha"]
    assert completion.initial_memberships == tuple(sorted(membership.initial_memberships, key=lambda m: m.canonical_key))
    assert completion.initial_membership_closure_digest == membership.initial_membership_closure_digest
    assert record.phase_revision == before_record.phase_revision + 1
    assert record.quiescence_observations[:-1] == before_record.quiescence_observations
    assert record.quiescence_observations[-1].payload()["issuer_reference"] == "i6-final-operator"
    assert record.child_operation_references == before_record.child_operation_references
    assert completion.quiescence_evidence_digest == payload_digest({"quiescence_observations": [o.payload() for o in record.quiescence_observations]})
    assert completion.preparation_result_digest == payload_digest(completion.preparation_payload())
    assert read_genesis_operation_record(data_root=root) == record
    assert native_snapshot(root, intent) == before and owner_snapshot(root) == owners
    after = file_snapshot(root)
    assert set(files) == set(after)
    assert [key for key in files if files[key] != after[key]] == [(i3.CONTROL_DIRECTORY / i3.RECORD_NAME).as_posix()]
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        metadata = i6.require_current_schema(connection)
        assert (completion.schema_id, completion.schema_major, completion.schema_minor) == (metadata.schema_id, metadata.schema_major, metadata.schema_minor)
    if not enabled:
        assert completion.character_seed_completion.payload() == {"mode": "DISABLED"}
        assert bundle.native_seed is None
    assert_switched_off(root, intent, record)


def test_dual_character_digests_bind_exact_native_receipts_and_strict_decode(tmp_path):
    root, intent, bundle, _membership, _record = prepared_root(tmp_path)
    result = run_seal(root, intent)
    completion = result.completion
    seed = completion.character_seed_completion.payload()
    source, native = i6._character_projections(intent, bundle.native_seed)
    genesis_digest = payload_digest(intent.payload()["character"]["definition"])
    native_digest = i6.character_seed_definition_digest(i4._seed(intent))
    assert genesis_digest != native_digest
    assert seed["definition_digest"] == source["genesis_definition_digest"] == genesis_digest
    assert bundle.native_seed.seed_definition_digest == source["native_character_definition_digest"] == native_digest
    assert native["native_character_definition_digest"] == native_digest
    assert seed["source_intent_digest"] == payload_digest(source)
    assert seed["result_digest"] == payload_digest(native)
    config = i4._configuration(intent, i5._CommittedLane(intent))
    assert seed["source_operation_key"] == config.parent_native_operation_key
    assert seed["seed_eids"] == [0, 1, 2]
    assert seed["representation_ids"] == [str(s.representation_id) for s in bundle.native_seed.sources]
    assert seed["seed_motif_id"] == bundle.native_seed.seed_motif_id
    assert NativeGenesisCompletionWitness.from_payload(completion.payload()) == completion
    for digest_key in ("genesis_definition_digest", "native_character_definition_digest"):
        changed = {**source, digest_key: "0" * 64}
        assert payload_digest(changed) != seed["source_intent_digest"]
    assert payload_digest({**native, "native_character_definition_digest": "0" * 64}) != seed["result_digest"]
    with pytest.raises(GenesisPreparationRefused, match="native Character definition digest"):
        i6._character_projections(intent, replace(bundle.native_seed, seed_definition_digest="0" * 64))


@pytest.mark.parametrize("enabled", [False, True])
def test_sealed_replay_and_process_restart_do_not_rewrite_or_observe(tmp_path, enabled, monkeypatch):
    root, intent, _bundle, _membership, _ = prepared_root(tmp_path, enabled)
    result = run_seal(root, intent)
    before = file_snapshot(root)
    def forbidden(*_args, **_kwargs):
        pytest.fail("sealed replay must not observe writers or publish bytes")
    with monkeypatch.context() as patch:
        patch.setattr(i6, "replace_if_exact_predecessor", forbidden)
        with read_only_native_guard(monkeypatch):
            assert run_seal(root, intent, observer=forbidden) == result
    code = """
import json,sys
from pathlib import Path
from torment_service.substrate.genesis_contracts import GenesisIntent
from torment_service.substrate.genesis_completion_administration import begin_genesis_completion_administration
with begin_genesis_completion_administration(data_root=Path(sys.argv[1]),intent=GenesisIntent.from_payload(json.loads(sys.argv[2]))) as session:
    result=session.seal_preparation()
    print(json.dumps(result.completion.payload(),sort_keys=True))
"""
    process = child(code, str(root), json.dumps(intent.payload()))
    stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 0, stderr
    assert json.loads(stdout) == result.completion.payload()
    assert file_snapshot(root) == before


@pytest.mark.parametrize("point", ["before-final-completion-reread", "before-completion-seal", "after-completion-seal"])
@pytest.mark.parametrize("enabled", [False, True])
def test_fault_before_or_after_seal_recovers_without_extra_revision(tmp_path, enabled, point):
    root, intent, _, _, original = prepared_root(tmp_path, enabled)
    before = native_snapshot(root, intent)
    def fail(where):
        if where == point:
            raise RuntimeError("seal response lost")
    with pytest.raises(RuntimeError, match="seal response lost"):
        run_seal(root, intent, fault=fail)
    current = read_genesis_operation_record(data_root=root)
    assert current.phase_revision == original.phase_revision + (point == "after-completion-seal")
    result = run_seal(root, intent)
    assert result.operation_record.phase_revision == original.phase_revision + 1
    assert len(result.operation_record.quiescence_observations) == len(original.quiescence_observations) + 1
    assert native_snapshot(root, intent) == before


def test_atomic_owner_response_loss_and_hard_process_death(tmp_path, monkeypatch):
    root, intent, _, _, before = prepared_root(tmp_path)
    original = i6.replace_if_exact_predecessor
    def lost(*args):
        original(*args)
        raise RuntimeError("owner response lost")
    with monkeypatch.context() as patch:
        patch.setattr(i6, "replace_if_exact_predecessor", lost)
        with pytest.raises(RuntimeError, match="owner response lost"):
            run_seal(root, intent)
    sealed = read_genesis_operation_record(data_root=root)
    assert sealed.phase_revision == before.phase_revision + 1
    files = file_snapshot(root)
    assert run_seal(root, intent).operation_record == sealed
    assert file_snapshot(root) == files
    (tmp_path / "hard-death").mkdir()
    root2, intent2, _, _, before2 = prepared_root(tmp_path / "hard-death")
    code = """
import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd() / 'tests'))
from test_native_genesis_completion import run_seal
from torment_service.substrate.genesis_contracts import GenesisIntent
run_seal(Path(sys.argv[1]),GenesisIntent.from_payload(json.loads(sys.argv[2])),
    fault=lambda where: os._exit(73) if where=='after-completion-seal' else None)
"""
    process = child(code, str(root2), json.dumps(intent2.payload()))
    _stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 73, stderr
    assert run_seal(root2, intent2).operation_record.phase_revision == before2.phase_revision + 1


CONFLICTS = ["external-owner", "character-linkage", "representation", "root-profile", "membership", "witness",
    "catalog", "core", "schema", "native-digest", "marker", "selector", "core-completion"]


@pytest.mark.parametrize("sealed", [False, True])
@pytest.mark.parametrize("conflict", CONFLICTS)
def test_durable_conflict_refuses_without_seal_or_repair(tmp_path, sealed, conflict):
    root, intent, bundle, membership, _ = prepared_root(tmp_path)
    if sealed:
        run_seal(root, intent)
    if conflict in {"external-owner", "character-linkage"}:
        path = root / i4._owner_paths(intent)[2 if conflict == "external-owner" else -1]
        value = json.loads(path.read_text())
        if conflict == "external-owner":
            value["updated_ts"] += 1
        else:
            value["seed_eids"] = [99]
        path.write_bytes(owner_bytes(value))
    elif conflict in {"marker", "selector"}:
        (root / i3.CONTROL_DIRECTORY / ("selector-era-v1.json" if conflict == "marker" else "selector.sqlite")).write_bytes(b"foreign")
    elif conflict in {"root-profile", "membership", "witness"}:
        with corrupt_authority(root, intent, "profile-payload" if conflict == "root-profile" else "membership-lifecycle") as c:
            if conflict == "root-profile":
                c.execute("UPDATE object_revisions SET payload_text=json_set(payload_text,'$.profile_generation',2) WHERE object_id=?",
                    (UUID(membership.root_profile.payload()["profile_object_id"]).bytes,))
            else:
                rid = UUID(membership.initial_memberships[0].payload()["relationship_id"]).bytes
                if conflict == "membership":
                    c.execute("UPDATE relationship_revisions SET lifecycle_state='RETIRED' WHERE relationship_id=?", (rid,))
                else:
                    c.execute("UPDATE relationship_revisions SET payload_text=json_set(payload_text,'$.external_witness.witness_digest',?) WHERE relationship_id=?", ("0" * 64, rid))
    else:
        with open_existing_native_core_connection(core_path(root, intent)) as opened:
            c = opened.connection
            if conflict == "representation":
                with corrupt_immutable_table(c, "representation_payloads"):
                    c.execute("UPDATE representation_payloads SET payload_bytes=?", (bytes(12),))
            elif conflict == "catalog":
                c.execute("UPDATE idempotency_namespaces SET namespace_key=namespace_key || '-foreign'")
            elif conflict == "schema":
                c.execute("UPDATE core_metadata SET schema_minor=999")
            elif conflict == "core":
                c.execute("UPDATE core_metadata SET core_role='EVIDENCE_ONLY'")
            elif conflict == "native-digest":
                c.execute("UPDATE operations SET canonical_intent_json=json_set(canonical_intent_json,'$.seed_definition_digest',?) WHERE idempotency_key LIKE '%:SOURCE:%'", ("0" * 64,))
            else:
                c.execute("INSERT INTO maintenance_events VALUES (?,?,0,0,?)", (UUID(int=900, version=4).bytes, "CUTOVER", '{"completion_witness":"foreign"}'))
    before = file_snapshot(root)
    with pytest.raises(SubstrateError):
        run_seal(root, intent)
    assert file_snapshot(root) == before


@pytest.mark.parametrize("field", ["definition_digest", "source_intent_digest", "result_digest", "qualified-profile", "completion-bytes"])
def test_tampered_sealed_completion_refuses_even_when_outer_digest_is_recomputed(tmp_path, field):
    root, intent, _, _, _ = prepared_root(tmp_path)
    run_seal(root, intent)
    path = root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME
    value = json.loads(path.read_bytes())
    completion = value["sealed_completion_payload"]
    if field == "completion-bytes":
        path.write_bytes(b" " + path.read_bytes())
    else:
        if field == "qualified-profile":
            completion["qualified_deployment_profile"]["representation_model"] = "different"
            completion["qualified_deployment_profile_digest"] = payload_digest(completion["qualified_deployment_profile"])
        else:
            completion["character_seed_completion"][field] = "0" * 64
        completion.pop("preparation_result_digest")
        completion["preparation_result_digest"] = payload_digest(completion)
        path.write_bytes(owner_bytes(value))
    before = file_snapshot(root)
    with pytest.raises(SubstrateError):
        run_seal(root, intent)
    assert file_snapshot(root) == before


@pytest.mark.parametrize("owner", ["native-core-preparation", "first-character-linkage", "initial-root-membership-closure"])
def test_missing_checkpoint_refuses_before_observation(tmp_path, owner):
    root, intent, _, _, record = prepared_root(tmp_path)
    record = replace(record, child_operation_references=tuple(r for r in record.child_operation_references if r.payload()["owner"] != owner))
    path = root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME
    path.write_bytes(owner_bytes(record.payload()))
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused, match="checkpoints"):
        run_seal(root, intent, observer=lambda *_: pytest.fail("preconditions must precede observation"))
    assert file_snapshot(root) == before


@pytest.mark.parametrize("old", [i3.begin_genesis_administration, i4.begin_genesis_character_administration, i5.begin_genesis_membership_administration])
def test_old_mutating_administrators_remain_closed_after_seal(tmp_path, old):
    root, intent, _, _, _ = prepared_root(tmp_path)
    run_seal(root, intent)
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused):
        with old(data_root=root, intent=intent):
            pytest.fail("old mutation session entered a sealed root")
    assert file_snapshot(root) == before


@pytest.mark.parametrize("sealed", [False, True])
@pytest.mark.parametrize("changed", ["genesis-definition", "qualified-profile-input"])
def test_changed_frozen_digest_inputs_cannot_seal_or_recover(tmp_path, sealed, changed):
    root, intent, bundle, _, _ = prepared_root(tmp_path)
    if sealed:
        run_seal(root, intent)
    value = intent.payload()
    if changed == "genesis-definition":
        value["character"]["definition"]["character_name"] = "Changed declaration"
        value["agent"]["identity_seed"]["character_name"] = "Changed declaration"
    else:
        value["profile_choice"]["representation_model"] = "different-model"
        value["representation_lane"]["model"] = "different-model"
        for plan in value["allocations"]["runtime_scope_plans"]:
            plan["representation_lane"]["model"] = "different-model"
    changed_intent = GenesisIntent.from_payload(value)
    if changed == "genesis-definition":
        assert payload_digest(value["character"]["definition"]) != payload_digest(intent.payload()["character"]["definition"])
        assert i6.character_seed_definition_digest(i4._seed(changed_intent)) != bundle.native_seed.seed_definition_digest
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused):
        run_seal(root, changed_intent)
    assert file_snapshot(root) == before


@pytest.mark.parametrize("point", ["observation", "before-final-completion-reread", "before-completion-seal"])
def test_writer_drift_is_refused_before_atomic_seal(tmp_path, point):
    root, intent, _, _, _ = prepared_root(tmp_path)
    path = root / i4._owner_paths(intent)[2]
    def change():
        value = json.loads(path.read_bytes())
        value["updated_ts"] += 1
        path.write_bytes(owner_bytes(value))
    def observer(root, intent):
        evidence = quiet_observer(root, intent)
        if point == "observation":
            change()
        return evidence
    def fault(where):
        if where == point:
            change()
    record_path = root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME
    before = record_path.read_bytes()
    with pytest.raises(GenesisPreparationRefused):
        run_seal(root, intent, observer=observer, fault=fault)
    assert record_path.read_bytes() == before


def test_stale_quiescence_and_competing_predecessor_do_not_seal(tmp_path, monkeypatch):
    from torment_service.atomic_publication import PublicationConflict
    root, intent, _, _, record = prepared_root(tmp_path, False)
    before = file_snapshot(root)
    def stale(root, intent):
        return replace(quiet_observer(root, intent), observed_at_ns=1)
    with pytest.raises(GenesisPreparationRefused, match="stale"):
        run_seal(root, intent, observer=stale)
    assert file_snapshot(root) == before
    original = i6.replace_if_exact_predecessor
    competing = owner_bytes(replace(record, phase_revision=record.phase_revision + 1).payload())
    def race(path, predecessor, successor):
        path.write_bytes(competing)
        return original(path, predecessor, successor)
    with monkeypatch.context() as patch:
        patch.setattr(i6, "replace_if_exact_predecessor", race)
        with pytest.raises(PublicationConflict, match="predecessor"):
            run_seal(root, intent)
    assert (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).read_bytes() == competing
    assert read_genesis_operation_record(data_root=root).sealed_completion_payload is None


def test_i6_requires_live_existing_os_lock(tmp_path):
    root, intent, _, _, record = prepared_root(tmp_path, False)
    session = i6.GenesisCompletionAdministration(root, intent, record)
    with pytest.raises(GenesisPreparationRefused, match="live"):
        session.seal_preparation()
    code = """
import sys,json
from pathlib import Path
from torment_service.substrate.genesis_contracts import GenesisIntent
from torment_service.substrate.genesis_completion_administration import begin_genesis_completion_administration
from torment_service.substrate.genesis_fence import GenesisPreparationRefused
try:
    with begin_genesis_completion_administration(data_root=Path(sys.argv[1]),
        intent=GenesisIntent.from_payload(json.loads(sys.argv[2])),timeout_seconds=0.1):
        raise AssertionError('entered locked root')
except GenesisPreparationRefused:
    print('CONTENDED')
"""
    with i3.root_onboarding_lock(data_root=root):
        process = child(code, str(root), json.dumps(intent.payload()))
        stdout, stderr = process.communicate(timeout=60)
        assert process.returncode == 0, stderr
        assert stdout.strip() == "CONTENDED"
    with i6.begin_genesis_completion_administration(data_root=root, intent=intent) as ended:
        pass
    with pytest.raises(GenesisPreparationRefused, match="live"):
        ended.seal_preparation()


def test_sealing_after_last_writer_closes_keeps_database_and_wal_truth_read_only(tmp_path, monkeypatch):
    root, intent, _, _, _ = prepared_root(tmp_path)
    # Closing the final rw connection checkpoints/removes its coordination
    # sidecars. I6 must still recover through normal WAL-aware read-only access.
    with open_existing_native_core_connection(core_path(root, intent)):
        pass
    before = file_snapshot(root)
    with read_only_native_guard(monkeypatch):
        result = run_seal(root, intent)
    after = file_snapshot(root)
    changed = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    assert changed == {(i3.CONTROL_DIRECTORY / i3.RECORD_NAME).as_posix()}
    assert_switched_off(root, intent, result.operation_record)
