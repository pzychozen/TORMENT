"""Read-only half-life input-identity helpers for D1O/V2.

The helpers keep the storage-facing frozen facts, durable values, and fresh
HTTP/kernel observations distinct.  They neither alter the D1 fixture nor
reclassify either historical result.
"""
from __future__ import annotations

from dataclasses import asdict
import inspect
import json
import math
from pathlib import Path
from typing import Any, Mapping

from torment_service.fabric import TormentFabric
from torment_service.memory_graph import _half_life_decay_factor
from torment_service.memory_kernel import TriOctaMemoryKernel

from .compare import compare_scalar
from .formal_core_executor import CoreFrozenFixture
from .protocol import D1ProtocolError


RESIDUAL_FIXTURE_IDS = (
    "CORE-M3-distinct",
    "CORE-M4-contradiction",
    "CORE-S-distinct",
    "CORE-S-contradiction",
)

# These are the qualified-native durable values recorded by the completed V1
# result.  Keeping the historical observation separate from a fresh V2 run
# makes the required pre-check explicit: a sealed fixture must agree with the
# already-recorded qualified result before this slice treats fresh legacy HTTP
# values as an upstream characterization.
REGRESSION_V1_NATIVE_DURABLE_HALF_LIVES = {
    "CORE-M3-distinct": 99.33128211275871,
    "CORE-M4-contradiction": 99.55574927563462,
    "CORE-S-distinct": 93.3092862907214,
    "CORE-S-contradiction": 93.19844095045838,
}


def frozen_residual_half_lives(fixture: CoreFrozenFixture) -> dict[str, float]:
    """Extract exactly the four frozen storage-facing half-life inputs."""
    values: dict[str, float] = {}
    for arm in fixture.arms:
        for event in arm.events:
            if event.fixture_id not in RESIDUAL_FIXTURE_IDS:
                continue
            raw = event.native_request().get("half_life_days")
            try:
                value = float(raw)
            except (TypeError, ValueError, OverflowError) as exc:
                raise D1ProtocolError(f"{event.fixture_id} has no finite frozen half-life input") from exc
            if not math.isfinite(value) or value <= 0.0:
                raise D1ProtocolError(f"{event.fixture_id} frozen half-life input is invalid")
            values[event.fixture_id] = value
    if tuple(values) != RESIDUAL_FIXTURE_IDS:
        raise D1ProtocolError("D1O requires exactly the four known residual fixture IDs")
    return values


def verify_frozen_inputs_match_v1_native_artifact(
    fixture: CoreFrozenFixture,
) -> dict[str, bool]:
    """Prove the frozen A facts match the recorded V1 qualified B facts."""
    frozen = frozen_residual_half_lives(fixture)
    if tuple(REGRESSION_V1_NATIVE_DURABLE_HALF_LIVES) != RESIDUAL_FIXTURE_IDS:
        raise D1ProtocolError("D1O V1 native artifact inventory changed")
    result = {
        fixture_id: frozen[fixture_id] == REGRESSION_V1_NATIVE_DURABLE_HALF_LIVES[fixture_id]
        for fixture_id in RESIDUAL_FIXTURE_IDS
    }
    if not all(result.values()):
        raise D1ProtocolError("D1O frozen half-life facts do not match the recorded V1 native artifact")
    return result


