"""I7 qualification. Activation exists only in explicit disposable fixtures."""
from contextlib import closing, contextmanager
from dataclasses import replace
import ast
import json
from pathlib import Path
import sqlite3
import threading
from types import SimpleNamespace
from uuid import UUID

import pytest

from torment_service.substrate import deployment_selector as selector
from torment_service.substrate import deployment_core_maintenance as maintenance
from torment_service.substrate import genesis_recovery as recovery
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate.deployment_types import DeploymentResolutionMode, QualifiedDeploymentProfile
from torment_service.substrate.deployment_types import AdmissionCompletionWitness, canonical_json
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.errors import DeploymentAuthorityError
from torment_service.substrate.genesis_contracts import payload_digest
from torment_service.substrate.genesis_fence import read_genesis_fence
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime
from torment_service.substrate.production_native_owner import (
    NativeProductionResourceOwner, NativeProductionResourceOwnerError,
    NativeProductionQueryContext, NativeProductionWriteContext, NativeProductionPostWriteContext,
)
from test_native_genesis_completion import prepared_root, run_seal, file_snapshot
from test_native_genesis_administration import child
from test_native_genesis_character import corrupt_immutable_table, core_path
from test_native_genesis_membership import corrupt_authority
from torment_service.external_owner_json import owner_bytes


@pytest.fixture(autouse=True)
def no_planting_or_embedding(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("I7 fixture/recovery must use only committed representations")
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, "plant_seed", forbidden)
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, "_embed", forbidden)


def activate_fixture(root, completion, *, stop_after=None):
    """Existing activation APIs under the existing mutex; never production code."""
    stages = []
    def observe(name):
        stages.append((name, read_genesis_fence(data_root=root).value))
        return stop_after == name
    with i3.root_onboarding_lock(data_root=root):
        selector.establish_selector_era(data_root=root)
        if stop_after == "marker":
            observe("marker")
            return stages
        # Frozen adjacency: no inspection/work between these two publications.
        state = selector.initialize_selector(data_root=root, operation_key="i7-fixture-initialize")
        if observe("legacy-selector"):
            return stages
        state = selector.begin_cutover_pending(data_root=root, core_relative_path=completion.core_relative_path,
            descriptor_digest=completion.admission_identity_digest, profile=completion.qualified_deployment_profile,
            expected_generation=state.generation, operation_key="i7-fixture-selector-pending")
        if observe("selector-pending"):
            return stages
        inspected = maintenance.inspect_contained_core_deployment(data_root=root, core_relative_path=completion.core_relative_path)
        predecessor = maintenance.staging_legacy_witness(inspected, descriptor_digest=completion.admission_identity_digest,
            profile_digest=completion.profile_digest)
        pending = maintenance.enter_cutover_pending(data_root=root, core_relative_path=completion.core_relative_path,
            expected_witness=predecessor, selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest, operation_key="i7-fixture-core-pending")
        if observe("core-pending"):
            return stages
        active = maintenance.activate_core(data_root=root, core_relative_path=completion.core_relative_path,
            expected_witness=pending.witness, selector_generation=state.generation,
            selector_witness_digest=state.core_witness_digest, operation_key="i7-fixture-core-active",
            completion_witness=completion)
        if observe("core-active-selector-pending"):
            return stages
        selector.activate_selector_native(data_root=root, core_relative_path=completion.core_relative_path,
            core_result=active, expected_generation=state.generation, operation_key="i7-fixture-selector-active",
            disposition_execution_receipt_digest=None)
        observe("active")
    return stages


def active_root(tmp_path, enabled=True):
    root, intent, bundle, memberships, record = prepared_root(tmp_path, enabled)
    sealed = run_seal(root, intent)
    stages = activate_fixture(root, sealed.completion)
    return root, intent, sealed, stages


def resolve(root, completion):
    return selector.resolve_deployment_agreement(data_root=root, effective_profile=completion.qualified_deployment_profile)


def owner_for(root, completion):
    return NativeProductionResourceOwner.from_native_agreement(data_root=root,
        effective_profile=completion.qualified_deployment_profile, agreement=resolve(root, completion),
        admission_descriptor_path=None)


