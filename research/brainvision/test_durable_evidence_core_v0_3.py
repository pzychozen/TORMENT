from __future__ import annotations

from pathlib import Path

import pytest

import durable_evidence_primary_writer_v0_3 as writer
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


EXECUTION_IDENTITY = "a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00"
SCIENTIFIC_AUTHORITY = "715e24b1abb80ed04bbcff57ad4d0a8e33096f31af1093a7d1d3858b69f5f7af"
PREDECESSOR = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
WRITER_ATTEMPT = "3f2a1c9e77b4402db8e6a15c0d99e412"


class ConfirmedSyntheticAdapter(windows_adapter.WindowsDurabilityAdapter):
    def sync_directory_entry(self, directory_path: str):
        return windows_adapter.DirectoryDurabilityResult(
            windows_adapter.DIRECTORY_DURABILITY_CONFIRMED,
            "synthetic test adapter",
        )


def _scientific_example_preimage():
    return {
        "protocol_identity": schema.PROTOCOL_IDENTITY,
        "record_schema_identity": schema.SCIENTIFIC_LOGICAL_RECORD_SCHEMA,
        "record_kind": "MANIFEST_CONTACT_ATTEMPT",
        "sequence_number": 2,
        "execution_identity": EXECUTION_IDENTITY,
        "scientific_execution_authorization_identity": SCIENTIFIC_AUTHORITY,
        "predecessor_logical_record_sha256": PREDECESSOR,
        "payload": {"pass_index": 1},
    }


def _scientific_example_record():
    record = _scientific_example_preimage()
    record["logical_record_sha256"] = (
        "4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e"
    )
    return record


def _stored_example_preimage():
    return {
        "storage_schema_identity": schema.STORED_RECORD_OBJECT_SCHEMA,
        "logical_record_sha256": "4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e",
        "writer_identity": writer.PRIMARY_WRITER_IDENTITY,
        "writer_attempt_identity": WRITER_ATTEMPT,
        "logical_record": _scientific_example_record(),
    }


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
                    "case": "null_control",
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


