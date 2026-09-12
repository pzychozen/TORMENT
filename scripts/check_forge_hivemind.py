#!/usr/bin/env python3
"""Qualify actual Hivemind Forge output with fake transport/provider boundaries.

All artifacts go outside the repository. No model or service is invoked here.
"""
from __future__ import annotations
import argparse
import ast
from copy import deepcopy
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO),str(REPO/'scripts')]
from torment_service.substrate.genesis_onboarding import NativeGenesisOnboardingRequest
from torment_service.identity import DEFAULT_AGENT_OVERLAY

MODES = ('window','basic_hive','broadcast')


def generate(options):
    proc = subprocess.run(['node',str(REPO/'scripts/forge_hivemind_fixture.cjs')],
        input=json.dumps(options),capture_output=True,text=True,encoding='utf-8',check=True)
    return json.loads(proc.stdout)


def load_client(source):
    namespace = {'__name__':'forge_qualified_client'}
    exec(compile(source,'<generated-hive-client>','exec'),namespace)
    return namespace


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.fail_write = None
        self.fail_query = False
        self.decline = False

    def get(self, path):
        assert path == '/health'
        return {'status':'ok'}

    def post(self, path, payload, key=None):
        self.calls.append((path,deepcopy(payload),key))
        if path == '/agent/query':
            if self.fail_query: raise OSError('synthetic query failure')
            return {'hits':[{'summary':'actual memory {braces}'}], 'character_context':{'seed_preamble':"Agent's {context}"},
                'collective_context':{'recent_events':[]}}
        assert path == '/agent/ingest' and key
        if self.fail_write == payload['agent_id']:
            self.fail_write = None
            raise OSError('synthetic storage failure')
        return {'stored':not self.decline}

    def writes(self):
        return [call for call in self.calls if call[0] == '/agent/ingest']


def mutation_checks(output):
    namespace = load_client(output['outputs']['out-loop-python'])
    config = namespace['CONFIG']
    ids = [a['agent_id'] for a in config['agents']]
    mode = config['mode']
    transport = FakeTransport()
    calls, messages = [], []
    keys = iter(range(100))
    def provider(agent, system, history):
        calls.append((agent['agent_id'],system,deepcopy(history)))
        return "Harmless assistant response with {braces} and an apostrophe's meaning."
    client = namespace['HiveClient'](ids[0], transport=transport, provider=provider, emit=messages.append,
        key_factory=lambda: 'fixture-'+str(next(keys)))
    target = ids[1] if mode == 'broadcast' else ids[0]
    transport.fail_write = target
    assert client.submit('First question') is False
    writes = deepcopy(transport.writes())
    pending = deepcopy(next(e['pending'] for e in client.turn['agents'] if e['state']=='PENDING_WRITE'))
    assert pending['agent_id'] == target and json.loads(pending['payload_json'])['domain_id'] == pending['domain_id']
    if mode == 'broadcast':
        assert client.progress() == [(ids[0],'COMPLETE'),(ids[1],'PENDING_WRITE'),(ids[2],'NOT_ATTEMPTED')]
        assert len(calls) == 2
    else:
        assert len(calls) == 1
    before = len(calls),len(transport.calls)
    assert client.submit('Must not replace pending write') is False
    assert (len(calls),len(transport.calls)) == before
    if mode == 'window':
        assert client.switch(ids[1]) is False
        assert client.selected == ids[0]
    assert client.retry() is True
    completed = client.last_turn['agents']
    expected = len(ids) if mode == 'broadcast' else 1
    assert len(calls) == expected
    retry = transport.writes()[len(writes)]
    assert retry == writes[-1]
    assert len({e['pending']['key'] for e in completed}) == expected
    if mode == 'broadcast':
        assert [a for a,_,_ in calls] == ids
        assert [w[1]['agent_id'] for w in transport.writes()] == [ids[0],ids[1],ids[1],ids[2]]
    first_keys = {e['pending']['key'] for e in completed}
    if mode == 'window':
        assert client.switch(ids[1]) is True
        assert all(history == [] for history in client.history.values())
        assert 'persistent TORMENT memory is unchanged' in messages[-1]
    assert client.submit('Second question') is True
    assert not first_keys & {e['pending']['key'] for e in client.last_turn['agents']}
    assert any('storage failed' in message for message in messages)
    if mode == 'basic_hive':
        try: namespace['HiveClient'](transport=transport, provider=provider)
        except ValueError: pass
        else: raise AssertionError('Basic Hive accepted missing agent')
    # Provider exceptions and query errors must never create pending error text.
    for failure in ('provider','query','declined'):
        tr = FakeTransport(); emitted=[]; invocations=[]
        def failing_provider(*args):
            invocations.append(args)
            if failure == 'provider': raise RuntimeError('provider secret/error must never become memory')
            return 'Valid synthetic assistant answer'
        tr.fail_query = failure == 'query'; tr.decline = failure == 'declined'
        c = namespace['HiveClient'](ids[0],transport=tr,provider=failing_provider,emit=emitted.append)
        assert c.submit('Failure fixture') is False
        if failure in ('provider','query'):
            assert tr.writes() == []
            assert all(e['pending'] is None for e in c.turn['agents'])
            assert len(invocations) == (failure == 'provider')
        else:
            assert len(invocations) == len(tr.writes()) == 1
            assert c.turn['agents'][0]['state'] == 'PENDING_WRITE'
            assert any('did not retain' in message for message in emitted)
            pending_call=deepcopy(tr.writes()[0]); tr.decline=False
            assert c.retry() is True
            assert tr.writes()[1] == pending_call
            assert len(invocations) == expected
        c.command('/abandon'); assert c.turn is None
    # All local commands use cached output only; unsupported commands never route.
    before=len(transport.calls)
    for command in ('/help','/clear','/debug','/memories','/events','/reingest','/identity','/proposals'):
        client.command(command)
    assert len(transport.calls)==before


