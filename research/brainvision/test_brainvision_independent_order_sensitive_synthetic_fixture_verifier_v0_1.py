"""Bounded verifier tests for the S1B synthetic-fixture infrastructure.

Descriptor-blind. Standard-library only. These tests exercise the pure,
integer-only mathematics of the verifier module: fixed-fixture certification
(triple disagreement count = 288), the ordered first-failure eligibility
predicate, the orbit / pair-duplicate keys, and support validation.

The tests never import, construct, or evaluate the challenger descriptor, never
contact PsiTRS or the frozen family, never touch production, and never run any
seed scan. ``unittest`` and plain assertions only; ``pytest`` is not imported.
No ``if __name__ == '__main__'`` block is present (bounded-run discipline).
"""

import unittest
from unittest import mock

# The authorized modules are siblings of this test file; pytest's default
# (prepend) import mode places this directory on sys.path, so no filesystem
# path resolution is performed here.
import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as verifier


# A convenient weight-9 support (nine consecutive residues).
W9 = (0, 1, 2, 3, 4, 5, 6, 7, 8)


class LazyConstantTableTests(unittest.TestCase):
    def test_l3_lag_order_is_3906_with_b_ne_a(self):
        lags = verifier.l3_lags()
        self.assertEqual(len(lags), verifier.L3_ENTRY_COUNT)
        self.assertEqual(len(lags), 3906)
        self.assertEqual(len(set(lags)), 3906)
        for a, b in lags:
            self.assertTrue(1 <= a <= 63)
            self.assertTrue(1 <= b <= 63)
            self.assertNotEqual(a, b)
        # Exact lexicographic order: a outer (1..63), b inner (1..63), omit b == a.
        self.assertEqual(lags[0], (1, 2))
        self.assertEqual(lags[-1], (63, 62))

    def test_units_mod_64_are_the_32_odd_residues(self):
        units = verifier.units_mod_64()
        self.assertEqual(len(units), 32)
        self.assertEqual(tuple(units), tuple(range(1, 64, 2)))
        for u in units:
            self.assertEqual(u % 2, 1)

    def test_tables_are_memoized_identical_objects(self):
        self.assertIs(verifier.l3_lags(), verifier.l3_lags())
        self.assertIs(verifier.units_mod_64(), verifier.units_mod_64())


class SupportValidationTests(unittest.TestCase):
    def test_normalize_sorts_and_dedupes_and_returns_tuple(self):
        self.assertEqual(verifier.normalize_support([2, 0, 1]), (0, 1, 2))

    def test_bool_is_never_a_valid_support_element(self):
        with self.assertRaises(ValueError):
            verifier.normalize_support([True, 2, 3])
        with self.assertRaises(ValueError):
            verifier.normalize_support([0, False])

    def test_out_of_range_is_rejected(self):
        with self.assertRaises(ValueError):
            verifier.normalize_support([64])
        with self.assertRaises(ValueError):
            verifier.normalize_support([-1])

    def test_duplicate_residue_is_rejected(self):
        with self.assertRaises(ValueError):
            verifier.normalize_support([1, 1])

    def test_string_bytes_dict_are_rejected(self):
        for bad in ("012", b"012", {"0": 1}):
            with self.assertRaises(ValueError):
                verifier.normalize_support(bad)

    def test_non_iterable_is_rejected(self):
        with self.assertRaises(ValueError):
            verifier.normalize_support(5)

    def test_support_to_binary_and_weight(self):
        binary = verifier.support_to_binary((0, 3))
        self.assertEqual(len(binary), 64)
        self.assertEqual(binary[0], 1)
        self.assertEqual(binary[3], 1)
        self.assertEqual(sum(binary), 2)
        self.assertEqual(verifier.weight(W9), 9)