@contextmanager
def readonly_recovery_guard(monkeypatch):
    original = recovery._open_readonly_core
    calls, writes = [], []
    denied = {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE, sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_DROP_INDEX,
        sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    def authorizer(action, one, two, database, trigger):
        if action in denied:
            writes.append((action, one))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    def read(path):
        connection = original(path)
        assert connection.execute("PRAGMA query_only").fetchone() == (1,)
        connection.set_authorizer(authorizer)
        calls.append(str(path))
        return connection
    with monkeypatch.context() as patch:
        patch.setattr(recovery, "_open_readonly_core", read)
        yield
    assert calls and not writes


@pytest.mark.parametrize("enabled", [False, True])
def test_active_genesis_transitions_owner_and_admin_independence(tmp_path, enabled, monkeypatch):
    root, intent, sealed, stages = active_root(tmp_path, enabled)
    assert stages == [(name, "BLOCK_LEGACY") for name in ["legacy-selector", "selector-pending", "core-pending", "core-active-selector-pending"]] + [("active", "NATIVE_AUTHORITY_WINS")]
    completion = sealed.completion
    record_path = root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME
    assert json.loads(record_path.read_bytes())["administrative_phase"] == "PREPARATION_SEALED"
    assert read_genesis_fence(data_root=root).value == "NATIVE_AUTHORITY_WINS"
    before = file_snapshot(root)
    with readonly_recovery_guard(monkeypatch):
        owner = owner_for(root, completion)
        assert owner._admission_descriptor_path is None
        runtime = owner._recover_active_runtime(workspace_id="workspace")
        assert runtime.native_core_id == completion.native_core_id
        assert runtime.representation_lane == recovery.NativeRepresentationLane(**intent.payload()["representation_lane"])
        assert len(runtime.scopes) == 3
        assert runtime.lookup_private("agent").memory_runtime_scope.agent_id == "agent"
        assert {runtime.lookup_shared(name).memory_runtime_scope.domain_id for name in ["zeta", "alpha"]} == {"zeta", "alpha"}
        with pytest.raises(recovery.NativeGenesisRecoveryRefused):
            recovery.recover_active_native_genesis(data_root=root, workspace_id="foreign")
        owner.close()
    assert file_snapshot(root) == before
    record_path.unlink()  # only the explicit disposable administrative file
    assert read_genesis_fence(data_root=root).value == "ABSENT"
    assert resolve(root, completion).mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    before = file_snapshot(root)
    with readonly_recovery_guard(monkeypatch):
        owner = owner_for(root, completion)
        assert owner._recover_active_runtime(workspace_id="workspace") == runtime
        owner.close()
    assert file_snapshot(root) == before


def test_sealed_and_marker_only_remain_blocked_and_exact_initialization_recovers(tmp_path):
    root, intent, _, _, _ = prepared_root(tmp_path, False)
    sealed = run_seal(root, intent)
    assert read_genesis_fence(data_root=root).value == "BLOCK_LEGACY"
    assert activate_fixture(root, sealed.completion, stop_after="marker") == [("marker", "BLOCK_LEGACY")]
    assert not selector.selector_paths(root).selector_path.exists()
    assert resolve(root, sealed.completion).mode is not DeploymentResolutionMode.LEGACY_PUBLIC
    # Replay the exact adjacent pair; marker replay is idempotent.
    assert activate_fixture(root, sealed.completion)[-1] == ("active", "NATIVE_AUTHORITY_WINS")


@pytest.mark.parametrize("enabled", [False, True])
def test_stable_identity_allows_overlay_updates_and_restart_without_admin(tmp_path, enabled):
    root, intent, sealed, _ = active_root(tmp_path, enabled)
    path = root / i4._owner_paths(intent)[2]
    identity = json.loads(path.read_bytes())
    identity["updated_ts"] += 100
    identity["overlay"] = {key: 0.375 for key in identity["overlay"]}
    path.write_bytes(owner_bytes(identity))
    (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).unlink()
    before = file_snapshot(root)
    owner = owner_for(root, sealed.completion)
    runtime = owner._recover_active_runtime(workspace_id="workspace")
    owner.close()
    code = """
import sys,json
from pathlib import Path
from torment_service.substrate.genesis_recovery import recover_active_native_genesis
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.production_native_owner import NativeProductionResourceOwner
root=Path(sys.argv[1])
authority=recover_active_native_genesis(data_root=root)
profile=authority.completion.qualified_deployment_profile
agreement=resolve_deployment_agreement(data_root=root,effective_profile=profile)
owner=NativeProductionResourceOwner.from_native_agreement(data_root=root,effective_profile=profile,agreement=agreement)
runtime=owner._recover_active_runtime(workspace_id='workspace')
print(json.dumps(dict(completion=authority.completion.payload(),scopes=[s.memory_runtime_scope.qualifier for s in runtime.scopes])))
owner.close()
"""
    process = child(code, str(root))
    stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 0, stderr
    output = json.loads(stdout)
    assert output["completion"] == sealed.completion.payload()
    assert output["scopes"] == [s.memory_runtime_scope.qualifier for s in runtime.scopes]
    assert file_snapshot(root) == before


def test_fence_needs_no_host_profile_but_resolver_requires_exact_profile(tmp_path):
    root, _, sealed, _ = active_root(tmp_path, False)
    assert recovery.verify_active_native_genesis(data_root=root).completion == sealed.completion
    assert read_genesis_fence(data_root=root).value == "NATIVE_AUTHORITY_WINS"
    changed = replace(sealed.completion.qualified_deployment_profile, representation_model="foreign")
    assert selector.resolve_deployment_agreement(data_root=root, effective_profile=changed).mode is DeploymentResolutionMode.REFUSED


def change_completion(root, completion, change):
    """Corrupt only a disposable activation receipt, maintaining its outer binding."""
    path = maintenance.contained_core_path(data_root=root, core_relative_path=completion.core_relative_path, require_exists=True)
    with open_existing_native_core_connection(path) as opened:
        for mid, raw in opened.connection.execute("SELECT maintenance_id,detail_json FROM maintenance_events WHERE maintenance_kind='CUTOVER'").fetchall():
            detail = json.loads(raw)
            if detail.get("transition_kind") != "ACTIVATE_CORE":
                continue
            payload = change(detail["completion_witness"])
            if isinstance(payload, dict) and "preparation_result_digest" in payload:
                payload.pop("preparation_result_digest")
                payload["preparation_result_digest"] = payload_digest(payload)
            detail["completion_witness"] = payload
            detail["canonical_intent"]["completion_witness"] = payload
            opened.connection.execute("UPDATE maintenance_events SET detail_json=? WHERE maintenance_id=?", (canonical_json(detail), mid))


CONFLICTS = ["selector-core", "selector-intent", "selector-profile", "selector-witness",
    "completion-absent", "completion-family", "completion-core", "completion-profile", "completion-root-profile",
    "completion-runtime-allocation", "completion-source-digest", "completion-result-digest",
    "root-profile", "membership-revision", "membership-retired", "membership-witness", "runtime-catalog",
    "membership-missing", "membership-extra", "external-identity", "external-workspace",
    "character-linkage", "character-definition", "representation", "native-definition"]


def corrupt_fixture(root, intent, completion, conflict):
    if conflict.startswith("selector-"):
        field = {"selector-core": "core_id", "selector-intent": "descriptor_digest",
            "selector-profile": "profile_digest", "selector-witness": "core_witness_digest"}[conflict]
        value = str(UUID(int=990, version=4)) if field == "core_id" else "0" * 64
        with closing(selector._open_selector(selector.selector_paths(root).selector_path, writable=True)) as c:
            c.execute(f"UPDATE selector_state SET {field}=?", (value,))
            # Keep singleton/last ledger equal so core agreement must be checked.
            c.execute(f"UPDATE selector_ledger SET new_{field}=? WHERE generation=(SELECT max(generation) FROM selector_ledger)", (value,))
        return
    if conflict.startswith("completion-"):
        def mutate(value):
            if conflict == "completion-absent":
                return None
            if conflict == "completion-family":
                return AdmissionCompletionWitness(admission_identity_digest=completion.admission_identity_digest,
                    completed_descriptor_digest="1" * 64, completed_progress_digest="2" * 64,
                    native_core_id=completion.native_core_id, workspace_id="workspace",
                    whole_workspace_closure_digest="3" * 64, profile_digest=completion.profile_digest).payload()
            if conflict == "completion-core":
                value["native_core_id"] = str(UUID(int=999, version=4))
            elif conflict == "completion-profile":
                value["qualified_deployment_profile_digest"] = "0" * 64
            elif conflict == "completion-root-profile":
                value["root_profile"]["profile_revision_id"] = str(UUID(int=999, version=4))
                from torment_service.substrate.genesis_contracts import initial_membership_closure_digest, GenesisRootProfileReference
                value["initial_membership_closure_digest"] = initial_membership_closure_digest(
                    GenesisRootProfileReference.from_payload(value["root_profile"]), completion.runtime_scope_plans, completion.initial_memberships)
            elif conflict == "completion-runtime-allocation":
                value["runtime_scope_plans"][0]["scope_plan"]["target_semantic_scope_id"] = str(UUID(int=999, version=4))
            else:
                key = "source_intent_digest" if conflict == "completion-source-digest" else "result_digest"
                value["character_seed_completion"][key] = "0" * 64
            return value
        change_completion(root, completion, mutate)
        return
    if conflict in {"external-identity", "external-workspace", "character-linkage", "character-definition"}:
        paths = i4._owner_paths(intent)
        path = root / paths[2 if conflict == "external-identity" else 0 if conflict == "external-workspace" else -1]
        value = json.loads(path.read_bytes())
        if conflict == "external-identity":
            value["seed"]["core_traits"].append("foreign identity")
        elif conflict == "external-workspace":
            value["created_ts"] += 1
        elif conflict == "character-linkage":
            value["seed_eids"] = [9]
        else:
            value["character_name"] = "Changed stable character"
        path.write_bytes(owner_bytes(value))
        return
    if conflict == "root-profile" or conflict.startswith("membership-"):
        if conflict == "membership-extra":
            from torment_service.substrate.root_scope_membership import RootScopeMembershipService, RootScopeMembershipWitness
            from torment_service.substrate.root_profile import current_root_profile_generation
            from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
            with open_existing_native_core_connection(core_path(root, intent)) as opened:
                c = opened.connection
                source, identity, semantic, member_ns, operations = [UUID(int=n, version=4) for n in range(950, 955)]
                for table, identifier in [("legacy_source_namespaces", source), ("identity_namespaces", identity),
                    ("semantic_scopes", semantic), ("identity_namespaces", member_ns)]:
                    c.execute(f"INSERT INTO {table} VALUES (?,?,0)", (identifier.bytes, "foreign-" + str(identifier)))
                c.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (operations.bytes, "foreign-operations"))
                RootScopeMembershipService(c).admit(profile=current_root_profile_generation(c),
                    runtime_scope=NativeMemoryRuntimeScope("workspace", "SHARED_DOMAIN", source, identity, semantic, domain_id="foreign"),
                    witness=RootScopeMembershipWitness("foreign-member", "1" * 64, "foreign-operator", "QUALIFICATION_TEST"),
                    membership_identity_namespace_id=member_ns, idempotency_namespace_id=operations,
                    idempotency_key="i7-negative-extra-membership")
            return
        with corrupt_authority(root, intent, "profile-payload" if conflict == "root-profile" else "membership-lifecycle") as c:
            if conflict == "root-profile":
                c.execute("UPDATE object_revisions SET payload_text=json_set(payload_text,'$.profile_generation',2) WHERE object_id=?",
                    (UUID(completion.root_profile.payload()["profile_object_id"]).bytes,))
            else:
                rid = UUID(completion.initial_memberships[0].payload()["relationship_id"]).bytes
                if conflict == "membership-revision":
                    c.execute("UPDATE relationship_revisions SET relationship_revision_id=? WHERE relationship_id=?", (UUID(int=980, version=4).bytes, rid))
                elif conflict == "membership-retired":
                    c.execute("UPDATE relationship_revisions SET lifecycle_state='RETIRED' WHERE relationship_id=?", (rid,))
                elif conflict == "membership-missing":
                    c.execute("DELETE FROM relationships WHERE relationship_id=?", (rid,))
                else:
                    c.execute("UPDATE relationship_revisions SET payload_text=json_set(payload_text,'$.external_witness.witness_digest',?) WHERE relationship_id=?", ("0" * 64, rid))
        return
    with open_existing_native_core_connection(core_path(root, intent)) as opened:
        c = opened.connection
        if conflict == "runtime-catalog":
            c.execute("UPDATE identity_namespaces SET namespace_key=namespace_key || '-foreign'")
        elif conflict == "representation":
            with corrupt_immutable_table(c, "representation_payloads"):
                c.execute("UPDATE representation_payloads SET payload_bytes=?", (bytes(12),))
        else:
            c.execute("UPDATE operations SET canonical_intent_json=json_set(canonical_intent_json,'$.seed_definition_digest',?) WHERE idempotency_key LIKE '%:SOURCE:%'", ("0" * 64,))


