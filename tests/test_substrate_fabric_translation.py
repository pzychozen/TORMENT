"""Phase 7G5A3C1 pure Fabric structural translation qualification."""
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from torment_service.collective_models import MemoryGovernanceFlags
from torment_service.governance import (
    allows_collective_reingest,
    is_compression_protected,
    is_decay_accelerated,
    should_emit_packet,
)
from torment_service.provenance_v1 import (
    SOURCE_CLOSURE_COMMIT,
    SOURCE_COLLECTIVE_ECHO,
    SOURCE_ENVIRONMENT_OBSERVED,
    SOURCE_ENVIRONMENT_USER_ASSERTED,
    SOURCE_ROLE_OUTPUT,
    SOURCE_TOOL_RESULT,
    SOURCE_USER_INPUT,
    VALID_SOURCE_TYPES,
    VALID_WRITE_PATHS,
    WRITE_CLOSURE_COMMIT,
    WRITE_COGNITION_WRITEBACK,
    WRITE_COLLECTIVE_REINGEST,
    WRITE_DIRECT_INGEST,
    WRITE_REFLECTION_WRITEBACK,
    WRITE_TOOL_INGEST,
    ProvenanceV1,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.fabric_translation import (
    ABSENT,
    QUALIFIED_COMPAT_LINK_INTENT,
    UNRESOLVED_LEGACY_LINK_REFERENCE,
    FabricStructuralTranslationRequest,
    QualifiedCompatibilityLinkTarget,
    prepare_flexible_payload,
    project_legacy_governance,
    project_legacy_scope,
    translate_fabric_structural,
    translate_governance_flags,
    translate_provenance_v1,
)
from torment_service.substrate.schema import create_schema


def _provenance(**overrides) -> ProvenanceV1:
    values = {
        "source_type": SOURCE_USER_INPUT,
        "write_path": WRITE_DIRECT_INGEST,
        "created_at_step": 17,
        "created_at_ts": "2026-08-30T12:34:56Z",
    }
    values.update(overrides)
    return ProvenanceV1(**values)


def _request(**overrides) -> FabricStructuralTranslationRequest:
    values = {
        "workspace_id": "ws",
        "scope": "private",
        "agent_id": "agent-a",
        "legacy_source_namespace_id": uuid4(),
        "identity_namespace_id": uuid4(),
        "semantic_scope_id": uuid4(),
        "provenance": _provenance(),
        "governance": MemoryGovernanceFlags(),
    }
    values.update(overrides)
    return FabricStructuralTranslationRequest(**values)


def _governance_payload(governance: MemoryGovernanceFlags) -> dict:
    return {"governance": governance.to_dict()}


def test_private_scope_translation_and_projection_are_exact_and_immutable():
    result = translate_fabric_structural(_request())

    assert result.runtime_scope.scope_kind == "PRIVATE_AGENT"
    assert result.runtime_scope.workspace_id == "ws"
    assert result.runtime_scope.agent_id == "agent-a"
    assert result.runtime_scope.domain_id is None
    assert dict(result.legacy_scope_projection) == {
        "scope": "private",
        "workspace_id": "ws",
        "agent_id": "agent-a",
    }
    assert project_legacy_scope(result.runtime_scope) == dict(result.legacy_scope_projection)
    with pytest.raises(TypeError):
        result.legacy_scope_projection["scope"] = "shared"  # type: ignore[index]


def test_shared_scope_translation_and_projection_are_exact():
    result = translate_fabric_structural(
        _request(scope="shared", agent_id=None, domain_id="research")
    )

    assert result.runtime_scope.scope_kind == "SHARED_DOMAIN"
    assert result.runtime_scope.workspace_id == "ws"
    assert result.runtime_scope.agent_id is None
    assert result.runtime_scope.domain_id == "research"
    assert dict(result.legacy_scope_projection) == {
        "scope": "shared",
        "workspace_id": "ws",
        "domain_id": "research",
    }


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent_id": None},
        {"domain_id": "research"},
        {"scope": "shared", "agent_id": "agent-a", "domain_id": None},
        {"scope": "shared", "agent_id": "agent-a", "domain_id": "research"},
        {"scope": "unknown"},
    ],
)
def test_invalid_scope_combinations_fail_closed(overrides):
    with pytest.raises(ValueError):
        _request(**overrides)


def test_flexible_payload_retains_ordinary_fields_and_refuses_structural_shadows():
    assert prepare_flexible_payload({"affect": {"mood": "curious"}, "srg": 0.4}) == {
        "affect": {"mood": "curious"},
        "srg": 0.4,
    }
    for key in (
        "scope",
        "semantic_scope_id",
        "provenance",
        "provenance_id",
        "governance",
        "governance_state",
        "lifecycle_state",
        "authority_category",
        "operation_id",
        "transition_id",
        "representation_readiness",
        "integrity_measurement",
    ):
        with pytest.raises(ValueError):
            prepare_flexible_payload({key: "shadow"})


