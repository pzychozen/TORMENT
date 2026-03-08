#!/usr/bin/env python3
"""
visualize_attractors.py — TORMENT Attractor Visualization & Basin Mapping

Generates a multi-panel PNG showing three layers of the attractor geometry:

  Layer 1 (top): Basin Landscape — side-by-side
    Left:  Native engine geometry (phi vs kappa, colored by tension)
    Right: Embedding PCA projection (semantic space)

  Layer 2 (middle): Phase Space Dynamics
    Trajectory through D24 sectors, coherence, corridor proximity

  Layer 3 (bottom): Drift + Identity Timeline
    Drift score, memory events, coherence/corridor over time

Usage:
    python tools/visualize_attractors.py \\
      --data-dir data \\
      --workspace ryuki \\
      --agent ryuki_nox \\
      --domain research \\
      --out outputs
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# matplotlib must be set to non-interactive backend before import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.coherence_field import compute_coherence_field


# ---------------------------------------------------------------------------
# Shared helpers (reused from motif_field_viz.py)
# ---------------------------------------------------------------------------

def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)


def _pca_2d(X: np.ndarray) -> np.ndarray:
    """Simple PCA via SVD; returns Nx2."""
    if X.ndim != 2:
        raise ValueError("X must be 2D")
    if X.shape[0] == 0:
        return np.zeros((0, 2), dtype=np.float32)
    Xc = X - X.mean(axis=0, keepdims=True)
    if X.shape[0] == 1:
        return np.zeros((1, 2), dtype=np.float32)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = Xc @ Vt[:2].T
    if Z.shape[1] == 1:
        Z = np.concatenate([Z, np.zeros((Z.shape[0], 1), dtype=Z.dtype)], axis=1)
    return Z[:, :2].astype(np.float32)


def make_color_cycle(n: int) -> List[str]:
    base = [
        "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
        "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan",
    ]
    return [base[i % len(base)] for i in range(n)]


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

@dataclass
class MotifInfo:
    motif_id: str
    label: str
    strength: float
    stability_score: float
    members: List[int]
    centroid: np.ndarray

    @property
    def density(self) -> float:
        return float(min(1.0, np.log1p(max(0, len(self.members))) / np.log(33.0)))

    @property
    def gravity_bonus(self) -> float:
        return float(
            0.10 * np.clip(self.strength, 0.0, 1.0)
            + 0.07 * self.density
            + 0.05 * np.clip(self.stability_score, 0.0, 1.0)
        )


def load_motifs(data_dir: str, workspace: str, domain: str) -> Dict[str, MotifInfo]:
    path = os.path.join(data_dir, "workspaces", workspace, "domains", domain, "motifs.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    out: Dict[str, MotifInfo] = {}
    for mid, md in obj.get("motifs", {}).items():
        centroid_raw = md.get("centroid", [])
        if not centroid_raw:
            continue
        out[mid] = MotifInfo(
            motif_id=mid,
            label=str(md.get("label", mid)),
            strength=float(md.get("strength", 0.0)),
            stability_score=float(md.get("stability_score", 0.0)),
            members=[int(x) for x in md.get("members", [])],
            centroid=_unit(np.asarray(centroid_raw, dtype=np.float32)),
        )
    return out


def load_member_embeddings(data_dir: str, workspace: str, agent: str,
                            motifs: Dict[str, MotifInfo]) -> Tuple[List[dict], int]:
    """Load member embeddings — tries shard storage first, then legacy emb_<eid>.npy."""
    rows = []
    dim = 0

    # Try shard-based loading
    private_dir = os.path.join(data_dir, "workspaces", workspace, "agents", agent, "private")
    emb_dir = os.path.join(private_dir, "embeddings")
    shard_reader = None
    nodes_by_eid: Dict[int, dict] = {}

    try:
        from torment_service.embedding_store import EmbeddingShardReader, load_embedding
        if os.path.isdir(emb_dir):
            shard_reader = EmbeddingShardReader(emb_dir)

        # Load node payloads for embedding_ref lookup
        nodes_path = os.path.join(private_dir, "nodes.jsonl")
        if os.path.exists(nodes_path):
            with open(nodes_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        eid = rec.get("eid")
                        if eid is not None:
                            nodes_by_eid[int(eid)] = rec.get("payload", {})
                    except Exception:
                        continue
    except ImportError:
        pass

    all_eids = set()
    for m in motifs.values():
        all_eids.update(m.members)

    for mid, m in motifs.items():
        for eid in m.members:
            emb = None

            # Try shard loading via payload
            if shard_reader and eid in nodes_by_eid:
                payload = nodes_by_eid[eid]
                try:
                    from torment_service.embedding_store import load_embedding
                    emb_vec = load_embedding(eid, payload, shard_reader, private_dir)
                    if emb_vec is not None:
                        emb = _unit(emb_vec)
                except Exception:
                    pass

            # Fallback: legacy file
            if emb is None:
                for search_dir in [private_dir, data_dir]:
                    p = os.path.join(search_dir, f"emb_{int(eid)}.npy")
                    if os.path.exists(p):
                        try:
                            emb = _unit(np.load(p))
                        except Exception:
                            pass
                        break

            if emb is not None:
                dim = max(dim, int(emb.shape[0]))
                rows.append({"eid": int(eid), "motif_id": mid, "label": m.label, "emb": emb})

    return rows, dim


def load_character_state(data_dir: str, workspace: str, agent: str) -> Optional[dict]:
    path = os.path.join(data_dir, "workspaces", workspace, "agents", agent, "character_state.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_trajectory_index(data_dir: str, workspace: str, agent: str) -> List[dict]:
    """Load trajectory data from SQLite index."""
    db_path = os.path.join(
        data_dir, "workspaces", workspace, "agents", agent,
        "index", "memory_index.sqlite",
    )
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT step, eid, coh, phi_index, corridor_deg, pos_x, pos_y, pos_z "
            "FROM trajectory_index ORDER BY step"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def load_core_events(data_dir: str, workspace: str, agent: str) -> List[dict]:
    """Load memory creation events from SQLite index."""
    db_path = os.path.join(
        data_dir, "workspaces", workspace, "agents", agent,
        "index", "memory_index.sqlite",
    )
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT event_type, step, eid, coherence, timestamp "
            "FROM core_events ORDER BY step"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Layer 1: Basin Landscape
# ---------------------------------------------------------------------------

def _sparse_notice(ax, msg: str):
    """Put a centered notice on an axis when data is insufficient."""
    ax.text(0.5, 0.5, msg, transform=ax.transAxes, fontsize=12,
            ha="center", va="center", alpha=0.5,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))


def plot_basin_native(ax, field_rows: List[dict], seed_motif_id: Optional[str] = None):
    """Left panel — phi vs kappa colored by tension, shaped by role."""
    if not field_rows:
        _sparse_notice(ax, "No motifs found\nNeed at least one motif for basin landscape")
        ax.set_title("Physics Topology", fontsize=10, fontweight="bold")
        return

    role_markers = {"basin": "o", "ridge": "^", "plateau": "s"}
    tension_vals = [float(r.get("tension", 0)) for r in field_rows]
    norm = Normalize(vmin=min(tension_vals) - 0.01, vmax=max(tension_vals) + 0.01)
    cmap = plt.cm.viridis

    for r in field_rows:
        phi = float(r.get("phi", 0))
        kappa = float(r.get("kappa", 0))
        tension = float(r.get("tension", 0))
        role = str(r.get("role", "plateau"))
        members = int(r.get("members", 1))
        strength = float(r.get("strength", 0.1))
        mid = r.get("motif_id", "")

        marker = role_markers.get(role, "o")
        size = max(80, min(600, members * strength * 500))
        color = cmap(norm(tension))

        is_seed = (mid == seed_motif_id) if seed_motif_id else False

        ax.scatter(phi, kappa, s=size, c=[color], marker=marker,
                   edgecolors="gold" if is_seed else "black",
                   linewidths=2.5 if is_seed else 0.8,
                   zorder=10 if is_seed else 5, alpha=0.85)

        # Label
        label_text = r.get("label", mid)
        if len(label_text) > 20:
            label_text = label_text[:18] + ".."
        suffix = f"\nn={members}"
        if is_seed:
            suffix += " [SEED]"
        ax.annotate(label_text + suffix, (phi, kappa),
                    fontsize=6.5, ha="center", va="bottom",
                    xytext=(0, 8), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.15", alpha=0.15, facecolor="white"))

    # Threshold lines
    ax.axhline(-0.015, color="blue", linewidth=0.6, linestyle="--", alpha=0.3, label="basin threshold")
    ax.axhline(0.015, color="red", linewidth=0.6, linestyle="--", alpha=0.3, label="ridge threshold")
    ax.axvline(0.0, color="gray", linewidth=0.4, linestyle=":", alpha=0.3)

    # Colorbar
    sm = ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("tension", fontsize=8)

    ax.set_xlabel("phi (reinforcement)", fontsize=9)
    ax.set_ylabel("kappa (curvature)", fontsize=9)
    ax.set_title("Physics Topology\nwhere the engine sees attractors", fontsize=10, fontweight="bold")
    ax.grid(alpha=0.12)
    ax.legend(fontsize=7, loc="lower right", framealpha=0.6)


def plot_basin_pca(ax, motifs: Dict[str, MotifInfo], member_rows: List[dict],
                   field_by_mid: Dict[str, dict], seed_motif_id: Optional[str] = None):
    """Right panel — PCA embedding projection with gravity circles."""
    if not member_rows and not motifs:
        _sparse_notice(ax, "No embeddings found\nNeed member embeddings for PCA view")
        ax.set_title("Semantic Space", fontsize=10, fontweight="bold")
        return

    motif_ids = list(motifs.keys())
    colors = make_color_cycle(len(motif_ids))
    color_by_mid = {mid: colors[i] for i, mid in enumerate(motif_ids)}

    # Build PCA input
    if member_rows:
        member_X = np.stack([r["emb"] for r in member_rows], axis=0).astype(np.float32)
    else:
        member_X = np.zeros((0, motifs[motif_ids[0]].centroid.shape[0]), dtype=np.float32) if motif_ids else np.zeros((0, 2), dtype=np.float32)

    centroid_X = np.stack([m.centroid for m in motifs.values()], axis=0).astype(np.float32) if motifs else np.zeros((0, member_X.shape[1] if member_X.size else 2), dtype=np.float32)

    if member_X.shape[0] + centroid_X.shape[0] < 2:
        _sparse_notice(ax, "Not enough data for PCA\nNeed at least 2 embeddings")
        ax.set_title("Semantic Space", fontsize=10, fontweight="bold")
        return

    all_X = np.concatenate([member_X, centroid_X], axis=0)
    Z = _pca_2d(all_X)
    member_Z = Z[:len(member_rows)]
    centroid_Z = Z[len(member_rows):]
    centroid_by_mid = {mid: centroid_Z[i] for i, mid in enumerate(motif_ids)}

    # Scatter member points
    for mid in motif_ids:
        pts = np.asarray(
            [member_Z[i] for i, r in enumerate(member_rows) if r["motif_id"] == mid],
            dtype=np.float32,
        )
        if pts.size == 0:
            continue
        ax.scatter(pts[:, 0], pts[:, 1], s=18, alpha=0.40,
                   color=color_by_mid[mid], zorder=3)

    # Centroids + gravity circles
    for mid in motif_ids:
        m = motifs[mid]
        cz = centroid_by_mid[mid]
        is_seed = (mid == seed_motif_id) if seed_motif_id else False

        radius = 0.08 + 0.28 * m.gravity_bonus
        circ = plt.Circle((float(cz[0]), float(cz[1])), radius=radius,
                          fill=False, linewidth=1.8 if is_seed else 1.2,
                          alpha=0.6, color="gold" if is_seed else color_by_mid[mid])
        ax.add_patch(circ)

        star_color = "gold" if is_seed else color_by_mid[mid]
        ax.scatter([cz[0]], [cz[1]], marker="*", s=320 if is_seed else 220,
                   color=star_color, edgecolors="black", linewidths=0.8, zorder=10)

        # Role annotation
        field_info = field_by_mid.get(mid, {})
        role = field_info.get("role", "")
        role_tag = f" ({role})" if role else ""
        seed_tag = " [SEED]" if is_seed else ""

        label_text = m.label if len(m.label) <= 20 else m.label[:18] + ".."
        ax.text(float(cz[0]) + 0.02, float(cz[1]) + 0.02,
                f"{label_text}{role_tag}{seed_tag}\nn={len(m.members)} s={m.strength:.2f}",
                fontsize=6.5, bbox=dict(boxstyle="round,pad=0.15", alpha=0.15))

    ax.axhline(0.0, linewidth=0.4, alpha=0.2)
    ax.axvline(0.0, linewidth=0.4, alpha=0.2)
    ax.set_xlabel("PCA-1", fontsize=9)
    ax.set_ylabel("PCA-2", fontsize=9)
    ax.set_title("Semantic Space\nwhere memories actually cluster", fontsize=10, fontweight="bold")
    ax.grid(alpha=0.12)


# ---------------------------------------------------------------------------
# Layer 2: Phase Space Dynamics
# ---------------------------------------------------------------------------

def plot_phase_space(ax, trajectory_rows: List[dict]):
    """Phase space: phi_index vs coherence, colored by corridor proximity."""
    if len(trajectory_rows) < 3:
        _sparse_notice(ax, "Needs more conversation data\n(< 3 trajectory points)")
        ax.set_title("Phase Space Dynamics", fontsize=10, fontweight="bold")
        return

    steps = [r["step"] for r in trajectory_rows]
    phi_idx = [r["phi_index"] for r in trajectory_rows]
    coh = [r["coh"] for r in trajectory_rows]
    corr_deg = [r.get("corridor_deg", 0.0) or 0.0 for r in trajectory_rows]

    # Normalize corridor_deg for coloring
    corr_arr = np.array(corr_deg)
    corr_norm = np.clip(corr_arr, -1, 1)

    # Create diverging colormap: red (low) → white → green (high corridor)
    from matplotlib.colors import LinearSegmentedColormap
    corr_cmap = LinearSegmentedColormap.from_list(
        "corridor", ["#d62728", "#f0f0f0", "#2ca02c"]
    )
    norm = Normalize(vmin=-0.5, vmax=0.5)

    # Trajectory line (thin, connecting)
    ax.plot(phi_idx, coh, color="gray", linewidth=0.6, alpha=0.4, zorder=2)

    # Scatter colored by corridor_deg
    sc = ax.scatter(phi_idx, coh, c=corr_norm, cmap=corr_cmap, norm=norm,
                    s=50, edgecolors="black", linewidths=0.4, zorder=5, alpha=0.85)

    # Mark latest point
    ax.scatter([phi_idx[-1]], [coh[-1]], s=150, marker="D", color="gold",
               edgecolors="black", linewidths=1.2, zorder=11, label="current")

    # Mark first point
    ax.scatter([phi_idx[0]], [coh[0]], s=100, marker="o", color="white",
               edgecolors="black", linewidths=1.2, zorder=10, label="start")

    # Step annotations on a few key points
    n = len(steps)
    for idx in [0, n // 2, n - 1]:
        ax.annotate(f"s{steps[idx]}", (phi_idx[idx], coh[idx]),
                    fontsize=6, ha="center", va="bottom",
                    xytext=(0, 6), textcoords="offset points", alpha=0.6)

    cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label("corridor_deg", fontsize=8)

    ax.set_xlabel("phi_index (D24 sector)", fontsize=9)
    ax.set_ylabel("coherence", fontsize=9)
    ax.set_title("Phase Space Dynamics\ntrajectory through D24 sectors", fontsize=10, fontweight="bold")
    ax.set_xticks(range(12))
    ax.grid(alpha=0.15)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.6)


# ---------------------------------------------------------------------------
# Layer 3: Drift + Identity Timeline
# ---------------------------------------------------------------------------

def plot_timeline(axes, char_state: Optional[dict], core_events: List[dict],
                  trajectory_rows: List[dict]):
    """Three-track timeline: drift, memory events, coherence/corridor."""
    ax_drift, ax_events, ax_coh = axes

    # --- Track A: Drift Score ---
    drift_history = []
    if char_state and "drift_history" in char_state:
        drift_history = char_state["drift_history"]

    if len(drift_history) >= 2:
        steps_d = [h[0] for h in drift_history]
        scores_d = [h[1] for h in drift_history]
        ax_drift.plot(steps_d, scores_d, color="tab:blue", linewidth=1.5, marker="o", markersize=3)
        ax_drift.fill_between(steps_d, -0.35, 0.35, alpha=0.08, color="green", label="safe zone")
        ax_drift.axhline(0.0, color="gray", linewidth=0.5, linestyle=":")
    elif len(drift_history) == 1:
        s, sc = drift_history[0]
        ax_drift.scatter([s], [sc], color="tab:blue", s=60, zorder=5)
        ax_drift.fill_between([s - 100, s + 100], -0.35, 0.35, alpha=0.08, color="green")
        ax_drift.annotate(f"drift={sc:.2f}", (s, sc), fontsize=8, ha="center",
                          xytext=(0, 10), textcoords="offset points")
    else:
        _sparse_notice(ax_drift, "No drift history yet")

    ax_drift.set_ylabel("drift score", fontsize=8)
    ax_drift.set_title("Drift Score", fontsize=9, fontweight="bold")
    ax_drift.set_ylim(-1.1, 1.1)
    ax_drift.grid(alpha=0.12)

    # --- Track B: Memory Events ---
    if core_events:
        event_steps = [e["step"] for e in core_events]
        event_types = [e["event_type"] for e in core_events]
        type_colors = {
            "MEMORY_CREATE": "tab:blue",
            "MEMORY_UPDATE": "tab:orange",
            "MEMORY_DECAY": "tab:red",
        }
        for i, (s, t) in enumerate(zip(event_steps, event_types)):
            c = type_colors.get(t, "gray")
            ax_events.bar(s, 1, width=max(1, (max(event_steps) - min(event_steps)) / 50),
                          color=c, alpha=0.7)

        # Legend from unique types
        for t in set(event_types):
            ax_events.bar([], [], color=type_colors.get(t, "gray"), label=t)
        ax_events.legend(fontsize=6, loc="upper right", framealpha=0.6)
    else:
        _sparse_notice(ax_events, "No memory events in index")

    ax_events.set_ylabel("events", fontsize=8)
    ax_events.set_title("Memory Events", fontsize=9, fontweight="bold")
    ax_events.grid(alpha=0.12)

    # --- Track C: Coherence + Corridor ---
    if len(trajectory_rows) >= 2:
        steps_t = [r["step"] for r in trajectory_rows]
        coh_vals = [r["coh"] for r in trajectory_rows]
        corr_vals = [r.get("corridor_deg", 0.0) or 0.0 for r in trajectory_rows]

        ax_coh.plot(steps_t, coh_vals, color="tab:blue", linewidth=1.2, label="coherence")
        ax_coh.fill_between(steps_t, 0, corr_vals, alpha=0.25, color="green", label="corridor_deg")
        ax_coh.legend(fontsize=6, loc="upper right", framealpha=0.6)
    else:
        _sparse_notice(ax_coh, "Needs more trajectory data")

    ax_coh.set_ylabel("value", fontsize=8)
    ax_coh.set_xlabel("step", fontsize=9)
    ax_coh.set_title("Coherence & Corridor", fontsize=9, fontweight="bold")
    ax_coh.grid(alpha=0.12)


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def generate_visualization(
    data_dir: str,
    workspace: str,
    agent: str,
    domain: str,
    out_dir: str,
    layers: str = "all",
    dpi: int = 180,
    title: str = "",
) -> str:
    """Generate the multi-panel attractor visualization. Returns PNG path."""

    os.makedirs(out_dir, exist_ok=True)
    show_layers = set(layers.split(",")) if layers != "all" else {"basin", "orbits", "timeline"}

    # --- Load data ---
    motifs = load_motifs(data_dir, workspace, domain)

    # Compute coherence field
    motif_rows_for_field = []
    for mid, m in motifs.items():
        motif_rows_for_field.append({
            "motif_id": mid, "label": m.label,
            "centroid": list(m.centroid), "strength": m.strength,
            "stability_score": m.stability_score, "members": m.members,
        })
    field_rows = compute_coherence_field(motif_rows_for_field) if motif_rows_for_field else []
    field_by_mid = {r["motif_id"]: r for r in field_rows}

    # Load embeddings for PCA
    member_rows, emb_dim = load_member_embeddings(data_dir, workspace, agent, motifs)

    # Character state
    char_state = load_character_state(data_dir, workspace, agent)
    seed_motif_id = None
    if char_state:
        seed_id = char_state.get("seed_id", "")
        # Find motif that contains seed memories
        for mid, m in motifs.items():
            if "seed" in m.label.lower() or mid.endswith("0001"):
                seed_motif_id = mid
                break

    # Trajectory + events from SQLite
    trajectory_rows = load_trajectory_index(data_dir, workspace, agent)
    core_events = load_core_events(data_dir, workspace, agent)

    # --- Determine layout ---
    n_layers = len(show_layers)
    if n_layers == 0:
        show_layers = {"basin", "orbits", "timeline"}
        n_layers = 3

    layer_order = [l for l in ["basin", "orbits", "timeline"] if l in show_layers]
    height_ratios = []
    for l in layer_order:
        if l == "basin":
            height_ratios.append(4)
        elif l == "orbits":
            height_ratios.append(3)
        elif l == "timeline":
            height_ratios.append(4)

    fig_height = sum(height_ratios) * 2.2
    fig = plt.figure(figsize=(16, fig_height))
    gs_main = gridspec.GridSpec(len(layer_order), 1, height_ratios=height_ratios,
                                 hspace=0.35, figure=fig)

    plot_title = title or f"TORMENT Attractor Visualization — {workspace} / {agent} / {domain}"
    fig.suptitle(plot_title, fontsize=13, fontweight="bold", y=0.98)

    layer_idx = 0

    # --- Layer 1: Basin Landscape ---
    if "basin" in show_layers:
        gs_basin = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs_main[layer_idx],
                                                     wspace=0.30)
        ax_native = fig.add_subplot(gs_basin[0])
        ax_pca = fig.add_subplot(gs_basin[1])

        plot_basin_native(ax_native, field_rows, seed_motif_id)
        plot_basin_pca(ax_pca, motifs, member_rows, field_by_mid, seed_motif_id)
        layer_idx += 1

    # --- Layer 2: Phase Space ---
    if "orbits" in show_layers:
        ax_phase = fig.add_subplot(gs_main[layer_idx])
        plot_phase_space(ax_phase, trajectory_rows)
        layer_idx += 1

    # --- Layer 3: Timeline ---
    if "timeline" in show_layers:
        gs_time = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs_main[layer_idx],
                                                    hspace=0.35)
        ax_drift = fig.add_subplot(gs_time[0])
        ax_events = fig.add_subplot(gs_time[1], sharex=ax_drift)
        ax_coh = fig.add_subplot(gs_time[2], sharex=ax_drift)

        plot_timeline([ax_drift, ax_events, ax_coh], char_state, core_events, trajectory_rows)
        layer_idx += 1

    # --- Save ---
    png_name = f"attractors_{workspace}_{domain}_{agent}.png"
    png_path = os.path.join(out_dir, png_name)
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # --- CSV summary ---
    csv_name = f"attractors_{workspace}_{domain}_{agent}_summary.csv"
    csv_path = os.path.join(out_dir, csv_name)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "motif_id", "label", "members", "strength", "stability_score",
            "density", "gravity_bonus", "phi", "kappa", "tension", "role",
        ])
        w.writeheader()
        for r in field_rows:
            mid = r["motif_id"]
            m = motifs.get(mid)
            w.writerow({
                "motif_id": mid,
                "label": r.get("label", ""),
                "members": r.get("members", 0),
                "strength": f"{r.get('strength', 0):.4f}",
                "stability_score": f"{r.get('stability_score', 0):.4f}",
                "density": f"{r.get('density', 0):.4f}",
                "gravity_bonus": f"{m.gravity_bonus:.4f}" if m else "0.0000",
                "phi": f"{r.get('phi', 0):.4f}",
                "kappa": f"{r.get('kappa', 0):.6f}",
                "tension": f"{r.get('tension', 0):.4f}",
                "role": r.get("role", ""),
            })

    print(f"Wrote: {png_path}")
    print(f"Wrote: {csv_path}")
    return png_path


def main():
    ap = argparse.ArgumentParser(description="TORMENT Attractor Visualization")
    ap.add_argument("--data-dir", required=True, help="TORMENT data directory")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--domain", default="research")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--layers", default="all", help="Comma-separated: basin,orbits,timeline or all")
    ap.add_argument("--dpi", type=int, default=180)
    ap.add_argument("--title", default="")
    args = ap.parse_args()

    generate_visualization(
        data_dir=args.data_dir,
        workspace=args.workspace,
        agent=args.agent,
        domain=args.domain,
        out_dir=args.out,
        layers=args.layers,
        dpi=args.dpi,
        title=args.title,
    )


if __name__ == "__main__":
    main()
