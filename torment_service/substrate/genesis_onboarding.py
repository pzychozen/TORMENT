"""Local/offline declaration planning and orchestration of the qualified phases.

Operator files are recovery configuration outside the root. No phase writes,
deployment authority, model provider selection or progress ledger live here.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import time
from urllib.parse import urlsplit
from uuid import UUID

from ..atomic_publication import _replacement_lock, publish_if_absent
from ..external_owner_json import owner_bytes, strict_object
from . import genesis_administration as i3
from . import genesis_character_administration as i4
from . import genesis_membership_administration as i5
from . import genesis_completion_administration as i6
from . import genesis_recovery as i7
from . import genesis_activation_administration as i8
from . import genesis_contracts as g
from . import deployment_selector as selector
from .deployment_types import DeploymentResolutionMode
from .errors import SubstrateError
from .genesis_fence import canonical_genesis_root, checked_stat, read_genesis_operation_record, read_genesis_fence
from .ids import generate_native_id, native_id_to_text


class NativeGenesisOnboardingRefused(g.GenesisContractError):
    """Invalid operator configuration or conflicting existing installation."""


def _require(condition, message):
    if not condition:
        raise NativeGenesisOnboardingRefused(message)


_DECLARATION_FIELDS = "data_root_identity workspace agent character profile_choice representation_lane"


def _operation_key(value):
    return "genesis-onboarding-v1:" + g.payload_digest(dict(contract=value["contract"], version=value["version"],
        data_root_identity=value["data_root_identity"], workspace_id=value["workspace"]["workspace_id"],
        agent_id=value["agent"]["agent_id"], request_digest=g.payload_digest(value)))


def _expanded_payload(value, id_factory, timestamp):
    """One allocation layout for validation and planning; no I/O or defaults."""
    workspace, agent = value["workspace"], value["agent"]
    key = _operation_key(value)
    root_fields = ("core_id", "root_profile_object_id", "root_profile_semantic_scope_id",
                   "root_profile_identity_namespace_id", "root_profile_idempotency_namespace_id")
    allocation = {field: native_id_to_text(id_factory()) for field in root_fields}
    allocation.update(core_relative_path="genesis-" + allocation["core_id"] + ".db", root_profile_generation=1)
    namespace_keys = {allocation[field]: key + ":" + field for field in root_fields[-2:]}
    plans = []
    scopes = [("PRIVATE", agent["agent_id"])] + [("SHARED", d) for d in workspace["ordered_domains"]]
    for kind, qualifier in sorted(scopes):
        scope_key = dict(workspace_id=workspace["workspace_id"], scope_kind=kind,
            agent_id=qualifier if kind == "PRIVATE" else None, domain_id=qualifier if kind == "SHARED" else None)
        identifiers = {field: native_id_to_text(id_factory()) for field in g.SCOPE_PLAN_UUID_FIELDS}
        domain = g.payload_digest(scope_key)
        namespace_keys.update({identifier: key + ":" + domain + ":" + field for field, identifier in identifiers.items()
                              if field != "target_semantic_scope_id"})
        plans.append(dict(scope_key=scope_key, scope_plan=dict(**identifiers, workspace_id=workspace["workspace_id"],
            scope_kind="PRIVATE_AGENT" if kind == "PRIVATE" else "SHARED_DOMAIN", qualifier=qualifier,
            motif_domain_id=agent["private_motif_domain_id"] if kind == "PRIVATE" else qualifier),
            representation_lane=value["representation_lane"]))
    allocation.update(namespace_keys=namespace_keys, runtime_scope_plans=plans)
    return dict(contract=g.GenesisIntent.CONTRACT, version=g.GenesisIntent.VERSION, origin=g.GenesisIntent.ORIGIN,
        operation_key=key, **{name: value[name] for name in _DECLARATION_FIELDS.split()}, allocations=allocation,
        creation_facts=dict(workspace_created_ts=timestamp, identity_created_ts=timestamp,
            character_created_ts=timestamp if value["character"]["mode"] == "ENABLED" else None))


class NativeGenesisOnboardingRequest(g.GenesisPayload):
    CONTRACT = "TORMENT_NATIVE_GENESIS_ONBOARDING_REQUEST"
    VERSION = 1
    KEYS = "contract version " + _DECLARATION_FIELDS

    @classmethod
    def validate(cls, value):
        _require(value["contract"] == cls.CONTRACT and type(value["version"]) is int and value["version"] == cls.VERSION,
            "unsupported onboarding request contract")
        _require(isinstance(value["data_root_identity"], str)
            and str(canonical_genesis_root(value["data_root_identity"])) == value["data_root_identity"],
            "request requires canonical data-root identity")
        # Delegate every nested declaration/tuning rule to frozen I1. These
        # fixed validation sentinels are never saved, returned or executed;
        # validation consumes neither the native ID factory nor the clock.
        index = iter(range(1, 1_000_000))
        try:
            payload = _expanded_payload(value, lambda: UUID(int=next(index), version=4), 0)
            g.GenesisIntent.from_payload(payload)
        except (KeyError, TypeError, ValueError, StopIteration) as exc:
            raise NativeGenesisOnboardingRefused("invalid nested onboarding declaration") from exc

    @property
    def operation_key(self):
        return _operation_key(self.payload())


def request_from_intent(intent):
    _require(isinstance(intent, g.GenesisIntent), "typed expanded GenesisIntent required")
    value = intent.payload()
    request = NativeGenesisOnboardingRequest.from_payload(dict(contract=NativeGenesisOnboardingRequest.CONTRACT,
        version=1, **{name: value[name] for name in _DECLARATION_FIELDS.split()}))
    _require(intent.operation_key == request.operation_key, "intent operation identity differs from its operator declaration")
    return request


def plan_native_genesis(request: NativeGenesisOnboardingRequest, *, id_factory=generate_native_id, time_factory=None):
    """Create an unsaved plan once. Use prepare_intent_plan for durable replay."""
    _require(isinstance(request, NativeGenesisOnboardingRequest), "typed onboarding request required")
    timestamp = int(time.time()) if time_factory is None else time_factory()
    return g.GenesisIntent.from_payload(_expanded_payload(request.payload(), id_factory, timestamp))


def _regular_path(path, *, root=None, required=False):
    _require(isinstance(path, (str, Path)) and bool(str(path)), "explicit operator file path required")
    absolute = Path(os.path.abspath(Path(path).expanduser()))
    for current in (*reversed(absolute.parents), absolute):
        info = checked_stat(current)
        if current != absolute:
            _require(info is not None and stat.S_ISDIR(info.st_mode), "operator file parent must be an existing directory")
        elif info is not None:
            _require(stat.S_ISREG(info.st_mode), "operator artifact must be a regular file")
        elif required:
            raise NativeGenesisOnboardingRefused("required operator artifact is absent")
    if root is not None:
        _require(not absolute.is_relative_to(root), "operator artifacts must be outside the data root")
    return absolute


def _read_payload(path):
    _require(path.stat().st_size <= 4 * 1024 * 1024, "operator artifact exceeds the bounded JSON size")
    return strict_object(path.read_bytes())


def read_onboarding_request(path):
    path = _regular_path(path, required=True)
    request = NativeGenesisOnboardingRequest.from_payload(_read_payload(path))
    _regular_path(path, root=canonical_genesis_root(request.payload()["data_root_identity"]), required=True)
    return request


def read_intent_plan(path):
    path = _regular_path(path, required=True)
    intent = g.GenesisIntent.from_payload(_read_payload(path))
    request_from_intent(intent)
    _regular_path(path, root=canonical_genesis_root(intent.data_root_identity), required=True)
    return intent


def _empty_start(root):
    i3._fresh_start(root, i3._inventory(root))


def _root_snapshot(root, intent=None):
    """Only called under root_observation; authority and phase share its boundary."""
    authority = _active(root, intent)
    if authority is not None:
        return authority, None
    record = read_genesis_operation_record(data_root=root)
    _require(intent is None or record is None or record.expanded_intent == intent,
        "root belongs to another Genesis intent")
    if record is None:
        _empty_start(root)
    else:
        # Planning and dependency selection must also refuse unexplained roots;
        # the phase owner revalidates these facts before its own mutation.
        phase = _phase(record)
        if phase == 3:
            i3._classify(root, record.expanded_intent, i3._inventory(root))
        elif phase in (4, 5):
            i4._inspect(root, record.expanded_intent)
        elif phase == 6:
            i6._inspect(root, record.expanded_intent)
        else:
            i8._read_state(root, record.expanded_intent, i8.activation_operation_keys(record.expanded_intent))
    return None, record


def _recovered_intent(root):
    authority, record = _root_snapshot(root)
    return authority.completion.expanded_intent if authority is not None else record.expanded_intent if record is not None else None


def prepare_intent_plan(request, *, intent_path, request_path=None, id_factory=generate_native_id, time_factory=None):
    """Recover/publish the exact external plan; only the OS rendezvous precedes it."""
    _require(isinstance(request, NativeGenesisOnboardingRequest), "typed onboarding request required")
    root = canonical_genesis_root(request.payload()["data_root_identity"])
    target = _regular_path(intent_path, root=root)
    if request_path is not None:
        source = _regular_path(request_path, root=root, required=True)
        _require(source != target and read_onboarding_request(source) == request, "request file differs from declaration")
    _regular_path(target.with_name(f".{target.name}.publication.lock"), root=root)
    with i3.root_observation(data_root=root, timeout_seconds=60.0) as held:
        with _replacement_lock(target):
            _regular_path(target, root=root)
            existing = read_intent_plan(target) if target.exists() else None
            recovered = held.observe(_recovered_intent, root)
            for candidate in (existing, recovered):
                if candidate is not None:
                    _require(request_from_intent(candidate) == request, "existing plan/root belongs to another declaration")
            if existing is not None:
                _require(recovered is None or recovered == existing, "saved allocations disagree with root recovery evidence")
                return existing
            intent = recovered if recovered is not None else plan_native_genesis(request, id_factory=id_factory, time_factory=time_factory)
            publish_if_absent(target, owner_bytes(intent.payload()))
            _require(read_intent_plan(target) == intent, "published intent differs from the frozen plan")
            return intent


def _profile_target(intent, path):
    if path is None:
        return None
    target = _regular_path(path, root=canonical_genesis_root(intent.data_root_identity))
    if target.exists():
        _require(owner_bytes(_read_payload(target)) == owner_bytes(i5.qualified_genesis_profile(intent).__dict__), "profile output conflicts")
    return target


def export_qualified_profile(intent, profile, path):
    target = _profile_target(intent, path)
    if target is not None:
        expected = profile.__dict__
        _require(expected == i5.qualified_genesis_profile(intent).__dict__, "profile differs from frozen intent")
        if not target.exists():
            publish_if_absent(target, owner_bytes(expected))
        _require(owner_bytes(_read_payload(_regular_path(target, root=canonical_genesis_root(intent.data_root_identity), required=True))) == owner_bytes(expected),
            "profile publication conflicts")


def _active(root, intent=None):
    authority = i7.verify_active_native_genesis(data_root=root, expected_intent=intent)
    if authority is None:
        return None
    authority = i7.recover_active_native_genesis(data_root=root, expected_completion=authority.completion)
    if intent is not None:
        _require(authority.completion.expanded_intent == intent, "active root belongs to another intent")
    agreement = selector.resolve_deployment_agreement(data_root=root, effective_profile=authority.completion.qualified_deployment_profile)
    _require(agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT, "active root lacks native agreement")
    return authority


def _phase(record):
    """References select the next owner; that owner must verify its native truth."""
    if record is None:
        return 3
    if record.administrative_phase is not g.GenesisAdministrativePhase.PREPARING:
        return 8
    owners = {ref.payload()["owner"] for ref in record.child_operation_references}
    if set(i5._OWNERS) <= owners:
        return 6
    character_owners = set(i4._EXTERNAL_OWNERS)
    if record.expanded_intent.payload()["character"]["mode"] == "ENABLED":
        character_owners.update(i4._NATIVE_OWNERS)
    if character_owners <= owners:
        return 5
    if {"native-core-preparation", *("native-catalog:" + table for table in i3.CATALOG_COLUMNS)} <= owners:
        return 4
    return 3


def _needs_embedding(root, intent, record):
    if intent.payload()["character"]["mode"] == "DISABLED" or _phase(record) > 4:
        return False
    if _phase(record) < 4:
        return True
    path = root / i3.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]
    with closing(i3._open_readonly(path)) as connection:
        runtime = i7.NativeCharacterSeedPlantRuntime(connection, configuration=i4._configuration(intent, i5._CommittedLane(intent)))
        return runtime.recover_completed_seed(i7.NativeCharacterSeedPlantRequest(i4._seed(intent))) is None


def onboarding_needs_embedding(intent):
    """Read-only dependency decision, including completed native seed recovery."""
    request_from_intent(intent)
    root = canonical_genesis_root(intent.data_root_identity)
    with i3.root_observation(data_root=root, timeout_seconds=60.0) as held:
        authority, record = held.observe(_root_snapshot, root, intent)
        return False if authority is not None else held.observe(_needs_embedding, root, intent, record)


@dataclass(frozen=True)
class LocalOperatorConfirmation:
    """Human confirmation covering other writers for this whole invocation.

    Each phase timestamps its use of the operator's continuing confirmation.
    This is explicitly not a process census or an automatically detected fact.
    """
    service_stopped: bool
    mcp_stopped: bool
    direct_tools_stopped: bool
    fabric_hosts_stopped: bool
    root_jobs_absent: bool
    public_listener_absent: bool
    public_listener: str

    def __post_init__(self):
        _require(all(value is True for name, value in self.__dict__.items() if name != "public_listener"),
            "explicit confirmation of every offline condition is required")
        g.text(self.public_listener, "public TORMENT listener")
        address = urlsplit(self.public_listener)
        _require(address.scheme in ("http", "https") and address.hostname and address.port
            and not address.username and not address.password and not address.query and not address.fragment,
            "explicit public listener URL with host and port required")

    def __call__(self, root, intent):
        mechanism = "LOCAL_HUMAN_OPERATOR_CONFIRMATION_V1"
        writers = tuple(i3.WriterProcessObservation(kind, mechanism,
            i3.WriterObservationResult.ABSENT if kind is i3.RootWriterClass.NONTERMINAL_ROOT_JOB else i3.WriterObservationResult.STOPPED)
            for kind in i3.RootWriterClass)
        listeners = (i3.ListenerObservation(self.public_listener, mechanism, i3.ListenerObservationResult.ABSENT),)
        return i3.GenesisWriterObservation(str(root), intent.operation_key, time.time_ns(), writers, listeners, True)


def onboarding_result(authority):
    completion = authority.completion
    value = completion.expanded_intent.payload()
    return dict(status="NATIVE_ACTIVE", data_root=str(authority.data_root), workspace_id=value["workspace"]["workspace_id"],
        agent_id=value["agent"]["agent_id"], core_id=str(completion.native_core_id), core_relative_path=completion.core_relative_path,
        selector_generation=authority.selector_state.generation, completion_digest=completion.digest,
        qualified_deployment_profile=completion.qualified_profile_payload())


def run_native_genesis_onboarding(*, intent, intent_path, observer, operator_attestation, issuer_reference,
                                 embedder=None, profile_out=None, timeout_seconds=1.0, fault=i3._noop):
    """Observe, select and run each phase within one existing root acquisition.

    Phase owners reuse the live token and retain their quiescence, identity,
    completion and activation checks. Active replay does not invoke the observer.
    """
    request_from_intent(intent)
    root = canonical_genesis_root(intent.data_root_identity)
    target = _regular_path(intent_path, root=root, required=True)
    _require(read_intent_plan(target) == intent, "the exact intent must be persisted before execution")
    output = _profile_target(intent, profile_out)
    _require(output is None or output != target, "intent and profile outputs must be distinct")
    deadline = time.monotonic() + 60.0
    observations = dict(observer=observer, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
    while True:
        try:
            with i3.root_observation(data_root=root, timeout_seconds=timeout_seconds) as held:
                authority, record = held.observe(_root_snapshot, root, intent)
                if authority is not None:
                    export_qualified_profile(intent, authority.completion.qualified_deployment_profile, output)
                    return onboarding_result(authority)
                _require(callable(observer), "typed writer observer required")
                since = time.time_ns()
                facts = observer(root, intent)
                _require(isinstance(facts, i3.GenesisWriterObservation), "typed writer observation required")
                facts.evidence(intent, since_ns=since, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
                dependency = None
                if intent.payload()["character"]["mode"] == "ENABLED":
                    dependency = embedder if held.observe(_needs_embedding, root, intent, record) else i5._CommittedLane(intent)
                    lane = intent.payload()["representation_lane"]
                    _require(dependency is not None and dependency.provider == lane["provider"] and dependency.model == lane["model"]
                        and type(dependency.dim) is int and dependency.dim == lane["dimension"], "embedder differs from declared representation lane")
                phase = _phase(record)
                context = dict(data_root=root, intent=intent, timeout_seconds=timeout_seconds, held_lock=held)
                if phase == 3:
                    i3.prepare_genesis_inert_root(**context, **observations)
                elif phase == 4:
                    with i4.begin_genesis_character_administration(**context) as session:
                        session.observe_quiescence(**observations)
                        session.prepare_first_character_bundle(embedder=dependency, **observations)
                elif phase == 5:
                    with i5.begin_genesis_membership_administration(**context) as session:
                        session.observe_quiescence(**observations)
                        session.prepare_initial_memberships(**observations)
                elif phase == 6:
                    with i6.begin_genesis_completion_administration(**context) as session:
                        session.seal_preparation(**observations)
                else:
                    i8.activate_genesis(**context, **observations)
        except SubstrateError as exc:
            # A busy mutex proves only that observation must wait. Exact peer
            # identity is established after acquisition, never inferred here.
            if str(exc) == "root-onboarding-lock-busy" and time.monotonic() < deadline:
                continue
            raise
        fault("after-i" + str(phase))


def native_genesis_status(*, data_root, intent=None):
    """Coherent evidence projection; only the OS rendezvous, no provider/phase writes."""
    root = canonical_genesis_root(data_root)
    try:
        with i3.root_observation(data_root=root, timeout_seconds=60.0) as held:
            return held.observe(_status, root, intent)

    except (SubstrateError, ValueError, OSError):
        return dict(status="CONFLICT", data_root=str(root))


def _status(root, intent):
    authority = _active(root, intent)
    if authority is not None:
        return onboarding_result(authority)
    record = read_genesis_operation_record(data_root=root)
    if record is None:
        _empty_start(root)
        return dict(status="NOT_STARTED", data_root=str(root))
    _require(intent is None or record.expanded_intent == intent, "foreign Genesis intent")
    _require(read_genesis_fence(data_root=root).value == "BLOCK_LEGACY", "unfinished Genesis fence conflicts")
    status = record.administrative_phase.value
    if status != "PREPARING":
        state = i8._read_state(root, record.expanded_intent, i8.activation_operation_keys(record.expanded_intent))
        status = "CORE_ACTIVATED_SELECTOR_PENDING" if len(state.receipts) == 2 else "PREPARATION_SEALED"
    return dict(status=status, data_root=str(root))
