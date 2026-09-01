"""Focused Phase 7G5A1 native motif persistence tests."""
from __future__ import annotations

from pathlib import Path
from dataclasses import replace
import sqlite3

import pytest

from torment_service.substrate.compat import NativeMemoryCompatibilityFacade
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict, SubstrateInvariantViolation, SubstrateRevisionConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.motifs import (
    DERIVED_MOTIF_OBJECT_KIND,
    MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
    MotifState,
    NativeMotifService,
    NativeMotifMergeResult,
    NativeMotifSplitPlan,
)
from torment_service.substrate.motif_runtime_reader import NativeMotifRuntimeReader
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope, NativeMotifProcessOrder
from torment_service.substrate.native_motif_merge_runtime import NativeMotifMergeRuntime
from torment_service.substrate.runtime_binding import NativeMemoryRuntimeScope
from torment_service.substrate.objects import NativeObjectService
from torment_service.substrate.relationships import NativeRelationshipService
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _database(tmp_path: Path):
    qualified = open_temporary_test_connection(tmp_path / "native-motifs.db")
    create_schema(qualified.connection)
    connection = qualified.connection
    motif_identity, membership_identity, memory_identity = _id(), _id(), _id()
    motif_scope, alternate_motif_scope, memory_scope = _id(), _id(), _id()
    idempotency, memory_alias, motif_alias, alternate_motif_alias = _id(), _id(), _id(), _id()
    for value, key in (
        (motif_identity, "native-motif-objects"),
        (membership_identity, "native-motif-memberships"),
        (memory_identity, "native-motif-memories"),
    ):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in (
        (motif_scope, "native-motif-scope"),
        (alternate_motif_scope, "native-motif-alternate-scope"),
        (memory_scope, "native-motif-memory-scope"),
    ):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "native-motif-idempotency"))
    for value, key in (
        (memory_alias, "native-motif-memory-alias"),
        (motif_alias, "native-motif-alias"),
        (alternate_motif_alias, "native-motif-alternate-alias"),
    ):
        connection.execute("INSERT INTO legacy_source_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    return {
        "qualified": qualified,
        "connection": connection,
        "motif_identity": motif_identity,
        "membership_identity": membership_identity,
        "memory_identity": memory_identity,
        "motif_scope": motif_scope,
        "alternate_motif_scope": alternate_motif_scope,
        "memory_scope": memory_scope,
        "idempotency": idempotency,
        "memory_alias": memory_alias,
        "motif_alias": motif_alias,
        "alternate_motif_alias": alternate_motif_alias,
    }


def _memory(values, eid: int, *, scope=None):
    return NativeMemoryCompatibilityFacade(values["connection"]).create_memory_state(
        legacy_source_namespace_id=values["memory_alias"],
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=f"memory-{eid}",
        identity_namespace_id=values["memory_identity"],
        semantic_scope_id=scope or values["memory_scope"],
        summary=f"memory {eid}",
        memory_type="reflection",
        logical_step=eid,
    )


def _state(values, *, motif_id="motif_reflection_0001", scope=None, step=102, strength=0.7, centroid=(0.25, -0.5, 0.75)):
    return MotifState(
        scope or values["motif_scope"],
        motif_id,
        "reflection",
        "Synthetic reflection basin",
        centroid,
        strength,
        0.8,
        ("aria", "nox"),
        101,
        step,
        {"algorithm": "already-decided-test"},
        {"test_marker": "native-motif"},
    )


def _create(values, memory, *, key="motif-create", state=None, alias=None):
    return NativeMotifService(values["connection"]).create_motif_with_member(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        motif_identity_namespace_id=values["motif_identity"],
        membership_identity_namespace_id=values["membership_identity"],
        motif_alias_namespace_id=alias or values["motif_alias"],
        state=state or _state(values),
        member_object_id=memory.object_id,
    )


def _merge(values, *, key="motif-merge", timestamp=200, a="motif_reflection_0001", b="motif_reflection_0002", source=None, fail=None):
    return NativeMotifService(values["connection"]).merge_motifs(
        idempotency_namespace_id=values["idempotency"],
        idempotency_key=key,
        legacy_source_namespace_id=source or values["memory_alias"],
        motif_identity_namespace_id=values["motif_identity"],
        motif_alias_namespace_id=values["motif_alias"],
        membership_identity_namespace_id=values["membership_identity"],
        semantic_scope_id=values["motif_scope"],
        domain_id="reflection",
        a_runtime_motif_id=a,
        b_runtime_motif_id=b,
        merge_timestamp=timestamp,
        _test_fail_after=fail,
    )


