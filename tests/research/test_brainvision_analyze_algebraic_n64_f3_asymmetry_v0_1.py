"""Tests for the standalone read-only F3 frozen-family asymmetry audit analyzer.

Non-contact: no PsiTRS, no descriptor recomputation, no F3 evaluator, no real
audit execution over the retained canonical JSON, and no real audit-gate use.
Synthetic fixtures and temporary directories / Git repositories only, plus exactly
one read-only preflight-only test of the real retained JSON that stops before any
audit calculation. An autouse guard blocks writes to the real audit paths and the
retained F3 directory and keeps the audit gate unset.
"""
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import analyze_algebraic_n64_f3_asymmetry_v0_1 as az  # noqa: E402

REPO_ROOT = Path(BV_DIR).parents[1]
REAL_FINAL = (REPO_ROOT / az.FINAL_DIR_RELATIVE_PATH).resolve()
REAL_STAGING = (REPO_ROOT / az.STAGING_DIR_RELATIVE_PATH).resolve()
RETAINED_F3_DIR = (REPO_ROOT / "research" / "brainvision" / "results"
                   / "algebraic_n64_primary_v0_1_f3_evaluation_v0_1").resolve()
REAL_RETAINED_JSON = (REPO_ROOT / az.INPUT_RELATIVE_PATH).resolve()

ANALYZER_SOURCE_BYTES = Path(az.__file__).read_bytes()

ALLOWED_STDLIB = {
    "__future__", "hashlib", "json", "math", "os", "pathlib", "stat",
    "subprocess", "sys", "typing", "statistics",
}
FORBIDDEN_IMPORTS = {
    "numpy", "pandas", "scipy", "psi_trs",
    "algebraic_n64_f3_evaluator_v0_1", "algebraic_n64_f3_frozen_identity_v0_1",
    "witness_canonical_json_v0_1", "torment_service",
    "research",
}
FORBIDDEN_CALLS = {
    "psi_trs_features", "build_production_feature_cache", "evaluate_from_feature_cache",
}


# --------------------------------------------------------------------------- #
# Autouse real-path protection guard
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _real_path_protection(monkeypatch):
    # No test may run with either real gate set.
    monkeypatch.delenv(az.GATE_ENV, raising=False)
    monkeypatch.delenv("ALGEBRAIC_N64_F3_EVALUATION_AUTHORIZED", raising=False)

    original_write = az.write_derived_artifacts_exclusively

    def guarded_write(final_dir, staging_dir, *args, **kwargs):
        for candidate in (Path(final_dir).resolve(), Path(staging_dir).resolve()):
            assert candidate != REAL_FINAL, "blocked write to real audit final directory"
            assert candidate != REAL_STAGING, "blocked write to real audit staging directory"
            assert candidate != RETAINED_F3_DIR and RETAINED_F3_DIR not in candidate.parents, \
                "blocked write inside retained F3 directory"
        return original_write(final_dir, staging_dir, *args, **kwargs)

    monkeypatch.setattr(az, "write_derived_artifacts_exclusively", guarded_write)
    yield
    assert not REAL_FINAL.exists(), "real audit final directory must remain absent"
    assert not REAL_STAGING.exists(), "real audit staging directory must remain absent"


# --------------------------------------------------------------------------- #
# Synthetic fixture construction
# --------------------------------------------------------------------------- #

CAND = [478, 479, 480]


def _per_start(distances):
    return [{"distance": float(d), "finite": True} for d in distances]


def _const_shift_block(mean_fn, perstart_fn=None):
    """63 nonidentity shifts.

    Retained aggregate ``mean`` = mean_fn(q); per-start distances = perstart_fn(q)
    (a scalar or a 64-list), defaulting to mean_fn(q). Decoupling mean_fn from
    perstart_fn lets tests prove class-level calculations use the retained
    aggregate mean rather than a per-start recomputation.
    """
    if perstart_fn is None:
        perstart_fn = mean_fn
    shifts = []
    for r in range(1, 64):
        q = min(r, 64 - r)
        mval = float(mean_fn(q))
        pv = perstart_fn(q)
        per = [float(x) for x in pv] if isinstance(pv, (list, tuple)) else [float(pv)] * 64
        shifts.append({
            "relative_shift": r,
            "per_start": _per_start(per),
            "count": 64, "mean": mval, "median": mval, "minimum": mval,
            "maximum": mval, "population_standard_deviation": 0.0,
            "argmax_starts": list(range(64)), "argmin_starts": list(range(64)),
        })
    return {
        "nonidentity_shifts": shifts,
        "identity_controls": {"all_distance_zero": True, "count": 64, "nonzero_starts": []},
        "coverage": {"responses": 4032, "shift_count": 63},
        "maximum_nonidentity_mean": max(mean_fn(q) for q in range(1, 33)),
        "argmax_nonidentity_shifts": [32],
    }


def _member(idx, role, full_fn, k0_fn, full_ps=None, k0_ps=None):
    return {
        "member_id": "candidate_%d_%s" % (CAND[idx], role),
        "pair_order_index": idx,
        "raw_role": role,
        "candidate_generation_index": CAND[idx],
        "weight": 12,
        "raw_support": [], "raw_support_sha256": "0" * 64,
        "pair_verifier_certificate_sha256": "0" * 64,
        "features_by_variant": {"psi_trs": [], "psi_trs_k0": []},
        "self_orbits_by_variant": {
            "psi_trs": _const_shift_block(full_fn, full_ps),
            "psi_trs_k0": _const_shift_block(k0_fn, k0_ps),
        },
    }


def _cross(mean_full, mean_k0):
    def block(mean):
        return {
            "per_start": _per_start([mean] * 64), "count": 64, "mean": mean,
            "median": mean, "minimum": mean, "maximum": mean,
            "population_standard_deviation": 0.0, "argmax_starts": [], "argmin_starts": [],
        }
    return {"psi_trs": block(mean_full), "psi_trs_k0": block(mean_k0)}


def _blocking_fn(n_above, cross_full):
    """Return a class-mean function producing exactly n_above classes above cross_full."""
    def fn(q):
        return (cross_full + 1.0) if q <= n_above else (cross_full - 1.0)
    return fn


