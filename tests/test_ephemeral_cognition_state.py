"""tests/test_ephemeral_cognition_state.py — Slice 1 locks for the
ephemeral structured cognition state.

Covers the Slice-1 contract for ``EphemeralCognitionState`` and its builder
``ThinkingController._build_ephemeral_cognition_state``:

  * the dataclass is frozen and primitive-only (content-free);
  * its field names exclude every content-bearing concept on the denylist
    (raw/normalized text, reasons, payloads, metadata, tone hints, drafts,
    notes, memory/seed text, vectors/embeddings, arbitrary collections);
  * the builder is deterministic and returns a primitive-only state;
  * the state is NOT serialized and NOT exposed on ``ThinkingResult`` /
    ``think().to_dict()``;
  * ``build_memory_plan`` now routes *through* the state while preserving
    EXACT ``MemoryPlan`` parity (retrieval booleans, ``top_k_by_lane``,
    ``weight_by_lane``, ``safety_constraints``, ``max_token_budget``) across
    a representative mode/lane matrix.

These are behavior-preserving characterization locks for a refactor, NOT a
claim that the routing struct does anything on its own in Slice 1.
"""
from __future__ import annotations

import dataclasses

import pytest

import torment_service.thinking_controller as tc
from torment_service.thinking_controller import (
    ThinkingController,
    _ARCHIVE_RECALL_ENABLE,
    _SRG_COGNITION_ENABLE,
)
from torment_service.thinking_models import (
    CognitiveMode,
    EphemeralCognitionState,
    MemoryPlan,
    ThinkingResult,
)


# ---------------------------------------------------------------------------
# Representative matrix: (raw_input, source_type).
#
# Chosen to exercise every cognitive mode (FAST, RETRIEVAL, REFLECTIVE, TOOL,
# GOVERNED, IDENTITY_SENSITIVE, LIVE_SOCIAL), both non-default token budgets
# (1200 FAST / 900 LIVE_SOCIAL / 2400 else), the collective branch on and off,
# archive on/off, deep on/off, character-state on/off, and the reflex
# source_type that forces identity_sensitive.
# ---------------------------------------------------------------------------
MATRIX = [
    ("Can you delete this protected identity memory and inspect governance state?", "user_text"),
    ("Should we approve collective reingest for this protected memory?", "user_text"),
    ("I want to understand my identity drift and character seed history.", "user_text"),
    ("live audio yo", "live_transcript"),
    ("Please calculate and compute the sum of the first 100 primes using code.", "user_text"),
    ("Can you look through the archive document notes and remember what was said before?", "user_text"),
    ("Look through the archive transcript for what was said before.", "user_text"),
    ("maybe something off", "user_text"),
    ("Hello there", "user_text"),
    ("thanks for the help", "user_text"),
    ("Tell me about the document archive collective governance policy we decided.", "user_text"),
    ("kernel coherence dipped below the basin floor", "reflex"),
]


def _frame_and_mode(ctl: ThinkingController, raw: str, source_type: str):
    frame = ctl.frame_task("ws", "ag", raw, source_type=source_type)
    mode = ctl.choose_mode(frame)
    return frame, mode


def _reference_memory_plan(frame, mode) -> MemoryPlan:
    """Parity oracle: a faithful transcription of the PRE-Slice-1
    ``build_memory_plan`` body, computed directly from ``(frame, mode)``
    without the ephemeral state. The env gates are imported from the
    controller module so the oracle tracks whatever environment the test
    runs under.
    """
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


# Field-name contract -------------------------------------------------------

_EXPECTED_FIELDS = (
    "chosen_mode",
    "allowed_depth",
    "requires_self_review",
    "may_escalate",
    "confidence_floor",
    "urgency",
    "ambiguity_score",
    "confidence_need",
    "action_need",
    "memory_need",
    "tool_need",
    "governance_sensitive",
    "identity_sensitive",
    "live_social",
    "archive_context_signal",
    "collective_context_signal",
    "character_state_context_eligible",
    "deep_context_eligible",
)

