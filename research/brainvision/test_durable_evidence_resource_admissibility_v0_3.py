from __future__ import annotations

import pytest

import durable_evidence_schema_v0_3 as schema


def nested_list(depth: int):
    value = []
    for _ in range(depth):
        value = [value]
    return value


def test_resource_policy_declaration_identity_and_sha_are_exact():
    declaration = schema.resource_admissibility_policy_declaration()
    assert tuple(declaration.keys()) == schema.RESOURCE_ADMISSIBILITY_POLICY_DECLARATION_KEYS
    assert declaration["policy_schema_identity"] == (
        schema.RESOURCE_ADMISSIBILITY_POLICY_SCHEMA
    )
    assert declaration["max_resource_nesting_depth"] == 32
    assert declaration["max_resource_container_members_per_container"] == 4096
    assert declaration["max_stored_record_object_bytes"] == 65536
    assert declaration["max_stored_bundle_object_bytes"] == 4194304
    assert declaration["max_resource_total_node_count"] == 16384
    assert declaration["max_resource_integer_abs"] == 9223372036854775807
    assert declaration["max_publication_artifact_set_bytes"] == 8406016
    assert declaration["max_publication_staging_write_bytes"] == 8406016
    assert declaration["max_publication_recovery_verification_bytes"] == 8406016
    assert schema.resource_admissibility_policy_sha256() == schema.sha256_hex(
        schema.canonical_json_bytes(declaration)
    )
    identity = schema.resource_admissibility_policy_identity()
    assert tuple(identity.keys()) == schema.RESOURCE_ADMISSIBILITY_POLICY_IDENTITY_KEYS
    assert identity["policy_schema_identity"] == schema.RESOURCE_ADMISSIBILITY_POLICY_SCHEMA
    assert len(identity["policy_sha256"]) == 64
    assert identity["policy_sha256"] == identity["policy_sha256"].lower()
    schema.validate_resource_admissibility_policy_identity(identity)


def test_policy_identity_rejects_shape_and_digest_mismatches():
    good = schema.resource_admissibility_policy_identity()
    bad_order = {
        "policy_sha256": good["policy_sha256"],
        "policy_schema_identity": good["policy_schema_identity"],
    }
    for value in (
        None,
        {},
        {"resource_admissibility_policy_identity": good},
        bad_order,
        {
            "policy_schema_identity": "wrong",
            "policy_sha256": good["policy_sha256"],
        },
        {
            "policy_schema_identity": good["policy_schema_identity"],
            "policy_sha256": "A" * 64,
        },
        {
            "policy_schema_identity": good["policy_schema_identity"],
            "policy_sha256": "0" * 64,
        },
    ):
        with pytest.raises(schema.ResourcePolicyIdentityMismatchError):
            schema.validate_resource_admissibility_policy_identity(value)


def test_canonical_json_bytes_remains_unchanged_for_old_fixture():
    value = {"b": [True, 7, "x"], "a": {"z": "y"}}
    assert schema.canonical_json_bytes(value) == b'{"b":[true,7,"x"],"a":{"z":"y"}}\n'
    assert schema.canonical_json_bytes_bounded(value, 35) == (
        schema.canonical_json_bytes(value)
    )
    with pytest.raises(schema.ResourceStructureLimitError) as excinfo:
        schema.canonical_json_bytes_bounded(
            value,
            len(schema.canonical_json_bytes(value)) - 1,
        )
    assert excinfo.value.failure_code == schema.CANONICAL_STRUCTURE_LIMIT_EXCEEDED


def test_structural_accounting_root_mapping_values_and_list_elements():
    schema.validate_resource_domain({"a": [1, 2], "b": {"c": True}})
    with pytest.raises(schema.ResourceStructureLimitError):
        schema.validate_resource_domain([0] * schema.MAX_RESOURCE_TOTAL_NODE_COUNT)


def test_mapping_keys_count_as_string_bytes_but_not_nodes(monkeypatch):
    monkeypatch.setattr(schema, "MAX_RESOURCE_TOTAL_NODE_COUNT", 2)
    schema.validate_resource_domain({"abc": True})
    monkeypatch.setattr(schema, "MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES", 2)
    with pytest.raises(schema.ResourceStringLimitError):
        schema.validate_resource_domain({"abc": True})


def test_string_single_and_total_limits(monkeypatch):
    schema.validate_resource_domain("x" * schema.MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES)
    with pytest.raises(schema.ResourceStringLimitError):
        schema.validate_resource_domain(
            "x" * (schema.MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES + 1)
        )
    monkeypatch.setattr(schema, "MAX_RESOURCE_TOTAL_STRING_ASCII_BYTES", 5)
    schema.validate_resource_domain({"ab": "cde"})
    with pytest.raises(schema.ResourceStringLimitError):
        schema.validate_resource_domain({"ab": "cdef"})


