"""Actual local command parsing, subprocess recovery and operator-file safety."""
from contextlib import closing
import ast
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from torment_service import native_genesis as cli
from torment_service.external_owner_json import owner_bytes
from torment_service.substrate import genesis_onboarding as onboarding
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_recovery as i7
from torment_service.substrate.errors import SubstrateError
from test_native_genesis_administration import child
from test_native_genesis_completion import file_snapshot
from test_native_genesis_onboarding import request_payload, planned, run_driver, confirmation, DeterministicTestEmbedder, NoEmbeddingDependency


def inputs(tmp_path, enabled=False):
    root, request, intent = tmp_path / "root", tmp_path / "request.json", tmp_path / "intent.json"
    request.write_bytes(owner_bytes(request_payload(root, enabled)))
    return root, request, intent


def arguments(request, intent, *, command="create", profile=None):
    args = [command, "--intent", str(intent)]
    if command != "apply": args += ["--request", str(request)]
    if command != "plan":
        args += ["--operator-attestation", "I confirm the explicit offline conditions for this disposable root.",
            "--issuer-reference", "i9-test-operator", "--confirm-all-offline-conditions", "--public-listener", "http://127.0.0.1:8787"]
        if profile: args += ["--profile-out", str(profile)]
    return args


def call(args, **kwargs):
    output = StringIO()
    code = cli.main(args, stdout=output, **kwargs)
    return code, json.loads(output.getvalue())


def forbidden_factory():
    pytest.fail("model dependency must not be constructed")


def test_plan_has_no_root_or_model_effect_and_exact_replay(tmp_path):
    root, request, intent = inputs(tmp_path, True)
    args = arguments(request, intent, command="plan")
    code, first = call(args, embedder_factory=forbidden_factory)
    assert code == 0 and first["status"] == "PLANNED" and not root.exists()
    before = intent.read_bytes(), intent.stat().st_mtime_ns
    assert call(args, embedder_factory=forbidden_factory) == (code, first)
    assert (intent.read_bytes(), intent.stat().st_mtime_ns) == before


@pytest.mark.parametrize("enabled", [False, True])
def test_cli_create_apply_profile_and_active_replay(tmp_path, enabled):
    root, request, intent_path = inputs(tmp_path, enabled)
    profile = tmp_path / "profile.json"
    embedder = DeterministicTestEmbedder()
    args = arguments(request, intent_path, profile=profile)
    code, result = call(args, embedder_factory=(lambda: embedder) if enabled else forbidden_factory)
    assert code == 0 and result["status"] == "NATIVE_ACTIVE"
    assert len(embedder.calls) == (3 if enabled else 0)
    before = file_snapshot(root), intent_path.read_bytes(), profile.read_bytes()
    assert call(args, embedder_factory=forbidden_factory) == (code, result)
    assert call(arguments(request, intent_path, command="apply", profile=profile), embedder_factory=forbidden_factory) == (code, result)
    assert (file_snapshot(root), intent_path.read_bytes(), profile.read_bytes()) == before
    assert set(result) == {"status", "data_root", "workspace_id", "agent_id", "core_id", "core_relative_path",
        "selector_generation", "completion_digest", "qualified_deployment_profile"}
    assert "First anchor" not in json.dumps(result) and "analytical" not in json.dumps(result)


