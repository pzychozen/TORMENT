"""Focused A3C3 qualification for native reinforcement continuity."""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID, uuid4

import numpy as np
import pytest

from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import (
    SubstrateIdempotencyConflict,
    SubstrateInvariantViolation,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.memory_motif_composition import (
    NativeMemoryMotifCompositionRequest,
    NativeMemoryMotifCompositionService,
)
from torment_service.substrate.memory_reinforcement import (
    NativeMemoryReinforcementRequest,
    NativeMemoryReinforcementService,
    StaleReinforcementPlanError,
    realize_reinforcement_patch,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
)
from torment_service.substrate.provenance import NativeProvenanceRecord
from torment_service.substrate.representations import (
    INTEGRITY_ALGORITHM_SHA256,
    INTEGRITY_VALUE_ENCODING_RAW,
    NativeRepresentationService,
    RepresentationFailureRequest,
    RepresentationIntegrityExpectationRequest,
    RepresentationIntegrityVerificationRequest,
    RepresentationReadyRequest,
    RepresentationRequest,
)
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3c3.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    values = {
        "qualified": qualified,
        "connection": connection,
        "memory_identity": _id(),
        "motif_identity": _id(),
        "membership_identity": _id(),
        "scope": _id(),
        "idempotency": _id(),
        "memory_alias": _id(),
        "motif_alias": _id(),
    }
    for key, label in (
        ("memory_identity", "a3c3-memory-identity"),
        ("motif_identity", "a3c3-motif-identity"),
        ("membership_identity", "a3c3-membership-identity"),
    ):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[key]), label))
    connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(values["scope"]), "a3c3-scope"))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(values["idempotency"]), "a3c3-idempotency"))
    for key, label in (("memory_alias", "a3c3-memory-alias"), ("motif_alias", "a3c3-motif-alias")):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(values[key]), label))
    return values


def _composition_request(values, *, key="compose", source_channel="user_input", strength=0.7):
    return NativeMemoryMotifCompositionRequest(
        legacy_source_namespace_id=values["memory_alias"], memory_identity_namespace_id=values["memory_identity"],
        semantic_scope_id=values["scope"], summary="reinforce fixture", memory_type="reflection", memory_class="core",
        strength=strength, confidence=0.8, half_life_days=7.0, user_id="aria", logical_step=10,
        flexible_payload={"state_symbol": "◈", "symbol_trace": ["◯", "◈"], "resonance_score": 0.5},
        lifecycle_state="ORDINARY", lifecycle_authoritative=False, governance_state="DERIVED",
        provenance=NativeProvenanceRecord("DIRECT", source_channel, "user", "DIRECT", "KNOWN", 1, 2, "INPUT", "fixture"),
        governance=NativeMemoryGovernanceFacts(protected=True, non_shareable=True),
        motif_alias_namespace_id=values["motif_alias"], motif_identity_namespace_id=values["motif_identity"],
        membership_identity_namespace_id=values["membership_identity"], domain_id="research", agent_id="aria",
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        incoming_embedding=(2.0, 0.6, 0.0), attach_threshold=0.72, created_ts=10, last_active_ts=11,
        expected_dimension=3,
    )


def _vector_bytes(vector=(2.0, 0.6, 0.0)):
    return np.asarray(vector, dtype=np.float32).tobytes(order="C")


