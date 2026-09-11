"""I5 qualification on disposable roots; no embedder or model may be invoked."""
from contextlib import closing, contextmanager
from dataclasses import asdict, replace
import json
from pathlib import Path
from uuid import UUID, uuid4

import numpy as np
import pytest

from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_membership_administration as i5
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.genesis_contracts import GenesisOperationRecord
from torment_service.substrate.genesis_fence import GenesisPreparationRefused, read_genesis_fence
from torment_service.substrate.native_character_seed_plant import (
    NativeCharacterSeedPlantRuntime as Planter, NativeCharacterSeedPlantRequest, NativeCharacterSeedSourceResult,
)
from torment_service.substrate.objects import NativeObjectService
from torment_service.substrate.root_scope_membership import RootScopeMembershipService, RootScopeMembershipReader
from torment_service.substrate.root_profile import current_root_profile_generation
from torment_service.substrate.errors import SubstrateError
from test_native_genesis_administration import quiet_observer, observe, child
from test_native_genesis_character import (
    setup_root, run_bundle, core_path, native_snapshot, owner_snapshot, corrupt_immutable_table,
)


@pytest.fixture(autouse=True)
def forbid_planting_and_embedding(monkeypatch):
    def refuse(*_args, **_kwargs):
        pytest.fail("I5 must not plant or embed, including during fixture setup")
    monkeypatch.setattr(Planter, "plant_seed", refuse)
    monkeypatch.setattr(Planter, "_embed", refuse)


def committed_character_fixture(root, intent):
    """Publish literal representation test data through existing native owners.

    These are precomputed float32 bytes, not the result of an embedder call. The
    fixture constructs committed I4 owner receipts without calling plant_seed;
    the production I4 bundle then exercises only completed-result recovery.
    """
    config = i4._configuration(intent, i5._CommittedLane(intent))
    seed = i4._seed(intent)
    request = NativeCharacterSeedPlantRequest(seed)
    digest = i4.character_seed_definition_digest(seed)
    vector = np.frombuffer(bytes.fromhex("0000803f0000000000000000"), dtype=np.float32).copy()
    sources, vectors = [], []
    with open_existing_native_core_connection(core_path(root, intent)) as opened:
        runtime = Planter(opened.connection, configuration=config)
        for index, concept in enumerate(i4._split_seed_text(seed.seed_text)):
            source = runtime._source(request, digest, index, concept, vector)
            ready = runtime._publish_representation(source, vector)
            sources.append(NativeCharacterSeedSourceResult(source.object_id, source.revision_id, source.eid,
                source.provenance_id, ready.representation_id, index, concept, source.payload_sha256, source.created_ts))
            vectors.append(vector)
        runtime._ensure_seed_motif(request, sources, vectors)


def prepared_bundle(tmp_path, enabled=True):
    root, intent = setup_root(tmp_path, enabled)
    if enabled:
        committed_character_fixture(root, intent)
    bundle, _record = run_bundle(root, intent, i5._CommittedLane(intent))
    return root, intent, bundle


def run_memberships(root, intent, *, fault=i3._noop, observer=quiet_observer, issuer="i5-test-operator"):
    with i5.begin_genesis_membership_administration(data_root=root, intent=intent, fault=fault) as session:
        observe(session, observer)
        result = session.prepare_initial_memberships(observer=observer,
            operator_attestation="Disposable root has no writers.", issuer_reference=issuer)
        return result, session.record


def assert_inert(root, intent, record):
    assert record.administrative_phase.value == "PREPARING"
    assert record.sealed_completion_payload is None and not record.final_activation_references
    assert read_genesis_fence(data_root=root).value == "BLOCK_LEGACY"
    assert not (root / i3.CONTROL_DIRECTORY / "selector-era-v1.json").exists()
    assert not (root / i3.CONTROL_DIRECTORY / "selector.sqlite").exists()
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        assert connection.execute("SELECT core_role FROM core_metadata").fetchall() == [("STAGING",)]
        assert connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() == [("LEGACY_ACTIVE", None)]


