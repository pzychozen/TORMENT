from __future__ import annotations

import copy
import inspect
from dataclasses import dataclass
from pathlib import Path

import pytest

import durable_evidence_authority_v0_3 as authority
import durable_evidence_durability_v0_3 as durability
import durable_evidence_primary_writer_v0_3 as writer
import durable_evidence_scientific_result_v0_3 as scientific_result
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


EXECUTION_IDENTITY = "8" * 64
SCIENTIFIC_AUTHORITY = "9" * 64
CHAIN_RECORD_NAMES = (
    "AUTHORITY_CONSUMED",
    "MANIFEST_CONTACT_ATTEMPT_PASS_1",
    "MANIFEST_READ_SUCCESS_PASS_1",
    "MANIFEST_CONTACT_ATTEMPT_PASS_2",
    "MANIFEST_READ_SUCCESS_PASS_2",
    "SCIENTIFIC_COMPLETION",
)


class ConfirmedSyntheticAdapter(windows_adapter.WindowsDurabilityAdapter):
    def sync_directory_entry(self, directory_path: str, *, context=None):
        return windows_adapter.DirectoryDurabilityResult(
            status=windows_adapter.DIRECTORY_DURABILITY_CONFIRMED,
            detail="synthetic scientific-result recognition test double",
            adapter_policy_identity=schema.directory_durability_policy_identity(),
            target_role=(
                context.target_role
                if context is not None
                else schema.ARTIFACT_PARENT_DIRECTORY
            ),
        )


@dataclass(frozen=True)
class WrittenChain:
    records_by_name: dict[str, dict]
    writes_by_name: dict[str, writer.ImmutableWriteResult]

    @property
    def completion(self) -> dict:
        return self.records_by_name["SCIENTIFIC_COMPLETION"]

    def record_writes(self, *, omit: tuple[str, ...] = ()) -> tuple[tuple[dict, object], ...]:
        omitted = set(omit)
        return tuple(
            (self.records_by_name[name], self.writes_by_name[name])
            for name in CHAIN_RECORD_NAMES
            if name not in omitted
        )


def _source_identity(source_path: str):
    return {
        "source_path": source_path,
        "git_blob": "1" * 40,
        "raw_sha256": "2" * 64,
    }


def _canonical_pass_bundle(result_kind: str):
    return {
        "schema": schema.PASS_BUNDLE_SCHEMA,
        "fixed_positive": {"distinguished": True},
        "controls": {
            "malformed_and_degenerate_controls_correct": True,
            "identity_controls_correct": True,
            "nuisance_controls_correct": True,
            "method_b_full_enumeration": True,
            "sampling_used": False,
            "malformed_and_degenerate_control_cases": [
                {
                    "case": "synthetic",
                    "expected_failure_code": "CONTROLLED_INVALID",
                    "observed_failure_code": "CONTROLLED_INVALID",
                    "observed_failure_stage": "schema",
                    "correct": True,
                }
            ],
            "identity_control_cases": {
                "raw_identity_behavior": True,
                "repeat_determinism": True,
                "independently_allocated_equal_input": True,
                "affine_identity_behavior": True,
                "affine_equivalent_behavior": True,
                "affine_plus_complement_identity_behavior": True,
                "affine_plus_complement_behavior": True,
            },
            "method_b_counts": {
                "rotations": 4,
                "affine_transforms": 8,
                "affine_plus_complement_transforms": 16,
            },
            "method_b_required_counts": {
                "rotations": 4,
                "affine_transforms": 8,
                "affine_plus_complement_transforms": 16,
            },
            "method_b_unique_vectors_evaluated": 28,
        },
        "accepted_family": {
            "required_count": 8,
            "distinguished_count": 8,
            "results": [
                {
                    "family_index": 0,
                    "seed_order_position": 0,
                    "pair_duplicate_key": "synthetic-0",
                    "distinguished": True,
                }
            ],
        },
        "scientific_result_kind": result_kind,
    }


