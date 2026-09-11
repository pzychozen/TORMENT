"""Bounded, read-only installation presence; never migration or startup authority.

Historical witnesses are workspace identity ownership (Fabric's permissive
metadata generation), per-EID MemoryGraph storage, and EmbeddingShardWriter v1
storage, including empty materialized scopes. This is presence evidence, not a
whole-installation integrity audit. Other legacy side files need not be modernized.
See docs/TORMENT_I11_LEGACY_FRESH_INSTALL_RETIREMENT.md for the evidence grammar.
"""
from __future__ import annotations

import ast
from enum import Enum
import json
import os
from pathlib import Path
import re
import stat

from .genesis_contracts import GenesisAcceptedStart


class PreselectorRootClass(str, Enum):
    FRESH_UNINITIALIZED = "FRESH_UNINITIALIZED"
    EXISTING_LEGACY = "EXISTING_LEGACY"
    AMBIGUOUS_OR_INVALID = "AMBIGUOUS_OR_INVALID"


_MAX_ENTRIES = 32_768
_MAX_DOCUMENT_BYTES = 1_048_576
_MAX_NODE_LINES = 128
_MAX_NPY_HEADER_BYTES = 65_536
_FLOAT_DTYPE = re.compile(r"[<>=|]f([248])\Z")


class _InvalidEvidence(ValueError):
    pass


def _kind(path: Path) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    # Windows junctions/reparse points must not redirect presence inspection.
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise _InvalidEvidence("redirected evidence")
    if stat.S_ISDIR(info.st_mode):
        return "directory"
    if stat.S_ISREG(info.st_mode):
        return "file"
    raise _InvalidEvidence("nonregular evidence")


def _children(path: Path, budget: list[int]) -> list[Path]:
    kind = _kind(path)
    if kind is None:
        return []
    if kind != "directory":
        raise _InvalidEvidence("expected directory")
    children = []
    with os.scandir(path) as entries:
        for entry in entries:
            budget[0] -= 1
            if budget[0] < 0:
                raise _InvalidEvidence("inspection bound exceeded")
            children.append(path / entry.name)
    return sorted(children, key=lambda child: child.name)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidEvidence("duplicate object key")
        result[key] = value
    return result


def _json(raw: bytes) -> dict:
    def reject_constant(_value):
        raise _InvalidEvidence("nonfinite JSON")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                       parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise _InvalidEvidence("expected object")
    return value


def _document(path: Path) -> dict:
    if _kind(path) != "file":
        raise _InvalidEvidence("expected file")
    with path.open("rb") as handle:
        raw = handle.read(_MAX_DOCUMENT_BYTES + 1)
    if len(raw) > _MAX_DOCUMENT_BYTES:
        raise _InvalidEvidence("document bound exceeded")
    return _json(raw)


def _npy_shape(path: Path, *, itemsize: int | None = None) -> tuple[int, ...] | None:
    """Inspect only the numeric NPY header and length, without loading a vector."""
    if _kind(path) is None:
        return None
    if _kind(path) != "file":
        raise _InvalidEvidence("expected representation file")
    with path.open("rb") as handle:
        prefix = handle.read(8)
        if prefix[:6] != b"\x93NUMPY" or prefix[6:] not in (b"\x01\x00", b"\x02\x00", b"\x03\x00"):
            raise _InvalidEvidence("invalid NPY version")
        width = 2 if prefix[6] == 1 else 4
        length = handle.read(width)
        if len(length) != width:
            raise _InvalidEvidence("truncated NPY header")
        size = int.from_bytes(length, "little")
        if size > _MAX_NPY_HEADER_BYTES:
            raise _InvalidEvidence("NPY header bound exceeded")
        raw = handle.read(size)
        if len(raw) != size:
            raise _InvalidEvidence("truncated NPY header")
        header = ast.literal_eval(raw.decode("utf-8" if prefix[6] == 3 else "latin1"))
        if not isinstance(header, dict) or set(header) != {"descr", "fortran_order", "shape"}:
            raise _InvalidEvidence("invalid NPY header")
        dtype = _FLOAT_DTYPE.fullmatch(str(header["descr"]))
        shape = header["shape"]
        if (dtype is None or header["fortran_order"] is not False or not isinstance(shape, tuple)
                or len(shape) not in (1, 2) or any(type(n) is not int or n <= 0 for n in shape)):
            raise _InvalidEvidence("invalid numeric representation")
        expected_size = int(dtype[1])
        if itemsize is not None and expected_size != itemsize:
            raise _InvalidEvidence("NPY dtype mismatch")
        for count in shape:
            expected_size *= count
        if os.fstat(handle.fileno()).st_size != handle.tell() + expected_size:
            raise _InvalidEvidence("NPY data length mismatch")
    return shape


