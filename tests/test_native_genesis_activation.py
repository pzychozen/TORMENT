"""I8 qualification using disposable roots and committed literal representations."""
from contextlib import closing
from dataclasses import replace
import ast
import json
from pathlib import Path
import sqlite3

import pytest

from torment_service.external_owner_json import owner_bytes
from torment_service.substrate import genesis_activation_administration as i8
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_membership_administration as i5
from torment_service.substrate import genesis_completion_administration as i6
from torment_service.substrate import genesis_recovery as i7
from torment_service.substrate import deployment_selector as selector
from torment_service.substrate import deployment_core_maintenance as core
from torment_service.substrate.deployment_types import DeploymentResolutionMode, canonical_json
from torment_service.substrate.errors import SubstrateError
from torment_service.substrate.genesis_contracts import GenesisOperationRecord
from torment_service.substrate.genesis_fence import GenesisPreparationRefused, read_genesis_fence, read_genesis_operation_record
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime
from test_native_genesis_completion import prepared_root, run_seal, file_snapshot
from test_native_genesis_administration import quiet_observer, child
from test_native_genesis_character import core_path, corrupt_immutable_table
from test_native_genesis_membership import corrupt_authority
from test_native_genesis_recovery import owner_for, resolve, corrupt_fixture


@pytest.fixture(autouse=True)
def no_models_or_planting(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("I8 must use only committed literal Character representations")
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, "plant_seed", forbidden)
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, "_embed", forbidden)


def sealed_root(tmp_path, enabled=False):
    root, intent, *_ = prepared_root(tmp_path, enabled)
    return root, intent, run_seal(root, intent)


def run_activation(root, intent, **kwargs):
    kwargs.setdefault("observer", quiet_observer)
    kwargs.setdefault("operator_attestation", "Disposable root has no running service or writers.")
    kwargs.setdefault("issuer_reference", "i8-activation-operator")
    return i8.activate_genesis(data_root=root, intent=intent, **kwargs)


def authority_rows(root, intent):
    path = selector.selector_paths(root).selector_path
    ledger = []
    if path.exists():
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
            ledger = connection.execute("SELECT * FROM selector_ledger ORDER BY generation").fetchall()
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        events = connection.execute("SELECT * FROM maintenance_events ORDER BY completed_at_ns,maintenance_id").fetchall()
    return ledger, events


def prepared_native_rows(root, intent):
    with closing(i3._open_readonly(core_path(root, intent))) as connection:
        names = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {name: sorted(connection.execute('SELECT * FROM "' + name.replace('"', '""') + '"').fetchall(), key=repr)
                for name in names if name not in {"core_metadata", "deployment_metadata", "maintenance_events"}}


