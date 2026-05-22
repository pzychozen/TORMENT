"""torment_service/lifecycle.py

Lifecycle envelope types for the Path C Q2 contract.

Per:

- ``docs/CLUSTER_5_PATH_C_GOVERNANCE_PRESERVATION_FRAMING_v0.1.md``
- ``docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md``

This module defines the Shape D hybrid canonical lifecycle envelope used to
carry per-memory lifecycle status on the row, with explicit "authoritative
on row vs. join-required" semantics.

Public surface:

- ``LifecycleStatus``       -- the envelope itself (top-level dataclass)
- ``LifecycleSetBy``        -- nested write-time provenance
- ``LifecycleJoinTarget``   -- nested side-channel pointer (when needed)
- ``LifecycleHistoryRef``   -- nested optional event-ledger pointer
- ``LifecycleState``        -- closed state vocabulary (str Enum)
- ``SideChannel``           -- closed side-channel vocabulary (str Enum)
- ``LifecycleActor``        -- closed actor vocabulary (str Enum)
- ``LifecycleSetVia``       -- closed write-mechanism vocabulary (str Enum)
- ``LifecycleStateError``   -- validation failure exception
- ``validate_lifecycle_envelope(d)`` -- canonical dict -> typed conversion

Q2 invariant: a consumer reading a memory row must be able to determine
its lifecycle state -- including whether the row is authoritative for
that state or whether a join to a named side channel is required --
without guessing.

Slice 0 commitment: this module is NOT yet load-bearing. No production
caller in ``torment_service/`` constructs, reads, or persists a
``LifecycleStatus``. The envelope vocabulary exists in code; subsequent
slices wire it into write sites, read sites, the protected dual-source
collapse, the review-queue join, and the migration shim.

Note on the ``ARCHIVED`` lifecycle state:
    ``LifecycleState.ARCHIVED`` is the **lifecycle stage** "this memory
    has been archived". It is structurally distinct from the
    ``torment_service/archive_memory.py`` subsystem, which is a separate
    document-chunk store. Consumers must not conflate the two.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Closed vocabularies (str Enums for JSON-friendly serialization)
# ---------------------------------------------------------------------------


class LifecycleState(str, Enum):
    """Closed set of lifecycle states per Q2-C decision table.

    Deferred states (committed, ratified, revised, deleted) are not part
    of this vocabulary at Slice 0 and may be added by a future ratified
    extension.
    """

    UNSET = "unset"
    SCRATCH = "scratch"
    RELEASED = "released"
    PROTECTED = "protected"
    REVIEW_PENDING = "review_pending"
    ACTIVE = "active"
    CONSUMED = "consumed"
    # ARCHIVED -- the LIFECYCLE STAGE. Distinct from the
    # ``torment_service/archive_memory.py`` document-chunk subsystem.
    ARCHIVED = "archived"


class SideChannel(str, Enum):
    """Closed set of named side channels per Q2-B Section 5.

    Semantic names -- the mapping to filesystem paths is a deployment
    concern deferred to Q2-E (review-queue join formalization).
    """

    REVIEW_QUEUE = "review_queue"
    CLOSURE_LEDGER = "closure_ledger"
    BATON_LEDGER = "baton_ledger"


class LifecycleActor(str, Enum):
    """Closed set of actors who can transition a memory's lifecycle."""

    OPERATOR = "operator"
    SYSTEM = "system"
    USER = "user"
    MIGRATION = "migration"


