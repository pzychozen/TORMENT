"""Legacy-only fixture-margin qualification and immutable fixture sealing."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Mapping

from .protocol import D1ProtocolError, FROZEN_TOLERANCES, FrozenAdministrationInputs, sha256_value


class FixtureKind(StrEnum):
    M1_CREATE = "M1_CREATE"
    M2_REINFORCE = "M2_REINFORCE"
    M3_DISTINCT = "M3_DISTINCT"
    M4_CONTRADICTION = "M4_CONTRADICTION"
    M5_NO_WRITE = "M5_NO_WRITE"
    SEQUENTIAL = "SEQUENTIAL"
    CHARACTER_SUBARM = "CHARACTER_SUBARM"


@dataclass(frozen=True)
class FrozenReplayArm:
    """One future replay arm with explicitly separate legacy/native clones."""

    arm_id: str
    legacy_clone_id: str
    native_clone_id: str
    fixture_ids: tuple[str, ...]
    character_specific_baseline: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (self.arm_id, self.legacy_clone_id, self.native_clone_id)):
            raise D1ProtocolError("D1 replay arm requires explicit clone identities")
        if not self.fixture_ids or any(not isinstance(value, str) or not value for value in self.fixture_ids):
            raise D1ProtocolError("D1 replay arm requires one or more frozen fixture IDs")


@dataclass(frozen=True)
class FrozenReplayPlan:
    """Prevents the future administrator from merging independent D1 arms."""

    micro_arms: tuple[FrozenReplayArm, ...]
    sequential_arm: FrozenReplayArm
    character_arm: FrozenReplayArm

    def validate(self, fixture_set: "FrozenFixtureSet") -> None:
        expected = {
            "M1_CREATE", "M2_REINFORCE", "M3_DISTINCT", "M4_CONTRADICTION", "M5_NO_WRITE",
        }
        if {arm.arm_id for arm in self.micro_arms} != expected or len(self.micro_arms) != 5:
            raise D1ProtocolError("D1 needs five separately cloned micro-trace arms")
        all_arms = (*self.micro_arms, self.sequential_arm, self.character_arm)
        clone_pairs = [(arm.legacy_clone_id, arm.native_clone_id) for arm in all_arms]
        if len(clone_pairs) != len(set(clone_pairs)):
            raise D1ProtocolError("D1 replay arms may not share a legacy/native clone pair")
        if self.sequential_arm.arm_id != "SEQUENTIAL" or self.character_arm.arm_id != "CHARACTER_SUBARM":
            raise D1ProtocolError("D1 requires named sequential and Character arms")
        if not self.character_arm.character_specific_baseline:
            raise D1ProtocolError("D1 Character sub-arm requires an explicit Character baseline")
        known_ids = {fixture.fixture_id for fixture in fixture_set.fixtures}
        used_ids = {fixture_id for arm in all_arms for fixture_id in arm.fixture_ids}
        if used_ids != known_ids:
            raise D1ProtocolError("D1 replay plan must account for every frozen fixture exactly by ID")
        m2 = next(arm for arm in self.micro_arms if arm.arm_id == "M2_REINFORCE")
        if len(m2.fixture_ids) != 2:
            raise D1ProtocolError("M2 must preserve its create then duplicate opportunity")
        m5 = next(arm for arm in self.micro_arms if arm.arm_id == "M5_NO_WRITE")
        if len(m5.fixture_ids) != 1:
            raise D1ProtocolError("M5 must be one no-write event")


@dataclass(frozen=True)
class CharacterSubarmQualification:
    """Legacy-only proof that the separate C1A/C1B arm is meaningful."""

    recent_non_seed_memory_count: int
    logical_step: int
    character_enabled: bool
    expected_stored: bool
    split_edge: bool
    checkpoint_edge: bool
    correction_embedding_bytes_stable_across_environments: bool

    def validate(self) -> None:
        if self.recent_non_seed_memory_count < 1:
            raise D1ProtocolError("Character sub-arm lacks recent non-seed memory evidence")
        if self.logical_step != 25 or not self.character_enabled or not self.expected_stored:
            raise D1ProtocolError("Character sub-arm requires an enabled hard-stored logical step 25 request")
        if self.split_edge or self.checkpoint_edge:
            raise D1ProtocolError("Character sub-arm may not overlap split or checkpoint edges")
        if not self.correction_embedding_bytes_stable_across_environments:
            raise D1ProtocolError("Character correction embeddings are not byte-stable across required environments")


@dataclass(frozen=True)
class WriteGateEvidence:
    write_intent: bool
    strength: float
    effective_write_threshold: float
    write_band: float

    def validate(self, *, expected_stored: bool) -> None:
        if self.write_intent and self.strength >= self.effective_write_threshold + 0.02:
            observed_stored = True
        elif (not self.write_intent) or self.strength <= self.effective_write_threshold - self.write_band - 0.02:
            observed_stored = False
        else:
            raise D1ProtocolError("D1 fixture is inside the probabilistic soft write band")
        if observed_stored is not expected_stored:
            raise D1ProtocolError("fixture write-gate evidence disagrees with its frozen expected path")


@dataclass(frozen=True)
class StorageDecisionEvidence:
    raw_similarity: float | None
    reinforce_threshold: float | None
    attach_score: float
    effective_attach_threshold: float
    expected_reinforced: bool | None

    def validate(self) -> None:
        if abs(self.attach_score - self.effective_attach_threshold) < 0.02:
            raise D1ProtocolError("D1 fixture is too near its motif attach threshold")
        if self.expected_reinforced is None:
            return
        if self.raw_similarity is None or self.reinforce_threshold is None:
            raise D1ProtocolError("reinforcement fixture lacks raw similarity evidence")
        if self.expected_reinforced:
            if self.raw_similarity < self.reinforce_threshold + 0.02:
                raise D1ProtocolError("reinforcement fixture is too near TORMENT_REINFORCE_SIM_THRESHOLD")
        elif self.raw_similarity > self.reinforce_threshold - 0.02:
            raise D1ProtocolError("distinct fixture is too near TORMENT_REINFORCE_SIM_THRESHOLD")


@dataclass(frozen=True)
class FrozenFixtureEvidence:
    fixture_id: str
    kind: FixtureKind
    request_sha256: str
    expected_stored: bool
    write_gate: WriteGateEvidence
    decision: StorageDecisionEvidence | None
    links: tuple[str, ...]
    pre_event_motif_member_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.fixture_id, str) or not self.fixture_id:
            raise D1ProtocolError("fixture ID is required")
        if not isinstance(self.request_sha256, str) or len(self.request_sha256) != 64:
            raise D1ProtocolError("fixture must bind one frozen request SHA256")
        if self.links:
            raise D1ProtocolError("D1 fixtures may not carry deferred links")
        if not isinstance(self.pre_event_motif_member_count, int) or self.pre_event_motif_member_count < 0:
            raise D1ProtocolError("fixture motif count is invalid")

    def validate(self) -> None:
        self.write_gate.validate(expected_stored=self.expected_stored)
        if self.pre_event_motif_member_count >= 80:
            raise D1ProtocolError("D1 fixture is not dramatically below the C2A split boundary")
        if self.decision is not None:
            self.decision.validate()


@dataclass(frozen=True)
class FrozenFixtureSet:
    protocol_sha256: str
    fixtures: tuple[FrozenFixtureEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_sha256, str) or len(self.protocol_sha256) != 64:
            raise D1ProtocolError("fixture set must bind the frozen protocol bytes")
        ids = [item.fixture_id for item in self.fixtures]
        if len(ids) != len(set(ids)):
            raise D1ProtocolError("fixture IDs must be unique")

    def validate(self) -> None:
        for fixture in self.fixtures:
            fixture.validate()
        expected = {FixtureKind.M1_CREATE, FixtureKind.M2_REINFORCE, FixtureKind.M3_DISTINCT, FixtureKind.M4_CONTRADICTION, FixtureKind.M5_NO_WRITE, FixtureKind.SEQUENTIAL, FixtureKind.CHARACTER_SUBARM}
        present = {fixture.kind for fixture in self.fixtures}
        if present != expected:
            raise D1ProtocolError("D1 fixture set is missing a required frozen arm")

    @property
    def digest(self) -> str:
        return sha256_value({"protocol_sha256": self.protocol_sha256, "fixtures": [asdict(item) for item in self.fixtures]})

    def freeze_inputs(self) -> FrozenAdministrationInputs:
        self.validate()
        return FrozenAdministrationInputs(
            protocol_sha256=self.protocol_sha256,
            fixture_sha256=self.digest,
            tolerances_sha256=FROZEN_TOLERANCES.digest,
        )


def load_fixture_recipes(value: Mapping[str, Any]) -> tuple[FixtureKind, ...]:
    """Validate the checked-in recipe vocabulary without pretending it is an L0 run."""
    kinds = value.get("fixture_kinds")
    if not isinstance(kinds, list):
        raise D1ProtocolError("fixture recipe file must declare fixture_kinds")
    parsed = tuple(FixtureKind(item) for item in kinds)
    if len(parsed) != len(set(parsed)):
        raise D1ProtocolError("fixture recipes contain duplicate kinds")
    return parsed