class LowerOrderPrimitiveTests(unittest.TestCase):
    def test_periodic_autocorrelation_is_translation_invariant(self):
        base = verifier.periodic_autocorrelation(W9)
        shifted_support = tuple((s + 1) % verifier.N for s in W9)
        shifted = verifier.periodic_autocorrelation(shifted_support)
        self.assertEqual(base, shifted)
        # A2(0) == weight.
        self.assertEqual(base[0], 9)

    def test_step_one_transition_table_shape_and_row_sums(self):
        table = verifier.step_one_transition_table(W9)
        self.assertEqual(len(table), 2)
        self.assertEqual(len(table[0]), 2)
        # Row 1 sum (x_i == 1) equals weight; total equals 64.
        self.assertEqual(table[1][0] + table[1][1], 9)
        self.assertEqual(sum(table[0]) + sum(table[1]), 64)

    def test_step_one_transition_table_can_differ_between_supports(self):
        # A block of nine has many adjacent 1-1 pairs; a spread of nine has none.
        block = verifier.step_one_transition_table((0, 1, 2, 3, 4, 5, 6, 7, 8))
        spread = verifier.step_one_transition_table((0, 7, 14, 21, 28, 35, 42, 49, 56))
        self.assertNotEqual(block, spread)

    def test_direct_triple_array_length_matches_l3(self):
        arr = verifier.direct_triple_array(W9)
        self.assertEqual(len(arr), verifier.L3_ENTRY_COUNT)

    def test_triple_disagreement_of_a_support_with_itself_is_empty(self):
        self.assertEqual(verifier.triple_disagreement_indices(W9, W9), [])


class TransformAndOrbitTests(unittest.TestCase):
    def test_affine_support_requires_odd_multiplier(self):
        with self.assertRaises(ValueError):
            verifier.affine_support(W9, 2, 0)
        with self.assertRaises(ValueError):
            verifier.affine_support(W9, True, 0)

    def test_member_orbit_key_is_affine_invariant(self):
        base = verifier.member_orbit_key(W9)
        for u, v in ((3, 5), (7, 0), (63, 11)):
            self.assertEqual(base, verifier.member_orbit_key(verifier.affine_support(W9, u, v)))

    def test_member_orbit_key_is_complement_invariant(self):
        self.assertEqual(
            verifier.member_orbit_key(W9),
            verifier.member_orbit_key(verifier.complement_support(W9)),
        )

    def test_member_orbit_key_is_64_char_binary_string(self):
        key = verifier.member_orbit_key(W9)
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 64)
        self.assertTrue(all(ch in "01" for ch in key))

    def test_pair_duplicate_key_is_slot_exchange_invariant_and_sorted(self):
        pk_ab = verifier.pair_duplicate_key(verifier.FIXED_H0, verifier.FIXED_H1)
        pk_ba = verifier.pair_duplicate_key(verifier.FIXED_H1, verifier.FIXED_H0)
        self.assertEqual(pk_ab, pk_ba)
        self.assertLessEqual(pk_ab[0], pk_ab[1])
        # Distinct orbits -> strict ordering.
        self.assertLess(pk_ab[0], pk_ab[1])

    def test_orbit_related_supports_collide_on_the_pair_key(self):
        # A support and one of its affine images share a member orbit key,
        # so their pair-duplicate key has two equal slots (a collision).
        image = verifier.affine_support(W9, 3, 5)
        self.assertEqual(verifier.member_orbit_key(W9), verifier.member_orbit_key(image))
        pk = verifier.pair_duplicate_key(W9, image)
        self.assertEqual(pk[0], pk[1])


