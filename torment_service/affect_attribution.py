"""Q3-D1 affect-attribution contract — validator + read shim (S1).

Implements the tracked contract in
``docs/CLUSTER_5_PATH_C_Q3_D1_AFFECT_ATTRIBUTION_CONTRACT_v0.1.md``.

Pure functions only. No I/O, no logging side effects, no mutation of input
payloads or envelopes. This module defines and validates the row-local
``affect_attribution`` envelope (a sibling of ``affect_tag`` / ``affect_conf`` in
the memory payload, deliberately *outside* ``ProvenanceV1``) and provides a
read-time legacy fallback for rows that predate the contract.

D1-S2 scope: this module now also provides the ordinary-ingest producer
constructor (:func:`build_ingest_classifier_attribution`). The
``TormentFabric.ingest()`` fresh-spawn branch stamps the canonical
``system / inferred / unconfirmed / subject=unknown / via=ingest_affect_classifier``
envelope iff affect classification *completed successfully* (``set`` when it found
an affect value, ``unset`` when it ran but found none). The not-evaluated states
(classifier disabled, or raised under fail-soft) are deliberately left unstamped —
``unset != not evaluated`` — and that gating lives at the call site, since a
constructor cannot observe whether it was invoked. Still no scoring influence; the
mood_drift producer (D1-S3) and others remain unstamped. Absent/null envelopes
still route to a synthetic read-time fallback; a present, non-null, malformed
envelope fails loud.
"""

from __future__ import annotations

from typing import Any, Dict

SCHEMA_VERSION = "1.0"

# Allowed enum values. "Reserved" values are recognized so the vocabulary is
# stable, but must NOT be emitted by a producer until a later slice deliberately
# activates them.
VALUE_STATES = ("set", "unset", "ambiguous")
RESERVED_VALUE_STATES = ("ambiguous",)

ORIGIN_KINDS = ("inferred", "asserted", "derived", "recovered", "measured")
RESERVED_ORIGIN_KINDS = ("measured",)

ACTORS = ("user", "system", "agent", "migration", "operator")
# Actor classes that represent an explicit assertion and therefore require an
# auditable ``actor_reference``. ``system`` / ``migration`` are class-sufficient.
ASSERTION_ACTORS = ("user", "agent", "operator")

SUBJECTS = ("user", "unknown")
CONFIRMATIONS = ("unconfirmed", "confirmed")

# Stable producing-method / derivation tokens allowed in S1. Centralized so later
# slices can deliberately extend the allowlist.
VIA_TOKENS = (
    "ingest_affect_classifier",
    "mood_drift_transition",
    "legacy_read_fallback",
)

REQUIRED_KEYS = (
    "schema_version",
    "value_state",
    "origin_kind",
    "actor",
    "actor_reference",
    "subject",
    "confirmation",
    "confirmation_actor",
    "confirmation_actor_reference",
    "via",
)
_ALLOWED_KEYS = frozenset(REQUIRED_KEYS)


class AffectAttributionError(ValueError):
    """Raised when a present affect-attribution envelope is malformed.

    Absent/null envelopes never raise — they route to the read-time legacy
    fallback. Only a present, non-null, malformed envelope fails loud, so a
    corrupt authoritative-looking envelope can never masquerade as a benign
    legacy row.
    """


def _legacy_fallback(affect_tag: Any) -> Dict[str, Any]:
    """Synthetic read-time fallback for rows with no attribution envelope."""
    return {
        "schema_version": SCHEMA_VERSION,
        "value_state": "set" if affect_tag is not None else "unset",
        "origin_kind": "recovered",
        "actor": "migration",
        "actor_reference": None,
        "subject": "unknown",
        "confirmation": "unconfirmed",
        "confirmation_actor": None,
        "confirmation_actor_reference": None,
        "via": "legacy_read_fallback",
    }


