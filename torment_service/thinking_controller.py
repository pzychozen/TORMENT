from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional

from .thinking_models import (
    ActionDecision,
    ActionType,
    CognitiveMode,
    CognitiveModeDecision,
    DeliberationBundle,
    GeometricStanceContext,
    MemoryPlan,
    ReviewResult,
    TaskFrame,
    ThinkingResult,
)
from .stance_policy import determine_stance
from .reflection_trace import build_reflection_trace


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

# v0.1.0d: tool-intent tuning.
#
# With `code_exec` as the only declared tool family in v0.1, the hint
# words that should raise frame.tool_need are execution/computation
# verbs. Analytical verbs (analyze/explain/debug/trace/inspect/check)
# have been moved into ANALYTICAL_DEPTH_HINT_WORDS — they push
# confidence_need toward REFLECTIVE mode, NOT tool_need. Retrieval
# verbs (search/find/lookup/fetch/read/open/scan) have been moved into
# RETRIEVAL_HINT_WORDS and are explicitly unmapped in v0.1 because
# no retrieval tool family exists yet; they fall back to normal
# non-tool routing.
TOOL_HINT_WORDS = {
    "calculate",
    "compute",
    "execute",
    "evaluate",
    "run",
    "simulate",
}

# v0.1.0d: phrase-level triggers for tool_need. Substring-matched on
# lowered text. A single matching phrase is as strong as a single
# matching word in TOOL_HINT_WORDS. These override ambiguous single
# words (like the retrieval verbs below) because their presence is
# a much stronger signal that the user wants code execution.
TOOL_HINT_PHRASES = (
    "using python",
    "using code",
    "run code",
    "python code",
    "write and run",
    "programmatically",
)

