"""Coherent observation qualification: real peers, explicit gates, no models."""
from contextlib import contextmanager, closing
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from torment_service import atomic_publication as atomic
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_recovery as i7
from torment_service.substrate.errors import SubstrateError
from test_native_genesis_onboarding import planned, run_driver, confirmation, onboarding, assert_control_only
from test_native_genesis_completion import file_snapshot
from test_native_genesis_administration import child


PEER = r"""
import sys, os, time, json, hashlib
from pathlib import Path
from contextlib import contextmanager
sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_native_genesis_onboarding import onboarding, run_driver
from torment_service import atomic_publication as atomic
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_activation_administration as i8
path, ready, release = map(Path, sys.argv[1:4])
stage, disposition = sys.argv[4:6]
paused = False

def pause(target=None, temporary=None):
    global paused
    if paused:
        return
    paused = True
    value = dict(stage=stage, target=str(target) if target else None, temporary=str(temporary) if temporary else None)
    if temporary:
        value['temporary_sha256'] = hashlib.sha256(temporary.read_bytes()).hexdigest()
    ready.write_text(json.dumps(value))
    deadline = time.monotonic() + 30
    while not release.exists():
        if time.monotonic() >= deadline:
            raise RuntimeError('test publisher gate timed out')
        time.sleep(.01)
    if disposition == 'die':
        os._exit(71)

original_link = os.link
def link(source, target, *args, **kwargs):
    if stage == 'selector-marker' and Path(target).name == 'selector-era-v1.json':
        pause(Path(target), Path(source))
    return original_link(source, target, *args, **kwargs)
os.link = link

original_prepared = atomic._prepared_file
@contextmanager
def prepared(target, content):
    with original_prepared(target, content) as temporary:
        matches = (stage == 'i3-temp' and target.name == 'genesis-operation.json' and not target.exists()
            or stage == 'i4-temp' and target.name == 'workspace_meta.json'
            or stage == 'checkpoint' and target.name == 'genesis-operation.json' and target.exists())
        if matches:
            pause(target, temporary)
        yield temporary
atomic._prepared_file = prepared
original_sync = atomic._sync_publication
def sync(target):
    original_sync(target)
    if stage == 'published' and target.name == 'genesis-operation.json':
        # This is still inside the real prepared-file context, before cleanup.
        temporary = next(target.parent.glob('.genesis-operation.json.*.tmp'))
        pause(target, temporary)
atomic._sync_publication = sync
original_mutex = i3.root_onboarding_lock
@contextmanager
def mutex(**kwargs):
    with original_mutex(**kwargs) as root:
        if stage == 'mutex':
            pause()
        yield root
i3.root_onboarding_lock = mutex
original_activation = i8.activate_genesis
def activation(**kwargs):
    def fault(point):
        if stage == 'mid-i8' and point == 'after-selector-pending':
            pause()
    return original_activation(**kwargs, fault=fault)
i8.activate_genesis = activation
def phase_fault(point):
    if stage == 'between-phases' and point == 'after-i3':
        pause()
intent = onboarding.read_intent_plan(path)
print(json.dumps(run_driver(intent, path, fault=phase_fault)), flush=True)
"""


FOLLOWER = r"""
import sys, json
from pathlib import Path
from contextlib import contextmanager
sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_native_genesis_onboarding import onboarding, run_driver
from torment_service.substrate import genesis_administration as i3
path, attempted, result_path = map(Path, sys.argv[1:4])
intent = onboarding.read_intent_plan(path)
root = Path(intent.data_root_identity)
inside = False
def audit_open(event, args):
    if event != 'open' or not isinstance(args[0], (str, bytes)):
        return
    import os
    path = Path(os.fsdecode(args[0]))
    if path.is_relative_to(root) and path != root / i3.CONTROL_DIRECTORY / i3.LOCK_NAME:
        if not inside:
            raise AssertionError('pre-lock content open: ' + str(path))
        mode, flags = args[1], args[2]
        reading = (isinstance(mode, str) and mode.startswith('r')) or flags & (os.O_WRONLY | os.O_RDWR) == os.O_RDONLY
        if path.name.endswith('.tmp') and reading:
            raise AssertionError('publisher temporary opened as evidence: ' + str(path))
sys.addaudithook(audit_open)
original_mutex = i3.root_onboarding_lock
@contextmanager
def mutex(**kwargs):
    global inside
    attempted.write_text('attempting existing root mutex')
    with original_mutex(**kwargs) as held:
        inside = True
        try:
            yield held
        finally:
            inside = False
i3.root_onboarding_lock = mutex
# Exercise all startup observation surfaces as well as the iteration boundary.
request = onboarding.request_from_intent(intent)
assert onboarding.prepare_intent_plan(request, intent_path=path) == intent
assert onboarding.onboarding_needs_embedding(intent) is False
result = run_driver(intent, path)
result_path.write_text(json.dumps(result))
print(json.dumps(result), flush=True)
"""


