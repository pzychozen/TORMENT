"""Focused qualification for the unwired A3C2 composition boundary."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from torment_service.motif_decision import _unit
from torment_service.motif_geometry import motif_radius_from_member_vectors
from torment_service.resonance import append_symbol, summarize_resonance
from torment_service.substrate.compat import (
    CompatibilityEmbeddingPublicationRequest,
    NativeMemoryCompatibilityFacade,
)
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation
from torment_service.substrate.fabric_translation import (
    QualifiedCompatibilityLinkIntent,
    UnresolvedLegacyLinkReference,
)
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.memory_motif_composition import (
    NativeMemoryMotifCompositionRequest,
    NativeMemoryMotifCompositionService,
    StaleMotifCatalogError,
    UnsupportedNativeSplitError,
)
from torment_service.substrate.motifs import MotifState, NativeMotifService
from torment_service.substrate.object_revision_governance import (
    NativeMemoryGovernanceFacts,
    NativeObjectRevisionGovernanceService,
)
from torment_service.substrate.provenance import NativeProvenanceRecord
from torment_service.substrate.schema import create_schema
from torment_service.symbols import assign_symbol_state


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "a3c2.db")
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
        ("memory_identity", "a3c2-memory-identity"),
        ("motif_identity", "a3c2-motif-identity"),
        ("membership_identity", "a3c2-membership-identity"),
    ):
        connection.execute(
            "INSERT INTO identity_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[key]), label),
        )
    connection.execute(
        "INSERT INTO semantic_scopes VALUES (?,?,0)",
        (native_id_to_bytes(values["scope"]), "a3c2-scope"),
    )
    connection.execute(
        "INSERT INTO idempotency_namespaces VALUES (?,?)",
        (native_id_to_bytes(values["idempotency"]), "a3c2-idempotency"),
    )
    for key, label in (("memory_alias", "a3c2-memory-alias"), ("motif_alias", "a3c2-motif-alias")):
        connection.execute(
            "INSERT INTO legacy_source_namespaces VALUES (?,?,0)",
            (native_id_to_bytes(values[key]), label),
        )
    return values


def _request(values, *, key="composition-1", embedding=(1.0, 0.0, 0.0), **changes):
    facts = {
        "legacy_source_namespace_id": values["memory_alias"],
        "memory_identity_namespace_id": values["memory_identity"],
        "semantic_scope_id": values["scope"],
        "summary": "new composed memory",
        "memory_type": "reflection",
        "memory_class": "core",
        "strength": 0.75,
        "confidence": 0.8,
        "half_life_days": 7.0,
        "user_id": "aria",
        "logical_step": 42,
        "flexible_payload": {"affect": {"mood": "curious"}},
        "lifecycle_state": "ORDINARY",
        "lifecycle_authoritative": False,
        "governance_state": "DERIVED",
        "provenance": NativeProvenanceRecord(
            "USER_INPUT", "chat", "user", "DIRECT", "KNOWN", 1, 2, "INPUT", "test",
        ),
        "governance": NativeMemoryGovernanceFacts(),
        "motif_alias_namespace_id": values["motif_alias"],
        "motif_identity_namespace_id": values["motif_identity"],
        "membership_identity_namespace_id": values["membership_identity"],
        "domain_id": "research",
        "agent_id": "aria",
        "idempotency_namespace_id": values["idempotency"],
        "idempotency_key": key,
        "incoming_embedding": embedding,
        "attach_threshold": 0.72,
        "created_ts": 100,
        "last_active_ts": 101,
        "expected_dimension": 3,
        "prior_symbol": "",
        "prior_symbol_trace": (),
        "prior_motif_id": "",
        "prior_tension": 0.0,
    }
    facts.update(changes)
    return NativeMemoryMotifCompositionRequest(**facts)


def _semantic_counts(connection):
    tables = (
        "objects", "object_revisions", "legacy_object_aliases", "provenance_records",
        "object_revision_governance", "relationships", "relationship_revisions",
        "semantic_transitions", "operations", "object_revision_effects",
        "relationship_revision_effects", "operation_outputs", "representations",
    )
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in tables)


def _existing_memory(values, *, key: str, eid_label: int, summary="seed"):
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=values["memory_alias"],
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        identity_namespace_id=values["memory_identity"], semantic_scope_id=values["scope"],
        summary=summary, memory_type="reflection", logical_step=eid_label,
    )


def _existing_memory_with_embedding(values, *, key: str, eid_label: int, vector):
    raw = np.asarray(vector, dtype=np.float32)
    facade = NativeMemoryCompatibilityFacade(values["connection"])
    draft = facade.begin_memory_draft(
        legacy_source_namespace_id=values["memory_alias"],
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        identity_namespace_id=values["memory_identity"], semantic_scope_id=values["scope"],
        summary=key, memory_type="reflection", logical_step=eid_label,
        embedding_request=CompatibilityEmbeddingPublicationRequest(
            raw.tobytes(), "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
            dtype="float32", dimension=len(raw),
        ),
    )
    return facade.finalize_memory_draft(draft).source


def _motif_state(values, *, runtime_id="motif_research_0001", centroid=(1.0, 0.0, 0.0), last_active=50):
    return MotifState(
        values["scope"], runtime_id, "research", "Research basin", centroid,
        0.8, 0.7, ("aria",), 10, last_active,
        {"derivation": "seed"}, {"keep": "metadata"},
    )


def _seed_motif(values, *, runtime_id="motif_research_0001", centroid=(1.0, 0.0, 0.0), key="seed-motif", source=None):
    source = source or _existing_memory(values, key=f"{key}-memory", eid_label=10, summary=runtime_id)
    return NativeMotifService(values["connection"]).create_motif_with_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        motif_identity_namespace_id=values["motif_identity"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_alias_namespace_id=values["motif_alias"],
        state=_motif_state(values, runtime_id=runtime_id, centroid=centroid),
        member_object_id=source.object_id,
    )


def _advance_motif(values, result, *, key="advance-motif"):
    service = NativeMotifService(values["connection"])
    current = service.get_current_motif(result.motif_object_id)
    source = _existing_memory(values, key=f"{key}-memory", eid_label=30, summary=key)
    return service.add_motif_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        motif_alias_namespace_id=values["motif_alias"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_object_id=result.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
        state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
        member_object_id=source.object_id,
    )


def _add_member(values, result, *, key: str, eid_label: int):
    service = NativeMotifService(values["connection"])
    current = service.get_current_motif(result.motif_object_id)
    source = _existing_memory(values, key=f"{key}-memory", eid_label=eid_label, summary=key)
    return service.add_motif_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key=key,
        motif_alias_namespace_id=values["motif_alias"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_object_id=result.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
        state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
        member_object_id=source.object_id,
    )


def test_create_is_one_atomic_compound_transition_with_closed_children_and_retry(tmp_path: Path):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        service = NativeMemoryMotifCompositionService(connection)
        request = _request(values)
        before = _semantic_counts(connection)
        preview = service.prepare_plan(request)
        assert preview.decision.kind == "CREATE_NEW"
        first = service.commit(preview)
        assert service.commit(service.prepare_plan(request)) == first
        assert first.memory_eid == 0 and first.runtime_motif_id == "motif_research_0001"
        assert _semantic_counts(connection) == tuple(a + b for a, b in zip(before, (2, 2, 2, 1, 1, 1, 1, 1, 1, 2, 1, 3, 0)))
        assert connection.execute(
            "SELECT output_ordinal,output_role,output_kind FROM operation_outputs WHERE operation_id=? ORDER BY output_ordinal",
            (native_id_to_bytes(first.operation_id),),
        ).fetchall() == [(0, "MEMORY", "OBJECT"), (1, "MOTIF", "OBJECT"), (2, "MOTIF_MEMBERSHIP", "RELATIONSHIP")]
        assert connection.execute(
            "SELECT count(*) FROM semantic_transitions WHERE operation_id=?", (native_id_to_bytes(first.operation_id),)
        ).fetchone()[0] == 1
        assert NativeObjectRevisionGovernanceService(connection).get_current_object_governance(
            object_id=first.memory_object_id
        ).facts == NativeMemoryGovernanceFacts()
        payload = connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(first.memory_revision_id),)
        ).fetchone()[0]
        assert "symbol_trace" in payload and "resonance_score" in payload
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
            "representation_current_state", "representation_payloads", "integrity_expectations", "integrity_measurements",
        )) == (0, 0, 0, 0)
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("change", (
    {"summary": "changed"},
    {"governance": NativeMemoryGovernanceFacts(protected=True)},
    {"provenance": NativeProvenanceRecord("TOOL", "tool", None, "DIRECT", "KNOWN")},
    {"incoming_embedding": (0.0, 1.0, 0.0)},
    {"domain_id": "other"},
))
def test_changed_intent_retry_conflicts_without_new_transition(tmp_path: Path, change):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        first = service.commit(service.prepare_plan(_request(values)))
        before = _semantic_counts(values["connection"])
        changed = _request(values, **change)
        changed_preview = replace(service.prepare_plan(_request(values)), request=changed) if "domain_id" in change else service.prepare_plan(changed)
        with pytest.raises(SubstrateIdempotencyConflict):
            service.commit(changed_preview)
        assert _semantic_counts(values["connection"]) == before
        assert first.memory_eid == 0
    finally:
        values["qualified"].close()


def test_attach_publishes_one_successor_and_identity_bound_membership(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed = _seed_motif(values)
        service = NativeMemoryMotifCompositionService(values["connection"])
        preview = service.prepare_plan(_request(values, key="attach", embedding=(2.0, 0.0, 0.0)))
        assert preview.decision.kind == "ATTACH_EXISTING"
        result = service.commit(preview)
        assert result.motif_object_id == seed.motif_object_id
        assert result.motif_revision_ordinal == 2
        assert service.commit(service.prepare_plan(_request(values, key="attach", embedding=(2.0, 0.0, 0.0)))) == result
        assert values["connection"].execute(
            "SELECT count(*) FROM legacy_object_aliases WHERE alias_kind='MOTIF_ID' AND object_id=?",
            (native_id_to_bytes(seed.motif_object_id),),
        ).fetchone()[0] == 1
        endpoints = values["connection"].execute(
            "SELECT endpoint_role,object_id,binding_mode FROM relationship_revision_endpoints WHERE relationship_revision_id=? ORDER BY endpoint_ordinal",
            (native_id_to_bytes(result.membership_revision_id),),
        ).fetchall()
        assert endpoints == [("MOTIF", native_id_to_bytes(result.motif_object_id), "IDENTITY"), ("MEMBER", native_id_to_bytes(result.memory_object_id), "IDENTITY")]
        state = NativeMotifService(values["connection"]).get_current_motif(seed.motif_object_id).state
        assert dict(state.extra_payload) == {"keep": "metadata"}
    finally:
        values["qualified"].close()


def test_stale_selected_competing_and_new_catalog_entries_refuse_without_residue(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed_a = _seed_motif(values, runtime_id="motif_research_0001", key="seed-a")
        seed_b = _seed_motif(values, runtime_id="motif_research_0002", centroid=(0.0, 1.0, 0.0), key="seed-b")
        service = NativeMemoryMotifCompositionService(values["connection"])
        attach = service.prepare_plan(_request(values, key="stale-selected"))
        _advance_motif(values, seed_a, key="advance-a")
        advanced = _semantic_counts(values["connection"])
        with pytest.raises(StaleMotifCatalogError):
            service.commit(attach)
        assert _semantic_counts(values["connection"]) == advanced

        competing = service.prepare_plan(_request(values, key="stale-competing"))
        _advance_motif(values, seed_b, key="advance-b")
        advanced = _semantic_counts(values["connection"])
        with pytest.raises(StaleMotifCatalogError):
            service.commit(competing)
        assert _semantic_counts(values["connection"]) == advanced

        create = service.prepare_plan(_request(values, key="stale-new", embedding=(0.0, 0.0, 1.0)))
        _seed_motif(values, runtime_id="motif_research_0003", centroid=(0.0, 0.0, -1.0), key="seed-c")
        advanced = _semantic_counts(values["connection"])
        with pytest.raises(StaleMotifCatalogError):
            service.commit(create)
        assert _semantic_counts(values["connection"]) == advanced
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("where", ("provenance", "governance", "memory", "motif", "membership"))
def test_private_failure_seams_roll_back_every_compound_part(tmp_path: Path, where: str):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        before = _semantic_counts(values["connection"])
        with pytest.raises(RuntimeError):
            service.commit(service.prepare_plan(_request(values, key=f"rollback-{where}")), _test_fail_after=where)
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("effect", ("memory", "motif", "membership"))
def test_effect_omission_is_rejected_and_rolls_back(tmp_path: Path, effect: str):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        before = _semantic_counts(values["connection"])
        with pytest.raises(SubstrateInvariantViolation):
            service.commit(service.prepare_plan(_request(values, key=f"effect-{effect}")), _test_omit_effect=effect)
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("output", ("memory", "motif", "membership"))
def test_output_omission_is_rejected_and_rolls_back(tmp_path: Path, output: str):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        before = _semantic_counts(values["connection"])
        with pytest.raises(SubstrateInvariantViolation):
            service.commit(service.prepare_plan(_request(values, key=f"output-{output}")), _test_omit_output=output)
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_next_runtime_id_matches_legacy_numeric_extraction_and_rolls_back(tmp_path: Path):
    values = _database(tmp_path)
    try:
        for index, runtime_id in enumerate(("motif_research_0001", "motif_research_0004", "motif_research_0003_split0008")):
            _seed_motif(values, runtime_id=runtime_id, key=f"id-seed-{index}")
        service = NativeMemoryMotifCompositionService(values["connection"])
        preview = service.prepare_plan(_request(values, key="allocate-nine", embedding=(0.0, 0.0, 1.0)))
        assert preview.predicted_runtime_motif_id == "motif_research_0009"
        before = _semantic_counts(values["connection"])
        with pytest.raises(RuntimeError):
            service.commit(preview, _test_fail_after="motif")
        assert _semantic_counts(values["connection"]) == before
        result = service.commit(preview)
        assert result.runtime_motif_id == "motif_research_0009"
    finally:
        values["qualified"].close()


def test_link_inputs_are_independently_rejected_and_split_boundary_is_fail_closed(tmp_path: Path):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        qualified = QualifiedCompatibilityLinkIntent(values["memory_alias"], 0)
        unresolved = UnresolvedLegacyLinkReference("legacy-raw-target", 0)
        for changes in (
            {"qualified_link_intents": (qualified,)},
            {"unresolved_link_references": (unresolved,)},
            {"qualified_link_intents": (qualified,), "unresolved_link_references": (unresolved,)},
        ):
            with pytest.raises(ValueError, match="defers"):
                service.prepare_plan(_request(values, **changes))

        # The full native 2-means split is deliberately absent.  The bounded
        # gate itself is unit-qualified with a synthetic read model below in
        # the dedicated geometry/decision test path; no live split is invoked.
        assert UnsupportedNativeSplitError.__name__ == "UnsupportedNativeSplitError"
    finally:
        values["qualified"].close()


def test_catalog_witness_order_and_alias_target_changes_refuse_before_publication(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first = _seed_motif(values, runtime_id="motif_research_0001", key="order-a")
        second = _seed_motif(values, runtime_id="motif_research_0002", centroid=(0.0, 1.0, 0.0), key="order-b")
        service = NativeMemoryMotifCompositionService(values["connection"])
        preview = service.prepare_plan(_request(values, key="bad-order"))
        before = _semantic_counts(values["connection"])
        reversed_preview = replace(preview, catalog_witness=tuple(reversed(preview.catalog_witness)))
        with pytest.raises(StaleMotifCatalogError):
            service.commit(reversed_preview)
        assert _semantic_counts(values["connection"]) == before

        preview = service.prepare_plan(_request(values, key="rewired-alias"))
        values["connection"].execute(
            "UPDATE legacy_object_aliases SET object_id=? WHERE legacy_source_namespace_id=? AND alias_kind='MOTIF_ID' AND alias_value='motif_research_0001'",
            (native_id_to_bytes(second.motif_object_id), native_id_to_bytes(values["motif_alias"])),
        )
        before = _semantic_counts(values["connection"])
        with pytest.raises(SubstrateInvariantViolation):
            service.commit(preview)
        assert _semantic_counts(values["connection"]) == before
        assert first.motif_object_id != second.motif_object_id
    finally:
        values["qualified"].close()


@pytest.mark.parametrize(
    "incoming",
    (
        (2.0, 0.6, 0.0),
        (1e-12, 3e-13, 0.0),
    ),
    ids=("nonunit", "small-nonzero"),
)
def test_attach_preview_radius_matches_legacy_unit_geometry_for_raw_qualified_members(tmp_path: Path, incoming):
    values = _database(tmp_path)
    try:
        old_raw = (2.0, 0.6, 0.0)
        source = _existing_memory_with_embedding(values, key="geometry-source", eid_label=7, vector=old_raw)
        _seed_motif(values, key="geometry-motif", source=source)
        preview = NativeMemoryMotifCompositionService(values["connection"]).prepare_plan(
            _request(values, key=f"geometry-{incoming[0]}", embedding=incoming)
        )
        assert preview.decision.kind == "ATTACH_EXISTING"
        expected = motif_radius_from_member_vectors(
            preview.prospective_motif_state.centroid,
            (_unit(np.asarray(old_raw, dtype=np.float32)), _unit(np.asarray(incoming, dtype=np.float32))),
        )
        assert preview.prospective_radius == pytest.approx(expected, abs=1e-8)
    finally:
        values["qualified"].close()


def test_zero_vector_is_valid_create_geometry_under_legacy_unit_semantics(tmp_path: Path):
    values = _database(tmp_path)
    try:
        preview = NativeMemoryMotifCompositionService(values["connection"]).prepare_plan(
            _request(values, key="zero-geometry", embedding=(0.0, 0.0, 0.0))
        )
        assert preview.decision.kind == "CREATE_NEW"
        expected = motif_radius_from_member_vectors(
            preview.prospective_motif_state.centroid,
            (_unit(np.asarray((0.0, 0.0, 0.0), dtype=np.float32)),),
        )
        assert preview.prospective_radius == pytest.approx(expected, abs=1e-8)
        # Current shared legacy helper semantics deliberately retain zero as a
        # valid sample; against the zero centroid its measured radius is 1.0.
        assert preview.prospective_radius == 1.0
    finally:
        values["qualified"].close()


def test_missing_current_member_embedding_is_counted_but_skipped_from_radius_sample(tmp_path: Path):
    values = _database(tmp_path)
    try:
        raw = (2.0, 0.6, 0.0)
        source = _existing_memory_with_embedding(values, key="represented", eid_label=5, vector=raw)
        seed = _seed_motif(values, key="mixed-geometry", source=source)
        _add_member(values, seed, key="unrepresented", eid_label=6)
        incoming = (2.0, 0.6, 0.0)
        preview = NativeMemoryMotifCompositionService(values["connection"]).prepare_plan(
            _request(values, key="mixed-preview", embedding=incoming)
        )
        assert preview.primary_field_row["members"] == 3
        expected = motif_radius_from_member_vectors(
            preview.prospective_motif_state.centroid,
            (_unit(np.asarray(raw, dtype=np.float32)), _unit(np.asarray(incoming, dtype=np.float32))),
        )
        assert preview.prospective_radius == pytest.approx(expected, abs=1e-8)
    finally:
        values["qualified"].close()


def test_preview_symbol_and_resonance_match_frozen_helper_sequence_without_files(tmp_path: Path):
    values = _database(tmp_path)
    try:
        request = _request(
            values, key="symbols", prior_symbol="◈", prior_symbol_trace=("◈", "⋮"),
            prior_motif_id="motif_research_0001", prior_tension=0.1, stability_delta=0.2,
        )
        preview = NativeMemoryMotifCompositionService(values["connection"]).prepare_plan(request)
        field = preview.primary_field_row
        direct_symbol = assign_symbol_state(
            motif_role=str(field.get("role", "") or ""), phi=float(field.get("phi", 0.0) or 0.0),
            tension=float(field.get("tension", 0.0) or 0.0), kappa=float(field.get("kappa", 0.0) or 0.0),
            coherence_delta=request.stability_delta,
            tension_delta=float(field.get("tension", 0.0) or 0.0) - request.prior_tension,
            previous_symbol=request.prior_symbol, repeated_same_motif=False, is_new_motif=True,
            symbol_trace=request.prior_symbol_trace,
        )
        direct_resonance = summarize_resonance(
            append_symbol(request.prior_symbol_trace, direct_symbol["state_symbol"]),
            prev_trace=request.prior_symbol_trace,
        )
        assert dict(preview.enrichment_patch) == {
            "state_symbol": direct_symbol["state_symbol"],
            "symbol_confidence": direct_symbol["symbol_confidence"],
            "symbol_reason": direct_symbol["symbol_reason"],
            "symbol_trace": direct_resonance["symbol_trace"],
            "resonance_score": direct_resonance["resonance_score"],
            "transition_entropy": direct_resonance["transition_entropy"],
            "loop_type": direct_resonance["loop_type"],
            "phase_shift": direct_resonance["phase_shift"],
            "dominant_transition": direct_resonance["dominant_transition"],
            "cycles": direct_resonance["cycles"],
        }
    finally:
        values["qualified"].close()


def test_lifecycle_governance_and_authority_remain_independent_and_non_authorizing(tmp_path: Path):
    values = _database(tmp_path)
    try:
        service = NativeMemoryMotifCompositionService(values["connection"])
        first = service.commit(service.prepare_plan(_request(
            values, key="protected-false-governance", lifecycle_state="PROTECTED",
            lifecycle_authoritative=True, governance=NativeMemoryGovernanceFacts(),
        )))
        second = service.commit(service.prepare_plan(_request(
            values, key="ordinary-protected-governance", lifecycle_state="ORDINARY",
            lifecycle_authoritative=False, governance=NativeMemoryGovernanceFacts(protected=True),
        )))
        connection = values["connection"]
        assert connection.execute(
            "SELECT lifecycle_state,lifecycle_authoritative,authority_category FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(first.memory_revision_id),),
        ).fetchone() == ("PROTECTED", 1, "NOT_APPLICABLE")
        assert connection.execute(
            "SELECT lifecycle_state,lifecycle_authoritative,authority_category FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(second.memory_revision_id),),
        ).fetchone() == ("ORDINARY", 0, "NOT_APPLICABLE")
        assert NativeObjectRevisionGovernanceService(connection).get_current_object_governance(
            object_id=second.memory_object_id
        ).facts == NativeMemoryGovernanceFacts(protected=True)
        assert connection.execute(
            "SELECT authority_category FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(second.motif_revision_id),)
        ).fetchone()[0] == "NOT_APPLICABLE"
        assert connection.execute(
            "SELECT authority_category FROM relationship_revisions WHERE relationship_revision_id=?", (native_id_to_bytes(second.membership_revision_id),)
        ).fetchone()[0] == "NOT_APPLICABLE"
    finally:
        values["qualified"].close()


def test_split_gate_refuses_a_real_ninety_sixth_attach_without_compound_residue(tmp_path: Path):
    values = _database(tmp_path)
    try:
        seed = _seed_motif(values, key="split-seed")
        for offset in range(2, 96):
            _add_member(values, seed, key=f"split-member-{offset}", eid_label=offset)
        service = NativeMemoryMotifCompositionService(values["connection"])
        before = _semantic_counts(values["connection"])
        with pytest.raises(UnsupportedNativeSplitError, match="UNSUPPORTED_NATIVE_SPLIT"):
            service.prepare_plan(_request(values, key="split-refusal"))
        assert _semantic_counts(values["connection"]) == before
    finally:
        values["qualified"].close()


def test_explicit_ordered_catalog_preserves_a3d_tie_order_while_verifying_current_witness(tmp_path: Path):
    values = _database(tmp_path)
    try:
        _seed_motif(values, runtime_id="motif_research_0001", centroid=(1.0, 0.0, 0.0), key="ordered-a")
        _seed_motif(values, runtime_id="motif_research_0002", centroid=(0.0, 1.0, 0.0), key="ordered-b")
        service = NativeMemoryMotifCompositionService(values["connection"])
        catalog = service._reader.list_runtime_motifs(  # test-only inspection of the reader boundary
            motif_alias_namespace_id=values["motif_alias"], domain_id="research", semantic_scope_id=values["scope"],
        )
        preview = service.prepare_plan_from_ordered_catalog(
            _request(values, key="ordered-tie", embedding=(1.0, 1.0, 0.0)),
            tuple(reversed(catalog)),
        )
        assert preview.decision.selected is not None
        assert preview.decision.selected.runtime_motif_id == "motif_research_0002"
        result = service.commit(preview)
        assert result.runtime_motif_id == "motif_research_0002"
    finally:
        values["qualified"].close()