def _two_mergeable_motifs(values):
    one, two, three, four = (_memory(values, eid) for eid in range(1, 5))
    first = _create(values, one, state=_state(values, strength=0.8, centroid=(1.0, 0.0, 0.0)))
    service = NativeMotifService(values["connection"])
    added = service.add_motif_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key="merge-add-three",
        motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
        motif_object_id=first.motif_object_id, expected_motif_revision_id=first.motif_revision_id,
        state=_state(values, strength=0.8, centroid=(1.0, 0.0, 0.0), step=103), member_object_id=three.object_id,
    )
    second = _create(
        values, two, key="merge-create-second",
        state=_state(values, motif_id="motif_reflection_0002", strength=0.4, centroid=(0.0, 1.0, 0.0)),
    )
    service.add_motif_member(
        idempotency_namespace_id=values["idempotency"], idempotency_key="merge-add-four",
        motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
        motif_object_id=second.motif_object_id, expected_motif_revision_id=second.motif_revision_id,
        state=_state(values, motif_id="motif_reflection_0002", strength=0.4, centroid=(0.0, 1.0, 0.0), step=104), member_object_id=four.object_id,
    )
    return first, added, second, (one, two, three, four)


def test_native_motif_merge_is_atomic_idempotent_and_retires_the_drop_without_losing_history(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first, added, second, memories = _two_mergeable_motifs(values)
        connection = values["connection"]
        service = NativeMotifService(connection)
        before = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        with pytest.raises(RuntimeError, match="before current-pointer"):
            _merge(values, key="merge-rollback", fail="before_current_pointer_publication")
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions")) == before
        result = _merge(values)
        assert isinstance(result, NativeMotifMergeResult)
        assert _merge(values) == result
        with pytest.raises(SubstrateIdempotencyConflict):
            _merge(values, timestamp=201)
        keep = service.get_current_motif(result.keep_motif_object_id)
        drop = service.get_current_motif(result.drop_motif_object_id)
        assert (keep.motif_object_id, keep.revision_ordinal) == (first.motif_object_id, added.motif_revision_ordinal + 1)
        assert keep.state.strength == 1.0
        assert keep.state.contributing_agents == ("aria", "nox")
        assert keep.state.last_active_ts == 200
        assert keep.state.centroid == pytest.approx((0.8944271909999159, 0.4472135954999579, 0.0))
        assert drop.motif_object_id == second.motif_object_id
        assert connection.execute("SELECT existence_state FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(drop.motif_revision_id),)).fetchone() == ("RETIRED",)
        assert service.resolve_motif_alias(motif_alias_namespace_id=values["motif_alias"], runtime_motif_id="motif_reflection_0002") == second.motif_object_id
        assert service.list_current_motif_members(second.motif_object_id) == ()
        assert {item.member_object_id for item in service.list_current_motif_members(first.motif_object_id)} == {item.object_id for item in memories}
        assert len(result.retired_drop_membership_relationship_ids) == 2
        assert len(result.created_keep_membership_relationship_ids) == 2
        assert connection.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone() == (2,)
        assert connection.execute("SELECT count(*) FROM relationship_revision_effects WHERE transition_id=?", (native_id_to_bytes(result.transition_id),)).fetchone() == (4,)
        assert connection.execute("SELECT output_role,output_kind FROM operation_outputs WHERE operation_id=? ORDER BY output_ordinal", (native_id_to_bytes(result.operation_id),)).fetchall() == [
            ("MERGE_KEEP_MOTIF", "OBJECT"), ("RETIRED_DROP_MOTIF", "OBJECT"),
            ("RETIRED_DROP_MEMBERSHIP", "RELATIONSHIP"), ("RETIRED_DROP_MEMBERSHIP", "RELATIONSHIP"),
            ("MERGE_KEEP_MEMBERSHIP", "RELATIONSHIP"), ("MERGE_KEEP_MEMBERSHIP", "RELATIONSHIP"),
        ]
        reader = NativeMotifRuntimeReader(connection)
        assert [item.read_model.runtime_motif_id for item in reader.list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="reflection", semantic_scope_id=values["motif_scope"],
        )] == ["motif_reflection_0001"]
        assert [item.member_object_id for item in reader.list_ordered_current_motif_members(first.motif_object_id)] == [item.object_id for item in memories]
    finally:
        values["qualified"].close()


def test_native_motif_merge_lost_response_reconstructs_once_and_rejects_cross_scope_pre_mutation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        _two_mergeable_motifs(values)
        connection = values["connection"]
        before = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        foreign_memory = _memory(values, 9, scope=values["memory_scope"])
        _create(
            values, foreign_memory, key="foreign-motif",
            state=_state(values, motif_id="motif_reflection_foreign", scope=values["alternate_motif_scope"]),
        )
        before_cross = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        with pytest.raises(SubstrateInvariantViolation, match="semantic scopes"):
            _merge(values, key="merge-cross-scope", b="motif_reflection_foreign")
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions")) == before_cross
        foreign_domain_memory = _memory(values, 10)
        _create(
            values, foreign_domain_memory, key="foreign-domain-motif",
            state=replace(_state(values, motif_id="motif_other_0001"), domain_id="other"),
        )
        before_domain = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        with pytest.raises(SubstrateInvariantViolation, match="claimed domain"):
            _merge(values, key="merge-cross-domain", b="motif_other_0001")
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions")) == before_domain
        with pytest.raises(SubstrateInvariantViolation, match="no legacy EID alias"):
            _merge(values, key="merge-wrong-source", source=values["motif_alias"])
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions")) == before_domain
        with pytest.raises(RuntimeError, match="lost response"):
            _merge(values, key="merge-lost", fail="after_complete_before_response")
        result = _merge(values, key="merge-lost")
        assert result.operation_id is not None
        after = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        assert after == tuple(value + delta for value, delta in zip(before_domain, (1, 1, 2, 4)))
    finally:
        values["qualified"].close()


def test_native_motif_merge_reuses_the_existing_keep_membership_for_an_overlapping_member(tmp_path: Path):
    values = _database(tmp_path)
    try:
        member = _memory(values, 1)
        first = _create(values, member, state=_state(values, strength=.8, centroid=(1.0, 0.0)))
        second = _create(
            values, member, key="merge-overlap-second",
            state=_state(values, motif_id="motif_reflection_0002", strength=.4, centroid=(0.0, 1.0)),
        )
        result = _merge(values, key="merge-overlap")
        assert result.keep_motif_object_id == first.motif_object_id
        assert result.drop_motif_object_id == second.motif_object_id
        assert result.created_keep_membership_relationship_ids == ()
        assert _merge(values, key="merge-overlap") == result
        assert {item.member_object_id for item in NativeMotifService(values["connection"]).list_current_motif_members(first.motif_object_id)} == {member.object_id}
    finally:
        values["qualified"].close()


def test_native_motif_merge_runtime_reconciles_initialized_process_order_for_the_next_attach(tmp_path: Path):
    values = _database(tmp_path)
    try:
        _two_mergeable_motifs(values)
        routing_scope = NativeFabricRoutingScope(
            NativeMemoryRuntimeScope(
                "ws", "PRIVATE_AGENT", values["memory_alias"], values["memory_identity"],
                values["motif_scope"], agent_id="aria",
            ),
            values["motif_alias"], values["motif_identity"], values["membership_identity"], values["idempotency"],
        )
        process_order = NativeMotifProcessOrder()
        reader = NativeMotifRuntimeReader(values["connection"])
        with process_order.locked_catalog(reader=reader, routing_scope=routing_scope, domain_id="reflection") as catalog:
            assert [item.read_model.runtime_motif_id for item in catalog] == [
                "motif_reflection_0001", "motif_reflection_0002",
            ]
        result = NativeMotifMergeRuntime(
            values["connection"], routing_scope=routing_scope, domain_id="reflection",
            process_order=process_order,
        ).merge_suggestion({
            "suggestion_id": "merge_motif_reflection_0001__motif_reflection_0002",
            "a": "motif_reflection_0001", "b": "motif_reflection_0002", "created_ts": 300,
        }, note="manual")
        assert result is not None
        assert process_order.runtime_ids_for_testing(
            routing_scope=routing_scope, domain_id="reflection",
        ) == ("motif_reflection_0001",)
        with process_order.locked_catalog(reader=reader, routing_scope=routing_scope, domain_id="reflection") as catalog:
            assert [item.read_model.runtime_motif_id for item in catalog] == ["motif_reflection_0001"]
        # A fresh reader has no process cache and sees exactly the same live truth.
        assert [item.read_model.runtime_motif_id for item in NativeMotifRuntimeReader(values["connection"]).list_runtime_motifs(
            motif_alias_namespace_id=values["motif_alias"], domain_id="reflection", semantic_scope_id=values["motif_scope"],
        )] == ["motif_reflection_0001"]
    finally:
        values["qualified"].close()


def test_native_motif_create_is_atomic_idempotent_and_centroid_is_not_a_representation(tmp_path: Path):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        source = _memory(values, 1)
        source_before = NativeObjectService(connection).get_current_object(source.object_id)
        service = NativeMotifService(connection)
        first = _create(values, source)
        retry = _create(values, source)
        assert retry == first  # lost response reconstruction is the durable result, not a duplicate.
        with pytest.raises(SubstrateIdempotencyConflict):
            _create(values, source, state=_state(values, strength=0.8))
        current = service.get_current_motif(first.motif_object_id)
        assert current.motif_revision_id == first.motif_revision_id
        assert current.revision_ordinal == 1
        assert connection.execute("SELECT object_kind FROM objects WHERE object_id=?", (native_id_to_bytes(first.motif_object_id),)).fetchone()[0] == DERIVED_MOTIF_OBJECT_KIND
        assert current.state.centroid == (0.25, -0.5, 0.75)
        assert "members" not in current.state.payload() and "member_count" not in current.state.payload()
        assert connection.execute("SELECT authority_category FROM object_revisions WHERE object_revision_id=?", (native_id_to_bytes(first.motif_revision_id),)).fetchone()[0] == "NOT_APPLICABLE"
        assert connection.execute("SELECT authority_category FROM relationship_revisions WHERE relationship_revision_id=?", (native_id_to_bytes(first.membership_relationship_revision_id),)).fetchone()[0] == "NOT_APPLICABLE"
        assert service.resolve_motif_alias(motif_alias_namespace_id=values["motif_alias"], runtime_motif_id="motif_reflection_0001") == first.motif_object_id
        members = service.list_current_motif_members(first.motif_object_id)
        assert [(item.member_object_id, item.member_semantic_scope_id) for item in members] == [(source.object_id, values["memory_scope"])]
        endpoint_view = NativeRelationshipService(connection).get_current_relationship(first.membership_relationship_id)
        assert [(item.ordinal, item.role, item.binding_mode, item.object_revision_id) for item in endpoint_view.endpoints] == [
            (0, "MOTIF", "IDENTITY", None),
            (1, "MEMBER", "IDENTITY", None),
        ]
        assert NativeObjectService(connection).get_current_object(source.object_id) == source_before
        assert connection.execute("SELECT count(*) FROM representations").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM representation_payloads").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM operation_outputs WHERE operation_id=?", (native_id_to_bytes(first.operation_id),)).fetchone()[0] == 2
        assert connection.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (native_id_to_bytes(first.transition_id),)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revision_effects WHERE transition_id=?", (native_id_to_bytes(first.transition_id),)).fetchone()[0] == 1
        assert connection.execute(
            "SELECT output_role,output_kind FROM operation_outputs WHERE operation_id=? ORDER BY output_ordinal",
            (native_id_to_bytes(first.operation_id),),
        ).fetchall() == [("MOTIF", "OBJECT"), ("MOTIF_MEMBERSHIP", "RELATIONSHIP")]
        counts = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions"))
        assert service.get_current_motif(first.motif_object_id).motif_revision_id == first.motif_revision_id
        assert service.list_current_motif_members(first.motif_object_id) == members
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("operations", "semantic_transitions", "object_revisions", "relationship_revisions")) == counts
    finally:
        values["qualified"].close()


