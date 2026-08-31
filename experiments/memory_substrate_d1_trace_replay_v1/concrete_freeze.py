"""Translate one immutable legacy-only HTTP capture into concrete D1 inputs."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .concrete import ConcreteFixtureArtifact
from .fixture_qualification import (
    D1ReplayProfile,
    DuplicateDecisionKind,
    FixtureKind,
    FrozenFixtureEvidence,
    FrozenFixtureSet,
    FrozenReplayArm,
    FrozenReplayPlan,
    ReplayEventRole,
    StorageDecisionEvidence,
    WriteGateEvidence,
)
from .legacy_capture import InitialPostWritePlaceholderPosture
from .manifest import (
    CORE_CHARACTER_FREE_BASELINE_PROFILE,
    fingerprint_legacy_baseline,
    verify_legacy_baseline,
)
from .protocol import (
    D1ProtocolError,
    EnvironmentFingerprint,
    StoreDisposition,
    StoreDispositionManifest,
    StoreDispositionRule,
    StorePresence,
    protocol_document_sha256,
    sha256_value,
)
from .side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
    verify_frozen_d1_core_retained_side_stores,
)


def _load(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise D1ProtocolError(f"D1 evidence file is missing: {source}")
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise D1ProtocolError("D1 evidence document must be an object")
    return value


def _environment(path: str | Path) -> EnvironmentFingerprint:
    value = _load(path)
    if value.get("schema") != "memory-substrate-d1-environment-v1" or not isinstance(value.get("fingerprint"), dict):
        raise D1ProtocolError("D1 environment evidence has an unrecognized schema")
    source = dict(value["fingerprint"])
    source["runtime_flags"] = tuple(tuple(item) for item in source.get("runtime_flags", ()))
    return EnvironmentFingerprint(**source)


def _store_manifest(paths: tuple[str, ...], *, workspace_id: str) -> StoreDispositionManifest:
    rules: list[StoreDispositionRule] = []
    for path in paths:
        if "/index/" in path:
            disposition = StoreDisposition.ACCELERATION_EXCLUDED
        elif "/trajectories/" in path:
            disposition = StoreDisposition.PROCESS_LOCAL
        elif path.endswith(("memory_events.jsonl", "motif_events.jsonl")):
            disposition = StoreDisposition.OUT_OF_PROFILE
        else:
            disposition = StoreDisposition.IN_SCOPE_EXACT
        rules.append(StoreDispositionRule(path, disposition, StorePresence.REQUIRED_PRESENT))
    # Deliberately exact rather than wildcarded: this named optional legacy
    # operational store may appear, but a different unknown path cannot.
    optional = f"workspaces/{workspace_id}/domains/research/motif_merge_suggestions.jsonl"
    rules.append(StoreDispositionRule(optional, StoreDisposition.OUT_OF_PROFILE, StorePresence.OPTIONAL_PRESENT))
    return StoreDispositionManifest(tuple(rules))


def _fixture(event: dict[str, Any], protocol_sha256: str) -> FrozenFixtureEvidence:
    qualification = dict(event["qualification"])
    duplicate = DuplicateDecisionKind(qualification["duplicate_decision"])
    decision = None
    if duplicate is not DuplicateDecisionKind.NOT_APPLICABLE:
        motif = dict(qualification["motif"])
        decision = StorageDecisionEvidence(
            duplicate, qualification.get("raw_similarity"), qualification.get("reinforce_threshold"),
            float(motif["attach_score"]), float(motif["effective_attach_threshold"]),
            qualification.get("expected_reinforced"), qualification.get("contradiction_guard_observed"),
        )
    write = dict(qualification["write_gate"])
    motif = dict(qualification["motif"])
    return FrozenFixtureEvidence(
        fixture_id=str(event["fixture_id"]), kind=FixtureKind(event["kind"]),
        request_sha256=str(event["request_sha256"]), expected_stored=bool(event["legacy_response"].get("stored")),
        write_gate=WriteGateEvidence(
            bool(write["write_intent"]), float(write["strength"]),
            float(write["effective_write_threshold"]), float(write["write_band"]),
        ),
        decision=decision, links=tuple(qualification.get("links", ())),
        pre_event_motif_member_count=int(motif["pre_event_motif_member_count"]),
    )


def _replay_plan(
    events: dict[str, list[dict[str, Any]]], *, profile: D1ReplayProfile,
) -> FrozenReplayPlan:
    def arm(arm_id: str, roles: tuple[ReplayEventRole, ...], *, character: bool = False) -> FrozenReplayArm:
        values = events[arm_id]
        return FrozenReplayArm(
            arm_id, f"L0-{arm_id}", f"N0-{arm_id}",
            tuple(str(value["fixture_id"]) for value in values), roles, character,
        )
    character_arm = None
    if profile is D1ReplayProfile.CHARACTER_EXTENDED:
        character_arm = arm(
            "CHARACTER_SUBARM",
            (
                ReplayEventRole.CHARACTER_PREPARATION, ReplayEventRole.CHARACTER_PREPARATION,
                ReplayEventRole.CHARACTER_PREPARATION, ReplayEventRole.CHARACTER_ADMINISTRATION,
            ),
            character=True,
        )
    return FrozenReplayPlan(
        micro_arms=(
            arm("M1_CREATE", (ReplayEventRole.CREATE,)),
            arm("M2_REINFORCE", (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE)),
            arm("M3_DISTINCT", (ReplayEventRole.CREATE, ReplayEventRole.DISTINCT)),
            arm("M4_CONTRADICTION", (ReplayEventRole.CREATE, ReplayEventRole.CONTRADICTION)),
            arm("M5_NO_WRITE", (ReplayEventRole.NO_WRITE,)),
        ),
        sequential_arm=arm("SEQUENTIAL", (ReplayEventRole.CREATE, ReplayEventRole.REINFORCE, ReplayEventRole.DISTINCT, ReplayEventRole.CONTRADICTION)),
        character_arm=character_arm,
        profile=profile,
    )


def freeze_concrete_legacy_only_fixture(
    *, capture_document: str | Path, legacy_environment_document: str | Path,
    native_environment_document: str | Path, protocol_document: str | Path,
    destination: str | Path, expected_repository_head: str,
) -> tuple[ConcreteFixtureArtifact, Any]:
    """Create a new committed concrete-input artifact without starting replay."""
    capture = _load(capture_document)
    if capture.get("schema") != "memory-substrate-d1-legacy-only-http-capture-v1":
        raise D1ProtocolError("concrete D1 freeze requires a legacy-only HTTP capture")
    if capture.get("native_outcomes_inspected") is not False or capture.get("native_formal_event_count") != 0:
        raise D1ProtocolError("concrete D1 freeze refuses any capture with native formal evidence")
    workspace_id = str(capture["workspace_id"])
    agent_id = str(capture["agent_id"])
    baseline = fingerprint_legacy_baseline(root=str(capture["l0_root"]), workspace_id=workspace_id, agent_id=agent_id)
    verify_legacy_baseline(baseline)
    if baseline.digest != capture.get("l0_fingerprint_sha256"):
        raise D1ProtocolError("concrete D1 freeze L0 fingerprint does not match the real baseline")
    protocol_sha256 = protocol_document_sha256(protocol_document)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in capture.get("captures", []):
        if not isinstance(event, dict):
            raise D1ProtocolError("concrete D1 capture event is malformed")
        grouped.setdefault(str(event["arm_id"]), []).append(event)
    required = {"M1_CREATE", "M2_REINFORCE", "M3_DISTINCT", "M4_CONTRADICTION", "M5_NO_WRITE", "SEQUENTIAL", "CHARACTER_SUBARM"}
    if set(grouped) != required:
        raise D1ProtocolError("concrete D1 capture lacks the exact required arm inventory")
    ordered = [event for arm in ("M1_CREATE", "M2_REINFORCE", "M3_DISTINCT", "M4_CONTRADICTION", "M5_NO_WRITE", "SEQUENTIAL", "CHARACTER_SUBARM") for event in grouped[arm]]
    fixtures = FrozenFixtureSet(
        protocol_sha256, tuple(_fixture(event, protocol_sha256) for event in ordered),
        D1ReplayProfile.CHARACTER_EXTENDED,
    )
    plan = _replay_plan(grouped, profile=D1ReplayProfile.CHARACTER_EXTENDED)
    paths = tuple(item.relative_path for item in baseline.files)
    posture = InitialPostWritePlaceholderPosture(False, "read_only")
    artifact = ConcreteFixtureArtifact(
        expected_repository_head=expected_repository_head,
        baseline=baseline,
        environments=(("legacy", _environment(legacy_environment_document)), ("native", _environment(native_environment_document))),
        fixture_set=fixtures, replay_plan=plan,
        requests=tuple((str(event["fixture_id"]), {
            "request": event["request"], "storage_facts": event["storage_facts"],
            "legacy_only_observed_outcome": {
                "stored": event["legacy_response"].get("stored"), "reinforced": event["legacy_response"].get("reinforced"),
                "eid": event["legacy_response"].get("eid"), "motifs": event["legacy_response"].get("motifs"),
            },
            "qualification": event["qualification"],
            **({"character_legacy_observation": {"state_after": event.get("character_state_after"), "memory_count_after": event.get("character_memory_count_after")}} if event["fixture_id"] == "C-admin-25" else {}),
        }) for event in ordered),
        store_dispositions=_store_manifest(paths, workspace_id=workspace_id), placeholder_posture=posture,
        workspace_domains=tuple(capture.get("workspace_domains", ())), observed_store_paths=paths,
        profile=D1ReplayProfile.CHARACTER_EXTENDED,
        workspace_id=workspace_id, agent_id=agent_id, domain_id="research",
        side_store_observation_digest=sha256_value({"unbound_character_capture_l0": baseline.digest}),
        character_subarm_status="LEGACY_ONLY_QUALIFIED_NOT_ADMINISTERED",
        character_arm_administered=False, native_formal_event_count=0,
    )
    inputs = artifact.seal(protocol_document=protocol_document)
    artifact.write_new(destination=destination, inputs=inputs)
    return artifact, inputs


def _require_exact_core_baseline(*, root: str | Path, workspace_id: str, agent_id: str):
    """Read the selected core L0 only in explicit Character-free mode."""
    baseline = fingerprint_legacy_baseline(
        root=root,
        workspace_id=workspace_id,
        agent_id=agent_id,
        domain_id="research",
        character_seed_required=False,
    )
    verify_legacy_baseline(baseline)
    if baseline.baseline_profile != CORE_CHARACTER_FREE_BASELINE_PROFILE:
        raise D1ProtocolError("CORE_ONLY concrete freeze requires the Character-free baseline profile")
    if baseline.character_seed is not None or baseline.character_state is not None:
        raise D1ProtocolError("CORE_ONLY concrete freeze found Character baseline artifacts")
    if baseline.digest != CORE_CHARACTER_FREE_L0_FINGERPRINT:
        raise D1ProtocolError("CORE_ONLY concrete freeze core L0 fingerprint differs from the qualified L0")
    nodes = Path(root).resolve() / "workspaces" / workspace_id / "agents" / agent_id / "private" / "nodes.jsonl"
    rows = [line for line in nodes.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise D1ProtocolError("CORE_ONLY concrete freeze requires exactly one ordinary baseline memory")
    return baseline


def freeze_concrete_core_only_fixture(
    *, capture_document: str | Path, legacy_environment_document: str | Path,
    native_environment_document: str | Path, protocol_document: str | Path,
    destination: str | Path, expected_repository_head: str,
) -> tuple[ConcreteFixtureArtifact, Any]:
    """Seal the selected core-only fixture bytes; it never starts native replay."""
    capture = _load(capture_document)
    if (
        capture.get("schema") != "memory-substrate-d1-legacy-only-http-capture-v1"
        or capture.get("profile") != D1ReplayProfile.CORE_ONLY.value
    ):
        raise D1ProtocolError("CORE_ONLY concrete freeze requires a CORE_ONLY legacy HTTP capture")
    if capture.get("native_outcomes_inspected") is not False or capture.get("native_formal_event_count") != 0:
        raise D1ProtocolError("CORE_ONLY concrete freeze refuses native formal evidence")
    workspace_id = str(capture["workspace_id"])
    agent_id = str(capture["agent_id"])
    baseline = _require_exact_core_baseline(
        root=str(capture["l0_root"]), workspace_id=workspace_id, agent_id=agent_id,
    )
    if baseline.digest != capture.get("l0_fingerprint_sha256"):
        raise D1ProtocolError("CORE_ONLY capture L0 fingerprint does not match the immutable core L0")
    observation = verify_frozen_d1_core_retained_side_stores(
        root=baseline.root, workspace_id=workspace_id, agent_id=agent_id, domain_id="research",
    )
    if observation.digest != CORE_SIDE_STORE_OBSERVATION_DIGEST:
        raise D1ProtocolError("CORE_ONLY concrete freeze side-store witness differs from the qualified evidence")
    protocol_sha256 = protocol_document_sha256(protocol_document)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in capture.get("captures", []):
        if not isinstance(event, dict):
            raise D1ProtocolError("CORE_ONLY capture event is malformed")
        grouped.setdefault(str(event["arm_id"]), []).append(event)
    order = ("M1_CREATE", "M2_REINFORCE", "M3_DISTINCT", "M4_CONTRADICTION", "M5_NO_WRITE", "SEQUENTIAL")
    if set(grouped) != set(order):
        raise D1ProtocolError("CORE_ONLY capture must contain exactly the six core replay arms")
    ordered = [event for arm in order for event in grouped[arm]]
    if any(event.get("kind") == FixtureKind.CHARACTER_SUBARM.value for event in ordered):
        raise D1ProtocolError("CORE_ONLY capture may not carry a Character fixture")
    fixtures = FrozenFixtureSet(
        protocol_sha256,
        tuple(_fixture(event, protocol_sha256) for event in ordered),
        D1ReplayProfile.CORE_ONLY,
    )
    plan = _replay_plan(grouped, profile=D1ReplayProfile.CORE_ONLY)
    paths = tuple(item.relative_path for item in baseline.files)
    artifact = ConcreteFixtureArtifact(
        expected_repository_head=expected_repository_head,
        baseline=baseline,
        environments=(
            ("legacy", _environment(legacy_environment_document)),
            ("native", _environment(native_environment_document)),
        ),
        fixture_set=fixtures,
        replay_plan=plan,
        requests=tuple((str(event["fixture_id"]), {
            "request": event["request"],
            "storage_facts": event["storage_facts"],
            "legacy_only_observed_outcome": {
                "stored": event["legacy_response"].get("stored"),
                "reinforced": event["legacy_response"].get("reinforced"),
                "eid": event["legacy_response"].get("eid"),
                "motifs": event["legacy_response"].get("motifs"),
            },
            "qualification": event["qualification"],
        }) for event in ordered),
        store_dispositions=_store_manifest(paths, workspace_id=workspace_id),
        placeholder_posture=InitialPostWritePlaceholderPosture(False, "read_only"),
        workspace_domains=("research",), observed_store_paths=paths,
        profile=D1ReplayProfile.CORE_ONLY,
        workspace_id=workspace_id, agent_id=agent_id, domain_id="research",
        side_store_observation_digest=observation.digest,
        character_subarm_status="DEFERRED_PENDING_PROVENANCE_VOCABULARY",
        character_arm_administered=False,
        native_formal_event_count=0,
    )
    inputs = artifact.seal(protocol_document=protocol_document)
    artifact.write_new(destination=destination, inputs=inputs)
    return artifact, inputs


__all__ = ["freeze_concrete_core_only_fixture", "freeze_concrete_legacy_only_fixture"]
