"""Synthetic and static tests for the unadministered Phase-13 instrument.

No test here constructs a live lineage, host, or manager, and no test passes a
formal E1–E12 command array to the execution backend.
"""

from __future__ import annotations

import ast
import copy
from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from brainvision.projection import OPERATOR_ID, PROJECTION_ID, PROJECTION_SCHEMA_ID


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from brainvision_phase13.clock import QualificationClock
import brainvision_phase13.backend as backend_module
import brainvision_phase13.orchestrator as orchestrator_module
import brainvision_phase13.run_qualification as runner_module
from brainvision_phase13.backend import (
    ArtifactBytes,
    BlockExecutionEvidence,
    FAULT_IDS,
    QualificationExecutionBackend,
    QualificationFaultController,
    QualificationLineageSpec,
    RecordingSink,
    SCHEDULE_OPERATION_NAMES,
    ThrowingSink,
    flatten_block_commands,
)
from brainvision_phase13.evidence import (
    EvidenceBuilder,
    RawStateEvidenceError,
    assert_evidence_safe,
    canonical_projection_evidence,
    detached_block_checkpoint_evidence,
    detached_block_evidence,
)
from brainvision_phase13.grader import (
    GradedBlockResult,
    GradingRecord,
    grade_block,
    grade_evidence_package,
    validate_evidence_selector,
)
from brainvision_phase13.inventory import instrument_content_hash_inventory
from brainvision_phase13.manifests import (
    AUTHORITY_MANIFEST_PATH,
    EVIDENCE_OBLIGATIONS_MANIFEST_PATH,
    EXPECTED_RESULT_MANIFEST_PATH,
    FIXTURE_MANIFEST_PATH,
    SCHEDULE_MANIFEST_PATH,
    load_manifest,
    load_complete_expected_result_manifest,
    manifest_sha256,
    validate_failure_evidence_shapes,
    validate_frozen_instrument_counts,
    validate_schedule_manifest,
    validate_all_manifests,
)
from brainvision_phase13.preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_READY,
    PreflightFacts,
    build_administration_identity,
    collect_environment_checks,
    qualification_harness_sha256,
    verify_preflight,
)
from brainvision_phase13.orchestrator import (
    ExternalAuthorizationArtifact,
    FormalAuthorization,
    FormalAuthorizationError,
    canonical_formal_command_identity,
    dispatch_authorized_qualification,
    load_external_formal_authorization_artifact,
    verify_authorization_arguments,
)
from brainvision_phase13.qualification import (
    MANDATORY_HOLD_PARAGRAPH,
    QualificationExecutionBackend as QualificationExecutionBackendProtocol,
    build_all_block_plans,
    render_final_result,
    stimulate_runtime_snapshot,
)
from brainvision_phase13.result_document import render_formal_result_document
from brainvision_phase13.schemas import (
    BLOCK_IDS,
    FAIL_IMPLEMENTATION,
    FAIL_SCIENTIFIC,
    INVALID_ADMINISTRATION,
    INVALID_ENVIRONMENT,
    ExecutionDefect,
    SyntheticBlockResult,
    TOP_LEVEL_FAIL,
    TOP_LEVEL_INVALID,
    TOP_LEVEL_PASS,
    aggregate_taxonomy,
    canonical_json_bytes,
)


def _manifest_hashes() -> dict[str, str]:
    return {
        "authority_manifest": manifest_sha256(AUTHORITY_MANIFEST_PATH),
        "expected_result_manifest": manifest_sha256(EXPECTED_RESULT_MANIFEST_PATH),
        "evidence_obligations_manifest": manifest_sha256(EVIDENCE_OBLIGATIONS_MANIFEST_PATH),
        "authority_clause_registry": manifest_sha256(TESTS_DIR / "brainvision_phase13" / "authority_clause_registry.json"),
        "criterion_provenance_manifest": manifest_sha256(TESTS_DIR / "brainvision_phase13" / "criterion_provenance_manifest.json"),
        "fixture_manifest": manifest_sha256(FIXTURE_MANIFEST_PATH),
        "schedule_manifest": manifest_sha256(SCHEDULE_MANIFEST_PATH),
    }


def test_clock_is_idempotent_exact_integer_and_explicitly_advanced() -> None:
    clock = QualificationClock()
    assert (clock(), clock(), clock()) == (0, 0, 0)
    clock.set_ns(1_000_000_000)
    assert (clock(), clock()) == (1_000_000_000, 1_000_000_000)
    clock.advance_ns(10_000_000_000)
    assert clock() == 11_000_000_000
    with pytest.raises(ValueError):
        clock.set_ns(10_999_999_999)
    with pytest.raises(TypeError):
        clock.advance_ns(1.0)  # type: ignore[arg-type]


def test_static_manifest_and_machine_graph_validation_do_not_execute_an_arm() -> None:
    hashes = validate_all_manifests()
    assert tuple(hashes) == (
        "authority_manifest",
        "expected_result_manifest",
        "evidence_obligations_manifest",
        "authority_clause_registry",
        "criterion_provenance_manifest",
        "fixture_manifest",
        "schedule_manifest",
    )
    assert all(len(digest) == 64 for digest in hashes.values())


def test_every_frozen_arm_has_complete_structured_commands_and_supported_handlers() -> None:
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    assert tuple(schedule["operation_vocabulary"]) == SCHEDULE_OPERATION_NAMES
    blocks = schedule["blocks"]
    assert tuple(blocks) == BLOCK_IDS
    assert all(
        arm["commands"]
        for block in blocks.values()
        for arm in block["arms"].values()
    )
    flattened = [
        command
        for block in blocks.values()
        for arm in block["arms"].values()
        for command in arm["commands"]
    ]
    assert all(command["operation"] in SCHEDULE_OPERATION_NAMES for command in flattened)
    assert not any(command["operation"] == "CONSTRUCT_SIDECAR_AHEAD" for command in flattened)
    assert sum(len(block["arms"]) for block in blocks.values()) == 45
    e7_plan = next(plan for plan in build_all_block_plans() if plan.block_id == "E7")
    e7_flattened = list(flatten_block_commands(e7_plan.schedule))
    assert all("arm" in command for command in e7_flattened)
    assert all(
        set(command["observation"]) == {
            "fixture_id", "source_sequence", "adapter_id", "adapter_contract_id",
            "source_capture_time_unix_ns", "confidence_q", "semantic_event_class", "world_event_id",
        }
        for command in e7_flattened if command["operation"] == "ADMIT"
    )