@pytest.mark.parametrize("enabled", [False, True])
def test_i5_exact_closure_replay_and_declared_publication_order(tmp_path, enabled, monkeypatch):
    root, intent, bundle = prepared_bundle(tmp_path, enabled)
    before, owners = native_snapshot(root, intent), owner_snapshot(root)
    calls = []
    original = RootScopeMembershipService.admit
    def tracking(self, **kwargs):
        calls.append((kwargs["runtime_scope"].scope_kind, kwargs["runtime_scope"].qualifier))
        return original(self, **kwargs)
    monkeypatch.setattr(RootScopeMembershipService, "admit", tracking)
    result, record = run_memberships(root, intent)
    assert calls == [("SHARED_DOMAIN", "zeta"), ("SHARED_DOMAIN", "alpha"), ("PRIVATE_AGENT", "agent")]
    assert len(result.initial_memberships) == 3
    assert len(record.child_operation_references) == (12 if enabled else 10)
    assert len(asdict(result.qualified_deployment_profile)) == 7
    assert result.qualified_deployment_profile == i5.qualified_genesis_profile(intent)
    from torment_service.substrate.deployment_types import digest_mapping
    from torment_service.substrate.root_blocker5_binding import root_membership_closure_digest
    assert result.qualified_deployment_profile.external_owner_digest == digest_mapping(intent.external_owner_projection())
    assert result.qualified_deployment_profile.digest == digest_mapping(asdict(result.qualified_deployment_profile))
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        profile = current_root_profile_generation(connection)
        recovered = RootScopeMembershipReader(connection).recover(profile)
        assert root_membership_closure_digest(connection=connection, profile=profile,
            runtime_scopes=tuple(i5._runtime_scope(p) for p in i5._publication_plans(intent)),
            declared_scope_keys=tuple(r.runtime_key.scope_key for r in recovered)) == result.initial_membership_closure_digest
    assert result.root_profile.payload()["profile_revision_ordinal"] == 1
    assert "profile_revision_id" not in intent.payload()["allocations"]
    assert {m.payload()["membership_witness"]["provenance_kind"] for m in result.initial_memberships} == {"EXTERNAL_ISSUED"}
    after = native_snapshot(root, intent)
    assert len(after["objects"]) == len(before["objects"]) + 1
    assert len(after["relationships"]) == len(before["relationships"]) + 3
    for table in ("representations", "representation_payloads", "legacy_object_aliases", "provenance_records"):
        assert after[table] == before[table]
    assert owner_snapshot(root) == owners
    if enabled:
        assert bundle.native_seed.seed_eids == (0, 1, 2)
    for _ in range(2):
        replay, record = run_memberships(root, intent)
        assert replay == result
        assert native_snapshot(root, intent) == after
        assert owner_snapshot(root) == owners
    assert len(calls) == 3
    assert_inert(root, intent, record)


@pytest.mark.parametrize("enabled", [False, True])
def test_i4_committed_bundle_replay_still_works_without_embedding(tmp_path, enabled):
    root, intent, bundle = prepared_bundle(tmp_path, enabled)
    before, owners = native_snapshot(root, intent), owner_snapshot(root)
    replay, record = run_bundle(root, intent, i5._CommittedLane(intent))
    assert replay == bundle
    assert native_snapshot(root, intent) == before and owner_snapshot(root) == owners
    assert_inert(root, intent, record)


FAULTS = ["after-root-profile-commit", "after-membership-commit:0", "after-membership-commit:1",
    "before-private-membership", "after-membership-commit:2", "before-initial-membership-checkpoint",
    "after-initial-membership-checkpoint"]


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("point", FAULTS)
def test_i5_failure_resumes_exact_committed_authority(tmp_path, enabled, point):
    root, intent, _bundle = prepared_bundle(tmp_path, enabled)
    def fail(where):
        if where == point:
            raise RuntimeError("I5 injected failure")
    with pytest.raises(RuntimeError, match="injected"):
        run_memberships(root, intent, fault=fail)
    partial = native_snapshot(root, intent)
    result, record = run_memberships(root, intent)
    complete = native_snapshot(root, intent)
    for table in ("objects", "object_revisions", "relationships", "relationship_revisions", "operations"):
        assert all(row in complete[table] for row in partial[table])
    assert len(result.initial_memberships) == 3
    assert run_memberships(root, intent)[0] == result
    assert native_snapshot(root, intent) == complete
    assert_inert(root, intent, record)


@pytest.mark.parametrize("owner", ["profile", "membership"])
def test_response_lost_inside_native_owner_recovers_same_revision(tmp_path, owner, monkeypatch):
    root, intent, _bundle = prepared_bundle(tmp_path)
    cls, name = (NativeObjectService, "create_object") if owner == "profile" else (RootScopeMembershipService, "admit")
    original = getattr(cls, name)
    def lose(self, **kwargs):
        original(self, **kwargs)
        raise RuntimeError("native response lost after commit")
    monkeypatch.setattr(cls, name, lose)
    with pytest.raises(RuntimeError, match="response lost"):
        run_memberships(root, intent)
    before = native_snapshot(root, intent)
    monkeypatch.setattr(cls, name, original)
    result, _record = run_memberships(root, intent)
    after = native_snapshot(root, intent)
    for table in ("object_revisions", "relationship_revisions", "operations"):
        assert all(row in after[table] for row in before[table])
    assert run_memberships(root, intent)[0] == result


