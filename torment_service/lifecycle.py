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
- ``read_lifecycle_envelope(payload, *, now=None)`` -- read-side migration
  shim; returns the validated envelope from a payload, or a canonical
  UNSET envelope when the payload predates Q2.
- ``NonAuthoritativeLifecycleError``  -- raised when a non-row-authoritative
  envelope is passed to the Q2-F enforcement primitive at a decision
  boundary.
- ``assert_lifecycle_row_authoritative(envelope)`` -- Q2-F enforcement
  primitive; raises when the envelope announces a side-channel join is
  required, returns ``None`` when the row is authoritative for its own
  lifecycle answer.
- ``derive_protected_lifecycle_from_legacy_markers(payload, *, now=None)``
  -- Q2-D Slice 1 derivation: returns a row-authoritative PROTECTED
  envelope when legacy protected markers (canon, kind, tier,
  srg.is_crystal, governance.protected) are present; returns ``None``
  otherwise. Helper-only -- production wiring into the H1a read shim,
  the H1c write stamp, and existing protected readers is deferred to
  later Q2-D slices.
- ``LifecycleDisagreementKind``        -- closed set of legacy-marker
  disagreement categories detected by Q2-D Slice 4
  (``STATE_MISMATCH``, ``AUTHORITY_MISMATCH``). ``PROVENANCE_DRIFT``
  is deliberately not in this slice's vocabulary.
- ``LifecycleLegacyMarkerDisagreement`` -- structured report returned
  by the Q2-D Slice 4 detector when an explicit lifecycle envelope
  conflicts with what legacy protected markers would derive for the
  same payload.
- ``detect_lifecycle_legacy_marker_disagreement(payload)`` -- Q2-D
  Slice 4 detection helper; returns a structured disagreement report
  when a load-bearing conflict is present, or ``None`` otherwise.
  Never mutates the payload, never raises on disagreement (returns
  it). Helper-only -- production wiring into the H1b inspector,
  write-side raising, or reader migration is deferred to later
  separately-ratified slices.

Q2 invariant: a consumer reading a memory row must be able to determine
its lifecycle state -- including whether the row is authoritative for
that state or whether a join to a named side channel is required --
without guessing.

Slice 0 / H1a commitment: this module is NOT yet load-bearing. No
production caller in ``torment_service/`` constructs, reads, or persists
a ``LifecycleStatus``. The envelope vocabulary and the read-side
migration shim exist in code; subsequent slices wire them into write
sites, read sites, the protected dual-source collapse, and the
review-queue join.

Note on the ``ARCHIVED`` lifecycle state:
    ``LifecycleState.ARCHIVED`` is the **lifecycle stage** "this memory
    has been archived". It is structurally distinct from the
    ``torment_service/archive_memory.py`` subsystem, which is a separate
    document-chunk store. Consumers must not conflate the two.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union


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


# ---------------------------------------------------------------------------
# Read-side migration shim (Q2-H1a)
# ---------------------------------------------------------------------------


