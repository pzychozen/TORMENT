"""L0 construction through the real legacy HTTP surface only."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol
from urllib.request import Request, urlopen

from .manifest import LegacyBaselineFingerprint, fingerprint_legacy_baseline
from .protocol import D1ProtocolError


class HttpTransport(Protocol):
    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]: ...


class UrllibHttpTransport:
    """Small standard-library client; no in-process Fabric shortcut exists here."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 20.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            self._base_url + path, data=body, method=method,
            headers={"Content-Type": "application/json"} if body is not None else {},
        )
        with urlopen(request, timeout=self._timeout_seconds) as response:  # nosec B310 -- explicit operator URL
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            raise D1ProtocolError(f"legacy service returned a non-object for {path}")
        return decoded


@dataclass(frozen=True)
class LegacyBaselineSpec:
    data_root: str | Path
    workspace_id: str
    agent_id: str
    character_seed: dict[str, Any]
    domain_id: str = "research"

    def __post_init__(self) -> None:
        root = Path(self.data_root).resolve()
        if not root.is_absolute() or not all(isinstance(value, str) and value for value in (self.workspace_id, self.agent_id, self.domain_id)):
            raise D1ProtocolError("L0 requires an absolute dedicated root and explicit identifiers")
        if self.domain_id != "research":
            raise D1ProtocolError("D1 L0 is fixed to the research domain")
        if not isinstance(self.character_seed, dict) or not self.character_seed:
            raise D1ProtocolError("L0 requires a frozen ordinary Character seed")


@dataclass(frozen=True)
class LegacyBaselineReceipt:
    workspace_response: dict[str, Any]
    agent_response: dict[str, Any]
    formal_trace_administered: bool = False


class LegacyBaselineBuilder:
    """Create L0 through HTTP, then fingerprint only after external shutdown."""

    def __init__(self, transport: HttpTransport, spec: LegacyBaselineSpec) -> None:
        self._transport = transport
        self._spec = spec

    def create_l0(self) -> LegacyBaselineReceipt:
        workspace = self._transport.request("POST", "/workspace/create", {
            "workspace_id": self._spec.workspace_id, "domains": ["research"],
        })
        if workspace.get("workspace_id") != self._spec.workspace_id or workspace.get("domains") != ["research"]:
            raise D1ProtocolError("legacy service did not create the requested research-only workspace")
        agent = self._transport.request("POST", "/agent/create", {
            "workspace_id": self._spec.workspace_id,
            "agent_id": self._spec.agent_id,
            "seed": self._spec.character_seed,
        })
        if agent.get("workspace_id") != self._spec.workspace_id or agent.get("agent_id") != self._spec.agent_id:
            raise D1ProtocolError("legacy service did not create the requested baseline agent")
        return LegacyBaselineReceipt(workspace, agent)

    def freeze_after_clean_shutdown(self, *, service_has_stopped: bool) -> LegacyBaselineFingerprint:
        if service_has_stopped is not True:
            raise D1ProtocolError("L0 may be fingerprinted only after clean legacy service shutdown")
        return fingerprint_legacy_baseline(
            root=self._spec.data_root, workspace_id=self._spec.workspace_id,
            agent_id=self._spec.agent_id, domain_id=self._spec.domain_id,
        )
