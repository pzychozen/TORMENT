"""Offline Meridian Outage execution harness with injectable agent providers.

No provider is configured by default and this module makes no live model call.
The real-Fabric adapter is opt-in for a separately authorized characterization.
"""
from __future__ import annotations

import copy
import logging
import platform
import sys
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .results import RESULT_SCHEMA_PREREGISTRATION, RESULT_SCHEMA_VERSION, write_sealed_run
from .scoring import VALID_CLAIM_STANCES, score_run
from .spec import (
    EXPERIMENT_VERSION,
    FROZEN_BASELINE_COMMIT,
    VALID_CONDITIONS,
    VALID_N,
    assignment_manifest,
    assignment_manifest_sha256,
    cards_for_agent,
    corpus_sha256,
    ground_truth_sha256,
)


RESEARCH_INSTRUCTION = (
    "Inspect only the assigned Meridian Outage evidence. Identify likely causes, "
    "preserve card and source provenance, report uncertainty, and do not treat "
    "repetition as independent truth. Return structured findings for later "
    "deterministic synthesis."
)


@dataclass(frozen=True)
class ConditionConfig:
    condition: str
    hivemind_enabled: bool
    telemetry_enabled: bool
    collective_context_surfaced: bool
    naive_shared_content: bool

    @classmethod
    def for_condition(cls, condition: str) -> "ConditionConfig":
        configs = {
            "A_PRIVATE": cls(condition, False, False, False, False),
            "B1_TORMENT_MECHANISMS_ONLY": cls(condition, True, True, False, False),
            "B2_TORMENT_SALIENCE_SURFACED": cls(condition, True, True, True, False),
            "C_NAIVE_SHARED_CONTENT": cls(condition, False, False, False, True),
        }
        try:
            return configs[condition]
        except KeyError as exc:
            raise ValueError(f"invalid Meridian condition: {condition}") from exc

    def to_dict(self) -> dict[str, bool | str]:
        return {
            "condition": self.condition,
            "hivemind_enabled": self.hivemind_enabled,
            "telemetry_enabled": self.telemetry_enabled,
            "collective_context_surfaced": self.collective_context_surfaced,
            "naive_shared_content": self.naive_shared_content,
        }


