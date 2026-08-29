from __future__ import annotations

import math

import pytest

from torment_service.substrate.canonical_intent import (
    CANONICAL_INTENT_CONTRACT,
    canonical_intent_bytes,
    canonical_intent_text,
)
from torment_service.substrate.errors import CanonicalIntentError


def test_canonical_intent_orders_dict_keys_deterministically() -> None:
    assert canonical_intent_bytes({"b": 2, "a": 1}) == canonical_intent_bytes({"a": 1, "b": 2})
    assert canonical_intent_text({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert CANONICAL_INTENT_CONTRACT == "TMS-INTENT-1"


def test_canonical_intent_normalizes_unicode_nfc() -> None:
    assert canonical_intent_bytes({"value": "e\u0301"}) == canonical_intent_bytes({"value": "é"})


def test_canonical_intent_preserves_list_order() -> None:
    assert canonical_intent_bytes(["a", "b"]) != canonical_intent_bytes(["b", "a"])


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_canonical_intent_rejects_nonfinite_numbers(value: float) -> None:
    with pytest.raises(CanonicalIntentError):
        canonical_intent_bytes({"value": value})


def test_canonical_intent_rejects_unsupported_values_and_generates_no_metadata() -> None:
    with pytest.raises(CanonicalIntentError):
        canonical_intent_bytes({"value": {"unordered"}})

    value = {"semantic": "same"}
    encoded = canonical_intent_text(value)
    assert encoded == '{"semantic":"same"}'
    assert value == {"semantic": "same"}
    assert canonical_intent_bytes({"semantic": "different"}) != encoded.encode("utf-8")