def _bundle_payload_without_hash(
    result_kind: str = "SYNTHETIC_GATE_PASSED",
    *,
    execution_identity: str = EXECUTION_IDENTITY,
    scientific_execution_authorization_identity: str = SCIENTIFIC_AUTHORITY,
):
    pass_bundle = _canonical_pass_bundle(result_kind)
    return {
        "bundle_schema_identity": schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
        "protocol_identity": schema.PROTOCOL_IDENTITY,
        "execution_identity": execution_identity,
        "scientific_execution_authorization_identity": (
            scientific_execution_authorization_identity
        ),
        "scientific_result_kind": result_kind,
        "pass_bundle_sha256": schema.sha256_hex(schema.canonical_json_bytes(pass_bundle)),
        "two_pass_canonical_identity_status": "identical",
        "configuration_identity": "3" * 64,
        "manifest_identities": {
            "manifest_external_sha256": "4" * 64,
            "manifest_payload_sha256": "5" * 64,
        },
        "implementation_identities": {
            "runner_identity": _source_identity("research/brainvision/runner.py"),
            "runner_test_identity": _source_identity("research/brainvision/test_runner.py"),
            "schema_contract_identity": _source_identity("research/brainvision/schema.py"),
        },
        "descriptor_identity": _source_identity("research/brainvision/descriptor.py"),
        "repository_execution_context": {
            "head": "6" * 40,
            "branch": "main",
            "python_version": "Python 3.11.15",
        },
        "publication_projection_source": {
            "current_state_snapshot": {
                "phase": "SCIENTIFIC_COMPLETE",
                "authority_consumed": True,
                "contact_armed": True,
                "manifest_contact_attempt_count": 2,
                "manifest_read_success_count": 2,
            },
            "canonical_pass_bundle": pass_bundle,
            "publication_recipe_identity": "7" * 64,
        },
    }


def _stored_bundle(
    *,
    result_kind: str = "SYNTHETIC_GATE_PASSED",
    attempt: str = "0",
    execution_identity: str = EXECUTION_IDENTITY,
    scientific_execution_authorization_identity: str = SCIENTIFIC_AUTHORITY,
):
    bundle_payload = schema.build_bundle_payload(
        _bundle_payload_without_hash(
            result_kind,
            execution_identity=execution_identity,
            scientific_execution_authorization_identity=(
                scientific_execution_authorization_identity
            ),
        )
    )
    return schema.build_stored_bundle_object(
        bundle_payload=bundle_payload,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt * 32,
    )


def _write_bundle(path: Path, stored_bundle: dict, *, confirmed: bool = True):
    adapter = ConfirmedSyntheticAdapter() if confirmed else None
    return writer.write_stored_bundle_object(
        path,
        stored_bundle,
        durability_adapter=adapter,
    )


def _write_record(path: Path, stored_record: dict, *, confirmed: bool = True):
    adapter = ConfirmedSyntheticAdapter() if confirmed else None
    return writer.write_stored_record_object(
        path,
        stored_record,
        durability_adapter=adapter,
    )


def _stored_scientific_record(
    *,
    record_kind: str,
    sequence_number: int,
    predecessor_logical_record_sha256: str,
    payload: dict,
    attempt: str,
    execution_identity: str = EXECUTION_IDENTITY,
    scientific_execution_authorization_identity: str = SCIENTIFIC_AUTHORITY,
) -> dict:
    logical = schema.build_scientific_logical_record(
        record_kind=record_kind,
        sequence_number=sequence_number,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )
    return schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt * 32,
    )


def _completion_stored(
    stored_bundle: dict,
    *,
    sequence_number: int,
    predecessor_logical_record_sha256: str,
    attempt: str = "6",
    include_optional_forensic_hash: bool = True,
    completion_payload_mutator=None,
    completion_record_mutator=None,
) -> dict:
    payload = scientific_result.build_scientific_completion_payload(
        stored_bundle,
        include_optional_forensic_hash=include_optional_forensic_hash,
    )
    if completion_payload_mutator is not None:
        payload = completion_payload_mutator(payload)
    logical = schema.build_scientific_logical_record(
        record_kind="SCIENTIFIC_COMPLETION",
        sequence_number=sequence_number,
        execution_identity=payload["execution_identity"],
        scientific_execution_authorization_identity=payload[
            "scientific_execution_authorization_identity"
        ],
        predecessor_logical_record_sha256=predecessor_logical_record_sha256,
        payload=payload,
    )
    if completion_record_mutator is not None:
        logical = completion_record_mutator(logical)
    return schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=attempt * 32,
    )