@pytest.mark.parametrize("conflict", CONFLICTS)
def test_independent_active_corruption_refuses_without_repair_or_fallback(tmp_path, conflict):
    root, intent, sealed, _ = active_root(tmp_path)
    owner = owner_for(root, sealed.completion)
    corrupt_fixture(root, intent, sealed.completion, conflict)
    before = file_snapshot(root)
    try:
        with pytest.raises(DeploymentAuthorityError):
            recovery.recover_active_native_genesis(data_root=root, workspace_id="workspace")
        with pytest.raises(NativeProductionResourceOwnerError):
            owner._revalidate_authority()
        with pytest.raises(NativeProductionResourceOwnerError):
            owner_for(root, sealed.completion)
        assert resolve(root, sealed.completion).mode is not DeploymentResolutionMode.LEGACY_PUBLIC
        if conflict.startswith("selector-") or conflict in {"completion-absent", "completion-family", "completion-core",
            "completion-profile", "completion-runtime-allocation"}:
            assert read_genesis_fence(data_root=root).value == "CONFLICT"
    finally:
        owner.close()
    assert file_snapshot(root) == before


@pytest.mark.parametrize("kind", ["query", "write", "post-write"])
def test_existing_request_contexts_revalidate_genesis_before_use(tmp_path, kind):
    root, intent, sealed, _ = active_root(tmp_path)
    owner = owner_for(root, sealed.completion)
    runtime = owner._recover_active_runtime(workspace_id="workspace")
    def forbidden(*args, **kwargs):
        pytest.fail("stale context reached a query, writer or post-write adapter")
    dependency = SimpleNamespace(domain_ids=forbidden, route=forbidden, run=forbidden, close=lambda: None)
    if kind == "query":
        context = NativeProductionQueryContext(owner, dependency)
        invoke = context.domain_ids
    elif kind == "write":
        context = NativeProductionWriteContext(owner, runtime, dependency)
        invoke = lambda: context.route(None)
    else:
        context = NativeProductionPostWriteContext(owner, runtime, dependency)
        invoke = lambda: context.run(None)
    corrupt_fixture(root, intent, sealed.completion, "membership-witness")
    before = file_snapshot(root)
    with pytest.raises(NativeProductionResourceOwnerError):
        invoke()
    context.close()
    owner.close()
    assert file_snapshot(root) == before


