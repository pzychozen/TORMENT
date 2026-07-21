"""Bounded, non-gating Stage S2 unit tests for the independent order-sensitive
descriptor v0.1.

These tests prove implementation mechanics only. They use exclusively independent,
neutral N=64 binary sequences constructed inside this file; none is drawn from the
frozen synthetic family, the fixed positive fixture, or any manifest, candidate, or
findings value. No preregistered synthetic or frozen-family outcome is exercised, so
no gate result is revealed. The suite reads no evidence file: the only source text it
inspects is the descriptor module's own source, obtained through ``inspect.getsource``.

Standard library only. ``pytest`` is not imported (an external pytest collector may
run these ``unittest`` cases). No ``if __name__ == '__main__'`` block is present.
"""

import ast
import hashlib
import importlib
import inspect
import json
import math
import unittest

import independent_order_sensitive_descriptor_v0_1 as descriptor

N = 64


# --------------------------------------------------------------------------- #
# Independent neutral inputs and independent reference calculations
# --------------------------------------------------------------------------- #

def _neutral(seed):
    """Deterministic neutral N=64 binary sequence, independent of the frozen family.

    A small self-contained integer recurrence, not derived from any fixture,
    manifest, candidate, or findings value. Forced nonconstant.
    """
    values = []
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    for _ in range(N):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        values.append((state >> 16) & 1)
    if sum(values) == 0:
        values[0] = 1
    elif sum(values) == N:
        values[0] = 0
    return values


# A couple of representative neutral sequences (kept small to bound the workload).
SEQ_A = _neutral(1)
SEQ_B = _neutral(2)
# A tiny explicit hand-built neutral sequence (two ones), clearly not a frozen pair.
SEQ_SPARSE = [0] * N
SEQ_SPARSE[3] = 1
SEQ_SPARSE[20] = 1


def _ref_centered(x):
    w = sum(x)
    return [N * xi - w for xi in x]


def _ref_tensor(x):
    z = _ref_centered(x)
    out = []
    for a in range(1, N):
        for b in range(1, N):
            if a == b:
                continue
            s = 0
            for i in range(N):
                s += z[i] * z[(i + a) % N] * z[(i + b) % N]
            out.append(s)
    return out


def _ref_a2(x):
    return [sum(x[i] * x[(i + d) % N] for i in range(N)) for d in range(N)]


def _ref_transition(x):
    counts = [[0, 0], [0, 0]]
    for i in range(N):
        counts[x[i]][x[(i + 1) % N]] += 1
    return [[counts[0][0], counts[0][1]], [counts[1][0], counts[1][1]]]


def _rotate(x, r):
    return [x[(i - r) % N] for i in range(N)]


def _reflect(x):
    return [x[(-j) % N] for j in range(N)]


def _complement(x):
    return [1 - xi for xi in x]


def _affine_relabel(x, u, v):
    uinv = pow(u, -1, N)
    return [x[(uinv * (j - v)) % N] for j in range(N)]


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #

