"""Bounded non-authoritative tests for Stage S3B v0.2 synthetic validation."""

from __future__ import annotations

import ast
import builtins
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import independent_order_sensitive_descriptor_v0_1 as descriptor
import independent_order_sensitive_synthetic_validation_schema_contract_v0_2 as schema
import run_independent_order_sensitive_synthetic_validation_v0_2 as runner


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
FREEZE_LIBRARY = HERE / "independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"
VERIFIER_SOURCE = HERE / "independent_order_sensitive_synthetic_fixture_verifier_v0_1.py"
FREEZE_RUNNER_SOURCE = HERE / "run_independent_order_sensitive_synthetic_fixture_freeze_v0_1.py"

THREE_AUTHORIZED_FILES = {
    "research/brainvision/independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py",
    "research/brainvision/run_independent_order_sensitive_synthetic_validation_v0_2.py",
    "research/brainvision/test_independent_order_sensitive_synthetic_fixtures_v0_2.py",
}


def _repo_state() -> runner.RepositoryState:
    return runner.RepositoryState(
        str(REPO_ROOT),
        "main",
        True,
        "4dd7784922f3f4d11de203ffd42f1cca473bef59",
        "4dd7784922f3f4d11de203ffd42f1cca473bef59",
        "3.11.15",
    )


def _paths(tmp_path: Path) -> runner.ExecutionPaths:
    return runner.ExecutionPaths(
        str(tmp_path / "synthetic-validation-v0-2.arming"),
        str(tmp_path / "synthetic-validation-v0-2.journal"),
        str(tmp_path / "synthetic-validation-v0-2.staging"),
        str(tmp_path / "synthetic-validation-v0-2.final"),
    )


def _manifest_bytes(manifest=None) -> bytes:
    if manifest is None:
        manifest = make_manifest()
    return schema.canonical_json_bytes(manifest)


def _rehash_manifest(manifest):
    manifest["manifest_payload_sha256"] = "0" * 64
    manifest["manifest_payload_sha256"] = schema.manifest_payload_sha256(manifest)
    return manifest


def _rotated_support(start: int, step: int):
    values = sorted({(start + step * offset) % schema.N for offset in range(schema.REQUIRED_WEIGHT)})
    while len(values) < schema.REQUIRED_WEIGHT:
        start = (start + 1) % schema.N
        values = sorted(set(values) | {start})
    return values[:schema.REQUIRED_WEIGHT]


def _simple_a2(seed: int):
    return [schema.REQUIRED_WEIGHT] + [((seed + offset) % 5) for offset in range(1, schema.N)]


def _simple_transition_table(seed: int):
    return [[seed + 1, seed + 2], [seed + 3, seed + 4]]


def _certificate(search_space_size: int):
    return {
        "equivalent": False,
        "search_space_size": search_space_size,
        "first_equivalence_mapping": None,
    }


def _triple_indices(count: int):
    return [[(index % (schema.N - 1)) + 1, ((index * 3) % (schema.N - 1)) + 1]
            for index in range(count)]


def make_fixed_fixture():
    support_h0 = _rotated_support(0, 1)
    support_h1 = _rotated_support(1, 2)
    binary_h0 = schema.support_to_binary(support_h0)
    binary_h1 = schema.support_to_binary(support_h1)
    key_h0 = schema.binary_key(binary_h0)
    key_h1 = schema.binary_key(binary_h1)
    return {
        "C": [0, 1, 4],
        "D": [0, 2, 8],
        "support_H0": support_h0,
        "support_H1": support_h1,
        "binary_H0": binary_h0,
        "binary_H1": binary_h1,
        "weight_H0": schema.REQUIRED_WEIGHT,
        "weight_H1": schema.REQUIRED_WEIGHT,
        "A2_H0": _simple_a2(0),
        "A2_H1": _simple_a2(0),
        "transition_table_H0": _simple_transition_table(0),
        "transition_table_H1": _simple_transition_table(0),
        "affine_inequivalence_certificate": _certificate(schema.AFFINE_SEARCH_SPACE_SIZE),
        "affine_complement_inequivalence_certificate": _certificate(
            schema.AFFINE_COMPLEMENT_SEARCH_SPACE_SIZE,
        ),
        "triple_disagreement_count": 8,
        "triple_disagreement_indices": _triple_indices(8),
        "member_orbit_key_H0": key_h0,
        "member_orbit_key_H1": key_h1,
        "pair_duplicate_key": sorted([key_h0, key_h1]),
        "validation": {"valid": True, "failure_code": None, "detail": None},
    }


def make_accepted_fixture(family_index: int, seed_order_position=None):
    if seed_order_position is None:
        seed_order_position = family_index
    support_a = _rotated_support(2 + family_index * 5, 1)
    support_b = _rotated_support(3 + family_index * 5, 2)
    binary_a = schema.support_to_binary(support_a)
    binary_b = schema.support_to_binary(support_b)
    key_a = schema.binary_key(binary_a)
    key_b = schema.binary_key(binary_b)
    seed_tuple = [
        family_index,
        (family_index + 1) % schema.N,
        (family_index + 2) % schema.N,
        (family_index + 3) % schema.N,
    ]
    return {
        "family_index": family_index,
        "seed_order_position": seed_order_position,
        "seed_tuple": seed_tuple,
        "C": [0, seed_tuple[0], seed_tuple[1]],
        "D": [0, seed_tuple[2], seed_tuple[3]],
        "support_A": support_a,
        "support_B": support_b,
        "binary_A": binary_a,
        "binary_B": binary_b,
        "weight_A": schema.REQUIRED_WEIGHT,
        "weight_B": schema.REQUIRED_WEIGHT,
        "A2_A": _simple_a2(family_index + 1),
        "A2_B": _simple_a2(family_index + 1),
        "transition_table_A": _simple_transition_table(family_index + 1),
        "transition_table_B": _simple_transition_table(family_index + 1),
        "affine_inequivalence_certificate": _certificate(schema.AFFINE_SEARCH_SPACE_SIZE),
        "affine_complement_inequivalence_certificate": _certificate(
            schema.AFFINE_COMPLEMENT_SEARCH_SPACE_SIZE,
        ),
        "triple_disagreement_count": 8,
        "triple_disagreement_indices": _triple_indices(8),
        "member_orbit_key_A": key_a,
        "member_orbit_key_B": key_b,
        "pair_duplicate_key": sorted([key_a, key_b]),
    }


