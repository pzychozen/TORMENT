"""Additive initial Hive policy ownership; no models or production roots."""
from copy import deepcopy
import io
import json

import pytest

from torment_service import domain_policies as policies, domain_policy_setup as setup
from torment_service.external_owner_json import ExternalOwnerConflict, owner_bytes
from torment_service.substrate import genesis_onboarding as onboarding
from torment_service.substrate.errors import SubstrateError
from test_h2b_native_genesis_v2 import roster_payload
from test_native_genesis_onboarding import run_driver, NoEmbeddingDependency

POSTURE = policies.HIVEMIND_INITIAL_POSTURE
DOMAINS = ['research', 'engineering', 'creative', 'operations', 'meta']


def make_active(tmp_path, domains=DOMAINS):
    root = tmp_path/'root'
    value = roster_payload(root, (False, False))
    value['workspace']['ordered_domains'] = list(domains)
    for agent in value['agents']:
        agent['private_motif_domain_id'] = domains[0]
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    path = tmp_path/'intent.json'
    intent = onboarding.prepare_intent_plan(request, intent_path=path)
    assert run_driver(intent, path, embedder=NoEmbeddingDependency())['status'] == 'NATIVE_ACTIVE'
    return root, dict(data_root=root, workspace_id='workspace', posture=POSTURE, request_path=tmp_path/'policy-request.json')


@pytest.fixture
def active(tmp_path):
    return make_active(tmp_path)


def policy_path(root):
    return root/'workspaces'/'workspace'/'domain_policies.json'


def snapshot(path):
    return path.read_bytes(), path.stat().st_mtime_ns


@pytest.mark.parametrize('domain', list(policies.DEFAULT_DOMAIN_POLICIES))
def test_complete_builtin_policies_change_only_auto_merge(domain):
    before = deepcopy(policies.DEFAULT_DOMAIN_POLICIES)
    raw = policies.resolve_initial_policy(POSTURE, domains=[domain])
    value = json.loads(raw)
    assert raw == owner_bytes(value)
    assert value == {'policies': {domain: {**before[domain], 'auto_merge_motifs': False}}}
    assert len(value['policies'][domain]) == 14
    assert policies.DEFAULT_DOMAIN_POLICIES == before
    assert before['creative']['auto_merge_motifs'] is True and before['personal']['auto_merge_motifs'] is True


def test_policy_keys_canonical_without_reordering_domain_declaration(active, monkeypatch):
    root, kwargs = active
    declaration = root/'workspaces'/'workspace'/'domains.json'
    before = snapshot(declaration)
    request = setup.prepare_policy_setup(**kwargs)
    assert request['contract'] == 'TORMENT_INITIAL_DOMAIN_POLICY_SETUP' and request['version'] == 1
    assert not policy_path(root).exists()
    assert list(json.loads(request['policy_json'])['policies']) == sorted(DOMAINS)
    assert snapshot(declaration) == before
    assert setup.execute_policy_setup(**kwargs)['status'] == 'CREATED_OR_VERIFIED'
    assert setup.execute_policy_setup(**kwargs, verify_only=True)['status'] == 'VERIFIED'
    frozen_request, frozen_policy = snapshot(kwargs['request_path']), snapshot(policy_path(root))
    monkeypatch.setitem(policies.DEFAULT_DOMAIN_POLICIES['creative'], 'auto_propose_min_confidence', 99.0)
    monkeypatch.setitem(policies.DEFAULT_DOMAIN_POLICIES['research'], 'future_setting', True)
    monkeypatch.setattr(policies, 'resolve_initial_policy', lambda *a, **kw: pytest.fail('replay resolved defaults'))
    for _ in range(2):
        assert setup.prepare_policy_setup(**kwargs) == request
        setup.execute_policy_setup(**kwargs)
        setup.execute_policy_setup(**kwargs, verify_only=True)
    assert snapshot(kwargs['request_path']) == frozen_request
    assert snapshot(policy_path(root)) == frozen_policy
    assert snapshot(declaration) == before


@pytest.mark.parametrize('domains', [['custom'], ['research','custom'], ['personal','creative']])
def test_unknown_refuses_before_request_or_policy_and_personal_is_explicit(tmp_path, domains):
    root, kwargs = make_active(tmp_path, domains)
    if 'custom' in domains:
        with pytest.raises(ExternalOwnerConflict, match='known built-in'):
            setup.prepare_policy_setup(**kwargs)
        assert not kwargs['request_path'].exists() and not policy_path(root).exists()
    else:
        setup.prepare_policy_setup(**kwargs)
        setup.execute_policy_setup(**kwargs)
        value = json.loads(policy_path(root).read_bytes())
        assert set(value['policies']) == set(domains)
        assert all(p['auto_merge_motifs'] is False for p in value['policies'].values())


@pytest.mark.parametrize('bad', ['missing-domain','extra-domain','unknown-domain','wrapper','extra-wrapper',
    'missing-field','extra-field','auto-merge','wrong-bool','wrong-int','wrong-float','duplicate','nonfinite','formatting'])
