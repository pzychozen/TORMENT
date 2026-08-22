"""Future-only Phase-13 dispatcher with durable post-start evidence closure."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Final, Protocol

from brainvision_phase13.backend import (
    QualificationExecutionBackend as ConcreteQualificationExecutionBackend,
)
from brainvision_phase13.evidence import EvidenceBuilder, assert_evidence_safe, detached_block_evidence
from brainvision_phase13.grader import GradingRecord, grade_evidence_package
from brainvision_phase13.inventory import instrument_content_hash_inventory
from brainvision_phase13.manifests import (
    AUTHORITY_MANIFEST_PATH,
    load_complete_expected_result_manifest,
    load_manifest,
    validate_all_manifests,
)
from brainvision_phase13.preflight import (
    PREFLIGHT_READY,
    PreflightFacts,
    build_administration_identity,
    collect_environment_checks,
    identity_binding_record,
    qualification_harness_sha256,
    verify_preflight,
)
from brainvision_phase13.qualification import (
    QualificationExecutionBackend as QualificationExecutionBackendProtocol,
    build_all_block_plans,
)
from brainvision_phase13.result_document import render_formal_result_document
from brainvision_phase13.schemas import BLOCK_IDS, canonical_json_bytes


_PACKAGE_DIRECTORY = Path(__file__).resolve().parent
_REPOSITORY_ROOT = _PACKAGE_DIRECTORY.parents[1]
_SPECIFICATION_PATH = _REPOSITORY_ROOT / "docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md"
_AUTHORIZATION_SCHEMA_ID = "brainvision.phase13.formal_authorization.v2"
_REQUIRED_IMPORTS = (
    "brainvision.lifecycle", "brainvision.ingress", "brainvision.sink", "brainvision_phase13.backend",
)


class FormalAuthorizationError(RuntimeError):
    """Refusal before formal dispatch; it emits neither evidence nor taxonomy."""


class BackendFactory(Protocol):
    def __call__(self, data_root: Path) -> QualificationExecutionBackendProtocol: ...


# The protocol remains the injected-factory boundary; formal dispatch constructs
# only the concrete executor supplied by the test-only backend module.
_DEFAULT_BACKEND_FACTORY: Final[BackendFactory] = ConcreteQualificationExecutionBackend


@dataclass(frozen=True, kw_only=True)
class FormalAuthorization:
    """Later immutable data-only authorization; this workorder does not create it."""

    expected_head: str
    administration_id: str
    authorization_token: str
    command_identity: str
    specification_sha256: str
    manifest_sha256s: Mapping[str, str]
    harness_sha256: str
    instrument_inventory: Mapping[str, str]


@dataclass(frozen=True, kw_only=True)
class FormalDispatchResult:
    administration_identity: str
    evidence_path: Path
    grading_path: Path
    result_document_path: Path
    evidence_index_path: Path
    grading: GradingRecord


class _DurableOperationJournal:
    """Append-only, fsync-backed safe-operation journal after start consumption."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, _block_id: str, entry: Mapping[str, object]) -> None:
        assert_evidence_safe(entry)
        with self.path.open("ab") as target:
            target.write(canonical_json_bytes(entry) + b"\n")
            target.flush()
            os.fsync(target.fileno())


def _run_git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments), cwd=_REPOSITORY_ROOT, check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    return completed.stdout.strip()


def _safe_exception_record(
    error: Exception, *, stage: str, block_id: str | None = None
) -> dict[str, object]:
    field = getattr(error, "field", None)
    reason = getattr(error, "reason", None)
    durable_committed = getattr(error, "durable_committed", None)
    return {
        "block_id": block_id,
        "durable_committed": durable_committed if type(durable_committed) is bool else None,
        "exception_class": type(error).__name__,
        "field": field if type(field) is str else None,
        "reason": reason if type(reason) is str else None,
        "stage": stage,
    }


def _write_once(path: Path, payload: bytes) -> None:
    with path.open("xb") as target:
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())


def _component_record(path: Path, *, status: str = "PRESENT") -> dict[str, object]:
    return {
        "path": path.name,
        "sha256": None if not path.is_file() else sha256(path.read_bytes()).hexdigest(),
        "status": status if path.is_file() else "ABSENT",
    }


