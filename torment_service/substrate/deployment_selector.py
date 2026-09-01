"""Durable B5-A2 deployment selector and pure startup-agreement resolver.

This module is an administrative fence, not a public backend selector.  Its
SQLite file has no semantic-memory tables and this module deliberately has no
dependency on ``TormentFabric``, REST, or MCP.  A successful native agreement
therefore remains a fact for a later, explicitly authorized cutover phase.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Any, Iterable
from uuid import UUID, uuid4

from .deployment_core_maintenance import (
    CoreDeploymentInspection,
    CoreMaintenanceResult,
    abort_cutover_pending,
    activate_core,
    enter_cutover_pending,
    inspect_contained_core_deployment,
    staging_legacy_witness,
)
from .deployment_types import (
    CoreDeploymentWitness,
    DeploymentResolution,
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
    SelectorState,
    canonical_json,
    require_digest,
    require_relative_core_path,
)
from .errors import DeploymentAuthorityError, DeploymentIdempotencyConflict
from .runtime_qualification import QUALIFIED_SQLITE_RUNTIME, qualify_runtime


_MARKER_CONTRACT = "TORMENT_B5_A2_SELECTOR_ERA"
_MARKER_VERSION = 1
_SELECTOR_CONTRACT = "TORMENT_B5_A2_DEPLOYMENT_SELECTOR"
_SELECTOR_VERSION = 1
_SELECTOR_ERA = "selector-era-v1"
_MAX_CONTROLLED_CORES = 64
_BUSY_TIMEOUT_MS = 1_000
_SELECTOR_COLUMNS = {
    "selector_metadata": (
        ("singleton", "INTEGER", 1),
        ("contract", "TEXT", 0),
        ("schema_version", "INTEGER", 0),
        ("selector_era", "TEXT", 0),
        ("created_at_ns", "INTEGER", 0),
    ),
    "selector_state": (
        ("singleton", "INTEGER", 1),
        ("generation", "INTEGER", 0),
        ("deployment_state", "TEXT", 0),
        ("core_id", "TEXT", 0),
        ("core_relative_path", "TEXT", 0),
        ("descriptor_digest", "TEXT", 0),
        ("profile_digest", "TEXT", 0),
        ("core_witness_digest", "TEXT", 0),
        ("updated_at_ns", "INTEGER", 0),
    ),
    "selector_ledger": (
        ("generation", "INTEGER", 1),
        ("previous_generation", "INTEGER", 0),
        ("previous_deployment_state", "TEXT", 0),
        ("previous_core_id", "TEXT", 0),
        ("previous_core_relative_path", "TEXT", 0),
        ("previous_descriptor_digest", "TEXT", 0),
        ("previous_profile_digest", "TEXT", 0),
        ("previous_core_witness_digest", "TEXT", 0),
        ("new_generation", "INTEGER", 0),
        ("new_deployment_state", "TEXT", 0),
        ("new_core_id", "TEXT", 0),
        ("new_core_relative_path", "TEXT", 0),
        ("new_descriptor_digest", "TEXT", 0),
        ("new_profile_digest", "TEXT", 0),
        ("new_core_witness_digest", "TEXT", 0),
        ("operation_key", "TEXT", 0),
        ("canonical_intent", "TEXT", 0),
        ("reason_kind", "TEXT", 0),
        ("recorded_at_ns", "INTEGER", 0),
    ),
}


@dataclass(frozen=True)
class SelectorPaths:
    """Only the controlled deployment-administration locations for one root."""

    data_root: Path
    deployment_root: Path
    core_root: Path
    marker_path: Path
    selector_path: Path


def selector_paths(data_root: str | Path) -> SelectorPaths:
    """Return controlled paths without creating a directory or opening a database."""

    root = _data_root(data_root)
    substrate = root / "substrate"
    deployment = substrate / "deployment"
    return SelectorPaths(
        data_root=root,
        deployment_root=deployment,
        core_root=substrate / "cores",
        marker_path=deployment / "selector-era-v1.json",
        selector_path=deployment / "selector.sqlite",
    )


def establish_selector_era(*, data_root: str | Path) -> Path:
    """Establish the static, write-once selector-era marker idempotently.

    The document contains no mutable deployment decision.  A retry accepts
    only the same canonical document; a malformed or different pre-existing
    marker is an authority failure rather than an opportunity to rewrite it.
    """

    paths = selector_paths(data_root)
    marker = _marker_bytes()
    if paths.marker_path.exists() or paths.marker_path.is_symlink():
        _read_marker(paths)
        return paths.marker_path
    if paths.selector_path.exists() or paths.selector_path.is_symlink():
        raise DeploymentAuthorityError("selector without its era marker is incompatible")
    _prepare_deployment_root(paths)
    _atomic_create(paths.marker_path, marker)
    _read_marker(paths)
    return paths.marker_path


def initialize_selector(*, data_root: str | Path, operation_key: str) -> SelectorState:
    """Create the selector's immutable generation-zero ledger entry once."""

    _require_operation_key(operation_key)
    paths = selector_paths(data_root)
    _read_marker(paths)
    intent = {
        "contract": _SELECTOR_CONTRACT,
        "kind": "INITIALIZE_SELECTOR",
        "operation_key": operation_key,
    }
    if paths.selector_path.exists() or paths.selector_path.is_symlink():
        with _open_selector(paths.selector_path, writable=False) as connection:
            state, ledger = _validated_selector(connection)
        existing = _ledger_for_operation(ledger, operation_key)
        if existing is None:
            raise DeploymentAuthorityError("selector is already initialized")
        _require_same_intent(existing, intent)
        return _state_from_ledger(existing, prefix="new")

    # Construct a fully durable database out-of-place, then link it into the
    # authority location.  A process death cannot leave a blank or half-schema
    # selector at the target path.
    _prepare_deployment_root(paths)
    temporary = paths.deployment_root / f".selector-init-{uuid4().hex}.sqlite"
    try:
        with _open_selector(temporary, writable=True, create=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _create_selector_schema(connection)
                initial = SelectorState(
                    generation=0,
                    deployment_state=DeploymentState.LEGACY_ACTIVE,
                    core_id=None,
                    core_relative_path=None,
                    descriptor_digest=None,
                    profile_digest=None,
                    core_witness_digest=None,
                    updated_at_ns=time.time_ns(),
                )
                _write_state(connection, initial)
                _append_ledger(
                    connection,
                    previous=None,
                    result=initial,
                    operation_key=operation_key,
                    intent=intent,
                    reason_kind="INITIALIZE_SELECTOR",
                )
                connection.execute("COMMIT")
                checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
                if checkpoint is None or checkpoint[0] != 0:
                    raise DeploymentAuthorityError("selector initialization WAL checkpoint failed")
            except Exception:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        _fsync_file(temporary)
        try:
            os.link(temporary, paths.selector_path)
        except FileExistsError:
            # Another administrator won the one-time create race.  Its ledger
            # is the only possible authority, including for our retry key.
            with _open_selector(paths.selector_path, writable=False) as connection:
                _state, ledger = _validated_selector(connection)
            existing = _ledger_for_operation(ledger, operation_key)
            if existing is None:
                raise DeploymentAuthorityError("selector was initialized by another operation")
            _require_same_intent(existing, intent)
            return _state_from_ledger(existing, prefix="new")
        with _open_selector(paths.selector_path, writable=False) as connection:
            state, _ledger = _validated_selector(connection)
        return state
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def read_selector_state(*, data_root: str | Path) -> SelectorState:
    """Read one valid selector snapshot.  This never creates selector state."""

    paths = selector_paths(data_root)
    _read_marker(paths)
    if not paths.selector_path.is_file() or paths.selector_path.is_symlink():
        raise DeploymentAuthorityError("selector is missing")
    with _open_selector(paths.selector_path, writable=False) as connection:
        state, _ledger = _validated_selector(connection)
    return state


def begin_cutover_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    descriptor_digest: str,
    profile: QualifiedDeploymentProfile,
    expected_generation: int,
    operation_key: str,
) -> SelectorState:
    """Move external authority from LEGACY_ACTIVE to CUTOVER_PENDING.

    The selected core is inspected before the transition and must still be an
    inert STAGING/LEGACY core.  This is the first durable step in B5-A2's
    ordering; it does not modify that core.
    """

    require_relative_core_path(core_relative_path)
    require_digest(descriptor_digest, "descriptor_digest")
    _require_generation(expected_generation)
    _require_operation_key(operation_key)
    intent = {
        "contract": _SELECTOR_CONTRACT,
        "kind": "BEGIN_CUTOVER_PENDING",
        "operation_key": operation_key,
        "expected_generation": expected_generation,
        "expected_state": DeploymentState.LEGACY_ACTIVE.value,
        "core_relative_path": core_relative_path,
        "descriptor_digest": descriptor_digest,
        "profile_digest": profile.digest,
    }
    recovered = _recover_selector_operation(data_root, operation_key, intent)
    if recovered is not None:
        return recovered
    inspection = inspect_contained_core_deployment(
        data_root=data_root, core_relative_path=core_relative_path
    )
    witness = staging_legacy_witness(
        inspection,
        descriptor_digest=descriptor_digest,
        profile_digest=profile.digest,
    )
    result = SelectorState(
        generation=expected_generation + 1,
        deployment_state=DeploymentState.CUTOVER_PENDING,
        core_id=witness.core_id,
        core_relative_path=core_relative_path,
        descriptor_digest=descriptor_digest,
        profile_digest=profile.digest,
        core_witness_digest=witness.digest,
        updated_at_ns=time.time_ns(),
    )
    return _transition_selector(
        data_root=data_root,
        expected_generation=expected_generation,
        expected_state=DeploymentState.LEGACY_ACTIVE,
        result=result,
        operation_key=operation_key,
        intent=intent,
        reason_kind="BEGIN_CUTOVER_PENDING",
    )


