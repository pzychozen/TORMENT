"""TORMENT Brainvision engineering replay benchmark v0.1 (offline; no-write-by-default).

This is an ENGINEERING harness. It orchestrates EXISTING offline Brainvision engineering entry points
and records, for each replay: the repository commit/branch, the exact argument-vector command, the exit
code, elapsed time, stdout/stderr hashes plus bounded tails, relevant input hashes, and pre-run/post-run
repository working-tree state (so any tracked or untracked mutation is detected). It also snapshots the
meaningful ignored artifacts (results files and local .npz inputs) before and after the run so that a
change to a gitignored artifact still fails the benchmark. It reuses existing calculations via subprocess
and never reimplements them.

It introduces NO new scientific target, metric, fixture, control, threshold, parameter, gate, classifier,
model, or interpretation. It makes NO vision, perception, temporal-order, scientific-validation, or
experiment-readiness claim. A completed replay says only that existing code ran and left the repository
(including its meaningful ignored artifacts) unchanged.

Standing (report metadata, not new authority):
    FORMAL HOLD active. Mode 0 active. verdict = HOLD. bounded_experiment_ready = False.
    Brainvision_perceptual_claim_ready = False.

Brainvision stays offline and quarantined. This module imports no torment_service; opens no provider or
live-model route; performs no camera / screen / stream capture; touches no memory-to-prompt,
caller-ownership, MCP, action, movement, autonomy, database, substrate, carrier, or Stage-B route; runs
no classifier or neural route; generates no fixtures; converts or downloads no media; and adds no new
scientific control. Standard library only.

Run (from the repository root, `torment_fabric/`):
    python research/brainvision/run_engineering_benchmark_v0_1.py            # 3 core jobs -> JSON on stdout
    python research/brainvision/run_engineering_benchmark_v0_1.py --list-only
    python research/brainvision/run_engineering_benchmark_v0_1.py --include-local-inputs
    python research/brainvision/run_engineering_benchmark_v0_1.py --output <path-outside-repo>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ----------------------------- fixed identifiers -----------------------------
SCHEMA = "torment.brainvision.engineering_benchmark"
SCHEMA_VERSION = "0.1"
BENCHMARK_NAME = "TORMENT_BRAINVISION_ENGINEERING_BENCHMARK"
BENCHMARK_VERSION = "v0.1"

# research/brainvision/<this file>  ->  parents[2] == repository root (torment_fabric/)
_THIS = Path(__file__).resolve()
DEFAULT_REPO_ROOT = _THIS.parents[2]

BV_RELDIR = "research/brainvision"
LOCAL_INPUTS_RELDIR = BV_RELDIR + "/local_inputs"
RESULTS_RELDIR = BV_RELDIR + "/results"
# Output must never land inside a tracked Brainvision result directory.
PROHIBITED_OUTPUT_RELDIRS = (RESULTS_RELDIR,)

# Bounded summaries so raw output is never embedded unbounded.
TAIL_MAX_LINES = 40
TAIL_MAX_CHARS = 4000

# Report metadata locks (NOT new authority; they restate the standing Brainvision boundary).
LOCKS = {
    "verdict": "HOLD",
    "bounded_experiment_ready": False,
    "Brainvision_perceptual_claim_ready": False,
    "runtime_integration_authorized": False,
    "new_scientific_claim_authorized": False,
}

# ---- fixed child snippets (executed as argument-vector `-c` payloads; never shell strings) ----
# Job 2: replay existing deterministic synthetic behavior WITHOUT writing accepted result artifacts.
JOB2_SYNTHETIC_CODE = (
    "import sys\n"
    'sys.path.insert(0, r"research/brainvision")\n'
    "import run_falsifier\n"
    "run_falsifier.report_all(seeds=range(8), do_write=False)\n"
)

# Optional local-input replays reuse the EXISTING run_npz / format_report surfaces. The parent passes the
# sorted, repo-relative .npz paths as argv; the child only reads them (never writes / converts / mutates).
_LOCAL_REPLAY_TEMPLATE = (
    "import sys\n"
    'sys.path.insert(0, r"research/brainvision")\n'
    "import {module} as m\n"
    "for path in sys.argv[1:]:\n"
    "    res = m.run_npz(path)\n"
    "    print(m.format_report(path, res))\n"
    "    print()\n"
)


class BenchmarkError(RuntimeError):
    """Expected, user-facing configuration/usage/safety failure (clear message, nonzero exit)."""


# ----------------------------- explicit structures -----------------------------
@dataclass(frozen=True)
class JobSpec:
    """A single replay job: identity, standing, its exact argument vector, and its declared inputs."""

    job_id: str
    title: str
    category: str  # "core" | "optional"
    purpose: str
    scientific_standing: str
    argv: List[str]
    input_paths: List[str] = field(default_factory=list)  # repo-relative, posix


@dataclass(frozen=True)
class RepoState:
    """The mutation-relevant surface of the working tree at one instant."""

    status: str  # `git status --porcelain=v1 --untracked-files=all`
    tracked_diff_sha: str  # sha256 of `git diff --binary`
    staged_diff_sha: str  # sha256 of `git diff --cached --binary`


# ----------------------------- hashing / formatting helpers -----------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def bounded_tail(text: str, max_lines: int = TAIL_MAX_LINES, max_chars: int = TAIL_MAX_CHARS) -> str:
    """Last `max_lines` lines, further capped to `max_chars` characters (from the end)."""
    tail = "\n".join(text.splitlines()[-max_lines:])
    if len(tail) > max_chars:
        tail = tail[-max_chars:]
    return tail


def line_count(text: str) -> int:
    return len(text.splitlines())


def to_posix_relpath(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _is_within(child: Path, parent: Path) -> bool:
    """True if `child` is `parent` or lives inside it (component-wise, not string-prefix)."""
    child_s, parent_s = str(child), str(parent)
    try:
        return os.path.commonpath([child_s, parent_s]) == parent_s
    except ValueError:  # different drives on Windows -> cannot be inside
        return False


def _diff_snapshots(before: Dict[str, str], after: Dict[str, str]):
    """Return (created, deleted, modified) sorted path lists comparing two {path: sha256} maps."""
    before_keys, after_keys = set(before), set(after)
    created = sorted(after_keys - before_keys)
    deleted = sorted(before_keys - after_keys)
    modified = sorted(k for k in (before_keys & after_keys) if before[k] != after[k])
    return created, deleted, modified


# ----------------------------- input discovery -----------------------------
def discover_npz(repo_root: Path) -> List[Path]:
    """Deterministically discover existing local .npz inputs (sorted; never created or modified)."""
    d = repo_root / LOCAL_INPUTS_RELDIR
    if not d.is_dir():
        return []
    return sorted(d.glob("*.npz"), key=lambda p: p.name)


def hash_inputs(repo_root: Path, paths: List[Path]) -> Dict[str, str]:
    return {to_posix_relpath(p, repo_root): sha256_file(p) for p in paths}


# ----------------------------- protected ignored-artifact snapshots -----------------------------
def snapshot_protected_artifacts(repo_root: Path) -> Dict[str, str]:
    """Deterministic {repo-relative-posix-path: sha256} over MEANINGFUL IGNORED artifacts:

      * every regular file recursively under research/brainvision/results/
      * every .npz recursively under research/brainvision/local_inputs/

    These are gitignored (so `git status`/`git diff` never see them), yet the harness is no-write-by
    -default: a created/deleted/modified protected artifact must fail the benchmark. Sorted for
    determinism; never creates, deletes, or modifies anything.
    """
    snapshot: Dict[str, str] = {}

    results_dir = repo_root / RESULTS_RELDIR
    if results_dir.is_dir():
        for p in sorted(results_dir.rglob("*"), key=lambda x: x.as_posix()):
            if p.is_file():
                snapshot[to_posix_relpath(p, repo_root)] = sha256_file(p)

    inputs_dir = repo_root / LOCAL_INPUTS_RELDIR
    if inputs_dir.is_dir():
        for p in sorted(inputs_dir.rglob("*.npz"), key=lambda x: x.as_posix()):
            if p.is_file():
                snapshot[to_posix_relpath(p, repo_root)] = sha256_file(p)

    return dict(sorted(snapshot.items()))


# ----------------------------- job inventory -----------------------------
def build_jobs(repo_root: Path, include_local_inputs: bool) -> List[JobSpec]:
    """Deterministic job inventory: three core replays, optionally two prerecorded-input replays."""
    jobs: List[JobSpec] = [
        JobSpec(
            job_id="brainvision_regression_tests",
            title="Brainvision regression tests",
            category="core",
            purpose="implementation regression and lock verification",
            scientific_standing="NO_NEW_SCIENTIFIC_EVIDENCE",
            argv=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                  "tests/research", "-k", "brainvision"],
        ),
        JobSpec(
            job_id="no_write_synthetic_replay",
            title="No-write synthetic falsifier replay",
            category="core",
            purpose=("replay existing deterministic synthetic behavior without writing accepted "
                     "result artifacts"),
            scientific_standing="ENGINEERING_REPLAY_ONLY",
            argv=[sys.executable, "-c", JOB2_SYNTHETIC_CODE],
        ),
        JobSpec(
            job_id="recurrence_det_replay",
            title="Recurrence / DET replay (v1.2a)",
            category="core",
            purpose="replay historical recurrence and control-failure behavior",
            scientific_standing="CANDIDATE_AND_DIAGNOSTIC_ONLY",
            argv=[sys.executable, "research/brainvision/run_sag_recurrence_v1_2a.py"],
        ),
    ]

    if include_local_inputs:
        npz = discover_npz(repo_root)
        if not npz:
            raise BenchmarkError(
                "--include-local-inputs requested but no .npz inputs were found under "
                + LOCAL_INPUTS_RELDIR)
        rel = [to_posix_relpath(p, repo_root) for p in npz]
        jobs.append(JobSpec(
            job_id="local_descriptor_replay",
            title="Prerecorded descriptor replay",
            category="optional",
            purpose="engineering transfer replay on existing prerecorded descriptor inputs",
            scientific_standing="REPLAY_ONLY_NOT_NEW_EVIDENCE",
            argv=[sys.executable, "-c",
                  _LOCAL_REPLAY_TEMPLATE.format(module="run_real_video_descriptors"), *rel],
            input_paths=list(rel),
        ))
        jobs.append(JobSpec(
            job_id="local_sag_control_replay",
            title="Prerecorded SAG-control replay",
            category="optional",
            purpose="engineering transfer replay on existing prerecorded descriptor inputs",
            scientific_standing="REPLAY_ONLY_NOT_NEW_EVIDENCE",
            argv=[sys.executable, "-c",
                  _LOCAL_REPLAY_TEMPLATE.format(module="run_real_video_sag_controls"), *rel],
            input_paths=list(rel),
        ))
    return jobs


# ----------------------------- environment discipline -----------------------------
# Child-process environment overrides applied UNIFORMLY to EVERY benchmark job. PYTHONUTF8 /
# PYTHONIOENCODING force child stdout/stderr to UTF-8 regardless of the parent console code page: on
# Windows the default cp1252 child stdout raised UnicodeEncodeError when an existing report contained a
# scientific symbol such as the Greek capital psi. The harness makes child execution portable itself and
# does not depend on the parent command prompt already exporting UTF-8 variables.
CHILD_ENV_OVERRIDES = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
}


def build_child_env() -> Dict[str, str]:
    """Child env inherits the parent's, then forces bytecode-off + UTF-8 child I/O (portable output)."""
    env = dict(os.environ)
    env.update(CHILD_ENV_OVERRIDES)
    return env