@pytest.mark.parametrize(
    ("label", "provenance"),
    [
        ("plain user ingest", _provenance()),
        (
            "tool result",
            _provenance(source_type=SOURCE_TOOL_RESULT, write_path=WRITE_TOOL_INGEST, tool_name="tool"),
        ),
        (
            "role output cognition writeback",
            _provenance(
                source_type=SOURCE_ROLE_OUTPUT,
                source_role="archivist",
                write_path=WRITE_COGNITION_WRITEBACK,
            ),
        ),
        ("reflection writeback", _provenance(write_path=WRITE_REFLECTION_WRITEBACK)),
        (
            "collective echo reinjest",
            _provenance(source_type=SOURCE_COLLECTIVE_ECHO, write_path=WRITE_COLLECTIVE_REINGEST),
        ),
        (
            "closure origin",
            _provenance(source_type=SOURCE_CLOSURE_COMMIT, write_path=WRITE_CLOSURE_COMMIT),
        ),
        (
            "character scoped",
            _provenance(character_id="character-1", character_name="Scout", character_scope="active_context"),
        ),
        (
            "environment asserted",
            _provenance(source_type=SOURCE_ENVIRONMENT_USER_ASSERTED, asserted_by="user"),
        ),
        (
            "environment observed",
            _provenance(source_type=SOURCE_ENVIRONMENT_OBSERVED, observation_source="sensor"),
        ),
    ],
)
def test_provenance_categories_preserve_structural_and_descriptive_fields(label, provenance):
    del label
    result = translate_provenance_v1(provenance)
    descriptive = json.loads(result.descriptive_notes)

    assert result.origin_kind == "RUNTIME_PROVENANCE_V1"
    assert result.source_channel == provenance.source_type
    assert result.source_role == provenance.source_role
    assert result.derivation_status == provenance.write_path
    assert result.uncertainty_state == "UNKNOWN"
    assert result.source_time_ns is None
    assert result.capture_time_ns == 1_788_093_296_000_000_000
    assert result.memory_role is None
    assert descriptive["format"] == "TORMENT_PROVENANCE_V1_DESCRIPTIVE/1"
    assert descriptive["provenance_v1"] == provenance.to_dict()


@pytest.mark.parametrize("source_type", sorted(VALID_SOURCE_TYPES))
def test_every_valid_source_type_maps_to_the_source_channel(source_type):
    values = {
        "source_type": source_type,
        "source_role": "role" if source_type == SOURCE_ROLE_OUTPUT else None,
    }
    if source_type == "gate1_unrecoverable":
        values.update(
            admission_refused=True,
            admission_reason="GATE1",
            admission_policy_version="test",
        )
    provenance = _provenance(
        **values,
    )
    assert translate_provenance_v1(provenance).source_channel == source_type


@pytest.mark.parametrize("write_path", sorted(VALID_WRITE_PATHS))
def test_every_valid_write_path_maps_without_loss(write_path):
    provenance = _provenance(write_path=write_path)
    result = translate_provenance_v1(provenance)
    assert result.derivation_status == write_path
    assert json.loads(result.descriptive_notes)["provenance_v1"]["write_path"] == write_path


def test_provenance_encoding_is_canonical_and_has_no_translation_clock():
    first = _provenance(
        parent_eids=[5, 2, 5, 7],
        notes="stable",
        session_id="session",
        tool_name="tool",
    )
    second = _provenance(
        parent_eids=[5, 2, 5, 7],
        notes="stable",
        session_id="session",
        tool_name="tool",
    )

    translated_first = translate_provenance_v1(first)
    translated_second = translate_provenance_v1(second)
    description = json.loads(translated_first.descriptive_notes)
    assert translated_first.descriptive_notes == translated_second.descriptive_notes
    assert translated_first.capture_time_ns == translated_second.capture_time_ns
    assert description["provenance_v1"]["parent_eids"] == [5, 2, 7]
    assert description["parent_eids_classification"] == "UNRESOLVED_NAMESPACED_LEGACY_LINEAGE_EVIDENCE"


def test_revalidation_normalises_mutated_parent_eids_before_descriptive_encoding():
    provenance = _provenance()
    provenance.parent_eids = [5, 2, 5, 7]

    translated = translate_provenance_v1(provenance)
    assert json.loads(translated.descriptive_notes)["provenance_v1"]["parent_eids"] == [5, 2, 7]


