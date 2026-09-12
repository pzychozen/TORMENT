"""Offline I6: reread I1-I5 truth and seal administrative evidence only.

SQLite is opened read-only. The existing root mutex and operator observation
exclude cooperating writers through the final reread and record replacement.
No selector, activation, native publication, planting or model capability is
used here. Sealed replay verifies durable truth without refreshing observations.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import time
from uuid import UUID

from ..atomic_publication import replace_if_exact_predecessor
from ..external_owner_json import owner_bytes, strict_object
from . import genesis_administration as i3
from . import genesis_character_administration as i4
from . import genesis_membership_administration as i5
from .character_seed_witness import character_seed_definition_digest
from .deployment_types import NativeGenesisCompletionWitness
from .genesis_contracts import (
    GenesisAdministrativePhase, GenesisCompletedSeed, GenesisIntent,
    GenesisOperationRecord, GenesisSeedCompletion, initial_membership_closure_digest,
    payload_digest, runtime_plan_digest,
)
from .genesis_fence import (
    GenesisPreparationRefused, canonical_genesis_root, read_genesis_fence,
    read_genesis_operation_record,
)
from .root_scope_membership import RootScopeMembershipReader
from .schema import require_current_schema

_LIVE_SESSION = object()
_PREPARING = GenesisAdministrativePhase.PREPARING
_SEALED = GenesisAdministrativePhase.PREPARATION_SEALED


def _inspect(root, intent):
    """The existing I4/I5 filesystem closure, accepting only I6's two phases."""
    if str(root) != intent.data_root_identity:
        raise GenesisPreparationRefused("I6 intent must name the canonical explicit root")
    record = read_genesis_operation_record(data_root=root)
    if (record is None or record.expanded_intent != intent
        or record.administrative_phase not in (_PREPARING, _SEALED)
        or record.final_activation_references):
        raise GenesisPreparationRefused("I6 requires the exact PREPARING or PREPARATION_SEALED record")
    allowed = i3._recovery_paths(intent, record)
    for path in i4._owner_paths(intent):
        allowed[path.as_posix()] = False
        allowed[path.with_name(f".{path.name}.publication.lock").as_posix()] = False
        for parent in path.parents:
            allowed[parent.as_posix()] = True
    entries = i3._inventory(root, publication_targets=i4._owner_paths(intent),
        selector_marker_residue=record.administrative_phase is _SEALED)
    if any(name not in allowed or facts[0] != allowed[name] for name, facts in entries.items()):
        raise GenesisPreparationRefused("I6 contains an undeclared artifact, selector or marker")
    for name in entries:
        if name.endswith(("-wal", "-shm", "-journal")) and name.rsplit("-", 1)[0] not in entries:
            raise GenesisPreparationRefused("I6 orphan SQLite sidecar")
    if (root / i3.PRIVATE_CORE).exists():
        raise GenesisPreparationRefused("I6 cannot resume an incomplete I3 core publication")
    manifest = root / i3.PRIVATE_MANIFEST
    if manifest.exists() and strict_object(manifest.read_bytes()) != i3._bootstrap_manifest(intent):
        raise GenesisPreparationRefused("I6 bootstrap manifest conflicts")
    core = root / i3.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]
    if not core.is_file() or read_genesis_fence(data_root=root).value != "BLOCK_LEGACY":
        raise GenesisPreparationRefused("I6 requires the prepared core and unchanged Genesis fence")
    raw = (root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME).read_bytes()
    if GenesisOperationRecord.from_payload(strict_object(raw)) != record:
        raise GenesisPreparationRefused("I6 record changed during inspection")
    if record.administrative_phase is _SEALED and raw != owner_bytes(record.payload()):
        raise GenesisPreparationRefused("I6 sealed record bytes differ from the canonical administrative seal")
    # Standard mode=ro WAL readers can recreate coordination files after the
    # last writer closes. Type/path checks above include every sidecar. Only
    # shared memory and a zero-byte WAL are excluded from the authority change
    # fingerprint; main DB, nonempty WAL, and external/administrative bytes keep
    # their complete fingerprints. No immutable=1 shortcut can ignore WAL data.
    durable = {name: facts for name, facts in entries.items()
               if not name.endswith("-shm") and not (name.endswith("-wal") and len(facts) == 6 and facts[3] == 0)}
    return record, raw, durable


