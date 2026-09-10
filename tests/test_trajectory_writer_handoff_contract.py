"""Inert state-machine guardrails for the ratified trajectory handoff.

This is a test-local model of the v1.2 design contract.  It neither opens a
real root nor creates a coordinator, writer, receipt, selector transition, or
trajectory artifact.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

import pytest


class HandoffRefused(ValueError):
    """The inert model's fail-closed outcome."""


class Phase(StrEnum):
    LEGACY_AUTHORITATIVE = "LEGACY_AUTHORITATIVE"
    QUIESCING = "QUIESCING"
    LEGACY_QUIESCED = "LEGACY_QUIESCED"
    NATIVE_ADMITTING = "NATIVE_ADMITTING"
    NATIVE_AUTHORITATIVE = "NATIVE_AUTHORITATIVE"
    HANDOFF_COMPLETE = "HANDOFF_COMPLETE"


@dataclass(frozen=True)
class ScopeHandoff:
    scope: str
    phase: Phase = Phase.LEGACY_AUTHORITATIVE
    generation: int = 1
    legacy_generation: int = 1
    legacy_quiesced: bool = False
    ledger_settled: bool = True
    native_writer: str | None = None
    receipt: str | None = None


def _refuse_unless(value: bool, message: str) -> None:
    if not value:
        raise HandoffRefused(message)


def _begin_quiesce(state: ScopeHandoff) -> ScopeHandoff:
    _refuse_unless(state.phase is Phase.LEGACY_AUTHORITATIVE, "quiesce requires legacy authority")
    return replace(state, phase=Phase.QUIESCING)


def _fence_legacy(state: ScopeHandoff, *, fresh_freeze: bool) -> ScopeHandoff:
    _refuse_unless(state.phase is Phase.QUIESCING, "legacy fence requires quiescing")
    _refuse_unless(fresh_freeze and state.legacy_quiesced and state.ledger_settled, "legacy is not quiesced")
    return replace(state, phase=Phase.LEGACY_QUIESCED, generation=state.generation + 1)


def _begin_native_admission(state: ScopeHandoff) -> ScopeHandoff:
    _refuse_unless(state.phase is Phase.LEGACY_QUIESCED, "native admission requires legacy fence")
    return replace(state, phase=Phase.NATIVE_ADMITTING)


def _admit_native(state: ScopeHandoff, *, writer: str) -> ScopeHandoff:
    _refuse_unless(state.phase is Phase.NATIVE_ADMITTING, "native writer is not admissible")
    _refuse_unless(bool(writer), "native writer identity is required")
    _refuse_unless(state.native_writer is None, "second native writer is refused")
    return replace(
        state,
        phase=Phase.NATIVE_AUTHORITATIVE,
        generation=state.generation + 1,
        native_writer=writer,
    )


def _complete(state: ScopeHandoff, *, writer: str) -> ScopeHandoff:
    if state.phase is Phase.HANDOFF_COMPLETE:
        _refuse_unless(writer == state.native_writer, "conflicting replay")
        return state
    _refuse_unless(state.phase is Phase.NATIVE_AUTHORITATIVE, "completion requires native authority")
    _refuse_unless(writer == state.native_writer, "different native writer is refused")
    return replace(state, phase=Phase.HANDOFF_COMPLETE, receipt=f"receipt:{state.scope}:{writer}")


def _write_allowed(state: ScopeHandoff, *, family: str, generation: int, writer: str | None = None) -> bool:
    if family == "legacy":
        return state.phase is Phase.LEGACY_AUTHORITATIVE and generation == state.legacy_generation
    return (
        family == "native"
        and state.phase in {Phase.NATIVE_AUTHORITATIVE, Phase.HANDOFF_COMPLETE}
        and generation == state.generation
        and writer == state.native_writer
    )


def _recover_after_crash(state: ScopeHandoff) -> ScopeHandoff:
    """Recovery reads durable state; it never restores legacy authority."""
    return state


def _trajectory_eligible(scopes: tuple[ScopeHandoff, ...], *, selector_state: str) -> bool:
    if selector_state != "CUTOVER_PENDING" or not scopes:
        return False
    identities = {(scope.scope, scope.native_writer) for scope in scopes}
    return (
        len(identities) == len(scopes)
        and all(
            scope.phase is Phase.HANDOFF_COMPLETE
            and scope.receipt is not None
            and scope.native_writer is not None
            and _write_allowed(
                scope,
                family="native",
                generation=scope.generation,
                writer=scope.native_writer,
            )
            for scope in scopes
        )
    )


def _valid_complete(scope: str = "private:ws:agent") -> ScopeHandoff:
    state = ScopeHandoff(scope=scope)
    state = _begin_quiesce(state)
    state = replace(state, legacy_quiesced=True)
    state = _fence_legacy(state, fresh_freeze=True)
    state = _begin_native_admission(state)
    state = _admit_native(state, writer=f"native:{scope}")
    return _complete(state, writer=f"native:{scope}")


def test_valid_handoff_passes_in_required_order():
    state = _valid_complete()
    assert state.phase is Phase.HANDOFF_COMPLETE
    assert state.receipt is not None


def test_native_admission_before_quiescence_is_refused():
    with pytest.raises(HandoffRefused, match="legacy fence"):
        _begin_native_admission(ScopeHandoff(scope="private:ws:agent"))


def test_stale_legacy_write_after_fence_is_refused():
    state = _begin_quiesce(ScopeHandoff(scope="private:ws:agent"))
    state = _fence_legacy(replace(state, legacy_quiesced=True), fresh_freeze=True)
    assert _write_allowed(state, family="legacy", generation=1) is False


def test_second_native_writer_is_refused():
    state = _valid_complete()
    with pytest.raises(HandoffRefused, match="native writer is not admissible"):
        _admit_native(state, writer="native:other")


def test_exact_terminal_replay_is_idempotent():
    state = _valid_complete()
    assert _complete(state, writer=state.native_writer or "") == state


def test_conflicting_terminal_replay_is_refused():
    with pytest.raises(HandoffRefused, match="conflicting replay"):
        _complete(_valid_complete(), writer="native:other")


def test_partial_crash_recovery_keeps_exact_durable_stage_and_no_dual_writer():
    state = _begin_quiesce(ScopeHandoff(scope="private:ws:agent"))
    state = _fence_legacy(replace(state, legacy_quiesced=True), fresh_freeze=True)
    recovered = _recover_after_crash(state)
    assert recovered.phase is Phase.LEGACY_QUIESCED
    assert _write_allowed(recovered, family="legacy", generation=1) is False
    assert _write_allowed(recovered, family="native", generation=recovered.generation, writer="native:x") is False


def test_missing_scope_receipt_is_p7_ineligible():
    complete = _valid_complete("private:ws:agent")
    missing = replace(_valid_complete("shared:ws:domain"), receipt=None)
    assert _trajectory_eligible((complete, missing), selector_state="CUTOVER_PENDING") is False


def test_all_scope_receipts_complete_makes_trajectory_eligible():
    assert _trajectory_eligible(
        (_valid_complete("private:ws:agent"), _valid_complete("shared:ws:domain")),
        selector_state="CUTOVER_PENDING",
    ) is True


def test_selector_authority_stays_cutover_pending_throughout():
    assert _trajectory_eligible((_valid_complete(),), selector_state="NATIVE_ACTIVE") is False
    assert _trajectory_eligible((_valid_complete(),), selector_state="CUTOVER_PENDING") is True
