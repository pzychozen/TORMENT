import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _close_fabric_resources(fabric):
    for graph in list(getattr(fabric, "private_graphs", {}).values()):
        graph.close()
    for workspace in list(getattr(fabric, "workspaces", {}).values()):
        for graph in list(getattr(workspace, "shared_graphs", {}).values()):
            graph.close()
    fabric.close()


def _torment_module_names():
    return {
        name
        for name in sys.modules
        if name == "torment_service" or name.startswith("torment_service.")
    }


@pytest.fixture(autouse=True)
def _restore_torment_imports_after_test():
    before = _torment_module_names()
    yield
    appmod = sys.modules.get("torment_service.app")
    if appmod is not None and "torment_service.app" not in before:
        fabric = getattr(appmod, "fabric", None)
        if fabric is not None:
            _close_fabric_resources(fabric)
    for name in sorted(_torment_module_names() - before, reverse=True):
        sys.modules.pop(name, None)


def test_positive_aligned_drift_route_probe_ingest_and_persistence():
    repo_root = Path(__file__).resolve().parents[1].resolve()
    with tempfile.TemporaryDirectory(prefix="ingest_route_probe_") as temp_name:
        tmp_root = Path(temp_name).resolve()
        data_dir = tmp_root / "data"
        assert repo_root not in data_dir.resolve().parents
        assert data_dir.resolve() != repo_root
        assert "eira_voss" not in str(data_dir).lower()
        data_dir.mkdir(parents=True, exist_ok=True)

        saved_env = {
            "TORMENT_DATA_DIR": os.environ.get("TORMENT_DATA_DIR"),
            "TORMENT_EMBED_PROVIDER": os.environ.get("TORMENT_EMBED_PROVIDER"),
            "TORMENT_SQLITE_INDEX_ENABLE": os.environ.get("TORMENT_SQLITE_INDEX_ENABLE"),
            "TORMENT_TEST_CONDITION": os.environ.get("TORMENT_TEST_CONDITION"),
        }
        os.environ["TORMENT_DATA_DIR"] = str(data_dir)
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        os.environ["TORMENT_SQLITE_INDEX_ENABLE"] = "0"
        os.environ["TORMENT_TEST_CONDITION"] = "integration_probe"

        import torment_service.app as appmod
        from torment_service.character import CharacterState
        from torment_service.fabric import TormentFabric

        original_data_dir = appmod.DATA_DIR
        original_fabric = appmod.fabric
        test_fabric = TormentFabric(data_dir=str(data_dir))
        appmod.DATA_DIR = str(data_dir)
        appmod.fabric = test_fabric
        fresh = None
        try:
            with TestClient(appmod.app) as client:
                assert client.post("/workspace/create", json={"workspace_id": "probe_ws"}).status_code == 200
                assert client.post(
                    "/agent/create",
                    json={
                        "workspace_id": "probe_ws",
                        "agent_id": "eira_probe",
                        "seed": {
                            "seed_id": "seed-test",
                            "character_name": "Eira Probe",
                            "seed_text": "steady seed",
                        },
                    },
                ).status_code == 200

                appmod.fabric.character_store.save_state(
                    "probe_ws",
                    CharacterState(
                        workspace_id="probe_ws",
                        agent_id="eira_probe",
                        seed_id="seed-test",
                        drift_score=0.915931224822998,
                        drift_direction="stable",
                        relational_count=22,
                    ),
                )
                before_state = appmod.fabric.character_store.load_state("probe_ws", "eira_probe").to_dict()
                before_relational_count = before_state["relational_count"]
                before_drift_history = list(before_state["drift_history"])
                ak = appmod.fabric._agent_key("probe_ws", "eira_probe")
                before_graph_steps = {
                    int(eid): int(ent.born_step)
                    for eid, ent in appmod.fabric.private_graphs[ak].entities.items()
                }

                route_resp = client.post(
                    "/agent/ingest/route_probe",
                    json={
                        "workspace_id": "probe_ws",
                        "agent_id": "eira_probe",
                        "text": "who am i as a stable character identity summary",
                        "step": 1,
                        "scope": "private",
                    },
                )
                assert route_resp.status_code == 200
                route = route_resp.json()
                assert route["predicted_path"] == "fast"
                assert route["write_capable"] is True
                assert route["would_escalate"] is False
                assert route["drift_score"] == 0.915931224822998
                assert route["drift_direction"] == "stable"
                assert route["relational_count"] == 22
                assert "identity_sensitive" in route["escalation_reasons"]
                after_state = appmod.fabric.character_store.load_state("probe_ws", "eira_probe").to_dict()
                assert after_state["relational_count"] == before_relational_count
                assert after_state["drift_history"] == before_drift_history
                assert after_state == before_state
                after_probe_steps = {
                    int(eid): int(ent.born_step)
                    for eid, ent in appmod.fabric.private_graphs[ak].entities.items()
                }
                assert after_probe_steps == before_graph_steps

                ingest_resp = client.post(
                    "/agent/ingest",
                    json={
                        "workspace_id": "probe_ws",
                        "agent_id": "eira_probe",
                        "text": "First durable probe memory.",
                        "step": 1,
                        "scope": "private",
                    },
                )
                assert ingest_resp.status_code == 200
                body = ingest_resp.json()
                assert body.get("stored") is True or body.get("reinforced") is True
                assert body["path"] == "fast"
                assert body["result_code"] in ("stored", "reinforced")

                graph = appmod.fabric.private_graphs[ak]
                assert any(int(ent.born_step) == 1 for ent in graph.entities.values())

                fresh = TormentFabric(data_dir=str(data_dir))
                fresh.get_workspace("probe_ws")
                fresh.create_agent("probe_ws", "eira_probe")
                fresh_graph = fresh.private_graphs[fresh._agent_key("probe_ws", "eira_probe")]
                assert any(int(ent.born_step) == 1 for ent in fresh_graph.entities.values())
        finally:
            if fresh is not None:
                _close_fabric_resources(fresh)
            _close_fabric_resources(test_fabric)
            appmod.fabric = original_fabric
            appmod.DATA_DIR = original_data_dir
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
