"""Phase 1b TrioOctagon oracle parity and runtime continuity tests."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from torment_service.embeddings import HashEmbedding
from torment_service.memory_kernel import TriOctaMemoryKernel
from torment_service.kernel import model_core as production_model_core


_REPO_ROOT = Path(__file__).resolve().parents[1]
_ORACLE_PATH = _REPO_ROOT / "tests" / "oracles" / "model_core_v4_0_original.py"
_KERNEL_DIR = _REPO_ROOT / "torment_service" / "kernel"
_ORACLE_METADATA_HEADER_LINES = (
    b"# Authoritative TrioOctagon behavioral oracle; must not be edited.",
    b"# Source md5 after CRLF-normalization: 05ba0d9c.",
)
_ORACLE_BODY_MD5_AFTER_LF_NORMALIZATION = "05ba0d9ca44841746cf3420b524acad1"
_LATCH_SEEDS = range(16)
_LATCH_STEPS_PER_SEED = 1200
_EXPECTED_SIGN_FLIPS_PER_SEED = 600


def _load_oracle_module():
    spec = importlib.util.spec_from_file_location(
        "tests.oracles.model_core_v4_0_original",
        _ORACLE_PATH,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(_KERNEL_DIR))
    try:
        assert spec.loader is not None
        spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(_KERNEL_DIR))
        except ValueError:
            pass
    return module


ORACLE = _load_oracle_module()


def test_v4_0_oracle_fixture_body_identity_guard() -> None:
    # The vendored fixture adds two metadata comments; the guarded hash covers
    # the original supplied oracle body after CRLF/LF normalization.
    raw = _ORACLE_PATH.read_bytes()
    lines = raw.splitlines(keepends=True)
    actual_header = tuple(line.rstrip(b"\r\n") for line in lines[:2])
    assert actual_header == _ORACLE_METADATA_HEADER_LINES

    body = b"".join(lines[2:])
    normalized_body = body.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    assert hashlib.md5(normalized_body).hexdigest() == _ORACLE_BODY_MD5_AFTER_LF_NORMALIZATION


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

_ARMS = [
    ("none", None),
    ("g_mod", {"g_mod": 0.17}),
    ("theta_lock_mod", {"theta_lock_mod": 0.10}),
    ("both", {"g_mod": 0.23, "theta_lock_mod": 0.40}),
]


class _SplicedReferenceModel(production_model_core.TriOctaPhaseLockModel):
    """Phase 1a in-kernel cognitive splice, kept test-local as a reference."""

    def update_z(
        self, state: production_model_core.ModelState, *, theta_lock_override: float | None = None,
    ) -> None:
        kappa = state.kappa()
        rho = kappa / (1.0 + kappa)  # 0..1 soft saturation

        theta = (2.0 * np.pi * state.phi_index) / float(self.p.d24_steps)
        lam = float(self.p.lambda_vp)
        theta_lock = float(
            self.p.theta_lock
            if theta_lock_override is None
            else theta_lock_override
        )

        z_inst = lam * rho * np.cos(3.0 * (theta - theta_lock))  # bounded in [-lam*rho, +lam*rho]

        O1, O2, O3 = state.Omega
        jeff = float(np.imag(O1 * np.conj(O2) * O3))
        jeff_norm = jeff / (1.0 + abs(jeff))  # in (-1,1)

        tau_meta = 0.01
        state.z_mem = (
            (1.0 - tau_meta) * float(getattr(state, "z_mem", 0.0))
            + tau_meta * float(jeff_norm)
        )

        state.z = float(z_inst + state.z_mem)

        z = float(state.z)
        phi = float(theta)

        state.Z_macro[:] = np.array([z * np.cos(phi), z * np.sin(phi), z], dtype=float)

        Z_chiral = np.array(
            [
                float(np.imag(np.conj(O2) * O3)),
                float(np.imag(np.conj(O3) * O1)),
                float(np.imag(np.conj(O1) * O2)),
            ],
            dtype=float,
        )
        state.Z_chiral[:] = Z_chiral

        alpha = float(self.p.z_alpha)
        beta = float(self.p.z_beta)
        state.Z_vec[:] = alpha * state.Z_macro + beta * state.Z_chiral


def _kernel_pair(character_modulation: dict[str, Any] | None, seed_text: str):
    restored = TriOctaMemoryKernel(embedder=HashEmbedding())
    spliced = TriOctaMemoryKernel(
        params=copy.deepcopy(restored.params),
        embedder=HashEmbedding(),
    )
    spliced.model = _SplicedReferenceModel(spliced.params)
    restored_state = restored.init_state(seed_text, character_modulation=character_modulation)
    spliced_state = spliced.init_state(seed_text, character_modulation=character_modulation)
    restored_ctx = restored.new_runtime_context()
    spliced_ctx = spliced.new_runtime_context()
    return restored, restored_state, restored_ctx, spliced, spliced_state, spliced_ctx


def _seed_omega(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    real = rng.normal(size=3)
    imag = rng.normal(size=3)
    return (real + 1j * imag).astype(np.complex128)


def _same_params_pair():
    prod_params = production_model_core.ModelParams(omega_noise_sigma=0.0)
    oracle_params = ORACLE.ModelParams()
    for name in (
        "eps",
        "g",
        "d24_steps",
        "phi_step_per_iter",
        "lambda_phase",
        "lambda_vp",
        "gamma",
        "theta_lock",
        "z_alpha",
        "z_beta",
    ):
        setattr(oracle_params, name, copy.deepcopy(getattr(prod_params, name)))
    oracle_params.k_vals = np.array(prod_params.k_vals, dtype=np.asarray(prod_params.k_vals).dtype).copy()
    oracle_params.delta_vals = np.array(
        prod_params.delta_vals,
        dtype=np.asarray(prod_params.delta_vals).dtype,
    ).copy()
    oracle_params.kappa_thresholds = np.array(
        prod_params.kappa_thresholds,
        dtype=np.asarray(prod_params.kappa_thresholds).dtype,
    ).copy()
    assert prod_params.omega_noise_sigma == 0.0
    return prod_params, oracle_params


def _make_state_pair(seed: int):
    omega = _seed_omega(seed)
    prod_state = production_model_core.ModelState(Omega=omega.copy())
    oracle_state = ORACLE.ModelState(Omega=omega.copy())
    return prod_state, oracle_state


def _assert_model_state_exact(prod_state, oracle_state) -> None:
    assert np.array_equal(prod_state.Omega, oracle_state.Omega)
    assert prod_state.kappa() == oracle_state.kappa()
    assert prod_state.phi_index == oracle_state.phi_index
    assert prod_state.cycle_stage == oracle_state.cycle_stage
    assert prod_state.identity_state == oracle_state.identity_state
    assert prod_state.z == oracle_state.z
    assert np.array_equal(prod_state.Z_macro, oracle_state.Z_macro)
    assert np.array_equal(prod_state.Z_chiral, oracle_state.Z_chiral)
    assert np.array_equal(prod_state.Z_vec, oracle_state.Z_vec)
    assert prod_state.t == oracle_state.t
    assert prod_state.step == oracle_state.step


@pytest.mark.parametrize("seed", range(16))
def test_model_core_matches_v4_0_original_oracle_exactly(seed: int) -> None:
    prod_params, oracle_params = _same_params_pair()
    prod_model = production_model_core.TriOctaPhaseLockModel(prod_params)
    oracle_model = ORACLE.TriOctaPhaseLockModel(oracle_params)
    prod_state, oracle_state = _make_state_pair(seed)

    for _ in range(1200):
        prod_model.step(prod_state, dt=prod_params.eps)
        oracle_model.step(oracle_state, dt=oracle_params.eps)
        _assert_model_state_exact(prod_state, oracle_state)


@pytest.mark.parametrize("seed", range(16))
def test_theta_lock_override_does_not_change_omega_path(seed: int) -> None:
    prod_params, oracle_params = _same_params_pair()
    prod_model = production_model_core.TriOctaPhaseLockModel(prod_params)
    oracle_model = ORACLE.TriOctaPhaseLockModel(oracle_params)
    prod_state, oracle_state = _make_state_pair(seed)
    saw_z_diverge = False

    for _ in range(1200):
        prod_model.step(
            prod_state,
            dt=prod_params.eps,
            theta_lock_override=prod_params.theta_lock + 0.125,
        )
        oracle_model.step(oracle_state, dt=oracle_params.eps)
        assert np.array_equal(prod_state.Omega, oracle_state.Omega)
        saw_z_diverge = saw_z_diverge or prod_state.z != oracle_state.z

    assert saw_z_diverge


@pytest.mark.parametrize("arm_label,character_modulation", _ARMS)
def test_process_cognitive_continuity_survives_kernel_restoration(
    arm_label: str,
    character_modulation: dict[str, Any] | None,
) -> None:
    (
        restored,
        restored_state,
        restored_ctx,
        spliced,
        spliced_state,
        spliced_ctx,
    ) = _kernel_pair(
        character_modulation,
        "phase1b cognitive continuity seed",
    )
    saw_canonical_z_diverge = False

    for step in range(2000):
        observation = (
            f"Phase 1b continuity arm={arm_label} step={step}: "
            "cognition stays attached to the legacy readout path."
        )
        restored_state, _, debug = restored.process(
            restored_state,
            observation,
            restored_ctx,
        )
        spliced_state, _, _ = spliced.process(
            spliced_state,
            observation,
            spliced_ctx,
        )
        cog = restored_ctx.cognitive_state

        assert np.array_equal(restored_state.Omega, spliced_state.Omega)
        assert cog.z_mem == spliced_state.z_mem
        assert cog.z_identity == spliced_state.z
        assert cog.identity_state == spliced_state.identity_state
        assert debug["z"] == cog.z_identity
        assert debug["identity_state"] == float(cog.identity_state)
        assert debug["tri_mod"]["identity_state"] == float(cog.identity_state)
        assert set(debug) == _EXPECTED_DEBUG_KEYS
        assert set(debug["tri_mod"]) == _EXPECTED_TRI_MOD_KEYS
        saw_canonical_z_diverge = saw_canonical_z_diverge or restored_state.z != spliced_state.z

    assert saw_canonical_z_diverge


@pytest.mark.parametrize("arm_label,character_modulation", _ARMS)
def test_process_phase1b_golden_replay_preserves_torment_surface(
    arm_label: str,
    character_modulation: dict[str, Any] | None,
) -> None:
    (
        restored,
        restored_state,
        restored_ctx,
        spliced,
        spliced_state,
        spliced_ctx,
    ) = _kernel_pair(
        character_modulation,
        "phase1b golden replay seed",
    )

    for step in range(1000):
        observation = (
            f"Phase 1b golden replay arm={arm_label} step={step}: "
            "surface contract remains unchanged."
        )
        restored_state, restored_signals, restored_debug = restored.process(
            restored_state,
            observation,
            restored_ctx,
        )
        spliced_state, spliced_signals, spliced_debug = spliced.process(
            spliced_state,
            observation,
            spliced_ctx,
        )
        cog = restored_ctx.cognitive_state

        assert restored_signals == spliced_signals
        assert restored_debug == spliced_debug
        assert restored_debug["z"] == cog.z_identity
        assert restored_debug["identity_state"] == float(cog.identity_state)
        assert restored_debug["tri_mod"]["identity_state"] == float(cog.identity_state)
        assert set(restored_debug) == _EXPECTED_DEBUG_KEYS
        assert set(restored_debug["tri_mod"]) == _EXPECTED_TRI_MOD_KEYS

        speed = 0.05 + 0.25 * float(restored_debug["coherence"])
        sign_z = 1.0 if cog.z_identity >= 0 else -1.0
        assert restored_debug["tri_mod"]["seed_v0"][2] == float(0.15 * sign_z * speed)

        assert restored_signals.write_intent is True
        assert restored_signals.memory_type == "episode"
        assert 0.0 <= restored_signals.strength <= 1.0
        assert 0.0 <= restored_signals.confidence <= 1.0
        assert restored_signals.links == []


@pytest.mark.parametrize("seed", range(16))
def test_v4_0_oracle_z_sign_flips_every_other_step(seed: int) -> None:
    zs, signs = _oracle_z_series(seed)
    _assert_canonical_latch_shape(zs, signs)


@pytest.mark.parametrize("seed", range(16))
def test_v4_0_production_z_sign_flips_every_other_step(seed: int) -> None:
    zs, signs = _production_z_series(seed)
    _assert_canonical_latch_shape(zs, signs)


def _oracle_z_series(seed: int) -> tuple[list[float], list[int]]:
    _, oracle_params = _same_params_pair()
    oracle_model = ORACLE.TriOctaPhaseLockModel(oracle_params)
    oracle_state = ORACLE.ModelState(Omega=_seed_omega(seed))
    return _collect_z_series(oracle_model, oracle_state, oracle_params.eps)


def _production_z_series(
    seed: int,
    *,
    model_cls=production_model_core.TriOctaPhaseLockModel,
) -> tuple[list[float], list[int]]:
    prod_params = production_model_core.ModelParams(omega_noise_sigma=0.0)
    assert prod_params.omega_noise_sigma == 0.0
    prod_model = model_cls(prod_params)
    prod_state = production_model_core.ModelState(Omega=_seed_omega(seed))
    return _collect_z_series(prod_model, prod_state, prod_params.eps)


def _collect_z_series(model, state, dt: float) -> tuple[list[float], list[int]]:
    signs: list[int] = []
    zs: list[float] = []

    for _ in range(_LATCH_STEPS_PER_SEED):
        model.step(state, dt=dt)
        z = float(state.z)
        zs.append(z)
        signs.append(1 if z >= 0.0 else -1)
    return zs, signs


def _sign_flips(signs: list[int]) -> int:
    return sum(1 for prev, cur in zip(signs, signs[1:]) if prev != cur)


def _assert_canonical_latch_shape(zs: list[float], signs: list[int]) -> None:
    assert len(zs) == _LATCH_STEPS_PER_SEED
    assert _sign_flips(signs) == _EXPECTED_SIGN_FLIPS_PER_SEED
    assert signs.count(1) > 0
    assert signs.count(-1) > 0


def test_v4_0_oracle_latch_regression_pooled() -> None:
    latched = 0
    pooled_z: list[float] = []
    for seed in _LATCH_SEEDS:
        zs, signs = _oracle_z_series(seed)
        _assert_canonical_latch_shape(zs, signs)
        latched += int(signs.count(1) == 0 or signs.count(-1) == 0)
        pooled_z.extend(zs)
    assert latched == 0
    assert math.fsum(pooled_z) / len(pooled_z) == pytest.approx(0.0, abs=1e-5)


def test_v4_0_production_latch_regression_pooled() -> None:
    latched = 0
    pooled_z: list[float] = []
    flips_by_seed: list[int] = []
    for seed in _LATCH_SEEDS:
        zs, signs = _production_z_series(seed)
        _assert_canonical_latch_shape(zs, signs)
        flips_by_seed.append(_sign_flips(signs))
        latched += int(signs.count(1) == 0 or signs.count(-1) == 0)
        pooled_z.extend(zs)

    assert flips_by_seed == [_EXPECTED_SIGN_FLIPS_PER_SEED] * 16
    assert latched == 0
    assert math.fsum(pooled_z) / len(pooled_z) == pytest.approx(0.0, abs=1e-5)


def test_spliced_reference_would_fail_production_latch_regression() -> None:
    flips_by_seed: list[int] = []
    pooled_z: list[float] = []
    for seed in _LATCH_SEEDS:
        zs, signs = _production_z_series(seed, model_cls=_SplicedReferenceModel)
        flips_by_seed.append(_sign_flips(signs))
        pooled_z.extend(zs)

    assert any(flips != _EXPECTED_SIGN_FLIPS_PER_SEED for flips in flips_by_seed)
    assert math.fsum(pooled_z) / len(pooled_z) != pytest.approx(0.0, abs=1e-5)


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add("." * node.level + (node.module or ""))
    return modules


def test_phase1b_source_boundary_contract() -> None:
    cognitive_path = _REPO_ROOT / "torment_service" / "cognitive_core.py"
    model_path = _REPO_ROOT / "torment_service" / "kernel" / "model_core.py"

    cognitive_src = cognitive_path.read_text(encoding="utf-8")
    model_src = model_path.read_text(encoding="utf-8")

    assert "model_core" not in cognitive_src
    assert "cognitive_core" not in model_src
    assert "CognitiveCore" not in model_src
    assert "z_mem" in cognitive_src
    assert "z_mem" not in model_src

    cognitive_imports = _import_modules(cognitive_path)
    model_imports = _import_modules(model_path)
    assert "torment_service.kernel.model_core" not in cognitive_imports
    assert ".kernel.model_core" not in cognitive_imports
    assert "torment_service.cognitive_core" not in model_imports
    assert "..cognitive_core" not in model_imports
