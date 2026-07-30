from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import sys
from typing import Any, Callable, Mapping

import blocker2_r4_authority_b_evidence_publisher_v0_1 as publisher
import blocker2_r4_ordered_directory_creation_helper_v0_1 as authority_a
import durable_evidence_windows_adapter_v0_3 as windows_adapter


VERSION = "v0.1"
ORCHESTRATOR_IDENTITY = "blocker2_r4_ab_orchestrator_v0_1"
CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT = (
    "CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT"
)

FAILURE_PHASE_OPERATOR_ASSERTION_VALIDATION = "OPERATOR_ASSERTION_VALIDATION"
FAILURE_PHASE_TEST_PATH_MODEL_VALIDATION = "TEST_PATH_MODEL_VALIDATION"
FAILURE_PHASE_AUTHORITY_A_RESULT = "AUTHORITY_A_RESULT"
FAILURE_PHASE_AUTHORITY_B_RECORD_CONSTRUCTION = "AUTHORITY_B_RECORD_CONSTRUCTION"


@dataclass(frozen=True)
class OperatorAssertions:
    window_open: bool
    authority_a_active: bool
    authority_b_active: bool
    authority_c_inactive: bool
    authority_d_inactive: bool
    authority_e_inactive: bool
    formal_hold_active: bool
    blocker_2_open: bool
    blocker_4_inactive: bool

    def as_authority_a_assertions(self) -> authority_a.AuthorityAssertions:
        return authority_a.AuthorityAssertions(
            window_open=self.window_open,
            authority_a_active=self.authority_a_active,
            authority_b_active=self.authority_b_active,
            authority_c_active=not self.authority_c_inactive,
            authority_d_active=not self.authority_d_inactive,
            authority_e_active=not self.authority_e_inactive,
        )

    def as_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class R4AuthorityABOrchestrationResult:
    classification: str
    accepted: bool
    detail: str
    accepted_invocation_head: str
    classification_kind: str | None = None
    terminal: bool | None = None
    sequence_terminal: bool | None = None
    contact_started: bool | None = None
    opportunity_consumed: bool | None = None
    mutation_succeeded_count: int | None = None
    failure_phase: str | None = None
    committed_detail_label: str | None = None
    derived_subreason: str | None = None
    authority_a_result: dict[str, Any] | None = None
    authority_b_result: dict[str, Any] | None = None
    whole_record_byte_count: int | None = None
    whole_record_sha256: str | None = None
    operator_assertions: dict[str, bool] | None = None
    operator_assertions_do_not_activate_authority: bool = True
    machine_verified_governance_assertions: bool = False
    authority_c_active: bool = False
    authority_d_active: bool = False
    authority_e_active: bool = False
    exception: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return _strip_none(asdict(self))


