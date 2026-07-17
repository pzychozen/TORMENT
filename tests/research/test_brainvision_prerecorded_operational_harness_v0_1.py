"""Focused tests for the prerecorded operational harness v0.1 (offline; unit-only).

Small deterministic inputs are UNIT-TEST INPUTS ONLY -- not scientific fixtures and not evidence. These tests
do not assert scientific correctness, hard-code no machine-specific absolute paths, and touch no
torment_service. Most tests monkeypatch ``paired.analyze_paths`` with a deterministic native dictionary;
exactly one focused integration test uses a real temporary .npz to prove verbatim paired-analysis and
companion preservation. The harness must write nothing to disk under any supported mode.
"""
import ast
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_prerecorded_operational_harness_v0_1 as harness  # noqa: E402
import run_prerecorded_paired_analysis_v0_1 as paired  # noqa: E402

GOOD_COMMIT = "0123456789abcdef0123456789abcdef01234567"  # 40 lowercase hex
EXPECTED_TOP_LEVEL = {
    "schema", "authority", "source", "environment", "configuration", "input_manifest",
    "paired_analysis", "analysis_error", "harness_health", "warnings", "replay",
}
EXPECTED_HEALTH_KEYS = {
    "manifest_valid", "inputs_readable_valid", "analyzer_identity_valid", "analysis_completed_valid",
    "clip_count_valid", "serialization_valid", "replay_material_valid", "overall_health",
    "error_codes", "warnings",
}
EXPECTED_AUTHORITY = {
    "FORMAL_HOLD_active": True,
    "Mode_0_active": True,
    "verdict": "HOLD",
    "output_type": "OFFLINE_DESCRIPTIVE_ENGINEERING_DIAGNOSTICS",
    "scientific_claim_authorized": False,
    "temporal_order_claim_authorized": False,
    "perception_or_vision_claim_authorized": False,
    "runtime_integration_authorized": False,
    "production_kernel_modification_authorized": False,
}


# ----------------------------- helpers -----------------------------
def _touch_npz(directory, name, content=b"unit-test-bytes"):
    path = os.path.join(str(directory), name)
    with open(path, "wb") as handle:
        handle.write(content)
    return path


def _write_manifest(directory, entries, name="manifest.json"):
    path = os.path.join(str(directory), name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(entries))
    return path


def _fake_result(ordered_paths, include_sag=True, with_companion=True):
    """Deterministic native-dict stand-in for paired.analyze_paths (UNIT-TEST INPUT ONLY)."""
    assert include_sag is True and with_companion is True
    clips = []
    for ordinal, path in enumerate(ordered_paths):
        clips.append({
            "clip_name": os.path.basename(path),
            "clip_ordinal": ordinal,
            "source": path,
            "descriptors": list(paired.DESCRIPTOR_NAMES),
            "descriptor_responses": {"psi_trs": {"true": {"per_block": [0.1], "median": 0.1, "iqr": 0.0}}},
            "boundary_neutral_companion": {"per_control": {"true": {"per_block": []}}},
            "empty_edge_null": None,  # existing None/null must be preserved verbatim
        })
    return {
        "schema": paired.SCHEMA,
        "analyzer_name": paired.ANALYZER_NAME,
        "analyzer_version": paired.ANALYZER_VERSION,
        "controls": list(paired.CONTROLS),
        "descriptors": list(paired.DESCRIPTOR_NAMES),
        "clips": clips,
        "locks": dict(paired.LOCKS),
        # value text intentionally contains 'perception'/'vision'/'classifier' words: allowed in VALUES.
        "non_claims": "no perception, no vision, no classifier, no temporal-order claim is made.",
        "perception_claim_authorized": False,  # negative authority KEY: allowed
    }


def _install_fake(monkeypatch, fn=_fake_result):
    monkeypatch.setattr(paired, "analyze_paths", fn)


def _collect_keys(obj, acc):
    if isinstance(obj, dict):
        for key, value in obj.items():
            acc.add(key)
            _collect_keys(value, acc)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, acc)
    return acc


def _payload(argv):
    return harness.build_payload(harness._build_parser().parse_args(argv))