def _workspace_owner(workspace: Path) -> bool:
    metadata = workspace / "workspace_meta.json"
    if _kind(metadata) is None:
        return False
    value = _document(metadata)
    # F7 explicitly supports the old identity-only payload. Do not require
    # Genesis's five-field metadata closure or a host representation profile.
    if value.get("workspace_id") != workspace.name:
        raise _InvalidEvidence("workspace owner mismatch")
    domains = workspace / "domains.json"
    if _kind(domains) is not None:
        names = _document(domains).get("domains")
        if not isinstance(names, list) or any(not isinstance(name, str) or not name for name in names):
            raise _InvalidEvidence("invalid domains owner")
    return True


def _scope_owner(scope: Path) -> bool:
    if _kind(scope) is None:
        return False
    if _kind(scope) != "directory":
        raise _InvalidEvidence("expected scope directory")
    storage = scope / "embeddings"
    if _kind(storage) is not None:
        if _kind(storage) != "directory":
            raise _InvalidEvidence("expected storage directory")
        manifest = storage / "manifest.json"
        if _kind(manifest) is not None:
            value = _document(manifest)
            keys = ("version", "embedding_dim", "rows_per_shard", "active_shard", "next_row", "total_rows")
            if any(type(value.get(key)) is not int for key in keys):
                raise _InvalidEvidence("invalid shard manifest")
            if (value["version"] != 1 or value.get("dtype") != "float32" or value["embedding_dim"] <= 0
                    or value["rows_per_shard"] <= 0 or value["active_shard"] < 0
                    or not 0 <= value["next_row"] <= value["rows_per_shard"]
                    or value["total_rows"] != value["active_shard"] * value["rows_per_shard"] + value["next_row"]):
                raise _InvalidEvidence("invalid shard counters")
            shard = storage / f"shard_{value['active_shard']:06d}.npy"
            if _npy_shape(shard, itemsize=4) == (value["rows_per_shard"], value["embedding_dim"]):
                return True
    nodes = scope / "nodes.jsonl"
    if _kind(nodes) is None:
        return False
    if _kind(nodes) != "file":
        raise _InvalidEvidence("expected nodes file")
    # One matching historical node/vector pair proves presence. Do not parse
    # or migrate a whole append-only log, nor claim complete graph integrity.
    with nodes.open("rb") as handle:
        for _ in range(_MAX_NODE_LINES):
            line = handle.readline(_MAX_DOCUMENT_BYTES + 1)
            if not line:
                break
            if len(line) > _MAX_DOCUMENT_BYTES:
                raise _InvalidEvidence("node line bound exceeded")
            if not line.strip():
                continue
            node = _json(line)
            eid = node.get("eid")
            if type(eid) is not int or eid < 0 or not isinstance(node.get("payload", {}), dict):
                raise _InvalidEvidence("invalid historical node")
            shape = _npy_shape(scope / f"emb_{eid}.npy")
            if shape is not None and len(shape) == 1:
                return True
    return False


def _fresh(root: Path, children: list[Path], budget: list[int]) -> bool:
    """Recognize only Genesis's harmless files and fixed pre-intent controls."""
    pending = list(children)
    controls = set(GenesisAcceptedStart.CONTROL_ENTRIES)
    while pending:
        path = pending.pop()
        relative = path.relative_to(root).as_posix()
        kind = _kind(path)
        if relative in GenesisAcceptedStart.ALLOWED_FILES and kind == "file":
            continue
        if relative not in controls:
            return False
        if relative.endswith("root-onboarding.lock"):
            if kind != "file":
                return False
        elif kind == "directory":
            pending.extend(_children(path, budget))
        else:
            return False
    return True


def classify_preselector_root(data_root: str | Path) -> PreselectorRootClass:
    """Read presence without creating a root, opening SQLite, or constructing runtime."""
    try:
        if not isinstance(data_root, (str, Path)) or not str(data_root).strip():
            return PreselectorRootClass.AMBIGUOUS_OR_INVALID
        root = Path(os.path.abspath(os.path.expanduser(str(data_root))))
        if _kind(root) is None:
            return PreselectorRootClass.FRESH_UNINITIALIZED
        budget = [_MAX_ENTRIES]
        children = _children(root, budget)
        if _fresh(root, children, budget):
            return PreselectorRootClass.FRESH_UNINITIALIZED
        for workspace in _children(root / "workspaces", budget):
            if _kind(workspace) != "directory":
                raise _InvalidEvidence("expected workspace directory")
            if _workspace_owner(workspace):
                return PreselectorRootClass.EXISTING_LEGACY
            for owners, leaf in (("agents", "private"), ("domains", "shared")):
                for owner in _children(workspace / owners, budget):
                    if _kind(owner) != "directory":
                        raise _InvalidEvidence("expected scope owner directory")
                    if _scope_owner(owner / leaf):
                        return PreselectorRootClass.EXISTING_LEGACY
    except (OSError, ValueError, TypeError, SyntaxError, RecursionError, OverflowError):
        pass
    return PreselectorRootClass.AMBIGUOUS_OR_INVALID