class FixedFixtureCertificateTests(unittest.TestCase):
    def setUp(self):
        self.result = verifier.verify_fixed_fixture()

    def test_manifest_is_valid_and_key_ordered(self):
        expected_keys = [
            "C", "D", "support_H0", "support_H1", "binary_H0", "binary_H1",
            "weight_H0", "weight_H1", "A2_H0", "A2_H1",
            "transition_table_H0", "transition_table_H1",
            "affine_inequivalence_certificate",
            "affine_complement_inequivalence_certificate",
            "triple_disagreement_count", "triple_disagreement_indices",
            "member_orbit_key_H0", "member_orbit_key_H1",
            "pair_duplicate_key", "validation",
        ]
        self.assertEqual(list(self.result.keys()), expected_keys)
        self.assertTrue(self.result["validation"]["valid"])
        self.assertIsNone(self.result["validation"]["failure_code"])

    def test_reconstruction_matches_committed_supports(self):
        self.assertEqual(tuple(self.result["support_H0"]), verifier.FIXED_H0)
        self.assertEqual(tuple(self.result["support_H1"]), verifier.FIXED_H1)
        self.assertEqual(self.result["C"], list(verifier.FIXED_C))
        self.assertEqual(self.result["D"], list(verifier.FIXED_D))

    def test_both_supports_have_weight_nine(self):
        self.assertEqual(self.result["weight_H0"], 9)
        self.assertEqual(self.result["weight_H1"], 9)

    def test_lower_order_invariants_are_equal(self):
        self.assertEqual(self.result["A2_H0"], self.result["A2_H1"])
        self.assertEqual(self.result["transition_table_H0"], self.result["transition_table_H1"])

    def test_affine_and_affine_complement_inequivalence(self):
        aff = self.result["affine_inequivalence_certificate"]
        self.assertFalse(aff["equivalent"])
        self.assertEqual(aff["search_space_size"], 2048)
        self.assertIsNone(aff["first_equivalence_mapping"])
        acomp = self.result["affine_complement_inequivalence_certificate"]
        self.assertFalse(acomp["equivalent"])
        self.assertEqual(acomp["search_space_size"], 4096)
        self.assertIsNone(acomp["first_equivalence_mapping"])

    def test_triple_disagreement_count_is_exactly_288(self):
        self.assertEqual(self.result["triple_disagreement_count"], 288)
        self.assertEqual(self.result["triple_disagreement_count"],
                         verifier.FIXED_TRIPLE_DISAGREEMENT_COUNT)
        indices = self.result["triple_disagreement_indices"]
        self.assertEqual(len(indices), 288)
        lag_set = set(verifier.l3_lags())
        for a, b in indices:
            self.assertIn((a, b), lag_set)

    def test_pair_key_matches_independent_recomputation(self):
        self.assertEqual(
            self.result["pair_duplicate_key"],
            list(verifier.pair_duplicate_key(verifier.FIXED_H0, verifier.FIXED_H1)),
        )

    def test_verification_is_deterministic(self):
        self.assertEqual(self.result, verifier.verify_fixed_fixture())


class EligibilityRejectionOrderTests(unittest.TestCase):
    """The eight-predicate ordered first-failure eligibility contract.

    Five of the eight rejection reasons are reachable with hand-authored
    bounded inputs and are exercised here through the real
    ``evaluate_pair_eligibility``. The remaining three cannot be reached by a
    naturally-authored weight-9 input pair under canonical mathematics:

      * TRANSITION_TABLE_MISMATCH -- once full A2 equality holds and both
        weights are 9, the step-one transition table is fully determined, so
        this branch can never fire after A2_MISMATCH passes.
      * AFFINE_COMPLEMENT_EQUIVALENT -- a genuine affine+complement
        equivalence between two weight-9 sets requires the complemented image
        (weight 55), which fails B_CARDINALITY_NOT_9 first; the plain-affine
        case is already caught by AFFINE_EQUIVALENT.
      * TRIPLE_ARRAY_EQUAL -- requires a third-order-homometric weight-9 pair
        on Z_64 that is affine+complement inequivalent; such a pair is a
        research-grade object outside the bounded S1B fixture-authoring scope.

    All three are nonetheless covered as defensive control-flow branch tests in
    ``DefensiveEligibilityBranchTests`` below, which force the real function
    down to each branch with white-box helper patches. Those tests are control-
    flow coverage only: they are not naturally discovered fixtures, not
    generated-family evidence, and not evidence that the branch is reachable
    under canonical mathematics.
    """

    def test_reason_vocabulary_is_the_exact_ordered_tuple(self):
        self.assertEqual(
            verifier.ELIGIBILITY_REJECTION_ORDER,
            (
                "A_CARDINALITY_NOT_9",
                "B_CARDINALITY_NOT_9",
                "IDENTICAL_SUPPORTS",
                "A2_MISMATCH",
                "TRANSITION_TABLE_MISMATCH",
                "AFFINE_EQUIVALENT",
                "AFFINE_COMPLEMENT_EQUIVALENT",
                "TRIPLE_ARRAY_EQUAL",
            ),
        )

    def _reject(self, a, b):
        result = verifier.evaluate_pair_eligibility(a, b)
        self.assertFalse(result["eligible"])
        return result["eligibility_rejection_reason"]

    def test_a_cardinality_not_9(self):
        self.assertEqual(self._reject((0, 1), W9), "A_CARDINALITY_NOT_9")

    def test_b_cardinality_not_9(self):
        self.assertEqual(self._reject(W9, (0, 1)), "B_CARDINALITY_NOT_9")

    def test_identical_supports(self):
        self.assertEqual(self._reject(W9, W9), "IDENTICAL_SUPPORTS")

    def test_a2_mismatch(self):
        spread = (0, 7, 14, 21, 28, 35, 42, 49, 56)
        # Different autocorrelation profile from the consecutive block.
        self.assertNotEqual(
            verifier.periodic_autocorrelation(W9),
            verifier.periodic_autocorrelation(spread),
        )
        self.assertEqual(self._reject(W9, spread), "A2_MISMATCH")

    def test_affine_equivalent_via_translation(self):
        translate = tuple((s + 1) % verifier.N for s in W9)
        # Translation preserves A2 and the transition table but is affine-equivalent.
        self.assertEqual(
            verifier.periodic_autocorrelation(W9),
            verifier.periodic_autocorrelation(translate),
        )
        self.assertEqual(self._reject(W9, translate), "AFFINE_EQUIVALENT")

    def test_unreachable_transition_branch_is_determined_by_a2_and_weight(self):
        # If full A2 is equal and both weights are 9, the transition table is
        # forced equal, so TRANSITION_TABLE_MISMATCH cannot fire post-A2.
        translate = tuple((s + 1) % verifier.N for s in W9)
        self.assertEqual(
            verifier.periodic_autocorrelation(W9),
            verifier.periodic_autocorrelation(translate),
        )
        self.assertEqual(
            verifier.step_one_transition_table(W9),
            verifier.step_one_transition_table(translate),
        )


class EligibilityEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.result = verifier.evaluate_pair_eligibility(verifier.FIXED_H0, verifier.FIXED_H1)

    def test_fixed_fixture_pair_is_eligible(self):
        self.assertTrue(self.result["eligible"])
        self.assertIsNone(self.result["eligibility_rejection_reason"])

    def test_eligible_evidence_key_order(self):
        expected_keys = [
            "eligible", "eligibility_rejection_reason", "weight_A", "weight_B",
            "A2_A", "A2_B", "transition_table_A", "transition_table_B",
            "affine_inequivalence_certificate",
            "affine_complement_inequivalence_certificate",
            "triple_disagreement_count", "triple_disagreement_indices",
            "member_orbit_key_A", "member_orbit_key_B", "pair_duplicate_key",
            "support_A", "support_B", "binary_A", "binary_B",
        ]
        self.assertEqual(list(self.result.keys()), expected_keys)

    def test_eligible_evidence_agrees_with_fixed_fixture_certificate(self):
        fixed = verifier.verify_fixed_fixture()
        self.assertEqual(self.result["triple_disagreement_count"], 288)
        self.assertEqual(self.result["triple_disagreement_count"],
                         fixed["triple_disagreement_count"])
        self.assertEqual(self.result["pair_duplicate_key"], fixed["pair_duplicate_key"])
        self.assertEqual(self.result["weight_A"], 9)
        self.assertEqual(self.result["weight_B"], 9)

    def test_eligible_evidence_is_deterministic(self):
        self.assertEqual(
            self.result,
            verifier.evaluate_pair_eligibility(verifier.FIXED_H0, verifier.FIXED_H1),
        )


# Two distinct, valid, weight-9 hand-authored supports. The cardinality and
# identical-support gates run normally against these; only strictly downstream
# helper calls are patched to force each otherwise-unreachable branch.
_WHITEBOX_A = (0, 1, 2, 3, 4, 5, 6, 7, 8)
_WHITEBOX_B = (0, 1, 2, 3, 4, 5, 6, 7, 9)
_EQUAL_A2 = tuple([9] + [0] * 63)
_EQUAL_TABLE = [[46, 9], [9, 0]]


