"""Read-only, redacted operator evidence for the B5 deployment boundary.

This module consumes the durable selector/core resolver and the existing
admission descriptor reader.  It deliberately has no transition, repair, or
runtime-construction API.  Its JSON projection contains only stable,
operator-relevant facts; paths, digests, raw descriptor payloads, caller data,
and credentials never cross this boundary.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

from .deployment_core_maintenance import (
    CoreDeploymentInspection,
    inspect_contained_core_deployment,
)
from .deployment_selector import (
    read_selector_state,
    resolve_deployment_agreement,
    selector_paths,
)
from .deployment_types import (
    DeploymentResolutionMode,
    DeploymentState,
    QualifiedDeploymentProfile,
    SelectorState,
)
from .migration.existing_workspace_multi_scope_admission import (
    ExistingWorkspaceNativeMultiScopeDescriptor,
    load_existing_workspace_multi_scope_admission_descriptor,
)
from .runtime_qualification import RuntimeQualificationResult, inspect_runtime


_SCHEMA = "TORMENT_B5_A6_DEPLOYMENT_DIAGNOSTIC"
_VERSION = 1


@dataclass(frozen=True)
class DeploymentDiagnosticRequest:
    """Host-owned, non-transport inputs to one diagnostic observation."""

    data_root: Path | str
    effective_profile: QualifiedDeploymentProfile | None = None
    admission_descriptor_path: Path | str | None = None

    def __post_init__(self) -> None:
        root = Path(self.data_root).expanduser().resolve()
        if self.effective_profile is not None and not isinstance(
            self.effective_profile, QualifiedDeploymentProfile,
        ):
            raise ValueError("effective_profile must be a QualifiedDeploymentProfile or None")
        if self.admission_descriptor_path is not None and not isinstance(
            self.admission_descriptor_path, (str, Path),
        ):
            raise ValueError("admission_descriptor_path must be a path or None")
        object.__setattr__(self, "data_root", root)


@dataclass(frozen=True)
class DeploymentDiagnostic:
    """Stable redacted output for a single deployment observation."""

    schema: str
    version: int
    deployment_mode: str
    selector_generation: int | None
    selector_state: str | None
    selected_core_id: str | None
    core_id: str | None
    core_role: str | None
    core_deployment_state: str | None
    sqlite_runtime_version: str
    runtime_admissible: bool
    profile_qualified: bool | None
    admission_state: str | None
    admission_identity_matches: bool | None
    completion_witness_valid: bool | None
    public_backend_mode: str
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        """Return the intentionally bounded public projection.

        Keep this explicit rather than using ``asdict`` so a future internal
        field cannot accidentally broaden the CLI output contract.
        """

        return {
            "schema": self.schema,
            "version": self.version,
            "deployment_mode": self.deployment_mode,
            "selector_generation": self.selector_generation,
            "selector_state": self.selector_state,
            "selected_core_id": self.selected_core_id,
            "core_id": self.core_id,
            "core_role": self.core_role,
            "core_deployment_state": self.core_deployment_state,
            "sqlite_runtime_version": self.sqlite_runtime_version,
            "runtime_admissible": self.runtime_admissible,
            "profile_qualified": self.profile_qualified,
            "admission_state": self.admission_state,
            "admission_identity_matches": self.admission_identity_matches,
            "completion_witness_valid": self.completion_witness_valid,
            "public_backend_mode": self.public_backend_mode,
            "reason_code": self.reason_code,
        }


def inspect_deployment_diagnostic(request: DeploymentDiagnosticRequest) -> DeploymentDiagnostic:
    """Observe B5 authority without opening a writable deployment resource."""

    root = Path(request.data_root)
    runtime = inspect_runtime()
    profile = request.effective_profile or _observation_profile()
    resolution = resolve_deployment_agreement(
        data_root=root,
        effective_profile=profile,
    )
    state, selector_issue = _read_selector_state(root)
    inspection, core_inspection_failed = _read_core_inspection(root, state)
    descriptor, descriptor_invalid = _read_descriptor(request.admission_descriptor_path)

    admission_state = None if descriptor is None else descriptor.state.value
    identity_matches = _identity_matches(descriptor, state)
    completion_valid = _completion_witness_valid(descriptor)

    mode = resolution.mode
    reason = resolution.reason

    # These are explanations of read-only facts, not new authority rules.  A
    # resolver disposition remains the sole source for ordinary deployment
    # state; the descriptor checks below only state whether native public
    # construction has the already-required host proof material.
    if selector_issue is not None:
        mode = DeploymentResolutionMode.REFUSED
        reason = selector_issue
    elif state is not None and core_inspection_failed:
        mode = DeploymentResolutionMode.REFUSED
        reason = "selected-core-unavailable"
    elif state is not None and inspection is not None and state.core_id is not None:
        if inspection.core_id != state.core_id:
            mode = DeploymentResolutionMode.REFUSED
            reason = "selected-core-uuid-mismatch"
        elif (
            state.deployment_state is DeploymentState.NATIVE_ACTIVE
            and (
                inspection.core_role != "ACTIVE_CORE"
                or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            )
        ):
            mode = DeploymentResolutionMode.REFUSED
            reason = "native-selector-core-is-not-active"
        elif (
            state.deployment_state is DeploymentState.CUTOVER_PENDING
            and inspection.core_role == "ACTIVE_CORE"
            and inspection.deployment_state is DeploymentState.NATIVE_ACTIVE
        ):
            # This intentionally remains MAINTENANCE_ONLY: only the external
            # selector may make native public authority active.
            mode = DeploymentResolutionMode.MAINTENANCE_ONLY
            reason = "core-active-external-pending"

    if mode is DeploymentResolutionMode.NATIVE_AGREEMENT:
        if request.effective_profile is None:
            mode = DeploymentResolutionMode.REFUSED
            reason = "host-profile-configuration-required"
        elif descriptor is None:
            mode = DeploymentResolutionMode.REFUSED
            reason = (
                "admission-descriptor-invalid"
                if descriptor_invalid
                else "admission-descriptor-configuration-required"
            )
        elif identity_matches is not True:
            mode = DeploymentResolutionMode.REFUSED
            reason = "admission-identity-does-not-match-selector"
        elif completion_valid is not True:
            mode = DeploymentResolutionMode.REFUSED
            reason = "admission-completion-witness-invalid"
        elif not runtime.runtime_admissible:
            mode = DeploymentResolutionMode.REFUSED
            reason = "actual-sqlite-runtime-is-not-qualified"

    backend = {
        DeploymentResolutionMode.LEGACY_PUBLIC: "LEGACY",
        DeploymentResolutionMode.NATIVE_AGREEMENT: "NATIVE",
    }.get(mode, "REFUSED")
    selected_core_id = None if state is None or state.core_id is None else str(state.core_id)
    core_id = None if inspection is None else str(inspection.core_id)
    return DeploymentDiagnostic(
        schema=_SCHEMA,
        version=_VERSION,
        deployment_mode=mode.value,
        selector_generation=None if state is None else state.generation,
        selector_state=None if state is None else state.deployment_state.value,
        selected_core_id=selected_core_id,
        core_id=core_id,
        core_role=None if inspection is None else inspection.core_role,
        core_deployment_state=(
            None if inspection is None else inspection.deployment_state.value
        ),
        sqlite_runtime_version=runtime.sqlite_runtime_version,
        runtime_admissible=runtime.runtime_admissible,
        profile_qualified=(
            None if request.effective_profile is None
            else request.effective_profile.is_qualified
        ),
        admission_state=admission_state,
        admission_identity_matches=identity_matches,
        completion_witness_valid=completion_valid,
        public_backend_mode=backend,
        reason_code=reason,
    )


def _read_selector_state(root: Path) -> tuple[SelectorState | None, str | None]:
    paths = selector_paths(root)
    marker_exists = paths.marker_path.exists() or paths.marker_path.is_symlink()
    selector_exists = paths.selector_path.exists() or paths.selector_path.is_symlink()
    if not marker_exists and not selector_exists:
        return None, None
    if marker_exists != selector_exists:
        return None, "selector-era-marker-and-selector-must-coexist"
    try:
        return read_selector_state(data_root=root), None
    except Exception:
        return None, "selector-invalid"


def _read_core_inspection(
    root: Path,
    state: SelectorState | None,
) -> tuple[CoreDeploymentInspection | None, bool]:
    if state is not None and state.core_relative_path is not None:
        try:
            return inspect_contained_core_deployment(
                data_root=root,
                core_relative_path=state.core_relative_path,
            ), False
        except Exception:
            return None, True

    # P1 has a real, inert core but no selector yet.  Show that one bounded
    # single-core observation without inventing a selection decision.
    paths = selector_paths(root)
    try:
        if paths.core_root.is_symlink() or not paths.core_root.is_dir():
            return None, False
        candidates = [
            item for item in paths.core_root.iterdir()
            if item.suffix.lower() == ".db" and item.is_file() and not item.is_symlink()
        ]
        if len(candidates) != 1:
            return None, False
        return inspect_contained_core_deployment(
            data_root=root,
            core_relative_path=candidates[0].name,
        ), False
    except Exception:
        return None, False


def _read_descriptor(
    path: Path | str | None,
) -> tuple[ExistingWorkspaceNativeMultiScopeDescriptor | None, bool]:
    if path is None:
        return None, False
    try:
        return load_existing_workspace_multi_scope_admission_descriptor(path), False
    except Exception:
        return None, True


def _identity_matches(
    descriptor: ExistingWorkspaceNativeMultiScopeDescriptor | None,
    state: SelectorState | None,
) -> bool | None:
    if descriptor is None or state is None or state.core_id is None:
        return None
    identity = descriptor.admission_identity_digest
    if identity is None:
        return False
    return identity == state.descriptor_digest and descriptor.native_core_id == state.core_id


def _completion_witness_valid(
    descriptor: ExistingWorkspaceNativeMultiScopeDescriptor | None,
) -> bool | None:
    if descriptor is None:
        return None
    try:
        descriptor.completed_admission_witness()
        return True
    except Exception:
        return False


def _observation_profile() -> QualifiedDeploymentProfile:
    # This valid but deliberately non-matching profile lets the frozen
    # resolver observe legacy/pending authority even before host proof facts
    # are supplied.  It cannot qualify a native startup.
    digest = "0" * 64
    return QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider="diagnostic-observer",
        representation_model="diagnostic-observer-v1",
        representation_dimension=1,
        admitted_scope_plan_digest=digest,
        external_owner_digest=digest,
    )


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only TORMENT deployment diagnostic")
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args(argv)
    try:
        # Import lazily: the operator CLI uses precisely the same optional
        # host proof parser as REST and MCP, while a legacy root needs none.
        from torment_service.public_runtime import (
            load_public_runtime_configuration_from_host_environment,
        )

        configuration = load_public_runtime_configuration_from_host_environment()
        request = DeploymentDiagnosticRequest(
            data_root=args.data_root,
            effective_profile=(
                None if configuration is None else configuration.effective_profile
            ),
            admission_descriptor_path=(
                None if configuration is None else configuration.admission_descriptor_path
            ),
        )
        print(json.dumps(inspect_deployment_diagnostic(request).to_dict(), sort_keys=True))
        return 0
    except Exception:
        # Do not echo a descriptor path, profile payload, or raw diagnostic
        # input in an operator-facing error channel.
        print("deployment diagnostic configuration refused", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "DeploymentDiagnostic",
    "DeploymentDiagnosticRequest",
    "inspect_deployment_diagnostic",
]
