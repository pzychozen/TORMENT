"""Bounded, non-authoritative Stage S3A tests for the synthetic-validation runner.

Orchestration mechanics only, using exclusively injected manifest bytes, independently
constructed neutral N=64 sequences, reduced injected control plans, injected byte
readers, and test doubles. The real frozen manifest and real fixtures are never opened,
read, hashed, parsed, or evaluated; no authoritative CLI is run against the real
manifest; and no repository result or staging path is created (filesystem tests use
temporary directories only).

Standard library only. ``pytest`` is not imported (an external pytest collector may run
these ``unittest`` cases). No ``if __name__ == '__main__'`` block is present.
"""

import ast
import hashlib
import importlib
import inspect
import json
import math
import os
import tempfile
import unittest

import run_independent_order_sensitive_synthetic_validation_v0_1 as runner
import independent_order_sensitive_descriptor_v0_1 as descriptor

N = 64


# --------------------------------------------------------------------------- #
# Independent neutral inputs and an independent DENSE reference kernel
# --------------------------------------------------------------------------- #

def _bits(seed):
    values = []
    state = (seed * 2654435761 + 1) & 0x7FFFFFFF
    for _ in range(N):
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        values.append((state >> 17) & 1)
    if sum(values) == 0:
        values[0] = 1
    elif sum(values) == N:
        values[0] = 0
    return values


def _bits_weight(seed, target_weight):
    # Deterministic neutral sequence with an exact target weight (independent of frozen data).
    x = [0] * N
    state = (seed * 40503 + 7) & 0x7FFFFFFF
    chosen = set()
    while len(chosen) < target_weight:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        chosen.add((state >> 9) % N)
    for i in chosen:
        x[i] = 1
    return x


def _rotate(x, r):
    return [x[(i - r) % N] for i in range(N)]


def _matched_pair(seed):
    x = _bits(seed)
    return x, _rotate(x, 1)


def _make_fixture(seed, family_index, identical=False):
    a, b = _matched_pair(seed)
    if identical:
        b = list(a)
    return {"family_index": family_index, "binary_A": a, "binary_B": b}