def _reconsolidate(payload):
    """Recompute retained gate/margin/maximum_nonidentity_mean fields so a
    synthetic payload is internally consistent with the analyzer's validators:
    self-orbit maxima over all 63 raw shifts, Boolean gates derived from numeric
    gates, and the recursive minimum from retained cross per-start distances."""
    ep = payload["evaluation_pass"]
    mmap = {m["member_id"]: m for m in ep["members"]}
    for m in ep["members"]:
        for v in ("psi_trs", "psi_trs_k0"):
            shifts = m["self_orbits_by_variant"][v]["nonidentity_shifts"]
            m["self_orbits_by_variant"][v]["maximum_nonidentity_mean"] = max(
                float(s["mean"]) for s in shifts)
    for pair in ep["pairs"]:
        cbv = pair["cross_by_variant"]
        full_cross = float(cbv["psi_trs"]["mean"])
        k0_cross = float(cbv["psi_trs_k0"]["mean"])
        member_a = mmap[pair["member_A_id"]]
        member_b = mmap[pair["member_B_id"]]
        fa = float(member_a["self_orbits_by_variant"]["psi_trs"]["maximum_nonidentity_mean"])
        fb = float(member_b["self_orbits_by_variant"]["psi_trs"]["maximum_nonidentity_mean"])
        ka = float(member_a["self_orbits_by_variant"]["psi_trs_k0"]["maximum_nonidentity_mean"])
        kb = float(member_b["self_orbits_by_variant"]["psi_trs_k0"]["maximum_nonidentity_mean"])
        full_d = [float(o["distance"]) for o in cbv["psi_trs"]["per_start"]]
        k0_d = [float(o["distance"]) for o in cbv["psi_trs_k0"]["per_start"]]
        diffs = [full_d[s] - k0_d[s] for s in range(64)]
        pair["gates"] = {
            "full_cross_mean": full_cross, "k0_cross_mean": k0_cross,
            "full_self_A_max": fa, "full_self_B_max": fb,
            "k0_self_A_max": ka, "k0_self_B_max": kb,
            "full_dual_orbit_extreme": bool(full_cross > fa and full_cross > fb),
            "k0_not_extreme_against_either_member": bool(k0_cross <= ka and k0_cross <= kb),
            "recursive_positive_all_starts": bool(all(d > 0.0 for d in diffs)),
        }
        pair["margins"] = {
            "full_margin_vs_A": full_cross - fa, "full_margin_vs_B": full_cross - fb,
            "k0_margin_vs_A": k0_cross - ka, "k0_margin_vs_B": k0_cross - kb,
            "minimum_recursive_difference": min(diffs),
        }
    return payload


def _assemble(specs, cross_full=1.0, cross_k0=0.5):
    """Assemble a valid payload from per-pair member specs.

    specs[idx] maps each of A_full/B_full/A_k0/B_k0 to (mean_fn, per_start_fn).
    Retained gates and margins are populated to be exactly consistent with the
    retained cross means and maximum_nonidentity_mean values.
    """
    members = []
    pairs = []
    for idx in range(3):
        s = specs[idx]
        member_a = _member(idx, "A", s["A_full"][0], s["A_k0"][0], s["A_full"][1], s["A_k0"][1])
        member_b = _member(idx, "B", s["B_full"][0], s["B_k0"][0], s["B_full"][1], s["B_k0"][1])
        members.extend([member_a, member_b])
        full_a = max(s["A_full"][0](q) for q in range(1, 33))
        full_b = max(s["B_full"][0](q) for q in range(1, 33))
        k0_a = max(s["A_k0"][0](q) for q in range(1, 33))
        k0_b = max(s["B_k0"][0](q) for q in range(1, 33))
        gates = {
            "full_cross_mean": cross_full, "k0_cross_mean": cross_k0,
            "full_self_A_max": full_a, "full_self_B_max": full_b,
            "k0_self_A_max": k0_a, "k0_self_B_max": k0_b,
            "full_dual_orbit_extreme": False,
            "k0_not_extreme_against_either_member": True,
            "recursive_positive_all_starts": True,
        }
        margins = {
            "full_margin_vs_A": cross_full - full_a, "full_margin_vs_B": cross_full - full_b,
            "k0_margin_vs_A": cross_k0 - k0_a, "k0_margin_vs_B": cross_k0 - k0_b,
            "minimum_recursive_difference": 0.0,
        }
        pairs.append({
            "candidate_generation_index": CAND[idx], "pair_order_index": idx,
            "member_A_id": "candidate_%d_A" % CAND[idx],
            "member_B_id": "candidate_%d_B" % CAND[idx],
            "cross_by_variant": _cross(cross_full, cross_k0),
            "gates": gates, "margins": margins,
            "pair_verdict_flags": ["PAIR_FULL_NOT_DUAL_ORBIT_EXTREME"], "primary_pass": False,
        })
    payload = {
        "schema_name": az.REQUIRED_SCHEMA_NAME, "schema_version": az.REQUIRED_SCHEMA_VERSION,
        "execution_commit_identity": az.INPUT_EXECUTION_COMMIT_IDENTITY,
        "family_verdict": az.REQUIRED_FAMILY_VERDICT,
        "failure_record": None,
        "replay_record": {"byte_identical": True, "run1_sha256": "x", "run2_sha256": "x"},
        "validity": {k: True for k in az.EXPECTED_VALIDITY_KEYS},
        "frozen_evidence_identity": {"accepted_candidate_indices": [478, 479, 480]},
        "evaluation_pass": {"members": members, "pairs": pairs},
    }
    return _reconsolidate(payload)


def make_valid_payload(n_above_per_pair=(1, 1, 1), cross_full=1.0, cross_k0=0.5,
                       a0_full_mean_fn=None, a0_full_ps_fn=None, b0_full_mean_fn=None):
    specs = []
    for idx in range(3):
        a_full = _blocking_fn(n_above_per_pair[idx], cross_full)
        b_full = _blocking_fn(0, cross_full)
        k0 = _blocking_fn(0, cross_k0)
        a_full_ps = None
        if idx == 0:
            if a0_full_mean_fn is not None:
                a_full = a0_full_mean_fn
            if a0_full_ps_fn is not None:
                a_full_ps = a0_full_ps_fn
            if b0_full_mean_fn is not None:
                b_full = b0_full_mean_fn
        specs.append({
            "A_full": (a_full, a_full_ps), "B_full": (b_full, None),
            "A_k0": (k0, None), "B_k0": (k0, None),
        })
    return _assemble(specs, cross_full, cross_k0)


def make_envelope(payload):
    return {
        "family_evaluation_result": payload,
        "family_evaluation_result_sha256": az.sha256_bytes(az.canonical_json_bytes(payload)),
    }