class AgentProvider(Protocol):
    """Boundary for a future approved model or agent runtime provider."""

    def metadata(self) -> Mapping[str, Any]:
        """Return provider/model/configuration fields that are actually available."""

    def run_round(
        self,
        *,
        agent_id: str,
        round_number: int,
        instruction: str,
        assigned_cards: Sequence[Mapping[str, str]],
        collective_context: Mapping[str, Any] | None,
        naive_shared_findings: Sequence[Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        """Return findings, claims, and an optional structured final answer."""


class CoordinationAdapter(Protocol):
    """Harness-owned adapter; its API is deliberately smaller than Fabric."""

    def start(self, *, workspace_id: str, agent_ids: Sequence[str], config: ConditionConfig) -> None:
        """Initialize isolated condition state."""

    def ingest_findings(self, *, agent_id: str, findings: Sequence[Mapping[str, Any]]) -> None:
        """Store round-one findings through the current condition's mechanism."""

    def process_round_boundary(self) -> Mapping[str, Any]:
        """Perform the one frozen B1/B2 operator action."""

    def collective_context(self, *, agent_id: str) -> Mapping[str, Any]:
        """Read current Fabric collective context without transforming it."""

    def mechanism_metrics(self) -> Mapping[str, Any]:
        """Return observable production-artifact metrics only."""

    def cost_metrics(self) -> Mapping[str, Any]:
        """Return measured storage costs where the adapter owns observable paths."""

    def close(self) -> None:
        """Release condition-owned resources."""


class TelemetryCapture(logging.Handler):
    """Harness-local copy of structured Hivemind records; no production hook."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.records: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        telemetry = getattr(record, "hivemind_telemetry", None)
        if isinstance(telemetry, dict):
            self.records.append(copy.deepcopy(telemetry))


class TormentFabricAdapter:
    """Optional adapter over an externally constructed, condition-configured Fabric.

    The caller owns environment flag setup before creating the Fabric.  The
    adapter validates that it received the requested Hivemind/telemetry mode;
    it does not mutate production configuration itself.
    """

    def __init__(self, fabric: Any, *, owns_fabric: bool = False) -> None:
        self._fabric = fabric
        self._owns_fabric = owns_fabric
        self._workspace_id = ""
        self._step_by_agent: dict[str, int] = {}
        self._capture = TelemetryCapture()
        self._logger = logging.getLogger("torment.hivemind")
        self._boundary_results: list[dict[str, Any]] = []
        self._context_reads = 0
        self._context_query_seconds: list[float] = []
        self._proposals_drafted = 0
        self._live_agent_count = 0
        self._cost_start: dict[str, int] = {}
        self._data_root: Path | None = None

    @staticmethod
    def _path_bytes(path: Path) -> int:
        if not path.exists():
            return 0
        if path.is_file():
            return path.stat().st_size
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total

    def _graph_bytes(self) -> tuple[int, int]:
        private_paths = {
            Path(graph.data_dir)
            for graph in getattr(self._fabric, "private_graphs", {}).values()
            if getattr(graph, "data_dir", None)
        }
        workspace = self._fabric.get_workspace(self._workspace_id)
        shared_graph = workspace.shared_graphs.get("research")
        shared_path = Path(shared_graph.data_dir) if getattr(shared_graph, "data_dir", None) else None
        return (
            sum(self._path_bytes(path) for path in private_paths),
            self._path_bytes(shared_path) if shared_path is not None else 0,
        )

    def _current_costs(self) -> dict[str, int]:
        field = self._fabric._get_collective_field(self._workspace_id)
        private_bytes, shared_bytes = self._graph_bytes()
        return {
            "total": self._path_bytes(Path(self._fabric.data_dir)),
            "packets": self._path_bytes(Path(field._packets_path)),
            "events": self._path_bytes(Path(field._events_path)),
            "private_graphs": private_bytes,
            "shared_graph": shared_bytes,
        }

    def start(self, *, workspace_id: str, agent_ids: Sequence[str], config: ConditionConfig) -> None:
        if bool(getattr(self._fabric, "_hivemind_enable", False)) != config.hivemind_enabled:
            raise ValueError("Fabric Hivemind mode does not match condition")
        if bool(getattr(self._fabric, "_hivemind_telemetry_enable", False)) != config.telemetry_enabled:
            raise ValueError("Fabric telemetry mode does not match condition")
        data_root = Path(self._fabric.data_dir).resolve()
        if data_root.exists() and any(data_root.iterdir()):
            raise ValueError("Meridian real-Fabric data root must be fresh and empty")
        self._data_root = data_root
        self._workspace_id = workspace_id
        self._live_agent_count = len(agent_ids)
        self._fabric.get_workspace(workspace_id, domains=["research"])
        for agent_id in agent_ids:
            self._fabric.create_agent(workspace_id, agent_id)
            self._step_by_agent[agent_id] = 0
        self._logger.addHandler(self._capture)
        self._cost_start = self._current_costs()

    def ingest_findings(self, *, agent_id: str, findings: Sequence[Mapping[str, Any]]) -> None:
        for finding in findings:
            self._step_by_agent[agent_id] += 1
            card_ids = [str(card_id) for card_id in finding.get("card_ids", [])]
            text = str(finding.get("text", ""))
            self._fabric.ingest(
                workspace_id=self._workspace_id,
                agent_id=agent_id,
                text=text,
                step=self._step_by_agent[agent_id],
                domain_id="research",
                extra_payload={
                    "experiment": EXPERIMENT_VERSION,
                    "corpus_card_ids": card_ids,
                },
            )
            if finding.get("share_permitted") is True:
                self._fabric.propose_share(
                    workspace_id=self._workspace_id,
                    agent_id=agent_id,
                    summary=text,
                    domain_id="research",
                    mtype="fact",
                )
                self._proposals_drafted += 1

    def process_round_boundary(self) -> Mapping[str, Any]:
        result = self._fabric.process_proposals(
            self._workspace_id,
            "research",
        )
        self._boundary_results.append(dict(result))
        return result

    def collective_context(self, *, agent_id: str) -> Mapping[str, Any]:
        self._context_reads += 1
        started = time.perf_counter()
        response = self._fabric.query(
            self._workspace_id,
            agent_id,
            "Meridian Outage incident reconstruction",
            domain_id="research",
        )
        self._context_query_seconds.append(time.perf_counter() - started)
        context = response.get("collective_context", {})
        return copy.deepcopy(context) if isinstance(context, Mapping) else {}

    def mechanism_metrics(self) -> Mapping[str, Any]:
        field = self._fabric._get_collective_field(self._workspace_id)
        status = field.status()
        packets = field.recent_packets(limit=200)
        events = field.recent_events(limit=100000)
        event_degrees = Counter(
            agent_id
            for event in events
            for agent_id in event.get("participating_agents", [])
        )
        skip_reasons = Counter(
            record.get("skip_reason")
            for record in self._capture.records
            if not record.get("packet_emitted") and record.get("skip_reason")
        )
        pending = self._fabric.list_proposals(
            self._workspace_id,
            "research",
            status="pending",
        )
        approved = self._fabric.list_proposals(
            self._workspace_id,
            "research",
            status="approved",
        )
        support_agents_per_promoted_node: list[int] = []
        shared_graph = self._fabric.get_workspace(self._workspace_id).shared_graphs.get("research")
        if shared_graph is not None:
            for entity in getattr(shared_graph, "entities", {}).values():
                payload = getattr(entity, "payload", {}) or {}
                support_agents = payload.get("support_agents")
                if isinstance(support_agents, list):
                    support_agents_per_promoted_node.append(len(set(support_agents)))
        return {
            "packet_count": len(packets),
            "packet_count_total": status.get("packet_count_total", 0),
            "packet_skip_reasons": dict(sorted(skip_reasons.items())),
            "convergence_event_count": len(events),
            "event_participants": [event.get("participating_agents", []) for event in events],
            "semantic_similarity": [event.get("semantic_overlap") for event in events],
            "agent_degree_distribution": dict(sorted(event_degrees.items())),
            "packet_window_occupancy": status.get("packet_count_cached", 0),
            "distinct_agents_in_active_window": len(status.get("active_agents", [])),
            "fraction_live_agents_in_active_window": (
                len(status.get("active_agents", [])) / self._live_agent_count
                if self._live_agent_count else 0.0
            ),
            "per_agent_packet_occupancy": dict(sorted(Counter(
                packet.get("agent_id") for packet in packets
            ).items())),
            "convergence_coverage": len({
                agent_id for event in events for agent_id in event.get("participating_agents", [])
            }),
            "proposal_boundary_results": copy.deepcopy(self._boundary_results),
            "proposals_drafted": self._proposals_drafted,
            "proposal_groups": sum(
                int(result.get("approved_groups", 0)) for result in self._boundary_results
            ),
            "proposals_promoted": sum(
                int(result.get("approved", 0)) for result in self._boundary_results
            ),
            "proposals_pending": int(pending.get("count", 0)),
            "support_agents_per_promoted_node": support_agents_per_promoted_node,
            "echo_eligible_delivered_blocked": {
                "eligible": 0,
                "delivered": 0,
                "blocked": 0,
                "schedule": "not invoked in Meridian v1",
            },
            "reingest_dedup_outcomes": [],
            "collective_context_available_count": self._context_reads,
            "event_history_cumulative_count": len(events),
            "collective_context_query_latency_seconds": self._context_query_seconds,
            "workspace_isolation_check": {
                "field_workspace_matches_requested_workspace": (
                    status.get("workspace_id") == self._workspace_id
                ),
                "cross_workspace_probe": "not_run_in_dry_harness",
            },
            "experimental_data_root": str(self._data_root) if self._data_root is not None else None,
        }

    def cost_metrics(self) -> Mapping[str, Any]:
        current = self._current_costs()
        return {
            "disk_growth_bytes": current["total"] - self._cost_start.get("total", 0),
            "packet_event_file_growth_bytes": (
                current["packets"] - self._cost_start.get("packets", 0)
                + current["events"] - self._cost_start.get("events", 0)
            ),
            "private_graph_growth_bytes": (
                current["private_graphs"] - self._cost_start.get("private_graphs", 0)
            ),
            "shared_graph_growth_bytes": (
                current["shared_graph"] - self._cost_start.get("shared_graph", 0)
            ),
        }

    @property
    def telemetry_records(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._capture.records)

    @property
    def data_root(self) -> str | None:
        return str(self._data_root) if self._data_root is not None else None

    def close(self) -> None:
        self._logger.removeHandler(self._capture)
        if self._owns_fabric:
            self._fabric.close()


class NullCoordinationAdapter:
    """Private/C test adapter; records no Hivemind behavior or shared state."""

    def __init__(self) -> None:
        self._ingested: dict[str, list[dict[str, Any]]] = {}

    def start(self, *, workspace_id: str, agent_ids: Sequence[str], config: ConditionConfig) -> None:
        self._ingested = {agent_id: [] for agent_id in agent_ids}

    def ingest_findings(self, *, agent_id: str, findings: Sequence[Mapping[str, Any]]) -> None:
        self._ingested[agent_id].extend(copy.deepcopy(list(findings)))

    def process_round_boundary(self) -> Mapping[str, Any]:
        return {"operator_action": "none"}

    def collective_context(self, *, agent_id: str) -> Mapping[str, Any]:
        return {}

    def mechanism_metrics(self) -> Mapping[str, Any]:
        return {
            "packet_count": 0,
            "packet_skip_reasons": {},
            "convergence_event_count": 0,
            "event_participants": [],
            "semantic_similarity": [],
            "agent_degree_distribution": {},
            "packet_window_occupancy": 0,
            "distinct_agents_in_active_window": 0,
            "per_agent_packet_occupancy": {},
            "convergence_coverage": 0,
            "proposal_boundary_results": [],
            "echo_eligible_delivered_blocked": {
                "eligible": 0,
                "delivered": 0,
                "blocked": 0,
                "schedule": "not applicable",
            },
            "reingest_dedup_outcomes": [],
            "collective_context_available_count": 0,
            "workspace_isolation_check": {
                "status": "not_applicable_no_hivemind",
            },
        }

    def cost_metrics(self) -> Mapping[str, Any]:
        return {
            "disk_growth_bytes": None,
            "packet_event_file_growth_bytes": None,
            "private_graph_growth_bytes": None,
            "shared_graph_growth_bytes": None,
        }

    def close(self) -> None:
        return None


def _findings(output: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = output.get("findings", [])
    if not isinstance(raw, list):
        raise ValueError("provider findings must be a list")
    findings: list[dict[str, Any]] = []
    for finding in raw:
        if not isinstance(finding, Mapping) or not isinstance(finding.get("text"), str):
            raise ValueError("every finding must be a mapping with text")
        card_ids = finding.get("card_ids", [])
        if not isinstance(card_ids, list) or not all(isinstance(card_id, str) for card_id in card_ids):
            raise ValueError("finding card_ids must be a list of strings")
        findings.append(copy.deepcopy(dict(finding)))
    return findings


def _claims(output: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = output.get("claims", [])
    if not isinstance(raw, list):
        raise ValueError("provider claims must be a list")
    claims: list[dict[str, Any]] = []
    for claim in raw:
        if not isinstance(claim, Mapping):
            raise ValueError("every claim must be a mapping")
        normalized = copy.deepcopy(dict(claim))
        stance = normalized.get("stance", "asserts")
        if stance not in VALID_CLAIM_STANCES:
            raise ValueError(f"invalid Meridian claim stance: {stance!r}")
        normalized["stance"] = stance
        claims.append(normalized)
    return claims


def _naive_shared_findings(
    findings_by_agent: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """C's simple pool: cited findings, sorted mechanically, without TORMENT rules."""
    shared = [
        {"agent_id": agent_id, "text": str(finding["text"]), "card_ids": list(finding["card_ids"])}
        for agent_id, findings in findings_by_agent.items()
        for finding in findings
        if finding.get("card_ids")
    ]
    return sorted(shared, key=lambda item: (item["agent_id"], item["text"], item["card_ids"]))


def _aggregate_final_answers(outputs: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Population-only deterministic union; never a substitute for an agent answer."""
    answers = [answer for _, answer in sorted(outputs.items()) if isinstance(answer, Mapping)]
    roots = Counter(
        str(answer.get("root_cause", "")) for answer in answers if answer.get("root_cause")
    )
    root_cause = ""
    if roots:
        highest_support = max(roots.values())
        root_cause = sorted(root for root, count in roots.items() if count == highest_support)[0]
    factors = sorted({
        str(factor)
        for answer in answers
        for factor in answer.get("contributing_factors", [])
        if isinstance(factor, str)
    })
    cited_card_ids = sorted({
        str(card_id)
        for answer in answers
        for card_id in answer.get("cited_card_ids", [])
        if isinstance(card_id, str)
    })
    return {
        "aggregation": "support_count_union_v1",
        "representative_root_rule": (
            "highest individual-agent support count; lexical order only breaks an equal-support tie; "
            "population diagnostic only"
        ),
        "root_cause": root_cause,
        "contributing_factors": factors,
        "cited_card_ids": cited_card_ids,
    }


def _provider_metadata(provider: AgentProvider) -> dict[str, Any]:
    metadata = provider.metadata()
    if not isinstance(metadata, Mapping):
        raise ValueError("provider metadata must be a mapping")
    normalized = copy.deepcopy(dict(metadata))
    missing = sorted({"model_id", "session_isolation", "retry_policy"} - set(normalized))
    if missing:
        raise ValueError(f"provider metadata missing required fields: {missing}")
    if normalized["session_isolation"] not in {"per_agent_per_round", "per_agent"}:
        raise ValueError("Meridian v1 requires non-shared provider session isolation")
    if "retry_count" in normalized:
        if not isinstance(normalized["retry_count"], int) or normalized["retry_count"] < 0:
            raise ValueError("provider retry_count must be a non-negative integer")
    elif normalized.get("retry_observability") != "unavailable":
        raise ValueError("provider must report retry_count or retry_observability='unavailable'")
    return normalized


class MeridianOutageHarness:
    """Two-round offline runner; caller supplies provider and condition adapter."""

    def __init__(self, provider: AgentProvider, adapter: CoordinationAdapter) -> None:
        self._provider = provider
        self._adapter = adapter

    def run(
        self,
        *,
        output_root: Path,
        run_id: str,
        condition: str,
        n_agents: int,
        execution_commit: str = FROZEN_BASELINE_COMMIT,
        successor_kind: str | None = None,
    ) -> Path:
        if condition not in VALID_CONDITIONS:
            raise ValueError(f"invalid condition: {condition}")
        if n_agents not in VALID_N:
            raise ValueError(f"invalid N: {n_agents}")
        config = ConditionConfig.for_condition(condition)
        provider_metadata = _provider_metadata(self._provider)
        manifest = assignment_manifest(n_agents)
        assignments = manifest["assignments"]
        workspace_id = f"meridian-{condition.lower()}-{run_id}"
        started = time.perf_counter()
        visibility_ledger: list[dict[str, Any]] = []
        round_outputs: dict[str, dict[str, Any]] = {}
        round_inputs: dict[str, dict[str, Any]] = {}
        findings_by_agent: dict[str, list[dict[str, Any]]] = {}
        claims_by_agent: dict[str, list[dict[str, Any]]] = {}
        failures: list[dict[str, str]] = []

        self._adapter.start(
            workspace_id=workspace_id,
            agent_ids=sorted(assignments),
            config=config,
        )
        try:
            round_1_started = time.perf_counter()
            for agent_id in sorted(assignments):
                assigned_cards = cards_for_agent(manifest, agent_id)
                output = dict(self._provider.run_round(
                    agent_id=agent_id,
                    round_number=1,
                    instruction=RESEARCH_INSTRUCTION,
                    assigned_cards=assigned_cards,
                    collective_context=None,
                    naive_shared_findings=[],
                ))
                findings = _findings(output)
                claims = _claims(output)
                output["claims"] = claims
                round_outputs[f"round_1:{agent_id}"] = output
                round_inputs[f"round_1:{agent_id}"] = {
                    "collective_context": None,
                    "naive_shared_findings": [],
                }
                findings_by_agent[agent_id] = findings
                claims_by_agent[agent_id] = claims
                visibility_ledger.append({
                    "agent_id": agent_id,
                    "round": 1,
                    "assigned_card_ids": list(assignments[agent_id]),
                    "naive_shared_card_ids": [],
                    "collective_context_available": False,
                    "collective_context_surfaced": False,
                })
                self._adapter.ingest_findings(agent_id=agent_id, findings=findings)
            round_1_seconds = time.perf_counter() - round_1_started

            boundary_started = time.perf_counter()
            operator_result: Mapping[str, Any] = {"operator_action": "none"}
            if config.hivemind_enabled:
                operator_result = self._adapter.process_round_boundary()
            naive_shared = _naive_shared_findings(findings_by_agent) if config.naive_shared_content else []
            boundary_seconds = time.perf_counter() - boundary_started

            round_2_started = time.perf_counter()
            for agent_id in sorted(assignments):
                assigned_cards = cards_for_agent(manifest, agent_id)
                collective_context: Mapping[str, Any] | None = None
                context_available = False
                if config.hivemind_enabled:
                    available_context = self._adapter.collective_context(agent_id=agent_id)
                    context_available = bool(available_context)
                    if config.collective_context_surfaced:
                        collective_context = available_context
                output = dict(self._provider.run_round(
                    agent_id=agent_id,
                    round_number=2,
                    instruction=RESEARCH_INSTRUCTION,
                    assigned_cards=assigned_cards,
                    collective_context=collective_context,
                    naive_shared_findings=naive_shared,
                ))
                claims = _claims(output)
                output["claims"] = claims
                round_outputs[f"round_2:{agent_id}"] = output
                round_inputs[f"round_2:{agent_id}"] = {
                    "collective_context": copy.deepcopy(collective_context),
                    "naive_shared_findings": copy.deepcopy(naive_shared),
                }
                claims_by_agent[agent_id].extend(claims)
                context_consumed = bool(
                    collective_context is not None
                    and output.get("collective_context_consumed") is True
                )
                visibility_ledger.append({
                    "agent_id": agent_id,
                    "round": 2,
                    "assigned_card_ids": list(assignments[agent_id]),
                    "naive_shared_card_ids": sorted({
                        card_id
                        for finding in naive_shared
                        for card_id in finding["card_ids"]
                    }),
                    "collective_context_available": context_available,
                    "collective_context_surfaced": collective_context is not None,
                    "collective_context_consumed": context_consumed,
                })
            round_2_seconds = time.perf_counter() - round_2_started

            final_outputs = {
                agent_id: (
                    dict(round_outputs[f"round_2:{agent_id}"].get("final_answer", {}))
                    if isinstance(round_outputs[f"round_2:{agent_id}"].get("final_answer", {}), Mapping)
                    else {}
                )
                for agent_id in sorted(assignments)
            }
            final_answer = _aggregate_final_answers(final_outputs)
            task_metrics = score_run(
                final_outputs,
                final_answer,
                claims_by_agent,
                findings_by_agent,
                assignments=assignments,
            )
            mechanism_metrics = dict(self._adapter.mechanism_metrics())
            mechanism_metrics.update({
                "collective_context_available_count": sum(
                    int(record["collective_context_available"])
                    for record in visibility_ledger if record["round"] == 2
                ),
                "collective_context_surfaced_count": sum(
                    int(record["collective_context_surfaced"])
                    for record in visibility_ledger if record["round"] == 2
                ),
                "collective_context_consumed_count": sum(
                    int(record.get("collective_context_consumed", False))
                    for record in visibility_ledger if record["round"] == 2
                ),
                "frozen_operator_schedule": {
                    "round_boundary": "process_proposals_once" if config.hivemind_enabled else "none",
                    "reingest_convergence": "not invoked",
                    "operator_result": dict(operator_result),
                },
            })
            total_seconds = time.perf_counter() - started
            cost_metrics = {
                "total_wall_clock_seconds": total_seconds,
                "round_1_wall_clock_seconds": round_1_seconds,
                "round_boundary_wall_clock_seconds": boundary_seconds,
                "round_2_wall_clock_seconds": round_2_seconds,
                "provider_call_count": len(round_outputs),
                "model_call_count": provider_metadata.get("model_call_count"),
                "model_tokens": None,
                "coordination_model_call_count": 0,
                "coordination_model_tokens": 0,
                **dict(self._adapter.cost_metrics()),
                "restart_time_seconds": None,
                "failure_retry_count": provider_metadata.get("retry_count"),
                "failure_retry_observability": provider_metadata.get(
                    "retry_observability", "reported"
                ),
                "human_operator_intervention_count": 0,
            }
            baseline = {
                "frozen_implementation_commit": FROZEN_BASELINE_COMMIT,
                "execution_commit": execution_commit,
            }
            if execution_commit != FROZEN_BASELINE_COMMIT:
                baseline["successor_kind"] = successor_kind
            result = {
                "schema_version": RESULT_SCHEMA_VERSION,
                "preregistration": RESULT_SCHEMA_PREREGISTRATION,
                "run_id": run_id,
                "experiment_version": EXPERIMENT_VERSION,
                "baseline": baseline,
                "condition": condition,
                "condition_config": config.to_dict(),
                "n_agents": n_agents,
                "seed": manifest["assignment_seed"],
                "corpus_sha256": corpus_sha256(),
                "ground_truth_sha256": ground_truth_sha256(),
                "assignment_manifest_sha256": assignment_manifest_sha256(n_agents),
                "provider": provider_metadata,
                "environment": {
                    "python": sys.version,
                    "platform": platform.platform(),
                    "live_model_calls": False,
                    "experimental_data_root": getattr(self._adapter, "data_root", None),
                },
                "timing": {
                    "round_1_seconds": round_1_seconds,
                    "round_boundary_seconds": boundary_seconds,
                    "round_2_seconds": round_2_seconds,
                    "total_seconds": total_seconds,
                },
                "task_metrics": task_metrics,
                "mechanism_metrics": mechanism_metrics,
                "cost_metrics": cost_metrics,
                "failure_ledger": failures,
                "visibility_ledger": visibility_ledger,
                "artifact_hashes": {},
            }
            telemetry_records = getattr(self._adapter, "telemetry_records", [])
            return write_sealed_run(
                output_root,
                result=result,
                raw_outputs={
                    "round_outputs": round_outputs,
                    "round_inputs": round_inputs,
                    "final_answer": final_answer,
                    "research_instruction": RESEARCH_INSTRUCTION,
                },
                telemetry_records=copy.deepcopy(telemetry_records),
            )
        except Exception as exc:
            failures.append({"stage": "harness", "error_type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            self._adapter.close()
