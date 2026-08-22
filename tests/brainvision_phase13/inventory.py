"""Deterministic content-hash inventory for a later Phase-13 authorization."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Final


PACKAGE_DIRECTORY: Final = Path(__file__).resolve().parent
REPOSITORY_ROOT: Final = PACKAGE_DIRECTORY.parents[1]
_INVENTORY_PATHS: Final[tuple[str, ...]] = (
    "docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md",
    "docs/TORMENT_BRAINVISION_PHASE_13_FORMAL_ADMINISTRATION_BINDINGS_v1.0.md",
    "docs/TORMENT_BRAINVISION_PHASE_13_INSTRUMENT_AMENDMENT_1_EXTERNAL_AUTHORIZATION_ARTIFACT_v1.0.md",
    "docs/TORMENT_BRAINVISION_PHASE_13_CORRECTED_QUALIFICATION_INSTRUMENT_AMENDMENT_v1.0.md",
    "tests/test_brainvision_phase13_instrument.py",
    "tests/brainvision_phase13/__init__.py",
    "tests/brainvision_phase13/backend.py",
    "tests/brainvision_phase13/clock.py",
    "tests/brainvision_phase13/authority_clause_registry.json",
    "tests/brainvision_phase13/criterion_provenance_manifest.json",
    "tests/brainvision_phase13/evidence_obligations_manifest.json",
    "tests/brainvision_phase13/evidence.py",
    "tests/brainvision_phase13/fixtures.py",
    "tests/brainvision_phase13/grader.py",
    "tests/brainvision_phase13/inventory.py",
    "tests/brainvision_phase13/manifests.py",
    "tests/brainvision_phase13/orchestrator.py",
    "tests/brainvision_phase13/preflight.py",
    "tests/brainvision_phase13/qualification.py",
    "tests/brainvision_phase13/result_document.py",
    "tests/brainvision_phase13/run_qualification.py",
    "tests/brainvision_phase13/schemas.py",
    "tests/brainvision_phase13/fixture_manifest.json",
    "tests/brainvision_phase13/expected_result_manifest.json",
    "tests/brainvision_phase13/schedule_manifest.json",
    "tests/brainvision_phase13/authority_manifest.json",
)


def instrument_content_hash_inventory() -> dict[str, str]:
    """Return deterministic relative-path to SHA-256 source bindings only."""
    result: dict[str, str] = {}
    for relative_path in _INVENTORY_PATHS:
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        result[relative_path] = sha256(path.read_bytes()).hexdigest()
    return result


__all__ = ("instrument_content_hash_inventory",)