# Exact field names that must NEVER appear (content-bearing / output-control).
_NAME_DENYLIST = frozenset({
    "raw_input",
    "normalized_input",
    "reason",
    "reasons",
    "payload",
    "tone_hints",
    "metadata",
    "context_tags",
    "response_draft",
    "revised_text",
    "notes",
    "text",
    "rationale",
    "embeddings",
    "embedding",
    "vectors",
    "vector",
    "seed_text",
    "memory_text",
})

# Content-bearing *leaf tokens* that would betray stored content. Matched
# token-aware (field name split on "_") rather than by raw substring, because
# raw substring matching produces false positives inside approved compound
# names — e.g. "text_" / "_text" both occur inside "con-text-_-signal"
# ("archive_context_signal"). "context" is a benign token; "text" as a whole
# token (raw_text, memory_text, seed_text, ...) is not. Deliberately omits
# "memory" and "seed" as tokens so the legitimate boolean ``memory_need`` is
# not caught; the banned ``*_text`` names are caught by the "text" token, and
# the bare forbidden identifiers (reason/notes/payload/tone_hints/...) are
# caught by the exact-name denylist above.
_FORBIDDEN_NAME_TOKENS = frozenset({
    "raw",
    "normalized",
    "text",
    "rationale",
    "payload",
    "embedding",
    "embeddings",
    "vector",
    "vectors",
    "draft",
    "tone",
    "hint",
    "hints",
})


def _content_bearing_tokens(name: str) -> set:
    """Return the forbidden leaf tokens present in a field name (token-aware).

    Splits on "_" and intersects with ``_FORBIDDEN_NAME_TOKENS`` so that
    "context" / "signal" / "eligible" never trip the "text" check.
    """
    return set(name.split("_")) & _FORBIDDEN_NAME_TOKENS


# Matcher fixtures: names that MUST be flagged vs approved compound names that
# MUST NOT be flagged (the regression that caused the false positive).
_CONTENT_BEARING_EXAMPLES = (
    "raw_text",
    "normalized_text",
    "memory_text",
    "seed_text",
    "draft_text",
    "response_text",
    "reason_text",
    "notes_text",
)
_APPROVED_CONTEXT_NAMES = (
    "archive_context_signal",
    "collective_context_signal",
    "character_state_context_eligible",
    "deep_context_eligible",
)

_PRIMITIVE_TYPES = (bool, int, float, str)


def _built_state():
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "I want to understand my identity drift.", "user_text")
    return ctl._build_ephemeral_cognition_state(frame, mode)


# ===========================================================================
# Dataclass shape: frozen + exact fields
# ===========================================================================

def test_is_frozen_dataclass():
    assert dataclasses.is_dataclass(EphemeralCognitionState)
    assert EphemeralCognitionState.__dataclass_params__.frozen is True


def test_frozen_rejects_mutation():
    state = _built_state()
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.chosen_mode = "tampered"  # type: ignore[misc]


def test_field_set_is_exactly_the_spec():
    names = tuple(f.name for f in dataclasses.fields(EphemeralCognitionState))
    assert names == _EXPECTED_FIELDS


# ===========================================================================
# Primitive-only / content-free
# ===========================================================================

def test_all_fields_are_primitive_scalars():
    state = _built_state()
    for f in dataclasses.fields(EphemeralCognitionState):
        value = getattr(state, f.name)
        # Strict type check (not isinstance): a str-subclass Enum would FAIL,
        # proving chosen_mode is stored as a plain str, not CognitiveMode.
        assert type(value) in _PRIMITIVE_TYPES, (
            f"field {f.name!r} holds non-primitive {type(value)!r}"
        )