def _ready_e1(values, source, *, key="e1", vector=(2.0, 0.6, 0.0), dependencies=()):
    object_id = source.memory_object_id if hasattr(source, "memory_object_id") else source.object_id
    revision_id = source.memory_revision_id if hasattr(source, "memory_revision_id") else source.revision_id
    payload = _vector_bytes(vector)
    representations = NativeRepresentationService(values["connection"])
    pending = representations.create_representation_pending(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", object_id, revision_id, None, None,
            "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", "float32", 3,
            tuple(dependencies), None, len(payload),
        ),
    )
    representations.establish_representation_integrity_expectation(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return representations.publish_representation_ready(
        idempotency_namespace_id=values["idempotency"], idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(pending.representation_id, "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR", payload),
    )


def _source(values, *, source_channel="user_input", strength=0.7, vector=(2.0, 0.6, 0.0)):
    composition = NativeMemoryMotifCompositionService(values["connection"]).commit(
        NativeMemoryMotifCompositionService(values["connection"]).prepare_plan(
            _composition_request(values, source_channel=source_channel, strength=strength)
        )
    )
    e1 = _ready_e1(values, composition, vector=vector)
    return composition, e1


def _request(values, source, e1, *, key="reinforce", step=20, reinforced_ts=200, tool_ts=None):
    return NativeMemoryReinforcementRequest(
        legacy_source_namespace_id=values["memory_alias"], eid=source.memory_eid,
        expected_revision_id=source.memory_revision_id, expected_representation_id=e1.representation_id,
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        reinforcement_step=step, last_reinforced_ts=reinforced_ts,
        last_tool_refresh_ts=tool_ts, expected_dimension=3,
    )


def _payload(connection, revision_id):
    return json.loads(connection.execute("SELECT payload_text FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(revision_id),)).fetchone()[0])


def _counts(connection):
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "legacy_object_aliases", "provenance_records", "object_revision_governance",
        "relationships", "relationship_revisions", "representations", "representation_dependencies",
        "integrity_expectations", "integrity_measurements", "operations", "semantic_transitions",
    ))


def test_reinforcement_creates_r2_then_exact_e2_without_motif_or_symbol_mutation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        before = _counts(connection)
        result = NativeMemoryReinforcementService(connection).reinforce(_request(values, source, e1))
        r1_payload, r2_payload = _payload(connection, source.memory_revision_id), _payload(connection, result.source.revision_id)
        assert result.source.memory_object_id == source.memory_object_id
        assert result.source.eid == source.memory_eid and result.source.revision_ordinal == 2
        assert r2_payload["strength"] == 0.79 and r2_payload["reinforcement_count"] == 1
        assert (r2_payload["last_reinforced"], r2_payload["last_reinforced_ts"]) == (20, 200)
        assert _payload(connection, source.memory_revision_id) == r1_payload
        for key in ("state_symbol", "symbol_trace", "resonance_score"):
            assert r2_payload[key] == r1_payload[key]
        assert connection.execute(
            "SELECT lineage_kind,predecessor_revision_id,revision_ordinal,provenance_id,lifecycle_state,lifecycle_authoritative,authority_category FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(result.source.revision_id),),
        ).fetchone() == (
            "NATIVE_ORDINARY", native_id_to_bytes(source.memory_revision_id), 2,
            native_id_to_bytes(source.provenance_id), "ORDINARY", 0, "NOT_APPLICABLE",
        )
        governance = NativeObjectRevisionGovernanceService(connection)
        assert governance.get_current_object_governance(object_id=source.memory_object_id).facts == governance.get_object_revision_governance(
            object_id=source.memory_object_id, object_revision_id=source.memory_revision_id, object_revision_ordinal=1,
        ).facts
        e2_bytes = NativeRepresentationService(connection).read_representation_payload(result.e2_representation_id)
        e1_bytes = NativeRepresentationService(connection).read_representation_payload(e1.representation_id)
        assert e2_bytes == e1_bytes and sha256(e2_bytes).digest() == sha256(e1_bytes).digest()
        assert connection.execute(
            "SELECT source_object_id,source_object_revision_id,source_object_revision_ordinal FROM representations WHERE representation_id=?",
            (native_id_to_bytes(result.e2_representation_id),),
        ).fetchone() == (native_id_to_bytes(source.memory_object_id), native_id_to_bytes(result.source.revision_id), 2)
        assert connection.execute("SELECT source_object_revision_id FROM representations WHERE representation_id=?", (native_id_to_bytes(e1.representation_id),)).fetchone()[0] == native_id_to_bytes(source.memory_revision_id)
        assert _counts(connection) == tuple(a + b for a, b in zip(before, (0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 4, 3)))
        assert connection.execute("SELECT count(*) FROM objects WHERE object_kind='DERIVED_MOTIF'", ()).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revisions").fetchone()[0] == 1
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("stop", ("source", "pending", "expectation"))
def test_retry_recovers_r2_and_one_e2_after_each_partial_workflow_boundary(tmp_path: Path, stop: str):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        service = NativeMemoryReinforcementService(values["connection"])
        request = _request(values, source, e1, key=f"partial-{stop}")
        with pytest.raises(RuntimeError):
            service.reinforce(request, _test_stop_after=stop)
        current = NativeMemoryCompatibilityFacade(values["connection"]).get_memory_by_eid(
            legacy_source_namespace_id=values["memory_alias"], eid=source.memory_eid
        )
        assert current.revision_ordinal == 2
        result = service.reinforce(request)
        assert service.reinforce(request) == result
        assert result.source.revision_ordinal == 2
        assert values["connection"].execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.memory_object_id),)).fetchone()[0] == 2
        assert values["connection"].execute("SELECT count(*) FROM representations WHERE source_object_id=?", (native_id_to_bytes(source.memory_object_id),)).fetchone()[0] == 2
    finally:
        values["qualified"].close()