def test_schedule_observation_contracts_match_their_lineage_contracts() -> None:
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    contract_b = schedule["blocks"]["E3"]["arms"]["contract-b"]
    commands = contract_b["commands"]
    lineage_contract = commands[0]["spec"]["adapter_contract_id"]
    observations = [
        command["observation"] for command in commands if command["operation"] == "ADMIT"
    ]

    assert lineage_contract == "bv13-contract-b"
    assert len(observations) == 3
    assert all(observation["adapter_contract_id"] == lineage_contract for observation in observations)

    incompatible = copy.deepcopy(schedule)
    del incompatible["blocks"]["E3"]["arms"]["contract-b"]["commands"][5]["observation"]["adapter_contract_id"]
    with pytest.raises(ValueError, match="adapter_contract_id"):
        validate_schedule_manifest(incompatible)


def _metric_relation_status(relation: str, records: list[dict[str, object]]) -> str:
    criterion = {
        "criterion_id": f"synthetic-{relation}",
        "block_id": "E1",
        "actual_selectors": ["arm_ledgers" if relation == "ALL_ARM_RECORDS_FIELD_EXACT" else "records"],
        "relation": relation,
        "field_path": "metrics.projection_construction_failures_total",
        "expected_value": 0,
        "failure_class": "FAIL_IMPLEMENTATION",
    }
    evidence = (
        {"arm_ledgers": {"synthetic": {"records": records}}}
        if relation == "ALL_ARM_RECORDS_FIELD_EXACT"
        else {"records": records}
    )
    return grade_block(block_id="E1", expected={"criteria": [criterion]}, evidence=evidence).status


@pytest.mark.parametrize(
    "relation",
    ("ALL_ARM_RECORDS_FIELD_EXACT", "ALL_PRESENT_RECORDS_FIELD_EXACT"),
)
def test_metric_record_relations_apply_before_nested_resolution(relation: str) -> None:
    metric = {"projection_construction_failures_total": 0}
    assert _metric_relation_status(relation, [{"metrics": None}, {"metrics": metric}]) == "PASS"
    assert _metric_relation_status(relation, [{"metrics": None}]) == "FAIL"
    assert _metric_relation_status(relation, [{"metrics": {}}]) == "FAIL"
    assert _metric_relation_status(
        relation, [{"metrics": {"projection_construction_failures_total": 1}}]
    ) == "FAIL"


def test_all_projection_construction_obligations_accept_mixed_setup_and_metric_records() -> None:
    obligations = load_manifest(EVIDENCE_OBLIGATIONS_MANIFEST_PATH)
    criteria = [
        criterion
        for block in obligations["blocks"].values()
        for criterion in block["criteria"]
        if criterion["relation"] == "ALL_ARM_RECORDS_FIELD_EXACT"
    ]
    assert len(criteria) == 12
    evidence = {
        "arm_ledgers": {
            "synthetic": {
                "records": [
                    {"metrics": None},
                    {"metrics": {"projection_construction_failures_total": 0}},
                ]
            }
        }
    }
    for criterion in criteria:
        result = grade_block(
            block_id=criterion["block_id"], expected={"criteria": [criterion]}, evidence=evidence
        )
        assert result.status == "PASS"


def test_failure_shapes_and_frozen_counts_are_validated_uniformly() -> None:
    expected = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)
    obligations = load_manifest(EVIDENCE_OBLIGATIONS_MANIFEST_PATH)
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    validate_failure_evidence_shapes(expected)
    validate_frozen_instrument_counts(
        expected_manifest=expected,
        evidence_obligations_manifest=obligations,
        schedule_manifest=schedule,
    )

    failures = {
        criterion["criterion_id"]: criterion["expected_value"]
        for block in expected["blocks"].values()
        for criterion in block["criteria"]
        if criterion["relation"] == "MAPPING_EXACT"
        and criterion["actual_selectors"][0].endswith(".failure")
    }
    assert failures["E7_sidecar_failure"]["durable_committed"] is False
    assert failures["E7_config_pre_failure"]["durable_committed"] is True
    assert failures["E7_post_durable_failure"]["durable_committed"] is True
    assert failures["E10_suspended_refusal"]["durable_committed"] is False
    assert failures["E10_disabled_refusal"]["durable_committed"] is False
    assert "durable_committed" not in failures["E8_equal_replay"]

    malformed = copy.deepcopy(expected)
    del malformed["blocks"]["E10"]["criteria"][0]["expected_value"]["durable_committed"]
    with pytest.raises(ValueError, match="durable_committed"):
        validate_failure_evidence_shapes(malformed)


def test_canonical_fault_vocabulary_has_no_legacy_alias_or_fourth_fault() -> None:
    assert FAULT_IDS == {
        "E7_SIDECAR_WRITE_FAIL",
        "E7_CONFIG_WRITE_PRE_DURABILITY_FAIL",
        "E7_CONFIG_WRITE_POST_DURABILITY_RAISE",
    }
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    assert tuple(schedule["fault_ids"]) == tuple(sorted(FAULT_IDS))


def test_tamper_helper_changes_only_observation_id_to_stream_sequence_two() -> None:
    spec = QualificationLineageSpec(
        workspace_id="synthetic-workspace",
        agent_id="synthetic-agent",
        stream_identity="synthetic-stream",
        adapter_contract_id="synthetic-contract",
        theta=0,
        adapter_id="synthetic-adapter",
    )
    backend = QualificationExecutionBackend(TESTS_DIR / "unused-backend-root")
    lineage = type("SyntheticLineage", (), {"spec": spec})()
    observation = backend.build_observation(
        lineage,
        fixture_id="dA",
        source_sequence=1,
        adapter_id="synthetic-adapter",
        adapter_contract_id="synthetic-contract",
    )
    original_descriptor = observation.descriptor
    original_adapter = observation.adapter_id
    result = backend.tamper_observation_id(observation)
    from brainvision.observation import derive_observation_id

    assert result is observation
    assert observation.source_sequence == 1
    assert observation.observation_id == derive_observation_id(observation.stream_identity, 2)
    assert observation.descriptor == original_descriptor
    assert observation.adapter_id == original_adapter


def test_fault_controller_restores_patched_primitive_without_admission() -> None:
    original_sidecar = backend_module.lifecycle_module.write_vhe_sidecar
    controller = QualificationFaultController()
    controller.inject("E7_SIDECAR_WRITE_FAIL")
    assert backend_module.lifecycle_module.write_vhe_sidecar is not original_sidecar
    controller.clear()
    assert backend_module.lifecycle_module.write_vhe_sidecar is original_sidecar
    with QualificationFaultController() as scoped:
        scoped.inject("E7_CONFIG_WRITE_PRE_DURABILITY_FAIL")
    assert backend_module.lifecycle_module.write_vhe_sidecar is original_sidecar


