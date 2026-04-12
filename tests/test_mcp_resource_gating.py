"""Tests for MCP resource exposure-tier gating.

Covers:
  - Sensitive resources (provenance, admin/status) hidden below guarded tier
  - Low-risk resources remain available at open tier
  - exposure_allows() shared helper consistency
  - Tools and resources share the same tier logic
"""
import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.spine import (
    exposure_allows,
    EXPOSURE_OPEN,
    EXPOSURE_GUARDED,
    EXPOSURE_INTERNAL,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_resource_uris(max_tier: str) -> set:
    """Create an MCP server at the given tier and return all resource URIs.

    FastMCP splits parameterised resources (with {workspace_id} etc.) into
    "resource templates" and non-parameterised ones into plain "resources".
    This helper merges both lists so tests can check for any registered
    resource surface regardless of parameterisation.
    """
    # Set the tier before importing/creating the server
    old_tier = os.environ.get("TORMENT_MCP_EXPOSURE_TIER")
    os.environ["TORMENT_MCP_EXPOSURE_TIER"] = max_tier
    # Set minimal context so create_mcp_server doesn't warn excessively
    os.environ.setdefault("TORMENT_MCP_DATA_DIR", "/tmp/torment_test_mcp_gating")
    os.environ.setdefault("TORMENT_MCP_WORKSPACE_ID", "test_ws")
    os.environ.setdefault("TORMENT_MCP_AGENT_ID", "test_agent")

    try:
        # Force re-read of env by resetting module-level singletons
        import torment_service.mcp_server as mcp_mod
        mcp_mod._fabric = None
        mcp_mod._client_ctx = None

        mcp = mcp_mod.create_mcp_server()
        resources = asyncio.run(mcp.list_resources())
        templates = asyncio.run(mcp.list_resource_templates())
        uris = {str(r.uri) for r in resources}
        uris |= {str(t.uriTemplate) for t in templates}
        return uris
    finally:
        if old_tier is None:
            os.environ.pop("TORMENT_MCP_EXPOSURE_TIER", None)
        else:
            os.environ["TORMENT_MCP_EXPOSURE_TIER"] = old_tier


# ---------------------------------------------------------------------------
# Test: exposure_allows() shared helper
# ---------------------------------------------------------------------------

class TestExposureAllows:
    """Unit tests for the canonical tier-comparison helper."""

    def test_open_allows_open(self):
        assert exposure_allows("open", "open") is True

    def test_open_allows_guarded(self):
        assert exposure_allows("open", "guarded") is True

    def test_guarded_requires_guarded(self):
        assert exposure_allows("guarded", "open") is False

    def test_guarded_allows_guarded(self):
        assert exposure_allows("guarded", "guarded") is True

    def test_guarded_allows_internal(self):
        assert exposure_allows("guarded", "internal") is True

    def test_internal_requires_internal(self):
        assert exposure_allows("internal", "open") is False
        assert exposure_allows("internal", "guarded") is False
        assert exposure_allows("internal", "internal") is True


# ---------------------------------------------------------------------------
# Test: provenance resource hidden below guarded tier
# ---------------------------------------------------------------------------

class TestMCPProvenanceResourceGating:

    def test_mcp_provenance_resource_requires_guarded_tier(self):
        """provenance resource should not appear when tier is 'open'."""
        uris = _get_resource_uris("open")
        provenance_uris = [u for u in uris if "provenance" in u]
        assert len(provenance_uris) == 0, (
            f"Provenance resource should be hidden at open tier, found: {provenance_uris}"
        )

    def test_mcp_provenance_resource_available_at_guarded_tier(self):
        """provenance resource should appear when tier is 'guarded'."""
        uris = _get_resource_uris("guarded")
        provenance_uris = [u for u in uris if "provenance" in u]
        assert len(provenance_uris) == 1, (
            f"Provenance resource should be visible at guarded tier, found: {provenance_uris}"
        )


# ---------------------------------------------------------------------------
# Test: admin/status resource hidden below guarded tier
# ---------------------------------------------------------------------------

class TestMCPAdminStatusResourceGating:

    def test_mcp_admin_status_resource_requires_guarded_tier(self):
        """admin/status resource should not appear when tier is 'open'."""
        uris = _get_resource_uris("open")
        admin_uris = [u for u in uris if "admin" in u]
        assert len(admin_uris) == 0, (
            f"Admin status resource should be hidden at open tier, found: {admin_uris}"
        )

    def test_mcp_admin_status_resource_available_at_guarded_tier(self):
        """admin/status resource should appear when tier is 'guarded'."""
        uris = _get_resource_uris("guarded")
        admin_uris = [u for u in uris if "admin" in u]
        assert len(admin_uris) == 1, (
            f"Admin status resource should be visible at guarded tier, found: {admin_uris}"
        )


# ---------------------------------------------------------------------------
# Test: low-risk resources remain available at open tier
# ---------------------------------------------------------------------------

class TestMCPLowRiskResourcesRemainAvailable:

    def test_mcp_collective_status_resource_remains_available_at_basic_tier(self):
        """collective/status is low-risk and should appear at open tier."""
        uris = _get_resource_uris("open")
        collective_uris = [u for u in uris if "collective" in u]
        assert len(collective_uris) >= 1, (
            f"Collective status resource should be visible at open tier, found: {collective_uris}"
        )

    def test_agent_state_remains_available_at_open_tier(self):
        """Agent state is basic telemetry and should appear at open tier."""
        uris = _get_resource_uris("open")
        state_uris = [u for u in uris if "/state" in u]
        assert len(state_uris) >= 1, (
            f"Agent state resource should be visible at open tier, found: {state_uris}"
        )

    def test_memory_summary_remains_available_at_open_tier(self):
        """Memory summary is a safe hybrid view and should appear at open tier."""
        uris = _get_resource_uris("open")
        summary_uris = [u for u in uris if "memory-summary" in u]
        assert len(summary_uris) >= 1, (
            f"Memory summary resource should be visible at open tier, found: {summary_uris}"
        )


# ---------------------------------------------------------------------------
# Test: tools and resources share the same tier logic
# ---------------------------------------------------------------------------

class TestMCPSharedTierLogic:

    def test_mcp_resource_and_tool_exposure_use_shared_tier_logic(self):
        """Both tool and resource gating use exposure_allows() from spine.py."""
        # Structural test: exposure_allows is the same function used by
        # get_exposed_operations and imported by mcp_server
        from torment_service.spine import exposure_allows as spine_fn
        from torment_service.mcp_server import exposure_allows as mcp_fn
        assert spine_fn is mcp_fn, (
            "mcp_server.exposure_allows should be the same object as spine.exposure_allows"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_mcp_resource_gating_tests():
    """Run all MCP resource gating tests."""
    tests = [
        # exposure_allows helper
        ("EA.1 open allows open", TestExposureAllows().test_open_allows_open),
        ("EA.2 open allows guarded", TestExposureAllows().test_open_allows_guarded),
        ("EA.3 guarded requires guarded", TestExposureAllows().test_guarded_requires_guarded),
        ("EA.4 guarded allows guarded", TestExposureAllows().test_guarded_allows_guarded),
        ("EA.5 guarded allows internal", TestExposureAllows().test_guarded_allows_internal),
        ("EA.6 internal requires internal", TestExposureAllows().test_internal_requires_internal),
        # provenance resource gating
        ("PRV.1 Provenance hidden at open", TestMCPProvenanceResourceGating().test_mcp_provenance_resource_requires_guarded_tier),
        ("PRV.2 Provenance visible at guarded", TestMCPProvenanceResourceGating().test_mcp_provenance_resource_available_at_guarded_tier),
        # admin/status resource gating
        ("ADM.1 Admin hidden at open", TestMCPAdminStatusResourceGating().test_mcp_admin_status_resource_requires_guarded_tier),
        ("ADM.2 Admin visible at guarded", TestMCPAdminStatusResourceGating().test_mcp_admin_status_resource_available_at_guarded_tier),
        # low-risk resources stay visible
        ("LOW.1 Collective status at open", TestMCPLowRiskResourcesRemainAvailable().test_mcp_collective_status_resource_remains_available_at_basic_tier),
        ("LOW.2 Agent state at open", TestMCPLowRiskResourcesRemainAvailable().test_agent_state_remains_available_at_open_tier),
        ("LOW.3 Memory summary at open", TestMCPLowRiskResourcesRemainAvailable().test_memory_summary_remains_available_at_open_tier),
        # shared tier logic
        ("SHR.1 Shared tier function", TestMCPSharedTierLogic().test_mcp_resource_and_tool_exposure_use_shared_tier_logic),
    ]

    passed = 0
    failed = 0
    print("\n--- MCP Resource Gating Tests ---")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception:
            print(f"  FAIL: {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_mcp_resource_gating_tests()
    print(f"\nMCP Resource Gating: {p} passed, {f} failed")
    if f > 0:
        exit(1)