def _identities():
    return {
        "input_size_bytes": 123, "input_whole_file_sha256": "a" * 64,
        "input_payload_sha256": "b" * 64,
        "audit_execution_commit_identity": "0" * 40,
        "analyzer_git_blob_sha": "1" * 40, "analyzer_raw_file_sha256": "2" * 40,
    }


# --------------------------------------------------------------------------- #
# Import and source boundary
# --------------------------------------------------------------------------- #

def test_module_import_is_inert(tmp_path, capsys):
    spec = importlib.util.spec_from_file_location("az_inert_copy", az.__file__)
    module = importlib.util.module_from_spec(spec)
    before_final = REAL_FINAL.exists()
    spec.loader.exec_module(module)
    out = capsys.readouterr()
    assert out.out == "" and out.err == ""
    assert REAL_FINAL.exists() == before_final
    assert not REAL_STAGING.exists()


def test_no_forbidden_imports_and_stdlib_only():
    tree = ast.parse(ANALYZER_SOURCE_BYTES)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    assert roots & FORBIDDEN_IMPORTS == set(), "forbidden import present: %s" % (roots & FORBIDDEN_IMPORTS)
    assert roots <= ALLOWED_STDLIB, "non-allowed import root(s): %s" % (roots - ALLOWED_STDLIB)


def test_no_forbidden_calls():
    tree = ast.parse(ANALYZER_SOURCE_BYTES)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    assert names & FORBIDDEN_CALLS == set(), "forbidden call present: %s" % (names & FORBIDDEN_CALLS)
    # No dynamic import machinery.
    assert "__import__" not in names
    assert "import_module" not in names


# --------------------------------------------------------------------------- #
# Canonical serialization
# --------------------------------------------------------------------------- #

def test_canonical_json_sorted_compact_ascii_no_newline():
    data = {"b": 1, "a": 2, "z": "é"}
    raw = az.canonical_json_bytes(data)
    assert raw == b'{"a":2,"b":1,"z":"\\u00e9"}'
    assert not raw.endswith(b"\n")


def test_canonical_json_rejects_nonfinite():
    with pytest.raises(ValueError):
        az.canonical_json_bytes({"x": float("inf")})
    with pytest.raises(ValueError):
        az.canonical_json_bytes({"x": float("nan")})


def test_canonical_hash_stable():
    data = {"k": [1, 2, 3], "j": "value"}
    assert az.sha256_bytes(az.canonical_json_bytes(data)) == \
        az.sha256_bytes(az.canonical_json_bytes(dict(reversed(list(data.items())))))


def test_negative_zero_normalized():
    assert az._num(-0.0) == 0.0
    assert json.dumps(az._num(-0.0)) == "0.0"


# --------------------------------------------------------------------------- #
# Envelope and payload validation
# --------------------------------------------------------------------------- #

def test_exact_envelope_accepted():
    env = make_envelope(make_valid_payload())
    payload = az.validate_retained_envelope(env)
    az.validate_retained_payload(payload)


def test_extra_top_level_key_refused():
    env = make_envelope(make_valid_payload())
    env["extra"] = 1
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_retained_envelope(env)
    assert exc.value.code == az.INPUT_ENVELOPE_INVALID


def test_missing_top_level_key_refused():
    env = make_envelope(make_valid_payload())
    del env["family_evaluation_result_sha256"]
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_retained_envelope(env)
    assert exc.value.code == az.INPUT_ENVELOPE_INVALID


def test_payload_hash_mismatch_refused():
    env = make_envelope(make_valid_payload())
    env["family_evaluation_result_sha256"] = "0" * 64
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_retained_envelope(env)
    assert exc.value.code == az.INPUT_PAYLOAD_HASH_MISMATCH


@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.update({"schema_name": "wrong"}), az.INPUT_SCHEMA_MISMATCH),
    (lambda p: p.update({"schema_version": "9.9"}), az.INPUT_SCHEMA_MISMATCH),
    (lambda p: p.update({"execution_commit_identity": "0" * 40}), az.INPUT_EXECUTION_IDENTITY_MISMATCH),
    (lambda p: p.update({"replay_record": {"byte_identical": False}}), az.INPUT_REPLAY_STATUS_INVALID),
    (lambda p: p.update({"validity": {"a": False}}), az.INPUT_VALIDITY_INVALID),
    (lambda p: p.update({"failure_record": {"x": 1}}), az.INPUT_VALIDITY_INVALID),
    (lambda p: p["frozen_evidence_identity"].update({"accepted_candidate_indices": [1, 2, 3]}),
     az.INPUT_PAIR_ORDER_MISMATCH),
    (lambda p: p.update({"family_verdict": "SOMETHING_ELSE"}), az.INPUT_FAMILY_VERDICT_MISMATCH),
])
def test_payload_bound_field_refusals(mutate, code):
    payload = make_valid_payload()
    mutate(payload)
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_retained_payload(payload)
    assert exc.value.code == code


def test_nonfinite_retained_distance_yields_disposition_d():
    payload = make_valid_payload()
    payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"][
        "nonidentity_shifts"][0]["per_start"][0]["distance"] = float("inf")
    result = az.run_pure_audit(payload, _identities())
    assert result["audit_valid"] is False
    assert result["family_disposition"] == az.DISPOSITION_D


# --------------------------------------------------------------------------- #
# Inverse-shift validation
# --------------------------------------------------------------------------- #

def test_inverse_shift_multiset_agreement_order_independent():
    payload = make_valid_payload()
    # Reverse the per-start order of one raw shift; sorted multiset still agrees.
    shifts = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"]
    shifts[0]["per_start"] = list(reversed(shifts[0]["per_start"]))
    inverse = az.validate_inverse_shift_classes(payload)
    assert inverse["valid"] is True
    assert inverse["classes_compared"] == 6 * 2 * 31


def test_inverse_shift_missing_shift_disposition_d():
    payload = make_valid_payload()
    sob = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]
    sob["nonidentity_shifts"] = sob["nonidentity_shifts"][:-1]
    result = az.run_pure_audit(payload, _identities())
    assert result["family_disposition"] == az.DISPOSITION_D


def test_inverse_shift_wrong_count_disposition_d():
    payload = make_valid_payload()
    sob = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]
    sob["nonidentity_shifts"][0]["per_start"] = sob["nonidentity_shifts"][0]["per_start"][:63]
    inverse = az.validate_inverse_shift_classes(payload)
    assert inverse["valid"] is False


