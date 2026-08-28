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
import numbers
import os
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .embedding_store import _child_path
from .pathing import validate_structural_path_component

log = logging.getLogger("torment.checkpoint")

CHECKPOINT_VERSION = 3
Z_SEMANTICS = "kernel_canonical_v4_0"


_FILESYSTEM_CONTAINMENT_EVENT = "filesystem_containment_substitution"
_CHECKPOINT_ROOT_GUARD_MAX = 512


class CheckpointContainmentError(RuntimeError):
    """A checkpoint root no longer has its captured filesystem identity.

    This is deliberately distinct from ordinary non-fatal checkpoint I/O
    failures.  It reports bounded identity-continuity detection, not a claim
    that a path-only check closes every TOCTOU window.
    """


@dataclass(frozen=True)
class _DirectoryIdentity:
    """Canonical directory identity used for bounded continuity detection."""

    canonical_path: str
    st_dev: int
    st_ino: int


@dataclass(frozen=True)
class _CheckpointRootGuard:
    """Captured identities for one checkpoint root.

    Matching identities are evidence of continuity, not proof that later
    filesystem operations are race-free.
    """

    data_dir_input: str
    workspace_id: str
    agent_id: str
    data_root: _DirectoryIdentity
    checkpoint_parent: _DirectoryIdentity
    checkpoint_root: _DirectoryIdentity


_checkpoint_root_guards: "OrderedDict[Tuple[str, str, str], _CheckpointRootGuard]" = OrderedDict()
_checkpoint_root_guards_lock = threading.RLock()


def _sanitize_log(value: str) -> str:
    """Strip control characters that could forge log entries."""
    return str(value).replace("\n", "\\n").replace("\r", "\\r")


def _validate_path_component(value: str, label: str) -> str:
    """Reject path separators and traversal sequences in identifiers."""
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        if value == ".":
            raise ValueError(f"Invalid {label}: must not be '.'") from exc
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")


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


def _directory_identity(path: str) -> _DirectoryIdentity:
    """Capture a directory identity token without retaining a live handle."""
    canonical_path = os.path.normcase(os.path.realpath(path))
    st = os.stat(canonical_path)
    if not os.path.isdir(canonical_path):
        raise OSError("expected checkpoint directory is not a directory")
    return _DirectoryIdentity(
        canonical_path=canonical_path,
        st_dev=int(st.st_dev),
        st_ino=int(st.st_ino),
    )


def _is_link_or_reparse(path: str) -> bool:
    """Return whether a destructive checkpoint candidate is redirected."""
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if callable(isjunction) and isjunction(path):
        return True
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    return bool(attributes & 0x0400)  # FILE_ATTRIBUTE_REPARSE_POINT


def _checkpoint_guard_key(data_dir: str, workspace_id: str, agent_id: str) -> Tuple[str, str, str]:
    return (os.path.normcase(os.path.abspath(data_dir)), workspace_id, agent_id)


def _discard_checkpoint_root_guard(guard: _CheckpointRootGuard) -> None:
    key = _checkpoint_guard_key(guard.data_dir_input, guard.workspace_id, guard.agent_id)
    with _checkpoint_root_guards_lock:
        if _checkpoint_root_guards.get(key) is guard:
            _checkpoint_root_guards.pop(key, None)


def _record_checkpoint_containment_incident(
    operation: str, workspace_id: str, agent_id: str,
) -> None:
    """Emit a stable, non-secret incident record for a rejected root."""
    log.error(
        "security_incident=%s subsystem=checkpoint operation=%s "
        "workspace_id=%s agent_id=%s failure_class=identity_continuity",
        _FILESYSTEM_CONTAINMENT_EVENT,
        operation,
        _sanitize_log(workspace_id),
        _sanitize_log(agent_id),
    )


def _checkpoint_containment_failure(
    guard: _CheckpointRootGuard, operation: str,
) -> CheckpointContainmentError:
    _discard_checkpoint_root_guard(guard)
    _record_checkpoint_containment_incident(
        operation, guard.workspace_id, guard.agent_id,
    )
    return CheckpointContainmentError(
        "checkpoint filesystem containment or identity continuity validation failed"
    )


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


