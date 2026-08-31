from __future__ import annotations

import inspect
import json

import pytest

from experiments.memory_substrate_d1_trace_replay_v1.identified_defect_regression import (
    native_owned_contradiction_guard,
)
from experiments.memory_substrate_d1_trace_replay_v1.identified_defect_semantics import (
    SemanticProjectionUnavailable,
    compare_regression_semantics,
    project_legacy_durable_storage,
    project_legacy_regression_semantics,
    project_native_regression_semantics,
)
from torment_service.fabric import TormentFabric, _detect_canon_conflict
from torment_service.provenance_v1 import ProvenanceV1
from torment_service.substrate.memory_reinforcement import realize_reinforcement_patch


def _provenance() -> dict[str, object]:
    return ProvenanceV1(
        source_type="user_input",
        source_role=None,
        write_path="direct_ingest",
        created_at_step=101,
        created_at_ts="2026-08-31T13:02:42Z",
        parent_eids=[],
    ).to_dict()


def _governance() -> dict[str, bool]:
    return {
        "protected": False,
        "non_shareable": False,
        "collective_export_blocked": False,
        "collective_reingest_blocked": False,
        "decay_accelerated": False,
    }


def test_direct_ingest_semantic_profile_compares_actual_durable_facts() -> None:
    legacy = project_legacy_regression_semantics({
        "governance": _governance(),
        "provenance": _provenance(),
        "lifecycle_status": {
            "state": "unset",
            "is_authoritative_on_row": True,
            "requires_join": None,
            "set_by": {"actor": "system", "via": "ingest_unmarked", "at": 1},
            "history_ref": None,
        },
    })
    native = project_native_regression_semantics(
        existence_state="EXISTS",
        lifecycle_state="ORDINARY",
        lifecycle_authoritative=False,
        governance=_governance(),
        provenance_record={
            "origin_kind": "RUNTIME_PROVENANCE_V1",
            "descriptive_notes": json.dumps({
                "format": "TORMENT_PROVENANCE_V1_DESCRIPTIVE/1",
                "provenance_v1": _provenance(),
            }),
        },
    )

    assert legacy["lifecycle"]["legacy_authority_observation"] != native["lifecycle"]["native_authority_observation"]
    assert compare_regression_semantics(legacy, native, frozen_provenance=_provenance()) == ()


def test_native_provenance_projection_refuses_missing_retained_evidence() -> None:
    with pytest.raises(SemanticProjectionUnavailable, match="retained descriptive evidence"):
        project_native_regression_semantics(
            existence_state="EXISTS",
            lifecycle_state="ORDINARY",
            lifecycle_authoritative=False,
            governance=_governance(),
            provenance_record={"origin_kind": "RUNTIME_PROVENANCE_V1", "descriptive_notes": None},
        )


def test_regression_storage_uses_actual_legacy_payload_not_response_signals() -> None:
    projected = project_legacy_durable_storage(
        {"strength": 0.944426, "confidence": 0.939794, "half_life_days": 92.590, "reinforcement_count": 1},
        {"strength": 0.9664, "confidence": 0.9479279126163149, "half_life": 93.59112770662337, "reinforcement_count": 1},
    )
    assert projected == {
        "strength": 0.9664,
        "confidence": 0.9479279126163149,
        "half_life_days": 93.59112770662337,
        "reinforcement_count": 1,
    }


def test_high_strength_characterization_reads_the_live_legacy_reinforcement_law() -> None:
    source = inspect.getsource(TormentFabric.ingest)
    assert "min(0.98, _old_str + (1.0 - _old_str) * 0.3)" in source


@pytest.mark.parametrize(
    ("prior", "expected"),
    [
        (0.50, 0.65),
        (0.95, 0.965),
        (0.9799, 0.98),
        (0.98, 0.98),
        (0.9801, 0.98),
        (0.999943, 0.98),
    ],
)
def test_native_reinforcement_uses_the_existing_legacy_high_strength_law(
    prior: float, expected: float,
) -> None:
    patch = realize_reinforcement_patch(
        {"strength": prior, "reinforcement_count": 0},
        source_channel="direct_ingest",
        reinforcement_step=2,
        last_reinforced_ts=2,
        last_tool_refresh_ts=None,
    )
    assert patch.values["strength"] == expected


def test_native_contradiction_guard_is_the_production_decision_without_legacy_answer() -> None:
    incoming = "The harbor pathway is not permitted"
    existing = "The harbor pathway is permitted"
    similarity = 0.95
    assert native_owned_contradiction_guard(incoming, existing, similarity) is True
    assert native_owned_contradiction_guard(incoming, existing, similarity) == _detect_canon_conflict(
        incoming, existing, similarity,
    )[0]
