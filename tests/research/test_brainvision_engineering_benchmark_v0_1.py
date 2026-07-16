"""Focused tests for the Brainvision engineering replay benchmark v0.1 (offline).

These lock the harness MACHINERY only: job inventory, optional-input gating, deterministic sorted .npz
discovery + hashing, the report schema and metadata locks, subprocess environment/argument-vector/cwd
discipline, output-path policy, repository-mutation -> failure semantics, protected ignored-artifact
snapshots (results/ files and local_inputs/ .npz), optional-input pre/post hash comparison, and fatal
safety-critical git-failure behavior. They do NOT run the expensive Brainvision replay suite (subprocess
and git execution are mocked where needed), assert no scientific correctness, and hard-code no
machine-specific absolute paths. Offline; no torment_service.
"""
import ast
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
BV_DIR = os.path.realpath(os.path.join(HERE, "..", "..", "research", "brainvision"))
if BV_DIR not in sys.path:
    sys.path.insert(0, BV_DIR)

import run_engineering_benchmark_v0_1 as bench  # noqa: E402

CORE_IDS = ["brainvision_regression_tests", "no_write_synthetic_replay", "recurrence_det_replay"]


# ----------------------------- helpers -----------------------------
class _FakeCP:
    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _ok_record(job, repo_root):
    return {
        "job_id": job.job_id, "title": job.title, "category": job.category, "enabled": True,
        "command": list(job.argv), "cwd": str(repo_root), "purpose": job.purpose,
        "scientific_standing": job.scientific_standing, "started_utc": "t0", "finished_utc": "t1",
        "elapsed_seconds": 0.0, "exit_code": 0, "succeeded": True, "stdout_sha256": "o",
        "stderr_sha256": "e", "stdout_line_count": 1, "stderr_line_count": 0, "stdout_tail": "ok",
        "stderr_tail": "", "input_paths": list(job.input_paths), "input_sha256": {},
    }


def _patch_git_ok(monkeypatch):
    """Mock only the git surface (valid repo, clean & unchanged) so no real git runs. Leaves the
    protected-artifact snapshot and input hashing REAL so filesystem-level checks are exercised."""
    monkeypatch.setattr(bench, "ensure_git_repository", lambda root: str(root))
    monkeypatch.setattr(bench, "capture_repository_state",
                        lambda root: bench.RepoState("", "t", "s"))
    monkeypatch.setattr(bench, "repository_identity",
                        lambda root: {"head": "deadbeef", "branch": "main", "upstream": None})


def _patch_env_ok(monkeypatch):
    """As _patch_git_ok, but also stub the protected-artifact snapshot to empty (fully mocked run)."""
    _patch_git_ok(monkeypatch)
    monkeypatch.setattr(bench, "snapshot_protected_artifacts", lambda root: {})


def _patch_clean_run(monkeypatch):
    _patch_env_ok(monkeypatch)
    monkeypatch.setattr(bench, "run_job",
                        lambda job, repo_root, env, input_sha256: _ok_record(job, repo_root))


def _make_local_inputs(tmp_path, names):
    d = tmp_path / "research" / "brainvision" / "local_inputs"
    d.mkdir(parents=True, exist_ok=True)
    for name, payload in names.items():
        (d / name).write_bytes(payload)
    return d


def _make_results(tmp_path):
    d = tmp_path / "research" / "brainvision" / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _one_shot_mutator(action):
    """Return a run_job stub that performs `action(repo_root)` during the first job only."""
    calls = {"n": 0}

    def run(job, repo_root, env, input_sha256):
        if calls["n"] == 0:
            action(Path(repo_root))
        calls["n"] += 1
        return _ok_record(job, repo_root)

    return run


# ----------------------------- 1-4: inventory + optional gating -----------------------------
def test_inventory_contains_three_core_jobs(tmp_path):
    jobs = bench.build_jobs(tmp_path, include_local_inputs=False)
    assert [j.job_id for j in jobs] == CORE_IDS
    assert all(j.category == "core" for j in jobs)


def test_local_input_jobs_disabled_by_default(tmp_path):
    _make_local_inputs(tmp_path, {"clip1.npz": b"x"})  # present, but flag is off
    jobs = bench.build_jobs(tmp_path, include_local_inputs=False)
    assert not any(j.category == "optional" for j in jobs)
    assert len(jobs) == 3


