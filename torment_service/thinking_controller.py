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
    EphemeralCognitionState,
    GeometricStanceContext,
    MemoryPlan,
    ReviewResult,
    TaskFrame,
    ThinkingResult,
    map_participation_guidance,
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

# Slice 2 (ephemeral cognition state) — numeric retrieval shaping. DEFAULT OFF.
# Opt-in, plan-boundary-only shaping of `top_k_by_lane["deep"]`. The empty
# string is treated as OFF (stricter than the always-on flags above) because
# this flag defaults off and must not silently enable on a blank value.
# Envelope: docs/TORMENT_EPHEMERAL_COGNITION_STATE_SLICE_2_DEFINITION_v0.1.md
_COGNITION_SHAPING_V2_ENABLE = os.environ.get("TORMENT_COGNITION_SHAPING_V2", "0").strip() not in (
    "", "0", "false", "no", "off",
)

# Slice 3 (ephemeral cognition state) — core-lane numeric shaping. DEFAULT OFF.
# Separate flag from Slice 2 (deliberately NOT folded in), so each rule toggles
# independently. Opt-in, plan-boundary-only shaping of `top_k_by_lane["core"]`.
# Empty string is treated as OFF (same stricter default-off posture as Slice 2).
_COGNITION_CORE_SHAPING_V1_ENABLE = os.environ.get("TORMENT_COGNITION_CORE_SHAPING_V1", "0").strip() not in (
    "", "0", "false", "no", "off",
)

# Geometric MemoryPlan shaping v1 — the first retrieval-plan (MemoryPlan)
# consumer of the live kernel ``geometric_context`` (``stance_policy`` already
# consumes it for contextual abstention). DEFAULT OFF. Opt-in, plan-boundary-only shaping
# of ``weight_by_lane`` for already-enabled core/deep lanes, driven by
# coherence + stability. No-op when the flag is off OR when
# ``geometric_context is None`` (every non-advisory path). Empty string is
# treated as OFF (same stricter default-off posture as Slices 2/3).
_GEOMETRIC_MEMORY_SHAPING_V1_ENABLE = os.environ.get("TORMENT_GEOMETRIC_MEMORY_SHAPING_V1", "0").strip() not in (
    "", "0", "false", "no", "off",
)

# Geometric relational-prominence shaping v1 — sibling of the geometric shaping
# above, on its OWN DEFAULT-OFF flag. Opt-in, plan-boundary-only shaping of the
# already-enabled ``relational`` lane weight only, driven by ``ambiguity_tolerance``
# (seed-basin health). This changes relational *prominence among already-retrieved
# candidates* — it does NOT widen recall (``top_k`` is untouched), and does not
# touch core/deep/archive/identity lanes, stance, or output. No-op when the flag
# is off OR ``geometric_context is None``. Empty string is treated as OFF.
_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE = os.environ.get(
    "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1", "0"
).strip() not in ("", "0", "false", "no", "off")

# Relational ambiguity-prominence shaping v1 — a Layer-1 / MemoryPlan-shaping rule
# that translates "high ambiguity / instability increases the usefulness of
# relational context" into a small, bounded advisory LIFT on the already-enabled
# ``relational`` lane WEIGHT (prominence). DEFAULT OFF. Opt-in, plan-boundary-only;
# driven purely by the content-free ambiguity signal (``state.ambiguity_score``)
# with NO dynamic-kernel / geometric-context coupling. No-op when the flag is off,
# when ambiguity is not high, or when the relational lane is not already enabled.
# Empty string is treated as OFF (same stricter default-off posture as the siblings).
_RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE = os.environ.get(
    "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1", "0"
).strip() not in ("", "0", "false", "no", "off")

# Ambiguity context-diversity shaping v1 — a Layer-1 / MemoryPlan-shaping rule that
# translates "high ambiguity should not over-collapse context into a single lane"
# into a small, bounded advisory LIFT on the already-enabled non-core lane BUDGETS
# (``top_k_by_lane``), NOT weights. DEFAULT OFF. Opt-in, plan-boundary-only; driven
# purely by the content-free ambiguity signal (``state.ambiguity_score``) with NO
# dynamic-kernel / geometric-context coupling. It never enables a disabled lane,
# never touches ``core``, and never touches ``weight_by_lane`` / retrieval booleans /
# ``safety_constraints`` / ``max_token_budget``. No-op when the flag is off, when
# ambiguity is not high, or on identity-/governance-sensitive turns.
# Empty string is treated as OFF (same stricter default-off posture as the siblings).
_AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE = os.environ.get(
    "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1", "0"
).strip() not in ("", "0", "false", "no", "off")