class InputValidationTests(unittest.TestCase):

    def _code(self, x):
        payload = descriptor.descriptor_result(x)
        self.assertFalse(payload["validation"]["valid"])
        self.assertEqual(len(payload["ordered_failure_codes"]), 1)
        self.assertEqual(payload["validation"]["failure_code"],
                         payload["ordered_failure_codes"][0])
        return payload["ordered_failure_codes"][0]

    def test_length_rejection(self):
        self.assertEqual(self._code([0, 1] * 31), "INPUT_LENGTH_INVALID")   # 62
        self.assertEqual(self._code([0] * 65), "INPUT_LENGTH_INVALID")
        self.assertEqual(self._code(5), "INPUT_LENGTH_INVALID")

    def test_strict_int_rejection(self):
        bad = list(SEQ_A)
        bad[0] = 1.0
        self.assertEqual(self._code(bad), "INPUT_ELEMENT_TYPE_INVALID")
        bad2 = list(SEQ_A)
        bad2[7] = "1"
        self.assertEqual(self._code(bad2), "INPUT_ELEMENT_TYPE_INVALID")

    def test_bool_rejection(self):
        bad = list(SEQ_A)
        bad[0] = True
        self.assertEqual(self._code(bad), "INPUT_ELEMENT_TYPE_INVALID")
        self.assertEqual(self._code([False] * N), "INPUT_ELEMENT_TYPE_INVALID")

    def test_binary_domain_rejection(self):
        bad = list(SEQ_A)
        bad[2] = 2
        self.assertEqual(self._code(bad), "INPUT_BINARY_DOMAIN_INVALID")
        bad2 = list(SEQ_A)
        bad2[5] = -1
        self.assertEqual(self._code(bad2), "INPUT_BINARY_DOMAIN_INVALID")

    def test_all_zero_and_all_one_rejection(self):
        self.assertEqual(self._code([0] * N), "DEGENERATE_SEQUENCE")
        self.assertEqual(self._code([1] * N), "DEGENERATE_SEQUENCE")

    def test_first_failure_ordering(self):
        # Wrong length takes precedence over element-type problems.
        self.assertEqual(self._code([True] * 63), "INPUT_LENGTH_INVALID")
        # Element type (bool) takes precedence over binary-domain (2).
        mixed = list(SEQ_A)
        mixed[0] = True
        mixed[1] = 2
        self.assertEqual(self._code(mixed), "INPUT_ELEMENT_TYPE_INVALID")

    def test_validate_input_stage(self):
        self.assertEqual(descriptor.validate_input([0] * N),
                         ("DEGENERATE_SEQUENCE", "input_validation"))
        self.assertIsNone(descriptor.validate_input(SEQ_A))


# --------------------------------------------------------------------------- #
# Lag domain
# --------------------------------------------------------------------------- #

class LagDomainTests(unittest.TestCase):

    def test_entry_count(self):
        self.assertEqual(len(descriptor.LAG_DOMAIN), 3906)
        self.assertEqual(descriptor.ENTRY_COUNT, 3906)

    def test_exact_lexicographic_order(self):
        expected = tuple((a, b) for a in range(1, N) for b in range(1, N) if a != b)
        self.assertEqual(descriptor.LAG_DOMAIN, expected)

    def test_domain_membership(self):
        for a, b in descriptor.LAG_DOMAIN:
            self.assertTrue(1 <= a <= 63 and 1 <= b <= 63 and a != b)


# --------------------------------------------------------------------------- #
# Exact tensor, normalization, and canonical reduction
# --------------------------------------------------------------------------- #

