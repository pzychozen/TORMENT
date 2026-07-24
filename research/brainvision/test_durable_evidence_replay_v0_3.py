from __future__ import annotations

import copy
from pathlib import Path

import pytest

import durable_evidence_primary_writer_v0_3 as writer
import durable_evidence_replay_v0_3 as replay
import durable_evidence_schema_v0_3 as schema


EXECUTION_IDENTITY = "8" * 64
SCIENTIFIC_AUTHORITY = "9" * 64
PUBLICATION_AUTHORITY = "a" * 64
PUBLICATION_RECOVERY_AUTHORITY = "b" * 64
PUBLICATION_CHAIN = schema.publication_chain_identity(
    publication_projection_identity="c" * 64,
    publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
)
PUBLICATION_RECOVERY_CHAIN = schema.publication_recovery_chain_identity(
    original_publication_chain_identity=PUBLICATION_CHAIN,
    publication_recovery_authorization_identity=PUBLICATION_RECOVERY_AUTHORITY,
)


def _stored_scientific(
    *,
    kind: str,
    sequence: int,
    predecessor: str,
    payload: dict,
    attempt: str,
    authority: str = SCIENTIFIC_AUTHORITY,
):
    logical = schema.build_scientific_logical_record(
        record_kind=kind,
        sequence_number=sequence,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=authority,
        predecessor_logical_record_sha256=predecessor,
        payload=payload,
    )
    return schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt,
    )


def _stored_publication(attempt: str):
    logical = schema.build_publication_logical_record(
        record_kind="PUBLICATION_PROJECTION_AUTHORITY_ACCEPTED",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity=PUBLICATION_AUTHORITY,
        publication_chain_identity=PUBLICATION_CHAIN,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"accepted": True},
    )
    return schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt,
    )


def _stored_recovery(attempt: str):
    logical = schema.build_publication_recovery_logical_record(
        record_kind="PUBLICATION_RECOVERY_AUTHORITY_ACCEPTED",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        publication_recovery_authorization_identity=PUBLICATION_RECOVERY_AUTHORITY,
        publication_recovery_chain_identity=PUBLICATION_RECOVERY_CHAIN,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"accepted": True},
    )
    return schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt,
    )


def _write(path: Path, stored_object: dict):
    destination = path / writer.record_storage_filename(stored_object)
    destination.write_bytes(schema.canonical_json_bytes(stored_object))
    return destination


def _two_record_scientific_chain():
    first = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={},
        attempt="0" * 32,
    )
    second = _stored_scientific(
        kind="MANIFEST_CONTACT_ATTEMPT",
        sequence=1,
        predecessor=first["logical_record_sha256"],
        payload={"pass_index": 1},
        attempt="1" * 32,
    )
    return first, second


def test_valid_linear_chain_replay_is_deterministic_and_order_independent(tmp_path):
    first, second = _two_record_scientific_chain()
    _write(tmp_path, second)
    _write(tmp_path, first)
    result_a = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    result_b = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result_a.classification == replay.VALID_LINEAR_CHAIN
    assert [item["record_kind"] for item in result_a.accepted_records] == [
        "AUTHORITY_CONSUMED",
        "MANIFEST_CONTACT_ATTEMPT",
    ]
    assert result_a.accepted_records == result_b.accepted_records


def test_redundant_physical_instances_are_flagged_without_a_fork(tmp_path):
    first = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={},
        attempt="0" * 32,
    )
    redundant = schema.build_stored_record_object(
        logical_record=first["logical_record"],
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    _write(tmp_path, first)
    _write(tmp_path, redundant)
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.VALID_LINEAR_CHAIN
    assert len(result.accepted_records) == 1
    assert len(result.redundant_instances) == 1
    assert result.redundant_instances[0].classification == replay.REDUNDANT_PHYSICAL_INSTANCES


def test_different_logical_records_at_same_sequence_and_predecessor_are_a_fork(tmp_path):
    fork_a = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"variant": "a"},
        attempt="0" * 32,
    )
    fork_b = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"variant": "b"},
        attempt="1" * 32,
    )
    _write(tmp_path, fork_a)
    _write(tmp_path, fork_b)
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.LOGICAL_FORK
    assert result.accepted_records == ()


def test_predecessor_mismatch_rejected(tmp_path):
    wrong_predecessor = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor="1" * 64,
        payload={},
        attempt="0" * 32,
    )
    _write(tmp_path, wrong_predecessor)
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.PREDECESSOR_MISMATCH


def test_sequence_gap_or_missing_link_rejected(tmp_path):
    gap = _stored_scientific(
        kind="MANIFEST_CONTACT_ATTEMPT",
        sequence=1,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"pass_index": 1},
        attempt="0" * 32,
    )
    _write(tmp_path, gap)
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.SEQUENCE_GAP


def test_sequence_number_must_be_strict_int():
    with pytest.raises(schema.EvidenceValidationError):
        schema.build_scientific_logical_record(
            record_kind="AUTHORITY_CONSUMED",
            sequence_number=True,
            execution_identity=EXECUTION_IDENTITY,
            scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
            predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
            payload={},
        )


def test_cross_chain_object_rejected(tmp_path):
    _write(tmp_path, _stored_publication("0" * 32))
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.CROSS_CHAIN_OBJECT
    assert result.rejected_objects[0].classification == replay.CROSS_CHAIN_OBJECT


def test_cross_identity_object_rejected(tmp_path):
    _write(tmp_path, _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={},
        attempt="0" * 32,
        authority="f" * 64,
    ))
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.classification == replay.CROSS_IDENTITY_OBJECT


def test_publication_and_recovery_chains_replay_with_distinct_chain_identities(tmp_path):
    publication_dir = tmp_path / "publication"
    recovery_dir = tmp_path / "recovery"
    publication_dir.mkdir()
    recovery_dir.mkdir()
    _write(publication_dir, _stored_publication("0" * 32))
    _write(recovery_dir, _stored_recovery("1" * 32))
    publication_result = replay.replay_chain(
        publication_dir,
        expected_record_schema_identity=schema.PUBLICATION_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=PUBLICATION_AUTHORITY,
        expected_chain_identity=PUBLICATION_CHAIN,
    )
    recovery_result = replay.replay_chain(
        recovery_dir,
        expected_record_schema_identity=schema.PUBLICATION_RECOVERY_LOGICAL_RECORD_SCHEMA,
        expected_execution_identity=EXECUTION_IDENTITY,
        expected_authorization_identity=PUBLICATION_RECOVERY_AUTHORITY,
        expected_chain_identity=PUBLICATION_RECOVERY_CHAIN,
    )
    assert publication_result.classification == replay.VALID_LINEAR_CHAIN
    assert recovery_result.classification == replay.VALID_LINEAR_CHAIN


def test_malformed_canonical_bytes_rejected(tmp_path):
    (tmp_path / "bad.json").write_bytes(b'{ "not":"canonical" }\n')
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
    )
    assert result.classification == replay.INVALID_CANONICAL_BYTES


def test_physical_hash_mismatch_rejected(tmp_path):
    stored = _stored_scientific(
        kind="AUTHORITY_CONSUMED",
        sequence=0,
        predecessor=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={},
        attempt="0" * 32,
    )
    mutated = copy.deepcopy(stored)
    mutated["stored_object_sha256"] = "f" * 64
    (tmp_path / "mutated.json").write_bytes(schema.canonical_json_bytes(mutated))
    result = replay.replay_chain(
        tmp_path,
        expected_record_schema_identity=schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
    )
    assert result.classification == replay.INVALID_PHYSICAL_OBJECT_IDENTITY
