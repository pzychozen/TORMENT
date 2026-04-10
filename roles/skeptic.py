# roles/skeptic.py
"""
Skeptic Role — flags weak reasoning, contradiction, contamination, and overreach.

Input:  TaskPacket + all other role outputs so far
Output: RoleOutput with flags, uncertainty markers, contamination warnings

The skeptic is the guardian of Invariants C (preservable disagreement),
E (drift checks), and G (trust hierarchy). It reviews all prior role outputs
and flags anything suspicious.

v0.1 is deterministic — pattern-based checks, not LLM reasoning.

See docs/archive/AGENT_SPINE_PLAN.md §7 (Skeptic).
"""
from __future__ import annotations

from typing import List

from roles.base import RoleBase
from cognition.task_models import TaskPacket
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.provenance import Provenance, STATUS_SKEPTIC_PASSED, STATUS_SKEPTIC_FLAGGED


class Skeptic(RoleBase):
    """Flags weak reasoning, contradiction, contamination, and overreach."""

    name = "skeptic"

    def execute(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        findings: List[str] = []
        contradictions: List[str] = []
        uncertainties: List[str] = []
        recommendations: List[str] = []

        flags_raised = 0

        # --- Check 1: Low-confidence prior outputs ---
        for out in prior_outputs:
            if out.confidence < 0.5:
                findings.append(
                    f"LOW CONFIDENCE: {out.role_name} reported "
                    f"confidence={out.confidence:.2f}"
                )
                flags_raised += 1
            if out.uncertainties:
                for u in out.uncertainties:
                    findings.append(f"[{out.role_name} uncertainty] {u}")

        # --- Check 2: Cross-role contradictions ---
        all_findings = {}
        for out in prior_outputs:
            all_findings[out.role_name] = out.findings

        contradiction_pairs = _detect_contradictions(prior_outputs)
        for pair in contradiction_pairs:
            contradictions.append(
                f"{pair['role_a']} vs {pair['role_b']}: "
                f"\"{pair['claim_a'][:60]}\" contradicts \"{pair['claim_b'][:60]}\""
            )
            flags_raised += 1

        # --- Check 3: Memory proposal overreach ---
        for out in prior_outputs:
            for mp in out.memory_proposals:
                issues = _check_proposal_safety(mp, memory_context)
                for issue in issues:
                    findings.append(f"PROPOSAL FLAG [{mp.proposal_id[:12]}]: {issue}")
                    flags_raised += 1

        # --- Check 4: Identity contamination ---
        if memory_context.aperture_name == "protected":
            contamination = _check_identity_contamination(task, prior_outputs)
            for warning in contamination:
                findings.append(f"CONTAMINATION WARNING: {warning}")
                flags_raised += 1

        # --- Check 5: Drift awareness ---
        if memory_context.has_drift_snapshot:
            drift = memory_context.drift_snapshot
            total = drift.get("total_drift", 0.0)
            if total >= 0.35:
                findings.append(
                    f"DRIFT ALERT: total_drift={total:.3f} — "
                    f"durable identity writes should be blocked"
                )
                recommendations.append("Block all durable identity-sensitive writes")
                flags_raised += 1
            elif total >= 0.20:
                findings.append(
                    f"DRIFT WARNING: total_drift={total:.3f} — "
                    f"provisional writes only"
                )
                recommendations.append("Downgrade to provisional writes only")

        # --- Check 6: Missing context ---
        if not prior_outputs:
            uncertainties.append("No prior role outputs to review — skeptic has nothing to check")
        if memory_context.total_memories == 0:
            uncertainties.append("No memory context — cannot verify against history")

        # --- Verdict ---
        if flags_raised == 0:
            findings.append("All checks passed — no flags raised")
            recommendations.append("Proceed with normal processing")
            verdict = STATUS_SKEPTIC_PASSED
        else:
            findings.append(f"Raised {flags_raised} flag(s) — review recommended")
            verdict = STATUS_SKEPTIC_FLAGGED

        # --- Confidence: inversely related to flags ---
        confidence = max(0.3, 1.0 - (flags_raised * 0.1))

        provenance = Provenance.from_role(
            role_name=self.name,
            task_id=task.task_id,
            confidence=confidence,
        )
        # Tag the provenance with the skeptic verdict
        provenance.verification_status = verdict

        return RoleOutput(
            role_name=self.name,
            summary=f"Review: {flags_raised} flags | verdict: {verdict}",
            findings=findings,
            recommendations=recommendations,
            uncertainties=uncertainties,
            contradictions=contradictions,
            confidence=confidence,
            provenance=provenance,
        )


# ============================================================================
# Internal checks
# ============================================================================

def _detect_contradictions(prior_outputs: List[RoleOutput]) -> List[dict]:
    """Detect simple contradictions between role outputs.

    v0.1 heuristic: look for negation patterns between findings of
    different roles ("should" vs "should not", positive vs negative framing).
    """
    contradictions = []

    negation_pairs = [
        ("should", "should not"),
        ("can", "cannot"),
        ("safe", "unsafe"),
        ("proceed", "block"),
        ("approve", "reject"),
        ("valid", "invalid"),
        ("correct", "incorrect"),
    ]

    for i, out_a in enumerate(prior_outputs):
        for out_b in prior_outputs[i + 1:]:
            for finding_a in out_a.findings + out_a.recommendations:
                for finding_b in out_b.findings + out_b.recommendations:
                    fa_lower = finding_a.lower()
                    fb_lower = finding_b.lower()
                    for pos, neg in negation_pairs:
                        if (pos in fa_lower and neg in fb_lower) or \
                           (neg in fa_lower and pos in fb_lower):
                            contradictions.append({
                                "role_a": out_a.role_name,
                                "role_b": out_b.role_name,
                                "claim_a": finding_a,
                                "claim_b": finding_b,
                                "topic": f"{pos}/{neg} disagreement",
                            })
    return contradictions


def _check_proposal_safety(
    mp, memory_context: MemoryContext
) -> List[str]:
    """Check a memory proposal for safety issues."""
    issues = []

    # High strength proposals are suspicious
    if mp.proposed_strength > 0.9:
        issues.append(
            f"Very high proposed_strength ({mp.proposed_strength:.2f}) — "
            f"may overwrite existing memories (Invariant G)"
        )

    # Very long half-life for non-insight memories
    if mp.half_life_days > 90 and mp.memory_type == "episode":
        issues.append(
            f"Episode with half_life={mp.half_life_days} days — "
            f"episodes should typically decay faster"
        )

    # Provenance check
    if mp.provenance is None:
        issues.append("Missing provenance (Invariant B violation)")
    elif mp.provenance.derivation_depth > 3:
        issues.append(
            f"Deep derivation chain (depth={mp.provenance.derivation_depth}) — "
            f"trust may be diluted"
        )

    return issues


def _check_identity_contamination(
    task: TaskPacket, prior_outputs: List[RoleOutput]
) -> List[str]:
    """Check for potential identity contamination in protected aperture.

    Looks for patterns where an output might be trying to modify core
    identity without proper governance gates.
    """
    warnings = []

    identity_modify_patterns = [
        "rewrite", "replace", "override", "overwrite",
        "change personality", "new identity", "forget",
    ]

    for out in prior_outputs:
        for rec in out.recommendations:
            rec_lower = rec.lower()
            for pattern in identity_modify_patterns:
                if pattern in rec_lower:
                    warnings.append(
                        f"{out.role_name} recommends '{rec[:60]}' — "
                        f"may modify core identity"
                    )
                    break

    return warnings
