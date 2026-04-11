# tests/test_admission_policy_drift.py
"""
CI drift check for the WRITE_MIGRATION admission policy.

This test enforces **enumeration equality** between:

  - the frozensets / tuples declared in
    ``torment_service/migration/constants.py``, and
  - the rule set enumerated in
    ``docs/ADMISSION_POLICY_v2.4.x.md``.

Adding an admission reason, a gate-1 class, or a re-run decision to one
side without updating the other will fail CI. This exists because the
doctrine doc is load-bearing — it is the source of truth for what the
migration is *allowed* to do, not just a description of what it does —
and silent drift between the code and the doc would quietly erode that
authority.

The check is **substring-based** on the doc: the test reads the
markdown file, looks for the identifier name of each constant (e.g.
``ADMISSION_REASON_GATE1_UNRECOVERABLE``), and requires:

1. Every identifier in the constants module must appear somewhere in
   the doc.
2. Every identifier of a tracked type that appears in the doc must
   also appear in the constants module.

This is intentionally a looser test than parsing the markdown tables —
it catches the real drift failure modes (name typos, missing rows,
orphaned constants) without coupling the test to the exact prose
layout of the doc, which is allowed to evolve.

Two additional invariants are asserted:

- ``ADMISSION_POLICY_VERSION`` must appear verbatim in the doc.
- The class-7 empty posture and the class-6 empty mapping table must
  be explicitly stated in the doc, per Decision 4. We search for the
  phrase "empty in commit A" as the discoverable marker.
"""
from __future__ import annotations

import os
import re
import unittest

from torment_service.migration import constants as C

_DOC_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "docs",
    "ADMISSION_POLICY_v2.4.x.md",
)


