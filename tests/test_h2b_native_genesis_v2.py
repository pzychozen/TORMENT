"""Fresh roster v2 qualification; deterministic vectors and disposable roots."""
from copy import deepcopy
import json

import pytest

from torment_service.substrate import genesis_contracts as g
from torment_service.substrate import genesis_onboarding as onboarding
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_recovery as recovery
from torment_service.substrate.deployment_types import NativeGenesisCompletionWitness, completion_witness_from_payload
from test_native_genesis_onboarding import request_payload, run_driver, DeterministicTestEmbedder, NoEmbeddingDependency
from test_native_genesis_completion import file_snapshot
from torment_service.substrate.errors import SubstrateError
from torment_service.substrate import genesis_administration as i3
from test_native_genesis_administration import child


def roster_payload(root, modes=(True, False, True)):
    result = request_payload(root, False)
    result['version'] = 2
    result.pop('agent')
    result.pop('character')
    agents = []
    for index, enabled in enumerate(modes):
        singular = request_payload(root, enabled)
        agent, character = singular['agent'], singular['character']
        agent['agent_id'] = f'agent-{index}'
        agent['private_motif_domain_id'] = result['workspace']['ordered_domains'][index % 2]
        if enabled:
            character['definition']['owner_agent_id'] = agent['agent_id']
            character['definition']['seed_id'] = f'seed-{index}'
            agent['identity_seed']['seed_id'] = f'seed-{index}'
        agents.append(dict(**agent, character=character))
    result['agents'] = agents
    return result


def planned_roster(tmp_path, modes=(True, False, True)):
    root, path = tmp_path/'root', tmp_path/'intent.json'
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(roster_payload(root, modes))
    intent = onboarding.prepare_intent_plan(request, intent_path=path)
    return root, request, path, intent


@pytest.mark.parametrize('modes', [(False, False), (True, False, True), (True, True, True, True, True)])
def test_fresh_rosters_and_cold_replay(tmp_path, modes):
    root, request, path, intent = planned_roster(tmp_path, modes)
    dependency = DeterministicTestEmbedder()
    result = run_driver(intent, path, embedder=dependency)
    assert result['agent_ids'] == [a['agent_id'] for a in request.payload()['agents']]
    assert result['selector_generation'] == 2
    assert len(dependency.calls) == sum(modes)*3
    authority = recovery.recover_active_native_genesis(data_root=root)
    completion = authority.completion
    assert completion.VERSION == 2 and completion.expanded_intent == intent
    assert 'character_seed_completion' not in completion.payload()
    assert len(completion.character_seed_completions) == len(modes)
    assert completion_witness_from_payload(completion.payload()) == completion
    assert NativeGenesisCompletionWitness.from_payload(completion.payload()) == completion
    assert len(completion.initial_memberships) == len(modes)+2
    assert all(m.payload()['relationship_revision_ordinal'] == 1 for m in completion.initial_memberships)
    runtime = recovery.recover_active_native_genesis(data_root=root, workspace_id='workspace')
    assert len(runtime.scopes) == len(modes)+2
    for index, enabled in enumerate(modes):
        agent_id = f'agent-{index}'
        assert runtime.lookup_private(agent_id).memory_runtime_scope.agent_id == agent_id
        entry = completion.character_seed_completions[index].payload()
        assert entry['agent_id'] == agent_id
        assert entry['seed_id'] == (f'seed-{index}' if enabled else None)
        assert entry['completion']['mode'] == ('ENABLED' if enabled else 'DISABLED')
        if enabled:
            seed = json.loads((root/'workspaces'/'workspace'/'seeds'/f'seed-{index}'/'seed.json').read_bytes())
            assert seed['owner_agent_id'] == agent_id
            assert seed['seed_eids'] == entry['completion']['seed_eids']
            assert seed['seed_motif_id'] == entry['completion']['seed_motif_id']
        else:
            assert not (root/'workspaces'/'workspace'/'seeds'/f'seed-{index}').exists()
    before = file_snapshot(root)
    assert onboarding.onboarding_needs_embedding(intent) is False
    assert run_driver(intent, path, embedder=NoEmbeddingDependency()) == result
    assert file_snapshot(root) == before


