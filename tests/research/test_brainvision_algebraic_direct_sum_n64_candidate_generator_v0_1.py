"""Tests for the algebraic direct-sum N=64 candidate generator v0.1 (offline; implementation verification only).

These tests are implementation verification, not Brainvision evidence. They never run PRIMARY_V0_1, never invoke
the verifier or freezer, never touch ΨTRS / descriptors / operational code / torment_service, and never persist a
candidate stream. Record-emitting coverage uses the private pure core with injected tiny deterministic synthetic
parameter iterables and explicit test-local limits, as authorized.
"""
import ast
import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import algebraic_direct_sum_n64_candidate_generator_v0_1 as gen  # noqa: E402
import witness_canonical_json_v0_1 as cjson  # noqa: E402

# frozen hand-checkable fixtures
U_POS = (0, 1, 2)
V_POS = (0, 3, 6, 9)
A_POS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
B_POS = [0, 1, 2, 55, 56, 57, 58, 59, 60, 61, 62, 63]
U_COLLIDE = (0, 1, 2)
V_COLLIDE = (0, 1, 3, 5)
# second hand-checkable direct tuple, used only for synthetic multi-record core tests
U_ALT = (0, 1, 12)


def _run(result_envelope):
    return result_envelope["generator_run_result"]


def _replay(result_envelope):
    return result_envelope["generator_replay_result"]


# ----------------------------- normalization -----------------------------
def test_translation_normal_form_correctness():
    assert gen.translation_normal_form(U_POS) == U_POS
    assert gen.translation_normal_form(V_POS) == V_POS
    assert gen.translation_normal_form((5, 6, 7)) == (0, 1, 2)          # translation-invariant
    assert gen.translation_normal_form((0, 1, 63)) == (0, 1, 2)         # wraps: anchor at 63
    assert gen.translation_normal_form((0, 1, 5)) == (0, 1, 5)          # already minimal
    assert gen.translation_normal_form((59, 60, 0)) == (0, 1, 5)        # same orbit as above


@pytest.mark.parametrize("bad", [(), [], (0, 0, 1), (0, 1, 64), (0, 1, -1), (0, True, 2), (0, 1.0, 2)])
def test_translation_normal_form_rejects_invalid_input(bad):
    with pytest.raises(gen.GeneratorInvariantError):
        gen.translation_normal_form(bad)


def test_v_sign_normalization():
    assert gen.negated_normal_form(V_POS) == V_POS                       # frozen fixture is negation-fixed
    reduced = gen.sign_reduced_v_representatives()
    assert all(candidate <= gen.negated_normal_form(candidate) for candidate in reduced)
    assert V_POS in reduced


def test_u_v_role_separation():
    configuration = gen.generator_configuration_payload()
    assert configuration["u_size"] == 3 and configuration["v_size"] == 4
    assert configuration["u_v_role_separation"] is True
    assert gen.U_SIZE != gen.V_SIZE                                      # roles are not interchangeable


# ----------------------------- parameter-domain count regressions -----------------------------
def test_parameter_domain_count_regressions():
    counts = gen.parameter_domain_counts()
    assert counts["normalized_u_count"] == gen.NORMALIZED_U_COUNT == 651
    assert counts["translation_normalized_v_count"] == gen.TRANSLATION_NORMALIZED_V_COUNT == 9936
    assert counts["negation_fixed_v_count"] == gen.NEGATION_FIXED_V_COUNT == 496
    assert counts["sign_reduced_v_count"] == gen.SIGN_REDUCED_V_COUNT == 5216
    assert 651 * 5216 == gen.NORMALIZED_PARAMETER_DOMAIN_SIZE == 3_395_616
    assert counts["normalized_parameter_domain_size"] == 3_395_616


def test_representatives_are_ascending_lexicographic_and_canonical():
    u_reps = gen.canonical_u_representatives()
    v_reps = gen.sign_reduced_v_representatives()
    assert list(u_reps) == sorted(u_reps) and list(v_reps) == sorted(v_reps)
    assert all(gen.translation_normal_form(u) == u for u in u_reps[:50])
    assert all(candidate[0] == 0 for candidate in u_reps[:50] + v_reps[:50])