@pytest.mark.parametrize("point", FAULTS)
def test_process_death_and_restart_preserve_closure(tmp_path, point):
    root, intent, _bundle = prepared_bundle(tmp_path)
    code = """
import os,sys,json
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_native_genesis_membership import run_memberships
from torment_service.substrate.genesis_contracts import GenesisIntent
root=Path(sys.argv[1]); intent=GenesisIntent.from_payload(json.loads(sys.argv[2]))
run_memberships(root,intent,fault=lambda where: os._exit(73) if where==sys.argv[3] else None)
"""
    crashed = child(code, str(root), json.dumps(intent.payload()), point)
    _stdout, stderr = crashed.communicate(timeout=60)
    assert crashed.returncode == 73, stderr
    before = native_snapshot(root, intent)
    result, _ = run_memberships(root, intent)
    after = native_snapshot(root, intent)
    for table in ("object_revisions", "relationship_revisions", "operations"):
        assert all(row in after[table] for row in before[table])
    check = child("""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd() / 'tests'))
from test_native_genesis_membership import run_memberships
from torment_service.substrate.genesis_contracts import GenesisIntent
result,_=run_memberships(Path(sys.argv[1]),GenesisIntent.from_payload(json.loads(sys.argv[2])))
print(result.initial_membership_closure_digest)
""", str(root), json.dumps(intent.payload()))
    stdout, stderr = check.communicate(timeout=60)
    assert check.returncode == 0, stderr
    assert stdout.strip() == result.initial_membership_closure_digest
    assert native_snapshot(root, intent) == after


CONFLICTS = ["profile-object", "profile-generation", "profile-scope", "profile-namespace", "profile-payload",
    "profile-operation-namespace", "shared-scope", "private-scope", "witness-digest", "witness-issuer",
    "membership-namespace", "membership-lifecycle", "foreign-membership", "membership-generation", "membership-operation-namespace"]


@contextmanager
def corrupt_authority(root, intent, conflict):
    if conflict in {"profile-object", "profile-namespace"}:
        table = "objects"
    elif conflict in {"profile-generation", "profile-scope", "profile-payload"}:
        table = "object_revisions"
    elif conflict.endswith("operation-namespace"):
        table = "operations"
    elif conflict in {"membership-namespace", "foreign-membership"}:
        table = "relationships"
    else:
        table = "relationship_revisions"
    with open_existing_native_core_connection(core_path(root, intent)) as opened:
        opened.connection.execute("PRAGMA foreign_keys=OFF")
        with corrupt_immutable_table(opened.connection, table):
            yield opened.connection


