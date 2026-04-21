# tests/test_environment_consult_boundary.py
"""
T2 — AC-2.1 through AC-2.5: environment memory consult boundary tests.

Covers acceptance criteria from BLOCK_B_DESIGN.md §4.2:

    AC-2.1 — Environment writes require one of three evidence classes.
    AC-2.2 — Inferred writes require a named inference rule.
    AC-2.3 — Consult is relevance-filtered and returns a view, not entries.
    AC-2.4 — Environment facts never auto-inject into prompt context.
    AC-2.5 — Probe-on-fail produces observed provenance only.

Design intent per BLOCK_B_DESIGN.md §7 and the carry-forward caution
from ratification:

    Entry identity is separate from consult result shape. An
    EnvironmentEntry has its own persistent payload; consult returns
    an EnvironmentConsultResult that is a VIEW over relevant entries
    with reduced fields (no env_id, no workspace_id, no full
    provenance). The two shapes must not collapse.

    VALID_INFERENCE_RULES ships empty in v0.1 — no inferred writes
    accepted until explicit future ratification.

Environment is the higher-risk category. Tests are deliberately strict.

These tests FAIL against current code (pre-implementation). They pass
once:
    - torment_service.environment_memory.EnvironmentStore exists
    - fabric.write_environment / consult_environment
      / probe_environment_on_fail exist with specified envelopes
    - Three ProvenanceV1 factories land (user_asserted, observed, inferred)
    - VALID_INFERENCE_RULES frozenset exists (empty in v0.1)
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# AC-2.1 — evidence class required on every write
# ---------------------------------------------------------------------------


class TestEnvironmentWriteRequiresEvidenceClass(unittest.TestCase):
    """Block B §4.2 AC-2.1: every write declares user_asserted, observed,
    or inferred. Missing or invalid evidence_class → rejected."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_fabric_has_write_environment(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "write_environment"),
            "fabric.write_environment must exist per §7.2"
        )

    def test_user_asserted_write_succeeds(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="network_available",
            value=True,
            evidence_class="user_asserted",
            ownership="user",
            asserted_by="pzychozen",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "written")
        self.assertTrue(result.get("env_id"))

    def test_observed_write_succeeds(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="linux_sandbox",
            scope_tag="default",
            key="python_version",
            value="3.10.12",
            evidence_class="observed",
            ownership="system",
            observation_source="python_version_probe",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "written")

    def test_missing_evidence_class_is_rejected(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="network_available",
            value=True,
            evidence_class="",  # empty
            ownership="user",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_evidence_class")

    def test_unknown_evidence_class_is_rejected(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="network_available",
            value=True,
            evidence_class="vibes",  # invalid
            ownership="user",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_evidence_class")

    def test_user_asserted_requires_asserted_by(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="network_available",
            value=True,
            evidence_class="user_asserted",
            ownership="user",
            # asserted_by omitted
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_evidence_field")

    def test_observed_requires_observation_source(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="linux_sandbox",
            scope_tag="default",
            key="python_version",
            value="3.10.12",
            evidence_class="observed",
            ownership="system",
            # observation_source omitted
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_evidence_field")


# ---------------------------------------------------------------------------
# AC-2.2 — inferred requires a named, ratified inference rule
# ---------------------------------------------------------------------------


class TestInferredRequiresRatifiedRule(unittest.TestCase):
    """v0.1 ships with VALID_INFERENCE_RULES empty. No inferred writes
    are accepted until rule ratification lands."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_valid_inference_rules_constant_exists(self) -> None:
        from torment_service.environment_memory import VALID_INFERENCE_RULES
        self.assertIsInstance(VALID_INFERENCE_RULES, frozenset)

    def test_valid_inference_rules_empty_in_v0_1(self) -> None:
        """Per §7.1: v0.1 ships with zero rules. Any rule addition
        requires explicit future ratification. This test pins the
        v0.1 strict posture."""
        from torment_service.environment_memory import VALID_INFERENCE_RULES
        self.assertEqual(
            len(VALID_INFERENCE_RULES), 0,
            "VALID_INFERENCE_RULES must be empty in v0.1 per "
            "BLOCK_B_DESIGN §7.1"
        )

    def test_inferred_without_rule_is_rejected(self) -> None:
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="something",
            value="some_value",
            evidence_class="inferred",
            ownership="system",
            # inference_rule omitted
        )
        self.assertFalse(result.get("ok"))
        self.assertIn(
            result.get("result_code"),
            ("inferred_requires_rule", "missing_evidence_field"),
        )

    def test_inferred_with_unknown_rule_is_rejected(self) -> None:
        """Even with a rule name, if it's not in VALID_INFERENCE_RULES,
        reject. This closes the R+5 back door."""
        result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="something",
            value="some_value",
            evidence_class="inferred",
            ownership="system",
            inference_rule="some_unregistered_rule",
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "unknown_inference_rule")


# ---------------------------------------------------------------------------
# AC-2.3 — consult is relevance-filtered and returns a view
# ---------------------------------------------------------------------------


class TestConsultReturnsViewNotEntries(unittest.TestCase):
    """Consult returns EnvironmentConsultResult — a VIEW — not the
    underlying EnvironmentEntry objects. Entry identity is separate
    from consult result shape (carry-forward caution)."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

        # Write two facts in the same scope, one in a different scope
        self.fabric.write_environment(
            workspace_id="ws1", target_runtime="python_3.10",
            scope_tag="default", key="network_available", value=True,
            evidence_class="user_asserted", ownership="user",
            asserted_by="pzychozen",
        )
        self.fabric.write_environment(
            workspace_id="ws1", target_runtime="python_3.10",
            scope_tag="default", key="python_version", value="3.10.12",
            evidence_class="observed", ownership="system",
            observation_source="python_version_probe",
        )
        self.fabric.write_environment(
            workspace_id="ws1", target_runtime="linux_sandbox",
            scope_tag="test_env", key="ephemeral_fs", value=True,
            evidence_class="observed", ownership="system",
            observation_source="fs_probe",
        )

    def test_fabric_has_consult_environment(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "consult_environment"),
            "fabric.consult_environment must exist per §7.3"
        )

    def test_consult_returns_envelope_with_facts_list(self) -> None:
        result = self.fabric.consult_environment(
            workspace_id="ws1",
            operation="any_op",
            scope="default",
        )
        self.assertTrue(result.get("ok"))
        self.assertIn(
            result.get("result_code"), ("consulted", "no_relevant_facts")
        )
        self.assertIsInstance(result.get("facts"), list)

    def test_consult_filters_by_scope(self) -> None:
        """Default-scope consult should not return test_env facts."""
        result = self.fabric.consult_environment(
            workspace_id="ws1",
            operation="any_op",
            scope="default",
        )
        keys = [f.get("key") for f in result.get("facts", [])]
        self.assertNotIn("ephemeral_fs", keys,
                         "scope filter must hide facts from other scopes")

    def test_consult_result_is_a_view_not_entries(self) -> None:
        """Per carry-forward caution: consult returns a view shape,
        NOT the underlying EnvironmentEntry. The fact dicts must NOT
        carry env_id, workspace_id, or the full provenance dict."""
        result = self.fabric.consult_environment(
            workspace_id="ws1",
            operation="any_op",
            scope="default",
        )
        facts = result.get("facts", [])
        self.assertGreater(len(facts), 0, "precondition: setup wrote facts")
        for fact in facts:
            # View shape — identity fields absent
            self.assertNotIn(
                "env_id", fact,
                "consult result must not echo env_id (view, not entry)"
            )
            self.assertNotIn(
                "workspace_id", fact,
                "consult result must not echo workspace_id (view, not entry)"
            )
            self.assertNotIn(
                "provenance", fact,
                "consult result must not echo full provenance (view, not entry)"
            )
            # View shape — required fields present
            self.assertIn("key", fact)
            self.assertIn("value", fact)
            self.assertIn("evidence_class", fact)

    def test_consult_empty_scope_returns_no_relevant_facts(self) -> None:
        result = self.fabric.consult_environment(
            workspace_id="ws1",
            operation="any_op",
            scope="nonexistent_scope",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "no_relevant_facts")
        self.assertEqual(result.get("facts"), [])


# ---------------------------------------------------------------------------
# AC-2.4 — environment never in prompt context
# ---------------------------------------------------------------------------


class TestEnvironmentNotInAssembler(unittest.TestCase):
    """Environment facts must NEVER reach any retrieval_assembler output.
    Hard structural exclusion, not a filter."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

        self.fabric.write_environment(
            workspace_id="ws1", target_runtime="python_3.10",
            scope_tag="default", key="network_available", value=True,
            evidence_class="user_asserted", ownership="user",
            asserted_by="pzychozen",
        )

    def test_environment_not_a_memory_plan_lane(self) -> None:
        """MemoryPlan must not have a retrieve_environment field —
        environment is not a lane (preconditions §4)."""
        from torment_service.thinking_models import MemoryPlan
        plan_fields = set(MemoryPlan.__dataclass_fields__.keys())
        for forbidden in ("retrieve_environment", "retrieve_env"):
            self.assertNotIn(
                forbidden, plan_fields,
                f"MemoryPlan must not have {forbidden!r} — environment is "
                "not a retrieval lane"
            )

    def test_no_block_environment_constant_in_assembler(self) -> None:
        """retrieval_assembler must not have a BLOCK_ENVIRONMENT
        constant — environment must not be a prompt-context citizen."""
        from torment_service import retrieval_assembler as ra
        for forbidden in ("BLOCK_ENVIRONMENT", "BLOCK_ENV"):
            self.assertFalse(
                hasattr(ra, forbidden),
                f"retrieval_assembler must not declare {forbidden} "
                "(R+4: environment never auto-injects)"
            )

    def test_fill_order_excludes_environment(self) -> None:
        from torment_service.retrieval_assembler import FILL_ORDER
        for block_type in FILL_ORDER:
            self.assertNotIn(
                "environment", block_type.lower(),
                f"FILL_ORDER must not mention environment; got {block_type}"
            )


# ---------------------------------------------------------------------------
# AC-2.5 — probe_on_fail is observed-only
# ---------------------------------------------------------------------------


class TestProbeOnFailObservedOnly(unittest.TestCase):
    """probe_environment_on_fail forces evidence_class='observed' and
    requires observation_source. LLM guesswork cannot reach environment
    memory through this path."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_fabric_has_probe_on_fail(self) -> None:
        self.assertTrue(
            hasattr(self.fabric, "probe_environment_on_fail"),
            "fabric.probe_environment_on_fail must exist per §7.4"
        )

    def test_probe_writes_with_observed_evidence_class(self) -> None:
        result = self.fabric.probe_environment_on_fail(
            workspace_id="ws1",
            target_runtime="linux_sandbox",
            scope_tag="default",
            key="network_available",
            value=False,
            observation_source="tool_call_failed_with_connection_error",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "written")

        # Fetch back and assert provenance shape. Environment stores
        # live on fabric.environment_stores[workspace_id] per the
        # ratified design (per-workspace, not per-workspace-object).
        env_id = result.get("env_id")
        store = self.fabric._get_environment_store("ws1")
        entry = store.get(env_id)
        self.assertIsNotNone(
            entry,
            "probe result must be retrievable for provenance inspection"
        )
        evidence_class = getattr(entry, "evidence_class", None) \
            or (entry.get("evidence_class") if isinstance(entry, dict) else None)
        self.assertEqual(
            evidence_class, "observed",
            "probe_on_fail MUST produce observed provenance"
        )

    def test_probe_requires_observation_source(self) -> None:
        """Even the probe path requires a non-empty observation_source."""
        result = self.fabric.probe_environment_on_fail(
            workspace_id="ws1",
            target_runtime="linux_sandbox",
            scope_tag="default",
            key="some_key",
            value="some_value",
            observation_source="",  # empty
        )
        self.assertFalse(result.get("ok"))
        self.assertEqual(result.get("result_code"), "missing_evidence_field")


if __name__ == "__main__":
    unittest.main()
