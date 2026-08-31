"""Operator-facing, pre-administration-only helpers for the D1 harness.

This module deliberately has no command that starts formal replay.  The only
supported state here is frozen construction/preflight evidence.
"""
from __future__ import annotations

from pathlib import Path

from .fixture_qualification import FrozenFixtureSet
from .protocol import D1ProtocolError, protocol_document_sha256, refuse_formal_administration


def seal_fixture_set(*, protocol_document: str | Path, fixtures: FrozenFixtureSet):
    """Bind qualified L0-specific fixture facts to the checked-in protocol bytes."""
    document_hash = protocol_document_sha256(protocol_document)
    if fixtures.protocol_sha256 != document_hash:
        raise D1ProtocolError("fixture evidence was qualified against different protocol bytes")
    return fixtures.freeze_inputs()


def run_formal_administration(*args, **kwargs):
    """Refuse the deliberately deferred D1 administration step."""
    refuse_formal_administration(None)
