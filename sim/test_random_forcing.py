# sim/test_random_forcing.py
from __future__ import annotations
import os, argparse, random
import numpy as np

from torment_service.fabric import TormentFabric

# Reuse helpers from your other sim scripts if they exist.
# If these imports fail, copy the helper functions from test_metastability_dryrun.py
from sim.test_metastability_dryrun import get_tri_and_dbg, get_first, f


def make_text_bank():
    # Keep the same “rhythm texts” but add variety + noise phrases.
    base = [
        "short note",
        "This is a longer observation about recurring themes and structure in the workspace.",
        "Another longer observation about the same theme and the same objects and their relations.",
        "Completely different topic: cooking, cats, and a new plan for tomorrow morning.",
    ]
    extra = [
        "A new object appears. Link it to the old plan and store the relationship.",
        "Contradiction: earlier claim conflicts with new evidence. Resolve or annotate uncertainty.",
        "Edge case: missing context, but propose a repair action and log it.",
        "Novelty spike: introduce a new concept and see if the kernel overreacts.",
        "Reinforcement: repeat the same core theme with slightly different phrasing.",
        "Compression test: summarize the last 3 items into 1 sentence.",
    ]
    return base + extra


def jitter_text(rng: np.random.RandomState, s: str, p_jitter: float) -> str:
    if rng.rand() > p_jitter:
        return s
    # Tiny stochastic perturbation to break perfect periodicity
    suffix = f" [j{rng.randint(0,9999)}]"
    return s + suffix


def main(args=None):
    p = argparse.ArgumentParser()
    p.add_argument("--steps", type=int, default=5000)
    p.add_argument("--print-every", type=int, default=50)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--p-repeat", type=float, default=0.35, help="probability to reuse last chosen text")
    p.add_argument("--p-jitter", type=float, default=0.15, help="probability to perturb chosen text")
    args = p.parse_args(args)

    random.seed(int(args.seed))
    rng = np.random.RandomState(int(args.seed))

    os.environ["TORMENT_AFFECT_ENABLE"] = "0"

    fab = TormentFabric(data_dir="data")
    ws = "ws_random_forcing"
    agent = "agent_0"

    bank = make_text_bank()
    last = None

    for i in range(int(args.steps)):
        # Choose text with “sticky” randomness so we get bursts + novelty
        if last is not None and rng.rand() < float(args.p_repeat):
            text = last
        else:
            text = bank[int(rng.randint(0, len(bank)))]
        text = jitter_text(rng, text, float(args.p_jitter))
        last = text

        out = fab.ingest(workspace_id=ws, agent_id=agent, text=text, step=i, scope="private")

        if i % int(args.print_every) != 0:
            continue

        tri, dbg = get_tri_and_dbg(out)

        stored = bool(out.get("stored"))
        coh = f(get_first(dbg, ["coherence", "coh"], 0.0))
        z = f(get_first(dbg, ["z"], 0.0))

        in_corr = f(get_first(tri, ["in_corridor"], get_first(dbg, ["in_corridor"], 0.0)))
        surv = f(get_first(tri, ["survival_ema", "surv_ema", "survival_steps"],
                           get_first(dbg, ["survival_ema", "surv_ema", "survival_steps"], 0.0)))
        tear = f(get_first(tri, ["tearing_risk", "tear", "tear_score"],
                           get_first(dbg, ["tearing_risk", "tear"], 0.0)))
        phasev = f(get_first(tri, ["phase_var", "phasev"], get_first(dbg, ["phase_var", "phasev"], 0.0)))

        align = f(get_first(tri, ["tangent_align", "align"], get_first(dbg, ["tangent_align", "align"], 0.0)))
        aema = f(get_first(tri, ["align_ema", "aema"], get_first(dbg, ["align_ema", "aema"], 0.0)))

        disp = f(get_first(tri, ["disp", "phase_disp"], get_first(dbg, ["phase_disp", "phase_dispersion", "disp"], 0.0)))
        coh_phase = f(get_first(tri, ["coh_phase"], get_first(dbg, ["coh_phase"], 0.0)))

        wm = f(get_first(tri, ["write_mult", "wm"], 1.0))
        pm = f(get_first(tri, ["proposal_mult", "pm"], 1.0))
        bp = f(get_first(tri, ["bridge_p", "bp"], 0.08))
        bs = f(get_first(tri, ["bridge_sim", "bs"], 0.86))

        print(
            f"step={i:04d} stored={stored} "
            f"coh={coh:.6f} disp={disp:.3e} coh_phase={coh_phase:.6f} z={z:+.3f} "
            f"in_corr={in_corr:.1f} surv={surv:.3f} tear={tear:.3f} phasev={phasev:.3f} "
            f"align={align:+.3f} aema={aema:.3f} "
            f"wm={wm:.3f} pm={pm:.3f} bp={bp:.3f} bs={bs:.3f}"
        )


if __name__ == "__main__":
    main()