from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent

SUBSTRATE_MODULES = (
    "durable_evidence_schema_v0_3",
    "durable_evidence_windows_adapter_v0_3",
    "durable_evidence_primary_writer_v0_3",
    "durable_evidence_replay_v0_3",
    "durable_evidence_durability_v0_3",
    "durable_evidence_authority_v0_3",
    "durable_evidence_scientific_result_v0_3",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "torment_service",
    "independent_order_sensitive_descriptor_v0_1",
    "independent_order_sensitive_synthetic_fixture_freeze_v0_1",
    "independent_order_sensitive_synthetic_fixture_verifier_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_2",
    "psi_trs",
    "subprocess",
)

FORBIDDEN_CALLABLE_TOKENS = (
    "manifest",
    "descriptor",
    "psitrs",
    "publish",
    "publication_project",
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


def test_new_substrate_direct_imports_do_not_reach_forbidden_surfaces():
    for module_name in SUBSTRATE_MODULES:
        for imported in _imports_for_module(module_name):
            assert not any(
                imported == forbidden or imported.startswith(forbidden + ".")
                for forbidden in FORBIDDEN_IMPORT_PREFIXES
            ), (module_name, imported)


def test_new_substrate_transitive_local_imports_stay_inside_substrate():
    visited = set()
    stack = list(SUBSTRATE_MODULES)
    while stack:
        module_name = stack.pop()
        if module_name in visited:
            continue
        visited.add(module_name)
        for imported in _imports_for_module(module_name):
            if imported.startswith("durable_evidence_") and imported not in visited:
                stack.append(imported)
    assert visited == set(SUBSTRATE_MODULES)


def test_importing_substrate_has_no_forbidden_transitive_modules():
    script = (
        "import importlib, sys\n"
        "mods = %r\n"
        "for name in mods:\n"
        "    importlib.import_module(name)\n"
        "for name in sys.modules:\n"
        "    if name.startswith(%r):\n"
        "        raise SystemExit(name)\n"
        "print('imported')\n"
    ) % (SUBSTRATE_MODULES, FORBIDDEN_IMPORT_PREFIXES)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(HERE),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert completed.stdout.strip() == b"imported"


def test_callable_surface_exposes_no_execution_manifest_descriptor_or_retry_entrypoints():
    for module_name in SUBSTRATE_MODULES:
        module = importlib.import_module(module_name)
        for name, value in vars(module).items():
            if name.startswith("_") or not callable(value):
                continue
            lowered = name.lower()
            assert not any(token in lowered for token in FORBIDDEN_CALLABLE_TOKENS), (
                module_name,
                name,
            )


def test_source_contains_no_mutable_authoritative_pointer_or_replace_transition():
    for module_name in SUBSTRATE_MODULES:
        source = (HERE / ("%s.py" % module_name)).read_text(encoding="utf-8")
        assert "os.replace" not in source
        assert ".replace(" not in source
        assert "current_state.json" not in source
        assert "__import__" not in source
        assert "importlib" not in source
        assert "subprocess" not in source