def test_include_local_inputs_enables_optional_jobs(tmp_path):
    _make_local_inputs(tmp_path, {"clip1.npz": b"x"})
    jobs = bench.build_jobs(tmp_path, include_local_inputs=True)
    cats = [j.category for j in jobs]
    assert cats.count("core") == 3 and cats.count("optional") == 2
    for j in [j for j in jobs if j.category == "optional"]:
        assert j.input_paths == ["research/brainvision/local_inputs/clip1.npz"]


def test_include_local_inputs_without_npz_fails_clearly(tmp_path):
    (tmp_path / "research" / "brainvision" / "local_inputs").mkdir(parents=True)
    with pytest.raises(bench.BenchmarkError):
        bench.build_jobs(tmp_path, include_local_inputs=True)


# ----------------------------- 5: sorted discovery + hashing -----------------------------
def test_npz_discovery_is_sorted_and_hashes_inputs(tmp_path):
    _make_local_inputs(tmp_path, {"b.npz": b"BBB", "a.npz": b"AAA", "notes.txt": b"ignore"})
    found = bench.discover_npz(tmp_path)
    assert [p.name for p in found] == ["a.npz", "b.npz"]  # sorted; non-npz excluded
    assert bench.sha256_file(found[0]) == hashlib.sha256(b"AAA").hexdigest()
    mapping = bench.hash_inputs(tmp_path, found)
    assert mapping == {
        "research/brainvision/local_inputs/a.npz": hashlib.sha256(b"AAA").hexdigest(),
        "research/brainvision/local_inputs/b.npz": hashlib.sha256(b"BBB").hexdigest(),
    }


# ----------------------------- 6: schema + locks -----------------------------
def test_report_has_required_top_level_fields_and_locks(monkeypatch, tmp_path):
    _patch_clean_run(monkeypatch)
    report, code = bench.run_benchmark(repo_root=tmp_path)
    for key in ("schema", "schema_version", "benchmark_name", "benchmark_version",
                "engineering_replay_only", "scientific_evidence_generated", "repository",
                "environment", "jobs", "inputs", "summary", "locks"):
        assert key in report, key
    assert report["benchmark_name"] == "TORMENT_BRAINVISION_ENGINEERING_BENCHMARK"
    assert report["benchmark_version"] == "v0.1"
    assert report["engineering_replay_only"] is True
    assert report["scientific_evidence_generated"] is False
    assert report["locks"] == {
        "verdict": "HOLD",
        "bounded_experiment_ready": False,
        "Brainvision_perceptual_claim_ready": False,
        "runtime_integration_authorized": False,
        "new_scientific_claim_authorized": False,
    }
    for key in ("root", "head", "branch", "upstream", "status_before", "status_after",
                "state_unchanged", "repository_state_unchanged", "pre_run_status",
                "post_run_status", "repository_clean_before", "repository_clean_after",
                "tracked_diff_unchanged", "staged_diff_unchanged",
                "protected_artifacts_before", "protected_artifacts_after",
                "protected_artifacts_created", "protected_artifacts_deleted",
                "protected_artifacts_modified", "protected_artifacts_unchanged"):
        assert key in report["repository"], key
    for key in ("local_inputs_included", "inputs_before_sha256", "inputs_after_sha256",
                "inputs_unchanged"):
        assert key in report["inputs"], key
    for key in ("jobs_enabled", "jobs_succeeded", "jobs_failed", "all_jobs_succeeded",
                "repository_state_unchanged", "protected_artifacts_unchanged", "inputs_unchanged",
                "benchmark_succeeded", "total_elapsed_seconds"):
        assert key in report["summary"], key
    assert code == 0


