"""H2a: existing-native Hivemind writes and non-materializing query context.

The admitted root uses the existing root-wide disposable cutover fixture with
two private agents in an admitted shared domain. No Genesis or model is involved.
"""
from __future__ import annotations

from hashlib import sha256
from contextlib import contextmanager
import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.character import CharacterSeed, CharacterState
from torment_service.collective_field import CollectiveField, read_existing_collective_events
from torment_service.fabric import TormentFabric
from torment_service.public_runtime import (
    PublicRuntimeConfiguration, PublicRuntimeMode, close_public_runtime, create_public_runtime,
)
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.deployment_selector import establish_selector_era, initialize_selector

from test_b5_a4r3_public_backend_selection import _forbid_legacy_core_memory
from test_post_i4_full_root_disposable_rehearsal_r1 import (
    _activate_root_to_p7, _build_disposable_root,
)

WS, AGENT_A, AGENT_B, DOMAIN = "north", "same-agent", "second-agent", "common-domain"
VECTOR = [0.0, 1.0] + [0.0] * 382


class _DeterministicHiveEmbedder:
    # Match the admitted fixture lane identity, without importing its model.
    provider, model, dim = "st", "BAAI/bge-small-en-v1.5", 384

    def embed(self, _text):
        return np.asarray(VECTOR, dtype=np.float32)


class _NativeHiveFabric(TormentFabric):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kernel.embedder = _DeterministicHiveEmbedder()