def test_canonical_roster_planning_and_explicit_version_dispatch(tmp_path):
    from uuid import UUID
    def plan(request):
        ids = iter(range(1, 100))
        return onboarding.plan_native_genesis(request, id_factory=lambda: UUID(int=next(ids), version=4), time_factory=lambda: 1234)
    source = roster_payload(tmp_path/'root')
    first = onboarding.NativeGenesisOnboardingRequest.from_payload(source)
    source['agents'].reverse()
    second = onboarding.NativeGenesisOnboardingRequest.from_payload(source)
    assert first == second and first.digest == second.digest
    intent = plan(first)
    assert intent == plan(second)
    assert intent.VERSION == 2 and g.GenesisIntent.from_payload(intent.payload()) == intent
    assert onboarding.request_from_intent(intent) == first
    assert [p.canonical_key for p in intent.runtime_plans] == sorted(p.canonical_key for p in intent.runtime_plans)
    assert len({p.canonical_key for p in intent.runtime_plans}) == 5
    # Domain order is an existing ordered declaration, not a set to normalize.
    assert intent.payload()['workspace']['ordered_domains'] == ['zeta', 'alpha']
    changed = intent.payload()
    changed['agents'].reverse()
    with pytest.raises(SubstrateError): g.GenesisIntent.from_payload(changed)
    for value in (first.payload(), intent.payload()):
        value['version'] = 1
        decoder = onboarding.NativeGenesisOnboardingRequest if 'allocations' not in value else g.GenesisIntent
        with pytest.raises(SubstrateError): decoder.from_payload(value)
    v1 = onboarding.NativeGenesisOnboardingRequest.from_payload(request_payload(tmp_path/'single', True))
    assert type(v1) is onboarding.NativeGenesisOnboardingRequest
    assert type(plan(v1)) is g.GenesisIntent
    assert 'agents' not in v1.payload()
    malformed = json.dumps(first.payload()).replace('"version": 2', '"version": 2, "version": 2', 1)
    with pytest.raises(SubstrateError): onboarding.NativeGenesisOnboardingRequestV2(malformed)


@pytest.mark.parametrize('bad', ['empty', 'duplicate', 'case-alias', 'unicode-alias', 'malformed', 'agent-path',
    'owner-mismatch', 'shared-seed', 'case-seed', 'undeclared-domain', 'duplicate-domains', 'missing-overlay',
    'disabled-seed', 'seed-mismatch', 'agent-embedding', 'lane-mismatch', 'nonfinite', 'boolean-version',
    'runtime-flag', 'interaction-mode', 'provider', 'slider'])
def test_invalid_v2_declarations_refuse_before_root_creation(tmp_path, bad):
    value = roster_payload(tmp_path/'root')
    agents = value['agents']
    if bad == 'empty': value['agents'] = []
    elif bad == 'duplicate': agents.append(deepcopy(agents[0]))
    elif bad == 'case-alias': agents[1]['agent_id'] = agents[0]['agent_id'].upper()
    elif bad == 'unicode-alias': agents[0]['agent_id'], agents[1]['agent_id'] = 'caf\u00e9', 'cafe\u0301'
    elif bad == 'malformed': agents[1] = None
    elif bad == 'agent-path': agents[1]['agent_id'] = '../agent'
    elif bad == 'owner-mismatch': agents[2]['character']['definition']['owner_agent_id'] = agents[0]['agent_id']
    elif bad in ('shared-seed', 'case-seed'):
        seed = agents[0]['identity_seed']['seed_id']
        if bad == 'case-seed': seed = seed.upper()
        agents[2]['identity_seed']['seed_id'] = agents[2]['character']['definition']['seed_id'] = seed
    elif bad == 'undeclared-domain': agents[0]['private_motif_domain_id'] = 'foreign'
    elif bad == 'duplicate-domains': value['workspace']['ordered_domains'] *= 2
    elif bad == 'missing-overlay': agents[1]['initial_overlay'].pop('write_threshold')
    elif bad == 'disabled-seed': agents[1]['identity_seed']['seed_id'] = 'foreign-seed'
    elif bad == 'seed-mismatch': agents[2]['identity_seed']['seed_text'] += ' Changed.'
    elif bad == 'agent-embedding': agents[2]['representation_lane'] = value['representation_lane']
    elif bad == 'lane-mismatch': value['profile_choice']['representation_dimension'] += 1
    elif bad == 'nonfinite': agents[0]['initial_overlay']['write_threshold'] = float('nan')
    elif bad == 'boolean-version': value['version'] = True
    elif bad == 'runtime-flag': value['TORMENT_HIVEMIND_ENABLE'] = True
    else: agents[0][bad] = 'not-genesis-identity'
    with pytest.raises((SubstrateError, ValueError)):
        onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    assert not (tmp_path/'root').exists()


