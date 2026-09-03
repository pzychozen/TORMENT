"""Synthetic native-public external precommit owner qualification for I4B-1E."""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from torment_service.public_runtime import close_public_runtime
from torment_service.substrate.native_public_ingest_executor import NativePublicIngestRequest

from tests.test_p9d_i3b0_native_materialization_fencing import _native_runtime


def _role_state(root: Path) -> dict:
    return json.loads(
        (root / "workspaces" / "orchard" / "agents" / "aria" / "roles.json").read_text(encoding="utf-8")
    )


def _symbol_state(root: Path) -> dict:
    return json.loads(
        (root / "workspaces" / "orchard" / "agents" / "aria" / "symbol_state.json").read_text(encoding="utf-8")
    )


def test_native_public_precommit_uses_retained_role_and_symbol_owners(tmp_path: Path, monkeypatch):
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        initial_roles = _role_state(root)["samples"]
        created_request = NativePublicIngestRequest(
            workspace_id="orchard", agent_id="aria",
            text="plan and investigate a fresh subject",
            public_mutation_key="i4b1e-created", step=1,
            domain_id="personal", supplied_embedding=[1.0, 0.0, 0.0],
        )
        created_prepared = runtime._executor._prepare(created_request)  # noqa: SLF001 - I4B precommit boundary
        created = runtime._executor._storage.store(created_prepared)  # noqa: SLF001 - I4B precommit boundary
        assert created.stored is True and created.reinforced is False
        assert created_prepared.affect_classification_completed is True
        after_create_roles = _role_state(root)["samples"]
        created_symbol = _symbol_state(root)
        assert after_create_roles == initial_roles + 1
        assert created_symbol["last_motif_id"]

        reinforced_request = NativePublicIngestRequest(
            workspace_id="orchard", agent_id="aria",
            text="plan and investigate a fresh subject",
            public_mutation_key="i4b1e-reinforced", step=2,
            domain_id="personal", supplied_embedding=[1.0, 0.0, 0.0],
        )
        reinforced_prepared = runtime._executor._prepare(reinforced_request)  # noqa: SLF001
        reinforced = runtime._executor._storage.store(reinforced_prepared)  # noqa: SLF001
        assert reinforced.stored is True and reinforced.reinforced is True
        assert reinforced_prepared.affect_classification_completed is True
        assert _role_state(root)["samples"] == after_create_roles + 1
        assert _symbol_state(root) == created_symbol

        failed_prepared = runtime._executor._prepare(  # noqa: SLF001
            NativePublicIngestRequest(
                workspace_id="orchard", agent_id="aria",
                text="create a different symbol residue",
                public_mutation_key="i4b1e-canonical-failure", step=3,
                domain_id="personal", supplied_embedding=[0.0, 1.0, 0.0],
            ),
        )
        failed = runtime._executor._storage.store(  # noqa: SLF001
            failed_prepared, _test_stop_after="precommit_canonical_failure",
        )
        assert failed.stored is False
        assert _role_state(root)["samples"] == after_create_roles + 2
        failed_symbol = _symbol_state(root)
        assert failed_symbol["last_motif_id"] != created_symbol["last_motif_id"]
    finally:
        close_public_runtime(root)


def test_native_public_role_and_symbol_owner_failures_remain_fail_soft(tmp_path: Path, monkeypatch):
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        monkeypatch.setattr(runtime.cognition_fabric.role_store, "save", lambda _profile: (_ for _ in ()).throw(OSError("role write")))
        role_prepared = runtime._executor._prepare(  # noqa: SLF001
            NativePublicIngestRequest(
                workspace_id="orchard", agent_id="aria",
                text="role writer failure remains soft",
                public_mutation_key="i4b1e-role-failure", step=1,
                domain_id="personal", supplied_embedding=[1.0, 0.0, 0.0],
            ),
        )
        role_failed = runtime._executor._storage.store(role_prepared)  # noqa: SLF001
        assert role_failed.stored is True
        before_symbol_failure = _symbol_state(root)

        monkeypatch.setattr(runtime.cognition_fabric, "_persist_symbol_precommit_state", lambda *_args, **_kwargs: False)
        symbol_prepared = runtime._executor._prepare(  # noqa: SLF001
            NativePublicIngestRequest(
                workspace_id="orchard", agent_id="aria",
                text="symbol writer failure remains soft",
                public_mutation_key="i4b1e-symbol-failure", step=2,
                domain_id="personal", supplied_embedding=[0.0, 1.0, 0.0],
            ),
        )
        symbol_failed = runtime._executor._storage.store(symbol_prepared)  # noqa: SLF001
        assert symbol_failed.stored is True
        assert _symbol_state(root) == before_symbol_failure
    finally:
        close_public_runtime(root)


def test_native_public_affect_failure_is_soft_and_no_write_keeps_predecision_role_effect(tmp_path: Path, monkeypatch):
    import torment_service.fabric as fabric_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        monkeypatch.setattr(
            fabric_module, "classify_affect",
            lambda _summary: (_ for _ in ()).throw(RuntimeError("affect classifier")),
        )
        affect_prepared = runtime._executor._prepare(  # noqa: SLF001
            NativePublicIngestRequest(
                workspace_id="orchard", agent_id="aria", text="affect failure remains soft",
                public_mutation_key="i4b1e-affect-failure", step=1,
                domain_id="personal", supplied_embedding=[1.0, 0.0, 0.0],
            ),
        )
        assert affect_prepared.affect_classification_completed is False
        assert runtime._executor._storage.store(affect_prepared).stored is True  # noqa: SLF001

        samples_before_no_write = _role_state(root)["samples"]
        no_write_prepared = runtime._executor._prepare(  # noqa: SLF001
            NativePublicIngestRequest(
                workspace_id="orchard", agent_id="aria", text="no write role still advances",
                public_mutation_key="i4b1e-no-write", step=2,
                domain_id="personal", supplied_embedding=[0.0, 1.0, 0.0],
            ),
        )
        no_write = runtime._executor._storage.store(replace(no_write_prepared, allow_write=False))  # noqa: SLF001
        assert no_write.stored is False and no_write.disposition.value == "NO_WRITE"
        assert _role_state(root)["samples"] == samples_before_no_write + 1
    finally:
        close_public_runtime(root)
