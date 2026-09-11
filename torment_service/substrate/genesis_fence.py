"""Read-only I3 projection of the fixed Genesis record; no native authority.

Fresh completion/activation recovery is deliberately not integrated here. A
record can only block legacy startup or conflict at this implementation boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
import stat

from ..external_owner_json import strict_object
from .errors import DeploymentAuthorityError
from .genesis_contracts import (
    GenesisAuthorityDisposition, GenesisEvidenceStatus, GenesisFenceDisposition,
    GenesisFenceFacts, GenesisOperationRecord, classify_genesis_fence,
)

CONTROL_DIRECTORY = Path("substrate/deployment")
RECORD_NAME = "genesis-operation.json"
LOCK_NAME = "root-onboarding.lock"


class GenesisPreparationRefused(DeploymentAuthorityError):
    """Offline preparation or legacy startup cannot safely proceed."""


def checked_stat(path: Path):
    """Inspect without following links, junctions, or other reparse points."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise GenesisPreparationRefused("Genesis paths must not be links or reparse points")
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        raise GenesisPreparationRefused("Genesis path is not a regular file or directory")
    return info


def canonical_genesis_root(data_root: str | Path) -> Path:
    if not isinstance(data_root, (str, Path)) or not str(data_root).strip():
        raise GenesisPreparationRefused("an explicit data root is required")
    candidate = Path(os.path.abspath(Path(data_root).expanduser()))
    for path in (*reversed(candidate.parents), candidate):
        info = checked_stat(path)
        if info is not None and not stat.S_ISDIR(info.st_mode):
            raise GenesisPreparationRefused("data root ancestry must contain directories")
    # normcase gives Windows aliases one identity as well as one OS rendezvous.
    return Path(os.path.normcase(str(candidate.resolve())))


def read_genesis_operation_record(*, data_root: str | Path) -> GenesisOperationRecord | None:
    root = canonical_genesis_root(data_root)
    for path in (root / "substrate", root / CONTROL_DIRECTORY):
        info = checked_stat(path)
        if info is None:
            return None
        if not stat.S_ISDIR(info.st_mode):
            raise GenesisPreparationRefused("Genesis control path is not a directory")
    path = root / CONTROL_DIRECTORY / RECORD_NAME
    info = checked_stat(path)
    if info is None:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise GenesisPreparationRefused("Genesis record is not a regular file")
    try:
        return GenesisOperationRecord.from_payload(strict_object(path.read_bytes()))
    except (OSError, ValueError, TypeError) as exc:
        raise GenesisPreparationRefused("Genesis operation record is malformed") from exc


def read_genesis_fence(*, data_root: str | Path) -> GenesisFenceDisposition:
    """Fail closed on unavailable/malformed evidence, without any writes/SQLite."""
    root_identity = str(data_root)
    record = None
    try:
        # Absence adds no Genesis path policy to historical roots. The existing
        # resolver/Fabric retains its own path validation in that case. Once a
        # record is present, strictly reject redirected ancestry before reading.
        candidate = Path(data_root).expanduser().absolute() / CONTROL_DIRECTORY / RECORD_NAME
        try:
            candidate.lstat()
        except (FileNotFoundError, NotADirectoryError):
            present = False
        else:
            present = True
        if present:
            root_identity = str(canonical_genesis_root(data_root))
            record = read_genesis_operation_record(data_root=data_root)
            if record is None:
                raise GenesisPreparationRefused("Genesis record disappeared during projection")
        status = GenesisEvidenceStatus.ABSENT if record is None else GenesisEvidenceStatus.VALID
    except (OSError, ValueError, TypeError, DeploymentAuthorityError):
        status = GenesisEvidenceStatus.INVALID
    return classify_genesis_fence(GenesisFenceFacts(
        requested_data_root_identity=root_identity,
        record_status=status,
        record_data_root_identity=None if record is None else record.expanded_intent.data_root_identity,
        record_operation_key=None if record is None else record.expanded_intent.operation_key,
        authority_disposition=GenesisAuthorityDisposition.UNPUBLISHED,
        fresh_completion_status=GenesisEvidenceStatus.ABSENT,
        fresh_completion_data_root_identity=None,
        fresh_completion_operation_key=None,
    ))


def require_genesis_allows_legacy_materialization(*, data_root: str | Path) -> None:
    disposition = read_genesis_fence(data_root=data_root)
    if disposition is GenesisFenceDisposition.BLOCK_LEGACY:
        raise GenesisPreparationRefused("native-genesis-preparation-incomplete")
    if disposition is GenesisFenceDisposition.CONFLICT:
        raise GenesisPreparationRefused("native-genesis-evidence-invalid")