def make_manifest():
    accepted = [make_accepted_fixture(index) for index in range(schema.K_SYNTHETIC)]
    manifest = {
        "schema": schema.MANIFEST_SCHEMA,
        "generator_id": schema.GENERATOR_ID,
        "verifier_id": schema.VERIFIER_ID,
        "N": schema.N,
        "K_synthetic": schema.K_SYNTHETIC,
        "seed_enumeration_policy": schema.SEED_ENUMERATION_POLICY,
        "construction_policy": schema.CONSTRUCTION_POLICY,
        "eligibility_policy": schema.ELIGIBILITY_POLICY,
        "duplicate_policy": schema.DUPLICATE_POLICY,
        "family_frozen": True,
        "fixed_fixture": make_fixed_fixture(),
        "accepted_fixtures": accepted,
        "search_diagnostics": {
            "total_seeds_visited": schema.K_SYNTHETIC,
            "eligibility_rejection_counts": {
                key: 0 for key in schema.ELIGIBILITY_REJECTION_ORDER
            },
            "eligible_duplicate_count": 0,
            "accepted_seed_order_positions": list(range(schema.K_SYNTHETIC)),
            "terminal_seed_tuple": [0, 1, 2, 3],
            "terminal_status": "ACCEPTED_EIGHT",
        },
        "source_identity": {
            "generator_source_path": (
                "research/brainvision/"
                "independent_order_sensitive_synthetic_fixture_generator_v0_1.py"
            ),
            "generator_git_blob": "1" * 40,
            "generator_raw_sha256": "2" * 64,
            "verifier_source_path": (
                "research/brainvision/"
                "independent_order_sensitive_synthetic_fixture_verifier_v0_1.py"
            ),
            "verifier_git_blob": "3" * 40,
            "verifier_raw_sha256": "4" * 64,
            "test_source_identities": [
                {
                    "source_path": "research/brainvision/source_%d.py" % index,
                    "git_blob": ("%x" % (index + 5)) * 40,
                    "raw_sha256": ("%x" % (index + 8)) * 64,
                }
                for index in range(3)
            ],
            "repository_commit": "a" * 40,
            "python_version": "3.11.15",
        },
        "configuration_identity": {
            "configuration_payload": schema.frozen_configuration_payload(),
            "configuration_sha256": schema.FROZEN_CONFIGURATION_SHA256,
        },
        "validation": {"valid": True, "failure_stage": None, "detail": None},
        "ordered_failure_codes": [],
        "manifest_payload_sha256": "0" * 64,
    }
    manifest["manifest_payload_sha256"] = schema.manifest_payload_sha256(manifest)
    return manifest


class ManifestReader:
    def __init__(self, payload: bytes, fail_on=None):
        self.payload = payload
        self.fail_on = set(fail_on or [])
        self.calls = []
        self.returned = []

    def __call__(self, pass_index: int) -> bytes:
        self.calls.append(pass_index)
        if pass_index in self.fail_on:
            raise OSError("synthetic read failure")
        fresh = bytes(bytearray(self.payload))
        self.returned.append(fresh)
        return fresh


class DescriptorRecorder:
    def __init__(self, collapse_vectors=None, fail=False):
        self.collapse_vectors = {tuple(vector) for vector in (collapse_vectors or [])}
        self.collapsed_signature = None
        if self.collapse_vectors:
            first = list(next(iter(self.collapse_vectors)))
            self.collapsed_signature = descriptor.affine_plus_complement_signature(first)
        self.fail = fail
        self.calls = []
        self.outputs = []

    def __call__(self, vector):
        assert isinstance(vector, list)
        assert len(vector) == schema.N
        assert all(isinstance(bit, int) and not isinstance(bit, bool) for bit in vector)
        assert all(bit in (0, 1) for bit in vector)
        self.calls.append({"id": id(vector), "vector": list(vector)})
        if self.fail:
            raise RuntimeError("synthetic descriptor failure")
        if tuple(vector) in self.collapse_vectors:
            output = self.collapsed_signature
        else:
            output = descriptor.affine_plus_complement_signature(vector)
        self.outputs.append(output)
        return output


class RecordingFs:
    def __init__(self, fail_rename=False):
        self.fail_rename = fail_rename
        self.log = []

    def path_exists(self, path):
        return os.path.exists(path)

    def path_is_dir(self, path):
        return os.path.isdir(path)

    def make_directory(self, path):
        self.log.append(("mkdir", path))
        os.mkdir(path)

    def rename_directory(self, source, destination):
        self.log.append(("rename", source, destination))
        if self.fail_rename:
            raise OSError("simulated rename failure")
        os.rename(source, destination)

    def replace_file(self, source, destination):
        self.log.append(("replace", source, destination))
        os.replace(source, destination)

    def list_directory(self, path):
        return os.listdir(path)

    def open_file(self, *args, **kwargs):
        return builtins.open(*args, **kwargs)

    def sync_directory(self, path):
        self.log.append(("sync_dir", path))

    def ops(self):
        return runner.FileSystemOps(
            path_exists=self.path_exists,
            path_is_dir=self.path_is_dir,
            make_directory=self.make_directory,
            rename_directory=self.rename_directory,
            replace_file=self.replace_file,
            list_directory=self.list_directory,
            open_file=self.open_file,
            sync_directory=self.sync_directory,
        )


def _config(tmp_path: Path, manifest=None, descriptor_callable=None, **kwargs):
    reader = ManifestReader(_manifest_bytes(manifest))
    recorder = descriptor_callable or DescriptorRecorder()
    config = runner.BoundedRunConfig(
        paths=_paths(tmp_path),
        read_manifest_bytes=reader,
        descriptor_callable=recorder,
        repository_state=_repo_state(),
        clock=lambda: "2026-07-22T00:00:00Z",
        **kwargs,
    )
    return config, reader, recorder


def _tuple_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError("missing assignment %s" % name)


