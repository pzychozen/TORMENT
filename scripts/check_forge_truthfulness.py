#!/usr/bin/env python3
"""Check Solo settings using real Forge output and fake provider boundaries.

Run with --artifacts-dir EXTERNAL_DIR. Optional --baseline-html proves that
Hivemind output and the Solo Genesis/policy/write/retry boundary are unchanged.
No model, service, Genesis creation or actual memory write is invoked.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import redirect_stdout
import io
import itertools
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def settings(output, shell):
    env = output['outputs']['out-env']
    pattern = r'^export (\w+)=(.*)$' if shell == 'posix' else r'^set "(\w+)=(.*)"$'
    return dict(re.findall(pattern, env, re.M))


def functions(source):
    return {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}


def provider_probe(source, environment):
    """Execute only the emitted main function, with memory and SDK calls replaced."""
    calls, constructors = [], []
    def complete(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(text='fixture reply')],
            choices=[SimpleNamespace(message=SimpleNamespace(content='fixture reply'))])
    def client(**kwargs):
        constructors.append(kwargs)
        return SimpleNamespace(messages=SimpleNamespace(create=complete),
            chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))
    inputs = iter(['fixture question', 'quit'])
    namespace = dict(input=lambda prompt: next(inputs), setup=lambda: None,
        t_query=lambda q: {}, t_ingest=lambda *args, **kwargs: {'stored': True},
        format_character_context=lambda result: '', format_memories=lambda result: '',
        format_drift_note=lambda result: '', os=SimpleNamespace(environ=environment),
        anthropic=SimpleNamespace(Anthropic=client), OpenAI=client,
        time=SimpleNamespace(time=lambda: 1000),
        uuid=SimpleNamespace(uuid4=lambda: SimpleNamespace(hex='a' * 32)),
        json=json, CHARACTER_NAME='Fixture', WORKSPACE_ID='fixture', AGENT_ID='fixture',
        TORMENT_URL='fixture', TOP_K=8, SYSTEM_PROMPT_TEMPLATE='{character_context}{memory_context}{drift_note}')
    with redirect_stdout(io.StringIO()):
        emitted = functions(source)
        exec(compile(ast.Module(body=[emitted['build_summary'], emitted['main']], type_ignores=[]), '<generated-main>', 'exec'), namespace)
        namespace['main']()
    assert len(calls) == len(constructors) == 1
    return constructors[0], calls[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir', type=Path, required=True)
    parser.add_argument('--baseline-html', type=Path)
    args = parser.parse_args()
    artifacts = args.artifacts_dir.resolve()
    if artifacts.is_relative_to(REPO):
        parser.error('Use an external disposable artifact directory.')
    artifacts.mkdir(parents=True, exist_ok=True)
    results = {}

    def generate(label, **options):
        fixture = dict(dataRoot=str(artifacts / 'unused-root').lower(), **options)
        proc = subprocess.run(['node', str(REPO / 'scripts/forge_solo_fixture.cjs')],
            input=json.dumps(fixture), capture_output=True, text=True, encoding='utf-8', check=True)
        result = json.loads(proc.stdout)
        (artifacts / (label + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        return result

    fixed_off = ['SPINE_ENABLE', 'IDENTITY_SENSITIVE', 'HIVEMIND_ENABLE', 'SRG_COGNITION',
                 'ARCHIVE_RECALL', 'LIVE_SOCIAL', 'CONTEXTUAL_ABSTENTION']
    caps = dict.fromkeys(['cog-spine', 'cog-identity', 'cog-collective', 'cog-srg',
                         'cog-archive', 'cog-livesocial', 'cog-abstention'], True)
    for index, (srg, thinking, heartbeat, bands) in enumerate(itertools.product(
            (False, True), (False, True), ('auto', 'deep', 'active'), ('3', '5', '7', '9'))):
        output = generate('settings-' + str(index), features={'srg': srg, 'crystal': False},
            cognition={**caps, 'cog-thinking': thinking},
            fields={'solo-srg-heartbeat': heartbeat, 'srg-bands': bands})
        assert not output['alerts'], output['alerts']
        wanted = {'TORMENT_SRG_ENABLE': str(int(srg)), 'TORMENT_SRG_BANDS': bands,
                  'TORMENT_SRG_CLASS_A_RATIO': {'auto': '0.25', 'deep': '0.6', 'active': '0.1'}[heartbeat],
                  'TORMENT_SRG_CRYSTAL': '1', 'TORMENT_THINKING_ADVISORY': str(int(thinking)),
                  **{'TORMENT_' + key: '0' for key in fixed_off}}
        for shell in ('posix', 'cmd'):
            emitted = settings(output, shell)
            assert {key: emitted.get(key) for key in wanted} == wanted
            assert dict(dict.fromkeys(wanted, 'stale'), **emitted).items() >= wanted.items()
        assert output['outputs']['out-voice'] == ''
        assert 'voice_pipeline.py' not in output['markdown']
    results['explicit-on-off-default-matrix'] = '48 PASS (both shells)'

    # Execute the actual CMD SET lines in a contaminated process environment,
    # then read the production import-time and per-call SRG/controller flags.
    probe = artifacts / 'runtime_probe.py'
    probe.write_text('''import json
from torment_service import srg_engine as s, thinking_controller as t
print(json.dumps(dict(bands=s.DEFAULT_NUM_BANDS, ratio=s.CLASS_A_RATIO,
    srg=s.srg_enabled(), crystal=s.srg_crystal_enabled(),
    spine=t._SPINE_ENABLE, identity=t._IDENTITY_SENSITIVE_ENABLE,
    srg_cognition=t._SRG_COGNITION_ENABLE, archive=t._ARCHIVE_RECALL_ENABLE,
    live_social=t._LIVE_SOCIAL_ENABLE)))
''', encoding='utf-8')
    for heartbeat, ratio in [('auto', .25), ('deep', .6), ('active', .1)]:
        output = generate('runtime-' + heartbeat, features={'srg': False},
                          fields={'solo-srg-heartbeat': heartbeat})
        emitted = settings(output, 'cmd')
        wanted = {k: v for k, v in emitted.items() if k.startswith('TORMENT_SRG_') or
                  k in {'TORMENT_' + name for name in fixed_off} or k == 'TORMENT_THINKING_ADVISORY'}
        env = dict(os.environ, PYTHONPATH=str(REPO) + os.pathsep + os.environ.get('PYTHONPATH', ''))
        env.update(dict.fromkeys(wanted, '1'))
        env.update(TORMENT_SRG_BANDS='9', TORMENT_SRG_CLASS_A_RATIO='.9', TORMENT_SRG_CRYSTAL='0')
        if os.name == 'nt':
            script = artifacts / ('runtime-' + heartbeat + '.cmd')
            lines = ['@echo off', *[f'set "{k}={v}"' for k, v in wanted.items()],
                     f'"{sys.executable}" -B "{probe}"']
            script.write_text('\n'.join(lines) + '\n', encoding='utf-8')
            proc = subprocess.run(['cmd.exe', '/d', '/c', str(script)], env=env,
                capture_output=True, text=True, check=True)
        else:
            proc = subprocess.run([sys.executable, '-B', str(probe)], env={**env, **wanted},
                capture_output=True, text=True, check=True)
        observed = json.loads(proc.stdout)
        assert observed == dict(bands=5, ratio=ratio, srg=False, crystal=True,
            spine=False, identity=False, srg_cognition=False, archive=False, live_social=False)
    results['stale-environment-production-readers'] = '3 PASS'

    for llm in ('claude', 'openai', 'ollama', 'other'):
        fields = {'openai-model': 'fixture-openai', 'ollama-model': 'fixture-ollama',
                  'ollama-host': 'http://127.0.0.1:12345/', 'other-model': 'fixture-custom',
                  'other-url': 'http://127.0.0.1:23456/v1', 'char-name': 'Fixture "quoted"'}
        output = generate('provider-' + llm, llm=llm, fields=fields)
        assert not output['alerts']
        source = output['outputs']['out-loop-python']
        path = artifacts / (llm + '-chat.py')
        path.write_text(source, encoding='utf-8')
        py_compile.compile(str(path), cfile=str(artifacts / (llm + '-chat.pyc')), doraise=True)
        env = settings(output, 'cmd')
        constructor, request = provider_probe(source, env)
        wanted_model = {'claude': 'claude-sonnet-4-6', 'openai': 'fixture-openai',
                        'ollama': 'fixture-ollama', 'other': 'fixture-custom'}[llm]
        assert request['model'] == wanted_model
        if llm in ('ollama', 'other'):
            assert constructor['base_url'] == ('http://127.0.0.1:12345/v1' if llm == 'ollama'
                                               else fields['other-url'])
        # New-terminal fallback preserves the chosen model/endpoint too.
        fallback, request = provider_probe(source, {})
        assert request['model'] == wanted_model
        assert fallback == constructor
        if llm != 'claude':
            env_key = {'openai': 'OPENAI_MODEL', 'ollama': 'OLLAMA_MODEL', 'other': 'LLM_MODEL'}[llm]
            _, request = provider_probe(source, {env_key: 'terminal-override'})
            assert request['model'] == 'terminal-override'
    results['provider-field-env-client-compile'] = '4 PASS'

    default = generate('default')
    assert 'HF_HUB_OFFLINE=1' in default['outputs']['out-install']
    assert 'uncached BGE' in default['markdown'] and 'complete model is cached' in default['markdown']

    if args.baseline_html:
        before = generate('baseline', htmlPath=str(args.baseline_html.resolve()))
        for block in ('out-workspace', 'out-agent', 'out-prompts', 'out-loop-curl', 'out-response'):
            assert default['outputs'][block] == before['outputs'][block], block
        # Entire default Claude loop remains identical; provider alternatives
        # change only selected SDK model/endpoint arguments.
        assert default['outputs']['out-loop-python'] == before['outputs']['out-loop-python']
        policy = lambda output: [line for line in output['outputs']['out-env'].splitlines()
                                 if 'domain_policy_setup' in line]
        assert policy(default) == policy(before)
        for llm in ('claude', 'openai', 'ollama', 'other'):
            for interaction in ('window', 'basic_hive', 'broadcast'):
                for srg in (False, True):
                    options = dict(mode='hivemind', llm=llm, interaction=interaction, features={'srg': srg})
                    current = generate(f'hive-{llm}-{interaction}-{srg}', **options)
                    baseline = generate(f'hive-before-{llm}-{interaction}-{srg}',
                        htmlPath=str(args.baseline_html.resolve()), **options)
                    assert current == baseline, (llm, interaction, srg)
        results['hivemind-generated-output-and-export'] = '24 exact baseline matches'
        results['solo-genesis-policy-default-client-write-retry'] = 'UNCHANGED'
    (artifacts / 'truthfulness-results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
