"""Full native-public I4B-1F outcome and owner-identity qualification.

Every fixture crosses ``NativePublicIngestExecutor.execute`` over a synthetic
active root.  No service, provider, or real workspace root is used.
"""
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from torment_service.fabric import _load_symbol_state
from torment_service.post_write_runtime import LegacyFabricPostWriteAdapter
from torment_service.public_mutation_identity import (
    derive_native_operation_key,
    normalize_public_mutation_key,
)
from torment_service.public_runtime import close_public_runtime
from torment_service.roles import RoleStore
from torment_service.substrate.connection import open_existing_native_core_connection
from torment_service.substrate.compat import (
    CompatibilityEmbeddingPublicationRequest,
    NativeMemoryCompatibilityFacade,
)
from torment_service.substrate.fabric_native_routing import NativePrecommitAttachFailure
from torment_service.substrate.motifs import NativeMotifService
from torment_service.substrate.native_public_ingest_executor import NativePublicIngestRequest

from tests.test_p9d_i3b0_native_materialization_fencing import _native_runtime


def _request(
    key: str,
    text: str,
    vector: list[float],
    *,
    step: int,
    **changes: object,
) -> NativePublicIngestRequest:
    values: dict[str, object] = {
        "workspace_id": "orchard",
        "agent_id": "aria",
        "text": text,
        "public_mutation_key": key,
        "step": step,
        "domain_id": "personal",
        "supplied_embedding": vector,
    }
    values.update(changes)
    return NativePublicIngestRequest(**values)  # type: ignore[arg-type]


def _role_samples(root: Path) -> int:
    path = root / "workspaces" / "orchard" / "agents" / "aria" / "roles.json"
    return int(json.loads(path.read_text(encoding="utf-8"))["samples"])


def _symbol_path(root: Path) -> Path:
    return root / "workspaces" / "orchard" / "agents" / "aria" / "symbol_state.json"


def _canonical_source_key(request: NativePublicIngestRequest) -> str:
    key = normalize_public_mutation_key(request.public_mutation_key)
    assert key is not None
    public_key = derive_native_operation_key(
        operation="ingest",
        workspace_id=request.workspace_id,
        agent_id=request.agent_id,
        key=key,
    )
    return f"NATIVE_FABRIC_NEW_MEMORY:SOURCE:{public_key}:STORAGE"


def _reinforcement_source_key(request: NativePublicIngestRequest) -> str:
    key = normalize_public_mutation_key(request.public_mutation_key)
    assert key is not None
    public_key = derive_native_operation_key(
        operation="ingest",
        workspace_id=request.workspace_id,
        agent_id=request.agent_id,
        key=key,
    )
    return f"NATIVE_REINFORCEMENT:SOURCE:NATIVE_FABRIC_REINFORCEMENT:{public_key}:STORAGE"


def _operation_owns_current_result(runtime, *, key: str, eid: int) -> None:
    core_path = runtime.native_owner.authority_facts.core_database_path
    with open_existing_native_core_connection(core_path) as opened:
        rows = opened.connection.execute(
            """
            SELECT o.operation_id
              FROM operations o
              JOIN operation_outputs out ON out.operation_id=o.operation_id
              JOIN legacy_object_aliases alias ON alias.object_id=out.object_id
              JOIN objects memory ON memory.object_id=alias.object_id
             WHERE o.idempotency_key=?
               AND alias.alias_kind='EID' AND alias.alias_value=?
               AND out.object_revision_id=memory.current_revision_id
            """,
            (key, str(eid)),
        ).fetchall()
    assert len(rows) == 1


def _operation_count(runtime, key: str) -> int:
    core_path = runtime.native_owner.authority_facts.core_database_path
    with open_existing_native_core_connection(core_path) as opened:
        return int(
            opened.connection.execute(
                "SELECT count(*) FROM operations WHERE idempotency_key=?", (key,),
            ).fetchone()[0]
        )


def _post_write_attempts(runtime, monkeypatch) -> list[object]:
    observed: list[object] = []
    original = runtime.native_owner.open_post_write_context

    def observe(*args, **kwargs):
        observed.append(kwargs.get("configuration"))
        return original(*args, **kwargs)

    monkeypatch.setattr(runtime.native_owner, "open_post_write_context", observe)
    return observed