def test_container_member_count_limit_is_checked_before_children():
    schema.validate_resource_domain([0] * schema.MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER)
    over_limit = [object()] * (schema.MAX_RESOURCE_CONTAINER_MEMBERS_PER_CONTAINER + 1)
    with pytest.raises(schema.ResourceStructureLimitError):
        schema.validate_resource_domain(over_limit)


def test_depth_limit_accepts_32_and_rejects_33():
    schema.validate_resource_domain(nested_list(schema.MAX_RESOURCE_NESTING_DEPTH))
    with pytest.raises(schema.ResourceStructureLimitError):
        schema.validate_resource_domain(nested_list(schema.MAX_RESOURCE_NESTING_DEPTH + 1))


def test_bool_is_handled_before_int_and_integer_magnitude_is_bounded():
    schema.validate_resource_domain(True)
    schema.validate_resource_domain(schema.MAX_RESOURCE_INTEGER_ABS)
    schema.validate_resource_domain(-schema.MAX_RESOURCE_INTEGER_ABS)
    with pytest.raises(schema.ResourceIntegerLimitError):
        schema.validate_resource_domain(schema.MAX_RESOURCE_INTEGER_ABS + 1)
    with pytest.raises(schema.ResourceIntegerLimitError):
        schema.validate_resource_domain(-(schema.MAX_RESOURCE_INTEGER_ABS + 1))


def test_deterministic_first_failure_follows_mapping_and_list_order(monkeypatch):
    monkeypatch.setattr(schema, "MAX_RESOURCE_SINGLE_STRING_ASCII_BYTES", 3)
    with pytest.raises(schema.ResourceIntegerLimitError):
        schema.validate_resource_domain(
            {"a": schema.MAX_RESOURCE_INTEGER_ABS + 1, "b": "xxxx"}
        )
    with pytest.raises(schema.ResourceStringLimitError):
        schema.validate_resource_domain(["xxxx", schema.MAX_RESOURCE_INTEGER_ABS + 1])


def test_semantic_domain_error_is_not_resource_relabelled():
    with pytest.raises(schema.EvidenceValidationError) as excinfo:
        schema.validate_resource_domain({"bad": None})
    assert not isinstance(excinfo.value, schema.ResourceAdmissibilityError)


def test_memory_and_overflow_convert_only_at_bounded_canonical_boundary(monkeypatch):
    monkeypatch.setattr(
        schema,
        "validate_resource_domain",
        lambda value: (_ for _ in ()).throw(MemoryError()),
    )
    with pytest.raises(schema.ResourceAdmissibilityIndeterminateError):
        schema.canonical_json_bytes_bounded({"a": True}, 100)
    monkeypatch.setattr(
        schema,
        "validate_resource_domain",
        lambda value: (_ for _ in ()).throw(OverflowError()),
    )
    with pytest.raises(schema.ResourceAdmissibilityIndeterminateError):
        schema.canonical_json_bytes_bounded({"a": True}, 100)


def test_unrelated_programming_exceptions_propagate(monkeypatch):
    monkeypatch.setattr(
        schema,
        "validate_resource_domain",
        lambda value: (_ for _ in ()).throw(RuntimeError("programming bug")),
    )
    with pytest.raises(RuntimeError):
        schema.canonical_json_bytes_bounded({"a": True}, 100)


def test_artifact_resource_map_exact_inventory_and_budget():
    artifacts = {
        schema.PUBLICATION_RESULT_ARTIFACT_FILENAME: b"a",
        schema.PUBLICATION_EXECUTION_ENVELOPE_FILENAME: b"b",
        schema.PUBLICATION_SUMMARY_FILENAME: b"c",
    }
    assert schema.validate_publication_artifact_resource_map(artifacts) == 3
    with pytest.raises(schema.PublicationArtifactSetSizeLimitError):
        schema.validate_publication_artifact_resource_map({})
    too_large_summary = dict(artifacts)
    too_large_summary[schema.PUBLICATION_SUMMARY_FILENAME] = (
        b"x" * (schema.MAX_PUBLICATION_SUMMARY_BYTES + 1)
    )
    with pytest.raises(schema.PublicationArtifactSizeLimitError) as excinfo:
        schema.validate_publication_artifact_resource_map(too_large_summary)
    assert excinfo.value.failure_code == schema.SUMMARY_SIZE_LIMIT_EXCEEDED
