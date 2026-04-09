# -*- coding: utf-8 -*-
"""
DISP_SCALE Sensitivity Test
============================
Runs the same 9 ingest texts against 4 DISP_SCALE values (1.0, 1.2, 1.5, 2.0)
using separate workspaces so results don't interfere.

For each scale value, the server's kernel is patched at runtime via a special
endpoint... except there IS no such endpoint. Instead, this script does the
comparison OFFLINE using the kernel directly — no server needed.

It also tests against the LIVE server (current DISP_SCALE) for comparison.

Usage:
    python examples/test_disp_scale.py          # offline kernel comparison
    python examples/test_disp_scale.py --live    # also run against live server
"""
import sys
import os
import argparse

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np


# ─────────────────────────────────────────────────────
# The 9 ingest texts (same as agents.py Entity9 run)
# ─────────────────────────────────────────────────────
TEXTS = [
    "Atlas round1: Memory governance reliability depends on provenance retention, contamination resistance, drift stability, and decision consistency.",
    "Vanta round1: Memory governance reliability can fail through provenance loss, contamination, drift instability, and false decision consistency.",
    "Raven round1: Build evaluation for memory governance reliability with provenance logs, contamination checks, drift monitoring, and decision consistency scoring.",
    "Atlas round2: Compare governed memory versus unguided memory using provenance retention, contamination resistance, drift stability, and decision consistency.",
    "Vanta round2: Test whether governed memory versus unguided memory changes provenance retention, contamination resistance, drift stability, and decision consistency.",
    "Raven round2: Implement baseline versus governed memory runs and log provenance retention, contamination resistance, drift stability, and decision consistency.",
    "Atlas round3: Longitudinal evaluation should measure whether memory governance improves provenance retention, contamination resistance, drift stability, and decision consistency over time.",
    "Vanta round3: Longitudinal evaluation must detect whether lower variance hides worse provenance retention, contamination resistance, drift stability, or decision consistency.",
    "Raven round3: Produce dashboards for provenance retention, contamination resistance, drift stability, and decision consistency across governed and unguided memory runs.",
]

# Assign agents cyclically so we know which domain each text belongs to
AGENT_CYCLE = ["atlas", "vanta", "raven"]
DOMAIN_CYCLE = ["research", "research", "engineering"]

DISP_SCALES = [1.0, 1.2, 1.5, 2.0]

# Packet emission threshold
COH_THRESHOLD = 0.15