def test_active_v2_conflicts_cannot_mutate_roster_or_allocations(tmp_path):
    from uuid import UUID
    root, request, path, intent = planned_roster(tmp_path)
    run_driver(intent, path, embedder=DeterministicTestEmbedder())
    before = file_snapshot(root), path.read_bytes()
    for conflict in ('add-agent', 'remove-agent', 'agent-id', 'seed', 'character-mode', 'domain'):
        value = request.payload()
        if conflict == 'add-agent':
            extra = deepcopy(value['agents'][1]); extra['agent_id'] = 'agent-extra'; value['agents'].append(extra)
        elif conflict == 'remove-agent': value['agents'].pop()
        elif conflict == 'agent-id': value['agents'][1]['agent_id'] = 'different-agent'
        elif conflict == 'seed':
            value['agents'][2]['character']['definition']['seed_text'] += ' Changed.'
            value['agents'][2]['identity_seed']['seed_text'] += ' Changed.'
        elif conflict == 'character-mode':
            disabled = deepcopy(value['agents'][1]); disabled['agent_id'] = 'agent-2'; value['agents'][2] = disabled
        else: value['workspace']['ordered_domains'].append('new-domain')
        changed = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
        with pytest.raises(SubstrateError):
            onboarding.prepare_intent_plan(changed, intent_path=tmp_path/'conflicting.json')
        assert not (tmp_path/'conflicting.json').exists()
    value = intent.payload()
    value['allocations']['core_id'] = str(UUID(int=8888, version=4))
    conflicting = g.GenesisIntent.from_payload(value)
    other = tmp_path/'conflicting-allocation.json'
    other.write_text(json.dumps(conflicting.payload()), encoding='utf-8')
    with pytest.raises(SubstrateError): run_driver(conflicting, other, embedder=NoEmbeddingDependency())
    assert (file_snapshot(root), path.read_bytes()) == before


DEATH_PROCESS = r'''
import sys, os, json
from pathlib import Path
from test_h2b_native_genesis_v2 import onboarding, run_driver, DeterministicTestEmbedder
from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime
path, stage, log = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
class Audited(DeterministicTestEmbedder):
    def embed(self, text):
        with log.open('a', encoding='utf-8') as out: out.write(json.dumps(text)+'\n')
        return super().embed(text)
if stage == 'during-first-agent':
    original = NativeCharacterSeedPlantRuntime._publish_representation
    def publish(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        os._exit(71)
    NativeCharacterSeedPlantRuntime._publish_representation = publish
native_plants = 0
def fault(point):
    global native_plants
    if point == 'after-native-seed-plant': native_plants += 1
    if point == stage or (stage == 'after-last-native-seed' and point == 'after-native-seed-plant' and native_plants == 3):
        os._exit(71)
run_driver(onboarding.read_intent_plan(path), path, embedder=Audited(), fault=fault)
raise AssertionError('requested death boundary not reached')
'''


