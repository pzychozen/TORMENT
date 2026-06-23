"""Characterization: audit evidence-packet exclusion MARKERS are identifiable.

This is MARKER / READERS characterization, **not** packet-filter implementation.
It proves the future admissible-evidence-packet contract's exclusion markers are
identifiable with EXISTING source behavior — it builds no filter, no packet, no
evaluator, and adds no production code or new filtering semantics.

It exercises only existing pure helpers/readers:
  * ``lifecycle.derive_protected_lifecycle_from_legacy_markers`` (the legacy
    protected-marker reader: canon / kind|type / tier / srg.is_crystal /
    governance.protected → PROTECTED, else None);
  * ``governance.filter_llm_facing(..., surface=SURFACE_LLM_CONTEXT)`` (the
    existing universal LLM-facing exclusion: non_shareable);
  * direct disposable-dict marker reads where no helper exists (scope,
    deep_memory, spirit_return_mode).

Honest cautions (carried from Codex review):
  * ``filter_llm_facing(..., SURFACE_LLM_CONTEXT)`` does **NOT** exclude private
    memory — private memory may be model-visible to its own agent today. Here
    ``scope=="private"`` is characterized only as a *packet-contract exclusion
    marker*, identifiable by direct read, not by the LLM-facing filter.
  * ``deep_memory`` / ``spirit_return_mode`` are characterized as *deep /
    spirit-return markers* identifiable and excluded by the packet contract —
    no stronger "private-cognition" claim is made about them here.
  * ``srg.is_crystal`` is treated **only** as the known silent-honoring
    anti-pattern marker. SRG / R-field behavior is not reopened, altered, or
    revalidated.
  * "raw_hits absent by default" is asserted only for the default
    ``include_raw_hits=False`` call; it is **not** generalized to all
    context-assembly paths.
  * No claim is made that current LLM-facing retrieval excludes every class the
    future audit packet would exclude. The packet contract layers its own
    exclusions on top of existing markers.

Explicitly deferred (require a builder that does not exist yet, so NOT tested
here): caps (max 8 items / 240 chars each / 2,000 total); primitive-only packet
shape; snippets drawn only from already-admitted response context; no fresh
retrieval; no raw-hit rebuild; whole prompt-transcript / hidden-CoT / raw-model-
reasoning exclusions.
"""

import unittest

from torment_service.lifecycle import derive_protected_lifecycle_from_legacy_markers
from torment_service.governance import filter_llm_facing, SURFACE_LLM_CONTEXT


class TestLifecycleProtectedMarkersIdentifyExclusionClasses(unittest.TestCase):
    """The legacy protected-marker reader identifies the packet contract's
    canon / seed / identity / tier / governance-protected exclusion classes.

    A future packet filter keying on these markers would therefore exclude the
    corresponding class. Negative control: a non-sensitive shared memory is not
    flagged.
    """

    def test_canon_true_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers({"canon": True}, now=0)
        )

    def test_kind_seed_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers({"kind": "seed"}, now=0)
        )

    def test_kind_identity_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers({"kind": "identity"}, now=0)
        )

    def test_kind_core_identity_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers(
                {"kind": "core_identity"}, now=0
            )
        )

    def test_type_fallback_for_kind_is_protected(self):
        # `kind` absent → reader falls back to `type` (seed/identity/core_identity).
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers({"type": "seed"}, now=0)
        )

    def test_tier_core_identity_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers(
                {"tier": "core_identity"}, now=0
            )
        )

    def test_governance_protected_is_protected(self):
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers(
                {"governance": {"protected": True}}, now=0
            )
        )

    def test_srg_is_crystal_is_the_named_antipattern_marker(self):
        # Anti-pattern reference ONLY: a payload key runtime readers silently
        # honor. SRG / R-field behavior is not reopened or revalidated here.
        self.assertIsNotNone(
            derive_protected_lifecycle_from_legacy_markers(
                {"srg": {"is_crystal": True}}, now=0
            )
        )

    def test_non_sensitive_shared_control_is_not_protected(self):
        self.assertIsNone(
            derive_protected_lifecycle_from_legacy_markers(
                {"kind": "observation", "scope": "shared"}, now=0
            )
        )


class TestPacketContractMarkersNotCaughtByLifecycleReader(unittest.TestCase):
    """Markers that are packet-contract exclusions but are NOT legacy protected
    markers — identifiable by direct read, not by the lifecycle reader.
    """

    def test_scope_private_is_not_a_lifecycle_protected_marker(self):
        # scope is not one of the five legacy protected markers; the lifecycle
        # reader returns None. It is a packet-contract exclusion marker only.
        self.assertIsNone(
            derive_protected_lifecycle_from_legacy_markers({"scope": "private"}, now=0)
        )

    def test_scope_private_identifiable_by_direct_read(self):
        payload = {"scope": "private"}
        self.assertEqual(payload.get("scope"), "private")

    def test_deep_memory_marker_identifiable_by_direct_read(self):
        # Deep / spirit-return marker; not a lifecycle protected marker.
        payload = {"deep_memory": True}
        self.assertTrue(bool(payload.get("deep_memory")))
        self.assertIsNone(
            derive_protected_lifecycle_from_legacy_markers(payload, now=0)
        )

    def test_spirit_return_mode_marker_identifiable_by_direct_read(self):
        # Deep / spirit-return marker; not a lifecycle protected marker.
        payload = {"spirit_return_mode": "resonance"}
        self.assertEqual(payload.get("spirit_return_mode"), "resonance")
        self.assertIsNone(
            derive_protected_lifecycle_from_legacy_markers(payload, now=0)
        )


class TestNonShareableExcludedByLlmFacingFilter(unittest.TestCase):
    """The existing universal LLM-facing exclusion removes non_shareable hits.

    Honest boundary: this filter does NOT exclude private-scope memory, and
    "raw_hits absent" holds only for the default include_raw_hits=False call.
    """

    @staticmethod
    def _eids(items):
        return {it.get("eid") for it in items}

    def test_non_shareable_hit_is_excluded(self):
        out = filter_llm_facing(
            [{"eid": 1, "governance": {"non_shareable": True}}],
            surface=SURFACE_LLM_CONTEXT,
        )
        self.assertIn(1, self._eids(out["excluded"]))
        self.assertNotIn(1, self._eids(out["results"]))
        self.assertTrue(
            any(e.get("excluded_reason") == "non_shareable" for e in out["excluded"])
        )

    def test_shareable_hit_is_in_results(self):
        out = filter_llm_facing([{"eid": 2}], surface=SURFACE_LLM_CONTEXT)
        self.assertIn(2, self._eids(out["results"]))

    def test_private_scope_hit_is_not_excluded_by_filter(self):
        # CAUTION (Codex): filter_llm_facing does NOT exclude private memory;
        # private may be model-visible to its own agent. The packet contract's
        # scope exclusion is SEPARATE from this filter.
        out = filter_llm_facing(
            [{"eid": 3, "scope": "private"}], surface=SURFACE_LLM_CONTEXT
        )
        self.assertIn(3, self._eids(out["results"]))

    def test_raw_hits_absent_by_default(self):
        # Valid only for include_raw_hits=False (the default). Not generalized.
        out = filter_llm_facing([{"eid": 4}], surface=SURFACE_LLM_CONTEXT)
        self.assertNotIn("raw_hits", out)


if __name__ == "__main__":
    unittest.main()