def wait_file(path, processes):
    deadline = time.monotonic() + 30
    while not path.exists() and all(p.poll() is None for p in processes) and time.monotonic() < deadline:
        time.sleep(.01)
    assert path.exists(), 'peer did not reach its explicit test gate'


@pytest.mark.parametrize('stage,disposition', [
    ('i3-temp', 'continue'), ('i4-temp', 'continue'), ('checkpoint', 'continue'), ('mid-i8', 'continue'),
    ('selector-marker', 'die'), ('mutex', 'die'), ('i3-temp', 'die'), ('i4-temp', 'die'), ('published', 'die'), ('between-phases', 'die'),
])
def test_matching_peer_observation_and_process_death(tmp_path, stage, disposition):
    root, request, path, intent = planned(tmp_path)
    ready, release, attempted = (tmp_path / name for name in ('ready', 'release', 'attempted'))
    follower_result = tmp_path / 'follower-result.json'
    first = child(PEER, path, ready, release, stage, disposition)
    second = None
    outputs = []
    try:
        wait_file(ready, [first])
        checkpoint = json.loads(ready.read_text())
        second = child(FOLLOWER, path, attempted, follower_result)
        wait_file(attempted, [first, second])
    finally:
        release.write_text('release publisher')
        outputs.append(first.communicate(timeout=60))
        if second is not None:
            outputs.append(second.communicate(timeout=60))
    assert first.returncode == (71 if disposition == 'die' else 0), outputs
    assert second is not None and second.returncode == 0, outputs
    result = json.loads(outputs[1][0])
    assert result == json.loads(follower_result.read_text())
    if disposition == 'continue':
        assert json.loads(outputs[0][0]) == result
    else:
        assert not outputs[0][0] and not outputs[0][1]
    assert result['status'] == 'NATIVE_ACTIVE'
    with i3.root_observation(data_root=root) as held:
        authority = held.observe(i7.recover_active_native_genesis, data_root=root)
        assert authority.completion.expanded_intent == intent
        with closing(i3._open_readonly(authority.core_database_path)) as connection:
            assert connection.execute('select count(*) from maintenance_events').fetchone()[0] == 2
    if disposition == 'die' and checkpoint['temporary']:
        import hashlib
        temporary = Path(checkpoint['temporary'])
        assert temporary.is_file()
        assert hashlib.sha256(temporary.read_bytes()).hexdigest() == checkpoint['temporary_sha256']
    assert run_driver(intent, path) == result


@pytest.mark.parametrize('artifact', [
    'substrate/deployment/.foreign.json.abc12345.tmp',
    'substrate/deployment/.genesis-operation.json.short.tmp',
    'unowned.txt', 'workspace/legacy/graph.db',
    'workspaces/workspace/agents/agent/legacy-vectors.npy',
])
def test_unknown_artifact_and_foreign_temporary_still_refuse(tmp_path, artifact):
    root, request, path, intent = planned(tmp_path)
    target = root / artifact
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b'foreign artifact')
    before = file_snapshot(root)
    with pytest.raises(SubstrateError):
        run_driver(intent, path)
    assert file_snapshot(root) == before
    assert onboarding.read_genesis_operation_record(data_root=root) is None


def test_exact_owned_target_residue_is_not_opened_or_adopted(tmp_path, monkeypatch):
    root, request, path, intent = planned(tmp_path)
    temporary = root / i3.CONTROL_DIRECTORY / '.genesis-operation.json.abc12345.tmp'
    temporary.write_bytes(b'not a Genesis record; never parse or adopt')
    original = Path.open
    def guarded(path, *args, **kwargs):
        if path == temporary:
            pytest.fail('temporary residue opened as semantic evidence')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)
    assert run_driver(intent, path)['status'] == 'NATIVE_ACTIVE'
    assert temporary.exists()


@pytest.mark.parametrize('failures', [1, 2])
def test_permission_error_under_mutex_has_one_bounded_reread(tmp_path, monkeypatch, failures):
    root, request, path, intent = planned(tmp_path)
    original = i3._inventory
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(1)
        if len(calls) <= failures:
            raise PermissionError('test observation denied')
        return original(*args, **kwargs)
    monkeypatch.setattr(i3, '_inventory', unavailable)
    with i3.root_observation(data_root=root) as held:
        if failures == 2:
            with pytest.raises(i3.GenesisObservationUnavailable, match='root observation unavailable'):
                held.observe(onboarding._root_snapshot, root, intent)
        else:
            assert held.observe(onboarding._root_snapshot, root, intent) == (None, None)
    assert len(calls) == 2
    assert_control_only(root)