@pytest.mark.parametrize("conflict", CONFLICTS)
def test_conflicting_native_authority_is_refused_without_repair(tmp_path, conflict):
    root, intent, _bundle = prepared_bundle(tmp_path)
    result, _record = run_memberships(root, intent)
    a = intent.payload()["allocations"]
    profile_id = UUID(a["root_profile_object_id"]).bytes
    members = result.initial_memberships
    member_id = UUID(members[-1 if conflict == "private-scope" else 0].payload()["relationship_id"]).bytes
    with corrupt_authority(root, intent, conflict) as c:
        if conflict == "profile-object":
            c.execute("UPDATE objects SET object_id=? WHERE object_id=?", (uuid4().bytes, profile_id))
        elif conflict in {"profile-generation", "profile-payload"}:
            payload = i5.root_profile_generation_payload(2 if conflict == "profile-generation" else 1)
            if conflict == "profile-payload":
                payload["extra-authority"] = True
            c.execute("UPDATE object_revisions SET payload_text=? WHERE object_id=?", (json.dumps(payload), profile_id))
        elif conflict == "profile-scope":
            c.execute("UPDATE object_revisions SET effective_semantic_scope_id=? WHERE object_id=?",
                (UUID(intent.runtime_plans[0].payload()["scope_plan"]["target_semantic_scope_id"]).bytes, profile_id))
        elif conflict == "profile-namespace":
            c.execute("UPDATE objects SET identity_namespace_id=? WHERE object_id=?",
                (UUID(intent.runtime_plans[0].payload()["scope_plan"]["target_identity_namespace_id"]).bytes, profile_id))
        elif conflict in {"profile-operation-namespace", "membership-operation-namespace"}:
            key = i5._operation_key(intent, i5._OWNERS[0]) if conflict.startswith("profile") else i5._operation_key(
                intent, "initial-membership", scope_key=i5._publication_plans(intent)[0]["scope_key"])
            c.execute("UPDATE operations SET idempotency_namespace_id=? WHERE idempotency_key=?",
                (UUID(intent.runtime_plans[0].payload()["scope_plan"]["idempotency_namespace_id"]).bytes, key))
        elif conflict in {"shared-scope", "private-scope"}:
            c.execute("UPDATE relationship_revisions SET effective_semantic_scope_id=? WHERE relationship_id=?",
                (UUID(a["root_profile_semantic_scope_id"]).bytes, member_id))
        elif conflict in {"witness-digest", "witness-issuer", "membership-generation"}:
            payload = json.loads(c.execute("SELECT payload_text FROM relationship_revisions WHERE relationship_id=?", (member_id,)).fetchone()[0])
            if conflict == "membership-generation":
                payload["profile"]["profile_generation"] = 2
            else:
                payload["external_witness"]["witness_digest" if conflict == "witness-digest" else "issuer_reference"] = "f" * 64
            c.execute("UPDATE relationship_revisions SET payload_text=? WHERE relationship_id=?", (json.dumps(payload), member_id))
        elif conflict == "membership-namespace":
            c.execute("UPDATE relationships SET identity_namespace_id=? WHERE relationship_id=?", (UUID(a["root_profile_identity_namespace_id"]).bytes, member_id))
        elif conflict == "membership-lifecycle":
            c.execute("UPDATE relationship_revisions SET lifecycle_state='RETIRED' WHERE relationship_id=?", (member_id,))
        elif conflict == "foreign-membership":
            c.execute("INSERT INTO relationships(relationship_id,identity_namespace_id,relationship_kind,created_at_ns) VALUES (?,?,?,0)",
                (uuid4().bytes, UUID(a["root_profile_identity_namespace_id"]).bytes, "ROOT_SCOPE_MEMBERSHIP"))
    before, owners = native_snapshot(root, intent), owner_snapshot(root)
    with pytest.raises(SubstrateError):
        run_memberships(root, intent)
    assert native_snapshot(root, intent) == before and owner_snapshot(root) == owners


def test_changed_issuer_refuses_existing_witness(tmp_path):
    root, intent, _bundle = prepared_bundle(tmp_path)
    run_memberships(root, intent)
    before = native_snapshot(root, intent)
    with pytest.raises(GenesisPreparationRefused, match="witness"):
        run_memberships(root, intent, issuer="different-operator")
    assert native_snapshot(root, intent) == before


@pytest.mark.parametrize("broken", ["catalog", "i4-checkpoint", "external-linkage", "seed-receipt", "foreign-file"])
def test_i5_preconditions_refuse_before_profile_publication(tmp_path, broken):
    root, intent, _bundle = prepared_bundle(tmp_path)
    if broken == "i4-checkpoint":
        path = root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME
        record = GenesisOperationRecord.from_payload(json.loads(path.read_text()))
        path.write_text(json.dumps(replace(record, child_operation_references=record.child_operation_references[:-1]).payload()))
    elif broken == "external-linkage":
        path = root / i4._owner_paths(intent)[-1]
        payload = json.loads(path.read_text())
        payload["seed_eids"] = [99]
        path.write_text(json.dumps(payload))
    elif broken == "foreign-file":
        (root / "foreign.json").write_text("{}")
    else:
        with open_existing_native_core_connection(core_path(root, intent)) as opened:
            if broken == "catalog":
                opened.connection.execute("UPDATE idempotency_namespaces SET namespace_key=namespace_key || '-foreign'")
            else:
                opened.connection.execute("UPDATE operations SET idempotency_key=idempotency_key || '-foreign' WHERE idempotency_key LIKE '%SEED_BASIN_BOOST'")
    before = native_snapshot(root, intent)
    with pytest.raises(SubstrateError):
        run_memberships(root, intent)
    assert native_snapshot(root, intent) == before