def module_process(tmp_path, args):
    """Real python -m invocation; install the existing test audit at startup."""
    boot = tmp_path / "python-bootstrap"
    boot.mkdir(exist_ok=True)
    (boot / "sitecustomize.py").write_text(
        "import os\np=os.environ.get('TORMENT_GENESIS_I3_CHILD_AUDIT')\n"
        "if p: exec(compile(open(p,encoding='utf8').read(),p,'exec'))\n", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(boot), str(Path.cwd())))
    return subprocess.Popen([sys.executable, "-B", "-X", "utf8", "-m", "torment_service.native_genesis", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)


def test_actual_module_invocation_and_readonly_status(tmp_path):
    root, request, intent = inputs(tmp_path)
    process = module_process(tmp_path, arguments(request, intent))
    output, error = process.communicate(timeout=60)
    assert process.returncode == 0, output + error
    expected = json.loads(output)
    before = file_snapshot(root)
    process = module_process(tmp_path, ["status", "--data-root", str(root)])
    output, error = process.communicate(timeout=60)
    assert process.returncode == 0 and json.loads(output) == expected, output + error
    assert file_snapshot(root) == before


def test_cli_environment_dependency_is_lazy_and_constructed_once(monkeypatch):
    from types import ModuleType
    module = ModuleType("torment_service.embeddings")
    calls = []
    dependency = DeterministicTestEmbedder()
    def factory():
        calls.append(1)
        return dependency
    module.build_embedder_from_env = factory
    monkeypatch.setitem(sys.modules, "torment_service.embeddings", module)
    lazy = cli._EnvironmentEmbedder()
    assert calls == []
    assert (lazy.provider, lazy.model, lazy.dim) == (dependency.provider, dependency.model, dependency.dim)
    assert calls == [1] and dependency.calls == []


CHILD_COMMAND = r'''
import sys,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tests'))
from torment_service.native_genesis import main
from test_native_genesis_onboarding import DeterministicTestEmbedder
def fault(stage):
    if stage==sys.argv[1]: os._exit(71)
raise SystemExit(main(sys.argv[2:],fault=fault,embedder_factory=DeterministicTestEmbedder))
'''


@pytest.mark.parametrize("stage", ["after-intent-publication", "after-i3", "after-i4", "after-i5", "after-i6", "after-i8"])
def test_exact_cli_command_recovers_cross_phase_process_death(tmp_path, stage):
    root, request, intent_path = inputs(tmp_path, True)
    args = arguments(request, intent_path)
    process = child(CHILD_COMMAND, stage, *args)
    output, error = process.communicate(timeout=60)
    assert process.returncode == 71, output + error
    before = intent_path.read_bytes()
    if stage == "after-intent-publication": assert not root.exists()
    process = child(CHILD_COMMAND, "no-fault", *args)
    output, error = process.communicate(timeout=60)
    assert process.returncode == 0, output + error
    result = json.loads(output)
    intent = onboarding.read_intent_plan(intent_path)
    assert intent_path.read_bytes() == before and result["core_id"] == intent.payload()["allocations"]["core_id"]
    authority = i7.recover_active_native_genesis(data_root=root)
    assert authority.completion.expanded_intent == intent
    assert authority.completion.character_seed_completion.payload()["seed_eids"] == [0, 1, 2]


@pytest.mark.parametrize("matching", [True, False])
def test_separate_process_concurrent_drivers(tmp_path, matching):
    root, request, intent = inputs(tmp_path)
    second_request, second_intent = request, intent
    if not matching:
        second_request, second_intent = tmp_path / "other-request.json", tmp_path / "other-intent.json"
        value = request_payload(root); value["agent"]["initial_overlay"]["write_threshold"] += .1
        second_request.write_bytes(owner_bytes(value))
    gate = tmp_path / "gate"
    code = CHILD_COMMAND.replace("def fault(stage):", r'''
import time
gate=Path(sys.argv.pop(1))
ready=Path(sys.argv.pop(1))
ready.write_text('ready')
while not gate.exists(): time.sleep(.01)
def fault(stage):''')
    ready = [tmp_path / "ready-a", tmp_path / "ready-b"]
    processes = [child(code, gate, ready[0], "no-fault", *arguments(request, intent)),
                 child(code, gate, ready[1], "no-fault", *arguments(second_request, second_intent))]
    try:
        deadline = time.monotonic() + 30
        while not all(p.exists() for p in ready) and all(p.poll() is None for p in processes) and time.monotonic() < deadline:
            time.sleep(.02)
        assert all(p.exists() for p in ready)
    finally:
        gate.write_text("go")
    outputs = [p.communicate(timeout=60) for p in processes]
    codes = [p.returncode for p in processes]
    assert sorted(codes) == ([0, 0] if matching else [0, 2]), outputs
    results = [json.loads(output) for output, error in outputs]
    if matching: assert results[0] == results[1]
    winner = codes.index(0)
    plan = onboarding.read_intent_plan([intent, second_intent][winner])
    authority = i7.recover_active_native_genesis(data_root=root)
    assert authority.completion.expanded_intent == plan
    with closing(i3._open_readonly(authority.core_database_path)) as connection:
        assert connection.execute("SELECT count(*) FROM maintenance_events").fetchone() == (2,)


@pytest.mark.parametrize("kind", ["request", "intent", "profile"])
def test_operator_artifacts_inside_root_are_refused(tmp_path, kind):
    root, request, intent = inputs(tmp_path)
    root.mkdir()
    profile = None
    if kind == "request":
        inside = root / "request.json"; inside.write_bytes(request.read_bytes()); request = inside
    elif kind == "intent": intent = root / "intent.json"
    else: profile = root / "profile.json"
    before = file_snapshot(root)
    code, result = call(arguments(request, intent, profile=profile), embedder_factory=forbidden_factory)
    assert code == 2 and result["status"] == "CONFLICT" and file_snapshot(root) == before


@pytest.mark.parametrize("kind", ["request", "intent", "profile"])
def test_operator_file_redirects_are_refused(tmp_path, kind):
    root, request, intent = inputs(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    redirected = tmp_path / "redirected"
    if os.name == "nt":
        # Native CMD junction creation only inside this explicit test directory.
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(redirected), str(real)], check=True, capture_output=True)
    else:
        redirected.symlink_to(real, target_is_directory=True)
    profile = None
    if kind == "request":
        (real / "request.json").write_bytes(request.read_bytes()); request = redirected / "request.json"
    elif kind == "intent": intent = redirected / "intent.json"
    else: profile = redirected / "profile.json"
    before = file_snapshot(root)
    assert call(arguments(request, intent, profile=profile), embedder_factory=forbidden_factory)[0] == 2
    assert file_snapshot(root) == before


