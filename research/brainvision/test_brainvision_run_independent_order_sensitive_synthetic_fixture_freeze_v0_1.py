"""Bounded tests for the authoritative synthetic-fixture freeze runner (v0.1).

All Git access, project-module imports, file reads, seed streams, and publication
faults are injected or mocked. No real Git command is run, no real complete
canonical iterator is driven, the actual first eight fixtures are never
discovered, no repository-tree output is written (temporary directories only),
and the runner entry point is never invoked. Positive ACCEPTED_EIGHT orchestration
uses hand-authored distinct pair identities together with mocked manifest / bundle
/ finalization library boundaries; canonical-negative and process-failure paths
use the real freeze library over a bounded zero-record seed-exhaustion structure.
``unittest`` and ``unittest.mock`` only; ``pytest`` is not imported and there is
no executable ``__main__`` block.
"""

import ast
import hashlib
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import independent_order_sensitive_synthetic_fixture_verifier_v0_1 as verifier
import independent_order_sensitive_synthetic_fixture_generator_v0_1 as generator
import independent_order_sensitive_synthetic_fixture_freeze_v0_1 as freeze
import run_independent_order_sensitive_synthetic_fixture_freeze_v0_1 as run


CURRENT_PYTHON = "%d.%d.%d" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
REAL_CONFIG_SHA = freeze.canonical_configuration_sha256(run.build_configuration_payload())


def _sha1_hex(text):
    return hashlib.sha1(("blob:" + text).encode("utf-8")).hexdigest()


def _sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def _s1b_paths():
    return [source["source_path"] for source in run.S1B_SOURCE_IDENTITIES]


def _distinct_key(i):
    body = format(i, "b").zfill(63)
    return ("0" + body, "1" + body)   # 64-char 0/1 strings; key_0 < key_1; distinct per i


_DISTINCT_KEYS = [_distinct_key(i) for i in range(8)]


def _distinct_wrapper(i):
    return {"family_index": i, "seed_order_position": i,
            "fixture_record": {"pair_duplicate_key": _distinct_key(i), "seed_tuple": (1, 2, 1, 3 + i)}}


def _accepted_eight_wrappers():
    return [_distinct_wrapper(i) for i in range(8)]


def _diag(terminal_status, positions):
    return {
        "total_seeds_visited": 480,
        "eligibility_rejection_counts": freeze._empty_rejection_counts(),
        "eligible_duplicate_count": 0,
        "accepted_seed_order_positions": list(positions),
        "terminal_seed_tuple": [62, 63, 62, 63],
        "terminal_status": terminal_status,
    }


