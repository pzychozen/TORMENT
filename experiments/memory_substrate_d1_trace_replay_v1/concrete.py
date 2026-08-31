"""Concrete, legacy-only fixture evidence sealed for later D1 administration."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .fixture_qualification import D1ReplayProfile, FrozenFixtureSet, FrozenReplayPlan
from .legacy_capture import InitialPostWritePlaceholderPosture
from .manifest import CORE_CHARACTER_FREE_BASELINE_PROFILE, LegacyBaselineFingerprint
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
    profile: D1ReplayProfile
    workspace_id: str
    agent_id: str
    domain_id: str
    side_store_observation_digest: str
    character_subarm_status: str
    character_arm_administered: bool
    native_formal_event_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.expected_repository_head, str) or len(self.expected_repository_head) != 40:
            raise D1ProtocolError("concrete D1 fixture requires the exact repository HEAD")
        if not isinstance(self.profile, D1ReplayProfile):
            raise D1ProtocolError("concrete D1 fixture must name an explicit replay profile")
        if self.fixture_set.profile is not self.profile or self.replay_plan.profile is not self.profile:
            raise D1ProtocolError("concrete D1 fixture profile must match its fixture set and replay plan")
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
        if (
            (self.workspace_id, self.agent_id) != (self.baseline.workspace_id, self.baseline.agent_id)
            or self.domain_id != "research"
        ):
            raise D1ProtocolError("D1 concrete fixture workspace identity is not bound to its L0")
        if not isinstance(self.side_store_observation_digest, str) or len(self.side_store_observation_digest) != 64:
            raise D1ProtocolError("concrete D1 fixture requires the immutable side-store observation digest")
        if self.profile is D1ReplayProfile.CORE_ONLY:
            if self.baseline.baseline_profile != CORE_CHARACTER_FREE_BASELINE_PROFILE:
                raise D1ProtocolError("CORE_ONLY concrete fixture requires the Character-free L0 profile")
            if self.character_arm_administered or self.character_subarm_status != "DEFERRED_PENDING_PROVENANCE_VOCABULARY":
                raise D1ProtocolError("CORE_ONLY concrete fixture must preserve the deferred Character disposition")
        if not isinstance(self.native_formal_event_count, int) or self.native_formal_event_count != 0:
            raise D1ProtocolError("concrete D1 fixture must have no native formal event")
        observed = set(self.observed_store_paths)
        if len(observed) != len(self.observed_store_paths):
            raise D1ProtocolError("concrete D1 observed store inventory must be unique")
        self.store_dispositions.validate_observed(observed)

    def binding_payload(self) -> dict[str, Any]:
        return {
            "schema": "memory-substrate-d1-concrete-fixtures-v2",
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
            "profile": self.profile.value,
            "workspace_id": self.workspace_id,
            "agent_id": self.agent_id,
            "domain_id": self.domain_id,
            "side_store_observation_digest": self.side_store_observation_digest,
            "character_subarm_status": self.character_subarm_status,
            "character_arm_administered": self.character_arm_administered,
            "native_formal_event_count": self.native_formal_event_count,
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
