from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import sys

from test_durable_evidence_publication_recovery_v0_3 import (
    run_recovery,
    setup_final_artifacts_with_incomplete_publication_chain,
)


HERE = Path(__file__).resolve().parent
J2_MODULE = "durable_evidence_publication_recovery_v0_3"

FORBIDDEN_DIRECT_IMPORTS = (
    "durable_evidence_publication_v0_3",
    "durable_evidence_windows_adapter_v0_3",
    "durable_evidence_scientific_result_v0_3",
    "durable_evidence_authority_v0_3",
    "torment_service",
    "independent_order_sensitive_descriptor_v0_1",
    "independent_order_sensitive_synthetic_fixture_freeze_v0_1",
    "independent_order_sensitive_synthetic_fixture_verifier_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_1",
    "run_independent_order_sensitive_synthetic_validation_v0_2",
    "psi_trs",
    "os",
    "shutil",
)

FORBIDDEN_TRANSITIVE_IMPORTS = (
    "durable_evidence_publication_v0_3",
    "durable_evidence_scientific_result_v0_3",
    "durable_evidence_authority_v0_3",
)

FORBIDDEN_SOURCE_TOKENS = (
    "durable_evidence_publication_v0_3",
    "SameVolumeNoReplacePromotionAdapter",
    "promote_verified_directory_no_replace",
    "shutil.copy",
    "shutil.copytree",
    "os.rename",
    "os.replace",
    ".write_bytes(",
    ".write_text(",
    ".unlink(",
    ".rename(",
    ".replace(",
    "__import__",
    "importlib",
    "subprocess",
    "manifest_reader",
    "fixture_loader",
    "psi_trs",
    "torment_service",
)

FORBIDDEN_CALLABLE_TOKENS = (
    "generate",
    "promote",
    "project_publication",
    "artifact_writer",
    "copy",
    "rename",
    "repair",
    "delete",
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


def test_j2_direct_imports_do_not_reach_projector_promotion_science_or_kernel():
    for imported in _imports_for_module(J2_MODULE):
        assert not any(
            imported == forbidden or imported.startswith(forbidden + ".")
            for forbidden in FORBIDDEN_DIRECT_IMPORTS
        ), imported


def test_j2_transitive_local_imports_exclude_projector_and_science_modules():
    closure = _local_import_closure(J2_MODULE)
    for forbidden in FORBIDDEN_TRANSITIVE_IMPORTS:
        assert forbidden not in closure
    assert "durable_evidence_publication_replay_v0_3" in closure
    assert "durable_evidence_primary_writer_v0_3" in closure


def test_j2_callable_surface_exposes_no_generation_mutation_or_retry_entrypoints():
    module = importlib.import_module(J2_MODULE)
    for name, value in vars(module).items():
        if name.startswith("_") or not callable(value):
            continue
        lowered = name.lower()
        assert not any(token in lowered for token in FORBIDDEN_CALLABLE_TOKENS), name


def test_j2_source_contains_no_artifact_mutation_or_dynamic_import_tokens():
    source = (HERE / ("%s.py" % J2_MODULE)).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source


def test_j2_isolated_import_has_no_projector_or_science_modules():
    script = (
        "import importlib, sys\n"
        "importlib.import_module(%r)\n"
        "for name in sys.modules:\n"
        "    if name.startswith(%r):\n"
        "        raise SystemExit(name)\n"
        "print('imported')\n"
    ) % (J2_MODULE, FORBIDDEN_TRANSITIVE_IMPORTS)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(HERE),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    assert completed.stdout.strip() == b"imported"


def test_j2_path_ownership_writes_only_recovery_chain(tmp_path):
    publication_result, bundle_payload, completion = (
        setup_final_artifacts_with_incomplete_publication_chain(tmp_path)
    )
    before_final = {
        item.relative_to(publication_result.paths.final_directory).as_posix(): (
            item.read_bytes()
        )
        for item in publication_result.paths.final_directory.iterdir()
    }
    recovered = run_recovery(
        tmp_path, publication_result, bundle_payload, completion
    )
    assert recovered.classification == "PUBLICATION_RECOVERY_EVIDENCE_COMPLETED"
    assert recovered.paths.recovery_chain_directory.parts[-2] == (
        ".iososv_v0_3.publication_recovery_chain"
    )
    assert recovered.paths.recovery_chain_directory.name == (
        recovered.publication_recovery_chain_identity
    )
    assert recovered.paths.original_publication_chain_directory == (
        publication_result.paths.chain_directory
    )
    assert recovered.paths.final_publication_directory == (
        publication_result.paths.final_directory
    )
    after_final = {
        item.relative_to(publication_result.paths.final_directory).as_posix(): (
            item.read_bytes()
        )
        for item in publication_result.paths.final_directory.iterdir()
    }
    assert after_final == before_final