def _scan_accepted_eight():
    def scan(seed_iterable, initial_seen_pair_keys=None):
        return {"valid": True, "failure_code": None, "failure_stage": None,
                "accepted_records": _accepted_eight_wrappers(),
                "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))}
    return scan


def _scan_seed_exhausted_empty():
    def scan(seed_iterable, initial_seen_pair_keys=None):
        return {"valid": True, "failure_code": None, "failure_stage": None,
                "accepted_records": [],
                "search_diagnostics": _diag("SEED_SPACE_EXHAUSTED", [])}
    return scan


def _scan_returning(payload):
    def scan(seed_iterable, initial_seen_pair_keys=None):
        import copy
        return copy.deepcopy(payload) if isinstance(payload, dict) else payload
    return scan


def _scan_raising(exc):
    """A scan that raises an unexpected (non-authorized) exception."""
    def scan(seed_iterable, initial_seen_pair_keys=None):
        raise exc
    return scan


def _scan_first_ok_then_fail():
    """Pass 1 seed-exhausts (a complete canonical failure); pass 2 fails."""
    calls = {"i": 0}

    def scan(seed_iterable, initial_seen_pair_keys=None):
        calls["i"] += 1
        if calls["i"] == 1:
            return {"valid": True, "failure_code": None, "failure_stage": None,
                    "accepted_records": [],
                    "search_diagnostics": _diag("SEED_SPACE_EXHAUSTED", [])}
        return {"valid": False, "failure_code": "SEED_ENUMERATION_FAILURE",
                "failure_stage": "seed_validation", "accepted_records": []}
    return scan


# Canned freeze structures for the mocked ACCEPTED_EIGHT positive path.
def _canned_manifest():
    return {"accepted_fixtures": [{"pair_duplicate_key": k} for k in _DISTINCT_KEYS],
            "manifest_payload_sha256": "1" * 64,
            "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))}


def _canned_bundle():
    return {"canonical_payload_bytes": b"PAYLOAD", "manifest_payload_sha256": "1" * 64,
            "canonical_manifest_bytes": b"CANDIDATE-MANIFEST\n", "external_manifest_sha256": "2" * 64,
            "accepted_fixture_order": list(_DISTINCT_KEYS),
            "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))}


def _canned_finalized():
    return {"final_manifest_object": {"family_frozen": True, "manifest_payload_sha256": "3" * 64},
            "canonical_payload_bytes": b"PAYLOAD", "manifest_payload_sha256": "3" * 64,
            "canonical_manifest_bytes": b"FINAL-MANIFEST\n", "external_manifest_sha256": "4" * 64}


def _patch_positive_freeze(test, manifest_effect=None):
    """Mock only the manifest and finalization boundaries for a positive
    ACCEPTED_EIGHT run; the real build_candidate_pass_bundle and
    compare_candidate_passes operate over the canned manifest (so an injected
    per-pass manifest difference produces a genuine replay mismatch). Each mocked
    call returns a fresh object (no pass-1 object leak)."""
    manifest_effect = manifest_effect or (lambda *a, **k: _canned_manifest())
    for name, effect in (
        ("build_candidate_manifest", manifest_effect),
        ("finalize_authoritative_manifest", lambda *a, **k: _canned_finalized()),
    ):
        p = mock.patch.object(freeze, name, side_effect=effect)
        p.start(); test.addCleanup(p.stop)


class FakeGit:
    def __init__(self, head):
        self.head = head
        self.origin_main = head
        self.branch = "main"
        self.status = ""
        self.path_present = True
        self.path_commit = head
        self.toplevel = ""
        self._blobs = {}
        self._committed = {}

    def set_blob(self, path, blob):
        self._blobs[path] = blob

    def set_committed(self, path, data):
        self._committed[path] = data

    def resolve_head(self):
        return self.head

    def resolve_origin_main(self):
        return self.origin_main

    def current_branch(self):
        return self.branch

    def status_porcelain(self):
        return self.status

    def show_toplevel(self):
        return self.toplevel

    def path_exists_at_head(self, path):
        return self.path_present

    def latest_commit_for_path(self, path):
        return self.path_commit

    def blob_id_at_head(self, path):
        return self._blobs.get(path, "")

    def committed_bytes(self, path):
        if path not in self._committed:
            raise run.PreContactRefusal("UNAUTHORIZED_EXECUTION", "no committed bytes")
        return self._committed[path]


def _binding_text(runner_blob, runner_raw, rt_blob, rt_raw, config_sha, fields=None):
    if fields is None:
        fields = [
            ("authorization_schema", run.AUTHORIZATION_SCHEMA),
            ("authorization_version", run.AUTHORIZATION_VERSION),
            ("runner_git_blob", runner_blob),
            ("runner_raw_sha256", runner_raw),
            ("runner_test_git_blob", rt_blob),
            ("runner_test_raw_sha256", rt_raw),
            ("configuration_sha256", config_sha),
        ]
    body = "\n".join("%s=%s" % (k, v) for k, v in fields)
    return ("# execution authorization\n%s\n%s\n%s\n# end\n"
            % (run.BINDING_BEGIN_MARKER, body, run.BINDING_END_MARKER)).encode("utf-8")


class _World:
    def __init__(self, test, *, renamer=None):
        head = "a" * 40
        self.repo_root = tempfile.mkdtemp()
        test.addCleanup(self._cleanup)

        self.s1b_bytes = b"x = 1\n"
        s1b_identities = tuple(
            {"artifact_role": s["artifact_role"], "source_path": s["source_path"],
             "git_blob": _sha1_hex(s["source_path"]), "raw_sha256": _sha256_hex(self.s1b_bytes)}
            for s in run.S1B_SOURCE_IDENTITIES
        )
        p1 = mock.patch.object(run, "S1B_SOURCE_IDENTITIES", new=s1b_identities)
        p1.start(); test.addCleanup(p1.stop)
        p2 = mock.patch.object(run, "PYTHON_VERSION", new=CURRENT_PYTHON)
        p2.start(); test.addCleanup(p2.stop)

        self.runner_bytes = b"# runner\n"
        self.runner_test_bytes = b"# runner test\n"
        self._file_bytes = {p: self.s1b_bytes for p in _s1b_paths()}
        self._file_bytes[run.RUNNER_SOURCE_PATH] = self.runner_bytes
        self._file_bytes[run.RUNNER_TEST_SOURCE_PATH] = self.runner_test_bytes

        self.runner_blob = _sha1_hex(run.RUNNER_SOURCE_PATH)
        self.runner_raw = _sha256_hex(self.runner_bytes)
        self.rt_blob = _sha1_hex(run.RUNNER_TEST_SOURCE_PATH)
        self.rt_raw = _sha256_hex(self.runner_test_bytes)
        self.binding_bytes = _binding_text(self.runner_blob, self.runner_raw,
                                           self.rt_blob, self.rt_raw, REAL_CONFIG_SHA)

        self.git = FakeGit(head)
        self.git.toplevel = self.repo_root
        for p in _s1b_paths():
            self.git.set_blob(p, _sha1_hex(p))
        self.git.set_blob(run.RUNNER_SOURCE_PATH, self.runner_blob)
        self.git.set_blob(run.RUNNER_TEST_SOURCE_PATH, self.rt_blob)
        self.git.set_blob(run.AUTHORIZATION_DOCUMENT_PATH, _sha1_hex(run.AUTHORIZATION_DOCUMENT_PATH))
        self.git.set_committed(run.AUTHORIZATION_DOCUMENT_PATH, self.binding_bytes)

        self.modules = types.SimpleNamespace(verifier=verifier, generator=generator, freeze=freeze)
        self.runner = run.FreezeRunner(
            repo_root=self.repo_root,
            argv=[run.RUNNER_SOURCE_PATH],
            stdin_bytes=b"",
            git=self.git,
            importer=lambda: self.modules,
            file_reader=lambda path: self._file_bytes[path],
            renamer=renamer,
            runner_file=os.path.join(self.repo_root, *run.RUNNER_SOURCE_PATH.split("/")),
        )

    def install_scan(self, scan, verifier_module=verifier):
        gen = types.SimpleNamespace(
            scan_seed_stream=scan,
            iter_canonical_seed_tuples=lambda: iter(()),
            fixed_fixture_pair_key=generator.fixed_fixture_pair_key,
        )
        self.modules = types.SimpleNamespace(verifier=verifier_module, generator=gen, freeze=freeze)
        self.runner._modules = self.modules

    def context(self):
        return {
            "execution_head": self.git.head,
            "authorization_document_git_blob": _sha1_hex(run.AUTHORIZATION_DOCUMENT_PATH),
            "binding": run.parse_authorization_binding(self.binding_bytes),
            "configuration_identity": freeze.build_configuration_identity(run.build_configuration_payload()),
            "source_identity": self.runner._build_manifest_source_identity(self.git.head),
        }

    def _cleanup(self):
        import shutil
        shutil.rmtree(self.repo_root, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Import boundary, CLI, stdin
# --------------------------------------------------------------------------- #

class ImportBoundaryTests(unittest.TestCase):
    def test_no_project_import_at_module_top_level(self):
        with open(run.__file__, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        project = {
            "independent_order_sensitive_synthetic_fixture_verifier_v0_1",
            "independent_order_sensitive_synthetic_fixture_generator_v0_1",
            "independent_order_sensitive_synthetic_fixture_freeze_v0_1",
        }
        top_imports = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top_imports += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_imports.append(node.module)
        self.assertTrue(project.isdisjoint(set(top_imports)))


class CliTests(unittest.TestCase):
    def _runner(self, argv, stdin=b""):
        return run.FreezeRunner(repo_root="/x", argv=argv, stdin_bytes=stdin,
                                git=FakeGit("a" * 40), runner_file="/x/" + run.RUNNER_SOURCE_PATH)

    def test_exact_shape_accepted(self):
        self._runner([run.RUNNER_SOURCE_PATH]).validate_cli()

    def test_empty_argv_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner([]).validate_cli)

    def test_extra_argument_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner([run.RUNNER_SOURCE_PATH, "--go"]).validate_cli)

    def test_wrong_argv0_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner(["other.py"]).validate_cli)

    def test_absolute_argv0_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner(["/repo/" + run.RUNNER_SOURCE_PATH]).validate_cli)

    def test_suffix_only_argv0_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner(["x/" + run.RUNNER_SOURCE_PATH]).validate_cli)

    def test_stdin_input_rejected(self):
        self.assertRaises(run.PreContactRefusal, self._runner([run.RUNNER_SOURCE_PATH], b"data").validate_cli)


class StdinWiringTests(unittest.TestCase):
    def test_tty_stdin_is_empty(self):
        stream = types.SimpleNamespace(isatty=lambda: True,
                                       buffer=types.SimpleNamespace(read=lambda: b"IGNORED"))
        self.assertEqual(run.collect_stdin(stream), b"")

    def test_redirected_empty_stdin_is_empty(self):
        stream = types.SimpleNamespace(isatty=lambda: False,
                                       buffer=types.SimpleNamespace(read=lambda: b""))
        self.assertEqual(run.collect_stdin(stream), b"")

    def test_redirected_nonempty_stdin_returned(self):
        stream = types.SimpleNamespace(isatty=lambda: False,
                                       buffer=types.SimpleNamespace(read=lambda: b"payload"))
        self.assertEqual(run.collect_stdin(stream), b"payload")

    def test_none_stdin_is_empty(self):
        self.assertEqual(run.collect_stdin(None), b"")

    def test_nonempty_stdin_refused_before_import(self):
        stream = types.SimpleNamespace(isatty=lambda: False,
                                       buffer=types.SimpleNamespace(read=lambda: b"x"))
        runner = run.FreezeRunner(repo_root="/x", argv=[run.RUNNER_SOURCE_PATH],
                                  stdin_bytes=run.collect_stdin(stream), git=FakeGit("a" * 40),
                                  runner_file="/x/" + run.RUNNER_SOURCE_PATH)
        self.assertRaises(run.PreContactRefusal, runner.validate_cli)
        self.assertFalse(runner.project_modules_imported)


# --------------------------------------------------------------------------- #
# Repository root + non-circular HEAD
# --------------------------------------------------------------------------- #

