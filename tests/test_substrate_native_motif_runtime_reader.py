"""Focused Phase 7G5A3B native motif runtime read and geometry tests."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from torment_service.coherence_field import compute_coherence_field
from torment_service.motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    _unit,
    motif_gravity_bonus,
)
from torment_service.motif_geometry import motif_radius_from_member_vectors
from torment_service.substrate import representations as representations_module
from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateInvariantViolation
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.motifs import MotifState, NativeMotifService
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
    tmp_path.mkdir(parents=True, exist_ok=True)
    qualified = open_temporary_test_connection(tmp_path / "native-motif-runtime-reader.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    values = {name: _id() for name in (
        "motif_identity", "membership_identity", "memory_identity", "motif_scope",
        "other_motif_scope", "empty_motif_scope", "memory_scope", "idempotency", "memory_alias", "motif_alias",
        "other_motif_alias", "empty_motif_alias",
    )}
    for name in ("motif_identity", "membership_identity", "memory_identity"):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"a3b-{name}"),
        )
    for name in ("motif_scope", "other_motif_scope", "empty_motif_scope", "memory_scope"):
        connection.execute(
            "INSERT INTO semantic_scopes VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"a3b-{name}"),
        )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(values["idempotency"]), "a3b-idempotency"),
    )
    for name in ("memory_alias", "motif_alias", "other_motif_alias", "empty_motif_alias"):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[name]), f"a3b-{name}"),
        )
    values["qualified"] = qualified
    values["connection"] = connection
    return values


def _memory(values, key: str):
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=values["memory_alias"],
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"memory:{key}",
        identity_namespace_id=values["memory_identity"],
        semantic_scope_id=values["memory_scope"],
        summary=f"memory {key}",
        memory_type="reflection",
        logical_step=1,
    )


def _state(
    values,
    runtime_motif_id: str,
    *,
    domain_id: str = "personal",
    centroid: tuple[float, ...] = (1.0, 0.0, 0.0),
    strength: float = 0.6,
    last_active_ts: int = 100,
    semantic_scope_id=None,
) -> MotifState:
    return MotifState(
        semantic_scope_id or values["motif_scope"], runtime_motif_id, domain_id,
        f"label {runtime_motif_id}", centroid, strength, 0.7,
        ("aria",), 100, last_active_ts,
    )


def _create(values, memory, runtime_motif_id: str, *, key: str, **state_overrides):
    return NativeMotifService(values["connection"]).create_motif_with_member(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        motif_identity_namespace_id=values["motif_identity"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_alias_namespace_id=values["motif_alias"],
        state=_state(values, runtime_motif_id, **state_overrides),
        member_object_id=memory.object_id,
    )


def _successor(values, current, *, centroid=None, strength=None, last_active_ts=None):
    state = current.state
    return MotifState(
        state.semantic_scope_id, state.runtime_motif_id, state.domain_id, state.label,
        tuple(centroid if centroid is not None else state.centroid),
        float(strength if strength is not None else state.strength),
        state.stability_score, state.contributing_agents, state.created_ts,
        int(last_active_ts if last_active_ts is not None else state.last_active_ts + 1),
        state.derivation_metadata, state.extra_payload,
    )


def _add(values, motif, memory, *, key: str, **state_overrides):
    service = NativeMotifService(values["connection"])
    current = service.get_current_motif(motif.motif_object_id)
    return service.add_motif_member(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        motif_alias_namespace_id=values["motif_alias"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_object_id=motif.motif_object_id,
        expected_motif_revision_id=current.motif_revision_id,
        state=_successor(values, current, **state_overrides),
        member_object_id=memory.object_id,
    )


def _advance(values, motif, *, key: str, **state_overrides):
    service = NativeMotifService(values["connection"])
    current = service.get_current_motif(motif.motif_object_id)
    return service.advance_motif_state(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        motif_alias_namespace_id=values["motif_alias"],
        motif_object_id=motif.motif_object_id,
        expected_motif_revision_id=current.motif_revision_id,
        state=_successor(values, current, **state_overrides),
    )


def _vector_bytes(vector, dtype="float32"):
    return np.asarray(vector, dtype=np.dtype(dtype)).reshape(-1).tobytes(order="C")


def _pending(
    values, source, key: str, vector, *, representation_class="COMPAT_EMBEDDING",
    generation=1, derivation_contract_version="compat-embedding-v1",
    encoding_id="RAW_VECTOR", dtype="float32", dimension=3,
):
    payload = _vector_bytes(vector, dtype)
    return NativeRepresentationService(values["connection"]).create_representation_pending(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"pending:{key}",
        request=RepresentationRequest(
            "OBJECT_REVISION", source.object_id, source.revision_id, None, None,
            representation_class, generation, derivation_contract_version, encoding_id,
            dtype=dtype, dimension=dimension, expected_payload_byte_length=len(payload),
        ),
    )


def _ready(values, source, key: str, vector, **kwargs):
    pending = _pending(values, source, key, vector, **kwargs)
    payload = _vector_bytes(vector, kwargs.get("dtype", "float32"))
    service = NativeRepresentationService(values["connection"])
    service.establish_representation_integrity_expectation(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"expect:{key}",
        request=RepresentationIntegrityExpectationRequest(
            pending.representation_id, INTEGRITY_ALGORITHM_SHA256,
            sha256(payload).digest(), INTEGRITY_VALUE_ENCODING_RAW,
        ),
    )
    return service.publish_representation_ready(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"ready:{key}",
        request=RepresentationReadyRequest(
            pending.representation_id,
            kwargs.get("representation_class", "COMPAT_EMBEDDING"),
            kwargs.get("generation", 1),
            kwargs.get("derivation_contract_version", "compat-embedding-v1"),
            kwargs.get("encoding_id", "RAW_VECTOR"),
            payload,
        ),
    )


def _semantic_counts(connection):
    return tuple(
        connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        for table in (
            "objects", "object_revisions", "relationships", "relationship_revisions",
            "representations", "operations", "semantic_transitions",
            "integrity_measurements", "reconciliation_cases",
        )
    )


def test_catalog_restart_order_scope_and_alias_invariants_are_read_only(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source = _memory(values, "catalog")
        for index, runtime_id in enumerate((
            "motif_personal_0003", "motif_personal_0001",
            "motif_personal_0002", "motif_personal_0001_split_0007",
        )):
            _create(values, source, runtime_id, key=f"catalog:{index}")
        NativeMotifService(values["connection"]).create_motif_with_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="other-namespace",
            motif_identity_namespace_id=values["motif_identity"],
            membership_identity_namespace_id=values["membership_identity"],
            motif_alias_namespace_id=values["other_motif_alias"],
            state=_state(values, "motif_personal_9999", semantic_scope_id=values["other_motif_scope"]), member_object_id=source.object_id,
        )
        reader = NativeMotifRuntimeReader(values["connection"])
        before = _semantic_counts(values["connection"])
        catalog = reader.list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal",
            semantic_scope_id=values["motif_scope"],
        )
        assert [item.read_model.runtime_motif_id for item in catalog] == [
            "motif_personal_0001", "motif_personal_0001_split_0007",
            "motif_personal_0002", "motif_personal_0003",
        ]
        assert all(item.read_model.member_count == 1 for item in catalog)
        assert _semantic_counts(values["connection"]) == before

        motif = catalog[0]
        values["connection"].execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (native_id_to_bytes(values["motif_alias"]), "MOTIF_ID", "motif_personal_9999", native_id_to_bytes(motif.motif_object_id)),
        )
        with pytest.raises(SubstrateInvariantViolation, match="multiple MOTIF_ID aliases"):
            reader.list_runtime_motifs(
                motif_alias_namespace_id=values["motif_alias"], domain_id="personal",
                semantic_scope_id=values["motif_scope"],
            )
    finally:
        values["qualified"].close()


def test_catalog_refuses_wrong_kind_and_domain_payload(tmp_path: Path):
    values = _database(tmp_path)
    try:
        source = _memory(values, "wrong-kind")
        reader = NativeMotifRuntimeReader(values["connection"])
        values["connection"].execute(
            "INSERT INTO legacy_object_aliases VALUES (?,?,?,?)",
            (native_id_to_bytes(values["motif_alias"]), "MOTIF_ID", "not-a-motif", native_id_to_bytes(source.object_id)),
        )
        with pytest.raises(SubstrateInvariantViolation, match="does not target"):
            reader.list_runtime_motifs(motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["motif_scope"])
    finally:
        values["qualified"].close()

    values = _database(tmp_path / "missing-alias")
    try:
        source = _memory(values, "missing-alias")
        NativeMotifService(values["connection"]).create_motif_with_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="missing-alias",
            motif_identity_namespace_id=values["motif_identity"],
            membership_identity_namespace_id=values["membership_identity"],
            motif_alias_namespace_id=values["other_motif_alias"],
            state=_state(values, "motif_personal_0001"), member_object_id=source.object_id,
        )
        with pytest.raises(SubstrateInvariantViolation, match="no MOTIF_ID alias"):
            NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
                motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["motif_scope"]
            )
    finally:
        values["qualified"].close()

    values = _database(tmp_path / "alias-disagreement")
    try:
        source = _memory(values, "alias-disagreement")
        created = _create(values, source, "motif_personal_0001", key="alias-disagreement")
        values["connection"].execute(
            "UPDATE legacy_object_aliases SET alias_value=? WHERE legacy_source_namespace_id=? AND alias_kind=? AND object_id=?",
            ("motif_personal_alias_disagrees", native_id_to_bytes(values["motif_alias"]), "MOTIF_ID", native_id_to_bytes(created.motif_object_id)),
        )
        with pytest.raises(SubstrateInvariantViolation, match="payload disagrees"):
            NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
                motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["motif_scope"]
            )
    finally:
        values["qualified"].close()

    values = _database(tmp_path / "domain")
    try:
        source = _memory(values, "wrong-domain")
        _create(values, source, "motif_research_0001", key="wrong-domain", domain_id="research")
        with pytest.raises(SubstrateInvariantViolation, match="payload domain"):
            NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
                motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["motif_scope"]
            )
    finally:
        values["qualified"].close()


def test_member_append_order_uses_shared_transition_motif_ordinal(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first, second, third = (_memory(values, key) for key in ("A", "B", "C"))
        created = _create(values, first, "motif_personal_0001", key="create")
        added_second = _add(values, created, second, key="add-second", last_active_ts=101)
        advanced = _advance(values, created, key="state-only", last_active_ts=102)
        added_third = _add(values, created, third, key="add-third", last_active_ts=103)
        assert (created.motif_revision_ordinal, added_second.motif_revision_ordinal, advanced.motif_revision_ordinal, added_third.motif_revision_ordinal) == (1, 2, 3, 4)

        reader = NativeMotifRuntimeReader(values["connection"])
        before = _semantic_counts(values["connection"])
        ordered = reader.list_ordered_current_motif_members(created.motif_object_id)
        assert [item.member_object_id for item in ordered] == [first.object_id, second.object_id, third.object_id]
        assert [item.motif_publication_ordinal for item in ordered] == [1, 2, 4]
        uuid_ordered = NativeMotifService(values["connection"]).list_current_motif_members(created.motif_object_id)
        assert list(uuid_ordered) == sorted(uuid_ordered, key=lambda item: item.relationship_id.bytes)
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_current_raw_embedding_read_is_qualified_unscaled_and_current_revision_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    values = _database(tmp_path)
    try:
        reader = NativeMotifRuntimeReader(values["connection"])
        ready_source = _memory(values, "ready")
        _ready(values, ready_source, "ready", (2.0, 0.0, 0.0))
        raw = reader.read_current_compat_embedding(ready_source.object_id, expected_dimension=3)
        assert raw is not None and raw.dtype == np.float32 and raw.tolist() == [2.0, 0.0, 0.0]
        zero_source = _memory(values, "zero")
        _ready(values, zero_source, "zero", (0.0, 0.0, 0.0))
        assert reader.read_current_compat_embedding(zero_source.object_id, expected_dimension=3).tolist() == [0.0, 0.0, 0.0]

        for label, kwargs in (
            ("class", {"representation_class": "OTHER"}),
            ("generation", {"generation": 2}),
            ("contract", {"derivation_contract_version": "other-v1"}),
            ("encoding", {"encoding_id": "OTHER"}),
            ("dtype", {"dtype": "float64"}),
            ("dimension", {"dimension": 4, "vector": (1.0, 0.0, 0.0, 0.0)}),
        ):
            source = _memory(values, label)
            vector = kwargs.pop("vector", (1.0, 0.0, 0.0))
            _ready(values, source, label, vector, **kwargs)
            assert reader.read_current_compat_embedding(source.object_id, expected_dimension=3) is None

        pending_source = _memory(values, "pending")
        _pending(values, pending_source, "pending", (1.0, 0.0, 0.0))
        assert reader.read_current_compat_embedding(pending_source.object_id, expected_dimension=3) is None
        failed_source = _memory(values, "failed")
        failed = _pending(values, failed_source, "failed", (1.0, 0.0, 0.0))
        NativeRepresentationService(values["connection"]).fail_representation(
            idempotency_namespace_id=values["idempotency"], idempotency_key="fail:failed",
            request=RepresentationFailureRequest(failed.representation_id, "synthetic"),
        )
        assert reader.read_current_compat_embedding(failed_source.object_id, expected_dimension=3) is None

        advanced = NativeMemoryCompatibilityFacade(values["connection"]).patch_memory_state(
            legacy_source_namespace_id=values["memory_alias"], eid=ready_source.eid,
            patch={"fixture_note": "R2"}, idempotency_namespace_id=values["idempotency"],
            idempotency_key="ready:R2", expected_revision_id=ready_source.revision_id,
        )
        assert reader.read_current_compat_embedding(ready_source.object_id, expected_dimension=3) is None
        _ready(values, advanced, "ready:R2", (3.0, 0.0, 0.0))
        assert reader.read_current_compat_embedding(ready_source.object_id, expected_dimension=3).tolist() == [3.0, 0.0, 0.0]

        mismatch_source = _memory(values, "mismatch")
        mismatch = _ready(values, mismatch_source, "mismatch", (1.0, 0.0, 0.0))
        current_source = _memory(values, "malformed")
        _ready(values, current_source, "malformed", (1.0, 0.0, 0.0))
        monkeypatch.setattr(representations_module, "_measure_payload", lambda *_args: b"x" * 32)
        NativeRepresentationService(values["connection"]).verify_published_representation_integrity(
            idempotency_namespace_id=values["idempotency"], idempotency_key="mismatch:verify",
            request=RepresentationIntegrityVerificationRequest(mismatch.representation_id, "test"),
        )
        assert reader.read_current_compat_embedding(mismatch_source.object_id, expected_dimension=3) is None

        monkeypatch.setattr(reader._representations, "read_representation_payload", lambda _id: b"short")
        with pytest.raises(SubstrateInvariantViolation, match="payload length"):
            reader.read_current_compat_embedding(current_source.object_id, expected_dimension=3)
    finally:
        values["qualified"].close()


def test_native_radius_projection_and_centroid_are_read_only_and_math_shared(tmp_path: Path):
    values = _database(tmp_path)
    try:
        assert motif_radius_from_member_vectors((1.0, 0.0), ((1.0, 0.0), (0.0, 1.0))) == pytest.approx(0.5)
        assert motif_radius_from_member_vectors((1.0, 0.0), ((0.0, 0.0), None, (1.0, 0.0, 0.0))) == pytest.approx(1.0)
        assert motif_radius_from_member_vectors((1.0, 0.0), (None, (1.0, 0.0, 0.0))) == 0.0

        first, second, missing = (_memory(values, key) for key in ("geometry-A", "geometry-B", "geometry-C"))
        _ready(values, first, "geometry-A", (1.0, 0.0, 0.0))
        _ready(values, second, "geometry-B", (0.0, 1.0, 0.0))
        motif = _create(values, first, "motif_personal_0001", key="geometry", centroid=(1.0, 0.0, 0.0))
        _add(values, motif, second, key="geometry:add-b", last_active_ts=101)
        _add(values, motif, missing, key="geometry:add-c", last_active_ts=102)
        second_motif = _create(values, first, "motif_personal_0002", key="centroid-second", centroid=(0.0, 1.0, 0.0), strength=0.8)
        _create(values, first, "motif_personal_0003", key="centroid-mismatch", centroid=(1.0, 0.0), strength=0.9)
        reader = NativeMotifRuntimeReader(values["connection"])
        before = _semantic_counts(values["connection"])
        catalog = reader.list_runtime_motifs(motif_alias_namespace_id=values["motif_alias"], domain_id="personal", semantic_scope_id=values["motif_scope"])
        first_model = next(item.read_model for item in catalog if item.motif_object_id == motif.motif_object_id)
        assert first_model.member_count == 3
        assert reader.motif_radius(motif.motif_object_id, expected_dimension=3) == pytest.approx(0.5)
        native_rows = reader.project_coherence_field_rows(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal", expected_dimension=3, semantic_scope_id=values["motif_scope"],
        )
        first_row = next(row for row in native_rows if row["motif_id"] == "motif_personal_0001")
        assert first_row["members"] == 3 and first_row["radius"] == pytest.approx(0.5)
        legacy_row = dict(first_row)
        legacy_row["members"] = [10, 11, 12]
        assert compute_coherence_field([legacy_row]) == compute_coherence_field([first_row])

        valid_models = [item.read_model for item in catalog if len(item.read_model.centroid) == 3]
        W = np.asarray([
            max(1e-6, model.strength) * (1.0 + motif_gravity_bonus(model, CURRENT_MOTIF_DECISION_POLICY))
            for model in valid_models
        ], dtype=np.float32)
        C = np.vstack([model.centroid_np() for model in valid_models])
        expected = _unit((C * W[:, None]).sum(axis=0) / (W.sum() + 1e-12))
        actual = reader.domain_centroid(
            motif_alias_namespace_id=values["motif_alias"], domain_id="personal", dimension=3, semantic_scope_id=values["motif_scope"],
        )
        assert actual.dtype == np.float32 and np.array_equal(actual, expected)
        assert np.array_equal(
            reader.domain_centroid(
                motif_alias_namespace_id=values["empty_motif_alias"], domain_id="personal", dimension=3, semantic_scope_id=values["empty_motif_scope"],
            ),
            np.zeros(3, dtype=np.float32),
        )
        assert _semantic_counts(values["connection"]) == before
        assert second_motif.motif_object_id != motif.motif_object_id
    finally:
        values["qualified"].close()
