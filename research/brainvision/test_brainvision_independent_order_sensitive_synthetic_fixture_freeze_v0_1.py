"""Bounded generator, reducer, and freeze-library tests for the S1B infrastructure.

Descriptor-blind. Standard-library only. These tests exercise: canonical seed
shape validation, scan-record construction and its eleven-step validation, the
single shared reducer (duplicate collapse, first-eight stopping, malformed
early-stop, and instrumented non-over-consumption), the real seed-stream
pipeline, canonical manifest construction / serialization / hashing, candidate
comparison, deterministic finalization, the two failure-manifest builders, and
lexical + AST static source-boundary validation.

No seed scan of the canonical space is performed; only short explicit seed lists
and hand-authored records are used, so the reducer never contacts seed tuple 17
or later, never requests a ninth accepted fixture, and never touches a record
after a malformed one -- each of these is asserted with an instrumented
iterator. Source-boundary validation is exercised with bounded in-memory source
strings only; no test reads any source file from disk. The tests never import,
construct, or evaluate the challenger descriptor, never contact PsiTRS or the
frozen family, and never touch production. ``unittest`` and plain assertions
only; ``pytest`` is not imported. No ``if __name__ == '__main__'`` block is
present.
"""

import copy
import hashlib
import unittest
from unittest import mock

# The authorized modules are siblings of this test file; pytest's default
# (prepend) import mode places this directory on sys.path, so no filesystem
# path resolution is performed here.
import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as verifier
import independent_order_sensitive_synthetic_fixture_generator_v0_1 as generator
import independent_order_sensitive_synthetic_fixture_freeze_v0_1 as freeze


# --------------------------------------------------------------------------- #
# Instrumented iterator that proves the reducer never over-consumes.
# --------------------------------------------------------------------------- #

class _CountingIterator:
    """Counts consumed items; raises if consumption reaches ``explode_after``.

    The reducer's lazy contract is verified by placing a booby-trapped element
    just past the point at which the reducer must stop requesting records; if
    that element is ever requested the test fails loudly.
    """

    def __init__(self, items, explode_after=None):
        self._items = list(items)
        self.consumed = 0
        self._explode_after = explode_after

    def __iter__(self):
        return self

    def __next__(self):
        if self._explode_after is not None and self.consumed >= self._explode_after:
            raise AssertionError(
                "reducer requested item %d, past the permitted stopping point" % self.consumed)
        if self.consumed >= len(self._items):
            raise StopIteration
        item = self._items[self.consumed]
        self.consumed += 1
        return item


def _fab_key(lead, i):
    """A fabricated 64-character binary key beginning with ``lead`` (0 or 1)."""
    return lead + format(i, "b").zfill(63)


def _fab_pair(i):
    """A fabricated well-ordered pair-duplicate key as an exact tuple (key_0 < key_1)."""
    return (_fab_key("0", i), _fab_key("1", i))


def _eligible_record(i, pair=None):
    pk = _fab_pair(i) if pair is None else pair
    return {
        "seed_tuple": (1, 2, 1, 2),   # actual tuple: the exact seed-tuple contract
        "eligible": True,
        "eligibility_rejection_reason": None,
        "pair_duplicate_key": pk,
        "fixture_record": {"pair_duplicate_key": pk, "tag": i},
    }


def _ineligible_record(reason):
    return {
        "seed_tuple": (1, 2, 1, 2),   # actual tuple: the exact seed-tuple contract
        "eligible": False,
        "eligibility_rejection_reason": reason,
        "pair_duplicate_key": None,
        "fixture_record": None,
    }


# The known fixed positive-control seed: C={0,25,55}, D={0,49,57} reconstructs
# the fixed pair (H0, H1). It is an explicit hand-authored seed used to build a
# real, fully-valid eligible fixture record via the real pipeline. It is NOT a
# canonical seed scan and NOT discovery of any generated first-eight fixture.
_FIXED_SEED = (25, 55, 49, 57)


def _real_scan_record():
    support_a, support_b = generator.construct_pair_from_seed(_FIXED_SEED)
    eligibility = verifier.evaluate_pair_eligibility(support_a, support_b)
    return generator.build_scan_record(_FIXED_SEED, eligibility)


# Built once; each test deep-copies before corrupting a single field.
_REAL_FIXTURE_RECORD = _real_scan_record()["fixture_record"]
_REAL_PAIR_KEY = _REAL_FIXTURE_RECORD["pair_duplicate_key"]


def _real_accepted_wrapper(family_index=0, seed_order_position=0):
    fixture = copy.deepcopy(_REAL_FIXTURE_RECORD)
    return {
        "family_index": family_index,
        "seed_order_position": seed_order_position,
        "fixture_record": fixture,
    }


def _corrupt_wrapper(mutate):
    """A real accepted wrapper with one deep-copied field corrupted by ``mutate``
    (which receives the wrapper's fixture_record and mutates it in place)."""
    wrapper = _real_accepted_wrapper()
    mutate(wrapper["fixture_record"])
    return wrapper


# --------------------------------------------------------------------------- #
# Seed enumeration and shape validation
# --------------------------------------------------------------------------- #

class SeedEnumerationTests(unittest.TestCase):
    def test_canonical_seed_generator_is_lazy_and_starts_at_1212(self):
        it = generator.iter_canonical_seed_tuples()
        self.assertTrue(hasattr(it, "__next__"))
        first_five = []
        for seed in it:
            first_five.append(seed)
            if len(first_five) == 5:
                break  # bounded: never enumerate the full canonical space
        self.assertEqual(first_five[0], (1, 2, 1, 2))
        # Inner d2 advances fastest, then d1.
        self.assertEqual(first_five[1], (1, 2, 1, 3))
        for c1, c2, d1, d2 in first_five:
            self.assertTrue(c1 < c2 and d1 < d2)

    def test_validate_seed_tuple_accepts_canonical_seed(self):
        result = generator.validate_seed_tuple((1, 2, 1, 2))
        self.assertTrue(result["valid"])
        self.assertIsNone(result["failure_code"])
        self.assertIsNone(result["failure_stage"])

    def test_validate_seed_tuple_first_failure_branches(self):
        cases = [
            [1, 2, 1, 2],              # not a tuple
            (1, 2, 1),                 # wrong length
            (True, 2, 1, 2),           # boolean element
            (1, 2.0, 1, 2),            # non-integer element
            (0, 2, 1, 2),              # element below 1
            (1, 64, 1, 2),             # element above 63
            (2, 2, 1, 2),              # c1 >= c2
            (1, 2, 3, 3),              # d1 >= d2
        ]
        for seed in cases:
            result = generator.validate_seed_tuple(seed)
            self.assertFalse(result["valid"], seed)
            self.assertEqual(result["failure_code"], "SEED_ENUMERATION_FAILURE", seed)
            self.assertEqual(result["failure_stage"], "seed_validation", seed)

    def test_construct_pair_from_seed_matches_sumset_and_difference(self):
        a, b = generator.construct_pair_from_seed((1, 2, 1, 2))
        c = (0, 1, 2)
        d = (0, 1, 2)
        expected_a = tuple(sorted({(x + y) % 64 for x in c for y in d}))
        expected_b = tuple(sorted({(x - y) % 64 for x in c for y in d}))
        self.assertEqual(a, expected_a)
        self.assertEqual(b, expected_b)

    def test_construct_pair_from_seed_rejects_invalid_seed(self):
        with self.assertRaises(ValueError):
            generator.construct_pair_from_seed((2, 2, 1, 2))