def provider_checks(output):
    ns=load_client(output['outputs']['out-loop-python']); config=ns['CONFIG']
    constructors,calls=[],[]
    def complete(**kw):
        calls.append(kw)
        return SimpleNamespace(content=[SimpleNamespace(type='text',text='fixture')],choices=[SimpleNamespace(message=SimpleNamespace(content='fixture'))])
    def factory(**kw):
        constructors.append(kw)
        return SimpleNamespace(messages=SimpleNamespace(create=complete),chat=SimpleNamespace(completions=SimpleNamespace(create=complete)))
    previous={key:sys.modules.get(key) for key in ('anthropic','openai')}
    env=dict(os.environ)
    try:
        sys.modules['anthropic']=SimpleNamespace(Anthropic=factory)
        sys.modules['openai']=SimpleNamespace(OpenAI=factory)
        os.environ.update(ANTHROPIC_API_KEY='fixture-anthropic',OPENAI_API_KEY='fixture-openai',LLM_API_KEY='fixture-custom',
            OPENAI_MODEL='stale',OLLAMA_MODEL='stale',LLM_MODEL='stale',OPENAI_BASE_URL='https://stale.invalid',
            ANTHROPIC_BASE_URL='https://stale.invalid',OLLAMA_HOST='https://stale.invalid',LLM_BASE_URL='https://stale.invalid')
        assert ns['call_provider'](config['agents'][0],'fixture system',[{'role':'user','content':'fixture'}])=='fixture'
        assert calls[0]['model']==config['model']
        choice=config['provider']; actual=constructors[0]
        if choice=='claude': assert actual==dict(api_key='fixture-anthropic',base_url='https://api.anthropic.com')
        elif choice=='openai': assert actual==dict(api_key='fixture-openai',base_url='https://api.openai.com/v1')
        elif choice=='ollama': assert actual==dict(api_key='ollama',base_url=config['host'].rstrip('/')+'/v1')
        else: assert actual==dict(api_key='fixture-custom',base_url=config['host'])
    finally:
        os.environ.clear(); os.environ.update(env)
        for key,value in previous.items():
            if value is None: sys.modules.pop(key,None)
            else: sys.modules[key]=value


