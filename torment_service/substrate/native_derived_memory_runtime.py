"""Connection-scoped native implementation of the closed derived-memory port.

It is qualification-only: callers explicitly bind a current qualified
connection, a native scope, process SRG/world owners, an embedder callable,
and the existing independent side-store owner.  This module neither selects a
backend nor creates a shadow ``MemoryGraph``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
import math
import os
import sqlite3
import time
from typing import Any, Callable, Mapping
from uuid import UUID

import numpy as np

from torment_service.affect_attribution import build_mood_drift_attribution
from torment_service.derived_memory_runtime import (
    DerivedMemoryRuntimeContext,
    DerivedMemoryRuntimePort,
    DerivedMemorySideStorePort,
)
from torment_service.embeddings import embedding_checksum

from .compat import NativeMemoryCompatibilityFacade
from .compat_embedding_reader import NativeCompatEmbeddingReader
from .derived_memory import (
    DerivedMemoryCreateKind,
    IdentityAnchorLifecyclePatch,
    NativeDerivedMemoryCreationRequest,
    NativeDerivedMemoryCreationService,
    NativeTypedMemorySuccessorRequest,
    NativeTypedMemorySuccessorService,
    derived_child_operation_key,
)
from .ids import native_id_to_bytes
from .motif_runtime_reader import NativeMotifRuntimeReader
from .native_srg_runtime import NativeSRGProcessState, NativeSRGTransientRuntime
from .native_world_runtime import NativeWorldProcessState, NativeWorldRuntime
from .object_revision_governance import NativeMemoryGovernanceFacts
from .provenance import NativeProvenanceRecord
from .schema import require_current_schema


_LOG = logging.getLogger("torment.substrate.native_derived_memory")


@dataclass(frozen=True)
class NativeDerivedMemoryRuntimeConfiguration:
    """Explicit non-routing facts needed for one derived-memory execution."""

    workspace_id: str
    agent_id: str
    domain_id: str
    legacy_source_namespace_id: UUID
    motif_alias_namespace_id: UUID
    memory_identity_namespace_id: UUID
    semantic_scope_id: UUID
    idempotency_namespace_id: UUID
    parent_native_operation_key: str
    expected_dimension: int
    embed: Callable[[str], Any] = field(repr=False, compare=False)
    embedder_provider: str = ""
    embedder_model: str = ""
    side_store: DerivedMemorySideStorePort = field(default=None, repr=False, compare=False)  # type: ignore[assignment]
    role_multiplier: Mapping[str, float] = field(default_factory=dict)
    seed_eids: tuple[int, ...] = ()
    governance: NativeMemoryGovernanceFacts = field(default_factory=NativeMemoryGovernanceFacts)
    now_ts: Callable[[], int] = field(default=lambda: int(time.time()), repr=False, compare=False)

    def __post_init__(self) -> None:
        for field_name in ("workspace_id", "agent_id", "domain_id", "parent_native_operation_key", "embedder_provider", "embedder_model"):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name):
                raise ValueError(f"{field_name} must be non-empty text")
        for field_name in (
            "legacy_source_namespace_id", "motif_alias_namespace_id", "memory_identity_namespace_id",
            "semantic_scope_id", "idempotency_namespace_id",
        ):
            if not isinstance(getattr(self, field_name), UUID):
                raise ValueError(f"{field_name} must be a UUID")
        if not isinstance(self.expected_dimension, int) or isinstance(self.expected_dimension, bool) or self.expected_dimension < 1:
            raise ValueError("expected_dimension must be a positive integer")
        if not callable(self.embed) or not callable(self.now_ts):
            raise ValueError("embed and now_ts must be callables")
        if self.side_store is None:
            raise ValueError("side_store is required")
        if not isinstance(self.governance, NativeMemoryGovernanceFacts):
            raise ValueError("governance must be NativeMemoryGovernanceFacts")
        for value in self.seed_eids:
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("seed_eids must contain non-negative integers")


class NativeDerivedMemoryRuntime(DerivedMemoryRuntimePort):
    """Native no-motif creation and anchor successor runtime for A3D9 tests.

    The object may retain a connection only for the caller's one execution.
    Its SRG and world state are process-owned inputs; no SQLite path or handle
    is placed in either process owner.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        configuration: NativeDerivedMemoryRuntimeConfiguration,
        world_process_state: NativeWorldProcessState,
        srg_process_state: NativeSRGProcessState,
    ) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise ValueError("connection must be an already-open qualified sqlite connection")
        require_current_schema(connection)
        if not isinstance(configuration, NativeDerivedMemoryRuntimeConfiguration):
            raise ValueError("configuration must be NativeDerivedMemoryRuntimeConfiguration")
        self._connection = connection
        self._config = configuration
        self._reads = NativeMemoryCompatibilityFacade(connection)
        self._embeddings = NativeCompatEmbeddingReader(connection)
        self._motifs = NativeMotifRuntimeReader(connection)
        self._world = NativeWorldRuntime(
            connection,
            legacy_source_namespace_id=configuration.legacy_source_namespace_id,
            expected_dimension=configuration.expected_dimension,
            process_state=world_process_state,
        )
        self._srg = NativeSRGTransientRuntime(
            connection,
            legacy_source_namespace_id=configuration.legacy_source_namespace_id,
            process_state=srg_process_state,
        )

    def maybe_emit_identity_anchor(self, context: DerivedMemoryRuntimeContext) -> int | None:
        # D0: a shared trigger is inapplicable to private identity-anchor
        # semantics.  This must precede all qualified-scope assertions and
        # SQLite/side-store activity so no cross-scope provenance is read or
        # written.
        if context.trigger_scope == "shared":
            return None
        self._assert_context(context)
        min_count, min_gap, max_examples = _anchor_thresholds(self._config.role_multiplier)
        state = dict(self._config.side_store.load_anchor_state(
            workspace_id=context.workspace_id, agent_id=context.agent_id,
        ))
        seen = state.get("motifs", {}) or {}
        if not isinstance(seen, Mapping):
            seen = {}
        catalog = {
            item.read_model.runtime_motif_id: item
            for item in self._motifs.list_runtime_motifs(
                motif_alias_namespace_id=self._config.motif_alias_namespace_id,
                domain_id=context.domain_id,
                semantic_scope_id=self._config.semantic_scope_id,
            )
        }
        for motif_id in context.motif_ids:
            motif = catalog.get(motif_id)
            if motif is None:
                continue
            member_eids = self._member_eids(motif.motif_object_id)
            count = len(member_eids)
            affect_sensitive = self._affect_sensitive(member_eids)
            required_count, required_gap = _affect_anchor_thresholds(min_count, min_gap, affect_sensitive)
            if count < required_count:
                continue
            previous = seen.get(motif_id) or {}
            try:
                last_step = int(previous.get("last_step", -10**9))
                count_at_create = int(previous.get("count_at_create", 0))
            except (AttributeError, TypeError, ValueError):
                last_step, count_at_create = -10**9, 0
            if context.step - last_step < required_gap or count <= max(count_at_create, min_count - 1):
                continue
            label = str(motif.read_model.label or motif_id)
            examples = self._anchor_examples(member_eids, max_examples)
            summary = f"Identity anchor: recurring theme '{label}'." + (
                "" if not examples else " Examples: " + " | ".join(examples[:max_examples])
            )
            vector = self._embed(summary)
            overlap = len(set(self._config.seed_eids).intersection(member_eids))
            payload = {
                "workspace_id": context.workspace_id, "domain_id": context.domain_id,
                "scope": "private", "agent_id": context.agent_id,
                "anchor_for_motif": motif_id, "anchor_member_count": count,
                "anchor_label": label, "anchor_affect_sensitive": affect_sensitive,
                "anchor_origin": "derived", "anchor_source": "motif_cluster",
                "seed_overlap_count": overlap, "seed_aligned": bool(overlap > 0),
                "source_member_eids": list(member_eids),
                **self._embedding_metadata(summary, vector),
            }
            child_key = derived_child_operation_key(
                parent_native_operation_key=self._config.parent_native_operation_key,
                operation_kind=DerivedMemoryCreateKind.IDENTITY_ANCHOR_CREATE.value,
                semantic_discriminator=f"{context.domain_id}:{motif_id}:{context.step}",
            )
            request = NativeDerivedMemoryCreationRequest(
                operation_kind=DerivedMemoryCreateKind.IDENTITY_ANCHOR_CREATE,
                legacy_source_namespace_id=self._config.legacy_source_namespace_id,
                memory_identity_namespace_id=self._config.memory_identity_namespace_id,
                semantic_scope_id=self._config.semantic_scope_id,
                idempotency_namespace_id=self._config.idempotency_namespace_id,
                idempotency_key=child_key, summary=summary,
                strength=float(min(1.0, 0.55 + 0.08 * count)), confidence=0.85,
                half_life_days=3650.0, user_id=context.agent_id, logical_step=context.step,
                created_ts=int(self._config.now_ts()), payload_fields=payload,
                provenance=self._provenance("identity_anchor"), governance=self._config.governance,
                embedding=vector, expected_dimension=self._config.expected_dimension,
            )
            self._world.ensure_initialized()
            result = NativeDerivedMemoryCreationService(self._connection).create(
                request, on_source_committed=self._register_fresh,
            )
            # This follows the legacy order: creation is durable before the
            # best-effort predecessor retirement, which is before anchors.json.
            previous_eid = _nonnegative_int(previous.get("last_eid", 0) if isinstance(previous, Mapping) else 0)
            if previous_eid and previous_eid != result.source.eid:
                try:
                    self._publish_lifecycle(
                        eid=previous_eid,
                        patch=IdentityAnchorLifecyclePatch.superseded(
                            anchor_superseded_by=result.source.eid,
                            anchor_merged_into=result.source.eid,
                            last_reinforced=context.step,
                        ),
                        discriminator=f"emit:{motif_id}:{previous_eid}:{result.source.eid}:{context.step}",
                    )
                except Exception as exc:
                    _LOG.debug("native anchor retire failed: %s", exc)
            next_seen = dict(seen)
            next_seen[motif_id] = {
                "last_step": int(context.step), "count_at_create": count,
                "last_eid": result.source.eid,
            }
            state["motifs"] = next_seen
            self._config.side_store.save_anchor_state(
                workspace_id=context.workspace_id, agent_id=context.agent_id, state=state,
            )
            return result.source.eid
        return None

    def refine_identity_anchors(self, context: DerivedMemoryRuntimeContext) -> None:
        # See ``maybe_emit_identity_anchor``: historical private anchors are
        # never refined in response to a shared trigger.
        if context.trigger_scope == "shared":
            return
        self._assert_context(context)
        keep_k = _env_int("TORMENT_ANCHOR_KEEP_PER_MOTIF", 1)
        weak_max = _env_int("TORMENT_ANCHOR_WEAK_MEMBER_MAX", 3)
        weak_min_age = _env_int("TORMENT_ANCHOR_WEAK_MIN_AGE_STEPS", 800)
        all_views = self._list_current_views()
        try:
            now_step = max(int(view.payload.get("created_at", 0)) for view in all_views)
        except (TypeError, ValueError):
            now_step = 0
        for motif_id in context.motif_ids:
            anchors: list[tuple[int, int, int]] = []
            for view in all_views:
                payload = view.payload
                if (
                    payload.get("type") == "identity_anchor"
                    and str(payload.get("anchor_for_motif", "")) == str(motif_id)
                    and not bool(payload.get("anchor_retired", False))
                ):
                    anchors.append((view.eid, _nonnegative_int(payload.get("anchor_member_count", 0)), _nonnegative_int(payload.get("created_at", 0))))
            if not anchors:
                continue
            anchors.sort(key=lambda item: (item[1], item[2]), reverse=True)
            keep = anchors[:max(1, keep_k)]
            keep_eids = {item[0] for item in keep}
            best_eid = keep[0][0]
            for eid, _member_count, _created in anchors:
                if eid in keep_eids:
                    continue
                try:
                    self._publish_lifecycle(
                        eid=eid,
                        patch=IdentityAnchorLifecyclePatch.superseded(
                            anchor_superseded_by=best_eid, anchor_merged_into=best_eid,
                            last_reinforced=now_step,
                        ),
                        discriminator=f"refine:{motif_id}:{eid}:superseded:{best_eid}:{now_step}",
                    )
                except Exception as exc:
                    _LOG.debug("native anchor supersede update failed: %s", exc)
            for eid, member_count, created_step in keep:
                if eid == best_eid:
                    continue
                if member_count <= weak_max and now_step - created_step >= weak_min_age:
                    try:
                        self._publish_lifecycle(
                            eid=eid,
                            patch=IdentityAnchorLifecyclePatch.weak_old(
                                anchor_superseded_by=best_eid, last_reinforced=now_step,
                            ),
                            discriminator=f"refine:{motif_id}:{eid}:weak_old:{best_eid}:{now_step}",
                        )
                    except Exception as exc:
                        _LOG.debug("native weak anchor retire failed: %s", exc)

    def maybe_emit_mood_drift(self, context: DerivedMemoryRuntimeContext) -> int | None:
        self._assert_context(context)
        if not context.affect_tag or context.affect_tag == "neutral":
            return None
        if not _env_enabled("TORMENT_MOOD_DRIFT_ENABLE", True):
            return None
        min_conf = _env_float("TORMENT_MOOD_DRIFT_MIN_CONF", 0.55)
        min_gap = _env_int("TORMENT_MOOD_DRIFT_MIN_GAP_STEPS", 120)
        confidence = float(context.affect_conf or 0.0)
        if confidence < min_conf:
            return None
        state = dict(self._config.side_store.load_affect_state(
            workspace_id=context.workspace_id, agent_id=context.agent_id,
        ))
        last_tag = state.get("last_tag")
        last_step = _as_int(state.get("last_step", -10**9), -10**9)
        # Exact legacy topology: persist the latest affect before deciding
        # whether there is a drift row.  Its failure is best-effort and does
        # not prevent the subsequent memory decision.
        state["last_tag"] = str(context.affect_tag)
        state["last_conf"] = confidence
        state["last_step"] = int(context.step)
        try:
            self._config.side_store.save_affect_state(
                workspace_id=context.workspace_id, agent_id=context.agent_id, state=state,
            )
        except Exception as exc:
            # ``_save_affect_state`` is itself best-effort in the legacy
            # implementation; a side-store failure does not block this call.
            _LOG.debug("native affect state save failed: %s", exc)
        if not last_tag or last_tag == "neutral" or str(last_tag) == str(context.affect_tag):
            return None
        if context.step - last_step < min_gap:
            return None
        summary = f"Mood drift: from {last_tag} to {context.affect_tag}."
        vector = self._embed(summary)
        payload = {
            "workspace_id": context.workspace_id, "domain_id": context.domain_id,
            "scope": "private", "agent_id": context.agent_id,
            "affect_tag": str(context.affect_tag), "affect_conf": confidence,
            "affect_attribution": build_mood_drift_attribution(affect_tag=str(context.affect_tag)),
            "mood_from": str(last_tag), "mood_to": str(context.affect_tag),
            **self._embedding_metadata(summary, vector),
        }
        child_key = derived_child_operation_key(
            parent_native_operation_key=self._config.parent_native_operation_key,
            operation_kind=DerivedMemoryCreateKind.MOOD_DRIFT_CREATE.value,
            semantic_discriminator=f"{context.domain_id}:{last_tag}:{context.affect_tag}:{context.step}",
        )
        request = NativeDerivedMemoryCreationRequest(
            operation_kind=DerivedMemoryCreateKind.MOOD_DRIFT_CREATE,
            legacy_source_namespace_id=self._config.legacy_source_namespace_id,
            memory_identity_namespace_id=self._config.memory_identity_namespace_id,
            semantic_scope_id=self._config.semantic_scope_id,
            idempotency_namespace_id=self._config.idempotency_namespace_id,
            idempotency_key=child_key, summary=summary,
            strength=float(min(1.0, 0.50 + 0.20 * confidence)),
            confidence=float(min(0.95, 0.6 + 0.35 * confidence)),
            half_life_days=_env_float("TORMENT_MOOD_DRIFT_HALF_LIFE_DAYS", 60.0),
            user_id=context.agent_id, logical_step=context.step,
            created_ts=int(self._config.now_ts()), payload_fields=payload,
            provenance=self._provenance("mood_drift"), governance=self._config.governance,
            embedding=vector, expected_dimension=self._config.expected_dimension,
        )
        self._world.ensure_initialized()
        result = NativeDerivedMemoryCreationService(self._connection).create(
            request, on_source_committed=self._register_fresh,
        )
        # Exact legacy post-memory side-store shape: reload, append, save; a
        # failure here leaves the memory durable and returns its EID.
        try:
            state2 = dict(self._config.side_store.load_affect_state(
                workspace_id=context.workspace_id, agent_id=context.agent_id,
            ))
            history = state2.get("drift_hist") or []
            if not isinstance(history, list):
                history = []
            history.append({
                "from": str(last_tag), "to": str(context.affect_tag),
                "step": int(context.step), "conf": confidence,
            })
            state2["drift_hist"] = history[-50:]
            self._config.side_store.save_affect_state(
                workspace_id=context.workspace_id, agent_id=context.agent_id, state=state2,
            )
        except Exception as exc:
            _LOG.debug("native affect state save failed: %s", exc)
        return result.source.eid

    def _publish_lifecycle(
        self, *, eid: int, patch: IdentityAnchorLifecyclePatch, discriminator: str,
    ) -> None:
        current = self._reads.get_memory_by_eid(
            legacy_source_namespace_id=self._config.legacy_source_namespace_id, eid=eid,
        )
        e1 = self._embeddings.read_current(
            current.object_id, expected_dimension=self._config.expected_dimension,
        )
        if e1 is None:
            raise RuntimeError("identity anchor has no qualified current embedding")
        materialization = self._srg.prepare_successor_materialization(
            eid=eid, expected_revision_id=current.revision_id,
        )
        world_materialization = self._world.prepare_successor_materialization(
            eid=eid, expected_revision_id=current.revision_id,
        )
        key = derived_child_operation_key(
            parent_native_operation_key=self._config.parent_native_operation_key,
            operation_kind="IDENTITY_ANCHOR_LIFECYCLE", semantic_discriminator=discriminator,
        )
        request = NativeTypedMemorySuccessorRequest(
            legacy_source_namespace_id=self._config.legacy_source_namespace_id, eid=eid,
            expected_revision_id=current.revision_id, expected_representation_id=e1.representation_id,
            idempotency_namespace_id=self._config.idempotency_namespace_id, idempotency_key=key,
            expected_dimension=self._config.expected_dimension, patch=patch,
            srg_materialization=materialization, world_diagnostic_materialization=world_materialization,
        )
        result = NativeTypedMemorySuccessorService(self._connection).publish_identity_anchor_lifecycle(
            request, on_source_committed=self._synchronize_successor,
        )
        if materialization is not None:
            self._srg.acknowledge_materialized_successor(
                materialization, eid=eid, successor_revision_id=result.source.revision_id,
            )
        if world_materialization is not None:
            self._world.acknowledge_materialized_successor(
                world_materialization, eid=eid, successor_revision_id=result.source.revision_id,
            )

    def _register_fresh(self, source: Any) -> None:
        self._world.register_fresh_created(
            eid=source.eid, memory_object_id=source.memory_object_id,
            memory_revision_id=source.memory_revision_id,
            memory_revision_ordinal=source.memory_revision_ordinal,
            born_step=self._active_context_step, channel=0,
        )

    def _synchronize_successor(self, source: Any) -> None:
        self._world.synchronize_reinforcement_successor(
            eid=source.eid, memory_object_id=source.memory_object_id,
            predecessor_revision_id=source.predecessor_revision_id,
            predecessor_revision_ordinal=source.predecessor_revision_ordinal,
            successor_revision_id=source.revision_id,
            successor_revision_ordinal=source.revision_ordinal,
        )

    def _member_eids(self, motif_object_id: UUID) -> tuple[int, ...]:
        result: list[int] = []
        for member in self._motifs.list_ordered_current_motif_members(motif_object_id):
            result.append(self._reads.resolve_native_memory_legacy_eid(
                legacy_source_namespace_id=self._config.legacy_source_namespace_id,
                native_object_id=member.member_object_id,
            ))
        return tuple(result)

    def _list_current_views(self):
        rows = self._connection.execute(
            """SELECT a.alias_value FROM legacy_object_aliases a
                 JOIN memory_runtime_enumeration_orders o ON o.object_id=a.object_id
                   AND o.legacy_source_namespace_id=a.legacy_source_namespace_id
                WHERE a.legacy_source_namespace_id=? AND a.alias_kind='EID'
                ORDER BY o.runtime_ordinal""",
            (native_id_to_bytes(self._config.legacy_source_namespace_id),),
        ).fetchall()
        return tuple(self._reads.get_memory_by_eid(
            legacy_source_namespace_id=self._config.legacy_source_namespace_id, eid=int(row[0]),
        ) for row in rows)

    def _affect_sensitive(self, member_eids: tuple[int, ...]) -> bool:
        non_neutral = checked = 0
        for eid in member_eids[-12:]:
            try:
                tag = str(self._reads.get_memory_by_eid(
                    legacy_source_namespace_id=self._config.legacy_source_namespace_id, eid=eid,
                ).payload.get("affect_tag") or "")
            except Exception:
                tag = ""
            if tag:
                checked += 1
                if tag != "neutral":
                    non_neutral += 1
        return checked >= 4 and (float(non_neutral) / float(max(1, checked))) >= 0.60

    def _anchor_examples(self, member_eids: tuple[int, ...], max_examples: int) -> list[str]:
        result: list[str] = []
        for eid in member_eids[-max_examples:]:
            try:
                summary = str(self._reads.get_memory_by_eid(
                    legacy_source_namespace_id=self._config.legacy_source_namespace_id, eid=eid,
                ).payload.get("summary", "")).strip()
            except Exception:
                summary = ""
            if summary:
                result.append(summary)
        return result

    def _embed(self, text: str) -> np.ndarray:
        vector = np.asarray(self._config.embed(text), dtype=np.float32).reshape(-1)
        if vector.size != self._config.expected_dimension or not np.all(np.isfinite(vector)):
            raise RuntimeError("derived runtime embedder returned an unqualified vector")
        return np.ascontiguousarray(vector, dtype=np.float32)

    def _embedding_metadata(self, summary: str, vector: np.ndarray) -> dict[str, Any]:
        return {
            "embedding_provider": self._config.embedder_provider,
            "embedding_model": self._config.embedder_model,
            "embedding_dim": int(vector.size),
            "embedding_checksum": embedding_checksum(
                summary, self._config.embedder_provider, self._config.embedder_model,
            ),
        }

    def _provenance(self, memory_role: str) -> NativeProvenanceRecord:
        return NativeProvenanceRecord(
            "LEGACY_DERIVED_MEMORY", "derived", "system", "legacy_derived",
            "UNKNOWN", None, None, memory_role, f"A3D9 {memory_role} derived memory",
        )

    def _assert_context(self, context: DerivedMemoryRuntimeContext) -> None:
        if not isinstance(context, DerivedMemoryRuntimeContext):
            raise ValueError("context must be DerivedMemoryRuntimeContext")
        if (
            context.workspace_id != self._config.workspace_id
            or context.agent_id != self._config.agent_id
            or context.domain_id != self._config.domain_id
        ):
            raise ValueError("derived runtime context does not match its qualified scope")
        self._active_context_step = int(context.step)


