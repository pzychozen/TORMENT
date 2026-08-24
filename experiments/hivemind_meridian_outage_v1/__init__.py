"""Frozen, offline Meridian Outage experiment harness.

This package is deliberately outside production runtime wiring.  It prepares
deterministic experiment evidence and mock-only dry runs; it does not execute a
live model experiment by import or test collection.
"""

from .spec import EXPERIMENT_VERSION, FROZEN_BASELINE_COMMIT

__all__ = ["EXPERIMENT_VERSION", "FROZEN_BASELINE_COMMIT"]