class DefensiveEligibilityBranchTests(unittest.TestCase):
    """Defensive control-flow branch tests for the three eligibility rejection
    reasons that are not reachable by a naturally-authored weight-9 pair under
    canonical mathematics: TRANSITION_TABLE_MISMATCH, AFFINE_COMPLEMENT_EQUIVALENT,
    and TRIPLE_ARRAY_EQUAL.

    Each test calls the real ``evaluate_pair_eligibility`` with two distinct
    valid weight-9 supports (so ``normalize_support``, the cardinality gates, and
    the identical-support gate all execute normally), patches only the
    verifier-owned pure helpers needed to force the earlier gates to pass and the
    exact target branch to fire, asserts the exact rejection reason, and asserts
    that no strictly-later eligibility helper is consulted after the selected
    failure (first-failure discipline).

    These are control-flow coverage only. They are NOT naturally discovered
    fixtures, NOT generated-family evidence, and NOT evidence that any branch is
    reachable under canonical mathematics. No canonical seed scan is performed
    and no generated fixture is discovered.
    """

    def test_force_transition_table_mismatch_branch(self):
        # Force the A2 gate to pass (equal), force the step-one transition
        # tables to differ; every strictly-later helper must be untouched.
        with mock.patch.object(verifier, "periodic_autocorrelation",
                               new=lambda support: _EQUAL_A2), \
             mock.patch.object(verifier, "step_one_transition_table",
                               side_effect=[[[0, 0], [0, 0]], [[1, 1], [1, 1]]]), \
             mock.patch.object(verifier, "_affine_equivalence") as affine_mock, \
             mock.patch.object(verifier, "_affine_complement_equivalence") as ac_mock, \
             mock.patch.object(verifier, "triple_disagreement_indices") as triple_mock, \
             mock.patch.object(verifier, "member_orbit_key") as orbit_mock:
            result = verifier.evaluate_pair_eligibility(_WHITEBOX_A, _WHITEBOX_B)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["eligibility_rejection_reason"], "TRANSITION_TABLE_MISMATCH")
        affine_mock.assert_not_called()
        ac_mock.assert_not_called()
        triple_mock.assert_not_called()
        orbit_mock.assert_not_called()

    def test_force_affine_complement_equivalent_branch(self):
        # Force A2 equal, transition tables equal, plain-affine inequivalence,
        # and an affine+complement equivalence; triple and orbit must not run.
        with mock.patch.object(verifier, "periodic_autocorrelation",
                               new=lambda support: _EQUAL_A2), \
             mock.patch.object(verifier, "step_one_transition_table",
                               new=lambda support: _EQUAL_TABLE), \
             mock.patch.object(verifier, "_affine_equivalence",
                               new=lambda a, b: (False, None)), \
             mock.patch.object(verifier, "_affine_complement_equivalence",
                               new=lambda a, b: (True, [3, 5, 1])), \
             mock.patch.object(verifier, "triple_disagreement_indices") as triple_mock, \
             mock.patch.object(verifier, "member_orbit_key") as orbit_mock:
            result = verifier.evaluate_pair_eligibility(_WHITEBOX_A, _WHITEBOX_B)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["eligibility_rejection_reason"], "AFFINE_COMPLEMENT_EQUIVALENT")
        triple_mock.assert_not_called()
        orbit_mock.assert_not_called()

    def test_force_triple_array_equal_branch(self):
        # Force every earlier gate to pass and the triple disagreement set to be
        # empty; the eligible-path member_orbit_key must never be consulted.
        with mock.patch.object(verifier, "periodic_autocorrelation",
                               new=lambda support: _EQUAL_A2), \
             mock.patch.object(verifier, "step_one_transition_table",
                               new=lambda support: _EQUAL_TABLE), \
             mock.patch.object(verifier, "_affine_equivalence",
                               new=lambda a, b: (False, None)), \
             mock.patch.object(verifier, "_affine_complement_equivalence",
                               new=lambda a, b: (False, None)), \
             mock.patch.object(verifier, "triple_disagreement_indices",
                               new=lambda a, b: []), \
             mock.patch.object(verifier, "member_orbit_key") as orbit_mock:
            result = verifier.evaluate_pair_eligibility(_WHITEBOX_A, _WHITEBOX_B)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["eligibility_rejection_reason"], "TRIPLE_ARRAY_EQUAL")
        orbit_mock.assert_not_called()
