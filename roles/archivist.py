# roles/archivist.py
"""
Archivist Role — evaluates memory effects and durable write proposals.

Input:  TaskPacket + all prior role outputs + drift report (if required)
Output: RoleOutput containing a list of MemoryProposals with approve/reject decisions

The archivist is the ONLY path to durable memory writes (Invariant A).
It enforces:
  - Invariant A: gated writes (only archivist-approved proposals proceed)
  - Invariant G: low-trust cannot overwrite high-trust
  - Drift-aware gating: if drift report requires block, reject identity-sensitive proposals

v0.1 is deterministic — rule-based approval, not LLM judgment.

See docs/archive/AGENT_SPINE_PLAN.md §7 (Archivist).
"""
from __future__ import annotations

from typing import List, Optional

from roles.base import RoleBase
from cognition.task_models import TaskPacket
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.provenance import Provenance, STATUS_SKEPTIC_FLAGGED
from schemas.memory_proposal import MemoryProposal
from schemas.drift_report import DriftReport


class Archivist(RoleBase):
    """Evaluates memory proposals and gates durable writes."""

    name = "archivist"

    def execute(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        findings: List[str] = []
        recommendations: List[str] = []
        uncertainties: List[str] = []
        reviewed_proposals: List[MemoryProposal] = []

        # --- Collect all proposals from prior roles ---
        all_proposals = _collect_proposals(prior_outputs)
        findings.append(f"Received {len(all_proposals)} memory proposal(s) to review")

        # --- Get skeptic verdict ---
        skeptic_output = _find_role_output(prior_outputs, "skeptic")
        skeptic_verdict = _get_skeptic_verdict(skeptic_output)
        if skeptic_verdict:
            findings.append(f"Skeptic verdict: {skeptic_verdict}")

        # --- Get drift info ---
        drift_report = _build_drift_from_context(memory_context)

        # --- Review each proposal ---
        for proposal in all_proposals:
            decision, reason = _review_proposal(
                proposal=proposal,
                skeptic_output=skeptic_output,
                drift_report=drift_report,
                memory_context=memory_context,
            )

            if decision == "approved":
                proposal.approve()
                findings.append(
                    f"APPROVED [{proposal.proposal_id[:12]}]: "
                    f"{proposal.summary[:60]}"
                )
            else:
                proposal.reject(reason)
                findings.append(
                    f"REJECTED [{proposal.proposal_id[:12]}]: {reason}"
                )

            reviewed_proposals.append(proposal)

        # --- Summary stats ---
        approved = sum(1 for p in reviewed_proposals if p.is_approved)
        rejected = sum(1 for p in reviewed_proposals if p.is_rejected)
        findings.append(f"Review complete: {approved} approved, {rejected} rejected")

        if rejected > 0:
            recommendations.append(
                "Some proposals were rejected — check governance_rejections in result"
            )

        if drift_report and drift_report.requires_block:
            recommendations.append(
                "Drift is elevated — all identity-sensitive durable writes blocked"
            )

        if not all_proposals:
            findings.append("No memory proposals to review — pass-through")

        # --- Confidence ---
        confidence = 0.95 if not uncertainties else 0.8

        provenance = Provenance.from_role(
            role_name=self.name,
            task_id=task.task_id,
            confidence=confidence,
        )

        return RoleOutput(
            role_name=self.name,
            summary=f"Archival review: {approved} approved, {rejected} rejected of {len(all_proposals)}",
            findings=findings,
            recommendations=recommendations,
            uncertainties=uncertainties,
            memory_proposals=reviewed_proposals,
            confidence=confidence,
            provenance=provenance,
        )


# ============================================================================
# Internal helpers
# ============================================================================

def _find_role_output(
    prior_outputs: List[RoleOutput], role_name: str
) -> Optional[RoleOutput]:
    """Find the output from a specific role."""
    for out in prior_outputs:
        if out.role_name == role_name:
            return out
    return None


def _collect_proposals(prior_outputs: List[RoleOutput]) -> List[MemoryProposal]:
    """Collect all memory proposals from all prior roles."""
    proposals = []
    for out in prior_outputs:
        proposals.extend(out.memory_proposals)
    return proposals


def _get_skeptic_verdict(skeptic_output: Optional[RoleOutput]) -> Optional[str]:
    """Extract the skeptic's verification status."""
    if skeptic_output is None:
        return None
    if skeptic_output.provenance:
        return skeptic_output.provenance.verification_status
    return None


def _build_drift_from_context(memory_context: MemoryContext) -> Optional[DriftReport]:
    """Build a DriftReport from the memory context's drift snapshot."""
    if not memory_context.has_drift_snapshot:
        return None
    snap = memory_context.drift_snapshot
    if isinstance(snap, dict):
        return DriftReport.from_dict(snap)
    return None


def _review_proposal(
    proposal: MemoryProposal,
    skeptic_output: Optional[RoleOutput],
    drift_report: Optional[DriftReport],
    memory_context: MemoryContext,
) -> tuple:
    """Review a single proposal. Returns (decision, reason).

    Rules (in order of precedence):
    1. Missing provenance → reject (Invariant B)
    2. Drift block + identity-sensitive → reject (Invariant E)
    3. Skeptic flagged + high strength → reject (Invariant G caution)
    4. Deep derivation + high strength → reject (Invariant G)
    5. Otherwise → approve
    """
    # Rule 1: Provenance is mandatory
    if proposal.provenance is None:
        return ("rejected", "Missing provenance (Invariant B)")

    # Rule 2: Drift block prevents identity-sensitive writes
    if drift_report and drift_report.requires_block:
        if memory_context.aperture_name == "protected":
            return ("rejected", f"Drift block (total_drift={drift_report.total_drift:.3f})")

    # Rule 3: Drift yellow zone → only allow low-strength provisionals
    if drift_report and not drift_report.allows_durable_write:
        if proposal.proposed_strength > 0.7:
            return (
                "rejected",
                f"Drift in {drift_report.zone} zone — "
                f"high-strength ({proposal.proposed_strength:.2f}) proposals blocked"
            )

    # Rule 4: Skeptic flagged concerns + high strength = too risky
    if skeptic_output and skeptic_output.provenance:
        if skeptic_output.provenance.verification_status == STATUS_SKEPTIC_FLAGGED:
            if proposal.proposed_strength > 0.8:
                return (
                    "rejected",
                    f"Skeptic flagged concerns — "
                    f"high-strength ({proposal.proposed_strength:.2f}) proposal blocked"
                )

    # Rule 5: Deep derivation chain with high strength (Invariant G)
    if proposal.provenance.derivation_depth > 3 and proposal.proposed_strength > 0.7:
        return (
            "rejected",
            f"Deep derivation (depth={proposal.provenance.derivation_depth}) "
            f"with high strength — trust dilution (Invariant G)"
        )

    # Rule 6: Very high strength episodes are suspicious
    if proposal.proposed_strength > 0.95 and proposal.memory_type == "episode":
        return (
            "rejected",
            "Episode with near-maximum strength — requires explicit governance approval"
        )

    # Default: approve
    return ("approved", "")