def _seed_public_true_split_parent(runtime, *, seed_request: NativePublicIngestRequest) -> None:
    """Build a synthetic bimodal parent through existing native test seams."""
    seed = runtime._executor.execute(seed_request)  # noqa: SLF001 - public boundary fixture setup
    assert seed["stored"] is True
    scope = runtime._active_runtime().lookup_private("aria").fabric_routing_scope  # noqa: SLF001
    core_path = runtime.native_owner.authority_facts.core_database_path
    with open_existing_native_core_connection(core_path) as opened:
        connection = opened.connection
        motifs = NativeMotifService(connection)
        parent = motifs.resolve_motif_alias(
            motif_alias_namespace_id=scope.motif_alias_namespace_id,
            runtime_motif_id=seed["motifs"][0],
        )
        facade = NativeMemoryCompatibilityFacade(connection)
        for ordinal, vector in enumerate(
            [(1.0, 0.0, 0.0)] * 47 + [(-1.0, 0.0, 0.0)] * 47,
            start=2,
        ):
            raw = np.asarray(vector, dtype=np.float32)
            source = facade.finalize_memory_draft(facade.begin_memory_draft(
                legacy_source_namespace_id=scope.runtime_scope.legacy_source_namespace_id,
                idempotency_namespace_id=scope.idempotency_namespace_id,
                idempotency_key=f"i4b2-public-split-source:{ordinal}",
                identity_namespace_id=scope.runtime_scope.identity_namespace_id,
                semantic_scope_id=scope.runtime_scope.semantic_scope_id,
                summary=f"i4b2 public split source {ordinal}", memory_type="reflection",
                logical_step=ordinal,
                embedding_request=CompatibilityEmbeddingPublicationRequest(
                    raw.tobytes(), "COMPAT_EMBEDDING", 1, "compat-embedding-v1", "RAW_VECTOR",
                    dtype="float32", dimension=3,
                ),
            )).source
            current = motifs.get_current_motif(parent)
            motifs.add_motif_member(
                idempotency_namespace_id=scope.idempotency_namespace_id,
                idempotency_key=f"i4b2-public-split-member:{ordinal}",
                motif_alias_namespace_id=scope.motif_alias_namespace_id,
                membership_identity_namespace_id=scope.membership_identity_namespace_id,
                motif_object_id=parent,
                expected_motif_revision_id=current.motif_revision_id,
                state=replace(current.state, last_active_ts=current.state.last_active_ts + 1),
                member_object_id=source.object_id,
            )


def test_i4b1f_full_public_create_uses_existing_canonical_source_owner(tmp_path: Path, monkeypatch):
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        request = _request("i4b1f-create", "plan a fresh public memory", [1.0, 0.0, 0.0], step=1)
        post_write = _post_write_attempts(runtime, monkeypatch)

        result = runtime._executor.execute(request)  # noqa: SLF001 - required public-executor boundary

        assert result["stored"] is True and result["reinforced"] is False
        assert "failure_code" not in result
        _operation_owns_current_result(runtime, key=_canonical_source_key(request), eid=int(result["eid"]))
        assert _operation_count(runtime, f"I4B1:CANONICAL_COMMIT:{_canonical_source_key(request)}") == 0
        assert len(post_write) == 1
    finally:
        close_public_runtime(root)


def test_i4b2_full_public_true_split_enters_only_the_motif_tail(tmp_path: Path, monkeypatch):
    """Cross the real public executor handoff with an actual true-split result."""
    import torment_service.substrate.native_world_runtime as world_module

    monkeypatch.setattr(world_module.NativeWorldRuntime, "ensure_initialized", lambda _self: None)
    monkeypatch.setattr(
        world_module.NativeWorldRuntime,
        "register_fresh_created",
        lambda _self, **_kwargs: None,
    )
    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        _seed_public_true_split_parent(
            runtime,
            seed_request=_request("i4b2-public-seed", "seed a split parent", [1.0, 0.0, 0.0], step=1),
        )
        runtime.cognition_fabric._hivemind_enable = False
        post_write = _post_write_attempts(runtime, monkeypatch)

        def forbidden(*_args, **_kwargs):
            raise AssertionError("I4B-2 public handoff reached an unqualified post-write owner")

        for name in (
            "_run_contradiction_surface",
            "_run_srg_collision",
            "_run_hivemind",
            "_run_world_step",
            "_run_character_drift",
            "_run_proposal",
            "_run_derived_memory",
        ):
            monkeypatch.setattr(LegacyFabricPostWriteAdapter, name, forbidden)

        request = _request(
            "i4b2-public-true-split",
            "a public true split reaches only its qualified tail",
            [0.7, 0.714, 0.0],
            step=200,
        )
        result = runtime._executor.execute(request)  # noqa: SLF001 - required public-executor boundary

        assert result["stored"] is True and result["reinforced"] is False
        assert result["created_motif"] is None
        assert len(result["motifs"]) == 2
        assert len(post_write) == 1
        configuration = post_write[0]
        assert configuration.motif_suggestion_maintenance_required is True
        assert configuration.profile.motif_suggestion_maintenance.name == "QUALIFIED"
        assert configuration.profile.motif_auto_merge.name == "QUALIFIED"
    finally:
        close_public_runtime(root)