def test_inverse_shift_multiset_mismatch_disposition_d():
    payload = make_valid_payload()
    shifts = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"]
    # Change only shift r=1 (class q=1, inverse 63); its multiset now differs from r=63.
    shifts[0]["per_start"][0]["distance"] = 999.0
    inverse = az.validate_inverse_shift_classes(payload)
    assert inverse["valid"] is False
    result = az.run_pure_audit(payload, _identities())
    assert result["family_disposition"] == az.DISPOSITION_D
    assert az.INVERSE_SHIFT_VALIDATION_FAILURE in result["ordered_failure_codes"]


def test_inverse_shift_q32_self_inverse_handled():
    payload = make_valid_payload()
    inverse = az.validate_inverse_shift_classes(payload)
    assert inverse["valid"] is True
    # q=32 present as a single class: collapse yields 32 classes.
    member = payload["evaluation_pass"]["members"][0]
    ok, by_r, by_r_mean, _ = az._index_member_shifts(member, "psi_trs")
    cm = az.collapse_validated_inverse_shift_classes(by_r_mean)
    assert set(cm.keys()) == set(range(1, 33))


# --------------------------------------------------------------------------- #
# Deterministic metrics
# --------------------------------------------------------------------------- #

def test_cross_insertion_rank_strict_greater():
    class_means = {q: float(q) for q in range(1, 33)}  # 1..32
    block = az.summarize_blocking_classes(class_means, cross_mean=10.0)
    # classes strictly greater than 10 => q in 11..32 => 22 classes; rank = 23.
    assert block["count_above_cross_mean"] == 22
    assert block["cross_insertion_rank"] == 23
    # Equality is not counted as greater.
    block_eq = az.summarize_blocking_classes(class_means, cross_mean=32.0)
    assert block_eq["count_above_cross_mean"] == 0
    assert block_eq["cross_insertion_rank"] == 1


def test_shift_class_distribution_tie_and_topk_objects():
    class_means = {q: (5.0 if q in (1, 2) else 1.0) for q in range(1, 33)}
    dist = az.summarize_shift_class_distribution(class_means)
    assert dist["argmax_q"] == [1, 2]
    assert dist["top_2"] == [{"q": 1, "mean": 5.0}, {"q": 2, "mean": 5.0}]
    assert dist["top_5"][0] == {"q": 1, "mean": 5.0}
    # top-5 are ordered {q, mean} objects, not an average.
    assert all(set(o.keys()) == {"q", "mean"} for o in dist["top_5"])
    # within-99% count: classes >= 0.99*max(=4.95) => the two 5.0 classes.
    assert dist["within_99_percent"]["count"] == 2


def test_threshold_counts_use_fraction_of_maximum():
    class_means = {q: float(q) for q in range(1, 33)}  # max 32
    dist = az.summarize_shift_class_distribution(class_means)
    # >= 0.90*32 = 28.8 => q in 29..32 => 4 classes.
    assert dist["within_90_percent"]["count"] == 4


def test_contribution_share_and_zero_total():
    distances = [1.0] * 64
    share8 = az._contribution_share(distances, 8)
    assert abs(share8 - (8.0 / 64.0)) < 1e-12
    assert az._contribution_share([0.0] * 64, 8) is None
    summary = az._summarize_start_distances([0.0] * 64)
    assert summary["zero_total"] is True
    assert summary["top_8_contribution_share"] is None


def test_aligned_start_ordering_and_fewer_than_eight():
    member_a = _member(0, "A", _blocking_fn(1, 1.0), _blocking_fn(0, 0.5))
    # Give the blocking class (q with max mean) a per-start pattern with few positives.
    ok, by_r, by_r_mean, _ = az._index_member_shifts(member_a, "psi_trs")
    cm = az.collapse_validated_inverse_shift_classes(by_r_mean)
    # blocking q is min q where class mean is max; craft self > cross at 3 starts only.
    self_max = max(cm.values())
    blocking_q = min(q for q in range(1, 33) if cm[q] == self_max)
    for r in (blocking_q, 64 - blocking_q):
        block = member_a["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"][r - 1]
        assert block["relative_shift"] == r
        vals = [0.0] * 64
        vals[5] = 10.0
        vals[2] = 10.0
        vals[9] = 5.0
        block["per_start"] = _per_start(vals)
    cross_full = [0.0] * 64
    out = az.summarize_blocking_per_start(member_a, cm, cross_full)
    aligned = out["per_raw_shift"][0]["aligned_self_minus_cross"]
    assert aligned["positive_count"] == 3
    starts = [o["start"] for o in aligned["largest_positive_starts"]]
    assert starts == [2, 5, 9]  # tie value 10 at 2 and 5 -> ascending start; then 9
    assert len(aligned["largest_positive_starts"]) == 3  # fewer than 8 available


# --------------------------------------------------------------------------- #
# Pair and family classification
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("count,expected", [
    (0, "narrow"), (2, "narrow"), (3, "intermediate"),
    (7, "intermediate"), (8, "broad"), (32, "broad"),
])
def test_pair_classification_boundaries(count, expected):
    assert az.select_pair_classification(count) == expected


def test_family_disposition_selection():
    assert az.select_family_disposition(["narrow", "narrow", "narrow"]) == az.DISPOSITION_A
    assert az.select_family_disposition(["broad", "broad", "broad"]) == az.DISPOSITION_B
    assert az.select_family_disposition(["narrow", "broad", "narrow"]) == az.DISPOSITION_C
    assert az.select_family_disposition(["narrow", "intermediate", "narrow"]) == az.DISPOSITION_C


def test_end_to_end_family_dispositions():
    a = az.run_pure_audit(make_valid_payload((1, 1, 1)), _identities())
    assert a["family_disposition"] == az.DISPOSITION_A
    b = az.run_pure_audit(make_valid_payload((10, 12, 15)), _identities())
    assert b["family_disposition"] == az.DISPOSITION_B
    c = az.run_pure_audit(make_valid_payload((1, 10, 5)), _identities())
    assert c["family_disposition"] == az.DISPOSITION_C
    for r in (a, b, c):
        assert r["authoritative_f3_verdict_preserved"] == az.REQUIRED_FAMILY_VERDICT


# --------------------------------------------------------------------------- #
# Pure synthetic end-to-end determinism
# --------------------------------------------------------------------------- #

