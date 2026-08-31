"""Phase 7G5B2 evidence-bounded R1 -> R2 normalization qualification."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from uuid import UUID

import pytest

from torment_service.provenance_v1 import ProvenanceV1
from torment_service.governance import resolve_governance
from torment_service.substrate.connection import open_temporary_test_connection
from torment_service.substrate.errors import SubstrateIdempotencyConflict
from torment_service.substrate.ids import generate_native_id, native_id_to_bytes
from torment_service.substrate.migration import (
    MigrationRehearsalConfig,
    MigrationRuntimeNormalizationRefused,
    MigrationRuntimeNormalizationRequest,
    MigrationRuntimeReadinessRequest,
    MigrationRuntimeScopePlan,
    NativeLegacyMigrationRehearsal,
    NativeMigrationRuntimeNormalizationService,
    NativeMigrationRuntimeReadinessPreflight,
    ObjectRuntimeReadiness,
    create_snapshot_manifest,
)
from torment_service.substrate.native_memory_runtime_access import NativePostWriteMemoryAccess
from torment_service.substrate.runtime_binding import NativeRepresentationLane
from torment_service.substrate.schema import create_schema


def _id():
    return generate_native_id()


def _line(value: dict[str, object]) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def _provenance() -> dict[str, object]:
    return ProvenanceV1(
        source_type="role_output", source_role="archivist",
        write_path="cognition_writeback", parent_eids=[], created_at_step=4,
        created_at_ts="2024-01-02T03:04:05Z",
    ).to_dict()


def _lifecycle() -> dict[str, object]:
    return {
        "state": "active", "is_authoritative_on_row": True,
        "requires_join": None,
        "set_by": {"actor": "user", "via": "api", "at": 7},
        "history_ref": None,
    }


def _payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "summary": "evidence-complete legacy memory", "type": "memory", "memory_class": "core",
        "strength": 0.75, "confidence": 0.9, "seed_pos0": [1, 2, 3], "seed_v0": [0.1, 0.2, 0.3],
        "governance": {
            "protected": False, "non_shareable": True, "collective_export_blocked": True,
            "collective_reingest_blocked": False, "decay_accelerated": False,
        },
        "provenance": _provenance(), "lifecycle_status": _lifecycle(),
    }
    value.update(overrides)
    return value


def _absent_governance_payload(**overrides: object) -> dict[str, object]:
    value = _payload(**overrides)
    value.pop("governance")
    return value


def _fixture(tmp_path: Path, rows: list[dict[str, object]] | None = None):
    qualified = open_temporary_test_connection(tmp_path / "b2-normalization.db")
    connection = qualified.connection
    metadata = create_schema(connection)
    object_namespace, relationship_namespace = _id(), _id()
    unknown_scope, target_scope, idempotency = _id(), _id(), _id()
    for value, key in ((object_namespace, "b2-objects"), (relationship_namespace, "b2-relationships")):
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(value), key))
    for value, key in ((unknown_scope, "b2-unknown"), (target_scope, "b2-target")):
        connection.execute("INSERT INTO semantic_scopes VALUES (?,?,0)", (native_id_to_bytes(value), key))
    connection.execute("INSERT INTO idempotency_namespaces VALUES (?,?)", (native_id_to_bytes(idempotency), "b2-idempotency"))
    root = tmp_path / "frozen" / "legacy"
    root.mkdir(parents=True)
    actual_rows = rows or [{"eid": 7, "born_step": 12, "channel": 4, "payload": _payload()}]
    (root / "nodes.jsonl").write_bytes(b"".join(_line(row) for row in actual_rows))
    source_namespace = _id()
    manifest_path = root.parent / "manifest.json"
    manifest = create_snapshot_manifest(
        snapshot_root=root, manifest_path=manifest_path,
        legacy_source_namespace_id=source_namespace, legacy_source_namespace_key="b2-source",
        capture_label="B2 evidence-complete controlled fixture",
    )
    NativeLegacyMigrationRehearsal(connection).run(
        snapshot_root=root, manifest_path=manifest_path,
        config=MigrationRehearsalConfig(
            native_core_id=_id(), idempotency_namespace_id=idempotency,
            object_identity_namespace_id=object_namespace,
            relationship_identity_namespace_id=relationship_namespace,
            unknown_semantic_scope_id=unknown_scope,
        ),
    )
    plan = MigrationRuntimeScopePlan(
        legacy_source_namespace_id=source_namespace, workspace_id="orchard",
        scope_kind="PRIVATE_AGENT", agent_id="aria",
        target_identity_namespace_id=object_namespace, target_semantic_scope_id=target_scope,
        motif_alias_namespace_id=source_namespace, motif_identity_namespace_id=object_namespace,
        membership_identity_namespace_id=relationship_namespace, idempotency_namespace_id=idempotency,
    )
    lane = NativeRepresentationLane(
        provider="synthetic", model="synthetic", dimension=3,
        representation_class="COMPAT_EMBEDDING", generation=1,
        derivation_contract_version="compat-embedding-v1", encoding_id="RAW_VECTOR", dtype="float32",
    )
    return qualified, {
        "metadata": metadata, "root": root, "manifest_path": manifest_path, "manifest": manifest,
        "source_namespace": source_namespace, "plan": plan, "lane": lane, "idempotency": idempotency,
    }


def _request(facts: dict[str, object], *, eid: int = 7, key: str = "normalize-7") -> MigrationRuntimeNormalizationRequest:
    return MigrationRuntimeNormalizationRequest(
        snapshot_root=facts["root"], manifest_path=facts["manifest_path"],
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        legacy_source_namespace_id=facts["source_namespace"],
        expected_native_core_id=UUID(bytes=facts["metadata"].core_id), eid=eid,
        expected_revision_id=facts["r1_by_eid"][eid], scope_plans=(facts["plan"],),
        idempotency_namespace_id=facts["idempotency"], idempotency_key=key,
    )


def _add_r1_ids(connection, facts: dict[str, object]) -> None:
    facts["r1_by_eid"] = {
        int(alias): UUID(bytes=revision)
        for alias, revision in connection.execute(
            """SELECT alias.alias_value,object.current_revision_id
                 FROM legacy_object_aliases alias JOIN objects object USING(object_id)
                 WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='EID'""",
            (native_id_to_bytes(facts["source_namespace"]),),
        )
    }


def _counts(connection) -> tuple[int, ...]:
    return tuple(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in (
        "objects", "object_revisions", "provenance_records", "object_revision_governance",
        "legacy_object_aliases", "memory_runtime_enumeration_orders", "representations",
        "operations", "semantic_transitions", "object_revision_effects",
    ))


def _readiness_request(facts: dict[str, object]) -> MigrationRuntimeReadinessRequest:
    return MigrationRuntimeReadinessRequest(
        legacy_snapshot_id=facts["manifest"].legacy_snapshot_id,
        expected_native_core_id=UUID(bytes=facts["metadata"].core_id),
        scope_plans=(facts["plan"],), target_lane=facts["lane"],
    )


def test_evidence_complete_r1_normalizes_once_and_b1_moves_to_representation_gap(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    try:
        connection = qualified.connection
        _add_r1_ids(connection, facts)
        before = NativeMigrationRuntimeReadinessPreflight(connection).run(_readiness_request(facts))
        assert before.object_items[0].readiness is ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
        before_counts = _counts(connection)
        result = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(_request(facts))
        assert result.revision_ordinal == result.predecessor_revision_ordinal + 1 == 2
        assert _counts(connection) == tuple(value + delta for value, delta in zip(before_counts, (0, 1, 1, 1, 0, 0, 0, 1, 1, 1)))
        r1 = connection.execute(
            "SELECT lineage_kind,payload_format,payload_text FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(result.predecessor_revision_id),),
        ).fetchone()
        assert r1[0:2] == ("LEGACY_PREDECESSOR_UNKNOWN", "TEXT")
        r2 = connection.execute(
            """SELECT lineage_kind,predecessor_revision_id,predecessor_revision_ordinal,
                      lifecycle_state,lifecycle_authoritative,lifecycle_actor,lifecycle_via,lifecycle_set_at_ns,
                      governance_state,authority_category,payload_format,payload_text
                 FROM object_revisions WHERE object_revision_id=?""",
            (native_id_to_bytes(result.revision_id),),
        ).fetchone()
        assert r2[:10] == (
            "NATIVE_ORDINARY", native_id_to_bytes(result.predecessor_revision_id), 1,
            "ACTIVE", 1, "user", "api", 7_000_000_000, "EXPLICIT", "NOT_APPLICABLE",
        )
        payload = json.loads(r2[11])
        assert r2[10] == "JSON"
        assert payload["pos"] == [1.0, 2.0, 3.0]
        assert payload["vel"] == pytest.approx([0.1, 0.2, 0.3])
        assert payload["vel0"] == pytest.approx([0.1, 0.2, 0.3])
        assert payload["alive"] is True and "born_step" not in payload and "channel" not in payload
        assert NativePostWriteMemoryAccess(
            connection, legacy_source_namespace_id=facts["source_namespace"], expected_dimension=3,
        ).get_current(7).summary == "evidence-complete legacy memory"
        after = NativeMigrationRuntimeReadinessPreflight(connection).run(_readiness_request(facts))
        assert after.object_items[0].readiness is ObjectRuntimeReadiness.REPRESENTATION_BOOTSTRAP_REQUIRED
        assert connection.execute("SELECT count(*) FROM representations WHERE representation_class='COMPAT_EMBEDDING'").fetchone()[0] == 0
    finally:
        qualified.close()


def test_absent_legacy_governance_uses_only_the_frozen_production_default_rule(tmp_path: Path):
    row = {"eid": 7, "born_step": 12, "channel": 4, "payload": _absent_governance_payload()}
    qualified, facts = _fixture(tmp_path, [row])
    try:
        connection = qualified.connection
        source_bytes = (facts["root"] / "nodes.jsonl").read_bytes()
        _add_r1_ids(connection, facts)
        before = NativeMigrationRuntimeReadinessPreflight(connection).run(_readiness_request(facts))
        item = before.object_items[0]
        assert item.governance.value == "DERIVABLE_BY_FROZEN_LEGACY_RULE"
        assert item.readiness is ObjectRuntimeReadiness.DETERMINISTIC_NORMALIZATION_REQUIRED
        assert resolve_governance(row["payload"]).to_dict() == {
            "protected": False, "non_shareable": False, "decay_accelerated": False,
            "collective_export_blocked": False, "collective_reingest_blocked": False,
        }
        result = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(_request(facts))
        assert (facts["root"] / "nodes.jsonl").read_bytes() == source_bytes
        assert connection.execute(
            """SELECT protected,non_shareable,collective_export_blocked,
                      collective_reingest_blocked,decay_accelerated
                 FROM object_revision_governance
                WHERE object_id=? AND object_revision_id=? AND object_revision_ordinal=2""",
            (native_id_to_bytes(result.object_id), native_id_to_bytes(result.revision_id)),
        ).fetchone() == (0, 0, 0, 0, 0)
        r2_payload = json.loads(connection.execute(
            "SELECT payload_text FROM object_revisions WHERE object_revision_id=?",
            (native_id_to_bytes(result.revision_id),),
        ).fetchone()[0])
        assert "governance" not in r2_payload
    finally:
        qualified.close()


def test_absent_governance_and_protected_lifecycle_remain_distinct_r2_facts(tmp_path: Path):
    protected_lifecycle = {**_lifecycle(), "state": "protected"}
    payload = _absent_governance_payload(lifecycle_status=protected_lifecycle, canon=True)
    qualified, facts = _fixture(tmp_path, [{"eid": 7, "payload": payload}])
    try:
        connection = qualified.connection
        _add_r1_ids(connection, facts)
        result = NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(_request(facts))
        revision = connection.execute(
            """SELECT lifecycle_state,lifecycle_authoritative,governance_state
                 FROM object_revisions WHERE object_revision_id=?""",
            (native_id_to_bytes(result.revision_id),),
        ).fetchone()
        governance = connection.execute(
            """SELECT protected,non_shareable,collective_export_blocked,
                      collective_reingest_blocked,decay_accelerated
                 FROM object_revision_governance WHERE object_revision_id=?""",
            (native_id_to_bytes(result.revision_id),),
        ).fetchone()
        assert revision == ("PROTECTED", 1, "EXPLICIT")
        assert governance == (0, 0, 0, 0, 0)
    finally:
        qualified.close()


def test_controlled_b1_unresolved_fixture_still_refuses_without_effects(tmp_path: Path):
    from test_substrate_migration_runtime_readiness import _fixture as b1_fixture

    qualified, request, plan = b1_fixture(tmp_path)
    try:
        connection = qualified.connection
        revision = UUID(bytes=connection.execute(
            """SELECT object.current_revision_id FROM objects object JOIN legacy_object_aliases alias USING(object_id)
                 WHERE alias.legacy_source_namespace_id=? AND alias.alias_value='1'""",
            (native_id_to_bytes(plan.legacy_source_namespace_id),),
        ).fetchone()[0])
        before = _counts(connection)
        with pytest.raises(MigrationRuntimeNormalizationRefused):
            NativeMigrationRuntimeNormalizationService(connection).normalize_legacy_core_memory(
                MigrationRuntimeNormalizationRequest(
                    snapshot_root=tmp_path / "snapshot" / "legacy", manifest_path=tmp_path / "snapshot" / "snapshot-manifest.json",
                    legacy_snapshot_id=request.legacy_snapshot_id, legacy_source_namespace_id=plan.legacy_source_namespace_id,
                    expected_native_core_id=request.expected_native_core_id, eid=1, expected_revision_id=revision,
                    scope_plans=(plan,), idempotency_namespace_id=plan.idempotency_namespace_id, idempotency_key="b2-must-refuse",
                )
            )
        assert _counts(connection) == before
        report = NativeMigrationRuntimeReadinessPreflight(connection).run(request)
        assert sum(item.readiness is ObjectRuntimeReadiness.SEMANTIC_FACTS_UNRESOLVED for item in report.object_items) == 2
    finally:
        qualified.close()


@pytest.mark.parametrize("payload_patch,outer_patch,code", [
    ({"governance": {}}, {}, "B2_EXPLICIT_GOVERNANCE_REQUIRED"),
    ({"governance": {"protected": False}}, {}, "B2_EXPLICIT_GOVERNANCE_REQUIRED"),
    ({"governance": {"protected": 0, "non_shareable": False, "collective_export_blocked": False, "collective_reingest_blocked": False, "decay_accelerated": False}}, {}, "B2_EXPLICIT_GOVERNANCE_REQUIRED"),
    ({}, {"governance": {"protected": True}}, "B2_GOVERNANCE_EVIDENCE_CONFLICT"),
    ({"provenance": "unknown"}, {}, "B2_EXACT_PROVENANCE_V1_REQUIRED"),
    ({}, {"provenance": {"source_type": "user_input"}}, "B2_PROVENANCE_EVIDENCE_CONFLICT"),
    ({"lifecycle_status": None}, {}, "B2_EXPLICIT_LIFECYCLE_REQUIRED"),
    ({"lifecycle_status": {**_lifecycle(), "state": "unset"}, "canon": True}, {}, "B2_EXPLICIT_LIFECYCLE_REQUIRED"),
    ({}, {"lifecycle_status": {**_lifecycle(), "state": "protected"}}, "B2_LIFECYCLE_EVIDENCE_CONFLICT"),
])
def test_incomplete_or_conflicting_evidence_refuses_pre_semantic(
    tmp_path: Path, payload_patch: dict[str, object], outer_patch: dict[str, object], code: str,
):
    payload = _payload(**payload_patch)
    row = {"eid": 7, "payload": payload, **outer_patch}
    qualified, facts = _fixture(tmp_path, [row])
    try:
        _add_r1_ids(qualified.connection, facts)
        before = _counts(qualified.connection)
        with pytest.raises(MigrationRuntimeNormalizationRefused, match=code):
            NativeMigrationRuntimeNormalizationService(qualified.connection).normalize_legacy_core_memory(_request(facts))
        assert _counts(qualified.connection) == before
    finally:
        qualified.close()


def test_missing_payload_and_top_level_text_never_become_runtime_payload(tmp_path: Path):
    qualified, facts = _fixture(tmp_path, [{"eid": 7, "text": "not a loader payload"}])
    try:
        _add_r1_ids(qualified.connection, facts)
        before = _counts(qualified.connection)
        with pytest.raises(MigrationRuntimeNormalizationRefused, match="B2_LEGACY_PAYLOAD_REQUIRED"):
            NativeMigrationRuntimeNormalizationService(qualified.connection).normalize_legacy_core_memory(_request(facts))
        assert _counts(qualified.connection) == before
    finally:
        qualified.close()


def test_scope_identity_alias_order_and_currentness_all_fail_closed(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    try:
        connection = qualified.connection
        _add_r1_ids(connection, facts)
        service = NativeMigrationRuntimeNormalizationService(connection)
        request = _request(facts)
        bad_plan = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=facts["source_namespace"], workspace_id="orchard",
            scope_kind="PRIVATE_AGENT", agent_id="aria", target_identity_namespace_id=_id(),
            target_semantic_scope_id=facts["plan"].target_semantic_scope_id,
            motif_alias_namespace_id=facts["source_namespace"], motif_identity_namespace_id=facts["plan"].motif_identity_namespace_id,
            membership_identity_namespace_id=facts["plan"].membership_identity_namespace_id,
            idempotency_namespace_id=facts["idempotency"],
        )
        with pytest.raises(MigrationRuntimeNormalizationRefused, match="B2_SCOPE_PLAN_AMBIGUOUS"):
            service.normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(**{**request.__dict__, "scope_plans": (facts["plan"], bad_plan)}))
        with pytest.raises(MigrationRuntimeNormalizationRefused, match="B2_SCOPE_PLAN_MISSING"):
            service.normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(**{**request.__dict__, "scope_plans": ()}))
        different_identity = _id()
        connection.execute("INSERT INTO identity_namespaces VALUES (?,?,0)", (native_id_to_bytes(different_identity), "b2-different"))
        wrong_identity = MigrationRuntimeScopePlan(
            legacy_source_namespace_id=facts["source_namespace"], workspace_id="orchard", scope_kind="PRIVATE_AGENT", agent_id="aria",
            target_identity_namespace_id=different_identity, target_semantic_scope_id=facts["plan"].target_semantic_scope_id,
            motif_alias_namespace_id=facts["source_namespace"], motif_identity_namespace_id=facts["plan"].motif_identity_namespace_id,
            membership_identity_namespace_id=facts["plan"].membership_identity_namespace_id, idempotency_namespace_id=facts["idempotency"],
        )
        with pytest.raises(MigrationRuntimeNormalizationRefused, match="B2_OBJECT_IDENTITY_NAMESPACE_MISMATCH"):
            service.normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(**{**request.__dict__, "scope_plans": (wrong_identity,)}))
        result = service.normalize_legacy_core_memory(request)
        with pytest.raises(MigrationRuntimeNormalizationRefused, match="B2_CURRENT_R1_REQUIRED"):
            service.normalize_legacy_core_memory(
                MigrationRuntimeNormalizationRequest(**{**request.__dict__, "idempotency_key": "cannot-rebase"})
            )
        assert result.revision_ordinal == 2
    finally:
        qualified.close()


def test_rollback_retry_and_response_loss_are_one_r2_only(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    try:
        connection = qualified.connection
        _add_r1_ids(connection, facts)
        service = NativeMigrationRuntimeNormalizationService(connection)
        request = _request(facts, key="retryable")
        before = _counts(connection)
        with pytest.raises(RuntimeError, match="rollback"):
            service.normalize_legacy_core_memory(request, _test_fail_after_provenance=True)
        assert _counts(connection) == before
        with pytest.raises(RuntimeError, match="response loss"):
            service.normalize_legacy_core_memory(request, _test_lose_response_after_commit=True)
        after_commit = _counts(connection)
        recovered = service.normalize_legacy_core_memory(request)
        assert recovered.revision_ordinal == 2 and _counts(connection) == after_commit
        with pytest.raises(SubstrateIdempotencyConflict):
            service.normalize_legacy_core_memory(MigrationRuntimeNormalizationRequest(
                **{**request.__dict__, "expected_native_core_id": _id()}
            ))
    finally:
        qualified.close()


def test_snapshot_mutation_refuses_before_any_normalization(tmp_path: Path):
    qualified, facts = _fixture(tmp_path)
    try:
        _add_r1_ids(qualified.connection, facts)
        (facts["root"] / "nodes.jsonl").write_text("changed\n", encoding="utf-8")
        before = _counts(qualified.connection)
        with pytest.raises(Exception):
            NativeMigrationRuntimeNormalizationService(qualified.connection).normalize_legacy_core_memory(_request(facts))
        assert _counts(qualified.connection) == before
    finally:
        qualified.close()