def _function_return_dict_keys(path: Path, function_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                    return tuple(ast.literal_eval(key) for key in child.value.keys)
    raise AssertionError("missing return dict in %s" % function_name)


def _freeze_runner_configuration_payload():
    tree = ast.parse(FREEZE_RUNNER_SOURCE.read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    constants[target.id] = ast.literal_eval(node.value)
                except ValueError:
                    pass
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_configuration_payload":
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                    payload = {}
                    for key_node, value_node in zip(child.value.keys, child.value.values):
                        key = ast.literal_eval(key_node)
                        if isinstance(value_node, ast.Name):
                            payload[key] = constants[value_node.id]
                        else:
                            payload[key] = ast.literal_eval(value_node)
                    return payload
    raise AssertionError("missing build_configuration_payload return")


def _read_terminal_payload(journal_dir: str):
    path = Path(journal_dir) / "terminal_evidence.json"
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    assert wrapper["payload_sha256"] == schema.sha256_hex(
        schema.canonical_json_bytes(wrapper["payload"])
    )
    return wrapper["payload"]


def test_literal_key_contracts_are_normative():
    assert schema.FIXED_MEMBER_BINARY_KEYS == ("binary_H0", "binary_H1")
    assert schema.ACCEPTED_MEMBER_BINARY_KEYS == ("binary_A", "binary_B")
    assert schema.FIXED_FIXTURE_KEYS[4:6] == ("binary_H0", "binary_H1")
    assert schema.ACCEPTED_FIXTURE_KEYS[7:9] == ("binary_A", "binary_B")


def test_complete_ordered_manifest_schema_validates():
    manifest = make_manifest()
    assert tuple(manifest.keys()) == schema.MANIFEST_TOP_LEVEL_KEYS
    assert tuple(manifest["fixed_fixture"].keys()) == schema.FIXED_FIXTURE_KEYS
    assert tuple(manifest["accepted_fixtures"][0].keys()) == schema.ACCEPTED_FIXTURE_KEYS
    assert schema.validate_manifest_payload(manifest).valid


def test_schema_contract_runtime_surface_has_no_test_fixture_builders():
    assert not hasattr(schema, "make_manifest")
    assert not hasattr(schema, "make_fixed_fixture")
    assert not hasattr(schema, "make_accepted_fixture")
    source = Path(schema.__file__).read_text(encoding="utf-8")
    assert "def make_manifest" not in source
    assert "def make_fixed_fixture" not in source
    assert "def make_accepted_fixture" not in source


@pytest.mark.parametrize(
    "mutator, detail",
    [
        (lambda m: m.pop("schema"), "missing top-level field"),
        (lambda m: m.update({"unexpected": True}), "unexpected top-level field"),
        (
            lambda m: m.__setitem__(
                "fixed_fixture",
                {key: m["fixed_fixture"][key] for key in reversed(schema.FIXED_FIXTURE_KEYS)},
            ),
            "fixed order violation",
        ),
        (
            lambda m: m["fixed_fixture"].pop(schema.FIXED_MEMBER_BINARY_KEYS[0]),
            "missing fixed field",
        ),
        (
            lambda m: m["fixed_fixture"].update({"binary_A": [0] * schema.N}),
            "unexpected fixed field",
        ),
        (
            lambda m: m["accepted_fixtures"][0].pop(schema.ACCEPTED_MEMBER_BINARY_KEYS[0]),
            "missing accepted field",
        ),
        (
            lambda m: m["accepted_fixtures"][0].update({"binary_H0": [0] * schema.N}),
            "unexpected accepted field",
        ),
    ],
)
def test_schema_rejects_missing_unexpected_and_order_errors(mutator, detail):
    manifest = make_manifest()
    mutator(manifest)
    result = schema.validate_manifest_payload(manifest)
    assert not result.valid, detail


@pytest.mark.parametrize(
    "mutator",
    [
        lambda m: m.__setitem__("N", True),
        lambda m: m["fixed_fixture"].__setitem__(schema.FIXED_WEIGHT_KEYS[0], True),
        lambda m: m["fixed_fixture"].__setitem__(
            schema.FIXED_MEMBER_BINARY_KEYS[0],
            [0] * (schema.N - 1),
        ),
        lambda m: m["fixed_fixture"][schema.FIXED_MEMBER_BINARY_KEYS[0]].__setitem__(0, 2),
        lambda m: m["accepted_fixtures"][0].__setitem__(
            schema.ACCEPTED_MEMBER_BINARY_KEYS[0],
            [0] * (schema.N - 1),
        ),
        lambda m: m["accepted_fixtures"][0][schema.ACCEPTED_MEMBER_BINARY_KEYS[0]].__setitem__(0, True),
        lambda m: m["accepted_fixtures"].pop(),
        lambda m: m["accepted_fixtures"][1].__setitem__("family_index", 7),
        lambda m: m["accepted_fixtures"][1].__setitem__("seed_order_position", 0),
    ],
)
def test_schema_rejects_wrong_types_bool_binary_count_and_family_order(mutator):
    manifest = make_manifest()
    mutator(manifest)
    _rehash_manifest(manifest)
    assert not schema.validate_manifest_payload(manifest).valid


@pytest.mark.parametrize(
    "mutator",
    [
        lambda m: m["fixed_fixture"]["affine_inequivalence_certificate"].pop("equivalent"),
        lambda m: m["fixed_fixture"]["transition_table_H0"].__setitem__(0, [1]),
        lambda m: m["fixed_fixture"]["validation"].__setitem__("failure_code", "X"),
        lambda m: m["source_identity"].__setitem__("repository_commit", "not-hex"),
        lambda m: m["search_diagnostics"].__setitem__("terminal_status", "SEED_SPACE_EXHAUSTED"),
        lambda m: m["configuration_identity"].__setitem__("configuration_sha256", "0" * 64),
    ],
)
def test_schema_rejects_nested_certificate_lower_order_validation_identity_and_diagnostics(mutator):
    manifest = make_manifest()
    mutator(manifest)
    _rehash_manifest(manifest)
    assert not schema.validate_manifest_payload(manifest).valid


def test_provider_parity_for_manifest_and_accepted_contracts():
    assert _tuple_assignment(FREEZE_LIBRARY, "MANIFEST_TOP_LEVEL_KEYS") == schema.MANIFEST_TOP_LEVEL_KEYS
    assert _tuple_assignment(FREEZE_LIBRARY, "SOURCE_IDENTITY_KEYS") == schema.SOURCE_IDENTITY_KEYS
    assert _tuple_assignment(FREEZE_LIBRARY, "SEARCH_DIAGNOSTICS_KEYS") == schema.SEARCH_DIAGNOSTICS_KEYS
    assert _tuple_assignment(FREEZE_LIBRARY, "ACCEPTED_FIXTURE_KEYS") == schema.ACCEPTED_FIXTURE_KEYS


def test_provider_parity_for_fixed_fixture_contract():
    fixed_keys = _function_return_dict_keys(VERIFIER_SOURCE, "verify_fixed_fixture")
    assert fixed_keys == schema.FIXED_FIXTURE_KEYS
    assert "binary_H0" in fixed_keys
    assert "binary_H1" in fixed_keys
    assert "binary_A" not in fixed_keys
    assert "binary_B" not in fixed_keys


def test_provider_parity_for_configuration_payload_contract():
    payload = _freeze_runner_configuration_payload()
    assert tuple(payload.keys()) == schema.CONFIGURATION_PAYLOAD_KEYS
    assert payload == schema.frozen_configuration_payload()
    assert schema.canonical_configuration_sha256() == schema.FROZEN_CONFIGURATION_SHA256


def test_schema_contract_imports_no_provider_and_runner_import_graph_is_closed():
    schema_tree = ast.parse(Path(schema.__file__).read_text(encoding="utf-8"))
    runner_tree = ast.parse(Path(runner.__file__).read_text(encoding="utf-8"))
    schema_imports = {
        alias.name
        for node in ast.walk(schema_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    schema_imports.update(
        node.module
        for node in ast.walk(schema_tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert not any("synthetic_fixture" in item for item in schema_imports)

    runner_imports = {
        alias.name
        for node in ast.walk(runner_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "independent_order_sensitive_synthetic_validation_schema_contract_v0_2" in runner_imports
    assert "independent_order_sensitive_descriptor_v0_1" in runner_imports
    assert not any("synthetic_fixture" in item for item in runner_imports)


def test_fresh_process_import_purity_for_new_modules(tmp_path):
    script = r"""
import builtins
import os
import socket
import subprocess
import sys

original_open = builtins.open

def guarded_open(file, *args, **kwargs):
    mode = args[0] if args else kwargs.get("mode", "r")
    path = os.fspath(file) if hasattr(file, "__fspath__") else str(file)
    normalized = path.replace("\\", "/").lower()
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        raise AssertionError("filesystem write during import")
    if "synthetic_fixture_freeze_manifest_v0_1" in normalized:
        raise AssertionError("real manifest access during import")
    if "brainvision/results" in normalized:
        raise AssertionError("result-path access during import")
    return original_open(file, *args, **kwargs)

def forbidden(*args, **kwargs):
    raise AssertionError("prohibited import-time side effect")

builtins.open = guarded_open
os.mkdir = forbidden
os.makedirs = forbidden
os.rmdir = forbidden
os.remove = forbidden
os.unlink = forbidden
os.rename = forbidden
os.replace = forbidden
subprocess.run = forbidden
subprocess.Popen = forbidden
socket.socket = forbidden
sys.exit = forbidden

class GuardedStdin:
    @property
    def buffer(self):
        raise AssertionError("stdin buffer read during import")
    def read(self, *args, **kwargs):
        raise AssertionError("stdin read during import")

sys.stdin = GuardedStdin()

import independent_order_sensitive_descriptor_v0_1 as descriptor

descriptor.canonical_sha256 = forbidden
descriptor.affine_plus_complement_signature = forbidden
descriptor.raw_labeled_signature = forbidden
descriptor.affine_only_signature = forbidden
descriptor.descriptor_result = forbidden

import independent_order_sensitive_synthetic_validation_schema_contract_v0_2
import run_independent_order_sensitive_synthetic_validation_v0_2
import test_independent_order_sensitive_synthetic_fixtures_v0_2
print("imported")
"""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", "-c", script],
        cwd=str(HERE),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert completed.stdout.strip() == b"imported"
    for relative in (
            runner.EXECUTION_ARMING_PATH,
            runner.EXECUTION_JOURNAL_DIR,
            runner.SCIENTIFIC_RESULT_STAGING_DIR,
            runner.FINAL_PUBLICATION_DIR):
        assert not (REPO_ROOT / relative).exists()


def test_source_boundary_has_no_top_level_exit_main_or_mutation_calls():
    prohibited_names = {"open", "eval", "exec", "compile", "input"}
    prohibited_attrs = {
        "os.mkdir",
        "os.makedirs",
        "os.rmdir",
        "os.remove",
        "os.unlink",
        "os.rename",
        "os.replace",
        "subprocess.run",
        "subprocess.Popen",
        "socket.socket",
        "sys.exit",
    }

    def call_name(node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                return ".".join(reversed(parts))
        return None

    for path in (
            HERE / "independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py",
            HERE / "run_independent_order_sensitive_synthetic_validation_v0_2.py",
            HERE / "test_independent_order_sensitive_synthetic_fixtures_v0_2.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                name = call_name(node.value.func)
                if name in prohibited_names or name in prohibited_attrs:
                    pytest.fail("prohibited top-level call in %s" % path.name)
            values = []
            if isinstance(node, ast.Assign):
                values.append(node.value)
            elif isinstance(node, ast.AnnAssign):
                values.append(node.value)
            elif isinstance(node, ast.NamedExpr):
                values.append(node.value)
            for value in values:
                if value is None:
                    continue
                for child in ast.walk(value):
                    if isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                        pytest.fail("module-level comprehension in %s" % path.name)
                    if isinstance(child, ast.Call):
                        name = call_name(child.func)
                        if name in prohibited_names or name in prohibited_attrs:
                            pytest.fail("prohibited module-level call assignment in %s" % path.name)
        source = path.read_text(encoding="utf-8")
        assert ("sys" + ".exit(") not in source


def test_unbound_authoritative_preflight_refuses_before_paths_or_manifest(monkeypatch, tmp_path):
    monkeypatch.setenv("TORMENT_SYNTHETIC_VALIDATION_IDENTITY", "replacement")
    paths = _paths(tmp_path)
    with pytest.raises(runner.PreContactRefusal) as excinfo:
        runner.perform_precontact_validation(
            ["runner", "--manifest", "ignored"],
            b"",
            repository_state=_repo_state(),
            paths=paths,
        )
    assert excinfo.value.failure_code == runner.FAIL_PRECONTACT_AUTHORIZATION
    assert not Path(paths.execution_arming_path).exists()
    assert not Path(paths.execution_journal_dir).exists()
    assert not Path(paths.scientific_result_staging_dir).exists()
    assert not Path(paths.final_publication_dir).exists()


def test_run_authoritative_unbound_refuses_before_dependency_construction(monkeypatch, tmp_path):
    paths = _paths(tmp_path)

    def forbidden_construct(*args, **kwargs):
        raise AssertionError("authoritative dependencies constructed while UNBOUND")

    def forbidden_core(*args, **kwargs):
        raise AssertionError("authoritative core invoked while UNBOUND")

    monkeypatch.setattr(runner, "construct_authoritative_run_config", forbidden_construct)
    monkeypatch.setattr(runner, "run_bounded_validation", forbidden_core)
    outcome = runner.run_authoritative(
        ["runner"],
        b"",
        repository_state=_repo_state(),
        paths=paths,
    )
    assert outcome.exit_code == runner.EXIT_PRECONTACT_REFUSAL
    assert outcome.failure_code == runner.FAIL_PRECONTACT_AUTHORIZATION
    assert not Path(paths.execution_arming_path).exists()
    assert not Path(paths.execution_journal_dir).exists()
    assert not Path(paths.scientific_result_staging_dir).exists()
    assert not Path(paths.final_publication_dir).exists()


def test_authoritative_route_is_dormantly_wired_after_future_identity_binding(monkeypatch, tmp_path):
    paths = _paths(tmp_path)
    identities = {
        "later_execution_authorization_identity": "bound",
        "runner_git_blob": "bound",
        "runner_raw_sha256": "bound",
        "runner_test_git_blob": "bound",
        "runner_test_raw_sha256": "bound",
        "schema_contract_git_blob": "bound",
        "schema_contract_raw_sha256": "bound",
        "expected_manifest_external_sha256": "e" * 64,
        "expected_manifest_payload_sha256": "f" * 64,
        "v0_2_configuration_identity": "bound",
    }
    captured = {}

    def fake_core(config):
        captured["config"] = config
        return runner.RunOutcome(runner.EXIT_PRECONTACT_REFUSAL, authority_consumed=False)

    monkeypatch.setattr(runner, "run_bounded_validation", fake_core)
    outcome = runner.run_authoritative(
        ["runner"],
        b"",
        repository_state=_repo_state(),
        identities=identities,
        paths=paths,
    )
    assert outcome.exit_code == runner.EXIT_PRECONTACT_REFUSAL
    assert captured["config"].paths == paths
    assert captured["config"].descriptor_callable is runner.default_descriptor_callable
    assert captured["config"].expected_external_manifest_sha256 == "e" * 64
    assert captured["config"].expected_manifest_payload_sha256 == "f" * 64
    assert not Path(paths.execution_arming_path).exists()
    assert not Path(paths.execution_journal_dir).exists()


def test_bounded_precontact_refusal_is_exit_2_and_unconsumed(tmp_path):
    config, reader, recorder = _config(tmp_path, precontact_authorized=False)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_PRECONTACT_REFUSAL
    assert not outcome.authority_consumed
    assert reader.calls == []
    assert recorder.calls == []
    assert not Path(config.paths.execution_arming_path).exists()
    assert not Path(config.paths.execution_journal_dir).exists()


def test_atomic_authority_arming_uses_one_directory_rename(tmp_path):
    paths = _paths(tmp_path)
    recording = RecordingFs()
    result = runner.arm_authority(paths, recording.ops())
    assert result.authority_consumed
    assert not Path(paths.execution_arming_path).exists()
    assert Path(paths.execution_journal_dir).is_dir()
    assert (Path(paths.execution_journal_dir) / "current_state.json").is_file()
    assert json.loads((Path(paths.execution_journal_dir) / "current_state.json").read_text()) == runner.contact_armed_state()
    mkdirs = [entry for entry in recording.log if entry[0] == "mkdir"]
    renames = [entry for entry in recording.log if entry[0] == "rename"]
    assert mkdirs == [("mkdir", paths.execution_arming_path)]
    assert renames == [("rename", paths.execution_arming_path, paths.execution_journal_dir)]


def test_atomic_rename_failure_leaves_authority_unconsumed_and_no_journal(tmp_path):
    paths = _paths(tmp_path)
    recording = RecordingFs(fail_rename=True)
    with pytest.raises(runner.PreContactRefusal) as excinfo:
        runner.arm_authority(paths, recording.ops())
    assert excinfo.value.failure_code == runner.FAIL_CONTACT_ARM_PROMOTION
    assert Path(paths.execution_arming_path).is_dir()
    assert not Path(paths.execution_journal_dir).exists()
    assert [entry for entry in recording.log if entry[0] == "rename"] == [
        ("rename", paths.execution_arming_path, paths.execution_journal_dir)
    ]


def test_atomic_source_has_no_multi_operation_promotion_primitives():
    source = (HERE / "run_independent_order_sensitive_synthetic_validation_v0_2.py").read_text(encoding="utf-8")
    assert "shutil" not in source
    assert ".copy" not in source
    assert "copytree" not in source
    assert "rmtree" not in source
    assert ".unlink" not in source
    assert ".remove" not in source


def test_manifest_contact_attempt_is_durable_before_reader_runs(tmp_path):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)
    observed_state_inside_reader = {}

    def read_manifest(pass_index):
        observed_state_inside_reader.update(
            json.loads((Path(paths.execution_journal_dir) / "current_state.json").read_text())
        )
        return _manifest_bytes()

    state = runner.contact_armed_state()
    manifest_bytes, state = runner.read_manifest_with_accounting(
        paths.execution_journal_dir,
        state,
        1,
        read_manifest,
    )
    assert manifest_bytes
    assert observed_state_inside_reader["manifest_contact_attempt_count"] == 1
    assert observed_state_inside_reader["manifest_read_success_count"] == 0
    assert state["manifest_read_success_count"] == 1


def test_manifest_read_failure_after_consumption_retains_attempt_count(tmp_path):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)

    def failing_reader(pass_index):
        raise OSError("read failed")

    with pytest.raises(runner.ConsumedInfrastructureFailure):
        runner.read_manifest_with_accounting(
            paths.execution_journal_dir,
            runner.contact_armed_state(),
            1,
            failing_reader,
        )
    state = json.loads((Path(paths.execution_journal_dir) / "current_state.json").read_text())
    assert state["manifest_contact_attempt_count"] == 1
    assert state["manifest_read_success_count"] == 0


def test_third_manifest_contact_attempt_is_rejected_before_reader(tmp_path):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)
    state = runner.contact_armed_state()
    state["manifest_contact_attempt_count"] = 2
    state["manifest_read_success_count"] = 2
    called = []

    def reader(pass_index):
        called.append(pass_index)
        return _manifest_bytes()

    with pytest.raises(runner.ConsumedInfrastructureFailure):
        runner.read_manifest_with_accounting(paths.execution_journal_dir, state, 3, reader)
    assert called == []


def test_two_pass_validation_uses_fresh_bytes_validation_descriptor_outputs_and_bundles(tmp_path, monkeypatch):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)
    reader = ManifestReader(_manifest_bytes())
    recorder = DescriptorRecorder()
    validation_ids = []
    original_validate = schema.validate_manifest_payload

    def recording_validate(manifest):
        validation_ids.append((
            id(manifest),
            id(manifest["fixed_fixture"]),
            id(manifest["accepted_fixtures"]),
        ))
        return original_validate(manifest)

    monkeypatch.setattr(schema, "validate_manifest_payload", recording_validate)
    config = runner.BoundedRunConfig(
        paths=paths,
        read_manifest_bytes=reader,
        descriptor_callable=recorder,
        repository_state=_repo_state(),
    )
    bundle, state = runner.run_two_pass_validation(paths.execution_journal_dir, runner.contact_armed_state(), config)
    assert state["manifest_contact_attempt_count"] == 2
    assert state["manifest_read_success_count"] == 2
    assert len(reader.returned) == 2
    assert id(reader.returned[0]) != id(reader.returned[1])
    assert len(validation_ids) == 2
    assert validation_ids[0][0] != validation_ids[1][0]
    assert validation_ids[0][1] != validation_ids[1][1]
    assert validation_ids[0][2] != validation_ids[1][2]
    assert len({id(output) for output in recorder.outputs}) == len(recorder.outputs)
    assert bundle["scientific_result_kind"] == runner.RESULT_KIND_PASSED


def test_pass_two_is_skipped_when_pass_one_fails_before_science(tmp_path):
    manifest = make_manifest()
    manifest["fixed_fixture"].pop(schema.FIXED_MEMBER_BINARY_KEYS[0])
    _rehash_manifest(manifest)
    config, reader, recorder = _config(tmp_path, manifest)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONTROLLED_INVALID
    assert reader.calls == [1]
    assert recorder.calls == []
    assert not Path(config.paths.final_publication_dir).exists()


def test_successful_bounded_run_publishes_pass_bundle_and_terminal_evidence(tmp_path):
    config, reader, recorder = _config(tmp_path)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_PUBLISHED_PASS
    assert outcome.scientific_result_kind == runner.RESULT_KIND_PASSED
    assert outcome.terminal_evidence_written
    assert Path(config.paths.final_publication_dir).is_dir()
    assert tuple(sorted(os.listdir(config.paths.final_publication_dir))) == tuple(sorted(runner.SCIENTIFIC_FILE_SET))
    payload = _read_terminal_payload(config.paths.execution_journal_dir)
    assert payload["scientific_result_kind"] == runner.RESULT_KIND_PASSED
    assert payload["final_publication_available"] is True
    assert reader.calls == [1, 2]
    assert recorder.calls


def test_real_descriptor_distinguishes_fixed_positive_by_exact_signature():
    fixed = make_fixed_fixture()
    left = fixed[schema.FIXED_MEMBER_BINARY_KEYS[0]]
    right = fixed[schema.FIXED_MEMBER_BINARY_KEYS[1]]
    left_signature = descriptor.affine_plus_complement_signature(left)
    right_signature = descriptor.affine_plus_complement_signature(right)
    assert isinstance(left_signature[0], int)
    assert len(left_signature[1]) == descriptor.ENTRY_COUNT
    assert left_signature != right_signature
    assert runner._distinguished_by_signature(
        runner.default_descriptor_callable,
        left,
        right,
        "fixed_positive_regression",
    )


def test_raw_binary_inequality_is_not_scientific_distinction():
    manifest = make_manifest()
    first = manifest["accepted_fixtures"][0]
    transformed = runner._affine_transform_vector(
        first[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]],
        3,
        5,
    )
    assert schema.binary_key(first[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]]) != schema.binary_key(transformed)
    assert not runner._distinguished_by_signature(
        runner.default_descriptor_callable,
        first[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]],
        transformed,
        "raw_key_regression",
    )


def test_gate_does_not_depend_on_canonical_sha256(monkeypatch):
    def forbidden(_vector):
        raise AssertionError("canonical_sha256 must remain transport-only")

    monkeypatch.setattr(descriptor, "canonical_sha256", forbidden)
    bundle = runner._evaluate_scientific_bundle(
        make_manifest(),
        runner.BoundedRunConfig(
            paths=_paths(Path(os.environ.get("TEMP", ".")) / "unused"),
            read_manifest_bytes=lambda _pass: _manifest_bytes(),
            repository_state=_repo_state(),
            descriptor_callable=runner.default_descriptor_callable,
        ),
    )
    assert bundle["scientific_result_kind"] == runner.RESULT_KIND_PASSED


def test_malformed_and_degenerate_controls_use_real_descriptor_results():
    controls = runner._evaluate_malformed_and_degenerate_controls(descriptor.descriptor_result)
    assert controls["correct"] is True
    expected = {
        "wrong_length_below": "INPUT_LENGTH_INVALID",
        "wrong_length_above": "INPUT_LENGTH_INVALID",
        "non_integer_entry": "INPUT_ELEMENT_TYPE_INVALID",
        "bool_entry": "INPUT_ELEMENT_TYPE_INVALID",
        "negative_entry": "INPUT_BINARY_DOMAIN_INVALID",
        "greater_than_one_entry": "INPUT_BINARY_DOMAIN_INVALID",
        "all_zero_sequence": "DEGENERATE_SEQUENCE",
        "all_one_sequence": "DEGENERATE_SEQUENCE",
    }
    assert {
        case["case"]: case["observed_failure_code"]
        for case in controls["cases"]
    } == expected


def test_control_success_is_not_hardcoded_true():
    def bad_descriptor_result(_vector):
        return {
            "validation": {
                "valid": True,
                "failure_code": None,
                "failure_stage": None,
                "detail": None,
            }
        }

    config = runner.BoundedRunConfig(
        paths=_paths(Path(os.environ.get("TEMP", ".")) / "unused-hardcoded"),
        read_manifest_bytes=lambda _pass: _manifest_bytes(),
        repository_state=_repo_state(),
        descriptor_callable=runner.default_descriptor_callable,
        descriptor_result_callable=bad_descriptor_result,
    )
    bundle = runner._evaluate_scientific_bundle(make_manifest(), config)
    assert bundle["controls"]["malformed_and_degenerate_controls_correct"] is False
    assert bundle["scientific_result_kind"] == runner.RESULT_KIND_FAILED


def test_identity_controls_use_raw_affine_and_affine_plus_real_signatures():
    manifest = make_manifest()
    vectors = [
        manifest["fixed_fixture"][schema.FIXED_MEMBER_BINARY_KEYS[0]],
        manifest["fixed_fixture"][schema.FIXED_MEMBER_BINARY_KEYS[1]],
    ]
    config = runner.BoundedRunConfig(
        paths=_paths(Path(os.environ.get("TEMP", ".")) / "unused-identity"),
        read_manifest_bytes=lambda _pass: _manifest_bytes(),
        repository_state=_repo_state(),
        descriptor_callable=runner.default_descriptor_callable,
    )
    controls = runner._evaluate_identity_controls(config, vectors)
    assert controls["correct"] is True
    assert all(controls["cases"].values())


def test_method_b_full_nuisance_enumeration_uses_real_descriptor_counts():
    config = runner.BoundedRunConfig(
        paths=_paths(Path(os.environ.get("TEMP", ".")) / "unused-method-b"),
        read_manifest_bytes=lambda _pass: _manifest_bytes(),
        repository_state=_repo_state(),
        descriptor_callable=runner.default_descriptor_callable,
    )
    controls = runner._evaluate_method_b_nuisance_controls(config)
    assert controls["correct"] is True
    assert controls["counts"]["rotations"] == 64
    assert controls["counts"]["affine_transforms"] == 2048
    assert controls["counts"]["affine_plus_complement_transforms"] == 4096
    assert controls["method_b_full_enumeration"] is True
    assert controls["sampling_used"] is False


def test_nuisance_equivalent_vectors_have_equal_exact_signatures_across_full_orbits():
    base = runner._method_b_control_vector()
    cache = {}

    def exact_signature(vector):
        key = tuple(vector)
        if key not in cache:
            cache[key] = descriptor.affine_plus_complement_signature(list(vector))
        return cache[key]

    base_signature = exact_signature(base)
    for shift in range(schema.N):
        assert exact_signature(runner._rotate_vector(base, shift)) == base_signature
    for unit in runner._units_mod_n():
        for shift in range(schema.N):
            affine = runner._affine_transform_vector(base, unit, shift)
            assert exact_signature(affine) == base_signature
            assert exact_signature(runner._complement_vector(affine)) == base_signature
    assert len(cache) == 2


def test_nuisance_controls_do_not_use_manifest_lower_order_metadata():
    manifest = make_manifest()
    manifest["fixed_fixture"]["A2_H1"] = _simple_a2(41)
    manifest["accepted_fixtures"][0]["transition_table_B"] = _simple_transition_table(42)
    _rehash_manifest(manifest)
    assert schema.validate_manifest_payload(manifest).valid
    config = runner.BoundedRunConfig(
        paths=_paths(Path(os.environ.get("TEMP", ".")) / "unused-metadata"),
        read_manifest_bytes=lambda _pass: _manifest_bytes(manifest),
        repository_state=_repo_state(),
        descriptor_callable=runner.default_descriptor_callable,
    )
    bundle = runner._evaluate_scientific_bundle(manifest, config)
    assert bundle["controls"]["nuisance_controls_correct"] is True
    assert bundle["scientific_result_kind"] == runner.RESULT_KIND_PASSED


def _make_first_accepted_pair_affine_equivalent(manifest):
    fixture = manifest["accepted_fixtures"][0]
    transformed = runner._affine_transform_vector(
        fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]],
        3,
        5,
    )
    if transformed == fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]]:
        transformed = runner._affine_transform_vector(
            fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]],
            5,
            7,
        )
    support_b = schema.binary_to_support(transformed)
    key_a = schema.binary_key(fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]])
    key_b = schema.binary_key(transformed)
    fixture["support_B"] = support_b
    fixture[schema.ACCEPTED_MEMBER_BINARY_KEYS[1]] = transformed
    fixture["weight_B"] = schema.REQUIRED_WEIGHT
    fixture["member_orbit_key_B"] = key_b
    fixture["pair_duplicate_key"] = sorted([key_a, key_b])
    _rehash_manifest(manifest)


