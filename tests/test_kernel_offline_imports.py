"""P1: optional libraries are required at use, not at offline-module import.

Each probe gets a fresh interpreter and disposable data roots. Plot/cluster and
real-driver tests skip explicitly if their optional dependencies are absent;
the substitute-driver tests check import resolution only, not end-to-end use.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULES = ("diagnostics", "physics_sampler", "physics_sampler2", "tangent_corridor_analysis")
PLOTS = (
    ("physics_sampler", "plot_phase_and_cp_distributions", 2),
    ("physics_sampler2", "plot_flavor_time_series", 1),
    ("physics_sampler2", "plot_Jeff_vs_time", 1),
    ("tangent_corridor_analysis", "detect_tangent_corridors", 1),
    ("tangent_corridor_analysis", "cluster_delta_kz", 2),
)


def _child(tmp_path, code, *, blocked=(), expected_attempt=False):
    env = os.environ.copy()
    env.update(
        TORMENT_DATA_DIR=str(tmp_path / "data"),
        TORMENT_MCP_DATA_DIR=str(tmp_path / "mcp"),
        MPLBACKEND="Agg",
        MPLCONFIGDIR=str(tmp_path / "mpl"),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONIOENCODING="utf-8",
    )
    setup = f"""
import importlib
import importlib.abc
import sys
sys.path.insert(0, {str(ROOT)!r})
blocked = {tuple(blocked)!r}
attempts = []
assert not any(name.split('.')[0] in blocked for name in sys.modules)
class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked:
            attempts.append(fullname)
            raise ModuleNotFoundError('P1 blocked ' + fullname, name=fullname)
sys.meta_path.insert(0, BlockOptional())
"""
    checks = "\nassert not any(name.split('.')[0] in blocked for name in sys.modules)\n"
    checks += "assert attempts\n" if expected_attempt else "assert not attempts\n"
    completed = subprocess.run(
        [sys.executable, "-B", "-c", setup + textwrap.dedent(code) + checks],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8", timeout=90,
    )
    if completed.returncode == 77:
        pytest.skip(completed.stdout.strip())
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.parametrize("module", MODULES)
def test_offline_module_import_without_optional_libraries(tmp_path, module):
    _child(tmp_path, f"importlib.import_module('torment_service.kernel.{module}')",
           blocked=("matplotlib", "scipy"))


def test_normal_runtime_imports_without_optional_libraries(tmp_path):
    # T0's existing runtime consumer map; import only, never start a service.
    _child(tmp_path, """
        import torment_service.kernel
        import torment_service.kernel.model_core
        import torment_service.memory_kernel
        import torment_service.cognitive_core
        import torment_service.checkpoint
        import torment_service.memory_graph
        import torment_service.fabric
        assert not any('torment_service.kernel.' + name in sys.modules for name in
                       ('diagnostics', 'physics_sampler', 'physics_sampler2', 'tangent_corridor_analysis'))
    """, blocked=("matplotlib", "scipy"))


def test_numpy_helpers_without_optional_libraries(tmp_path):
    _child(tmp_path, """
        import numpy as np
        from torment_service.kernel import diagnostics as d, physics_sampler as s
        from torment_service.kernel import physics_sampler2 as s2, tangent_corridor_analysis as c
        hist = {'Omega': np.tile([1+0j, 1j, 1+0j], (12, 1)),
                'phi_index': np.arange(12), 't': np.arange(12, dtype=float)}
        obs = s.sample_physics_observables(hist)
        assert set(obs) == {'P', 'theta12', 'theta23', 'theta31', 'J_eff'}
        np.testing.assert_allclose(obs['P'], 1 / 3, rtol=1e-12)
        np.testing.assert_array_equal(obs['J_eff'], -np.ones(12))
        np.testing.assert_array_equal(obs['theta12'], np.full(12, -np.pi / 2))
        np.testing.assert_array_equal(obs['theta23'], np.full(12, np.pi / 2))
        np.testing.assert_array_equal(obs['theta31'], np.zeros(12))
        cp, non = s2.cp_conditioned_masks(hist)
        np.testing.assert_array_equal(cp, [0,0,1,1,1,0,0,0,1,1,1,0])
        np.testing.assert_array_equal(non, ~cp)
        signal = np.array([0., .01, .04, -.1, .3, .5, .8, .9, 1., 1.])
        # Small pre-P1 results, captured before the import move.
        window = s2.detect_chirality_selection_window({'t': np.arange(10.)}, {'J_eff': signal})
        assert window == {'t_10': 3., 't_90': 7., 'dt': 4., 't_commit': 7., 'sign_commit': 1}
        falling = np.array([1., .9, .8, .5, .3, .1, .04, .01, 0., 0.])
        window = s2.detect_chirality_selection_window({'t': np.arange(10.)}, {'J_eff': falling})
        assert window == {'t_10': 1., 't_90': 6., 'dt': 5., 't_commit': 0., 'sign_commit': 1}
        assert s2.detect_chirality_selection_window(hist, {'J_eff': np.zeros(12)}) is None
        assert s2.detect_chirality_selection_window({'t': np.arange(2.)}, {'J_eff': np.ones(2)}) is None
        strong = np.ones(11, dtype=bool)
        all_c, cp_c, non_c = d.strong_delta_sector_histogram(hist, strong)
        np.testing.assert_array_equal(all_c, [0] + [1] * 11)
        np.testing.assert_array_equal(cp_c, cp.astype(int))
        np.testing.assert_array_equal(cp_c + non_c, all_c)
        split = c.cp_split_big_delta_events(hist, strong, np.arange(1., 12.))
        np.testing.assert_array_equal(split['strong_cp_mask'], cp[1:])
        np.testing.assert_array_equal(split['strong_ncp_mask'], non[1:])
        s.summarize_observables(obs)
        s2.summarize_cp_conditioned_observables(hist, obs)
    """, blocked=("matplotlib", "scipy"))


@pytest.mark.parametrize("module,function,_", PLOTS)
def test_plot_dependency_error_is_deferred_until_call(tmp_path, module, function, _):
    _child(tmp_path, f"""
        mod = importlib.import_module('torment_service.kernel.{module}')
        try:
            getattr(mod, {function!r})(*({{}}, {{}}) if {function!r} in
                ('plot_flavor_time_series', 'plot_Jeff_vs_time') else ({{}},))
        except ModuleNotFoundError as exc:
            assert exc.name == 'matplotlib'
        else:
            raise AssertionError('plotting must still require matplotlib')
    """, blocked=("matplotlib", "scipy"), expected_attempt=True)


_PLOTTING = """
import importlib.util
for dependency in dependencies:
    if importlib.util.find_spec(dependency) is None:
        print('Unavailable capability: ' + dependency + ' required for real plotting/clustering')
        sys.exit(77)
