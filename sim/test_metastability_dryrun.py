import argparse
# sim/test_metastability_dryrun.py
import os, sys
from pathlib import Path

# Ensure project root is on sys.path BEFORE importing torment_service
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from torment_service.fabric import TormentFabric


def f(x, default=0.0) -> float:
    """Safe float coercion."""
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def get_tri_and_dbg(out: dict):
    dbg = (out.get("debug") or {})
    tri = out.get("tri_mod") or dbg.get("tri_mod") or {}
    return tri, dbg


def get_first(d: dict, keys, default=0.0):
    for k in keys:
        if k in d and d.get(k) is not None:
            return d.get(k)
    return default


def main(args=None):
    import os
    import numpy as np
    import random

    # args may be None when called programmatically
    seed = int(getattr(args, "seed", 123) or 123)
    random.seed(seed)
    np.random.seed(seed)

    os.environ["TORMENT_AFFECT_ENABLE"] = "0"

    fab = TormentFabric(data_dir="data")  # adjust if needed
    ws = "ws_meta_dryrun"
    agent = "agent_0"

    texts = [
        "short note",
        "This is a longer observation about recurring themes and structure in the workspace.",
        "Another longer observation about the same theme and the same objects and their relations.",
        "Completely different topic: cooking, cats, and a new plan for tomorrow morning.",
    ]

    # robust defaults (match your historical behavior)
    steps = int(getattr(args, "steps", 120) or 120)
    print_every = int(getattr(args, "print_every", 10) or 10)

    for i in range(steps):

        # Choose forcing mode FIRST
        if getattr(args, "random_text", False):
            text = random.choice(texts)
        else:
            text = texts[i % len(texts)]

        # Optional step tag (helps debugging but not required)
        text = text + f" | step={i}"

        # Now ingest
        out = fab.ingest(
            workspace_id=ws,
            agent_id=agent,
            text=text,
            step=i,
            scope="private",
        )

        # Only print on cadence
        if (i % print_every) != 0:
            continue

        tri, dbg = get_tri_and_dbg(out)
        stored = bool(out.get("stored"))

        coh = f(get_first(dbg, ["coherence", "coh"], 0.0))
        z = f(get_first(dbg, ["z"], 0.0))

        in_corr = f(get_first(tri, ["in_corridor"], get_first(dbg, ["in_corridor"], 0.0)))
        surv = f(get_first(
            tri,
            ["survival_ema", "surv_ema", "survival_steps"],
            get_first(dbg, ["survival_ema", "surv_ema", "survival_steps"], 0.0),
        ))
        tear = f(get_first(tri, ["tearing_risk", "tear", "tear_score"], get_first(dbg, ["tearing_risk", "tear"], 0.0)))
        phasev = f(get_first(tri, ["phase_var", "phasev"], get_first(dbg, ["phase_var", "phasev"], 0.0)))

        align = f(get_first(tri, ["tangent_align", "align"], get_first(dbg, ["tangent_align", "align"], 0.0)))
        aema = f(get_first(tri, ["align_ema", "aema"], get_first(dbg, ["align_ema", "aema"], 0.0)))

        wm = f(get_first(tri, ["write_mult", "wm"], 1.0))
        pm = f(get_first(tri, ["proposal_mult", "pm"], 1.0))
        bp = f(get_first(tri, ["bridge_p", "bp"], 0.08))
        bs = f(get_first(tri, ["bridge_sim", "bs"], 0.86))

        disp = f(get_first(tri, ["disp", "phase_disp"], get_first(dbg, ["phase_disp", "phase_dispersion", "disp"], 0.0)))
        coh_phase = f(get_first(tri, ["coh_phase"], get_first(dbg, ["coh_phase"], 0.0)))

        print(
            f"step={i:03d} stored={stored} "
            f"coh={coh:.6f} disp={disp:.3e} coh_phase={coh_phase:.6f} z={z:+.3f} "
            f"in_corr={in_corr:.1f} surv={surv:.3f} tear={tear:.3f} phasev={phasev:.3f} "
            f"align={align:+.3f} aema={aema:.3f} "
            f"wm={wm:.3f} pm={pm:.3f} bp={bp:.3f} bs={bs:.3f}"
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=120, help="number of steps")
    p.add_argument("--print-every", dest="print_every", type=int, default=10, help="print cadence")
    p.add_argument("--seed", type=int, default=123, help="rng seed")
    p.add_argument("--random-text", dest="random_text", action="store_true", help="randomly sample text each step instead of cycling")
    args = p.parse_args()
    main(args)
