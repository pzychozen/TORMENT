from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from torment_service.compression import CompressionCandidate
from torment_service.deep_memory import DeepMemory
from torment_service.deep_memory import DeepMemoryStore


def _candidate(eid: int, summary: str, score: float = 0.9) -> CompressionCandidate:
    return CompressionCandidate(
        eid=int(eid),
        born_step=int(eid),
        summary=str(summary),
        score=float(score),
        memory_class="core",
    )


def _record(eid: int, summary: str, embedding_ref=None) -> str:
    return json.dumps(
        DeepMemory(
            eid=int(eid),
            born_step=int(eid),
            compressed_step=100 + int(eid),
            summary=str(summary),
            compression_score=0.5,
            original_motif_id=None,
            memory_class="core",
            embedding_ref=embedding_ref,
            metadata={"type": "episode"},
        ).to_dict(),
        ensure_ascii=False,
    )


def _write_memories(base: Path, lines: list[str]) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base / "memories.jsonl").write_text(
        "".join(line if line.endswith("\n") else f"{line}\n" for line in lines),
        encoding="utf-8",
    )


def _export(
    store: DeepMemoryStore,
    eid: int,
    summary: str,
    embedding=None,
    score: float = 0.9,
    *,
    step: int | None = None,
) -> DeepMemory:
    return store.export(
        _candidate(eid, summary, score=score),
        embedding,
        {"type": "episode"},
        step=int(eid) if step is None else int(step),
    )


def _query_eids(
    store: DeepMemoryStore,
    embedding,
    *,
    top_k: int,
    min_similarity: float = 0.0,
) -> list[int]:
    return [
        int(mem.eid)
        for mem in store.query(
            np.asarray(embedding, dtype=np.float32),
            top_k=top_k,
            min_similarity=min_similarity,
        )
    ]


def test_blank_complete_line_before_later_valid_rows_keeps_recall_correct(tmp_path):
    base = tmp_path / "deep"
    _write_memories(
        base,
        [
            _record(1, "one"),
            "",
            _record(2, "two"),
            _record(3, "three"),
        ],
    )

    store = DeepMemoryStore(base, dim=4)
    try:
        recalled = store.recall(2)
        assert recalled is not None
        assert recalled.eid == 2
        assert recalled.summary == "two"
    finally:
        store.close()


def test_malformed_complete_line_before_later_valid_rows_keeps_recall_correct(tmp_path):
    base = tmp_path / "deep"
    _write_memories(
        base,
        [
            _record(1, "one"),
            "{not valid json",
            _record(2, "two"),
            _record(3, "three"),
        ],
    )

    store = DeepMemoryStore(base, dim=4)
    try:
        recalled = store.recall(2)
        assert recalled is not None
        assert recalled.eid == 2
        assert recalled.summary == "two"
    finally:
        store.close()


def test_skipped_line_cannot_make_recall_return_wrong_memory_position(tmp_path):
    base = tmp_path / "deep"
    _write_memories(
        base,
        [
            _record(1, "one"),
            "{malformed complete json line",
            _record(2, "two"),
            _record(3, "three"),
        ],
    )

    store = DeepMemoryStore(base, dim=4)
    try:
        recalled = store.recall(2)
        assert recalled is not None
        assert recalled.eid == 2
        assert recalled.summary == "two"
        assert recalled.summary != "three"
    finally:
        store.close()


