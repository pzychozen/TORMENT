#!/usr/bin/env python3
"""Exercise actual Forge JS output against I9, without starting models or services.

Run from the repository: python -B scripts/check_forge_genesis.py --artifacts-dir EXTERNAL_DIR
The directory holds requests, emitted Python and evidence. No Genesis create is run here.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from torment_service.substrate.genesis_onboarding import NativeGenesisOnboardingRequest
from torment_service.substrate.genesis_fence import canonical_genesis_root
from check_forge_output import check_section, SOLO_GENESIS_REQUIRED


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
    return 'PASS'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir', required=True, type=Path)
    parser.add_argument('--profile-file', type=Path,
                        help='Optional existing I9 profile for actual Windows CMD transport validation')
    args = parser.parse_args()
    artifacts = args.artifacts_dir.resolve()
    if artifacts.is_relative_to(REPO):
        parser.error('Use an external disposable artifact directory.')
    artifacts.mkdir(parents=True, exist_ok=True)
    html = (REPO / 'start/torment_character_creator.html').read_text(encoding='utf-8')
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
        assert '## 1. Native Genesis Request\n\n```json\n' + raw in output['markdown']
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
    for position in range(5):
        # All existing slider settings must remain expressible by frozen I9.
        valid('sliders-' + str(position), fields={key + '-slider': str(position)
              for key in ('drift', 'gravity', 'wt', 'ds', 'nb', 'ms')})
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
