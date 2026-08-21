"""Static Phase-11 architectural-isolation coverage."""

from __future__ import annotations

import ast
from dataclasses import fields
import inspect

import brainvision.ingress as ingress


def test_ingress_imports_only_brainvision_phase2_phase7_and_phase10_boundaries() -> None:
    tree = ast.parse(inspect.getsource(ingress))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    assert imported_modules <= {
        "__future__",
        "dataclasses",
        "brainvision.character_modulation",
        "brainvision.lifecycle",
        "brainvision.observation",
    }
    source = inspect.getsource(ingress)
    for forbidden in (
        "torment_service.fabric",
        "Fabric.ingest",
        "MemoryGraph",
        "memory_kernel",
        "CharacterSeed",
        "CharacterState",
        "CognitiveCore",
        "SRG",
        "Hivermind",
        "Spine",
        "evolve_vhe_state_as_of",
    ):
        assert forbidden not in source


def test_ingress_exposes_no_second_observation_contract_or_phase12_sink() -> None:
    assert ingress.__all__ == (
        "BrainvisionIngressError",
        "FirsthandVisualAdmissionReceipt",
        "admit_firsthand_visual_observation",
    )
    assert tuple(field.name for field in fields(ingress.FirsthandVisualAdmissionReceipt)) == (
        "observation_id",
        "source_sequence",
        "committed_active_time_ns",
    )
    source = inspect.getsource(ingress)
    assert "from_dict" not in source
    assert "json" not in source
    assert "sink" not in source.lower()
    assert "projection" not in source.lower()