def test_backend_adapters_and_artifact_hashes_are_detached_and_ungraded() -> None:
    receipt = type("Receipt", (), {"source_sequence": 0})()
    payload = {"detached": "payload"}
    recording = RecordingSink()
    recording.on_projection(receipt, payload)
    payload["detached"] = "changed"
    assert recording.records[0][1] == {"detached": "payload"}
    throwing = ThrowingSink()
    with pytest.raises(RuntimeError, match="phase13_test_only_throwing_sink"):
        throwing.on_projection(receipt, {"detached": "payload"})
    assert throwing.attempts == 1
    assert ArtifactBytes(configuration_bytes=b"c", sidecar_bytes=None).hashes() == {
        "configuration_sha256": sha256(b"c").hexdigest(), "sidecar_sha256": None
    }


def test_backend_contains_no_expected_scientific_results_or_retry_policy() -> None:
    source = (TESTS_DIR / "brainvision_phase13" / "backend.py").read_text(encoding="utf-8")
    for prohibited in (
        "retained_history_code = 8", "trajectory_code = +5", "H1 retained", "6/8/10",
        "for attempt", "while retry", "backoff",
    ):
        assert prohibited not in source


def test_inventory_is_deterministic_and_binds_documents_grader_and_execution_layers() -> None:
    inventory = instrument_content_hash_inventory()
    assert inventory == instrument_content_hash_inventory()
    for required in (
        "docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md",
        "docs/TORMENT_BRAINVISION_PHASE_13_FORMAL_ADMINISTRATION_BINDINGS_v1.0.md",
        "docs/TORMENT_BRAINVISION_PHASE_13_INSTRUMENT_AMENDMENT_1_EXTERNAL_AUTHORIZATION_ARTIFACT_v1.0.md",
        "docs/TORMENT_BRAINVISION_PHASE_13_CORRECTED_QUALIFICATION_INSTRUMENT_AMENDMENT_v1.0.md",
        "tests/brainvision_phase13/backend.py",
        "tests/brainvision_phase13/evidence_obligations_manifest.json",
        "tests/brainvision_phase13/grader.py",
        "tests/brainvision_phase13/orchestrator.py",
        "tests/brainvision_phase13/result_document.py",
        "tests/brainvision_phase13/run_qualification.py",
    ):
        assert required in inventory


def test_independent_grader_uses_only_manifest_criteria_and_detached_synthetic_evidence() -> None:
    expected = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)["blocks"]
    evidence = {
        "checkpoints": {
            "E1_H0_final": {"projection": {"payload": {"schema_id": PROJECTION_SCHEMA_ID, "projection_id": PROJECTION_ID, "operator_id": OPERATOR_ID, "current_activity_code": 0, "retained_history_code": 0, "present_history_relation_code": 0, "trajectory_code": 0, "open_event_class": None, "recurrence_code": 0}}},
            "E1_H1_final": {"projection": {"payload": {"schema_id": PROJECTION_SCHEMA_ID, "projection_id": PROJECTION_ID, "operator_id": OPERATOR_ID, "current_activity_code": 0, "retained_history_code": 8, "present_history_relation_code": 0, "trajectory_code": 0, "open_event_class": None, "recurrence_code": 0}}},
        }
    }
    result = grade_block(block_id="E1", expected=expected["E1"], evidence=evidence)
    assert result.status == "PASS"
    source = (TESTS_DIR / "brainvision_phase13" / "grader.py").read_text(encoding="utf-8")
    assert "brainvision_phase13.backend" not in source
    assert "301_000_000_000" not in source


def test_grader_reports_missing_administered_evidence_as_invalid_without_retry() -> None:
    expected = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)
    package = {"blocks": {block_id: {} for block_id in BLOCK_IDS}}
    record = grade_evidence_package(
        expected_manifest=expected, evidence_package=package, manifest_sha256="a" * 64
    )
    assert record.taxonomy.top_level == "V1A_QUALIFICATION_INVALID"
    assert all(block.status == "INVALID" for block in record.blocks)


def test_e5_authority_only_reference_requires_no_live_h0_evidence() -> None:
    e5 = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)["blocks"]["E5"]
    result = grade_block(block_id="E5", expected=e5, evidence={})
    authority_only = next(item for item in result.criterion_results if item.criterion_id == "E5_H0_authority_only")
    assert authority_only.status == "PASS"
    assert authority_only.evidence_refs == ()


def test_raw_state_selectors_and_raw_evidence_are_rejected() -> None:
    for selector in (
        "checkpoints.x.runtime_snapshot.vhe_state",
        "checkpoints.x.amplitude_1_q",
        "checkpoints.x.remaining_ns",
        "checkpoints.x.write_gate",
    ):
        with pytest.raises(ValueError):
            validate_evidence_selector(selector)
    with pytest.raises(RawStateEvidenceError, match="remaining_ns"):
        assert_evidence_safe({"remaining_ns": 0})
    with pytest.raises(RawStateEvidenceError, match="VheState"):
        assert_evidence_safe({"nested": {"VheState": "synthetic"}})
    builder = EvidenceBuilder()
    builder.record("run_ledger", {"block": "E1", "source_sequence": 0})
    assert builder.to_canonical_bytes()


def test_projection_evidence_is_detached_nine_field_canonical_mapping() -> None:
    record = canonical_projection_evidence(
        {
            "schema_id": PROJECTION_SCHEMA_ID, "projection_id": PROJECTION_ID, "operator_id": OPERATOR_ID,
            "current_activity_code": 0, "retained_history_code": 8,
            "present_history_relation_code": 0, "trajectory_code": 5,
            "open_event_class": None, "recurrence_code": 0,
        }
    )
    assert len(record["payload"]) == 9
    assert record["sha256"] == sha256(record["canonical_bytes_ascii"].encode("ascii")).hexdigest()


def test_checkpoint_serializer_accepts_synthetic_operation_only_and_exposes_no_raw_state() -> None:
    metrics = type("Metrics", (), {
        "sink_invocations_total": 0,
        "sink_delivery_failures_total": 0,
        "projection_construction_failures_total": 0,
    })()
    receipt = type("Receipt", (), {
        "observation_id": "synthetic-id",
        "source_sequence": 1,
        "committed_active_time_ns": 1,
    })()
    operation = type("Operation", (), {
        "operation": "ADMIT",
        "arm": "synthetic-arm",
        "checkpoint": "synthetic",
        "receipt": receipt,
        "projection_record": None,
        "failure": None,
        "artifact_hashes": {"configuration_sha256": "a", "sidecar_sha256": "b"},
        "artifact_metadata": {},
        "lineage_identity": {},
        "recovery": {},
        "metrics": metrics,
    })()
    package = detached_block_checkpoint_evidence((operation,))
    assert package["checkpoints"]["synthetic"]["receipt"]["source_sequence"] == 1


def test_all_e_blocks_are_staticly_constructed_in_exact_order_without_dispatch() -> None:
    plans = build_all_block_plans()
    assert tuple(plan.block_id for plan in plans) == BLOCK_IDS
    assert all(plan.expected and plan.schedule for plan in plans)


