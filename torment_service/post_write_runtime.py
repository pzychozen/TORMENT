"""Explicit legacy post-write runtime boundary for :mod:`torment_service.fabric`.

This module deliberately has no substrate imports and no native adapter.  Its
single production implementation is a narrow legacy adapter over the exact
objects selected by Fabric during the preceding legacy write.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
import os
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol

import numpy as np

from .character import CharacterState, gravity_correction, measure_drift
from .memory_runtime_access import PostWriteMemoryReadPort


class PostWriteStorageOutcome(str, Enum):
    """Process-local classification of the already-completed storage branch."""

    NO_WRITE = "NO_WRITE"
    REINFORCED_EXISTING = "REINFORCED_EXISTING"
    CREATED_NEW = "CREATED_NEW"


@dataclass(frozen=True)
class FabricPostWriteContext:
    """Immutable facts consumed by Fabric's legacy post-write runtime.

    This is orchestration state only: it is not serialized or persisted and
    does not model a native storage operation.
    """

    workspace_id: str
    agent_id: str
    scope: str
    chosen_domain: str
    step: int
    storage_outcome: PostWriteStorageOutcome
    stored: bool
    eid: int | None
    created_motif: str | None
    motif_ids: tuple[str, ...]
    half_life_days: float | None
    summary: str
    embedding: np.ndarray
    memory_class: str
    memory_type: str
    strength: float
    confidence: float
    promotion_score: float
    stability_delta: float
    tri_mod: Mapping[str, float]
    debug: Mapping[str, Any]
    srg_state: Mapping[str, Any] | None
    phase_durations: Mapping[str, Any]
    state_symbol: str | None
    affect_tag: str | None
    affect_conf: float | None
    skip_packet_emission: bool

    @classmethod
    def make(cls, **values: Any) -> "FabricPostWriteContext":
        """Freeze mutable mapping carriers at the Fabric boundary."""
        for name in ("tri_mod", "debug", "phase_durations"):
            values[name] = MappingProxyType(dict(values[name] or {}))
        srg_state = values.get("srg_state")
        values["srg_state"] = MappingProxyType(dict(srg_state)) if isinstance(srg_state, Mapping) else None
        values["motif_ids"] = tuple(values["motif_ids"])
        return cls(**values)


@dataclass(frozen=True)
class FabricPostWriteOutcome:
    """The only post-write value currently consumed by Fabric's public reply."""

    proposal_id: str | None = None


@dataclass(frozen=True)
class LegacyFabricPostWriteDependencies:
    """Legacy-only mutable objects and callbacks selected by Fabric.

    The adapter receives the existing in-memory graph, registry, workspace and
    Fabric owner; it never reloads, recreates, or wraps any legacy state.
    """

    owner: Any
    workspace: Any
    graph: Any
    memory_access: PostWriteMemoryReadPort
    identity: Any
    motif_registry: Any | None
    motif_runtime: Any | None
    model_state: Any
    kernel_context: Any
    agent_key: str
    detect_canon_conflict: Callable[[str, str, float], tuple[bool, float, str]]
    proposal_allowed: Callable[..., bool]
    random_chance: Callable[[float], bool]
    save_checkpoint: Callable[..., Any]
    build_motif_summary: Callable[..., Any]
    build_shard_snapshot: Callable[..., Any]
    hivemind_log: logging.Logger


class FabricPostWriteRuntimePort(Protocol):
    def run(self, context: FabricPostWriteContext) -> FabricPostWriteOutcome:
        """Run post-write work without changing Fabric's storage selection."""