def test_add_member_advances_state_atomically_rejects_duplicates_and_preserves_identity_binding(tmp_path: Path):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        first_memory, second_memory, third_memory = _memory(values, 1), _memory(values, 2), _memory(values, 3)
        created = _create(values, first_memory)
        service = NativeMotifService(connection)
        source_before = NativeObjectService(connection).get_current_object(second_memory.object_id)
        second_state = _state(values, step=103, strength=0.75, centroid=(0.3, -0.45, 0.75))
        added = service.add_motif_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="motif-add-second",
            motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
            motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
            state=second_state, member_object_id=second_memory.object_id,
        )
        assert service.add_motif_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="motif-add-second",
            motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
            motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
            state=second_state, member_object_id=second_memory.object_id,
        ) == added
        with pytest.raises(SubstrateIdempotencyConflict):
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key="motif-add-second",
                motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
                state=second_state, member_object_id=third_memory.object_id,
            )
        assert service.get_current_motif(created.motif_object_id).motif_revision_id == added.motif_revision_id
        assert service.get_current_motif(created.motif_object_id).revision_ordinal == 2
        assert {item.member_object_id for item in service.list_current_motif_members(created.motif_object_id)} == {first_memory.object_id, second_memory.object_id}
        assert NativeObjectService(connection).get_current_object(second_memory.object_id) == source_before
        assert connection.execute("SELECT count(*) FROM object_revision_effects WHERE transition_id=?", (native_id_to_bytes(added.transition_id),)).fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM relationship_revision_effects WHERE transition_id=?", (native_id_to_bytes(added.transition_id),)).fetchone()[0] == 1
        duplicate_counts = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "relationship_revisions", "object_revisions"))
        with pytest.raises(SubstrateRevisionConflict):
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key="motif-add-duplicate",
                motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=added.motif_revision_id,
                state=_state(values, step=104, strength=0.8), member_object_id=second_memory.object_id,
            )
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "relationship_revisions", "object_revisions")) == duplicate_counts
        with pytest.raises(SubstrateRevisionConflict):
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key="motif-add-stale",
                motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
                state=_state(values, step=104, strength=0.8), member_object_id=third_memory.object_id,
            )
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "relationship_revisions", "object_revisions")) == duplicate_counts
        relationship_before = NativeRelationshipService(connection).get_current_relationship(added.membership_relationship_id)
        advanced_source = NativeMemoryCompatibilityFacade(connection).patch_memory_state(
            legacy_source_namespace_id=values["memory_alias"], eid=second_memory.eid, patch={"note": "R2"},
            idempotency_namespace_id=values["idempotency"], idempotency_key="advance-source",
            expected_revision_id=second_memory.revision_id,
        )
        assert advanced_source.revision_id != second_memory.revision_id
        assert NativeRelationshipService(connection).get_current_relationship(added.membership_relationship_id) == relationship_before
    finally:
        values["qualified"].close()