import numpy as np
import matplotlib
matplotlib.use('Agg', force=True)
import matplotlib.pyplot as plt
from unittest.mock import patch
from torment_service.kernel import diagnostics as d, physics_sampler as s
from torment_service.kernel import physics_sampler2 as s2, tangent_corridor_analysis as c
from torment_service.kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel
saved_rng = np.random.get_state()
np.random.seed(2718)
"""


def test_clustering_still_requires_scipy_at_call(tmp_path):
    _child(tmp_path, "dependencies = ('matplotlib',)\n" + _PLOTTING + """
try:
    with patch.object(plt, 'show') as show:
        try:
            c.cluster_delta_kz({})
        except ModuleNotFoundError as exc:
            assert exc.name == 'scipy'
        else:
            raise AssertionError('clustering must still require scipy')
        show.assert_not_called()
finally:
    np.random.set_state(saved_rng)
    plt.close('all')
""", blocked=("scipy",), expected_attempt=True)


@pytest.mark.parametrize("module,function,figures", PLOTS)
def test_real_plotting_and_clustering(tmp_path, module, function, figures):
    dependencies = ("matplotlib", "scipy") if function == "cluster_delta_kz" else ("matplotlib",)
    _child(tmp_path, f"dependencies = {dependencies!r}\n" + _PLOTTING + f"""