@pytest.mark.parametrize('stage,completed', [
    ('before-initial-agent:0', 0), ('during-first-agent', 0), ('after-initial-agent:0', 1),
    ('before-initial-agent:1', 1), ('after-initial-agent:1', 2), ('after-initial-agent:2', 3),
    ('after-last-native-seed', 3),
    ('after-i4', 3), ('after-membership-commit:0', 3), ('after-i5', 3), ('after-i6', 3),
])
def test_real_process_death_resumes_each_agent_once(tmp_path, stage, completed, monkeypatch):
    from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime
    root, request, path, intent = planned_roster(tmp_path, (True, True, True))
    log = tmp_path/'embedding.jsonl'
    process = child(DEATH_PROCESS, path, stage, log)
    stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 71 and not stdout and not stderr, (stdout, stderr)
    planted = []
    original = NativeCharacterSeedPlantRuntime.plant_seed
    def plant(self, request):
        planted.append(request.seed.owner_agent_id)
        return original(self, request)
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, 'plant_seed', plant)
    dependency = DeterministicTestEmbedder()
    assert onboarding.onboarding_needs_embedding(intent) is (completed < 3)
    result = run_driver(intent, path, embedder=dependency if completed < 3 else NoEmbeddingDependency())
    assert result['status'] == 'NATIVE_ACTIVE'
    assert planted == [f'agent-{index}' for index in range(completed, 3)]
    initial = len(log.read_text(encoding='utf-8').splitlines()) if log.exists() else 0
    assert initial + len(dependency.calls) == 9
    authority = recovery.recover_active_native_genesis(data_root=root)
    assert len(authority.completion.initial_memberships) == 5
    assert len(list((root/'workspaces'/'workspace'/'agents').glob('*/identity.json'))) == 3
    assert len(list((root/'workspaces'/'workspace'/'seeds').glob('*/seed.json'))) == 3
    before = file_snapshot(root)
    assert run_driver(intent, path, embedder=NoEmbeddingDependency()) == result
    assert file_snapshot(root) == before


CONCURRENT_PROCESS = r'''
import sys, time, json
from pathlib import Path
from test_h2b_native_genesis_v2 import onboarding, run_driver, DeterministicTestEmbedder
from torment_service.substrate.errors import SubstrateError
path, ready, release, attempted = map(Path, sys.argv[1:5])
role = sys.argv[5]
def fault(point):
    if role == 'leader' and point == 'before-initial-agent:1':
        ready.write_text('held existing root observation lock')
        deadline = time.monotonic()+45
        while not release.exists():
            if time.monotonic()>deadline: raise AssertionError('peer gate timeout')
            time.sleep(.01)
if role == 'follower': attempted.write_text('entering existing coherent observation')
try:
    result = run_driver(onboarding.read_intent_plan(path), path, embedder=DeterministicTestEmbedder(), fault=fault)
except SubstrateError:
    print(json.dumps(dict(status='CONFLICT')), flush=True)
    sys.exit(2)
print(json.dumps(result), flush=True)
'''


@pytest.mark.parametrize('conflicting', [False, True])
def test_matching_and_conflicting_real_concurrent_v2_callers(tmp_path, conflicting):
    from test_native_genesis_concurrency import wait_file
    from torment_service.external_owner_json import owner_bytes
    root, request, path, intent = planned_roster(tmp_path, (True, True))
    follower_path = path
    if conflicting:
        value = request.payload()
        value['agents'][1]['identity_seed']['seed_text'] += ' Different.'
        value['agents'][1]['character']['definition']['seed_text'] += ' Different.'
        changed = onboarding.plan_native_genesis(onboarding.NativeGenesisOnboardingRequest.from_payload(value))
        follower_path = tmp_path/'other-intent.json'
        follower_path.write_bytes(owner_bytes(changed.payload()))
    ready, release, attempted = (tmp_path/name for name in ('ready', 'release', 'attempted'))
    first = child(CONCURRENT_PROCESS, path, ready, release, attempted, 'leader')
    second = None
    try:
        wait_file(ready, [first])
        second = child(CONCURRENT_PROCESS, follower_path, ready, release, attempted, 'follower')
        wait_file(attempted, [first, second])
        assert second.poll() is None
    finally:
        release.write_text('release existing lock')
        out1, err1 = first.communicate(timeout=60)
        if second is not None: out2, err2 = second.communicate(timeout=60)
    assert first.returncode == 0 and not err1, (out1, err1)
    assert second is not None and not err2
    result = json.loads(out1)
    assert second.returncode == (2 if conflicting else 0)
    assert json.loads(out2) == (dict(status='CONFLICT') if conflicting else result)
    authority = recovery.recover_active_native_genesis(data_root=root)
    assert authority.completion.expanded_intent == intent
    assert len(list((root/'substrate'/'cores').glob('*.db'))) == 1
    assert authority.selector_state.generation == 2
    assert run_driver(intent, path, embedder=NoEmbeddingDependency()) == result