def _dense_canonical(x):
    w = sum(x)
    z = [N * xi - w for xi in x]
    tensor = []
    for a in range(1, N):
        for b in range(1, N):
            if a == b:
                continue
            s = 0
            for i in range(N):
                s += z[i] * z[(i + a) % N] * z[(i + b) % N]
            tensor.append(s)
    denom = sum(abs(zi) ** 3 for zi in z)
    g = denom
    for t in tensor:
        if t:
            g = math.gcd(g, abs(t))
    return w, denom, tensor, (denom // g, tuple(t // g for t in tensor))


def _make_manifest(accepted=None, fixed=None, family_frozen=True):
    if accepted is None:
        accepted = [_make_fixture(i + 1, i) for i in range(8)]
    if fixed is None:
        fa, fb = _matched_pair(100)
        fixed = {"binary_A": fa, "binary_B": fb,
                 "affine_inequivalence_certificate": True,
                 "affine_complement_inequivalence_certificate": True,
                 "triple_disagreement_count": 5}
    manifest = {
        "schema": runner.EXPECTED_MANIFEST_SCHEMA,
        "family_frozen": family_frozen,
        "configuration_identity": {"configuration_sha256": runner.FREEZE_CONFIGURATION_SHA256},
        "fixed_fixture": fixed,
        "accepted_fixtures": accepted,
    }
    payload_sha = runner._payload_hash_of(manifest)
    manifest["manifest_payload_sha256"] = payload_sha
    raw = runner.canonical_bytes(manifest)
    identity = {
        "external_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_sha256": payload_sha,
        "schema": runner.EXPECTED_MANIFEST_SCHEMA,
        "configuration_sha256": runner.FREEZE_CONFIGURATION_SHA256,
    }
    return raw, identity, manifest


class FakeDescriptor:
    def raw_labeled_signature(self, x):
        return (1, tuple(x))

    def affine_only_signature(self, x):
        return (2, tuple(x))

    def affine_plus_complement_signature(self, x):
        return (3, tuple(x))


class DriftingDescriptor(FakeDescriptor):
    def __init__(self):
        self._n = 0

    def raw_labeled_signature(self, x):
        self._n += 1
        return (self._n, tuple(x))


REDUCED_PLAN = {
    "rotations": [(1, 0, 1), (1, 1, 1), (1, 7, 1)],
    "reflection": (63, 0, 1),
    "affine": [(3, 0, 1), (3, 5, 1), (5, 2, 1)],
    "self_orbit": [(1, 0, 1), (1, 0, -1), (3, 0, -1)],
}
TINY_PLAN = {"rotations": [(1, 0, 1)], "reflection": (63, 0, 1),
             "affine": [(3, 0, 1)], "self_orbit": [(1, 0, -1)]}


def _binding_and_identities():
    rb, rr, tb, tr = "1" * 40, "2" * 64, "3" * 40, "4" * 64
    binding = "\n".join([
        runner.BINDING_BEGIN,
        "authorization_schema=" + runner.BINDING_SCHEMA,
        "authorization_version=0.1",
        "runner_git_blob=" + rb,
        "runner_raw_sha256=" + rr,
        "runner_test_git_blob=" + tb,
        "runner_test_raw_sha256=" + tr,
        "configuration_sha256=" + runner.CONFIGURATION_SHA256,
        runner.BINDING_END,
    ])
    blobs = {runner.DESCRIPTOR_IDENTITY["path"]: runner.DESCRIPTOR_IDENTITY["git_blob"],
             runner.DESCRIPTOR_TEST_IDENTITY["path"]: runner.DESCRIPTOR_TEST_IDENTITY["git_blob"],
             runner.RUNNER_PATH: rb, runner.RUNNER_TEST_PATH: tb}
    raws = {runner.DESCRIPTOR_IDENTITY["path"]: runner.DESCRIPTOR_IDENTITY["raw_sha256"],
            runner.DESCRIPTOR_TEST_IDENTITY["path"]: runner.DESCRIPTOR_TEST_IDENTITY["raw_sha256"],
            runner.RUNNER_PATH: rr, runner.RUNNER_TEST_PATH: tr}
    return binding, blobs, raws


def _with_publication_paths(staging, final, action):
    original_staging = runner.STAGING_DIRECTORY
    original_final = runner.FINAL_DIRECTORY
    runner.STAGING_DIRECTORY = staging
    runner.FINAL_DIRECTORY = final
    try:
        return action()
    finally:
        runner.STAGING_DIRECTORY = original_staging
        runner.FINAL_DIRECTORY = original_final


class FakeAdapter:
    """Injected IO adapter that satisfies every authoritative precondition. Provides
    injected manifest bytes; the real manifest path is never touched."""

    def __init__(self, manifest_bytes, root=None, publish_mode=None):
        self.argv = []
        self.stdin_data = b""
        binding, blobs, raws = _binding_and_identities()
        self._binding = binding.encode("utf-8")
        self._blobs = blobs
        self._raws = raws
        self._manifest = manifest_bytes
        self._head = "e" * 40
        self._tmp = None if root is not None else tempfile.TemporaryDirectory()
        self.root = root if root is not None else self._tmp.name
        self.staging_dir = os.path.join(self.root, "staging")
        self.final_dir = os.path.join(self.root, "final")
        self.read_count = 0
        self.staging_made = 0
        self.publish_calls = 0
        self.publish_mode = publish_mode

    def python_version(self):
        return runner.REQUIRED_PYTHON

    def repo_root_ok(self):
        return True

    def branch(self):
        return "main"

    def clean_tree(self):
        return True

    def head(self):
        return self._head

    def origin_main(self):
        return self._head

    def authorization_latest_commit(self):
        return self._head

    def read_authorization_bytes(self):
        return self._binding

    def git_blob(self, path):
        return self._blobs[path]

    def raw_sha256(self, path):
        return self._raws[path]

    def static_boundaries_pass(self):
        return True

    def manifest_is_regular_file(self):
        return True

    def final_exists(self):
        return os.path.exists(self.final_dir)

    def staging_exists(self):
        return os.path.exists(self.staging_dir)

    def make_staging(self):
        os.makedirs(self.staging_dir, exist_ok=False)
        self.staging_made += 1

    def read_manifest_bytes(self):
        self.read_count += 1
        return self._manifest

    def publish_files(self, files):
        self.publish_calls += 1
        def do_publish():
            if self.publish_mode == "verify_failure":
                original = runner.sha256_hex
                calls = []

                def bad_sha(raw):
                    calls.append(raw)
                    if len(calls) % 2 == 0:
                        return "bad"
                    return original(raw)

                runner.sha256_hex = bad_sha
                try:
                    runner.publish(self.staging_dir, self.final_dir, files, staging_already_created=True)
                finally:
                    runner.sha256_hex = original
                return
            runner.publish(self.staging_dir, self.final_dir, files, staging_already_created=True)

        return _with_publication_paths(self.staging_dir, self.final_dir, do_publish)


# --------------------------------------------------------------------------- #
# Correction 1 — S3B binding route
# --------------------------------------------------------------------------- #

class BindingParserTests(unittest.TestCase):

    def _good_lines(self):
        return [
            runner.BINDING_BEGIN,
            "authorization_schema=" + runner.BINDING_SCHEMA,
            "authorization_version=0.1",
            "runner_git_blob=" + "a" * 40,
            "runner_raw_sha256=" + "b" * 64,
            "runner_test_git_blob=" + "c" * 40,
            "runner_test_raw_sha256=" + "d" * 64,
            "configuration_sha256=" + "e" * 64,
            runner.BINDING_END,
        ]

    def test_good_binding_parses(self):
        binding, failures = runner.parse_binding_block("\n".join(self._good_lines()))
        self.assertEqual(failures, [])
        self.assertEqual(list(binding.keys()), list(runner.BINDING_FIELDS))

    def test_narrative_prose_outside_binding_is_allowed(self):
        text = "\n".join(["# Execution authorization", "ordinary prose"] + self._good_lines()
                         + ["more ordinary prose", "no machine field here"])
        binding, failures = runner.parse_binding_block(text)
        self.assertEqual(failures, [])
        self.assertEqual(binding["authorization_version"], "0.1")

    def test_binding_like_content_before_block_rejected(self):
        lines = ["runner_git_blob=" + "1" * 40, "ordinary prose"] + self._good_lines()
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_binding_like_content_after_block_rejected(self):
        lines = self._good_lines() + ["runner_git_blob=" + "1" * 40]
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_missing_marker(self):
        lines = self._good_lines()[1:]   # drop begin marker
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_duplicate_marker(self):
        lines = self._good_lines() + [runner.BINDING_END]
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_missing_field(self):
        lines = self._good_lines()
        del lines[3]
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_duplicate_field_breaks_order(self):
        lines = self._good_lines()
        lines[4] = lines[3]   # repeat runner_git_blob where runner_raw_sha256 expected
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_out_of_order_field(self):
        lines = self._good_lines()
        lines[3], lines[4] = lines[4], lines[3]
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_unexpected_extra_field(self):
        lines = self._good_lines()
        lines.insert(8, "extra=deadbeef")
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_whitespace_ambiguity(self):
        lines = self._good_lines()
        lines[2] = "authorization_version = 0.1"
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_trailing_content_on_field_line(self):
        lines = self._good_lines()
        lines[2] = "authorization_version=0.1 extra"
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])
        lines = self._good_lines()
        lines[3] = "runner_git_blob=" + "a" * 40 + "=extra"
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_invalid_hex_length(self):
        lines = self._good_lines()
        lines[3] = "runner_git_blob=" + "a" * 39
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_invalid_schema(self):
        lines = self._good_lines()
        lines[1] = "authorization_schema=wrong"
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])

    def test_trailing_content_rejected(self):
        lines = self._good_lines()
        lines.insert(8, "runner_raw_sha256=" + "b" * 64)   # extra line before end
        self.assertIsNone(runner.parse_binding_block("\n".join(lines))[0])


class ConfigurationIdentityTests(unittest.TestCase):

    def test_configuration_sha256_stable(self):
        self.assertEqual(runner.configuration_sha256(), runner.CONFIGURATION_SHA256)
        self.assertTrue(runner._valid_hex(runner.CONFIGURATION_SHA256, 64))
        # Deterministic across independent calls.
        self.assertEqual(runner.configuration_sha256(), runner.configuration_sha256())

    def test_configuration_payload_contains_frozen_facts(self):
        payload = runner.configuration_identity()
        self.assertEqual(payload["descriptor_identity"], runner.DESCRIPTOR_IDENTITY)
        self.assertEqual(payload["control_plan_counts"], [64, 2048, 4096, 1, 8, 2])
        self.assertEqual(payload["s3b_authorization_path"], runner.S3B_AUTHORIZATION_PATH)


