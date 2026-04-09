"""Tests for Attractor Visualization & Basin Mapping tool.

Covers:
  - Data loading (motifs, character state, trajectories, events)
  - PCA projection edge cases
  - Coherence field integration
  - Plot rendering (no exceptions)
  - End-to-end on live Ryuki data
"""
import os
import shutil
import sys
import tempfile
import traceback

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.visualize_attractors import (
    _pca_2d, _unit, load_motifs, load_character_state,
    load_trajectory_index, load_core_events, MotifInfo,
    make_color_cycle, generate_visualization,
    plot_basin_native, plot_basin_pca, plot_phase_space, plot_timeline,
    load_member_embeddings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def _tmp():
    return tempfile.mkdtemp(prefix="torment_viz_test_")


def _make_mock_motifs():
    return {
        "m1": MotifInfo("m1", "seed motif", 0.85, 0.9, [1, 2, 3],
                        _unit(np.random.randn(384).astype(np.float32))),
        "m2": MotifInfo("m2", "relational motif", 0.5, 0.6, [4, 5],
                        _unit(np.random.randn(384).astype(np.float32))),
    }


def _make_mock_field_rows():
    return [
        {"motif_id": "m1", "label": "seed motif", "phi": 0.6, "kappa": -0.02,
         "tension": 0.1, "role": "basin", "members": 3, "strength": 0.85,
         "stability_score": 0.9, "density": 0.3},
        {"motif_id": "m2", "label": "relational motif", "phi": 0.2, "kappa": 0.01,
         "tension": 0.5, "role": "ridge", "members": 2, "strength": 0.5,
         "stability_score": 0.6, "density": 0.2},
    ]


def _make_mock_trajectory():
    return [
        {"step": 100, "eid": 1, "coh": 0.01, "phi_index": 3, "corridor_deg": 0.1, "pos_x": 0, "pos_y": 0, "pos_z": 0},
        {"step": 200, "eid": 1, "coh": 0.03, "phi_index": 5, "corridor_deg": -0.2, "pos_x": 0.1, "pos_y": 0, "pos_z": 0},
        {"step": 300, "eid": 1, "coh": 0.02, "phi_index": 7, "corridor_deg": 0.3, "pos_x": 0.2, "pos_y": 0.1, "pos_z": 0},
        {"step": 400, "eid": 1, "coh": 0.05, "phi_index": 9, "corridor_deg": 0.0, "pos_x": 0.3, "pos_y": 0.1, "pos_z": 0},
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class TestPCA:
    def test_basic_projection(self):
        X = np.random.randn(10, 384).astype(np.float32)
        Z = _pca_2d(X)
        assert Z.shape == (10, 2)
        assert not np.any(np.isnan(Z))

    def test_single_point(self):
        X = np.random.randn(1, 384).astype(np.float32)
        Z = _pca_2d(X)
        assert Z.shape == (1, 2)

    def test_empty(self):
        X = np.zeros((0, 384), dtype=np.float32)
        Z = _pca_2d(X)
        assert Z.shape == (0, 2)

    def test_two_points(self):
        X = np.random.randn(2, 50).astype(np.float32)
        Z = _pca_2d(X)
        assert Z.shape == (2, 2)


class TestDataLoading:
    def test_load_motifs_live(self):
        motifs = load_motifs(DATA_DIR, "ryuki", "research")
        assert len(motifs) > 0
        for mid, m in motifs.items():
            assert isinstance(m.motif_id, str)
            assert isinstance(m.centroid, np.ndarray)
            assert m.centroid.shape[0] > 0
            assert 0 <= m.strength <= 1.0

    def test_load_motifs_missing(self):
        motifs = load_motifs(DATA_DIR, "nonexistent", "research")
        assert motifs == {}

    def test_load_character_state_live(self):
        state = load_character_state(DATA_DIR, "ryuki", "ryuki_nox")
        assert state is not None
        assert "drift_score" in state
        assert "drift_history" in state
        assert "seed_id" in state

    def test_load_character_state_missing(self):
        state = load_character_state(DATA_DIR, "nonexistent", "agent")
        assert state is None

    def test_load_trajectory_index_live(self):
        rows = load_trajectory_index(DATA_DIR, "ryuki", "ryuki_nox")
        assert len(rows) > 0
        for r in rows:
            assert "step" in r
            assert "phi_index" in r
            assert "coh" in r

    def test_load_core_events_live(self):
        events = load_core_events(DATA_DIR, "ryuki", "ryuki_nox")
        assert len(events) > 0
        for e in events:
            assert "event_type" in e
            assert "step" in e

    def test_load_member_embeddings_live(self):
        motifs = load_motifs(DATA_DIR, "ryuki", "research")
        rows, dim = load_member_embeddings(DATA_DIR, "ryuki", "ryuki_nox", motifs)
        assert dim > 0
        assert len(rows) > 0
        for r in rows:
            assert "eid" in r
            assert "emb" in r
            assert r["emb"].shape[0] == dim


class TestPlotRendering:
    def test_basin_native_renders(self):
        fig, ax = plt.subplots()
        field_rows = _make_mock_field_rows()
        plot_basin_native(ax, field_rows, seed_motif_id="m1")
        plt.close(fig)

    def test_basin_native_empty(self):
        fig, ax = plt.subplots()
        plot_basin_native(ax, [], seed_motif_id=None)
        plt.close(fig)

    def test_basin_pca_renders(self):
        fig, ax = plt.subplots()
        motifs = _make_mock_motifs()
        member_rows = [
            {"eid": i, "motif_id": mid, "label": m.label,
             "emb": _unit(np.random.randn(384).astype(np.float32))}
            for mid, m in motifs.items() for i in m.members
        ]
        field_by_mid = {r["motif_id"]: r for r in _make_mock_field_rows()}
        plot_basin_pca(ax, motifs, member_rows, field_by_mid, seed_motif_id="m1")
        plt.close(fig)

    def test_phase_space_renders(self):
        fig, ax = plt.subplots()
        plot_phase_space(ax, _make_mock_trajectory())
        plt.close(fig)

    def test_phase_space_sparse(self):
        fig, ax = plt.subplots()
        plot_phase_space(ax, [{"step": 1, "phi_index": 0, "coh": 0, "corridor_deg": 0}])
        plt.close(fig)

    def test_timeline_renders(self):
        fig, axes = plt.subplots(3, 1)
        char_state = {
            "drift_history": [[100, 0.1], [200, -0.2], [300, 0.05]],
            "seed_id": "test",
        }
        events = [
            {"event_type": "MEMORY_CREATE", "step": 100, "eid": 1, "coherence": 0.5, "timestamp": "123"},
            {"event_type": "MEMORY_CREATE", "step": 200, "eid": 2, "coherence": 0.6, "timestamp": "456"},
        ]
        plot_timeline(axes, char_state, events, _make_mock_trajectory())
        plt.close(fig)

    def test_timeline_empty(self):
        fig, axes = plt.subplots(3, 1)
        plot_timeline(axes, None, [], [])
        plt.close(fig)


class TestEndToEnd:
    def test_full_ryuki_visualization(self):
        tmp = _tmp()
        try:
            png_path = generate_visualization(
                data_dir=DATA_DIR,
                workspace="ryuki",
                agent="ryuki_nox",
                domain="research",
                out_dir=tmp,
            )
            assert os.path.exists(png_path)
            assert os.path.getsize(png_path) > 10_000  # > 10KB
            # CSV also generated
            csv_path = png_path.replace(".png", "_summary.csv")
            assert os.path.exists(csv_path)
        finally:
            shutil.rmtree(tmp)

    def test_single_layer_basin(self):
        tmp = _tmp()
        try:
            png_path = generate_visualization(
                data_dir=DATA_DIR,
                workspace="ryuki",
                agent="ryuki_nox",
                domain="research",
                out_dir=tmp,
                layers="basin",
            )
            assert os.path.exists(png_path)
        finally:
            shutil.rmtree(tmp)

    def test_single_layer_orbits(self):
        tmp = _tmp()
        try:
            png_path = generate_visualization(
                data_dir=DATA_DIR,
                workspace="ryuki",
                agent="ryuki_nox",
                domain="research",
                out_dir=tmp,
                layers="orbits",
            )
            assert os.path.exists(png_path)
        finally:
            shutil.rmtree(tmp)


class TestHelpers:
    def test_color_cycle(self):
        colors = make_color_cycle(15)
        assert len(colors) == 15

    def test_unit_normalization(self):
        v = np.array([3.0, 4.0, 0.0], dtype=np.float32)
        u = _unit(v)
        assert abs(np.linalg.norm(u) - 1.0) < 1e-5


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_viz_tests():
    tests = [
        ("V.1 PCA basic", TestPCA().test_basic_projection),
        ("V.2 PCA single point", TestPCA().test_single_point),
        ("V.3 PCA empty", TestPCA().test_empty),
        ("V.4 PCA two points", TestPCA().test_two_points),
        ("V.5 Load motifs live", TestDataLoading().test_load_motifs_live),
        ("V.6 Load motifs missing", TestDataLoading().test_load_motifs_missing),
        ("V.7 Load char state live", TestDataLoading().test_load_character_state_live),
        ("V.8 Load char state missing", TestDataLoading().test_load_character_state_missing),
        ("V.9 Load trajectory live", TestDataLoading().test_load_trajectory_index_live),
        ("V.10 Load events live", TestDataLoading().test_load_core_events_live),
        ("V.11 Load embeddings live", TestDataLoading().test_load_member_embeddings_live),
        ("V.12 Basin native renders", TestPlotRendering().test_basin_native_renders),
        ("V.13 Basin native empty", TestPlotRendering().test_basin_native_empty),
        ("V.14 Basin PCA renders", TestPlotRendering().test_basin_pca_renders),
        ("V.15 Phase space renders", TestPlotRendering().test_phase_space_renders),
        ("V.16 Phase space sparse", TestPlotRendering().test_phase_space_sparse),
        ("V.17 Timeline renders", TestPlotRendering().test_timeline_renders),
        ("V.18 Timeline empty", TestPlotRendering().test_timeline_empty),
        ("V.19 E2E Ryuki full", TestEndToEnd().test_full_ryuki_visualization),
        ("V.20 E2E basin only", TestEndToEnd().test_single_layer_basin),
        ("V.21 E2E orbits only", TestEndToEnd().test_single_layer_orbits),
        ("V.22 Color cycle", TestHelpers().test_color_cycle),
        ("V.23 Unit normalization", TestHelpers().test_unit_normalization),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception:
            print(f"  FAIL  {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_viz_tests()
    print(f"\nVisualization: {p} passed, {f} failed")
    if f > 0:
        exit(1)
