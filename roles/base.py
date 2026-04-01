# roles/base.py
"""
RoleBase — abstract base class for all cognition roles.

v0.1 roles are bounded deterministic transforms:
  Input:  TaskPacket + MemoryContext + prior RoleOutputs
  Output: RoleOutput (with mandatory provenance)

No external model calls. No side effects except structured output emission.
LLM-backed executors may be introduced later behind this same interface.

See AGENT_SPINE_PLAN.md §7 for the design rationale.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from cognition.task_models import TaskPacket
from cognition.apertures import MemoryContext
from schemas.role_output import RoleOutput
from schemas.provenance import Provenance


class RoleBase(ABC):
    """Abstract base for all v0.1 cognition roles.

    Subclasses must implement:
        name      — class-level string (e.g. "interpreter")
        execute() — deterministic transform producing a RoleOutput
    """

    # Subclasses MUST override this
    name: str = ""

    def run(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        """Public entry point — calls execute() and attaches provenance.

        This wrapper ensures every role output has valid provenance
        (Invariant B: mandatory provenance).
        """
        output = self.execute(task, memory_context, prior_outputs)

        # Enforce provenance — if the role forgot, attach one
        if output.provenance is None:
            output.provenance = Provenance.from_role(
                role_name=self.name,
                task_id=task.task_id,
                confidence=output.confidence,
            )

        return output

    @abstractmethod
    def execute(
        self,
        task: TaskPacket,
        memory_context: MemoryContext,
        prior_outputs: List[RoleOutput],
    ) -> RoleOutput:
        """Produce a RoleOutput from the given inputs.

        Implementations MUST:
          - Return a valid RoleOutput with role_name = self.name
          - Be deterministic given the same inputs
          - Not make external calls (network, LLM, filesystem)
          - Not mutate task, memory_context, or prior_outputs

        Implementations SHOULD:
          - Attach provenance via Provenance.from_role()
          - Set confidence < 1.0 when uncertain
          - Populate uncertainties and contradictions fields when relevant
        """