class S3bEnablementTests(unittest.TestCase):

    def test_later_docs_only_s3b_enables_unchanged_runner(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, REDUCED_PLAN, state,
                                           manifest_identity=identity)
        # The runner is no longer permanently incapable: it passed pre-contact, contacted
        # the (injected) manifest, and produced a gate result rather than a refusal.
        self.assertIn(outcome["result_kind"], runner.RESULT_KINDS)
        self.assertTrue(outcome["authority_consumed"])
        self.assertEqual(state.phase, "published")
        self.assertEqual(adapter.read_count, 2)
        self.assertEqual(adapter.publish_calls, 1)
        self.assertFalse(os.path.exists(adapter.staging_dir))
        self.assertEqual(set(os.listdir(adapter.final_dir)),
                         {runner.RESULT_FILENAME, runner.ENVELOPE_FILENAME, runner.SUMMARY_FILENAME})
        for name in os.listdir(adapter.final_dir):
            with open(os.path.join(adapter.final_dir, name), "rb") as handle:
                raw = handle.read()
            self.assertTrue(raw.endswith(b"\n"))

    def test_binding_config_mismatch_refuses(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        # Corrupt the binding's configuration_sha256.
        adapter._binding = adapter._binding.replace(
            runner.CONFIGURATION_SHA256.encode(), (b"0" * 64))
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, REDUCED_PLAN, state, manifest_identity=identity)
        self.assertIsNone(outcome["result_kind"])
        self.assertIn("FROZEN_INPUT_IDENTITY_MISMATCH", outcome["failure_codes"])
        self.assertFalse(outcome["authority_consumed"])

    def test_identity_override_via_env_cli_stdin_impossible(self):
        # main() accepts only argv/stdin and refuses any content; identities come only
        # from the binding and read-only Git, never from CLI/env/stdin.
        sig = inspect.signature(runner.main)
        self.assertEqual(list(sig.parameters), ["argv", "stdin_data"])
        self.assertEqual(runner.main(["ident=x"]), 2)
        self.assertEqual(runner.main([], b"ident=x"), 2)


# --------------------------------------------------------------------------- #
# Correction 2 — one-run threshold wired to the real read boundary
# --------------------------------------------------------------------------- #

class ThresholdTests(unittest.TestCase):

    def test_pre_contact_zero_contact(self):
        state = runner.ExecutionState()
        self.assertEqual(state.phase, "pre_contact")
        self.assertEqual(state.manifest_contact_count, 0)
        self.assertFalse(state.authority_consumed)

    def test_first_and_second_read(self):
        raw, _, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        state = runner.ExecutionState()
        runner.authoritative_manifest_read(adapter, state)
        self.assertEqual(state.manifest_contact_count, 1)
        self.assertTrue(state.authority_consumed)
        self.assertEqual(state.phase, "contacted")
        runner.authoritative_manifest_read(adapter, state)
        self.assertEqual(state.manifest_contact_count, 2)
        self.assertTrue(state.authority_consumed)

    def test_third_read_rejected(self):
        raw, _, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        state = runner.ExecutionState()
        runner.authoritative_manifest_read(adapter, state)
        runner.authoritative_manifest_read(adapter, state)
        with self.assertRaises(RuntimeError):
            runner.authoritative_manifest_read(adapter, state)

    def test_no_reset_route(self):
        state = runner.ExecutionState()
        state.mark_manifest_read()
        for forbidden in ("reset", "rerun", "resume", "retry", "reinitialize"):
            self.assertFalse(hasattr(state, forbidden))

    def test_phases_present(self):
        self.assertEqual(runner.ExecutionState.PHASES,
                         ("pre_contact", "contacted", "pass_1_complete", "pass_2_complete",
                          "published", "failed_after_contact"))

    def test_staging_before_read_and_persistence_on_failure(self):
        # An invalid manifest (default real identity) fails after contact; staging was
        # already created and authority consumed (durable refusal for later invocations).
        raw, _, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, TINY_PLAN, state)   # default real identity -> invalid
        self.assertEqual(adapter.staging_made, 1)
        self.assertTrue(outcome["authority_consumed"])
        self.assertEqual(outcome["result_kind"], "SYNTHETIC_GATE_INVALID")
        self.assertEqual(state.phase, "failed_after_contact")
        self.assertTrue(os.path.isdir(adapter.staging_dir))
        self.assertFalse(os.path.exists(adapter.final_dir))


# --------------------------------------------------------------------------- #
# Correction 3 — exact sparse kernel, witness transport, cost
# --------------------------------------------------------------------------- #

class SparseKernelTests(unittest.TestCase):

    def _compare(self, x):
        w, denom, tensor, (cden, cvec) = _dense_canonical(x)
        self.assertEqual(runner.ref_weight(x), w)
        self.assertEqual(runner.ref_autocorrelation(x), [sum(x[i] * x[(i + d) % N] for i in range(N)) for d in range(N)])
        s_tensor, s_denom = runner.sparse_tensor(x)
        self.assertEqual(s_tensor, tensor)
        self.assertEqual(s_denom, denom)
        self.assertEqual(runner.ref_canonical(x), (cden, cvec))

    def test_sparse_equals_dense_low_weight(self):
        self._compare(_bits_weight(11, 12))   # weight below 32

    def test_sparse_equals_dense_high_weight(self):
        self._compare(_bits_weight(12, 45))   # weight above 32 -> complement path

    def test_sparse_matches_frozen_descriptor(self):
        for seed, wt in ((13, 9), (14, 31), (15, 40)):
            x = _bits_weight(seed, wt)
            self.assertEqual(runner.ref_canonical(x), descriptor.raw_labeled_signature(x))


