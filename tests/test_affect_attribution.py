"""D1-S1 tests: affect-attribution contract validator + read shim.

Covers the legacy read shim (absent/null -> synthetic fallback), the strict
fail-loud validation of present envelopes, and the no-mutation guarantee. No
producer wiring, no scoring — pure contract behavior.
"""

import copy
import unittest

from torment_service.affect_attribution import (
    AffectAttributionError,
    SCHEMA_VERSION,
    read_affect_attribution,
)


def _valid_envelope():
    return {
        "schema_version": SCHEMA_VERSION,
        "value_state": "set",
        "origin_kind": "inferred",
        "actor": "system",
        "actor_reference": None,
        "subject": "unknown",
        "confirmation": "unconfirmed",
        "confirmation_actor": None,
        "confirmation_actor_reference": None,
        "via": "ingest_affect_classifier",
    }


class TestReadShim(unittest.TestCase):
    # 1
    def test_absent_envelope_yields_legacy_fallback(self):
        env = read_affect_attribution({"affect_tag": "sad", "affect_conf": 0.7})
        self.assertEqual(env["origin_kind"], "recovered")
        self.assertEqual(env["actor"], "migration")
        self.assertEqual(env["subject"], "unknown")
        self.assertEqual(env["confirmation"], "unconfirmed")
        self.assertEqual(env["via"], "legacy_read_fallback")
        self.assertEqual(env["value_state"], "set")

    # 2
    def test_null_envelope_yields_legacy_fallback(self):
        env = read_affect_attribution(
            {"affect_tag": "sad", "affect_conf": 0.7, "affect_attribution": None}
        )
        self.assertEqual(env["via"], "legacy_read_fallback")
        self.assertEqual(env["value_state"], "set")

    # 3
    def test_legacy_affect_present_is_set(self):
        self.assertEqual(read_affect_attribution({"affect_tag": "angry"})["value_state"], "set")

    # 4
    def test_legacy_affect_missing_or_null_is_unset(self):
        self.assertEqual(read_affect_attribution({})["value_state"], "unset")
        self.assertEqual(
            read_affect_attribution({"affect_tag": None})["value_state"], "unset"
        )

    # 5
    def test_valid_explicit_envelope_returns_validated_copy(self):
        payload = {"affect_tag": "sad", "affect_attribution": _valid_envelope()}
        env = read_affect_attribution(payload)
        self.assertEqual(env["origin_kind"], "inferred")
        self.assertEqual(env["via"], "ingest_affect_classifier")
        self.assertIsNot(env, payload["affect_attribution"])  # returned a copy

    # 6
    def test_fallback_never_mutates_payload(self):
        payload = {"affect_tag": "sad"}
        before = copy.deepcopy(payload)
        read_affect_attribution(payload)
        self.assertEqual(payload, before)
        self.assertNotIn("affect_attribution", payload)


class TestStrictValidation(unittest.TestCase):
    def _read_with(self, **overrides):
        env = _valid_envelope()
        env.update(overrides)
        return read_affect_attribution({"affect_tag": "sad", "affect_attribution": env})

    # 7
    def test_present_non_dict_envelope_raises(self):
        with self.assertRaises(AffectAttributionError):
            read_affect_attribution({"affect_tag": "sad", "affect_attribution": "nope"})

    # 8
    def test_invalid_enum_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(origin_kind="wishful")

    # 9
    def test_invalid_schema_version_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(schema_version="9.9")

    # 10
    def test_unknown_key_raises(self):
        env = _valid_envelope()
        env["extra"] = "x"
        with self.assertRaises(AffectAttributionError):
            read_affect_attribution({"affect_tag": "sad", "affect_attribution": env})

    def test_missing_required_key_raises(self):
        env = _valid_envelope()
        del env["via"]
        with self.assertRaises(AffectAttributionError):
            read_affect_attribution({"affect_tag": "sad", "affect_attribution": env})

    # 11
    def test_unknown_via_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(via="some_future_token")

    # 12
    def test_set_without_tag_raises(self):
        env = _valid_envelope()  # value_state == "set"
        with self.assertRaises(AffectAttributionError):
            read_affect_attribution({"affect_tag": None, "affect_attribution": env})

    def test_unset_with_tag_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(value_state="unset")  # affect_tag="sad" present

    # 13
    def test_confirmed_without_actor_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(
                confirmation="confirmed",
                confirmation_actor=None,
                confirmation_actor_reference="user:stable-1",
            )

    def test_confirmed_without_reference_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(
                confirmation="confirmed",
                confirmation_actor="user",
                confirmation_actor_reference=None,
            )

    # 14
    def test_unconfirmed_with_confirmer_metadata_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(confirmation="unconfirmed", confirmation_actor="user")

    # 15
    def test_assertion_actor_without_reference_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(origin_kind="asserted", actor="user", actor_reference=None)

    # 16
    def test_reserved_ambiguous_rejected(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(value_state="ambiguous")

    def test_reserved_measured_rejected(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(origin_kind="measured")

    # --- follow-up hardening: reference semantics ---
    def test_confirmed_actor_not_a_valid_class_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(
                confirmation="confirmed",
                confirmation_actor="buddy",  # not an ACTORS class
                confirmation_actor_reference="buddy:1",
            )

    def test_confirmed_reference_non_string_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(
                confirmation="confirmed",
                confirmation_actor="user",
                confirmation_actor_reference=123,  # truthy non-string
            )

    def test_actor_reference_non_string_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(actor_reference=123)  # truthy non-string

    def test_actor_reference_empty_string_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(actor_reference="")

    def test_asserted_with_non_assertion_actor_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(origin_kind="asserted", actor="system", actor_reference="x")

    def test_asserted_requires_reference_raises(self):
        with self.assertRaises(AffectAttributionError):
            self._read_with(origin_kind="asserted", actor="agent", actor_reference=None)

    def test_asserted_valid_ok(self):
        env = self._read_with(
            origin_kind="asserted", actor="user", actor_reference="user:stable-1"
        )
        self.assertEqual(env["origin_kind"], "asserted")
        self.assertEqual(env["actor_reference"], "user:stable-1")

    # positive: a fully-bound confirmed envelope validates
    def test_confirmed_complete_binding_ok(self):
        env = self._read_with(
            confirmation="confirmed",
            confirmation_actor="user",
            confirmation_actor_reference="user:stable-1",
        )
        self.assertEqual(env["confirmation"], "confirmed")
        self.assertEqual(env["confirmation_actor_reference"], "user:stable-1")


if __name__ == "__main__":
    unittest.main()