def activate_selector_native(
    *,
    data_root: str | Path,
    core_relative_path: str,
    core_result: CoreMaintenanceResult,
    expected_generation: int,
    operation_key: str,
) -> SelectorState:
    """Finalize external PENDING -> NATIVE only after core-side activation."""

    _require_generation(expected_generation)
    _require_operation_key(operation_key)
    if core_result.transition_kind != "ACTIVATE_CORE":
        raise DeploymentAuthorityError("selector activation requires an ACTIVATE_CORE receipt")
    intent = {
        "contract": _SELECTOR_CONTRACT,
        "kind": "ACTIVATE_SELECTOR_NATIVE",
        "operation_key": operation_key,
        "expected_generation": expected_generation,
        "expected_state": DeploymentState.CUTOVER_PENDING.value,
        "core_relative_path": core_relative_path,
        "activation_maintenance_id": str(core_result.maintenance_id),
        "core_witness_digest": core_result.witness.digest,
    }
    recovered = _recover_selector_operation(data_root, operation_key, intent)
    if recovered is not None:
        return recovered
    actual = inspect_contained_core_deployment(
        data_root=data_root, core_relative_path=core_relative_path
    )
    if actual.witness != core_result.witness:
        raise DeploymentAuthorityError("activation receipt no longer matches the selected core")
    if (
        actual.core_role != "ACTIVE_CORE"
        or actual.deployment_state is not DeploymentState.NATIVE_ACTIVE
    ):
        raise DeploymentAuthorityError("selector activation requires an ACTIVE_CORE/NATIVE_ACTIVE core")
    result_witness = core_result.witness
    result = SelectorState(
        generation=expected_generation + 1,
        deployment_state=DeploymentState.NATIVE_ACTIVE,
        core_id=result_witness.core_id,
        core_relative_path=core_relative_path,
        descriptor_digest=result_witness.descriptor_digest,
        profile_digest=result_witness.profile_digest,
        core_witness_digest=result_witness.digest,
        updated_at_ns=time.time_ns(),
    )
    return _transition_selector(
        data_root=data_root,
        expected_generation=expected_generation,
        expected_state=DeploymentState.CUTOVER_PENDING,
        result=result,
        operation_key=operation_key,
        intent=intent,
        reason_kind="ACTIVATE_SELECTOR_NATIVE",
        expected_selected_core_relative_path=core_relative_path,
    )