def test_default_backend_factory_uses_concrete_executor_without_dispatch() -> None:
    factory = orchestrator_module._DEFAULT_BACKEND_FACTORY
    assert factory is QualificationExecutionBackend
    assert factory is not QualificationExecutionBackendProtocol
    assert factory.__module__ == "brainvision_phase13.backend"
    backend = factory(TESTS_DIR / "unused-default-backend-root")
    assert type(backend) is QualificationExecutionBackend
    backend.close()


def test_administration_identity_is_canonical_and_has_no_reservation_side_effect() -> None:
    hashes = _manifest_hashes()
    arguments = {
        "expected_head": "a" * 40, "specification_sha256": "b" * 64,
        "manifest_sha256s": hashes, "harness_sha256": "c" * 64,
        "command_identity": "python tests/brainvision_phase13/run_qualification.py",
    }
    first = build_administration_identity(**arguments)
    assert first == build_administration_identity(**arguments)
    assert first.startswith("bvphase13a1_")


def test_synthetic_preflight_ready_and_blocked_paths_are_not_execution() -> None:
    hashes = _manifest_hashes()
    blocked = PreflightFacts(
        head="wrong", origin_main="wrong", worktree_clean=False, specification_sha256="wrong",
        manifest_sha256s={}, harness_sha256="wrong", output_directory_fresh=False,
        administration_identity_unused=False, environment_checks=(),
    )
    outcome = verify_preflight(
        facts=blocked, expected_head="a" * 40, expected_specification_sha256="b" * 64,
        expected_manifest_sha256s=hashes, expected_harness_sha256="c" * 64,
    )
    assert outcome.status == PREFLIGHT_BLOCKED
    assert not outcome.administration_identity_consumed and not outcome.taxonomy_emitted
    ready = PreflightFacts(
        head="a" * 40, origin_main="a" * 40, worktree_clean=True, specification_sha256="b" * 64,
        manifest_sha256s=hashes, harness_sha256="c" * 64, output_directory_fresh=True,
        administration_identity_unused=True,
        environment_checks=({"check_id": "synthetic", "status": "PASS", "observed": True, "expected": True},),
    )
    assert verify_preflight(
        facts=ready, expected_head="a" * 40, expected_specification_sha256="b" * 64,
        expected_manifest_sha256s=hashes, expected_harness_sha256="c" * 64,
    ).status == PREFLIGHT_READY


def test_taxonomy_and_terminal_hold_remain_synthetic_only() -> None:
    results = tuple(
        SyntheticBlockResult(
            block_id=block_id, outcome="FAIL" if block_id in {"E1", "E2"} else "UNEXECUTED",
            subcode=FAIL_SCIENTIFIC if block_id == "E1" else FAIL_IMPLEMENTATION if block_id == "E2" else None,
        ) for block_id in BLOCK_IDS
    )
    decision = aggregate_taxonomy(results, administration_defect_after_start=True, environment_prevented_completion=True)
    assert (decision.top_level, decision.subcode) == (TOP_LEVEL_FAIL, FAIL_SCIENTIFIC)
    invalid = aggregate_taxonomy((), administration_defect_after_start=True)
    assert (invalid.top_level, invalid.subcode) == (TOP_LEVEL_INVALID, INVALID_ADMINISTRATION)
    environment = aggregate_taxonomy((), environment_prevented_completion=True)
    assert (environment.top_level, environment.subcode) == (TOP_LEVEL_INVALID, INVALID_ENVIRONMENT)
    passed = aggregate_taxonomy(tuple(SyntheticBlockResult(block_id=block_id, outcome="PASS") for block_id in BLOCK_IDS))
    assert passed.top_level == TOP_LEVEL_PASS
    assert render_final_result(passed).endswith(MANDATORY_HOLD_PARAGRAPH)


def test_runtime_snapshot_stimulus_discards_return_value() -> None:
    class FakeManager:
        calls = 0

        def runtime_snapshot(self, workspace_id: str, agent_id: str) -> object:
            assert (workspace_id, agent_id) == ("workspace", "agent")
            self.calls += 1
            return object()

    manager = FakeManager()
    assert stimulate_runtime_snapshot(manager, "workspace", "agent") is None
    assert manager.calls == 1


def test_formal_latch_refuses_before_dispatch_even_with_all_cli_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    dispatched = 0

    def dispatch_spy(args: object) -> int:
        nonlocal dispatched
        del args
        dispatched += 1
        return 99

    monkeypatch.setattr(runner_module, "dispatch_formal_administration", dispatch_spy)
    assert not hasattr(runner_module, "FORMAL_AUTHORIZATION_MANIFEST")
    with pytest.raises(ValueError, match="every frozen authorization"):
        runner_module.main([
            "--expected-head", "a" * 40,
            "--administration-id", "bvphase13a1_" + "b" * 64,
            "--output-dir", "C:\\TORMENT\\phase13_formal_not_created",
            "--formal-first-administration", "--formal-authorization-token", "unfrozen",
        ])
    assert dispatched == 0


def test_external_authorization_file_must_be_absolute_and_outside_repository() -> None:
    with pytest.raises(FormalAuthorizationError, match="absolute path"):
        load_external_formal_authorization_artifact(Path("formal_authorization_manifest.json"))
    with pytest.raises(FormalAuthorizationError, match="outside the authoritative repository"):
        load_external_formal_authorization_artifact(
            TESTS_DIR / "brainvision_phase13" / "formal_authorization_manifest.json"
        )
    source = (TESTS_DIR / "brainvision_phase13" / "run_qualification.py").read_text(encoding="utf-8")
    assert "FORMAL_AUTHORIZATION_MANIFEST" not in source
    assert "--authorization-file" in source


def test_clean_worktree_preflight_remains_literal_without_authorization_exception() -> None:
    source = (TESTS_DIR / "brainvision_phase13" / "orchestrator.py").read_text(encoding="utf-8")
    assert 'worktree_clean=not _run_git("status", "--porcelain")' in source
    assert "clean except" not in source
    assert "status filtering" not in source


def test_runner_has_no_implicit_execution() -> None:
    assert runner_module.main(["--validate-instrument"]) == 0
    with pytest.raises(ValueError, match="no implicit qualification"):
        runner_module.main([])
    with pytest.raises(ValueError, match="every frozen authorization"):
        runner_module.main(["--formal-first-administration"])


def test_static_isolation_and_no_production_module_points_back_to_phase13_tests() -> None:
    package = TESTS_DIR / "brainvision_phase13"
    forbidden_import_prefixes = (
        "torment_service.fabric", "cognition", "memory", "srg", "hivermind", "spine", "torch", "transformers",
    )
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imported_modules += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        assert not any(
            module == prefix or module.startswith(prefix + ".")
            for module in imported_modules for prefix in forbidden_import_prefixes
        )
    production_sources = tuple((TESTS_DIR.parent / "brainvision").glob("*.py")) + tuple(
        (TESTS_DIR.parent / "torment_service").rglob("*.py")
    )
    assert production_sources
    assert all("brainvision_phase13" not in path.read_text(encoding="utf-8") for path in production_sources)


