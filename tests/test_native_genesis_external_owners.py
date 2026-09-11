"""I2 owner-level tests on disposable files; no Fabric, models, or SQLite."""

import __future__
import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from torment_service import atomic_publication as atomic
from torment_service import character as character_module
from torment_service import identity as identity_module
from torment_service import workspace_declaration as workspace
from torment_service.character import CharacterSeed, CharacterStore
from torment_service.external_owner_json import ExternalOwnerConflict, exact_json, owner_bytes, strict_object
from torment_service.identity import AgentIdentity, IdentityStore
from torment_service.substrate.character_seed_witness import character_seed_definition_digest
from torment_service.substrate.genesis_contracts import GenesisIntent
from test_native_genesis_contracts import intent_payload


def facts(enabled=True):
    return GenesisIntent.from_payload(intent_payload(enabled)).payload()


def declaration():
    value = facts()
    return workspace.WorkspaceDeclaration(
        value["workspace"]["workspace_id"], value["creation_facts"]["workspace_created_ts"],
        value["profile_choice"]["representation_dimension"], value["profile_choice"]["representation_provider"],
        value["profile_choice"]["representation_model"], tuple(value["workspace"]["ordered_domains"]),
    )


def expected_identity():
    value = facts()
    return AgentIdentity(value["workspace"]["workspace_id"], value["agent"]["agent_id"],
                         value["agent"]["identity_seed"], value["agent"]["initial_overlay"],
                         value["creation_facts"]["identity_created_ts"], value["creation_facts"]["identity_created_ts"])


def seed_definition():
    return facts()["character"]["definition"]


def create_seed(store):
    return store.create_or_verify_seed_definition("workspace", seed_definition(), created_ts=12)


def finalize_seed(store, eids=(11, 12), motif="native-seed-motif"):
    return store.finalize_or_verify_seed_linkage("workspace", seed_definition(), created_ts=12,
                                                seed_eids=eids, seed_motif_id=motif)


def snapshot(path):
    return Path(path).read_bytes(), Path(path).stat().st_mtime_ns


def fail(*args, **kwargs):
    raise OSError("simulated interrupted publication")


def test_atomic_create_never_overwrites_and_cleans_private_temps(tmp_path):
    path = tmp_path / "owner.json"
    assert atomic.publish_if_absent(path, b"complete") is atomic.PublicationResult.CREATED
    before = snapshot(path)
    assert atomic.publish_if_absent(path, b"complete") is atomic.PublicationResult.ALREADY_EXISTS
    assert atomic.publish_if_absent(path, b"conflict") is atomic.PublicationResult.ALREADY_EXISTS
    assert snapshot(path) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["owner.json"]


@pytest.mark.parametrize("fault", ["before-publication", "after-publication"])
def test_atomic_create_interruption_leaves_absent_or_complete_target(tmp_path, monkeypatch, fault):
    path = tmp_path / "owner.json"
    with monkeypatch.context() as patch:
        patch.setattr(atomic.os, "link", fail) if fault == "before-publication" else patch.setattr(atomic, "_sync_publication", fail)
        with pytest.raises(OSError):
            atomic.publish_if_absent(path, b"complete")
    assert not list(tmp_path.glob("*.tmp"))
    if fault == "before-publication":
        assert not path.exists()
        assert atomic.publish_if_absent(path, b"complete") is atomic.PublicationResult.CREATED
    else:
        assert path.read_bytes() == b"complete"
        assert atomic.publish_if_absent(path, b"complete") is atomic.PublicationResult.ALREADY_EXISTS


