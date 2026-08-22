"""Strict static validation for the frozen Phase-13 test-only instrument."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
import json
from pathlib import Path
from typing import Final

from brainvision.character_modulation import (
    MODULATION_MAPPING_ID,
    MODULATION_PROFILE_SCHEMA_ID,
    MODULATION_SCHEMA_ID,
    modulation_profile_id,
)
from brainvision.fixtures import D0, DA, DB
from brainvision.observation import IDENTITY_SCHEMA_ID, OBSERVATION_SCHEMA_ID
from brainvision.projection import PROJECTION_ID, PROJECTION_SCHEMA_ID
from brainvision.vhe import OPERATOR_ID, RNE_ALGORITHM_ID

from brainvision_phase13.fixtures import (
    FIXTURE_MANIFEST_PATH,
    frozen_fixture_manifest_data,
    validate_fixture_manifest,
)
from brainvision_phase13.grader import CRITERION_RELATIONS, validate_evidence_selector
from brainvision_phase13.schemas import BLOCK_IDS, canonical_json_bytes, require_exact_block_ids, sha256_hex


PACKAGE_DIR: Final = Path(__file__).resolve().parent
EXPECTED_RESULT_MANIFEST_PATH: Final = PACKAGE_DIR / "expected_result_manifest.json"
EVIDENCE_OBLIGATIONS_MANIFEST_PATH: Final = PACKAGE_DIR / "evidence_obligations_manifest.json"
AUTHORITY_CLAUSE_REGISTRY_PATH: Final = PACKAGE_DIR / "authority_clause_registry.json"
CRITERION_PROVENANCE_MANIFEST_PATH: Final = PACKAGE_DIR / "criterion_provenance_manifest.json"
SCHEDULE_MANIFEST_PATH: Final = PACKAGE_DIR / "schedule_manifest.json"
AUTHORITY_MANIFEST_PATH: Final = PACKAGE_DIR / "authority_manifest.json"
_SINK_MODES: Final[frozenset[str]] = frozenset({"null", "recording", "throwing"})
_OBSERVATION_DEFAULT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "adapter_id",
        "adapter_contract_id",
        "source_capture_time_unix_ns",
        "confidence_q",
        "semantic_event_class",
        "world_event_id",
    }
)
_OBSERVATION_COMMAND_FIELDS: Final[frozenset[str]] = frozenset(
    {"fixture_id", "source_sequence"} | _OBSERVATION_DEFAULT_FIELDS
)
_FROZEN_FORMAL_ARM_COUNT: Final = 45
_FROZEN_PRIMARY_CRITERIA_COUNT: Final = 81
_FROZEN_EVIDENCE_OBLIGATION_COUNT: Final = 147
_FROZEN_TOTAL_CRITERIA_COUNT: Final = 228
_FAILURE_DURABILITY_BY_SHAPE: Final[dict[tuple[str, str], bool | None]] = {
    ("observation_id", "invalid_observation_id"): None,
    ("source_sequence", "refused_replay"): None,
    ("sidecar", "durability_failure"): False,
    ("configuration", "recovery_required"): True,
    ("lifecycle_status", "invalid_lifecycle_transition"): False,
}


def load_manifest(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON manifest: {path.name}") from error
    if type(payload) is not dict:
        raise ValueError(f"manifest root must be an object: {path.name}")
    return payload


def manifest_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _command_checkpoints(schedule: Mapping[str, object]) -> frozenset[str]:
    checkpoints: set[str] = set()
    blocks = schedule["blocks"]
    assert isinstance(blocks, Mapping)
    for block in blocks.values():
        assert isinstance(block, Mapping)
        arms = block.get("arms")
        assert isinstance(arms, Mapping)
        for arm in arms.values():
            assert isinstance(arm, Mapping)
            commands = arm.get("commands")
            assert isinstance(commands, Sequence)
            for command in commands:
                assert isinstance(command, Mapping)
                checkpoint = command.get("checkpoint")
                if checkpoint is not None:
                    if type(checkpoint) is not str or checkpoint in checkpoints:
                        raise ValueError("command checkpoint must be unique and textual")
                    checkpoints.add(checkpoint)
    return frozenset(checkpoints)


def resolve_effective_observation_spec(
    observation_defaults: Mapping[str, object], command_observation: Mapping[str, object]
) -> dict[str, object]:
    """Return one complete frozen observation without backend-only defaults."""
    if set(observation_defaults) != _OBSERVATION_DEFAULT_FIELDS:
        raise ValueError("schedule observation defaults must bind the exact metadata fields")
    if set(command_observation) - _OBSERVATION_COMMAND_FIELDS:
        raise ValueError("ADMIT uses an unknown observation field")
    if set(command_observation) & {"fixture_id", "source_sequence"} != {
        "fixture_id",
        "source_sequence",
    }:
        raise ValueError("ADMIT must bind fixture_id and source_sequence explicitly")
    resolved = dict(observation_defaults)
    resolved.update(command_observation)
    if resolved["fixture_id"] not in {"d0", "dA", "dB"}:
        raise ValueError("ADMIT must use a frozen descriptor fixture")
    if type(resolved["source_sequence"]) is not int:
        raise ValueError("ADMIT source_sequence must be an exact integer")
    for field in ("adapter_id", "adapter_contract_id"):
        if type(resolved[field]) is not str:
            raise ValueError(f"ADMIT {field} must resolve to str")
    for field in ("source_capture_time_unix_ns", "confidence_q"):
        if resolved[field] is not None and type(resolved[field]) is not int:
            raise ValueError(f"ADMIT {field} must resolve to int or null")
    for field in ("semantic_event_class", "world_event_id"):
        if resolved[field] is not None and type(resolved[field]) is not str:
            raise ValueError(f"ADMIT {field} must resolve to str or null")
    return resolved


def resolved_schedule_commands(payload: Mapping[str, object]) -> dict[str, tuple[dict[str, object], ...]]:
    """Expose all statically completed ADMIT commands without executing them."""
    defaults = payload.get("observation_defaults")
    blocks = payload.get("blocks")
    if not isinstance(defaults, Mapping) or not isinstance(blocks, Mapping):
        raise ValueError("schedule lacks defaults or blocks")
    result: dict[str, tuple[dict[str, object], ...]] = {}
    for block_id, block in blocks.items():
        if not isinstance(block, Mapping) or not isinstance(block.get("arms"), Mapping):
            raise ValueError("schedule block is malformed")
        commands: list[dict[str, object]] = []
        for arm_name, arm in block["arms"].items():
            if not isinstance(arm, Mapping) or not isinstance(arm.get("commands"), Sequence):
                raise ValueError("schedule arm is malformed")
            for command in arm["commands"]:
                if not isinstance(command, Mapping):
                    raise ValueError("schedule command is malformed")
                completed = dict(command)
                completed.setdefault("arm", arm_name)
                if completed.get("operation") == "ADMIT":
                    observation = completed.get("observation")
                    if not isinstance(observation, Mapping):
                        raise ValueError("ADMIT requires an observation mapping")
                    completed["observation"] = resolve_effective_observation_spec(
                        defaults, observation
                    )
                commands.append(completed)
        result[str(block_id)] = tuple(commands)
    return result


def _validate_command(
    command: Mapping[str, object], lineages: set[str], observation_defaults: Mapping[str, object]
) -> None:
    from brainvision_phase13.backend import FAULT_IDS, FIXTURE_IDS, SCHEDULE_OPERATION_NAMES

    operation = command.get("operation")
    if operation not in SCHEDULE_OPERATION_NAMES:
        raise ValueError(f"schedule command has no backend handler: {operation!r}")
    lineage = command.get("lineage")
    if type(lineage) is not str:
        raise ValueError("every command must bind one explicit lineage")
    if operation == "CREATE_LINEAGE":
        spec = command.get("spec")
        if not isinstance(spec, Mapping) or set(spec) != {
            "workspace_id", "agent_id", "stream_identity", "adapter_contract_id", "theta", "adapter_id"
        }:
            raise ValueError("CREATE_LINEAGE must contain the closed lineage spec")
        if lineage in lineages:
            raise ValueError("lineage may be created only once")
        lineages.add(lineage)
        if command.get("sink_mode") not in _SINK_MODES:
            raise ValueError("CREATE_LINEAGE requires a frozen sink mode")
        return
    if lineage not in lineages:
        raise ValueError("schedule command references a lineage before creation")
    if operation == "ADMIT":
        observation = command.get("observation")
        if not isinstance(observation, Mapping):
            raise ValueError("ADMIT must use the closed observation schema")
        resolved = resolve_effective_observation_spec(observation_defaults, observation)
        if resolved["fixture_id"] not in FIXTURE_IDS:
            raise ValueError("ADMIT must resolve a frozen fixture")
        if command.get("tamper_observation_id", False) not in {True, False}:
            raise ValueError("tamper_observation_id must be boolean")
    if operation == "INJECT_FAULT" and command.get("fault_id") not in FAULT_IDS:
        raise ValueError("command does not resolve a frozen fault ID")
    if operation == "CREATE_HOST" and "sink_mode" in command and command["sink_mode"] not in _SINK_MODES:
        raise ValueError("CREATE_HOST sink mode is not frozen")
    for numeric_key in ("active_time_ns", "delta_ns"):
        if numeric_key in command and type(command[numeric_key]) is not int:
            raise ValueError(f"{numeric_key} must be an integer nanosecond value")


def validate_expected_result_manifest(
    payload: Mapping[str, object], *, require_provenance: bool = False
) -> None:
    if payload.get("schema_id") != "brainvision.phase13.expected_result_manifest.v2":
        raise ValueError("unexpected expected-result manifest schema")
    blocks = payload.get("blocks")
    if not isinstance(blocks, Mapping):
        raise ValueError("expected-result manifest requires blocks")
    require_exact_block_ids(blocks)
    criterion_ids: set[str] = set()
    for block_id, block in blocks.items():
        if not isinstance(block, Mapping):
            raise ValueError(f"{block_id} expected block must be a mapping")
        criteria = block.get("criteria")
        if not isinstance(criteria, Sequence) or isinstance(criteria, (str, bytes)) or not criteria:
            raise ValueError(f"{block_id} needs frozen criteria")
        for criterion in criteria:
            if not isinstance(criterion, Mapping):
                raise ValueError("criterion must be an object")
            identifier = criterion.get("criterion_id")
            selectors = criterion.get("actual_selectors")
            relation = criterion.get("relation")
            if type(identifier) is not str or identifier in criterion_ids:
                raise ValueError("criterion IDs must be globally unique")
            criterion_ids.add(identifier)
            if criterion.get("block_id") != block_id or relation not in CRITERION_RELATIONS:
                raise ValueError("criterion has an invalid block or relation")
            if not isinstance(selectors, Sequence) or isinstance(selectors, (str, bytes)):
                raise ValueError("criterion actual selectors must be an array")
            for selector in selectors:
                validate_evidence_selector(selector)
                if selector.startswith("checkpoints."):
                    parts = selector.split(".")
                    if len(parts) < 2 or (len(parts) > 2 and parts[2] not in {
                        "artifact_hashes", "artifact_metadata", "failure", "failure_type", "lineage_identity",
                        "metrics", "operation", "projection", "receipt", "recovery"
                    }):
                        raise ValueError(
                            f"criterion selector has no detached evidence root: {identifier}"
                        )
            if relation == "AUTHORITY_ONLY_STRUCTURAL_REPRODUCTION_REFERENCE":
                if selectors or not isinstance(criterion.get("authority_reference"), Mapping):
                    raise ValueError("authority-only criterion must not require live evidence")
            elif not selectors:
                raise ValueError("administered criterion must select detached evidence")
            if criterion.get("failure_class") not in {
                "FAIL_SCIENTIFIC", "FAIL_IMPLEMENTATION", "INVALID_ADMINISTRATION"
            }:
                raise ValueError("criterion must bind a frozen failure class")
            if require_provenance:
                sources = criterion.get("authority_sources")
                if (
                    not isinstance(sources, Sequence)
                    or isinstance(sources, (str, bytes))
                    or not sources
                    or any(not isinstance(source, Mapping) for source in sources)
                ):
                    raise ValueError("every criterion requires mechanical authority provenance")
                if criterion.get("obligation_kind") not in {
                    "EVIDENCE_COMPLETENESS",
                    "SCIENTIFIC_CRITERION",
                    "IMPLEMENTATION_CRITERION",
                    "AUTHORITY_ONLY_REFERENCE",
                }:
                    raise ValueError("criterion requires a closed obligation kind")


def validate_failure_evidence_shapes(payload: Mapping[str, object]) -> None:
    """Bind each formal failure mapping to its frozen runtime durability shape."""

    blocks = payload.get("blocks")
    if not isinstance(blocks, Mapping):
        raise ValueError("expected-result manifest requires blocks")
    for block in blocks.values():
        if not isinstance(block, Mapping):
            raise ValueError("expected block must be a mapping")
        criteria = block.get("criteria")
        if not isinstance(criteria, Sequence) or isinstance(criteria, (str, bytes)):
            raise ValueError("expected block requires criteria")
        for criterion in criteria:
            if not isinstance(criterion, Mapping):
                raise ValueError("criterion must be a mapping")
            selectors = criterion.get("actual_selectors")
            if (
                criterion.get("relation") != "MAPPING_EXACT"
                or not isinstance(selectors, Sequence)
                or isinstance(selectors, (str, bytes))
                or len(selectors) != 1
                or not isinstance(selectors[0], str)
                or not selectors[0].endswith(".failure")
            ):
                continue
            expected = criterion.get("expected_value")
            if not isinstance(expected, Mapping):
                raise ValueError("failure mapping must be an object")
            field = expected.get("field")
            reason = expected.get("reason")
            if type(field) is not str or type(reason) is not str:
                raise ValueError("failure mapping requires field and reason")
            try:
                durable_required = _FAILURE_DURABILITY_BY_SHAPE[(field, reason)]
            except KeyError as error:
                raise ValueError("failure mapping has no frozen runtime error contract") from error
            has_durable = "durable_committed" in expected
            if durable_required is None:
                if has_durable:
                    raise ValueError("ingress refusal must omit durable_committed")
            elif expected.get("durable_committed") is not durable_required:
                raise ValueError("lifecycle failure has wrong durable_committed value")


def validate_frozen_instrument_counts(
    *,
    expected_manifest: Mapping[str, object],
    evidence_obligations_manifest: Mapping[str, object],
    schedule_manifest: Mapping[str, object],
) -> None:
    """Prevent silent scientific-arm or criterion-count drift."""

    expected_blocks = expected_manifest.get("blocks")
    obligation_blocks = evidence_obligations_manifest.get("blocks")
    schedule_blocks = schedule_manifest.get("blocks")
    if not all(isinstance(value, Mapping) for value in (
        expected_blocks, obligation_blocks, schedule_blocks
    )):
        raise ValueError("Phase-13 manifests require block mappings")
    primary_count = sum(
        len(block["criteria"])
        for block in expected_blocks.values()
        if isinstance(block, Mapping) and isinstance(block.get("criteria"), Sequence)
    )
    obligation_count = sum(
        len(block["criteria"])
        for block in obligation_blocks.values()
        if isinstance(block, Mapping) and isinstance(block.get("criteria"), Sequence)
    )
    arm_count = sum(
        len(block["arms"])
        for block in schedule_blocks.values()
        if isinstance(block, Mapping) and isinstance(block.get("arms"), Mapping)
    )
    if (
        arm_count != _FROZEN_FORMAL_ARM_COUNT
        or primary_count != _FROZEN_PRIMARY_CRITERIA_COUNT
        or obligation_count != _FROZEN_EVIDENCE_OBLIGATION_COUNT
        or primary_count + obligation_count != _FROZEN_TOTAL_CRITERIA_COUNT
    ):
        raise ValueError("Phase-13 frozen arm or criterion count drift")


def _load_provenance_sources() -> dict[str, tuple[dict[str, object], ...]]:
    registry = load_manifest(AUTHORITY_CLAUSE_REGISTRY_PATH)
    mapping = load_manifest(CRITERION_PROVENANCE_MANIFEST_PATH)
    if registry.get("schema_id") != "brainvision.phase13.authority_clause_registry.v1":
        raise ValueError("unexpected authority-clause registry schema")
    if mapping.get("schema_id") != "brainvision.phase13.criterion_provenance_manifest.v1":
        raise ValueError("unexpected criterion-provenance manifest schema")
    documents = registry.get("documents")
    clauses = registry.get("clauses")
    block_clause_ids = mapping.get("block_clause_ids")
    if not isinstance(documents, Mapping) or not isinstance(clauses, Mapping) or not isinstance(block_clause_ids, Mapping):
        raise ValueError("criterion provenance manifests are malformed")
    require_exact_block_ids(block_clause_ids)
    repository_root = PACKAGE_DIR.parents[1]
    for document_id, record in documents.items():
        if type(document_id) is not str or not isinstance(record, Mapping):
            raise ValueError("authority registry document is malformed")
        path_value = record.get("path")
        digest = record.get("sha256")
        if type(path_value) is not str or type(digest) is not str:
            raise ValueError("authority registry document requires path and SHA-256")
        path = repository_root / path_value
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("authority registry document hash mismatch")
    resolved: dict[str, tuple[dict[str, object], ...]] = {}
    for block_id in BLOCK_IDS:
        clause_ids = block_clause_ids[block_id]
        if not isinstance(clause_ids, Sequence) or isinstance(clause_ids, (str, bytes)) or not clause_ids:
            raise ValueError("every block requires one or more authority clause IDs")
        sources: list[dict[str, object]] = []
        for clause_id in clause_ids:
            clause = clauses.get(clause_id)
            if type(clause_id) is not str or not isinstance(clause, Mapping):
                raise ValueError("criterion provenance references an unknown clause")
            clause_sources = clause.get("sources")
            if not isinstance(clause_sources, Sequence) or isinstance(clause_sources, (str, bytes)) or not clause_sources:
                raise ValueError("authority clause requires sources")
            for source in clause_sources:
                if not isinstance(source, Mapping) or source.get("document") not in documents:
                    raise ValueError("authority source references an unknown document")
                if any(type(source.get(field)) is not str or not source[field] for field in ("document", "section", "semantic_role")):
                    raise ValueError("authority source is incomplete")
                document = documents[source["document"]]
                assert isinstance(document, Mapping)
                sources.append(
                    {
                        "clause_id": clause_id,
                        "document_path": document["path"],
                        "document_sha256": document["sha256"],
                        "section": source["section"],
                        "semantic_role": source["semantic_role"],
                    }
                )
        resolved[block_id] = tuple(sources)
    return resolved


def _criterion_kind(criterion: Mapping[str, object], *, is_evidence_obligation: bool) -> str:
    if is_evidence_obligation:
        return "EVIDENCE_COMPLETENESS"
    if criterion.get("relation") == "AUTHORITY_ONLY_STRUCTURAL_REPRODUCTION_REFERENCE":
        return "AUTHORITY_ONLY_REFERENCE"
    return (
        "SCIENTIFIC_CRITERION"
        if criterion.get("failure_class") == "FAIL_SCIENTIFIC"
        else "IMPLEMENTATION_CRITERION"
    )


def _annotate_criteria(
    criteria: Sequence[object], *, sources: Sequence[Mapping[str, object]], is_evidence_obligation: bool
) -> list[dict[str, object]]:
    annotated: list[dict[str, object]] = []
    for criterion in criteria:
        if not isinstance(criterion, Mapping):
            raise ValueError("criterion must be an object")
        annotated.append(
            {
                **dict(criterion),
                "authority_sources": [dict(source) for source in sources],
                "obligation_kind": _criterion_kind(
                    criterion, is_evidence_obligation=is_evidence_obligation
                ),
            }
        )
    return annotated


def load_complete_expected_result_manifest() -> dict[str, object]:
    """Combine frozen primary outcomes with manifest-owned evidence obligations."""
    primary = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)
    obligations = load_manifest(EVIDENCE_OBLIGATIONS_MANIFEST_PATH)
    validate_expected_result_manifest(primary)
    if primary.get("evidence_obligations_manifest") != EVIDENCE_OBLIGATIONS_MANIFEST_PATH.name:
        raise ValueError("primary expected manifest does not bind the evidence-obligations manifest")
    if obligations.get("schema_id") != "brainvision.phase13.evidence_obligations_manifest.v1":
        raise ValueError("unexpected evidence-obligations manifest schema")
    obligation_blocks = obligations.get("blocks")
    primary_blocks = primary.get("blocks")
    if not isinstance(obligation_blocks, Mapping) or not isinstance(primary_blocks, Mapping):
        raise ValueError("evidence-obligations manifest requires blocks")
    require_exact_block_ids(obligation_blocks)
    provenance_by_block = _load_provenance_sources()
    combined_blocks: dict[str, object] = {}
    for block_id in BLOCK_IDS:
        primary_block = primary_blocks[block_id]
        obligation_block = obligation_blocks[block_id]
        if not isinstance(primary_block, Mapping) or not isinstance(obligation_block, Mapping):
            raise ValueError("combined expected block must be a mapping")
        if type(obligation_block.get("authority_trace")) is not str:
            raise ValueError("each evidence-obligations block must trace frozen authority")
        additional = obligation_block.get("criteria")
        if not isinstance(additional, Sequence) or isinstance(additional, (str, bytes)):
            raise ValueError("evidence-obligations criteria must be an array")
        primary_criteria = primary_block.get("criteria")
        additional = obligation_block.get("criteria")
        if not isinstance(primary_criteria, Sequence) or isinstance(primary_criteria, (str, bytes)):
            raise ValueError("primary criteria must be an array")
        if not isinstance(additional, Sequence) or isinstance(additional, (str, bytes)):
            raise ValueError("evidence-obligations criteria must be an array")
        combined_blocks[block_id] = {
            **dict(primary_block),
            "criteria": [
                *_annotate_criteria(
                    primary_criteria,
                    sources=provenance_by_block[block_id],
                    is_evidence_obligation=False,
                ),
                *_annotate_criteria(
                    additional,
                    sources=provenance_by_block[block_id],
                    is_evidence_obligation=True,
                ),
            ],
        }
    combined = {
        "schema_id": "brainvision.phase13.complete_expected_result_manifest.v1",
        "blocks": combined_blocks,
    }
    # Reuse the strict criterion validator with its expected external schema.
    validate_expected_result_manifest(
        {"schema_id": "brainvision.phase13.expected_result_manifest.v2", "blocks": combined_blocks},
        require_provenance=True,
    )
    return combined


def validate_schedule_manifest(payload: Mapping[str, object]) -> None:
    from brainvision_phase13.backend import FAULT_IDS, validate_schedule_handler_completeness

    if payload.get("schema_id") != "brainvision.phase13.schedule_manifest.v2":
        raise ValueError("unexpected schedule manifest schema")
    blocks = payload.get("blocks")
    if not isinstance(blocks, Mapping):
        raise ValueError("schedule manifest requires blocks")
    require_exact_block_ids(blocks)
    observation_defaults = payload.get("observation_defaults")
    if not isinstance(observation_defaults, Mapping):
        raise ValueError("schedule must bind observation_defaults")
    resolve_effective_observation_spec(
        observation_defaults,
        {"fixture_id": "d0", "source_sequence": 0},
    )
    if tuple(payload.get("fault_ids", ())) != tuple(sorted(FAULT_IDS)):
        raise ValueError("schedule fault IDs do not match the frozen backend vocabulary")
    required_arm_ids = payload.get("required_arm_ids")
    if not isinstance(required_arm_ids, Mapping):
        raise ValueError("schedule must declare every frozen arm")
    require_exact_block_ids(required_arm_ids)
    lineages: set[str] = set()
    lineage_specs: dict[str, Mapping[str, object]] = {}
    for block_id, block in blocks.items():
        if not isinstance(block, Mapping):
            raise ValueError(f"{block_id} schedule block must be an object")
        arms = block.get("arms")
        if not isinstance(arms, Mapping) or not arms:
            raise ValueError(f"{block_id} needs explicitly named arms")
        required_arms = required_arm_ids[block_id]
        if not isinstance(required_arms, Sequence) or isinstance(required_arms, (str, bytes)):
            raise ValueError(f"{block_id} required arms must be an array")
        if tuple(arms) != tuple(required_arms):
            raise ValueError(f"{block_id} arm coverage differs from frozen schedule")
        for arm_name, arm in arms.items():
            if type(arm_name) is not str or not isinstance(arm, Mapping):
                raise ValueError("arm IDs and arm documents must be mappings")
            commands = arm.get("commands")
            if not isinstance(commands, Sequence) or isinstance(commands, (str, bytes)) or not commands:
                raise ValueError(f"{block_id}/{arm_name} needs complete structured commands")
            for command in commands:
                if not isinstance(command, Mapping):
                    raise ValueError("schedule command must be an object")
                _validate_command(command, lineages, observation_defaults)
                if command.get("operation") == "CREATE_LINEAGE":
                    candidate = command.get("spec")
                    assert isinstance(candidate, Mapping)
                    lineage = command.get("lineage")
                    assert type(lineage) is str
                    lineage_specs[lineage] = candidate
                elif command.get("operation") == "ADMIT":
                    lineage = command.get("lineage")
                    assert type(lineage) is str
                    lineage_spec = lineage_specs.get(lineage)
                    if lineage_spec is None:
                        raise ValueError("ADMIT must resolve a lineage configuration")
                    observation = command.get("observation")
                    assert isinstance(observation, Mapping)
                    resolved = resolve_effective_observation_spec(
                        observation_defaults, observation
                    )
                    if resolved["adapter_contract_id"] != lineage_spec["adapter_contract_id"]:
                        raise ValueError(
                            "ADMIT adapter_contract_id must match its lineage configuration"
                        )
    if payload.get("administered_sink_purity_depth") != 2:
        raise ValueError("schedule must bind the frozen E11 sink-purity depth")
    e11 = blocks["E11"]
    assert isinstance(e11, Mapping)
    e11_arms = e11["arms"]
    assert isinstance(e11_arms, Mapping)
    for arm in e11_arms.values():
        assert isinstance(arm, Mapping)
        commands = arm["commands"]
        assert isinstance(commands, Sequence)
        close_index = next(
            (index for index, command in enumerate(commands) if command.get("operation") == "CLOSE_HOST"),
            len(commands),
        )
        initial_admits = sum(
            1 for command in commands[:close_index] if command.get("operation") == "ADMIT"
        )
        if initial_admits != 2:
            raise ValueError("E11 initial segment must contain exactly two admissions")
    rendered_schedule = canonical_json_bytes(payload).decode("ascii")
    if '"e10"' in rendered_schedule or '"e11"' in rendered_schedule or '"e12"' in rendered_schedule:
        raise ValueError("obsolete E10/E11/E12 stream alias remains in schedule")
    _command_checkpoints(payload)
    if "TODO" in rendered_schedule or "PLACEHOLDER" in rendered_schedule:
        raise ValueError("placeholder remains in schedule")
    validate_schedule_handler_completeness(payload)


def validate_fixture_schedule_boundary(
    fixture_manifest: Mapping[str, object], schedule_manifest: Mapping[str, object]
) -> None:
    """Keep fixture facts unable to override formal observation envelopes."""
    if "observation_envelope_defaults" in fixture_manifest:
        raise ValueError("fixture manifest must not declare formal observation defaults")
    resolved = resolved_schedule_commands(schedule_manifest)
    for commands in resolved.values():
        for command in commands:
            if command.get("operation") == "ADMIT":
                observation = command.get("observation")
                if not isinstance(observation, Mapping) or set(observation) != _OBSERVATION_COMMAND_FIELDS:
                    raise ValueError("every formal ADMIT must resolve only schedule-owned metadata")


def validate_authority_manifest(payload: Mapping[str, object]) -> None:
    if payload.get("schema_id") != "brainvision.phase13.authority_manifest.v1":
        raise ValueError("unexpected authority manifest schema")
    if "formal_administration_head" in payload:
        raise ValueError("authority manifest must not contain a self-referential HEAD")
    expected = {
        "modulation_mapping_id": MODULATION_MAPPING_ID,
        "modulation_profile_schema_id": MODULATION_PROFILE_SCHEMA_ID,
        "modulation_schema_id": MODULATION_SCHEMA_ID,
        "observation_schema_id": OBSERVATION_SCHEMA_ID,
        "observation_identity_schema_id": IDENTITY_SCHEMA_ID,
        "operator_id": OPERATOR_ID,
        "projection_id": PROJECTION_ID,
        "projection_schema_id": PROJECTION_SCHEMA_ID,
        "rounding_algorithm_id": RNE_ALGORITHM_ID,
        "theta_profile_ids": {"-1": modulation_profile_id(-1), "0": modulation_profile_id(0), "1": modulation_profile_id(1)},
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"authority manifest mismatch: {key}")
    expected_fixture_hashes = {
        "d0": sha256(D0.to_canonical_json_bytes()).hexdigest(),
        "dA": sha256(DA.to_canonical_json_bytes()).hexdigest(),
        "dB": sha256(DB.to_canonical_json_bytes()).hexdigest(),
    }
    if payload.get("phase2_fixture_sha256s") != expected_fixture_hashes:
        raise ValueError("authority manifest mismatch: phase2_fixture_sha256s")
    repository_root = PACKAGE_DIR.parents[1]
    for field, expected_path in (
        ("phase13_specification", "docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md"),
        ("phase13_bindings", "docs/TORMENT_BRAINVISION_PHASE_13_FORMAL_ADMINISTRATION_BINDINGS_v1.0.md"),
    ):
        record = payload.get(field)
        if not isinstance(record, Mapping) or record.get("path") != expected_path:
            raise ValueError(f"authority manifest mismatch: {field} path")
        path = repository_root / expected_path
        if not path.is_file() or record.get("sha256") != sha256(path.read_bytes()).hexdigest():
            raise ValueError(f"authority manifest mismatch: {field} hash")


def validate_graph_completeness(
    *, fixture_manifest: Mapping[str, object], expected_manifest: Mapping[str, object],
    schedule_manifest: Mapping[str, object], authority_manifest: Mapping[str, object],
) -> None:
    from brainvision_phase13.backend import validate_backend_manifest_bindings

    validate_backend_manifest_bindings(
        fixture_manifest=fixture_manifest,
        expected_manifest=expected_manifest,
        schedule_manifest=schedule_manifest,
        authority_manifest=authority_manifest,
    )
    checkpoints = _command_checkpoints(schedule_manifest)
    blocks = expected_manifest["blocks"]
    assert isinstance(blocks, Mapping)
    for block in blocks.values():
        assert isinstance(block, Mapping)
        criteria = block["criteria"]
        assert isinstance(criteria, Sequence)
        for criterion in criteria:
            assert isinstance(criterion, Mapping)
            for selector in criterion["actual_selectors"]:
                assert isinstance(selector, str)
                if selector.startswith("checkpoints."):
                    checkpoint = selector.split(".", 2)[1]
                    if checkpoint not in checkpoints:
                        raise ValueError(f"criterion references missing checkpoint: {checkpoint}")


def validate_all_manifests() -> dict[str, str]:
    """Validate the frozen graph without instantiating or executing an arm."""
    fixture = load_manifest(FIXTURE_MANIFEST_PATH)
    validate_fixture_manifest(fixture)
    expected = load_manifest(EXPECTED_RESULT_MANIFEST_PATH)
    obligations = load_manifest(EVIDENCE_OBLIGATIONS_MANIFEST_PATH)
    schedule = load_manifest(SCHEDULE_MANIFEST_PATH)
    authority = load_manifest(AUTHORITY_MANIFEST_PATH)
    validate_expected_result_manifest(expected)
    validate_failure_evidence_shapes(expected)
    validate_frozen_instrument_counts(
        expected_manifest=expected,
        evidence_obligations_manifest=obligations,
        schedule_manifest=schedule,
    )
    complete_expected = load_complete_expected_result_manifest()
    validate_schedule_manifest(schedule)
    validate_fixture_schedule_boundary(fixture, schedule)
    validate_authority_manifest(authority)
    validate_graph_completeness(
        fixture_manifest=fixture,
        expected_manifest=complete_expected,
        schedule_manifest=schedule,
        authority_manifest=authority,
    )
    return {
        "authority_manifest": manifest_sha256(AUTHORITY_MANIFEST_PATH),
        "expected_result_manifest": manifest_sha256(EXPECTED_RESULT_MANIFEST_PATH),
        "evidence_obligations_manifest": manifest_sha256(EVIDENCE_OBLIGATIONS_MANIFEST_PATH),
        "authority_clause_registry": manifest_sha256(AUTHORITY_CLAUSE_REGISTRY_PATH),
        "criterion_provenance_manifest": manifest_sha256(CRITERION_PROVENANCE_MANIFEST_PATH),
        "fixture_manifest": manifest_sha256(FIXTURE_MANIFEST_PATH),
        "schedule_manifest": manifest_sha256(SCHEDULE_MANIFEST_PATH),
    }


def canonical_manifest_identity(payload: Mapping[str, object]) -> str:
    return sha256_hex(canonical_json_bytes(payload))


__all__ = (
    "AUTHORITY_CLAUSE_REGISTRY_PATH", "AUTHORITY_MANIFEST_PATH", "CRITERION_PROVENANCE_MANIFEST_PATH", "EVIDENCE_OBLIGATIONS_MANIFEST_PATH", "EXPECTED_RESULT_MANIFEST_PATH", "FIXTURE_MANIFEST_PATH",
    "SCHEDULE_MANIFEST_PATH", "canonical_manifest_identity", "load_manifest", "manifest_sha256",
    "load_complete_expected_result_manifest", "resolve_effective_observation_spec", "resolved_schedule_commands",
    "validate_all_manifests", "validate_authority_manifest", "validate_expected_result_manifest",
    "validate_failure_evidence_shapes", "validate_frozen_instrument_counts",
    "validate_fixture_schedule_boundary", "validate_graph_completeness", "validate_schedule_manifest",
)
