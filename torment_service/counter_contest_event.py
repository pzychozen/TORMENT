# torment_service/counter_contest_event.py
"""CounterContestEvent — Track B v0.2 B2-S4 vocabulary + validation only.

B2-S4 counter-contest event vocabulary + validation only.

NOT load-bearing.
No production caller constructs, reads, writes, persists, resolves,
ranks, prompts, or applies CounterContestEvent.

No effective-authority resolver.
No status / verdict / precedence.
No target-existence lookup.

This module is the Slice vocabulary for a *future* Track B v0.2 counter-contest
event ledger. It mirrors the B2-S2 ``contest_record.py`` posture: a closed
vocabulary, an immutable record, a deterministic pure validator, and pure
dict/JSON serialization exist in code; the runtime does not import, construct,
read, persist, or apply them. A mandatory AST conformance test
(``tests/test_counter_contest_event_conformance_meta.py``) keeps this guarantee
executable by failing if any non-allowlisted production module imports this one.

Doctrine anchor (framing
``docs/TRACK_B_V0_2_B2_S4_COUNTER_CONTEST_EVENT_FRAMING_v0.1.md``): a
counter-contest event is *immutable observational history*. It records that a
structurally valid ``ContestRecord`` identifier was itself contested. It records
a *claimed* linkage; it does NOT prove target existence. It does not mutate,
reverse, overturn, cancel, supersede, resolve, override, or win against the
prior ``ContestRecord``. *Recording disagreement != resolving authority.*

The vocabulary deliberately carries NO outcome field. There is no
``contest_result`` / ``status`` / ``effective_status`` / ``active`` /
``overturned`` / ``superseded`` / ``resolved`` / ``winner`` / ``precedence`` /
``weight`` / ``rank`` / ``confidence`` / ``priority`` (or any equivalent). A
counter-contest event records disagreement only; it asserts no outcome.

Vocabulary reuse (B2-S4 decision): the closed ``ContestActor`` and
``ContestReasonClass`` vocabularies are reused unchanged from ``contest_record``
(B2-S2) rather than duplicated, so the actor / reason vocabulary has a single
source of truth. This is the only cross-module import beyond ``ProvenanceV1``;
it is recorded in the ``contest_record`` importer allowlist
(``tests/test_contest_record_conformance_meta.py``). No generic shared
vocabulary layer is created, ``ContestRecord`` is not refactored, and
``ProvenanceV1`` is unchanged (no ``SOURCE_CONTEST``).

Parked here (NOT decided in B2-S4): target-existence integrity policy,
dangling-linkage policy, ``candidate_handle`` -> eid binding, counter-contest
result routing, operator authorization, effective-authority resolution,
retrieval/prompt/cognition/MCP exposure.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any, Dict

from torment_service.contest_record import ContestActor, ContestReasonClass
from torment_service.provenance_v1 import ProvenanceV1


# ── Error type (contest_record Slice pattern) ───────────────────────


class CounterContestEventError(ValueError):
    """Raised when a CounterContestEvent fails validation.

    Inherits ``ValueError`` because the failure is a shape/content contract
    violation. Carries the offending ``field`` and a short ``reason`` code so
    callers and audit logs can identify the failure without re-inspecting the
    input.
    """

    def __init__(self, field: str, reason: str, detail: str = "") -> None:
        self.field = str(field)
        self.reason = str(reason)
        msg = f"CounterContestEventError on {self.field!r}: {self.reason}"
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
        raise CounterContestEventError(field_name, "unknown_value", str(value)) from None


def _coerce_provenance(value: Any) -> ProvenanceV1:
    """Reconstruct a ProvenanceV1 from a dict (or pass an instance through).

    Reuses ProvenanceV1 unchanged. Fail-closed boundary (mirrors the B2-S2
    ContestRecord boundary): a serialized ``event_provenance`` dict must be an
    *already-canonical* ProvenanceV1 serialization. ``ProvenanceV1.from_dict()``
    may synthesize defaults and silently drop unknown keys; if the reconstructed
    canonical form differs from the supplied dict, the input was partial,
    drifted, or carried ignored keys, and we reject rather than accept a
    silently-completed nested provenance. This tightening lives only at the
    CounterContestEvent boundary; ProvenanceV1 behavior is unchanged.

    A direct, already-valid ``ProvenanceV1`` object is accepted unchanged.
    """
    if isinstance(value, ProvenanceV1):
        return value
    if isinstance(value, dict):
        try:
            prov = ProvenanceV1.from_dict(value)
        except ValueError as exc:
            raise CounterContestEventError(
                "event_provenance", "invalid_provenance", str(exc)
            ) from None
        if prov.to_dict() != value:
            raise CounterContestEventError(
                "event_provenance", "non_canonical_provenance",
                "nested provenance must be an exact canonical ProvenanceV1 "
                "serialization (no partial / drifted / silently-completed dict)",
            )
        return prov
    raise CounterContestEventError(
        "event_provenance", "invalid_type", type(value).__name__
    )


# ── Immutable event ─────────────────────────────────────────────────


@dataclass(frozen=True, kw_only=True)
class CounterContestEvent:
    """An immutable observational event recording that a ContestRecord
    identifier was itself contested.

    Append-only history. It is not a mutation, not a verdict, and not a
    resolver input with automatic effect. The event carries vocabulary +
    provenance + a structurally-validated *claimed* link to a prior contest;
    it does not write, read, resolve, or apply anything, and it does not prove
    that the linked ContestRecord exists.

    Required fields (all):
        event_id, target_contest_id, contestant_actor, contestant_id,
        reason_class, event_provenance

    There is intentionally NO outcome field (see module docstring). A
    counter-contest event records disagreement only; it asserts no outcome.
    """

    event_id: str
    target_contest_id: str
    contestant_actor: ContestActor
    contestant_id: str
    reason_class: ContestReasonClass
    event_provenance: ProvenanceV1

    def __post_init__(self) -> None:
        # event_id — required, UUID-shaped, never auto-generated, never
        # derived from content.
        if not _is_uuid_shaped(self.event_id):
            raise CounterContestEventError(
                "event_id", "not_uuid_shaped", repr(self.event_id)
            )

        # target_contest_id — required, UUID-shaped STRUCTURAL validation only.
        # It structurally identifies the ContestRecord this event claims to
        # contest. NO existence lookup is performed (append-time or replay-time
        # existence checks and dangling-linkage policy are parked).
        if not _is_uuid_shaped(self.target_contest_id):
            raise CounterContestEventError(
                "target_contest_id", "not_uuid_shaped", repr(self.target_contest_id)
            )

        # Closed vocabularies — direct construction requires enum members;
        # string coercion happens only in from_dict / validate_*.
        if not isinstance(self.contestant_actor, ContestActor):
            raise CounterContestEventError(
                "contestant_actor", "invalid_type",
                type(self.contestant_actor).__name__,
            )
        if not isinstance(self.reason_class, ContestReasonClass):
            raise CounterContestEventError(
                "reason_class", "invalid_type",
                type(self.reason_class).__name__,
            )

        # contestant_id — required, non-empty string.
        if not isinstance(self.contestant_id, str) or not self.contestant_id:
            raise CounterContestEventError("contestant_id", "empty_or_not_string")

        # event_provenance — required ProvenanceV1 instance.
        if not isinstance(self.event_provenance, ProvenanceV1):
            raise CounterContestEventError(
                "event_provenance", "invalid_type",
                type(self.event_provenance).__name__,
            )

    # ── Serialization (pure; in-memory only) ────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict.

        Enums serialize to their string ``.value``; ``event_provenance``
        serializes via ``ProvenanceV1.to_dict()``. No file writing.
        """
        return {
            "event_id": self.event_id,
            "target_contest_id": self.target_contest_id,
            "contestant_actor": self.contestant_actor.value,
            "contestant_id": self.contestant_id,
            "reason_class": self.reason_class.value,
            "event_provenance": self.event_provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CounterContestEvent":
        """Deserialize from a canonical dict. Pure; no ID generation.

        Fail-closed on unknown top-level keys (this is also what rejects any
        forbidden outcome field such as ``contest_result`` / ``status``).
        Required keys must be present. Enum strings are coerced to members;
        ``event_provenance`` is reconstructed as a ProvenanceV1.
        """
        if not isinstance(d, dict):
            raise CounterContestEventError("<root>", "not_a_dict", type(d).__name__)
        if not d:
            raise CounterContestEventError("<root>", "empty")

        known = {f.name for f in fields(cls)}
        unknown = [k for k in d if k not in known]
        if unknown:
            raise CounterContestEventError(
                sorted(unknown)[0], "unknown_field",
                f"unknown top-level keys: {sorted(unknown)}",
            )

        required = (
            "event_id", "target_contest_id", "contestant_actor",
            "contestant_id", "reason_class", "event_provenance",
        )
        for key in required:
            if key not in d:
                raise CounterContestEventError(key, "missing")

        return cls(
            event_id=d["event_id"],
            target_contest_id=d["target_contest_id"],
            contestant_actor=_coerce_enum(ContestActor, d["contestant_actor"], "contestant_actor"),
            contestant_id=d["contestant_id"],
            reason_class=_coerce_enum(ContestReasonClass, d["reason_class"], "reason_class"),
            event_provenance=_coerce_provenance(d["event_provenance"]),
        )


def validate_counter_contest_event(d: Dict[str, Any]) -> CounterContestEvent:
    """Pure validator: canonical dict -> validated CounterContestEvent.

    No side effects, no filesystem access, no ID generation. Thin wrapper over
    ``CounterContestEvent.from_dict`` provided as the module's named validation
    entry point (mirrors the contest_record Slice precedent).
    """
    return CounterContestEvent.from_dict(d)