# --------------------------------------------------------------------------- #
# Scan-record construction and eleven-step validation
# --------------------------------------------------------------------------- #

class ScanRecordTests(unittest.TestCase):
    def test_eligible_scan_record_shape_and_order(self):
        eligibility = verifier.evaluate_pair_eligibility(verifier.FIXED_H0, verifier.FIXED_H1)
        record = generator.build_scan_record((1, 2, 1, 2), eligibility)
        self.assertEqual(tuple(record.keys()), generator.SCAN_RECORD_KEYS)
        self.assertIs(record["eligible"], True)
        self.assertIsNone(record["eligibility_rejection_reason"])
        self.assertEqual(tuple(record["fixture_record"].keys()), generator.FIXTURE_RECORD_KEYS)
        self.assertEqual(generator.validate_scan_record(record)["valid"], True)

    def test_ineligible_scan_record_shape(self):
        eligibility = {"eligible": False, "eligibility_rejection_reason": "A2_MISMATCH"}
        record = generator.build_scan_record((1, 2, 1, 2), eligibility)
        self.assertEqual(tuple(record.keys()), generator.SCAN_RECORD_KEYS)
        self.assertIs(record["eligible"], False)
        self.assertEqual(record["eligibility_rejection_reason"], "A2_MISMATCH")
        self.assertIsNone(record["pair_duplicate_key"])
        self.assertIsNone(record["fixture_record"])
        self.assertEqual(generator.validate_scan_record(record)["valid"], True)

    def test_validate_scan_record_eleven_malformed_branches(self):
        # Records whose intended failure is a step later than 4 carry an actual
        # tuple seed so they pass step 4 and reach the branch under test.
        pk = _fab_pair(1)
        good_fixture = {"pair_duplicate_key": pk, "tag": 1}
        malformed = [
            # 1. not an ordered mapping
            [],
            # 2. wrong key set (missing fixture_record)
            {"seed_tuple": (1, 2, 1, 2), "eligible": True,
             "eligibility_rejection_reason": None, "pair_duplicate_key": pk},
            # 3. right keys, wrong iteration order
            {"eligible": True, "seed_tuple": (1, 2, 1, 2),
             "eligibility_rejection_reason": None, "pair_duplicate_key": pk,
             "fixture_record": good_fixture},
            # 4. invalid seed_tuple contract: an actual tuple with c1 >= c2
            {"seed_tuple": (2, 2, 1, 2), "eligible": True,
             "eligibility_rejection_reason": None, "pair_duplicate_key": pk,
             "fixture_record": good_fixture},
            # 5. eligible is not a JSON boolean
            {"seed_tuple": (1, 2, 1, 2), "eligible": 1,
             "eligibility_rejection_reason": None, "pair_duplicate_key": pk,
             "fixture_record": good_fixture},
            # 6. eligible true but rejection reason not null
            {"seed_tuple": (1, 2, 1, 2), "eligible": True,
             "eligibility_rejection_reason": "A2_MISMATCH", "pair_duplicate_key": pk,
             "fixture_record": good_fixture},
            # 7. eligible true but malformed pair key (valid tuple, key_0 >= key_1)
            {"seed_tuple": (1, 2, 1, 2), "eligible": True,
             "eligibility_rejection_reason": None,
             "pair_duplicate_key": (_fab_key("1", 1), _fab_key("0", 1)),
             "fixture_record": {"pair_duplicate_key": (_fab_key("1", 1), _fab_key("0", 1))}},
            # 8. eligible true but fixture_record key mismatch
            {"seed_tuple": (1, 2, 1, 2), "eligible": True,
             "eligibility_rejection_reason": None, "pair_duplicate_key": pk,
             "fixture_record": {"pair_duplicate_key": _fab_pair(2)}},
            # 9. eligible false but rejection reason not canonical
            {"seed_tuple": (1, 2, 1, 2), "eligible": False,
             "eligibility_rejection_reason": "NOT_A_REASON", "pair_duplicate_key": None,
             "fixture_record": None},
            # 10. eligible false but pair key not null
            {"seed_tuple": (1, 2, 1, 2), "eligible": False,
             "eligibility_rejection_reason": "A2_MISMATCH", "pair_duplicate_key": pk,
             "fixture_record": None},
            # 11. eligible false but fixture_record not null
            {"seed_tuple": (1, 2, 1, 2), "eligible": False,
             "eligibility_rejection_reason": "A2_MISMATCH", "pair_duplicate_key": None,
             "fixture_record": {}},
        ]
        for index, record in enumerate(malformed):
            result = generator.validate_scan_record(record)
            self.assertFalse(result["valid"], "branch %d unexpectedly valid" % (index + 1))
            self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID", index + 1)
            self.assertEqual(result["failure_stage"], "scan_record_validation", index + 1)

    def test_list_seed_tuple_record_is_malformed_without_coercion(self):
        # A record whose seed_tuple is a LIST of otherwise-valid contents must
        # fail scan-record validation at step 4 (no coercion to a tuple).
        pk = _fab_pair(5)
        list_seed_record = {
            "seed_tuple": [1, 2, 1, 2],
            "eligible": True,
            "eligibility_rejection_reason": None,
            "pair_duplicate_key": pk,
            "fixture_record": {"pair_duplicate_key": pk, "tag": 5},
        }
        result = generator.validate_scan_record(list_seed_record)
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        self.assertEqual(result["failure_stage"], "scan_record_validation")

    def test_list_seed_tuple_record_is_non_disruptive_in_reducer(self):
        # The malformed list-seed record must not enter accepted records, must
        # not alter seen keys / duplicate / rejection counts accumulated before
        # it, and must not cause the following record to be consumed.
        list_seed_record = {
            "seed_tuple": [1, 2, 1, 2], "eligible": True,
            "eligibility_rejection_reason": None, "pair_duplicate_key": _fab_pair(5),
            "fixture_record": {"pair_duplicate_key": _fab_pair(5), "tag": 5},
        }
        records = [_eligible_record(0), _ineligible_record("A2_MISMATCH"),
                   list_seed_record, _eligible_record(9)]
        it = _CountingIterator(records, explode_after=3)
        result = generator.reduce_scan_records(it, [], 8)
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        self.assertEqual(result["failure_stage"], "scan_record_validation")
        self.assertEqual(len(result["accepted_records"]), 1)          # only pre-malformed accept
        self.assertEqual(result["accepted_records"][0]["fixture_record"]["tag"], 0)
        self.assertEqual(result["eligibility_rejection_counts"]["A2_MISMATCH"], 1)
        self.assertEqual(result["eligible_duplicate_count"], 0)       # seen keys unaltered
        self.assertEqual(it.consumed, 3)                              # following record not consumed

    def test_list_pair_key_fails_branch_7_without_coercion(self):
        # A list pair key (equivalent elements) is not an exact tuple -> branch 7.
        pk_list = [_fab_key("0", 5), _fab_key("1", 5)]
        record = {"seed_tuple": (1, 2, 1, 2), "eligible": True,
                  "eligibility_rejection_reason": None, "pair_duplicate_key": pk_list,
                  "fixture_record": {"pair_duplicate_key": pk_list}}
        result = generator.validate_scan_record(record)
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")

    def test_tuple_enclosing_key_with_list_fixture_key_fails_branch_8(self):
        # Valid tuple enclosing key passes branch 7; a list fixture key with the
        # same elements is not equal to the tuple -> branch 8.
        pk = _fab_pair(6)
        record = {"seed_tuple": (1, 2, 1, 2), "eligible": True,
                  "eligibility_rejection_reason": None, "pair_duplicate_key": pk,
                  "fixture_record": {"pair_duplicate_key": list(pk)}}
        result = generator.validate_scan_record(record)
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")

    def test_valid_tuple_key_record_is_accepted(self):
        result = generator.reduce_scan_records([_eligible_record(0)], [], 8)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["accepted_records"]), 1)

    def test_malformed_list_pair_key_record_is_non_disruptive(self):
        pk_list = [_fab_key("0", 5), _fab_key("1", 5)]
        bad = {"seed_tuple": (1, 2, 1, 2), "eligible": True,
               "eligibility_rejection_reason": None, "pair_duplicate_key": pk_list,
               "fixture_record": {"pair_duplicate_key": pk_list}}
        it = _CountingIterator([_eligible_record(0), bad, _eligible_record(9)], explode_after=2)
        result = generator.reduce_scan_records(it, [], 8)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["accepted_records"]), 1)   # no state mutation past the accept
        self.assertEqual(result["eligible_duplicate_count"], 0)
        self.assertEqual(it.consumed, 2)                        # following record not consumed