class WitnessTransportTests(unittest.TestCase):

    def test_nuisance_controls_pass(self):
        acc = runner.run_nuisance_controls(_bits(21), REDUCED_PLAN)
        self.assertEqual(acc["failure_codes"], [])
        self.assertEqual(acc["classification"], "NUISANCE_ORBIT_EQUIVALENT")

    def test_evaluate_transform_matches(self):
        x = _bits(22)
        for (u, v, s) in [(1, 0, 1), (1, 3, 1), (3, 0, 1), (63, 0, 1), (5, 9, 1), (3, 0, -1)]:
            self.assertTrue(runner.evaluate_transform(x, u, v, s)[2], (u, v, s))

    def test_no_per_transform_recanonicalization(self):
        # full_orbit_canonicalizations stays at 2 (base only) regardless of member count,
        # and no dense tensor loop is used.
        small = runner.run_nuisance_controls(_bits(23), TINY_PLAN)["cost"]
        large = runner.run_nuisance_controls(_bits(23), REDUCED_PLAN)["cost"]
        self.assertEqual(small["full_orbit_canonicalizations"], 2)
        self.assertEqual(large["full_orbit_canonicalizations"], 2)
        self.assertEqual(small["dense_tensor_loops"], 0)
        self.assertEqual(large["dense_tensor_loops"], 0)

    def test_fresh_pass_caches(self):
        # Two independent calls each build a fresh memo (no cross-call persistence).
        a = runner.run_nuisance_controls(_bits(24), REDUCED_PLAN)["cost"]
        b = runner.run_nuisance_controls(_bits(24), REDUCED_PLAN)["cost"]
        self.assertEqual(a["memoized_hits"], b["memoized_hits"])
        self.assertGreaterEqual(a["sparse_canonical_calls"], 1)

    def test_generator_set_direct_descriptor_check(self):
        self.assertEqual(runner.run_generator_set_descriptor_check(_bits(25)), [])

    def test_reference_does_not_reuse_descriptor(self):
        # AST check: the reference kernel references no ``descriptor`` name (docstrings
        # that mention the word are ignored).
        for fn in (runner.ref_canonical, runner.sparse_tensor, runner._sparse_core,
                   runner._affine_only_with_witness, runner._affine_complement_with_witness):
            names = {node.id for node in ast.walk(ast.parse(inspect.getsource(fn)))
                     if isinstance(node, ast.Name)}
            self.assertNotIn("descriptor", names)


class CostEstimateTests(unittest.TestCase):

    def test_cost_estimate_high_but_executable(self):
        est = runner.authoritative_cost_estimate()
        self.assertEqual(est["classification"], "HIGH_BUT_EXECUTABLE")
        self.assertEqual(est["dense_tensor_loops"], 0)
        self.assertEqual(est["full_orbit_canonicalizations_per_base"], 2)
        self.assertEqual(est["base_canonicalizations_per_base_per_pass"], 2)
        self.assertEqual(est["admitted_base_sequences"], 18)
        self.assertEqual(est["two_pass_multiplier"], 2)
        self.assertEqual(est["materialized_transformations_per_base"], 6209)
        self.assertEqual(est["maximum_unique_transformed_sequences_per_base"], 4096)
        self.assertEqual(est["two_pass_materialized_checks"], 223524)
        self.assertEqual(est["complete_vector_comparisons_per_base_per_pass"], 16579)
        self.assertEqual(est["complete_vector_comparisons_two_pass_total"], 596844)
        self.assertEqual(est["complete_3906_entry_vectors_computed"], "up to 147492")
        self.assertEqual(est["base_canonicalizations"], 36)
        self.assertIn("one base sequence within one pass", est["cache_scope"])

    def test_authoritative_plan_cardinalities(self):
        plan = runner.authoritative_control_plan()
        self.assertEqual(len(plan["rotations"]), 64)
        self.assertEqual(len(plan["affine"]), 2048)
        self.assertEqual(len(plan["self_orbit"]), 4096)
        for name, value in (("ROTATION_COUNT", 64), ("AFFINE_COUNT", 2048),
                            ("AFFINE_COMPLEMENT_COUNT", 4096), ("FIXED_POSITIVE_COUNT", 1),
                            ("GENERATED_POSITIVE_COUNT", 8), ("PASS_COUNT", 2)):
            self.assertEqual(getattr(runner, name), value)

    def test_comparison_count_matches_loop_obligations(self):
        plan = runner.authoritative_control_plan()
        positives = len(plan["rotations"]) + 1 + len(plan["affine"]) + len(plan["self_orbit"]) // 2
        negatives = len(plan["self_orbit"]) // 2
        self.assertEqual((positives * 3) + (negatives * 2), 16579)


# --------------------------------------------------------------------------- #
# Retained coverage: CLI, manifest validation, controls, serialization, publish
# --------------------------------------------------------------------------- #

class CliTests(unittest.TestCase):

    def test_argv_and_stdin_rejection(self):
        self.assertEqual(runner.main(["--x"]), 2)
        self.assertEqual(runner.main([], b"x"), 2)

    def test_main_refuses_invalid_stage_s3a_invocation_before_git(self):
        self.assertEqual(runner.main(["stage-s3a-not-authorized"]), 2)


class ManifestValidationTests(unittest.TestCase):

    def test_valid_injected_manifest(self):
        raw, identity, _ = _make_manifest()
        manifest, failures = runner.validate_manifest_bytes(raw, identity)
        self.assertEqual(failures, [])
        self.assertEqual(len(manifest["accepted_fixtures"]), 8)

    def test_external_hash_mismatch(self):
        raw, identity, _ = _make_manifest()
        identity["external_sha256"] = "0" * 64
        self.assertEqual(runner.validate_manifest_bytes(raw, identity)[1],
                         ["FROZEN_INPUT_IDENTITY_MISMATCH"])

    def test_unparseable(self):
        raw = b"not json\n"
        identity = {"external_sha256": hashlib.sha256(raw).hexdigest(), "payload_sha256": "0" * 64,
                    "schema": runner.EXPECTED_MANIFEST_SCHEMA,
                    "configuration_sha256": runner.FREEZE_CONFIGURATION_SHA256}
        self.assertEqual(runner.validate_manifest_bytes(raw, identity)[1], ["SERIALIZATION_FAILURE"])

    def test_family_not_frozen(self):
        raw, identity, _ = _make_manifest(family_frozen=False)
        self.assertIn("FROZEN_INPUT_IDENTITY_MISMATCH", runner.validate_manifest_bytes(raw, identity)[1])

    def test_wrong_accepted_count(self):
        raw, identity, _ = _make_manifest(accepted=[_make_fixture(i + 1, i) for i in range(7)])
        self.assertIn("FROZEN_INPUT_IDENTITY_MISMATCH", runner.validate_manifest_bytes(raw, identity)[1])

    def test_payload_hash_convention_unchanged(self):
        # Runner payload hash = SHA-256 of compact canonical UTF-8 JSON + terminal LF with
        # only manifest_payload_sha256 removed. Prove exactly that convention here.
        _raw, _identity, manifest = _make_manifest()
        payload = {k: v for k, v in manifest.items() if k != "manifest_payload_sha256"}
        expected = hashlib.sha256(
            json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8") + b"\n"
        ).hexdigest()
        self.assertEqual(runner._payload_hash_of(manifest), expected)
        self.assertEqual(manifest["manifest_payload_sha256"], expected)