def _snapshot(root: Path):
    """Include all paths and durable bytes/mtimes; SHM read marks are transient."""
    return {
        p.relative_to(root).as_posix(): (
            "directory" if p.is_dir() else "sqlite-transient-read-marks" if p.name.endswith("-shm")
            else (sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        )
        for p in sorted(root.rglob("*"))
    }


@contextmanager
def _settled_native_storage(runtime):
    """Settle setup WAL before the observation; pin resources during query.

    The checkpoint belongs to fixture preparation, not the measured query.
    Keeping this connection open prevents last-close sidecar cleanup from
    being confused with a query mutation. Logical SQL and durable bytes are
    both compared; only the non-durable SHM read marks are excluded.
    """
    with open_existing_native_core_connection(runtime.native_owner.authority_facts.core_database_path) as opened:
        assert opened.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
        before_sql = tuple(opened.connection.iterdump())
        yield
        assert tuple(opened.connection.iterdump()) == before_sql


@pytest.fixture
def native_hive(tmp_path, monkeypatch):
    import torment_service.public_runtime as public_runtime

    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_HIVEMIND_ENABLE", "1")
    monkeypatch.setenv("TORMENT_CHARACTER_ENABLE", "0")
    monkeypatch.setenv("TORMENT_COMPRESS_ENABLE", "0")
    monkeypatch.setattr(public_runtime, "TormentFabric", _NativeHiveFabric)
    request, profile = _build_disposable_root(tmp_path, "h2a-native", extra_private_in_north=True)
    # The synthetic source fixture has an inert core and explicit historical
    # owners. Establish its existing selector-era authority with the same
    # supported test APIs as B5; do not infer fresh-root public authority.
    establish_selector_era(data_root=request.root)
    initialize_selector(data_root=request.root, operation_key="h2a-fixture-existing-legacy")
    _activate_root_to_p7(request)
    root = request.root
    legacy_calls = _forbid_legacy_core_memory(monkeypatch)
    config = PublicRuntimeConfiguration(effective_profile=profile)
    runtime = create_public_runtime(root, config)
    try:
        assert runtime.mode is PublicRuntimeMode.NATIVE
        assert runtime.cognition_fabric._hivemind_enable is True
        with runtime.native_owner.open_query_context(embedder=runtime.kernel.embedder, workspace_id=WS) as reader:
            for agent in (AGENT_A, AGENT_B):
                assert reader.private_lane(WS, agent) is not None
            assert reader.shared_lane(WS, DOMAIN) is not None
        yield root, runtime, config
        assert legacy_calls == []
    finally:
        close_public_runtime(root)


def _ingest(runtime, agent, *, scope="private", skip_packet=False):
    return runtime.ingest(
        WS, agent, f"{agent} {scope} research protocol observation",
        step=10, domain_id=DOMAIN, scope=scope,
        supplied_embedding=VECTOR,
        public_mutation_key=f"h2a:{agent}:{scope}", skip_packet_emission=skip_packet,
    )


def _provide_character_context(runtime, private_result):
    """Supply frozen existing external Character facts, as in A3 read parity."""
    fabric = runtime.cognition_fabric
    identity = fabric.ident_store.load(WS, AGENT_A)
    identity.seed = {"seed_id": "aria-h2a", "seed_text": "Aria keeps precise research records."}
    fabric.ident_store.save(identity)
    fabric.character_store.save_seed(WS, CharacterSeed(
        "aria-h2a", "Aria", identity.seed["seed_text"], owner_agent_id=AGENT_A,
        seed_motif_id=private_result["motifs"][0], seed_eids=[private_result["eid"]],
    ))
    fabric.character_store.save_state(WS, CharacterState(
        WS, AGENT_A, "aria-h2a", drift_direction="toward_seed",
    ))
    fabric._character_enable = True


def _query(runtime):
    return runtime.query(
        WS, AGENT_A, "research protocol observation", domain_id=DOMAIN, top_k=8, explain=True,
    )


def _assert_query_lanes(result):
    private = [r for r in result["results"] if r["scope"] == "private"]
    shared = [r for r in result["results"] if r["scope"] == "shared"]
    assert private and shared
    assert any(f"{AGENT_A} private" in r["summary"] for r in private)
    assert all(f"{AGENT_B} private" not in r["summary"] for r in result["results"])
    assert any(r["domain_id"] == DOMAIN for r in shared)
    assert result["character_context"]["seed_id"] == "aria-h2a"


def _forbid_query_writer(fabric, monkeypatch):
    calls = []

    def refuse(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("query must not acquire a collective writer")

    monkeypatch.setattr(fabric, "_get_collective_field", refuse)
    monkeypatch.setattr(CollectiveField, "__init__", refuse)
    return calls


def test_absent_native_field_query_keeps_storage_absent(native_hive, monkeypatch):
    root, runtime, _config = native_hive
    first = _ingest(runtime, AGENT_A, skip_packet=True)
    assert first["stored"] is True
    assert _ingest(runtime, AGENT_B, skip_packet=True)["stored"] is True
    assert _ingest(runtime, AGENT_A, scope="shared", skip_packet=True)["stored"] is True
    _provide_character_context(runtime, first)
    field = root / "workspaces" / WS / "collective"
    assert not field.exists()
    calls = _forbid_query_writer(runtime.cognition_fabric, monkeypatch)
    with _settled_native_storage(runtime):
        before = _snapshot(root)
        result = _query(runtime)
        _assert_query_lanes(result)
        assert result.get("collective_context", {}) == {}
        assert not field.exists()
        assert _snapshot(root) == before
    assert not calls and not runtime.cognition_fabric._collective_fields


def test_native_two_agent_ingest_events_query_and_scoring_parity(native_hive, monkeypatch):
    root, runtime, config = native_hive
    first = _ingest(runtime, AGENT_A)
    second = _ingest(runtime, AGENT_B)
    assert first["stored"] is True and second["stored"] is True
    field = runtime.cognition_fabric._collective_fields[WS]
    packets = field.all_packets()
    events = field.recent_events()
    assert {p["agent_id"] for p in packets} == {AGENT_A, AGENT_B}
    assert all(p["domain_id"] == DOMAIN for p in packets)
    assert any(set(e["participating_agents"]) == {AGENT_A, AGENT_B} for e in events)
    assert _ingest(runtime, AGENT_A, scope="shared", skip_packet=True)["stored"] is True
    # Exact public replay must not duplicate an emitted packet or event.
    assert _ingest(runtime, AGENT_A) == first
    assert field.all_packets() == packets and field.recent_events() == events
    _provide_character_context(runtime, first)
    fabric = runtime.cognition_fabric
    calls = _forbid_query_writer(fabric, monkeypatch)
    # Freeze only query wall time so ordinary recency is identical in both reads.
    import torment_service.fabric as fabric_module
    query_time = fabric_module.time.time()
    monkeypatch.setattr(fabric_module.time, "time", lambda: query_time)
    with _settled_native_storage(runtime):
        before = _snapshot(root)
        on = _query(runtime)
        fabric._hivemind_enable = False
        off = _query(runtime)
        fabric._hivemind_enable = True
        _assert_query_lanes(on)
        assert on["collective_context"]["recent_events"] == events[-5:]
        assert "collective_context" not in off
        assert on["results"] == off["results"]
        assert on["domains"] == off["domains"]
        assert on["character_context"] == off["character_context"]
        assert _snapshot(root) == before and not calls
    # A cold public runtime reads the same persisted field without reconstructing
    # a CollectiveField or relying on the ingest process's packet cache.
    close_public_runtime(root)
    restarted = create_public_runtime(root, config)
    restarted.cognition_fabric._character_enable = True
    with _settled_native_storage(restarted):
        before_restart_query = _snapshot(root)
        cold = _query(restarted)
        assert cold["collective_context"] == on["collective_context"]
        _assert_query_lanes(cold)
        assert not restarted.cognition_fabric._collective_fields
        assert _snapshot(root) == before_restart_query and not calls


def test_collective_reader_absent_root_creates_nothing(tmp_path):
    root = tmp_path / "absent"
    before = _snapshot(tmp_path)
    assert read_existing_collective_events("orchard", str(root)) == []
    assert _snapshot(tmp_path) == before and not root.exists()


def test_collective_reader_tolerates_incomplete_records_and_preserves_context_order(tmp_path):
    field = CollectiveField("orchard", str(tmp_path))
    rows = [
        {"event_id": f"research-{i}", "domain_id": "research"} for i in range(8)
    ] + [{"event_id": "archive-1", "domain_id": "archive"}]
    Path(field._events_path).write_text(
        "\n".join(json.dumps(row) for row in rows) + '\nnull\n[]\n{"incomplete":', encoding="utf-8",
    )
    before = _snapshot(tmp_path)
    assert read_existing_collective_events("orchard", str(tmp_path)) == rows
    # Exercise the production context formatter without constructing a Fabric.
    owner = type("ReadOwner", (), {"data_dir": str(tmp_path)})()
    result = TormentFabric._collective_query_context(owner, "orchard", ["research", "archive", "research"])
    assert result["collective_context"]["recent_events"] == rows[3:8] + rows[8:]
    assert result["collective_context"]["event_count"] == 6
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("workspace", ["", ".", "..", "../escape", "ws/escape", "ws\\escape"])
def test_collective_reader_rejects_invalid_workspace(tmp_path, workspace):
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError):
        read_existing_collective_events(workspace, str(tmp_path))
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("escape_at", ["collective", "events.jsonl"])
def test_collective_reader_retains_canonical_containment(tmp_path, monkeypatch, escape_at):
    import os
    original = os.path.realpath

    def resolved(path, *args, **kwargs):
        if str(path).endswith(escape_at):
            return original(tmp_path.parent / "outside" / escape_at)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", resolved)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="escapes"):
        read_existing_collective_events("orchard", str(tmp_path))
    assert _snapshot(tmp_path) == before