class RepositoryRootTests(unittest.TestCase):
    def test_happy(self):
        _World(self).runner.verify_repository_root()

    def test_wrong_top_level(self):
        w = _World(self); w.git.toplevel = tempfile.mkdtemp()
        self.assertRaises(run.PreContactRefusal, w.runner.verify_repository_root)

    def test_invocation_from_subdirectory_refuses(self):
        # cwd (repo_root) is a subdirectory; git resolves the real top level above it.
        w = _World(self)
        subdir = os.path.join(w.repo_root, "research")
        os.makedirs(subdir, exist_ok=True)
        w.runner._repo_root = subdir
        w.runner._runner_file = os.path.join(subdir, *run.RUNNER_SOURCE_PATH.split("/"))
        # git top level remains the real repo root (w.repo_root), != subdir
        with self.assertRaises(run.PreContactRefusal) as ctx:
            w.runner.verify_repository_root()
        self.assertEqual(ctx.exception.failure_code, "UNAUTHORIZED_EXECUTION")

    def test_runner_not_at_authoritative_path(self):
        w = _World(self); w.runner._runner_file = os.path.join(w.repo_root, "x", "run.py")
        self.assertRaises(run.PreContactRefusal, w.runner.verify_repository_root)

    def test_unresolved_top_level(self):
        w = _World(self); w.git.toplevel = ""
        self.assertRaises(run.PreContactRefusal, w.runner.verify_repository_root)


class ExecutionHeadTests(unittest.TestCase):
    def test_happy(self):
        w = _World(self)
        head, blob = w.runner.resolve_execution_head()
        self.assertEqual(head, w.git.head)
        self.assertEqual(blob, _sha1_hex(run.AUTHORIZATION_DOCUMENT_PATH))

    def test_head_not_origin(self):
        w = _World(self); w.git.origin_main = "b" * 40
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_wrong_branch(self):
        w = _World(self); w.git.branch = "feature"
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_dirty_tree(self):
        w = _World(self); w.git.status = " M x"
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_document_absent(self):
        w = _World(self); w.git.path_present = False
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_path_commit_not_head(self):
        w = _World(self); w.git.path_commit = "c" * 40
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_missing_path_history(self):
        w = _World(self); w.git.path_commit = ""
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)

    def test_malformed_document_blob(self):
        w = _World(self); w.git.set_blob(run.AUTHORIZATION_DOCUMENT_PATH, "ZZZ")
        with self.assertRaises(run.PreContactRefusal) as ctx:
            w.runner.resolve_execution_head()
        self.assertEqual(ctx.exception.failure_code, "HASH_IDENTITY_FAILURE")

    def test_later_unrelated_head(self):
        w = _World(self); w.git.head = "d" * 40; w.git.origin_main = "d" * 40; w.git.path_commit = "a" * 40
        self.assertRaises(run.PreContactRefusal, w.runner.resolve_execution_head)


# --------------------------------------------------------------------------- #
# Binding
# --------------------------------------------------------------------------- #

class BindingTests(unittest.TestCase):
    def _binding(self, **kw):
        base = dict(runner_blob=_sha1_hex("r"), runner_raw=_sha256_hex(b"r"),
                    rt_blob=_sha1_hex("t"), rt_raw=_sha256_hex(b"t"), config_sha="e" * 64)
        base.update(kw)
        return _binding_text(base["runner_blob"], base["runner_raw"], base["rt_blob"],
                             base["rt_raw"], base["config_sha"])

    def test_valid_seven_fields(self):
        fields = run.parse_authorization_binding(self._binding())
        self.assertEqual(tuple(fields.keys()), run.BINDING_FIELD_ORDER)
        self.assertEqual(len(fields), 7)

    def test_two_self_referential_fields_absent(self):
        self.assertNotIn("repository_execution_head", run.BINDING_FIELD_ORDER)
        self.assertNotIn("authorization_document_git_blob", run.BINDING_FIELD_ORDER)

    def test_uppercase_hex(self):
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding, self._binding(runner_blob="A" * 40))

    def test_wrong_length_hex(self):
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding, self._binding(config_sha="e" * 63))

    def test_missing_field(self):
        f = [("authorization_schema", run.AUTHORIZATION_SCHEMA), ("authorization_version", "0.1"),
             ("runner_git_blob", _sha1_hex("r")), ("runner_raw_sha256", _sha256_hex(b"r")),
             ("runner_test_git_blob", _sha1_hex("t")), ("runner_test_raw_sha256", _sha256_hex(b"t"))]
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding,
                          _binding_text("", "", "", "", "", fields=f))

    def test_extra_field(self):
        f = [("authorization_schema", run.AUTHORIZATION_SCHEMA), ("authorization_version", "0.1"),
             ("runner_git_blob", _sha1_hex("r")), ("runner_raw_sha256", _sha256_hex(b"r")),
             ("runner_test_git_blob", _sha1_hex("t")), ("runner_test_raw_sha256", _sha256_hex(b"t")),
             ("configuration_sha256", "e" * 64), ("extra", "1")]
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding,
                          _binding_text("", "", "", "", "", fields=f))

    def test_duplicate_field(self):
        f = [("authorization_schema", run.AUTHORIZATION_SCHEMA), ("authorization_version", "0.1"),
             ("runner_git_blob", _sha1_hex("r")), ("runner_git_blob", _sha1_hex("r")),
             ("runner_raw_sha256", _sha256_hex(b"r")), ("runner_test_git_blob", _sha1_hex("t")),
             ("runner_test_raw_sha256", _sha256_hex(b"t"))]
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding,
                          _binding_text("", "", "", "", "", fields=f))

    def test_wrong_order(self):
        f = [("authorization_version", "0.1"), ("authorization_schema", run.AUTHORIZATION_SCHEMA),
             ("runner_git_blob", _sha1_hex("r")), ("runner_raw_sha256", _sha256_hex(b"r")),
             ("runner_test_git_blob", _sha1_hex("t")), ("runner_test_raw_sha256", _sha256_hex(b"t")),
             ("configuration_sha256", "e" * 64)]
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding,
                          _binding_text("", "", "", "", "", fields=f))

    def test_missing_marker(self):
        self.assertRaises(run.PreContactRefusal, run.parse_authorization_binding,
                          self._binding().replace(run.BINDING_BEGIN_MARKER.encode(), b"X"))


# --------------------------------------------------------------------------- #
# Pre-contact
# --------------------------------------------------------------------------- #