def test_only_str_field_is_chosen_mode_and_is_a_known_mode_value():
    state = _built_state()
    str_fields = {
        f.name for f in dataclasses.fields(EphemeralCognitionState)
        if isinstance(getattr(state, f.name), str)
    }
    assert str_fields == {"chosen_mode"}
    # The single str field carries a controlled enum *value*, never free text.
    assert type(state.chosen_mode) is str
    assert state.chosen_mode in {m.value for m in CognitiveMode}


# ===========================================================================
# Field-name denylist
# ===========================================================================

def test_field_names_excluded_from_denylist():
    names = {f.name for f in dataclasses.fields(EphemeralCognitionState)}
    leaked = names & _NAME_DENYLIST
    assert leaked == set(), f"field names hit content denylist: {sorted(leaked)!r}"


def test_content_token_matcher_has_teeth_and_no_context_false_positive():
    # Teeth: every content-bearing example name is flagged.
    for bad in _CONTENT_BEARING_EXAMPLES:
        assert _content_bearing_tokens(bad), f"matcher failed to flag {bad!r}"
    # No false positive: approved compound names containing "context" are clean.
    # (This is the exact regression: "text_"/"_text" substrings live inside
    # "context_signal" but "context" is a benign token.)
    for ok in _APPROVED_CONTEXT_NAMES:
        assert not _content_bearing_tokens(ok), f"matcher wrongly flagged {ok!r}"


def test_field_names_have_no_content_bearing_tokens():
    for name in (f.name for f in dataclasses.fields(EphemeralCognitionState)):
        hits = _content_bearing_tokens(name)
        assert not hits, (
            f"field {name!r} contains content-bearing token(s) {sorted(hits)!r}"
        )


# ===========================================================================
# Deterministic builder
# ===========================================================================

def test_builder_is_deterministic_same_objects():
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "Should we approve collective reingest?", "user_text")
    a = ctl._build_ephemeral_cognition_state(frame, mode)
    b = ctl._build_ephemeral_cognition_state(frame, mode)
    assert a == b


def test_builder_is_deterministic_same_input():
    ctl = ThinkingController()
    f1, m1 = _frame_and_mode(ctl, "Look through the archive document notes.", "user_text")
    f2, m2 = _frame_and_mode(ctl, "Look through the archive document notes.", "user_text")
    assert ctl._build_ephemeral_cognition_state(f1, m1) == ctl._build_ephemeral_cognition_state(f2, m2)


@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_builder_returns_primitive_state_across_matrix(raw, source_type):
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    state = ctl._build_ephemeral_cognition_state(frame, mode)
    assert isinstance(state, EphemeralCognitionState)
    for f in dataclasses.fields(EphemeralCognitionState):
        assert type(getattr(state, f.name)) in _PRIMITIVE_TYPES


def test_builder_mirrors_frame_and_mode_scalars():
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "I want to understand my identity drift.", "user_text")
    state = ctl._build_ephemeral_cognition_state(frame, mode)
    assert state.chosen_mode == mode.chosen_mode.value
    assert state.allowed_depth == mode.allowed_depth
    assert state.requires_self_review == mode.requires_self_review
    assert state.may_escalate == mode.may_escalate
    assert state.confidence_floor == mode.confidence_floor
    assert state.urgency == frame.urgency
    assert state.ambiguity_score == frame.ambiguity_score
    assert state.confidence_need == frame.confidence_need
    assert state.action_need == frame.action_need
    assert state.memory_need == frame.memory_need
    assert state.tool_need == frame.tool_need
    assert state.governance_sensitive == frame.governance_sensitive
    assert state.identity_sensitive == frame.identity_sensitive
    assert state.live_social == frame.live_social


# ===========================================================================
# No serialization / no ThinkingResult exposure (Slice-1 hard lines)
# ===========================================================================

def test_state_has_no_serialization_method():
    state = _built_state()
    for attr in ("to_dict", "to_json", "json", "serialize", "asdict"):
        assert not hasattr(state, attr), f"state exposes serialization hook {attr!r}"


