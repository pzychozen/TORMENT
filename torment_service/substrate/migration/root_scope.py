"""Typed root-wide scope identity for generalized admission evidence.

This module is administrative only.  It deliberately does not allocate a
namespace, create a scope row, open SQLite, or infer a scope from a path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from torment_service.pathing import validate_structural_path_component

from ..errors import SubstrateConfigurationError


class RootScopeKind(StrEnum):
    """The two root-wide materialized-memory scope kinds."""

    PRIVATE = "PRIVATE"
    SHARED = "SHARED"


class RootScopeKeyError(SubstrateConfigurationError):
    """Raised when a root-wide scope key is malformed or ambiguous."""


@dataclass(frozen=True)
class RootScopeKey:
    """A non-colliding root-wide private or shared scope identity."""

    workspace_id: str
    scope_kind: RootScopeKind
    agent_id: str | None = None
    domain_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.workspace_id, "workspace_id")
        if not isinstance(self.scope_kind, RootScopeKind):
            raise RootScopeKeyError("scope_kind must be RootScopeKind")
        if self.scope_kind is RootScopeKind.PRIVATE:
            if self.agent_id is None:
                raise RootScopeKeyError("PRIVATE scope requires agent_id")
            if self.domain_id is not None:
                raise RootScopeKeyError("PRIVATE scope forbids domain_id")
            _identifier(self.agent_id, "agent_id")
        else:
            if self.domain_id is None:
                raise RootScopeKeyError("SHARED scope requires domain_id")
            if self.agent_id is not None:
                raise RootScopeKeyError("SHARED scope forbids agent_id")
            _identifier(self.domain_id, "domain_id")

    @property
    def qualifier(self) -> str:
        return self.agent_id if self.scope_kind is RootScopeKind.PRIVATE else self.domain_id or ""

    @property
    def canonical_key(self) -> tuple[str, str, str]:
        """Stable evidence ordering only; it is never runtime priority."""
        return (self.workspace_id, self.scope_kind.value, self.qualifier)

    def identity_payload(self) -> dict[str, str | None]:
        return {
            "workspace_id": self.workspace_id,
            "scope_kind": self.scope_kind.value,
            "agent_id": self.agent_id,
            "domain_id": self.domain_id,
        }


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RootScopeKeyError(f"{label} must be non-empty text")
    try:
        return validate_structural_path_component(value, label)
    except ValueError as exc:
        raise RootScopeKeyError(str(exc)) from exc


__all__ = ["RootScopeKey", "RootScopeKeyError", "RootScopeKind"]
