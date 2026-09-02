"""Qualified, backend-neutral read models for future query integration.

This module is intentionally a *qualification seam*.  It reproduces one
``MemoryGraph.search`` lane and exposes current motif read facts without
changing ``TormentFabric.query`` or selecting a production backend.  SQLite
remains the native authority; the native vector runtime is an independently
rebuildable candidate cache and this module does not add SQL ranking.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Protocol
from uuid import UUID

from .memory_graph import MemoryGraph
from .motif_decision import (
    CURRENT_MOTIF_DECISION_POLICY,
    MotifReadModel,
    motif_density,
    motif_gravity_bonus,
)
from .motif_geometry_port import (
    LegacyMotifGeometryAdapter,
    NativeMotifGeometryAdapter,
    RuntimeMotifGeometry,
)
from .motifs import MotifRegistry
from .scoring import QueryMemoryIdentity, qualified_query_memory_identity
from .substrate.native_memory_vector_runtime import NativeMemoryVectorRuntime
from .substrate.native_srg_runtime import (
    NativeSRGProcessState,
    NativeSRGTransientRuntime,
)


_PRIVATE = "private"
_SHARED = "shared"
_PRIVATE_AGENT_SCOPE = "PRIVATE_AGENT"
_SHARED_DOMAIN_SCOPE = "SHARED_DOMAIN"


class QualifiedQueryReadModelError(ValueError):
    """Raised when a backend cannot prove the qualified A2 read contract."""


@dataclass(frozen=True)
class QualifiedQueryMotifIdentity:
    """A motif ID qualified by its domain and (where native) semantic scope.

    ``motif_id`` is a compatibility value only.  Two domains are permitted to
    use the same string, so query consumers must carry this complete value
    instead of building a process-global ``dict[str, motif]``.
    """

    workspace_id: str
    domain_id: str
    motif_id: str
    semantic_scope_id: UUID | None = None


@dataclass(frozen=True)
class QualifiedQueryHit:
    """One legacy-shaped result plus non-public structural identity.

    ``compatibility_hit`` deliberately contains only the existing flattened
    search surface.  A later Fabric integration can pass a fresh copy of that
    surface to current ranking code while using ``memory_identity`` and
    ``motif_memberships`` internally for qualified joins.
    """

    compatibility_hit: Mapping[str, Any]
    memory_identity: QueryMemoryIdentity
    motif_memberships: tuple[QualifiedQueryMotifIdentity, ...]
    native_object_id: UUID | None = None
    native_revision_id: UUID | None = None

    def as_legacy_hit(self) -> dict[str, Any]:
        """Return a mutable compatibility copy without structural fields."""
        return dict(self.compatibility_hit)

    @property
    def motif_ids(self) -> tuple[str, ...]:
        """Compatibility motif IDs; callers requiring identity use memberships."""
        return tuple(item.motif_id for item in self.motif_memberships)


@dataclass(frozen=True)
class QualifiedMotifGeometry:
    """One geometry record whose motif cannot lose its source namespace."""

    identity: QualifiedQueryMotifIdentity
    geometry: RuntimeMotifGeometry


@dataclass(frozen=True)
class QualifiedDomainGeometry:
    """Current geometry for one explicitly admitted shared domain."""

    workspace_id: str
    domain_id: str
    semantic_scope_id: UUID | None
    centroid: tuple[float, ...]
    motifs: tuple[QualifiedMotifGeometry, ...]


class QualifiedQueryLane(Protocol):
    """The narrow search boundary for one already-qualified memory lane."""

    def search(
        self,
        query_text: str,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[QualifiedQueryHit, ...]: ...


class QualifiedQueryReadModel(Protocol):
    """Read-only contract retained for A3; it has no public-query authority."""

    def private_lane(self, workspace_id: str, agent_id: str) -> QualifiedQueryLane: ...

    def shared_lane(self, workspace_id: str, domain_id: str) -> QualifiedQueryLane: ...

    def domain_geometry(self, domain_id: str) -> QualifiedDomainGeometry: ...

    def active_motifs(self, domain_id: str, top_k: int = 8) -> list[dict[str, Any]]: ...


def _qualified_hit(
    hit: Mapping[str, Any],
    *,
    workspace_id: str,
    expected_scope: str,
    expected_qualifier: str,
    motif_memberships: tuple[QualifiedQueryMotifIdentity, ...],
    native_object_id: UUID | None = None,
    native_revision_id: UUID | None = None,
    identity_input: Mapping[str, Any] | None = None,
) -> QualifiedQueryHit:
    """Fail closed unless a flattened candidate proves its A1 identity."""
    compatibility = dict(hit)
    identity_candidate = dict(compatibility if identity_input is None else identity_input)
    identity = qualified_query_memory_identity(
        identity_candidate, expected_workspace_id=workspace_id,
    )
    if (
        identity is None
        or identity.scope != expected_scope
        or identity.qualifier != expected_qualifier
    ):
        raise QualifiedQueryReadModelError(
            "query hit does not prove its expected workspace/scope/qualifier"
        )
    return QualifiedQueryHit(
        MappingProxyType(compatibility), identity, motif_memberships,
        native_object_id, native_revision_id,
    )


def _legacy_memberships(
    registry: MotifRegistry,
    *,
    workspace_id: str,
) -> dict[int, tuple[QualifiedQueryMotifIdentity, ...]]:
    """Project current legacy memberships without changing registry state."""
    memberships: dict[int, list[QualifiedQueryMotifIdentity]] = {}
    for motif in registry.motifs.values():
        qualified = QualifiedQueryMotifIdentity(
            workspace_id, motif.domain_id, motif.motif_id,
        )
        for eid in motif.members:
            memberships.setdefault(int(eid), []).append(qualified)
    return {eid: tuple(values) for eid, values in memberships.items()}


def _active_summary(
    motifs: tuple[tuple[MotifReadModel, float], ...], *, top_k: int,
) -> list[dict[str, Any]]:
    """Project the exact local ``MotifRegistry.active`` field/order surface."""
    limit = int(top_k)
    ranked = sorted(
        motifs,
        key=lambda item: (
            float(item[0].strength) + motif_gravity_bonus(
                item[0], CURRENT_MOTIF_DECISION_POLICY,
            ),
            int(item[0].last_active_ts),
        ),
        reverse=True,
    )[:limit]
    return [
        {
            "motif_id": state.runtime_motif_id,
            "label": state.label,
            "strength": state.strength,
            "stability_score": state.stability_score,
            "density": motif_density(state.member_count),
            "gravity_bonus": motif_gravity_bonus(
                state, CURRENT_MOTIF_DECISION_POLICY,
            ),
            "radius": radius,
            "members": state.member_count,
        }
        for state, radius in ranked
    ]


class _LegacyQualifiedQueryLane:
    def __init__(
        self,
        graph: MemoryGraph,
        registry: MotifRegistry,
        *,
        workspace_id: str,
        scope: str,
        qualifier: str,
    ) -> None:
        self._graph = graph
        self._registry = registry
        self._workspace_id = workspace_id
        self._scope = scope
        self._qualifier = qualifier

    def search(
        self,
        query_text: str,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[QualifiedQueryHit, ...]:
        memberships = _legacy_memberships(self._registry, workspace_id=self._workspace_id)
        hits = self._graph.search(
            query_text, top_k=top_k, user_id=user_id, min_score=min_score,
            type_filter=list(type_filter) if type_filter is not None else None,
        )
        qualified: list[QualifiedQueryHit] = []
        for hit in hits:
            # Legacy public hits historically need not flatten their known
            # lane origin.  The adapter itself already owns that binding, so
            # use it only to construct the private A1 identity witness; do
            # not add fields to the compatibility hit that Fabric exposes.
            identity_input = dict(hit)
            identity_input.setdefault("workspace_id", self._workspace_id)
            identity_input.setdefault("scope", self._scope)
            if self._scope == _PRIVATE:
                identity_input.setdefault("agent_id", self._qualifier)
            else:
                identity_input.setdefault("domain_id", self._qualifier)
            qualified.append(_qualified_hit(
                hit,
                workspace_id=self._workspace_id,
                expected_scope=self._scope,
                expected_qualifier=self._qualifier,
                motif_memberships=memberships.get(int(hit["eid"]), ()),
                identity_input=identity_input,
            ))
        return tuple(qualified)


class LegacyQualifiedQueryReadModel:
    """A non-invasive reference implementation over legacy graph objects."""

    def __init__(
        self,
        workspace_id: str,
        *,
        private_graphs: Mapping[str, MemoryGraph],
        shared_graphs: Mapping[str, MemoryGraph],
        motif_registries: Mapping[str, MotifRegistry],
        private_motif_domains: Mapping[str, str],
        shared_domain_order: tuple[str, ...],
    ) -> None:
        _nonempty("workspace_id", workspace_id)
        if not isinstance(shared_domain_order, tuple) or not shared_domain_order:
            raise QualifiedQueryReadModelError("shared domain order must be explicit")
        if len(set(shared_domain_order)) != len(shared_domain_order):
            raise QualifiedQueryReadModelError("shared domain order contains duplicates")
        if tuple(shared_graphs) != shared_domain_order:
            raise QualifiedQueryReadModelError(
                "shared graph mapping must preserve explicit admitted domain order"
            )
        if set(shared_graphs) != set(shared_domain_order):
            raise QualifiedQueryReadModelError("shared graph/domain order mismatch")
        if set(private_graphs) != set(private_motif_domains):
            raise QualifiedQueryReadModelError("every private graph needs an explicit motif domain")
        required_motif_domains = set(private_motif_domains.values()) | set(shared_domain_order)
        if set(motif_registries) != required_motif_domains:
            raise QualifiedQueryReadModelError("motif registries must match admitted motif domains")
        self._workspace_id = workspace_id
        self._private = {
            agent_id: _LegacyQualifiedQueryLane(
                graph, motif_registries[private_motif_domains[agent_id]],
                workspace_id=workspace_id, scope=_PRIVATE, qualifier=agent_id,
            )
            for agent_id, graph in private_graphs.items()
        }
        self._shared = {
            domain_id: _LegacyQualifiedQueryLane(
                graph, motif_registries[domain_id], workspace_id=workspace_id,
                scope=_SHARED, qualifier=domain_id,
            )
            for domain_id, graph in shared_graphs.items()
        }
        self._registries = dict(motif_registries)
        self._geometry = LegacyMotifGeometryAdapter(
            {domain_id: motif_registries[domain_id] for domain_id in shared_domain_order}
        )
        self._geometry_dimension = _legacy_geometry_dimension(
            tuple(shared_graphs.values())
        )
        self._shared_domain_order = shared_domain_order

    def private_lane(self, workspace_id: str, agent_id: str) -> QualifiedQueryLane:
        self._require_workspace(workspace_id)
        try:
            return self._private[agent_id]
        except KeyError as exc:
            raise KeyError(f"private query lane is not admitted for agent {agent_id!r}") from exc

    def shared_lane(self, workspace_id: str, domain_id: str) -> QualifiedQueryLane:
        self._require_workspace(workspace_id)
        try:
            return self._shared[domain_id]
        except KeyError as exc:
            raise KeyError(f"shared query lane is not admitted for domain {domain_id!r}") from exc

    def domain_geometry(self, domain_id: str) -> QualifiedDomainGeometry:
        geometry = self._geometry
        motifs = geometry.list_motifs(domain_id)
        return QualifiedDomainGeometry(
            self._workspace_id,
            domain_id,
            None,
            tuple(float(value) for value in geometry.domain_centroid(domain_id, self._geometry_dimension)),
            tuple(
                QualifiedMotifGeometry(
                    QualifiedQueryMotifIdentity(self._workspace_id, item.domain_id, item.runtime_motif_id),
                    item,
                )
                for item in motifs
            ),
        )

    def active_motifs(self, domain_id: str, top_k: int = 8) -> list[dict[str, Any]]:
        registry = self._registry(domain_id)
        # Delegate to the local implementation to freeze every compatibility
        # quirk, including member-vector radius and Python stable ties.
        return registry.active(top_k=top_k)

    def domain_ids(self) -> tuple[str, ...]:
        return self._shared_domain_order

    def _registry(self, domain_id: str) -> MotifRegistry:
        try:
            return self._registries[domain_id]
        except KeyError as exc:
            raise KeyError(f"motif domain is not admitted: {domain_id!r}") from exc

    def _require_workspace(self, workspace_id: str) -> None:
        if workspace_id != self._workspace_id:
            raise QualifiedQueryReadModelError("query read model workspace mismatch")


class _NativeQualifiedQueryLane:
    def __init__(
        self,
        scope: Any,
        *,
        workspace_id: str,
        scope_name: str,
        qualifier: str,
        motif_domain_id: str,
        embedder: Any,
    ) -> None:
        self._scope = scope
        self._workspace_id = workspace_id
        self._scope_name = scope_name
        self._qualifier = qualifier
        self._motif_domain_id = motif_domain_id
        # Deliberately create the existing native vector runtime, not a
        # replacement SQL search path or a call to search_by_embedding.
        self._runtime: NativeMemoryVectorRuntime = scope.new_vector_runtime(embedder=embedder)

    def close(self) -> None:
        self._runtime.close()

    def search(
        self,
        query_text: str,
        *,
        top_k: int = 8,
        user_id: str | None = None,
        min_score: float | None = None,
        type_filter: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[QualifiedQueryHit, ...]:
        hits = self._runtime.search(
            query_text, top_k=top_k, user_id=user_id, min_score=min_score,
            type_filter=type_filter,
        )
        if not hits:
            return ()
        snapshot = self._runtime.snapshot
        rows = {} if snapshot is None else {row.eid: row for row in snapshot.rows}
        memberships = self._current_memberships()
        qualified: list[QualifiedQueryHit] = []
        for hit in hits:
            eid = int(hit["eid"])
            row = rows.get(eid)
            if row is None:
                raise QualifiedQueryReadModelError(
                    "native search hit is missing its current vector witness"
                )
            # Migration normally retains these flattened compatibility facts.
            # Direct native writers intentionally keep the lane scope as
            # substrate configuration, so derive only those lane-identity
            # facts from this already-qualified recovered binding when absent.
            # No caller-controlled value is replaced.
            compatibility = dict(hit)
            compatibility.setdefault("workspace_id", self._workspace_id)
            compatibility.setdefault("scope", self._scope_name)
            if self._scope_name == _PRIVATE:
                compatibility.setdefault("agent_id", self._qualifier)
            else:
                compatibility.setdefault("domain_id", self._qualifier)
            qualified.append(_qualified_hit(
                compatibility,
                workspace_id=self._workspace_id,
                expected_scope=self._scope_name,
                expected_qualifier=self._qualifier,
                motif_memberships=memberships.get(row.object_id, ()),
                native_object_id=row.object_id,
                native_revision_id=row.object_revision_id,
            ))
        return tuple(qualified)

    def _current_memberships(self) -> dict[UUID, tuple[QualifiedQueryMotifIdentity, ...]]:
        result: dict[UUID, list[QualifiedQueryMotifIdentity]] = {}
        routing = self._scope.fabric_routing_scope
        semantic_scope_id = self._scope.memory_runtime_scope.semantic_scope_id
        with self._scope.open_readers() as readers:
            motifs = readers.motifs.list_runtime_motifs(
                motif_alias_namespace_id=routing.motif_alias_namespace_id,
                domain_id=self._motif_domain_id,
                semantic_scope_id=semantic_scope_id,
            )
            for motif in motifs:
                identity = QualifiedQueryMotifIdentity(
                    self._workspace_id,
                    motif.read_model.domain_id,
                    motif.read_model.runtime_motif_id,
                    motif.semantic_scope_id,
                )
                for member in readers.motifs.list_ordered_current_motif_members(
                    motif.motif_object_id
                ):
                    result.setdefault(member.member_object_id, []).append(identity)
        return {object_id: tuple(values) for object_id, values in result.items()}


class NativeQualifiedQueryReadModel:
    """Read-only adapter over one recovered native multi-scope runtime.

    The constructor deliberately accepts a recovered-runtime shaped object so
    it can be characterized in isolation.  Production recovery provides the
    same shape; no connection, schema, or activation capability is accepted
    here.  Private motif domains come from the verified admission descriptor,
    never from a guessed agent/domain relationship.
    """

    def __init__(
        self,
        recovered_runtime: Any,
        *,
        embedder: Any,
        srg_process_state: NativeSRGProcessState | None = None,
    ) -> None:
        if not hasattr(recovered_runtime, "scopes") or not hasattr(recovered_runtime, "lookup_private") or not hasattr(recovered_runtime, "lookup_shared"):
            raise QualifiedQueryReadModelError("native query read model requires recovered multi-scope runtime")
        self._runtime = recovered_runtime
        self._workspace_id = _workspace_id(recovered_runtime)
        self._lane_dimension = _representation_dimension(recovered_runtime)
        self._private_motif_domains = _private_motif_domains(recovered_runtime)
        self._shared_domain_order = _explicit_shared_domain_order(recovered_runtime)
        self._geometry = NativeMotifGeometryAdapter(
            recovered_runtime,
            domain_ids=self._shared_domain_order,
            expected_dimension=self._lane_dimension,
        )
        self._embedder = embedder
        # A3 query breathing uses the existing process-local native SRG owner;
        # this model never publishes a SQLite successor merely because it read.
        # Qualification callers retain historical self-owned state, while the
        # production request owner can pass its service-process state so it is
        # not reset for every request.
        if srg_process_state is not None and not isinstance(srg_process_state, NativeSRGProcessState):
            raise QualifiedQueryReadModelError("native query SRG state must be NativeSRGProcessState")
        self._srg_process_state = srg_process_state or NativeSRGProcessState()
        self._private_lanes: dict[str, _NativeQualifiedQueryLane] = {}
        self._shared_lanes: dict[str, _NativeQualifiedQueryLane] = {}

    def close(self) -> None:
        """Release only process-local vector readers owned by this adapter."""
        for lane in (*self._private_lanes.values(), *self._shared_lanes.values()):
            lane.close()
        self._private_lanes.clear()
        self._shared_lanes.clear()

    def effective_srg_state(self, hit: QualifiedQueryHit) -> dict[str, Any] | None:
        """Return current durable-or-process-local SRG state for one native hit."""
        scope = self._native_srg_scope(hit)
        with scope.open_readers() as readers:
            _source, view = self._current_native_srg_view(hit, scope, readers)
            runtime = NativeSRGTransientRuntime(
                readers._qualified_connection.connection,
                legacy_source_namespace_id=scope.memory_runtime_scope.legacy_source_namespace_id,
                process_state=self._srg_process_state,
            )
            state = runtime.effective_srg_state(view)
            return None if state is None else dict(state)

    def replace_srg_state(self, hit: QualifiedQueryHit, state: Mapping[str, Any]) -> None:
        """Store an evolved SRG overlay under the exact current native witness."""
        scope = self._native_srg_scope(hit)
        with scope.open_readers() as readers:
            source, _view = self._current_native_srg_view(hit, scope, readers)
        identity = hit.memory_identity
        self._srg_process_state.set_overlay(
            core_id=self._runtime.native_core_id,
            namespace=scope.memory_runtime_scope.legacy_source_namespace_id,
            eid=identity.eid,
            revision_id=source.revision_id,
            srg_state=state,
            collision_report=source.payload.get("srg_collision"),
        )

    def _native_srg_scope(self, hit: QualifiedQueryHit) -> Any:
        if not isinstance(hit, QualifiedQueryHit) or hit.native_object_id is None or hit.native_revision_id is None:
            raise QualifiedQueryReadModelError("native SRG requires a qualified native query hit")
        identity = hit.memory_identity
        if identity.workspace_id != self._workspace_id:
            raise QualifiedQueryReadModelError("native SRG hit workspace mismatch")
        if identity.scope == _PRIVATE:
            scope = self._runtime.lookup_private(identity.qualifier)
        elif identity.scope == _SHARED:
            scope = self._runtime.lookup_shared(identity.qualifier)
        else:
            raise QualifiedQueryReadModelError("native SRG hit scope is not query-qualified")
        return scope

    @staticmethod
    def _current_native_srg_view(hit: QualifiedQueryHit, scope: Any, readers: Any) -> tuple[Any, Any]:
        source = readers.memory.get_memory_by_eid(
            legacy_source_namespace_id=scope.memory_runtime_scope.legacy_source_namespace_id,
            eid=hit.memory_identity.eid,
        )
        view = readers.memory_enumeration.get_current(hit.memory_identity.eid)
        if view is None or source.object_id != hit.native_object_id or source.revision_id != hit.native_revision_id:
            raise QualifiedQueryReadModelError("native SRG hit is no longer current")
        return source, view

    def private_lane(self, workspace_id: str, agent_id: str) -> QualifiedQueryLane:
        self._require_workspace(workspace_id)
        if agent_id not in self._private_motif_domains:
            raise KeyError(f"private query lane is not admitted for agent {agent_id!r}")
        lane = self._private_lanes.get(agent_id)
        if lane is None:
            lane = _NativeQualifiedQueryLane(
                self._runtime.lookup_private(agent_id), workspace_id=self._workspace_id,
                scope_name=_PRIVATE, qualifier=agent_id,
                motif_domain_id=self._private_motif_domains[agent_id], embedder=self._embedder,
            )
            self._private_lanes[agent_id] = lane
        return lane

    def shared_lane(self, workspace_id: str, domain_id: str) -> QualifiedQueryLane:
        self._require_workspace(workspace_id)
        if domain_id not in self._shared_domain_order:
            raise KeyError(f"shared query lane is not admitted for domain {domain_id!r}")
        lane = self._shared_lanes.get(domain_id)
        if lane is None:
            lane = _NativeQualifiedQueryLane(
                self._runtime.lookup_shared(domain_id), workspace_id=self._workspace_id,
                scope_name=_SHARED, qualifier=domain_id, motif_domain_id=domain_id,
                embedder=self._embedder,
            )
            self._shared_lanes[domain_id] = lane
        return lane

    def domain_geometry(self, domain_id: str) -> QualifiedDomainGeometry:
        scope = self._runtime.lookup_shared(domain_id)
        semantic_scope_id = scope.memory_runtime_scope.semantic_scope_id
        motifs = self._geometry.list_motifs(domain_id)
        return QualifiedDomainGeometry(
            self._workspace_id,
            domain_id,
            semantic_scope_id,
            tuple(float(value) for value in self._geometry.domain_centroid(domain_id, self._lane_dimension)),
            tuple(
                QualifiedMotifGeometry(
                    QualifiedQueryMotifIdentity(
                        self._workspace_id, item.domain_id, item.runtime_motif_id,
                        semantic_scope_id,
                    ),
                    item,
                )
                for item in motifs
            ),
        )

    def active_motifs(self, domain_id: str, top_k: int = 8) -> list[dict[str, Any]]:
        scope = self._runtime.lookup_shared(domain_id)
        with scope.open_readers() as readers:
            motifs = readers.motifs.list_runtime_motifs(
                motif_alias_namespace_id=scope.fabric_routing_scope.motif_alias_namespace_id,
                domain_id=domain_id,
                semantic_scope_id=scope.memory_runtime_scope.semantic_scope_id,
            )
            current = tuple(
                (
                    item.read_model,
                    float(readers.motifs.motif_radius(
                        item.motif_object_id, expected_dimension=self._lane_dimension,
                    )),
                )
                for item in motifs
            )
        return _active_summary(current, top_k=top_k)

    def domain_ids(self) -> tuple[str, ...]:
        """Return descriptor/admission order, never an incidental SQL order."""
        return self._shared_domain_order

    def _require_workspace(self, workspace_id: str) -> None:
        if workspace_id != self._workspace_id:
            raise QualifiedQueryReadModelError("query read model workspace mismatch")


def _workspace_id(recovered_runtime: Any) -> str:
    value = getattr(recovered_runtime, "workspace_id", None)
    if not isinstance(value, str) or not value:
        raise QualifiedQueryReadModelError("recovered runtime has no workspace identity")
    return value


def _representation_dimension(recovered_runtime: Any) -> int:
    lane = getattr(recovered_runtime, "representation_lane", None)
    dimension = getattr(lane, "dimension", None)
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
        raise QualifiedQueryReadModelError("recovered runtime has no qualified vector dimension")
    return dimension


def _private_motif_domains(recovered_runtime: Any) -> dict[str, str]:
    descriptor = getattr(recovered_runtime, "descriptor", None)
    payload = getattr(descriptor, "payload", None)
    lanes = payload.get("lanes") if isinstance(payload, dict) else None
    if not isinstance(lanes, list):
        raise QualifiedQueryReadModelError("recovered runtime lacks admission motif-domain evidence")
    values: dict[str, str] = {}
    for entry in lanes:
        plan = entry.get("plan") if isinstance(entry, dict) else None
        if not isinstance(plan, dict) or plan.get("scope_kind") != _PRIVATE_AGENT_SCOPE:
            continue
        agent_id = plan.get("agent_id")
        motif_domain_id = plan.get("motif_domain_id")
        if not isinstance(agent_id, str) or not agent_id or not isinstance(motif_domain_id, str) or not motif_domain_id:
            raise QualifiedQueryReadModelError("admitted private lane lacks truthful motif-domain evidence")
        if agent_id in values:
            raise QualifiedQueryReadModelError("admission has duplicate private query lanes")
        values[agent_id] = motif_domain_id
    if not values:
        raise QualifiedQueryReadModelError("recovered runtime has no admitted private query lane")
    return values


def _explicit_shared_domain_order(recovered_runtime: Any) -> tuple[str, ...]:
    values: list[str] = []
    for scope in recovered_runtime.scopes:
        runtime_scope = getattr(scope, "memory_runtime_scope", None)
        if getattr(runtime_scope, "scope_kind", None) != _SHARED_DOMAIN_SCOPE:
            continue
        domain_id = getattr(runtime_scope, "domain_id", None)
        if not isinstance(domain_id, str) or not domain_id:
            raise QualifiedQueryReadModelError("admitted shared lane lacks a domain identity")
        values.append(domain_id)
    if not values or len(set(values)) != len(values):
        raise QualifiedQueryReadModelError("recovered runtime has invalid explicit shared domain order")
    return tuple(values)


def _legacy_geometry_dimension(graphs: tuple[MemoryGraph, ...]) -> int:
    """Use the existing graph lock even when a domain has no live motifs."""
    dimensions = [getattr(graph, "_emb_dim", None) for graph in graphs]
    if not dimensions or any(
        not isinstance(value, int) or isinstance(value, bool) or value < 1
        for value in dimensions
    ):
        raise QualifiedQueryReadModelError("legacy query graphs lack one embedding dimension")
    if len(set(dimensions)) != 1:
        raise QualifiedQueryReadModelError("legacy query graph dimensions disagree")
    return dimensions[0]


def _nonempty(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise QualifiedQueryReadModelError(f"{name} must be non-empty text")


__all__ = [
    "LegacyQualifiedQueryReadModel",
    "NativeQualifiedQueryReadModel",
    "QualifiedDomainGeometry",
    "QualifiedMotifGeometry",
    "QualifiedQueryHit",
    "QualifiedQueryLane",
    "QualifiedQueryMotifIdentity",
    "QualifiedQueryReadModel",
    "QualifiedQueryReadModelError",
]