def transport_checks(output):
    ns=load_client(output['outputs']['out-loop-python'])
    requests_module=ns['requests']
    previous_session=requests_module.Session
    previous_env=dict(os.environ)
    calls=[]
    class Session:
        def __init__(self): self.headers={}; self.status=200
        def post(self, url, **kwargs):
            calls.append((url,deepcopy(kwargs),deepcopy(self.headers)))
            def raise_for_status():
                if self.status>=400: raise requests_module.HTTPError(str(self.status))
            return SimpleNamespace(raise_for_status=raise_for_status,json=lambda:{'stored':False})
    try:
        requests_module.Session=Session
        os.environ['TORMENT_API_KEY']='fixture-torment-key'
        tr=ns['HttpTransport']('http://127.0.0.1:8787')
        assert tr.post('/agent/ingest',{'text':'fixture'},key='exact-write-key')=={'stored':False}
        assert calls[-1][1]['headers']=={'Idempotency-Key':'exact-write-key'}
        assert calls[-1][2]=={'X-API-Key':'fixture-torment-key'}
        for status in (401,409,500):
            tr.session.status=status
            try: tr.post('/agent/ingest',{'text':'fixture'},key='exact-write-key')
            except requests_module.HTTPError: pass
            else: raise AssertionError('HTTP refusal treated as success: '+str(status))
        del os.environ['TORMENT_API_KEY']
        assert ns['HttpTransport']().session.headers=={}
    finally:
        requests_module.Session=previous_session
        os.environ.clear(); os.environ.update(previous_env)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts-dir',required=True,type=Path)
    parser.add_argument('--baseline-html',type=Path)
    args=parser.parse_args(); artifacts=args.artifacts_dir.resolve()
    if artifacts.is_relative_to(REPO): parser.error('Use an external artifact directory')
    artifacts.mkdir(parents=True,exist_ok=True)
    base=dict(dataRoot=str(artifacts/'unused-root').lower())
    results={}; modes={}
    def fixture(name, **options):
        output=generate({**base,**options})
        (artifacts/(re.sub(r'[^A-Za-z0-9_.-]','_',name)+'.json')).write_text(json.dumps(output,indent=2),encoding='utf-8')
        return output
    for mode in MODES:
        out=fixture(mode,interaction=mode)
        assert not out['alerts'],out['alerts']
        request=NativeGenesisOnboardingRequest.from_payload(json.loads(out['outputs']['out-workspace']))
        assert request.VERSION==2
        assert [a['agent_id'] for a in request.payload()['agents']]==['alpha','mu','zeta']
        for agent in request.payload()['agents']:
            assert agent['initial_overlay']==DEFAULT_AGENT_OVERLAY
            assert agent['character']['mode']=='ENABLED'
        ns=load_client(out['outputs']['out-loop-python'])
        assert [a['agent_id'] for a in ns['CONFIG']['agents']]==['zeta','alpha','mu']
        mutation_checks(out); transport_checks(out); modes[mode]=out
    for field in ('out-install','out-workspace','out-agent','out-env'):
        assert len({out['outputs'][field] for out in modes.values()})==1,field
    results['three_mode_identity_and_mutations']='PASS'
    matrix=0
    for mode,llm,embed,srg in itertools.product(MODES,('claude','openai','ollama','other'),('hash','st','ollama'),(False,True)):
        out=fixture(f'matrix-{matrix}',interaction=mode,llm=llm,provider=embed,features={'srg':srg,'crystal':False},
            fields={'st-model':'BAAI/bge-small-en-v1.5','st-device':'cpu','ollama-embed-model':'fixture-embed',
                'ollama-url':'http://127.0.0.1:22434','ollama-embed-dimension':'768','openai-model':'fixture-openai','ollama-model':'fixture-chat',
                'ollama-host':'http://127.0.0.1:33434','other-model':'fixture-custom','other-url':'http://localhost:4444/v1'})
        assert not out['alerts'],out['alerts']
        native=NativeGenesisOnboardingRequest.from_payload(json.loads(out['outputs']['out-workspace']))
        provider_checks(out)
        env=out['outputs']['out-env']; install=out['outputs']['out-install']
        assert f'TORMENT_SRG_ENABLE={int(srg)}' in env
        assert 'TORMENT_HIVEMIND_ENABLE=1' in env and 'hivemind_initial_v1' in env
        assert 'set /p' not in env and 'for /f "delims=" %P' in env
        assert 'pip install '+('anthropic' if llm=='claude' else 'openai') in install
        assert ('pip install anthropic' in install)==(llm=='claude')
        assert ('pip install sentence-transformers' in install)==(embed=='st')
        assert native.payload()['representation_lane']['provider']==embed
        for forbidden in ('/workspace/create','/agent/create','/collective/events','/collective/reingest','/proposals/status','/character/state'):
            assert forbidden not in out['markdown'],forbidden
        assert '```bat' in out['markdown'] and '```bash' in out['markdown']
        matrix+=1
    results['provider_embedding_srg_shell_matrix']=matrix
    for value in (30,50,100):
        out=fixture('discount-'+str(value),fields={'discount-slider':value})
        assert f'TORMENT_COLLECTIVE_RETRIEVAL_DISCOUNT={value/100:.2f}' in out['outputs']['out-env']
    for hb,ratio in [('auto','0.25'),('deep','0.6'),('active','0.1')]:
        for bands in ('3','5','7','9'):
            out=fixture('srg-'+hb+bands,fields={'srg-heartbeat':hb,'srg-bands':bands},features={'srg':True})
            assert 'TORMENT_SRG_CLASS_A_RATIO='+ratio in out['outputs']['out-env']
            assert 'TORMENT_SRG_BANDS='+bands in out['outputs']['out-env']
    agents=[{'name':f'Agent {i}','role':"Researcher's {role}\n```",'domain':'creative',
        'seed':"An apostrophe's {meaning}. Newline\ntriple quotes: \"\"\" and backticks ``` </textarea><script> are data."} for i in range(5)]
    for count in (2,5):
        out=fixture('roster-'+str(count),agents=agents[:count],domains=['creative','research'])
        assert not out['alerts'],out['alerts']
        req=NativeGenesisOnboardingRequest.from_payload(json.loads(out['outputs']['out-workspace']))
        assert len(req.payload()['agents'])==count
        assert req.payload()['agents'][0]['character']['definition']['seed_text']==agents[0]['seed'].replace('\n',' ')
        ns=load_client(out['outputs']['out-loop-python'])
        assert ns['CONFIG']['agents'][0]['seed']==agents[0]['seed']
        assert ns['CONFIG']['agents'][0]['role']==agents[0]['role']
        text=ns['system_prompt'](ns['CONFIG']['agents'][0],{'character_context':{'seed_preamble':agents[0]['seed']}})
        assert '{meaning}' in text and "Researcher's {role}" in text
    for names in (['Same Name','same name'],['A!','A?'],['!!!','Valid'],['CON','Valid']):
        bad=deepcopy(agents[:2])
        for agent,name in zip(bad,names): agent['name']=name
        out=fixture('invalid-'+str(names),agents=bad)
        assert out['alerts'] and not out['markdown']
    for domains in ([],['research','custom'],['personal'],['research','research']):
        assert fixture('invalid-domains-'+str(domains),domains=domains)['alerts']
    assert fixture('custom-add',addDomain='custom')['alerts']
    workspace="Hive's {garden} $notes"
    escaped=fixture('workspace-escaping',fields={'hive-workspace-id':workspace})
    assert not escaped['alerts'],escaped['alerts']
    NativeGenesisOnboardingRequest.from_payload(json.loads(escaped['outputs']['out-workspace']))
    posix=escaped['outputs']['out-env'].split('WINDOWS CMD')[0]
    prepare=next(line for line in posix.splitlines() if 'domain_policy_setup prepare' in line)
    tokens=shlex.split(prepare.removesuffix(' && \\'))
    assert tokens[tokens.index('--workspace')+1]==workspace
    assert 'Run python hivemind_client.py' in escaped['outputs']['out-chat-guidance']
    for workspace in ('bad%PATH%','bad!value'):
        assert fixture('unsafe-workspace-'+workspace,fields={'hive-workspace-id':workspace})['alerts']
    removed=fixture('remove-creative',removeDomains=['creative'])
    assert not removed['alerts'] and all(a['domain']!='creative' for a in removed['state']['agents'])
    NativeGenesisOnboardingRequest.from_payload(json.loads(removed['outputs']['out-workspace']))
    results['roster_domain_and_escaping']='PASS'
    html=(REPO/'start/torment_character_creator.html').read_text(encoding='utf-8')
    assert '<select id="domain-input"' in html and 'add custom domain...' not in html
    for field in ('echo','convergence','confidence','drift-budget','rate-limit'):
        before=html[:html.index('id="'+field+'-slider"')]
        assert 'hidden' in before[before.rfind('<div class="slider-field'):]
    for field in ('character-hive','hivemind-feature'):
        assert re.search(r'<div class="toggle-row active" hidden style="display:none" id="toggle-'+field+'"',html)
    if args.baseline_html:
        old=args.baseline_html.read_text(encoding='utf-8')
        def sliders(text):
            return {re.search(r'id="([^"]+)"',tag).group(1):{k:v for k,v in re.findall(r'(min|max|value|step)="([^"]*)"',tag)}
                for tag in re.findall(r'<input\b[^>]*type="range"[^>]*>',text)}
        assert sliders(html)==sliders(old)
        for start,end in [('function generateSolo() {','function generateHivemind() {'),('// <<< BEGIN solo_genesis >>>','// <<< END solo_genesis >>>')]:
            if start.startswith('function'):
                # New Hive helpers now follow the untouched Solo body.
                actual=html.split(start)[1].split('let lastHivemindGeneration')[0].rstrip()
                expected=old.split(start)[1].split(end)[0].rstrip()
            else:
                actual=html.split(start)[1].split(end)[0]; expected=old.split(start)[1].split(end)[0]
            assert actual==expected,'Solo source changed'
        results['numeric_sliders_and_solo_source']='UNCHANGED'
    results.update(status='PASS',real_models_invoked=False,conversational_models_invoked=False)
    (artifacts/'H2C_STATIC_RESULTS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))


if __name__=='__main__': main()
