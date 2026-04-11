# tests/test_provenance_v1_admission.py
"""
Tests for the v2.4.x step-6 WRITE_MIGRATION admission-field additions to
``torment_service.provenance_v1.ProvenanceV1``.

Scope
-----
These tests cover the foundation changes in commit A of step 6:
  - The new ``SOURCE_GATE1_UNRECOVERABLE`` storage sentinel.
  - The three new admission fields (``admission_refused``,
    ``admission_reason``, ``admission_policy_version``).
  - The construction-time invariants that make half-formed admission
    records impossible.
  - Backward compatibility: rows produced by live ingest paths serialize
    byte-compatibly with the pre-step-6 shape, and rows deserialized from
    the pre-step-6 shape construct cleanly with admission defaults.

These tests do NOT exercise gate-1 recovery, gate-2 admission, the
recursion guard, or any migration-writer path. Those are covered by
their own dedicated test files as each sub-task lands.

See ``docs/ADMISSION_POLICY_v2.4.x.md`` for the authoritative admission
rule set and ``docs/WRITE_MIGRATION_FRAMING_v2.4.x.md`` for the two-gate
framing.
"""
from __future__ import annotations

import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.provenance_v1 import (
    ProvenanceV1,
    SOURCE_GATE1_UNRECOVERABLE,
    SOURCE_USER_INPUT,
    SOURCE_MEMORY,
    VALID_SOURCE_TYPES,
    WRITE_DIRECT_INGEST,
    WRITE_MIGRATION,
)


class TestSentinelRegistration(unittest.TestCase):
    """The gate-1 FAIL sentinel must be a first-class member of the
    source_type vocabulary so migration-produced rows can be stored in
    the uniform ProvenanceV1 schema."""

    def test_sentinel_value_is_stable_string(self) -> None:
        self.assertEqual(SOURCE_GATE1_UNRECOVERABLE, "gate1_unrecoverable")

    def test_sentinel_in_valid_source_types(self) -> None:
        self.assertIn(SOURCE_GATE1_UNRECOVERABLE, VALID_SOURCE_TYPES)

    def test_sentinel_distinct_from_live_origin_classes(self) -> None:
        # The sentinel is a storage marker, not an origin class.
        # None of the live-ingest origin classes should alias to it.
        for live in ("user_input", "role_output", "memory", "tool_result",
                     "collective_echo", "derived"):
            self.assertNotEqual(SOURCE_GATE1_UNRECOVERABLE, live)


class TestAdmissionFieldDefaults(unittest.TestCase):
    """Live ingest paths must construct ProvenanceV1 without touching any
    admission field. The defaults must encode 'no admission decision on
    file' and serialize byte-compatibly with the pre-step-6 shape."""

    def test_default_admission_refused_is_false(self) -> None:
        p = ProvenanceV1()
        self.assertFalse(p.admission_refused)

    def test_default_admission_reason_is_empty(self) -> None:
        p = ProvenanceV1()
        self.assertEqual(p.admission_reason, "")

    def test_default_admission_policy_version_is_empty(self) -> None:
        p = ProvenanceV1()
        self.assertEqual(p.admission_policy_version, "")

    def test_default_to_dict_omits_admission_fields(self) -> None:
        # Pre-step-6 shape compatibility: default admission fields MUST
        # NOT appear in serialized output. This guarantees that rows
        # written by live ingest paths after the step-6 merge are
        # byte-identical to rows written before the merge.
        p = ProvenanceV1()
        d = p.to_dict()
        self.assertNotIn("admission_refused", d)
        self.assertNotIn("admission_reason", d)
        self.assertNotIn("admission_policy_version", d)

    def test_factory_methods_do_not_set_admission_fields(self) -> None:
        # Every live-ingest factory must default-construct admission fields.
        factories = [
            ProvenanceV1.for_user_ingest(),
            ProvenanceV1.for_cognition_writeback(source_role="archivist"),
            ProvenanceV1.for_tool_result(tool_name="test_tool"),
            ProvenanceV1.for_collective_echo(),
        ]
        for p in factories:
            with self.subTest(factory=p.write_path):
                self.assertFalse(p.admission_refused)
                self.assertEqual(p.admission_reason, "")
                self.assertEqual(p.admission_policy_version, "")
                # And serialization must not leak the admission fields.
                d = p.to_dict()
                self.assertNotIn("admission_refused", d)
                self.assertNotIn("admission_reason", d)
                self.assertNotIn("admission_policy_version", d)


