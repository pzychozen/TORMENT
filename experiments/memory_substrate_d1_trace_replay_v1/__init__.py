"""7G5D1's experiment-local legacy-to-native replay instrument.

Nothing in this package is imported by the service.  It deliberately contains
no backend selector, deployment-state writer, or production fallback.
"""

from .protocol import (
    D1_PROTOCOL_VERSION,
    D1_RUNTIME_FLAG_NAMES,
    FORMAL_ADMINISTRATION_AUTHORIZED,
    FROZEN_TOLERANCES,
    D1ProtocolError,
)

__all__ = [
    "D1_PROTOCOL_VERSION",
    "D1_RUNTIME_FLAG_NAMES",
    "FORMAL_ADMINISTRATION_AUTHORIZED",
    "FROZEN_TOLERANCES",
    "D1ProtocolError",
]