def environment_report() -> Dict[str, object]:
    """Minimal, non-secret environment record (never the whole environment)."""
    report: Dict[str, object] = {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
    report.update(CHILD_ENV_OVERRIDES)  # PYTHONDONTWRITEBYTECODE / PYTHONUTF8 / PYTHONIOENCODING
    return report


# ----------------------------- git (read-only, fatal on safety-critical failure) -----------------------------
def _git(repo_root: Path, args: List[str]) -> subprocess.CompletedProcess:
    """Invoke git; a missing/uninvokable git binary is a fatal BenchmarkError (never swallowed)."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BenchmarkError("git executable not found on PATH: " + str(exc)) from exc
    except OSError as exc:
        raise BenchmarkError("failed to invoke git: " + str(exc)) from exc


def _git_required_bytes(repo_root: Path, args: List[str]) -> bytes:
    """Run a SAFETY-CRITICAL git command; any nonzero exit raises (never returns empty on failure)."""
    cp = _git(repo_root, args)
    if cp.returncode != 0:
        raise BenchmarkError(
            "safety-critical git command failed: git " + " ".join(args)
            + " (exit " + str(cp.returncode) + "): "
            + cp.stderr.decode("utf-8", errors="replace").strip())
    return cp.stdout


def _git_required_text(repo_root: Path, args: List[str]) -> str:
    return _git_required_bytes(repo_root, args).decode("utf-8", errors="replace")


def _git_optional_text(repo_root: Path, args: List[str]) -> Optional[str]:
    """ONLY for non-safety-critical queries that may legitimately fail (e.g. no configured upstream)."""
    cp = _git(repo_root, args)
    if cp.returncode != 0:
        return None
    return cp.stdout.decode("utf-8", errors="replace")


def ensure_git_repository(repo_root: Path) -> str:
    """Fatal precondition: `repo_root` must resolve to a real git working tree. Raises otherwise."""
    top = _git_required_text(repo_root, ["rev-parse", "--show-toplevel"]).strip()
    if not top:
        raise BenchmarkError("could not resolve a git repository root at " + str(repo_root))
    return top


def repository_identity(repo_root: Path) -> Dict[str, Optional[str]]:
    # HEAD and branch are safety-critical (must not be silently blank); upstream may be legitimately unset.
    head = _git_required_text(repo_root, ["rev-parse", "HEAD"]).strip()
    branch = _git_required_text(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()
    upstream = _git_optional_text(
        repo_root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
    upstream = upstream.strip() if upstream else ""
    return {"head": head or None, "branch": branch or None, "upstream": upstream or None}


def capture_repository_state(repo_root: Path) -> RepoState:
    # status and both diffs are safety-critical; a failed inspection must never look like a clean tree.
    status = _git_required_text(repo_root, ["status", "--porcelain=v1", "--untracked-files=all"])
    tracked = _git_required_bytes(repo_root, ["diff", "--binary"])
    staged = _git_required_bytes(repo_root, ["diff", "--cached", "--binary"])
    return RepoState(status=status,
                     tracked_diff_sha=sha256_bytes(tracked),
                     staged_diff_sha=sha256_bytes(staged))


def build_repository_section(repo_root: Path, ident: Dict[str, Optional[str]],
                             pre: RepoState, post: RepoState,
                             protected_before: Dict[str, str],
                             protected_after: Dict[str, str]) -> Dict[str, object]:
    status_unchanged = pre.status == post.status
    tracked_unchanged = pre.tracked_diff_sha == post.tracked_diff_sha
    staged_unchanged = pre.staged_diff_sha == post.staged_diff_sha
    created, deleted, modified = _diff_snapshots(protected_before, protected_after)
    protected_unchanged = not (created or deleted or modified)
    overall_unchanged = (status_unchanged and tracked_unchanged and staged_unchanged
                         and protected_unchanged)
    return {
        "root": str(repo_root),
        "head": ident["head"],
        "branch": ident["branch"],
        "upstream": ident["upstream"],
        "status_before": pre.status,
        "status_after": post.status,
        "pre_run_status": pre.status,
        "post_run_status": post.status,
        "repository_clean_before": pre.status.strip() == "",
        "repository_clean_after": post.status.strip() == "",
        "status_unchanged": status_unchanged,
        "tracked_diff_unchanged": tracked_unchanged,
        "staged_diff_unchanged": staged_unchanged,
        "tracked_diff_sha256_before": pre.tracked_diff_sha,
        "tracked_diff_sha256_after": post.tracked_diff_sha,
        "staged_diff_sha256_before": pre.staged_diff_sha,
        "staged_diff_sha256_after": post.staged_diff_sha,
        "protected_artifacts_before": dict(protected_before),
        "protected_artifacts_after": dict(protected_after),
        "protected_artifacts_created": created,
        "protected_artifacts_deleted": deleted,
        "protected_artifacts_modified": modified,
        "protected_artifacts_unchanged": protected_unchanged,
        "state_unchanged": overall_unchanged,
        "repository_state_unchanged": overall_unchanged,
    }


# ----------------------------- job execution -----------------------------
def _decode_stream(stream_name: str, data: bytes):
    """Strict UTF-8 decode of captured child output.

    Successful child output is expected to be UTF-8 (the harness forces UTF-8 child I/O), so decoding is
    STRICT: it never replacement-decodes, which would silently conceal an encoding defect behind '?'/U+FFFD.
    On an unexpected decode failure it returns a bounded, explicit error note and ok=False, so the job is
    represented as failed rather than as corrupted text. Raw-byte hashing is done by the caller on the
    original bytes and is unaffected. Returns (text_or_None, ok, line_count, bounded_tail)."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        note = "<" + stream_name + " not decodable as UTF-8 (strict): " + str(exc) + ">"
        return None, False, 0, note[:TAIL_MAX_CHARS]
    return text, True, line_count(text), bounded_tail(text)


def run_job(job: JobSpec, repo_root: Path, env: Dict[str, str],
            input_sha256: Dict[str, str]) -> Dict[str, object]:
    """Execute one job as an argument-vector subprocess with repo-root cwd; record it fully."""
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    cp = subprocess.run(
        job.argv,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed = time.perf_counter() - t0
    finished = datetime.now(timezone.utc)

    out_bytes = cp.stdout or b""
    err_bytes = cp.stderr or b""
    # Raw bytes are hashed as-is; text is decoded STRICTLY (a decode failure fails the job, never hides).
    out_text, out_decode_ok, out_lines, out_tail = _decode_stream("stdout", out_bytes)
    err_text, err_decode_ok, err_lines, err_tail = _decode_stream("stderr", err_bytes)
    succeeded = cp.returncode == 0 and out_decode_ok and err_decode_ok

    return {
        "job_id": job.job_id,
        "title": job.title,
        "category": job.category,
        "enabled": True,
        "command": list(job.argv),
        "cwd": str(repo_root),
        "purpose": job.purpose,
        "scientific_standing": job.scientific_standing,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "elapsed_seconds": round(elapsed, 6),
        "exit_code": cp.returncode,
        "succeeded": succeeded,
        "stdout_sha256": sha256_bytes(out_bytes),
        "stderr_sha256": sha256_bytes(err_bytes),
        "stdout_decode_ok": out_decode_ok,
        "stderr_decode_ok": err_decode_ok,
        "stdout_line_count": out_lines,
        "stderr_line_count": err_lines,
        "stdout_tail": out_tail,
        "stderr_tail": err_tail,
        "input_paths": list(job.input_paths),
        "input_sha256": {p: input_sha256[p] for p in job.input_paths if p in input_sha256},
    }


# ----------------------------- output path policy -----------------------------
def validate_output_path(output_path, repo_root: Path) -> Path:
    """Resolve `output_path`; reject any location inside the repository (and, explicitly, a tracked
    result directory). Returns the resolved external path. Never writes."""
    repo = repo_root.resolve()
    p = Path(output_path)
    resolved = (p if p.is_absolute() else (Path.cwd() / p)).resolve()

    for rel in PROHIBITED_OUTPUT_RELDIRS:
        if _is_within(resolved, (repo / rel).resolve()):
            raise BenchmarkError(
                "refusing to write the report into a tracked Brainvision result directory: " + rel)

    if _is_within(resolved, repo):
        raise BenchmarkError(
            "refusing to write the report inside the repository (" + str(resolved)
            + "); choose an --output path outside " + str(repo))

    return resolved


def write_report(output_path: Path, report: Dict[str, object]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)  # only creates missing parents
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, sort_keys=True, indent=2)
        fh.write("\n")


# ----------------------------- report assembly -----------------------------
def build_inputs_section(include_local_inputs: bool, inputs_before: Dict[str, str],
                         inputs_after: Dict[str, str]) -> Dict[str, object]:
    created, deleted, modified = _diff_snapshots(inputs_before, inputs_after)
    inputs_unchanged = not (created or deleted or modified)
    return {
        "local_inputs_included": include_local_inputs,
        "local_inputs_dir": LOCAL_INPUTS_RELDIR,
        "count": len(inputs_before),
        "files": [{"path": p, "sha256": inputs_before[p]} for p in sorted(inputs_before)],
        "inputs_before_sha256": dict(inputs_before),
        "inputs_after_sha256": dict(inputs_after),
        "inputs_created": created,
        "inputs_deleted": deleted,
        "inputs_modified": modified,
        "inputs_unchanged": inputs_unchanged,
    }


def build_report(repo_section: Dict[str, object], inputs_section: Dict[str, object],
                 job_records: List[Dict[str, object]]) -> Dict[str, object]:
    enabled = len(job_records)
    succeeded = sum(1 for r in job_records if r["succeeded"])
    failed = enabled - succeeded
    all_ok = failed == 0
    repo_unchanged = bool(repo_section["repository_state_unchanged"])
    protected_unchanged = bool(repo_section["protected_artifacts_unchanged"])
    inputs_unchanged = bool(inputs_section["inputs_unchanged"])
    total_elapsed = round(sum(float(r["elapsed_seconds"]) for r in job_records), 6)
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "benchmark_name": BENCHMARK_NAME,
        "benchmark_version": BENCHMARK_VERSION,
        "engineering_replay_only": True,
        "scientific_evidence_generated": False,
        "repository": repo_section,
        "environment": environment_report(),
        "jobs": job_records,
        "inputs": inputs_section,
        "summary": {
            "jobs_enabled": enabled,
            "jobs_succeeded": succeeded,
            "jobs_failed": failed,
            "all_jobs_succeeded": all_ok,
            "repository_state_unchanged": repo_unchanged,
            "protected_artifacts_unchanged": protected_unchanged,
            "inputs_unchanged": inputs_unchanged,
            "benchmark_succeeded": bool(all_ok and repo_unchanged and inputs_unchanged),
            "total_elapsed_seconds": total_elapsed,
        },
        "locks": dict(LOCKS),
    }