# ----------------------------- 7-8: env + argv/cwd discipline -----------------------------
def test_child_env_sets_dontwritebytecode():
    env = bench.build_child_env()
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_subprocess_uses_argument_vector_and_repo_root_cwd(monkeypatch, tmp_path):
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["kwargs"] = kwargs
        return _FakeCP(0, b"ok\n", b"")

    monkeypatch.setattr(bench.subprocess, "run", fake_run)
    job = bench.build_jobs(tmp_path, include_local_inputs=False)[1]  # synthetic replay job
    rec = bench.run_job(job, tmp_path, bench.build_child_env(), {})

    assert isinstance(seen["argv"], list)                     # argument vector, not a shell string
    assert seen["kwargs"].get("shell", False) is False        # never shell=True
    assert seen["kwargs"]["cwd"] == str(tmp_path)             # repository-root cwd
    assert seen["kwargs"]["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert seen["argv"][0] == sys.executable                  # runs via sys.executable
    assert rec["succeeded"] is True and rec["exit_code"] == 0


# ----------------------------- 9: stable hashes -----------------------------
def test_stdout_stderr_hashes_stable_for_fixed_bytes():
    assert bench.sha256_bytes(b"hello world") == hashlib.sha256(b"hello world").hexdigest()
    assert bench.sha256_bytes(b"hello world") == bench.sha256_bytes(b"hello world")
    assert bench.sha256_text("hello world") == hashlib.sha256(b"hello world").hexdigest()


# ----------------------------- 10-12: mutation + failure semantics -----------------------------
def test_clean_repository_produces_success(monkeypatch, tmp_path):
    _patch_clean_run(monkeypatch)
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code == 0
    assert report["summary"]["repository_state_unchanged"] is True
    assert report["summary"]["protected_artifacts_unchanged"] is True
    assert report["summary"]["inputs_unchanged"] is True
    assert report["summary"]["benchmark_succeeded"] is True
    assert report["summary"]["jobs_enabled"] == 3


def test_repository_mutation_produces_failure(monkeypatch, tmp_path):
    _patch_env_ok(monkeypatch)
    states = [bench.RepoState("", "t", "s"),
              bench.RepoState(" M research/brainvision/x.py\n", "t2", "s")]
    counter = {"n": 0}

    def fake_capture(root):
        st = states[min(counter["n"], 1)]
        counter["n"] += 1
        return st

    monkeypatch.setattr(bench, "capture_repository_state", fake_capture)
    monkeypatch.setattr(bench, "run_job",
                        lambda job, repo_root, env, input_sha256: _ok_record(job, repo_root))
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code != 0
    assert report["summary"]["repository_state_unchanged"] is False
    assert report["summary"]["benchmark_succeeded"] is False
    assert len(report["jobs"]) == 3  # report still produced with all job records


def test_child_job_failure_fails_benchmark_but_retains_report(monkeypatch, tmp_path):
    _patch_env_ok(monkeypatch)

    def failing(job, repo_root, env, input_sha256):
        rec = _ok_record(job, repo_root)
        rec["exit_code"] = 1
        rec["succeeded"] = False
        return rec

    monkeypatch.setattr(bench, "run_job", failing)
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code != 0
    assert report["summary"]["all_jobs_succeeded"] is False
    assert report["summary"]["jobs_failed"] == 3
    assert len(report["jobs"]) == 3  # report retained despite failures


# ----------------------------- 13: list-only executes nothing -----------------------------
def test_list_only_executes_no_subprocess(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise AssertionError("subprocess must not run under --list-only")

    monkeypatch.setattr(bench.subprocess, "run", boom)
    code = bench.main(["--list-only"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data.get("list_only") is True
    assert [j["job_id"] for j in data["jobs"]] == CORE_IDS


# ----------------------------- 14-16: output-path policy -----------------------------
def test_output_inside_repository_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(bench.BenchmarkError):
        bench.validate_output_path(repo / "sub" / "report.json", repo)


def test_external_output_path_is_accepted(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    out = tmp_path / "external" / "report.json"
    resolved = bench.validate_output_path(out, repo)
    assert str(resolved) == str(out.resolve())


def test_output_in_results_directory_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(bench.BenchmarkError):
        bench.validate_output_path(
            repo / "research" / "brainvision" / "results" / "report.json", repo)


# ----------------------------- 17: no service import / runtime integration -----------------------------
def test_no_torment_service_import_or_runtime_integration():
    with open(bench.__file__, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=bench.__file__)
    stdlib_ok = {
        "__future__", "argparse", "dataclasses", "datetime", "hashlib", "json", "os",
        "pathlib", "platform", "subprocess", "sys", "time", "typing",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("torment"), alias.name
                assert alias.name.split(".")[0] in stdlib_ok, alias.name
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("torment"), mod
            if node.level == 0:
                assert mod.split(".")[0] in stdlib_ok, mod


# ----------------------------- 18-19: protected results-file creation / modification -----------------------------
def test_protected_snapshot_covers_results_and_local_npz(tmp_path):
    results = _make_results(tmp_path)
    (results / "a.json").write_text("{}")
    (results / "sub").mkdir()
    (results / "sub" / "b.csv").write_text("x,y\n")            # recursive regular file under results/
    _make_local_inputs(tmp_path, {"clip1.npz": b"AAA", "ignore.txt": b"no"})
    snap = bench.snapshot_protected_artifacts(tmp_path)
    assert set(snap) == {
        "research/brainvision/results/a.json",
        "research/brainvision/results/sub/b.csv",
        "research/brainvision/local_inputs/clip1.npz",         # .npz only; .txt excluded
    }
    assert snap["research/brainvision/local_inputs/clip1.npz"] == hashlib.sha256(b"AAA").hexdigest()


def test_ignored_results_file_creation_fails_benchmark(monkeypatch, tmp_path):
    _patch_git_ok(monkeypatch)          # git clean/unchanged; protected snapshot stays REAL
    _make_results(tmp_path)             # empty results/ before the run
    monkeypatch.setattr(bench, "run_job", _one_shot_mutator(
        lambda root: (root / "research/brainvision/results/new.json").write_text("{}")))
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code != 0
    assert "research/brainvision/results/new.json" in report["repository"]["protected_artifacts_created"]
    assert report["repository"]["protected_artifacts_unchanged"] is False
    assert report["summary"]["repository_state_unchanged"] is False
    assert report["summary"]["benchmark_succeeded"] is False


def test_ignored_results_file_modification_fails_benchmark(monkeypatch, tmp_path):
    _patch_git_ok(monkeypatch)
    results = _make_results(tmp_path)
    (results / "existing.json").write_text("A")
    monkeypatch.setattr(bench, "run_job", _one_shot_mutator(
        lambda root: (root / "research/brainvision/results/existing.json").write_text("B")))
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code != 0
    assert "research/brainvision/results/existing.json" in report["repository"]["protected_artifacts_modified"]
    assert report["summary"]["benchmark_succeeded"] is False


# ----------------------------- 20: protected-file deletion -----------------------------
def test_protected_file_deletion_fails_benchmark(monkeypatch, tmp_path):
    _patch_git_ok(monkeypatch)
    results = _make_results(tmp_path)
    (results / "gone.json").write_text("here")
    monkeypatch.setattr(bench, "run_job", _one_shot_mutator(
        lambda root: (root / "research/brainvision/results/gone.json").unlink()))
    report, code = bench.run_benchmark(repo_root=tmp_path)
    assert code != 0
    assert "research/brainvision/results/gone.json" in report["repository"]["protected_artifacts_deleted"]
    assert report["repository"]["protected_artifacts_unchanged"] is False
    assert report["summary"]["benchmark_succeeded"] is False


# ----------------------------- 21: local .npz modified during optional replay -----------------------------
def test_local_npz_modification_during_replay_fails(monkeypatch, tmp_path):
    _patch_git_ok(monkeypatch)
    _make_local_inputs(tmp_path, {"clip1.npz": b"AAA"})
    monkeypatch.setattr(bench, "run_job", _one_shot_mutator(
        lambda root: (root / "research/brainvision/local_inputs/clip1.npz").write_bytes(b"BBB")))
    report, code = bench.run_benchmark(repo_root=tmp_path, include_local_inputs=True)
    assert code != 0
    rel = "research/brainvision/local_inputs/clip1.npz"
    assert report["inputs"]["inputs_unchanged"] is False
    assert rel in report["inputs"]["inputs_modified"]
    assert report["inputs"]["inputs_before_sha256"][rel] == hashlib.sha256(b"AAA").hexdigest()
    assert report["inputs"]["inputs_after_sha256"][rel] == hashlib.sha256(b"BBB").hexdigest()
    assert report["summary"]["inputs_unchanged"] is False
    assert report["repository"]["protected_artifacts_unchanged"] is False  # also caught by snapshot
    assert report["summary"]["benchmark_succeeded"] is False


# ----------------------------- 22-24: fatal safety-critical git failure -----------------------------
def test_nonzero_safety_critical_git_command_is_fatal(monkeypatch, tmp_path):
    monkeypatch.setattr(bench.subprocess, "run",
                        lambda *a, **k: _FakeCP(returncode=128, stderr=b"fatal: bad thing"))
    with pytest.raises(bench.BenchmarkError):
        bench.capture_repository_state(tmp_path)          # a failed status must never look clean


def test_missing_git_binary_is_fatal(monkeypatch, tmp_path):
    def no_git(*a, **k):
        raise FileNotFoundError("git")

    monkeypatch.setattr(bench.subprocess, "run", no_git)
    with pytest.raises(bench.BenchmarkError):
        bench.capture_repository_state(tmp_path)


def test_invalid_repository_root_is_fatal(tmp_path):
    # tmp_path is a real directory but NOT a git working tree -> ensure_git_repository must raise,
    # and run_benchmark must propagate it (nonzero) rather than claim a clean repository.
    with pytest.raises(bench.BenchmarkError):
        bench.ensure_git_repository(tmp_path)
    with pytest.raises(bench.BenchmarkError):
        bench.run_benchmark(repo_root=tmp_path)


def test_main_returns_nonzero_on_benchmark_error(monkeypatch):
    def boom(**kwargs):
        raise bench.BenchmarkError("simulated safety failure")

    monkeypatch.setattr(bench, "run_benchmark", boom)
    assert bench.main([]) == 2


# ----------------------------- 27-32: UTF-8 child portability (Windows cp1252 psi defect) -----------------------------
UTF8_ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
PSI = "Ψ"  # Greek capital psi -- the scientific symbol that broke cp1252 child stdout on Windows


def test_child_env_sets_utf8_portability_vars():
    env = bench.build_child_env()
    for key, value in UTF8_ENV.items():
        assert env[key] == value


def test_every_child_job_receives_utf8_environment(monkeypatch, tmp_path):
    # Uniform env across ALL five job types (3 core + 2 optional), independent of the parent's env.
    _patch_env_ok(monkeypatch)
    _make_local_inputs(tmp_path, {"clip1.npz": b"x"})  # enables the two optional jobs
    captured = []

    def capture_run_job(job, repo_root, env, input_sha256):
        captured.append((job.job_id, job.category, dict(env)))
        return _ok_record(job, repo_root)

    monkeypatch.setattr(bench, "run_job", capture_run_job)
    report, code = bench.run_benchmark(repo_root=tmp_path, include_local_inputs=True)
    assert len(captured) == 5
    assert {category for _, category, _ in captured} == {"core", "optional"}  # includes optional jobs
    for _job_id, _category, env in captured:
        for key, value in UTF8_ENV.items():
            assert env[key] == value


def test_environment_section_records_utf8_vars(monkeypatch, tmp_path):
    _patch_clean_run(monkeypatch)
    report, _code = bench.run_benchmark(repo_root=tmp_path)
    env = report["environment"]
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"


def test_unicode_child_succeeds_through_run_job(tmp_path):
    # A lightweight child that prints psi must succeed through the SAME run_job path the harness uses,
    # under the harness UTF-8 child environment. It executes no Brainvision calculation.
    job = bench.JobSpec(
        job_id="unicode_probe", title="unicode probe", category="core",
        purpose="portability probe", scientific_standing="ENGINEERING_REPLAY_ONLY",
        argv=[sys.executable, "-c", 'print("Ψ")'],
    )
    rec = bench.run_job(job, tmp_path, bench.build_child_env(), {})
    assert rec["exit_code"] == 0
    assert rec["succeeded"] is True
    assert rec["stdout_decode_ok"] is True
    assert PSI in rec["stdout_tail"]                       # retained correctly
    assert "�" not in rec["stdout_tail"] and "?" not in rec["stdout_tail"]


def test_run_job_strict_utf8_preserves_psi_and_hashes_raw_bytes(monkeypatch, tmp_path):
    psi_bytes = PSI.encode("utf-8") + b"\n"               # actual UTF-8 bytes of the child's stdout
    monkeypatch.setattr(bench.subprocess, "run",
                        lambda *a, **k: _FakeCP(0, psi_bytes, b""))
    job = bench.build_jobs(tmp_path, include_local_inputs=False)[1]
    rec = bench.run_job(job, tmp_path, bench.build_child_env(), {})
    assert rec["succeeded"] is True and rec["stdout_decode_ok"] is True
    assert rec["stdout_tail"] == PSI                       # strict decode kept psi, no ? / replacement
    assert "�" not in rec["stdout_tail"]
    assert rec["stdout_sha256"] == hashlib.sha256(psi_bytes).hexdigest()  # hash over the real bytes


def test_run_job_marks_undecodable_output_as_failed(monkeypatch, tmp_path):
    bad = b"\xff\xfe\xfa"                                 # not valid UTF-8; must NOT be silently concealed
    monkeypatch.setattr(bench.subprocess, "run",
                        lambda *a, **k: _FakeCP(0, bad, b""))
    job = bench.build_jobs(tmp_path, include_local_inputs=False)[1]
    rec = bench.run_job(job, tmp_path, bench.build_child_env(), {})
    assert rec["stdout_decode_ok"] is False
    assert rec["succeeded"] is False                      # exit 0 but undecodable -> failed job
    assert "not decodable" in rec["stdout_tail"]          # bounded, explicit error note (not corruption)
    assert rec["stdout_sha256"] == hashlib.sha256(bad).hexdigest()  # raw-byte hash preserved