class ControlTests(unittest.TestCase):

    def test_malformed_controls(self):
        base = _bits(31)
        cases = [
            (base[:63], "INPUT_LENGTH_INVALID"),
            (base + [0], "INPUT_LENGTH_INVALID"),
            ([1.0] + base[1:], "INPUT_ELEMENT_TYPE_INVALID"),
            ([True] + base[1:], "INPUT_ELEMENT_TYPE_INVALID"),
            ([-1] + base[1:], "INPUT_BINARY_DOMAIN_INVALID"),
            ([2] + base[1:], "INPUT_BINARY_DOMAIN_INVALID"),
            ([0] * N, "DEGENERATE_SEQUENCE"),
            ([1] * N, "DEGENERATE_SEQUENCE"),
        ]
        for seq, code in cases:
            self.assertEqual(runner.run_malformed_control(seq, code), [], code)

    def test_identity_control(self):
        self.assertEqual(runner.run_identity_control(_bits(32))["classification"],
                         "NO_DECLARED_DISTINCTION")
        self.assertEqual(runner.run_identity_control(_bits(32), DriftingDescriptor())["failure_codes"],
                         ["SYNTHETIC_NEGATIVE_CONTROL_FAILURE"])

    def test_raw_vector_only_descriptor_calls(self):
        seen = []

        class Spy(FakeDescriptor):
            def affine_plus_complement_signature(self, x):
                seen.append(x)
                return (3, tuple(x))

        runner.run_eight_pair_gate([_make_fixture(i + 1, i) for i in range(8)], Spy())
        self.assertTrue(seen)
        for arg in seen:
            self.assertIsInstance(arg, list)
            self.assertTrue(all(isinstance(v, int) and v in (0, 1) for v in arg))

    def test_fixed_positive_pass_and_fail(self):
        fa, fb = _matched_pair(100)
        good = {"binary_A": fa, "binary_B": fb, "affine_inequivalence_certificate": True,
                "affine_complement_inequivalence_certificate": True, "triple_disagreement_count": 5}
        self.assertEqual(runner.run_fixed_positive(good, FakeDescriptor())["classification"],
                         "DECLARED_THIRD_ORDER_DISTINCTION_DETECTED")
        a = _bits(101)
        bad = {"binary_A": a, "binary_B": list(a), "affine_inequivalence_certificate": True,
               "affine_complement_inequivalence_certificate": True, "triple_disagreement_count": 5}
        self.assertEqual(runner.run_fixed_positive(bad, FakeDescriptor())["failure_codes"],
                         ["SYNTHETIC_POSITIVE_CONTROL_FAILURE"])

    def test_eight_of_eight_pass_and_seven_of_eight_fail(self):
        accepted = [_make_fixture(i + 1, i) for i in range(8)]
        good = runner.run_eight_pair_gate(accepted, FakeDescriptor())
        self.assertEqual(good["distinctions"], 8)
        self.assertEqual(good["failure_codes"], [])
        self.assertEqual([r["family_index"] for r in good["records"]], list(range(8)))
        accepted7 = [_make_fixture(i + 1, i) for i in range(7)]
        accepted7.append(_make_fixture(99, 7, identical=True))
        bad = runner.run_eight_pair_gate(accepted7, FakeDescriptor())
        self.assertEqual(bad["distinctions"], 7)
        self.assertEqual(bad["failure_codes"], ["SYNTHETIC_POSITIVE_CONTROL_FAILURE"])

    def test_lower_order_mismatch(self):
        accepted = [_make_fixture(i + 1, i) for i in range(8)]
        bad = list(accepted[0]["binary_A"])
        bad[0] = 1 - bad[0]
        accepted[0]["binary_B"] = bad
        self.assertIn("LOWER_ORDER_CONTROL_MISMATCH",
                      runner.run_eight_pair_gate(accepted, FakeDescriptor())["failure_codes"])


class SerializationTests(unittest.TestCase):

    def test_canonical_bytes(self):
        raw = runner.canonical_bytes({"b": 2, "a": [1, 2, 3]})
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"), 1)
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b", ", raw)
        self.assertNotIn(b": ", raw)
        self.assertEqual(list(json.loads(raw.decode()).keys()), ["b", "a"])

    def test_summary_and_result_kinds(self):
        s = runner.summary_lines("SYNTHETIC_GATE_FAILED", ["SYNTHETIC_POSITIVE_CONTROL_FAILURE"])
        self.assertIn(b"result_kind=SYNTHETIC_GATE_FAILED", s)
        self.assertIn(b"failure_codes=SYNTHETIC_POSITIVE_CONTROL_FAILURE", s)
        self.assertEqual(runner.RESULT_KINDS,
                         ("SYNTHETIC_GATE_PASSED", "SYNTHETIC_GATE_FAILED", "SYNTHETIC_GATE_INVALID"))

    def test_two_pass_replay_determinism(self):
        raw, identity, _ = _make_manifest()
        m1 = runner.validate_manifest_bytes(raw, identity)[0]
        m2 = runner.validate_manifest_bytes(raw, identity)[0]
        self.assertEqual(runner.canonical_bytes(m1), runner.canonical_bytes(m2))

    def test_ordered_failures_and_vocabulary(self):
        self.assertEqual(runner.ordered_failures({"UNAUTHORIZED_EXECUTION", "INPUT_LENGTH_INVALID"}),
                         ["INPUT_LENGTH_INVALID", "UNAUTHORIZED_EXECUTION"])
        self.assertEqual(runner.FAILURE_CODES, descriptor.FAILURE_CODES)
        self.assertEqual(len(runner.FAILURE_CODES), 24)


