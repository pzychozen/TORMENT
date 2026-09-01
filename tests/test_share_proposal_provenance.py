"""7G5E4D deterministic typed lineage for authorized ShareProposals."""
from __future__ import annotations

from datetime import datetime

import pytest

import torment_service.provenance_v1 as provenance_v1
from torment_service.provenance_v1 import (
    ProvenanceV1,
    SOURCE_SHARE_PROPOSAL,
    VALID_SOURCE_TYPES,
    VALID_WRITE_PATHS,
    WRITE_SHARE_PROPOSAL_OPERATOR,
    WRITE_SHARE_PROPOSAL_QUORUM,
)


def test_share_proposal_vocabulary_is_accepted_and_unknown_values_still_fail() -> None:
    assert SOURCE_SHARE_PROPOSAL in VALID_SOURCE_TYPES
    assert WRITE_SHARE_PROPOSAL_QUORUM in VALID_WRITE_PATHS
    assert WRITE_SHARE_PROPOSAL_OPERATOR in VALID_WRITE_PATHS
    with pytest.raises(ValueError, match="Invalid source_type"):
        ProvenanceV1(source_type="unknown_share_proposal_origin")
    with pytest.raises(ValueError, match="Invalid write_path"):
        ProvenanceV1(write_path="unknown_share_proposal_path")


def test_quorum_factory_uses_maximum_contributor_timestamp_independent_of_order() -> None:
    first = ProvenanceV1.for_share_proposal_quorum(
        contributing_created_ts=(100, 200, 150),
    )
    reordered = ProvenanceV1.for_share_proposal_quorum(
        contributing_created_ts=(150, 100, 200),
    )

    assert first.to_dict() == reordered.to_dict()
    assert first.source_type == SOURCE_SHARE_PROPOSAL
    assert first.write_path == WRITE_SHARE_PROPOSAL_QUORUM
    assert first.source_role is None
    assert first.parent_eids == []
    assert first.created_at_step is None
    assert first.created_at_ts == "1970-01-01T00:03:20Z"
    assert first.notes is None


def test_operator_factory_uses_the_durable_proposal_creation_timestamp() -> None:
    provenance = ProvenanceV1.for_share_proposal_operator(
        proposal_created_ts=1_700_000_000,
    )

    assert provenance.source_type == SOURCE_SHARE_PROPOSAL
    assert provenance.write_path == WRITE_SHARE_PROPOSAL_OPERATOR
    assert provenance.source_role is None
    assert provenance.parent_eids == []
    assert provenance.created_at_step is None
    assert provenance.created_at_ts == "2023-11-14T22:13:20Z"
    assert provenance.notes is None


def test_share_proposal_factories_do_not_consult_the_wall_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    class ClockWithChangingNow:
        now_value = datetime(2001, 1, 1)
        now_calls = 0

        @classmethod
        def now(cls, *_args, **_kwargs):
            cls.now_calls += 1
            return cls.now_value

        @staticmethod
        def fromtimestamp(timestamp, tz):
            return datetime.fromtimestamp(timestamp, tz)

    monkeypatch.setattr(provenance_v1, "datetime", ClockWithChangingNow)

    quorum_first = ProvenanceV1.for_share_proposal_quorum(
        contributing_created_ts=(170, 220),
    )
    operator_first = ProvenanceV1.for_share_proposal_operator(proposal_created_ts=220)
    ClockWithChangingNow.now_value = datetime(2099, 12, 31)
    quorum_retry = ProvenanceV1.for_share_proposal_quorum(
        contributing_created_ts=(170, 220),
    )
    operator_retry = ProvenanceV1.for_share_proposal_operator(proposal_created_ts=220)

    assert ClockWithChangingNow.now_calls == 0
    assert quorum_first.to_dict() == quorum_retry.to_dict()
    assert operator_first.to_dict() == operator_retry.to_dict()


@pytest.mark.parametrize(
    ("timestamps", "message"),
    (
        ((), "must not be empty"),
        ((1, -1), "non-negative integers"),
        ((1, True), "non-negative integers"),
        ((1, "200"), "non-negative integers"),
    ),
)
def test_quorum_factory_refuses_empty_and_invalid_durable_timestamps(timestamps, message) -> None:
    with pytest.raises(ValueError, match=message):
        ProvenanceV1.for_share_proposal_quorum(contributing_created_ts=timestamps)


@pytest.mark.parametrize("timestamp", (-1, True, "200", 1.5))
def test_operator_factory_refuses_invalid_durable_timestamp(timestamp) -> None:
    with pytest.raises(ValueError, match="non-negative integers"):
        ProvenanceV1.for_share_proposal_operator(proposal_created_ts=timestamp)
