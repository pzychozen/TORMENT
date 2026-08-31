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
    NativeMotifSplitPlan,
)
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
