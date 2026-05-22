"""torment_service/deep_hits.py

Wrapper types for the Shape B non-authoritative deep-retrieval contract.

Per Cluster 5 §9.3 Path C framing
(``docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md``) and the
Q1 implementation framing
(``docs/CLUSTER_5_PATH_C_Q1_IMPLEMENTATION_FRAMING_v0.1.md``):

DeepMemory derivatives are NOT authoritative. They are retrieval-grade echoes
of source-row memories held by ``MemoryGraph``. Authoritative use requires
explicit rehydration from the source row.

This module defines:

- ``NonAuthoritativeDeepHit``: abstract base type. Authority-bearing APIs
  reject any input that is an ``isinstance`` of this type.
- ``DeepRetrievalHit``: live, rehydratable retrieval echo. Returned to normal
  consumers by the β-filtered path at ``fabric._query_deep_lane`` (wiring
  deferred to a later slice).
- ``OrphanedDeepHit``: broken-pointer diagnostic-only record. The source row
  cannot be rehydrated. Returned only by α diagnostic surfaces.
- ``OrphanedAtRehydrateError``: raised when ``rehydrate()`` is called on a
  ``DeepRetrievalHit`` whose source row has disappeared between hit creation
  and the rehydrate call.

Serialized records always carry an ``authority_status`` block per the
field-marker contract (Phase 7 Step C)::

    {
        "authoritative": false,
        "requires_rehydration": true | false,
        "role": "retrieval_echo" | "orphaned_echo",
        "rehydration_blocked": <reason>   # orphan only
    }

Slice 0 commitment: this module is NOT yet load-bearing.
``fabric._query_deep_lane`` does not yet construct these wrappers.
Authority-bearing APIs do not yet import-and-reject. This module establishes
the vocabulary; subsequent slices wire it through the system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class OrphanedAtRehydrateError(Exception):
    """Raised when ``DeepRetrievalHit.rehydrate()`` is called but the source
    row has disappeared between hit creation and the rehydrate call.

    The exception carries the identity of the missing source row so callers
    can log or report the orphan condition without re-deriving it.
    """

    def __init__(self, source_eid: int, workspace_id: str, agent_id: str):
        self.source_eid = int(source_eid)
        self.workspace_id = str(workspace_id)
        self.agent_id = str(agent_id)
        super().__init__(
            f"Source row missing at rehydrate time: eid={self.source_eid} "
            f"workspace={self.workspace_id!r} agent={self.agent_id!r}"
        )


@dataclass(frozen=True, kw_only=True)
class NonAuthoritativeDeepHit:
    """Abstract base for non-authoritative deep-hit wrapper types.

    Concrete subtypes:

    - ``DeepRetrievalHit`` — live, rehydratable.
    - ``OrphanedDeepHit`` — broken pointer, diagnostic-only.

    Authority-bearing APIs reject any input where
    ``isinstance(x, NonAuthoritativeDeepHit)`` is True. This single
    rejection check covers all current and future non-authoritative
    subtypes.

    The four fields here are the immutable identity of a deep hit: the
    source EID, the workspace/agent scope, and the step at which the source
    was last seen via compression export.
    """

    source_eid: int
    workspace_id: str
    agent_id: str
    compressed_step: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize identity fields.

        Subclasses extend by calling ``super().to_dict()`` and merging
        their additional fields plus an ``authority_status`` block.
        """
        return {
            "source_eid": int(self.source_eid),
            "workspace_id": str(self.workspace_id),
            "agent_id": str(self.agent_id),
            "compressed_step": int(self.compressed_step),
        }


