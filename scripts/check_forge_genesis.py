#!/usr/bin/env python3
"""Exercise actual Forge JS output against I9, without starting models or services.

Run from the repository: python -B scripts/check_forge_genesis.py --artifacts-dir EXTERNAL_DIR
The directory holds requests, emitted Python and evidence. No Genesis create is run here.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
from types import SimpleNamespace
import uuid

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from torment_service.substrate.genesis_onboarding import NativeGenesisOnboardingRequest
from torment_service.substrate.genesis_fence import canonical_genesis_root
from check_forge_output import check_section, SOLO_GENESIS_REQUIRED


# S5 read/client setup stays frozen. Initial policy setup changes startup
# commands without changing the Genesis request builder or client reads.
FROZEN_FUNCTION_SHA256 = {
    't_post': 'd8f6f0bade6de5558d2d860adfe92e2148395a112036f7ffb7b74aff3a7dd707',
    't_get': '7205e7f413b63a6c5ec0be41ef79b7e211e56bddadc29b95361dda4ad68b07e4',
    'setup': '73bf1c438646b2ca3ac09c476dd6ea6b0a1ec667633cff49747cfba984288987',
    't_query': '37e7594df09ccc3527a537cdd9e1a200367a3e9d9e5addeae5dd91e1f44ac87b',
}
FROZEN_GENESIS_REQUEST_BUILDER_SHA256 = 'c2e5550c881ff18fc2f02e39c4ae3c1726ec5f9888d52526b50959b82e71af09'
# Only setup-artifact guidance changed inside the helper; the builder above
# retains its original lock independently of this newly qualified helper hash.
FROZEN_GENESIS_HELPER_SHA256 = '6ae9088f8441ab69f63c02a1ccb215d496fa1f51ae59e8695840250b50e6267a'
FROZEN_REQUEST_SHA256 = 'eb3c5a3c957c9f217fe158c3a48218ad8caaf3b78f8a15ed1a2756eb885b0bba'


def check_solo_write_contract(output):
    """Exercise emitted functions with fake HTTP/provider boundaries, never SDK imports."""
    source = output['outputs']['out-loop-python']
    tree = ast.parse(source)
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name, expected in FROZEN_FUNCTION_SHA256.items():
        assert hashlib.sha256(ast.get_source_segment(source, functions[name]).encode()).hexdigest() == expected, name
    ingest = functions['t_ingest']
    assert [arg.arg for arg in ingest.args.kwonlyargs] == ['idempotency_key']
    assert ingest.args.kw_defaults == [None], 'caller must retain the key, not regenerate it on retry'
    curl = output['outputs']['out-loop-curl']
    assert '-H "Idempotency-Key: <unique-key-for-this-write>"' in curl
    assert 'Reuse the same key only when retrying the same write.' in curl
    assert 'Use a new key for a new conversation memory.' in curl

    writes, queries, generations, gets = [], [], [], []

    def response(payload):
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)

    def post(url, *, json, timeout, headers=None):
        assert timeout == 30
        if url.endswith('/agent/query'):
            assert headers is None, 'read transport must remain unkeyed'
            queries.append(deepcopy(json))
            return response({'hits': [], 'character_context': {}})
        assert url == 'fixture/agent/ingest'
        assert set(headers) == {'Idempotency-Key'}
        writes.append({'payload': deepcopy(json), 'headers': dict(headers)})
        if len(writes) == 1:
            raise TimeoutError('synthetic lost write response')
        return response({'stored': True, 'eid': 17})

    def get(url, **kwargs):
        gets.append(url)
        return response({'ok': True})

    def complete(**kwargs):
        generations.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text='Synthetic reply.')],
                               choices=[SimpleNamespace(message=SimpleNamespace(content='Synthetic reply.'))])

    provider = SimpleNamespace(messages=SimpleNamespace(create=complete),
                               chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))
    commands = iter(['first memory', 'must wait for retry', '/retry', 'second memory', 'quit'])
    namespace = dict(Dict=dict, Any=object, List=list, uuid=uuid, json=json, os=os, sys=sys,
        time=SimpleNamespace(time=lambda: 1000), requests=SimpleNamespace(post=post, get=get),
        anthropic=SimpleNamespace(Anthropic=lambda: provider), OpenAI=lambda **kwargs: provider,
        input=lambda prompt: next(commands), TORMENT_URL='fixture', WORKSPACE_ID='fixture_ws',
        AGENT_ID='fixture_agent', CHARACTER_NAME='Fixture', TOP_K=8,
        SYSTEM_PROMPT_TEMPLATE='{character_context}{memory_context}{drift_note}')
    # No top-level imports, SDK construction or real provider/network calls.
    exec(compile(ast.Module(body=list(functions.values()), type_ignores=[]), '<emitted-client>', 'exec'), namespace)
    with redirect_stdout(io.StringIO()):
        namespace['main']()
    assert gets == ['fixture/health']
    assert [q['query'] for q in queries] == ['first memory', 'second memory']
    assert all(q == dict(workspace_id='fixture_ws', agent_id='fixture_agent',
                        query=q['query'], top_k=8) for q in queries)
    assert len(generations) == 2, 'retry or blocked input must not regenerate a reply'
    assert len(writes) == 3 and writes[0] == writes[1], 'retry changed its key or semantic payload'
    keys = [w['headers']['Idempotency-Key'] for w in writes]
    assert keys[0] != keys[2], 'distinct conversation writes reused a key'
    assert all(re.fullmatch(r'[0-9a-f]{32}', key) and len(key) <= 256 for key in keys)
    assert [w['payload']['step'] for w in writes] == [1001, 1001, 1002]
    assert writes[0]['payload']['text'] == 'User said: first memory\nFixture responded: Synthetic reply.'
    assert writes[2]['payload']['text'] == 'User said: second memory\nFixture responded: Synthetic reply.'


def check_windows_profile_loader(output, artifacts, profile_file=None):
    """Run the emitted interactive CMD loader, adapting only %P for a batch file."""
    if os.name != 'nt':
        return 'NOT_APPLICABLE_ON_THIS_PLATFORM'
    target = artifacts / 'torment_genesis_profile.json'
    if profile_file is not None:
        raw = profile_file.read_bytes()
    else:
        # Same multiline serializer/shape used by I9; no installation is created.
        from torment_service.external_owner_json import owner_bytes
        raw = owner_bytes(dict(compression_enabled=False, deep_memory_enabled=False,
            representation_provider='st', representation_model='BAAI/bge-small-en-v1.5',
            representation_dimension=384, admitted_scope_plan_digest='a' * 64,
            external_owner_digest='b' * 64))
    assert len(raw.splitlines()) > 1 and len(json.loads(raw)) == 7
    target.write_bytes(raw)
    lines = output['outputs']['out-env'].splitlines()
    loader, = [line for line in lines if line.startswith('for /f "delims=" %P ')]
    assert hashlib.sha256(loader.encode()).hexdigest() == 'abc1174ecbd2f6a2f0a3314c88045ed5e7bb14818127cd050b234e2c80392ecf'
    assert '%%P' not in loader, 'Forge must emit interactive CMD syntax'
    verifier = artifacts / 'verify_profile_env.py'
    verifier.write_text('''import json, os
from pathlib import Path
text = os.environ["TORMENT_DEPLOYMENT_PROFILE_JSON"]
value = json.loads(text)
expected = json.loads(Path("torment_genesis_profile.json").read_text(encoding="utf-8"))
assert value == expected and len(value) == 7
assert "\\n" not in text and "\\r" not in text
Path("windows-profile-env.json").write_text(json.dumps({"json_parse": "PASS",
    "exact_value_equality": "PASS", "field_count": len(value), "profile": value}, indent=2))
print("WINDOWS_PROFILE_ENV_JSON_PARSE=PASS; WINDOWS_PROFILE_ENV_EXACT_VALUE_EQUALITY=PASS; WINDOWS_PROFILE_ENV_FIELD_COUNT=7")
''', encoding='utf-8')
    batch = artifacts / 'profile-loader.cmd'
    batch.write_text('@echo off\ncall conda activate torment\nif errorlevel 1 exit /b %errorlevel%\n'
        'set "TORMENT_DEPLOYMENT_PROFILE_JSON="\n' + loader.replace('%P', '%%P') +
        '\npython -B -X utf8 verify_profile_env.py\n', encoding='utf-8')
    proc = subprocess.run(['cmd.exe', '/d', '/c', batch.name], cwd=artifacts,
                          text=True, encoding='utf-8', capture_output=True)
    (artifacts / 'profile-loader.stdout.log').write_text(proc.stdout, encoding='utf-8')
    (artifacts / 'profile-loader.stderr.log').write_text(proc.stderr, encoding='utf-8')
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    print(proc.stdout.strip())
    # Follow the S5 path guidance: stay in the repository and use quoted absolute
    # artifact paths, including spaces. Only the filename placeholder is replaced.
    external = artifacts / 'setup artifacts'
    external.mkdir(exist_ok=True)
    external_profile = external / target.name
    external_profile.write_bytes(raw)
    absolute_loader = loader.replace(target.name, '"' + str(external_profile) + '"')
    absolute_verifier = external / verifier.name
    absolute_verifier.write_text(verifier.read_text(encoding='utf-8').replace(
        'Path("torment_genesis_profile.json")', 'Path(' + repr(str(external_profile)) + ')').replace(
        'Path("windows-profile-env.json")', 'Path(' + repr(str(external / 'windows-profile-env.json')) + ')'),
        encoding='utf-8')
    absolute_batch = artifacts / 'profile-loader-from-repo.cmd'
    absolute_batch.write_text('@echo off\ncall conda activate torment\nif errorlevel 1 exit /b %errorlevel%\n'
        'set "TORMENT_DEPLOYMENT_PROFILE_JSON="\n' + absolute_loader.replace('%P', '%%P') +
        '\npython -B -X utf8 "' + str(absolute_verifier) + '"\n', encoding='utf-8')
    proc = subprocess.run(['cmd.exe', '/d', '/c', str(absolute_batch)], cwd=REPO,
                          text=True, encoding='utf-8', capture_output=True)
    (artifacts / 'profile-loader-from-repo.stdout.log').write_text(proc.stdout, encoding='utf-8')
    (artifacts / 'profile-loader-from-repo.stderr.log').write_text(proc.stderr, encoding='utf-8')
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    print('WINDOWS_PROFILE_FROM_REPOSITORY_WITH_EXTERNAL_PATH=PASS')
    return 'PASS'


def check_solo_presentation(output):
    """Check the actual exported instructions without running product commands."""
    blocks, markdown = output['outputs'], output['markdown']
    guide = blocks['out-directory-guide']
    for role in ('REPOSITORY DIRECTORY', 'GENESIS ARTIFACT DIRECTORY', 'TORMENT DATA ROOT'):
        assert role in guide and role in markdown, role
    assert 'examples only' in guide
    assert 'C:\\path\\to\\TORMENT' in guide and '/path/to/TORMENT' in guide
    assert 'my-character-setup' in guide and 'my-character-data' in guide
    assert 'quoted absolute path' in guide and 'do not change into the artifact directory' in guide
    for name in ('install', 'request', 'create', 'startup', 'chat'):
        assert blocks['out-' + name + '-guidance'] in markdown, name
    assert 'NOT inside the TORMENT data root' in blocks['out-request-guidance']
    for name in ('install', 'create', 'startup'):
        assert 'repository with the torment environment active' in blocks['out-' + name + '-guidance']
    request_section = markdown.split('## 1. Native Genesis Request\n\n', 1)[1].split('\n---', 1)[0]
    assert request_section.index(blocks['out-request-guidance']) < request_section.index('```json')
    assert '```json\n' + blocks['out-workspace'] + '\n```' in request_section
    for name in ('out-install', 'out-agent', 'out-env'):
        source = blocks[name]
        assert source.count('LINUX / MACOS / WSL — copy this section only') == 1
        assert source.count('WINDOWS CMD — copy this section only') == 1
        posix, cmd = source.split(':: ' + '=' * 60, 1)
        assert not any(line.startswith('#') for line in cmd.splitlines())
        assert not any(line.startswith(('set ', 'for /f', '::')) for line in posix.splitlines())
    windows_blocks = re.findall(r'```bat\n(.*?)\n```', markdown, re.S)
    assert len(windows_blocks) == 3
    assert all(not any(line.startswith('#') for line in block.splitlines()) for block in windows_blocks)
    assert markdown.count('### LINUX / MACOS / WSL') == markdown.count('### WINDOWS CMD') == 3
    credentials = blocks['out-credentials-guidance']
    if credentials:
        assert credentials in markdown and credentials not in blocks['out-env']


def check_solo_policy_setup(output, artifacts=None):
    """Check the emitted initial chain; optionally test shell failure gating.

    Shell probes replace only command executables with a recording stub. They
    never start Genesis, a model, policy publication, or the actual service.
    """
    blocks = output['outputs']
    workspace = json.loads(blocks['out-workspace'])['workspace']['workspace_id']
    assert 'torment_solo_policy_request.json' in blocks['out-directory-guide']
    assert 'Setup completes only after policy verification passes' in blocks['out-startup-guidance']
    assert 'without repeating initial policy setup' in blocks['out-startup-guidance']
    assert 'auto_merge_motifs' not in blocks['out-env'], 'Forge must not contain semantic policy values'
    sections = blocks['out-env'].split(':: ' + '=' * 60, 1)
    for shell, section in zip(('posix', 'cmd'), sections):
        root = '"%TORMENT_DATA_DIR%"' if shell == 'cmd' else '"$TORMENT_DATA_DIR"'
        args = ' --data-root ' + root + ' --workspace "' + workspace + '" --posture solo_private_v1 --request torment_solo_policy_request.json'
        expected = ['python -m torment_service.domain_policy_setup ' + cmd + args for cmd in ('prepare', 'create', 'verify')]
        expected.append('python -m torment_service')
        chain = ' && '.join(expected)
        assert section.count(chain) == 1, shell
        assert section.index('TORMENT_DEPLOYMENT_PROFILE_JSON=') < section.index(chain)
        assert section.index(chain) < section.index('/health')
        assert section.count('python -m torment_service\n') == 1, 'startup must occur only inside the gated chain'
        if artifacts is None or (shell == 'cmd' and os.name != 'nt'):
            continue
        if shell == 'posix':
            import shutil
            executable = shutil.which('bash') if os.name != 'nt' else None
            if executable is None:
                continue  # POSIX structure still checked on Windows; CMD is authoritative.
        stub = artifacts / 'policy-chain-stub.py'
        stub.write_text('import os, sys\nfrom pathlib import Path\n'
            'with Path(os.environ["POLICY_PROBE_LOG"]).open("a") as f: f.write(sys.argv[1] + "\\n")\n'
            'raise SystemExit(7 if sys.argv[1] == os.environ.get("POLICY_PROBE_FAIL") else 0)\n', encoding='utf-8')
        invocation = '"' + sys.executable + '" "' + str(stub) + '"'
        probe = chain.replace('python -m torment_service.domain_policy_setup', invocation)
        probe = probe.replace('python -m torment_service', invocation + ' service')
        script = artifacts / ('policy-chain.cmd' if shell == 'cmd' else 'policy-chain.sh')
        script.write_text(('@echo off\n' if shell == 'cmd' else '') + probe + '\n', encoding='utf-8')
        for fail in ('prepare', 'create', 'verify', ''):
            log = artifacts / ('policy-chain-' + shell + '-' + (fail or 'success') + '.log')
            log.write_text('', encoding='utf-8')
            env = dict(os.environ, POLICY_PROBE_LOG=str(log), POLICY_PROBE_FAIL=fail)
            command = ['cmd.exe', '/d', '/c', str(script)] if shell == 'cmd' else [executable, str(script)]
            proc = subprocess.run(command, env=env, capture_output=True, text=True)
            wanted = ['prepare', 'create', 'verify', 'service']
            if fail: wanted = wanted[:wanted.index(fail) + 1]
            assert log.read_text().splitlines() == wanted, (shell, fail, proc.stdout, proc.stderr)
            assert proc.returncode == (7 if fail else 0)


def without_initial_policy_setup(env):
    """Retain S5 env equality after removing only the newly qualified setup."""
    env = re.sub(r'python -m torment_service\.domain_policy_setup prepare[^\n]* && (?=python -m torment_service\n)', '', env)
    for comment in ('#', '::'):
        env = env.replace(comment + ' Initial setup: replace profile and policy-request filenames with quoted absolute artifact paths.',
            comment + ' Replace the profile filename with its quoted absolute path in your setup-artifact directory.')
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir', required=True, type=Path)
    parser.add_argument('--profile-file', type=Path,
                        help='Optional existing I9 profile for actual Windows CMD transport validation')
    parser.add_argument('--frozen-output', type=Path,
                        help='Optional accepted S4/S5 output to prove its exact request hash and unchanged setup blocks')
    args = parser.parse_args()
    artifacts = args.artifacts_dir.resolve()
    if artifacts.is_relative_to(REPO):
        parser.error('Use an external disposable artifact directory.')
    artifacts.mkdir(parents=True, exist_ok=True)
    html = (REPO / 'start/torment_character_creator.html').read_text(encoding='utf-8')
    helper = re.search(r'// <<< BEGIN solo_genesis >>>(.*?)// <<< END solo_genesis >>>', html, re.S)
    assert helper and hashlib.sha256(helper.group(1).encode()).hexdigest() == FROZEN_GENESIS_HELPER_SHA256
    builder = html[html.index('function buildSoloGenesisRequest('):html.index('\nfunction soloEmbeddingVars(')]
    assert hashlib.sha256(builder.encode()).hexdigest() == FROZEN_GENESIS_REQUEST_BUILDER_SHA256
    js = artifacts / 'forge.js'
    js.write_text(html.split('<script>')[1].split('</script>')[0], encoding='utf-8')
    subprocess.run(['node', '--check', str(js)], check=True)
    results = {}

    def generate(label, **options):
        root = str(canonical_genesis_root(artifacts / (label + '-root')))
        fixture = dict(dataRoot=root, **options)
        proc = subprocess.run(['node', str(REPO / 'scripts/forge_solo_fixture.cjs')],
                              input=json.dumps(fixture), text=True, encoding='utf-8',
                              capture_output=True, check=True)
        output = json.loads(proc.stdout)
        (artifacts / (label + '-output.json')).write_text(json.dumps(output, indent=2), encoding='utf-8')
        return output

    def valid(label, **options):
        output = generate(label, **options)
        assert not output['alerts'], output['alerts']
        blocks = output['outputs']
        raw = blocks['out-workspace']
        assert '"version": 1' in raw
        payload = json.loads(raw)
        assert set(payload) == set('contract version data_root_identity workspace agent character profile_choice representation_lane'.split())
        assert NativeGenesisOnboardingRequest.from_payload(payload).payload() == payload
        assert payload['workspace'] == {'workspace_id': 'forge_qualification', 'ordered_domains': ['personal']}
        assert payload['agent']['private_motif_domain_id'] == 'personal'
        lane, profile = payload['representation_lane'], payload['profile_choice']
        assert profile == dict(compression_enabled=False, deep_memory_enabled=False,
                              representation_provider=lane['provider'], representation_model=lane['model'],
                              representation_dimension=lane['dimension'])
        assert len(lane) == 8
        source = '\n'.join(blocks.values())
        for term in SOLO_GENESIS_REQUIRED:
            assert term in source, term
        errors = check_section('solo', source + '\n' + output['markdown'])
        assert not errors, errors
        for forbidden in ('/workspace/create', '/agent/create', 'TORMENT_PROFILE=companion',
                          'First run creates workspace + agent automatically',
                          'set /p TORMENT_DEPLOYMENT_PROFILE_JSON='):
            assert forbidden not in source + output['markdown'], forbidden
        assert 'python -m torment_service' not in blocks['out-install']
        assert '/health' not in blocks['out-install']
        assert blocks['out-agent'].count('python -m torment_service.native_genesis create') == 2
        assert '--confirm-all-offline-conditions' in blocks['out-agent']
        assert 'human statement' in blocks['out-agent'] and 'not an automatic process census' in blocks['out-agent']
        assert 'for /f "delims=" %P ' in blocks['out-env']
        assert 'json.dumps(json.load(open(sys.argv[1])))' in blocks['out-env']
        assert 'torment_genesis_profile.json\') do @set "TORMENT_DEPLOYMENT_PROFILE_JSON=%P"' in blocks['out-env']
        assert 'export TORMENT_DEPLOYMENT_PROFILE_JSON="$(cat torment_genesis_profile.json)"' in blocks['out-env']
        assert 'TORMENT_ADMISSION_DESCRIPTOR_PATH' in blocks['out-env']
        assert 'outside the selected data root' in output['markdown']
        check_solo_presentation(output)
        check_solo_write_contract(output)
        check_solo_policy_setup(output)
        py = artifacts / (label + '-chat.py')
        py.write_text(blocks['out-loop-python'], encoding='utf-8')
        py_compile.compile(str(py), cfile=str(artifacts / (label + '-chat.pyc')), doraise=True)
        tree = ast.parse(py.read_text(encoding='utf-8'))
        assert not any(isinstance(n, ast.FunctionDef) and n.name == 't_identity' for n in tree.body)
        for command in ('/status', '/debug', '/memories', '/clear'):
            assert command in blocks['out-loop-python'], command
        assert 'identity_state' in blocks['out-response']
        setup = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'setup')
        calls = [n for n in ast.walk(setup) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        assert not any(n.func.id == 't_post' for n in calls)
        assert '/identity' not in ast.get_source_segment(blocks['out-loop-python'], setup)
        # Execute only setup, with fake GETs. No imports, SDK, network or chat loop.
        gets = []
        namespace = {'t_get': lambda *args: gets.append(args), 'TORMENT_URL': 'fixture',
                     'WORKSPACE_ID': 'forge_qualification', 'AGENT_ID': 'forge_qualification'}
        exec(compile(ast.Module(body=[setup], type_ignores=[]), '<emitted-setup>', 'exec'), namespace)
        namespace['setup']()
        assert gets == [('/health',)]
        attempted = []
        def refused_get(path, *params):
            attempted.append(path)
            raise RuntimeError('fixture unavailable')
        namespace.update(t_get=refused_get, sys=sys)
        message = io.StringIO()
        with redirect_stdout(message):
            try:
                namespace['setup']()
            except SystemExit as exc:
                assert exc.code == 1
            else:
                raise AssertionError('setup accepted an unreachable service')
        assert 'Complete Native Genesis setup' in message.getvalue()
        assert attempted == ['/health']
        assert not any(isinstance(n, ast.Name) and n.id == 'SEED' for n in ast.walk(tree))
        (artifacts / (label + '-request.json')).write_text(raw, encoding='utf-8')
        results[label] = 'PASS'
        return payload, output

    default, default_output = valid('default-st')
    check_solo_policy_setup(default_output, artifacts)
    results['policy-setup-order-and-failure-gating'] = 'PASS'
    results['windows-profile-loader'] = check_windows_profile_loader(default_output, artifacts, args.profile_file)
    assert default['representation_lane']['model'] == 'BAAI/bge-small-en-v1.5'
    assert default['representation_lane']['dimension'] == 384
    assert default['agent']['initial_overlay'] == dict(write_threshold=.45, decay_scale=1.0,
        novelty_bias=.50, motif_sensitivity=.70, promotion_bias=.6, contradiction_sensitivity=.8,
        reinforcement_gain=.9, coupling_strength=.25, shared_trust=.6, stability_guard=.8)
    definition = default['character']['definition']
    assert definition == dict(seed_id='forge_qualification_v1', character_name='Forge Qualification',
        seed_text='Keeps careful records. Values patient reasoning. Remembers shared projects.',
        owner_agent_id='forge_qualification', drift_window_steps=500, drift_correction_threshold=.35,
        drift_gravity_strength=.12, core_half_life=3650., relational_half_life=30., situational_half_life=7.,
        core_weight=.50, derived_weight=.42, relational_weight=.35, situational_weight=.15, version='1.0.0')
    seed = default['agent']['identity_seed']
    assert seed['core_traits'] == ['analytical']
    assert seed['priority_weights'] == dict(facts=.8, projects=.7, preferences=.4, motifs=.7)
    assert seed['coupling_mode'] == 'read_only' and seed['coupling_strength'] == .25
    disabled, _ = valid('disabled', character=False)
    assert disabled['character'] == {'mode': 'DISABLED'}
    assert disabled['agent']['identity_seed']['seed_id'] == disabled['agent']['identity_seed']['seed_text'] == ''
    assert 'character_name' not in disabled['agent']['identity_seed']
    hash_request, hash_output = valid('hash', provider='hash')
    assert hash_request['representation_lane']['model'] == 'hash:384:torment'
    for block in ('out-agent', 'out-env'):
        for term in ('TORMENT_EMBED_PROVIDER=hash', 'TORMENT_HASH_DIM=384', 'TORMENT_HASH_SALT=torment'):
            assert term in hash_output['outputs'][block]
    custom, _ = valid('custom-st', fields={'st-model': 'operator/model', 'st-dimension': '768'}, traits=['curious'])
    assert custom['representation_lane']['dimension'] == 768
    assert custom['agent']['identity_seed']['core_traits'] == ['curious']
    ollama, out = valid('ollama', provider='ollama', fields={'ollama-embed-dimension': '768'})
    assert ollama['representation_lane']['dimension'] == 768
    assert 'TORMENT_OLLAMA_URL=http://127.0.0.1:11434' in out['outputs']['out-agent']
    assert 'TORMENT_EMBED_STRICT=1' in out['outputs']['out-env']
    for llm in ('openai', 'ollama', 'other'):
        valid('llm-' + llm, llm=llm)
    decay_values = []
    for position in range(5):
        # All existing slider settings must remain expressible by frozen I9.
        payload, _ = valid('sliders-' + str(position), fields={key + '-slider': str(position)
                          for key in ('drift', 'gravity', 'wt', 'ds', 'nb', 'ms')})
        decay_values.append(payload['agent']['initial_overlay']['decay_scale'])
    assert decay_values == [0.50, 0.75, 1.0, 1.4, 2.0], 'S6A must not change decay mapping'
    if args.frozen_output:
        frozen = json.loads(args.frozen_output.read_text(encoding='utf-8'))['outputs']
        assert hashlib.sha256(frozen['out-workspace'].encode()).hexdigest() == FROZEN_REQUEST_SHA256
        frozen_root = json.loads(frozen['out-workspace'])['data_root_identity']
        _, current = valid('frozen-request', fields={'solo-data-root': frozen_root})
        for name in ('out-workspace', 'out-agent', 'out-install',
                     'out-prompts', 'out-response', 'out-voice'):
            assert current['outputs'][name] == frozen[name], name
        assert without_initial_policy_setup(current['outputs']['out-env']) == frozen['out-env']
        results['frozen-request-sha256'] = FROZEN_REQUEST_SHA256
    results['native-write-client-retry-contract'] = 'PASS'
    results['frozen-read-client-setup-genesis-request-builder'] = 'PASS'
    results['decay-numeric-mapping-unchanged'] = 'PASS'
    spaced_root = str(canonical_genesis_root(artifacts / 'space & (parentheses)' / 'root'))
    _, spaced = valid('spaced-root', fields={'solo-data-root': spaced_root})
    assert 'set "TORMENT_DATA_DIR=' + spaced_root + '"' in spaced['outputs']['out-env']
    for label, options in [
        ('blank-root', {'fields': {'solo-data-root': ''}}),
        ('relative-root', {'fields': {'solo-data-root': 'relative/root'}}),
        ('drive-relative', {'fields': {'solo-data-root': 'C:relative'}}),
        ('compression', {'compression': True}),
        ('missing-dimension', {'provider': 'ollama'}),
        ('fraction-dimension', {'fields': {'st-dimension': '1.5'}}),
        ('zero-dimension', {'fields': {'st-dimension': '0'}}),
    ]:
        output = generate(label, **options)
        assert output['alerts'] and not output['outputs']['out-workspace'], label
        results[label] = 'REFUSED_AS_REQUIRED'
    (artifacts / 'contract-checks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
