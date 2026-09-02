"""One read-only-selected public memory runtime per canonical data root.

The durable B5 deployment resolver chooses the public memory authority.  This
module consumes that decision; it never initializes or mutates selector/core
state, and it contains no request-controlled backend choice.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import logging
import os
from pathlib import Path
import threading
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np

from .conflicts import CanonConflict
from .fabric import (
    DEFAULT_DOMAIN_POLICIES,
    DomainScore,
    TormentFabric,
    _detect_canon_conflict,
    _load_affect_state,
    _load_anchor_state,
    _save_affect_state,
    _save_anchor_state,
)
from .ingest_orchestration import PreparedFabricIngest
from .query_read_model import _private_motif_domains
from .substrate.deployment_selector import resolve_deployment_agreement
from .substrate.deployment_types import (
    DeploymentResolutionMode,
    QualifiedDeploymentProfile,
)
from .substrate.native_derived_memory_runtime import NativeDerivedMemoryRuntimeConfiguration
from .substrate.native_post_write_runtime import (
    NativePostWriteExternalDependencies,
    NativePostWriteQualificationConfiguration,
    NativePostWriteQualificationProfile,
    NativeSharedTriggerMoodDriftBinding,
)
from .substrate.native_public_ingest_executor import (
    NativePublicIngestExecutor,
    NativePublicIngestRequest,
)
from .substrate.production_native_owner import NativeProductionResourceOwner


_LOG = logging.getLogger("torment.public_runtime")


class PublicRuntimeMode(str, Enum):
    LEGACY = "LEGACY"
    NATIVE = "NATIVE"


class PublicRuntimeStartupRefused(RuntimeError):
    """The durable deployment authority does not permit public startup."""

    status_code = 503


class NativePublicOperationRefused(RuntimeError):
    """A native public route is not qualified for this operation."""

    status_code = 409


@dataclass(frozen=True)
class PublicRuntimeConfiguration:
    """Host-supplied, non-transport facts needed to consume NATIVE_AGREEMENT.

    The selector remains the sole authority for LEGACY versus NATIVE.  These
    facts only let the already-selected active core prove its profile and
    admission descriptor.  A caller request, environment backend flag, or
    workspace/agent field cannot populate this object.
    """

    effective_profile: QualifiedDeploymentProfile
    admission_descriptor_path: Path | str

    def __post_init__(self) -> None:
        if not isinstance(self.effective_profile, QualifiedDeploymentProfile):
            raise ValueError("public runtime requires a qualified deployment profile")
        path = Path(self.admission_descriptor_path).expanduser().resolve()
        if path.is_symlink() or not path.is_file():
            raise ValueError("public runtime admission descriptor must be a real file")
        object.__setattr__(self, "admission_descriptor_path", path)


_HOST_PROFILE_ENV = "TORMENT_DEPLOYMENT_PROFILE_JSON"
_HOST_DESCRIPTOR_ENV = "TORMENT_ADMISSION_DESCRIPTOR_PATH"
_HOST_PROFILE_FIELDS = frozenset({
    "compression_enabled",
    "deep_memory_enabled",
    "representation_provider",
    "representation_model",
    "representation_dimension",
    "admitted_scope_plan_digest",
    "external_owner_digest",
})


def load_public_runtime_configuration_from_host_environment() -> PublicRuntimeConfiguration | None:
    """Load explicit host proof facts without offering a backend override.

    The two values are intentionally all-or-nothing.  They are consumed only
    after the durable resolver has made its disposition: no environment value
    can ask for LEGACY or NATIVE.  The error text is deliberately value-free
    because these facts may be supplied by an operations environment.
    """

    profile_text = os.environ.get(_HOST_PROFILE_ENV)
    descriptor_path = os.environ.get(_HOST_DESCRIPTOR_ENV)
    if profile_text is None and descriptor_path is None:
        return None
    if not profile_text or not descriptor_path:
        raise PublicRuntimeStartupRefused("host deployment proof configuration is incomplete")
    try:
        payload = json.loads(profile_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise PublicRuntimeStartupRefused("host deployment proof configuration is invalid") from exc
    if not isinstance(payload, Mapping) or set(payload) != _HOST_PROFILE_FIELDS:
        raise PublicRuntimeStartupRefused("host deployment proof configuration is invalid")
    try:
        profile = QualifiedDeploymentProfile(**dict(payload))
        return PublicRuntimeConfiguration(
            effective_profile=profile,
            admission_descriptor_path=descriptor_path,
        )
    except Exception as exc:
        # QualifiedDeploymentProfile intentionally raises its own detailed
        # deployment errors.  Keep those details out of a host-facing startup
        # channel and never echo environment values or descriptor paths.
        raise PublicRuntimeStartupRefused("host deployment proof configuration is invalid") from exc


class _ReadOnlyBridges:
    """Minimal read-only bridge projection; it never creates bridge storage."""

    def __init__(self, path: Path) -> None:
        self._bridges: tuple[dict[str, Any], ...] = _read_bridges(path)

    def relevant_to_domains(self, domains: list[str], top_k: int = 8) -> list[dict[str, Any]]:
        domain_set = set(domains)
        matched = [
            dict(item) for item in self._bridges
            if item.get("from_domain") in domain_set or item.get("to_domain") in domain_set
        ]
        matched.sort(key=lambda item: float(item.get("confidence", 0.0) or 0.0), reverse=True)
        return matched[:max(0, int(top_k))]


class _ReadOnlyConflictRegistry:
    """Replay the external conflict log without constructing its writer."""

    def __init__(self, domain_root: Path) -> None:
        self._conflicts_path = domain_root / "conflicts.jsonl"
        self._events_path = domain_root / "conflict_events.jsonl"

    def list(self, status: str = "open", limit: int = 200) -> list[CanonConflict]:
        latest: dict[str, CanonConflict] = {}
        for path, is_event in ((self._conflicts_path, False), (self._events_path, True)):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                continue
            except (OSError, UnicodeDecodeError) as exc:
                raise NativePublicOperationRefused("native public conflict evidence is unreadable") from exc
            for line in lines:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise NativePublicOperationRefused("native public conflict evidence is malformed") from exc
                if not isinstance(payload, dict):
                    raise NativePublicOperationRefused("native public conflict evidence is malformed")
                if not is_event:
                    try:
                        conflict = CanonConflict(**payload)
                    except TypeError as exc:
                        raise NativePublicOperationRefused("native public conflict evidence is malformed") from exc
                    latest[conflict.conflict_id] = conflict
                    continue
                conflict = latest.get(str(payload.get("conflict_id") or ""))
                if conflict is None:
                    continue
                decision = str(payload.get("decision") or "").strip().lower()
                conflict.decision = decision
                conflict.note = payload.get("note")
                try:
                    conflict.decided_ts = int(payload.get("ts"))
                except (TypeError, ValueError):
                    raise NativePublicOperationRefused("native public conflict evidence is malformed") from None
                if decision in {"keep_a", "keep_b", "merge", "demote_both"}:
                    conflict.status = "resolved"
                elif decision == "fork":
                    conflict.status = "forked"
                elif decision == "reject":
                    conflict.status = "rejected"
        values = [item for item in latest.values() if status == "any" or item.status == status]
        values.sort(key=lambda item: item.created_ts, reverse=True)
        return values[:max(0, int(limit))]


class _NativeDomainRouter:
    """Existing cosine/stable domain-ranking law over request-scoped native geometry."""

    def __init__(self, owner: NativeProductionResourceOwner, embedder: Any, domains: tuple[str, ...]) -> None:
        self._owner = owner
        self._embedder = embedder
        self._domains = domains

    def rank_domains(self, vector: Any, top_k: int = 2) -> list[DomainScore]:
        incoming = np.asarray(vector, dtype=np.float32).reshape(-1)
        scores: list[DomainScore] = []
        with self._owner.open_query_context(embedder=self._embedder) as query:
            for domain_id in self._domains:
                centroid = np.asarray(query.domain_geometry(domain_id).centroid, dtype=np.float32).reshape(-1)
                if centroid.size != incoming.size:
                    raise ValueError("native domain geometry dimension mismatch")
                denom = float(np.linalg.norm(incoming) * np.linalg.norm(centroid))
                score = 0.0 if denom <= 0.0 else float(np.dot(incoming, centroid) / denom)
                scores.append(DomainScore(domain_id=domain_id, score=score))
        scores.sort(key=lambda item: item.score, reverse=True)
        return scores[:max(0, int(top_k))]


@dataclass(frozen=True)
class NativePublicWorkspaceView:
    """Inert external/workspace compatibility facts for Fabric cognition.

    The view deliberately exposes domain names, policies, and read-only bridge
    data but contains no legacy shared graph, motif registry, or writer.
    """

    data_dir: str
    workspace_id: str
    embed_dim: int
    domains: tuple[str, ...]
    private_motif_domains: tuple[str, ...]
    domain_policies: Mapping[str, Mapping[str, Any]]
    router: _NativeDomainRouter
    bridges: _ReadOnlyBridges
    conflicts: Mapping[str, _ReadOnlyConflictRegistry]
    meta: Mapping[str, Any]

    @property
    def shared_graphs(self) -> Mapping[str, None]:
        return MappingProxyType({domain: None for domain in self.domains})

    @property
    def motif_regs(self) -> Mapping[str, None]:
        # Fabric preparation only needs the pre-admitted motif-domain names.
        # Private motif domains deliberately do not appear in shared_graphs:
        # native query may only open an admitted shared native lane there.
        return MappingProxyType({
            domain: None
            for domain in (*self.domains, *self.private_motif_domains)
        })


class _FabricDerivedMemorySideStore:
    """Bind existing non-core side stores without granting graph authority."""

    def __init__(self, fabric: TormentFabric) -> None:
        self._fabric = fabric

    def load_anchor_state(self, *, workspace_id: str, agent_id: str) -> Mapping[str, Any]:
        return _load_anchor_state(self._fabric.data_dir, workspace_id, agent_id)

    def save_anchor_state(self, *, workspace_id: str, agent_id: str, state: Mapping[str, Any]) -> None:
        _save_anchor_state(self._fabric.data_dir, workspace_id, agent_id, dict(state))

    def load_affect_state(self, *, workspace_id: str, agent_id: str) -> Mapping[str, Any]:
        return _load_affect_state(self._fabric.data_dir, workspace_id, agent_id)

    def save_affect_state(self, *, workspace_id: str, agent_id: str, state: Mapping[str, Any]) -> None:
        _save_affect_state(self._fabric.data_dir, workspace_id, agent_id, dict(state))


class PublicTormentRuntime:
    """Authoritative public facade; legacy is delegated and native is explicit."""

    def __init__(
        self,
        *,
        mode: PublicRuntimeMode,
        cognition_fabric: TormentFabric,
        native_owner: NativeProductionResourceOwner | None = None,
    ) -> None:
        self.mode = mode
        self.cognition_fabric = cognition_fabric
        self.native_owner = native_owner
        self._closed = False

    @property
    def native_mode(self) -> bool:
        return self.mode is PublicRuntimeMode.NATIVE

    @property
    def data_dir(self) -> str:
        return self.cognition_fabric.data_dir

    @property
    def kernel(self) -> Any:
        return self.cognition_fabric.kernel

    @property
    def locks(self) -> Any:
        return self.cognition_fabric.locks

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self.native_owner is not None:
                self.native_owner.close()
        finally:
            self.cognition_fabric.close()

    def preflight_spine_operation(
        self,
        operation: str,
        *,
        idempotency_key: str | None = None,
        path: str | None = None,
    ) -> None:
        """Legacy has no new preflight; subclasses constrain native routes."""

    def __getattr__(self, name: str) -> Any:
        return getattr(self.cognition_fabric, name)


class NativePublicTormentRuntime(PublicTormentRuntime):
    """NATIVE_AGREEMENT runtime using R2 ingest and B5-A3 query contexts."""

    _SUPPORTED_SPINE_OPERATIONS = frozenset({"ingest", "tool_result_ingest", "query_memory"})
    _KEYED_MUTATIONS = frozenset({"ingest", "tool_result_ingest"})

    def __init__(self, *, cognition_fabric: TormentFabric, native_owner: NativeProductionResourceOwner) -> None:
        super().__init__(
            mode=PublicRuntimeMode.NATIVE,
            cognition_fabric=cognition_fabric,
            native_owner=native_owner,
        )
        self._workspace_views: dict[str, NativePublicWorkspaceView] = {}
        self._side_store = _FabricDerivedMemorySideStore(cognition_fabric)
        self._executor = NativePublicIngestExecutor(
            owner=native_owner,
            fabric=cognition_fabric,
            post_write_configuration=self._post_write_configuration,
            preparation_context=self._preparation_context,
        )

    @property
    def private_graphs(self) -> Mapping[str, Any]:
        raise NativePublicOperationRefused("native public runtime refuses legacy private MemoryGraph access")

    def preflight_spine_operation(
        self,
        operation: str,
        *,
        idempotency_key: str | None = None,
        path: str | None = None,
    ) -> None:
        if operation not in self._SUPPORTED_SPINE_OPERATIONS:
            raise NativePublicOperationRefused(
                f"native public operation '{operation}' is refused before effect"
            )
        if path is not None and path != "fast":
            raise NativePublicOperationRefused(
                f"native public operation '{operation}' has no qualified full-cognition transport route"
            )
        if operation in self._KEYED_MUTATIONS and not idempotency_key:
            raise NativePublicOperationRefused(
                "native public mutation requires Idempotency-Key before cognition"
            )

    def create_agent(self, workspace_id: str, agent_id: str, seed: Mapping[str, Any] | None = None) -> Any:
        if seed is not None:
            raise NativePublicOperationRefused("native public agent creation is refused before legacy graph creation")
        return self._prepare_native_agent(workspace_id, agent_id)

    def get_workspace(self, workspace_id: str, domains: list[str] | None = None) -> NativePublicWorkspaceView:
        view = self._workspace_view(workspace_id)
        if domains is not None and tuple(domains) != view.domains:
            raise NativePublicOperationRefused("native public workspace domain mutation is refused before effect")
        return view

    def ingest(self, workspace_id: str, agent_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        key = kwargs.pop("public_mutation_key", None)
        self.preflight_spine_operation("ingest", idempotency_key=key, path="fast")
        scope = kwargs.pop("scope", "private")
        domain_id = kwargs.pop("domain_id", None)
        if scope == "private":
            admitted_domain = self._private_motif_domain(workspace_id, agent_id)
            if domain_id is None:
                # B5-A3's recovered private lane has one explicit motif
                # domain.  Allowing generic shared-domain routing to select a
                # different tag would make the native lane unreadable.
                domain_id = admitted_domain
            elif domain_id != admitted_domain:
                raise NativePublicOperationRefused(
                    "native private ingest domain differs from the admitted private motif domain"
                )
        elif scope == "shared":
            if not isinstance(domain_id, str) or not domain_id:
                raise NativePublicOperationRefused(
                    "native shared ingest requires an explicit admitted domain before cognition"
                )
            self._require_shared_scope(workspace_id, domain_id)
        else:
            raise NativePublicOperationRefused("native public ingest scope is not admitted")
        view = self._workspace_view(workspace_id)
        if bool(view.domain_policies.get(domain_id, {}).get("auto_merge_motifs", False)):
            raise NativePublicOperationRefused(
                "native public ingest refuses an unqualified auto-merge motif policy before cognition"
            )
        request = NativePublicIngestRequest(
            workspace_id=workspace_id,
            agent_id=agent_id,
            text=text,
            public_mutation_key=str(key),
            step=int(kwargs.pop("step", 0)),
            domain_id=domain_id,
            tri_mod=kwargs.pop("tri_mod", None),
            supplied_summary=kwargs.pop("supplied_summary", None),
            supplied_embedding=kwargs.pop("supplied_embedding", None),
            scope=scope,
            provenance=kwargs.pop("provenance", None),
            memory_class=kwargs.pop("memory_class", "core"),
            extra_payload=kwargs.pop("extra_payload", None),
            skip_packet_emission=bool(kwargs.pop("skip_packet_emission", False)),
            suppress_canon=bool(kwargs.pop("suppress_canon", False)),
        )
        if kwargs:
            raise TypeError(f"unsupported native public ingest arguments: {sorted(kwargs)}")
        return self._executor.execute(request)

    def query(
        self,
        workspace_id: str,
        agent_id: str,
        query_text: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        self.preflight_spine_operation("query_memory", path="fast")
        identity = self._prepare_native_agent(workspace_id, agent_id)
        view = self._workspace_view(workspace_id)
        with self.native_owner.open_query_context(embedder=self.cognition_fabric.kernel.embedder) as read_model:  # type: ignore[union-attr]
            return self.cognition_fabric.query(
                workspace_id=workspace_id,
                agent_id=agent_id,
                query_text=query_text,
                _qualification_read_model=read_model,  # NativeProductionQueryContext has this qualified surface.
                _native_workspace_view=view,
                _native_identity=identity,
                _native_public=True,
                **kwargs,
            )

    def _preparation_context(self, request: NativePublicIngestRequest) -> Mapping[str, Any]:
        return {
            "_native_workspace_view": self._workspace_view(request.workspace_id),
            "_native_identity": self._prepare_native_agent(request.workspace_id, request.agent_id),
            "_native_public": True,
        }

    def _prepare_native_agent(self, workspace_id: str, agent_id: str) -> Any:
        runtime = self.native_owner._recover_active_runtime()  # type: ignore[union-attr]
        try:
            scope = runtime.lookup_private(agent_id).fabric_routing_scope
        except Exception as exc:
            raise NativePublicOperationRefused("native public agent scope is not admitted") from exc
        if scope.runtime_scope.workspace_id != workspace_id:
            raise NativePublicOperationRefused("native public workspace is not admitted")
        return self.cognition_fabric.prepare_native_cognition_agent(workspace_id, agent_id)

    def _private_motif_domain(self, workspace_id: str, agent_id: str) -> str:
        runtime = self.native_owner._recover_active_runtime()  # type: ignore[union-attr]
        try:
            scope = runtime.lookup_private(agent_id).memory_runtime_scope
            domain = _private_motif_domains(runtime)[agent_id]
        except Exception as exc:
            raise NativePublicOperationRefused("native private motif domain is not admitted") from exc
        if scope.workspace_id != workspace_id:
            raise NativePublicOperationRefused("native public workspace is not admitted")
        return domain

    def _require_shared_scope(self, workspace_id: str, domain_id: str) -> None:
        runtime = self.native_owner._recover_active_runtime()  # type: ignore[union-attr]
        try:
            scope = runtime.lookup_shared(domain_id).memory_runtime_scope
        except Exception as exc:
            raise NativePublicOperationRefused("native public shared domain is not admitted") from exc
        if scope.workspace_id != workspace_id:
            raise NativePublicOperationRefused("native public workspace is not admitted")

    def _workspace_view(self, workspace_id: str) -> NativePublicWorkspaceView:
        existing = self._workspace_views.get(workspace_id)
        if existing is not None:
            return existing
        runtime = self.native_owner._recover_active_runtime()  # type: ignore[union-attr]
        private_scopes = [
            item for item in runtime.scopes
            if item.memory_runtime_scope.scope_kind == "PRIVATE_AGENT"
        ]
        if (
            len(private_scopes) != 1
            or private_scopes[0].memory_runtime_scope.workspace_id != workspace_id
        ):
            raise NativePublicOperationRefused("native public workspace is not admitted")
        domains = tuple(
            item.memory_runtime_scope.domain_id or ""
            for item in runtime.scopes
            if item.memory_runtime_scope.scope_kind == "SHARED_DOMAIN"
        )
        if not domains or any(not item for item in domains):
            raise NativePublicOperationRefused("native public workspace has no admitted shared domains")
        try:
            private_motif_domains = tuple(sorted(set(_private_motif_domains(runtime).values())))
        except Exception as exc:
            raise NativePublicOperationRefused("native private motif-domain evidence is not admitted") from exc
        view = NativePublicWorkspaceView(
            data_dir=self.cognition_fabric.data_dir,
            workspace_id=workspace_id,
            embed_dim=int(runtime.representation_lane.dimension),
            domains=domains,
            private_motif_domains=private_motif_domains,
            domain_policies=_read_domain_policies(
                self.cognition_fabric.data_dir,
                workspace_id,
                tuple(dict.fromkeys((*domains, *private_motif_domains))),
            ),
            router=_NativeDomainRouter(self.native_owner, self.cognition_fabric.kernel.embedder, domains),  # type: ignore[arg-type]
            bridges=_ReadOnlyBridges(Path(self.cognition_fabric.data_dir) / "workspaces" / workspace_id / "bridges.json"),
            conflicts=MappingProxyType({
                domain: _ReadOnlyConflictRegistry(
                    Path(self.cognition_fabric.data_dir) / "workspaces" / workspace_id / "domains" / domain
                )
                for domain in domains
            }),
            meta=_read_workspace_meta(self.cognition_fabric.data_dir, workspace_id),
        )
        self._workspace_views[workspace_id] = view
        return view

    def _post_write_configuration(
        self, prepared: PreparedFabricIngest,
    ) -> NativePostWriteQualificationConfiguration:
        runtime = self.native_owner._recover_active_runtime()  # type: ignore[union-attr]
        private = runtime.lookup_private(prepared.agent_id).fabric_routing_scope
        scope = private if prepared.scope == "private" else runtime.lookup_shared(prepared.domain_id).fabric_routing_scope
        identity = self._prepare_native_agent(prepared.workspace_id, prepared.agent_id)
        view = self._workspace_view(prepared.workspace_id)
        external = NativePostWriteExternalDependencies(
            owner=self.cognition_fabric,
            workspace=view,
            identity=identity,
            agent_key=self.cognition_fabric._agent_key(prepared.workspace_id, prepared.agent_id),
            detect_canon_conflict=lambda incoming, existing, similarity: _detect_canon_conflict(
                incoming, existing, similarity,
            ),
            proposal_allowed=lambda *_args, **_kwargs: False,
            hivemind_log=_LOG,
            character_store=self.cognition_fabric.character_store,
            character_embedder=self.cognition_fabric.kernel.embedder,
        )
        template = NativeDerivedMemoryRuntimeConfiguration(
            workspace_id=prepared.workspace_id,
            agent_id=prepared.agent_id,
            domain_id=prepared.domain_id,
            legacy_source_namespace_id=private.runtime_scope.legacy_source_namespace_id,
            motif_alias_namespace_id=private.motif_alias_namespace_id,
            memory_identity_namespace_id=private.runtime_scope.identity_namespace_id,
            semantic_scope_id=private.runtime_scope.semantic_scope_id,
            idempotency_namespace_id=private.idempotency_namespace_id,
            parent_native_operation_key="public-native-post-write-template",
            expected_dimension=prepared.embedding_dimension,
            embed=self.cognition_fabric.kernel.embedder.embed,
            embedder_provider=prepared.embedding_provider,
            embedder_model=prepared.embedding_model,
            side_store=self._side_store,
        )
        if prepared.scope == "shared":
            return NativePostWriteQualificationConfiguration(
                routing_scope=scope,
                profile=NativePostWriteQualificationProfile.core_staging_with_shared_m1_mood_drift(),
                external=external,
                derived_runtime_template=None,
                motif_suggestion_maintenance_required=False,
                persistent_trajectory_evidence_required=False,
                checkpoint_snapshots_required=False,
                bridge_suggestions_required=False,
                deep_memory_required=False,
                shared_motif_suggestion_maintenance_required=True,
                shared_mood_drift_binding=NativeSharedTriggerMoodDriftBinding(private, template),
            )
        return NativePostWriteQualificationConfiguration(
            routing_scope=scope,
            profile=NativePostWriteQualificationProfile.core_staging(),
            external=external,
            derived_runtime_template=template,
            motif_suggestion_maintenance_required=False,
            persistent_trajectory_evidence_required=False,
            checkpoint_snapshots_required=False,
            bridge_suggestions_required=False,
            deep_memory_required=False,
        )


_RUNTIME_LOCK = threading.RLock()
_RUNTIME_CACHE: dict[Path, PublicTormentRuntime] = {}
_RUNTIME_CONFIGURATION: dict[Path, PublicRuntimeConfiguration] = {}


def configure_public_runtime(data_root: str | Path, configuration: PublicRuntimeConfiguration) -> None:
    """Register host configuration before startup; it cannot select a backend."""
    root = Path(data_root).expanduser().resolve()
    if not isinstance(configuration, PublicRuntimeConfiguration):
        raise ValueError("configuration must be PublicRuntimeConfiguration")
    with _RUNTIME_LOCK:
        current = _RUNTIME_CACHE.get(root)
        if current is not None:
            raise RuntimeError("public runtime is already constructed for this data root")
        _RUNTIME_CONFIGURATION[root] = configuration


def create_public_runtime(
    data_root: str | Path,
    configuration: PublicRuntimeConfiguration | None = None,
) -> PublicTormentRuntime:
    """Resolve durable deployment authority, then construct exactly one runtime."""
    root = Path(data_root).expanduser().resolve()
    with _RUNTIME_LOCK:
        configured = configuration or _RUNTIME_CONFIGURATION.get(root)
        cached = _RUNTIME_CACHE.get(root)
        if cached is not None:
            if configured is not None and cached.native_mode:
                owner = cached.native_owner
                if owner is None or owner._effective_profile != configured.effective_profile:  # exact host facts only
                    raise PublicRuntimeStartupRefused("existing public runtime has different qualified profile facts")
            return cached
        profile = configured.effective_profile if configured is not None else _legacy_compatibility_profile()
        resolution = resolve_deployment_agreement(data_root=root, effective_profile=profile)
        if resolution.mode is DeploymentResolutionMode.LEGACY_PUBLIC:
            runtime = PublicTormentRuntime(
                mode=PublicRuntimeMode.LEGACY,
                cognition_fabric=TormentFabric(data_dir=str(root)),
            )
        elif resolution.mode is DeploymentResolutionMode.NATIVE_AGREEMENT:
            if configured is None:
                raise PublicRuntimeStartupRefused("native public startup requires host-qualified profile and descriptor")
            fabric = TormentFabric(data_dir=str(root))
            try:
                owner = NativeProductionResourceOwner.from_native_agreement(
                    data_root=root,
                    effective_profile=configured.effective_profile,
                    agreement=resolution,
                    admission_descriptor_path=configured.admission_descriptor_path,
                    character_store=fabric.character_store,
                )
                runtime = NativePublicTormentRuntime(cognition_fabric=fabric, native_owner=owner)
            except Exception:
                fabric.close()
                raise
        else:
            raise PublicRuntimeStartupRefused(
                f"public startup refused by durable deployment authority: {resolution.reason}"
            )
        _RUNTIME_CACHE[root] = runtime
        return runtime


def close_public_runtime(data_root: str | Path) -> None:
    """Close and forget the one process/runtime owner for a canonical root."""
    root = Path(data_root).expanduser().resolve()
    with _RUNTIME_LOCK:
        runtime = _RUNTIME_CACHE.pop(root, None)
    if runtime is not None:
        runtime.close()


def reset_public_runtime_for_test(data_root: str | Path) -> None:
    """Test-only cache reset; it never changes selector/core deployment state."""
    root = Path(data_root).expanduser().resolve()
    close_public_runtime(root)
    with _RUNTIME_LOCK:
        _RUNTIME_CONFIGURATION.pop(root, None)


def _legacy_compatibility_profile() -> QualifiedDeploymentProfile:
    digest = hashlib.sha256(b"public-runtime-legacy-compatible-placeholder").hexdigest()
    return QualifiedDeploymentProfile(
        compression_enabled=False,
        deep_memory_enabled=False,
        representation_provider="legacy-placeholder",
        representation_model="legacy-placeholder",
        representation_dimension=1,
        admitted_scope_plan_digest=digest,
        external_owner_digest=digest,
    )


def _read_domain_policies(data_dir: str, workspace_id: str, domains: tuple[str, ...]) -> Mapping[str, Mapping[str, Any]]:
    path = Path(data_dir) / "workspaces" / workspace_id / "domain_policies.json"
    values: Mapping[str, Any] = {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping) and isinstance(payload.get("policies"), Mapping):
            values = payload["policies"]
    except FileNotFoundError:
        pass
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativePublicOperationRefused("native public domain policy evidence is unreadable") from exc
    return MappingProxyType({
        domain: MappingProxyType(dict(values.get(domain) or DEFAULT_DOMAIN_POLICIES.get(domain) or {}))
        for domain in domains
    })


def _read_workspace_meta(data_dir: str, workspace_id: str) -> Mapping[str, Any]:
    path = Path(data_dir) / "workspaces" / workspace_id / "workspace_meta.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return MappingProxyType({})
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativePublicOperationRefused("native public workspace metadata is unreadable") from exc
    if not isinstance(payload, Mapping):
        raise NativePublicOperationRefused("native public workspace metadata is malformed")
    return MappingProxyType(dict(payload))


def _read_bridges(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NativePublicOperationRefused("native public bridge evidence is unreadable") from exc
    items = payload.get("bridges", []) if isinstance(payload, Mapping) else []
    if not isinstance(items, list):
        raise NativePublicOperationRefused("native public bridge evidence is malformed")
    return tuple(dict(item) for item in items if isinstance(item, Mapping))


__all__ = [
    "NativePublicOperationRefused",
    "NativePublicTormentRuntime",
    "PublicRuntimeConfiguration",
    "PublicRuntimeMode",
    "PublicRuntimeStartupRefused",
    "PublicTormentRuntime",
    "close_public_runtime",
    "configure_public_runtime",
    "create_public_runtime",
    "load_public_runtime_configuration_from_host_environment",
    "reset_public_runtime_for_test",
]
