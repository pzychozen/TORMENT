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

CHECKPOINT_VERSION = 3
Z_SEMANTICS = "kernel_canonical_v4_0"


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

    Uses bare ``os.path.realpath`` (which already normalises) so that
    CodeQL's taint model recognises the sanitiser.  All filesystem sinks
    are gated inside the positive ``startswith`` branch.
    """
    root = os.path.realpath(checkpoint_dir)
    if ".." in root.split(os.sep):
        raise ValueError(f"Canonical path contains traversal segment: {root!r}")
    base = os.path.realpath(base_dir)
    if root == base or root.startswith(base + os.sep):
        if mkdir:
            os.makedirs(root, exist_ok=True)
        return root
    raise ValueError("Checkpoint directory escapes base")


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
        "z_semantics": Z_SEMANTICS,
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
    from .kernel.model_core import ModelParams, ModelState, TriOctaPhaseLockModel

    state = ModelState(
        Omega=_json_to_complex_array(data["Omega"]),
        phi_index=int(data.get("phi_index", 0)),
        t=float(data.get("t", 0.0)),
        step=int(data.get("step", 0)),
    )
    # Restore character modulation
    state._char_mod = dict(data.get("_char_mod", {}))  # type: ignore[attr-defined]
    char_mod = getattr(state, "_char_mod", {}) or {}
    theta_lock_override = (
        float(char_mod["theta_lock_mod"])
        if "theta_lock_mod" in char_mod
        else None
    )
    model = TriOctaPhaseLockModel(ModelParams())
    model.update_z(state, theta_lock_override=theta_lock_override)
    model.update_cycle_stage(state)
    model.update_identity_state(state)
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


def serialize_cognitive_core_state(cognitive_state) -> Dict[str, Any]:
    """Serialize the extracted cognitive identity state."""
    return {
        "z_mem": float(cognitive_state.z_mem),
        "z_identity": float(cognitive_state.z_identity),
        "identity_state": int(cognitive_state.identity_state),
    }


def deserialize_cognitive_core_state(data: Dict[str, Any] | None):
    """Restore cognitive identity state with safe defaults."""
    from .cognitive_core import CognitiveCoreState

    payload = data or {}
    return CognitiveCoreState(
        z_mem=float(payload.get("z_mem", 0.0)),
        z_identity=float(payload.get("z_identity", 0.0)),
        identity_state=int(payload.get("identity_state", 0)),
    )


def serialize_kernel_runtime_context(runtime_ctx) -> Dict[str, Any]:
    """Serialize per-agent kernel observation history."""
    return {
        "mon": serialize_corridor_monitor(runtime_ctx.mon),
        "disp_buffer": [float(x) for x in runtime_ctx.disp_buffer],
        "last_effective_scale": float(runtime_ctx.last_effective_scale),
        "cognitive_state": serialize_cognitive_core_state(runtime_ctx.cognitive_state),
    }


def deserialize_kernel_runtime_context(data: Dict[str, Any]):
    """Restore per-agent kernel observation history with safe defaults."""
    from .memory_kernel import DEFAULT_DISP_SCALE, KernelRuntimeContext

    return KernelRuntimeContext(
        mon=deserialize_corridor_monitor(data["mon"]),
        disp_buffer=[float(x) for x in data.get("disp_buffer", [])],
        last_effective_scale=float(data.get("last_effective_scale", DEFAULT_DISP_SCALE)),
        cognitive_state=deserialize_cognitive_core_state(data.get("cognitive_state")),
    )


def _migrate_legacy_cognitive_state(runtime_ctx, model_state_data: Dict[str, Any]) -> None:
    """Move legacy spliced model fields into the extracted cognitive state."""
    runtime_ctx.cognitive_state = deserialize_cognitive_core_state(
        {
            "z_mem": model_state_data.get("z_mem", 0.0),
            "z_identity": model_state_data.get("z", 0.0),
            "identity_state": model_state_data.get("identity_state", 0),
        }
    )


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


def _build_checkpoint_dir(data_dir: str, workspace_id: str, agent_id: str) -> str:
    """Build and validate the checkpoint directory path.

    All user-controlled components are validated inline so CodeQL
    can trace the sanitisation chain without crossing function
    boundaries.  Returns a ``realpath``-resolved directory that
    is verified to reside under the ``realpath``-resolved *data_dir*.
    """
    # Inline component validation — no helper calls.
    if not workspace_id or ".." in workspace_id or "/" in workspace_id or "\\" in workspace_id:
        raise ValueError(f"Invalid workspace_id: {workspace_id!r}")
    if not agent_id or ".." in agent_id or "/" in agent_id or "\\" in agent_id:
        raise ValueError(f"Invalid agent_id: {agent_id!r}")

    base = os.path.realpath(data_dir)
    safe_dir = os.path.realpath(os.path.join(
        base, "workspaces", workspace_id,
        "agents", agent_id, "private", "checkpoints",
    ))
    if not safe_dir.startswith(base + os.sep):
        raise ValueError("Checkpoint directory escapes data root")
    return safe_dir


def save_checkpoint(
    data_dir: str,
    workspace_id: str,
    agent_id: str,
    step: int,
    model_state,
    corridor_monitor,
    character_state_dict: Optional[Dict[str, Any]] = None,
    motif_summary: Optional[Dict[str, Any]] = None,
    shard_snapshot: Optional[Dict[str, Any]] = None,
    max_checkpoints: int = 10,
    kernel_runtime_context=None,
) -> Optional[str]:
    """Save a checkpoint to disk.  Returns the file path on success, None on failure.

    Keeps at most ``max_checkpoints`` files, removing the oldest.

    Path is built internally from validated ``workspace_id`` /
    ``agent_id`` components so that no pre-built tainted path
    parameter reaches filesystem sinks.
    """
    try:
        safe_dir = _build_checkpoint_dir(data_dir, workspace_id, agent_id)
        os.makedirs(safe_dir, exist_ok=True)

        mon = kernel_runtime_context.mon if kernel_runtime_context is not None else corridor_monitor
        model_state_data = serialize_model_state(model_state)
        if kernel_runtime_context is not None:
            model_state_data["z_mem"] = float(kernel_runtime_context.cognitive_state.z_mem)
        payload: Dict[str, Any] = {
            "version": CHECKPOINT_VERSION,
            "step": int(step),
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model_state": model_state_data,
            "corridor_monitor": serialize_corridor_monitor(mon),
            "character_state": character_state_dict,
            "motif_summary": motif_summary,
            "shard_snapshot": shard_snapshot,
        }
        if kernel_runtime_context is not None:
            payload["kernel_runtime_context"] = serialize_kernel_runtime_context(
                kernel_runtime_context,
            )

        ckpt_name = _checkpoint_filename(step)
        path = _child_path(safe_dir, ckpt_name)
        tmp = _child_path(safe_dir, ckpt_name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, path)

        # Prune old checkpoints
        _prune_old_checkpoints(safe_dir, max_checkpoints)

        log.info("Checkpoint saved: step=%d -> %s", step, _sanitize_log(path))
        return path

    except Exception as exc:
        log.warning("Checkpoint save failed (step=%d): %s", step, exc)
        return None


def _prune_old_checkpoints(safe_dir: str, keep: int) -> None:
    """Remove oldest checkpoints, keeping at most ``keep``.

    *safe_dir* must already be a validated, ``realpath``-resolved
    checkpoint directory (as returned by ``_build_checkpoint_dir``).
    """
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


def load_latest_checkpoint(
    data_dir: str, workspace_id: str, agent_id: str,
) -> Optional[Dict[str, Any]]:
    """Load the most recent checkpoint file.  Returns None if no checkpoint exists.

    Path is built internally from validated ``workspace_id`` /
    ``agent_id`` components so that no pre-built tainted path
    parameter reaches filesystem sinks.
    """
    try:
        safe_dir = _build_checkpoint_dir(data_dir, workspace_id, agent_id)
    except ValueError:
        return None

    if not os.path.isdir(safe_dir):
        return None
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
      - kernel_runtime_context: KernelRuntimeContext
      - character_state: dict or None
      - motif_summary: dict or None
      - shard_snapshot: dict or None
    """
    runtime_payload = checkpoint_data.get("kernel_runtime_context")
    if runtime_payload is not None:
        runtime_ctx = deserialize_kernel_runtime_context(
            runtime_payload,
        )
        mon = runtime_ctx.mon
    else:
        from .memory_kernel import DEFAULT_DISP_SCALE, KernelRuntimeContext

        mon = deserialize_corridor_monitor(checkpoint_data["corridor_monitor"])
        runtime_ctx = KernelRuntimeContext(
            mon=mon,
            disp_buffer=[],
            last_effective_scale=DEFAULT_DISP_SCALE,
        )

    model_state_data = checkpoint_data["model_state"]
    model_state = deserialize_model_state(model_state_data)
    if not (isinstance(runtime_payload, dict) and "cognitive_state" in runtime_payload):
        _migrate_legacy_cognitive_state(runtime_ctx, model_state_data)

    return {
        "step": int(checkpoint_data["step"]),
        "model_state": model_state,
        "corridor_monitor": mon,
        "kernel_runtime_context": runtime_ctx,
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