_CHAR_MOD_SCALAR_FIELDS = (
    "g_mod",
    "theta_lock_mod",
    "warmth",
    "structure",
)
_CHAR_MOD_FIELDS = frozenset(("omega_init", *_CHAR_MOD_SCALAR_FIELDS))


def _serialize_character_modulation(state) -> Dict[str, Any]:
    """Serialize the fixed, internal ``ModelState._char_mod`` schema.

    Character modulation is intentionally not a general JSON payload.  The
    production schema contains one three-element complex initial vector and
    four real scalar modulation values; unknown additions must be made
    explicit here rather than being silently persisted as arbitrary objects.
    """
    char_mod = getattr(state, "_char_mod", {}) or {}
    if not isinstance(char_mod, dict):
        raise TypeError(
            "invalid _char_mod: expected dict, "
            f"got {type(char_mod).__name__}"
        )

    unexpected = [field for field in char_mod if field not in _CHAR_MOD_FIELDS]
    if unexpected:
        raise TypeError(f"unsupported _char_mod.{unexpected[0]}")

    payload: Dict[str, Any] = {}
    if "omega_init" in char_mod:
        omega_init = char_mod["omega_init"]
        if not isinstance(omega_init, np.ndarray):
            raise TypeError(
                "invalid _char_mod.omega_init: expected complex ndarray "
                f"with shape (3,), got {type(omega_init).__name__}"
            )
        if omega_init.shape != (3,):
            raise ValueError(
                "invalid _char_mod.omega_init: expected shape (3,), "
                f"got {omega_init.shape}"
            )
        if not np.issubdtype(omega_init.dtype, np.complexfloating):
            raise TypeError(
                "invalid _char_mod.omega_init: expected complex ndarray, "
                f"got dtype={omega_init.dtype}"
            )
        payload["omega_init"] = _complex_array_to_json(omega_init)

    for field in _CHAR_MOD_SCALAR_FIELDS:
        if field not in char_mod:
            continue
        value = char_mod[field]
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
            raise TypeError(
                f"invalid _char_mod.{field}: expected real numeric scalar, "
                f"got {type(value).__name__}"
            )
        payload[field] = float(value)

    return payload


def _deserialize_character_modulation(data: Any) -> Dict[str, Any]:
    """Restore the supported character modulation values from checkpoint JSON."""
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError(
            "invalid _char_mod: expected dict, "
            f"got {type(data).__name__}"
        )

    char_mod = dict(data)
    if "omega_init" in char_mod:
        try:
            omega_init = _json_to_complex_array(char_mod["omega_init"])
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid _char_mod.omega_init encoding") from exc
        if omega_init.shape != (3,):
            raise ValueError(
                "invalid _char_mod.omega_init: expected decoded shape (3,), "
                f"got {omega_init.shape}"
            )
        char_mod["omega_init"] = omega_init
    return char_mod


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
        "_char_mod": _serialize_character_modulation(state),
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
    state._char_mod = _deserialize_character_modulation(  # type: ignore[attr-defined]
        data.get("_char_mod", {}),
    )
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
    requested_dir = os.path.join(
        base, "workspaces", workspace_id,
        "agents", agent_id, "private", "checkpoints",
    )
    # ``_validated_checkpoint_root`` is the single checkpoint containment
    # contract used by the live builder and compatibility helper.
    return _validated_checkpoint_root(requested_dir, base)


def _capture_checkpoint_root_guard(
    data_dir: str, workspace_id: str, agent_id: str,
) -> _CheckpointRootGuard:
    """Create the first identity snapshot for a checkpoint root."""
    safe_dir = _build_checkpoint_dir(data_dir, workspace_id, agent_id)
    os.makedirs(safe_dir, exist_ok=True)
    # Rebuild after creation so a substituted parent is detected before the
    # initial snapshot is trusted.
    safe_dir = _build_checkpoint_dir(data_dir, workspace_id, agent_id)
    return _CheckpointRootGuard(
        data_dir_input=os.path.abspath(data_dir),
        workspace_id=workspace_id,
        agent_id=agent_id,
        data_root=_directory_identity(data_dir),
        checkpoint_parent=_directory_identity(os.path.dirname(safe_dir)),
        checkpoint_root=_directory_identity(safe_dir),
    )


