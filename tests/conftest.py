import contextlib
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

# Ensure project root is on sys.path so `import torment_service` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Run-wide disposable default root (I11 completion, part 1 of R1).
#
# torment_service.app binds DATA_DIR from TORMENT_DATA_DIR at import time and
# defaults to <repo>/data (app.py:102-104).  Several REST/MCP tests import the
# application at module import, i.e. during collection.  This conftest module
# executes before any test module in tests/ is imported, so the guard below is
# in force for every such import.  It only redirects the DEFAULT: an explicit,
# non-default TORMENT_DATA_DIR set by the operator/runner is left untouched and
# reported.  No root is seeded here; nothing is reset here.  This is not a
# filesystem sandbox: tests with literal paths or children that ignore the
# environment are not covered by it.
# ---------------------------------------------------------------------------
REPO_DEFAULT_DATA_DIR = (ROOT / "data").resolve()
RUN_GUARD_MARKER_ENV = "TORMENT_TEST_RUN_GUARD_ROOT"
LEGACY_FIXTURE_WORKSPACE_ID = "preexisting"  # the literal I11 used in test_p9d_i2_public_native_fencing


def _is_repo_default(value: str | None) -> bool:
    if not value or not value.strip():
        return True
    try:
        return Path(value).expanduser().resolve() == REPO_DEFAULT_DATA_DIR
    except OSError:
        return False


def _establish_run_guard() -> str:
    current = os.environ.get("TORMENT_DATA_DIR")
    if not _is_repo_default(current):
        return current  # operator/runner-supplied non-default root; respected
    guard = tempfile.mkdtemp(prefix="torment-test-run-guard-")
    os.environ["TORMENT_DATA_DIR"] = guard
    os.environ[RUN_GUARD_MARKER_ENV] = guard
    return guard


RUN_DATA_ROOT = _establish_run_guard()


def pytest_report_header(config):
    kind = "run guard (fresh, unseeded)" if os.environ.get(RUN_GUARD_MARKER_ENV) == RUN_DATA_ROOT else "operator-supplied (non-default)"
    return f"TORMENT_DATA_DIR for this run: {RUN_DATA_ROOT}  [{kind}]"


def safe_run_data_root() -> Path:
    """The run-wide root tests may fall back to.  Never the repository default."""
    current = os.environ.get("TORMENT_DATA_DIR")
    if _is_repo_default(current):
        pytest.fail("safe run environment not established: TORMENT_DATA_DIR is unset or the repository default")
    return Path(current).expanduser().resolve()


# ---------------------------------------------------------------------------
# Existing-legacy-root seed (I11 contract: an existing pre-selector legacy
# installation is recognised by a workspace owner whose workspace_meta.json
# names itself; preselector_root_classification.py:138-152, 238-242).
# Guarded: only an absent or EMPTY directory is accepted; anything else is
# refused rather than overwritten or modernised.
# ---------------------------------------------------------------------------
class LegacyRootSeedRefused(RuntimeError):
    """The target is not a freshly allocated disposable root."""


def existing_legacy_root(root: os.PathLike | str, workspace_id: str = LEGACY_FIXTURE_WORKSPACE_ID) -> Path:
    root = Path(root)
    if root.exists():
        if not root.is_dir():
            raise LegacyRootSeedRefused(f"refusing to seed non-directory {root}")
        if any(root.iterdir()):
            raise LegacyRootSeedRefused(f"refusing to seed non-empty root {root} (existing evidence is never overwritten)")
    if _is_repo_default(str(root)):
        raise LegacyRootSeedRefused("refusing to seed the repository default data directory")
    workspace = root / "workspaces" / workspace_id
    workspace.mkdir(parents=True, exist_ok=False)
    meta = workspace / "workspace_meta.json"
    with meta.open("x", encoding="utf-8") as fh:  # 'x': fail closed if it somehow exists
        json.dump({"workspace_id": workspace_id}, fh)
    return root


def legacy_seed_visible_meta(workspace_id: str = LEGACY_FIXTURE_WORKSPACE_ID) -> dict:
    """What fabric.list_workspaces_meta / GET /workspaces/meta reports for the seed (fabric.py:1314-1340)."""
    return {"workspace_id": workspace_id, "created_ts": 0, "embed_dim": 0, "embed_provider": "", "embed_model": ""}


