# torment_service/contest_record.py
"""ContestRecord — Track B v0.2 B2-S2 vocabulary + validation only.

B2-S2 vocabulary + validation only.

NOT load-bearing.
No production caller constructs, reads, writes, persists, resolves,
ranks, prompts, or applies ContestRecord.

No ledger writer.
No ledger reader.
No effective-authority resolver.

This module is the Slice-0 sidecar-memo vocabulary for a *future* Track B
v0.2 contest ledger. It mirrors the Q2 lifecycle Slice-0 posture
(``torment_service/lifecycle.py``): the closed vocabulary, the immutable
record, a deterministic pure validator, and pure dict/JSON serialization
exist in code; the runtime does not import, construct, read, persist, or
apply them. A mandatory AST conformance test
(``tests/test_contest_record_conformance_meta.py``) keeps this guarantee
executable by failing if any production module imports this one.

``ContestRecord`` is a *provisional working name* (Track B v0.2 framing
§13 #1), not a final public naming decision.

Doctrine anchor: a ``ContestRecord`` is a sidecar memo beside a memory. It
is not a command controlling character voice, response, identity, or
behavior. *Memory may shape context. Memory may not seize authority.*

Axis caution (framing §4): the authority-class ``ContestResult.RELEASED``
value (``"released"``) is NOT the lifecycle ``LifecycleState.RELEASED``
state. They are distinct axes with nearly opposite valence. This module
deliberately does not import ``LifecycleState`` and defines its own
contest-local vocabulary.

Parked here (NOT decided in B2-S2): ledger shape, persistence, target
existence lookup, ``candidate_handle`` -> eid binding, operator
authorization beyond the prohibition-only rule, operator-refuse live
enforcement, effective-authority resolution, counter-contest replay, a new
ProvenanceV1 ``source_type``, retrieval/prompt/cognition/MCP exposure.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Dict, Optional

from torment_service.provenance_v1 import ProvenanceV1


# ── eid numeric convention (grounded in local precedent) ────────────
#
# Memory entity ids (``eid``) are assigned monotonically starting at 1:
#   - ``kernel/seed_entities.py`` ``_next_id: int = 1`` (first assigned id)
#   - ``memory_graph.py`` loads with ``max_eid = 0`` then sets
#     ``_next_id = max_eid + 1`` (line ~599)
# A valid assigned eid is therefore a positive integer; 0 and negatives are
# never assigned. ``contested_eid`` is range-checked against this rule only.
# No existence lookup is performed (that is a future slice).
MIN_VALID_EID = 1


# ── Closed vocabularies (str, Enum for JSON-friendly serialization) ──


class ContestScope(str, Enum):
    """Closed scope vocabulary. ``WORKSPACE`` is declared-only; its runtime
    behavior is deferred."""

    AGENT = "agent"
    CHARACTER = "character"
    WORKSPACE = "workspace"


class ContestActor(str, Enum):
    """Closed actor vocabulary. ``USER`` is declared-only (deferred to
    Cluster 3); its runtime behavior is deferred."""

    AGENT = "agent"
    CHARACTER = "character"
    OPERATOR = "operator"
    USER = "user"


class ContestReasonClass(str, Enum):
    """Closed required-reason vocabulary (Track B v0.1)."""

    IDENTITY_CONFLICT = "identity_conflict"
    MATERIAL_DISAGREEMENT = "material_disagreement"
    SCOPE_CREEP = "scope_creep"
    AUDIT_CONCERN = "audit_concern"


class ContestResult(str, Enum):
    """Closed authority-class result vocabulary (framing §4 / §8).

    Authority-class axis ONLY. ``RELEASED`` here is the authority-class
    value ``"released"`` and is NOT ``LifecycleState.RELEASED``.
    """

    LOW_AUTHORITY = "low-authority"
    RELEASED = "released"
    AUDIT_ONLY = "audit-only"
    REFUSE = "refuse"


# ── Error type (lifecycle Slice-0 pattern) ──────────────────────────


class ContestRecordError(ValueError):
    """Raised when a ContestRecord fails validation.

    Inherits ``ValueError`` because the failure is a shape/content contract
    violation. Carries the offending ``field`` and a short ``reason`` code so
    callers and audit logs can identify the failure without re-inspecting
    the input.
    """

    def __init__(self, field: str, reason: str, detail: str = "") -> None:
        self.field = str(field)
        self.reason = str(reason)
        msg = f"ContestRecordError on {self.field!r}: {self.reason}"
        if detail:
            msg += f" ({detail})"
        super().__init__(msg)


# ── Internal pure helpers (no side effects) ─────────────────────────


def _is_uuid_shaped(value: Any) -> bool:
    """True iff ``value`` is a non-empty string parseable as a UUID."""
    if not isinstance(value, str) or not value:
        return False
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _coerce_enum(enum_cls: type, value: Any, field_name: str) -> Any:
    """Coerce a serialized value into an enum member, or raise."""
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        raise ContestRecordError(field_name, "unknown_value", str(value)) from None


def _coerce_provenance(value: Any) -> ProvenanceV1:
    """Reconstruct a ProvenanceV1 from a dict (or pass an instance through).

    Reuses ProvenanceV1 unchanged — its own validation decides validity, and
    its unknown-key behavior is NOT redesigned globally.

    Fail-closed boundary tightening (B2-S2): a serialized ``contest_provenance``
    dict must be an *already-canonical* ProvenanceV1 serialization.
    ``ProvenanceV1.from_dict()`` may synthesize defaults (``schema_version``,
    ``write_path``, ``created_at_ts``, ...) and silently drops unknown keys; if
    the reconstructed canonical form differs from the supplied dict, the input
    was partial, drifted, or carried ignored keys. We reject rather than accept
    a silently-completed nested provenance. This tightening lives only at the
    ContestRecord boundary; ProvenanceV1 behavior is unchanged.

    A direct, already-valid ``ProvenanceV1`` object is accepted unchanged.
    """
    if isinstance(value, ProvenanceV1):
        return value
    if isinstance(value, dict):
        try:
            prov = ProvenanceV1.from_dict(value)
        except ValueError as exc:
            raise ContestRecordError(
                "contest_provenance", "invalid_provenance", str(exc)
            ) from None
        if prov.to_dict() != value:
            raise ContestRecordError(
                "contest_provenance", "non_canonical_provenance",
                "nested provenance must be an exact canonical ProvenanceV1 "
                "serialization (no partial / drifted / silently-completed dict)",
            )
        return prov
    raise ContestRecordError(
        "contest_provenance", "invalid_type", type(value).__name__
    )


# ── Immutable record ────────────────────────────────────────────────


@dataclass(frozen=True, kw_only=True)
class ContestRecord:
    """A sidecar memo recording a contest of a memory's authority posture.

    Immutable. Reversal is a future counter-contest, never an edit. This
    Slice-0 record carries vocabulary + provenance only; it does not write,
    read, resolve, or apply anything.

    Required fields:
        contest_id, contest_scope, contestant_actor, contestant_id,
        reason_class, contest_result, original_memory_preserved,
        contest_provenance

    One-of-required target:
        exactly one of ``contested_eid`` / ``candidate_handle``

    ``created_at_step`` / ``session_id`` are intentionally NOT top-level
    fields in this slice — they are already carried by ``contest_provenance``
    (a ``ProvenanceV1``).
    """

    contest_id: str
    contest_scope: ContestScope
    contestant_actor: ContestActor
    contestant_id: str
    reason_class: ContestReasonClass
    contest_result: ContestResult
    original_memory_preserved: bool
    contest_provenance: ProvenanceV1
    contested_eid: Optional[int] = None
    candidate_handle: Optional[str] = None
    contest_reason: Optional[str] = None

    def __post_init__(self) -> None:
        # contest_id — required, UUID-shaped, never auto-generated.
        if not _is_uuid_shaped(self.contest_id):
            raise ContestRecordError(
                "contest_id", "not_uuid_shaped", repr(self.contest_id)
            )

        # Closed vocabularies — direct construction requires enum members;
        # string coercion happens only in from_dict / validate_contest_record.
        if not isinstance(self.contest_scope, ContestScope):
            raise ContestRecordError(
                "contest_scope", "invalid_type",
                type(self.contest_scope).__name__,
            )
        if not isinstance(self.contestant_actor, ContestActor):
            raise ContestRecordError(
                "contestant_actor", "invalid_type",
                type(self.contestant_actor).__name__,
            )
        if not isinstance(self.reason_class, ContestReasonClass):
            raise ContestRecordError(
                "reason_class", "invalid_type",
                type(self.reason_class).__name__,
            )
        if not isinstance(self.contest_result, ContestResult):
            raise ContestRecordError(
                "contest_result", "invalid_type",
                type(self.contest_result).__name__,
            )

        # contestant_id — required, non-empty string.
        if not isinstance(self.contestant_id, str) or not self.contestant_id:
            raise ContestRecordError("contestant_id", "empty_or_not_string")

        # contest_reason — optional; if present, non-empty string.
        if self.contest_reason is not None:
            if not isinstance(self.contest_reason, str) or not self.contest_reason:
                raise ContestRecordError("contest_reason", "empty_or_not_string")

        # original_memory_preserved — required literal True (assertion only;
        # this does NOT prove any writer behavior). ``is True`` rejects
        # False / None / truthy ints.
        if self.original_memory_preserved is not True:
            raise ContestRecordError(
                "original_memory_preserved", "must_be_true",
                repr(self.original_memory_preserved),
            )

        # contest_provenance — required ProvenanceV1 instance.
        if not isinstance(self.contest_provenance, ProvenanceV1):
            raise ContestRecordError(
                "contest_provenance", "invalid_type",
                type(self.contest_provenance).__name__,
            )

        # Target — exactly one of contested_eid / candidate_handle.
        has_eid = self.contested_eid is not None
        has_handle = self.candidate_handle is not None
        if has_eid and has_handle:
            raise ContestRecordError(
                "target", "ambiguous_target",
                "set exactly one of contested_eid / candidate_handle",
            )
        if not has_eid and not has_handle:
            raise ContestRecordError(
                "target", "missing_target",
                "set exactly one of contested_eid / candidate_handle",
            )

        # contested_eid — int (bool rejected), positive per eid convention.
        # No existence lookup.
        if has_eid:
            if isinstance(self.contested_eid, bool) or not isinstance(self.contested_eid, int):
                raise ContestRecordError(
                    "contested_eid", "must_be_int",
                    type(self.contested_eid).__name__,
                )
            if self.contested_eid < MIN_VALID_EID:
                raise ContestRecordError(
                    "contested_eid", "out_of_range",
                    f"eids are assigned from {MIN_VALID_EID}; got {self.contested_eid}",
                )

        # candidate_handle — UUID-shaped string. No binding lookup.
        if has_handle and not _is_uuid_shaped(self.candidate_handle):
            raise ContestRecordError(
                "candidate_handle", "not_uuid_shaped", repr(self.candidate_handle)
            )

        # Cross-field PROHIBITION ONLY: a non-operator actor may not route to
        # ``refuse``. The converse is NOT implemented — operator actor is
        # necessary but NOT sufficient, and this slice grants no authorization.
        if (
            self.contest_result == ContestResult.REFUSE
            and self.contestant_actor != ContestActor.OPERATOR
        ):
            raise ContestRecordError(
                "contest_result", "refuse_requires_operator",
                "non-operator actor may not route to refuse",
            )

    # ── Serialization (pure; in-memory only) ────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict. Omits None optional fields.

        Enums serialize to their string ``.value``; ``contest_provenance``
        serializes via ``ProvenanceV1.to_dict()``. No file writing.
        """
        d: Dict[str, Any] = {
            "contest_id": self.contest_id,
            "contest_scope": self.contest_scope.value,
            "contestant_actor": self.contestant_actor.value,
            "contestant_id": self.contestant_id,
            "reason_class": self.reason_class.value,
            "contest_result": self.contest_result.value,
            "original_memory_preserved": self.original_memory_preserved,
            "contest_provenance": self.contest_provenance.to_dict(),
        }
        if self.contested_eid is not None:
            d["contested_eid"] = int(self.contested_eid)
        if self.candidate_handle is not None:
            d["candidate_handle"] = self.candidate_handle
        if self.contest_reason is not None:
            d["contest_reason"] = self.contest_reason
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContestRecord":
        """Deserialize from a canonical dict. Pure; no ID generation.

        Fail-closed on unknown top-level keys. Required keys must be present.
        Enum strings are coerced to members; ``contest_provenance`` is
        reconstructed as a ProvenanceV1.
        """
        if not isinstance(d, dict):
            raise ContestRecordError("<root>", "not_a_dict", type(d).__name__)
        if not d:
            raise ContestRecordError("<root>", "empty")

        known = {f.name for f in fields(cls)}
        unknown = [k for k in d if k not in known]
        if unknown:
            raise ContestRecordError(
                sorted(unknown)[0], "unknown_field",
                f"unknown top-level keys: {sorted(unknown)}",
            )

        required = (
            "contest_id", "contest_scope", "contestant_actor", "contestant_id",
            "reason_class", "contest_result", "original_memory_preserved",
            "contest_provenance",
        )
        for key in required:
            if key not in d:
                raise ContestRecordError(key, "missing")

        return cls(
            contest_id=d["contest_id"],
            contest_scope=_coerce_enum(ContestScope, d["contest_scope"], "contest_scope"),
            contestant_actor=_coerce_enum(ContestActor, d["contestant_actor"], "contestant_actor"),
            contestant_id=d["contestant_id"],
            reason_class=_coerce_enum(ContestReasonClass, d["reason_class"], "reason_class"),
            contest_result=_coerce_enum(ContestResult, d["contest_result"], "contest_result"),
            original_memory_preserved=d["original_memory_preserved"],
            contest_provenance=_coerce_provenance(d["contest_provenance"]),
            contested_eid=d.get("contested_eid"),
            candidate_handle=d.get("candidate_handle"),
            contest_reason=d.get("contest_reason"),
        )


def validate_contest_record(d: Dict[str, Any]) -> ContestRecord:
    """Pure validator: canonical dict -> validated ContestRecord.

    No side effects, no filesystem access, no ID generation. Thin wrapper
    over ``ContestRecord.from_dict`` provided as the module's named
    validation entry point (lifecycle Slice-0 precedent).
    """
    return ContestRecord.from_dict(d)
