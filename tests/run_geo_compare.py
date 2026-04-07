#!/usr/bin/env python3
"""Geometric Modulation Comparison Harness — TORMENT stance layer.

Runs a fixed set of inputs through multiple named geometric contexts and
prints a clear comparison showing how kernel state nudges stance decisions.

This does NOT change production logic.  It is a read-only diagnostic tool.

Usage (offline, no server required):
    python tests/run_geo_compare.py
    python tests/run_geo_compare.py --json          # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import sys
import os

# Ensure torment_service is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import GeometricStanceContext

# ── Named geometric contexts ───────────────────────────────────────────

GEO_PROFILES = {
    "neutral": GeometricStanceContext(
        coherence=0.5, stability=0.5, identity_lock=0.5,
        ambiguity_tolerance=0.5, social_resonance=0.5,
    ),
    "stable_locked": GeometricStanceContext(
        coherence=0.92, stability=0.90, identity_lock=0.95,
        ambiguity_tolerance=0.80, social_resonance=0.50,
    ),
    "drifting_fragile": GeometricStanceContext(
        coherence=0.30, stability=0.15, identity_lock=0.10,
        ambiguity_tolerance=0.20, social_resonance=0.35,
    ),
    "socially_open": GeometricStanceContext(
        coherence=0.70, stability=0.60, identity_lock=0.50,
        ambiguity_tolerance=0.50, social_resonance=0.95,
    ),
    "ambiguity_tolerant": GeometricStanceContext(
        coherence=0.85, stability=0.70, identity_lock=0.60,
        ambiguity_tolerance=0.95, social_resonance=0.50,
    ),
    "extreme_low": GeometricStanceContext(
        coherence=0.0, stability=0.0, identity_lock=0.0,
        ambiguity_tolerance=0.0, social_resonance=0.0,
    ),
    "extreme_high": GeometricStanceContext(
        coherence=1.0, stability=1.0, identity_lock=1.0,
        ambiguity_tolerance=1.0, social_resonance=1.0,
    ),
    "none": None,  # baseline: no geometric context at all
}

# ── Test inputs ─────────────────────────────────────────────────────────

TEST_INPUTS = [
    {
        "label": "identity_ambiguous",
        "text": "identity maybe something",
        "why": "Identity-sensitive + high ambiguity → tests rule 4 (defer threshold modulated by identity_lock + stability)",
    },
    {
        "label": "ambiguous_no_question",
        "text": "maybe something",
        "why": "High ambiguity, no '?' → tests rule 5 (clarification threshold modulated by ambiguity_tolerance + coherence)",
    },
    {
        "label": "live_social_short",
        "text": "live audio",
        "why": "Live-social, 2 tokens → tests rule 6 (silence threshold modulated by social_resonance)",
    },
    {
        "label": "live_social_low_urgency",
        "text": "live audio what do you think about that topic",
        "why": "Live-social, low urgency → tests rule 7 (brevity threshold modulated by social_resonance)",
    },
    {
        "label": "governance_sensitive",
        "text": "Can you delete this protected identity memory and inspect governance state?",
        "why": "Governance-sensitive → should remain governed_redirect regardless of geometry (robustness check)",
    },
    {
        "label": "normal_direct",
        "text": "Hello there, how are you doing today?",
        "why": "Normal input → respond_now baseline; check geometry doesn't inadvertently flip it",
    },
    # ── Boundary probes: inputs engineered to sit near modulated thresholds ──
    {
        "label": "PROBE_ambiguity_near_060",
        "text": "kind of working",
        "why": "BOUNDARY: amb=0.55, threshold=0.60*amb_mod. At extreme_low (mod=0.85) → 0.51, should flip to ask_clarification",
    },
    {
        "label": "PROBE_live_social_3tok",
        "text": "live audio yo",
        "why": "BOUNDARY: 3 tokens, threshold=3*soc_mod. At socially_open (mod=1.135) → 3.405, should flip to silent_observe",
    },
    {
        "label": "PROBE_live_social_urgency",
        "text": "live space speak now about this urgent topic quickly",
        "why": "BOUNDARY: live-social + urgency near 0.3. Tests whether social_resonance widens the brevity window",
    },
]

CAPS_ON = {"contextual_abstention": True}


# ── Runner ──────────────────────────────────────────────────────────────

def run_comparison():
    ctl = ThinkingController()
    results = []

    for inp in TEST_INPUTS:
        input_results = {
            "label": inp["label"],
            "text": inp["text"],
            "why": inp["why"],
            "profiles": {},
        }

        for profile_name, geo in GEO_PROFILES.items():
            result = ctl.think(
                "default", "ryuki", inp["text"],
                capabilities=CAPS_ON,
                geometric_context=geo,
            )

            stance = result.stance
            mods = stance.context_factors.get("geo_modifiers", {}) if stance else {}

            input_results["profiles"][profile_name] = {
                "stance": stance.stance.value if stance else None,
                "confidence": round(stance.confidence, 3) if stance else None,
                "mode": result.mode_decision.chosen_mode.value,
                "action": result.action_decision.action.value,
                "geo_modifiers": {k: round(v, 4) for k, v in mods.items()} if mods else None,
            }

        results.append(input_results)

    return results


def print_table(results):
    profile_names = list(GEO_PROFILES.keys())

    for inp in results:
        print()
        print("=" * 90)
        print(f"  INPUT: {inp['label']}")
        print(f"  TEXT:  \"{inp['text']}\"")
        print(f"  WHY:   {inp['why']}")
        print("-" * 90)
        print(f"  {'Profile':<22} {'Stance':<22} {'Conf':>5}  {'Mode':<20} {'Action':<18}")
        print(f"  {'':22} {'id_mod':>8} {'amb_mod':>8} {'soc_mod':>8}")
        print("-" * 90)

        baseline_stance = inp["profiles"]["none"]["stance"]

        for pname in profile_names:
            p = inp["profiles"][pname]
            stance_str = p["stance"] or "—"
            conf_str = f"{p['confidence']:.2f}" if p["confidence"] is not None else "—"

            # Mark if stance differs from baseline
            marker = ""
            if p["stance"] != baseline_stance and pname != "none":
                marker = " ◄ SHIFTED"

            mods = p.get("geo_modifiers") or {}
            id_m = f"{mods.get('identity_defer', 1.0):.3f}" if mods else "  —  "
            amb_m = f"{mods.get('ambiguity_clarify', 1.0):.3f}" if mods else "  —  "
            soc_m = f"{mods.get('social_compact', 1.0):.3f}" if mods else "  —  "

            print(f"  {pname:<22} {stance_str:<22} {conf_str:>5}  {p['mode']:<20} {p['action']:<18}{marker}")
            print(f"  {'':22} {id_m:>8} {amb_m:>8} {soc_m:>8}")

    # ── Summary ──
    print()
    print("=" * 90)
    print("  SUMMARY")
    print("-" * 90)

    total_comparisons = 0
    shifted = 0
    governance_robust = True

    for inp in results:
        baseline_stance = inp["profiles"]["none"]["stance"]
        for pname in profile_names:
            if pname == "none":
                continue
            total_comparisons += 1
            if inp["profiles"][pname]["stance"] != baseline_stance:
                shifted += 1
            if inp["label"] == "governance_sensitive" and inp["profiles"][pname]["stance"] != "governed_redirect":
                governance_robust = False

    print(f"  Total input×profile comparisons: {total_comparisons}")
    print(f"  Stance shifts from baseline:     {shifted}")
    print(f"  Shift rate:                      {shifted}/{total_comparisons} = {shifted/total_comparisons*100:.1f}%")
    print(f"  Governance robustness:           {'PASS' if governance_robust else 'FAIL — governance weakened!'}")
    print()

    if shifted == 0:
        print("  ⚠  No stance shifts detected. Modulation may be too subtle for these inputs.")
        print("     This is expected if thresholds are borderline — the 0.85–1.15 band is intentionally tight.")
    elif shifted <= total_comparisons * 0.3:
        print("  ✓  Moderate shift rate — geometry nudges some decisions without overwhelming the scaffold.")
    else:
        print("  ⚠  High shift rate — geometry may be too aggressive. Review modifier bounds.")

    print()


def main():
    parser = argparse.ArgumentParser(description="Geometric modulation comparison harness")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of table")
    args = parser.parse_args()

    results = run_comparison()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_table(results)


if __name__ == "__main__":
    main()
