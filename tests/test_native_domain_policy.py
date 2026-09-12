"""Native policy qualification on disposable roots, without model calls."""
from contextlib import contextmanager
import json
from types import SimpleNamespace

import pytest

from torment_service import domain_policies as policies, domain_policy_setup as setup
from torment_service.fabric import TormentFabric, Workspace
from torment_service.public_runtime import (
    NativePublicOperationRefused,
    NativePublicTormentRuntime,
    _read_domain_policies,
)
from torment_service.substrate import genesis_onboarding as onboarding, genesis_recovery as recovery
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.production_native_owner import NativeProductionResourceOwner
from test_h2b_native_genesis_v2 import roster_payload
from test_hivemind_initial_domain_policy import make_active
from test_native_genesis_onboarding import NoEmbeddingDependency, request_payload, run_driver
from test_post_i4_root_v2_production_recovery import _active_root_fixture


UNQUALIFIED = "native public domain policy is unqualified for admitted domain"


def policy_path(root, workspace="workspace"):
    return root / "workspaces" / workspace / "domain_policies.json"


def write_policies(root, values, workspace="workspace"):
    path = policy_path(root, workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"policies": values}), encoding="utf-8")
    return path


def snapshot(path):
    return path.read_bytes(), path.stat().st_mtime_ns


@contextmanager
def native_runtime(root, profile):
    # Real owner, reader, view and preflight; any embedding access is a failure.
    class NoCognitionFabric(TormentFabric):
        def __init__(self):
            self.data_dir = str(root)
            self.kernel = SimpleNamespace(embedder=NoEmbeddingDependency())
            self._legacy_materialization_fence = None

    agreement = resolve_deployment_agreement(data_root=root, effective_profile=profile)
    owner = NativeProductionResourceOwner.from_native_agreement(
        data_root=root, agreement=agreement, effective_profile=profile,
        admission_descriptor_path=None,
    )
    try:
        yield NativePublicTormentRuntime(cognition_fabric=NoCognitionFabric(), native_owner=owner)
    finally:
        owner.close()


def assert_view_refuses_after_restart(root, profile, workspace, agent, monkeypatch):
    for _ in range(2):
        with native_runtime(root, profile) as runtime:
            monkeypatch.setattr(runtime._executor, "execute", lambda request: pytest.fail("reached executor"))
            with pytest.raises(NativePublicOperationRefused, match=f"^{UNQUALIFIED}$"):
                runtime.get_workspace(workspace)
            with pytest.raises(NativePublicOperationRefused, match=f"^{UNQUALIFIED}$"):
                runtime.ingest(workspace, agent, "memory", public_mutation_key="unqualified-write")
            assert runtime._workspace_views == {}


@pytest.mark.parametrize("file_present", [False, True])
def test_all_builtins_without_persisted_entries_use_complete_defaults(tmp_path, file_present):
    path = policy_path(tmp_path)
    if file_present:
        write_policies(tmp_path, {})
    before = snapshot(path) if file_present else None
    result = _read_domain_policies(str(tmp_path), "workspace", tuple(policies.DEFAULT_DOMAIN_POLICIES))
    assert result == policies.DEFAULT_DOMAIN_POLICIES
    assert all(len(policy) == 14 for policy in result.values())
    with pytest.raises(TypeError):
        result["research"]["auto_merge_motifs"] = True
    with pytest.raises(TypeError):
        result["custom"] = {}
    assert (snapshot(path) if path.exists() else None) == before


@pytest.mark.parametrize("domain", ["engineering", "custom"])
def test_complete_persisted_mapping_is_used_wholesale(tmp_path, domain):
    # An existing policy with different values proves no domain-based rewrite.
    expected = dict(policies.DEFAULT_DOMAIN_POLICIES["personal"])
    path = write_policies(tmp_path, {domain: expected})
    before = snapshot(path)
    result = _read_domain_policies(str(tmp_path), "workspace", (domain,))
    assert result == {domain: expected}
    assert result[domain]["auto_merge_motifs"] is True  # Completeness is posture-neutral.
    assert snapshot(path) == before


@pytest.mark.parametrize("domain", ["research", "custom"])
def test_invalid_persisted_policy_never_falls_back_or_fills_fields(tmp_path, domain):
    complete = policies.DEFAULT_DOMAIN_POLICIES["research"]
    invalid = [{}, None, False, [], "policy", {"auto_merge_motifs": False},
               {**complete, "unknown_field": True}]
    for field, value in complete.items():
        invalid.append({key: item for key, item in complete.items() if key != field})
        # bool must not qualify as int, nor int as float or bool.
        wrong_type = True if type(value) is int else 0
        invalid.append({**complete, field: wrong_type})
    invalid.extend({**complete, "motif_entropy_high": value}
                   for value in (float("nan"), float("inf")))
    for value in invalid:
        path = write_policies(tmp_path, {domain: value})
        before = snapshot(path)
        with pytest.raises(NativePublicOperationRefused, match=f"^{UNQUALIFIED}$"):
            _read_domain_policies(str(tmp_path), "workspace", (domain,))
        assert snapshot(path) == before