def test_atomic_cleanup_failure_keeps_published_truth(tmp_path, monkeypatch):
    path = tmp_path / "owner.json"
    original = Path.unlink

    def cannot_cleanup(self, *args, **kwargs):
        if self.suffix == ".tmp":
            raise PermissionError("cleanup unavailable")
        return original(self, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", cannot_cleanup)
        assert atomic.publish_if_absent(path, b"complete") is atomic.PublicationResult.CREATED
    assert path.read_bytes() == b"complete"
    assert len(list(tmp_path.glob("*.tmp"))) == 1
    assert atomic.publish_if_absent(path, b"different") is atomic.PublicationResult.ALREADY_EXISTS
    assert path.read_bytes() == b"complete"


def test_atomic_expected_predecessor_and_exact_successor_replay(tmp_path):
    path = tmp_path / "owner.json"
    path.write_bytes(b"old")
    with pytest.raises(atomic.PublicationConflict):
        atomic.replace_if_exact_predecessor(path, b"wrong", b"new")
    assert path.read_bytes() == b"old"
    assert atomic.replace_if_exact_predecessor(path, b"old", b"new") is atomic.PublicationResult.REPLACED
    before = snapshot(path)
    assert atomic.replace_if_exact_predecessor(path, b"old", b"new") is atomic.PublicationResult.ALREADY_EXACT
    assert snapshot(path) == before
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("fault", ["before-replace", "after-replace"])
def test_atomic_replacement_response_loss_is_recoverable(tmp_path, monkeypatch, fault):
    path = tmp_path / "owner.json"
    path.write_bytes(b"old")
    with monkeypatch.context() as patch:
        patch.setattr(atomic.os, "replace", fail) if fault == "before-replace" else patch.setattr(atomic, "_sync_publication", fail)
        with pytest.raises(OSError):
            atomic.replace_if_exact_predecessor(path, b"old", b"new")
    assert path.read_bytes() == (b"old" if fault == "before-replace" else b"new")
    atomic.replace_if_exact_predecessor(path, b"old", b"new")
    assert path.read_bytes() == b"new"
    assert not list(tmp_path.glob("*.tmp"))


def test_conflicting_replacements_serialize_across_processes(tmp_path):
    path = tmp_path / "owner.json"
    path.write_bytes(b"old")
    script = (
        "import sys\n"
        "from torment_service.atomic_publication import replace_if_exact_predecessor, PublicationConflict\n"
        "try:\n"
        " print(replace_if_exact_predecessor(sys.argv[1], b'old', sys.argv[2].encode()).value)\n"
        "except PublicationConflict:\n"
        " print('CONFLICT')\n"
    )

    def run(value):
        result = subprocess.run([sys.executable, "-B", "-c", script, str(path), value],
                                capture_output=True, text=True, timeout=20, check=True)
        return result.stdout.strip()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, ("first", "second")))
    assert sorted(results) == ["CONFLICT", "REPLACED"]
    assert path.read_bytes() in (b"first", b"second")


def test_process_death_releases_file_local_replacement_lock(tmp_path):
    path = tmp_path / "owner.json"
    path.write_bytes(b"old")
    script = (
        "import os,sys\n"
        "from pathlib import Path\n"
        "from torment_service.atomic_publication import _replacement_lock\n"
        "with _replacement_lock(Path(sys.argv[1])):\n"
        " print('LOCKED', flush=True)\n"
        " os._exit(9)\n"
    )
    result = subprocess.run([sys.executable, "-B", "-c", script, str(path)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 9 and result.stdout.strip() == "LOCKED"
    assert path.read_bytes() == b"old"
    assert atomic.replace_if_exact_predecessor(path, b"old", b"new") is atomic.PublicationResult.REPLACED


def test_workspace_exact_create_replay_order_and_no_optional_legacy_files(tmp_path, monkeypatch):
    expected = declaration()
    assert workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected) == expected
    root = tmp_path / "workspaces" / "workspace"
    assert sorted(p.name for p in root.iterdir()) == ["domains.json", "workspace_meta.json"]
    assert strict_object((root / "domains.json").read_bytes()) == {"domains": ["zeta", "alpha"]}
    before = {p.name: snapshot(p) for p in root.iterdir()}
    monkeypatch.setattr(workspace, "publish_if_absent", fail)
    assert workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected) == expected
    assert {p.name: snapshot(p) for p in root.iterdir()} == before