def execute_authority_a_and_b(
    *,
    operator_assertions: OperatorAssertions | Mapping[str, bool],
    accepted_invocation_head: str,
    repository_root: str | Path = ".",
    path_model: authority_a.PathModel = authority_a.GOVERNED_PATH_MODEL,
    allow_test_path_model: bool = False,
    repository_reader: Callable[[], authority_a.RepositoryState] | None = None,
    native_adapter: Any = None,
    creation_primitive: Callable[[str], None] | None = None,
    durability_adapter: Any = None,
    corrected_governance_chain_identities: Mapping[str, object] | None = None,
    commit_free_window_declaration: Mapping[str, object] | None = None,
    source_identities: Mapping[str, object] | None = None,
    helper_executor: Callable[..., Any] | None = None,
    file_opener: Callable[[str, str], Any] | None = None,
    fsync_callable: Callable[[int], None] = os.fsync,
    read_bytes_function: Callable[[str], bytes] | None = None,
) -> R4AuthorityABOrchestrationResult:
    assertions = _coerce_operator_assertions(operator_assertions)
    assertion_failure = _operator_assertion_failure(assertions)
    if assertion_failure is not None:
        detail, derived_subreason = assertion_failure
        return _pre_contact_abort_result(
            detail,
            accepted_invocation_head,
            operator_assertions=assertions,
            failure_phase=FAILURE_PHASE_OPERATOR_ASSERTION_VALIDATION,
            derived_subreason=derived_subreason,
        )
    test_path_failure = _test_path_model_failure(path_model, allow_test_path_model)
    if test_path_failure is not None:
        detail, derived_subreason = test_path_failure
        return _pre_contact_abort_result(
            detail,
            accepted_invocation_head,
            operator_assertions=assertions,
            failure_phase=FAILURE_PHASE_TEST_PATH_MODEL_VALIDATION,
            derived_subreason=derived_subreason,
        )

    authority = assertions.as_authority_a_assertions()
    helper_call = helper_executor or authority_a.execute_ordered_directory_creation
    try:
        helper_result = helper_call(
            authority=authority,
            accepted_invocation_head=accepted_invocation_head,
            path_model=path_model,
            repository_reader=repository_reader,
            native_adapter=native_adapter,
            creation_primitive=creation_primitive,
            allow_test_path_model=allow_test_path_model,
            repository_root=repository_root,
        )
    except Exception as exc:
        return _result(
            publisher.AUTHORITY_A_PARTIAL,
            False,
            "Authority-A helper raised an exception",
            accepted_invocation_head,
            operator_assertions=assertions,
            exception=_exception_dict(exc),
        )

    helper_payload = _plain_helper_result(helper_result)
    if getattr(helper_result, "classification", None) != (
        authority_a.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    ):
        classification = getattr(
            helper_result,
            "classification",
            publisher.AUTHORITY_A_PARTIAL,
        )
        return _result(
            classification,
            False,
            _helper_failure_detail(helper_result),
            accepted_invocation_head,
            authority_a_result=helper_payload,
            operator_assertions=assertions,
            failure_phase=FAILURE_PHASE_AUTHORITY_A_RESULT,
            **_helper_classification_metadata(helper_result),
        )

    governance_identities = corrected_governance_chain_identities or {
        "fresh_accepted_invocation_head": accepted_invocation_head,
        "blocker": "BLOCKER-2",
        "stage": "Brainvision Stage S3B v0.3 R4",
    }
    window_declaration = commit_free_window_declaration or {
        "corrected_commit_free_window": "OPERATOR_ASSERTED_OPEN_FOR_INVOCATION",
        "machine_verified": False,
        "assertion_is_not_authority_activation": True,
    }
    sources = source_identities or _default_source_identities()
    try:
        record = publisher.build_path_creation_evidence_record(
            helper_result,
            corrected_governance_chain_identities=governance_identities,
            accepted_invocation_head=accepted_invocation_head,
            commit_free_window_declaration=window_declaration,
            authority_assertions=authority,
            path_model=path_model,
            source_identities=sources,
        )
        canonical_bytes = publisher.canonical_record_bytes(record)
    except (publisher.R4RecordConstructionError, publisher.R4CanonicalizationError) as exc:
        if _authority_a_completed_three_mutations(helper_result):
            return _result(
                publisher.AUTHORITY_B_RECORD_UNPUBLISHED,
                False,
                "Authority-B record construction failed",
                accepted_invocation_head,
                authority_a_result=helper_payload,
                operator_assertions=assertions,
                exception=_exception_dict(exc),
                classification_kind=authority_a.CLASSIFICATION_COMMITTED_TERMINAL,
                terminal=True,
                sequence_terminal=True,
                contact_started=True,
                opportunity_consumed=True,
                mutation_succeeded_count=3,
                failure_phase=FAILURE_PHASE_AUTHORITY_B_RECORD_CONSTRUCTION,
                committed_detail_label=publisher.AUTHORITY_B_RECORD_UNPUBLISHED,
                derived_subreason=type(exc).__name__,
            )
        return _result(
            getattr(
                helper_result,
                "classification",
                authority_a.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION,
            ),
            False,
            "Authority-A result failed publication prerequisites",
            accepted_invocation_head,
            authority_a_result=helper_payload,
            operator_assertions=assertions,
            exception=_exception_dict(exc),
            failure_phase=FAILURE_PHASE_AUTHORITY_A_RESULT,
            **_helper_classification_metadata(helper_result),
        )

    publication = publisher.publish_record_create_new(
        raw_record_path=path_model.evidence_record_path,
        canonical_bytes=canonical_bytes,
        durability_adapter=durability_adapter,
        native_adapter=native_adapter,
        expected_raw_record_path=path_model.evidence_record_path,
        allow_test_path_model=allow_test_path_model,
        file_opener=file_opener,
        fsync_callable=fsync_callable,
    )
    if not publication.accepted_for_validation:
        return _result(
            publication.classification,
            False,
            publication.detail,
            accepted_invocation_head,
            authority_a_result=helper_payload,
            authority_b_result=publication.as_dict(),
            operator_assertions=assertions,
        )

    acceptance = publisher.accept_authority_b_evidence(
        publication_result=publication,
        raw_record_path=path_model.evidence_record_path,
        expected_canonical_bytes=canonical_bytes,
        expected_helper_body_identity=helper_result.body_identity,
        expected_accepted_invocation_head=accepted_invocation_head,
        native_adapter=native_adapter,
        path_model=path_model,
        expected_raw_record_path=path_model.evidence_record_path,
        allow_test_path_model=allow_test_path_model,
        read_bytes_function=read_bytes_function,
    )
    return _result(
        acceptance.classification,
        acceptance.accepted,
        acceptance.detail,
        accepted_invocation_head,
        authority_a_result=helper_payload,
        authority_b_result=acceptance.as_dict(),
        whole_record_byte_count=acceptance.whole_record_byte_count,
        whole_record_sha256=acceptance.whole_record_sha256,
        operator_assertions=assertions,
    )


