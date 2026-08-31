"""Live, experiment-local post-write dependencies for a later CORE_ONLY run.

This module intentionally does not reuse the inert B5 construction posture in
``real_n0``.  Its objects are retained only in a mutable formal arm (or in
memory for preflight) and are never production Fabric owners or registries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import numpy as np

from torment_service.embeddings import HashEmbedding
from torment_service.fabric import _detect_canon_conflict, _proposal_allowed
from torment_service.substrate.fabric_native_routing import NativeFabricRoutingScope
from torment_service.substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from torment_service.substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
)
from torment_service.substrate.object_revision_governance import NativeMemoryGovernanceFacts
from torment_service.substrate.runtime_binding import NativeRepresentationLane

from .protocol import D1ProtocolError


class FormalPostWriteDependencyError(D1ProtocolError):
    """The experiment-local live dependency posture is incomplete or altered."""


# Frozen verbatim from the admitted CORE_ONLY L0 research policy.  It is
# deliberately not a generic A3D10 synthetic policy.
_FROZEN_RESEARCH_POLICY = {
    "auto_merge_entropy_trigger": 0.8,
    "auto_merge_motifs": False,
    "auto_propose_max_per_window": 8,
    "auto_propose_min_confidence": 0.7,
    "auto_propose_min_gap_s": 10,
    "auto_propose_min_promotion": 0.78,
    "auto_propose_min_strength": 0.8,
    "auto_propose_require_novelty": False,
    "bridge_peek_requires_approval": False,
    "motif_entropy_high": 0.72,
    "motif_entropy_target_n": 24,
    "motif_merge_max_suggestions": 20,
    "motif_merge_similarity": 0.93,
    "shared_min_distinct_agents": 2,
}

_FROZEN_IDENTITY_SEED = {
    "d1_baseline_profile": "core_character_free",
    # The source identity relies on this production default when absent.  Make
    # it explicit here so the experimental proposal boundary is deterministic.
    "coupling_mode": "read_only",
}

_FROZEN_IDENTITY_OVERLAY = {
    "contradiction_sensitivity": 0.8,
    "coupling_strength": 0.25,
    "decay_scale": 1.0,
    "motif_sensitivity": 0.7,
    "novelty_bias": 0.5,
    "promotion_bias": 0.6,
    "reinforcement_gain": 0.9,
    "shared_trust": 0.6,
    "stability_guard": 0.8,
    "write_threshold": 0.45,
}


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _copy_json(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(_json_value(dict(value)), sort_keys=True))


class FormalDerivedMemorySideStore:
    """Arm-local retained anchor and affect state; ``None`` is preflight-only."""

    def __init__(self, root: Path | None) -> None:
        self._root = root.resolve() if root is not None else None
        self._anchor: dict[str, Any] = {"motifs": {}}
        self._affect: dict[str, Any] = {
            "last_tag": None, "last_conf": 0.0, "last_step": -10**9, "drift_hist": [],
        }

    def load_anchor_state(self, **_kwargs: Any) -> Mapping[str, Any]:
        return self._load("anchor_state.json", self._anchor)

    def save_anchor_state(self, *, state: Mapping[str, Any], **_kwargs: Any) -> None:
        self._anchor = _copy_json(state)
        self._save("anchor_state.json", self._anchor)

    def load_affect_state(self, **_kwargs: Any) -> Mapping[str, Any]:
        return self._load("affect_state.json", self._affect)

    def save_affect_state(self, *, state: Mapping[str, Any], **_kwargs: Any) -> None:
        self._affect = _copy_json(state)
        self._save("affect_state.json", self._affect)

    def _load(self, name: str, fallback: Mapping[str, Any]) -> Mapping[str, Any]:
        if self._root is None:
            return _copy_json(fallback)
        path = self._root / name
        if not path.is_file():
            return _copy_json(fallback)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FormalPostWriteDependencyError("FORMAL_POST_WRITE_EXTERNAL_DEPENDENCIES_INVALID: unreadable side state") from exc
        if not isinstance(value, dict):
            raise FormalPostWriteDependencyError("FORMAL_POST_WRITE_EXTERNAL_DEPENDENCIES_INVALID: invalid side state")
        return _copy_json(value)

    def _save(self, name: str, value: Mapping[str, Any]) -> None:
        if self._root is None:
            return
        self._root.mkdir(parents=True, exist_ok=True)
        (self._root / name).write_text(
            json.dumps(dict(value), sort_keys=True, separators=(",", ":")), encoding="utf-8",
        )


class FormalConflictSurface:
    """Retains each qualified conflict effect inside one mutable formal arm."""

    def __init__(self, root: Path | None) -> None:
        self._root = root.resolve() if root is not None else None
        self.records: list[dict[str, Any]] = []

    def add(self, **kwargs: Any) -> None:
        record = _copy_json(kwargs)
        self.records.append(record)
        if self._root is not None:
            self._root.mkdir(parents=True, exist_ok=True)
            with (self._root / "conflicts.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


class FormalProposalSurface:
    """Arm-local proposal registry for structurally executable proposal calls."""

    def __init__(self, root: Path | None) -> None:
        self._root = root.resolve() if root is not None else None
        self.records: list[dict[str, Any]] = []

    def submit(self, **kwargs: Any) -> Any:
        record = _copy_json(kwargs)
        self.records.append(record)
        proposal_id = f"formal-proposal-{len(self.records)}"
        if self._root is not None:
            self._root.mkdir(parents=True, exist_ok=True)
            with (self._root / "proposals.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        return SimpleNamespace(proposal_id=proposal_id)


@dataclass
class _FormalIdentityStore:
    root: Path | None
    saved: list[dict[str, Any]] = field(default_factory=list)

    def save(self, identity: Any) -> None:
        value = {
            "seed": _copy_json(identity.seed),
            "overlay": _copy_json(identity.overlay),
        }
        self.saved.append(value)
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / "identity.json").write_text(
                json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8",
            )


class _FormalCollectiveField:
    def append_packet(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class _FormalProposalBridge:
    def maybe_draft_proposal(self, **_kwargs: Any) -> None:
        return None


class _FormalOwner:
    """Complete owner shape with the frozen CORE_ONLY features disabled."""

    def __init__(self, root: Path | None) -> None:
        self._log = logging.getLogger("torment.d1.formal.post_write")
        self._srg_enable = False
        self._hivemind_enable = False
        self._hivemind_telemetry_enable = False
        self._character_enable = False
        self._character_drift_every = 25
        self._compress_enable = False
        self._compress_min_step = 100
        self._checkpoint_enable = False
        self._checkpoint_interval = 500
        self._checkpoint_max_keep = 10
        self._last_drift_was_high: dict[tuple[str, str], bool] = {}
        self.drift_reflex_callback = None
        self.character_store = SimpleNamespace(load_state=lambda *_args: None)
        self.ident_store = _FormalIdentityStore(root)
        self.data_dir = str(root) if root is not None else ""
        self._field = _FormalCollectiveField()
        self._proposal_bridge = _FormalProposalBridge()

    def _get_collective_field(self, _workspace_id: str) -> _FormalCollectiveField:
        return self._field

    def _get_proposal_bridge(self, _workspace_id: str) -> _FormalProposalBridge:
        return self._proposal_bridge

    def _emit_hivemind_packet_telemetry(self, **_kwargs: Any) -> None:
        return None


def build_formal_native_post_write_configuration(
    *,
    routing_scope: NativeFabricRoutingScope,
    lane: NativeRepresentationLane,
    mutable_arm_root: Path | None,
) -> NativePostWriteQualificationConfiguration:
    """Return the complete frozen CORE_ONLY live posture for one formal arm.

    ``mutable_arm_root`` is required for live replay and intentionally omitted
    by the pre-execution validator over the frozen N0 source.
    """
    root = mutable_arm_root.resolve() if mutable_arm_root is not None else None
    side_root = root / "formal_post_write" if root is not None else None
    owner = _FormalOwner(side_root)
    conflict = FormalConflictSurface(side_root)
    proposal = FormalProposalSurface(side_root)
    workspace = SimpleNamespace(
        domain_policies={"research": dict(_FROZEN_RESEARCH_POLICY)},
        conflicts={"research": conflict},
        proposals={"research": proposal},
    )
    identity = SimpleNamespace(seed=dict(_FROZEN_IDENTITY_SEED), overlay=dict(_FROZEN_IDENTITY_OVERLAY))
    hash_embedder = HashEmbedding(dim=lane.dimension, salt="torment")
    scope = routing_scope.runtime_scope
    template = NativeDerivedMemoryRuntimeConfiguration(
        workspace_id=scope.workspace_id,
        agent_id=scope.agent_id or "d1coreagent",
        domain_id="research",
        legacy_source_namespace_id=scope.legacy_source_namespace_id,
        motif_alias_namespace_id=routing_scope.motif_alias_namespace_id,
        memory_identity_namespace_id=scope.identity_namespace_id,
        semantic_scope_id=scope.semantic_scope_id,
        idempotency_namespace_id=routing_scope.idempotency_namespace_id,
        parent_native_operation_key="D1:FORMAL:POST_WRITE:TEMPLATE",
        expected_dimension=lane.dimension,
        embed=hash_embedder.embed,
        embedder_provider=hash_embedder.provider,
        embedder_model=hash_embedder.model,
        side_store=FormalDerivedMemorySideStore(side_root),
        governance=NativeMemoryGovernanceFacts(),
    )
    configuration = NativePostWriteQualificationConfiguration(
        routing_scope=routing_scope,
        profile=NativePostWriteQualificationProfile.core_staging(),
        external=NativePostWriteExternalDependencies(
            owner=owner,
            workspace=workspace,
            identity=identity,
            agent_key=scope.agent_id or "d1coreagent",
            detect_canon_conflict=_detect_canon_conflict,
            proposal_allowed=_proposal_allowed,
            hivemind_log=logging.getLogger("torment.d1.formal.hivemind"),
        ),
        derived_runtime_template=template,
        motif_suggestion_maintenance_required=False,
        persistent_trajectory_evidence_required=False,
        checkpoint_snapshots_required=False,
        bridge_suggestions_required=False,
        deep_memory_required=False,
    )
    validate_formal_post_write_external_dependencies(configuration)
    return configuration


def validate_formal_post_write_external_dependencies(
    configuration: NativePostWriteQualificationConfiguration,
) -> None:
    """Refuse incomplete formal dependencies before any route or post-write call."""
    failures: list[str] = []
    if not isinstance(configuration, NativePostWriteQualificationConfiguration):
        failures.append("configuration")
    else:
        external = configuration.external
        owner = external.owner
        workspace = external.workspace
        identity = external.identity
        for name in (
            "_log", "_srg_enable", "_hivemind_enable", "_hivemind_telemetry_enable",
            "_character_enable", "_character_drift_every", "_compress_enable", "_compress_min_step",
            "_checkpoint_enable", "_checkpoint_interval", "character_store", "ident_store",
        ):
            if not hasattr(owner, name):
                failures.append(f"owner.{name}")
        for name in ("_get_collective_field", "_get_proposal_bridge", "_emit_hivemind_packet_telemetry"):
            if not callable(getattr(owner, name, None)):
                failures.append(f"owner.{name}")
        if not callable(getattr(getattr(owner, "_log", None), "debug", None)):
            failures.append("owner._log.debug")
        if not callable(getattr(getattr(owner, "character_store", None), "load_state", None)):
            failures.append("owner.character_store.load_state")
        if not callable(getattr(getattr(owner, "ident_store", None), "save", None)):
            failures.append("owner.ident_store.save")
        if not hasattr(workspace, "domain_policies") or not isinstance(workspace.domain_policies, Mapping):
            failures.append("workspace.domain_policies")
        if not hasattr(workspace, "conflicts") or not isinstance(workspace.conflicts, Mapping):
            failures.append("workspace.conflicts")
        if not hasattr(workspace, "proposals") or not isinstance(workspace.proposals, Mapping):
            failures.append("workspace.proposals")
        policy = workspace.domain_policies.get("research") if hasattr(workspace, "domain_policies") else None
        if policy != _FROZEN_RESEARCH_POLICY:
            failures.append("workspace.domain_policies.research")
        if not isinstance(policy, Mapping) or bool(policy.get("auto_merge_motifs", True)):
            failures.append("workspace.domain_policies.research.auto_merge_motifs")
        conflict = workspace.conflicts.get("research") if hasattr(workspace, "conflicts") else None
        proposal = workspace.proposals.get("research") if hasattr(workspace, "proposals") else None
        if not callable(getattr(conflict, "add", None)):
            failures.append("workspace.conflicts.research.add")
        if not callable(getattr(proposal, "submit", None)):
            failures.append("workspace.proposals.research.submit")
        if not isinstance(getattr(identity, "seed", None), Mapping):
            failures.append("identity.seed")
        elif identity.seed.get("coupling_mode") != "read_only":
            failures.append("identity.seed.coupling_mode")
        if not isinstance(getattr(identity, "overlay", None), Mapping):
            failures.append("identity.overlay")
        if not callable(external.detect_canon_conflict):
            failures.append("detect_canon_conflict")
        if not callable(external.proposal_allowed):
            failures.append("proposal_allowed")
        if not callable(getattr(external.hivemind_log, "exception", None)):
            failures.append("hivemind_log.exception")
        template = configuration.derived_runtime_template
        for name in ("load_anchor_state", "save_anchor_state", "load_affect_state", "save_affect_state"):
            if not callable(getattr(template.side_store, name, None)):
                failures.append(f"derived_side_store.{name}")
        if not callable(template.embed):
            failures.append("derived_embed")
        disabled_owner_values = {
            "_character_enable": False,
            "_compress_enable": False,
            "_checkpoint_enable": False,
            "_srg_enable": False,
            "_hivemind_enable": False,
            "_hivemind_telemetry_enable": False,
        }
        for name, expected in disabled_owner_values.items():
            if getattr(owner, name, None) is not expected:
                failures.append(f"owner.{name}")
        for name, minimum in (
            ("_character_drift_every", 1), ("_compress_min_step", 0), ("_checkpoint_interval", 1),
        ):
            value = getattr(owner, name, None)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                failures.append(f"owner.{name}")
        if (
            configuration.motif_suggestion_maintenance_required
            or configuration.persistent_trajectory_evidence_required
            or configuration.checkpoint_snapshots_required
            or configuration.bridge_suggestions_required
            or configuration.deep_memory_required
        ):
            failures.append("frozen_feature_posture")
    if failures:
        raise FormalPostWriteDependencyError(
            "FORMAL_POST_WRITE_EXTERNAL_DEPENDENCIES_INVALID: " + ", ".join(sorted(set(failures)))
        )


__all__ = [
    "FormalConflictSurface",
    "FormalDerivedMemorySideStore",
    "FormalPostWriteDependencyError",
    "FormalProposalSurface",
    "build_formal_native_post_write_configuration",
    "validate_formal_post_write_external_dependencies",
]
