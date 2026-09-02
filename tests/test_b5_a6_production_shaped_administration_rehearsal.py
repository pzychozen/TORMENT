"""B5-A6 operator diagnostics and real-service administration rehearsal."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from torment_service.substrate.deployment_diagnostic import (
    DeploymentDiagnosticRequest,
    inspect_deployment_diagnostic,
)
from torment_service.substrate.deployment_selector import (
    establish_selector_era,
    initialize_selector,
)
from torment_service.substrate.deployment_types import DeploymentState
from torment_service.substrate.ids import generate_native_id
from torment_service.substrate.offline_cutover_controller import (
    OfflineCutoverController,
    OfflineCutoverStage,
)
from torment_service.substrate.runtime_qualification import RuntimeQualificationResult

from test_b5_a5_offline_cutover_rehearsal import (
    _controller_request,
    _direct_request,
    _freeze_native_compatible_external_policy,
    _set_hash_environment,
    _tree_digest,
)
from test_substrate_existing_workspace_multi_scope_admission import (
    _create_real_workspace,
    _freeze_zero_eid_overlap,
    _plans,
)


_REPOSITORY = Path(__file__).resolve().parents[1]
_SERVICE_URL = "http://127.0.0.1:8787"


def _service_environment(root: Path, *, profile: object | None = None, descriptor: Path | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "TORMENT_DATA_DIR": str(root),
        "TORMENT_EMBED_PROVIDER": "hash",
        "TORMENT_HASH_DIM": "3",
        "TORMENT_AUTH_ENABLE": "0",
        "TORMENT_CHARACTER_ENABLE": "0",
        "TORMENT_CHECKPOINT_ENABLE": "0",
        "TORMENT_HIVEMIND_ENABLE": "0",
        "TORMENT_THINKING_ADVISORY": "0",
        "TORMENT_SRG_COGNITION": "0",
        "TORMENT_REINFORCE_SIM_THRESHOLD": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "1000",
    })
    environment.pop("TORMENT_DEPLOYMENT_PROFILE_JSON", None)
    environment.pop("TORMENT_ADMISSION_DESCRIPTOR_PATH", None)
    if profile is not None and descriptor is not None:
        environment["TORMENT_DEPLOYMENT_PROFILE_JSON"] = json.dumps(asdict(profile), sort_keys=True)
        environment["TORMENT_ADMISSION_DESCRIPTOR_PATH"] = str(descriptor)
    return environment


def _start_service(environment: dict[str, str]) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        [sys.executable, "-m", "torment_service"],
        cwd=_REPOSITORY,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("production-shaped torment_service exited before health")
        try:
            with urlopen(f"{_SERVICE_URL}/health", timeout=1) as response:
                if response.status == 200:
                    return process
        except OSError:
            time.sleep(0.15)
    _stop_service(process)
    raise AssertionError("production-shaped torment_service did not become healthy")


def _stop_service(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def _assert_service_refused(environment: dict[str, str]) -> None:
    process = subprocess.Popen(
        [sys.executable, "-m", "torment_service"],
        cwd=_REPOSITORY,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                return
            try:
                with urlopen(f"{_SERVICE_URL}/health", timeout=0.5) as response:
                    if response.status == 200:
                        raise AssertionError("pending deployment started a public REST service")
            except HTTPError:
                pass
            except OSError:
                pass
            time.sleep(0.15)
        raise AssertionError("pending public startup did not fail closed")
    finally:
        _stop_service(process)


def _http(path: str, payload: dict[str, object], *, headers: dict[str, str] | None = None) -> dict:
    request = Request(
        f"{_SERVICE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except OSError:
            detail = "response body unavailable"
        raise AssertionError(f"{path} returned HTTP {exc.code}: {detail}") from exc


def _health() -> dict:
    with urlopen(f"{_SERVICE_URL}/health", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _mcp_runtime_probe(environment: dict[str, str], root: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(environment)
    environment["TORMENT_MCP_DATA_DIR"] = str(root)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from torment_service import mcp_server; "
            "runtime = mcp_server._get_fabric(); "
            "print(runtime.mode.value); "
            "mcp_server._close_runtime()",
        ],
        cwd=_REPOSITORY,
        env=environment,
        capture_output=True,
        text=True,
        timeout=35,
    )


def _diagnostic(root: Path, profile=None, descriptor: Path | None = None) -> dict:
    return inspect_deployment_diagnostic(
        DeploymentDiagnosticRequest(root, profile, descriptor),
    ).to_dict()


def test_b5_a6_formal_two_window_rehearsal_and_safe_abort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Exercise R0--R12 through actual ``python -m torment_service`` lifecycles."""

    _set_hash_environment(monkeypatch)
    data_root = tmp_path / "formal-api-token-redacted-root"

    # R0/R1: the established executable service creates the required private
    # plus shared legacy lanes through ordinary HTTP, then shuts down cleanly.
    initial = _diagnostic(data_root)
    assert initial["deployment_mode"] == "LEGACY_PUBLIC"
    assert initial["public_backend_mode"] == "LEGACY"
    workspace_root = _create_real_workspace(data_root)
    _freeze_native_compatible_external_policy(workspace_root)
    _freeze_zero_eid_overlap(workspace_root, _plans(workspace_root))

    legacy_environment = _service_environment(data_root)
    service = _start_service(legacy_environment)
    try:
        assert _health()["public_memory_mode"] == "LEGACY"
        legacy_ingest = _http("/agent/ingest", {
            "workspace_id": "orchard", "agent_id": "aria",
            "text": "formal legacy operator memory", "step": 41,
            "domain_id": "personal", "scope": "private",
            "supplied_embedding": [1.0, 0.0, 0.0],
        })
        assert legacy_ingest["stored"] is True
        assert _http("/agent/query", {
            "workspace_id": "orchard", "agent_id": "aria",
            "query": "formal legacy operator memory", "domain_id": "personal",
        })["results"]
    finally:
        _stop_service(service)
    legacy_mcp = _mcp_runtime_probe(legacy_environment, data_root)
    assert legacy_mcp.returncode == 0 and "LEGACY" in legacy_mcp.stdout

    # R2 is an explicit writer drain: after REST/MCP processes stop, the
    # legacy source is frozen before P1.  No service remains running here.
    legacy_evidence = _tree_digest(workspace_root)
    request, profile = _controller_request(
        data_root,
        workspace_root,
        admission_key="b5-a6-formal-admission",
        operator_key="b5-a6-formal-operator",
    )
    controller = OfflineCutoverController()

    # R3--R5: P1 is inert legacy compatibility; P2 fences every public
    # transport; interrupted/resumed admission remains maintenance-only.
    prepared = controller.prepare(request)
    p1 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert p1["deployment_mode"] == "LEGACY_PUBLIC"
    assert p1["core_role"] == "STAGING"
    assert p1["core_deployment_state"] == "LEGACY_ACTIVE"
    assert p1["admission_state"] == "ADMISSION_INCOMPLETE_RESUMABLE"

    controller.enter_external_pending(request)
    pending_environment = _service_environment(
        data_root, profile=profile, descriptor=request.admission_request.admission_descriptor_path,
    )
    p2 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert p2["deployment_mode"] == "MAINTENANCE_ONLY"
    assert p2["public_backend_mode"] == "REFUSED"
    _assert_service_refused(pending_environment)
    pending_mcp = _mcp_runtime_probe(pending_environment, data_root)
    assert pending_mcp.returncode != 0

    with pytest.raises(RuntimeError):
        controller.admit_under_external_fence(request, _test_interrupt_after="SHARED_B3A")
    interrupted_admission = _diagnostic(
        data_root, profile, request.admission_request.admission_descriptor_path,
    )
    assert interrupted_admission["deployment_mode"] == "MAINTENANCE_ONLY"
    completed = controller.admit_under_external_fence(request)
    assert completed.descriptor.state.value == "ADMISSION_COMPLETE"

    # R6--R8: completed admission and each core maintenance step are visible
    # through observation only.  Reconstructing the controller models an
    # operator-process restart: all recovery facts are durable elsewhere.
    verified = controller.verify_completion(request)
    r6 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert r6["deployment_mode"] == "MAINTENANCE_ONLY"
    assert r6["admission_state"] == "ADMISSION_COMPLETE"
    assert r6["admission_identity_matches"] is True
    assert r6["completion_witness_valid"] is True
    assert verified.stage is OfflineCutoverStage.ADMISSION_COMPLETE

    controller.enter_core_pending(request)
    r7 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert r7["deployment_mode"] == "MAINTENANCE_ONLY"
    assert r7["core_deployment_state"] == "CUTOVER_PENDING"

    controller.activate_core(request)
    r8 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert r8["deployment_mode"] == "MAINTENANCE_ONLY"
    assert r8["reason_code"] == "core-active-external-pending"
    _assert_service_refused(pending_environment)
    assert _mcp_runtime_probe(pending_environment, data_root).returncode != 0

    # The administrator process is intentionally state-free.  A fresh
    # diagnostic subprocess and a new controller instance resume R9 without
    # touching SQLite manually.
    cli = subprocess.run(
        [sys.executable, "-m", "torment_service.substrate.deployment_diagnostic", "--data-root", str(data_root)],
        cwd=_REPOSITORY, env=pending_environment, capture_output=True, text=True, timeout=35,
    )
    assert cli.returncode == 0
    assert json.loads(cli.stdout)["reason_code"] == "core-active-external-pending"
    controller = OfflineCutoverController()
    controller.activate_external_selector(request)
    r9 = _diagnostic(data_root, profile, request.admission_request.admission_descriptor_path)
    assert r9["deployment_mode"] == "NATIVE_AGREEMENT"
    assert r9["public_backend_mode"] == "NATIVE"
    assert r9["runtime_admissible"] is True and r9["profile_qualified"] is True

    # R10/R11: the same actual entry point now receives only host proof facts;
    # it cannot be instructed to choose native.  The durable selector is what
    # makes its health surface native.
    native_environment = _service_environment(
        data_root, profile=profile, descriptor=request.admission_request.admission_descriptor_path,
    )
    service = _start_service(native_environment)
    try:
        assert _health()["public_memory_mode"] == "NATIVE"
        native_query = _http("/agent/query", {
            "workspace_id": "orchard", "agent_id": "aria",
            "query": "formal legacy operator memory",
        })
        assert native_query["results"]
        retrieved = _http("/retrieve", {
            "workspace_id": "orchard", "agent_id": "aria",
            "query": "formal legacy operator memory",
        })
        assert "blocks" in retrieved and "assembled_text" in retrieved
        spine = _http("/spine/submit_task", {
            "workspace_id": "orchard", "agent_id": "aria", "operation": "query_memory",
            "payload": {"query": "formal legacy operator memory"},
        })
        assert spine["ok"] is True
        headers = {"Idempotency-Key": "b5-a6-redaction-key-not-diagnostic"}
        body = {
            "workspace_id": "orchard", "agent_id": "aria",
            "text": "formal native recovery memory", "step": 92,
            "domain_id": "personal", "scope": "private",
            "supplied_embedding": [1.0, 0.0, 0.0],
        }
        first = _http("/agent/ingest", body, headers=headers)
        replay = _http("/agent/ingest", body, headers=headers)
        assert first == replay and first["stored"] is True
        assert _http("/agent/query", {
            "workspace_id": "orchard", "agent_id": "aria",
            "query": "formal native recovery memory",
        })["results"]
    finally:
        _stop_service(service)
    native_mcp = _mcp_runtime_probe(native_environment, data_root)
    assert native_mcp.returncode == 0 and "NATIVE" in native_mcp.stdout
    assert _tree_digest(workspace_root) == legacy_evidence

    # R12: cold native restart preserves both migrated and native memory.
    service = _start_service(native_environment)
    try:
        assert _health()["public_memory_mode"] == "NATIVE"
        assert _http("/agent/query", {
            "workspace_id": "orchard", "agent_id": "aria",
            "query": "formal native recovery memory",
        })["results"]
    finally:
        _stop_service(service)

    # Separate safe-abort rehearsal: no core becomes active, selector returns
    # legacy, and a real legacy service can start on that root afterward.
    abort_request, abort_profile = _direct_request(tmp_path, monkeypatch, "safe-abort-root")
    abort_controller = OfflineCutoverController()
    abort_controller.prepare(abort_request)
    abort_controller.enter_external_pending(abort_request)
    abort_controller.admit_under_external_fence(abort_request)
    abort_controller.verify_completion(abort_request)
    abort_controller.enter_core_pending(abort_request)
    abort_controller.safe_pending_abort(abort_request)
    aborted = _diagnostic(
        abort_request.root, abort_profile, abort_request.admission_request.admission_descriptor_path,
    )
    assert aborted["deployment_mode"] == "LEGACY_PUBLIC"
    abort_service = _start_service(_service_environment(abort_request.root))
    try:
        assert _health()["public_memory_mode"] == "LEGACY"
    finally:
        _stop_service(abort_service)


