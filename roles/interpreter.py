# roles/interpreter.py
"""
Interpreter Role — normalizes task intent and suggests route.

Input:  TaskPacket + memory aperture (narrow/broad/protected)
Output: RoleOutput with interpreted intent, suggested route, relevant memory context

The v0.1 interpreter is a deterministic keyword/structure analyzer.
It does NOT call an LLM. It classifies intent, extracts key phrases,
and surfaces relevant memories from the aperture context.

See docs/archive/AGENT_SPINE_PLAN.md §7 (Interpreter).
"""
from __future__ import annotations

import re
from typing import List

from roles.base import RoleBase
from cognition.task_models import TaskPacket
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.provenance import Provenance


class Interpreter(RoleBase):
    """Normalizes task intent and surfaces relevant memory context."""

    name = "interpreter"

    def execute(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        findings: List[str] = []
        recommendations: List[str] = []
        uncertainties: List[str] = []

        user_text = task.user_input.strip()
        lower_text = user_text.lower()

        # --- Intent classification ---
        intent_type = _classify_intent(lower_text)
        findings.append(f"Classified intent: {intent_type}")
        findings.append(f"Effective mode: {task.mode}")
        findings.append(f"Aperture: {memory_context.aperture_name}")

        # --- Key phrase extraction (simple) ---
        key_phrases = _extract_key_phrases(user_text)
        if key_phrases:
            findings.append(f"Key phrases: {', '.join(key_phrases)}")

        # --- Memory context summary ---
        mem_count = memory_context.total_memories
        if mem_count > 0:
            findings.append(f"Memory context: {mem_count} memories available")
            # Surface top private memories as context
            for mem in memory_context.private_memories[:3]:
                text = mem.get("text", mem.get("summary", ""))
                if text:
                    findings.append(f"Relevant memory: {text[:120]}")
        else:
            uncertainties.append("No memory context available — operating without history")

        # --- Character context ---
        if memory_context.has_character_context:
            findings.append("Character context loaded")
        else:
            uncertainties.append("No character context in aperture")

        # --- Route suggestion ---
        if intent_type == "question":
            recommendations.append("Route: retrieval-heavy, prioritize memory context")
        elif intent_type == "action":
            recommendations.append("Route: action-oriented, prioritize engineering analysis")
        elif intent_type == "reflection":
            recommendations.append("Route: identity-sensitive, check drift before durable writes")
        else:
            recommendations.append("Route: general processing, balanced analysis")

        # --- Confidence ---
        confidence = 0.9 if key_phrases else 0.7
        if not memory_context.total_memories:
            confidence -= 0.1

        provenance = Provenance.from_role(
            role_name=self.name,
            task_id=task.task_id,
            confidence=confidence,
        )

        return RoleOutput(
            role_name=self.name,
            summary=f"Intent: {intent_type} | {len(key_phrases)} key phrases | {mem_count} memories",
            findings=findings,
            recommendations=recommendations,
            uncertainties=uncertainties,
            confidence=max(0.0, min(1.0, confidence)),
            provenance=provenance,
        )


# ============================================================================
# Internal helpers
# ============================================================================

_QUESTION_PATTERNS = [
    r"^(what|who|where|when|why|how|is|are|can|should|does|do|did)\b",
    r"\?$",
]
_ACTION_PATTERNS = [
    r"^(implement|build|create|fix|add|remove|refactor|write|deploy|run|test)\b",
]
_REFLECTION_PATTERNS = [
    r"\b(identity|who am i|self|persona|values|beliefs|character)\b",
    r"\b(reflect|introspect|meaning|purpose)\b",
]

_QUESTION_RE = [re.compile(p, re.IGNORECASE) for p in _QUESTION_PATTERNS]
_ACTION_RE = [re.compile(p, re.IGNORECASE) for p in _ACTION_PATTERNS]
_REFLECTION_RE = [re.compile(p, re.IGNORECASE) for p in _REFLECTION_PATTERNS]


def _classify_intent(text: str) -> str:
    """Classify user input into intent type."""
    for pat in _REFLECTION_RE:
        if pat.search(text):
            return "reflection"
    for pat in _ACTION_RE:
        if pat.search(text):
            return "action"
    for pat in _QUESTION_RE:
        if pat.search(text):
            return "question"
    return "general"


def _extract_key_phrases(text: str) -> List[str]:
    """Extract salient phrases (simple heuristic: capitalized runs + quoted strings)."""
    phrases = []

    # Quoted strings
    quoted = re.findall(r'"([^"]+)"', text)
    phrases.extend(quoted)
    quoted_single = re.findall(r"'([^']+)'", text)
    phrases.extend(quoted_single)

    # Capitalized multi-word runs (excluding sentence starts)
    # Look for sequences of capitalized words mid-sentence
    words = text.split()
    if len(words) > 2:
        run = []
        for i, w in enumerate(words[1:], 1):  # skip first word
            clean = re.sub(r'[^\w]', '', w)
            if clean and clean[0].isupper() and len(clean) > 1:
                run.append(w.strip('.,;:!?'))
            else:
                if len(run) >= 1:
                    phrases.append(' '.join(run))
                run = []
        if run:
            phrases.append(' '.join(run))

    # Deduplicate preserving order
    seen = set()
    result = []
    for p in phrases:
        if p.lower() not in seen and len(p) > 1:
            seen.add(p.lower())
            result.append(p)

    return result[:10]  # cap at 10