def test_seven_of_eight_accepted_pairs_is_scientific_fail_with_publication(tmp_path):
    manifest = make_manifest()
    _make_first_accepted_pair_affine_equivalent(manifest)
    assert schema.validate_manifest_payload(manifest).valid
    first = manifest["accepted_fixtures"][0]
    assert (
        descriptor.affine_plus_complement_signature(first[schema.ACCEPTED_MEMBER_BINARY_KEYS[0]])
        == descriptor.affine_plus_complement_signature(first[schema.ACCEPTED_MEMBER_BINARY_KEYS[1]])
    )
    config, reader, recorder = _config(tmp_path, manifest)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_PUBLISHED_FAIL
    assert outcome.scientific_result_kind == runner.RESULT_KIND_FAILED
    result_payload = json.loads(
        (Path(config.paths.final_publication_dir) / runner.RESULT_FILE_NAME).read_text()
    )
    assert result_payload["result_kind"] == runner.RESULT_KIND_FAILED


def test_controlled_schema_invalid_routes_to_exit_3_with_no_scientific_bundle(tmp_path):
    manifest = make_manifest()
    manifest["fixed_fixture"].pop(schema.FIXED_MEMBER_BINARY_KEYS[0])
    _rehash_manifest(manifest)
    config, reader, recorder = _config(tmp_path, manifest)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONTROLLED_INVALID
    assert outcome.controlled_outcome_kind == runner.CONTROLLED_KIND_INVALID
    assert not outcome.scientific_evaluation_reached
    assert not outcome.descriptor_evaluation_reached
    assert not Path(config.paths.final_publication_dir).exists()
    payload = _read_terminal_payload(config.paths.execution_journal_dir)
    assert payload["terminal_status"] == runner.TERMINAL_STATUS_INVALID_POST_CONTACT
    assert payload["controlled_outcome_available"] is True
    assert payload["scientific_result_available"] is False
    assert payload["scientific_result_kind"] is None


