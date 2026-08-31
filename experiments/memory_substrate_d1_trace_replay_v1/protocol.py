"""Immutable 7G5D1 protocol vocabulary and pre-administration guards."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import hashlib
import json
import os
import platform
from pathlib import Path
import sys
from typing import Any, Mapping


D1_PROTOCOL_VERSION = "memory-substrate-d1-trace-replay-v1"
FORMAL_ADMINISTRATION_AUTHORIZED = False
D1_RUNTIME_FLAG_NAMES = (
    "TORMENT_DATA_DIR",
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_EMBED_MODEL",
    "TORMENT_EMBED_STRICT",
    "TORMENT_HASH_DIM",
    "TORMENT_REINFORCE_SIM_THRESHOLD",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_CHARACTER_DRIFT_CHECK_EVERY",
    "TORMENT_CHECKPOINT_ENABLE",
    "TORMENT_CHECKPOINT_INTERVAL",
    "TORMENT_COMPRESS_ENABLE",
    "TORMENT_COMPRESS_MIN_STEP",
    "TORMENT_HIVEMIND_ENABLE",
    "TORMENT_SRG_ENABLE",
    "TORMENT_AFFECT_ENABLE",
)
_TOLERANCE_INTENT = {
    "centroid_rtol": 1e-6,
    "centroid_atol": 1e-7,
    "scalar_atol": 1e-6,
    "character_drift_atol": 1e-6,
    "retrieval_score_atol": 1e-6,
    "ranking_order_epsilon": 1e-6,
}


class D1ProtocolError(RuntimeError):
    """Raised when a D1 input tries to widen the frozen experiment."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_value(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ComparisonTolerances:
    centroid_rtol: float
    centroid_atol: float
    scalar_atol: float
    character_drift_atol: float
    retrieval_score_atol: float
    ranking_order_epsilon: float

    def intent(self) -> dict[str, float]:
        return dict(asdict(self))

    @property
    def digest(self) -> str:
        return sha256_value(self.intent())


FROZEN_TOLERANCES = ComparisonTolerances(**_TOLERANCE_INTENT)


def require_frozen_tolerances(value: ComparisonTolerances) -> None:
    if value != FROZEN_TOLERANCES:
        raise D1ProtocolError("D1 comparison tolerances are immutable")


class ReplayOperationKeyRegistry:
    """Deterministic D1 operation keys with explicit retry reuse protection.

    The registry is intentionally tiny and experiment-local.  It makes the
    idempotency fact testable before replay, without inventing a production
    operation or migration namespace.
    """

    def __init__(self) -> None:
        self._claims: dict[tuple[str, int], tuple[str, str]] = {}
        self._keys: dict[str, tuple[str, int]] = {}

    def claim(self, *, fixture_id: str, ordinal: int, request_sha256: str) -> str:
        if not isinstance(fixture_id, str) or not fixture_id:
            raise D1ProtocolError("D1 operation key requires a fixture ID")
        if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 0:
            raise D1ProtocolError("D1 operation key requires a non-negative ordinal")
        if not isinstance(request_sha256, str) or len(request_sha256) != 64:
            raise D1ProtocolError("D1 operation key requires a frozen request SHA256")
        claim = (fixture_id, ordinal)
        existing = self._claims.get(claim)
        if existing is not None:
            if existing[0] != request_sha256:
                raise D1ProtocolError("D1 retry key was reused for different request bytes")
            return existing[1]
        key = f"D1:REPLAY:{fixture_id}:{ordinal}:{request_sha256[:24]}"
        prior = self._keys.get(key)
        if prior is not None and prior != claim:
            raise D1ProtocolError("D1 operation-key collision")
        self._claims[claim] = (request_sha256, key)
        self._keys[key] = claim
        return key


class StoreDisposition(StrEnum):
    IN_SCOPE_EXACT = "IN_SCOPE_EXACT"
    IN_SCOPE_TOLERANCE = "IN_SCOPE_TOLERANCE"
    OUT_OF_PROFILE = "OUT_OF_PROFILE"
    ACCELERATION_EXCLUDED = "ACCELERATION_EXCLUDED"
    PROCESS_LOCAL = "PROCESS_LOCAL"


class StorePresence(StrEnum):
    REQUIRED_PRESENT = "REQUIRED_PRESENT"
    OPTIONAL_PRESENT = "OPTIONAL_PRESENT"