def read_lifecycle_envelope(
    payload: Dict[str, Any],
    *,
    now: Optional[int] = None,
) -> LifecycleStatus:
    """Read a lifecycle envelope from a memory payload, lazily deriving for legacy rows.

    Q2-H1a migration shim, extended by Q2-D Slice 2 to recognize legacy
    protected markers on rows that pre-date the Q2 lifecycle envelope.
    Produces a deterministic typed envelope for every legal payload so
    consumers can read lifecycle state through a single entry point
    without guessing whether the row is pre- or post-Q2.

    Behavior -- three branches:

    1. If ``payload`` is not a dict, raise
       ``LifecycleStateError(field="payload", reason="not_a_dict")``.
       (Unchanged from H1a.)

    2. If ``payload["lifecycle_status"]`` is present and non-null, it is
       passed through :func:`validate_lifecycle_envelope` and the typed
       result is returned. The validator's ``LifecycleStateError`` is
       **not caught** -- a malformed envelope is a real data-integrity
       signal and must propagate, not be silently downgraded to UNSET
       or rerouted to a derived envelope. **Explicit envelope wins**:
       legacy protected markers on the same payload are NOT consulted
       in this branch, even if they would derive a different state.
       Silent disagreement is acceptable for Slice 2; detection of
       explicit-vs-legacy conflicts is deferred to Q2-D Slice 4.

    3. If ``payload["lifecycle_status"]`` is absent or explicitly
       ``None``:

       a. Q2-D Slice 2 -- first call
          :func:`derive_protected_lifecycle_from_legacy_markers` to see
          whether any of the five legacy protected markers (canon, kind,
          tier, srg.is_crystal, governance.protected) is present. If the
          derivation returns a ``LifecycleStatus``, that derived
          envelope is returned. This prevents legacy on-disk rows with
          protected markers from being misread as plain UNSET (Hazard
          A from the Q2-D plan).

       b. Otherwise fall back to the canonical H1a UNSET envelope:
          ``state=UNSET``, ``is_authoritative_on_row=True``,
          ``set_by.actor=MIGRATION``, ``set_by.via=UNSET_DEFAULT``,
          ``requires_join=None``, ``history_ref=None``. Missing-key and
          explicit-``None`` continue to be treated identically.

    The shim **never mutates** ``payload``. The returned envelope
    (whether validated, derived, or UNSET) is a read-time
    interpretation, not persistence.

    Out of scope at this slice (Q2-D Slice 2):

    * The H1c write stamp (``_ensure_lifecycle_envelope``) is NOT
      modified. New rows written via ``MemoryGraph.spawn_memory`` with
      legacy protected markers but no explicit envelope still get
      stamped UNSET at write time. Slice 3 addresses this (Hazard B).
    * Disagreement detection between an explicit envelope and legacy
      markers is NOT performed -- explicit wins silently. Slice 4
      addresses this (Hazard C).
    * Existing protected readers
      (``governance.is_compression_protected``,
      ``compression.derive_retention_tier``) continue to read legacy
      markers directly. Slice 5+ migrates them to consult the envelope
      with ``assert_lifecycle_row_authoritative`` at the boundary.

    Parameters
    ----------
    payload : dict
        The memory row dict. Must be a dict; other types raise.
    now : int, optional
        Unix timestamp recorded in the synthesized envelope's
        ``set_by.at``. Propagates to both the derived PROTECTED branch
        (3a) and the UNSET fallback branch (3b). When omitted, defaults
        to ``int(time.time())``. Tests should pass this explicitly for
        deterministic results. Ignored when the payload already carries
        a valid envelope (branch 2) -- the embedded envelope's own
        ``set_by.at`` is preserved.

    Returns
    -------
    LifecycleStatus
        Either the validated envelope from the payload (branch 2), the
        derived PROTECTED envelope from legacy markers (branch 3a), or
        the canonical UNSET migration-shim envelope (branch 3b).

    Raises
    ------
    LifecycleStateError
        If ``payload`` is not a dict, or if a present, non-null
        ``lifecycle_status`` fails validation.
    """
    if not isinstance(payload, dict):
        raise LifecycleStateError(
            "payload", "not_a_dict",
            f"got {type(payload).__name__}",
        )

    raw = payload.get("lifecycle_status")
    if raw is None:
        # Q2-D Slice 2: try legacy protected derivation first. If any of
        # the five legacy protected markers (canon, kind, tier,
        # srg.is_crystal, governance.protected) is present, return the
        # derived PROTECTED envelope so legacy rows are no longer
        # misread as plain UNSET. Hazard A from the Q2-D plan.
        derived = derive_protected_lifecycle_from_legacy_markers(
            payload, now=now,
        )
        if derived is not None:
            return derived
        # Otherwise fall back to canonical UNSET (existing H1a contract).
        at = now if now is not None else int(time.time())
        return LifecycleStatus(
            state=LifecycleState.UNSET,
            is_authoritative_on_row=True,
            requires_join=None,
            set_by=LifecycleSetBy(
                actor=LifecycleActor.MIGRATION,
                via=LifecycleSetVia.UNSET_DEFAULT,
                at=at,
            ),
            history_ref=None,
        )

    return validate_lifecycle_envelope(raw)


