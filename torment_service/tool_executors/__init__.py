"""Tool executor implementations for the TORMENT agent.

Each executor implements the `ToolExecutor` protocol declared in
`torment_service.agent_loop`. The `AgentRunner` receives at most one
executor at construction; behavior packs' action contracts permit
exactly one tool family at Phase 5 narrowing (doctrine invariant 2).

v0.1.0b: subprocess-based code_exec executor.
Future: additional executor implementations (web_fetch adapter,
read_file adapter, etc.) go alongside `subprocess_python.py`.
"""
from .subprocess_python import SubprocessPythonExecutor

__all__ = ["SubprocessPythonExecutor"]