def test_thinking_result_does_not_carry_the_state():
    field_names = {f.name for f in dataclasses.fields(ThinkingResult)}
    for name in field_names:
        assert "ephemeral" not in name
        assert "cognition_state" not in name
    for f in dataclasses.fields(ThinkingResult):
        assert f.type is not EphemeralCognitionState
        # str-annotation form (from __future__ annotations) guard:
        assert "EphemeralCognitionState" not in str(f.type)


def test_think_to_dict_does_not_expose_the_state():
    ctl = ThinkingController()
    payload = ctl.think("ws", "ag", "Can you inspect the archive notes?").to_dict()
    for key in payload:
        assert "ephemeral" not in key
        assert "cognition_state" not in key


def test_build_memory_plan_returns_memory_plan_not_state():
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "Hello there", "user_text")
    plan = ctl.build_memory_plan(frame, mode)
    assert isinstance(plan, MemoryPlan)
    assert not isinstance(plan, EphemeralCognitionState)


# ===========================================================================
# Exact MemoryPlan parity across the representative matrix
# ===========================================================================

@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_memory_plan_parity_matches_reference(raw, source_type):
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    got = ctl.build_memory_plan(frame, mode)
    expected = _reference_memory_plan(frame, mode)
    # Full-shape equality covers every parity-relevant field at once:
    # retrieval booleans, top_k_by_lane, weight_by_lane, safety_constraints,
    # max_token_budget.
    assert got.to_dict() == expected.to_dict()


@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_plan_routes_through_state(raw, source_type):
    """The refactor genuinely derives the plan from the state: every
    parity-relevant retrieval boolean equals the state-derived expression
    (with env gates applied exactly where the production code applies them).
    """
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    state = ctl._build_ephemeral_cognition_state(frame, mode)
    plan = ctl.build_memory_plan(frame, mode)

    assert plan.retrieve_core is True
    assert plan.retrieve_character_state == state.character_state_context_eligible
    assert plan.retrieve_srg_state == (_SRG_COGNITION_ENABLE and state.character_state_context_eligible)
    assert plan.retrieve_relational == (state.memory_need or state.live_social)
    assert plan.retrieve_archive == (_ARCHIVE_RECALL_ENABLE and state.archive_context_signal)
    assert plan.retrieve_deep == (_ARCHIVE_RECALL_ENABLE and state.deep_context_eligible)
    assert plan.retrieve_collective == (state.governance_sensitive and state.collective_context_signal)


@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_token_budget_parity(raw, source_type):
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    plan = ctl.build_memory_plan(frame, mode)
    if mode.chosen_mode == CognitiveMode.FAST:
        assert plan.max_token_budget == 1200
    elif mode.chosen_mode == CognitiveMode.LIVE_SOCIAL:
        assert plan.max_token_budget == 900
    else:
        assert plan.max_token_budget == 2400


# ===========================================================================
# Slice 2 — default-off numeric retrieval shaping (deep top_k)
#
# Approved rule (env flag TORMENT_COGNITION_SHAPING_V2): when
# ambiguity_score >= 0.50, deep.top_k += 1 clamped to <= 4, shaping only an
# already-enabled deep lane and never reducing an existing value.
# ===========================================================================


@pytest.fixture(autouse=True)
def _shaping_v2_off_by_default(monkeypatch):
    # Pin BOTH cognition-shaping flags OFF for every test in this module unless a
    # test explicitly turns one on. Makes the suite (incl. the Slice-1 parity
    # tests above) robust to an ambient TORMENT_COGNITION_SHAPING_V2 /
    # TORMENT_COGNITION_CORE_SHAPING_V1 in the env.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", False)


def _state_with_ambiguity(amb: float):
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "maybe something off", "user_text")
    base = ctl._build_ephemeral_cognition_state(frame, mode)
    return dataclasses.replace(base, ambiguity_score=amb)