def main(
    argv: list[str] | None = None,
    *,
    execute: Callable[..., R4AuthorityABOrchestrationResult] = execute_authority_a_and_b,
    stdout: Any = None,
) -> int:
    parser = _argument_parser()
    args = parser.parse_args(argv)
    output = stdout if stdout is not None else sys.stdout
    assertions = OperatorAssertions(
        window_open=args.operator_assert_window_open,
        authority_a_active=args.operator_assert_authority_a_active,
        authority_b_active=args.operator_assert_authority_b_active,
        authority_c_inactive=args.operator_assert_authority_c_inactive,
        authority_d_inactive=args.operator_assert_authority_d_inactive,
        authority_e_inactive=args.operator_assert_authority_e_inactive,
        formal_hold_active=args.operator_assert_formal_hold_active,
        blocker_2_open=args.operator_assert_blocker_2_open,
        blocker_4_inactive=args.operator_assert_blocker_4_inactive,
    )
    result = execute(
        operator_assertions=assertions,
        accepted_invocation_head=args.accepted_invocation_head,
        repository_root=Path(__file__).resolve().parents[2],
        path_model=authority_a.GOVERNED_PATH_MODEL,
        allow_test_path_model=False,
    )
    payload = result.as_dict()
    payload["cli_fixed_path_binding"] = True
    payload["operator_assertions_do_not_activate_authority"] = True
    output.write(publisher.canonical_record_bytes(payload).decode("utf-8"))
    return 0 if result.accepted else 1


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TORMENT Brainvision BLOCKER-2 R4 Authority-A/B orchestrator"
    )
    parser.add_argument("--accepted-invocation-head", required=True)
    parser.add_argument("--operator-assert-window-open", action="store_true", required=True)
    parser.add_argument(
        "--operator-assert-authority-a-active",
        action="store_true",
        required=True,
    )
    parser.add_argument(
        "--operator-assert-authority-b-active",
        action="store_true",
        required=True,
    )
    parser.add_argument(
        "--operator-assert-authority-c-inactive",
        action="store_true",
        required=True,
    )
    parser.add_argument(
        "--operator-assert-authority-d-inactive",
        action="store_true",
        required=True,
    )
    parser.add_argument(
        "--operator-assert-authority-e-inactive",
        action="store_true",
        required=True,
    )
    parser.add_argument(
        "--operator-assert-formal-hold-active",
        action="store_true",
        required=True,
    )
    parser.add_argument("--operator-assert-blocker-2-open", action="store_true", required=True)
    parser.add_argument(
        "--operator-assert-blocker-4-inactive",
        action="store_true",
        required=True,
    )
    return parser