def run_offline_comparison():
    """Run the kernel directly with different DISP_SCALE values."""
    from torment_service.memory_kernel import TriOctaMemoryKernel
    from torment_service.kernel.model_core import ModelParams
    # Try to use the ST embedder if available
    embedder = None
    try:
        embed_provider = os.environ.get("TORMENT_EMBED_PROVIDER", "hash")
        if embed_provider == "st":
            from torment_service.embeddings import STEmbedding
            model_name = os.environ.get("TORMENT_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
            device = os.environ.get("TORMENT_EMBED_DEVICE", "cpu")
            embedder = STEmbedding(model=model_name, device=device)
            print(f"[INFO] Using SentenceTransformer embedder: {model_name}")
        else:
            print("[INFO] Using HashEmbedding (set TORMENT_EMBED_PROVIDER=st for production embedder)")
    except Exception as e:
        print(f"[INFO] Could not load ST embedder ({e}), falling back to HashEmbedding")

    print("\n" + "=" * 100)
    print("DISP_SCALE SENSITIVITY COMPARISON")
    print("=" * 100)

    # Summary table header
    summary_rows = []

    for scale in DISP_SCALES:
        print(f"\n{'─' * 100}")
        print(f"DISP_SCALE = {scale}")
        print(f"{'─' * 100}")

        kernel = TriOctaMemoryKernel(params=ModelParams(), embedder=embedder)
        kernel.DISP_SCALE = scale
        kernel.COH_SMOOTH = 0.70

        state = kernel.init_state("boot")
        cohs = []
        disps = []
        packets_emitted = 0
        deltas = []

        print(f"{'Text':<55} {'disp':>6} {'coh_ph':>7} {'coh_raw':>7} {'coh_ema':>7} {'delta':>7} {'packet':>6}")
        print("-" * 100)

        prev_coh = None
        for i, text in enumerate(TEXTS):
            state, signals, debug = kernel.process(state, text)
            d = debug["phase_disp"]
            cp = debug["coh_phase"]
            cr = debug["coh_raw"]
            ce = debug["coherence"]
            delta = ce - prev_coh if prev_coh is not None else 0.0
            prev_coh = ce
            emitted = ce >= COH_THRESHOLD
            if emitted:
                packets_emitted += 1

            cohs.append(ce)
            disps.append(d)
            deltas.append(delta)

            marker = "YES" if emitted else "no"
            symbol = ""
            if abs(delta) > 0.10:
                symbol = " ** insight"
            elif abs(delta) > 0.02:
                symbol = " * release"

            print(f"{text[:55]:<55} {d:6.3f} {cp:7.4f} {cr:7.4f} {ce:7.4f} {delta:+7.4f} {marker:>6}{symbol}")

        # Summary for this scale
        coh_min = min(cohs)
        coh_max = max(cohs)
        coh_mean = np.mean(cohs)
        disp_mean = np.mean(disps)
        max_delta = max(abs(d) for d in deltas)
        insight_count = sum(1 for d in deltas if abs(d) > 0.10)
        release_count = sum(1 for d in deltas if 0.02 < abs(d) <= 0.10)

        summary_rows.append({
            "scale": scale,
            "coh_min": coh_min,
            "coh_max": coh_max,
            "coh_mean": coh_mean,
            "disp_mean": disp_mean,
            "packets": packets_emitted,
            "total": len(TEXTS),
            "max_delta": max_delta,
            "insights": insight_count,
            "releases": release_count,
        })

        print(f"\n  Summary: coh=[{coh_min:.4f}, {coh_max:.4f}], mean={coh_mean:.4f}, "
              f"packets={packets_emitted}/{len(TEXTS)}, "
              f"max_delta={max_delta:.4f}, insights={insight_count}, releases={release_count}")

    # Final comparison table
    print("\n\n" + "=" * 100)
    print("COMPARISON SUMMARY")
    print("=" * 100)
    print(f"{'DISP_SCALE':>10} | {'coh_min':>8} | {'coh_max':>8} | {'coh_mean':>8} | {'packets':>10} | {'max_delta':>10} | {'insights':>8} | {'releases':>8}")
    print("-" * 100)
    for row in summary_rows:
        pkt_str = f"{row['packets']}/{row['total']}"
        print(f"{row['scale']:>10.1f} | {row['coh_min']:>8.4f} | {row['coh_max']:>8.4f} | {row['coh_mean']:>8.4f} | {pkt_str:>10} | {row['max_delta']:>10.4f} | {row['insights']:>8} | {row['releases']:>8}")

    print()
    print("INTERPRETATION:")
    print("  - 'packets' = ingests where coherence >= 0.15 (would emit a hivemind packet)")
    print("  - 'insights' = steps where |coherence_delta| > 0.10 (symbol system fires insight)")
    print("  - 'releases' = steps where 0.02 < |coherence_delta| <= 0.10 (symbol system fires release)")
    print("  - Lower DISP_SCALE = more sensitivity to dispersion = wider coherence range = more selective")
    print("  - Higher DISP_SCALE = less sensitivity = coherence stays high = everything passes")

    # Warn about embedder mismatch
    embedder_name = type(embedder).__name__ if embedder else "HashEmbedding"
    if embedder_name == "HashEmbedding":
        print("\n  *** WARNING: Offline test used HashEmbedding (sparse). ***")
        print("  *** ST embedder produces MUCH larger dispersion (~0.3-0.9 vs ~0.0-0.2). ***")
        print("  *** Recommendation below only applies to HashEmbedding. ***")
        print("  *** For ST production runs, use --live or set TORMENT_EMBED_PROVIDER=st ***")
    else:
        print(f"\n  Embedder: {embedder_name} (production-representative)")

    # Recommendation
    best = None
    for row in summary_rows:
        # We want: most packets pass, but not ALL (some selectivity),
        # and we want symbol transitions (insights + releases > 0)
        score = 0
        # Penalize if all packets pass (no selectivity)
        if row["packets"] < row["total"]:
            score += 2
        # Reward symbol activity
        score += row["insights"] * 3 + row["releases"] * 1
        # Reward wider coherence range
        score += (row["coh_max"] - row["coh_min"]) * 10
        # Penalize if too few packets
        if row["packets"] < row["total"] * 0.5:
            score -= 5
        row["_score"] = score
        if best is None or score > best["_score"]:
            best = row

    if best:
        print(f"\n  RECOMMENDED: DISP_SCALE = {best['scale']}")
        print(f"    Reason: coh range [{best['coh_min']:.3f}, {best['coh_max']:.3f}], "
              f"{best['packets']}/{best['total']} packets, "
              f"{best['insights']} insights, {best['releases']} releases")


def run_live_comparison():
    """Run against the live server to show current behavior."""
    import requests

    BASE = "http://127.0.0.1:8787"
    WS = "ScaleTest_live"

    print("\n\n" + "=" * 100)
    print(f"LIVE SERVER TEST (workspace={WS}, current DISP_SCALE)")
    print("=" * 100)

    # Health check
    try:
        health = requests.get(f"{BASE}/health", timeout=5).json()
        print(f"Server running, embedder={health.get('embedder', {}).get('provider', '?')}")
    except Exception as e:
        print(f"[ERROR] Cannot reach server: {e}")
        print("Start server with: python -m torment_service")
        return

    # Create workspace
    requests.post(f"{BASE}/workspace/create", json={
        "workspace_id": WS,
        "domains": ["research", "engineering"],
    }, timeout=10)

    # Create agents
    for aid in ["atlas", "vanta", "raven"]:
        requests.post(f"{BASE}/agent/create", json={
            "workspace_id": WS,
            "agent_id": aid,
            "seed": {
                "seed_text": f"Test agent {aid}",
                "seed_id": f"{aid}_v1",
                "coupling_mode": "propose",
                "coupling_strength": 0.70,
            },
        }, timeout=10)

    # Ingest and collect coherence
    print(f"\n{'Text':<55} {'disp':>6} {'coh':>7} {'strength':>9} {'stored':>6} {'packet_ok':>9}")
    print("-" * 100)

    cohs = []
    disps = []
    for i, text in enumerate(TEXTS):
        aid = AGENT_CYCLE[i % 3]
        domain = DOMAIN_CYCLE[i % 3]
        resp = requests.post(f"{BASE}/agent/ingest", json={
            "workspace_id": WS,
            "agent_id": aid,
            "text": text,
            "step": i + 1,
            "domain_id": domain,
        }, timeout=30).json()

        # Coherence lives in debug, not signals
        debug = resp.get("debug", {})
        signals = resp.get("signals", {})
        coh = float(debug.get("coherence", 0.0))
        disp = float(debug.get("phase_disp", 0.0))
        strength = float(signals.get("strength", 0.0))
        stored = resp.get("stored", False)
        cohs.append(coh)
        disps.append(disp)
        pkt_ok = "YES" if coh >= COH_THRESHOLD else "no"

        print(f"{text[:55]:<55} {disp:6.3f} {coh:7.4f} {strength:9.4f} {'Y' if stored else 'N':>6} {pkt_ok:>9}")

    status = requests.get(f"{BASE}/workspace/{WS}/collective/status", timeout=10).json()
    print(f"\nPackets emitted: {status.get('packet_count_total', 0)}")
    print(f"Convergence events: {status.get('event_count', 0)}")
    print(f"Coherence range: [{min(cohs):.4f}, {max(cohs):.4f}]")
    print(f"Dispersion range: [{min(disps):.4f}, {max(disps):.4f}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DISP_SCALE sensitivity test")
    parser.add_argument("--live", action="store_true", help="Also run against live server")
    args = parser.parse_args()

    run_offline_comparison()

    if args.live:
        run_live_comparison()
