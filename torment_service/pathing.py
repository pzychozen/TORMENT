"""Centralised path-safety helpers for TORMENT Fabric.

Every filesystem path that includes a dynamic component (workspace ID,
agent ID, domain ID, user-supplied filename, etc.) **must** pass through
one of the helpers in this module before being used in a filesystem sink
(``os.makedirs``, ``open``, ``os.listdir``, ``os.remove``, etc.).

The helpers enforce three invariants:

1. Dynamic path components are sanitised (no ``..``, ``/``, ``\\``).
2. Resolved paths are validated to remain inside an approved base directory.
3. ``os.path.realpath`` + ``str.startswith`` guards are **inline and
   local** so that CodeQL's taint tracker can verify them without needing
   to follow into called functions.

Layout conventions
------------------

* Durable named entities::

      <base>/state/<category>/<shard>/<safe-id>.json

* High-frequency append-only event logs::

      <base>/logs/<category>/daily/YYYY-MM-DD.jsonl

* SQLite / index files::

      <base>/index/<name>

* Temporary artefacts::

      <base>/tmp/<name>
"""

from __future__ import annotations

import datetime
import hashlib
import os
import re
from typing import Optional


# ---------------------------------------------------------------------------
# 1. safe_slug — sanitise a dynamic path component
# ---------------------------------------------------------------------------

def safe_slug(value: str, label: str = "identifier") -> str:
    """Validate that *value* is safe to embed in a filesystem path.

    Rejects empty strings, ``..``, forward-slash, and back-slash.
    Returns *value* unchanged if valid; raises ``ValueError`` otherwise.

    This replaces the per-module ``_validate_path_component`` duplicates.
    """
    if not value or ".." in value or "/" in value or "\\" in value:
        raise ValueError(
            f"Invalid {label}: must be non-empty and free of "
            f"path separators or '..'; got {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# 2. ensure_within_base — post-hoc containment check
# ---------------------------------------------------------------------------

def ensure_within_base(path: str, base_dir: str) -> str:
    """Resolve *path* and verify it is inside *base_dir*.

    Returns the resolved absolute path.
    Raises ``ValueError`` if the path escapes the base.
    """
    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(path)
    if resolved != base and not resolved.startswith(base + os.sep):
        raise ValueError(f"Path escapes base directory: {resolved!r}")
    return resolved


# ---------------------------------------------------------------------------
# 3. safe_join — build a validated sub-path under a trusted base
# ---------------------------------------------------------------------------

def safe_join(base: str, *parts: str) -> str:
    """Join *parts* under *base*, resolve, and verify containment.

    ``base`` is resolved via ``realpath`` first, so symlinks in the base
    itself are tolerated.  The assembled result must remain inside that
    resolved base (``startswith`` check).

    Returns the resolved absolute path.
    """
    real_base = os.path.realpath(base)
    joined = os.path.realpath(os.path.join(real_base, *parts))
    if joined != real_base and not joined.startswith(real_base + os.sep):
        raise ValueError(
            f"Joined path escapes base directory: {joined!r} "
            f"is not under {real_base!r}"
        )
    return joined


# ---------------------------------------------------------------------------
# 4. shard_for_key — deterministic hex-bucket from a string key
# ---------------------------------------------------------------------------

def shard_for_key(key: str, n: int = 256) -> str:
    """Return a 2-char hex shard directory name for *key*.

    Uses a truncated SHA-256 to distribute keys across *n* buckets
    (default 256 → ``"00"`` … ``"ff"``).
    """
    digest = hashlib.sha256(key.encode("utf-8", errors="replace")).hexdigest()
    bucket = int(digest[:4], 16) % n
    return f"{bucket:02x}"


# ---------------------------------------------------------------------------
# 5. sharded_entity_path — state/<category>/<shard>/<safe-id>.<ext>
# ---------------------------------------------------------------------------

def sharded_entity_path(
    base: str,
    category: str,
    key: str,
    ext: str = ".json",
) -> str:
    """Build a sharded entity storage path.

    Returns::

        <base>/state/<category>/<shard>/<safe-key><ext>

    ``key`` is slugified and the result is verified to stay inside *base*.
    """
    safe_cat = safe_slug(category, "category")
    safe_key = safe_slug(key, "entity key")
    shard = shard_for_key(safe_key)
    return safe_join(base, "state", safe_cat, shard, safe_key + ext)


# ---------------------------------------------------------------------------
# 6. dated_log_path — logs/<category>/daily/YYYY-MM-DD.jsonl
# ---------------------------------------------------------------------------

def dated_log_path(
    base: str,
    category: str,
    *,
    date: Optional[datetime.date] = None,
) -> str:
    """Build a date-partitioned append-only log path.

    Returns::

        <base>/logs/<category>/daily/YYYY-MM-DD.jsonl

    Uses today's date (UTC) when *date* is ``None``.
    """
    safe_cat = safe_slug(category, "log category")
    day = date or datetime.datetime.utcnow().date()
    day_str = day.isoformat()  # YYYY-MM-DD
    # Extra guard: day_str is trusted (from datetime), but belt-and-suspenders
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day_str):
        raise ValueError(f"Unexpected date format: {day_str!r}")
    return safe_join(base, "logs", safe_cat, "daily", day_str + ".jsonl")


# ---------------------------------------------------------------------------
# 7. approved_subdir — build and optionally create a nested subdirectory
# ---------------------------------------------------------------------------

def approved_subdir(base: str, *parts: str, mkdir: bool = True) -> str:
    """Build a nested subdirectory path under *base* and optionally create it.

    Each element in *parts* is validated via ``safe_slug`` before joining.
    The assembled path is resolved and verified to stay inside *base*.

    When *mkdir* is ``True`` (the default), the directory is created if it
    does not already exist.

    Returns the resolved absolute path.
    """
    sanitised = [safe_slug(p, f"subdir part [{i}]") for i, p in enumerate(parts)]
    result = safe_join(base, *sanitised)
    if mkdir:
        os.makedirs(result, exist_ok=True)
    return result


# ---------------------------------------------------------------------------
# 8. stable_filename — derive a child file from a trusted root
# ---------------------------------------------------------------------------

def stable_filename(root: str, filename: str) -> str:
    """Derive a child file path from a canonical *root* directory.

    ``filename`` must be a simple name (no separators, no ``..``).
    The result is resolved and verified to remain inside *root*.

    This is the centralised replacement for the per-module
    ``_child_path`` helper.
    """
    if not filename or ".." in filename or os.sep in filename or "/" in filename or "\\" in filename:
        raise ValueError(f"Invalid filename: {filename!r}")
    real_root = os.path.realpath(root)
    child = os.path.realpath(os.path.join(real_root, filename))
    if not child.startswith(real_root + os.sep):
        raise ValueError(
            f"Child path escapes root: {child!r} not under {real_root!r}"
        )
    return child