class TensorAndReductionTests(unittest.TestCase):

    def test_centered_sum_zero(self):
        z = descriptor.centered_sequence(SEQ_A)
        self.assertEqual(sum(z), 0)
        self.assertEqual(list(z), _ref_centered(SEQ_A))

    def test_tensor_matches_independent_reference(self):
        got = list(descriptor.third_order_tensor(SEQ_A))
        self.assertEqual(len(got), 3906)
        self.assertEqual(got, _ref_tensor(SEQ_A))

    def test_denominator_positive(self):
        self.assertGreater(descriptor.normalization_denominator(SEQ_A), 0)
        self.assertGreater(descriptor.normalization_denominator(SEQ_SPARSE), 0)

    def test_integer_bound_invariant(self):
        d = descriptor.normalization_denominator(SEQ_A)
        for t in descriptor.third_order_tensor(SEQ_A):
            self.assertLessEqual(abs(t), d)

    def test_common_denominator_reduction_and_reconstruction(self):
        d = descriptor.normalization_denominator(SEQ_A)
        tensor = list(descriptor.third_order_tensor(SEQ_A))
        g = d
        for t in tensor:
            if t:
                g = math.gcd(g, abs(t))
        canon_denom, canon_nums = descriptor.canonical_reduction(SEQ_A)
        self.assertEqual(canon_denom, d // g)
        self.assertEqual(list(canon_nums), [t // g for t in tensor])
        # exact reconstruction
        self.assertEqual([n * g for n in canon_nums], tensor)
        self.assertEqual(canon_denom * g, d)
        # fully reduced
        reduced = canon_denom
        for n in canon_nums:
            if n:
                reduced = math.gcd(reduced, abs(n))
        self.assertEqual(reduced, 1)


# --------------------------------------------------------------------------- #
# Lower-order diagnostics
# --------------------------------------------------------------------------- #

class LowerOrderTests(unittest.TestCase):

    def test_weight(self):
        self.assertEqual(descriptor.weight(SEQ_A), sum(SEQ_A))

    def test_autocorrelation_all_lags(self):
        a2 = list(descriptor.second_order_autocorrelation(SEQ_A))
        self.assertEqual(len(a2), 64)
        self.assertEqual(a2, _ref_a2(SEQ_A))
        # A2(0) equals the support weight for a binary sequence.
        self.assertEqual(a2[0], sum(SEQ_A))

    def test_transition_table_includes_wraparound(self):
        table = descriptor.transition_table(SEQ_A)
        self.assertEqual(table, _ref_transition(SEQ_A))
        total = table[0][0] + table[0][1] + table[1][0] + table[1][1]
        self.assertEqual(total, 64)
        # Difference between the sparse two-ones sequence and its rotation shows
        # the wraparound transition is counted (a purely internal check).
        self.assertEqual(sum(descriptor.transition_table(SEQ_SPARSE)[0]) +
                         sum(descriptor.transition_table(SEQ_SPARSE)[1]), 64)


# --------------------------------------------------------------------------- #
# Transformation laws
# --------------------------------------------------------------------------- #

class TransformationTests(unittest.TestCase):

    def test_rotation_invariance(self):
        base = descriptor.raw_labeled_signature(SEQ_A)
        for r in (1, 7, 31):
            self.assertEqual(descriptor.raw_labeled_signature(_rotate(SEQ_A, r)), base)

    def test_reflection_lag_mapping(self):
        tensor = list(descriptor.third_order_tensor(SEQ_A))
        reflected = list(descriptor.third_order_tensor(_reflect(SEQ_A)))
        for idx, (a, b) in enumerate(descriptor.LAG_DOMAIN):
            src = descriptor.LAG_INDEX[((-a) % N, (-b) % N)]
            self.assertEqual(reflected[idx], tensor[src])

    def test_affine_lag_mapping_uses_modular_inverse(self):
        u = 5
        uinv = pow(u, -1, N)
        tensor = list(descriptor.third_order_tensor(SEQ_A))
        relabelled = list(descriptor.third_order_tensor(_affine_relabel(SEQ_A, u, 0)))
        for idx, (a, b) in enumerate(descriptor.LAG_DOMAIN):
            src = descriptor.LAG_INDEX[((uinv * a) % N, (uinv * b) % N)]
            self.assertEqual(relabelled[idx], tensor[src])

    def test_complement_antisymmetry(self):
        z = descriptor.centered_sequence(SEQ_A)
        zc = descriptor.centered_sequence(_complement(SEQ_A))
        self.assertEqual(list(zc), [-v for v in z])
        tensor = list(descriptor.third_order_tensor(SEQ_A))
        tensor_c = list(descriptor.third_order_tensor(_complement(SEQ_A)))
        self.assertEqual(tensor_c, [-t for t in tensor])
        self.assertEqual(descriptor.normalization_denominator(_complement(SEQ_A)),
                         descriptor.normalization_denominator(SEQ_A))


# --------------------------------------------------------------------------- #
# Canonical signatures and orbit collapse
# --------------------------------------------------------------------------- #

class SignatureTests(unittest.TestCase):

    def test_identity_action_equals_raw(self):
        denom, nums = descriptor.canonical_reduction(SEQ_A)
        self.assertEqual(descriptor.raw_labeled_signature(SEQ_A), (denom, nums))
        # u = 1 relabeling is the identity.
        self.assertEqual(descriptor.raw_labeled_signature(_affine_relabel(SEQ_A, 1, 0)),
                         (denom, nums))

    def test_affine_only_orbit_invariance(self):
        base = descriptor.affine_only_signature(SEQ_A)
        for (u, v) in ((5, 0), (7, 3), (63, 0)):
            self.assertEqual(descriptor.affine_only_signature(_affine_relabel(SEQ_A, u, v)),
                             base)

    def test_affine_plus_complement_invariance(self):
        base = descriptor.affine_plus_complement_signature(SEQ_A)
        self.assertEqual(
            descriptor.affine_plus_complement_signature(_complement(SEQ_A)), base)
        self.assertEqual(
            descriptor.affine_plus_complement_signature(_affine_relabel(SEQ_A, 5, 2)),
            base)

    def test_self_orbit_collapse(self):
        # Every affine image collapses to the same affine-only signature.
        base = descriptor.affine_only_signature(SEQ_B)
        for u in (3, 9, 17):
            self.assertEqual(descriptor.affine_only_signature(_affine_relabel(SEQ_B, u, 1)),
                             base)

    def test_signature_uses_exact_denominator_and_vector(self):
        denom, vec = descriptor.affine_plus_complement_signature(SEQ_A)
        self.assertIsInstance(denom, int)
        self.assertEqual(len(vec), 3906)
        self.assertTrue(all(isinstance(v, int) for v in vec))


# --------------------------------------------------------------------------- #
# Canonical payload and serialization
# --------------------------------------------------------------------------- #

TOP_LEVEL_ORDER = [
    "schema", "descriptor_id", "N", "weight", "lag_domain_id", "entry_count",
    "canonical_denominator", "raw_labeled_numerators", "affine_canonical_numerators",
    "affine_complement_canonical_numerators", "lower_order_signature",
    "transition_table", "validation", "ordered_failure_codes",
]


class SerializationTests(unittest.TestCase):

    def test_valid_payload_shape_and_constants(self):
        payload = descriptor.descriptor_result(SEQ_A)
        self.assertEqual(list(payload.keys()), TOP_LEVEL_ORDER)
        self.assertEqual(payload["schema"],
                         "torment-brainvision-independent-order-sensitive-descriptor-result-v0.1")
        self.assertEqual(payload["descriptor_id"],
                         "n64-normalized-labeled-third-order-cyclic-correlation-v0.1")
        self.assertEqual(payload["N"], 64)
        self.assertEqual(payload["lag_domain_id"],
                         "n64-distinct-position-ordered-lag-pairs-lexicographic-v0.1")
        self.assertEqual(payload["entry_count"], 3906)
        self.assertEqual(payload["weight"], sum(SEQ_A))
        self.assertEqual(len(payload["raw_labeled_numerators"]), 3906)
        self.assertEqual(len(payload["affine_canonical_numerators"]), 3906)
        self.assertEqual(len(payload["affine_complement_canonical_numerators"]), 3906)
        self.assertEqual(list(payload["lower_order_signature"].keys()),
                         ["N", "weight", "A2"])
        self.assertEqual(len(payload["lower_order_signature"]["A2"]), 64)
        self.assertEqual(list(payload["validation"].keys()),
                         ["valid", "failure_code", "failure_stage", "detail"])
        self.assertEqual(payload["validation"],
                         {"valid": True, "failure_code": None,
                          "failure_stage": None, "detail": None})
        self.assertEqual(payload["ordered_failure_codes"], [])

    def test_invalid_payload_shape(self):
        payload = descriptor.descriptor_result([0] * N)
        self.assertEqual(list(payload.keys()), TOP_LEVEL_ORDER)
        for key in ("weight", "canonical_denominator", "raw_labeled_numerators",
                    "affine_canonical_numerators", "affine_complement_canonical_numerators",
                    "lower_order_signature", "transition_table"):
            self.assertIsNone(payload[key])
        self.assertEqual(payload["validation"],
                         {"valid": False, "failure_code": "DEGENERATE_SEQUENCE",
                          "failure_stage": "input_validation", "detail": None})
        self.assertEqual(payload["ordered_failure_codes"], ["DEGENERATE_SEQUENCE"])

    def test_canonical_bytes_encoding(self):
        raw = descriptor.canonical_bytes(SEQ_A)
        self.assertIsInstance(raw, bytes)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertFalse(raw.endswith(b"\n\n"))
        self.assertEqual(raw.count(b"\n"), 1)
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))   # no BOM
        self.assertNotIn(b", ", raw)                        # compact separators
        self.assertNotIn(b": ", raw)
        # round-trips and preserves key order
        loaded = json.loads(raw.decode("utf-8"))
        self.assertEqual(list(loaded.keys()), TOP_LEVEL_ORDER)
        self.assertEqual(list(loaded["lower_order_signature"].keys()),
                         ["N", "weight", "A2"])

    def test_deterministic_replay(self):
        self.assertEqual(descriptor.descriptor_result(SEQ_A),
                         descriptor.descriptor_result(SEQ_A))
        self.assertEqual(descriptor.canonical_bytes(SEQ_A),
                         descriptor.canonical_bytes(SEQ_A))

    def test_sha256_transport_identity(self):
        raw = descriptor.canonical_bytes(SEQ_A)
        digest = descriptor.canonical_sha256(SEQ_A)
        self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))


