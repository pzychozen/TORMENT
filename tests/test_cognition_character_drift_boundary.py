"""D1 regressions for the Character signed-score → cognition-risk boundary."""

from cognition.drift import _raw_to_drift_report, make_live_drift_check
from cognition.reintegration import _run_drift_check
from cognition.task_models import TaskPacket
from schemas.drift_report import DriftReport


def test_positive_character_centering_has_zero_cognition_risk() -> None:
    report = _raw_to_drift_report({"drift_score": 0.88, "drift_direction": "stable"})

    assert report.total_drift == 0.0
    assert report.zone == "green"
    assert not report.requires_block


def test_negative_away_seed_character_score_blocks() -> None:
    report = _raw_to_drift_report({"drift_score": -0.8, "drift_direction": "away_seed"})

    assert report.total_drift == 0.8
    assert report.zone == "hard_block"
    assert report.requires_block


def test_negative_away_seed_threshold_is_red_and_blocks() -> None:
    report = _raw_to_drift_report({"drift_score": -0.35, "drift_direction": "away_seed"})

    assert report.total_drift == 0.35
    assert report.zone == "red"
    assert report.requires_block


def test_negative_recovering_or_stable_score_does_not_block() -> None:
    toward = _raw_to_drift_report({"drift_score": -0.8, "drift_direction": "toward_seed"})
    stable = _raw_to_drift_report({"drift_score": -0.8, "drift_direction": "stable"})

    assert toward.zone == stable.zone == "hard_block"
    assert not toward.requires_block
    assert not stable.requires_block


def test_governance_breach_blocks_independently_of_direction() -> None:
    report = DriftReport(
        total_drift=0.0,
        drift_direction="toward_seed",
        governance_breach=True,
    )

    assert report.zone == "green"
    assert report.requires_block
    assert not report.allows_durable_write


def test_drift_exception_fails_closed_as_away_seed_hard_block() -> None:
    task = TaskPacket(
        workspace_id="d1-ws",
        agent_id="d1-agent",
        user_input="identity continuity review",
    )

    def fail(*_args):
        raise RuntimeError("drift source unavailable")

    report = _run_drift_check(task, fail)

    assert report.zone == "hard_block"
    assert report.drift_direction == "away_seed"
    assert report.requires_block


def test_live_adapter_exception_fails_closed_as_away_seed_hard_block() -> None:
    class BrokenFabric:
        def get_workspace(self, *_args):
            raise RuntimeError("workspace unavailable")

    report = make_live_drift_check(BrokenFabric())("d1-ws", "d1-agent")

    assert report.zone == "hard_block"
    assert report.drift_direction == "away_seed"
    assert report.requires_block