def test_controlled_identity_invalid_routes_to_exit_3(tmp_path):
    config, reader, recorder = _config(
        tmp_path,
        expected_external_manifest_sha256="0" * 64,
    )
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONTROLLED_INVALID
    assert outcome.failure_code == runner.FAIL_POSTCONTACT_IDENTITY_INVALID
    assert reader.calls == [1]
    assert recorder.calls == []


def test_manifest_read_failure_after_consumption_routes_to_exit_4(tmp_path):
    paths = _paths(tmp_path)
    reader = ManifestReader(_manifest_bytes(), fail_on={1})
    config = runner.BoundedRunConfig(
        paths=paths,
        read_manifest_bytes=reader,
        descriptor_callable=DescriptorRecorder(),
        repository_state=_repo_state(),
    )
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONSUMED_INFRASTRUCTURE_FAILURE
    assert outcome.failure_code == runner.FAIL_MANIFEST_READ_AFTER_CONSUMPTION
    assert outcome.authority_consumed
    state = outcome.last_verified_durable_state
    assert state["manifest_contact_attempt_count"] == 1
    assert state["manifest_read_success_count"] == 0


def test_postcontact_implementation_exception_routes_to_exit_4(tmp_path, monkeypatch):
    config, reader, recorder = _config(tmp_path)

    def broken_payload_hash(manifest):
        raise RuntimeError("synthetic implementation failure")

    monkeypatch.setattr(schema, "manifest_payload_sha256", broken_payload_hash)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONSUMED_INFRASTRUCTURE_FAILURE
    assert outcome.failure_code == runner.FAIL_POSTCONTACT_IMPLEMENTATION_EXCEPTION


