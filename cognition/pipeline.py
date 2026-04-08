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
    ingest_fn: Optional[Callable] = None,
    lookup_fn: Optional[Callable] = None,
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

        # --- 4b. Archivist write-back (v2.4.2) ---
        # Ingest approved memory proposals into the fabric. This closes the
        # cognition→memory loop.
        #
        # DISABLED BY DEFAULT — requires TORMENT_ARCHIVIST_WRITEBACK=1.
        # Provenance is now plumbed through fabric.ingest() (v2.4.x),
        # so write-back memories are tagged with ProvenanceV1 and
        # distinguishable from user ingest. The env-var gate remains
        # as a safety measure until the full provenance path is tested
        # with real queries.
        import os as _os
        _writeback_enabled = _os.environ.get("TORMENT_ARCHIVIST_WRITEBACK", "0").strip() == "1"
        writeback_results: list = []
        if _writeback_enabled:
            writeback_results = _write_back_approved(
                task, result, ingest_fn,
                lookup_fn=lookup_fn,
                memory_context=memory_context,
            )

        # --- 5. Build response ---
        resp = _build_response(task, routing, result)
        if writeback_results:
            resp["writeback"] = writeback_results
        return resp

    except Exception as exc:
        _log.exception("Cognition pipeline failed for task %s", task.task_id)
        return {
            "ok": False,
            "task_id": task.task_id,
            "error": "Cognition pipeline failed",
            "error_type": "InternalError",
        }


_WRITEBACK_MAX_PER_RUN = 5  # Hard cap on proposals ingested per pipeline run