def abort_selector_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    core_result: CoreMaintenanceResult,
    expected_generation: int,
    operation_key: str,
) -> SelectorState:
    """Safely return external PENDING -> LEGACY after the core-side abort proof."""

    _require_generation(expected_generation)
    _require_operation_key(operation_key)
    if core_result.transition_kind != "ABORT_CUTOVER_PENDING" or not core_result.safe_abort_proven:
        raise DeploymentAuthorityError("selector abort requires a safe ABORT_CUTOVER_PENDING receipt")
    intent = {
        "contract": _SELECTOR_CONTRACT,
        "kind": "ABORT_SELECTOR_PENDING",
        "operation_key": operation_key,
        "expected_generation": expected_generation,
        "expected_state": DeploymentState.CUTOVER_PENDING.value,
        "core_relative_path": core_relative_path,
        "abort_maintenance_id": str(core_result.maintenance_id),
        "core_witness_digest": core_result.witness.digest,
    }
    recovered = _recover_selector_operation(data_root, operation_key, intent)
    if recovered is not None:
        return recovered
    actual = inspect_contained_core_deployment(
        data_root=data_root, core_relative_path=core_relative_path
    )
    if actual.witness != core_result.witness or actual.ever_active:
        raise DeploymentAuthorityError("selector abort lacks a never-active core proof")
    if (
        actual.core_role != "STAGING"
        or actual.deployment_state is not DeploymentState.LEGACY_ACTIVE
    ):
        raise DeploymentAuthorityError("selector abort requires a restored STAGING/LEGACY core")
    result = SelectorState(
        generation=expected_generation + 1,
        deployment_state=DeploymentState.LEGACY_ACTIVE,
        core_id=None,
        core_relative_path=None,
        descriptor_digest=None,
        profile_digest=None,
        core_witness_digest=None,
        updated_at_ns=time.time_ns(),
    )
    return _transition_selector(
        data_root=data_root,
        expected_generation=expected_generation,
        expected_state=DeploymentState.CUTOVER_PENDING,
        result=result,
        operation_key=operation_key,
        intent=intent,
        reason_kind="ABORT_SELECTOR_PENDING",
        expected_selected_core_relative_path=core_relative_path,
    )


