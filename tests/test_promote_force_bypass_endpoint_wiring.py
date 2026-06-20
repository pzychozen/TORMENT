"""tests/test_promote_force_bypass_endpoint_wiring.py

POST /promote FORCE-BYPASS ENDPOINT-WIRING CHARACTERIZATION (test-only).

Seam-3 slice (test-only, RESHAPE per Codex: endpoint *wiring* only).
This pack pins how the live ``POST /promote`` handler wires ``force=True``
into the promotion evaluation and execution path. It makes **no
production change** and proposes no fix.

This characterizes the CURRENT endpoint call path. It is NOT a statement
of desired/required runtime behavior, auth doctrine, or promotion policy.
If a later, separately-authorized slice adds an upstream authorization or
governed crossing to this endpoint, these assertions are expected to
change deliberately — that is the signal, not a surprise.

The writer row shape produced by ``promote_chunk`` is already pinned by
tests/test_checkpoint_promotion.py and is deliberately NOT re-asserted
here — ``promote_chunk`` is replaced by a sentinel so the test proves
endpoint reachability without touching the emitted row.

What it pins (endpoint wiring only):
  * a bland low-signal chunk does NOT promote under ``force=False``
    (``evaluation.promote`` False, ``promoted_eid`` None);
  * with ``force=True`` the handler passes ``is_canon=True`` AND
    ``user_approved=True`` into ``evaluate_promotion``, and reaches
    ``promote_chunk`` (sentinel eid returned);
  * the ``result.promote or req.force`` branch: even when evaluation is
    stubbed to decline (``promote=False``), ``force=True`` still reaches
    ``promote_chunk``.

Current request-surface note (characterization only, not doctrine):
  the endpoint currently accepts a normal TestClient request carrying
  ``force=True``; the test passes no extra approval/governance object.
  No claim is made about the presence or absence of any auth middleware
  or security control beyond this single call path.
"""
from __future__ import annotations

import importlib
import os

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Isolated app fixture (mirrors tests/test_smoke_api.py: manual env
# save/restore + module reload so DATA_DIR + module-level fabric bind to a
# temp dir, then revert after the test).
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    original_env = os.environ.get("TORMENT_DATA_DIR")
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)

    import torment_service.app as appmod
    appmod = importlib.reload(appmod)
    try:
        yield TestClient(appmod.app)
    finally:
        if original_env is None:
            os.environ.pop("TORMENT_DATA_DIR", None)
        else:
            os.environ["TORMENT_DATA_DIR"] = original_env
        importlib.reload(appmod)


_DOC_ID = "doc_bland"
_CHUNK_ID = f"{_DOC_ID}_chunk_0000"  # archive_memory: f"{doc_id}_chunk_{i:04d}"
_BLAND_TEXT = (
    "The afternoon weather report noted mild temperatures with a light "
    "breeze and a small chance of scattered clouds toward the evening."
)


def _setup_ws_agent_and_chunk(client: TestClient) -> None:
    """Create ws + agent and ingest one bland low-signal archive chunk."""
    r = client.post("/workspace/create", json={"workspace_id": "ws"})
    assert r.status_code == 200, r.text
    r = client.post("/agent/create", json={"workspace_id": "ws", "agent_id": "a1"})
    assert r.status_code == 200, r.text
    r = client.post(
        "/archive/ingest_document",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "text": _BLAND_TEXT,
            "title": "Bland",
            "doc_id": _DOC_ID,
        },
    )
    assert r.status_code == 200, r.text
    assert int(r.json().get("chunk_count", 0)) >= 1


def _promote(client: TestClient, force: bool):
    return client.post(
        "/promote",
        json={
            "workspace_id": "ws",
            "agent_id": "a1",
            "chunk_id": _CHUNK_ID,
            "force": force,
        },
    )


# ===========================================================================
# 1. force=False on a low-signal chunk does not promote (baseline)
# ===========================================================================


def test_promote_force_false_low_signal_chunk_does_not_promote(client: TestClient):
    _setup_ws_agent_and_chunk(client)

    r = _promote(client, force=False)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["evaluation"]["promote"] is False
    assert body["promoted_eid"] is None


# ===========================================================================
# 2. force=True maps is_canon + user_approved and reaches promote_chunk
# ===========================================================================