def test_scientific_evaluation_exception_routes_to_exit_4(tmp_path):
    config, reader, recorder = _config(
        tmp_path,
        descriptor_callable=DescriptorRecorder(fail=True),
    )
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONSUMED_INFRASTRUCTURE_FAILURE
    assert outcome.failure_code == runner.FAIL_SCIENTIFIC_EVALUATION_EXCEPTION


@pytest.mark.parametrize(
    "flag, expected_code",
    [
        ("simulate_result_construction_failure", runner.FAIL_RESULT_CONSTRUCTION),
        ("simulate_staging_write_failure", runner.FAIL_STAGING_WRITE),
        ("simulate_staging_verification_failure", runner.FAIL_STAGING_VERIFICATION),
        ("simulate_promotion_failure", runner.FAIL_PROMOTION),
        ("simulate_final_verification_failure", runner.FAIL_FINAL_VERIFICATION),
    ],
)
def test_publication_failure_routes_to_exit_5(tmp_path, flag, expected_code):
    kwargs = {flag: True}
    config, reader, recorder = _config(tmp_path, **kwargs)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONSUMED_PUBLICATION_FAILURE
    assert outcome.failure_code == expected_code
    assert outcome.authority_consumed


def test_evidence_update_failure_after_consumption_uses_bounded_fallback(tmp_path):
    manifest = make_manifest()
    manifest["fixed_fixture"].pop(schema.FIXED_MEMBER_BINARY_KEYS[0])
    _rehash_manifest(manifest)
    config, reader, recorder = _config(
        tmp_path,
        manifest,
        simulate_terminal_evidence_failure=True,
    )
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONSUMED_INFRASTRUCTURE_FAILURE
    assert outcome.failure_code == runner.FAIL_EVIDENCE_UPDATE_AFTER_CONSUMPTION
    assert outcome.terminal_evidence_written is False
    assert b"EVIDENCE_UPDATE_FAILED_AFTER_CONSUMPTION" in outcome.stderr
    assert b"Traceback" not in outcome.stderr
    assert outcome.last_verified_durable_state["authority_consumed"] is True


