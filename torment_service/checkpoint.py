"""
checkpoint.py — TORMENT checkpoint save / load system (Phase 5)

Periodically snapshots the running engine state so that recovery does
not require replaying every JSONL event from zero.  Checkpoints are
written to `memory_core/checkpoints/` as plain JSON.

Checkpoint contains:
  - step counter
  - Full kernel ModelState (Omega as real/imag pairs, phi_index, z, etc.)
  - CorridorMonitor EMA fields (the physics "memory" of the corridor)
  - Character modulation dict (_char_mod)
  - CharacterState drift snapshot
  - Motif summary (active motifs count, top motifs)
  - Embedding shard manifest snapshot (active shard, next row)

Design rules:
  - Checkpoints are convenience — never authoritative.
  - If a checkpoint is missing or corrupt, the system replays JSONL.
  - Write is non-fatal: failure logs a warning and continues.
  - JSON format for human readability (each checkpoint < 5 KB).
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import numpy as np

from .embedding_store import _canonical_storage_root, _child_path

log = logging.getLogger("torment.checkpoint")


def _sanitize_log(value: str) -> str:
    """Strip control characters that could forge log entries."""
    return str(value).replace("\n", "\\n").replace("\r", "\\r")


def _validate_path_component(value: str, label: str) -> str:
    """Reject path separators and traversal sequences in identifiers."""
    if not value or ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")
    return value


def _ensure_within_base(path: str, base_dir: str) -> str:
    """Resolve *path* and verify it stays inside *base_dir*.

    Returns the resolved absolute path on success.
    Raises ``ValueError`` if the path escapes the base directory.

    Used to revalidate externally-sourced paths (e.g. glob results)
    against a trusted root.
    """
    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(path)
    if resolved != base and not resolved.startswith(base + os.sep):
        raise ValueError(f"Path escapes base directory")
    return resolved


def _validated_checkpoint_root(
    checkpoint_dir: str, base_dir: str, *, mkdir: bool = False,
) -> str:
    """Canonicalize *checkpoint_dir* and verify containment in *base_dir*.

    Inlines ``os.path.realpath`` + ``startswith`` containment so that
    static-analysis tools (CodeQL) see the sanitiser barrier in the
    same module as the filesystem sinks that consume the returned path.
    """
    root = os.path.realpath(os.path.normpath(checkpoint_dir))
    if ".." in root.split(os.sep):
        raise ValueError(f"Canonical path contains traversal segment: {root!r}")
    base = os.path.realpath(os.path.normpath(base_dir))
    if root != base and not root.startswith(base + os.sep):
        raise ValueError("Checkpoint directory escapes base")
    if mkdir:
        os.makedirs(root, exist_ok=True)
    return root


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _complex_array_to_json(arr: np.ndarray) -> List[List[float]]:
    """Serialize a complex numpy array as [[re, im], ...]."""
    arr = np.asarray(arr, dtype=np.complex128).reshape(-1)
    return [[float(c.real), float(c.imag)] for c in arr]


def _json_to_complex_array(data: List[List[float]]) -> np.ndarray:
    """Deserialize [[re, im], ...] back to complex128 numpy array."""
    return np.array([complex(r, i) for r, i in data], dtype=np.complex128)


def _float_array_to_json(arr: np.ndarray) -> List[float]:
    """Serialize a real numpy array."""
    return [float(x) for x in np.asarray(arr, dtype=float).reshape(-1)]


def _json_to_float_array(data: List[float]) -> np.ndarray:
    """Deserialize back to float64 numpy array."""
    return np.array(data, dtype=float)


# ---------------------------------------------------------------------------
# Serialize kernel state (ModelState + CorridorMonitor)
# ---------------------------------------------------------------------------

def serialize_model_state(state) -> Dict[str, Any]:
    """Serialize a ModelState to a JSON-safe dict.

    Handles complex Omega, numpy vectors, and the _char_mod attribute.
    """
    return {
        "Omega": _complex_array_to_json(state.Omega),
        "phi_index": int(state.phi_index),
        "cycle_stage": int(state.cycle_stage),
        "identity_state": int(state.identity_state),
        "z": float(state.z),
        "z_mem": float(state.z_mem),
        "Z_macro": _float_array_to_json(state.Z_macro),
        "Z_chiral": _float_array_to_json(state.Z_chiral),
        "Z_vec": _float_array_to_json(state.Z_vec),
        "t": float(state.t),
        "step": int(state.step),
        "_char_mod": dict(getattr(state, "_char_mod", {}) or {}),
    }


def deserialize_model_state(data: Dict[str, Any]):
    """Restore a ModelState from a serialized dict.

    Imports ModelState locally to avoid circular imports.
    """
    from .kernel.model_core import ModelState

    state = ModelState(
        Omega=_json_to_complex_array(data["Omega"]),
        phi_index=int(data.get("phi_index", 0)),
        cycle_stage=int(data.get("cycle_stage", 0)),
        identity_state=int(data.get("identity_state", 0)),
        z=float(data.get("z", 0.0)),
        z_mem=float(data.get("z_mem", 0.0)),
        t=float(data.get("t", 0.0)),
        step=int(data.get("step", 0)),
    )
    # Restore numpy vectors
    if "Z_macro" in data:
        state.Z_macro[:] = _json_to_float_array(data["Z_macro"])[:3]
    if "Z_chiral" in data:
        state.Z_chiral[:] = _json_to_float_array(data["Z_chiral"])[:3]
    if "Z_vec" in data:
        state.Z_vec[:] = _json_to_float_array(data["Z_vec"])[:3]
    # Restore character modulation
    state._char_mod = dict(data.get("_char_mod", {}))  # type: ignore[attr-defined]
    return state


def serialize_corridor_monitor(mon) -> Dict[str, Any]:
    """Serialize CorridorMonitor EMA fields."""
    return {
        "prev_xy": _float_array_to_json(mon.prev_xy) if mon.prev_xy is not None else None,
        "prev_uxy": _float_array_to_json(mon.prev_uxy) if mon.prev_uxy is not None else None,
        "tear_score_ema": float(mon.tear_score_ema),
        "align_ema": float(mon.align_ema),
        "prox_ema": float(mon.prox_ema),
        "surv_ema": float(mon.surv_ema),
        "coh_ema": float(mon.coh_ema),
    }


def deserialize_corridor_monitor(data: Dict[str, Any]):
    """Restore a CorridorMonitor from serialized dict."""
    from .memory_kernel import CorridorMonitor

    mon = CorridorMonitor()
    mon.prev_xy = _json_to_float_array(data["prev_xy"]) if data.get("prev_xy") is not None else None
    mon.prev_uxy = _json_to_float_array(data["prev_uxy"]) if data.get("prev_uxy") is not None else None
    mon.tear_score_ema = float(data.get("tear_score_ema", 0.0))
    mon.align_ema = float(data.get("align_ema", 0.0))
    mon.prox_ema = float(data.get("prox_ema", 0.0))
    mon.surv_ema = float(data.get("surv_ema", 0.0))
    mon.coh_ema = float(data.get("coh_ema", 0.0))
    return mon


# ---------------------------------------------------------------------------
# Motif summary (lightweight — not the full registry)
# ---------------------------------------------------------------------------

def build_motif_summary(motif_registry) -> Dict[str, Any]:
    """Extract a lightweight summary from a MotifRegistry for checkpointing."""
    motifs = getattr(motif_registry, "motifs", {})
    top = sorted(
        motifs.values(),
        key=lambda m: float(getattr(m, "strength", 0.0) or 0.0),
        reverse=True,
    )[:20]
    return {
        "total_count": len(motifs),
        "top_motifs": [
            {
                "motif_id": m.motif_id,
                "label": m.label,
                "strength": float(m.strength),
                "members_count": len(m.members),
            }
            for m in top
        ],
    }


# ---------------------------------------------------------------------------
# Shard manifest snapshot
# ---------------------------------------------------------------------------

def build_shard_snapshot(embeddings_dir: str, base_dir: str) -> Optional[Dict[str, Any]]:
    """Read current shard manifest for checkpoint.

    *base_dir* is the trusted root directory.  All resolved paths are
    verified to stay inside it before any file access.
    """
    try:
        safe_dir = _ensure_within_base(embeddings_dir, base_dir)
        manifest_path = _child_path(safe_dir, "manifest.json")
    except ValueError:
        return None
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        return {
            "active_shard": int(m.get("active_shard", 0)),
            "next_row": int(m.get("next_row", 0)),
            "total_rows": int(m.get("total_rows", 0)),
            "embedding_dim": int(m.get("embedding_dim", 0)),
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Save / Load
# ---------------------------------------------------------------------------

def _checkpoint_filename(step: int) -> str:
    return f"checkpoint_{step:06d}.json"


def _extract_step_from_filename(filename: str) -> Optional[int]:
    m = re.match(r"checkpoint_(\d+)\.json$", os.path.basename(filename))
    return int(m.group(1)) if m else None


def save_checkpoint(
    checkpoint_dir: str,
    step: int,
    model_state,
    corridor_monitor,
    character_state_dict: Optional[Dict[str, Any]] = None,
    motif_summary: Optional[Dict[str, Any]] = None,
    shard_snapshot: Optional[Dict[str, Any]] = None,
    max_checkpoints: int = 10,
    *,
    base_dir: str,
) -> Optional[str]:
    """Save a checkpoint to disk.  Returns the file path on success, None on failure.

    Keeps at most ``max_checkpoints`` files, removing the oldest.
    *base_dir* is the trusted root directory.  All resolved paths are
    verified to stay inside it before any file access.
    """
    try:
        safe_dir = _validated_checkpoint_root(checkpoint_dir, base_dir, mkdir=True)

        payload: Dict[str, Any] = {
            "version": 1,
            "step": int(step),
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model_state": serialize_model_state(model_state),
            "corridor_monitor": serialize_corridor_monitor(corridor_monitor),
            "character_state": character_state_dict,
            "motif_summary": motif_summary,
            "shard_snapshot": shard_snapshot,
        }

        ckpt_name = _checkpoint_filename(step)
        path = _child_path(safe_dir, ckpt_name)
        tmp = _child_path(safe_dir, ckpt_name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, path)

        # Prune old checkpoints
        _prune_old_checkpoints(safe_dir, max_checkpoints, base_dir)

        log.info("Checkpoint saved: step=%d -> %s", step, _sanitize_log(path))
        return path

    except Exception as exc:
        log.warning("Checkpoint save failed (step=%d): %s", step, exc)
        return None


def _prune_old_checkpoints(checkpoint_dir: str, keep: int, base_dir: str) -> None:
    """Remove oldest checkpoints, keeping at most ``keep``.

    *base_dir* is the trusted root directory. Deletion targets are
    revalidated against the canonical checkpoint directory before removal.
    """
    try:
        safe_dir = _validated_checkpoint_root(checkpoint_dir, base_dir)
    except ValueError:
        return

    # Use os.listdir on the trusted root instead of glob.glob to avoid
    # passing a derived path into glob (which CodeQL traces as tainted).
    try:
        entries = os.listdir(safe_dir)
    except OSError:
        return

    valid_names: List[str] = sorted(
        name for name in entries
        if re.match(r"^checkpoint_\d+\.json$", name)
    )

    if len(valid_names) <= keep:
        return

    for name in valid_names[: len(valid_names) - keep]:
        try:
            candidate = _child_path(safe_dir, name)
            os.remove(candidate)
        except (ValueError, OSError) as e:
            log.debug("Could not remove old checkpoint: %s", e)


def load_latest_checkpoint(checkpoint_dir: str, base_dir: str) -> Optional[Dict[str, Any]]:
    """Load the most recent checkpoint file.  Returns None if no checkpoint exists.

    *base_dir* is the trusted root directory.  All resolved paths are
    verified to stay inside it before any file access.
    """
    try:
        safe_dir = _validated_checkpoint_root(checkpoint_dir, base_dir)
    except ValueError:
        return None
    if not os.path.isdir(safe_dir):
        return None
    # Use os.listdir on the trusted root instead of glob.glob to avoid
    # passing a derived path into glob (which CodeQL traces as tainted).
    try:
        entries = os.listdir(safe_dir)
    except OSError:
        return None

    valid_names: List[str] = sorted(
        name for name in entries
        if re.match(r"^checkpoint_\d+\.json$", name)
    )
    if not valid_names:
        return None
    try:
        path = _child_path(safe_dir, valid_names[-1])
    except ValueError:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("Checkpoint loaded: step=%d", data.get("step", -1))
        return data
    except Exception as exc:
        log.warning("Checkpoint load failed: %s", exc)
        return None


def restore_from_checkpoint(
    checkpoint_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Unpack a loaded checkpoint dict into live objects.

    Returns a dict with keys:
      - step: int
      - model_state: ModelState
      - corridor_monitor: CorridorMonitor
      - character_state: dict or None
      - motif_summary: dict or None
      - shard_snapshot: dict or None
    """
    return {
        "step": int(checkpoint_data["step"]),
        "model_state": deserialize_model_state(checkpoint_data["model_state"]),
        "corridor_monitor": deserialize_corridor_monitor(checkpoint_data["corridor_monitor"]),
        "character_state": checkpoint_data.get("character_state"),
        "motif_summary": checkpoint_data.get("motif_summary"),
        "shard_snapshot": checkpoint_data.get("shard_snapshot"),
    }


def get_checkpoint_dir(data_dir: str, workspace_id: str, agent_id: str) -> str:
    """Return the canonical checkpoint directory path for an agent.

    Validates workspace_id and agent_id, canonicalizes data_dir,
    and returns a trusted root path.
    """
    _validate_path_component(workspace_id, "workspace_id")
    _validate_path_component(agent_id, "agent_id")
    canonical_data = _canonical_storage_root(data_dir)
    return _canonical_storage_root(
        os.path.join(
            canonical_data, "workspaces", workspace_id,
            "agents", agent_id, "private", "checkpoints",
        ),
    )
