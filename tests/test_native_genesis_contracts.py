"""I1 pure contracts: synthetic values only, no native core or owner calls."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import builtins
import json
import math
import sqlite3
from uuid import UUID

import pytest

from torment_service.substrate import genesis_contracts as g
from torment_service.substrate.deployment_types import (
    AdmissionCompletionWitness, NativeGenesisCompletionWitness,
    QualifiedDeploymentProfile, RootAdmissionCompletionWitness,
    canonical_json, completion_witness_from_payload, digest_mapping,
)
from torment_service.substrate.errors import DeploymentAuthorityError
from torment_service.substrate.schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR


def uid(index):
    return str(UUID(int=index, version=4))


def intent_payload(enabled=False):
    lane = dict(provider="fixture-provider", model="fixture-model", dimension=3,
                representation_class="COMPAT_EMBEDDING", generation=1,
                derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32")
    seed = dict(core_traits=["analytical"], priority_weights={"facts": 0.8},
                coupling_mode="read_only", coupling_strength=0.25, seed_text="", seed_id="")
    character = {"mode": "DISABLED"}
    if enabled:
        definition = dict(seed_id="seed-one", character_name="Character One", seed_text="Stable identity.",
                          owner_agent_id="agent", drift_window_steps=500, drift_correction_threshold=0.35,
                          drift_gravity_strength=0.12, core_half_life=3650.0, relational_half_life=30.0,
                          situational_half_life=7.0, core_weight=0.5, derived_weight=0.42,
                          relational_weight=0.35, situational_weight=0.15, version="1.0.0")
        character = dict(mode="ENABLED", definition=definition)
        seed.update({k: definition[k] for k in ("seed_id", "seed_text", "character_name")})
    plans = []
    namespace_keys = {uid(4): "root-profile-identity"}
    for i, (kind, qualifier) in enumerate((("PRIVATE", "agent"), ("SHARED", "alpha"), ("SHARED", "zeta"))):
        ids = {key: uid(10 + i * 10 + n) for n, key in enumerate(g.SCOPE_PLAN_UUID_FIELDS)}
        namespace_keys.update({value: f"scope-{i}-{key}" for key, value in ids.items() if key != "target_semantic_scope_id"})
        plans.append(dict(
            scope_key=dict(workspace_id="workspace", scope_kind=kind,
                           agent_id=qualifier if kind == "PRIVATE" else None,
                           domain_id=qualifier if kind == "SHARED" else None),
            scope_plan={**ids, "workspace_id": "workspace", "scope_kind": "PRIVATE_AGENT" if kind == "PRIVATE" else "SHARED_DOMAIN",
                        "qualifier": qualifier, "motif_domain_id": "zeta" if kind == "PRIVATE" else qualifier},
            representation_lane=deepcopy(lane),
        ))
    return dict(
        contract=g.GenesisIntent.CONTRACT, version=1, origin="NATIVE_GENESIS", operation_key="genesis-fixture",
        data_root_identity="synthetic-root-identity", workspace=dict(workspace_id="workspace", ordered_domains=["zeta", "alpha"]),
        agent=dict(agent_id="agent", identity_seed=seed, initial_overlay={key: 0.5 for key in g.INITIAL_OVERLAY_KEYS.split()},
                   private_motif_domain_id="zeta"), character=character,
        profile_choice=dict(compression_enabled=False, deep_memory_enabled=False,
                            representation_provider=lane["provider"], representation_model=lane["model"], representation_dimension=3),
        representation_lane=lane,
        allocations=dict(core_id=uid(1), core_relative_path="genesis.db", root_profile_generation=1,
                         root_profile_object_id=uid(2), root_profile_semantic_scope_id=uid(3),
                         root_profile_identity_namespace_id=uid(4), namespace_keys=namespace_keys, runtime_scope_plans=plans),
        creation_facts=dict(workspace_created_ts=10, identity_created_ts=11, character_created_ts=12 if enabled else None),
    )


def start_payload(kind="EMPTY_ROOT", entries=None, operation=None):
    return dict(classification=kind, data_root_identity="synthetic-root-identity", observed_at_ns=100,
                observed_entries=[] if entries is None else entries, matching_operation_key=operation)


def quiescence():
    return g.GenesisQuiescenceObservation.from_payload(dict(
        data_root_identity="synthetic-root-identity", operation_key="genesis-fixture", observed_at_ns=200,
        operator_attestation="All writers stopped for this synthetic observation.", issuer_reference="fixture-operator",
        observations={"processes": [], "listeners": [], "writers_stopped": True},
    ))


def completion_payload(enabled=False):
    intent = g.GenesisIntent.from_payload(intent_payload(enabled))
    allocations = intent.payload()["allocations"]
    plans = intent.runtime_plans
    projection = intent.external_owner_projection()
    profile = QualifiedDeploymentProfile(False, False, "fixture-provider", "fixture-model", 3,
                                         g.runtime_plan_digest(plans), digest_mapping(projection))
    root_profile = g.GenesisRootProfileReference.from_payload(dict(
        core_id=uid(1), profile_generation=1, profile_object_id=uid(2), profile_revision_id=uid(100),
        profile_revision_ordinal=1, profile_semantic_scope_id=uid(3),
    ))
    memberships = tuple(g.GenesisMembershipReference.from_payload(dict(
        scope_key=plan.payload()["scope_key"], relationship_id=uid(110 + i), relationship_revision_id=uid(120 + i),
        relationship_revision_ordinal=1, lifecycle="ACTIVE",
        membership_witness=dict(witness_id=f"membership-{i}", witness_digest="a" * 64,
                                issuer_reference="fixture-operator", provenance_kind="QUALIFICATION_TEST"),
    )) for i, plan in enumerate(plans))
    seed = {"mode": "DISABLED"}
    if enabled:
        seed = dict(mode="ENABLED", status="COMPLETED", definition_digest=digest_mapping(intent.payload()["character"]["definition"]),
                    source_operation_key="native-seed-source", source_intent_digest="b" * 64, result_digest="c" * 64,
                    seed_eids=[1, 2], seed_motif_id="seed-motif", representation_ids=[uid(150), uid(151)])
    value = dict(
        contract=NativeGenesisCompletionWitness.CONTRACT, version=1, origin="NATIVE_GENESIS",
        data_root_identity=intent.data_root_identity, operation_key=intent.operation_key, intent_digest=intent.digest,
        expanded_intent=intent.payload(), accepted_start_observation=start_payload(), native_core_id=uid(1),
        core_relative_path=allocations["core_relative_path"], schema_id=SCHEMA_ID, schema_major=SCHEMA_MAJOR, schema_minor=SCHEMA_MINOR,
        qualified_deployment_profile={field.name: getattr(profile, field.name) for field in fields(profile)},
        qualified_deployment_profile_digest=profile.digest, representation_lane=intent.payload()["representation_lane"],
        root_profile=root_profile.payload(), runtime_scope_plans=[p.payload() for p in plans], runtime_plan_digest=g.runtime_plan_digest(plans),
        external_owner_projection=projection, external_owner_closure_digest=digest_mapping(projection), character_seed_completion=seed,
        initial_memberships=[m.payload() for m in memberships],
        initial_membership_closure_digest=g.initial_membership_closure_digest(root_profile, plans, memberships),
        quiescence_evidence_digest=digest_mapping({"quiescence_observations": [quiescence().payload()]}),
    )
    value["preparation_result_digest"] = digest_mapping(value)
    return value


def record(phase=g.GenesisAdministrativePhase.PREPARING):
    intent = g.GenesisIntent.from_payload(intent_payload())
    early = phase is g.GenesisAdministrativePhase.PREPARING
    activated = phase in (g.GenesisAdministrativePhase.CORE_ACTIVATED, g.GenesisAdministrativePhase.COMPLETED)
    return g.GenesisOperationRecord(
        intent, intent.digest, g.GenesisAcceptedStart.from_payload(start_payload()), phase, 1, (),
        () if early else (quiescence(),),
        None if early else NativeGenesisCompletionWitness.from_payload(completion_payload()),
        (g.GenesisEvidenceReference.from_payload(dict(owner="native-activation", operation_key="activate", result_digest="d" * 64)),) if activated else (),
    )


def change(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


@pytest.mark.parametrize("enabled", [False, True])
def test_intent_round_trip_is_expanded_immutable_and_ordered(enabled):
    source = intent_payload(enabled)
    intent = g.GenesisIntent.from_payload(source)
    assert intent.payload() == source
    assert intent.payload()["workspace"]["ordered_domains"] == ["zeta", "alpha"]
    assert g.GenesisIntent.from_payload(dict(reversed(list(source.items())))) == intent
    assert intent.digest == digest_mapping(source)
    source["agent"]["initial_overlay"]["decay_scale"] = 999
    intent.payload()["agent"]["initial_overlay"]["decay_scale"] = 888
    assert intent.payload()["agent"]["initial_overlay"]["decay_scale"] == 0.5
    with pytest.raises(FrozenInstanceError):
        intent._canonical_payload = "{}"


@pytest.mark.parametrize("path,value", [
    (("contract",), "UNKNOWN"), (("version",), True), (("version",), 2), (("origin",), "MIGRATION"),
    (("operation_key",), ""), (("operation_key",), " " * 3), (("operation_key",), "x" * 161),
    (("workspace", "ordered_domains"), []), (("workspace", "ordered_domains"), ["zeta", "zeta"]),
    (("agent", "private_motif_domain_id"), "undeclared"), (("workspace", "workspace_id"), "../workspace"),
    (("workspace", "workspace_id"), "CON"), (("workspace", "workspace_id"), "space "),
    (("representation_lane", "dimension"), 0), (("representation_lane", "dimension"), True),
    (("representation_lane", "generation"), True), (("representation_lane", "dtype"), "float64"),
    (("profile_choice", "representation_dimension"), -1), (("profile_choice", "representation_dimension"), True),
    (("profile_choice", "compression_enabled"), True), (("profile_choice", "deep_memory_enabled"), True),
    (("profile_choice", "compression_enabled"), 0), (("profile_choice", "representation_model"), "different"),
    (("agent", "initial_overlay", "decay_scale"), math.nan), (("agent", "identity_seed", "coupling_strength"), math.inf),
    (("agent", "identity_seed", "seed_text"), "enabled unexpectedly"), (("character",), {"mode": "UNKNOWN"}),
    (("creation_facts", "character_created_ts"), 1), (("allocations", "root_profile_generation"), True),
    (("allocations", "core_relative_path"), "../escape.db"), (("allocations", "core_id"), uid(2)),
    (("allocations", "namespace_keys"), {}), (("allocations", "runtime_scope_plans"), []),
    (("creation_facts", "identity_created_ts"), True),
])
def test_intent_refuses_invalid_or_unexpanded_inputs(path, value):
    source = intent_payload()
    change(source, path, value)
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload(source)


@pytest.mark.parametrize("path", [
    ("agent", "identity_seed", "coupling_strength"), ("agent", "initial_overlay", "decay_scale"),
    ("creation_facts", "workspace_created_ts"), ("representation_lane", "encoding_id"),
])
def test_missing_expanded_values_never_default(path):
    source = intent_payload()
    parent = source
    for key in path[:-1]:
        parent = parent[key]
    del parent[path[-1]]
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload(source)


@pytest.mark.parametrize("field", ["membership_relationship_id", "seed_eids", "profile_digest", "completion_digest", "activation_receipt", "legacy_manifest"])
def test_intent_forbids_future_outputs(field):
    source = intent_payload()
    source[field] = "unowned"
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload(source)


@pytest.mark.parametrize("path,value", [
    (("character", "definition", "owner_agent_id"), "other"),
    (("character", "definition", "seed_id"), "other"),
    (("character", "definition", "core_weight"), math.inf),
    (("character", "definition", "drift_window_steps"), True),
    (("character", "definition", "seed_eids"), [1]),
    (("agent", "identity_seed", "character_name"), "other"),
    (("character", "mode"), "DISABLED"),
])
def test_character_enabled_consistency(path, value):
    source = intent_payload(True)
    change(source, path, value)
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload(source)


def test_exact_id_spelling_retains_case_and_unicode_collision_semantics():
    source = intent_payload()
    source["workspace"]["workspace_id"] = "Workspace-e\u0301"
    for plan in source["allocations"]["runtime_scope_plans"]:
        plan["scope_key"]["workspace_id"] = source["workspace"]["workspace_id"]
        plan["scope_plan"]["workspace_id"] = source["workspace"]["workspace_id"]
    first = g.GenesisIntent.from_payload(source)
    assert first.payload()["workspace"]["workspace_id"] == "Workspace-e\u0301"
    other = json.loads(json.dumps(source).replace("Workspace-e\\u0301", "workspace-\\u00e9"))
    assert g.GenesisIntent.from_payload(other).digest != first.digest


def test_strict_json_rejects_duplicate_keys_nonfinite_cycles_and_nonstring_keys():
    source = intent_payload()
    duplicate = json.dumps(source).replace('"version": 1', '"version": 1, "version": 1', 1)
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent(duplicate)
    source["cycle"] = source
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload(source)
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisIntent.from_payload({1: "not a JSON object key"})


@pytest.mark.parametrize("kind,entries,key", [
    ("ABSENT_ROOT", [], None), ("EMPTY_ROOT", [], None),
    ("ALLOWED_NON_AUTHORITATIVE_ROOT_FILES", ["README.md", ".gitkeep"], None),
    ("PRE_INTENT_GENESIS_CONTROL_RESIDUE", list(g.GenesisAcceptedStart.CONTROL_ENTRIES), None),
    ("PRE_INTENT_GENESIS_CONTROL_RESIDUE", ["."], None),
    ("MATCHING_GENESIS_RECOVERY_STATE", [], "genesis-fixture"),
])
def test_accepted_start_distinctions(kind, entries, key):
    source = start_payload(kind, entries, key)
    result = g.GenesisAcceptedStart.from_payload(source)
    assert result.payload() == source
    result.require_intent(g.GenesisIntent.from_payload(intent_payload()))
    assert g.PRE_INTENT_LOCK_RESIDUE_IS_AUTHORITY is False


@pytest.mark.parametrize("kind,entries,key", [
    ("UNKNOWN", [], None), ("EMPTY_ROOT", ["README.md"], None),
    ("ABSENT_ROOT", [], "operation"), ("ALLOWED_NON_AUTHORITATIVE_ROOT_FILES", ["dir/README.md"], None),
    ("ALLOWED_NON_AUTHORITATIVE_ROOT_FILES", [], None),
    ("PRE_INTENT_GENESIS_CONTROL_RESIDUE", ["substrate/deployment/root-onboarding.lock"], None),
    ("PRE_INTENT_GENESIS_CONTROL_RESIDUE", [".", "unknown"], None),
    ("MATCHING_GENESIS_RECOVERY_STATE", [], None),
])
def test_accepted_start_refusals(kind, entries, key):
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisAcceptedStart.from_payload(start_payload(kind, entries, key))


@pytest.mark.parametrize("phase", list(g.GenesisAdministrativePhase))
def test_record_phase_dependent_round_trip_and_non_authority(phase):
    result = record(phase)
    assert g.GenesisOperationRecord.from_payload(result.payload()) == result
    assert result.digest == digest_mapping(result.payload())
    assert not hasattr(result, "deployment_state")
    assert not hasattr(result, "deployment_authority")
    assert not hasattr(result, "membership_authority")
    assert g.GENESIS_OPERATION_RECORD_IS_DEPLOYMENT_AUTHORITY is False
    assert g.GENESIS_OPERATION_RECORD_IS_MEMBERSHIP_AUTHORITY is False
    assert g.GENESIS_OPERATION_RECORD_IS_EXTERNAL_IDENTITY_AUTHORITY is False


@pytest.mark.parametrize("field,value", [
    ("phase_revision", 0), ("phase_revision", True), ("phase_revision", 1.5),
    ("intent_digest", "0" * 64), ("administrative_phase", "COMPLETED"),
    ("child_operation_references", []),
])
def test_record_refuses_malformed_typed_fields(field, value):
    with pytest.raises(DeploymentAuthorityError):
        replace(record(), **{field: value})


def test_record_refuses_missing_late_fields_and_early_output_claims():
    sealed = record(g.GenesisAdministrativePhase.PREPARATION_SEALED)
    for changes in (dict(sealed_completion_payload=None), dict(quiescence_observations=()),
                    dict(administrative_phase=g.GenesisAdministrativePhase.COMPLETED),
                    dict(administrative_phase=g.GenesisAdministrativePhase.PREPARING)):
        with pytest.raises(DeploymentAuthorityError):
            replace(sealed, **changes)
    source = record().payload()
    source["deployment_authority"] = "NATIVE_ACTIVE"
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisOperationRecord.from_payload(source)
    del source["deployment_authority"]
    source["version"] = True
    with pytest.raises(DeploymentAuthorityError):
        g.GenesisOperationRecord.from_payload(source)


def test_activated_record_may_release_completion_cache_to_native_owner():
    completed = replace(record(g.GenesisAdministrativePhase.COMPLETED), sealed_completion_payload=None)
    assert g.GenesisOperationRecord.from_payload(completed.payload()) == completed


def test_record_refuses_conflicting_child_results_for_one_owner_operation():
    refs = tuple(g.GenesisEvidenceReference.from_payload(dict(owner="native-owner", operation_key="child", result_digest=d * 64))
                 for d in ("a", "b"))
    with pytest.raises(DeploymentAuthorityError):
        replace(record(), child_operation_references=refs)


@pytest.mark.parametrize("enabled", [False, True])
def test_fresh_completion_round_trip_profile_and_common_properties(enabled):
    source = completion_payload(enabled)
    completion = completion_witness_from_payload(source)
    assert type(completion) is NativeGenesisCompletionWitness
    assert completion.payload() == source
    assert NativeGenesisCompletionWitness.from_payload(json.loads(canonical_json(source))) == completion
    assert completion.digest == digest_mapping(source)
    assert completion.admission_identity_digest == completion.expanded_intent.digest == source["intent_digest"]
    assert completion.native_core_id == UUID(uid(1))
    assert completion.profile_digest == completion.qualified_deployment_profile.digest
    exported = completion.qualified_profile_payload()
    assert exported == source["qualified_deployment_profile"] and len(exported) == 7
    assert QualifiedDeploymentProfile(**exported) == completion.qualified_deployment_profile
    exported["representation_model"] = "mutated"
    source["external_owner_projection"]["identity"]["seed"]["core_traits"].append("mutated")
    assert completion.qualified_profile_payload()["representation_model"] == "fixture-model"
    assert completion.external_owner_projection.payload() != source["external_owner_projection"]


@pytest.mark.parametrize("field", [
    "legacy_census", "manifest_digest", "normalization_closure_digest", "geometry_disposition_table_digest",
    "migrated_character_seed_witness", "quiescence_observations", "processes", "listeners",
    "overlay", "role", "character_drift_state", "runtime_caches",
])
def test_fresh_completion_forbids_migration_and_mutable_fields(field):
    source = completion_payload()
    assert field not in source
    source[field] = {}
    with pytest.raises(DeploymentAuthorityError):
        completion_witness_from_payload(source)


@pytest.mark.parametrize("path,value", [
    (("intent_digest",), "0" * 64), (("operation_key",), "different"), (("data_root_identity",), "different"),
    (("native_core_id",), uid(200)), (("core_relative_path",), "other.db"),
    (("schema_id",), "other"), (("schema_major",), True), (("schema_minor",), 999),
    (("qualified_deployment_profile_digest",), "0" * 64), (("runtime_plan_digest",), "0" * 64),
    (("external_owner_closure_digest",), "0" * 64), (("initial_membership_closure_digest",), "0" * 64),
    (("preparation_result_digest",), "0" * 64), (("quiescence_evidence_digest",), "not-a-digest"),
    (("root_profile", "profile_object_id"), uid(201)), (("root_profile", "profile_revision_ordinal"), True),
    (("external_owner_projection", "identity", "overlay"), {}),
    (("external_owner_projection", "identity", "created_ts"), 999),
    (("character_seed_completion", "mode"), "ENABLED"),
    (("initial_memberships",), []), (("runtime_scope_plans",), []),
    (("accepted_start_observation", "data_root_identity"), "other"),
])
def test_fresh_completion_refuses_cross_binding_mismatch_even_if_rehashed(path, value):
    source = completion_payload()
    change(source, path, value)
    if path != ("preparation_result_digest",):
        del source["preparation_result_digest"]
        source["preparation_result_digest"] = digest_mapping(source)
    with pytest.raises(DeploymentAuthorityError):
        completion_witness_from_payload(source)


def test_fresh_owner_projection_requires_exact_json_not_python_numeric_equality():
    source = completion_payload()
    source["expanded_intent"]["creation_facts"]["identity_created_ts"] = 1
    source["intent_digest"] = digest_mapping(source["expanded_intent"])
    source["external_owner_projection"]["identity"]["created_ts"] = True
    source["external_owner_closure_digest"] = digest_mapping(source["external_owner_projection"])
    source["qualified_deployment_profile"]["external_owner_digest"] = source["external_owner_closure_digest"]
    source["qualified_deployment_profile_digest"] = digest_mapping(source["qualified_deployment_profile"])
    del source["preparation_result_digest"]
    source["preparation_result_digest"] = digest_mapping(source)
    with pytest.raises(DeploymentAuthorityError, match="external owner projection mismatch"):
        completion_witness_from_payload(source)


@pytest.mark.parametrize("field,value", [
    ("definition_digest", "0" * 64), ("status", "PENDING"), ("seed_eids", []),
    ("seed_eids", [True]), ("representation_ids", ["bad-id"]), ("source_operation_key", ""),
])
def test_enabled_seed_requires_completed_native_evidence(field, value):
    source = completion_payload(True)
    source["character_seed_completion"][field] = value
    del source["preparation_result_digest"]
    source["preparation_result_digest"] = digest_mapping(source)
    with pytest.raises(DeploymentAuthorityError):
        completion_witness_from_payload(source)


@pytest.mark.parametrize("eids", [[0], [0, 1, 2], [1], [11, 12]])
def test_completed_seed_accepts_nonnegative_eids_and_fresh_completion_round_trip(eids):
    source = completion_payload(True)
    seed = source["character_seed_completion"]
    seed["seed_eids"] = eids
    seed["representation_ids"] = [uid(150 + i) for i in range(len(eids))]
    assert g.GenesisCompletedSeed.from_payload(seed).payload() == seed
    del source["preparation_result_digest"]
    source["preparation_result_digest"] = digest_mapping(source)
    assert completion_witness_from_payload(source).payload() == source


@pytest.mark.parametrize("eids", [[], [-1], [-1, 0], [False], [True], [0, 0], [1, 1], ["0"], [0.0], [None]])
def test_completed_seed_refuses_invalid_or_duplicate_eids(eids):
    seed = completion_payload(True)["character_seed_completion"]
    seed["seed_eids"] = eids
    with pytest.raises(g.GenesisContractError):
        g.GenesisCompletedSeed.from_payload(seed)


def historical_payload():
    return dict(admission_identity_digest="a" * 64, completed_descriptor_digest="b" * 64,
                completed_progress_digest="c" * 64, native_core_id=uid(1), workspace_id="historical",
                whole_workspace_closure_digest="d" * 64, profile_digest=None)


def migration_payload():
    value = {field.name: "a" * 64 for field in fields(RootAdmissionCompletionWitness)}
    value.update(data_root_identity="historical-root", target_representation_identity="historical-lane",
                 native_staging_core_id=uid(1), root_profile_object_id=uid(2), root_profile_revision_id=uid(3), root_profile_ordinal=1,
                 contract=RootAdmissionCompletionWitness.CONTRACT, version=2)
    return value


def test_decoder_retains_both_historical_wire_shapes():
    for source, cls in ((historical_payload(), AdmissionCompletionWitness), (migration_payload(), RootAdmissionCompletionWitness)):
        result = completion_witness_from_payload(source)
        assert type(result) is cls
        assert result.payload() == source
        assert canonical_json(result.payload()) == canonical_json(source)
        assert not isinstance(result, NativeGenesisCompletionWitness)
    source = historical_payload()
    del source["profile_digest"]
    assert completion_witness_from_payload(source).profile_digest is None


@pytest.mark.parametrize("contract,version", [("UNKNOWN", 1), (None, None), ("TORMENT_NATIVE_GENESIS_COMPLETION_WITNESS", 2),
                                              ("TORMENT_NATIVE_GENESIS_COMPLETION_WITNESS", True),
                                              ("TORMENT_ROOT_ADMISSION_COMPLETION_WITNESS", 3)])
def test_unknown_tagged_payload_cannot_fall_through_to_historical(contract, version):
    for source in (historical_payload(), completion_payload(), migration_payload()):
        source.update(contract=contract, version=version)
        with pytest.raises(DeploymentAuthorityError):
            completion_witness_from_payload(source)


def test_migration_and_genesis_cannot_impersonate_each_other():
    fresh, migration = completion_payload(), migration_payload()
    fresh.update(contract=RootAdmissionCompletionWitness.CONTRACT, version=2)
    migration.update(contract=NativeGenesisCompletionWitness.CONTRACT, version=1, origin="NATIVE_GENESIS")
    for value in (fresh, migration, {}, {"version": 1}, None):
        with pytest.raises(DeploymentAuthorityError):
            completion_witness_from_payload(value)


def fence_facts():
    return g.GenesisFenceFacts("root", g.GenesisEvidenceStatus.VALID, "root", "operation",
                              g.GenesisAuthorityDisposition.UNPUBLISHED, g.GenesisEvidenceStatus.ABSENT, None, None)


def test_fence_absent_does_not_add_an_independent_startup_authority():
    facts = replace(fence_facts(), record_status=g.GenesisEvidenceStatus.ABSENT,
                    record_data_root_identity=None, record_operation_key=None,
                    authority_disposition=g.GenesisAuthorityDisposition.NATIVE_ACTIVE_AGREEMENT,
                    fresh_completion_status=g.GenesisEvidenceStatus.VALID,
                    fresh_completion_data_root_identity="root", fresh_completion_operation_key="operation")
    assert g.classify_genesis_fence(facts) is g.GenesisFenceDisposition.ABSENT


def test_fence_preparation_and_stale_phase_native_authority():
    facts = fence_facts()
    assert g.classify_genesis_fence(facts) is g.GenesisFenceDisposition.BLOCK_LEGACY
    assert "administrative_phase" not in {field.name for field in fields(facts)}
    facts = replace(facts, fresh_completion_status=g.GenesisEvidenceStatus.VALID,
                    fresh_completion_data_root_identity="root", fresh_completion_operation_key="operation")
    assert g.classify_genesis_fence(facts) is g.GenesisFenceDisposition.BLOCK_LEGACY
    facts = replace(facts, authority_disposition=g.GenesisAuthorityDisposition.NATIVE_ACTIVE_AGREEMENT)
    assert g.classify_genesis_fence(facts) is g.GenesisFenceDisposition.NATIVE_AUTHORITY_WINS
    assert record().administrative_phase is g.GenesisAdministrativePhase.PREPARING


@pytest.mark.parametrize("changes", [
    dict(record_status=g.GenesisEvidenceStatus.INVALID), dict(record_status="VALID"),
    dict(record_data_root_identity="other"), dict(record_operation_key=""),
    dict(authority_disposition=g.GenesisAuthorityDisposition.INVALID), dict(authority_disposition="NATIVE_ACTIVE"),
    dict(fresh_completion_status=g.GenesisEvidenceStatus.INVALID),
    dict(fresh_completion_status=g.GenesisEvidenceStatus.VALID, fresh_completion_data_root_identity="other", fresh_completion_operation_key="operation"),
    dict(fresh_completion_status=g.GenesisEvidenceStatus.VALID, fresh_completion_data_root_identity="root", fresh_completion_operation_key="other"),
    dict(fresh_completion_status=g.GenesisEvidenceStatus.VALID), dict(fresh_completion_operation_key="unexpected"),
    dict(record_status=g.GenesisEvidenceStatus.ABSENT),
])
def test_fence_conflicts(changes):
    assert g.classify_genesis_fence(replace(fence_facts(), **changes)) is g.GenesisFenceDisposition.CONFLICT


def test_contracts_and_replay_never_consult_defaults_filesystem_sqlite_or_owners(monkeypatch):
    source = completion_payload(True)
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        assert name not in {"torment_service.identity", "torment_service.character", "torment_service.fabric"}
        assert name not in {"identity", "character", "fabric"}
        return original_import(name, *args, **kwargs)

    def forbidden(*args, **kwargs):
        pytest.fail("pure contract attempted IO")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", guarded_import)
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(sqlite3, "connect", forbidden)
        result = completion_witness_from_payload(source)
        assert result.payload() == source
        assert g.GenesisOperationRecord.from_payload(record().payload()) == record()
        assert g.classify_genesis_fence(fence_facts()) is g.GenesisFenceDisposition.BLOCK_LEGACY
    assert g.GENESIS_MARKER_CREATED_DURING_G0 is False
    assert g.GENESIS_MARKER_AND_SELECTOR_INITIALIZATION_ADJACENT is True
    assert g.COMPLETED_NATIVE_SEED_RESULT_RECOVERY_WITHOUT_EMBEDDING is True
    assert g.CRYPTOGRAPHIC_HUMAN_OPERATOR_IDENTITY_REQUIRED is False
    assert g.OPERATOR_ATTESTATION_REQUIRED is True
