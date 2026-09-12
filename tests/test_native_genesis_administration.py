"""I3 administration and pre-materialization fence, disposable roots only."""

from __future__ import annotations

import ast
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

from torment_service.external_owner_json import owner_bytes
from torment_service.substrate import genesis_administration as a
from torment_service.substrate import genesis_fence as f
from torment_service.substrate import genesis_contracts as g
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.deployment_types import DeploymentResolutionMode
from torment_service.substrate.writer_freeze_evidence import (
    ListenerObservation, ListenerObservationResult, RootWriterClass,
    WriterObservationResult, WriterProcessObservation,
)
from test_native_genesis_contracts import intent_payload


def intent_for(root, enabled=False):
    payload = intent_payload(enabled)
    payload["data_root_identity"] = str(f.canonical_genesis_root(root))
    return g.GenesisIntent.from_payload(payload)


def quiet_observer(root, intent):
    assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.BLOCK_LEGACY
    return a.GenesisWriterObservation(
        str(root), intent.operation_key, time.time_ns(),
        tuple(WriterProcessObservation(c, "injected disposable observation", WriterObservationResult.ABSENT) for c in RootWriterClass),
        (ListenerObservation("disposable-root-service", "injected listener census", ListenerObservationResult.ABSENT),), True,
    )


def observe(session, observer=quiet_observer):
    return session.observe_quiescence(observer, operator_attestation="Test root writers are stopped.", issuer_reference="disposable-test-operator")


def prepare(root, intent=None, fault=a._noop):
    return a.prepare_genesis_inert_root(
        data_root=root, intent=intent or intent_for(root), observer=quiet_observer,
        operator_attestation="Test root writers are stopped.", issuer_reference="disposable-test-operator", fault=fault,
    )


def files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and not p.name.endswith(".lock")}