def test_parameter_traversal_is_v_major():
    u_reps = ((0, 1, 2), (0, 1, 3))
    v_reps = ((0, 1, 2, 3), (0, 1, 2, 4))
    order = list(gen._parameter_tuples(v_reps, u_reps))
    assert order == [(v_reps[0], u_reps[0]), (v_reps[0], u_reps[1]),
                     (v_reps[1], u_reps[0]), (v_reps[1], u_reps[1])]
    assert gen.PARAMETER_ORDER_IDENTITY == "V_LEXICOGRAPHIC_OUTER_U_LEXICOGRAPHIC_INNER"


# ----------------------------- strict integers -----------------------------
def test_strict_int_rejects_bool():
    assert gen.is_strict_int(3) is True
    assert gen.is_strict_int(True) is False and gen.is_strict_int(False) is False
    assert gen.is_strict_int(3.0) is False


# ----------------------------- directness and construction -----------------------------
def test_positive_fixture_directness_and_construction():
    sum_direct, difference_direct, sum_count, difference_count = gen.directness(U_POS, V_POS)
    assert sum_direct is True and difference_direct is True
    assert sum_count == difference_count == 12
    raw_a, raw_b = gen.construct_oriented_pair(U_POS, V_POS)
    assert raw_a == A_POS and raw_b == B_POS
    assert len(raw_a) == len(raw_b) == gen.CANDIDATE_WEIGHT


def test_colliding_fixture_is_ordinary_rejection():
    sum_direct, difference_direct, sum_count, difference_count = gen.directness(U_COLLIDE, V_COLLIDE)
    assert sum_direct is False and difference_direct is False            # equivalent forms agree
    assert sum_count == difference_count == 8
    records, counters, status, reason = gen._generate_core([(V_COLLIDE, U_COLLIDE)], 10, 10)
    assert records == [] and counters["colliding_parameter_tuples_rejected"] == 1
    assert status == gen.STREAM_COMPLETED and reason == "DOMAIN_EXHAUSTED"


def test_orientation_is_lexicographically_smaller_first():
    raw_a, raw_b = gen.construct_oriented_pair(U_ALT, V_POS)
    assert raw_a <= raw_b
    assert len(raw_a) == len(raw_b) == 12


def test_support_normalization_failure_is_detected():
    with pytest.raises(gen.GeneratorInvariantError):
        gen._validate_constructed_support([0, 1, 2])                     # wrong weight
    with pytest.raises(gen.GeneratorInvariantError):
        gen._validate_constructed_support([0, 1, 1] + list(range(2, 11)))  # not strictly ascending


def test_directness_consistency_disagreement_is_execution_failure(monkeypatch):
    monkeypatch.setattr(gen, "directness", lambda u, v: (True, False, 12, 11))
    with pytest.raises(gen.GeneratorInvariantError) as excinfo:
        gen._generate_core([(V_POS, U_POS)], 10, 10)
    assert excinfo.value.failure_code == gen.GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT


# ----------------------------- core emission, dedup, indices -----------------------------
def test_core_emits_record_for_direct_tuple():
    records, counters, status, reason = gen._generate_core([(V_POS, U_POS)], 10, 10)
    assert len(records) == 1 and counters["direct_tuples_found"] == 1
    assert status == gen.STREAM_COMPLETED and reason == "DOMAIN_EXHAUSTED"
    record = records[0]
    assert record["raw_support_A"] == A_POS and record["raw_support_B"] == B_POS
    assert record["candidate_generation_index"] == 0
    diagnostics = record["generator_diagnostics"]
    assert set(diagnostics) == {"parameter_tuple_index", "U", "V", "sum_directness_count",
                                "difference_directness_count", "exact_duplicate_count_before_emission"}
    assert diagnostics["U"] == list(U_POS) and diagnostics["V"] == list(V_POS)


