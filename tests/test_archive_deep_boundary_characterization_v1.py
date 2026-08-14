"""Regression coverage for the Archive/Deep automatic-recall boundary.

Every Fabric and endpoint instance uses ``tmp_path`` data only.  This locks
the post-restoration rule: Archive automatic recall is opt-in, while Deep
remains mode-derived and continues to use the existing fallback semantics.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterator

import numpy as np
import pytest
from starlette.requests import Request

from torment_service.compression import (
    CompressionCandidate,
    CompressionExecutor,
    _get_or_create_deep_store,
)
from torment_service.fabric import TormentFabric


WORKSPACE_ID = "archive_deep_boundary_ws"
AGENT_ID = "archive_deep_boundary_agent"
DOMAIN_ID = "personal"
DEEP_SENTINEL = "DEEP_BOUNDARY_SENTINEL cobalt archive-independent memory"
PUBLIC_ARCHIVE_SENTINEL = "PUBLIC_ARCHIVE_BOUNDARY_SENTINEL amber reference"
PRIVATE_ARCHIVE_SENTINEL = "PRIVATE_ARCHIVE_BOUNDARY_SENTINEL violet restricted"
PLANNER_PROMPT = "Please explain the identity in this archive document."


def _restore_env(saved: Dict[str, str | None]) -> None:
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _flag_enabled(flag: str | None) -> bool:
    value = "0" if flag is None else flag
    return value not in ("0", "false", "no", "off")


def _planner_snapshot(
    flag: str | None, monkeypatch: pytest.MonkeyPatch,
) -> Dict[str, Any]:
    """Run the real controller with its import-time environment latch set to flag."""
    import torment_service.thinking_controller as tc

    enabled = _flag_enabled(flag)
    with monkeypatch.context() as scoped:
        if flag is None:
            scoped.delenv("TORMENT_ARCHIVE_RECALL", raising=False)
        else:
            scoped.setenv("TORMENT_ARCHIVE_RECALL", flag)
        # ``thinking_controller`` reads this environment variable at import time.
        # Set the loaded latch to exactly the value that its source expression
        # produces, avoiding Windows-unstable in-process reload/subprocess paths.
        scoped.setattr(tc, "_ARCHIVE_RECALL_ENABLE", enabled)
        plan = tc.ThinkingController().deliberate_only(
            WORKSPACE_ID, AGENT_ID, PLANNER_PROMPT,
        ).memory_plan
        return {
            "retrieve_archive": plan.retrieve_archive,
            "retrieve_deep": plan.retrieve_deep,
            "top_k_by_lane": dict(plan.top_k_by_lane),
            "weight_by_lane": dict(plan.weight_by_lane),
        }


def _configure_fabric_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_CHECKPOINT_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "1")
    monkeypatch.setenv("TORMENT_SRG_ENABLE", "0")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "0")
    monkeypatch.setenv("TORMENT_SQLITE_INDEX_ENABLE", "0")


def _close_fabric_io(fabric: TormentFabric) -> None:
    for graph in list(getattr(fabric, "private_graphs", {}).values()):
        try:
            graph.close()
        except Exception:
            pass
    for store in list(getattr(fabric, "_deep_stores", {}).values()):
        try:
            store.close()
        except Exception:
            pass
    fabric.close()


def _create_real_deep_sentinel(fabric: TormentFabric) -> int:
    """Create one genuine compressed record whose source row remains present."""
    fabric.get_workspace(WORKSPACE_ID, domains=[DOMAIN_ID])
    fabric.create_agent(WORKSPACE_ID, AGENT_ID)
    ak = fabric._agent_key(WORKSPACE_ID, AGENT_ID)
    graph = fabric.private_graphs[ak]
    embedding = np.asarray(fabric.kernel.embedder.embed(DEEP_SENTINEL), dtype=np.float32)
    eid = graph.add_memory(
        summary=DEEP_SENTINEL,
        embedding=embedding,
        mtype="episode",
        strength=0.25,
        confidence=0.9,
        half_life_days=30.0,
        canon=False,
        user_id=AGENT_ID,
        step=1,
        memory_class="core",
        extra_payload={
            "workspace_id": WORKSPACE_ID,
            "domain_id": DOMAIN_ID,
            "scope": "private",
            "agent_id": AGENT_ID,
            "state_symbol": "circle",
            "symbol_trace": ["circle"],
            "in_corridor": False,
            "survival_steps": 0.0,
            "tearing_risk": 0.0,
        },
    )
    deep_store = _get_or_create_deep_store(fabric, AGENT_ID, workspace_id=WORKSPACE_ID)
    event = CompressionExecutor(graph, deep_store).execute(
        [CompressionCandidate(
            eid=int(eid), born_step=1, summary=DEEP_SENTINEL, score=0.9,
            memory_class="core", tier="relational", route="long_path",
        )],
        step=600,
        trigger="archive_deep_boundary_characterization",
    )
    assert event.exported_deep == 1
    return int(eid)


def _core_sentinel_hits(count: int) -> list[Dict[str, Any]]:
    return [
        {
            "eid": 10_000 + index,
            "summary": f"CORE_HEADROOM_SENTINEL_{count}_{index}",
            "score": 0.99 - index * 0.01,
            "scope": "private",
            "memory_class": "core",
        }
        for index in range(count)
    ]


def test_archive_recall_flag_owns_archive_but_not_deep_planning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Archive defaults off; Deep remains enabled for the same identity turn."""
    observed = {
        "absent" if flag is None else flag: _planner_snapshot(flag, monkeypatch)
        for flag in (None, "0", "1")
    }

    assert observed["1"]["retrieve_archive"] is True
    assert observed["1"]["retrieve_deep"] is True
    assert observed["1"]["top_k_by_lane"]["archive"] == 4
    assert observed["1"]["top_k_by_lane"]["deep"] == 3
    assert observed["1"]["weight_by_lane"]["archive"] == 0.45
    assert observed["1"]["weight_by_lane"]["deep"] == 0.60

    for disabled in ("absent", "0"):
        assert observed[disabled]["retrieve_archive"] is False
        assert observed[disabled]["retrieve_deep"] is True
        assert observed[disabled]["top_k_by_lane"]["archive"] == 0
        assert observed[disabled]["top_k_by_lane"]["deep"] == 3
        assert observed[disabled]["weight_by_lane"]["archive"] == 0.0
        assert observed[disabled]["weight_by_lane"]["deep"] == 0.60

    print("ARCHIVE_DEEP_PLANNER=" + json.dumps(observed, sort_keys=True))