@dataclass(frozen=True)
class _OwnerReads:
    """Carrier for existing pure checkpoint projections and strict owner reads."""
    root: Path
    intent: GenesisIntent

    _reference = i4.GenesisCharacterAdministration._reference
    references = i4.GenesisCharacterAdministration._references
    verify_external = i4.GenesisCharacterAdministration._verify_external


def _character_projections(intent, native_result):
    """Documented source-family and result projections with distinct digest domains.

    The source projection cross-binds the Genesis declaration digest and the
    existing native Character digest. The result projection names the latter
    explicitly and retains every ordered source field from the recovered result.
    Neither projection is a durable operation ledger or a new completion type.
    """
    value = intent.payload()
    definition = value["character"]["definition"]
    seed = i4._seed(intent)
    if seed is None or {key: seed.to_dict()[key] for key in definition} != definition:
        raise GenesisPreparationRefused("I6 reconstructed Character declaration conflicts")
    genesis_digest = payload_digest(definition)
    native_digest = character_seed_definition_digest(seed)
    if native_result is None or native_result.seed_definition_digest != native_digest or native_result.state != "COMPLETE":
        raise GenesisPreparationRefused("I6 native Character definition digest or completion conflicts")
    config = i4._configuration(intent, i5._CommittedLane(intent))
    private = next(p.payload() for p in intent.runtime_plans if p.payload()["scope_key"]["scope_kind"] == "PRIVATE")
    source = dict(parent_native_operation_key=config.parent_native_operation_key,
        workspace_id=config.workspace_id, agent_id=config.agent_id, domain_id=config.domain_id,
        seed_id=seed.seed_id, genesis_definition_digest=genesis_digest,
        native_character_definition_digest=native_digest,
        ordered_seed_concepts=list(i4._split_seed_text(seed.seed_text)),
        private_routing_allocation=private["scope_plan"], representation_lane=value["representation_lane"])
    result = dict(native_character_definition_digest=native_result.seed_definition_digest,
        seed_eids=list(native_result.seed_eids), seed_motif_id=native_result.seed_motif_id,
        seed_motif_object_id=str(native_result.seed_motif_object_id),
        ordered_source_results=[i4._json_result(asdict(s)) for s in native_result.sources],
        state=native_result.state)
    return source, result


def _character_completion(intent, native_result):
    if intent.payload()["character"]["mode"] == "DISABLED":
        if native_result is not None:
            raise GenesisPreparationRefused("I6 disabled Character has a native result")
        return GenesisSeedCompletion.from_payload({"mode": "DISABLED"})
    source, result = _character_projections(intent, native_result)
    return GenesisCompletedSeed.from_payload(dict(mode="ENABLED", status="COMPLETED",
        definition_digest=source["genesis_definition_digest"],
        source_operation_key=source["parent_native_operation_key"], source_intent_digest=payload_digest(source),
        result_digest=payload_digest(result), seed_eids=result["seed_eids"], seed_motif_id=result["seed_motif_id"],
        representation_ids=[s["representation_id"] for s in result["ordered_source_results"]]))