def _write_completion_chain(
    chain_dir: Path,
    stored_bundle: dict,
    *,
    include_optional_forensic_hash: bool = True,
    completion_payload_mutator=None,
    completion_record_mutator=None,
    confirmed: bool = True,
    omit_records: tuple[str, ...] = (),
    contact_passes: tuple[int, int] = (1, 2),
    wrong_kind_at: str | None = None,
    completion_predecessor_name: str = "MANIFEST_READ_SUCCESS_PASS_2",
) -> WrittenChain:
    records: dict[str, dict] = {}
    writes: dict[str, writer.ImmutableWriteResult] = {}
    omitted = set(omit_records)
    records["AUTHORITY_CONSUMED"] = authority.build_stored_authority_consumed_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="1" * 32,
    )
    records["MANIFEST_CONTACT_ATTEMPT_PASS_1"] = _stored_scientific_record(
        record_kind="MANIFEST_CONTACT_ATTEMPT",
        sequence_number=1,
        predecessor_logical_record_sha256=(
            records["AUTHORITY_CONSUMED"]["logical_record_sha256"]
        ),
        payload={"pass_index": contact_passes[0]},
        attempt="2",
    )
    records["MANIFEST_READ_SUCCESS_PASS_1"] = _stored_scientific_record(
        record_kind="MANIFEST_READ_SUCCESS",
        sequence_number=2,
        predecessor_logical_record_sha256=(
            records["MANIFEST_CONTACT_ATTEMPT_PASS_1"]["logical_record_sha256"]
        ),
        payload={"pass_index": contact_passes[0]},
        attempt="3",
    )
    contact_two_kind = "MANIFEST_CONTACT_ATTEMPT"
    if wrong_kind_at == "MANIFEST_CONTACT_ATTEMPT_PASS_2":
        contact_two_kind = "MANIFEST_READ_SUCCESS"
    records["MANIFEST_CONTACT_ATTEMPT_PASS_2"] = _stored_scientific_record(
        record_kind=contact_two_kind,
        sequence_number=3,
        predecessor_logical_record_sha256=(
            records["MANIFEST_READ_SUCCESS_PASS_1"]["logical_record_sha256"]
        ),
        payload={"pass_index": contact_passes[1]},
        attempt="4",
    )
    read_two_predecessor = records["MANIFEST_CONTACT_ATTEMPT_PASS_2"][
        "logical_record_sha256"
    ]
    records["MANIFEST_READ_SUCCESS_PASS_2"] = _stored_scientific_record(
        record_kind="MANIFEST_READ_SUCCESS",
        sequence_number=4,
        predecessor_logical_record_sha256=read_two_predecessor,
        payload={"pass_index": contact_passes[1]},
        attempt="5",
    )
    completion_predecessor = records[completion_predecessor_name][
        "logical_record_sha256"
    ]
    records["SCIENTIFIC_COMPLETION"] = _completion_stored(
        stored_bundle,
        sequence_number=5,
        predecessor_logical_record_sha256=completion_predecessor,
        include_optional_forensic_hash=include_optional_forensic_hash,
        completion_payload_mutator=completion_payload_mutator,
        completion_record_mutator=completion_record_mutator,
    )
    for name in CHAIN_RECORD_NAMES:
        if name not in omitted:
            writes[name] = _write_record(chain_dir, records[name], confirmed=confirmed)
    return WrittenChain(records, writes)


def _ledger(*, bundle_writes=(), record_writes=()):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        bundle_writes=bundle_writes,
        record_writes=record_writes,
    )