class PublicationTests(unittest.TestCase):

    def _files(self):
        return {runner.RESULT_FILENAME: b"{}\n", runner.ENVELOPE_FILENAME: b"{}\n",
                runner.SUMMARY_FILENAME: b"x\n"}

    def test_exclusive_staging_atomic_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging, final = os.path.join(tmp, "s"), os.path.join(tmp, "f")
            os.makedirs(staging)
            _with_publication_paths(
                staging, final,
                lambda: runner.publish(staging, final, self._files(), staging_already_created=True))
            self.assertTrue(os.path.isdir(final))
            self.assertFalse(os.path.exists(staging))
            self.assertEqual(set(os.listdir(final)), set(self._files().keys()))

    def test_existing_final_and_staging_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            staging, final = os.path.join(tmp, "s"), os.path.join(tmp, "f")
            os.makedirs(staging)
            os.makedirs(final)
            with self.assertRaises(FileExistsError):
                _with_publication_paths(
                    staging, final,
                    lambda: runner.publish(staging, final, self._files(), staging_already_created=True))
        with tempfile.TemporaryDirectory() as tmp:
            staging, final = os.path.join(tmp, "s"), os.path.join(tmp, "f")
            os.makedirs(staging)
            with open(os.path.join(staging, "extra"), "wb") as handle:
                handle.write(b"x")
            with self.assertRaises(FileExistsError):
                _with_publication_paths(
                    staging, final,
                    lambda: runner.publish(staging, final, self._files(), staging_already_created=True))

    def test_run_authoritative_publishes_after_atomic_promotion(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, REDUCED_PLAN, state, manifest_identity=identity)
        self.assertEqual(outcome["state"], "published")
        self.assertEqual(adapter.publish_calls, 1)
        self.assertFalse(os.path.exists(adapter.staging_dir))
        result_path = os.path.join(adapter.final_dir, runner.RESULT_FILENAME)
        envelope_path = os.path.join(adapter.final_dir, runner.ENVELOPE_FILENAME)
        summary_path = os.path.join(adapter.final_dir, runner.SUMMARY_FILENAME)
        for path in (result_path, envelope_path, summary_path):
            self.assertTrue(os.path.isfile(path), path)
        with open(result_path, "rb") as handle:
            result = json.loads(handle.read().decode("utf-8"))
        with open(envelope_path, "rb") as handle:
            envelope = json.loads(handle.read().decode("utf-8"))
        with open(summary_path, "rb") as handle:
            summary = handle.read()
        self.assertEqual(result["result_kind"], outcome["result_kind"])
        self.assertEqual(envelope["publication_status"], "published_after_atomic_promotion")
        self.assertIn(b"publication_status=published_after_atomic_promotion", summary)

    def test_serialization_failure_leaves_failed_after_contact(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        adapter.force_artifact_serialization_failure = True
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, TINY_PLAN, state, manifest_identity=identity)
        self.assertEqual(outcome["result_kind"], "SYNTHETIC_GATE_INVALID")
        self.assertEqual(state.phase, "failed_after_contact")
        self.assertEqual(adapter.publish_calls, 0)
        self.assertTrue(os.path.isdir(adapter.staging_dir))

    def test_write_verification_failure_leaves_failed_after_contact(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw, publish_mode="verify_failure")
        state = runner.ExecutionState()
        outcome = runner.run_authoritative(adapter, TINY_PLAN, state, manifest_identity=identity)
        self.assertEqual(outcome["result_kind"], "SYNTHETIC_GATE_INVALID")
        self.assertEqual(state.phase, "failed_after_contact")
        self.assertEqual(adapter.publish_calls, 1)
        self.assertTrue(os.path.isdir(adapter.staging_dir))

    def test_atomic_rename_failure_leaves_failed_after_contact(self):
        raw, identity, _ = _make_manifest()
        adapter = FakeAdapter(raw)
        original = runner.os.replace

        def fail_replace(_src, _dst):
            raise OSError("atomic rename refused")

        runner.os.replace = fail_replace
        try:
            state = runner.ExecutionState()
            outcome = runner.run_authoritative(adapter, TINY_PLAN, state, manifest_identity=identity)
        finally:
            runner.os.replace = original
        self.assertEqual(outcome["result_kind"], "SYNTHETIC_GATE_INVALID")
        self.assertEqual(state.phase, "failed_after_contact")
        self.assertEqual(adapter.publish_calls, 1)
        self.assertTrue(os.path.isdir(adapter.staging_dir))

    def test_no_repository_paths_created(self):
        self.assertFalse(os.path.exists(runner.FINAL_DIRECTORY))
        self.assertFalse(os.path.exists(runner.STAGING_DIRECTORY))


# --------------------------------------------------------------------------- #
# Static source-boundary checker
# --------------------------------------------------------------------------- #

def _frag(*parts):
    return "".join(parts)


def _scan(source_text, role="runner"):
    return runner.source_boundary_findings(source_text, role)


