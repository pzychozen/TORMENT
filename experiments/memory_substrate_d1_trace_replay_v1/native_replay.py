"""Explicit native replay over A3D/A3D10 without a MemoryGraph fallback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Any, Callable

from torment_service.post_write_runtime import FabricPostWriteContext, PostWriteStorageOutcome
from torment_service.substrate.fabric_native_routing import NativeFabricMemoryRouter, NativeFabricRouteRequest
from torment_service.substrate.native_post_write_runtime import NativeFabricPostWriteAdapter, NativePostWriteRouteWitness

from .legacy_capture import LegacyCapturedEvent, LegacyStorageFacingFacts
from .protocol import D1ProtocolError


_NATIVE_STORAGE_TABLES = (
    "objects", "object_revisions", "legacy_object_aliases", "memory_runtime_enumeration_orders",
    "provenance_records", "object_revision_governance", "relationships", "relationship_revisions",
    "representations", "representation_payloads", "operations", "semantic_transitions",
    "object_revision_effects", "relationship_revision_effects",
)


@dataclass(frozen=True)
class NativeCoreStorageSnapshot:
    """Exact durable-count snapshot used only for D1's NO_WRITE gate."""

    table_counts: tuple[tuple[str, int], ...]

    @classmethod
    def capture(cls, core_database_path: str | Path) -> "NativeCoreStorageSnapshot":
        database = Path(core_database_path).resolve()
        if database.suffix.lower() != ".db" or not database.is_file():
            raise D1ProtocolError("D1 NO_WRITE snapshot requires an existing native core database")
        with sqlite3.connect(str(database)) as connection:
            counts = tuple(
                (table, int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]))
                for table in _NATIVE_STORAGE_TABLES
            )
        return cls(counts)


@dataclass(frozen=True)
class NativeReplayOutcome:
    route_attempt: Any | None
    post_write_outcome: Any | None
    storage_outcome: PostWriteStorageOutcome
    operation_key: str | None


class NativeReplayHarness:
    """Use native-owned selection; never accept a legacy graph or target EID."""

    def __init__(
        self,
        *,
        router: NativeFabricMemoryRouter,
        post_write: NativeFabricPostWriteAdapter,
        native_storage_snapshot: Callable[[], NativeCoreStorageSnapshot],
    ) -> None:
        self._router = router
        self._post_write = post_write
        self._native_storage_snapshot = native_storage_snapshot

    @staticmethod
    def _request(facts: LegacyStorageFacingFacts) -> NativeFabricRouteRequest:
        return NativeFabricRouteRequest(
            workspace_id=facts.workspace_id, scope=facts.scope, agent_id=facts.agent_id,
            domain_id=facts.domain_id, native_operation_key=facts.native_operation_key,
            embedder_lane=facts.embedder_lane, summary=facts.summary,
            memory_type=facts.memory_type, memory_class=facts.memory_class,
            strength=facts.strength, confidence=facts.confidence, half_life_days=facts.half_life_days,
            logical_step=facts.logical_step, created_ts=facts.created_ts,
            last_active_ts=facts.last_active_ts, last_reinforced_ts=facts.last_reinforced_ts,
            incoming_embedding=facts.embedding, provenance=facts.provenance, governance=facts.governance,
            flexible_payload=facts.flexible_payload, raw_links=(), qualified_link_targets=(),
            attach_threshold=facts.attach_threshold, stability_delta=facts.stability_delta,
            prior_symbol=facts.prior_symbol, prior_symbol_trace=facts.prior_symbol_trace,
            prior_motif_id=facts.prior_motif_id, prior_tension=facts.prior_tension,
            last_tool_refresh_ts=facts.last_tool_refresh_ts, contradiction_guard=facts.contradiction_guard,
        )

    @staticmethod
    def _context(facts: LegacyStorageFacingFacts, *, outcome: PostWriteStorageOutcome, eid: int | None, motifs: tuple[str, ...]) -> FabricPostWriteContext:
        return FabricPostWriteContext.make(
            workspace_id=facts.workspace_id, agent_id=facts.agent_id, scope=facts.scope,
            chosen_domain=facts.domain_id, step=facts.logical_step, storage_outcome=outcome,
            stored=outcome is not PostWriteStorageOutcome.NO_WRITE, eid=eid,
            created_motif=None, motif_ids=motifs, half_life_days=facts.half_life_days,
            summary=facts.summary, embedding=facts.embedding, memory_class=facts.memory_class,
            memory_type=facts.memory_type, strength=facts.strength, confidence=facts.confidence,
            promotion_score=0.0, stability_delta=facts.stability_delta, tri_mod=facts.tri_mod,
            debug=facts.debug, srg_state=facts.srg_state, phase_durations=facts.phase_durations,
            state_symbol=None, affect_tag=facts.affect_tag, affect_conf=facts.affect_conf,
            skip_packet_emission=facts.skip_packet_emission,
        )

    def replay(self, event: LegacyCapturedEvent) -> NativeReplayOutcome:
        facts = event.native_input()
        if not event.observed_outcome.stored:
            before = self._native_storage_snapshot()
            context = self._context(facts, outcome=PostWriteStorageOutcome.NO_WRITE, eid=None, motifs=())
            post = self._post_write.run(context, route_witness=NativePostWriteRouteWitness(None, None))
            after = self._native_storage_snapshot()
            if after != before:
                raise D1ProtocolError("M5 NO_WRITE changed durable native storage")
            return NativeReplayOutcome(None, post, PostWriteStorageOutcome.NO_WRITE, None)
        attempt = self._router.route(self._request(facts))
        if not attempt.qualification.eligible or attempt.result is None:
            raise D1ProtocolError(f"qualified native route refused stored D1 request: {attempt.qualification.reason_code}")
        result = attempt.result
        outcome = PostWriteStorageOutcome.REINFORCED_EXISTING if result.reinforced else PostWriteStorageOutcome.CREATED_NEW
        context = self._context(facts, outcome=outcome, eid=result.eid, motifs=tuple(result.motifs))
        post = self._post_write.run(
            context,
            route_witness=NativePostWriteRouteWitness(result, facts.native_operation_key),
        )
        return NativeReplayOutcome(attempt, post, outcome, facts.native_operation_key)
