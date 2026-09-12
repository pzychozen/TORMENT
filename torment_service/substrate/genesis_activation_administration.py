"""Offline I8 coordinator. Existing selector/core ledgers alone own activation.

The root mutex covers observation, verification, publication and administrative
closeout. Read helpers recover historical receipts without invoking a writable
API on replay. No service, model, descriptor or request surface is constructed.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, replace
import time
import re

from ..atomic_publication import replace_if_exact_predecessor
from ..external_owner_json import owner_bytes, strict_object
from . import deployment_core_maintenance as core
from . import deployment_selector as selector
from . import genesis_administration as i3
from . import genesis_character_administration as i4
from . import genesis_completion_administration as i6
from . import genesis_membership_administration as i5
from . import genesis_recovery as i7
from .deployment_types import DeploymentResolutionMode, DeploymentState, NativeGenesisCompletionWitness
from .genesis_contracts import GenesisAdministrativePhase, GenesisEvidenceReference, GenesisIntent, payload_digest
from .genesis_fence import GenesisPreparationRefused, canonical_genesis_root, read_genesis_fence, read_genesis_operation_record
from .root_scope_membership import RootScopeMembershipReader
from .schema import require_current_schema

_SEALED = GenesisAdministrativePhase.PREPARATION_SEALED
_CORE = GenesisAdministrativePhase.CORE_ACTIVATED
_DONE = GenesisAdministrativePhase.COMPLETED
_ROLES = ("selector-initialize", "selector-cutover-pending", "core-cutover-pending", "core-activate", "selector-activate")


def activation_operation_keys(intent):
    """Retry identities contain only immutable Genesis identity and a role."""
    return {role: "genesis-i8:" + payload_digest(dict(genesis_operation_key=intent.operation_key,
        intent_digest=intent.digest, role=role)) for role in _ROLES}


def _require(condition, message):
    if not condition:
        raise GenesisPreparationRefused("I8 " + message)


def _record_path(root):
    return root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME


def _core_reference(result, keys):
    return GenesisEvidenceReference.from_payload(dict(owner="native-core-activation",
        operation_key=keys["core-activate"], result_digest=payload_digest(dict(
            transition_kind=result.transition_kind, maintenance_id=str(result.maintenance_id),
            selector_generation=result.selector_generation, selector_witness_digest=result.selector_witness_digest,
            core_witness=core._witness_payload(result.witness), completion_witness_digest=result.completion_witness.digest))))


def _selector_projection(state):
    return dict(generation=state.generation, deployment_state=state.deployment_state.value,
        core_id=None if state.core_id is None else str(state.core_id), core_relative_path=state.core_relative_path,
        descriptor_digest=state.descriptor_digest, profile_digest=state.profile_digest, core_witness_digest=state.core_witness_digest)


def _selector_intent(role, keys, completion, active=None):
    # Exact existing API intent projections, used only to reject foreign ledger
    # entries. Publication always goes through the qualified selector owner.
    kinds = {"selector-initialize": "INITIALIZE_SELECTOR", "selector-cutover-pending": "BEGIN_CUTOVER_PENDING",
             "selector-activate": "ACTIVATE_SELECTOR_NATIVE"}
    value = dict(contract=selector._SELECTOR_CONTRACT, kind=kinds[role], operation_key=keys[role])
    if role == "selector-cutover-pending":
        value.update(expected_generation=0, expected_state="LEGACY_ACTIVE", core_relative_path=completion.core_relative_path,
            descriptor_digest=completion.admission_identity_digest, profile_digest=completion.profile_digest)
    elif role == "selector-activate":
        _require(active is not None, "active selector lacks core activation")
        value.update(expected_generation=1, expected_state="CUTOVER_PENDING", core_relative_path=completion.core_relative_path,
            activation_maintenance_id=str(active.maintenance_id), core_witness_digest=active.witness.digest)
    return value


def _selector_reference(state, intent, keys):
    return GenesisEvidenceReference.from_payload(dict(owner="native-selector-activation",
        operation_key=keys["selector-activate"], result_digest=payload_digest(dict(
            **_selector_projection(state), activation_operation_intent=intent))))


def _transition_truth(root, record, completion):
    """Reread sealed preparation facts while the deployment state is advancing.

    I6's inert-only verifier remains unchanged. Its pure completion projection
    and the existing native readers bind the same profile/membership/Character
    facts; deployment changes are independently checked against their ledgers.
    """
    intent = record.expanded_intent
    path = core.contained_core_path(data_root=root, core_relative_path=completion.core_relative_path, require_exists=True)
    with closing(core._open_readonly_core(path)) as connection:
        metadata = require_current_schema(connection)
        profile = i5._recover_profile(connection, intent)
        _require(profile is not None, "sealed root profile is missing")
        observed = RootScopeMembershipReader(connection).recover(profile)
        issuers = {r.witness.issuer_reference for r in observed}
        _require(len(issuers) == 1, "initial membership issuer conflicts")
        members = i5._recover_members(connection, intent, profile, next(iter(issuers)))
        closure = i5._closure(intent, profile, members)
        _require(closure is not None, "initial membership closure is incomplete")
        plans = tuple(p.payload() for p in intent.runtime_plans)
        runtimes = tuple(i5._runtime_scope(p) for p in plans)
        i7._validate_scope_bindings(connection, runtimes)
        routes = tuple(i7.NativeFabricRoutingScope(runtime, i7.UUID(p["scope_plan"]["motif_alias_namespace_id"]),
            i7.UUID(p["scope_plan"]["motif_identity_namespace_id"]), i7.UUID(p["scope_plan"]["membership_identity_namespace_id"]),
            i7.UUID(p["scope_plan"]["idempotency_namespace_id"])) for p, runtime in zip(plans, runtimes, strict=True))
        i7._validate_production_routing_scopes(connection, routes)
        for table, expected in i3.genesis_prerequisites(intent).items():
            identifier, key = i3.CATALOG_COLUMNS[table]
            actual = {str(i7.UUID(bytes=row[0])): row[1] for row in connection.execute(f"SELECT {identifier},{key} FROM {table}")}
            _require(all(actual.get(identity) == name for identity, name in expected.items()), "native catalog changed")
        native_seed = i4._versioned_seed_result(intent, i4._recover_seeds(connection, intent))
        character = i6._character_completion(intent, native_seed)
        _require(i6._completion(record, (metadata, closure, character)) == completion, "sealed completion differs from durable truth")
        _require(not connection.execute("PRAGMA foreign_key_check").fetchone(), "native foreign-key closure conflicts")
    i7._verify_external(root, completion)
    owners = i6._OwnerReads(root, intent)
    expected = [i3.GenesisAdministration._reference(owners, "native-core-preparation", i3._bootstrap_manifest(intent))]
    for table, rows in i3.genesis_prerequisites(intent).items():
        expected.append(i3.GenesisAdministration._reference(owners, "native-catalog:" + table, dict(table=table, rows=rows)))
    expected.extend(owners.references(native_seed))
    expected.extend(closure.child_references)
    _require(len(record.child_operation_references) == len(expected) and set(record.child_operation_references) == set(expected),
        "preparation references disagree with durable truth")


def _transition_inventory(root, record):
    allowed = i3._recovery_paths(record.expanded_intent, record)
    paths = list(i4._owner_paths(record.expanded_intent))
    paths += [p.with_name(f".{p.name}.publication.lock") for p in paths]
    deployment = selector.selector_paths(root)
    paths += [deployment.marker_path.relative_to(root), deployment.selector_path.relative_to(root)]
    paths += [deployment.selector_path.with_name(deployment.selector_path.name + suffix).relative_to(root)
              for suffix in ("-wal", "-shm", "-journal")]
    for path in paths:
        allowed[path.as_posix()] = False
        for parent in path.parents:
            allowed[parent.as_posix()] = True
    entries = i3._inventory(root, publication_targets=i4._owner_paths(record.expanded_intent), selector_marker_residue=True)
    initialization_coordination = set()
    # The qualified selector owner may retain its publication hard link on
    # Windows while SQLite handles are open. It is the same file, not another
    # selector. Never open it as authority, remove it, or accept a copied DB.
    for name in entries:
        path = root / name
        if path.parent == deployment.deployment_root and re.fullmatch(r"\.selector-init-[0-9a-f]{32}\.sqlite", path.name):
            _require(deployment.selector_path.is_file() and path.samefile(deployment.selector_path), "foreign selector initialization residue")
            allowed[name] = False
            initialization_coordination.add(name)
            for suffix in ("-shm", "-wal"):
                sidecar = name + suffix
                if sidecar in entries:
                    _require(suffix == "-shm" or (root / sidecar).stat().st_size == 0, "uncommitted selector initialization WAL")
                    allowed[sidecar] = False
                    initialization_coordination.add(sidecar)
    _require(all(name in allowed and facts[0] == allowed[name] for name, facts in entries.items()), "undeclared activation artifact")
    for name in entries:
        _require(not name.endswith(("-wal", "-shm", "-journal")) or name.rsplit("-", 1)[0] in entries, "orphan SQLite sidecar")
    _require(not (root / i3.PRIVATE_CORE).exists(), "incomplete core publication")
    manifest = root / i3.PRIVATE_MANIFEST
    _require(not manifest.exists() or strict_object(manifest.read_bytes()) == i3._bootstrap_manifest(record.expanded_intent),
        "bootstrap manifest conflicts")
    return {name: facts for name, facts in entries.items()
            if name not in initialization_coordination and not name.endswith("-shm")
            and not (name.endswith("-wal") and len(facts) == 6 and facts[3] == 0)}


@dataclass(frozen=True)
class _State:
    record: object
    raw: bytes
    completion: NativeGenesisCompletionWitness
    marker: bool
    states: tuple
    inert_witness: object
    receipts: tuple
    fingerprint: object


def _read_state(root, intent, keys):
    record = read_genesis_operation_record(data_root=root)
    _require(record is not None and record.expanded_intent == intent and
        record.administrative_phase in (_SEALED, _CORE, _DONE), "requires the exact sealed or activated Genesis record")
    raw = _record_path(root).read_bytes()
    _require(raw == owner_bytes(record.payload()), "administrative record is not exact canonical evidence")
    paths = selector.selector_paths(root)
    marker = i3.checked_stat(i7._checked_path(root, paths.marker_path)) is not None
    database = i3.checked_stat(i7._checked_path(root, paths.selector_path)) is not None
    _require(marker or not database, "selector exists without its marker")
    if marker:
        selector._read_marker(paths)
    ledger = []
    if database:
        with closing(selector._open_selector(paths.selector_path, writable=False)) as connection:
            _, ledger = selector._validated_selector(connection)
    _require(len(ledger) <= 3, "unexpected selector transition history")
    relative = intent.payload()["allocations"]["core_relative_path"]
    inspection = core.inspect_contained_core_deployment(data_root=root, core_relative_path=relative)
    completion = record.sealed_completion_payload
    if completion is None and record.administrative_phase in (_CORE, _DONE):
        completion = inspection.activation_completion_witness
    _require(isinstance(completion, NativeGenesisCompletionWitness) and completion.expanded_intent == intent,
        "requires the exact fresh completion")
    path = core.contained_core_path(data_root=root, core_relative_path=relative, require_exists=True)
    with closing(core._open_readonly_core(path)) as connection:
        events = core._core_events(connection, inspection.core_id)
        _require(connection.execute("SELECT COUNT(*) FROM maintenance_events").fetchone()[0] == len(events) <= 2,
            "foreign core maintenance evidence")
        if events:
            inert = core._witness_from_event_result(events[0]["previous"])
        else:
            inert = core.staging_legacy_witness(inspection, descriptor_digest=completion.admission_identity_digest,
                profile_digest=completion.profile_digest)
        _require(inert.core_role == "STAGING" and inert.deployment_state is DeploymentState.LEGACY_ACTIVE
            and inert.core_id == completion.native_core_id and inert.descriptor_digest == completion.admission_identity_digest
            and inert.profile_digest == completion.profile_digest and (inert.schema_id, inert.schema_major, inert.schema_minor)
            == (completion.schema_id, completion.schema_major, completion.schema_minor), "inert predecessor conflicts")
        receipts, predecessor = [], inert
        for index, event in enumerate(events):
            role, kind = (("core-cutover-pending", "ENTER_CUTOVER_PENDING"), ("core-activate", "ACTIVATE_CORE"))[index]
            expected = core._intent(transition_kind=kind, expected_witness=predecessor, selector_generation=1,
                selector_witness_digest=inert.digest, operation_key=keys[role], completion_witness=completion if index else None)
            _require(event["canonical_intent"] == expected, "core transition belongs to another activation intent")
            receipt = core._recover_existing_transition(inspection=inspection,
                event=core._event_for_operation(connection, keys[role]), expected_intent=expected)
            _require(receipt.witness == core._result_witness(predecessor, kind), "core transition result conflicts")
            receipts.append(receipt)
            predecessor = receipt.witness
    states = tuple(selector._state_from_ledger(row, prefix="new") for row in ledger)
    active = receipts[1] if len(receipts) == 2 else None
    for index, (row, state) in enumerate(zip(ledger, states, strict=True)):
        role = ("selector-initialize", "selector-cutover-pending", "selector-activate")[index]
        expected = _selector_intent(role, keys, completion, active)
        _require(row["operation_key"] == keys[role] and row["intent"] == expected and row["reason_kind"] == expected["kind"],
            "selector transition belongs to another activation intent")
        projection = dict(generation=index, deployment_state=("LEGACY_ACTIVE", "CUTOVER_PENDING", "NATIVE_ACTIVE")[index],
            core_id=None, core_relative_path=None, descriptor_digest=None, profile_digest=None, core_witness_digest=None)
        if index:
            projection.update(core_id=str(completion.native_core_id), core_relative_path=relative,
                descriptor_digest=completion.admission_identity_digest, profile_digest=completion.profile_digest,
                core_witness_digest=inert.digest if index == 1 else active.witness.digest)
        _require(_selector_projection(state) == projection, "selector result conflicts")
    _require((len(states) >= 2 or not receipts) and (len(states) != 3 or active is not None), "deployment transition order conflicts")
    refs = () if active is None else (_core_reference(active, keys),)
    if record.administrative_phase is _SEALED:
        _require(not record.final_activation_references and record.sealed_completion_payload == completion, "sealed cache conflicts")
    else:
        _require(active is not None, "activated checkpoint has no committed core activation")
        if record.administrative_phase is _DONE:
            _require(len(states) == 3, "completed checkpoint has no active selector")
            refs += (_selector_reference(states[2], ledger[2]["intent"], keys),)
        _require(record.final_activation_references == refs, "administrative activation references conflict")
    if not marker:
        before = i6._inspect(root, intent)
        _require(i6._completion(record, i6._read_truth(root, record)) == completion, "sealed I6 truth changed")
        _require(i6._inspect(root, intent) == before, "sealed root changed during verification")
    else:
        _transition_truth(root, record, completion)
    if len(states) == 3:
        _full_agreement(root, intent, completion)
        fingerprint = None
    else:
        _require(read_genesis_fence(data_root=root).value == "BLOCK_LEGACY", "unpublished Genesis fence changed")
        fingerprint = _transition_inventory(root, record)
    _require(_record_path(root).read_bytes() == raw, "administrative predecessor changed during verification")
    return _State(record, raw, completion, marker, states, inert, tuple(receipts), fingerprint)


def _full_agreement(root, intent, completion):
    authority = i7.verify_active_native_genesis(data_root=root, expected_intent=intent)
    _require(authority is not None and authority.completion == completion, "active Genesis agreement conflicts")
    i7.recover_active_native_genesis(data_root=root, expected_completion=completion)
    _require(read_genesis_fence(data_root=root).value == "NATIVE_AUTHORITY_WINS", "native authority does not outrank administration")
    agreement = selector.resolve_deployment_agreement(data_root=root, effective_profile=completion.qualified_deployment_profile)
    _require(agreement.mode is DeploymentResolutionMode.NATIVE_AGREEMENT, "deployment resolution is not native agreement")


@dataclass(frozen=True)
class GenesisActivationResult:
    completion: NativeGenesisCompletionWitness
    operation_record: object
    core_result: core.CoreMaintenanceResult
    selector_state: object


def activate_genesis(*, data_root, intent: GenesisIntent, observer=None, operator_attestation=None,
                     issuer_reference=None, timeout_seconds=1.0, fault=i3._noop, held_lock=None):
    """Activate/recover one sealed root using a live local operator observation.

    Already active replay performs reads and, if needed, administrative closeout
    only. The observer is not called then. The fault callback is for qualification
    at completed API boundaries; marker-only death must wrap the marker owner.
    """
    root = canonical_genesis_root(data_root)
    _require(isinstance(intent, GenesisIntent) and intent.data_root_identity == str(root), "requires the canonical explicit root intent")
    keys = activation_operation_keys(intent)
    initialize_key = keys["selector-initialize"]
    with i3.root_observation(data_root=root, timeout_seconds=timeout_seconds, held_lock=held_lock) as held:
        record = held.observe(read_genesis_operation_record, data_root=root)
        _require(record is not None and record.expanded_intent == intent and record.administrative_phase in (_SEALED, _CORE, _DONE),
            "requires an existing sealed Genesis operation")
        state = held.observe(_read_state, root, intent, keys)
        if len(state.states) < 3:
            _require(callable(observer), "activation requires a fresh writer observation")
            since = time.time_ns()
            facts = observer(root, intent)
            _require(isinstance(facts, i3.GenesisWriterObservation), "requires a typed writer observation")
            facts.evidence(intent, since_ns=since, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
            _require(held.observe(_read_state, root, intent, keys) == state, "root changed during activation-time observation")
        while True:
            completion = state.completion
            arguments = dict(data_root=root, core_relative_path=completion.core_relative_path)
            if not state.states:
                selector.establish_selector_era(data_root=root)
                selector.initialize_selector(data_root=root, operation_key=initialize_key)
                fault("after-selector-initialization")
            elif len(state.states) == 1:
                selector.begin_cutover_pending(**arguments, descriptor_digest=completion.admission_identity_digest,
                    profile=completion.qualified_deployment_profile, expected_generation=0, operation_key=keys["selector-cutover-pending"])
                fault("after-selector-pending")
            elif not state.receipts:
                core.enter_cutover_pending(**arguments, expected_witness=state.inert_witness, selector_generation=1,
                    selector_witness_digest=state.states[1].core_witness_digest, operation_key=keys["core-cutover-pending"])
                fault("after-core-pending")
            elif len(state.receipts) == 1:
                core.activate_core(**arguments, expected_witness=state.receipts[0].witness, selector_generation=1,
                    selector_witness_digest=state.states[1].core_witness_digest, operation_key=keys["core-activate"], completion_witness=completion)
                fault("after-core-activation")
            elif state.record.administrative_phase is _SEALED:
                fault("before-core-activated-checkpoint")
                _require(held.observe(_read_state, root, intent, keys) == state, "core checkpoint predecessor changed")
                successor = replace(state.record, administrative_phase=_CORE, phase_revision=state.record.phase_revision + 1,
                    final_activation_references=(_core_reference(state.receipts[1], keys),))
                replace_if_exact_predecessor(_record_path(root), state.raw, owner_bytes(successor.payload()))
                fault("after-core-activated-checkpoint")
            elif len(state.states) == 2:
                selector.activate_selector_native(**arguments, core_result=state.receipts[1], expected_generation=1,
                    operation_key=keys["selector-activate"], disposition_execution_receipt_digest=None)
                _full_agreement(root, intent, completion)
                fault("after-selector-activation")
            elif state.record.administrative_phase is _CORE:
                fault("before-completed-checkpoint")
                _require(held.observe(_read_state, root, intent, keys) == state, "completed checkpoint predecessor changed")
                activation_intent = _selector_intent("selector-activate", keys, completion, state.receipts[1])
                successor = replace(state.record, administrative_phase=_DONE, phase_revision=state.record.phase_revision + 1,
                    final_activation_references=(_core_reference(state.receipts[1], keys),
                        _selector_reference(state.states[2], activation_intent, keys)))
                replace_if_exact_predecessor(_record_path(root), state.raw, owner_bytes(successor.payload()))
                fault("after-completed-checkpoint")
            else:
                return GenesisActivationResult(completion, state.record, state.receipts[1], state.states[2])
            state = held.observe(_read_state, root, intent, keys)
