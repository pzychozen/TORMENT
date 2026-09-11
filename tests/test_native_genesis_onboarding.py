"""I9 qualification: only disposable roots, explicit confirmation and test vectors."""
from contextlib import closing
from dataclasses import replace
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
from uuid import UUID

import numpy as np
import pytest

from torment_service.external_owner_json import owner_bytes
from torment_service.substrate import genesis_onboarding as onboarding
from torment_service.substrate import genesis_contracts as g
from torment_service.substrate import genesis_administration as i3
from torment_service.substrate import genesis_character_administration as i4
from torment_service.substrate import genesis_recovery as i7
from torment_service.substrate import deployment_selector as selector
from torment_service.substrate.errors import SubstrateError
from torment_service.substrate.genesis_fence import canonical_genesis_root, read_genesis_operation_record, read_genesis_fence
from torment_service.substrate.production_native_owner import NativeProductionResourceOwner
from test_native_genesis_contracts import intent_payload
from test_native_genesis_completion import file_snapshot
from test_native_genesis_administration import child


class DeterministicTestEmbedder:
    provider, model, dim = "fixture-provider", "fixture-model", 3

    def __init__(self):
        self.calls = []

    def embed(self, text):
        self.calls.append(text)
        return np.asarray((1, 0, 0), dtype=np.float32)


class NoEmbeddingDependency:
    def __getattr__(self, name):
        pytest.fail("completed recovery must not touch embedding dependency")


def request_payload(root, enabled=False):
    value = intent_payload(enabled)
    value["data_root_identity"] = str(canonical_genesis_root(root))
    if enabled:
        value["character"]["definition"]["seed_text"] = "First anchor. Second anchor. Third anchor."
        value["agent"]["identity_seed"]["seed_text"] = value["character"]["definition"]["seed_text"]
    return dict(contract=onboarding.NativeGenesisOnboardingRequest.CONTRACT, version=1,
        **{name: value[name] for name in onboarding._DECLARATION_FIELDS.split()})


def confirmation():
    return onboarding.LocalOperatorConfirmation(True, True, True, True, True, True, "http://127.0.0.1:8787")


def planned(tmp_path, enabled=False):
    root, path = tmp_path / "root", tmp_path / "intent.json"
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(request_payload(root, enabled))
    intent = onboarding.prepare_intent_plan(request, intent_path=path)
    return root, request, path, intent


def run_driver(intent, path, **kwargs):
    kwargs.setdefault("observer", confirmation())
    return onboarding.run_native_genesis_onboarding(intent=intent, intent_path=path,
        operator_attestation="Local operator confirms every offline condition for this disposable root.",
        issuer_reference="i9-test-operator", **kwargs)


@pytest.mark.parametrize("enabled", [False, True])
def test_empty_root_through_driver_and_active_replay_without_embedding(tmp_path, enabled):
    root, request, path, intent = planned(tmp_path, enabled)
    assert not root.exists()
    embedder = DeterministicTestEmbedder()
    profile = tmp_path / "profile.json"
    result = run_driver(intent, path, embedder=embedder, profile_out=profile)
    assert result["status"] == "NATIVE_ACTIVE" and result["selector_generation"] == 2
    assert read_genesis_fence(data_root=root).value == "NATIVE_AUTHORITY_WINS"
    authority = i7.recover_active_native_genesis(data_root=root)
    assert authority.completion.expanded_intent == intent
    assert authority.core_inspection.core_role == "ACTIVE_CORE"
    assert authority.core_inspection.deployment_state.value == "NATIVE_ACTIVE"
    assert authority.selector_state.deployment_state.value == "NATIVE_ACTIVE"
    assert authority.completion.qualified_profile_payload() == result["qualified_deployment_profile"]
    assert len(json.loads(profile.read_bytes())) == 7
    assert json.loads(profile.read_bytes()) == result["qualified_deployment_profile"]
    agreement = selector.resolve_deployment_agreement(data_root=root, effective_profile=authority.completion.qualified_deployment_profile)
    assert agreement.mode.value == "NATIVE_AGREEMENT"
    owner = NativeProductionResourceOwner.from_native_agreement(data_root=root, agreement=agreement,
        effective_profile=authority.completion.qualified_deployment_profile, admission_descriptor_path=None)
    runtime = owner._recover_active_runtime(workspace_id="workspace")
    assert len(runtime.scopes) == 3 and runtime.lookup_private("agent").memory_runtime_scope.agent_id == "agent"
    owner.close()
    if enabled:
        concepts = i4._split_seed_text(request.payload()["character"]["definition"]["seed_text"])
        assert embedder.calls == list(concepts)
        evidence = authority.completion.character_seed_completion.payload()
        assert evidence["seed_eids"] == list(range(len(concepts)))
        external = json.loads((root / i4._owner_paths(intent)[-1]).read_bytes())
        assert external["seed_eids"] == evidence["seed_eids"] and external["seed_motif_id"] == evidence["seed_motif_id"]
    else:
        assert not embedder.calls
    def forbidden(*args):
        pytest.fail("active replay must not observe writers")
    before, external_before = file_snapshot(root), profile.read_bytes()
    assert run_driver(intent, path, embedder=NoEmbeddingDependency(), observer=forbidden, profile_out=profile) == result
    assert file_snapshot(root) == before and profile.read_bytes() == external_before


