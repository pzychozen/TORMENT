"""Immutable environment-fingerprint writer used by the D1 concrete freeze."""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess

from torment_service.embeddings import HashEmbedding

from .protocol import D1ProtocolError, EnvironmentFingerprint


def write_environment_fingerprint(*, destination: str | Path, repository_root: str | Path) -> EnvironmentFingerprint:
    """Collect exactly the active interpreter/runtime and write a new JSON file."""
    root = Path(repository_root).resolve()
    target = Path(destination).resolve()
    if target.exists():
        raise D1ProtocolError("D1 environment fingerprint destination must be new")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    fingerprint = EnvironmentFingerprint.collect(embedder=HashEmbedding(), repository_head=head)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError as exc:
        raise D1ProtocolError("D1 environment fingerprint destination already exists") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(json.dumps({"schema": "memory-substrate-d1-environment-v1", "fingerprint": asdict(fingerprint)}, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    return fingerprint


__all__ = ["write_environment_fingerprint"]