@pytest.mark.parametrize("enabled", [False, True])
def test_complete_activation_replay_and_admin_independence(tmp_path, enabled, monkeypatch):
    root, intent, sealed = sealed_root(tmp_path, enabled)
    native_before = prepared_native_rows(root, intent)
    stages, observations = [], []
    def observer(root, intent):
        observations.append(1)
        return quiet_observer(root, intent)
    def observe(stage):
        stages.append((stage, read_genesis_fence(data_root=root).value))
    result = run_activation(root, intent, observer=observer, fault=observe)
    assert observations == [1]
    assert result.completion == sealed.completion == result.core_result.completion_witness
    assert prepared_native_rows(root, intent) == native_before
    assert result.operation_record.administrative_phase.value == "COMPLETED"
    assert result.operation_record.phase_revision == sealed.operation_record.phase_revision + 2
    assert result.operation_record.quiescence_observations == sealed.operation_record.quiescence_observations
    assert owner_bytes(result.operation_record.sealed_completion_payload.payload()) == owner_bytes(sealed.completion.payload())
    assert [r.payload()["owner"] for r in result.operation_record.final_activation_references] == ["native-core-activation", "native-selector-activation"]
    assert result.selector_state.generation == 2 and result.selector_state.deployment_state.value == "NATIVE_ACTIVE"
    assert result.core_result.witness.core_role == "ACTIVE_CORE" and result.core_result.witness.deployment_state.value == "NATIVE_ACTIVE"
    assert all(fence == ("NATIVE_AUTHORITY_WINS" if name in ["after-selector-activation", "before-completed-checkpoint", "after-completed-checkpoint"] else "BLOCK_LEGACY") for name, fence in stages)
    ledger, events = authority_rows(root, intent)
    assert len(ledger) == 3 and len(events) == 2
    keys = i8.activation_operation_keys(intent)
    assert len(set(keys.values())) == 5
    before = file_snapshot(root)
    def forbidden(*args, **kwargs):
        pytest.fail("completed replay must not publish or observe")
    with monkeypatch.context() as patch:
        for module, names in [(selector, ["establish_selector_era", "initialize_selector", "begin_cutover_pending", "activate_selector_native"]),
                              (core, ["enter_cutover_pending", "activate_core"])]:
            for name in names:
                patch.setattr(module, name, forbidden)
        assert run_activation(root, intent, observer=forbidden) == result
    assert file_snapshot(root) == before
    assert authority_rows(root, intent) == (ledger, events)
    owner = owner_for(root, result.completion)
    runtime = owner._recover_active_runtime(workspace_id="workspace")
    assert owner._admission_descriptor_path is None and runtime.native_core_id == result.completion.native_core_id
    assert len(runtime.scopes) == 3
    assert runtime.lookup_private("agent").memory_runtime_scope.agent_id == "agent"
    assert {runtime.lookup_shared(name).memory_runtime_scope.domain_id for name in ["zeta", "alpha"]} == {"zeta", "alpha"}
    owner.close()
    i8._record_path(root).unlink()
    assert read_genesis_fence(data_root=root).value == "ABSENT"
    assert resolve(root, result.completion).mode is DeploymentResolutionMode.NATIVE_AGREEMENT
    assert i7.verify_active_native_genesis(data_root=root).completion == result.completion
    before = file_snapshot(root)
    owner = owner_for(root, result.completion)
    assert owner._recover_active_runtime(workspace_id="workspace") == runtime
    owner.close()
    with pytest.raises(GenesisPreparationRefused):
        run_activation(root, intent)
    assert file_snapshot(root) == before and not i8._record_path(root).exists()


BOUNDARIES = ["after-marker", "after-selector-initialization", "after-selector-pending", "after-core-pending",
    "after-core-activation", "before-core-activated-checkpoint", "after-core-activated-checkpoint",
    "after-selector-activation", "before-completed-checkpoint", "after-completed-checkpoint"]


class ResponseLost(BaseException):
    pass


def interrupt_at(root, intent, stage, monkeypatch):
    def fail(name):
        if name == stage:
            raise ResponseLost(name)
    original = selector.establish_selector_era
    def marker(**kwargs):
        original(**kwargs)
        fail("after-marker")
    with monkeypatch.context() as patch:
        patch.setattr(selector, "establish_selector_era", marker)
        with pytest.raises(ResponseLost, match=stage):
            run_activation(root, intent, fault=fail)


@pytest.mark.parametrize("stage", BOUNDARIES)
def test_response_loss_matrix_preserves_committed_authority(tmp_path, stage, monkeypatch):
    root, intent, sealed = sealed_root(tmp_path)
    interrupt_at(root, intent, stage, monkeypatch)
    before_record = read_genesis_operation_record(data_root=root)
    before_rows = authority_rows(root, intent)
    expected_native = BOUNDARIES.index(stage) >= 7
    assert read_genesis_fence(data_root=root).value == ("NATIVE_AUTHORITY_WINS" if expected_native else "BLOCK_LEGACY")
    if not expected_native:
        assert resolve(root, sealed.completion).mode is not DeploymentResolutionMode.LEGACY_PUBLIC
    observations = []
    def observer(root, intent):
        observations.append(1)
        return quiet_observer(root, intent)
    result = run_activation(root, intent, observer=observer)
    assert observations == ([] if expected_native else [1])
    assert result.operation_record.phase_revision == sealed.operation_record.phase_revision + 2
    assert result.operation_record.sealed_completion_payload == sealed.completion
    rows = authority_rows(root, intent)
    assert rows[0][:len(before_rows[0])] == before_rows[0] and rows[1][:len(before_rows[1])] == before_rows[1]
    assert len(rows[0]) == 3 and len(rows[1]) == 2
    assert result.operation_record.phase_revision - before_record.phase_revision in (0, 1, 2)