class BoundaryCheckerTests(unittest.TestCase):

    def test_runner_source_passes(self):
        self.assertEqual(_scan(inspect.getsource(runner), "runner"), [])

    def test_frozen_descriptor_source_passes(self):
        self.assertEqual(_scan(inspect.getsource(descriptor), "descriptor"), [])

    def test_checker_detects_assembled_sensitive_routes(self):
        cases = [
            ("service import",
             "A='torment_'\nB='service'\nTARGET=A+B\n__import__(TARGET)"),
            ("kernel path",
             "A='memory_'\nB='kernel'\nPATH=A+B\nopen(PATH, 'rb')"),
            ("psi name",
             "A='psi'\nB='trs'\nTARGET=A+B\n__import__(TARGET)"),
            ("f3 route",
             "A='f3_'\nB='asymmetry'\nPATH=A+B\nopen(PATH, 'rb')"),
            ("audit route",
             "A='asymmetry'\nB='_audit'\nPATH=A+B\nopen(PATH, 'rb')"),
            ("historical route",
             "A='historical_'\nB='f3'\nPATH=A+B\nopen(PATH, 'rb')"),
            ("retained path",
             "A='retained_'\nB='evidence'\nPATH=A+B\nopen(PATH, 'rb')"),
            ("alternate manifest path",
             "ROOT='research/brainvision/results/'\nTAIL='alternate_manifest.json'\n"
             "PATH=ROOT+TAIL\nopen(PATH, 'rb')"),
            ("alternate result path",
             "ROOT='research/brainvision/results/'\nTAIL='alternate_result.json'\n"
             "PATH=ROOT+TAIL\nopen(PATH, 'rb')"),
            ("dynamic socket",
             "A='sock'\nB='et'\nTARGET=A+B\n__import__(TARGET)"),
            ("chained alias",
             "A='retained_'\nB='family'\nC=A+B\nD=C\nopen(D, 'rb')"),
            ("constant f-string",
             "ROOT='candidate_'\nN=478\nPATH=f'{ROOT}{N}'\nopen(PATH, 'rb')"),
            ("constant os path join",
             "import os\nROOT='research/brainvision/results'\nTAIL='alternate_manifest.json'\n"
             "PATH=os.path.join(ROOT, TAIL)\nopen(PATH, 'rb')"),
            ("constant pathlib path",
             "import pathlib\nROOT='research/brainvision/results'\nTAIL='alternate_result.json'\n"
             "PATH=pathlib.PurePath(ROOT, TAIL)\nopen(str(PATH), 'rb')"),
            ("str join module",
             "PARTS=('request', 's')\nTARGET=''.join(PARTS)\n__import__(TARGET)"),
            ("getattr attribute",
             "import os\nA='get'\nB='env'\nATTR=A+B\ngetattr(os, ATTR)('X')"),
            ("subprocess fragments",
             "import subprocess\nEXE='gi'+'t'\nVERB='sta'+'tus'\nsubprocess.run([EXE, VERB])"),
            ("mutating git fragments",
             "import subprocess\nEXE='gi'+'t'\nVERB='com'+'mit'\nsubprocess.run([EXE, VERB])"),
            ("environment name",
             "import os\nKEY='torment_'+'service'\nos.getenv(KEY)"),
            ("candidate str call",
             "ROOT='candidate_'\nN=479\nPATH=ROOT+str(N)\nopen(PATH, 'rb')"),
        ]
        self.assertEqual(len(cases), 20)
        for _label, source in cases:
            self.assertTrue(_scan(source, "runner"), source)

    def test_checker_detects_importlib_setattr_and_reassignment_bypasses(self):
        cases = [
            ("importlib assembled",
             "import importlib\nA='torment_'\nB='service'\nTARGET=A+B\n"
             "importlib.import_module(TARGET)"),
            ("importlib alias assembled",
             "import importlib as il\nLEFT='Psi'\nRIGHT='TRS'\nNAME=LEFT+RIGHT\n"
             "il.import_module(NAME)"),
            ("setattr assembled",
             "import os\nLEFT='get'\nRIGHT='env'\nATTRIBUTE=LEFT+RIGHT\n"
             "setattr(os, ATTRIBUTE, lambda *_: None)"),
            ("setattr alias assembled",
             "import os as operating_system\nLEFT='fd'\nRIGHT='open'\nATTRIBUTE=LEFT+RIGHT\n"
             "setattr(operating_system, ATTRIBUTE, lambda *_: None)"),
            ("import reassignment",
             "TARGET='torment_'+'service'\nTARGET='json'\n__import__(TARGET)"),
            ("path reassignment",
             "AUTHORIZATION_PATH=%r\nPATH='alternate_'+'manifest.json'\nPATH=AUTHORIZATION_PATH\n"
             "open(PATH, 'rb')" % runner.S3B_AUTHORIZATION_PATH),
            ("git verb reassignment",
             "import subprocess\nVERB='re'+'set'\nVERB='status'\n"
             "subprocess.run(['git', VERB], shell=False)"),
            ("chained reassignment alias",
             "AUTHORIZATION_PATH=%r\nA='alternate_'+'manifest.json'\nB=A\nA=AUTHORIZATION_PATH\n"
             "open(B, 'rb')" % runner.S3B_AUTHORIZATION_PATH),
        ]
        self.assertEqual(len(cases), 8)
        for _label, source in cases:
            self.assertTrue(_scan(source, "runner"), source)

    def test_checker_detects_low_level_os_bypasses(self):
        cases = [
            ("open alternate",
             "import os\nROOT='research/brainvision/results/'\nPATH=ROOT+'alternate_manifest.json'\n"
             "os.open(PATH, os.O_RDONLY)"),
            ("open caller path",
             "import os\ndef f(path):\n    return os.open(path, os.O_RDONLY)"),
            ("read caller fd",
             "import os\ndef f(fd):\n    return os.read(fd, 1)"),
            ("write caller fd",
             "import os\ndef f(fd):\n    return os.write(fd, b'x')"),
            ("fdopen",
             "import os\ndef f(fd):\n    return os.fdopen(fd, 'rb')"),
            ("pread",
             "import os\ndef f(fd):\n    return os.pread(fd, 1, 0)"),
            ("pwrite",
             "import os\ndef f(fd):\n    return os.pwrite(fd, b'x', 0)"),
            ("rename alternate",
             "import os\nSRC='research/brainvision/results/'+'alternate_staging'\nDST='x'\n"
             "os.rename(SRC, DST)"),
            ("replace alternate",
             "import os\nSRC='x'\nDST='research/brainvision/results/'+'alternate_final'\n"
             "os.replace(SRC, DST)"),
            ("directory fd traversal",
             "import os\ndef f(fd):\n    PATH='alternate'\n    return os.open(PATH, os.O_RDONLY, dir_fd=fd)"),
        ]
        self.assertEqual(len(cases), 10)
        for _label, source in cases:
            self.assertTrue(_scan(source, "runner"), source)

    def test_checker_rejects_unresolved_and_alternate_publication_paths(self):
        fixed = runner.RESULT_FILENAME
        cases = [
            ("publish unresolved open",
             "def publish(staging_dir, final_dir):\n"
             "    open(staging_dir / 'x.json', 'wb')\n"),
            ("publish unresolved listdir",
             "import os\n"
             "def publish(staging_dir, final_dir):\n"
             "    os.listdir(staging_dir)\n"),
            ("publish unresolved replace",
             "import os\n"
             "def publish(staging_dir, final_dir):\n"
             "    os.replace(staging_dir, final_dir)\n"),
            ("publish alternate staging",
             "from pathlib import Path\nFIXED_RESULT_FILENAME=%r\n"
             "def publish():\n"
             "    staging_dir = Path('alternate/staging')\n"
             "    open(staging_dir / FIXED_RESULT_FILENAME, 'wb')\n" % fixed),
            ("publish alternate final",
             "from pathlib import Path\nSTAGING_DIRECTORY=%r\n"
             "def publish():\n"
             "    final_dir = Path('alternate/final')\n"
             "    os.replace(STAGING_DIRECTORY, final_dir)\n" % runner.STAGING_DIRECTORY),
            ("publish traversal",
             "import os\nSTAGING_DIRECTORY=%r\nFINAL_DIRECTORY=%r\nRESULT_FILENAME=%r\n"
             "def publish():\n"
             "    os.replace(STAGING_DIRECTORY, FINAL_DIRECTORY)\n"
             "    os.listdir(STAGING_DIRECTORY)\n"
             "    if os.path.exists(FINAL_DIRECTORY):\n"
             "        raise FileExistsError('x')\n"
             "    open(os.path.join(STAGING_DIRECTORY, '..', RESULT_FILENAME), 'wb')\n"
             % (runner.STAGING_DIRECTORY, runner.FINAL_DIRECTORY, runner.RESULT_FILENAME)),
        ]
        self.assertEqual(len(cases), 6)
        for _label, source in cases:
            self.assertTrue(_scan(source, "runner"), source)

    def test_checker_allows_exact_authoritative_routes(self):
        snippets = [
            """
S3B_AUTHORIZATION_PATH = %r
def read_authorization_bytes():
    with open(S3B_AUTHORIZATION_PATH, "rb") as handle:
        return handle.read()
""" % runner.S3B_AUTHORIZATION_PATH,
            """
RUNNER_PATH = %r
DESCRIPTOR_IDENTITY = {"path": %r}
def static_boundaries_pass():
    with open(RUNNER_PATH, "rb") as handle:
        runner_source = handle.read()
    with open(DESCRIPTOR_IDENTITY["path"], "rb") as handle:
        descriptor_source = handle.read()
    return bool(runner_source and descriptor_source)
""" % (runner.RUNNER_PATH, runner.DESCRIPTOR_IDENTITY["path"]),
            """
MANIFEST_PATH = %r
def read_manifest_bytes():
    with open(MANIFEST_PATH, "rb") as handle:
        return handle.read()
""" % runner.MANIFEST_PATH,
            """
import os
FINAL_DIRECTORY = %r
STAGING_DIRECTORY = %r
RESULT_FILENAME = %r
ENVELOPE_FILENAME = %r
SUMMARY_FILENAME = %r
def final_exists():
    return os.path.exists(FINAL_DIRECTORY)
def staging_exists():
    return os.path.exists(STAGING_DIRECTORY)
def make_staging():
    os.makedirs(STAGING_DIRECTORY, exist_ok=False)
def ship_exact_artifacts(files, staging_already_created=False):
    expected = {RESULT_FILENAME, ENVELOPE_FILENAME, SUMMARY_FILENAME}
    if set(files.keys()) != expected:
        raise ValueError("publication file set mismatch")
    if os.path.exists(FINAL_DIRECTORY):
        raise FileExistsError("final directory exists")
    if not os.path.isdir(STAGING_DIRECTORY):
        raise FileNotFoundError("staging directory absent")
    if os.listdir(STAGING_DIRECTORY):
        raise FileExistsError("staging directory not empty")
    with open(os.path.join(STAGING_DIRECTORY, RESULT_FILENAME), "wb") as handle:
        handle.write(files[RESULT_FILENAME])
    with open(os.path.join(STAGING_DIRECTORY, ENVELOPE_FILENAME), "wb") as handle:
        handle.write(files[ENVELOPE_FILENAME])
    with open(os.path.join(STAGING_DIRECTORY, SUMMARY_FILENAME), "wb") as handle:
        handle.write(files[SUMMARY_FILENAME])
    with open(os.path.join(STAGING_DIRECTORY, RESULT_FILENAME), "rb") as handle:
        handle.read()
    with open(os.path.join(STAGING_DIRECTORY, ENVELOPE_FILENAME), "rb") as handle:
        handle.read()
    with open(os.path.join(STAGING_DIRECTORY, SUMMARY_FILENAME), "rb") as handle:
        handle.read()
    if set(os.listdir(STAGING_DIRECTORY)) != set(files.keys()):
        raise ValueError("staging set mismatch")
    os.replace(STAGING_DIRECTORY, FINAL_DIRECTORY)
""" % (runner.FINAL_DIRECTORY, runner.STAGING_DIRECTORY, runner.RESULT_FILENAME,
       runner.ENVELOPE_FILENAME, runner.SUMMARY_FILENAME),
            """
import subprocess
def _git():
    return subprocess.run(["git", "status", "--porcelain"], capture_output=True, check=False)
""",
            """
import hashlib
_IDENTITY_PATHS = frozenset({%r, %r, %r, %r})
def raw_sha256(path):
    if path not in _IDENTITY_PATHS:
        raise ValueError("UNAUTHORIZED_EXECUTION")
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()
""" % (runner.RUNNER_PATH, runner.RUNNER_TEST_PATH,
       runner.DESCRIPTOR_IDENTITY["path"], runner.DESCRIPTOR_TEST_IDENTITY["path"]),
        ]
        self.assertEqual(len(snippets), 6)
        for source in snippets:
            self.assertEqual(_scan(source, "runner"), [], source)

    def test_checker_marker_fragments_do_not_self_trigger(self):
        source = (
            "def _source_boundary_markers():\n"
            "    return {'forbidden_text': {'torment_' + 'service'}}\n"
        )
        self.assertEqual(_scan(source, "runner"), [])

    def test_checker_scans_executable_routes_inside_scanner_helpers(self):
        cases = [
            ("helper import",
             "def _source_boundary_markers():\n"
             "    module_name = 'torment_' + 'service'\n"
             "    return __import__(module_name)\n"),
            ("helper open",
             "def _collect_source_boundary_context():\n"
             "    path = 'alternate_' + 'manifest.json'\n"
             "    return open(path, 'rb')\n"),
            ("helper subprocess",
             "import subprocess\n"
             "def _scan_text_values():\n"
             "    command = ['git', 're' + 'set', '--hard']\n"
             "    return subprocess.run(command, shell=False)\n"),
            ("helper getattr",
             "import os\n"
             "def _chain_name():\n"
             "    name = 'get' + 'env'\n"
             "    return getattr(os, name)('IDENTITY')\n"),
        ]
        self.assertEqual(len(cases), 4)
        for _label, source in cases:
            self.assertTrue(_scan(source, "runner"), source)

    def test_runner_imports_allowlisted(self):
        roots = set()
        for node in ast.walk(ast.parse(inspect.getsource(runner))):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                roots.add((node.module or "").split(".")[0])
        self.assertTrue(roots.issubset({"ast", "json", "hashlib", "math", "os", "sys",
                                        "subprocess",
                                        "independent_order_sensitive_descriptor_v0_1"}), roots)

    def test_read_only_git_allowlist(self):
        src = inspect.getsource(runner.RealIoAdapter)
        for mutating in ("commit", "push", "reset", "checkout", "merge", "rebase", "add "):
            self.assertNotIn('"' + mutating + '"', src)
            self.assertNotIn("'" + mutating + "'", src)
        self.assertTrue(_scan("import subprocess\nsubprocess.run(['git', 'commit'])", "runner"))

    def test_import_inertness(self):
        fresh = importlib.reload(runner)
        self.assertEqual(fresh._PLAN_CACHE, {})