@dataclass(frozen=True, kw_only=True)
class DeepRetrievalHit(NonAuthoritativeDeepHit):
    """Live, rehydratable retrieval echo.

    Returned to normal consumers via the β-filtered path at
    ``fabric._query_deep_lane`` (wiring deferred to a later slice).

    The record carries retrieval-grade signal only. Authoritative use
    requires calling ``.rehydrate(memory_graph)`` to obtain the source row.

    Field names ``display_text`` and ``derivative_metadata`` deliberately
    encode their non-authoritative role; do not rename to ``summary`` or
    ``metadata`` without revisiting the contract.
    """

    similarity_score: float
    embedding_ref: Optional[Dict[str, Any]] = None
    display_text: Optional[str] = None
    derivative_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize live-retrieval shape with ``authority_status`` marker."""
        base = super().to_dict()
        base.update(
            {
                "similarity_score": float(self.similarity_score),
                "embedding_ref": (
                    dict(self.embedding_ref)
                    if self.embedding_ref is not None
                    else None
                ),
                "display_text": (
                    str(self.display_text)
                    if self.display_text is not None
                    else None
                ),
                "derivative_metadata": dict(self.derivative_metadata),
                "authority_status": {
                    "authoritative": False,
                    "requires_rehydration": True,
                    "role": "retrieval_echo",
                },
            }
        )
        return base

    def rehydrate(self, memory_graph: Any) -> Any:
        """Look up the authoritative source row by ``source_eid``.

        Parameters
        ----------
        memory_graph
            An object with an ``entities`` mapping keyed by EID. Typically
            a ``MemoryGraph`` instance, but loosely typed here so that
            Slice 0 does not import ``MemoryGraph`` and avoids coupling
            this module to that class.

        Returns
        -------
        Any
            The source-row entity for ``self.source_eid``. Loosely typed
            because the concrete entity class is not imported here.

        Raises
        ------
        OrphanedAtRehydrateError
            If the source row has disappeared between hit creation and
            this call (i.e., ``memory_graph.entities`` lacks
            ``self.source_eid``), or if ``memory_graph`` does not expose
            an ``entities`` mapping.
        """
        entities = getattr(memory_graph, "entities", None)
        if entities is None:
            raise OrphanedAtRehydrateError(
                self.source_eid, self.workspace_id, self.agent_id
            )
        entity = entities.get(self.source_eid)
        if entity is None:
            raise OrphanedAtRehydrateError(
                self.source_eid, self.workspace_id, self.agent_id
            )
        return entity


@dataclass(frozen=True, kw_only=True)
class OrphanedDeepHit(NonAuthoritativeDeepHit):
    """Broken-pointer record where the source row cannot be rehydrated.

    Returned ONLY by α diagnostic surfaces. Never reaches normal consumers
    because β filtering at ``fabric._query_deep_lane`` drops orphans before
    cognition sees them.

    Deliberately omits retrieval-useful fields (``similarity_score``,
    ``embedding_ref``, ``display_text``, ``derivative_metadata``).
    Operators inspecting an orphan cannot accidentally treat it as a
    retrieval result because the retrieval shape is structurally absent.

    Does NOT define ``rehydrate()``; calling it raises ``AttributeError``.
    This is enforced by class definition, not by runtime check.
    """

    orphan_reason: str
    detected_at: int

    def to_dict(self) -> Dict[str, Any]:
        """Serialize orphan-diagnostic shape with ``authority_status`` marker.

        ``rehydration_blocked`` in the marker mirrors ``orphan_reason`` on
        the dataclass. The dataclass field is the canonical source; the
        marker block is derived.
        """
        base = super().to_dict()
        base.update(
            {
                "orphan_reason": str(self.orphan_reason),
                "detected_at": int(self.detected_at),
                "authority_status": {
                    "authoritative": False,
                    "requires_rehydration": False,
                    "role": "orphaned_echo",
                    "rehydration_blocked": str(self.orphan_reason),
                },
            }
        )
        return base

# ---------------------------------------------------------------------------
# Authority guard (Shape B enforcement primitive)
# ---------------------------------------------------------------------------
#
# The wrapper-type contract (Step B) says authority-bearing APIs must reject
# any NonAuthoritativeDeepHit subtype. This guard is the standalone
# enforcement primitive. Authority-bearing APIs call
# ``assert_authoritative_memory(value)`` at entry; it raises
# ``NonAuthoritativeMemoryError`` if the value announces non-authoritative
# status.
#
# The guard is a NEGATIVE check: returning normally means the value is not
# structurally non-authoritative. It does NOT certify the value is
# authenticated authoritative memory -- that responsibility belongs to the
# source-row read via MemoryGraph.


class NonAuthoritativeMemoryError(TypeError):
    """Raised when a non-authoritative deep hit is passed where
    authoritative memory is required.

    Inherits from ``TypeError`` because the failure is a type contract
    violation: the caller passed a structurally non-authoritative value
    into an authority-bearing API.

    Diagnostic attributes carry the rejected value's identity so that
    callers, telemetry, and audit logs can trace the offending input
    without re-introspecting the wrapper:

    Attributes
    ----------
    received_type : type
        The concrete subtype of ``NonAuthoritativeDeepHit`` that was
        rejected (e.g., ``DeepRetrievalHit``, ``OrphanedDeepHit``).
    source_eid : int
        The source EID the rejected wrapper points to.
    role : str
        The wrapper's ``authority_status.role`` value
        (e.g., ``"retrieval_echo"``, ``"orphaned_echo"``). ``"unknown"``
        if the role cannot be extracted.
    """

    def __init__(self, value: "NonAuthoritativeDeepHit") -> None:
        self.received_type = type(value)
        try:
            self.source_eid = int(value.source_eid)
        except Exception:
            self.source_eid = -1
        try:
            self.role = str(value.to_dict()["authority_status"]["role"])
        except Exception:
            self.role = "unknown"
        super().__init__(
            f"Authoritative memory required, received "
            f"{self.received_type.__name__} "
            f"(role={self.role!r}, source_eid={self.source_eid}). "
            f"Call .rehydrate() to obtain the authoritative source row."
        )


def assert_authoritative_memory(value: object) -> None:
    """Raise ``NonAuthoritativeMemoryError`` if ``value`` is a
    non-authoritative deep-hit wrapper.

    Authority-bearing APIs call this at entry to reject any
    ``NonAuthoritativeDeepHit`` subtype. The check uses ``isinstance``
    against the abstract base class, so any current or future
    non-authoritative subtype is rejected by the same call.

    Note
    ----
    This is a **negative guard**. Returning normally means the value is
    not structurally non-authoritative. It does NOT certify the value
    is verified authoritative memory; authority verification is the
    source row's responsibility (``MemoryGraph``), not this helper.

    Parameters
    ----------
    value : object
        Any object. The helper only inspects whether it is a
        ``NonAuthoritativeDeepHit`` instance.

    Raises
    ------
    NonAuthoritativeMemoryError
        If ``value`` is an instance of ``NonAuthoritativeDeepHit``
        (any subtype).
    """
    if isinstance(value, NonAuthoritativeDeepHit):
        raise NonAuthoritativeMemoryError(value)
