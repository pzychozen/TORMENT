from __future__ import annotations

from pathlib import Path

import pytest

import durable_evidence_authority_v0_3 as authority
import durable_evidence_durability_v0_3 as durability
import durable_evidence_primary_writer_v0_3 as writer
import durable_evidence_schema_v0_3 as schema
import durable_evidence_windows_adapter_v0_3 as windows_adapter


EXECUTION_IDENTITY = "8" * 64
SCIENTIFIC_AUTHORITY = "9" * 64


class ConfirmedSyntheticAdapter(windows_adapter.WindowsDurabilityAdapter):
    def sync_directory_entry(self, directory_path: str):
        return windows_adapter.DirectoryDurabilityResult(
            windows_adapter.DIRECTORY_DURABILITY_CONFIRMED,
            "synthetic authority-state test double",
        )


def _context():
    return authority.SyntheticAuthorityContext()


def _invocation(context=None):
    return authority.SyntheticProtectedInvocation(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        context=context or _context(),
    )


def _write_stored_record(path: Path, stored_record: dict, *, confirmed: bool = True):
    adapter = ConfirmedSyntheticAdapter() if confirmed else None
    return writer.write_stored_record_object(
        path,
        stored_record,
        durability_adapter=adapter,
    )


def _ledger(record_writes=()):
    return durability.VerifiedDurabilityEvidence.from_immutable_write_results(
        record_writes=record_writes
    )


def test_live_pre_begin_state_is_not_attempted(tmp_path):
    invocation = _invocation()
    assert invocation.live_state == authority.NOT_ATTEMPTED
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    assert result.state == authority.NOT_ATTEMPTED
    assert result.scientific_state == authority.AUTHORITY_NOT_ATTEMPTED
    assert result.reusable is True


def test_same_object_second_begin_denied():
    invocation = _invocation()
    begin = invocation.begin()
    assert begin.state == authority.CONSUMED
    assert begin.reuse_permission_consumed is True
    assert invocation.reuse_permission_consumed is True
    with pytest.raises(authority.AuthorityReuseDenied):
        invocation.begin()


def test_same_context_second_object_begin_denied():
    context = _context()
    first = _invocation(context)
    second = _invocation(context)
    first.begin()
    with pytest.raises(authority.AuthorityReuseDenied):
        second.begin()


def test_exception_after_begin_does_not_restore_reuse():
    context = _context()
    invocation = _invocation(context)
    with pytest.raises(RuntimeError):
        invocation.begin()
        raise RuntimeError("synthetic post-begin failure")
    with pytest.raises(authority.AuthorityReuseDenied):
        _invocation(context).begin()


def test_missing_genesis_does_not_restore_live_reuse(tmp_path):
    context = _context()
    _invocation(context).begin()
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE
    assert result.reusable is False
    with pytest.raises(authority.AuthorityReuseDenied):
        _invocation(context).begin()


def test_valid_durable_genesis_replays_as_consumed(tmp_path):
    evidence = authority.write_authority_consumed_record(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="0" * 32,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=_ledger(record_writes=(evidence,)),
        invocation_window_observed=True,
    )
    assert result.state == authority.CONSUMED
    assert result.scientific_state == authority.AUTHORITY_CONSUMED
    assert result.reusable is False


def test_missing_genesis_after_ambiguous_death_replays_as_indeterminate(tmp_path):
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE
    assert result.scientific_state == authority.AUTHORITY_ATTEMPT_STATE_INDETERMINATE
    assert result.reusable is False


def test_ambiguity_alone_never_becomes_attempt_failed(tmp_path):
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        invocation_window_observed=True,
    )
    assert result.state != authority.ATTEMPT_FAILED


