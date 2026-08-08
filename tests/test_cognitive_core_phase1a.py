"""Phase 1a extraction proof for the TORMENT cognitive identity layer."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from torment_service.cognitive_core import CognitiveCore, CognitiveCoreState
from torment_service.embeddings import HashEmbedding
from torment_service.memory_kernel import TriOctaMemoryKernel


_EXPECTED_TRI_MOD_KEYS = {
    "write_mult",
    "proposal_mult",
    "bridge_p",
    "bridge_sim",
    "cycle_stage",
    "identity_state",
    "in_corridor",
    "survival_steps",
    "tearing_risk",
    "tangent_align",
    "align_ema",
    "disp",
    "coh_phase",
    "seed_v0",
    "seed_pos0",
}


_EXPECTED_DEBUG_KEYS = {
    "coherence",
    "z",
    "phase_disp",
    "coh_phase",
    "tri_mod",
    "summary",
    "coh_raw",
    "cycle_stage",
    "identity_state",
    "id_label",
    "S_mag",
    "phi_coll",
    "effective_disp_scale",
}


@pytest.mark.parametrize(
    "arm_label,character_modulation",
    [
        ("none", None),
        ("g_mod", {"g_mod": 0.17}),
        ("theta_lock_mod", {"theta_lock_mod": 0.10}),
        ("both", {"g_mod": 0.23, "theta_lock_mod": 0.40}),
    ],
)
def test_process_phase1a_cognitive_values_recur_independently(
    arm_label: str,
    character_modulation: dict[str, Any] | None,
) -> None:
    kernel = TriOctaMemoryKernel(embedder=HashEmbedding())
    state = kernel.init_state(
        "phase1a cognitive extraction seed",
        character_modulation=character_modulation,
    )
    runtime_ctx = kernel.new_runtime_context()
    ref_core = CognitiveCore()
    ref_cog = CognitiveCoreState()

    for step in range(1000):
        observation = (
            f"Phase 1a recurrent equality arm={arm_label} step={step}: "
            "kernel identity surface remains cognitive."
        )
        state, _, debug = kernel.process(state, observation, runtime_ctx)
        cog = runtime_ctx.cognitive_state
        char_mod = getattr(state, "_char_mod", {}) or {}
        theta_lock_override = (
            float(char_mod["theta_lock_mod"])
            if "theta_lock_mod" in char_mod
            else None
        )
        ref_core.update(
            ref_cog,
            state=state,
            params=kernel.params,
            theta_lock_override=theta_lock_override,
        )

        assert cog.z_mem == ref_cog.z_mem
        assert cog.z_identity == ref_cog.z_identity
        assert cog.identity_state == ref_cog.identity_state

        assert debug["z"] == cog.z_identity
        assert debug["identity_state"] == float(cog.identity_state)
        assert debug["tri_mod"]["identity_state"] == float(cog.identity_state)
        assert set(debug) == _EXPECTED_DEBUG_KEYS
        assert set(debug["tri_mod"]) == _EXPECTED_TRI_MOD_KEYS

        speed = 0.05 + 0.25 * float(debug["coherence"])
        sign_z = 1.0 if cog.z_identity >= 0 else -1.0
        assert debug["tri_mod"]["seed_v0"][2] == float(0.15 * sign_z * speed)


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add("." * node.level + (node.module or ""))
    return modules


def test_cognitive_and_model_core_source_boundary_contract() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cognitive_path = repo_root / "torment_service" / "cognitive_core.py"
    memory_kernel_path = repo_root / "torment_service" / "memory_kernel.py"
    model_path = repo_root / "torment_service" / "kernel" / "model_core.py"

    cognitive_src = cognitive_path.read_text(encoding="utf-8")
    memory_kernel_src = memory_kernel_path.read_text(encoding="utf-8")
    model_src = model_path.read_text(encoding="utf-8")

    assert "model_core" not in cognitive_src
    assert "cognitive_core" not in model_src
    assert "CognitiveCore" not in model_src
    assert "z_mem" not in model_src
    assert "z_mem" in cognitive_src
    assert "cognitive_state.z_mem =" not in memory_kernel_src

    cognitive_imports = _import_modules(cognitive_path)
    model_imports = _import_modules(model_path)
    assert "torment_service.kernel.model_core" not in cognitive_imports
    assert ".kernel.model_core" not in cognitive_imports
    assert "torment_service.cognitive_core" not in model_imports
    assert "..cognitive_core" not in model_imports