@pytest.mark.parametrize("lookup,qualifier", [("private_lane", "agent"), ("shared_lane", "alpha")])
def test_returned_query_lane_and_retained_method_cannot_outlive_authority(tmp_path, lookup, qualifier):
    root, intent, sealed, _ = active_root(tmp_path)
    owner = owner_for(root, sealed.completion)
    def forbidden(*args, **kwargs):
        pytest.fail("stale returned lane reached its query adapter")
    lane = SimpleNamespace(search=forbidden)
    model = SimpleNamespace(private_lane=lambda *args: lane, shared_lane=lambda *args: lane, close=lambda: None)
    context = NativeProductionQueryContext(owner, model)
    returned = getattr(context, lookup)("workspace", qualifier)
    retained_method = returned.search
    corrupt_fixture(root, intent, sealed.completion, "membership-witness")
    before = file_snapshot(root)
    with pytest.raises(NativeProductionResourceOwnerError):
        retained_method("never reaches a query")
    with pytest.raises(NativeProductionResourceOwnerError):
        returned.search("never reaches a query")
    context.close()
    owner.close()
    assert file_snapshot(root) == before


def root_v2_fixture(tmp_path):
    """Run the existing fixture verbatim, omitting unrelated public/Fabric imports.

    Importing its full test module brings in the generative service surface.
    Its fixture needs none of those imports and is qualified here without any
    query, model or public service construction.
    """
    path = Path(__file__).with_name("test_post_i4_root_v2_production_recovery.py")
    tree = ast.parse(path.read_text(encoding="utf8"))
    body = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and (node.module in {
            "torment_service.public_runtime", "torment_service.fabric", "torment_service.memory_graph"}
            or (node.module == "torment_service" and any(alias.name == "public_runtime" for alias in node.names))):
            continue
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            continue
        body.append(node)
    namespace = {"__name__": "i7_root_v2_fixture"}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), namespace)
    return namespace["_active_root_fixture"](tmp_path)