def test_promote_force_true_maps_is_canon_and_user_approved_and_reaches_promote_chunk(
    client: TestClient, monkeypatch
):
    _setup_ws_agent_and_chunk(client)

    import torment_service.promotion as promo

    captured = {}
    real_eval = promo.evaluate_promotion

    def _spy_eval(*args, **kwargs):
        captured["is_canon"] = kwargs.get("is_canon")
        captured["user_approved"] = kwargs.get("user_approved")
        res = real_eval(*args, **kwargs)
        captured["eval_promote"] = bool(res.promote)
        return res

    sentinel = {"called": False, "extra_payload": None}

    def _sentinel_promote(*args, **kwargs):
        sentinel["called"] = True
        sentinel["extra_payload"] = kwargs.get("extra_payload")
        return 424242

    # Patch at the source module — the endpoint imports these names
    # function-locally from torment_service.promotion at call time.
    monkeypatch.setattr(promo, "evaluate_promotion", _spy_eval)
    monkeypatch.setattr(promo, "promote_chunk", _sentinel_promote)

    # A normal request carrying force=True; no approval/governance object passed.
    r = _promote(client, force=True)
    assert r.status_code == 200, r.text
    body = r.json()

    # Endpoint reached promote_chunk (sentinel eid), proving reachability
    # without re-asserting the writer row shape.
    assert sentinel["called"] is True
    assert body["promoted_eid"] == 424242

    # force=True is wired into BOTH evaluation inputs.
    assert captured["is_canon"] is True
    assert captured["user_approved"] is True

    # H3 provenance: the force route is recorded in the written extra_payload,
    # and the evaluator's own decision is recorded alongside it.
    ep = sentinel["extra_payload"]
    assert ep is not None
    assert ep["promotion_force_requested"] is True
    assert ep["promotion_evaluator_promote"] == captured["eval_promote"]


# ===========================================================================
# 3. result.promote or req.force — force executes even when eval declines
# ===========================================================================


def test_promote_force_true_executes_even_when_evaluation_declines(
    client: TestClient, monkeypatch
):
    _setup_ws_agent_and_chunk(client)

    import torment_service.promotion as promo

    def _declining_eval(*args, **kwargs):
        return promo.PromotionResult(
            promote=False, score=0.0, reason="patched-decline", criteria={}
        )

    sentinel = {"called": False, "extra_payload": None}

    def _sentinel_promote(*args, **kwargs):
        sentinel["called"] = True
        sentinel["extra_payload"] = kwargs.get("extra_payload")
        return 525252

    monkeypatch.setattr(promo, "evaluate_promotion", _declining_eval)
    monkeypatch.setattr(promo, "promote_chunk", _sentinel_promote)

    r = _promote(client, force=True)
    assert r.status_code == 200, r.text
    body = r.json()

    # Evaluation declined, yet force alone reached promote_chunk:
    # pins the current `result.promote or req.force` execution branch.
    assert body["evaluation"]["promote"] is False
    assert sentinel["called"] is True
    assert body["promoted_eid"] == 525252

    # H3 provenance: a true force-bypass (force requested, evaluator declined)
    # is recorded distinctly in the written extra_payload.
    ep = sentinel["extra_payload"]
    assert ep is not None
    assert ep["promotion_force_requested"] is True
    assert ep["promotion_evaluator_promote"] is False


# ===========================================================================
# 4. evaluator-approved, non-force promotion records provenance distinctly
# ===========================================================================


def test_promote_evaluator_approved_non_force_records_provenance(
    client: TestClient, monkeypatch
):
    _setup_ws_agent_and_chunk(client)

    import torment_service.promotion as promo

    def _approving_eval(*args, **kwargs):
        return promo.PromotionResult(
            promote=True, score=1.0, reason="patched-approve", criteria={}
        )

    sentinel = {"called": False, "extra_payload": None}

    def _sentinel_promote(*args, **kwargs):
        sentinel["called"] = True
        sentinel["extra_payload"] = kwargs.get("extra_payload")
        return 626262

    monkeypatch.setattr(promo, "evaluate_promotion", _approving_eval)
    monkeypatch.setattr(promo, "promote_chunk", _sentinel_promote)

    # Non-force request; evaluator approves on its own.
    r = _promote(client, force=False)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["evaluation"]["promote"] is True
    assert sentinel["called"] is True
    assert body["promoted_eid"] == 626262

    # H3 provenance: evaluator-approved, non-force route recorded distinctly.
    ep = sentinel["extra_payload"]
    assert ep is not None
    assert ep["promotion_force_requested"] is False
    assert ep["promotion_evaluator_promote"] is True