def test_native_split_retires_parent_memberships_without_reusing_relationship_identity(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first, moved, retained, candidate = (_memory(values, index) for index in range(1, 5))
        created = _create(values, first)
        service = NativeMotifService(values["connection"])
        for memory, key in ((moved, "split-add-moved"), (retained, "split-add-retained")):
            current = service.get_current_motif(created.motif_object_id)
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key=key,
                motif_alias_namespace_id=values["motif_alias"],
                membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
                state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
                member_object_id=memory.object_id,
            )
        current = service.get_current_motif(created.motif_object_id)
        moved_membership = next(item for item in service.list_current_motif_members(created.motif_object_id) if item.member_object_id == moved.object_id)
        parent_state = replace(current.state, centroid=(0.1, -0.4, 0.8), last_active_ts=current.state.last_active_ts + 1)
        child_state = _state(
            values, motif_id="motif_reflection_0001_split_0002", step=parent_state.last_active_ts,
            centroid=(-0.2, 0.3, 0.7), strength=.6,
        )
        plan = NativeMotifSplitPlan(
            created.motif_object_id, current.motif_revision_id, parent_state, child_state,
            (moved.object_id,), candidate.object_id, True,
        )
        result = service.split_motif_with_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="split-native",
            motif_identity_namespace_id=values["motif_identity"],
            membership_identity_namespace_id=values["membership_identity"],
            motif_alias_namespace_id=values["motif_alias"], plan=plan,
        )
        assert service.split_motif_with_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key="split-native",
            motif_identity_namespace_id=values["motif_identity"],
            membership_identity_namespace_id=values["membership_identity"],
            motif_alias_namespace_id=values["motif_alias"], plan=plan,
        ) == result
        assert {item.member_object_id for item in service.list_current_motif_members(created.motif_object_id)} == {first.object_id, retained.object_id}
        assert {item.member_object_id for item in service.list_current_motif_members(result.child_motif_object_id)} == {moved.object_id, candidate.object_id}
        retired = values["connection"].execute(
            "SELECT relationship_revision_id,predecessor_revision_id,predecessor_revision_ordinal,existence_state FROM relationship_revisions WHERE relationship_id=? ORDER BY revision_ordinal",
            (native_id_to_bytes(moved_membership.relationship_id),),
        ).fetchall()
        assert retired[0][3] == "EXISTS"
        assert retired[1][1:] == (native_id_to_bytes(moved_membership.relationship_revision_id), 1, "RETIRED")
        assert service.resolve_motif_alias(
            motif_alias_namespace_id=values["motif_alias"], runtime_motif_id="motif_reflection_0001_split_0002",
        ) == result.child_motif_object_id
        # Revision rows are immutable.  A malformed retirement cannot be
        # injected after publication, and both readers defensively validate
        # current retirement lineage before excluding it from active geometry.
        with pytest.raises(sqlite3.IntegrityError, match="immutable relationship revision"):
            values["connection"].execute(
                "UPDATE relationship_revisions SET predecessor_revision_id=NULL,predecessor_revision_ordinal=NULL WHERE relationship_revision_id=?",
                (retired[1][0],),
            )
    finally:
        values["qualified"].close()