class LegacyFabricPostWriteAdapter:
    """Exact legacy runtime adapter for Fabric's post-storage tail."""

    def __init__(self, dependencies: LegacyFabricPostWriteDependencies) -> None:
        self._deps = dependencies

    def run(self, context: FabricPostWriteContext) -> FabricPostWriteOutcome:
        if context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
            self._run_created_memory_consumers(context)
        self._run_world_step(context)
        self._run_character_drift(context)
        self._run_checkpoint(context)
        self._run_compression(context)
        proposal_id = self._run_proposal(context)
        self._run_bridges(context)
        return FabricPostWriteOutcome(proposal_id=proposal_id)

    def _run_created_memory_consumers(self, context: FabricPostWriteContext) -> None:
        self._run_contradiction_surface(context)
        self._run_srg_collision(context)
        self._run_hivemind(context)
        self._run_motif_maintenance_and_anchors(context)

    def _run_contradiction_surface(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        if not (context.scope == "private" and context.memory_class == "core" and context.eid is not None):
            return
        try:
            outcome = deps.memory_access.search_by_embedding(
                context.embedding, top_k=3, user_id=context.agent_id,
            )
            if outcome.status == "ZERO_NORM":
                return
            for hit in outcome.hits:
                old_eid = int(hit.eid)
                if old_eid <= 0 or old_eid == context.eid:
                    continue
                if hit.view.memory_class != "core":
                    continue
                similarity = float(hit.raw_score)
                is_conflict, score, reason = deps.detect_canon_conflict(
                    context.summary, hit.view.summary, similarity,
                )
                if is_conflict:
                    deps.workspace.conflicts[context.chosen_domain].add(
                        eid_a=old_eid,
                        eid_b=int(context.eid),
                        sim=similarity,
                        conflict_score=float(score),
                        reason=str(reason or "heuristic"),
                        origin_scope="private",
                        origin_agent_id=context.agent_id,
                        origin_domain_id=None,
                    )
                    break
        except Exception as exc:
            deps.owner._log.debug("private contradiction surface skipped: %s", exc)

    def _run_srg_collision(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        if not (deps.owner._srg_enable and context.srg_state and context.eid is not None):
            return
        try:
            from .embedding_store import load_embedding
            from .srg_engine import SRGMemoryState, collision

            new_normalized = context.embedding / (np.linalg.norm(context.embedding) + 1e-12)
            best_similarity = 0.0
            best_eid = None
            for object_id, entity in deps.graph.entities.items():
                if int(object_id) == int(context.eid):
                    continue
                payload = getattr(entity, "payload", {}) or {}
                if not payload.get("srg"):
                    continue
                raw = load_embedding(object_id, payload, deps.graph._shard_reader, deps.graph.data_dir)
                if raw is None:
                    continue
                vector = np.asarray(raw, dtype=np.float32).reshape(-1)
                norm = float(np.linalg.norm(vector))
                if norm < 1e-12:
                    continue
                similarity = float(np.dot(new_normalized, vector / norm))
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_eid = int(object_id)
            if best_eid is not None and best_similarity >= 0.75:
                existing_entity = deps.graph.entities.get(best_eid)
                if existing_entity is not None:
                    existing = SRGMemoryState.from_dict((existing_entity.payload or {}).get("srg", {}))
                    incoming = SRGMemoryState.from_dict(dict(context.srg_state))
                    report = collision(existing, incoming, best_similarity, int(context.step))
                    if report.get("collision"):
                        existing_entity.payload["srg"] = existing.to_dict()
                        own_entity = deps.graph.entities.get(int(context.eid))
                        if own_entity is not None:
                            own_entity.payload["srg"] = incoming.to_dict()
                            own_entity.payload["srg_collision"] = report
        except Exception as exc:
            deps.owner._log.debug("Failed to process SRG collision for eid=%s: %s", context.eid, exc)

    def _run_hivemind(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        owner = deps.owner
        if owner._hivemind_enable and context.stored and context.eid is not None and not context.skip_packet_emission:
            try:
                from .collective_models import ResonancePacket

                emit_ok = True
                skip_reason = None
                provenance_class = None
                try:
                    view = deps.memory_access.get_current(int(context.eid))
                    if view is not None:
                        emit_ok = not (
                            view.governance.non_shareable
                            or view.governance.collective_export_blocked
                        )
                        if not emit_ok:
                            skip_reason = "governance: non_shareable or export_blocked"
                        if view.provenance.collective_echo:
                            provenance_class = "collective_echo"
                            emit_ok = False
                            skip_reason = "governance: collective provenance (echo invariant)"
                except Exception as exc:
                    deps.hivemind_log.exception(
                        "Hivemind packet governance evaluation failed ws=%s agent=%s eid=%s: %s",
                        context.workspace_id, context.agent_id, context.eid, exc,
                    )
                coherence = float(context.debug.get("coherence", 0.0) or 0.0)
                if emit_ok and coherence >= 0.15:
                    embedding_hash = ""
                    try:
                        embedding_hash = hashlib.md5(context.embedding.tobytes()).hexdigest()[:12]
                    except Exception as exc:
                        owner._log.debug("Failed to compute embedding hash: %s", exc)
                    resonance_score = None
                    loop_type = None
                    try:
                        view = deps.memory_access.get_current(int(context.eid))
                        if view is not None:
                            resonance_score = view.payload.get("resonance_score")
                            loop_type = view.payload.get("loop_type")
                    except Exception as exc:
                        owner._log.debug("Failed to extract resonance data for packet: %s", exc)
                    drift = drift_direction = seed_id = None
                    try:
                        character_state = owner.character_store.load_state(context.workspace_id, context.agent_id)
                        if character_state:
                            drift = character_state.drift_score
                            drift_direction = character_state.drift_direction
                            seed_id = character_state.seed_id
                    except Exception as exc:
                        owner._log.debug("Failed to load character state for packet: %s", exc)
                    srg = context.srg_state or {}
                    packet = ResonancePacket(
                        workspace_id=context.workspace_id,
                        agent_id=context.agent_id,
                        domain_id=context.chosen_domain,
                        source_eid=int(context.eid),
                        summary=str(context.summary),
                        embedding_hash=embedding_hash,
                        cycle_stage=str(context.tri_mod.get("cycle_stage", "")),
                        identity_state=str(context.tri_mod.get("identity_state", "")),
                        coherence=coherence,
                        stability_delta=float(context.stability_delta),
                        corridor_angle_deg=context.phase_durations.get("corridor_angle_deg"),
                        corridor_duration_steps=int(context.phase_durations.get("corridor_duration_steps", 0)),
                        phase_duration_steps=int(context.phase_durations.get("phase_duration_steps", 0)),
                        motifs=list(context.motif_ids),
                        created_motif=context.created_motif,
                        state_symbol=context.state_symbol,
                        resonance_score=float(resonance_score) if resonance_score is not None else None,
                        loop_type=str(loop_type) if loop_type else None,
                        drift_score=float(drift) if drift is not None else None,
                        drift_direction=str(drift_direction) if drift_direction else None,
                        seed_id=str(seed_id) if seed_id else None,
                        srg_band=srg.get("R_band"),
                        srg_heartbeat_class=srg.get("heartbeat_class"),
                        srg_is_crystal=bool(srg.get("is_crystal", False)),
                    )
                    convergence = owner._get_collective_field(context.workspace_id).append_packet(
                        packet, embedding=context.embedding,
                    )
                    if owner._hivemind_telemetry_enable:
                        owner._emit_hivemind_packet_telemetry(
                            workspace_id=context.workspace_id, agent_id=context.agent_id,
                            domain_id=context.chosen_domain, source_eid=int(context.eid),
                            packet_emitted=True, gate_outcome="emitted", skip_reason=None,
                            coherence=coherence, provenance_class=provenance_class,
                            convergence_event=convergence,
                        )
                    if convergence is not None:
                        try:
                            owner._get_proposal_bridge(context.workspace_id).maybe_draft_proposal(
                                event=convergence.to_dict(),
                                proposal_registry=deps.workspace.proposals.get(context.chosen_domain),
                                embedding=context.embedding,
                            )
                        except Exception:
                            pass
                elif owner._hivemind_telemetry_enable:
                    owner._emit_hivemind_packet_telemetry(
                        workspace_id=context.workspace_id, agent_id=context.agent_id,
                        domain_id=context.chosen_domain, source_eid=int(context.eid),
                        packet_emitted=False, gate_outcome="skipped",
                        skip_reason=skip_reason if not emit_ok else "coherence_below_threshold",
                        coherence=coherence, provenance_class=provenance_class,
                    )
            except Exception as exc:
                deps.hivemind_log.exception(
                    "Hivemind packet emission failed ws=%s agent=%s eid=%s: %s",
                    context.workspace_id, context.agent_id, context.eid, exc,
                )
                if owner._hivemind_telemetry_enable:
                    owner._emit_hivemind_packet_telemetry(
                        workspace_id=context.workspace_id, agent_id=context.agent_id,
                        domain_id=context.chosen_domain, source_eid=int(context.eid),
                        packet_emitted=False, gate_outcome="error",
                        skip_reason="packet_emission_error", coherence=None,
                    )
        elif owner._hivemind_telemetry_enable:
            reasons = []
            if not owner._hivemind_enable:
                reasons.append("hivemind_disabled")
            if context.eid is None:
                reasons.append("source_eid_missing")
            if context.skip_packet_emission:
                reasons.append("packet_emission_skipped")
            owner._emit_hivemind_packet_telemetry(
                workspace_id=context.workspace_id, agent_id=context.agent_id,
                domain_id=context.chosen_domain,
                source_eid=int(context.eid) if context.eid is not None else None,
                packet_emitted=False, gate_outcome="blocked",
                skip_reason=",".join(reasons) or "outer_gate_blocked", coherence=None,
            )

    def _run_motif_maintenance_and_anchors(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        if deps.motif_runtime is None:
            return
        policy = deps.workspace.domain_policies.get(context.chosen_domain, {})
        try:
            deps.motif_runtime.update_entropy_and_suggest(
                target_n=int(policy.get("motif_entropy_target_n", 24)),
                entropy_high=float(policy.get("motif_entropy_high", 0.72)),
                sim_threshold=float(policy.get("motif_merge_similarity", 0.93)),
                max_suggestions=int(policy.get("motif_merge_max_suggestions", 20)),
                auto_merge=bool(policy.get("auto_merge_motifs", False)),
                auto_merge_trigger=float(policy.get("auto_merge_entropy_trigger", 0.80)),
            )
        except Exception as exc:
            deps.owner._log.debug("motif entropy update failed for domain=%s: %s", context.chosen_domain, exc)
        try:
            deps.owner._maybe_emit_identity_anchor(
                deps.workspace, agent_id=context.agent_id, domain_id=context.chosen_domain,
                step=int(context.step), motif_ids=list(context.motif_ids),
            )
        except Exception as exc:
            deps.owner._log.debug("identity anchor emission failed: %s", exc)
        try:
            deps.owner._refine_identity_anchors(
                deps.workspace, agent_id=context.agent_id, domain_id=context.chosen_domain,
                motif_ids=list(context.motif_ids),
            )
        except Exception as exc:
            deps.owner._log.debug("identity anchor refinement failed: %s", exc)
        try:
            deps.owner._maybe_emit_mood_drift(
                deps.workspace, agent_id=context.agent_id, domain_id=context.chosen_domain,
                step=int(context.step), affect_tag=context.affect_tag, affect_conf=context.affect_conf,
            )
        except Exception as exc:
            deps.owner._log.debug("mood drift emission failed: %s", exc)

    def _run_world_step(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        try:
            deps.graph.step_world(step=int(context.step), classify_every=50, log_every=1)
        except Exception as exc:
            deps.owner._log.debug(
                "step_world failed at step=%s for workspace_id=%s agent_id=%s: %s",
                context.step, context.workspace_id, context.agent_id, exc,
            )

    def _run_character_drift(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        owner = deps.owner
        if not (owner._character_enable and context.stored and int(context.step) > 0 and int(context.step) % owner._character_drift_every == 0):
            return
        try:
            seed_id = str(deps.identity.seed.get("seed_id", "") or "").strip()
            if seed_id:
                seed = owner.character_store.load_seed(context.workspace_id, seed_id)
                # `reg` was created only by the legacy CREATED_NEW branch.  The
                # old outer fail-soft boundary therefore produced no drift side
                # effects for a reinforcement with a seed.  Preserve that
                # observed behavior rather than repairing it in this extraction.
                if seed and seed.seed_motif_id and context.storage_outcome is PostWriteStorageOutcome.CREATED_NEW:
                    state = owner.character_store.load_state(context.workspace_id, context.agent_id)
                    drift = measure_drift(
                        graph=deps.graph, motif_registry=deps.motif_registry,
                        coherence_field=None, seed=seed, agent_id=context.agent_id,
                        current_step=int(context.step), previous_state=state,
                    )
                    if state is None:
                        state = CharacterState(workspace_id=context.workspace_id, agent_id=context.agent_id, seed_id=seed_id)
                    state.drift_score = float(drift["drift_score"])
                    state.drift_direction = str(drift["drift_direction"])
                    state.distance_to_seed = float(drift["distance_to_seed"])
                    state.seed_basin_phi = float(drift.get("seed_basin_phi", 0.0))
                    state.seed_basin_kappa = float(drift.get("seed_basin_kappa", 0.0))
                    state.seed_basin_tension = float(drift.get("seed_basin_tension", 0.0))
                    state.seed_basin_role = str(drift.get("seed_basin_role", "plateau"))
                    state.core_count = int(drift.get("core_count", 0))
                    state.relational_count = int(drift.get("relational_count", 0))
                    state.situational_count = int(drift.get("situational_count", 0))
                    state.drift_history.append((int(context.step), float(drift["drift_score"])))
                    state.drift_history = state.drift_history[-50:]
                    owner.character_store.save_state(context.workspace_id, state)
                    high_drift = float(drift["drift_score"]) < -seed.drift_correction_threshold and str(drift["drift_direction"]) == "away_seed"
                    if high_drift:
                        gravity_correction(
                            graph=deps.graph, motif_registry=deps.motif_registry,
                            embedder=owner.kernel.embedder, seed=seed,
                            agent_id=context.agent_id, step=int(context.step), drift_info=drift,
                        )
                    reflex_key = (context.workspace_id, context.agent_id)
                    was_high = owner._last_drift_was_high.get(reflex_key, False)
                    owner._last_drift_was_high[reflex_key] = high_drift
                    if high_drift and not was_high and owner.drift_reflex_callback is not None:
                        try:
                            owner.drift_reflex_callback(context.workspace_id, context.agent_id, dict(drift))
                        except Exception:
                            owner._log.exception("drift_reflex_callback raised for ws=%s agent=%s", context.workspace_id, context.agent_id)
        except Exception:
            pass

    def _run_checkpoint(self, context: FabricPostWriteContext) -> None:
        deps = self._deps
        owner = deps.owner
        if not (owner._checkpoint_enable and int(context.step) > 0 and int(context.step) % owner._checkpoint_interval == 0):
            return
        try:
            motif_summary = None
            try:
                registry = deps.workspace.motif_regs.get(context.chosen_domain)
                if registry:
                    motif_summary = deps.build_motif_summary(registry)
            except Exception as exc:
                owner._log.debug("checkpoint motif summary build failed: %s", exc)
            shard_snapshot = None
            try:
                private_directory = os.path.join(owner.data_dir, "workspaces", context.workspace_id, "agents", context.agent_id, "private", "embeddings")
                shard_snapshot = deps.build_shard_snapshot(private_directory, base_dir=owner.data_dir)
            except Exception as exc:
                owner._log.debug("checkpoint shard snapshot build failed for path=%s: %s", private_directory, exc)
            character_state = None
            try:
                from dataclasses import asdict
                state = owner.character_store.load_state(context.workspace_id, context.agent_id)
                if state:
                    character_state = asdict(state)
            except Exception as exc:
                owner._log.debug("checkpoint character state load failed: %s", exc)
            if deps.kernel_context is None:
                owner._log.debug("checkpoint skipped: KernelRuntimeContext missing for %s", deps.agent_key)
            else:
                deps.save_checkpoint(
                    data_dir=owner.data_dir, workspace_id=context.workspace_id,
                    agent_id=context.agent_id, step=int(context.step),
                    model_state=deps.model_state, corridor_monitor=deps.kernel_context.mon,
                    kernel_runtime_context=deps.kernel_context, character_state_dict=character_state,
                    motif_summary=motif_summary, shard_snapshot=shard_snapshot,
                    max_checkpoints=owner._checkpoint_max_keep,
                )
        except Exception as exc:
            owner._log.debug("checkpoint save failed for step=%s: %s", context.step, exc)

    def _run_compression(self, context: FabricPostWriteContext) -> None:
        owner = self._deps.owner
        if not (owner._compress_enable and int(context.step) >= owner._compress_min_step):
            return
        try:
            from .compression import check_hard_cap, try_compress
            event = try_compress(owner, context.agent_id, dict(context.tri_mod), int(context.step), workspace_id=context.workspace_id)
            if event and (event.compressed + event.exported_deep) > 0:
                logging.getLogger("torment.compression").info("compression at step %s: %d compressed, %d exported deep (trigger=%s)", context.step, event.compressed, event.exported_deep, event.trigger)
            hard_cap_event = check_hard_cap(owner, context.agent_id, int(context.step), workspace_id=context.workspace_id)
            if hard_cap_event and (hard_cap_event.compressed + hard_cap_event.exported_deep) > 0:
                logging.getLogger("torment.compression").warning("HARD CAP compression at step %s: %d compressed, %d exported deep", context.step, hard_cap_event.compressed, hard_cap_event.exported_deep)
        except Exception:
            pass

    def _run_proposal(self, context: FabricPostWriteContext) -> str | None:
        deps = self._deps
        coupling_mode = str(deps.identity.seed.get("coupling_mode", "read_only"))
        if not (context.stored and context.scope == "private" and coupling_mode in ("propose", "sync") and context.half_life_days is not None):
            return None
        if not deps.proposal_allowed(
            deps.identity, deps.workspace.domain_policies.get(context.chosen_domain, {}),
            context.created_motif, context.promotion_score, context.strength,
            context.confidence, tri_mod=dict(context.tri_mod),
        ):
            return None
        registry = deps.workspace.proposals.get(context.chosen_domain)
        if registry is None:
            return None
        proposal = registry.submit(
            agent_id=context.agent_id, summary=context.summary, embedding=context.embedding,
            mtype=context.memory_type, confidence=context.confidence, strength=context.strength,
            half_life_days=float(context.half_life_days),
        )
        deps.owner.ident_store.save(deps.identity)
        return proposal.proposal_id

    def _run_bridges(self, context: FabricPostWriteContext) -> None:
        tear = float(context.tri_mod.get("tearing_risk", 0.0))
        probability = float(context.tri_mod.get("bridge_p", 0.08)) * (1.0 - 0.40 * tear)
        threshold = float(context.tri_mod.get("bridge_sim", 0.86)) + (0.03 * tear)
        probability = float(np.clip(probability, 0.02, 0.12))
        threshold = float(np.clip(threshold, 0.84, 0.92))
        if context.stored and self._deps.random_chance(probability):
            self._deps.workspace.bridges.suggest(self._deps.workspace.motif_regs, sim_threshold=threshold, max_new=5)


__all__ = [
    "FabricPostWriteContext",
    "FabricPostWriteOutcome",
    "FabricPostWriteRuntimePort",
    "LegacyFabricPostWriteAdapter",
    "LegacyFabricPostWriteDependencies",
    "PostWriteStorageOutcome",
]
