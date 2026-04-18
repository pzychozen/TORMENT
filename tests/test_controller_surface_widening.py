"""§2A controller-surface widening: contract tests.

Validates that relational cues trigger RETRIEVAL mode and analytical
depth cues trigger REFLECTIVE mode, without disturbing B5 FAST routing.

Ratified decisions: D1=(a) relational→memory_need, D2=(a) analytical→confidence_need,
D3=(c) keep substring matcher with space-padded hints.
"""

from torment_service.thinking_controller import ThinkingController


tc = ThinkingController()


def _mode(query: str) -> str:
    """Return the chosen mode string for a query."""
    frame = tc.frame_task("ws_test", "agent_test", query)
    return tc.choose_mode(frame).chosen_mode.value


def _frame(query: str):
    """Return the TaskFrame for a query."""
    return tc.frame_task("ws_test", "agent_test", query)


# ---------------------------------------------------------------------------
# D1: Relational cues → RETRIEVAL
# ---------------------------------------------------------------------------

class TestRelationalRetrieval:
    """B2-style collaborative/relational queries should route to RETRIEVAL."""

    def test_we_agreed(self):
        assert _mode("What did we agree about handling that issue?") == "retrieval"

    def test_our_stance(self):
        assert _mode("What was our stance on that proposal?") == "retrieval"

    def test_settled(self):
        assert _mode("What did we settle on for that workflow?") == "retrieval"

    def test_concluded(self):
        assert _mode("What did we conclude about handling the edge case?") == "retrieval"

    def test_decided(self):
        assert _mode("Which approach did we decide to keep?") == "retrieval"

    def test_together(self):
        assert _mode("Pick up from the conclusion we reached together.") == "retrieval"

    def test_position(self):
        assert _mode("What position did we take once we reviewed that problem?") == "retrieval"

    def test_team_position(self):
        assert _mode("What was the team position on the earlier plan?") == "retrieval"

    def test_memory_need_is_true(self):
        """Relational cues should set memory_need=True on the frame."""
        frame = _frame("What did we agree about that?")
        assert frame.memory_need is True

    def test_we_at_start_of_sentence(self):
        """'we' at the start should still match (input is space-padded)."""
        assert _mode("We decided to go with plan B.") == "retrieval"

    def test_no_false_positive_awesome(self):
        """'we' inside 'awesome' must not trigger relational."""
        frame = _frame("That is awesome.")
        assert frame.memory_need is False

    def test_no_false_positive_our_in_four(self):
        """'our' inside 'four' must not trigger relational (space-padded)."""
        frame = _frame("There are four options.")
        assert frame.memory_need is False


# ---------------------------------------------------------------------------
# D2: Analytical depth → REFLECTIVE
# ---------------------------------------------------------------------------

class TestAnalyticalReflective:
    """B3-style analytical queries should route to REFLECTIVE."""

    def test_why_does_pattern(self):
        assert _mode("Why does that pattern keep reappearing in different contexts?") == "reflective"

    def test_tradeoff(self):
        assert _mode("How does that tradeoff usually resolve over time?") == "reflective"

    def test_assumption(self):
        assert _mode("What hidden assumption usually makes that move seem reasonable?") == "reflective"

    def test_bias(self):
        assert _mode("What makes that bias show up there but not everywhere else?") == "reflective"

    def test_tension(self):
        assert _mode("What usually has to give for that tension to settle?") == "reflective"

    def test_interact(self):
        assert _mode("How do those two ideas interact when you combine them?") == "reflective"

    def test_robust_fragile(self):
        assert _mode("What makes that approach robust in one domain but fragile in another?") == "reflective"

    def test_tend_to(self):
        assert _mode("Why do systems like that tend to evolve in that direction?") == "reflective"

    def test_behind_the_scenes(self):
        assert _mode("What tends to shape that outcome behind the scenes?") == "reflective"

    def test_confidence_need_crosses_threshold(self):
        """Analytical question should reach confidence_need >= 0.60."""
        frame = _frame("Why does that pattern keep reappearing?")
        assert frame.confidence_need >= 0.60


# ---------------------------------------------------------------------------
# D4: B5 guard — FAST must hold
# ---------------------------------------------------------------------------

class TestB5Guard:
    """B5-style terse/directive queries must remain FAST after widening."""

    def test_keep_brief(self):
        assert _mode("Keep this brief.") == "fast"

    def test_main_point(self):
        assert _mode("Just the main point.") == "fast"

    def test_say_plainly(self):
        assert _mode("Say it plainly.") == "fast"

    def test_one_sentence(self):
        assert _mode("One sentence only.") == "fast"

    def test_whats_main_point(self):
        assert _mode("What's the main point here?") == "fast"

    def test_what_matters(self):
        assert _mode("What matters most here?") == "fast"

    def test_direct_answer(self):
        assert _mode("Give me the direct answer.") == "fast"

    def test_simplest_way(self):
        assert _mode("What's the simplest way to say it?") == "fast"

    def test_boil_down(self):
        assert _mode("Boil that down.") == "fast"

    def test_short_and_clear(self):
        assert _mode("Keep it short and clear.") == "fast"


# ---------------------------------------------------------------------------
# Existing mode routing must be undisturbed
# ---------------------------------------------------------------------------

class TestExistingModesUndisturbed:
    """Verify the patch doesn't break identity, governance, or tool routing."""

    def test_identity_still_works(self):
        assert _mode("Who are you?") == "identity_sensitive"

    def test_governance_still_works(self):
        assert _mode("Delete that memory from the canon.") == "governed"

    def test_tool_still_works(self):
        # v0.1.0d: "search" moved from TOOL_HINT_WORDS to
        # RETRIEVAL_HINT_WORDS (unmapped). Use an explicit execution
        # verb so the test continues to validate TOOL routing.
        assert _mode("Run code to tally recent entries about that topic.") == "tool"

    def test_archive_retrieval_still_works(self):
        assert _mode("What does the document say about that?") == "retrieval"