def _bundle_payload_without_hash(result_kind: str = "SYNTHETIC_GATE_PASSED"):
    pass_bundle = _canonical_pass_bundle(result_kind)
    pass_bundle_sha256 = schema.sha256_hex(schema.canonical_json_bytes(pass_bundle))
    return {
        "bundle_schema_identity": schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
        "protocol_identity": schema.PROTOCOL_IDENTITY,
        "execution_identity": EXECUTION_IDENTITY,
        "scientific_execution_authorization_identity": SCIENTIFIC_AUTHORITY,
        "scientific_result_kind": result_kind,
        "pass_bundle_sha256": pass_bundle_sha256,
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


def _scientific_completion_payload(include_optional_forensic_hash: bool = True):
    bundle_payload = schema.build_bundle_payload(_bundle_payload_without_hash())
    stored_bundle = schema.build_stored_bundle_object(
        bundle_payload=bundle_payload,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="2" * 32,
    )
    payload = {
        "scientific_result_kind": bundle_payload["scientific_result_kind"],
        "bundle_payload_sha256": bundle_payload["bundle_payload_sha256"],
        "bundle_payload_byte_length": len(schema.canonical_json_bytes(bundle_payload)),
        "bundle_schema_identity": schema.IMMUTABLE_SCIENTIFIC_BUNDLE_SCHEMA,
    }
    if include_optional_forensic_hash:
        payload["accepted_stored_bundle_object_sha256"] = stored_bundle[
            "stored_bundle_object_sha256"
        ]
    payload.update(
        {
            "scientific_pass_count": 2,
            "two_pass_canonical_identity_status": "identical",
            "authority_consumed_status": "AUTHORITY_CONSUMED",
            "manifest_contact_attempt_count": 2,
            "manifest_read_success_count": 2,
            "implementation_identities": bundle_payload["implementation_identities"],
            "configuration_identity": bundle_payload["configuration_identity"],
            "manifest_identities": bundle_payload["manifest_identities"],
            "execution_identity": bundle_payload["execution_identity"],
            "scientific_execution_authorization_identity": bundle_payload[
                "scientific_execution_authorization_identity"
            ],
            "protocol_identity": schema.PROTOCOL_IDENTITY,
            "completion_validity": "VALID",
        }
    )
    return payload


def test_canonical_serialization_stability_terminal_lf_and_reparse():
    value = {"a": 1, "b": [True, "text"]}
    first = schema.canonical_json_bytes(value)
    second = schema.canonical_json_bytes({"a": 1, "b": [True, "text"]})
    assert first == second == b'{"a":1,"b":[true,"text"]}\n'
    assert first.endswith(b"\n")
    assert first.count(b"\n") == 1
    assert schema.load_canonical_json_bytes(first) == value


@pytest.mark.parametrize(
    "payload",
    (
        b'{"a":1}\r\n',
        b'{ "a": 1 }\n',
        b'{"a":1}\n\n',
        b'{"a":1,"a":2}\n',
    ),
)
def test_noncanonical_bytes_rejected(payload):
    with pytest.raises(schema.EvidenceValidationError):
        schema.load_canonical_json_bytes(payload)


@pytest.mark.parametrize(
    "value",
    (
        {"a": None},
        {"a": 1.25},
        {"a": "caf\xc3\xa9"},
        {"a": "line\nbreak"},
        {"a": ("tuple",)},
    ),
)
def test_unsupported_values_rejected(value):
    with pytest.raises(schema.EvidenceValidationError):
        schema.canonical_json_bytes(value)


def test_spec_section_7_scientific_logical_record_example_recomputes_exactly():
    preimage = _scientific_example_preimage()
    expected_bytes = (
        b'{"protocol_identity":"torment-brainvision-durable-evidence-v0.3",'
        b'"record_schema_identity":"scientific-logical-record-v0.3",'
        b'"record_kind":"MANIFEST_CONTACT_ATTEMPT","sequence_number":2,'
        b'"execution_identity":"a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00",'
        b'"scientific_execution_authorization_identity":"715e24b1abb80ed04bbcff57ad4d0a8e33096f31af1093a7d1d3858b69f5f7af",'
        b'"predecessor_logical_record_sha256":"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",'
        b'"payload":{"pass_index":1}}\n'
    )
    assert schema.canonical_json_bytes(preimage) == expected_bytes
    assert len(expected_bytes) == 516
    assert schema.compute_logical_record_sha256(preimage) == (
        "4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e"
    )
    schema.validate_logical_record(_scientific_example_record())


def test_spec_section_7_stored_object_example_recomputes_exactly():
    preimage = _stored_example_preimage()
    expected_bytes = (
        b'{"storage_schema_identity":"stored-record-object-v0.3",'
        b'"logical_record_sha256":"4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e",'
        b'"writer_identity":"durable_evidence_primary_writer_v0_3",'
        b'"writer_attempt_identity":"3f2a1c9e77b4402db8e6a15c0d99e412",'
        b'"logical_record":{"protocol_identity":"torment-brainvision-durable-evidence-v0.3",'
        b'"record_schema_identity":"scientific-logical-record-v0.3",'
        b'"record_kind":"MANIFEST_CONTACT_ATTEMPT","sequence_number":2,'
        b'"execution_identity":"a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00",'
        b'"scientific_execution_authorization_identity":"715e24b1abb80ed04bbcff57ad4d0a8e33096f31af1093a7d1d3858b69f5f7af",'
        b'"predecessor_logical_record_sha256":"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",'
        b'"payload":{"pass_index":1},'
        b'"logical_record_sha256":"4d5cfc3607c466bbc025f81437e9aeb0d0863bdfc0d0a9968b6e336a79ddc81e"}}\n'
    )
    assert schema.canonical_json_bytes(preimage) == expected_bytes
    assert len(expected_bytes) == 889
    assert schema.compute_stored_record_object_sha256(preimage) == (
        "d92660f650611d7f2301d43ea0e92183614c7501a99d2e8690c297dbc75d74ee"
    )
    stored = schema.build_stored_record_object(
        logical_record=_scientific_example_record(),
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=WRITER_ATTEMPT,
    )
    assert stored["stored_object_sha256"] == (
        "d92660f650611d7f2301d43ea0e92183614c7501a99d2e8690c297dbc75d74ee"
    )
    schema.validate_stored_record_object(stored)


def test_publication_chain_identity_examples_recompute_exactly():
    projection = "1" * 64
    assert schema.publication_chain_identity(
        publication_projection_identity=projection,
        publication_projection_authorization_identity="a" * 64,
    ) == "903217783c511519cbccd0234dfae5a6d5920ee51895f4b72c915b74f8b7edb7"
    assert schema.publication_chain_identity(
        publication_projection_identity=projection,
        publication_projection_authorization_identity="b" * 64,
    ) == "88ccee0708459c5122f3f33af22b817a7c9188f6d12cacb6e04a74bf44a99f79"


def test_publication_recovery_chain_identity_examples_recompute_exactly():
    original = "903217783c511519cbccd0234dfae5a6d5920ee51895f4b72c915b74f8b7edb7"
    assert schema.publication_recovery_chain_identity(
        original_publication_chain_identity=original,
        publication_recovery_authorization_identity="c" * 64,
    ) == "fc05a6671e60a3d095afd473a5ed58a5a6b616dd1bdb4beb5aeba8da7379e7ce"
    assert schema.publication_recovery_chain_identity(
        original_publication_chain_identity=original,
        publication_recovery_authorization_identity="d" * 64,
    ) == "28ddd3908c4bc90ac7d31fc54f21503696be0213f160da2ee97bdea7d6bd29bb"


def test_logical_and_physical_identity_nonce_separation():
    logical = _scientific_example_record()
    stored_a = schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="0" * 32,
    )
    stored_b = schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    assert stored_a["logical_record_sha256"] == stored_b["logical_record_sha256"]
    assert stored_a["stored_object_sha256"] != stored_b["stored_object_sha256"]