def test_pure_audit_two_runs_byte_identical():
    payload = make_valid_payload((2, 6, 9))
    r1 = az.build_audit_envelope(az.run_pure_audit(payload, _identities()))
    r2 = az.build_audit_envelope(az.run_pure_audit(payload, _identities()))
    assert az.canonical_json_bytes(r1) == az.canonical_json_bytes(r2)
    assert r1["asymmetry_audit_result_sha256"] == r2["asymmetry_audit_result_sha256"]


# --------------------------------------------------------------------------- #
# Retained aggregate means are authoritative for class-level calculations
# --------------------------------------------------------------------------- #

def test_class_level_calcs_use_retained_means_not_per_start():
    low = 1.0 - 1e-9
    high = 1.0 + 1e-9
    cross = 1.0

    def retained(q):       # retained class means: only q=1 above cross
        return high if q == 1 else low

    def per_start(q):      # per-start recomputation: q=2..11 above cross (a decoy)
        return high if 2 <= q <= 11 else low

    def member_b(q):       # member B retained just below cross (isolates A/B diffs)
        return low

    payload = make_valid_payload(
        n_above_per_pair=(1, 1, 1), cross_full=cross,
        a0_full_mean_fn=retained, a0_full_ps_fn=per_start, b0_full_mean_fn=member_b)
    res = az.run_pure_audit(payload, _identities())
    assert res["audit_valid"] is True

    # class ranking follows the retained aggregate mean, not the per-start decoy.
    dist = res["member_audit_tables"][0]["shift_class_distribution"]["psi_trs"]
    assert dist["argmax_q"] == [1]
    assert dist["top_2"][0]["q"] == 1

    # cross insertion rank uses the retained cross aggregate mean and retained class means.
    block_a = res["pair_audit_tables"][0]["blocking_classes"]["psi_trs"]["member_A"]
    assert block_a["classes_above_cross_mean"] == [1]
    assert block_a["count_above_cross_mean"] == 1
    assert block_a["cross_insertion_rank"] == 2

    # A/B class differences use retained means.
    asym = res["pair_audit_tables"][0]["ab_shiftwise_asymmetry"]["psi_trs"]
    assert asym["count_a_greater"] == 1

    # blocking_class_count and pair/family classification follow the retained means
    # (retained gives 1 -> narrow -> A; the per-start decoy would give 10 -> broad).
    pc = res["pair_classifications"][0]
    assert pc["blocking_class_count"] == 1
    assert pc["classification"] == "narrow"
    assert res["family_disposition"] == az.DISPOSITION_A

    # per-start recomputation is emitted only as a non-gating diagnostic.
    diag = res["pair_audit_tables"][0]["diagnostic_per_start_recomputation"]["psi_trs"]
    assert set(diag.keys()) == {
        "retained_cross_mean", "recomputed_cross_mean_from_per_start", "equal"}


def _decorate_nonconstant_perstart(payload):
    """Give every shift a non-constant per-start pattern that depends only on the
    inverse-shift class q (so q and 64-q keep identical multisets), leaving the
    retained aggregate ``mean`` fields untouched."""
    for member in payload["evaluation_pass"]["members"]:
        for variant in ("psi_trs", "psi_trs_k0"):
            for shift in member["self_orbits_by_variant"][variant]["nonidentity_shifts"]:
                q = min(shift["relative_shift"], 64 - shift["relative_shift"])
                vals = [float((q * 7 + s * 3) % 11) for s in range(64)]
                shift["per_start"] = [{"distance": x, "finite": True} for x in vals]
    return payload


def test_per_start_reordering_preserves_class_level_output():
    payload = _decorate_nonconstant_perstart(make_valid_payload((2, 6, 9)))
    res1 = az.run_pure_audit(payload, _identities())
    assert res1["audit_valid"] is True

    for member in payload["evaluation_pass"]["members"]:
        for variant in ("psi_trs", "psi_trs_k0"):
            for shift in member["self_orbits_by_variant"][variant]["nonidentity_shifts"]:
                shift["per_start"] = list(reversed(shift["per_start"]))
    res2 = az.run_pure_audit(payload, _identities())

    # class-level output is invariant under per-start reordering.
    assert res1["member_audit_tables"] == res2["member_audit_tables"]
    assert res1["pair_classifications"] == res2["pair_classifications"]
    assert res1["family_disposition"] == res2["family_disposition"]
    for p1, p2 in zip(res1["pair_audit_tables"], res2["pair_audit_tables"]):
        assert p1["blocking_classes"] == p2["blocking_classes"]
        assert p1["ab_shiftwise_asymmetry"] == p2["ab_shiftwise_asymmetry"]

    # the reordering genuinely changed the per-start (start-indexed) output.
    changed = any(
        res1["pair_audit_tables"][i]["blocking_per_start_full"]
        != res2["pair_audit_tables"][i]["blocking_per_start_full"]
        for i in range(3))
    assert changed


def test_valid_run_strict_derivation():
    base = make_valid_payload()
    assert az._derive_valid_run(base) is True

    missing = copy.deepcopy(base)
    missing["validity"].pop(sorted(missing["validity"].keys())[0])
    assert az._derive_valid_run(missing) is False  # exact key set required

    extra = copy.deepcopy(base)
    extra["validity"]["unexpected_extra_key"] = True
    assert az._derive_valid_run(extra) is False

    truthy = copy.deepcopy(base)
    truthy["validity"][sorted(truthy["validity"].keys())[0]] = 1  # truthy, not True
    assert az._derive_valid_run(truthy) is False

    failed = copy.deepcopy(base)
    failed["failure_record"] = {}
    assert az._derive_valid_run(failed) is False

    replay_int = copy.deepcopy(base)
    replay_int["replay_record"]["byte_identical"] = 1
    assert az._derive_valid_run(replay_int) is False

    replay_str = copy.deepcopy(base)
    replay_str["replay_record"]["byte_identical"] = "true"
    assert az._derive_valid_run(replay_str) is False


def test_retained_gate_inconsistency_yields_disposition_d():
    payload = make_valid_payload((1, 1, 1))
    payload["evaluation_pass"]["pairs"][0]["gates"]["full_cross_mean"] += 1.0
    res = az.run_pure_audit(payload, _identities())
    assert res["audit_valid"] is False
    assert res["family_disposition"] == az.DISPOSITION_D
    assert az.RETAINED_AGGREGATE_INCONSISTENCY in res["ordered_failure_codes"]


