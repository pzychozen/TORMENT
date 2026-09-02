"""Dedicated B5-A2 maintenance transitions for one contained native core.

The functions here are administration-only.  They use the existing core
metadata and CUTOVER maintenance evidence; they do not widen ordinary STAGING
writers or construct a public native capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import time
from typing import Any
from uuid import UUID

from .connection import open_existing_native_core_connection
from .deployment_types import (
    AdmissionCompletionWitness,
    CoreDeploymentWitness,
    DeploymentState,
    canonical_json,
    require_digest,
    require_relative_core_path,
)
from .errors import DeploymentAuthorityError, DeploymentIdempotencyConflict
from .ids import generate_native_id, native_id_from_bytes, native_id_to_bytes
from .schema import SCHEMA_ID, SCHEMA_MAJOR, SCHEMA_MINOR, require_current_schema


_CONTRACT = "TORMENT_B5_A2_CORE_MAINTENANCE_V1"
_ENTER_PENDING = "ENTER_CUTOVER_PENDING"
_ACTIVATE = "ACTIVATE_CORE"
_ABORT_PENDING = "ABORT_CUTOVER_PENDING"
_EVENT_KINDS = frozenset({_ENTER_PENDING, _ACTIVATE, _ABORT_PENDING})


@dataclass(frozen=True)
class CoreDeploymentInspection:
    """Read-only contained-core facts used by selector and maintenance callers."""

    core_id: UUID
    core_role: str
    deployment_state: DeploymentState
    witness: CoreDeploymentWitness | None
    latest_maintenance_id: UUID | None
    ever_active: bool
    activation_completion_witness: AdmissionCompletionWitness | None = None


@dataclass(frozen=True)
class CoreMaintenanceResult:
    """Committed core-side transition receipt; it grants no writer capability."""

    transition_kind: str
    maintenance_id: UUID
    witness: CoreDeploymentWitness
    selector_generation: int
    selector_witness_digest: str
    safe_abort_proven: bool = False
    completion_witness: AdmissionCompletionWitness | None = None


def inspect_contained_core_deployment(
    *,
    data_root: str | Path,
    core_relative_path: str,
) -> CoreDeploymentInspection:
    """Read one controlled core path without creating it or changing it."""

    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    # The resolver calls this function at startup.  It must not establish WAL,
    # create sidecars, or otherwise change a core merely to inspect authority
    # facts, so it deliberately does not reuse the rw maintenance boundary.
    connection = _open_readonly_core(path)
    try:
        return _inspect_connection(connection)
    finally:
        connection.close()


def contained_core_path(
    *,
    data_root: str | Path,
    core_relative_path: str,
    require_exists: bool,
) -> Path:
    """Resolve one selector-owned filename beneath data_root/substrate/cores."""

    name = require_relative_core_path(core_relative_path)
    root = _data_root(data_root)
    expected_root = root / "substrate" / "cores"
    if expected_root.is_symlink():
        raise DeploymentAuthorityError("contained core root must not be a symlink")
    if not expected_root.is_dir():
        if require_exists:
            raise DeploymentAuthorityError("contained core root is missing")
        return expected_root / name
    core_root = expected_root.resolve()
    if not _is_relative_to(core_root, root):
        raise DeploymentAuthorityError("contained core root escapes the data root")
    unresolved_path = expected_root / name
    if unresolved_path.is_symlink():
        raise DeploymentAuthorityError("selected contained core must not be a symlink")
    path = unresolved_path.resolve()
    if not _is_relative_to(path, core_root):
        raise DeploymentAuthorityError("selector core path escapes the contained core root")
    if require_exists and (not path.is_file() or path.suffix.lower() != ".db"):
        raise DeploymentAuthorityError("selected contained core is missing")
    return path


def staging_legacy_witness(
    inspection: CoreDeploymentInspection,
    *,
    descriptor_digest: str,
    profile_digest: str,
) -> CoreDeploymentWitness:
    """Bind supplied admission/profile evidence to an inert STAGING core."""

    require_digest(descriptor_digest, "descriptor_digest")
    require_digest(profile_digest, "profile_digest")
    if (
        inspection.core_role != "STAGING"
        or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE
    ):
        raise DeploymentAuthorityError("initial selector witness requires STAGING/LEGACY_ACTIVE core")
    return CoreDeploymentWitness(
        core_id=inspection.core_id,
        schema_id=SCHEMA_ID,
        schema_major=SCHEMA_MAJOR,
        schema_minor=SCHEMA_MINOR,
        core_role="STAGING",
        deployment_state=DeploymentState.LEGACY_ACTIVE,
        descriptor_digest=descriptor_digest,
        profile_digest=profile_digest,
    )


def enter_cutover_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
) -> CoreMaintenanceResult:
    """Transition STAGING/LEGACY_ACTIVE to STAGING/CUTOVER_PENDING once."""

    if expected_witness.deployment_state is not DeploymentState.LEGACY_ACTIVE:
        raise DeploymentAuthorityError("pending maintenance requires LEGACY_ACTIVE predecessor witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ENTER_PENDING,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
    )


def activate_core(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: AdmissionCompletionWitness | None = None,
) -> CoreMaintenanceResult:
    """Transition STAGING/CUTOVER_PENDING to ACTIVE_CORE/NATIVE_ACTIVE once."""

    if expected_witness.deployment_state is not DeploymentState.CUTOVER_PENDING:
        raise DeploymentAuthorityError("activation maintenance requires CUTOVER_PENDING predecessor witness")
    if completion_witness is None:
        raise DeploymentAuthorityError("activation requires a completed admission witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ACTIVATE,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
        completion_witness=completion_witness,
    )


def abort_cutover_pending(
    *,
    data_root: str | Path,
    core_relative_path: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
) -> CoreMaintenanceResult:
    """Safely return a never-active pending core to STAGING/LEGACY_ACTIVE."""

    if expected_witness.deployment_state is not DeploymentState.CUTOVER_PENDING:
        raise DeploymentAuthorityError("pending abort requires CUTOVER_PENDING predecessor witness")
    return _transition(
        data_root=data_root,
        core_relative_path=core_relative_path,
        transition_kind=_ABORT_PENDING,
        expected_witness=expected_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        operation_key=operation_key,
    )


def _transition(
    *,
    data_root: str | Path,
    core_relative_path: str,
    transition_kind: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: AdmissionCompletionWitness | None = None,
) -> CoreMaintenanceResult:
    path = contained_core_path(
        data_root=data_root, core_relative_path=core_relative_path, require_exists=True
    )
    _require_operation_key(operation_key)
    _require_selector_facts(selector_generation, selector_witness_digest)
    if completion_witness is not None:
        if transition_kind != _ACTIVATE:
            raise DeploymentAuthorityError("completion witness is valid only for core activation")
        if (
            completion_witness.admission_identity_digest != expected_witness.descriptor_digest
            or completion_witness.native_core_id != expected_witness.core_id
        ):
            raise DeploymentAuthorityError("completion witness does not match the selected admission identity")
        if completion_witness.profile_digest is None:
            raise DeploymentAuthorityError("activation requires a completion witness bound to the selected profile")
        if completion_witness.profile_digest != expected_witness.profile_digest:
            raise DeploymentAuthorityError("completion witness does not match the selected deployment profile")
    with open_existing_native_core_connection(path) as opened:
        connection = opened.connection
        before = _inspect_connection(connection)
        if before.core_id != expected_witness.core_id:
            raise DeploymentAuthorityError("core maintenance witness names another core")
        intent = _intent(
            transition_kind=transition_kind,
            expected_witness=expected_witness,
            selector_generation=selector_generation,
            selector_witness_digest=selector_witness_digest,
            operation_key=operation_key,
            completion_witness=completion_witness,
        )
        existing = _event_for_operation(connection, operation_key)
        if existing is not None:
            return _recover_existing_transition(
                inspection=before,
                event=existing,
                expected_intent=intent,
            )
        _require_predecessor(before, expected_witness, transition_kind)
        if transition_kind == _ABORT_PENDING and before.ever_active:
            raise DeploymentAuthorityError("post-native reverse transition is refused")

        result_witness = _result_witness(expected_witness, transition_kind)
        maintenance_id = generate_native_id()
        now_ns = time.time_ns()
        detail = _event_detail(
            transition_kind=transition_kind,
            maintenance_id=maintenance_id,
            intent=intent,
            previous=expected_witness,
            result=result_witness,
            selector_generation=selector_generation,
            selector_witness_digest=selector_witness_digest,
            recorded_at_ns=now_ns,
            completion_witness=completion_witness,
        )
        connection.execute("BEGIN IMMEDIATE")
        try:
            _write_core_state(connection, result_witness)
            connection.execute(
                "INSERT INTO maintenance_events VALUES (?, 'CUTOVER', ?, ?, ?)",
                (
                    native_id_to_bytes(maintenance_id),
                    now_ns,
                    now_ns,
                    canonical_json(detail),
                ),
            )
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
    return CoreMaintenanceResult(
        transition_kind=transition_kind,
        maintenance_id=maintenance_id,
        witness=result_witness,
        selector_generation=selector_generation,
        selector_witness_digest=selector_witness_digest,
        safe_abort_proven=transition_kind == _ABORT_PENDING,
        completion_witness=completion_witness,
    )


def _inspect_connection(connection: sqlite3.Connection) -> CoreDeploymentInspection:
    metadata = require_current_schema(connection)
    core_id = native_id_from_bytes(metadata.core_id)
    rows = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if len(rows) != 1:
        raise DeploymentAuthorityError("core deployment metadata is not singleton")
    try:
        deployment_state = DeploymentState(rows[0][0])
    except (TypeError, ValueError) as exc:
        raise DeploymentAuthorityError("core deployment state is invalid") from exc
    referenced = rows[0][1]
    valid_pairs = {
        ("STAGING", DeploymentState.LEGACY_ACTIVE, None),
        ("STAGING", DeploymentState.CUTOVER_PENDING, native_id_to_bytes(core_id)),
        ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE, native_id_to_bytes(core_id)),
    }
    if (metadata.core_role, deployment_state, referenced) not in valid_pairs:
        raise DeploymentAuthorityError("core role/deployment metadata is incompatible")

    events = _core_events(connection, core_id)
    latest = events[-1] if events else None
    if latest is None:
        return CoreDeploymentInspection(
            core_id=core_id,
            core_role=metadata.core_role,
            deployment_state=deployment_state,
            witness=None,
            latest_maintenance_id=None,
            ever_active=False,
        )
    expected_chain = ("STAGING", DeploymentState.LEGACY_ACTIVE)
    ever_active = False
    for event in events:
        previous = event["previous"]
        result = event["result"]
        if (
            previous["core_role"],
            DeploymentState(previous["deployment_state"]),
        ) != expected_chain:
            raise DeploymentAuthorityError("core maintenance evidence predecessor chain is inconsistent")
        kind = event["transition_kind"]
        expected_result = {
            _ENTER_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
            _ACTIVATE: ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE),
            _ABORT_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
        }[kind]
        if (
            result["core_role"],
            DeploymentState(result["deployment_state"]),
        ) != expected_result:
            raise DeploymentAuthorityError("core maintenance evidence transition is invalid")
        expected_chain = expected_result
        ever_active = ever_active or kind == _ACTIVATE
    if (metadata.core_role, deployment_state) != expected_chain:
        raise DeploymentAuthorityError("core metadata disagrees with immutable maintenance evidence")
    witness = _witness_from_event_result(latest["result"])
    activation_completion = next(
        (item.get("completion_witness") for item in reversed(events)
         if item["transition_kind"] == _ACTIVATE),
        None,
    )
    return CoreDeploymentInspection(
        core_id=core_id,
        core_role=metadata.core_role,
        deployment_state=deployment_state,
        witness=witness,
        latest_maintenance_id=latest["maintenance_id"],
        ever_active=ever_active,
        activation_completion_witness=activation_completion,
    )


def _core_events(connection: sqlite3.Connection, core_id: UUID) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT maintenance_id,completed_at_ns,detail_json FROM maintenance_events "
        "WHERE maintenance_kind='CUTOVER' ORDER BY completed_at_ns,maintenance_id"
    ).fetchall()
    events: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for maintenance_id_raw, _completed_at_ns, detail_raw in rows:
        try:
            detail = json.loads(detail_raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise DeploymentAuthorityError("core CUTOVER evidence is malformed") from exc
        if not isinstance(detail, dict) or detail.get("contract") != _CONTRACT:
            continue
        if canonical_json(detail) != detail_raw:
            raise DeploymentAuthorityError("core maintenance evidence is non-canonical")
        try:
            maintenance_id = native_id_from_bytes(maintenance_id_raw)
            kind = detail["transition_kind"]
            key = detail["operation_key"]
            intent = detail["canonical_intent"]
            previous = detail["previous"]
            result = detail["result"]
            completion = _completion_witness_from_payload(detail.get("completion_witness"))
            if (
                kind not in _EVENT_KINDS
                or not isinstance(key, str)
                or not key
                or not isinstance(intent, dict)
                or not isinstance(previous, dict)
                or not isinstance(result, dict)
                or detail["maintenance_id"] != str(maintenance_id)
                or detail["core_id"] != str(core_id)
                or (kind != _ACTIVATE and completion is not None)
            ):
                raise ValueError("invalid event shape")
            if key in seen_keys:
                raise ValueError("duplicate operation key")
            seen_keys.add(key)
            _witness_from_event_result(previous)
            _witness_from_event_result(result)
            if (
                UUID(previous["core_id"]) != core_id
                or UUID(result["core_id"]) != core_id
            ):
                raise ValueError("event witness names another core")
            if detail["selector_generation"] < 0:
                raise ValueError("invalid selector generation")
            require_digest(detail["selector_witness_digest"], "selector_witness_digest")
            if ("completion_witness" in detail) != ("completion_witness" in intent):
                raise ValueError("event completion witness is not intent-bound")
            expected_intent = _intent(
                transition_kind=kind,
                expected_witness=_witness_from_event_result(previous),
                selector_generation=detail["selector_generation"],
                selector_witness_digest=detail["selector_witness_digest"],
                operation_key=key,
                completion_witness=completion,
            )
            # Read old B5-A2 records exactly as written.  New records bind the
            # optional completion witness in both detail and canonical intent.
            if "completion_witness" not in intent:
                expected_intent.pop("completion_witness")
            if intent != expected_intent:
                raise ValueError("event intent does not bind its transition evidence")
        except (KeyError, TypeError, ValueError, DeploymentAuthorityError) as exc:
            raise DeploymentAuthorityError("core maintenance evidence is incompatible") from exc
        events.append({**detail, "maintenance_id": maintenance_id, "completion_witness": completion})
    return events


def _event_for_operation(connection: sqlite3.Connection, operation_key: str) -> dict[str, Any] | None:
    rows = connection.execute(
        "SELECT maintenance_id,detail_json FROM maintenance_events WHERE maintenance_kind='CUTOVER'"
    ).fetchall()
    matches: list[dict[str, Any]] = []
    for maintenance_id_raw, detail_raw in rows:
        try:
            detail = json.loads(detail_raw)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(detail, dict) and detail.get("contract") == _CONTRACT and detail.get("operation_key") == operation_key:
            detail = dict(detail)
            detail["maintenance_id"] = native_id_from_bytes(maintenance_id_raw)
            matches.append(detail)
    if len(matches) > 1:
        raise DeploymentAuthorityError("core maintenance operation key is not unique")
    return matches[0] if matches else None


def _recover_existing_transition(
    *,
    inspection: CoreDeploymentInspection,
    event: dict[str, Any],
    expected_intent: dict[str, Any],
) -> CoreMaintenanceResult:
    if canonical_json(event.get("canonical_intent", {})) != canonical_json(expected_intent):
        raise DeploymentIdempotencyConflict("core maintenance operation key was reused with different intent")
    witness = _witness_from_event_result(event["result"])
    # A later, separately authorized maintenance event may have advanced the
    # core after this caller lost its response.  The inspected evidence chain
    # has already proved that the historic event remains genuine, so return its
    # immutable receipt rather than allocating a second transition.
    del inspection
    return CoreMaintenanceResult(
        transition_kind=event["transition_kind"],
        maintenance_id=event["maintenance_id"],
        witness=witness,
        selector_generation=event["selector_generation"],
        selector_witness_digest=event["selector_witness_digest"],
        safe_abort_proven=event["transition_kind"] == _ABORT_PENDING,
        completion_witness=_completion_witness_from_payload(event.get("completion_witness")),
    )


def _require_predecessor(
    inspection: CoreDeploymentInspection,
    expected_witness: CoreDeploymentWitness,
    transition_kind: str,
) -> None:
    if inspection.witness is None:
        actual = staging_legacy_witness(
            inspection,
            descriptor_digest=expected_witness.descriptor_digest,
            profile_digest=expected_witness.profile_digest,
        )
    else:
        actual = inspection.witness
    if actual != expected_witness:
        raise DeploymentAuthorityError("core maintenance predecessor witness mismatch")
    required = {
        _ENTER_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
        _ACTIVATE: ("STAGING", DeploymentState.CUTOVER_PENDING),
        _ABORT_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
    }[transition_kind]
    if (inspection.core_role, inspection.deployment_state) != required:
        raise DeploymentAuthorityError("core maintenance predecessor state is not eligible")


def _result_witness(
    predecessor: CoreDeploymentWitness, transition_kind: str
) -> CoreDeploymentWitness:
    role, state = {
        _ENTER_PENDING: ("STAGING", DeploymentState.CUTOVER_PENDING),
        _ACTIVATE: ("ACTIVE_CORE", DeploymentState.NATIVE_ACTIVE),
        _ABORT_PENDING: ("STAGING", DeploymentState.LEGACY_ACTIVE),
    }[transition_kind]
    return CoreDeploymentWitness(
        core_id=predecessor.core_id,
        schema_id=predecessor.schema_id,
        schema_major=predecessor.schema_major,
        schema_minor=predecessor.schema_minor,
        core_role=role,
        deployment_state=state,
        descriptor_digest=predecessor.descriptor_digest,
        profile_digest=predecessor.profile_digest,
    )


def _write_core_state(connection: sqlite3.Connection, witness: CoreDeploymentWitness) -> None:
    connection.execute(
        "UPDATE core_metadata SET core_role=? WHERE singleton=1",
        (witness.core_role,),
    )
    reference = (
        None
        if witness.deployment_state is DeploymentState.LEGACY_ACTIVE
        else native_id_to_bytes(witness.core_id)
    )
    connection.execute(
        "UPDATE deployment_metadata SET deployment_state=?,referenced_core_id=?,updated_at_ns=? WHERE singleton=1",
        (witness.deployment_state.value, reference, time.time_ns()),
    )


def _intent(
    *,
    transition_kind: str,
    expected_witness: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    operation_key: str,
    completion_witness: AdmissionCompletionWitness | None,
) -> dict[str, Any]:
    return {
        "contract": _CONTRACT,
        "transition_kind": transition_kind,
        "operation_key": operation_key,
        "expected_witness_digest": expected_witness.digest,
        "selector_generation": selector_generation,
        "selector_witness_digest": selector_witness_digest,
        "completion_witness": (
            None if completion_witness is None else completion_witness.payload()
        ),
    }


def _event_detail(
    *,
    transition_kind: str,
    maintenance_id: UUID,
    intent: dict[str, Any],
    previous: CoreDeploymentWitness,
    result: CoreDeploymentWitness,
    selector_generation: int,
    selector_witness_digest: str,
    recorded_at_ns: int,
    completion_witness: AdmissionCompletionWitness | None,
) -> dict[str, Any]:
    return {
        "canonical_intent": intent,
        "completion_witness": (
            None if completion_witness is None else completion_witness.payload()
        ),
        "contract": _CONTRACT,
        "core_id": str(result.core_id),
        "maintenance_id": str(maintenance_id),
        "operation_key": intent["operation_key"],
        "previous": _witness_payload(previous),
        "recorded_at_ns": recorded_at_ns,
        "result": _witness_payload(result),
        "selector_generation": selector_generation,
        "selector_witness_digest": selector_witness_digest,
        "transition_kind": transition_kind,
    }


def _completion_witness_from_payload(value: Any) -> AdmissionCompletionWitness | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DeploymentAuthorityError("core activation completion witness is malformed")
    try:
        return AdmissionCompletionWitness(
            admission_identity_digest=value["admission_identity_digest"],
            completed_descriptor_digest=value["completed_descriptor_digest"],
            completed_progress_digest=value["completed_progress_digest"],
            native_core_id=UUID(value["native_core_id"]),
            workspace_id=value["workspace_id"],
            whole_workspace_closure_digest=value["whole_workspace_closure_digest"],
            profile_digest=value.get("profile_digest"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise DeploymentAuthorityError("core activation completion witness is malformed") from exc


def _witness_payload(witness: CoreDeploymentWitness) -> dict[str, Any]:
    return {
        "core_id": str(witness.core_id),
        "core_role": witness.core_role,
        "deployment_state": witness.deployment_state.value,
        "descriptor_digest": witness.descriptor_digest,
        "profile_digest": witness.profile_digest,
        "schema_id": witness.schema_id,
        "schema_major": witness.schema_major,
        "schema_minor": witness.schema_minor,
    }


def _witness_from_event_result(value: dict[str, Any]) -> CoreDeploymentWitness:
    return CoreDeploymentWitness(
        core_id=UUID(value["core_id"]),
        schema_id=value["schema_id"],
        schema_major=value["schema_major"],
        schema_minor=value["schema_minor"],
        core_role=value["core_role"],
        deployment_state=DeploymentState(value["deployment_state"]),
        descriptor_digest=value["descriptor_digest"],
        profile_digest=value["profile_digest"],
    )


def _data_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DeploymentAuthorityError("deployment data root is required")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise DeploymentAuthorityError("deployment data root must already exist")
    return root


def _open_readonly_core(path: Path) -> sqlite3.Connection:
    """Open a qualified core solely for resolver inspection, with no WAL setup."""

    from .runtime_qualification import qualify_runtime

    qualify_runtime()
    try:
        connection = sqlite3.connect(
            f"{path.as_uri()}?mode=ro",
            uri=True,
            isolation_level=None,
            check_same_thread=True,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        return connection
    except sqlite3.Error as exc:
        raise DeploymentAuthorityError("contained core cannot be opened read-only") from exc


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_operation_key(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise DeploymentAuthorityError("maintenance operation_key must be bounded non-empty text")
    return value


def _require_selector_facts(generation: object, witness_digest: object) -> None:
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise DeploymentAuthorityError("selector_generation must be non-negative")
    require_digest(witness_digest, "selector_witness_digest")


__all__ = [
    "CoreDeploymentInspection",
    "CoreMaintenanceResult",
    "abort_cutover_pending",
    "activate_core",
    "contained_core_path",
    "enter_cutover_pending",
    "inspect_contained_core_deployment",
    "staging_legacy_witness",
]
