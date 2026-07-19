"""Tests for the frozen K=3 family identity module (constants-only; no contact)."""
import ast
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import algebraic_n64_f3_frozen_identity_v0_1 as frozen  # noqa: E402

_HEX64 = set("0123456789abcdef")


def _is_hex64(value):
    return isinstance(value, str) and len(value) == 64 and all(c in _HEX64 for c in value)


def test_core_constants_exact():
    assert frozen.N == 64
    assert frozen.K == 3
    assert frozen.MEMBER_WEIGHT == 12
    assert frozen.accepted_candidate_indices == (478, 479, 480)
    assert frozen.accepted_order_indices == (0, 1, 2)
    assert frozen.verification_mode == "PRIMARY_CANDIDATE_N64"
    assert frozen.candidate_count == 20000
    assert frozen.terminal_stream_status == "budget_exhausted"
    assert frozen.execution_commit_identity == "6ddd02f9f6fdf74721dc9cd620cbb2a0aa0fecc8"


def test_all_six_supports_exact():
    assert frozen.raw_support_478_A == (0, 1, 2, 4, 5, 6, 7, 9, 11, 12, 13, 15)
    assert frozen.raw_support_478_B == (0, 1, 3, 4, 5, 7, 9, 10, 11, 60, 62, 63)
    assert frozen.raw_support_479_A == (0, 1, 2, 4, 5, 6, 7, 9, 12, 13, 14, 16)
    assert frozen.raw_support_479_B == (0, 1, 3, 4, 5, 8, 10, 11, 12, 60, 62, 63)
    assert frozen.raw_support_480_A == (0, 1, 2, 4, 5, 6, 7, 9, 13, 14, 15, 17)
    assert frozen.raw_support_480_B == (0, 1, 3, 4, 5, 9, 11, 12, 13, 60, 62, 63)


def test_each_support_sorted_unique_in_range_weight_12():
    for candidate in (478, 479, 480):
        for role in ("A", "B"):
            support = frozen.frozen_supports[candidate][role]
            assert len(support) == 12
            assert list(support) == sorted(support)
            assert len(set(support)) == 12
            assert all(0 <= t < 64 for t in support)


def test_pair_hashes_exact_and_ordered():
    assert frozen.pair_certificate_sha256 == (
        "51e72030237da850757979588b4c4107de69a6098ce7c9a3559243b5545edf2b",
        "3b3475fc9bd2264fd17035f62ddbbc03d584a1fa94f5f28db712941f6e683408",
        "d4bbb7d8d8958cca261728721115de21efa154c50930bf787e4153fcb28ddfd9")
    assert all(_is_hex64(h) for h in frozen.pair_certificate_sha256)


def test_family_and_freeze_result_hashes_exact():
    assert frozen.freeze_result_payload_sha256 == \
        "35e03a83fee83b7fc13514397e10115b3f6b99f847bf17d20772a0e61376796e"
    assert frozen.freeze_result_whole_file_sha256 == \
        "97af61ea4debf9d66146f3e33f035c17c60965c1d9fed0ebbf3d09ead58cbca5"
    assert frozen.family_manifest_sha256 == \
        "352a49bc8d06a35b41b8783f8a869a1645d93c76ddb91df379492b37106d8151"
    assert frozen.family_verifier_certificate_sha256 == \
        "416d32bba578856b5122402186860643071070c946829020799138da13ee764e"
    assert frozen.candidate_stream_payload_sha256 == \
        "70763a2ebbf7ea71267553debee2bf79c2ed3b7b0c016d9a903161074e7bf8c5"
    for value in (frozen.freeze_result_payload_sha256, frozen.freeze_result_whole_file_sha256,
                  frozen.family_manifest_sha256, frozen.family_verifier_certificate_sha256,
                  frozen.candidate_stream_payload_sha256, frozen.summary_whole_file_sha256,
                  frozen.candidate_decision_ledger_sha256):
        assert _is_hex64(value)


def test_frozen_members_and_pairs_layout():
    assert frozen.member_ids == ("candidate_478_A", "candidate_478_B", "candidate_479_A",
                                 "candidate_479_B", "candidate_480_A", "candidate_480_B")
    assert len(frozen.frozen_members) == 6
    assert len(frozen.frozen_pairs) == 3
    for candidate, order, support_a, support_b, cert in frozen.frozen_pairs:
        assert frozen.frozen_supports[candidate]["A"] == support_a
        assert frozen.frozen_supports[candidate]["B"] == support_b
        assert cert == frozen.pair_certificate_sha256[order]


def test_module_is_constants_only_no_forbidden_imports():
    with open(os.path.join(BV_DIR, "algebraic_n64_f3_frozen_identity_v0_1.py"), "r",
              encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    assert roots.issubset({"__future__", "typing"})
    for forbidden in ("numpy", "psi_trs", "run_n64_falsifier_v0_1", "witness_family_verifier_v0_1",
                      "witness_family_freeze_v0_1", "torment_service"):
        assert forbidden not in roots
    # constants-only: no function or class definitions
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