class PreContactTests(unittest.TestCase):
    def test_happy(self):
        w = _World(self)
        context = w.runner.pre_contact()
        self.assertTrue(w.runner.project_modules_imported)
        self.assertEqual(set(context["source_identity"].keys()), set(freeze.SOURCE_IDENTITY_KEYS))

    def _refuse_no_import(self, w, code=None):
        with self.assertRaises(run.PreContactRefusal) as ctx:
            w.runner.pre_contact()
        if code is not None:
            self.assertEqual(ctx.exception.failure_code, code)
        self.assertFalse(w.runner.project_modules_imported)

    def test_s1b_blob_mismatch(self):
        w = _World(self); w.git.set_blob(_s1b_paths()[0], "f" * 40)
        self._refuse_no_import(w, "HASH_IDENTITY_FAILURE")

    def test_s1b_raw_mismatch(self):
        w = _World(self); w._file_bytes[_s1b_paths()[1]] = b"diff\n"
        self._refuse_no_import(w, "HASH_IDENTITY_FAILURE")

    def test_runner_identity_mismatch(self):
        w = _World(self); w._file_bytes[run.RUNNER_SOURCE_PATH] = b"tampered\n"
        self._refuse_no_import(w, "HASH_IDENTITY_FAILURE")

    def test_dirty_tree(self):
        w = _World(self); w.git.status = " M x"
        self._refuse_no_import(w)

    def test_wrong_repo_root(self):
        w = _World(self); w.git.toplevel = tempfile.mkdtemp()
        self._refuse_no_import(w, "UNAUTHORIZED_EXECUTION")

    def test_staging_exists(self):
        w = _World(self)
        os.makedirs(os.path.join(w.repo_root, run.RESULTS_DIR, run.STAGING_DIR_NAME))
        self._refuse_no_import(w)

    def test_output_exists(self):
        w = _World(self)
        os.makedirs(os.path.join(w.repo_root, run.RESULTS_DIR, run.FINAL_DIR_NAME))
        self._refuse_no_import(w)

    def test_python_mismatch(self):
        w = _World(self)
        with mock.patch.object(run, "PYTHON_VERSION", "9.9.9"):
            with self.assertRaises(run.PreContactRefusal) as ctx:
                w.runner.verify_python_version()
        self.assertEqual(ctx.exception.failure_code, "HASH_IDENTITY_FAILURE")

    def test_config_mismatch(self):
        w = _World(self)
        w.git.set_committed(run.AUTHORIZATION_DOCUMENT_PATH,
                            _binding_text(w.runner_blob, w.runner_raw, w.rt_blob, w.rt_raw, "0" * 64))
        with self.assertRaises(run.PreContactRefusal) as ctx:
            w.runner.pre_contact()
        self.assertEqual(ctx.exception.failure_code, "HASH_IDENTITY_FAILURE")

    def test_source_boundary_rejection(self):
        w = _World(self)
        fault = freeze.SyntheticFixtureProcessFailure("FORBIDDEN_IMPORT_DETECTED", "source_boundary", "x")
        with mock.patch.object(freeze, "validate_source_boundary", side_effect=fault):
            with self.assertRaises(run.PreContactRefusal) as ctx:
                w.runner.pre_contact()
        self.assertEqual(ctx.exception.failure_code, "FORBIDDEN_IMPORT_DETECTED")
        self.assertEqual(ctx.exception.failure_stage, "pre_contact")

    def test_unexpected_git_exception_normalized(self):
        w = _World(self)
        w.git.resolve_head = lambda: (_ for _ in ()).throw(RuntimeError("git broke"))
        with self.assertRaises(run.PreContactRefusal) as ctx:
            w.runner.pre_contact()
        self.assertEqual(ctx.exception.failure_code, "UNAUTHORIZED_EXECUTION")
        self.assertEqual(ctx.exception.failure_stage, "pre_contact")


# --------------------------------------------------------------------------- #
# Scan invariants (duplicate / fixed-key / cardinality / shape)
# --------------------------------------------------------------------------- #

class ScanInvariantTests(unittest.TestCase):
    def _pass(self, w):
        return w.runner.two_pass_operation(w.context())["pass_1"]

    def _install(self, w, payload):
        w.install_scan(_scan_returning(payload))

    def test_accepted_eight_valid(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "POSITIVE")

    def test_duplicate_pair_key_rejected(self):
        w = _World(self)
        wrappers = _accepted_eight_wrappers()
        wrappers[1]["fixture_record"]["pair_duplicate_key"] = _distinct_key(0)   # duplicate of index 0
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": wrappers, "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))})
        self.assertIsNone(self._pass(w).kind)

    def test_fixed_fixture_pair_key_rejected(self):
        w = _World(self)
        wrappers = _accepted_eight_wrappers()
        wrappers[0]["fixture_record"]["pair_duplicate_key"] = generator.fixed_fixture_pair_key()
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": wrappers, "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))})
        self.assertIsNone(self._pass(w).kind)

    def test_duplicate_seed_tuple_rejected(self):
        w = _World(self)
        wrappers = _accepted_eight_wrappers()
        wrappers[1]["fixture_record"]["seed_tuple"] = wrappers[0]["fixture_record"]["seed_tuple"]
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": wrappers, "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))})
        self.assertIsNone(self._pass(w).kind)

    def test_wrong_wrapper_key_order_rejected(self):
        w = _World(self)
        wrappers = _accepted_eight_wrappers()
        wr = wrappers[0]
        wrappers[0] = {"seed_order_position": wr["seed_order_position"], "family_index": wr["family_index"],
                       "fixture_record": wr["fixture_record"]}
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": wrappers, "search_diagnostics": _diag("ACCEPTED_EIGHT", list(range(8)))})
        self.assertIsNone(self._pass(w).kind)

    def test_accepted_eight_cardinality_contradiction(self):
        w = _World(self)
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": [_distinct_wrapper(0)],
                          "search_diagnostics": _diag("ACCEPTED_EIGHT", [0])})
        self.assertIsNone(self._pass(w).kind)

    def test_seed_exhaustion_with_eight(self):
        w = _World(self)
        self._install(w, {"valid": True, "failure_code": None, "failure_stage": None,
                          "accepted_records": _accepted_eight_wrappers(),
                          "search_diagnostics": _diag("SEED_SPACE_EXHAUSTED", list(range(8)))})
        self.assertIsNone(self._pass(w).kind)

    def test_malformed_scan(self):
        w = _World(self)
        self._install(w, {"valid": True, "accepted_records": [], "search_diagnostics": {"wrong": 1}})
        self.assertIsNone(self._pass(w).kind)


# --------------------------------------------------------------------------- #
# Two-pass orchestration
# --------------------------------------------------------------------------- #