@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_flag_off_parity_matches_reference(raw, source_type, monkeypatch):
    # (1) Flag OFF: build_memory_plan is byte-identical to the pre-Slice-2
    # reference oracle across the full matrix.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    got = ctl.build_memory_plan(frame, mode)
    expected = _reference_memory_plan(frame, mode)
    assert got.to_dict() == expected.to_dict()


def test_flag_on_low_ambiguity_leaves_plan_unchanged(monkeypatch):
    # (2) Flag ON but ambiguity below threshold: plan identical to flag-off,
    # even though the deep lane is enabled (so the bump is purely
    # threshold-gated, not lane-availability-gated).
    monkeypatch.setattr(tc, "_ARCHIVE_RECALL_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(
        ctl, "I want to understand my identity drift and character seed history.", "user_text"
    )
    assert frame.ambiguity_score < 0.50

    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    on = ctl.build_memory_plan(frame, mode).to_dict()
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    off = ctl.build_memory_plan(frame, mode).to_dict()

    assert on["top_k_by_lane"]["deep"] == 3  # deep enabled
    assert on == off


def test_flag_on_high_ambiguity_changes_only_deep_topk(monkeypatch):
    # (3,5,6,7,8,9) Flag ON, ambiguity >= 0.50, deep enabled: ONLY
    # top_k_by_lane["deep"] moves, by exactly +1; every other field is
    # untouched (weights, other lanes, retrieval booleans, safety_constraints,
    # max_token_budget).
    monkeypatch.setattr(tc, "_ARCHIVE_RECALL_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "maybe something off", "user_text")
    assert frame.ambiguity_score >= 0.50

    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    off = ctl.build_memory_plan(frame, mode).to_dict()
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    on = ctl.build_memory_plan(frame, mode).to_dict()

    assert off["top_k_by_lane"]["deep"] == 3
    assert on["top_k_by_lane"]["deep"] == 4

    # Everything except the top_k_by_lane dict is identical.
    for key in off:
        if key == "top_k_by_lane":
            continue
        assert on[key] == off[key], f"field {key!r} changed under shaping"

    # Within top_k_by_lane, only "deep" differs, by exactly +1.
    off_topk, on_topk = off["top_k_by_lane"], on["top_k_by_lane"]
    for lane in ("core", "relational", "archive", "collective"):
        assert on_topk[lane] == off_topk[lane], f"lane {lane!r} top_k changed"
    assert on_topk["deep"] - off_topk["deep"] == 1


def test_flag_on_high_ambiguity_but_deep_disabled_no_bump(monkeypatch):
    # (9 / guard) Flag ON, ambiguity >= 0.50, but deep lane disabled: the bump
    # is NOT applied — Slice 2 shapes only already-enabled lanes (Definition
    # §2). Locks the interpretive choice that 0 -> 1 must not happen.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    # Pin spine on so "delete" routes to GOVERNED (deep disabled) deterministically,
    # rather than falling through to REFLECTIVE (deep enabled) if spine is off.
    monkeypatch.setattr(tc, "_SPINE_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "maybe delete something??", "user_text")
    assert frame.ambiguity_score >= 0.50

    plan = ctl.build_memory_plan(frame, mode)
    assert plan.retrieve_deep is False
    assert plan.top_k_by_lane["deep"] == 0


def test_shaping_caps_at_4_and_never_reduces(monkeypatch):
    # (4) Direct unit test of the shaping rule: +1, capped at 4, never reduces,
    # threshold-gated, lane-availability-gated, and flag-gated.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    ctl = ThinkingController()
    st_hi = _state_with_ambiguity(0.50)

    def _shaped(deep_val):
        plan = MemoryPlan()
        plan.top_k_by_lane = {"core": 6, "deep": deep_val}
        ctl._apply_cognition_shaping_v2(plan, st_hi)
        return plan.top_k_by_lane["deep"]

    assert _shaped(3) == 4   # +1
    assert _shaped(4) == 4   # already at cap -> unchanged
    assert _shaped(5) == 5   # above cap -> never reduced
    assert _shaped(0) == 0   # lane disabled -> untouched

    # Below threshold -> unchanged.
    st_lo = _state_with_ambiguity(0.49)
    plan = MemoryPlan()
    plan.top_k_by_lane = {"deep": 3}
    ctl._apply_cognition_shaping_v2(plan, st_lo)
    assert plan.top_k_by_lane["deep"] == 3

    # Flag off -> no-op even at high ambiguity.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    plan = MemoryPlan()
    plan.top_k_by_lane = {"deep": 3}
    ctl._apply_cognition_shaping_v2(plan, st_hi)
    assert plan.top_k_by_lane["deep"] == 3


def test_flag_on_does_not_change_result_shape_or_expose_state(monkeypatch):
    # (10) Flag ON must not change /think result shape and must not expose the
    # ephemeral state. Shaping touches only a MemoryPlan numeric field.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    ctl = ThinkingController()
    payload = ctl.think("ws", "ag", "maybe something off").to_dict()
    expected_keys = {
        "task_frame", "mode_decision", "memory_plan", "action_decision",
        "review_result", "response_draft", "stance", "geometric_context",
        "debug", "reflection_trace",
    }
    assert set(payload) == expected_keys
    for key in payload:
        assert "ephemeral" not in key
        assert "cognition_state" not in key


# ===========================================================================
# Slice 3 — default-off core-lane shaping (TORMENT_COGNITION_CORE_SHAPING_V1)
#
# Rule: when confidence_need >= 0.60 AND the turn is neither governance- nor
# identity-sensitive AND core top_k > 0, core.top_k -> min(current + 1, 7),
# never reducing. Separate flag from Slice 2; mutates only top_k_by_lane["core"].
# ===========================================================================


def _state_for_core(confidence_need, *, governance=False, identity=False):
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "why does this pattern tend to be fragile?", "user_text")
    base = ctl._build_ephemeral_cognition_state(frame, mode)
    return dataclasses.replace(
        base,
        confidence_need=confidence_need,
        governance_sensitive=governance,
        identity_sensitive=identity,
    )


@pytest.mark.parametrize("raw,source_type", MATRIX)
def test_core_flag_off_parity_matches_reference(raw, source_type, monkeypatch):
    # Flag OFF: build_memory_plan is byte-identical to the pre-shaping reference
    # across the full matrix (Slice 2 flag also off via autouse).
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", False)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, raw, source_type)
    assert ctl.build_memory_plan(frame, mode).to_dict() == _reference_memory_plan(frame, mode).to_dict()


def test_core_flag_on_bumps_core_only(monkeypatch):
    # Flag ON, confidence_need >= 0.60, non-governance, non-identity: ONLY
    # top_k_by_lane["core"] moves, 6 -> 7; everything else identical.
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", False)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "why does this pattern tend to be fragile?", "user_text")
    assert frame.confidence_need >= 0.60
    assert frame.governance_sensitive is False
    assert frame.identity_sensitive is False

    off = ctl.build_memory_plan(frame, mode).to_dict()
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    on = ctl.build_memory_plan(frame, mode).to_dict()

    assert off["top_k_by_lane"]["core"] == 6
    assert on["top_k_by_lane"]["core"] == 7
    for key in off:
        if key == "top_k_by_lane":
            continue
        assert on[key] == off[key], f"field {key!r} changed under core shaping"
    off_topk, on_topk = off["top_k_by_lane"], on["top_k_by_lane"]
    for lane in ("relational", "archive", "deep", "collective"):
        assert on_topk[lane] == off_topk[lane], f"lane {lane!r} changed"
    assert on_topk["core"] - off_topk["core"] == 1


def test_core_flag_on_below_threshold_unchanged(monkeypatch):
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "tell me about the weather", "user_text")
    assert frame.confidence_need < 0.60
    assert ctl.build_memory_plan(frame, mode).top_k_by_lane["core"] == 6