def test_duplicate_physical_records_contribute_one_query_slot_per_eid(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        anchor = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        near = np.array([0.99, 0.01, 0.0, 0.0], dtype=np.float32)
        _export(store, 5, "eid 5 old", anchor)
        _export(store, 5, "eid 5 middle", anchor)
        _export(store, 5, "eid 5 latest", anchor)
        _export(store, 7, "eid 7", near)

        eids = _query_eids(store, anchor, top_k=2)
        assert eids == [5, 7]
        assert len(eids) == len(set(eids))
    finally:
        store.close()


def test_duplicate_heavy_store_returns_distinct_eids_up_to_top_k(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        anchor = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        for i in range(30):
            _export(store, 5, f"eid 5 duplicate {i}", anchor)
        for eid, vec in [
            (6, [0.99, 0.01, 0.0, 0.0]),
            (7, [0.98, 0.02, 0.0, 0.0]),
            (8, [0.97, 0.03, 0.0, 0.0]),
        ]:
            _export(store, eid, f"eid {eid}", np.array(vec, dtype=np.float32))

        eids = _query_eids(store, anchor, top_k=4)
        assert eids == [5, 6, 7, 8]
        assert len(eids) == 4
        assert len(eids) == len(set(eids))
    finally:
        store.close()


def test_duplicate_eid_query_and_recall_return_latest_canonical_record(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        anchor = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        _export(store, 5, "old canonical", anchor, score=0.1)
        _export(store, 5, "latest canonical", anchor, score=0.9)

        recalled = store.recall(5)
        assert recalled is not None
        assert recalled.summary == "latest canonical"

        hits = store.query(anchor, top_k=1, min_similarity=0.0)
        assert len(hits) == 1
        assert hits[0].eid == 5
        assert hits[0].summary == "latest canonical"
    finally:
        store.close()


def test_latest_record_without_embedding_uses_older_same_eid_embedding(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        old_vec = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
        _export(store, 9, "old vector-bearing record", old_vec)
        _export(store, 9, "latest record without vector", None)

        hits = store.query(old_vec, top_k=1, min_similarity=0.0)
        assert len(hits) == 1
        assert hits[0].eid == 9
        assert hits[0].summary == "latest record without vector"
    finally:
        store.close()


def test_latest_without_embedding_uses_most_recent_older_same_eid_vector(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        vector_a = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        vector_b = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
        _export(store, 31, "revision 1 vector A", vector_a)
        _export(store, 31, "revision 2 vector B", vector_b)
        _export(store, 31, "revision 3 canonical no vector", None)

        b_hits = store.query(vector_b, top_k=1, min_similarity=0.9)
        assert len(b_hits) == 1
        assert b_hits[0].eid == 31
        assert b_hits[0].summary == "revision 3 canonical no vector"

        a_hits = store.query(vector_a, top_k=1, min_similarity=0.9)
        assert a_hits == []
    finally:
        store.close()


def test_latest_usable_embedding_overrides_older_and_missing_revisions(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        vector_a = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        vector_c = np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32)
        _export(store, 32, "revision 1 vector A", vector_a)
        _export(store, 32, "revision 2 no vector", None)
        _export(store, 32, "revision 3 canonical vector C", vector_c)

        c_hits = store.query(vector_c, top_k=1, min_similarity=0.9)
        assert len(c_hits) == 1
        assert c_hits[0].eid == 32
        assert c_hits[0].summary == "revision 3 canonical vector C"

        a_hits = store.query(vector_a, top_k=1, min_similarity=0.9)
        assert a_hits == []
    finally:
        store.close()


def test_normal_distinct_eid_ranking_remains_score_ordered(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        _export(store, 1, "x axis", np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32))
        _export(store, 2, "y axis", np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32))
        _export(store, 3, "mostly x", np.array([0.8, 0.2, 0.0, 0.0], dtype=np.float32))

        eids = _query_eids(
            store,
            np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
            top_k=3,
        )
        assert eids == [2, 3, 1]
    finally:
        store.close()


def test_equal_score_ordering_is_deterministic_and_stable_after_reload(tmp_path):
    base = tmp_path / "deep"
    vector = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    eids = [
        130, 110, 120, 190, 180, 170, 160, 150,
        140, 210, 200, 230, 220, 250, 240, 270,
        260, 290, 280, 310, 300,
    ]
    top_k = 7
    expected = eids[:top_k]
    store = DeepMemoryStore(base, dim=4)
    try:
        for eid in eids:
            _export(store, eid, f"eid {eid}", vector)
        live_order = _query_eids(store, vector, top_k=top_k)
        assert live_order == expected
    finally:
        store.close()

    reloaded = DeepMemoryStore(base, dim=4)
    try:
        reload_order = _query_eids(reloaded, vector, top_k=top_k)
        assert reload_order == expected
        assert reload_order == live_order
    finally:
        reloaded.close()


def test_broken_canonical_embedding_ref_falls_back_to_older_same_eid_vector(tmp_path):
    base = tmp_path / "deep"
    older_vec = np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)
    unrelated_vec = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    first = DeepMemoryStore(base, dim=4)
    try:
        _export(first, 41, "older usable same-eid vector", older_vec)
        _export(first, 42, "unrelated searchable eid", unrelated_vec)
    finally:
        first.close()

    broken_ref = {"shard": 999999, "row": 999999, "dim": 4}
    with (base / "memories.jsonl").open("a", encoding="utf-8") as f:
        f.write(_record(41, "canonical broken embedding ref", broken_ref) + "\n")

    store = DeepMemoryStore(base, dim=4)
    try:
        fallback_hits = store.query(older_vec, top_k=1, min_similarity=0.9)
        assert len(fallback_hits) == 1
        assert fallback_hits[0].eid == 41
        assert fallback_hits[0].summary == "canonical broken embedding ref"

        unrelated_hits = store.query(unrelated_vec, top_k=1, min_similarity=0.9)
        assert len(unrelated_hits) == 1
        assert unrelated_hits[0].eid == 42
        assert unrelated_hits[0].summary == "unrelated searchable eid"
    finally:
        store.close()


def test_eid_with_no_usable_vector_recalls_but_never_queries(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        _export(store, 51, "old no vector", None)
        _export(store, 51, "latest no vector", None)
        searchable_vec = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        _export(store, 52, "searchable vector", searchable_vec)

        recalled = store.recall(51)
        assert recalled is not None
        assert recalled.eid == 51
        assert recalled.summary == "latest no vector"

        eids = _query_eids(store, searchable_vec, top_k=5, min_similarity=0.0)
        assert 51 not in eids
        assert eids == [52]
    finally:
        store.close()


def test_historical_duplicate_laden_store_loads_without_memories_rewrite(tmp_path):
    base = tmp_path / "deep"
    vector = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    store = DeepMemoryStore(base, dim=4)
    try:
        for i in range(10):
            _export(store, 5, f"historical duplicate {i}", vector)
        _export(store, 6, "other eid", np.array([0.99, 0.01, 0.0, 0.0], dtype=np.float32))
    finally:
        store.close()

    memories_path = base / "memories.jsonl"
    before = memories_path.read_bytes()

    reloaded = DeepMemoryStore(base, dim=4)
    try:
        assert _query_eids(reloaded, vector, top_k=2) == [5, 6]
    finally:
        reloaded.close()

    assert memories_path.read_bytes() == before


def test_epoch_valued_historical_record_loads_recalls_and_queries(tmp_path):
    base = tmp_path / "deep"
    vector = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    store = DeepMemoryStore(base, dim=4)
    try:
        _export(store, 77, "historical epoch record", vector, step=77)
    finally:
        store.close()

    memories_path = base / "memories.jsonl"
    historical = json.loads(memories_path.read_text(encoding="utf-8"))
    historical["compressed_step"] = 1_786_463_657
    memories_path.write_text(json.dumps(historical) + "\n", encoding="utf-8")

    reloaded = DeepMemoryStore(base, dim=4)
    try:
        recalled = reloaded.recall(77)
        assert recalled is not None
        assert recalled.compressed_step == 1_786_463_657
        assert isinstance(recalled.compressed_step, int)
        assert _query_eids(reloaded, vector, top_k=1) == [77]
    finally:
        reloaded.close()


def test_stats_count_remains_physical_record_based(tmp_path):
    store = DeepMemoryStore(tmp_path / "deep", dim=4)
    try:
        _export(store, 1, "eid 1 old", None)
        _export(store, 1, "eid 1 latest", None)
        _export(store, 2, "eid 2", None)

        stats = store.stats()
        assert stats["count"] == 3
    finally:
        store.close()