def test_marker_initialization_are_adjacent_calls_with_precomputed_identity():
    tree = ast.parse(Path(i8.__file__).read_text())
    target = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "activate_genesis")
    pairs = []
    for node in ast.walk(target):
        for field in ("body", "orelse", "finalbody"):
            statements = getattr(node, field, None)
            if not isinstance(statements, list):
                continue
            for index, statement in enumerate(statements):
                call = statement.value if isinstance(statement, ast.Expr) else None
                if isinstance(call, ast.Call) and ast.unparse(call.func) == "selector.establish_selector_era":
                    following = statements[index + 1]
                    assert isinstance(following, ast.Expr) and isinstance(following.value, ast.Call)
                    assert ast.unparse(following.value.func) == "selector.initialize_selector"
                    assert all(isinstance(k.value, ast.Name) for k in following.value.keywords)
                    pairs.append(1)
    assert pairs == [1]
    # The module has no direct SQLite writes or runtime/service construction.
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert not calls & {"sqlite3.connect", "open_existing_native_core_connection", "Fabric", "create_public_runtime", "plant_seed", "embed"}


def test_actual_foreign_selector_initialization_is_not_adopted(tmp_path):
    root, intent, _ = sealed_root(tmp_path)
    with i3.root_onboarding_lock(data_root=root):
        selector.establish_selector_era(data_root=root)
        selector.initialize_selector(data_root=root, operation_key="another-operator")
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused, match="another activation intent"):
        run_activation(root, intent)
    assert file_snapshot(root) == before


def test_copied_initialization_residue_is_not_accepted_as_publication_hard_link(tmp_path, monkeypatch):
    import shutil
    root, intent, _ = sealed_root(tmp_path)
    interrupt_at(root, intent, "after-selector-initialization", monkeypatch)
    paths = selector.selector_paths(root)
    copied = paths.deployment_root / (".selector-init-" + "a" * 32 + ".sqlite")
    shutil.copyfile(paths.selector_path, copied)
    assert not copied.samefile(paths.selector_path)
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused, match="foreign selector initialization residue"):
        run_activation(root, intent)
    assert file_snapshot(root) == before


CHILD_ACTIVATE = r'''
import sys,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tests'))
from test_native_genesis_activation import run_activation
from torment_service.substrate import deployment_selector as selector
from torment_service.substrate.genesis_fence import read_genesis_operation_record
root=Path(sys.argv[1])
intent=read_genesis_operation_record(data_root=root).expanded_intent
stage=sys.argv[2]
original=selector.establish_selector_era
def marker(**kwargs):
    original(**kwargs)
    if stage=='after-marker': os._exit(71)
selector.establish_selector_era=marker
def fault(name):
    if name==stage: os._exit(71)
result=run_activation(root,intent,fault=fault)
print(result.operation_record.administrative_phase.value,flush=True)
'''


@pytest.mark.parametrize("stage", ["after-marker", "after-core-activation", "after-selector-activation"])
def test_process_death_and_separate_process_recovery(tmp_path, stage):
    root, intent, sealed = sealed_root(tmp_path, True)
    process = child(CHILD_ACTIVATE, root, stage)
    output, error = process.communicate(timeout=60)
    assert process.returncode == 71, output + error
    before_rows = authority_rows(root, intent)
    process = child(CHILD_ACTIVATE, root, "no-fault")
    output, error = process.communicate(timeout=60)
    assert process.returncode == 0 and output.strip() == "COMPLETED", output + error
    rows = authority_rows(root, intent)
    assert rows[0][:len(before_rows[0])] == before_rows[0] and rows[1][:len(before_rows[1])] == before_rows[1]
    record = read_genesis_operation_record(data_root=root)
    assert record.phase_revision == sealed.operation_record.phase_revision + 2
    assert record.sealed_completion_payload == sealed.completion
    assert i7.recover_active_native_genesis(data_root=root).completion == sealed.completion