def test_conflicting_profile_refuses_before_activation_and_secrets_never_echo(tmp_path):
    root, request, intent = inputs(tmp_path, True)
    profile = tmp_path / "profile.json"
    profile.write_bytes(b'{"credential":"DO-NOT-ECHO-THIS"}')
    before = profile.read_bytes()
    code, value = call(arguments(request, intent, profile=profile), embedder_factory=forbidden_factory)
    assert code == 2 and not root.exists() and profile.read_bytes() == before
    assert "DO-NOT-ECHO-THIS" not in json.dumps(value) and "First anchor" not in json.dumps(value)


def test_apply_requires_durably_saved_intent_and_explicit_confirmation(tmp_path):
    root, request, intent_path = inputs(tmp_path)
    request_value = onboarding.read_onboarding_request(request)
    intent = onboarding.plan_native_genesis(request_value)
    with pytest.raises(SubstrateError):
        run_driver(intent, intent_path)
    assert not root.exists()
    args = arguments(request, intent_path)
    args.remove("--confirm-all-offline-conditions")
    assert call(args)[0] == 2 and not root.exists() and not intent_path.exists()


def test_fresh_operator_surfaces_have_no_legacy_or_public_onboarding_calls():
    sources = [Path(cli.__file__), Path(onboarding.__file__)]
    forbidden = {"Workspace", "MemoryGraph", "Fabric", "TormentFabric", "bootstrap_real_root_staging", "RealRootStagingBootstrap",
        "record_root_admission_envelope", "establish_selector_era", "initialize_selector", "create_schema", "create_object", "admit", "plant_seed"}
    for source in sources:
        tree = ast.parse(source.read_text(encoding="utf-8"))
        calls = {getattr(n.func, "id", getattr(n.func, "attr", "")) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        assert not calls & forbidden
    service = Path(cli.__file__).parent
    for name in ("app.py", "mcp_server.py", "__main__.py", "public_runtime.py", "fabric.py"):
        path = service / name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        assert not any((getattr(n, "module", "") or "").split(".")[-1] in {"genesis_onboarding", "native_genesis"}
            or any(alias.name.split(".")[-1] in {"genesis_onboarding", "native_genesis"} for alias in n.names)
            for n in imports), str(path)