def _assert_disposition_d(payload):
    res = az.run_pure_audit(payload, _identities())
    assert res["audit_valid"] is False
    assert res["family_disposition"] == az.DISPOSITION_D
    assert az.RETAINED_AGGREGATE_INCONSISTENCY in res["ordered_failure_codes"]
    return res


def _self_orbit_diag(res, member_id, variant):
    for entry in res["retained_aggregate_validation"]["self_orbit_maximum_diagnostics"]:
        if entry["member_id"] == member_id and entry["variant"] == variant:
            return entry
    raise AssertionError("self-orbit diagnostic not found")


# --------------- Blocker 1: self maximum over all 63 raw shifts --------------- #

def test_self_orbit_maximum_uses_all_63_raw_shifts_not_32_classes():
    payload = make_valid_payload((1, 1, 1))
    shifts = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"]
    # Give the inverse raw shift 64-q=63 the global retained maximum; canonical q=1 stays lower.
    inverse = next(s for s in shifts if s["relative_shift"] == 63)
    inverse["mean"] = 3.0  # per-start left unchanged, so the q/64-q multisets still agree
    _reconsolidate(payload)  # maximum_nonidentity_mean becomes 3.0, gates stay consistent

    res = az.run_pure_audit(payload, _identities())
    assert res["audit_valid"] is True
    diag = _self_orbit_diag(res, "candidate_478_A", "psi_trs")
    assert diag["consistent"] is True
    assert diag["retained_self_orbit_maximum"] == 3.0
    assert diag["all_raw_shift_maximum"] == 3.0
    assert diag["raw_shifts_at_maximum"] == [63]
    assert diag["class_mean_maximum"] == 2.0
    assert diag["canonical_q_at_class_maximum"] == [1]
    assert diag["retained_self_orbit_maximum"] != diag["class_mean_maximum"]

    # canonical class metrics still use raw shift q (mean 2.0), never the inverse or an average.
    dist = res["member_audit_tables"][0]["shift_class_distribution"]["psi_trs"]
    assert dist["top_2"][0] == {"q": 1, "mean": 2.0}
    assert dist["argmax_q"] == [1]


def test_stale_maximum_nonidentity_mean_yields_disposition_d():
    payload = make_valid_payload((1, 1, 1))
    node = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]
    true_max = max(float(s["mean"]) for s in node["nonidentity_shifts"])
    node["maximum_nonidentity_mean"] = true_max + 1.0  # stale, not equal to the 63-shift maximum
    _assert_disposition_d(payload)


# --------------- Blocker 2: retained Boolean gates and recursive min ---------- #

def test_stale_full_dual_orbit_extreme_boolean_yields_d():
    payload = make_valid_payload((1, 1, 1))
    g = payload["evaluation_pass"]["pairs"][0]["gates"]
    g["full_dual_orbit_extreme"] = not g["full_dual_orbit_extreme"]
    _assert_disposition_d(payload)


def test_stale_k0_not_extreme_boolean_yields_d():
    payload = make_valid_payload((1, 1, 1))
    g = payload["evaluation_pass"]["pairs"][0]["gates"]
    g["k0_not_extreme_against_either_member"] = not g["k0_not_extreme_against_either_member"]
    _assert_disposition_d(payload)


def test_non_boolean_truthy_gate_value_yields_d():
    payload = make_valid_payload((1, 1, 1))
    payload["evaluation_pass"]["pairs"][0]["gates"]["full_dual_orbit_extreme"] = 1  # truthy int
    _assert_disposition_d(payload)


def test_stale_recursive_positive_boolean_yields_d():
    payload = make_valid_payload((1, 1, 1))
    g = payload["evaluation_pass"]["pairs"][0]["gates"]
    g["recursive_positive_all_starts"] = not g["recursive_positive_all_starts"]
    _assert_disposition_d(payload)


def test_stale_minimum_recursive_difference_yields_d():
    payload = make_valid_payload((1, 1, 1))
    payload["evaluation_pass"]["pairs"][0]["margins"]["minimum_recursive_difference"] += 1.0
    _assert_disposition_d(payload)


def test_retained_gate_and_recursive_clean_consistency_passes():
    res = az.run_pure_audit(make_valid_payload((1, 1, 1)), _identities())
    assert res["audit_valid"] is True
    assert res["family_disposition"] == az.DISPOSITION_A
    consistency = res["retained_aggregate_validation"]["pair_gate_consistency"]
    assert all(c["retained_gate_consistent"] for c in consistency)


# --------------- Blocker 3: inverse-shift aggregate diagnostics --------------- #

def test_inverse_aggregate_mismatch_is_diagnostic_only():
    payload = make_valid_payload((1, 1, 1))
    shifts = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]["nonidentity_shifts"]
    inverse = next(s for s in shifts if s["relative_shift"] == 63)  # inverse of q=1
    inverse["mean"] = 1.5                          # different retained aggregate mean
    inverse["population_standard_deviation"] = 0.5  # different retained aggregate std
    _reconsolidate(payload)  # per-start multisets untouched; gates stay consistent

    res = az.run_pure_audit(payload, _identities())
    inv = res["inverse_shift_validation"]
    assert inv["valid"] is True
    assert res["audit_valid"] is True
    assert res["family_disposition"] != az.DISPOSITION_D

    diag = inv["inverse_shift_diagnostics"]["candidate_478_A"]["psi_trs"]["1"]
    assert diag["distance_multiset_equal"] is True
    assert set(diag["aggregate_mismatch_fields"]) == {"mean", "population_standard_deviation"}
    assert diag["aggregate_comparisons"]["mean"]["raw_shift_q_value"] == 2.0
    assert diag["aggregate_comparisons"]["mean"]["raw_shift_inverse_value"] == 1.5
    assert diag["aggregate_comparisons"]["mean"]["difference"] == 0.5

    # self-inverse diagnostic for q=32
    diag32 = inv["inverse_shift_diagnostics"]["candidate_478_A"]["psi_trs"]["32"]
    assert diag32["self_inverse"] is True
    assert diag32["aggregate_mismatch_fields"] == []

    # canonical class mean still comes from raw shift q (2.0), not the average (1.75).
    dist = res["member_audit_tables"][0]["shift_class_distribution"]["psi_trs"]
    assert dist["top_2"][0] == {"q": 1, "mean": 2.0}


# --------------------------------------------------------------------------- #
# run_execution: gate / argv / output-path refusals and publication
# --------------------------------------------------------------------------- #