def _read_truth(root, record):
    """Always reopen native and external owners; administrative references verify outputs."""
    intent = record.expanded_intent
    core = root / i3.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]
    with closing(i3._open_readonly(core)) as connection:
        metadata = require_current_schema(connection)
        profile = i5._recover_profile(connection, intent)
        if profile is None:
            raise GenesisPreparationRefused("I6 requires the committed I5 root profile")
        observed = RootScopeMembershipReader(connection).recover(profile)
        issuers = {r.witness.issuer_reference for r in observed}
        if len(issuers) != 1:
            raise GenesisPreparationRefused("I6 requires one exact I5 membership issuer")
        # The issuer is recovered from native witnesses, then cross-checked
        # against the immutable I5 closure references below. It is not the
        # potentially different issuer of this final quiescence observation.
        members = i5._recover_members(connection, intent, profile, next(iter(issuers)))
        native_seed = i5._verify_core(connection, intent, profile, members)
        closure = i5._closure(intent, profile, members)
        if closure is None:
            raise GenesisPreparationRefused("I6 requires complete I5 membership closure")
        if connection.execute("SELECT 1 FROM maintenance_events LIMIT 1").fetchone():
            raise GenesisPreparationRefused("I6 core maintenance evidence must remain empty")
    owners = _OwnerReads(root, intent)
    owners.verify_external(native_seed)
    expected = [i3.GenesisAdministration._reference(owners, "native-core-preparation", i3._bootstrap_manifest(intent))]
    for table, rows in i3.genesis_prerequisites(intent).items():
        expected.append(i3.GenesisAdministration._reference(owners, "native-catalog:" + table, dict(table=table, rows=rows)))
    expected.extend(owners.references(native_seed))
    expected.extend(closure.child_references)
    if len(record.child_operation_references) != len(expected) or set(record.child_operation_references) != set(expected):
        raise GenesisPreparationRefused("I6 I3/I4/I5 checkpoints disagree with complete durable truth")
    return metadata, closure, _character_completion(intent, native_seed)


def _completion(record, truth):
    metadata, closure, character = truth
    intent = record.expanded_intent
    value = intent.payload()
    members = tuple(sorted(closure.initial_memberships, key=lambda m: m.canonical_key))
    membership_digest = initial_membership_closure_digest(closure.root_profile, intent.runtime_plans, members)
    if membership_digest != closure.initial_membership_closure_digest:
        raise GenesisPreparationRefused("I6 canonical completion order changes I5 closure")
    profile = closure.qualified_deployment_profile
    payload = dict(contract=NativeGenesisCompletionWitness.CONTRACT, version=NativeGenesisCompletionWitness.VERSION,
        origin=NativeGenesisCompletionWitness.ORIGIN, data_root_identity=intent.data_root_identity,
        operation_key=intent.operation_key, intent_digest=intent.digest, expanded_intent=value,
        accepted_start_observation=record.accepted_start_observation.payload(), native_core_id=str(UUID(bytes=metadata.core_id)),
        core_relative_path=value["allocations"]["core_relative_path"], schema_id=metadata.schema_id,
        schema_major=metadata.schema_major, schema_minor=metadata.schema_minor,
        qualified_deployment_profile=asdict(profile), qualified_deployment_profile_digest=profile.digest,
        representation_lane=value["representation_lane"], root_profile=closure.root_profile.payload(),
        runtime_scope_plans=[p.payload() for p in intent.runtime_plans], runtime_plan_digest=runtime_plan_digest(intent.runtime_plans),
        external_owner_projection=intent.external_owner_projection(),
        external_owner_closure_digest=payload_digest(intent.external_owner_projection()), character_seed_completion=character.payload(),
        initial_memberships=[m.payload() for m in members], initial_membership_closure_digest=membership_digest,
        quiescence_evidence_digest=payload_digest({"quiescence_observations": [v.payload() for v in record.quiescence_observations]}))
    payload["preparation_result_digest"] = payload_digest(payload)
    completion = NativeGenesisCompletionWitness.from_payload(payload)
    if (NativeGenesisCompletionWitness.from_payload(completion.payload()) != completion
        or completion.admission_identity_digest != intent.digest or completion.native_core_id.bytes != metadata.core_id
        or completion.profile_digest != profile.digest or completion.qualified_profile_payload() != asdict(profile)
        or completion.external_owner_closure_digest != profile.external_owner_digest):
        raise GenesisPreparationRefused("I6 completion round-trip or common binding conflicts")
    return completion


