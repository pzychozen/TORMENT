"""I11 presence and actual public construction, disposable roots / production hash."""
import ast
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys

import pytest

from torment_service.substrate import preselector_root_classification as presence
from torment_service.substrate.deployment_selector import resolve_deployment_agreement
from torment_service.substrate.deployment_types import DeploymentResolutionMode as Mode
from test_b5_a2_deployment_fence import _profile


def snapshot(root):
    if not root.exists():
        return None
    return {p.relative_to(root).as_posix(): (p.is_dir(), p.stat().st_mtime_ns,
            None if p.is_dir() else hashlib.sha256(p.read_bytes()).hexdigest())
            for p in [root, *root.rglob("*")]}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_npy(path, shape, *, dtype="<f4"):
    """Literal fixture bytes, not an embedder; same NPY v1 source format as P3."""
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = repr(dict(descr=dtype, fortran_order=False, shape=shape)).encode("latin1")
    raw += b" " * ((16 - ((10 + len(raw) + 1) % 16)) % 16) + b"\n"
    count = 1
    for n in shape:
        count *= n
    path.write_bytes(b"\x93NUMPY\x01\x00" + struct.pack("<H", len(raw)) + raw + b"\0" * (count * int(dtype[-1])))


def historical_per_eid(root, *, shared=False, eid=7):
    # Preserve the metadata-less Phase 9B fixture grammar verbatim. The shared
    # placement uses the same MemoryGraph owner as Fabric's domain stores.
    workspace = root / "workspaces" / "synthetic-alpha"
    scope = workspace / ("domains" if shared else "agents") / "aria" / ("shared" if shared else "private")
    scope.mkdir(parents=True)
    (scope / "nodes.jsonl").write_text(json.dumps({"eid": eid, "payload": {
        "summary": "canonical summary", "text": "other text"}}) + "\n", encoding="utf-8")
    write_npy(scope / f"emb_{eid}.npy", (3,))
    return scope


def workspace_owner(root, *, minimal=False, domains=None):
    workspace = root / "workspaces" / "workspace"
    metadata = {"workspace_id": "workspace"}
    if not minimal:
        metadata.update(created_ts=1, embed_provider="hash", embed_model="hash:384:torment", embed_dim=384)
    write_json(workspace / "workspace_meta.json", metadata)
    if domains is not None:
        write_json(workspace / "domains.json", {"domains": domains})
    return workspace


def shard_scope(root, *, shared, populated):
    # EmbeddingShardWriter v1, including the no-map/no-nodes empty case seen
    # in the frozen D1 shared scope. No workspace metadata is added to qualify it.
    scope = root / "workspaces" / "workspace" / ("domains" if shared else "agents") / "owner" / ("shared" if shared else "private")
    write_json(scope / "embeddings" / "manifest.json", dict(version=1, embedding_dim=3,
        dtype="float32", rows_per_shard=4096, active_shard=0, next_row=int(populated), total_rows=int(populated)))
    write_npy(scope / "embeddings" / "shard_000000.npy", (4096, 3))
    if populated:
        (scope / "nodes.jsonl").write_text('{"eid":0,"payload":{}}\n', encoding="utf-8")
        (scope / "embeddings" / "shard_000000.map.jsonl").write_text(
            '{"row":0,"eid":0,"memory_class":"core","kind":"episode","step":0,"ts":1}\n', encoding="utf-8")
    return scope


