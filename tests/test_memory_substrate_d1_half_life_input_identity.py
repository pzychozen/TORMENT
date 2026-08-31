from __future__ import annotations

import inspect
import json

import numpy as np

from experiments.memory_substrate_d1_trace_replay_v1.formal_core_executor import CoreFrozenFixture
from experiments.memory_substrate_d1_trace_replay_v1.formal_core_ports import CoreD1SourceLocations
from experiments.memory_substrate_d1_trace_replay_v1.half_life_input_identity import (
    RESIDUAL_FIXTURE_IDS,
    characterize_legacy_http_time_sensitivity,
    frozen_residual_half_lives,
    trace_half_life_values,
    verify_frozen_inputs_match_v1_native_artifact,
)
from experiments.memory_substrate_d1_trace_replay_v1.identified_defect_regression import (
    characterize_native_same_input_half_life_storage,
)
from torment_service.memory_graph import MemoryGraph


def test_frozen_half_life_inputs_match_the_recorded_v1_native_artifact() -> None:
    fixture = CoreFrozenFixture.load()

    assert frozen_residual_half_lives(fixture) == {
        "CORE-M3-distinct": 99.33128211275871,
        "CORE-M4-contradiction": 99.55574927563462,
        "CORE-S-distinct": 93.3092862907214,
        "CORE-S-contradiction": 93.19844095045838,
    }
    assert verify_frozen_inputs_match_v1_native_artifact(fixture) == {
        fixture_id: True for fixture_id in RESIDUAL_FIXTURE_IDS
    }


def test_half_life_trace_keeps_frozen_native_and_fresh_legacy_observations_distinct() -> None:
    trace = trace_half_life_values(
        fixture_id="CORE-M3-distinct",
        frozen_storage_fact=99.33128211275871,
        native_durable=99.33128211275871,
        fresh_legacy_durable=99.03724640692022,
        fresh_legacy_signal=99.33128211275871,
        fresh_legacy_half_life_inputs={
            "kernel_signal_half_life": 99.33128211275871,
            "survival_steps": 0.0,
            "tearing_risk": 0.0,
        },
    )

    assert trace["frozen_input_equals_native_durable"] is True
    assert trace["comparisons"]["frozen_vs_native"] == []
    assert len(trace["comparisons"]["frozen_vs_fresh_legacy"]) == 1
    assert len(trace["comparisons"]["fresh_legacy_durable_vs_signal"]) == 1
    assert trace["fresh_legacy_prewrite_inputs"]["tri_multiplier"] == 1.0


def test_legacy_memory_graph_publishes_the_supplied_half_life_without_transformation(tmp_path) -> None:
    graph = MemoryGraph(str(tmp_path / "legacy"))
    supplied = (0.5, 0.95, 99.33128211275871, 93.19844095045838)
    eids: list[int] = []
    for ordinal, half_life in enumerate(supplied):
        vector = np.zeros(384, dtype=np.float32)
        vector[ordinal] = 1.0
        eids.append(graph.add_memory(
            summary=f"D1O legacy input {ordinal}", embedding=vector,
            mtype="episode", strength=0.5, confidence=0.5,
            half_life_days=half_life, user_id="d1o", step=ordinal + 1,
            memory_class="core",
        ))
    nodes = {
        int(row["eid"]): row["payload"]
        for row in (
            json.loads(line)
            for line in (tmp_path / "legacy" / "nodes.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }

    assert [float(nodes[eid]["half_life"]) for eid in eids] == list(supplied)
    assert '"half_life": float(half_life_days)' in inspect.getsource(MemoryGraph.spawn_memory)


def test_qualified_native_create_publishes_the_supplied_half_life_without_transformation(tmp_path) -> None:
    values = (0.5, 99.33128211275871)
    rows = characterize_native_same_input_half_life_storage(
        target_root=tmp_path / "native",
        fixture=CoreFrozenFixture.load(),
        half_life_inputs=values,
    )

    assert rows == tuple((value, value) for value in values)


def test_legacy_http_time_characterization_separates_kernel_signal_from_retrieval_decay() -> None:
    characterization = characterize_legacy_http_time_sensitivity(
        l0_root=CoreD1SourceLocations.frozen_default().l0_root,
    )

    assert characterization == {
        "immutable_l0_created_ts": 1788172879,
        "immutable_l0_half_life": 99.1158347920021,
        "retrieval_decay_reads_l0_timestamps": True,
        "kernel_signal_precedes_retrieval": True,
        "kernel_signal_reads_wall_clock": False,
        "legacy_http_replay_time_invariant": True,
    }
