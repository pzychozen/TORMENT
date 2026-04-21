# tests/test_block_b_primitives_not_substitutable.py
"""
T3 — AC-3.1: load and consult are not substitutable.

Covers the acceptance criterion from BLOCK_B_DESIGN.md §4.3:

    Calling fabric.load_reference with an ID that points to an
    environment entry, or fabric.consult_environment with an operation
    that is really a reference-load request, produces a specific
    mismatch result naming the primitive/category error. Mechanism-
    neutral: exception, ok=False envelope, or named result code are
    all acceptable — the behavior must not be silent empty, implicit
    coercion, or convergent success.

Design intent per PRE_BLOCK_B_PRECONDITIONS.md §4:

    load is pull-for-thinking — intentional, sustained, reasoning-
    oriented. consult is consult-at-action-site — action-scoped,
    relevance-filtered, does not stay in context. The two primitives
    must remain visibly distinct in code.

The failure modes this test guards against:

    - silent empty: calling load_reference with a non-reference id
      and getting an empty body with ok=True and no indication
      anything went wrong
    - implicit coercion: load_reference automatically looking up in
      environment store on failure, returning environment content
      instead
    - convergent success: a shared "get_block_b_memory_by_id" helper
      that eventually collapses both primitives into one call path

These tests FAIL against current code (pre-implementation). They pass
once the two primitives are implemented as separate methods with
incompatible signatures and explicit mismatch-result behavior on
cross-category calls.
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.fabric import TormentFabric


class TestMethodsExistSeparately(unittest.TestCase):
    """Both methods must exist as separately-named, separately-signatured
    entry points on TormentFabric."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")

    def test_load_reference_exists(self) -> None:
        self.assertTrue(hasattr(self.fabric, "load_reference"))

    def test_consult_environment_exists(self) -> None:
        self.assertTrue(hasattr(self.fabric, "consult_environment"))

    def test_signatures_are_incompatible(self) -> None:
        """load_reference takes ref_id; consult_environment takes
        operation+scope. The two signatures must not be interchangeable."""
        load_sig = inspect.signature(self.fabric.load_reference)
        consult_sig = inspect.signature(self.fabric.consult_environment)

        load_params = set(load_sig.parameters.keys())
        consult_params = set(consult_sig.parameters.keys())

        # load takes ref_id; consult does not
        self.assertIn("ref_id", load_params)
        self.assertNotIn("ref_id", consult_params)

        # consult takes operation + scope; load does not
        self.assertIn("operation", consult_params)
        self.assertIn("scope", consult_params)
        self.assertNotIn("operation", load_params)

    def test_no_generic_get_block_b_memory_helper_exists(self) -> None:
        """Guard against a collapse-temptation future helper. Any method
        name like 'get_block_b_memory_by_id' or 'get_memory_b' that
        could bypass the category boundary is forbidden."""
        forbidden_names = (
            "get_block_b_memory_by_id",
            "get_memory_b",
            "get_block_b",
            "resolve_block_b_entry",
            "fetch_reference_or_environment",
        )
        for name in forbidden_names:
            self.assertFalse(
                hasattr(self.fabric, name),
                f"Forbidden collapse-temptation helper {name!r} exists. "
                "Preconditions §4 forbids generic get-memory helpers that "
                "would collapse load/consult."
            )


class TestLoadWithEnvironmentIdIsMismatch(unittest.TestCase):
    """A load_reference call with an ID that is NOT in the reference
    store (including an env_id) must return a mismatch result. It must
    not silently succeed, silently return empty body, or implicitly
    coerce to environment-memory lookup."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        # Write an environment entry to get its env_id
        env_result = self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="network_available",
            value=True,
            evidence_class="user_asserted",
            ownership="user",
            asserted_by="pzychozen",
        )
        self.env_id = env_result.get("env_id")
        self.assertTrue(self.env_id, "precondition: env entry was written")

        # Ingest a reference for comparison
        ref_result = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="A reference",
            body="the reference body",
            source_link="docs/ref.md",
            source_kind="repo_file",
        )
        self.ref_id = ref_result.get("ref_id")
        self.assertTrue(self.ref_id, "precondition: reference was ingested")

    def test_load_with_ref_id_succeeds(self) -> None:
        """Sanity check — load works with a real ref_id."""
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("result_code"), "loaded")

    def test_load_with_env_id_returns_mismatch(self) -> None:
        """Passing an env_id to load_reference must not silently succeed
        and must not implicitly coerce into an environment lookup. The
        result_code is mechanism-neutral (not_found is acceptable; an
        explicit mismatch code is better)."""
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.env_id,  # WRONG category identifier
            scope_tag="scope_a",
        )
        # Must not silently succeed
        self.assertNotEqual(
            result.get("result_code"), "loaded",
            "load_reference must not silently succeed on an env_id"
        )
        # Must not return environment content (coercion)
        self.assertNotIn(
            "value", result,
            "load_reference must not coerce to environment lookup"
        )
        self.assertNotIn(
            "evidence_class", result,
            "load_reference must not return environment-shaped fields"
        )
        # Acceptable result codes per preconditions §6.3:
        # not_found, category_mismatch, mismatch, etc.
        self.assertIn(
            result.get("result_code"),
            ("not_found", "category_mismatch", "mismatch",
             "not_a_reference"),
            f"Unexpected result_code: {result.get('result_code')!r}"
        )


class TestReturnShapesAreDistinct(unittest.TestCase):
    """The two primitives must return structurally incompatible envelopes.
    load returns body/stale/load_id (single-object); consult returns
    facts list (view-over-entries). A caller that tries to treat one
    as the other will fail type-check-style assertions."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

        ref_result = self.fabric.ingest_reference(
            workspace_id="ws1",
            title="Ref",
            body="body content",
            source_link="docs/r.md",
            source_kind="repo_file",
        )
        self.ref_id = ref_result["ref_id"]

        self.fabric.write_environment(
            workspace_id="ws1",
            target_runtime="python_3.10",
            scope_tag="default",
            key="k", value="v",
            evidence_class="user_asserted", ownership="user",
            asserted_by="test",
        )

    def test_load_envelope_is_single_object_shape(self) -> None:
        result = self.fabric.load_reference(
            workspace_id="ws1", agent_id="atlas",
            ref_id=self.ref_id, scope_tag="scope_a",
        )
        # Single-object shape: has body and load_id
        self.assertIn("body", result)
        self.assertIn("load_id", result)
        # Not a view-over-list shape
        self.assertNotIn("facts", result)

    def test_consult_envelope_is_view_over_list_shape(self) -> None:
        result = self.fabric.consult_environment(
            workspace_id="ws1", operation="any", scope="default",
        )
        # View-over-list shape: has facts list
        self.assertIn("facts", result)
        self.assertIsInstance(result["facts"], list)
        # Not a single-object shape
        self.assertNotIn("body", result)
        self.assertNotIn("load_id", result)


if __name__ == "__main__":
    unittest.main()
