from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import sys

import durable_evidence_schema_v0_3 as schema

from test_durable_evidence_publication_v0_3 import (
    PUBLICATION_AUTHORITY,
    PositiveTmpPromotionAdapter,
    project,
)


HERE = Path(__file__).resolve().parent
J1_MODULE = "durable_evidence_publication_v0_3"

FORBIDDEN_IMPORT_PREFIXES = (
    "torment_service",
    "independent_order_sensitive_descriptor_v0_1",
    "independent_order_sensitive_synthetic_fixture_freeze_v0_1",
    "independent_order_sensitive_synthetic_fixture_verifier_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_2",
    "psi_trs",
    "durable_evidence_scientific_result_v0_3",
)

FORBIDDEN_SOURCE_TOKENS = (
    "torment_service",
    "psi_trs",
    "manifest_reader",
    "frozen_manifest",
    "fixture_loader",
    "run_independent_order_sensitive",
    "__import__",
    "importlib",
    "subprocess",
    "current_state.json",
)

FORBIDDEN_CALLABLE_TOKENS = (
    "manifest",
    "descriptor",
    "psitrs",
    "scientific_runner",
    "completion_writer",
    "retry",
    "callback",
)


def _imports_for_module(module_name: str):
    tree = ast.parse((HERE / ("%s.py" % module_name)).read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


def _local_import_closure(module_name: str):
    visited = set()
    stack = [module_name]
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for imported in _imports_for_module(current):
            if imported.startswith("durable_evidence_") and imported not in visited:
                stack.append(imported)
    return visited


def test_j1_direct_imports_do_not_reach_science_manifest_or_kernel_surfaces():
    for imported in _imports_for_module(J1_MODULE):
        assert not any(
            imported == forbidden or imported.startswith(forbidden + ".")
            for forbidden in FORBIDDEN_IMPORT_PREFIXES
        ), imported


def test_j1_transitive_local_imports_stay_on_publication_substrate():
    closure = _local_import_closure(J1_MODULE)
    assert "durable_evidence_scientific_result_v0_3" not in closure
    assert "durable_evidence_authority_v0_3" not in closure
    assert "durable_evidence_publication_recovery_v0_3" not in closure
    assert closure <= {
        "durable_evidence_publication_v0_3",
        "durable_evidence_primary_writer_v0_3",
        "durable_evidence_schema_v0_3",
        "durable_evidence_windows_adapter_v0_3",
    }


def test_j1_callable_surface_exposes_no_science_or_retry_entrypoints():
    module = importlib.import_module(J1_MODULE)
    for name, value in vars(module).items():
        if name.startswith("_") or not callable(value):
            continue
        lowered = name.lower()
        assert not any(token in lowered for token in FORBIDDEN_CALLABLE_TOKENS), name


def test_j1_source_contains_no_forbidden_science_or_dynamic_import_tokens():
    source = (HERE / ("%s.py" % J1_MODULE)).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source


def test_j1_isolated_import_has_no_forbidden_transitive_modules():
    script = (
        "import importlib, sys\n"
        "importlib.import_module(%r)\n"
        "for name in sys.modules:\n"
        "    if name.startswith(%r):\n"
        "        raise SystemExit(name)\n"
        "print('imported')\n"
    ) % (J1_MODULE, FORBIDDEN_IMPORT_PREFIXES)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(HERE),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert completed.stdout.strip() == b"imported"


def test_j1_path_ownership_is_limited_to_publication_namespaces(tmp_path):
    result, _, _ = project(
        tmp_path,
        publication_authority=PUBLICATION_AUTHORITY,
        promotion_adapter=PositiveTmpPromotionAdapter(tmp_path),
    )
    assert result.classification == "PUBLICATION_COMPLETED"
    root = tmp_path.resolve()
    for path in (
        result.paths.chain_directory,
        result.paths.final_directory,
    ):
        path.resolve().relative_to(root)
    assert result.paths.chain_directory.parts[-2] == (
        ".iososv_v0_3.publication_chain"
    )
    assert result.paths.final_directory.parts[-2] == "iososv_v0_3.publication"
    assert result.paths.chain_directory.name == result.publication_chain_identity
    assert result.paths.final_directory.name == result.publication_chain_identity
    assert not (Path("research") / "brainvision" / "results").resolve() in (
        item.resolve() for item in tmp_path.rglob("*")
    )
    assert set(item.name for item in result.paths.final_directory.iterdir()) == set(
        schema.PUBLICATION_ARTIFACT_FILENAMES
    )