@pytest.mark.parametrize("field,value", [
    ("ordered_domains", ("alpha", "zeta")), ("representation_dimension", 4),
    ("representation_provider", "different"), ("representation_model", "different"), ("workspace_created_ts", 99),
])
def test_workspace_changed_declaration_refuses_without_write(tmp_path, field, value):
    expected = declaration()
    workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    root = tmp_path / "workspaces" / "workspace"
    before = {p.name: snapshot(p) for p in root.iterdir()}
    with pytest.raises(ExternalOwnerConflict):
        workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=replace(expected, **{field: value}))
    assert {p.name: snapshot(p) for p in root.iterdir()} == before


@pytest.mark.parametrize("field,value", [("ordered_domains", ("zeta", "zeta")), ("ordered_domains", ()),
                                         ("representation_dimension", True), ("workspace_id", "../escape")])
def test_workspace_invalid_expanded_declaration(field, value):
    with pytest.raises(ExternalOwnerConflict):
        replace(declaration(), **{field: value})


@pytest.mark.parametrize("name,raw", [
    ("workspace_meta.json", b"{"), ("workspace_meta.json", b'{"workspace_id":"workspace","workspace_id":"workspace"}'),
    ("workspace_meta.json", b'{"workspace_id":"workspace"}'),
    ("domains.json", b'{"domains":["zeta","zeta"]}'), ("domains.json", b'{"domains":["alpha","zeta"]}'),
    ("domains.json", b'{"domains":["zeta","alpha"],"domains":["zeta","alpha"]}'), ("domains.json", b'{}'),
])
def test_workspace_malformed_or_conflicting_owner_refuses(tmp_path, name, raw):
    expected = declaration()
    workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    path = tmp_path / "workspaces" / "workspace" / name
    path.write_bytes(raw)
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    assert snapshot(path) == before


def test_workspace_identity_mismatch_refuses(tmp_path):
    expected = declaration()
    workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    path = tmp_path / "workspaces" / "workspace" / "workspace_meta.json"
    raw = expected.metadata_payload()
    raw["workspace_id"] = "Workspace"
    path.write_bytes(owner_bytes(raw))
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    assert snapshot(path) == before


def test_workspace_partial_recovery_publishes_only_missing_domains(tmp_path, monkeypatch):
    expected = declaration()
    publish = workspace.publish_if_absent

    def metadata_then_interrupt(path, content):
        result = publish(path, content)
        if Path(path).name == "workspace_meta.json":
            raise OSError("metadata publication response lost")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(workspace, "publish_if_absent", metadata_then_interrupt)
        with pytest.raises(OSError):
            workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    root = tmp_path / "workspaces" / "workspace"
    before = snapshot(root / "workspace_meta.json")
    assert not (root / "domains.json").exists()
    workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=expected)
    assert snapshot(root / "workspace_meta.json") == before
    assert strict_object((root / "domains.json").read_bytes()) == expected.domain_payload()


@pytest.mark.parametrize("reverse", [False, True])
def test_workspace_conflicting_precursor_never_gets_completed(tmp_path, reverse):
    root = tmp_path / "workspaces" / "workspace"
    root.mkdir(parents=True)
    name = "domains.json" if reverse else "workspace_meta.json"
    value = declaration().domain_payload() if reverse else {**declaration().metadata_payload(), "embed_dim": 99}
    (root / name).write_bytes(owner_bytes(value))
    with pytest.raises(ExternalOwnerConflict):
        workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=declaration())
    assert [p.name for p in root.iterdir()] == [name]


def test_identity_exact_initial_replay_never_calls_save_or_time(tmp_path, monkeypatch):
    store, expected = IdentityStore(str(tmp_path)), expected_identity()
    created = store.create_or_verify_for_onboarding(expected)
    assert created.to_dict() == expected.to_dict()
    assert created.created_ts == created.updated_ts == 11
    path = store._path(expected.workspace_id, expected.agent_id)
    before = snapshot(path)
    monkeypatch.setattr(identity_module, "_now_ts", fail)
    monkeypatch.setattr(store, "save", fail)
    monkeypatch.setattr(identity_module, "publish_if_absent", fail)
    assert store.create_or_verify_for_onboarding(expected).to_dict() == expected.to_dict()
    assert snapshot(path) == before