@pytest.mark.parametrize("raw", [b"{", b"\xff"])
def test_malformed_policy_file_keeps_unreadable_refusal(tmp_path, raw):
    path = write_policies(tmp_path, {})
    path.write_bytes(raw)
    before = snapshot(path)
    with pytest.raises(NativePublicOperationRefused, match="domain policy evidence is unreadable"):
        _read_domain_policies(str(tmp_path), "workspace", ("research",))
    assert snapshot(path) == before


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize("custom", [False, True])
def test_genesis_admission_and_recovery_are_independent_of_native_policy(tmp_path, monkeypatch, version, custom):
    root = tmp_path / "root"
    value = request_payload(root, enabled=False) if version == 1 else roster_payload(root, (False, False))
    domains = ["research", "custom"] if custom else ["research"]
    value["workspace"]["ordered_domains"] = domains
    agents = [value["agent"]] if version == 1 else value["agents"]
    for agent in agents:
        agent["private_motif_domain_id"] = domains[-1]
    agent_id = agents[0]["agent_id"]
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    intent_path = tmp_path / "intent.json"
    intent = onboarding.prepare_intent_plan(request, intent_path=intent_path)
    assert run_driver(intent, intent_path, embedder=NoEmbeddingDependency())["status"] == "NATIVE_ACTIVE"
    authority = recovery.recover_active_native_genesis(data_root=root)
    assert authority.completion.expanded_intent == intent
    profile = authority.completion.qualified_deployment_profile
    assert not policy_path(root).exists()
    if custom:
        assert_view_refuses_after_restart(root, profile, "workspace", agent_id, monkeypatch)
    else:
        with native_runtime(root, profile) as runtime:
            assert runtime.get_workspace("workspace").domain_policies == {
                "research": policies.DEFAULT_DOMAIN_POLICIES["research"]}
            monkeypatch.setattr(runtime._executor, "execute", lambda request: {"reached": request.domain_id})
            assert runtime.ingest("workspace", agent_id, "memory", public_mutation_key="qualified-write") == {
                "reached": "research"}
    assert not policy_path(root).exists()
    assert recovery.recover_active_native_genesis(data_root=root).completion == authority.completion

    expected = {domain: dict(policies.DEFAULT_DOMAIN_POLICIES[
        "research" if domain == "custom" else "engineering"]) for domain in domains}
    path = write_policies(root, expected)
    before = snapshot(path)
    with native_runtime(root, profile) as runtime:
        assert runtime.get_workspace("workspace").domain_policies == expected
    assert snapshot(path) == before

    write_policies(root, {**expected, "research": {"auto_merge_motifs": False}})
    before = snapshot(path)
    assert_view_refuses_after_restart(root, profile, "workspace", agent_id, monkeypatch)
    assert snapshot(path) == before
    assert recovery.recover_active_native_genesis(data_root=root).completion == authority.completion
    assert run_driver(intent, intent_path, embedder=NoEmbeddingDependency())["status"] == "NATIVE_ACTIVE"
    assert snapshot(path) == before


def test_migrated_custom_domain_retains_complete_historical_policy(tmp_path, monkeypatch):
    root, profile, _ = _active_root_fixture(tmp_path)
    path = policy_path(root, "ws-one")
    # Exercise the unchanged historical writer without constructing legacy
    # graphs or an embedding model. Its research copy is persisted evidence.
    historical = Workspace._load_or_init_domain_policies(SimpleNamespace(
        domain_policies_path=str(path), domains=["domain-one"]))
    assert historical == {"domain-one": policies.DEFAULT_DOMAIN_POLICIES["research"]}
    before = snapshot(path)
    monkeypatch.setitem(policies.DEFAULT_DOMAIN_POLICIES, "research",
                        dict(policies.DEFAULT_DOMAIN_POLICIES["engineering"]))
    for _ in range(2):
        with native_runtime(root, profile) as runtime:
            assert runtime.get_workspace("ws-one").domain_policies == historical
    assert snapshot(path) == before
    path.unlink()
    assert_view_refuses_after_restart(root, profile, "ws-one", "agent-one", monkeypatch)
    assert not path.exists()


def test_current_hivemind_setup_qualifies_native_view(tmp_path):
    root, kwargs = make_active(tmp_path)
    setup.prepare_policy_setup(**kwargs)
    setup.execute_policy_setup(**kwargs)
    path = policy_path(root)
    before = snapshot(path)
    profile = recovery.recover_active_native_genesis(data_root=root).completion.qualified_deployment_profile
    with native_runtime(root, profile) as runtime:
        assert runtime.get_workspace("workspace").domain_policies == json.loads(path.read_bytes())["policies"]
    assert snapshot(path) == before
