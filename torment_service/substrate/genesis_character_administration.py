"""Offline I4 extension: first external owners and native Character seed only.

I3's start classifier, preparation operation and fence remain unchanged. This
separate session accepts only an already prepared I3 root and its bounded I4
continuation, under the same I3 OS mutex and quiescence evidence contract.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import time
from uuid import UUID

from ..character import CharacterSeed, CharacterStore, _split_seed_text
from ..identity import AgentIdentity, IdentityStore
from ..workspace_declaration import WorkspaceDeclaration, create_or_verify_workspace_declaration
from . import genesis_administration as i3
from .character_seed_witness import character_seed_definition_digest
from .connection import open_existing_native_core_connection
from .fabric_native_routing import NativeFabricRoutingScope
from .genesis_contracts import GenesisEvidenceReference, GenesisIntent, payload_digest
from .genesis_fence import GenesisPreparationRefused, canonical_genesis_root
from .native_character_seed_plant import (
    NativeCharacterSeedPlantRequest, NativeCharacterSeedPlantResult,
    NativeCharacterSeedPlantRuntime, NativeCharacterSeedPlantRuntimeConfiguration,
)
from .runtime_binding import NativeMemoryRuntimeScope, NativeRepresentationLane
from .schema import require_current_schema

_LIVE_SESSION = object()
_EXTERNAL_OWNERS = ("first-workspace", "first-identity", "first-character-declaration")
_NATIVE_OWNERS = ("first-character-native-seed", "first-character-linkage")


def _owner_paths(intent):
    value = intent.payload()
    workspace = Path("workspaces") / value["workspace"]["workspace_id"]
    paths = [workspace / "workspace_meta.json", workspace / "domains.json",
             workspace / "agents" / value["agent"]["agent_id"] / "identity.json"]
    if value["character"]["mode"] == "ENABLED":
        paths.append(workspace / "seeds" / value["character"]["definition"]["seed_id"] / "seed.json")
    return paths


def _inspect(root, intent):
    if str(root) != intent.data_root_identity:
        raise GenesisPreparationRefused("I4 intent must name the canonical explicit root")
    record = i3._matching_record(root, intent)
    if record is None:
        raise GenesisPreparationRefused("I4 requires an already prepared I3 record")
    allowed = i3._recovery_paths(intent, record)
    for path in _owner_paths(intent):
        allowed[path.as_posix()] = False
        allowed[path.with_name(f".{path.name}.publication.lock").as_posix()] = False
        for parent in path.parents:
            allowed[parent.as_posix()] = True
    entries = i3._inventory(root)
    if any(name not in allowed or facts[0] != allowed[name] for name, facts in entries.items()):
        raise GenesisPreparationRefused("unknown artifact in I4 recovery root")
    for name in entries:
        if name.endswith(("-wal", "-shm", "-journal")) and name.rsplit("-", 1)[0] not in entries:
            raise GenesisPreparationRefused("orphan SQLite sidecar")
    if (root / i3.PRIVATE_CORE).exists():
        raise GenesisPreparationRefused("I3 private core publication cleanup is incomplete")
    manifest = root / i3.PRIVATE_MANIFEST
    if manifest.exists() and i3.strict_object(manifest.read_bytes()) != i3._bootstrap_manifest(intent):
        raise GenesisPreparationRefused("I3 bootstrap manifest conflicts")
    core = root / i3.CORE_DIRECTORY / intent.payload()["allocations"]["core_relative_path"]
    if not core.is_file():
        raise GenesisPreparationRefused("I4 prepared core is absent")
    return record, entries


def _routing(intent):
    """Construct allocated PRIVATE facts; never discover or allocate identities."""
    value = intent.payload()
    plans = [p.payload() for p in intent.runtime_plans if p.payload()["scope_key"]["scope_kind"] == "PRIVATE"]
    if len(plans) != 1:
        raise GenesisPreparationRefused("I4 requires exactly the allocated first PRIVATE plan")
    plan = plans[0]
    scope = plan["scope_plan"]
    if (scope["workspace_id"] != value["workspace"]["workspace_id"]
        or scope["qualifier"] != value["agent"]["agent_id"]
        or scope["scope_kind"] != "PRIVATE_AGENT"
        or scope["motif_domain_id"] != value["agent"]["private_motif_domain_id"]
        or plan["representation_lane"] != value["representation_lane"]):
        raise GenesisPreparationRefused("I4 PRIVATE routing binding conflicts")
    runtime = NativeMemoryRuntimeScope(
        scope["workspace_id"], scope["scope_kind"], UUID(scope["legacy_source_namespace_id"]),
        UUID(scope["target_identity_namespace_id"]), UUID(scope["target_semantic_scope_id"]), scope["qualifier"],
    )
    routing = NativeFabricRoutingScope(runtime, UUID(scope["motif_alias_namespace_id"]),
        UUID(scope["motif_identity_namespace_id"]), UUID(scope["membership_identity_namespace_id"]),
        UUID(scope["idempotency_namespace_id"]))
    return routing, NativeRepresentationLane(**value["representation_lane"]), scope["motif_domain_id"]


def _seed(intent):
    value = intent.payload()
    if value["character"]["mode"] == "DISABLED":
        return None
    return CharacterSeed(**value["character"]["definition"],
                         created_ts=value["creation_facts"]["character_created_ts"], seed_eids=[], seed_motif_id="")


def _configuration(intent, embedder):
    scope, lane, domain = _routing(intent)
    seed = _seed(intent)
    parent = "genesis-i4-seed:" + payload_digest(dict(
        genesis_operation_key=intent.operation_key, intent_digest=intent.digest,
        workspace_id=scope.runtime_scope.workspace_id, agent_id=scope.runtime_scope.agent_id,
        seed_id=seed.seed_id, definition_digest=character_seed_definition_digest(seed),
    ))
    return NativeCharacterSeedPlantRuntimeConfiguration(
        scope.runtime_scope.workspace_id, scope.runtime_scope.agent_id, domain, parent, scope, lane,
        embedder, now_ts=lambda: intent.payload()["creation_facts"]["character_created_ts"],
    )


def _json_result(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_result(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_result(v) for v in value]
    return value


@dataclass(frozen=True)
class GenesisFirstCharacterBundle:
    character_mode: str
    native_seed: NativeCharacterSeedPlantResult | None
    child_references: tuple[GenesisEvidenceReference, ...]


class GenesisCharacterAdministration(i3.GenesisAdministration):
    """An I4 continuation of the I3 lock protocol; use the context manager."""

    def __init__(self, root, record, fault=i3._noop):
        super().__init__(root, record, fault)
        self._lease = None

    def _require_active(self):
        super()._require_active()
        if self._lease is not _LIVE_SESSION:
            raise GenesisPreparationRefused("I4 requires a live I3 root-onboarding lock session")

    def _require_record(self):
        self._require_active()
        record, _entries = _inspect(self.root, self.intent)
        if record != self.record:
            raise GenesisPreparationRefused("I4 administrative record changed")
        expected = [super()._reference("native-core-preparation", i3._bootstrap_manifest(self.intent))]
        for table, rows in i3.genesis_prerequisites(self.intent).items():
            expected.append(super()._reference("native-catalog:" + table, dict(table=table, rows=rows)))
        if not all(ref in record.child_operation_references for ref in expected):
            raise GenesisPreparationRefused("I4 requires complete I3 preparation checkpoints")
        owners = _EXTERNAL_OWNERS + (_NATIVE_OWNERS if _seed(self.intent) is not None else ())
        for ref in record.child_operation_references:
            if ref not in expected and (ref.payload()["owner"] not in owners or
                ref.payload()["operation_key"] != self._reference(ref.payload()["owner"], {}).payload()["operation_key"]):
                raise GenesisPreparationRefused("unsupported or conflicting I4 child checkpoint")

    def _reference(self, owner, result):
        return GenesisEvidenceReference.from_payload(dict(owner=owner,
            operation_key="genesis-i4:" + payload_digest(dict(intent=self.intent.digest, owner=owner)),
            result_digest=payload_digest(result)))

    def observe_quiescence(self, observer, *, operator_attestation, issuer_reference):
        self._require_record()
        self._quiescent = False
        since = time.time_ns()
        facts = observer(self.root, self.intent)
        if not isinstance(facts, i3.GenesisWriterObservation):
            raise GenesisPreparationRefused("typed writer observation required")
        evidence = facts.evidence(self.intent, since_ns=since,
            operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        self._require_record()
        self.replace_record(self.record, replace(self.record, phase_revision=self.record.phase_revision + 1,
            quiescence_observations=self.record.quiescence_observations + (evidence,)))
        self._quiescent = True
        return evidence

    def _references(self, result):
        projection = self.intent.external_owner_projection()
        value = self.intent.payload()
        refs = tuple(self._reference(owner, projection[key]) for owner, key in
                     zip(_EXTERNAL_OWNERS, ("workspace", "identity", "character"), strict=True))
        if result is not None:
            refs += (self._reference(_NATIVE_OWNERS[0], _json_result(asdict(result))),
                     self._reference(_NATIVE_OWNERS[1], dict(
                         workspace_id=value["workspace"]["workspace_id"],
                         seed_id=value["character"]["definition"]["seed_id"],
                         definition_digest=result.seed_definition_digest,
                         seed_eids=list(result.seed_eids), seed_motif_id=result.seed_motif_id)))
        return refs

    def _verify_external(self, result):
        """Reopen fixed owners after the final observation; never repair here."""
        value = self.intent.payload()
        workspace, agent, created, lane = value["workspace"], value["agent"], value["creation_facts"], value["representation_lane"]
        declaration = WorkspaceDeclaration(workspace["workspace_id"], created["workspace_created_ts"], lane["dimension"],
            lane["provider"], lane["model"], tuple(workspace["ordered_domains"]))
        for path, expected in zip(_owner_paths(self.intent)[:2], (declaration.metadata_payload(), declaration.domain_payload()), strict=True):
            if not (self.root / path).is_file() or payload_digest(i3.strict_object((self.root / path).read_bytes())) != payload_digest(expected):
                raise GenesisPreparationRefused("workspace changed during I4 verification")
        identities = IdentityStore(str(self.root))
        observed = identities.read_strict_for_onboarding(workspace["workspace_id"], agent["agent_id"])
        expected = AgentIdentity(workspace["workspace_id"], agent["agent_id"], agent["identity_seed"], agent["initial_overlay"],
                                 created["identity_created_ts"], created["identity_created_ts"])
        if observed != expected:
            raise GenesisPreparationRefused("identity changed during I4 verification")
        identities.verify_stable_for_onboarding(expected)
        if result is not None:
            characters = CharacterStore(str(self.root))
            seed = characters.read_seed_strict_for_onboarding(workspace["workspace_id"], value["character"]["definition"]["seed_id"])
            if (seed is None or characters.stable_seed_projection(seed) != characters.stable_seed_projection(_seed(self.intent))
                or tuple(seed.seed_eids) != result.seed_eids or seed.seed_motif_id != result.seed_motif_id):
                raise GenesisPreparationRefused("Character owner changed during I4 verification")

    def prepare_first_character_bundle(self, *, embedder, observer, operator_attestation, issuer_reference):
        self._require_record()
        if not self._quiescent:
            raise GenesisPreparationRefused("fresh successful quiescence observation required")
        # A previous observation alone is insufficient: observe again immediately
        # before this bounded mutation, and consume it even if a child fails.
        self.observe_quiescence(observer, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        self._quiescent = False
        value = self.intent.payload()
        seed = _seed(self.intent)
        config = _configuration(self.intent, embedder) if seed is not None else None
        core = self.root / i3.CORE_DIRECTORY / value["allocations"]["core_relative_path"]
        request = NativeCharacterSeedPlantRequest(seed) if seed is not None else None
        with closing(i3._open_readonly(core)) as connection:
            _verify_core(connection, self.intent, config)
            recovered = NativeCharacterSeedPlantRuntime(connection, configuration=config).recover_completed_seed(request) if config else None
        prior_refs = {ref.payload()["owner"]: ref for ref in self.record.child_operation_references}
        for ref in self._references(recovered):
            self._has_reference(ref)
        if recovered is None and any(owner in prior_refs for owner in _NATIVE_OWNERS):
            raise GenesisPreparationRefused("checkpointed native seed completion is absent")
        paths = _owner_paths(self.intent)
        for owner, required in zip(_EXTERNAL_OWNERS, (paths[:2], paths[2:3], paths[3:]), strict=True):
            if owner in prior_refs and any(not (self.root / p).is_file() for p in required):
                raise GenesisPreparationRefused("checkpointed external owner is missing")
        workspace, agent, created, lane = value["workspace"], value["agent"], value["creation_facts"], value["representation_lane"]
        create_or_verify_workspace_declaration(data_dir=str(self.root), expected=WorkspaceDeclaration(
            workspace["workspace_id"], created["workspace_created_ts"], lane["dimension"], lane["provider"], lane["model"],
            tuple(workspace["ordered_domains"])))
        self.fault("after-workspace-declaration")
        identity = AgentIdentity(workspace["workspace_id"], agent["agent_id"], agent["identity_seed"],
                                 agent["initial_overlay"], created["identity_created_ts"], created["identity_created_ts"])
        identities = IdentityStore(str(self.root))
        identities.create_or_verify_for_onboarding(identity)
        identities.verify_stable_for_onboarding(identity)
        self.fault("after-identity-publication")
        if seed is not None:
            characters = CharacterStore(str(self.root))
            stored = characters.create_or_verify_seed_definition(workspace["workspace_id"], value["character"]["definition"],
                                                                 created_ts=created["character_created_ts"])
            if stored.seed_eids or stored.seed_motif_id:
                if recovered is None or tuple(stored.seed_eids) != recovered.seed_eids or stored.seed_motif_id != recovered.seed_motif_id:
                    raise GenesisPreparationRefused("external Character linkage has no matching native completion")
            self.fault("after-character-definition")
            if recovered is None:
                with open_existing_native_core_connection(core) as opened:
                    _verify_core(opened.connection, self.intent, config)
                    runtime = NativeCharacterSeedPlantRuntime(opened.connection, configuration=config)
                    runtime.plant_seed(request)
                self.fault("after-native-seed-plant")
            # Always reread committed owner truth, including the native-ahead case.
            with closing(i3._open_readonly(core)) as connection:
                _verify_core(connection, self.intent, config)
                recovered = NativeCharacterSeedPlantRuntime(connection, configuration=config).recover_completed_seed(request)
                if recovered is None:
                    raise GenesisPreparationRefused("native seed completion did not recover")
            self.fault("before-character-linkage")
            characters.finalize_or_verify_seed_linkage(workspace["workspace_id"], value["character"]["definition"],
                created_ts=created["character_created_ts"], seed_eids=recovered.seed_eids, seed_motif_id=recovered.seed_motif_id)
            final = characters.read_seed_strict_for_onboarding(workspace["workspace_id"], seed.seed_id)
            if final is None or tuple(final.seed_eids) != recovered.seed_eids or final.seed_motif_id != recovered.seed_motif_id:
                raise GenesisPreparationRefused("external Character linkage verification failed")
            self.fault("after-character-linkage")
        self.observe_quiescence(observer, operator_attestation=operator_attestation, issuer_reference=issuer_reference)
        self._quiescent = False
        with closing(i3._open_readonly(core)) as connection:
            _verify_core(connection, self.intent, config)
            if config and NativeCharacterSeedPlantRuntime(connection, configuration=config).recover_completed_seed(request) != recovered:
                raise GenesisPreparationRefused("native seed changed during final observation")
        self._verify_external(recovered)
        references = self._references(recovered)
        missing = tuple(ref for ref in references if not self._has_reference(ref))
        if missing:
            self.fault("before-first-character-checkpoint")
            self.replace_record(self.record, replace(self.record, phase_revision=self.record.phase_revision + 1,
                child_operation_references=self.record.child_operation_references + missing))
        return GenesisFirstCharacterBundle(value["character"]["mode"], recovered, references)


@contextmanager
def begin_genesis_character_administration(*, data_root: str | Path, intent: GenesisIntent,
                                           timeout_seconds=1.0, fault=i3._noop):
    root = canonical_genesis_root(data_root)
    record, before = _inspect(root, intent)
    with i3.root_onboarding_lock(data_root=root, timeout_seconds=timeout_seconds):
        current, after = _inspect(root, intent)
        if current != record or before != after:
            raise GenesisPreparationRefused("I4 root changed while acquiring the onboarding lock")
        session = GenesisCharacterAdministration(root, record, fault)
        session._lease = _LIVE_SESSION
        try:
            session._require_record()
            yield session
        finally:
            session._lease = None
            session._active = False
            session._quiescent = False


def _verify_core(connection, intent, config):
    """Exact I3 catalogs plus only the bounded seed operation's native effects."""
    expected = i3.genesis_prerequisites(intent)
    if config is not None:
        value = intent.payload()
        private = next(p.payload() for p in intent.runtime_plans if p.payload()["scope_key"]["scope_kind"] == "PRIVATE")
        plan, routing = private["scope_plan"], config.routing_scope
        observed = dict(
            workspace_id=routing.runtime_scope.workspace_id, scope_kind=routing.runtime_scope.scope_kind,
            qualifier=routing.runtime_scope.agent_id, motif_domain_id=config.domain_id,
            legacy_source_namespace_id=str(routing.runtime_scope.legacy_source_namespace_id),
            target_identity_namespace_id=str(routing.runtime_scope.identity_namespace_id),
            target_semantic_scope_id=str(routing.runtime_scope.semantic_scope_id),
            motif_alias_namespace_id=str(routing.motif_alias_namespace_id),
            motif_identity_namespace_id=str(routing.motif_identity_namespace_id),
            membership_identity_namespace_id=str(routing.membership_identity_namespace_id),
            idempotency_namespace_id=str(routing.idempotency_namespace_id),
        )
        if (observed != plan or routing.runtime_scope.domain_id is not None
            or asdict(config.representation_lane) != value["representation_lane"]
            or config.workspace_id != value["workspace"]["workspace_id"] or config.agent_id != value["agent"]["agent_id"]):
            raise GenesisPreparationRefused("I4 routing configuration differs from frozen PRIVATE allocation")
    if config is None or connection.execute("SELECT 1 FROM operations LIMIT 1").fetchone() is None:
        i3._verify_native(connection, intent, expected, complete=True)
        return
    metadata = require_current_schema(connection)
    if (metadata.core_id != UUID(intent.payload()["allocations"]["core_id"]).bytes or metadata.core_role != "STAGING"
        or connection.execute("SELECT deployment_state,referenced_core_id FROM deployment_metadata").fetchall() != [("LEGACY_ACTIVE", None)]):
        raise GenesisPreparationRefused("I4 core identity or inert deployment state conflicts")
    for table, (identifier, key) in i3.CATALOG_COLUMNS.items():
        rows = connection.execute(f"SELECT {identifier},{key}" + (",created_at_ns" if table != "idempotency_namespaces" else "") + f" FROM {table}").fetchall()
        if ({str(UUID(bytes=r[0])): r[1] for r in rows} != expected[table]
            or (table != "idempotency_namespaces" and any(r[2] != 0 for r in rows))):
            raise GenesisPreparationRefused("I4 allocated prerequisite closure conflicts")
    runtime = NativeCharacterSeedPlantRuntime(connection, configuration=config)
    request = NativeCharacterSeedPlantRequest(_seed(intent))
    seed = request.seed
    digest = character_seed_definition_digest(seed)
    keys, source_ids = set(), set()
    for index, concept in enumerate(_split_seed_text(seed.seed_text)):
        keys.add(runtime._source_key(seed.seed_id, index))
        keys.add(runtime._motif_key(seed.seed_id, f"DECISION:{index}"))
        source = runtime._recover_source(request, digest, index, concept)
        if source is not None:
            source_ids.add(source.object_id.bytes)
            runtime._recover_ready_representation(source)
            keys.update(runtime._representation_key(source, stage) for stage in ("PENDING", "EXPECTATION", "READY"))
    keys.add(runtime._motif_key(seed.seed_id, "SEED_BASIN_BOOST"))
    for namespace, key in connection.execute("SELECT idempotency_namespace_id,idempotency_key FROM operations"):
        if namespace != config.routing_scope.idempotency_namespace_id.bytes or key not in keys:
            raise GenesisPreparationRefused("native effect is not a child of this I4 seed")
    scope = config.routing_scope
    motif_ids = set()
    for oid, namespace, kind in connection.execute("SELECT object_id,identity_namespace_id,object_kind FROM objects"):
        if not ((oid in source_ids and namespace == scope.runtime_scope.identity_namespace_id.bytes and kind == "LEGACY_CORE_NODE")
                or (namespace == scope.motif_identity_namespace_id.bytes and kind == "DERIVED_MOTIF")):
            raise GenesisPreparationRefused("I4 contains a foreign object or root profile")
        if kind == "DERIVED_MOTIF":
            motif_ids.add(oid)
    catalog = runtime._motif_reader.list_runtime_motifs(motif_alias_namespace_id=scope.motif_alias_namespace_id,
        domain_id=config.domain_id, semantic_scope_id=scope.runtime_scope.semantic_scope_id)
    if {m.motif_object_id.bytes for m in catalog} != motif_ids:
        raise GenesisPreparationRefused("I4 motif domain or alias closure conflicts")
    members = set()
    for motif in catalog:
        for member in runtime._motifs.list_current_motif_members(motif.motif_object_id):
            if member.member_object_id.bytes not in source_ids or member.member_semantic_scope_id != scope.runtime_scope.semantic_scope_id:
                raise GenesisPreparationRefused("I4 motif contains a foreign member")
            members.add(member.member_object_id.bytes)
    if runtime.recover_completed_seed(request) is not None and members != source_ids:
        raise GenesisPreparationRefused("I4 completed seed motif membership closure is incomplete")
    for namespace, kind in connection.execute("SELECT identity_namespace_id,relationship_kind FROM relationships"):
        if namespace != scope.membership_identity_namespace_id.bytes or kind != "MOTIF_MEMBERSHIP":
            raise GenesisPreparationRefused("I4 contains a root membership or foreign relationship")
    if connection.execute("SELECT 1 FROM object_revisions WHERE effective_semantic_scope_id<>? LIMIT 1",
                          (scope.runtime_scope.semantic_scope_id.bytes,)).fetchone():
        raise GenesisPreparationRefused("I4 object revision scope conflicts")
    for table, column, output in (("object_revisions", "object_revision_id", "object_revision_id"),
                                  ("relationship_revisions", "relationship_revision_id", "relationship_revision_id"),
                                  ("representations", "representation_id", "representation_id")):
        if connection.execute(f"SELECT 1 FROM {table} r WHERE NOT EXISTS (SELECT 1 FROM operation_outputs o WHERE o.{output}=r.{column}) LIMIT 1").fetchone():
            raise GenesisPreparationRefused("I4 contains an unreceipted native effect")
    allowed = set(i3.CATALOG_COLUMNS) | {
        "core_metadata", "deployment_metadata", "objects", "provenance_records", "object_revisions",
        "relationships", "relationship_revisions", "relationship_revision_endpoints", "operations", "operation_outputs",
        "semantic_transitions", "object_revision_effects", "relationship_revision_effects", "representation_state_effects",
        "integrity_measurement_effects", "representations", "representation_current_state", "representation_payloads",
        "integrity_expectations", "integrity_measurements", "legacy_object_aliases", "object_revision_governance",
        "memory_runtime_enumeration_orders",
    }
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='view' LIMIT 1").fetchone():
        raise GenesisPreparationRefused("undeclared native schema view")
    for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        if table not in allowed and connection.execute('SELECT 1 FROM "' + table.replace('"', '""') + '" LIMIT 1').fetchone():
            raise GenesisPreparationRefused("unexpected native content outside I4 seed effects")
    if connection.execute("PRAGMA foreign_key_check").fetchone():
        raise GenesisPreparationRefused("I4 native foreign-key integrity conflicts")