def _recognize(
    bundle_dir: Path,
    chain_dir: Path,
    *,
    durability_evidence=None,
    execution_identity: str = EXECUTION_IDENTITY,
    scientific_execution_authorization_identity: str = SCIENTIFIC_AUTHORITY,
):
    return scientific_result.recognize_scientific_result(
        bundle_directory_path=bundle_dir,
        scientific_chain_directory_path=chain_dir,
        execution_identity=execution_identity,
        scientific_execution_authorization_identity=(
            scientific_execution_authorization_identity
        ),
        durability_evidence=durability_evidence,
    )


def _with_recomputed_logical_hash(record: dict) -> dict:
    record = copy.deepcopy(record)
    record["logical_record_sha256"] = schema.compute_logical_record_sha256(record)
    return record


def _full_authoritative_evidence(
    stored_bundle: dict,
    bundle_write,
    chain: WrittenChain,
    *,
    omit: tuple[str, ...] = (),
):
    bundle_writes = ()
    if "scientific bundle" not in omit:
        bundle_writes = ((stored_bundle, bundle_write),)
    return _ledger(
        bundle_writes=bundle_writes,
        record_writes=chain.record_writes(
            omit=tuple(name for name in omit if name != "scientific bundle")
        ),
    )


def test_canonical_bundle_construction():
    stored_bundle = _stored_bundle()
    schema.validate_stored_bundle_object(stored_bundle)
    bundle_payload = stored_bundle["bundle_payload"]
    assert bundle_payload["bundle_schema_identity"] == (
        schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA
    )
    assert bundle_payload["scientific_result_kind"] == "SYNTHETIC_GATE_PASSED"
    assert schema.canonical_json_bytes(bundle_payload).endswith(b"\n")