def test_planning_generates_once_and_exact_replay_never_calls_factories(tmp_path):
    root = tmp_path / "root"
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(request_payload(root, True))
    count, times = [], []
    def identifier():
        count.append(1)
        return UUID(int=len(count), version=4)
    def timestamp():
        times.append(1)
        return 1234
    path = tmp_path / "intent.json"
    first = onboarding.prepare_intent_plan(request, intent_path=path, id_factory=identifier, time_factory=timestamp)
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert len(count) == 26 and times == [1]
    def forbidden():
        pytest.fail("generated-once fact factory called during replay")
    assert onboarding.prepare_intent_plan(request, intent_path=path, id_factory=forbidden, time_factory=forbidden) == first
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    assert first.operation_key == request.operation_key
    assert len(set(first.payload()["allocations"]["namespace_keys"].values())) == 20
    assert first.payload()["creation_facts"] == dict(workspace_created_ts=1234, identity_created_ts=1234, character_created_ts=1234)
    changed = request.payload(); changed["agent"]["initial_overlay"]["write_threshold"] += .1
    second = onboarding.NativeGenesisOnboardingRequest.from_payload(changed)
    assert second.operation_key != request.operation_key
    with pytest.raises(SubstrateError):
        onboarding.prepare_intent_plan(second, intent_path=path, id_factory=forbidden, time_factory=forbidden)
    assert not root.exists() and (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_operator_request_cannot_be_used_as_execution_authority(tmp_path):
    root, request, path, intent = planned(tmp_path)
    with pytest.raises(SubstrateError, match="typed expanded GenesisIntent"):
        run_driver(request, path)
    assert not root.exists()


@pytest.mark.parametrize("bad", ["extra", "operation-key", "allocations", "creation-facts", "version-bool", "relative-root",
    "workspace-path", "agent-path", "domain-path", "duplicate-domains", "seed-path", "character-shape", "character-tuning",
    "overlay-missing", "overlay-bool", "identity-extra", "profile-default", "profile-lane", "lane-dtype", "nonfinite"])
def test_request_contract_refuses_unqualified_fields_and_shapes(tmp_path, bad):
    value = request_payload(tmp_path / "root", True)
    if bad in ("extra", "operation-key", "allocations", "creation-facts"):
        value[bad.replace("-", "_")] = {}
    elif bad == "version-bool": value["version"] = True
    elif bad == "relative-root": value["data_root_identity"] = "relative-root"
    elif bad == "workspace-path": value["workspace"]["workspace_id"] = "../workspace"
    elif bad == "agent-path": value["agent"]["agent_id"] = "CON"
    elif bad == "domain-path": value["workspace"]["ordered_domains"][0] = "../domain"
    elif bad == "duplicate-domains": value["workspace"]["ordered_domains"] *= 2
    elif bad == "seed-path": value["character"]["definition"]["seed_id"] = "../seed"
    elif bad == "character-shape": value["character"]["seed_eids"] = [0]
    elif bad == "character-tuning": value["character"]["definition"]["gravity"] = .5
    elif bad == "overlay-missing": value["agent"]["initial_overlay"].pop("write_threshold")
    elif bad == "overlay-bool": value["agent"]["initial_overlay"]["write_threshold"] = True
    elif bad == "identity-extra": value["agent"]["identity_seed"]["created_ts"] = 1
    elif bad == "profile-default": value["profile_choice"]["compression_enabled"] = True
    elif bad == "profile-lane": value["profile_choice"]["representation_dimension"] = 4
    elif bad == "lane-dtype": value["representation_lane"]["dtype"] = "float64"
    elif bad == "nonfinite": value["agent"]["initial_overlay"]["write_threshold"] = float("nan")
    with pytest.raises(SubstrateError):
        onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    assert not (tmp_path / "root").exists()


def test_duplicate_key_json_refuses_and_tuning_is_preserved_exactly(tmp_path):
    value = request_payload(tmp_path / "root", True)
    raw = json.dumps(value).replace('"drift_window_steps": 500', '"drift_window_steps": 500, "drift_window_steps": 501')
    with pytest.raises(SubstrateError):
        onboarding.NativeGenesisOnboardingRequest(raw)
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(value)
    planned_intent = onboarding.plan_native_genesis(request)
    assert {name: planned_intent.payload()[name] for name in onboarding._DECLARATION_FIELDS.split()} == {
        name: value[name] for name in onboarding._DECLARATION_FIELDS.split()}


@pytest.mark.parametrize("field", ["provider", "model", "dim"])
def test_embedder_mismatch_refuses_before_any_root_mutation(tmp_path, field):
    root, request, path, intent = planned(tmp_path, True)
    dependency = DeterministicTestEmbedder()
    setattr(dependency, field, 4 if field == "dim" else "foreign")
    with pytest.raises(SubstrateError, match="embedder differs"):
        run_driver(intent, path, embedder=dependency)
    assert not root.exists() and not dependency.calls


@pytest.mark.parametrize("condition", ["service_stopped", "mcp_stopped", "direct_tools_stopped", "fabric_hosts_stopped", "root_jobs_absent", "public_listener_absent"])
def test_every_offline_confirmation_is_explicit(condition):
    with pytest.raises(SubstrateError):
        replace(confirmation(), **{condition: False})


def test_operator_evidence_truthfully_names_human_confirmation(tmp_path):
    _, _, _, intent = planned(tmp_path)
    observed = confirmation()(canonical_genesis_root(intent.data_root_identity), intent)
    assert {v.writer_class for v in observed.writers} == set(i3.RootWriterClass)
    assert all(v.observation_mechanism == "LOCAL_HUMAN_OPERATOR_CONFIRMATION_V1" for v in observed.writers + observed.listeners)
    assert observed.listeners[0].listener_identity == "http://127.0.0.1:8787"
    assert observed.writers[-1].result is i3.WriterObservationResult.ABSENT


class BoundaryLoss(BaseException):
    pass


def stop_after(stage):
    def fault(name):
        if name == stage:
            raise BoundaryLoss(stage)
    return fault


@pytest.mark.parametrize("state", ["preparing", "active-with-admin", "active-without-admin"])
def test_lost_intent_file_recovers_exact_existing_allocations(tmp_path, state):
    root, request, path, intent = planned(tmp_path)
    original = path.read_bytes()
    if state == "preparing":
        with pytest.raises(BoundaryLoss): run_driver(intent, path, fault=stop_after("after-i3"))
    else:
        run_driver(intent, path)
        if state == "active-without-admin":
            (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).unlink()
    path.unlink()
    before = file_snapshot(root)
    def forbidden():
        pytest.fail("lost intent recovery must not regenerate facts")
    assert onboarding.prepare_intent_plan(request, intent_path=path, id_factory=forbidden, time_factory=forbidden) == intent
    assert path.read_bytes() == original and file_snapshot(root) == before
    run_driver(intent, path, embedder=NoEmbeddingDependency())
    if state == "active-without-admin":
        assert not (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).exists()


@pytest.mark.parametrize("stage", ["after-i3", "after-i4", "after-i5", "after-i6", "after-i8"])
def test_driver_boundary_replay_preserves_ids_and_does_not_replant(tmp_path, stage):
    root, request, path, intent = planned(tmp_path, True)
    embedder = DeterministicTestEmbedder()
    original = path.read_bytes()
    with pytest.raises(BoundaryLoss):
        run_driver(intent, path, embedder=embedder, fault=stop_after(stage))
    first = list(embedder.calls)
    result = run_driver(intent, path, embedder=embedder)
    assert result["core_id"] == intent.payload()["allocations"]["core_id"]
    assert path.read_bytes() == original
    assert embedder.calls == i4._split_seed_text(request.payload()["character"]["definition"]["seed_text"])
    if stage != "after-i3": assert first == embedder.calls


def test_committed_character_recovery_does_not_construct_dependency(tmp_path):
    root, request, path, intent = planned(tmp_path, True)
    with pytest.raises(BoundaryLoss):
        run_driver(intent, path, embedder=DeterministicTestEmbedder(), fault=stop_after("after-i4"))
    assert onboarding.onboarding_needs_embedding(intent) is False
    assert run_driver(intent, path, embedder=NoEmbeddingDependency())["status"] == "NATIVE_ACTIVE"


def test_active_native_authority_leaves_stale_admin_checkpoint_untouched(tmp_path):
    root, request, path, intent = planned(tmp_path)
    with pytest.raises(BoundaryLoss): run_driver(intent, path, fault=stop_after("after-i6"))
    with pytest.raises(BoundaryLoss):
        onboarding.i8.activate_genesis(data_root=root, intent=intent, observer=confirmation(),
            operator_attestation="Offline disposable root.", issuer_reference="i9-test-operator", fault=stop_after("after-selector-activation"))
    assert read_genesis_operation_record(data_root=root).administrative_phase.value == "CORE_ACTIVATED"
    before = file_snapshot(root)
    def forbidden(*args): pytest.fail("active recovery must not ask for a new observation")
    assert run_driver(intent, path, observer=forbidden, embedder=NoEmbeddingDependency())["status"] == "NATIVE_ACTIVE"
    assert file_snapshot(root) == before


@pytest.mark.parametrize("state", ["NOT_STARTED", "PREPARING", "PREPARATION_SEALED", "CORE_ACTIVATED_SELECTOR_PENDING", "NATIVE_ACTIVE", "CONFLICT"])
def test_status_has_no_writes_or_model_dependency(tmp_path, state):
    root, request, path, intent = planned(tmp_path)
    if state == "CONFLICT":
        root.mkdir(); (root / "legacy.db").write_bytes(b"unsupported existing installation")
    elif state == "PREPARING":
        with pytest.raises(BoundaryLoss): run_driver(intent, path, fault=stop_after("after-i3"))
    elif state in ("PREPARATION_SEALED", "CORE_ACTIVATED_SELECTOR_PENDING"):
        with pytest.raises(BoundaryLoss): run_driver(intent, path, fault=stop_after("after-i6"))
        if state == "CORE_ACTIVATED_SELECTOR_PENDING":
            with pytest.raises(BoundaryLoss):
                onboarding.i8.activate_genesis(data_root=root, intent=intent, observer=confirmation(),
                    operator_attestation="Offline disposable root.", issuer_reference="i9-test-operator", fault=stop_after("after-core-activation"))
    elif state == "NATIVE_ACTIVE": run_driver(intent, path)
    before = file_snapshot(root)
    assert onboarding.native_genesis_status(data_root=root, intent=intent)["status"] == state
    assert file_snapshot(root) == before


@pytest.mark.parametrize("family", ["historical-v1", "root-v2"])
def test_existing_active_installations_are_never_adopted(tmp_path, family):
    if family == "historical-v1":
        from test_b5_a3_production_native_resource_owner import _active_fixture
        root, *_ = _active_fixture(tmp_path)
    else:
        from test_native_genesis_recovery import root_v2_fixture
        root, *_ = root_v2_fixture(tmp_path)
    request = onboarding.NativeGenesisOnboardingRequest.from_payload(request_payload(root))
    before = file_snapshot(root)
    with pytest.raises(SubstrateError):
        onboarding.prepare_intent_plan(request, intent_path=tmp_path / "foreign-intent.json")
    assert file_snapshot(root) == before
