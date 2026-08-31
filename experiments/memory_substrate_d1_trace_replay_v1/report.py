"""Durable, result-neutral D1 preflight reporting types."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any

from .protocol import D1ProtocolError, EnvironmentFingerprint, FrozenAdministrationInputs


@dataclass(frozen=True)
class D1PreflightReport:
    """Records construction evidence without representing a D1 comparison run."""

    environment: EnvironmentFingerprint
    frozen_inputs: FrozenAdministrationInputs
    l0_construction_ready: bool
    n0_construction_ready: bool
    b4a_baseline_confirmed: bool
    microtrace_fixtures_frozen: bool
    sequential_fixture_frozen: bool
    character_subarm_fixture_frozen: bool
    formal_administration_run: bool = False
    results: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.formal_administration_run:
            raise D1ProtocolError("7G5D1 preflight may not record formal D1 administration")
        if self.results:
            raise D1ProtocolError("7G5D1 preflight may not record native comparison results")

    def write_json(self, path: str | Path) -> None:
        destination = Path(path)
        if destination.exists():
            raise D1ProtocolError("D1 preflight report destination must be new")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(asdict(self), sort_keys=True, indent=2) + "\n", encoding="utf-8")