# ---------------------------------------------------------------------------
# Q2-F enforcement primitive
# ---------------------------------------------------------------------------
#
# Mirrors the Q1 ``assert_authoritative_memory`` pattern (see
# ``torment_service/deep_hits.py``). Negative guard: the primitive enforces
# only that the row's lifecycle answer can be trusted at face value. It
# does NOT certify that the state itself is approved, released, safe, or
# acceptable for any specific consumer use. State acceptance is consumer
# policy and stays a separate, per-consumer concern.


class NonAuthoritativeLifecycleError(TypeError):
    """Raised when a non-row-authoritative lifecycle envelope is passed to a
    decision-bearing consumer that requires a row-authoritative answer.

    Inherits from ``TypeError`` because the failure is a contract
    violation: the caller passed a structurally valid but
    non-row-authoritative envelope into a decision boundary that demands a
    row-authoritative answer. ``LifecycleStateError`` (subclass of
    ``ValueError``) is reserved for malformed envelopes -- a data
    problem; ``NonAuthoritativeLifecycleError`` is a contract problem
    ("the envelope is well-formed but you cannot decide from it alone").

    Diagnostic attributes carry the envelope's join target so callers,
    telemetry, and audit logs can identify the required side-channel
    pivot without re-inspecting the envelope:

    Attributes
    ----------
    state : str
        The envelope's ``state`` value (e.g., ``"review_pending"``).
    side_channel : str
        The name of the side channel that holds the authoritative
        answer (e.g., ``"review_queue"``).
    join_key : str
        The join key the consumer must use against the side channel
        (e.g., ``"eid"``).
    """

    def __init__(self, envelope: "LifecycleStatus") -> None:
        self.state = str(envelope.state.value)
        # ``requires_join`` is guaranteed populated when this error is
        # raised (the primitive only constructs this error after
        # confirming ``is_authoritative_on_row=False``, which the
        # envelope's complementarity invariant pairs with a populated
        # join target).
        self.side_channel = str(envelope.requires_join.side_channel.value)
        self.join_key = str(envelope.requires_join.join_key)
        super().__init__(
            f"Lifecycle row is not authoritative for state {self.state!r}; "
            f"consumer must join side channel "
            f"{self.side_channel!r} on key {self.join_key!r} before "
            f"making an authoritative lifecycle decision."
        )