def test_core_flag_on_identity_sensitive_no_bump(monkeypatch):
    # Identity-sensitive turn at/above threshold: guard blocks the bump.
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "why does my identity drift tend to be fragile?", "user_text")
    assert frame.identity_sensitive is True
    assert frame.confidence_need >= 0.60
    assert ctl.build_memory_plan(frame, mode).top_k_by_lane["core"] == 6


def test_core_flag_on_governance_sensitive_no_bump(monkeypatch):
    # Governance-sensitive turn at/above threshold: guard blocks the bump.
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "why does deleting this policy tend to be fragile?", "user_text")
    assert frame.governance_sensitive is True
    assert frame.confidence_need >= 0.60
    assert ctl.build_memory_plan(frame, mode).top_k_by_lane["core"] == 6


def test_core_shaping_cap_never_reduce_and_guards(monkeypatch):
    # Direct unit test of the rule: +1 / cap at 7 / never-reduce / disabled-lane
    # / threshold / governance + identity guards / flag-off.
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    ctl = ThinkingController()

    def _shaped(core_val, *, conf=0.60, governance=False, identity=False):
        plan = MemoryPlan()
        plan.top_k_by_lane = {"core": core_val, "deep": 3}
        ctl._apply_cognition_core_shaping_v1(
            plan, _state_for_core(conf, governance=governance, identity=identity)
        )
        return plan.top_k_by_lane["core"]

    assert _shaped(6) == 7            # +1
    assert _shaped(7) == 7            # cap at 7
    assert _shaped(8) == 8            # never reduce an already-larger value
    assert _shaped(0) == 0            # disabled lane untouched
    assert _shaped(6, conf=0.59) == 6             # below threshold
    assert _shaped(6, governance=True) == 6       # governance guard
    assert _shaped(6, identity=True) == 6         # identity guard

    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", False)
    plan = MemoryPlan()
    plan.top_k_by_lane = {"core": 6}
    ctl._apply_cognition_core_shaping_v1(plan, _state_for_core(0.60))
    assert plan.top_k_by_lane["core"] == 6