def test_no_post_consumption_outcome_uses_unauthorized_execution(tmp_path):
    manifest = make_manifest()
    manifest["fixed_fixture"].pop(schema.FIXED_MEMBER_BINARY_KEYS[0])
    _rehash_manifest(manifest)
    config, reader, recorder = _config(tmp_path, manifest)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONTROLLED_INVALID
    payload = _read_terminal_payload(config.paths.execution_journal_dir)
    serialized = schema.canonical_json_bytes(payload)
    assert b"UNAUTHORIZED_EXECUTION" not in serialized
    assert b"UNAUTHORIZED_EXECUTION" not in outcome.stderr


def test_current_state_atomic_replacement_and_terminal_evidence_exclusive_once(tmp_path):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)
    state = runner._replace_state_phase(
        paths.execution_journal_dir,
        runner.contact_armed_state(),
        "MANIFEST_VALIDATING_PASS_1",
        runner.FileSystemOps(),
    )
    persisted = json.loads((Path(paths.execution_journal_dir) / "current_state.json").read_text())
    assert persisted == state
    payload = runner._terminal_payload(
        state,
        _repo_state(),
        runner.TERMINAL_STATUS_INVALID_POST_CONTACT,
        "controlled_invalidity",
        runner.FAIL_POSTCONTACT_SCHEMA_INVALID,
        "post_contact_validation",
        runner.EXIT_CONTROLLED_INVALID,
        True,
        runner.CONTROLLED_KIND_INVALID,
        False,
        None,
        False,
        False,
        False,
        "NO_SCIENTIFIC_PUBLICATION_OPERATIONAL_EVIDENCE_RETAINED",
        "NOT_CREATED",
        "2026-07-22T00:00:00Z",
    )
    runner._write_terminal_evidence(paths.execution_journal_dir, payload, runner.FileSystemOps(), state)
    with pytest.raises(runner.EvidenceUpdateFailedAfterConsumption):
        runner._write_terminal_evidence(paths.execution_journal_dir, payload, runner.FileSystemOps(), state)