def assert_lifecycle_row_authoritative(
    envelope: Union[LifecycleStatus, Dict[str, Any]],
) -> None:
    """Q2-F enforcement primitive: assert the lifecycle envelope can be used
    at face value, without a side-channel join.

    Mirrors the Q1 ``assert_authoritative_memory`` pattern. Decision-bearing
    consumers call this at entry to reject any envelope whose
    ``is_authoritative_on_row`` is ``False`` (the row announces that the
    consumer must join a named side channel before deciding).

    Negative guard. Returning normally means ONE thing:

        the row's lifecycle answer can be trusted at face value
        without a side-channel join.

    Returning normally does NOT mean:

        * the state is "released" or otherwise approved
        * the row is safe or acceptable for any specific consumer use
        * the state has been verified beyond what the envelope itself
          announces

    State acceptance ("is ``state=unset`` OK for my purpose?") is a
    separate consumer-policy concern and must NOT be mixed into this
    primitive. Consumers that require a particular state should write:

        assert_lifecycle_row_authoritative(env)         # Q2-F
        if env.state is not LifecycleState.RELEASED:    # consumer policy
            raise MyConsumerPolicyError(...)

    Parameters
    ----------
    envelope : LifecycleStatus or dict
        Either a typed ``LifecycleStatus`` instance, or a canonical
        envelope dict. Dicts are routed through
        :func:`validate_lifecycle_envelope` first; malformed dicts raise
        ``LifecycleStateError`` before any authoritativity check.
        ``None`` and non-dict / non-``LifecycleStatus`` inputs are
        programming errors and raise ``LifecycleStateError``. The
        primitive does NOT accept a payload (caller with a payload
        should run :func:`read_lifecycle_envelope` first).

    Raises
    ------
    LifecycleStateError
        If ``envelope`` is ``None``, is neither a ``LifecycleStatus`` nor
        a dict, or is a malformed envelope dict.
    NonAuthoritativeLifecycleError
        If ``envelope`` is a well-formed envelope whose
        ``is_authoritative_on_row`` is ``False`` (the row announces a
        side-channel join is required).
    """
    if envelope is None:
        raise LifecycleStateError(
            "envelope", "must_not_be_none",
            "pass a LifecycleStatus or envelope dict; for legacy "
            "payloads, run read_lifecycle_envelope(payload) first",
        )
    if isinstance(envelope, LifecycleStatus):
        typed = envelope
    elif isinstance(envelope, dict):
        # Validator raises LifecycleStateError on malformed dicts; we
        # deliberately do NOT catch and re-raise as
        # NonAuthoritativeLifecycleError. Malformed envelopes are a data
        # problem; authoritativity is a contract problem; the two error
        # paths must remain distinct.
        typed = validate_lifecycle_envelope(envelope)
    else:
        raise LifecycleStateError(
            "envelope", "invalid_type",
            f"expected LifecycleStatus or dict, got "
            f"{type(envelope).__name__}",
        )
    if not typed.is_authoritative_on_row:
        raise NonAuthoritativeLifecycleError(typed)


# ---------------------------------------------------------------------------
# Q2-D Slice 1: protected dual-source derivation
# ---------------------------------------------------------------------------
#
# Per docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md
# §9 R1, the system carries five independent legacy markers that today
# signal "this row is protected" in compression/governance code:
#
#     1. payload["canon"] is True                          -> CANON_SET
#     2. payload["kind"] in {seed, identity, core_identity}-> SEED_PLANT *
#        (or payload["type"] as fallback when "kind" absent)
#     3. payload["tier"] == "core_identity"                -> TIER_SET
#     4. payload["srg"]["is_crystal"] truthy               -> SRG_CRYSTAL
#     5. payload["governance"]["protected"] truthy         -> GOVERNANCE_FLAG
#
# This helper defines the Q2-D derivation law: given those legacy markers,
# what canonical Q2 LifecycleStatus envelope does the row "really" carry?
# It is the analog of H1a for the protected dimension specifically.
#
# Production wiring is deliberately deferred. This slice defines the law;
# later Q2-D slices apply it:
#   Slice 2: H1a read shim consults this derivation for legacy rows
#   Slice 3: H1c write stamp consults this derivation before defaulting
#            to UNSET
#   Slice 4: disagreement detection between supplied envelope and legacy
#            markers
#   Slice 5+: existing protected readers (is_compression_protected,
#             derive_retention_tier) start consulting the envelope, with
#             assert_lifecycle_row_authoritative at the boundary
#
# * Temporary legacy-marker mapping: SEED_PLANT is reused here for every
#   kind-based protected marker (seed, identity, core_identity) because
#   no clearer existing constant fits and the ratified Slice 1 scope
#   avoids adding new vocabulary. This is a denormalization for audit
#   purposes, not a semantic claim that every identity/core_identity row
#   was literally seed-planted. A future slice may introduce a dedicated
#   kind-based via if the audit story demands it.
#
# Precedence order matches ``compression.derive_retention_tier`` exactly,
# so the eventual reader migration (Slice 5+) can swap the legacy
# computation for the envelope-driven path without changing observable
# retention-tier output.