def test_core_and_slice2_flags_are_independent(monkeypatch):
    # Slice 3 fires under its own flag only; Slice 2's flag does not trigger it
    # and vice versa.
    ctl = ThinkingController()
    frame, mode = _frame_and_mode(ctl, "why does this pattern tend to be fragile?", "user_text")
    # Slice 2 ON, Slice 3 OFF -> core unchanged (this input's ambiguity < 0.50,
    # and core is not Slice 2's lane regardless).
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", True)
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", False)
    assert ctl.build_memory_plan(frame, mode).top_k_by_lane["core"] == 6
    # Slice 3 ON, Slice 2 OFF -> core bumps.
    monkeypatch.setattr(tc, "_COGNITION_SHAPING_V2_ENABLE", False)
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    assert ctl.build_memory_plan(frame, mode).top_k_by_lane["core"] == 7


def test_core_flag_on_does_not_expose_state(monkeypatch):
    # Flag ON must not change /think result shape or expose the ephemeral state.
    monkeypatch.setattr(tc, "_COGNITION_CORE_SHAPING_V1_ENABLE", True)
    ctl = ThinkingController()
    payload = ctl.think("ws", "ag", "why does this pattern tend to be fragile?").to_dict()
    expected_keys = {
        "task_frame", "mode_decision", "memory_plan", "action_decision",
        "review_result", "response_draft", "stance", "geometric_context",
        "debug", "reflection_trace",
    }
    assert set(payload) == expected_keys
    for key in payload:
        assert "ephemeral" not in key
        assert "cognition_state" not in key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
