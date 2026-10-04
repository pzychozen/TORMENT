import pandas as pd, numpy as np
df=pd.read_csv("outputs/wide_scan_triocta_ultra.csv")
print("vrec_mean finite fraction:", np.isfinite(df["vrec_mean"]).mean() if "vrec_mean" in df.columns else "NO vrec_mean")
print("stable fraction (flags):", (((df.get("has_nan",0)==0)&(df.get("omega_blowup",0)==0)&(df.get("kappa_runaway",0)==0)&(df.get("z_runaway",0)==0))).mean())
