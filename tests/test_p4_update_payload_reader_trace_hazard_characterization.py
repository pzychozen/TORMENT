"""Tests-only characterization: the `MemoryGraph.update_payload` canonical-last
reader-trace hazard (P4 O1/O2/O5 source-sameness terrain).

Pins — but does NOT solve — the concrete hazard the P4 source-sameness policy
frame (`docs/TORMENT_P4_SOURCE_SAMENESS_POLICY_FRAME_v0.1.md`) names:
``update_payload`` mutates the payload behind an EXISTING ``eid`` and re-appends
a ``nodes.jsonl`` record; the loader treats the LAST record per eid as canonical.
So the content behind an ``eid`` is a moving target, and nothing on the update
path records source lineage / revision / a source token — a later P4 reader-trace
/ source-sameness policy would have to govern this, but no such mechanism exists.

Two complementary lenses (mirrors the existing P4 readiness/O3-O4 characterization
style): a source/AST lens (no production import/exec) and a minimal temp-file
behavioral lens (importorskip-guarded, temp fixtures only). This file characterizes
the hazard as **P4 reader-trace / future-policy terrain** — it is **not** a bug fix
and introduces **no** mechanism.

Out of scope / NOT introduced here: any `ReaderPolicy`, source-sameness runtime
gate, `diagnostic_only` behavior, projection-eligibility change, source revision /
token / lineage / fingerprint / carrier / comparison mechanism, candidate store /
schema / substrate / admission / promotion, Dream / Gate D / Document B chamber /
Envelope-Audit runtime, AgentRunner / app / spine / MCP wiring, model/provider path,
or any production behavior change.
"""

import ast
import json
import os
import shutil
import tempfile

import pytest


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path):
    with open(path, "rb") as fh:
        return fh.read().replace(b"\x00", b"").decode("utf-8-sig")


def _mg_src():
    return _read(os.path.join(_repo_root(), "torment_service", "memory_graph.py"))


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _seg(text, node):
    return ast.get_source_segment(text, node) or ""


# Reader-trace / source-sameness lineage markers a later P4 policy MIGHT add.
# None of these should exist on the current update path. Matched as substrings,
# case-insensitive, against the function source segment.
_HAZARD_TOKENS = (
    "source_sameness",
    "source_membership",
    "readerpolicy",
    "diagnostic_only",
    "source_fingerprint",
    "fingerprint",
    "source_token",
    "source_revision",
    "revision_id",
    "lineage",
    "reader_trace",
    "carrier",
)


def _hazard_hits(text):
    low = text.lower()
    return sorted({tok for tok in _HAZARD_TOKENS if tok in low})


# --------------------------------------------------------------------------- #
# 1. Source/AST: same-eid mutation + reappend, canonical-last, no lineage marker
# --------------------------------------------------------------------------- #

class _MgTree:
    _cache = None

    @classmethod
    def get(cls):
        if cls._cache is None:
            src = _mg_src()
            cls._cache = (src, ast.parse(src))
        return cls._cache


def test_update_payload_updates_existing_eid_in_place():
    src, tree = _MgTree.get()
    fn = _find_func(tree, "update_payload")
    assert fn is not None, "update_payload not found in memory_graph.py"
    body = _seg(src, fn)
    # Requires the eid to already exist (no new source identity is allocated) ...
    assert "if eid not in self.entities" in body
    assert "raise KeyError" in body
    # ... and mutates that same eid's payload in place.
    assert ("ent.payload.update" in body) or ("ent.payload = dict(patch)" in body)


def test_update_payload_reappends_node_record_not_new_source():
    src, tree = _MgTree.get()
    body = _seg(src, _find_func(tree, "update_payload"))
    # Appends a nodes.jsonl (meta_path) record for the SAME eid ...
    assert "_append_jsonl" in body
    assert "self.meta_path" in body
    assert '"eid": int(ent.eid)' in body
    # ... and does NOT allocate a new eid or construct a new SeedEntity.
    assert "SeedEntity(" not in body
    assert "spawn_memory" not in body
    assert "_next_eid" not in body


def test_loader_treats_last_record_per_eid_as_canonical():
    # Source-ground the existing canonical-last loader behavior (O5 terrain).
    src, tree = _MgTree.get()
    load = _seg(src, _find_func(tree, "_load"))
    assert "LAST record per EID as canonical" in load
    assert "last record wins" in load