# Participation guidance v1 — surfaces a single visible advisory
# ``participation_guidance`` candidate on the thinking/advisory audit surface
# (``ThinkingResult.to_dict()`` / Spine ``audit["advisory_thinking"]``) ONLY. NOT
# on ``/agent/query``, NOT a response-control field; it never suppresses, vetoes,
# blocks, or empties a response and never touches dispatch / ``review.blocked`` /
# authority / memory. DEFAULT OFF — when off the field is omitted entirely (exact
# parity). Empty string treated as OFF. See
# docs/TORMENT_PARTICIPATION_GUIDANCE_FRAME_v0.1.md.
_PARTICIPATION_GUIDANCE_V1_ENABLE = os.environ.get(
    "TORMENT_PARTICIPATION_GUIDANCE_V1", "0"
).strip() not in ("", "0", "false", "no", "off")


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

    def _build_ephemeral_cognition_state(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
    ) -> EphemeralCognitionState:
        """Build the per-turn, content-free, deterministic cognition state.

        Pure function of ``(frame, mode)``. Collects only already-computed
        primitive scalars plus the derived retrieval-shaping predicates that
        ``build_memory_plan`` consumes. Holds NO raw/normalized text, no
        reasons, no payloads, no collections. The struct is advisory /
        observation-shape only — it is built here, consumed by
        ``build_memory_plan`` to shape the (identical) ``MemoryPlan``, and
        then discarded. It is never serialized, persisted, attached to
        ``ThinkingResult``, or exposed by any endpoint in Slice 1.

        Environment gates (``_SRG_COGNITION_ENABLE`` /
        ``_ARCHIVE_RECALL_ENABLE``) are deliberately NOT folded in here; the
        ``*_signal`` / ``*_eligible`` fields are the pre-flag predicates and
        the flags are applied downstream, so this state stays a pure
        function of its two inputs.
        """
        character_state_context_eligible = frame.identity_sensitive or mode.chosen_mode in {
            CognitiveMode.IDENTITY_SENSITIVE,
            CognitiveMode.LIVE_SOCIAL,
        }
        deep_context_eligible = mode.chosen_mode in {
            CognitiveMode.REFLECTIVE,
            CognitiveMode.IDENTITY_SENSITIVE,
        }
        archive_context_signal = (
            "archive" in frame.context_tags
            or "document" in frame.normalized_input.lower()
        )
        collective_context_signal = "collective" in frame.normalized_input.lower()

        return EphemeralCognitionState(
            chosen_mode=mode.chosen_mode.value,
            allowed_depth=mode.allowed_depth,
            requires_self_review=mode.requires_self_review,
            may_escalate=mode.may_escalate,
            confidence_floor=mode.confidence_floor,
            urgency=frame.urgency,
            ambiguity_score=frame.ambiguity_score,
            confidence_need=frame.confidence_need,
            action_need=frame.action_need,
            memory_need=frame.memory_need,
            tool_need=frame.tool_need,
            governance_sensitive=frame.governance_sensitive,
            identity_sensitive=frame.identity_sensitive,
            live_social=frame.live_social,
            archive_context_signal=archive_context_signal,
            collective_context_signal=collective_context_signal,
            character_state_context_eligible=character_state_context_eligible,
            deep_context_eligible=deep_context_eligible,
        )

    def build_memory_plan(
        self,
        frame: TaskFrame,
        mode: CognitiveModeDecision,
        geometric_context: Optional[GeometricStanceContext] = None,
    ) -> MemoryPlan:
        # Slice 1: route retrieval shaping through the ephemeral, content-free
        # cognition state. This is a behavior-preserving refactor — the
        # MemoryPlan produced below is byte-for-byte identical to the previous
        # direct-from-(frame, mode) computation. Environment gates are applied
        # here (not inside the state) exactly as before.
        state = self._build_ephemeral_cognition_state(frame, mode)

        plan = MemoryPlan()

        plan.retrieve_core = True
        plan.retrieve_character_state = state.character_state_context_eligible
        plan.retrieve_srg_state = _SRG_COGNITION_ENABLE and state.character_state_context_eligible
        plan.retrieve_relational = state.memory_need or state.live_social
        plan.retrieve_archive = _ARCHIVE_RECALL_ENABLE and state.archive_context_signal
        plan.retrieve_deep = _ARCHIVE_RECALL_ENABLE and state.deep_context_eligible
        plan.retrieve_collective = state.governance_sensitive and state.collective_context_signal

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

        if state.identity_sensitive:
            plan.safety_constraints.append("identity_must_outrank_archive")
        if state.governance_sensitive:
            plan.safety_constraints.append("governance_review_before_execution")
        if plan.retrieve_collective:
            plan.safety_constraints.append("collective_context_non_dominant")

        if state.chosen_mode == CognitiveMode.FAST.value:
            plan.max_token_budget = 1200
        elif state.chosen_mode == CognitiveMode.LIVE_SOCIAL.value:
            plan.max_token_budget = 900
        else:
            plan.max_token_budget = 2400

        # Slice 2 (default-off): optional numeric retrieval shaping at the plan
        # boundary. No-op unless TORMENT_COGNITION_SHAPING_V2 is enabled, so the
        # default-flag plan stays byte-identical to Slice 1.
        self._apply_cognition_shaping_v2(plan, state)

        # Slice 3 (default-off): optional core-lane shaping behind its own flag.
        # No-op unless TORMENT_COGNITION_CORE_SHAPING_V1 is enabled.
        self._apply_cognition_core_shaping_v1(plan, state)

        # Geometric shaping v1 (default-off): first retrieval-plan consumer of
        # the live kernel geometric_context. No-op unless the flag is on AND a
        # geometric_context is supplied (advisory path only), so the
        # default-flag / geo-None plan stays byte-identical to Slices 1-3.
        self._apply_geometric_memory_shaping_v1(plan, state, geometric_context)

        # Geometric relational-prominence shaping v1 (default-off, separate flag):
        # nudges ONLY the already-enabled relational lane weight from
        # ambiguity_tolerance. No-op unless its own flag is on AND geometric_context
        # is supplied. Disjoint from the core/deep shaping above — relational only.
        self._apply_geometric_relational_prominence_shaping_v1(plan, state, geometric_context)

        # Relational ambiguity-prominence shaping v1 (default-off, separate flag):
        # a small bounded advisory LIFT on the already-enabled relational lane weight
        # when ambiguity is high. Content-free (``state.ambiguity_score`` only); NO
        # dynamic-kernel coupling. Relational-only; never touches ``top_k_by_lane`` /
        # retrieval booleans / other lanes / ``safety_constraints``. No-op unless its
        # own flag is on, so the default-flag plan stays byte-identical to the above.
        # (observation) record whether THIS reflex actually changes the effective
        # relational lane weight, for the content-free ReflectionTrace posture below.
        _relational_weight_before = plan.weight_by_lane.get("relational")
        self._apply_relational_ambiguity_prominence_v1(plan, state)
        _relational_ambiguity_changed = (
            plan.weight_by_lane.get("relational") != _relational_weight_before
        )

        # Ambiguity context-diversity shaping v1 (default-off, separate flag): under
        # HIGH ambiguity, give the already-enabled non-core lanes a tiny bounded +1
        # budget lift so context is not over-collapsed into a single lane. Content-free
        # (``state.ambiguity_score`` only); NO dynamic-kernel coupling. Budget-only:
        # touches ONLY ``top_k_by_lane`` for already-enabled non-core lanes, never
        # ``core`` / ``weight_by_lane`` / retrieval booleans / ``safety_constraints`` /
        # ``max_token_budget``, and never enables a disabled lane. No-op unless its own
        # flag is on, so the default-flag plan stays byte-identical to the above.
        # (observation) record whether THIS reflex actually changes the effective
        # lane budgets, for the content-free ReflectionTrace posture below.
        _top_k_before = dict(plan.top_k_by_lane)
        self._apply_ambiguity_context_diversity_v1(plan, state)
        _ambiguity_context_diversity_changed = plan.top_k_by_lane != _top_k_before

        # Content-free, fixed-key boolean OBSERVATION surface: which default-off
        # MemoryPlan shaping reflex actually moved the effective plan this turn. It is
        # attached to the plan for the ReflectionTrace builder only; NOTHING in the
        # runtime branches on it, it carries no raw text / reasoning / content, and it
        # is NOT part of MemoryPlan's own serialization (asdict ignores it).
        plan._shaping_posture = {
            "relational_ambiguity_prominence": bool(_relational_ambiguity_changed),
            "ambiguity_context_diversity": bool(_ambiguity_context_diversity_changed),
        }

        return plan

    def _apply_cognition_shaping_v2(
        self,
        plan: MemoryPlan,
        state: EphemeralCognitionState,
    ) -> None:
        """Slice 2 (default-off) numeric retrieval shaping — first rule.

        Approved rule (env flag ``TORMENT_COGNITION_SHAPING_V2``):
          when ``state.ambiguity_score >= 0.50``, ``deep.top_k += 1``, clamped
          to ``<= 4``; otherwise unchanged.

        Scope (Slice 2 Definition v0.1): mutates ONLY ``top_k_by_lane["deep"]``.
        Weights, the other lanes (``core`` / ``relational`` / ``archive`` /
        ``collective``), retrieval booleans, ``safety_constraints`` and
        ``max_token_budget`` are left exactly as built.

        Guard — shape only an *already-enabled* deep lane (current
        ``deep`` top_k > 0). Definition §2 is explicit that Slice 2 shapes *how
        much* of an enabled lane, never *whether* a lane is enabled; bumping a
        disabled (``0``) deep budget to ``1`` would both create a never-before
        ``retrieve_deep=False / deep_top_k=1`` plan state and (downstream, in
        the untouched ``fabric.query`` gap-fill path) risk *reducing* deep
        retrieval. So a disabled deep lane is left at ``0``.

        Never reduces an existing value (the cap is an upper clamp only). A
        no-op when the flag is off — ``build_memory_plan`` then matches Slice 1
        byte-for-byte.
        """
        if not _COGNITION_SHAPING_V2_ENABLE:
            return
        if state.ambiguity_score < 0.50:
            return
        current_deep = plan.top_k_by_lane.get("deep", 0)
        if current_deep <= 0:
            # Deep lane not enabled this turn — shape already-enabled lanes only.
            return
        shaped = min(current_deep + 1, 4)
        # max(...) guarantees we never reduce an already-larger budget.
        plan.top_k_by_lane["deep"] = max(shaped, current_deep)

    def _apply_cognition_core_shaping_v1(
        self,
        plan: MemoryPlan,
        state: EphemeralCognitionState,
    ) -> None:
        """Slice 3 (default-off) numeric retrieval shaping — core lane.

        Approved rule (env flag ``TORMENT_COGNITION_CORE_SHAPING_V1``):
          when ``state.confidence_need >= 0.60`` AND the turn is neither
          governance- nor identity-sensitive AND the core lane is already
          enabled (``core`` top_k > 0), nudge ``core.top_k`` to
          ``min(current + 1, 7)``; otherwise unchanged.

        Scope: mutates ONLY ``top_k_by_lane["core"]``. Weights, the other lanes
        (``relational`` / ``archive`` / ``deep`` / ``collective``), retrieval
        booleans, ``safety_constraints`` and ``max_token_budget`` are left
        exactly as built. Independent of Slice 2 — its own flag, its own driver.

        Guards: governance- and identity-sensitive turns are explicitly excluded
        (no retrieval reshaping on those classes). Core is always enabled in the
        current builder, but the ``> 0`` check keeps the rule self-consistent and
        leaves a ``0`` budget untouched. Never reduces an existing value (the cap
        is an upper clamp only). A no-op when the flag is off — ``build_memory_plan``
        then matches the pre-Slice-3 plan byte-for-byte.
        """
        if not _COGNITION_CORE_SHAPING_V1_ENABLE:
            return
        if state.confidence_need < 0.60:
            return
        if state.governance_sensitive or state.identity_sensitive:
            return
        current_core = plan.top_k_by_lane.get("core", 0)
        if current_core <= 0:
            return
        shaped = min(current_core + 1, 7)
        # max(...) guarantees we never reduce an already-larger budget (7->7, 8->8).
        plan.top_k_by_lane["core"] = max(shaped, current_core)

    def _apply_geometric_memory_shaping_v1(
        self,
        plan: MemoryPlan,
        state: EphemeralCognitionState,
        geometric_context: Optional[GeometricStanceContext] = None,
    ) -> None:
        """Geometric shaping v1 — first retrieval-plan (MemoryPlan) consumer of
        geometric_context (``stance_policy.determine_stance`` already consumes it
        for contextual abstention; this is the first *retrieval-facing* one).

        When the live kernel's ``geometric_context`` is present, lightly shape
        the already-built MemoryPlan lane *weights* from ``coherence`` and
        ``stability`` — the two dimensions that semantically map to retrieval
        confidence/depth. This is guidance, not control:

          * No-op unless ``TORMENT_GEOMETRIC_MEMORY_SHAPING_V1`` is enabled, so
            the default-flag plan stays byte-identical to Slices 1-3.
          * No-op when ``geometric_context is None`` — every non-advisory caller
            (``agent_loop``, direct/test callers) passes ``None`` and is
            therefore unchanged regardless of the flag.
          * Shapes ONLY ``weight_by_lane`` for ALREADY-ENABLED ``core`` / ``deep``
            lanes (current weight > 0). Never enables a disabled lane, never
            touches ``top_k_by_lane``, retrieval booleans, ``safety_constraints``,
            ``max_token_budget``, or any other lane.
          * ``social_resonance`` is intentionally NOT used for retrieval shaping
            (that dimension belongs to stance, not retrieval depth).
          * Governance- / identity-sensitive turns are skipped entirely (safety
            parity with Slice 3) — the living kernel does not reshape retrieval
            on those classes.
          * Bounded: settledness ``s = (coherence + stability) / 2`` in [0, 1]
            maps to a multiplier ``m = clamp(0.85 + 0.30*s, 0.85, 1.15)``
            (neutral at ``s == 0.5``); each shaped weight is then re-clamped to
            the downstream ``[0.1, 2.0]`` lane-weight band. So the kernel can
            nudge a lane weight by at most +/-15% and can never invert lane
            ordering or zero a lane.
        """
        if not _GEOMETRIC_MEMORY_SHAPING_V1_ENABLE:
            return
        if geometric_context is None:
            return
        # Safety parity with Slice 3: no retrieval reshaping on governed/identity.
        if state.governance_sensitive or state.identity_sensitive:
            return

        def _clamp(v: float, lo: float, hi: float) -> float:
            return lo if v < lo else (hi if v > hi else v)

        settled = _clamp(
            0.5 * (float(geometric_context.coherence) + float(geometric_context.stability)),
            0.0, 1.0,
        )
        mult = _clamp(0.85 + 0.30 * settled, 0.85, 1.15)

        # core lane — always enabled in the current builder, so reliably
        # observable; shape only when actually enabled this turn (weight > 0).
        current_core_w = plan.weight_by_lane.get("core", 0.0)
        if plan.retrieve_core and current_core_w > 0.0:
            plan.weight_by_lane["core"] = _clamp(current_core_w * mult, 0.1, 2.0)

        # deep lane — shape only when already enabled this turn (weight > 0).
        current_deep_w = plan.weight_by_lane.get("deep", 0.0)
        if plan.retrieve_deep and current_deep_w > 0.0:
            plan.weight_by_lane["deep"] = _clamp(current_deep_w * mult, 0.1, 2.0)

    def _apply_geometric_relational_prominence_shaping_v1(
        self,
        plan: MemoryPlan,
        state: EphemeralCognitionState,
        geometric_context: Optional[GeometricStanceContext] = None,
    ) -> None:
        """Geometric relational-prominence shaping v1 — sibling of
        ``_apply_geometric_memory_shaping_v1``, on its own default-off flag.

        When the live kernel ``geometric_context`` is present, lightly shape the
        already-enabled ``relational`` lane *weight* from ``ambiguity_tolerance``
        (seed-basin health). This changes how strongly already-retrieved
        relational memory RANKS — relational *prominence* — it does NOT widen
        recall: ``top_k`` is never touched, so no new memory is pulled in. This
        is guidance, not control:

          * No-op unless ``TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1``
            is enabled (separate flag from the core/deep geometric shaping).
          * No-op when ``geometric_context is None``.
          * Shapes ONLY ``weight_by_lane["relational"]`` and ONLY when that lane
            is already enabled this turn (``retrieve_relational`` and weight > 0).
            Never creates/enables the lane; never touches core / deep / archive /
            collective, ``top_k_by_lane``, retrieval booleans, ``safety_constraints``
            or ``max_token_budget``.
          * Governance-/identity-sensitive turns are skipped entirely (parity with
            the core/deep helper).
          * Bounded: ``t = ambiguity_tolerance`` in [0, 1] maps to a multiplier
            ``clamp(0.85 + 0.30*t, 0.85, 1.15)`` (neutral at t=0.5); the shaped
            weight is re-clamped to ``[0.1, 2.0]`` and then held under a fixed
            peripheral ceiling (<= 0.99) so a peripheral lane never reaches core's
            base prominence (1.0) — peripheral stays peripheral, without coupling
            dynamically to the core helper.
        """
        if not _GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1_ENABLE:
            return
        if geometric_context is None:
            return
        # Safety parity with the core/deep helper: skip governed/identity turns.
        if state.governance_sensitive or state.identity_sensitive:
            return

        def _clamp(v: float, lo: float, hi: float) -> float:
            return lo if v < lo else (hi if v > hi else v)

        # relational lane only; shape only when already enabled this turn.
        current_relational_w = plan.weight_by_lane.get("relational", 0.0)
        if not (plan.retrieve_relational and current_relational_w > 0.0):
            return

        tol = _clamp(float(geometric_context.ambiguity_tolerance), 0.0, 1.0)
        mult = _clamp(0.85 + 0.30 * tol, 0.85, 1.15)
        shaped = _clamp(current_relational_w * mult, 0.1, 2.0)
        # Peripheral ceiling: relational never reaches core's base prominence (1.0).
        _PERIPHERAL_CEILING = 0.99
        plan.weight_by_lane["relational"] = min(shaped, _PERIPHERAL_CEILING)

    def _apply_relational_ambiguity_prominence_v1(
        self,
        plan: MemoryPlan,
        state: EphemeralCognitionState,
    ) -> None:
        """Relational ambiguity-prominence shaping v1 (default-off flag).

        Translates the research principle "ambiguity / instability increases the
        usefulness of relational context" into a small, bounded advisory LIFT on
        the already-enabled ``relational`` lane WEIGHT (prominence), driven purely
        by the content-free ``state.ambiguity_score``. Guidance, not control, and
        it references NO dynamic-kernel machinery:

          * No-op unless ``TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1`` is enabled.
          * No-op unless ambiguity is HIGH (``ambiguity_score > 0.5``); the lift is a
            monotone, bounded function of ambiguity above that threshold.
          * Shapes ONLY ``weight_by_lane["relational"]`` and ONLY when that lane is
            already enabled this turn (``retrieve_relational`` and weight > 0). Never
            creates/enables the lane; never touches ``top_k_by_lane``, retrieval
            booleans, ``core`` / ``deep`` / ``archive`` / ``collective`` weights,
            ``safety_constraints`` or ``max_token_budget``.
          * Governance-/identity-sensitive turns are skipped entirely (parity with
            the geometric shaping siblings).
          * LIFT-only + bounded: ``mult = 1.0 + 0.30 * clamp(ambiguity - 0.5, 0, 0.5)``
            (in ``[1.0, 1.15]``); the shaped weight is re-clamped to ``[0.1, 2.0]`` and
            held under a fixed peripheral ceiling (<= 0.99) so relational never reaches
            core's base prominence (1.0) -- peripheral stays peripheral.
        """
        if not _RELATIONAL_AMBIGUITY_PROMINENCE_V1_ENABLE:
            return
        # Safety parity with the geometric helpers: skip governed / identity turns.
        if state.governance_sensitive or state.identity_sensitive:
            return

        def _clamp(v: float, lo: float, hi: float) -> float:
            return lo if v < lo else (hi if v > hi else v)

        ambiguity = float(state.ambiguity_score)
        if ambiguity <= 0.5:  # only HIGH ambiguity lifts relational prominence
            return

        # relational lane only; shape only when it is already enabled this turn.
        current_relational_w = plan.weight_by_lane.get("relational", 0.0)
        if not (plan.retrieve_relational and current_relational_w > 0.0):
            return

        mult = 1.0 + 0.30 * _clamp(ambiguity - 0.5, 0.0, 0.5)  # in [1.0, 1.15]
        shaped = _clamp(current_relational_w * mult, 0.1, 2.0)
        _PERIPHERAL_CEILING = 0.99  # relational never reaches core's base prominence (1.0)
        plan.weight_by_lane["relational"] = min(shaped, _PERIPHERAL_CEILING)

    def _apply_ambiguity_context_diversity_v1(
        self, plan: MemoryPlan, state: EphemeralCognitionState
    ) -> None:
        """Bounded non-core BUDGET diversity under high ambiguity (default OFF).

        Rule (env flag ``TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1``): when ambiguity is
        HIGH, avoid over-collapsing retrieval into a single lane by giving each
        already-enabled NON-CORE lane a tiny, bounded ``+1`` budget lift on
        ``top_k_by_lane`` (capped per lane). It is:

          * BUDGET-ONLY: mutates ONLY ``top_k_by_lane``; never ``weight_by_lane``,
            retrieval booleans, ``safety_constraints``, or ``max_token_budget``.
          * NON-CORE-ONLY: ``core`` is never touched.
          * NON-ENABLING: a lane that is disabled (retrieval flag off or budget 0)
            stays at 0 — this never turns a lane on.
          * CONTENT-FREE: driven purely by ``state.ambiguity_score``; NO
            dynamic-kernel / geometric-context coupling.
          * PER-LANE CAPPED: each lift is ``min(current + 1, cap)`` so budgets stay
            small (deep<=4, relational<=5, archive<=5, collective<=3).

        No-op when the flag is off, when ambiguity is not high (``<= 0.5``), or on
        identity-/governance-sensitive turns (safety parity with the siblings).
        """
        if not _AMBIGUITY_CONTEXT_DIVERSITY_V1_ENABLE:
            return
        # Safety parity with the ambiguity/geometric helpers: skip governed / identity.
        if state.governance_sensitive or state.identity_sensitive:
            return
        if float(state.ambiguity_score) <= 0.5:  # only HIGH ambiguity broadens budgets
            return

        # BUDGET-ONLY, NON-CORE, NON-ENABLING, PER-LANE CAPPED. ``core`` is never a
        # target below (it is never broadened). Each non-core lane is broadened by +1
        # ONLY when it is already enabled (retrieval flag on AND current budget > 0);
        # the per-lane cap keeps each budget small. Explicit constant-key assignments
        # (not a dynamic loop) so the lane ownership stays AST-lockable, matching the
        # sibling top_k helpers.
        if plan.retrieve_deep and plan.top_k_by_lane.get("deep", 0) > 0:
            plan.top_k_by_lane["deep"] = min(plan.top_k_by_lane["deep"] + 1, 4)
        if plan.retrieve_relational and plan.top_k_by_lane.get("relational", 0) > 0:
            plan.top_k_by_lane["relational"] = min(plan.top_k_by_lane["relational"] + 1, 5)
        if plan.retrieve_archive and plan.top_k_by_lane.get("archive", 0) > 0:
            plan.top_k_by_lane["archive"] = min(plan.top_k_by_lane["archive"] + 1, 5)
        if plan.retrieve_collective and plan.top_k_by_lane.get("collective", 0) > 0:
            plan.top_k_by_lane["collective"] = min(plan.top_k_by_lane["collective"] + 1, 3)

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
        geometric_context: Optional[GeometricStanceContext] = None,
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
        memory_plan = self.build_memory_plan(frame, mode, geometric_context=geometric_context)
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
            geometric_context=geometric_context,
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
            weight_by_lane=memory_plan.weight_by_lane,
            geometric_context_present=(geometric_context is not None),
            # content-free fixed-key boolean posture computed in build_memory_plan
            # (which shaping reflex actually moved the effective plan); observation only
            memory_plan_shaping_posture=getattr(memory_plan, "_shaping_posture", None),
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

        # Participation guidance v1 (default-off, visible advisory only): map the
        # (frame, stance) to a single advisory candidate for the thinking/advisory
        # audit surface. Omitted entirely when the flag is off. Never output
        # control — the final response path stays free to ignore/soften/express it.
        _participation_guidance = (
            map_participation_guidance(frame, stance)
            if _PARTICIPATION_GUIDANCE_V1_ENABLE else None
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
            participation_guidance=_participation_guidance,
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