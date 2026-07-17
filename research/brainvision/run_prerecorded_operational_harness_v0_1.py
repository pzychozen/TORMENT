"""TORMENT Brainvision prerecorded operational harness v0.1 (offline; quarantined; descriptive-only).

Orchestration harness implementing docs/TORMENT_BRAINVISION_PRERECORDED_OPERATIONAL_HARNESS_IMPLEMENTATION_
SPECIFICATION_v0.1.md. It accepts a declared manifest of prerecorded .npz inputs and emits a deterministic
canonical JSON wrapper on stdout only, writing nothing to disk. All descriptor computation is delegated to the
existing paired analyzer's single entry point ``run_prerecorded_paired_analysis_v0_1.analyze_paths``; this
harness imports and duplicates NO descriptor, psi_trs, SAG, control-transform, companion, response, or N64
evaluation mathematics. The paired-analysis subtree is embedded verbatim (its existing None/null values are
preserved). This is offline, prerecorded, quarantined, service-disconnected, non-runtime, non-production, and
descriptive. FORMAL HOLD and Mode 0 remain active. No perception / vision / temporal-order / arrow-of-time /
causality / classification / significance / recursive-mechanism / production-readiness claim is made.

Offline and quarantined: no torment_service import; no runtime integration; no camera / live capture; no
prompt / context / memory / action; no MCP; no render-body; no autonomy; no database; no carrier. stdlib +
numpy + the single reused research/brainvision analyzer module. Transport is stdout-only; the process writes
no file. Exit codes: 0 = canonical payload emitted and overall_health true; 1 = canonical invalid payload
emitted and overall_health false; 2 = argparse-level CLI syntax failure before payload construction.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import os
import platform
import re
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np

# Sole descriptor-computation entry point. No other research/brainvision module is imported.
import run_prerecorded_paired_analysis_v0_1 as paired

HARNESS_NAME = "run_prerecorded_operational_harness_v0_1"
HARNESS_VERSION = "0.1"
SCHEMA_NAME = "torment_brainvision_prerecorded_operational_harness"
SCHEMA_VERSION = "0.1"
CANONICALIZATION_NAME = "torment_brainvision_operational_canonical_json"
CANONICALIZATION_VERSION = "0.1"
ANALYZER_MODULE_NAME = "run_prerecorded_paired_analysis_v0_1"

_SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_LOGICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Exact predeclared positive-outcome keys prohibited anywhere in the canonical payload (see spec S12).
PROHIBITED_OUTCOME_KEYS: Tuple[str, ...] = (
    "success", "scientific_success", "separation_detected", "higher_order_detected",
    "classification_result", "accuracy", "p_value", "significance", "mechanism_confirmed",
    "recursive_confirmed", "production_ready", "vision_detected", "perception_detected",
)

_INTERPRETATION_WARNINGS: Tuple[str, ...] = (
    "OFFLINE_DESCRIPTIVE_ENGINEERING_DIAGNOSTICS: descriptive engineering diagnostics only.",
    ("No perception, vision, temporal-order, arrow-of-time, causality, classification, statistical "
     "significance, recursive-mechanism, or production-readiness claim is made or implied."),
    ("kappa / companion differences are normalized transform-sensitivity descriptors, not mechanism "
     "contributions (see paired_analysis.non_claims and recursive-delta standing)."),
    "Stable, byte-identical output is an engineering property only and is not scientific validation.",
)


class _NonFiniteError(ValueError):
    """A bare non-finite float reached canonical serialization (must never happen for valid payloads)."""


# --------------------------------------------------------------------------- canonical JSON + hashing
# Local transport-canonicalization matching the frozen canonical contract (ensure_ascii, sort_keys, compact
# separators, allow_nan=False). None is permitted as JSON null; any new bare non-finite numeric value raises.

def canonicalize(obj: object) -> object:
    if isinstance(obj, dict):
        return {str(key): canonicalize(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [canonicalize(value) for value in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        value = float(obj)
        if not math.isfinite(value):
            raise _NonFiniteError("nonfinite float reached canonical serialization")
        return 0.0 if value == 0.0 else value
    if isinstance(obj, np.ndarray):
        return canonicalize(obj.tolist())
    if obj is None or isinstance(obj, str):
        return obj
    raise TypeError("uncanonicalizable object of type " + type(obj).__name__)


def canonical_text(value: object) -> str:
    return json.dumps(
        canonicalize(value), ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def canonical_bytes(value: object) -> bytes:
    return canonical_text(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sequence_sha256(value: object) -> str:
    return sha256_hex(canonical_bytes(value))


# --------------------------------------------------------------------------- environment fingerprint

def _numpy_build_configuration_sha256() -> str:
    func = getattr(np, "show_config", None)
    if func is None:
        return "unavailable_api_absent"
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):  # never let show_config text reach canonical stdout
            result = func()
    except Exception as exc:  # class name only; deterministic sentinel
        return "unavailable_call_failed_" + type(exc).__name__
    if isinstance(result, (dict, list)):
        return canonical_sequence_sha256(canonicalize(result))
    text = buffer.getvalue()
    if text:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
        normalized = "\n".join(line.rstrip(" \t") for line in normalized.split("\n"))
        return sha256_hex(normalized.encode("utf-8"))
    return "unavailable_empty"


def capture_environment() -> Dict[str, object]:
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "numpy_build_configuration_sha256": _numpy_build_configuration_sha256(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "byteorder": sys.byteorder,
        "canonicalization_name": CANONICALIZATION_NAME,
        "canonicalization_version": CANONICALIZATION_VERSION,
    }


# --------------------------------------------------------------------------- frozen envelope objects

def _authority() -> Dict[str, object]:
    return {
        "FORMAL_HOLD_active": True,
        "Mode_0_active": True,
        "verdict": "HOLD",
        "output_type": "OFFLINE_DESCRIPTIVE_ENGINEERING_DIAGNOSTICS",
        "scientific_claim_authorized": False,
        "temporal_order_claim_authorized": False,
        "perception_or_vision_claim_authorized": False,
        "runtime_integration_authorized": False,
        "production_kernel_modification_authorized": False,
    }


def _configuration(manifest_source: str) -> Dict[str, object]:
    return {
        "include_sag": True,
        "with_companion": True,
        "global_seed": paired.GLOBAL_SEED,
        "block_len": paired.BLOCK_LEN,
        "epsilon": paired.EPSILON,
        "near_epsilon_threshold": paired.NEAR_EPSILON_THRESHOLD,
        "controls": list(paired.CONTROLS),
        "descriptors": list(paired.DESCRIPTOR_NAMES),
        "companion_descriptor_domain": list(paired.D_COMPANION),
        "companion_offset_policy": paired.COMPANION_OFFSET_POLICY,
        "companion_aggregation_policy": paired.COMPANION_AGGREGATION_POLICY,
        "canonicalization_name": CANONICALIZATION_NAME,
        "canonicalization_version": CANONICALIZATION_VERSION,
        "analyzer_nonfinite_policy": "ANALYZER_JSONABLE_NONFINITE_TO_NULL",
        "manifest_source": manifest_source,
    }


def _source(source_commit: str) -> Dict[str, object]:
    return {
        "source_commit": source_commit,
        "harness_name": HARNESS_NAME,
        "harness_version": HARNESS_VERSION,
        "analyzer_module_name": ANALYZER_MODULE_NAME,
        "analyzer_version": paired.ANALYZER_VERSION,
    }


# --------------------------------------------------------------------------- manifest resolution

def _resolve_records(args: argparse.Namespace) -> Tuple[List[Dict[str, object]], Optional[str]]:
    """Resolve the ordered input source into structural records.

    Returns (records, hard_code). ``records`` is an ordered list of
    {"logical_id": str|None, "path": str|None, "structural_ok": bool}. ``hard_code`` is one of
    None / 'manifest_source_conflict' / 'manifest_parse_failed' / 'manifest_schema_invalid'
    (the last only for a non-list top-level manifest; per-entry schema faults are marked structural_ok=False).
    """
    has_manifest = args.manifest is not None
    has_positional = len(args.paths) > 0
    if has_manifest and has_positional:
        return [], "manifest_source_conflict"
    if has_manifest:
        try:
            with open(args.manifest, "r", encoding="utf-8") as handle:
                parsed = json.loads(handle.read())
        except Exception:
            return [], "manifest_parse_failed"
        if not isinstance(parsed, list):
            return [], "manifest_schema_invalid"
        records: List[Dict[str, object]] = []
        for element in parsed:
            if (isinstance(element, dict) and set(element.keys()) == {"logical_id", "path"}
                    and isinstance(element.get("logical_id"), str) and isinstance(element.get("path"), str)):
                records.append({"logical_id": element["logical_id"], "path": element["path"],
                                "structural_ok": True})
            else:
                lid = element.get("logical_id") if isinstance(element, dict) else None
                pth = element.get("path") if isinstance(element, dict) else None
                records.append({"logical_id": lid if isinstance(lid, str) else None,
                                "path": pth if isinstance(pth, str) else None, "structural_ok": False})
        return records, None
    return ([{"logical_id": "input_%04d" % index, "path": path, "structural_ok": True}
             for index, path in enumerate(args.paths)], None)


def _hash_file(path: str) -> Optional[str]:
    try:
        if os.path.isdir(path) or not os.path.isfile(path) or not os.access(path, os.R_OK):
            return None
        with open(path, "rb") as handle:
            return sha256_hex(handle.read())
    except OSError:
        return None


# --------------------------------------------------------------------------- payload assembly

def build_payload(args: argparse.Namespace) -> Dict[str, object]:
    error_codes: List[str] = []
    manifest_warnings: List[str] = []

    source_commit = args.source_commit
    source_commit_valid = bool(_SOURCE_COMMIT_RE.match(source_commit))
    if not source_commit_valid:
        error_codes.append("source_commit_invalid")

    manifest_source = "manifest_json" if args.manifest is not None else "positional_paths"
    records, hard_code = _resolve_records(args)

    per_record_hash: List[Optional[str]] = [None] * len(records)

    if hard_code is not None:
        error_codes.append(hard_code)
    elif not records:
        error_codes.append("manifest_empty")
    elif any(not record["structural_ok"] for record in records):
        error_codes.append("manifest_schema_invalid")
        for index, record in enumerate(records):  # best-effort hashing; entries preserved, never removed
            if record["structural_ok"] and isinstance(record["path"], str):
                per_record_hash[index] = _hash_file(record["path"])
    else:
        logical_id_counts: Dict[str, int] = {}
        norm_path_counts: Dict[str, int] = {}
        content_counts: Dict[str, int] = {}
        for index, record in enumerate(records):
            logical_id = record["logical_id"]
            path = record["path"]
            if not _LOGICAL_ID_RE.match(logical_id):
                error_codes.append("manifest_invalid_logical_id")
            logical_id_counts[logical_id] = logical_id_counts.get(logical_id, 0) + 1
            if not path.lower().endswith(".npz"):
                error_codes.append("manifest_wrong_extension")
            norm = os.path.normcase(os.path.realpath(os.path.abspath(path)))
            norm_path_counts[norm] = norm_path_counts.get(norm, 0) + 1
            if os.path.isdir(path):
                error_codes.append("manifest_path_is_directory")
            elif os.path.isfile(path) and os.access(path, os.R_OK):
                digest = _hash_file(path)
                if digest is None:
                    error_codes.append("manifest_missing_input")
                else:
                    per_record_hash[index] = digest
                    content_counts[digest] = content_counts.get(digest, 0) + 1
            else:
                error_codes.append("manifest_missing_input")
        if any(count > 1 for count in logical_id_counts.values()):
            error_codes.append("manifest_duplicate_logical_id")
        if any(count > 1 for count in norm_path_counts.values()):
            error_codes.append("manifest_duplicate_path")
        if any(count > 1 for count in content_counts.values()):
            manifest_warnings.append("manifest_duplicate_content")

    manifest_hard_errors = [code for code in error_codes if code.startswith("manifest_")]
    all_structural_ok = bool(records) and all(record["structural_ok"] for record in records)

    entries_public = [{"logical_id": records[index]["logical_id"], "npz_sha256": per_record_hash[index]}
                      for index in range(len(records))]

    ims_ok = (not manifest_hard_errors) and all_structural_ok and all(h is not None for h in per_record_hash)
    input_manifest_sha256 = canonical_sequence_sha256(entries_public) if ims_ok else None

    path_strings = [record["path"] for record in records if isinstance(record["path"], str)]
    input_path_identity_sha256 = canonical_sequence_sha256(path_strings) if path_strings else None

    analysis_allowed = source_commit_valid and (not manifest_hard_errors) and all_structural_ok

    # health booleans (seven) -----------------------------------------------------------------
    manifest_valid = not manifest_hard_errors
    inputs_readable_valid = not any(
        code in error_codes for code in ("manifest_missing_input", "manifest_path_is_directory"))
    replay_material_valid = source_commit_valid
    serialization_valid = True
    analyzer_identity_valid = False
    analysis_completed_valid = False
    clip_count_valid = False

    paired_analysis: object = {}
    analysis_error: Dict[str, object] = {"exception_class": None}

    if analysis_allowed:
        ordered_paths = [record["path"] for record in records]
        try:
            result = paired.analyze_paths(ordered_paths, include_sag=True, with_companion=True)
        except Exception as exc:  # engineering failure, not a scientific outcome; class name only
            error_codes.append("analysis_failed")
            analysis_error = {"exception_class": type(exc).__name__}
        else:
            try:
                canonical_bytes(result)  # verify the reused subtree serializes finite-only
            except Exception:
                error_codes.append("serialization_failed")
                serialization_valid = False
            else:
                paired_analysis = result
                analysis_completed_valid = True
                analyzer_identity_valid = bool(
                    isinstance(result, dict)
                    and result.get("schema") == paired.SCHEMA
                    and result.get("analyzer_name") == paired.ANALYZER_NAME
                    and result.get("analyzer_version") == paired.ANALYZER_VERSION)
                clips = result.get("clips") if isinstance(result, dict) else None
                clip_count_valid = bool(isinstance(clips, list) and len(clips) == len(records))

    overall_health = bool(
        manifest_valid and inputs_readable_valid and analyzer_identity_valid and analysis_completed_valid
        and clip_count_valid and serialization_valid and replay_material_valid)

    harness_health = {
        "manifest_valid": manifest_valid,
        "inputs_readable_valid": inputs_readable_valid,
        "analyzer_identity_valid": analyzer_identity_valid,
        "analysis_completed_valid": analysis_completed_valid,
        "clip_count_valid": clip_count_valid,
        "serialization_valid": serialization_valid,
        "replay_material_valid": replay_material_valid,
        "overall_health": overall_health,
        "error_codes": sorted(set(error_codes)),
        "warnings": list(manifest_warnings),
    }

    configuration = _configuration(manifest_source)
    environment = capture_environment()

    top_level_warnings = list(_INTERPRETATION_WARNINGS) + ["manifest_warning:" + w for w in manifest_warnings]

    payload = {
        "schema": {"name": SCHEMA_NAME, "version": SCHEMA_VERSION},
        "authority": _authority(),
        "source": _source(source_commit),
        "environment": environment,
        "configuration": configuration,
        "input_manifest": {
            "entries": entries_public,
            "input_manifest_sha256": input_manifest_sha256,
            "warnings": list(manifest_warnings),
        },
        "paired_analysis": paired_analysis,
        "analysis_error": analysis_error,
        "harness_health": harness_health,
        "warnings": top_level_warnings,
        "replay": {
            "source_commit": source_commit,
            "configuration_sha256": canonical_sequence_sha256(configuration),
            "environment_fingerprint_sha256": canonical_sequence_sha256(environment),
            "input_manifest_sha256": input_manifest_sha256,
            "input_path_identity_sha256": input_path_identity_sha256,
            "canonicalization_name": CANONICALIZATION_NAME,
            "canonicalization_version": CANONICALIZATION_VERSION,
        },
    }
    return payload


def build_wrapper(payload: Dict[str, object]) -> Dict[str, object]:
    return {"payload": payload, "payload_sha256": canonical_sequence_sha256(payload)}


# --------------------------------------------------------------------------- human report (payload-only)

def format_human_summary(payload: Dict[str, object]) -> str:
    schema = payload["schema"]
    lines = ["TORMENT Brainvision prerecorded operational harness v{} (schema {} v{})".format(
        HARNESS_VERSION, schema["name"], schema["version"])]
    lines.append("output_type: " + str(payload["authority"]["output_type"]))
    lines.append("source_commit: " + str(payload["source"]["source_commit"]))
    manifest = payload["input_manifest"]
    ims = manifest["input_manifest_sha256"]
    lines.append("manifest_source: {} ; entries: {} ; input_manifest_sha256: {}".format(
        payload["configuration"]["manifest_source"], len(manifest["entries"]),
        "null" if ims is None else ims))
    health = payload["harness_health"]
    for key in ("manifest_valid", "inputs_readable_valid", "analyzer_identity_valid",
                "analysis_completed_valid", "clip_count_valid", "serialization_valid",
                "replay_material_valid", "overall_health"):
        lines.append("  {} = {}".format(key, health[key]))
    if health["error_codes"]:
        lines.append("error_codes: " + ", ".join(health["error_codes"]))
    exception_class = payload["analysis_error"]["exception_class"]
    if exception_class is not None:
        lines.append("analysis_error.exception_class: " + str(exception_class))
    paired_analysis = payload["paired_analysis"]
    if isinstance(paired_analysis, dict) and isinstance(paired_analysis.get("clips"), list):
        lines.append("paired_analysis: {} clip(s) ; controls: {}".format(
            len(paired_analysis["clips"]), ", ".join(paired_analysis.get("controls", []))))
        for clip in paired_analysis["clips"]:
            lines.append("  clip {}: descriptors={} companion={}".format(
                clip.get("clip_name"),
                len(clip.get("descriptors", [])),
                "yes" if "boundary_neutral_companion" in clip else "no"))
    for warning in payload["warnings"]:
        lines.append("warning: " + warning)
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- transport / CLI

def emit(wrapper: Dict[str, object]) -> None:
    """Write only the canonical wrapper text to stdout with no trailing newline; write no file."""
    sys.stdout.write(canonical_text(wrapper))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=HARNESS_NAME,
        description=("Offline quarantined prerecorded operational harness (prints canonical wrapper only; "
                     "writes no file)."),
    )
    parser.add_argument("paths", nargs="*",
                        help="explicit ordered .npz descriptor clip paths (mutually exclusive with --manifest).")
    parser.add_argument("--source-commit", required=True,
                        help="full lowercase 40-character repository commit identity.")
    parser.add_argument("--manifest", default=None,
                        help="path to an ordered JSON manifest [{logical_id, path}, ...].")
    parser.add_argument("--human-summary", action="store_true",
                        help="also write a deterministic human report (derived only from payload) to stderr.")
    return parser


def _main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)  # argparse-level CLI syntax failure exits 2 before payload
    payload = build_payload(args)
    emit(build_wrapper(payload))
    if args.human_summary:
        sys.stderr.write(format_human_summary(payload))
    return 0 if payload["harness_health"]["overall_health"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