def test_fabric_deep_fallback_uses_remaining_headroom_for_both_flag_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe actual DeepMemoryStore.query calls under controlled Core headroom."""
    _configure_fabric_env(monkeypatch)
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric_data"))
    try:
        deep_eid = _create_real_deep_sentinel(fabric)
        ak = fabric._agent_key(WORKSPACE_ID, AGENT_ID)
        deep_store = fabric._deep_stores[ak]
        original_deep_query = deep_store.query
        observed: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for flag in ("1", "0"):
            plan = _planner_snapshot(flag, monkeypatch)
            per_headroom: Dict[str, Dict[str, Any]] = {}
            for core_count, label in ((0, "none"), (1, "some"), (3, "all")):
                calls: list[int] = []

                def deep_query_spy(query_embedding, *, top_k: int):
                    calls.append(top_k)
                    return original_deep_query(query_embedding, top_k=top_k)

                monkeypatch.setattr(deep_store, "query", deep_query_spy)
                monkeypatch.setattr(
                    fabric,
                    "_query_private_lane",
                    lambda *_args, _hits=_core_sentinel_hits(core_count), **_kwargs: list(_hits),
                )
                monkeypatch.setattr(
                    fabric,
                    "_query_shared_lane",
                    lambda *_args, **_kwargs: ([], []),
                )

                result = fabric.query(
                    WORKSPACE_ID,
                    AGENT_ID,
                    DEEP_SENTINEL,
                    top_k=3,
                    domain_id=DOMAIN_ID,
                    memory_plan={"top_k_by_lane": dict(plan["top_k_by_lane"])},
                )
                deep_hits = [
                    hit for hit in result["results"]
                    if hit.get("from_spirit_return") is True
                ]
                expected_budget = 3 - core_count
                assert calls == ([] if expected_budget == 0 else [expected_budget])
                assert bool(deep_hits) is (expected_budget > 0)
                deep_eids = [int(hit.get("eid", -1)) for hit in deep_hits]
                assert deep_eids == ([deep_eid] if expected_budget > 0 else [])
                if deep_hits:
                    assert any(DEEP_SENTINEL in json.dumps(hit, sort_keys=True) for hit in deep_hits)

                per_headroom[label] = {
                    "planned_deep_top_k": plan["top_k_by_lane"]["deep"],
                    "core_hits": core_count,
                    "DeepMemoryStore.query_top_k_calls": calls,
                    "deep_hit_count": len(deep_hits),
                    "deep_eids": deep_eids,
                    "deep_sentinel_surfaced": bool(deep_hits),
                }
            observed[flag] = per_headroom

        assert observed["1"] == {
            "none": {
                "planned_deep_top_k": 3,
                "core_hits": 0,
                "DeepMemoryStore.query_top_k_calls": [3],
                "deep_hit_count": 1,
                "deep_eids": [deep_eid],
                "deep_sentinel_surfaced": True,
            },
            "some": {
                "planned_deep_top_k": 3,
                "core_hits": 1,
                "DeepMemoryStore.query_top_k_calls": [2],
                "deep_hit_count": 1,
                "deep_eids": [deep_eid],
                "deep_sentinel_surfaced": True,
            },
            "all": {
                "planned_deep_top_k": 3,
                "core_hits": 3,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "deep_eids": [],
                "deep_sentinel_surfaced": False,
            },
        }
        assert observed["0"] == {
            "none": {
                "planned_deep_top_k": 3,
                "core_hits": 0,
                "DeepMemoryStore.query_top_k_calls": [3],
                "deep_hit_count": 1,
                "deep_eids": [deep_eid],
                "deep_sentinel_surfaced": True,
            },
            "some": {
                "planned_deep_top_k": 3,
                "core_hits": 1,
                "DeepMemoryStore.query_top_k_calls": [2],
                "deep_hit_count": 1,
                "deep_eids": [deep_eid],
                "deep_sentinel_surfaced": True,
            },
            "all": {
                "planned_deep_top_k": 3,
                "core_hits": 3,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "deep_eids": [],
                "deep_sentinel_surfaced": False,
            },
        }
        print("ARCHIVE_DEEP_FABRIC=" + json.dumps(observed, sort_keys=True))
    finally:
        _close_fabric_io(fabric)


def test_explicit_deep_zero_declines_lane_without_warmup_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit Deep zero is a lane decline, not a gap-fill request."""
    _configure_fabric_env(monkeypatch)
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric_data"))
    try:
        _create_real_deep_sentinel(fabric)
        ak = fabric._agent_key(WORKSPACE_ID, AGENT_ID)
        deep_store = fabric._deep_stores[ak]
        original_deep_query = deep_store.query
        warmup_path = (
            tmp_path / "fabric_data" / "workspaces" / WORKSPACE_ID / "agents"
            / AGENT_ID / "warmup" / "warmup_state.jsonl"
        )
        observed: Dict[str, Dict[str, Any]] = {}

        for core_count, label in ((3, "remaining_0"), (2, "remaining_1"), (0, "remaining_3")):
            calls: list[int] = []

            def deep_query_spy(query_embedding, *, top_k: int):
                calls.append(top_k)
                return original_deep_query(query_embedding, top_k=top_k)

            monkeypatch.setattr(deep_store, "query", deep_query_spy)
            monkeypatch.setattr(
                fabric,
                "_query_private_lane",
                lambda *_args, _hits=_core_sentinel_hits(core_count), **_kwargs: list(_hits),
            )
            monkeypatch.setattr(
                fabric,
                "_query_shared_lane",
                lambda *_args, **_kwargs: ([], []),
            )

            result = fabric.query(
                WORKSPACE_ID,
                AGENT_ID,
                DEEP_SENTINEL,
                top_k=3,
                domain_id=DOMAIN_ID,
                memory_plan={"top_k_by_lane": {"core": 6, "relational": 4, "deep": 0}},
            )
            deep_hits = [
                hit for hit in result["results"]
                if hit.get("from_spirit_return") is True
            ]
            remaining = 3 - core_count
            assert calls == []
            assert deep_hits == []
            assert not warmup_path.exists()
            observed[label] = {
                "remaining": remaining,
                "DeepMemoryStore.query_top_k_calls": calls,
                "deep_hit_count": len(deep_hits),
                "warmup_rows": 0,
            }

        assert observed == {
            "remaining_0": {
                "remaining": 0,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "warmup_rows": 0,
            },
            "remaining_1": {
                "remaining": 1,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "warmup_rows": 0,
            },
            "remaining_3": {
                "remaining": 3,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "warmup_rows": 0,
            },
        }
        print("ARCHIVE_DEEP_EXPLICIT_ZERO=" + json.dumps(observed, sort_keys=True))
    finally:
        _close_fabric_io(fabric)


