from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


PRIMARY_WRITER_IDENTITY = "durable_evidence_primary_writer_v0_3"

DURABLE_ACCEPTED = "DURABLE_ACCEPTED"
BYTE_VALID_DURABILITY_UNCONFIRMED = "BYTE_VALID_DURABILITY_UNCONFIRMED"


class ImmutableWriteError(RuntimeError):
    pass


@dataclass(frozen=True)
class ImmutableWriteResult:
    path: Path
    byte_length: int
    sha256: str
    readback_verified: bool
    durability_status: str
    authoritative_status: str
    directory_durability_failure_code: str | None = None
    directory_durability_policy_identity: dict[str, str] | None = None
    directory_durability_native_error_code: int | None = None
    directory_durability_native_error_name: str | None = None
    directory_durability_target_role: str | None = None


def record_storage_filename(stored_record_object: dict) -> str:
    schema.validate_stored_record_object(stored_record_object)
    logical_record = stored_record_object["logical_record"]
    return "%s.%06d.%s.%s.json" % (
        logical_record["record_kind"].lower(),
        logical_record["sequence_number"],
        stored_record_object["logical_record_sha256"],
        stored_record_object["writer_attempt_identity"],
    )


def bundle_storage_filename(stored_bundle_object: dict) -> str:
    schema.validate_stored_bundle_object(stored_bundle_object)
    return "bundle.000000.%s.%s.json" % (
        stored_bundle_object["bundle_payload_sha256"],
        stored_bundle_object["writer_attempt_identity"],
    )


def write_stored_record_object(
    directory_path: str | Path,
    stored_record_object: dict,
    *,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
    directory_target_role: str = schema.ARTIFACT_PARENT_DIRECTORY,
) -> ImmutableWriteResult:
    schema.validate_stored_record_object(stored_record_object)
    payload = schema.canonical_json_bytes(
        stored_record_object, max_bytes=schema.MAX_STORED_RECORD_OBJECT_BYTES
    )
    destination = Path(directory_path) / record_storage_filename(stored_record_object)
    return _write_immutable_bytes(
        destination,
        payload,
        expected_byte_sha256=schema.sha256_hex(payload),
        durability_adapter=durability_adapter,
        directory_target_role=directory_target_role,
    )


def write_stored_bundle_object(
    directory_path: str | Path,
    stored_bundle_object: dict,
    *,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None = None,
    directory_target_role: str = schema.ARTIFACT_PARENT_DIRECTORY,
) -> ImmutableWriteResult:
    schema.validate_stored_bundle_object(stored_bundle_object)
    payload = schema.canonical_json_bytes(
        stored_bundle_object, max_bytes=schema.MAX_STORED_BUNDLE_OBJECT_BYTES
    )
    destination = Path(directory_path) / bundle_storage_filename(stored_bundle_object)
    return _write_immutable_bytes(
        destination,
        payload,
        expected_byte_sha256=schema.sha256_hex(payload),
        durability_adapter=durability_adapter,
        directory_target_role=directory_target_role,
    )


def _write_immutable_bytes(
    destination: Path,
    payload: bytes,
    *,
    expected_byte_sha256: str,
    durability_adapter: windows_adapter.WindowsDurabilityAdapter | None,
    directory_target_role: str,
) -> ImmutableWriteResult:
    adapter = durability_adapter or windows_adapter.FailClosedWindowsDurabilityAdapter()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(_windows_api_path(destination), "xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise ImmutableWriteError("immutable destination already exists") from exc
    readback = _read_bytes(destination)
    if readback != payload:
        raise ImmutableWriteError("read-back byte verification failed")
    observed_sha256 = schema.sha256_hex(readback)
    if observed_sha256 != expected_byte_sha256:
        raise ImmutableWriteError("read-back SHA-256 verification failed")
    durability = _sync_directory_durability(
        adapter,
        destination.parent,
        directory_target_role,
    )
    policy_match = _directory_policy_identity_matches(
        durability.adapter_policy_identity
    )
    if (
        durability.status == windows_adapter.DIRECTORY_DURABILITY_CONFIRMED
        and policy_match
    ):
        authoritative_status = DURABLE_ACCEPTED
    else:
        authoritative_status = BYTE_VALID_DURABILITY_UNCONFIRMED
    failure_code = durability.failure_code
    if not policy_match:
        failure_code = schema.POLICY_IDENTITY_MISMATCH
    return ImmutableWriteResult(
        path=destination,
        byte_length=len(payload),
        sha256=observed_sha256,
        readback_verified=True,
        durability_status=durability.status,
        authoritative_status=authoritative_status,
        directory_durability_failure_code=failure_code,
        directory_durability_policy_identity=durability.adapter_policy_identity,
        directory_durability_native_error_code=durability.native_error_code,
        directory_durability_native_error_name=durability.native_error_name,
        directory_durability_target_role=durability.target_role,
    )


def _sync_directory_durability(
    adapter: windows_adapter.WindowsDurabilityAdapter,
    directory_path: Path,
    target_role: str,
) -> windows_adapter.DirectoryDurabilityResult:
    context = windows_adapter.DirectoryDurabilityContext(target_role=target_role)
    try:
        return adapter.sync_directory_entry(str(directory_path), context=context)
    except Exception as exc:
        return windows_adapter.DirectoryDurabilityResult(
            status=windows_adapter.DIRECTORY_DURABILITY_INDETERMINATE,
            detail="directory durability adapter exception: %s" % type(exc).__name__,
            failure_code=schema.UNEXPECTED_EXCEPTION,
            platform=None,
            adapter_policy_identity=schema.directory_durability_policy_identity(),
            target_role=target_role,
        )


def _directory_policy_identity_matches(value: object) -> bool:
    try:
        schema.validate_directory_durability_policy_identity(value)
    except schema.DirectoryDurabilityPolicyIdentityMismatchError:
        return False
    return True


def _read_bytes(path: Path) -> bytes:
    with open(_windows_api_path(path), "rb") as handle:
        return handle.read()


def _windows_api_path(path: Path) -> str:
    text = os.path.abspath(str(path))
    if os.name != "nt":
        return text
    prefix = "\\\\?\\"
    unc_prefix = "\\\\?\\UNC\\"
    if text.startswith(prefix):
        return text
    if text.startswith("\\\\"):
        return unc_prefix + text[2:]
    return prefix + text
