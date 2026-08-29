"""Inert, STAGING-only runtime binding facts for a pre-existing native core.

The binding is a validated immutable configuration object.  It neither owns a
SQLite connection nor provides a read, write, provider-selection, or activation
method.  Runtime callers may retain it while legacy memory remains authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

from .errors import SubstrateConfigurationError
from .ids import native_id_from_bytes, native_id_to_bytes
from .schema import CORE_ROLE_STAGING, SchemaMetadata, open_schema


_QUALIFIED_REPRESENTATION_CLASS = "COMPAT_EMBEDDING"
_QUALIFIED_GENERATION = 1
_QUALIFIED_DERIVATION_CONTRACT = "compat-embedding-v1"
_QUALIFIED_ENCODING = "RAW_VECTOR"
_QUALIFIED_DTYPE = "float32"
_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"
_LEGACY_ACTIVE_DEPLOYMENT = "LEGACY_ACTIVE"
_PREPARED = object()


@dataclass(frozen=True)
class NativeRepresentationLane:
    """One explicit query/search lane, including caller-owned model identity."""

    provider: str
    model: str
    dimension: int
    representation_class: str
    generation: int
    derivation_contract_version: str
    encoding_id: str
    dtype: str


@dataclass(frozen=True)
class NativeMemoryRuntimeScope:
    """One private-agent or shared-domain native compatibility scope."""

    workspace_id: str
    scope_kind: str
    legacy_source_namespace_id: UUID
    identity_namespace_id: UUID
    semantic_scope_id: UUID
    agent_id: str | None = None
    domain_id: str | None = None

    @property
    def qualifier(self) -> str:
        """Return the required scope-specific human identifier."""
        if self.scope_kind == _PRIVATE_AGENT_SCOPE:
            return self.agent_id or ""
        if self.scope_kind == _SHARED_DOMAIN_SCOPE:
            return self.domain_id or ""
        return ""


@dataclass(frozen=True)
class NativeMemoryBindingReadiness:
    """Operational binding evidence only; it grants no semantic authority."""

    core_qualified: bool
    core_role: str
    scope_bindings_valid: bool
    embedder_lane_compatible: bool
    activation_allowed: bool
    status: str
    reason: str


@dataclass(frozen=True)
class NativeMemoryRuntimeBinding:
    """A prevalidated STAGING core reference retained inertly by Fabric.

    Instances are produced by :func:`prepare_native_memory_runtime_binding`. The
    private marker prevents accidental use of an ad-hoc DTO in the Fabric
    construction seam; it is not a database capability or activation token.
    """

    core_database_path: Path
    core_id: UUID
    core_role: str
    scope_bindings: tuple[NativeMemoryRuntimeScope, ...]
    representation_lane: NativeRepresentationLane
    _prepared_marker: object = field(repr=False, compare=False, default=None)

    def __post_init__(self) -> None:
        if self._prepared_marker is not _PREPARED:
            raise SubstrateConfigurationError(
                "runtime binding must be prepared from an existing qualified STAGING core"
            )


def prepare_native_memory_runtime_binding(
    *,
    connection: sqlite3.Connection,
    core_database_path: str | Path,
    expected_core_id: UUID,
    scope_bindings: tuple[NativeMemoryRuntimeScope, ...],
    representation_lane: NativeRepresentationLane,
) -> NativeMemoryRuntimeBinding:
    """Validate existing STAGING-core facts and return an inert binding DTO.

    ``connection`` is used only during preparation and is never retained.  Its
    path must exactly match ``core_database_path`` so a binding cannot claim one
    core identity while having validated another.  This function writes no
    schema, semantic carrier, transition, operation, or authorization record.
    """

    core_path = _validated_existing_core_path(connection, core_database_path)
    metadata = open_schema(connection)
    actual_core_id = native_id_from_bytes(metadata.core_id)
    if expected_core_id != actual_core_id:
        raise SubstrateConfigurationError("runtime binding core identity does not match the supplied core")
    _validate_staging_deployment(connection, metadata)
    _validate_representation_lane(representation_lane)
    _validate_scope_bindings(connection, scope_bindings)
    return NativeMemoryRuntimeBinding(
        core_database_path=core_path,
        core_id=actual_core_id,
        core_role=metadata.core_role,
        scope_bindings=scope_bindings,
        representation_lane=representation_lane,
        _prepared_marker=_PREPARED,
    )


def validate_fabric_embedder(
    binding: NativeMemoryRuntimeBinding,
    embedder: Any,
) -> NativeMemoryBindingReadiness:
    """Check the Fabric-owned embedder without constructing or replacing it."""

    if not isinstance(binding, NativeMemoryRuntimeBinding):
        raise SubstrateConfigurationError("Fabric requires a prepared native runtime binding")
    lane = binding.representation_lane
    if getattr(embedder, "provider", None) != lane.provider:
        raise SubstrateConfigurationError("Fabric embedder provider does not match the native runtime lane")
    if getattr(embedder, "model", None) != lane.model:
        raise SubstrateConfigurationError("Fabric embedder model does not match the native runtime lane")
    dimension = getattr(embedder, "dim", None)
    if (
        not isinstance(dimension, int)
        or isinstance(dimension, bool)
        or dimension != lane.dimension
    ):
        raise SubstrateConfigurationError("Fabric embedder dimension does not match the native runtime lane")
    return NativeMemoryBindingReadiness(
        core_qualified=True,
        core_role=binding.core_role,
        scope_bindings_valid=True,
        embedder_lane_compatible=True,
        activation_allowed=False,
        status="INERT_STAGING_BOUND",
        reason="validated STAGING binding is attached inertly; legacy storage remains authoritative",
    )


def _validated_existing_core_path(connection: sqlite3.Connection, value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise SubstrateConfigurationError("runtime binding requires an existing native core database path")
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() != ".db" or not path.is_file():
        raise SubstrateConfigurationError("runtime binding core database must already exist as a .db file")
    if not isinstance(connection, sqlite3.Connection):
        raise SubstrateConfigurationError("runtime binding preparation requires a qualified sqlite connection")
    rows = connection.execute("PRAGMA database_list").fetchall()
    main_paths = [str(row[2]) for row in rows if row[1] == "main"]
    if len(main_paths) != 1 or not main_paths[0]:
        raise SubstrateConfigurationError("runtime binding connection must be file-backed")
    connected_path = Path(main_paths[0]).expanduser().resolve()
    if os.path.normcase(str(connected_path)) != os.path.normcase(str(path)):
        raise SubstrateConfigurationError("runtime binding database path does not match the qualified connection")
    return path


def _validate_staging_deployment(connection: sqlite3.Connection, metadata: SchemaMetadata) -> None:
    if metadata.core_role != CORE_ROLE_STAGING:
        raise SubstrateConfigurationError("only STAGING cores may be attached through the inert runtime binding")
    rows = connection.execute(
        "SELECT deployment_state,referenced_core_id FROM deployment_metadata"
    ).fetchall()
    if len(rows) != 1:
        raise SubstrateConfigurationError("native deployment metadata is not singleton")
    deployment_state, referenced_core_id = rows[0]
    if deployment_state != _LEGACY_ACTIVE_DEPLOYMENT or referenced_core_id is not None:
        raise SubstrateConfigurationError("inert runtime binding refuses non-legacy-active deployment state")


def _validate_representation_lane(lane: NativeRepresentationLane) -> None:
    if not isinstance(lane, NativeRepresentationLane):
        raise SubstrateConfigurationError("runtime binding requires an explicit native representation lane")
    if not isinstance(lane.provider, str) or not lane.provider:
        raise SubstrateConfigurationError("native runtime lane provider must be a non-empty string")
    if not isinstance(lane.model, str) or not lane.model:
        raise SubstrateConfigurationError("native runtime lane model must be a non-empty string")
    if not isinstance(lane.dimension, int) or isinstance(lane.dimension, bool) or lane.dimension < 1:
        raise SubstrateConfigurationError("native runtime lane dimension must be a positive integer")
    if (
        lane.representation_class,
        lane.generation,
        lane.derivation_contract_version,
        lane.encoding_id,
        lane.dtype,
    ) != (
        _QUALIFIED_REPRESENTATION_CLASS,
        _QUALIFIED_GENERATION,
        _QUALIFIED_DERIVATION_CONTRACT,
        _QUALIFIED_ENCODING,
        _QUALIFIED_DTYPE,
    ):
        raise SubstrateConfigurationError(
            "runtime binding supports only the qualified COMPAT_EMBEDDING/1 RAW_VECTOR float32 lane"
        )


def _validate_scope_bindings(
    connection: sqlite3.Connection,
    bindings: tuple[NativeMemoryRuntimeScope, ...],
) -> None:
    if not isinstance(bindings, tuple) or not bindings:
        raise SubstrateConfigurationError("runtime binding requires one or more explicit scope bindings")
    binding_keys: set[tuple[str, str, str]] = set()
    source_namespaces: set[UUID] = set()
    for binding in bindings:
        if not isinstance(binding, NativeMemoryRuntimeScope):
            raise SubstrateConfigurationError("runtime scope bindings must be typed NativeMemoryRuntimeScope values")
        if not isinstance(binding.workspace_id, str) or not binding.workspace_id:
            raise SubstrateConfigurationError("runtime scope workspace_id must be a non-empty string")
        if binding.scope_kind == _PRIVATE_AGENT_SCOPE:
            if not isinstance(binding.agent_id, str) or not binding.agent_id or binding.domain_id is not None:
                raise SubstrateConfigurationError("private runtime scope requires agent_id and forbids domain_id")
        elif binding.scope_kind == _SHARED_DOMAIN_SCOPE:
            if not isinstance(binding.domain_id, str) or not binding.domain_id or binding.agent_id is not None:
                raise SubstrateConfigurationError("shared runtime scope requires domain_id and forbids agent_id")
        else:
            raise SubstrateConfigurationError("runtime scope kind must be PRIVATE_AGENT or SHARED_DOMAIN")
        key = (binding.workspace_id, binding.scope_kind, binding.qualifier)
        if key in binding_keys:
            raise SubstrateConfigurationError("runtime scope binding collision")
        binding_keys.add(key)
        if binding.legacy_source_namespace_id in source_namespaces:
            raise SubstrateConfigurationError("runtime scope bindings cannot share a compatibility source namespace")
        source_namespaces.add(binding.legacy_source_namespace_id)
        _require_native_id_row(
            connection, "identity_namespaces", "identity_namespace_id", binding.identity_namespace_id
        )
        _require_native_id_row(
            connection, "semantic_scopes", "semantic_scope_id", binding.semantic_scope_id
        )
        _require_native_id_row(
            connection, "legacy_source_namespaces", "legacy_source_namespace_id", binding.legacy_source_namespace_id
        )


def _require_native_id_row(connection: sqlite3.Connection, table: str, column: str, value: UUID) -> None:
    try:
        encoded = native_id_to_bytes(value)
    except Exception as exc:
        raise SubstrateConfigurationError(f"runtime scope {column} must be a native UUID") from exc
    row = connection.execute(
        f"SELECT 1 FROM {table} WHERE {column}=?", (encoded,)
    ).fetchone()
    if row is None:
        raise SubstrateConfigurationError(f"runtime scope references a missing {column}")


__all__ = [
    "NativeMemoryBindingReadiness",
    "NativeMemoryRuntimeBinding",
    "NativeMemoryRuntimeScope",
    "NativeRepresentationLane",
    "prepare_native_memory_runtime_binding",
    "validate_fabric_embedder",
]
