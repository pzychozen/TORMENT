"""Legacy-only fixture-margin qualification and immutable fixture sealing."""
from __future__ import annotations

from collections import Counter
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


class D1ReplayProfile(StrEnum):
    """The explicit D1 administration shape selected before any replay exists."""

    CORE_ONLY = "CORE_ONLY"
    CHARACTER_EXTENDED = "CHARACTER_EXTENDED"


class DuplicateDecisionKind(StrEnum):
    """Frozen legacy-only explanation for a duplicate decision."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    CREATE_NO_CANDIDATE = "CREATE_NO_CANDIDATE"
    REINFORCE_MATCH = "REINFORCE_MATCH"
    CREATE_DISTINCT_BELOW_THRESHOLD = "CREATE_DISTINCT_BELOW_THRESHOLD"
    CREATE_CONTRADICTION_GUARD = "CREATE_CONTRADICTION_GUARD"


class ReplayEventRole(StrEnum):
    CREATE = "CREATE"
    REINFORCE = "REINFORCE"
    DISTINCT = "DISTINCT"
    CONTRADICTION = "CONTRADICTION"
    NO_WRITE = "NO_WRITE"
    CHARACTER_PREPARATION = "CHARACTER_PREPARATION"
    CHARACTER_ADMINISTRATION = "CHARACTER_ADMINISTRATION"


@dataclass(frozen=True)
class FrozenReplayArm:
    """One future replay arm with explicitly separate legacy/native clones."""

    arm_id: str
    legacy_clone_id: str
    native_clone_id: str
    fixture_ids: tuple[str, ...]
    event_roles: tuple[ReplayEventRole, ...]
    character_specific_baseline: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (self.arm_id, self.legacy_clone_id, self.native_clone_id)):
            raise D1ProtocolError("D1 replay arm requires explicit clone identities")
        if not self.fixture_ids or any(not isinstance(value, str) or not value for value in self.fixture_ids):
            raise D1ProtocolError("D1 replay arm requires one or more frozen fixture IDs")
        if len(self.fixture_ids) != len(self.event_roles) or any(not isinstance(role, ReplayEventRole) for role in self.event_roles):
            raise D1ProtocolError("D1 replay arm requires one frozen role per fixture ID")


@dataclass(frozen=True)
class FrozenReplayPlan:
    """Prevents the future administrator from merging independent D1 arms."""

    micro_arms: tuple[FrozenReplayArm, ...]
    sequential_arm: FrozenReplayArm
    character_arm: FrozenReplayArm | None = None
    profile: D1ReplayProfile = D1ReplayProfile.CHARACTER_EXTENDED

    def validate(self, fixture_set: "FrozenFixtureSet") -> None:
        if not isinstance(self.profile, D1ReplayProfile) or self.profile is not fixture_set.profile:
            raise D1ProtocolError("D1 replay plan and fixture set must name the same explicit profile")
        if self.profile is D1ReplayProfile.CORE_ONLY:
            if self.character_arm is not None:
                raise D1ProtocolError("CORE_ONLY D1 replay explicitly forbids a Character arm")
            all_arms = (*self.micro_arms, self.sequential_arm)
        else:
            if self.character_arm is None or self.character_arm.arm_id != "CHARACTER_SUBARM":
                raise D1ProtocolError("CHARACTER_EXTENDED D1 replay requires the Character arm")
            if not self.character_arm.character_specific_baseline:
                raise D1ProtocolError("D1 Character sub-arm requires an explicit Character baseline")
            all_arms = (*self.micro_arms, self.sequential_arm, self.character_arm)
        expected = {
            "M1_CREATE", "M2_REINFORCE", "M3_DISTINCT", "M4_CONTRADICTION", "M5_NO_WRITE",
        }
        if {arm.arm_id for arm in self.micro_arms} != expected or len(self.micro_arms) != 5:
            raise D1ProtocolError("D1 needs five separately cloned micro-trace arms")
        if self.sequential_arm.arm_id != "SEQUENTIAL":
            raise D1ProtocolError("D1 requires the named sequential arm")
        legacy_clones = [arm.legacy_clone_id for arm in all_arms]
        native_clones = [arm.native_clone_id for arm in all_arms]
        if len(legacy_clones) != len(set(legacy_clones)):
            raise D1ProtocolError("D1 replay arms may not reuse a legacy clone")
        if len(native_clones) != len(set(native_clones)):
            raise D1ProtocolError("D1 replay arms may not reuse a native clone")
        known_ids = [fixture.fixture_id for fixture in fixture_set.fixtures]
        used_ids = [fixture_id for arm in all_arms for fixture_id in arm.fixture_ids]
        if Counter(used_ids) != Counter(known_ids):
            raise D1ProtocolError("D1 replay plan must assign every frozen fixture ID exactly once")
        fixtures_by_id = {fixture.fixture_id: fixture for fixture in fixture_set.fixtures}
        expected_kinds = {
            "M1_CREATE": FixtureKind.M1_CREATE,
            "M2_REINFORCE": FixtureKind.M2_REINFORCE,
            "M3_DISTINCT": FixtureKind.M3_DISTINCT,
            "M4_CONTRADICTION": FixtureKind.M4_CONTRADICTION,
            "M5_NO_WRITE": FixtureKind.M5_NO_WRITE,
            "SEQUENTIAL": FixtureKind.SEQUENTIAL,
        }
        if self.profile is D1ReplayProfile.CHARACTER_EXTENDED:
            expected_kinds["CHARACTER_SUBARM"] = FixtureKind.CHARACTER_SUBARM
        for arm in all_arms:
            if any(fixtures_by_id[fixture_id].kind is not expected_kinds[arm.arm_id] for fixture_id in arm.fixture_ids):
                raise D1ProtocolError("D1 replay arm contains a fixture from another declared arm")
        exact_micro_shapes = {
            "M1_CREATE": (ReplayEventRole.CREATE,),
            "M2_REINFORCE": (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE),
            "M3_DISTINCT": (ReplayEventRole.CREATE, ReplayEventRole.DISTINCT),
            "M4_CONTRADICTION": (ReplayEventRole.CREATE, ReplayEventRole.CONTRADICTION),
            "M5_NO_WRITE": (ReplayEventRole.NO_WRITE,),
        }
        for arm in self.micro_arms:
            if arm.event_roles != exact_micro_shapes[arm.arm_id]:
                raise D1ProtocolError(f"D1 {arm.arm_id} event roles are not frozen in the required order")
        required_sequential = (
            ReplayEventRole.CREATE, ReplayEventRole.REINFORCE,
            ReplayEventRole.DISTINCT, ReplayEventRole.CONTRADICTION,
        )
        positions = [self.sequential_arm.event_roles.index(role) if role in self.sequential_arm.event_roles else -1 for role in required_sequential]
        if positions != sorted(positions) or any(position < 0 for position in positions):
            raise D1ProtocolError("D1 sequential arm lacks CREATE/REINFORCE/DISTINCT/CONTRADICTION order")
        if self.profile is D1ReplayProfile.CHARACTER_EXTENDED:
            assert self.character_arm is not None
            if (
                self.character_arm.event_roles.count(ReplayEventRole.CHARACTER_ADMINISTRATION) != 1
                or self.character_arm.event_roles[-1] is not ReplayEventRole.CHARACTER_ADMINISTRATION
                or ReplayEventRole.CHARACTER_PREPARATION not in self.character_arm.event_roles
            ):
                raise D1ProtocolError("D1 Character arm needs preparation events then one final administration event")


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
        if self.recent_non_seed_memory_count < 0:
            raise D1ProtocolError("Character sub-arm recent-memory count is invalid")
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
    duplicate_decision: DuplicateDecisionKind
    raw_similarity: float | None
    reinforce_threshold: float | None
    attach_score: float
    effective_attach_threshold: float
    expected_reinforced: bool | None
    contradiction_guard_observed: bool | None = None

    def validate(self) -> None:
        if abs(self.attach_score - self.effective_attach_threshold) < 0.02:
            raise D1ProtocolError("D1 fixture is too near its motif attach threshold")
        kind = self.duplicate_decision
        if kind is DuplicateDecisionKind.NOT_APPLICABLE:
            if any(value is not None for value in (self.raw_similarity, self.reinforce_threshold, self.expected_reinforced, self.contradiction_guard_observed)):
                raise D1ProtocolError("not-applicable duplicate decision may not claim threshold facts")
            return
        if kind is DuplicateDecisionKind.CREATE_NO_CANDIDATE:
            if self.expected_reinforced is not False or any(value is not None for value in (self.raw_similarity, self.reinforce_threshold, self.contradiction_guard_observed)):
                raise D1ProtocolError("no-candidate creation may not pretend a threshold decision occurred")
            return
        if self.raw_similarity is None or self.reinforce_threshold is None or self.expected_reinforced is None:
            raise D1ProtocolError("duplicate-decision fixture lacks raw similarity evidence")
        if kind is DuplicateDecisionKind.REINFORCE_MATCH:
            if self.expected_reinforced is not True or self.raw_similarity < self.reinforce_threshold + 0.02:
                raise D1ProtocolError("reinforcement fixture is too near TORMENT_REINFORCE_SIM_THRESHOLD")
            if self.contradiction_guard_observed is not False:
                raise D1ProtocolError("reinforcement match must freeze a false contradiction guard")
            return
        if kind is DuplicateDecisionKind.CREATE_DISTINCT_BELOW_THRESHOLD:
            if self.expected_reinforced is not False or self.raw_similarity > self.reinforce_threshold - 0.02:
                raise D1ProtocolError("distinct fixture is too near TORMENT_REINFORCE_SIM_THRESHOLD")
            if self.contradiction_guard_observed not in (False, None):
                raise D1ProtocolError("low-similarity distinct fixture may not claim contradiction prevention")
            return
        if kind is DuplicateDecisionKind.CREATE_CONTRADICTION_GUARD:
            if self.expected_reinforced is not False or self.raw_similarity < self.reinforce_threshold + 0.02:
                raise D1ProtocolError("contradiction fixture must have a high-similarity duplicate candidate")
            if self.contradiction_guard_observed is not True:
                raise D1ProtocolError("contradiction fixture must freeze a true contradiction guard")
            return
        raise D1ProtocolError("unrecognized duplicate-decision qualification")


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
    profile: D1ReplayProfile = D1ReplayProfile.CHARACTER_EXTENDED

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_sha256, str) or len(self.protocol_sha256) != 64:
            raise D1ProtocolError("fixture set must bind the frozen protocol bytes")
        ids = [item.fixture_id for item in self.fixtures]
        if len(ids) != len(set(ids)):
            raise D1ProtocolError("fixture IDs must be unique")

    def validate(self) -> None:
        if not isinstance(self.profile, D1ReplayProfile):
            raise D1ProtocolError("D1 fixture set must name an explicit replay profile")
        for fixture in self.fixtures:
            fixture.validate()
        expected = {
            FixtureKind.M1_CREATE, FixtureKind.M2_REINFORCE, FixtureKind.M3_DISTINCT,
            FixtureKind.M4_CONTRADICTION, FixtureKind.M5_NO_WRITE, FixtureKind.SEQUENTIAL,
        }
        if self.profile is D1ReplayProfile.CHARACTER_EXTENDED:
            expected.add(FixtureKind.CHARACTER_SUBARM)
        present = {fixture.kind for fixture in self.fixtures}
        if present != expected:
            raise D1ProtocolError("D1 fixture set does not match its explicit replay profile")

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
