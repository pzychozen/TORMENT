# roles — bounded role executors for the TORMENT Agent Spine (v0.1)
#
# Roles are deterministic transforms, not autonomous personas.
# They receive a TaskPacket + aperture context + prior role outputs
# and emit structured RoleOutput.  No external model calls in v0.1.
#
# Execution order (strict, sequential):
#   1. Interpreter
#   2. Engineer
#   3. Skeptic
#   4. Reintegration membrane
#   5. Archivist
#
# See AGENT_SPINE_PLAN.md §7 for the design rationale.

from .base import RoleBase
from .interpreter import Interpreter
from .engineer import Engineer
from .skeptic import Skeptic
from .archivist import Archivist

# Canonical execution order — used by the pipeline coordinator
ROLE_EXECUTION_ORDER = ["interpreter", "engineer", "skeptic", "archivist"]

# Role registry for lookup by name
ROLE_REGISTRY = {
    "interpreter": Interpreter,
    "engineer": Engineer,
    "skeptic": Skeptic,
    "archivist": Archivist,
}

__all__ = [
    "RoleBase",
    "Interpreter",
    "Engineer",
    "Skeptic",
    "Archivist",
    "ROLE_EXECUTION_ORDER",
    "ROLE_REGISTRY",
]