def test_update_path_has_no_reader_trace_or_source_sameness_marker():
    # The hazard: no lineage / revision / source-token / ReaderPolicy /
    # diagnostic_only / carrier marker is attached on the update path today.
    src, tree = _MgTree.get()
    body = _seg(src, _find_func(tree, "update_payload"))
    hits = _hazard_hits(body)
    assert hits == [], f"update_payload already carries reader-trace/source-sameness markers: {hits}"


# --------------------------------------------------------------------------- #
# 2. Minimal temp-file behavioral characterization (importorskip-guarded)
# --------------------------------------------------------------------------- #

def _eid_records(meta_path, eid):
    if not os.path.exists(meta_path):
        return []
    out = []
    with open(meta_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            try:
                if int(obj.get("eid")) == int(eid):
                    out.append(obj)
            except (TypeError, ValueError):
                continue
    return out


def test_update_payload_reappend_is_same_eid_and_canonical_last():
    memory_graph = pytest.importorskip("torment_service.memory_graph")
    embeddings = pytest.importorskip("torment_service.embeddings")
    np = pytest.importorskip("numpy")
    MemoryGraph = memory_graph.MemoryGraph
    HashEmbedding = embeddings.HashEmbedding

    tmpdir = tempfile.mkdtemp(prefix="p4_update_payload_hazard_")
    try:
        embedder = HashEmbedding(dim=8)
        g = MemoryGraph(tmpdir, embedder=embedder)
        eid = g.spawn_memory(
            summary="v1",
            embedding=np.zeros(embedder.dim, dtype=np.float32),
            mtype="episode",
            strength=0.5, confidence=0.5, half_life_days=30.0,
            user_id="default", step=0,
        )
        eids_before = set(g.entities)
        before = len(_eid_records(g.meta_path, eid))

        # Two same-eid payload updates → two reappended records for that eid.
        g.update_payload(eid, {"note": "v2"})
        g.update_payload(eid, {"note": "v3"})

        after_recs = _eid_records(g.meta_path, eid)

        # (a) same eid, still present; no NEW eid created by the update path.
        assert eid in g.entities
        assert set(g.entities) == eids_before
        # (b) reappend, not new source: two more records for the SAME eid.
        assert len(after_recs) - before == 2
        assert all(int(r.get("eid")) == int(eid) for r in after_recs)

        # (c) canonical-last: a fresh reload resolves the eid to the LAST payload.
        g2 = MemoryGraph(tmpdir, embedder=HashEmbedding(dim=8))
        assert int(eid) in g2.entities
        assert (g2.entities[int(eid)].payload or {}).get("note") == "v3"

        # (d) reader-trace hazard: no appended record carries a source
        # revision / token / lineage marker distinguishing which record a prior
        # reference pointed at — nothing to trace source-sameness by.
        lineage_keys = {
            "source_revision", "revision_id", "source_token", "lineage",
            "source_fingerprint", "reader_trace", "source_sameness",
        }
        for r in after_recs:
            keys = set(r.keys()) | set((r.get("payload") or {}).keys())
            leaked = keys & lineage_keys
            assert leaked == set(), f"unexpected lineage marker on record: {leaked}"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 3. Teeth — the hazard-marker detector catches a synthetic lineage update path
# --------------------------------------------------------------------------- #

def test_matcher_flags_synthetic_reader_trace_update_path():
    synthetic = (
        "def update_payload(self, eid, patch):\n"
        "    ent = self.entities[eid]\n"
        "    ent.payload.update(patch)\n"
        "    ent.payload['source_revision'] = self._next_revision_id()\n"
        "    ReaderPolicy().record_lineage(eid, source_token=make_fingerprint(ent))\n"
    )
    hits = _hazard_hits(synthetic)
    assert "source_revision" in hits
    assert "lineage" in hits
    assert "source_token" in hits
    assert "fingerprint" in hits
    assert "readerpolicy" in hits


def test_current_same_eid_reappend_shape_is_not_flagged():
    # The real update_payload shape (mutate same eid + append node record) carries
    # none of the markers — proving the absence assertions above are meaningful.
    benign = (
        "def update_payload(self, eid, patch):\n"
        "    if eid not in self.entities:\n"
        "        raise KeyError(eid)\n"
        "    ent = self.entities[eid]\n"
        "    ent.payload.update(dict(patch))\n"
        "    self._append_jsonl(self.meta_path, {'eid': int(ent.eid), 'payload': ent.payload})\n"
    )
    assert _hazard_hits(benign) == []


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
