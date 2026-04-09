
"""
motif_field_viz.py

Visualize TORMENT motif basins / gravity wells for one workspace+domain.

What it does:
- loads motifs.json
- loads member embeddings from emb_<eid>.npy
- projects embeddings + motif centroids to 2D with PCA (numpy SVD; no sklearn needed)
- draws:
    * member memory points, colored by motif
    * motif centroid stars
    * "gravity circles" sized by motif strength + density + stability
- writes:
    * motif_field_<workspace>_<domain>.png
    * motif_field_<workspace>_<domain>_summary.csv

Example:
python tools/motif_field_viz.py ^
  --data-dir data ^
  --workspace ws_stress_gw1 ^
  --domain research ^
  --out outputs
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)


def _pca_2d(X: np.ndarray) -> np.ndarray:
    """
    Simple PCA via SVD; returns Nx2.
    """
    if X.ndim != 2:
        raise ValueError("X must be 2D")
    if X.shape[0] == 0:
        return np.zeros((0, 2), dtype=np.float32)
    Xc = X - X.mean(axis=0, keepdims=True)
    if X.shape[0] == 1:
        return np.concatenate([np.zeros((1, 1)), np.zeros((1, 1))], axis=1)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = Xc @ Vt[:2].T
    if Z.shape[1] == 1:
        Z = np.concatenate([Z, np.zeros((Z.shape[0], 1), dtype=Z.dtype)], axis=1)
    return Z[:, :2].astype(np.float32)


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
        # Same saturation shape as the gravity-well patch.
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
        raise FileNotFoundError(f"motifs.json not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    out: Dict[str, MotifInfo] = {}
    for mid, md in obj.get("motifs", {}).items():
        out[mid] = MotifInfo(
            motif_id=mid,
            label=str(md.get("label", mid)),
            strength=float(md.get("strength", 0.0)),
            stability_score=float(md.get("stability_score", 0.0)),
            members=[int(x) for x in md.get("members", [])],
            centroid=_unit(np.asarray(md.get("centroid", []), dtype=np.float32)),
        )
    return out


def load_member_embeddings(data_dir: str, motifs: Dict[str, MotifInfo]) -> Tuple[List[dict], int]:
    """
    Returns list of rows:
      {eid, motif_id, label, emb}
    """
    rows = []
    dim = 0
    for mid, m in motifs.items():
        for eid in m.members:
            p = os.path.join(data_dir, f"emb_{int(eid)}.npy")
            if not os.path.exists(p):
                continue
            try:
                emb = _unit(np.load(p))
                dim = max(dim, int(emb.shape[0]))
                rows.append({
                    "eid": int(eid),
                    "motif_id": mid,
                    "label": m.label,
                    "emb": emb,
                })
            except Exception:
                continue
    return rows, dim


def make_color_cycle(n: int) -> List[str]:
    base = [
        "tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple",
        "tab:brown", "tab:pink", "tab:gray", "tab:olive", "tab:cyan"
    ]
    if n <= len(base):
        return base[:n]
    # repeat if more motifs than base colors
    return [base[i % len(base)] for i in range(n)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="TORMENT data dir (e.g. data)")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--title", default="")
    ap.add_argument("--max-points-per-motif", type=int, default=200)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    motifs = load_motifs(args.data_dir, args.workspace, args.domain)
    rows, dim = load_member_embeddings(args.data_dir, motifs)

    if not motifs:
        raise RuntimeError("No motifs found.")
    if not rows:
        raise RuntimeError("No member embeddings found for motif members.")

    # Subsample very large motifs to keep the plot readable.
    pruned = []
    rng = np.random.default_rng(1337)
    by_mid: Dict[str, List[dict]] = {}
    for r in rows:
        by_mid.setdefault(r["motif_id"], []).append(r)
    for mid, items in by_mid.items():
        if len(items) > args.max_points_per_motif:
            idx = rng.choice(len(items), size=args.max_points_per_motif, replace=False)
            pruned.extend([items[int(i)] for i in idx])
        else:
            pruned.extend(items)
    rows = pruned

    # Build projection matrix from both members + motif centroids.
    member_X = np.stack([r["emb"] for r in rows], axis=0).astype(np.float32)
    centroid_X = np.stack([m.centroid for m in motifs.values()], axis=0).astype(np.float32)
    all_X = np.concatenate([member_X, centroid_X], axis=0)
    Z = _pca_2d(all_X)
    member_Z = Z[:len(rows)]
    centroid_Z = Z[len(rows):]

    motif_ids = list(motifs.keys())
    colors = make_color_cycle(len(motif_ids))
    color_by_mid = {mid: colors[i] for i, mid in enumerate(motif_ids)}
    centroid_by_mid = {mid: centroid_Z[i] for i, mid in enumerate(motif_ids)}

    fig, ax = plt.subplots(figsize=(12, 9))

    # Scatter member points
    for mid in motif_ids:
        pts = np.asarray([member_Z[i] for i, r in enumerate(rows) if r["motif_id"] == mid], dtype=np.float32)
        if pts.size == 0:
            continue
        ax.scatter(
            pts[:, 0], pts[:, 1],
            s=18, alpha=0.45, label=f"{mid} members",
            color=color_by_mid[mid]
        )

    # Draw centroids + gravity circles
    for mid in motif_ids:
        m = motifs[mid]
        cz = centroid_by_mid[mid]
        radius = 0.08 + 0.28 * m.gravity_bonus  # plotting radius, not semantic radius
        circ = plt.Circle((float(cz[0]), float(cz[1])), radius=radius, fill=False, linewidth=1.8, alpha=0.5, color=color_by_mid[mid])
        ax.add_patch(circ)
        ax.scatter([cz[0]], [cz[1]], marker="*", s=280, color=color_by_mid[mid], edgecolors="black", linewidths=0.8, zorder=10)
        ax.text(
            float(cz[0]) + 0.02, float(cz[1]) + 0.02,
            f"{m.label}\n|n|={len(m.members)} s={m.strength:.2f} st={m.stability_score:.2f}",
            fontsize=8,
            bbox=dict(boxstyle="round,pad=0.2", alpha=0.12)
        )

    ax.axhline(0.0, linewidth=0.6, alpha=0.3)
    ax.axvline(0.0, linewidth=0.6, alpha=0.3)
    ax.set_xlabel("PCA-1")
    ax.set_ylabel("PCA-2")

    title = args.title.strip() or f"TORMENT motif field — workspace={args.workspace}, domain={args.domain}"
    ax.set_title(title)
    ax.grid(alpha=0.15)

    # Compact legend
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        # keep only first 8 labels to avoid clutter
        ax.legend(handles[:8], labels[:8], loc="upper right", fontsize=8, framealpha=0.8)

    png_path = os.path.join(args.out, f"motif_field_{args.workspace}_{args.domain}.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=180)
    plt.close(fig)

    # Summary CSV
    csv_path = os.path.join(args.out, f"motif_field_{args.workspace}_{args.domain}_summary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "motif_id", "label", "members", "strength", "stability_score", "density", "gravity_bonus",
            "pca_x", "pca_y"
        ])
        w.writeheader()
        for mid in motif_ids:
            m = motifs[mid]
            cz = centroid_by_mid[mid]
            w.writerow({
                "motif_id": mid,
                "label": m.label,
                "members": len(m.members),
                "strength": f"{m.strength:.6f}",
                "stability_score": f"{m.stability_score:.6f}",
                "density": f"{m.density:.6f}",
                "gravity_bonus": f"{m.gravity_bonus:.6f}",
                "pca_x": f"{float(cz[0]):.6f}",
                "pca_y": f"{float(cz[1]):.6f}",
            })

    print(f"Wrote: {png_path}")
    print(f"Wrote: {csv_path}")


if __name__ == "__main__":
    main()
