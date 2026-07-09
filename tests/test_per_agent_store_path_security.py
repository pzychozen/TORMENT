"""Defense-in-depth path-containment regression tests for the per-agent
JSON stores hardened in this slice:

  - IdentityStore        (identity.py)
  - CharacterStore       (character.py)
  - RoleStore            (roles.py)
  - ReingestTracker      (collective_policy.py)

Each store now validates its dynamic path components via centralized pathing
builders and contains the resolved path beneath base_dir, instead of relying
only on upstream caller validation. These tests assert: valid identifiers work
unchanged, traversal / separator / absolute forms fail closed with ValueError,
and resolved paths remain beneath base_dir.

Scope: path-integrity only. No behavior/persistence-format assertions beyond a
single normal save/load round-trip per store where cheap.
"""
from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from torment_service.identity import IdentityStore
from torment_service.character import CharacterStore
from torment_service.roles import RoleStore
from torment_service.collective_policy import ReingestTracker


@pytest.fixture
def base_dir():
    d = tempfile.mkdtemp(prefix="torment_store_sec_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


_BAD_COMPONENTS = [
    "../evil",        # traversal
    "..\\evil",       # Windows traversal
    "..",             # parent
    "a/b",            # forward slash component
    "a\\b",           # backslash component
    "/etc/passwd",    # absolute / leading slash
    "C:\\escape",     # Windows absolute path
]


# -------------------------------------------------------------------
# IdentityStore
# -------------------------------------------------------------------
class TestIdentityStorePaths:
    def test_valid_roundtrip(self, base_dir):
        store = IdentityStore(base_dir)
        ident = store.create("ws1", "a1")
        store.save(ident)
        loaded = store.load("ws1", "a1")
        assert loaded is not None
        assert loaded.agent_id == "a1"
        assert store._path("ws1", "a1").startswith(os.path.realpath(base_dir))

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_workspace_rejected(self, base_dir, bad):
        store = IdentityStore(base_dir)
        with pytest.raises(ValueError):
            store.load(bad, "a1")

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_agent_rejected(self, base_dir, bad):
        store = IdentityStore(base_dir)
        with pytest.raises(ValueError):
            store.load("ws1", bad)


# -------------------------------------------------------------------
# CharacterStore
# -------------------------------------------------------------------
class TestCharacterStorePaths:
    def test_valid_seed_and_state_paths(self, base_dir):
        store = CharacterStore(base_dir)
        # Valid ids: missing files return None (path-builder still validates).
        assert store.load_seed("ws1", "s1") is None
        assert store.load_state("ws1", "a1") is None
        assert store._seed_path("ws1", "s1").startswith(os.path.realpath(base_dir))
        assert store._state_path("ws1", "a1").startswith(os.path.realpath(base_dir))

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_seed_components_rejected(self, base_dir, bad):
        store = CharacterStore(base_dir)
        with pytest.raises(ValueError):
            store.load_seed(bad, "s1")
        with pytest.raises(ValueError):
            store.load_seed("ws1", bad)

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_state_components_rejected(self, base_dir, bad):
        store = CharacterStore(base_dir)
        with pytest.raises(ValueError):
            store.load_state(bad, "a1")
        with pytest.raises(ValueError):
            store.load_state("ws1", bad)


# -------------------------------------------------------------------
# RoleStore
# -------------------------------------------------------------------
class TestRoleStorePaths:
    def test_valid_roundtrip(self, base_dir):
        store = RoleStore(base_dir)
        rp = store.load("ws1", "a1")  # creates + saves on first load
        assert rp.agent_id == "a1"
        assert store._path("ws1", "a1").startswith(os.path.realpath(base_dir))

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_components_rejected(self, base_dir, bad):
        store = RoleStore(base_dir)
        with pytest.raises(ValueError):
            store.load(bad, "a1")
        with pytest.raises(ValueError):
            store.load("ws1", bad)


# -------------------------------------------------------------------
# ReingestTracker
# -------------------------------------------------------------------
class TestReingestTrackerPaths:
    def test_valid_construction(self, base_dir):
        tracker = ReingestTracker(base_dir, "ws1")
        assert tracker._base.startswith(os.path.realpath(base_dir))
        assert tracker._log_path.startswith(os.path.realpath(base_dir))
        assert os.path.isdir(tracker._base)

    @pytest.mark.parametrize("bad", _BAD_COMPONENTS)
    def test_bad_workspace_rejected(self, base_dir, bad):
        with pytest.raises(ValueError):
            ReingestTracker(base_dir, bad)