def resolve_deployment_agreement(
    *, data_root: str | Path, effective_profile: QualifiedDeploymentProfile
) -> DeploymentResolution:
    """Resolve durable agreement facts without routing, writes, or Fabric creation."""

    try:
        paths = selector_paths(data_root)
        marker_exists = paths.marker_path.exists() or paths.marker_path.is_symlink()
        selector_exists = paths.selector_path.exists() or paths.selector_path.is_symlink()
        if not marker_exists and not selector_exists:
            _require_only_inert_controlled_cores(paths, selected=None)
            return DeploymentResolution(DeploymentResolutionMode.LEGACY_PUBLIC, "pre-selector-compatible")
        if marker_exists != selector_exists:
            return _refused("selector-era-marker-and-selector-must-coexist")
        _read_marker(paths)
        with _open_selector(paths.selector_path, writable=False) as connection:
            state, _ledger = _validated_selector(connection)
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            _require_only_inert_controlled_cores(paths, selected=None)
            return DeploymentResolution(
                DeploymentResolutionMode.LEGACY_PUBLIC,
                "durable-legacy-selector",
                selector_state=state,
            )
        inspection = _require_selected_core(paths, state)
        _require_only_inert_controlled_cores(paths, selected=state.core_relative_path)
        if state.deployment_state is DeploymentState.CUTOVER_PENDING:
            if inspection.core_role not in {"STAGING", "ACTIVE_CORE"}:
                return _refused("selected-core-role-is-not-maintenance-eligible", state, inspection)
            if inspection.deployment_state not in {
                DeploymentState.LEGACY_ACTIVE,
                DeploymentState.CUTOVER_PENDING,
                DeploymentState.NATIVE_ACTIVE,
            }:
                return _refused("selected-core-state-is-not-maintenance-eligible", state, inspection)
            return DeploymentResolution(
                DeploymentResolutionMode.MAINTENANCE_ONLY,
                "cutover-pending-is-never-public-routing",
                selector_state=state,
                core_witness=inspection.witness,
            )
        return _resolve_native_agreement(state, inspection, effective_profile)
    except Exception as exc:
        # Resolver callers require a disposition, not an exception which might
        # tempt startup code to fall back to legacy.  Deliberately preserve only
        # a stable class-level reason rather than raw SQLite/path details.
        if isinstance(exc, DeploymentAuthorityError):
            return _refused("durable-deployment-authority-invalid")
        return _refused("durable-deployment-authority-unavailable")


def _resolve_native_agreement(
    state: SelectorState,
    inspection: CoreDeploymentInspection,
    effective_profile: QualifiedDeploymentProfile,
) -> DeploymentResolution:
    witness = inspection.witness
    if (
        inspection.core_role != "ACTIVE_CORE"
        or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
        or witness is None
    ):
        return _refused("native-selector-core-is-not-active", state, inspection)
    if (
        witness.core_id != state.core_id
        or witness.descriptor_digest != state.descriptor_digest
        or witness.profile_digest != state.profile_digest
        or witness.digest != state.core_witness_digest
    ):
        return _refused("native-selector-core-witness-mismatch", state, inspection)
    if not effective_profile.is_qualified or effective_profile.digest != state.profile_digest:
        return _refused("effective-profile-is-not-the-qualified-selector-profile", state, inspection)
    try:
        runtime = qualify_runtime()
    except Exception:
        return _refused("actual-sqlite-runtime-is-not-qualified", state, inspection)
    if runtime.sqlite_runtime_version != QUALIFIED_SQLITE_RUNTIME:
        return _refused("actual-sqlite-runtime-is-not-exactly-qualified", state, inspection)
    return DeploymentResolution(
        DeploymentResolutionMode.NATIVE_AGREEMENT,
        "native-agreement-qualified-no-public-routing",
        selector_state=state,
        core_witness=witness,
    )