# --------------------------------------------------------------------------- #
# The single shared reducer
# --------------------------------------------------------------------------- #

class ReducerTests(unittest.TestCase):
    def test_accepts_exactly_eight_and_never_requests_a_ninth(self):
        # Eight unique-accept records, then a booby-trapped tail.
        records = [_eligible_record(i) for i in range(8)] + [_eligible_record(99), _eligible_record(98)]
        it = _CountingIterator(records, explode_after=8)
        result = generator.reduce_scan_records(it, [], 8)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["accepted_records"]), 8)
        self.assertTrue(result["reached_acceptance_limit"])
        self.assertEqual(result["records_consumed"], 8)
        self.assertEqual(it.consumed, 8)  # the ninth record was never requested
        self.assertEqual([af["family_index"] for af in result["accepted_records"]], list(range(8)))
        self.assertEqual(result["accepted_seed_order_positions"], list(range(8)))

    def test_accepted_record_wraps_fixture_record_unchanged(self):
        # An opaque fixture record with multiple fields, nested data, a
        # nontrivial (non-alphabetical, pair-key-not-first) key order, and the
        # required pair_duplicate_key.
        pk = _fab_pair(3)
        fixture = {}
        fixture["zeta_field"] = [3, 1, 2]
        fixture["pair_duplicate_key"] = pk
        fixture["nested_opaque"] = {"beta": {"deep": [9, 8, 7]}, "alpha": 1}
        fixture["carried_note"] = "opaque-value"
        record = {
            "seed_tuple": (1, 2, 1, 2),
            "eligible": True,
            "eligibility_rejection_reason": None,
            "pair_duplicate_key": pk,
            "fixture_record": fixture,
        }
        # Snapshot the input's exact key order and (key, value) pairs before the call.
        items_before = list(fixture.items())
        keys_before = list(fixture.keys())

        result = generator.reduce_scan_records([record], [], 8)
        accepted = result["accepted_records"][0]

        # Acceptance metadata lives OUTSIDE the opaque mapping, in the wrapper.
        self.assertEqual(tuple(accepted.keys()), generator.ACCEPTED_RECORD_KEYS)
        self.assertEqual(accepted["family_index"], 0)
        self.assertEqual(accepted["seed_order_position"], 0)

        # The opaque fixture record is preserved exactly: same object, same keys,
        # same key order, same values, same nested values -- nothing injected,
        # prepended, appended, removed, renamed, or reordered inside it.
        carried = accepted["fixture_record"]
        self.assertIs(carried, fixture)
        self.assertEqual(list(carried.keys()), keys_before)
        self.assertEqual(list(carried.items()), items_before)
        self.assertEqual(carried["nested_opaque"], {"beta": {"deep": [9, 8, 7]}, "alpha": 1})

        # The original input object was not mutated by acceptance.
        self.assertEqual(list(fixture.items()), items_before)
        self.assertEqual(list(fixture.keys()), keys_before)
        # No acceptance-metadata key leaked into the opaque mapping.
        self.assertNotIn("family_index", fixture)
        self.assertNotIn("seed_order_position", fixture)

    def test_duplicate_pair_key_collapses_to_one_acceptance(self):
        result = generator.reduce_scan_records([_eligible_record(0), _eligible_record(0)], [], 8)
        self.assertEqual(len(result["accepted_records"]), 1)
        self.assertEqual(result["eligible_duplicate_count"], 1)

    def test_initial_seen_pair_keys_excludes_matching_record(self):
        seed_key = tuple(_fab_pair(0))
        result = generator.reduce_scan_records(
            [_eligible_record(0), _eligible_record(1)], [seed_key], 8)
        self.assertEqual(len(result["accepted_records"]), 1)
        self.assertEqual(result["accepted_records"][0]["fixture_record"]["tag"], 1)
        self.assertEqual(result["eligible_duplicate_count"], 1)

    def test_fixed_fixture_pair_key_is_excluded_when_seeded(self):
        fixed_key = generator.fixed_fixture_pair_key()
        self.assertEqual(fixed_key, verifier.pair_duplicate_key(verifier.FIXED_H0, verifier.FIXED_H1))
        self.assertIsInstance(fixed_key, tuple)
        record = _eligible_record(0, pair=fixed_key)   # exact tuple key
        result = generator.reduce_scan_records([record], [fixed_key], 8)
        self.assertEqual(len(result["accepted_records"]), 0)
        self.assertEqual(result["eligible_duplicate_count"], 1)

    def test_ineligible_records_are_counted_by_reason(self):
        result = generator.reduce_scan_records(
            [_ineligible_record("A2_MISMATCH"), _ineligible_record("A2_MISMATCH"),
             _eligible_record(0)], [], 8)
        self.assertEqual(result["eligibility_rejection_counts"]["A2_MISMATCH"], 2)
        self.assertEqual(len(result["accepted_records"]), 1)

    def test_malformed_record_stops_immediately_and_preserves_prior_state(self):
        # [accept, ineligible, malformed, booby-trap]; the fourth record must
        # never be requested, and the malformed record must not alter the seen
        # keys, duplicate count, or rejection counts accumulated before it.
        records = [_eligible_record(0), _ineligible_record("A2_MISMATCH"),
                   {"eligible": True}, _eligible_record(7)]
        it = _CountingIterator(records, explode_after=3)
        result = generator.reduce_scan_records(it, [], 8)
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        self.assertEqual(result["failure_stage"], "scan_record_validation")
        self.assertEqual(len(result["accepted_records"]), 1)  # prior state preserved
        self.assertEqual(it.consumed, 3)  # no record requested after the malformed one
        # Prior valid reduction state only -- malformed record altered nothing.
        self.assertEqual(result["accepted_records"][0]["fixture_record"]["tag"], 0)
        self.assertEqual(result["eligibility_rejection_counts"]["A2_MISMATCH"], 1)
        self.assertEqual(result["eligible_duplicate_count"], 0)


# --------------------------------------------------------------------------- #
# Seed-stream pipeline (real mathematics feeding the single reducer)
# --------------------------------------------------------------------------- #