def test_absent_deep_key_preserves_baseline_gap_fill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A present plan without a Deep key keeps pre-Thinking gap-fill behavior."""
    _configure_fabric_env(monkeypatch)
    fabric = TormentFabric(data_dir=str(tmp_path / "fabric_data"))
    try:
        deep_eid = _create_real_deep_sentinel(fabric)
        ak = fabric._agent_key(WORKSPACE_ID, AGENT_ID)
        deep_store = fabric._deep_stores[ak]
        original_deep_query = deep_store.query
        warmup_path = (
            tmp_path / "fabric_data" / "workspaces" / WORKSPACE_ID / "agents"
            / AGENT_ID / "warmup" / "warmup_state.jsonl"
        )
        observed: Dict[str, Dict[str, Any]] = {}

        for core_count, label in ((3, "remaining_0"), (2, "remaining_1"), (0, "remaining_3")):
            calls: list[int] = []

            def deep_query_spy(query_embedding, *, top_k: int):
                calls.append(top_k)
                return original_deep_query(query_embedding, top_k=top_k)

            monkeypatch.setattr(deep_store, "query", deep_query_spy)
            monkeypatch.setattr(
                fabric,
                "_query_private_lane",
                lambda *_args, _hits=_core_sentinel_hits(core_count), **_kwargs: list(_hits),
            )
            monkeypatch.setattr(
                fabric,
                "_query_shared_lane",
                lambda *_args, **_kwargs: ([], []),
            )

            result = fabric.query(
                WORKSPACE_ID,
                AGENT_ID,
                DEEP_SENTINEL,
                top_k=3,
                domain_id=DOMAIN_ID,
                memory_plan={"top_k_by_lane": {"core": 6, "relational": 4}},
            )
            deep_hits = [
                hit for hit in result["results"]
                if hit.get("from_spirit_return") is True
            ]
            remaining = 3 - core_count
            expected_calls = [] if remaining == 0 else [remaining]
            assert calls == expected_calls
            assert [int(hit.get("eid", -1)) for hit in deep_hits] == (
                [] if remaining == 0 else [deep_eid]
            )
            warmup_rows = (
                len([line for line in warmup_path.read_text(encoding="utf-8").splitlines() if line])
                if warmup_path.exists() else 0
            )
            observed[label] = {
                "remaining": remaining,
                "DeepMemoryStore.query_top_k_calls": calls,
                "deep_hit_count": len(deep_hits),
                "warmup_rows": warmup_rows,
            }

        assert observed == {
            "remaining_0": {
                "remaining": 0,
                "DeepMemoryStore.query_top_k_calls": [],
                "deep_hit_count": 0,
                "warmup_rows": 0,
            },
            "remaining_1": {
                "remaining": 1,
                "DeepMemoryStore.query_top_k_calls": [1],
                "deep_hit_count": 1,
                "warmup_rows": 1,
            },
            "remaining_3": {
                "remaining": 3,
                "DeepMemoryStore.query_top_k_calls": [3],
                "deep_hit_count": 1,
                "warmup_rows": 2,
            },
        }
        print("ARCHIVE_DEEP_ABSENT_KEY=" + json.dumps(observed, sort_keys=True))
    finally:
        _close_fabric_io(fabric)


@contextmanager
def _isolated_app(data_dir: Path, archive_recall_flag: str | None) -> Iterator[Any]:
    """Run real endpoint functions against temporary Fabric and Archive globals."""
    env_updates = {
        "TORMENT_DATA_DIR": str(data_dir),
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_COMPRESS_ENABLE": "0",
        "TORMENT_SRG_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_SQLITE_INDEX_ENABLE": "0",
    }
    saved = {key: os.environ.get(key) for key in env_updates}
    os.environ.update(env_updates)
    original_archive_recall_env = os.environ.get("TORMENT_ARCHIVE_RECALL")
    if archive_recall_flag is None:
        os.environ.pop("TORMENT_ARCHIVE_RECALL", None)
    else:
        os.environ["TORMENT_ARCHIVE_RECALL"] = archive_recall_flag
    import torment_service.app as appmod

    original_data_dir = appmod.DATA_DIR
    original_fabric = appmod.fabric
    original_archive_stores = appmod._archive_stores
    original_archive_latch = appmod._thinking_controller_module._ARCHIVE_RECALL_ENABLE
    test_fabric = TormentFabric(data_dir=str(data_dir))
    appmod.DATA_DIR = str(data_dir)
    appmod.fabric = test_fabric
    appmod._archive_stores = {}
    appmod._thinking_controller_module._ARCHIVE_RECALL_ENABLE = _flag_enabled(
        archive_recall_flag
    )
    try:
        yield appmod
    finally:
        test_fabric.close()
        appmod.DATA_DIR = original_data_dir
        appmod.fabric = original_fabric
        appmod._archive_stores = original_archive_stores
        appmod._thinking_controller_module._ARCHIVE_RECALL_ENABLE = original_archive_latch
        _restore_env(saved)
        if original_archive_recall_env is None:
            os.environ.pop("TORMENT_ARCHIVE_RECALL", None)
        else:
            os.environ["TORMENT_ARCHIVE_RECALL"] = original_archive_recall_env


def _endpoint_request(path: str) -> Request:
    """Minimal request object for endpoint-local auth-context resolution."""
    return Request({
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 0),
        "server": ("testserver", 80),
        "scheme": "http",
    })


def _bootstrap_endpoint(appmod: Any, workspace_id: str, agent_id: str) -> None:
    workspace = appmod.workspace_create(
        appmod.WorkspaceCreateReq(workspace_id=workspace_id),
    )
    assert workspace["workspace_id"] == workspace_id
    agent = appmod.agent_create(
        appmod.AgentCreateReq(
            workspace_id=workspace_id,
            agent_id=agent_id,
            seed={"coupling_mode": "read_only", "coupling_strength": 0.2},
        )
    )
    assert agent["agent_id"] == agent_id


def _archive_flag_http_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flag: str | None,
) -> Dict[str, Any]:
    label = "absent" if flag is None else flag
    data_dir = tmp_path / f"endpoint_data_{label}"
    data_dir.mkdir()
    workspace_id = "archive_deep_http_ws"
    agent_id = "archive_deep_http_agent"
    with _isolated_app(data_dir, flag) as appmod:
        _bootstrap_endpoint(appmod, workspace_id, agent_id)
        for doc_id, text, governance in (
            ("public_archive_doc", PUBLIC_ARCHIVE_SENTINEL, None),
            ("private_archive_doc", PRIVATE_ARCHIVE_SENTINEL, {"non_shareable": True}),
        ):
            payload: Dict[str, Any] = {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "doc_id": doc_id,
                "title": doc_id,
                "text": text,
            }
            if governance is not None:
                payload["governance"] = governance
            response = appmod.ingest_document(
                appmod.IngestDocumentReq(**payload),
                _endpoint_request("/archive/ingest_document"),
            )
            assert response["doc_id"] == doc_id

        store = appmod._get_archive_store(workspace_id, agent_id)
        original_retrieve = store.retrieve
        calls: list[Dict[str, Any]] = []

        def retrieve_spy(*args, **kwargs):
            calls.append(dict(kwargs))
            return original_retrieve(*args, **kwargs)

        monkeypatch.setattr(store, "retrieve", retrieve_spy)
        retrieved = appmod.retrieve_assembled(
            appmod.AssembleContextReq(
                workspace_id=workspace_id,
                agent_id=agent_id,
                query="ARCHIVE_BOUNDARY_SENTINEL",
                top_k=3,
                archive_top_k=10,
                archive_min_score=-1.0,
                token_budget=1500,
                include_assembly_audit=True,
            )
        )
        archive_blocks = retrieved.get("blocks", {}).get("archive_context", [])
        assembled_text = retrieved.get("assembled_text", "")
        excluded = (
            retrieved.get("assembly_audit", {})
            .get("filter_a", {})
            .get("archive_excluded", [])
        )
        counts_path = (
            data_dir / "workspaces" / workspace_id / "agents" / agent_id
            / "memory_archive" / "retrieval_counts.json"
        )
        if _flag_enabled(flag):
            assert archive_blocks, "public archive sentinel should create BLOCK_ARCHIVE"
            assert PUBLIC_ARCHIVE_SENTINEL in assembled_text
            assert PRIVATE_ARCHIVE_SENTINEL not in assembled_text
            assert any(
                item.get("doc_id") == "private_archive_doc"
                and item.get("excluded_reason") == "non_shareable"
                for item in excluded
            )
            assert counts_path.exists(), "automatic Archive retrieval should track its hits"
        else:
            assert archive_blocks == []
            assert PUBLIC_ARCHIVE_SENTINEL not in assembled_text
            assert PRIVATE_ARCHIVE_SENTINEL not in assembled_text
            assert excluded == []
            assert not counts_path.exists(), (
                "disabled automatic Archive recall must not write retrieval counts"
            )

        explicit_response = appmod.archive_query(
            appmod.ArchiveQueryReq(
                workspace_id=workspace_id,
                agent_id=agent_id,
                query="ARCHIVE_BOUNDARY_SENTINEL",
                top_k=10,
                min_score=-1.0,
            ),
            _endpoint_request("/archive/query"),
        )
        raw_results = explicit_response["results"]
        raw_doc_ids = {str(hit.get("doc_id")) for hit in raw_results}
        assert {"public_archive_doc", "private_archive_doc"} <= raw_doc_ids

        return {
            "retrieve_calls": calls,
            "BLOCK_ARCHIVE_present": bool(archive_blocks),
            "public_archive_in_assembled_text": PUBLIC_ARCHIVE_SENTINEL in assembled_text,
            "private_archive_in_assembled_text": PRIVATE_ARCHIVE_SENTINEL in assembled_text,
            "filter_a_excluded": sorted(
                (item.get("doc_id"), item.get("excluded_reason")) for item in excluded
            ),
            "retrieval_counts_written": counts_path.exists(),
            "archive_query_raw_doc_ids": sorted(raw_doc_ids),
        }


def test_automatic_archive_recall_is_default_off_and_explicit_archive_api_is_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only automatic /retrieve Archive participation is gated by the flag."""
    observed = {
        "absent" if flag is None else flag: _archive_flag_http_snapshot(
            tmp_path, monkeypatch, flag
        )
        for flag in (None, "0", "1")
    }
    for disabled in ("absent", "0"):
        snapshot = observed[disabled]
        # Disabled /retrieve makes no ArchiveStore.retrieve call. The one
        # recorded call is the explicit raw /archive/query request.
        assert snapshot["retrieve_calls"] == [{
            "query": "ARCHIVE_BOUNDARY_SENTINEL",
            "top_k": 10,
            "min_score": -1.0,
            "doc_id_filter": None,
        }]
        assert snapshot["BLOCK_ARCHIVE_present"] is False
        assert snapshot["retrieval_counts_written"] is False

    assert observed["1"]["retrieve_calls"] == [
        {
            "query": "ARCHIVE_BOUNDARY_SENTINEL",
            "top_k": 10,
            "min_score": -1.0,
        },
        {
            "query": "ARCHIVE_BOUNDARY_SENTINEL",
            "top_k": 10,
            "min_score": -1.0,
            "doc_id_filter": None,
        },
    ]
    assert observed["1"]["BLOCK_ARCHIVE_present"] is True
    assert observed["1"]["retrieval_counts_written"] is True
    assert observed["1"]["filter_a_excluded"] == [
        ("private_archive_doc", "non_shareable")
    ]
    # /archive/query remains raw and is independent of automatic recall.
    raw_doc_ids = ["private_archive_doc", "public_archive_doc"]
    assert all(
        snapshot["archive_query_raw_doc_ids"] == raw_doc_ids
        for snapshot in observed.values()
    )
    print("ARCHIVE_DEEP_ENDPOINT=" + json.dumps(observed, sort_keys=True))