def test_prelock_permission_error_is_provisional(tmp_path, monkeypatch):
    root, request, path, intent = planned(tmp_path)
    original = i3.checked_stat
    calls = []
    def unavailable(path):
        if path == root and not calls:
            calls.append(1)
            raise PermissionError('transient name observation')
        return original(path)
    monkeypatch.setattr(i3, 'checked_stat', unavailable)
    assert run_driver(intent, path)['status'] == 'NATIVE_ACTIVE'
    assert calls == [1]


def test_held_lock_token_rejects_foreign_expired_forged_and_other_thread(tmp_path):
    root, request, path, intent = planned(tmp_path)
    with i3.root_observation(data_root=root) as held:
        def reuse(data_root=root, token=held):
            with i3.root_observation(data_root=data_root, held_lock=token):
                return True
        assert reuse()
        with pytest.raises(SubstrateError):
            reuse(tmp_path / 'foreign')
        with pytest.raises(SubstrateError):
            reuse(token=object())
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pytest.raises(SubstrateError):
                executor.submit(reuse).result(timeout=5)
    with pytest.raises(SubstrateError):
        reuse()
    assert not (tmp_path / 'foreign').exists()


@pytest.mark.skipif(os.name != 'nt', reason='Windows file sharing behavior')
def test_windows_content_reader_blocks_replace_until_closed(tmp_path):
    target, replacement = tmp_path / 'target.json', tmp_path / 'replacement.json'
    target.write_bytes(b'old'); replacement.write_bytes(b'new')
    with target.open('rb'):
        with pytest.raises(PermissionError):
            os.replace(replacement, target)
    os.replace(replacement, target)
    assert target.read_bytes() == b'new'


@pytest.mark.parametrize('name,owned', [
    ('.genesis-operation.json.abc12345.tmp', True),
    ('.genesis-operation.json.abc12345.tmp.extra', False),
    ('.genesis-operation.json.abc1234.tmp', False),
    ('.foreign.json.abc12345.tmp', False),
    ('other/.genesis-operation.json.abc12345.tmp', False),
])
def test_exact_atomic_publication_residue_name(name, owned):
    assert bool(atomic.is_publication_temporary(Path(name), [Path('genesis-operation.json')])) is owned


def test_phase_session_cannot_outlive_reused_lock_acquisition(tmp_path):
    root, request, path, intent = planned(tmp_path)
    with i3.root_observation(data_root=root) as held:
        phase = i3.begin_genesis_administration(data_root=root, intent=intent, held_lock=held)
        session = phase.__enter__()
    before = file_snapshot(root)
    try:
        with pytest.raises(SubstrateError, match='live same-root'):
            session.observe_quiescence(confirmation(), operator_attestation='test offline', issuer_reference='test')
    finally:
        phase.__exit__(None, None, None)
    assert file_snapshot(root) == before


@pytest.mark.parametrize('different_declaration', [False, True])
def test_positive_peer_evidence_requires_the_exact_frozen_intent(tmp_path, different_declaration):
    root, request, path, intent = planned(tmp_path)
    i3.prepare_genesis_inert_root(data_root=root, intent=intent, observer=confirmation(),
        operator_attestation='Explicit offline test confirmation.', issuer_reference='test')
    if different_declaration:
        value = request.payload()
        value['agent']['initial_overlay']['write_threshold'] += .1
        request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    other = onboarding.plan_native_genesis(request)
    assert other != intent
    if not different_declaration:
        assert other.operation_key == intent.operation_key
    other_path = tmp_path / 'other-intent.json'
    from torment_service.external_owner_json import owner_bytes
    other_path.write_bytes(owner_bytes(other.payload()))
    before = file_snapshot(root)
    with pytest.raises(SubstrateError, match='another Genesis intent'):
        run_driver(other, other_path)
    assert file_snapshot(root) == before


def test_matching_record_does_not_hide_unknown_owner_artifact_during_planning(tmp_path):
    root, request, path, intent = planned(tmp_path)
    i3.prepare_genesis_inert_root(data_root=root, intent=intent, observer=confirmation(),
        operator_attestation='Explicit offline test confirmation.', issuer_reference='test')
    artifact = root / 'workspaces' / 'unowned.txt'
    artifact.parent.mkdir()
    artifact.write_bytes(b'unknown owner')
    before = file_snapshot(root)
    output = tmp_path / 'recovered-intent.json'
    with pytest.raises(SubstrateError, match='unknown artifact'):
        onboarding.prepare_intent_plan(request, intent_path=output)
    assert not output.exists() and file_snapshot(root) == before
