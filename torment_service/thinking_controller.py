from __future__ import annotations

import re
from typing import Any, Dict, Optional

from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
    GeometricStanceContext,
    MemoryPlan,
    ReviewResult,
    TaskFrame,
    ThinkingResult,
)
from .stance_policy import determine_stance


QUESTION_PREFIXES = (
    "what",
    "why",
    "how",
    "when",
    "where",
    "who",
    "can",
    "could",
    "should",
    "would",
    "do",
    "does",
    "did",
    "is",
    "are",
    "am",
)

TOOL_HINT_WORDS = {
    "search",
    "find",
    "lookup",
    "inspect",
    "open",
    "read",
    "fetch",
    "scan",
    "analyze",
    "repair",
    "rebuild",
    "trace",
    "debug",
    "check",
}

GOVERNANCE_HINT_WORDS = {
    "delete",
    "remove",
    "governance",
    "policy",
    "security",
    "private",
    "shared",
    "collective",
    "canon",
    "protected",
    "reingest",
    "approve",
    "reject",
}

IDENTITY_HINT_WORDS = {
    "identity",
    "character",
    "drift",
    "seed",
    "self",
    "personality",
    "role",
    "who are you",
    "who am i",
}

LIVE_SOCIAL_HINT_WORDS = {
    "space",
    "live",
    "audio",
    "speak",
    "voice",
    "x space",
    "twitter space",
}

ARCHIVE_HINT_WORDS = {
    "document",
    "archive",
    "chunk",
    "pdf",
    "notes",
    "transcript",
}


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