class LifecycleSetVia(str, Enum):
    """Closed set of mechanisms by which a lifecycle state was set."""

    UNSET_DEFAULT = "unset_default"
    INGEST = "ingest"
    INGEST_UNMARKED = "ingest_unmarked"
    API = "api"
    MIGRATION = "migration"
    GATE1_REFUSAL = "gate1_refusal"
    REVIEW_RATIFICATION = "review_ratification"
    SCRATCH_PROMOTION = "scratch_promotion"
    RELEASE_PROMOTION = "release_promotion"
    CANON_SET = "canon_set"
    TIER_SET = "tier_set"
    SRG_CRYSTAL = "srg_crystal"
    GOVERNANCE_FLAG = "governance_flag"
    SEED_PLANT = "seed_plant"
    BATON_CONSUME = "baton_consume"


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class LifecycleStateError(ValueError):
    """Raised when a lifecycle envelope fails validation.

    Inherits from ``ValueError`` because the failure is a shape/content
    contract violation. The exception carries the offending field name and
    a short reason code so callers and audit logs can identify the
    failure without re-inspecting the input.

    Attributes
    ----------
    field : str
        The field path that failed (e.g., ``"state"``, ``"set_by.via"``).
    reason : str
        Short reason code (e.g., ``"unknown_value"``, ``"missing"``,
        ``"must_be_bool"``).
    """

    def __init__(self, field: str, reason: str, detail: str = "") -> None:
        self.field = str(field)
        self.reason = str(reason)
        msg = f"LifecycleStateError on {self.field!r}: {self.reason}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Nested types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class LifecycleSetBy:
    """Write-time provenance for a lifecycle transition.

    All three fields (``actor``, ``via``, ``at``) are required and non-null.
    """

    actor: LifecycleActor
    via: LifecycleSetVia
    at: int

    def __post_init__(self) -> None:
        if not isinstance(self.actor, LifecycleActor):
            raise LifecycleStateError(
                "set_by.actor", "invalid_type",
                f"expected LifecycleActor, got {type(self.actor).__name__}",
            )
        if not isinstance(self.via, LifecycleSetVia):
            raise LifecycleStateError(
                "set_by.via", "invalid_type",
                f"expected LifecycleSetVia, got {type(self.via).__name__}",
            )
        # bool is a subclass of int in Python -- explicitly exclude.
        if not isinstance(self.at, int) or isinstance(self.at, bool):
            raise LifecycleStateError(
                "set_by.at", "must_be_int",
                f"got {type(self.at).__name__}",
            )
        if self.at < 0:
            raise LifecycleStateError(
                "set_by.at", "must_be_non_negative",
                f"got {self.at}",
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor": self.actor.value,
            "via": self.via.value,
            "at": int(self.at),
        }

    @classmethod
    def from_dict(cls, d: Any) -> "LifecycleSetBy":
        if not isinstance(d, dict):
            raise LifecycleStateError(
                "set_by", "not_a_dict",
                f"got {type(d).__name__}",
            )
        for key in ("actor", "via", "at"):
            if key not in d or d[key] is None:
                raise LifecycleStateError(f"set_by.{key}", "missing")
        try:
            actor = LifecycleActor(d["actor"])
        except ValueError:
            raise LifecycleStateError(
                "set_by.actor", "unknown_value", str(d["actor"]),
            ) from None
        try:
            via = LifecycleSetVia(d["via"])
        except ValueError:
            raise LifecycleStateError(
                "set_by.via", "unknown_value", str(d["via"]),
            ) from None
        return cls(actor=actor, via=via, at=d["at"])


@dataclass(frozen=True, kw_only=True)
class LifecycleJoinTarget:
    """Named side channel + join key required to determine lifecycle truth.

    Carried in ``LifecycleStatus.requires_join`` when the row is NOT
    authoritative for the state.
    """

    side_channel: SideChannel
    join_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.side_channel, SideChannel):
            raise LifecycleStateError(
                "requires_join.side_channel", "invalid_type",
                f"expected SideChannel, got {type(self.side_channel).__name__}",
            )
        if not isinstance(self.join_key, str):
            raise LifecycleStateError(
                "requires_join.join_key", "must_be_string",
                f"got {type(self.join_key).__name__}",
            )
        if not self.join_key:
            raise LifecycleStateError(
                "requires_join.join_key", "empty_string",
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "side_channel": self.side_channel.value,
            "join_key": str(self.join_key),
        }

    @classmethod
    def from_dict(cls, d: Any) -> "LifecycleJoinTarget":
        if not isinstance(d, dict):
            raise LifecycleStateError(
                "requires_join", "not_a_dict",
                f"got {type(d).__name__}",
            )
        for key in ("side_channel", "join_key"):
            if key not in d or d[key] is None:
                raise LifecycleStateError(f"requires_join.{key}", "missing")
        try:
            side_channel = SideChannel(d["side_channel"])
        except ValueError:
            raise LifecycleStateError(
                "requires_join.side_channel", "unknown_value",
                str(d["side_channel"]),
            ) from None
        return cls(side_channel=side_channel, join_key=d["join_key"])


