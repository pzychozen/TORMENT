"""Quarantined, test-only Phase-13 v1a qualification instrument.

Nothing in this package is imported by production Brainvision.  Importing it
only exposes inert manifest, evidence, preflight, and runner mechanics; it
never creates a manager, observation, sink, durable artifact, or result.
"""

__all__: tuple[str, ...] = ()