def test_historical_v1_still_requires_its_descriptor(tmp_path):
    from test_b5_a3_production_native_resource_owner import _active_fixture
    root, _, descriptor, profile, agreement = _active_fixture(tmp_path)
    assert read_genesis_fence(data_root=root).value == "ABSENT"
    with pytest.raises(NativeProductionResourceOwnerError, match="v1.*descriptor"):
        NativeProductionResourceOwner.from_native_agreement(data_root=root, effective_profile=profile, agreement=agreement)
    before = file_snapshot(root)
    owner = NativeProductionResourceOwner.from_native_agreement(data_root=root, effective_profile=profile,
        agreement=agreement, admission_descriptor_path=descriptor)
    assert owner._genesis_completion is None and owner._root_v2_completion is None
    assert owner._recover_active_runtime().lookup_private("aria").memory_runtime_scope.workspace_id == "orchard"
    owner.close()
    assert file_snapshot(root) == before


def test_root_v2_still_recovers_without_descriptor_and_requires_disposition_receipt(tmp_path, monkeypatch):
    import torment_service.substrate.production_native_owner as owner_module
    root, profile, agreement = root_v2_fixture(tmp_path)
    assert read_genesis_fence(data_root=root).value == "ABSENT"
    before = file_snapshot(root)
    owner = NativeProductionResourceOwner.from_native_agreement(data_root=root, effective_profile=profile, agreement=agreement)
    assert owner._genesis_completion is None and owner._root_v2_completion is not None
    runtime = owner._recover_active_runtime(workspace_id="ws-one")
    assert runtime.lookup_private("agent-one").memory_runtime_scope.workspace_id == "ws-one"
    assert runtime.lookup_shared("domain-one").memory_runtime_scope.domain_id == "domain-one"
    owner.close()
    monkeypatch.setattr(owner_module, "read_root_disposition_execution_receipt", lambda **kwargs: None)
    with pytest.raises(NativeProductionResourceOwnerError, match="disposition receipt"):
        NativeProductionResourceOwner.from_native_agreement(data_root=root, effective_profile=profile, agreement=agreement)
    assert file_snapshot(root) == before