def test_frozen_hive_policy_validation_refuses(bad):
    raw = policies.resolve_initial_policy(POSTURE, domains=DOMAINS)
    value = json.loads(raw)
    policy = value['policies']['creative']
    if bad == 'missing-domain': del value['policies']['research']
    if bad == 'extra-domain': value['policies']['personal'] = dict(policy)
    if bad == 'unknown-domain': value['policies']['custom'] = value['policies'].pop('research')
    if bad == 'wrapper': value = value['policies']
    if bad == 'extra-wrapper': value['extra'] = True
    if bad == 'missing-field': del policy['auto_propose_min_gap_s']
    if bad == 'extra-field': policy['extra'] = True
    if bad == 'auto-merge': policy['auto_merge_motifs'] = True
    if bad == 'wrong-bool': policy['auto_merge_motifs'] = 0
    if bad == 'wrong-int': policy['auto_propose_min_gap_s'] = True
    if bad == 'wrong-float': policy['motif_entropy_high'] = 1
    if bad == 'nonfinite': policy['motif_entropy_high'] = float('nan')
    raw = json.dumps(value).encode() if bad == 'nonfinite' else owner_bytes(value)
    if bad == 'duplicate': raw = raw.replace(b'"auto_merge_motifs": false', b'"auto_merge_motifs": false, "auto_merge_motifs": false')
    if bad == 'formatting': raw += b'\n'
    with pytest.raises(ExternalOwnerConflict): policies.validate_initial_policy(raw, POSTURE, domains=DOMAINS)


@pytest.mark.parametrize('change', ['reorder','remove','add'])
def test_workspace_domains_must_match_active_intent_before_publication(active, change):
    root, kwargs = active
    domains = list(DOMAINS)
    if change == 'reorder': domains.reverse()
    if change == 'remove': domains.pop()
    if change == 'add': domains.append('personal')
    path = root/'workspaces'/'workspace'/'domains.json'
    path.write_bytes(owner_bytes({'domains':domains}))
    before = snapshot(path)
    with pytest.raises((ExternalOwnerConflict, SubstrateError)):
        setup.prepare_policy_setup(**kwargs)
    assert snapshot(path) == before
    assert not kwargs['request_path'].exists() and not policy_path(root).exists()


@pytest.mark.parametrize('change', ['policy','digest','operation-key','installation','posture','domains'])
def test_changed_request_or_conflicting_policy_never_rewrites(active, change):
    root, kwargs = active
    request = setup.prepare_policy_setup(**kwargs)
    setup.execute_policy_setup(**kwargs)
    if change == 'policy':
        value = json.loads(policy_path(root).read_bytes())
        value['policies']['creative']['auto_propose_min_gap_s'] += 1
        policy_path(root).write_bytes(owner_bytes(value))
    else:
        if change == 'digest': request['policy_sha256'] = '0'*64
        if change == 'operation-key': request['operation_key'] += '-changed'
        if change == 'installation': request['genesis_intent_digest'] = '0'*64
        if change == 'posture': request['posture'] = policies.SOLO_PRIVATE_POSTURE
        if change == 'domains':
            value = json.loads(request['policy_json']); del value['policies']['creative']
            request['policy_json'] = owner_bytes(value).decode()
            request['policy_sha256'] = setup._digest(request['policy_json'].encode())
        request['operation_key'] = setup._operation_key(request) if change in ('installation','domains') else request['operation_key']
        kwargs['request_path'].write_bytes(owner_bytes(request))
    before = snapshot(policy_path(root)), snapshot(kwargs['request_path'])
    with pytest.raises(ExternalOwnerConflict): setup.prepare_policy_setup(**kwargs)
    with pytest.raises(ExternalOwnerConflict): setup.execute_policy_setup(**kwargs)
    assert (snapshot(policy_path(root)), snapshot(kwargs['request_path'])) == before


def test_cli_and_version_boundary(active):
    root, kwargs = active
    args = ['--data-root',str(root),'--workspace','workspace','--posture',POSTURE,'--request',str(kwargs['request_path'])]
    for command, status in [('prepare','PREPARED'), ('create','CREATED_OR_VERIFIED'), ('verify','VERIFIED')]:
        output = io.StringIO()
        assert setup.main([command,*args], stdout=output) == 0
        assert json.loads(output.getvalue())['status'] == status
    with pytest.raises(ExternalOwnerConflict, match='Genesis v1'):
        setup.prepare_policy_setup(**{**kwargs,'posture':policies.SOLO_PRIVATE_POSTURE})


def test_explicit_domains_required_and_unknown_posture():
    for domains in (None, [], ['research','research'], ['unknown']):
        with pytest.raises(ExternalOwnerConflict): policies.resolve_initial_policy(POSTURE, domains=domains)
    with pytest.raises(ExternalOwnerConflict): policies.resolve_initial_policy('unknown_v1', domains=DOMAINS)