class TwoPassTests(unittest.TestCase):
    def test_positive_finalization(self):
        w = _World(self)
        _patch_positive_freeze(self)
        seen = []
        w.install_scan(_scan_accepted_eight())
        w.runner._seed_iterator_factory = lambda: (seen.append(object()) or seen[-1])
        result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "POSITIVE")
        self.assertEqual(len(seen), 2)
        self.assertIsNot(seen[0], seen[1])
        self.assertIsNot(result["pass_1"].manifest, result["pass_2"].manifest)

    def test_fixed_fixture_failure(self):
        w = _World(self)
        invalid = dict(verifier.verify_fixed_fixture())
        invalid["validation"] = {"valid": False,
                                 "failure_code": "FIXED_FIXTURE_TRIPLE_CERTIFICATE_FAILURE", "detail": None}
        fake_verifier = types.SimpleNamespace(verify_fixed_fixture=lambda: dict(invalid))
        w.install_scan(_scan_accepted_eight(), verifier_module=fake_verifier)
        with mock.patch.object(freeze, "finalize_authoritative_manifest") as fin:
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "CANONICAL_FAILURE")
        self.assertEqual(result["pass_1"].kind, "FIXED_FIXTURE_FAILURE")
        fin.assert_not_called()

    def test_seed_exhaustion(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(freeze, "finalize_authoritative_manifest") as fin:
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "CANONICAL_FAILURE")
        self.assertEqual(result["pass_1"].kind, "SEED_SPACE_EXHAUSTED")
        fin.assert_not_called()

    def test_replay_mismatch(self):
        w = _World(self)
        calls = {"i": 0}

        def manifest_effect(*a, **k):
            m = _canned_manifest()
            if calls["i"] == 1:
                m["manifest_payload_sha256"] = "9" * 64   # pass 2 differs
            calls["i"] += 1
            return m
        _patch_positive_freeze(self, manifest_effect=manifest_effect)
        w.install_scan(_scan_accepted_eight())
        result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "REPLAY_MISMATCH")
        self.assertFalse(result["comparison"]["matches"])

    def test_pass_failure(self):
        w = _World(self)
        w.install_scan(_scan_returning({"valid": False, "failure_code": "SEED_ENUMERATION_FAILURE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        self.assertEqual(result["pass_1"].summary["failure_code"], "SEED_ENUMERATION_FAILURE")
        self.assertEqual(result["pass_1"].summary["failure_stage"], "pass_1")

    def test_comparison_process_failure(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        fault = freeze.SyntheticFixtureProcessFailure("MANIFEST_SCHEMA_FAILURE", "replay_comparison", "x")
        with mock.patch.object(freeze, "compare_candidate_passes", side_effect=fault):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "COMPARISON_PROCESS_FAILURE")
        self.assertEqual(result["failure_code"], "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(result["failure_stage"], "replay_comparison")
        self.assertIsNone(result["comparison"])

    def test_finalization_replay_mismatch(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        fault = freeze.SyntheticFixtureProcessFailure("REPLAY_MISMATCH", "finalization", "x")
        with mock.patch.object(freeze, "finalize_authoritative_manifest", side_effect=fault):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "FINALIZATION_FAILURE")
        self.assertEqual(result["failure_code"], "REPLAY_MISMATCH")
        self.assertEqual(result["failure_stage"], "finalization")

    def test_finalization_hash_identity(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        fault = freeze.SyntheticFixtureProcessFailure("HASH_IDENTITY_FAILURE", "hash_identity", "x")
        with mock.patch.object(freeze, "finalize_authoritative_manifest", side_effect=fault):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "FINALIZATION_FAILURE")
        self.assertEqual(result["failure_code"], "HASH_IDENTITY_FAILURE")


# --------------------------------------------------------------------------- #
# Unexpected-exception normalization
# --------------------------------------------------------------------------- #

class UnexpectedExceptionTests(unittest.TestCase):
    def test_verifier_keyerror_in_pass_normalized(self):
        w = _World(self)
        fake_verifier = types.SimpleNamespace(
            verify_fixed_fixture=lambda: (_ for _ in ()).throw(KeyError("boom")))
        w.install_scan(_scan_seed_exhausted_empty(), verifier_module=fake_verifier)
        result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        self.assertEqual(result["pass_1"].summary["failure_code"], "GENERATOR_CONFIGURATION_INVALID")

    def test_compare_runtimeerror_normalized(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(freeze, "compare_candidate_passes", side_effect=RuntimeError("boom")):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "COMPARISON_PROCESS_FAILURE")
        self.assertEqual(result["failure_code"], "MANIFEST_SCHEMA_FAILURE")

    def test_finalize_runtimeerror_normalized(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        with mock.patch.object(freeze, "finalize_authoritative_manifest", side_effect=RuntimeError("boom")):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "FINALIZATION_FAILURE")
        self.assertEqual(result["failure_code"], "HASH_IDENTITY_FAILURE")

    def _final_dir(self, w):
        return os.path.join(w.repo_root, run.RESULTS_DIR, run.FINAL_DIR_NAME)

    def test_unexpected_pass_fault_publishes_process_failure_exit_1(self):
        # An unexpected pass fault is normalized to a deterministic process-failure
        # result, published as the exact two-file failure set, and returns exit 1
        # only after a successful promotion (no exit 1 from an escaped exception).
        w = _World(self)
        w.install_scan(_scan_raising(RuntimeError("boom")))
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")
        self.assertEqual(sorted(os.listdir(self._final_dir(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))

    def test_unexpected_pass_fault_result_is_publishable(self):
        # The normalized process-failure result serializes and validates as a
        # bound pass failure (committed code, exact pass_1 stage/top-level binding).
        w = _World(self)
        context = w.runner.pre_contact()
        w.install_scan(_scan_raising(RuntimeError("boom")))
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # full nested validation
        self.assertEqual(envelope["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        self.assertEqual(envelope["failure_stage"], "pass_1")
        self.assertEqual(envelope["pass_1_identity_summary"]["failure_code"],
                         "GENERATOR_CONFIGURATION_INVALID")

    def test_run_publish_unexpected_exception_exit_3(self):
        # An unexpected publication fault becomes an exit-3 publication failure with
        # the exact authorized stderr line; no path returns exit 1 for it.
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(w.runner, "_publish_impl", side_effect=RuntimeError("wild")):
            outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_PUBLICATION_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, (run.PUBLICATION_FAILURE_HASH_IDENTITY + "\n").encode("ascii"))

    def test_run_no_traceback_escapes_any_boundary(self):
        # No injected fault at any boundary escapes run() as a traceback.
        w1 = _World(self)
        w1.git.resolve_head = lambda: (_ for _ in ()).throw(RuntimeError("wild"))
        out1 = w1.runner.run()
        self.assertIsInstance(out1, run.Outcome)
        self.assertEqual(out1.exit_code, run.EXIT_PRE_CONTACT_REFUSAL)

        w2 = _World(self)
        w2.install_scan(_scan_raising(RuntimeError("wild")))
        out2 = w2.runner.run()
        self.assertIsInstance(out2, run.Outcome)
        self.assertEqual(out2.exit_code, run.EXIT_POST_CONTACT_FAILURE)

        w3 = _World(self)
        w3.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(w3.runner, "_publish_impl", side_effect=RuntimeError("wild")):
            out3 = w3.runner.run()
        self.assertIsInstance(out3, run.Outcome)
        self.assertEqual(out3.exit_code, run.EXIT_PUBLICATION_FAILURE)


# --------------------------------------------------------------------------- #
# Trusted-library return-shape normalization
# --------------------------------------------------------------------------- #

class TrustedReturnShapeTests(unittest.TestCase):
    def _final_dir(self, w):
        return os.path.join(w.repo_root, run.RESULTS_DIR, run.FINAL_DIR_NAME)

    # ---- Comparison return shape ---- #

    def test_comparison_empty_dict_normalized(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(freeze, "compare_candidate_passes", return_value={}):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "COMPARISON_PROCESS_FAILURE")
        self.assertEqual(result["failure_code"], "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(result["failure_stage"], "replay_comparison")
        self.assertIsNone(result["comparison"])

    def test_comparison_malformed_matches_normalized(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        bad = {"matches": "yes", "failure_code": None, "failure_stage": None, "mismatch_reasons": []}
        with mock.patch.object(freeze, "compare_candidate_passes", return_value=bad):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "COMPARISON_PROCESS_FAILURE")
        self.assertEqual(result["failure_code"], "MANIFEST_SCHEMA_FAILURE")
        self.assertEqual(result["failure_stage"], "replay_comparison")
        self.assertIsNone(result["comparison"])

    def test_malformed_comparison_run_never_raises(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        with mock.patch.object(freeze, "compare_candidate_passes", return_value={}):
            outcome = w.runner.run()
        self.assertIsInstance(outcome, run.Outcome)
        self.assertEqual(outcome.exit_code, run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")
        self.assertEqual(sorted(os.listdir(self._final_dir(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))

    # ---- Finalization return shape ---- #

    def test_finalization_empty_dict_normalized(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        with mock.patch.object(freeze, "finalize_authoritative_manifest", return_value={}):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "FINALIZATION_FAILURE")
        self.assertEqual(result["failure_code"], "HASH_IDENTITY_FAILURE")
        self.assertEqual(result["failure_stage"], "finalization")

    def test_finalization_malformed_hashes_normalized(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        bad = {"final_manifest_object": {"family_frozen": True}, "canonical_payload_bytes": b"P",
               "manifest_payload_sha256": "not-hex", "canonical_manifest_bytes": b"M",
               "external_manifest_sha256": "4" * 64}
        with mock.patch.object(freeze, "finalize_authoritative_manifest", return_value=bad):
            result = w.runner.two_pass_operation(w.context())
        self.assertEqual(result["outcome"], "FINALIZATION_FAILURE")
        self.assertEqual(result["failure_code"], "HASH_IDENTITY_FAILURE")
        self.assertEqual(result["failure_stage"], "finalization")

    def test_malformed_finalization_publishes_two_files_exit_1(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        with mock.patch.object(freeze, "finalize_authoritative_manifest", return_value={}):
            outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")
        self.assertEqual(sorted(os.listdir(self._final_dir(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))

    # ---- Generator failure-code normalization ---- #

    def test_unknown_scan_code_normalized_and_serializable(self):
        w = _World(self)
        context = w.context()
        w.install_scan(_scan_returning({"valid": False, "failure_code": "NOT_A_REAL_CODE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        self.assertEqual(result["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        self.assertEqual(result["failure_stage"], "pass_1")
        self.assertEqual(result["pass_1"].summary["failure_code"], "GENERATOR_CONFIGURATION_INVALID")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # must not become a publication failure

    def test_unknown_scan_code_publishes_two_files_exit_1(self):
        w = _World(self)
        w.install_scan(_scan_returning({"valid": False, "failure_code": "NOT_A_REAL_CODE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")
        self.assertEqual(sorted(os.listdir(self._final_dir(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))

    # ---- Codex 2: only truthful generator scan codes are preserved ---- #

    def _pass1_code_for(self, reported):
        w = _World(self)
        context = w.context()
        w.install_scan(_scan_returning({"valid": False, "failure_code": reported,
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # normalized failures still serialize
        return result["pass_1"].summary["failure_code"]

    def test_scan_code_seed_enumeration_preserved(self):
        self.assertEqual(self._pass1_code_for("SEED_ENUMERATION_FAILURE"), "SEED_ENUMERATION_FAILURE")

    def test_scan_code_generator_configuration_preserved(self):
        self.assertEqual(self._pass1_code_for("GENERATOR_CONFIGURATION_INVALID"),
                         "GENERATOR_CONFIGURATION_INVALID")

    def test_scan_code_replay_mismatch_normalized(self):
        self.assertEqual(self._pass1_code_for("REPLAY_MISMATCH"), "GENERATOR_CONFIGURATION_INVALID")

    def test_scan_code_unauthorized_execution_normalized(self):
        self.assertEqual(self._pass1_code_for("UNAUTHORIZED_EXECUTION"), "GENERATOR_CONFIGURATION_INVALID")

    def test_scan_code_hash_identity_normalized(self):
        self.assertEqual(self._pass1_code_for("HASH_IDENTITY_FAILURE"), "GENERATOR_CONFIGURATION_INVALID")

    def test_scan_code_unknown_string_normalized(self):
        self.assertEqual(self._pass1_code_for("TOTALLY_MADE_UP"), "GENERATOR_CONFIGURATION_INVALID")

    def test_scan_code_null_normalized(self):
        self.assertEqual(self._pass1_code_for(None), "GENERATOR_CONFIGURATION_INVALID")

    def test_inappropriate_committed_scan_code_publishes_two_files_exit_1(self):
        # A committed-but-non-generator code is normalized, serializes, publishes
        # the two-file process-failure evidence, and exits 1 (never a publication
        # failure at serialization).
        w = _World(self)
        w.install_scan(_scan_returning({"valid": False, "failure_code": "UNAUTHORIZED_EXECUTION",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")
        self.assertEqual(sorted(os.listdir(self._final_dir(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))


# --------------------------------------------------------------------------- #
# Envelope validation
# --------------------------------------------------------------------------- #

class EnvelopeTests(unittest.TestCase):
    def _positive_envelope(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        context = w.context()
        result = w.runner.two_pass_operation(context)
        return w, context, result, w.runner.build_execution_envelope(context, result)

    def test_valid_positive_envelope(self):
        w, context, result, envelope = self._positive_envelope()
        self.assertEqual(tuple(envelope.keys()), run.ENVELOPE_KEY_ORDER)
        data = run.serialize_execution_envelope(envelope)   # full nested validation
        self.assertTrue(data.endswith(b"\n") and not data.endswith(b"\n\n"))
        self.assertEqual(data.count(b"\n"), 1)

    def test_reject_float(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["manifest_payload_sha256"] = 1.5
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_nan(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["external_manifest_sha256"] = float("nan")
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_relative_but_wrong_source_path(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["source_identities"] = [dict(o) for o in envelope["source_identities"]]
        envelope["source_identities"][0]["source_path"] = "research/brainvision/wrong.py"
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_source_hash(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["source_identities"] = [dict(o) for o in envelope["source_identities"]]
        envelope["source_identities"][0]["git_blob"] = "0" * 40
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_config_sha(self):
        w, context, result, envelope = self._positive_envelope()
        ci = dict(envelope["configuration_identity"]); ci["configuration_sha256"] = "0" * 64
        envelope["configuration_identity"] = ci
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_python_version(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["python_version"] = "1.2.3"
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_complete_with_family_frozen_false(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["family_frozen"] = False
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_contact_state(self):
        w, context, result, envelope = self._positive_envelope()
        envelope["canonical_contact_status"] = "PASS_1_STARTED"
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_failure_vocabulary(self):
        w, context, result, envelope = self._positive_envelope()
        # A published positive envelope must have failure_code None; a bogus code fails.
        envelope["manifest_payload_sha256"] = None
        envelope["external_manifest_sha256"] = None
        envelope["family_frozen"] = False
        envelope["finalization_status"] = "NOT_STARTED"
        envelope["comparison_result"] = None
        envelope["failure_code"] = "NOT_A_REAL_CODE"
        envelope["failure_stage"] = "pass_1"
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_manifest_hashes(self):
        # In a canonical-failure envelope the manifest hashes must equal the
        # replay-matched pass-bundle identities; a corrupted hash is rejected.
        w = _World(self)
        context = w.runner.pre_contact()
        w.install_scan(_scan_seed_exhausted_empty())
        result = w.runner.two_pass_operation(context)
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid
        envelope["manifest_payload_sha256"] = "a" * 64
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_wrong_terminal_status_for_pass_kind(self):
        w, context, result, envelope = self._positive_envelope()
        summary = dict(envelope["pass_1_identity_summary"])
        diag = dict(summary["search_diagnostics"]); diag["terminal_status"] = "SEED_SPACE_EXHAUSTED"
        summary["search_diagnostics"] = diag
        envelope["pass_1_identity_summary"] = summary
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_top_level_key_reorder(self):
        w, context, result, envelope = self._positive_envelope()
        reordered = {"envelope_version": envelope["envelope_version"]}
        for key in run.ENVELOPE_KEY_ORDER:
            if key != "envelope_version":
                reordered[key] = envelope[key]
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, reordered)

    # ---- Blocker 2: FAILED is a genuine positive-finalization failure only ---- #

    def test_reject_seed_exhaustion_mutated_to_failed(self):
        # A valid matched seed-exhaustion (NOT_APPLICABLE) envelope mutated to a
        # FAILED finalization_status must be rejected on serialization.
        w = _World(self)
        context = w.runner.pre_contact()
        w.install_scan(_scan_seed_exhausted_empty())
        result = w.runner.two_pass_operation(context)
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid (NOT_APPLICABLE)
        envelope["finalization_status"] = "FAILED"
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    # ---- Blocker 3: pass failures are bound exactly to the envelope failure ---- #

    def _pass1_failure_envelope(self):
        w = _World(self)
        context = w.context()
        w.install_scan(_scan_returning({"valid": False, "failure_code": "SEED_ENUMERATION_FAILURE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid
        return w, envelope

    def _pass2_failure_envelope(self):
        w = _World(self)
        context = w.context()
        w.install_scan(_scan_first_ok_then_fail())
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "PASS_FAILURE")
        self.assertEqual(result["failure_stage"], "pass_2")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid
        return w, envelope

    def _comparison_process_envelope(self):
        w = _World(self)
        context = w.context()
        w.install_scan(_scan_seed_exhausted_empty())
        fault = freeze.SyntheticFixtureProcessFailure("MANIFEST_SCHEMA_FAILURE", "replay_comparison", "x")
        with mock.patch.object(freeze, "compare_candidate_passes", side_effect=fault):
            result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "COMPARISON_PROCESS_FAILURE")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid
        return w, envelope

    def test_reject_noncanonical_pass_summary_code(self):
        w, envelope = self._pass1_failure_envelope()
        summary = dict(envelope["pass_1_identity_summary"])
        summary["failure_code"] = "NOT_A_REAL_CODE"
        envelope["pass_1_identity_summary"] = summary
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_pass_top_level_code_disagreement(self):
        w, envelope = self._pass1_failure_envelope()
        envelope["failure_code"] = "CONSTRUCTION_FAILURE"   # committed, but != pass_1 code
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_pass_top_level_stage_disagreement(self):
        w, envelope = self._pass1_failure_envelope()
        envelope["failure_stage"] = "pass_2"   # a valid stage, but not pass 1's
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_pass1_failure_with_non_not_started_pass2(self):
        w, envelope = self._pass1_failure_envelope()
        summary = dict(envelope["pass_2_identity_summary"])
        summary["pass_status"] = "FAILED"
        summary["failure_code"] = "SEED_ENUMERATION_FAILURE"
        summary["failure_stage"] = "pass_2"
        envelope["pass_2_identity_summary"] = summary
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_pass2_failure_without_complete_pass1(self):
        w, envelope = self._pass2_failure_envelope()
        envelope["pass_1_identity_summary"] = run._not_started_pass_summary("PASS_1")
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_comparison_process_wrong_replay_code(self):
        w, envelope = self._comparison_process_envelope()
        envelope["failure_code"] = "HASH_IDENTITY_FAILURE"   # committed, but not the bound code
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    # ---- Codex 1: the ordinary replay-mismatch envelope state is fully bound ---- #

    def _replay_mismatch_envelope(self):
        w = _World(self)
        calls = {"i": 0}

        def manifest_effect(*a, **k):
            m = _canned_manifest()
            if calls["i"] == 1:
                m["manifest_payload_sha256"] = "9" * 64   # pass 2 differs
            calls["i"] += 1
            return m
        _patch_positive_freeze(self, manifest_effect=manifest_effect)
        w.install_scan(_scan_accepted_eight())
        context = w.context()
        result = w.runner.two_pass_operation(context)
        self.assertEqual(result["outcome"], "REPLAY_MISMATCH")
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # baseline valid
        return w, envelope

    def test_valid_replay_mismatch_serializes(self):
        w, envelope = self._replay_mismatch_envelope()
        run.serialize_execution_envelope(envelope)   # the accepted path is preserved

    def test_reject_replay_mismatch_pass2_not_started(self):
        w, envelope = self._replay_mismatch_envelope()
        envelope["pass_2_identity_summary"] = run._not_started_pass_summary("PASS_2")
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_replay_mismatch_pass1_failed(self):
        w, envelope = self._replay_mismatch_envelope()
        summary = run._not_started_pass_summary("PASS_1")
        summary["pass_status"] = "FAILED"
        summary["failure_code"] = "SEED_ENUMERATION_FAILURE"
        summary["failure_stage"] = "pass_1"
        envelope["pass_1_identity_summary"] = summary
        envelope["canonical_contact_status"] = "PASS_1_STARTED"   # reach the replay-mismatch binding
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_replay_mismatch_null_failure_code(self):
        w, envelope = self._replay_mismatch_envelope()
        envelope["failure_code"] = None
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_replay_mismatch_different_failure_code(self):
        w, envelope = self._replay_mismatch_envelope()
        envelope["failure_code"] = "HASH_IDENTITY_FAILURE"   # committed, but not REPLAY_MISMATCH
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)

    def test_reject_replay_mismatch_wrong_failure_stage(self):
        w, envelope = self._replay_mismatch_envelope()
        envelope["failure_stage"] = "finalization"   # a valid stage, but not replay_comparison
        self.assertRaises(run.PostContactFailure, run.serialize_execution_envelope, envelope)


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #

class SummaryTests(unittest.TestCase):
    def _positive_envelope(self):
        w = _World(self)
        _patch_positive_freeze(self)
        w.install_scan(_scan_accepted_eight())
        context = w.context()
        return w.runner.build_execution_envelope(context, w.runner.two_pass_operation(context))

    def test_positive_summary(self):
        text = run.build_summary_text(self._positive_envelope()).decode("ascii")
        lines = text.split("\n")
        self.assertEqual(lines[-1], "")
        self.assertEqual(tuple(line.split("=", 1)[0] for line in lines[:-1]), run.SUMMARY_LINE_ORDER)
        self.assertIn("canonical_result_kind=ACCEPTED_EIGHT", text)
        self.assertIn("family_frozen=true", text)
        self.assertIn("finalization_status=COMPLETE", text)

    def test_comparison_process_summary_is_process_failure(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        fault = freeze.SyntheticFixtureProcessFailure("MANIFEST_SCHEMA_FAILURE", "replay_comparison", "x")
        with mock.patch.object(freeze, "compare_candidate_passes", side_effect=fault):
            context = w.context()
            result = w.runner.two_pass_operation(context)
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # must validate
        text = run.build_summary_text(envelope).decode("ascii")
        self.assertIn("canonical_result_kind=PROCESS_FAILURE", text)
        self.assertIn("finalization_status=NOT_STARTED", text)
        self.assertIn("comparison_status=NOT_RUN", text)

    def test_replay_mismatch_summary_is_process_failure(self):
        w = _World(self)
        calls = {"i": 0}

        def manifest_effect(*a, **k):
            m = _canned_manifest()
            if calls["i"] == 1:
                m["manifest_payload_sha256"] = "9" * 64
            calls["i"] += 1
            return m
        _patch_positive_freeze(self, manifest_effect=manifest_effect)
        w.install_scan(_scan_accepted_eight())
        context = w.context()
        result = w.runner.two_pass_operation(context)
        envelope = w.runner.build_execution_envelope(context, result)
        run.serialize_execution_envelope(envelope)   # must validate
        text = run.build_summary_text(envelope).decode("ascii")
        self.assertIn("canonical_result_kind=PROCESS_FAILURE", text)
        self.assertIn("comparison_status=MISMATCH", text)


# --------------------------------------------------------------------------- #
# Publication
# --------------------------------------------------------------------------- #

class PublicationTests(unittest.TestCase):
    def _seed_exhausted(self, renamer=None):
        w = _World(self, renamer=renamer)
        context = w.runner.pre_contact()
        w.install_scan(_scan_seed_exhausted_empty())
        result = w.runner.two_pass_operation(context)
        return w, context, result

    def _positive(self, renamer=None):
        w = _World(self, renamer=renamer)
        _patch_positive_freeze(self)
        context = w.context()
        w.install_scan(_scan_accepted_eight())
        result = w.runner.two_pass_operation(context)
        return w, context, result

    def _final(self, w):
        return os.path.join(w.repo_root, run.RESULTS_DIR, run.FINAL_DIR_NAME)

    def _staging(self, w):
        return os.path.join(w.repo_root, run.RESULTS_DIR, run.STAGING_DIR_NAME)

    def test_positive_three_files_exit_0(self):
        w, context, result = self._positive()
        self.assertEqual(w.runner.publish(context, result), run.EXIT_PROMOTED)
        self.assertEqual(sorted(os.listdir(self._final(w))),
                         sorted([run.MANIFEST_FILE_NAME, run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))
        self.assertFalse(os.path.exists(self._staging(w)))

    def test_seed_exhaustion_three_files_exit_0(self):
        w, context, result = self._seed_exhausted()
        self.assertEqual(w.runner.publish(context, result), run.EXIT_PROMOTED)
        self.assertIn(run.MANIFEST_FILE_NAME, os.listdir(self._final(w)))

    def test_process_failure_two_files_exit_1(self):
        w = _World(self)
        context = w.runner.pre_contact()
        w.install_scan(_scan_returning({"valid": False, "failure_code": "SEED_ENUMERATION_FAILURE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        result = w.runner.two_pass_operation(context)
        self.assertEqual(w.runner.publish(context, result), run.EXIT_POST_CONTACT_FAILURE)
        self.assertEqual(sorted(os.listdir(self._final(w))),
                         sorted([run.ENVELOPE_FILE_NAME, run.SUMMARY_FILE_NAME]))

    def test_positive_manifest_bytes(self):
        w, context, result = self._positive()
        w.runner.publish(context, result)
        with open(os.path.join(self._final(w), run.MANIFEST_FILE_NAME), "rb") as handle:
            self.assertEqual(handle.read(), result["finalized"]["canonical_manifest_bytes"])

    def test_canonical_failure_reuses_pass_bytes_without_reserialization(self):
        w, context, result = self._seed_exhausted()
        expected = result["pass_1"].bundle["canonical_manifest_bytes"]
        with mock.patch.object(freeze, "canonical_manifest_bytes",
                               wraps=freeze.canonical_manifest_bytes) as spy:
            w.runner.publish(context, result)
        spy.assert_not_called()
        with open(os.path.join(self._final(w), run.MANIFEST_FILE_NAME), "rb") as handle:
            self.assertEqual(handle.read(), expected)

    def test_rename_failure(self):
        def bad_rename(src, dst):
            raise OSError("blocked")
        w, context, result = self._seed_exhausted(renamer=bad_rename)
        with self.assertRaises(run.PublicationFailure) as ctx:
            w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_HASH_IDENTITY)
        staging = self._staging(w)
        self.assertTrue(os.path.isdir(staging))
        with open(os.path.join(staging, run.MANIFEST_FILE_NAME), "rb") as handle:
            self.assertEqual(handle.read(), result["pass_1"].bundle["canonical_manifest_bytes"])
        self.assertFalse(os.path.exists(self._final(w)))

    def test_write_failure_serialization(self):
        w, context, result = self._seed_exhausted()
        real_open = open

        def bad_open(path, mode="r", *a, **k):
            if isinstance(path, str) and path.endswith(".json") and "x" in mode:
                raise OSError("write blocked")
            return real_open(path, mode, *a, **k)
        with mock.patch("builtins.open", bad_open):
            with self.assertRaises(run.PublicationFailure) as ctx:
                w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_SERIALIZATION)

    def test_listing_failure_hash(self):
        w, context, result = self._seed_exhausted()
        with mock.patch("os.listdir", side_effect=OSError("no listdir")):
            with self.assertRaises(run.PublicationFailure) as ctx:
                w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_HASH_IDENTITY)

    def test_serialization_fault(self):
        w, context, result = self._seed_exhausted()
        with mock.patch.object(run, "serialize_execution_envelope",
                               side_effect=run.PostContactFailure("SERIALIZATION_FAILURE", "serialization", "x")):
            with self.assertRaises(run.PublicationFailure) as ctx:
                w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_SERIALIZATION)

    def test_publication_fault_before_staging_creates_no_evidence(self):
        # An unexpected fault before staging is created leaves no fabricated
        # evidence: neither the staging nor the final directory exists.
        w, context, result = self._seed_exhausted()
        with mock.patch.object(run, "serialize_execution_envelope", side_effect=RuntimeError("pre-staging")):
            with self.assertRaises(run.PublicationFailure) as ctx:
                w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_HASH_IDENTITY)
        self.assertFalse(os.path.exists(self._staging(w)))
        self.assertFalse(os.path.exists(self._final(w)))

    def test_publication_fault_after_partial_staging_retained(self):
        # An unexpected fault after the first staged file is written retains the
        # partial staging exactly (first file present, no promotion).
        w, context, result = self._seed_exhausted()
        real_open = open

        def bad_open(path, mode="r", *a, **k):
            if isinstance(path, str) and os.path.basename(path) == run.ENVELOPE_FILE_NAME and "x" in mode:
                raise RuntimeError("unexpected mid-staging fault")
            return real_open(path, mode, *a, **k)
        with mock.patch("builtins.open", bad_open):
            with self.assertRaises(run.PublicationFailure) as ctx:
                w.runner.publish(context, result)
        self.assertEqual(ctx.exception.stderr_line, run.PUBLICATION_FAILURE_HASH_IDENTITY)
        staging = self._staging(w)
        self.assertTrue(os.path.isdir(staging))
        self.assertEqual(os.listdir(staging), [run.MANIFEST_FILE_NAME])
        self.assertFalse(os.path.exists(self._final(w)))


# --------------------------------------------------------------------------- #
# Full run() outcomes
# --------------------------------------------------------------------------- #

class RunOutcomeTests(unittest.TestCase):
    def test_canonical_result_exit_0(self):
        w = _World(self)
        w.install_scan(_scan_seed_exhausted_empty())
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_PROMOTED)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, b"")

    def test_pre_contact_refusal_exit_2(self):
        w = _World(self); w.git.branch = "feature"
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_PRE_CONTACT_REFUSAL)
        self.assertFalse(os.path.exists(os.path.join(w.repo_root, run.RESULTS_DIR)))

    def test_process_failure_exit_1(self):
        w = _World(self)
        w.install_scan(_scan_returning({"valid": False, "failure_code": "SEED_ENUMERATION_FAILURE",
                                        "failure_stage": "seed_validation", "accepted_records": []}))
        self.assertEqual(w.runner.run().exit_code, run.EXIT_POST_CONTACT_FAILURE)

    def test_rename_failure_exit_3(self):
        def bad_rename(src, dst):
            raise OSError("blocked")
        w = _World(self, renamer=bad_rename)
        w.install_scan(_scan_seed_exhausted_empty())
        outcome = w.runner.run()
        self.assertEqual(outcome.exit_code, run.EXIT_PUBLICATION_FAILURE)
        self.assertEqual(outcome.stdout, b"")
        self.assertEqual(outcome.stderr, (run.PUBLICATION_FAILURE_HASH_IDENTITY + "\n").encode("ascii"))