def _write_synth_input(tmp_path, payload):
    env_bytes = az.canonical_json_bytes(make_envelope(payload))
    path = tmp_path / "synthetic_input.json"
    path.write_bytes(env_bytes)
    return path, len(env_bytes), hashlib.sha256(env_bytes).hexdigest()


def _run_exec(tmp_path, payload, *, gate="1", stdout=None, stderr=None, argv=()):
    inp, size, digest = _write_synth_input(tmp_path, payload)
    return az.run_execution(
        gate_value=gate, argv=argv,
        repo_state={"repository_root": str(tmp_path), "audit_execution_commit_identity": "0" * 40},
        source_identity={"analyzer_git_blob_sha": "1" * 40, "analyzer_raw_file_sha256": "2" * 40},
        input_path=inp,
        final_dir=tmp_path / "out" / "final",
        staging_dir=tmp_path / "out" / ".staging",
        stdout=io.StringIO() if stdout is None else stdout,
        stderr=io.StringIO() if stderr is None else stderr,
        expected_input_size=size, expected_input_sha256=digest,
    )


def test_run_execution_exit0_publishes_two_files(tmp_path):
    out = io.StringIO()
    code = _run_exec(tmp_path, make_valid_payload((1, 1, 1)), stdout=out)
    assert code == az.EXIT_OK
    final = tmp_path / "out" / "final"
    assert (final / az.RESULT_FILE_NAME).exists()
    assert (final / az.SUMMARY_FILE_NAME).exists()
    assert not (tmp_path / "out" / ".staging").exists()
    # stdout mirrors the summary file exactly.
    assert out.getvalue().encode("utf-8") == (final / az.SUMMARY_FILE_NAME).read_bytes()


def test_run_execution_disposition_d_still_publishes(tmp_path):
    payload = make_valid_payload((1, 1, 1))
    sob = payload["evaluation_pass"]["members"][0]["self_orbits_by_variant"]["psi_trs"]
    sob["nonidentity_shifts"][0]["per_start"][0]["distance"] = 12345.0  # multiset mismatch
    code = _run_exec(tmp_path, payload)
    assert code == az.EXIT_OK
    result = json.loads((tmp_path / "out" / "final" / az.RESULT_FILE_NAME).read_bytes())
    assert result["asymmetry_audit_result"]["family_disposition"] == az.DISPOSITION_D


def test_run_execution_gate_absent_refusal_no_output(tmp_path):
    code = _run_exec(tmp_path, make_valid_payload(), gate=None)
    assert code == az.EXIT_REFUSAL
    assert not (tmp_path / "out" / "final").exists()
    assert not (tmp_path / "out" / ".staging").exists()


def test_run_execution_cli_arguments_refused(tmp_path):
    code = _run_exec(tmp_path, make_valid_payload(), argv=["--foo"])
    assert code == az.EXIT_REFUSAL


def test_run_execution_final_exists_refusal(tmp_path):
    (tmp_path / "out" / "final").mkdir(parents=True)
    code = _run_exec(tmp_path, make_valid_payload())
    assert code == az.EXIT_REFUSAL


def test_run_execution_staging_exists_refusal(tmp_path):
    (tmp_path / "out" / ".staging").mkdir(parents=True)
    code = _run_exec(tmp_path, make_valid_payload())
    assert code == az.EXIT_REFUSAL


def test_run_execution_input_hash_mismatch_refusal(tmp_path):
    inp, size, _digest = _write_synth_input(tmp_path, make_valid_payload())
    code = az.run_execution(
        gate_value="1",
        repo_state={"repository_root": str(tmp_path), "audit_execution_commit_identity": "0" * 40},
        source_identity={"analyzer_git_blob_sha": "1" * 40, "analyzer_raw_file_sha256": "2" * 40},
        input_path=inp, final_dir=tmp_path / "f", staging_dir=tmp_path / ".s",
        stdout=io.StringIO(), stderr=io.StringIO(),
        expected_input_size=size, expected_input_sha256="0" * 64)
    assert code == az.EXIT_REFUSAL


def test_run_execution_published_final_survives_stdout_failure(tmp_path):
    class _BadStdout:
        def write(self, *a):
            raise IOError("stdout broken")

        def flush(self):
            pass
    code = _run_exec(tmp_path, make_valid_payload((1, 1, 1)), stdout=_BadStdout())
    assert code == az.EXIT_PROCESS_FAILURE
    assert (tmp_path / "out" / "final" / az.RESULT_FILE_NAME).exists()


def test_run_execution_does_not_mutate_input(tmp_path):
    inp, _size, digest = _write_synth_input(tmp_path, make_valid_payload())
    _run_exec_path = az.run_execution(
        gate_value="1",
        repo_state={"repository_root": str(tmp_path), "audit_execution_commit_identity": "0" * 40},
        source_identity={"analyzer_git_blob_sha": "1" * 40, "analyzer_raw_file_sha256": "2" * 40},
        input_path=inp, final_dir=tmp_path / "f", staging_dir=tmp_path / ".s",
        stdout=io.StringIO(), stderr=io.StringIO(),
        expected_input_size=inp.stat().st_size, expected_input_sha256=digest)
    assert _run_exec_path == az.EXIT_OK
    assert hashlib.sha256(inp.read_bytes()).hexdigest() == digest


# --------------------------------------------------------------------------- #
# Publication function: retention semantics
# --------------------------------------------------------------------------- #

def test_publish_final_exists_raises(tmp_path):
    final = tmp_path / "final"
    final.mkdir()
    with pytest.raises(az.AuditProcessFailure) as exc:
        az.write_derived_artifacts_exclusively(final, tmp_path / ".stg", b"{}", b"s")
    assert exc.value.code == az.OUTPUT_PATH_EXISTS


def test_publish_evidence_bearing_staging_retained(tmp_path, monkeypatch):
    final = tmp_path / "final"
    staging = tmp_path / ".stg"
    calls = {"n": 0}
    real_write = az._exclusive_write

    def flaky(path, data):
        calls["n"] += 1
        if calls["n"] == 1:
            return real_write(path, data)  # result file written
        raise IOError("summary write failed")

    monkeypatch.setattr(az, "_exclusive_write", flaky)
    with pytest.raises(az.AuditProcessFailure) as exc:
        az.write_derived_artifacts_exclusively(final, staging, b"{}", b"s")
    assert exc.value.code == az.PUBLICATION_FAILURE
    assert staging.exists()
    assert (staging / az.RESULT_FILE_NAME).exists()  # evidence retained
    assert not final.exists()