@pytest.mark.parametrize("field,value", [
    ("workspace_id", "Workspace"), ("agent_id", "Agent"), ("created_ts", -1), ("updated_ts", 0),
    ("created_ts", True), ("updated_ts", 99), ("seed", {}), ("overlay", {}),
])
def test_identity_conflicting_or_invalid_persisted_facts_refuse(tmp_path, field, value):
    store, expected = IdentityStore(str(tmp_path)), expected_identity()
    store.create_or_verify_for_onboarding(expected)
    raw = expected.to_dict()
    raw[field] = value
    path = Path(store._path(expected.workspace_id, expected.agent_id))
    path.write_bytes(owner_bytes(raw))
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        store.create_or_verify_for_onboarding(expected)
    assert snapshot(path) == before


@pytest.mark.parametrize("bad", ["malformed", "missing", "duplicate", "nonfinite", "seed-change", "overlay-change"])
def test_identity_raw_strict_verification_does_not_default_or_overwrite(tmp_path, bad):
    store, expected = IdentityStore(str(tmp_path)), expected_identity()
    store.create_or_verify_for_onboarding(expected)
    raw = expected.to_dict()
    if bad == "missing":
        del raw["created_ts"]
    if bad == "seed-change":
        raw["seed"]["core_traits"] = ["changed"]
    if bad in ("nonfinite", "overlay-change"):
        raw["overlay"]["decay_scale"] = float("nan") if bad == "nonfinite" else 9.0
    content = json.dumps(raw)
    if bad == "malformed":
        content = "{"
    if bad == "duplicate":
        content = content.replace('"created_ts": 11', '"created_ts": 11, "created_ts": 11')
    path = Path(store._path(expected.workspace_id, expected.agent_id))
    path.write_text(content, encoding="utf-8")
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        store.create_or_verify_for_onboarding(expected)
    assert snapshot(path) == before


def test_identity_stable_witness_excludes_evolving_overlay_and_update_time(tmp_path):
    store, expected = IdentityStore(str(tmp_path)), expected_identity()
    store.create_or_verify_for_onboarding(expected)
    raw = expected.to_dict()
    raw["overlay"]["decay_scale"] = 5.0
    raw["updated_ts"] = 55
    path = Path(store._path(expected.workspace_id, expected.agent_id))
    path.write_bytes(owner_bytes(raw))
    before = snapshot(path)
    observed = store.verify_stable_for_onboarding(expected)
    assert store.stable_identity_projection(observed) == GenesisIntent.from_payload(facts()).external_owner_projection()["identity"]
    assert snapshot(path) == before
    with pytest.raises(ExternalOwnerConflict):
        store.create_or_verify_for_onboarding(expected)


def test_identity_normal_permissive_load_remains_unchanged(tmp_path):
    store = IdentityStore(str(tmp_path))
    path = Path(store._path("workspace", "agent"))
    path.parent.mkdir(parents=True)
    path.write_text('{"workspace_id":"workspace","agent_id":"agent"}', encoding="utf-8")
    loaded = store.load("workspace", "agent")
    assert loaded.seed == identity_module.DEFAULT_AGENT_SEED
    assert loaded.overlay == identity_module.DEFAULT_AGENT_OVERLAY
    with pytest.raises(ExternalOwnerConflict):
        store.read_strict_for_onboarding("workspace", "agent")


def test_identity_initial_timestamps_refuse_before_creating_owner_files(tmp_path):
    with pytest.raises(ExternalOwnerConflict):
        IdentityStore(str(tmp_path)).create_or_verify_for_onboarding(replace(expected_identity(), updated_ts=12))
    assert not list(tmp_path.rglob("identity.json"))


def test_disabled_character_is_not_published_by_other_owner_primitives(tmp_path):
    value = facts(False)
    workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=declaration())
    identity = expected_identity()
    identity.seed = value["agent"]["identity_seed"]
    IdentityStore(str(tmp_path)).create_or_verify_for_onboarding(identity)
    assert not (tmp_path / "workspaces" / "workspace" / "seeds").exists()