def _coerce_operator_assertions(
    value: OperatorAssertions | Mapping[str, bool],
) -> OperatorAssertions:
    if isinstance(value, OperatorAssertions):
        return value
    return OperatorAssertions(
        window_open=bool(value.get("window_open")),
        authority_a_active=bool(value.get("authority_a_active")),
        authority_b_active=bool(value.get("authority_b_active")),
        authority_c_inactive=bool(value.get("authority_c_inactive")),
        authority_d_inactive=bool(value.get("authority_d_inactive")),
        authority_e_inactive=bool(value.get("authority_e_inactive")),
        formal_hold_active=bool(value.get("formal_hold_active")),
        blocker_2_open=bool(value.get("blocker_2_open")),
        blocker_4_inactive=bool(value.get("blocker_4_inactive")),
    )


def _operator_assertion_failure(assertions: OperatorAssertions) -> tuple[str, str] | None:
    for key, value in assertions.as_dict().items():
        if value is not True:
            return (
                "operator assertion not supplied or false: %s" % key,
                "operator_assertion_false_%s" % key,
            )
    return None


def _test_path_model_failure(
    path_model: authority_a.PathModel,
    allow_test_path_model: bool,
) -> tuple[str, str] | None:
    if not allow_test_path_model:
        return None
    governed_prefix = publisher.GOVERNED_PREFIX.casefold()
    for raw_path in (
        path_model.required_root,
        *path_model.components,
        path_model.evidence_record_path,
        path_model.canonical_input_path,
    ):
        if raw_path.casefold().startswith(governed_prefix):
            return (
                "test path model targets governed path",
                "governed_path_forbidden_in_test_mode",
            )
    return None


def _default_source_identities() -> dict[str, Any]:
    return {
        "authority_a_helper": _source_identity(authority_a.__file__),
        "authority_b_publisher": _source_identity(publisher.__file__),
        "authority_ab_orchestrator": _source_identity(__file__),
        "windows_durability_adapter": _source_identity(windows_adapter.__file__),
    }


def _source_identity(path_text: str | None) -> dict[str, Any]:
    if path_text is None:
        return {"path": "UNKNOWN", "sha256": "UNKNOWN", "byte_count": 0}
    path = Path(path_text)
    payload = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_count": len(payload),
    }


def _plain_helper_result(helper_result: Any) -> dict[str, Any]:
    return {
        "classification": getattr(helper_result, "classification", None),
        "classification_kind": getattr(helper_result, "classification_kind", None),
        "terminal": getattr(helper_result, "terminal", None),
        "committed_detail_label": getattr(helper_result, "committed_detail_label", None),
        "derived_subreason": getattr(helper_result, "derived_subreason", None),
        "authority_active": getattr(helper_result, "authority_active", None),
        "contact_started": getattr(helper_result, "contact_started", None),
        "opportunity_consumed": getattr(helper_result, "opportunity_consumed", None),
        "mutation_succeeded_count": getattr(helper_result, "mutation_succeeded_count", None),
        "sequence_terminal": getattr(helper_result, "sequence_terminal", None),
        "evidence_body": getattr(helper_result, "evidence_body", None),
        "body_identity": getattr(helper_result, "body_identity", None),
        "required_authority_gate_satisfied": getattr(
            helper_result, "required_authority_gate_satisfied", None
        ),
        "execution_mode": getattr(helper_result, "execution_mode", None),
    }


def _pre_contact_abort_result(
    detail: str,
    accepted_invocation_head: str,
    *,
    operator_assertions: OperatorAssertions,
    failure_phase: str,
    derived_subreason: str,
) -> R4AuthorityABOrchestrationResult:
    return _result(
        CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT,
        False,
        detail,
        accepted_invocation_head,
        operator_assertions=operator_assertions,
        classification_kind=authority_a.CLASSIFICATION_DERIVED_NON_TERMINAL,
        terminal=False,
        sequence_terminal=False,
        contact_started=False,
        opportunity_consumed=False,
        mutation_succeeded_count=0,
        failure_phase=failure_phase,
        derived_subreason=derived_subreason,
    )