def ensure_legacy_run_root() -> Path:
    """Seed the run-wide root ONCE for modules that still bind the application at
    import time (the former repo-default consumers).  Idempotent for our own seed,
    refused for anything else."""
    root = safe_run_data_root()
    meta = root / "workspaces" / LEGACY_FIXTURE_WORKSPACE_ID / "workspace_meta.json"
    if meta.exists():
        if json.loads(meta.read_text(encoding="utf-8")) != {"workspace_id": LEGACY_FIXTURE_WORKSPACE_ID}:
            raise LegacyRootSeedRefused(f"run root {root} holds a foreign owner; refusing")
        return root
    if root.exists() and any(root.iterdir()):
        raise LegacyRootSeedRefused(f"run root {root} is not empty and not our seed; refusing")
    return existing_legacy_root(root)


# ---------------------------------------------------------------------------
# Legacy-compatibility application fixture (part 2 of R1).
# Order of operations is the contract GPT required:
#   bind env -> import -> reload -> client, every step inside try/finally;
#   teardown: close ONLY this root's runtime, restore the previous env, and
#   rebind the module only to a known-safe non-default root (never the repo
#   default).  The fixture refuses to start if the run guard is absent.
# ---------------------------------------------------------------------------
@pytest.fixture()
def legacy_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=False)
    return existing_legacy_root(data_dir)


@contextlib.contextmanager
def bound_legacy_app(data_dir: Path):
    """Context manager form so unittest-style modules can use it too."""
    safe_previous = safe_run_data_root()           # refuse before touching anything
    data_dir = Path(data_dir)
    if _is_repo_default(str(data_dir)):
        pytest.fail("bound_legacy_app refuses the repository default data directory")
    if data_dir.resolve() == safe_previous:
        pytest.fail("bound_legacy_app refuses the shared run root (module-import consumers own it); use a disposable root")
    previous_env = os.environ.get("TORMENT_DATA_DIR")
    appmod = None
    os.environ["TORMENT_DATA_DIR"] = str(data_dir)
    try:
        appmod = importlib.import_module("torment_service.app")
        appmod = importlib.reload(appmod)          # rebind DATA_DIR + proxy to the disposable root
        from fastapi.testclient import TestClient
        with TestClient(appmod.app) as client:
            yield SimpleNamespace(app=appmod, client=client, data_dir=data_dir)
    finally:
        try:
            from torment_service.public_runtime import reset_public_runtime_for_test
            reset_public_runtime_for_test(data_dir)    # only this root's cache entry
        finally:
            if previous_env is None:
                os.environ.pop("TORMENT_DATA_DIR", None)
            else:
                os.environ["TORMENT_DATA_DIR"] = previous_env
            if appmod is not None and not _is_repo_default(os.environ.get("TORMENT_DATA_DIR")):
                importlib.reload(appmod)               # rebind to the safe run root, never the repo default
            # else: leave the module bound to the (closed) disposable root rather than the real default


@pytest.fixture()
def legacy_app(legacy_data_dir: Path):
    with bound_legacy_app(legacy_data_dir) as bound:
        yield bound


def assert_legacy_mode(appmod) -> None:
    from torment_service.public_runtime import PublicRuntimeMode
    runtime = appmod.fabric.runtime()
    assert runtime.mode is PublicRuntimeMode.LEGACY, runtime.mode
    assert runtime.native_owner is None


class LegacyRuntimeProxyForTest:
    """Narrow substitute for app._AppRuntimeProxy in handler/unit tests that
    construct their own TormentFabric and inject it into torment_service.app.
    It exposes the same two methods the application calls (runtime(), close())
    over the injected fabric, reporting LEGACY mode honestly.  It does NOT run
    the deployment resolver and therefore demonstrates nothing about startup
    or selector validation; use bound_legacy_app for that."""

    def __init__(self, fabric):
        from torment_service.public_runtime import PublicRuntimeMode, PublicTormentRuntime
        self._fabric = fabric
        self._runtime = PublicTormentRuntime(mode=PublicRuntimeMode.LEGACY, cognition_fabric=fabric)

    def runtime(self):
        return self._runtime

    def close(self) -> None:
        self._fabric.close()

    def __getattr__(self, name: str):
        return getattr(self._fabric, name)