def test_harness_hash_is_deterministic_source_only_identity() -> None:
    package_directory = TESTS_DIR / "brainvision_phase13"
    assert qualification_harness_sha256(package_directory) == qualification_harness_sha256(package_directory)


def test_schedule_binds_every_default_metadata_value_and_corrected_stream_identity() -> None:
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    assert schedule["observation_defaults"] == {
        "adapter_id": "bv13-adapter-a",
        "adapter_contract_id": "bv13-contract-a",
        "source_capture_time_unix_ns": None,
        "confidence_q": None,
        "semantic_event_class": None,
        "world_event_id": None,
    }
    assert schedule["administered_sink_purity_depth"] == 2
    rendered = SCHEDULE_MANIFEST_PATH.read_text(encoding="utf-8")
    assert '"stream_identity":"e10"' not in rendered
    assert '"stream_identity":"e11"' not in rendered
    assert '"stream_identity":"e12"' not in rendered
    assert "bv13-e10-stream" in rendered
    assert "bv13-e11-stream" in rendered
    assert "bv13-e12-stream" in rendered


def test_static_evidence_checkpoints_cover_the_frozen_immediate_later_and_sink_segments() -> None:
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    checkpoint_ids = {
        command["checkpoint"]
        for block in schedule["blocks"].values()
        for arm in block["arms"].values()
        for command in arm["commands"]
        if "checkpoint" in command
    }
    for required in (
        "E3_adapter_a_seq1", "E3_adapter_a_seq2", "E3_capture_b_seq1",
        "E3_world_b_seq2", "E7_1_pre", "E7_1_post", "E7_2_recovery",
        "E7_5_replay_pre", "E8_equal_pre", "E8_recovered_pre",
        "E9_read_0_seq0", "E9_read_1_seq1", "E9_read_7_seq2",
        "E9_repair_pre", "E9_repair_post_first", "E9_repair_post_second",
        "E11_null_seq0", "E11_null_initial", "E11_null_final",
    ):
        assert required in checkpoint_ids


def test_e3_e7_e8_e9_e11_and_e12_have_the_required_detached_evidence_bindings() -> None:
    obligations = load_manifest(EVIDENCE_OBLIGATIONS_MANIFEST_PATH)["blocks"]
    expected_ids = {
        "E3_adapter_seq1_projection_equal",
        "E3_adapter_seq2_receipt_equal",
        "E3_invalid_identity_configuration_inert",
        "E5_neg1_actual_run_binding",
        "E7_2_one_watermark_repair",
        "E7_3_second_configuration_inert",
        "E7_5_replay_artifacts_inert",
        "E8_equal_configuration_inert",
        "E8_invalid_refusal_receipt_absent",
        "E9_read_0_1_seq2_all_observables_equal",
        "E9_repair_second_sidecar_inert",
        "E11_null_recording_final_durable_equal",
        "E11_null_recording_seq0_durable_equal",
        "E12_complete_bounded_run_ledger_equal",
    }
    actual_ids = {
        criterion["criterion_id"]
        for block in obligations.values()
        for criterion in block["criteria"]
    }
    assert expected_ids <= actual_ids
    complete = load_complete_expected_result_manifest()
    complete_count = sum(len(block["criteria"]) for block in complete["blocks"].values())
    assert complete_count == 228


def test_detached_block_ledger_retains_all_safe_observables_and_arm_comparison_bytes() -> None:
    metrics = type("Metrics", (), {
        "sink_invocations_total": 1,
        "sink_delivery_failures_total": 0,
        "projection_construction_failures_total": 0,
    })()
    operation = type("Operation", (), {
        "operation": "ADMIT",
        "arm": "repeat-a",
        "checkpoint": "synthetic_checkpoint",
        "receipt": type("Receipt", (), {
            "observation_id": "synthetic-id",
            "source_sequence": 1,
            "committed_active_time_ns": 1,
        })(),
        "projection_record": None,
        "failure": None,
        "artifact_hashes": {"configuration_sha256": "a", "sidecar_sha256": "b"},
        "artifact_metadata": {
            "configuration_last_accepted_source_sequence": 1,
            "sidecar_accepted_source_sequence": 1,
        },
        "lineage_identity": {"theta": 0},
        "recovery": {"sidecar_ahead_configuration_repairs_total": 0},
        "metrics": metrics,
    })()
    package = detached_block_evidence((operation,))
    assert package["run_ledger"][0]["receipt"]["source_sequence"] == 1
    assert package["checkpoints"]["synthetic_checkpoint"]["metrics"]["sink_invocations_total"] == 1
    assert package["arm_ledgers"]["repeat-a"]["comparison_canonical_bytes_ascii"]
    assert "vhe_state" not in package["run_ledger_canonical_bytes_ascii"]


def test_formal_result_renderer_emits_the_full_frozen_section_46_only_on_pass() -> None:
    passed = aggregate_taxonomy(
        tuple(SyntheticBlockResult(block_id=block_id, outcome="PASS") for block_id in BLOCK_IDS)
    )
    grading = GradingRecord(
        manifest_sha256="a" * 64,
        evidence_sha256="b" * 64,
        blocks=tuple(
            GradedBlockResult(
                block_id=block_id, status="PASS", presentation_status="PASS", subcode=None,
                criterion_results=(), evidence_refs=(),
            ) for block_id in BLOCK_IDS
        ),
        taxonomy=passed,
    )
    rendered = render_formal_result_document(
        identity_binding_record={"expected_head": "c" * 40, "python_version": "synthetic"},
        preflight_record={"checks": [], "preflight_status": "PREFLIGHT_READY"},
        administration_identity="bvphase13a1_" + "d" * 64,
        evidence_package={"blocks": {}, "administration_started": True},
        grading=grading,
        evidence_index_path="evidence_package_index.json",
    )
    for nonclaim in (
        "emotion", "attention", "awareness", "consciousness", "experience",
        "semantic understanding", "MemoryGraph memory creation or retrieval",
        "general computer vision", "arbitrary-camera behavior", "LLM usefulness",
        "v1b readiness", "general order sensitivity", "natural 300-second memory duration",
        "half_life", "universal cross-platform determinism", "cross-process Phase-12 sink serialization",
    ):
        assert nonclaim in rendered
    assert "BRAINVISION_V1A:\nQUALIFIED\n\nMANDATORY_HOLD:\nACTIVE" in rendered
    assert "### E1" in rendered and "### E12" in rendered
    assert rendered.endswith("constitutes such authorization.")
    failed = GradingRecord(
        manifest_sha256="a" * 64,
        evidence_sha256="b" * 64,
        blocks=(
            GradedBlockResult(
                block_id="E1", status="FAIL", presentation_status="FAIL",
                subcode=FAIL_IMPLEMENTATION, criterion_results=(), evidence_refs=(),
            ),
        ),
        taxonomy=aggregate_taxonomy(
            (SyntheticBlockResult(block_id="E1", outcome="FAIL", subcode=FAIL_IMPLEMENTATION),)
        ),
    )
    failed_rendered = render_formal_result_document(
        identity_binding_record={},
        preflight_record={},
        administration_identity="bvphase13a1_" + "d" * 64,
        evidence_package={"blocks": {}},
        grading=failed,
        evidence_index_path="evidence_package_index.json",
    )
    assert "QUALIFIED" not in failed_rendered
    assert "MANDATORY_HOLD" not in failed_rendered