def test_cli_v2_lazy_embedding_and_completed_replay(tmp_path):
    from test_native_genesis_cli import arguments, call, forbidden_factory
    from torment_service.external_owner_json import owner_bytes
    root, request, path = tmp_path/'root', tmp_path/'request.json', tmp_path/'intent.json'
    request.write_bytes(owner_bytes(roster_payload(root)))
    calls = []
    dependency = DeterministicTestEmbedder()
    def factory():
        calls.append(1)
        return dependency
    args = arguments(request, path, profile=tmp_path/'profile.json')
    code, result = call(args, embedder_factory=factory)
    assert code == 0 and calls == [1] and len(dependency.calls) == 6
    before = file_snapshot(root)
    assert call(args, embedder_factory=forbidden_factory) == (code, result)
    assert call(arguments(request, path, command='apply'), embedder_factory=forbidden_factory) == (code, result)
    assert file_snapshot(root) == before


@pytest.mark.parametrize('conflict', ['membership-extra', 'membership-missing', 'membership-witness',
    'membership-revision', 'membership-retired', 'completion-core', 'completion-profile', 'completion-runtime-allocation',
    'external-identity', 'character-linkage', 'character-definition', 'representation'])
def test_v2_exact_initial_authority_tampering_refuses_without_repair(tmp_path, conflict):
    from test_native_genesis_recovery import corrupt_fixture
    root, request, path, intent = planned_roster(tmp_path)
    run_driver(intent, path, embedder=DeterministicTestEmbedder())
    completion = recovery.recover_active_native_genesis(data_root=root).completion
    corrupt_fixture(root, intent, completion, conflict)
    before = file_snapshot(root)
    with pytest.raises(SubstrateError): recovery.recover_active_native_genesis(data_root=root)
    assert file_snapshot(root) == before


@pytest.mark.parametrize('conflict', ['agent-id', 'seed-id', 'disabled-mode', 'source-digest', 'result-digest',
    'linkage', 'order', 'missing', 'intent', 'membership-digest'])
def test_tampered_per_agent_completion_refuses_even_with_rehashed_outer_receipt(tmp_path, conflict):
    from test_native_genesis_recovery import change_completion
    root, request, path, intent = planned_roster(tmp_path)
    run_driver(intent, path, embedder=DeterministicTestEmbedder())
    completion = recovery.recover_active_native_genesis(data_root=root).completion
    def mutate(value):
        entries = value['character_seed_completions']
        if conflict == 'agent-id': entries[0]['agent_id'] = 'agent-2'
        elif conflict == 'seed-id': entries[0]['seed_id'] = 'seed-2'
        elif conflict == 'disabled-mode': entries[1]['completion'] = entries[0]['completion']
        elif conflict == 'source-digest': entries[2]['completion']['source_intent_digest'] = '0'*64
        elif conflict == 'result-digest': entries[2]['completion']['result_digest'] = '0'*64
        elif conflict == 'linkage': entries[2]['completion']['seed_eids'] = [999]
        elif conflict == 'order': entries.reverse()
        elif conflict == 'missing': entries.pop()
        elif conflict == 'intent': value['expanded_intent']['agents'][1]['initial_overlay']['write_threshold'] += .1
        else: value['initial_membership_closure_digest'] = '0'*64
        return value
    change_completion(root, completion, mutate)
    before = file_snapshot(root)
    with pytest.raises(SubstrateError): recovery.recover_active_native_genesis(data_root=root)
    assert file_snapshot(root) == before