def trace_half_life_values(
    *, fixture_id: str, frozen_storage_fact: float, native_durable: float,
    fresh_legacy_durable: float,
    fresh_legacy_signal: float | None,
    fresh_legacy_half_life_inputs: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Record the A/B/C/D trace with frozen-tolerance comparisons."""
    if fixture_id not in RESIDUAL_FIXTURE_IDS:
        raise D1ProtocolError("D1O half-life trace received a non-residual fixture")
    values = {
        "frozen_storage_fact_half_life": frozen_storage_fact,
        "native_durable_half_life": native_durable,
        "fresh_legacy_durable_half_life": fresh_legacy_durable,
        "fresh_legacy_http_signal_half_life": fresh_legacy_signal,
    }
    for name, value in values.items():
        if value is None and name == "fresh_legacy_http_signal_half_life":
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise D1ProtocolError(f"D1O {fixture_id} has invalid {name}") from exc
        if not math.isfinite(numeric):
            raise D1ProtocolError(f"D1O {fixture_id} has non-finite {name}")
        values[name] = numeric
    frozen_native = compare_scalar(
        values["frozen_storage_fact_half_life"], values["native_durable_half_life"],
        field="frozen_storage_fact_half_life/native_durable_half_life",
    )
    frozen_legacy = compare_scalar(
        values["frozen_storage_fact_half_life"], values["fresh_legacy_durable_half_life"],
        field="frozen_storage_fact_half_life/fresh_legacy_durable_half_life",
    )
    legacy_signal = () if values["fresh_legacy_http_signal_half_life"] is None else compare_scalar(
        values["fresh_legacy_durable_half_life"], values["fresh_legacy_http_signal_half_life"],
        field="fresh_legacy_durable_half_life/fresh_legacy_http_signal_half_life",
    ).differences
    if not isinstance(fresh_legacy_half_life_inputs, Mapping):
        raise D1ProtocolError(f"D1O {fixture_id} has no fresh legacy half-life input trace")
    try:
        kernel_signal = float(fresh_legacy_half_life_inputs["kernel_signal_half_life"])
        survival_steps = float(fresh_legacy_half_life_inputs["survival_steps"])
        tearing_risk = float(fresh_legacy_half_life_inputs["tearing_risk"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise D1ProtocolError(f"D1O {fixture_id} fresh legacy half-life input trace is invalid") from exc
    if not all(math.isfinite(item) for item in (kernel_signal, survival_steps, tearing_risk)):
        raise D1ProtocolError(f"D1O {fixture_id} fresh legacy half-life input trace is non-finite")
    if values["fresh_legacy_http_signal_half_life"] is None:
        raise D1ProtocolError(f"D1O {fixture_id} has no observable fresh legacy signal")
    signal_trace = compare_scalar(
        values["fresh_legacy_http_signal_half_life"], kernel_signal,
        field="fresh_legacy_http_signal_half_life/kernel_signal_half_life",
    )
    if signal_trace.differences:
        raise D1ProtocolError(f"D1O {fixture_id} changed its observed kernel signal")
    tri_multiplier = max(
        0.85,
        min(
            1.25,
            (1.0 + 0.20 * math.tanh(survival_steps / 200.0)) * (1.0 - 0.15 * tearing_risk),
        ),
    )
    effective_multiplier = values["fresh_legacy_durable_half_life"] / kernel_signal
    return {
        "fixture_id": fixture_id,
        **values,
        "comparisons": {
            "frozen_vs_native": [asdict(item) for item in frozen_native.differences],
            "frozen_vs_fresh_legacy": [asdict(item) for item in frozen_legacy.differences],
            "fresh_legacy_durable_vs_signal": [asdict(item) for item in legacy_signal],
        },
        "frozen_input_equals_native_durable": not frozen_native.differences,
        "fresh_legacy_prewrite_inputs": {
            "kernel_signal_half_life": kernel_signal,
            "survival_steps": survival_steps,
            "tearing_risk": tearing_risk,
            "tri_multiplier": tri_multiplier,
            "effective_legacy_prewrite_multiplier": effective_multiplier,
            "inferred_identity_decay_scale": effective_multiplier / tri_multiplier,
        },
    }


def characterize_legacy_http_time_sensitivity(*, l0_root: str | Path) -> dict[str, Any]:
    """Establish the current replay time boundary from L0 evidence and code.

    The L0 does have aging timestamps.  Current legacy retrieval consumes them
    only after ``TormentFabric.ingest`` has already produced kernel signals;
    neither the kernel signal producer nor Fabric's half-life multiplier reads
    wall-clock time.  This is intentionally a source characterization, not a
    clock-freezing intervention.
    """
    root = Path(l0_root).resolve()
    node_path = root / "workspaces" / "d1core20260831" / "agents" / "d1coreagent" / "private" / "nodes.jsonl"
    try:
        rows = [json.loads(line) for line in node_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise D1ProtocolError("D1O cannot read immutable L0 node timestamp evidence") from exc
    if len(rows) != 1 or not isinstance(rows[0], Mapping):
        raise D1ProtocolError("D1O requires exactly one immutable L0 node")
    payload = rows[0].get("payload")
    if not isinstance(payload, Mapping):
        raise D1ProtocolError("D1O immutable L0 node has no payload")
    created_ts = payload.get("created_ts")
    if not isinstance(created_ts, int) or isinstance(created_ts, bool) or created_ts <= 0:
        raise D1ProtocolError("D1O immutable L0 node has no valid created_ts")
    ingest_source = inspect.getsource(TormentFabric.ingest)
    kernel_source = inspect.getsource(TriOctaMemoryKernel.process)
    decay_source = inspect.getsource(_half_life_decay_factor)
    kernel_position = ingest_source.find("self.kernel.process(state, text, runtime_ctx)")
    retrieval_position = ingest_source.find("graph.search_by_embedding(")
    if kernel_position < 0 or retrieval_position < 0 or kernel_position >= retrieval_position:
        raise D1ProtocolError("D1O cannot establish kernel-before-retrieval ordering")
    if "time." in kernel_source or "_now_ts" in kernel_source:
        raise D1ProtocolError("D1O kernel signal producer has an unreviewed wall-clock dependency")
    if "now_ts" not in decay_source or "created_ts" not in decay_source:
        raise D1ProtocolError("D1O cannot establish legacy retrieval-decay timestamp use")
    return {
        "immutable_l0_created_ts": created_ts,
        "immutable_l0_half_life": float(payload.get("half_life", 0.0)),
        "retrieval_decay_reads_l0_timestamps": True,
        "kernel_signal_precedes_retrieval": True,
        "kernel_signal_reads_wall_clock": False,
        "legacy_http_replay_time_invariant": True,
    }


__all__ = [
    "REGRESSION_V1_NATIVE_DURABLE_HALF_LIVES",
    "RESIDUAL_FIXTURE_IDS",
    "characterize_legacy_http_time_sensitivity",
    "frozen_residual_half_lives",
    "trace_half_life_values",
    "verify_frozen_inputs_match_v1_native_artifact",
]
