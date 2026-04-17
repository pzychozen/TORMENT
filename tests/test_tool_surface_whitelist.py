"""
Invariant 1 test: Memory is never exposed as open-ended search to
the internal agent's LLM.

Asserts that `torment_service.tool_registry.TOOL_REGISTRY` — the
single source of truth for tool families the internal agent's LLM
can see — does NOT contain any open-ended memory-search tool. Any
memory-adjacency must go through the closed expansion primitives
declared in R2 of the doctrine.

Also cross-checks that the MCP server surface
(`torment_service.mcp_server`) is NOT the source feeding the
internal agent's tool registry. Per doctrine R5, the MCP server is
a secondary external interface; its tools live under a different
contract.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 2 R2, R5
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 (invariant 1)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S3
"""
import re

import pytest

from torment_service.tool_registry import (
    CODE_EXEC,
    TOOL_REGISTRY,
    llm_visible_tool_names,
    is_registered,
)


# ---------------------------------------------------------------------------
# Forbidden names — anything that would admit open memory search
# ---------------------------------------------------------------------------

FORBIDDEN_NAMES = {
    # MCP-surface names that must not leak into internal-agent registry
    "torment_query_memory",
    "torment_ingest",
    "torment_reinforce",
    "torment_query_state",
    "torment_submit_task",
    "torment_tool_result_ingest",
    "torment_feedback",
    # Generic open-ended memory-search names
    "search_memory",
    "fetch_memory_by_id",
    "recall",
    "retrieve_memory",
    "memory_search",
    "query_memory",
    "get_memory",
}


# Allowed memory-adjacency set — the closed expansion primitives
# declared in doctrine R2. If any memory-adjacent name ever does
# enter the registry, it MUST be one of these.
ALLOWED_MEMORY_ADJACENT = {
    "trace",
    "deepen",
    "conflict_check",
    "continuity_expand",
}


# Pattern for anything that looks memory-adjacent by name.
_MEMORY_ADJACENCY_PATTERN = re.compile(
    r"memory|recall|retrieve|search|fetch_.*mem|query_mem",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Forbidden names are not in the registry
# ---------------------------------------------------------------------------


class TestForbiddenNamesNotInRegistry:
    """None of the open-memory-search names leak into the internal
    agent's tool registry."""

    @pytest.mark.parametrize("name", sorted(FORBIDDEN_NAMES))
    def test_forbidden_name_not_registered(self, name):
        assert not is_registered(name), (
            f"Forbidden name {name!r} is in TOOL_REGISTRY. "
            f"Invariant 1 violation: internal agent's LLM would "
            f"see an open-ended memory-search tool."
        )

    @pytest.mark.parametrize("name", sorted(FORBIDDEN_NAMES))
    def test_forbidden_name_not_in_llm_visible_list(self, name):
        visible = set(llm_visible_tool_names())
        assert name not in visible


# ---------------------------------------------------------------------------
# Any memory-adjacent name in the registry must be in the closed set
# ---------------------------------------------------------------------------


class TestMemoryAdjacentNamesAreClosedSet:
    """If a memory-adjacent name ever appears in the registry, it
    must be one of the declared closed expansion primitives."""

    def test_no_memory_adjacent_names_in_current_registry(self):
        """v0.1: the only family is code_exec, which is not
        memory-adjacent. If anyone adds a memory-adjacent family
        later without it being in the allowed set, this fails."""
        for name in llm_visible_tool_names():
            if _MEMORY_ADJACENCY_PATTERN.search(name):
                assert name in ALLOWED_MEMORY_ADJACENT, (
                    f"Memory-adjacent name {name!r} in registry but "
                    f"not in the declared closed set "
                    f"{sorted(ALLOWED_MEMORY_ADJACENT)}. "
                    f"Invariant 1 violation."
                )


# ---------------------------------------------------------------------------
# Positive assertions on the v0.1 registry state
# ---------------------------------------------------------------------------


class TestV01RegistryState:
    """Pins the v0.1 registry shape so a later refactor can't
    accidentally admit extra families without a test update."""

    def test_code_exec_is_registered(self):
        assert is_registered("code_exec")

    def test_code_exec_is_the_only_v0_1_family(self):
        """v0.1 scope: exactly one declared family. Changing this
        requires a doctrine amendment and should fail this test
        deliberately so the reviewer notices."""
        assert llm_visible_tool_names() == ["code_exec"]

    def test_code_exec_defaults_are_sandbox_bound(self):
        """Controller-side constraints are not LLM-fillable."""
        assert CODE_EXEC.defaults.get("scope") == "sandbox"
        assert CODE_EXEC.defaults.get("language") == "python"
        assert "timeout_seconds" in CODE_EXEC.defaults

    def test_code_exec_signature_has_single_code_parameter(self):
        """The LLM fills `code`; nothing else. No file paths, no
        URLs, no shell commands — just Python source."""
        params = CODE_EXEC.parameters
        properties = params.get("properties", {})
        assert set(properties.keys()) == {"code"}
        assert properties["code"]["type"] == "string"

    def test_registry_has_no_open_api_surface(self):
        """Each entry in TOOL_REGISTRY must be an explicit
        ToolSignature, not a class or callable that could accept
        arbitrary names."""
        for name, sig in TOOL_REGISTRY.items():
            assert hasattr(sig, "name"), (
                f"{name}: registry entry has no .name attribute; "
                f"not a ToolSignature"
            )
            assert sig.name == name