class SeedStreamTests(unittest.TestCase):
    def test_short_valid_stream_exhausts_with_ordered_diagnostics(self):
        result = generator.scan_seed_stream([(1, 2, 3, 4), (2, 3, 4, 5)], [])
        self.assertTrue(result["valid"])
        diagnostics = result["search_diagnostics"]
        self.assertEqual(tuple(diagnostics.keys()), freeze.SEARCH_DIAGNOSTICS_KEYS)
        self.assertEqual(diagnostics["total_seeds_visited"], 2)
        self.assertEqual(diagnostics["terminal_seed_tuple"], [2, 3, 4, 5])
        self.assertEqual(diagnostics["terminal_status"], "SEED_SPACE_EXHAUSTED")

    def test_malformed_seed_stops_scan_without_over_consuming(self):
        seeds = _CountingIterator([(1, 2, 3, 4), (0, 2, 1, 2), (5, 6, 7, 8)], explode_after=2)
        result = generator.scan_seed_stream(seeds, [])
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "SEED_ENUMERATION_FAILURE")
        self.assertEqual(result["failure_stage"], "seed_validation")
        self.assertEqual(result["total_seeds_visited"], 2)
        self.assertEqual(result["terminal_seed_tuple"], [0, 2, 1, 2])
        self.assertEqual(seeds.consumed, 2)  # the third seed was never requested

    def test_malformed_list_seed_invokes_no_downstream_operation(self):
        # A malformed list seed must be rejected before any construction,
        # eligibility, pair-key, or scan-record work, and the following seed
        # must not be requested. Every downstream operation is patched to fail
        # loudly if called.
        seeds = _CountingIterator([[1, 2, 1, 2], (3, 4, 5, 6)], explode_after=1)
        with mock.patch.object(generator, "construct_pair_from_seed") as construct_mock, \
             mock.patch.object(generator, "build_scan_record") as build_mock, \
             mock.patch.object(verifier, "evaluate_pair_eligibility") as eligibility_mock, \
             mock.patch.object(verifier, "pair_duplicate_key") as pair_key_mock:
            result = generator.scan_seed_stream(seeds, [])
        self.assertFalse(result["valid"])
        self.assertEqual(result["failure_code"], "SEED_ENUMERATION_FAILURE")
        self.assertEqual(result["failure_stage"], "seed_validation")
        self.assertEqual(result["total_seeds_visited"], 1)
        self.assertEqual(result["terminal_seed_tuple"], [1, 2, 1, 2])
        construct_mock.assert_not_called()
        build_mock.assert_not_called()
        eligibility_mock.assert_not_called()
        pair_key_mock.assert_not_called()
        self.assertEqual(seeds.consumed, 1)   # following seed not requested


# --------------------------------------------------------------------------- #
# Canonical serialization and hashing
# --------------------------------------------------------------------------- #

class CanonicalSerializationTests(unittest.TestCase):
    def test_fixed_key_order_is_preserved_not_sorted(self):
        payload = {"b": 1, "a": 2}
        self.assertEqual(freeze._canonical_json_bytes(payload, "serialization"), b'{"b":1,"a":2}\n')

    def test_exactly_one_terminal_newline_and_compact_separators(self):
        data = freeze._canonical_json_bytes({"x": [1, 2], "y": {"z": 3}}, "serialization")
        self.assertTrue(data.endswith(b"\n"))
        self.assertFalse(data.endswith(b"\n\n"))
        self.assertEqual(data.count(b"\n"), 1)
        self.assertNotIn(b", ", data)
        self.assertNotIn(b": ", data)

    def test_nan_and_non_serializable_raise_serialization_failure(self):
        for bad in (float("nan"), {"s": {1, 2}}):
            with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
                freeze._canonical_json_bytes(bad, "serialization")
            self.assertEqual(ctx.exception.failure_code, "SERIALIZATION_FAILURE")
            self.assertEqual(ctx.exception.failure_stage, "serialization")


class _ManifestFixtures:
    """Shared manifest-construction helpers (not a test case)."""

    def _search_diagnostics(self, total=3):
        return {
            "total_seeds_visited": total,
            "eligibility_rejection_counts": freeze._empty_rejection_counts(),
            "eligible_duplicate_count": 0,
            "accepted_seed_order_positions": [],
            "terminal_seed_tuple": None,
            "terminal_status": "SEED_SPACE_EXHAUSTED",
        }

    def _source_identity(self):
        allow = freeze.AUTHORIZED_ALLOWLIST
        return {
            "generator_source_path": allow[1],
            "generator_git_blob": "a" * 40,
            "generator_raw_sha256": "b" * 64,
            "verifier_source_path": allow[0],
            "verifier_git_blob": "c" * 40,
            "verifier_raw_sha256": "d" * 64,
            "test_source_identities": [],
            "repository_commit": "20f5297",
            "python_version": "3.11",
        }

    def _candidate(self, total=3, accepted=None):
        fixed = verifier.verify_fixed_fixture()
        configuration_identity = freeze.build_configuration_identity({"policy": "v0.1"})
        return freeze.build_candidate_manifest(
            fixed, accepted or [], self._search_diagnostics(total),
            self._source_identity(), configuration_identity)