def _helper_classification_metadata(helper_result: Any) -> dict[str, Any]:
    return {
        "classification_kind": getattr(helper_result, "classification_kind", None),
        "terminal": getattr(helper_result, "terminal", None),
        "sequence_terminal": getattr(helper_result, "sequence_terminal", None),
        "contact_started": getattr(helper_result, "contact_started", None),
        "opportunity_consumed": getattr(helper_result, "opportunity_consumed", None),
        "mutation_succeeded_count": getattr(helper_result, "mutation_succeeded_count", None),
        "committed_detail_label": getattr(helper_result, "committed_detail_label", None),
        "derived_subreason": getattr(helper_result, "derived_subreason", None),
    }


def _helper_failure_detail(helper_result: Any) -> str:
    committed_detail = getattr(helper_result, "committed_detail_label", None)
    derived_subreason = getattr(helper_result, "derived_subreason", None)
    if committed_detail and derived_subreason:
        return "%s: %s" % (committed_detail, derived_subreason)
    if committed_detail:
        return committed_detail
    if derived_subreason:
        return derived_subreason
    return "Authority-A did not produce publishable evidence"


def _authority_a_completed_three_mutations(helper_result: Any) -> bool:
    if getattr(helper_result, "classification", None) != (
        authority_a.CORRECTED_PATH_CREATION_EVIDENCE_READY_FOR_PUBLICATION
    ):
        return False
    if getattr(helper_result, "mutation_succeeded_count", None) != 3:
        return False
    if getattr(helper_result, "opportunity_consumed", None) is not True:
        return False
    if getattr(helper_result, "sequence_terminal", None) is not False:
        return False
    evidence_body = getattr(helper_result, "evidence_body", None)
    if not isinstance(evidence_body, Mapping):
        return False
    aggregate = evidence_body.get("aggregate")
    if not isinstance(aggregate, Mapping):
        return False
    return (
        aggregate.get("mutation_succeeded_count") == 3
        and aggregate.get("opportunity_consumed") is True
        and aggregate.get("sequence_terminal") is False
        and aggregate.get("full_ordered_sequence_succeeded") is True
    )


def _result(
    classification: str,
    accepted: bool,
    detail: str,
    accepted_invocation_head: str,
    *,
    authority_a_result: dict[str, Any] | None = None,
    authority_b_result: dict[str, Any] | None = None,
    whole_record_byte_count: int | None = None,
    whole_record_sha256: str | None = None,
    operator_assertions: OperatorAssertions | None = None,
    exception: dict[str, Any] | None = None,
    classification_kind: str | None = None,
    terminal: bool | None = None,
    sequence_terminal: bool | None = None,
    contact_started: bool | None = None,
    opportunity_consumed: bool | None = None,
    mutation_succeeded_count: int | None = None,
    failure_phase: str | None = None,
    committed_detail_label: str | None = None,
    derived_subreason: str | None = None,
) -> R4AuthorityABOrchestrationResult:
    return R4AuthorityABOrchestrationResult(
        classification=classification,
        accepted=accepted,
        detail=detail,
        accepted_invocation_head=accepted_invocation_head,
        classification_kind=classification_kind,
        terminal=terminal,
        sequence_terminal=sequence_terminal,
        contact_started=contact_started,
        opportunity_consumed=opportunity_consumed,
        mutation_succeeded_count=mutation_succeeded_count,
        failure_phase=failure_phase,
        committed_detail_label=committed_detail_label,
        derived_subreason=derived_subreason,
        authority_a_result=authority_a_result,
        authority_b_result=authority_b_result,
        whole_record_byte_count=whole_record_byte_count,
        whole_record_sha256=whole_record_sha256,
        operator_assertions=(
            operator_assertions.as_dict() if operator_assertions is not None else None
        ),
        exception=exception,
    )


def _strip_none(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_none(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_strip_none(item) for item in value]
    return value


def _exception_dict(exc: BaseException) -> dict[str, Any]:
    return {
        "exception_type": type(exc).__name__,
        "message": str(exc)[:240],
    }


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CORRECTED_PATH_CREATION_AB_ORCHESTRATION_PRE_CONTACT_ABORT",
    "FAILURE_PHASE_OPERATOR_ASSERTION_VALIDATION",
    "FAILURE_PHASE_TEST_PATH_MODEL_VALIDATION",
    "OperatorAssertions",
    "R4AuthorityABOrchestrationResult",
    "execute_authority_a_and_b",
    "main",
]
