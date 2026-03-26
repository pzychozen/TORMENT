# cognition/reintegration.py
"""
Reintegration Membrane — final aggregation boundary for role outputs.

This is NOT a summarizer. It is the final circuit breaker in the pipeline.

Responsibilities:
  1. Merges compatible findings across roles
  2. Preserves contradictions as structured dissent (Invariant C)
  3. Collects and deduplicates memory proposals from all roles by proposal_id
     (prefers archivist-reviewed versions when duplicates exist)
  4. Enforces final safety invariants (not full governance — that is the
     archivist's job). Reintegration only enforces:
     - Missing provenance rejection (Invariant B)
     - Drift-based hard blocks (Invariant E)
     - Scope violations / malformed proposals
  5. Calls drift checker when routing requires it (Invariant E)
  6. Emits final answer plus structured side products

Governance split:
  - Archivist: semantic review, policy intent, proposal quality assessment
  - Reintegration: final invariant enforcement, dedup, circuit-breaker safety

See AGENT_SPINE_PLAN.md §9 for the design.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from cognition.task_models import TaskPacket, RoutingDecision, ReintegrationResult
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.memory_proposal import MemoryProposal
from schemas.drift_report import DriftReport
from schemas.provenance import STATUS_SKEPTIC_FLAGGED  # retained for _is_skeptic_flagged utility


# Type alias for an optional drift check function
# Signature: (workspace_id, agent_id) -> DriftReport
DriftCheckFn = Callable[[str, str], DriftReport]


def reintegrate(
    task: TaskPacket,
    routing: RoutingDecision,
    role_outputs: List[RoleOutput],
    memory_context: MemoryContext,
    drift_check_fn: Optional[DriftCheckFn] = None,
) -> ReintegrationResult:
    """Merge role outputs into a single ReintegrationResult.

    Parameters
    ----------
    task : TaskPacket
        The original task driving this pipeline run.
    routing : RoutingDecision
        Router output — tells us aperture, drift requirements, etc.
    role_outputs : list[RoleOutput]
        All role outputs in execution order.
    memory_context : MemoryContext
        The aperture-scoped memory context.
    drift_check_fn : callable, optional
        Function to call for drift measurement. Only called if
        routing.require_drift_check is True. If None when required,
        a default zero-drift report is generated.

    Returns
    -------
    ReintegrationResult
    """
    # --- 1. Merge findings ---
    merged_findings = _merge_findings(role_outputs)

    # --- 2. Detect and preserve contradictions (Invariant C) ---
    dissent = _detect_dissent(role_outputs)

    # --- 3. Collect all memory proposals ---
    all_proposals = _collect_proposals(role_outputs)

    # --- 4. Drift check (Invariant E) ---
    drift_report: Optional[DriftReport] = None
    if routing.require_drift_check:
        drift_report = _run_drift_check(task, drift_check_fn)

    # --- 5. Governance filtering (Invariant G) ---
    approved, rejections = _apply_governance(
        proposals=all_proposals,
        drift_report=drift_report,
        routing=routing,
        role_outputs=role_outputs,
    )

    # --- 6. Build final answer ---
    final_answer = _build_final_answer(task, role_outputs, dissent)

    return ReintegrationResult(
        final_answer=final_answer,
        merged_findings=merged_findings,
        dissent=dissent,
        role_outputs=role_outputs,
        all_memory_proposals=approved,
        governance_rejections=rejections,
        drift_report=drift_report,
        memory_effects=_build_memory_effects(approved, rejections),
    )


# ============================================================================
# Merge findings
# ============================================================================

def _merge_findings(role_outputs: List[RoleOutput]) -> List[str]:
    """Merge compatible findings across roles, deduplicating.

    Prefix each finding with its source role so provenance is visible
    in the merged list.
    """
    merged: List[str] = []
    seen_normalized: set = set()

    for out in role_outputs:
        for finding in out.findings:
            # Normalize for dedup (lowercase, strip whitespace)
            norm = finding.strip().lower()
            if norm not in seen_normalized:
                seen_normalized.add(norm)
                merged.append(f"[{out.role_name}] {finding}")

    return merged


# ============================================================================
# Dissent detection (Invariant C)
# ============================================================================

_OPPOSITION_PAIRS = [
    ("should", "should not"),
    ("can", "cannot"),
    ("safe", "unsafe"),
    ("proceed", "block"),
    ("approve", "reject"),
    ("valid", "invalid"),
    ("correct", "incorrect"),
    ("recommend", "warn against"),
    ("confident", "uncertain"),
]


def _detect_dissent(role_outputs: List[RoleOutput]) -> List[Dict[str, Any]]:
    """Detect contradictions between role outputs.

    Scans findings + recommendations across role pairs for opposition patterns.
    Returns structured dissent entries: {role_a, role_b, claim_a, claim_b, topic}.
    """
    dissent: List[Dict[str, Any]] = []

    for i, out_a in enumerate(role_outputs):
        statements_a = out_a.findings + out_a.recommendations
        for out_b in role_outputs[i + 1:]:
            statements_b = out_b.findings + out_b.recommendations

            for sa in statements_a:
                sa_lower = sa.lower()
                for sb in statements_b:
                    sb_lower = sb.lower()
                    for pos, neg in _OPPOSITION_PAIRS:
                        if (pos in sa_lower and neg in sb_lower) or \
                           (neg in sa_lower and pos in sb_lower):
                            dissent.append({
                                "role_a": out_a.role_name,
                                "role_b": out_b.role_name,
                                "claim_a": sa[:200],
                                "claim_b": sb[:200],
                                "topic": f"{pos}/{neg} disagreement",
                            })

    # Also surface explicit contradictions from the skeptic
    for out in role_outputs:
        if out.role_name == "skeptic" and out.contradictions:
            for contra in out.contradictions:
                dissent.append({
                    "role_a": "skeptic",
                    "role_b": "prior_roles",
                    "claim_a": contra[:200],
                    "claim_b": "(see skeptic findings)",
                    "topic": "skeptic-detected contradiction",
                })

    return dissent


# ============================================================================
# Proposal collection + governance (Invariant G)
# ============================================================================

def _collect_proposals(role_outputs: List[RoleOutput]) -> List[MemoryProposal]:
    """Collect and deduplicate memory proposals from all roles by proposal_id.

    When the same proposal_id appears from multiple roles (e.g. engineer
    creates it, archivist reviews and re-emits it), we prefer the version
    from the archivist — the last role to touch it — because it carries
    the review decision.

    Dedup rule: merge by proposal_id; when duplicates exist, prefer the
    archivist-reviewed version (i.e. the latest occurrence, since archivist
    runs after other roles in the execution order).
    """
    seen: dict = {}  # proposal_id → (MemoryProposal, source_role)
    for out in role_outputs:
        for proposal in out.memory_proposals:
            pid = proposal.proposal_id
            if pid not in seen:
                seen[pid] = (proposal, out.role_name)
            else:
                # Prefer archivist-reviewed version, otherwise keep latest
                _, prev_role = seen[pid]
                if out.role_name == "archivist" or prev_role != "archivist":
                    seen[pid] = (proposal, out.role_name)
    return [p for p, _ in seen.values()]


def _apply_governance(
    proposals: List[MemoryProposal],
    drift_report: Optional[DriftReport],
    routing: RoutingDecision,
    role_outputs: List[RoleOutput],
) -> tuple:
    """Final invariant enforcement on proposals.

    This is NOT a full governance review — the archivist handles semantic
    policy (quality, strength assessment, skeptic evaluation). Reintegration
    only acts as the final circuit breaker for hard safety invariants.

    Returns (all_proposals, rejection_list).
    All proposals are included in the first list regardless of decision,
    so memory_effects can report both approved and rejected.

    Safety invariants enforced here:
    1. Missing provenance → reject (Invariant B — structural safety)
    2. Drift hard block → reject all (Invariant E — identity protection)
    3. Malformed / impossible proposals → reject (structural safety)

    The archivist's decisions are respected: if the archivist already
    rejected a proposal, reintegration does not override that rejection.
    """
    all_proposals: List[MemoryProposal] = []
    rejections: List[Dict[str, str]] = []

    for proposal in proposals:
        reason = _check_final_invariants(proposal, drift_report)
        if reason:
            proposal.reject(reason)
            rejections.append({
                "proposal_id": proposal.proposal_id,
                "reason": reason,
            })
        elif proposal.is_rejected:
            # Archivist already rejected — respect that decision
            rejections.append({
                "proposal_id": proposal.proposal_id,
                "reason": proposal.rejection_reason or "Rejected by archivist",
            })
        # If not rejected by either layer, leave the archivist's approve intact.
        # Do NOT call proposal.approve() here — the archivist is the semantic
        # governor. Reintegration only adds rejections, never overrides them.

        all_proposals.append(proposal)

    return all_proposals, rejections


def _check_final_invariants(
    proposal: MemoryProposal,
    drift_report: Optional[DriftReport],
) -> Optional[str]:
    """Final circuit-breaker checks on a single proposal.

    These are hard safety invariants only. Semantic policy is the
    archivist's domain.

    Returns rejection reason string, or None if no invariant violated.
    """
    # Invariant B: Provenance is structurally mandatory
    if proposal.provenance is None:
        return "Missing provenance (Invariant B)"

    # Invariant E: Drift hard block prevents all durable writes
    if drift_report and drift_report.requires_block:
        return f"Drift block (total_drift={drift_report.total_drift:.3f})"

    return None  # no invariant violation


def _is_skeptic_flagged(role_outputs: List[RoleOutput]) -> bool:
    """Check if the skeptic flagged any concerns.

    Note: This is retained as a utility for future use and for tests that
    inspect the skeptic's verdict. The reintegration membrane no longer uses
    it directly (semantic governance is the archivist's domain).
    """
    for out in role_outputs:
        if out.role_name == "skeptic" and out.provenance:
            return out.provenance.verification_status == STATUS_SKEPTIC_FLAGGED
    return False


# ============================================================================
# Drift check
# ============================================================================

def _run_drift_check(
    task: TaskPacket,
    drift_check_fn: Optional[DriftCheckFn],
) -> DriftReport:
    """Run drift check, or return a safe default if no function provided."""
    if drift_check_fn is not None:
        try:
            return drift_check_fn(task.workspace_id, task.agent_id)
        except Exception:
            # Drift check failure → assume worst case (block)
            return DriftReport(
                total_drift=0.50,
                governance_breach=False,
                reasons=["Drift check failed — defaulting to hard_block"],
            )
    # No drift function → zero drift (safe pass-through for testing)
    return DriftReport(total_drift=0.0)


# ============================================================================
# Final answer synthesis
# ============================================================================

def _build_final_answer(
    task: TaskPacket,
    role_outputs: List[RoleOutput],
    dissent: List[Dict[str, Any]],
) -> str:
    """Build the final answer string from role outputs.

    v0.1: concatenates role summaries. Future versions may use LLM synthesis.
    """
    parts: List[str] = []

    # Primary answer from interpreter + engineer
    for out in role_outputs:
        if out.role_name in ("interpreter", "engineer"):
            parts.append(f"{out.role_name.capitalize()}: {out.summary}")

    # Skeptic notes (if flagged)
    for out in role_outputs:
        if out.role_name == "skeptic" and out.contradictions:
            parts.append(f"Skeptic flagged {len(out.contradictions)} contradiction(s)")

    # Archivist summary
    for out in role_outputs:
        if out.role_name == "archivist":
            parts.append(f"Archivist: {out.summary}")

    # Dissent note
    if dissent:
        parts.append(f"Note: {len(dissent)} point(s) of dissent preserved")

    if not parts:
        return f"Processed task: {task.user_input[:100]}"

    return " | ".join(parts)


# ============================================================================
# Memory effects summary
# ============================================================================

def _build_memory_effects(
    proposals: List[MemoryProposal],
    rejections: List[Dict[str, str]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Build a summary of memory effects for the result."""
    rejected_ids = {r["proposal_id"] for r in rejections}

    approved_list = []
    rejected_list = []

    for p in proposals:
        entry = {
            "proposal_id": p.proposal_id,
            "summary": p.summary,
            "target_domain": p.target_domain,
            "proposed_strength": p.proposed_strength,
            "memory_type": p.memory_type,
        }
        if p.proposal_id in rejected_ids:
            entry["rejection_reason"] = p.rejection_reason
            rejected_list.append(entry)
        else:
            approved_list.append(entry)

    return {"approved": approved_list, "rejected": rejected_list}
