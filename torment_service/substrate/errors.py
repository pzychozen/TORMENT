"""Small explicit exception hierarchy for the native substrate boundary."""


class SubstrateError(Exception):
    """Base error for substrate-owned failures."""


class SubstrateRuntimeIneligible(SubstrateError):
    """Raised when Python's loaded SQLite runtime is not admissible."""


class SubstrateConfigurationError(SubstrateError):
    """Raised for invalid substrate configuration or caller input."""


class SubstrateConnectionError(SubstrateError):
    """Raised when a qualified temporary connection cannot be configured."""


class SubstrateSchemaCompatibilityError(SubstrateError):
    """Reserved for the schema-compatibility boundary introduced in Phase 7B."""


class SubstrateIdentifierError(SubstrateError):
    """Raised when a native substrate identifier is malformed."""


class CanonicalIntentError(SubstrateError):
    """Raised when a value cannot participate in TMS-INTENT-1 encoding."""


class SubstrateIdempotencyConflict(SubstrateError):
    """Raised when a retry identity is reused with different canonical intent."""


class SubstrateRevisionConflict(SubstrateError):
    """Raised when an object no longer has the expected current revision."""


class SubstrateObjectNotFound(SubstrateError):
    """Raised when a native object identity has no durable carrier row."""


class SubstrateInvariantViolation(SubstrateError):
    """Raised when a current-slice helper-owned invariant is not satisfied."""