def test_terminal_evidence_wrapper_uses_payload_only_sha256(tmp_path):
    paths = _paths(tmp_path)
    runner.arm_authority(paths)
    state = runner.contact_armed_state()
    payload = runner._terminal_payload(
        state,
        _repo_state(),
        runner.TERMINAL_STATUS_COMPLETE,
        None,
        None,
        None,
        runner.EXIT_PUBLISHED_PASS,
        False,
        None,
        True,
        runner.RESULT_KIND_PASSED,
        True,
        True,
        True,
        "PUBLISHED",
        "PROMOTED",
        "2026-07-22T00:00:00Z",
    )
    runner._write_terminal_evidence(paths.execution_journal_dir, payload, runner.FileSystemOps(), state)
    wrapper = json.loads((Path(paths.execution_journal_dir) / "terminal_evidence.json").read_text())
    assert tuple(wrapper.keys()) == ("payload", "payload_sha256")
    assert wrapper["payload_sha256"] == schema.sha256_hex(schema.canonical_json_bytes(payload))
    assert wrapper["payload_sha256"] != schema.sha256_hex(schema.canonical_json_bytes(wrapper))


def test_direct_publication_writes_exact_three_file_bundle_and_refuses_existing_destination(tmp_path):
    paths = _paths(tmp_path)
    pass_bundle = {
        "schema": "torment-brainvision-synthetic-validation-pass-bundle-v0.2",
        "scientific_result_kind": runner.RESULT_KIND_PASSED,
    }
    artifacts = runner._result_artifacts(
        runner.RESULT_KIND_PASSED,
        pass_bundle,
        runner.contact_armed_state(),
        _repo_state(),
    )
    runner.publish_scientific_artifacts(paths, artifacts)
    assert tuple(sorted(os.listdir(paths.final_publication_dir))) == tuple(sorted(runner.SCIENTIFIC_FILE_SET))
    second_paths = _paths(tmp_path / "second")
    Path(second_paths.final_publication_dir).mkdir(parents=True)
    Path(second_paths.scientific_result_staging_dir).parent.mkdir(parents=True, exist_ok=True)
    with pytest.raises(runner.PublicationFailure) as excinfo:
        runner.publish_scientific_artifacts(second_paths, artifacts)
    assert excinfo.value.failure_code == runner.FAIL_PROMOTION


def test_controlled_invalid_produces_no_scientific_publication_bundle(tmp_path):
    manifest = make_manifest()
    manifest["configuration_identity"]["configuration_sha256"] = "0" * 64
    _rehash_manifest(manifest)
    config, reader, recorder = _config(tmp_path, manifest)
    outcome = runner.run_bounded_validation(config)
    assert outcome.exit_code == runner.EXIT_CONTROLLED_INVALID
    assert not Path(config.paths.scientific_result_staging_dir).exists()
    assert not Path(config.paths.final_publication_dir).exists()


def test_runner_defines_no_competing_fixture_key_constants_or_aliases():
    source_path = HERE / "run_independent_order_sensitive_synthetic_validation_v0_2.py"
    source = source_path.read_text(encoding="utf-8")
    assert "binary_H0" not in source
    assert "binary_H1" not in source
    assert "binary_A" not in source
    assert "binary_B" not in source


def test_v0_1_validation_and_production_boundaries_are_absent_from_new_sources():
    combined = "\n".join(
        (HERE / name).read_text(encoding="utf-8")
        for name in (
            "independent_order_sensitive_synthetic_validation_schema_contract_v0_2.py",
            "run_independent_order_sensitive_synthetic_validation_v0_2.py",
            "test_independent_order_sensitive_synthetic_fixtures_v0_2.py",
        )
    )
    forbidden = [
        "run_independent_order_sensitive_synthetic_validation_" + "v0_1.py",
        "test_independent_order_sensitive_synthetic_fixtures_" + "v0_1.py",
        "torment_" + "service",
        "Psi" + "TRS",
        "pre" + "recorded",
    ]
    for token in forbidden:
        assert token not in combined


def _validate_injected_git_status_change_set(status_text: str):
    observed = set()
    rejected = []
    for raw_line in status_text.splitlines():
        line = raw_line.rstrip()
        if not line or line.startswith("## "):
            continue
        path = line[3:].replace("\\", "/")
        status = line[:2]
        if path in THREE_AUTHORIZED_FILES and status.strip() in {"?", "??", "M"}:
            observed.add(path)
        else:
            rejected.append(raw_line)
    return observed == THREE_AUTHORIZED_FILES and not rejected


def test_change_set_validator_accepts_exact_three_file_status():
    status_text = "\n".join(
        ["## main...origin/main"] +
        ["?? %s" % path for path in sorted(THREE_AUTHORIZED_FILES)]
    )
    assert _validate_injected_git_status_change_set(status_text)


def test_change_set_validator_rejects_extra_fourth_file():
    status_text = "\n".join(
        ["?? %s" % path for path in sorted(THREE_AUTHORIZED_FILES)] +
        ["?? research/brainvision/extra_helper.py"]
    )
    assert not _validate_injected_git_status_change_set(status_text)


def test_change_set_validator_rejects_frozen_or_production_file():
    frozen_status = "\n".join(
        ["?? %s" % path for path in sorted(THREE_AUTHORIZED_FILES)] +
        [" M research/brainvision/independent_order_sensitive_descriptor_v0_1.py"]
    )
    production_status = "\n".join(
        ["?? %s" % path for path in sorted(THREE_AUTHORIZED_FILES)] +
        [" M " + "torment_" + "service/kernel/live.py"]
    )
    assert not _validate_injected_git_status_change_set(frozen_status)
    assert not _validate_injected_git_status_change_set(production_status)


def test_descriptor_module_still_imports_and_accepts_raw_binary_sequence():
    result = descriptor.descriptor_result(make_fixed_fixture()[schema.FIXED_MEMBER_BINARY_KEYS[0]])
    assert result["validation"]["valid"] is True
