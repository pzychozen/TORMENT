import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from torment_service.coherence_field import compute_coherence_field, summarize_coherence_field

MOTIF_FILE = ROOT / "data" / "workspaces" / "ws_stress_split1" / "domains" / "research" / "motifs.json"

print("Using motif file:", MOTIF_FILE)

with open(MOTIF_FILE, "r", encoding="utf-8") as f:
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