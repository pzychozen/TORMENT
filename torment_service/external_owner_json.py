"""Strict JSON evidence helpers for onboarding; ordinary loaders are unchanged."""

import json
import math
import os
from pathlib import Path
import stat

from .pathing import validate_portable_new_identifier


class ExternalOwnerConflict(ValueError):
    """An external document is malformed or differs from its intended owner."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExternalOwnerConflict(message)


def _unique_object(pairs):
    require(len({key for key, _ in pairs}) == len(pairs), "duplicate JSON key")
    return dict(pairs)


def finite_json(value, ancestors=frozenset()) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        require(math.isfinite(value), "nonfinite JSON number")
        return
    require(type(value) in (dict, list), "expected plain JSON data")
    require(id(value) not in ancestors, "cyclic JSON data")
    ancestors = ancestors | {id(value)}
    if type(value) is dict:
        require(all(type(k) is str for k in value), "JSON object keys must be strings")
        values = value.values()
    else:
        values = value
    for item in values:
        finite_json(item, ancestors)


def strict_object(raw: bytes) -> dict:
    require(type(raw) is bytes, "external JSON must be raw bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        finite_json(value)
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ExternalOwnerConflict("malformed external JSON (including duplicate keys or nonfinite numbers)") from exc
    require(type(value) is dict, "external owner document must be an object")
    return value


def exact_keys(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), f"{label} has missing or unexpected fields")
    return value


def exact_json(value) -> str:
    finite_json(value)
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def owner_bytes(value: dict, *, sort_keys: bool = True) -> bytes:
    """Match existing owners' json.dump(indent=2) and native text newlines."""
    finite_json(value)
    return json.dumps(value, indent=2, sort_keys=sort_keys, allow_nan=False).replace("\n", os.linesep).encode("utf-8")


def logical_id(value, label):
    require(type(value) is str, f"{label} must be text")
    try:
        return validate_portable_new_identifier(value, label)
    except ValueError as exc:
        raise ExternalOwnerConflict(str(exc)) from exc


def nonempty_text(value, label):
    require(type(value) is str and bool(value.strip()), f"{label} must be nonempty text")
    return value


def integer(value, label, *, minimum=0):
    require(type(value) is int and value >= minimum, f"{label} must be an integer >= {minimum}")
    return value


def read_optional_owner(path: str | Path) -> bytes | None:
    """Absence alone is recoverable; non-files and dangling links refuse."""
    path = Path(path)
    try:
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode), "external owner must be a regular file")
        return path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ExternalOwnerConflict("external owner is not a readable regular file") from exc


def require_exact_owner_path(resolved: str, declared: str) -> str:
    """Keep the existing owner's contained path and reject physical aliases.

    Callers first validate IDs and obtain the path through their existing
    containment helpers. This extra comparison prevents onboarding through a
    differently spelled existing path or a redirected child directory.
    """
    require(resolved == os.path.abspath(declared), "external owner path aliases another spelling or location")
    return resolved
