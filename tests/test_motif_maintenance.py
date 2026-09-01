"""7G5E4D-M1 parity tests for suggestion-only motif maintenance."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import numpy as np
import pytest

from torment_service.fabric import TormentFabric
from torment_service.motif_geometry_port import (
    LegacyMotifGeometryAdapter,
    RuntimeMotifGeometry,
)
from torment_service.motif_maintenance import (
    LegacyMotifMaintenanceAdapter,
    NativeMotifAutoMergeRefused,
    NativeMotifMaintenanceAdapter,
)
from torment_service.motifs import Motif, MotifRegistry


def _row(
    motif_id: str,
    *,
    centroid: tuple[float, ...],
    strength: float,
    label: str | None = None,
) -> RuntimeMotifGeometry:
    return RuntimeMotifGeometry(
        domain_id="research",
        runtime_motif_id=motif_id,
        label=label or f"Label {motif_id}",
        centroid=centroid,
        strength=strength,
        stability_score=.6,
        member_count=3,
        created_ts=100,
        last_active_ts=101,
    )


class _StaticGeometry:
    """Read-only fixture geometry; its centroid helper must not be consulted."""

    def __init__(self, rows: Mapping[str, tuple[RuntimeMotifGeometry, ...]]) -> None:
        self._rows = dict(rows)

    def domain_ids(self) -> tuple[str, ...]:
        return tuple(self._rows)

    def list_motifs(self, domain_id: str) -> tuple[RuntimeMotifGeometry, ...]:
        return self._rows[domain_id]

    def domain_centroid(self, _domain_id: str, _expected_dimension: int) -> np.ndarray:
        raise AssertionError("domain suggestion must preserve its raw-mean law")


def _legacy_registry(root: Path, rows: tuple[RuntimeMotifGeometry, ...]) -> MotifRegistry:
    registry = MotifRegistry(str(root), "ws", "research")
    for row in rows:
        registry.motifs[row.runtime_motif_id] = Motif(
            motif_id=row.runtime_motif_id,
            domain_id=row.domain_id,
            label=row.label,
            centroid=list(row.centroid),
            strength=row.strength,
            members=list(range(row.member_count)),
            contributing_agents=["aria"],
            stability_score=row.stability_score,
            created_ts=row.created_ts,
            last_active_ts=row.last_active_ts,
        )
    return registry


def _event_rows(root: Path) -> list[dict]:
    path = root / "workspaces" / "ws" / "domains" / "research" / "motif_events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _workflow_paths(root: Path) -> tuple[Path, Path, Path]:
    base = root / "workspaces" / "ws" / "domains" / "research"
    return base / "motifs.json", base / "motif_events.jsonl", base / "motif_merges.json"


@pytest.mark.parametrize(
    ("rows", "target_n", "expect_score"),
    [
        ((), 24, 0.0),
        ((_row("motif_research_0001", centroid=(1.0, 0.0), strength=.8),), 24, 0.0),
        (
            (
                _row("motif_research_0001", centroid=(1.0, 0.0), strength=1.0),
                _row("motif_research_0002", centroid=(0.99, 0.01), strength=1.0),
            ),
            24,
                # Exact current NumPy/epsilon result for equal strengths;
                # this is intentionally not rounded before threshold use.
                .5874999999981381,
        ),
        (
            (
                _row("motif_research_0001", centroid=(1.0, 0.0), strength=1.0),
                _row("motif_research_0002", centroid=(0.99, 0.01), strength=.2),
                _row("motif_research_0003", centroid=(0.98, 0.02), strength=.5),
            ),
            3,
            None,
        ),
    ],
)
def test_native_entropy_matches_legacy_for_empty_single_threshold_and_uneven_states(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rows: tuple[RuntimeMotifGeometry, ...],
    target_n: int,
    expect_score: float | None,
) -> None:
    monkeypatch.setattr("time.time", lambda: 1_000)
    legacy = _legacy_registry(tmp_path / "legacy", rows)
    native = NativeMotifMaintenanceAdapter(
        _StaticGeometry({"research": rows}),
        data_dir=str(tmp_path / "native"), workspace_id="ws", domain_id="research",
    )

    legacy_report = LegacyMotifMaintenanceAdapter(legacy).update_entropy_and_suggest(
        target_n=target_n, entropy_high=2.0, sim_threshold=.93,
        max_suggestions=20, auto_merge=False, auto_merge_trigger=.8,
    )
    native_report = native.update_entropy_and_suggest(
        target_n=target_n, entropy_high=2.0, sim_threshold=.93,
        max_suggestions=20, auto_merge=False, auto_merge_trigger=.8,
    )

    assert native_report == legacy_report
    if expect_score is not None:
        assert native_report["entropy_score"] == expect_score
    assert _event_rows(tmp_path / "native") == _event_rows(tmp_path / "legacy")


def test_native_maintenance_matches_legacy_events_suggestions_order_and_retry_law(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 1_111)
    rows = (
        _row("motif_research_0001", centroid=(1.0, 0.0), strength=.8),
        _row("motif_research_0002", centroid=(.999, .001), strength=.4),
        _row("motif_research_0003", centroid=(.998, .002), strength=.2),
    )
    legacy_root, native_root = tmp_path / "legacy", tmp_path / "native"
    legacy = _legacy_registry(legacy_root, rows)
    native = NativeMotifMaintenanceAdapter(
        _StaticGeometry({"research": rows}),
        data_dir=str(native_root), workspace_id="ws", domain_id="research",
    )
    kwargs = dict(
        target_n=3, entropy_high=.0, sim_threshold=.9,
        max_suggestions=2, auto_merge=False, auto_merge_trigger=.8,
    )

    assert native.update_entropy_and_suggest(**kwargs) == LegacyMotifMaintenanceAdapter(legacy).update_entropy_and_suggest(**kwargs)
    legacy_paths = _workflow_paths(legacy_root)
    native_paths = _workflow_paths(native_root)
    assert native_paths[1].read_bytes() == legacy_paths[1].read_bytes()
    assert native_paths[2].read_bytes() == legacy_paths[2].read_bytes()
    assert not native_paths[0].exists()  # no native geometry copied into motifs.json
    first_events = _event_rows(native_root)
    assert [event["type"] for event in first_events] == [
        "MOTIF_ENTROPY", "MOTIF_MERGE_SUGGESTED", "MOTIF_MERGE_SUGGESTED",
    ]
    first_merges = native_paths[2].read_bytes()

    # Existing suggestions are retained, entropy events intentionally repeat,
    # and a call producing no new suggestion does not rewrite the merge JSON.
    assert native.update_entropy_and_suggest(**kwargs) == LegacyMotifMaintenanceAdapter(legacy).update_entropy_and_suggest(**kwargs)
    assert native_paths[2].read_bytes() == first_merges
    assert native_paths[1].read_bytes() == legacy_paths[1].read_bytes()
    assert [event["type"] for event in _event_rows(native_root)] == [
        "MOTIF_ENTROPY", "MOTIF_MERGE_SUGGESTED", "MOTIF_MERGE_SUGGESTED", "MOTIF_ENTROPY",
    ]

    # Reloading only the workflow side-store preserves duplicate suppression;
    # geometry remains caller-owned and no legacy motif truth is needed.
    reopened = NativeMotifMaintenanceAdapter(
        _StaticGeometry({"research": rows}),
        data_dir=str(native_root), workspace_id="ws", domain_id="research",
    )
    reopened.update_entropy_and_suggest(**kwargs)
    assert native_paths[2].read_bytes() == first_merges
    assert not native_paths[0].exists()


def test_native_entropy_threshold_is_identical_below_at_and_above_the_current_score(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("time.time", lambda: 1_222)
    rows = (
        _row("motif_research_0001", centroid=(1.0, 0.0), strength=1.0),
        _row("motif_research_0002", centroid=(.999, .001), strength=1.0),
    )
    baseline = _legacy_registry(tmp_path / "baseline", rows).entropy_report(target_n=24)["entropy_score"]
    for name, threshold, expect_merges in (
        ("below", np.nextafter(baseline, np.inf), False),
        ("at", baseline, True),
        ("above", np.nextafter(baseline, -np.inf), True),
    ):
        legacy_root, native_root = tmp_path / f"legacy-{name}", tmp_path / f"native-{name}"
        legacy = _legacy_registry(legacy_root, rows)
        native = NativeMotifMaintenanceAdapter(
            _StaticGeometry({"research": rows}),
            data_dir=str(native_root), workspace_id="ws", domain_id="research",
        )
        kwargs = dict(
            target_n=24, entropy_high=threshold, sim_threshold=.9,
            max_suggestions=20, auto_merge=False, auto_merge_trigger=.8,
        )
        assert native.update_entropy_and_suggest(**kwargs) == LegacyMotifMaintenanceAdapter(legacy).update_entropy_and_suggest(**kwargs)
        legacy_paths, native_paths = _workflow_paths(legacy_root), _workflow_paths(native_root)
        assert native_paths[1].read_bytes() == legacy_paths[1].read_bytes()
        assert native_paths[2].exists() is expect_merges
        assert legacy_paths[2].exists() is expect_merges
        if expect_merges:
            assert native_paths[2].read_bytes() == legacy_paths[2].read_bytes()


def test_native_auto_merge_refuses_before_any_workflow_or_motif_effect(tmp_path: Path) -> None:
    rows = (
        _row("motif_research_0001", centroid=(1.0, 0.0), strength=.8),
        _row("motif_research_0002", centroid=(.999, .001), strength=.7),
    )
    root = tmp_path / "native"
    native = NativeMotifMaintenanceAdapter(
        _StaticGeometry({"research": rows}),
        data_dir=str(root), workspace_id="ws", domain_id="research",
    )
    motifs_path, events_path, merges_path = _workflow_paths(root)
    with pytest.raises(NativeMotifAutoMergeRefused, match="7G5E4D-M2"):
        native.update_entropy_and_suggest(
            target_n=2, entropy_high=.0, sim_threshold=.9,
            max_suggestions=20, auto_merge=True, auto_merge_trigger=.0,
        )
    assert not motifs_path.exists() and not events_path.exists() and not merges_path.exists()


def _suggestion_geometry() -> _StaticGeometry:
    return _StaticGeometry({
        "research": (
            _row("motif_research_0001", centroid=(1.0, 0.0), strength=.8, label="Emergent Thread"),
            _row("motif_research_0002", centroid=(-1.0, 0.0), strength=.2, label="Counterweight"),
        ),
        "engineering": (
            RuntimeMotifGeometry(
                domain_id="engineering", runtime_motif_id="motif_engineering_0001",
                label="Engineering", centroid=(0.0, 1.0), strength=.5,
                stability_score=.5, member_count=1, created_ts=100, last_active_ts=101,
            ),
        ),
    })


def _domain_suggestion_bytes(root: Path) -> bytes:
    return (root / "workspaces" / "ws" / "domain_suggestions.json").read_bytes()


def test_domain_suggestion_uses_injected_geometry_raw_centroid_and_existing_side_store_law(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_HASH_DIM", "2")
    monkeypatch.setattr("time.time", lambda: 2_222)
    native_root, legacy_root = tmp_path / "native-domain", tmp_path / "legacy-domain"
    geometry = _suggestion_geometry()

    native_fabric = TormentFabric(str(native_root))
    legacy_fabric = TormentFabric(str(legacy_root))
    try:
        native_ws = native_fabric.get_workspace("ws", domains=["research", "engineering"])
        legacy_ws = legacy_fabric.get_workspace("ws", domains=["research", "engineering"])
        # Native geometry is the only geometry reachable by this call.  Its
        # domain_centroid deliberately raises, proving the raw motif-centroid
        # average—not the weighted helper—is the preserved law.
        native_fabric._maybe_suggest_domain(native_ws, "research", geometry=geometry)

        for domain, rows in (("research", geometry.list_motifs("research")), ("engineering", geometry.list_motifs("engineering"))):
            registry = legacy_ws.motif_regs[domain]
            for row in rows:
                registry.motifs[row.runtime_motif_id] = Motif(
                    motif_id=row.runtime_motif_id, domain_id=domain, label=row.label,
                    centroid=list(row.centroid), strength=row.strength,
                    members=[1], contributing_agents=["aria"],
                    stability_score=row.stability_score, created_ts=row.created_ts,
                    last_active_ts=row.last_active_ts,
                )
        legacy_fabric._maybe_suggest_domain(
            legacy_ws, "research", geometry=LegacyMotifGeometryAdapter(legacy_ws.motif_regs),
        )
        assert _domain_suggestion_bytes(native_root) == _domain_suggestion_bytes(legacy_root)
        suggestions = json.loads(_domain_suggestion_bytes(native_root))["suggestions"]
        assert suggestions == [{
            "domain_id": "suggested_emergent_thread", "from_domain": "research",
            "motif_id": "motif_research_0001", "motif_label": "Emergent Thread",
            "strength": .8, "score": 0.0, "ts": 2_222, "approved": False,
        }]

        # Current duplicate suppression is only (domain_id, motif_id); no
        # separate existing-domain refusal is present in the legacy heuristic.
        native_fabric._maybe_suggest_domain(native_ws, "research", geometry=geometry)
        assert _domain_suggestion_bytes(native_root) == _domain_suggestion_bytes(legacy_root)
    finally:
        native_fabric.close()
        legacy_fabric.close()

    # Reloading the external workflow normally retains the pair-key duplicate
    # suppression without asking any legacy motif registry for native geometry.
    reopened = TormentFabric(str(native_root))
    try:
        reopened_ws = reopened.get_workspace("ws")
        reopened._maybe_suggest_domain(reopened_ws, "research", geometry=geometry)
        assert _domain_suggestion_bytes(native_root) == _domain_suggestion_bytes(legacy_root)
    finally:
        reopened.close()