def child(code, *args):
    # An audit harness may inject a startup script into this child; it contains
    # only test-boundary checks, never production observation or service code.
    guard = os.environ.get("TORMENT_GENESIS_I3_CHILD_AUDIT")
    if guard:
        code = "exec(open(" + repr(guard) + ", encoding='utf8').read())\n" + code
    return subprocess.Popen([sys.executable, "-B", "-X", "utf8", "-c", code, *map(str, args)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.mark.parametrize("state", ["absent", "empty", "readme", "gitkeep", "substrate", "deployment", "lock"])
def test_accepted_start_and_first_fence_order(tmp_path, state):
    root = tmp_path / "root"
    if state != "absent":
        root.mkdir()
    if state in ("readme", "gitkeep"):
        (root / ("README.md" if state == "readme" else ".gitkeep")).write_text("fixture")
    if state in ("substrate", "deployment", "lock"):
        (root / "substrate").mkdir()
    if state in ("deployment", "lock"):
        (root / a.CONTROL_DIRECTORY).mkdir()
    if state == "lock":
        (root / a.CONTROL_DIRECTORY / a.LOCK_NAME).touch()
    intent = intent_for(root)
    before = files(root) if root.exists() else {}
    # The coherent observation occurs after the rendezvous control paths exist.
    kind = "PRE_INTENT_GENESIS_CONTROL_RESIDUE"
    assert a.inspect_genesis_start(data_root=root, intent=intent).payload()["classification"] == kind
    assert (files(root) if root.exists() else {}) == before
    with a.begin_genesis_administration(data_root=root, intent=intent) as session:
        assert session.record.accepted_start_observation.payload()["classification"] == kind
        assert session.record.phase_revision == 1
        assert session.record.administrative_phase is g.GenesisAdministrativePhase.PREPARING
        assert not session.record.quiescence_observations
        assert not (root / a.CORE_DIRECTORY).exists()
        assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.BLOCK_LEGACY
    snapshot = files(root)
    record_path = root / a.CONTROL_DIRECTORY / a.RECORD_NAME
    timestamp = record_path.stat().st_mtime_ns
    with a.begin_genesis_administration(data_root=root, intent=intent) as replay:
        assert replay.record == session.record
    assert files(root) == snapshot
    assert record_path.stat().st_mtime_ns == timestamp


@pytest.mark.parametrize("artifact", [
    "unknown.txt", "workspaces/legacy/workspace_meta.json", "substrate/cores/foreign.db",
    "substrate/deployment/selector-era-v1.json", "substrate/deployment/selector.sqlite",
    "substrate/deployment/genesis-operation.json", "substrate/deployment/.unrelated.tmp",
    "substrate/deployment/.genesis-operation.json.publication.lock",
])
def test_unknown_legacy_selector_core_and_malformed_entry_refuse_without_changes(tmp_path, artifact):
    root = tmp_path / "root"
    path = root / artifact
    path.parent.mkdir(parents=True)
    path.write_bytes(b"unexplained fixture")
    before = files(root)
    before_paths = {p.relative_to(root).as_posix() for p in root.rglob("*")}
    with pytest.raises(a.GenesisPreparationRefused):
        with a.begin_genesis_administration(data_root=root, intent=intent_for(root)):
            pytest.fail("invalid root accepted")
    assert files(root) == before
    # Shallow peer-possible evidence may establish only the OS rendezvous.
    after_paths = {p.relative_to(root).as_posix() for p in root.rglob("*")}
    assert after_paths - before_paths <= set(g.GenesisAcceptedStart.CONTROL_ENTRIES)


def test_allowed_files_plus_control_residue_are_accepted_under_mutex(tmp_path):
    # The selected observation boundary permits allowed files plus its controls.
    root = tmp_path / "root"
    (root / "substrate").mkdir(parents=True)
    (root / "README.md").write_text("retained")
    before = (root / "README.md").read_bytes()
    with a.begin_genesis_administration(data_root=root, intent=intent_for(root)) as session:
        start = session.record.accepted_start_observation.payload()
        assert start["classification"] == "PRE_INTENT_GENESIS_CONTROL_RESIDUE"
        assert start["observed_entries"] == list(g.GenesisAcceptedStart.CONTROL_ENTRIES) + ["README.md"]
    assert (root / "README.md").read_bytes() == before


def test_competing_intent_and_root_identity_refuse(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    with a.begin_genesis_administration(data_root=root, intent=intent):
        pass
    payload = intent.payload()
    for key, value in (("operation_key", "other-operation"), ("data_root_identity", "other-root")):
        altered = g.GenesisIntent.from_payload({**payload, key: value})
        before = files(root)
        with pytest.raises(a.GenesisPreparationRefused):
            with a.begin_genesis_administration(data_root=root, intent=altered):
                pytest.fail("foreign operation accepted")
        assert files(root) == before


def test_noncontrol_delta_during_lock_acquisition_is_refused(tmp_path, monkeypatch):
    root = tmp_path / "root"
    original = a._establish_control

    def race(path):
        original(path)
        (path / "racing-writer.txt").write_text("not adopted")

    monkeypatch.setattr(a, "_establish_control", race)
    with pytest.raises(a.GenesisPreparationRefused, match="unknown artifact"):
        with a.begin_genesis_administration(data_root=root, intent=intent_for(root)):
            pytest.fail("racing writer accepted")
    assert not (root / a.CONTROL_DIRECTORY / a.RECORD_NAME).exists()


def test_root_mutex_competitor_alias_death_and_persistent_filename(tmp_path):
    root = tmp_path / "root"
    code = """import os,sys
from torment_service.substrate.genesis_administration import root_onboarding_lock
with root_onboarding_lock(data_root=sys.argv[1]):
 print('LOCKED',flush=True)
 sys.stdin.read(1)
 os._exit(9)
"""
    # PIPE keeps the child alive until its explicit hard-exit, including Windows.
    guard = os.environ.get("TORMENT_GENESIS_I3_CHILD_AUDIT")
    if guard:
        code = "exec(open(" + repr(guard) + ", encoding='utf8').read())\n" + code
    process = subprocess.Popen([sys.executable, "-B", "-c", code, str(root)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert process.stdout.readline().strip() == "LOCKED"
        alias = root / "." / ".." / "root"
        start = time.monotonic()
        with pytest.raises(a.GenesisPreparationRefused, match="lock-busy"):
            with a.root_onboarding_lock(data_root=alias, timeout_seconds=0.1):
                pytest.fail("competing alias lock acquired")
        assert time.monotonic() - start < 3
        process.communicate("x", timeout=10)
        assert process.returncode == 9
        assert (root / a.CONTROL_DIRECTORY / a.LOCK_NAME).exists()
        with a.root_onboarding_lock(data_root=alias, timeout_seconds=0):
            assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.ABSENT
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def test_actual_windows_junction_or_posix_symlink_refused(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    if os.name == "nt":
        outcome = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(target)], capture_output=True, text=True)
        assert outcome.returncode == 0, outcome.stderr
    else:
        alias.symlink_to(target, target_is_directory=True)
    with pytest.raises(a.GenesisPreparationRefused, match="reparse"):
        f.canonical_genesis_root(alias)
    assert not list(target.iterdir())


def test_checkpoint_cas_and_response_loss(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    with a.begin_genesis_administration(data_root=root, intent=intent) as session:
        original = session.record
        evidence = observe(session)
        updated = session.record
        assert updated.quiescence_observations == (evidence,)
        timestamp = (root / a.CONTROL_DIRECTORY / a.RECORD_NAME).stat().st_mtime_ns
        session.replace_record(original, updated)  # lost response, exact replacement
        assert (root / a.CONTROL_DIRECTORY / a.RECORD_NAME).stat().st_mtime_ns == timestamp
        conflicting = replace(updated, quiescence_observations=())
        with pytest.raises(a.GenesisPreparationRefused, match="predecessor"):
            session.replace_record(original, conflicting)
        with pytest.raises(a.GenesisPreparationRefused):
            session.replace_record(updated, original)
    assert f.read_genesis_operation_record(data_root=root) == updated
    with pytest.raises(a.GenesisPreparationRefused, match="ended"):
        session.prepare_inert_core()


@pytest.mark.parametrize("case", ["running", "unresolved", "listener-active", "listener-unresolved", "incomplete", "missing-writer", "duplicate-writer", "missing-listener", "competing", "foreign-root", "foreign-operation", "stale"])
def test_quiescence_refusal_keeps_first_fence_and_no_core(tmp_path, case):
    root = tmp_path / "root"

    def observer(path, intent):
        facts = quiet_observer(path, intent)
        if case in ("running", "unresolved"):
            facts = replace(facts, writers=(replace(facts.writers[0], result=WriterObservationResult(case.upper())), *facts.writers[1:]))
        elif case.startswith("listener-"):
            facts = replace(facts, listeners=(replace(facts.listeners[0], result=ListenerObservationResult(case.split("-")[1].upper())),))
        elif case == "incomplete": facts = replace(facts, complete=False)
        elif case == "missing-writer": facts = replace(facts, writers=facts.writers[:-1])
        elif case == "duplicate-writer": facts = replace(facts, writers=(facts.writers[0],) * len(RootWriterClass))
        elif case == "missing-listener": facts = replace(facts, listeners=())
        elif case == "competing": facts = replace(facts, competing_operation_keys=("other",))
        elif case == "foreign-root": facts = replace(facts, data_root_identity="other")
        elif case == "foreign-operation": facts = replace(facts, operation_key="other")
        elif case == "stale": facts = replace(facts, observed_at_ns=0)
        return facts

    with a.begin_genesis_administration(data_root=root, intent=intent_for(root)) as session:
        with pytest.raises(a.GenesisPreparationRefused):
            observe(session, observer)
        assert session.record.phase_revision == 1
        with pytest.raises(a.GenesisPreparationRefused, match="quiescence"):
            session.prepare_inert_core()
    assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.BLOCK_LEGACY
    assert not (root / a.CORE_DIRECTORY).exists()
    with a.begin_genesis_administration(data_root=root, intent=intent_for(root)) as session:
        observe(session)


@pytest.mark.parametrize("state", ["absent", "empty", "preparing", "malformed", "wrong-root", "duplicate-json-key"])
def test_fence_and_resolver_read_only_no_sqlite(tmp_path, monkeypatch, state):
    root = tmp_path / "root"
    if state != "absent": root.mkdir()
    if state not in ("absent", "empty"):
        with a.begin_genesis_administration(data_root=root, intent=intent_for(root)):
            pass
        path = root / a.CONTROL_DIRECTORY / a.RECORD_NAME
        if state == "malformed": path.write_bytes(b"{")
        elif state == "wrong-root":
            payload = intent_for(root).payload()
            payload["data_root_identity"] = "other"
            foreign = g.GenesisIntent.from_payload(payload)
            record = f.read_genesis_operation_record(data_root=root)
            accepted = record.accepted_start_observation.payload()
            accepted["data_root_identity"] = "other"
            path.write_bytes(owner_bytes(replace(record, expanded_intent=foreign, intent_digest=foreign.digest,
                accepted_start_observation=g.GenesisAcceptedStart.from_payload(accepted)).payload()))
        elif state == "duplicate-json-key":
            path.write_bytes(path.read_bytes().replace(b'"version": 1', b'"version": 1, "version": 1', 1))
    before = files(root) if root.exists() else {}
    import sqlite3
    monkeypatch.setattr(sqlite3, "connect", lambda *args, **kwargs: pytest.fail("fence opened SQLite"))
    # Profile is irrelevant to absent/preparing evidence; no profile is finalized.
    result = resolve_deployment_agreement(data_root=root, effective_profile=None)
    assert result.mode is DeploymentResolutionMode.REFUSED
    assert result.reason == ("fresh-root-requires-native-genesis" if state in ("absent", "empty") else
                             "native-genesis-preparation-incomplete" if state == "preparing" else "native-genesis-evidence-invalid")
    assert (files(root) if root.exists() else {}) == before
    if state == "absent": assert not root.exists()


def test_no_genesis_record_does_not_make_unrelated_residue_legacy(tmp_path):
    root = tmp_path / "legacy-root"
    root.mkdir()
    # The Genesis reader stays ABSENT; I11 separately refuses ambiguous residue.
    (root / "substrate").write_text("historical non-Genesis fixture")
    assert f.read_genesis_fence(data_root=root) is g.GenesisFenceDisposition.ABSENT
    assert resolve_deployment_agreement(data_root=root, effective_profile=None).reason == "pre-selector-root-ambiguous-or-invalid"


def test_formatted_matching_record_reuses_then_checkpoints_actual_predecessor(tmp_path):
    root = tmp_path / "root"
    intent = intent_for(root)
    with a.begin_genesis_administration(data_root=root, intent=intent) as session:
        original = session.record
    path = root / a.CONTROL_DIRECTORY / a.RECORD_NAME
    formatted = json.dumps(original.payload(), indent=4).encode("utf8")
    path.write_bytes(formatted)
    with a.begin_genesis_administration(data_root=root, intent=intent) as session:
        assert path.read_bytes() == formatted
        observe(session)
    assert f.read_genesis_operation_record(data_root=root).phase_revision == 2


def actual_fabric_constructor():
    """Compile the actual complete constructor, avoiding unrelated module imports.

    A sentinel is injected at the original canonical-root call: if reached, the
    historical path is continuing. No embedder/Brainvision/Fabric host is loaded.
    """
    source = Path(a.__file__).parents[1] / "fabric.py"
    tree = ast.parse(source.read_text(encoding="utf8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TormentFabric")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), init], type_ignores=[])
    namespace = {"__package__": "torment_service"}
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    return namespace["__init__"], namespace


@pytest.mark.parametrize("state", ["absent", "empty", "preparing", "malformed"])
def test_direct_actual_fabric_constructor_guard_before_any_effect(tmp_path, state):
    root = tmp_path / "root"
    if state != "absent": root.mkdir()
    if state in ("preparing", "malformed"):
        with a.begin_genesis_administration(data_root=root, intent=intent_for(root)):
            pass
        if state == "malformed": (root / a.CONTROL_DIRECTORY / a.RECORD_NAME).write_bytes(b"{")
    before = files(root) if root.exists() else {}
    init, namespace = actual_fabric_constructor()

    class HistoricalPathReached(BaseException): pass

    def reached(*args, **kwargs): raise HistoricalPathReached()

    namespace.update(_canonical_data_root=reached, build_embedder_from_env=lambda: pytest.fail("embedder invoked"))
    instance = SimpleNamespace()
    expected = a.GenesisPreparationRefused if state in ("preparing", "malformed") else HistoricalPathReached
    with pytest.raises(expected):
        init(instance, str(root))
    if state in ("preparing", "malformed"):
        assert not vars(instance)
    assert (files(root) if root.exists() else {}) == before