def test_b5_a6_diagnostic_refusals_redaction_and_no_side_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Characterize bounded refusal codes without a legacy fallback or writes."""

    _set_hash_environment(monkeypatch)
    from torment_service.public_runtime import (
        PublicRuntimeStartupRefused,
        load_public_runtime_configuration_from_host_environment,
    )

    monkeypatch.setenv("TORMENT_DEPLOYMENT_PROFILE_JSON", "{}")
    monkeypatch.delenv("TORMENT_ADMISSION_DESCRIPTOR_PATH", raising=False)
    with pytest.raises(PublicRuntimeStartupRefused, match="incomplete"):
        load_public_runtime_configuration_from_host_environment()
    monkeypatch.delenv("TORMENT_DEPLOYMENT_PROFILE_JSON", raising=False)
    data_root = tmp_path / "api-token-abc123-request-text-hidden"
    data_root.mkdir()
    baseline = _tree_digest(data_root)
    first = _diagnostic(data_root)
    second = _diagnostic(data_root)
    assert first == second
    assert _tree_digest(data_root) == baseline
    rendered = json.dumps(first, sort_keys=True)
    for forbidden in (str(data_root), "api-token-abc123", "request-text-hidden", "b5-a6-redaction-key-not-diagnostic"):
        assert forbidden not in rendered

    # Managed marker without a selector and a corrupted selector both refuse;
    # neither diagnostic read makes a selector or an SQLite sidecar.
    establish_selector_era(data_root=data_root)
    marker_only = _diagnostic(data_root)
    assert marker_only["deployment_mode"] == "REFUSED"
    assert marker_only["reason_code"] == "selector-era-marker-and-selector-must-coexist"
    initialize_selector(data_root=data_root, operation_key="b5-a6-diagnostic-fixture")
    paths = data_root / "substrate" / "deployment" / "selector.sqlite"
    paths.write_bytes(b"not-a-selector")
    corrupt = _diagnostic(data_root)
    assert corrupt["deployment_mode"] == "REFUSED"
    assert corrupt["reason_code"] == "selector-invalid"

    # Use a separate qualified active root for every remaining redacted
    # observation.  The controller remains the sole mutator in this fixture.
    request, profile = _direct_request(tmp_path, monkeypatch, "diagnostic-active")
    controller = OfflineCutoverController()
    controller.prepare(request)
    controller.enter_external_pending(request)
    controller.admit_under_external_fence(request)
    controller.verify_completion(request)
    controller.enter_core_pending(request)
    controller.activate_core(request)
    controller.activate_external_selector(request)
    descriptor = request.admission_request.admission_descriptor_path
    active_before = _tree_digest(request.root)
    active = _diagnostic(request.root, profile, descriptor)
    assert active["deployment_mode"] == "NATIVE_AGREEMENT"
    assert active["admission_identity_matches"] is True
    assert active["completion_witness_valid"] is True
    assert _diagnostic(request.root, profile, descriptor) == active
    assert _tree_digest(request.root) == active_before

    mismatched_profile = replace(
        profile,
        external_owner_digest=hashlib.sha256(b"b5-a6-profile-mismatch").hexdigest(),
    )
    mismatch = _diagnostic(request.root, mismatched_profile, descriptor)
    assert mismatch["deployment_mode"] == "REFUSED"
    assert mismatch["reason_code"] == "effective-profile-is-not-the-qualified-selector-profile"

    # These isolated reader fixtures simulate an unavailable/mismatched core
    # without changing durable facts.  The diagnostic may only refuse; it
    # never repairs, selects, or falls back.
    import torment_service.substrate.deployment_diagnostic as diagnostic_module
    import torment_service.substrate.deployment_selector as selector_module

    original_inspection = diagnostic_module.inspect_contained_core_deployment
    with monkeypatch.context() as scoped:
        scoped.setattr(
            diagnostic_module,
            "inspect_contained_core_deployment",
            lambda **_kwargs: (_ for _ in ()).throw(FileNotFoundError("fixture")),
        )
        missing = _diagnostic(request.root, profile, descriptor)
        assert missing["deployment_mode"] == "REFUSED"
        assert missing["reason_code"] == "selected-core-unavailable"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            diagnostic_module,
            "inspect_contained_core_deployment",
            lambda **kwargs: replace(
                original_inspection(**kwargs), core_id=generate_native_id(),
            ),
        )
        uuid_mismatch = _diagnostic(request.root, profile, descriptor)
        assert uuid_mismatch["deployment_mode"] == "REFUSED"
        assert uuid_mismatch["reason_code"] == "selected-core-uuid-mismatch"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            diagnostic_module,
            "inspect_contained_core_deployment",
            lambda **kwargs: replace(
                original_inspection(**kwargs),
                core_role="STAGING",
                deployment_state=DeploymentState.LEGACY_ACTIVE,
            ),
        )
        staging = _diagnostic(request.root, profile, descriptor)
        assert staging["deployment_mode"] == "REFUSED"
        assert staging["reason_code"] == "native-selector-core-is-not-active"
    with monkeypatch.context() as scoped:
        scoped.setattr(diagnostic_module, "_completion_witness_valid", lambda _descriptor: False)
        completion_invalid = _diagnostic(request.root, profile, descriptor)
        assert completion_invalid["deployment_mode"] == "REFUSED"
        assert completion_invalid["reason_code"] == "admission-completion-witness-invalid"

    # Runtime eligibility uses the same resolver gate.  A synthetic
    # ineligible runtime must not be represented as a native public result.
    synthetic = RuntimeQualificationResult(
        python_version="test", sqlite3_module_version="test", sqlite_runtime_version="3.51.2",
        json_available=True, transaction_savepoint_available=True,
        runtime_admissible=False, reason="synthetic-ineligible",
    )
    monkeypatch.setattr(diagnostic_module, "inspect_runtime", lambda: synthetic)
    monkeypatch.setattr(
        selector_module,
        "qualify_runtime",
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic-ineligible")),
    )
    synthetic_result = _diagnostic(request.root, profile, descriptor)
    assert synthetic_result["runtime_admissible"] is False
    assert synthetic_result["deployment_mode"] == "REFUSED"
    assert synthetic_result["reason_code"] == "actual-sqlite-runtime-is-not-qualified"
