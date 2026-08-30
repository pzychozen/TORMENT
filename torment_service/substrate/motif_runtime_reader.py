"""Read-only native motif runtime catalog and geometry boundary.

This module accepts an already-open qualified connection. It has no mutation,
allocation, routing, binding, or activation behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any
from uuid import UUID

import numpy as np

from ..motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifReadModel,
    _unit,
    motif_gravity_bonus,
)
from ..motif_geometry import motif_radius_from_member_vectors
from .compat_embedding_reader import NativeCompatEmbeddingReader
from .errors import SubstrateInvariantViolation, SubstrateObjectNotFound
from .ids import native_id_to_bytes
from .motifs import (
    DERIVED_MOTIF_OBJECT_KIND,
    MOTIF_ID_ALIAS_KIND,
    MOTIF_MEMBERSHIP_RELATIONSHIP_KIND,
    NativeMotifView,
    _state_from_payload,
)
from .schema import open_schema


_MEMORY_OBJECT_KIND = "LEGACY_CORE_NODE"
_REPRESENTATION_CLASS = "COMPAT_EMBEDDING"
_GENERATION = 1
_DERIVATION_CONTRACT = "compat-embedding-v1"
_ENCODING = "RAW_VECTOR"
_DTYPE = "float32"


class _ReadOnlyRepresentationPayloadReader:
    """Explicit payload boundary for this read-only runtime reader."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def read_representation_payload(self, representation_id: UUID) -> bytes:
        row = self._connection.execute(
            """
            SELECT p.payload_bytes
            FROM representation_payloads p
            JOIN representation_current_state state USING(representation_id)
            WHERE p.representation_id=?
              AND state.readiness='READY'
              AND state.operational_disposition='USABLE'
            """,
            (native_id_to_bytes(representation_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("usable representation payload was not found")
        return row[0]


@dataclass(frozen=True)
class NativeRuntimeMotif:
    """One current native motif paired with the decision-layer read model."""

    motif_object_id: UUID
    motif_revision_id: UUID
    motif_revision_ordinal: int
    semantic_scope_id: UUID
    read_model: MotifReadModel


@dataclass(frozen=True)
class NativeOrderedMotifMember:
    """A current membership with its recovered motif-publication sequence."""

    relationship_id: UUID
    relationship_revision_id: UUID
    relationship_revision_ordinal: int
    member_object_id: UUID
    member_semantic_scope_id: UUID
    motif_publication_ordinal: int


class NativeMotifRuntimeReader:
    """Read current ``DERIVED_MOTIF`` state without creating semantic state."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        open_schema(connection, writable=False)
        self._connection = connection
        self._representations = _ReadOnlyRepresentationPayloadReader(connection)
        self._compat_embeddings = NativeCompatEmbeddingReader(
            connection, payload_reader=self._representations
        )

    def list_runtime_motifs(
        self,
        *,
        motif_alias_namespace_id: UUID,
        domain_id: str,
        semantic_scope_id: UUID,
    ) -> tuple[NativeRuntimeMotif, ...]:
        """Seed runtime order from sorted scoped ``MOTIF_ID`` aliases."""
        _require_uuid("motif_alias_namespace_id", motif_alias_namespace_id)
        _nonempty_text("domain_id", domain_id)
        _require_uuid("semantic_scope_id", semantic_scope_id)

        alias_rows = self._connection.execute(
            """
            SELECT a.alias_value,a.object_id,o.object_kind
              FROM legacy_object_aliases a
              JOIN objects o ON o.object_id=a.object_id
             WHERE a.legacy_source_namespace_id=? AND a.alias_kind=?
             ORDER BY a.alias_value,a.object_id
            """,
            (native_id_to_bytes(motif_alias_namespace_id), MOTIF_ID_ALIAS_KIND),
        ).fetchall()
        aliases_by_object: dict[bytes, list[str]] = {}
        for alias_value, object_id, object_kind in alias_rows:
            if object_kind != DERIVED_MOTIF_OBJECT_KIND:
                raise SubstrateInvariantViolation(
                    "MOTIF_ID alias does not target a native derived motif"
                )
            aliases_by_object.setdefault(object_id, []).append(alias_value)
        rows = self._connection.execute(
            """
            SELECT o.object_id
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_kind=? AND r.effective_semantic_scope_id=?
            """,
            (DERIVED_MOTIF_OBJECT_KIND, native_id_to_bytes(semantic_scope_id)),
        ).fetchall()
        motifs: list[NativeRuntimeMotif] = []
        for (object_id,) in rows:
            aliases = aliases_by_object.get(object_id, [])
            if not aliases:
                raise SubstrateInvariantViolation(
                    "native motif has no MOTIF_ID alias in the requested runtime namespace"
                )
            if len(aliases) != 1:
                raise SubstrateInvariantViolation(
                    "native motif has multiple MOTIF_ID aliases in one runtime namespace"
                )
            alias_value = aliases[0]
            view = self._get_current_motif(UUID(bytes=object_id))
            state = view.state
            if state.runtime_motif_id != alias_value:
                raise SubstrateInvariantViolation(
                    "native motif runtime ID payload disagrees with its MOTIF_ID alias"
                )
            if state.domain_id != domain_id:
                raise SubstrateInvariantViolation(
                    "native motif payload domain does not match the requested runtime domain"
                )
            if state.semantic_scope_id != semantic_scope_id:
                raise SubstrateInvariantViolation(
                    "native motif semantic scope does not match the requested runtime scope"
                )
            members = self.list_ordered_current_motif_members(view.motif_object_id)
            motifs.append(
                NativeRuntimeMotif(
                    view.motif_object_id,
                    view.motif_revision_id,
                    view.revision_ordinal,
                    state.semantic_scope_id,
                    MotifReadModel(
                        state.runtime_motif_id,
                        state.domain_id,
                        state.label,
                        state.centroid,
                        state.strength,
                        len(members),
                        state.contributing_agents,
                        state.stability_score,
                        state.created_ts,
                        state.last_active_ts,
                    ),
                )
            )
        return tuple(sorted(motifs, key=lambda motif: motif.read_model.runtime_motif_id))

    def list_ordered_current_motif_members(
        self, motif_object_id: UUID
    ) -> tuple[NativeOrderedMotifMember, ...]:
        """Recover append sequence from shared membership/motif publication evidence."""
        _require_uuid("motif_object_id", motif_object_id)
        self._get_current_motif(motif_object_id)
        memberships = self._connection.execute(
            """
            SELECT h.relationship_id,r.relationship_revision_id,r.revision_ordinal,
                   member.object_id,member.endpoint_semantic_scope_id,member_object.object_kind
              FROM relationships h
              JOIN relationship_revisions r
                ON r.relationship_id=h.relationship_id
               AND r.relationship_revision_id=h.current_revision_id
               AND r.revision_ordinal=h.current_revision_ordinal
              JOIN relationship_revision_endpoints motif
                ON motif.relationship_revision_id=r.relationship_revision_id
               AND motif.endpoint_ordinal=0 AND motif.endpoint_role='MOTIF'
               AND motif.binding_mode='IDENTITY'
              JOIN relationship_revision_endpoints member
                ON member.relationship_revision_id=r.relationship_revision_id
               AND member.endpoint_ordinal=1 AND member.endpoint_role='MEMBER'
               AND member.binding_mode='IDENTITY'
              JOIN objects member_object ON member_object.object_id=member.object_id
             WHERE h.relationship_kind=? AND motif.object_id=?
            """,
            (MOTIF_MEMBERSHIP_RELATIONSHIP_KIND, native_id_to_bytes(motif_object_id)),
        ).fetchall()
        effects = self._connection.execute(
            """
            SELECT effect.relationship_id,effect.relationship_revision_id,
                   effect.relationship_revision_ordinal,effect.transition_id,
                   motif_effect.object_revision_ordinal
              FROM relationship_revision_effects effect
              JOIN object_revision_effects motif_effect
                ON motif_effect.transition_id=effect.transition_id
               AND motif_effect.object_id=?
            """,
            (native_id_to_bytes(motif_object_id),),
        ).fetchall()
        evidence: dict[tuple[bytes, bytes, int], tuple[bytes, int]] = {}
        for relationship_id, revision_id, ordinal, transition_id, motif_ordinal in effects:
            key = (relationship_id, revision_id, ordinal)
            if key in evidence:
                raise SubstrateInvariantViolation(
                    "current motif membership has ambiguous publication evidence"
                )
            evidence[key] = (transition_id, motif_ordinal)

        ordered: list[NativeOrderedMotifMember] = []
        seen_members: set[bytes] = set()
        seen_publication_ordinals: set[int] = set()
        for relationship_id, revision_id, ordinal, member_object_id, member_scope_id, member_kind in memberships:
            key = (relationship_id, revision_id, ordinal)
            item = evidence.get(key)
            if item is None:
                raise SubstrateInvariantViolation(
                    "current motif membership has no unambiguous motif publication evidence"
                )
            if member_kind != _MEMORY_OBJECT_KIND:
                raise SubstrateInvariantViolation(
                    "native motif membership does not target a LEGACY_CORE_NODE"
                )
            _, motif_ordinal = item
            if member_object_id in seen_members:
                raise SubstrateInvariantViolation(
                    "current motif memberships duplicate one member identity"
                )
            if motif_ordinal in seen_publication_ordinals:
                raise SubstrateInvariantViolation(
                    "current motif memberships share one publication ordinal"
                )
            seen_members.add(member_object_id)
            seen_publication_ordinals.add(motif_ordinal)
            ordered.append(
                NativeOrderedMotifMember(
                    UUID(bytes=relationship_id),
                    UUID(bytes=revision_id),
                    ordinal,
                    UUID(bytes=member_object_id),
                    UUID(bytes=member_scope_id),
                    motif_ordinal,
                )
            )
        return tuple(sorted(ordered, key=lambda member: member.motif_publication_ordinal))

    def read_current_compat_embedding(
        self, member_object_id: UUID, *, expected_dimension: int
    ) -> np.ndarray | None:
        """Read one current qualified raw float32 vector, or ``None`` if unavailable."""
        qualified = self._compat_embeddings.read_current(
            member_object_id, expected_dimension=expected_dimension
        )
        return None if qualified is None else qualified.float32_vector()

    def motif_radius(
        self, motif_object_id: UUID, *, expected_dimension: int
    ) -> float:
        """Calculate radius through the legacy-compatible member-unit-vector path."""
        _positive_dimension(expected_dimension)
        view = self._get_current_motif(motif_object_id)
        members = self.list_ordered_current_motif_members(motif_object_id)

        def legacy_unit_member_vectors():
            for member in members:
                raw_vector = self.read_current_compat_embedding(
                    member.member_object_id,
                    expected_dimension=expected_dimension,
                )
                yield None if raw_vector is None else _unit(raw_vector)

        return motif_radius_from_member_vectors(
            view.state.centroid,
            legacy_unit_member_vectors(),
        )

    def _get_current_motif(self, motif_object_id: UUID) -> NativeMotifView:
        """Read one current motif without constructing a write-capable service."""
        _require_uuid("motif_object_id", motif_object_id)
        row = self._connection.execute(
            """
            SELECT o.object_id,o.identity_namespace_id,o.object_kind,
                   r.object_revision_id,r.revision_ordinal,r.effective_semantic_scope_id,
                   r.payload_format,r.payload_text
              FROM objects o
              JOIN object_revisions r
                ON r.object_id=o.object_id
               AND r.object_revision_id=o.current_revision_id
               AND r.revision_ordinal=o.current_revision_ordinal
             WHERE o.object_id=?
            """,
            (native_id_to_bytes(motif_object_id),),
        ).fetchone()
        if row is None:
            raise SubstrateObjectNotFound("native motif was not found")
        if row[2] != DERIVED_MOTIF_OBJECT_KIND:
            raise SubstrateInvariantViolation("object is not a native derived motif")
        if row[6] != "JSON" or row[7] is None:
            raise SubstrateInvariantViolation("native motif current state is not JSON")
        return NativeMotifView(
            UUID(bytes=row[0]),
            UUID(bytes=row[3]),
            row[4],
            UUID(bytes=row[1]),
            _state_from_payload(UUID(bytes=row[5]), row[7]),
        )

    def project_coherence_field_rows(
        self,
        *,
        motif_alias_namespace_id: UUID,
        domain_id: str,
        expected_dimension: int,
        semantic_scope_id: UUID,
    ) -> list[dict[str, Any]]:
        """Project native counts, not fabricated member compatibility IDs."""
        motifs = self.list_runtime_motifs(
            motif_alias_namespace_id=motif_alias_namespace_id,
            domain_id=domain_id,
            semantic_scope_id=semantic_scope_id,
        )
        return [
            {
                "motif_id": motif.read_model.runtime_motif_id,
                "label": motif.read_model.label,
                "centroid": list(motif.read_model.centroid),
                "strength": motif.read_model.strength,
                "stability_score": motif.read_model.stability_score,
                "members": motif.read_model.member_count,
                "radius": self.motif_radius(
                    motif.motif_object_id, expected_dimension=expected_dimension
                ),
            }
            for motif in motifs
        ]

    def domain_centroid(
        self,
        *,
        motif_alias_namespace_id: UUID,
        domain_id: str,
        dimension: int,
        semantic_scope_id: UUID,
    ) -> np.ndarray:
        """Return the legacy-weighted centroid for current native read models."""
        _positive_dimension(dimension)
        motifs = self.list_runtime_motifs(
            motif_alias_namespace_id=motif_alias_namespace_id,
            domain_id=domain_id,
            semantic_scope_id=semantic_scope_id,
        )
        centroids: list[np.ndarray] = []
        weights: list[float] = []
        for motif in motifs:
            center = motif.read_model.centroid_np()
            if center.size != dimension:
                continue
            weight = max(1e-6, float(motif.read_model.strength)) * (
                1.0
                + motif_gravity_bonus(
                    motif.read_model, CURRENT_MOTIF_DECISION_POLICY
                )
            )
            centroids.append(center)
            weights.append(weight)
        if not centroids:
            return np.zeros(dimension, dtype=np.float32)
        W = np.asarray(weights, dtype=np.float32)
        C = np.vstack(centroids)
        return _unit((C * W[:, None]).sum(axis=0) / (W.sum() + 1e-12))


def _require_uuid(field: str, value: Any) -> None:
    if not isinstance(value, UUID):
        raise ValueError(f"{field} must be a UUID")


def _nonempty_text(field: str, value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be non-empty text")


def _positive_dimension(value: Any) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError("expected dimension must be a positive integer")
