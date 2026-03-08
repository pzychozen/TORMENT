import pandas as pd
from pathlib import Path

# ---- config
BASE = Path("outputs_patch39_unified")
OUT_CSV = BASE / "trajectory_class_summary.csv"

# ---- load all trajectory CSVs
files = sorted(BASE.glob("lambda_*/seed_trajectories_seed*.csv"))
if not files:
    raise RuntimeError("No seed_trajectories_seed*.csv files found")

#---- read and concatenate
frames = []
for f in files:
    d = pd.read_csv(f)
    if len(d) > 0:
        frames.append(d)

df = pd.concat(frames, ignore_index=True)

# ---- basic cleanup
df = df[df["traj_class"].notna()]
df = df[df["traj_class"] != "unknown"]

# ---- counts
counts = (
    df.groupby(["lambda_phase", "channel", "traj_class"])
      .size()
      .reset_index(name="count")
)

# ---- totals per (lambda, channel)
totals = (
    counts.groupby(["lambda_phase", "channel"])["count"]
          .sum()
          .reset_index(name="total")
)

# ---- merge + fraction
summary = counts.merge(
    totals,
    on=["lambda_phase", "channel"],
    how="left"
)
summary["fraction"] = summary["count"] / summary["total"]

# ---- sort for readability
summary = summary.sort_values(
    ["lambda_phase", "channel", "traj_class"]
)

# ---- write output
summary.to_csv(OUT_CSV, index=False)

print(f"[OK] wrote {OUT_CSV}")
print(summary.head(48))

#---- pivot for easier reading
pivot = summary.pivot_table(
    index=["lambda_phase", "channel"],
    columns="traj_class",
    values="fraction",
    fill_value=0.0
)
print("\n=== Fraction table ===")
print(pivot)