def test_publish_rename_failure_retains_complete_staging(tmp_path, monkeypatch):
    final = tmp_path / "final"
    staging = tmp_path / ".stg"

    def bad_rename(src, dst):
        raise OSError("rename failed")

    monkeypatch.setattr(az.os, "rename", bad_rename)
    with pytest.raises(az.AuditProcessFailure):
        az.write_derived_artifacts_exclusively(final, staging, b"{}", b"s")
    assert staging.exists()
    assert (staging / az.RESULT_FILE_NAME).exists()
    assert (staging / az.SUMMARY_FILE_NAME).exists()
    assert not final.exists()


def test_publish_empty_staging_removed_on_early_failure(tmp_path, monkeypatch):
    final = tmp_path / "final"
    staging = tmp_path / ".stg"

    def fail_first(path, data):
        raise IOError("first write failed")

    monkeypatch.setattr(az, "_exclusive_write", fail_first)
    with pytest.raises(az.AuditProcessFailure):
        az.write_derived_artifacts_exclusively(final, staging, b"{}", b"s")
    assert not staging.exists()  # empty staging removed
    assert not final.exists()


# --------------------------------------------------------------------------- #
# Temporary-Git repository-state and source-identity tests
# --------------------------------------------------------------------------- #

def _git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def _init_repo_with_origin(tmp_path, commit_analyzer=True):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "symbolic-ref", "HEAD", "refs/heads/main")
    _git(root, "config", "user.email", "t@t.t")
    _git(root, "config", "user.name", "t")
    (root / "README").write_text("seed\n")
    if commit_analyzer:
        target = root / az.ANALYZER_RELATIVE_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(ANALYZER_SOURCE_BYTES)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    origin = tmp_path / "origin.git"
    _git(root, "init", "--bare", "-q", str(origin), check=False)
    subprocess.run(["git", "init", "--bare", "-q", str(origin)],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "-u", "origin", "main")
    _git(root, "fetch", "-q", "origin")
    return root


def _skip_if_no_git():
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available")


def test_repo_state_success_captures_commit_identity(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    state = az.resolve_and_validate_repository_state(str(root))
    assert state["branch"] == "main"
    assert az._is_sha40(state["audit_execution_commit_identity"])
    head = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    assert state["audit_execution_commit_identity"] == head


def test_repo_state_wrong_branch_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    _git(root, "checkout", "-q", "-b", "feature")
    with pytest.raises(az.AuditRefusal) as exc:
        az.resolve_and_validate_repository_state(str(root))
    assert exc.value.code == az.REPOSITORY_STATE_INVALID


def test_repo_state_head_origin_mismatch_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    (root / "another").write_text("x\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "ahead")  # HEAD now ahead of origin/main
    with pytest.raises(az.AuditRefusal) as exc:
        az.resolve_and_validate_repository_state(str(root))
    assert exc.value.code == az.REPOSITORY_STATE_INVALID


def test_repo_state_dirty_tracked_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    (root / "README").write_text("modified\n")
    with pytest.raises(az.AuditRefusal) as exc:
        az.resolve_and_validate_repository_state(str(root))
    assert exc.value.code == az.REPOSITORY_STATE_INVALID


def test_repo_state_untracked_file_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    (root / "stray.txt").write_text("untracked\n")
    with pytest.raises(az.AuditRefusal) as exc:
        az.resolve_and_validate_repository_state(str(root))
    assert exc.value.code == az.REPOSITORY_STATE_INVALID


def test_source_identity_success(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    ident = az.validate_analyzer_source_identity(str(root), root / az.ANALYZER_RELATIVE_PATH)
    assert az._is_sha40(ident["analyzer_git_blob_sha"])
    assert ident["analyzer_raw_file_sha256"] == hashlib.sha256(ANALYZER_SOURCE_BYTES).hexdigest()


def test_source_identity_uncommitted_analyzer_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path, commit_analyzer=False)
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_analyzer_source_identity(str(root), root / az.ANALYZER_RELATIVE_PATH)
    assert exc.value.code == az.SOURCE_IDENTITY_FAILURE


def test_source_identity_local_byte_mismatch_refused(tmp_path):
    _skip_if_no_git()
    root = _init_repo_with_origin(tmp_path)
    (root / az.ANALYZER_RELATIVE_PATH).write_bytes(ANALYZER_SOURCE_BYTES + b"# tampered\n")
    with pytest.raises(az.AuditRefusal) as exc:
        az.validate_analyzer_source_identity(str(root), root / az.ANALYZER_RELATIVE_PATH)
    assert exc.value.code == az.SOURCE_IDENTITY_FAILURE


# --------------------------------------------------------------------------- #
# Real-path protection and single retained-preflight-only test
# --------------------------------------------------------------------------- #

def test_real_path_protection_blocks_real_final(tmp_path):
    with pytest.raises(AssertionError):
        az.write_derived_artifacts_exclusively(REAL_FINAL, tmp_path / ".stg", b"{}", b"s")


def test_real_path_protection_blocks_real_staging(tmp_path):
    with pytest.raises(AssertionError):
        az.write_derived_artifacts_exclusively(tmp_path / "final", REAL_STAGING, b"{}", b"s")


def test_retained_canonical_preflight_only(monkeypatch):
    if not REAL_RETAINED_JSON.exists():
        pytest.skip("retained canonical F3 result unavailable in this environment")

    def _boom(*a, **k):
        raise AssertionError("complete audit / publication must not run in preflight-only test")

    monkeypatch.setattr(az, "run_pure_audit", _boom)
    monkeypatch.setattr(az, "write_derived_artifacts_exclusively", _boom)
    assert az.GATE_ENV not in os.environ

    loaded = az.load_and_validate_retained_input(REAL_RETAINED_JSON)
    payload = loaded["payload"]
    assert loaded["input_size_bytes"] == az.EXPECTED_INPUT_SIZE_BYTES
    assert loaded["input_whole_file_sha256"] == az.EXPECTED_INPUT_WHOLE_FILE_SHA256
    assert payload["family_verdict"] == az.REQUIRED_FAMILY_VERDICT
    assert payload["execution_commit_identity"] == az.INPUT_EXECUTION_COMMIT_IDENTITY
    assert payload["replay_record"]["byte_identical"] is True
    assert not REAL_FINAL.exists()
    assert not REAL_STAGING.exists()
