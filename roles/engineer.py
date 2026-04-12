# roles/engineer.py
"""
Engineer Role — produces implementation-ready plan or action structure.

Input:  TaskPacket + interpreted intent (from interpreter) + memory aperture
Output: RoleOutput with structured plan, concrete steps, implementation notes

The v0.1 engineer is a deterministic structure builder.
It reads the interpreter's findings and the memory context to produce
actionable steps. No LLM calls.

See docs/archive/AGENT_SPINE_PLAN.md §7 (Engineer).
"""
from __future__ import annotations

from typing import List, Optional

from roles.base import RoleBase
from cognition.task_models import TaskPacket
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.provenance import Provenance
from schemas.memory_proposal import MemoryProposal


class Engineer(RoleBase):
    """Produces implementation-ready plans and action structures."""

    name = "engineer"

    def execute(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        findings: List[str] = []
        recommendations: List[str] = []
        uncertainties: List[str] = []
        memory_proposals: List[MemoryProposal] = []

        # --- Consume interpreter output ---
        interpreter_output = _find_role_output(prior_outputs, "interpreter")
        if interpreter_output:
            findings.append(
                f"Building on interpreter analysis (confidence: "
                f"{interpreter_output.confidence:.2f})"
            )
            # Inherit relevant findings
            for f in interpreter_output.findings:
                if f.startswith("Key phrases:") or f.startswith("Classified intent:"):
                    findings.append(f"[from interpreter] {f}")
        else:
            uncertainties.append("No interpreter output available — working from raw input")

        # --- Analyze task scope ---
        user_text = task.user_input.strip()
        scope = _assess_scope(user_text)
        findings.append(f"Scope assessment: {scope}")

        # --- Build action structure ---
        steps = _build_action_steps(user_text, memory_context, interpreter_output)
        if steps:
            findings.append(f"Action plan: {len(steps)} steps identified")
            for i, step in enumerate(steps, 1):
                recommendations.append(f"Step {i}: {step}")
        else:
            uncertainties.append("Could not derive concrete action steps")
            recommendations.append("Requires clarification or additional context")

        # --- Memory-informed recommendations ---
        if memory_context.total_memories > 0:
            findings.append(
                f"Consulted {memory_context.total_memories} memories for context"
            )
            # Check if any memories are relevant to the task
            relevant = _find_relevant_memories(user_text, memory_context)
            if relevant:
                findings.append(f"Found {len(relevant)} relevant prior memories")
                for mem_text in relevant[:3]:
                    findings.append(f"[prior context] {mem_text[:100]}")

        # --- Propose memory write if substantial work ---
        if len(steps) >= 3 and scope in ("large", "medium"):
            prov = Provenance.from_role(
                role_name=self.name,
                task_id=task.task_id,
                confidence=0.7,
            )
            mp = MemoryProposal.create(
                summary=f"Engineering plan for: {user_text[:80]}",
                content=f"Action steps: {'; '.join(steps)}",
                target_domain=memory_context.domain_id or "engineering",
                proposed_strength=0.5,
                half_life_days=14.0,
                memory_type="episode",
                provenance=prov,
            )
            memory_proposals.append(mp)
            findings.append("Proposed memory write for engineering plan")

        # --- Confidence ---
        confidence = 0.85
        if not interpreter_output:
            confidence -= 0.15
        if not steps:
            confidence -= 0.20
        if not memory_context.total_memories:
            confidence -= 0.05

        provenance = Provenance.from_role(
            role_name=self.name,
            task_id=task.task_id,
            confidence=max(0.0, min(1.0, confidence)),
        )

        return RoleOutput(
            role_name=self.name,
            summary=f"Plan: {len(steps)} steps | scope: {scope} | {len(memory_proposals)} proposals",
            findings=findings,
            recommendations=recommendations,
            uncertainties=uncertainties,
            memory_proposals=memory_proposals,
            confidence=max(0.0, min(1.0, confidence)),
            provenance=provenance,
        )


# ============================================================================
# Internal helpers
# ============================================================================

def _find_role_output(
    prior_outputs: List[RoleOutput], role_name: str
) -> Optional[RoleOutput]:
    """Find the output from a specific role in prior outputs."""
    for out in prior_outputs:
        if out.role_name == role_name:
            return out
    return None


def _assess_scope(text: str) -> str:
    """Assess task scope: small, medium, large."""
    words = len(text.split())
    if words > 50:
        return "large"
    elif words > 15:
        return "medium"
    return "small"


def _build_action_steps(
    user_text: str,
    memory_context: MemoryContext,
    interpreter_output: Optional[RoleOutput],
) -> List[str]:
    """Build a list of action steps from the task.

    v0.1 heuristic: split on common delimiters, enumerate sub-tasks,
    and add context-gathering steps.
    """
    steps: List[str] = []
    text = user_text.strip()

    # If text contains numbered items or bullet-like structure, extract them
    import re
    numbered = re.findall(r'(?:^|\n)\s*\d+[.)]\s*(.+)', text)
    if numbered:
        steps.extend([s.strip() for s in numbered])
        return steps

    # If text contains "and" or "then" connectors, split
    if " then " in text.lower():
        parts = text.lower().split(" then ")
        steps.extend([p.strip().capitalize() for p in parts if p.strip()])
        return steps

    # Single task — wrap in analysis + execute + verify
    steps.append(f"Analyze: {text[:80]}")
    if memory_context.total_memories > 0:
        steps.append("Review relevant prior memory for context")
    steps.append(f"Execute: {text[:80]}")
    steps.append("Verify output meets requirements")

    return steps


def _find_relevant_memories(
    user_text: str, memory_context: MemoryContext
) -> List[str]:
    """Find memories that might be relevant to the user's request.

    v0.1 heuristic: simple word overlap check.
    """
    user_words = set(user_text.lower().split())
    relevant = []

    for mem in memory_context.private_memories + memory_context.shared_memories + memory_context.deep_memories:
        text = mem.get("text", mem.get("summary", ""))
        if not text:
            continue
        mem_words = set(text.lower().split())
        overlap = user_words & mem_words
        # Require at least 2 non-trivial overlapping words
        meaningful = {w for w in overlap if len(w) > 3}
        if len(meaningful) >= 2:
            relevant.append(text)

    return relevant