class ManifestBuildTests(_ManifestFixtures, unittest.TestCase):
    def test_candidate_manifest_key_order_and_defaults(self):
        manifest = self._candidate()
        self.assertEqual(tuple(manifest.keys()), freeze.MANIFEST_TOP_LEVEL_KEYS)
        self.assertIs(manifest["family_frozen"], False)
        self.assertEqual(manifest["validation"], {"valid": True, "failure_stage": None, "detail": None})
        self.assertEqual(manifest["ordered_failure_codes"], [])
        digest = manifest["manifest_payload_sha256"]
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)
        self.assertEqual(tuple(manifest["source_identity"].keys()), freeze.SOURCE_IDENTITY_KEYS)
        self.assertEqual(tuple(manifest["search_diagnostics"].keys()), freeze.SEARCH_DIAGNOSTICS_KEYS)

    def test_payload_hash_is_a_true_sha256_over_the_projection(self):
        manifest = self._candidate()
        payload_bytes = freeze.canonical_payload_bytes(manifest)
        self.assertNotIn(b"manifest_payload_sha256", payload_bytes)
        self.assertIn(b"schema", payload_bytes)
        self.assertEqual(manifest["manifest_payload_sha256"],
                         hashlib.sha256(payload_bytes).hexdigest())

    def test_external_manifest_sha256_is_a_true_sha256_over_full_bytes(self):
        manifest = self._candidate()
        manifest_bytes = freeze.canonical_manifest_bytes(manifest)
        self.assertEqual(freeze.external_manifest_sha256(manifest),
                         hashlib.sha256(manifest_bytes).hexdigest())

    def test_canonical_manifest_bytes_requires_populated_hash(self):
        manifest = self._candidate()
        manifest["manifest_payload_sha256"] = None
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.canonical_manifest_bytes(manifest)
        self.assertEqual(ctx.exception.failure_code, "SERIALIZATION_FAILURE")

    def test_configuration_identity_hash_matches(self):
        payload = {"policy": "v0.1", "n": 64}
        identity = freeze.build_configuration_identity(payload)
        expected = hashlib.sha256(
            freeze._canonical_json_bytes(payload, "serialization")).hexdigest()
        self.assertEqual(identity["configuration_sha256"], expected)

    def test_bad_source_identity_key_set_raises_schema_failure(self):
        fixed = verifier.verify_fixed_fixture()
        configuration_identity = freeze.build_configuration_identity({"policy": "v0.1"})
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.build_candidate_manifest(
                fixed, [], self._search_diagnostics(), {"only": "one"}, configuration_identity)
        self.assertEqual(ctx.exception.failure_code, "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(ctx.exception.failure_stage, "replay_comparison")

    def test_bad_search_diagnostics_key_set_raises_schema_failure(self):
        fixed = verifier.verify_fixed_fixture()
        configuration_identity = freeze.build_configuration_identity({"policy": "v0.1"})
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.build_candidate_manifest(
                fixed, [], {"total_seeds_visited": 1}, self._source_identity(),
                configuration_identity)
        self.assertEqual(ctx.exception.failure_code, "MANIFEST_SCHEMA_FAILURE")

    def test_fixed_fixture_failure_manifest(self):
        fixed = verifier.verify_fixed_fixture()
        fixed = dict(fixed)
        fixed["validation"] = {"valid": False,
                               "failure_code": "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE",
                               "detail": None}
        configuration_identity = freeze.build_configuration_identity({"policy": "v0.1"})
        manifest = freeze.build_fixed_fixture_failure_manifest(
            fixed, self._source_identity(), configuration_identity)
        self.assertIs(manifest["family_frozen"], False)
        self.assertEqual(manifest["ordered_failure_codes"], ["FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE"])
        self.assertEqual(manifest["search_diagnostics"]["terminal_status"], "FIXED_FIXTURE_FAILURE")
        self.assertEqual(manifest["validation"]["valid"], False)
        self.assertEqual(manifest["validation"]["failure_stage"], "fixed_fixture")

    def test_seed_exhaustion_failure_manifest_forces_status_and_code(self):
        fixed = verifier.verify_fixed_fixture()
        configuration_identity = freeze.build_configuration_identity({"policy": "v0.1"})
        # Supply a non-exhaustion terminal status; the builder must force it.
        diagnostics = self._search_diagnostics()
        diagnostics["terminal_status"] = "ACCEPTED_EIGHT"
        manifest = freeze.build_seed_exhaustion_failure_manifest(
            fixed, [], diagnostics, self._source_identity(), configuration_identity)
        self.assertIs(manifest["family_frozen"], False)
        self.assertEqual(manifest["ordered_failure_codes"], ["INSUFFICIENT_UNIQUE_FIXTURES"])
        self.assertEqual(manifest["search_diagnostics"]["terminal_status"], "SEED_SPACE_EXHAUSTED")
        self.assertEqual(manifest["validation"]["failure_stage"], "seed_exhaustion")


class ComparisonAndFinalizationTests(_ManifestFixtures, unittest.TestCase):
    def test_identical_candidates_match(self):
        bundle_a = freeze.build_candidate_pass_bundle(self._candidate())
        bundle_b = freeze.build_candidate_pass_bundle(self._candidate())
        result = freeze.compare_candidate_passes(bundle_a, bundle_b)
        self.assertTrue(result["matches"])
        self.assertIsNone(result["failure_code"])
        self.assertEqual(result["mismatch_reasons"], [])

    def test_mismatch_reasons_follow_canonical_order(self):
        bundle_a = freeze.build_candidate_pass_bundle(self._candidate(total=3))
        bundle_b = freeze.build_candidate_pass_bundle(self._candidate(total=99))
        result = freeze.compare_candidate_passes(bundle_a, bundle_b)
        self.assertFalse(result["matches"])
        self.assertEqual(result["failure_code"], "REPLAY_MISMATCH")
        self.assertEqual(result["failure_stage"], "replay_comparison")
        self.assertEqual(result["mismatch_reasons"], [
            "canonical_payload_bytes_mismatch",
            "manifest_payload_sha256_mismatch",
            "canonical_manifest_bytes_mismatch",
            "external_manifest_sha256_mismatch",
            "search_diagnostics_mismatch",
        ])

    def test_accepted_fixture_order_mismatch_isolated(self):
        base = freeze.build_candidate_pass_bundle(self._candidate())
        variant = dict(base)
        variant["accepted_fixture_order"] = [_fab_pair(5)]
        result = freeze.compare_candidate_passes(base, variant)
        self.assertFalse(result["matches"])
        self.assertEqual(result["mismatch_reasons"], ["accepted_fixture_order_mismatch"])

    def test_accepted_fixture_order_reflects_pair_keys(self):
        bundle = freeze.build_candidate_pass_bundle(
            self._candidate(accepted=[_real_accepted_wrapper()]))
        self.assertEqual(set(bundle.keys()), set(freeze.CANDIDATE_BUNDLE_KEYS))
        self.assertEqual(bundle["accepted_fixture_order"], [_REAL_PAIR_KEY])

    def test_malformed_bundle_raises_schema_failure(self):
        good = freeze.build_candidate_pass_bundle(self._candidate())
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.compare_candidate_passes({"unexpected": 1}, good)
        self.assertEqual(ctx.exception.failure_code, "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(ctx.exception.failure_stage, "replay_comparison")

    def test_finalize_changes_only_family_frozen_and_hash(self):
        candidate = self._candidate()
        comparison = freeze.compare_candidate_passes(
            freeze.build_candidate_pass_bundle(candidate),
            freeze.build_candidate_pass_bundle(self._candidate()))
        bundle = freeze.finalize_authoritative_manifest(candidate, comparison)
        self.assertEqual(set(bundle.keys()), {
            "final_manifest_object", "canonical_payload_bytes", "manifest_payload_sha256",
            "canonical_manifest_bytes", "external_manifest_sha256"})
        final = bundle["final_manifest_object"]
        self.assertIs(final["family_frozen"], True)
        self.assertEqual(tuple(final.keys()), freeze.MANIFEST_TOP_LEVEL_KEYS)
        changed = [k for k in candidate
                   if candidate[k] != final[k]]
        self.assertEqual(sorted(changed), ["family_frozen", "manifest_payload_sha256"])
        self.assertEqual(bundle["manifest_payload_sha256"], final["manifest_payload_sha256"])

    def test_finalize_rejects_non_matching_comparison(self):
        candidate = self._candidate()
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.finalize_authoritative_manifest(candidate, {"matches": False})
        self.assertEqual(ctx.exception.failure_code, "REPLAY_MISMATCH")
        self.assertEqual(ctx.exception.failure_stage, "finalization")


_SUCCESS_COMPARISON = {"matches": True, "failure_code": None, "failure_stage": None,
                       "mismatch_reasons": []}


class DirectSerializationFailureTests(_ManifestFixtures, unittest.TestCase):
    """The direct canonical serialization helpers keep SERIALIZATION_FAILURE /
    serialization when called independently."""

    def test_direct_canonical_payload_bytes_serialization_failure(self):
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.canonical_payload_bytes({"bad": {1, 2}, "manifest_payload_sha256": None})
        self.assertEqual(ctx.exception.failure_code, "SERIALIZATION_FAILURE")
        self.assertEqual(ctx.exception.failure_stage, "serialization")

    def test_direct_canonical_manifest_bytes_serialization_failure(self):
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.canonical_manifest_bytes({"manifest_payload_sha256": "a" * 64, "bad": {1, 2}})
        self.assertEqual(ctx.exception.failure_code, "SERIALIZATION_FAILURE")
        self.assertEqual(ctx.exception.failure_stage, "serialization")


class FinalizationFailureStageTests(_ManifestFixtures, unittest.TestCase):
    """Finalization exposes every final-recomputation failure as
    HASH_IDENTITY_FAILURE / hash_identity (SERIALIZATION_FAILURE must not escape
    finalization); an absent or malformed comparison is REPLAY_MISMATCH /
    finalization."""

    def _expect_through_finalize(self, patched, raised, code, stage):
        candidate = self._candidate()
        with mock.patch.object(freeze, patched, side_effect=raised):
            with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
                freeze.finalize_authoritative_manifest(candidate, dict(_SUCCESS_COMPARISON))
        self.assertEqual(ctx.exception.failure_code, code)
        self.assertEqual(ctx.exception.failure_stage, stage)

    def test_payload_serialization_through_finalization_is_hash_identity(self):
        self._expect_through_finalize(
            "canonical_payload_bytes",
            freeze.SyntheticFixtureProcessFailure("SERIALIZATION_FAILURE", "serialization", "x"),
            "HASH_IDENTITY_FAILURE", "hash_identity")

    def test_manifest_serialization_through_finalization_is_hash_identity(self):
        self._expect_through_finalize(
            "canonical_manifest_bytes",
            freeze.SyntheticFixtureProcessFailure("SERIALIZATION_FAILURE", "serialization", "x"),
            "HASH_IDENTITY_FAILURE", "hash_identity")

    def test_payload_hash_population_through_finalization_is_hash_identity(self):
        self._expect_through_finalize(
            "populate_manifest_payload_hash",
            freeze.SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", "x"),
            "HASH_IDENTITY_FAILURE", "hash_identity")

    def test_external_manifest_hash_through_finalization_is_hash_identity(self):
        self._expect_through_finalize(
            "external_manifest_sha256",
            freeze.SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", "x"),
            "HASH_IDENTITY_FAILURE", "hash_identity")

    def test_exact_successful_comparison_is_accepted(self):
        candidate = self._candidate()
        bundle = freeze.finalize_authoritative_manifest(candidate, dict(_SUCCESS_COMPARISON))
        self.assertIs(bundle["final_manifest_object"]["family_frozen"], True)
        # The real compare_candidate_passes success value is exactly this shape.
        self.assertEqual(
            freeze.compare_candidate_passes(
                freeze.build_candidate_pass_bundle(candidate),
                freeze.build_candidate_pass_bundle(self._candidate())),
            _SUCCESS_COMPARISON)

    def test_non_exact_comparisons_are_replay_mismatch(self):
        candidate = self._candidate()
        bad_comparisons = [
            "not-a-mapping",
            {"matches": True, "failure_code": None, "failure_stage": None},           # missing key
            {"matches": True, "failure_code": None, "failure_stage": None,
             "mismatch_reasons": [], "extra": 1},                                      # extra key
            {"failure_code": None, "failure_stage": None, "mismatch_reasons": [],
             "matches": True},                                                         # wrong key order
            {"matches": 1, "failure_code": None, "failure_stage": None, "mismatch_reasons": []},
            {"matches": False, "failure_code": None, "failure_stage": None, "mismatch_reasons": []},
            {"matches": True, "failure_code": "X", "failure_stage": None, "mismatch_reasons": []},
            {"matches": True, "failure_code": None, "failure_stage": "s", "mismatch_reasons": []},
            {"matches": True, "failure_code": None, "failure_stage": None, "mismatch_reasons": ()},
            {"matches": True, "failure_code": None, "failure_stage": None, "mismatch_reasons": ["x"]},
        ]
        for comparison in bad_comparisons:
            with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
                freeze.finalize_authoritative_manifest(candidate, comparison)
            self.assertEqual(ctx.exception.failure_code, "REPLAY_MISMATCH", comparison)
            self.assertEqual(ctx.exception.failure_stage, "finalization", comparison)


class ReducerToManifestCompositionTests(_ManifestFixtures, unittest.TestCase):
    """A real scan record composes through the reducer wrapper and the strict
    projection into an exact flat committed S1A manifest fixture."""

    def test_scan_record_to_reducer_to_projection_to_flat_manifest_fixture(self):
        scan_record = _real_scan_record()
        fixture_before = copy.deepcopy(scan_record["fixture_record"])
        reduction = generator.reduce_scan_records([scan_record], [], 8)
        self.assertTrue(reduction["valid"])
        wrapper = reduction["accepted_records"][0]
        self.assertEqual(tuple(wrapper.keys()), generator.ACCEPTED_RECORD_KEYS)

        manifest = freeze.build_candidate_manifest(
            verifier.verify_fixed_fixture(), reduction["accepted_records"],
            self._search_diagnostics(), self._source_identity(),
            freeze.build_configuration_identity({"policy": "v0.1"}))
        entry = manifest["accepted_fixtures"][0]

        self.assertEqual(tuple(entry.keys()), freeze.ACCEPTED_FIXTURE_KEYS)
        self.assertNotIn("fixture_record", entry)
        self.assertEqual(entry["family_index"], 0)
        self.assertEqual(entry["seed_order_position"], 0)
        self.assertEqual(entry["pair_duplicate_key"], _REAL_PAIR_KEY)
        self.assertEqual(entry["triple_disagreement_count"], 288)
        for key in freeze.FIXTURE_RECORD_FIELD_KEYS:
            self.assertEqual(entry[key], scan_record["fixture_record"][key])
        # The original opaque fixture record was not mutated.
        self.assertEqual(scan_record["fixture_record"], fixture_before)
        self.assertNotIn("family_index", scan_record["fixture_record"])

    def _expect_projection_failure(self, wrapper):
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.project_accepted_record(wrapper)
        self.assertEqual(ctx.exception.failure_code, "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(ctx.exception.failure_stage, "replay_comparison")

    def test_valid_real_wrapper_projects(self):
        flat = freeze.project_accepted_record(_real_accepted_wrapper())
        self.assertEqual(tuple(flat.keys()), freeze.ACCEPTED_FIXTURE_KEYS)

    def test_wrapper_level_malformations(self):
        def set_family(w, v):
            w["family_index"] = v
        def set_sop(w, v):
            w["seed_order_position"] = v
        w = _real_accepted_wrapper(); set_family(w, True)
        self._expect_projection_failure(w)                                # family_index=True
        w = _real_accepted_wrapper(); set_family(w, -1)
        self._expect_projection_failure(w)                                # negative family_index
        w = _real_accepted_wrapper(); set_sop(w, True)
        self._expect_projection_failure(w)                                # seed_order_position=True
        w = _real_accepted_wrapper(); set_sop(w, -1)
        self._expect_projection_failure(w)                                # negative seed_order_position
        # wrong wrapper key order
        real = _real_accepted_wrapper()
        reordered = {"seed_order_position": 0, "family_index": 0,
                     "fixture_record": real["fixture_record"]}
        self._expect_projection_failure(reordered)
        # non-wrapper
        self._expect_projection_failure({"family_index": 0, "seed_order_position": 0})

    def test_list_level_malformations(self):
        # wrong family-index sequence
        a = _real_accepted_wrapper(0, 0)
        b = _real_accepted_wrapper(2, 1)
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze._project_accepted_records([a, b])
        self.assertEqual(ctx.exception.failure_code, "MANIFEST_SCHEMA_FAILURE")
        # non-increasing seed-order positions
        a = _real_accepted_wrapper(0, 5)
        b = _real_accepted_wrapper(1, 3)
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure):
            freeze._project_accepted_records([a, b])
        # more than K_synthetic accepted fixtures
        overflow = [_real_accepted_wrapper(i, i) for i in range(9)]
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure):
            freeze._project_accepted_records(overflow)

    def test_fixture_field_malformations(self):
        cases = {
            "wrong fixture key order": lambda fr: fr.__setitem__(
                "seed_tuple", fr.pop("seed_tuple")),  # moves seed_tuple to the end
            "list-shaped seed tuple": lambda fr: fr.__setitem__("seed_tuple", [1, 2, 1, 2]),
            "malformed C": lambda fr: fr.__setitem__("C", [0, 1]),
            "malformed D": lambda fr: fr.__setitem__("D", [0, 1, 2, 3]),
            "unsorted support": lambda fr: fr["support_A"].reverse(),
            "duplicate support member": lambda fr: fr.__setitem__(
                "support_A", [0, 0] + fr["support_A"][2:]),
            "out-of-range support member": lambda fr: fr.__setitem__(
                "support_A", [64] + fr["support_A"][1:]),
            "wrong support cardinality": lambda fr: fr.__setitem__("support_A", fr["support_A"][:8]),
            "wrong binary length": lambda fr: fr.__setitem__("binary_A", fr["binary_A"][:-1]),
            "bool in binary": lambda fr: fr["binary_A"].__setitem__(0, True),
            "binary/support disagreement": lambda fr: fr["binary_A"].__setitem__(
                0, 1 - fr["binary_A"][0]),
            "wrong weight": lambda fr: fr.__setitem__("weight_A", 8),
            "malformed A2": lambda fr: fr.__setitem__("A2_A", fr["A2_A"][:-1]),
            "malformed transition table": lambda fr: fr.__setitem__(
                "transition_table_A", [[1, 2, 3], [4, 5, 6]]),
            "bad affine certificate shape": lambda fr: fr["affine_inequivalence_certificate"].__setitem__(
                "search_space_size", 999),
            "bad affine-complement certificate shape":
                lambda fr: fr.__setitem__("affine_complement_inequivalence_certificate", {"x": 1}),
            "wrong triple count": lambda fr: fr.__setitem__("triple_disagreement_count", 999),
            "unordered triple indices": lambda fr: fr["triple_disagreement_indices"].reverse(),
            "duplicate triple indices": lambda fr: fr.__setitem__(
                "triple_disagreement_indices",
                [fr["triple_disagreement_indices"][0]] * fr["triple_disagreement_count"]),
            "invalid lag pair": lambda fr: fr["triple_disagreement_indices"].__setitem__(0, [64, 2]),
            "bad member key": lambda fr: fr.__setitem__("member_orbit_key_A", "0" * 64),
            "list pair key": lambda fr: fr.__setitem__(
                "pair_duplicate_key", list(fr["pair_duplicate_key"])),
            "pair-key disagreement": lambda fr: fr.__setitem__("pair_duplicate_key", _fab_pair(1)),
            "mathematically incorrect but serializable": lambda fr: fr.__setitem__(
                "A2_A", [7] + fr["A2_A"][1:]),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                self._expect_projection_failure(_corrupt_wrapper(mutate))


# --------------------------------------------------------------------------- #
# Static source-boundary validation (bounded in-memory sources only)
# --------------------------------------------------------------------------- #

# Prohibited markers are assembled from fragments purely for readability; no test
# reads any source file from disk, so these are only ever passed as bounded
# in-memory source strings to validate_source_boundary.
_FROZEN_MODULE_TOKEN = "psi" + "_trs"
_FROZEN_F3_MODULE_TOKEN = "algebraic_n64_f3" + "_evaluator"
_FROZEN_PATH_TOKEN = "algebraic_n64_primary_v0_1_f3_" + "evaluation"
_RESULTS_DIR_TOKEN = "research/brainvision/" + "results" + "/"
# Generic historical / frozen / retained module names and path directories.
_GEN_HIST_F3_MODULE = "historical" + "_f3_module"
_GEN_FROZEN_FAMILY_MODULE = "frozen" + "_family_module"
_GEN_RETAINED_FAMILY_MODULE = "retained" + "_family_module"
_GEN_RETAINED_EVIDENCE_MODULE = "retained" + "_evidence_module"
_GEN_PATH_DIRS = tuple(
    "research/brainvision/" + fragment + "/"
    for fragment in ("historical" + "_f3", "frozen" + "_family",
                     "retained" + "_family", "retained" + "_evidence"))


class SourceBoundaryTests(unittest.TestCase):
    """All coverage uses bounded in-memory source strings; nothing is read from
    disk. validate_source_boundary receives (repo-relative path, source text,
    exact allowlist) as explicit inputs."""

    def _expect(self, source_path, source_text, allowlist, code):
        with self.assertRaises(freeze.SyntheticFixtureProcessFailure) as ctx:
            freeze.validate_source_boundary(source_path, source_text, allowlist)
        self.assertEqual(ctx.exception.failure_code, code)
        self.assertEqual(ctx.exception.failure_stage, "source_boundary")

    def _expect_pass(self, source_text):
        result = freeze.validate_source_boundary(
            freeze.AUTHORIZED_ALLOWLIST[2], source_text, freeze.AUTHORIZED_ALLOWLIST)
        self.assertTrue(result["valid"])

    def test_all_five_authorized_paths_pass_with_benign_in_memory_source(self):
        for path in freeze.AUTHORIZED_ALLOWLIST:
            result = freeze.validate_source_boundary(path, "x = 1\n", freeze.AUTHORIZED_ALLOWLIST)
            self.assertTrue(result["valid"], path)
            self.assertEqual(result["normalized_path"], path)

    def test_allowlist_is_exactly_the_five_authorized_paths_in_order(self):
        self.assertEqual(freeze.AUTHORIZED_ALLOWLIST, (
            "research/brainvision/independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
            "research/brainvision/independent_order_sensitive_synthetic_fixture_generator_v0_1.py",
            "research/brainvision/independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
            "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_verifier_v0_1.py",
            "research/brainvision/test_brainvision_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py",
        ))

    def test_path_normalization_accepts_equivalent_relative_path(self):
        freeze_path = freeze.AUTHORIZED_ALLOWLIST[2]
        messy = ("research/./brainvision/tmp/../"
                 "independent_order_sensitive_synthetic_fixture_freeze_v0_1.py")
        result = freeze.validate_source_boundary(messy, "x = 1\n", freeze.AUTHORIZED_ALLOWLIST)
        self.assertTrue(result["valid"])
        self.assertEqual(result["normalized_path"], freeze_path)

    def test_forbidden_imports_including_network_and_capture(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "import numpy", allow, "FORBIDDEN_IMPORT_DETECTED")
        self._expect(p, "import socket", allow, "FORBIDDEN_IMPORT_DETECTED")   # network
        self._expect(p, "import mss", allow, "FORBIDDEN_IMPORT_DETECTED")      # screen capture
        self._expect(p, "x = __import__('os')", allow, "FORBIDDEN_IMPORT_DETECTED")   # dynamic import

    def test_production_kernel_contact_and_main_block(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "import torment_service", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, 'if __name__ == "__main__":\n    x = 1', allow, "PRODUCTION_BOUNDARY_VIOLATION")

    def test_challenger_contact(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "import independent_order_sensitive_descriptor_v0_1", allow,
                     "PROHIBITED_CHALLENGER_CONTACT")

    def test_frozen_family_historical_f3_and_retained_evidence_literals(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "import %s" % _FROZEN_MODULE_TOKEN, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "import %s" % _FROZEN_F3_MODULE_TOKEN, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")   # historical F3 evaluator
        self._expect(p, "PATH = %r" % ("results/" + _FROZEN_PATH_TOKEN + "/x.json"),
                     allow, "PROHIBITED_FROZEN_FAMILY_CONTACT")   # retained-evidence literal

    def test_ownership_failures(self):
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect("research/brainvision/not_authorized.py", "x = 1", allow,
                     "SOURCE_OWNERSHIP_FAILURE")                       # wrong ownership
        self._expect("../escape.py", "x = 1", allow, "SOURCE_OWNERSHIP_FAILURE")        # root escape
        self._expect("/abs/path.py", "x = 1", allow, "SOURCE_OWNERSHIP_FAILURE")        # absolute
        self._expect("C:/drive/path.py", "x = 1", allow, "SOURCE_OWNERSHIP_FAILURE")    # drive-prefixed
        self._expect("//host/share/x.py", "x = 1", allow, "SOURCE_OWNERSHIP_FAILURE")   # UNC-like
        self._expect(allow[2], "x = 1", ("only/one/path.py",), "SOURCE_OWNERSHIP_FAILURE")  # wrong allowlist
        self._expect(allow[2], "x = 1", tuple(reversed(allow)), "SOURCE_OWNERSHIP_FAILURE")  # allowlist order
        self._expect(allow[2], 123, allow, "SOURCE_OWNERSHIP_FAILURE")   # non-string source text

    def test_relative_import_bypasses_are_detected(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "from . import independent_order_sensitive_descriptor_v0_1", allow,
                     "PROHIBITED_CHALLENGER_CONTACT")
        self._expect(p, "from .independent_order_sensitive_descriptor_v0_1 import x", allow,
                     "PROHIBITED_CHALLENGER_CONTACT")
        self._expect(p, "from . import %s" % _FROZEN_F3_MODULE_TOKEN, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")   # relative historical-F3
        self._expect(p, "from .. import %s" % _FROZEN_MODULE_TOKEN, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")   # relative frozen-family

    def test_environment_reads_are_production_violations(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "import os\nx = os.environ['A']", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, "import os\nx = os.environ.get('A')", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, "import os\nx = os.getenv('A')", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, "import os as o\nx = o.getenv('A')", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, "from os import getenv", allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, "from os import environ", allow, "PRODUCTION_BOUNDARY_VIOLATION")

    def test_retained_results_path_literals(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "PATH = %r" % (_RESULTS_DIR_TOKEN + "results.csv"), allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "PATH = %r" % (_RESULTS_DIR_TOKEN + "results.json"), allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "PATH = %r" % _RESULTS_DIR_TOKEN, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")   # retained results directory

    def test_main_block_both_operand_orders(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, 'if __name__ == "__main__":\n    x = 1', allow, "PRODUCTION_BOUNDARY_VIOLATION")
        self._expect(p, 'if "__main__" == __name__:\n    x = 1', allow, "PRODUCTION_BOUNDARY_VIOLATION")

    def test_syntax_error_fails_closed(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        self._expect(p, "def x(:\n    pass", allow, "FORBIDDEN_IMPORT_DETECTED")

    def test_os_assignment_alias_environment_reads(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        # direct assignment alias + getenv
        self._expect(p, "import os\noperating_system = os\noperating_system.getenv('X')",
                     allow, "PRODUCTION_BOUNDARY_VIOLATION")
        # direct assignment alias + environ subscript
        self._expect(p, "import os\nalias = os\ny = alias.environ['X']",
                     allow, "PRODUCTION_BOUNDARY_VIOLATION")
        # two-step alias chain + environ.get
        self._expect(p, "import os as first\nsecond = first\nthird = second\nthird.environ.get('X')",
                     allow, "PRODUCTION_BOUNDARY_VIOLATION")
        # aliased import followed by assignment alias
        self._expect(p, "import os as first\nsecond = first\ny = second.environ['X']",
                     allow, "PRODUCTION_BOUNDARY_VIOLATION")

    def test_environment_alias_false_positive_guards(self):
        # benign alias assignment with no environment read
        self._expect_pass("import os\nalias = os\ny = alias.sep")
        # unrelated object exposing a getenv attribute (even with os imported)
        self._expect_pass(
            "import os\nclass Helper:\n    def getenv(self, name):\n        return name\n"
            "helper = Helper()\nhelper.getenv('X')")

    def test_generic_frozen_retained_module_imports(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        # absolute imports
        self._expect(p, "import %s" % _GEN_HIST_F3_MODULE, allow, "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "import %s" % _GEN_FROZEN_FAMILY_MODULE, allow, "PROHIBITED_FROZEN_FAMILY_CONTACT")
        # relative imports (module portion present)
        self._expect(p, "from ..%s import x" % _GEN_HIST_F3_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "from ..%s import x" % _GEN_FROZEN_FAMILY_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "from ..%s import x" % _GEN_RETAINED_FAMILY_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        self._expect(p, "from ..%s import x" % _GEN_RETAINED_EVIDENCE_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        # relative import with empty module portion (imported alias name)
        self._expect(p, "from .. import %s" % _GEN_RETAINED_FAMILY_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")

    def test_generic_frozen_retained_path_literals(self):
        p = freeze.AUTHORIZED_ALLOWLIST[2]
        allow = freeze.AUTHORIZED_ALLOWLIST
        for directory in _GEN_PATH_DIRS:
            self._expect(p, "PATH = %r" % directory, allow, "PROHIBITED_FROZEN_FAMILY_CONTACT")

    def test_generic_marker_precedence(self):
        allow = freeze.AUTHORIZED_ALLOWLIST
        p = allow[2]
        # forbidden import (15) precedes generic frozen-family (18)
        self._expect(p, "import numpy\nimport %s" % _GEN_FROZEN_FAMILY_MODULE, allow,
                     "FORBIDDEN_IMPORT_DETECTED")
        # bad allowlist (16) precedes generic historical-F3 (18)
        self._expect(p, "import %s" % _GEN_HIST_F3_MODULE, ("only/one/path.py",),
                     "SOURCE_OWNERSHIP_FAILURE")
        # generic retained-family (18) precedes production (19)
        self._expect(p, "import %s\nimport torment_service" % _GEN_RETAINED_FAMILY_MODULE, allow,
                     "PROHIBITED_FROZEN_FAMILY_CONTACT")
        # challenger (17) precedes generic retained-family (18)
        self._expect(p, "import independent_order_sensitive_descriptor_v0_1\nimport %s"
                     % _GEN_RETAINED_FAMILY_MODULE, allow, "PROHIBITED_CHALLENGER_CONTACT")

    def test_first_applicable_code_precedence(self):
        allow = freeze.AUTHORIZED_ALLOWLIST
        # Forbidden import (index 15) precedes source-ownership (index 16).
        self._expect(allow[2], "import numpy", ("only/one/path.py",), "FORBIDDEN_IMPORT_DETECTED")
        # Challenger contact (index 17) precedes production boundary (index 19).
        self._expect(allow[2],
                     "import independent_order_sensitive_descriptor_v0_1\nimport torment_service",
                     allow, "PROHIBITED_CHALLENGER_CONTACT")
        # Syntax error (fail-closed FORBIDDEN, index 15) precedes source-ownership (16).
        self._expect(allow[2], "def x(:", ("only/one/path.py",), "FORBIDDEN_IMPORT_DETECTED")

    def test_process_failure_exposes_code_stage_and_detail(self):
        error = freeze.SyntheticFixtureProcessFailure("REPLAY_MISMATCH", "finalization", "detail text")
        self.assertEqual(error.failure_code, "REPLAY_MISMATCH")
        self.assertEqual(error.failure_stage, "finalization")
        self.assertEqual(error.detail, "detail text")