def test_bundle_payload_and_stored_bundle_identity_separation():
    bundle_payload = schema.build_bundle_payload(_bundle_payload_without_hash())
    stored_a = schema.build_stored_bundle_object(
        bundle_payload=bundle_payload,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="0" * 32,
    )
    stored_b = schema.build_stored_bundle_object(
        bundle_payload=bundle_payload,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="1" * 32,
    )
    assert stored_a["bundle_payload_sha256"] == stored_b["bundle_payload_sha256"]
    assert stored_a["stored_bundle_object_sha256"] != stored_b["stored_bundle_object_sha256"]
    schema.validate_stored_bundle_object(stored_a)
    schema.validate_stored_bundle_object(stored_b)


def test_scientific_completion_payload_accepts_full_form_with_optional_forensic_hash():
    payload = _scientific_completion_payload(include_optional_forensic_hash=True)
    schema.validate_scientific_completion_payload(payload)


def test_scientific_completion_payload_accepts_form_without_optional_forensic_hash():
    payload = _scientific_completion_payload(include_optional_forensic_hash=False)
    schema.validate_scientific_completion_payload(payload)


def test_scientific_completion_present_optional_hash_must_be_lower_hex64():
    payload = _scientific_completion_payload(include_optional_forensic_hash=True)
    payload["accepted_stored_bundle_object_sha256"] = "A" * 64
    with pytest.raises(schema.EvidenceValidationError):
        schema.validate_scientific_completion_payload(payload)


def test_scientific_completion_without_optional_reordered_form_rejected():
    payload = _scientific_completion_payload(include_optional_forensic_hash=False)
    items = list(payload.items())
    items[0], items[1] = items[1], items[0]
    reordered = dict(items)
    with pytest.raises(schema.EvidenceValidationError):
        schema.validate_scientific_completion_payload(reordered)


@pytest.mark.parametrize("include_optional_forensic_hash", (True, False))
def test_scientific_completion_unknown_field_rejected(include_optional_forensic_hash):
    payload = _scientific_completion_payload(
        include_optional_forensic_hash=include_optional_forensic_hash
    )
    payload["unknown_field"] = "unexpected"
    with pytest.raises(schema.EvidenceValidationError):
        schema.validate_scientific_completion_payload(payload)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("completion_validity", "INVALID"),
        ("scientific_pass_count", 1),
        ("authority_consumed_status", "AUTHORITY_NOT_CONSUMED"),
        ("scientific_result_kind", "SYNTHETIC_GATE_INVALID"),
        ("manifest_contact_attempt_count", True),
    ),
)
def test_scientific_completion_semantic_constraints_rejected(field, replacement):
    payload = _scientific_completion_payload(include_optional_forensic_hash=False)
    payload[field] = replacement
    with pytest.raises(schema.EvidenceValidationError):
        schema.validate_scientific_completion_payload(payload)


def test_immutable_no_overwrite_and_byte_verification(tmp_path: Path):
    stored = schema.build_stored_record_object(
        logical_record=_scientific_example_record(),
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity=WRITER_ATTEMPT,
    )
    result = writer.write_stored_record_object(
        tmp_path,
        stored,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    assert result.readback_verified is True
    assert result.authoritative_status == writer.DURABLE_ACCEPTED
    assert result.path.read_bytes() == schema.canonical_json_bytes(stored)
    with pytest.raises(writer.ImmutableWriteError):
        writer.write_stored_record_object(
            tmp_path,
            stored,
            durability_adapter=ConfirmedSyntheticAdapter(),
        )


def test_fail_closed_platform_stubs_do_not_claim_validation():
    durability = windows_adapter.FailClosedWindowsDurabilityAdapter().sync_directory_entry(
        "synthetic"
    )
    promotion = (
        windows_adapter.FailClosedSameVolumeNoReplacePromotionAdapter()
        .promote_verified_directory_no_replace("synthetic_staging", "synthetic_final")
    )
    assert durability.status == windows_adapter.DIRECTORY_DURABILITY_UNCONFIRMED
    assert promotion.status == windows_adapter.PROMOTION_UNCONFIRMED