def test_bundle_logical_hash_independent_from_writer_attempt_identity():
    first = _stored_bundle(attempt="0")
    second = schema.build_stored_bundle_object(
        bundle_payload=first["bundle_payload"],
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    assert first["bundle_payload_sha256"] == second["bundle_payload_sha256"]


def test_stored_bundle_hash_depends_on_writer_attempt_identity():
    first = _stored_bundle(attempt="0")
    second = schema.build_stored_bundle_object(
        bundle_payload=first["bundle_payload"],
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    assert first["stored_bundle_object_sha256"] != second["stored_bundle_object_sha256"]


def test_same_logical_bundle_with_different_physical_instances_is_redundant(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_a = _stored_bundle(attempt="0")
    stored_b = schema.build_stored_bundle_object(
        bundle_payload=stored_a["bundle_payload"],
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    write_a = _write_bundle(bundle_dir, stored_a)
    write_b = _write_bundle(bundle_dir, stored_b)
    chain = _write_completion_chain(
        chain_dir,
        stored_a,
        include_optional_forensic_hash=False,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(
            bundle_writes=((stored_a, write_a), (stored_b, write_b)),
            record_writes=chain.record_writes(),
        ),
    )
    assert result.classification == (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )
    assert len(result.redundant_bundle_instances) == 1


def test_different_logical_bundles_at_one_result_position_fail_closed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    passed = _stored_bundle(result_kind="SYNTHETIC_GATE_PASSED", attempt="0")
    failed = _stored_bundle(result_kind="SYNTHETIC_GATE_FAILED", attempt="1")
    write_passed = _write_bundle(bundle_dir, passed)
    write_failed = _write_bundle(bundle_dir, failed)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(
            bundle_writes=((passed, write_passed), (failed, write_failed))
        ),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


@pytest.mark.parametrize("result_kind", ("SYNTHETIC_GATE_INVALID", "OTHER"))
def test_invalid_result_kind_produces_no_accepted_bundle(result_kind):
    with pytest.raises(schema.EvidenceValidationError):
        schema.build_bundle_payload(_bundle_payload_without_hash(result_kind))


def test_bundle_byte_length_mismatch_is_rejected():
    stored_bundle = _stored_bundle()
    mutated = copy.deepcopy(stored_bundle)
    mutated["bundle_payload_byte_length"] = 1
    with pytest.raises(schema.EvidenceValidationError):
        schema.validate_stored_bundle_object(mutated)


def test_bundle_schema_mismatch_is_rejected():
    payload = _bundle_payload_without_hash()
    payload["bundle_schema_identity"] = "wrong-schema"
    with pytest.raises(schema.EvidenceValidationError):
        schema.build_bundle_payload(payload)


def test_bundle_size_ceiling_is_enforced():
    with pytest.raises(schema.EvidenceValidationError):
        schema.canonical_json_bytes(
            {"oversized": "x" * schema.MAX_STORED_BUNDLE_OBJECT_BYTES},
            max_bytes=schema.MAX_STORED_BUNDLE_OBJECT_BYTES,
        )


def test_cross_authorization_bundle_is_rejected(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    foreign = _stored_bundle(
        scientific_execution_authorization_identity="a" * 64,
    )
    write_result = _write_bundle(bundle_dir, foreign)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(bundle_writes=((foreign, write_result),)),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_cross_execution_bundle_is_rejected(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    foreign = _stored_bundle(execution_identity="b" * 64)
    write_result = _write_bundle(bundle_dir, foreign)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(bundle_writes=((foreign, write_result),)),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_malformed_bundle_canonical_bytes_are_rejected(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    bundle_dir.mkdir()
    (bundle_dir / "bad.json").write_bytes(b'{ "bad":"not canonical" }\n')
    result = _recognize(bundle_dir, chain_dir)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


@pytest.mark.parametrize("include_optional", (True, False))
def test_valid_durable_pair_is_authoritative(tmp_path, include_optional):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        include_optional_forensic_hash=include_optional,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )
    assert result.scientific_result_kind == "SYNTHETIC_GATE_PASSED"


def test_orphan_bundle_is_non_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(bundle_writes=((stored_bundle, bundle_write),)),
    )
    assert result.classification == scientific_result.ORPHAN_IMMUTABLE_SCIENTIFIC_BUNDLE


def test_completion_without_matching_bundle_is_invalid(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    chain = _write_completion_chain(chain_dir, stored_bundle)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(record_writes=chain.record_writes()),
    )
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


@pytest.mark.parametrize(
    "field_replacement",
    (
        ("bundle_payload_sha256", "f" * 64),
        ("accepted_stored_bundle_object_sha256", "f" * 64),
        ("bundle_payload_byte_length", 1),
        ("scientific_result_kind", "SYNTHETIC_GATE_FAILED"),
        ("scientific_pass_count", 1),
        ("two_pass_canonical_identity_status", "different"),
        ("authority_consumed_status", "AUTHORITY_NOT_CONSUMED"),
        ("manifest_contact_attempt_count", 1),
        ("manifest_read_success_count", 1),
        (
            "manifest_identities",
            {
                "manifest_external_sha256": "a" * 64,
                "manifest_payload_sha256": "b" * 64,
            },
        ),
        ("completion_validity", "INVALID"),
    ),
)
def test_completion_payload_mismatch_is_invalid(tmp_path, field_replacement):
    field, replacement = field_replacement
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)

    def mutate(payload):
        payload = copy.deepcopy(payload)
        payload[field] = replacement
        return payload

    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        completion_payload_mutator=mutate,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


@pytest.mark.parametrize(
    "mutator",
    (
        lambda record: _with_recomputed_logical_hash(
            {**record, "execution_identity": "a" * 64}
        ),
        lambda record: _with_recomputed_logical_hash(
            {
                **record,
                "scientific_execution_authorization_identity": "b" * 64,
            }
        ),
    ),
)
def test_completion_wrong_execution_or_authorization_identity_fails_closed(
    tmp_path, mutator
):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        completion_record_mutator=mutator,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_cross_chain_completion_fails_closed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    publication_record = schema.build_publication_logical_record(
        record_kind="PUBLICATION_COMPLETED",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        publication_projection_authorization_identity="a" * 64,
        publication_chain_identity="b" * 64,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={"published": True},
    )
    stored_publication = schema.build_stored_record_object(
        logical_record=publication_record,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="9" * 32,
    )
    _write_record(chain_dir, stored_publication)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(bundle_writes=((stored_bundle, bundle_write),)),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_terminal_status_absence_does_not_prevent_recognition(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_default_fail_closed_adapter_remains_non_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle, confirmed=False)
    chain = _write_completion_chain(chain_dir, stored_bundle, confirmed=False)
    result = _recognize(bundle_dir, chain_dir)
    assert result.classification == scientific_result.BYTE_VALID_DURABILITY_UNCONFIRMED
    with pytest.raises(durability.DurabilityEvidenceError):
        _full_authoritative_evidence(stored_bundle, bundle_write, chain)


def test_input_permutation_does_not_alter_recognition(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    chain = _write_completion_chain(chain_dir, stored_bundle)
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    ledger = _full_authoritative_evidence(stored_bundle, bundle_write, chain)
    first = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    second = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert first.classification == second.classification
    assert first.bundle_payload_sha256 == second.bundle_payload_sha256


def test_malformed_or_foreign_evidence_cannot_be_hidden_by_valid_pair(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    (bundle_dir / "malformed.json").write_bytes(b'{ "bad":"not canonical" }\n')
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_recognition_requires_authority_consumed_record(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        omit_records=("AUTHORITY_CONSUMED",),
    )
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=chain.record_writes(omit=("AUTHORITY_CONSUMED",)),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification != (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_recognition_requires_durable_authority_consumed_record(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    ledger = _full_authoritative_evidence(
        stored_bundle,
        bundle_write,
        chain,
        omit=("AUTHORITY_CONSUMED",),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.BYTE_VALID_DURABILITY_UNCONFIRMED


def test_completion_self_declared_authority_status_is_not_proof(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    completion = _completion_stored(
        stored_bundle,
        sequence_number=0,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
    )
    completion_write = _write_record(chain_dir, completion)
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=((completion, completion_write),),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification != (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_conflicting_consumed_and_failure_authority_evidence_fails_closed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    failure = authority.build_stored_authority_consumption_failure_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="a" * 32,
    )
    failure_write = _write_record(chain_dir, failure)
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=chain.record_writes() + ((failure, failure_write),),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_completion_at_sequence_zero_is_not_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    completion = _completion_stored(
        stored_bundle,
        sequence_number=0,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
    )
    completion_write = _write_record(chain_dir, completion)
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=((completion, completion_write),),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


def test_completion_requires_manifest_read_success_pass_two_predecessor(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        completion_predecessor_name="MANIFEST_CONTACT_ATTEMPT_PASS_2",
    )
    ledger = _full_authoritative_evidence(stored_bundle, bundle_write, chain)
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_missing_manifest_contact_attempt_is_not_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        omit_records=("MANIFEST_CONTACT_ATTEMPT_PASS_1",),
    )
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=chain.record_writes(omit=("MANIFEST_CONTACT_ATTEMPT_PASS_1",)),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_missing_manifest_read_success_is_not_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        omit_records=("MANIFEST_READ_SUCCESS_PASS_2",),
    )
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=chain.record_writes(omit=("MANIFEST_READ_SUCCESS_PASS_2",)),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_wrong_manifest_pass_order_is_not_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        contact_passes=(2, 1),
    )
    ledger = _full_authoritative_evidence(stored_bundle, bundle_write, chain)
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


def test_wrong_record_kind_at_required_position_is_not_authoritative(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        wrong_kind_at="MANIFEST_CONTACT_ATTEMPT_PASS_2",
    )
    ledger = _full_authoritative_evidence(stored_bundle, bundle_write, chain)
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


def test_valid_prefix_cannot_hide_later_contradictory_evidence(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    unexpected = _stored_scientific_record(
        record_kind="MANIFEST_CONTACT_ATTEMPT",
        sequence_number=6,
        predecessor_logical_record_sha256=chain.completion["logical_record_sha256"],
        payload={"pass_index": 3},
        attempt="7",
    )
    unexpected_write = _write_record(chain_dir, unexpected)
    ledger = _ledger(
        bundle_writes=((stored_bundle, bundle_write),),
        record_writes=chain.record_writes() + ((unexpected, unexpected_write),),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.CONTRADICTORY_EVIDENCE


def test_raw_hash_iterable_is_not_accepted_as_durability_evidence(tmp_path):
    with pytest.raises(scientific_result.ScientificResultEvidenceError):
        _recognize(tmp_path / "bundles", tmp_path / "chain", durability_evidence={"f" * 64})
    with pytest.raises(TypeError):
        durability.VerifiedDurabilityEvidence({"f" * 64})


def test_unbacked_durability_assertion_cannot_produce_authoritative_result(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    _write_bundle(bundle_dir, stored_bundle)
    _write_completion_chain(chain_dir, stored_bundle)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=durability.VerifiedDurabilityEvidence.empty(),
    )
    assert result.classification == scientific_result.BYTE_VALID_DURABILITY_UNCONFIRMED


def test_synthetic_confirmed_durability_isolated_to_test_path():
    assert "Synthetic" in ConfirmedSyntheticAdapter.__name__
    assert issubclass(ConfirmedSyntheticAdapter, windows_adapter.WindowsDurabilityAdapter)
    production_modules = (authority, scientific_result)
    for module in production_modules:
        assert "ConfirmedSyntheticAdapter" not in vars(module)


def test_production_api_signatures_expose_no_raw_hash_durability_parameters():
    authority_params = inspect.signature(
        authority.replay_scientific_authority_state
    ).parameters
    recognition_params = inspect.signature(
        scientific_result.recognize_scientific_result
    ).parameters
    for params in (authority_params, recognition_params):
        assert "durability_evidence" in params
        assert not any("durably_accepted" in name for name in params)
        assert not any(name.endswith("sha256s") for name in params)


@pytest.mark.parametrize(
    "omitted",
    CHAIN_RECORD_NAMES + ("scientific bundle",),
)
def test_all_required_objects_must_have_accepted_durability(tmp_path, omitted):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    ledger = _full_authoritative_evidence(
        stored_bundle,
        bundle_write,
        chain,
        omit=(omitted,),
    )
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification != (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_optional_physical_hash_omitted_with_valid_linkage_may_succeed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        include_optional_forensic_hash=False,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_optional_physical_hash_present_with_durable_redundant_instance_may_succeed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_a = _stored_bundle(attempt="0")
    stored_b = schema.build_stored_bundle_object(
        bundle_payload=stored_a["bundle_payload"],
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    write_a = _write_bundle(bundle_dir, stored_a)
    write_b = _write_bundle(bundle_dir, stored_b)
    chain = _write_completion_chain(chain_dir, stored_a)
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_ledger(
            bundle_writes=((stored_a, write_a), (stored_b, write_b)),
            record_writes=chain.record_writes(),
        ),
    )
    assert result.classification == (
        scientific_result.AUTHORITATIVE_DURABLE_SCIENTIFIC_RESULT
    )


def test_optional_physical_hash_present_but_unconfirmed_fails_closed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    _write_bundle(bundle_dir, stored_bundle, confirmed=False)
    chain = _write_completion_chain(chain_dir, stored_bundle)
    ledger = _ledger(record_writes=chain.record_writes())
    result = _recognize(bundle_dir, chain_dir, durability_evidence=ledger)
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION


def test_optional_physical_hash_unrelated_instance_fails_closed(tmp_path):
    bundle_dir = tmp_path / "bundles"
    chain_dir = tmp_path / "chain"
    stored_bundle = _stored_bundle()
    bundle_write = _write_bundle(bundle_dir, stored_bundle)
    unrelated_hash = "f" * 64

    def mutate(payload):
        payload = copy.deepcopy(payload)
        payload["accepted_stored_bundle_object_sha256"] = unrelated_hash
        return payload

    chain = _write_completion_chain(
        chain_dir,
        stored_bundle,
        completion_payload_mutator=mutate,
    )
    result = _recognize(
        bundle_dir,
        chain_dir,
        durability_evidence=_full_authoritative_evidence(
            stored_bundle, bundle_write, chain
        ),
    )
    assert result.classification == scientific_result.INVALID_SCIENTIFIC_COMPLETION