def test_exact_duplicate_deduplication_only():
    records, counters, _status, _reason = gen._generate_core([(V_POS, U_POS), (V_POS, U_POS)], 10, 10)
    assert len(records) == 1 and counters["exact_duplicate_candidates_skipped"] == 1
    assert counters["direct_tuples_found"] == 2                          # both were direct; one was a duplicate
    records, _c, _s, _r = gen._generate_core([(V_POS, U_POS), (V_POS, U_ALT)], 10, 10)
    assert len(records) == 2                                             # distinct pairs are never suppressed


def test_indices_zero_based_monotone_gap_free_and_count_consistent():
    records, counters, _s, _r = gen._generate_core([(V_POS, U_POS), (V_POS, U_ALT)], 10, 10)
    assert [record["candidate_generation_index"] for record in records] == [0, 1]
    assert counters["candidate_records_emitted"] == len(records)


def test_index_order_and_counter_validation_failures():
    with pytest.raises(gen.GeneratorInvariantError) as excinfo:
        gen._validate_records_and_counters([{"candidate_generation_index": 1}], {**gen._zero_counters(),
                                                                                 "candidate_records_emitted": 1})
    assert excinfo.value.failure_code == gen.GENERATOR_INDEX_ORDER_FAILURE
    with pytest.raises(gen.GeneratorInvariantError) as excinfo:
        gen._validate_records_and_counters([{"candidate_generation_index": 0}], gen._zero_counters())
    assert excinfo.value.failure_code == gen.GENERATOR_COUNTER_INCONSISTENCY


# ----------------------------- terminal precedence -----------------------------
def test_terminal_domain_exhausted_wins_on_final_tuple():
    _records, _counters, status, reason = gen._generate_core([(V_POS, U_POS)], 10, 1)
    assert status == gen.STREAM_COMPLETED and reason == "DOMAIN_EXHAUSTED"


def test_terminal_max_records_emitted():
    _records, _counters, status, reason = gen._generate_core([(V_POS, U_POS), (V_POS, U_ALT)], 10, 1)
    assert status == gen.BUDGET_EXHAUSTED and reason == "MAX_CANDIDATE_RECORDS_EMITTED"


def test_terminal_max_parameter_tuples_examined():
    synthetic = [(V_POS, (0, 1, 3)), (V_POS, (0, 1, 4)), (V_POS, (0, 1, 5))]
    _records, counters, status, reason = gen._generate_core(synthetic, 2, 99)
    assert status == gen.BUDGET_EXHAUSTED and reason == "MAX_PARAMETER_TUPLES_EXAMINED"
    assert counters["parameter_tuples_examined"] == 2


def test_terminal_empty_domain():
    _records, _counters, status, reason = gen._generate_core([], 10, 10)
    assert status == gen.STREAM_COMPLETED and reason == "DOMAIN_EXHAUSTED"


# ----------------------------- budgets -----------------------------
def test_both_budget_profiles_carry_full_domain_size():
    for profile in (gen.PRIMARY_PROFILE, gen.TEST_PROFILE):
        budget = gen.structural_budget_payload(profile)
        assert budget["normalized_parameter_domain_size"] == 3_395_616
        assert budget["termination_precedence"] == list(gen.TERMINATION_PRECEDENCE)
    primary = gen.structural_budget_payload(gen.PRIMARY_PROFILE)
    tiny = gen.structural_budget_payload(gen.TEST_PROFILE)
    assert primary["max_parameter_tuples_examined"] == 3_395_616
    assert primary["max_candidate_records_emitted"] == 20_000
    assert tiny["max_parameter_tuples_examined"] == 64
    assert tiny["max_candidate_records_emitted"] == 4


def test_unknown_profile_raises_configuration_error():
    with pytest.raises(gen.GeneratorConfigurationError) as excinfo:
        gen.structural_budget_payload("NOT_A_PROFILE")
    assert excinfo.value.failure_code == gen.GENERATOR_CONFIGURATION_INVALID


# ----------------------------- TEST_TINY_V0_1 execution (authorized) -----------------------------
def test_test_tiny_profile_execution():
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    assert result["provisional"] is True
    assert result["terminal_status"] == gen.BUDGET_EXHAUSTED
    assert result["termination_reason"] == "MAX_PARAMETER_TUPLES_EXAMINED"
    assert result["structural_counters"]["parameter_tuples_examined"] == 64
    stream = result["candidate_stream_envelope"]["candidate_stream"]
    assert stream["schema_name"] == "brainvision_descriptor_blind_candidate_stream"
    assert stream["verification_mode"] == "PRIMARY_CANDIDATE_N64" and stream["N"] == 64
    assert stream["candidate_count"] == len(stream["records"])
    assert result["failure_record"] is None


