# cognition/pipeline.py
"""
Pipeline Orchestrator — wires the single-pass cognition pipeline.

  TaskPacket → Router → Apertures → Roles (sequential) → Reintegration → Response

This is the main entry point called by the /cognition/run endpoint.
It composes all components without itself being a role or service.

See AGENT_SPINE_PLAN.md §1 ("single-pass pipeline, request in → response out").
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

_log = logging.getLogger(__name__)

from cognition.task_models import TaskPacket, RoutingDecision, ReintegrationResult
from cognition.router import route
from cognition.apertures import MemoryContext, build_memory_context
from cognition.reintegration import reintegrate
from cognition.drift import DriftCheckFn
from schemas.role_output import RoleOutput
from roles import ROLE_REGISTRY, ROLE_EXECUTION_ORDER


def run_cognition_pipeline(
    task: TaskPacket,
    query_fn: Optional[Callable] = None,
    character_fn: Optional[Callable] = None,
    drift_check_fn: Optional[DriftCheckFn] = None,
    primary_domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Execute the full cognition pipeline and return a structured result.

    Parameters
    ----------
    task : TaskPacket
        The incoming request.
    query_fn : callable, optional
        Memory query function for aperture building (wraps fabric.query).
    character_fn : callable, optional
        Character context retrieval function.
    drift_check_fn : callable, optional
        Drift measurement function (only called for identity routes).
    primary_domains : list[str], optional
        Domain ranking from fabric's domain router.

    Returns
    -------
    dict
        Structured response with keys: ok, task_id, final_answer,
        merged_findings, dissent, memory_effects, drift_report,
        governance_rejections, role_summaries, routing.
    """
    try:
        # --- 1. Route ---
        routing = route(task, primary_domains=primary_domains)

        # --- 2. Build aperture context ---
        # Wrap drift_check_fn to return a dict for aperture's drift_snapshot,
        # since downstream consumers (skeptic, archivist) expect dict access.
        drift_fn_for_aperture = None
        if drift_check_fn is not None:
            def drift_fn_for_aperture(ws_id, ag_id):
                report = drift_check_fn(ws_id, ag_id)
                return report.to_dict() if hasattr(report, 'to_dict') else report

        memory_context = build_memory_context(
            aperture_name=routing.aperture,
            workspace_id=task.workspace_id,
            agent_id=task.agent_id,
            query_text=task.user_input,
            domain_id=primary_domains[0] if primary_domains else None,
            query_fn=query_fn,
            character_fn=character_fn,
            drift_fn=drift_fn_for_aperture,
        )

        # --- 3. Execute roles sequentially ---
        role_outputs: List[RoleOutput] = []
        for role_name in ROLE_EXECUTION_ORDER:
            if role_name not in routing.roles_to_activate:
                continue
            role_cls = ROLE_REGISTRY.get(role_name)
            if role_cls is None:
                continue
            role = role_cls()
            output = role.run(task, memory_context, role_outputs)
            role_outputs.append(output)

        # --- 4. Reintegrate ---
        result = reintegrate(
            task=task,
            routing=routing,
            role_outputs=role_outputs,
            memory_context=memory_context,
            drift_check_fn=drift_check_fn if routing.require_drift_check else None,
        )

        # --- 5. Build response ---
        return _build_response(task, routing, result)

    except Exception as exc:
        _log.exception("Cognition pipeline failed for task %s", task.task_id)
        return {
            "ok": False,
            "task_id": task.task_id,
            "error": "Cognition pipeline failed",
            "error_type": "InternalError",
        }


def _build_response(
    task: TaskPacket,
    routing: RoutingDecision,
    result: ReintegrationResult,
) -> Dict[str, Any]:
    """Build the JSON-serializable response dict."""
    return {
        "ok": True,
        "task_id": task.task_id,
        "final_answer": result.final_answer,
        "merged_findings": result.merged_findings,
        "dissent": result.dissent,
        "memory_effects": result.memory_effects,
        "drift_report": result.drift_report.to_dict() if result.drift_report else None,
        "governance_rejections": result.governance_rejections,
        "role_summaries": [
            {
                "role": out.role_name,
                "summary": out.summary,
                "confidence": out.confidence,
                "findings_count": len(out.findings),
                "contradictions_count": len(out.contradictions),
                "proposals_count": len(out.memory_proposals),
            }
            for out in result.role_outputs
        ],
        "routing": {
            "effective_aperture": routing.aperture,
            "roles_activated": routing.roles_to_activate,
            "drift_check_required": routing.require_drift_check,
            "skeptic_pass_required": routing.require_skeptic_pass,
        },
    }