@pytest.mark.parametrize("seam", (
    "parent_successor", "child_object", "first_retirement",
    "child_memberships", "before_current_pointer_publication",
))
def test_native_split_rolls_back_every_partial_topology_seam(tmp_path: Path, seam: str):
    values = _database(tmp_path)
    try:
        first, moved, candidate = (_memory(values, index) for index in range(11, 14))
        created = _create(values, first, key=f"split-rollback-create:{seam}")
        service = NativeMotifService(values["connection"])
        current = service.get_current_motif(created.motif_object_id)
        service.add_motif_member(
            idempotency_namespace_id=values["idempotency"], idempotency_key=f"split-rollback-add:{seam}",
            motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
            motif_object_id=created.motif_object_id, expected_motif_revision_id=current.motif_revision_id,
            state=replace(current.state, last_active_ts=current.state.last_active_ts + 1), member_object_id=moved.object_id,
        )
        current = service.get_current_motif(created.motif_object_id)
        plan = NativeMotifSplitPlan(
            created.motif_object_id, current.motif_revision_id,
            replace(current.state, last_active_ts=current.state.last_active_ts + 1),
            _state(values, motif_id=f"motif_reflection_0001_split_{seam}", step=current.state.last_active_ts + 1),
            (moved.object_id,), candidate.object_id, True,
        )
        before = tuple(values["connection"].execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
            "objects", "object_revisions", "relationships", "relationship_revisions", "semantic_transitions", "operation_outputs",
        ))
        with pytest.raises(RuntimeError, match="forced native motif split failure"):
            service.split_motif_with_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key=f"split-rollback:{seam}",
                motif_identity_namespace_id=values["motif_identity"], membership_identity_namespace_id=values["membership_identity"],
                motif_alias_namespace_id=values["motif_alias"], plan=plan, _test_fail_after=seam,
            )
        after = tuple(values["connection"].execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
            "objects", "object_revisions", "relationships", "relationship_revisions", "semantic_transitions", "operation_outputs",
        ))
        assert after == before
        assert len(service.list_current_motif_members(created.motif_object_id)) == 2
    finally:
        values["qualified"].close()


