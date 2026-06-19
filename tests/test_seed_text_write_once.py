"""tests/test_seed_text_write_once.py

Authored seed-content stability lock (tests-only characterization).

Locks the CURRENT invariant that ordinary runtime creation/planting and
ordinary ingest do NOT rewrite *authored* seed content. Only the authored
fields are locked:

    * seed_text
    * seed_id
    * character_name (authored display label)

This is deliberately NOT a "seed never changes" claim. Planting legitimately
populates derived basin fields (``seed_motif_id``, ``seed_eids``, and
``created_ts``); the positive control below asserts those CAN populate,
proving the lock is on authored content, not on object identity.

It is also NOT a seed-revision API or an overwrite API. The repeat-create
test characterizes the CURRENT idempotent-create behavior: a second
``create_agent`` for the same workspace/agent with a different seed payload
does not rewrite the already-persisted authored seed, because
``create_agent`` skips identity creation when the agent already exists, so
the second payload is ignored. That is a characterization of today's
behavior, not a sanctioned revision path.

Seam: direct temp-data ``TormentFabric.create_agent`` — the real plant/save
path (fabric.py:2122-2152), with no endpoint noise. ``get_workspace`` with no
explicit domains always initializes a single-agent default domain (with a
motif registry), so the plant/save path runs; if it ever did not, ``load_seed``
would return None and these tests fail loudly rather than silently passing.

Anchors:
  * docs/TORMENT_SEED_GOVERNANCE_BLUEPRINT_v0.1.md §7 — authored seed revision
    is a separate governed boundary; never a side effect of ingest /
    reflection / drift / automatic correction.
  * docs/TORMENT_A_B_SEED_GOV_IDENTITY_SEED_CANON_CANDIDATE_CROSSING_RECONCILIATION_FRAME_v0.1.md
    — actual authored seed revision is separate from ordinary admission.

Tests only. No production code. If a real seed-mutating runtime path is ever
discovered, that is a hazard finding — not a reason to relax these tests.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


AUTHORED_SEED_ID = "seed_stability_v1"
AUTHORED_NAME = "Stability Lock Character"
AUTHORED_TEXT = (
    "A steady witness who keeps her shape across sessions. "
    "She values clarity and remembers who she is. "
    "Her voice is calm and unhurried."
)


def _make_fabric(prefix: str = "torment_seed_write_once_"):
    """Fresh in-memory fabric with workspace 'test-ws'. Returns (fabric,
    data_dir). No agent is created yet — each test creates its own with an
    authored seed."""
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    fabric = TormentFabric(data_dir=tmpdir)
    fabric.get_workspace("test-ws")
    return fabric, tmpdir


def _authored_seed(
    seed_id: str = AUTHORED_SEED_ID,
    name: str = AUTHORED_NAME,
    text: str = AUTHORED_TEXT,
) -> dict:
    return {"seed_id": seed_id, "character_name": name, "seed_text": text}


def _ordinary_ingest(fabric, agent_id: str = "agent-1") -> None:
    """One ordinary private ingest, mirroring the known-good pattern in
    tests/test_authority_lane_matrix.py. No query is issued: query would add
    unrelated retrieval / warmup behavior, and is not part of this contract."""
    fabric.ingest(
        workspace_id="test-ws",
        agent_id=agent_id,
        text="A short ordinary note about today's weather.",
        step=1,
        scope="private",
        domain_id="personal",
    )


def test_authored_seed_content_persists_through_create_and_ingest():
    fabric, _ = _make_fabric()

    # (1) Create an agent with an authored seed (real plant/save path).
    fabric.create_agent("test-ws", "agent-1", seed=_authored_seed())

    loaded = fabric.character_store.load_seed("test-ws", AUTHORED_SEED_ID)
    assert loaded is not None, (
        "create_agent did not persist the CharacterSeed; the plant/save path "
        "(fabric.py:2122-2152) did not run, so the authored-content lock cannot "
        "be evaluated"
    )

    # (2) Authored fields match the authored input right after create/plant.
    assert loaded.seed_text == AUTHORED_TEXT
    assert loaded.seed_id == AUTHORED_SEED_ID
    assert loaded.character_name == AUTHORED_NAME

    # (3) Positive control: derived basin fields populated by planting. This
    # proves the lock is on authored content, not on object identity.
    # plant_seed returns the seed with seed_motif_id and seed_eids populated.
    assert loaded.seed_eids, "planting did not populate derived seed_eids"
    assert loaded.seed_motif_id != "", (
        "planting did not populate derived seed_motif_id"
    )

    # (4) Ordinary activity after creation.
    _ordinary_ingest(fabric, "agent-1")

    # (5) Reload — authored fields still match after ordinary activity.
    reloaded = fabric.character_store.load_seed("test-ws", AUTHORED_SEED_ID)
    assert reloaded is not None
    assert reloaded.seed_text == AUTHORED_TEXT
    assert reloaded.seed_id == AUTHORED_SEED_ID

    # (6) character_name unchanged. Recorded as the authored display label;
    # NOT elevated to seed-revision doctrine.
    assert reloaded.character_name == AUTHORED_NAME


def test_repeat_create_agent_does_not_overwrite_authored_seed():
    """Current idempotent-create characterization (NOT a seed-revision or
    overwrite mechanism). A second create_agent for the same workspace/agent
    with a DIFFERENT seed payload does not rewrite the already-persisted
    authored seed: create_agent skips identity creation when the agent already
    exists, so the second payload is ignored."""
    fabric, _ = _make_fabric()

    fabric.create_agent("test-ws", "agent-1", seed=_authored_seed())
    before = fabric.character_store.load_seed("test-ws", AUTHORED_SEED_ID)
    assert before is not None and before.seed_text == AUTHORED_TEXT

    # (7) Repeat create for the same agent with a DIFFERENT seed payload.
    fabric.create_agent(
        "test-ws",
        "agent-1",
        seed=_authored_seed(
            seed_id="seed_stability_v2",
            name="Rewritten Name",
            text="An entirely different authored narrative that must NOT win.",
        ),
    )

    # (8) The original persisted authored seed is unchanged...
    after = fabric.character_store.load_seed("test-ws", AUTHORED_SEED_ID)
    assert after is not None
    assert after.seed_text == AUTHORED_TEXT
    assert after.seed_id == AUTHORED_SEED_ID
    assert after.character_name == AUTHORED_NAME

    # ...and the different payload created NO new persisted seed (the
    # idempotent create ignored it; there is no ordinary seed-revision path).
    assert (
        fabric.character_store.load_seed("test-ws", "seed_stability_v2") is None
    ), (
        "a second create_agent with a different seed payload persisted a new "
        "seed; that would be an unsanctioned ordinary-path seed write"
    )
