"""TORMENT Brainvision - Matched prerecorded paired analyzer v0.1 (offline; descriptive-only).

Bounded offline ENGINEERING analyzer over explicitly supplied prerecorded .npz descriptor clips. It reuses
the EXISTING Brainvision descriptor preprocessing, descriptor extractors, control transforms, and SAG
computation WITHOUT modifying them, and reports matched paired responses of every descriptor family to
identical cached control transforms of the same non-overlapping 64-row blocks.

Feasibility standing: the nine existing prerecorded clips support only DESCRIPTIVE PAIRED ANALYSIS, not an
inferential benchmark (source provenance absent; clips 1-4 cannot be proven independent; content
categories are unreplicated singletons; nine clips are underpowered even under assumed independence;
shuffle disruption remains a major confound). The historical true-versus-shuffled diagnostic (the paired
classifier) is deliberately NOT reused here.

Standing (report metadata, not new authority): FORMAL HOLD active; Mode 0 active; verdict = HOLD;
bounded_experiment_ready = False; Brainvision_perceptual_claim_ready = False;
runtime_integration_authorized = False; new_scientific_claim_authorized = False.

Offline and quarantined: no torment_service import; no runtime integration; no camera / live capture; no
prompt / context / memory / action; no MCP; no render-body; no autonomy; no database; no carrier. Default
run writes nothing; a script invocation prints only. stdlib + numpy + existing research/brainvision modules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

import descriptors as _descriptors
import real_video as _real_video
import run_real_video_descriptors as _rvd
import run_real_video_sag_controls as _ctrl

ANALYZER_NAME = "TORMENT_BRAINVISION_PRERECORDED_PAIRED_ANALYSIS"
ANALYZER_VERSION = "v0.1"
ANALYSIS_TYPE = "DESCRIPTIVE_PAIRED_ENGINEERING_ANALYSIS"
SCHEMA = "torment.brainvision.prerecorded_paired_analysis"

GLOBAL_SEED = 20260716          # fixed global seed; stable integer seed derivation, not a randomized builtin
BLOCK_LEN = 64                  # non-overlapping 64-row blocks; incomplete trailing block is discarded
EPSILON = 1e-12                 # fixed normalization epsilon (recorded in the output)
NEAR_EPSILON_THRESHOLD = 1e-9   # diagnostic near-epsilon threshold (>= EPSILON); recorded in the output

# Reuse the existing control-transform semantics and their exact order (do not reinvent).
CONTROLS: Tuple[str, ...] = tuple(_ctrl.CONTROLS)
# Reuse the existing descriptor extractor set (do not duplicate their computation).
DESCRIPTOR_NAMES: Tuple[str, ...] = (
    "descriptor_only", "frame_diff", "plain_fft", "random_mapping",
    "psi", "rpsr", "psi_trs", "psi_trs_k0",
)

FEASIBILITY_STANDING = "DESCRIPTIVE PAIRED ANALYSIS"
FEASIBILITY_REASONS = (
    "source provenance is absent",
    "clips 1-4 cannot be proven independent",
    "content categories are unreplicated singletons",
    "nine clips are underpowered even if independence were assumed",
    "shuffle disruption remains a major confound",
)

LOCKS = {
    "FORMAL_HOLD_active": True,
    "Mode_0_active": True,
    "verdict": "HOLD",
    "bounded_experiment_ready": False,
    "Brainvision_perceptual_claim_ready": False,
    "runtime_integration_authorized": False,
    "new_scientific_claim_authorized": False,
}

# The one place inferential vocabulary is permitted: an explicit statement that those mechanisms are ABSENT.
NON_CLAIM = (
    "This is a descriptive paired engineering analysis. It contains no classifier, no train / test split, "
    "no fold, no cross_validation, no prediction, and no label, and it emits no balanced_accuracy: those "
    "inferential mechanisms are deliberately ABSENT. A positive matched recursive_delta means only greater "
    "normalized transform sensitivity of psi_trs than psi_trs_k0 on identical cached arrays; it is not "
    "better perception, not better temporal-order detection, not scientific superiority, and not a "
    "validated recursive-time contribution."
)

RECURSIVE_DELTA_STANDING = (
    "positive recursive_delta = greater normalized transform sensitivity of psi_trs than psi_trs_k0; "
    "negative recursive_delta = lower normalized transform sensitivity of psi_trs than psi_trs_k0. It does "
    "NOT mean better perception, better temporal-order detection, scientific superiority, or a validated "
    "recursive-time contribution."
)


# ----------------------------- small helpers -----------------------------
def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_array(arr: np.ndarray) -> str:
    a = np.ascontiguousarray(np.asarray(arr, dtype=np.float64))
    return _sha256_bytes(a.tobytes())


def _l2(vec: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(vec, dtype=float).reshape(-1)))


def _finite(values: Sequence[float]) -> List[float]:
    return [float(x) for x in values if np.isfinite(x)]


def _median(values: Sequence[float]) -> float:
    v = _finite(values)
    return float(np.median(v)) if v else float("nan")


def _iqr(values: Sequence[float]) -> float:
    v = _finite(values)
    if not v:
        return float("nan")
    q75, q25 = np.percentile(v, [75.0, 25.0])
    return float(q75 - q25)


def _mean(values: Sequence[float]) -> float:
    v = _finite(values)
    return float(np.mean(v)) if v else float("nan")


def _finite_counts(values: Sequence[float]) -> Tuple[int, int]:
    finite = sum(1 for x in values if np.isfinite(x))
    return finite, len(values) - finite


def _jsonable(obj):
    """Recursively convert to deterministic, JSON-safe native types. Non-finite floats become null."""
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    return obj


# ----------------------------- descriptor extractor set -----------------------------
def default_extractors() -> Dict[str, Callable[[np.ndarray], np.ndarray]]:
    """The EXISTING descriptor implementations, in a stable order (reuse, no duplication)."""
    existing = _rvd._extractors()
    return {name: existing[name] for name in DESCRIPTOR_NAMES}


# ----------------------------- block extraction -----------------------------
def extract_descriptor_field(frames: np.ndarray) -> np.ndarray:
    """Existing Brainvision preprocessing: frames -> low-level (T, C) descriptor field."""
    return _real_video.frames_to_low_level_descriptors(frames)


def non_overlapping_blocks(field: np.ndarray):
    """Split a (T, C) descriptor field into non-overlapping BLOCK_LEN-row blocks; discard the incomplete
    trailing block. Returns (raw_blocks, block_info). Blocks are non-overlapping WITHIN A CLIP ONLY; they
    are NOT described as statistically independent."""
    field = np.asarray(field, dtype=float)
    if field.ndim != 2:
        raise ValueError("descriptor field must be 2-D (T, C); got shape " + str(field.shape))
    total_rows = int(field.shape[0])
    n_blocks = total_rows // BLOCK_LEN
    raw_blocks = [field[i * BLOCK_LEN:(i + 1) * BLOCK_LEN] for i in range(n_blocks)]
    ranges = [[i * BLOCK_LEN, i * BLOCK_LEN + BLOCK_LEN] for i in range(n_blocks)]
    info = {
        "descriptor_row_count": total_rows,
        "complete_block_count": n_blocks,
        "discarded_trailing_rows": total_rows - n_blocks * BLOCK_LEN,
        "block_index_ranges": ranges,
        "block_len": BLOCK_LEN,
        "block_independence": "NON_OVERLAPPING_WITHIN_CLIP_ONLY_NOT_STATISTICALLY_INDEPENDENT",
    }
    return raw_blocks, info


# ----------------------------- deterministic transform cache -----------------------------
def _seed_sequence(clip_ordinal: int, block_ordinal: int, control_ordinal: int) -> np.random.SeedSequence:
    """Stable integer seed derivation from (global seed, clip, block, control); not a randomized builtin."""
    return np.random.SeedSequence(
        [int(GLOBAL_SEED), int(clip_ordinal), int(block_ordinal), int(control_ordinal)])


def _control_metadata(control: str, true_array: np.ndarray,
                      seed_sequence: np.random.SeedSequence) -> Dict[str, object]:
    """Record enough transform metadata to verify matching. A fresh rng with the SAME seed reproduces the
    single draw the existing transform_window consumes, so the recorded params reproduce the array (checked
    by _expected_from_metadata). The transform_window output itself remains authoritative."""
    T, C = true_array.shape
    rng = np.random.default_rng(seed_sequence)
    meta: Dict[str, object] = {"control": control}
    if control == "true":
        meta["kind"] = "identity"
    elif control == "time_reversed":
        meta["kind"] = "time_reversed"                       # deterministic; no rng draw
    elif control == "time_shuffled":
        perm = rng.permutation(T)
        meta["kind"] = "time_shuffled"
        meta["time_permutation"] = [int(x) for x in perm]
        meta["time_permutation_sha256"] = _sha256_bytes(np.asarray(perm, dtype=np.int64).tobytes())
    elif control == "circular_shift":
        offset = int(T // 3 + int(rng.integers(0, 5)))
        meta["kind"] = "circular_shift"
        meta["circular_shift_offset"] = offset
    elif control == "channel_shuffle":
        cperm = rng.permutation(C)
        meta["kind"] = "channel_shuffle"
        meta["channel_permutation"] = [int(x) for x in cperm]
        meta["channel_permutation_sha256"] = _sha256_bytes(np.asarray(cperm, dtype=np.int64).tobytes())
    elif control == "descriptor_dropout":
        dropped = int(rng.integers(0, C))
        mask = np.zeros(C, dtype=np.int64)
        mask[dropped] = 1
        meta["kind"] = "descriptor_dropout"
        meta["dropped_channel"] = dropped
        meta["dropout_mask"] = [int(x) for x in mask]
        meta["dropout_mask_sha256"] = _sha256_bytes(mask.tobytes())
    else:
        raise ValueError("unknown control: " + repr(control))
    return meta


def _expected_from_metadata(control: str, true_array: np.ndarray, meta: Dict[str, object]) -> np.ndarray:
    """Reconstruct the expected transformed array from recorded metadata (matching self-check only)."""
    if control == "true":
        return true_array
    if control == "time_reversed":
        return true_array[::-1]
    if control == "time_shuffled":
        return true_array[np.asarray(meta["time_permutation"], dtype=int)]
    if control == "circular_shift":
        return np.roll(true_array, int(meta["circular_shift_offset"]), axis=0)
    if control == "channel_shuffle":
        return true_array[:, np.asarray(meta["channel_permutation"], dtype=int)]
    if control == "descriptor_dropout":
        out = true_array.copy()
        out[:, int(meta["dropped_channel"])] = 0.0
        return out
    raise ValueError("unknown control: " + repr(control))


def build_block_cache(raw_block: np.ndarray, clip_ordinal: int, block_ordinal: int):
    """For one block, construct EACH cached transformed 64-row descriptor array EXACTLY ONCE (before any
    descriptor runs), using the existing transform_window semantics under a deterministic per-(clip, block,
    control) seed. Every descriptor family later receives these exact cached arrays; no descriptor advances
    its own random-number stream."""
    true_array = _descriptors._zscore(np.asarray(raw_block, dtype=float))
    cache: Dict[str, Dict[str, object]] = {}
    for control_ordinal, control in enumerate(CONTROLS):
        seed_sequence = _seed_sequence(clip_ordinal, block_ordinal, control_ordinal)
        rng = np.random.default_rng(seed_sequence)
        transformed = _ctrl.transform_window(true_array, control, rng)
        transformed = np.ascontiguousarray(np.asarray(transformed, dtype=float))
        meta = _control_metadata(control, true_array, seed_sequence)
        expected = np.ascontiguousarray(
            np.asarray(_expected_from_metadata(control, true_array, meta), dtype=float))
        cache[control] = {
            "array": transformed,
            "array_sha256": _sha256_array(transformed),
            "metadata": meta,
            "metadata_consistent": bool(
                transformed.shape == expected.shape
                and np.allclose(transformed, expected, rtol=1e-9, atol=1e-12)),
        }
    return true_array, cache


def compute_block_caches(field: np.ndarray, clip_ordinal: int):
    raw_blocks, info = non_overlapping_blocks(field)
    block_caches = []
    for block_ordinal, raw in enumerate(raw_blocks):
        true_array, cache = build_block_cache(raw, clip_ordinal, block_ordinal)
        block_caches.append({"true_array": true_array, "cache": cache})
    return block_caches, info


# ----------------------------- descriptor response analysis -----------------------------
def descriptor_responses(block_caches, extractors: Optional[Dict[str, Callable]] = None):
    """Apply each existing descriptor to every cached variant; report normalized paired responses.

    response_d(b, c) = L2(f_d(cached_control) - f_d(cached_true)) / max(L2(f_d(cached_true)), EPSILON).
    Every descriptor reads the SAME cached array for a given (block, control). The response formula is
    UNCHANGED; the raw numerator L2(f_c - f_true) and the raw denominator L2(f_true) are additionally
    captured for response-normalization diagnostics only. Returns (summary, per, raw) where
    raw = {'true_feature_norms': {name: [per-block L2(f_true)]},
           'raw_numerators': {name: {control: [per-block L2(f_c - f_true)]}}}."""
    extractors = extractors if extractors is not None else default_extractors()
    names = list(extractors.keys())
    per = {name: {c: [] for c in CONTROLS} for name in names}
    true_feature_norms = {name: [] for name in names}          # raw denominator per block (control-independent)
    raw_numerators = {name: {c: [] for c in CONTROLS} for name in names}
    for blk in block_caches:
        cache = blk["cache"]
        true_arr = cache["true"]["array"]
        for name, fn in extractors.items():
            f_true = np.asarray(fn(true_arr), dtype=float)
            raw_den = _l2(f_true)
            den = max(raw_den, EPSILON)
            true_feature_norms[name].append(float(raw_den))
            for control in CONTROLS:
                f_c = np.asarray(fn(cache[control]["array"]), dtype=float)
                num = _l2(f_c - f_true)
                per[name][control].append(num / den)
                raw_numerators[name][control].append(float(num))
    summary = {}
    for name in names:
        summary[name] = {}
        for control in CONTROLS:
            vals = per[name][control]
            finite, nonfinite = _finite_counts(vals)
            summary[name][control] = {
                "per_block": [float(x) for x in vals],
                "median": _median(vals),
                "iqr": _iqr(vals),
                "mean": _mean(vals),
                "finite_count": finite,
                "nonfinite_count": nonfinite,
            }
    raw = {"true_feature_norms": true_feature_norms, "raw_numerators": raw_numerators}
    return summary, per, raw


NEAR_EPSILON_CONVENTION = ("near_epsilon_count counts blocks with raw_denominator <= near_epsilon_threshold "
                           "and therefore includes every epsilon hit (near_epsilon_threshold >= epsilon)")


def build_normalization_diagnostics(clip_name, descriptor_names, controls, block_count,
                                    true_feature_norms, raw_numerators, per_responses):
    """Per-clip response-normalization diagnostics (structured; numeric fields stay JSON-safe numbers).

    Convention: an 'epsilon hit' is a block whose raw denominator L2(f_true) <= EPSILON; a 'near-epsilon
    hit' is a block whose raw denominator <= NEAR_EPSILON_THRESHOLD. Because NEAR_EPSILON_THRESHOLD >=
    EPSILON, near_epsilon_count INCLUDES every epsilon hit. The raw denominator is control-independent
    (L2(f_true)), so per-descriptor counts are taken over analyzed blocks. Diagnostics only; the response
    formula and every response value are unchanged."""
    per_descriptor = {}
    for name in descriptor_names:
        norms = true_feature_norms[name]
        per_descriptor[name] = {
            "min_true_feature_norm": float(min(norms)) if norms else float("nan"),
            "epsilon_hit_count": int(sum(1 for d in norms if d <= EPSILON)),
            "near_epsilon_count": int(sum(1 for d in norms if d <= NEAR_EPSILON_THRESHOLD)),
            "block_count": len(norms),
        }
    largest = None
    for b in range(block_count):                    # deterministic clip/block/control/descriptor order
        for control in controls:
            for name in descriptor_names:
                resp = per_responses[name][control][b]
                if not np.isfinite(resp):
                    continue
                if largest is None or resp > largest["normalized_response"]:
                    raw_den = float(true_feature_norms[name][b])
                    largest = {
                        "clip": clip_name,
                        "descriptor": name,
                        "control": control,
                        "block": int(b),
                        "normalized_response": float(resp),
                        "raw_numerator": float(raw_numerators[name][control][b]),
                        "raw_denominator": raw_den,
                        "effective_denominator": float(max(raw_den, EPSILON)),
                    }
    return {
        "epsilon": EPSILON,
        "near_epsilon_threshold": NEAR_EPSILON_THRESHOLD,
        "near_epsilon_convention": NEAR_EPSILON_CONVENTION,
        "per_descriptor": per_descriptor,
        "largest_response": largest,
        "epsilon_hit_total": int(sum(pd["epsilon_hit_count"] for pd in per_descriptor.values())),
        "near_epsilon_total": int(sum(pd["near_epsilon_count"] for pd in per_descriptor.values())),
    }


def aggregate_normalization_diagnostics(clip_results):
    """Top-level aggregate across all supplied clips. Per-clip diagnostics are retained separately, so
    per-clip auditability is preserved."""
    per_descriptor = {}
    epsilon_total = 0
    near_total = 0
    largest = None
    for cr in clip_results:
        diag = cr["response_normalization_diagnostics"]
        epsilon_total += diag["epsilon_hit_total"]
        near_total += diag["near_epsilon_total"]
        for name, pd in diag["per_descriptor"].items():
            agg = per_descriptor.setdefault(
                name, {"min_true_feature_norm": float("inf"), "epsilon_hit_count": 0,
                       "near_epsilon_count": 0, "block_count": 0})
            if np.isfinite(pd["min_true_feature_norm"]):
                agg["min_true_feature_norm"] = min(agg["min_true_feature_norm"],
                                                   pd["min_true_feature_norm"])
            agg["epsilon_hit_count"] += pd["epsilon_hit_count"]
            agg["near_epsilon_count"] += pd["near_epsilon_count"]
            agg["block_count"] += pd["block_count"]
        lr = diag["largest_response"]
        if lr is not None and (largest is None
                               or lr["normalized_response"] > largest["normalized_response"]):
            largest = dict(lr)
    for agg in per_descriptor.values():
        if not np.isfinite(agg["min_true_feature_norm"]):
            agg["min_true_feature_norm"] = float("nan")
    return {
        "epsilon": EPSILON,
        "near_epsilon_threshold": NEAR_EPSILON_THRESHOLD,
        "near_epsilon_convention": NEAR_EPSILON_CONVENTION,
        "per_descriptor": per_descriptor,
        "largest_response": largest,
        "epsilon_hit_total": int(epsilon_total),
        "near_epsilon_total": int(near_total),
    }


def control_ranks(response_summary):
    """Per-descriptor ranking of controls by per-clip median response (descriptor-internal only; response
    magnitudes are never compared across descriptor families)."""
    ranks = {}
    for name, per_control in response_summary.items():
        medians = [(c, per_control[c]["median"]) for c in CONTROLS]
        finite = [(c, m) for c, m in medians if np.isfinite(m)]
        nonfinite = [c for c, m in medians if not np.isfinite(m)]
        ordered = sorted(finite, key=lambda cm: (-cm[1], cm[0]))
        ranks[name] = {
            "by_median_desc": [{"control": c, "median": float(m)} for c, m in ordered],
            "nonfinite_controls": nonfinite,
            "ties": _detect_ties(finite),
        }
    return ranks


def recursive_delta(per_responses):
    """Matched psi_trs vs psi_trs_k0 on identical cached arrays: delta = response_psi_trs - response_psi_trs_k0."""
    psi = per_responses["psi_trs"]
    k0 = per_responses["psi_trs_k0"]
    per_control = {}
    positive, negative = [], []
    for control in CONTROLS:
        deltas = [float(x - y) for x, y in zip(psi[control], k0[control])]
        med = _median(deltas)
        per_control[control] = {
            "per_block": deltas,
            "median": med,
            "iqr": _iqr(deltas),
            "positive_blocks": sum(1 for d in deltas if np.isfinite(d) and d > 0.0),
            "zero_blocks": sum(1 for d in deltas if np.isfinite(d) and d == 0.0),
            "negative_blocks": sum(1 for d in deltas if np.isfinite(d) and d < 0.0),
        }
        if np.isfinite(med) and med > 0.0:
            positive.append(control)
        elif np.isfinite(med) and med < 0.0:
            negative.append(control)
    return {
        "per_control": per_control,
        "controls_with_positive_median_delta": positive,
        "controls_with_negative_median_delta": negative,
        "standing": RECURSIVE_DELTA_STANDING,
    }


# ----------------------------- SAG control-rank analysis -----------------------------
def _sag_inputs(block_caches, control: str) -> List[np.ndarray]:
    """The exact cached control arrays (same objects the descriptors consumed) for the SAG stage."""
    return [blk["cache"][control]["array"] for blk in block_caches]


def _detect_ties(finite_pairs):
    groups: Dict[float, List[str]] = {}
    for c, m in finite_pairs:
        groups.setdefault(round(float(m), 12), []).append(c)
    return [{"value": k, "controls": sorted(v)}
            for k, v in sorted(groups.items(), key=lambda kv: -kv[0]) if len(v) > 1]


def sag_control_analysis(block_caches):
    """Reuse the EXISTING multi-window SAG (evaluate_sag_real) on the SAME cached control arrays. The API
    consumes (T, C) descriptor arrays directly, so reuse is technically compatible with no semantic change."""
    per_control = {}
    for control in CONTROLS:
        arrays = _sag_inputs(block_caches, control)
        if not arrays:
            per_control[control] = {
                "n_blocks": 0, "per_block_gain_kpos": [], "per_block_gain_k0": [],
                "median": float("nan"), "iqr": float("nan"), "mean": float("nan"),
                "mean_median_ratio": float("nan"), "amplifying_blocks": 0,
            }
            continue
        sag = _rvd.evaluate_sag_real(arrays)
        kpos = [float(w["G_kpos"]) for w in sag["per_window"]]
        k0 = [float(w["G_k0"]) for w in sag["per_window"]]
        med = _median(kpos)
        mean = _mean(kpos)
        per_control[control] = {
            "n_blocks": len(arrays),
            "per_block_gain_kpos": [float(x) for x in kpos],
            "per_block_gain_k0": [float(x) for x in k0],
            "median": med,
            "iqr": _iqr(kpos),
            "mean": mean,
            "mean_median_ratio": (float(mean / med)
                                  if (np.isfinite(mean) and np.isfinite(med) and med != 0.0)
                                  else float("nan")),
            "amplifying_blocks": int(sag["n_amplifying"]),
        }
    medians = [(c, per_control[c]["median"]) for c in CONTROLS]
    finite = [(c, m) for c, m in medians if np.isfinite(m)]
    ordered = sorted(finite, key=lambda cm: (-cm[1], cm[0]))
    true_rank = next((i + 1 for i, (c, _m) in enumerate(ordered) if c == "true"), None)
    return {
        "included": True,
        "reused": "run_real_video_descriptors.evaluate_sag_real (steps=60, kappa=3.0, margin=0.2)",
        "per_control": per_control,
        "ranking_by_median_gain_kpos": [{"control": c, "median_gain_kpos": float(m)} for c, m in ordered],
        "true_rank": true_rank,
        "ties": _detect_ties(finite),
        "note": ("non-overlapping blocks only; the rank is descriptive and is not a pass/fail or a "
                 "temporal-order verdict."),
    }


# ----------------------------- per-clip + top-level assembly -----------------------------
def analyze_descriptor_field(field: np.ndarray, clip_ordinal: int, clip_name: str,
                             source: Optional[str] = None, include_sag: bool = True,
                             extractors: Optional[Dict[str, Callable]] = None):
    block_caches, info = compute_block_caches(field, clip_ordinal)

    cache_summary = []
    for b, blk in enumerate(block_caches):
        entry: Dict[str, object] = {"block": b}
        for control in CONTROLS:
            cc = blk["cache"][control]
            entry[control] = {
                "array_sha256": cc["array_sha256"],
                "metadata": cc["metadata"],
                "metadata_consistent": cc["metadata_consistent"],
            }
        cache_summary.append(entry)

    responses_summary, per_responses, raw_responses = descriptor_responses(
        block_caches, extractors=extractors)
    ranks = control_ranks(responses_summary)
    rec = recursive_delta(per_responses)
    sag = (sag_control_analysis(block_caches) if include_sag
           else {"included": False, "reason": "SAG stage disabled for this call"})

    all_vals = [x for name in per_responses for c in CONTROLS for x in per_responses[name][c]]
    finite, nonfinite = _finite_counts(all_vals)
    descriptor_names = list(per_responses.keys())
    norm_diag = build_normalization_diagnostics(
        clip_name, descriptor_names, CONTROLS, len(block_caches),
        raw_responses["true_feature_norms"], raw_responses["raw_numerators"], per_responses)
    return {
        "clip_name": clip_name,
        "clip_ordinal": int(clip_ordinal),
        "source": source,
        "epsilon": EPSILON,
        "blocks": info,
        "controls": list(CONTROLS),
        "descriptors": descriptor_names,
        "transform_cache": cache_summary,
        "descriptor_responses": responses_summary,
        "control_ranks": ranks,
        "recursive_delta": rec,
        "sag": sag,
        "response_normalization_diagnostics": norm_diag,
        "finite_summary": {"finite": finite, "nonfinite": nonfinite, "total": finite + nonfinite},
    }


def build_result(clip_results) -> Dict[str, object]:
    total_finite = sum(cr["finite_summary"]["finite"] for cr in clip_results)
    total_nonfinite = sum(cr["finite_summary"]["nonfinite"] for cr in clip_results)
    return {
        "schema": SCHEMA,
        "analyzer_name": ANALYZER_NAME,
        "analyzer_version": ANALYZER_VERSION,
        "analysis_type": ANALYSIS_TYPE,
        "global_seed": GLOBAL_SEED,
        "block_len": BLOCK_LEN,
        "epsilon": EPSILON,
        "controls": list(CONTROLS),
        "descriptors": list(DESCRIPTOR_NAMES),
        "feasibility_standing": FEASIBILITY_STANDING,
        "feasibility_reasons": list(FEASIBILITY_REASONS),
        "independent_inference_authorized": False,
        "temporal_order_claim_authorized": False,
        "recursive_time_claim_authorized": False,
        "perception_claim_authorized": False,
        "scientific_evidence_generated": False,
        "locks": dict(LOCKS),
        "non_claims": NON_CLAIM,
        "response_normalization_diagnostics": aggregate_normalization_diagnostics(clip_results),
        "clips": clip_results,
        "finite_summary": {"finite": total_finite, "nonfinite": total_nonfinite,
                           "total": total_finite + total_nonfinite},
    }


def analyze_paths(npz_paths: Sequence[str], include_sag: bool = True) -> Dict[str, object]:
    """Analyze explicitly supplied .npz paths. Loads frames via the existing loader; writes nothing."""
    clip_results = []
    for ordinal, path in enumerate(npz_paths):
        frames = _real_video.load_frame_stack_npz(path)
        field = extract_descriptor_field(frames)
        clip_results.append(analyze_descriptor_field(
            field, clip_ordinal=ordinal, clip_name=os.path.basename(path), source=path,
            include_sag=include_sag))
    return _jsonable(build_result(clip_results))


# ----------------------------- human-readable formatter -----------------------------
def _fmt(x) -> str:
    if x is None:
        return "nan"
    if isinstance(x, float):
        return "nan" if not math.isfinite(x) else "{:.4f}".format(x)
    return str(x)


def format_report(result: Dict[str, object]) -> str:
    """Deterministic, UTF-8-safe (ASCII) human summary of a (jsonable) analysis result."""
    lines = [
        "{} {} - {}".format(result["analyzer_name"], result["analyzer_version"], result["analysis_type"]),
        "feasibility: {}".format(result["feasibility_standing"]),
    ]
    for reason in result["feasibility_reasons"]:
        lines.append("  - " + reason)
    lines.append("global_seed={}  block_len={}  epsilon={}".format(
        result["global_seed"], result["block_len"], result["epsilon"]))
    lines.append("controls: " + ", ".join(result["controls"]))
    lines.append("descriptors: " + ", ".join(result["descriptors"]))
    for clip in result["clips"]:
        b = clip["blocks"]
        lines.append("")
        lines.append("clip[{}] {}: rows={} blocks={} discarded={} ranges={}".format(
            clip["clip_ordinal"], clip["clip_name"], b["descriptor_row_count"],
            b["complete_block_count"], b["discarded_trailing_rows"], b["block_index_ranges"]))
        for name in clip["descriptors"]:
            ranked = "  ".join(
                "{}={}".format(e["control"], _fmt(e["median"]))
                for e in clip["control_ranks"][name]["by_median_desc"])
            lines.append("  response median rank [{}]: {}".format(name, ranked))
        rec = clip["recursive_delta"]
        lines.append("  recursive_delta (psi_trs - psi_trs_k0) positive-median controls: {}  "
                     "negative-median: {}".format(rec["controls_with_positive_median_delta"],
                                                   rec["controls_with_negative_median_delta"]))
        sag = clip["sag"]
        if sag.get("included"):
            rank = "  ".join("{}={}".format(e["control"], _fmt(e["median_gain_kpos"]))
                             for e in sag["ranking_by_median_gain_kpos"])
            lines.append("  SAG median G(k>0) rank: {}  true_rank={}".format(rank, sag["true_rank"]))
            if sag["ties"]:
                lines.append("  SAG ties: {}".format(sag["ties"]))
        lines.append("  finite/nonfinite: {}/{}".format(
            clip["finite_summary"]["finite"], clip["finite_summary"]["nonfinite"]))
    nd = result.get("response_normalization_diagnostics")
    if nd is not None:
        lines.append("")
        lines.append("NORMALIZATION SAFETY:")
        lines.append("  epsilon={}  near_epsilon_threshold={}".format(
            nd["epsilon"], nd["near_epsilon_threshold"]))
        lines.append("  epsilon-hit total={}  near-epsilon-hit total={}".format(
            nd["epsilon_hit_total"], nd["near_epsilon_total"]))
        finite_mins = sorted(
            (pd["min_true_feature_norm"], name)
            for name, pd in nd["per_descriptor"].items()
            if pd["min_true_feature_norm"] is not None and math.isfinite(pd["min_true_feature_norm"]))
        if finite_mins:
            lines.append("  min true-feature norm (overall)={} (descriptor={})".format(
                _fmt(finite_mins[0][0]), finite_mins[0][1]))
        lr = nd["largest_response"]
        if lr is not None:
            lines.append("  largest normalized response={} at clip={} descriptor={} control={} block={}".format(
                _fmt(lr["normalized_response"]), lr["clip"], lr["descriptor"], lr["control"], lr["block"]))
            lines.append("    raw_numerator={}  raw_denominator={}  effective_denominator={}".format(
                _fmt(lr["raw_numerator"]), _fmt(lr["raw_denominator"]), _fmt(lr["effective_denominator"])))
    lines.append("")
    lines.append("LOCKS: " + ", ".join("{}={}".format(k, v) for k, v in result["locks"].items()))
    lines.append("NON-CLAIM: " + result["non_claims"])
    return "\n".join(lines)


# ----------------------------- CLI (prints only; never writes) -----------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_prerecorded_paired_analysis_v0_1",
        description=("Offline descriptive paired analyzer over explicitly supplied prerecorded .npz clips. "
                     "Writes nothing; prints a JSON report and a human-readable summary. No inferential "
                     "benchmark; no classifier is reused."),
    )
    parser.add_argument("npz_paths", nargs="*",
                        help="explicit .npz descriptor clip paths (no repository asset is required).")
    parser.add_argument("--no-sag", action="store_true", help="skip the SAG control-rank reuse stage.")
    parser.add_argument("--format", choices=["json", "human", "both"], default="both",
                        help="what to print to stdout (default: both).")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    ns = _build_parser().parse_args(argv)
    if not ns.npz_paths:
        print("no .npz paths supplied; nothing to analyze (this analyzer operates only on explicit paths).",
              file=sys.stderr)
        return 0
    result = analyze_paths(ns.npz_paths, include_sag=not ns.no_sag)
    if ns.format in ("json", "both"):
        print(json.dumps(result, sort_keys=True, indent=2))
    if ns.format in ("human", "both"):
        print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