def test_root_lock_contends_in_another_process_and_recovers(tmp_path):
    root, intent, sealed = sealed_root(tmp_path)
    # child() deliberately has no stdin pipe. Use a process held at the live
    # observer by an explicit release file, so ownership spans the I8 sequence.
    code = CHILD_ACTIVATE.replace("result=run_activation(root,intent,fault=fault)", r'''
import time
from test_native_genesis_administration import quiet_observer
def observation(root,intent):
    Path(sys.argv[3]).write_text('locked')
    while not Path(sys.argv[4]).exists(): time.sleep(.02)
    return quiet_observer(root,intent)
result=run_activation(root,intent,observer=observation,fault=fault)
''')
    ready, release = tmp_path / "ready", tmp_path / "release"
    process = child(code, root, "no-fault", ready, release)
    try:
        import time
        deadline = time.monotonic() + 30
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        before = file_snapshot(root)
        with pytest.raises(GenesisPreparationRefused, match="root-onboarding-lock-busy"):
            run_activation(root, intent, timeout_seconds=0)
        assert file_snapshot(root) == before
    finally:
        release.write_text("release")
        output, error = process.communicate(timeout=60)
    assert process.returncode == 0, output + error
    assert run_activation(root, intent).completion == sealed.completion


@pytest.mark.parametrize("bad", ["missing", "untyped", "stale", "incomplete", "running-writer", "unresolved-listener", "foreign-root", "attestation", "issuer"])
def test_activation_observation_refuses_before_publication(tmp_path, bad):
    root, intent, sealed = sealed_root(tmp_path)
    before = file_snapshot(root)
    def observe(root, intent):
        facts = quiet_observer(root, intent)
        if bad == "untyped": return facts.__dict__
        if bad == "stale": return replace(facts, observed_at_ns=0)
        if bad == "incomplete": return replace(facts, complete=False)
        if bad == "running-writer":
            return replace(facts, writers=(replace(facts.writers[0], result=i3.WriterObservationResult.RUNNING),) + facts.writers[1:])
        if bad == "unresolved-listener":
            return replace(facts, listeners=())
        if bad == "foreign-root": return replace(facts, data_root_identity=str(root.parent))
        return facts
    kwargs = dict(observer=None if bad == "missing" else observe)
    if bad in ("attestation", "issuer"):
        kwargs["operator_attestation" if bad == "attestation" else "issuer_reference"] = ""
    with pytest.raises(SubstrateError):
        run_activation(root, intent, **kwargs)
    assert file_snapshot(root) == before
    assert not selector.selector_paths(root).marker_path.exists()


@pytest.mark.parametrize("conflict", ["root-profile", "membership-witness", "external-workspace", "external-identity", "character-linkage", "representation"])
def test_final_reread_refuses_observation_time_drift(tmp_path, conflict):
    root, intent, sealed = sealed_root(tmp_path, True)
    def observation(root, intent):
        corrupt_fixture(root, intent, sealed.completion, conflict)
        return quiet_observer(root, intent)
    with pytest.raises(SubstrateError):
        run_activation(root, intent, observer=observation)
    assert not selector.selector_paths(root).marker_path.exists()
    assert i8._record_path(root).read_bytes() == owner_bytes(sealed.operation_record.payload())