def test_small_budget_deterministic_prefix_stability():
    first = gen.generate_candidate_stream(gen.TEST_PROFILE)
    second = gen.generate_candidate_stream(gen.TEST_PROFILE)
    assert cjson.canonical_json_bytes(first) == cjson.canonical_json_bytes(second)


# ----------------------------- hashes and identities -----------------------------
def test_stream_hashes_are_real_payload_hashes():
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    stream_envelope = result["candidate_stream_envelope"]
    stream = stream_envelope["candidate_stream"]
    assert stream_envelope["candidate_stream_sha256"] == cjson.payload_sha256(stream)
    assert stream["generator_identity_hash"] == cjson.payload_sha256(gen.generator_identity_payload())
    assert stream["generator_configuration_hash"] == cjson.payload_sha256(gen.generator_configuration_payload())
    assert stream["budget_identity_hash"] == cjson.payload_sha256(
        gen.structural_budget_payload(gen.TEST_PROFILE))


def test_no_sentinel_or_placeholder_hashes():
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    stream = result["candidate_stream_envelope"]["candidate_stream"]
    for field in ("generator_identity_hash", "generator_configuration_hash", "budget_identity_hash"):
        value = stream[field]
        assert cjson.is_lower_hex_64(value)
        assert value != "0" * 64 and value != "f" * 64


def test_identity_payload_binds_sources():
    identity = gen.generator_identity_payload()
    assert identity["route_identity"] == "ALGEBRAIC_DIRECT_SUM_Z64"
    assert identity["generator_source_path"].startswith("research/brainvision/")
    assert identity["serializer_source_path"].startswith("research/brainvision/")
    assert cjson.is_lower_hex_64(identity["generator_source_sha256"])
    assert cjson.is_lower_hex_64(identity["serializer_source_sha256"])
    assert set(identity) == {"schema_name", "schema_version", "generator_name", "generator_version",
                             "route_identity", "generator_source_path", "generator_source_sha256",
                             "serializer_source_path", "serializer_source_sha256"}


def test_source_path_ownership_rejects_outside_repository(tmp_path):
    outside = os.path.join(str(tmp_path), "algebraic_direct_sum_n64_candidate_generator_v0_1.py")
    with open(outside, "w", encoding="utf-8") as handle:
        handle.write("x = 1\n")
    with pytest.raises(gen.GeneratorIdentityError) as excinfo:
        gen.generator_identity_payload(outside, None)
    assert excinfo.value.failure_code == gen.GENERATOR_CONFIGURATION_INVALID


def test_diagnostics_are_hashed():
    records, _c, _s, _r = gen._generate_core([(V_POS, U_POS)], 10, 10)
    baseline = cjson.payload_sha256(records)
    mutated = copy.deepcopy(records)
    mutated[0]["generator_diagnostics"]["parameter_tuple_index"] = 999
    assert cjson.payload_sha256(mutated) != baseline                     # diagnostics are inside the hash


# ----------------------------- failure artifacts -----------------------------
def test_pre_hash_identity_failure_yields_null_stream(tmp_path):
    outside = os.path.join(str(tmp_path), "algebraic_direct_sum_n64_candidate_generator_v0_1.py")
    with open(outside, "w", encoding="utf-8") as handle:
        handle.write("x = 1\n")
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE, outside, None))
    assert result["candidate_stream_envelope"] is None                   # no fabricated identity hash
    assert result["terminal_status"] == gen.ROUTE_INCOMPLETE
    assert result["termination_reason"] == result["failure_record"]["failure_code"]


def test_pre_hash_configuration_invalid_yields_null_stream():
    result = _run(gen.generate_candidate_stream("NOT_A_PROFILE"))
    assert result["candidate_stream_envelope"] is None
    assert result["terminal_status"] == gen.ROUTE_INCOMPLETE
    assert result["failure_record"]["failure_code"] == gen.GENERATOR_CONFIGURATION_INVALID