# ----------------------------- healthy run + envelope shape -----------------------------
def test_healthy_run_shape_and_exit_zero(tmp_path, monkeypatch, capsys):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    f2 = _touch_npz(tmp_path, "b.npz", content=b"other-bytes")
    payload = _payload([f1, f2, "--source-commit", GOOD_COMMIT])

    assert set(payload.keys()) == EXPECTED_TOP_LEVEL
    assert payload["harness_health"]["overall_health"] is True
    assert payload["harness_health"]["error_codes"] == []
    assert payload["analysis_error"] == {"exception_class": None}
    assert payload["harness_health"]["clip_count_valid"] is True
    assert payload["harness_health"]["analyzer_identity_valid"] is True

    rc = harness._main([f1, f2, "--source-commit", GOOD_COMMIT])
    assert rc == 0
    out = capsys.readouterr()
    assert out.err == ""  # stderr empty on a healthy run without --human-summary
    assert out.out and not out.out.endswith("\n")  # canonical wrapper only, no trailing newline


def test_eleven_top_level_objects_on_healthy_and_invalid(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    healthy = _payload([f1, "--source-commit", GOOD_COMMIT])
    invalid = _payload([f1, "--source-commit", "NOT-A-COMMIT"])
    assert set(healthy.keys()) == EXPECTED_TOP_LEVEL
    assert set(invalid.keys()) == EXPECTED_TOP_LEVEL  # no top-level object omitted on invalid runs


def test_authority_is_exact_frozen_object(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    assert payload["authority"] == EXPECTED_AUTHORITY
    assert "documentation_authorized" not in payload["authority"]
    assert "implementation_authorized" not in payload["authority"]


def test_configuration_frozen_and_hashes_stable(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    p1 = _payload([f1, "--source-commit", GOOD_COMMIT])
    p2 = _payload([f1, "--source-commit", GOOD_COMMIT])
    assert p1["configuration"] == p2["configuration"]
    assert p1["configuration"]["analyzer_nonfinite_policy"] == "ANALYZER_JSONABLE_NONFINITE_TO_NULL"
    assert p1["configuration"]["include_sag"] is True and p1["configuration"]["with_companion"] is True
    assert p1["replay"]["configuration_sha256"] == p2["replay"]["configuration_sha256"]


def test_harness_health_ten_keys_and_overall_is_and(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    health = _payload([f1, "--source-commit", GOOD_COMMIT])["harness_health"]
    assert set(health.keys()) == EXPECTED_HEALTH_KEYS
    seven = [health[k] for k in ("manifest_valid", "inputs_readable_valid", "analyzer_identity_valid",
                                 "analysis_completed_valid", "clip_count_valid", "serialization_valid",
                                 "replay_material_valid")]
    assert health["overall_health"] == all(seven)


# ----------------------------- source-commit -----------------------------
@pytest.mark.parametrize("bad", ["short", "0123456789abcdef0123456789abcdef0123456G",
                                 "0123456789ABCDEF0123456789abcdef01234567", "0" * 39])
def test_source_commit_invalid(tmp_path, monkeypatch, bad):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    payload = _payload([f1, "--source-commit", bad])
    assert "source_commit_invalid" in payload["harness_health"]["error_codes"]
    assert payload["harness_health"]["overall_health"] is False
    assert payload["paired_analysis"] == {}
    assert harness._main([f1, "--source-commit", bad]) == 1


def test_source_commit_required_is_argparse_exit_2(tmp_path):
    f1 = _touch_npz(tmp_path, "a.npz")
    with pytest.raises(SystemExit) as excinfo:
        harness._main([f1])  # missing --source-commit
    assert excinfo.value.code == 2


# ----------------------------- manifest source / schema failures -----------------------------
def test_manifest_source_conflict(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": f1}])
    payload = _payload([f1, "--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_source_conflict" in payload["harness_health"]["error_codes"]
    assert payload["input_manifest"]["entries"] == []
    assert payload["input_manifest"]["input_manifest_sha256"] is None
    assert payload["replay"]["input_path_identity_sha256"] is None
    assert payload["paired_analysis"] == {}


def test_manifest_parse_failed(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    bad = os.path.join(str(tmp_path), "bad.json")
    with open(bad, "w", encoding="utf-8") as handle:
        handle.write("{not valid json")
    payload = _payload(["--manifest", bad, "--source-commit", GOOD_COMMIT])
    assert "manifest_parse_failed" in payload["harness_health"]["error_codes"]
    assert payload["input_manifest"]["entries"] == []
    assert payload["input_manifest"]["input_manifest_sha256"] is None
    assert payload["replay"]["input_path_identity_sha256"] is None
    assert payload["paired_analysis"] == {}


def test_manifest_schema_invalid_toplevel_not_list(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    path = os.path.join(str(tmp_path), "m.json")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps({"logical_id": "x", "path": "y.npz"}))  # object, not a list
    payload = _payload(["--manifest", path, "--source-commit", GOOD_COMMIT])
    assert "manifest_schema_invalid" in payload["harness_health"]["error_codes"]
    assert payload["input_manifest"]["entries"] == []
    assert payload["paired_analysis"] == {}


def test_manifest_schema_invalid_entry_extra_key_preserves_entries(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    manifest = _write_manifest(tmp_path, [
        {"logical_id": "ok", "path": f1},
        {"logical_id": "bad", "path": f1, "extra": 1},  # unknown/additional key
    ])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_schema_invalid" in payload["harness_health"]["error_codes"]
    assert len(payload["input_manifest"]["entries"]) == 2  # entries preserved, not silently removed
    assert payload["input_manifest"]["input_manifest_sha256"] is None
    assert payload["paired_analysis"] == {}


def test_manifest_empty(monkeypatch):
    _install_fake(monkeypatch)
    payload = _payload(["--source-commit", GOOD_COMMIT])  # neither source supplies entries
    assert "manifest_empty" in payload["harness_health"]["error_codes"]
    assert payload["input_manifest"]["entries"] == []
    assert payload["paired_analysis"] == {}


# ----------------------------- per-entry manifest validation -----------------------------
def test_manifest_invalid_logical_id(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    manifest = _write_manifest(tmp_path, [{"logical_id": "-bad", "path": f1}])  # leading hyphen
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_invalid_logical_id" in payload["harness_health"]["error_codes"]
    assert payload["paired_analysis"] == {}


def test_manifest_duplicate_logical_id(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    f2 = _touch_npz(tmp_path, "b.npz", content=b"bbb")
    manifest = _write_manifest(tmp_path, [{"logical_id": "dup", "path": f1},
                                          {"logical_id": "dup", "path": f2}])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_duplicate_logical_id" in payload["harness_health"]["error_codes"]
    assert payload["paired_analysis"] == {}


def test_manifest_wrong_extension(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.txt")  # not .npz
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": f1}])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_wrong_extension" in payload["harness_health"]["error_codes"]
    assert payload["paired_analysis"] == {}


def test_manifest_path_is_directory(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    d = os.path.join(str(tmp_path), "adir.npz")
    os.makedirs(d)
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": d}])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_path_is_directory" in payload["harness_health"]["error_codes"]
    assert payload["harness_health"]["inputs_readable_valid"] is False
    assert payload["paired_analysis"] == {}


def test_manifest_missing_input(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": os.path.join(str(tmp_path), "nope.npz")}])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_missing_input" in payload["harness_health"]["error_codes"]
    assert payload["input_manifest"]["entries"][0]["npz_sha256"] is None  # unhashable -> null
    assert payload["input_manifest"]["input_manifest_sha256"] is None
    assert payload["paired_analysis"] == {}


def test_manifest_duplicate_path(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": f1},
                                          {"logical_id": "y", "path": f1}])  # same normalized path
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_duplicate_path" in payload["harness_health"]["error_codes"]
    assert payload["paired_analysis"] == {}


def test_manifest_duplicate_content_is_warning_only(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz", content=b"same")
    f2 = _touch_npz(tmp_path, "b.npz", content=b"same")  # identical bytes, distinct paths
    manifest = _write_manifest(tmp_path, [{"logical_id": "x", "path": f1},
                                          {"logical_id": "y", "path": f2}])
    payload = _payload(["--manifest", manifest, "--source-commit", GOOD_COMMIT])
    assert "manifest_duplicate_content" in payload["input_manifest"]["warnings"]
    assert payload["harness_health"]["overall_health"] is True  # warning does not invalidate


# ----------------------------- hashing / path identity -----------------------------
def test_hash_is_raw_npz_bytes(tmp_path, monkeypatch):
    import hashlib
    _install_fake(monkeypatch)
    content = b"raw-npz-content"
    f1 = _touch_npz(tmp_path, "a.npz", content=content)
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    assert payload["input_manifest"]["entries"][0]["npz_sha256"] == hashlib.sha256(content).hexdigest()


def test_path_free_manifest_hash_vs_path_sensitive_identity(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    # entries carry no path key
    f1 = _touch_npz(tmp_path, "a.npz", content=b"content")
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    assert set(payload["input_manifest"]["entries"][0].keys()) == {"logical_id", "npz_sha256"}

    # identical content + identical logical_ids in two different dirs -> same manifest hash, different identity
    dir_a = tmp_path / "A"
    dir_b = tmp_path / "B"
    dir_a.mkdir()
    dir_b.mkdir()
    pa = _touch_npz(dir_a, "clip.npz", content=b"same-content")
    pb = _touch_npz(dir_b, "clip.npz", content=b"same-content")
    man_a = _write_manifest(dir_a, [{"logical_id": "clip", "path": pa}], name="ma.json")
    man_b = _write_manifest(dir_b, [{"logical_id": "clip", "path": pb}], name="mb.json")
    payload_a = _payload(["--manifest", man_a, "--source-commit", GOOD_COMMIT])
    payload_b = _payload(["--manifest", man_b, "--source-commit", GOOD_COMMIT])
    assert (payload_a["input_manifest"]["input_manifest_sha256"]
            == payload_b["input_manifest"]["input_manifest_sha256"])  # path-free -> identical
    assert (payload_a["replay"]["input_path_identity_sha256"]
            != payload_b["replay"]["input_path_identity_sha256"])  # path-sensitive -> differ


# ----------------------------- canonical serialization / replay -----------------------------
def test_canonical_output_no_nan_or_infinity_and_null_preserved(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    wrapper = harness.build_wrapper(payload)
    text = harness.canonical_text(wrapper)
    assert "NaN" not in text and "Infinity" not in text
    round_trip = json.loads(text)
    assert round_trip["payload"]["paired_analysis"]["clips"][0]["empty_edge_null"] is None


def test_canonicalizer_rejects_new_bare_nonfinite():
    with pytest.raises(harness._NonFiniteError):
        harness.canonical_text({"x": float("nan")})
    with pytest.raises(harness._NonFiniteError):
        harness.canonical_text({"x": float("inf")})


def test_byte_identical_same_environment_replay(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    argv = [f1, "--source-commit", GOOD_COMMIT]
    w1 = harness.build_wrapper(_payload(argv))
    w2 = harness.build_wrapper(_payload(argv))
    assert harness.canonical_text(w1) == harness.canonical_text(w2)
    assert w1["payload_sha256"] == w2["payload_sha256"]


# ----------------------------- claim locks -----------------------------
def test_prohibited_outcome_keys_absent_but_negative_wording_allowed(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    keys = _collect_keys(payload, set())
    assert keys.isdisjoint(set(harness.PROHIBITED_OUTCOME_KEYS))
    # negative authority KEY allowed; and 'perception'/'vision' words appear only in VALUES (non_claims text)
    assert "perception_claim_authorized" in keys
    assert "perception" in payload["paired_analysis"]["non_claims"]


# ----------------------------- analyzer failure -----------------------------
def test_analyzer_exception_maps_to_analysis_failed(tmp_path, monkeypatch):
    def boom(ordered_paths, include_sag=True, with_companion=True):
        raise ValueError("secret detail that must not leak")

    monkeypatch.setattr(paired, "analyze_paths", boom)
    f1 = _touch_npz(tmp_path, "a.npz")
    payload = _payload([f1, "--source-commit", GOOD_COMMIT])
    assert "analysis_failed" in payload["harness_health"]["error_codes"]
    assert payload["harness_health"]["analysis_completed_valid"] is False
    assert payload["paired_analysis"] == {}
    assert payload["analysis_error"] == {"exception_class": "ValueError"}
    text = harness.canonical_text(harness.build_wrapper(payload))
    assert "secret detail" not in text  # no message/traceback in canonical payload
    assert harness._main([f1, "--source-commit", GOOD_COMMIT]) == 1


# ----------------------------- human summary / transport -----------------------------
def test_human_summary_stderr_behavior(tmp_path, monkeypatch, capsys):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    # default: no stderr
    harness._main([f1, "--source-commit", GOOD_COMMIT])
    default_io = capsys.readouterr()
    assert default_io.err == ""
    # with flag: deterministic stderr derived from payload fields
    harness._main([f1, "--source-commit", GOOD_COMMIT, "--human-summary"])
    flagged_io = capsys.readouterr()
    assert flagged_io.err != ""
    assert GOOD_COMMIT in flagged_io.err and "overall_health" in flagged_io.err
    assert flagged_io.out and not flagged_io.out.endswith("\n")  # stdout still wrapper-only


def test_exit_codes(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    f1 = _touch_npz(tmp_path, "a.npz")
    assert harness._main([f1, "--source-commit", GOOD_COMMIT]) == 0            # healthy
    assert harness._main([f1, "--source-commit", "bad"]) == 1                  # invalid payload
    with pytest.raises(SystemExit) as excinfo:
        harness._main(["--bogus-flag"])                                        # CLI syntax failure
    assert excinfo.value.code == 2


# ----------------------------- no writes / no production imports -----------------------------
def test_no_writes_under_any_mode(tmp_path, monkeypatch):
    _install_fake(monkeypatch)
    input_dir = tmp_path / "inputs"
    work_dir = tmp_path / "work"
    input_dir.mkdir()
    work_dir.mkdir()
    f1 = _touch_npz(input_dir, "a.npz")
    before_inputs = set(os.listdir(input_dir))
    cwd = os.getcwd()
    os.chdir(str(work_dir))
    try:
        harness._main([f1, "--source-commit", GOOD_COMMIT])
        harness._main([f1, "--source-commit", GOOD_COMMIT, "--human-summary"])
        harness._main([f1, "--source-commit", "bad"])  # invalid path also writes nothing
    finally:
        os.chdir(cwd)
    assert os.listdir(str(work_dir)) == []  # no file created in the working directory under any mode
    assert set(os.listdir(input_dir)) == before_inputs  # inputs untouched


def test_no_torment_service_in_sys_modules():
    assert not any(name == "torment_service" or name.startswith("torment_service.")
                   for name in list(sys.modules))


def test_harness_imports_only_paired_analyzer_for_analysis():
    with open(harness.__file__, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported_roots.add(node.module.split(".")[0])
    assert "run_prerecorded_paired_analysis_v0_1" in imported_roots  # sole analysis entry point
    forbidden = {
        "psi_trs", "run_n64_falsifier_v0_1", "descriptors", "symmetry_gain", "metrics", "baselines",
        "rpsr", "psi_mapping", "run_real_video_descriptors", "run_real_video_sag_controls",
    }
    assert imported_roots.isdisjoint(forbidden)
    assert not any(root.startswith("torment_service") for root in imported_roots)
    allowed = {"__future__", "argparse", "contextlib", "hashlib", "io", "json", "math", "os",
               "platform", "re", "sys", "typing", "numpy", "run_prerecorded_paired_analysis_v0_1"}
    assert imported_roots.issubset(allowed)


# ----------------------------- one real .npz integration test -----------------------------
def test_real_npz_verbatim_paired_analysis_and_companion_preserved(tmp_path):
    rng = np.random.default_rng(20260717)
    t = np.arange(64, dtype=float)
    frames = np.empty((64, 8, 8), dtype=float)
    for row in range(8):
        for col in range(8):
            frames[:, row, col] = 0.5 + 0.3 * np.sin(2 * np.pi * (1 + row + col) * t / 41.0) \
                + 0.02 * rng.standard_normal(64)
    frames = np.clip(frames, 0.0, 1.0)
    npz_path = os.path.join(str(tmp_path), "clip.npz")
    np.savez(npz_path, frames=frames)

    reference = paired.analyze_paths([npz_path], include_sag=True, with_companion=True)
    payload = _payload([npz_path, "--source-commit", GOOD_COMMIT])

    assert payload["paired_analysis"] == reference  # embedded verbatim
    assert payload["harness_health"]["overall_health"] is True
    assert payload["harness_health"]["analyzer_identity_valid"] is True
    assert payload["harness_health"]["clip_count_valid"] is True

    ref_companion = reference["clips"][0]["boundary_neutral_companion"]
    got_companion = payload["paired_analysis"]["clips"][0]["boundary_neutral_companion"]
    assert got_companion == ref_companion  # companion subtree preserved unchanged

    # canonical serialization succeeds and carries no bare non-finite tokens
    text = harness.canonical_text(harness.build_wrapper(payload))
    assert "NaN" not in text and "Infinity" not in text
