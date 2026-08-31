"""Concrete, legacy-only fixture evidence sealed for later D1 administration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .fixture_qualification import FrozenFixtureSet, FrozenReplayPlan
from .legacy_capture import InitialPostWritePlaceholderPosture
from .manifest import LegacyBaselineFingerprint
from .protocol import D1ProtocolError, EnvironmentFingerprint, FrozenAdministrationInputs, StoreDispositionManifest, sha256_value
from .run import seal_fixture_set


@dataclass(frozen=True)
class ConcreteFixtureArtifact:
    """All L0-qualified input bytes and evidence; no native result is included."""

    expected_repository_head: str
    baseline: LegacyBaselineFingerprint
    environments: tuple[tuple[str, EnvironmentFingerprint], ...]
    fixture_set: FrozenFixtureSet
    replay_plan: FrozenReplayPlan
    requests: tuple[tuple[str, Mapping[str, Any]], ...]
    store_dispositions: StoreDispositionManifest
    placeholder_posture: InitialPostWritePlaceholderPosture
    workspace_domains: tuple[str, ...]
    observed_store_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.expected_repository_head, str) or len(self.expected_repository_head) != 40:
            raise D1ProtocolError("concrete D1 fixture requires the exact repository HEAD")
        self.fixture_set.validate()
        self.replay_plan.validate(self.fixture_set)
        self.placeholder_posture.validate()
        names = [name for name, _ in self.environments]
        ids = [fixture_id for fixture_id, _ in self.requests]
        if len(names) != len(set(names)) or set(names) != {"legacy", "native"}:
            raise D1ProtocolError("concrete D1 fixture requires one legacy and one native environment fingerprint")
        if len(ids) != len(set(ids)) or set(ids) != {fixture.fixture_id for fixture in self.fixture_set.fixtures}:
            raise D1ProtocolError("concrete D1 fixture request material must bind every fixture exactly once")
        if self.workspace_domains != ("research",):
            raise D1ProtocolError("D1 concrete fixture requires exactly the research workspace domain")
        observed = set(self.observed_store_paths)
        if len(observed) != len(self.observed_store_paths):
            raise D1ProtocolError("concrete D1 observed store inventory must be unique")
        self.store_dispositions.validate_observed(observed)

    def binding_payload(self) -> dict[str, Any]:
        return {
            "schema": "memory-substrate-d1-concrete-fixtures-v1",
            "expected_repository_head": self.expected_repository_head,
            "l0_fingerprint_sha256": self.baseline.digest,
            "l0_fingerprint": asdict(self.baseline),
            "environments": [(name, asdict(value)) for name, value in self.environments],
            "fixture_set": asdict(self.fixture_set),
            "replay_plan": asdict(self.replay_plan),
            "requests": [(fixture_id, dict(value)) for fixture_id, value in self.requests],
            "store_dispositions": asdict(self.store_dispositions),
            "placeholder_posture": asdict(self.placeholder_posture),
            "workspace_domains": self.workspace_domains,
            "observed_store_paths": self.observed_store_paths,
        }

    def seal(self, *, protocol_document: str | Path) -> FrozenAdministrationInputs:
        return seal_fixture_set(
            protocol_document=protocol_document,
            fixtures=self.fixture_set,
            concrete_binding=self.binding_payload(),
        )

    def write_new(self, *, destination: str | Path, inputs: FrozenAdministrationInputs) -> None:
        target = Path(destination)
        if target.exists():
            raise D1ProtocolError("concrete D1 fixture destination must be new")
        expected = sha256_value(self.binding_payload())
        if inputs.fixture_sha256 != expected:
            raise D1ProtocolError("concrete D1 fixture lock does not bind its evidence payload")
        target.parent.mkdir(parents=True, exist_ok=True)
        document = {"binding": self.binding_payload(), "administration_inputs": asdict(inputs)}
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        try:
            descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise D1ProtocolError("concrete D1 fixture destination already exists") from exc
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