def derive_protected_lifecycle_from_legacy_markers(
    payload: Dict[str, Any],
    *,
    now: Optional[int] = None,
    actor: LifecycleActor = LifecycleActor.MIGRATION,
) -> Optional[LifecycleStatus]:
    """Derive a Q2 PROTECTED envelope from a memory payload's legacy markers.

    Q2-D Slice 1: defines the law for mapping pre-Q2 protected markers
    onto the Q2 lifecycle envelope vocabulary, without applying that law
    at any production read/write site.

    Inspection precedence (mirrors ``compression.derive_retention_tier``):

    1. ``payload["canon"] is True``                         -> CANON_SET
    2. ``payload["kind"]`` (fallback ``payload["type"]``)
       in ``{"seed", "identity", "core_identity"}``         -> SEED_PLANT
    3. ``payload["tier"] == "core_identity"``               -> TIER_SET
    4. ``payload["srg"]["is_crystal"]`` truthy              -> SRG_CRYSTAL
    5. ``payload["governance"]["protected"]`` truthy        -> GOVERNANCE_FLAG

    The first matching marker wins; remaining markers are not inspected.

    Behavior:

    * Returns ``None`` when NO legacy protected marker is present. Does
      not fall back to UNSET -- distinguishing "no protected derivation
      available" from "definitely unset" is structural and must remain
      the H1a shim's responsibility, not this helper's. Callers that
      want a non-None envelope for every payload should compose this
      helper with ``read_lifecycle_envelope`` explicitly.
    * Returns a row-authoritative ``LifecycleStatus`` with
      ``state=PROTECTED``, ``set_by.actor=MIGRATION``, ``set_by.via``
      set to the first matching marker's constant, and
      ``set_by.at = now if now is not None else int(time.time())``.
    * The ``actor`` keyword parameter controls the stamped
      ``set_by.actor``. Default ``LifecycleActor.MIGRATION`` reflects the
      Q2-D Slice 1 / Slice 2 read-time legacy interpretation use case
      (mirroring the H1a shim's actor choice). Q2-D Slice 3 write-side
      callers (the H1c ``_ensure_lifecycle_envelope`` stamp) pass
      ``LifecycleActor.SYSTEM`` to record that the envelope was assigned
      by the runtime at row-creation time rather than derived from
      legacy markers at read time. The two actors preserve a
      load-bearing audit distinction: was this PROTECTED interpretation
      inferred at read or asserted at write?
    * Does NOT consult ``payload["lifecycle_status"]``. Resolution of
      any disagreement between an explicit envelope and legacy markers
      is Q2-D Slice 4's concern.
    * Does NOT mutate ``payload``.

    On marker truth semantics:

    * ``canon``: strict ``is True`` -- matches the existing
      ``derive_retention_tier`` check. ``False``, ``None``, ``"yes"``,
      ``1`` do not trigger.
    * ``kind`` / ``type``: exact string membership in the protected
      set. Coerced via ``str(... or "")`` for None-safety.
    * ``tier``: exact string equality with ``"core_identity"``.
    * ``srg.is_crystal``: truthy (matches existing
      ``srg.get("is_crystal", False)``). ``srg`` must itself be a dict;
      non-dict ``srg`` is silently ignored (defensive).
    * ``governance.protected``: truthy (parallel to srg). ``governance``
      must be a dict; non-dict is silently ignored.

    Parameters
    ----------
    payload : dict
        The memory row dict. Must be a dict; other types raise.
    now : int, optional
        Unix timestamp to record in the synthesized ``set_by.at``.
        Defaults to ``int(time.time())``. Tests should pass this
        explicitly for deterministic results.
    actor : LifecycleActor, optional
        The actor to record in ``set_by.actor`` on the derived envelope.
        Defaults to ``LifecycleActor.MIGRATION`` (Q2-D Slice 1 / Slice 2
        read-time legacy interpretation). Q2-D Slice 3 write-side
        callers pass ``LifecycleActor.SYSTEM`` to mark the envelope as
        runtime-assigned at write time.

    Returns
    -------
    LifecycleStatus or None
        A row-authoritative PROTECTED envelope when any marker matched;
        otherwise ``None``.

    Raises
    ------
    LifecycleStateError
        If ``payload`` is not a dict.
    """
    if not isinstance(payload, dict):
        raise LifecycleStateError(
            "payload", "not_a_dict",
            f"got {type(payload).__name__}",
        )

    via: Optional[LifecycleSetVia] = None

    # 1. canon=True (strict)
    if payload.get("canon") is True:
        via = LifecycleSetVia.CANON_SET
    else:
        # 2. kind / type fallback (string membership)
        kind = str(payload.get("kind", payload.get("type", "")) or "")
        if kind in ("seed", "identity", "core_identity"):
            via = LifecycleSetVia.SEED_PLANT
        else:
            # 3. tier (string equality)
            tier = str(payload.get("tier", "") or "")
            if tier == "core_identity":
                via = LifecycleSetVia.TIER_SET
            else:
                # 4. srg.is_crystal (truthy; srg must be a dict)
                srg = payload.get("srg")
                if isinstance(srg, dict) and srg.get("is_crystal", False):
                    via = LifecycleSetVia.SRG_CRYSTAL
                else:
                    # 5. governance.protected (truthy; gov must be a dict)
                    gov = payload.get("governance")
                    if isinstance(gov, dict) and gov.get("protected", False):
                        via = LifecycleSetVia.GOVERNANCE_FLAG

    if via is None:
        return None

    at = now if now is not None else int(time.time())
    return LifecycleStatus(
        state=LifecycleState.PROTECTED,
        is_authoritative_on_row=True,
        requires_join=None,
        set_by=LifecycleSetBy(
            actor=actor,
            via=via,
            at=at,
        ),
        history_ref=None,
    )