def test_add_member_rolls_back_when_membership_effect_or_motif_successor_fails(tmp_path: Path, monkeypatch):
    values = _database(tmp_path)
    try:
        connection = values["connection"]
        first_memory, second_memory = _memory(values, 1), _memory(values, 2)
        created = _create(values, first_memory)
        service = NativeMotifService(connection)
        baseline = tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "object_revisions", "relationship_revisions"))
        original_publish = service._publish

        def omit_membership_effect(*args, **kwargs):
            kwargs["omit_membership_effect"] = True
            return original_publish(*args, **kwargs)

        monkeypatch.setattr(service, "_publish", omit_membership_effect)
        with pytest.raises(SubstrateInvariantViolation):
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key="missing-membership-effect",
                motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
                state=_state(values, step=103, strength=0.75), member_object_id=second_memory.object_id,
            )
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "object_revisions", "relationship_revisions")) == baseline
        assert service.get_current_motif(created.motif_object_id).motif_revision_id == created.motif_revision_id
        assert {item.member_object_id for item in service.list_current_motif_members(created.motif_object_id)} == {first_memory.object_id}
        monkeypatch.setattr(service, "_publish", original_publish)

        def fail_successor(*_args, **_kwargs):
            raise RuntimeError("forced motif successor failure")

        monkeypatch.setattr(service, "_insert_motif_successor", fail_successor)
        with pytest.raises(RuntimeError, match="forced motif successor failure"):
            service.add_motif_member(
                idempotency_namespace_id=values["idempotency"], idempotency_key="forced-successor-failure",
                motif_alias_namespace_id=values["motif_alias"], membership_identity_namespace_id=values["membership_identity"],
                motif_object_id=created.motif_object_id, expected_motif_revision_id=created.motif_revision_id,
                state=_state(values, step=103, strength=0.75), member_object_id=second_memory.object_id,
            )
        assert tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("semantic_transitions", "object_revisions", "relationship_revisions")) == baseline
    finally:
        values["qualified"].close()


