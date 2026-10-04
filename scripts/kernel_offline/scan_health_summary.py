import pandas as pd, numpy as np
df=pd.read_csv("outputs/wide_scan_triocta_ultra.csv")
required_columns = ("has_nan", "omega_blowup", "kappa_runaway", "z_runaway")
missing_columns = [name for name in required_columns if name not in df.columns]
if missing_columns:
    raise ValueError("Missing required health columns: " + ", ".join(missing_columns))
if df.empty:
    raise RuntimeError("No health data rows found")
print("vrec_mean finite fraction:", np.isfinite(df["vrec_mean"]).mean() if "vrec_mean" in df.columns else "NO vrec_mean")
print("stable fraction (flags):", (((df.get("has_nan",0)==0)&(df.get("omega_blowup",0)==0)&(df.get("kappa_runaway",0)==0)&(df.get("z_runaway",0)==0))).mean())