try:
    hist = TriOctaPhaseLockModel(ModelParams()).run(
        ModelState(Omega=np.array([.3+.1j, -.2+.4j, .1-.3j])), n_steps=32, dt=.05)
    obs = s.sample_physics_observables(hist)
    func = getattr(importlib.import_module('torment_service.kernel.{module}'), {function!r})
    args = (obs,) if {function!r} == 'plot_phase_and_cp_distributions' else (
        (hist, obs) if {function!r} in ('plot_flavor_time_series', 'plot_Jeff_vs_time') else (hist,))
    with patch.object(plt, 'show') as show:
        if {function!r} == 'cluster_delta_kz':
            from scipy.cluster.vq import kmeans2
            with patch('scipy.cluster.vq.kmeans2', wraps=kmeans2) as actual_kmeans:
                mask, mags = func(*args)
            assert actual_kmeans.call_count == 1
            assert actual_kmeans.call_args.args[1] == 3
            assert actual_kmeans.call_args.kwargs == {{'minit': 'points'}}
            assert mask.dtype == bool and mask.shape == mags.shape == (31,)
            assert mask.any() and np.isfinite(mags).all()
        else:
            result = func(*args)
            if {function!r} == 'detect_tangent_corridors':
                assert [item.shape for item in result] == [(31,), (31, 2), (31, 3), (31,)]
        show.assert_called_once_with()
        assert len(plt.get_fignums()) == {figures}
        for num in plt.get_fignums():
            fig = plt.figure(num)
            assert fig.axes and all(ax.lines or ax.collections or ax.patches for ax in fig.axes)
            fig.canvas.draw()
finally:
    plt.close('all')
    np.random.set_state(saved_rng)
""")


@pytest.mark.parametrize("driver", ("run_ic_scan", "run_noise_robustness_test"))
def test_repaired_driver_import_resolution_with_substitutes(tmp_path, driver):
    _child(tmp_path, f"""
        import numpy as np
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from torment_service.kernel import diagnostics as d, model_core as core
        from torment_service.kernel.offline import experiments as e, samplers as s
        hist = {{'t': np.arange(4.), 'kappa': np.arange(4.), 'z': np.arange(4.)}}
        sampler = Mock(return_value={{'J_eff': np.array([.1, .2, .4, .8])}})
        model = Mock()
        model.run.return_value = hist
        factory = Mock(return_value=model)
        state = Mock(return_value=object())
        cluster = Mock(return_value=(np.array([True, False, True]), np.array([1., 2., 3.])))
        params = SimpleNamespace(eps=.1, g=.2, k_vals=(1, 2, 3))
        # Call through diagnostics, but patch the actual implementation owners.
        # IC imports its sampler from samplers; noise imports model_core classes.
        target = e if {driver!r} == 'run_ic_scan' else core
        sampler_target = s if {driver!r} == 'run_ic_scan' else e
        with patch.object(target, 'ModelState', state), patch.object(target, 'TriOctaPhaseLockModel', factory), \
             patch.object(sampler_target, 'sample_physics_observables', sampler), \
             patch.object(e, 'cluster_delta_kz', cluster):
            if {driver!r} == 'run_ic_scan':
                result = d.run_ic_scan(params, n_inits=1, verbose=False)
                assert len(result) == 1 and result[0]['num_strong_delta'] == 2
                assert model.run.call_args.kwargs == {{'n_steps': 200, 'dt': .05}}
            else:
                result = d.run_noise_robustness_test(params, n_steps=4)
                assert result['frac_agree'] == 1.
                assert model.run.call_args.kwargs == {{'n_steps': 4, 'dt': .05}}
            sampler.assert_called_once_with(hist)
            factory.assert_called_once_with(params)
            state.assert_called_once()
    """, blocked=("matplotlib", "scipy"))


@pytest.mark.parametrize("driver", ("run_ic_scan", "run_noise_robustness_test"))
def test_repaired_driver_real_smoke(tmp_path, driver):
    _child(tmp_path, "dependencies = ('matplotlib', 'scipy')\n" + _PLOTTING + f"""
try:
    with patch.object(plt, 'show') as show:
        if {driver!r} == 'run_ic_scan':
            result = d.run_ic_scan(ModelParams(), n_inits=1, verbose=True)
            assert len(result) == 1 and result[0]['run'] == 0
            assert set(result[0]) == {{'run', 'J_plateau', 'J_sign', 't10', 't90', 'dtJ',
                                      'num_strong_delta', 'max_delta'}}
            assert np.isfinite(result[0]['J_plateau']) and result[0]['max_delta'] > 0
            assert show.call_count == 1
        else:
            result = d.run_noise_robustness_test(ModelParams(), n_steps=32)
            assert set(result) == {{'base_n_strong', 'noisy_n_strong', 'frac_agree', 'corr_mags'}}
            assert 0 <= result['frac_agree'] <= 1 and np.isfinite(result['corr_mags'])
            assert show.call_count == 2
        for num in plt.get_fignums():
            plt.figure(num).canvas.draw()
finally:
    plt.close('all')
    np.random.set_state(saved_rng)
""")