def test_hash_available_invalid_execution_yields_valid_zero_record_stream(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise gen.GeneratorInvariantError(gen.GENERATOR_COUNTER_INCONSISTENCY, "counters")
    monkeypatch.setattr(gen, "_generate_core", _raise)
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    stream = result["candidate_stream_envelope"]["candidate_stream"]     # valid zero-record stream, not null
    assert stream["records"] == [] and stream["candidate_count"] == 0
    assert stream["terminal_status"] == gen.ROUTE_INCOMPLETE
    assert result["failure_record"]["failure_code"] == gen.GENERATOR_COUNTER_INCONSISTENCY
    assert cjson.is_lower_hex_64(stream["generator_identity_hash"])


def test_dependency_unavailable_branch(monkeypatch):
    monkeypatch.setattr(gen, "_dependency_probe", lambda: gen.GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE)
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    stream = result["candidate_stream_envelope"]["candidate_stream"]
    assert stream["terminal_status"] == gen.DEPENDENCY_UNAVAILABLE
    assert stream["records"] == [] and stream["candidate_count"] == 0
    assert result["failure_record"]["failure_code"] == gen.GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE


def test_candidate_stream_serialization_failure_yields_null_stream(monkeypatch):
    def _raise(name, payload, stage):
        raise gen.GeneratorSerializationError(gen.SERIALIZATION_FAILURE, stage)
    monkeypatch.setattr(gen, "_build_envelope", _raise)
    result = _run(gen.generate_candidate_stream(gen.TEST_PROFILE))
    assert result["candidate_stream_envelope"] is None
    assert result["failure_record"]["failure_code"] == gen.SERIALIZATION_FAILURE


def test_failure_record_shape_is_minimal_and_deterministic():
    result = _run(gen.generate_candidate_stream("NOT_A_PROFILE"))
    record = result["failure_record"]
    assert set(record) == {"failure_code", "stage", "ordered_failure_codes"}
    assert record["ordered_failure_codes"] == [record["failure_code"]]


def test_internal_errors_never_escape_public_operations(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise gen.GeneratorInvariantError(gen.GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT, "directness")
    monkeypatch.setattr(gen, "_generate_core", _raise)
    assert _run(gen.generate_candidate_stream(gen.TEST_PROFILE))["failure_record"]["failure_code"] == \
        gen.GENERATOR_DIRECTNESS_CONSISTENCY_DISAGREEMENT
    assert _replay(gen.generate_candidate_stream_with_replay(gen.TEST_PROFILE)) is not None


# ----------------------------- replay: four frozen cases -----------------------------
def test_replay_case1_identical_valid_stream_is_authoritative_and_eligible():
    replay = _replay(gen.generate_candidate_stream_with_replay(gen.TEST_PROFILE))
    assert replay["authoritative_operation"] is True
    assert replay["downstream_freeze_eligible"] is True
    assert replay["byte_identical"] is True
    assert replay["run1_candidate_stream_sha256"] == replay["run2_candidate_stream_sha256"]
    assert replay["candidate_stream_envelope"] is not None
    for field in ("generator_identity_envelope", "generator_configuration_envelope",
                  "structural_budget_envelope", "source_identity_envelope"):
        assert replay[field] is not None


def test_replay_case2_identical_zero_record_route_stream_not_eligible(monkeypatch):
    monkeypatch.setattr(gen, "_dependency_probe", lambda: gen.GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE)
    replay = _replay(gen.generate_candidate_stream_with_replay(gen.TEST_PROFILE))
    assert replay["authoritative_operation"] is True
    assert replay["downstream_freeze_eligible"] is False
    assert replay["candidate_stream_envelope"] is not None
    stream = replay["candidate_stream_envelope"]["candidate_stream"]
    assert stream["records"] == [] and stream["terminal_status"] == gen.DEPENDENCY_UNAVAILABLE
    assert replay["failure_record"]["failure_code"] == gen.GENERATOR_UNEXPECTED_DEPENDENCY_UNAVAILABLE


def test_replay_case3_mismatch(monkeypatch):
    real = gen.generate_candidate_stream(gen.TEST_PROFILE)
    diverged = copy.deepcopy(real)
    diverged["generator_run_result"]["candidate_stream_envelope"]["candidate_stream"]["candidate_count"] = 7
    calls = {"n": 0}

    def _alternating(*_args, **_kwargs):
        calls["n"] += 1
        return real if calls["n"] == 1 else diverged
    monkeypatch.setattr(gen, "generate_candidate_stream", _alternating)
    replay = _replay(gen.generate_candidate_stream_with_replay(gen.TEST_PROFILE))
    assert replay["byte_identical"] is False
    assert replay["authoritative_operation"] is False
    assert replay["downstream_freeze_eligible"] is False
    assert replay["candidate_stream_envelope"] is None
    assert replay["failure_record"]["failure_code"] == gen.REPLAY_MISMATCH


def test_replay_case4_pre_hash_failure_not_authoritative(tmp_path):
    outside = os.path.join(str(tmp_path), "algebraic_direct_sum_n64_candidate_generator_v0_1.py")
    with open(outside, "w", encoding="utf-8") as handle:
        handle.write("x = 1\n")
    replay = _replay(gen.generate_candidate_stream_with_replay(gen.TEST_PROFILE, outside, None))
    assert replay["authoritative_operation"] is False
    assert replay["downstream_freeze_eligible"] is False
    assert replay["candidate_stream_envelope"] is None
    assert replay["generator_identity_envelope"] is None                 # nullability matches availability
    assert replay["source_identity_envelope"] is None
    assert replay["generator_configuration_envelope"] is not None
    assert replay["structural_budget_envelope"] is not None
    assert replay["failure_record"] is not None


# ----------------------------- independence -----------------------------
_FORBIDDEN_ROOTS = {"psi_trs", "run_n64_falsifier_v0_1", "witness_family_verifier_v0_1",
                    "witness_family_freeze_v0_1", "run_prerecorded_paired_analysis_v0_1",
                    "run_prerecorded_operational_harness_v0_1", "descriptors", "symmetry_gain",
                    "real_video", "torment_service", "subprocess", "socket", "urllib", "requests",
                    "numpy", "scipy", "z3", "ortools", "pysat"}


def _roots(filename):
    with open(os.path.join(BV_DIR, filename), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_generator_import_roots_are_bounded():
    roots = _roots("algebraic_direct_sum_n64_candidate_generator_v0_1.py")
    assert roots.isdisjoint(_FORBIDDEN_ROOTS)
    assert roots.issubset({"__future__", "ast", "os", "itertools", "typing", "witness_canonical_json_v0_1"})


def test_only_project_local_import_is_the_serializer():
    report = gen.independence_report()
    assert report["project_local_import_roots"] == ["witness_canonical_json_v0_1"]
    assert report["violations"] == []
    assert report["failure_code"] is None


def test_serializer_transitive_imports_are_stdlib_only():
    assert _roots("witness_canonical_json_v0_1.py").issubset({"__future__", "hashlib", "json", "typing"})


def test_no_dynamic_import_subprocess_or_network_calls():
    assert gen.dynamic_import_calls_in_source(gen.default_generator_source_path()) == frozenset()


def test_independence_report_flags_injected_violation(tmp_path):
    bad = os.path.join(str(tmp_path), "bad_generator.py")
    with open(bad, "w", encoding="utf-8") as handle:
        handle.write("import psi_trs\n")
    report = gen.independence_report(bad, gen.default_serializer_source_path())
    assert report["failure_code"] == gen.FORBIDDEN_IMPORT_DETECTED
    assert report["violations"]


def test_generator_module_is_not_a_verifier():
    source_roots = _roots("algebraic_direct_sum_n64_candidate_generator_v0_1.py")
    assert "witness_family_verifier_v0_1" not in source_roots
    assert "witness_family_freeze_v0_1" not in source_roots
    for banned in ("autocorrelation", "triple_array", "member_g_equivalence_key", "primitive_period"):
        assert not hasattr(gen, banned)                                  # no witness predicate surface
