"""Rebuildable, process-local native vector retrieval for one explicit lane.

This module is deliberately a read-only substrate primitive.  SQLite remains
the authority for core memories, current revisions, aliases, runtime order,
representations, and integrity.  The dense matrix below is only an atomic,
discardable cache reconstructed from those facts.  Nothing in this module
selects it from Fabric or changes native activation state.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping, Protocol
from uuid import UUID

import numpy as np

from .compat import LegacyMemoryView, NativeMemoryCompatibilityFacade
from .compat_embedding_reader import CurrentCompatEmbeddingWitness, NativeCompatEmbeddingReader
from .connection import QualifiedExistingCoreConnection, open_existing_native_core_connection
from .errors import (
    SubstrateConfigurationError,
    SubstrateError,
    SubstrateInvariantViolation,
)
from .ids import native_id_to_bytes
from .runtime_binding import (
    NativeMemoryRuntimeBinding,
    NativeMemoryRuntimeScope,
    NativeRepresentationLane,
    prepare_native_memory_runtime_binding,
)


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"
_DECAY_RANKING_FLOOR = 0.03


class NativeVectorRuntimeEmbedder(Protocol):
    """The caller-owned query derivation capability for one vector lane."""

    provider: str
    model: str
    dim: int

    def embed(self, text: str) -> Any: ...


@dataclass(frozen=True)
class NativeMemoryVectorRuntimeConfiguration:
    """The complete durable identity of one rebuildable cache lane.

    ``scope`` carries workspace, scope kind, qualifier, source namespace,
    identity namespace, and semantic scope.  ``representation_lane`` carries
    all representation identity facts.  A bare EID cannot identify this
    configuration or any row built from it.
    """

    core_database_path: Path | str
    expected_core_id: UUID
    scope: NativeMemoryRuntimeScope
    representation_lane: NativeRepresentationLane

    def __post_init__(self) -> None:
        if not isinstance(self.core_database_path, (str, Path)) or not str(self.core_database_path).strip():
            raise ValueError("core_database_path must be a non-empty file path")
        object.__setattr__(self, "core_database_path", Path(self.core_database_path).expanduser().resolve())
        if not isinstance(self.expected_core_id, UUID):
            raise ValueError("expected_core_id must be a UUID")
        if not isinstance(self.scope, NativeMemoryRuntimeScope):
            raise ValueError("scope must be a NativeMemoryRuntimeScope")
        if not isinstance(self.representation_lane, NativeRepresentationLane):
            raise ValueError("representation_lane must be a NativeRepresentationLane")

    @property
    def lane_key(self) -> tuple[object, ...]:
        """Return the full process-local cache identity, never a bare EID."""
        lane = self.representation_lane
        scope = self.scope
        return (
            str(self.core_database_path),
            self.expected_core_id,
            scope.workspace_id,
            scope.scope_kind,
            scope.qualifier,
            scope.legacy_source_namespace_id,
            scope.identity_namespace_id,
            scope.semantic_scope_id,
            lane.provider,
            lane.model,
            lane.representation_class,
            lane.generation,
            lane.derivation_contract_version,
            lane.encoding_id,
            lane.dtype,
            lane.dimension,
        )


@dataclass(frozen=True)
class NativeVectorRuntimeSourceWitness:
    """One current source witness, including sources without usable vectors."""

    eid: int
    object_id: UUID
    object_revision_id: UUID
    object_revision_ordinal: int
    runtime_ordinal: int
    representation_id: UUID | None
    integrity_expectation_id: UUID | None
    selected_integrity_measurement_id: UUID | None
    raw_representation_digest: str | None


@dataclass(frozen=True)
class NativeVectorRuntimeRow:
    """Immutable durable witnesses corresponding to exactly one matrix row."""

    eid: int
    object_id: UUID
    object_revision_id: UUID
    object_revision_ordinal: int
    representation_id: UUID
    integrity_expectation_id: UUID
    selected_integrity_measurement_id: UUID
    raw_representation_digest: str


@dataclass(frozen=True)
class NativeVectorRuntimeSnapshot:
    """One complete candidate cache published atomically inside this process."""

    lane_key: tuple[object, ...]
    rows: tuple[NativeVectorRuntimeRow, ...]
    source_witnesses: tuple[NativeVectorRuntimeSourceWitness, ...]
    matrix: np.ndarray | None
    currentness_signature: tuple[object, ...]
    database_data_version: int

    def __post_init__(self) -> None:
        if not isinstance(self.database_data_version, int) or self.database_data_version < 0:
            raise ValueError("vector snapshot database data version must be non-negative")
        if self.matrix is None:
            if self.rows:
                raise ValueError("vector snapshot rows require a matrix")
            return
        if self.matrix.dtype != np.float32 or self.matrix.ndim != 2:
            raise ValueError("vector snapshot matrix must be two-dimensional float32")
        if self.matrix.shape[0] != len(self.rows):
            raise ValueError("vector snapshot row witnesses contradict the matrix")
        if self.matrix.flags.writeable:
            raise ValueError("vector snapshot matrix must be immutable")


@dataclass(frozen=True)
class _QualifiedVectorCandidate:
    """One batched, fully-qualified raw vector read during candidate rebuild."""

    object_id: UUID
    object_revision_id: UUID
    object_revision_ordinal: int
    representation_id: UUID
    integrity_expectation_id: UUID
    selected_integrity_measurement_id: UUID
    payload_sha256: str
    raw_vector: np.ndarray


class NativeMemoryVectorRuntime:
    """An exact MemoryGraph-cache-shaped reader for one native storage lane.

    The runtime owns its qualified existing-core connection for its lifetime.
    It never opens legacy files, uses a legacy ``MemoryGraph``, creates a
    semantic transaction, or changes a durable carrier.  ``close()`` releases
    that reader connection; callers are expected to construct a fresh runtime
    after process recovery.
    """

    def __init__(
        self,
        configuration: NativeMemoryVectorRuntimeConfiguration,
        *,
        embedder: NativeVectorRuntimeEmbedder,
    ) -> None:
        if not isinstance(configuration, NativeMemoryVectorRuntimeConfiguration):
            raise ValueError("configuration must be a NativeMemoryVectorRuntimeConfiguration")
        self._configuration = configuration
        self._embedder = _validate_embedder(embedder, configuration.representation_lane)
        self._opened: QualifiedExistingCoreConnection = open_existing_native_core_connection(
            configuration.core_database_path
        )
        try:
            self._binding: NativeMemoryRuntimeBinding = prepare_native_memory_runtime_binding(
                connection=self._opened.connection,
                core_database_path=configuration.core_database_path,
                expected_core_id=configuration.expected_core_id,
                scope_bindings=(configuration.scope,),
                representation_lane=configuration.representation_lane,
            )
            self._connection = self._opened.connection
            self._compatibility = NativeMemoryCompatibilityFacade(self._connection)
            self._embeddings = NativeCompatEmbeddingReader(self._connection)
        except Exception:
            self._opened.close()
            raise
        self._snapshot: NativeVectorRuntimeSnapshot | None = None
        self._dirty = True
        self._last_invalidation_reason: str | None = "initial-build"
        self._closed = False
        self._rebuild_count = 0

    @property
    def configuration(self) -> NativeMemoryVectorRuntimeConfiguration:
        return self._configuration

    @property
    def snapshot(self) -> NativeVectorRuntimeSnapshot | None:
        """Return the active immutable cache snapshot, if one is usable."""
        return self._snapshot

    @property
    def rebuild_count(self) -> int:
        """Expose a diagnostic counter without making cache state authoritative."""
        return self._rebuild_count

    @property
    def last_invalidation_reason(self) -> str | None:
        return self._last_invalidation_reason

    def close(self) -> None:
        if not self._closed:
            self._opened.close()
            self._closed = True
            self._snapshot = None
            self._dirty = True

    def __enter__(self) -> "NativeMemoryVectorRuntime":
        self._require_open()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def invalidate(self, reason: str) -> None:
        """Mark this one process-local lane unusable without writing durable state."""
        self._require_open()
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("invalidation reason must be a non-empty string")
        self._dirty = True
        self._last_invalidation_reason = reason

    def search(
        self,
        query_text: str,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: list[str] | tuple[str, ...] | None = None,
    ) -> list[dict[str, Any]]:
        """Invoke the lane's own embedder, then run exact cached search semantics."""
        self._require_open()
        query = (query_text or "").strip()
        if not query:
            return []
        # This intentionally mirrors MemoryGraph.search(): the configured
        # per-lane embedder is called here, not supplied an earlier Fabric qemb.
        vector = np.asarray(self._embedder.embed(query), dtype=np.float32).reshape(-1)
        if int(vector.shape[0]) != int(self._configuration.representation_lane.dimension):
            vector = self._normalize(vector)
        return self._search_vector(
            vector,
            top_k=top_k,
            user_id=user_id,
            min_score=min_score,
            type_filter=type_filter,
            canon_only=False,
        )

    def search_by_embedding(
        self,
        embedding: Any,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: list[str] | tuple[str, ...] | None = None,
        canon_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Run MemoryGraph's vectorised cached search law over one native lane."""
        self._require_open()
        query = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if query.size == 0:
            return []
        return self._search_vector(
            query,
            top_k=top_k,
            user_id=user_id,
            min_score=min_score,
            type_filter=type_filter,
            canon_only=canon_only,
        )

    def _search_vector(
        self,
        query: np.ndarray,
        *,
        top_k: int,
        user_id: str | None,
        min_score: float | None,
        type_filter: list[str] | tuple[str, ...] | None,
        canon_only: bool,
    ) -> list[dict[str, Any]]:
        snapshot = self._ensure_snapshot()
        if snapshot is None or snapshot.matrix is None:
            return []
        normalized_query = self._normalize(query)
        scores = (snapshot.matrix @ normalized_query).astype(np.float32)
        limit = int(max(1, top_k))
        if int(scores.shape[0]) <= limit:
            order = np.argsort(-scores)
        else:
            candidate = np.argpartition(-scores, limit - 1)[:limit]
            order = candidate[np.argsort(-scores[candidate])]

        selected = tuple(
            (snapshot.rows[int(index)], float(scores[int(index)]))
            for index in order[:limit]
        )
        sources = self._batch_project_current_rows(tuple(row for row, _ in selected))
        if sources is None:
            # A durable change raced after pre-query currentness validation.
            # Do not mix a stale vector with a new semantic payload.
            self._snapshot = None
            self._dirty = True
            self._last_invalidation_reason = "concurrent-currentness-change"
            return []

        now_ts = int(time.time())
        type_set = set(type_filter or [])
        results: list[dict[str, Any]] = []
        for (row, raw_score), source in zip(selected, sources, strict=True):
            payload = dict(source.payload)
            if min_score is not None and raw_score < float(min_score):
                continue
            if canon_only and not payload.get("canon", False):
                continue
            if user_id is not None and str(payload.get("user_id", "")) != str(user_id):
                continue
            memory_type = str(payload.get("type") or payload.get("mtype") or "")
            if type_set and memory_type and memory_type not in type_set:
                continue
            decay = _half_life_decay_factor(payload, now_ts)
            result = {
                "eid": int(row.eid),
                "score": raw_score * decay,
                "raw_score": raw_score,
                "decay_factor": decay,
                "summary": str(payload.get("summary") or payload.get("text") or ""),
                "type": memory_type or "memory",
                "strength": float(payload.get("strength") or 0.0),
                "confidence": float(payload.get("confidence") or 0.0),
                "step": int(payload.get("step") or payload.get("born_step") or 0),
                "ts": int(payload.get("ts") or payload.get("created_ts") or 0),
            }
            # MemoryGraph deliberately leaves flexible payload fields last.
            result.update(payload)
            results.append(result)
        results.sort(key=lambda item: item["score"], reverse=True)
        return results

    def _batch_project_current_rows(
        self,
        rows: tuple[NativeVectorRuntimeRow, ...],
    ) -> tuple[LegacyMemoryView, ...] | None:
        """Return one coherent selected-result snapshot or refuse it whole.

        The runtime begins a SQLite read transaction before the first witness
        read.  The batched representation proof and facade projection therefore
        observe one durable point in time.  A later writer commit is visible to
        the next query through ``data_version``; it cannot mix revisions inside
        this result.
        """
        if not rows:
            return ()
        if self._connection.in_transaction:
            raise SubstrateInvariantViolation("native vector projection requires a fresh read transaction")
        try:
            self._connection.execute("BEGIN")
            witnesses = tuple(CurrentCompatEmbeddingWitness(
                row.eid,
                row.object_id,
                row.object_revision_id,
                row.object_revision_ordinal,
                row.representation_id,
                row.integrity_expectation_id,
                row.selected_integrity_measurement_id,
            ) for row in rows)
            if not self._embeddings.validate_current_witnesses(
                legacy_source_namespace_id=self._configuration.scope.legacy_source_namespace_id,
                identity_namespace_id=self._configuration.scope.identity_namespace_id,
                semantic_scope_id=self._configuration.scope.semantic_scope_id,
                witnesses=witnesses,
            ):
                raise SubstrateInvariantViolation("selected native vector rows are no longer current")
            sources = self._compatibility.get_memories_by_eids(
                legacy_source_namespace_id=self._configuration.scope.legacy_source_namespace_id,
                eids=tuple(row.eid for row in rows),
            )
            if len(sources) != len(rows):
                raise SubstrateInvariantViolation("selected native vector projection is incomplete")
            for row, source in zip(rows, sources, strict=True):
                if (
                    source.eid != row.eid
                    or source.object_id != row.object_id
                    or source.revision_id != row.object_revision_id
                    or source.revision_ordinal != row.object_revision_ordinal
                    or source.semantic_scope_id != self._configuration.scope.semantic_scope_id
                ):
                    raise SubstrateInvariantViolation("selected native vector projection contradicts its witness")
            self._connection.execute("COMMIT")
            return sources
        except (SubstrateError, TypeError, ValueError, sqlite3.Error):
            if self._connection.in_transaction:
                self._connection.execute("ROLLBACK")
            return None

    def _ensure_snapshot(self) -> NativeVectorRuntimeSnapshot | None:
        self._require_open()
        try:
            database_data_version = self._database_data_version()
        except (SubstrateError, sqlite3.Error):
            self._snapshot = None
            self._dirty = True
            self._last_invalidation_reason = "currentness-signature-unavailable"
            return None
        if (
            not self._dirty
            and self._snapshot is not None
            and self._snapshot.database_data_version == database_data_version
        ):
            return self._snapshot
        current_signature: tuple[object, ...] | None = None
        if not self._dirty and self._snapshot is not None:
            try:
                current_signature = self._currentness_signature()
            except (SubstrateError, sqlite3.Error):
                self._snapshot = None
                self._dirty = True
                self._last_invalidation_reason = "currentness-signature-unavailable"
                return None
        if (
            not self._dirty
            and self._snapshot is not None
            and current_signature is not None
            and self._snapshot.currentness_signature == current_signature
        ):
            # A motif/relationship-only durable write changed SQLite's global
            # data version but no memory-vector witness. Retain this exact
            # matrix and mark the observed version; no rebuild is warranted.
            self._snapshot = replace(self._snapshot, database_data_version=database_data_version)
            return self._snapshot
        # A changed signature makes the old matrix unusable immediately.  A
        # failed candidate rebuild cannot cause us to serve the older state.
        self._snapshot = None
        self._dirty = True
        try:
            candidate = self._build_snapshot(current_signature, database_data_version)
        except SubstrateError:
            self._last_invalidation_reason = "candidate-rebuild-failed"
            return None
        except (TypeError, ValueError, sqlite3.Error):
            self._last_invalidation_reason = "candidate-rebuild-failed"
            return None
        self._snapshot = candidate
        self._dirty = False
        self._last_invalidation_reason = None
        self._rebuild_count += 1
        return candidate

    def _build_snapshot(
        self,
        initial_signature: tuple[object, ...] | None,
        initial_data_version: int,
    ) -> NativeVectorRuntimeSnapshot:
        # These batched reads validate aliases, current revisions, source
        # scope, immutable order, representation state, and byte witnesses.
        # Semantic result payloads remain deliberately deferred to
        # NativeMemoryCompatibilityFacade for selected candidate rows.
        current_sources = self._enumerate_current_sources()
        qualified_vectors = self._enumerate_qualified_vectors()
        normalized_rows: list[tuple[NativeVectorRuntimeRow, np.ndarray]] = []
        sources: list[NativeVectorRuntimeSourceWitness] = []
        for source in current_sources:
            qualified = qualified_vectors.get(source.object_id)
            if qualified is None:
                sources.append(NativeVectorRuntimeSourceWitness(
                    source.eid, source.object_id, source.object_revision_id,
                    source.object_revision_ordinal, source.runtime_ordinal,
                    None,
                    None,
                    None,
                    None,
                ))
                continue
            if (
                qualified.object_revision_id != source.object_revision_id
                or qualified.object_revision_ordinal != source.object_revision_ordinal
            ):
                raise SubstrateInvariantViolation("qualified vector is not attached to its source current revision")
            digest = qualified.payload_sha256
            source_witness = NativeVectorRuntimeSourceWitness(
                source.eid, source.object_id, source.object_revision_id,
                source.object_revision_ordinal, source.runtime_ordinal,
                qualified.representation_id, qualified.integrity_expectation_id,
                qualified.selected_integrity_measurement_id,
                digest,
            )
            sources.append(source_witness)
            row = NativeVectorRuntimeRow(
                source_witness.eid,
                source_witness.object_id,
                source_witness.object_revision_id,
                source_witness.object_revision_ordinal,
                qualified.representation_id,
                qualified.integrity_expectation_id,
                qualified.selected_integrity_measurement_id,
                digest,
            )
            normalized_rows.append((row, self._normalize(qualified.raw_vector)))
        if len(sources) != len(current_sources):
            raise SubstrateInvariantViolation("native vector source enumeration is incomplete")
        normalized_rows.sort(key=lambda item: item[0].eid)
        rows = [item[0] for item in normalized_rows]
        sources.sort(key=lambda item: item.runtime_ordinal)
        if len({item.eid for item in sources}) != len(sources):
            raise SubstrateInvariantViolation("native vector source enumeration has duplicate EIDs")
        matrix: np.ndarray | None
        if rows:
            matrix = np.stack([item[1] for item in normalized_rows], axis=0).astype(np.float32)
            matrix.setflags(write=False)
        else:
            matrix = None
        final_signature = _snapshot_currentness_signature(current_sources, qualified_vectors)
        if initial_signature is not None and final_signature != initial_signature:
            raise SubstrateInvariantViolation("native vector sources changed during candidate rebuild")
        final_data_version = self._database_data_version()
        if final_data_version != initial_data_version:
            raise SubstrateInvariantViolation("native vector sources changed during candidate rebuild")
        return NativeVectorRuntimeSnapshot(
            self._configuration.lane_key,
            tuple(rows),
            tuple(sources),
            matrix,
            final_signature,
            final_data_version if final_data_version != initial_data_version else initial_data_version,
        )

    def _enumerate_current_sources(self) -> tuple[NativeVectorRuntimeSourceWitness, ...]:
        """Validate full alias/order completeness in bounded bulk reads."""
        namespace = native_id_to_bytes(self._configuration.scope.legacy_source_namespace_id)
        alias_rows = self._connection.execute(
            """
            SELECT a.alias_value,a.object_id,o.identity_namespace_id,o.object_kind,
                   o.current_revision_id,o.current_revision_ordinal,
                   r.effective_semantic_scope_id
              FROM legacy_object_aliases a
              JOIN objects o ON o.object_id=a.object_id
              LEFT JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
             ORDER BY a.alias_value
            """,
            (namespace,),
        ).fetchall()
        order_rows = self._connection.execute(
            """
            SELECT object_id,runtime_ordinal
              FROM memory_runtime_enumeration_orders
             WHERE legacy_source_namespace_id=?
             ORDER BY runtime_ordinal
            """,
            (namespace,),
        ).fetchall()
        ordinals: dict[UUID, int] = {}
        seen_ordinals: set[int] = set()
        for object_id, ordinal in order_rows:
            if not isinstance(object_id, bytes) or len(object_id) != 16:
                raise SubstrateInvariantViolation("runtime-order witness has an invalid object identity")
            if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
                raise SubstrateInvariantViolation("runtime-order witness has an invalid ordinal")
            identifier = UUID(bytes=object_id)
            if identifier in ordinals or ordinal in seen_ordinals:
                raise SubstrateInvariantViolation("runtime-order witness is ambiguous")
            ordinals[identifier] = ordinal
            seen_ordinals.add(ordinal)
        sources: list[NativeVectorRuntimeSourceWitness] = []
        seen_objects: set[UUID] = set()
        seen_eids: set[int] = set()
        for alias, object_id, identity, kind, revision_id, revision_ordinal, semantic_scope in alias_rows:
            eid = _canonical_eid(alias)
            if not isinstance(object_id, bytes) or len(object_id) != 16:
                raise SubstrateInvariantViolation("runtime EID alias has an invalid object identity")
            if not isinstance(revision_id, bytes) or len(revision_id) != 16:
                raise SubstrateInvariantViolation("runtime memory has no complete current revision")
            if not isinstance(revision_ordinal, int) or isinstance(revision_ordinal, bool) or revision_ordinal < 1:
                raise SubstrateInvariantViolation("runtime memory has an invalid current revision ordinal")
            identifier = UUID(bytes=object_id)
            if identifier in seen_objects or eid in seen_eids:
                raise SubstrateInvariantViolation("runtime memory aliases are ambiguous")
            if identifier not in ordinals:
                raise SubstrateInvariantViolation("runtime memory alias has no order witness")
            if identity != native_id_to_bytes(self._configuration.scope.identity_namespace_id):
                raise SubstrateInvariantViolation("native vector source has a different identity namespace")
            if kind != _MEMORY_OBJECT_KIND:
                raise SubstrateInvariantViolation("native vector source is not a core memory")
            if semantic_scope != native_id_to_bytes(self._configuration.scope.semantic_scope_id):
                raise SubstrateInvariantViolation("native vector source has a different semantic scope")
            seen_objects.add(identifier)
            seen_eids.add(eid)
            sources.append(NativeVectorRuntimeSourceWitness(
                eid, identifier, UUID(bytes=revision_id), revision_ordinal,
                ordinals[identifier], None, None, None, None,
            ))
        if seen_objects != set(ordinals):
            raise SubstrateInvariantViolation("runtime memory aliases and runtime order disagree")
        sources.sort(key=lambda item: item.runtime_ordinal)
        return tuple(sources)

    def _enumerate_qualified_vectors(self) -> dict[UUID, _QualifiedVectorCandidate]:
        """Read every eligible raw float32 row through the frozen qualification law."""
        lane = self._configuration.representation_lane
        namespace = native_id_to_bytes(self._configuration.scope.legacy_source_namespace_id)
        rows = self._connection.execute(
            """
            WITH expected AS MATERIALIZED (
                SELECT representation_id,MIN(expectation_id) AS expectation_id
                  FROM integrity_expectations
                 WHERE subject_kind='REPRESENTATION'
                 GROUP BY representation_id
                HAVING count(*)=1
            )
            SELECT r.representation_id,r.source_object_id,r.source_object_revision_id,
                   r.source_object_revision_ordinal,r.expected_payload_byte_length,
                   expectation.expectation_id,state.selected_integrity_measurement_id,payload.payload_bytes
              FROM legacy_object_aliases alias
              JOIN objects object ON object.object_id=alias.object_id
              JOIN representations r
                ON r.source_kind='OBJECT_REVISION'
               AND r.source_object_id=object.object_id
               AND r.source_object_revision_id=object.current_revision_id
               AND r.source_object_revision_ordinal=object.current_revision_ordinal
              JOIN representation_current_state state USING(representation_id)
              JOIN expected expectation ON expectation.representation_id=r.representation_id
              JOIN integrity_measurements measurement
                ON measurement.measurement_id=state.selected_integrity_measurement_id
               AND measurement.expectation_id=expectation.expectation_id
              JOIN representation_payloads payload USING(representation_id)
             WHERE alias.legacy_source_namespace_id=? AND alias.alias_kind='EID'
               AND object.object_kind=?
               AND r.representation_class=? AND r.generation=?
               AND r.derivation_contract_version=? AND r.encoding_id=?
               AND r.dtype=? AND r.dimension=?
               AND state.readiness='READY' AND state.operational_disposition='USABLE'
               AND measurement.result='MATCH'
               AND NOT EXISTS (
                   SELECT 1
                     FROM reconciliation_cases reconciliation
                     JOIN reconciliation_case_states reconciliation_state
                       ON reconciliation_state.reconciliation_case_id=reconciliation.reconciliation_case_id
                      AND reconciliation_state.reconciliation_state_id=reconciliation.current_state_id
                      AND reconciliation_state.state_ordinal=reconciliation.current_state_ordinal
                    WHERE reconciliation.subject_kind='REPRESENTATION'
                      AND reconciliation.representation_id=r.representation_id
                      AND reconciliation_state.operational_disposition<>'USABLE'
               )
             ORDER BY r.source_object_id,r.representation_id
            """,
            (
                namespace, _MEMORY_OBJECT_KIND, lane.representation_class, lane.generation,
                lane.derivation_contract_version, lane.encoding_id, lane.dtype, lane.dimension,
            ),
        ).fetchall()
        candidates: dict[UUID, _QualifiedVectorCandidate] = {}
        required_length = lane.dimension * np.dtype(np.float32).itemsize
        for representation_id, object_id, revision_id, ordinal, expected_length, expectation_id, measurement_id, payload in rows:
            if (
                not isinstance(representation_id, bytes) or len(representation_id) != 16
                or not isinstance(object_id, bytes) or len(object_id) != 16
                or not isinstance(revision_id, bytes) or len(revision_id) != 16
                or not isinstance(expectation_id, bytes) or len(expectation_id) != 16
                or not isinstance(measurement_id, bytes) or len(measurement_id) != 16
            ):
                raise SubstrateInvariantViolation("qualified vector has an invalid durable identity")
            if expected_length != required_length or not isinstance(payload, bytes) or len(payload) != required_length:
                raise SubstrateInvariantViolation("qualified vector payload length contradicts its lane")
            if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
                raise SubstrateInvariantViolation("qualified vector has an invalid source revision ordinal")
            vector = np.frombuffer(payload, dtype=np.float32)
            if vector.size != lane.dimension or not np.all(np.isfinite(vector)):
                raise SubstrateInvariantViolation("qualified vector payload is not finite float32 geometry")
            identifier = UUID(bytes=object_id)
            if identifier in candidates:
                raise SubstrateInvariantViolation("native vector lane has contradictory qualified representations")
            candidates[identifier] = _QualifiedVectorCandidate(
                identifier,
                UUID(bytes=revision_id),
                ordinal,
                UUID(bytes=representation_id),
                UUID(bytes=expectation_id),
                UUID(bytes=measurement_id),
                sha256(payload).hexdigest(),
                vector.copy(),
            )
        return candidates

    def _currentness_signature(self) -> tuple[object, ...]:
        """Observe only durable facts that can alter this matrix's rows.

        A data-version change causes a fresh qualified source/vector pass. A
        noneligible representation changing among noneligible states therefore
        need not invalidate a matrix; if it becomes READY/USABLE/MATCH it
        appears in the observed qualified set and changes this signature.
        Motif/relationship writes do neither and leave it unchanged.
        """
        return _snapshot_currentness_signature(
            self._enumerate_current_sources(),
            self._enumerate_qualified_vectors(),
        )

    def _database_data_version(self) -> int:
        row = self._connection.execute("PRAGMA data_version").fetchone()
        if row is None or not isinstance(row[0], int) or isinstance(row[0], bool) or row[0] < 0:
            raise SubstrateInvariantViolation("SQLite data version is unavailable")
        return row[0]

    def _normalize(self, value: Any) -> np.ndarray:
        """Mirror ``MemoryGraph._normalize`` byte-for-byte in float32 space."""
        dimension = self._configuration.representation_lane.dimension
        vector = np.asarray(value, dtype=np.float32).reshape(-1)
        if vector.size == 0:
            return np.zeros(dimension, dtype=np.float32)
        if int(vector.shape[0]) != int(dimension):
            if vector.size < int(dimension):
                vector = np.pad(vector, (0, int(dimension) - int(vector.size)))
            else:
                vector = vector[: int(dimension)]
        norm = float(np.linalg.norm(vector) + 1e-12)
        return (vector / norm).astype(np.float32)

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("native memory vector runtime is closed")


def _validate_embedder(
    embedder: NativeVectorRuntimeEmbedder,
    lane: NativeRepresentationLane,
) -> NativeVectorRuntimeEmbedder:
    if getattr(embedder, "provider", None) != lane.provider:
        raise SubstrateConfigurationError("native vector embedder provider does not match the configured lane")
    if getattr(embedder, "model", None) != lane.model:
        raise SubstrateConfigurationError("native vector embedder model does not match the configured lane")
    dimension = getattr(embedder, "dim", None)
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension != lane.dimension:
        raise SubstrateConfigurationError("native vector embedder dimension does not match the configured lane")
    if not callable(getattr(embedder, "embed", None)):
        raise SubstrateConfigurationError("native vector embedder must provide a callable embed method")
    return embedder


def _half_life_decay_factor(payload: Mapping[str, Any], now_ts: int) -> float:
    """Copy MemoryGraph's frozen query-time decay law without importing it."""
    half_life = float(payload.get("half_life", 0) or 0)
    if half_life <= 0:
        return 1.0
    anchor_ts = int(payload.get("last_reinforced_ts", 0) or 0)
    if anchor_ts <= 0:
        anchor_ts = int(payload.get("created_ts", 0) or 0)
    if anchor_ts <= 0:
        return 1.0
    age_days = max(0.0, (now_ts - anchor_ts) / 86400.0)
    if age_days <= 0:
        return 1.0
    factor = float(2.0 ** (-age_days / half_life))
    return max(_DECAY_RANKING_FLOOR, factor)


def _canonical_eid(value: object) -> int:
    if not isinstance(value, str) or not value:
        raise SubstrateInvariantViolation("runtime EID alias is invalid")
    try:
        eid = int(value)
    except ValueError as exc:
        raise SubstrateInvariantViolation("runtime EID alias is invalid") from exc
    if str(eid) != value or eid < 0:
        raise SubstrateInvariantViolation("runtime EID alias is not canonical")
    return eid


def _snapshot_currentness_signature(
    sources: tuple[NativeVectorRuntimeSourceWitness, ...],
    qualified_vectors: Mapping[UUID, _QualifiedVectorCandidate],
) -> tuple[object, ...]:
    """Build a lane-local freshness fingerprint from qualified durable facts."""
    source_facts = tuple(
        (
            item.eid,
            item.object_id.bytes,
            item.object_revision_id.bytes,
            item.object_revision_ordinal,
            item.runtime_ordinal,
        )
        for item in sources
    )
    vector_facts = tuple(sorted(
        (
            item.object_id.bytes,
            item.object_revision_id.bytes,
            item.object_revision_ordinal,
            item.representation_id.bytes,
            item.integrity_expectation_id.bytes,
            item.selected_integrity_measurement_id.bytes,
            item.payload_sha256,
        )
        for item in qualified_vectors.values()
    ))
    return (source_facts, vector_facts)


__all__ = [
    "NativeMemoryVectorRuntime",
    "NativeMemoryVectorRuntimeConfiguration",
    "NativeVectorRuntimeEmbedder",
    "NativeVectorRuntimeRow",
    "NativeVectorRuntimeSnapshot",
    "NativeVectorRuntimeSourceWitness",
]