def _get_checkpoint_root_guard(
    data_dir: str, workspace_id: str, agent_id: str,
) -> _CheckpointRootGuard:
    """Get the bounded cached guard or capture a root for a future check."""
    key = _checkpoint_guard_key(data_dir, workspace_id, agent_id)
    with _checkpoint_root_guards_lock:
        guard = _checkpoint_root_guards.get(key)
        if guard is not None:
            _checkpoint_root_guards.move_to_end(key)
            return guard

    guard = _capture_checkpoint_root_guard(data_dir, workspace_id, agent_id)
    with _checkpoint_root_guards_lock:
        _checkpoint_root_guards[key] = guard
        _checkpoint_root_guards.move_to_end(key)
        while len(_checkpoint_root_guards) > _CHECKPOINT_ROOT_GUARD_MAX:
            _checkpoint_root_guards.popitem(last=False)
    return guard


def _revalidate_checkpoint_root(
    guard: _CheckpointRootGuard, operation: str,
) -> str:
    """Fail closed if a cached checkpoint root has been substituted.

    The checks intentionally happen immediately before a write or destructive
    prune operation.  They provide identity-continuity detection only; they do
    not retain a pinned OS directory handle and therefore do not claim TOCTOU
    race closure.
    """
    try:
        current_data = _directory_identity(guard.data_dir_input)
        if current_data != guard.data_root:
            raise OSError("checkpoint data root identity changed")

        current_root = _build_checkpoint_dir(
            guard.data_dir_input, guard.workspace_id, guard.agent_id,
        )
        current_parent = _directory_identity(os.path.dirname(current_root))
        current_checkpoint_root = _directory_identity(current_root)
        if (
            current_parent != guard.checkpoint_parent
            or current_checkpoint_root != guard.checkpoint_root
        ):
            raise OSError("checkpoint root identity changed")
        return current_checkpoint_root.canonical_path
    except Exception as exc:
        if isinstance(exc, CheckpointContainmentError):
            raise
        raise _checkpoint_containment_failure(guard, operation) from None


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
        # Preserve the existing non-fatal invalid-ID / ordinary-I/O behaviour,
        # while making a previously trusted root substitution a distinct error.
        root_guard = _get_checkpoint_root_guard(data_dir, workspace_id, agent_id)

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

        safe_dir = _revalidate_checkpoint_root(root_guard, "write")
        ckpt_name = _checkpoint_filename(step)
        path = _child_path(safe_dir, ckpt_name)
        tmp = _child_path(safe_dir, ckpt_name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, path)

        # Prune old checkpoints
        _prune_old_checkpoints(root_guard, max_checkpoints)

        log.info("Checkpoint saved: step=%d -> %s", step, _sanitize_log(path))
        return path

    except CheckpointContainmentError:
        # The error is deliberately caller-visible: ordinary checkpoint I/O
        # failures still return None below, but a root substitution must not be
        # mistaken for "checkpoint just was not saved".
        raise
    except Exception as exc:
        log.warning("Checkpoint save failed (step=%d): %s", step, exc)
        return None


def _prune_old_checkpoints(root_guard: _CheckpointRootGuard, keep: int) -> None:
    """Remove oldest checkpoints, keeping at most ``keep``.

    Each candidate is revalidated against the original captured root and the
    current root/parent identities immediately before deletion.  This aborts
    on substitution detection; it does not claim to close the remaining
    check-to-remove race.
    """
    safe_dir = _revalidate_checkpoint_root(root_guard, "prune")
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
        # Keep the strict filename contract even though entries were filtered.
        if not re.fullmatch(r"checkpoint_\d+\.json", name):
            continue
        safe_dir = _revalidate_checkpoint_root(root_guard, "prune")
        try:
            # A symlink/reparse candidate is not a normal checkpoint file.  Do
            # not rely on remove()'s link behaviour for a destructive flow.
            if _is_link_or_reparse(os.path.join(safe_dir, name)):
                raise _checkpoint_containment_failure(root_guard, "prune")
            candidate = _child_path(safe_dir, name)
            os.remove(candidate)
        except CheckpointContainmentError:
            raise
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
    return _build_checkpoint_dir(data_dir, workspace_id, agent_id)
