
"""
motif_field_viz.py

Visualize TORMENT motif basins / gravity wells for one workspace+domain.

What it does:
- loads motifs.json
- loads member embeddings (shard storage first, legacy emb_<eid>.npy fallback)
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
  --agent stress_agent ^
  --domain research ^
  --out outputs
"""
from __future__ import annotations
import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt

log = logging.getLogger(__name__)

# Path setup. `tools/` itself is added so the bare `from _viz_common`
# sibling import below works under both direct-script execution
# (`python tools/motif_field_viz.py ...`) and pytest collection
# from `torment_fabric/`. `tools/..` is added so any future
# `torment_service.*` import (none today, but matches sibling
# `visualize_attractors.py` for consistency) resolves. Idempotent.
TOOLS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(TOOLS_DIR, "..")

for path in (ROOT_DIR, TOOLS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from _viz_common import MotifInfo, _pca_2d, _unit, load_motifs, make_color_cycle


def load_member_embeddings(
    data_dir: str,
    workspace: str,
    agent: str,
    motifs: Dict[str, MotifInfo],
) -> Tuple[List[dict], int]:
    """Load member embeddings — shard storage first, legacy emb_<eid>.npy fallback.

    Returns (rows, max_dim) where each row is {eid, motif_id, label, emb}.
    """
    rows: List[dict] = []
    dim = 0

    private_dir = os.path.join(
        data_dir, "workspaces", workspace, "agents", agent, "private"
    )
    emb_dir = os.path.join(private_dir, "embeddings")
    shard_reader = None
    nodes_by_eid: Dict[int, dict] = {}

    try:
        from torment_service.embedding_store import (
            EmbeddingShardReader,
            load_embedding,
        )

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
                    except Exception as e:
                        log.debug("Failed to parse node record: %s", e)
                        continue
    except ImportError as e:
        log.debug("Could not load embedding_store; shard loading unavailable: %s", e)

    for mid, m in motifs.items():
        for eid in m.members:
            emb = None

            # Shard-first loading via canonical load_embedding
            if shard_reader is not None or nodes_by_eid:
                payload = nodes_by_eid.get(eid, {})
                try:
                    from torment_service.embedding_store import load_embedding

                    emb_vec = load_embedding(eid, payload, shard_reader, private_dir)
                    if emb_vec is not None:
                        emb = _unit(emb_vec)
                except Exception as e:
                    log.debug("Shard load failed for eid %d: %s", eid, e)

            # Legacy fallback: search data_dir root (original behavior)
            if emb is None:
                p = os.path.join(data_dir, f"emb_{int(eid)}.npy")
                if os.path.exists(p):
                    try:
                        emb = _unit(np.load(p))
                    except Exception:
                        continue

            if emb is not None:
                dim = max(dim, int(emb.shape[0]))
                rows.append({
                    "eid": int(eid),
                    "motif_id": mid,
                    "label": m.label,
                    "emb": emb,
                })

    return rows, dim



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="TORMENT data dir (e.g. data)")
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--agent", required=True, help="Agent name (for embedding shard lookup)")
    ap.add_argument("--domain", required=True)
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--title", default="")
    ap.add_argument("--max-points-per-motif", type=int, default=200)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    motifs = load_motifs(args.data_dir, args.workspace, args.domain)
    rows, dim = load_member_embeddings(args.data_dir, args.workspace, args.agent, motifs)

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