def test_character_definition_replay_preserves_bytes_digest_and_state(tmp_path, monkeypatch):
    store = CharacterStore(str(tmp_path))
    seed = create_seed(store)
    assert seed.seed_eids == [] and seed.seed_motif_id == "" and seed.created_ts == 12
    assert {k: v for k, v in seed.to_dict().items() if k not in {"created_ts", "seed_eids", "seed_motif_id"}} == seed_definition()
    path = store._seed_path("workspace", seed.seed_id)
    before = snapshot(path)
    monkeypatch.setattr(character_module, "_now_ts", fail)
    monkeypatch.setattr(store, "save_seed", fail)
    monkeypatch.setattr(character_module, "publish_if_absent", fail)
    replay = create_seed(store)
    assert character_seed_definition_digest(seed) == character_seed_definition_digest(replay)
    assert snapshot(path) == before
    assert store.load_seed("workspace", seed.seed_id).to_dict() == replay.to_dict()
    assert not (tmp_path / "workspaces" / "workspace" / "agents").exists()


@pytest.mark.parametrize("field,value", [("owner_agent_id", "different"), ("seed_text", "different"),
                                         ("created_ts", 99), ("seed_id", "different"), ("core_weight", 99)])
def test_character_definition_conflicts_refuse_without_writes(tmp_path, field, value):
    store = CharacterStore(str(tmp_path))
    seed = create_seed(store)
    raw = seed.to_dict()
    raw[field] = value
    path = Path(store._seed_path("workspace", seed.seed_id))
    path.write_bytes(owner_bytes(raw))
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        create_seed(store)
    assert snapshot(path) == before


def test_character_definition_digest_cannot_adopt_unicode_identifier_alias(tmp_path):
    store = CharacterStore(str(tmp_path))
    definition = deepcopy(seed_definition())
    definition["owner_agent_id"] = "e\u0301"
    initial = store.create_or_verify_seed_definition("workspace", definition, created_ts=12)
    alias = deepcopy(initial)
    alias.owner_agent_id = "\u00e9"
    assert character_seed_definition_digest(alias) == character_seed_definition_digest(initial)
    path = Path(store._seed_path("workspace", initial.seed_id))
    path.write_bytes(owner_bytes(alias.to_dict()))
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        store.create_or_verify_seed_definition("workspace", definition, created_ts=12)
    assert snapshot(path) == before


def test_character_ordinary_legacy_load_still_supplies_its_existing_defaults(tmp_path):
    store = CharacterStore(str(tmp_path))
    path = Path(store._seed_path("workspace", "legacy"))
    path.parent.mkdir(parents=True)
    path.write_bytes(owner_bytes(dict(seed_id="legacy", character_name="Legacy", seed_text="Definition.")))
    loaded = store.load_seed("workspace", "legacy")
    assert loaded.owner_agent_id == "" and loaded.seed_eids == [] and loaded.seed_motif_id == ""
    with pytest.raises(ExternalOwnerConflict):
        store.read_seed_strict_for_onboarding("workspace", "legacy")


@pytest.mark.parametrize("bad", ["malformed", "missing", "duplicate", "nonfinite", "partial-eids", "partial-motif", "unexpected"])
def test_character_strict_document_refusal(tmp_path, bad):
    store = CharacterStore(str(tmp_path))
    seed = create_seed(store)
    raw = seed.to_dict()
    if bad == "missing":
        del raw["core_weight"]
    if bad == "nonfinite":
        raw["drift_gravity_strength"] = float("inf")
    if bad == "partial-eids":
        raw["seed_eids"] = [1]
    if bad == "partial-motif":
        raw["seed_motif_id"] = "motif"
    if bad == "unexpected":
        raw["runtime_cache"] = {}
    content = json.dumps(raw)
    if bad == "malformed":
        content = "{"
    if bad == "duplicate":
        content = content.replace('"created_ts": 12', '"created_ts": 12, "created_ts": 12')
    path = Path(store._seed_path("workspace", seed.seed_id))
    path.write_text(content, encoding="utf-8")
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        create_seed(store)
    assert snapshot(path) == before