# --------------------------------------------------------------------------- #
# Failure vocabulary
# --------------------------------------------------------------------------- #

class FailureVocabularyTests(unittest.TestCase):

    def test_full_ordered_vocabulary(self):
        expected = (
            "INPUT_LENGTH_INVALID", "INPUT_ELEMENT_TYPE_INVALID",
            "INPUT_BINARY_DOMAIN_INVALID", "DEGENERATE_SEQUENCE",
            "NORMALIZATION_INVALID", "INTEGER_BOUND_INVARIANT_FAILURE",
            "LOWER_ORDER_CONTROL_MISMATCH", "ROTATION_INVARIANCE_FAILURE",
            "REFLECTION_EQUIVARIANCE_FAILURE", "AFFINE_EQUIVARIANCE_FAILURE",
            "COMPLEMENT_ANTISYMMETRY_FAILURE", "SELF_ORBIT_CANONICALIZATION_FAILURE",
            "SYNTHETIC_NEGATIVE_CONTROL_FAILURE", "SYNTHETIC_POSITIVE_CONTROL_FAILURE",
            "FORBIDDEN_IMPORT_DETECTED", "PROHIBITED_EVIDENCE_CONTACT_DETECTED",
            "PRODUCTION_BOUNDARY_VIOLATION", "SERIALIZATION_FAILURE",
            "NONFINITE_DIAGNOSTIC", "REPLAY_MISMATCH",
            "FROZEN_CANDIDATE_ORDER_MISMATCH", "FROZEN_INPUT_IDENTITY_MISMATCH",
            "BENCHMARK_METADATA_LEAKAGE", "UNAUTHORIZED_EXECUTION",
        )
        self.assertEqual(descriptor.FAILURE_CODES, expected)