def test_scoped_aliases_are_distinct_and_state_advance_is_immutable(tmp_path: Path):
    values = _database(tmp_path)
    try:
        first_memory, second_memory = _memory(values, 1), _memory(values, 2)
        first = _create(values, first_memory)
        alternate = _create(
            values,
            second_memory,
            key="alternate-motif-create",
            alias=values["alternate_motif_alias"],
            state=_state(values, scope=values["alternate_motif_scope"]),
        )
        service = NativeMotifService(values["connection"])
        assert first.motif_object_id != alternate.motif_object_id
        assert service.resolve_motif_alias(motif_alias_namespace_id=values["motif_alias"], runtime_motif_id="motif_reflection_0001") == first.motif_object_id
        assert service.resolve_motif_alias(motif_alias_namespace_id=values["alternate_motif_alias"], runtime_motif_id="motif_reflection_0001") == alternate.motif_object_id
        advanced = service.advance_motif_state(
            idempotency_namespace_id=values["idempotency"], idempotency_key="motif-state-advance",
            motif_alias_namespace_id=values["motif_alias"], motif_object_id=first.motif_object_id,
            expected_motif_revision_id=first.motif_revision_id,
            state=_state(values, step=103, strength=0.8, centroid=(0.2, -0.4, 0.8)),
        )
        assert advanced.membership_relationship_id is None
        assert NativeObjectService(values["connection"]).get_object_revision(first.motif_revision_id).revision_id == first.motif_revision_id
        with pytest.raises(sqlite3.IntegrityError):
            values["connection"].execute(
                "UPDATE object_revisions SET payload_text='{}' WHERE object_revision_id=?",
                (native_id_to_bytes(first.motif_revision_id),),
            )
        with pytest.raises(sqlite3.IntegrityError):
            values["connection"].execute(
                "UPDATE relationship_revisions SET lifecycle_state='ACTIVE' WHERE relationship_id=?",
                (native_id_to_bytes(first.membership_relationship_id),),
            )
        with pytest.raises(SubstrateRevisionConflict):
            service.advance_motif_state(
                idempotency_namespace_id=values["idempotency"], idempotency_key="motif-state-stale",
                motif_alias_namespace_id=values["motif_alias"], motif_object_id=first.motif_object_id,
                expected_motif_revision_id=first.motif_revision_id,
                state=_state(values, step=104, strength=0.85),
            )
        assert service.get_current_motif(first.motif_object_id).motif_revision_id == advanced.motif_revision_id
        assert values["connection"].execute(
            "SELECT count(*) FROM relationships WHERE relationship_kind=?", (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,)
        ).fetchone()[0] == 2
    finally:
        values["qualified"].close()