def _load_doc() -> str:
    with open(_DOC_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _constant_names_starting_with(prefix: str) -> set:
    """Return every module-level identifier in ``constants`` whose name
    starts with ``prefix``, excluding the frozenset/tuple bundles."""
    out: set = set()
    for name in dir(C):
        if name.startswith("_"):
            continue
        if not name.startswith(prefix):
            continue
        # Skip the bundles themselves (they end in plural forms we
        # explicitly exclude below) — the check wants the per-reason
        # identifiers, not the container frozenset.
        if name in (
            "ADMISSION_REASONS",
            "GATE1_CLASSES",
            "RERUN_DECISIONS",
            "ADMISSION_POLICY_VERSION",
            "GATE1_CLASS_ALREADY_CANONICAL",  # handled under GATE1_CLASS_ prefix
        ):
            continue
        out.add(name)
    return out


class AdmissionPolicyDriftTests(unittest.TestCase):
    """Enumeration equality between constants.py and the doctrine doc."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc_text = _load_doc()

    # ── Admission reasons ─────────────────────────────────────────

    def test_every_admission_reason_constant_is_named_in_doc(self) -> None:
        names = {n for n in dir(C) if n.startswith("ADMISSION_REASON_")}
        self.assertTrue(names, "constants module has no ADMISSION_REASON_* entries")
        for name in sorted(names):
            self.assertIn(
                name,
                self.doc_text,
                msg=(
                    f"{name} is defined in constants.py but not named "
                    f"in docs/ADMISSION_POLICY_v2.4.x.md. Either update "
                    f"the doc or remove the constant."
                ),
            )

    def test_every_admission_reason_named_in_doc_is_a_constant(self) -> None:
        # Find all identifiers in the doc that match the naming pattern.
        in_doc = set(re.findall(r"ADMISSION_REASON_[A-Z0-9_]+", self.doc_text))
        self.assertTrue(
            in_doc,
            "admission policy doc names no ADMISSION_REASON_* identifiers",
        )
        for name in sorted(in_doc):
            self.assertTrue(
                hasattr(C, name),
                msg=(
                    f"{name} is named in the doctrine doc but not "
                    f"defined in torment_service/migration/constants.py. "
                    f"Either add the constant or fix the doc."
                ),
            )

    def test_admission_reasons_frozenset_matches_individual_constants(self) -> None:
        individual = {
            getattr(C, n)
            for n in dir(C)
            if n.startswith("ADMISSION_REASON_")
        }
        self.assertEqual(
            set(C.ADMISSION_REASONS),
            individual,
            msg="ADMISSION_REASONS frozenset drifted from per-reason constants",
        )

    # ── Gate-1 classes ────────────────────────────────────────────

    def test_every_gate1_class_constant_is_named_in_doc(self) -> None:
        names = {
            n for n in dir(C)
            if n.startswith("GATE1_CLASS_") and not n.startswith("GATE1_CLASSES")
        }
        self.assertEqual(
            len(names),
            7,
            msg="expected exactly 7 GATE1_CLASS_* constants (one per gate-1 class)",
        )
        for name in sorted(names):
            self.assertIn(
                name,
                self.doc_text,
                msg=(
                    f"{name} is defined in constants.py but not named "
                    f"in docs/ADMISSION_POLICY_v2.4.x.md"
                ),
            )

    def test_every_gate1_class_named_in_doc_is_a_constant(self) -> None:
        in_doc = set(re.findall(r"GATE1_CLASS_[A-Z0-9_]+", self.doc_text))
        self.assertTrue(in_doc, "doc names no GATE1_CLASS_* identifiers")
        for name in sorted(in_doc):
            self.assertTrue(
                hasattr(C, name),
                msg=f"{name} appears in doc but not in constants.py",
            )

    def test_gate1_classes_frozenset_matches_individual_constants(self) -> None:
        individual = {
            getattr(C, n)
            for n in dir(C)
            if n.startswith("GATE1_CLASS_") and n != "GATE1_CLASSES"
        }
        self.assertEqual(
            set(C.GATE1_CLASSES),
            individual,
            msg="GATE1_CLASSES frozenset drifted from per-class constants",
        )

    # ── Re-run decisions ─────────────────────────────────────────

    def test_every_rerun_decision_is_named_in_doc_table(self) -> None:
        # Each RERUN_DECISION_* value (the string, not the identifier)
        # must appear in the doc — the re-run policy table names them
        # by value (FIRST_EVALUATION, BUMP_ONLY, APPLY, BLOCK_AND_REVIEW).
        for name in dir(C):
            if not name.startswith("RERUN_DECISION_"):
                continue
            if name == "RERUN_DECISIONS":
                continue
            value = getattr(C, name)
            self.assertIn(
                value,
                self.doc_text,
                msg=(
                    f"rerun decision {name}={value!r} is not named in "
                    f"the doctrine doc re-run policy table"
                ),
            )

    def test_rerun_decisions_frozenset_matches_individual_constants(self) -> None:
        individual = {
            getattr(C, n)
            for n in dir(C)
            if n.startswith("RERUN_DECISION_") and n != "RERUN_DECISIONS"
        }
        self.assertEqual(
            set(C.RERUN_DECISIONS),
            individual,
            msg="RERUN_DECISIONS frozenset drifted from per-decision constants",
        )

    # ── Policy version ───────────────────────────────────────────

    def test_current_policy_version_appears_verbatim_in_doc(self) -> None:
        self.assertIn(
            C.ADMISSION_POLICY_VERSION,
            self.doc_text,
            msg=(
                f"ADMISSION_POLICY_VERSION={C.ADMISSION_POLICY_VERSION!r} "
                f"is not named in the doctrine doc. Bumping the version "
                f"in constants.py requires adding a matching row in the "
                f"version history table and updating any dependent prose."
            ),
        )

    # ── Empty-in-commit-A postures ───────────────────────────────

    def test_class_7_zero_event_artifact_patterns_is_empty(self) -> None:
        # Code-side: the tuple is empty.
        self.assertEqual(
            C.ZERO_EVENT_ARTIFACT_PATTERNS,
            (),
            msg=(
                "ZERO_EVENT_ARTIFACT_PATTERNS is non-empty. Adding an "
                "entry to this tuple is a doctrine change: it must be "
                "justified against an observed row in a dry-run report "
                "and requires bumping ADMISSION_POLICY_VERSION."
            ),
        )

    def test_doc_explicitly_marks_class_7_empty_posture(self) -> None:
        # Decision 4 required the empty class-7 posture to be stated
        # *explicitly* as a deliberate conservative default, so a future
        # reader doesn't mistake it for an oversight.
        self.assertRegex(
            self.doc_text,
            r"deliberate conservative default",
            msg=(
                "doctrine doc does not explicitly state that the class-7 "
                "empty posture is a deliberate conservative default"
            ),
        )

    def test_doc_explicitly_marks_class_6_empty_mapping_table(self) -> None:
        # Class 6's deprecated-vocabulary mapping table ships empty in
        # commit A; the doc must acknowledge this is intentional.
        self.assertIn(
            "empty in commit A",
            self.doc_text,
            msg=(
                "doctrine doc does not state that the class-6 deprecated "
                "vocabulary mapping table is empty in commit A"
            ),
        )

    # ── Sentinel visibility ──────────────────────────────────────

    def test_sentinel_source_type_is_named_in_doc(self) -> None:
        # SOURCE_GATE1_UNRECOVERABLE is a storage sentinel, not an
        # admissible class. The doc must identify it so future readers
        # understand what ``source_type: gate1_unrecoverable`` on a
        # stored row means.
        self.assertIn(
            "SOURCE_GATE1_UNRECOVERABLE",
            self.doc_text,
            msg="sentinel SOURCE_GATE1_UNRECOVERABLE is not named in the doc",
        )
        self.assertIn(
            C.SOURCE_GATE1_UNRECOVERABLE,  # the literal string value
            self.doc_text,
            msg=(
                f"sentinel value {C.SOURCE_GATE1_UNRECOVERABLE!r} "
                f"(the string actually written to storage) is not named "
                f"in the doc"
            ),
        )


if __name__ == "__main__":
    unittest.main()