def test_requires_live_os_lock_and_fresh_quiescence(tmp_path):
    root, intent, _bundle = prepared_bundle(tmp_path, False)
    record = i3._matching_record(root, intent)
    raw = i5.GenesisMembershipAdministration(root, record)
    with pytest.raises(GenesisPreparationRefused, match="lock"):
        raw._require_record()
    with i5.begin_genesis_membership_administration(data_root=root, intent=intent) as session:
        with pytest.raises(GenesisPreparationRefused, match="quiescence"):
            session.prepare_initial_memberships(observer=quiet_observer, operator_attestation="quiet", issuer_reference="operator")
    with pytest.raises(GenesisPreparationRefused):
        session._require_record()


@pytest.mark.parametrize("enabled", [False, True])
def test_qualified_profile_uses_production_runtime_plan_digest(enabled):
    from test_native_genesis_contracts import intent_payload
    from torment_service.substrate.genesis_contracts import GenesisIntent, SCOPE_PLAN_UUID_FIELDS
    from torment_service.substrate.migration.runtime_readiness import MigrationRuntimeScopePlan
    from torment_service.substrate.root_blocker5_binding import root_runtime_scope_plan_digest
    from torment_service.substrate.runtime_binding import NativeRepresentationLane
    intent = GenesisIntent.from_payload(intent_payload(enabled))
    plans = []
    for plan in i5._publication_plans(intent):
        scope, key = plan["scope_plan"], plan["scope_key"]
        plans.append(MigrationRuntimeScopePlan(**{name: UUID(scope[name]) for name in SCOPE_PLAN_UUID_FIELDS},
            workspace_id=scope["workspace_id"], scope_kind=scope["scope_kind"], motif_domain_id=scope["motif_domain_id"],
            agent_id=key["agent_id"], domain_id=key["domain_id"]))
    lane = NativeRepresentationLane(**intent.payload()["representation_lane"])
    profile = i5.qualified_genesis_profile(intent)
    assert profile.admitted_scope_plan_digest == root_runtime_scope_plan_digest(tuple(plans), lane)
    assert profile.admitted_scope_plan_digest == root_runtime_scope_plan_digest(tuple(reversed(plans)), lane)


def test_admin_owner_response_loss_recovers_published_checkpoint(tmp_path, monkeypatch):
    root, intent, _ = prepared_bundle(tmp_path)
    original = i3.replace_if_exact_predecessor
    def lose(path, previous, replacement):
        original(path, previous, replacement)
        payload = json.loads(replacement)
        if any(ref["owner"] == "initial-root-membership-closure" for ref in payload["child_operation_references"]):
            raise RuntimeError("admin owner response lost")
    monkeypatch.setattr(i3, "replace_if_exact_predecessor", lose)
    with pytest.raises(RuntimeError, match="admin owner response lost"):
        run_memberships(root, intent)
    before = native_snapshot(root, intent)
    monkeypatch.setattr(i3, "replace_if_exact_predecessor", original)
    result, record = run_memberships(root, intent)
    assert set(result.child_references) <= set(record.child_operation_references)
    assert native_snapshot(root, intent) == before


def test_fresh_observation_failure_prevents_all_profile_and_membership_writes(tmp_path):
    root, intent, _ = prepared_bundle(tmp_path, False)
    before = native_snapshot(root, intent)
    observations = []
    def stale_on_write(root, intent):
        observations.append(1)
        result = quiet_observer(root, intent)
        return replace(result, observed_at_ns=1) if len(observations) > 1 else result
    with pytest.raises(GenesisPreparationRefused, match="stale"):
        run_memberships(root, intent, observer=stale_on_write)
    assert len(observations) == 2 and native_snapshot(root, intent) == before


def test_i5_contends_on_existing_i3_os_lock(tmp_path):
    root, intent, _ = prepared_bundle(tmp_path, False)
    code = """
import sys,json
from pathlib import Path
from torment_service.substrate.genesis_contracts import GenesisIntent
from torment_service.substrate.genesis_membership_administration import begin_genesis_membership_administration
from torment_service.substrate.genesis_fence import GenesisPreparationRefused
try:
    with begin_genesis_membership_administration(data_root=Path(sys.argv[1]),
        intent=GenesisIntent.from_payload(json.loads(sys.argv[2])),timeout_seconds=0.1):
        raise AssertionError('entered locked root')
except GenesisPreparationRefused:
    print('CONTENDED')
"""
    with i3.root_onboarding_lock(data_root=root):
        contender = child(code, str(root), json.dumps(intent.payload()))
        stdout, stderr = contender.communicate(timeout=60)
        assert contender.returncode == 0, stderr
        assert stdout.strip() == "CONTENDED"
    run_memberships(root, intent)