# --------------------------------------------------------------------------- #
# Static source-boundary checker and import inertness
# --------------------------------------------------------------------------- #

def _frag(*parts):
    """Assemble a sensitive marker from fragments so this test's own literals do
    not contain any complete forbidden token as a direct constant."""
    return "".join(parts)


def _scan_source(source_text):
    """Return a list of boundary findings for the given source text.

    Detects genuine executable routes: imports outside the standard-library
    allowlist, dynamic-import / eval / exec / open calls, environment or process
    or network attribute access, and specific production / historical / evidence
    path or module fragments appearing as string constants. Marker vocabulary is
    assembled from fragments to avoid self-triggering on this checker's own text.
    """
    tree = ast.parse(source_text)
    allowed_imports = {"json", "hashlib", "math"}
    forbidden_import_roots = {
        _frag("o", "s"), _frag("sub", "process"), _frag("sock", "et"),
        _frag("import", "lib"), _frag("path", "lib"), _frag("request", "s"),
        _frag("url", "lib"), _frag("ht", "tp"), _frag("cty", "pes"),
        _frag("shu", "til"), _frag("sy", "s"),
    }
    forbidden_call_names = {
        _frag("op", "en"), "__" + "import" + "__", _frag("ev", "al"),
        _frag("ex", "ec"), _frag("comp", "ile"),
    }
    forbidden_attr_names = {
        _frag("envi", "ron"), _frag("get", "env"), _frag("sys", "tem"),
        _frag("pop", "en"), _frag("Pop", "en"), _frag("conn", "ect"),
        _frag("url", "open"),
    }
    forbidden_text = {
        _frag("torment_", "service"), _frag("memory_", "kernel"),
        _frag("trioctamemory", "kernel"), _frag("psi", "_trs"),
        _frag("psi", "trs"), _frag("f3_", "evaluator"), _frag("f3_", "asymmetry"),
        _frag("asymmetry_", "audit"),
        _frag("results/independent_order_sensitive_synthetic_fixture_", "freeze"),
    }
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in forbidden_import_roots or root not in allowed_imports:
                    findings.append(("import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level and node.level > 0:
                findings.append(("relative_import", node.module or ""))
            elif root in forbidden_import_roots or root not in allowed_imports:
                findings.append(("import_from", node.module))
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in forbidden_call_names:
                findings.append(("call", func.id))
            if isinstance(func, ast.Attribute) and func.attr in forbidden_attr_names:
                findings.append(("attr_call", func.attr))
        elif isinstance(node, ast.Attribute):
            if node.attr in forbidden_attr_names:
                findings.append(("attr", node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            low = node.value.lower()
            for marker in forbidden_text:
                if marker in low:
                    findings.append(("text", marker))
    return findings


class BoundaryCheckerTests(unittest.TestCase):

    def test_descriptor_source_passes_boundary_scan(self):
        source = inspect.getsource(descriptor)
        self.assertEqual(_scan_source(source), [])

    def test_descriptor_imports_are_standard_library_allowlist_only(self):
        tree = ast.parse(inspect.getsource(descriptor))
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                roots.add((node.module or "").split(".")[0])
        self.assertTrue(roots.issubset({"json", "hashlib", "math"}), roots)

    def test_checker_detects_genuine_violations(self):
        bad_import = "import " + _frag("o", "s") + "\n"
        self.assertTrue(_scan_source(bad_import))
        bad_open = _frag("op", "en") + "('x')\n"
        self.assertTrue(_scan_source(bad_open))
        bad_dynamic = "__" + "import" + "__('x')\n"
        self.assertTrue(_scan_source(bad_dynamic))
        bad_text = "PATH = " + repr(_frag("torment_", "service") + "/kernel/x")
        self.assertTrue(_scan_source(bad_text))

    def test_descriptor_has_no_main_block(self):
        source = inspect.getsource(descriptor)
        self.assertNotIn("__main__", source)

    def test_import_inertness(self):
        # A freshly (re)executed module performs no eager affine build and no I/O.
        fresh = importlib.reload(descriptor)
        self.assertEqual(fresh._AFFINE_PERMUTATIONS, {})
        # Using it then lazily builds the cache without touching import time.
        fresh.affine_only_signature(SEQ_A)
        self.assertIn("perms", fresh._AFFINE_PERMUTATIONS)