def test_source_only_state_drops_current_search_and_motif_geometry_then_e2_restores_them(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        facade = NativeMemoryCompatibilityFacade(connection)
        reader = NativeMotifRuntimeReader(connection)
        motif_before = connection.execute("SELECT object_id FROM objects WHERE object_kind='DERIVED_MOTIF'").fetchone()[0]
        before_radius = reader.motif_radius(UUID(bytes=motif_before), expected_dimension=3)
        assert [hit.representation_id for hit in facade.search_by_embedding(legacy_source_namespace_id=values["memory_alias"], embedding=(2.0, 0.6, 0.0), dimension=3)] == [e1.representation_id]
        service = NativeMemoryReinforcementService(connection)
        request = _request(values, source, e1, key="source-only")
        with pytest.raises(RuntimeError):
            service.reinforce(request, _test_stop_after="source")
        assert facade.search_by_embedding(legacy_source_namespace_id=values["memory_alias"], embedding=(2.0, 0.6, 0.0), dimension=3) == ()
        assert reader.motif_radius(UUID(bytes=motif_before), expected_dimension=3) != before_radius
        result = service.reinforce(request)
        assert [hit.representation_id for hit in facade.search_by_embedding(legacy_source_namespace_id=values["memory_alias"], embedding=(2.0, 0.6, 0.0), dimension=3)] == [result.e2_representation_id]
        assert reader.motif_radius(UUID(bytes=motif_before), expected_dimension=3) == pytest.approx(before_radius)
        assert connection.execute("SELECT current_revision_ordinal FROM objects WHERE object_id=?", (motif_before,)).fetchone()[0] == 1
    finally:
        values["qualified"].close()


def test_second_authorized_reinforcement_creates_r3_e3_with_same_bytes(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        service = NativeMemoryReinforcementService(values["connection"])
        first = service.reinforce(_request(values, source, e1, key="r2", step=20, reinforced_ts=200))
        second_request = NativeMemoryReinforcementRequest(
            legacy_source_namespace_id=values["memory_alias"], eid=source.memory_eid,
            expected_revision_id=first.source.revision_id, expected_representation_id=first.e2_representation_id,
            idempotency_namespace_id=values["idempotency"], idempotency_key="r3", reinforcement_step=21,
            last_reinforced_ts=201, expected_dimension=3,
        )
        second = service.reinforce(second_request)
        assert second.source.revision_ordinal == 3
        assert _payload(values["connection"], second.source.revision_id)["reinforcement_count"] == 2
        assert _payload(values["connection"], second.source.revision_id)["strength"] == 0.853
        assert NativeRepresentationService(values["connection"]).read_representation_payload(second.e2_representation_id) == NativeRepresentationService(values["connection"]).read_representation_payload(e1.representation_id)
    finally:
        values["qualified"].close()


def test_tool_result_has_no_strength_boost_and_requires_refresh_timestamp(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values, source_channel="tool_result", strength=0.7)
        service = NativeMemoryReinforcementService(values["connection"])
        with pytest.raises(ValueError, match="last_tool_refresh_ts"):
            service.reinforce(_request(values, source, e1, key="tool-missing"))
        result = service.reinforce(_request(values, source, e1, key="tool", tool_ts=300))
        payload = _payload(values["connection"], result.source.revision_id)
        assert (payload["strength"], payload["reinforcement_count"], payload["last_tool_refresh_ts"]) == (0.7, 1, 300)
    finally:
        values["qualified"].close()


def test_strength_cap_and_pure_patch_refuses_malformed_payload(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values, strength=0.979)
        result = NativeMemoryReinforcementService(values["connection"]).reinforce(_request(values, source, e1, key="cap"))
        assert _payload(values["connection"], result.source.revision_id)["strength"] == 0.98
        with pytest.raises(ValueError):
            realize_reinforcement_patch({"strength": "not-a-number"}, source_channel="user_input", reinforcement_step=1, last_reinforced_ts=1, last_tool_refresh_ts=None)
        with pytest.raises(ValueError):
            realize_reinforcement_patch({"strength": float("nan")}, source_channel="user_input", reinforcement_step=1, last_reinforced_ts=1, last_tool_refresh_ts=None)
    finally:
        values["qualified"].close()


def test_zero_vector_e1_is_carried_byte_for_byte_without_search_selection_logic(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values, vector=(0.0, 0.0, 0.0))
        result = NativeMemoryReinforcementService(values["connection"]).reinforce(
            _request(values, source, e1, key="zero-continuity")
        )
        assert NativeRepresentationService(values["connection"]).read_representation_payload(result.e2_representation_id) == _vector_bytes((0.0, 0.0, 0.0))
    finally:
        values["qualified"].close()


@pytest.mark.parametrize(
    "change",
    (
        {"reinforcement_step": 21},
        {"last_reinforced_ts": 201},
        {"expected_dimension": 4},
        {"expected_representation_id": uuid4()},
        {"expected_revision_id": uuid4()},
    ),
)
def test_changed_retry_contract_conflicts_without_r3_or_e3(tmp_path: Path, change):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        service = NativeMemoryReinforcementService(values["connection"])
        result = service.reinforce(_request(values, source, e1, key="changed-retry"))
        before = _counts(values["connection"])
        with pytest.raises(SubstrateIdempotencyConflict):
            service.reinforce(replace(_request(values, source, e1, key="changed-retry"), **change))
        assert _counts(values["connection"]) == before
        assert result.source.revision_ordinal == 2
    finally:
        values["qualified"].close()


def test_stale_r1_refusal_precedes_any_source_successor(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        NativeMemoryCompatibilityFacade(values["connection"]).patch_memory_state(
            legacy_source_namespace_id=values["memory_alias"], eid=source.memory_eid,
            patch={"fixture": "advance"}, idempotency_namespace_id=values["idempotency"],
            idempotency_key="external-advance", expected_revision_id=source.memory_revision_id,
        )
        before = _counts(values["connection"])
        with pytest.raises(StaleReinforcementPlanError):
            NativeMemoryReinforcementService(values["connection"]).reinforce(_request(values, source, e1, key="stale-r1"))
        assert _counts(values["connection"]) == before
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("seam", ("revision", "governance"))
def test_source_internal_failure_rolls_back_r2_and_governance(tmp_path: Path, seam: str):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        before = _counts(connection)
        with pytest.raises(RuntimeError):
            NativeMemoryReinforcementService(connection).reinforce(
                _request(values, source, e1, key=f"rollback-{seam}"), _test_source_fail_after=seam
            )
        assert _counts(connection) == before
        assert connection.execute("SELECT current_revision_id FROM objects WHERE object_id=?", (native_id_to_bytes(source.memory_object_id),)).fetchone()[0] == native_id_to_bytes(source.memory_revision_id)
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("seam", ("effect", "output", "governance"))
def test_source_effect_output_and_governance_omission_are_rejected_atomically(tmp_path: Path, seam: str):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        before = _counts(connection)
        with pytest.raises(SubstrateInvariantViolation):
            NativeMemoryReinforcementService(connection).reinforce(
                _request(values, source, e1, key=f"omit-{seam}"),
                _test_omit_source_effect=seam == "effect",
                _test_omit_source_output=seam == "output",
                _test_omit_governance=seam == "governance",
            )
        assert _counts(connection) == before
    finally:
        values["qualified"].close()


def test_missing_governance_provenance_stale_and_wrong_e1_refuse_before_r2(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        service = NativeMemoryReinforcementService(connection)
        before = _counts(connection)
        with pytest.raises(StaleReinforcementPlanError):
            service.reinforce(replace(_request(values, source, e1, key="wrong-e1"), expected_representation_id=uuid4()))
        assert _counts(connection) == before
        plain = NativeMemoryCompatibilityFacade(connection).create_memory_state(
            legacy_source_namespace_id=values["memory_alias"], idempotency_namespace_id=values["idempotency"],
            idempotency_key="plain-source", identity_namespace_id=values["memory_identity"],
            semantic_scope_id=values["scope"], summary="plain", memory_type="reflection", logical_step=1,
        )
        plain_e1 = _ready_e1(values, plain, key="plain-e1")
        plain_request = NativeMemoryReinforcementRequest(
            legacy_source_namespace_id=values["memory_alias"], eid=plain.eid,
            expected_revision_id=plain.revision_id, expected_representation_id=plain_e1.representation_id,
            idempotency_namespace_id=values["idempotency"], idempotency_key="missing-governance",
            reinforcement_step=2, last_reinforced_ts=2, expected_dimension=3,
        )
        with pytest.raises(SubstrateInvariantViolation, match="explicit current governance"):
            service.reinforce(plain_request)
        connection.execute(
            "INSERT INTO object_revision_governance VALUES (?,?,?,?,?,?,?,?)",
            (native_id_to_bytes(plain.object_id), native_id_to_bytes(plain.revision_id), 1, 1, 1, 0, 0, 0),
        )
        with pytest.raises(SubstrateInvariantViolation, match="structural provenance"):
            service.reinforce(replace(plain_request, idempotency_key="missing-provenance"))
    finally:
        values["qualified"].close()


def test_unusable_wrong_dimension_and_corrupt_e1_refuse_without_r2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        connection = values["connection"]
        service = NativeMemoryReinforcementService(connection)
        before = _counts(connection)
        with pytest.raises(StaleReinforcementPlanError):
            service.reinforce(replace(_request(values, source, e1, key="wrong-dim"), expected_dimension=4))
        # A later integrity mismatch makes E1 non-usable without changing R1.
        from torment_service.substrate import representations as representations_module
        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        NativeRepresentationService(connection).verify_published_representation_integrity(
            idempotency_namespace_id=values["idempotency"], idempotency_key="e1-mismatch",
            request=RepresentationIntegrityVerificationRequest(e1.representation_id, "synthetic"),
        )
        with pytest.raises(StaleReinforcementPlanError):
            service.reinforce(_request(values, source, e1, key="unusable"))
        assert _counts(connection)[0:2] == before[0:2]
    finally:
        values["qualified"].close()


def test_e1_later_unusable_blocks_e2_retry_but_preserves_committed_r2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values)
        service = NativeMemoryReinforcementService(values["connection"])
        request = _request(values, source, e1, key="e1-later-unusable")
        with pytest.raises(RuntimeError):
            service.reinforce(request, _test_stop_after="source")
        from torment_service.substrate import representations as representations_module
        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        NativeRepresentationService(values["connection"]).verify_published_representation_integrity(
            idempotency_namespace_id=values["idempotency"], idempotency_key="e1-later-mismatch",
            request=RepresentationIntegrityVerificationRequest(e1.representation_id, "later mismatch"),
        )
        with pytest.raises(SubstrateInvariantViolation, match="historical embedding"):
            service.reinforce(request)
        current = NativeMemoryCompatibilityFacade(values["connection"]).get_memory_by_eid(
            legacy_source_namespace_id=values["memory_alias"], eid=source.memory_eid
        )
        assert current.revision_ordinal == 2
        assert values["connection"].execute("SELECT count(*) FROM object_revisions WHERE object_id=?", (native_id_to_bytes(source.memory_object_id),)).fetchone()[0] == 2
    finally:
        values["qualified"].close()


def test_changed_tool_refresh_timestamp_conflicts_after_tool_reinforcement(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, e1 = _source(values, source_channel="tool_result")
        service = NativeMemoryReinforcementService(values["connection"])
        request = _request(values, source, e1, key="tool-retry", tool_ts=300)
        service.reinforce(request)
        with pytest.raises(SubstrateIdempotencyConflict):
            service.reinforce(replace(request, last_tool_refresh_ts=301))
    finally:
        values["qualified"].close()


def test_e1_dependencies_are_preserved_without_adding_e1_as_dependency(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source, _initial_e1 = _source(values)
        # The original E1 used by this test is created with one ready dependency.
        payload = _vector_bytes((0.0, 1.0, 0.0))
        representations = NativeRepresentationService(values["connection"])
        dependency = representations.create_representation_pending(
            idempotency_namespace_id=values["idempotency"], idempotency_key="dep-pending",
            request=RepresentationRequest("OBJECT_REVISION", source.memory_object_id, source.memory_revision_id, None, None, "DEPENDENCY", 1, "v1", "RAW", expected_payload_byte_length=len(payload)),
        )
        representations.establish_representation_integrity_expectation(
            idempotency_namespace_id=values["idempotency"], idempotency_key="dep-expect",
            request=RepresentationIntegrityExpectationRequest(dependency.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW),
        )
        representations.publish_representation_ready(
            idempotency_namespace_id=values["idempotency"], idempotency_key="dep-ready",
            request=RepresentationReadyRequest(dependency.representation_id, "DEPENDENCY", 1, "v1", "RAW", payload),
        )
        # Build an independent composition with its declared-dependency E1.
        dependency_root = tmp_path / "dependency-source"
        dependency_root.mkdir()
        values2 = _database(dependency_root)
        try:
            source2 = NativeMemoryMotifCompositionService(values2["connection"]).commit(NativeMemoryMotifCompositionService(values2["connection"]).prepare_plan(_composition_request(values2, key="compose-dep")))
            dep_payload = _vector_bytes((0.0, 1.0, 0.0))
            dep = NativeRepresentationService(values2["connection"]).create_representation_pending(
                idempotency_namespace_id=values2["idempotency"], idempotency_key="dep-pending",
                request=RepresentationRequest("OBJECT_REVISION", source2.memory_object_id, source2.memory_revision_id, None, None, "DEPENDENCY", 1, "v1", "RAW", expected_payload_byte_length=len(dep_payload)),
            )
            reps2 = NativeRepresentationService(values2["connection"])
            reps2.establish_representation_integrity_expectation(idempotency_namespace_id=values2["idempotency"], idempotency_key="dep-expect", request=RepresentationIntegrityExpectationRequest(dep.representation_id, INTEGRITY_ALGORITHM_SHA256, sha256(dep_payload).digest(), INTEGRITY_VALUE_ENCODING_RAW))
            reps2.publish_representation_ready(idempotency_namespace_id=values2["idempotency"], idempotency_key="dep-ready", request=RepresentationReadyRequest(dep.representation_id, "DEPENDENCY", 1, "v1", "RAW", dep_payload))
            e1 = _ready_e1(values2, source2, key="e1-dep", dependencies=(dep.representation_id,))
            result = NativeMemoryReinforcementService(values2["connection"]).reinforce(_request(values2, source2, e1, key="dep-reinforce"))
            dependencies = values2["connection"].execute("SELECT dependency_representation_id FROM representation_dependencies WHERE representation_id=?", (native_id_to_bytes(result.e2_representation_id),)).fetchall()
            assert dependencies == [(native_id_to_bytes(dep.representation_id),)]
            assert native_id_to_bytes(e1.representation_id) not in {item[0] for item in dependencies}
        finally:
            values2["qualified"].close()
    finally:
        values["qualified"].close()