def test_absent_provenance_timestamp_stays_absent_without_a_translation_clock():
    provenance = _provenance()
    provenance.created_at_ts = None

    result = translate_provenance_v1(provenance)
    assert result.capture_time_ns is None
    assert json.loads(result.descriptive_notes)["provenance_v1"]["created_at_ts"] is None


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: setattr(value, "source_type", "invalid"),
        lambda value: setattr(value, "write_path", "invalid"),
        lambda value: (setattr(value, "source_type", SOURCE_ROLE_OUTPUT), setattr(value, "source_role", None)),
        lambda value: setattr(value, "character_scope", "invalid"),
        lambda value: setattr(value, "created_at_ts", "not-a-timestamp"),
    ],
)
def test_mutated_or_malformed_provenance_fails_closed(mutator):
    provenance = _provenance()
    mutator(provenance)
    with pytest.raises(ValueError):
        translate_provenance_v1(provenance)
    with pytest.raises(ValueError):
        translate_provenance_v1({})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "governance",
    [
        MemoryGovernanceFlags(),
        MemoryGovernanceFlags(protected=True),
        MemoryGovernanceFlags(non_shareable=True),
        MemoryGovernanceFlags(collective_export_blocked=True),
        MemoryGovernanceFlags(collective_reingest_blocked=True),
        MemoryGovernanceFlags(decay_accelerated=True),
        MemoryGovernanceFlags(True, True, True, True, True),
        MemoryGovernanceFlags(True, False, True, False, True),
    ],
)
def test_governance_mapping_is_exact_including_all_false(governance):
    facts = translate_governance_flags(governance)
    assert facts.as_storage_tuple() == (
        int(governance.protected),
        int(governance.non_shareable),
        int(governance.collective_export_blocked),
        int(governance.collective_reingest_blocked),
        int(governance.decay_accelerated),
    )
    assert project_legacy_governance(facts).to_dict() == governance.to_dict()


@pytest.mark.parametrize(
    "governance",
    [
        MemoryGovernanceFlags(),
        MemoryGovernanceFlags(protected=True),
        MemoryGovernanceFlags(non_shareable=True, collective_export_blocked=True),
        MemoryGovernanceFlags(collective_reingest_blocked=True, decay_accelerated=True),
        MemoryGovernanceFlags(True, True, True, True, True),
    ],
)
def test_governance_projection_preserves_legacy_behavioral_decisions(governance):
    projected = project_legacy_governance(translate_governance_flags(governance))
    legacy_payload = _governance_payload(governance)
    projected_payload = _governance_payload(projected)

    assert should_emit_packet(legacy_payload) == should_emit_packet(projected_payload)
    assert allows_collective_reingest(legacy_payload) == allows_collective_reingest(projected_payload)
    assert is_decay_accelerated(legacy_payload) == is_decay_accelerated(projected_payload)
    assert is_compression_protected(legacy_payload) == is_compression_protected(projected_payload)


def test_lifecycle_and_governance_remain_separate_structural_inputs():
    unprotected = translate_fabric_structural(_request(governance=MemoryGovernanceFlags()))
    protected = translate_fabric_structural(_request(governance=MemoryGovernanceFlags(protected=True)))

    assert unprotected.governance.protected is False
    assert protected.governance.protected is True
    assert not hasattr(unprotected.governance, "lifecycle_state")
    with pytest.raises(ValueError):
        prepare_flexible_payload({"lifecycle_state": "PROTECTED"})


@pytest.mark.parametrize(
    ("raw_links", "classification", "expected"),
    [
        (None, ABSENT, ()),
        ([], ABSENT, ()),
        (["memory-about-project-x"], UNRESOLVED_LEGACY_LINK_REFERENCE, ("memory-about-project-x",)),
        (["12"], UNRESOLVED_LEGACY_LINK_REFERENCE, ("12",)),
        (["foo", "12", "bar"], UNRESOLVED_LEGACY_LINK_REFERENCE, ("foo", "12", "bar")),
    ],
)
def test_raw_links_are_unresolved_evidence_with_original_order(raw_links, classification, expected):
    result = translate_fabric_structural(_request(raw_links=raw_links))
    assert result.link_classification == classification
    assert tuple(item.raw_reference for item in result.unresolved_link_references) == expected
    assert tuple(item.source_index for item in result.unresolved_link_references) == tuple(range(len(expected)))
    assert result.qualified_link_intents == ()


def test_qualified_link_intent_is_distinguishable_from_raw_string_eid():
    namespace = uuid4()
    qualified = translate_fabric_structural(
        _request(qualified_link_targets=[QualifiedCompatibilityLinkTarget(namespace, 12)])
    )
    raw = translate_fabric_structural(_request(raw_links=["12"]))

    assert qualified.link_classification == QUALIFIED_COMPAT_LINK_INTENT
    assert qualified.qualified_link_intents[0].classification == QUALIFIED_COMPAT_LINK_INTENT
    assert qualified.qualified_link_intents[0].target_legacy_source_namespace_id == namespace
    assert qualified.qualified_link_intents[0].target_eid == 12
    assert raw.link_classification == UNRESOLVED_LEGACY_LINK_REFERENCE
    assert raw.qualified_link_intents == ()


def test_translation_never_changes_semantic_row_counts(tmp_path):
    qualified = open_temporary_test_connection(tmp_path / "translation-purity.db")
    try:
        create_schema(qualified.connection)
        tables = (
            "objects",
            "object_revisions",
            "object_revision_governance",
            "relationships",
            "relationship_revisions",
            "provenance_records",
            "representations",
            "operations",
            "semantic_transitions",
        )
        before = {
            table: qualified.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }

        translate_fabric_structural(
            _request(
                raw_links=["12"],
                qualified_link_targets=[QualifiedCompatibilityLinkTarget(uuid4(), 3)],
            )
        )

        after = {
            table: qualified.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        assert after == before
    finally:
        qualified.close()
