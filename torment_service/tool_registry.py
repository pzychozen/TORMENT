# torment_service/tool_registry.py
"""
TORMENT internal-agent tool registry.

Declares the set of tool families that the internal agent may be
granted through a behavior pack's action contract. Every family has
a SINGLE, well-defined signature — no alternatives are ever visible
to the LLM (doctrine invariant 2).

This registry is SEPARATE from the MCP server's tool surface
(`torment_service.mcp_server`). Per doctrine R5, the MCP server is
a secondary external interface; its tool set (`torment_query_memory`,
etc.) is not visible to the internal agent. Invariant 1 (memory
never exposed as open-ended search to the internal agent's LLM) is
enforced here: the registry contains no open-ended memory-search
tool. Adding one would require amending R2 of the doctrine.

v0.1 scope (S3):
    - One declared family: code_exec (sandboxed Python).
    - Stub executor is the v0.1/S1 default — no real subprocess.
    - Hardened subprocess sandboxing is deferred to v0.1.0b.

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 9 invariants 1, 2
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 5 (behavior pack
      action contract)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md S3
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# ToolSignature — declared family shape
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolSignature:
    """Immutable declaration of a tool family's LLM-visible shape.

    The signature is what the LLM sees when the behavior pack's
    action contract permits this family at Phase 5 narrowing. It is
    THE SINGLE signature — there are no alternatives. The LLM fills
    parameters; it never chooses between signatures.

    `defaults` carries constraints that always apply when this family
    is invoked (language, sandbox scope, timeout). Those values are
    not LLM-fillable; they are controller/pack-decided.
    """
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)

    def as_llm_tool_spec(self) -> Dict[str, Any]:
        """Render the signature as a tools=[{...}] dict for LLM calls.

        Shape follows the OpenAI/Anthropic tools-array convention.
        Consumers that need a different shape should adapt it at the
        integration layer, not at the registry layer.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


# ---------------------------------------------------------------------------
# ActionContract — pack-level declaration of permitted families
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionContract:
    """Declaration of which tool families a given context (behavior
    pack, mode override, etc.) is permitted to invoke at Phase 5.

    v0.1: a frozen set of family names. The runner checks that a
    USE_TOOL intent can be narrowed to exactly one permitted family
    via this contract.

    Composition rules and per-pack overlays are S4 / v0.2 territory.
    For S3 in isolation, a bare ActionContract can be constructed
    directly by callers and passed to `AgentRunner` at construction;
    the default contract is empty, which causes USE_TOOL to fall
    through to the fallback chain.
    """
    allowed_tool_families: frozenset = frozenset()


# Convenience constants.
EMPTY_CONTRACT = ActionContract()  # permits no tools — USE_TOOL falls through


# ---------------------------------------------------------------------------
# Declared families
# ---------------------------------------------------------------------------


CODE_EXEC = ToolSignature(
    name="code_exec",
    description=(
        "Execute a short Python snippet in a sandboxed environment. "
        "Use for calculations, data transforms, or deterministic logic "
        "when an answer requires a computation you cannot do from "
        "aperture content alone. Do not use for I/O, network access, "
        "or long-running work."
    ),
    parameters={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": (
                    "Python 3 source to execute. Must be self-contained; "
                    "uses only the Python standard library."
                ),
            },
        },
        "required": ["code"],
    },
    defaults={
        "language": "python",
        "scope": "sandbox",
        "timeout_seconds": 10,
    },
)


# The registry: name → signature. Every entry must be a first-class
# declared family. Nothing dynamic. Adding a family is a doctrinal
# change that should be reflected in the slice-plan or a subsequent
# doctrine amendment.
TOOL_REGISTRY: Dict[str, ToolSignature] = {
    CODE_EXEC.name: CODE_EXEC,
}


# ---------------------------------------------------------------------------
# Registry accessors
# ---------------------------------------------------------------------------


def get_tool_signature(name: str) -> Optional[ToolSignature]:
    """Look up a tool signature by family name."""
    return TOOL_REGISTRY.get(name)


def llm_visible_tool_names() -> List[str]:
    """Return every name the internal agent's LLM could ever see as
    a tool family.

    Used by the invariant 1 test (`tests/test_tool_surface_whitelist.py`)
    to prove no open memory-search tool is exposed, and by anyone
    writing a behavior pack's action contract who wants to enumerate
    the approved family universe.
    """
    return list(TOOL_REGISTRY.keys())


def is_registered(name: str) -> bool:
    """True if `name` is a declared tool family."""
    return name in TOOL_REGISTRY