class ThinkingController:
    """
    First-pass cognition controller for TORMENT.

    This version is intentionally heuristic-first:
    - bounded
    - inspectable
    - deterministic
    - easy to test
    """

    def frame_task(
        self,
        workspace_id: str,
        agent_id: str,
        raw_input: str,
        *,
        source_type: str = "user_text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskFrame:
        text = _normalize_text(raw_input)
        lower = text.lower()

        token_count = len(lower.split())
        has_question = lower.endswith("?") or lower.startswith(QUESTION_PREFIXES)
        ambiguity_score = self._estimate_ambiguity(lower)
        urgency = self._estimate_urgency(lower)
        tool_need = self._has_any(lower, TOOL_HINT_WORDS)
        governance_sensitive = self._has_any(lower, GOVERNANCE_HINT_WORDS)
        identity_sensitive = self._has_any(lower, IDENTITY_HINT_WORDS)
        live_social = self._has_any(lower, LIVE_SOCIAL_HINT_WORDS)
        archive_relevant = self._has_any(lower, ARCHIVE_HINT_WORDS)

        memory_need = bool(
            archive_relevant
            or identity_sensitive
            or "remember" in lower
            or "before" in lower
            or "previous" in lower
            or "past" in lower
            or token_count > 25
        )

        action_need = bool(
            tool_need
            or governance_sensitive
            or "create" in lower
            or "delete" in lower
            or "repair" in lower
            or "build" in lower
            or "run" in lower
        )

        confidence_need = 0.2
        if has_question:
            confidence_need += 0.2
        if governance_sensitive:
            confidence_need += 0.3
        if identity_sensitive:
            confidence_need += 0.2
        if ambiguity_score > 0.45:
            confidence_need += 0.2

        context_tags = []
        if archive_relevant:
            context_tags.append("archive")
        if governance_sensitive:
            context_tags.append("governance")
        if identity_sensitive:
            context_tags.append("identity")
        if live_social:
            context_tags.append("live_social")
        if tool_need:
            context_tags.append("tooling")

        return TaskFrame(
            workspace_id=workspace_id,
            agent_id=agent_id,
            raw_input=raw_input,
            normalized_input=text,
            source_type=source_type,
            context_tags=context_tags,
            urgency=urgency,
            ambiguity_score=ambiguity_score,
            confidence_need=min(confidence_need, 1.0),
            action_need=action_need,
            memory_need=memory_need,
            tool_need=tool_need,
            governance_sensitive=governance_sensitive,
            identity_sensitive=identity_sensitive,
            live_social=live_social,
            tone_hints={
                "question": has_question,
                "length_tokens": token_count,
            },
            metadata=metadata or {},
        )

    def choose_mode(self, frame: TaskFrame) -> CognitiveModeDecision:
        if frame.governance_sensitive:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.GOVERNED,
                reason="Governance-sensitive input requires stricter control.",
                allowed_depth=2,
                requires_self_review=True,
                may_escalate=True,
                confidence_floor=0.75,
            )

        if frame.live_social:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.LIVE_SOCIAL,
                reason="Live-social context requires compact and responsive cognition.",
                allowed_depth=1,
                requires_self_review=True,
                may_escalate=False,
                confidence_floor=0.55,
            )

        if frame.identity_sensitive:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.IDENTITY_SENSITIVE,
                reason="Identity-sensitive input should preserve continuity and drift safety.",
                allowed_depth=2,
                requires_self_review=True,
                may_escalate=True,
                confidence_floor=0.70,
            )

        if frame.tool_need:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.TOOL,
                reason="Task appears to require tool use or system inspection.",
                allowed_depth=2,
                requires_self_review=True,
                may_escalate=False,
                confidence_floor=0.60,
            )

        if frame.memory_need or "archive" in frame.context_tags:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.RETRIEVAL,
                reason="Task likely benefits from memory retrieval.",
                allowed_depth=2,
                requires_self_review=False,
                may_escalate=False,
                confidence_floor=0.50,
            )

        if frame.ambiguity_score >= 0.50 or frame.confidence_need >= 0.60:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.REFLECTIVE,
                reason="Ambiguity/confidence needs suggest a slower reflective pass.",
                allowed_depth=2,
                requires_self_review=True,
                may_escalate=False,
                confidence_floor=0.65,
            )

        return CognitiveModeDecision(
            chosen_mode=CognitiveMode.FAST,
            reason="Input appears direct and low-risk.",
            allowed_depth=1,
            requires_self_review=False,
            may_escalate=False,
            confidence_floor=0.40,
        )

    def build_memory_plan(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
    ) -> MemoryPlan:
        plan = MemoryPlan()

        plan.retrieve_core = True
        plan.retrieve_character_state = frame.identity_sensitive or mode.chosen_mode in {
            CognitiveMode.IDENTITY_SENSITIVE,
            CognitiveMode.LIVE_SOCIAL,
        }
        plan.retrieve_relational = frame.memory_need or frame.live_social
        plan.retrieve_archive = (
            "archive" in frame.context_tags
            or "document" in frame.normalized_input.lower()
        )
        plan.retrieve_deep = mode.chosen_mode in {
            CognitiveMode.REFLECTIVE,
            CognitiveMode.IDENTITY_SENSITIVE,
        }
        plan.retrieve_collective = (
            frame.governance_sensitive
            and "collective" in frame.normalized_input.lower()
        )

        plan.top_k_by_lane = {
            "core": 6,
            "relational": 4 if plan.retrieve_relational else 0,
            "archive": 4 if plan.retrieve_archive else 0,
            "deep": 3 if plan.retrieve_deep else 0,
            "collective": 2 if plan.retrieve_collective else 0,
        }

        plan.weight_by_lane = {
            "core": 1.0,
            "relational": 0.85 if plan.retrieve_relational else 0.0,
            "archive": 0.45 if plan.retrieve_archive else 0.0,
            "deep": 0.60 if plan.retrieve_deep else 0.0,
            "collective": 0.35 if plan.retrieve_collective else 0.0,
        }

        if frame.identity_sensitive:
            plan.safety_constraints.append("identity_must_outrank_archive")
        if frame.governance_sensitive:
            plan.safety_constraints.append("governance_review_before_execution")
        if plan.retrieve_collective:
            plan.safety_constraints.append("collective_context_non_dominant")

        if mode.chosen_mode == CognitiveMode.FAST:
            plan.max_token_budget = 1200
        elif mode.chosen_mode == CognitiveMode.LIVE_SOCIAL:
            plan.max_token_budget = 900
        else:
            plan.max_token_budget = 2400

        return plan

    def choose_action(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
        memory_plan: MemoryPlan,
    ) -> ActionDecision:
        lower = frame.normalized_input.lower()

        if frame.governance_sensitive:
            return ActionDecision(
                action=ActionType.GOVERNANCE_REVIEW,
                reason="Governance-sensitive request should route through governed execution.",
                requires_execution=True,
                payload={"route": "governed"},
            )

        if frame.tool_need:
            return ActionDecision(
                action=ActionType.USE_TOOL,
                reason="Input appears to require inspection, retrieval, or system action.",
                requires_execution=True,
                payload={"route": "tool"},
            )

        if frame.ambiguity_score > 0.72 and "?" not in lower:
            return ActionDecision(
                action=ActionType.ASK_CLARIFICATION,
                reason="High ambiguity with no explicit question suggests clarification is safer.",
                requires_execution=False,
            )

        if frame.live_social and len(frame.normalized_input.split()) < 3:
            return ActionDecision(
                action=ActionType.NO_OP,
                reason="Very short live-social turn likely not worth interrupting for.",
                requires_execution=False,
            )

        if "proposal" in lower or "share" in lower:
            return ActionDecision(
                action=ActionType.PROPOSE_SHARE,
                reason="Input appears to concern proposal/share flow.",
                requires_execution=True,
                payload={"route": "proposal"},
            )

        if memory_plan.retrieve_archive and ("note" in lower or "archive" in lower):
            return ActionDecision(
                action=ActionType.CREATE_ARCHIVE_NOTE,
                reason="Archive-oriented task suggests an archive note or archive-bound response.",
                requires_execution=True,
                payload={"route": "archive"},
            )

        return ActionDecision(
            action=ActionType.ANSWER,
            reason="Default response path is direct answer generation.",
            requires_execution=False,
        )

    def review(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
        action: ActionDecision,
        response_draft: Optional[str],
    ) -> ReviewResult:
        notes = []
        revised_text = None
        response_text = response_draft or ""

        if mode.requires_self_review:
            notes.append("self_review_required")

        if frame.governance_sensitive and action.action != ActionType.GOVERNANCE_REVIEW:
            return ReviewResult(
                approved=False,
                blocked=True,
                escalate=True,
                notes=["governance_sensitive_action_mismatch"],
            )

        if frame.identity_sensitive and "i am definitely" in response_text.lower():
            revised_text = response_text.replace("I am definitely", "I may be")
            notes.append("softened_identity_overconfidence")

        if len(response_text) > 1200 and mode.chosen_mode == CognitiveMode.LIVE_SOCIAL:
            revised_text = response_text[:900].rstrip() + "..."
            notes.append("trimmed_for_live_social")

        if revised_text is not None:
            return ReviewResult(
                approved=True,
                revised=True,
                notes=notes,
                revised_text=revised_text,
            )

        return ReviewResult(
            approved=True,
            revised=False,
            notes=notes,
        )

    def think(
        self,
        workspace_id: str,
        agent_id: str,
        raw_input: str,
        *,
        source_type: str = "user_text",
        metadata: Optional[Dict[str, Any]] = None,
        capabilities: Optional[Dict[str, bool]] = None,
        geometric_context: Optional[GeometricStanceContext] = None,
    ) -> ThinkingResult:
        frame = self.frame_task(
            workspace_id=workspace_id,
            agent_id=agent_id,
            raw_input=raw_input,
            source_type=source_type,
            metadata=metadata,
        )
        mode = self.choose_mode(frame)
        memory_plan = self.build_memory_plan(frame, mode)
        action = self.choose_action(frame, mode, memory_plan)

        response_draft = self._draft_response(frame, mode, action)
        review = self.review(frame, mode, action, response_draft)
        if review.revised and review.revised_text is not None:
            response_draft = review.revised_text

        # Optional stance layer — only active when contextual_abstention is on
        stance = determine_stance(
            frame, mode, memory_plan, action, review,
            capabilities=capabilities,
            geometric_context=geometric_context,
        )

        return ThinkingResult(
            task_frame=frame,
            mode_decision=mode,
            memory_plan=memory_plan,
            action_decision=action,
            review_result=review,
            response_draft=response_draft,
            stance=stance,
            geometric_context=geometric_context,
            debug={"controller_version": "0.3"},
        )

    def _draft_response(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
        action: ActionDecision,
    ) -> Optional[str]:
        if action.action == ActionType.NO_OP:
            return None

        if action.action == ActionType.ASK_CLARIFICATION:
            return "I need a little more specificity before I choose the right path."

        if action.action == ActionType.GOVERNANCE_REVIEW:
            return "This looks like a governed or safety-sensitive operation and should go through the controlled path."

        if action.action == ActionType.USE_TOOL:
            return "This looks like a task that should inspect state, retrieve context, or use a tool before answering."

        if action.action == ActionType.PROPOSE_SHARE:
            return "This appears to relate to proposal/share logic and should be evaluated through the proposal path."

        if action.action == ActionType.CREATE_ARCHIVE_NOTE:
            return "This appears archive-oriented and may be better handled as an archive-bound operation."

        return (
            f"Mode selected: {mode.chosen_mode.value}. "
            f"Input framed for agent '{frame.agent_id}' in workspace '{frame.workspace_id}'."
        )

    @staticmethod
    def _has_any(text: str, hints: set[str]) -> bool:
        return any(h in text for h in hints)

    @staticmethod
    def _estimate_urgency(text: str) -> float:
        score = 0.0
        if "urgent" in text or "asap" in text or "immediately" in text:
            score += 0.6
        if "now" in text or "quickly" in text:
            score += 0.2
        if "!" in text:
            score += 0.1
        return min(score, 1.0)

    @staticmethod
    def _estimate_ambiguity(text: str) -> float:
        score = 0.0
        if len(text.split()) < 4:
            score += 0.35
        if "maybe" in text or "sort of" in text or "kind of" in text:
            score += 0.20
        if text.count("?") > 1:
            score += 0.20
        if "something" in text or "stuff" in text or "thing" in text:
            score += 0.20
        return min(score, 1.0)