# ---------------------------------------------------------------------------
# Q2-D Slice 4: explicit-envelope-vs-legacy-marker disagreement detection
# ---------------------------------------------------------------------------
#
# Per docs/CLUSTER_5_PATH_C_Q2_LIFECYCLE_IMPLEMENTATION_FRAMING_v0.1.md
# §9 R1 / Hazard C: a payload can carry BOTH an explicit
# ``lifecycle_status`` envelope AND legacy protected markers (canon,
# kind, tier, srg.is_crystal, governance.protected). Slice 2 (read
# shim) and Slice 3 (write stamp) both preserve the explicit envelope
# verbatim in that case -- the explicit-wins contract. But the system
# has had no way to even NOTICE when explicit and legacy disagree.
#
# This slice adds the detection law. It does NOT change any production
# behavior; it returns a structured report so future slices can decide
# whether to log, surface in observability (H1b inspector), warn at
# write time, or gate at read time.
#
# Disagreement taxonomy (closed at this slice):
#
#   STATE_MISMATCH      -- explicit envelope state != PROTECTED, while
#                          legacy markers derive PROTECTED. Both sides
#                          disagree about what stage the row is in.
#                          Strongest conflict. Example: explicit
#                          ``state=unset + canon=True``.
#
#   AUTHORITY_MISMATCH  -- explicit envelope state == PROTECTED, but
#                          the explicit envelope is NOT row-authoritative
#                          (announces a side-channel join is required).
#                          Legacy markers always derive a row-authoritative
#                          PROTECTED. The two sides disagree about
#                          whether the row alone can be trusted at face
#                          value. Example: explicit ``state=protected,
#                          is_authoritative_on_row=False`` + canon=True.
#
# Deliberately NOT a disagreement at this slice:
#
#   PROVENANCE_DRIFT    -- both sides agree on
#                          ``state=PROTECTED, is_authoritative_on_row=True``
#                          but record different ``set_by.via``. Audit-
#                          interesting; not decision-bearing. A future
#                          audit slice may surface drift if needed.
#
#   actor mismatch      -- Slice 3 deliberately introduced the
#                          MIGRATION-vs-SYSTEM distinction as an
#                          AUDIT FEATURE (read-side legacy interpretation
#                          vs write-side runtime assertion). Treating
#                          it as a disagreement would walk back Slice 3's
#                          design. The detector ignores actor.
# ---------------------------------------------------------------------------