def startup_function_namespace(events):
    """Execute the actual startup function with inert compatibility surfaces.

    Selector resolution and NativeProductionResourceOwner remain real. Only the
    subsequent Fabric/public facade constructors are inert; no service starts.
    """
    path = Path(__file__).parents[1] / "torment_service/public_runtime.py"
    tree = ast.parse(path.read_text(encoding="utf8"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "create_public_runtime")
    class Owner:
        @staticmethod
        def from_native_agreement(**kwargs):
            owner = NativeProductionResourceOwner.from_native_agreement(**kwargs)
            events.append("owner")
            return owner
    class Fabric:
        character_store = None
        def __init__(self, **kwargs):
            events.append("fabric")
        def close(self):
            pass
    def facade(**kwargs):
        return SimpleNamespace(**kwargs)
    from torment_service.substrate.deployment_types import NativeGenesisCompletionWitness, RootAdmissionCompletionWitness
    namespace = dict(Path=Path, _RUNTIME_LOCK=threading.RLock(), _RUNTIME_CONFIGURATION={}, _RUNTIME_CACHE={},
        resolve_deployment_agreement=selector.resolve_deployment_agreement,
        inspect_contained_core_deployment=maintenance.inspect_contained_core_deployment,
        DeploymentResolutionMode=DeploymentResolutionMode, NativeGenesisCompletionWitness=NativeGenesisCompletionWitness,
        RootAdmissionCompletionWitness=RootAdmissionCompletionWitness, NativeProductionResourceOwner=Owner,
        TormentFabric=Fabric, PublicTormentRuntime=facade, NativePublicTormentRuntime=facade,
        PublicRuntimeMode=SimpleNamespace(LEGACY="LEGACY"), PublicRuntimeStartupRefused=RuntimeError)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, function], type_ignores=[])), str(path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("family", ["genesis-disabled", "genesis-enabled", "root-v2", "v1"])
def test_actual_startup_branch_recovers_descriptor_free_owner_before_compatibility(tmp_path, family):
    descriptor = None
    if family.startswith("genesis"):
        root, _, sealed, _ = active_root(tmp_path, family == "genesis-enabled")
        (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).unlink()
        profile = sealed.completion.qualified_deployment_profile
    elif family == "root-v2":
        root, profile, _ = root_v2_fixture(tmp_path)
    else:
        from test_b5_a3_production_native_resource_owner import _active_fixture
        root, _, descriptor, profile, _ = _active_fixture(tmp_path)
    events = []
    namespace = startup_function_namespace(events)
    before = file_snapshot(root)
    runtime = namespace["create_public_runtime"](root, SimpleNamespace(effective_profile=profile, admission_descriptor_path=descriptor))
    assert events == (["fabric", "owner"] if family == "v1" else ["owner", "fabric"])
    runtime.native_owner.close()
    assert file_snapshot(root) == before


def test_startup_conflict_never_constructs_compatibility_or_repairs(tmp_path):
    root, intent, sealed, _ = active_root(tmp_path)
    corrupt_fixture(root, intent, sealed.completion, "external-identity")
    events = []
    namespace = startup_function_namespace(events)
    before = file_snapshot(root)
    with pytest.raises(NativeProductionResourceOwnerError):
        namespace["create_public_runtime"](root, SimpleNamespace(
            effective_profile=sealed.completion.qualified_deployment_profile, admission_descriptor_path=None))
    assert events == [] and file_snapshot(root) == before


def test_absent_legacy_root_keeps_existing_resolution_without_creation(tmp_path):
    root = tmp_path / "never-created"
    from test_b5_a2_deployment_fence import _profile
    assert read_genesis_fence(data_root=root).value == "ABSENT"
    assert selector.resolve_deployment_agreement(data_root=root, effective_profile=_profile()).mode is DeploymentResolutionMode.LEGACY_PUBLIC
    assert not root.exists()


def test_production_i7_has_no_activation_or_publication_calls():
    repository = Path(__file__).parents[1]
    forbidden = {"establish_selector_era", "initialize_selector", "begin_cutover_pending", "enter_cutover_pending",
        "activate_core", "activate_selector_native", "plant_seed", "publish_if_absent", "replace_if_exact_predecessor"}
    for relative in ["substrate/genesis_recovery.py", "substrate/genesis_fence.py", "substrate/production_native_owner.py", "public_runtime.py"]:
        tree = ast.parse((repository / "torment_service" / relative).read_text(encoding="utf8"))
        calls = {n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else ""
                 for n in ast.walk(tree) if isinstance(n, ast.Call)}
        assert not calls.intersection(forbidden), relative