def test_valid_durable_failure_evidence_replays_as_attempt_failed(tmp_path):
    evidence = authority.write_authority_consumption_failure_record(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="1" * 32,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=_ledger(record_writes=(evidence,)),
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_FAILED
    assert result.scientific_state == (
        authority.AUTHORITY_CONSUMPTION_ATTEMPT_FAILED
    )
    assert result.reusable is False


def test_invalid_failure_evidence_does_not_prove_attempt_failed(tmp_path):
    logical = schema.build_scientific_logical_record(
        record_kind="SCIENTIFIC_TERMINAL_STATUS",
        sequence_number=0,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        predecessor_logical_record_sha256=schema.GENESIS_PREDECESSOR_LOGICAL_RECORD_SHA256,
        payload={
            "terminal_classification": "UNRELATED_FAILURE",
            "exit_code": authority.AUTHORITY_FAILURE_EXIT_CODE,
        },
    )
    stored = schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="2" * 32,
    )
    write_result = _write_stored_record(tmp_path, stored)
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=_ledger(record_writes=((stored, write_result),)),
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE


def test_post_event_missing_evidence_never_silently_permits_reuse(tmp_path):
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        invocation_window_observed=True,
    )
    assert result.reusable is False


def test_cross_authorization_evidence_is_rejected(tmp_path):
    evidence = authority.write_authority_consumed_record(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity="a" * 64,
        writer_attempt_identity="3" * 32,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=_ledger(record_writes=(evidence,)),
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE
    assert result.reusable is False


def test_cross_execution_evidence_is_rejected(tmp_path):
    evidence = authority.write_authority_consumed_record(
        tmp_path,
        execution_identity="b" * 64,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="4" * 32,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=_ledger(record_writes=(evidence,)),
        invocation_window_observed=True,
    )
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE
    assert result.reusable is False


def test_authority_replay_is_input_order_independent(tmp_path):
    logical = authority.build_authority_consumed_logical_record(
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
    )
    stored_a = schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="5" * 32,
    )
    stored_b = schema.build_stored_record_object(
        logical_record=logical,
        writer_identity=writer.PRIMARY_WRITER_IDENTITY,
        writer_attempt_identity="6" * 32,
    )
    write_b = _write_stored_record(tmp_path, stored_b)
    write_a = _write_stored_record(tmp_path, stored_a)
    ledger = _ledger(
        record_writes=((stored_b, write_b), (stored_a, write_a))
    )
    first = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=ledger,
        invocation_window_observed=True,
    )
    second = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=ledger,
        invocation_window_observed=True,
    )
    assert first.state == second.state == authority.CONSUMED


def test_raw_hash_iterable_is_not_accepted_as_durability_evidence(tmp_path):
    with pytest.raises(authority.AuthorityEvidenceError):
        authority.replay_scientific_authority_state(
            tmp_path,
            execution_identity=EXECUTION_IDENTITY,
            scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
            durability_evidence={"f" * 64},
            invocation_window_observed=True,
        )


def test_unbacked_durability_assertion_cannot_prove_consumed(tmp_path):
    evidence = authority.write_authority_consumed_record(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="7" * 32,
        durability_adapter=ConfirmedSyntheticAdapter(),
    )
    result = authority.replay_scientific_authority_state(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        durability_evidence=durability.VerifiedDurabilityEvidence.empty(),
        invocation_window_observed=True,
    )
    assert evidence.stored_record_object["stored_object_sha256"]
    assert result.state == authority.ATTEMPT_STATE_INDETERMINATE


def test_default_fail_closed_adapter_remains_unconfirmed_authority(tmp_path):
    evidence = authority.write_authority_consumed_record(
        tmp_path,
        execution_identity=EXECUTION_IDENTITY,
        scientific_execution_authorization_identity=SCIENTIFIC_AUTHORITY,
        writer_attempt_identity="8" * 32,
    )
    with pytest.raises(durability.DurabilityEvidenceError):
        _ledger(record_writes=(evidence,))


def test_no_automatic_retry_surface_exists():
    exported = {
        name.lower()
        for name in dir(authority)
        if not name.startswith("_")
    }
    assert not any("retry" in name for name in exported)