@contextmanager
def read_only_boundary(root):
    observed = []
    enabled = [True]
    def audit(event, args):
        if not enabled[0]:
            return
        if event == "sqlite3.connect":
            pytest.fail("presence/resolution opened SQLite")
        if event == "open":
            _path, mode, flags = args
            if (mode and any(c in mode for c in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                observed.append(event)
                pytest.fail("presence/resolution attempted a write")
        if event in {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink"}:
            observed.append(event)
            pytest.fail("presence/resolution attempted a mutation")
    sys.addaudithook(audit)
    try:
        yield observed
    finally:
        enabled[0] = False


@pytest.mark.parametrize("state", ["absent", "empty", "README.md", ".gitkeep", "substrate", "deployment", "lock", "mixed"])
def test_fresh_is_refused_without_any_effect(tmp_path, state):
    root = tmp_path / "root"
    if state != "absent":
        root.mkdir()
    if state in {"README.md", ".gitkeep", "mixed"}:
        (root / (state if state != "mixed" else "README.md")).write_text("harmless", encoding="utf-8")
    if state in {"substrate", "deployment", "lock", "mixed"}:
        (root / "substrate").mkdir()
    if state in {"deployment", "lock", "mixed"}:
        (root / "substrate" / "deployment").mkdir()
    if state in {"lock", "mixed"}:
        (root / "substrate" / "deployment" / "root-onboarding.lock").touch()
    before = snapshot(root)
    with read_only_boundary(root) as writes:
        assert presence.classify_preselector_root(root) is presence.PreselectorRootClass.FRESH_UNINITIALIZED
        result = resolve_deployment_agreement(data_root=root, effective_profile=_profile())
    assert result.mode is Mode.REFUSED and result.reason == "fresh-root-requires-native-genesis"
    assert not writes and snapshot(root) == before


@pytest.mark.parametrize("family", ["minimal-owner", "modern-owner", "declared-empty-shared", "private-per-eid", "shared-per-eid",
    "empty-private-shard", "empty-shared-shard", "populated-private-shard", "populated-shared-shard"])
def test_supported_historical_presence_is_read_only(tmp_path, family):
    root = tmp_path / "root"
    if "owner" in family:
        workspace_owner(root, minimal=family == "minimal-owner", domains=None if family == "minimal-owner" else ["research"])
    elif family == "declared-empty-shared":
        workspace = workspace_owner(root, domains=["research"])
        (workspace / "domains" / "research" / "shared").mkdir(parents=True)
    elif "per-eid" in family:
        historical_per_eid(root, shared=family.startswith("shared"), eid=0)
    else:
        shard_scope(root, shared="shared" in family, populated=family.startswith("populated"))
    before = snapshot(root)
    with read_only_boundary(root) as writes:
        assert presence.classify_preselector_root(root) is presence.PreselectorRootClass.EXISTING_LEGACY
        result = resolve_deployment_agreement(data_root=root, effective_profile=_profile())
    assert result.mode is Mode.LEGACY_PUBLIC and result.reason == "pre-selector-existing-legacy"
    assert not writes and snapshot(root) == before


@pytest.mark.parametrize("shape", ["random", "workspaces-only", "scope-directory-only", "nodes-only", "wrong-eid", "bad-npy",
    "truncated-npy", "object-npy", "owner-mismatch", "owner-alias", "duplicate-owner", "bad-domains", "manifest-only", "bad-counters", "wrong-shard-dtype"])
def test_ambiguous_or_invalid_evidence_never_supplies_legacy(tmp_path, shape):
    root = tmp_path / "root"
    root.mkdir()
    if shape == "random":
        (root / "unrelated.txt").write_text("not installation evidence", encoding="utf-8")
    elif shape == "workspaces-only":
        (root / "workspaces").mkdir()
    elif shape == "scope-directory-only":
        (root / "workspaces" / "w" / "agents" / "a" / "private").mkdir(parents=True)
    elif shape.startswith("owner") or shape in {"duplicate-owner", "bad-domains"}:
        workspace = workspace_owner(root, domains=[])
        if shape == "duplicate-owner":
            (workspace / "workspace_meta.json").write_text('{"workspace_id":"foreign","workspace_id":"workspace"}', encoding="utf-8")
        elif shape == "bad-domains":
            write_json(workspace / "domains.json", {"domains": "research"})
        else:
            write_json(workspace / "workspace_meta.json", {"workspace_id" if shape == "owner-mismatch" else "workspace": "foreign"})
    elif shape in {"manifest-only", "bad-counters", "wrong-shard-dtype"}:
        scope = shard_scope(root, shared=False, populated=False)
        if shape == "manifest-only":
            (scope / "embeddings" / "shard_000000.npy").unlink()
        elif shape == "bad-counters":
            path = scope / "embeddings" / "manifest.json"
            value = json.loads(path.read_text()); value["total_rows"] = 5; write_json(path, value)
        else:
            write_npy(scope / "embeddings" / "shard_000000.npy", (4096, 3), dtype="<f8")
    else:
        scope = historical_per_eid(root)
        vector = scope / "emb_7.npy"
        if shape == "nodes-only": vector.unlink()
        elif shape == "wrong-eid": vector.rename(scope / "emb_8.npy")
        elif shape == "bad-npy": vector.write_bytes(b"unrelated bytes")
        elif shape == "truncated-npy": vector.write_bytes(vector.read_bytes()[:-1])
        else: vector.write_bytes(vector.read_bytes().replace(b"<f4", b"|O4"))
    before = snapshot(root)
    with read_only_boundary(root):
        assert presence.classify_preselector_root(root) is presence.PreselectorRootClass.AMBIGUOUS_OR_INVALID
        result = resolve_deployment_agreement(data_root=root, effective_profile=_profile())
    assert result.mode is Mode.REFUSED and result.reason == "pre-selector-root-ambiguous-or-invalid"
    assert snapshot(root) == before and str(root) not in result.reason


def test_redirected_workspace_evidence_is_not_followed(tmp_path):
    root, external = tmp_path / "root", tmp_path / "external"
    workspace_owner(external)
    root.mkdir()
    link = root / "workspaces"
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(external / "workspaces")], check=True, capture_output=True)
    else:
        link.symlink_to(external / "workspaces", target_is_directory=True)
    try:
        before = snapshot(external)
        assert presence.classify_preselector_root(root) is presence.PreselectorRootClass.AMBIGUOUS_OR_INVALID
        assert snapshot(external) == before
    finally:
        if os.name == "nt": link.rmdir()
        else: link.unlink()


@pytest.mark.parametrize("state", ["absent", "empty", "ambiguous"])
def test_public_refusal_precedes_fabric_workspace_graph_and_embedder(tmp_path, monkeypatch, state):
    import torment_service.public_runtime as public
    from torment_service.fabric import Workspace
    from torment_service.memory_graph import MemoryGraph
    from torment_service.embeddings import HashEmbedding
    root = tmp_path / "root"
    if state != "absent": root.mkdir()
    if state == "ambiguous": (root / "unrelated").write_text("residue")
    def forbidden(*args, **kwargs): pytest.fail("refused startup constructed a runtime or embedder")
    monkeypatch.setattr(public, "TormentFabric", forbidden)
    for cls in (Workspace, MemoryGraph, HashEmbedding): monkeypatch.setattr(cls, "__init__", forbidden)
    before = snapshot(root)
    with pytest.raises(public.PublicRuntimeStartupRefused, match="pre-selector-root-ambiguous-or-invalid" if state == "ambiguous" else "fresh-root-requires-native-genesis"):
        public.create_public_runtime(root)
    assert snapshot(root) == before


def test_real_legacy_constructor_uses_production_hash_without_modernizing_fixture(tmp_path, monkeypatch):
    import torment_service.public_runtime as public
    from torment_service.fabric import TormentFabric
    from torment_service.embeddings import HashEmbedding
    root = tmp_path / "root"
    historical_per_eid(root)
    before = snapshot(root)
    monkeypatch.setenv("TORMENT_EMBED_PROVIDER", "hash")
    monkeypatch.setenv("TORMENT_HASH_DIM", "384")
    monkeypatch.delenv("TORMENT_EMBED_MODEL", raising=False)
    monkeypatch.delenv("TORMENT_JOB_PERSIST", raising=False)
    counts = {"construct": 0, "embed": 0}
    init, embed = HashEmbedding.__init__, HashEmbedding.embed
    def counted_init(self, *args, **kwargs):
        counts["construct"] += 1
        init(self, *args, **kwargs)
    def counted_embed(self, *args, **kwargs):
        counts["embed"] += 1
        return embed(self, *args, **kwargs)
    monkeypatch.setattr(HashEmbedding, "__init__", counted_init)
    monkeypatch.setattr(HashEmbedding, "embed", counted_embed)
    runtime = public.create_public_runtime(root)
    try:
        assert runtime.mode is public.PublicRuntimeMode.LEGACY and runtime.native_owner is None
        assert type(runtime.cognition_fabric) is TormentFabric
        assert type(runtime.cognition_fabric.embedder) is HashEmbedding
        assert runtime.cognition_fabric.embedder.dim == 384
        assert counts == {"construct": 1, "embed": 0}
        assert runtime.cognition_fabric.workspaces == {} and runtime.cognition_fabric.private_graphs == {}
    finally:
        public.close_public_runtime(root)
    # Normal constructor effects are observed, not prevented. With default
    # job persistence off, this historical fixture remains byte/file identical.
    assert snapshot(root) == before
    assert not list(root.rglob("workspace_meta.json")) and not (root / "substrate").exists()


def test_presence_static_boundary_has_no_runtime_migration_or_mutation_calls():
    tree = ast.parse(Path(presence.__file__).read_text(encoding="utf-8"))
    forbidden = {"TormentFabric", "Workspace", "MemoryGraph", "build_embedder_from_env", "SentenceTransformer",
                 "connect", "mkdir", "makedirs", "write_text", "write_bytes", "unlink", "rename", "replace",
                 "apply", "create", "plant_seed", "qualify_metadata_less_per_eid_legacy_source"}
    calls = {getattr(n.func, "id", getattr(n.func, "attr", "")) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert not calls & forbidden
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any("migration" in name or "fabric" in name or "embedding" in name for name in imports)


@pytest.mark.parametrize("state", ["absent", "empty"])
def test_normal_service_module_refuses_fresh_root_without_materialization(tmp_path, state):
    root = tmp_path / "root"
    if state == "empty": root.mkdir()
    before = snapshot(root)
    env = {key: value for key, value in os.environ.items() if not key.startswith("TORMENT_")}
    # Preserve an optional external audit used by qualification subprocesses.
    for key in ("TORMENT_GENESIS_I3_CHILD_AUDIT",):
        if key in os.environ: env[key] = os.environ[key]
    env.update(TORMENT_DATA_DIR=str(root), TORMENT_EMBED_PROVIDER="hash", TORMENT_HASH_DIM="384",
               HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    result = subprocess.run([sys.executable, "-B", "-X", "utf8", "-m", "torment_service"],
        env=env, text=True, capture_output=True, timeout=45)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "fresh-root-requires-native-genesis" in result.stderr
    assert "Application startup failed" in result.stderr
    assert snapshot(root) == before


@pytest.mark.parametrize("family", ["identity-only", "service-migration"])
def test_updated_legacy_regression_fixtures_supply_existing_owners_without_models(tmp_path, family):
    root = tmp_path / "root"
    if family == "identity-only":
        from test_p9d_i2_public_native_fencing import _existing_legacy_root
        _existing_legacy_root(root)
    else:
        from test_substrate_existing_workspace_multi_scope_admission import _prepare_existing_legacy_workspace
        _prepare_existing_legacy_workspace(root)
        before = snapshot(root)
        _prepare_existing_legacy_workspace(root)
        assert snapshot(root) == before
    before = snapshot(root)
    with read_only_boundary(root):
        assert presence.classify_preselector_root(root) is presence.PreselectorRootClass.EXISTING_LEGACY
        assert resolve_deployment_agreement(data_root=root, effective_profile=_profile()).mode is Mode.LEGACY_PUBLIC
    assert snapshot(root) == before


def test_service_fixture_preparation_never_modernizes_metadata_less_history(tmp_path):
    from test_substrate_existing_workspace_multi_scope_admission import _prepare_existing_legacy_workspace
    root = tmp_path / "root"
    historical_per_eid(root)
    before = snapshot(root)
    with pytest.raises(AssertionError, match="must not modernize"):
        _prepare_existing_legacy_workspace(root)
    assert snapshot(root) == before
