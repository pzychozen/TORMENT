"""
run_coherence_field.py — diagnostic: compute and print the coherence field for a workspace/domain.

Usage:
    python tools/run_coherence_field.py --workspace ws_stress_split1 --domain research
    python tools/run_coherence_field.py  # defaults to ws_stress_split1 / research
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from torment_service.coherence_field import compute_coherence_field, summarize_coherence_field


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute and print coherence field for a workspace/domain")
    ap.add_argument("--data-dir", default=str(ROOT / "data"), help="TORMENT data directory (default: data/)")
    ap.add_argument("--workspace", default="ws_stress_split1", help="Workspace name (default: ws_stress_split1)")
    ap.add_argument("--domain", default="research", help="Domain name (default: research)")
    args = ap.parse_args()

    motif_file = Path(args.data_dir) / "workspaces" / args.workspace / "domains" / args.domain / "motifs.json"
    print("Using motif file:", motif_file)

    if not motif_file.exists():
        print(f"ERROR: motifs.json not found at {motif_file}", file=sys.stderr)
        sys.exit(1)

    with open(motif_file, "r", encoding="utf-8") as f:
        obj = json.load(f)

    motifs = []
    for motif_id, md in obj["motifs"].items():
        row = dict(md)
        row["motif_id"] = motif_id
        motifs.append(row)

    field = compute_coherence_field(motifs)
    summary = summarize_coherence_field(motifs)

    print("\nFIELD SUMMARY")
    print(summary)

    print("\nTOP MOTIFS")
    for m in field[:10]:
        print(
            m["motif_id"],
            m["role"],
            "phi=", round(m["phi"], 3),
            "kappa=", round(m["kappa"], 3),
            "tension=", round(m["tension"], 3),
            "members=", m["members"],
        )


if __name__ == "__main__":
    main()