def _transition_selector(
    *,
    data_root: str | Path,
    expected_generation: int,
    expected_state: DeploymentState,
    result: SelectorState,
    operation_key: str,
    intent: dict[str, Any],
    reason_kind: str,
    expected_selected_core_relative_path: str | None = None,
) -> SelectorState:
    paths = selector_paths(data_root)
    _read_marker(paths)
    if not paths.selector_path.is_file() or paths.selector_path.is_symlink():
        raise DeploymentAuthorityError("selector is missing")
    with _open_selector(paths.selector_path, writable=True) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            current, ledger = _validated_selector(connection)
            existing = _ledger_for_operation(ledger, operation_key)
            if existing is not None:
                _require_same_intent(existing, intent)
                connection.execute("COMMIT")
                return _state_from_ledger(existing, prefix="new")
            if current.generation != expected_generation or current.deployment_state is not expected_state:
                raise DeploymentAuthorityError("selector expected predecessor does not match durable state")
            if (
                expected_selected_core_relative_path is not None
                and current.core_relative_path != expected_selected_core_relative_path
            ):
                raise DeploymentAuthorityError("selector predecessor names a different controlled core")
            if result.generation != current.generation + 1:
                raise DeploymentAuthorityError("selector generation is not monotonic")
            _write_state(connection, result)
            _append_ledger(
                connection,
                previous=current,
                result=result,
                operation_key=operation_key,
                intent=intent,
                reason_kind=reason_kind,
            )
            _validated_selector(connection)
            connection.execute("COMMIT")
            return result
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise


def _recover_selector_operation(
    data_root: str | Path, operation_key: str, intent: dict[str, Any]
) -> SelectorState | None:
    """Recover an exact committed operation before inspecting its core.

    This permits a lost response to be retried after a later authorized core
    maintenance step has changed the selected core.
    """

    paths = selector_paths(data_root)
    _read_marker(paths)
    if not paths.selector_path.is_file() or paths.selector_path.is_symlink():
        raise DeploymentAuthorityError("selector is missing")
    with _open_selector(paths.selector_path, writable=False) as connection:
        _state, ledger = _validated_selector(connection)
    existing = _ledger_for_operation(ledger, operation_key)
    if existing is None:
        return None
    _require_same_intent(existing, intent)
    return _state_from_ledger(existing, prefix="new")


def _require_selected_core(paths: SelectorPaths, state: SelectorState) -> CoreDeploymentInspection:
    assert state.core_relative_path is not None and state.core_id is not None
    inspection = inspect_contained_core_deployment(
        data_root=paths.data_root, core_relative_path=state.core_relative_path
    )
    if inspection.core_id != state.core_id:
        raise DeploymentAuthorityError("selected core UUID disagrees with selector")
    return inspection


def _require_only_inert_controlled_cores(
    paths: SelectorPaths, *, selected: str | None
) -> None:
    for relative, inspection in _controlled_core_inspections(paths):
        if selected is not None and relative == selected:
            continue
        if (
            inspection.core_role != "STAGING"
            or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
        ):
            raise DeploymentAuthorityError("unselected controlled core asserts cutover authority")


def _controlled_core_inspections(paths: SelectorPaths) -> Iterable[tuple[str, CoreDeploymentInspection]]:
    if paths.core_root.is_symlink():
        raise DeploymentAuthorityError("controlled core root is invalid")
    if not paths.core_root.exists():
        return ()
    if not paths.core_root.is_dir():
        raise DeploymentAuthorityError("controlled core root is invalid")
    entries = sorted(paths.core_root.iterdir(), key=lambda value: value.name)
    candidates = [entry for entry in entries if entry.suffix.lower() == ".db"]
    if len(candidates) > _MAX_CONTROLLED_CORES:
        raise DeploymentAuthorityError("controlled core inspection bound exceeded")
    inspected: list[tuple[str, CoreDeploymentInspection]] = []
    for entry in candidates:
        if not entry.is_file() or entry.is_symlink():
            raise DeploymentAuthorityError("controlled core file is invalid")
        relative = require_relative_core_path(entry.name)
        inspected.append(
            (
                relative,
                inspect_contained_core_deployment(
                    data_root=paths.data_root, core_relative_path=relative
                ),
            )
        )
    return tuple(inspected)


def _refused(
    reason: str,
    state: SelectorState | None = None,
    inspection: CoreDeploymentInspection | None = None,
) -> DeploymentResolution:
    return DeploymentResolution(
        DeploymentResolutionMode.REFUSED,
        reason,
        selector_state=state,
        core_witness=None if inspection is None else inspection.witness,
    )


def _marker_bytes() -> bytes:
    return (canonical_json({
        "authority": "NONE",
        "contract": _MARKER_CONTRACT,
        "schema_version": _MARKER_VERSION,
        "selector_era": _SELECTOR_ERA,
    }) + "\n").encode("utf-8")