def test_character_exact_finalization_and_later_definition_replay(tmp_path, monkeypatch):
    store = CharacterStore(str(tmp_path))
    unplanted = create_seed(store)
    result = finalize_seed(store)
    assert result.seed_eids == [11, 12] and result.seed_motif_id == "native-seed-motif"
    assert result.created_ts == unplanted.created_ts == 12
    assert character_seed_definition_digest(result) == character_seed_definition_digest(unplanted)
    assert store.stable_seed_projection(result) == store.stable_seed_projection(unplanted)
    path = store._seed_path("workspace", result.seed_id)
    before = snapshot(path)
    monkeypatch.setattr(character_module, "replace_if_exact_predecessor", fail)
    assert finalize_seed(store).to_dict() == result.to_dict()
    assert create_seed(store).to_dict() == result.to_dict()
    assert store.load_seed("workspace", result.seed_id).to_dict() == result.to_dict()
    assert snapshot(path) == before


@pytest.mark.parametrize("eids,motif", [((13,), "native-seed-motif"), ((11, 12), "other"), ((12, 11), "native-seed-motif")])
def test_character_different_native_linkage_refuses(tmp_path, eids, motif):
    store = CharacterStore(str(tmp_path))
    create_seed(store)
    result = finalize_seed(store)
    path = store._seed_path("workspace", result.seed_id)
    before = snapshot(path)
    with pytest.raises(ExternalOwnerConflict):
        finalize_seed(store, eids, motif)
    assert snapshot(path) == before


def test_character_wrong_predecessor_and_absent_definition_refuse(tmp_path):
    store = CharacterStore(str(tmp_path))
    with pytest.raises(ExternalOwnerConflict):
        finalize_seed(store)
    assert not list(tmp_path.rglob("seed.json"))
    create_seed(store)
    other = seed_definition()
    other["core_weight"] = 42
    before = snapshot(store._seed_path("workspace", other["seed_id"]))
    with pytest.raises(ExternalOwnerConflict):
        store.finalize_or_verify_seed_linkage("workspace", other, created_ts=12, seed_eids=(11,), seed_motif_id="motif")
    assert snapshot(store._seed_path("workspace", other["seed_id"])) == before


@pytest.mark.parametrize("fault", ["before-replace", "after-replace"])
def test_character_replacement_interruption_has_complete_old_or_new_owner(tmp_path, monkeypatch, fault):
    store = CharacterStore(str(tmp_path))
    unplanted = create_seed(store)
    path = Path(store._seed_path("workspace", unplanted.seed_id))
    with monkeypatch.context() as patch:
        patch.setattr(atomic.os, "replace", fail) if fault == "before-replace" else patch.setattr(atomic, "_sync_publication", fail)
        with pytest.raises(OSError):
            finalize_seed(store)
    observed = store.seed_from_strict_json(path.read_bytes())
    assert observed.seed_eids == ([] if fault == "before-replace" else [11, 12])
    assert finalize_seed(store).seed_eids == [11, 12]
    assert not list(path.parent.glob("*.tmp"))


@pytest.mark.parametrize("owner", ["workspace", "identity", "character"])
def test_owner_path_traversal_is_refused_before_publication(tmp_path, owner):
    with pytest.raises(ValueError):
        if owner == "workspace":
            workspace.create_or_verify_workspace_declaration(data_dir=str(tmp_path), expected=replace(declaration(), workspace_id="../escape"))
        elif owner == "identity":
            IdentityStore(str(tmp_path)).create_or_verify_for_onboarding(replace(expected_identity(), agent_id="../escape"))
        else:
            CharacterStore(str(tmp_path)).create_or_verify_seed_definition("../escape", seed_definition(), created_ts=12)
    assert not list(tmp_path.rglob("*.json"))


def test_owner_case_alias_cannot_adopt_existing_identity(tmp_path):
    store = IdentityStore(str(tmp_path))
    expected = replace(expected_identity(), agent_id="Agent")
    store.create_or_verify_for_onboarding(expected)
    alias = tmp_path / "workspaces" / "workspace" / "agents" / "agent" / "identity.json"
    if not alias.exists():
        pytest.skip("filesystem has distinct case-sensitive paths")
    before = snapshot(alias)
    with pytest.raises(ExternalOwnerConflict):
        store.create_or_verify_for_onboarding(replace(expected, agent_id="agent"))
    assert snapshot(alias) == before