# v0.1.0d: retrieval verbs — DECLARED but NOT MAPPED to any tool
# family in v0.1. Prompts containing these words fall back to normal
# non-tool routing (RETRIEVAL mode via memory_need, or ANSWER,
# depending on other signals). When a retrieval tool family like
# `web_fetch` or `read_file` is added to tool_registry.py, this set
# can be wired to raise tool_need for that family. Keeping the list
# here gives the intent a truthful home instead of silently dropping
# these words.
RETRIEVAL_HINT_WORDS = {
    "search",
    "find",
    "lookup",
    "fetch",
    "read",
    "open",
    "scan",
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

# §2A D1: collaborative/relational language that implies shared context
# and should trigger memory retrieval.  Space-padded pronouns avoid
# false positives (e.g. " we " won't match "awesome").
RELATIONAL_HINT_WORDS = {
    " we ",
    " our ",
    " us ",
    "agreed",
    "decided",
    "settled",
    "concluded",
    "stance",
    "position",
    "together",
}

# §2A D2 + v0.1.0d: analytical-depth cues that indicate the query
# needs deeper deliberation. Bumps confidence_need to cross the
# REFLECTIVE threshold.
#
# v0.1.0d additions: analytical verbs previously in TOOL_HINT_WORDS
# have been moved here. They push REFLECTIVE mode via confidence_need,
# which is what they actually mean semantically — a user saying
# "analyze why" wants deliberation, not a subprocess.
ANALYTICAL_DEPTH_HINT_WORDS = {
    # §2A D2 originals
    "why does",
    "pattern",
    "tradeoff",
    "assumption",
    "bias",
    "tension",
    "interact",
    "robust",
    "fragile",
    "usually",
    "tend to",
    "tends to",
    "behind the scenes",
    # v0.1.0d: analytical verbs relocated from TOOL_HINT_WORDS
    "analyze",
    "explain",
    "debug",
    "trace",
    "inspect",
    "check",
}

# ---------------------------------------------------------------------------
# Cognition feature flags — default OFF (opt-in via environment)
# When disabled, detection still runs for tagging/logging but the thinking
# controller will not escalate to the corresponding cognitive mode.
# ---------------------------------------------------------------------------

_SPINE_ENABLE = os.environ.get("TORMENT_SPINE_ENABLE", "1").strip() not in ("0", "false", "no", "off")
_IDENTITY_SENSITIVE_ENABLE = os.environ.get("TORMENT_IDENTITY_SENSITIVE", "1").strip() not in ("0", "false", "no", "off")
_SRG_COGNITION_ENABLE = os.environ.get("TORMENT_SRG_COGNITION", "1").strip() not in ("0", "false", "no", "off")
_ARCHIVE_RECALL_ENABLE = os.environ.get("TORMENT_ARCHIVE_RECALL", "1").strip() not in ("0", "false", "no", "off")
_LIVE_SOCIAL_ENABLE = os.environ.get("TORMENT_LIVE_SOCIAL", "1").strip() not in ("0", "false", "no", "off")


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
        # v0.1.0d: tool_need fires when either a word-level trigger
        # (TOOL_HINT_WORDS — execution verbs) OR a phrase-level trigger
        # (TOOL_HINT_PHRASES — explicit execution phrases like
        # "run code", "using python") is present. Phrase matches
        # deliberately override ambiguous single-word context.
        tool_need = (
            self._has_any(lower, TOOL_HINT_WORDS)
            or any(phrase in lower for phrase in TOOL_HINT_PHRASES)
        )
        governance_sensitive = self._has_any(lower, GOVERNANCE_HINT_WORDS)
        identity_sensitive = self._has_any(lower, IDENTITY_HINT_WORDS)
        live_social = self._has_any(lower, LIVE_SOCIAL_HINT_WORDS)
        archive_relevant = self._has_any(lower, ARCHIVE_HINT_WORDS)

        # S5: reflex observations are identity-sensitive by definition.
        # A reflex turn is fired because a kernel-state signal crossed
        # a threshold that warrants stabilization — that IS identity
        # preservation. Force identity_sensitive=True so the existing
        # choose_mode branch routes to IDENTITY_SENSITIVE. Slice plan
        # S5 / doctrine Part 4 high regime.
        if source_type == "reflex":
            identity_sensitive = True
        # §2A D1: pad with spaces so " we " matches at string boundaries
        _padded = " " + lower + " "
        relational_cue = self._has_any(_padded, RELATIONAL_HINT_WORDS)
        # §2A D2: analytical depth detection
        analytical_depth = self._has_any(lower, ANALYTICAL_DEPTH_HINT_WORDS)

        memory_need = bool(
            archive_relevant
            or identity_sensitive
            or relational_cue
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
        if analytical_depth:
            confidence_need += 0.2   # §2A D2: crosses 0.60 REFLECTIVE threshold
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
        if frame.governance_sensitive and _SPINE_ENABLE:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.GOVERNED,
                reason="Governance-sensitive input requires stricter control.",
                allowed_depth=2,
                requires_self_review=True,
                may_escalate=True,
                confidence_floor=0.75,
            )

        if frame.live_social and _LIVE_SOCIAL_ENABLE:
            return CognitiveModeDecision(
                chosen_mode=CognitiveMode.LIVE_SOCIAL,
                reason="Live-social context requires compact and responsive cognition.",
                allowed_depth=1,
                requires_self_review=True,
                may_escalate=False,
                confidence_floor=0.55,
            )

        if frame.identity_sensitive and _IDENTITY_SENSITIVE_ENABLE:
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
        plan.retrieve_srg_state = _SRG_COGNITION_ENABLE and plan.retrieve_character_state
        plan.retrieve_relational = frame.memory_need or frame.live_social
        plan.retrieve_archive = _ARCHIVE_RECALL_ENABLE and (
            "archive" in frame.context_tags
            or "document" in frame.normalized_input.lower()
        )
        plan.retrieve_deep = _ARCHIVE_RECALL_ENABLE and mode.chosen_mode in {
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

        # M1 (doctrine v0.1): PROPOSE_SHARE and CREATE_ARCHIVE_NOTE are
        # assimilation outcomes, not primary runtime intents. Their
        # emission has been moved to the Phase 7 dispatcher in
        # agent_loop.assimilation_outcomes. The text-hint branches that
        # previously emitted them from Phase 4 have been removed per
        # docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 3 and the M1
        # migration in docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md.

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

    def deliberate_only(
        self,
        workspace_id: str,
        agent_id: str,
        raw_input: str,
        *,
        source_type: str = "user_text",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DeliberationBundle:
        """Run the inner deliberation loop (Phases 2-4) and return the bundle.

        Does NOT run review (Phase 6 sub-gate, owned by the outer-loop
        runner), draft (Phase 6 execute, owned by the runner), or stance.
        This is the clean seam between the inner cognition scaffold and
        the outer agent turn, per doctrine Part 2 R6 and R6.a.

        Consumed by `torment_service.agent_loop.AgentRunner.run_turn`.
        Also callable directly by any component that needs the pre-
        policy/pre-execution deliberation bundle without the
        backward-compat `think()` pipeline.
        """
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
        return DeliberationBundle(
            task_frame=frame,
            mode_decision=mode,
            memory_plan=memory_plan,
            action_decision=action,
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
        """Backward-compat single-shot deliberation pipeline.

        Runs `deliberate_only()` followed by the Phase 6 sub-components
        (draft + review + stance) in one call. New code should prefer
        `deliberate_only()` + the outer-loop runner
        (`agent_loop.AgentRunner.run_turn`) so that Phase 5 (action
        policy), Phase 6 execution, Phase 7 assimilation, and Phase 8
        stabilization are visibly runner-owned.
        """
        bundle = self.deliberate_only(
            workspace_id=workspace_id,
            agent_id=agent_id,
            raw_input=raw_input,
            source_type=source_type,
            metadata=metadata,
        )
        frame = bundle.task_frame
        mode = bundle.mode_decision
        memory_plan = bundle.memory_plan
        action = bundle.action_decision

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

        # ReflectionTrace v0.1 (observation only): coarse decision-shape labels
        # built from the values already computed above. It is NOT branched on,
        # NOT consumed by any decision/retrieval/write path, and NOT fed back
        # anywhere. Attached to the per-call ThinkingResult for inspection
        # surfaces (e.g. /thinking/debug) only.
        _reflection_trace = build_reflection_trace(
            chosen_mode=mode.chosen_mode.value,
            action=action.action.value,
            stance=(stance.stance.value if stance is not None else None),
            review_status_flags={
                "approved": bool(review.approved),
                "revised": bool(review.revised),
                "escalate": bool(review.escalate),
                "ask_user": bool(review.ask_user),
                "blocked": bool(review.blocked),
            },
            top_k_by_lane=memory_plan.top_k_by_lane,
            geometric_context_present=(geometric_context is not None),
            # v0.2 coarse mode/action/frame shape (already-computed scalars only)
            allowed_depth=mode.allowed_depth,
            requires_self_review=mode.requires_self_review,
            may_escalate=mode.may_escalate,
            confidence_floor=mode.confidence_floor,
            requires_execution=action.requires_execution,
            source_type=frame.source_type,
            action_need=frame.action_need,
            memory_need=frame.memory_need,
            tool_need=frame.tool_need,
            governance_sensitive=frame.governance_sensitive,
            identity_sensitive=frame.identity_sensitive,
            live_social=frame.live_social,
            urgency=frame.urgency,
            ambiguity_score=frame.ambiguity_score,
            confidence_need=frame.confidence_need,
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
            reflection_trace=_reflection_trace,
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