def _read_marker(paths: SelectorPaths) -> None:
    if not paths.marker_path.is_file() or paths.marker_path.is_symlink():
        raise DeploymentAuthorityError("selector-era marker is missing")
    try:
        raw = paths.marker_path.read_bytes()
        parsed = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeploymentAuthorityError("selector-era marker is malformed") from exc
    expected = _marker_bytes()
    if raw != expected or not isinstance(parsed, dict):
        raise DeploymentAuthorityError("selector-era marker is incompatible")


def _open_selector(
    path: Path, *, writable: bool, create: bool = False
) -> sqlite3.Connection:
    if path.is_symlink():
        raise DeploymentAuthorityError("selector path must not be a symlink")
    try:
        if create:
            connection = sqlite3.connect(str(path), isolation_level=None, check_same_thread=True)
        elif writable:
            connection = sqlite3.connect(
                f"{path.resolve().as_uri()}?mode=rw",
                uri=True,
                isolation_level=None,
                check_same_thread=True,
            )
        else:
            connection = sqlite3.connect(
                f"{path.resolve().as_uri()}?mode=ro",
                uri=True,
                isolation_level=None,
                check_same_thread=True,
            )
    except sqlite3.Error as exc:
        raise DeploymentAuthorityError("selector database cannot be opened") from exc
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        if writable or create:
            connection.execute("PRAGMA synchronous = FULL")
            if connection.execute("PRAGMA synchronous").fetchone()[0] < 2:
                raise DeploymentAuthorityError("selector SQLite synchronous mode is inadequate")
            mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
            if mode != "wal":
                raise DeploymentAuthorityError("selector SQLite WAL mode is unavailable")
        return connection
    except Exception:
        connection.close()
        raise


def _create_selector_schema(connection: sqlite3.Connection) -> None:
    statements = (
        """CREATE TABLE selector_metadata (
          singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
          contract TEXT NOT NULL,
          schema_version INTEGER NOT NULL,
          selector_era TEXT NOT NULL,
          created_at_ns INTEGER NOT NULL
        ) STRICT""",
        """CREATE TABLE selector_state (
          singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
          generation INTEGER NOT NULL,
          deployment_state TEXT NOT NULL,
          core_id TEXT,
          core_relative_path TEXT,
          descriptor_digest TEXT,
          profile_digest TEXT,
          core_witness_digest TEXT,
          updated_at_ns INTEGER NOT NULL
        ) STRICT""",
        """CREATE TABLE selector_ledger (
          generation INTEGER PRIMARY KEY,
          previous_generation INTEGER,
          previous_deployment_state TEXT,
          previous_core_id TEXT,
          previous_core_relative_path TEXT,
          previous_descriptor_digest TEXT,
          previous_profile_digest TEXT,
          previous_core_witness_digest TEXT,
          new_generation INTEGER NOT NULL,
          new_deployment_state TEXT NOT NULL,
          new_core_id TEXT,
          new_core_relative_path TEXT,
          new_descriptor_digest TEXT,
          new_profile_digest TEXT,
          new_core_witness_digest TEXT,
          operation_key TEXT NOT NULL UNIQUE,
          canonical_intent TEXT NOT NULL,
          reason_kind TEXT NOT NULL,
          recorded_at_ns INTEGER NOT NULL
        ) STRICT""",
    )
    for statement in statements:
        connection.execute(statement)
    connection.execute(
        "INSERT INTO selector_metadata VALUES (1,?,?,?,?)",
        (_SELECTOR_CONTRACT, _SELECTOR_VERSION, _SELECTOR_ERA, time.time_ns()),
    )