def test_synthetic_dispatcher_orchestration_uses_mock_backend_only(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, specification_sha256 = _synthetic_authorization(tmp_path)
    authorization = authorization_artifact.authorization
    hashes = _manifest_hashes()
    facts = PreflightFacts(
        head="a" * 40,
        origin_main="a" * 40,
        worktree_clean=True,
        specification_sha256=specification_sha256,
        manifest_sha256s=hashes,
        harness_sha256=authorization.harness_sha256,
        output_directory_fresh=True,
        administration_identity_unused=True,
        environment_checks=({"check_id": "synthetic", "status": "PASS", "observed": True, "expected": True},),
    )
    calls: list[str] = []

    class MockBackend:
        def __init__(self, _root: Path) -> None:
            pass

        def execute_block(self, plan: object, evidence: object) -> BlockExecutionEvidence:
            del evidence
            calls.append(getattr(plan, "block_id"))
            return BlockExecutionEvidence(block_id=getattr(plan, "block_id"), operations=())

        def close(self) -> None:
            return None

    args = SimpleNamespace(
        expected_head="a" * 40,
        administration_id=canonical_id,
        formal_authorization_token="synthetic-token",
        authorization_file=authorization_artifact.normalized_path,
        output_dir=tmp_path / "synthetic-output",
    )
    authorization_artifact.normalized_path.write_bytes(b"{}")
    result = dispatch_authorized_qualification(
        args=args,
        authorization_artifact=authorization_artifact,
        preflight_collector=lambda **_: facts,
        backend_factory=MockBackend,
    )
    assert tuple(calls) == BLOCK_IDS
    assert result.evidence_path.is_file() and result.grading_path.is_file()
    assert result.evidence_index_path.is_file()
    assert "V1A_QUALIFICATION_INVALID" in result.result_document_path.read_text(encoding="utf-8")
    package = __import__("json").loads(result.evidence_path.read_text(encoding="utf-8"))
    assert package["authorization_artifact_sha256"] == authorization_artifact.sha256
    assert package["identity_binding_record"]["authorization_artifact_path"] == str(
        authorization_artifact.normalized_path
    )
    assert package["preflight_record"]["authorization_schema_id"] == authorization_artifact.schema_id


def _synthetic_environment_checks() -> tuple[dict[str, object], ...]:
    return ({"check_id": "synthetic", "status": "PASS", "observed": True, "expected": True},)


def _synthetic_authorization(
    tmp_path: Path,
    *,
    administration_id: str | None = None,
    output_directory: Path | None = None,
) -> tuple[ExternalAuthorizationArtifact, str, str]:
    hashes = _manifest_hashes()
    specification_sha256 = sha256(
        (TESTS_DIR.parent / "docs" / "TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md").read_bytes()
    ).hexdigest()
    harness_sha = qualification_harness_sha256(TESTS_DIR / "brainvision_phase13")
    authorization_path = tmp_path / "external_authorization" / "formal_authorization_manifest.json"
    authorization_path.parent.mkdir(parents=True)
    selected_output_directory = tmp_path / "synthetic-output" if output_directory is None else output_directory
    command_identity = canonical_formal_command_identity(
        authorization_file=authorization_path,
        expected_head="a" * 40,
        output_directory=selected_output_directory,
        authorization_token="synthetic-token",
    )
    canonical_id = build_administration_identity(
        expected_head="a" * 40, specification_sha256=specification_sha256,
        manifest_sha256s=hashes, harness_sha256=harness_sha, command_identity=command_identity,
    )
    payload = {
        "schema_id": "brainvision.phase13.formal_authorization.v2",
        "expected_head": "a" * 40,
        "administration_id": canonical_id if administration_id is None else administration_id,
        "authorization_token": "synthetic-token",
        "command_identity": command_identity,
        "specification_sha256": specification_sha256,
        "manifest_sha256s": hashes,
        "harness_sha256": harness_sha,
        "instrument_inventory": instrument_content_hash_inventory(),
    }
    authorization_path.write_bytes(canonical_json_bytes(payload))
    return (
        load_external_formal_authorization_artifact(authorization_path),
        canonical_id,
        specification_sha256,
    )


def _synthetic_ready_facts(*, specification_sha256: str, hashes: dict[str, str], harness_sha: str) -> PreflightFacts:
    return PreflightFacts(
        head="a" * 40, origin_main="a" * 40, worktree_clean=True,
        specification_sha256=specification_sha256, manifest_sha256s=hashes,
        harness_sha256=harness_sha, output_directory_fresh=True,
        administration_identity_unused=True, environment_checks=_synthetic_environment_checks(),
    )


def test_formal_authorization_freezes_nested_mappings_without_source_aliases() -> None:
    source_manifest_hashes = {"authority_manifest": "a" * 64}
    source_inventory = {"tests/brainvision_phase13/orchestrator.py": "b" * 64}
    authorization = FormalAuthorization(
        expected_head="c" * 40,
        administration_id="bvphase13a1_" + "d" * 64,
        authorization_token="synthetic-token",
        command_identity="synthetic-command",
        specification_sha256="e" * 64,
        manifest_sha256s=source_manifest_hashes,
        harness_sha256="f" * 64,
        instrument_inventory=source_inventory,
    )

    source_manifest_hashes["authority_manifest"] = "g" * 64
    source_inventory["tests/brainvision_phase13/orchestrator.py"] = "h" * 64

    assert authorization.manifest_sha256s["authority_manifest"] == "a" * 64
    assert authorization.instrument_inventory["tests/brainvision_phase13/orchestrator.py"] == "b" * 64
    with pytest.raises(TypeError):
        authorization.manifest_sha256s["unexpected"] = "i" * 64  # type: ignore[index]
    with pytest.raises(TypeError):
        authorization.instrument_inventory["unexpected"] = "j" * 64  # type: ignore[index]


def test_immutable_authorization_preserves_canonical_bytes_and_administration_id(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, _ = _synthetic_authorization(tmp_path)
    authorization = authorization_artifact.authorization
    canonical_payload = {
        "schema_id": "brainvision.phase13.formal_authorization.v2",
        "expected_head": authorization.expected_head,
        "administration_id": authorization.administration_id,
        "authorization_token": authorization.authorization_token,
        "command_identity": authorization.command_identity,
        "specification_sha256": authorization.specification_sha256,
        "manifest_sha256s": dict(authorization.manifest_sha256s),
        "harness_sha256": authorization.harness_sha256,
        "instrument_inventory": dict(authorization.instrument_inventory),
    }

    assert canonical_json_bytes(canonical_payload) == authorization_artifact.canonical_bytes
    assert build_administration_identity(
        expected_head=authorization.expected_head,
        specification_sha256=authorization.specification_sha256,
        manifest_sha256s=authorization.manifest_sha256s,
        harness_sha256=authorization.harness_sha256,
        command_identity=authorization.command_identity,
    ) == canonical_id
    with pytest.raises(TypeError):
        authorization_artifact.authorization.manifest_sha256s["unexpected"] = "a" * 64  # type: ignore[index]


def test_fixture_manifest_is_descriptor_only_and_all_criteria_have_machine_provenance() -> None:
    fixture = load_manifest(FIXTURE_MANIFEST_PATH)
    assert "observation_envelope_defaults" not in fixture
    assert "phase13-adapter-v1" not in (TESTS_DIR / "brainvision_phase13" / "fixtures.py").read_text(encoding="utf-8")
    complete = load_complete_expected_result_manifest()
    criteria = [
        criterion for block in complete["blocks"].values() for criterion in block["criteria"]
    ]
    assert len(criteria) == 228
    for criterion in criteria:
        assert criterion["authority_sources"]
        assert criterion["obligation_kind"] in {
            "EVIDENCE_COMPLETENESS", "SCIENTIFIC_CRITERION",
            "IMPLEMENTATION_CRITERION", "AUTHORITY_ONLY_REFERENCE",
        }
        assert all(source["document_sha256"] in {
            "3f53bcbbf5e2d4380c72a110060a8b032db22e02df25a2024e7b04f2ccd09ba0",
            "05db28035b5fec45e1412ac765e9aadba3503cbbc43fa870d6707747f6f51e8d",
        } for source in criterion["authority_sources"])


def test_canonical_authorization_identity_refuses_cli_and_artifact_mismatches(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, _ = _synthetic_authorization(tmp_path)
    authorization = authorization_artifact.authorization
    valid = SimpleNamespace(
        expected_head="a" * 40, administration_id=canonical_id,
        formal_authorization_token="synthetic-token",
        authorization_file=authorization_artifact.normalized_path,
        output_dir=tmp_path / "synthetic-output",
    )
    verify_authorization_arguments(valid, authorization_artifact, canonical_id)
    with pytest.raises(FormalAuthorizationError):
        verify_authorization_arguments(
            SimpleNamespace(
                expected_head="a" * 40, administration_id="bvphase13a1_" + "0" * 64,
                formal_authorization_token="synthetic-token",
                authorization_file=authorization_artifact.normalized_path,
                output_dir=tmp_path / "synthetic-output",
            ), authorization_artifact, canonical_id,
        )
    mismatched, _, _ = _synthetic_authorization(
        tmp_path / "mismatched", administration_id="bvphase13a1_" + "1" * 64
    )
    with pytest.raises(FormalAuthorizationError):
        verify_authorization_arguments(valid, mismatched, canonical_id)


def test_environment_preflight_failure_is_blocked_without_dispatch() -> None:
    hashes = _manifest_hashes()
    facts = _synthetic_ready_facts(
        specification_sha256="b" * 64, hashes=hashes, harness_sha="c" * 64,
    )
    failed_environment = PreflightFacts(
        **{**facts.__dict__, "environment_checks": ({"check_id": "fsync", "status": "FAIL", "observed": False, "expected": True},)}
    )
    outcome = verify_preflight(
        facts=failed_environment, expected_head="a" * 40,
        expected_specification_sha256="b" * 64, expected_manifest_sha256s=hashes,
        expected_harness_sha256="c" * 64,
    )
    assert outcome.status == PREFLIGHT_BLOCKED
    assert "environment_not_capable" in outcome.reasons
    assert not outcome.administration_identity_consumed and not outcome.taxonomy_emitted


def test_post_start_backend_construction_failure_preserves_invalid_evidence(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, specification_sha256 = _synthetic_authorization(
        tmp_path, output_directory=tmp_path / "construction-failure"
    )
    authorization = authorization_artifact.authorization
    facts = _synthetic_ready_facts(
        specification_sha256=specification_sha256, hashes=_manifest_hashes(),
        harness_sha=authorization.harness_sha256,
    )

    def failing_factory(_root: Path) -> object:
        raise RuntimeError("synthetic backend construction failure")

    result = dispatch_authorized_qualification(
        args=SimpleNamespace(
            expected_head="a" * 40, administration_id=canonical_id,
            formal_authorization_token="synthetic-token", authorization_file=authorization_artifact.normalized_path,
            output_dir=tmp_path / "construction-failure",
        ), authorization_artifact=authorization_artifact, preflight_collector=lambda **_: facts,
        backend_factory=failing_factory,
    )
    package = __import__("json").loads(result.evidence_path.read_text(encoding="utf-8"))
    assert package["administration_started"] is True
    assert package["execution_failure"]["stage"] == "backend_construction"
    assert all(block["execution_state"] == "NOT_EXECUTED" for block in package["blocks"].values())
    rendered = result.result_document_path.read_text(encoding="utf-8")
    assert "presentation_status: `NOT_EXECUTED`" in rendered
    assert "V1A_QUALIFICATION_INVALID" in rendered
    index = __import__("json").loads(result.evidence_index_path.read_text(encoding="utf-8"))
    assert {"identity_binding_record", "environment_preflight_record", "ordered_operation_run_ledger", "formal_result_document"} <= set(index["components"])


def test_mid_block_defect_preserves_partial_safe_ledger_without_live_backend(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, specification_sha256 = _synthetic_authorization(
        tmp_path, output_directory=tmp_path / "partial-failure"
    )
    authorization = authorization_artifact.authorization
    facts = _synthetic_ready_facts(
        specification_sha256=specification_sha256, hashes=_manifest_hashes(),
        harness_sha=authorization.harness_sha256,
    )
    operation = type("SyntheticOperation", (), {
        "operation": "SET_CLOCK", "checkpoint": "synthetic-partial", "lineage_name": "synthetic",
        "arm": "synthetic", "receipt": None, "projection_record": None, "failure": None,
        "artifact_hashes": {"configuration_sha256": None, "sidecar_sha256": None},
        "artifact_metadata": {}, "lineage_identity": {}, "recovery": {}, "metrics": None,
    })()

    class PartialBackend:
        def __init__(self, _root: Path) -> None:
            self.calls = 0

        def execute_block(self, plan: object, evidence: EvidenceBuilder) -> BlockExecutionEvidence:
            self.calls += 1
            evidence.record_backend_operation(getattr(plan, "block_id"), operation)
            return BlockExecutionEvidence(
                block_id=getattr(plan, "block_id"), operations=(operation,), complete=False,
                defect=ExecutionDefect(
                    block_id=getattr(plan, "block_id"), operation_index=1,
                    operation="ADMIT", arm="synthetic", exception_class="SyntheticFailure",
                ),
            )

        def close(self) -> None:
            return None

    result = dispatch_authorized_qualification(
        args=SimpleNamespace(
            expected_head="a" * 40, administration_id=canonical_id,
            formal_authorization_token="synthetic-token", authorization_file=authorization_artifact.normalized_path,
            output_dir=tmp_path / "partial-failure",
        ), authorization_artifact=authorization_artifact, preflight_collector=lambda **_: facts,
        backend_factory=PartialBackend,
    )
    package = __import__("json").loads(result.evidence_path.read_text(encoding="utf-8"))
    assert package["blocks"]["E1"]["execution_state"] == "INCOMPLETE"
    assert package["blocks"]["E1"]["run_ledger"]
    assert package["blocks"]["E2"]["execution_state"] == "NOT_EXECUTED"
    assert (result.evidence_path.parent / "operation_journal.ndjson").read_bytes()
    rendered = result.result_document_path.read_text(encoding="utf-8")
    assert "presentation_status: `INCOMPLETE`" in rendered
    assert "presentation_status: `NOT_EXECUTED`" in rendered


def test_safe_exception_capture_never_serializes_attached_raw_state() -> None:
    class LeakingException(RuntimeError):
        field = object()
        reason = object()
        durable_committed = object()
        raw_state = {"vhe_state": "forbidden"}

    record = orchestrator_module._safe_exception_record(LeakingException(), stage="synthetic")
    assert record["field"] is None and record["reason"] is None
    assert_evidence_safe(record)


def test_environment_check_record_is_structured_and_never_a_hard_coded_boolean(tmp_path: Path) -> None:
    checks = collect_environment_checks(
        output_directory=tmp_path / "isolated-output", repository_root=TESTS_DIR.parent,
        required_imports=("json",),
    )
    assert {"python_runtime", "required_imports", "isolated_output_root", "output_parent_exists", "output_directory_fresh", "persistence_filesystem"} == {
        item["check_id"] for item in checks
    }
    assert all(set(item) == {"check_id", "expected", "observed", "status"} for item in checks)


def test_formal_authorization_schema_is_closed_and_data_only(tmp_path: Path) -> None:
    authorization_artifact, _, _ = _synthetic_authorization(tmp_path)
    authorization = authorization_artifact.authorization
    payload = {
        "schema_id": "brainvision.phase13.formal_authorization.v2",
        "expected_head": authorization.expected_head,
        "administration_id": authorization.administration_id,
        "authorization_token": authorization.authorization_token,
        "command_identity": authorization.command_identity,
        "specification_sha256": authorization.specification_sha256,
        "manifest_sha256s": dict(authorization.manifest_sha256s),
        "harness_sha256": authorization.harness_sha256,
        "instrument_inventory": dict(authorization.instrument_inventory),
    }
    artifact = tmp_path / "synthetic_authorization.json"
    artifact.write_bytes(canonical_json_bytes(payload))
    assert load_external_formal_authorization_artifact(artifact).authorization.administration_id == authorization.administration_id
    payload["unexpected"] = True
    artifact.write_bytes(canonical_json_bytes(payload))
    with pytest.raises(FormalAuthorizationError):
        load_external_formal_authorization_artifact(artifact)


def test_independent_grading_preserves_valid_fail_precedence_over_later_environment_gap() -> None:
    expected = {"blocks": {block_id: {"criteria": []} for block_id in BLOCK_IDS}}
    expected["blocks"]["E1"] = {
        "criteria": [{
            "criterion_id": "synthetic-fail", "actual_selectors": ["value"],
            "relation": "EXACT", "expected_value": 1,
            "failure_class": "FAIL_IMPLEMENTATION",
        }]
    }
    evidence = {"blocks": {block_id: {"execution_state": "NOT_EXECUTED"} for block_id in BLOCK_IDS}}
    evidence["blocks"]["E1"] = {"value": 0}
    evidence["blocks"]["E2"] = {
        "execution_state": "INCOMPLETE",
        "defect": {"invalid_subcode": INVALID_ENVIRONMENT},
    }
    grading = grade_evidence_package(
        expected_manifest=expected, evidence_package=evidence, manifest_sha256="a" * 64,
    )
    assert (grading.taxonomy.top_level, grading.taxonomy.subcode) == (
        TOP_LEVEL_FAIL, FAIL_IMPLEMENTATION,
    )
    assert grading.blocks[0].presentation_status == "FAIL"
    assert grading.blocks[1].presentation_status == "INCOMPLETE"


def test_independent_reconstruction_of_synthetic_evidence_never_calls_backend(tmp_path: Path) -> None:
    authorization_artifact, canonical_id, specification_sha256 = _synthetic_authorization(
        tmp_path, output_directory=tmp_path / "reconstruction"
    )
    authorization = authorization_artifact.authorization
    facts = _synthetic_ready_facts(
        specification_sha256=specification_sha256, hashes=_manifest_hashes(),
        harness_sha=authorization.harness_sha256,
    )

    def failing_factory(_root: Path) -> object:
        raise RuntimeError("synthetic only")

    result = dispatch_authorized_qualification(
        args=SimpleNamespace(
            expected_head="a" * 40, administration_id=canonical_id,
            formal_authorization_token="synthetic-token", authorization_file=authorization_artifact.normalized_path,
            output_dir=tmp_path / "reconstruction",
        ), authorization_artifact=authorization_artifact, preflight_collector=lambda **_: facts,
        backend_factory=failing_factory,
    )
    package = __import__("json").loads(result.evidence_path.read_text(encoding="utf-8"))
    rebuilt = grade_evidence_package(
        expected_manifest=load_complete_expected_result_manifest(), evidence_package=package,
        manifest_sha256=result.grading.manifest_sha256,
    )
    rebuilt_document = render_formal_result_document(
        identity_binding_record=package["identity_binding_record"],
        preflight_record=package["preflight_record"], administration_identity=canonical_id,
        evidence_package=package, grading=rebuilt,
        evidence_index_path="evidence_package_index.json",
    )
    assert rebuilt.taxonomy.top_level == TOP_LEVEL_INVALID
    assert rebuilt_document == result.result_document_path.read_text(encoding="utf-8")