def test_i4b1f_full_public_no_write_is_distinct_and_reaches_legacy_tail_boundary(
    tmp_path: Path, monkeypatch,
):
    import torment_service.fabric as fabric_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        classified: list[str] = []
        original_classify = fabric_module.classify_affect

        def classify(summary: str):
            classified.append(summary)
            return original_classify(summary)

        monkeypatch.setattr(fabric_module, "classify_affect", classify)
        request = _request(
            "i4b1f-ordinary-no-write", "", [1.0, 0.0, 0.0], step=1,
            supplied_summary="ordinary no-write still updates role evidence",
        )
        role_before = _role_samples(root)
        assert not _symbol_path(root).exists()
        post_write = _post_write_attempts(runtime, monkeypatch)

        result = runtime._executor.execute(request)  # noqa: SLF001 - required public-executor boundary

        assert result["stored"] is False and result["reinforced"] is False
        assert "failure_code" not in result
        assert _role_samples(root) == role_before + 1
        assert classified == ["ordinary no-write still updates role evidence"]
        assert not _symbol_path(root).exists()
        assert _operation_count(runtime, _canonical_source_key(request)) == 0
        # Legacy invokes its always-run post-write adapter after ordinary
        # NO_WRITE.  Native reaches the existing qualified boundary with no
        # fabricated storage witness.
        assert len(post_write) == 1
    finally:
        close_public_runtime(root)


def test_i4b1f_canonical_failure_returns_before_post_write_and_external_residue_survives_restart(
    tmp_path: Path, monkeypatch,
):
    import torment_service.fabric as fabric_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    closed = False
    try:
        classified: list[str] = []
        original_classify = fabric_module.classify_affect

        def classify(summary: str):
            classified.append(summary)
            return original_classify(summary)

        monkeypatch.setattr(fabric_module, "classify_affect", classify)
        request = _request(
            "i4b1f-canonical-failure", "canonical failure retains precommit residue",
            [0.0, 1.0, 0.0], step=1,
        )
        role_before = _role_samples(root)
        post_write = _post_write_attempts(runtime, monkeypatch)

        result = runtime._executor.execute(  # noqa: SLF001 - required public-executor boundary
            request, _test_storage_stop_after="precommit_canonical_failure",
        )

        assert result == {
            "stored": False,
            "reinforced": False,
            "failure_code": "canonical_commit_failed",
            "eid": None,
            "domain_chosen": "personal",
        }
        assert _role_samples(root) == role_before + 1
        assert classified == [request.text]
        symbol_before_restart = json.loads(_symbol_path(root).read_text(encoding="utf-8"))
        assert symbol_before_restart["last_motif_id"]
        assert not (root / "workspaces" / "orchard" / "agents" / "aria" / "affect_state.json").exists()
        assert _operation_count(runtime, _canonical_source_key(request)) == 0
        assert post_write == []
        core_path = runtime.native_owner.authority_facts.core_database_path

        close_public_runtime(root)
        closed = True
        assert RoleStore(str(root)).load("orchard", "aria").samples == role_before + 1
        assert _load_symbol_state(str(root), "orchard", "aria") == symbol_before_restart
        with open_existing_native_core_connection(core_path) as opened:
            states = [
                row[0]
                for row in opened.connection.execute(
                    """
                    SELECT revision.existence_state
                      FROM objects memory
                      JOIN object_revisions revision
                        ON revision.object_id=memory.object_id
                       AND revision.object_revision_id=memory.current_revision_id
                     WHERE memory.object_kind='LEGACY_CORE_NODE'
                    """,
                ).fetchall()
            ]
        assert "ABORTED" in states and "EXISTS" not in states
    finally:
        if not closed:
            close_public_runtime(root)