def _validated_selector(connection: sqlite3.Connection) -> tuple[SelectorState, list[dict[str, Any]]]:
    try:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        if names != {"selector_metadata", "selector_state", "selector_ledger"}:
            raise ValueError("schema table set")
        for table, expected_columns in _SELECTOR_COLUMNS.items():
            columns = tuple(
                (str(row[1]), str(row[2]).upper(), int(row[5]))
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            )
            if columns != expected_columns:
                raise ValueError("schema columns")
        table_list = {
            str(row[1]): int(row[5])
            for row in connection.execute("PRAGMA table_list").fetchall()
            if str(row[1]) in _SELECTOR_COLUMNS
        }
        if table_list != {name: 1 for name in _SELECTOR_COLUMNS}:
            raise ValueError("selector tables must remain STRICT")
        metadata_rows = connection.execute(
            "SELECT contract,schema_version,selector_era FROM selector_metadata"
        ).fetchall()
        if metadata_rows != [(_SELECTOR_CONTRACT, _SELECTOR_VERSION, _SELECTOR_ERA)]:
            raise ValueError("metadata singleton")
        state_rows = connection.execute(
            "SELECT generation,deployment_state,core_id,core_relative_path,descriptor_digest,"
            "profile_digest,core_witness_digest,updated_at_ns FROM selector_state"
        ).fetchall()
        if len(state_rows) != 1:
            raise ValueError("state singleton")
        state = _state_from_values(state_rows[0])
        rows = connection.execute(
            "SELECT generation,previous_generation,previous_deployment_state,previous_core_id,"
            "previous_core_relative_path,previous_descriptor_digest,previous_profile_digest,"
            "previous_core_witness_digest,new_generation,new_deployment_state,new_core_id,"
            "new_core_relative_path,new_descriptor_digest,new_profile_digest,new_core_witness_digest,"
            "operation_key,canonical_intent,reason_kind,recorded_at_ns "
            "FROM selector_ledger ORDER BY generation"
        ).fetchall()
        if not rows:
            raise ValueError("missing ledger")
        ledger = [_ledger_row(row) for row in rows]
        _validate_ledger(state, ledger)
        return state, ledger
    except (sqlite3.Error, TypeError, ValueError, KeyError, DeploymentAuthorityError) as exc:
        raise DeploymentAuthorityError("selector database is malformed or incompatible") from exc


def _validate_ledger(state: SelectorState, ledger: list[dict[str, Any]]) -> None:
    previous: SelectorState | None = None
    keys: set[str] = set()
    for expected_generation, record in enumerate(ledger):
        result = _state_from_ledger(record, prefix="new")
        if record["generation"] != expected_generation or result.generation != expected_generation:
            raise DeploymentAuthorityError("selector ledger generations are not contiguous")
        if record["operation_key"] in keys:
            raise DeploymentAuthorityError("selector ledger operation key is duplicated")
        keys.add(record["operation_key"])
        intent = record["intent"]
        if canonical_json(intent) != record["canonical_intent"]:
            raise DeploymentAuthorityError("selector ledger intent is non-canonical")
        if previous is None:
            if any(record[name] is not None for name in _PREVIOUS_COLUMNS):
                raise DeploymentAuthorityError("selector genesis ledger has a predecessor")
        else:
            recorded_previous = _state_from_ledger(record, prefix="previous")
            if (
                not _same_authority_state(recorded_previous, previous)
                or record["previous_generation"] != previous.generation
            ):
                raise DeploymentAuthorityError("selector ledger predecessor disagrees")
            if result.generation != previous.generation + 1:
                raise DeploymentAuthorityError("selector ledger is not monotonic")
        previous = result
    if previous != state:
        raise DeploymentAuthorityError("selector singleton disagrees with immutable ledger")


_PREVIOUS_COLUMNS = (
    "previous_generation",
    "previous_deployment_state",
    "previous_core_id",
    "previous_core_relative_path",
    "previous_descriptor_digest",
    "previous_profile_digest",
    "previous_core_witness_digest",
)


def _same_authority_state(left: SelectorState, right: SelectorState) -> bool:
    """Compare durable state fields excluding a prior state's unrecorded clock."""

    return _state_values(left)[:-1] == _state_values(right)[:-1]


def _ledger_row(row: tuple[Any, ...]) -> dict[str, Any]:
    try:
        intent = json.loads(row[16])
        if not isinstance(intent, dict):
            raise ValueError("intent type")
        if not isinstance(row[15], str) or not row[15] or not isinstance(row[17], str) or not row[17]:
            raise ValueError("ledger text")
        if not isinstance(row[18], int) or row[18] < 0:
            raise ValueError("ledger timestamp")
        return {
            "generation": row[0],
            "previous_generation": row[1],
            "previous_deployment_state": row[2],
            "previous_core_id": row[3],
            "previous_core_relative_path": row[4],
            "previous_descriptor_digest": row[5],
            "previous_profile_digest": row[6],
            "previous_core_witness_digest": row[7],
            "new_generation": row[8],
            "new_deployment_state": row[9],
            "new_core_id": row[10],
            "new_core_relative_path": row[11],
            "new_descriptor_digest": row[12],
            "new_profile_digest": row[13],
            "new_core_witness_digest": row[14],
            "operation_key": row[15],
            "canonical_intent": row[16],
            "intent": intent,
            "reason_kind": row[17],
            "recorded_at_ns": row[18],
        }
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DeploymentAuthorityError("selector ledger row is malformed") from exc


