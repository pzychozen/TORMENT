"""Exact runtime-negative proof for certified B2 source-semantic refusals.

A certified refusal leaves the imported R1 record as historical evidence.  In
particular, it may retain a ``LEGACY_EMBEDDING_CAPTURE`` that is explicitly
readable by the legacy-evidence admission boundary.  That is distinct from a
native runtime embedding: the latter must never be attached to a refused
memory, and neither the qualified embedding reader nor the vector owner may
return the memory for runtime use.

This module is a read-only audit boundary.  It creates no semantic transition,
representation, carrier, or reconciliation state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sqlite3
from typing import Any
from uuid import UUID

from ..compat_embedding_reader import NativeCompatEmbeddingReader
from ..errors import SubstrateInvariantViolation
from ..ids import native_id_to_bytes
from ..native_memory_vector_runtime import (
    NativeMemoryVectorRuntime,
    NativeMemoryVectorRuntimeConfiguration,
    NativeVectorReadConsistencyRefused,
)
from ..runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from ..runtime_semantic_admission import RUNTIME_SEMANTIC_ADMISSION_REFUSED


_LEGACY_CAPTURE = "LEGACY_EMBEDDING_CAPTURE"
_COMPAT_EMBEDDING = "COMPAT_EMBEDDING"
_LEGACY_R1 = "LEGACY_PREDECESSOR_UNKNOWN"
_UNKNOWN = "UNKNOWN"
_RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
_READY = "READY"
_USABLE = "USABLE"


@dataclass(frozen=True)
class CertifiedRefusalRuntimeSource:
    """One B1 R1 memory that was terminally certified as B2-refused."""

    eid: int
    object_id: UUID
    r1_revision_id: UUID
    scope: NativeMemoryRuntimeScope


@dataclass(frozen=True)
class CertifiedRefusalRuntimeNegativeProof:
    """Separated evidence and runtime facts for a refusal set."""

    certified_refusal_memory_count: int
    legacy_current_r1_count: int
    native_ordinary_successor_count: int
    legacy_evidence_capture_count: int
    certified_refusal_with_no_capture_count: int
    other_representation_count: int
    runtime_compat_embedding_count: int
    ready_usable_runtime_representation_count: int
    qualified_embedding_reader_none_count: int
    qualified_embedding_reader_refusal_count: int
    qualified_embedding_reader_result_count: int
    qualified_embedding_reader_unexpected_error_count: int
    native_vector_candidate_count: int
    native_vector_search_hit_count: int
    native_vector_search_refusal_count: int

    def identity_payload(self) -> dict[str, int]:
        """Return a JSON-safe accounting record for a rehearsal carrier."""

        return asdict(self)


class CertifiedRefusalRuntimeProofFailed(SubstrateInvariantViolation):
    """The audit found a non-evidence runtime shape on a refused memory."""

    def __init__(self, proof: CertifiedRefusalRuntimeNegativeProof) -> None:
        self.proof = proof
        # ``observed`` makes this safe for a stop-oriented rehearsal runner to
        # record without string parsing.
        self.observed = proof.identity_payload()
        super().__init__(
            "CERTIFIED_REFUSAL_RUNTIME_REPRESENTATION_LEAK: " + repr(self.observed)
        )


def prove_certified_refusal_runtime_negative(
    connection: sqlite3.Connection,
    *,
    sources: tuple[CertifiedRefusalRuntimeSource, ...],
    native_core_database_path: str | Path,
    expected_native_core_id: UUID,
    representation_lane: NativeRepresentationLane,
    vector_embedder: Any,
    search_query: str = "certified-refusal-runtime-negative-proof",
) -> CertifiedRefusalRuntimeNegativeProof:
    """Prove that certified refusals retain only lawful historical evidence.

    The proof deliberately counts legacy evidence separately from native
    runtime representations.  It also exercises both runtime reader owners;
    metadata alone is not accepted as evidence of runtime exclusion.
    """

    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("certified-refusal proof requires a SQLite connection")
    if not isinstance(sources, tuple) or not sources:
        raise ValueError("certified-refusal proof requires a non-empty source tuple")
    if not isinstance(expected_native_core_id, UUID):
        raise ValueError("certified-refusal proof requires an expected native core UUID")
    if not isinstance(representation_lane, NativeRepresentationLane):
        raise ValueError("certified-refusal proof requires a native representation lane")
    if not isinstance(search_query, str) or not search_query.strip():
        raise ValueError("certified-refusal proof search query must be non-empty")
    if len({(item.scope.legacy_source_namespace_id, item.eid) for item in sources}) != len(sources):
        raise ValueError("certified-refusal sources must have unique scope-local EIDs")
    if len({item.object_id for item in sources}) != len(sources):
        raise ValueError("certified-refusal sources must have unique object IDs")
    if not all(isinstance(item, CertifiedRefusalRuntimeSource) for item in sources):
        raise ValueError("certified-refusal proof sources must be typed")

    legacy_current = 0
    native_ordinary = 0
    legacy_captures = 0
    other_representations = 0
    runtime_compat_embeddings = 0
    ready_usable = 0
    sources_with_capture: set[UUID] = set()

    for source in sources:
        current = connection.execute(
            """SELECT r.lineage_kind,o.current_revision_id,o.current_revision_ordinal
                 FROM objects o
                 JOIN object_revisions r ON r.object_revision_id=o.current_revision_id
                WHERE o.object_id=?""",
            (native_id_to_bytes(source.object_id),),
        ).fetchone()
        if current == (_LEGACY_R1, native_id_to_bytes(source.r1_revision_id), 1):
            legacy_current += 1
        native_ordinary += connection.execute(
            """SELECT count(*) FROM object_revisions
                 WHERE object_id=? AND lineage_kind='NATIVE_ORDINARY'""",
            (native_id_to_bytes(source.object_id),),
        ).fetchone()[0]

        rows = connection.execute(
            """SELECT r.representation_id,r.source_kind,r.source_object_revision_id,
                       r.source_object_revision_ordinal,r.representation_class,
                       state.readiness,state.operational_disposition
                  FROM representations r
                  JOIN representation_current_state state USING(representation_id)
                 WHERE r.source_object_id=?""",
            (native_id_to_bytes(source.object_id),),
        ).fetchall()
        for representation_id, source_kind, revision_id, ordinal, representation_class, readiness, disposition in rows:
            exact_capture = (
                source_kind == "OBJECT_REVISION"
                and revision_id == native_id_to_bytes(source.r1_revision_id)
                and ordinal == 1
                and representation_class == _LEGACY_CAPTURE
                and readiness == _UNKNOWN
                and disposition == _RECONCILIATION_REQUIRED
                and _is_legacy_representation_admission(connection, representation_id)
                and _representation_integrity_counts(connection, representation_id) == (0, 0, None)
            )
            if exact_capture:
                legacy_captures += 1
                sources_with_capture.add(source.object_id)
            else:
                other_representations += 1
            if representation_class == _COMPAT_EMBEDDING:
                runtime_compat_embeddings += 1
            if readiness == _READY and disposition == _USABLE:
                ready_usable += 1

    reader_none = reader_refusal = reader_result = reader_unexpected = 0
    reader = NativeCompatEmbeddingReader(connection)
    for source in sources:
        try:
            result = reader.read_current(
                source.object_id, expected_dimension=representation_lane.dimension,
            )
        except SubstrateInvariantViolation as exc:
            if str(exc) == RUNTIME_SEMANTIC_ADMISSION_REFUSED:
                reader_refusal += 1
            else:
                reader_unexpected += 1
        else:
            if result is None:
                reader_none += 1
            else:
                reader_result += 1

    vector_candidates = vector_hits = vector_refusals = 0
    for scope, scoped_sources in _sources_by_scope(sources):
        object_ids = {item.object_id for item in scoped_sources}
        eids = {item.eid for item in scoped_sources}
        configuration = NativeMemoryVectorRuntimeConfiguration(
            core_database_path=native_core_database_path,
            expected_core_id=expected_native_core_id,
            scope=scope,
            representation_lane=representation_lane,
        )
        with NativeMemoryVectorRuntime(configuration, embedder=vector_embedder) as runtime:
            candidates = runtime._enumerate_qualified_vectors()
            vector_candidates += len(set(candidates).intersection(object_ids))
            try:
                # ``top_k`` covers every qualified row in this scoped cache,
                # so an omitted refused EID cannot be hidden by ranking.
                hits = runtime.search(search_query, top_k=100_000)
            except NativeVectorReadConsistencyRefused:
                vector_refusals += 1
            else:
                vector_hits += len({int(item["eid"]) for item in hits}.intersection(eids))

    proof = CertifiedRefusalRuntimeNegativeProof(
        certified_refusal_memory_count=len(sources),
        legacy_current_r1_count=legacy_current,
        native_ordinary_successor_count=native_ordinary,
        legacy_evidence_capture_count=legacy_captures,
        certified_refusal_with_no_capture_count=len(sources) - len(sources_with_capture),
        other_representation_count=other_representations,
        runtime_compat_embedding_count=runtime_compat_embeddings,
        ready_usable_runtime_representation_count=ready_usable,
        qualified_embedding_reader_none_count=reader_none,
        qualified_embedding_reader_refusal_count=reader_refusal,
        qualified_embedding_reader_result_count=reader_result,
        qualified_embedding_reader_unexpected_error_count=reader_unexpected,
        native_vector_candidate_count=vector_candidates,
        native_vector_search_hit_count=vector_hits,
        native_vector_search_refusal_count=vector_refusals,
    )
    if (
        proof.legacy_current_r1_count != proof.certified_refusal_memory_count
        or proof.native_ordinary_successor_count != 0
        or proof.other_representation_count != 0
        or proof.runtime_compat_embedding_count != 0
        or proof.ready_usable_runtime_representation_count != 0
        or proof.qualified_embedding_reader_result_count != 0
        or proof.qualified_embedding_reader_unexpected_error_count != 0
        or proof.qualified_embedding_reader_none_count + proof.qualified_embedding_reader_refusal_count
        != proof.certified_refusal_memory_count
        or proof.native_vector_candidate_count != 0
        or proof.native_vector_search_hit_count != 0
    ):
        raise CertifiedRefusalRuntimeProofFailed(proof)
    return proof


def _is_legacy_representation_admission(connection: sqlite3.Connection, representation_id: bytes) -> bool:
    rows = connection.execute(
        """SELECT transition.transition_kind,transition.origin_kind,operation.operation_kind
              FROM operation_outputs output
              JOIN operations operation ON operation.operation_id=output.operation_id
              JOIN semantic_transitions transition ON transition.operation_id=operation.operation_id
             WHERE output.output_kind='REPRESENTATION' AND output.representation_id=?""",
        (representation_id,),
    ).fetchall()
    return rows == [(
        "LEGACY_REPRESENTATION_ADMISSION", "LEGACY_ADMISSION", "ADMIT_LEGACY_EMBEDDING_EVIDENCE",
    )]


def _representation_integrity_counts(
    connection: sqlite3.Connection, representation_id: bytes,
) -> tuple[int, int, bytes | None]:
    expectation_count = connection.execute(
        """SELECT count(*) FROM integrity_expectations
             WHERE subject_kind='REPRESENTATION' AND representation_id=?""",
        (representation_id,),
    ).fetchone()[0]
    measurement_count = connection.execute(
        """SELECT count(*) FROM integrity_measurements measurement
             JOIN integrity_expectations expectation ON expectation.expectation_id=measurement.expectation_id
             WHERE expectation.subject_kind='REPRESENTATION' AND expectation.representation_id=?""",
        (representation_id,),
    ).fetchone()[0]
    selected = connection.execute(
        "SELECT selected_integrity_measurement_id FROM representation_current_state WHERE representation_id=?",
        (representation_id,),
    ).fetchone()[0]
    return expectation_count, measurement_count, selected


def _sources_by_scope(
    sources: tuple[CertifiedRefusalRuntimeSource, ...],
) -> tuple[tuple[NativeMemoryRuntimeScope, tuple[CertifiedRefusalRuntimeSource, ...]], ...]:
    grouped: dict[NativeMemoryRuntimeScope, list[CertifiedRefusalRuntimeSource]] = {}
    for source in sources:
        grouped.setdefault(source.scope, []).append(source)
    return tuple(
        (scope, tuple(sorted(items, key=lambda item: item.eid)))
        for scope, items in sorted(
            grouped.items(),
            key=lambda item: (
                item[0].workspace_id, item[0].scope_kind, item[0].qualifier,
            ),
        )
    )


__all__ = [
    "CertifiedRefusalRuntimeNegativeProof",
    "CertifiedRefusalRuntimeProofFailed",
    "CertifiedRefusalRuntimeSource",
    "prove_certified_refusal_runtime_negative",
]