def test_i4b1f_full_public_reinforcement_and_fallthroughs_preserve_external_owner_scopes(
    tmp_path: Path, monkeypatch,
):
    import torment_service.fabric as fabric_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        symbol_calls: list[object] = []
        classified: list[str] = []
        original_symbol_owner = runtime.cognition_fabric._persist_symbol_precommit_state
        original_classify = fabric_module.classify_affect

        def observe_symbol(*args, **kwargs):
            symbol_calls.append(kwargs.get("primary_motif_id"))
            return original_symbol_owner(*args, **kwargs)

        def classify(summary: str):
            classified.append(summary)
            return original_classify(summary)

        monkeypatch.setattr(runtime.cognition_fabric, "_persist_symbol_precommit_state", observe_symbol)
        monkeypatch.setattr(fabric_module, "classify_affect", classify)
        seed_request = _request("i4b1f-reinforce-seed", "plan reinforcement parity", [1.0, 0.0, 0.0], step=1)
        seed = runtime._executor.execute(seed_request)  # noqa: SLF001
        symbol_after_seed = json.loads(_symbol_path(root).read_text(encoding="utf-8"))
        role_after_seed = _role_samples(root)
        assert len(symbol_calls) == 1

        reinforce_request = _request("i4b1f-reinforce", "plan reinforcement parity", [1.0, 0.0, 0.0], step=2)
        reinforced = runtime._executor.execute(reinforce_request)  # noqa: SLF001
        assert reinforced["stored"] is True and reinforced["reinforced"] is True
        assert _role_samples(root) == role_after_seed + 1
        assert json.loads(_symbol_path(root).read_text(encoding="utf-8")) == symbol_after_seed
        assert len(symbol_calls) == 1
        _operation_owns_current_result(
            runtime, key=_reinforcement_source_key(reinforce_request), eid=int(reinforced["eid"]),
        )

        semantic_request = _request(
            "i4b1f-semantic-fallthrough", "plan reinforcement parity", [1.0, 0.0, 0.0],
            step=3,
            memory_class="baton",
            extra_payload={
                "baton_lifecycle": {
                    "owner": "user",
                    "expires_when": "resolved",
                    "resolution_condition": "resolved",
                },
            },
        )
        semantic = runtime._executor.execute(semantic_request)  # noqa: SLF001
        assert semantic["stored"] is True and semantic["reinforced"] is False
        assert len(symbol_calls) == 2

        from torment_service.substrate.memory_reinforcement import NativeMemoryReinforcementService

        exception_request = _request(
            "i4b1f-exception-fallthrough", "exception reinforcement fallthrough", [0.0, 1.0, 0.0], step=4,
        )
        runtime._executor.execute(_request(  # noqa: SLF001 - seed the duplicate candidate
            "i4b1f-exception-seed", exception_request.text, [0.0, 1.0, 0.0], step=3,
        ))
        with monkeypatch.context() as patched:
            patched.setattr(
                NativeMemoryReinforcementService,
                "reinforce",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced reinforcement failure")),
            )
            exception = runtime._executor.execute(exception_request)  # noqa: SLF001
        assert exception["stored"] is True and exception["reinforced"] is False
        assert len(symbol_calls) == 4
        assert _role_samples(root) == role_after_seed + 4
        assert classified == [
            seed_request.text,
            reinforce_request.text,
            semantic_request.text,
            exception_request.text,
            exception_request.text,
        ]
    finally:
        close_public_runtime(root)


def test_i4b1f_precommit_attach_failure_is_publicly_raised_without_post_write(tmp_path: Path, monkeypatch):
    import torment_service.substrate.fabric_native_routing as routing_module

    root, runtime = _native_runtime(tmp_path, monkeypatch)
    try:
        request = _request("i4b1f-attach-failure", "attach failure remains precommit", [1.0, 0.0, 0.0], step=1)
        post_write = _post_write_attempts(runtime, monkeypatch)
        monkeypatch.setattr(
            routing_module,
            "_commit_precommit_motif",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced attach failure")),
        )

        with pytest.raises(NativePrecommitAttachFailure):
            runtime._executor.execute(request)  # noqa: SLF001 - required public-executor boundary

        assert _operation_count(runtime, _canonical_source_key(request)) == 0
        assert post_write == []
        assert not _symbol_path(root).exists()
    finally:
        close_public_runtime(root)