def _state_from_values(row: tuple[Any, ...]) -> SelectorState:
    try:
        return SelectorState(
            generation=row[0],
            deployment_state=DeploymentState(row[1]),
            core_id=None if row[2] is None else UUID(row[2]),
            core_relative_path=row[3],
            descriptor_digest=row[4],
            profile_digest=row[5],
            core_witness_digest=row[6],
            updated_at_ns=row[7],
        )
    except (TypeError, ValueError, DeploymentAuthorityError) as exc:
        raise DeploymentAuthorityError("selector state is malformed") from exc


def _state_from_ledger(record: dict[str, Any], *, prefix: str) -> SelectorState:
    if prefix == "previous":
        return _state_from_values(
            (
                record["previous_generation"],
                record["previous_deployment_state"],
                record["previous_core_id"],
                record["previous_core_relative_path"],
                record["previous_descriptor_digest"],
                record["previous_profile_digest"],
                record["previous_core_witness_digest"],
                record["recorded_at_ns"],
            )
        )
    return _state_from_values(
        (
            record["new_generation"],
            record["new_deployment_state"],
            record["new_core_id"],
            record["new_core_relative_path"],
            record["new_descriptor_digest"],
            record["new_profile_digest"],
            record["new_core_witness_digest"],
            record["recorded_at_ns"],
        )
    )


def _write_state(connection: sqlite3.Connection, state: SelectorState) -> None:
    connection.execute("DELETE FROM selector_state")
    connection.execute(
        "INSERT INTO selector_state VALUES (1,?,?,?,?,?,?,?,?)",
        _state_values(state),
    )


def _append_ledger(
    connection: sqlite3.Connection,
    *,
    previous: SelectorState | None,
    result: SelectorState,
    operation_key: str,
    intent: dict[str, Any],
    reason_kind: str,
) -> None:
    previous_values = (None,) * 7 if previous is None else _state_values(previous)[:-1]
    recorded_at_ns = result.updated_at_ns
    connection.execute(
        "INSERT INTO selector_ledger VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            result.generation,
            *previous_values,
            *_state_values(result)[:-1],
            operation_key,
            canonical_json(intent),
            reason_kind,
            recorded_at_ns,
        ),
    )


def _state_values(state: SelectorState) -> tuple[Any, ...]:
    return (
        state.generation,
        state.deployment_state.value,
        None if state.core_id is None else str(state.core_id),
        state.core_relative_path,
        state.descriptor_digest,
        state.profile_digest,
        state.core_witness_digest,
        state.updated_at_ns,
    )


def _ledger_for_operation(ledger: list[dict[str, Any]], operation_key: str) -> dict[str, Any] | None:
    return next((record for record in ledger if record["operation_key"] == operation_key), None)


def _require_same_intent(record: dict[str, Any], expected: dict[str, Any]) -> None:
    if record["canonical_intent"] != canonical_json(expected):
        raise DeploymentIdempotencyConflict("selector operation key was reused with different intent")


def _data_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DeploymentAuthorityError("deployment data root is required")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise DeploymentAuthorityError("deployment data root must already exist")
    return root


def _prepare_deployment_root(paths: SelectorPaths) -> None:
    """Create only the fixed deployment directory, never through a symlink."""

    substrate_root = paths.deployment_root.parent
    for path in (substrate_root, paths.deployment_root):
        if path.is_symlink():
            raise DeploymentAuthorityError("deployment authority directory must not be a symlink")
        if path.exists() and not path.is_dir():
            raise DeploymentAuthorityError("deployment authority location is not a directory")
    paths.deployment_root.mkdir(parents=True, exist_ok=True)
    if paths.deployment_root.is_symlink() or not paths.deployment_root.is_dir():
        raise DeploymentAuthorityError("deployment authority directory is invalid")


def _atomic_create(target: Path, content: bytes) -> None:
    temporary = target.parent / f".{target.name}.{uuid4().hex}.tmp"
    try:
        with open(temporary, "xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            # A simultaneous exact writer is an idempotent success only if its
            # contents are the frozen marker.  _read_marker performs that test.
            pass
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _fsync_file(path: Path) -> None:
    # Windows rejects FlushFileBuffers on a read-only descriptor.
    with open(path, "r+b") as handle:
        os.fsync(handle.fileno())


def _require_operation_key(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise DeploymentAuthorityError("selector operation_key must be bounded non-empty text")
    return value


def _require_generation(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise DeploymentAuthorityError("selector expected_generation must be non-negative")
    return value


__all__ = [
    "SelectorPaths",
    "abort_selector_pending",
    "activate_selector_native",
    "begin_cutover_pending",
    "establish_selector_era",
    "initialize_selector",
    "read_selector_state",
    "resolve_deployment_agreement",
    "selector_paths",
]