def _write_back_approved(
    task: TaskPacket,
    result: ReintegrationResult,
    ingest_fn: Optional[Callable],
    lookup_fn: Optional[Callable] = None,
    memory_context: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Ingest archivist-approved memory proposals back into the fabric.

    Implements the TORMENT 2.4.x Recursion-Safety Policy (Rules A–F):
      Rule A: reject if any parent_eid has archivist-origin provenance
      Rule B: any archivist parent → reject (strict, not majority-based)
      Rule C: unknown/missing parent provenance → reject
      Rule D: archivist-origin memories may be retrieved but not re-written
      Rule E: effective archivist depth >= 1 → blocked
      Rule F: reinforcement/resurfacing does not reset provenance origin

    Parameters
    ----------
    lookup_fn : callable, optional
        lookup_fn(workspace_id, agent_id, eid) -> dict or None
        Returns the payload dict for a memory entity. Needed for parent
        provenance inspection. If None, parent inspection is skipped and
        the safety posture defaults to allowing only parentless proposals.
    memory_context : MemoryContext, optional
        The retrieval context from this pipeline run. Used to extract
        the actual parent memory EIDs (the retrieved memories that the
        roles used to form their proposals).
    """
    if ingest_fn is None:
        return []

    # Late import to avoid circular dependency at module load
    from torment_service.provenance_v1 import ProvenanceV1

    # Safe parent source_types for first pass (per GPT policy)
    _SAFE_PARENT_SOURCE_TYPES = frozenset({"user_input", "tool_result", "memory"})

    approved = [
        p for p in result.all_memory_proposals
        if p.is_approved and p.content
    ]

    if not approved:
        return []

    # Pre-filter: skip proposals whose spine-level provenance already
    # indicates archivist origin (fast path, no lookup needed).
    approved = [
        p for p in approved
        if not (p.provenance
                and getattr(p.provenance, 'source_role', None) == 'archivist_writeback')
    ]

    # Bounded: cap per-run writes
    approved = approved[:_WRITEBACK_MAX_PER_RUN]

    # --- Extract retrieved memory EIDs from the pipeline's memory context ---
    # These are the ACTUAL parent memories: the ones the roles saw and used
    # to form their proposals. The spine-level Provenance.parent_ids contains
    # task IDs (strings like "tsk_abc123"), not memory EIDs — those are
    # useless for recursion-safety checks.
    _context_eids: List[int] = []
    _log.info(
        "Archivist write-back: memory_context present=%s, type=%s",
        memory_context is not None,
        type(memory_context).__name__ if memory_context is not None else "N/A",
    )
    if memory_context is not None:
        for mem in (getattr(memory_context, 'private_memories', []) or []):
            _eid = mem.get("eid")
            if _eid is not None:
                try:
                    _context_eids.append(int(_eid))
                except (ValueError, TypeError) as e:
                    _log.debug("Skipping non-integer private eid %r: %s", _eid, e)
        for mem in (getattr(memory_context, 'shared_memories', []) or []):
            _eid = mem.get("eid")
            if _eid is not None:
                try:
                    _context_eids.append(int(_eid))
                except (ValueError, TypeError) as e:
                    _log.debug("Skipping non-integer shared eid %r: %s", _eid, e)
    # Deduplicate, preserve order
    _seen_eids: set = set()
    _deduped_eids: List[int] = []
    for _e in _context_eids:
        if _e not in _seen_eids:
            _seen_eids.add(_e)
            _deduped_eids.append(_e)
    _context_eids = _deduped_eids
    _log.info(
        "Archivist write-back: extracted %d context EIDs: %s",
        len(_context_eids), _context_eids[:10],  # log first 10 max
    )

    results = []
    for proposal in approved:
        # Parent EIDs = the retrieved memories from this pipeline run.
        # Every proposal in this run was influenced by the same retrieval
        # context, so they share the same parent set.
        _parent_eids = _context_eids

        # --- Recursion-safety check (Rules A, B, C, E) ---
        # Inspect stored provenance of each parent memory.
        _safe = True
        _rejection_reason: Optional[str] = None

        if _parent_eids and lookup_fn is not None:
            for parent_eid in _parent_eids:
                try:
                    parent_payload = lookup_fn(
                        task.workspace_id, task.agent_id, parent_eid
                    )
                except Exception:
                    parent_payload = None

                if parent_payload is None:
                    # Could not retrieve parent → treat as unknown
                    _safe = False
                    _rejection_reason = "unknown_parent_provenance"
                    break

                parent_prov = parent_payload.get("provenance") if isinstance(parent_payload, dict) else None

                if not parent_prov:
                    # Rule C: missing provenance → not safe
                    _safe = False
                    _rejection_reason = "unknown_parent_provenance"
                    break

                # Rule A + E: archivist-origin parent → blocked
                p_source_role = parent_prov.get("source_role") or ""
                if "archivist" in p_source_role.lower():
                    _safe = False
                    _rejection_reason = "archivist_parent_blocked"
                    break

                # Rule B: check source_type is in safe set
                p_source_type = parent_prov.get("source_type", "")
                if p_source_type not in _SAFE_PARENT_SOURCE_TYPES:
                    _safe = False
                    _rejection_reason = "unsafe_parent_source_type"
                    break

        elif _parent_eids and lookup_fn is None:
            # No lookup function available — cannot inspect parents.
            # Conservative posture: reject if there are parent EIDs we can't verify.
            _safe = False
            _rejection_reason = "unknown_parent_provenance"

        # else: no parent_eids → proposal derives from context, not specific
        # memories. Allow (this is typical for first-generation proposals).

        if not _safe:
            results.append({
                "proposal_id": proposal.proposal_id,
                "ingested": False,
                "rejected": True,
                "rejection_reason": _rejection_reason,
                "parent_eids": _parent_eids,
                "source_role": getattr(proposal.provenance, 'source_role', None) if proposal.provenance else None,
            })
            _log.info(
                "Archivist write-back REJECTED proposal %s: %s (parents: %s)",
                proposal.proposal_id, _rejection_reason, _parent_eids,
            )
            continue

        # --- Build ingest-level provenance and write ---
        try:
            _log.info(
                "Archivist write-back: building provenance for proposal %s with parent_eids=%s",
                proposal.proposal_id, _parent_eids[:10],
            )
            wb_provenance = ProvenanceV1.for_cognition_writeback(
                source_role="archivist_writeback",
                parent_eids=_parent_eids,
                notes=f"proposal_id={proposal.proposal_id}",
            )

            ingest_fn(
                workspace_id=task.workspace_id,
                agent_id=task.agent_id,
                text=proposal.content,
                domain_id=proposal.target_domain,
                supplied_summary=proposal.summary,
                provenance=wb_provenance.to_dict(),
            )
            results.append({
                "proposal_id": proposal.proposal_id,
                "ingested": True,
                "target_domain": proposal.target_domain,
                "memory_type": proposal.memory_type,
                "provenance_write_path": wb_provenance.write_path,
            })
            _log.info(
                "Archivist write-back: ingested proposal %s → domain %s (provenance: %s)",
                proposal.proposal_id, proposal.target_domain, wb_provenance.write_path,
            )
        except Exception as exc:
            results.append({
                "proposal_id": proposal.proposal_id,
                "ingested": False,
                "error": str(exc),
            })
            _log.warning(
                "Archivist write-back failed for proposal %s: %s",
                proposal.proposal_id, exc,
            )

    return results


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