def _anchor_thresholds(multiplier: Mapping[str, float]) -> tuple[int, int, int]:
    min_count = _env_int("TORMENT_ID_ANCHOR_MIN_COUNT", 3)
    min_gap = _env_int("TORMENT_ID_ANCHOR_MIN_GAP_STEPS", 50)
    max_examples = _env_int("TORMENT_ID_ANCHOR_MAX_EXAMPLES", 2)
    try:
        min_count = int(max(2, round(float(min_count) * float(multiplier.get("anchor_count_mult", 1.0)))))
        min_gap = int(max(10, round(float(min_gap) * float(multiplier.get("anchor_gap_mult", 1.0)))))
    except Exception:
        pass
    return min_count, min_gap, max_examples


def _affect_anchor_thresholds(min_count: int, min_gap: int, sensitive: bool) -> tuple[int, int]:
    if not sensitive:
        return min_count, min_gap
    return (
        int(max(2, math.ceil(float(min_count) * _env_float("TORMENT_ID_ANCHOR_AFFECT_COUNT_MULT", 1.6)))),
        int(max(10, math.ceil(float(min_gap) * _env_float("TORMENT_ID_ANCHOR_AFFECT_GAP_MULT", 1.5)))),
    )


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_enabled(name: str, default: bool) -> bool:
    try:
        return str(os.getenv(name, "1" if default else "0")).strip().lower() not in ("0", "false", "no")
    except Exception:
        return default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _nonnegative_int(value: Any) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return 0
    return result if result >= 0 else 0


__all__ = [
    "NativeDerivedMemoryRuntime",
    "NativeDerivedMemoryRuntimeConfiguration",
]