@dataclass(frozen=True)
class GenesisCompletionSealResult:
    completion: NativeGenesisCompletionWitness
    operation_record: GenesisOperationRecord

    @property
    def qualified_profile_payload(self):
        """Detached seven-field operator/configuration evidence, not authority."""
        return self.completion.qualified_profile_payload()


class GenesisCompletionAdministration:
    """I6-only session; use begin_genesis_completion_administration."""
    def __init__(self, root, intent, record, fault=i3._noop):
        self.root, self.intent, self.record, self.fault = root, intent, record, fault
        self._lease = None
        self._held_lock = None

    def _current(self):
        if self._lease is not _LIVE_SESSION:
            raise GenesisPreparationRefused("I6 requires a live root-onboarding lock session")
        if self._held_lock is None:
            raise GenesisPreparationRefused("I6 requires a live root-onboarding lock acquisition")
        current = self._held_lock.observe(_inspect, self.root, self.intent)
        if current[0] != self.record:
            raise GenesisPreparationRefused("I6 administrative predecessor changed")
        return current

    def _recover_sealed(self):
        record, raw, before = self._current()
        if record.administrative_phase is not _SEALED:
            raise GenesisPreparationRefused("I6 sealed recovery requires PREPARATION_SEALED")
        actual = _completion(record, _read_truth(self.root, record))
        if actual != record.sealed_completion_payload:
            raise GenesisPreparationRefused("I6 sealed completion conflicts with durable truth")
        if self._current() != (record, raw, before):
            raise GenesisPreparationRefused("I6 sealed root changed during read-only recovery")
        return GenesisCompletionSealResult(record.sealed_completion_payload, record)

    def seal_preparation(self, *, observer=None, operator_attestation=None, issuer_reference=None):
        record, raw, before = self._current()
        if record.administrative_phase is _SEALED:
            return self._recover_sealed()
        _read_truth(self.root, record)  # preconditions only; never reuse these results
        if not callable(observer):
            raise GenesisPreparationRefused("I6 sealing requires a fresh writer observation")
        since = time.time_ns()
        facts = observer(self.root, self.intent)
        if not isinstance(facts, i3.GenesisWriterObservation):
            raise GenesisPreparationRefused("I6 requires a typed writer observation")
        evidence = facts.evidence(self.intent, since_ns=since,
            operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        if self._current() != (record, raw, before):
            raise GenesisPreparationRefused("I6 root changed during final observation")
        # Retain the observation and phase transition in one atomic successor.
        # There is no intermediate record write or second revision increment.
        observed = replace(record, quiescence_observations=record.quiescence_observations + (evidence,))
        self.fault("before-final-completion-reread")
        completion = _completion(observed, _read_truth(self.root, observed))
        sealed = replace(observed, administrative_phase=_SEALED, phase_revision=record.phase_revision + 1,
            sealed_completion_payload=completion, final_activation_references=())
        if GenesisOperationRecord.from_payload(sealed.payload()) != sealed:
            raise GenesisPreparationRefused("I6 sealed record round-trip conflicts")
        self.fault("before-completion-seal")
        if self._current() != (record, raw, before):
            raise GenesisPreparationRefused("I6 root changed after final verification")
        replace_if_exact_predecessor(self.root / i3.CONTROL_DIRECTORY / i3.RECORD_NAME, raw, owner_bytes(sealed.payload()))
        self.record = sealed
        self.fault("after-completion-seal")
        return self._recover_sealed()


@contextmanager
def begin_genesis_completion_administration(*, data_root: str | Path, intent: GenesisIntent,
                                           timeout_seconds=1.0, fault=i3._noop, held_lock=None):
    root = canonical_genesis_root(data_root)
    with i3.root_observation(data_root=root, timeout_seconds=timeout_seconds, held_lock=held_lock) as held:
        after = held.observe(_inspect, root, intent)
        session = GenesisCompletionAdministration(root, intent, after[0], fault)
        session._held_lock = held
        session._lease = _LIVE_SESSION
        try:
            yield session
        finally:
            session._lease = None
