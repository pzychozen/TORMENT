"""Focused Track J regressions for shared-kernel character overrides."""

from __future__ import annotations

import copy
import threading
from typing import Dict

import numpy as np

from torment_service.embeddings import HashEmbedding
from torment_service.kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel
from torment_service.memory_kernel import TriOctaMemoryKernel


def _isolated_character_step(
    text: str, *, g_mod: float, theta_lock_mod: float,
) -> np.ndarray:
    kernel = TriOctaMemoryKernel(embedder=HashEmbedding())
    state = kernel.init_state(
        text,
        character_modulation={
            "g_mod": g_mod,
            "theta_lock_mod": theta_lock_mod,
        },
    )
    state, _, _ = kernel.process(state, text)
    return np.asarray(state.Omega, dtype=np.complex128).copy()


def test_raw_step_default_overrides_preserve_existing_behavior() -> None:
    params = ModelParams()
    Omega = np.array(
        [0.6 + 0.1j, -0.2 + 0.5j, 0.3 - 0.4j],
        dtype=np.complex128,
    )
    state_default = ModelState(Omega=Omega.copy())
    state_explicit = copy.deepcopy(state_default)
    model_default = TriOctaPhaseLockModel(params)
    model_explicit = TriOctaPhaseLockModel(params)

    model_default.step(state_default, dt=params.eps)
    model_explicit.step(
        state_explicit,
        dt=params.eps,
        g_override=params.g,
        theta_lock_override=params.theta_lock,
    )

    np.testing.assert_allclose(state_default.Omega, state_explicit.Omega)
    np.testing.assert_allclose(state_default.Z_vec, state_explicit.Z_vec)
    assert state_default.z == state_explicit.z
    assert state_default.phi_index == state_explicit.phi_index
    assert state_default.cycle_stage == state_explicit.cycle_stage
    assert state_default.identity_state == state_explicit.identity_state


def test_character_parameter_overrides_remain_local_during_forced_overlap() -> None:
    kernel = TriOctaMemoryKernel(embedder=HashEmbedding())
    default_g = float(kernel.params.g)
    default_theta_lock = float(kernel.params.theta_lock)
    mod_by_label = {
        "a": {"g_mod": 0.17, "theta_lock_mod": 0.10},
        "b": {"g_mod": 0.23, "theta_lock_mod": 0.40},
    }
    state_by_label = {
        label: kernel.init_state(
            f"concurrent:{label}",
            character_modulation=mod,
        )
        for label, mod in mod_by_label.items()
    }
    label_by_state_id = {
        id(state): label for label, state in state_by_label.items()
    }
    expected = {
        label: _isolated_character_step(f"concurrent:{label}", **mod)
        for label, mod in mod_by_label.items()
    }

    phase_barrier = threading.Barrier(2)
    original_phase_lock_step = kernel.model.phase_lock_step
    original_update_z = kernel.model.update_z
    observed: Dict[str, Dict[str, float | None]] = {}
    errors: Dict[str, BaseException] = {}

    def wrapped_phase_lock_step(
        state: ModelState, *, g_override: float | None = None,
    ) -> None:
        label = label_by_state_id[id(state)]
        observed.setdefault(label, {})["g_override"] = g_override
        observed[label]["shared_g"] = float(kernel.params.g)
        phase_barrier.wait(timeout=5)
        original_phase_lock_step(state, g_override=g_override)

    def wrapped_update_z(
        state: ModelState, *, theta_lock_override: float | None = None,
    ) -> None:
        label = label_by_state_id[id(state)]
        observed.setdefault(label, {})["theta_lock_override"] = theta_lock_override
        observed[label]["shared_theta_lock"] = float(kernel.params.theta_lock)
        original_update_z(state, theta_lock_override=theta_lock_override)

    kernel.model.phase_lock_step = wrapped_phase_lock_step  # type: ignore[method-assign]
    kernel.model.update_z = wrapped_update_z  # type: ignore[method-assign]

    def run(label: str) -> None:
        try:
            kernel.process(state_by_label[label], f"concurrent:{label}")
        except BaseException as exc:  # pragma: no cover - asserted below
            errors[label] = exc

    threads = [
        threading.Thread(target=run, args=(label,), daemon=True)
        for label in ("a", "b")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not any(thread.is_alive() for thread in threads)
    assert errors == {}
    for label, mod in mod_by_label.items():
        assert observed[label] == {
            "g_override": mod["g_mod"],
            "shared_g": default_g,
            "theta_lock_override": mod["theta_lock_mod"],
            "shared_theta_lock": default_theta_lock,
        }
        np.testing.assert_allclose(state_by_label[label].Omega, expected[label])

    assert kernel.params.g == default_g
    assert kernel.params.theta_lock == default_theta_lock