class TestRefusalRowConstruction(unittest.TestCase):
    """A valid refusal row — the only shape the WRITE_MIGRATION writer
    will emit for gate-1 FAIL rows — must construct cleanly and
    round-trip through serialization."""

    def _refusal_row(self) -> ProvenanceV1:
        return ProvenanceV1(
            source_type=SOURCE_GATE1_UNRECOVERABLE,
            write_path=WRITE_MIGRATION,
            admission_refused=True,
            admission_reason="gate1_unrecoverable",
            admission_policy_version="v2.4.x-step6-a",
            notes="legacy_row_had_no_provenance_field",
        )

    def test_refusal_row_constructs(self) -> None:
        p = self._refusal_row()
        self.assertEqual(p.source_type, SOURCE_GATE1_UNRECOVERABLE)
        self.assertTrue(p.admission_refused)
        self.assertEqual(p.admission_reason, "gate1_unrecoverable")
        self.assertEqual(p.admission_policy_version, "v2.4.x-step6-a")

    def test_refusal_row_to_dict_includes_admission_fields(self) -> None:
        p = self._refusal_row()
        d = p.to_dict()
        self.assertTrue(d["admission_refused"])
        self.assertEqual(d["admission_reason"], "gate1_unrecoverable")
        self.assertEqual(d["admission_policy_version"], "v2.4.x-step6-a")

    def test_refusal_row_round_trip(self) -> None:
        p = self._refusal_row()
        d = p.to_dict()
        p2 = ProvenanceV1.from_dict(d)
        self.assertEqual(p.source_type, p2.source_type)
        self.assertEqual(p.admission_refused, p2.admission_refused)
        self.assertEqual(p.admission_reason, p2.admission_reason)
        self.assertEqual(
            p.admission_policy_version, p2.admission_policy_version
        )
        self.assertEqual(p.notes, p2.notes)

    def test_refused_admit_row_admission_reason_can_be_any_registered_value(self) -> None:
        # A refused row with a non-sentinel source_type is legal — this
        # is the "dict with source_type in the rejected set" shape from
        # the Question 1b admission predicate. The writer stores the
        # recovered source_type in its natural field and encodes refusal
        # in the admission fields.
        p = ProvenanceV1(
            source_type=SOURCE_MEMORY,
            write_path=WRITE_MIGRATION,
            admission_refused=True,
            admission_reason="source_type_in_rejected_set",
            admission_policy_version="v2.4.x-step6-a",
        )
        self.assertEqual(p.source_type, SOURCE_MEMORY)
        self.assertTrue(p.admission_refused)


class TestAdmissionInvariants(unittest.TestCase):
    """The construction-time invariants that prevent half-formed
    admission records from reaching storage."""

    def test_refused_requires_reason(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            ProvenanceV1(
                admission_refused=True,
                admission_policy_version="v2.4.x-step6-a",
            )
        self.assertIn("admission_reason", str(ctx.exception))

    def test_any_admission_decision_requires_policy_version(self) -> None:
        # Refused but no policy version.
        with self.assertRaises(ValueError) as ctx:
            ProvenanceV1(
                admission_refused=True,
                admission_reason="gate1_unrecoverable",
            )
        self.assertIn("admission_policy_version", str(ctx.exception))

    def test_admission_reason_alone_requires_policy_version(self) -> None:
        # A row with admission_reason set but policy_version empty is
        # also half-formed — the reason-without-version shape would make
        # the re-run policy unable to determine whether the decision is
        # stale.
        with self.assertRaises(ValueError) as ctx:
            ProvenanceV1(admission_reason="gate1_unrecoverable")
        self.assertIn("admission_policy_version", str(ctx.exception))

    def test_sentinel_source_type_requires_refused(self) -> None:
        # Constructing a row with the sentinel source_type while
        # claiming admission_refused=False is internally contradictory:
        # the recursion guard rejects the sentinel at any depth via
        # _REJECTED_SOURCE_TYPES_IN_WALK, so a "not refused" label on a
        # sentinel row would misrepresent reality.
        with self.assertRaises(ValueError) as ctx:
            ProvenanceV1(
                source_type=SOURCE_GATE1_UNRECOVERABLE,
                write_path=WRITE_MIGRATION,
            )
        self.assertIn("SOURCE_GATE1_UNRECOVERABLE", str(ctx.exception))


class TestBackwardCompatibility(unittest.TestCase):
    """Rows written before the step-6 schema addition must deserialize
    cleanly with the new fields defaulting to their 'no admission
    decision on file' values."""

    def test_pre_step6_dict_deserializes(self) -> None:
        # The exact shape a row would have carried before the admission
        # fields existed.
        legacy_dict = {
            "schema_version": "1.0",
            "source_type": SOURCE_USER_INPUT,
            "source_role": None,
            "write_path": WRITE_DIRECT_INGEST,
            "parent_eids": [],
            "created_at_step": 42,
            "created_at_ts": "2026-04-11T00:00:00Z",
        }
        p = ProvenanceV1.from_dict(legacy_dict)
        self.assertEqual(p.source_type, SOURCE_USER_INPUT)
        self.assertFalse(p.admission_refused)
        self.assertEqual(p.admission_reason, "")
        self.assertEqual(p.admission_policy_version, "")

    def test_pre_step6_dict_round_trip_byte_compatible(self) -> None:
        # Round-tripping a pre-step-6 dict must not introduce admission
        # fields into the serialized output.
        legacy_dict = {
            "schema_version": "1.0",
            "source_type": SOURCE_USER_INPUT,
            "source_role": None,
            "write_path": WRITE_DIRECT_INGEST,
            "parent_eids": [],
            "created_at_step": 42,
            "created_at_ts": "2026-04-11T00:00:00Z",
        }
        p = ProvenanceV1.from_dict(legacy_dict)
        d = p.to_dict()
        self.assertNotIn("admission_refused", d)
        self.assertNotIn("admission_reason", d)
        self.assertNotIn("admission_policy_version", d)


if __name__ == "__main__":
    unittest.main()