@pytest.mark.parametrize('transition', ['revision', 'retirement', 'different-issuer'])
def test_later_service_lineage_remains_outside_exact_genesis_closure(tmp_path, transition):
    from dataclasses import replace
    from uuid import UUID
    from torment_service.substrate import genesis_membership_administration as i5
    from torment_service.substrate.connection import open_existing_native_core_connection
    from torment_service.substrate.root_scope_membership import RootScopeMembershipService
    from torment_service.substrate.relationships import NativeRelationshipService
    root, request, path, intent = planned_roster(tmp_path, (False, False))
    run_driver(intent, path)
    authority = recovery.recover_active_native_genesis(data_root=root)
    with open_existing_native_core_connection(authority.core_database_path) as opened:
        c = opened.connection
        profile = i5._recover_profile(c, intent)
        service = RootScopeMembershipService(c)
        original = service.recover(profile)[0]
        plan = next(p.payload() for p in intent.runtime_plans
                    if p.payload()['scope_plan']['target_semantic_scope_id'] == str(original.semantic_scope_id))
        namespace = UUID(plan['scope_plan']['idempotency_namespace_id'])
        before = c.execute('SELECT * FROM relationship_revisions WHERE relationship_revision_id=?',
                           (original.relationship_revision_id.bytes,)).fetchone()
        if transition == 'retirement':
            service.retire(profile=profile, relationship_id=original.relationship_id,
                expected_relationship_revision_id=original.relationship_revision_id,
                idempotency_namespace_id=namespace, idempotency_key='disposable-later-retirement')
        else:
            witness = original.witness if transition == 'revision' else replace(original.witness, issuer_reference='other-issuer')
            state = service._relationship_state(profile=profile, runtime_scope=i5._runtime_scope(plan), witness=witness,
                membership_identity_namespace_id=original.membership_identity_namespace_id, lifecycle_state='ACTIVE')
            NativeRelationshipService(c).transition_relationship(idempotency_namespace_id=namespace,
                idempotency_key='disposable-later-revision', relationship_id=original.relationship_id,
                expected_revision_id=original.relationship_revision_id, state=state)
        assert c.execute('SELECT * FROM relationship_revisions WHERE relationship_revision_id=?',
                         (original.relationship_revision_id.bytes,)).fetchone() == before
        assert next(r for r in service.recover(profile) if r.relationship_id == original.relationship_id).relationship_revision_ordinal == 2
    assert recovery.verify_active_native_genesis(data_root=root).completion == authority.completion
    before = file_snapshot(root)
    with pytest.raises(SubstrateError): recovery.recover_active_native_genesis(data_root=root)
    assert file_snapshot(root) == before


def test_v2_staging_only_plant_and_readonly_cold_owner_recovery(tmp_path, monkeypatch):
    from test_native_genesis_recovery import readonly_recovery_guard, owner_for
    from test_native_genesis_onboarding import confirmation
    from torment_service.substrate.native_character_seed_plant import NativeCharacterSeedPlantRuntime
    root, request, path, intent = planned_roster(tmp_path)
    planted = []
    original = NativeCharacterSeedPlantRuntime.plant_seed
    def plant(self, request):
        assert self._connection.execute('SELECT core_role FROM core_metadata').fetchone() == ('STAGING',)
        assert request.seed.owner_agent_id == self._config.agent_id
        planted.append(request.seed.owner_agent_id)
        return original(self, request)
    monkeypatch.setattr(NativeCharacterSeedPlantRuntime, 'plant_seed', plant)
    run_driver(intent, path, embedder=DeterministicTestEmbedder())
    assert planted == ['agent-0', 'agent-2']
    before = file_snapshot(root)
    with readonly_recovery_guard(monkeypatch):
        authority = recovery.recover_active_native_genesis(data_root=root)
        owner = owner_for(root, authority.completion)
        try:
            assert len(owner._recover_active_runtime(workspace_id='workspace').scopes) == 5
        finally:
            owner.close()
    ids = [rid for entry in authority.completion.character_seed_completions
           for rid in entry.payload()['completion'].get('representation_ids', [])]
    assert len(ids) == len(set(ids)) == 6
    with pytest.raises(SubstrateError):
        with i4.begin_genesis_character_administration(data_root=root, intent=intent):
            pytest.fail('active root admitted to I4')
    assert planted == ['agent-0', 'agent-2'] and file_snapshot(root) == before


def test_actual_v2_module_create_and_status_without_embedding(tmp_path):
    from test_native_genesis_cli import arguments, module_process
    from torment_service.external_owner_json import owner_bytes
    root, request, path = tmp_path/'root', tmp_path/'request.json', tmp_path/'intent.json'
    request.write_bytes(owner_bytes(roster_payload(root, (False, False))))
    process = module_process(tmp_path, arguments(request, path))
    stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 0 and not stderr, (stdout, stderr)
    result = json.loads(stdout)
    assert result['agent_ids'] == ['agent-0', 'agent-1']
    before = file_snapshot(root)
    process = module_process(tmp_path, ['status', '--data-root', str(root)])
    stdout, stderr = process.communicate(timeout=60)
    assert process.returncode == 0 and not stderr and json.loads(stdout) == result
    assert file_snapshot(root) == before
