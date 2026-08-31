"""Focused guards for the 7G5D1F core-only concrete fixture lock."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.memory_substrate_d1_trace_replay_v1 import concrete_freeze
from experiments.memory_substrate_d1_trace_replay_v1.fixture_qualification import (
    D1ReplayProfile,
    FrozenFixtureSet,
    FrozenReplayArm,
    FrozenReplayPlan,
    ReplayEventRole,
)
from experiments.memory_substrate_d1_trace_replay_v1.formal import FormalAdministrationRunner
from experiments.memory_substrate_d1_trace_replay_v1.manifest import CORE_CHARACTER_FREE_BASELINE_PROFILE
from experiments.memory_substrate_d1_trace_replay_v1.protocol import D1ProtocolError, FrozenAdministrationInputs
from experiments.memory_substrate_d1_trace_replay_v1.side_store_observation import (
    CORE_CHARACTER_FREE_L0_FINGERPRINT,
    CORE_SIDE_STORE_OBSERVATION_DIGEST,
)


_ROOT = Path(__file__).resolve().parents[1]
_FIXTURES = _ROOT / "experiments" / "memory_substrate_d1_trace_replay_v1" / "fixtures"
_OLD = _FIXTURES / "concrete_legacy_only_fixture_set_20260831.json"
_CORE = _FIXTURES / "concrete_core_legacy_only_fixture_set_20260831.json"
_OLD_SHA256 = "ff86d62cdfa153c3c2a4833197c7ba17b881b1ffa5e2f798a03459856117f72a"


def _arm(arm_id: str) -> FrozenReplayArm:
    return FrozenReplayArm(arm_id, f"legacy-{arm_id}", f"native-{arm_id}", ("fixture",), (ReplayEventRole.CREATE,))


def test_core_only_rejects_character_arm_and_character_extended_requires_one() -> None:
    core_set = FrozenFixtureSet("a" * 64, (), D1ReplayProfile.CORE_ONLY)
    character = FrozenReplayArm(
        "CHARACTER_SUBARM", "legacy-character", "native-character", ("character-prep", "character-admin"),
        (ReplayEventRole.CHARACTER_PREPARATION, ReplayEventRole.CHARACTER_ADMINISTRATION), True,
    )
    with pytest.raises(D1ProtocolError, match="forbids a Character"):
        FrozenReplayPlan((), _arm("SEQUENTIAL"), character, D1ReplayProfile.CORE_ONLY).validate(core_set)
    extended_set = FrozenFixtureSet("a" * 64, (), D1ReplayProfile.CHARACTER_EXTENDED)
    with pytest.raises(D1ProtocolError, match="requires the Character arm"):
        FrozenReplayPlan((), _arm("SEQUENTIAL"), None, D1ReplayProfile.CHARACTER_EXTENDED).validate(extended_set)


def test_core_baseline_helper_explicitly_selects_character_free_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "core"
    nodes = root / "workspaces" / "workspace" / "agents" / "agent" / "private" / "nodes.jsonl"
    nodes.parent.mkdir(parents=True)
    nodes.write_text('{"eid": 1}\n', encoding="utf-8")
    baseline = SimpleNamespace(
        root=str(root), workspace_id="workspace", agent_id="agent",
        baseline_profile=CORE_CHARACTER_FREE_BASELINE_PROFILE,
        character_seed=None, character_state=None, digest="f" * 64,
    )
    observed: dict[str, object] = {}

    def fingerprint(**kwargs):
        observed.update(kwargs)
        return baseline

    monkeypatch.setattr(concrete_freeze, "fingerprint_legacy_baseline", fingerprint)
    monkeypatch.setattr(concrete_freeze, "verify_legacy_baseline", lambda _baseline: None)
    monkeypatch.setattr(concrete_freeze, "CORE_CHARACTER_FREE_L0_FINGERPRINT", "f" * 64)
    assert concrete_freeze._require_exact_core_baseline(root=root, workspace_id="workspace", agent_id="agent") is baseline
    assert observed["character_seed_required"] is False


def _document(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_core_artifact_is_separate_pinned_and_assigns_every_fixture_once() -> None:
    assert hashlib.sha256(_OLD.read_bytes()).hexdigest() == _OLD_SHA256
    document = _document(_CORE)
    binding = document["binding"]
    assert binding["profile"] == D1ReplayProfile.CORE_ONLY.value
    assert binding["l0_fingerprint_sha256"] == CORE_CHARACTER_FREE_L0_FINGERPRINT
    assert binding["side_store_observation_digest"] == CORE_SIDE_STORE_OBSERVATION_DIGEST
    assert binding["character_arm_administered"] is False
    assert binding["character_subarm_status"] == "DEFERRED_PENDING_PROVENANCE_VOCABULARY"
    assert binding["native_formal_event_count"] == 0
    assert binding["replay_plan"]["character_arm"] is None
    assert all(item["kind"] != "CHARACTER_SUBARM" for item in binding["fixture_set"]["fixtures"])
    requested_ids = [item[0] for item in binding["requests"]]
    assigned_ids = [
        fixture_id
        for arm in (*binding["replay_plan"]["micro_arms"], binding["replay_plan"]["sequential_arm"])
        for fixture_id in arm["fixture_ids"]
    ]
    assert Counter(assigned_ids) == Counter(requested_ids)
    assert len(assigned_ids) == len(set(assigned_ids))


def test_old_character_hash_cannot_verify_core_but_core_lock_passes_read_only_runner_check() -> None:
    old = _document(_OLD)["administration_inputs"]
    core = _document(_CORE)["administration_inputs"]
    old_inputs = FrozenAdministrationInputs(**old)
    core_inputs = FrozenAdministrationInputs(**core)
    runner = FormalAdministrationRunner(repository_root=_ROOT, expected_repository_head="0" * 40)
    with pytest.raises(D1ProtocolError, match="changed after freeze"):
        runner.verify_frozen_inputs(
            inputs=old_inputs,
            protocol_sha256=core["protocol_sha256"],
            fixture_sha256=core["fixture_sha256"],
        )
    runner.verify_frozen_inputs(
        inputs=core_inputs,
        protocol_sha256=core["protocol_sha256"],
        fixture_sha256=core["fixture_sha256"],
    )