class LifecycleDisagreementKind(str, Enum):
    """Closed set of legacy-marker disagreement categories detected by
    :func:`detect_lifecycle_legacy_marker_disagreement`.

    Q2-D Slice 4 vocabulary: two kinds, both load-bearing.

    * ``STATE_MISMATCH`` -- explicit envelope state is NOT PROTECTED
      while legacy markers derive PROTECTED. The two answers
      structurally disagree about what stage the row is in.
    * ``AUTHORITY_MISMATCH`` -- both sides agree state=PROTECTED but
      the explicit envelope is not row-authoritative (announces a
      side-channel join is required), while legacy markers always
      derive a row-authoritative PROTECTED. The two answers disagree
      about whether the row alone can be trusted.

    PROVENANCE_DRIFT (both sides agree state=PROTECTED row-authoritative
    but via differs) is deliberately NOT in this vocabulary at Slice 4.
    Both sides agree on the load-bearing facts; via differences are
    audit-interesting but not decision-bearing.
    """

    STATE_MISMATCH = "state_mismatch"
    AUTHORITY_MISMATCH = "authority_mismatch"


@dataclass(frozen=True, kw_only=True)
class LifecycleLegacyMarkerDisagreement:
    """Structured report of a conflict between an explicit lifecycle
    envelope and what legacy protected markers would derive for the
    same payload.

    Returned (not raised) by
    :func:`detect_lifecycle_legacy_marker_disagreement`. The helper
    produces this so consumers -- future H1b inspector enrichment,
    optional write-side warning, eventual protected-reader migration --
    can decide independently whether to log, surface in observability,
    raise, or short-circuit.

    The ``derived_state`` field is NOT included at Slice 4 because the
    Q2-D Slice 1 derivation helper currently only knows about PROTECTED.
    Adding ``derived_state`` later (if derivation extends to other
    states) is a non-breaking change.

    Attributes
    ----------
    kind : LifecycleDisagreementKind
        The category of disagreement detected.
    explicit_state : LifecycleState
        The state of the explicit envelope on the payload.
    explicit_is_authoritative_on_row : bool
        The ``is_authoritative_on_row`` flag of the explicit envelope.
    explicit_via : LifecycleSetVia
        The ``set_by.via`` of the explicit envelope (audit trail of
        how the explicit envelope was originally assigned).
    derived_via : LifecycleSetVia
        Which legacy marker won under the canonical precedence order
        (canon > kind/type > tier > srg.is_crystal > governance.protected).
    """

    kind: LifecycleDisagreementKind
    explicit_state: LifecycleState
    explicit_is_authoritative_on_row: bool
    explicit_via: LifecycleSetVia
    derived_via: LifecycleSetVia