@pytest.mark.parametrize("stage,conflict", [
    ("after-selector-initialization", "foreign-key"),
    ("after-selector-pending", "selector-core"), ("after-selector-pending", "selector-intent"),
    ("after-selector-pending", "selector-profile"), ("after-core-pending", "selector-witness"),
    ("after-core-pending", "core-key"), ("after-core-activation", "completion-root-profile"),
    ("after-core-activation", "completion-family"), ("after-selector-activation", "selector-core"),
    ("after-core-pending", "root-profile"), ("after-core-pending", "membership-retired"),
    ("after-core-pending", "external-identity"), ("after-core-pending", "external-workspace"),
    ("after-core-pending", "character-linkage"), ("after-core-pending", "representation"),
    ("after-core-activated-checkpoint", "admin-core-reference"), ("after-completed-checkpoint", "admin-selector-reference"),
])
def test_partial_or_active_contradiction_refuses_without_repair(tmp_path, stage, conflict, monkeypatch):
    root, intent, sealed = sealed_root(tmp_path, True)
    interrupt_at(root, intent, stage, monkeypatch)
    if conflict == "foreign-key":
        with closing(selector._open_selector(selector.selector_paths(root).selector_path, writable=True)) as connection:
            row = connection.execute("SELECT canonical_intent FROM selector_ledger WHERE generation=0").fetchone()
            value = json.loads(row[0]); value["operation_key"] = "foreign-initializer"
            connection.execute("UPDATE selector_ledger SET operation_key=?,canonical_intent=? WHERE generation=0", ("foreign-initializer", canonical_json(value)))
    elif conflict == "core-key":
        with closing(sqlite3.connect(core_path(root, intent))) as connection:
            row = connection.execute("SELECT detail_json FROM maintenance_events").fetchone()
            value = json.loads(row[0]); value["operation_key"] = value["canonical_intent"]["operation_key"] = "foreign-pending"
            connection.execute("UPDATE maintenance_events SET detail_json=?", (canonical_json(value),))
            connection.commit()
    elif conflict.startswith("admin-"):
        value = json.loads(i8._record_path(root).read_bytes())
        value["final_activation_references"][-1]["result_digest"] = "0" * 64
        i8._record_path(root).write_bytes(owner_bytes(value))
    else:
        corrupt_fixture(root, intent, sealed.completion, conflict)
    before = file_snapshot(root)
    with pytest.raises(SubstrateError):
        run_activation(root, intent)
    assert file_snapshot(root) == before


@pytest.mark.parametrize("stage", ["after-core-activation", "after-completed-checkpoint"])
def test_old_mutators_refuse_after_native_core_activation(tmp_path, stage, monkeypatch):
    root, intent, _ = sealed_root(tmp_path)
    interrupt_at(root, intent, stage, monkeypatch)
    before = file_snapshot(root)
    for begin in [i3.begin_genesis_administration, i4.begin_genesis_character_administration,
                  i5.begin_genesis_membership_administration, i6.begin_genesis_completion_administration]:
        with pytest.raises(GenesisPreparationRefused):
            with begin(data_root=root, intent=intent):
                pytest.fail("old administration must not reopen activated preparation")
    assert file_snapshot(root) == before


@pytest.mark.parametrize("stage", ["after-core-activated-checkpoint", "after-selector-activation", "after-completed-checkpoint"])
def test_optional_completion_cache_recovers_native_evidence(tmp_path, stage, monkeypatch):
    root, intent, sealed = sealed_root(tmp_path)
    interrupt_at(root, intent, stage, monkeypatch)
    value = json.loads(i8._record_path(root).read_bytes())
    value["sealed_completion_payload"] = None
    record = GenesisOperationRecord.from_payload(value)
    i8._record_path(root).write_bytes(owner_bytes(record.payload()))
    result = run_activation(root, intent)
    assert result.completion == sealed.completion
    assert result.operation_record.sealed_completion_payload is None
    assert result.operation_record.phase_revision == sealed.operation_record.phase_revision + 2


def test_unsealed_or_absent_operation_refuses_without_publication(tmp_path):
    root, intent, *_ = prepared_root(tmp_path)
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused):
        run_activation(root, intent)
    assert file_snapshot(root) == before
    i8._record_path(root).unlink()
    before = file_snapshot(root)
    with pytest.raises(GenesisPreparationRefused):
        run_activation(root, intent)
    assert file_snapshot(root) == before


def test_exact_seven_field_profile_configures_actual_public_configuration(tmp_path):
    from dataclasses import dataclass
    from torment_service.substrate.deployment_types import QualifiedDeploymentProfile
    root, intent, sealed = sealed_root(tmp_path)
    result = run_activation(root, intent)
    path = Path(i8.__file__).parents[1] / "public_runtime.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    definition = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PublicRuntimeConfiguration")
    namespace = dict(dataclass=dataclass, QualifiedDeploymentProfile=QualifiedDeploymentProfile, Path=Path)
    exec(compile(ast.Module(body=[definition], type_ignores=[]), str(path), "exec"), namespace)
    payload = sealed.qualified_profile_payload
    assert len(payload) == 7
    config = namespace["PublicRuntimeConfiguration"](effective_profile=QualifiedDeploymentProfile(**payload), admission_descriptor_path=None)
    assert config.effective_profile.digest == result.selector_state.profile_digest
    assert config.admission_descriptor_path is None
