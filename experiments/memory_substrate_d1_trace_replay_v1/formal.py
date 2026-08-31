"""One-shot formal-administration mechanics, deliberately unauthorized by default.

The runner is an experiment-local safety envelope.  This phase never creates
an authorization manifest and never invokes it against a native route.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable

from .protocol import D1ProtocolError, FrozenAdministrationInputs


class FormalAdministrationRefused(D1ProtocolError):
    """The one-shot formal runner refused before external trace contact."""


@dataclass(frozen=True)
class FormalAdministrationAuthorization:
    administration_id: str
    repository_head: str
    protocol_sha256: str
    fixture_sha256: str
    tolerances_sha256: str
    result_root: str
    authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.administration_id, str) or not self.administration_id:
            raise FormalAdministrationRefused("formal administration ID is required")
        if not isinstance(self.repository_head, str) or len(self.repository_head) != 40:
            raise FormalAdministrationRefused("formal authorization requires the exact repository HEAD")
        if any(not isinstance(value, str) or len(value) != 64 for value in (
            self.protocol_sha256, self.fixture_sha256, self.tolerances_sha256,
        )):
            raise FormalAdministrationRefused("formal authorization requires immutable input hashes")
        if not isinstance(self.result_root, str) or not Path(self.result_root).is_absolute():
            raise FormalAdministrationRefused("formal result root must be an absolute path")

    def verify(self, inputs: FrozenAdministrationInputs, *, expected_head: str) -> None:
        if self.authorized is not True:
            raise FormalAdministrationRefused("formal administration has no explicit one-administration authorization")
        if self.repository_head != expected_head:
            raise FormalAdministrationRefused("formal authorization does not name the expected repository HEAD")
        if (
            self.protocol_sha256 != inputs.protocol_sha256
            or self.fixture_sha256 != inputs.fixture_sha256
            or self.tolerances_sha256 != inputs.tolerances_sha256
        ):
            raise FormalAdministrationRefused("formal authorization hashes do not match frozen administration inputs")


@dataclass(frozen=True)
class FormalResultSchema:
    """Unpopulated result shape; no outcome values are authored in preflight."""

    administration_id: str
    harness_validity: str | None = None
    storage_substrate_verdict: str | None = None
    qualified_post_write_verdict: str | None = None
    optional_feature_divergences: tuple[dict[str, Any], ...] = ()
    known_unsupported_edges: tuple[str, ...] = ()
    m1: dict[str, Any] | None = None
    m2: dict[str, Any] | None = None
    m3: dict[str, Any] | None = None
    m4: dict[str, Any] | None = None
    m5: dict[str, Any] | None = None
    sequential: dict[str, Any] | None = None
    character: dict[str, Any] | None = None
    restart_evidence: tuple[dict[str, Any], ...] = ()
    retrieval_characterization: tuple[dict[str, Any], ...] = ()
    native_structural_invariants: tuple[dict[str, Any], ...] = ()
    timestamp_generation_parity_tested: bool = False
    timestamp_preservation_parity_tested: bool = True
    closed_loop_query_parity_tested: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.administration_id, str) or not self.administration_id:
            raise FormalAdministrationRefused("formal result requires an administration ID")
        if self.timestamp_generation_parity_tested or not self.timestamp_preservation_parity_tested or self.closed_loop_query_parity_tested:
            raise FormalAdministrationRefused("formal result schema has immutable D1 timestamp/query declarations")


class FormalAdministrationRunner:
    """Atomic marker-first runner with no fallback or implicit retry behaviour."""

    def __init__(self, *, repository_root: str | Path, expected_repository_head: str) -> None:
        self._repository_root = Path(repository_root).resolve()
        self._expected_head = expected_repository_head
        if not self._repository_root.is_dir() or not isinstance(expected_repository_head, str) or len(expected_repository_head) != 40:
            raise FormalAdministrationRefused("formal runner requires an exact repository root and expected HEAD")

    def run(
        self,
        *,
        authorization: FormalAdministrationAuthorization | None,
        inputs: FrozenAdministrationInputs,
        protocol_sha256: str,
        fixture_sha256: str,
        verify_baselines_and_fixture: Callable[[], None],
        contact_formal_trace: Callable[[], FormalResultSchema],
    ) -> FormalResultSchema:
        if authorization is None:
            raise FormalAdministrationRefused("formal administration authorization is absent")
        authorization.verify(inputs, expected_head=self._expected_head)
        inputs.verify(protocol_sha256=protocol_sha256, fixture_sha256=fixture_sha256)
        if self._current_head() != self._expected_head:
            raise FormalAdministrationRefused("formal runner repository HEAD changed after fixture freeze")
        verify_baselines_and_fixture()
        result_root = Path(authorization.result_root)
        marker = result_root.parent / f".{authorization.administration_id}.administration-started.json"
        if result_root.exists() or marker.exists():
            raise FormalAdministrationRefused("formal administration ID or result root was already used")
        self._write_marker_exclusive(marker, authorization)
        try:
            result_root.mkdir(parents=False, exist_ok=False)
            # The marker is durable before this callback can send a legacy or
            # native request.  There is intentionally no catch-and-retry path.
            result = contact_formal_trace()
            if not isinstance(result, FormalResultSchema):
                raise FormalAdministrationRefused("formal trace callback returned an invalid result schema")
            self._write_result_exclusive(result_root / "result.json", result)
            return result
        except Exception as exc:
            if result_root.is_dir():
                failure = {
                    "administration_id": authorization.administration_id,
                    "harness_validity": "EXPERIMENT_HARNESS_FAILURE",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                self._write_json_exclusive(result_root / "result.json", failure)
            raise

    def _current_head(self) -> str:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self._repository_root,
            check=True, capture_output=True, text=True,
        )
        return completed.stdout.strip()

    @staticmethod
    def _write_marker_exclusive(path: Path, authorization: FormalAdministrationAuthorization) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(authorization), sort_keys=True, separators=(",", ":")).encode("utf-8")
        try:
            descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise FormalAdministrationRefused("formal administration marker already exists") from exc
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)

    @staticmethod
    def _write_json_exclusive(path: Path, value: Any) -> None:
        payload = json.dumps(value, sort_keys=True, indent=2, default=str).encode("utf-8") + b"\n"
        try:
            descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise FormalAdministrationRefused("formal result overwrite refused") from exc
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)

    def _write_result_exclusive(self, path: Path, result: FormalResultSchema) -> None:
        self._write_json_exclusive(path, asdict(result))