def validate_affect_attribution(envelope: Dict[str, Any], *, affect_tag: Any) -> Dict[str, Any]:
    """Strictly validate a present, non-null affect-attribution envelope.

    Returns a validated shallow copy. Raises :class:`AffectAttributionError` on
    any violation. Does not mutate the input. ``affect_tag`` is the row's stored
    affect value, used for value_state consistency.
    """
    if not isinstance(envelope, dict):
        raise AffectAttributionError(
            f"affect_attribution must be a dict, got {type(envelope).__name__}"
        )

    # Unknown keys (catch typos / silent drift).
    extra = set(envelope) - _ALLOWED_KEYS
    if extra:
        raise AffectAttributionError(f"unknown affect_attribution key(s): {sorted(extra)}")

    # Required keys present (value may be None for the reference / actor fields).
    missing = [k for k in REQUIRED_KEYS if k not in envelope]
    if missing:
        raise AffectAttributionError(f"missing required key(s): {missing}")

    # schema_version compatibility boundary.
    if envelope["schema_version"] != SCHEMA_VERSION:
        raise AffectAttributionError(
            f"unknown schema_version {envelope['schema_version']!r}; "
            f"expected {SCHEMA_VERSION!r}"
        )

    value_state = envelope["value_state"]
    origin_kind = envelope["origin_kind"]
    actor = envelope["actor"]
    actor_reference = envelope["actor_reference"]
    subject = envelope["subject"]
    confirmation = envelope["confirmation"]
    confirmation_actor = envelope["confirmation_actor"]
    confirmation_actor_reference = envelope["confirmation_actor_reference"]
    via = envelope["via"]

    # Enum membership.
    if value_state not in VALUE_STATES:
        raise AffectAttributionError(f"invalid value_state {value_state!r}")
    if origin_kind not in ORIGIN_KINDS:
        raise AffectAttributionError(f"invalid origin_kind {origin_kind!r}")
    if actor not in ACTORS:
        raise AffectAttributionError(f"invalid actor {actor!r}")
    if subject not in SUBJECTS:
        raise AffectAttributionError(f"invalid subject {subject!r}")
    if confirmation not in CONFIRMATIONS:
        raise AffectAttributionError(f"invalid confirmation {confirmation!r}")
    if via not in VIA_TOKENS:
        raise AffectAttributionError(f"unknown via token {via!r}")

    # Reserved values must not be emitted before activation.
    if value_state in RESERVED_VALUE_STATES:
        raise AffectAttributionError(
            f"value_state {value_state!r} is reserved and not yet active"
        )
    if origin_kind in RESERVED_ORIGIN_KINDS:
        raise AffectAttributionError(
            f"origin_kind {origin_kind!r} is reserved and not yet active"
        )

    # value_state / affect_tag consistency.
    if value_state == "set" and affect_tag is None:
        raise AffectAttributionError("value_state=set requires a stored affect_tag")
    if value_state == "unset" and affect_tag is not None:
        raise AffectAttributionError("value_state=unset must not carry a stored affect_tag")

    # actor_reference, when present, must be a non-empty string.
    if actor_reference is not None and not (
        isinstance(actor_reference, str) and actor_reference
    ):
        raise AffectAttributionError(
            "actor_reference, when present, must be a non-empty string"
        )

    # Assertion posture: origin_kind=asserted is a future auditable-assertion
    # posture. It requires an assertion actor (user/agent/operator) AND a
    # non-empty string actor_reference. `asserted` never implies `confirmed` —
    # confirmation is a separate axis, validated below.
    if origin_kind == "asserted":
        if actor not in ASSERTION_ACTORS:
            raise AffectAttributionError(
                "origin_kind=asserted requires an assertion actor (user/agent/operator)"
            )
        if not (isinstance(actor_reference, str) and actor_reference):
            raise AffectAttributionError(
                "origin_kind=asserted requires a non-empty string actor_reference"
            )

    # Confirmation binding.
    if confirmation == "confirmed":
        if confirmation_actor not in ACTORS:
            raise AffectAttributionError(
                "confirmation=confirmed requires confirmation_actor to be a valid actor class"
            )
        if not (isinstance(confirmation_actor_reference, str) and confirmation_actor_reference):
            raise AffectAttributionError(
                "confirmation=confirmed requires a non-empty string confirmation_actor_reference"
            )
    else:  # unconfirmed
        if confirmation_actor is not None or confirmation_actor_reference is not None:
            raise AffectAttributionError(
                "confirmation=unconfirmed must not carry confirmer metadata"
            )

    return dict(envelope)


def build_ingest_classifier_attribution(*, affect_tag: Any) -> Dict[str, Any]:
    """Canonical D1-S2 attribution envelope for an ordinary-ingest fresh row.

    Returns the producer-default envelope for affect produced by the ingest affect
    classifier: ``system / inferred / unconfirmed / subject=unknown /
    via=ingest_affect_classifier``. ``value_state`` is derived from the stored
    ``affect_tag``:

    - ``set``   -> classifier completed and produced an affect value
    - ``unset`` -> classifier completed and produced no affect value

    This producer must be called ONLY when affect classification completed
    successfully. It never expresses the *not-evaluated* states (classifier
    disabled or raised); that gating lives at the call site, because a constructor
    cannot observe whether it was invoked. ``unset != not evaluated``.

    Pure: no I/O, no mutation of any input. Returns a validated dict (a shallow
    copy from :func:`validate_affect_attribution`), and raises
    :class:`AffectAttributionError` if the produced envelope is somehow
    inconsistent — defense in depth so a producer bug cannot emit a malformed
    envelope.
    """
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "value_state": "set" if affect_tag is not None else "unset",
        "origin_kind": "inferred",
        "actor": "system",
        "actor_reference": None,
        "subject": "unknown",
        "confirmation": "unconfirmed",
        "confirmation_actor": None,
        "confirmation_actor_reference": None,
        "via": "ingest_affect_classifier",
    }
    return validate_affect_attribution(envelope, affect_tag=affect_tag)


def read_affect_attribution(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return the affect-attribution envelope for a memory payload (read-time).

    - ``affect_attribution`` absent or null -> synthetic legacy fallback derived
      from the row's existing ``affect_tag``.
    - present, non-null -> a strictly validated copy (raises on malformed).

    Never mutates or persists the payload; never backfills.
    """
    envelope = payload.get("affect_attribution")
    if envelope is None:
        return _legacy_fallback(payload.get("affect_tag"))
    return validate_affect_attribution(envelope, affect_tag=payload.get("affect_tag"))
