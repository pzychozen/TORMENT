from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import durable_evidence_primary_writer_v0_3 as primary_writer
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


RECORD_OBJECT_CLASS = "stored-record-object-v0.3"
BUNDLE_OBJECT_CLASS = "stored-bundle-object-v0.3"


class DurabilityEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class VerifiedDurabilityEntry:
    object_class: str
    stored_object_sha256: str
    path: str
    byte_length: int
    byte_sha256: str


@dataclass(frozen=True, init=False)
class VerifiedDurabilityEvidence:
    _record_entries: tuple[VerifiedDurabilityEntry, ...]
    _bundle_entries: tuple[VerifiedDurabilityEntry, ...]
    _record_hashes: frozenset[str]
    _bundle_hashes: frozenset[str]

    def __init__(self, *args, **kwargs) -> None:
        raise TypeError("use from_immutable_write_results")

    @classmethod
    def from_immutable_write_results(
        cls,
        *,
        record_writes: Iterable[object] = (),
        bundle_writes: Iterable[object] = (),
    ) -> "VerifiedDurabilityEvidence":
        record_entries = tuple(_record_entry(item) for item in record_writes)
        bundle_entries = tuple(_bundle_entry(item) for item in bundle_writes)
        _reject_duplicate_conflicts(record_entries, "record")
        _reject_duplicate_conflicts(bundle_entries, "bundle")
        instance = cls.__new__(cls)
        object.__setattr__(instance, "_record_entries", record_entries)
        object.__setattr__(instance, "_bundle_entries", bundle_entries)
        object.__setattr__(
            instance,
            "_record_hashes",
            frozenset(entry.stored_object_sha256 for entry in record_entries),
        )
        object.__setattr__(
            instance,
            "_bundle_hashes",
            frozenset(entry.stored_object_sha256 for entry in bundle_entries),
        )
        return instance

    @classmethod
    def empty(cls) -> "VerifiedDurabilityEvidence":
        instance = cls.__new__(cls)
        object.__setattr__(instance, "_record_entries", ())
        object.__setattr__(instance, "_bundle_entries", ())
        object.__setattr__(instance, "_record_hashes", frozenset())
        object.__setattr__(instance, "_bundle_hashes", frozenset())
        return instance

    def has_record_object(self, stored_object_sha256: str) -> bool:
        return stored_object_sha256 in self._record_hashes

    def has_bundle_object(self, stored_bundle_object_sha256: str) -> bool:
        return stored_bundle_object_sha256 in self._bundle_hashes

    @property
    def record_entries(self) -> tuple[VerifiedDurabilityEntry, ...]:
        return self._record_entries

    @property
    def bundle_entries(self) -> tuple[VerifiedDurabilityEntry, ...]:
        return self._bundle_entries


def _record_entry(item: object) -> VerifiedDurabilityEntry:
    stored_object, write_result = _coerce_evidence_pair(
        item, "stored_record_object", "record"
    )
    schema.validate_stored_record_object(stored_object)
    expected_name = primary_writer.record_storage_filename(stored_object)
    return _validate_write_result(
        stored_object=stored_object,
        write_result=write_result,
        object_class=RECORD_OBJECT_CLASS,
        expected_name=expected_name,
        max_bytes=schema.MAX_STORED_RECORD_OBJECT_BYTES,
        stored_object_hash_key="stored_object_sha256",
    )


def _bundle_entry(item: object) -> VerifiedDurabilityEntry:
    stored_object, write_result = _coerce_evidence_pair(
        item, "stored_bundle_object", "bundle"
    )
    schema.validate_stored_bundle_object(stored_object)
    expected_name = primary_writer.bundle_storage_filename(stored_object)
    return _validate_write_result(
        stored_object=stored_object,
        write_result=write_result,
        object_class=BUNDLE_OBJECT_CLASS,
        expected_name=expected_name,
        max_bytes=schema.MAX_STORED_BUNDLE_OBJECT_BYTES,
        stored_object_hash_key="stored_bundle_object_sha256",
    )


def _coerce_evidence_pair(
    item: object, stored_attr: str, label: str
) -> tuple[dict, primary_writer.ImmutableWriteResult]:
    if hasattr(item, stored_attr) and hasattr(item, "write_result"):
        return getattr(item, stored_attr), getattr(item, "write_result")
    if isinstance(item, tuple) and len(item) == 2:
        return item[0], item[1]
    raise DurabilityEvidenceError(
        "%s durability evidence must pair a stored object with an ImmutableWriteResult"
        % label
    )


def _validate_write_result(
    *,
    stored_object: dict,
    write_result: primary_writer.ImmutableWriteResult,
    object_class: str,
    expected_name: str,
    max_bytes: int,
    stored_object_hash_key: str,
) -> VerifiedDurabilityEntry:
    if not isinstance(write_result, primary_writer.ImmutableWriteResult):
        raise DurabilityEvidenceError("write evidence must be ImmutableWriteResult")
    if write_result.authoritative_status != primary_writer.DURABLE_ACCEPTED:
        raise DurabilityEvidenceError("write evidence is not DURABLE_ACCEPTED")
    if (
        write_result.durability_status
        != windows_adapter.DIRECTORY_DURABILITY_CONFIRMED
    ):
        raise DurabilityEvidenceError("directory durability was not confirmed")
    if write_result.readback_verified is not True:
        raise DurabilityEvidenceError("write read-back was not verified")
    path = Path(write_result.path)
    if not path.exists() or not path.is_file():
        raise DurabilityEvidenceError("durability evidence path does not exist")
    if path.name != expected_name:
        raise DurabilityEvidenceError("path filename does not match stored identity")
    stored_object_sha256 = stored_object[stored_object_hash_key]
    _require_hex64(stored_object_sha256, stored_object_hash_key)
    raw = path.read_bytes()
    if len(raw) != write_result.byte_length:
        raise DurabilityEvidenceError("write-result byte length mismatch")
    if schema.sha256_hex(raw) != write_result.sha256:
        raise DurabilityEvidenceError("write-result byte SHA-256 mismatch")
    observed = schema.load_canonical_json_bytes(raw, max_bytes=max_bytes)
    if observed != stored_object:
        raise DurabilityEvidenceError("stored bytes do not match supplied object")
    if object_class == RECORD_OBJECT_CLASS:
        schema.validate_stored_record_object(observed)
    elif object_class == BUNDLE_OBJECT_CLASS:
        schema.validate_stored_bundle_object(observed)
    else:
        raise DurabilityEvidenceError("unsupported object class")
    return VerifiedDurabilityEntry(
        object_class=object_class,
        stored_object_sha256=stored_object_sha256,
        path=str(path),
        byte_length=len(raw),
        byte_sha256=schema.sha256_hex(raw),
    )


def _reject_duplicate_conflicts(
    entries: tuple[VerifiedDurabilityEntry, ...], label: str
) -> None:
    path_to_hash: dict[str, str] = {}
    for entry in entries:
        existing = path_to_hash.get(entry.path)
        if existing is not None and existing != entry.stored_object_sha256:
            raise DurabilityEvidenceError(
                "duplicate-conflicting %s durability evidence" % label
            )
        path_to_hash[entry.path] = entry.stored_object_sha256


def _require_hex64(value: object, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise DurabilityEvidenceError("%s must be lowercase 64-hex" % label)
    if any(char not in "0123456789abcdef" for char in value):
        raise DurabilityEvidenceError("%s must be lowercase 64-hex" % label)