@dataclass(frozen=True, kw_only=True)
class LifecycleHistoryRef:
    """Optional pointer to an event ledger for lifecycle transition history.

    Carried in ``LifecycleStatus.history_ref`` when additional history is
    available (e.g., baton ledger for ``consumed``). Independent of
    ``requires_join`` -- the join target and the history target may name
    the same channel, different channels, or neither.
    """

    ledger: SideChannel
    last_event_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.ledger, SideChannel):
            raise LifecycleStateError(
                "history_ref.ledger", "invalid_type",
                f"expected SideChannel, got {type(self.ledger).__name__}",
            )
        if not isinstance(self.last_event_id, str):
            raise LifecycleStateError(
                "history_ref.last_event_id", "must_be_string",
                f"got {type(self.last_event_id).__name__}",
            )
        if not self.last_event_id:
            raise LifecycleStateError(
                "history_ref.last_event_id", "empty_string",
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ledger": self.ledger.value,
            "last_event_id": str(self.last_event_id),
        }

    @classmethod
    def from_dict(cls, d: Any) -> "LifecycleHistoryRef":
        if not isinstance(d, dict):
            raise LifecycleStateError(
                "history_ref", "not_a_dict",
                f"got {type(d).__name__}",
            )
        for key in ("ledger", "last_event_id"):
            if key not in d or d[key] is None:
                raise LifecycleStateError(f"history_ref.{key}", "missing")
        try:
            ledger = SideChannel(d["ledger"])
        except ValueError:
            raise LifecycleStateError(
                "history_ref.ledger", "unknown_value", str(d["ledger"]),
            ) from None
        return cls(ledger=ledger, last_event_id=d["last_event_id"])


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class LifecycleStatus:
    """The canonical Path C Q2 lifecycle envelope.

    Carried on memory payloads under the ``lifecycle_status`` key. The
    envelope announces, on the row itself, both the canonical current
    lifecycle state and whether the row is authoritative for that state.
    When the row is not authoritative, ``requires_join`` names the side
    channel that holds the authoritative answer.

    Invariants enforced at ``__post_init__``:

    1. ``state`` is a ``LifecycleState`` enum member.
    2. ``is_authoritative_on_row`` is a Python ``bool``.
    3. ``set_by`` is a ``LifecycleSetBy`` (required, never None).
    4. ``requires_join`` is either None or a ``LifecycleJoinTarget``.
    5. ``history_ref`` is either None or a ``LifecycleHistoryRef``.
    6. Complementarity:

       - ``is_authoritative_on_row=True`` implies ``requires_join is None``
       - ``is_authoritative_on_row=False`` implies ``requires_join`` is a
         populated ``LifecycleJoinTarget``.

    State-to-authority pairing (e.g., "``state=REVIEW_PENDING`` must have
    ``is_authoritative_on_row=False``") is NOT enforced at Slice 0; it
    is a write-site policy deferred to later wiring slices.
    """

    state: LifecycleState
    is_authoritative_on_row: bool
    requires_join: Optional[LifecycleJoinTarget]
    set_by: LifecycleSetBy
    history_ref: Optional[LifecycleHistoryRef]

    def __post_init__(self) -> None:
        if not isinstance(self.state, LifecycleState):
            raise LifecycleStateError(
                "state", "invalid_type",
                f"expected LifecycleState, got {type(self.state).__name__}",
            )
        if not isinstance(self.is_authoritative_on_row, bool):
            raise LifecycleStateError(
                "is_authoritative_on_row", "must_be_bool",
                f"got {type(self.is_authoritative_on_row).__name__}",
            )
        if not isinstance(self.set_by, LifecycleSetBy):
            raise LifecycleStateError(
                "set_by", "invalid_type",
                f"expected LifecycleSetBy, got {type(self.set_by).__name__}",
            )
        if self.requires_join is not None and not isinstance(
            self.requires_join, LifecycleJoinTarget
        ):
            raise LifecycleStateError(
                "requires_join", "invalid_type",
                f"expected LifecycleJoinTarget or None, "
                f"got {type(self.requires_join).__name__}",
            )
        if self.history_ref is not None and not isinstance(
            self.history_ref, LifecycleHistoryRef
        ):
            raise LifecycleStateError(
                "history_ref", "invalid_type",
                f"expected LifecycleHistoryRef or None, "
                f"got {type(self.history_ref).__name__}",
            )
        # Complementarity (the load-bearing invariant)
        if self.is_authoritative_on_row and self.requires_join is not None:
            raise LifecycleStateError(
                "requires_join",
                "must_be_null_when_authoritative",
                "is_authoritative_on_row=True implies requires_join=None",
            )
        if (not self.is_authoritative_on_row) and self.requires_join is None:
            raise LifecycleStateError(
                "requires_join",
                "must_be_populated_when_not_authoritative",
                "is_authoritative_on_row=False implies requires_join is required",
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the envelope to a canonical dict.

        Enum-typed fields produce their ``.value`` (string) form, never
        their ``Enum.NAME`` representation, for JSON compatibility.
        """
        return {
            "state": self.state.value,
            "is_authoritative_on_row": bool(self.is_authoritative_on_row),
            "requires_join": (
                self.requires_join.to_dict()
                if self.requires_join is not None
                else None
            ),
            "set_by": self.set_by.to_dict(),
            "history_ref": (
                self.history_ref.to_dict()
                if self.history_ref is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, d: Any) -> "LifecycleStatus":
        """Construct a ``LifecycleStatus`` from a dict, via the validator.

        Equivalent to ``validate_lifecycle_envelope(d)``.
        """
        return validate_lifecycle_envelope(d)


# ---------------------------------------------------------------------------
# Module-level validator
# ---------------------------------------------------------------------------


_REQUIRED_TOP_LEVEL = (
    "state",
    "is_authoritative_on_row",
    "requires_join",
    "set_by",
    "history_ref",
)


def validate_lifecycle_envelope(d: Any) -> LifecycleStatus:
    """Canonical dict -> ``LifecycleStatus`` conversion.

    Validates every invariant defined by the Q2 framing and returns a
    typed ``LifecycleStatus`` instance. Raises ``LifecycleStateError`` on
    any validation failure. The exception carries the offending field
    name and a reason code.

    This is the single canonical entry point for converting payload
    dicts into typed envelopes. Callers should not bypass it.
    """
    if not isinstance(d, dict):
        raise LifecycleStateError(
            "lifecycle_status", "not_a_dict",
            f"got {type(d).__name__}",
        )

    for key in _REQUIRED_TOP_LEVEL:
        if key not in d:
            raise LifecycleStateError(key, "missing_required_key")

    # state
    try:
        state = LifecycleState(d["state"])
    except ValueError:
        raise LifecycleStateError(
            "state", "unknown_value", str(d["state"]),
        ) from None

    # is_authoritative_on_row
    auth = d["is_authoritative_on_row"]
    if not isinstance(auth, bool):
        raise LifecycleStateError(
            "is_authoritative_on_row", "must_be_bool",
            f"got {type(auth).__name__}",
        )

    # requires_join (nullable)
    rj_raw = d["requires_join"]
    requires_join: Optional[LifecycleJoinTarget]
    if rj_raw is None:
        requires_join = None
    else:
        requires_join = LifecycleJoinTarget.from_dict(rj_raw)

    # set_by (required, non-null)
    sb_raw = d["set_by"]
    if sb_raw is None:
        raise LifecycleStateError("set_by", "missing")
    set_by = LifecycleSetBy.from_dict(sb_raw)

    # history_ref (nullable)
    hr_raw = d["history_ref"]
    history_ref: Optional[LifecycleHistoryRef]
    if hr_raw is None:
        history_ref = None
    else:
        history_ref = LifecycleHistoryRef.from_dict(hr_raw)

    # Construct the envelope (its __post_init__ enforces complementarity).
    return LifecycleStatus(
        state=state,
        is_authoritative_on_row=auth,
        requires_join=requires_join,
        set_by=set_by,
        history_ref=history_ref,
    )