def build_listing(repo_root: Path, jobs: List[JobSpec],
                  include_local_inputs: bool) -> Dict[str, object]:
    """The --list-only payload: what would run, executing nothing and producing no benchmark output."""
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "benchmark_name": BENCHMARK_NAME,
        "benchmark_version": BENCHMARK_VERSION,
        "engineering_replay_only": True,
        "scientific_evidence_generated": False,
        "list_only": True,
        "local_inputs_included": include_local_inputs,
        "repository_root": str(repo_root),
        "jobs": [
            {
                "job_id": j.job_id,
                "title": j.title,
                "category": j.category,
                "enabled": True,
                "command": list(j.argv),
                "cwd": str(repo_root),
                "purpose": j.purpose,
                "scientific_standing": j.scientific_standing,
                "input_paths": list(j.input_paths),
            }
            for j in jobs
        ],
        "locks": dict(LOCKS),
    }


# ----------------------------- orchestration -----------------------------
def run_benchmark(repo_root: Optional[Path] = None, include_local_inputs: bool = False,
                  output_path=None, list_only: bool = False):
    """Build the inventory and (unless list-only) execute it under repository-mutation protection.

    Returns (report_dict, exit_code). exit_code is 0 only when every job succeeded, no repository
    mutation (status, tracked diff, staged diff, or protected ignored-artifact snapshot) was detected,
    and (with --include-local-inputs) no local .npz input changed. Any safety-critical git failure or an
    invalid repository root raises BenchmarkError and never claims a clean repository.
    """
    repo_root = (Path(repo_root) if repo_root is not None else DEFAULT_REPO_ROOT).resolve()

    resolved_output: Optional[Path] = None
    if output_path is not None:
        resolved_output = validate_output_path(output_path, repo_root)

    jobs = build_jobs(repo_root, include_local_inputs)

    if list_only:
        # --list-only executes nothing and touches no git/subprocess.
        return build_listing(repo_root, jobs, include_local_inputs), 0

    # Fatal precondition: a real git working tree must exist before we can guarantee mutation safety.
    ensure_git_repository(repo_root)

    protected_before = snapshot_protected_artifacts(repo_root)
    inputs_before = hash_inputs(repo_root, discover_npz(repo_root)) if include_local_inputs else {}

    ident = repository_identity(repo_root)
    pre = capture_repository_state(repo_root)

    env = build_child_env()
    job_records = [run_job(job, repo_root, env, inputs_before) for job in jobs]

    post = capture_repository_state(repo_root)
    protected_after = snapshot_protected_artifacts(repo_root)
    inputs_after = hash_inputs(repo_root, discover_npz(repo_root)) if include_local_inputs else {}

    repo_section = build_repository_section(
        repo_root, ident, pre, post, protected_before, protected_after)
    inputs_section = build_inputs_section(include_local_inputs, inputs_before, inputs_after)

    report = build_report(repo_section, inputs_section, job_records)
    exit_code = 0 if report["summary"]["benchmark_succeeded"] else 1

    if resolved_output is not None:  # already validated to be outside the repository
        write_report(resolved_output, report)

    return report, exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_engineering_benchmark_v0_1",
        description=("Offline, no-write-by-default engineering replay benchmark for TORMENT "
                     "Brainvision. Records commands, exit codes, timings, output hashes, input "
                     "hashes, and pre/post repository state. Generates no scientific evidence."),
    )
    parser.add_argument("--list-only", action="store_true",
                        help="list the jobs that would run and exit; execute nothing.")
    parser.add_argument("--include-local-inputs", action="store_true",
                        help="also replay existing prerecorded .npz descriptor inputs (disabled by default).")
    parser.add_argument("--output", metavar="PATH", default=None,
                        help="write the JSON report to PATH (must be outside the repository).")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    ns = parser.parse_args(argv)
    try:
        report, exit_code = run_benchmark(
            include_local_inputs=ns.include_local_inputs,
            output_path=ns.output,
            list_only=ns.list_only,
        )
    except BenchmarkError as exc:
        print("benchmark error: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
