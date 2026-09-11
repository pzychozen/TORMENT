"""I7 read-only recovery of fresh Genesis deployment and runtime authority.

No administrative record, host profile, migration descriptor, or disposition
receipt supplies deployment authority here. Only the selector and active core's
persisted fresh completion do. Runtime recovery then verifies native membership
and stable external owners without replaying any preparation or activation.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import stat
from uuid import UUID

from ..character import CharacterStore
from ..identity import AgentIdentity, IdentityStore
from ..external_owner_json import exact_json, strict_object
from ..workspace_declaration import WorkspaceDeclaration
from . import deployment_selector as selector
from . import genesis_administration as i3
from . import genesis_character_administration as i4
from . import genesis_membership_administration as i5
from .genesis_completion_administration import _character_completion
from .deployment_core_maintenance import (
    CoreDeploymentInspection, _open_readonly_core, contained_core_path,
    inspect_contained_core_deployment, staging_legacy_witness,
)
from .deployment_types import (
    DeploymentState, NativeGenesisCompletionWitness, SelectorState,
)
from .errors import DeploymentAuthorityError
from .fabric_native_routing import NativeFabricRoutingScope, _validate_production_routing_scopes
from .genesis_contracts import GenesisIntent
from .genesis_fence import canonical_genesis_root, checked_stat
from .migration.existing_workspace_multi_scope_admission import (
    RecoveredActiveExistingWorkspaceNativeMultiScopeScope,
    RecoveredExistingWorkspaceNativeMultiScopeScope,
)
from .native_character_seed_plant import NativeCharacterSeedPlantRequest, NativeCharacterSeedPlantRuntime
from .root_profile import RootProfileGenerationRef, verify_root_profile_generation
from .root_scope_membership import RootScopeMembershipReader
from .runtime_binding import (
    NativeRepresentationLane, _validate_representation_lane, _validate_scope_bindings,
)


class NativeGenesisRecoveryRefused(DeploymentAuthorityError):
    """Contradictory or unavailable fresh authority; never repair or fall back."""


@dataclass(frozen=True)
class ActiveNativeGenesisAuthority:
    data_root: Path
    core_database_path: Path
    selector_state: SelectorState
    core_inspection: CoreDeploymentInspection
    completion: NativeGenesisCompletionWitness


def _checked_path(root, path):
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        info = checked_stat(current)
        if info is not None and current != path and not stat.S_ISDIR(info.st_mode):
            raise NativeGenesisRecoveryRefused("Genesis owner ancestry is not a directory")
    return path


def _completion_binding(root, state, inspection, expected_intent):
    completion, witness = inspection.activation_completion_witness, inspection.witness
    if not isinstance(completion, NativeGenesisCompletionWitness) or witness is None:
        raise NativeGenesisRecoveryRefused("active Genesis requires a persisted fresh completion")
    if (completion.data_root_identity != str(root)
        or completion.native_core_id != inspection.core_id or state.core_id != inspection.core_id
        or completion.core_relative_path != state.core_relative_path
        or completion.admission_identity_digest != state.descriptor_digest
        or completion.admission_identity_digest != witness.descriptor_digest
        or completion.profile_digest != state.profile_digest or completion.profile_digest != witness.profile_digest
        or (completion.schema_id, completion.schema_major, completion.schema_minor)
        != (witness.schema_id, witness.schema_major, witness.schema_minor)
        or (expected_intent is not None and completion.expanded_intent != expected_intent)):
        raise NativeGenesisRecoveryRefused("fresh completion disagrees with selected core, profile or intent")
    return completion


def verify_active_native_genesis(*, data_root, expected_intent: GenesisIntent | None = None):
    """Return exact active authority, or None for an unpublished transition.

    This deliberately does not call the deployment resolver (which calls the
    Genesis fence), require host configuration, or read genesis-operation.json.
    The fence may supply its already-read intent to detect a foreign activation.
    """
    try:
        root = canonical_genesis_root(data_root)
        paths = selector.selector_paths(root)
        marker = checked_stat(_checked_path(root, paths.marker_path))
        database = checked_stat(_checked_path(root, paths.selector_path))
        if marker is None:
            if database is not None:
                raise NativeGenesisRecoveryRefused("Genesis selector has no era marker")
            return None
        selector._read_marker(paths)
        if database is None:
            return None  # interrupted adjacent marker/initialization step
        state = selector.read_selector_state(data_root=root)
        if state.deployment_state is DeploymentState.LEGACY_ACTIVE:
            if expected_intent is not None:
                allocated = expected_intent.payload()["allocations"]["core_relative_path"]
                inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=allocated)
                if inspection.core_role != "STAGING" or inspection.deployment_state is not DeploymentState.LEGACY_ACTIVE:
                    raise NativeGenesisRecoveryRefused("legacy Genesis selector has a non-inert core")
            return None
        core_path = contained_core_path(data_root=root, core_relative_path=state.core_relative_path, require_exists=True)
        _checked_path(root, core_path)
        inspection = inspect_contained_core_deployment(data_root=root, core_relative_path=state.core_relative_path)
        if state.core_id != inspection.core_id:
            raise NativeGenesisRecoveryRefused("Genesis selector points at another core")
        if expected_intent is not None:
            allocation = expected_intent.payload()["allocations"]
            if (state.core_id != UUID(allocation["core_id"])
                or state.core_relative_path != allocation["core_relative_path"]
                or state.descriptor_digest != expected_intent.digest
                or state.profile_digest != i5.qualified_genesis_profile(expected_intent).digest):
                raise NativeGenesisRecoveryRefused("Genesis transition disagrees with the frozen intent")
        if state.deployment_state is DeploymentState.CUTOVER_PENDING:
            if inspection.deployment_state is DeploymentState.LEGACY_ACTIVE:
                witness = staging_legacy_witness(inspection, descriptor_digest=state.descriptor_digest,
                    profile_digest=state.profile_digest)
                if witness.digest != state.core_witness_digest:
                    raise NativeGenesisRecoveryRefused("Genesis pending selector has a conflicting predecessor")
            else:
                witness = inspection.witness
                if (witness is None or witness.descriptor_digest != state.descriptor_digest
                    or witness.profile_digest != state.profile_digest):
                    raise NativeGenesisRecoveryRefused("Genesis pending core witness conflicts")
                if inspection.deployment_state is DeploymentState.NATIVE_ACTIVE:
                    _completion_binding(root, state, inspection, expected_intent)
            return None  # includes core activation response loss before selector finalization
        if (state.deployment_state is not DeploymentState.NATIVE_ACTIVE
            or inspection.core_role != "ACTIVE_CORE" or inspection.deployment_state is not DeploymentState.NATIVE_ACTIVE
            or inspection.witness is None or state.core_witness_digest != inspection.witness.digest):
            raise NativeGenesisRecoveryRefused("Genesis selector/core active agreement is incomplete")
        completion = _completion_binding(root, state, inspection, expected_intent)
        activation = selector.read_selector_native_activation_intent(data_root=root)
        if (activation.get("activation_maintenance_id") != str(inspection.latest_maintenance_id)
            or activation.get("disposition_execution_receipt_digest") is not None):
            raise NativeGenesisRecoveryRefused("Genesis selector activation receipt conflicts")
        if selector.read_selector_state(data_root=root) != state:
            raise NativeGenesisRecoveryRefused("Genesis selector changed during authority recovery")
        return ActiveNativeGenesisAuthority(root, core_path, state, inspection, completion)
    except NativeGenesisRecoveryRefused:
        raise
    except Exception as exc:
        raise NativeGenesisRecoveryRefused("fresh Genesis deployment evidence is invalid or unavailable") from exc


@dataclass(frozen=True)
class _GenesisWorkspacePlan:
    """Completion-derived compatibility view; no admission descriptor is read."""
    admission_identity_digest: str
    payload: dict

    @property
    def digest(self):
        return self.admission_identity_digest


@dataclass(frozen=True)
class RecoveredNativeGenesisWorkspace:
    native_core_database_path: Path
    native_core_id: UUID
    workspace_id: str
    representation_lane: NativeRepresentationLane
    descriptor: _GenesisWorkspacePlan
    scopes: tuple[RecoveredActiveExistingWorkspaceNativeMultiScopeScope, ...]

    def lookup_private(self, agent_id):
        return self._lookup("PRIVATE_AGENT", agent_id)

    def lookup_shared(self, domain_id):
        return self._lookup("SHARED_DOMAIN", domain_id)

    def _lookup(self, kind, qualifier):
        found = [s for s in self.scopes if s.memory_runtime_scope.scope_kind == kind
                 and s.memory_runtime_scope.qualifier == qualifier]
        if len(found) != 1:
            raise NativeGenesisRecoveryRefused("Genesis workspace scope is absent or ambiguous")
        return found[0]


def _verify_external(root, completion):
    intent = completion.expanded_intent
    value = intent.payload()
    workspace, agent = value["workspace"], value["agent"]
    created, lane = value["creation_facts"], value["representation_lane"]
    declaration = WorkspaceDeclaration(workspace["workspace_id"], created["workspace_created_ts"],
        lane["dimension"], lane["provider"], lane["model"], tuple(workspace["ordered_domains"]))
    paths = tuple(_checked_path(root, root / path) for path in i4._owner_paths(intent))
    for path, wanted in zip(paths[:2], (declaration.metadata_payload(), declaration.domain_payload()), strict=True):
        if exact_json(strict_object(path.read_bytes())) != exact_json(wanted):
            raise NativeGenesisRecoveryRefused("Genesis workspace declaration changed")
    # Use the existing owner's strict decoder and continuing stable projection.
    # IdentityStore.__init__ creates directories, so recovery uses no constructor.
    identity = IdentityStore.identity_from_strict_json(paths[2].read_bytes())
    expected = AgentIdentity(workspace["workspace_id"], agent["agent_id"], agent["identity_seed"],
        agent["initial_overlay"], created["identity_created_ts"], created["identity_created_ts"])
    if exact_json(IdentityStore.stable_identity_projection(identity)) != exact_json(IdentityStore.stable_identity_projection(expected)):
        raise NativeGenesisRecoveryRefused("Genesis stable identity changed")
    if value["character"]["mode"] == "ENABLED":
        seed = CharacterStore.seed_from_strict_json(paths[-1].read_bytes())
        evidence = completion.character_seed_completion.payload()
        if (exact_json(CharacterStore.stable_seed_projection(seed)) != exact_json(CharacterStore.stable_seed_projection(i4._seed(intent)))
            or seed.seed_eids != evidence["seed_eids"] or seed.seed_motif_id != evidence["seed_motif_id"]):
            raise NativeGenesisRecoveryRefused("Genesis Character declaration or linkage changed")


def recover_active_native_genesis(*, data_root, workspace_id=None, expected_completion=None):
    """Recover exact completion/profile/membership/Character/runtime facts.

    None workspace performs full validation for owner construction. An explicit
    workspace returns existing runtime wrappers with the standard router shape.
    Normal runtime objects may evolve; initial profile/membership and committed
    seed evidence remain exact. This is not the I5 empty-installation verifier.
    """
    try:
        authority = verify_active_native_genesis(data_root=data_root)
        if authority is None:
            raise NativeGenesisRecoveryRefused("Genesis runtime requires fully active native authority")
        completion = authority.completion
        if expected_completion is not None and completion != expected_completion:
            raise NativeGenesisRecoveryRefused("Genesis owner completion became stale")
        intent = completion.expanded_intent
        plans = tuple(p.payload() for p in completion.runtime_scope_plans)
        runtimes = tuple(i5._runtime_scope(p) for p in plans)
        routes = tuple(NativeFabricRoutingScope(scope, UUID(p["scope_plan"]["motif_alias_namespace_id"]),
            UUID(p["scope_plan"]["motif_identity_namespace_id"]), UUID(p["scope_plan"]["membership_identity_namespace_id"]),
            UUID(p["scope_plan"]["idempotency_namespace_id"])) for p, scope in zip(plans, runtimes, strict=True))
        lane = NativeRepresentationLane(**intent.payload()["representation_lane"])
        claimed = completion.root_profile.payload()
        profile = RootProfileGenerationRef(**{k: UUID(v) if k.endswith("_id") else v for k, v in claimed.items()})
        with closing(_open_readonly_core(authority.core_database_path)) as connection:
            verify_root_profile_generation(connection, profile)
            if i5._recover_profile(connection, intent) != profile:
                raise NativeGenesisRecoveryRefused("Genesis root profile differs from completion")
            records = RootScopeMembershipReader(connection).recover(profile)
            issuers = {r.witness.issuer_reference for r in records}
            if len(issuers) != 1:
                raise NativeGenesisRecoveryRefused("Genesis initial membership witnesses disagree")
            members = i5._recover_members(connection, intent, profile, next(iter(issuers)))
            closure = i5._closure(intent, profile, members)
            if (closure is None or tuple(sorted(closure.initial_memberships, key=lambda m: m.canonical_key)) != completion.initial_memberships
                or closure.initial_membership_closure_digest != completion.initial_membership_closure_digest
                or closure.qualified_deployment_profile != completion.qualified_deployment_profile):
                raise NativeGenesisRecoveryRefused("Genesis initial membership closure changed")
            _validate_representation_lane(lane)
            _validate_scope_bindings(connection, runtimes)
            _validate_production_routing_scopes(connection, routes)
            for table, expected in i3.genesis_prerequisites(intent).items():
                identifier, key = i3.CATALOG_COLUMNS[table]
                actual = {str(UUID(bytes=row[0])): row[1] for row in connection.execute(f"SELECT {identifier},{key} FROM {table}")}
                if any(actual.get(identity) != name for identity, name in expected.items()):
                    raise NativeGenesisRecoveryRefused("Genesis runtime catalog allocation changed")
            native_seed = None
            seed = i4._seed(intent)
            if seed is not None:
                config = i4._configuration(intent, i5._CommittedLane(intent))
                native_seed = NativeCharacterSeedPlantRuntime(connection, configuration=config).recover_completed_seed(NativeCharacterSeedPlantRequest(seed))
            if _character_completion(intent, native_seed) != completion.character_seed_completion:
                raise NativeGenesisRecoveryRefused("Genesis committed Character completion changed")
        _verify_external(authority.data_root, completion)
        if verify_active_native_genesis(data_root=authority.data_root) != authority:
            raise NativeGenesisRecoveryRefused("Genesis deployment changed during runtime recovery")
        if workspace_id is None:
            return authority
        selected = [(p, scope, routing) for p, scope, routing in zip(plans, runtimes, routes, strict=True)
                    if scope.workspace_id == workspace_id]
        if not isinstance(workspace_id, str) or not workspace_id or not selected:
            raise NativeGenesisRecoveryRefused("Genesis workspace is not explicitly admitted")
        scopes = tuple(RecoveredActiveExistingWorkspaceNativeMultiScopeScope(RecoveredExistingWorkspaceNativeMultiScopeScope(
            authority.core_database_path, completion.native_core_id, lane, scope, routing)) for _, scope, routing in selected)
        descriptor = _GenesisWorkspacePlan(completion.admission_identity_digest, {"lanes": [
            {"plan": {**p["scope_plan"], "agent_id": p["scope_key"]["agent_id"], "domain_id": p["scope_key"]["domain_id"]}}
            for p, _, _ in selected]})
        return RecoveredNativeGenesisWorkspace(authority.core_database_path, completion.native_core_id,
            workspace_id, lane, descriptor, scopes)
    except NativeGenesisRecoveryRefused:
        raise
    except Exception as exc:
        raise NativeGenesisRecoveryRefused("fresh Genesis runtime evidence is invalid or unavailable") from exc
