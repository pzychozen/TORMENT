"""Initial Solo policy ownership; disposable files and deterministic vectors only."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from torment_service import atomic_publication as atomic
from torment_service import domain_policies as policies
from torment_service import domain_policy_setup as setup
from torment_service.external_owner_json import ExternalOwnerConflict, owner_bytes
from torment_service.workspace_declaration import WorkspaceDeclaration, create_or_verify_workspace_declaration
from torment_service.substrate import genesis_onboarding as onboarding
from torment_service.substrate import genesis_recovery as recovery
from torment_service.substrate.genesis_contracts import GenesisIntent
from torment_service.substrate.errors import SubstrateError
from test_native_genesis_contracts import intent_payload
from test_native_genesis_onboarding import request_payload, run_driver, NoEmbeddingDependency


POSTURE = policies.SOLO_PRIVATE_POSTURE


def snapshot(path):
    return path.read_bytes(), path.stat().st_mtime_ns


@pytest.fixture
def declaration(tmp_path):
    create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=WorkspaceDeclaration(
        'workspace', 0, 3, 'fixture-provider', 'fixture-model', ('personal',)))
    return dict(data_dir=str(tmp_path), workspace_id='workspace', posture=POSTURE,
                expected=policies.resolve_initial_policy(POSTURE))


def policy_path(root):
    return Path(root) / 'workspaces/workspace/domain_policies.json'


def test_posture_resolves_every_personal_field_without_changing_defaults():
    before = deepcopy(policies.DEFAULT_DOMAIN_POLICIES)
    resolved = json.loads(policies.resolve_initial_policy(POSTURE))
    personal = resolved['policies']['personal']
    assert set(resolved) == {'policies'} and set(resolved['policies']) == {'personal'}
    assert len(personal) == 14 and set(personal) == set(before['personal'])
    assert personal == {**before['personal'], 'auto_merge_motifs': False}
    assert policies.DEFAULT_DOMAIN_POLICIES == before
    assert before['personal']['auto_merge_motifs'] is True


def test_create_and_exact_replay_do_not_rewrite(declaration, monkeypatch):
    path = policies.create_or_verify_initial_policy(**declaration)
    assert path.read_bytes() == declaration['expected']
    before = snapshot(path)
    monkeypatch.setattr(atomic, 'publish_if_absent', lambda *a: pytest.fail('replay attempted publication'))
    assert policies.create_or_verify_initial_policy(**declaration) == path
    assert policies.verify_initial_policy(**declaration) == path
    assert snapshot(path) == before


@pytest.mark.parametrize('bad', ['value', 'partial', 'wrapper', 'extra-domain', 'extra-field',
    'malformed', 'duplicate', 'nonfinite', 'formatting', 'wrong-type', 'auto-merge'])
def test_existing_conflicts_refuse_without_rewrite(declaration, bad):
    path = policy_path(declaration['data_dir'])
    value = json.loads(declaration['expected'])
    personal = value['policies']['personal']
    if bad == 'value': personal['auto_propose_max_per_window'] += 1
    if bad == 'partial': value['policies']['personal'] = {'auto_merge_motifs': False}
    if bad == 'wrapper': value = value['policies']
    if bad == 'extra-domain': value['policies']['other'] = dict(personal)
    if bad == 'extra-field': personal['unknown'] = True
    if bad == 'nonfinite': personal['motif_entropy_high'] = float('nan')
    if bad == 'wrong-type': personal['shared_min_distinct_agents'] = True
    if bad == 'auto-merge': personal['auto_merge_motifs'] = True
    raw = owner_bytes(value) if bad != 'nonfinite' else json.dumps(value).encode()
    if bad == 'malformed': raw = b'{'
    if bad == 'duplicate': raw = raw.replace(b'"auto_merge_motifs": false', b'"auto_merge_motifs": false, "auto_merge_motifs": false')
    if bad == 'formatting': raw += b'\n'
    path.write_bytes(raw)
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict): policies.create_or_verify_initial_policy(**declaration)
    with pytest.raises(ExternalOwnerConflict): policies.verify_initial_policy(**declaration)
    assert snapshot(path) == before


@pytest.mark.parametrize('domains', [['research'], ['personal', 'research'], []])
def test_undeclared_or_additional_domains_refuse(declaration, domains):
    path = policy_path(declaration['data_dir'])
    path.with_name('domains.json').write_bytes(owner_bytes({'domains': domains}))
    with pytest.raises(ExternalOwnerConflict): policies.create_or_verify_initial_policy(**declaration)
    assert not path.exists()


@pytest.mark.parametrize('name', ['domains.json', 'workspace_meta.json'])
def test_missing_declaration_is_not_created(declaration, name):
    path = policy_path(declaration['data_dir'])
    path.with_name(name).unlink()
    with pytest.raises(ExternalOwnerConflict): policies.create_or_verify_initial_policy(**declaration)
    assert not path.exists() and not path.with_name(name).exists()


@pytest.mark.parametrize('workspace', ['../escape', 'other', 'Workspace'])
def test_wrong_workspace_and_alias_refuse(declaration, workspace):
    with pytest.raises(ValueError):
        policies.create_or_verify_initial_policy(**{**declaration, 'workspace_id': workspace})
    assert not policy_path(declaration['data_dir']).exists()


@pytest.mark.parametrize('stage', ['before-publication', 'after-publication'])
def test_interrupted_publication_is_absent_or_complete(declaration, monkeypatch, stage):
    def interrupted(*args): raise OSError('synthetic interruption')
    with monkeypatch.context() as patch:
        patch.setattr(atomic.os, 'link', interrupted) if stage == 'before-publication' else patch.setattr(atomic, '_sync_publication', interrupted)
        with pytest.raises(OSError): policies.create_or_verify_initial_policy(**declaration)
    path = policy_path(declaration['data_dir'])
    assert path.exists() == (stage == 'after-publication')
    if path.exists(): assert path.read_bytes() == declaration['expected']
    assert not list(path.parent.glob('*.tmp'))
    policies.create_or_verify_initial_policy(**declaration)
    assert path.read_bytes() == declaration['expected']


def test_concurrent_conflicting_publication_never_overwrites(declaration, monkeypatch):
    path = policy_path(declaration['data_dir'])
    original = atomic.publish_if_absent
    other = json.loads(declaration['expected'])
    other['policies']['personal']['shared_min_distinct_agents'] = 2
    conflicting = owner_bytes(other)
    def compete(target, raw):
        original(target, conflicting)
        return original(target, raw)
    monkeypatch.setattr(atomic, 'publish_if_absent', compete)
    with pytest.raises(ExternalOwnerConflict): policies.create_or_verify_initial_policy(**declaration)
    assert path.read_bytes() == conflicting


@pytest.fixture
def active(tmp_path):
    root = tmp_path / 'root'
    value = request_payload(root)
    value['workspace']['ordered_domains'] = ['personal']
    value['agent']['private_motif_domain_id'] = 'personal'
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    intent_path = tmp_path / 'intent.json'
    intent = onboarding.prepare_intent_plan(request, intent_path=intent_path)
    assert run_driver(intent, intent_path, embedder=NoEmbeddingDependency())['status'] == 'NATIVE_ACTIVE'
    return root, intent, intent_path, dict(data_root=root, workspace_id='workspace', posture=POSTURE,
        request_path=tmp_path / 'initial-policy.json')


def test_explicit_prepare_create_verify_and_replay_freeze_defaults(active, monkeypatch):
    root, intent, _, kwargs = active
    request = setup.prepare_policy_setup(**kwargs)
    assert not policy_path(root).exists(), 'prepare must not publish policy'
    frozen = snapshot(kwargs['request_path'])
    assert request['genesis_intent_digest'] == intent.digest
    assert request['operation_key'] == setup._operation_key(request)
    # Both value and shape changes to future defaults must not replan replay.
    monkeypatch.setitem(policies.DEFAULT_DOMAIN_POLICIES['personal'], 'shared_min_distinct_agents', 99)
    monkeypatch.setitem(policies.DEFAULT_DOMAIN_POLICIES['personal'], 'future_setting', True)
    monkeypatch.setattr(policies, 'resolve_initial_policy', lambda *a: pytest.fail('replay resolved defaults'))
    assert setup.prepare_policy_setup(**kwargs) == request
    assert setup.execute_policy_setup(**kwargs)['status'] == 'CREATED_OR_VERIFIED'
    before = snapshot(policy_path(root))
    assert policy_path(root).read_bytes() == request['policy_json'].encode()
    assert setup.execute_policy_setup(**kwargs, verify_only=True)['status'] == 'VERIFIED'
    assert setup.execute_policy_setup(**kwargs)['operation_key'] == request['operation_key']
    assert snapshot(policy_path(root)) == before and snapshot(kwargs['request_path']) == frozen


@pytest.mark.parametrize('field,value', [('workspace_id', 'wrong'), ('posture', 'unknown_v1'), ('data_root', 'relative-root')])
def test_explicit_declaration_conflicts_refuse(active, field, value):
    root, _, _, kwargs = active
    setup.prepare_policy_setup(**kwargs)
    with pytest.raises((ExternalOwnerConflict, SubstrateError)):
        setup.execute_policy_setup(**{**kwargs, field: value})
    assert not policy_path(root).exists()


@pytest.mark.parametrize('bad', ['identity', 'digest', 'operation-key', 'partial', 'malformed', 'extra-domain'])
def test_frozen_request_conflicts_refuse(active, bad):
    root, _, _, kwargs = active
    request = setup.prepare_policy_setup(**kwargs)
    if bad == 'identity': request['genesis_intent_digest'] = '0' * 64
    if bad == 'digest': request['policy_sha256'] = '0' * 64
    if bad == 'operation-key': request['operation_key'] += '-different'
    if bad == 'partial': request['policy_json'] = '{"policies":{"personal":{"auto_merge_motifs":false}}}'
    if bad == 'extra-domain':
        value = json.loads(request['policy_json']); value['policies']['other'] = {}
        request['policy_json'] = json.dumps(value)
    if bad in ('identity', 'partial', 'extra-domain'):
        request['policy_sha256'] = setup._digest(request['policy_json'].encode())
        request['operation_key'] = setup._operation_key(request)
    kwargs['request_path'].write_bytes(b'{' if bad == 'malformed' else owner_bytes(request))
    before = snapshot(kwargs['request_path'])
    with pytest.raises(ValueError): setup.execute_policy_setup(**kwargs)
    assert not policy_path(root).exists() and snapshot(kwargs['request_path']) == before


def test_request_cannot_be_inside_root_and_verify_does_not_create(active):
    root, _, _, kwargs = active
    with pytest.raises(onboarding.NativeGenesisOnboardingRefused, match='outside the data root'):
        setup.prepare_policy_setup(**{**kwargs, 'request_path': root / 'request.json'})
    assert not (root / 'request.json').exists()
    setup.prepare_policy_setup(**kwargs)
    with pytest.raises(ExternalOwnerConflict): setup.execute_policy_setup(**kwargs, verify_only=True)
    assert not policy_path(root).exists()


@pytest.mark.parametrize('kind', ['absent', 'legacy', 'incomplete'])
def test_nonactive_roots_refuse_without_policy_or_request(tmp_path, kind):
    root = tmp_path / 'root'
    if kind == 'legacy':
        root.mkdir(); (root / 'legacy.txt').write_text('existing')
    if kind == 'incomplete':
        value = request_payload(root)
        request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
        intent = onboarding.prepare_intent_plan(request, intent_path=tmp_path / 'intent.json')
        def stop(stage):
            if stage == 'after-i3': raise RuntimeError('synthetic stop')
        with pytest.raises(RuntimeError): run_driver(intent, tmp_path / 'intent.json', embedder=NoEmbeddingDependency(), fault=stop)
    target = tmp_path / 'policy-request.json'
    with pytest.raises(SubstrateError):
        setup.prepare_policy_setup(data_root=root, workspace_id='workspace', posture=POSTURE, request_path=target)
    assert not target.exists() and not policy_path(root).exists()


def test_genesis_recovery_has_no_policy_opinion_or_repair(active, monkeypatch):
    root, intent, intent_path, kwargs = active
    original = recovery.recover_active_native_genesis(data_root=root)
    assert not policy_path(root).exists()
    setup.prepare_policy_setup(**kwargs); setup.execute_policy_setup(**kwargs)
    for raw in (policy_path(root).read_bytes(), owner_bytes({'policies': {'personal': {'auto_merge_motifs': True}}}), b'{'):
        policy_path(root).write_bytes(raw)
        before = snapshot(policy_path(root))
        original_read = Path.read_bytes
        def read(path):
            if path == policy_path(root): pytest.fail('Genesis inspected policy')
            return original_read(path)
        with monkeypatch.context() as patch:
            patch.setattr(Path, 'read_bytes', read)
            assert recovery.recover_active_native_genesis(data_root=root) == original
            assert run_driver(intent, intent_path, embedder=NoEmbeddingDependency())['status'] == 'NATIVE_ACTIVE'
        assert snapshot(policy_path(root)) == before
    # Explicit initial replay refuses the changed current file; ordinary
    # recovery above never restores it. Future mutation stays a separate lane.
    with pytest.raises(ExternalOwnerConflict): setup.execute_policy_setup(**kwargs)


def test_genesis_v1_intent_fixture_digest_is_unchanged():
    assert GenesisIntent.from_payload(intent_payload()).digest == 'e549bc3efa86785eb49b952cc0f82bd581246f3a63f23cd3c000656e5e4cbf31'


def test_real_native_view_policy_guard_and_executor_boundary(active, monkeypatch):
    from torment_service.fabric import TormentFabric
    from torment_service.public_runtime import NativePublicTormentRuntime, NativePublicOperationRefused
    from torment_service.substrate.deployment_selector import resolve_deployment_agreement
    from torment_service.substrate.production_native_owner import NativeProductionResourceOwner
    root, _, _, kwargs = active
    authority = recovery.recover_active_native_genesis(data_root=root)
    profile = authority.completion.qualified_deployment_profile
    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    owner = NativeProductionResourceOwner.from_native_agreement(data_root=root, agreement=agreement,
        effective_profile=profile, admission_descriptor_path=None)
    # Real admitted native owner, workspace reader, and public preflight. Only
    # the executor is stopped before cognition; no model or fake policy loader.
    class NoCognitionFabric(TormentFabric):
        def __init__(self):
            self.data_dir = str(root)
            self.kernel = SimpleNamespace(embedder=NoEmbeddingDependency())
            self._legacy_materialization_fence = None
    calls = []
    try:
        runtime = NativePublicTormentRuntime(cognition_fabric=NoCognitionFabric(), native_owner=owner)
        monkeypatch.setattr(runtime._executor, 'execute', lambda request: calls.append(request) or {'reached': True})
        with pytest.raises(NativePublicOperationRefused, match='unqualified auto-merge'):
            runtime.ingest('workspace', 'agent', 'memory', public_mutation_key='write-1')
        assert not calls
        setup.prepare_policy_setup(**kwargs); setup.execute_policy_setup(**kwargs)
        # Setup precedes service startup; construct its fresh workspace view.
        runtime = NativePublicTormentRuntime(cognition_fabric=NoCognitionFabric(), native_owner=owner)
        monkeypatch.setattr(runtime._executor, 'execute', lambda request: calls.append(request) or {'reached': True})
        assert runtime.ingest('workspace', 'agent', 'memory', public_mutation_key='write-1') == {'reached': True}
        assert len(calls) == 1 and calls[0].domain_id == 'personal'
    finally:
        owner.close()


def test_cli_subprocess_sequence_and_refusal_exit_code(active):
    root, _, _, kwargs = active
    base = [sys.executable, '-B', '-m', 'torment_service.domain_policy_setup']
    args = ['--data-root', str(root), '--workspace', 'workspace', '--posture', POSTURE,
            '--request', str(kwargs['request_path'])]
    for command, status in [('prepare', 'PREPARED'), ('create', 'CREATED_OR_VERIFIED'), ('verify', 'VERIFIED')]:
        proc = subprocess.run(base + [command] + args, capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert json.loads(proc.stdout)['status'] == status
    before = snapshot(policy_path(root))
    proc = subprocess.run(base + ['create'] + args[:-5] + ['wrong'] + args[-4:], capture_output=True, text=True)
    assert proc.returncode != 0
    assert snapshot(policy_path(root)) == before