def isolated_workspace_format_methods():
    """Execute actual Workspace owner methods without importing Fabric/Brainvision.

    Only the four persistence methods and their path validators are selected
    from the source AST. This preserves their code while excluding unrelated
    constructors, MemoryGraph/SQLite, runtime owners, and model imports.
    """
    from fastapi import HTTPException
    from torment_service.pathing import validate_portable_new_identifier, validate_structural_path_component

    source = Path(__file__).resolve().parents[1] / "torment_service" / "fabric.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    helpers = {"_canonical_data_root", "_ws_root", "_safe_child", "_validate_path_component", "_validate_new_path_component"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in helpers]
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Workspace")
    cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in
                {"_meta_path", "_load_or_init_meta", "_domains_path", "_load_or_init_domains"}]
    selected.append(cls)
    namespace = dict(os=os, json=json, _now_ts=lambda: 123, HTTPException=HTTPException,
                     validate_portable_new_identifier=validate_portable_new_identifier,
                     validate_structural_path_component=validate_structural_path_component,
                     workspace_meta_payload=workspace.workspace_meta_payload, domains_payload=workspace.domains_payload)
    router = ast.parse((source.parent / "router.py").read_text(encoding="utf-8"))
    assignment = next(node for node in router.body if isinstance(node, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == "SINGLE_AGENT_DOMAIN" for t in node.targets))
    namespace["SINGLE_AGENT_DOMAIN"] = ast.literal_eval(assignment.value)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec", flags=__future__.annotations.compiler_flag), namespace)
    return namespace["Workspace"], namespace["SINGLE_AGENT_DOMAIN"]


def test_existing_workspace_format_methods_keep_exact_bytes_order_and_replay(tmp_path):
    cls, default_domain = isolated_workspace_format_methods()
    instance = cls()
    instance.data_dir, instance.workspace_id = str(tmp_path), "workspace"
    instance.kernel = SimpleNamespace(embedder=SimpleNamespace(dim=3, provider="fixture-provider", model="fixture-model"))
    expected = replace(declaration(), workspace_created_ts=123)
    assert instance._load_or_init_meta() == expected.metadata_payload()
    assert Path(instance._meta_path()).read_bytes() == owner_bytes(expected.metadata_payload())
    assert instance._load_or_init_domains(["zeta", "alpha"]) == ["zeta", "alpha"]
    assert Path(instance._domains_path()).read_bytes() == owner_bytes(expected.domain_payload(), sort_keys=False)
    before = snapshot(instance._domains_path())
    assert instance._load_or_init_domains() == ["zeta", "alpha"]
    assert snapshot(instance._domains_path()) == before
    assert instance._load_or_init_domains(["alpha", "middle"]) == ["zeta", "alpha", "middle"]
    Path(instance._meta_path()).write_bytes(b"{")
    assert instance._load_or_init_meta() == {}
    instance.workspace_id = "default-workspace"
    assert instance._load_or_init_domains() == [default_domain]


def test_existing_workspace_payload_builders_keep_legacy_permissiveness(tmp_path):
    cls, _ = isolated_workspace_format_methods()
    instance = cls()
    instance.data_dir, instance.workspace_id = str(tmp_path), "workspace"
    instance.kernel = SimpleNamespace(embedder=SimpleNamespace())
    assert instance._load_or_init_meta() == dict(workspace_id="workspace", created_ts=123, embed_dim=0, embed_provider="", embed_model="")
    assert instance._load_or_init_domains(["same", "same"]) == ["same", "same"]


@pytest.mark.parametrize("raw", [b"[]", b"null", b'{"x":NaN}', b'{"x":Infinity}', b'{"x":{"y":1,"y":2}}', b'\xff'])
def test_strict_json_refuses_nonobjects_duplicates_and_nonfinite_values(raw):
    with pytest.raises(ExternalOwnerConflict):
        strict_object(raw)