def detect_lifecycle_legacy_marker_disagreement(
    payload: Dict[str, Any],
) -> Optional[LifecycleLegacyMarkerDisagreement]:
    """Detect a conflict between an explicit lifecycle envelope and
    what legacy protected markers would derive for the same payload.

    Q2-D Slice 4 detection law. The helper compares two answers about
    the same row:

    1. The explicit ``payload["lifecycle_status"]`` (if present and
       non-null), validated through :func:`validate_lifecycle_envelope`.
    2. The protected envelope derivable from legacy markers (canon,
       kind, tier, srg.is_crystal, governance.protected) via
       :func:`derive_protected_lifecycle_from_legacy_markers`.

    Returns a structured ``LifecycleLegacyMarkerDisagreement`` when the
    two answers conflict on a load-bearing fact, or ``None`` when no
    actionable disagreement exists.

    Returns ``None`` when:

    * payload has no explicit ``lifecycle_status`` (missing or explicit
      ``None``);
    * payload has an explicit valid envelope but no legacy protected
      markers;
    * BOTH the explicit envelope and the legacy markers agree on
      ``state=PROTECTED`` AND ``is_authoritative_on_row=True``, even if
      ``set_by.via`` differs -- provenance drift is NOT surfaced as a
      disagreement at this slice.

    Returns ``LifecycleLegacyMarkerDisagreement(kind=STATE_MISMATCH, ...)``
    when:

    * the explicit envelope's state is NOT ``PROTECTED``, and
    * legacy markers derive ``PROTECTED``.

    Returns ``LifecycleLegacyMarkerDisagreement(kind=AUTHORITY_MISMATCH, ...)``
    when:

    * the explicit envelope's state IS ``PROTECTED``, and
    * the explicit envelope is NOT row-authoritative (announces a
      side-channel join), and
    * legacy markers derive ``PROTECTED`` (which is always row-
      authoritative).

    Raises ``LifecycleStateError`` when:

    * ``payload`` is not a dict;
    * ``payload["lifecycle_status"]`` is present but malformed (the
      detector does NOT swallow malformation into a disagreement;
      corruption stays loud, same as everywhere else in Q2).

    Never mutates ``payload``. Never raises on disagreement (returns
    the report). The actor distinction between the read-side
    derivation (``MIGRATION``) and the write-side stamp (``SYSTEM``)
    is intentional and is NOT a disagreement; the detector ignores
    actor entirely.

    Parameters
    ----------
    payload : dict
        The memory row dict. Must be a dict; other types raise.

    Returns
    -------
    LifecycleLegacyMarkerDisagreement or None
        A structured disagreement report if a load-bearing conflict is
        detected, otherwise ``None``.

    Raises
    ------
    LifecycleStateError
        If ``payload`` is not a dict or if a present
        ``lifecycle_status`` fails validation.
    """
    if not isinstance(payload, dict):
        raise LifecycleStateError(
            "payload", "not_a_dict",
            f"got {type(payload).__name__}",
        )

    raw = payload.get("lifecycle_status")
    if raw is None:
        return None

    # Validate the explicit envelope. Malformed propagates as
    # LifecycleStateError -- we do NOT swallow corruption into a
    # disagreement report.
    explicit_env = validate_lifecycle_envelope(raw)

    # Derive the protected envelope from legacy markers. Returns None
    # when no marker is present; in that case there is nothing to
    # disagree with.
    derived_env = derive_protected_lifecycle_from_legacy_markers(payload)
    if derived_env is None:
        return None

    # Three branches:
    #   (a) explicit PROTECTED + row-authoritative -> agreement
    #       (provenance drift NOT surfaced)
    #   (b) explicit PROTECTED + NOT row-authoritative -> AUTHORITY_MISMATCH
    #   (c) explicit state != PROTECTED -> STATE_MISMATCH
    if explicit_env.state is LifecycleState.PROTECTED:
        if explicit_env.is_authoritative_on_row:
            # Both sides agree on the load-bearing facts. Any via
            # difference is provenance drift, deliberately not surfaced.
            return None
        return LifecycleLegacyMarkerDisagreement(
            kind=LifecycleDisagreementKind.AUTHORITY_MISMATCH,
            explicit_state=explicit_env.state,
            explicit_is_authoritative_on_row=False,
            explicit_via=explicit_env.set_by.via,
            derived_via=derived_env.set_by.via,
        )

    return LifecycleLegacyMarkerDisagreement(
        kind=LifecycleDisagreementKind.STATE_MISMATCH,
        explicit_state=explicit_env.state,
        explicit_is_authoritative_on_row=explicit_env.is_authoritative_on_row,
        explicit_via=explicit_env.set_by.via,
        derived_via=derived_env.set_by.via,
    )
