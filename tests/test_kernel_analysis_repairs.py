"""Stage A behavior repairs; historical P4A/P4B captures remain immutable."""
from collections import UserDict
import copy
import itertools
import subprocess
import sys

import numpy as np
import pytest

from torment_service.kernel.offline import rsb_analysis as rsb
from torment_service.kernel.observables.recursive_velocity import compute_recursive_velocity_geom
from test_kernel_definitions_ownership import _encode
from test_kernel_offline_relocation import ROOT, SCRIPT_PATHS, _environment_for_child


def _same(actual, expected):
    assert _encode(actual) == _encode(expected)


@pytest.mark.parametrize("steps,extras", [(48, False), (None, False), (48, True)],
                         ids=["48-ordinary", "default-2000", "48-metadata"])
def test_real_long_driver(monkeypatch, steps, extras):
    """Spies delegate to real model/sampler/clustering; only show is suppressed."""
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from torment_service.kernel.offline import experiments as exp
    from torment_service.kernel.model_core import ModelParams

    saved_rng = np.random.get_state()
    calls, original, snapshots, shows = [], [], [], []
    real_run = exp.TriOctaPhaseLockModel.run
    real_cluster = exp.cluster_delta_kz

    def record_run(self, *args, **kwargs):
        history = real_run(self, *args, **kwargs)
        if extras:
            n = len(history["t"])
            history.update(other_mapping=UserDict({i: i for i in range(n)}),
                           scalar=7, numpy_scalar=np.float32(.5), zero_dim=np.array(9),
                           text="diagnostic", absent=None, constant_tuple=(4, 5),
                           constant_array=np.array([1, 2], dtype=np.int16),
                           series_list=list(range(n)), series_tuple=tuple(range(n)),
                           strided=np.arange(n * 4, dtype=np.int16).reshape(n, 4)[:, ::2])
        original.append(history)
        snapshots.append(copy.deepcopy(history))
        return history

    def record_cluster(history, *args, **kwargs):
        result = real_cluster(history, *args, **kwargs)
        calls.append((history, result))
        return result

    monkeypatch.setattr(exp.TriOctaPhaseLockModel, "run", record_run)
    monkeypatch.setattr(exp, "cluster_delta_kz", record_cluster)
    monkeypatch.setattr(plt, "show", lambda: shows.append(True))
    try:
        np.random.seed(2718)
        kwargs = {} if steps is None else {"n_steps": steps}
        result = exp.run_long_time_stability_test(ModelParams(), **kwargs)
        assert list(result) == ["J_early_mean", "J_late_mean", "sign_early", "sign_late",
                                "early_all", "late_all", "early_cp", "late_cp", "early_ncp", "late_ncp"]
        assert len(calls) == len(shows) == 3
        assert len(plt.get_fignums()) == 6
        full = original[0]
        n = 2000 if steps is None else steps
        assert len(full["t"]) == n
        for history, (mask, mags) in calls:
            assert mask.shape == mags.shape == (len(history["t"]) - 1,)
        for index, (lo, hi) in enumerate(((0, n // 4), (3 * n // 4, n)), 1):
            segment = calls[index][0]
            assert list(segment) == list(full)
            for key, value in full.items():
                if key in {"_meta", "other_mapping", "scalar", "numpy_scalar", "zero_dim",
                           "text", "absent", "constant_tuple", "constant_array"}:
                    assert segment[key] is value
                else:
                    arr = np.asarray(value)
                    if arr.ndim and arr.shape[0] == n:
                        _same(segment[key], arr[lo:hi])
                    else:
                        assert segment[key] is value
            assert len(segment["t"]) == hi - lo
            prefix = "early" if index == 1 else "late"
            for suffix in ("all", "cp", "ncp"):
                hist = result[prefix + "_" + suffix]
                assert hist.shape == (12,) and np.issubdtype(hist.dtype, np.integer)
                assert np.all(hist >= 0)
            np.testing.assert_array_equal(result[prefix + "_all"],
                                          result[prefix + "_cp"] + result[prefix + "_ncp"])
            assert result[prefix + "_all"].sum() == calls[index][1][0].sum()
        obs = exp.sample_physics_observables(full)
        for prefix, window in (("early", slice((n // 4) // 2, n // 4)), ("late", slice(3 * n // 4, n))):
            expected = float(np.mean(obs["J_eff"][window]))
            assert result["J_" + prefix + "_mean"] == expected
            assert result["sign_" + prefix] == int(np.sign(expected))
        for key, value in full.items():
            if isinstance(value, UserDict):
                assert value == snapshots[0][key]
            else:
                _same(value, snapshots[0][key])
    finally:
        plt.close("all")
        np.random.set_state(saved_rng)
    _same(np.random.get_state(), saved_rng)


def _psi():
    # Distinct T=5, C=3, M=4, H=2; integral energies avoid reduction-order noise.
    amplitudes = np.array([[1, 1, 1, 1], [1, 1, 0, 0], [0, 0, 2, 0],
                           [0, 0, 2, 0], [0, 0, 2, 0]], dtype=float)
    return (amplitudes[:, None, :, None] * np.array([1, 2, 3])[None, :, None, None]
            * np.array([1, 2])[None, None, None, :]).astype(complex)


@pytest.mark.parametrize("order", list(itertools.permutations(range(4))))
@pytest.mark.parametrize("storage", ["contiguous", "strided"])
def test_rsb_layouts(order, storage):
    canonical = _psi()
    expected = rsb.analyze_rsb_history(canonical, verbose=False)
    energy = np.array([[70, 70, 70, 70], [70, 70, 0, 0], [0, 0, 280, 0],
                       [0, 0, 280, 0], [0, 0, 280, 0]], dtype=float)
    np.testing.assert_array_equal(expected["E_t_m"], energy)
    np.testing.assert_array_equal(expected["dom_band_series"], [0, 0, 2, 2, 2])
    assert expected["meta_label"] == "Class III_slow"
    assert expected["seed_summary"]["t_collapse_10pct"] == 2.
    value = canonical.transpose(order).copy()
    if storage == "strided":
        backing = np.empty((*value.shape[:-1], value.shape[-1] * 2), dtype=complex)
        backing[..., ::2] = value
        value = backing[..., ::2]
        assert not value.flags.c_contiguous
    before = value.copy()
    actual = rsb.analyze_rsb_history(value, chan_axis=order.index(1),
                                     phase_axis=order.index(2), hel_axis=order.index(3), verbose=False)
    _same(actual, expected)
    np.testing.assert_array_equal(value, before)


@pytest.mark.parametrize("order", list(itertools.permutations(range(4))))
def test_empty_layouts(order):
    actual = rsb.analyze_rsb_history(np.empty((0, 3, 4, 2)).transpose(order),
                                    chan_axis=order.index(1), phase_axis=order.index(2),
                                    hel_axis=order.index(3), verbose=False, seed=0)
    assert list(actual) == ["label", "d_series", "sigma_spec_series", "h_series", "E_t_m",
                            "dom_band_series", "spectral_entropy_series"]
    assert actual["label"] == "Transitional / ambiguous"
    for name in ("d_series", "sigma_spec_series", "h_series"):
        _same(actual[name], np.array([], dtype=float))
    assert actual["E_t_m"] is actual["dom_band_series"] is actual["spectral_entropy_series"] is None


@pytest.mark.parametrize("axes", [(2, 2, 3), (-1, 2, 3), (4, 2, 3), (0, 0, 0)])
def test_invalid_axes_unchanged(axes):
    with pytest.raises(ValueError, match="Could not infer time axis"):
        rsb.analyze_rsb_history(_psi(), *axes, verbose=False)


@pytest.mark.parametrize("seed", [None, 0, 19])
def test_seed_is_only_a_label(seed):
    before = np.random.get_state()
    expected = rsb.analyze_rsb_history(_psi(), verbose=False)
    expected["seed_summary"]["seed"] = seed
    actual = rsb.analyze_rsb_history(_psi(), seed=seed, verbose=False)
    _same(actual, expected)
    _same(np.random.get_state(), before)


@pytest.mark.parametrize("omega", [None, [], "omitted"])
def test_optional_omega_components(omega):
    hist = {"Z_total": np.array([[0., 0., 0.], [3., 4., 0.], [3., 4., 2.]]),
            "phi_index": [1, 1, 2], "kappa": [0., 4., 1.]}
    if not isinstance(omega, str):
        hist["Omega"] = omega
    before = copy.deepcopy(hist)
    velocity, components = compute_recursive_velocity_geom(hist, w_z=2., w_phase=3.,
                                                           w_corridor=3., w_kappa=1., return_components=True)
    _same(components, {"z_key": "Z_total", "dZ": np.array([5., 2.]), "dphi": np.array([0., 0.]),
                       "dcorr": np.array([0., 1.]), "dkappa": np.array([4., 3.])})
    np.testing.assert_array_equal(velocity, np.sqrt([116., 34.]))
    _same(hist, before)


def test_geometry_retains_required_data_and_nan_contracts():
    with pytest.raises(KeyError, match="Z_total"):
        compute_recursive_velocity_geom({"Omega": None})
    with pytest.raises(ValueError, match="broadcast"):
        compute_recursive_velocity_geom({"Z_total": np.ones((3, 3)), "Omega": np.ones((5, 3))})
    value, components = compute_recursive_velocity_geom({"Z_total": np.array([[0., 0., 0.], [np.nan, 0., 0.]]),
                                                         "Omega": None}, return_components=True)
    assert np.isnan(value[0]) and np.isnan(components["dZ"][0])
    value = compute_recursive_velocity_geom({"Z_total": np.ones((2, 3)), "Omega": np.full((2, 3), np.nan)})
    assert np.isnan(value[0])


@pytest.mark.parametrize("entropy,bands", [(None, None), (None, [2, 1, 2]), ([1., .5, .0], None)])
def test_optional_summary_series(entropy, bands):
    stats = dict(label="example", spectral_entropy_series=entropy, dom_band_series=bands)
    before = copy.deepcopy(stats)
    summary = rsb.summarize_rsb_seed(stats, seed=0)
    expected = dict(regime="example", seed=0, H0=None, HT=None, delta_H=None,
                    t_collapse_10pct=None, collapsed_10pct=False,
                    m0_final=None, visited_bands=[], n_band_switches=0)
    if entropy is not None:
        expected.update(H0=1., HT=0., delta_H=1., t_collapse_10pct=2., collapsed_10pct=True)
    if bands is not None:
        expected.update(m0_final=2, visited_bands=[1, 2], n_band_switches=2)
    _same(summary, expected)
    _same(stats, before)


def test_empty_wrapper_composes():
    stats = rsb.analyze_rsb_history(np.empty((0, 3, 4, 2)), verbose=False)
    _same(rsb.summarize_rsb_seed(stats), dict(regime="Transitional / ambiguous", seed=None,
          H0=None, HT=None, delta_H=None, t_collapse_10pct=None, collapsed_10pct=False,
          m0_final=None, visited_bands=[], n_band_switches=0))


@pytest.mark.parametrize("stats,error", [({"spectral_entropy_series": 2.}, IndexError),
                                         ({"dom_band_series": [np.nan]}, ValueError),
                                         ({"dom_band_series": [[1, 2]]}, TypeError)])
def test_summary_malformed_inputs_still_rejected(stats, error):
    with pytest.raises(error):
        rsb.summarize_rsb_seed(stats)


@pytest.mark.parametrize("difference", ["missing", None, 0., -.25])
def test_incomplete_formatter(difference):
    summary = {"H0": 1., "HT": .5}
    if difference != "missing":
        summary["delta_H"] = difference
    before = copy.deepcopy(summary)
    expected = .5 if difference in ("missing", None) else difference
    assert rsb.format_rsb_seed_summary(summary) == (
        "RSB seed summary\n  regime: ?\n  H(0)    = 1.000\n  H(T)    = 0.500\n"
        f"  ΔH      = {expected:.3f}\n  t_collapse_10pct: none (no 10% collapse)\n"
        "  m₀(T)   = None\n  visited bands = []\n  # band switches = 0")
    assert summary == before


@pytest.mark.parametrize("summary", [{}, {"H0": 1.}, {"HT": .5}, {"H0": None, "HT": .5}])
def test_formatter_absent_endpoints(summary):
    assert "H(0), H(T), ΔH: N/A" in rsb.format_rsb_seed_summary(summary)


INVALID_CSV = [
    ("trajectories", "lambda_phase,channel,traj_class\n", "No trajectory data rows found"),
    ("trajectories", "lambda_phase,channel\n.2,vis\n", "Missing required trajectory columns: traj_class"),
    ("trajectories", "traj_class\nlocked\n", "Missing required trajectory columns: lambda_phase, channel"),
    ("health", "vrec_mean\n1\n", "Missing required health columns: has_nan, omega_blowup, kappa_runaway, z_runaway"),
    ("health", "has_nan,omega_blowup,kappa_runaway\n0,0,0\n", "Missing required health columns: z_runaway"),
    ("health", "has_nan,omega_blowup,kappa_runaway,z_runaway\n", "No health data rows found"),
]


@pytest.mark.parametrize("kind,payload,message", INVALID_CSV)
@pytest.mark.parametrize("existing_output", [False, True])
def test_csv_deliberate_validation(tmp_path, kind, payload, message, existing_output):
    relative = ("outputs_patch39_unified/lambda_02/seed_trajectories_seed1.csv" if kind == "trajectories"
                else "outputs/wide_scan_triocta_ultra.csv")
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(payload.encode())
    output = tmp_path / "outputs_patch39_unified/trajectory_class_summary.csv"
    if existing_output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"preexisting summary\r\n")
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*.csv")}
    result = subprocess.run([sys.executable, "-B", str(ROOT / SCRIPT_PATHS[kind][1])],
                            cwd=tmp_path, env=_environment_for_child(tmp_path),
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode != 0
    assert message in result.stderr
    assert result.stdout == ""
    assert {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*.csv")} == before


def test_trajectory_validates_each_file_before_output(tmp_path):
    base = tmp_path / "outputs_patch39_unified/lambda_02"
    base.mkdir(parents=True)
    (base / "seed_trajectories_seed1.csv").write_text("lambda_phase,channel,traj_class\n.2,vis,locked\n")
    (base / "seed_trajectories_seed2.csv").write_text("lambda_phase,channel\n.2,dark\n")
    output = base.parent / "trajectory_class_summary.csv"
    output.write_bytes(b"existing\n")
    before = {p.name: p.read_bytes() for p in base.parent.rglob("*.csv")}
    result = subprocess.run([sys.executable, "-B", str(ROOT / SCRIPT_PATHS["trajectories"][1])],
                            cwd=tmp_path, env=_environment_for_child(tmp_path),
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode != 0
    assert "Missing required trajectory columns: traj_class" in result.stderr
    assert result.stdout == ""
    assert {p.name: p.read_bytes() for p in base.parent.rglob("*.csv")} == before