def load_formal_authorization(path: Path) -> FormalAuthorization:
    """Strictly parse a later authorization artifact without consuming it."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FormalAuthorizationError("formal authorization artifact is unreadable") from error
    required = {
        "schema_id", "expected_head", "administration_id", "authorization_token",
        "command_identity", "specification_sha256", "manifest_sha256s", "harness_sha256",
        "instrument_inventory",
    }
    if (
        type(raw) is not dict or raw.get("schema_id") != _AUTHORIZATION_SCHEMA_ID
        or set(raw) != required or not isinstance(raw["manifest_sha256s"], Mapping)
        or not isinstance(raw["instrument_inventory"], Mapping)
    ):
        raise FormalAuthorizationError("formal authorization artifact has an invalid schema or field set")
    values = (
        raw["expected_head"], raw["administration_id"], raw["authorization_token"],
        raw["command_identity"], raw["specification_sha256"], raw["harness_sha256"],
    )
    if any(type(value) is not str or not value for value in values):
        raise FormalAuthorizationError("formal authorization artifact has invalid scalar fields")
    return FormalAuthorization(
        expected_head=raw["expected_head"], administration_id=raw["administration_id"],
        authorization_token=raw["authorization_token"], command_identity=raw["command_identity"],
        specification_sha256=raw["specification_sha256"],
        manifest_sha256s=dict(raw["manifest_sha256s"]), harness_sha256=raw["harness_sha256"],
        instrument_inventory=dict(raw["instrument_inventory"]),
    )


def verify_authorization_arguments(
    args: object, authorization: FormalAuthorization, canonical_administration_id: str
) -> None:
    """Require CLI, artifact, and independent recomputation to agree before start."""
    if (
        getattr(args, "expected_head", None) != authorization.expected_head
        or getattr(args, "administration_id", None) != authorization.administration_id
        or getattr(args, "formal_authorization_token", None) != authorization.authorization_token
        or authorization.administration_id != canonical_administration_id
    ):
        raise FormalAuthorizationError("formal authorization identity does not match canonical frozen inputs")


def collect_live_preflight_facts(
    *, authorization: FormalAuthorization, output_directory: Path
) -> PreflightFacts:
    """Collect all deterministic pre-start repository and environment facts."""
    manifest_sha256s = validate_all_manifests()
    return PreflightFacts(
        head=_run_git("rev-parse", "HEAD"),
        origin_main=_run_git("rev-parse", "origin/main"),
        worktree_clean=not _run_git("status", "--porcelain"),
        specification_sha256=sha256(_SPECIFICATION_PATH.read_bytes()).hexdigest(),
        manifest_sha256s=manifest_sha256s,
        harness_sha256=qualification_harness_sha256(_PACKAGE_DIRECTORY),
        output_directory_fresh=not output_directory.exists(),
        administration_identity_unused=not (output_directory / "administration_started.json").exists(),
        environment_checks=collect_environment_checks(
            output_directory=output_directory, repository_root=_REPOSITORY_ROOT,
            required_imports=_REQUIRED_IMPORTS,
        ),
    )


def _consume_administration_start(
    *, output_directory: Path, administration_identity: str,
    identity_record: Mapping[str, object], preflight_record: Mapping[str, object],
) -> tuple[Path, Path, Path]:
    """Durably write immutable pre-start records before the one start marker."""
    output_directory.mkdir(parents=True, exist_ok=False)
    identity_path = output_directory / "identity_binding_record.json"
    preflight_path = output_directory / "environment_preflight_record.json"
    start_path = output_directory / "administration_started.json"
    _write_once(identity_path, canonical_json_bytes(identity_record))
    _write_once(preflight_path, canonical_json_bytes(preflight_record))
    _write_once(start_path, canonical_json_bytes({
        "administration_identity": administration_identity,
        "identity_binding_record_sha256": sha256(identity_path.read_bytes()).hexdigest(),
        "schema_id": "brainvision.phase13.administration_start.v2",
    }))
    return identity_path, preflight_path, start_path


def _not_executed_block_evidence() -> dict[str, object]:
    return {
        "arm_ledgers": {}, "checkpoints": {}, "defect": None,
        "execution_state": "NOT_EXECUTED", "run_ledger": [],
        "run_ledger_canonical_bytes_ascii": "[]",
    }


def _build_evidence_index(
    *, output_directory: Path, identity_path: Path, preflight_path: Path, start_path: Path,
    journal_path: Path, evidence_path: Path, grading_path: Path, result_path: Path,
) -> dict[str, object]:
    """One deterministic top-level index for all durable formal evidence components."""
    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    records = [
        record
        for block in evidence_payload["blocks"].values()
        for record in block.get("run_ledger", [])
        if isinstance(record, Mapping)
    ]

    def embedded(name: str) -> dict[str, object]:
        return {
            "embedded_in": "evidence_package.json",
            "sha256": sha256(canonical_json_bytes([
                record.get(name) for record in records
            ])).hexdigest(),
            "status": "PRESENT" if any(record.get(name) is not None for record in records) else "ABSENT",
        }

    components = {
        "identity_binding_record": _component_record(identity_path),
        "environment_preflight_record": _component_record(preflight_path),
        "administration_start_record": _component_record(start_path),
        "ordered_operation_run_ledger": _component_record(journal_path),
        "receipts": embedded("receipt"),
        "projection_records": embedded("projection"),
        "artifact_hash_ledger": embedded("artifact_hashes"),
        "recovery_ledger": embedded("recovery"),
        "metrics": embedded("metrics"),
        "block_results": _component_record(grading_path),
        "grading_audit": _component_record(grading_path),
        "final_taxonomy": _component_record(grading_path),
        "evidence_package": _component_record(evidence_path),
        "formal_result_document": _component_record(result_path),
    }
    index = {
        "components": components,
        "output_directory": str(output_directory),
        "schema_id": "brainvision.phase13.evidence_package_index.v1",
    }
    assert_evidence_safe(index)
    return index


def dispatch_authorized_qualification(
    *, args: object, authorization: FormalAuthorization,
    preflight_collector: Callable[..., PreflightFacts] = collect_live_preflight_facts,
    backend_factory: BackendFactory | None = None,
) -> FormalDispatchResult:
    """Future-only, one-shot formal dispatch after all data-only guards pass."""
    canonical_administration_id = build_administration_identity(
        expected_head=authorization.expected_head,
        specification_sha256=authorization.specification_sha256,
        manifest_sha256s=authorization.manifest_sha256s,
        harness_sha256=authorization.harness_sha256,
        command_identity=authorization.command_identity,
    )
    verify_authorization_arguments(args, authorization, canonical_administration_id)
    output_directory = getattr(args, "output_dir", None)
    if not isinstance(output_directory, Path):
        raise FormalAuthorizationError("formal output directory is not a Path")
    facts = preflight_collector(authorization=authorization, output_directory=output_directory)
    outcome = verify_preflight(
        facts=facts, expected_head=authorization.expected_head,
        expected_specification_sha256=authorization.specification_sha256,
        expected_manifest_sha256s=authorization.manifest_sha256s,
        expected_harness_sha256=authorization.harness_sha256,
    )
    if outcome.status != PREFLIGHT_READY:
        raise FormalAuthorizationError("formal preflight blocked: " + ",".join(outcome.reasons))
    inventory = instrument_content_hash_inventory()
    if dict(authorization.instrument_inventory) != inventory:
        raise FormalAuthorizationError("formal authorization inventory differs from frozen instrument")
    authority_manifest = load_manifest(AUTHORITY_MANIFEST_PATH)
    identity_record = identity_binding_record(
        expected_head=authorization.expected_head, actual_head=facts.head,
        origin_main=facts.origin_main, administration_identity=canonical_administration_id,
        manifest_sha256s=facts.manifest_sha256s, harness_sha256=facts.harness_sha256,
        command_identity=authorization.command_identity, output_directory=output_directory,
        environment_checks=facts.environment_checks, authority_manifest=authority_manifest,
        inventory=inventory,
    )
    preflight_record = {
        "checks": [dict(check) for check in facts.environment_checks],
        "preflight_status": outcome.status,
        "schema_id": "brainvision.phase13.environment_preflight_record.v1",
    }
    assert_evidence_safe(identity_record)
    assert_evidence_safe(preflight_record)
    identity_path, preflight_path, start_path = _consume_administration_start(
        output_directory=output_directory, administration_identity=canonical_administration_id,
        identity_record=identity_record, preflight_record=preflight_record,
    )
    journal_path = output_directory / "operation_journal.ndjson"
    journal = _DurableOperationJournal(journal_path)
    evidence_builder = EvidenceBuilder(operation_journal_writer=journal.append)
    blocks: dict[str, object] = {}
    execution_failure: dict[str, object] | None = None
    selected_factory = _DEFAULT_BACKEND_FACTORY if backend_factory is None else backend_factory
    backend: object | None = None
    try:
        try:
            backend = selected_factory(output_directory / "runtime")
        except Exception as error:
            execution_failure = _safe_exception_record(error, stage="backend_construction")
        if backend is not None:
            for plan in build_all_block_plans():
                try:
                    execution = backend.execute_block(plan, evidence_builder)
                except Exception as error:
                    execution_failure = _safe_exception_record(error, stage="block_dispatch", block_id=plan.block_id)
                    break
                blocks[execution.block_id] = detached_block_evidence(
                    execution.operations, complete=execution.complete, defect=execution.defect
                )
                if not execution.complete:
                    defect = execution.defect
                    assert defect is not None
                    execution_failure = {
                        "arm": defect.arm, "block_id": defect.block_id,
                        "durable_committed": defect.durable_committed,
                        "exception_class": defect.exception_class, "field": defect.field,
                        "operation": defect.operation, "operation_index": defect.operation_index,
                        "reason": defect.reason, "stage": "block_command",
                    }
                    break
    except Exception as error:
        if execution_failure is None:
            execution_failure = _safe_exception_record(error, stage="post_start_evidence")
    finally:
        if backend is not None:
            close = getattr(backend, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as error:
                    if execution_failure is None:
                        execution_failure = _safe_exception_record(error, stage="backend_close")
    for block_id in BLOCK_IDS:
        blocks.setdefault(block_id, _not_executed_block_evidence())
    evidence_package: dict[str, object] = {
        "administration_identity": canonical_administration_id,
        "administration_started": True,
        "blocks": blocks,
        "execution_failure": execution_failure,
        "identity_binding_record": identity_record,
        "identity_binding_record_sha256": sha256(canonical_json_bytes(identity_record)).hexdigest(),
        "instrument_inventory": inventory,
        "preflight_record": preflight_record,
        "schema_id": "brainvision.phase13.detached_evidence_package.v2",
    }
    assert_evidence_safe(evidence_package)
    evidence_path = output_directory / "evidence_package.json"
    _write_once(evidence_path, canonical_json_bytes(evidence_package))
    expected_manifest = load_complete_expected_result_manifest()
    grading = grade_evidence_package(
        expected_manifest=expected_manifest, evidence_package=evidence_package,
        manifest_sha256=sha256(canonical_json_bytes(expected_manifest)).hexdigest(),
    )
    grading_path = output_directory / "grading_record.json"
    _write_once(grading_path, grading.to_canonical_bytes())
    result_document = render_formal_result_document(
        identity_binding_record=identity_record, preflight_record=preflight_record,
        administration_identity=canonical_administration_id, evidence_package=evidence_package,
        grading=grading, evidence_index_path="evidence_package_index.json",
    )
    result_document_path = output_directory / "formal_result.md"
    _write_once(result_document_path, result_document.encode("utf-8"))
    evidence_index_path = output_directory / "evidence_package_index.json"
    _write_once(evidence_index_path, canonical_json_bytes(_build_evidence_index(
        output_directory=output_directory, identity_path=identity_path, preflight_path=preflight_path,
        start_path=start_path, journal_path=journal_path, evidence_path=evidence_path,
        grading_path=grading_path, result_path=result_document_path,
    )))
    return FormalDispatchResult(
        administration_identity=canonical_administration_id, evidence_path=evidence_path,
        grading_path=grading_path, result_document_path=result_document_path,
        evidence_index_path=evidence_index_path, grading=grading,
    )


__all__ = (
    "FormalAuthorization", "FormalAuthorizationError", "FormalDispatchResult",
    "collect_live_preflight_facts", "dispatch_authorized_qualification",
    "load_formal_authorization", "verify_authorization_arguments",
)
