"""Pure Phase-13 preflight and administration-identity mechanics.

Nothing in this module starts an E-block, allocates a Brainvision lineage, or
writes evidence.  The live repository facts required by a future authorization
are deliberately supplied by the caller so ordinary instrument tests can use
synthetic values only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import importlib
import os
from pathlib import Path
import platform
import sys
from typing import Final

from brainvision_phase13.schemas import canonical_json_bytes, sha256_hex


PREFLIGHT_READY: Final = "PREFLIGHT_READY"
PREFLIGHT_BLOCKED: Final = "PREFLIGHT_BLOCKED"
_REQUIRED_MANIFEST_NAMES: Final[tuple[str, ...]] = (
    "authority_manifest",
    "expected_result_manifest",
    "evidence_obligations_manifest",
    "authority_clause_registry",
    "criterion_provenance_manifest",
    "fixture_manifest",
    "schedule_manifest",
)


@dataclass(frozen=True, kw_only=True)
class PreflightFacts:
    """Caller-collected facts for a future formal preflight."""

    head: str
    origin_main: str
    worktree_clean: bool
    specification_sha256: str
    manifest_sha256s: Mapping[str, str]
    harness_sha256: str
    output_directory_fresh: bool
    administration_identity_unused: bool
    environment_checks: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, kw_only=True)
class PreflightOutcome:
    """A blocked start has no formal taxonomy and consumes no identity."""

    status: str
    reasons: tuple[str, ...]
    administration_identity_consumed: bool = False
    taxonomy_emitted: bool = False


def _require_sha256(value: object, field: str) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field} must be a lower-case SHA-256 hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field} must be a lower-case SHA-256 hex string")
    return value


def qualification_harness_sha256(package_directory: Path) -> str:
    """Hash only committed test-only Python source in deterministic path order."""
    source_paths = tuple(sorted(package_directory.glob("*.py")))
    if not source_paths:
        raise ValueError("qualification package contains no Python source")
    payload = [
        {
            "path": path.name,
            "sha256": sha256_hex(path.read_bytes()),
        }
        for path in source_paths
    ]
    return sha256_hex(canonical_json_bytes(payload))


def collect_environment_checks(
    *, output_directory: Path, repository_root: Path, required_imports: tuple[str, ...]
) -> tuple[dict[str, object], ...]:
    """Run only deterministic capabilities needed by the future test instrument.

    The isolated probe is removed before preflight returns.  It never creates
    an administration artifact and does not use a random or wall-clock name.
    """
    checks: list[dict[str, object]] = []

    def add(check_id: str, status: bool, observed: object, expected: object) -> None:
        checks.append(
            {
                "check_id": check_id,
                "expected": expected,
                "observed": observed,
                "status": "PASS" if status else "FAIL",
            }
        )

    interpreter = Path(sys.executable).resolve()
    add("python_runtime", bool(sys.version_info >= (3, 11)), {
        "executable": str(interpreter), "version": sys.version,
    }, "Python>=3.11")
    imported: dict[str, bool] = {}
    for module_name in required_imports:
        try:
            importlib.import_module(module_name)
            imported[module_name] = True
        except Exception:
            imported[module_name] = False
    add("required_imports", all(imported.values()), imported, "all imports available")
    resolved_output = output_directory.resolve(strict=False)
    resolved_root = repository_root.resolve()
    try:
        resolved_output.relative_to(resolved_root)
    except ValueError:
        isolated = True
    else:
        isolated = False
    add("isolated_output_root", isolated, str(resolved_output), "outside repository root")
    parent = resolved_output.parent
    add("output_parent_exists", parent.is_dir(), str(parent), "existing directory")
    add("output_directory_fresh", not resolved_output.exists(), str(resolved_output), "absent")
    probe = parent / ".brainvision_phase13_preflight_probe"
    probe_ok = False
    probe_observed: object = "not attempted"
    if parent.is_dir() and not probe.exists():
        first = probe / "first.bin"
        second = probe / "second.bin"
        try:
            probe.mkdir()
            with first.open("xb") as target:
                target.write(b"phase13-preflight")
                target.flush()
                os.fsync(target.fileno())
            os.replace(first, second)
            with second.open("rb") as source:
                probe_ok = source.read() == b"phase13-preflight"
            probe_observed = "create_read_fsync_atomic_replace"
        except OSError as error:
            probe_observed = type(error).__name__
        finally:
            for candidate in (first, second):
                try:
                    candidate.unlink()
                except FileNotFoundError:
                    pass
            try:
                probe.rmdir()
            except OSError:
                pass
    elif probe.exists():
        probe_observed = "reserved_probe_path_exists"
    add("persistence_filesystem", probe_ok, probe_observed, "create/read/fsync/atomic_replace")
    return tuple(checks)


def environment_capable(checks: tuple[Mapping[str, object], ...]) -> bool:
    """A closed structured environment check set, never a default boolean."""
    return bool(checks) and all(
        isinstance(check, Mapping) and check.get("status") == "PASS" for check in checks
    )


def build_administration_identity(
    *,
    expected_head: str,
    specification_sha256: str,
    manifest_sha256s: Mapping[str, str],
    harness_sha256: str,
    command_identity: str,
) -> str:
    """Build a deterministic synthetic-or-formal identity without reserving it."""
    if type(expected_head) is not str or len(expected_head) != 40:
        raise ValueError("expected_head must be an exact 40-character commit SHA")
    if any(character not in "0123456789abcdef" for character in expected_head):
        raise ValueError("expected_head must be lower-case hexadecimal")
    if type(command_identity) is not str or not command_identity:
        raise ValueError("command_identity must be a nonempty string")
    _require_sha256(specification_sha256, "specification_sha256")
    _require_sha256(harness_sha256, "harness_sha256")
    if set(manifest_sha256s) != set(_REQUIRED_MANIFEST_NAMES):
        raise ValueError("manifest identities must have the frozen exact key set")
    ordered_manifest_sha256s = {
        key: manifest_sha256s[key] for key in _REQUIRED_MANIFEST_NAMES
    }
    for key, value in ordered_manifest_sha256s.items():
        _require_sha256(value, key)
    digest = sha256_hex(
        canonical_json_bytes(
            {
                "command_identity": command_identity,
                "expected_head": expected_head,
                "harness_sha256": harness_sha256,
                "manifest_sha256s": ordered_manifest_sha256s,
                "schema_id": "brainvision.phase13.administration_identity.v1",
                "specification_sha256": specification_sha256,
            }
        )
    )
    return "bvphase13a1_" + digest


def verify_preflight(
    *,
    facts: PreflightFacts,
    expected_head: str,
    expected_specification_sha256: str,
    expected_manifest_sha256s: Mapping[str, str],
    expected_harness_sha256: str,
) -> PreflightOutcome:
    """Compare supplied facts; never emit a formal result or reserve an ID."""
    reasons: list[str] = []
    if facts.head != expected_head:
        reasons.append("head_mismatch")
    if facts.origin_main != expected_head:
        reasons.append("origin_main_mismatch")
    if not facts.worktree_clean:
        reasons.append("worktree_not_clean")
    if facts.specification_sha256 != expected_specification_sha256:
        reasons.append("specification_hash_mismatch")
    if dict(facts.manifest_sha256s) != dict(expected_manifest_sha256s):
        reasons.append("manifest_hash_mismatch")
    if facts.harness_sha256 != expected_harness_sha256:
        reasons.append("harness_hash_mismatch")
    if not facts.output_directory_fresh:
        reasons.append("evidence_directory_not_fresh")
    if not facts.administration_identity_unused:
        reasons.append("administration_identity_already_used")
    if not environment_capable(facts.environment_checks):
        reasons.append("environment_not_capable")
    return PreflightOutcome(
        status=PREFLIGHT_READY if not reasons else PREFLIGHT_BLOCKED,
        reasons=tuple(reasons),
    )


def identity_binding_record(
    *,
    expected_head: str,
    actual_head: str,
    origin_main: str,
    administration_identity: str,
    manifest_sha256s: Mapping[str, str],
    harness_sha256: str,
    command_identity: str,
    output_directory: Path,
    environment_checks: tuple[Mapping[str, object], ...],
    authority_manifest: Mapping[str, object],
    inventory: Mapping[str, str],
    authorization_artifact_path: Path,
    authorization_artifact_sha256: str,
    authorization_schema_id: str,
) -> dict[str, object]:
    """Build one immutable pre-start formal identity/environment record."""
    return {
        "administration_identity": administration_identity,
        "authorization_artifact_path": str(authorization_artifact_path),
        "authorization_artifact_sha256": authorization_artifact_sha256,
        "authorization_schema_id": authorization_schema_id,
        "architecture": platform.architecture(),
        "authority_identities": dict(authority_manifest),
        "command_identity": command_identity,
        "environment_checks": [dict(check) for check in environment_checks],
        "expected_head": expected_head,
        "actual_head": actual_head,
        "harness_sha256": harness_sha256,
        "instrument_inventory": dict(inventory),
        "manifest_sha256s": dict(manifest_sha256s),
        "origin_main": origin_main,
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": str(Path(sys.executable).resolve()),
        "qualification_output_directory": str(output_directory.resolve(strict=False)),
        "schema_id": "brainvision.phase13.identity_binding_record.v1",
    }


__all__ = (
    "PREFLIGHT_BLOCKED",
    "PREFLIGHT_READY",
    "PreflightFacts",
    "PreflightOutcome",
    "build_administration_identity",
    "collect_environment_checks",
    "environment_capable",
    "identity_binding_record",
    "qualification_harness_sha256",
    "verify_preflight",
)