@dataclass(frozen=True)
class StoreDispositionRule:
    path: str
    disposition: StoreDisposition
    presence: StorePresence = StorePresence.REQUIRED_PRESENT

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path:
            raise D1ProtocolError("store disposition path is required")
        if not isinstance(self.disposition, StoreDisposition) or not isinstance(self.presence, StorePresence):
            raise D1ProtocolError("store disposition rule uses unrecognized frozen vocabulary")


@dataclass(frozen=True)
class StoreDispositionManifest:
    """Complete, predeclared disposition for every observed store path."""

    rules: tuple[StoreDispositionRule, ...]

    def __post_init__(self) -> None:
        paths = [rule.path for rule in self.rules]
        if len(set(paths)) != len(paths):
            raise D1ProtocolError("store dispositions require unique non-empty paths")

    def validate_observed(self, observed_paths: set[str]) -> None:
        declared = {rule.path for rule in self.rules}
        unknown = sorted(observed_paths - declared)
        missing = sorted(
            rule.path for rule in self.rules
            if rule.presence is StorePresence.REQUIRED_PRESENT and rule.path not in observed_paths
        )
        if unknown:
            raise D1ProtocolError(f"unclassified observed stores: {unknown}")
        if missing:
            raise D1ProtocolError(f"declared stores were not observed: {missing}")

    @property
    def digest(self) -> str:
        return sha256_value([(rule.path, rule.disposition.value, rule.presence.value) for rule in self.rules])


@dataclass(frozen=True)
class EnvironmentFingerprint:
    python: str
    sqlite_module: str
    sqlite_runtime: str
    numpy: str
    embedder_provider: str
    embedder_model: str
    embedder_dimension: int
    runtime_flags: tuple[tuple[str, str | None], ...]
    repository_head: str
    platform: str

    @classmethod
    def collect(
        cls,
        *,
        embedder: Any,
        repository_head: str,
        runtime_flag_names: tuple[str, ...] = D1_RUNTIME_FLAG_NAMES,
    ) -> "EnvironmentFingerprint":
        import numpy
        import sqlite3

        if not isinstance(repository_head, str) or not repository_head:
            raise D1ProtocolError("repository HEAD must be recorded")
        dimension = getattr(embedder, "dim", None)
        if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
            raise D1ProtocolError("embedder dimension must be a positive integer")
        flags = tuple((name, os.environ.get(name)) for name in sorted(set(runtime_flag_names)))
        return cls(
            python=sys.version.split()[0],
            sqlite_module=sqlite3.version,
            sqlite_runtime=sqlite3.sqlite_version,
            numpy=numpy.__version__,
            embedder_provider=str(getattr(embedder, "provider", "")),
            embedder_model=str(getattr(embedder, "model", "")),
            embedder_dimension=dimension,
            runtime_flags=flags,
            repository_head=repository_head,
            platform=platform.platform(),
        )

    @property
    def digest(self) -> str:
        return sha256_value(asdict(self))


def protocol_document_sha256(path: str | Path) -> str:
    document = Path(path)
    if not document.is_file():
        raise D1ProtocolError("D1 protocol document is missing")
    return hashlib.sha256(document.read_bytes()).hexdigest()


@dataclass(frozen=True)
class FrozenAdministrationInputs:
    protocol_sha256: str
    fixture_sha256: str
    tolerances_sha256: str

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or len(value) != 64 for value in asdict(self).values()):
            raise D1ProtocolError("D1 freeze inputs require SHA256 digests")

    def verify(self, *, protocol_sha256: str, fixture_sha256: str) -> None:
        if self.protocol_sha256 != protocol_sha256 or self.fixture_sha256 != fixture_sha256:
            raise D1ProtocolError("protocol or fixture bytes changed after freeze")
        if self.tolerances_sha256 != FROZEN_TOLERANCES.digest:
            raise D1ProtocolError("comparison tolerances changed after freeze")


def refuse_formal_administration(inputs: FrozenAdministrationInputs | None = None) -> None:
    """Make the lack of D1 administration authority executable, not editorial."""
    if inputs is None:
        raise D1ProtocolError("formal administration requires frozen protocol and fixture hashes")
    if not FORMAL_ADMINISTRATION_AUTHORIZED:
        raise D1ProtocolError("formal D1 administration is not authorized by the preflight harness")
